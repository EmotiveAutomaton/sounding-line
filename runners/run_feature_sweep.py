"""The 342-feature sweep — B1's variance test, and a re-validation of everything we have claimed.

Runs off the cache built by `runners/build_features.py`. Two jobs, one pass.

── JOB 1 · B1, THE VARIATION OF THE VENEER ───────────────────────────────────────────────────

`docs/theory/CURATOR_GUESSES.md` B1 is the curator's primary detector and **no measure in this
project has ever kept a within-artifact spread.** Every one takes a whole-document mean.

So each of the 342 features is turned into three candidate measures and all three are scored:

    whole      the feature over the entire artifact           <- what we have always done
    mean       its mean across windows                        <- control: should track `whole`
    cv         its COEFFICIENT OF VARIATION across windows    <- B1. Never tried.

**Coefficient of variation, not raw variance**, because raw variance scales with the mean and would
just rediscover whichever features happen to be large. CV is sd/|mean|, so it asks *how much does
this wobble relative to its own size*, which is what "the performance slips" actually means.

**The comparison is the test, not the count.** If `cv` finds features that `whole` and `mean` do not,
B1 has something. If it finds the same ones, it is a noisier way of measuring the mean.

── JOB 2 · RE-VALIDATION ─────────────────────────────────────────────────────────────────────

Every population we have made a claim about, re-scored with 342 features under
Benjamini-Yekutieli correction:

    ladder        does ANYTHING rank the five rungs?          re-tests "the ladder fails"
    ladder2       the held-out replication                    the honest version of the above
    nomaker       N28 -- does anything move where there is no maker?
    gate3         do the two halves differ at all?            re-tests "uninterpretable"

**An empty result is a real finding and a strong one.** 342 features, every one validated somewhere
in the literature, carrying nothing about specified intent would be a far better negative than ten
hand-written misses.

── THE TRAP THIS RUNNER IS BUILT AROUND ──────────────────────────────────────────────────────

342 features x 3 forms x 4 populations = ~4,100 tests. At p < 0.05 that is **205 false positives by
construction.** Every score goes through `measures/select.py` (Benjamini-Yekutieli, valid under the
arbitrary dependence our overlapping feature libraries guarantee), and the uncorrected count is
printed beside the corrected one **specifically so the gap is visible.**

Anything surviving here is a CANDIDATE, not a result. It still has to clear echo, length, transfer
and rung -1 before it means anything.
"""

from __future__ import annotations

import argparse
import json
import math
import statistics
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

CACHE = REPO / "results" / "features"
OUT = REPO / "results" / "feature_sweep"


def load(corpus: str) -> dict | None:
    p = CACHE / f"{corpus}.json"
    if not p.exists():
        return None
    return json.loads(p.read_text(encoding="utf-8"))


def forms(items: list[dict]) -> dict[str, tuple[list[str], list[list[float]]]]:
    """Build the three feature matrices: whole, windowed mean, windowed CV."""
    usable = [it for it in items if it.get("enough_windows")]
    if not usable:
        return {}
    keys = sorted(set.intersection(*(set(it["whole"]) for it in usable)))

    def finite(col: list[float]) -> bool:
        return all(math.isfinite(v) for v in col)

    out: dict[str, tuple[list[str], list[list[float]]]] = {}

    whole = {k: [it["whole"][k] for it in usable] for k in keys}
    whole = {k: v for k, v in whole.items() if finite(v)}
    out["whole"] = (list(whole), [list(r) for r in zip(*whole.values())])

    means, cvs = {}, {}
    for k in keys:
        mcol, ccol = [], []
        for it in usable:
            # a single inf/nan in one window would otherwise poison the whole feature, and
            # statistics.stdev raises an opaque AttributeError on non-finite input
            vals = [float(w[k]) for w in it["windows"] if k in w and math.isfinite(w.get(k, math.nan))]
            if len(vals) < 2:
                mcol, ccol = [], []
                break
            m = statistics.fmean(vals)
            sd = statistics.stdev(vals)
            if not (math.isfinite(m) and math.isfinite(sd)):
                mcol, ccol = [], []
                break
            mcol.append(m)
            ccol.append(sd / abs(m) if abs(m) > 1e-9 else 0.0)
        if mcol and finite(mcol) and finite(ccol):
            means[k], cvs[k] = mcol, ccol
    if means:
        out["mean"] = (list(means), [list(r) for r in zip(*means.values())])
        out["cv"] = (list(cvs), [list(r) for r in zip(*cvs.values())])
    return out


