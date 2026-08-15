"""Decode Fig 3 of BST 2009 (page 8): all 36 conditions as grid-world stimuli.

The panels draw each stimulus as TEXT: 'x' at the start cell, '-' glyphs at visited cells,
digits at numbered judgment points, capital letters at goals. Walls are filled rects. The grid
is 17 wide x 9 high (paper text), 8-connected movement.

Pass 1 (--dump): char-level spans + wall rects, clustered into the 9x4 panel lattice, with
per-panel local coordinates, so the cell pitch and origin can be calibrated.
Pass 2 (default): full decode -> fig3_stimuli.json with, per panel: goals, wall cells, start,
path cells in order, judgment-point step numbers.
"""

from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

import pymupdf

PDF = sys.argv[1]
PAGE = int(sys.argv[2]) if len(sys.argv) > 2 else 8
DUMP = "--dump" in sys.argv

doc = pymupdf.open(PDF)
p = doc[PAGE - 1]

# ── collect atoms ────────────────────────────────────────────────────────────────────────────
raw = p.get_text("rawdict")
chars = []
for li, (b, line) in enumerate((b, line) for b in raw["blocks"]
                               for line in b.get("lines", [])):
    for s in line["spans"]:
        for c in s["chars"]:
            x0, y0, x1, y1 = c["bbox"]
            chars.append({"c": c["c"], "x": (x0 + x1) / 2, "y": (y0 + y1) / 2,
                          "x0": x0, "x1": x1, "line": li,
                          "size": round(s["size"], 1)})
# figure area only (the big frame found by the probe: x 41-507, y 55-614). Space characters
# are KEPT: they are the only reliable delimiter between adjacent-cell numbers ("10 11")
# and the digits of one number ("15"), whose x-gap distributions overlap (4.48 vs 4.6+ pt
# under the figure's varying character advance).
chars = [c for c in chars if 41 <= c["x"] <= 508 and 54 <= c["y"] <= 615
         and (c["c"].strip() or c["c"] == " ")]

walls = []
for d in p.get_drawings():
    if not d["items"] or not all(it[0] == "re" for it in d["items"]):
        continue
    r = d["rect"]
    if r.width > 30 and r.height > 15:
        continue
    if d.get("fill") and sum(d["fill"]) < 0.5 and 54 <= r.y0 <= 615:
        walls.append((r.x0, r.y0, r.x1, r.y1))

# ── panel lattice: 4 columns x 9 rows, inferred from wall x-clusters and y-clusters ─────────
wall_xs = sorted({round((w[0] + w[2]) / 2, 1) for w in walls})
col_x = []
for x in wall_xs:
    if not col_x or x - col_x[-1] > 40:
        col_x.append(x)
row_ys = sorted({round(w[1], 1) for w in walls} | {round(w[3], 1) for w in walls})
print(f"chars in figure: {len(chars)}; wall rects: {len(walls)}; "
      f"wall x-centers (cols): {col_x}")

# panel columns: wall sits mid-panel; panel width from column spacing
dx = col_x[1] - col_x[0]
col_left = [x - dx / 2 for x in col_x]
# panel rows: cluster ALL glyph ys into 9 bands
ys = sorted(c["y"] for c in chars)
bands = []
for y in ys:
    if not bands or y - bands[-1][-1] > 12:
        bands.append([y])
    else:
        bands[-1].append(y)
print(f"y-bands found: {len(bands)}; extents: "
      f"{[(round(b[0]), round(b[-1])) for b in bands]}")

if DUMP:
    # dump panel (row 0, col 0) in local coords for calibration
    b0 = bands[0]
    y0, y1 = b0[0] - 6, b0[-1] + 6
    x0, x1 = col_left[0], col_left[0] + dx
    sel = sorted((c for c in chars if x0 <= c["x"] <= x1 and y0 <= c["y"] <= y1),
                 key=lambda c: (c["y"], c["x"]))
    print(f"\npanel(0,0) chars, window x[{x0:.1f},{x1:.1f}] y[{y0:.1f},{y1:.1f}]:")
    for c in sel:
        print(f"  {c['c']!r:6} x={c['x']:7.2f} y={c['y']:7.2f}")
    pw = [w for w in walls if x0 <= (w[0] + w[2]) / 2 <= x1 and y0 - 5 <= w[1] <= y1 + 5]
    print("panel walls:", [[round(v, 1) for v in w] for w in pw])
    sys.exit(0)

