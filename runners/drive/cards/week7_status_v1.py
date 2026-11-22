"""Phase 0 status panels on the pinned open-diary projections."""
from pathlib import Path
import sys
import time

import numpy as np
import pandas as pd

from . import week6_lb_bank_v1 as bank
from . import week6_ld12_common_v1 as core
from . import week6_person_small_v1 as old
from .batch_runtime import atomic, filehash, freeze, now, read
from .week6_ld_draws_v1 import RequestedYield

CARDS = ('PSD2','ISO1','PSD1')
BASE = ('id','day','beep','interaction')

def columns(card):
    if card == 'PSD1':
        return ('id','interaction','int_ashamed',*old.EVENTS)
    if card == 'ISO1':
        feelings = ('ashamed','angry','sad')
        events = ()
    elif card == 'PSD2':
        feelings = ('proud','ashamed')
        events = ('status_admired','status_criticised')
    else:
        raise ValueError('Unknown panel')
    return (*BASE,*events,*(ctx+'_'+m for m in feelings for ctx in ('int','occup')))

def binding(card,member,root):
    if member not in ('0056','0057'):
        raise ValueError('Unknown member')
    path, digest = old.binding('PRD1',member,root)
    directory = path.parent.parent
    features = {f['name']: f for f in read(directory/'DOCUMENTED_METADATA.json')['features']}
    layout, = (t for t in read(directory/'SCHEMA.json')['files'] if t['file']==path.name)
    if set(columns(card)) - features.keys() or set(columns(card)) - {c['name'] for c in layout['columns']}:
        raise ValueError('Unbound columns')
    if any(str(features[c]['answer_categories']) != '6' for c in columns(card) if c.startswith(('status_','int_','occup_'))):
        raise ValueError('Unexpected rating scale')
    return path,digest

def joint_terms(pride,shame,cut):
    complete = np.isfinite(pride) & np.isfinite(shame)
    a = pride[complete] >= cut
    b = shame[complete] >= cut
    if not a.any() or not b.any():
        return 0., 0.
    n = len(a)
    return n*n*float((a & b).sum())/(a.sum()*b.sum()), float(n)

def dial_terms(g, median_positive=False):
    p, s = (g[k].to_numpy(float) for k in ('proud','ashamed'))
    v = []
    for cutoff in (2,3):
        v.extend(joint_terms(p,s,cutoff))
    # Values are in source units, with 1 at the floor.
    adm = g.status_admired.to_numpy(float)
    cri = g.status_criticised.to_numpy(float)
    both = g.interaction.eq(1).to_numpy() & np.isfinite(adm) & np.isfinite(cri)
    a,c,n = (both & x for x in ((adm>1)&(cri==1),(cri>1)&(adm==1),(cri==1)&(adm==1)))
    valid_pride = p[np.isfinite(p) & ((p>1) if median_positive else True)]
    med = np.median(valid_pride) if valid_pride.size else np.inf
    adjacent = g.adjacent.to_numpy(bool)[1:]
    for y,other,own,threshold in ((p,c,a,med),(s,a,c,1)):
        change = np.diff(y)
        use = adjacent & (y[:-1]>threshold) & np.isfinite(change)
        for mask in (use & other[1:],use & n[1:]):
            v.extend((change[mask].sum(),float(mask.sum())))
        # The analogue of the reference's centred event/none rise, in points.
        obs = np.isfinite(y)
        center = y[obs].mean() if obs.any() else 0.
        for mask in (obs & own,obs & n):
            v.extend(((y[mask]-center).sum(),float(mask.sum())))
    return v

def dial_values(v):
    def ratio(a,b):
        return float(a/b) if b else None
    means=[ratio(a,b) for a,b in zip(v[::2],v[1::2])]
    result={'cooccurrence_one':means[0],'cooccurrence_two':means[1]}
    for i,name in ((2,'proud'),(6,'ashamed')):
        fall=core.contrast(means[i],means[i+1])
        rise=core.contrast(means[i+2],means[i+3])
        result['fall_'+name]=fall
        result['rise_'+name]=rise
        result['fall_share_'+name]=ratio(fall,rise) if fall is not None and rise is not None else None
    return result

def ordered(frame):
    g=frame.sort_values(['id','day','beep'],kind='stable').copy()
    dup=g.duplicated(['id','day','beep'],keep=False) | g.day.isna() | g.beep.isna()
    same=g.id.eq(g.id.shift()) & g.day.eq(g.day.shift()) & g.beep.diff().eq(1)
    g['adjacent']=same & ~dup & ~dup.shift(fill_value=True)
    g['next_no']=g.interaction.shift(-1).map({1:0.,2:1.}).where(g.adjacent.shift(-1,fill_value=False))
    return g,int(dup.sum())

def iso_moments(frame,beeps,reverse):
    f=frame.copy()
    for feeling in ('ashamed','angry','sad'):
        values=f[feeling]
        sd=values.std(ddof=1)
        f[feeling]=(values-values.mean())/sd if sd>0 else values.where(values.isna(),0.)
    f['current_no']=f.interaction.map({1:0.,2:1.})
    f=f.dropna(subset=['ashamed','angry','sad','current_no','next_no','beep'])
    vals=f[['ashamed','angry','sad','current_no']].to_numpy()
    x=np.column_stack([vals,*[(f.beep==b).to_numpy(float) for b in beeps[1:]],f.next_no.to_numpy()])
    if len(x):
        x=x-x.mean(axis=0)
    return np.einsum('ij,ik->jk',x,x) if reverse else x.T@x

