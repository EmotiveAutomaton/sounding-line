import sys, pymupdf
doc = pymupdf.open(sys.argv[1])
pages = [int(x) for x in sys.argv[2].split(",")]
for pno in pages:
    p = doc[pno-1]
    dr = p.get_drawings()
    imgs = p.get_images(full=True)
    # count item types
    types = {}
    for d in dr:
        for it in d["items"]:
            types[it[0]] = types.get(it[0], 0) + 1
    print(f"--- page {pno}: {len(dr)} drawing paths, items={types}, raster_images={len(imgs)}")
    for im in imgs:
        print("    IMG xref", im[0], "w,h=", im[2], im[3], "bpc", im[4], "cs", im[5])
