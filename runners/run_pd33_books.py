"""PD-33b — does the polish-side author-share excess replicate on books?

L57 found polish-side features carry half again the depth side's author-share on student essays
at fixed topic. Books are the adversarial replication surface, since topic varies freely with
author, so author-share here includes topic. The comparison that survives that contamination is
the SIDE CONTRAST, as both sides face the same topic mixture; if the polish side's excess is a
maker signature it should persist, and if it was an essay-corpus artifact it should vanish.

    REPLICATES   polish-side author-share exceeds depth-side, same direction as L57, p < 0.05
    FAILS        no side difference, or reversed
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

RESULTS = REPO / "results" / "positional_polish"
CACHE = REPO / "results" / "features" / "books_w80.json"

POLISH_PATTERNS = ("readability", "flesch", "ttr", "type_token", "punct", "exclam",
                   "uppercase", "smog", "coleman", "kincaid", "ari_", "lix", "rix",
                   "unique_tokens")
DEPTH_PATTERNS = ("caus", "conc", "cond", "osub", "whcl", "whsub", "whobj", "thac",
                  "thvc", "tsub", "tobj", "nomz", "bypa", "pastp", "wzpast", "wzpres",
                  "presp", "pire", "dependency_distance")


def main() -> None:
    import argparse                                                   # noqa: PLC0415
    import numpy as np                                                # noqa: PLC0415
    from scipy import stats                                           # noqa: PLC0415

    ap = argparse.ArgumentParser()
    ap.add_argument("--cache", default=str(CACHE))
    ap.add_argument("--out", default=str(RESULTS / "pd33_books.json"))
    args = ap.parse_args()

    items = [it for it in json.loads(Path(args.cache).read_text(encoding="utf-8"))["items"]
             if it.get("windows")]
    keys = sorted(set.intersection(*(set(it["windows"][0]) for it in items)))
    pol = [k for k in keys if any(p in k.lower() for p in POLISH_PATTERNS)]
    dep = [k for k in keys if any(p in k.lower() for p in DEPTH_PATTERNS)]
    authors = [it["id"].split("__")[0] for it in items]
    n_auth = len(set(authors))
    print(f"{len(items)} segments, {n_auth} authors, {len(pol)} polish / {len(dep)} depth")
    if n_auth < 8:
        print(">>> NEEDS-DATA -- too few authors")
        sys.exit(1)

    def author_share(k: str) -> float | None:
        vals, labs = [], []
        for it, a in zip(items, authors):
            for w in it["windows"]:
                v = float(w.get(k, 0.0) or 0.0)
                if np.isfinite(v):
                    vals.append(v)
                    labs.append(a)
        v = np.array(vals)
        if v.std() <= 0:
            return None
        agg: dict[str, list[float]] = {}
        for x, a in zip(v, labs):
            agg.setdefault(a, []).append(x)
        between = sum(len(g) * (np.mean(g) - v.mean()) ** 2 for g in agg.values()) / len(v)
        return float(between / v.var())

    # known-answer gate, same as L57's: a planted author-constant feature must land ~1
    rng = np.random.default_rng(5)
    av = {a: rng.normal() for a in set(authors)}
    for it, a in zip(items, authors):
        for w in it["windows"]:
            w["_ka"] = av[a]
    ga = author_share("_ka")
    print(f"gate: author-constant share {ga:.4f}")
    if ga is None or ga < 0.95:
        print(">>> GATE-FAILED")
        sys.exit(1)

    pa = np.array([s for s in (author_share(k) for k in pol) if s is not None])
    da = np.array([s for s in (author_share(k) for k in dep) if s is not None])
    _, p = stats.mannwhitneyu(pa, da, alternative="two-sided")
    pm, dm = float(np.median(pa)), float(np.median(da))
    verdict = ("REPLICATES" if pm > dm and p < 0.05 else
               "REVERSED" if dm > pm and p < 0.05 else "NO-DIFFERENCE")
    print(f"author share: polish {pm:.3f} vs depth {dm:.3f} (p={p:.2e})\n  >>> {verdict}")

    RESULTS.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(
        {"n_segments": len(items), "n_authors": n_auth, "polish_median": pm,
         "depth_median": dm, "p": float(p), "verdict": verdict}, indent=2),
        encoding="utf-8", newline="\n")
    print(f"wrote {Path(args.out).relative_to(REPO)}")


if __name__ == "__main__":
    main()
