"""Stage 8 question-run scaffold: the Stage 7 scaffold (cardrun.py) over the Stage 8 registry
and lanes: opens the cell directory, reads the frozen design, resumes from cases.jsonl at
unit granularity, writes rows and predictions, registers constructions, and closes with
metrics, a verdict, and a completion marker. The 48-hour ceiling is checked between units;
a cell interrupted by it exits 3 with its rows checkpointed.

DESIGN CHECK (2026-09-04)
lessons read: LESSONS §3 (rows key on (reader, unit, arm) so duplication cannot move a
  unit-level mean; every statistic a verdict rests on is written), §5 (a clean exit that
  wrote no produce is a failure; the deadline is a wake-and-decide event).
gates: none here; the engines own the bands. bands: none.
"""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from runners import s5_lib                                                         # noqa: E402
from runners.stage8 import cards as C                                              # noqa: E402
from soundingline.stage7 import workload_locked                                   # noqa: E402
from soundingline.stage8 import (S8, SMOKE, SPLITS, TRACK_OF, Lineages8, Manifest8,  # noqa: E402
                                 RunContract8, append_jsonl, card_dir, classify_outcome,
                                 code_hash, completion_marker, now_iso, read_jsonl,
                                 sha256_text, write_json)

LANE_ENV = "S7_SPLIT"


class DeadlineReached(RuntimeError):
    pass


class WorkloadNotLocked(RuntimeError):
    pass


class EndpointStarved(RuntimeError):
    """A model arm lost more than STARVED_SHARE of its rows to the endpoint (503 out of
    memory under a shared card, a dead server): the cell must not close on the fragment."""


STARVED_SHARE = 0.2
STARVED_MARK = "no prediction: EndpointError"


def endpoint_failed(row: dict) -> bool:
    return (not row.get("valid")) and str(row.get("validity_reason", "")).startswith(STARVED_MARK)


def construction_hash(obj) -> str:
    return sha256_text(json.dumps(obj, sort_keys=True, default=str))[:16]


