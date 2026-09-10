"""Training-only source construction with shared parameter-combination exclusions.

DESIGN CHECK: C05/C06/X01. Narrow rendering equals the original replay recipe.
NULL: an earlier work in another partition excludes the entire training example.
ALTERNATIVE: both law coverages preserve the same non-law factors and visible renderer.
This prepares candidates, not a locked token-matched training corpus.
"""
import copy

from runners.stage8.constructor import population as POP
from runners.stage8.constructor.gradient import make_world_ext, doc_plan
from runners.stage8.constructor.purpose import PURPOSES, required_sections
from runners.stage8.reader import logfmt as LF
from runners.stage9.common import digest
from runners.stage9.construction import W, register

SECONDARY_BY_ROLE = {'novice': 'novice2', 'expert': 'editor2', 'specialist': 'scholar2'}
ROLE_BY_SECONDARY = {v: k for k, v in SECONDARY_BY_ROLE.items()}


def combination(world):
    names = world['state']['names']
    # Both law variants of one role belong to the same held-out combination.
    return {'law_role': ROLE_BY_SECONDARY.get(names['law'], names['law']), 'belief': names['belief'],
            'residue': names['residue'], 'tendency': names['tendency'],
            'goal': world['goal_name'], 'shape': world['shape']}


def parameter_partition(world):
    value = int(digest({'stage9_parameter_partition_v1': combination(world)})[:12], 16) % 100
    return 'reserve' if value < 30 else 'discovery' if value < 45 else 'development' if value < 55 else 'training'


def sampled_world(lid, coverage='original'):
    if coverage not in ('original', 'both'):
        raise ValueError('unknown law coverage')
    register()
    original = POP.sample_world(lid)
    if coverage == 'original' or int(digest({'law_variant': lid})[:8], 16) % 2 == 0:
        return original
    names = original['state']['names']
    goal = original['goal_name']
    forced = {'brief_sections': required_sections(original['doc'], goal)} if goal in PURPOSES else None
    world = make_world_ext(lid, original['domain'], original['shape'], goal=goal, law_name=SECONDARY_BY_ROLE[names['law']],
                           belief=names['belief'], residue=names['residue'], tendency=names['tendency'],
                           forced_cext=forced, owner_all=goal if goal in PURPOSES else None, finish=False)
    world['goal_name'] = goal
    return world


def training_record(i, domain, band, coverage='original'):
    lid = POP.pop_lid(i, domain, band)
    world = sampled_world(lid, coverage)
    r = W._rng(lid, 'render')
    with_goal = r.random() < .5
    earlier, worlds, lids = [], [world], [lid]
    if r.random() < .4:
        names = world['state']['names']
        for k in range(1 + r.randrange(3)):
            plid = f'{lid}|prev{k}'
            rk = W._rng(plid, 'pop')
            goal = POP.GOAL_SPACE[rk.randrange(len(POP.GOAL_SPACE))]
            shape = POP.SHAPES[rk.randrange(len(POP.SHAPES))]
            forced = {'brief_sections': required_sections(doc_plan(plid, domain, shape), goal)} if goal in PURPOSES else None
            pw = make_world_ext(plid, domain, shape, goal=goal, law_name=names['law'], residue=names['residue'],
                                tendency=names['tendency'], forced_cext=forced, owner_all=goal if goal in PURPOSES else None,
                                finish=False, salt='prev')
            pw['goal_name'] = goal
            earlier.append(POP.world_log(pw, False))
            worlds.append(pw)
            lids.append(plid)
    log = POP.world_log(world, with_goal)
    text = '\n'.join([LF.EARLIER] + earlier + [LF.NOW, log]) if earlier else log
    original_fields = {'lid': lid, 'lineages': lids, 'text': text, 'goal': world['goal_name'], 'with_goal': with_goal,
                       'n_earlier': len(earlier), 'shape': world['shape'], 'domain': domain,
                       'n_events': len(world['trajectory']['steps']), 'names': copy.deepcopy(world['state']['names'])}
    return original_fields, worlds


def eligible_training_pair(i, domain, band):
    narrow, nw = training_record(i, domain, band, 'original')
    broad, bw = training_record(i, domain, band, 'both')
    allowed = all(parameter_partition(w) == 'training' for w in nw + bw)
    return allowed, {'original': narrow, 'both': broad}, {'original': nw, 'both': bw}
