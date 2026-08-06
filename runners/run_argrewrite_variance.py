"""Does the WOBBLE inside a piece carry the maker? — the veneer claim, on human text at last.

── THE QUESTION IN PLAIN LANGUAGE ────────────────────────────────────────────────────────────

The curator's own primary detector when he reads by hand is not how polished a piece is, but **how
much the polish varies from beginning to end.** A writer reaches for a professional register, and
then relaxes out of it. Keeping up a performance costs effort, so the performance is what slips, and
the slip is where the person shows.

**Every measure this project has ever built takes an average over a whole document and throws the
variation away.**

── WHY THIS CORPUS AND NOT THE OTHERS ────────────────────────────────────────────────────────

We tried this once on the intent ladder and it found nothing, which was uninformative: every ladder
artifact is machine-written, and **a machine has no performance to slip.** A null there is the
absence of the thing, not evidence against it.

ArgRewrite is human, and it is the version the literature has *not* pre-empted. Within-document
variation is a mature field — it is GPTZero's "burstiness" (variance of per-sentence perplexity),
Koppel's "unmasking" from 2004, and a CLEF shared task running since 2018. **What none of them does
is measure the variance of anything other than perplexity or surface style.** This runner measures
the variance of 342 linguistic features and, separately, of the reader's internal affective response.

── THE TEST ──────────────────────────────────────────────────────────────────────────────────

For each author, split each draft into fixed windows and compute, per feature, the **coefficient of
variation** across windows — the wobble relative to its own size, so large features do not
automatically look variable.

Then ask two questions, both paired within author so between-person differences contribute nothing:

    1. does the wobble CHANGE as the author revises?      draft 1 vs draft 3
    2. does the wobble differ from the MEAN's behaviour?  variance-only survivors

**Pre-registered.** Pass needs a signed-rank result surviving Benjamini-Yekutieli correction across
all features, **and** at least one survivor that the mean does not also find — otherwise the wobble
is just a noisier way of measuring the average.

**Length matters less here than usual** (windows are fixed size) but is not zero, so every draft is
truncated to that author's shortest before windowing.

**No direction predicted.** Revision might smooth a piece out — the maker converging, ironing the
performance flat — or roughen it. Committing to no sign means we cannot claim one afterwards.
"""

from __future__ import annotations

import argparse
import contextlib
import io
import json
import statistics
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

RESULTS = REPO / "results" / "argrewrite"
WINDOW = 150
MIN_WINDOWS = 3


def windows(text: str, n: int = WINDOW) -> list[str]:
    w = text.split()
    return [" ".join(w[i:i + n]) for i in range(0, len(w) - n + 1, n)]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--cap", type=int, default=0)
    args = ap.parse_args()

    import numpy as np                                               # noqa: PLC0415
    import pandas as pd                                              # noqa: PLC0415
    from scipy import stats                                          # noqa: PLC0415

    from runners.run_argrewrite import load                          # noqa: PLC0415
    from soundingline.measures.features import extract               # noqa: PLC0415

    authors = load()
    if args.cap:
        authors = dict(list(authors.items())[: args.cap])
    print(f"{len(authors)} authors; windows of {WINDOW} words, "
          f"minimum {MIN_WINDOWS} per draft\n", flush=True)

    buf = io.StringIO()
    rows = []
    for i, (aid, drafts) in enumerate(authors.items()):
        n = min(len(t.split()) for t in drafts.values())
        drafts = {d: " ".join(t.split()[:n]) for d, t in drafts.items()}
        ws = {d: windows(t) for d, t in drafts.items()}
        if any(len(v) < MIN_WINDOWS for v in ws.values()):
            continue
        with contextlib.redirect_stdout(buf):
            feats = {d: [extract(w) for w in v] for d, v in ws.items()}
        rows.append({"author": aid, "feats": feats, "n_windows": len(ws[1])})
        if (i + 1) % 10 == 0:
            print(f"  {i + 1}/{len(authors)}", flush=True)

    print(f"\n{len(rows)} authors usable, "
          f"median {statistics.median(r['n_windows'] for r in rows):.0f} windows each\n")

    keys = sorted(set.intersection(*(set(f) for r in rows for d in (1, 3) for f in r["feats"][d])))

    def stat_for(r, d, k, kind):
        v = [w.get(k) for w in r["feats"][d] if k in w and np.isfinite(w.get(k, np.nan))]
        if len(v) < MIN_WINDOWS:
            return np.nan
        m, sd = float(np.mean(v)), float(np.std(v, ddof=1))
        return sd / abs(m) if kind == "cv" and abs(m) > 1e-9 else (m if kind == "mean" else 0.0)

    out = {}
    for kind in ("cv", "mean"):
        recs = []
        for k in keys:
            a = np.array([stat_for(r, 1, k, kind) for r in rows])
            b = np.array([stat_for(r, 3, k, kind) for r in rows])
            ok = np.isfinite(a) & np.isfinite(b)
            if ok.sum() < 30 or np.allclose(a[ok], b[ok]):
                continue
            try:
                _, p = stats.wilcoxon(a[ok], b[ok])
            except ValueError:
                continue
            d = b[ok] - a[ok]
            recs.append({"feature": k, "p": float(p), "median_delta": float(np.median(d)),
                         "sign_agreement": float(np.mean(np.sign(d) == np.sign(np.median(d))))})
        tbl = pd.DataFrame(recs).sort_values("p")
        n = len(tbl)
        c = sum(1.0 / j for j in range(1, n + 1))
        tbl["p_adj"] = (tbl["p"] * n / (np.arange(n) + 1) * c).cummax().clip(upper=1.0)
        surv = tbl[tbl["p_adj"] < 0.05]
        out[kind] = {"n_tested": n, "n_survive": int(len(surv)),
                     "survivors": surv.head(40).to_dict("records")}
        print(f"{kind.upper():<6} {n} features tested, {len(surv)} survive correction")
        for _, r in surv.head(8).iterrows():
            print(f"        {r['feature']:<32}{r['median_delta']:>+12.4f}"
                  f"{r['sign_agreement']:>8.0%}{r['p_adj']:>12.2e}")

    cv_only = sorted({s["feature"] for s in out["cv"]["survivors"]}
                     - {s["feature"] for s in out["mean"]["survivors"]})
    print(f"\nwobble finds {out['cv']['n_survive']}, average finds {out['mean']['n_survive']}, "
          f"**wobble-only {len(cv_only)}**")
    for f in cv_only[:10]:
        print(f"    {f}")
    print("\n>>> " + ("THE WOBBLE CARRIES SOMETHING THE AVERAGE DOES NOT."
                      if cv_only else
                      "The wobble finds nothing the average does not. On human text, with the "
                      "maker held fixed, within-document variation is not adding information."))

    RESULTS.mkdir(parents=True, exist_ok=True)
    (RESULTS / "variance.json").write_text(json.dumps(
        {"n_authors": len(rows), "window": WINDOW, "results": out, "cv_only": cv_only},
        indent=2), encoding="utf-8", newline="\n")
    print(f"\nwrote {(RESULTS / 'variance.json').relative_to(REPO)}")


if __name__ == "__main__":
    main()
