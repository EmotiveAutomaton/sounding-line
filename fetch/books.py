"""G — a long-form corpus, so the measurement has enough text to work with.

── WHY THIS EXISTS ───────────────────────────────────────────────────────────────────────────

D-0 was inconclusive because 380-word samples give about five tokens in a function-word category,
and five is not a number you can do statistics with. The curator's response reframed the whole
approach:

    It might have always been true that we needed to start on whole books and then scale down to
    articles. Just because of the resolution that we're going to have to be gaining.

That is right, and it is the standard design in stylometry rather than a workaround: work where
the signal is unambiguous, then **calibrate downward until it breaks**, which tells you the actual
resolution limit instead of guessing it.

    380-word generation      ~5 tokens in a category      D-0's failure
    3,000-word essay        ~40 tokens                    the Gate 3 corpus
    100,000-word book     ~1,300 tokens                   here

── AND IT SOLVES THE OTHER BLOCKER AT THE SAME TIME ──────────────────────────────────────────

`measures/leakage.py` says a corpus-mean baseline answers *"unusual for this collection"* when the
question is *"unusual for this person"*. A per-maker baseline needs several works by one maker.

Public-domain books give that for free: multiple works per author, written years apart, on
different topics, with the author known. **That is exactly the design authorship attribution uses**,
and it is available for the cost of a download.

── PROVENANCE ────────────────────────────────────────────────────────────────────────────────

Project Gutenberg, plain-text mirror, robots.txt honoured, one request per host per interval, via
the same `Fetcher` everything else uses — so the fetch/analysis isolation holds here too. Nothing
is re-hosted; the store is gitignored and the manifest carries hashes and URLs.

Authors chosen for **spread within author** rather than for literary merit: several works each,
separated in time, in more than one register where possible. A corpus of one book per author would
measure authors; this is meant to measure how much of a maker survives across their own range.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fetch.fetcher import Fetcher, FetchRefused          # noqa: E402

MANIFEST = Path(__file__).resolve().parents[1] / "corpora" / "manifests" / "books.json"
GUTENBERG = "https://www.gutenberg.org/cache/epub/{id}/pg{id}.txt"

# Author -> [(gutenberg id, short title)]. Several works each, spread across a career, and mixed
# register where the author has one. Ids are Project Gutenberg ebook numbers.
AUTHORS: dict[str, list[tuple[int, str]]] = {
    "austen":      [(1342, "pride-and-prejudice"), (161, "sense-and-sensibility"),
                    (121, "northanger-abbey"), (105, "persuasion")],
    "dickens":     [(98, "tale-of-two-cities"), (1400, "great-expectations"),
                    (766, "david-copperfield"), (46, "christmas-carol")],
    "twain":       [(76, "huckleberry-finn"), (74, "tom-sawyer"),
                    (86, "connecticut-yankee"), (3176, "innocents-abroad")],
    "eliot":       [(145, "middlemarch"), (507, "silas-marner"), (6688, "mill-on-the-floss")],
    "conan-doyle": [(1661, "adventures-of-sherlock-holmes"), (2852, "hound-of-the-baskervilles"),
                    (139, "the-lost-world"), (244, "study-in-scarlet")],
    "wells":       [(35, "time-machine"), (36, "war-of-the-worlds"),
                    (5230, "invisible-man"), (159, "island-of-doctor-moreau")],
    "stevenson":   [(43, "jekyll-and-hyde"), (120, "treasure-island"), (421, "kidnapped")],
    "melville":    [(2701, "moby-dick"), (11231, "bartleby"), (15859, "typee")],
    "wollstonecraft": [(3420, "vindication-rights-of-woman"), (16199, "letters-sweden")],
    "darwin":      [(1228, "origin-of-species"), (2300, "voyage-of-the-beagle"),
                    (1227, "expression-of-emotions")],
}

# Gutenberg wraps each text in a licence header and footer. They are boilerplate, identical across
# every book, and would dominate a function-word profile of a short excerpt — so they come off
# before anything is measured. Removing them is not sanitisation of the artifact; they were never
# part of it.
_START = re.compile(r"\*\*\*\s*START OF (THE|THIS) PROJECT GUTENBERG EBOOK.*?\*\*\*", re.I | re.S)
_END = re.compile(r"\*\*\*\s*END OF (THE|THIS) PROJECT GUTENBERG EBOOK.*?\*\*\*", re.I | re.S)


def strip_boilerplate(text: str) -> str:
    m = _START.search(text)
    if m:
        text = text[m.end():]
    m = _END.search(text)
    if m:
        text = text[: m.start()]
    return text.strip()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--authors", nargs="*", default=sorted(AUTHORS))
    ap.add_argument("--limit-per-author", type=int, default=0)
    args = ap.parse_args()

    f = Fetcher(allow_hosts={"www.gutenberg.org", "gutenberg.org"})
    items, failed = [], []
    for author in args.authors:
        works = AUTHORS[author]
        if args.limit_per_author:
            works = works[: args.limit_per_author]
        for gid, title in works:
            url = GUTENBERG.format(id=gid)
            try:
                rec = f.fetch(url)
            except (FetchRefused, Exception) as e:               # noqa: BLE001
                failed.append(f"{author}/{title}: {type(e).__name__}: {e}")
                print(f"  {author:<16}{title:<32} FAILED  {type(e).__name__}", flush=True)
                continue
            items.append({"id": f"{author}__{title}", "author": author, "title": title,
                          "gutenberg_id": gid, "url": url, "final_url": rec.final_url,
                          "sha256": rec.sha256, "n_chars": rec.n_chars,
                          "robots_allowed": rec.robots_allowed})
            print(f"  {author:<16}{title:<32} {rec.n_chars:>9,} chars", flush=True)

    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST.write_text(json.dumps(
        {"name": "books", "source": "Project Gutenberg",
         "why": "long-form calibration (G) and per-maker baselines (H); see fetch/books.py",
         "boilerplate": "Gutenberg header/footer stripped at read time, not at fetch time",
         "failed": failed, "items": items}, indent=2), encoding="utf-8")
    print(f"\n{len(items)} works, {len({i['author'] for i in items})} authors "
          f"-> {MANIFEST.name}   ({len(failed)} failed)")


if __name__ == "__main__":
    main()
