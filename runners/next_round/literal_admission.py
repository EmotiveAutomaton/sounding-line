"""Finite literal-feature apparatus admission; no paid or human-data calls.

DESIGN CHECK: LESSONS 3-5, CONTROLS 1-3 read 2026-10-15.
NULL: constant/wrong labels fail; malformed whole responses remain invalid.
ALTERNATIVE: realized literal facts pass each complete question separately.
Source drift, occupied service, non-CPU residency and uncertain calls refuse.
Constructed admission never becomes a natural-data or scientific promotion.
"""
import os
for _name in ('OMP_NUM_THREADS','MKL_NUM_THREADS','OPENBLAS_NUM_THREADS','NUMEXPR_NUM_THREADS'):
    os.environ[_name]='1'
import argparse,json,sys,threading,time,traceback,urllib.request
from collections import Counter
from pathlib import Path
from .engine_interface_v2 import CAPSULE,verify as verify_engine
from .queue import resource_snapshot,require_resources
from runners.stage14.common import REPO,read,freeze,atomic,pins,check_pins,filehash,digest,now,limits
from runners.stage9.process_identity import native_identity

ROOT=REPO/'results/phase_2_4_stage_15/raw/f4-literal-local-v1'
QUESTIONS=('Q8','Q9','Q7','Q1','Q3','Q4','Q6','Q10')
MODEL='llama3.1:8b'
MODEL_DIGEST='46e0c10c039e019119339687c3c1757cc81b9da49709a3b3924863ba87ca666e'
ENDPOINT='http://127.0.0.1:11435'
VERSION='0.40.3'


def engine():
    verify_engine();path=str(CAPSULE/'engine')
    if path not in sys.path:sys.path.insert(0,path)
    import tompathy_engine
    if not Path(tompathy_engine.__file__).resolve().is_relative_to(CAPSULE):raise ValueError('wrong engine import')
    from tompathy_engine.transcribe.runner import Transcriber
    from tompathy_engine.transcribe.admission import battery
    from tompathy_engine.transcribe.batteries import constructed
    from tompathy_engine.transcribe.cache import Cache
    return Transcriber,battery,constructed,Cache


def api(path,body=None,timeout=600):
    if path not in ('/api/version','/api/tags','/api/ps','/api/generate'):raise ValueError('unsupported endpoint')
    req=urllib.request.Request(ENDPOINT+path,data=None if body is None else json.dumps(body,ensure_ascii=False).encode(),headers={'Content-Type':'application/json'})
    op=urllib.request.build_opener(urllib.request.ProxyHandler({}))
    with op.open(req,timeout=timeout) as response:return json.load(response)


def inspect_service(allow_owned=False):
    if api('/api/version')['version']!=VERSION:raise RuntimeError('runtime changed')
    matches=[r for r in api('/api/tags')['models'] if r['name']==MODEL and r['digest']==MODEL_DIGEST]
    if len(matches)!=1:raise RuntimeError('model changed')
    resident=api('/api/ps')['models']
    if resident:
        if not allow_owned or len(resident)!=1 or resident[0]['digest']!=MODEL_DIGEST or resident[0].get('size_vram')!=0 or resident[0].get('context_length')!=8192:
            raise RuntimeError('service occupied or CPU residency not verified')
    return dict(version=VERSION,model=MODEL,digest=MODEL_DIGEST,resident=resident)


def gate_summary(canonical,items):
    if len(canonical['outcomes'])!=len(items):raise ValueError('incomplete outcomes')
    by_id={r['id']:r for r in canonical['outcomes']}
    if len(by_id)!=len(items) or set(by_id)!={r['id'] for r in items}:raise ValueError('changed outcome roster')
    groups={}
    for item in items:
        label=json.dumps(item['expected'],sort_keys=True);r=by_id[item['id']]
        group=groups.setdefault(label,dict(attempted=0,correct=0))
        group['attempted']+=1;group['correct']+=bool(r['valid'] and r.get('answer')==item['expected'])
    for group in groups.values():group['accuracy']=group['correct']/group['attempted']
    eligible=canonical['passed'] and canonical['accuracy']>=.85 and min(g['accuracy'] for g in groups.values())>=.70
    return dict(canonical=canonical,per_label=groups,constructed_feature_eligible=bool(eligible),
        natural_data_admission=False,engine_admission=False,template_dependence=True)


class Backend:
    model_id=MODEL+'@'+MODEL_DIGEST
    settings=dict(temperature=0,seed=0,protocol='ollama',gpu=False,num_thread=1,num_ctx=8192,num_predict=256,runtime=VERSION,transport='s15-recorded-cpu-v1')
    def __init__(self,folder,guard):self.folder=folder;self.guard=guard;self.owned=False;self.uncertain=False;self.calls=0
    def complete(self,prompt,schema):
        self.guard();inspect_service(self.owned)
        body=dict(model=MODEL,prompt=prompt,format=schema,stream=False,keep_alive=120,
            options=dict(temperature=0,seed=0,num_predict=256,num_gpu=0,num_thread=1,num_ctx=8192))
        dest=self.folder/digest(body)
        if dest.exists():raise RuntimeError('request already dispatched; no automatic retry')
        freeze(dest/'REQUEST.json',body);freeze(dest/'DISPATCH.json',dict(at=now(),native=native_identity()))
        self.uncertain=True;start=time.time()
        raw=api('/api/generate',body)
        freeze(dest/'RAW.json',raw)
        freeze(dest/'RECEIPT.json',dict(at=now(),wall_seconds=time.time()-start,raw_sha256=filehash(dest/'RAW.json')))
        self.owned=True
        resident=inspect_service(True)
        freeze(dest/'RESIDENCY.json',resident)
        if not resident['resident'] or not raw.get('done'):raise RuntimeError('completion/residency unknown')
        self.uncertain=False;self.calls+=1
        if raw.get('done_reason')!='stop':raise ValueError('whole response unfinished')
        return dict(text=raw['response'],logprobs=None)
    def close(self):
        if self.uncertain:raise RuntimeError('uncertain request retains service lease')
        if self.owned:
            inspect_service(True);api('/api/generate',dict(model=MODEL,keep_alive=0),timeout=60)
            if api('/api/ps')['models']:raise RuntimeError('owned model did not unload')


