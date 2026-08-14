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
for b in raw["blocks"]:
    for line in b.get("lines", []):
        for s in line["spans"]:
            for c in s["chars"]:
                x0, y0, x1, y1 = c["bbox"]
                chars.append({"c": c["c"], "x": (x0 + x1) / 2, "y": (y0 + y1) / 2,
                              "size": round(s["size"], 1)})
# figure area only (the big frame found by the probe: x 41-507, y 55-614)
chars = [c for c in chars if 41 <= c["x"] <= 508 and 54 <= c["y"] <= 615 and c["c"].strip()]

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

        goals, path_atoms = {}, []
        digits = []
        for c in sel:
            col, row = cell(c["x"], c["y"])
            if c["c"] in "ABC":
                goals[c["c"]] = (col, row)
            elif c["c"] == "x":
                path_atoms.append(("start", col, row, c["x"]))
            elif c["c"] == "-":
                path_atoms.append(("step", col, row, c["x"]))
            elif c["c"].isdigit():
                digits.append((c["x"], c["y"], c["c"], col, row))
        # digit glyphs group into numbers by x-adjacency at the same y. Intra-number glyph gap
        # measures 3.58-3.86pt, inter-number 4.12+; the threshold sits between them, and
        # grouping happens BEFORE cell snapping because a two-digit number straddles cells
        digits.sort(key=lambda d: (round(d[1], 1), d[0]))
        numbers = []
        for x, y, ch, col, row in digits:
            if numbers and abs(numbers[-1]["y"] - y) < 2 and x - numbers[-1]["x1"] < 4.0:
                numbers[-1]["text"] += ch
                numbers[-1]["x1"] = x
            else:
                numbers.append({"text": ch, "x0": x, "x1": x, "y": y})
        for n in numbers:
            col, row = cell((n["x0"] + n["x1"]) / 2, n["y"])
            path_atoms.append((f"jp{int(n['text'])}", col, row, n["x0"]))

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
        atom_cells = {}
        for kind, col, row, _ in path_atoms:
            atom_cells.setdefault((col, row), []).append(kind)
        start = next(((c, r) for (c, r), ks in atom_cells.items() if "start" in ks), None)

        def adjacent(a, b):
            dx, dy = abs(a[0] - b[0]), abs(a[1] - b[1])
            loose = any(k.startswith("jp") for k in atom_cells[a] + atom_cells[b])
            return (dx <= (2 if loose else 1)) and dy <= 1 and (dx or dy)

        chain, jps = [], {}
        if start:
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
            chain = hold["best"]
            for i, cellc in enumerate(chain):
                for k in atom_cells.get(cellc, []):
                    if k.startswith("jp"):
                        jps[int(k[2:])] = i
        panels.append({"row": ri, "col": ci, "goals": goals,
                       "wall_cells": sorted(wall_cells), "start": start,
                       "path": chain, "judgment_steps": jps,
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