# ── full decode ──────────────────────────────────────────────────────────────────────────────
# Lattice, calibrated from anchors verified in the dump: within a panel, A sits at cell (16,0),
# B at (16,8), the wall at column 8, the start 'x' at (0,8). Row origins are EMPIRICAL: the
# figure inserts extra spacing between its three path groups, so each panel row's y comes from
# its own 'A' goal glyph in panel column 0 rather than a fixed pitch.
XPITCH = 4.60
YPITCH = 5.50
X16 = 181.88                        # x of the A/B column (cell 16) in panel column 0
GRID_W, GRID_H = 17, 9

a_ys = sorted(c["y"] for c in chars
              if c["c"] == "A" and abs(c["x"] - X16) < 3)
row_origins = []
for y in a_ys:
    if not row_origins or y - row_origins[-1] > 20:
        row_origins.append(y)
print(f"empirical panel-row origins from 'A' anchors: "
      f"{[round(y, 1) for y in row_origins]} ({len(row_origins)} rows)")

panels = []
for ri, py0 in enumerate(row_origins):
    for ci in range(len(col_left)):
        xoff = col_left[ci] - col_left[0]

        def cell(x, y):
            c = round((x - (X16 + xoff)) / XPITCH) + 16
            r = round((y - py0) / YPITCH)
            return c, r

        sel = [c for c in chars
               if col_left[ci] <= c["x"] <= col_left[ci] + dx
               and py0 - YPITCH * 0.6 <= c["y"] <= py0 + 8 * YPITCH + YPITCH * 0.6]
        pw = [w for w in walls
              if col_left[ci] <= (w[0] + w[2]) / 2 <= col_left[ci] + dx
              and py0 - 4 <= w[1] <= py0 + 8 * YPITCH + 6]

        # ── line-aware column assignment. The stimulus rows are monospace text strings whose
        # glyph-pair advance (~4.98pt) exceeds the wall/goal-calibrated grid pitch (4.60pt),
        # so per-glyph lattice snapping accumulates ~0.38pt of drift per cell and rounds the
        # tail of a long run one column right (caught 2026-08-14: '7' at fractional column
        # 6.53, '10' at 9.8 in a run whose truth is 6 and 9). Within a line, RELATIVE columns
        # are exact by construction: consecutive glyph groups advance by whole slots, so
        # cumulative rounding of consecutive gaps carries no drift. The anchor is the line's
        # first group, where the string starts and the lattice snap is still clean.
        goals, path_atoms = {}, []
        jp_raw = {}
        by_line = defaultdict(list)
        for c in sel:
            by_line[c["line"]].append(c)
        # pass 1: per line, glyph groups + drift-free relative columns + anchor confidence.
        # Digit runs merge into one number below one slot (~4.98pt): intra-number gaps run
        # 3.58-4.5pt (the '15' split at 4.1 taught the old 4.0 threshold), two separate
        # numbers in adjacent cells sit a full slot apart.
        lines = []
        clusters = []
        for li, lchars in by_line.items():
            # a rawdict line can carry spans from different grid rows (a goal letter beside
            # a judgment number); sorting such a line by x interleaves them and splits the
            # number. Cluster by y first, each cluster its own run.
            lchars.sort(key=lambda c: c["y"])
            cur = [lchars[0]]
            for c in lchars[1:]:
                if c["y"] - cur[-1]["y"] > 2.5:
                    clusters.append(cur)
                    cur = [c]
                else:
                    cur.append(c)
            clusters.append(cur)
        for lchars in clusters:
            lchars.sort(key=lambda c: c["x"])
            gs, space_break = [], True
            for c in lchars:
                if c["c"] == " ":
                    space_break = True
                    continue
                if (c["c"].isdigit() and gs and gs[-1]["text"].isdigit()
                        and not space_break and c["x"] - gs[-1]["xlast"] < 6.0):
                    gs[-1]["text"] += c["c"]
                    gs[-1]["xlast"] = c["x"]
                    gs[-1]["x1"] = c["x1"]
                    gs[-1]["chars"].append(c)
                else:
                    gs.append({"text": c["c"], "x": c["x"], "xlast": c["x"],
                               "x0": c["x0"], "x1": c["x1"], "y": c["y"],
                               "chars": [c]})
                space_break = False
            # an unbroken digit run longer than two is adjacent-cell two-digit numbers
            # packed without a delimiter ("1011" = 10 then 11); chunk in pairs. An odd run
            # takes the split whose values are all plausible labels (<= 16), leading single
            # first if both work.
            split = []
            for g in gs:
                t = g["text"]
                if t.isdigit() and len(t) >= 3:
                    chs = g["chars"]
                    if len(t) % 2 == 0:
                        chunks = [chs[i:i + 2] for i in range(0, len(chs), 2)]
                    else:
                        a = [chs[:1]] + [chs[i:i + 2] for i in range(1, len(chs), 2)]
                        b = [chs[i:i + 2] for i in range(0, len(chs) - 1, 2)] + [chs[-1:]]
                        va = [int("".join(c["c"] for c in ch)) for ch in a]
                        vb = [int("".join(c["c"] for c in ch)) for ch in b]
                        chunks = a if all(v <= 16 for v in va) else b
                        if all(v <= 16 for v in va) and all(v <= 16 for v in vb):
                            print(f"  WARNING odd digit run {t!r}: both splits plausible, "
                                  f"took {va}")
                    for ci_, ch in enumerate(chunks):
                        split.append({"text": "".join(c["c"] for c in ch),
                                      "x": (ch[0]["x"] + ch[-1]["x"]) / 2,
                                      "xlast": ch[-1]["x"], "x0": ch[0]["x0"],
                                      "x1": ch[-1]["x1"], "y": ch[0]["y"], "chars": ch,
                                      "run_prev": ci_ > 0})
                else:
                    split.append(g)
            gs = split
            for g in gs:
                if g["text"].isdigit() and len(g["text"]) > 1:
                    g["x"] = (g["x0"] + g["x1"]) / 2
            gaps = [gs[i + 1]["x"] - gs[i]["x"] for i in range(len(gs) - 1)]
            slot_gaps = sorted(g_ for g_ in gaps if 3.5 <= g_ <= 6.5)
            slot = slot_gaps[len(slot_gaps) // 2] if slot_gaps else 4.98
            rel, rels = 0, [0]
            for i in range(1, len(gs)):
                # chunks of one packed digit run are adjacent cells BY CONSTRUCTION; their
                # centers sit ~1.5 slots apart (wide digit advance) and gap-rounding would
                # skip a cell
                if gs[i].get("run_prev"):
                    rel += 1
                else:
                    rel += max(1, round((gs[i]["x"] - gs[i - 1]["x"]) / slot))
                rels.append(rel)
            # anchor on the FIRST CHAR of the first group: a two-digit number spans ~1.5
            # cells, so its group center sits half a cell right of the cell it occupies
            ax = gs[0]["chars"][0]
            anchor_x = (ax["x0"] + ax["x1"]) / 2 if len(gs[0]["chars"]) > 1 else gs[0]["x"]
            latcol0 = (anchor_x - (X16 + xoff)) / XPITCH + 16
            frac = abs(latcol0 - round(latcol0))
            rows = [cell(g["x"], g["y"])[1] for g in gs]
            lines.append({"gs": gs, "rels": rels, "rows": rows,
                          "latcol0": latcol0, "frac": frac})
        # pass 2: anchor selection by CHAIN VALIDITY. A line whose first glyph sits near a
        # column boundary can round one column off; for those lines every shift in
        # {-1, 0, +1} is tried and the winning combination is the one whose atoms form the
        # best single chain (most atoms chained, then lowest label cost, then fewest
        # non-strict steps, then least total shift). The walk's own connectivity is the
        # constraint; local adjacency voting proved fragile (it broke two panels).
        ambiguous = [ln for ln in lines if 0.35 <= ln["frac"] <= 0.65]
        ambiguous = sorted(ambiguous, key=lambda l_: -l_["frac"])[:3]

        def build_atoms(shift_map):
            g_, pa_, raw_ = {}, [], {}
            for ln in lines:
                c0 = round(ln["latcol0"]) + shift_map.get(id(ln), 0)
                for g, rel_, row in zip(ln["gs"], ln["rels"], ln["rows"]):
                    col, t = c0 + rel_, g["text"]
                    if t in "ABC":
                        g_[t] = (col, row)
                    elif t == "x":
                        pa_.append(("start", col, row, g["x"]))
                    elif t == "-":
                        pa_.append(("step", col, row, g["x"]))
                    elif t.isdigit():
                        pa_.append((f"jp{int(t)}", col, row, g["x0"]))
                        # raw local coordinates (panel-relative) so a downstream pass can
                        # tell decode jitter from a genuinely different judgment placement
                        raw_[int(t)] = [round(g["x0"] - (X16 + xoff), 2),
                                        round(g["x1"] - (X16 + xoff), 2),
                                        round(g["y"] - py0, 2)]
            return g_, pa_, raw_

        wall_cells = set()
        for w in pw:
            wc = round(((w[0] + w[2]) / 2 - (X16 + xoff)) / XPITCH) + 16
            r0 = round((w[1] - py0) / YPITCH + 0.5)
            r1 = round((w[3] - py0) / YPITCH - 0.5)
            for r in range(max(0, r0), min(GRID_H - 1, r1) + 1):
                wall_cells.add((wc, r))

        # chain the path from the start over the atom cells: exhaustive DFS for a Hamiltonian
        # path (greedy misordered wherever the path doubled back — the L108 defect). Dash
        # atoms must be strictly 8-adjacent; number atoms tolerate one extra column of slack
        # because multi-digit glyph groups straddle cells.
        def chain_atoms(atom_cells, start):
            def adjacent(a, b):
                dx, dy = abs(a[0] - b[0]), abs(a[1] - b[1])
                loose = any(k.startswith("jp") for k in atom_cells[a] + atom_cells[b])
                return (dx <= (2 if loose else 1)) and dy <= 1 and (dx or dy)

            nodes = list(atom_cells)

            def label_cost(acc):
                # the paper's own step numbers are the ground truth for ordering: a correct
                # chain places judgment label k at index k-1
                cost = 0
                for i, cellc in enumerate(acc):
                    for k in atom_cells.get(cellc, []):
                        if k.startswith("jp"):
                            cost += abs(i - (int(k[2:]) - 1))
                return cost

            hold = {"best": [], "cost": 10 ** 9}

            def dfs(cur, seen, acc):
                if len(acc) == len(nodes):
                    c = label_cost(acc)
                    if (len(acc), -c) > (len(hold["best"]), -hold["cost"]):
                        hold["best"], hold["cost"] = list(acc), c
                    return
                progressed = False
                for n in nodes:
                    if n not in seen and adjacent(cur, n):
                        progressed = True
                        seen.add(n)
                        acc.append(n)
                        dfs(n, seen, acc)
                        acc.pop()
                        seen.remove(n)
                if not progressed:
                    c = label_cost(acc)
                    if (len(acc), -c) > (len(hold["best"]), -hold["cost"]):
                        hold["best"], hold["cost"] = list(acc), c

            dfs(start, {start}, [start])
            nonstrict = sum(1 for i in range(len(hold["best"]) - 1)
                            if max(abs(hold["best"][i][0] - hold["best"][i + 1][0]),
                                   abs(hold["best"][i][1] - hold["best"][i + 1][1])) != 1)
            return hold["best"], hold["cost"], nonstrict

        from itertools import product as iproduct
        best = None
        for combo in iproduct((-1, 0, 1), repeat=len(ambiguous)) if ambiguous else [()]:
            shift_map = {id(ln): s for ln, s in zip(ambiguous, combo)}
            g_, pa_, raw_ = build_atoms(shift_map)
            atom_cells = {}
            for kind, col, row, _ in pa_:
                atom_cells.setdefault((col, row), []).append(kind)
            start = next(((c, r) for (c, r), ks in atom_cells.items()
                          if "start" in ks), None)
            if start is None:
                continue
            chain, cost, nonstrict = chain_atoms(atom_cells, start)
            score = (len(chain), -cost, -nonstrict, -sum(abs(s) for s in combo))
            if best is None or score > best[0]:
                jps = {}
                for i, cellc in enumerate(chain):
                    for k in atom_cells.get(cellc, []):
                        if k.startswith("jp"):
                            jps[int(k[2:])] = i
                best = (score, g_, raw_, atom_cells, start, chain, jps)

        _, goals, jp_raw, atom_cells, start, chain, jps = best
        panels.append({"row": ri, "col": ci, "goals": goals,
                       "wall_cells": sorted(wall_cells), "start": start,
                       "path": chain, "judgment_steps": jps, "jp_raw": jp_raw,
                       "n_atoms": len(atom_cells)})

ok = sum(1 for pl in panels if pl["path"] and len(pl["path"]) == pl["n_atoms"])
print(f"panels decoded: {len(panels)}; fully chained: {ok}")
for pl in panels[:4]:
    print(f"  r{pl['row']}c{pl['col']}: goals {pl['goals']} start {pl['start']} "
          f"path len {len(pl['path'])} jps {pl['judgment_steps']} "
          f"walls {len(pl['wall_cells'])}")

dest = Path(__file__).with_name("fig3_stimuli.json")
dest.write_text(json.dumps({"grid": [GRID_W, GRID_H], "panels": panels}, indent=1),
                encoding="utf-8", newline="\n")
print(f"wrote {dest.name}")
