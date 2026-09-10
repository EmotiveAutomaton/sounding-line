"""Executable candidate over observable construction marks, not a true-state kernel.

DESIGN CHECK: M01/M02/M05/C08; LESSONS 3--5. NULL: equal operative programs
give equal predictions regardless of labels. ALTERNATIVE: purpose utility, believed
tools, available types, expertise cost/progress and habitual bias can imply different
choices. Every factor is supplied by an inference proposal or training-only library.
No constructor, inventory, episode identifier or future trace is imported here.

This deliberately approximate process has a set-valued state. Failures leave that
state unchanged. It models successful-mark progress, not the original constructor's
attempt clock, belief learning, goal transitions or entire historical process.
"""
import math

from .artifact_view import TYPES, all_header_actions, type_counts, support, validate_work
from .program_inference import distribution

VERSION = 's9-mark-program-v1'
FIELDS = {'version', 'purpose', 'context', 'available_types', 'expertise', 'history', 'stop',
          'section_bias', 'action_noise', 'outcome_noise'}


def numeric(value):
    return type(value) in (int, float) and math.isfinite(value)


def vector(values, keys):
    return isinstance(values, dict) and set(values) == set(keys) and all(numeric(v) for v in values.values())


def validate(program):
    if set(program) != FIELDS or program['version'] != VERSION:
        raise ValueError('incomplete mark program')
    if not vector(program['purpose'], TYPES) or not vector(program['history'], TYPES):
        raise ValueError('invalid purpose or history operation weights')
    context = program['context']
    if (set(context) != {'library', 'source_access', 'deadline'} or
            any(context[k] not in ('follow', 'available', 'unavailable') for k in ('library', 'source_access')) or
            context['deadline'] not in ('follow', 'tight', 'loose')):
        raise ValueError('invalid interpreted context')
    available = program['available_types']
    if not isinstance(available, list) or len(set(available)) != len(available) or not set(available) <= set(TYPES):
        raise ValueError('invalid subjective action types')
    expertise = program['expertise']
    if (set(expertise) != {'cost', 'progress', 'fluency', 'success'} or
            not vector(expertise['cost'], TYPES) or not vector(expertise['success'], TYPES) or
            any(not 0 <= p <= 1 for p in expertise['success'].values()) or
            not vector(expertise['progress'], [a+'>'+b for a in TYPES for b in TYPES]) or
            not numeric(expertise['fluency']) or expertise['fluency'] <= 0):
        raise ValueError('invalid expertise law')
    if not vector(program['stop'], ('intercept', 'progress', 'deadline', 'self')):
        raise ValueError('invalid stopping law')
    if (not numeric(program['section_bias']) or
            any(not numeric(program[k]) or not 0 <= program[k] < 1 for k in ('action_noise', 'outcome_noise'))):
        raise ValueError('invalid declared noise or section bias')
    return program


def requirements(kind):
    # Public operation semantics in this approximate representation. These are
    # proposed executable rules, not a hidden inventory membership test.
    return ('source_access',) if kind == 'consult' else ('library',) if kind == 'cite' else ()


def policy(program, work, *, believed_checked=()):
    p = validate(program)
    validate_work(work, 'artifact')
    context = work['context']
    actions = all_header_actions(context)
    choices = support(work, 'artifact')
    sections = [s['name'] for s in context['sections']]
    if (not isinstance(believed_checked, (tuple, list)) or len(set(believed_checked)) != len(believed_checked)
            or not set(believed_checked) <= set(sections)):
        raise ValueError('invalid announced checked-section state')
    counts = type_counts(work)
    progress = len(work['marks']) / len(actions)
    interpreted_tools = {k: context['tools'][k] if p['context'][k] == 'follow' else p['context'][k] == 'available'
                         for k in context['tools']}
    deadline = context['deadline'] if p['context']['deadline'] == 'follow' else p['context']['deadline']
    logits = {}
    for aid in choices[1:]:
        action = actions[aid]
        kind = action['type']
        if kind == 'check' and action['section'] in believed_checked:
            continue
        if kind not in p['available_types'] or any(not interpreted_tools[t] for t in requirements(kind)):
            continue
        value = p['purpose'][kind] - p['expertise']['cost'][kind] + p['history'][kind]
        value += math.fsum(p['expertise']['progress'][old+'>'+kind] * counts[old]/len(actions) for old in TYPES)
        value += p['section_bias'] * (1-sections.index(action['section'])/len(sections))
        logits[aid] = value/p['expertise']['fluency']
    z = p['stop']['intercept'] + p['stop']['progress']*progress
    z += p['stop']['deadline']*float(deadline == 'tight') + p['stop']['self']*float(context['audience'] == 'self')
    if not math.isfinite(z) or any(not math.isfinite(v) for v in logits.values()):
        raise ValueError('nonfinite executed program')
    hazard = (1/(1+math.exp(-z)) if z >= 0 else math.exp(z)/(1+math.exp(z))) if logits else 1.
    peak = max(logits.values(), default=0.)
    weights = {a: math.exp(v-peak) for a, v in logits.items()}
    total = math.fsum(weights.values())
    eps = p['action_noise']
    result = {a: eps/len(choices)+(1-eps)*(hazard if a == 'stop' else
              (1-hazard)*weights.get(a, 0.)/total if total else 0.) for a in choices}
    return distribution(result, choices)


def success_probabilities(program, work):
    """Outcome law uses the public external tools, distinct from believed tools."""
    p = validate(program)
    validate_work(work, 'artifact')
    eps = p['outcome_noise']
    actions = all_header_actions(work['context'])
    return {aid: eps/2+(1-eps)*(p['expertise']['success'][action['type']]
               if all(work['context']['tools'][t] for t in requirements(action['type'])) else 0.)
            for aid, action in actions.items() if aid not in work['marks']}


def neutral_program():
    """Explicit test/proposal starting point; never a fallback for invalid inference."""
    return {'version': VERSION, 'purpose': {t: 0. for t in TYPES},
            'context': {'library': 'follow', 'source_access': 'follow', 'deadline': 'follow'},
            'available_types': list(TYPES),
            'expertise': {'cost': {t: 0. for t in TYPES}, 'success': {t: 1. for t in TYPES},
                          'progress': {a+'>'+b: 0. for a in TYPES for b in TYPES}, 'fluency': 1.},
            'history': {t: 0. for t in TYPES}, 'stop': {'intercept': -3., 'progress': 4., 'deadline': 1., 'self': 0.},
            'section_bias': 0., 'action_noise': .01, 'outcome_noise': .02}
