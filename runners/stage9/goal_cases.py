"""Existing-goal intervention with fixed skill and an unchanged-goal deadline control.

DESIGN CHECK: T03/X01/X08/X11; LESSONS 3--5, CONTROLS 6--7.
NULL: absent familiar reusable restructuring, no utility-sign reversal or an already
tight deadline fails eligibility before any future is drawn. ALTERNATIVE: the same
pending operation remains executable while its symbolic purpose utility reverses;
the harder control changes only the deadline. Source conditioning is explicit and
is not the upstream realization gate. This does not establish human communicative
effects or infer that independently fitted coefficients identify true skill.
"""
import argparse
import copy
import time
from pathlib import Path
from .common import REPO, ROOT, Units, digest, file_hash, freeze, read, closure
from .construction import Replay, LAW, register
from .queue import inside, writer
from .revision_predictions import sources, reentry, finish
from .artifact_comparisons import validate_cases
from .training_jobs import cell_identity

GOALS = {'persuade': 'document', 'teach': 'explore', 'document': 'persuade', 'explore': 'teach'}


def eligibility(case):
    world = case['source_worlds'][0]
    replay = Replay(world, world['trajectory']['steps'][:case['requested_boundary']])
    old = replay.snapshot()
    goal = old['proximal_goal']['name_ref']
    if goal not in GOALS:
        raise ValueError('goal-transfer source outside supported purpose family')
    changed = copy.deepcopy(replay)
    changed.goal_name = changed.goal_last = GOALS[goal]
    # A purpose owns this work's remaining inventory. Reassigning its ownership
    # prevents the existing next_goal rule from silently reinstating the old goal.
    for action in changed.pending + changed.inventory:
        action['goal_owner'] = GOALS[goal]
    new = changed.snapshot()
    for key in ('external_context', 'belief_state', 'expertise_law', 'history_residue', 'persistent_tendency'):
        if old[key] != new[key]:
            raise ValueError('goal intervention changed a held-fixed factor')
    if replay.steps != changed.steps or replay.done != changed.done or replay.last_type != changed.last_type:
        raise ValueError('goal intervention rewrote historical execution')
    harder = copy.deepcopy(replay)
    harder.c_ext, harder.belief = LAW.apply_change(harder.c_ext, harder.belief, 'deadline_imposed')
    hard = harder.snapshot()
    if hard['proximal_goal'] != old['proximal_goal'] or harder.steps != replay.steps:
        raise ValueError('harder-task control changed the goal or past')
    legal = {LAW.action_id(a): a for a in replay.legal_actions()}
    reusable = [LAW.action_id(a) for a in replay.pending if a['type'] == 'restructure'
                and legal.get(LAW.action_id(a), {}).get('outcome') == 'done'
                and LAW.action_id(a) in old['subjective_action_space']]
    predicates = {'familiar': any(e['type'] == 'restructure' and e['outcome'] == 'done'
                                 for w in case['source_worlds'][1:] for e in w['trajectory']['steps']),
                  'reusable': bool(reusable),
                  'utility_sign_reversal': old['proximal_goal']['utility']['restructure'] *
                                           new['proximal_goal']['utility']['restructure'] < 0,
                  'deadline_was_loose': old['external_context']['deadline'] == 'loose' and
                                        old['maker_context']['perceived_deadline'] == 'loose',
                  'deadline_has_progress_to_affect': bool(replay.done)}
    if reusable and any(changed.probabilities().get(a, 0) <= 0 for a in reusable):
        raise ValueError('goal reversal made the reusable operation unavailable')
    return {'eligible': all(predicates.values()), 'conditions': predicates,
            'old_purpose': goal, 'new_purpose': GOALS[goal], 'reusable_actions': reusable}, changed, harder


