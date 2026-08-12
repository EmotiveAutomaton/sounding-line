"""G80 — reserve versus overpaint, first pass: abandoned scaffolding, computable on one text.

The imported cue (READER_HEURISTICS §7): planned room versus insertion, and its cheapest
observable is scaffolding that stops. Three counters per document:

    promised counts   "three reasons/points/ways..." followed by fewer enumerators than promised
    orphan ordinals   "first(ly)" with no second/next/then/finally afterward
    dangling forwards "as we will see / below / later in this essay" with <20% of the doc left

Corpora: human drafts (argrewrite Draft1, unedited student work, expected highest), books
(published and edited, expected lowest), machine long-form (ladder3). Exploratory first pass:
no directional gate between human and machine is pre-registered; the human-draft > books
ordering is the sanity expectation, since editing is what removes abandoned scaffolding.

Ruler gate (LESSONS §3): a planted document with exactly two known abandonments and a clean
document must score 2 and 0 before any corpus is read.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "results" / "g80_scaffolding"

NUM = {"two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7}
PROMISE = re.compile(r"\b(two|three|four|five|six|seven|\d)\s+"
                     r"(reasons|points|ways|steps|arguments|factors|parts|things|aspects)\b",
                     re.I)
ENUM = re.compile(r"\b(first(ly)?|second(ly)?|third(ly)?|fourth|fifth|finally|lastly)\b|"
                  r"^\s*\d+[.)]\s", re.I | re.M)
ORD_FIRST = re.compile(r"\bfirst(ly)?\b", re.I)
ORD_LATER = re.compile(r"\b(second(ly)?|next|then|finally|lastly|third(ly)?)\b", re.I)
FORWARD = re.compile(r"\b(as we (will|shall) see|discussed below|later in this "
                     r"(essay|paper|piece)|more on (this|that) (below|later)|"
                     r"we will (return|come back) to)\b", re.I)


def count_abandoned(text: str) -> dict:
    n = 0
    details = []
    for m in PROMISE.finditer(text):
        promised = NUM.get(m.group(1).lower()) or (int(m.group(1)) if m.group(1).isdigit()
                                                   else 0)
        if not 2 <= promised <= 7:
            continue
        after = text[m.end(): m.end() + 4000]
        found = len(ENUM.findall(after))
        if found < promised - 1:
            n += 1
            details.append(f"promised {promised} {m.group(2)}, enumerated ~{found}")
    for m in ORD_FIRST.finditer(text):
        if not ORD_LATER.search(text[m.end(): m.end() + 3000]):
            n += 1
            details.append("orphan 'first'")
            break                                                     # one per doc
    for m in FORWARD.finditer(text):
        if m.start() > 0.8 * len(text):
            n += 1
            details.append("dangling forward reference in final fifth")
    return {"n": n, "details": details}


def main() -> None:
    import numpy as np                                                # noqa: PLC0415
    from scipy import stats                                           # noqa: PLC0415

    # ── ruler gate
    planted = ("There are three reasons this matters. First, the cost. I never got to the "
               "others because the meeting ran long. As we will see below, more followed. " +
               "filler " * 300)
    clean = ("There are two reasons. First, the cost. Second, the risk. That is the whole "
             "of it. " + "filler " * 300)
    g1, g0 = count_abandoned(planted)["n"], count_abandoned(clean)["n"]
    if g1 < 2 or g0 != 0:
        print(f">>> VOID: ruler gate failed (planted {g1}, clean {g0})")
        sys.exit(1)
    print(f"gate ok: planted {g1}, clean {g0}")

    corpora = {
        "human_drafts": sorted((REPO / "corpora" / "public" / "argrewrite" / "essays"
                                / "Draft1").glob("*.txt")),
        "books": None,
        "machine": sorted((REPO / "corpora" / "ladder3").glob("*.txt")),
    }
    texts: dict[str, list[str]] = {}
    texts["human_drafts"] = [p.read_text(encoding="utf-8", errors="replace")
                             for p in corpora["human_drafts"]]
    sys.path.insert(0, str(REPO / "runners"))
    from run_g28_twolayers import load_texts                          # noqa: PLC0415
    texts["books"] = [t["text"] for t in load_texts()]
    texts["machine"] = [p.read_text(encoding="utf-8", errors="replace")
                        for p in corpora["machine"]]

    out = {"gate": {"planted": g1, "clean": g0}, "corpora": {}}
    rates = {}
    for name, ts in texts.items():
        counts = [count_abandoned(t)["n"] for t in ts if len(t.split()) > 100]
        r = float(np.mean(counts)) if counts else 0.0
        rates[name] = counts
        out["corpora"][name] = {"n_docs": len(counts), "mean_abandoned": round(r, 3),
                                "share_with_any": round(float(np.mean(
                                    [c > 0 for c in counts])), 3)}
        print(f"{name:14s} n={len(counts):4d} mean {r:.3f} "
              f"any {out['corpora'][name]['share_with_any']:.2f}")

    u_hb = stats.mannwhitneyu(rates["human_drafts"], rates["books"],
                              alternative="two-sided")
    u_hm = stats.mannwhitneyu(rates["human_drafts"], rates["machine"],
                              alternative="two-sided")
    out["human_vs_books_p"] = float(u_hb.pvalue)
    out["human_vs_machine_p"] = float(u_hm.pvalue)
    out["verdict"] = "INSTRUMENT-FIRST-PASS"
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "summary.json").write_text(json.dumps(out, indent=1), encoding="utf-8",
                                      newline="\n")
    print(f"human-vs-books p {u_hb.pvalue:.3g} | human-vs-machine p {u_hm.pvalue:.3g}")
    print(f"wrote {(OUT / 'summary.json').relative_to(REPO)}")


if __name__ == "__main__":
    main()
