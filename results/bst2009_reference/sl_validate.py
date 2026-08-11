import json, sys, math
d = json.load(open(sys.argv[1]))
p1 = d["panel1"]["points"]
n = len(p1)
print("n points:", n, " -> triples:", n/3)
# check consecutive triples of HUMAN y sum to 1
bad = 0
sums = []
for i in range(0, n, 3):
    s = sum(p1[j][1] for j in range(i, i+3))
    sums.append(s)
    if abs(s-1) > 0.01: bad += 1
print(f"human triple sums: min={min(sums):.5f} max={max(sums):.5f} mean={sum(sums)/len(sums):.5f} outside 1+-0.01: {bad}")
# same for each panel's model x
for pk in ["panel1","panel2","panel3","panel4"]:
    pts = d[pk]["points"]
    ss = [sum(pts[j][0] for j in range(i,i+3)) for i in range(0,len(pts),3)]
    print(f"{pk} model-x triple sums: min={min(ss):.5f} max={max(ss):.5f} outside 1+-0.01: {sum(1 for s in ss if abs(s-1)>0.01)}")
# check y identical across panels
ys = [[pt[1] for pt in d[pk]["points"]] for pk in ["panel1","panel2","panel3","panel4"]]
maxdiff = max(max(abs(ys[0][i]-ys[k][i]) for i in range(n)) for k in range(1,4))
print("max |y_panel1 - y_panelK| across panels:", maxdiff)
# black points
blk = [i for i,pt in enumerate(p1) if pt[2] and pt[2][0] < 0.2]
print("black (targeted-analysis) points:", len(blk), "=", len(blk)/3, "stimuli")
