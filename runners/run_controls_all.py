"""Every no-maker control, against a real control set, length-matched, with a real null.

── WHY THIS EXISTS ───────────────────────────────────────────────────────────────────────────

Four measures were tested against the same three Gate 1 artifacts — method unlock, density, the
wall, and the refusal panel. `n = 3` was named as the binding constraint **before** the most recent
two of those ran, and in the density case the three artifacts' length alone produced the entire
apparent effect.

`corpora/nomaker/` now holds **36 artifacts in three kinds**, and this reruns everything against
them at once so the comparison is made on one footing rather than four.

── THE THREE KINDS ARE NOT INTERCHANGEABLE, AND THAT IS THE POINT ────────────────────────────

    thin      bare prompt, nothing specified. The obvious no-maker case.
    rich      a long directed prompt with a purpose and an audience. **This one SHOULD have
              recoverable intent — the prompt-writer's.** A measure that calls `rich` as empty as
              `thin` is detecting machines, which this project refuses to do.
    averaged  generated then rewritten twice. Regression to the mean, by construction.

**The `rich` arm is the one that can embarrass a measure**, and it is reported separately for
exactly that reason.

── TWO THINGS EVERY COMPARISON GETS, BECAUSE TODAY COST TWO INSTRUMENTS WITHOUT THEM ─────────

**Length matching.** Human artifacts are truncated to the no-maker median before any comparison.
Density died to a word-count confound this morning; nothing else will.

**A permutation null.** The refusal panel's original pass condition — *3 of 5 components higher* —
had a **50% false-positive rate**, which is a coin flip wearing a criterion's clothes. Every
verdict here is against labels shuffled 2,000 times, so the reported p is what it says it is.
"""

from __future__ import annotations

import argparse
import json
import random
import statistics
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from soundingline.measures.density import density                      # noqa: E402
from soundingline.measures.leakage import delta_classify, profile      # noqa: E402
from runners.run_gate3 import load_corpus                              # noqa: E402

NOMAKER = REPO / "corpora" / "nomaker"
RESULTS = REPO / "results" / "controls"


def truncate(t: str, words: int) -> str:
    return " ".join(t.split()[:words])


def perm_test(a: list[float], b: list[float], n: int = 2000, seed: int = 0) -> dict:
    """Difference in means against shuffled labels. Two-sided."""
    obs = statistics.fmean(a) - statistics.fmean(b)
    pool = a + b
    rng = random.Random(seed)
    hits = 0
    for _ in range(n):
        rng.shuffle(pool)
        d = statistics.fmean(pool[:len(a)]) - statistics.fmean(pool[len(a):])
        hits += abs(d) >= abs(obs)
    return {"diff": obs, "p": (hits + 1) / (n + 1), "n_a": len(a), "n_b": len(b)}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--perms", type=int, default=2000)
    args = ap.parse_args()

    man = json.loads((NOMAKER / "manifest.json").read_text(encoding="utf-8"))
    nm = {}
    for it in man["items"]:
        p = NOMAKER / f"{it['id']}.txt"
        if p.exists():
            nm.setdefault(it["kind"], []).append(p.read_text(encoding="utf-8"))
    corpus = load_corpus()

    match = int(statistics.median(len(t.split()) for v in nm.values() for t in v))
    human = [truncate(t, match) for _, _, t in corpus]
    kinds = {k: [truncate(t, match) for t in v] for k, v in nm.items()}
    allnm = [t for v in kinds.values() for t in v]

    print(f"human n={len(human)}   no-maker n={len(allnm)} "
          f"({', '.join(f'{k}={len(v)}' for k, v in kinds.items())})")
    print(f"every text truncated to {match} words — the length confound that killed density\n")

    out: dict = {"match_words": match, "n_human": len(human), "kinds": {k: len(v) for k, v in kinds.items()}}

    # ── 1 · density, now length-matched ───────────────────────────────────────────────────────
    hd = [density(t).scale_gain for t in human]
    print("DENSITY (scale_gain), length-matched")
    print(f"  {'group':<12}{'mean':>9}{'diff':>9}{'p':>9}")
    print(f"  {'human':<12}{statistics.fmean(hd):>9.4f}")
    out["density"] = {"human": statistics.fmean(hd), "kinds": {}}
    for k, v in kinds.items():
        d = [density(t).scale_gain for t in v]
        r = perm_test(d, hd, args.perms)
        print(f"  {k:<12}{statistics.fmean(d):>9.4f}{r['diff']:>+9.4f}{r['p']:>9.4f}")
        out["density"]["kinds"][k] = {"mean": statistics.fmean(d), **r}

    # ── 2 · the function-word channel: can it tell no-maker from human at all? ─────────────────
    print("\nFUNCTION WORDS — Burrows' Delta, human vs each no-maker kind")
    out["leakage"] = {}
    for k, v in kinds.items():
        r = delta_classify({"human": human, k: v})
        print(f"  human vs {k:<10} {r['accuracy']:>6.1%} vs {r['chance']:.0%} chance"
              f" = {r['lift']:.2f}x")
        out["leakage"][k] = r
    r = delta_classify({"human": human, "nomaker": allnm})
    print(f"  human vs ALL        {r['accuracy']:>6.1%} vs {r['chance']:.0%} = {r['lift']:.2f}x")
    out["leakage"]["all"] = r

    # ── 3 · the three-kind test: does anything tell rich from thin? ───────────────────────────
    print("\nTHE RICH ARM — can any measure tell a directed prompt from a bare one?")
    print("  (if not, every measure here detects MACHINES rather than reads intent)")
    if "rich" in kinds and "thin" in kinds:
        r = delta_classify({"rich": kinds["rich"], "thin": kinds["thin"]})
        print(f"  function words   rich vs thin: {r['accuracy']:.1%} vs 50% = {r['lift']:.2f}x")
        out["rich_vs_thin_leakage"] = r
        rd = [density(t).scale_gain for t in kinds["rich"]]
        td = [density(t).scale_gain for t in kinds["thin"]]
        pr = perm_test(rd, td, args.perms)
        print(f"  density          rich {statistics.fmean(rd):.4f} vs thin "
              f"{statistics.fmean(td):.4f}  diff {pr['diff']:+.4f}  p={pr['p']:.4f}")
        out["rich_vs_thin_density"] = pr

    RESULTS.mkdir(parents=True, exist_ok=True)
    (RESULTS / "controls.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(f"\nwrote {(RESULTS / 'controls.json').relative_to(REPO)}")


if __name__ == "__main__":
    main()
