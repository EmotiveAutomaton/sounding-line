"""Evaluator-owned independent maker-series cases and prospective query cuts.

DESIGN CHECK: M01/M04/C08/X01/X02; LESSONS 3--5, especially terminal truth,
realization, whole-unit independence and evidence leakage. NULL: altering unseen
events cannot change the chosen boundary or visible input; copied works cannot add
independent units. ALTERNATIVE: recorded stop and action targets both survive an
outcome-independent cut, and actual same-maker works retain persistent factors.
Bands: realized with complete support, or explicit construction exclusion; no
reader score for an unrealized case. Consumers gate each condition's realization.

The cut is sampled BEFORE constructing its current world: geometric(p=.35) failures,
starting at boundary zero. Cuts >=40 are outside the declared observation window.
Stopping before that requested boundary makes the attempt unrealized; it is never
replaced by the last available action. Thus selection at a reached boundary cannot
depend on the unobserved stop/next-action draw at that boundary. No oversampling or
unrecorded importance weights. The estimand is the reached-boundary population.
"""
from __future__ import annotations

import itertools
import math
import random

from .artifact_preparation import evidence, work
from .artifact_training import LAWS, RESIDUES
from .artifact_view import action_id
from .common import digest, distribution
from .construction import Replay, register
from .recipes import (POP, PURPOSES, W, doc_plan, make_world_ext,
                      parameter_partition, required_sections)

COHORTS = tuple(itertools.product(POP.DOMAINS, LAWS, RESIDUES, PURPOSES))
ROLES = ('training', 'pilot', 'development', 'discovery', 'reserve')
TERMINAL = ('hazard', 'exhausted', 'no_options')


def requested_boundary(key, probability=.35):
    if not isinstance(key, str) or not key or not 0 < probability < 1:
        raise ValueError('explicit query seed and interior boundary probability required')
    u = random.Random(int(digest({'s9_prospective_cut_v1': key})[:16], 16)).random()
    return int(math.log1p(-u)/math.log1p(-probability))


def recorded_target(trajectory, cut):
    if type(cut) is not int or not 0 <= cut < 40:
        return None, 'outside_declared_query_window'
    steps = trajectory['steps']
    if cut > len(steps):
        return None, 'terminated_before_requested_boundary'
    if cut == len(steps):
        if trajectory['stop_kind'] in TERMINAL:
            return 'stop', None
        return None, 'right_censored_without_target'
    return action_id(steps[cut]), None


def content_identity(world):
    # Excludes labels that change only the pseudorandom seed or directory name.
    return digest({k:world[k] for k in ('domain','doc','inventory','state','trajectory','shape')})


def prepare_case(current, earlier, cut, role):
    """Private targets remain outside each validated public evidence object."""
    if role not in ROLES or not 0 <= len(earlier) <= 7:
        raise ValueError('invalid case role or dose')
    expected_partition = 'training' if role == 'pilot' else role
    if any(parameter_partition(w) != expected_partition for w in [current, *earlier]):
        raise ValueError('whole series crosses the declared parameter partition')
    target, reason = recorded_target(current['trajectory'], cut)
    if reason:
        return {'realized':False, 'reason':reason, 'requested_boundary':cut}
    names = current['state']['names']
    if any(w['state']['names'][k] != names[k] for w in earlier for k in ('law','residue','tendency')):
        raise ValueError('earlier work does not preserve the declared maker factors')
    source_hashes = [content_identity(w) for w in [current, *earlier]]
    if len(set(source_hashes)) != len(source_hashes):
        raise ValueError('duplicate world content in maker series')
    prefix = current['trajectory']['steps'][:cut]
    previous = [(w, w['trajectory']['steps'], w['trajectory']['stop_kind'] in TERMINAL) for w in earlier]
    views = {v:evidence(current, prefix, v, previous) for v in ('artifact','process_record')}
    # Exact target copies are refused for all comparator routes before adaptation.
    visible_hashes = [digest(views['artifact']['current']), *[digest(w) for w in views['artifact']['earlier']]]
    if len(set(visible_hashes)) != len(visible_hashes):
        return {'realized':False, 'reason':'duplicate_visible_work', 'requested_boundary':cut}
    oracle = Replay(current, prefix).probabilities()
    distribution(oracle)
    if any(set(oracle)-set(v['support']) or target not in v['support'] for v in views.values()):
        raise ValueError('recorded target or true predictive support omitted from public query')
    if oracle.get(target, 0) <= 0:
        raise ValueError('recorded target impossible under the reconstructed generator')
    return {'realized':True, 'unit':digest({'stage9_series_content_v1':source_hashes}),
        'role':role, 'parameter_partition':expected_partition, 'requested_boundary':cut,
        'sources':source_hashes, 'views':views, 'target':target, 'oracle':oracle,
        'private_factors':{'law':names['law'], 'residue':names['residue'],
                           'tendency':names['tendency'], 'purpose':current['goal_name'],
                           'domain':current['domain'], 'shape':current['shape']}}


