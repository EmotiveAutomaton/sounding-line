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
                   "uppercase", "smog", "coleman", "kincaid", "ari_", "lix", "rix",
                   "unique_tokens")
# v2: v1's descriptive words missed Biber's tag codes (3 hits of ~20 intended); mapped to the
# actual inventory BEFORE the first valid run — v1 scored zero essays, so nothing was fit to
DEPTH_PATTERNS = ("caus", "conc", "cond", "osub", "whcl", "whsub", "whobj", "thac",
                  "thvc", "tsub", "tobj", "nomz", "bypa", "pastp", "wzpast", "wzpres",
                  "presp", "pire", "dependency_distance")


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

    # v3: v2 z-scored each series by its own std before taking variance, and the variance of a
    # z-scored series is 1 by construction -- the criterion could not fail (both medians landed at
    # 0.9999999, p=5e-44 on epsilon arithmetic; quarantined in v2_zvar_degenerate/). The honest
    # unit: positional variance in CORPUS-scale units, so features are comparable while the
    # within-artifact movement stays the measured quantity.
    corpus_std = {}
    for k in keys:
        allvals = np.array([float(w.get(k, 0.0) or 0.0) for it in items
                            for w in it.get("windows", [])])
        corpus_std[k] = float(np.nanstd(allvals))

    def posvar(it, ks):
        vals = []
        for k in ks:
            if corpus_std[k] <= 0 or not np.isfinite(corpus_std[k]):
                continue
            series = np.array([float(w.get(k, 0.0) or 0.0) for w in it["windows"]])
            series = series[np.isfinite(series)]
            if len(series) < 4:
                continue
            vals.append(float(np.var((series - series.mean()) / corpus_std[k])))
        return float(np.mean(vals)) if vals else None

    # known-answer gate, per the standing rule: a planted flat series must score near zero and a
    # planted moving series must score high, or the statistic cannot measure what it claims
    flat = {"windows": [{"ka": 5.0} for _ in range(6)], "n_windows": 6}
    moving = {"windows": [{"ka": float(v)} for v in (1, 9, 2, 8, 1, 9)], "n_windows": 6}
    corpus_std["ka"] = 3.0
    ka_flat, ka_move = posvar(flat, ["ka"]), posvar(moving, ["ka"])
    print(f"known-answer gate: flat {ka_flat:.4f} moving {ka_move:.4f}")
    if not (ka_flat < 0.01 and ka_move > 0.5):
        print(">>> GATE-FAILED — statistic cannot separate flat from moving; no verdict")
        sys.exit(1)
    del corpus_std["ka"]

    pairs = []
    for it in items:
        if it.get("n_windows", 0) < 4:
            continue
        pv, dv = posvar(it, pol), posvar(it, dep)
        if pv is not None and dv is not None:
            pairs.append((it["id"], pv, dv))
    print(f"{len(pairs)} essays with >= 4 windows")
    if len(pairs) < 12:
        # no summary written on purpose: the produces-guard must stay missing so the
        # stage refires once the cache is rebuilt at the real window size
        print(f">>> NEEDS-DATA — only {len(pairs)} usable essays; cache or corpus is wrong")
        sys.exit(1)
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
