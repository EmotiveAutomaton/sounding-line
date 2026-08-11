import sys, pymupdf
doc = pymupdf.open(sys.argv[1])
p = doc[int(sys.argv[2])-1]
d = p.get_text("dict")
spans = []
for b in d["blocks"]:
    for l in b.get("lines", []):
        for s in l["spans"]:
            spans.append((s["bbox"], s["text"], round(s["size"],1)))
# panel 1 of Fig 3 occupies roughly x 90-160, y 70-110 (from wall rect 143.7,77.6-105.7)
sel = [s for s in spans if 80 <= s[0][0] <= 175 and 65 <= s[0][1] <= 115]
sel.sort(key=lambda s: (s[0][0]))
print("=== Fig3 top-left panel (x 80-175, y 65-115): chars with positions ===")
for bbox, t, sz in sel:
    print(f"  x={bbox[0]:7.2f} y={bbox[1]:7.2f}  size={sz}  {t!r}")
print("\ntotal spans on page:", len(spans))
