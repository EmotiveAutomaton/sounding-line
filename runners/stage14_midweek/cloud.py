"""Bounded Modal lane, callable only through runners/gear3.py stage14.

DESIGN CHECK: LESSONS 3-5; known-bad transport preserved historically. Both
hypotheses require exact apparatus, actual token count, complete raw replay,
fresh account and finite reservation. Invalid pilot blocks main; no repeat.
"""
import argparse,inspect,json,math,threading,time
from pathlib import Path
from .data import ROOT,RAW
from .protocol import render,tokenizer,verify_rows,SCHEMA,parse
from .budget import reserve,reconcile,cost,account_headroom
from runners.stage14.common import REPO,read,freeze,atomic,digest,filehash
IMAGE='ollama/ollama@sha256:9d30908e41144b1f1da89b9d8e33c07e4aeb43ff41a8660241b1686e2cc330ad'
MODEL='qwen3.5:27b'
MODEL_SHA='7653528ba5cba4dd8e19da24aaddc7f4d0b5ecd93571c0825dfd4137958ec06e'

def pilot_planning():
    """Pilot-only variance estimate, retained separately from the frozen PLAN."""
    import statistics
    from .data import ACTIONS
    terminal=read(RAW/'modal-pilot-v1/restored/TERMINAL.json')
    bundles={r['id']:r for r in read(RAW/'data-v2/READER.json') if r['pilot']}
    targets={r['key']:r for r in read(RAW/'data-v2/EVALUATOR.json') if r['pilot']}
    scores={}
    for row in terminal['rows']:
        if row['id'].endswith('-c2'):continue
        bundle=bundles[row['id']];p=parse(row['response']['response'])['probabilities'];truth=ACTIONS.index(targets[bundle['target']]['handling'])
        scores[(bundle['target'],bundle['arm'])]=.5*sum((v-(i==truth))**2 for i,v in enumerate(p))
    writers=sorted({r['writer'] for r in targets.values()});gains=[]
    for writer in writers:
        gains.append(statistics.mean(scores[(t['key'],'H3')]-scores[(t['key'],'H2')] for t in targets.values() if t['writer']==writer))
    n=len({r['writer'] for r in read(RAW/'data-v2/EVALUATOR.json') if not r['pilot']})
    sd=statistics.stdev(gains)
    return dict(pilot_writers=len(writers),main_writers=n,pilot_writer_sd=sd,empirical_unadjusted_mde=2.8016*sd/math.sqrt(n),
        empirical_first_holm_mde=3.68*sd/math.sqrt(n),scope='three discarded writers, serial H2 minus H3 only; unstable planning estimate, not power certification for every contrast',
        pilot_archive_sha256=filehash(RAW/'modal-pilot-v1/OUTPUT.zip'))

