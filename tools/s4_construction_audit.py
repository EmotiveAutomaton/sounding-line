"""Stage-4 construction audit: rebuild every ROOT lineage's world from its id and count
distinct constructions per card and split, cross-domain twins, and cross-split twins.

Built 2026-08-28 after the concurrency audit found the T-track constructor ignoring its
domain argument (128 nominal T01 units, 54 distinct constructions; the 256 confirmation
units saturating the same 64-world space, every one a textual twin of a discovery
world). The scheduler's validate step writes this into COVERAGE.json and the run logs
its summary at start, so the packet reads "checked" with numbers instead of inferring
"no duplicates" from a control that never looked.

Usage: ./.venv/Scripts/python.exe tools/s4_construction_audit.py [--json]
       (S4_ROOT selects a scratch root, as for the scheduler). Exit 1 on any duplicate.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from runners import s4_worlds                                                     # noqa: E402
from soundingline.s4 import Lineages                                              # noqa: E402

# cards whose units are worlds built from the ROOT lineage id; derived lineages (A02/A03 on
# A01's worlds, T02/T03 on T01's) share the parent's construction and are not re-counted
BUILDERS = {
    "C01": lambda lid, dom: s4_worlds.make_world(lid, dom),
    "C02": lambda lid, dom: s4_worlds.make_world(lid, dom),
    "C03": lambda lid, dom: s4_worlds.make_world(lid, dom),
    "A01": lambda lid, dom: s4_worlds.make_appraisal_world(lid, dom),
    "T01": lambda lid, dom: s4_worlds.make_lesson_world(lid, dom),
    "H01": lambda lid, dom: s4_worlds.make_chain_world(lid, dom),
    "H02": lambda lid, dom: s4_worlds.make_history_world(lid, dom, "stable"),
}


def audit(L: Lineages) -> dict:
    groups: dict = {}
    errors: dict = {}
    for lid, r in sorted(L.rows.items()):
        if r.get("parent") or r["card"] not in BUILDERS:
            continue
        key = f"{r['card']}|{r['split']}"
        g = groups.setdefault(key, {"card": r["card"], "split": r["split"], "units": 0,
                                    "by_hash": {}})
        g["units"] += 1
        try:
            h = s4_worlds.construction_hash(BUILDERS[r["card"]](lid, r["domain"]))
        except Exception as e:                                                       # noqa: BLE001
            errors[lid] = repr(e)
            continue
        g["by_hash"].setdefault(h, []).append((r["domain"], lid))
    out: dict = {}
    for key, g in sorted(groups.items()):
        distinct = len(g["by_hash"])
        cross_dom = sum(1 for v in g["by_hash"].values() if len({d for d, _ in v}) > 1)
        out[key] = {"card": g["card"], "split": g["split"], "units": g["units"],
                    "distinct": distinct, "duplicate_units": g["units"] - distinct,
                    "cross_domain_twin_groups": cross_dom}
    # cross-split twins: a confirmation construction identical to a discovery one of the
    # same card is not fresh, whatever its lineage flags say
    for key, g in groups.items():
        if g["split"] != "confirmation":
            continue
        disc = groups.get(f"{g['card']}|discovery")
        if not disc:
            continue
        twins = sum(len(v) for h, v in g["by_hash"].items() if h in disc["by_hash"])
        out[key]["cross_split_twins"] = twins
    dup_cards = sorted({v["card"] for v in out.values()
                        if v["duplicate_units"] or v.get("cross_split_twins")})
    total_units = sum(v["units"] for v in out.values())
    total_dups = sum(v["duplicate_units"] for v in out.values())
    total_cross = sum(v.get("cross_split_twins", 0) for v in out.values())
    summary = (f"{total_units} root units over {len(out)} card-splits; "
               f"{total_dups} duplicate units; {total_cross} cross-split twins; "
               + ("all distinct" if not dup_cards else f"DUPLICATES in {', '.join(dup_cards)}"))
    return {"groups": out, "errors": errors, "cards_with_duplicates": dup_cards,
            "ok": not dup_cards and not errors, "summary": summary}


def main() -> int:
    res = audit(Lineages())
    if "--json" in sys.argv:
        print(json.dumps(res, indent=1))
    else:
        print(f"{'card':6} {'split':13} {'units':>5} {'distinct':>8} {'dups':>5} {'xdom':>5} {'xsplit':>6}")
        for v in res["groups"].values():
            print(f"{v['card']:6} {v['split']:13} {v['units']:5} {v['distinct']:8} "
                  f"{v['duplicate_units']:5} {v['cross_domain_twin_groups']:5} "
                  f"{v.get('cross_split_twins', 0):6}")
        for lid, e in res["errors"].items():
            print(f"ERROR {lid}: {e}")
        print(res["summary"])
    return 0 if res["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
