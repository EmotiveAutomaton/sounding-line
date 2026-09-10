"""Creation-time freedom/pressure cross; stopped and short artifacts remain visible.

DESIGN CHECK: M06/X01/X02/X05/X08/X11; LESSONS 3--5, CONTROLS 6--7.
NULL: unchanged productive options or ineffective deadline pressure refuses source
realization. ALTERNATIVE: existing library/deadline interventions change available
operations versus stopping pressure, keeping initial maker, goal, shape and inventory
fixed. Observe up to three executed actions without conditioning on reaching that
cut. A separate unstarted work supplies one common future for every creation/view
condition. Source realization is checked before drawing that future or reading it.
This is a bounded visibility surface; no event-count authorship ratio is defined.
"""
import argparse
import copy
import time
from pathlib import Path

from .artifact_preparation import evidence
from .common import REPO, ROOT, Units, closure, digest, file_hash, freeze, read
from .construction import LAW, Replay, register
from .artifact_comparisons import validate_cases
from .queue import inside, writer
from .revision_predictions import sources, reentry, finish
from .training_jobs import cell_identity

CONDITIONS = ('restricted|loose', 'restricted|tight', 'expanded|loose', 'expanded|tight')
MAXIMUM_ACTIONS = 3


def initial_world(base):
    world = {k: copy.deepcopy(base[k]) for k in ('lid', 'domain', 'doc', 'inventory', 'state', 'shape', 'goal_name')}
    world['trajectory'] = {'changes': []}
    return world


def construct(case):
    register()
    if len(case['source_worlds']) < 2:
        raise ValueError('bounded creation needs a distinct earlier and target work')
    target, base = (initial_world(w) for w in case['source_worlds'][:2])
    if digest({k: target[k] for k in ('domain', 'doc', 'inventory', 'state', 'shape')}) == digest({k: base[k] for k in ('domain', 'doc', 'inventory', 'state', 'shape')}):
        raise ValueError('earlier creation duplicates the target work')
    seed = int(digest({'constraint_creation_v1': base['lid']})[:16], 16)
    worlds, observations, realization, views = {}, {}, {}, {}
    for condition in CONDITIONS:
        freedom, pressure = condition.split('|')
        world = copy.deepcopy(base)
        context, belief = world['state']['external_context'], world['state']['belief_state']
        context, belief = LAW.apply_change(context, belief, 'library_arrives' if freedom == 'expanded' else 'library_withdrawn')
        context, belief = LAW.apply_change(context, belief, 'deadline_imposed' if pressure == 'tight' else 'deadline_lifted')
        world['state'].update(external_context=context, belief_state=belief,
            maker_context=LAW.maker_context(context, belief, world['state']['expertise_law']))
        for field in ('expertise_law', 'proximal_goal', 'history_residue', 'persistent_tendency'):
            if world['state'][field] != base['state'][field]:
                raise ValueError('creation intervention changed the maker or purpose')
        replay = Replay(world); state = replay.snapshot()
        productive = sorted(LAW.action_id(a) for a in replay.legal_actions()
                            if a['outcome'] == 'done' and LAW.action_id(a) in state['subjective_action_space'])
        events, stopped = replay.continue_teacher(seed, max_events=MAXIMUM_ACTIONS)
        if len(events) > MAXIMUM_ACTIONS or (stopped == (len(events) == MAXIMUM_ACTIONS)):
            raise ValueError('source stop and censoring horizon disagree')
        observed_stop = True if stopped else None
        worlds[condition] = world
        observations[condition] = {'events': events, 'observed_stop': observed_stop}
        realization[condition] = {'initial_productive': productive,
            'initial_subjective': state['subjective_action_space'], 'observed_actions': len(events),
            'visible_marks': sum(e['outcome'] == 'done' for e in events), 'stopped_before_budget': stopped}
        for view in ('artifact', 'process_record'):
            views[view+'|'+condition] = evidence(target, [], view, [(world, events, observed_stop)])
    freedom_realized = all(set(realization['restricted|'+p]['initial_productive']) < set(realization['expanded|'+p]['initial_productive'])
                          for p in ('loose', 'tight'))
    pressure_checks = {}
    for freedom in ('restricted', 'expanded'):
        lo, hi = (freedom+'|'+p for p in ('loose', 'tight'))
        if any(realization[lo][k] != realization[hi][k] for k in ('initial_productive', 'initial_subjective')):
            raise ValueError('deadline pressure changes the initial action set')
        # Same available, positive first action in both deadlines. This verifies
        # causal stopping pressure independently of the sampled creation's length.
        probe = Replay(worlds[lo]); first = next((a for a in probe.legal_actions()
            if a['outcome'] == 'done' and probe.probabilities().get(LAW.action_id(a), 0) > 0), None)
        hazards = {}
        if first is not None:
            for condition in (lo, hi):
                probe = Replay(worlds[condition]); probe.apply(first)
                hazards[condition] = probe.probabilities()['stop']
        pressure_checks[freedom] = {'hazards_after_common_first_action': hazards,
            'realized': bool(hazards) and hazards[hi] > hazards[lo]}
    if not freedom_realized or not all(p['realized'] for p in pressure_checks.values()):
        raise ValueError('source cannot realize independent freedom and stopping pressure')
    # Future sampling is last and cannot select the creation, its length or view.
    replay = Replay(target); oracle = replay.probabilities()
    future_seed = int(digest({'constraint_target_v1': target['lid']})[:16], 16)
    future, stopped = replay.continue_teacher(future_seed, max_events=1)
    truth = 'stop' if stopped else LAW.action_id(future[0])
    support = next(iter(views.values()))['support']
    if truth not in support or set(oracle) - set(support) or oracle.get(truth, 0) <= 0:
        raise ValueError('separate target future outside complete public support')
    return {'maximum_actions': MAXIMUM_ACTIONS, 'views': views, 'target': truth,
        'future_event': future, 'future_stopped': stopped, 'oracle': oracle,
        'creation_seed': seed, 'future_seed': future_seed, 'realization': realization,
        'pressure_checks': pressure_checks, 'freedom_realized': freedom_realized,
        'source_template_sha256': digest([{k:w[k] for k in ('domain','doc','inventory','state','shape')} for w in (target,base)]),
        'scope': 'one bounded earlier creation; independent common target; no conditioning on realized length'}


