"""ArgRewrite — the first controlled comparison on HUMAN text this project has ever had.

── WHY THIS IS DIFFERENT FROM EVERY CORPUS BEFORE IT ─────────────────────────────────────────

`FINDINGS.md` weakness 1, unchanged for the life of the project: **every positive rides on
machine-written or public-domain text, and we have never had a controlled corpus of human
artifacts.** Every uncontrolled human comparison has died to register.

ArgRewrite fixes exactly that. 86 university students, one prompt, three drafts each:

    draft 1     first attempt
    draft 2     revised after feedback
    draft 3     revised again

**Maker, prompt, topic, register and genre are all held constant by the same person writing the same
essay three times.** The only thing that moves is how much revision intent has been applied. It is
the human version of the ladder, and it is paired — every comparison is within one author.

── THE TEST, PRE-REGISTERED ──────────────────────────────────────────────────────────────────

Every measure is scored **within author**, as the change from draft 1 to draft 3, so between-person
variation cannot contribute anything at all.

    PASS       a measure moves monotonically across drafts, sign-consistent in a clear majority of
               the 86 authors, surviving a length control and Benjamini-Yekutieli correction
    FAIL       no measure moves within author

**The length trap is live here.** Drafts get longer (median 493 -> 562 -> 627 words, +27%). Any
measure that is really a length measure will sail through, so the paired test is reported both raw
and on length-matched windows.

**And the direction is not obvious.** Revision could raise decision density (more deliberate choices)
or lower it (the maker converging, cleaning up, removing options). We do not predict a sign, and
recording that here means we cannot claim one afterwards.

── WHAT MAKES THIS CORPUS UNUSUAL, AND IT IS THE PART TO EXPLOIT LATER ───────────────────────

It ships 5,834 human-annotated revisions on a taxonomy that splits **Surface** (word usage,
spelling/grammar, organization) from **Content** (claim, evidence, reasoning, rebuttal, precision,
development), with inter-annotator agreement 0.71-0.92.

**That is the polish/depth split, labelled by people, at scale.** This runner does not use the
annotations yet — it establishes first whether anything moves at all.
"""

from __future__ import annotations

import argparse
import contextlib
import io
import json
import re
import statistics
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

DATA = REPO / "corpora" / "public" / "argrewrite" / "essays"
RESULTS = REPO / "results" / "argrewrite"


def load() -> dict[str, dict[int, str]]:
    """{author_id: {draft_number: text}} for authors present in all three drafts."""
    by: dict[str, dict[int, str]] = {}
    for d in sorted(DATA.iterdir()):
        if not d.is_dir():
            continue
        n = int(re.findall(r"\d+", d.name)[0])
        for f in d.glob("*.txt"):
            nums = re.findall(r"\d+", f.stem)
            if not nums:
                continue
            by.setdefault(nums[-1], {})[n] = f.read_text(encoding="utf-8", errors="ignore")
    return {a: v for a, v in by.items() if len(v) == 3}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--cap", type=int, default=0, help="limit authors, for a smoke test")
    ap.add_argument("--length-matched", action="store_true",
                    help="truncate every draft of an author to their SHORTEST draft, so word "
                         "count is identical across the comparison by construction")
    args = ap.parse_args()

    import numpy as np                                                # noqa: PLC0415
    from scipy import stats                                           # noqa: PLC0415

    from soundingline.measures.features import extract                # noqa: PLC0415
    from soundingline.measures.select import relevance                # noqa: PLC0415

    authors = load()
    if args.cap:
        authors = dict(list(authors.items())[: args.cap])
    print(f"{len(authors)} authors with all three drafts", flush=True)

    buf = io.StringIO()
    rows = []
    for i, (aid, drafts) in enumerate(authors.items()):
        if args.length_matched:
            n = min(len(t.split()) for t in drafts.values())
            drafts = {d: " ".join(t.split()[:n]) for d, t in drafts.items()}
        with contextlib.redirect_stdout(buf):
            f = {d: extract(t) for d, t in drafts.items()}
        rows.append({"author": aid, "feats": f,
                     "words": {d: len(t.split()) for d, t in drafts.items()}})
        if (i + 1) % 10 == 0:
            print(f"  {i + 1}/{len(authors)}", flush=True)

    keys = sorted(set.intersection(*(set(r["feats"][d]) for r in rows for d in (1, 2, 3))))
    print(f"\n{len(keys)} features present in every draft of every author\n", flush=True)

    # ── the paired within-author test ─────────────────────────────────────────────────────────
    out = []
    for k in keys:
        d1 = np.array([r["feats"][1].get(k, np.nan) for r in rows])
        d3 = np.array([r["feats"][3].get(k, np.nan) for r in rows])
        if not (np.isfinite(d1).all() and np.isfinite(d3).all()):
            continue
        delta = d3 - d1
        if np.allclose(delta, 0):
            continue
        # Wilcoxon signed-rank: paired, non-parametric, ignores between-person variation entirely
        try:
            stat, p = stats.wilcoxon(d1, d3)
        except ValueError:
            continue
        agree = float(np.mean(np.sign(delta) == np.sign(np.median(delta))))
        out.append({"feature": k, "p": float(p), "median_delta": float(np.median(delta)),
                    "sign_agreement": agree})

    # correct for having tested ~340 of them
    import pandas as pd                                               # noqa: PLC0415
    tbl = pd.DataFrame(out).sort_values("p")
    n = len(tbl)
    c = sum(1.0 / k for k in range(1, n + 1))                          # Benjamini-Yekutieli
    tbl["p_adj"] = (tbl["p"] * n / (np.arange(n) + 1) * c).cummax().clip(upper=1.0)
    surv = tbl[tbl["p_adj"] < 0.05]

    print(f"{'feature':<34}{'median change':>15}{'sign agree':>12}{'p (corrected)':>15}")
    print("-" * 78)
    for _, r in surv.head(20).iterrows():
        print(f"{r['feature']:<34}{r['median_delta']:>+15.4f}{r['sign_agreement']:>11.0%}"
              f"{r['p_adj']:>15.2e}")

    wd = [r["words"] for r in rows]
    print(f"\nlength: draft1 {statistics.median(w[1] for w in wd):.0f}w  "
          f"draft3 {statistics.median(w[3] for w in wd):.0f}w  "
          f"(+{statistics.median(w[3] for w in wd) / statistics.median(w[1] for w in wd) - 1:.0%})")
    print(f"\n{n} features tested, {len(surv)} survive correction "
          f"({0.05 * n:.0f} expected by chance)")
    print("\n>>> " + ("SOMETHING MOVES within author across drafts. Length control owed next."
                      if len(surv) else
                      "NOTHING moves within author. A clean null on the first controlled "
                      "human corpus."))

    RESULTS.mkdir(parents=True, exist_ok=True)
    name = "drafts_length_matched.json" if args.length_matched else "drafts.json"
    (RESULTS / name).write_text(json.dumps(
        {"n_authors": len(rows), "n_features": n, "n_survive": int(len(surv)),
         "median_words": {str(d): statistics.median(w[d] for w in wd) for d in (1, 2, 3)},
         "survivors": surv.head(60).to_dict("records")}, indent=2),
        encoding="utf-8", newline="\n")
    print(f"\nwrote {(RESULTS / 'drafts.json').relative_to(REPO)}")


if __name__ == "__main__":
    main()
