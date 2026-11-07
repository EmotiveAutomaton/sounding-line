"""TD5.ic balanced constructed whole-comment sensitivity, no human-power claim.

DESIGN CHECK: LESSONS 2-5, CONTROLS 6-7. Analytic zero and signed population
contrasts, full six-pair rule, missing support and exact grouped bootstrap law.
Every world stays in the denominator. Source labels and parent code unchanged.
"""
from pathlib import Path
from itertools import combinations,combinations_with_replacement
from math import factorial
import numpy as np
from runners.stage14.common import freeze,read,filehash
from .emotions import LABELS,CHANNELS,lifts,interval,pair_decision
from .mind_sensitivity import wilson

N=37335
DOSES=(0.,.1,.2,-.2)
NAMES=tuple(x for x in LABELS if x in {y for c in CHANNELS for y in c})
PAIRS=tuple(combinations(range(len(NAMES)),2))
PATTERNS=tuple(combinations_with_replacement(range(len(NAMES)),3))
NEGATIVE=(('anger','fear'),('annoyance','nervousness'),('grief','amusement'),('sadness','joy'),('curiosity','caring'),('excitement','love'),('desire','disgust'))

def features():
    counts=np.array([np.bincount(t,minlength=14) for t in PATTERNS],dtype=float)
    a=counts[:,[i for i,j in PAIRS]];b=counts[:,[j for i,j in PAIRS]]
    return np.column_stack([a*b,a,b,np.full(len(PATTERNS),3),np.full(len(PATTERNS),6)])

def probabilities(delta):
    if abs(delta)>7:raise ValueError('Impossible mixture')
    groups=CHANNELS if delta>=0 else NEGATIVE
    sets=[{NAMES.index(x) for x in g} for g in groups]
    beta=abs(delta)/7;out=[]
    for t in PATTERNS:
        factor=6
        for n in np.bincount(t,minlength=14):factor/=factorial(int(n))
        base=factor/14**3
        structured=sum(factor*(len(g)/14)/(len(g)**3) for g in sets if set(t)<=g)
        out.append((1-beta)*base+beta*structured)
    out=np.array(out);assert np.isclose(out.sum(),1,rtol=0,atol=1e-14)
    return out/out.sum()

def summarize(sums,boot):
    point,expected=lifts(sums,len(PAIRS));lookup={p:i for i,p in enumerate(PAIRS)}
    assignment={x:i for i,c in enumerate(CHANNELS) for x in c};rows=[]
    for channel in CHANNELS[:6]:
        members=[NAMES.index(x) for x in channel];own=lookup[tuple(sorted(members))]
        candidates=[]
        for k,(i,j) in enumerate(PAIRS):
            if not (i in members or j in members):continue
            other=j if i in members else i
            if assignment[NAMES[other]]!=assignment[channel[0]] and expected[k]>=50 and np.isfinite(point[k]):candidates.append(k)
        row=dict(channel=channel,within_lift=float(point[own]),within_expected=float(expected[own]),unassigned='unsupported competitor')
        if not candidates:
            row.update(status='unsupported competitor',difference=None,fixed_interval=None,reselected_interval=None,fixed='inconclusive',reselected='inconclusive')
        else:
            best=max(candidates,key=lambda k:(point[k],-k));delta=float(point[own]-point[best])
            fixed=interval(boot[:,own]-boot[:,best]);selected=interval(boot[:,own]-np.max(boot[:,candidates],axis=1))
            row.update(status='supported competitor',competitor=[NAMES[x] for x in PAIRS[best]],difference=delta,fixed_interval=fixed,reselected_interval=selected,fixed=pair_decision(delta,fixed),reselected=pair_decision(delta,selected))
        rows.append(row)
    packet={}
    for role in ('fixed','reselected'):
        decisions=[r[role] for r in rows]
        packet[role]='against' if decisions.count('loss')>=3 else 'supports' if decisions.count('win')==6 else 'inconclusive'
    return dict(pairs=rows,packet=packet)

