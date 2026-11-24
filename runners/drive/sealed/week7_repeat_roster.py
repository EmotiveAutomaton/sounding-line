"""MIB2 and DFB1 on an eligible previously released cohort.

DESIGN CHECK. Select by authenticated membership, greatest size, and the
frozen tie rule. Equal cardinalities cannot establish identical membership.
No eligible roster returns fixed code 32 with an empty output directory.
All comparisons, source decoding, family draws and release checks stay sealed.
"""
from pathlib import Path
from tempfile import TemporaryDirectory
import analysis_v1 as analysis
import argument_bank
import argument_panel
from bm_numeric import numerical_outputs
from family_draws import family_index
from independent_release import Entry, decide
from joined_source import take_snapshot
from science_entry import MAX_PRIVATE_BYTES
from week6_sealed_support_v1 import SealedFailure, write_tables
from week7_mib1 import reconstruct, NO_ROSTER
from week7_mib3 import latest_trait_rosters
from week7_mib_roster import largest_released_roster


def choose(catalog, eligible):
    counts={key:len(value) for key,value in catalog.items()}
    selected=largest_released_roster(counts,catalog,eligible)
    if selected is None:raise SealedFailure(NO_ROSTER,'No eligible released roster')
    return selected[1]


def mi_tables(first, second, catalog, families, other_families):
    if 'MI2' not in first or 'MI2' not in second:raise SealedFailure(11,'Primary input unavailable')
    actual=[]
    for panel in (first,second):
        ids,sets=analysis.groups_for(panel['MI2'],'MI2')
        actual.append(choose(catalog,ids.intersection(*sets)))
    if actual[0]!=actual[1]:raise SealedFailure(14,'Primary membership differs')
    roster=actual[0]
    analyses={}
    for branch in ('MI2-reliability','MI2','MI2-traits'):
        if branch not in first or branch not in second:continue
        aligned=[]
        for panel in (first,second):
            people=[p for p in panel[branch] if p['id'] in roster]
            contributors,required=analysis.groups_for(people,branch)
            aligned.append((people,contributors,required))
        left,right=aligned
        if left[1:]!=right[1:]:raise SealedFailure(14,'Contributing sets differ')
        if left[1]==roster and all(g==roster for g in left[2]):
            analyses[branch]=(left[0],right[0],roster,left[2])
    return roster,numerical_outputs(analyses,families,other_families)


def argument_tables(paths,catalog,families,other_families):
    plan=argument_panel.support_plan(paths)
    # Exposure counts are computed before outcome projection, as in amendment BF.
    argument_panel.support_summary(plan)
    data,replica=argument_panel.outcome_plan(paths,plan)
    groups,_=argument_bank.contributors(data);check,_=argument_bank.contributors(replica)
    if groups!=check:raise SealedFailure(14,'Argument contributors differ')
    roster=choose(catalog,groups[argument_bank.WITHIN])
    baselines,days=plan
    limited=({p:v for p,v in baselines.items() if p in roster},{k:v for k,v in days.items() if k[0] in roster})
    first={p:data[p] for p in roster};second={p:replica[p] for p in roster}
    values=argument_bank.run(limited,first,second,families,other_families)
    permitted={}
    # Never imply that a secondary with missing same-day ratings used the primary cohort.
    for name,rows in values.items():
        kept=[r for r in rows if r['n']==len(roster)]
        if kept:permitted[name]=kept
    return roster,permitted


def run(mount,out,mapping,published,latest,card):
    limit=sum(v['bytes'] for v in mapping['M2'].values())
    if limit>MAX_PRIVATE_BYTES:raise SealedFailure(14,'Source exceeds bound')
    with TemporaryDirectory(prefix='week7-repeat-') as tmp:
        wave,paths=take_snapshot(Path(mount),Path(tmp),mapping,limit)
        if wave!='M2':raise SealedFailure(11,'Wrong wave')
        first,rosters,groups=reconstruct(paths,published,False)
        second,independent,other=reconstruct(paths,published,True)
        if rosters!=independent or groups!=other or any(len(rosters[k])!=n for k,n in published.items()):
            raise SealedFailure(14,'Published roster or count differs')
        newer=latest_trait_rosters(paths,latest)
        catalog={**rosters,**newer}
        families=family_index(paths['survey']);check=family_index(paths['survey'])
        if families!=check:raise SealedFailure(14,'Family map differs')
        if card=='MIB2':roster,rows=mi_tables(first,second,catalog,families,check)
        elif card=='DFB1':roster,rows=argument_tables(paths,catalog,families,check)
        else:raise ValueError('Unregistered study')
        if any(row['n']!=len(roster) for values in rows.values() for row in values):
            raise SealedFailure(14,'Contributing population changed')
        tables=[(index,name,[Entry(row,roster) for row in values]) for index,(name,values) in enumerate(sorted(rows.items()),1)]
        allowed,_=decide(tables,groups['diary'],[groups['survey'],*catalog.values()])
        if not allowed:raise SealedFailure(12,'Release withheld')
        return write_tables(out,allowed)

