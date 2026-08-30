"""Stage 5 card-run scaffold: the Stage-4 scaffold (runners/s4_run_common.py) on the
Stage-5 records and lanes. Opens the card directory for the lane, reads the frozen
design, resumes from cases.jsonl at unit granularity, writes provenance rows and raw
outputs, registers every root construction's content hash on its lineage (the duplicate
control), and closes the card with metrics, a verdict, and a completion marker. Cards
never write the manifest (one writer, the scheduler).

DESIGN CHECK (2026-08-29)
lessons read: LESSONS §3, §5 (a library carries no gate of its own).
gates: none in the run record; every gate and its expectation under the null and the alternative,
  with the failure direction it guards, lives in the card runner that uses it.
bands: none here; the card runners' verdict bands are exhaustive (no silent interval) and
  are stated there.
"""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from runners import s5_lib                                                        # noqa: E402
from runners.s4_run_common import (cell_counts, cid, cluster_by_construction,      # noqa: E402,F401
                                   construction_summary, mean_by, select_rows)
from runners.s4_worlds import construction_hash                                   # noqa: E402
from soundingline.stage5 import (SPLITS, TRACK_OF, Lineages5, Manifest5, RunContract5,       # noqa: E402
                                 append_jsonl, classify_outcome, code_hash,
                                 completion_marker, now_iso, read_jsonl, write_json,
                                 workload_locked)

LANE_ENV = "S5_SPLIT"
SMOKE = bool(os.environ.get("S5_SMOKE"))

__all__ = ['Lineages5', 'Manifest5', 'RunContract5', 'SPLITS', 'cell_counts', 'cid', 'classify_outcome', 'cluster_by_construction', 'code_hash', 'completion_marker', 'construction_hash', 'construction_summary', 'mean_by', 'now_iso', 'read_jsonl', 's5_lib', 'select_rows', 'workload_locked', 'write_json']



class DeadlineReached(RuntimeError):
    pass


class WorkloadNotLocked(RuntimeError):
    """§8.3: discovery outputs may not be opened before the workload lock is written."""


