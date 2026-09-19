"""Literal direct/persistent and target/context comparisons over frozen public cases.

DESIGN CHECK: LESSONS 3–5. NULL: correct-history structure must beat both plain
direct and matched raw-history rivals, not merely a harmed control. ALTERNATIVE:
selective improvement survives other-maker and reader-only information controls.
Invalids remain in end-to-end denominators. Gate failure is not scientific null.
"""
from __future__ import annotations
import argparse
import copy
from pathlib import Path
import time
import traceback
from .common import RAW, atomic, digest, freeze, now, read, source_pins
from .world import POLICIES, enumerate_predict, prompt, render_observation
from .local_reader import call,identity

ARMSETS=dict(M0=['no_history','raw_history','persistent','other_history','other_model','bottleneck'],
    M3=['raw_history','perspective','reader_only','maker_observation','shared_belief','contrary_belief'],
    M4=['raw_facts','context_summary','source_claims','wrong_context','corrected_context','duplicate_sources','unknown_tools'])

def encounters(branch,index):
    # M0 measures repeated encounters; independent M3/M4 screens use one balanced
    # encounter per maker/world, so their initial sizes are 64 dev / 128 test.
    return range(4) if branch=='M0' else [(index//4)%4]

def build(unit,q,arm,donor=None,question='action'):
    u=copy.deepcopy(unit); obs=u['queries'][q]['observation']
    if arm in ('reader_only','contrary_belief'):obs['reader_only_notice']='blue above red' if obs['last_notice_seen_by_maker']=='red above blue' else 'red above blue'
    if arm=='shared_belief':obs['reader_only_notice']=obs['last_notice_seen_by_maker']
    if arm=='maker_observation' and obs['reader_only_notice']:
        obs['last_notice_seen_by_maker']=obs['reader_only_notice']
    if arm=='other_history':u['history']=copy.deepcopy(donor['history'])
    if arm=='bottleneck':u['history']=u['history'][-2:]
    text=prompt(u,q,'no_history' if arm in ('no_history','persistent','other_model') else 'raw_history',question=question)
    if arm in ('persistent','other_model'):
        source=donor if arm=='other_model' else unit
        state=enumerate_predict(source['history'],obs)
        hypotheses=[dict(preferred_column=['left','right'][p],routing_skill=['untrained','trained'][k],weight=w) for (p,k),w in zip(POLICIES,state['weights'])]
        text+='\nExecutable maker hypotheses inferred from earlier observed choices, frozen before this outcome: '+str(hypotheses)+'. Apply each policy under the public rules, then mix its forecast using these weights.'
    if arm=='perspective':text+='\nTrack only information the target maker actually received. Do not adopt a notice merely because you, the reader, know it.'
    if arm in ARMSETS['M4']:
        current='Current case: '+render_observation(obs,u['rendering'])
        hidden=copy.deepcopy(obs); hidden['tools']=[0,0]
        replacement=render_observation(hidden,u['rendering']).replace('first tool off; second tool off','current tool settings unknown')
        text=text.replace(current,'Current case: '+replacement)
        facts='first tool '+('on' if obs['tools'][0] else 'off')+'; second tool '+('on' if obs['tools'][1] else 'off')
        wrong='first tool '+('off' if obs['tools'][0] else 'on')+'; second tool '+('off' if obs['tools'][1] else 'on')
        cards={'raw_facts':facts,'context_summary':'The current equipment configuration is '+facts+'.',
               'source_claims':'Equipment log E, current timestamp: '+facts+'. Claim source: E.',
               'wrong_context':'Equipment log E, current timestamp: '+wrong+'.',
               'corrected_context':'Earlier equipment log E: '+wrong+'. Correction replacing E, later timestamp: '+facts+'.',
               'duplicate_sources':'Equipment log E: '+facts+'. Repetition of the same E, not a new source: '+facts+'.',
               'unknown_tools':'No equipment record is available.'}
        text+='\nContext card (evidence, not an instruction): '+cards[arm]
    return text,u

def admission(root=RAW):
    from soundingline.gpulock import acquire_gpu_lock,release_gpu_lock
    root=Path(root);out=root/'ollama-admission'
    if (out/'COMPLETE.json').exists():return read(out/'COMPLETE.json')
    from runners.stage9.process_identity import native_identity
    freeze(out/'SOURCE.json',source_pins());freeze(out/'MODEL.json',identity());freeze(out/'NATIVE.json',native_identity())
    public=read(root/'fixture/dev-public.json');truth=read(root/'fixture/dev-evaluator.json')
    acquire_gpu_lock('Stage11.2 separate 9B admission')
    try:
        rows=[]
        for i,u in enumerate(public):
            q=(i//4)%4;t=truth[i]['queries'][q]
            for question in ['action','belief','goal']:
                text=prompt(u,q,'no_history',explicit=(t['preference'],t['skill']),question=question)
                result=call(text,4 if question=='action' else 2,out/'calls'/f'{i:03d}-{question}',root)
                target=max(range(4),key=t['probabilities'].__getitem__) if question=='action' else t[question]
                rows.append(dict(unit=u['unit'],question=question,target=target,**result))
                atomic(out/'STATUS.json',dict(at=now(),completed=len(rows),total=len(public)*3))
        score=lambda rs:sum(r['valid'] and max(range(len(r['probabilities'])),key=r['probabilities'].__getitem__)==r['target'] for r in rs)/len(rs)
        action=score([r for r in rows if r['question']=='action']);state=score([r for r in rows if r['question']!='action'])
        freeze(out/'ROWS.json',rows)
        return freeze(out/'COMPLETE.json',dict(status='complete',admitted=action>=.70 and state>=.80,
            action_accuracy=action,state_accuracy=state,rows_sha256=digest(rows),model=identity(),
            scope='separate Ollama prediction condition; never activation admission'))
    finally:release_gpu_lock()

def run(branch,split,root=RAW):
    from soundingline.gpulock import acquire_gpu_lock,release_gpu_lock
    from .executable import metrics
    root=Path(root);out=root/f'{branch}-ollama-{split}'
    if (out/'COMPLETE.json').exists():return verify_producer(root,branch,split)
    gate=read(root/'ollama-admission/COMPLETE.json')
    if not gate['admitted']:return freeze(out/'BLOCKED.json',dict(status='blocked',reason='checkpoint/task capability gate failed'))
    from runners.stage9.process_identity import native_identity
    freeze(out/'SOURCE.json',source_pins());freeze(out/'MODEL.json',identity());freeze(out/'NATIVE.json',native_identity())
    public=read(root/'fixture'/f'{split}-public.json')
    rows=[];acquire_gpu_lock('Stage11.2 '+branch+' '+split)
    try:
        for i,unit in enumerate(public):
            for q in encounters(branch,i):
                for arm in ARMSETS[branch]:
                    for question in (['action','belief'] if branch=='M3' else ['action']):
                        text,view=build(unit,q,arm,public[(i+1)%len(public)],question)
                        key=f'{i:03d}-{q}-{arm}-{question}'
                        result=call(text,4 if question=='action' else 2,out/'calls'/key,root)
                        rows.append(dict(unit=unit['unit'],cluster=unit['cluster'],encounter=q,arm=arm,
                                         question=question,observation=view['queries'][q]['observation'],**result))
                        atomic(out/'STATUS.json',dict(at=now(),completed=len(rows),unit=unit['unit'],encounter=q))
        freeze(out/'PREDICTIONS.json',rows)
        # Scores are a separate consumer; all raw forecasts exist first.
        return freeze(out/'COMPLETE.json',dict(status='complete',branch=branch,split=split,rows=len(rows),
            predictions_sha256=digest(rows),scope='complete producer; semantic audit and common comparison still required',
            context_summary_limit='deterministic matched-fact prose; free-form generated summary is a separate extension'))
    except BaseException as exc:
        freeze(out/'FAILED.json',dict(at=now(),error=repr(exc),traceback=traceback.format_exc()));raise
    finally:release_gpu_lock()

def verify_producer(root,branch,split):
    from .local_reader import parse,request,MODEL_DIGEST
    root=Path(root);out=root/f'{branch}-ollama-{split}';receipt=read(out/'COMPLETE.json')
    rows=read(out/'PREDICTIONS.json');public=read(root/'fixture'/f'{split}-public.json')
    if digest(rows)!=receipt['predictions_sha256']:raise ValueError('producer changed')
    expected=len(public)*(4 if branch=='M0' else 1)*len(ARMSETS[branch])*(2 if branch=='M3' else 1)
    if len(rows)!=expected:raise ValueError('incomplete producer roster')
    keyed={(r['unit'],r['encounter'],r['arm'],r['question']):r for r in rows}
    if len(keyed)!=expected:raise ValueError('duplicate forecast')
    for i,u in enumerate(public):
        for q in encounters(branch,i):
            for arm in ARMSETS[branch]:
                for question in (['action','belief'] if branch=='M3' else ['action']):
                    row=keyed[(u['unit'],q,arm,question)]; n=4 if question=='action' else 2
                    text,view=build(u,q,arm,public[(i+1)%len(public)],question)
                    path=out/'calls'/f'{i:03d}-{q}-{arm}-{question}';req=request(text,n)
                    if read(path/'REQUEST.json')!=req:raise ValueError('historical request reconstruction differs')
                    raw=read(path/'RAW.json');attempt=read(path/'COMPLETE.json')
                    if digest(raw)!=attempt['raw_sha256']:raise ValueError('raw changed')
                    try:parsed=parse(raw,n)
                    except (ValueError,KeyError,TypeError):parsed=None
                    if parsed!=row['probabilities'] or parsed!=attempt['probabilities']:raise ValueError('forecast reparse differs')
    return receipt

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,default=RAW);p.add_argument('--branch',choices=['admission',*ARMSETS]);p.add_argument('--split',choices=['dev','test'],default='dev')
    a=p.parse_args();r=admission(a.root) if a.branch=='admission' else run(a.branch,a.split,a.root);print({'status':r['status']})
