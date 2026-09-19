"""Finite state-query, sourced-summary and distinct history/combinations tests.

DESIGN CHECK: LESSONS 3-5, CONTROLS 6. NULL: extra prose or persistent state can
harm relative to the same public history. ALTERNATIVE: benefit must survive raw
history and exact Bayesian rivals. Model mismatch is reported, not suppressed.
No new units are claimed for multiple encounters of the same constructed maker.
"""
from __future__ import annotations
import argparse
import copy
import json
import random
import time
from pathlib import Path
from .common import RAW,atomic,digest,freeze,gpu_service,now,read,source_pins
from .world import POLICIES,decode,distribution,enumerate_predict,make_unit,observe,prompt,reference
from . import repair
from . import local_reader as transport
from .model_study import build
from .consumer import measures,summarize,target_for


def long_unit(split,index):
    u,t=make_unit(split,index);rng=random.Random(8112+index+(10000 if split=='test' else 0))
    p,k=t['queries'][0]['preference'],t['queries'][0]['skill']
    history=[]
    for step in range(36):
        g,b=rng.randrange(2),rng.randrange(2);tools=[rng.randrange(2),rng.randrange(2)]
        obs=observe(g,b,u['world_family'],tools)
        action=rng.choices(range(4),weights=distribution(p,k,g,b,u['world_family'],tools))[0]
        history.append(dict(sequence=step,observation=obs,action=action))
    u['history']=history
    # The missing fourth goal/belief combination, after a delay with unrelated
    # observations. Persistent expertise is unchanged. This is not a new maker.
    obs=copy.deepcopy(u['queries'][2]['observation'])
    obs['requested_item']=u['queries'][0]['observation']['requested_item']
    u['queries']=[dict(encounter=0,observation=obs)]
    g,b=decode(obs);probs=reference(p,k,g,b,obs['world_family'],obs['tools'])
    truth=dict(unit=u['unit'],encounter=0,preference=p,skill=k,goal=g,belief=b,
               probabilities=probs,action=rng.choices(range(4),weights=probs)[0])
    return u,truth


def history_text(unit,arm,donor=None):
    u=copy.deepcopy(unit)
    text=prompt(u,0,'no_history')
    history=u['history']
    if arm=='other_history':history=donor['history']
    if arm=='retrieval_12':history=history[-12:]
    if arm=='no_history':history=[]
    if arm=='persistent':
        fit=enumerate_predict(history,u['queries'][0]['observation'])
        model=[dict(preference=['left','right'][p],skill=['untrained','trained'][k],weight=w) for (p,k),w in zip(POLICIES,fit['weights'])]
        text+='\nFrozen executable hypotheses from earlier history: '+json.dumps(model)
    else:
        entries=[]
        for e in history:
            obs=e['observation'];a,b=obs['tools']
            entries.append(f"{e['sequence']}: wanted {obs['requested_item']}; saw {obs['last_notice_seen_by_maker']}; tools {a}/{b} (1=on,0=off); chose {'ABCD'[e['action']]}")
        text+='\nEarlier history, in order:\n'+'\n'.join(entries)
    text+='\nA delay included unrelated room observations. The CURRENT request above supersedes older goals; routing skill is stable.'
    return text,u


def summary_call(obs,path,root):
    path=Path(path);facts=[dict(tool=tool,on=bool(obs['tools'][i]),source='E') for i,tool in enumerate(['first','second'])]
    schema=dict(type='object',properties=dict(summary=dict(type='string'),claims=dict(type='array',items=dict(type='object',
        properties=dict(tool=dict(type='string',enum=['first','second']),on=dict(type='boolean'),source=dict(type='string',enum=['E'])),
        required=['tool','on','source'],additionalProperties=False),minItems=2,maxItems=2)),required=['summary','claims'],additionalProperties=False)
    req=dict(model=transport.MODEL,stream=False,think=False,format=schema,keep_alive='2m',
        options=dict(temperature=0,seed=112,num_ctx=8192,num_predict=256,num_thread=4),
        messages=[dict(role='user',content='Summarize this current equipment record in one sentence, then list its two source-linked claims. Do not infer maker traits or actions. Facts: '+json.dumps(facts)+' Schema: '+json.dumps(schema))])
    if (path/'COMPLETE.json').exists():
        saved=read(path/'COMPLETE.json');raw=read(path/'RAW.json')
        if read(path/'REQUEST.json')!=req or digest(raw)!=saved['raw_sha256']:raise ValueError('summary changed')
    else:
        if (path/'REQUEST.json').exists():raise RuntimeError('unfinished summary transport; inspect before retry')
        freeze(path/'REQUEST.json',req);start=time.monotonic()
        try:
            with gpu_service(root,'context-summary:'+path.name,330):raw=transport.api('/api/chat',req,timeout=300)
        except BaseException as exc:
            freeze(path/'FAILED.json',dict(at=now(),error=repr(exc)))
            freeze(Path(root)/'charges'/('uncertain-summary-'+digest(req)+'.json'),dict(reserved_seconds=330,elapsed_seconds=330,state='uncertain'));raise
        freeze(path/'RAW.json',raw);saved=dict(raw_sha256=digest(raw),seconds=time.monotonic()-start)
    try:
        body=json.loads(raw['message']['content'])
        valid=raw.get('done_reason')=='stop' and isinstance(body['summary'],str) and isinstance(body['claims'],list)
        supported=valid and sorted(body['claims'],key=lambda x:x['tool'])==sorted(facts,key=lambda x:x['tool'])
    except (ValueError,KeyError,TypeError):body=None;valid=False;supported=False
    result=dict(saved,body=body,valid=valid,claims_supported=supported,
        support_limit='structured claim agreement only; free prose entailment is not mechanically certified')
    return freeze(path/'COMPLETE.json',result)


