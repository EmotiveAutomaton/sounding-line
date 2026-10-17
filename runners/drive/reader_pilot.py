"""Finite five-reader scoring admission and measured throughput pilot.

DESIGN CHECK: LESSONS 3-5. NULL: cache/direct mismatch, missing full residency,
overflow or inadequate memory stops before full scoring. ALTERNATIVE: all five
exact readers produce finite aligned losses with retained exclusions and timings.
No hypothesis or model-selection score is reported from this apparatus pilot.
"""
import os
for _n in ('OMP_NUM_THREADS','MKL_NUM_THREADS','OPENBLAS_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[_n]='1'
import argparse,gc,json,subprocess,threading,time,traceback
from pathlib import Path
from runners.stage14.common import REPO,read,freeze,atomic,pins,check_pins,filehash,now,limits
from runners.stage9.process_identity import native_identity
from runners.next_round.queue import resource_snapshot,require_resources
from .readers import CATALOGUE,verify_model,contexts,pack,score_menu,COMMON_WINDOW
from .foundation import PREPARED,ROSTER

ROOT=REPO/'results/phase_2_4_stage_15/raw/drive-reader-pilot-v1'
ORDER=('smol360','qwen500','pythia410','pythia1000','pythia1400')


def gpu():
    raw=subprocess.check_output(['nvidia-smi','--query-gpu=memory.free,memory.used,temperature.gpu','--format=csv,noheader,nounits'],timeout=20,text=True)
    free,used,temp=map(float,raw.strip().split(','))
    return dict(free_MiB=free,used_MiB=used,temperature_C=temp)


def prepare():
    if (ROOT/'PLAN.json').exists():raise ValueError('existing pilot identity')
    limits();require_resources(resource_snapshot());models=read(CATALOGUE/'MODELS.json')
    if set(models)!=set(ORDER):raise ValueError('full size ladder not ready')
    for entry in models.values():verify_model(entry)
    ss=read(PREPARED/'SESSIONS.json');roster={s['session']:s for s in read(ROSTER)};cases=[]
    # Support-only deterministic sample; never inspect response/model scores.
    for s in sorted(ss,key=lambda s:(s['writer'],s['timestamp'],s['session'])):
        if s['writer'] in {r['writer'] for r in cases}:continue
        events_path=REPO/roster[s['session']]['path']
        with events_path.open(encoding='utf8') as f:brief=json.loads(next(f))['currentDoc']
        for row in s['rows'][:2]:cases.append(dict(key=row['key'],writer=s['writer'],brief=brief,document=row['document'],menu=row['menu']))
        if len({r['writer'] for r in cases})==6:break
    freeze(ROOT/'CASES.json',cases);freeze(ROOT/'MODELS.json',models)
    src=[REPO/p for p in ('runners/drive/reader_pilot.py','runners/drive/readers.py','runners/drive/foundation.py',
        'runners/stage14/common.py','runners/stage9/process_identity.py','runners/next_round/queue.py',
        'tests/test_drive_readers.py')]+[ROOT/'CASES.json',ROOT/'MODELS.json',CATALOGUE/'COMPLETE.json',PREPARED/'SESSIONS.json',ROSTER]
    freeze(ROOT/'PLAN.json',dict(at=now(),pins=pins(src),order=list(ORDER),cases=len(cases),common_window=2048,
        dtype='float16',minimum_free_MiB=6500,working_free_floor_MiB=1024,maximum_temperature_C=78,
        cuda_allocator_fraction=.40,
        cache_direct_max_abs_tolerance=.02,max_wall_seconds=14400,max_resource_wait_seconds=21600,scientific_admission=False))
    print('Five-reader pilot frozen:',len(cases),'menus per reader; no inference yet.')


def direct_loss(model,torch,packed):
    ids=packed['prefix']+packed['target'];start=len(packed['prefix'])-1
    with torch.inference_mode():
        logits=model(input_ids=torch.tensor([ids[:-1]],device='cuda'),use_cache=False).logits[0,start:,:].float()
        return torch.nn.functional.cross_entropy(logits,torch.tensor(packed['target'],device='cuda'),reduction='none').cpu().tolist()


def run():
    limits();plan=read(ROOT/'PLAN.json');check_pins(plan['pins']);require_resources(resource_snapshot())
    with (ROOT/'ATTEMPT.claim').open('x',encoding='utf8') as f:f.write(now()+'\n')
    freeze(ROOT/'OWNER.json',dict(at=now(),native=native_identity(),plan_sha256=filehash(ROOT/'PLAN.json')))
    started=time.time();lock=REPO/'results/.gpu.lock';token=f'{os.getpid()} drive-reader-pilot-v1'.encode();owned=False;stop=threading.Event()
    def hard_deadline():
        if stop.wait(plan['max_resource_wait_seconds']+plan['max_wall_seconds']):return
        atomic(ROOT/'FAILED.json',dict(status='FAILED',at=now(),reason='hard finite worker ceiling; lease retained'))
        os._exit(124)
    threading.Thread(target=hard_deadline,daemon=True).start()
    try:
        while not (ROOT/'MONITOR_READY.json').exists():
            if time.time()-started>90:raise TimeoutError('monitor handshake')
            time.sleep(.25)
        if read(ROOT/'MONITOR_READY.json')['owner_sha256']!=filehash(ROOT/'OWNER.json'):raise ValueError('monitor binding')
        # A resource wait is healthy; do not reclaim another project's lease.
        while True:
            snap=gpu();require_resources(resource_snapshot())
            if not lock.exists() and snap['free_MiB']>=plan['minimum_free_MiB'] and snap['temperature_C']<=78:
                try:
                    fd=os.open(lock,os.O_WRONLY|os.O_CREAT|os.O_EXCL);os.write(fd,token);os.close(fd);owned=True;break
                except FileExistsError:pass
            atomic(ROOT/'PROGRESS.json',dict(at=now(),task='WAITING_RESOURCE',gpu=snap,existing_lease=lock.exists()))
            if time.time()-started>plan['max_resource_wait_seconds']:raise TimeoutError('resource wait exhausted; no other worker touched')
            time.sleep(60)
        import torch
        from transformers import AutoTokenizer,AutoModelForCausalLM
        torch.cuda.set_per_process_memory_fraction(plan['cuda_allocator_fraction'])
        torch.set_num_threads(1);models=read(ROOT/'MODELS.json');cases=read(ROOT/'CASES.json');run_start=time.time();summaries={}
        for name in ORDER:
            check_pins(plan['pins']);path=verify_model(models[name]);require_resources(resource_snapshot())
            if gpu()['free_MiB']<plan['minimum_free_MiB']:raise RuntimeError('cold-load VRAM floor lost')
            tok=AutoTokenizer.from_pretrained(path,local_files_only=True,trust_remote_code=False,use_fast=True)
            model=AutoModelForCausalLM.from_pretrained(path,local_files_only=True,trust_remote_code=False,torch_dtype=torch.float16).to('cuda').eval()
            if any(p.device.type!='cuda' for p in model.parameters()):raise ValueError('partial reader residency')
            torch.cuda.reset_peak_memory_stats();before=gpu();model_start=time.time();total=0;target_tokens=0;checks=[];outputs=[]
            for i,case in enumerate(cases):
                snap=gpu();require_resources(resource_snapshot())
                if snap['free_MiB']<1024 or snap['temperature_C']>78:raise RuntimeError('working GPU floor lost')
                if time.time()-run_start>plan['max_wall_seconds']:raise TimeoutError('finite scoring allowance')
                atomic(ROOT/'PROGRESS.json',dict(at=now(),task=name,menu=i,total=len(cases),gpu=snap))
                for condition,context in contexts(tok,case['brief'],case['document']).items():
                    scores=score_menu(model,tok,context,case['menu'],torch)
                    if gpu()['free_MiB']<plan['working_free_floor_MiB']:raise RuntimeError('post-call dedicated VRAM floor lost')
                    if i==0:
                        for text,scored in zip(case['menu'],scores):
                            if not scored['eligible']:continue
                            direct=direct_loss(model,torch,pack(tok,context,text));err=max(abs(a-b) for a,b in zip(direct,scored['native_token_nll']))
                            checks.append(err)
                            if err>plan['cache_direct_max_abs_tolerance']:raise ValueError('KV-cache/direct teacher forcing disagreement')
                    outputs.append(dict(key=case['key'],condition=condition,scores=scores));total+=len(scores)
                    target_tokens+=sum(r.get('target_tokens',0) for r in scores if r['eligible'])
            elapsed=time.time()-model_start
            summaries[name]=dict(items=total,target_tokens=target_tokens,seconds=elapsed,
                target_tokens_per_second=target_tokens/elapsed,cache_direct_max_abs=max(checks),
                max_allocated_bytes=torch.cuda.max_memory_allocated(),max_reserved_bytes=torch.cuda.max_memory_reserved(),
                gpu_before=before,gpu_after=gpu(),all_parameters_cuda=True,context_window=COMMON_WINDOW)
            freeze(ROOT/name/'SCORES.json',outputs);freeze(ROOT/name/'TELEMETRY.json',summaries[name])
            del model;gc.collect();torch.cuda.empty_cache()
        freeze(ROOT/'SUMMARY.json',summaries)
        freeze(ROOT/'COMPLETE.json',dict(status='COMPLETE',at=now(),outputs={p.relative_to(ROOT).as_posix():filehash(p)
            for p in ROOT.rglob('*.json') if p.name not in ('PROGRESS.json','MONITOR_READY.json')},
            scientific_admission=False,write_through_required=True))
    except BaseException as exc:
        freeze(ROOT/'FAILED.json',dict(status='FAILED',at=now(),reason=str(exc),traceback=traceback.format_exc()));raise
    finally:
        stop.set()
        if owned and lock.exists() and lock.read_bytes()==token:lock.unlink()


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('action',choices=['prepare','run']);args=ap.parse_args()
    prepare() if args.action=='prepare' else run()
