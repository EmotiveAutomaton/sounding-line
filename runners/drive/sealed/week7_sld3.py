"""Sealed daily-diary trait study, with the previously qualified TRX1 effect."""
from itertools import combinations
from pathlib import Path
from tempfile import TemporaryDirectory

import numpy as np

import mi_source_contract_v1 as contract
from mi_source_bridge_v1 import _id, _trait
from joined_source import take_snapshot, read_roles
from independent_release import Entry, decide
from week6_sealed_support_v1 import SealedFailure, write_tables
from frozen_trait import effect


ITEMS = contract.NEGATIVE
GROUPS = [(i,) for i in ITEMS] + [(19, 16, 20), (14, 2, 15), ITEMS]


def prepare(tables, wave):
    fields = contract.fields(wave)
    trait_field = fields['traits']['neuroticism']
    participants = {}
    for row in tables['survey']:
        person = _id(row['M2ID'])
        if person in participants:
            raise ValueError('duplicate survey person')
        family = row.get('M2FAMNUM')
        family = None if family is None or not np.isfinite(family) or family <= 0 else _id(family)
        participants[person] = (_trait(row[trait_field]), family)
    history = {}
    universe = set()
    for row in tables['diary']:
        person = _id(row['M2ID'])
        universe.add(person)
        day = contract.valid_code(row[fields['study_day']], range(1, 9), missing=())
        if day is None:
            continue
        entries = history.setdefault(person, {})
        if day in entries:
            raise ValueError('duplicate diary day')
        event = contract.occurrence([row[s['occurrence']] for s in fields['stressors']])
        decoded = {i:contract.valid_code(row[k], range(5)) for i,k in zip(ITEMS,fields['negative'])}
        feelings = [np.mean([decoded[i] for i in group]) if all(decoded[i] is not None for i in group)
                    else np.nan for group in GROUPS]
        entries[day] = event, feelings
    ids = sorted(p for p in history if p in participants and np.isfinite(participants[p][0]))
    scores = np.array([participants[p][0] for p in ids])
    families = [participants[p][1] for p in ids]
    panels = []
    for item in range(len(GROUPS)):
        halves = []
        for half in (0,1):
            record = {k:[] for k in ('b','L','S','n1')}
            for person in ids:
                values = ([], [])
                for day,(event,feelings) in history[person].items():
                    if (day > 4) == bool(half) and event is not None and np.isfinite(feelings[item]):
                        values[event].append(feelings[item])
                base, exposed = values
                level = np.mean(base) if base else np.nan
                record['n1'].append(len(exposed))
                record['L'].append(level)
                record['S'].append(np.std(base,ddof=1) if len(base)>1 else 0.)
                record['b'].append(np.mean(exposed)-level if exposed and base else np.nan)
            halves.append({k:np.array(v) for k,v in record.items()})
        panels.append(halves)
    return universe, ids, scores, families, panels


def estimates(tables, draws=2000):
    universe, ids, scores, families, panels = prepare(tables, 'M2')
    if len(universe)<11:
        raise SealedFailure(12,'Insufficient identified people')
    supports=[np.isfinite(a['b']) & np.isfinite(b['b']) for a,b in panels]
    # Original diary groups and their difference; all pairwise differences of
    # the individual unpleasant items. Codes are stable positions in the registry.
    contrasts=[(i,) for i in range(len(GROUPS))]
    contrasts+=list(combinations(range(len(ITEMS)),2))+[(len(ITEMS),len(ITEMS)+1)]
    catalog=[]
    family_numbers = {f:i for i,f in enumerate(sorted(set(families)-{None}))}
    rng = np.random.default_rng(2026112203)
    valid_family = np.array([f is not None for f in families],dtype=bool)
    # Whole-family multipliers are shared across all effects and differences.
    # Missing linkage withholds a branch if an otherwise eligible person lacks it.
    cluster=np.array([family_numbers.get(f,-1) for f in families],dtype=int)
    population=len(family_numbers)
    # Small draw blocks bound memory with the full original survey.
    output=[[] for _ in contrasts]
    masks=[np.logical_and.reduce([supports[i] for i in terms]) for terms in contrasts]
    eligible=[mask.sum()>=11 and np.all(valid_family[mask]) for mask in masks]
    for start in range(-1,draws,32):
        count=min(32,draws-start)
        weights=np.zeros((count,len(ids)),dtype=int)
        for j in range(count):
            if start+j<0:
                weights[j]=1
            elif population:
                multiples=np.bincount(rng.integers(population,size=population),minlength=population)
                weights[j,valid_family]=multiples[cluster[valid_family]]
        cache={}
        for k,(terms,mask) in enumerate(zip(contrasts,masks)):
            if not eligible[k]:
                continue
            effects=[]
            for idx in terms:
                cache_key=(idx,mask.tobytes())
                if cache_key not in cache:
                    halves=[{name:v[mask] for name,v in half.items()} for half in panels[idx]]
                    cache[cache_key]=effect(scores[mask],halves,weights[:,mask])
                effects.append(cache[cache_key])
            output[k].extend(effects[0] if len(effects)==1 else effects[0]-effects[1])
    for k,(mask,values) in enumerate(zip(masks,output),1):
        rows=[]
        if len(values)==draws+1 and np.isfinite(values).all():
            people=frozenset(p for p,keep in zip(ids,mask) if keep)
            low,high=np.quantile(values[1:],[.025,.975])
            rows=[Entry(dict(contrast=k,estimate=values[0],lower=low,upper=high,n=len(people)),people)]
        catalog.append((k,'contrast_'+str(k),rows))
    result,status=decide(catalog,universe)
    for row, mask, included, values in zip(status,masks,eligible,output):
        # Status n is always the number of identified diary participants.
        row.pop('reason')
        if mask.sum()<11:
            row['analysis_state']=2
        elif not included:
            row['analysis_state']=3
        elif not np.isfinite(values).all():
            row['analysis_state']=4
        else:
            row['analysis_state']=1 if row['kept'] else 5
    rows=[row for values in result.values() for row in values]
    return dict(table_status=status,**({'trait':rows} if rows else {}))


def run(mount, out, source_map, draws=2000):
    fields=contract.fields('M2')
    selections={'survey':['M2ID','M2FAMNUM',fields['traits']['neuroticism']],
                'diary':['M2ID',fields['study_day'],*fields['negative'],
                         *(s['occurrence'] for s in fields['stressors'])]}
    limit=sum(meta['bytes'] for meta in source_map['M2'].values())
    with TemporaryDirectory(prefix='sld3-') as tmp:
        wave,paths=take_snapshot(Path(mount),Path(tmp),source_map,limit)
        if wave!='M2':
            raise SealedFailure(11,'Unexpected source wave')
        tables=read_roles(paths,selections)
        first=estimates(tables,draws)
        repeat=estimates(read_roles(paths,selections),draws)
        if first!=repeat:
            raise SealedFailure(14,'Replay differs')
        return write_tables(out,first)
