"""Matched prior exposure crossed with pre-future expected-choice strata.

DESIGN CHECK: T02/X01/X02/X05/X08; LESSONS 3--5, CONTROLS 6--7.
NULL: a label alone cannot change any trajectory; modifying old unseen outcomes
cannot change this construction. ALTERNATIVE: same-maker prior works can support
recognition even for an expected choice. The current maker is fixed; familiar
exposure uses its earlier works, unfamiliar exposure a different persistent maker
under the exact same public conditions and per-work purposes. No length matching.
Expected/unexpected draws condition the FIRST executed action on disjoint high/low
probability sets fixed from the actual initial policy. This balanced conditional
stress population is not a natural-frequency calibration sample. Future draws are
last, never selection inputs. Neither stratum nor maker identity enters the reader.
"""
import copy
import argparse
import math
import random
import time
from pathlib import Path

from .artifact_preparation import evidence, work
from .common import REPO, ROOT, Units, closure, digest, file_hash, freeze, read
from .constraint_cases import initial_world
from .construction import LAW, Replay, register
from .matched_controls import construct as other_maker
from .artifact_comparisons import validate_cases
from .queue import inside, writer
from .revision_predictions import sources, reentry, finish
from .training_jobs import cell_identity

MAXIMUM_ACTIONS = 3
ARCHIVE_WORKS = 3
CONDITIONS = tuple(f+'|'+s for f in ('familiar', 'unfamiliar') for s in ('expected', 'unexpected'))


def choice_strata(probabilities):
    """Strict per-action probability separation; no sampled action/outcome input."""
    actions = {a:p for a,p in probabilities.items() if a != 'stop' and p > 0}
    if len(actions) < 2 or max(actions.values()) <= min(actions.values()):
        raise ValueError('initial policy cannot realize distinct expected-choice strata')
    threshold = (min(actions.values()) + max(actions.values())) / 2
    strata = {'expected': {a:p for a,p in actions.items() if p >= threshold},
              'unexpected': {a:p for a,p in actions.items() if p < threshold}}
    if any(not row for row in strata.values()):
        raise ValueError('empty expected-choice stratum')
    return strata, threshold


def draw(probabilities, seed):
    total = math.fsum(probabilities.values())
    u = random.Random(seed).random() * total
    for action, p in sorted(probabilities.items()):
        u -= p
        if u <= 0: return action
    return sorted(probabilities)[-1]


def construct(case, role='pilot'):
    register()
    if len(case['source_worlds']) < ARCHIVE_WORKS + 1:
        raise ValueError('familiarity requires a target and three separate earlier works')
    current = initial_world(case['source_worlds'][0])
    old = case['source_worlds'][1:ARCHIVE_WORKS+1]
    key = digest({'familiarity_other_maker_v1':[w['lid'] for w in old]})
    # This existing constructor reads only earlier templates; no current world or
    # old continuation enters the other-maker choice. Re-sample bounded histories.
    alternative = other_maker(old, role, key)
    archives, observations = {}, {}
    for familiarity, originals in (('familiar', old), ('unfamiliar', alternative['worlds'])):
        archives[familiarity], observations[familiarity] = [], []
        for original in originals:
            w = initial_world(original)
            seed = int(digest({'familiarity_archive_v1':w['lid']})[:16], 16)
            events, stopped = Replay(w).continue_teacher(seed, max_events=MAXIMUM_ACTIONS)
            if len(events) > MAXIMUM_ACTIONS or stopped == (len(events) == MAXIMUM_ACTIONS):
                raise ValueError('bounded archive stopping and censoring disagree')
            archives[familiarity].append((w, events, True if stopped else None))
            observations[familiarity].append({'seed':seed, 'events':events, 'stopped':stopped})
    for original, other in zip(archives['familiar'], archives['unfamiliar']):
        if (work(original[0], [], 'artifact') != work(other[0], [], 'artifact') or
                original[0]['inventory'] != other[0]['inventory'] or
                original[0]['goal_name'] != other[0]['goal_name']):
            raise ValueError('prior-exposure manipulation changes matched public conditions or purpose')
    def template(w):
        return {k:w[k] for k in ('domain','doc','inventory','state','shape')}
    current_id = digest(template(current))
    for archive in archives.values():
        ids = [digest(template(w)) for w,_,_ in archive]
        if len(set(ids)) != ARCHIVE_WORKS or current_id in ids:
            raise ValueError('familiarity archive repeats a source or the target')
    initial = Replay(current).probabilities()
    strata, threshold = choice_strata(initial)
    prefixes, outcomes = {}, {}
    for stratum, choices in strata.items():
        seed = int(digest({'familiarity_choice_v1':current['lid'], 'stratum':stratum})[:16],16)
        chosen = draw(choices, seed)
        replay = Replay(current)
        action = next(a for a in replay.legal_actions() if LAW.action_id(a) == chosen)
        prefix = replay.apply(action)
        prefixes[stratum] = {'events':[prefix], 'seed':seed, 'action':chosen,
            'source_action_probability_given_execution':initial[chosen]/(1-initial['stop']),
            'stratum_mass_given_execution':math.fsum(choices.values())/(1-initial['stop'])}
    # Strata, exact matching and both prefixes exist before any future is drawn.
    for stratum, row in prefixes.items():
        replay = Replay(current, row['events']); oracle = replay.probabilities()
        seed = int(digest({'familiarity_future_v1':current['lid'], 'stratum':stratum})[:16],16)
        events, stopped = replay.continue_teacher(seed, max_events=2)
        target = 'stop' if stopped else LAW.action_id(events[0])
        outcomes[stratum] = {'target':target, 'future_event':events, 'future_stopped':stopped,
                            'oracle':oracle, 'seed':seed}
    queries, metadata = {}, {}
    for view in ('artifact','process_record'):
        for condition in CONDITIONS:
            familiarity, stratum = condition.split('|')
            name = 'q'+str(len(queries))
            ev = evidence(current, prefixes[stratum]['events'], view, archives[familiarity])
            result = outcomes[stratum]
            if result['target'] not in ev['support'] or set(result['oracle'])-set(ev['support']):
                raise ValueError('future outside full public support')
            queries[name] = ev
            metadata[name] = {'view':view, 'condition':condition, 'recognition_target':
                'same' if familiarity == 'familiar' else 'different', 'future_target':result['target']}
    return {'views':queries, 'queries':metadata, 'maximum_actions':MAXIMUM_ACTIONS,
        'archive_work_count':ARCHIVE_WORKS, 'prefixes':prefixes, 'outcomes':outcomes,
        'choice_threshold':threshold, 'choice_strata':strata, 'initial_policy':initial,
        'other_maker_plan':alternative['plan'], 'archive_observations':observations,
        'source_template_sha256':digest([template(current),*[template(w) for w in old]]),
        'scope':'balanced conditional first-choice stress; three bounded prior works; no natural-frequency calibration',
        'current_observation':'exactly one executed action; no observed future stop'}


