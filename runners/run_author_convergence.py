"""G60 — the convergence-rate claim, measured on the corpus we hold: does recovery of a maker
sharpen with more works, and toward what asymptote?

§8's disagreement with the impossibility proofs is a claim about a **convergence rate**: recovery
error shrinks with more artifacts by one maker, toward a small residual — *"report the asymptote,
not just the slope."* Nobody has measured either. The 34-book, ~10-author corpus supports the
first measurable version: author recovery from function words as a function of how many works the
reader has seen.

── THE TEST ──────────────────────────────────────────────────────────────────────────────────

Split each book into 1,000-word chunks. For k = 1..3 reference works per author, classify held-out
chunks by nearest author centroid (function-word rates, cosine). Accuracy(k) is the convergence
curve; the gap between accuracy(max k) and 100% is the residual the theorems say must exist.

    CONVERGES   accuracy rises monotonically with k and the curve visibly flattens
    FLAT        more works do not help — the one-episode limit binds harder than claimed
"""

from __future__ import annotations

import json
import re
import sys
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

RESULTS = REPO / "results" / "author_convergence"

FUNCTION_WORDS = ("the a an and or but if then than of to in on at by for with from as is are was "
                  "were be been being have has had do does did will would shall should may might "
                  "can could must not no nor so yet it its he she they we you i his her their our "
                  "your my this that these those there here when where who whom which what while "
                  "because although though upon into over under between through during before "
                  "after above below again once only very too also just both each few more most "
                  "other some such own same about against").split()


def fw_vector(text: str):
    import numpy as np                                                # noqa: PLC0415
    toks = re.findall(r"[a-z']+", text.lower())
    n = max(len(toks), 1)
    c = Counter(toks)
    return np.array([c[w] / n for w in FUNCTION_WORDS], dtype=float)


def main() -> None:
    import numpy as np                                                # noqa: PLC0415

    man = json.loads((REPO / "corpora" / "manifests" / "books.json").read_text(encoding="utf-8"))
    items = man["items"] if isinstance(man, dict) else man
    by_author: dict[str, list[list]] = {}
    for it in items:
        p = REPO / "corpora" / "store" / f"{it['id']}.txt"
        if not p.exists():
            continue
        words = p.read_text(encoding="utf-8", errors="ignore").split()
        chunks = [" ".join(words[i:i + 1000]) for i in range(2000, len(words) - 1000, 1000)]
        if len(chunks) < 6:
            continue
        by_author.setdefault(it["author"], []).append([fw_vector(c) for c in chunks[:40]])
    by_author = {a: w for a, w in by_author.items() if len(w) >= 4}
    authors = sorted(by_author)
    print(f"{len(authors)} authors with >= 4 usable works")

    rng = np.random.default_rng(3)
    max_k = 3
    curve = {}
    for k in range(1, max_k + 1):
        correct = total = 0
        for trial in range(20):
            cents, tests = {}, {}
            for a in authors:
                works = list(range(len(by_author[a])))
                rng.shuffle(works)
                ref, held = works[:k], works[k]
                cents[a] = np.mean([v for w in ref for v in by_author[a][w]], axis=0)
                tests[a] = by_author[a][held]
            for a in authors:
                for v in tests[a]:
                    sims = {b: float(np.dot(v, c) / (np.linalg.norm(v) * np.linalg.norm(c) + 1e-12))
                            for b, c in cents.items()}
                    correct += max(sims, key=sims.get) == a
                    total += 1
        curve[k] = correct / total
        print(f"  k={k} reference works: accuracy {curve[k]:.3f}  (chance {1 / len(authors):.3f})")

    ks = sorted(curve)
    mono = all(curve[ks[i + 1]] >= curve[ks[i]] - 0.01 for i in range(len(ks) - 1))
    gain_last = curve[ks[-1]] - curve[ks[-2]]
    gain_first = curve[ks[1]] - curve[ks[0]]
    flattening = gain_last < gain_first
    verdict = "CONVERGES" if mono and curve[ks[-1]] > curve[ks[0]] else "FLAT"
    resid = 1 - curve[ks[-1]]
    print(f"\n  residual at k={ks[-1]}: {resid:.3f}   flattening: {flattening}")
    print(f"  >>> {verdict}")

    RESULTS.mkdir(parents=True, exist_ok=True)
    (RESULTS / "summary.json").write_text(json.dumps(
        {"n_authors": len(authors), "chance": 1 / len(authors), "curve": curve,
         "residual_at_max_k": resid, "flattening": flattening, "verdict": verdict}, indent=2),
        encoding="utf-8", newline="\n")
    print(f"wrote {(RESULTS / 'summary.json').relative_to(REPO)}")


if __name__ == "__main__":
    main()
