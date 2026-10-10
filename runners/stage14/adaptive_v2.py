"""P03: text-only LoRA helpers, scored on later actual offered choices.

DESIGN CHECK: LESSONS 3-5; SL2/SL9/SL11. NULL: text adaptation improves only
fluency or sharpness, or wrong-writer adaptation does as well. ALTERNATIVE:
own text improves later recorded choices versus base, matched pool and donor.
No event labels train the adapter. Calibration chooses temperature, not weights.
Sparse real token budgets are retained, not replaced by fabricated training text.
"""
from contextlib import contextmanager
import gc,os,time,uuid
import numpy as np
from .common import REPO,read,freeze,digest,now
from .local import api
from .uncertainty_v2 import contrast
from runners.stage12.local_api import snapshot
from runners.stage13.detectors import cached_model,model_pins

def proper(p,y):
    import math
    valid=len(p)>1 and 0<=y<len(p) and all(math.isfinite(float(x)) and 0<=x<=1 for x in p) and abs(sum(p)-1)<1e-6
    if not valid:return dict(half_brier=1.,log_loss='Infinity',correct=0,valid=False)
    return dict(half_brier=float(.5*sum((x-(i==y))**2 for i,x in enumerate(p))),log_loss=float(-math.log(p[y])) if p[y]>0 else 'Infinity',correct=int(np.argmax(p)==y),valid=True)

@contextmanager
def device(out,minimum=4500):
    import torch
    if api('/api/ps')['models']:raise RuntimeError('Ollama must be unloaded before PyTorch admission')
    if snapshot()['free_MiB']<minimum:raise RuntimeError('insufficient free VRAM for frozen torch block')
    lock=REPO/'results/.gpu.lock';token=f'{os.getpid()} stage14-torch:{uuid.uuid4().hex}'.encode()
    fd=os.open(lock,os.O_CREAT|os.O_EXCL|os.O_WRONLY);os.write(fd,token);os.close(fd)
    torch.set_num_threads(1);torch.cuda.reset_peak_memory_stats()
    freeze(out/'GPU_BEFORE.json',snapshot())
    try:yield torch
    finally:
        gc.collect();torch.cuda.empty_cache()
        freeze(out/'GPU_AFTER.json',dict(snapshot=snapshot(),max_allocated_bytes=torch.cuda.max_memory_allocated(),max_reserved_bytes=torch.cuda.max_memory_reserved()))
        if lock.exists() and lock.read_bytes()==token:lock.unlink()

def guard(model):
    if any(p.device.type!='cuda' for p in model.parameters()):raise RuntimeError('CPU/offloaded parameter violates full residency')
    if snapshot()['free_MiB']<768:raise RuntimeError('free VRAM floor lost; stop this block')

def train(model,tokens,torch,card,tick):
    from peft import LoraConfig,get_peft_model
    model=get_peft_model(model,LoraConfig(r=card['rank'],lora_alpha=2*card['rank'],lora_dropout=0.,target_modules=['q_proj','k_proj','v_proj','o_proj','gate_proj','up_proj','down_proj'],task_type='CAUSAL_LM'))
    model.train();model.config.use_cache=False
    optim=torch.optim.AdamW([p for p in model.parameters() if p.requires_grad],lr=2e-4,weight_decay=.01)
    chunks=[tokens[i:i+256] for i in range(0,len(tokens)-255,256)]
    if not chunks:raise ValueError('no complete native training chunk')
    rng=np.random.default_rng(card['seed']);losses=[];start=time.monotonic()
    for epoch in range(card['epochs']):
        for idx in rng.permutation(len(chunks)):
            ids=torch.tensor([chunks[idx]],device='cuda');optim.zero_grad(set_to_none=True)
            loss=model(input_ids=ids,labels=ids).loss
            if not torch.isfinite(loss):raise ValueError('nonfinite LoRA loss')
            loss.backward();torch.nn.utils.clip_grad_norm_(model.parameters(),1.);optim.step();losses.append(float(loss.detach()))
            if len(losses)%8==0:guard(model);tick(dict(training_steps=len(losses),training_steps_total=len(chunks)*card['epochs']))
    model.eval();model.config.use_cache=True
    return model,dict(steps=len(losses),tokens_per_epoch=len(chunks)*256,epochs=card['epochs'],losses=losses,seconds=time.monotonic()-start)

