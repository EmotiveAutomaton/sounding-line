"""Finite fixed-model extension of F4, with complete-question offline replay.

DESIGN CHECK: LESSONS 2-5, CONTROLS 1-3 read 2026-10-15.
NULL: malformed/constant/wrong answers fail unchanged complete-question gates.
ALTERNATIVE: literal answers pass known-answer and per-label controls.
Unknown transport/residency/pins stop; constructed success never admits science.
"""
import os
for _name in ('OMP_NUM_THREADS','MKL_NUM_THREADS','OPENBLAS_NUM_THREADS','NUMEXPR_NUM_THREADS'):
    os.environ[_name]='1'
import argparse,json,threading,time,traceback
from pathlib import Path
from .literal_admission import engine,api,gate_summary,VERSION
from .engine_interface_v2 import CAPSULE
from .queue import resource_snapshot,require_resources
from runners.stage14.common import REPO,read,freeze,atomic,pins,check_pins,filehash,digest,now,limits
from runners.stage9.process_identity import native_identity

ROOT=REPO/'results/phase_2_4_stage_15/raw/f4-models-v1'
QUESTIONS=('Q7','Q3','Q4','Q5','Q8','Q9','Q1','Q6','Q10')
MODELS={
    'llama3':dict(name='llama3.2:3b',digest='a80c4f17acd55265feec403c7aef86be0c25983ab279d83f3bcd3abbcb5b8b72',think=None),
    'qwen9':dict(name='qwen3.5:9b',digest='6488c96fa5faab64bb65cbd30d4289e20e6130ef535a93ef9a49f42eda893ea7',think=False),
}
SETTINGS=dict(temperature=0,seed=0,num_predict=256,num_gpu=0,num_thread=1,num_ctx=8192)

def request(model,prompt,schema):
    body=dict(model=model['name'],prompt=prompt,format=schema,stream=False,keep_alive=120,options=SETTINGS)
    if model['think'] is not None:body['think']=model['think']
    return body

def inspect(model,owned=False):
    if api('/api/version')['version']!=VERSION:raise RuntimeError('runtime drift')
    matches=[m for m in api('/api/tags')['models'] if m['name']==model['name'] and m['digest']==model['digest']]
    if len(matches)!=1:raise RuntimeError('model digest drift')
    residents=api('/api/ps')['models']
    if residents and (not owned or len(residents)!=1 or residents[0]['digest']!=model['digest']
                     or residents[0].get('size_vram')!=0 or residents[0].get('context_length')!=8192):
        raise RuntimeError('foreign or non-CPU resident')
    return dict(version=VERSION,model=model,resident=residents)

def text_response(raw):
    if not raw.get('done'):raise RuntimeError('unknown completion')
    if raw.get('done_reason')!='stop' or raw.get('thinking'):
        raise ValueError('unfinished or unexpected thinking response')
    return dict(text=raw['response'],logprobs=None)

class Backend:
    def __init__(self,model,folder,guard):
        self.model=model;self.folder=folder;self.guard=guard
        self.model_id=model['name']+'@'+model['digest']
        self.settings=dict(SETTINGS,runtime=VERSION,think=model['think'],transport='s15-fixed-models-v1')
        self.calls=0;self.owned=False;self.uncertain=False
    def complete(self,prompt,schema):
        self.guard();inspect(self.model,self.owned)
        body=request(self.model,prompt,schema);dest=self.folder/digest(body)
        if dest.exists():raise RuntimeError('duplicate dispatch refused')
        freeze(dest/'REQUEST.json',body)
        freeze(dest/'DISPATCH.json',dict(at=now(),native=native_identity()))
        self.uncertain=True;start=time.time();raw=api('/api/generate',body)
        freeze(dest/'RAW.json',raw)
        freeze(dest/'RECEIPT.json',dict(at=now(),wall_seconds=time.time()-start,raw_sha256=filehash(dest/'RAW.json')))
        self.owned=True;resident=inspect(self.model,True);freeze(dest/'RESIDENCY.json',resident)
        if not resident['resident'] or not raw.get('done'):raise RuntimeError('unknown completion/residency')
        self.uncertain=False;self.calls+=1
        return text_response(raw)
    def close(self):
        if self.uncertain:raise RuntimeError('uncertain request retains lease')
        if self.owned:
            inspect(self.model,True);api('/api/generate',dict(model=self.model['name'],keep_alive=0),timeout=60)
            if api('/api/ps')['models']:raise RuntimeError('owned resident failed to unload')

