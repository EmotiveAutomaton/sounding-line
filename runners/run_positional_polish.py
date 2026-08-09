"""G119 / PD-1 — the definitional polish/depth test, first run ever.

PD-1: depth-side quantities show smaller between-position variance than polish-side quantities
within one artifact. *If both move equally, the distinction is not real and the decision-traces
file is wrong* — its own words. Needs the small-window feature cache (`argrewrite_w80`).

First-pass operationalisation, pre-registered here: polish-side features are the reader-facing
surface (readability indices, punctuation variety, type-token ratio, emphasis); depth-side are the
problem-facing structure (conditionals, causal connectives, clause depth, nominalisation). Both
sets are named lists below — arguable, which is why this is a first pass and says so.

    POLISH-MOVES   polish-set positional variance > depth-set, paired across essays, p < 0.05
    NO-ASYMMETRY   they move equally — the file's own falsifier fires
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
                   "uppercase", "smog", "coleman", "kincaid", "ari_")
DEPTH_PATTERNS = ("cond", "caus", "subord", "nominal", "clause", "infinitive",
                  "agentless", "conc", "wh_")


def main() -> None:
    import numpy as np                                                # noqa: PLC0415
    from scipy import stats                                           # noqa: PLC0415

    if not CACHE.exists():
        print("needs the small-window cache first (queued before this stage)")
        sys.exit(1)
    items = json.loads(CACHE.read_text(encoding="utf-8"))["items"]
    keys = sorted(set.intersection(*(set(it["windows"][0]) for it in items
                                     if it.get("windows"))))
    pol = [k for k in keys if any(p in k.lower() for p in POLISH_PATTERNS)]
    dep = [k for k in keys if any(p in k.lower() for p in DEPTH_PATTERNS)]
    print(f"{len(pol)} polish-side features, {len(dep)} depth-side features")

    def posvar(it, ks):
        # mean over features of the within-artifact positional variance of the z-scored series
        vals = []
        for k in ks:
            series = np.array([float(w.get(k, 0.0) or 0.0) for w in it["windows"]])
            if series.std() > 0:
                vals.append(float(np.var((series - series.mean()) / (series.std() + 1e-9))))
        return float(np.mean(vals)) if vals else None

    pairs = []
    for it in items:
        if it.get("n_windows", 0) < 4:
            continue
        pv, dv = posvar(it, pol), posvar(it, dep)
        if pv is not None and dv is not None:
            pairs.append((it["id"], pv, dv))
    print(f"{len(pairs)} essays with >= 4 windows")
    pv = np.array([p[1] for p in pairs])
    dv = np.array([p[2] for p in pairs])
    _, p = stats.wilcoxon(pv, dv) if len(pairs) > 10 else (None, 1.0)
    direction = float(np.median(pv - dv))
    verdict = ("POLISH-MOVES" if direction > 0 and p < 0.05 else
               "DEPTH-MOVES (inverted!)" if direction < 0 and p < 0.05 else "NO-ASYMMETRY")
    print(f"median polish var {np.median(pv):.3f} vs depth var {np.median(dv):.3f}  "
          f"paired p={p:.4f}\n  >>> {verdict}")

    RESULTS.mkdir(parents=True, exist_ok=True)
    (RESULTS / "summary.json").write_text(json.dumps(
        {"n": len(pairs), "polish_median": float(np.median(pv)),
         "depth_median": float(np.median(dv)), "p": float(p), "verdict": verdict,
         "polish_features": pol, "depth_features": dep}, indent=2),
        encoding="utf-8", newline="\n")
    print(f"wrote {(RESULTS / 'summary.json').relative_to(REPO)}")


if __name__ == "__main__":
    main()
