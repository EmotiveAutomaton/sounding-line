"""Evaluator-owned training preparation for the constructed artifact comparators.

DESIGN CHECK: M01/C08/X01/X02; LESSONS 3--5. NULL: incomplete declared cohorts
or a nontraining parameter combination refuse preparation. ALTERNATIVE: every
selected whole source yields only allowlisted input prefixes and independently
recorded next actions/stops. No future-dependent evaluation cut is chosen here:
all recorded supervised training boundaries are used, with equal whole-unit fitting.

The library's declared coverage is the four artifact purposes, six existing laws,
and two existing residue regimes. Other goals/histories remain coverage challenges.
This prepares data, not a scientific launch or a held-out evaluation.
"""
from collections import Counter
import itertools

from .artifact_preparation import evidence
from .artifact_view import action_id
from .common import digest
from .recipes import POP, PURPOSES, SECONDARY_BY_ROLE, parameter_partition, sampled_world

LAWS = tuple(SECONDARY_BY_ROLE)+tuple(SECONDARY_BY_ROLE.values())
RESIDUES = ('none', 'habit_check')


def prepare(*, band, per_domain=4, maximum_indices=20000, view='artifact'):
    if type(band) is not int or band < 1000000 or type(per_domain) is not int or per_domain < 1:
        raise ValueError('explicit new construction band and positive cohort size required')
    if type(maximum_indices) is not int or maximum_indices < 1 or view not in ('artifact', 'process_record'):
        raise ValueError('invalid artifact training envelope')
    expected = set(itertools.product(LAWS, RESIDUES, PURPOSES, POP.DOMAINS))
    counts = Counter()
    rejected = Counter()
    records, units = [], []
    attempted = 0
    for index in range(maximum_indices):
        for domain in POP.DOMAINS:
            attempted += 1
            world = sampled_world(POP.pop_lid(index, domain, band), 'both')
            names = world['state']['names']
            cohort = (names['law'], names['residue'], world['goal_name'], domain)
            if cohort not in expected:
                rejected['outside_declared_cohorts'] += 1
                continue
            if counts[cohort] >= per_domain:
                rejected['cohort_filled'] += 1
                continue
            if parameter_partition(world) != 'training':
                rejected['nontraining_parameter_combination'] += 1
                continue
            events = world['trajectory']['steps']
            supervised = [(i, action_id(event)) for i, event in enumerate(events)]
            if world['trajectory']['stop_kind'] == 'hazard':
                supervised.append((len(events), 'stop'))
            if not supervised:
                rejected['no_recorded_supervised_target'] += 1
                continue
            unit = digest({'whole_training_world': world})
            if any(u['unit'] == unit for u in units):
                raise ValueError('duplicate constructed training source')
            for boundary, target in supervised:
                visible = evidence(world, events[:boundary], view)
                if target not in visible['support']:
                    raise ValueError('real recorded action omitted from public support')
                records.append({'unit': unit, 'evidence': visible, 'target': target,
                                'maker_group': names['law']+'|'+names['residue'], 'purpose_group': world['goal_name']})
            units.append({'unit': unit, 'lineage': world['lid'], 'cohort': list(cohort),
                          'parameter_partition': 'training', 'source_sha256': digest(world),
                          'recorded_actions': len(events), 'stop_kind': world['trajectory']['stop_kind']})
            counts[cohort] += 1
        if all(counts[c] == per_domain for c in expected):
            break
    if any(counts[c] != per_domain for c in expected):
        raise ValueError('declared artifact training cohorts incomplete within source budget')
    if attempted != len(units)+sum(rejected.values()):
        raise ValueError('artifact training attempt accounting mismatch')
    return {'records': records, 'units': units,
            'receipt': {'attempted_worlds': attempted, 'selected_worlds': len(units), 'excluded': dict(rejected),
                        'cohorts': [{'law': law, 'residue': residue, 'purpose': goal, 'domain': domain, 'units': counts[law,residue,goal,domain]}
                                    for law,residue,goal,domain in sorted(expected)],
                        'supervised_records': len(records), 'stop_records': sum(r['target'] == 'stop' for r in records),
                        'view': view, 'band': band, 'per_domain': per_domain,
                        'records_sha256': digest(records), 'unit_ledger_sha256': digest(units),
                        'meaning': 'training-only supervised boundaries; not outcome-selected evaluation units'}}
