"""PAN Multi-Author Writing Style Analysis — the field's race, run offline, scored their way.

── WHY THIS EXISTS ───────────────────────────────────────────────────────────────────────────

    If it's a race, I want to know what the finish line looks like and who's in the front.

Until now our testing environment has not been equivalent to the field's, so none of our numbers
were comparable to anyone's. This fixes that.

**The task.** A document is split into sentences. For each adjacent pair, decide whether the author
changes between them. Output is a binary vector; the metric is macro F1 over those decisions.

**And it is our problem.** This is within-document style variation — the thing
`docs/theory/CURATOR_GUESSES.md` B1 calls the primary detector, and what F7 argues is really goal
variation seen without the theory. The field has been running this as a shared task since 2018.

── THE THREE DIFFICULTIES, AND ONLY ONE OF THEM MATTERS ──────────────────────────────────────

    easy     authors write about different topics      -> topic gives it away
    medium   topic partially controlled
    hard     ALL sentences on ONE topic AND stylistically similar

**Only `hard` is worth reporting.** The easy split's ~0.99 scores circulate in abstracts and are
meaningless for us — they measure topic detection. Hard removes topic entirely, which is the
control this project has spent three days learning to demand.

── THE BAR ───────────────────────────────────────────────────────────────────────────────────

    2023 hard (paragraph)   0.821   Ye
    2024 hard (paragraph)   0.863   nycu-nlp        random baseline 0.495
    2025 hard (SENTENCE)    0.830   wqd             predict-all-zero baseline 0.453

**Judge against 0.83. Never against 0.99.** And note a different team wins each difficulty every
year, which suggests nobody has a general method.

── WHAT THIS RUNNER DOES ─────────────────────────────────────────────────────────────────────

Scores predictions with the official metric, and ships two floor baselines so any number we produce
has something honest beneath it:

    predict-none    all zeros. The 2025 overview's own floor, ~0.453
    random          coin flip per boundary, ~0.495

**Run a baseline first.** If we cannot reproduce ~0.45 for all-zeros, our scoring is wrong and no
result above it is readable — the same positive-control logic as the author-identification gate.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

DATA = REPO / "corpora" / "public" / "pan_style" / "full_dataset"
RESULTS = REPO / "results" / "pan_style"


def load(difficulty: str, split: str) -> list[dict]:
    """Every problem in one cell: its sentences and the true change vector."""
    d = DATA / difficulty / split
    out = []
    for truth in sorted(d.glob("truth-problem-*.json")):
        n = truth.stem.replace("truth-problem-", "")
        txt = d / f"problem-{n}.txt"
        if not txt.exists():
            continue
        t = json.loads(truth.read_text(encoding="utf-8"))
        sents = [s for s in txt.read_text(encoding="utf-8").split("\n") if s.strip()]
        # the change vector has one entry per ADJACENT PAIR, so it is one shorter than the text
        if len(t.get("changes", [])) != len(sents) - 1:
            continue
        out.append({"id": n, "sentences": sents, "changes": t["changes"],
                    "authors": t.get("authors")})
    return out


def macro_f1(true: list[int], pred: list[int]) -> float:
    """Macro F1 over both classes, which is what the PAN overview reports."""
    f1s = []
    for c in (0, 1):
        tp = sum(1 for t, p in zip(true, pred) if t == c and p == c)
        fp = sum(1 for t, p in zip(true, pred) if t != c and p == c)
        fn = sum(1 for t, p in zip(true, pred) if t == c and p != c)
        prec = tp / (tp + fp) if tp + fp else 0.0
        rec = tp / (tp + fn) if tp + fn else 0.0
        f1s.append(2 * prec * rec / (prec + rec) if prec + rec else 0.0)
    return sum(f1s) / len(f1s)


def score(problems: list[dict], predict) -> dict:
    """Pool every boundary decision across every document, then take macro F1."""
    true, pred = [], []
    for p in problems:
        pr = predict(p)
        assert len(pr) == len(p["changes"]), f"{p['id']}: {len(pr)} vs {len(p['changes'])}"
        true.extend(p["changes"])
        pred.extend(pr)
    base = sum(true) / len(true)
    return {"macro_f1": macro_f1(true, pred), "n_problems": len(problems),
            "n_boundaries": len(true), "positive_rate": base,
            "predicted_positive_rate": sum(pred) / len(pred)}


BASELINES = {
    "predict_none": lambda p: [0] * len(p["changes"]),
    "predict_all": lambda p: [1] * len(p["changes"]),
    "random": lambda p: [random.Random(hash(p["id"]) & 0xFFFF).randint(0, 1)
                         for _ in p["changes"]],
}

# published bests, so every run prints the distance to the finish line
SOTA = {"easy": 0.959, "medium": 0.825, "hard": 0.830}      # PAN 2025, sentence level
FLOOR = {"hard": 0.453}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--difficulty", default="hard", choices=["easy", "medium", "hard"])
    ap.add_argument("--split", default="validation", choices=["train", "validation", "test"])
    ap.add_argument("--baselines", action="store_true", help="run the floor baselines only")
    args = ap.parse_args()

    if not DATA.exists():
        print(f"missing {DATA} — download Zenodo record 21768938 first")
        return

    probs = load(args.difficulty, args.split)
    print(f"PAN26 · {args.difficulty} · {args.split}: {len(probs)} problems, "
          f"{sum(len(p['changes']) for p in probs):,} boundary decisions")
    print(f"the bar: SOTA {SOTA[args.difficulty]:.3f}"
          + (f", published floor {FLOOR[args.difficulty]:.3f}" if args.difficulty in FLOOR else "")
          + "\n")

    out = {}
    print(f"{'method':<18}{'macro F1':>10}{'pred pos rate':>15}{'vs SOTA':>10}")
    print("-" * 55)
    for name, fn in BASELINES.items():
        r = score(probs, fn)
        out[name] = r
        print(f"{name:<18}{r['macro_f1']:>10.4f}{r['predicted_positive_rate']:>15.3f}"
              f"{r['macro_f1'] - SOTA[args.difficulty]:>+10.3f}")

    print(f"\ntrue positive rate in this cell: {out['predict_none']['positive_rate']:.3f}")
    pn = out["predict_none"]["macro_f1"]
    if args.difficulty == "hard" and abs(pn - FLOOR["hard"]) < 0.06:
        print(f">>> SCORING VERIFIED — predict-none gives {pn:.3f}, the overview reports "
              f"{FLOOR['hard']:.3f}")
    elif args.difficulty == "hard":
        print(f">>> WARNING — predict-none gives {pn:.3f} but the overview reports "
              f"{FLOOR['hard']:.3f}. Check the metric before trusting anything above it.")

    RESULTS.mkdir(parents=True, exist_ok=True)
    (RESULTS / f"baselines_{args.difficulty}_{args.split}.json").write_text(
        json.dumps({"difficulty": args.difficulty, "split": args.split,
                    "sota": SOTA[args.difficulty], "results": out}, indent=2),
        encoding="utf-8", newline="\n")
    print(f"\nwrote {(RESULTS / f'baselines_{args.difficulty}_{args.split}.json').relative_to(REPO)}")


if __name__ == "__main__":
    main()
