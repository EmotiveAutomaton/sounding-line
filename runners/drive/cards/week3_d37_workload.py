"""D37 known-answer worlds, admitted source loader and complete-run accounting.

DESIGN CHECK: LESSONS 3-5 and CONTROLS 1-7 read 2026-10-29. Common and page-only
worlds lack complementary information; the three-entry mixture supplies it.
Full refits and all same-row controls precede a result. Unsupported sources,
chronology, incomplete banks or nonfinite statistics refuse, never count as null.
"""
from collections import defaultdict
from pathlib import Path
import numpy as np
from . import week3_d37_readers as m
from . import menus_p4 as p4
from . import states_v2
from .timing_census import read, filehash

SEED=20261026
PERMUTATIONS=200
BOOTSTRAP=2000
WORLDS=30


def source(inputs):
    if set(inputs)!={'source_complete','source_landing','d15_complete','d15_landing'}:
        raise ValueError('Exact D37 source identities required')
    complete=Path(inputs['source_complete']); landing=read(inputs['source_landing']); root=complete.parent
    if landing.get('completion_sha256')!=filehash(complete) or not landing.get('full_write_through'):
        raise ValueError('Unlanded D37 source')
    for marker in (complete,Path(inputs['d15_complete'])):
        receipt=read(marker)
        if receipt.get('status')!='COMPLETE' or not receipt.get('fresh_process_verified'):
            raise ValueError('Unverified source')
        for name,digest in receipt['outputs'].items():
            path=(marker.parent/name).resolve(); path.relative_to(marker.parent.resolve())
            if filehash(path)!=digest:raise ValueError('Changed source artifact')
    data=read(root/'output/ROWS.json'); rows=data['rows']; arrays={k:np.load(root/'output'/(k+'.npy'),allow_pickle=False) for k in ('page','process','embedding')}
    d15_path=Path(inputs['d15_complete']).parent/'output/ROWS.json'
    if filehash(d15_path)!=read(inputs['d15_landing'])['row_hash']:raise ValueError('Unlanded D15 row source')
    old=read(d15_path); joined={r['key']:r for r in old}
    if len(joined)!=len(old) or set(joined)!={r['key'] for r in rows}:raise ValueError('Incomplete decoding-setting join')
    out=[]
    for row in rows:
        match=joined[row['key']]
        if any(row[k]!=match[k] for k in ('writer','session','prompt','handling')):raise ValueError('Canonical row identity differs')
        out.append(dict(row,setting=match['setting']))
    if len(rows)!=16855 or len(data['partitions'])!=41 or len(data['exclusions'])!=20:
        raise ValueError('Changed full source population')
    if any(a.shape!=(16855,n) for a,n in ((arrays['page'],53),(arrays['process'],6),(arrays['embedding'],768))):
        raise ValueError('Changed feature shape')
    return out,arrays,data['partitions'],np.array([p4.ACTIONS.index(r['handling']) for r in out]),data['exclusions']


def world(number):
    if type(number) is not int or not 0<=number<WORLDS:raise ValueError('Unknown frozen world')
    kind=('common','page_only','complementary')[number//10]
    rng=np.random.default_rng(SEED+200000+number); rows=[]; page=[]; process=[]; embedding=[]; sessions=[]; truth=[]
    for s in range(12):
        for w in range(8):
            start=1000*s+50*w; group=[]
            for j in range(8):
                a,b=rng.integers(4,size=2); av=np.eye(4)[a]; bv=np.eye(4)[b]; pv=np.eye(4)[w%4]
                probability=np.full(4,.25) if kind=='common' else .75*av+.25/4 if kind=='page_only' else (av+bv+pv)/3
                y=int(rng.choice(4,p=probability)); truth.append(probability.tolist())
                row=dict(key=f'w{w}-s{s}-r{j}',writer=f'w{w}',session=f'w{w}-s{s}',prompt=str(s%3),setting=str(j%2),
                         open_at=start+j*3,resolved_at=start+j*3+1,session_time=start,session_end=start+30,handling=p4.ACTIONS[y])
                rows.append(row); group.append(row); page.append(av); process.append(bv); embedding.append(rng.normal(size=8))
            sessions.append(dict(writer=f'w{w}',session=f'w{w}-s{s}',timestamp=start,end_at=start+30,rows=group))
    splits,_=p4.chronological_partitions(sessions); parts={}
    for w in sorted(splits):
        split=p4.recipient_split(w,splits)
        if split['reason'] is not None:raise ValueError('Constructed chronology unsupported')
        parts[w]={k:[s['session'] for s in split[k]] for k in ('train','own_train','calibration','test')}
        parts[w].update(cutoff=split['cutoff'],test_cutoff=split['test_cutoff'])
    arrays=dict(page=np.array(page),process=np.array(process),embedding=np.array(embedding))
    return rows,arrays,parts,np.array([p4.ACTIONS.index(r['handling']) for r in rows]),dict(kind=kind,world=number,truth=truth)


def session_values(predicted):
    if len({r['key'] for r in predicted})!=len(predicted):raise ValueError('Duplicate predictions')
    grouped=defaultdict(list)
    for r in predicted:
        losses=[p4.brier([r[k]],[r['truth']])[0] for k in ('single','stack')]
        entries=[p4.brier([p],[r['truth']])[0] for p in r['entries']]
        grouped[(r['writer'],r['session'])].append([losses[0]-losses[1],*losses,*entries])
    if not grouped:raise ValueError('No scored support')
    keys=sorted(grouped); values=np.array([np.mean(grouped[k],axis=0) for k in keys])
    return keys,values


def effect(predicted):
    return float(session_values(predicted)[1][:,0].mean())


def summarize(predicted,reference):
    reference=np.asarray(reference,float)
    if reference.shape!=(PERMUTATIONS,) or not np.isfinite(reference).all():raise ValueError('Incomplete reference bank')
    keys,values=session_values(predicted); writers=sorted({k[0] for k in keys})
    if len(writers)<2:raise ValueError('Population interval needs multiple writers')
    totals=np.array([values[[k[0]==w for k in keys],0].sum() for w in writers]); n=np.array([sum(k[0]==w for k in keys) for w in writers])
    rng=np.random.default_rng(SEED); samples=rng.integers(len(writers),size=(BOOTSTRAP,len(writers)))
    draws=totals[samples].sum(1)/n[samples].sum(1)
    point=float(values[:,0].mean()); interval=np.quantile(draws,[.025,.975]).tolist()
    mean=float(reference.mean()); sd=float(reference.std(ddof=1)); bias=abs(mean)>.25*sd if sd>0 else mean!=0
    probability=float((1+np.sum(reference>=point))/(PERMUTATIONS+1))
    return dict(estimate=point,interval95=interval,state=states_v2.classify(point,*interval),
                standard_error=float(draws.std(ddof=1)),writers=len(writers),sessions=len(keys),decisions=len(predicted),
                losses=dict(zip(('single','stack','page','person','process'),values[:,1:].mean(0).tolist())),
                reference=dict(draws=PERMUTATIONS,mean=mean,sd=sd,interval95=np.quantile(reference,[.025,.975]).tolist(),p_one_sided=probability,bias_flag=bool(bias)),
                licensed_positive=bool(interval[0]>0 and probability<.05 and not bias),
                useful_licensed_detection=bool(point>=.01 and interval[0]>0 and probability<.05 and not bias))
