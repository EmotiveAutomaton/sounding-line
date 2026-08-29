"""Stage 4 card-run scaffold: the part every track runner shares that is not a model
call. Opens the card directory, reads the frozen design (readers and tier), resumes
from cases.jsonl (units already scored for a reader are skipped, so a restart costs
nothing), writes provenance rows and raw outputs, checks the deadline between units,
and closes the card with metrics, a verdict, and a completion marker.

Row schema (brief §9.2): card, cell_id, unit_id, lineage_id, split, model_id,
model_revision, construction_seed, treatment, factors, attempted, realized, valid,
validity_reason, truth, truth_provenance, access_level, raw_ref, label_mapping,
parser_version, probs, primary_score, intervention, code_hash, contract_hash,
compute_charged_s, extra.
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from runners import s4_lib, s4_worlds                                             # noqa: E402
from soundingline.s4 import (Lineages, Manifest, RunContract, append_jsonl,       # noqa: E402
                             classify_outcome, code_hash, completion_marker, now_iso,
                             read_jsonl, write_json)


class DeadlineReached(RuntimeError):
    """The contract's deadline passed between units; the card is checkpointed by rows."""


class CardRun:
    def __init__(self, card: str, runner_file: str, cell_id: str | None = None):
        import os                                                                 # noqa: PLC0415
        self.card = card
        # S4_SPLIT=confirmation runs the same card on its reserved fresh lineages, into
        # a separate directory, with its own cell id (F01 sets it; discovery never does)
        self.split = os.environ.get("S4_SPLIT", "discovery")
        self.cell_id = cell_id or (card if self.split == "discovery" else f"{card}/confirm")
        self.out = s4_lib.card_dir(card) if self.split == "discovery" else s4_lib.card_dir(f"{card}/confirmation")
        self.contract = RunContract.load()
        if self.contract is None:
            raise RuntimeError("no RUN_CONTRACT.json; run the scheduler's prepare first")
        self.design = self.contract.frozen("design") or {}
        self.readers = list((self.design.get("readers") or {}).keys())
        self.revisions = dict(self.design.get("readers") or {})
        self.tier = self.design.get("tier", "minimum")
        self.L = Lineages()
        self.manifest = Manifest()
        self.cases_path = self.out / "cases.jsonl"
        self.raw_path = self.out / "raw_outputs.jsonl"
        self.code_hash = code_hash(REPO / "runners" / runner_file,
                                   REPO / "runners" / "s4_lib.py",
                                   REPO / "runners" / "s4_worlds.py")
        self.contract_hash = self.contract.hash()
        self.t0 = time.time()
        self.done = set()
        for r in read_jsonl(self.cases_path):
            self.done.add((r["model_id"], r["unit_id"]))
        self._buffer: list[dict] = []
        self._raw_buffer: list[dict] = []
        self._chash: dict[str, str] = {}      # unit id -> construction hash, this process

    # units -------------------------------------------------------------------------
    def units(self, domain: str, split: str | None = None) -> list[str]:
        split = split or self.split
        ids = [lid for lid, r in self.L.rows.items()
               if r["card"] == self.card and r["domain"] == domain and r["split"] == split]
        return sorted(ids, key=lambda x: self.L.rows[x]["world_index"])

    def parent_of(self, lid: str) -> str:
        """The source world of a derived unit (A02 on A01's worlds, T02 on T01's)."""
        return self.L.rows[lid].get("parent") or lid

    def register_world(self, lid: str, world: dict) -> str:
        """Record the construction's content hash on its ROOT lineage (verification 3: two
        lineages with identical content are one unit) and remember it for this unit's
        rows, which carry it as extra.construction_hash so the analyses can cluster on
        the construction rather than the nominal unit. The 2026-08-28 audit found
        mark_generated never called by any runner, so the duplicate control returned no
        duplicates where the truth was not checked; every root construction passes
        through here now."""
        h = s4_worlds.construction_hash(world)
        root = self.parent_of(lid)
        self._chash[lid] = h
        self._chash[root] = h
        if root in self.L.rows:
            self.L.mark_generated(root, h)
        return h

    def is_done(self, reader: str, unit_id: str) -> bool:
        return (reader, unit_id) in self.done

    def check_deadline(self) -> None:
        """Only a contract that stops at its deadline checkpoints a card mid-run; under
        run-until-empty (his ruling 2026-08-28) a card always finishes its units."""
        if self.contract.deadline_passed():
            self.flush()
            raise DeadlineReached(self.card)

    # rows --------------------------------------------------------------------------
    def row(self, reader: str, unit_id: str, lineage_id: str, treatment: str,
            factors: dict, truth, truth_provenance: str, access_level: str,
            readout: dict | None, primary_score: float | None, split: str = "discovery",
            seed: int | None = None, realized: bool = True, attempted: bool = True,
            valid: bool | None = None, validity_reason: str | None = None,
            intervention: dict | None = None, raw_ref: str | None = None,
            compute_s: float = 0.0, extra: dict | None = None) -> dict:
        if valid is None:
            valid = bool(readout and readout.get("valid"))
        if validity_reason is None:
            validity_reason = (readout or {}).get("validity_reason", "ok" if valid else "invalid")
        if split == "discovery" and self.split != "discovery":
            split = self.split
        r = {"card": self.card, "cell_id": self.cell_id, "unit_id": unit_id,
             "lineage_id": lineage_id, "split": split, "model_id": reader,
             "model_revision": self.revisions.get(reader, s4_lib.model_revision(reader)),
             "construction_seed": seed if seed is not None else
             self.L.rows.get(lineage_id, {}).get("construction_seed"),
             "treatment": treatment, "factors": factors, "attempted": attempted,
             "realized": realized, "valid": valid, "validity_reason": validity_reason,
             "truth": truth, "truth_provenance": truth_provenance,
             "access_level": access_level, "raw_ref": raw_ref,
             "label_mapping": (readout or {}).get("labels"),
             "parser_version": (readout or {}).get("parser", s4_lib.READOUT_VERSION),
             "probs": (readout or {}).get("probs"), "pred": (readout or {}).get("pred"),
             "primary_score": primary_score, "intervention": intervention,
             "code_hash": self.code_hash, "contract_hash": self.contract_hash,
             "compute_charged_s": round(compute_s, 3), "at": now_iso(),
             "extra": dict(extra or {})}
        h = self._chash.get(unit_id) or self._chash.get(lineage_id)
        if h and "construction_hash" not in r["extra"]:
            r["extra"]["construction_hash"] = h
        self._buffer.append(r)
        return r

    def raw(self, reader: str, unit_id: str, prompt: str, gen: dict,
            validity_reason: str = "ok", extra: dict | None = None) -> str:
        ref = f"{self.card}:{unit_id}:{reader}:{len(self._raw_buffer) + 1}:{now_iso()}"
        self._raw_buffer.append(s4_lib.raw_output_row(
            self.card, self.cell_id, unit_id, reader, self.revisions.get(reader, "?"),
            prompt, gen, validity_reason=validity_reason, extra={"raw_ref": ref, **(extra or {})}))
        return ref

    def unit_complete(self, reader: str, unit_id: str) -> None:
        """Write the unit's rows atomically-enough (append after the unit finishes) so a
        restart resumes at unit granularity."""
        self.flush()
        self.done.add((reader, unit_id))

    def flush(self) -> None:
        if self._buffer:
            append_jsonl(self.cases_path, self._buffer)
            self._buffer = []
        if self._raw_buffer:
            append_jsonl(self.raw_path, self._raw_buffer)
            self._raw_buffer = []

    def rows(self) -> list[dict]:
        self.flush()
        return read_jsonl(self.cases_path)

    # closing -----------------------------------------------------------------------
    def classify(self, contrast: dict, threshold: float) -> dict:
        if contrast.get("point") is None:
            return {"outcome": "VOID", "reason": "no units"}
        oc, why = classify_outcome(contrast["point"], contrast["lo"], contrast["hi"], threshold)
        return {"outcome": oc, "reason": why, "point": contrast["point"],
                "ci": [contrast["lo"], contrast["hi"]], "n_units": contrast["n_units"],
                "threshold": threshold, "perm_p": contrast.get("perm_p")}

    def finish(self, metrics: dict, verdict: dict, gpu_lock_s: float = 0.0,
               inputs: dict | None = None) -> None:
        self.flush()
        write_json(self.out / "metrics.json", {"card": self.card, "written_at": now_iso(),
                                               "env": s4_lib.env_versions(), **metrics})
        verdict = {"card": self.card, "cell_id": self.cell_id, "readers": self.readers,
                   "tier": self.tier, "minutes": round((time.time() - self.t0) / 60, 2),
                   "gpu_lock_min": round(gpu_lock_s / 60, 2), **verdict}
        outputs = {"metrics": str(self.out / "metrics.json")}
        if self.cases_path.exists():
            outputs["cases"] = str(self.cases_path)
        verdict["marker"] = completion_marker(inputs or {}, outputs, self.contract)
        write_json(self.out / "verdict.json", verdict)
        # the manifest has ONE writer, the scheduler loop, which charges every cell from
        # the verdict's lock-held minutes; a card writing its own charge would save a
        # snapshot loaded at its start over the loop's later state
        print(f"{self.card} finished: {json.dumps({k: v for k, v in verdict.items() if k in ('outcome', 'primary', 'exec')})}")