def prepare(card,f,replay):
    f=f.dropna(subset=['id']).copy()
    people,idx=np.unique(f.id.astype(str),return_inverse=True)
    f['id']=idx
    for k in columns(card):
        if k=='id': continue
        f[k]=pd.to_numeric(f[k],errors='raise')
        a=f[k].dropna()
        if (a%1!=0).any() or (k=='interaction' and not a.isin([1,2]).all()) or (k.startswith(('int_','occup_','status_')) and not a.between(1,6).all()):
            raise ValueError('Unexpected coding for '+k)
    data=core.Prepared(len(people),dict(people=len(people),source_prompts=len(f)))
    if card=='PSD1':
        f=f.loc[f.interaction.eq(1)].dropna(subset=[*old.EVENTS,'int_ashamed'])
        data.panels['logit']=(f.id.to_numpy(),f[list(old.EVENTS)].to_numpy(float),f.int_ashamed.to_numpy()>1)
        keys=[*old.EVENTS,'criticised_minus_abs_admired']
        data.metadata['matched_prompts']=len(f)
    else:
        f,ambiguous=ordered(f)
        feelings=('proud','ashamed') if card=='PSD2' else ('ashamed','angry','sad')
        for name in feelings:
            f[name]=np.select([f.interaction.eq(1),f.interaction.eq(2)],[f['int_'+name],f['occup_'+name]],default=np.nan)
        data.metadata.update(ambiguous_or_undated=ambiguous,adjacent_pairs=int(f.adjacent.sum()))
        groups=f.groupby('id',sort=True)
        if card=='PSD2':
            matrix=np.array([dial_terms(g) for _,g in groups])
            data.panels['dial']=matrix
            data.metadata.update(one_step_people=int((matrix[:,1]>0).sum()),two_step_people=int((matrix[:,3]>0).sum()),
                                 one_step_prompts=int(matrix[:,1].sum()),two_step_prompts=int(matrix[:,3].sum()))
            keys=list(dial_values(np.ones(20)))
        else:
            beeps=sorted(f.dropna(subset=['beep','next_no','interaction',*feelings]).beep.unique())
            matrix=np.stack([iso_moments(g,beeps,replay) for _,g in groups])
            data.panels['iso']=matrix
            data.metadata.update(scheduled_beeps=[int(b) for b in beeps],people_with_predictor_variation=int(np.any(matrix[:,:3,:3]!=0,axis=(1,2)).sum()))
            keys=['ashamed','angry','sad','ashamed_minus_others']
    data.specs={key:{'bar':0.8 if key=='cooccurrence_two' else None} for key in keys}
    return data

def evaluate(data,weights,guard,*,verify=False):
    guard()
    m=core.multiplicities(data.people,weights)
    out=dict.fromkeys(data.specs)
    if 'dial' in data.panels:
        a=data.panels['dial']
        sums=np.einsum('i,ij->j',m,a) if verify else m@a
        return dial_values(sums)
    if 'iso' in data.panels:
        a=np.einsum('i,ijk->jk',m,data.panels['iso'])
        xx,xy=a[:-1,:-1],a[:-1,-1]
        if np.linalg.matrix_rank(xx)==len(xx):
            b=np.linalg.lstsq(xx,xy,rcond=None)[0] if verify else np.linalg.solve(xx,xy)
            out.update(zip(('ashamed','angry','sad'),map(float,b[:3])))
            out['ashamed_minus_others']=float(b[0]-np.mean(b[1:3]))
        return out
    ids,x,y=data.panels['logit']
    w=m[ids]
    within,logit,_=core.arithmetic(verify)
    try:
        z,means,_=within(x,ids,w)
        b=logit(np.column_stack((np.ones(len(y)),z,means)),y,w)
        out.update(zip(old.EVENTS,map(float,b[1:7])))
        out['criticised_minus_abs_admired']=float(b[3]-abs(b[1]))
    except old.ERRORS:
        pass
    return out

def operate(output,inputs,config,verify):
    card,member=config['card'],config['member']
    path,sha=binding(card,member,inputs['data_root'])
    if sha!=inputs['source_sha256'] or inputs['manifest_sha256']!=old.MANIFEST:
        raise ValueError('Source differs from reviewed plan')
    f=pd.read_csv(path,sep='\t',usecols=columns(card),dtype={'id':str})
    data=prepare(card,f,verify)
    phase='verify' if verify else 'execute'
    start=time.monotonic()
    def guard():
        if time.monotonic()-start>=config['max_wall_seconds'] or any((output/n).exists() for n in ('STOP_REQUEST.json','YIELD_REQUEST.json')):
            raise RequestedYield('runtime limit')
    def progress(count,elapsed):
        atomic(output/phase/'DRAW_PROGRESS.json',dict(at=now(),phase=phase,committed_draws=count,elapsed=elapsed))
    try:
        result=bank.run(output/phase,sys.modules[__name__],data,member=member,source_digest=sha,seed=202611190000+int(member),
                        guard=guard,verify=verify,execute_dir=output/'execute',limit=config['max_new_draws'],progress=progress)
    except RequestedYield as exc:
        return dict(status='yielded',verified=False,reason=str(exc))
    p=output/phase/'ENGINE_RESULT.json'
    if p.exists():
        if read(p)!=result: raise ValueError('Conflicting completed result')
    else: freeze(p,result)
    return dict(status='verified' if verify else 'computed',verified=verify,engine_sha256=filehash(p),draw_count=2000)

def execute(output,inputs,config):
    return operate(Path(output),inputs,config,False)

def verify(output,inputs,config):
    return operate(Path(output),inputs,config,True)