def prepare():
    limits();require_resources(resource_snapshot());service=inspect_service()
    if (ROOT/'PLAN.json').exists():raise ValueError('already prepared')
    _,_,constructed,_=engine();sources=[]
    for q in QUESTIONS:
        items=constructed(q)
        triples=[digest([i['context'],i.get('before'),i['text']]) for i in items]
        if len(set(triples))!=len(items):raise ValueError('duplicated actual battery inputs: '+q)
        freeze(ROOT/q/'ITEMS.json',items);sources.append(ROOT/q/'ITEMS.json')
    sources += [REPO/p for p in ('runners/next_round/literal_admission.py','runners/next_round/engine_interface_v2.py',
        'runners/next_round/queue.py','runners/stage14/common.py','runners/stage9/process_identity.py',
        'tests/test_next_round_literal_admission.py','docs/design/stage-15/F4_LITERAL_ADMISSION.md')]
    sources += [CAPSULE/'PIN.json',*[CAPSULE/n for n in read(CAPSULE/'PIN.json')['files']]]
    freeze(ROOT/'PLAN.json',dict(at=now(),questions=list(QUESTIONS),pins=pins(sources),service=service,
        maximum_calls=1600,max_wall_seconds=43200,provider_calls=0,engine_admission=False,
        q2='required independent entity package absent',q5='prior exact dialogue failure retained'))
    print('Eight complete literal batteries frozen; no inference performed.')


def run():
    limits();plan=read(ROOT/'PLAN.json');check_pins(plan['pins']);require_resources(resource_snapshot());inspect_service()
    with (ROOT/'ATTEMPT.claim').open('x',encoding='utf8') as f:f.write(now()+'\n')
    freeze(ROOT/'OWNER.json',dict(at=now(),native=native_identity(),plan_sha256=filehash(ROOT/'PLAN.json')))
    lease=REPO/'results/.literal-cpu.lock';token=json.dumps(native_identity()).encode()
    fd=os.open(lease,os.O_WRONLY|os.O_CREAT|os.O_EXCL);os.write(fd,token);os.close(fd)
    started=time.time();stop=threading.Event();backend=None
    def deadline():
        if stop.wait(plan['max_wall_seconds']):return
        atomic(ROOT/'FAILED.json',dict(status='FAILED',at=now(),reason='finite wall ceiling; lease retained'))
        os._exit(124)
    threading.Thread(target=deadline,daemon=True).start()
    try:
        while not (ROOT/'MONITOR_READY.json').exists():
            if time.time()-started>60:raise TimeoutError('monitor not registered')
            time.sleep(.25)
        if read(ROOT/'MONITOR_READY.json')['owner_sha256']!=filehash(ROOT/'OWNER.json'):raise ValueError('monitor identity mismatch')
        Transcriber,battery,_,Cache=engine()
        def guard():
            require_resources(resource_snapshot())
            if backend.calls>=plan['maximum_calls']:raise RuntimeError('call ceiling')
            atomic(ROOT/'PROGRESS.json',dict(at=now(),question=current,completed_calls=backend.calls,
                resources=resource_snapshot()))
        backend=Backend(ROOT/'calls',guard)
        transcriber=Transcriber(backend,Cache(ROOT/'cache.sqlite'))
        for current in plan['questions']:
            guard();check_pins(plan['pins']);folder=ROOT/current;items=read(folder/'ITEMS.json')
            canonical=battery(transcriber,current,items)
            # Cache-only replay of every returned answer; invalids retain raw attempts.
            result=gate_summary(canonical,items)
            freeze(folder/'SUMMARY.json',result)
            freeze(folder/'COMPLETE.json',dict(status='COMPLETE',at=now(),outputs={n:filehash(folder/n) for n in ('ITEMS.json','SUMMARY.json')},
                plan_sha256=filehash(ROOT/'PLAN.json'),engine_admission=False,write_through_required=True))
        backend.close();check_pins(plan['pins'])
        if lease.read_bytes()!=token:raise RuntimeError('service lease changed')
        lease.unlink()
        freeze(ROOT/'COMPLETE.json',dict(status='COMPLETE',at=now(),wall_seconds=time.time()-started,
            outputs={q+'/COMPLETE.json':filehash(ROOT/q/'COMPLETE.json') for q in plan['questions']},
            engine_admission=False,provider_calls=0,write_through_required=True))
    except BaseException as exc:
        freeze(ROOT/'FAILED.json',dict(status='FAILED',at=now(),type=type(exc).__name__,error=str(exc),traceback=traceback.format_exc(),lease_retained=lease.exists()))
        raise
    finally:stop.set()


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['prepare','run']);a=p.parse_args()
    prepare() if a.action=='prepare' else run()