def prepare_cases(rows,truth,tok,writer,partition):
    cases=[];excluded=[]
    for r in rows:
        if r['writer']!=writer or r['partition']!=partition:continue
        t=truth[r['key']]
        if t['handling'] not in ('accept','edit'):continue
        alts=r['evidence']['alternatives'];indices=r['option_indices']
        if t['selected_index'] not in indices or len(alts)<2:
            excluded.append(dict(key=r['key'],reason='recorded selection not in multi-option support'));continue
        prefix=tok.encode(r['evidence']['document'],add_special_tokens=False)[-256:]
        choices=[tok.encode(a,add_special_tokens=False) for a in alts]
        if not prefix or any(not a or len(a)>256 for a in choices):
            excluded.append(dict(key=r['key'],reason='empty or over-256-token offered continuation'));continue
        cases.append(dict(key=r['key'],writer=writer,prompt=r['prompt'],truth=indices.index(t['selected_index']),prefix=prefix,choices=choices,
            view='prospective final 256 native prefix tokens plus COMPLETE offered continuations',input_digest=digest([prefix,choices])))
    return cases,excluded

def likelihoods(model,cases,torch,tick):
    records=[];start=time.monotonic()
    for i,c in enumerate(cases):
        values=[]
        with torch.inference_mode():
            for option in c['choices']:
                ids=torch.tensor([c['prefix']+option],device='cuda')
                logits=model(input_ids=ids).logits[0,len(c['prefix'])-1:-1].float()
                target=ids[0,len(c['prefix']):]
                ll=torch.log_softmax(logits,-1).gather(1,target[:,None]).sum()
                if not torch.isfinite(ll):raise ValueError('nonfinite conditional likelihood')
                values.append(float(ll))
        records.append(values)
        if (i+1)%16==0:guard(model);tick(dict(scored_choices=i+1,total_choices=len(cases)))
    return records,time.monotonic()-start

def probs(values,temp):
    from scipy.special import softmax
    return softmax(np.array(values)/temp).tolist()

