"""Paired Smol precision diagnostic; preserves original failed pilot.

DESIGN CHECK: LESSONS 3-5 reread October 17. NULL: incomplete, misaligned,
nonfinite or discrepant pairs refuse admission. ALTERNATIVE: all same-input
float32 cached/direct token pairs pass unchanged tolerance. No auto successor.
"""
import os
for _n in ('OMP_NUM_THREADS','MKL_NUM_THREADS','OPENBLAS_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[_n]='1'
import argparse,gc,math,time,threading,traceback,importlib.metadata
from runners.stage14.common import REPO,read,freeze,atomic,pins,check_pins,filehash,now,limits
from runners.stage9.process_identity import native_identity
from runners.next_round.queue import resource_snapshot,require_resources
from .readers import verify_model,contexts,pack,score_menu
from .reader_pilot_v6 import release_workspace,gpu,direct_loss
from .suggestion_corpus import menu_ranks,validate_rows,MODELS,VERSIONS

RAW=REPO/'results/phase_2_4_stage_15/raw'
ROOT=RAW/'drive-smol-precision-v1'
PRIOR=RAW/'drive-suggestion-pilot-v1'
PUBLIC=REPO/'results/phase_2_4_stage_15/DRIVE/SUGGESTION_PILOT_V1_FAILED.json'

def compare(cached,direct,tolerance):
    if len(cached)!=len(direct) or not cached:raise ValueError('missing paired targets')
    errors=[]
    for a,b in zip(cached,direct):
        if a['eligible']!=b['eligible']:raise ValueError('paired eligibility')
        if not a['eligible']:
            if a!=b:raise ValueError('paired exclusion')
            continue
        for k in ('native_token_ids','codepoint_offsets','prefix_tokens','target_tokens','utf8_bytes'):
            if a[k]!=b[k]:raise ValueError('paired alignment')
        x=a['native_token_nll'];y=b['native_token_nll']
        if len(x)!=len(y) or len(x)!=a['target_tokens'] or not x or not all(math.isfinite(v) and v>=0 for v in x+y):raise ValueError('paired finite coverage')
        errors.append(max(abs(u-v) for u,v in zip(x,y)))
    return dict(eligible=len(errors),maximum_absolute_error=max(errors,default=0.),pass_all=all(e<=tolerance for e in errors))

def prepare():
    if ROOT.exists():raise ValueError('existing attempt')
    limits();require_resources(resource_snapshot());r=read(PUBLIC)
    if r['status']!='VERIFIED_APPARATUS_FAILURE' or r['terminal_sha256']!=filehash(PRIOR/'FAILED.json'):raise ValueError('unreviewed failure')
    if native_identity(read(PRIOR/'OWNER.json')['native']['pid'])==read(PRIOR/'OWNER.json')['native']:raise ValueError('predecessor live')
    old=read(PRIOR/'PLAN.json');check_pins(old['pins'])
    selected=read(PRIOR/'SELECTION.json')['smol360']
    cases=[c for g in read(PRIOR/'CASES.json') for c in g['cases'] if c['key'] in selected]
    if {c['key'] for c in cases}!=set(selected) or len(cases)!=len(selected):raise ValueError('selection coverage')
    versions={n:importlib.metadata.version(n) for n in VERSIONS}
    if versions!=old['versions']:raise ValueError('runtime drift')
    src=[PRIOR/n for n in ('PLAN.json','OWNER.json','FAILED.json','CASES.json','CENSUS.json','SELECTION.json','smol360/DIRECT_CHECK.json')]+[PUBLIC,REPO/'runners/drive/smol_precision.py',REPO/'tests/test_drive_smol_precision.py',REPO/'docs/design/stage-15/drive/SMOL_PRECISION_V1.md']
    bindings=dict(old['pins']);bindings.update(pins(src))
    freeze(ROOT/'CASES.json',cases);bindings.update(pins([ROOT/'CASES.json']))
    freeze(ROOT/'PLAN.json',dict(at=now(),pins=bindings,versions=versions,tolerance=.02,order=['float16','float32'],max_compute_seconds=1200,max_resource_wait_seconds=7200,max_output_bytes=64*1024**2,allocator_cap_MiB=5888,cold_floor_MiB=7424,empty_floor_MiB=7168,working_floor_MiB=1024,maximum_temperature_C=78))
    print('Paired precision plan frozen; no inference.')

def run():
    limits();plan=read(ROOT/'PLAN.json');check_pins(plan['pins']);require_resources(resource_snapshot())
    if {n:importlib.metadata.version(n) for n in VERSIONS}!=plan['versions']:raise ValueError('runtime drift')
    with (ROOT/'ATTEMPT.claim').open('x',encoding='utf8') as f:f.write(now()+'\n')
    freeze(ROOT/'OWNER.json',dict(at=now(),native=native_identity(),plan_sha256=filehash(ROOT/'PLAN.json')))
    start=time.monotonic();waited=0.;stop=threading.Event();torch=None;model=None;owned=False;lock=REPO/'results/.gpu.lock';token=f'{os.getpid()} smol-precision-v1'.encode()
    def deadline():
        if not stop.wait(plan['max_compute_seconds']+plan['max_resource_wait_seconds']+90):
            atomic(ROOT/'FAILED.json',dict(at=now(),status='FAILED',reason='hard finite deadline'));os._exit(124)
    threading.Thread(target=deadline,daemon=True).start()
    def wait(floor,acquire=False):
        nonlocal waited,owned
        began=time.monotonic()
        while True:
            s=gpu();require_resources(resource_snapshot())
            if s['free_MiB']>=floor and s['temperature_C']<=plan['maximum_temperature_C']:
                if not acquire:break
                try:
                    fd=os.open(lock,os.O_CREAT|os.O_EXCL|os.O_WRONLY)
                    try:os.write(fd,token)
                    finally:os.close(fd)
                    owned=True;break
                except FileExistsError:pass
            atomic(ROOT/'PROGRESS.json',dict(at=now(),task='WAITING_RESOURCE',gpu=s,required=floor))
            if waited+time.monotonic()-began>plan['max_resource_wait_seconds']:raise TimeoutError('resource allowance')
            time.sleep(30)
        waited+=time.monotonic()-began
    def guard():
        s=gpu();require_resources(resource_snapshot())
        if s['free_MiB']<plan['working_floor_MiB'] or s['temperature_C']>plan['maximum_temperature_C']:raise RuntimeError('working resource floor')
        if time.monotonic()-start-waited>plan['max_compute_seconds']:raise TimeoutError('compute allowance')
        return s
    try:
        while not (ROOT/'MONITOR_READY.json').exists():
            if time.monotonic()-start>90:raise TimeoutError('monitor handshake')
            time.sleep(.25)
        if read(ROOT/'MONITOR_READY.json')['owner_sha256']!=filehash(ROOT/'OWNER.json'):raise ValueError('monitor binding')
        wait(plan['cold_floor_MiB'],True)
        import torch as module
        from transformers import AutoTokenizer,AutoModelForCausalLM
        torch=module;torch.set_num_threads(1);torch.cuda.set_per_process_memory_fraction(plan['allocator_cap_MiB']*2**20/torch.cuda.get_device_properties(0).total_memory)
        path=verify_model(read(MODELS)['smol360']);tok=AutoTokenizer.from_pretrained(path,local_files_only=True,trust_remote_code=False,use_fast=True)
        cases=read(ROOT/'CASES.json');summary={}
        for precision in plan['order']:
            release_workspace(torch)
            if torch.cuda.memory_allocated() or torch.cuda.memory_reserved():raise ValueError('allocator not empty')
            wait(plan['empty_floor_MiB']);dtype=getattr(torch,precision)
            model=AutoModelForCausalLM.from_pretrained(path,local_files_only=True,trust_remote_code=False,torch_dtype=dtype).to('cuda').eval()
            if any(p.dtype!=dtype or p.device.type!='cuda' for p in model.parameters()):raise ValueError('precision/residency')
            samples=[guard()];torch.cuda.reset_peak_memory_stats();began=time.monotonic();cached_rows=[];direct_rows=[];comparisons=[]
            for i,case in enumerate(cases):
                atomic(ROOT/'PROGRESS.json',dict(at=now(),task=precision,menu=i,total=len(cases)))
                for cond,context in contexts(tok,case['brief'],case['document']).items():
                    samples.append(guard());cached=score_menu(model,tok,context,case['menu'],torch);samples.append(guard());direct=[]
                    for target in case['menu']:
                        x=pack(tok,context,target)
                        if not x['eligible']:direct.append(x);continue
                        samples.append(guard());v=direct_loss(model,torch,x);samples.append(guard());total=sum(v)
                        direct.append(dict(eligible=True,native_token_ids=x['target'],native_token_nll=v,codepoint_offsets=[list(z) for z in x['offsets']],prefix_tokens=len(x['prefix']),target_tokens=len(v),utf8_bytes=x['utf8_bytes'],total_nll=total,mean_token_nll=total/len(v),nll_per_utf8_byte=total/x['utf8_bytes']))
                    # Normalize the original fast tokenizer's tuple offsets at the JSON boundary.
                    for r in cached:
                        if r['eligible']:r['codepoint_offsets']=[list(z) for z in r['codepoint_offsets']]
                    comparisons.append(dict(key=case['key'],condition=cond,**compare(cached,direct,plan['tolerance'])))
                    cached_rows.append(dict(key=case['key'],condition=cond,scores=cached,ranks=menu_ranks(cached)))
                    direct_rows.append(dict(key=case['key'],condition=cond,scores=direct,ranks=menu_ranks(direct)))
            validate_rows(cached_rows,cases);validate_rows(direct_rows,cases)
            if not comparisons or sum(c['eligible'] for c in comparisons)<1:raise ValueError('no paired support')
            freeze(ROOT/precision/'CACHED.json',cached_rows);freeze(ROOT/precision/'DIRECT.json',direct_rows);freeze(ROOT/precision/'COMPARISONS.json',comparisons)
            summary[precision]=dict(pass_all=all(c['pass_all'] for c in comparisons),eligible=sum(c['eligible'] for c in comparisons),menu_contexts=len(comparisons),maximum_absolute_error=max(c['maximum_absolute_error'] for c in comparisons),seconds=time.monotonic()-began,minimum_sampled_free_MiB=min(s['free_MiB'] for s in samples),maximum_temperature_C=max(s['temperature_C'] for s in samples),peak_allocated_bytes=torch.cuda.max_memory_allocated(),peak_reserved_bytes=torch.cuda.max_memory_reserved(),all_parameters_cuda=True,dtype=precision)
            del model;model=None;release_workspace(torch)
            if sum(p.stat().st_size for p in ROOT.rglob('*') if p.is_file())>plan['max_output_bytes']:raise ValueError('retained byte ceiling')
        check_pins(plan['pins']);freeze(ROOT/'SUMMARY.json',dict(versions=plan['versions'],conditions=summary,remedy_supported=summary['float32']['pass_all'],scientific_admission=False,auto_successor=False))
        freeze(ROOT/'COMPLETE.json',dict(at=now(),status='COMPLETE',outputs={p.relative_to(ROOT).as_posix():filehash(p) for p in ROOT.rglob('*.json') if p.name not in ('MONITOR_READY.json','PROGRESS.json')},write_through_required=True))
    except BaseException as e:
        freeze(ROOT/'FAILED.json',dict(at=now(),status='FAILED',reason=str(e),traceback=traceback.format_exc()));raise
    finally:
        stop.set();model=None;gc.collect()
        try:
            if torch is not None and torch.cuda.is_initialized():release_workspace(torch)
        finally:
            if owned and lock.exists() and lock.read_bytes()==token:lock.unlink()

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['prepare','run']);(prepare if p.parse_args().action=='prepare' else run)()
