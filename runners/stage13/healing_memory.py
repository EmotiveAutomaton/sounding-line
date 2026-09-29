"""Information-matched rendering repair on the original exposed episode roster.

DESIGN CHECK: LESSONS 3-5; CONTROLS 6. NULL: unequal decoded payload, collapsed
treatments, missing source, changed roster, or excess native tokens refuses.
ALTERNATIVE: complete equal facts survive both renderings, repetition is exact,
paired loss is zero for equal replies and known categorical loss is reproduced.
No population interval is licensed by one connected source component.
"""
from copy import deepcopy
import json
import time
import numpy as np
from .common import freeze, read, digest, atomic, now
from . import context
from .reconstruction import ACTIONS, SLOTS
from .scoring import proper_loss, interval
from .detectors import Detector, cached_model

MODES=('none','raw','linked','repeated','mislinked','irrelevant','raw-unpadded')
LABELS=list(ACTIONS)+['unknown']


def render(payload,linked):
    if linked:return json.dumps(payload,ensure_ascii=False,separators=(',',':'))
    facts={r['slot']:r for r in payload['facts']}
    value={k:payload[k] for k in ('handling','endpoint_excerpt')}
    value['slots']=list(SLOTS)
    for field in ('actor','operation','relation','exact_spans'):
        value[field]=[facts[s][field] for s in SLOTS]
    return json.dumps(value,ensure_ascii=False,separators=(',',':'))


def decode(text,linked):
    value=json.loads(text)
    if linked:return value
    facts=[dict(slot=slot,**{f:value[f][i] for f in ('actor','operation','relation','exact_spans')}) for i,slot in enumerate(value['slots'])]
    return dict(handling=value['handling'],endpoint_excerpt=value['endpoint_excerpt'],facts=facts)


def prompts(row,training,tok,view):
    _,ids=context.intervention(row,training,'raw-retrieval')
    by={r['key']:r for r in training};source=by[ids[0]]
    if source['unit']==row['unit']:raise ValueError('memory crosses source component')
    payload=dict(handling=source['target']['handling'],
        endpoint_excerpt=tok.decode(tok.encode(source['views']['A']['endpoint'],add_special_tokens=False)[-12:]),
        facts=[{k:deepcopy(f[k]) for k in ('slot','actor','operation','relation','exact_spans')} for f in source['target']['facts']])
    payload['facts'].sort(key=lambda f:list(SLOTS).index(f['slot']))
    raw=render(payload,False);linked=render(payload,True)
    if decode(raw,False)!=payload or decode(linked,True)!=payload:raise ValueError('payload is not invertible')
    wrong=deepcopy(payload)
    # Deliberate misassociation of the same fact bundles to different slots.
    for i,f in enumerate(wrong['facts']):f['slot']=SLOTS[(i+1)%len(SLOTS)]
    memories=dict(none='',raw=raw,linked=linked,repeated=raw+'\n'+raw,
        mislinked=render(wrong,True),irrelevant='An unrelated weather station was repainted last year.',
        **{'raw-unpadded':raw})
    if len({raw,linked,memories['repeated'],memories['mislinked']})!=4:raise ValueError('treatment collapse')
    base=tok.decode(tok.encode(json.dumps(context.evidence(row,view),ensure_ascii=False),add_special_tokens=False)[:200])
    def build(memory):
        return ('Evidence from a completed writing episode: '+base+
            '\nTraining memory from a separate recorded episode (not this episode): '+memory+
            '\nPossible recorded actions: '+', '.join(LABELS)+'.\nRecorded action:')
    result={m:build(value) for m,value in memories.items()}
    sizes={m:len(tok.encode(s,add_special_tokens=False)) for m,s in result.items()}
    target=max(sizes.values())+12
    for mode in MODES:
        if mode=='raw-unpadded':continue
        # Explicit irrelevant filler preserves every memory byte. It is an
        # artificial token-matching intervention, measured against raw-unpadded.
        stem,suffix=result[mode].rsplit('\nPossible recorded actions:',1)
        pad='\nPadding:'
        s=stem+pad+'\nPossible recorded actions:'+suffix
        for _ in range(960):
            n=len(tok.encode(s,add_special_tokens=False))
            if n==target:break
            if n>target:raise ValueError('padding overshot token target')
            pad+=' .'
            s=stem+pad+'\nPossible recorded actions:'+suffix
        else:raise ValueError('padding did not converge')
        result[mode]=s
    for mode,s in result.items():
        ids_=tok.encode(s,add_special_tokens=False)
        if len(ids_)>960 or tok.decode(ids_)!=s:raise ValueError('native prompt admission failed')
        if mode!='raw-unpadded' and len(ids_)!=target:raise ValueError('native token lengths differ')
        if memories[mode] not in s:raise ValueError('memory payload erased')
    return result,dict(memory_source=source['key'],memory_component=source['unit'],
        payload_sha256=digest(payload),native_tokens={m:len(tok.encode(s,add_special_tokens=False)) for m,s in result.items()},
        prompt_hashes={m:digest(s) for m,s in result.items()},equal_information_raw_linked=True)