def cid(row: dict) -> str:
    """The cluster a row belongs to for any interval: its construction hash when the
    row carries one, else its nominal unit. Textual twins (the T01 defect, TODO R7)
    collapse to one cluster instead of inflating the resampling population."""
    return (row.get("extra") or {}).get("construction_hash") or row["unit_id"]


def cluster_by_construction(rows: list[dict]) -> list[dict]:
    """Copies of the rows with unit_id replaced by the construction cluster."""
    return [{**r, "unit_id": cid(r)} for r in rows]


def construction_summary(rows: list[dict]) -> dict:
    """Nominal units against distinct constructions among them: the two numbers a verdict
    reports side by side so an inflated n is visible in the receipt."""
    units = {r["unit_id"] for r in rows}
    clusters = {cid(r) for r in rows}
    hashed = {r["unit_id"] for r in rows if (r.get("extra") or {}).get("construction_hash")}
    return {"n_units": len(units), "n_distinct_constructions": len(clusters),
            "n_units_with_hash": len(hashed),
            "checked": bool(units) and hashed == units}


def cell_counts(rows: list[dict], factor_keys: list[str]) -> dict:
    """Attempted / realized / valid / scored per factorial cell (brief §6.4)."""
    out: dict = {}
    for r in rows:
        key = json.dumps({k: r["factors"].get(k) for k in factor_keys} | {"domain": r["factors"].get("domain")},
                         sort_keys=True)
        c = out.setdefault(key, {"attempted": 0, "realized": 0, "valid": 0, "scored": 0,
                                 "units": set()})
        c["attempted"] += int(r["attempted"])
        c["realized"] += int(r["realized"])
        c["valid"] += int(r["valid"])
        if r["primary_score"] is not None:
            c["scored"] += 1
            c["units"].add(r["unit_id"])
    for c in out.values():
        c["scored_units"] = len(c.pop("units"))
    return out


def mean_by(rows: list[dict], keys: list[str], value: str = "primary_score") -> dict:
    acc: dict = {}
    for r in rows:
        if r.get(value) is None:
            continue
        k = "|".join(str(r["factors"].get(x, r.get(x))) for x in keys)
        acc.setdefault(k, []).append(float(r[value]))
    return {k: {"mean": sum(v) / len(v), "n": len(v)} for k, v in acc.items()}


def select_rows(rows, **conds):
    out = []
    for r in rows:
        ok = True
        for k, v in conds.items():
            val = r["factors"].get(k, r.get(k))
            if val != v:
                ok = False
                break
        if ok and r.get("primary_score") is not None:
            out.append(r)
    return out
