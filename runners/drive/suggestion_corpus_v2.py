"""Finite P1 suggestion-only throughput pilot and checkpointed whole roster.

DESIGN CHECK: LESSONS 3-5 reread October 17. NULL: source drift, missing items,
nonfinite/misaligned output, disagreement or resource loss refuses. ALTERNATIVE:
all planned inputs have retained scores or explicit overflow dispositions.
No scientific contrast, typed-history substitution, implicit retry or auto-main.
"""
import os
for _k in ('OMP_NUM_THREADS','MKL_NUM_THREADS','OPENBLAS_NUM_THREADS','NUMEXPR_NUM_THREADS'):
    os.environ[_k]='1'
import gc,gzip,json,math,time,threading,traceback,importlib.metadata
from datetime import datetime
from collections import Counter
from pathlib import Path
from runners.stage14.common import REPO,read,freeze,atomic,pins,check_pins,filehash,digest,canonical,now,limits
from runners.stage9.process_identity import native_identity
from runners.next_round.queue import resource_snapshot,require_resources
from .foundation import PREPARED,ROSTER
from .readers import contexts,pack,verify_model,score_menu as cached_score
from .readers_low_memory import score_menu as blocked_score
from .reader_pilot_v6 import release_workspace,gpu,direct_loss

RAW=REPO/'results/phase_2_4_stage_15/raw'
PILOT=RAW/'drive-suggestion-pilot-v2'
MAIN=RAW/'drive-suggestion-main-v2'
ADMITTED=REPO/'results/phase_2_4_stage_15/DRIVE/READER_PILOT_V6.json'
MODELS=RAW/'drive-reader-pilot-v6/MODELS.json'
ORDER=('smol360','qwen500','pythia410','pythia1000','pythia1400')
VERSIONS=('torch','transformers','tokenizers','safetensors')

def menu_ranks(scores):
    values=[s['mean_token_nll'] if s['eligible'] else None for s in scores]
    return [None if x is None else 1+sum(y<x for y in values if y is not None)+.5*(sum(y==x for y in values if y is not None)-1) for x in values]

def validate_rows(rows,cases):
    """Pure full checkpoint replay; no model dispatch on a reused chunk."""
    if len(rows)!=len(cases)*4:raise ValueError('incomplete context roster')
    n=0
    for case in cases:
        for condition in ('c0','c1','c2','c3'):
            row=rows[n];n+=1
            if row['key']!=case['key'] or row['condition']!=condition or len(row['scores'])!=len(case['menu']):raise ValueError('menu identity/coverage changed')
            for target,s in zip(case['menu'],row['scores']):
                if not s['eligible']:
                    if s.get('reason') not in ('empty target','whole context plus target exceeds common 2048-token window'):raise ValueError('unknown exclusion')
                    if s['reason'].startswith('whole context') and (s.get('prefix_tokens',0)<1 or s.get('target_tokens',0)<1 or s['prefix_tokens']+s['target_tokens']<=2048):raise ValueError('false overflow')
                    continue
                values=s['native_token_nll']
                if not values or len(values)!=len(s['native_token_ids']) or len(values)!=len(s['codepoint_offsets']) or len(values)!=s['target_tokens']:raise ValueError('token alignment')
                if not all(math.isfinite(x) and x>=0 for x in values):raise ValueError('nonfinite/negative loss')
                if s['prefix_tokens']<1 or s['prefix_tokens']+len(values)>2048:raise ValueError('context boundary')
                if s['utf8_bytes']!=len(target.encode('utf8')):raise ValueError('byte denominator')
                total=sum(values)
                for k,v in [('total_nll',total),('mean_token_nll',total/len(values)),('nll_per_utf8_byte',total/s['utf8_bytes'])]:
                    if not math.isclose(s[k],v,rel_tol=1e-12,abs_tol=1e-12):raise ValueError('loss reduction')
                if any(not (0<=a<=b<=len(target)) for a,b in s['codepoint_offsets']):raise ValueError('character offset')
            if row['ranks']!=menu_ranks(row['scores']):raise ValueError('menu ranks')
    return True

