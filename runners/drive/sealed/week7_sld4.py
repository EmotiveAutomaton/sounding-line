"""The SLD3 fit on the original roster with one substituted observed trait."""
from math import isfinite
from pathlib import Path
from tempfile import TemporaryDirectory

import mi_source_contract_v1 as contract
from mi_source_bridge_v1 import _trait
from week7_sld3 import estimates
from week7_mib1 import reconstruct, trait_rosters
from independent_release import Entry, decide
from joined_source import take_snapshot, read_roles
from week6_sealed_support_v1 import SealedFailure, write_tables


def substitute(tables, trait):
    fields=contract.fields('M2')['traits']
    neuro, other=fields['neuroticism'],fields[trait]
    # An additional trait cannot bring a person into the original SLD3 population.
    return dict(diary=tables['diary'],survey=[dict(row, **{neuro:row[other]}) for row in tables['survey']
                                             if isfinite(_trait(row[neuro]))])


def run(mount,out,source_map,published,trait,prior=None,draws=2000):
    if trait not in ('agreeableness','extraversion'):raise ValueError('Unexpected trait')
    spec=contract.fields('M2')
    selections={'survey':['M2ID','M2FAMNUM',*spec['traits'].values()],
                'diary':['M2ID',spec['study_day'],*spec['negative'],*(s['occurrence'] for s in spec['stressors'])]}
    limit=sum(meta['bytes'] for meta in source_map['M2'].values())
    with TemporaryDirectory(prefix='sld4-') as scratch:
        wave,paths=take_snapshot(Path(mount),Path(scratch),source_map,limit)
        if wave!='M2':raise SealedFailure(11,'Wrong joined wave')
        _,historic,groups=reconstruct(paths,published,False)
        if any(len(historic[k])!=published[k] for k in published):raise SealedFailure(14,'Historical count mismatch')
        original=read_roles(paths,selections)
        catalog=trait_rosters(original)
        known=[groups['survey'],*historic.values()]
        if prior:
            prior_rosters=trait_rosters(substitute(original,'agreeableness'))
            for key,count in prior.items():
                if key not in historic or len(prior_rosters[key])!=count:raise SealedFailure(14,'Earlier SLD4 roster mismatch')
                known.append(prior_rosters[key])
        def calculate(rows):
            substituted=substitute(rows,trait)
            # A wholly missing extra trait has no scientific output.
            if not any(isfinite(_trait(row[spec['traits']['neuroticism']])) for row in substituted['survey']):
                return {}
            rosters=trait_rosters(substituted)
            values=estimates(substituted,draws).get('trait',[])
            entries=[]
            for row in values:
                key='sld3/'+str(row['contrast'])
                if key not in published:continue
                if catalog[key]!=historic[key] or not rosters[key]<=historic[key] or len(rosters[key])!=row['n']:
                    raise SealedFailure(14,'Population changed')
                entries.append(Entry(row,rosters[key]))
            allowed,_=decide([(1,'trait',entries)],groups['diary'],known)
            return allowed
        first=calculate(original)
        if first!=calculate(read_roles(paths,selections)):raise SealedFailure(14,'Replay differs')
        if not first:raise SealedFailure(12,'Trait return withheld')
        return write_tables(out,first)

