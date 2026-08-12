"""G107 — the label-permutation null for the no-maker control's flagship concentration.

The re-adjudication (L26) found the flagship fires the joint rule at 5 of 29 layers on maker-less
text, overlapping its held-out-ladder survivors 3-of-5. Clustered luck, or a real label leak? This
computes the actual chance rates instead of arguing about them.

── THE TEST ──────────────────────────────────────────────────────────────────────────────────

From the saved per-artifact signal matrices (`--save-signals` runs): permute the arbitrary rung
labels 2,000 times; per permutation, recount layers passing the computable joint rule
(|rho| > 0.2 AND |partial after length| > 0.2, conditioned on the observed random-direction null
passes), and recount the overlap with the ladder survivor set.

    CLUSTERED-LUCK   observed count and overlap sit inside the permutation distribution (p > 0.05)
    LABEL-LEAK       either exceeds it at p < 0.05 — the control is flagging a real problem at
                     exactly those layers, and the flagship survivor list carries an asterisk
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

SRC = REPO / "results" / "layer_correlation"
OUT = REPO / "results" / "audit"
LADDER_SURVIVORS = [12, 13, 17, 19, 21]   # ladder2 Qwen-1.5B strict survivors (L26 re-check)


def main() -> None:
    import argparse                                                   # noqa: PLC0415

    import numpy as np                                                # noqa: PLC0415
    from scipy.stats import rankdata, spearmanr                       # noqa: PLC0415

    # --corpora merges same-model signal files for the powered form (L40 was UNDECIDED at 36
    # artifacts; the near-significance policy says raise n with the construction frozen)
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpora", default="nomaker",
                    help="comma list of corpus tags whose _sig files merge (same reader model)")
    ap.add_argument("--perms", type=int, default=2000)
    ap.add_argument("--out-tag", default="")
    args = ap.parse_args()

    sigs, grps, wdss, beats_list = [], [], [], []
    for tag in args.corpora.split(","):
        f = SRC / f"{tag}_Qwen2.5-1.5B_sig.json"
        if not f.exists():
            print(f"needs the --save-signals run for {tag} first (queued before this stage)")
            sys.exit(1)
        d = json.loads(f.read_text(encoding="utf-8"))
        sigs.append(np.array(d["signals"]))
        grps.append(np.array(d["groups"], float))
        wdss.append(np.array(d["words"], float))
        beats_list.append(np.array([o["beats_null"] for o in d["layers"]], bool))
    sig = np.vstack(sigs)                 # artifacts x layers
    grp = np.concatenate(grps)
    wds = np.concatenate(wdss)
    # a layer is eligible if it beat its direction-null in any merged read; the widening applies
    # to observed and permuted counts alike, so the comparison stays fair
    beats = np.logical_or.reduce(beats_list)
    n_art, n_lay = sig.shape
    print(f"{n_art} artifacts x {n_lay} layers from {args.corpora}; "
          f"{beats.sum()} beat their direction-null")

    def rres(a, b):
        a, b = rankdata(a), rankdata(b)
        return a - np.polyval(np.polyfit(b, a, 1), b)

    def joint_layers(labels):
        hits = []
        for L in range(n_lay):
            if not beats[L]:
                continue
            rho = spearmanr(labels, sig[:, L]).statistic
            if abs(rho) <= 0.2:
                continue
            pr = spearmanr(rres(sig[:, L], wds), rres(labels, wds)).statistic
            if abs(pr) > 0.2:
                hits.append(L)
        return hits

    obs = joint_layers(grp)
    obs_overlap = len(set(obs) & set(LADDER_SURVIVORS))
    print(f"observed: {len(obs)} joint layers {obs}, overlap with ladder survivors {obs_overlap}")

    rng = np.random.default_rng(0)
    counts, overlaps = [], []
    for i in range(args.perms):
        perm = rng.permutation(grp)
        h = joint_layers(perm)
        counts.append(len(h))
        overlaps.append(len(set(h) & set(LADDER_SURVIVORS)))
        if (i + 1) % 500 == 0:
            print(f"  {i + 1}/{args.perms}", flush=True)
    counts, overlaps = np.array(counts), np.array(overlaps)
    p_count = float((counts >= len(obs)).mean())
    p_overlap = float((overlaps >= obs_overlap).mean())
    print(f"\n  P(joint count >= {len(obs)})   = {p_count:.4f}  (null mean {counts.mean():.2f})")
    print(f"  P(overlap    >= {obs_overlap})   = {p_overlap:.4f}  (null mean {overlaps.mean():.2f})")
    # failure to reject is not evidence for luck (the L40 relabel); the sub-.05 verdict is a
    # leak either way, and the other side is named for what it is at the n it ran at
    verdict = ("LABEL-LEAK" if min(p_count, p_overlap) < 0.05
               else f"NO-LEAK-DETECTED (n={n_art})")
    print(f"\n  >>> {verdict}")

    OUT.mkdir(parents=True, exist_ok=True)
    name = f"nomaker_permutation{args.out_tag}.json"
    (OUT / name).write_text(json.dumps(
        {"corpora": args.corpora, "n_artifacts": n_art,
         "observed_layers": obs, "observed_overlap": obs_overlap,
         "p_count": p_count, "p_overlap": p_overlap,
         "null_count_mean": float(counts.mean()), "null_overlap_mean": float(overlaps.mean()),
         "n_permutations": args.perms, "verdict": verdict}, indent=2),
        encoding="utf-8", newline="\n")
    print(f"wrote {(OUT / name).relative_to(REPO)}")


if __name__ == "__main__":
    main()
