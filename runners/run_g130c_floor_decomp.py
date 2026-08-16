"""G130c follow-up — WHICH covariates raised the matched blind floor to 0.40? (owed by L73)

The blind arm sees only candidate labels, never the text, so the floor can rise only through
label composition: matching reweighted the truth marginal (the matched subset is not
truth-balanced, unlike the L64 full-set construction whose floor is analytic 1/k), and the
reader has its own label preferences. Decomposition, on the existing matched_k4_blind records:

    (1) truth marginal of the matched subset vs uniform, and the reader's pick marginal;
    (2) the MARGINAL-ALIGNMENT FLOOR: expected accuracy if the reader picks by its empirical
        label preference restricted to the candidate set (Monte Carlo over fresh uniform decoy
        draws) -- how much of 0.402 is label-prior alignment alone;
    (3) per-label blind accuracy (where the preference concentrates);
    (4) logistic regression of blind correctness on the six CEM covariates, with and without
        truth-label dummies -- whether any text covariate predicts correctness at all once the
        label marginal is accounted for (it should not: the reader never saw the text).

The matched event list is reconstructed exactly (seed 41, same code path as
run_arg_matched_recovery.py); records join by index. CPU, seconds, no model calls.
Output: results/arg_recovery/floor_decomp.json (every verdict statistic on disk).
"""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

RESULTS = REPO / "results" / "arg_recovery"
EVENTS = REPO / "results" / "arg_baselines" / "events.json"

COMMON = None


def rare_rate(text: str) -> float:
    global COMMON
    if COMMON is None:
        from wordfreq import top_n_list                               # noqa: PLC0415
        COMMON = set(top_n_list("en", 5000))
    ws = [w.strip(".,;:!?\"'()").lower() for w in text.split()]
    ws = [w for w in ws if w]
    return sum(w not in COMMON for w in ws) / len(ws) if ws else 0.0