def prepare(directory, source, role, pilot_offset=0):
    start, cpu = time.monotonic(), time.process_time(); register()
    directory, source = inside(directory), inside(source)
    namespace = ROOT/'private'/('constraint-case-pilots' if role == 'pilot' else 'scientific-constraint-cases')
    if (role not in ('pilot','development','discovery') or not directory.is_relative_to(namespace)
            or pilot_offset not in (0,1) or role != 'pilot' and pilot_offset):
        raise ValueError('undeclared bounded creation source scope')
    done, own = read(source/'COMPLETE.json'), read(source/'IDENTITY.json')
    if (done.get('accepted') is not True or done.get('construction_only') is not True or done['role'] != role
            or done['identity_sha256'] != digest(own)
            or closure([REPO/p for p in done['outputs']['files']]) != done['outputs']):
        raise ValueError('ordinary source pool incomplete, changed or failed realization')
    candidates = read(source/'CASES.json'); validate_cases(candidates, role)
    if role != 'pilot' and (own['per_cohort'] != 2 or len(candidates) != 192):
        raise ValueError('bounded creation requires its full declared 192-series scientific pool')
    groups = {}
    for case in sorted(candidates, key=lambda c:digest({'constraint_selection_v1':c['source_worlds'][0]['lid']})):
        group = case['private_factors']['domain'] if role == 'pilot' else case['private_factors']['domain']+'|'+case['private_factors']['purpose']
        groups.setdefault(group, []).append(case)
    expected_groups, per_group = (2,1) if role == 'pilot' else (8,24)
    assigned = [c for group in sorted(groups) for c in groups[group][pilot_offset:pilot_offset+per_group]]
    selected, realization = [], []
    # Selection is fixed before construction. A failed assigned case stays an
    # implementation failure; there is no replacement, length filter or seed search.
    for case in assigned:
        try:
            cf = construct(case)
        except ValueError as exc:
            realization.append({'unit':case['unit'], 'realized':False, 'reason':str(exc)})
        else:
            selected.append({**case, 'constraint_creation':cf})
            realization.append({'unit':case['unit'], 'realized':True, 'conditions':cf['realization'], 'pressure_checks':cf['pressure_checks']})
    templates = [c['constraint_creation']['source_template_sha256'] for c in selected]
    accepted = (len(groups) == expected_groups and len(assigned) == expected_groups*per_group
                and len(selected) == len(assigned) and len(set(templates)) == len(templates))
    identity = {'cell_identity':cell_identity(), 'operation':'bounded-creation-cases-v1', 'role':role,
        'scope':'pilot' if role == 'pilot' else 'scientific', 'source':sources(),
        'source_pool':str(source), 'source_complete_sha256':file_hash(source/'COMPLETE.json'),
        'pilot_offset':pilot_offset, 'per_group':per_group, 'expected_groups':expected_groups,
        'assigned_units':[c['unit'] for c in assigned], 'selected_units':[c['unit'] for c in selected],
        'selection_uses_future':False, 'selection_uses_realized_length':False, 'maximum_actions':MAXIMUM_ACTIONS}
    with writer(directory):
        Units(directory, identity); previous = reentry(directory, identity)
        if previous is not None: return previous
        freeze(directory/'CASES.json', selected); freeze(directory/'REALIZATION.json', realization)
        return finish(directory, identity, start, cpu, ['CASES.json','REALIZATION.json'],
            accepted=accepted, role=role, construction_only=True, selected_series=len(selected),
            assigned_series=len(assigned), requested_series=expected_groups*per_group,
            source_candidates=len(candidates), scientific_admission=False,
            disposition='DESCRIPTIVE' if accepted else 'IMPLEMENTATION INVALID')


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    for name in ('output','source'): p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--role',choices=('pilot','development','discovery'),required=True)
    p.add_argument('--pilot-offset',type=int,default=0)
    a = p.parse_args(); prepare(a.output,a.source,a.role,a.pilot_offset)
