"""Bounded complete-matrix execution for source-bound discrete comparisons.

DESIGN CHECK: LESSONS 3-5. NULL: empty, duplicate or one-arm matrices refuse;
invalid calls stay in the denominator. ALTERNATIVE: complete source pairs
can be compared descriptively, with raw replay before completion. A local
constructed canary is interface admission, not proof of human task capability.
"""
from collections import defaultdict
import statistics
from .common import read,freeze,filehash,distribution
from .local_api import call,service
from .canary import PROFILE
from .context_battery import matched_timing_check


def run(out,card,pulse,raw):
    source=raw/'jobs'/card['compile_card'];all_rows=read(source/'REQUESTS.json');wanted=set(card['request_ids'])
    rows=[r for r in all_rows if r['id'] in wanted];targets={r['id']:r for r in read(source/'EVALUATOR_ONLY.json')}
    if not rows or len(rows)!=len(wanted):raise ValueError('discrete roster incomplete or duplicated')
    from .output_interface import rows_for_card,profile_for_card
    rows=rows_for_card(rows,card)
    units=defaultdict(set)
    for r in rows:units[r['source_id']].add((r['method'],r['direction']))
    expected={tuple(r) for r in card['conditions']}
    if any(v!=expected for v in units.values()):raise ValueError('source unit does not contain all frozen rivals')
    admission=raw/'jobs'/card['canary_card']
    if read(admission/'ADMISSION.json').get('reader_admitted') is not True:raise ValueError('reader interface not admitted')
    baseline=[r['call'] for r in read(admission/'ROWS.json') if r['call_class']=='forecast']
    calls=[];scored=[]
    with service(out,profile_for_card(card,admission,PROFILE),raw) as state:
        for i,r in enumerate(rows):
            pulse(phase='complete-discrete-matrix',completed=i,total=len(rows))
            target=targets[r['id']]['target'];c=call(r['request'],len(target),out/'calls'/r['id'],state,raw);calls.append(c)
            if len(calls)%5==0:
                matched=matched_timing_check(calls[-5:],baseline);freeze(out/f'TIMING-{i+1}.json',matched)
                if matched['degraded']:raise RuntimeError('matched throughput degraded; preserve incomplete unit')
            scored.append(dict(id=r['id'],source_id=r['source_id'],method=r['method'],direction=r['direction'],
                **distribution(c['probabilities'],target)))
    for r,c in zip(rows,calls):
        if call(r['request'],len(targets[r['id']]['target']),out/'calls'/r['id'],{'uncertain':False},raw)!=c:raise ValueError('raw replay differs')
    freeze(out/'ROWS.json',scored)
    return dict(status='complete',kind='scientific',sources=len(units),rows=len(scored),
        scope=card['claim_scope'],controls=dict(all_rivals=True,invalids_retained=True,raw_semantic_replay=True,actual_canary_verdict=True),
        files={'ROWS.json':filehash(out/'ROWS.json')})