def construct_attempt(*, key, cohort, role, dose=7, maximum_parameter_draws=100):
    """Return an explicit attempt disposition; never search for a reader success."""
    if role not in ROLES or cohort not in COHORTS or type(dose) is not int or not 0 <= dose <= 7:
        raise ValueError('undeclared series condition')
    if type(maximum_parameter_draws) is not int or maximum_parameter_draws < 1:
        raise ValueError('invalid bounded construction allowance')
    cut = requested_boundary(key)  # must precede construction and trajectory access
    if cut >= 40:
        return {'realized':False, 'reason':'outside_declared_query_window', 'requested_boundary':cut}
    register()
    domain, law, residue, goal = cohort
    expected = 'training' if role == 'pilot' else role
    worlds = []
    draw_counts = []
    for ordinal in range(dose+1):
        for attempt in range(maximum_parameter_draws):
            lid = f'S9SERIES|{role}|{key}|work{ordinal}|draw{attempt}'
            rng = W._rng(lid, 'series-conditions')
            purpose = goal if ordinal == 0 else PURPOSES[rng.randrange(len(PURPOSES))]
            shape = POP.SHAPES[rng.randrange(len(POP.SHAPES))]
            world = make_world_ext(lid, domain, shape, goal=purpose, law_name=law, residue=residue,
                tendency=worlds[0]['state']['names']['tendency'] if worlds else None,
                forced_cext={'brief_sections':required_sections(doc_plan(lid,domain,shape),purpose)},
                owner_all=purpose, finish=False)
            world['goal_name'] = purpose
            if parameter_partition(world) == expected:
                worlds.append(world)
                draw_counts.append(attempt+1)
                break
        else:
            return {'realized':False, 'reason':'parameter_draw_budget_exhausted',
                    'requested_boundary':cut, 'completed_works':len(worlds),
                    'parameter_draws':sum(draw_counts)+maximum_parameter_draws}
    result = prepare_case(worlds[0], worlds[1:], cut, role)
    result['parameter_draws'] = sum(draw_counts)
    result['source_worlds'] = worlds  # evaluator-only; never copied to a reader
    return result


def dose_view(case, dose, view='artifact', *, repeat=False, replacement=None):
    """Matched case construction; replacement must be separately matched by its caller."""
    import copy
    from .artifact_view import validate
    if not case['realized'] or type(dose) is not int or not 0 <= dose <= 7:
        raise ValueError('realized case and declared dose required')
    result = copy.deepcopy(case['views'][view])
    pool = result['earlier'] if replacement is None else replacement
    if len(pool) < (1 if repeat and dose else dose):
        raise ValueError('requested distinct prior dose unavailable')
    result['earlier'] = copy.deepcopy(([pool[0]]*dose if repeat and dose else pool[:dose]))
    return validate(result)
