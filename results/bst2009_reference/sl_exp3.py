import sys, pymupdf, math, json
doc = pymupdf.open(sys.argv[1])
p = doc[16]  # page 17 = Fig 10
dr = p.get_drawings()
panels = []
seen = set()
for d in dr:
    r = d["rect"]
    if len(d["items"]) == 1 and d["items"][0][0] == "re" and 55 < r.width < 62 and 43 < r.height < 48:
        k = (round(r.x0,1), round(r.y0,1), round(r.x1,1), round(r.y1,1))
        if k not in seen:
            seen.add(k); panels.append(r)
panels.sort(key=lambda r: (round(r.y0), r.x0))
labels = ["A-Far","A-Near","B-Far","B-Near","C-Far","C-Near","D-Far","D-Near"]
# NOTE: figure layout is 4 rows x 2 cols; row order per caption A,B,C,D (left col = Far? verify by x)
out = {}
for i, r in enumerate(panels):
    series = []
    for d in dr:
        rr = d["rect"]
        if not (r.x0-2 <= rr.x0 and rr.x1 <= r.x1+2 and r.y0-2 <= rr.y0 and rr.y1 <= r.y1+2):
            continue
        ls = [it for it in d["items"] if it[0] == "l"]
        if len(ls) < 3:
            continue
        pts = [(ls[0][1].x, ls[0][1].y)] + [(it[2].x, it[2].y) for it in ls]
        dashed = bool(d.get("dashes") and d["dashes"].strip() not in ("", "[] 0"))
        vals = [round((r.y1 - y) / (r.y1 - r.y0), 4) for (x, y) in pts]
        xs = [round(x, 2) for (x, y) in pts]
        series.append({"dashed": dashed, "x_px": xs, "values": vals})
    out[f"panel{i+1}"] = {"rect": [round(v,1) for v in (r.x0,r.y0,r.x1,r.y1)], "series": series}
    print(f"panel{i+1} rect={[round(v,1) for v in (r.x0,r.y0,r.x1,r.y1)]}")
    for s in series:
        print("   ", "MODEL(dashed)" if s["dashed"] else "PEOPLE(solid)", s["values"])
json.dump(out, open(sys.argv[2], "w"), indent=1)
print("\nwrote", sys.argv[2])
