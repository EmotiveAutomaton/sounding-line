import sys, pymupdf, math, json
doc = pymupdf.open(sys.argv[1]); p = doc[16]; dr = p.get_drawings()
panels, seen = [], set()
for d in dr:
    r = d["rect"]
    if len(d["items"])==1 and d["items"][0][0]=="re" and 55<r.width<62 and 43<r.height<48:
        k=(round(r.x0,1),round(r.y0,1));
        if k not in seen: seen.add(k); panels.append(r)
panels.sort(key=lambda r:(round(r.y0), r.x0))
TRIALX=[0.0,0.25,0.5,0.75,1.0]
res={}
for i,r in enumerate(panels):
    # collect ALL line segments inside panel, excluding the frame itself
    segs=[]
    for d in dr:
        rr=d["rect"]
        if not (r.x0-2<=rr.x0 and rr.x1<=r.x1+2 and r.y0-2<=rr.y0 and rr.y1<=r.y1+2): continue
        for it in d["items"]:
            if it[0]!="l": continue
            (x0,y0),(x1,y1)=(it[1].x,it[1].y),(it[2].x,it[2].y)
            if abs(x1-x0)<0.4 and abs(y1-y0)<0.4: continue
            if abs(y1-y0)<0.01 and abs(x1-x0)>50: continue   # axis line
            segs.append((x0,y0,x1,y1,bool(d.get("dashes") and d["dashes"].strip() not in ("","[] 0"))))
    # trial x positions
    xs=sorted({round(s[0],1) for s in segs}|{round(s[2],1) for s in segs})
    def val(y): return round((r.y1-y)/(r.y1-r.y0),4)
    solid={}; dash={}
    for (x0,y0,x1,y1,dsh) in segs:
        tgt = dash if dsh else solid
        tgt.setdefault(round(x0,1),[]).append(val(y0)); tgt.setdefault(round(x1,1),[]).append(val(y1))
    def collapse(dd):
        ks=sorted(dd)
        return [ (k, round(sum(dd[k])/len(dd[k]),4)) for k in ks ]
    res[i+1]={"people":collapse(solid),"model":collapse(dash)}
    print(f"panel{i+1} PEOPLE {collapse(solid)}")
    print(f"         MODEL  {collapse(dash)}")
# pooled correlation over panels where both have 4 pts
P=[];M=[]
for i,v in res.items():
    if len(v["people"])==4 and len(v["model"])==4:
        P += [a[1] for a in v["people"]]; M += [a[1] for a in v["model"]]
n=len(P); mp=sum(P)/n; mm=sum(M)/n
num=sum((a-mp)*(b-mm) for a,b in zip(P,M))
den=math.sqrt(sum((a-mp)**2 for a in P))*math.sqrt(sum((b-mm)**2 for b in M))
print(f"\npooled n={n}  recovered People-vs-Model r = {num/den:.4f}   (paper prints r=0.97)")
json.dump({str(k):v for k,v in res.items()}, open(sys.argv[2],"w"), indent=1)
