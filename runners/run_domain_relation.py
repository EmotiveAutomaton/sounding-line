"""Is depth a property of the writer, or a relation between the writer and the domain?

── THE CLAIM ─────────────────────────────────────────────────────────────────────────────────

The curator's, and it is the sharpest definition in the project:

    Depth is a property of the writer WITH RESPECT TO THE DOMAIN. It does not vary within an
    artifact unless the domain does.

**That makes depth a relation rather than an attribute**, and it arrived with its own falsifier
attached: **depth moves where domain moves.** It also explains why the missing corpus is fatal rather
than inconvenient — **a relation cannot be measured by varying one side**, and every measure this
project has built read artifacts alone.

`HUMAN_HEURISTICS.md` §4 has listed this as *blocked on a corpus that does not exist* since it was
written.

── WHAT THIS IS, AND WHAT IT IS NOT ──────────────────────────────────────────────────────────

**It is a pilot, at n = 3 makers.** The corpus we hold has ten authors and thirty-four works, and
**three of them wrote across genuinely different kinds**:

    Darwin           scientific treatise      vs   travel journal
    Twain            novels                   vs   travel reportage
    Wollstonecraft   political philosophy     vs   epistolary travel letters

**It is not the corpus the claim needs.** Three makers, 19th-century prose, and the kind labels are a
judgement rather than a datum. **What it can do is tell us whether the falsifier is worth the cost of
sourcing properly** — and it is runnable today on data already on disk, which nothing else about this
hypothesis has been.

── THE DESIGN ────────────────────────────────────────────────────────────────────────────────

For each maker, take windows from every work, and compare two distances:

    WITHIN-KIND     windows from two different works of the SAME kind by that maker
    ACROSS-KIND     windows from two works of DIFFERENT kinds by that maker

**The maker is held fixed in both.** If depth is an attribute of the writer, the two distances should
be the same — the writer is the same writer. **If depth is a relation to the domain, across-kind
should be reliably larger.**

**And the control that makes it interpretable is a second measure that should NOT move.** Authorship
signal — function words, which carry identity — should be roughly as recoverable across kinds as
within them, because the person did not change. **A design where both measures move equally has
measured genre, not depth.**

    depth-side     the reader's affect-projection profile, which is what this project measures
    identity-side  function-word rates, sixty years of authorship attribution behind them

── PRE-REGISTERED, BEFORE THE RUN ────────────────────────────────────────────────────────────

    RELATION    the depth-side distance is larger across kinds than within, in a majority of makers,
                AND the identity-side distance is not. Depth moves with domain; identity does not
    ATTRIBUTE   the depth-side distance is the same across and within kinds. Depth is a property of
                the writer and the definition is wrong
    GENRE       both distances grow across kinds. **The design cannot separate depth from genre**
                and this is a void rather than a result

**GENRE is the most likely outcome and it is the reason for the second measure.** Without it, any
across-kind difference would be uninterpretable — which is the trap every register-confounded result
in this project has fallen into.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

RESULTS = REPO / "results" / "domain_relation"

# Kind labels are a judgement, not a datum in the corpus. Stated here so they can be argued with.
KINDS: dict[str, str] = {
    "origin-of-species": "treatise", "expression-of-emotions": "treatise",
    "voyage-of-the-beagle": "travel",
    "huckleberry-finn": "novel", "tom-sawyer": "novel", "connecticut-yankee": "novel",
    "innocents-abroad": "travel",
    "vindication-rights-of-woman": "treatise", "letters-sweden": "travel",
}

FUNCTION_WORDS = (
    "a about above after again against all am an and any are as at be because been before being "
    "below between both but by can did do does doing down during each few for from further had has "
    "have having he her here hers herself him himself his how i if in into is it its itself just me "
    "more most my myself no nor not now of off on once only or other our ours ourselves out over own "
    "same she should so some such than that the their theirs them themselves then there these they "
    "this those through to too under until up very was we were what when where which while who whom "
    "why will with you your yours yourself yourselves"
).split()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--window", type=int, default=1200, help="words per window")
    ap.add_argument("--per-work", type=int, default=10)
    ap.add_argument("--model", default=None)
    ap.add_argument("--device", default="cuda")
    args = ap.parse_args()

    import numpy as np                                               # noqa: PLC0415
    from collections import Counter                                  # noqa: PLC0415

    from soundingline.probe.activations import (DEFAULT_MODEL, Reader,  # noqa: PLC0415
                                                fit_directions)
    from runners.run_b import split                                  # noqa: PLC0415
    from runners.run_g import load_books, windows                    # noqa: PLC0415

    books = [b for b in load_books()
             if KINDS.get(b.get("title", b["url"].split("/")[-1]))]
    for b in books:
        b["kind"] = KINDS[b.get("title", b["url"].split("/")[-1])]
    makers = sorted({b["author"] for b in books})
    usable = [m for m in makers
              if len({b["kind"] for b in books if b["author"] == m}) >= 2]
    print(f"{len(books)} works, {len(makers)} makers, {len(usable)} with two kinds: {usable}\n")
    for m in usable:
        for b in [x for x in books if x["author"] == m]:
            print(f"  {m:<16}{b['kind']:<11}{b.get('title', '?')}")

    model_name = args.model or DEFAULT_MODEL
    print(f"\nloading {model_name} ...", flush=True)
    reader = Reader(model_name, device=args.device)
    fit, _ = split()
    dirs = fit_directions(reader, fit)
    n_layers = dirs.n_layers
    concepts = list(dirs.concepts)

    def fw(text: str) -> np.ndarray:
        toks = [w.strip(".,;:!?\"'()[]—-").lower() for w in text.split()]
        c = Counter(t for t in toks if t)
        n = max(len(toks), 1)
        return np.array([c[w] / n * 1000 for w in FUNCTION_WORDS])

    per_work = {}
    for b in books:
        if b["author"] not in usable:
            continue
        title = b.get("title", "?")
        ws = windows(b["text"], args.window, cap=args.per_work)
        depth, ident = [], []
        for w in ws:
            p = dirs.project(reader.read(w))
            depth.append(np.array([[p[c][L] for L in range(n_layers)]
                                   for c in concepts]).ravel())
            ident.append(fw(w))
        per_work[title] = {"author": b["author"], "kind": b["kind"],
                           "depth": np.array(depth), "ident": np.array(ident)}
        print(f"  read {title}: {len(ws)} windows", flush=True)

    def centroid_dist(a, b, key):
        ca, cb = per_work[a][key].mean(0), per_work[b][key].mean(0)
        # scale-free: cosine distance, so a measure with larger raw values does not dominate
        return float(1 - (ca @ cb) / (np.linalg.norm(ca) * np.linalg.norm(cb) + 1e-12))

    out = {"makers": {}}
    print(f"\n{'maker':<16}{'within-kind':>13}{'across-kind':>13}{'ratio':>8}   "
          f"{'ident within':>13}{'ident across':>13}{'ratio':>8}")
    print("-" * 88)
    for m in usable:
        works = [t for t, v in per_work.items() if v["author"] == m]
        wi_d, ac_d, wi_i, ac_i = [], [], [], []
        for i, a in enumerate(works):
            for b in works[i + 1:]:
                same = per_work[a]["kind"] == per_work[b]["kind"]
                (wi_d if same else ac_d).append(centroid_dist(a, b, "depth"))
                (wi_i if same else ac_i).append(centroid_dist(a, b, "ident"))
        if not ac_d:
            continue
        row = {"within_depth": float(np.mean(wi_d)) if wi_d else float("nan"),
               "across_depth": float(np.mean(ac_d)),
               "within_ident": float(np.mean(wi_i)) if wi_i else float("nan"),
               "across_ident": float(np.mean(ac_i)),
               "n_within": len(wi_d), "n_across": len(ac_d)}
        row["depth_ratio"] = row["across_depth"] / row["within_depth"] if wi_d else float("nan")
        row["ident_ratio"] = row["across_ident"] / row["within_ident"] if wi_i else float("nan")
        out["makers"][m] = row
        print(f"{m:<16}{row['within_depth']:>13.4f}{row['across_depth']:>13.4f}"
              f"{row['depth_ratio']:>8.2f}   {row['within_ident']:>13.4f}"
              f"{row['across_ident']:>13.4f}{row['ident_ratio']:>8.2f}")

    rows = [r for r in out["makers"].values() if r["n_within"] > 0]
    d_moves = sum(1 for r in rows if r["depth_ratio"] > 1.15)
    i_moves = sum(1 for r in rows if r["ident_ratio"] > 1.15)
    if not rows:
        verdict = "VOID"
    elif d_moves > len(rows) / 2 and i_moves <= len(rows) / 2:
        verdict = "RELATION"
    elif d_moves > len(rows) / 2:
        verdict = "GENRE"
    else:
        verdict = "ATTRIBUTE"
    print(f"\n  makers with a within-kind comparison available: {len(rows)}")
    print(f"  depth moves across kind in {d_moves}; identity moves in {i_moves}")
    print(f"\n  >>> {verdict}")
    if verdict == "GENRE":
        print("  Both measures move, so this cannot separate depth from genre. A void, not a result.")
    elif verdict == "VOID":
        print("  No maker has two works of the same kind, so there is no within-kind baseline.")

    out["verdict"] = verdict
    out["n_makers"] = len(rows)
    RESULTS.mkdir(parents=True, exist_ok=True)
    (RESULTS / "pilot.json").write_text(json.dumps(out, indent=2),
                                        encoding="utf-8", newline="\n")
    print(f"\nwrote {(RESULTS / 'pilot.json').relative_to(REPO)}")


if __name__ == "__main__":
    main()
