"""Fit the registered three stressor effects and their joint family-bootstrap contrast.

Imported only in the sealed entry, with the exact Week 7 scientific modules.
"""
from pathlib import Path
from tempfile import TemporaryDirectory

import numpy as np
import mi_source_contract_v1 as contract
from mi_source_bridge_v1 import _id, _trait
from frozen_trait import effect
from joined_source import read_roles, take_snapshot
from independent_release import Entry, decide
from week6_sealed_support_v1 import SealedFailure, write_tables
from week7_mib1 import reconstruct, trait_rosters
from week7_sld4 import substitute
from week8_stressor_contract import day_class, TRAITS, NEGATIVE


def prepare(tables, available):
    participants={}
    for row in tables['survey']:
        person=_id(row['M2ID'])
        if person in participants:
            raise SealedFailure(22,'Duplicate survey key')
        raw_family=row['M2FAMNUM']
        family=_id(raw_family) if raw_family is not None and np.isfinite(raw_family) and raw_family>0 else None
        participants[person]=(family,{name:_trait(row[TRAITS[name]]) for name in available})
    diary={}
    for row in tables['diary']:
        person=_id(row['M2ID'])
        person_days=diary.setdefault(person,{})
        day=contract.valid_code(row['B2DDAY'],range(1,9),missing=())
        if day is None:
            continue
        if day in person_days:
            raise SealedFailure(22,'Duplicate diary day')
        kind=day_class([row['B2DF'+str(i)] for i in range(1,8)])
        items=[contract.valid_code(row['B2DC'+str(i)],range(5)) for i in NEGATIVE]
        person_days[day]=(kind, np.nan if None in items else np.mean(items))
    ids=sorted(diary.keys() & participants.keys())
    scores={name:np.asarray([participants[p][1][name] for p in ids]) for name in available}
    fam=np.array([participants[p][0] for p in ids],dtype=object)
    panels=[]
    for kind in (1,2,3):
        halves=[]
        for half in (0,1):
            stats={key:[] for key in ('b','L','S','n1')}
            for p in ids:
                control,exposed=[],[]
                for day,(category,val) in diary[p].items():
                    if (day>4)!=bool(half) or not np.isfinite(val):
                        continue
                    if category==0:
                        control.append(val)
                    elif category==kind:
                        exposed.append(val)
                level=np.mean(control) if control else np.nan
                stats['b'].append(np.mean(exposed)-level if exposed and control else np.nan)
                stats['L'].append(level)
                stats['S'].append(np.std(control,ddof=1) if len(control)>1 else 0.)
                stats['n1'].append(len(exposed))
            halves.append({key:np.asarray(v) for key,v in stats.items()})
        panels.append(halves)
    return ids,scores,fam,panels


def memberships(ids,scores,fam,panels):
    rosters={}
    for trait,observed in scores.items():
        sets=[]
        for a,b in panels:
            keep=np.isfinite(observed)&np.isfinite(a['b'])&np.isfinite(b['b'])
            group=frozenset(p for p,on in zip(ids,keep) if on)
            if any(f is None for f in fam[keep]) or len(group)<11:
                group=frozenset()
            sets.append(group)
        union=frozenset().union(*sets) if all(sets) else frozenset()
        rosters[trait]=[*sets,union]
    return rosters


def releasable(rosters,universe,old_groups):
    catalogue=[]
    for i,(trait,groups) in enumerate(rosters.items(),1):
        entries=[]
        for k,group in enumerate(groups,1):
            if group:
                linked=tuple(groups[:3]) if k==4 else ()
                entries.append(Entry(dict(measure=k,n=len(group)),group,linked))
        catalogue.append((i,trait,entries))
    allowed,_=decide(catalogue,universe,old_groups)
    return {name:{int(r['measure']) for r in rows} for name,rows in allowed.items()}


