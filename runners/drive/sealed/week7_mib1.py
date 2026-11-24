"""Select an authenticated released population inside the wave-two job."""
from itertools import combinations
from pathlib import Path
from tempfile import TemporaryDirectory

import numpy as np
import analysis_v1 as analysis
import aggregate_register_v1 as register
import mi_source_contract_v1 as contract
import daily_bank
import week7_sld3 as trait
from bm_numeric import numerical_outputs
from family_draws import family_index
from independent_release import Entry, decide
from joined_source import take_snapshot
from panels import plan
from science_entry import inspect_tables, read_available, MAX_PRIVATE_BYTES
from sealed_io_v1 import selected_columns
from table_support import required_columns, supported_columns, EXTRAS
from week6_sealed_support_v1 import SealedFailure, write_tables
from week7_mib_roster import largest_released_roster

NO_ROSTER = 32


def trait_rosters(tables):
    _, ids, _, _, panels = trait.prepare(tables, 'M2')
    supports = [np.isfinite(a['b']) & np.isfinite(b['b']) for a,b in panels]
    contrasts = [(i,) for i in range(len(panels))]
    contrasts += list(combinations(range(len(trait.ITEMS)),2))
    contrasts += [(len(trait.ITEMS), len(trait.ITEMS)+1)]
    return {'sld3/'+str(index):frozenset(p for p,yes in zip(ids,np.logical_and.reduce([supports[i] for i in terms])) if yes)
            for index,terms in enumerate(contrasts,1)}


def reconstruct(paths, published, reference):
    fields = {role:set(selected_columns('M2_'+part,contract.fields)) for role,part in [('diary','P2'),('survey','P1')]}
    for branch in EXTRAS:
        for role,cols in required_columns('M2',branch).items():
            fields[role].update(cols)
    fields['survey'].add('M2FAMNUM')
    fields = {role:sorted(names) for role,names in fields.items()}
    _,measured,groups = inspect_tables({'M2':paths},{'M2':fields},'M2')
    enabled = set(supported_columns(measured,'M2'))
    branches = tuple(k for k in register.BRANCHES if k in enabled)
    tables = read_available(paths,fields,measured['M2'])
    panels, counts = plan({'M2':tables},'M2',reference,branches,measured)
    rosters = {'count/'+str(i):counts[name] for i,name in enumerate(register.count_names(),1) if name in counts}
    for j,branch in enumerate(register.BRANCHES,1):
        if branch not in panels:continue
        members, required = analysis.groups_for(panels[branch],branch)
        roster = members.intersection(*required)
        for index in range(1,len(register.columns(branch))+1):
            rosters[f'branch/{j}/{index}']=roster
    if any(k.startswith('nt1/') for k in published):
        daily = daily_bank.plan(paths)
        rosters['nt1/exposure']=daily['exposed']
        if daily['panel'] is not None:
            for j in range(1,8):
                rosters[f'nt1/model/{j}']=set(daily['panel']['ids'])
    if any(k.startswith('sld3/') for k in published):
        rosters.update(trait_rosters(tables))
    return panels, {k:frozenset(rosters[k]) for k in published}, groups['M2']


def bind(published, rosters, panels, branch):
    if branch not in panels:raise SealedFailure(11,'Required variables unavailable')
    people = panels[branch]
    contributors, required = analysis.groups_for(people,branch)
    selected = largest_released_roster(published,rosters,contributors.intersection(*required))
    if selected is None:
        raise SealedFailure(NO_ROSTER,'No eligible released roster')
    key, roster = selected
    kept = [p for p in people if p['id'] in roster]
    actual, related = analysis.groups_for(kept,branch)
    if actual!=roster or any(v!=roster for v in related):
        raise SealedFailure(14,'Fit population differs')
    return key, roster, kept, related


def run(mount, out, source_map, published, branch='MI1'):
    size=sum(v['bytes'] for v in source_map['M2'].values())
    if size>MAX_PRIVATE_BYTES:raise SealedFailure(14,'Source exceeds bound')
    with TemporaryDirectory(prefix='mib-') as tmp:
        wave,paths=take_snapshot(Path(mount),Path(tmp),source_map,size)
        if wave!='M2':raise SealedFailure(11,'Wrong source wave')
        first,rosters,groups=reconstruct(paths,published,False)
        second,others,replica=reconstruct(paths,published,True)
        if rosters!=others or groups!=replica:raise SealedFailure(14,'Historical population replay differs')
        key,roster,people,required=bind(published,rosters,first,branch)
        key2,roster2,replay,related=bind(published,others,second,branch)
        if (key,roster,required)!=(key2,roster2,related):raise SealedFailure(14,'Selection replay differs')
        family=family_index(paths['survey'])
        tables=numerical_outputs({branch:(people,replay,roster,required)},family,family_index(paths['survey']))
        primary_parameters={j for j,(_,role,_) in enumerate(register.columns(branch),1) if role=='primary'}
        tables={name:[row for row in rows if row['parameter'] in primary_parameters] for name,rows in tables.items()}
        known=[groups['survey'],*rosters.values()]
        catalog=[]
        for j,(name,rows) in enumerate(sorted(tables.items()),1):
            catalog.append((j,name,[Entry(row,roster,tuple(required)) for row in rows]))
        allowed,_=decide(catalog,groups['diary'],known)
        if not allowed:raise SealedFailure(12,'Release held')
        return write_tables(out,allowed)


