"""Re-estimate the uncertainty of the released MI3 point on its original cohort.

DESIGN CHECK (LESSONS 3–5). Missing family links receive distinct singleton
clusters. Known relatives share a cluster. A changed point, roster or source
invalidates the reconstruction. The standard joint release decision governs
the only registered row. No identifiers or membership vectors leave the job.
"""
from math import isclose
from pathlib import Path
from tempfile import TemporaryDirectory

import analysis_v1 as analysis
import mi_source_contract_v1 as contract
from bm_numeric import numerical_outputs
from family_draws import family_index
from independent_release import Entry, decide
from joined_source import take_snapshot, read_roles
from science_entry import MAX_PRIVATE_BYTES
from week6_sealed_support_v1 import SealedFailure, write_tables
from week7_mib1 import reconstruct, trait_rosters
from week7_sld4 import substitute


def family_labels(index, roster):
    if index is None or not roster.issubset(index):
        raise SealedFailure(11, 'Family field or matching survey record unavailable')
    # Verified family numbers are positive integers. Negative labels cannot collide.
    return {person: index[person] or -int(person) for person in roster}


def latest_trait_rosters(paths, releases):
    if not releases:
        return {}
    spec = contract.fields('M2')
    fields = {'survey': ['M2ID', 'M2FAMNUM', *spec['traits'].values()],
              'diary': ['M2ID', spec['study_day'], *spec['negative'],
                        *(s['occurrence'] for s in spec['stressors'])]}
    tables = read_roles(paths, fields)
    groups = {}
    for trait, counts in releases.items():
        if trait not in ('agreeableness','extraversion'):
            raise SealedFailure(14, 'Unregistered trait release')
        rosters = trait_rosters(substitute(tables, trait))
        for key, count in counts.items():
            if key not in rosters or len(rosters[key]) != count:
                raise SealedFailure(14, 'Released trait count differs')
            groups[trait+'/'+key] = rosters[key]
    return groups


def run(mount, out, mapping, published, releases, previous_point):
    size = sum(v['bytes'] for v in mapping['M2'].values())
    if size > MAX_PRIVATE_BYTES:
        raise SealedFailure(14,'Source exceeds bound')
    with TemporaryDirectory(prefix='mib3-') as tmp:
        wave, paths = take_snapshot(Path(mount), Path(tmp), mapping, size)
        if wave != 'M2':
            raise SealedFailure(11,'Wrong wave')
        first, historic, groups = reconstruct(paths, published, False)
        replay, other, repeated = reconstruct(paths, published, True)
        if historic != other or groups != repeated or any(len(historic[k])!=n for k,n in published.items()):
            raise SealedFailure(14,'Released roster reconstruction differs')
        roster = historic['branch/5/1']
        people, check = first['MI3'], replay['MI3']
        for records in (people,check):
            contributors, required = analysis.groups_for(records,'MI3')
            if contributors != roster or any(g!=roster for g in required):
                raise SealedFailure(14,'Original contributing people differ')
        tables = numerical_outputs({'MI3':(people,check,roster,required)},
                                   family_labels(family_index(paths['survey']),roster),
                                   family_labels(family_index(paths['survey']),roster))
        rows = [(name,row) for name,values in tables.items() for row in values if row['parameter']==1]
        if len(rows)!=1:
            raise SealedFailure(14,'Incorrect number of registered estimates')
        name, row = rows[0]
        if row['n']!=len(roster) or row.get('estimate') is None or not isclose(row['estimate'],previous_point,abs_tol=1e-9,rel_tol=1e-8):
            raise SealedFailure(14,'Released point differs')
        known = [groups['survey'],*historic.values(),*latest_trait_rosters(paths,releases).values()]
        allowed,_ = decide([(1,name,[Entry(row,roster)])],groups['diary'],known)
        if not allowed:
            raise SealedFailure(12,'Release withheld')
        return write_tables(out,allowed)


