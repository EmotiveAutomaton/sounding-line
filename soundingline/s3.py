"""Stage 3 shared schema and manifest machinery (brief section 6.5).

One place for: the cell schema, manifest read/write, produces-path construction, the
lineage allocator that assigns discovery versus confirmation by stable hash, and status
transitions. Every Stage 3 runner imports from here; no second filename convention may
exist (the L133 one-helper rule).
"""

from __future__ import annotations

import contextlib
import hashlib
import json
import os
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
S3 = REPO / "results" / "phase_2_4_stage_3"
MANIFEST_PATH = S3 / "QUEUE_MANIFEST.json"
COVERAGE_PATH = S3 / "COVERAGE.json"

STATUSES = ("PLANNED", "BUILT", "VALIDATED", "RUNNING", "LANDED",
            "INSTRUMENT_FAILED", "SCIENTIFIC_CLOSED", "RESOURCE_BLOCKED")

# trunk -> minimum valid attempts (brief section 6.3)
TRUNK_FLOORS = {"S": 4, "D": 4, "E": 4, "A": 4, "H": 4, "V": 4,
                "L": 3, "M": 3, "C": 3}
TOTAL_ATTEMPT_FLOOR = 48


def produces_path(trunk: str, card: str, name: str) -> str:
    return f"results/phase_2_4_stage_3/{trunk}/{card}/{name}.json"


def lineage_side(lineage_id: str, reserve_frac: float = 0.25) -> str:
    """Discovery or confirmation, by stable hash of the lineage id. Frozen rule: the
    top reserve_frac of the hash space is confirmation, allocated before any scoring."""
    h = int(hashlib.md5(lineage_id.encode()).hexdigest()[:8], 16) / 0xFFFFFFFF
    return "confirmation" if h >= (1 - reserve_frac) else "discovery"


def card_hash(card: dict) -> str:
    frozen = {k: card[k] for k in sorted(card) if k not in
              ("status", "actual_gpu_minutes", "closure_reason", "card_hash",
               "landed_at")}
    return hashlib.sha256(json.dumps(frozen, sort_keys=True).encode()).hexdigest()[:16]


# ── manifest transactions (H3, 2026-08-28) ────────────────────────────────────────────
#
# `set_status` was load -> modify -> save with no mutual exclusion and a direct
# `write_text`. Stage 3 ran up to three runners at once, so two of them could each read the
# manifest, each change a DIFFERENT cell, and each write the whole list back: the first
# writer's status vanished with no error anywhere. The direct write could also leave a torn
# file if the process died mid-write, which the program validator then failed to parse.
#
# Two separate problems, two separate fixes -- and they are not the same fix:
#
#   * ATOMIC PUBLICATION (temp + os.replace) stops a torn file. It does NOT stop a lost
#     update: two atomic writes still leave only the second.
#   * The TRANSACTION LOCK stops the lost update, by holding read+modify+write together.
#
# The lock is held for one read-modify-write of a small JSON file -- milliseconds, never
# across an experiment. Contention is bounded, and failing to acquire RAISES rather than
# proceeding unlocked: a write that silently did not happen is the failure mode this whole
# section exists to remove.
#
# Windows note: os.replace onto a target another process holds open raises PermissionError,
# so the replace is retried briefly (the same sharing violation soundingline/s4.py records
# from the live Stage-4 run).

MANIFEST_LOCK = S3 / ".manifest.lock"
_LOCK_TIMEOUT_S = 30.0


class ManifestBusy(RuntimeError):
    """The manifest lock could not be acquired inside the timeout. Nothing was written."""


def load_manifest() -> list[dict]:
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


def _save_manifest_atomic(cells: list[dict]) -> None:
    S3.mkdir(parents=True, exist_ok=True)
    tmp = MANIFEST_PATH.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(cells, indent=1), encoding="utf-8", newline=chr(10))
    for attempt in range(20):
        try:
            os.replace(tmp, MANIFEST_PATH)
            return
        except PermissionError:
            if attempt == 19:
                raise
            time.sleep(0.25)


def save_manifest(cells: list[dict]) -> None:
    """Atomic whole-file publication. A caller that read-modify-writes MUST use
    `manifest_transaction` instead: atomicity alone cannot prevent a lost update."""
    _save_manifest_atomic(cells)


@contextlib.contextmanager
def manifest_transaction(timeout: float = _LOCK_TIMEOUT_S):
    """Hold the whole read/validate/modify/write. Yields the cell list; saves on clean exit.

    An exception inside the block releases the lock and writes NOTHING, so a failed write is
    never mistaken for a successful one.
    """
    S3.mkdir(parents=True, exist_ok=True)
    deadline = time.time() + timeout
    fd = None
    while True:
        try:
            fd = os.open(str(MANIFEST_LOCK), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            break
        except FileExistsError:
            if time.time() >= deadline:
                raise ManifestBusy(
                    f"{MANIFEST_LOCK} held for over {timeout:g}s; nothing was written. "
                    f"If no runner is alive, remove it by hand.") from None
            time.sleep(0.05)
    try:
        os.write(fd, str(os.getpid()).encode())
        os.close(fd)
        fd = None
        cells = load_manifest()
        yield cells
        _save_manifest_atomic(cells)
    finally:
        if fd is not None:
            os.close(fd)
        try:
            MANIFEST_LOCK.unlink()
        except OSError:
            pass


def set_status(cell_id: str, status: str, closure_reason: str | None = None,
               actual_gpu_minutes: float | None = None) -> None:
    assert status in STATUSES, status
    with manifest_transaction() as cells:
        hit = False
        for c in cells:
            if c["cell_id"] == cell_id:
                c["status"] = status
                if closure_reason is not None:
                    c["closure_reason"] = closure_reason
                if actual_gpu_minutes is not None:
                    c["actual_gpu_minutes"] = actual_gpu_minutes
                if status == "LANDED":
                    c["landed_at"] = time.strftime("%Y-%m-%d %H:%M")
                hit = True
        assert hit, f"unknown cell {cell_id}"


def make_cell(cell_id: str, trunk: str, question: str, unit: str, models: list[str],
              est_gpu_min: float, produces: str, lane: str = "discovery",
              seeds=(1, 2, 3), minimum_n: int = 0, data_split: str = "") -> dict:
    c = {"cell_id": cell_id, "trunk": trunk, "lane": lane, "question": question,
         "independent_unit": unit, "models": models, "data_split": data_split,
         "seeds": list(seeds), "minimum_n": minimum_n,
         "estimated_gpu_minutes": est_gpu_min, "actual_gpu_minutes": None,
         "produces": produces, "status": "PLANNED", "closure_reason": None}
    c["card_hash"] = card_hash(c)
    return c