class CardRun8:
    def __init__(self, card: str, cell_id: str | None = None, require_lock: bool = True):
        self.card = card
        self.split = os.environ.get(LANE_ENV, "discovery")
        assert self.split in SPLITS, self.split
        self.cell_id = cell_id or (card if self.split == "discovery" else f"{card}/{self.split}")
        override = os.environ.get("S7_CELL")
        if override and override.split("/")[0] == card and self.split == "discovery":
            self.cell_id = override
        self.out = card_dir(self.cell_id)
        self.contract = RunContract8.load()
        if self.contract is None:
            raise RuntimeError("no RUN_CONTRACT.json; run the scheduler's prepare first")
        if require_lock and self.split in ("discovery", "transfer", "confirmation") and not workload_locked():
            raise WorkloadNotLocked(f"{card}: the workload lock is not written; scientific outputs stay closed")
        self.design = self.contract.frozen("design") or {}
        self.readers = list((self.design.get("readers") or {}).keys()) or list(C.READERS.values())
        self.revisions = dict(self.design.get("readers") or {})
        self.gates = self.design.get("gates") or {}
        self.tier = self.design.get("tier", "minimum")
        self.L = Lineages8()
        self.manifest = Manifest8()
        self.cases_path = self.out / "cases.jsonl"
        self.raw_path = self.out / "raw_outputs.jsonl"
        self.pred_dir = S8 / "predictions" / self.cell_id.replace("/", "_")
        self.code_hash = code_hash(REPO / "runners" / "stage8" / "engines.py",
                                   REPO / "runners" / "stage8" / "constructor" / "population.py",
                                   REPO / "runners" / "stage8" / "constructor" / "purpose.py",
                                   REPO / "runners" / "stage8" / "reader" / "forward_model.py",
                                   REPO / "runners" / "stage8" / "reader" / "worker.py",
                                   REPO / "runners" / "stage7" / "reader" / "law.py",
                                   REPO / "soundingline" / "stage8.py")
        self.contract_hash = self.contract.hash()
        self.t0 = time.time()
        self.done = set()
        for r in read_jsonl(self.cases_path):
            if endpoint_failed(r):
                continue                      # an endpoint failure is not a done unit; it reruns on resume
            self.done.add((r.get("model_id") or "-", r["unit_id"], r.get("arm") or "-"))
        self._buffer: list[dict] = []
        self._raw_buffer: list[dict] = []
        self._degenerate = 0
        self._kept_fraction = None
        self.diagnosis_only = False

    def register_world(self, lid: str, obj: dict) -> str:
        h = construction_hash(obj)
        if lid not in self.L.rows:
            self.L.allocate(lid.split("|")[0], lid.split("|")[1] if "|" in lid else "-", [0], 1, self.split)
            self.L.rows.setdefault(lid, {"id": lid, "split": self.split, "generation_hash": None, "fit_use": [], "inspected": False})
        try:
            self.L.mark_generated(lid, h)
        except KeyError:
            pass
        return h

    def is_done(self, reader: str | None, unit_id: str, arm: str | None = None) -> bool:
        return (reader or "-", unit_id, arm or "-") in self.done

    def check_deadline(self) -> None:
        if self.contract.deadline_passed():
            self.flush()
            raise DeadlineReached(self.card)

    def row(self, unit_id: str, *, reader: str | None = None, arm: str | None = None,
            factors: dict | None = None, truth=None, truth_ref: str | None = None,
            scores: dict | None = None, primary_score: float | None = None,
            valid: bool = True, validity_reason: str = "ok", budget: dict | None = None,
            evidence_sha: str | None = None, pred_ref: str | None = None, extra: dict | None = None) -> dict:
        r = {"card": self.card, "cell_id": self.cell_id, "unit_id": unit_id, "lineage_id": unit_id,
             "split": self.split, "lane": self.split, "model_id": reader or "-", "arm": arm or "-",
             "model_revision": self.revisions.get(reader, "-") if reader else "-",
             "factors": dict(factors or {}), "truth": truth, "truth_ref": truth_ref,
             "scores": dict(scores or {}), "primary_score": primary_score,
             "valid": valid, "validity_reason": validity_reason, "budget": budget,
             "evidence_sha": evidence_sha, "pred_ref": pred_ref,
             "code_hash": self.code_hash, "contract_hash": self.contract_hash,
             "at": now_iso(), "extra": dict(extra or {})}
        self._buffer.append(r)
        return r

    def save_prediction(self, unit_id: str, arm: str, reader: str | None, pred: dict) -> str:
        self.pred_dir.mkdir(parents=True, exist_ok=True)
        ref = f"{arm}_{(reader or 'x').split('/')[-1].replace(':', '-')}_{unit_id.replace('|', '-')}.json"
        if len(ref) > 120:
            ref = ref[:80] + "-" + sha256_text(ref)[:12] + ".json"
        write_json(self.pred_dir / ref, pred)
        return str(self.pred_dir / ref)

    def unit_complete(self, reader: str | None, unit_id: str, arm: str | None = None) -> None:
        self.flush()
        self.done.add((reader or "-", unit_id, arm or "-"))

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

    def rows_of(self, other_card: str) -> list[dict]:
        d = (S8 / other_card) if self.split == "discovery" else (S8 / other_card / self.split)
        return read_jsonl(d / "cases.jsonl")

    def classify(self, contrast: dict, threshold: float) -> dict:
        if contrast.get("point") is None:
            return {"outcome": "VOID", "reason": "no units"}
        oc, why = classify_outcome(contrast["point"], contrast["lo"], contrast["hi"], threshold)
        return {"outcome": oc, "reason": why, "point": contrast["point"],
                "ci": [contrast["lo"], contrast["hi"]], "n_units": contrast.get("n_units"),
                "threshold": threshold, "perm_p": contrast.get("perm_p")}

    def threshold(self, default: float = 0.03) -> float:
        t = (self.design.get("thresholds") or {}).get(self.card)
        return t if t is not None else default

    def starved_arms(self) -> dict:
        """Per (reader, arm): the share of rows lost to the endpoint, counting a unit as lost
        only when no valid row exists for it (a rerun repairs the unit)."""
        by: dict = {}
        for r in read_jsonl(self.cases_path):
            if (r.get("model_id") or "-") == "-":
                continue
            k = (r["model_id"], r.get("arm") or "-")
            u = by.setdefault(k, {})
            u[r["unit_id"]] = u.get(r["unit_id"], False) or bool(r.get("valid"))
        out = {}
        for k, units in by.items():
            lost = sum(1 for ok in units.values() if not ok)
            out[f"{k[0]}|{k[1]}"] = round(lost / len(units), 4) if units else 0.0
        return out

    def finish(self, metrics: dict, verdict: dict, gpu_lock_s: float = 0.0,
               rival: str | None = None, inputs: dict | None = None) -> None:
        self.flush()
        starved = {k: v for k, v in self.starved_arms().items() if v > STARVED_SHARE}
        if starved and not os.environ.get("S8_ALLOW_STARVED"):
            write_json(self.out / "STARVED.json", {"at": now_iso(), "shares": starved, "bound": STARVED_SHARE,
                                                   "why": "rows lost to the endpoint (503 out of memory under a shared card, or a dead server); the cell refuses to close on the fragment; the lost units rerun on resume"})
            raise EndpointStarved(f"{self.card}: ENDPOINT STARVED {starved}; rows checkpointed; the lost units rerun on resume")
        write_json(self.out / "metrics.json", {"card": self.card, "lane": self.split,
                                               "written_at": now_iso(), "env": s5_lib.env_versions(), **metrics})
        if getattr(self, "diagnosis_only", False):
            verdict = dict(verdict, diagnosis_only=True,
                           reason="DIAGNOSIS on readers not admitted by the expertise gate (the generation gate failed after its one repair); no reader claim. " + str(verdict.get("reason", "")))
        verdict = {"card": self.card, "cell_id": self.cell_id, "lane": self.split,
                   "track": TRACK_OF.get(self.card), "readers": self.readers, "tier": self.tier,
                   "minutes": round((time.time() - self.t0) / 60, 2),
                   "gpu_lock_min": round(gpu_lock_s / 60, 2),
                   "strongest_surviving_rival": rival, **verdict}
        outputs = {"metrics": str(self.out / "metrics.json")}
        if self.cases_path.exists():
            outputs["cases"] = str(self.cases_path)
        verdict["marker"] = completion_marker(inputs or {}, outputs, self.contract)
        write_json(self.out / "verdict.json", verdict)
        print(f"{self.card} finished: {json.dumps({k: v for k, v in verdict.items() if k in ('outcome', 'primary', 'exec')})}")