def analyze(counts,draws=2000):
    counts=np.asarray(counts,dtype=np.int64);total=int(counts.sum())
    if total<=0 or np.any(counts<0):raise ValueError('Invalid pattern counts')
    mat=features();sums=counts@mat;active=counts>0
    rng=np.random.default_rng(20261106);boot=np.empty((draws,len(PAIRS)))
    for begin in range(0,draws,16):
        w=rng.multinomial(total,counts[active]/total,size=min(16,draws-begin)).astype(float)
        boot[begin:begin+len(w)]=lifts(w@mat[active],len(PAIRS))[0]
    return summarize(sums,boot)

def population(delta):
    sums=N*probabilities(delta)@features();point,_=lifts(sums,len(PAIRS))
    return summarize(sums,np.tile(point,(2,1)))

def calibration(worlds,n=N,draws=2000):
    doses={}
    for di,delta in enumerate(DOSES):
        prob=probabilities(delta);records=[]
        for wi in range(worlds):
            rng=np.random.default_rng(np.random.SeedSequence([20261106,di,wi]))
            records.append(analyze(rng.multinomial(n,prob),draws))
        roles={}
        for role in ('fixed','reselected'):
            counts={k:sum(r['packet'][role]==k for r in records) for k in ('supports','against','inconclusive')}
            counts['decisive']=counts['supports']+counts['against'];pair=[]
            for pi in range(6):
                rows=[r['pairs'][pi] for r in records]
                c={k:sum(r[role]==k for r in rows) for k in ('win','loss','inconclusive','invalid uncertainty')}
                c.update(coverage=sum(r[role+'_interval'] is not None and r[role+'_interval'][0]<=delta<=r[role+'_interval'][1] for r in rows),undefined=sum(r[role+'_interval'] is None for r in rows),unsupported=sum(r['status']=='unsupported competitor' for r in rows))
                values=[r['difference'] for r in rows if r['difference'] is not None]
                pair.append(dict(channel=CHANNELS[pi],counts=c,wilson95={k:wilson(v,worlds) for k,v in c.items()},mean_point_bias=float(np.mean(values))-delta if values else None))
            roles[role]=dict(counts=counts,wilson95={k:wilson(v,worlds) for k,v in counts.items()},pairs=pair)
        doses[str(delta)]=dict(delta=delta,worlds=worlds,roles=roles,records=records)
    sensitivity={}
    for role in ('fixed','reselected'):
        adequate=(doses['0.0']['roles'][role]['wilson95']['decisive'][1]<=.1 and doses['0.2']['roles'][role]['wilson95']['supports'][0]>=.8 and doses['-0.2']['roles'][role]['wilson95']['against'][0]>=.8)
        sensitivity[role]='adequate in construction' if adequate else 'limited in construction'
    return dict(constructed=True,comments=n,raters_per_comment=3,bootstrap_draws=draws,worlds_per_dose=worlds,doses=doses,sensitivity=sensitivity,human_power_validated=False)

def fixtures():
    pop={str(d):population(d) for d in DOSES}
    for d in DOSES:
        assert all(abs(r['difference']-d)<1e-12 for r in pop[str(d)]['pairs'])
    assert pop['0.0']['packet']['fixed']=='inconclusive'
    assert pop['0.2']['packet']['fixed']=='supports' and pop['-0.2']['packet']['fixed']=='against'
    return dict(populations=pop,calibration=calibration(2,n=4000,draws=32))

def calculate(inputs,config):
    if config.get('constructed'):return fixtures()
    for item in inputs.values():assert filehash(item['path'])==item['sha256']
    parent=read(inputs['parent']['path'])
    assert parent['exactly_three']['comments']==N and parent['exactly_three']['ratings']==N*3
    assert [r['channel'] for r in parent['primary']['pairs']]==CHANNELS[:6]
    return calibration(config['worlds'])

def execute(output,inputs,config):
    output=Path(output);output.mkdir(parents=True,exist_ok=True)
    freeze(output/'CALIBRATION.json',calculate(inputs,config));return dict(status='complete',constructed=True)

def verify(output,inputs,config):
    assert calculate(inputs,config)==read(Path(output)/'CALIBRATION.json')
    return dict(verified=True,complete_recalculation=True)
