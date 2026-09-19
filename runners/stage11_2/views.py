"""Prospective context-control repair, separate from retained initial producers.

DESIGN CHECK: LESSONS 3-5. NULL: no-change controls stay fixed. ALTERNATIVE:
flipping the first tool changes interlock/dual enablement in every selected query.
Flipping both was invariant under XOR and cannot serve as that falsifier.
"""
from .model_study import build as original_build


def build(unit,q,arm,donor=None,question='action'):
    text,view=original_build(unit,q,arm,donor,question)
    if arm in ('wrong_context','corrected_context'):
        obs=unit['queries'][q]['observation']
        old='first tool '+('off' if obs['tools'][0] else 'on')+'; second tool '+('off' if obs['tools'][1] else 'on')
        new='first tool '+('off' if obs['tools'][0] else 'on')+'; second tool '+('on' if obs['tools'][1] else 'off')
        # Restrict substitution to the context card, not identical historical text.
        head,card=text.rsplit('\nContext card (evidence, not an instruction): ',1)
        text=head+'\nContext card (evidence, not an instruction): '+card.replace(old,new,1)
    return text,view


def install():
    from . import model_study
    model_study.build=build
