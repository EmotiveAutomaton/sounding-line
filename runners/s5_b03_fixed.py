"""Post-run receipt (2026-08-29): the B03 specificity battery re-run with the OPTION ORDER
HELD FIXED across arms. The card (and L255 before it) drew a fresh option order per arm from
one shared generator, and the letter-likelihood readout carries a two-nat letter effect
(zero-arm log score −2.71 with the truth at A, −0.75 at B; B03_ORDER.json, B03_LEAK.json),
so every paired contrast carried an item-level noise of two nats and a standard error of
0.17 at 135 artifacts; the random arm's +0.40 (L260) and the receipts' 0.00 are draws of that
noise. Here every arm of an artifact is asked under the same order, so the pairing holds.
Writes results/phase_2_4_stage_5/post/B03_FIXED_ORDER.json, outside the frozen cells.

DESIGN CHECK (2026-08-29)
lessons read: LESSONS §3 (a paired contrast must hold the readout's nuisance fixed across
  arms; a quiet control in one run licenses nothing until its replicate is quiet), §4
  (hooks removed and replay verified, B03_LEAK.json).
expectations: under the null (no selective effect) the congruent arm equals the random arm
  within the fixed-order standard error (about 0.11); under the alternative the congruent
  arm exceeds the random, permuted-label, and reversed arms by at least the 0.03 threshold
  with the random arm inside 0.02 of zero. The direction guarded is a control read as loud
  from order noise. Receipt only: the closed stage's verdicts stand as landed; these numbers
  are the standing ones for the theory row.
"""
from __future__ import annotations

import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from runners import s5_lib                                                        # noqa: E402
from runners.s5_run_b import (CHECKPOINTS, CYCLE, TENDENCIES, _dose_ladder,       # noqa: E402
                              _fold_directions, _score, _steer_ctx, load_scene_artifacts)
from soundingline.s4 import now_iso, write_json                                    # noqa: E402
from soundingline.stage5 import S5                                                 # noqa: E402

ARMS = ("congruent", "incongruent", "random", "shifted", "random_blocks", "half", "double", "reversed", "permuted")


def main() -> int:
    import argparse                                                               # noqa: PLC0415
    import torch                                                                  # noqa: PLC0415
    from soundingline.probe.interventions import capture_block_states             # noqa: PLC0415
    ap = argparse.ArgumentParser()
    ap.add_argument("--checkpoint", default="anchor", choices=sorted(CHECKPOINTS))
    ap.add_argument("--domain", default="scenes", choices=["scenes", "scenes2"])
    args = ap.parse_args()
    reader_name = CHECKPOINTS[args.checkpoint]
    tag = "" if (args.checkpoint, args.domain) == ("anchor", "scenes") else f"_{args.checkpoint}_{args.domain}"
    arts = load_scene_artifacts(args.domain)
    tends = sorted(TENDENCIES)
    rows = []
    with s5_lib.GpuSession("s5_b03_fixed") as gs:
        model, tok, _ = s5_lib.load_model(reader_name)
        try:
            states = [[h.mean(0) for h in capture_block_states(model, tok, a["body"], device="cuda")] for a in arts]
            n_blocks = len(states[0])
            third = n_blocks // 3
            locus = list(range(third, 2 * third, 2))
            shifted = [min(n_blocks - 1, b + 3) for b in locus]
            rnd_blocks = random.Random(55100 + 11).sample([b for b in range(2, n_blocks - 1) if b not in locus], len(locus))
            for fit_fam, test_fam in (("smollm", "qwen"), ("qwen", "smollm")):
                fit_idx = [i for i, a in enumerate(arts) if a["fam"] == fit_fam]
                test_idx = [i for i, a in enumerate(arts) if a["fam"] == test_fam]
                cents, dirs = _fold_directions(states, arts, fit_idx, locus, tends)
                lab = [arts[i]["tend"] for i in fit_idx]
                random.Random(55100 + 9).shuffle(lab)
                fake = [dict(arts[i], tend=lab[j]) for j, i in enumerate(fit_idx)]
                _, perm_dirs = _fold_directions([states[i] for i in fit_idx], fake, list(range(len(fake))), locus, tends)
                mean_norm = float(torch.stack([states[i][locus[0]] for i in fit_idx]).norm(dim=1).mean())
                ladder, alpha, frac = _dose_ladder(model, tok, locus, dirs, tends, mean_norm)
                fold = f"{fit_fam}->{test_fam}"
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
                    cong = {b: dirs[b][a["tend"]] for b in locus}
                    arms = {"zero": (None, 0.0, locus), "congruent": (cong, alpha, locus),
                            "incongruent": ({b: dirs[b][CYCLE[a["tend"]]] for b in locus}, alpha, locus),
                            "random": (rd, alpha, locus),
                            "shifted": ({sb: dirs[b][a["tend"]] for sb, b in zip(shifted, locus)}, alpha, shifted),
                            "random_blocks": ({rb: dirs[b][a["tend"]] for rb, b in zip(rnd_blocks, locus)}, alpha, rnd_blocks),
                            "half": (cong, alpha / 2, locus), "double": (cong, alpha * 2, locus),
                            "reversed": (cong, -alpha, locus),
                            "permuted": ({b: perm_dirs[b][a["tend"]] for b in locus}, alpha, locus)}
                    for name, (dmap, al, blocks) in arms.items():
                        rng = random.Random(55100 + 7000 + i)                     # the SAME order for every arm
                        with _steer_ctx(model, blocks, dmap, al):
                            r = _score(model, tok, body, tends, rng)
                        rows.append({"fold": fold, "arm": name, "i": i, "truth": a["tend"],
                                     "ls": s5_lib.log_score(r["probs"], a["tend"]) if r["valid"] else None,
                                     "truth_letter": (r.get("labels") or {}).get(a["tend"]), "dose_frac": frac})
        finally:
            s5_lib.free_model(model)
        held = gs.held_s
    zero = {(r["fold"], r["i"]): r["ls"] for r in rows if r["arm"] == "zero" and r["ls"] is not None}
    out = {"written_at": now_iso(), "reader": reader_name, "checkpoint": args.checkpoint, "domain": args.domain,
           "n_artifacts": len(arts), "order": "fixed per artifact across arms",
           "contrasts": {}, "by_fold": {}, "gpu_lock_s": held}
    for arm in ARMS:
        diffs = {f"{r['fold']}|{r['i']}": r["ls"] - zero[(r["fold"], r["i"])] for r in rows
                 if r["arm"] == arm and r["ls"] is not None and (r["fold"], r["i"]) in zero}
        out["contrasts"][arm] = s5_lib.cluster_bootstrap_ci(diffs, 55100 + 3)
        for fold in ("smollm->qwen", "qwen->smollm"):
            sub = [v for k, v in diffs.items() if k.startswith(fold)]
            out["by_fold"][f"{arm}|{fold}"] = {"mean": (sum(sub) / len(sub)) if sub else None, "n": len(sub)}
    (S5 / "post").mkdir(parents=True, exist_ok=True)
    write_json(S5 / "post" / f"B03_FIXED_ORDER{tag}.json", out)
    for arm, c in out["contrasts"].items():
        print(f"{arm}: {c['point']:+.3f} [{c['lo']:+.3f}, {c['hi']:+.3f}]  folds "
              f"{out['by_fold'][arm + '|smollm->qwen']['mean']:+.3f} / {out['by_fold'][arm + '|qwen->smollm']['mean']:+.3f}")
    print("wrote", S5 / "post" / f"B03_FIXED_ORDER{tag}.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
