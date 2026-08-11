import sys, pymupdf, collections
doc = pymupdf.open(sys.argv[1])
p = doc[int(sys.argv[2])-1]
dr = p.get_drawings()
rects = [d for d in dr if all(it[0] == "re" for it in d["items"])]
print("rect-only paths:", len(rects))
big = [d for d in rects if d["rect"].width > 30 and d["rect"].height > 15]
print("large rects (panel frames?):", len(big))
for d in sorted(big, key=lambda d: (round(d["rect"].y0), d["rect"].x0))[:12]:
    r = d["rect"]
    print("   frame", [round(v,1) for v in (r.x0,r.y0,r.x1,r.y1)], "fill", d.get("fill"), "w/h=", round(r.width/r.height,3))
small_re = [d for d in rects if d["rect"].width <= 30 or d["rect"].height <= 15]
print("\nsmall/filled rects (walls):", len(small_re))
for d in sorted(small_re, key=lambda d: (round(d["rect"].y0), d["rect"].x0))[:10]:
    r = d["rect"]
    print("   wall", [round(v,1) for v in (r.x0,r.y0,r.x1,r.y1)], "fill", d.get("fill"))
print("\n--- polylines (agent paths) ---")
polys = [d for d in dr if sum(1 for it in d["items"] if it[0]=="l") >= 2]
print("count:", len(polys))
for d in sorted(polys, key=lambda d: (round(d["rect"].y0), d["rect"].x0))[:6]:
    ls = [it for it in d["items"] if it[0]=="l"]
    pts = [(round(ls[0][1].x,2), round(ls[0][1].y,2))] + [(round(it[2].x,2), round(it[2].y,2)) for it in ls]
    print("   n=", len(pts), "dashes=", d.get("dashes"), pts[:14])
