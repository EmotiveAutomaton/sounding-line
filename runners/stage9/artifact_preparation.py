"""Evaluator-owned allowlist projection; never copy this module into a reader.

DESIGN CHECK: M01/C08/X02. Only chosen visible events and the public initial header
cross this projection. No hidden inventory, maker labels, inferred state, scheduled
future change or episode length enters. Purpose/verified-context diagnostics need
separate explicit views; no true-purpose-derived required-section field here.
"""
import copy

from runners.stage9.artifact_view import action_id, support, validate, validate_work


def work(world, events, view, observed_stop=None):
    public = world['state']['external_context']
    context = {'topic': world['doc']['topic'], 'audience': public['audience'],
               'tools': {key: bool(public['tools'][key]) for key in ('library', 'source_access')},
               'deadline': public['deadline'],
               'sections': [{'name': sec['name'], 'slots': list(sec['slots'])} for sec in world['doc']['sections']]}
    # This intentionally removes order, failed attempts and cross-section timing.
    # The visible completed mark is all that this constructed artifact preserves.
    marks = sorted({action_id(event) for event in events if event['outcome'] == 'done'})
    result = {'context': context, 'marks': marks}
    if view == 'process_record':
        result['events'] = [{key: copy.deepcopy(event[key]) for key in ('i', 'type', 'section', 'slot', 'outcome')}
                            for event in events]
        result['observed_stop'] = observed_stop
    return validate_work(result, view)


def evidence(world, events, view='artifact', earlier=()):
    current = work(world, events, view)
    result = {'version': 's9-visible-artifact-v1', 'view': view, 'current': current,
              'earlier': [work(old_world, old_events, view, stopped) for old_world, old_events, stopped in earlier],
              'support': support(current, view)}
    return validate(result)