class Replay(Backend):
    def __init__(self,model,folder):
        super().__init__(model,folder,lambda:None);self.seen=set()
    def complete(self,prompt,schema):
        body=request(self.model,prompt,schema);dest=self.folder/digest(body)
        if dest in self.seen:raise RuntimeError('repeated replay request')
        self.seen.add(dest)
        if read(dest/'REQUEST.json')!=body:raise RuntimeError('wire mismatch')
        raw=read(dest/'RAW.json');receipt=read(dest/'RECEIPT.json');resident=read(dest/'RESIDENCY.json')
        if receipt['raw_sha256']!=filehash(dest/'RAW.json'):raise RuntimeError('raw receipt mismatch')
        rs=resident['resident']
        if resident['version']!=VERSION or resident['model']!=self.model or len(rs)!=1 or rs[0]['digest']!=self.model['digest'] or rs[0].get('size_vram')!=0 or rs[0].get('context_length')!=8192:
            raise RuntimeError('retained residency mismatch')
        return text_response(raw)

class MemoryCache:
    def __init__(self):self.values={}
    def get(self,key):return self.values.get(key)
    def put(self,key,value):
        if key in self.values and self.values[key]!=value:raise ValueError('conflicting replay cache')
        self.values[key]=value

def replay(model_id,q):
    plan=read(ROOT/'PLAN.json');check_pins(plan['pins']);folder=ROOT/model_id/q
    done=read(folder/'COMPLETE.json')
    if done['plan_sha256']!=filehash(ROOT/'PLAN.json'):raise ValueError('changed plan')
    for rel,h in done['outputs'].items():
        if filehash(folder/rel)!=h:raise ValueError('changed output: '+rel)
    Transcriber,battery,constructed,Cache=engine();items=read(folder/'ITEMS.json')
    if items!=constructed(q):raise ValueError('changed battery')
    backend=Replay(plan['models'][model_id],folder/'calls')
    # In-memory cache only: saved successful cache entries cannot hide failed wire.
    canonical=battery(Transcriber(backend,MemoryCache()),q,items)
    result=gate_summary(canonical,items)
    if len(backend.seen)!=200 or result!=read(folder/'SUMMARY.json'):raise ValueError('independent whole-wire replay differs')
    if set((folder/'calls').iterdir())!=backend.seen:raise ValueError('unaccounted calls')
    return dict(status='VERIFIED',at=now(),model=model_id,question=q,complete_sha256=filehash(folder/'COMPLETE.json'),
                exact_calls=200,scientific_admission=False)

def prepare(service_pid):
    limits();require_resources(resource_snapshot())
    if (ROOT/'PLAN.json').exists():raise ValueError('already prepared')
    if not service_pid:raise ValueError('verified project service PID required')
    service_native=native_identity(service_pid)
    _,_,constructed,_=engine();sources=[]
    for model_id,model in MODELS.items():
        inspect(model)
        for q in QUESTIONS:
            items=constructed(q)
            if len(items)!=200 or len({digest([i['context'],i['text'],i.get('before')]) for i in items})!=200:raise ValueError('battery not distinct')
            path=ROOT/model_id/q/'ITEMS.json';freeze(path,items);sources.append(path)
    sources += [REPO/p for p in ('runners/next_round/literal_models.py','runners/next_round/literal_admission.py',
        'runners/next_round/engine_interface_v2.py','runners/next_round/queue.py','runners/stage14/common.py',
        'runners/stage9/process_identity.py','tests/test_next_round_literal_models.py',
        'docs/design/stage-15/OVERNIGHT_CONTINUATION.md')]
    sources += [CAPSULE/'PIN.json',*[CAPSULE/n for n in read(CAPSULE/'PIN.json')['files']]]
    freeze(ROOT/'PLAN.json',dict(at=now(),models=MODELS,questions=list(QUESTIONS),model_order=list(MODELS),pins=pins(sources),service_native=service_native,
        maximum_calls=3600,max_wall_seconds=86400,provider_calls=0,scientific_admission=False))
    print('Frozen 18 complete cells / 3600 calls; no inference yet.')

