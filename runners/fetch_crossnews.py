"""CROSSNEWS — one maker, two kinds. Measure it before downloading it.

── WHY THIS CORPUS ───────────────────────────────────────────────────────────────────────────

Three hypotheses in `docs/theory/` are blocked on the same thing: **one maker across different KINDS
of artifact.** Not many works in one genre — different register, audience and purpose. Depth as a
relation to a domain needs it, the polish-variation claim needs it, and values-need-many-works needs
it. Every corpus this project holds varies the maker while fixing the kind, or fixes the maker *and*
the kind.

**CROSSNEWS is the first candidate with the right shape at usable size.** Identified journalists,
each with **bylined news articles** and **their own social-media posts** — two registers, two
audiences, two purposes, same person. Maker identity comes from a Wikidata → verified-account →
byline chain, which is a stronger link than the inferred handles most social corpora rely on.

── THE ONE NUMBER THAT DECIDES IT ────────────────────────────────────────────────────────────

**The social-media half is almost certainly far shorter than the article half.** Our measures need
roughly 300 words minimum and prefer 1,000+. If posts are 30 words, then an "artifact" has to become
*a concatenation of one person's posts*, which changes what is being measured — a pseudo-document is
not an artifact, and a maker's aggregated posting is not a thing they made.

**So this reads the length distribution per genre BEFORE committing to the 1.3 GB download**, and
reports how many makers survive at each length threshold. That is the decision, and it should be made
on the number rather than on the corpus's description of itself.

── WHAT IT REPORTS ───────────────────────────────────────────────────────────────────────────

    per genre       median, quartiles, and the share of artifacts over 300 and over 1000 words
    per maker       how many makers have at least 3 artifacts in EACH genre at each threshold
    the verdict     whether the corpus supports the design at artifact level, only at
                    pseudo-document level, or not at all

**Streaming, so nothing is downloaded that is not read.**
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

OUT = REPO / "corpora" / "public" / "crossnews"
REPO_ID = "gabrielloiseau/CROSSNEWS"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--scan", type=int, default=40000, help="rows to stream for the length survey")
    ap.add_argument("--download", action="store_true",
                    help="after the survey, materialise the usable subset to disk")
    ap.add_argument("--min-words", type=int, default=300)
    ap.add_argument("--per-genre", type=int, default=3, help="artifacts per maker per genre")
    args = ap.parse_args()

    import numpy as np                                               # noqa: PLC0415
    from datasets import load_dataset                                # noqa: PLC0415

    print(f"streaming {REPO_ID} ...", flush=True)
    ds = load_dataset(REPO_ID, split="train", streaming=True)

    lens = defaultdict(list)
    by_maker = defaultdict(lambda: defaultdict(list))
    genres = Counter()
    seen = 0
    for row in ds:
        text = row.get("text") or ""
        author = str(row.get("author", "?"))
        genre = str(row.get("genre", "?"))
        n = len(text.split())
        lens[genre].append(n)
        genres[genre] += 1
        by_maker[author][genre].append(n)
        seen += 1
        if seen >= args.scan:
            break
    print(f"  scanned {seen:,} rows, {len(by_maker):,} makers, genres {dict(genres)}\n")

    print(f"{'genre':<14}{'n':>8}{'median':>9}{'25th':>7}{'75th':>7}{'>=300w':>9}{'>=1000w':>10}")
    print("-" * 64)
    summary = {}
    for g, v in sorted(lens.items()):
        a = np.array(v)
        summary[g] = {"n": len(a), "median": float(np.median(a)),
                      "q25": float(np.percentile(a, 25)), "q75": float(np.percentile(a, 75)),
                      "over_300": float((a >= 300).mean()), "over_1000": float((a >= 1000).mean())}
        s = summary[g]
        print(f"{g:<14}{s['n']:>8}{s['median']:>9.0f}{s['q25']:>7.0f}{s['q75']:>7.0f}"
              f"{s['over_300']:>8.1%}{s['over_1000']:>10.1%}")

    print(f"\n{'threshold':>10}{'makers with ' + str(args.per_genre) + '+ in EVERY genre':>38}")
    print("-" * 50)
    usable = {}
    for thr in (0, 100, 300, 500, 1000):
        k = sum(1 for m, gs in by_maker.items()
                if len(gs) >= 2 and all(sum(1 for n in v if n >= thr) >= args.per_genre
                                        for v in gs.values()))
        usable[thr] = k
        print(f"{thr:>10}{k:>38}")

    at_min = usable.get(args.min_words, 0)
    if at_min >= 20:
        verdict = "USABLE AT ARTIFACT LEVEL"
    elif usable.get(0, 0) >= 20:
        verdict = "PSEUDO-DOCUMENTS ONLY"
    else:
        verdict = "NOT USABLE"
    print(f"\n  >>> {verdict}")
    if verdict == "PSEUDO-DOCUMENTS ONLY":
        print(f"  Enough makers, but not enough long artifacts at {args.min_words} words.")
        print("  An artifact would have to become a concatenation of one person's posts, and a")
        print("  maker's aggregated posting is not a thing they made. That is a different design.")
    elif verdict == "NOT USABLE":
        print("  Too few makers have artifacts in both genres in this sample.")
    print(f"\n  NOTE: scanned the first {seen:,} rows only. The full set is ~1.48M rows, so a")
    print("  maker's second genre may simply not have appeared yet. Re-run with a larger --scan")
    print("  before treating a low maker count as final.")

    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "survey.json").write_text(json.dumps(
        {"repo": REPO_ID, "scanned": seen, "genres": dict(genres),
         "length_by_genre": summary, "makers_by_threshold": usable,
         "verdict": verdict}, indent=2), encoding="utf-8", newline="\n")
    print(f"\nwrote {(OUT / 'survey.json').relative_to(REPO)}")

    if args.download and verdict != "NOT USABLE":
        print("\n--download was set; materialising the usable subset ...", flush=True)
        keep = {m for m, gs in by_maker.items()
                if len(gs) >= 2 and all(sum(1 for n in v if n >= args.min_words) >= args.per_genre
                                        for v in gs.values())}
        ds2 = load_dataset(REPO_ID, split="train", streaming=True)
        kept, idx = [], 0
        for row in ds2:
            if str(row.get("author", "?")) in keep and \
                    len((row.get("text") or "").split()) >= args.min_words:
                kept.append({"id": f"cn_{idx:05d}", "author": str(row["author"]),
                             "genre": str(row.get("genre", "?")),
                             "n_words": len((row["text"]).split())})
                (OUT / f"cn_{idx:05d}.txt").write_text(row["text"], encoding="utf-8", newline="\n")
                idx += 1
        (OUT / "manifest.json").write_text(json.dumps(
            {"source": REPO_ID, "min_words": args.min_words, "items": kept},
            indent=2), encoding="utf-8", newline="\n")
        print(f"  wrote {len(kept)} artifacts from {len(keep)} makers")


if __name__ == "__main__":
    main()
