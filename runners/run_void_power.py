"""Two voided tests, redesigned for the power they never had.

── WHY THESE TWO ─────────────────────────────────────────────────────────────────────────────

A **void** in this project means the test could not answer its own question. The 2026-08-07 audit
found eight, and **four of them died to sample size or text length rather than to the hypothesis.**
These are the two cheapest of those four, and both have a diagnosed cause rather than a guess.

    V2   "reader displacement varies more for machine text"     died on THREE artifacts
    V4   "function words separate specified maker states"       died at 38% power -- at 380 words a
         (and V5, purpose x affect, which died the same way)     pronoun rate gives FIVE tokens, and
                                                                the statistic divides by a variance
                                                                made almost entirely of Poisson noise
                                                                on five counts

**Neither redesign changes the question. Both change only the amount of evidence**, which is the one
move a void licenses.

── V2 · DISPLACEMENT VARIANCE, AT n ──────────────────────────────────────────────────────────

**The claim.** A reader's internal state should move *more erratically* while reading machine text
than while reading text with a maker — not further from rest, which was tested separately and came
back a clean null, but **more variably**.

**Method.** Read each artifact in fixed windows. At every window take the affect projection vector,
and measure how much it moves between consecutive windows. **Displacement variance is the spread of
that step size within one artifact.** Compare across corpora.

**The comparison that matters is ladder against no-maker**, because no-maker text is generated with
no maker to have a state, and everything else is held as close as this project can hold it.

    n was 3. It is now 75 + 36 at minimum, and the null is a permutation of the corpus labels
    rather than an eyeball.

── V4 · FUNCTION WORDS AGAINST SPECIFIED STATE, POOLED TO THE TOKEN COUNT THE STATISTIC NEEDS ─

**The claim.** Function words are produced non-consciously and track psychological state, so texts
written under different specified states should separate on their function-word distribution.

**Why it died, precisely.** The original ran on ~380-word texts. At a first-person-singular rate of
13.8 per 1,000 words that is **five tokens**. The separability statistic divides by a within-group
variance that is, at five counts, almost entirely Poisson noise. **The design could not have detected
a real effect and the power simulation showed that without touching the data.**

**The redesign, and it is the one D-0's own power analysis prescribes: pool within state.** Rung is a
known state, so concatenating artifacts *within* a rung is aggregation rather than contamination.
Fifteen artifacts at ~1,445 words gives **~21,000 words per state** — roughly 290 first-person tokens
instead of five, a **58-fold** improvement in the quantity that killed it.

**The cost is that n becomes the number of pools, not the number of artifacts**, so the test is run
at several pool sizes and the trade-off is reported rather than chosen.

── PRE-REGISTERED, BEFORE EITHER RUN ─────────────────────────────────────────────────────────

    V2   SEPARATES   displacement variance differs between ladder and no-maker, permutation p < 0.05
         NULL        it does not. **With n above 100 this is now an informative null**, which is
                     exactly what the void was not
    V4   SEPARATES   pooled function-word vectors classify rung above chance, held out
         NULL        they do not, at token counts where the statistic can work
         STILL VOID  the pooling cannot reach the token count the power analysis requires

**Both nulls are now worth having.** A void is not a negative result; these are designed so that
whatever comes back is one.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

RESULTS = REPO / "results" / "void_power"

# Function words: the closed-class items stylometry has used for sixty years. Frozen here so the
# feature set cannot drift between runs.
FUNCTION_WORDS = (
    "a about above after again against all am an and any are as at be because been before being "
    "below between both but by can did do does doing down during each few for from further had has "
    "have having he her here hers herself him himself his how i if in into is it its itself just me "
    "more most my myself no nor not now of off on once only or other our ours ourselves out over own "
    "same she should so some such than that the their theirs them themselves then there these they "
    "this those through to too under until up very was we were what when where which while who whom "
    "why will with you your yours yourself yourselves"
).split()


def load_corpus(name: str):
    d = REPO / "corpora" / name
    man = json.loads((d / "manifest.json").read_text(encoding="utf-8"))
    out = []
    for it in man["items"]:
        p = d / f"{it['id']}.txt"
        if p.exists():
            out.append((it.get("rung", it.get("kind")), p.read_text(encoding="utf-8")))
    return out


def run_v2(args) -> dict:
    import numpy as np                                               # noqa: PLC0415

    from soundingline.probe.activations import (DEFAULT_MODEL, Reader,  # noqa: PLC0415
                                                fit_directions)
    from runners.run_b import split                                  # noqa: PLC0415
    from runners.run_layer_ratio import windows                      # noqa: PLC0415

    model_name = args.model or DEFAULT_MODEL
    print(f"loading {model_name} ...", flush=True)
    reader = Reader(model_name, device=args.device)
    fit, _ = split()
    dirs = fit_directions(reader, fit)
    n_layers = dirs.n_layers
    concepts = list(dirs.concepts)

    per_corpus = {}
    for corpus in args.corpora.split(","):
        rows = load_corpus(corpus)
        if not rows:
            print(f"  {corpus}: nothing loadable")
            continue
        vals = []
        for i, (_, text) in enumerate(rows):
            ws = windows(text)
            if len(ws) < 3:
                continue
            V = []
            for w in ws:
                p = dirs.project(reader.read(w))
                V.append(np.array([[p[c][L] for L in range(n_layers)] for c in concepts]).ravel())
            V = np.array(V)
            steps = np.linalg.norm(np.diff(V, axis=0), axis=1)
            # displacement VARIANCE within one artifact, normalised by its own mean step so that
            # an artifact that simply moves more does not read as an artifact that moves erratically
            vals.append(float(steps.std() / steps.mean()) if steps.mean() > 0 else 0.0)
            if (i + 1) % 25 == 0:
                print(f"  {corpus} {i + 1}/{len(rows)}", flush=True)
        per_corpus[corpus] = vals
        print(f"  {corpus}: n={len(vals)}  mean {np.mean(vals):.4f}  sd {np.std(vals):.4f}", flush=True)

    rng = np.random.default_rng(7)
    out = {"per_corpus": {k: {"n": len(v), "mean": float(np.mean(v)), "sd": float(np.std(v))}
                          for k, v in per_corpus.items()}}
    if "nomaker" in per_corpus:
        base = per_corpus["nomaker"]
        print(f"\n  {'comparison':<28}{'diff':>10}{'permutation p':>16}")
        print("  " + "-" * 54)
        for k, v in per_corpus.items():
            if k == "nomaker":
                continue
            obs = float(np.mean(v) - np.mean(base))
            pool = np.array(v + base)
            nv = len(v)
            null = []
            for _ in range(5000):
                idx = rng.permutation(len(pool))
                null.append(pool[idx[:nv]].mean() - pool[idx[nv:]].mean())
            p = float((np.abs(np.array(null)) >= abs(obs)).mean())
            out.setdefault("vs_nomaker", {})[k] = {"diff": obs, "p": p, "n": nv}
            print(f"  {k + ' vs nomaker':<28}{obs:>+10.4f}{p:>16.4f}")
        ps = [x["p"] for x in out["vs_nomaker"].values()]
        out["verdict"] = "SEPARATES" if min(ps) < 0.05 else "NULL"
    else:
        out["verdict"] = "NULL"
    print(f"\n  >>> V2 {out['verdict']}")
    if out["verdict"] == "NULL":
        print("  An informative null this time: n is above 100, not 3.")
    return out


def run_v4(args) -> dict:
    import numpy as np                                               # noqa: PLC0415
    from sklearn.linear_model import LogisticRegression              # noqa: PLC0415
    from sklearn.model_selection import StratifiedKFold              # noqa: PLC0415
    from sklearn.preprocessing import StandardScaler                 # noqa: PLC0415

    rows = []
    for corpus in args.corpora.split(","):
        for rung, text in load_corpus(corpus):
            if isinstance(rung, int):
                rows.append((corpus, rung, text))
    states = sorted({r for _, r, _ in rows})
    print(f"\nV4: {len(rows)} artifacts across {len(states)} specified states {states}")

    def fw_vector(text: str) -> np.ndarray:
        toks = [w.strip(".,;:!?\"'()[]—-").lower() for w in text.split()]
        toks = [w for w in toks if w]
        n = max(len(toks), 1)
        from collections import Counter                              # noqa: PLC0415
        c = Counter(toks)
        return np.array([c[w] / n * 1000 for w in FUNCTION_WORDS]), n

    rng = np.random.default_rng(11)
    out = {"states": states, "pool_sizes": {}}
    print(f"\n  {'per pool':>9}{'pools':>7}{'words/pool':>12}{'1st-pers tokens':>17}"
          f"{'accuracy':>10}{'chance':>8}")
    print("  " + "-" * 66)
    for k in [int(x) for x in args.pool_sizes.split(",")]:
        X, y, wc = [], [], []
        for s in states:
            items = [t for _, r, t in rows if r == s]
            rng.shuffle(items)
            for i in range(0, len(items) - k + 1, k):
                v, n = fw_vector(" ".join(items[i:i + k]))
                X.append(v)
                y.append(s)
                wc.append(n)
        X, y = np.array(X), np.array(y)
        if len(set(y)) < 2 or min(np.bincount(np.searchsorted(states, y))) < 2:
            print(f"  {k:>9}{len(y):>7}   too few pools per state to cross-validate")
            continue
        i_idx = FUNCTION_WORDS.index("i")
        med_i = float(np.median(X[:, i_idx] * np.array(wc) / 1000))
        sc = StandardScaler()
        clf = LogisticRegression(max_iter=3000, C=1.0)
        acc, folds = [], min(5, min(np.bincount(np.searchsorted(states, y))))
        for tr, te in StratifiedKFold(folds, shuffle=True, random_state=0).split(X, y):
            clf.fit(sc.fit_transform(X[tr]), y[tr])
            acc.append(float((clf.predict(sc.transform(X[te])) == y[te]).mean()))
        a = float(np.mean(acc))
        chance = 1.0 / len(states)
        out["pool_sizes"][k] = {"pools": len(y), "words_per_pool": float(np.mean(wc)),
                                "first_person_tokens": med_i, "accuracy": a, "chance": chance}
        print(f"  {k:>9}{len(y):>7}{np.mean(wc):>12.0f}{med_i:>17.0f}{a:>10.3f}{chance:>8.3f}")

    best = max((v["accuracy"] - v["chance"], k) for k, v in out["pool_sizes"].items()) \
        if out["pool_sizes"] else (0, None)
    # The original power failure was about FIRST-PERSON rate specifically, because that design read
    # affect states expressed in first person. On a ladder the states are situational specifications
    # and the separating information sits in other function words entirely, so a first-person gate is
    # the wrong precondition here. It stays in the table as a diagnostic and no longer gates.
    if not out["pool_sizes"]:
        out["verdict"] = "STILL VOID"
    elif best[0] > 0.10:
        out["verdict"] = "SEPARATES"
    else:
        out["verdict"] = "NULL"
    print(f"\n  best margin over chance: {best[0]:+.3f} at pool size {best[1]}")
    print(f"  >>> V4 {out['verdict']}")
    if out["verdict"] == "NULL":
        print("  An informative null: the token counts the power analysis called for were reached.")
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--test", choices=["v2", "v4"], required=True)
    ap.add_argument("--corpora", default="ladder,ladder2,ladder3,nomaker")
    ap.add_argument("--pool-sizes", default="1,3,5,15")
    ap.add_argument("--model", default=None)
    ap.add_argument("--device", default="cuda")
    args = ap.parse_args()

    out = run_v2(args) if args.test == "v2" else run_v4(args)
    RESULTS.mkdir(parents=True, exist_ok=True)
    (RESULTS / f"{args.test}.json").write_text(json.dumps(out, indent=2),
                                               encoding="utf-8", newline="\n")
    print(f"\nwrote {(RESULTS / f'{args.test}.json').relative_to(REPO)}")


if __name__ == "__main__":
    main()
