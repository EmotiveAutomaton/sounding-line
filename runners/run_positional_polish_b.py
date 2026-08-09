"""PD-1b — does the PD-1 inversion survive a sampling-variance-matched null?

L53 found depth-side features moving MORE than polish-side within essays, against the prediction.
The named confound: depth features are sparse counts (high per-window sampling noise), polish
features dense indices (smooth by construction). This run cancels the sampling floor: each
feature's observed within-essay positional variance is divided by its own null variance under
window shuffling ACROSS essays (same windows, same counts, no positional structure). A feature
whose movement is only sampling noise lands at ratio ~1; genuine positional structure exceeds it.

    DEPTH-MOVES     depth-side ratios exceed polish-side, paired p < 0.05 -- the inversion is real
    STATIONARY      depth ratios sit at/below polish once sampling variance cancels
    BOTH-NOISE      neither side exceeds 1 meaningfully -- 80-word windows carry no positional
                    structure at all and PD-1 needs a different operationalisation
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

RESULTS = REPO / "results" / "positional_polish"
CACHE = REPO / "results" / "features" / "argrewrite_w80.json"

POLISH_PATTERNS = ("readability", "flesch", "ttr", "type_token", "punct", "exclam",
                   "uppercase", "smog", "coleman", "kincaid", "ari_", "lix", "rix",
                   "unique_tokens")
DEPTH_PATTERNS = ("caus", "conc", "cond", "osub", "whcl", "whsub", "whobj", "thac",
                  "thvc", "tsub", "tobj", "nomz", "bypa", "pastp", "wzpast", "wzpres",
                  "presp", "pire", "dependency_distance")
N_PERM = 200


def main() -> None:
    import numpy as np                                                # noqa: PLC0415
    from scipy import stats                                           # noqa: PLC0415

    items = [it for it in json.loads(CACHE.read_text(encoding="utf-8"))["items"]
             if it.get("n_windows", 0) >= 4]
    keys = sorted(set.intersection(*(set(it["windows"][0]) for it in items)))
    pol = [k for k in keys if any(p in k.lower() for p in POLISH_PATTERNS)]
    dep = [k for k in keys if any(p in k.lower() for p in DEPTH_PATTERNS)]
    sizes = [it["n_windows"] for it in items]
    print(f"{len(items)} essays, {len(pol)} polish / {len(dep)} depth features")

    rng = np.random.default_rng(11)

    def feature_ratio(k: str) -> float | None:
        pool = np.array([float(w.get(k, 0.0) or 0.0) for it in items for w in it["windows"]])
        pool = np.nan_to_num(pool)
        if pool.std() <= 0:
            return None
        obs = _mean_within(pool, sizes)
        nulls = []
        for _ in range(N_PERM):
            nulls.append(_mean_within(rng.permutation(pool), sizes))
        null = float(np.mean(nulls))
        return obs / null if null > 0 else None

    def _mean_within(flat: "np.ndarray", ns: list[int]) -> float:
        import numpy as np                                            # noqa: PLC0415
        out, i = [], 0
        for n in ns:
            seg = flat[i:i + n]
            out.append(float(np.var(seg - seg.mean())))
            i += n
        return float(np.mean(out))

    # known-answer gate: a planted alternating series must exceed its shuffle null; a planted
    # constant-per-essay series (pure between-essay variance) must land at ratio ~<=1
    import numpy as np                                                # noqa: PLC0415
    gate_sizes = [6] * 40
    alt = np.tile([1.0, 9.0], 120)
    per_essay = np.repeat(rng.normal(size=40), 6)
    g_alt = _mean_within(alt, gate_sizes) / np.mean(
        [_mean_within(rng.permutation(alt), gate_sizes) for _ in range(100)])
    g_flat = _mean_within(per_essay, gate_sizes) / np.mean(
        [_mean_within(rng.permutation(per_essay), gate_sizes) for _ in range(100)])
    print(f"known-answer gate: alternating ratio {g_alt:.2f} (needs >1.2), "
          f"between-only ratio {g_flat:.2f} (needs <1.0)")
    if not (g_alt > 1.2 and g_flat < 1.0):
        print(">>> GATE-FAILED")
        sys.exit(1)

    pr = [r for r in (feature_ratio(k) for k in pol) if r is not None]
    dr = [r for r in (feature_ratio(k) for k in dep) if r is not None]
    pr_a, dr_a = np.array(pr), np.array(dr)
    u, p = stats.mannwhitneyu(dr_a, pr_a, alternative="two-sided")
    pm, dm = float(np.median(pr_a)), float(np.median(dr_a))
    if pm <= 1.02 and dm <= 1.02:
        verdict = "BOTH-NOISE"
    elif dm > pm and p < 0.05:
        verdict = "DEPTH-MOVES (inversion survives the matched null)"
    elif pm > dm and p < 0.05:
        verdict = "POLISH-MOVES (the prediction, once sampling variance cancels)"
    else:
        verdict = "NO-ASYMMETRY at matched sampling variance"
    print(f"median ratio polish {pm:.3f} vs depth {dm:.3f}  p={p:.4f}\n  >>> {verdict}")

    RESULTS.mkdir(parents=True, exist_ok=True)
    (RESULTS / "summary_b.json").write_text(json.dumps(
        {"n_essays": len(items), "polish_median_ratio": pm, "depth_median_ratio": dm,
         "p": float(p), "gate": {"alternating": float(g_alt), "between_only": float(g_flat)},
         "verdict": verdict, "polish_ratios": pr, "depth_ratios": dr}, indent=2),
        encoding="utf-8", newline="\n")
    print(f"wrote {(RESULTS / 'summary_b.json').relative_to(REPO)}")


if __name__ == "__main__":
    main()
