"""Single-owner local transport with strict VRAM/residency admission.

DESIGN CHECK: LESSONS 3-5; SL11 owner exception October 10: strict memory and
residency checks replace the inaccessible per-program driver fallback setting.
NULL: partial residency, context mismatch, low headroom/throughput or uncertain
request parks the block. ALTERNATIVE: exact pinned local packages fit in VRAM
and emit native timing/token receipts. Never close another application's process.
"""
from contextlib import contextmanager
from datetime import datetime, timezone
import json,os,time,uuid,urllib.request
from .common import REPO,freeze,read,digest,now
from runners.stage12.local_api import snapshot
from runners.stage9.process_identity import native_identity

CONTEXT=8192
ENDPOINT='http://127.0.0.1:11435'
def api(path,payload=None,timeout=600):
    if path not in ('/api/chat','/api/generate','/api/ps','/api/version','/api/tags'):raise ValueError('local path outside allowlist')
    req=urllib.request.Request(ENDPOINT+path,data=None if payload is None else json.dumps(payload,ensure_ascii=False,allow_nan=False).encode(),headers={'Content-Type':'application/json'})
    with urllib.request.build_opener(urllib.request.ProxyHandler({})).open(req,timeout=timeout) as r:return json.load(r)

def ready(model,model_digest,need):
    snap=snapshot(); resident=api('/api/ps')['models']; installed=[m for m in api('/api/tags')['models'] if m['name']==model]
    if len(installed)!=1 or installed[0]['digest']!=model_digest:raise ValueError('model identity changed')
    def full(m):
        try: fresh=(datetime.fromisoformat(m['expires_at'].replace('Z','+00:00'))-datetime.now(timezone.utc)).total_seconds()>30
        except (ValueError,TypeError,KeyError): fresh=False
        return fresh and m['name']==model and m['digest']==model_digest and m.get('context_length')==CONTEXT and type(m.get('size')) is int and m['size']>0 and m['size']==m.get('size_vram')
    loaded=len(resident)==1 and full(resident[0])
    if resident and not loaded:return dict(ready=False,reason='incompatible or partially resident model; explicit unload required',snapshot=snap)
    required=1024 if loaded else need+1024
    return dict(ready=snap['free_MiB']>=required and snap['temperature_C']<=78,required_free_MiB=required,snapshot=snap,resident=resident,endpoint=ENDPOINT,
        reason='free-memory and full-residency admission',server=api('/api/version'))

@contextmanager
def service(out,card):
    lock=REPO/'results/.gpu.lock';token=f'{os.getpid()} stage14:{uuid.uuid4().hex}'.encode()
    fd=os.open(lock,os.O_WRONLY|os.O_CREAT|os.O_EXCL)
    try:os.write(fd,token)
    finally:os.close(fd)
    state=dict(uncertain=False)
    freeze(out/'GPU_OWNER.json',dict(native=native_identity(),at=now(),model=card['model'],digest=card['model_digest']))
    try:
        check=ready(card['model'],card['model_digest'],card['memory_MiB']);freeze(out/'GPU_ADMISSION.json',check)
        if not check['ready']:raise RuntimeError('resource held: '+check['reason'])
        yield state
    finally:
        if not state['uncertain']:
            try: api('/api/generate',dict(model=card['model'],keep_alive=0),timeout=60)
            except Exception: state['uncertain']=True
        if not state['uncertain'] and lock.exists() and lock.read_bytes()==token:lock.unlink()

def call(req,path,state,card):
    binding=digest(dict(request=req,model_digest=card['model_digest']))
    if (path/'RECEIPT.json').exists():
        r=read(path/'RECEIPT.json')
        if r['binding']!=binding or r['raw_sha256']!=digest(read(path/'RAW.json')):raise ValueError('saved response changed')
        return read(path/'RAW.json'),r
    if (path/'REQUEST.json').exists():raise RuntimeError('unknown earlier request; no retry')
    check=ready(card['model'],card['model_digest'],card['memory_MiB'])
    if not check['ready']:raise RuntimeError('resource changed before request')
    freeze(path/'REQUEST.json',req);start=time.monotonic()
    freeze(path/'DISPATCH.json',dict(at=now(),native=native_identity(),binding=binding,snapshot=check['snapshot'],reserved_seconds=600))
    try: response=api('/api/chat',req,timeout=600)
    except BaseException:state['uncertain']=True;raise
    elapsed=time.monotonic()-start;freeze(path/'RAW.json',response)
    receipt=dict(binding=binding,raw_sha256=digest(response),wall_seconds=elapsed,at=now(),
        prompt_tokens=response.get('prompt_eval_count'),output_tokens=response.get('eval_count'),
        timings_ns={k:response.get(k) for k in ('load_duration','prompt_eval_duration','eval_duration','total_duration')})
    freeze(path/'RECEIPT.json',receipt)
    resident=api('/api/ps')['models']
    if len(resident)!=1 or resident[0].get('digest')!=card['model_digest'] or resident[0].get('size')!=resident[0].get('size_vram') or resident[0].get('context_length')!=CONTEXT:
        raise RuntimeError('full GPU residency not verified after response; park block')
    free=snapshot()
    freeze(path/'AFTER.json',dict(resident=resident,snapshot=free))
    if free['free_MiB']<768:raise RuntimeError('GPU free-memory reserve lost')
    n=response.get('eval_count',0);ns=response.get('eval_duration',0)
    if n>=32 and (ns<=0 or n/(ns/1e9)<5):raise RuntimeError('throughput below frozen 5 tokens/s floor; resource diagnosis required')
    if response.get('prompt_eval_count',0)+response.get('eval_count',0)>CONTEXT:raise ValueError('native context overflow')
    return response,receipt
