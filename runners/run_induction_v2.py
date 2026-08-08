"""The induction control, rebuilt with the dose removed from its regressors (G75 / L22).

── WHY THE OLD CONTROL WAS BROKEN ────────────────────────────────────────────────────────────

The audit (FINDINGS L22) found that the induction control's regressor matrix — the binary indicator
of which specifications were drawn — has a row-sum equal to the rung. **The regressors contain the
dose.** A ridge model recovers rung from the sum alone, so what the control removed was set by the
regulariser, not the design. At the extreme ladder's top rung the pool holds exactly 60
specifications, all drawn, so the regressor block is constant there.

Consequences already recorded: L1's survival was against a control that can absorb the true effect
(stronger than designed); L17's failure was by construction; L2's kills cannot distinguish
*induced-by-which-specs* from *responds-to-how-many*.

── THE FIX ───────────────────────────────────────────────────────────────────────────────────

**Centre the indicator within rung.** Subtract each column's within-rung mean, so the centred matrix
carries only *which* specifications were drawn given *how many* — the dose is arithmetically absent.
An out-of-fold ridge prediction from the centred matrix captures pure specification-identity
structure; what survives its removal (plus length) is the effect the old control was supposed to
isolate and never did.

Both controls are run side by side, with the smoking-gun diagnostic printed for each: the
correlation between the control's own prediction and rung. **Old control: expected high — it was
predicting the dose. New control: expected ~0 by construction.**

This runner also saves per-artifact rows (ratio, words, rung, spec indices) so every future
re-analysis is CPU-only.

── PRE-REGISTERED, BEFORE THE RUN ────────────────────────────────────────────────────────────

    SURVIVES     the ratio's relationship with rung is significant (p < 0.05, negative) after
                 removing length and the WITHIN-RUNG specification identity
    DEAD         it is not
    predictions  ladder2 SURVIVES (it survived the harsher, dose-eating control, so it should
                 survive the fair one). ladder3 is genuinely open — this is its first
                 interpretable induction test.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

RESULTS = REPO / "results" / "induction_v2"

LADDERS = {
    "ladder":  {"seed": 70000,  "topic_off": 0, "pool": "base"},
    "ladder2": {"seed": 90000,  "topic_off": 5, "pool": "base"},
    "ladder3": {"seed": 110000, "topic_off": 3, "pool": "extended"},
}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus", default="ladder2", choices=sorted(LADDERS))
    ap.add_argument("--model", default=None)
    ap.add_argument("--device", default="cuda")
    args = ap.parse_args()

    import random                                                     # noqa: PLC0415

    import numpy as np                                                # noqa: PLC0415
    from scipy import stats                                           # noqa: PLC0415
    from scipy.stats import rankdata                                  # noqa: PLC0415
    from sklearn.linear_model import RidgeCV                          # noqa: PLC0415
    from sklearn.model_selection import KFold                         # noqa: PLC0415

    from soundingline.probe.activations import (DEFAULT_MODEL, Reader,  # noqa: PLC0415
                                                fit_directions)
    from runners.run_b import split                                   # noqa: PLC0415
    from runners.run_layer_ratio import ratio_for                     # noqa: PLC0415
    from runners.make_intent_ladder import SPECS as BASE              # noqa: PLC0415

    cfg = LADDERS[args.corpus]
    if cfg["pool"] == "extended":
        from runners.make_ladder3 import SPECS as POOL                # noqa: PLC0415
    else:
        POOL = BASE
    pool = list(POOL)

    model_name = args.model or DEFAULT_MODEL
    print(f"loading {model_name} ...", flush=True)
    reader = Reader(model_name, device=args.device)
    fit, _ = split()
    dirs = fit_directions(reader, fit)

    d = REPO / "corpora" / args.corpus
    man = json.loads((d / "manifest.json").read_text(encoding="utf-8"))
    rows = []
    for it in man["items"]:
        p = d / f"{it['id']}.txt"
        rung = it.get("rung")
        if not p.exists() or not isinstance(rung, int):
            continue
        text = p.read_text(encoding="utf-8")
        idx = int(it["id"].split("_")[1])
        # reconstruction arithmetic verified against recorded per-item seeds/topics, 2026-08-08
        drawn = (random.Random(cfg["seed"] + rung * 1000 + idx).sample(pool, rung)
                 if rung > 0 else [])
        rows.append({"id": it["id"], "rung": rung, "words": len(text.split()),
                     "spec_idx": sorted(pool.index(s) for s in drawn),
                     "ratio": ratio_for(reader, dirs, text)})
        if len(rows) % 25 == 0:
            print(f"  {len(rows)} scored", flush=True)
    n = len(rows)
    print(f"{args.corpus}: {n} artifacts\n", flush=True)

    y = np.array([r["ratio"] for r in rows])
    rung = np.array([r["rung"] for r in rows], dtype=float)
    words = np.array([r["words"] for r in rows], dtype=float)
    X = np.zeros((n, len(pool)))
    for i, r in enumerate(rows):
        X[i, r["spec_idx"]] = 1.0

    # within-rung centring: subtract each column's mean inside its rung stratum
    Xc = X.copy()
    for g in sorted(set(rung)):
        m = rung == g
        Xc[m] -= Xc[m].mean(0)

    def oof_pred(M):
        pred = np.zeros(n)
        for tr, te in KFold(5, shuffle=True, random_state=0).split(M):
            pred[te] = RidgeCV(alphas=np.logspace(-2, 3, 20)).fit(M[tr], y[tr]).predict(M[te])
        return pred

    def rres(a, b):
        a, b = rankdata(a), rankdata(b)
        return a - np.polyval(np.polyfit(b, a, 1), b)

    raw, p_raw = stats.spearmanr(rung, y)
    lenc, p_len = stats.spearmanr(rres(y, words), rres(rung, words))

    out = {"corpus": args.corpus, "model": model_name, "n": n,
           "pool_size": len(pool), "raw": float(raw), "p_raw": float(p_raw),
           "length_removed": float(lenc), "p_length": float(p_len), "rows": rows}
    print(f"{'control':<28}{'pred~rung':>10}{'both_removed':>14}{'p':>10}")
    print("-" * 64)
    for name, M in [("OLD (dose in regressors)", X), ("NEW (within-rung centred)", Xc)]:
        pred = oof_pred(M)
        leak = float(stats.spearmanr(pred, rung).statistic)
        resid = y - pred
        rho, p = stats.spearmanr(rres(resid, words), rres(rung, words))
        out[name.split()[0].lower()] = {"pred_vs_rung": leak,
                                        "both_removed": float(rho), "p_both": float(p)}
        print(f"{name:<28}{leak:>+10.3f}{rho:>+14.3f}{p:>10.4f}")

    new = out["new"]
    verdict = "SURVIVES" if (new["p_both"] < 0.05 and new["both_removed"] < 0) else "DEAD"
    out["verdict"] = verdict
    print(f"\n  old control's prediction correlates with rung at "
          f"{out['old']['pred_vs_rung']:+.3f} — the dose leak, now measured")
    print(f"  new control's prediction correlates with rung at "
          f"{new['pred_vs_rung']:+.3f} — should be ~0 by construction")
    print(f"\n  >>> {verdict}")

    # cross-family runs get their own file — an untagged name would overwrite the flagship result
    stem = args.corpus if args.model is None else f"{args.corpus}_{args.model.split('/')[-1]}"
    RESULTS.mkdir(parents=True, exist_ok=True)
    (RESULTS / f"{stem}.json").write_text(json.dumps(out, indent=2),
                                                 encoding="utf-8", newline="\n")
    print(f"\nwrote {(RESULTS / f'{args.corpus}.json').relative_to(REPO)}")


if __name__ == "__main__":
    main()
