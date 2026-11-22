"""PSD3. Chronological halves with the registered PST3 variance gates.

DESIGN CHECK (LESSONS 3–5). Constructed identical slopes recover one.
Missing support and nonpositive variances cannot establish a correlation.
"""
from pathlib import Path
import sys
import time
import numpy as np
import pandas as pd
from . import week6_lb_bank_v1 as bank, week6_ld12_common_v1 as core
from . import week6_person_ladder_v1 as ladder, week6_person_slopes_v1 as op, week6_person_small_v1 as old
from .batch_runtime import atomic, filehash, freeze, now, read
from .week6_ld_draws_v1 import RequestedYield

MEASURES=(('proud','admired'),('ashamed','criticised'))
COLUMNS=('id','day','interaction','int_proud','int_ashamed','status_admired','status_criticised')
KEYS=('proud_variance','ashamed_variance','paired_proud_variance','paired_ashamed_variance','covariance','correlation')

def binding(card,member,root):
    if card!='PSD3' or member not in ('0056','0057'):raise ValueError('Unknown half-slope source')
    p,pin=old.binding('PRD1',member,root)
    items={x['name']:x for x in read(p.parent.parent/'DOCUMENTED_METADATA.json')['features']}
    if not set(COLUMNS)<=items.keys() or any(str(items[c]['answer_categories'])!='6' for c in COLUMNS[3:]):
        raise ValueError('Unbound half-slope items')
    return p,pin

def panel_parts(parts,keep,w):
    pair=[{k:v[keep] for k,v in h.items()} for h in parts]
    covs=[(pair[0]['L'],pair[1]['L'])]
    if len(w)>1:
        with np.errstate(invalid='ignore',divide='ignore'):
            if op.wpearson(w,pair[0]['S'],pair[1]['S'])>=.30:covs.append((pair[0]['S'],pair[1]['S']))
    return ((pair[0]['b'],pair[1]['b']),covs)

def prepare(frame,replay):
    f=frame.dropna(subset=['id','day']).loc[lambda t:t.interaction.eq(1)].copy()
    for k in COLUMNS[3:]:
        if not f[k].dropna().isin(range(1,7)).all():raise ValueError('Out-of-range '+k)
    people,ids=np.unique(f.id.astype(str),return_inverse=True)
    y={a:ladder.scale(f['int_'+a].to_numpy(float),ids) for a,b in MEASURES}
    ev={a:f['status_'+b].where(f['status_'+b].isna(),f['status_'+b].gt(1).astype(float)).to_numpy(float) for a,b in MEASURES}
    days=f.groupby('id').day
    half=f.day.gt((days.transform('min')+days.transform('max'))/2).to_numpy(int)
    groups,_=ladder.half_panel(dict(ids=ids,n=len(people),feelings=y,slopes={a:(ev[a],y[a]) for a,b in MEASURES}),half,replay)
    valid={a:np.isfinite(parts[0]['b'])&np.isfinite(parts[1]['b']) for a,parts in groups.items()}
    data=core.Prepared(len(people),{'people':len(people),'interaction_prompts':len(f)})
    for name,keep in [*valid.items(),('paired',valid['proud']&valid['ashamed'])]:
        names=list(valid) if name=='paired' else [name]
        w=np.minimum.reduce([side['n1'][keep] for a in names for side in groups[a]])
        data.metadata[name+'_people']=int(keep.sum())
        data.panels[name]=(keep,w,[panel_parts(groups[a],keep,w) for a in names])
    data.specs={k:{} for k in KEYS}
    return data

def evaluate(data,weights,guard,*,verify=False):
    guard()
    counts=core.multiplicities(data.people,weights)
    result=dict.fromkeys(KEYS)
    for name,(keep,base,parts) in data.panels.items():
        w=(base*counts[keep])[None,:]
        if np.count_nonzero(w)<2:continue
        residual=[]
        for side,(slope,cov) in enumerate(parts):
            _,adjusted,beta=op.adjust(w,slope,cov)
            key=('paired_'+MEASURES[side][0] if name=='paired' else name)+'_variance'
            result[key]=float(adjusted[0])
            residual.append(tuple(slope[i]-sum(beta[0,j]*x[i] for j,x in enumerate(cov)) for i in (0,1)))
        if name=='paired':
            value=float(op.cc(w,*residual)[0])
            result['covariance']=value
            a,b=result['paired_proud_variance'],result['paired_ashamed_variance']
            if min(a,b)>np.finfo(float).eps:result['correlation']=value/float(np.sqrt(a*b))
    return result

def operate(output,inputs,config,replay):
    p,pin=binding(config['card'],config['member'],inputs['data_root'])
    if inputs['source_sha256']!=pin or inputs['manifest_sha256']!=old.MANIFEST:raise ValueError('Source changed')
    data=prepare(pd.read_csv(p,sep='\t',usecols=COLUMNS,dtype={'id':str}),replay)
    start=time.monotonic()
    def guard():
        if time.monotonic()-start>=config['max_wall_seconds'] or any((Path(output)/x).exists() for x in ('STOP_REQUEST.json','YIELD_REQUEST.json')):
            raise RequestedYield('runtime limit')
    d=Path(output)/('verify' if replay else 'execute')
    def progress(n,t):atomic(d/'DRAW_PROGRESS.json',dict(at=now(),committed_draws=n,elapsed=t))
    try:
        val=bank.run(d,sys.modules[__name__],data,member=config['member'],source_digest=pin,seed=202611190000+int(config['member']),
            guard=guard,verify=replay,execute_dir=Path(output)/'execute',limit=config['max_new_draws'],progress=progress)
    except RequestedYield as exc:return dict(status='yielded',verified=False,reason=str(exc))
    dest=d/'ENGINE_RESULT.json'
    if dest.exists():
        if read(dest)!=val:raise ValueError('Changed completed half-slope return')
    else:freeze(dest,val)
    return dict(status='verified' if replay else 'computed',verified=replay,engine_sha256=filehash(dest),draw_count=2000)

def execute(output,inputs,config):return operate(output,inputs,config,False)
def verify(output,inputs,config):return operate(output,inputs,config,True)
