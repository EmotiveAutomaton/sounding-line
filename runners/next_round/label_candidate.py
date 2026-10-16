"""Full exposed-battery check of the selected Qwen label-contract candidate.

DESIGN CHECK: LESSONS 2-5 and CONTROLS 1-3 re-read 2026-10-16.
NULL: constant/malformed/wrong labels fail unchanged full and per-label gates.
ALTERNATIVE: correct known-answer labels pass, including mixed person and empty tags.
All gates apply per question; no automatic feature/engine/scientific promotion.
"""
import os
for _name in ('OMP_NUM_THREADS','MKL_NUM_THREADS','OPENBLAS_NUM_THREADS','NUMEXPR_NUM_THREADS'):
    os.environ[_name]='1'
import argparse,json,threading,time,traceback
from . import label_contract as lc
from .queue import resource_snapshot,require_resources
from runners.stage14.common import REPO,read,freeze,atomic,pins,check_pins,filehash,digest,now,limits
from runners.stage9.process_identity import native_identity

ROOT=REPO/'results/phase_2_4_stage_15/raw/label-candidate-v1'
QUESTIONS=('Q6','Q10')
MODEL=lc.lm.MODELS['qwen9']

def roster():
    Transcriber,_,constructed,_=lc.lm.engine()
    class Capture:
        model_id='prompt-capture';settings={}
        def complete(self,prompt,schema):
            self.prompt,self.schema=prompt,schema
            return dict(text=json.dumps(dict(answer=self.label)))
    out=[];c=Capture();t=Transcriber(c,lc.NoCache())
    for q in QUESTIONS:
        items=constructed(q)
        assert len(items)==200
        for item in items:
            c.label=item['expected'];t.ask(q,context=item['context'],text=item['text'],before=item['before'],admission_test=True)
            out.append(dict(slot=len(out),target=item['id'],question=q,label=item['expected'],text=item['text'],context=item['context'],item=item,
                model='qwen9',arm='defined',repeat=0,context_kind='canonical',prompt=lc.SCOPE+lc.DEFINITIONS[q]+c.prompt,schema=c.schema))
    assert len(out)==400 and len({digest([r['prompt'],r['schema']]) for r in out})==400
    return out

def summarize(rows,items):
    if len(rows)!=400 or len(items)!=400 or len({r['slot'] for r in rows})!=400:raise ValueError('incomplete or duplicate roster')
    byslot={r['slot']:r for r in rows}
    for item in items:
        expected={k:v for k,v in item.items() if k not in ('prompt','schema','text','context')}
        row=byslot[item['slot']]
        if any(row.get(k)!=v for k,v in expected.items()):raise ValueError('changed identity')
        if row['correct']!=(row['valid'] and row['answer']==row['label']):raise ValueError('changed score')
    _,battery,_,_=lc.lm.engine();results={}
    for q in QUESTIONS:
        subset=[i for i in items if i['question']==q]
        lookup={digest([i['context'],i['text'],i['item']['before']]):byslot[i['slot']] for i in subset}
        class Saved:
            pin=digest(dict(model=MODEL,settings=lc.lm.SETTINGS,runtime=lc.lm.VERSION,prompts=[i['prompt'] for i in subset],schemas=[i['schema'] for i in subset],candidate='label-candidate-v1'))
            def ask(self,question_id,*,context,text,before,admission_test):
                assert question_id==q and admission_test
                r=lookup[digest([context,text,before])]
                if not r['valid']:raise ValueError('retained invalid whole response')
                return dict(answer=r['answer'])
        source=[i['item'] for i in subset]
        results[q]=lc.lm.gate_summary(battery(Saved(),q,source),source)
    return dict(questions=results,candidate_only=True,feature_admission=False,engine_admission=False,scientific_admission=False,exposed_templates=True,selection='Qwen scoped-plus-definition selected from complete label-contract diagnostic')

def replay(root=ROOT):
    plan=read(root/'PLAN.json');check_pins(plan['pins']);done=read(root/'COMPLETE.json')
    if done['plan_sha256']!=filehash(root/'PLAN.json'):raise ValueError('plan changed')
    for rel,h in done['outputs'].items():
        if filehash(root/rel)!=h:raise ValueError('output changed')
    items=read(root/'ITEMS.json')
    if items!=roster():raise ValueError('roster changed')
    rows=[]
    for item in items:
        b=lc.lm.Replay(MODEL,root/'calls'/f'{item["slot"]:04d}')
        try:response=b.complete(item['prompt'],item['schema'])
        except ValueError as exc:
            if str(exc)!='unfinished or unexpected thinking response':raise
            response=dict(text='__invalid_returned_response__')
        outcome=lc.parse(item,response)
        if outcome!=read(root/'outcomes'/f'{item["slot"]:04d}.json'):raise ValueError('outcome changed')
        rows.append(outcome)
    if len(list((root/'calls').glob('*/*/REQUEST.json')))!=400:raise ValueError('unaccounted calls')
    if summarize(rows,items)!=read(root/'SUMMARY.json'):raise ValueError('summary changed')
    return dict(at=now(),status='VERIFIED',calls=400,complete_sha256=filehash(root/'COMPLETE.json'),scientific_admission=False)