def checkpoint(path,payload,cases):
    raw=(canonical(payload)+'\n').encode('utf8');data=gzip.compress(raw,compresslevel=6,mtime=0)
    if path.exists():raise ValueError('checkpoint already exists')
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix('.tmp')
    with tmp.open('xb') as stream:stream.write(data)
    os.replace(tmp,path)
    actual=json.loads(gzip.decompress(path.read_bytes()))
    if actual!=payload:raise ValueError('checkpoint readback')
    validate_rows(actual['rows'],cases)
    return dict(file=path.name,sha256=filehash(path),bytes=path.stat().st_size,input_sha256=digest(cases))

def load_checkpoint(path,record,cases,plan_sha256,model):
    if filehash(path)!=record['sha256'] or digest(cases)!=record['input_sha256']:raise ValueError('checkpoint binding')
    value=json.loads(gzip.decompress(path.read_bytes()))
    if value['plan_sha256']!=plan_sha256 or value['model']!=model or value['input_sha256']!=digest(cases):raise ValueError('checkpoint provenance')
    validate_rows(value['rows'],cases)
    return value

def select_pilot(lengths):
    """Support only, deterministic canonical tie-breaking; include overflow."""
    eligible=sorted((n,k) for k,n in lengths if n<=2048)
    if not eligible:raise ValueError('no whole-context support')
    selected=[]
    for q in (0,.25,.5,.75,1):
        k=eligible[round(q*(len(eligible)-1))][1]
        if k not in selected:selected.append(k)
    overflow=sorted(k for k,n in lengths if n>2048)
    if overflow:selected.append(overflow[0])
    return selected

def main_bounds(timing):
    if set(timing)!=set(ORDER):raise ValueError('incomplete timing ladder')
    values=[v[k] for v in timing.values() for k in ('projected_seconds','projected_bytes')]
    if any(not math.isfinite(v) or v<=0 for v in values):raise ValueError('invalid timing/byte projection')
    forecast=sum(v['projected_seconds'] for v in timing.values())*3
    bytes_estimate=sum(v['projected_bytes'] for v in timing.values())*3
    if forecast>72*3600 or bytes_estimate>32*1024**3:raise ValueError('measured full-pass ceiling exceeded')
    return dict(max_compute_seconds=max(36000,math.ceil(forecast)),max_output_bytes=32*1024**3,forecast_seconds=forecast,forecast_bytes=bytes_estimate)

def recovery_inputs(prior=None,diagnostic=None,failure=None,precision=None,inspection=None):
    prior=prior or RAW/'drive-suggestion-pilot-v1'
    diagnostic=diagnostic or RAW/'drive-smol-precision-v1'
    failure=failure or REPO/'results/phase_2_4_stage_15/DRIVE/SUGGESTION_PILOT_V1_FAILED.json'
    precision=precision or REPO/'results/phase_2_4_stage_15/DRIVE/SMOL_PRECISION_V1.json'
    inspection=inspection or REPO/'.agent-state/drive-20261016/SUGGESTION_FAILURE_INSPECTION.json'
    f=read(failure);p=read(precision)
    if f['status']!='VERIFIED_APPARATUS_FAILURE' or p['status']!='VERIFIED_COMPLETE_DIAGNOSTIC' or not p['remedy_supported']:raise ValueError('precision recovery unadmitted')
    if f['terminal_sha256']!=filehash(prior/'FAILED.json') or p['terminal_sha256']!=filehash(diagnostic/'COMPLETE.json') or f['inspection_sha256']!=filehash(inspection):raise ValueError('recovery receipt binding')
    for path in (prior,diagnostic):
        owner=read(path/'OWNER.json')
        if native_identity(owner['native']['pid'])==owner['native']:raise ValueError('recovery predecessor live')
        check_pins(read(path/'PLAN.json')['pins'])
    retained=read(inspection)['retained']
    for name in ('CASES.json','CENSUS.json','SELECTION.json'):
        if filehash(prior/name)!=retained[name]:raise ValueError('retained input changed')
    for name,h in read(diagnostic/'COMPLETE.json')['outputs'].items():
        if filehash(diagnostic/name)!=h:raise ValueError('paired evidence changed')
    if not read(diagnostic/'SUMMARY.json')['remedy_supported']:raise ValueError('paired diagnostic failed')
    charged=sum((datetime.fromisoformat(read(path/terminal)['at'])-datetime.fromisoformat(read(path/'OWNER.json')['at'])).total_seconds() for path,terminal in ((prior,'FAILED.json'),(diagnostic,'COMPLETE.json')))
    if not 0<=charged<7200:raise ValueError('aggregate pilot computation allowance exhausted')
    files=[failure,precision,inspection]+[prior/n for n in ('PLAN.json','OWNER.json','FAILED.json','CASES.json','CENSUS.json','SELECTION.json')]+[diagnostic/n for n in ('PLAN.json','OWNER.json','COMPLETE.json','SUMMARY.json')]
    return dict(charged_seconds=charged,files=files,prior=prior)

