"""Cross-contract comparison (2026-08-29): the first Stage-5 contract (design 1, one reader,
results/phase_2_4_stage_5) against the second (design 2, both readers, every post-run
repair, results/phase_2_4_stage_5r), card by card: outcome, point, interval, readers, and
the repair cells. Analysis only; writes results/phase_2_4_stage_5r/post/CROSS_CONTRACT.json
and prints the table. Queued behind the second contract (needs its packet).

DESIGN CHECK (2026-08-29)
lessons read: LESSONS §3 (a comparison across contracts is descriptive; the bands belong to
  each contract's cards), §5 (produces guard).
gates: none; the two contracts' verdicts are read as written. under the null (the repairs
  changed nothing) the outcomes agree card by card; under the alternative they differ, and
  the table names where. The direction guarded is a reader treating a design-2 support as a
  replication of a design-1 one when the construction changed. bands: none here; each
  contract's card bands are exhaustive and stated in its runners.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
ROOTS = {"design1": REPO / "results" / "phase_2_4_stage_5", "design2": REPO / "results" / "phase_2_4_stage_5r"}


def verdicts(root: Path) -> dict:
    out = {}
    if not root.exists():
        return out
    for vp in sorted(root.glob("*/verdict.json")) + sorted(root.glob("*/v*/verdict.json")):
        try:
            v = json.loads(vp.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        cell = vp.parent.relative_to(root).as_posix()
        out[cell] = {"outcome": v.get("outcome"), "point": v.get("point"), "ci": v.get("ci"), "n": v.get("n_units"),
                     "readers": v.get("readers"), "reason": (v.get("reason") or "")[:80], "track_gate_note": v.get("track_gate_note")}
    return out


def main() -> int:
    a, b = verdicts(ROOTS["design1"]), verdicts(ROOTS["design2"])
    cards = sorted(set(k.split("/")[0] for k in a) | set(k.split("/")[0] for k in b))
    rows = []
    for c in cards:
        va = a.get(f"{c}/v2") or a.get(c) or {}
        vb = b.get(c) or {}
        rows.append({"card": c, "design1": va, "design2": vb,
                     "changed": (va.get("outcome") != vb.get("outcome")) if (va and vb) else None})
    out = {"roots": {k: str(v) for k, v in ROOTS.items()}, "rows": rows,
           "summary": {"cards": len(cards), "outcome_changed": sum(1 for r in rows if r["changed"]),
                       "design2_readers": sorted({tuple(v.get("readers") or []) for v in b.values()}, key=str)}}
    dest = ROOTS["design2"] / "post" / "CROSS_CONTRACT.json"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(out, indent=1), encoding="utf-8")
    print(f"{'card':7} {'design 1':28} {'design 2':28} changed")
    for r in rows:
        d1 = f"{(r['design1'] or {}).get('outcome') or '-'} {(r['design1'] or {}).get('point') if (r['design1'] or {}).get('point') is not None else ''}"
        d2 = f"{(r['design2'] or {}).get('outcome') or '-'} {(r['design2'] or {}).get('point') if (r['design2'] or {}).get('point') is not None else ''}"
        print(f"{r['card']:7} {d1[:28]:28} {d2[:28]:28} {r['changed']}")
    print("wrote", dest)
    return 0


if __name__ == "__main__":
    sys.exit(main())