def realization(rows,training,tok):
    checks=[]
    for r in rows:
        for view in ('A','C'):
            rendered,check=prompts(r,training,tok,view)
            if len(set(rendered.values()))!=len(MODES):raise ValueError('complete prompt collision')
            checks.append(dict(key=r['key'],view=view,**check))
    return dict(admitted=bool(rows),rows=len(rows),checks=checks,
        scope='equal raw/linked facts; equal native lengths for primary conditions; exposed source')


def run(rows,training,out,raw,tick):
    model=Detector('gpt2-medium-logrank',raw.parent);records=[]
    expected=read(raw.parent/'jobs/core-v1-lm-admission/ADMISSION.json')['identity']
    if model.identity!=expected:raise ValueError('memory model changed since original admission')
    freeze(out/'REALIZATION.json',realization(rows,training,model.tokenizer))
    for row in rows:
        for view in ('A','C'):
            rendered,check=prompts(row,training,model.tokenizer,view)
            for mode in MODES:
                tick();start=time.perf_counter()
                p,trace=context.conditional(model,rendered[mode],LABELS,prefix_budget=960)
                truth=ACTIONS.index(row['target']['handling'])
                r=dict(key=row['key'],unit=row['unit'],partition=row['partition'],view=view,mode=mode,
                    probabilities=p,truth=truth,n=5,scores=proper_loss(p,truth,5),trace=trace,
                    prompt_sha256=digest(rendered[mode]),memory=check,elapsed_seconds=time.perf_counter()-start)
                freeze(out/'rows'/f"{row['key']}-{view}-{mode}.json",r);records.append(r)
                atomic(out/'PROGRESS.json',dict(at=now(),done=len(records),total=len(rows)*2*len(MODES)))
    result=dict(rows=records,identity=model.identity,protocol='matched-memory-v1',prefix_budget=960)
    freeze(out/'PREDICTIONS.json',result);return result


def summarize(records,expected):
    census={(r['key'],v,m) for r in expected for v in ('A','C') for m in MODES}
    actual=[(r['key'],r['view'],r['mode']) for r in records]
    if len(actual)!=len(set(actual)) or set(actual)!=census:raise ValueError('incomplete or duplicate memory comparison')
    truth_by={r['key']:r for r in expected}
    for r in records:
        target=truth_by[r['key']]
        if r['unit']!=target['unit'] or r['partition']!=target['partition'] or r['truth']!=ACTIONS.index(target['target']['handling']):raise ValueError('paired memory truth differs')
        if proper_loss(r['probabilities'],r['truth'],5)!=r['scores']:raise ValueError('memory score replay differs')
    results={};paired={}
    for part in sorted({r['partition'] for r in records}):
        for view in ('A','C'):
            selected=[r for r in records if r['partition']==part and r['view']==view]
            by={(r['key'],r['mode']):r for r in selected}
            for mode in MODES:
                rs=[r for r in selected if r['mode']==mode]
                results[f'{part}/{view}/{mode}']={k:interval([r['scores'][k] for r in rs],[r['unit'] for r in rs]) for k in ('brier','log_loss','correct')}
                base=[by[(r['key'],'raw')] for r in rs]
                paired[f'{part}/{view}/{mode}-minus-raw']={k:interval([r['scores'][k]-b['scores'][k] for r,b in zip(rs,base)],[r['unit'] for r in rs]) for k in ('brier','log_loss','correct')}
    return dict(status='complete',comparisons=results,paired=paired,attempts=len(records),
        scope='post-exposure descriptive repair; one component per partition; padding is artificial; no mental-goal truth',
        independent_memory='unavailable: one training component; duplicate is not independent')


def handle(card,out,raw,tick):
    args=card['args']
    if card['action']=='healing-memory-admission':
        from transformers import AutoTokenizer
        tok=AutoTokenizer.from_pretrained(cached_model('openai-community/gpt2-medium'),local_files_only=True)
        result=realization(read(raw/args['rows']),read(raw/args['training']),tok)
        freeze(out/'ADMISSION.json',result);return result
    if card['action']=='healing-memory-batch':return run(read(raw/args['rows']),read(raw/args['training']),out,raw,tick)
    records=[r for n in args['blocks'] for r in read(raw/'jobs'/n/'PREDICTIONS.json')['rows']]
    result=summarize(records,read(raw/args['rows']));freeze(out/'ANALYSIS.json',result);return result
