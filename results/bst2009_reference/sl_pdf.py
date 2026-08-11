import sys, pymupdf, os
src = sys.argv[1]
out = sys.argv[2]
doc = pymupdf.open(src)
print("PAGES:", doc.page_count)
with open(out, "w", encoding="utf-8") as f:
    for i, p in enumerate(doc):
        f.write(f"\n\n===== PAGE {i+1} =====\n")
        f.write(p.get_text())
print("wrote", out, os.path.getsize(out))
