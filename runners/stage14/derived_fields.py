"""SL4 complete deterministic record adapter and exact constructor comparison.

DESIGN CHECK: LESSONS 2-5. NULL: absent or unlocated fields fabricated from spans
fail exact source controls. ALTERNATIVE: source-defined roles, relation, related
slot and anchor state derive without elicitation. This is extraction, not hidden
history inference; ambiguous marginal presence is not a coherent graph.
"""
from .common import freeze
from .factorized import controls
from .compact import free,expand
from runners.stage11_1.targets import anchors,SLOTS

def derive(value,text):
    result=expand(value);sp=anchors(text)
    for i,f in enumerate(result['facts']):
        if value['present'][i] not in (0.,1.):raise ValueError('coherent binary realization required; marginals are not a graph')
        present=bool(value['present'][i]);entry=bool(value['present'][1])
        parent='selection' if f['slot']=='entry' else 'entry'
        if f['slot'] in ('continuation','surrounding') and not entry:parent=''
        f['related_slot']=parent if present else ''
        ids=[a['id'] for a in sp if any(a['start']<end and start<a['end'] for start,end in f['exact_spans'])]
        f['span_ids']=ids;f['span_state']='located' if ids else 'unlocated' if present else 'absent'
    return result

def run(card,out,raw,tick):
    rows=[]
    for c in controls():
        d=derive(free(c['target']),c['event']['end_document'])
        exact=all(all(a[k]==b[k] for k in ('related_slot','span_ids','span_state','exact_spans')) for a,b in zip(d['facts'],c['target']['facts']))
        rows.append(dict(key=c['key'],exact=exact,record=d))
    freeze(out/'PREDICTIONS.json',rows);freeze(out/'SUMMARY.json',dict(cases=len(rows),exact=sum(r['exact'] for r in rows),scope='deterministic fields from binary free quantities; earlier compact scores omitted these fields and retain bounded scope'))
    freeze(out/'ADMISSION.json',dict(admitted=all(r['exact'] for r in rows),scope='source constructor equivalence for related slot and span state; no natural graph admission'))
