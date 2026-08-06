"""Our measures against the field's own race — style change detection, scored their way.

── THE QUESTION ──────────────────────────────────────────────────────────────────────────────

A document is split into sentences. For each adjacent pair, decide whether the author changes.
**This is within-document variation — the thing the curator calls his primary detector when he reads
by hand, and what he argues is really goal variation seen without the theory.**

The field has run it as a shared task since 2018. We now hold six years of it, with test labels.

── WHY ONLY THE HARD SPLIT COUNTS ────────────────────────────────────────────────────────────

    easy     authors write about different topics    -> topic gives it away
    medium   topic partly controlled
    hard     ALL sentences one topic AND stylistically similar

**The 0.99 scores that circulate in abstracts are the easy split measuring topic detection.** Hard
removes topic by construction, which is the control this project spent three days learning to
demand. The bar there is **0.830**; the floor, predicting no change anywhere, is **0.453**, and our
own scorer reproduces that floor to within 0.012.

── WHAT THIS RUNS ────────────────────────────────────────────────────────────────────────────

For every adjacent sentence pair, the **absolute difference** of 342 linguistic features between the
two sentences. A change of author should show as a large difference in *some* of them. Fit on the
training split, score on validation with the official metric.

**Deliberately the simplest possible model** — logistic regression on feature deltas. The point is
not to win; it is to find out where an off-the-shelf feature bank sits relative to a field that has
worked on this for eight years, **on a task where topic is controlled and our own theory says the
signal lives.**

── PRE-REGISTERED ────────────────────────────────────────────────────────────────────────────

    COMPETITIVE   above 0.75 on hard -- within striking distance of 0.830
    REAL          above 0.55 -- clearly beating the 0.453 floor, not yet competitive
    FLOOR         at or below 0.50 -- the feature bank carries nothing once topic is removed

**A floor result is informative and is the most likely outcome.** PAN 2024 reports that pure
stylometry has virtually disappeared from this task in favour of fine-tuned transformers, so a
342-feature bank landing near the floor would confirm the field's own conclusion on our data.
"""

from __future__ import annotations

import argparse
import contextlib
import io
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

DATA = REPO / "corpora" / "public" / "pan_style" / "full_dataset"
RESULTS = REPO / "results" / "pan_features"
SOTA = {"easy": 0.959, "medium": 0.825, "hard": 0.830}
FLOOR = 0.453


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--difficulty", default="hard")
    ap.add_argument("--n-train", type=int, default=250)
    ap.add_argument("--n-test", type=int, default=250)
    args = ap.parse_args()

    import numpy as np                                               # noqa: PLC0415
    from sklearn.linear_model import LogisticRegression              # noqa: PLC0415
    from sklearn.preprocessing import StandardScaler                 # noqa: PLC0415

    from soundingline.measures.features import extract               # noqa: PLC0415
    from runners.run_pan_style import load, macro_f1                 # noqa: PLC0415

    print(f"PAN26 {args.difficulty}: loading ...", flush=True)
    tr = load(args.difficulty, "train")[: args.n_train]
    te = load(args.difficulty, "validation")[: args.n_test]
    print(f"  {len(tr)} train / {len(te)} validation problems", flush=True)

    buf = io.StringIO()

    def featurise(problems, label):
        X, y, keys = [], [], None
        for i, p in enumerate(problems):
            with contextlib.redirect_stdout(buf):
                fs = [extract(s) for s in p["sentences"]]
            if keys is None:
                keys = sorted(set.intersection(*(set(f) for f in fs))) if fs else []
            for a, b, ch in zip(fs, fs[1:], p["changes"]):
                X.append([abs(a.get(k, 0.0) - b.get(k, 0.0)) for k in keys])
                y.append(ch)
            if (i + 1) % 25 == 0:
                print(f"  {label} {i + 1}/{len(problems)}", flush=True)
        return np.nan_to_num(np.array(X, dtype=float)), np.array(y), keys

    Xtr, ytr, keys = featurise(tr, "train")
    Xte, yte, _ = featurise(te, "test")
    print(f"\n  {Xtr.shape[0]:,} training pairs x {Xtr.shape[1]} features")
    print(f"  {Xte.shape[0]:,} validation pairs, {ytr.mean():.1%} positive\n")

    sc = StandardScaler().fit(Xtr)
    clf = LogisticRegression(max_iter=2000, C=0.1, class_weight="balanced")
    clf.fit(sc.transform(Xtr), ytr)
    pred = clf.predict(sc.transform(Xte))

    got = macro_f1(list(yte), list(pred))
    none = macro_f1(list(yte), [0] * len(yte))
    bar = SOTA[args.difficulty]
    verdict = ("COMPETITIVE" if got > 0.75 else "REAL" if got > 0.55 else "FLOOR")

    print(f"{'method':<28}{'macro F1':>10}")
    print("-" * 40)
    print(f"{'our 342 features':<28}{got:>10.4f}")
    print(f"{'predict-no-change floor':<28}{none:>10.4f}")
    print(f"{'published best (' + args.difficulty + ')':<28}{bar:>10.4f}")
    print(f"\n  gap to floor {got - none:+.4f}   gap to best {got - bar:+.4f}")
    print(f"\n  >>> {verdict}")

    RESULTS.mkdir(parents=True, exist_ok=True)
    (RESULTS / f"{args.difficulty}.json").write_text(json.dumps(
        {"difficulty": args.difficulty, "n_train_problems": len(tr),
         "n_test_problems": len(te), "n_train_pairs": int(Xtr.shape[0]),
         "n_features": int(Xtr.shape[1]), "macro_f1": got, "floor": none,
         "sota": bar, "verdict": verdict}, indent=2), encoding="utf-8", newline="\n")
    print(f"\nwrote {(RESULTS / f'{args.difficulty}.json').relative_to(REPO)}")


if __name__ == "__main__":
    main()