def prepare(directory, source, role, pilot_offset=0):
    start,cpu=time.monotonic(),time.process_time(); register()
    directory,source=inside(directory),inside(source)
    namespace=ROOT/'private'/('familiarity-case-pilots' if role=='pilot' else 'scientific-familiarity-cases')
    if (role not in ('pilot','development','discovery') or not directory.is_relative_to(namespace)
            or pilot_offset not in (0,1) or role!='pilot' and pilot_offset):
        raise ValueError('undeclared familiarity source scope')
    done,own=read(source/'COMPLETE.json'),read(source/'IDENTITY.json')
    if (done.get('accepted') is not True or done.get('construction_only') is not True or done['role']!=role
            or done['identity_sha256']!=digest(own)
            or closure([REPO/p for p in done['outputs']['files']])!=done['outputs']):
        raise ValueError('ordinary source pool incomplete, changed or failed realization')
    cases=read(source/'CASES.json');validate_cases(cases,role)
    if role!='pilot' and (own['per_cohort']!=2 or len(cases)!=192):
        raise ValueError('familiarity needs its full fixed 192-series scientific pool')
    groups={}
    for case in sorted(cases,key=lambda c:digest({'familiarity_selection_v1':c['source_worlds'][0]['lid']})):
        group=case['private_factors']['domain'] if role=='pilot' else case['private_factors']['domain']+'|'+case['private_factors']['purpose']
        groups.setdefault(group,[]).append(case)
    expected_groups,per_group=(2,1) if role=='pilot' else (8,24)
    assigned=[c for group in sorted(groups) for c in groups[group][pilot_offset:pilot_offset+per_group]]
    selected,realization=[],[]
    for case in assigned:
        try:cf=construct(case,role)
        except ValueError as exc:realization.append({'unit':case['unit'],'realized':False,'reason':str(exc)})
        else:
            selected.append({**case,'familiarity':cf})
            realization.append({'unit':case['unit'],'realized':True})
    templates=[c['familiarity']['source_template_sha256'] for c in selected]
    accepted=(len(groups)==expected_groups and len(assigned)==expected_groups*per_group
              and len(selected)==len(assigned) and len(set(templates))==len(templates))
    identity={'cell_identity':cell_identity(),'operation':'familiarity-cases-v1','role':role,
        'scope':'pilot' if role=='pilot' else 'scientific','source':sources(),'source_pool':str(source),
        'source_complete_sha256':file_hash(source/'COMPLETE.json'),'pilot_offset':pilot_offset,
        'per_group':per_group,'expected_groups':expected_groups,'assigned_units':[c['unit'] for c in assigned],
        'selected_units':[c['unit'] for c in selected],'maximum_actions':MAXIMUM_ACTIONS,
        'archive_work_count':ARCHIVE_WORKS,'selection_uses_future':False,'selection_uses_realized_length':False}
    with writer(directory):
        Units(directory,identity);previous=reentry(directory,identity)
        if previous is not None:return previous
        freeze(directory/'CASES.json',selected);freeze(directory/'REALIZATION.json',realization)
        return finish(directory,identity,start,cpu,['CASES.json','REALIZATION.json'],accepted=accepted,
            role=role,construction_only=True,selected_series=len(selected),assigned_series=len(assigned),
            requested_series=expected_groups*per_group,scientific_admission=False,
            disposition='DESCRIPTIVE' if accepted else 'IMPLEMENTATION INVALID')


if __name__=='__main__':
    p=argparse.ArgumentParser()
    for k in ('output','source'):p.add_argument('--'+k,type=Path,required=True)
    p.add_argument('--role',choices=('pilot','development','discovery'),required=True)
    p.add_argument('--pilot-offset',type=int,default=0)
    a=p.parse_args();prepare(a.output,a.source,a.role,a.pilot_offset)
