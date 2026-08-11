import sys, pymupdf, collections, math, json

def pearson(xs, ys):
    n = len(xs)
    mx = sum(xs)/n; my = sum(ys)/n
    sxy = sum((a-mx)*(b-my) for a, b in zip(xs, ys))
    sxx = math.sqrt(sum((a-mx)**2 for a in xs))
    syy = math.sqrt(sum((b-my)**2 for b in ys))
    return sxy/(sxx*syy)

path = sys.argv[1]
pno = int(sys.argv[2])
doc = pymupdf.open(path)
p = doc[pno-1]
dr = p.get_drawings()

# 1. find the 4 panel axes: filled/stroked rects that are the plot boxes
# heuristic: rect paths with width 60-90 and height 45-70 near top of page
panels = []
for d in dr:
    r = d["rect"]
    if len(d["items"]) == 1 and d["items"][0][0] == "re" and 60 < r.width < 90 and 45 < r.height < 70:
        key = (round(r.x0,1), round(r.y0,1), round(r.x1,1), round(r.y1,1))
        if key not in [pp[0] for pp in panels]:
            panels.append((key, r))
panels.sort(key=lambda t: (round(t[1].y0), t[1].x0))
print("PANELS found:", len(panels))
for k, r in panels:
    print("   ", k)

# 2. collect zero-size dot paths
dots = []
for d in dr:
    r = d["rect"]
    if r.width < 0.05 and r.height < 0.05:
        col = d.get("color") or d.get("fill")
        dots.append((r.x0, r.y0, tuple(round(c,3) for c in col) if col else None))
print("zero-size dot paths:", len(dots))

# 3. assign dots to panels
out = {}
for idx, (k, r) in enumerate(panels):
    inside = [dd for dd in dots if r.x0-1 <= dd[0] <= r.x1+1 and r.y0-1 <= dd[1] <= r.y1+1]
    # data coords: x axis 0..1 across r.x0..r.x1 ; y axis 0..1 from r.y1(bottom) up to r.y0(top)
    pts = []
    for (px, py, col) in inside:
        dx = (px - r.x0) / (r.x1 - r.x0)
        dy = (r.y1 - py) / (r.y1 - r.y0)
        pts.append((round(dx, 5), round(dy, 5), col))
    cols = collections.Counter(pt[2] for pt in pts)
    rr = pearson([q[0] for q in pts], [q[1] for q in pts]) if len(pts) > 2 else float('nan')
    print(f"\nPANEL {idx+1} {k}: n={len(pts)}  recovered r = {rr:.4f}")
    print("   colors:", dict(cols))
    print("   first 6 pts:", pts[:6])
    out[f"panel{idx+1}"] = {"rect": k, "n": len(pts), "r": rr, "points": pts}

with open(sys.argv[3], "w") as f:
    json.dump(out, f, indent=1)
print("\nwrote", sys.argv[3])
