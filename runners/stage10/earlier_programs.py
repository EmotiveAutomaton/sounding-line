"""Earlier drafts inform rule selection; the original executor stays fixed.

DESIGN CHECK: LESSONS3-5 and READER_HEURISTICS3/10 reread. NULL: changing a
prior draft cannot change an identical rule's current-state execution. The
ALTERNATIVE is changed proposal selection from additional genuine evidence,
not a new executor. Private handling fields and undeclared views refuse.
"""
from dataclasses import replace
from . import human_programs as original

ACTIONS = original.ACTIONS
FEATURES = original.FEATURES
DESCRIPTIONS = original.DESCRIPTIONS
validate = original.validate
execute = original.execute


def current_state(task):
    if task.evidence_view != 'earlier-artifacts' or set(task.evidence) != {'document', 'suggestions', 'earlier_drafts'}:
        raise ValueError('only the declared earlier-artifact view is supported')
    prior = task.evidence['earlier_drafts']
    if not isinstance(prior, list) or len(prior) > 1 or any(not isinstance(s, str) for s in prior):
        raise ValueError('expected zero or one complete prior draft')
    return replace(task, evidence_view='artifact', evidence={k: task.evidence[k] for k in ('document', 'suggestions')})


def features(task):
    return original.features(current_state(task))


def evaluate(task, candidates):
    return original.evaluate(current_state(task), candidates)