def counterfactual(case, condition):
    if condition not in ('goal', 'harder'):
        raise ValueError('unknown goal-transfer condition')
    check, changed, harder = eligibility(case)
    if not check['eligible']:
        raise ValueError('source cannot realize goal reversal and its harder-task control')
    replay = changed if condition == 'goal' else harder
    oracle = replay.probabilities()
    seed = int(digest({'goal_transfer_future_v1': case['source_worlds'][0]['lid'],
                       'boundary': case['requested_boundary']})[:16], 16)
    events, stopped = replay.continue_teacher(seed, max_events=case['requested_boundary']+1)
    if len(events) != int(not stopped):
        raise ValueError('goal-transfer future did not execute exactly one opportunity')
    target = 'stop' if stopped else LAW.action_id(events[0])
    support = case['views']['process_record']['support']
    if target not in support or set(oracle)-set(support) or oracle.get(target, 0) <= 0:
        raise ValueError('goal-transfer future outside the complete offered support')
    if condition == 'goal' and any(e['goal'] != check['new_purpose'] for e in events):
        raise ValueError('executed goal reverted to the old commission')
    return {'eligibility': check, 'condition': condition, 'target': target, 'oracle': oracle,
            'announced_purpose': check['new_purpose'] if condition == 'goal' else None,
            'deadline': 'unchanged' if condition == 'goal' else 'tight',
            'seed': seed, 'executed_events': events, 'stopped': stopped,
            'meaning': 'existing purpose-utility reversal with reusable operation, or unchanged-goal deadline control'}


def prepare(directory, source, role, condition, pilot_offset=0):
    start, cpu = time.monotonic(), time.process_time()
    register()
    directory, source = inside(directory), inside(source)
    namespace = ROOT/'private'/('goal-case-pilots' if role == 'pilot' else 'scientific-goal-cases')
    if (role not in ('pilot', 'development', 'discovery') or condition not in ('goal', 'harder')
            or not directory.is_relative_to(namespace) or pilot_offset not in (0, 1)
            or role != 'pilot' and pilot_offset != 0):
        raise ValueError('undeclared goal-transfer source scope or subset')
    done, source_identity = read(source/'COMPLETE.json'), read(source/'IDENTITY.json')
    if (done.get('accepted') is not True or done.get('construction_only') is not True or done['role'] != role
            or done['identity_sha256'] != digest(source_identity)
            or closure([REPO/p for p in done['outputs']['files']]) != done['outputs']):
        raise ValueError('ordinary source pool is incomplete, changed or failed realization')
    candidates = read(source/'CASES.json')
    validate_cases(candidates, role)
    if role != 'pilot' and (source_identity['per_cohort'] != 72 or len(candidates) != 6912):
        raise ValueError('goal transfer requires its one declared complete 6912-series pool')
    screened, groups = [], {}
    ordered = sorted(candidates, key=lambda c: digest({'goal_transfer_selection_v1': c['source_worlds'][0]['lid'],
                                                     'boundary': c['requested_boundary']}))
    for case in ordered:
        check, _, _ = eligibility(case)
        group = case['private_factors']['domain'] if role == 'pilot' else (
            case['private_factors']['domain']+'|'+case['private_factors']['purpose'])
        screened.append({'unit': case['unit'], 'group': group, **check})
        groups.setdefault(group, [])
        if check['eligible']:
            groups[group].append(case)
    expected_groups, per_group = (2, 1) if role == 'pilot' else (8, 24)
    selected = [case for group in sorted(groups) for case in groups[group][pilot_offset:pilot_offset+per_group]]
    accepted = len(groups) == expected_groups and len(selected) == expected_groups*per_group
    selected = [{**case, 'goal_transfer': counterfactual(case, condition)} for case in selected]
    identity = {'cell_identity': cell_identity(), 'operation': 'goal-transfer-cases-v1', 'role': role,
                'scope': 'pilot' if role == 'pilot' else 'scientific', 'condition': condition,
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
                      eligible_counts={k: len(v) for k, v in groups.items()}, condition=condition,
                      scientific_admission=False, disposition='DESCRIPTIVE' if accepted else 'IMPLEMENTATION INVALID')


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    for name in ('output', 'source'):
        p.add_argument('--'+name, type=Path, required=True)
    p.add_argument('--role', choices=('pilot', 'development', 'discovery'), required=True)
    p.add_argument('--condition', choices=('goal', 'harder'), required=True)
    p.add_argument('--pilot-offset', type=int, default=0)
    a = p.parse_args()
    prepare(a.output, a.source, a.role, a.condition, a.pilot_offset)