def remote_run(volume,invocation,payload,expires,campaign_root='/campaign'):
    import concurrent.futures,hashlib,json,os,subprocess,threading,time,urllib.request,zipfile
    from pathlib import Path
    base=Path(campaign_root);root=base/'stage14-maker'/invocation;volume.reload()
    if root.exists():raise RuntimeError('existing remote attempt; retrieve, never repeat')
    root.mkdir(parents=True);lock=threading.Lock()
    def sha(x):return hashlib.sha256(json.dumps(x,sort_keys=True,ensure_ascii=False,allow_nan=False,separators=(',',':')).encode()).hexdigest()
    def save(name,value):
        with lock:
            p=root/name;p.parent.mkdir(parents=True,exist_ok=True)
            with p.open('x',encoding='utf8') as f:json.dump(value,f,ensure_ascii=False,allow_nan=False);f.flush();os.fsync(f.fileno())
            volume.commit()
    entered=time.time();save('START.json',dict(entered=entered,expires=expires,payload_sha256=sha(payload)))
    server=None;rows=[];error=None;status='FAILED';runtime=None;ended=threading.Event()
    def api(path,data=None,timeout=30):
        req=urllib.request.Request('http://127.0.0.1:11434'+path,data=None if data is None else json.dumps(data).encode(),headers={'Content-Type':'application/json'})
        with urllib.request.build_opener(urllib.request.ProxyHandler({})).open(req,timeout=timeout) as f:return json.load(f)
    def stop():
        if server is not None and server.poll() is None:server.terminate()
    def watchdog():
        if not ended.wait(max(0,expires-time.time()-20)):stop()
    threading.Thread(target=watchdog,daemon=True).start()
    try:
        env=dict(os.environ,OLLAMA_MODELS=str(base/'models'),OLLAMA_HOST='127.0.0.1:11434',OLLAMA_NUM_PARALLEL='2',OLLAMA_MAX_LOADED_MODELS='1')
        with (root/'server.log').open('w',encoding='utf8') as log:
            server=subprocess.Popen(['ollama','serve'],env=env,stdout=log,stderr=subprocess.STDOUT)
            startup=time.time()+60
            while True:
                try:version=api('/api/version');break
                except OSError:
                    if time.time()>startup or server.poll() is not None:raise RuntimeError('model server startup failed')
                    time.sleep(.5)
            tags=api('/api/tags')['models'];matches=[m for m in tags if m['name']==payload['model']]
            if version['version']!='0.32.14' or len(matches)!=1 or matches[0]['digest']!=payload['model_digest']:raise ValueError('retained model or server mismatch; no pull or replacement')
            load_start=time.time();save('LOAD.json',api('/api/generate',dict(model=payload['model'],stream=False,keep_alive=-1,options={'num_ctx':16384,'num_thread':2}),timeout=300))
            models=api('/api/ps')['models'];runtime=dict(version=version,models=models,load_seconds=time.time()-load_start,
                device=subprocess.check_output(['nvidia-smi','--query-gpu=name,memory.total,memory.free','--format=csv,noheader'],text=True))
            save('RUNTIME.json',runtime)
            if len(models)!=1 or models[0]['digest']!=payload['model_digest'] or models[0].get('size_vram',0)<models[0]['size'] or models[0].get('context_length')!=16384 or models[0]['details']['quantization_level']!='Q4_K_M' or 'L40S' not in runtime['device']:raise ValueError('full GPU residency/apparatus not verified')
            def call(original):
                if expires-time.time()<payload['call_seconds']+45:raise TimeoutError('remaining reservation cannot contain next full call')
                req=dict(model=payload['model'],prompt=original['prompt'],raw=True,think=False,format=payload['schema'],stream=False,keep_alive=-1,
                         options=dict(num_ctx=16384,num_predict=2048,num_thread=2,temperature=0,seed=1001))
                started=time.time();save('calls/'+original['id']+'/REQUEST.json',dict(request=original,wire=req,started=started))
                response=api('/api/generate',req,timeout=payload['http_seconds'])
                row=dict(id=original['id'],request=original,response=response,seconds=time.time()-started)
                save('calls/'+original['id']+'/RESPONSE.json',row)
                return row
            for phase in payload['phases']:
                group=phase['rows'];concurrency=phase['concurrency']
                with concurrent.futures.ThreadPoolExecutor(max_workers=concurrency) as pool:
                    for start in range(0,len(group),concurrency):
                        futures=[pool.submit(call,r) for r in group[start:start+concurrency]]
                        completed,pending=concurrent.futures.wait(futures,timeout=payload['call_seconds'])
                        if pending:stop();raise TimeoutError('per-call allowance exhausted; HTTP timeout is deliberately longer')
                        rows.extend(f.result() for f in futures)
                        resident=api('/api/ps')['models']
                        save('residency/'+str(len(rows))+'.json',dict(at=time.time(),models=resident))
                        if len(resident)!=1 or resident[0]['digest']!=payload['model_digest'] or resident[0].get('size_vram',0)<resident[0]['size'] or resident[0].get('context_length')!=16384:raise ValueError('runtime residency lost; no fallback accepted')
            status='COMPLETE'
    except Exception as exc:error=repr(exc)
    finally:
        stop()
        if server is not None:
            try:server.wait(timeout=5)
            except subprocess.TimeoutExpired:server.kill();server.wait(timeout=5)
        ended.set()
        terminal=dict(status=status,error=error,owner_ended=True,entered_at=entered,ended_at=time.time(),rows=rows,runtime=runtime,payload_sha256=sha(payload))
        save('TERMINAL.json',terminal)
    archive=root.parent/(invocation+'.zip')
    with zipfile.ZipFile(archive,'x',compression=zipfile.ZIP_DEFLATED) as z:
        inventory={}
        for p in sorted(root.rglob('*')):
            if p.is_file():
                b=p.read_bytes();name=p.relative_to(root).as_posix();inventory[name]=dict(bytes=len(b),sha256=hashlib.sha256(b).hexdigest());z.writestr(name,b)
        z.writestr('INVENTORY.json',json.dumps(inventory,sort_keys=True))
    volume.commit()
    return dict(terminal,archive_path=archive.relative_to(base).as_posix(),archive_sha256=hashlib.sha256(archive.read_bytes()).hexdigest())

