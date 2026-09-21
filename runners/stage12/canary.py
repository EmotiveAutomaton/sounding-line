"""Current measured local-reader admission, separate from scientific comparison.

DESIGN CHECK: LESSONS 3-5. NULL: malformed or wrong known-answer outputs cannot
admit the instrument; inadequate hardware performs no inference. ALTERNATIVE:
complete matched classes may establish current reference timing, not a cause of
earlier slowdown or competence on unrelated human questions. Five representative
calls per class, one repeated request, one warm-up. A versioned shorter timeout
may fit remaining diagnostic allowance; cases and acceptance gates never shrink.
"""
from collections import Counter
from .common import REPO,read,freeze,filehash,digest,distribution
from .local_api import MODEL,MODEL_DIGEST,request,call,service,readiness

PROFILE=dict(model=MODEL,model_digest=MODEL_DIGEST,context=8192,output=512,threads=2,
             model_memory_MiB=7000,free_buffer_MiB=768)


def compile_inputs(output_interface=None):
    from runners.stage11_2.world import make_unit,prompt,reference,decode
    rows=[];probes={};used=set()
    for index in range(32):
        u,t=make_unit('dev',index)
        for q,s in enumerate(t['queries']):
            winner=max(range(4),key=s['probabilities'].__getitem__)
            if winner not in probes and u['unit'] not in used:
                probes[winner]=(u,t,q);used.add(u['unit']);break
        if len(probes)==4:break
    if len(probes)!=4:raise ValueError('known-answer canary lacks one action class')
    # Four action winners and an unchanged-input repeat in each class.
    for kind in ('forecast','account'):
        for winner in [0,1,2,3,0]:
            u,t,q=probes[winner];s=t['queries'][q];obs=u['queries'][q]['observation']
            text=prompt(u,q,explicit=(s['preference'],s['skill']))
            text=text.replace('Answer only A, B, C, or D.','Return probabilities in A, B, C, D order.')
            g,b=decode(obs);truth=reference(s['preference'],s['skill'],g,b,obs['world_family'],obs['tools'])
            rows.append(dict(id=f'{kind}-{len(rows)}',call_class=kind,source_id=u['unit'],
                request=request(text,4,kind),truth=truth))
    from .output_interface import rows_for_card
    return rows_for_card(rows, dict(output_interface=output_interface))


def capacity(out,card,pulse,raw):
    state=readiness(PROFILE);freeze(out/'CAPACITY.json',state)
    if state['ready']:freeze(out/'RESOURCE_READY.json',dict(status='complete',profile=PROFILE,inspection=state))
    # A complete inspection can report not ready. It is not reader admission.
    pulse(phase='resource-inspection')
    return dict(status='complete',kind='infrastructure',ready=state['ready'],reason=state['reason'],
        controls=dict(no_inference=True,actual_residency_checked=True,model_identity_verified=True),
        files={'CAPACITY.json':filehash(out/'CAPACITY.json')})


def run(out,card,pulse,raw):
    rows=compile_inputs(card.get('output_interface'))
    if digest(rows)!=card['requests_digest']:raise ValueError('canary input freeze differs')
    allowance=card.get('call_allowance_seconds',330)
    if type(allowance) not in (int,float) or not 60<=allowance<=330:
        raise ValueError('invalid frozen canary call allowance')
    reservation=150+len(rows)*allowance+120
    if any(card.get(k,0)<reservation for k in ('gpu_seconds','diagnostic_gpu_seconds','wall_seconds')):
        raise ValueError('canary reservation cannot contain complete fixed roster')
    freeze(out/'REQUESTS_WITH_KNOWN_TARGETS.json',rows)
    values=[]
    profile=card.get('profile',PROFILE)
    with service(out,profile,raw,diagnostic=True) as state:
        pulse(phase='warmup')
        warm=request('Known-answer task: A is correct and B, C, D are impossible. Label order A, B, C, D.',4)
        from .output_interface import adapt
        warm=adapt(warm,card.get('output_interface'))
        call(warm,4,out/'calls/warmup',state,raw,diagnostic=True,allowance=150)
        for i,row in enumerate(rows):
            pulse(phase='canary',completed=i,total=len(rows))
            value=call(row['request'],4,out/'calls'/row['id'],state,raw,diagnostic=True,allowance=allowance)
            values.append(dict(id=row['id'],call_class=row['call_class'],request_digest=digest(row['request']),
                score=distribution(value['probabilities'],row['truth']),call=value))
    # Full unit only. Half-Brier remains a probability score, not a binary gate.
    from .audit import quantiles
    groups={}
    for kind in ('forecast','account'):
        own=[r for r in values if r['call_class']==kind]
        groups[kind]=dict(n=len(own),wall=quantiles([r['call']['wall_seconds'] for r in own]),
            valid=sum(r['score']['valid'] for r in own),correct=sum(r['score']['accuracy'] for r in own),
            repeated_request_identical=own[0]['request_digest']==own[-1]['request_digest'],
            repeat_output_equal=own[0]['call']['probabilities']==own[-1]['call']['probabilities'],
            input_tokens=[r['call']['prompt_tokens'] for r in own],output_tokens=[r['call']['output_tokens'] for r in own])
    # Four distinct source probes plus one repeat: a structural screen only.
    admitted=all(g['valid']==5 and g['correct']>=4 for g in groups.values())
    report=dict(status='complete',kind='infrastructure',groups=groups,reader_admitted=admitted,
        target='explicit-state constructed task only; no human or hidden-state/HF capability admitted',
        reference_status='current measured matched reference with recorded hardware, not causal attribution',
        future_pause='p90 over twice this matched class after context/output and actual token-length matching; inspect rather than retry',
        diagnostic_limit_seconds=3600,controls=dict(all_declared_requests_replayed=True,known_answer_coverage=True,
            classes_separate=True,repeat_request_identity=all(g['repeated_request_identical'] for g in groups.values())))
    freeze(out/'ROWS.json',values);freeze(out/'ADMISSION.json',report)
    if admitted:
        ready=dict(status='complete',profile=profile,groups=groups,scope=report['target'])
        if card.get('output_interface'):ready['output_interface']=card['output_interface']
        freeze(out/'READER_READY.json',ready)
    report['files']={n:filehash(out/n) for n in ('ROWS.json','ADMISSION.json')}
    return report
