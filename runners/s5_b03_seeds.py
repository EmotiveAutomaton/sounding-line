"""Post-run receipt (TODO (e), 2026-08-29): L255's random arm was quiet (−0.09, +0.04 by fold)
and B03's on the same reader, artifacts, locus, dose, folds, and per-artifact random scheme
was +0.40 (L260); the only nominal difference is the seed base (Stage 3: 40000; Stage 5:
55100). This runner scores the zero, congruent, and random arms under BOTH seed bases on the
anchor, so the two random draws are compared on one code path. Writes
results/phase_2_4_stage_5/post/B03_SEEDS.json, outside the frozen cells.

DESIGN CHECK (2026-08-29)
lessons read: LESSONS §3 (a quiet control in one run licenses nothing until its replicate is
  quiet too; a control with one realization per artifact and no second seed is one draw),
  §5 (a tool run takes the GPU lock).
expectations: under the null (the random arm's mean does not depend on the seed base) both
  draws sit within each other's intervals and the discrepancy between L255 and L260 lies in
  the code path, not the seeds; under the alternative (seed luck) the 40000 draw is quiet
  and the 55100 draw is loud on this one code path. The direction guarded is reading one
  draw's quiet as selectivity. Receipt only; no band, no verdict, nothing landed changes.
"""
from __future__ import annotations

import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from runners import s5_lib                                                        # noqa: E402
from runners.s5_run_b import (ANCHOR_MODEL, CYCLE, TENDENCIES, _dose_ladder,      # noqa: E402
                              _fold_directions, _score, _steer_ctx, load_scene_artifacts)
from soundingline.s4 import now_iso, write_json                                    # noqa: E402
from soundingline.stage5 import S5                                                 # noqa: E402

SEED_BASES = {"stage3_L255": 40000, "stage5_B03": 55100}


def main() -> int:
    import torch                                                                  # noqa: PLC0415
    from soundingline.probe.interventions import capture_block_states             # noqa: PLC0415
    arts = load_scene_artifacts("scenes")
    tends = sorted(TENDENCIES)
    rows = []
    with s5_lib.GpuSession("s5_b03_seeds") as gs:
        model, tok, _ = s5_lib.load_model(ANCHOR_MODEL)
        try:
            states = [[h.mean(0) for h in capture_block_states(model, tok, a["body"], device="cuda")] for a in arts]
            n_blocks = len(states[0])
            third = n_blocks // 3
            locus = list(range(third, 2 * third, 2))
            for fit_fam, test_fam in (("smollm", "qwen"), ("qwen", "smollm")):
                fit_idx = [i for i, a in enumerate(arts) if a["fam"] == fit_fam]
                test_idx = [i for i, a in enumerate(arts) if a["fam"] == test_fam]
                cents, dirs = _fold_directions(states, arts, fit_idx, locus, tends)
                mean_norm = float(torch.stack([states[i][locus[0]] for i in fit_idx]).norm(dim=1).mean())
                ladder, alpha, frac = _dose_ladder(model, tok, locus, dirs, tends, mean_norm)
                fold = f"{fit_fam}->{test_fam}"
                for i in test_idx:
                    a = arts[i]
                    body = (f"Someone wrote this short passage about a situation they were in:\n\"{a['body']}\"\n\n"
                            f"Which impulse was driving the writer?")
                    arms = {"zero": (None, 0.0), "congruent": ({b: dirs[b][a["tend"]] for b in locus}, alpha),
                            "incongruent": ({b: dirs[b][CYCLE[a["tend"]]] for b in locus}, alpha)}
                    for name, base in SEED_BASES.items():
                        g = torch.Generator().manual_seed(base + 7100 + i)
                        rd = {}
                        for b in locus:
                            d = dirs[b][a["tend"]]
                            r = torch.randn(d.shape[0], generator=g)
                            r = r - (r @ d) * d
                            rd[b] = r / r.norm()
                        arms[f"random|{name}"] = (rd, alpha)
                    for arm, (dmap, al) in arms.items():
                        rng = random.Random(55100 + 7000 + i)
                        with _steer_ctx(model, locus, dmap, al):
                            r = _score(model, tok, body, tends, rng)
                        ls = s5_lib.log_score(r["probs"], a["tend"]) if r["valid"] else None
                        rows.append({"fold": fold, "arm": arm, "i": i, "truth": a["tend"], "ls": ls, "dose_frac": frac, "alpha": al})
        finally:
            s5_lib.free_model(model)
        held = gs.held_s
    zero = {(r["fold"], r["i"]): r["ls"] for r in rows if r["arm"] == "zero" and r["ls"] is not None}
    out = {"written_at": now_iso(), "reader": ANCHOR_MODEL, "n_artifacts": len(arts), "seed_bases": SEED_BASES, "contrasts": {}, "by_fold": {}}
    for arm in sorted({r["arm"] for r in rows} - {"zero"}):
        diffs = {f"{r['fold']}|{r['i']}": r["ls"] - zero[(r["fold"], r["i"])] for r in rows
                 if r["arm"] == arm and r["ls"] is not None and (r["fold"], r["i"]) in zero}
        out["contrasts"][arm] = s5_lib.cluster_bootstrap_ci(diffs, 55100 + 3)
        for fold in ("smollm->qwen", "qwen->smollm"):
            sub = [v for k, v in diffs.items() if k.startswith(fold)]
            out["by_fold"][f"{arm}|{fold}"] = {"mean": (sum(sub) / len(sub)) if sub else None, "n": len(sub)}
    out["gpu_lock_s"] = held
    (S5 / "post").mkdir(parents=True, exist_ok=True)
    write_json(S5 / "post" / "B03_SEEDS.json", out)
    for arm, c in out["contrasts"].items():
        print(arm, {k: (round(v, 3) if isinstance(v, float) else v) for k, v in c.items()}, {k: round(v["mean"], 3) for k, v in out["by_fold"].items() if k.startswith(arm) and v["mean"] is not None})
    print("wrote", S5 / "post" / "B03_SEEDS.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