def prepare_plan():
    data=RAW/'data-v2';reader=read(data/'READER.json');tok=tokenizer();rendered=[];overflow=[]
    for row in reader:
        if row['arm'] not in ('H0','H1','H2','H3'):continue
        try:r=render(row,tok)
        except ValueError as exc:overflow.append(dict(id=row['id'],writer=row['writer'],reason=str(exc)));continue
        rendered.append(dict(r,pilot=row['pilot']))
    if overflow:freeze(RAW/'CONTEXT_REFUSALS.json',overflow);raise ValueError('context overflow requires outcome-blind whole-writer roster review before launch')
    pilot=[{k:v for k,v in r.items() if k!='pilot'} for r in rendered if r['pilot']]
    main=[{k:v for k,v in r.items() if k!='pilot'} for r in rendered if not r['pilot']]
    if len(pilot)!=48:raise ValueError('literal four-arm pilot missing')
    second=[dict(r,id=r['id']+'-c2') for r in pilot]
    freeze(RAW/'MODAL_REQUESTS.json',dict(pilot=pilot,pilot_concurrency2=second,main=main))
    pins={str(p.relative_to(REPO)):filehash(p) for p in (REPO/'runners/stage14_midweek').glob('*.py')}
    for p in [REPO/'runners/gear3.py',REPO/'runners/stage14/common.py',ROOT/'APPROVAL.json',RAW/'MODAL_REQUESTS.json',*data.glob('*.json'),*(RAW/'tokenizer').glob('*')]:pins[str(p.relative_to(REPO))]=filehash(p)
    plan=dict(campaign='G3-S14-MAKER-1',source_pins=pins,approval_sha256=filehash(ROOT/'APPROVAL.json'),
        data_version='data-v2',pilot_calls=96,main_calls=len(main),pilot_seconds=3300,call_seconds=240,http_seconds=300,
        modal_model=MODEL,model_digest=MODEL_SHA,image=IMAGE,deadline='2026-10-16T17:00:00+00:00',
        optional_profiles='paired M1/M0 only; deferred if API access unavailable',
        primary_contrasts=['R27.H1-B-pop']+[f'{reader}.H2-{rival}' for reader in ('R27','RO') for rival in ('B-pop',reader+'.H3',reader+'.H0','B-writer','B-mixlogit')],
        normalization='Accept sum within .01, normalize once, then require all normalized probabilities within [.01,.97]. No clipping, repair or reask.',
        scope='descriptive historical human decisions, shared history/donor pool, no untouched confirmation or human value identification')
    freeze(ROOT/'PLAN.json',plan);return {k:plan[k] for k in ('pilot_calls','main_calls','pilot_seconds')}

