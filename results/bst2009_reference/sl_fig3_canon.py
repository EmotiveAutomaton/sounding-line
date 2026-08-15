"""Resolve Fig-3 stimulus identity across panels -> the paper's 99 unique stimuli.

The decode chains all 36 panels label-perfectly but unique (world, prefix) stimuli count 108
against the paper's 99. Diagnosis: two-digit judgment numbers (labels 10-13) straddle two grid
cells, so the same drawn stimulus snaps to different cells in different panels; single-digit
disputes are genuine route differences.

Identity is decided on the GLYPH, not the snapped cell: the decode now persists each judgment
number's raw panel-local coordinates (jp_raw). Two same-world, same-length prefixes are the
same stimulus iff every position where their cells differ is a judgment index in both panels
AND that judgment's raw coordinates agree within tolerance (repeat-draws of one stimulus land
sub-point; different placements sit a cell pitch apart, 4.6/5.5 pt). Merged classes take the
member sequence that is strictly 8-adjacent as canonical geometry where one exists.

Writes fig3_stimuli_canon.json (stimulus list with members and canonical paths) and prints
the class count against the 99 gate, plus the raw-delta separation so the tolerance is seen
to be safe rather than assumed.
"""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).parent
TOL = 2.0        # pt; same-stimulus repeat-draw jitter vs the 4.6/5.5 pt cell pitch

data = json.loads((HERE / "fig3_stimuli.json").read_text(encoding="utf-8"))
panels = data["panels"]


def world_key(pl):
    return (tuple(sorted((k, tuple(v)) for k, v in pl["goals"].items())),
            tuple(map(tuple, pl["wall_cells"])), tuple(pl["start"]))


def strictly_legal(path):
    return all(max(abs(path[i][0] - path[i + 1][0]),
                   abs(path[i][1] - path[i + 1][1])) == 1
               for i in range(len(path) - 1))


# every (panel, judgment label) is one stimulus instance
instances = []
for pl in panels:
    path = [tuple(c) for c in pl["path"]]
    raw = {int(k): tuple(v) for k, v in pl["jp_raw"].items()}
    for lab, step in sorted((int(l_), s) for l_, s in pl["judgment_steps"].items()):
        instances.append({"world": world_key(pl), "len": step + 1, "label": lab,
                          "prefix": tuple(path[:step + 1]), "panel": (pl["row"], pl["col"]),
                          "raw": raw})

# union-find over instances
parent = list(range(len(instances)))


def find(i):
    while parent[i] != i:
        parent[i] = parent[parent[i]]
        i = parent[i]
    return i


def union(i, j):
    parent[find(i)] = find(j)


by_wl = defaultdict(list)
for idx, ins in enumerate(instances):
    by_wl[(ins["world"], ins["len"])].append(idx)

merged_pair_max, kept_pair_max = [], []
for (wk, L), idxs in by_wl.items():
    for a_i in range(len(idxs)):
        for b_i in range(a_i + 1, len(idxs)):
            A, B = instances[idxs[a_i]], instances[idxs[b_i]]
            if A["prefix"] == B["prefix"]:
                union(idxs[a_i], idxs[b_i])
                continue
            diffs = [k for k in range(L) if A["prefix"][k] != B["prefix"][k]]
            # a differing position must be a judgment cell in both panels (label = index+1,
            # the label-perfect invariant) with raw coordinates present on both sides
            ok, deltas = True, []
            for k in diffs:
                lab = k + 1
                ra, rb = A["raw"].get(lab), B["raw"].get(lab)
                if ra is None or rb is None:
                    ok = False
                    break
                deltas.append(max(abs(ra[0] - rb[0]), abs(ra[-1] - rb[-1])))
            if not ok:
                continue
            if all(d <= TOL for d in deltas):
                union(idxs[a_i], idxs[b_i])
                merged_pair_max.append(max(deltas))
            else:
                kept_pair_max.append(max(deltas))

classes = defaultdict(list)
for idx in range(len(instances)):
    classes[find(idx)].append(idx)

