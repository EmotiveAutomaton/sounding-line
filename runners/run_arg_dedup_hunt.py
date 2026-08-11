"""G136 hunt — which extraction rule yields the paper's exact n = 3,238?

L72's diagnosis: our v3 extraction gives 3,323 sentential examples against the paper's 3,238,
the binary majority baseline matches to rounding while the fine majority accuracy runs 2.6
points high, so one of their dedup or filter rules is still unmodeled. This runner enumerates
candidate rules and reports, for each, the n, the fine majority-class share (their fine
majority accuracy is 0.29), and the binary majority share (theirs 0.58). A rule matching all
three at once is almost surely theirs; matching n alone is a candidate for a confirmation run.

Pure composition arithmetic, no models. Runtime is the xlsx parse plus milliseconds.
"""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "runners"))

import run_arg_replication as rar                                     # noqa: E402

OUT = REPO / "results" / "arg_baselines" / "dedup_hunt.json"
TARGET_N = 3238
TARGET_FINE_MAJ = 0.29
TARGET_BIN_MAJ = 0.58


def finish(events: list[dict]) -> list[dict]:
    evs = []
    for e in events:
        f = rar.FINE9.get(e["raw"])
        if f:
            e2 = dict(e)
            e2["fine"] = f
            e2["binary"] = "surface" if f in rar.SURFACE9 else "content"
            evs.append(e2)
    return evs


def first_only(events: list[dict], key_fn) -> list[dict]:
    seen: set = set()
    out = []
    for e in events:
        k = key_fn(e)
        if k in seen:
            continue
        seen.add(k)
        out.append(e)
    return out


def main() -> None:
    raw = rar.extract_raw()
    print(f"raw purpose events: {len(raw)}")

    k_pair = lambda e: (e["author"], e["cycle"], e["old"], e["new"])          # noqa: E731
    k_nocyc = lambda e: (e["author"], e["old"], e["new"])                     # noqa: E731
    k_global = lambda e: (e["old"], e["new"])                                 # noqa: E731
    k_old = lambda e: (e["author"], e["cycle"], e["old"])                     # noqa: E731
    k_new = lambda e: (e["author"], e["cycle"], e["new"])                     # noqa: E731

    def drop_noop(evs):
        return [e for e in evs if e["old"] != e["new"]]

    def drop_add(evs):
        return [e for e in evs if e["old"]]

    def drop_del(evs):
        return [e for e in evs if e["new"]]

    variants: dict[str, list[dict]] = {}
    fin = finish(raw)
    variants["A  split-all (v2)"] = fin
    variants["B  first-per-pair (v3)"] = first_only(fin, k_pair)
    variants["C  B + drop old==new"] = drop_noop(variants["B  first-per-pair (v3)"])
    variants["D  B + drop pure additions"] = drop_add(variants["B  first-per-pair (v3)"])
    variants["E  B + drop pure deletions"] = drop_del(variants["B  first-per-pair (v3)"])
    variants["F  B + aligned pairs only"] = drop_del(drop_add(variants["B  first-per-pair (v3)"]))
    variants["G  B + global (old,new) dedup"] = first_only(variants["B  first-per-pair (v3)"], k_global)
    variants["H  first-per-pair, cycle-blind"] = first_only(fin, k_nocyc)
    variants["I  first-per-old-sentence"] = first_only(fin, k_old)
    variants["J  first-per-new-sentence"] = first_only(fin, k_new)
    variants["K  C + drop pure additions"] = drop_add(variants["C  B + drop old==new"])
    variants["L  C + drop pure deletions"] = drop_del(variants["C  B + drop old==new"])
    variants["M  C + aligned pairs only"] = drop_del(drop_add(variants["C  B + drop old==new"]))
    variants["N  F, cycle-blind key"] = drop_del(drop_add(first_only(fin, k_nocyc)))

    rows = []
    hits = []
    for name, evs in variants.items():
        n = len(evs)
        if n == 0:
            continue
        fine_maj = Counter(e["fine"] for e in evs).most_common(1)[0][1] / n
        bin_maj = Counter(e["binary"] for e in evs).most_common(1)[0][1] / n
        row = {"rule": name, "n": n, "fine_majority_share": round(fine_maj, 4),
               "binary_majority_share": round(bin_maj, 4),
               "n_delta": n - TARGET_N}
        rows.append(row)
        mark = ""
        if n == TARGET_N:
            mark = "  <<< n EXACT"
            hits.append(name)
        elif abs(n - TARGET_N) <= 10:
            mark = "  <<< n within 10"
        print(f"{name:34s} n={n:5d} (d{n - TARGET_N:+5d})  fine-maj {fine_maj:.3f} "
              f"(vs {TARGET_FINE_MAJ})  bin-maj {bin_maj:.3f} (vs {TARGET_BIN_MAJ}){mark}")

    verdict = ("HIT: " + "; ".join(hits)) if hits else "NO-EXACT-HIT"
    print(f">>> {verdict}")
    OUT.write_text(json.dumps({"target_n": TARGET_N, "rows": rows, "verdict": verdict},
                              indent=1), encoding="utf-8", newline="\n")
    print(f"wrote {OUT.relative_to(REPO)}")


if __name__ == "__main__":
    main()
