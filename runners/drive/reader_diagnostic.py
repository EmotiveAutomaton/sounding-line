"""Fixed paired precision diagnostic, never automatic full-reader admission.

DESIGN CHECK: LESSONS 3-5. NULL: disagreement remains inadmissible; ALTERNATIVE:
all fixed float32 comparisons pass the original tolerance. Both outcomes and
overflow denominators are retained. Invalid/resource failures stop, not retry.
"""
import os
for _n in ('OMP_NUM_THREADS','MKL_NUM_THREADS','OPENBLAS_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[_n]='1'
import argparse,gc,importlib.metadata,threading,time,traceback
from runners.stage14.common import REPO,read,freeze,atomic,pins,check_pins,filehash,now,limits
from runners.stage9.process_identity import native_identity
from runners.next_round.queue import require_resources,resource_snapshot
from .readers import verify_model,contexts,pack,score_menu
from .reader_precision import discrepancy
from .reader_pilot_v3 import gpu,direct_loss

ROOT=REPO/'results/phase_2_4_stage_15/raw/drive-reader-diagnostic-v1'
PRIOR=REPO/'results/phase_2_4_stage_15/raw/drive-reader-pilot-v3'

def versions():
    return {n:importlib.metadata.version(n) for n in ('torch','transformers','tokenizers','safetensors')}

def prepare():
    if (ROOT/'PLAN.json').exists():raise ValueError('existing diagnostic')
    check_pins(read(PRIOR/'PLAN.json')['pins'])
    if read(PRIOR/'FAILED.json')['reason']!='KV-cache/direct teacher forcing disagreement':raise ValueError('unreviewed failure')
    if native_identity(read(PRIOR/'OWNER.json')['native']['pid'])==read(PRIOR/'OWNER.json')['native']:raise ValueError('prior still live')
    case=read(PRIOR/'CASES.json')[0];model=read(PRIOR/'MODELS.json')['pythia410'];verify_model(model)
    freeze(ROOT/'CASE.json',case);freeze(ROOT/'MODEL.json',model)
    files=['runners/drive/reader_diagnostic.py','runners/drive/readers.py','runners/drive/reader_precision.py',
           'runners/drive/reader_pilot_v3.py','runners/drive/foundation.py','runners/stage14/common.py',
           'runners/stage9/process_identity.py','runners/next_round/queue.py',
           'docs/design/stage-15/drive/READER_PRECISION_DIAGNOSTIC.md']
    freeze(ROOT/'PLAN.json',dict(at=now(),pins=pins([REPO/f for f in files]+[ROOT/'CASE.json',ROOT/'MODEL.json',PRIOR/'FAILED.json',PRIOR/'pythia410/check-c0-000.json']),
        versions=versions(),dtypes=['float16','float32'],tolerance=.02,max_wait=21600,max_compute=900))
    print('Paired fixed-input precision diagnostic frozen; no inference yet.')

def run():
    limits();plan=read(ROOT/'PLAN.json');check_pins(plan['pins'])
    if versions()!=plan['versions']:raise ValueError('runtime drift')
    require_resources(resource_snapshot())
    with (ROOT/'ATTEMPT.claim').open('x') as f:f.write(now())
    freeze(ROOT/'OWNER.json',dict(at=now(),native=native_identity(),plan_sha256=filehash(ROOT/'PLAN.json')))
    started=time.monotonic();lock=REPO/'results/.gpu.lock';token=f'{os.getpid()} drive-reader-diagnostic-v1'.encode();owned=False;stop=threading.Event()
    def deadline():
        if stop.wait(plan['max_wait']+plan['max_compute']):return
        atomic(ROOT/'FAILED.json',dict(status='FAILED',at=now(),reason='hard finite ceiling; lease retained'));os._exit(124)
    threading.Thread(target=deadline,daemon=True).start()
    try:
        while not (ROOT/'MONITOR_READY.json').exists():
            if time.monotonic()-started>90:raise TimeoutError('monitor handshake')
            time.sleep(.25)
        if read(ROOT/'MONITOR_READY.json')['owner_sha256']!=filehash(ROOT/'OWNER.json'):raise ValueError('monitor binding')
        while True:
            snap=gpu();require_resources(resource_snapshot())
            if not lock.exists() and snap['free_MiB']>=6500 and snap['temperature_C']<=78:
                try:
                    fd=os.open(lock,os.O_WRONLY|os.O_CREAT|os.O_EXCL);os.write(fd,token);os.close(fd);owned=True;break
                except FileExistsError:pass
            atomic(ROOT/'PROGRESS.json',dict(at=now(),task='WAITING_RESOURCE',gpu=snap))
            if time.monotonic()-started>plan['max_wait']:raise TimeoutError('resource wait')
            time.sleep(60)
        import torch
        from transformers import AutoTokenizer,AutoModelForCausalLM
        torch.set_num_threads(1);torch.cuda.set_per_process_memory_fraction(.40)
        path=verify_model(read(ROOT/'MODEL.json'));case=read(ROOT/'CASE.json');summary={};compute=time.monotonic()
        tok=AutoTokenizer.from_pretrained(path,local_files_only=True,trust_remote_code=False,use_fast=True)
        for dtype in plan['dtypes']:
            snap=gpu();require_resources(resource_snapshot())
            if snap['free_MiB']<6500 or snap['temperature_C']>78:raise RuntimeError('cold-load floor lost')
            model=AutoModelForCausalLM.from_pretrained(path,local_files_only=True,trust_remote_code=False,torch_dtype=getattr(torch,dtype)).to('cuda').eval()
            if any(p.device.type!='cuda' or p.dtype!=getattr(torch,dtype) for p in model.parameters()):raise ValueError('actual residency/dtype')
            comparisons=[];excluded=0
            for cond,context in contexts(tok,case['brief'],case['document']).items():
                snap=gpu();require_resources(resource_snapshot())
                if snap['free_MiB']<1024 or snap['temperature_C']>78:raise RuntimeError('working GPU floor')
                if time.monotonic()-compute>plan['max_compute']:raise TimeoutError('compute ceiling')
                atomic(ROOT/'PROGRESS.json',dict(at=now(),task=dtype,condition=cond,gpu=snap))
                scores=score_menu(model,tok,context,case['menu'],torch)
                for i,(target,score) in enumerate(zip(case['menu'],scores)):
                    if not score['eligible']:excluded+=1;continue
                    direct=direct_loss(model,torch,pack(tok,context,target));err=discrepancy(direct,score['native_token_nll'])
                    freeze(ROOT/dtype/f'{cond}-{i}.json',dict(direct=direct,cached=score['native_token_nll'],max_abs=err,passes=err<=plan['tolerance']))
                    comparisons.append(err)
                if gpu()['free_MiB']<1024:raise RuntimeError('post-call GPU floor')
            if not comparisons:raise ValueError('no comparisons')
            summary[dtype]=dict(comparisons=len(comparisons),excluded=excluded,max_abs=max(comparisons),all_pass=max(comparisons)<=plan['tolerance'],attention=model.config._attn_implementation,all_parameters_cuda=True)
            del model;gc.collect();torch.cuda.empty_cache()
        freeze(ROOT/'SUMMARY.json',dict(versions=versions(),runtime=summary,scientific_admission=False,full_pilot_admission=False))
        freeze(ROOT/'COMPLETE.json',dict(status='COMPLETE',at=now(),outputs={p.relative_to(ROOT).as_posix():filehash(p) for p in ROOT.rglob('*.json') if p.name not in ('PROGRESS.json','MONITOR_READY.json')},write_through_required=True))
    except BaseException as exc:
        freeze(ROOT/'FAILED.json',dict(status='FAILED',at=now(),reason=str(exc),traceback=traceback.format_exc()));raise
    finally:
        stop.set()
        if owned and lock.exists() and lock.read_bytes()==token:lock.unlink()

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('action',choices=['prepare','run']);args=ap.parse_args()
    prepare() if args.action=='prepare' else run()
