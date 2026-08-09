"""PD-33 — does the polish side's essay-boundness follow the AUTHOR or the DRAFT?

L55's accidental positive: polish-side features carry a 20% between-essay variance share against
the depth side's 8%, at fixed topic. "Essay" conflates author with draft stage (258 items = 86
authors x up to 3 drafts). This decomposes the between-share by grouping unit. If the polish
side's excess share follows the author, the maker-signature reading stands; if it follows the
draft stage, it is revision state.

    MAKER     polish-side author-share exceeds depth-side author-share, and the draft-within-
              author shares do not carry the split
    STATE     the split lives in draft-within-author instead
    MIXED     both carry it at comparable size
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

RESULTS = REPO / "results" / "positional_polish"
CACHE = REPO / "results" / "features" / "argrewrite_w80.json"

POLISH_PATTERNS = ("readability", "flesch", "ttr", "type_token", "punct", "exclam",
                   "uppercase", "smog", "coleman", "kincaid", "ari_", "lix", "rix",
                   "unique_tokens")
DEPTH_PATTERNS = ("caus", "conc", "cond", "osub", "whcl", "whsub", "whobj", "thac",
                  "thvc", "tsub", "tobj", "nomz", "bypa", "pastp", "wzpast", "wzpres",
                  "presp", "pire", "dependency_distance")


def parse_ids(item_id: str) -> tuple[str, str]:
    # cache ids run "<author>_d<draft>", e.g. 10_d2
    m = re.fullmatch(r"(\d+)_d(\d+)", item_id)
    if not m:
        raise ValueError(f"unparseable item id {item_id!r}")
    return m.group(1), f"d{m.group(2)}"


def main() -> None:
    import numpy as np                                                # noqa: PLC0415
    from scipy import stats                                           # noqa: PLC0415

    items = [it for it in json.loads(CACHE.read_text(encoding="utf-8"))["items"]
             if it.get("windows")]
    keys = sorted(set.intersection(*(set(it["windows"][0]) for it in items)))
    pol = [k for k in keys if any(p in k.lower() for p in POLISH_PATTERNS)]
    dep = [k for k in keys if any(p in k.lower() for p in DEPTH_PATTERNS)]
    authors = [parse_ids(it["id"])[0] for it in items]
    print(f"{len(items)} items, {len(set(authors))} authors, "
          f"{len(pol)} polish / {len(dep)} depth features")

    def shares(k: str) -> tuple[float, float] | None:
        # variance decomposition: author share of pool variance, then draft-within-author share
        vals, labs = [], []
        for it, a in zip(items, authors):
            for w in it["windows"]:
                v = float(w.get(k, 0.0) or 0.0)
                if np.isfinite(v):
                    vals.append(v)
                    labs.append((a, it["id"]))
        v = np.array(vals)
        if v.std() <= 0:
            return None
        pool = v.var()
        agg_a = {}
        for x, (a, _) in zip(v, labs):
            agg_a.setdefault(a, []).append(x)
        n = len(v)
        between_author = sum(len(g) * (np.mean(g) - v.mean()) ** 2 for g in agg_a.values()) / n
        agg_d = {}
        for x, (a, d) in zip(v, labs):
            agg_d.setdefault((a, d), []).append(x)
        between_draft_total = sum(len(g) * (np.mean(g) - v.mean()) ** 2
                                  for g in agg_d.values()) / n
        draft_within = max(between_draft_total - between_author, 0.0)
        return float(between_author / pool), float(draft_within / pool)

    # known-answer gate: a planted author-constant feature must land ~(1, 0); a planted
    # draft-varying author-centred feature must land ~(0, 1)
    rng = np.random.default_rng(3)
    fake_items = items
    author_vals = {a: rng.normal() for a in set(authors)}
    draft_vals = {it["id"]: rng.normal() for it in items}
    for it, a in zip(fake_items, authors):
        for w in it["windows"]:
            w["_ka_author"] = author_vals[a]
            w["_ka_draft"] = draft_vals[it["id"]] - author_vals[a] * 0  # draft-only signal
    ga = shares("_ka_author")
    gd = shares("_ka_draft")
    print(f"gate: author-constant feature shares {ga}; draft-varying shares {gd}")
    if not (ga and ga[0] > 0.95 and gd and gd[1] > 0.4):
        print(">>> GATE-FAILED")
        sys.exit(1)

    def side(ks):
        rows = [s for s in (shares(k) for k in ks) if s is not None]
        a = np.array([r[0] for r in rows])
        d = np.array([r[1] for r in rows])
        return a, d

    pa, pd_ = side(pol)
    da, dd = side(dep)
    _, p_author = stats.mannwhitneyu(pa, da, alternative="two-sided")
    _, p_draft = stats.mannwhitneyu(pd_, dd, alternative="two-sided")
    med = {"polish_author": float(np.median(pa)), "depth_author": float(np.median(da)),
           "polish_draft": float(np.median(pd_)), "depth_draft": float(np.median(dd))}
    author_gap = med["polish_author"] - med["depth_author"]
    draft_gap = med["polish_draft"] - med["depth_draft"]
    if author_gap > 2 * abs(draft_gap) and p_author < 0.05:
        verdict = "MAKER"
    elif abs(draft_gap) > 2 * abs(author_gap) and p_draft < 0.05:
        verdict = "STATE"
    else:
        verdict = "MIXED"
    print(f"author shares: polish {med['polish_author']:.3f} vs depth {med['depth_author']:.3f} "
          f"(p={p_author:.2e}) | draft-within: {med['polish_draft']:.3f} vs "
          f"{med['depth_draft']:.3f} (p={p_draft:.2e})\n  >>> {verdict}")

    RESULTS.mkdir(parents=True, exist_ok=True)
    (RESULTS / "pd33_decomposition.json").write_text(json.dumps(
        {"n_items": len(items), "n_authors": len(set(authors)), **med,
         "p_author": float(p_author), "p_draft": float(p_draft), "verdict": verdict},
        indent=2), encoding="utf-8", newline="\n")
    print(f"wrote {(RESULTS / 'pd33_decomposition.json').relative_to(REPO)}")


if __name__ == "__main__":
    main()
