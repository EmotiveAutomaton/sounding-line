"""Week 8 SLD9. All survey memberships and family bootstrap draws stay in the seal."""
from pathlib import Path
from tempfile import TemporaryDirectory

import numpy as np
import mi_source_contract_v1 as contract
from independent_release import Entry, decide
from joined_source import read_roles, take_snapshot
from week6_sealed_support_v1 import SealedFailure, write_tables
from week7_mib1 import reconstruct, trait_rosters
from week7_sld4 import substitute
from week8_stressor_contract import TRAITS

SCALES = ('B1SPWBU2','B1SPWBE2','B1SPWBG2','B1SPWBR2','B1SPWBS2','B1SPWBA2','B1SCTRL','B1SGENER','B1SE3')
BOUNDS = [(1,4)]*5 + [(7,49)]*6 + [(1,7),(6,24),(1,10)]
TOTAL = len(TRAITS)+len(SCALES)
NEURO = list(TRAITS).index('neuroticism')


def membership(survey):
    people=set()
    ids, family, data = [], [], []
    names=(*TRAITS.values(),*SCALES)
    for row in survey:
        person=row['M2ID']
        if not np.isfinite(person) or person<=0 or int(person)!=person or person in people:
            raise SealedFailure(22,'Ambiguous person')
        people.add(person)
        values=[row[k] for k in names]
        fam=row['M2FAMNUM']
        if not np.isfinite(fam) or fam<=0 or fam!=int(fam):
            continue
        if any(not (a<=val<=b) for val,(a,b) in zip(values,BOUNDS)):
            continue
        if values[-1]!=int(values[-1]):
            raise SealedFailure(24,'Unbound ladder category')
        values[-1]=11-values[-1]
        ids.append(person); family.append(fam); data.append(values)
    return frozenset(ids),np.asarray(data,dtype=float).reshape(-1,TOTAL),np.unique(family,return_inverse=True)[1]


def ranks_and_correlations(bins, weights):
    rank=[]
    for codes in bins:
        counts=np.bincount(codes,weights=weights,minlength=int(codes.max())+1)
        middle=counts.cumsum()-.5*counts
        rank.append(middle[codes])
    centered=np.column_stack(rank)
    centered-=np.average(centered,axis=0,weights=weights)
    gram=(centered.T * weights) @ centered
    norm=np.sqrt(np.diag(gram))
    with np.errstate(invalid='ignore',divide='ignore'):
        corr=gram/np.outer(norm,norm)
        t=corr[:5,NEURO,None]
        s=corr[None,NEURO,5:]
        raw=corr[:5,5:]
        tvar=np.maximum(0,1-t*t)
        svar=np.maximum(0,1-s*s)
        denom=np.sqrt(tvar*svar)
        out=np.divide(raw-t*s,denom,out=np.full_like(raw,np.nan),where=(tvar>1e-12)&(svar>1e-12))
    out[NEURO]=np.nan
    return np.clip(np.stack((raw,out)),-1,1)


def calculate(data, family, draws):
    bins=[np.unique(column,return_inverse=True)[1] for column in data.T]
    n=len(data)
    total=int(family.max())+1
    if total<2:
        return []
    rng=np.random.default_rng(2026112710)
    estimates=[ranks_and_correlations(bins,np.ones(n))]
    probabilities=np.full(total,1./total)
    for _ in range(draws):
        weights=rng.multinomial(total,probabilities)
        estimates.append(ranks_and_correlations(bins,weights[family]))
    estimates=np.asarray(estimates)
    rows=[]
    for form,trait,scale in np.ndindex(2,5,9):
        values=estimates[:,form,trait,scale]
        if not np.isfinite(values).all():
            continue
        low,high=np.quantile(values[1:],[.025,.975])
        rows.append(dict(form=form+1,trait=trait+1,scale=scale+1,estimate=float(values[0]),
                         lower=float(low),upper=float(high),n=n))
    return rows


def run(mount,out,config):
    src=config['files']
    maximum=sum(record['bytes'] for record in src['M2'].values())
    with TemporaryDirectory() as scratch:
        wave,paths=take_snapshot(Path(mount),Path(scratch),src,maximum)
        if wave!='M2':
            raise SealedFailure(11,'Incorrect source wave')
        _,sets,groups=reconstruct(paths,config['history'],False)
        if any(len(group)!=config['history'][key] for key,group in sets.items()):
            raise SealedFailure(14,'Historic count changed')
        known=[groups['survey'],*sets.values()]
        fields=contract.fields('M2')
        selection=dict(survey=['M2ID','M2FAMNUM',*TRAITS.values(),*SCALES],
                       diary=['M2ID',fields['study_day'],*fields['negative'],*[s['occurrence'] for s in fields['stressors']]])
        source=read_roles(paths,selection)
        for name,counts in config['sld4'].items():
            old=trait_rosters(substitute(source,name))
            for key,n in counts.items():
                if key not in old or len(old[key])!=n:
                    raise SealedFailure(14,'Earlier trait membership differs')
                known.append(old[key])
        def compute(rows):
            roster,data,family=membership(rows['survey'])
            check,_=decide([(1,'correlations',[Entry({'n':len(roster)},roster)])],groups['survey'],known)
            if not check:
                raise SealedFailure(12,'Complete sample withheld')
            table=calculate(data,family,config['draws'])
            if not table:
                raise SealedFailure(12,'No defined correlations')
            return {'correlations':table}
        result=compute(source)
        if result!=compute(read_roles(paths,selection)):
            raise SealedFailure(14,'Independent survey replay differs')
        write_tables(out,result)