def cli(argv):
    p=argparse.ArgumentParser();p.add_argument('phase',choices=['prepare','pilot','main']);p.add_argument('--account',type=Path);a=p.parse_args(argv)
    if a.phase=='prepare':print(json.dumps(prepare_plan()));return
    import importlib.metadata
    if importlib.metadata.version('modal')!='1.5.4':raise ValueError('unadmitted Modal SDK')
    plan=read(ROOT/'PLAN.json')
    for name,expected in plan['source_pins'].items():
        if filehash(REPO/name)!=expected:raise ValueError('frozen input/source changed: '+name)
    account=read(a.account)
    if account['status']!='VERIFIED' or time.time()-account['observed_at']>86400 or not account['payment_method_present'] or account['other_workloads']!='retained-storage-only':raise ValueError('fresh account readiness missing')
    requests=read(RAW/'MODAL_REQUESTS.json');seconds=3300;call_seconds=240;http_seconds=300;planning=None
    phases=[dict(concurrency=1,rows=requests['pilot']),dict(concurrency=2,rows=requests['pilot_concurrency2'])]
    if a.phase=='main':
        gate=read(RAW/'modal-pilot-v1/COMPLETE.json')
        if gate.get('valid')!=96 or gate.get('plan_sha256')!=digest(plan):raise ValueError('literal full-valid pilot and replay required')
        timings=gate['call_seconds'];p99=sorted(timings)[math.ceil(.99*len(timings))-1]
        call_seconds=max(240,math.ceil(2*p99));http_seconds=max(300,math.ceil(3*p99),call_seconds+30)
        seconds=math.ceil(1.4*(len(requests['main'])*p99/2+gate['load_seconds']+180))
        if cost(seconds)>1400:raise ValueError('whole main exceeds envelope; no silent shrink or control removal')
        planning=pilot_planning()
        phases=[dict(concurrency=2,rows=requests['main'])]
    from datetime import datetime
    if time.time()+seconds>=datetime.fromisoformat(plan['deadline']).timestamp():raise ValueError('allocation cannot finish before reporting reserve')
    from runners import gear3
    if account_headroom(account,gear3.load_ledger()['runs'])<cost(seconds):raise ValueError('account lacks conservative gross/net headroom')
    ident='modal-'+a.phase+'-v1';folder=RAW/ident
    if folder.exists():raise ValueError('existing attempt; retrieval only')
    payload=dict(model=MODEL,model_digest=MODEL_SHA,schema=SCHEMA,phases=phases,call_seconds=call_seconds,http_seconds=http_seconds)
    import modal
    from modal._utils.async_utils import synchronizer
    from modal_proto import api_pb2
    client=modal.Client.from_env()
    @synchronizer.create_blocking
    async def identity(bound):return await bound.stub.TokenInfoGet(api_pb2.TokenInfoGetRequest(),timeout=20,retry=None)
    if identity(client).workspace_name!=account['workspace']:raise ValueError('account workspace mismatch')
    reservation=reserve(ident,'P' if a.phase=='pilot' else 'M-27',cost(seconds),digest(plan),seconds)
    freeze(folder/'RESERVATION.json',reservation);freeze(folder/'PAYLOAD.json',payload);freeze(folder/'ACCOUNT.json',account)
    freeze(folder/'ADMISSION.json',dict(plan_sha256=digest(plan),account_sha256=filehash(folder/'ACCOUNT.json'),seconds=seconds,
        call_seconds=call_seconds,http_seconds=http_seconds,required_cents=cost(seconds),pilot_planning=planning,main_requires_agent_pilot_landing=True))
    app=modal.App('sounding-line-stage14-maker');call=None;done=threading.Event()
    @synchronizer.create_blocking
    async def stop_app(bound,app_id):return await bound.stub.AppStop(api_pb2.AppStopRequest(app_id=app_id,source=api_pb2.APP_STOP_SOURCE_CLI),timeout=20,retry=None)
    def cancel():
        evidence={}
        try:
            if app.app_id:evidence['app_stop']=str(stop_app(client,app.app_id))
        except Exception as exc:evidence['stop_error']=type(exc).__name__
        try:
            if call is not None:call.cancel(terminate_containers=True);evidence['call_cancel']=True
        except Exception as exc:evidence['cancel_error']=type(exc).__name__
        atomic(folder/'CANCELLATION.json',evidence)
    def watchdog():
        if not done.wait(max(0,reservation['expires']-time.time())):cancel()
    threading.Thread(target=watchdog,daemon=True).start();allocated=time.time()
    try:
        volume=modal.Volume.from_name('sounding-line-g3-round1',create_if_missing=False,client=client,environment_name=account['environment'])
        source=inspect.getsource(remote_run)
        def execute(ident,payload,expires):
            namespace={};exec(source,namespace);return namespace['remote_run'](volume,ident,payload,expires)
        image=modal.Image.from_registry(IMAGE,add_python='3.13').entrypoint([])
        function=app.function(image=image,gpu='L40S',cpu=(2,2),memory=(32768,32768),timeout=seconds,retries=0,max_containers=1,scaledown_window=2,volumes={'/campaign':volume},serialized=True,include_source=False)(execute)
        with app.run(detach=False,client=client,environment_name=account['environment']):
            freeze(folder/'APP.json',dict(app_id=app.app_id,expires=reservation['expires']))
            call=function.spawn(ident,payload,reservation['expires']);freeze(folder/'CALL.json',dict(call_id=call.object_id,app_id=app.app_id))
            terminal=call.get(timeout=max(1,reservation['expires']-time.time()));freeze(folder/'RETURN.json',terminal)
            if terminal['archive_path']!='stage14-maker/'+ident+'.zip':raise ValueError('unrecognized retrieval path')
            archive=folder/'OUTPUT.zip'
            with archive.open('xb') as f:
                for block in volume.read_file(terminal['archive_path']):f.write(block)
            from runners.stage12.cloud import restore
            restored=restore(archive,folder/'restored',terminal['archive_sha256'])
            if restored!={k:v for k,v in terminal.items() if k not in ('archive_path','archive_sha256')}:raise ValueError('returned archive mismatch')
        if terminal['payload_sha256']!=digest(payload) or not terminal['owner_ended']:raise ValueError('owner binding mismatch')
        reconcile(ident,status=terminal['status'],measured_seconds=time.time()-allocated+2,owner_ended=True,proof_sha256=filehash(archive))
        if terminal['status']!='COMPLETE':raise ValueError('incomplete remote attempt; raw retained')
        valid=verify_rows(terminal['rows'],[r for phase in phases for r in phase['rows']])
        freeze(folder/'REPLAY.json',dict(ids=[r['id'] for r in terminal['rows']],valid=valid,inference_calls=0,system_half_brier_invalid=1,system_log_loss_invalid=-math.log(.01)))
        if a.phase=='pilot' and not all(valid):raise ValueError('contract-invalid pilot; no automatic retry')
        if a.phase=='main' and 1-sum(valid)/len(valid)>.05:raise ValueError('main invalid rate exceeds five percent; all raw outputs retained')
        freeze(folder/'COMPLETE.json',dict(status='COMPLETE',valid=sum(valid),attempted=len(valid),plan_sha256=digest(plan),archive_sha256=filehash(archive),
            call_seconds=[r['seconds'] for r in terminal['rows']],load_seconds=terminal['runtime']['load_seconds'],owner_ended=True))
    except BaseException as exc:
        cancel();freeze(folder/'FAILED.json',dict(status='FAILED',error=str(exc),type=type(exc).__name__,at=time.time(),reservation_retained_unless_reconciled=True));raise
    finally:done.set()
