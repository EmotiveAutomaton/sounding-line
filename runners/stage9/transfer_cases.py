"""Conditional tool-removal sources with an independently executed future.

DESIGN CHECK: T01/X01/X08/X11/X12; LESSONS 3--5, CONTROLS 6.
NULL: absent/unfamiliar tools or missing useful alternatives cannot realize a ban
comparison. ALTERNATIVE: eligibility is fixed from the past, goal/law/history stay
unchanged and actual execution removes the means before drawing the new target.
The upstream ordinary source realization gate remains .75 in each domain/purpose;
conditional eligibility is separately reported, never relabeled as realization.
Scientific cohorts require 192 eligible independent units from one fixed complete
1152-series pool, balanced by domain/purpose; shortfall refuses, no seed replacement.
No interpretation of real-world effect follows from symbolic goal utility.
"""
import argparse
import copy
import time
from collections import Counter
from pathlib import Path

from .common import REPO, ROOT, Units, digest, file_hash, freeze, read, closure
from .construction import Replay, LAW, register
from .queue import inside, writer
from .revision_predictions import sources, reentry, finish
from .artifact_comparisons import validate_cases
from .training_jobs import cell_identity


def eligibility(case):
    world = case['source_worlds'][0]
    replay = Replay(world, world['trajectory']['steps'][:case['requested_boundary']])
    before = replay.snapshot()
    current = replay.probabilities()
    changed = copy.deepcopy(replay)
    changed.c_ext, changed.belief = LAW.apply_change(changed.c_ext, changed.belief, 'library_withdrawn')
    after = changed.snapshot()
    if (any(before[k] != after[k] for k in ('proximal_goal', 'expertise_law', 'history_residue'))
            or replay.steps != changed.steps):
        raise ValueError('tool removal changes goal, law, habit or recorded history')
    future = changed.probabilities()
    banned = {LAW.action_id(a) for a in replay.pending if 'library' in a['requires']}
    if any(future.get(k, 0) != 0 for k in banned):
        raise ValueError('withdrawn tool remains subjectively available')
    predicates = {
        'available': bool(replay.c_ext['tools']['library']),
        'could_choose': any(current.get(k, 0) > 0 for k in banned),
        'familiar': any(e['type'] == 'cite' and e['outcome'] == 'done'
                        for w in case['source_worlds'][1:] for e in w['trajectory']['steps']),
        'useful_alternative': any(LAW.action_id(a) not in banned and future.get(LAW.action_id(a), 0) > 0
                                 and before['proximal_goal']['utility'].get(a['type'], 0) > 0
                                 for a in changed.pending)}
    return {'eligible': all(predicates.values()), 'conditions': predicates}, changed


def counterfactual(case):
    check, changed = eligibility(case)
    if not check['eligible']:
        raise ValueError('source is ineligible for the declared familiar-tool ban')
    oracle = changed.probabilities()
    seed = int(digest({'tool_removal_future_v1': case['source_worlds'][0]['lid'],
                       'boundary': case['requested_boundary']})[:16], 16)
    events, stopped = changed.continue_teacher(seed, max_events=case['requested_boundary']+1)
    if len(events) != int(not stopped):
        raise ValueError('tool-removal future did not execute the single declared opportunity')
    target = 'stop' if stopped else LAW.action_id(events[0])
    support = case['views']['process_record']['support']
    if target not in support or set(oracle)-set(support) or oracle.get(target, 0) <= 0:
        raise ValueError('executed tool-removal future is outside the common support')
    return {'eligibility': check, 'announcement': 'library_withdrawn', 'target': target,
            'oracle': oracle, 'executed_events': events, 'stopped': stopped, 'seed': seed,
            'meaning': 'same symbolic goal and history; observed loss of library before a new future draw'}


def prepare(directory, source, role, pilot_offset=0):
    start, cpu = time.monotonic(), time.process_time()
    register()
    directory, source = inside(directory), inside(source)
    namespace = ROOT/'private'/('transfer-case-pilots' if role == 'pilot' else 'scientific-transfer-cases')
    if (role not in ('pilot', 'development', 'discovery') or not directory.is_relative_to(namespace)
            or pilot_offset not in (0, 1) or role != 'pilot' and pilot_offset != 0):
        raise ValueError('undeclared transfer source scope or subset')
    done, source_identity = read(source/'COMPLETE.json'), read(source/'IDENTITY.json')
    if (done.get('accepted') is not True or done.get('construction_only') is not True or done['role'] != role
            or done['identity_sha256'] != digest(source_identity)
            or closure([REPO/p for p in done['outputs']['files']]) != done['outputs']):
        raise ValueError('ordinary source pool is incomplete, changed or failed realization')
    candidates = read(source/'CASES.json')
    validate_cases(candidates, role)
    if role != 'pilot' and (source_identity['per_cohort'] != 12 or len(candidates) != 1152):
        raise ValueError('scientific transfer requires its one declared complete 1152-series source pool')
    screened, groups = [], {}
    ordered = sorted(candidates, key=lambda c: digest({'tool_removal_selection_v1': c['source_worlds'][0]['lid'],
                                                     'boundary': c['requested_boundary']}))
    for case in ordered:
        check, _ = eligibility(case)
        group = case['private_factors']['domain'] if role == 'pilot' else (
            case['private_factors']['domain']+'|'+case['private_factors']['purpose'])
        screened.append({'unit': case['unit'], 'group': group, **check})
        groups.setdefault(group, [])
        if check['eligible']:
            groups[group].append(case)
    expected_groups, per_group = (2, 1) if role == 'pilot' else (8, 24)
    selected = [case for group in sorted(groups) for case in groups[group][pilot_offset:pilot_offset+per_group]]
    accepted = len(groups) == expected_groups and len(selected) == expected_groups*per_group
    # Only after the complete selection is fixed do new counterfactual outcomes exist.
    selected = [{**case, 'transfer': counterfactual(case)} for case in selected]
    identity = {'cell_identity': cell_identity(), 'operation': 'tool-removal-cases-v1', 'role': role,
                'scope': 'pilot' if role == 'pilot' else 'scientific',
                'source': sources(), 'source_pool': str(source), 'source_complete_sha256': file_hash(source/'COMPLETE.json'),
                'pilot_offset': pilot_offset, 'per_group': per_group, 'expected_groups': expected_groups,
                'selected_units': [c['unit'] for c in selected], 'selection_uses_future': False}
    with writer(directory):
        Units(directory, identity)
        prior = reentry(directory, identity)
        if prior is not None:
            return prior
        freeze(directory/'CASES.json', selected)
        freeze(directory/'ELIGIBILITY.json', screened)
        return finish(directory, identity, start, cpu, ['CASES.json', 'ELIGIBILITY.json'],
                      accepted=accepted, role=role, construction_only=True, selected_series=len(selected),
                      requested_series=expected_groups*per_group, source_candidates=len(candidates),
                      eligible_counts={k: len(v) for k, v in groups.items()},
                      selected_laws=dict(Counter(c['private_factors']['law'] for c in selected)),
                      scientific_admission=False, disposition='DESCRIPTIVE' if accepted else 'IMPLEMENTATION INVALID')


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    for name in ('output', 'source'):
        p.add_argument('--'+name, type=Path, required=True)
    p.add_argument('--role', choices=('pilot', 'development', 'discovery'), required=True)
    p.add_argument('--pilot-offset', type=int, default=0)
    a = p.parse_args()
    prepare(a.output, a.source, a.role, a.pilot_offset)