def run(card,out,raw,tick):
    from transformers import AutoTokenizer,AutoModelForCausalLM
    parent=raw/'jobs'/card['requires'][0];rows=read(parent/'READER.json');truth={r['key']:r for r in read(parent/'EVALUATOR.json')};texts=read(parent/'SESSION_CORPORA.json')
    path=cached_model(card['backbone']);actual=model_pins(path)
    if actual!=card['model_files']:raise ValueError('cached model identity changed')
    tok=AutoTokenizer.from_pretrained(path,local_files_only=True,trust_remote_code=False)
    freeze(out/'MODEL.json',dict(backbone=card['backbone'],revision=path.name,files=actual,precision='bfloat16',device='cuda',no_offload=True))
    writers=sorted({r['writer'] for r in rows});results=[];costs={};exclusions=[];done=0
    with device(out,card['memory_MiB']) as torch:
        for writer in writers:
            if done>=card['writer_limit']:break
            calibration_times=[r['timestamp'] for r in rows if r['writer']==writer and r['partition']=='calibration']
            if not calibration_times:
                exclusions.append(dict(writer=writer,reason='no usable calibration opportunity'));continue
            cutoff=min(calibration_times)
            by={w:[] for w in writers}
            for s in texts:
                if s['timestamp']<cutoff:by[s['writer']].append(s['texts'][card['corpus']])
            encoded={w:tok.encode('\n\n'.join(dict.fromkeys(ss)),add_special_tokens=False) for w,ss in by.items()}
            donors=sorted((w for w in writers if w!=writer and len(encoded[w])>=256),key=lambda w:(abs(len(encoded[w])-len(encoded[writer])),w))
            cal,ce=prepare_cases(rows,truth,tok,writer,'calibration');test,te=prepare_cases(rows,truth,tok,writer,'evaluation');exclusions+=ce+te
            if not donors or len(encoded[writer])<256 or not cal or not test:
                exclusions.append(dict(writer=writer,reason='insufficient past-only text/donor or later multi-option choices'));continue
            donor=donors[0];n=min(card['training_tokens'],len(encoded[writer]),len(encoded[donor]));n=n//256*256
            pool=[]
            for w in sorted((w for w in writers if w!=writer),key=lambda w:digest([card['seed'],writer,w])):pool+=encoded[w]
            arms=dict(base=[],own=encoded[writer][:n],pooled=pool[:n],donor=encoded[donor][:n]);score_by={};detail={}
            if any(len(v)!=n for k,v in arms.items() if k!='base'):raise ValueError('unequal training token budgets')
            for arm,tokens in arms.items():
                torch.manual_seed(card['seed']);start=time.monotonic()
                model=AutoModelForCausalLM.from_pretrained(path,local_files_only=True,trust_remote_code=False,torch_dtype=torch.bfloat16).to('cuda')
                guard(model);training=None
                if arm!='base':
                    model,training=train(model,tokens,torch,card,tick)
                    dest=out/'adapters'/digest(writer)[:16]/arm;model.save_pretrained(dest,safe_serialization=True)
                model.eval();cc,cs=likelihoods(model,cal,torch,tick);tt,ts=likelihoods(model,test,torch,tick)
                temps=[(.25),.5,1.,2.,4.]
                selected=min(temps,key=lambda t:(np.mean([proper(probs(v,t),c['truth'])['half_brier'] for v,c in zip(cc,cal)]),t))
                score_by[arm]=[probs(v,selected) for v in tt]
                detail[arm]=dict(training=training,temperature=selected,calibration_raw=cc,evaluation_raw=tt,seconds=time.monotonic()-start,calibration_seconds=cs,evaluation_seconds=ts,train_digest=digest(tokens))
                del model;gc.collect();torch.cuda.empty_cache()
            for i,c in enumerate(test):
                ps={arm:v[i] for arm,v in score_by.items()};ps['uniform']=[1/len(c['choices'])]*len(c['choices'])
                results.append(dict(key=c['key'],writer=writer,prompt=c['prompt'],truth=c['truth'],input_digest=c['input_digest'],probabilities=ps,scores={k:proper(p,c['truth']) for k,p in ps.items()}))
            costs[writer]=dict(cutoff=cutoff,donor=donor,actual_tokens=n,sparse_regime=n<10000,details=detail)
            freeze(out/'writers'/f'{digest(writer)}.json',dict(results=[r for r in results if r['writer']==writer],cost=costs[writer]));done+=1
            tick(dict(completed_writers=done,requested_writer_limit=card['writer_limit']))
    if not results:raise ValueError('no complete eligible text-adaptation comparison')
    freeze(out/'PREDICTIONS.json',results);freeze(out/'COSTS.json',costs);freeze(out/'EXCLUSIONS.json',exclusions)
    freeze(out/'SUMMARY.json',dict(contrasts=[contrast(results,'own',b) for b in ('base','pooled','donor','uniform')],writers=done,
        task='prospective chosen offered continuation conditional on accept/edit; not handling, identity, private thought or preference',
        exposure='descriptive historical corpus; no fresh confirmation',corpus=card['corpus'],rank=card['rank'],seed=card['seed'],training_tokens_cap=card['training_tokens']))
    freeze(out/'ADMISSION.json',dict(admitted=True,memory_and_execution=True,scientific_promotion=False,scope='complete four-arm text adaptation and future choice scoring'))