def run():
    limits();plan=read(ROOT/'PLAN.json');check_pins(plan['pins']);require_resources(resource_snapshot())
    with (ROOT/'ATTEMPT.claim').open('x',encoding='utf8') as f:f.write(now()+'\n')
    freeze(ROOT/'OWNER.json',dict(at=now(),native=native_identity(),plan_sha256=filehash(ROOT/'PLAN.json')))
    lease=REPO/'results/.literal-cpu.lock';token=json.dumps(native_identity()).encode()
    fd=os.open(lease,os.O_WRONLY|os.O_CREAT|os.O_EXCL);os.write(fd,token);os.close(fd)
    started=time.time();stop=threading.Event();backend=None;total=0
    def deadline():
        if stop.wait(plan['max_wall_seconds']):return
        atomic(ROOT/'FAILED.json',dict(status='FAILED',at=now(),reason='finite wall ceiling; lease retained'))
        os._exit(124)
    threading.Thread(target=deadline,daemon=True).start()
    try:
        while not (ROOT/'MONITOR_READY.json').exists():
            if time.time()-started>60:raise TimeoutError('monitor not registered')
            time.sleep(.25)
        if read(ROOT/'MONITOR_READY.json')['owner_sha256']!=filehash(ROOT/'OWNER.json'):raise ValueError('monitor mismatch')
        Transcriber,battery,_,Cache=engine()
        for model_id in plan['model_order']:
            model=plan['models'][model_id];inspect(model)
            for q in plan['questions']:
                check_pins(plan['pins']);folder=ROOT/model_id/q
                def guard():
                    snapshot=resource_snapshot();require_resources(snapshot)
                    if native_identity(plan['service_native']['pid'])!=plan['service_native']:raise RuntimeError('service identity drift')
                    if total+backend.calls>=plan['maximum_calls']:raise RuntimeError('call ceiling')
                    if lease.read_bytes()!=token:raise RuntimeError('lease drift')
                    atomic(ROOT/'PROGRESS.json',dict(at=now(),model=model_id,question=q,completed_calls=total+backend.calls,resources=snapshot))
                backend=Backend(model,folder/'calls',guard)
                guard();items=read(folder/'ITEMS.json')
                result=gate_summary(battery(Transcriber(backend,Cache(folder/'cache.sqlite')),q,items),items)
                backend.close();total+=backend.calls;check_pins(plan['pins'])
                freeze(folder/'SUMMARY.json',result)
                paths=[folder/'ITEMS.json',folder/'SUMMARY.json',*sorted((folder/'calls').rglob('*.json'))]
                freeze(folder/'COMPLETE.json',dict(status='COMPLETE',at=now(),plan_sha256=filehash(ROOT/'PLAN.json'),
                    outputs={p.relative_to(folder).as_posix():filehash(p) for p in paths},write_through_required=True,scientific_admission=False))
                freeze(folder/'REPLAY.json',replay(model_id,q))
        if total!=plan['maximum_calls']:raise RuntimeError('unexpected final dispatch count')
        if lease.read_bytes()!=token:raise RuntimeError('lease drift')
        lease.unlink();freeze(ROOT/'COMPLETE.json',dict(status='COMPLETE',at=now(),wall_seconds=time.time()-started,calls=total,
            outputs={str(p.relative_to(ROOT)).replace('\\','/'):filehash(p) for p in ROOT.glob('*/*/COMPLETE.json')},
            provider_calls=0,scientific_admission=False,write_through_required=True))
    except BaseException as exc:
        freeze(ROOT/'FAILED.json',dict(status='FAILED',at=now(),type=type(exc).__name__,error=str(exc),traceback=traceback.format_exc(),lease_retained=lease.exists()))
        raise
    finally:stop.set()

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['prepare','run','replay']);p.add_argument('--model');p.add_argument('--question');p.add_argument('--service-pid',type=int);a=p.parse_args()
    if a.action=='prepare':prepare(a.service_pid)
    elif a.action=='run':run()
    else:print(json.dumps(replay(a.model,a.question)))
