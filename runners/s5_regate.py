"""Post-run re-gate (TODO (a), 2026-08-29): the readers the Stage-5 gate refused at 48 items
(SmolLM2-1.7B-Instruct on the position band by 0.004; Qwen2.5-3B-Instruct on the cheap
option) re-gated at 96 items per domain on FRESH items under the same bands, to tell a
band-edge miss from a stable failure. Writes results/phase_2_4_stage_5/post/REGATE_96.json,
outside the frozen cells; changes nothing the stage landed.

DESIGN CHECK (2026-08-29)
lessons read: LESSONS §3 (an instrument gate carries its band's definition, not only its
  number; a gate's band derived from its probe count), §5 (a tool run takes the GPU lock).
gates: the same four bands as I02 (validity at or above 0.95, accuracy at or above 0.75,
  every option at or above 0.5, the accuracy difference between two orderings at or under
  0.10). under the null (a stable failure) the refused reader misses at least one band again
  at 96 items; under the alternative (a band-edge miss) it passes every band at 96; the
  failure direction guarded is admitting a reader on a lucky second draw, so the verdict is
  written as a re-gate receipt and never re-opens the closed stage's reader set.
verdict bands, exhaustive (no silent interval): ADMITTED_AT_96 when every band passes in
  both domains; REFUSED_AT_96 otherwise, with the failing band named.
"""
from __future__ import annotations

import json
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from runners import s5_lib                                                        # noqa: E402
from runners.s5_run_i import _gate_reader                                          # noqa: E402
from soundingline.s4 import now_iso, write_json                                    # noqa: E402
from soundingline.stage5 import S5                                                 # noqa: E402

READERS = ["HuggingFaceTB/SmolLM2-1.7B-Instruct", "Qwen/Qwen2.5-3B-Instruct", "Qwen/Qwen2.5-1.5B-Instruct"]
BANDS = {"validity": 0.95, "accuracy": 0.75, "per_option": 0.5, "swing_pp": 0.10}


def failing_bands(rep: dict) -> list[str]:
    out = []
    for dom, m in rep["domains"].items():
        if m["validity"] < BANDS["validity"]:
            out.append(f"{dom}:validity")
        if min(m["accuracy"], m["accuracy_second_permutation"]) < BANDS["accuracy"]:
            out.append(f"{dom}:accuracy")
        if min(m["per_option"].values()) < BANDS["per_option"]:
            out.append(f"{dom}:per_option")
        if m["position_swing"] > BANDS["swing_pp"]:
            out.append(f"{dom}:swing")
    return out


def main() -> int:
    out = S5 / "post"
    out.mkdir(parents=True, exist_ok=True)
    result = {"written_at": now_iso(), "n_per_axis": 24, "items_per_domain": 96, "bands": BANDS, "readers": {}}
    with s5_lib.GpuSession("s5_regate") as gs:
        for reader in READERS:
            model, tok, _ = s5_lib.load_model(reader)
            try:
                rep = _gate_reader(model, tok, reader, random.Random(s5_lib.SEED0 + 9600), n_per_axis=24, seed_key="s5regate")
            finally:
                s5_lib.free_model(model)
            fails = failing_bands(rep)
            rep["failing_bands"] = fails
            rep["verdict"] = "ADMITTED_AT_96" if not fails else "REFUSED_AT_96"
            result["readers"][reader] = rep
            print(reader, rep["verdict"], fails, json.dumps({d: {k: round(v, 3) if isinstance(v, float) else v for k, v in m.items() if k != "per_option"} for d, m in rep["domains"].items()}), flush=True)
        result["gpu_lock_s"] = gs.held_s
    write_json(out / "REGATE_96.json", result)
    print("wrote", out / "REGATE_96.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