def prepare(service_pid):
    limits();require_resources(resource_snapshot());lc.lm.inspect(MODEL)
    if (ROOT/'PLAN.json').exists() or (REPO/'results/.literal-cpu.lock').exists():raise ValueError('already prepared or leased')
    previous=read(lc.ROOT/'PLAN.json');check_pins(previous['pins'])
    landing=read(lc.ROOT/'LANDED.json')
    if not landing['full_write_through'] or landing['complete_sha256']!=filehash(lc.ROOT/'COMPLETE.json'):raise ValueError('unlanded prerequisite')
    service=native_identity(service_pid)
    if service!=previous['service_native']:raise ValueError('service drift')
    freeze(ROOT/'ITEMS.json',roster())
    sources=[ROOT/'ITEMS.json',lc.ROOT/'COMPLETE.json',lc.ROOT/'LANDED.json',REPO/'results/phase_2_4_stage_15/LABEL_CONTRACT_PUBLIC.json',REPO/'runners/next_round/label_candidate.py',REPO/'tests/test_next_round_label_candidate.py',REPO/'docs/design/stage-15/LABEL_CANDIDATE_BATTERY.md']
    sourcepins=dict(previous['pins']);sourcepins.update(pins(sources))
    freeze(ROOT/'PLAN.json',dict(at=now(),pins=sourcepins,model=MODEL,service_native=service,maximum_calls=400,max_wall_seconds=21600,provider_calls=0,scientific_admission=False))

def run(root=ROOT):
    limits();plan=read(root/'PLAN.json');check_pins(plan['pins']);require_resources(resource_snapshot())
    if native_identity(plan['service_native']['pid'])!=plan['service_native']:raise RuntimeError('service drift')
    with (root/'ATTEMPT.claim').open('x',encoding='utf8') as f:f.write(now()+'\n')
    freeze(root/'OWNER.json',dict(at=now(),native=native_identity(),plan_sha256=filehash(root/'PLAN.json')))
    lease=REPO/'results/.literal-cpu.lock';token=json.dumps(native_identity()).encode()
    fd=os.open(lease,os.O_WRONLY|os.O_CREAT|os.O_EXCL);os.write(fd,token);os.close(fd)
    started=time.time();stop=threading.Event();backend=None
    def deadline():
        if stop.wait(plan['max_wall_seconds']):return
        atomic(root/'FAILED.json',dict(status='FAILED',at=now(),reason='wall ceiling; lease retained'));os._exit(124)
    threading.Thread(target=deadline,daemon=True).start()
    try:
        while not (root/'MONITOR_READY.json').exists():
            if time.time()-started>60:raise TimeoutError('monitor absent')
            time.sleep(.25)
        if read(root/'MONITOR_READY.json')['owner_sha256']!=filehash(root/'OWNER.json'):raise ValueError('monitor mismatch')
        lc.lm.engine();lc.lm.inspect(MODEL);items=read(root/'ITEMS.json');rows=[]
        def guard():
            check_pins(plan['pins']);resources=resource_snapshot();require_resources(resources)
            if native_identity(plan['service_native']['pid'])!=plan['service_native']:raise RuntimeError('service drift')
            if lease.read_bytes()!=token:raise RuntimeError('lease drift')
            if backend.calls>=plan['maximum_calls']:raise RuntimeError('call ceiling')
            atomic(root/'PROGRESS.json',dict(at=now(),completed_calls=backend.calls,maximum_calls=plan['maximum_calls'],resources=resources))
        backend=lc.SlottedBackend(MODEL,root/'calls',guard)
        for item in items:
            backend.slot=item['slot'];out=lc.parse(item,backend.complete(item['prompt'],item['schema']));rows.append(out)
            freeze(root/'outcomes'/f'{item["slot"]:04d}.json',out)
        backend.close();check_pins(plan['pins'])
        if backend.calls!=400 or lease.read_bytes()!=token:raise RuntimeError('endpoint mismatch')
        freeze(root/'SUMMARY.json',summarize(rows,items))
        paths=[root/'ITEMS.json',root/'SUMMARY.json',*sorted((root/'outcomes').glob('*.json')),*sorted((root/'calls').rglob('*.json'))]
        lease.unlink()
        freeze(root/'COMPLETE.json',dict(status='COMPLETE',at=now(),calls=400,wall_seconds=time.time()-started,plan_sha256=filehash(root/'PLAN.json'),outputs={p.relative_to(root).as_posix():filehash(p) for p in paths},provider_calls=0,scientific_admission=False,write_through_required=True))
        freeze(root/'REPLAY.json',replay(root))
    except BaseException as exc:
        freeze(root/'FAILED.json',dict(status='FAILED',at=now(),error=str(exc),traceback=traceback.format_exc(),lease_retained=lease.exists()));raise
    finally:stop.set()

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['prepare','run','replay']);p.add_argument('--service-pid',type=int);a=p.parse_args()
    if a.action=='prepare':prepare(a.service_pid)
    elif a.action=='run':run()
    else:print(json.dumps(replay()))
