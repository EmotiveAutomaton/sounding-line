"""Gate census of the local checkpoints (TODO (j), (p), (b); 2026-08-30). The joint and
appraisal tracks are gate-failed on both admitted readers (L278, L309: neither reads the
source register in full, neither maps stated latents onto a choice above uniform), and the
bridge owes a same-family second checkpoint that passes the reader gate (the 3B Qwen fails
the cheap-option floor, L282). This receipt runs the three gates, the Stage-5 reader gate
at ninety-six items per domain, the source-register gate, and the latent-to-choice gate, on
every instruction-tuned checkpoint on this machine not yet gated on all three, so the next
contract's reader question is answered from measurement. Execution is local only; no
checkpoint is downloaded. Writes results/phase_2_4_stage_5r/post/GATE_CENSUS.json; changes
nothing landed.

DESIGN CHECK (2026-08-30)
lessons read: LESSONS §3 (a gate dependency is the gate's verdict; "gate met" language only
  follows every gate passing under the card's own terms; an instrument gate carries its
  band's definition, so each gate's bands are the frozen ones, unchanged), §4 (a checkpoint
  that cannot load or answer is recorded as such, never dropped silently), §5 (one GPU
  lock per invocation; a produces guard).
expectations: under the null no local checkpoint passes all three gates and the third run
  of the joint and appraisal tracks stays blocked on a reader that does not exist here;
  under the alternative a checkpoint passes and is named with its numbers. The direction
  guarded is running the tracks a third time on a reader that passed the reader gate but
  not the track gate, or the reverse. The 3B's reader gate is taken from the ninety-six-item
  re-gate (REGATE_96.json) rather than re-run; its two track gates are new. Bands: the
  frozen ones (validity 0.95, accuracy 0.75, per option 0.5, position swing 0.10; register
  0.75 on both halves; latents-to-choice above uniform).
"""
from __future__ import annotations

import json
import random
import sys
import traceback

from pathlib import Path as _P
sys.path.insert(0, str(_P(__file__).resolve().parents[1]))
from runners import s5_receipts as R                                              # noqa: E402  (sets the environment first)
from runners import s5_lib                                                        # noqa: E402
from runners.s5_run_i import _gate_latent_to_choice, _gate_reader, _gate_source    # noqa: E402
from soundingline.s4 import now_iso                                                # noqa: E402

CANDIDATES = [("Qwen/Qwen2.5-3B-Instruct", "qwen"), ("allenai/OLMo-2-0425-1B-Instruct", "olmo"),
              ("HuggingFaceTB/SmolLM2-360M-Instruct", "smollm"), ("TinyLlama/TinyLlama-1.1B-Chat-v1.0", "llama")]
ANCHOR_FAMILY = "qwen"
REGATE = R.REPO / "results" / "phase_2_4_stage_5" / "post" / "REGATE_96.json"


def prior_reader_gate(name: str) -> dict | None:
    """The ninety-six-item re-gate's entry for a checkpoint it already measured (L282)."""
    if not REGATE.exists():
        return None
    try:
        rep = json.loads(REGATE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    for k in ("readers", "results", "by_reader"):
        if isinstance(rep.get(k), dict) and name in rep[k]:
            return dict(rep[k][name], source="REGATE_96.json")
    for r in (rep.get("rows") or []):
        if isinstance(r, dict) and r.get("reader") == name:
            return dict(r, source="REGATE_96.json")
    return None


def main() -> int:
    cands = CANDIDATES[2:3] if R.SMOKE else CANDIDATES
    n_axis, n_src, n_lat = (2, 3, 2) if R.SMOKE else (24, 48, 48)
    out = {"written_at": now_iso(), "design": "2", "checkpoints": {}, "bands": "the frozen Stage-5 gate bands"}
    with s5_lib.GpuSession("s5_gate_census") as gs:
        for name, fam in cands:
            rec = {"family": fam, "same_family_as_anchor": fam == ANCHOR_FAMILY, "reader_gate": None, "source_gate": None, "latent_gate": None, "error": None}
            out["checkpoints"][name] = rec
            if not s5_lib.model_available(name):
                rec["error"] = "checkpoint not present locally (execution is local only; nothing is downloaded)"
                continue
            try:
                model, tok, _ = s5_lib.load_model(name)
            except Exception as e:                                                # noqa: BLE001
                rec["error"] = f"load failed: {type(e).__name__}: {str(e)[:200]}"
                continue
            try:
                prior = None if R.SMOKE else prior_reader_gate(name)
                rec["reader_gate"] = prior or _gate_reader(model, tok, name, random.Random(s5_lib.SEED0 + 31), n_per_axis=n_axis, seed_key="s5census")
                rec["source_gate"] = _gate_source(model, tok, random.Random(s5_lib.SEED0 + 32), n=n_src)
                rec["latent_gate"] = _gate_latent_to_choice(model, tok, random.Random(s5_lib.SEED0 + 33), n=n_lat)
            except Exception as e:                                                # noqa: BLE001
                rec["error"] = f"gate failed: {type(e).__name__}: {str(e)[:200]}"
                traceback.print_exc()
            finally:
                s5_lib.free_model(model)
            rg = rec["reader_gate"] or {}
            rec["passes"] = {"reader": bool(rg.get("admitted")), "source": bool((rec["source_gate"] or {}).get("passed")),
                             "latent": bool((rec["latent_gate"] or {}).get("passed"))}
            rec["passes"]["all"] = all(rec["passes"].values())
            print(name, rec["passes"], rec["error"], flush=True)
        out["gpu_lock_s"] = gs.held_s
    ck = out["checkpoints"]
    out["summary"] = {"passing_all_three": [k for k, v in ck.items() if (v.get("passes") or {}).get("all")],
                      "passing_reader_gate": [k for k, v in ck.items() if (v.get("passes") or {}).get("reader")],
                      "passing_source_gate": [k for k, v in ck.items() if (v.get("passes") or {}).get("source")],
                      "passing_latent_gate": [k for k, v in ck.items() if (v.get("passes") or {}).get("latent")],
                      "same_family_second_checkpoint_for_the_bridge": [k for k, v in ck.items() if v["same_family_as_anchor"] and (v.get("passes") or {}).get("reader")],
                      "errors": {k: v["error"] for k, v in ck.items() if v["error"]}}
    R.write("GATE_CENSUS.json", out)
    print(json.dumps(out["summary"], indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
