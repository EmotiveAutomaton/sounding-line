"""Stage 6 card-run scaffold: the Stage-4/5 scaffold on the Stage-6 records and lanes.
Opens the card directory, reads the frozen design, resumes from cases.jsonl at unit
granularity, writes provenance rows and raw outputs, registers construction hashes, and
closes with metrics, a verdict, and a completion marker. Cards never write the manifest
(one writer, the scheduler). The 168-hour deadline is checked between units; a card
interrupted by it exits 3 with its rows checkpointed (test 16: a killed call resumes
without duplicating a completed unit).

DESIGN CHECK (2026-08-30)
lessons read: LESSONS §3, §5 (a library carries no gate of its own; the GPU lock is taken
  once per invocation by the engine, never per arm; a clean exit that wrote no produce is
  a failure).
gates: none here; the engines own the bands.
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
from runners.s4_worlds import construction_hash                                    # noqa: E402
from soundingline.stage6 import (S6, SMOKE, SPLITS, TRACK_OF, Lineages6,           # noqa: E402
                                 Manifest6, RunContract6, append_jsonl, card_dir,
                                 classify_outcome, code_hash, completion_marker,
                                 now_iso, read_jsonl, workload_locked, write_json)

LANE_ENV = "S6_SPLIT"
__all__ = ["SMOKE", "CardRun6", "DeadlineReached", "WorkloadNotLocked", "bench_lineages"]


class DeadlineReached(RuntimeError):
    pass


class WorkloadNotLocked(RuntimeError):
    """§11.2: scientific outputs may not be opened before the workload lock is written."""


def bench_lineages(card: str, domain: str, n: int, split: str = "discovery",
                   track: str | None = None, offset: int = 0) -> list[str]:
    """Deterministic lineage ids for a card's worlds. The COMMON BENCHMARK (M and P
    tracks) shares one id family (`MB`) so every architecture and endpoint sees the same
    worlds; the world tracks use their own construction card's family (C01/A01/V01/F01),
    so C03..C11 share C01's worlds and so on. Confirmation lanes offset the index."""
    fam = {"tournament": "MB", "prospective": "MB"}.get(track or "", None)
    if fam is None:
        fam = {"C": "C01", "A": "A01", "V": "V01", "F": "F01"}.get(card[0], card)
    base = {"discovery": 0, "pilot": 9000, "transfer": 20000, "confirmation": 30000, "attack": 40000}[split]
    base += int(os.environ.get("S6_WORLD_OFFSET", "0"))       # the expansion ladder's fresh-unit offset
    return [f"{fam}|{domain}|s0|w{base + offset + i:05d}|{split}" for i in range(n)]