print(f"instances: {len(instances)}; unique stimuli: {len(classes)} (gate 99)")
if merged_pair_max and kept_pair_max:
    print(f"separation: merged pairs' max raw delta {max(merged_pair_max):.2f} pt "
          f"(n={len(merged_pair_max)}) vs kept pairs' smallest max delta "
          f"{min(kept_pair_max):.2f} pt (n={len(kept_pair_max)})")

# ── canonical geometry per class, then LEGALIZATION ─────────────────────────────────────────
# A judgment glyph's snapped cell can sit one column off: two-digit numbers straddle two
# columns outright, and single digits jitter across a boundary (seen as a one-gap straight
# run with the judgment adjacent to the gap). The label-perfect invariant proves no cell is
# missing (consecutive labels sit at consecutive indices), so the repair space is exactly:
# every judgment cell may slide one column, dashes are fixed. Among strictly-8-adjacent
# assignments the winner moves fewest cells, ties ranked by agreement with the glyph's own
# raw x-span; a unique winner is demanded and anything else is reported.
XPITCH = 4.60

def legalize(path, jp_pos_raw):
    """jp_pos_raw: {index: (x0, x1)} for judgment cells; x may slide one column."""
    from itertools import product
    options = []
    for i, c in enumerate(path):
        if i in jp_pos_raw:
            options.append([(c[0] + dx, c[1]) for dx in (-1, 0, 1)])
        else:
            options.append([c])
    sols = []
    for combo in product(*options):
        if strictly_legal(combo):
            sols.append(combo)
            if len(sols) > 32:
                break
    if not sols:
        return None, "none"

    def rawcost(s):
        tot = 0.0
        for i, (x0, x1) in jp_pos_raw.items():
            tot += abs((s[i][0] - 16) * XPITCH - (x0 + x1) / 2)
        return round(tot, 3)

    sols.sort(key=lambda s: (sum(a != b for a, b in zip(s, path)), rawcost(s)))
    key0 = (sum(a != b for a, b in zip(sols[0], path)), rawcost(sols[0]))
    best = [s for s in sols
            if (sum(a != b for a, b in zip(s, path)), rawcost(s)) == key0]
    return sols[0], ("unique" if len(best) == 1 else f"ambiguous({len(best)})")

stimuli = []
tally = defaultdict(int)
for root, idxs in sorted(classes.items(), key=lambda kv: (instances[kv[1][0]]["len"],)):
    members = [instances[i] for i in idxs]
    variants = {m["prefix"] for m in members}
    legal = [v for v in variants if strictly_legal(v)]
    if legal:
        canon, status, moved = legal[0], "member-legal", 0
    else:
        base = sorted(variants)[0]
        jp_pos_raw = {}
        for k in range(len(base)):
            for m in members:
                r = m["raw"].get(k + 1)
                if r is not None:
                    jp_pos_raw[k] = (r[0], r[1]) if len(r) > 2 else (r[0], r[0] + 2.2)
                    break
        fixed, status = legalize(list(base), jp_pos_raw)
        canon = fixed if fixed else base
        moved = sum(a != b for a, b in zip(canon, base)) if fixed else 0
    tally[status] += 1
    stimuli.append({
        "world": json.loads(json.dumps(members[0]["world"], default=list)),
        "length": members[0]["len"], "label": members[0]["label"],
        "path": [list(c) for c in canon],
        "legalization": status, "cells_moved": moved,
        "n_variants": len(variants),
        "members": [{"panel": list(m["panel"]), "label": m["label"]} for m in members]})

print(f"canonical stimuli: {len(stimuli)}; legalization tally: {dict(tally)}")
still_bad = [s for s in stimuli
             if not strictly_legal([tuple(c) for c in s["path"]])]
print(f"paths still not strictly 8-adjacent after repair: {len(still_bad)}")
dest = HERE / "fig3_stimuli_canon.json"
dest.write_text(json.dumps({"grid": data["grid"], "unique_stimuli": len(stimuli),
                            "tol_pt": TOL, "stimuli": stimuli}, indent=1),
                encoding="utf-8", newline="\n")
print(f"wrote {dest.name}")
