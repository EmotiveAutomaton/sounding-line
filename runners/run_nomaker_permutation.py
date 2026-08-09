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
    import numpy as np                                                # noqa: PLC0415
    from scipy.stats import rankdata, spearmanr                       # noqa: PLC0415

    f = SRC / "nomaker_Qwen2.5-1.5B_sig.json"
    if not f.exists():
        print("needs the --save-signals nomaker run first (queued before this stage)")
        sys.exit(1)
    d = json.loads(f.read_text(encoding="utf-8"))
    sig = np.array(d["signals"])          # artifacts x layers
    grp = np.array(d["groups"], float)
    wds = np.array(d["words"], float)
    beats = np.array([o["beats_null"] for o in d["layers"]], bool)
    n_art, n_lay = sig.shape
    print(f"{n_art} artifacts x {n_lay} layers; {beats.sum()} beat their direction-null")

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
    for i in range(2000):
        perm = rng.permutation(grp)
        h = joint_layers(perm)
        counts.append(len(h))
        overlaps.append(len(set(h) & set(LADDER_SURVIVORS)))
        if (i + 1) % 500 == 0:
            print(f"  {i + 1}/2000", flush=True)
    counts, overlaps = np.array(counts), np.array(overlaps)
    p_count = float((counts >= len(obs)).mean())
    p_overlap = float((overlaps >= obs_overlap).mean())
    print(f"\n  P(joint count >= {len(obs)})   = {p_count:.4f}  (null mean {counts.mean():.2f})")
    print(f"  P(overlap    >= {obs_overlap})   = {p_overlap:.4f}  (null mean {overlaps.mean():.2f})")
    verdict = "LABEL-LEAK" if min(p_count, p_overlap) < 0.05 else "CLUSTERED-LUCK"
    print(f"\n  >>> {verdict}")

    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "nomaker_permutation.json").write_text(json.dumps(
        {"observed_layers": obs, "observed_overlap": obs_overlap,
         "p_count": p_count, "p_overlap": p_overlap,
         "null_count_mean": float(counts.mean()), "null_overlap_mean": float(overlaps.mean()),
         "n_permutations": 2000, "verdict": verdict}, indent=2),
        encoding="utf-8", newline="\n")
    print(f"wrote {(OUT / 'nomaker_permutation.json').relative_to(REPO)}")


if __name__ == "__main__":
    main()