def prepare(phase):
    root=PILOT if phase=='pilot' else MAIN
    if root.exists():raise ValueError('attempt exists')
    limits();require_resources(resource_snapshot())
    admission=read(ADMITTED)
    if admission['status']!='VERIFIED_COMPLETE_PILOT' or not admission['native_exit_verified']:raise ValueError('reader admission missing')
    previous=RAW/'drive-reader-pilot-v6'
    if filehash(previous/'COMPLETE.json')!=admission['terminal_sha256']:raise ValueError('admission binding')
    check_pins(read(previous/'PLAN.json')['pins'])
    src=[REPO/p for p in ('runners/drive/suggestion_corpus_v2.py','runners/drive/suggestion_pilot_v2.py','runners/drive/suggestion_main_v2.py','runners/drive/readers.py','runners/drive/readers_low_memory.py','runners/drive/reader_pilot_v6.py','runners/drive/reader_pilot_v4.py','runners/drive/foundation.py','runners/stage14/common.py','runners/stage9/process_identity.py','runners/next_round/queue.py','tests/test_drive_suggestion_corpus.py','docs/design/stage-15/drive/SUGGESTION_CORPUS_V2.md')]
    src += [ADMITTED,previous/'COMPLETE.json',MODELS,PREPARED/'SESSIONS.json',PREPARED/'SOURCE_PINS.json',ROSTER]
    recovery=recovery_inputs();src+=recovery['files']+[REPO/'tests/test_drive_suggestion_recovery.py']
    binding=dict(read(previous/'PLAN.json')['pins']);binding.update(pins(src))
    versions={n:importlib.metadata.version(n) for n in VERSIONS}
    if versions!=read(previous/'PLAN.json')['versions']:raise ValueError('runtime drift')
    plan=dict(at=now(),phase=phase,pins=binding,versions=versions,order=list(ORDER),allocator_cap_MiB=5888,cold_floor_MiB=7424,empty_floor_MiB=7168,working_floor_MiB=1024,maximum_temperature_C=78,tolerance=.02,max_resource_wait_seconds=7200,max_compute_seconds=7200,max_output_bytes=2*1024**3,scientific_admission=False,scope='all exposed suggestion menus; typed/history component separate')
    plan.update(dtype_by_model={name:'float32' for name in ORDER},predecessor_lifetime_charged_seconds=recovery['charged_seconds'])
    if phase=='pilot':plan['max_compute_seconds']=7200-math.ceil(recovery['charged_seconds'])
    if phase=='main':
        landed=REPO/'results/phase_2_4_stage_15/DRIVE/SUGGESTION_PILOT_V2.json'
        receipt=read(landed)
        if receipt['status']!='VERIFIED_COMPLETE_PILOT':raise ValueError('timing pilot not independently landed')
        if receipt['terminal_sha256']!=filehash(PILOT/'COMPLETE.json'):raise ValueError('pilot binding')
        timing=read(PILOT/'SUMMARY.json')
        plan.update(main_bounds(timing))
        plan['pins'].update(pins([landed,PILOT/'COMPLETE.json',PILOT/'SUMMARY.json',PILOT/'CASES.json',PILOT/'CENSUS.json',PILOT/'SELECTION.json']))
    freeze(root/'PLAN.json',plan)
    print('Frozen '+phase+' plan; no automatic dispatch.')

