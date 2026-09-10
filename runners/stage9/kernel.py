"""Finite executable candidate semantics, standard library only, capsule-copyable.

DESIGN CHECK: I05/I06/C04. This kernel receives a complete declared program, never
constructor files or a world identifier. Missing operative information is invalid.
NULL: an omitted belief/law/history field cannot be reconstructed from hidden truth.
ALTERNATIVE: supplied programs match the separate constructor on the supported domain.
The state, executable source and candidate support must be common to compared routes.
"""
import copy
import math

VERSION = 's9-finite-maker-kernel-1'
RULES = {'reading_order_bonus': .5, 'required_section_bonus': .4, 'maintained_bonus': 6.,
         'stop_base': -4.2, 'stop_satisfied': 3.8, 'stop_deadline': 2.4,
         'stop_fatigue': 1.8, 'stop_self': .3, 'minimum_temperature': 1e-6,
         'goal_transition': 'current goal if pending, else first pending goal in supplied order',
         'action_policy': 'softmax((utility-cost+chain+habit+reading_order+required_section+maintained)/fluency)',
         'unavailable': 'requires believed tool, minimum skill, and check section not believed checked',
         'stop': 'sigmoid(base+satisfaction+deadline*progress+fatigue*max(0,steps/expected_length-1)+self_audience)',
         'initial_stop': 'zero at step zero when an available action exists; one if no available action'}
FIELDS = {'version', 'rules', 'context', 'belief', 'law', 'history', 'goal_name', 'goal_last',
          'goal_order', 'goal_utilities', 'pending', 'inventory_size', 'done_ids', 'sections',
          'last_type', 'step'}


def action_id(action):
    return f"{action['type']}:{action['section']}:{action['slot']}"


def validate(program):
    if set(program) != FIELDS or program['version'] != VERSION or program['rules'] != RULES:
        raise ValueError('incomplete or different operative program')
    for key in ('context', 'belief', 'law', 'history', 'goal_utilities'):
        if not isinstance(program[key], dict):
            raise ValueError('missing numeric program factor: ' + key)
    if not {'tools', 'deadline', 'audience', 'brief_sections'} <= program['context'].keys():
        raise ValueError('incomplete external context')
    if not {'believed_tools', 'believed_deadline', 'believed_checked'} <= program['belief'].keys():
        raise ValueError('incomplete belief state')
    if not {'skill', 'feasible_min_skill', 'cost', 'chain', 'fluency', 'confidence', 'expected_len'} <= program['law'].keys():
        raise ValueError('incomplete executable law')
    if not {'habit', 'maintained'} <= program['history'].keys():
        raise ValueError('incomplete history residue')
    if type(program['step']) is not int or program['step'] < 0 or program['law']['expected_len'] <= 0:
        raise ValueError('invalid process clock')
    if len(set(program['done_ids'])) != len(program['done_ids']) or program['inventory_size'] < len(program['pending']):
        raise ValueError('invalid inventory accounting')
    if len({action_id(a) for a in program['pending']}) != len(program['pending']):
        raise ValueError('duplicate pending action')
    if program['goal_name'] not in program['goal_utilities'] or any(g not in program['goal_utilities'] for g in program['goal_order']):
        raise ValueError('missing operative goal utility')
    return program


def probabilities(program):
    p = validate(program)
    c, b, law, history = p['context'], p['belief'], p['law'], p['history']
    goal = p['goal_name']
    if not any(a['goal_owner'] == goal for a in p['pending']):
        goal = next((g for g in p['goal_order'] if any(a['goal_owner'] == g for a in p['pending'])), goal)
    utility = p['goal_utilities'][goal]
    available = []
    for a in p['pending']:
        if any(not b['believed_tools'].get(t, c['tools'].get(t, False)) for t in a['requires']):
            continue
        if law['skill'].get(a['type'], 0) < law['feasible_min_skill'].get(a['type'], 0):
            continue
        if a['type'] == 'check' and a['section'] in b['believed_checked']:
            continue
        available.append(a)
    if not available:
        return {'stop': 1.0}
    scores = {}
    audience_weight = round(1 - .6 * law['confidence'], 4) if c['audience'] != 'self' else 0.
    for a in available:
        kind = a['type']
        value = utility.get(kind, 0) - law['cost'].get(kind, 0) + history['habit'].get(kind, 0)
        if p['last_type'] is not None:
            value += law['chain'].get(p['last_type'] + '>' + kind, 0)
        position = p['sections'].index(a['section']) if a['section'] in p['sections'] else len(p['sections'])
        value += RULES['reading_order_bonus'] * (1 - position / max(1, len(p['sections'])))
        if a['section'] in c['brief_sections']:
            value += RULES['required_section_bonus'] * audience_weight
        maintained = history['maintained'] or {}
        if maintained.get('cue_step') == p['step'] and maintained.get('option') == action_id(a):
            value += RULES['maintained_bonus']
        scores[action_id(a)] = value
    maximum = max(scores.values())
    weights = {k: math.exp((v-maximum) / max(law['fluency'], RULES['minimum_temperature'])) for k, v in scores.items()}
    total = sum(weights.values())
    hazard = 0.
    if p['step']:
        z = RULES['stop_base']
        if not any(a['goal_owner'] == p['goal_last'] for a in p['pending']):
            z += RULES['stop_satisfied']
        if b['believed_deadline'] == 'tight':
            z += RULES['stop_deadline'] * len(p['done_ids']) / p['inventory_size']
        z += RULES['stop_fatigue'] * max(0., p['step'] / law['expected_len'] - 1)
        if c['audience'] == 'self':
            z += RULES['stop_self']
        hazard = 1 / (1 + math.exp(-z))
    result = {'stop': hazard, **{k: (1-hazard)*v/total for k, v in weights.items()}}
    if any(not math.isfinite(v) or not 0 <= v <= 1 for v in result.values()) or abs(sum(result.values())-1) > 1e-10:
        raise ValueError('invalid executed distribution')
    return result


def mixture(programs, weights):
    if not programs or len(programs) != len(weights) or any(not math.isfinite(w) or w < 0 for w in weights) or abs(sum(weights)-1) > 1e-8:
        raise ValueError('explicit normalized candidate-mixture weights required')
    predictions = [probabilities(p) for p in programs]
    support = sorted(set().union(*(d.keys() for d in predictions)))
    return {k: math.fsum(w*d.get(k, 0.) for w, d in zip(weights, predictions)) for k in support}