class CardRun:
    def __init__(self, card: str, runner_file: str, cell_id: str | None = None,
                 require_lock: bool = True):
        self.card = card
        self.split = os.environ.get(LANE_ENV, "discovery")
        assert self.split in SPLITS, self.split
        self.cell_id = cell_id or (card if self.split == "discovery" else f"{card}/{self.split}")
        # a repair cell (S5_CELL, e.g. J02/v2) writes beside the withdrawn cell, never over it
        override = os.environ.get("S5_CELL")
        if override and override.split("/")[0] == card and self.split == "discovery":
            self.cell_id = override
        self.out = s5_lib.card_dir(self.cell_id)
        self.contract = RunContract5.load()
        if self.contract is None:
            raise RuntimeError("no RUN_CONTRACT.json; run the scheduler's prepare first")
        if require_lock and self.split in ("discovery", "transfer", "confirmation") and not workload_locked():
            raise WorkloadNotLocked(f"{card}: the workload lock is not written; discovery outputs stay closed")
        self.design = self.contract.frozen("design") or {}
        self.readers = list((self.design.get("readers") or {}).keys())
        # design 2: a track gate (appraisal: the source register; joint: latents to choice)
        # keeps the readers that passed it; if none passed, every reader runs and the
        # verdict carries the note (the track's result is then read as gate-failed)
        self.track_gate_note = None
        tg = self.design.get("track_gates") or {}
        track_key = {"appraisal": "A", "joint": "J"}.get(TRACK_OF.get(card, ""))
        if tg and track_key:
            passing = [r for r in self.readers if ((tg.get(r) or {}).get(track_key) or {}).get("passed")]
            if passing:
                self.readers = passing
            else:
                self.track_gate_note = f"no admitted reader passed the {TRACK_OF[card]} track gate; all readers run, result gate-failed"
        self.revisions = dict(self.design.get("readers") or {})
        self.tier = self.design.get("tier", "minimum")
        self.L = Lineages5()
        self.manifest = Manifest5()
        self.cases_path = self.out / "cases.jsonl"
        self.raw_path = self.out / "raw_outputs.jsonl"
        self.code_hash = code_hash(REPO / "runners" / runner_file, REPO / "runners" / "s5_lib.py",
                                   REPO / "runners" / "s5_worlds.py", REPO / "soundingline" / "stage5.py")
        self.contract_hash = self.contract.hash()
        self.t0 = time.time()
        self.done = set()
        for r in read_jsonl(self.cases_path):
            self.done.add((r["model_id"], r["unit_id"]))
        self._buffer: list[dict] = []
        self._raw_buffer: list[dict] = []
        self._chash: dict[str, str] = {}

    # units ---------------------------------------------------------------------------
    def units(self, domain: str, split: str | None = None) -> list[str]:
        split = split or self.split
        ids = [lid for lid, r in self.L.rows.items()
               if r["card"] == self.card and r["domain"] == domain and r["split"] == split]
        return sorted(ids, key=lambda x: self.L.rows[x]["world_index"])

    def parent_of(self, lid: str) -> str:
        return self.L.rows[lid].get("parent") or lid

    def register_world(self, lid: str, world: dict) -> str:
        h = construction_hash(world)
        root = self.parent_of(lid)
        self._chash[lid] = h
        self._chash[root] = h
        if root in self.L.rows:
            self.L.mark_generated(root, h)
        return h

    def is_done(self, reader: str, unit_id: str) -> bool:
        return (reader, unit_id) in self.done

    def check_deadline(self) -> None:
        if self.contract.deadline_passed():
            self.flush()
            raise DeadlineReached(self.card)

    # rows ----------------------------------------------------------------------------
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
             "lineage_id": lineage_id, "split": split, "lane": split, "model_id": reader,
             "model_revision": self.revisions.get(reader, s5_lib.model_revision(reader)),
             "construction_seed": seed if seed is not None else
             self.L.rows.get(lineage_id, {}).get("construction_seed"),
             "treatment": treatment, "factors": factors, "attempted": attempted,
             "realized": realized, "valid": valid, "validity_reason": validity_reason,
             "truth": truth, "truth_provenance": truth_provenance,
             "access_level": access_level, "raw_ref": raw_ref,
             "label_mapping": (readout or {}).get("labels"),
             "parser_version": (readout or {}).get("parser", s5_lib.READOUT_VERSION),
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
        self._raw_buffer.append(s5_lib.raw_output_row(
            self.card, self.cell_id, unit_id, reader, self.revisions.get(reader, "?"),
            prompt, gen, parser_version=s5_lib.PARSER_VERSION, validity_reason=validity_reason,
            extra={"raw_ref": ref, **(extra or {})}))
        return ref

    def unit_complete(self, reader: str, unit_id: str) -> None:
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

    # closing -------------------------------------------------------------------------
    def classify(self, contrast: dict, threshold: float) -> dict:
        if contrast.get("point") is None:
            return {"outcome": "VOID", "reason": "no units"}
        oc, why = classify_outcome(contrast["point"], contrast["lo"], contrast["hi"], threshold)
        return {"outcome": oc, "reason": why, "point": contrast["point"],
                "ci": [contrast["lo"], contrast["hi"]], "n_units": contrast["n_units"],
                "threshold": threshold, "perm_p": contrast.get("perm_p")}

    def threshold(self, default: float = 0.03) -> float:
        return (self.design.get("thresholds") or {}).get(self.card) or default

    def finish(self, metrics: dict, verdict: dict, gpu_lock_s: float = 0.0,
               inputs: dict | None = None, rival: str | None = None) -> None:
        self.flush()
        write_json(self.out / "metrics.json", {"card": self.card, "lane": self.split,
                                               "written_at": now_iso(),
                                               "env": s5_lib.env_versions(), **metrics})
        verdict = {"card": self.card, "cell_id": self.cell_id, "lane": self.split,
                   "readers": self.readers, "tier": self.tier, "track_gate_note": self.track_gate_note,
                   "minutes": round((time.time() - self.t0) / 60, 2),
                   "gpu_lock_min": round(gpu_lock_s / 60, 2),
                   "strongest_surviving_rival": rival, **verdict}
        outputs = {"metrics": str(self.out / "metrics.json")}
        if self.cases_path.exists():
            outputs["cases"] = str(self.cases_path)
        verdict["marker"] = completion_marker(inputs or {}, outputs, self.contract)
        write_json(self.out / "verdict.json", verdict)
        print(f"{self.card} finished: {json.dumps({k: v for k, v in verdict.items() if k in ('outcome', 'primary', 'exec')})}")
