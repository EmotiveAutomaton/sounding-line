"""G — where does the function-word channel stop working, and does it carry anything past identity?

── PRE-REGISTERED BEFORE THE RUN. POWER FIRST THIS TIME. ─────────────────────────────────────

D-0 was inconclusive because 380-word samples give ~5 tokens in a function-word category. The fix
is not a bigger k; it is going where the signal is unambiguous and then calibrating downward until
it breaks. 34 books, 10 authors, several works each, ~25M characters.

**G-1 — the resolution limit.** Author identity is the signal function words are KNOWN to carry:
it is what authorship attribution does. So it is not a hypothesis, it is a calibration. Chop every
book into windows of 500 / 1,000 / 2,000 / 4,000 / 8,000 words and measure author separability at
each. The length where it stops working is the instrument's actual resolution limit, measured
instead of guessed.

    EXPECT identity separability to rise monotonically with window length. If it does NOT — if
    identity is unrecoverable even at 8,000 words — the implementation is broken, not the theory,
    because sixty years of stylometry says otherwise. **That is this run's honesty check.**

**G-2 — the real question, and the one D-0 could not afford to ask.** Hold the author fixed and
ask whether the channel separates their DIFFERENT WORKS. Same person, same non-conscious
machinery, different book: whatever separates them is not identity.

    Austen writing Persuasion is not Austen writing Northanger Abbey. Darwin writing the Origin is
    not Darwin writing the Voyage. If function words carry only identity, within-author separability
    sits at chance and the channel can never carry state. If it carries more, the leaked layer has
    a measurable component past who-wrote-it, and D-0b is worth running.

    PASS   within-author separability > 1.5 at 4,000-word windows, on a majority of authors
    FAIL   at or below 1.0
    Between is ambiguous and licenses nothing.

**The confound, named:** different works differ in topic as well as in state, and function words
are supposed to be topic-independent. If they are, topic contributes little; if they are not, the
whole premise is wrong and G-2 measures topic. **Genre-matched pairs are the control** — Austen's
four novels are one genre, Darwin's three books are not — so a within-genre effect that survives is
much stronger evidence than the aggregate.

**What G cannot show.** Nothing about affect. These authors' states are unknown and unlabelled.
G asks whether the channel has capacity beyond identity; it does not ask what fills it.
"""

from __future__ import annotations

import argparse
import json
import re
import statistics
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from soundingline.measures.leakage import (delta_classify, profile,   # noqa: E402
                                           separability)
from fetch.books import strip_boilerplate                         # noqa: E402

STORE = REPO / "corpora" / "store"
MANIFEST = REPO / "corpora" / "manifests" / "books.json"
RESULTS = REPO / "results" / "g"
WINDOWS = (500, 1000, 2000, 4000, 8000)
_WS = re.compile(r"\s+")


def load_books() -> list[dict]:
    import hashlib
    man = json.loads(MANIFEST.read_text(encoding="utf-8"))
    out = []
    for it in man["items"]:
        key = hashlib.sha256(it["url"].encode("utf-8")).hexdigest()[:16]
        p = STORE / f"{key}.txt"
        if p.exists():
            out.append({**it, "text": strip_boilerplate(p.read_text(encoding="utf-8"))})
    return out


def windows(text: str, n_words: int, cap: int = 12) -> list[str]:
    """Non-overlapping windows of n_words, at most `cap` per work.

    Capped so a long book cannot outvote a short one — David Copperfield would otherwise supply
    twenty times the windows of A Christmas Carol and the "author" groups would really be
    "longest book by that author".
    """
    w = _WS.split(text.strip())
    out = [" ".join(w[i:i + n_words]) for i in range(0, len(w) - n_words + 1, n_words)]
    if len(out) <= cap:
        return out
    step = len(out) / cap
    return [out[int(i * step)] for i in range(cap)]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--cap", type=int, default=12, help="windows per work")
    args = ap.parse_args()

    books = load_books()
    authors = sorted({b["author"] for b in books})
    print(f"{len(books)} works, {len(authors)} authors, "
          f"{sum(len(b['text']) for b in books):,} chars\n", flush=True)

    report: dict = {"windows": {}, "within_author": {}}

    # ── G-1: identity separability vs window length ───────────────────────────────────────────
    print("G-1  author identity separability by window length")
    print(f"  {'words':>7}{'windows':>9}{'ratio':>9}  {'cats>2':>7}   top categories")
    for n in WINDOWS:
        groups = {a: [w for b in books if b["author"] == a
                      for w in windows(b["text"], n, args.cap)] for a in authors}
        groups = {a: v for a, v in groups.items() if len(v) >= 2}
        sep = separability(groups)
        above2 = sum(1 for v in sep["per_category"].values() if v > 2.0)
        top = ", ".join(f"{k}={v:.1f}" for k, v in sep["top"][:3])
        print(f"  {n:>7}{sum(len(v) for v in groups.values()):>9}"
              f"{sep['mean_ratio']:>9.2f}  {above2:>7}   {top}", flush=True)
        report["windows"][n] = {"mean_ratio": sep["mean_ratio"], "cats_above_2": above2,
                                "per_category": sep["per_category"],
                                "n_windows": sum(len(v) for v in groups.values())}

    ratios = [report["windows"][n]["mean_ratio"] for n in WINDOWS]
    monotone = all(b >= a * 0.9 for a, b in zip(ratios, ratios[1:]))
    print(f"\n  rises with length: {'yes' if monotone else 'NO — implementation suspect'}"
          f"   |   best {max(ratios):.2f} at {WINDOWS[ratios.index(max(ratios))]} words")

    # ── G-2: within-author, between-work ──────────────────────────────────────────────────────
    print(f"\nG-2  within-author separability between WORKS, at 4,000-word windows")
    print(f"  {'author':<16}{'works':>6}{'ratio':>9}   top categories")
    wins = []
    for a in authors:
        mine = [b for b in books if b["author"] == a]
        if len(mine) < 2:
            continue
        groups = {b["title"]: windows(b["text"], 4000, args.cap) for b in mine}
        groups = {k: v for k, v in groups.items() if len(v) >= 2}
        if len(groups) < 2:
            continue
        sep = separability(groups)
        wins.append(sep["mean_ratio"])
        top = ", ".join(f"{k}={v:.1f}" for k, v in sep["top"][:3])
        print(f"  {a:<16}{len(groups):>6}{sep['mean_ratio']:>9.2f}   {top}", flush=True)
        report["within_author"][a] = {"mean_ratio": sep["mean_ratio"], "n_works": len(groups),
                                      "per_category": sep["per_category"]}

    above = sum(1 for r in wins if r > 1.5)
    med = statistics.median(wins) if wins else float("nan")
    verdict = ("PASS" if above > len(wins) / 2 else
               "FAIL" if med <= 1.0 else "AMBIGUOUS")
    print("\n" + "=" * 72)
    print(f">>> G-2 {verdict}   median within-author ratio {med:.2f}, "
          f"{above}/{len(wins)} authors above 1.5")
    if verdict == "PASS":
        print("    The channel carries more than identity. A maker's function-word profile moves")
        print("    between their own works, so there is capacity for state. D-0b is worth running.")
    elif verdict == "FAIL":
        print("    Function words carry identity and nothing else. The leaked layer cannot be")
        print("    read from them, and D and D-0b both die here rather than after more compute.")
    print("=" * 72)

    report["G2_verdict"] = verdict
    report["G2_median"] = med
    report["G1_monotone"] = monotone
    RESULTS.mkdir(parents=True, exist_ok=True)
    (RESULTS / "g.json").write_text(json.dumps(report, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
