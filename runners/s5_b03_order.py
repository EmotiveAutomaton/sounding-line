"""Post-run receipt (2026-08-29): is the bridge's loud random arm an option-order artifact?
In the card's sequence one random generator is shared across arms, so each arm's four-way
question is asked under a different option order; the seed receipt gave every arm the same
order and found the random arm quiet. On 24 held-out artifacts of one fold, the zero,
congruent, and random arms are scored under (i) one fixed order per artifact shared by all
arms and (ii) an independent order per arm, each over four order seeds. Writes
results/phase_2_4_stage_5/post/B03_ORDER.json.

DESIGN CHECK (2026-08-29)
lessons read: LESSONS §3 (a paired contrast must hold the readout's nuisance fixed across
  arms or average it out with enough draws), §4 (hooks removed and replay verified: done,
  B03_LEAK.json).
expectations: under the null (no order artifact) the random arm's mean is the same under
  shared and independent orders; under the alternative the random arm is quiet under a
  shared order and loud under independent orders, and the congruent arm's size changes
  little. The direction guarded is a control read as loud because its question was asked
  in a different order from the zero arm's. Receipt only; no band.
"""
from __future__ import annotations

import random
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from runners import s5_lib                                                        # noqa: E402
from runners.s5_run_b import (ANCHOR_MODEL, TENDENCIES, _dose_ladder,             # noqa: E402
                              _fold_directions, _score, _steer_ctx, load_scene_artifacts)
from soundingline.s4 import now_iso, write_json                                    # noqa: E402
from soundingline.stage5 import S5                                                 # noqa: E402


def main() -> int:
    import torch                                                                  # noqa: PLC0415
    from soundingline.probe.interventions import capture_block_states             # noqa: PLC0415
    arts = load_scene_artifacts("scenes")
    tends = sorted(TENDENCIES)
    out = {"written_at": now_iso(), "reader": ANCHOR_MODEL, "rows": []}
    with s5_lib.GpuSession("s5_b03_order") as gs:
        model, tok, _ = s5_lib.load_model(ANCHOR_MODEL)
        try:
            states = [[h.mean(0) for h in capture_block_states(model, tok, a["body"], device="cuda")] for a in arts]
            n_blocks = len(states[0])
            third = n_blocks // 3
            locus = list(range(third, 2 * third, 2))
            fit_idx = [i for i, a in enumerate(arts) if a["fam"] == "smollm"]
            test_idx = [i for i, a in enumerate(arts) if a["fam"] == "qwen"][:24]
            cents, dirs = _fold_directions(states, arts, fit_idx, locus, tends)
            mean_norm = float(torch.stack([states[i][locus[0]] for i in fit_idx]).norm(dim=1).mean())
            ladder, alpha, frac = _dose_ladder(model, tok, locus, dirs, tends, mean_norm)
            for i in test_idx:
                a = arts[i]
                body = (f"Someone wrote this short passage about a situation they were in:\n\"{a['body']}\"\n\n"
                        f"Which impulse was driving the writer?")
                g = torch.Generator().manual_seed(55100 + 7100 + i)
                rd = {}
                for b in locus:
                    d = dirs[b][a["tend"]]
                    r = torch.randn(d.shape[0], generator=g)
                    r = r - (r @ d) * d
                    rd[b] = r / r.norm()
                arms = {"zero": (None, 0.0), "congruent": ({b: dirs[b][a["tend"]] for b in locus}, alpha), "random": (rd, alpha)}
                for order_seed in range(4):
                    for scheme in ("shared", "independent"):
                        for name, (dmap, al) in arms.items():
                            rng = random.Random(1000 * order_seed + (0 if scheme == "shared" else {"zero": 1, "congruent": 2, "random": 3}[name]))
                            with _steer_ctx(model, locus, dmap, al):
                                r = _score(model, tok, body, tends, rng)
                            out["rows"].append({"i": i, "truth": a["tend"], "order_seed": order_seed, "scheme": scheme, "arm": name,
                                                "ls": s5_lib.log_score(r["probs"], a["tend"]) if r["valid"] else None})
        finally:
            s5_lib.free_model(model)
        out["gpu_lock_s"] = gs.held_s
    summ = {}
    for scheme in ("shared", "independent"):
        for arm in ("congruent", "random"):
            d = []
            for i in {r["i"] for r in out["rows"]}:
                for s in range(4):
                    z = [r["ls"] for r in out["rows"] if r["i"] == i and r["order_seed"] == s and r["scheme"] == scheme and r["arm"] == "zero"]
                    x = [r["ls"] for r in out["rows"] if r["i"] == i and r["order_seed"] == s and r["scheme"] == scheme and r["arm"] == arm]
                    if z and x and z[0] is not None and x[0] is not None:
                        d.append(x[0] - z[0])
            summ[f"{scheme}|{arm}_minus_zero"] = {"mean": statistics.mean(d), "sd": statistics.pstdev(d), "n": len(d)}
    out["summary"] = summ
    (S5 / "post").mkdir(parents=True, exist_ok=True)
    write_json(S5 / "post" / "B03_ORDER.json", out)
    for k, v in summ.items():
        print(k, {kk: round(vv, 3) if isinstance(vv, float) else vv for kk, vv in v.items()})
    print("wrote", S5 / "post" / "B03_ORDER.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
