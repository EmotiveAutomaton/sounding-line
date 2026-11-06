"""WB1.h1 exact cached document-state materialization, old source retained.

DESIGN CHECK: LESSONS3-5/CONTROLS reread2026-11-04. NULL no change retains
identical snapshots and sentence indicators; signed insertions/deletions and
eligible original-unit survival match the original exactly. A changed source
or anchor refuses. This optimization cannot alter a scientific gate or sample.
"""
from types import FunctionType, SimpleNamespace
import numpy as np
from . import week3_pieces_effects_h1 as old
from . import week3_pieces_effects_h1_pilot as pilot


def effect_windows(events,timeline,occurrences):
    clocks=old.checked_clock(events)
    lifetime=old.reconstruct(events,timeline)['eligible']
    required=set();spans=[]
    for occurrence in occurrences:
        at=occurrence['source_ordinal']
        if not 0<=at<len(events) or not np.isclose(clocks[at],occurrence['seconds'],atol=1e-7,rtol=0):
            raise ValueError('piece anchor differs from original source')
        target=clocks[at]+60;end=int(np.searchsorted(clocks,target,side='right'))-1
        required.update((at,end));spans.append((at,end,clocks[-1]>=target))
    snapshots={};completed=[];doc=old.units(events[0]['currentDoc'])
    current=old.text_of(doc);sentence_count=len(old.END_SENTENCE.findall(current))
    for ordinal,event in enumerate(events):
        ops=old.delta_ops(event.get('textDelta'))
        if ops:
            doc,_,_=old.apply_delta(doc,[None]*len(doc),event.get('textDelta'))
            current=old.text_of(doc);new_count=len(old.END_SENTENCE.findall(current))
            if new_count>sentence_count:completed.append(ordinal)
            sentence_count=new_count
        if ordinal in required:snapshots[ordinal]=current
    if old.text_of(doc)!=timeline['final_document']:raise ValueError('effect replay differs from P2')
    accepted=[d for d in timeline['decisions'] if d['handling'] in {'accept','edit'}]
    results=[]
    for occurrence,(at,end,full) in zip(occurrences,spans):
        menus=[d['ordinal'] for d in accepted if at<d['resolution_ordinal']<=end]
        original=sum(lifetime[k]['original_utf16'] for k in menus)
        surviving=sum(lifetime[k]['surviving_utf16'] for k in menus)
        results.append(dict(**occurrence,full_followup=full,end_ordinal=end,
            before=snapshots[at],after=snapshots[end],
            net_characters=len(snapshots[end])-len(snapshots[at]) if full else None,
            sentence_completed=int(any(at<i<=end for i in completed)) if full else None,
            accepted_original_utf16=original,accepted_surviving_utf16=surviving,
            accepted_retained_share=surviving/original if full and original else None))
    return results


def copied(function,**changes):
    return FunctionType(function.__code__,dict(function.__globals__,**changes),
                        function.__name__,function.__defaults__,function.__closure__)


effects=SimpleNamespace(**dict(old.__dict__,effect_windows=effect_windows))
measure=copied(pilot.measure,effects=effects)
execute=copied(pilot.execute,measure=measure)
verify=copied(pilot.verify,measure=measure)
