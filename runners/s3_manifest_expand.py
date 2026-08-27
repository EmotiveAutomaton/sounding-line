"""Stage 3 Wave 0: frozen expansion ladder instantiation (brief sections 6.3 and 7).

The calibrated mandatory queue is 82.6 GPU-hours, under the 120-hour envelope, so the
ladder expands INDEPENDENT INFORMATION in its frozen order before launch: (1) independent
makers and data seeds, (2) sibling checkpoints, (3) the third family beyond its S01 entry,
(4) a held-out artifact domain. Rungs 5-8 stay reserved for landed-branch expansion during
the week. Run once after s3_manifest_init.
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from soundingline.s3 import (load_manifest, make_cell, produces_path,            # noqa: E402
                             save_manifest)

Q3 = ["Qwen/Qwen2.5-1.5B-Instruct", "HuggingFaceTB/SmolLM2-1.7B-Instruct"]


def main() -> int:
    cells = load_manifest()
    have = {c["cell_id"] for c in cells}
    E = []

    def a(c):
        if c["cell_id"] not in have:
            E.append(c)

    # rung 1 — independent makers and data seeds (double instantiations)
    a(make_cell("E24-S3-S02/X1", "S", "S02 with a second independent adapter cohort (fresh data seeds)", "adapter_lineage", Q3, 8 * 60, produces_path("S", "S02", "cohort2"), seeds=(4, 5, 6)))
    a(make_cell("E24-S3-L01/X1", "L", "L01 with six additional independent data seeds", "data_seed", ["HuggingFaceTB/SmolLM2-360M-Instruct"], 6 * 60, produces_path("L", "L01", "seeds7to12"), seeds=(7, 8, 9, 10, 11, 12)))
    a(make_cell("E24-S3-D01/X1", "D", "D01 with four additional independent role assignments", "episode_lineage", Q3, 6 * 60, produces_path("D", "D01", "roles5to8")))
    a(make_cell("E24-S3-E03/X1", "E", "E03 with six additional independent maker policies", "maker_policy", Q3, 5 * 60, produces_path("E", "E03", "policies7to12")))
    a(make_cell("E24-S3-V01/X1", "V", "V01 with four additional utility profiles and fresh maker instances", "maker_instance", Q3, 7 * 60, produces_path("V", "V01", "profiles5to8")))

    # rung 2 — sibling checkpoints
    a(make_cell("E24-S3-S01/X2", "S", "S01 read by sibling checkpoints (0.5B, 3B, 360M) to split exact-weight from lineage", "maker", ["Qwen/Qwen2.5-0.5B", "Qwen/Qwen2.5-3B", "HuggingFaceTB/SmolLM2-360M-Instruct"], 4 * 60, produces_path("S", "S01", "siblings")))

    # rung 3 — third family beyond its S01 entry
    a(make_cell("E24-S3-S03/X3", "S", "S03 distance gradient extended through the third family", "maker_lineage", Q3 + ["third-family-after-gate"], 3 * 60, produces_path("S", "S03", "family3")))
    a(make_cell("E24-S3-S05/X3", "S", "S05 erasure ladder with the third family as an additional eraser", "artifact_lineage", ["third-family-after-gate"], 3 * 60, produces_path("S", "S05", "eraser3")))

    # rung 4 — held-out artifact domain
    a(make_cell("E24-S3-E03/X4", "E", "E03 route factorial on a held-out second domain", "maker_policy", Q3, 5 * 60, produces_path("E", "E03", "domain2")))
    a(make_cell("E24-S3-C01/X4", "C", "C01 late-fusion ruler on a held-out domain", "episode", Q3, 3 * 60, produces_path("C", "C01", "domain2")))
    a(make_cell("E24-S3-V04/X4", "V", "V04 cross-context prediction into a third structurally equivalent domain", "maker_instance", Q3, 4 * 60, produces_path("V", "V04", "domain3")))
    a(make_cell("E24-S3-A06/X4", "A", "A06 expressivity suppression on a second episode domain", "episode", Q3, 3 * 60, produces_path("A", "A06", "domain2")))

    cells.extend(E)
    save_manifest(cells)
    total = sum(c["estimated_gpu_minutes"] for c in cells)
    print(f"added {len(E)} expansion cells; program now {len(cells)} cells, "
          f"{total / 60:.1f} calibrated GPU-hours")
    return 0


if __name__ == "__main__":
    sys.exit(main())