class CardRun6:
    def __init__(self, card: str, cell_id: str | None = None, require_lock: bool = True):
        self.card = card
        self.split = os.environ.get(LANE_ENV, "discovery")
        assert self.split in SPLITS, self.split
        self.cell_id = cell_id or (card if self.split == "discovery" else f"{card}/{self.split}")
        override = os.environ.get("S6_CELL")
        if override and override.split("/")[0] == card and self.split == "discovery":
            self.cell_id = override
        self.out = card_dir(self.cell_id)
        self.contract = RunContract6.load()
        if self.contract is None:
            raise RuntimeError("no RUN_CONTRACT.json; run the scheduler's prepare first")
        if require_lock and self.split in ("discovery", "transfer", "confirmation") and not workload_locked():
            raise WorkloadNotLocked(f"{card}: the workload lock is not written; scientific outputs stay closed")
        self.design = self.contract.frozen("design") or {}
        self.readers = list((self.design.get("readers") or {}).keys())
        self.revisions = dict(self.design.get("readers") or {})
        self.capability = self.design.get("capability_gate") or {}    # I05's per-reader verdicts
        self.tier = self.design.get("tier", "minimum")
        self.L = Lineages6()
        self.manifest = Manifest6()
        self.cases_path = self.out / "cases.jsonl"
        self.raw_path = self.out / "raw_outputs.jsonl"
        self.states_dir = S6 / "states"
        self.code_hash = code_hash(REPO / "runners" / "stage6" / "engines.py",
                                   REPO / "runners" / "stage6" / "worlds.py",
                                   REPO / "runners" / "stage6" / "architectures.py",
                                   REPO / "soundingline" / "stage6.py")
        self.contract_hash = self.contract.hash()
        self.t0 = time.time()
        self.done = set()
        for r in read_jsonl(self.cases_path):
            self.done.add((r.get("model_id") or "-", r["unit_id"], r.get("arm") or "-"))
        self._buffer: list[dict] = []
        self._raw_buffer: list[dict] = []

    # units ---------------------------------------------------------------------------
    def register_world(self, lid: str, world: dict) -> str:
        clean = {k: v for k, v in world.items() if k not in ("cfg",)}
        h = construction_hash(clean)
        if lid in self.L.rows:
            self.L.mark_generated(lid, h)
        return h

    def is_done(self, reader: str | None, unit_id: str, arm: str | None = None) -> bool:
        return (reader or "-", unit_id, arm or "-") in self.done

    def check_deadline(self) -> None:
        if self.contract.deadline_passed():
            self.flush()
            raise DeadlineReached(self.card)

    # rows ----------------------------------------------------------------------------
    def row(self, unit_id: str, *, reader: str | None = None, arm: str | None = None,
            factors: dict | None = None, truth=None, truth_provenance: str = "construction",
            scores: dict | None = None, primary_score: float | None = None,
            valid: bool = True, validity_reason: str = "ok", budget: dict | None = None,
            state_ref: str | None = None, raw_ref: str | None = None,
            extra: dict | None = None) -> dict:
        r = {"card": self.card, "cell_id": self.cell_id, "unit_id": unit_id,
             "lineage_id": unit_id, "split": self.split, "lane": self.split,
             "model_id": reader or "-", "arm": arm or "-",
             "model_revision": self.revisions.get(reader, "-") if reader else "-",
             "factors": dict(factors or {}), "truth": truth, "truth_provenance": truth_provenance,
             "scores": dict(scores or {}), "primary_score": primary_score,
             "valid": valid, "validity_reason": validity_reason,
             "budget": budget, "state_ref": state_ref, "raw_ref": raw_ref,
             "code_hash": self.code_hash, "contract_hash": self.contract_hash,
             "at": now_iso(), "extra": dict(extra or {})}
        self._buffer.append(r)
        return r

    def raw(self, unit_id: str, reader: str | None, prompt_digest: str, text: str,
            extra: dict | None = None) -> str:
        ref = f"{self.card}:{unit_id}:{reader or '-'}:{len(self._raw_buffer) + 1}"
        self._raw_buffer.append({"raw_ref": ref, "card": self.card, "cell_id": self.cell_id,
                                 "unit_id": unit_id, "model_id": reader or "-",
                                 "prompt_sha": prompt_digest, "text": text[:2000],
                                 "at": now_iso(), **(extra or {})})
        return ref

    def save_state(self, unit_id: str, arm: str, reader: str | None, state: dict) -> str:
        self.states_dir.mkdir(parents=True, exist_ok=True)
        ref = f"{self.card}_{arm}_{(reader or 'x').split('/')[-1]}_{unit_id.replace('|', '-')}.json"
        write_json(self.states_dir / ref, state)
        return ref

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
        """Another card's landed rows (for contrasts against an already-run arm); the
        dependency is the scheduler's, the read is verbatim. Off the discovery split the
        read follows this run's split, so a confirmation contrast pairs confirmation rows
        (the hour-1.6 B01 defect: discovery rows share no unit ids with confirmation)."""
        d = (S6 / other_card) if self.split == "discovery" else (S6 / other_card / self.split)
        return read_jsonl(d / "cases.jsonl")

    # closing -------------------------------------------------------------------------
    def classify(self, contrast: dict, threshold: float) -> dict:
        if contrast.get("point") is None:
            return {"outcome": "VOID", "reason": "no units"}
        oc, why = classify_outcome(contrast["point"], contrast["lo"], contrast["hi"], threshold)
        return {"outcome": oc, "reason": why, "point": contrast["point"],
                "ci": [contrast["lo"], contrast["hi"]], "n_units": contrast.get("n_units"),
                "threshold": threshold, "perm_p": contrast.get("perm_p")}

    def threshold(self, default: float = 0.03) -> float:
        return (self.design.get("thresholds") or {}).get(self.card) or default

    def finish(self, metrics: dict, verdict: dict, gpu_lock_s: float = 0.0,
               rival: str | None = None, inputs: dict | None = None) -> None:
        self.flush()
        write_json(self.out / "metrics.json", {"card": self.card, "lane": self.split,
                                               "written_at": now_iso(), "env": s5_lib.env_versions(),
                                               **metrics})
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
