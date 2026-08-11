import sys, pymupdf, collections
doc = pymupdf.open(sys.argv[1])
p = doc[int(sys.argv[2])-1]
dr = p.get_drawings()
# find axes rects
panels = []
seen = set()
for d in dr:
    r = d["rect"]
    if len(d["items"]) == 1 and d["items"][0][0] == "re" and 30 < r.width < 200 and 20 < r.height < 120:
        k = (round(r.x0,1), round(r.y0,1), round(r.x1,1), round(r.y1,1))
        if k not in seen:
            seen.add(k); panels.append((k, r))
panels.sort(key=lambda t: (round(t[1].y0), t[1].x0))
print("candidate panels:", len(panels))
for k, r in panels: print("  ", k)

print("\n--- polylines with >=3 vertices (data series) ---")
for d in dr:
    its = d["items"]
    ls = [it for it in its if it[0] == "l"]
    if len(ls) >= 3:
        pts = [(round(ls[0][1].x,2), round(ls[0][1].y,2))] + [(round(it[2].x,2), round(it[2].y,2)) for it in ls]
        col = d.get("color") or d.get("fill")
        print("  n=", len(pts), "col=", [round(c,2) for c in col] if col else None,
              "dashes=", d.get("dashes"), "pts=", pts[:8])