def main() -> None:
    import numpy as np                                                # noqa: PLC0415

    all_events = [e for e in json.loads(EVENTS.read_text(encoding="utf-8"))["events"]
                  if e["coarse"] in ("surface", "content")]

    def covs(e):
        o, n = e["old"].split(), e["new"].split()
        os_, ns_ = set(w.lower() for w in o), set(w.lower() for w in n)
        return [len(ns_ - os_), len(os_ - ns_), len(n) - len(o),
                rare_rate(e["new"]) - rare_rate(e["old"]),
                min(len(o), 60), rare_rate(e["old"])]

    COV_NAMES = ["words_added", "words_removed", "length_change", "rarity_shift",
                 "sentence_length", "original_rarity"]

    # -- reconstruct the matched subset exactly (seed 41, identical code path) ----------------
    C = np.array([covs(e) for e in all_events], float)
    y = np.array([e["coarse"] == "content" for e in all_events])
    Z = (C - C.mean(0)) / (C.std(0) + 1e-9)
    rng_m = np.random.default_rng(41)
    bins = np.stack([np.digitize(Z[:, j], np.quantile(Z[:, j], [1 / 3, 2 / 3]))
                     for j in range(Z.shape[1])], axis=1)
    strata: dict = {}
    for i, b in enumerate(bins):
        strata.setdefault(tuple(b), {"c": [], "s": []})["c" if y[i] else "s"].append(i)
    keep = set()
    for st in strata.values():
        n = min(len(st["c"]), len(st["s"]))
        if n == 0:
            continue
        keep.update(rng_m.permutation(st["c"])[:n].tolist())
        keep.update(rng_m.permutation(st["s"])[:n].tolist())
    sub_all = [all_events[i] for i in sorted(keep)]
    labs_all = [e["fine"] for e in sub_all]
    keep_lab = sorted({l for l in set(labs_all) if labs_all.count(l) >= 20})
    sub = [e for e in sub_all if e["fine"] in keep_lab]
    k = min(4, len(keep_lab))

    rows = [json.loads(x) for x in
            (RESULTS / f"matched_k{k}_blind_partial.jsonl").read_text(encoding="utf-8").splitlines()]
    assert len(rows) == len(sub), (len(rows), len(sub))
    for r in rows:                       # join sanity: recorded truth must match reconstruction
        assert sub[r["i"]]["fine"] == r["truth"], r
    acc = sum(r["truth"] == r["pick"] for r in rows) / len(rows)

    # -- (1) marginals ------------------------------------------------------------------------
    n = len(rows)
    truth_marg = {l: c / n for l, c in Counter(r["truth"] for r in rows).items()}
    pick_marg = {l: c / n for l, c in Counter(r["pick"] for r in rows).items()}

    # -- (2) marginal-alignment floor: Monte Carlo over fresh uniform decoy draws -------------
    rng = np.random.default_rng(7)
    reps = 200
    hits = 0
    labs = keep_lab
    q = np.array([pick_marg.get(l, 0.0) for l in labs])
    for r in rows:
        truth = r["truth"]
        for _ in range(reps):
            decoys = [l for l in labs if l != truth]
            cand = list(rng.choice(decoys, size=k - 1, replace=False)) + [truth]
            w = np.array([q[labs.index(c)] for c in cand])
            w = w / w.sum() if w.sum() > 0 else np.ones(k) / k
            hits += w[cand.index(truth)]
    alignment_floor = hits / (n * reps)

    # -- (3) per-label blind accuracy ---------------------------------------------------------
    per_label = {l: {"n": 0, "hit": 0} for l in labs}
    for r in rows:
        per_label[r["truth"]]["n"] += 1
        per_label[r["truth"]]["hit"] += int(r["truth"] == r["pick"])
    per_label = {l: {"n": v["n"], "acc": round(v["hit"] / v["n"], 4)}
                 for l, v in per_label.items()}

    # -- (4) logistic regression of correctness on covariates ---------------------------------
    from sklearn.linear_model import LogisticRegression               # noqa: PLC0415
    X = np.array([covs(sub[r["i"]]) for r in rows], float)
    Xz = (X - X.mean(0)) / (X.std(0) + 1e-9)
    corr = np.array([r["truth"] == r["pick"] for r in rows], int)
    lr = LogisticRegression(max_iter=2000).fit(Xz, corr)
    base_ll = float(lr.score(Xz, corr))
    coefs = {nm: round(float(c), 4) for nm, c in zip(COV_NAMES, lr.coef_[0])}
    # with truth-label dummies: does any covariate survive the marginal account?
    D = np.zeros((len(rows), len(labs)))
    for j, r in enumerate(rows):
        D[j, labs.index(r["truth"])] = 1.0
    lr2 = LogisticRegression(max_iter=2000).fit(np.hstack([Xz, D]), corr)
    coefs_after = {nm: round(float(c), 4) for nm, c in zip(COV_NAMES, lr2.coef_[0][:6])}

    out = {
        "question": "which covariates raised the matched blind floor (0.402 vs analytic 0.25)",
        "n": n, "k": k, "blind_accuracy": round(acc, 4),
        "truth_marginal": {l: round(v, 4) for l, v in sorted(truth_marg.items())},
        "pick_marginal": {l: round(v, 4) for l, v in sorted(pick_marg.items())},
        "alignment_floor_mc": round(float(alignment_floor), 4),
        "alignment_share_of_rise": round(float((alignment_floor - 1 / k) / (acc - 1 / k)), 3)
        if acc > 1 / k else None,
        "per_label_blind_accuracy": per_label,
        "logistic_covariates_only": {"train_accuracy": round(base_ll, 4), "coefs": coefs},
        "logistic_with_label_dummies": {"coefs_covariate_part": coefs_after},
        "mc_reps": reps,
    }
    dest = RESULTS / "floor_decomp.json"
    dest.write_text(json.dumps(out, indent=1), encoding="utf-8", newline="\n")
    print(json.dumps(out, indent=1))
    print(f"wrote {dest.relative_to(REPO)}")


if __name__ == "__main__":
    main()
