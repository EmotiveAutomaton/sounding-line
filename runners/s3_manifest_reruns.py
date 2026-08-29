"""Stage 3 re-run cells owed by the Stage-4 theory errata (TODO R1-R5), registered BUILT
in the same edit that wrote their arms (LESSONS §5), 2026-08-28. Run once; idempotent.
Each cell writes a NEW produce beside its preserved first attempt.
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from soundingline.s3 import (load_manifest, make_cell, produces_path,            # noqa: E402
                             save_manifest, set_status)

Q3 = ["Qwen/Qwen2.5-1.5B-Instruct", "HuggingFaceTB/SmolLM2-1.7B-Instruct"]
CELLS = [
    make_cell("E24-S3-S05/X3b", "S",
              "Does the own-family margin survive the stake-free eraser once both families "
              "clear the survivor floor (regeneration attempts raised to eight)?",
              "artifact_lineage", ["allenai/OLMo-2-0425-1B-Instruct"] + Q3, 180,
              produces_path("S", "S05", "eraser3b"), minimum_n=40),
    make_cell("E24-S3-C06/R2", "C",
              "Does a stated hope bend the prediction away from the record when every "
              "generation is persisted, failure modes are separated, and a parser-free "
              "likelihood readout is the primary?",
              "episode", Q3, 45, produces_path("C", "C06", "verdict_b"), minimum_n=96),
    make_cell("E24-S3-H04/R3", "H",
              "Does contextual fit predict the writer's choice at the individual-suggestion "
              "grain (within-set rank; individually dismissed against selected)?",
              "writer_session", ["Qwen/Qwen2.5-1.5B-Instruct"], 30,
              produces_path("H", "H04", "verdict_b"), minimum_n=100),
    make_cell("E24-S3-XV4/R4", "L",
              "Is the transmission carrier nontrivial on an adequate held-out set "
              "(leave-one-seed-out over six seeds, exact swap null)?",
              "data_seed", ["HuggingFaceTB/SmolLM2-360M-Instruct"], 20,
              "results/phase_2_4_stage_3/X/XV4b_verdict.json", seeds=(1, 2, 3, 4, 5, 6)),
    make_cell("E24-S3-A07/R5", "A",
              "Is the affect representation used to infer a held-out maker: congruent "
              "against incongruent steering while predicting a maker the reader was not "
              "fit on?",
              "artifact", ["Qwen/Qwen2.5-1.5B-Instruct"], 40,
              produces_path("A", "A07", "verdict_b"), minimum_n=48),
]


def main() -> int:
    cells = load_manifest()
    have = {c["cell_id"] for c in cells}
    new = [c for c in CELLS if c["cell_id"] not in have]
    cells.extend(new)
    save_manifest(cells)
    for c in new:
        set_status(c["cell_id"], "BUILT")
    print(f"registered {len(new)} re-run cells ({[c['cell_id'] for c in new]}); "
          f"program now {len(cells)} cells")
    return 0


if __name__ == "__main__":
    sys.exit(main())