def score(name: str, corpus: str, keys: list[str], mat: list[list[float]],
          target: list[float], task: str) -> dict:
    from soundingline.measures.select import relevance                 # noqa: PLC0415
    tbl = relevance(keys, mat, target, ml_task=task)
    raw = int((tbl["p_value"] < 0.05).sum())
    rel = tbl[tbl["relevant"]]
    top = [{"feature": str(r["feature"]), "p": float(r["p_value"])}
           for _, r in tbl.head(8).iterrows()]
    res = {"corpus": corpus, "form": name, "n_tested": int(len(tbl)),
           "n_uncorrected_p05": raw, "n_expected_by_chance": round(0.05 * len(tbl), 1),
           "n_survive_BY": int(len(rel)),
           # ALL survivor names, uncapped -- the B1 set comparison below is only valid on full
           # sets. Capping these at 25 made "cv-only" a comparison of top-25 orderings, which is
           # not the same question and is not a finding.
           "survivor_names": [str(r["feature"]) for _, r in rel.iterrows()],
           "survivors": [{"feature": str(r["feature"]), "p": float(r["p_value"])}
                         for _, r in rel.head(25).iterrows()],
           "top_regardless": top}
    print(f"  {name:<6} tested {len(tbl):>4}   uncorrected p<.05: {raw:>4} "
          f"(chance {0.05 * len(tbl):>5.1f})   SURVIVE BY: {len(rel):>3}")
    if len(rel):
        for s in res["survivors"][:5]:
            print(f"           {s['feature']:<44} p={s['p']:.2e}")
    return res


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpora", default="ladder,ladder2,nomaker,gate3")
    args = ap.parse_args()

    results = []
    for corpus in args.corpora.split(","):
        d = load(corpus)
        if not d:
            print(f"\n=== {corpus}: NO CACHE — run runners/build_features.py first")
            continue
        items = d["items"]
        f = forms(items)
        if not f:
            print(f"\n=== {corpus}: no artifact has enough windows")
            continue
        groups = [it["group"] for it in items if it.get("enough_windows")]
        # rung is ordinal -> regression; kind/half are labels -> classification
        numeric = all(isinstance(g, (int, float)) for g in groups)
        task = "regression" if numeric else "classification"
        if not numeric:
            uniq = sorted({str(g) for g in groups})
            if len(uniq) != 2:
                print(f"\n=== {corpus}: {len(uniq)} groups, tsfresh needs 2 — skipping")
                continue
            target = [1.0 if str(g) == uniq[1] else 0.0 for g in groups]
            label = f"{uniq[0]} vs {uniq[1]}"
        else:
            target = [float(g) for g in groups]
            label = "rung"

        print(f"\n=== {corpus}  n={len(groups)}  target={label}  ({task})")
        for form_name in ("whole", "mean", "cv"):
            if form_name not in f:
                continue
            keys, mat = f[form_name]
            try:
                results.append(score(form_name, corpus, keys, mat, target, task))
            except Exception as e:                                     # noqa: BLE001
                print(f"  {form_name:<6} FAILED {type(e).__name__}: {str(e)[:60]}")

    # ── B1's actual question: does CV find anything the whole-document form does not? ──────────
    print("\n" + "=" * 78)
    print("B1 — does WITHIN-ARTIFACT VARIATION carry anything the whole-document mean does not?")
    print("=" * 78)
    by_corpus: dict[str, dict[str, dict]] = {}
    for r in results:
        by_corpus.setdefault(r["corpus"], {})[r["form"]] = r
    verdict = {}
    for corpus, fs in by_corpus.items():
        w = set(fs.get("whole", {}).get("survivor_names", []))
        m = set(fs.get("mean", {}).get("survivor_names", []))
        c = set(fs.get("cv", {}).get("survivor_names", []))
        # a feature counts as cv-only if NEITHER whole-document form found it. `mean` is the
        # control: it uses the same windows as cv, so anything cv finds that mean also finds is
        # a windowing effect, not a variation effect.
        only_cv = sorted(c - w - m)
        print(f"  {corpus:<10} whole:{len(w):>3}  mean:{len(m):>3}  cv:{len(c):>3}   "
              f"cv-only:{len(only_cv):>3}  "
              f"{'<<< carries something the mean does not' if only_cv else ''}")
        for x in only_cv[:8]:
            print(f"             {x}")
        verdict[corpus] = {"n_whole": len(w), "n_mean": len(m), "n_cv": len(c),
                           "cv_only": only_cv}

    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "feature_sweep.json").write_text(json.dumps(
        {"results": results, "b1_verdict": verdict}, indent=2), encoding="utf-8", newline="\n")
    print(f"\nwrote {(OUT / 'feature_sweep.json').relative_to(REPO)}")
    print("\nNothing here is a result. Survivors are CANDIDATES and still owe the control battery.")


if __name__ == "__main__":
    main()
