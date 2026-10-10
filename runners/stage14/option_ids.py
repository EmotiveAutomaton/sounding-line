"""SL6 raw generated-token option IDs; never arbitrary prompt likelihood.

DESIGN CHECK: LESSONS 3-5, CONTROLS, SL6. NULL: incomplete legal support,
order sensitivity or incoherent complements refuses admission. ALTERNATIVE:
complete generated-token support reads explicit controls coherently. Report the
conditional legal-token distribution and its original mass separately. No claim
that a missing top-20 token has zero probability. API: ollama/ollama api/types.go.
"""
import math,time
import numpy as np
from .common import freeze,read,digest,now
from .local import api,ready,service,CONTEXT
from .adaptive_v2 import proper
from runners.stage12.local_api import snapshot

def decode(response,n):
    if response.get('done') is not True or not response.get('logprobs'):
        raise ValueError('generated-token logprobs unavailable')
    first=response['logprobs'][0]; support={}
    for row in [first]+first.get('top_logprobs',[]):
        token=row['token']
        if token in [str(i+1) for i in range(n)]:
            value=float(row['logprob'])
            if not math.isfinite(value) or value>0:raise ValueError('invalid log probability')
            if token in support and support[token]!=value:raise ValueError('conflicting token probability')
            support[token]=value
    if len(support)!=n:raise ValueError('complete legal option support absent from top-20')
    p=[math.exp(support[str(i+1)]) for i in range(n)];mass=sum(p)
    if not 0<mass<=1.00001:raise ValueError('invalid legal mass')
    return dict(probabilities=[v/mass for v in p],legal_mass=mass,raw_logprobs=support)

def generate(req,path,state,card):
    if path.exists():raise RuntimeError('prior request directory: inspect, never retry')
    check=ready(card['model'],card['model_digest'],card['memory_MiB'])
    if not check['ready']:raise RuntimeError('resource changed before option request')
    freeze(path/'REQUEST.json',req);start=time.monotonic()
    freeze(path/'DISPATCH.json',dict(at=now(),binding=digest(req),snapshot=check))
    try:r=api('/api/generate',req,timeout=600)
    except BaseException:state['uncertain']=True;raise
    freeze(path/'RAW.json',r)
    freeze(path/'RECEIPT.json',dict(at=now(),wall_seconds=time.monotonic()-start,request_sha256=digest(req),raw_sha256=digest(r),
        timings_ns={k:r.get(k) for k in ('load_duration','prompt_eval_duration','eval_duration','total_duration')},output_tokens=r.get('eval_count')))
    resident=api('/api/ps')['models'];snap=snapshot();freeze(path/'AFTER.json',dict(resident=resident,snapshot=snap))
    if len(resident)!=1 or resident[0].get('digest')!=card['model_digest'] or resident[0].get('size')!=resident[0].get('size_vram') or resident[0].get('context_length')!=CONTEXT:raise RuntimeError('full residency not verified')
    if snap['free_MiB']<768 or snap['temperature_C']>78:raise RuntimeError('GPU reserve/temperature lost')
    if r.get('prompt_eval_count',0)+r.get('eval_count',0)>CONTEXT:raise RuntimeError('context overflow')
    return r

def run(card,out,raw,tick):
    actions=['accept','edit','dismiss','ignore'];rows=[];serial=0
    freeze(out/'SERVER.json',api('/api/version'))
    with service(out,card) as state:
        for action in actions:
            for query in actions:
                for neg in (False,True):
                    for labels in (['yes','no'],['no','yes']):
                        answer='yes' if (action!=query if neg else action==query) else 'no'
                        prompt=f'The recorded handling was {action}. Was the handling {"not " if neg else ""}{query}?\n'
                        prompt+='\n'.join(f'[{i+1}] {label}' for i,label in enumerate(labels))+'\nBest answer: ['
                        req=dict(model=card['model'],prompt=prompt,raw=True,stream=False,think=False,logprobs=True,top_logprobs=20,keep_alive='10m',options=dict(num_ctx=CONTEXT,num_predict=1,temperature=0,seed=141010,num_thread=1,top_k=0,top_p=1,repeat_penalty=1))
                        r=generate(req,out/'calls'/f'{serial:03d}',state,card);serial+=1
                        try:d=decode(r,2);error=None
                        except (ValueError,TypeError,KeyError) as e:d=dict(probabilities=[],legal_mass=None);error=str(e)
                        rows.append(dict(action=action,query=query,negated=neg,labels=labels,truth=labels.index(answer),readout=d,error=error,score=proper(d['probabilities'],labels.index(answer))))
                tick(dict(completed_calls=serial,total_calls=64))
    gaps=[];partition=[]
    for action in actions:
        for labels in (['yes','no'],['no','yes']):
            block=[r for r in rows if r['action']==action and r['labels']==labels]
            for query in actions:
                pair=[r for r in block if r['query']==query]
                if all(r['score']['valid'] for r in pair):gaps.append(abs(sum(r['readout']['probabilities'][labels.index('yes')] for r in pair)-1))
            positive=[r for r in block if not r['negated']]
            if all(r['score']['valid'] for r in positive):partition.append(abs(sum(r['readout']['probabilities'][labels.index('yes')] for r in positive)-1))
    valid=sum(r['score']['valid'] for r in rows);accuracy=float(np.mean([r['score']['correct'] for r in rows]))
    summary=dict(calls=len(rows),valid=valid,accuracy=accuracy,mean_half_brier=float(np.mean([r['score']['half_brier'] for r in rows])),mean_negation_gap=float(np.mean(gaps)) if gaps else None,max_partition_gap=max(partition) if partition else None,scope='constructed literal facts; probabilities conditional on complete legal first-token support; not sequence likelihood or human admission')
    freeze(out/'PREDICTIONS.json',rows);freeze(out/'SUMMARY.json',summary)
    freeze(out/'ADMISSION.json',dict(admitted=valid==64 and accuracy>=.95 and len(gaps)==32 and max(gaps)<=.1 and len(partition)==8 and max(partition)<=.1,scope='literal option-ID controls only'))