def values_for(scores,families,panels,mode,draws):
    fid={family:i for i,family in enumerate(sorted(set(families)-{None}))}
    codes=np.asarray([fid.get(f,-1) for f in families],dtype=int)
    known=codes>=0
    total=len(fid)
    if total==0:
        return np.full((4,draws+1),np.nan)
    rng=np.random.default_rng(2026112704 if mode=='bootstrap' else 2026112705)
    values=np.full((4,draws+1),np.nan)
    def calculate(s,w):
        return np.stack([effect(s,halves,w) for halves in panels])
    ones=np.ones((1,len(families)))
    values[:3,:1]=calculate(scores,ones)
    for start in range(0,draws,32):
        size=min(32,draws-start)
        if mode=='bootstrap':
            w=np.zeros((size,len(families)))
            for j in range(size):
                multiplicity=np.bincount(rng.integers(total,size=total),minlength=total)
                w[j,known]=multiplicity[codes[known]]
            values[:3,start+1:start+1+size]=calculate(scores,w)
        else:
            for j in range(size):
                s=scores.copy()
                valid=np.isfinite(s)
                s[valid]=rng.permutation(s[valid])
                values[:3,start+1+j:start+2+j]=calculate(s,ones)
    values[3]=values[0]-(values[1]+values[2])/2
    return values


def study(tables,config,historical,universe):
    ids,scores,families,panels=prepare(tables,config['available'])
    rosters=memberships(ids,scores,families,panels)
    permitted=releasable(rosters,universe,historical)
    shuffle=config['mode']=='shuffle'
    selected=config['available'] if shuffle else [config['mode']]
    entries=[]
    for name in selected:
        if not permitted.get(name):continue
        vals=values_for(scores[name],families,panels,'shuffle' if shuffle else 'bootstrap',config['draws'])
        for k in sorted(permitted[name]):
            v=vals[k-1]
            # The qualified SLD3 fit requires a defined estimate and every draw.
            if not np.isfinite(v).all():continue
            group=rosters[name][k-1]
            lower,upper=np.quantile(v[1:],[.025,.975])
            row=dict(trait=list(TRAITS).index(name)+1,measure=k,estimate=float(v[0]),
                     lower=float(lower),upper=float(upper),n=len(group))
            if shuffle:
                row['percentile']=float((np.sum(v[1:]<v[0])+.5*np.sum(v[1:]==v[0]))/len(v[1:]))
            entries.append(row)
    if not entries:
        raise SealedFailure(12,'No eligible disclosable fit')
    return {'shuffle' if shuffle else 'trait':entries}


def run(mount,out,config):
    source_map=config['files']
    maximum=sum(record['bytes'] for record in source_map['M2'].values())
    with TemporaryDirectory() as scratch:
        wave,paths=take_snapshot(Path(mount),Path(scratch),source_map,maximum)
        if wave!='M2':raise SealedFailure(11,'Unexpected wave')
        _,sets,groups=reconstruct(paths,config['history'],False)
        if any(len(group)!=config['history'][key] for key,group in sets.items()):
            raise SealedFailure(14,'Earlier survey or diary membership differs')
        fields=contract.fields(wave)
        selection=dict(survey=['M2ID','M2FAMNUM',*[TRAITS[x] for x in config['available']]],
                       diary=['M2ID',fields['study_day'],*fields['negative'],*[s['occurrence'] for s in fields['stressors']]])
        source=read_roles(paths,selection)
        previous=[groups['survey'],*sets.values()]
        for name,counts in config['sld4'].items():
            old=trait_rosters(substitute(source,name))
            for k,n in counts.items():
                if k not in old or len(old[k])!=n:
                    raise SealedFailure(14,'Earlier trait membership differs')
                previous.append(old[k])
        first=study(source,config,previous,groups['diary'])
        if first!=study(read_roles(paths,selection),config,previous,groups['diary']):
            raise SealedFailure(14,'Independent fit differs')
        write_tables(out,first)
