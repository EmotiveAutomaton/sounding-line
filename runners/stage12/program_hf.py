"""Serial cached-model generation, raw-token retention and separate admission.

DESIGN CHECK: LESSONS 4-5. NULL: cached weights do not establish capability;
invalid/truncated replies fail admission and are never retried. ALTERNATIVE:
literal known-answer responses admit only this interface. Exact file hashes,
one native GPU owner, finite generation and offline loading guard resource and
source drift. No next-token normalization is mislabeled as elicited confidence.
"""
from contextlib import contextmanager
import gc
import os
from pathlib import Path
import time
import uuid
from .common import REPO,read,freeze,atomic,digest,filehash,admit,now
from . import local_api
from runners.stage9.process_identity import native_identity


@contextmanager
def service(out,card,raw):
    os.environ['HF_HUB_OFFLINE']='1';os.environ['TRANSFORMERS_OFFLINE']='1'
    lock=REPO/'results/.gpu.lock';token=f'{os.getpid()} stage12-hf:{uuid.uuid4().hex}'.encode()
    fd=os.open(lock,os.O_WRONLY|os.O_CREAT|os.O_EXCL)
    try:os.write(fd,token)
    finally:os.close(fd)
    charge=Path(raw)/'charges'/('hf-owner-'+digest(str(out))+'.json');start=time.monotonic();state={'calls':0.}
    freeze(charge,dict(cpu_seconds=0,gpu_seconds=120,diagnostic_gpu_seconds=120 if card.get('diagnostic') else 0,state='reserved'))
    freeze(out/'GPU_OWNER.json',dict(native=native_identity(),at=now(),model=card['hf_model']))
    try:
        resident=local_api.api('/api/ps',timeout=20)['models']
        if resident:
            if any(r.get('digest')!=local_api.MODEL_DIGEST for r in resident):raise RuntimeError('another resident model; no automatic unload')
            # This is a zero-message unload of the known local service model,
            # while holding the same exclusive scientific GPU ownership lock.
            result=local_api.api('/api/chat',dict(model=local_api.MODEL,messages=[],stream=False,keep_alive=0),timeout=30)
            freeze(out/'OLLAMA_UNLOAD.json',result)
        snap=local_api.snapshot();freeze(out/'GPU_ADMISSION.json',snap)
        if snap['free_MiB']<6000 or snap['temperature_C']>78:raise RuntimeError('HF capacity not admitted')
        for p,h in card['model_files'].items():
            if filehash(p)!=h:raise ValueError('cached model file changed')
        import torch
        from transformers import AutoTokenizer,AutoModelForCausalLM
        torch.set_num_threads(2);torch.manual_seed(120923)
        tok=AutoTokenizer.from_pretrained(card['model_path'],local_files_only=True)
        model=AutoModelForCausalLM.from_pretrained(card['model_path'],local_files_only=True,dtype=torch.float16,attn_implementation='eager').eval().to('cuda');model.requires_grad_(False)
        state.update(model=model,tok=tok,torch=torch,deadline=time.monotonic()+card['wall_seconds'])
        def guard(m,i):
            if time.monotonic()>state.get('call_deadline',state['deadline']):raise TimeoutError('bounded native HF generation deadline')
        handle=model.register_forward_pre_hook(guard)
        try:yield state
        finally:handle.remove();state.pop('model',None);del model;gc.collect();torch.cuda.empty_cache()
    finally:
        overhead=max(0,time.monotonic()-start-state['calls'])
        atomic(charge,dict(cpu_seconds=0,gpu_seconds=overhead,diagnostic_gpu_seconds=overhead if card.get('diagnostic') else 0,state='complete',owner_wall_seconds=time.monotonic()-start))
        if lock.exists() and lock.read_bytes()==token:lock.unlink()


def call(req,n,path,state,raw,card):
    path=Path(path);binding=digest(dict(request=req,model=card['hf_model'],files=card['model_files'],output_tokens=1024,context_tokens=4096,temperature=0))
    if (path/'COMPLETE.json').exists():
        saved=read(path/'COMPLETE.json');response=read(path/'RAW.json')
        if saved['binding']!=binding or saved['raw_sha256']!=digest(response) or read(path/'REQUEST.json')!=req:raise ValueError('HF retained request/raw drift')
        try:p=local_api.parse(response,n,req['format'])
        except (ValueError,KeyError,TypeError):p=None
        if p!=saved['probabilities']:raise ValueError('HF parse differs')
        return saved
    if (path/'REQUEST.json').exists():raise RuntimeError('unknown old HF request; no retry')
    admit(dict(gpu_seconds=330,diagnostic_gpu_seconds=330 if card.get('diagnostic') else 0,wall_seconds=330),read(Path(raw)/'CONTRACT.json'),raw)
    freeze(path/'REQUEST.json',req);charge=Path(raw)/'charges'/('hf-'+digest(str(path))+'.json')
    freeze(charge,dict(cpu_seconds=0,gpu_seconds=330,diagnostic_gpu_seconds=330 if card.get('diagnostic') else 0,state='reserved'))
    tok=state['tok'];model=state['model'];torch=state['torch']
    text=tok.apply_chat_template(req['messages'],tokenize=False,add_generation_prompt=True)
    ids=tok(text,return_tensors='pt',add_special_tokens=False).input_ids.to('cuda')
    if ids.shape[1]+1024>4096:raise ValueError('actual HF context exceeds frozen allowance')
    freeze(path/'DISPATCH.json',dict(native=native_identity(),at=now(),binding=binding,input_ids=ids[0].tolist(),gpu=local_api.snapshot()))
    start=time.monotonic();state['call_deadline']=min(state['deadline'],start+300)
    with torch.inference_mode():
        generated=model.generate(ids,max_new_tokens=1024,do_sample=False,use_cache=True,pad_token_id=tok.eos_token_id)
    tokens=generated[0,ids.shape[1]:].tolist();wall=time.monotonic()-start;state['calls']+=wall
    content=tok.decode(tokens,skip_special_tokens=True).strip()
    # No text repair or extraction from surrounding prose: same literal contract.
    response=dict(done=True,done_reason='length' if len(tokens)>=1024 else 'stop',message=dict(content=content),output_ids=tokens,rendered_prompt_sha256=digest(text))
    freeze(path/'RAW.json',response)
    try:p=local_api.parse(response,n,req['format']);error=None
    except (ValueError,KeyError,TypeError) as e:p=None;error=str(e)
    value=freeze(path/'COMPLETE.json',dict(status='complete',binding=binding,raw_sha256=digest(response),probabilities=p,parse_error=error,wall_seconds=wall,model=card['hf_model'],input_tokens=ids.shape[1],output_tokens=len(tokens),after=local_api.snapshot()))
    atomic(charge,dict(cpu_seconds=0,gpu_seconds=wall,diagnostic_gpu_seconds=wall if card.get('diagnostic') else 0,state='complete'))
    return value
