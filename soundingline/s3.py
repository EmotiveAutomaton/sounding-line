"""Stage 3 shared schema and manifest machinery (brief section 6.5).

One place for: the cell schema, manifest read/write, produces-path construction, the
lineage allocator that assigns discovery versus confirmation by stable hash, and status
transitions. Every Stage 3 runner imports from here; no second filename convention may
exist (the L133 one-helper rule).
"""

from __future__ import annotations

import hashlib
import json
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


def load_manifest() -> list[dict]:
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


def save_manifest(cells: list[dict]) -> None:
    S3.mkdir(parents=True, exist_ok=True)
    MANIFEST_PATH.write_text(json.dumps(cells, indent=1), encoding="utf-8",
                             newline="\n")


def set_status(cell_id: str, status: str, closure_reason: str | None = None,
               actual_gpu_minutes: float | None = None) -> None:
    assert status in STATUSES, status
    cells = load_manifest()
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
    save_manifest(cells)


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
