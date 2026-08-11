import sys, pymupdf, collections
doc = pymupdf.open(sys.argv[1])
pno = int(sys.argv[2])
p = doc[pno-1]
dr = p.get_drawings()
# bucket paths by size of bbox
sizes = collections.Counter()
small = []
for d in dr:
    r = d["rect"]
    w, h = round(r.width, 2), round(r.height, 2)
    sizes[(w, h)] += 1
    if 0 < w < 8 and 0 < h < 8:
        small.append(d)
print("total paths:", len(dr))
print("top 25 bbox sizes (w,h)->count:")
for k, v in sizes.most_common(25):
    print("   ", k, v)
print("small paths (<8x8):", len(small))
# large rects = axes
print("\nlarge paths (>40 in either dim):")
for d in dr:
    r = d["rect"]
    if r.width > 40 or r.height > 40:
        print("   ", [round(x,1) for x in (r.x0,r.y0,r.x1,r.y1)], "items", [it[0] for it in d["items"]][:6], "n=", len(d["items"]))
