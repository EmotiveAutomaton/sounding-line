"""SLD3 calibration by one thousand within-roster permutations of Neuroticism.

DESIGN CHECK. Shuffling preserves each contributing roster and its trait
distribution. The observed score must reproduce the gated SLD3 estimate.
Only registered aggregate null percentiles and observed ranks may leave.
"""
from itertools import combinations
from pathlib import Path
from tempfile import TemporaryDirectory
import numpy as np
import mi_source_contract_v1 as contract
import week6_person_slopes_v1 as ref
from frozen_trait import effect
from independent_release import Entry, decide
from joined_source import take_snapshot, read_roles
from week6_sealed_support_v1 import SealedFailure, write_tables
from week7_mib1 import reconstruct
from week7_mib3 import latest_trait_rosters
from week7_sld3 import ITEMS, GROUPS, prepare


def permuted_effect(scores, halves):
    a,b = halves
    w = np.minimum(a['n1'], b['n1'])[None,:]
    controls = [(a['L'],b['L'])]
    if ref.wpearson(w[0],a['S'],b['S'])>=.3:
        controls.append((a['S'],b['S']))
    slopes = (a['b'],b['b'])
    _,_,coef = ref.adjust(w,slopes,controls)
    mid = (slopes[0]+slopes[1])/2
    num = ref.wcov(w,scores,mid)
    for j,(x,y) in enumerate(controls):
        num -= ref.wcov(w,scores,(x+y)/2)*coef[0,j]
    den = np.sqrt(ref.wcov(w,scores,scores))*abs(ref.wmean(w,mid))
    return np.divide(num,den,out=np.full_like(num,np.nan),where=den>ref.EPS)


def calibrate(tables, observed, draws=1000, scalar_check=False):
    _,ids,scores,_,panels = prepare(tables,'M2')
    terms = [(i,) for i in range(len(GROUPS))]+list(combinations(range(len(ITEMS)),2))+[(len(ITEMS),len(ITEMS)+1)]
    masks=[np.isfinite(a['b'])&np.isfinite(b['b']) for a,b in panels]
    rng=np.random.default_rng(2026112303)
    # Shared random ordering induces a uniform permutation on each contributing set.
    orders=np.array([rng.permutation(len(ids)) for _ in range(draws)])
    ranks=np.argsort(orders,axis=1)
    result={}
    for code,target in observed.items():
        ix=int(code)-1; pair=terms[ix]
        mask=np.logical_and.reduce([masks[k] for k in pair])
        people=frozenset(p for p,yes in zip(ids,mask) if yes)
        if len(people)!=target['n']:raise SealedFailure(14,'Contributing roster differs')
        tr=scores[mask];null=tr[np.argsort(ranks[:,mask],axis=1)]
        values=np.empty((len(pair),draws+1))
        for slot,k in enumerate(pair):
            halves=[{key:v[mask] for key,v in side.items()} for side in panels[k]]
            for start in range(0,draws,32):
                values[slot,1+start:1+start+32]=permuted_effect(null[start:start+32],halves)
            values[slot,0]=effect(tr,halves,np.ones((1,len(tr))))[0]
            if scalar_check:
                check=np.array([effect(t,halves,np.ones((1,len(tr))))[0] for t in null])
                np.testing.assert_allclose(check,values[slot,1:],rtol=1e-8,atol=1e-10,equal_nan=True)
        joined=values[0] if len(pair)==1 else values[0]-values[1]
        if not np.isclose(joined[0],target['point'],rtol=1e-8,atol=1e-10):
            raise SealedFailure(14,'Original point differs')
        if not np.isfinite(joined).all():continue
        dist=joined[1:];q=np.quantile(dist,[.025,.5,.975])
        result[int(code)]=(dict(contrast=int(code),n=len(people),observed=float(joined[0]),lower=float(q[0]),median=float(q[1]),upper=float(q[2]),percentile=float(100*((dist<joined[0]).sum()+.5*(dist==joined[0]).sum())/draws)),people)
    return result


def run(mount,out,mapping,history,latest,observed,draws=1000,fixture=False):
    spec=contract.fields('M2')
    selections={'survey':['M2ID','M2FAMNUM',spec['traits']['neuroticism']],
                'diary':['M2ID',spec['study_day'],*spec['negative'],*(s['occurrence'] for s in spec['stressors'])]}
    limit=sum(v['bytes'] for v in mapping['M2'].values())
    with TemporaryDirectory(prefix='cal3-') as tmp:
        wave,paths=take_snapshot(Path(mount),Path(tmp),mapping,limit)
        if wave!='M2':raise SealedFailure(11,'Wrong wave')
        _,historic,groups=reconstruct(paths,history,False)
        if any(len(historic[k])!=n for k,n in history.items()):raise SealedFailure(14,'Roster mismatch')
        first=calibrate(read_roles(paths,selections),observed,draws,fixture)
        if first!=calibrate(read_roles(paths,selections),observed,draws):raise SealedFailure(14,'Independent source decode differs')
        known=[groups['survey'],*historic.values(),*latest_trait_rosters(paths,latest).values()]
        rows=[]
        for k,(row,roster) in first.items():
            if historic['sld3/'+str(k)]!=roster:raise SealedFailure(14,'Original roster differs')
            rows.append(Entry(row,roster))
        allowed,_=decide([(1,'calibration',rows)],groups['diary'],known)
        if not allowed:raise SealedFailure(12,'Release withheld')
        return write_tables(out,allowed)

