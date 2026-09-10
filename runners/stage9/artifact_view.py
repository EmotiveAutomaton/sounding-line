"""Visible constructed-artifact schema and complete header-defined action support.

DESIGN CHECK: M01/C08/X02/X06; LESSONS 3--5. NULL: hidden maker fields,
unobserved attempts, future events and inventory membership cannot enter this view.
ALTERNATIVE: visible completed marks and explicit process records have distinct
projections; the actual next action is in the same broad support for every reader.
The constructed artifact consists of operation marks, not natural human prose.
"""
from collections import Counter

TYPES = ('write', 'revise', 'check', 'consult', 'cite', 'restructure', 'probe', 'fix')
FIXED_SLOTS = {'consult': 'src', 'cite': 'ref', 'restructure': 'order', 'probe': 'tech'}
TOOLS = ('library', 'source_access')


def action_id(action):
    return ':'.join(action[key] for key in ('type', 'section', 'slot'))


def validate_work(work, view):
    required = {'context', 'marks'} | ({'events', 'observed_stop'} if view == 'process_record' else set())
    if view not in ('artifact', 'process_record') or set(work) != required:
        raise ValueError('undeclared work fields or evidence view')
    context = work['context']
    if set(context) != {'topic', 'audience', 'tools', 'deadline', 'sections'}:
        raise ValueError('undeclared context fields')
    if context['audience'] not in ('peer', 'self', 'editor') or context['deadline'] not in ('loose', 'tight'):
        raise ValueError('invalid declared context')
    if not isinstance(context['topic'], str) or len(context['topic']) > 4096:
        raise ValueError('invalid public topic')
    if set(context['tools']) != set(TOOLS) or any(type(v) is not bool for v in context['tools'].values()):
        raise ValueError('invalid declared tools')
    sections = context['sections']
    if not isinstance(sections, list) or not 1 <= len(sections) <= 16:
        raise ValueError('invalid section count')
    names = []
    for section in sections:
        if set(section) != {'name', 'slots'} or not isinstance(section['name'], str) or not section['name']:
            raise ValueError('invalid section schema')
        slots = section['slots']
        if not isinstance(slots, list) or not slots or len(slots) != len(set(slots)) or any(not isinstance(s, str) or not s for s in slots):
            raise ValueError('invalid section slots')
        if ':' in section['name'] or any(':' in s for s in slots):
            raise ValueError('ambiguous public action identity')
        names.append(section['name'])
    if len(set(names)) != len(names):
        raise ValueError('duplicate section')
    all_actions = all_header_actions(context)
    marks = work['marks']
    if not isinstance(marks, list) or any(not isinstance(m, str) for m in marks):
        raise ValueError('invalid visible marks')
    if marks != sorted(set(marks)) or not set(marks) <= set(all_actions):
        raise ValueError('noncanonical or impossible visible marks')
    if view == 'process_record':
        if work['observed_stop'] is not None and type(work['observed_stop']) is not bool:
            raise ValueError('invalid observed stop')
        completed = set()
        for i, event in enumerate(work['events']):
            if set(event) != {'i', 'type', 'section', 'slot', 'outcome'} or event['i'] != i:
                raise ValueError('undeclared process event or discontinuous clock')
            aid = action_id(event)
            if aid not in all_actions or aid in completed or event['outcome'] not in ('done', 'failed'):
                raise ValueError('invalid visible event')
            if event['outcome'] == 'done':
                completed.add(aid)
        if completed != set(marks):
            raise ValueError('process/artifact projection disagreement')
    return work


def all_header_actions(context):
    actions = {}
    for section in context['sections']:
        for kind in TYPES:
            for slot in ([FIXED_SLOTS[kind]] if kind in FIXED_SLOTS else section['slots']):
                action = {'type': kind, 'section': section['name'], 'slot': slot}
                actions[action_id(action)] = action
    return actions


def support(work, view):
    validate_work(work, view)
    # Tool-unavailable attempts are still visible actions with potentially failed
    # outcomes. This function supplies a query set, not a model's legality knowledge.
    return ['stop', *sorted(set(all_header_actions(work['context'])) - set(work['marks']))]


def validate(evidence):
    if set(evidence) != {'version', 'view', 'current', 'earlier', 'support'} or evidence['version'] != 's9-visible-artifact-v1':
        raise ValueError('undeclared artifact evidence schema')
    view = evidence['view']
    validate_work(evidence['current'], view)
    if not isinstance(evidence['earlier'], list) or len(evidence['earlier']) > 7:
        raise ValueError('earlier works exceed declared dose envelope')
    for work in evidence['earlier']:
        validate_work(work, view)
    if evidence['support'] != support(evidence['current'], view):
        raise ValueError('support omits or adds a header-defined action')
    if view == 'process_record' and evidence['current']['observed_stop'] is not None:
        raise ValueError('current queried stop cannot be supplied as an observation')
    return evidence


def type_counts(work):
    return Counter(mark.split(':')[0] for mark in work['marks'])