def requests(kind,unit,donor,index,summary=None):
    q=(index//4)%4
    if kind=='states':
        for question in ['belief','goal','skill','preference']:
            for arm in ['no_history','raw_history','persistent']:
                text,view=build(unit,q,arm,donor,question)
                yield arm,question,q,text,view
    elif kind=='history':
        for arm in ['no_history','raw_history','retrieval_12','persistent','other_history']:
            text,view=history_text(unit,arm,donor)
            yield arm,'action',0,text,view
    elif kind=='summary':
        text,view=build(unit,q,'unknown_tools',donor,'action')
        obs=unit['queries'][q]['observation']
        facts='first tool '+('on' if obs['tools'][0] else 'off')+'; second tool '+('on' if obs['tools'][1] else 'off')
        cards={'raw_history':facts,'generated_summary':summary['body']['summary'] if summary['valid'] else None,
               'source_linked_summary':(summary['body']['summary']+' Source-linked claims: '+json.dumps(summary['body']['claims'])) if summary['valid'] else None}
        for arm,card in cards.items():yield arm,'action',q,None if card is None else text+'\nCurrent context evidence: '+card,view
    elif kind=='repeat':
        for arm in ['raw_history','unchanged_repeat']:
            text,view=build(unit,q,'raw_history',donor,'action')
            yield arm,'action',q,text,view


def run(kind,split,root=RAW):
    from soundingline.gpulock import acquire_gpu_lock,release_gpu_lock
    from runners.stage9.process_identity import native_identity
    root=Path(root);out=root/'repair-v1'/f'extension-{kind}-{split}'
    gate=read(root/'repair-v1/ollama-admission/COMPLETE.json')
    if gate.get('admitted') is not True:raise RuntimeError('repaired reader not admitted')
    public=read(root/'fixture'/f'{split}-public.json')
    if kind=='history':
        pairs=[long_unit(split,i) for i in range(len(public))]
        public=[u for u,t in pairs];truth=[dict(unit=u['unit'],queries=[t]) for u,t in pairs]
        freeze(out/'PUBLIC.json',public);freeze(out/'EVALUATOR.json',truth)
    else:truth=None
    fresh=not (out/'COMPLETE.json').exists()
    if fresh:freeze(out/'SOURCE.json',source_pins());freeze(out/'NATIVE.json',native_identity());freeze(out/'MODEL.json',transport.identity())
    rows=[];summaries=[];acquire_gpu_lock('Stage11.2 extension '+kind)
    try:
        for i,u in enumerate(public):
            summary=None
            if kind=='summary':
                summary=summary_call(u['queries'][(i//4)%4]['observation'],out/'summaries'/f'{i:03d}',root);summaries.append(summary)
            for arm,question,q,text,view in requests(kind,u,public[(i+1)%len(public)],i,summary):
                result=(repair.call(text,4 if question=='action' else 2,out/'calls'/f'{i:03d}-{arm}-{question}',root)
                        if text is not None else dict(valid=False,probabilities=None,seconds=0,error='upstream summary invalid',cost={}))
                rows.append(dict(unit=u['unit'],cluster=u['cluster'],encounter=q,arm=arm,question=question,
                    observation=view['queries'][q]['observation'],**result))
                atomic(out/'STATUS.json',dict(at=now(),completed=len(rows),unit=u['unit']))
        freeze(out/'PREDICTIONS.json',rows)
        if truth is None:truth=read(root/'fixture'/f'{split}-evaluator.json')
        keyed={(u['unit'],t['encounter']):t for u in truth for t in u['queries']}
        scored=[dict(r,score=measures(r['probabilities'],*target_for(r,keyed[(r['unit'],r['encounter'])]))) for r in rows]
        comparison=summarize(scored,'raw_history')
        freeze(out/'COMPARISON.json',comparison)
        return freeze(out/'COMPLETE.json',dict(status='complete',kind=kind,split=split,rows=len(rows),
            predictions_sha256=digest(rows),comparison_sha256=digest(comparison),
            summary_claim_support=None if not summaries else dict(n=len(summaries),supported=sum(s['claims_supported'] for s in summaries)),
            scope='constructed worlds, repeated units share original clusters; free-form summary source support checked separately'))
    finally:release_gpu_lock()


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,default=RAW);p.add_argument('--kind',choices=['states','summary','history','repeat'],required=True);p.add_argument('--split',choices=['dev','test'],required=True)
    a=p.parse_args();print(run(a.kind,a.split,a.root)['status'])