def build_cases():
    sessions=read(PREPARED/'SESSIONS.json');source=read(PREPARED/'SOURCE_PINS.json');check_pins(source)
    roster={r['session']:r for r in read(ROSTER)};groups=[]
    for s in sessions:
        path=REPO/roster[s['session']]['path']
        if filehash(path)!=roster[s['session']]['source_sha256']:raise ValueError('source identity changed')
        with path.open(encoding='utf8') as stream:brief=json.loads(next(stream))['currentDoc']
        cases=[dict(key=row['key'],brief=brief,document=row['document'],menu=row['menu']) for row in s['rows']]
        groups.append(dict(session=s['session'],writer=s['writer'],cases=cases))
    if len(groups)!=1399 or sum(len(g['cases']) for g in groups)!=16855:raise ValueError('source coverage')
    if len({c['key'] for g in groups for c in g['cases']})!=16855 or len({g['session'] for g in groups})!=1399:raise ValueError('duplicate source identity')
    return groups

def census(tok,groups,guard):
    lengths=[];counts=Counter();input_tokens=target_tokens=0
    for i,g in enumerate(groups):
        if i%25==0:guard('census',i)
        for case in g['cases']:
            for condition,context in contexts(tok,case['brief'],case['document']).items():
                inputs=[]
                for target in case['menu']:
                    p=pack(tok,context,target);counts[condition+'_total']+=1
                    if p['eligible']:
                        counts[condition+'_eligible']+=1;counts['eligible']+=1
                        n=len(p['prefix'])+len(p['target']);inputs.append(n)
                        input_tokens+=n;target_tokens+=len(p['target'])
                    else:counts[condition+'_excluded']+=1
                if condition=='c3':lengths.append((case['key'],max(inputs) if inputs else 2049))
    return dict(counts=dict(counts),input_tokens=input_tokens,target_tokens=target_tokens,menus=sum(len(g['cases']) for g in groups)),select_pilot(lengths)

