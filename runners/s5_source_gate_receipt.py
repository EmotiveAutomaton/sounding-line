"""Post-run receipt (TODO (t), 2026-08-29): the source-world register gate re-measured on
the repaired text (design 2: the intensity closers state gravity without asking for
anything). The second contract's frozen gate was measured on the pre-repair text (L284);
this receipt says whether the register is legible to the two readers now. Writes
results/phase_2_4_stage_5r/post/SOURCE_GATE_REPAIRED.json; changes nothing landed.

DESIGN CHECK (2026-08-29)
lessons read: LESSONS §3 (an instrument gate carries its band's definition; a construction
  whose levels are not semantically distinct is repaired before the gate is read as a
  reader limit), §5 (a tool run takes the GPU lock).
expectations: under the null (the readers cannot read the register) the action question
  stays at or under chance on the repaired text; under the alternative it clears the 0.75
  band. The direction guarded is reading a construction defect as a reader limit. Receipt
  only; no band beyond the gate's own; nothing landed changes.
"""
from __future__ import annotations

import os
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ["S5_DESIGN"] = "2"

from runners import s5_lib                                                        # noqa: E402
from runners.s5_run_i import _gate_source                                          # noqa: E402
from soundingline.s4 import now_iso, write_json                                    # noqa: E402

OUT = Path(__file__).resolve().parents[1] / "results" / "phase_2_4_stage_5r" / "post"


def main() -> int:
    out = {"written_at": now_iso(), "design": "2", "readers": {}}
    with s5_lib.GpuSession("s5_source_gate_receipt") as gs:
        for reader in s5_lib.READERS:
            model, tok, _ = s5_lib.load_model(reader)
            try:
                out["readers"][reader] = _gate_source(model, tok, random.Random(s5_lib.SEED0 + 17), n=48)
            finally:
                s5_lib.free_model(model)
            r = out["readers"][reader]
            print(reader, "passed" if r["passed"] else "failed", {d: (round(m["arousal_acc"], 2), round(m["action_acc"], 2)) for d, m in r["domains"].items()}, flush=True)
        out["gpu_lock_s"] = gs.held_s
    OUT.mkdir(parents=True, exist_ok=True)
    write_json(OUT / "SOURCE_GATE_REPAIRED.json", out)
    print("wrote", OUT / "SOURCE_GATE_REPAIRED.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
