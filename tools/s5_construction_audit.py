"""Stage-5 construction audit: rebuild every ROOT lineage's world from its id and count
distinct constructions per card and lane, cross-domain twins, and cross-lane twins (the
Stage-4 tool generalized to the Stage-5 builders and lanes). Collision twins of the source
worlds are deliberate and are counted apart.

Usage: ./.venv/Scripts/python.exe tools/s5_construction_audit.py [--json]   (S5_ROOT for a scratch root)
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from runners import s5_sources, s5_worlds                                          # noqa: E402
from runners.s4_worlds import construction_hash                                   # noqa: E402
from soundingline.stage5 import Lineages5                                         # noqa: E402

BUILDERS = {
    "J01": lambda lid, dom: (lambda w: {k: v for k, v in w.items() if k != "base"} | {"base": construction_hash(w["base"])})(s5_worlds.make_joint_world(lid, dom)),
    "A01": lambda lid, dom: s5_sources.make_source_world(lid, dom),
    "F01": lambda lid, dom: s5_worlds.make_foraging_set(lid),
}


def audit(L: Lineages5) -> dict:
    groups: dict = {}
    errors: dict = {}
    for lid, r in sorted(L.rows.items()):
        if r.get("parent") or r["card"] not in BUILDERS:
            continue
        key = f"{r['card']}|{r['split']}"
        g = groups.setdefault(key, {"card": r["card"], "split": r["split"], "units": 0, "by_hash": {}})
        g["units"] += 1
        try:
            h = construction_hash(BUILDERS[r["card"]](lid, r["domain"]))
        except Exception as e:                                                       # noqa: BLE001
            errors[lid] = repr(e)
            continue
        g["by_hash"].setdefault(h, []).append((r["domain"], lid))
    out: dict = {}
    for key, g in sorted(groups.items()):
        distinct = len(g["by_hash"])
        cross_dom = sum(1 for v in g["by_hash"].values() if len({d for d, _ in v}) > 1)
        out[key] = {"card": g["card"], "split": g["split"], "units": g["units"], "distinct": distinct,
                    "duplicate_units": g["units"] - distinct, "cross_domain_twin_groups": cross_dom}
    for key, g in groups.items():
        if g["split"] == "discovery":
            continue
        disc = groups.get(f"{g['card']}|discovery")
        if disc:
            out[key]["cross_lane_twins"] = sum(len(v) for h, v in g["by_hash"].items() if h in disc["by_hash"])
    dup_cards = sorted({v["card"] for v in out.values() if v["duplicate_units"] or v.get("cross_lane_twins")})
    total_units = sum(v["units"] for v in out.values())
    total_dups = sum(v["duplicate_units"] for v in out.values())
    total_cross = sum(v.get("cross_lane_twins", 0) for v in out.values())
    summary = (f"{total_units} root units over {len(out)} card-lanes; {total_dups} duplicate units; {total_cross} cross-lane twins; "
               + ("all distinct" if not dup_cards else f"DUPLICATES in {', '.join(dup_cards)}"))
    return {"groups": out, "errors": errors, "cards_with_duplicates": dup_cards, "ok": not dup_cards and not errors, "summary": summary}


def main() -> int:
    res = audit(Lineages5())
    if "--json" in sys.argv:
        print(json.dumps(res, indent=1))
    else:
        print(f"{'card':6} {'lane':13} {'units':>5} {'distinct':>8} {'dups':>5} {'xdom':>5} {'xlane':>6}")
        for v in res["groups"].values():
            print(f"{v['card']:6} {v['split']:13} {v['units']:5} {v['distinct']:8} {v['duplicate_units']:5} {v['cross_domain_twin_groups']:5} {v.get('cross_lane_twins', 0):6}")
        for lid, e in res["errors"].items():
            print(f"ERROR {lid}: {e}")
        print(res["summary"])
    return 0 if res["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