def run(phase):
    root=PILOT if phase=='pilot' else MAIN
    limits();plan=read(root/'PLAN.json');check_pins(plan['pins']);require_resources(resource_snapshot())
    if {n:importlib.metadata.version(n) for n in VERSIONS}!=plan['versions']:raise ValueError('runtime changed')
    with (root/'ATTEMPT.claim').open('x',encoding='utf8') as f:f.write(now()+'\n')
    freeze(root/'OWNER.json',dict(at=now(),native=native_identity(),plan_sha256=filehash(root/'PLAN.json')))
    start=time.monotonic();waited=0.;stop=threading.Event();lock=REPO/'results/.gpu.lock';owned=False;torch=None;model=None;token=f'{os.getpid()} drive-suggestion-{phase}-v2'.encode()
    def deadline():
        if not stop.wait(plan['max_compute_seconds']+plan['max_resource_wait_seconds']+90):
            atomic(root/'FAILED.json',dict(at=now(),status='FAILED',reason='hard wall; inspect owner/lease before recovery'));os._exit(124)
    threading.Thread(target=deadline,daemon=True).start()
    def host_guard(task,progress):
        require_resources(resource_snapshot())
        if time.monotonic()-start-waited>plan['max_compute_seconds']:raise TimeoutError('compute ceiling')
        atomic(root/'PROGRESS.json',dict(at=now(),task=task,progress=progress))
    def wait_gpu(floor,acquire=False):
        nonlocal waited,owned
        began=time.monotonic()
        while True:
            snap=gpu();require_resources(resource_snapshot())
            if snap['free_MiB']>=floor and snap['temperature_C']<=plan['maximum_temperature_C']:
                if not acquire:break
                try:
                    fd=os.open(lock,os.O_CREAT|os.O_EXCL|os.O_WRONLY)
                    try:os.write(fd,token)
                    finally:os.close(fd)
                    owned=True;break
                except FileExistsError:pass
            atomic(root/'PROGRESS.json',dict(at=now(),task='WAITING_RESOURCE',gpu=snap,required_free_MiB=floor))
            if waited+time.monotonic()-began>plan['max_resource_wait_seconds']:raise TimeoutError('resource wait ceiling')
            time.sleep(30)
        waited+=time.monotonic()-began
    try:
        while not (root/'MONITOR_READY.json').exists():
            if time.monotonic()-start>90:raise TimeoutError('monitor handshake')
            time.sleep(.25)
        if read(root/'MONITOR_READY.json')['owner_sha256']!=filehash(root/'OWNER.json'):raise ValueError('monitor binding')
        from transformers import AutoTokenizer,AutoModelForCausalLM
        if phase=='pilot':
            prior=recovery_inputs()['prior']
            groups=read(prior/'CASES.json');censuses=read(prior/'CENSUS.json');selections=read(prior/'SELECTION.json')
            freeze(root/'CASES.json',groups);freeze(root/'CENSUS.json',censuses);freeze(root/'SELECTION.json',selections)
            if any(filehash(root/n)!=filehash(prior/n) for n in ('CASES.json','CENSUS.json','SELECTION.json')):raise ValueError('reused census bytes differ')
            host_guard('verified_input_reuse',len(groups))
        else:groups=read(PILOT/'CASES.json');censuses=read(PILOT/'CENSUS.json');selections={}
        wait_gpu(plan['cold_floor_MiB'],True)
        import torch as torch_module
        torch=torch_module;torch.set_num_threads(1)
        torch.cuda.set_per_process_memory_fraction(plan['allocator_cap_MiB']*2**20/torch.cuda.get_device_properties(0).total_memory)
        summaries={};all_chunks=[];used_bytes=0
        for name in ORDER:
            check_pins(plan['pins']);release_workspace(torch)
            if torch.cuda.memory_allocated() or torch.cuda.memory_reserved():raise ValueError('allocator not empty')
            wait_gpu(plan['empty_floor_MiB'])
            path=verify_model(read(MODELS)[name]);tok=AutoTokenizer.from_pretrained(path,local_files_only=True,trust_remote_code=False,use_fast=True)
            dtype=getattr(torch,plan['dtype_by_model'][name])
            model=AutoModelForCausalLM.from_pretrained(path,local_files_only=True,trust_remote_code=False,torch_dtype=dtype).to('cuda').eval()
            if any(p.device.type!='cuda' or p.dtype!=dtype for p in model.parameters()):raise ValueError('precision/residency')
            extrema=dict(minimum_free_MiB=math.inf,maximum_temperature_C=0.,samples=0)
            def gpu_guard():
                snap=gpu();extrema['minimum_free_MiB']=min(extrema['minimum_free_MiB'],snap['free_MiB']);extrema['maximum_temperature_C']=max(extrema['maximum_temperature_C'],snap['temperature_C']);extrema['samples']+=1;require_resources(resource_snapshot())
                if snap['free_MiB']<plan['working_floor_MiB'] or snap['temperature_C']>plan['maximum_temperature_C']:raise RuntimeError('GPU safety floor')
                if time.monotonic()-start-waited>plan['max_compute_seconds']:raise TimeoutError('compute ceiling')
            gpu_guard();torch.cuda.reset_peak_memory_stats();began=time.monotonic();actual_tokens=actual_input=eligible=items=compressed_bytes=0;checks=[];model_chunks=[]
            for si,g in enumerate(groups):
                cases=g['cases'] if phase=='main' else [c for c in g['cases'] if c['key'] in selections[name]]
                if not cases:continue
                host_guard(name,dict(session=si,total=len(groups),completed_chunks=len(model_chunks)))
                rows=[]
                for case in cases:
                    for condition,context in contexts(tok,case['brief'],case['document']).items():
                        gpu_guard()
                        if name.startswith('pythia'):scores=blocked_score(model,tok,context,case['menu'],torch,block_tokens=32,check=gpu_guard)
                        else:scores=cached_score(model,tok,context,case['menu'],torch)
                        gpu_guard()
                        if phase=='pilot' and not checks and condition=='c0':
                            for target,s in zip(case['menu'],scores):
                                if not s['eligible']:continue
                                reference=direct_loss(model,torch,pack(tok,context,target));gpu_guard()
                                error=max(abs(x-y) for x,y in zip(reference,s['native_token_nll']))
                                freeze(root/name/'DIRECT_CHECK.json',dict(key=case['key'],direct=reference,actual=s['native_token_nll'],max_abs=error,tolerance=plan['tolerance']))
                                if len(reference)!=len(s['native_token_nll']) or error>plan['tolerance']:raise ValueError('numerical reference')
                                checks.append(error);break
                        rows.append(dict(key=case['key'],condition=condition,scores=scores,ranks=menu_ranks(scores)))
                        items+=len(scores)
                        for s in scores:
                            if s['eligible']:eligible+=1;actual_tokens+=s['target_tokens'];actual_input+=s['prefix_tokens']+s['target_tokens']
                validate_rows(rows,cases)
                payload=dict(model=name,session=g['session'],input_sha256=digest(cases),plan_sha256=filehash(root/'PLAN.json'),rows=rows)
                dest=root/name/(digest(g['session'])[:20]+'.json.gz');record=checkpoint(dest,payload,cases)
                record.update(session=g['session'],model=name);load_checkpoint(dest,record,cases,filehash(root/'PLAN.json'),name)
                model_chunks.append(record);all_chunks.append(record);compressed_bytes+=record['bytes'];used_bytes+=record['bytes']
                if used_bytes>plan['max_output_bytes']:raise ValueError('retained byte ceiling')
                atomic(root/'CHUNKS.json',all_chunks)
            elapsed=time.monotonic()-began
            if phase=='pilot' and not checks:raise ValueError('empty numerical control')
            if phase=='main' and (len(model_chunks)!=sum(bool(g['cases']) for g in groups) or eligible!=censuses[name]['counts']['eligible'] or actual_tokens!=censuses[name]['target_tokens'] or actual_input!=censuses[name]['input_tokens'] or items!=sum(censuses[name]['counts'][c+'_total'] for c in ('c0','c1','c2','c3'))):raise ValueError('full census mismatch')
            summaries[name]=dict(items=items,eligible=eligible,target_tokens=actual_tokens,input_tokens=actual_input,seconds=elapsed,compressed_bytes=compressed_bytes,minimum_sampled_free_MiB=extrema['minimum_free_MiB'],maximum_temperature_C=extrema['maximum_temperature_C'],resource_samples=extrema['samples'],peak_allocated_bytes=torch.cuda.max_memory_allocated(),peak_reserved_bytes=torch.cuda.max_memory_reserved(),dtype=str(dtype),all_parameters_cuda=True,versions=plan['versions'],context_window=2048,chunks=len(model_chunks),numerical_checks=checks)
            if phase=='pilot':
                ratio=max(censuses[name]['input_tokens']/max(1,actual_input),censuses[name]['counts']['eligible']/max(1,eligible))
                summaries[name].update(projected_seconds=elapsed*ratio,projected_bytes=compressed_bytes*ratio,projection='max(input-token ratio, eligible-option ratio); main adds 3x safety')
            freeze(root/name/'SUMMARY.json',summaries[name])
            del model;model=None;release_workspace(torch)
        check_pins(plan['pins']);freeze(root/'SUMMARY.json',summaries)
        freeze(root/'COMPLETE.json',dict(at=now(),status='COMPLETE',phase=phase,outputs={p.relative_to(root).as_posix():filehash(p) for p in root.rglob('*') if p.is_file() and (p.suffix=='.json' or p.name.endswith('.json.gz')) and p.name not in ('MONITOR_READY.json','PROGRESS.json')},scientific_admission=False,full_P1_complete=False,write_through_required=True))
    except BaseException as exc:
        freeze(root/'FAILED.json',dict(at=now(),status='FAILED',reason=str(exc),traceback=traceback.format_exc()));raise
    finally:
        stop.set();model=None;gc.collect()
        try:
            if torch is not None and torch.cuda.is_initialized():release_workspace(torch)
        finally:
            if owned and lock.exists() and lock.read_bytes()==token:lock.unlink()
