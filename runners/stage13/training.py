"""Full-tuned RoBERTa rival, never dispatched in Gear 1.

DESIGN CHECK: LESSONS 3-5. NULL: unknown GPU owner or expired whole block refuses;
shuffled labels are not an admission shortcut. ALTERNATIVE: all model parameters
train, development loss chooses an epoch, calibration/reserve remain unopened.
"""
from pathlib import Path
import math
import os
import time
import uuid
from .common import RAW,REPO,bound,freeze,now,SEED
from .detectors import cached_model,model_pins


def train(rows,dev,out,tick,raw=RAW):
    bound(raw,dict(resource='gpu',wall_seconds=14400))
    from runners.stage12.local_api import snapshot
    if snapshot()['free_MiB']<7500:raise RuntimeError('full tuning needs 7500 MiB actual free; no eviction')
    import torch
    from transformers import AutoTokenizer,AutoModelForSequenceClassification,get_linear_schedule_with_warmup
    from torch.utils.data import DataLoader
    torch.set_num_threads(1);torch.manual_seed(SEED)
    if not torch.cuda.is_available():raise RuntimeError('CUDA unavailable')
    lock=REPO/'results/.gpu.lock';contents=f'{os.getpid()} stage13-training:{uuid.uuid4().hex}'.encode()
    fd=os.open(lock,os.O_WRONLY|os.O_CREAT|os.O_EXCL)
    try:os.write(fd,contents)
    finally:os.close(fd)
    try:
        path=cached_model('roberta-base');tok=AutoTokenizer.from_pretrained(path,local_files_only=True,trust_remote_code=False)
        model=AutoModelForSequenceClassification.from_pretrained(path,num_labels=2,local_files_only=True,trust_remote_code=False).to('cuda')
        for p in model.parameters():p.requires_grad_(True)
        # Fixed source/label ordering is shuffled by a seeded torch Generator.
        def collate(batch):
            encoded=tok([r['text'] for r in batch],padding=True,truncation=True,max_length=512,return_tensors='pt')
            encoded['labels']=torch.tensor([r['label'] for r in batch]);return {k:v.to('cuda') for k,v in encoded.items()}
        generator=torch.Generator().manual_seed(SEED)
        loader=DataLoader(rows,batch_size=2,shuffle=True,generator=generator,collate_fn=collate,num_workers=0)
        val=DataLoader(dev,batch_size=2,shuffle=False,collate_fn=collate,num_workers=0)
        optim=torch.optim.AdamW(model.parameters(),lr=2e-5,weight_decay=.01)
        steps=math.ceil(len(loader)/8)*3;scheduler=get_linear_schedule_with_warmup(optim,num_warmup_steps=int(.06*steps),num_training_steps=steps)
        freeze(out/'RECIPE.json',dict(model_revision=path.name,files=model_pins(path),epochs=3,max_tokens=512,batch=2,accumulation=8,learning_rate=2e-5,weight_decay=.01,warmup_fraction=.06,selection='minimum development cross-entropy',all_parameters_trainable=True,seed=SEED))
        best=float('inf');history=[]
        for epoch in range(3):
            model.train();optim.zero_grad();losses=[]
            for i,batch in enumerate(loader):
                tick();loss=model(**batch).loss;losses.append(float(loss));(loss/8).backward()
                if (i+1)%8==0 or i+1==len(loader):
                    torch.nn.utils.clip_grad_norm_(model.parameters(),1.);optim.step();scheduler.step();optim.zero_grad()
            model.eval();total=0.;count=0
            with torch.inference_mode():
                for batch in val:
                    tick();n=len(batch['labels']);total+=float(model(**batch).loss)*n;count+=n
            value=total/count;history.append(dict(epoch=epoch+1,train_loss=sum(losses)/len(losses),development_loss=value))
            if value<best:
                best=value;model.save_pretrained(out/'best',safe_serialization=True);tok.save_pretrained(out/'best')
        result=dict(status='complete',history=history,selected_development_loss=best,checkpoint_files=model_pins(out/'best'),reserved_opened=False)
        freeze(out/'TRAINED.json',result);return result
    finally:
        if lock.exists() and lock.read_bytes()==contents:lock.unlink()
        if 'model' in locals():del model
        torch.cuda.empty_cache()


def evaluate(checkpoint,partitions,out,tick,raw=RAW):
    from .common import read
    from .scoring import threshold,detection_report
    from runners.stage12.local_api import snapshot
    import torch
    from transformers import AutoTokenizer,AutoModelForSequenceClassification
    bound(raw,dict(resource='gpu',wall_seconds=14400))
    if snapshot()['free_MiB']<7500:raise RuntimeError('GPU headroom below frozen comparator floor')
    trained=read(checkpoint.parent/'TRAINED.json')
    if model_pins(checkpoint)!=trained['checkpoint_files']:raise ValueError('trained checkpoint changed')
    lock=REPO/'results/.gpu.lock';contents=f'{os.getpid()} stage13-roberta-eval:{uuid.uuid4().hex}'.encode()
    fd=os.open(lock,os.O_WRONLY|os.O_CREAT|os.O_EXCL)
    try:os.write(fd,contents)
    finally:os.close(fd)
    try:
        tok=AutoTokenizer.from_pretrained(checkpoint,local_files_only=True);model=AutoModelForSequenceClassification.from_pretrained(checkpoint,local_files_only=True).to('cuda').eval();scored={}
        for part in ('calibration','development','reserve'):
            scored[part]=[];rows=partitions[part]
            for i in range(0,len(rows),8):
                tick();batch=rows[i:i+8];inputs=tok([r['text'] for r in batch],padding=True,truncation=True,max_length=512,return_tensors='pt').to('cuda')
                with torch.inference_mode():values=torch.softmax(model(**inputs).logits.float(),-1)[:,1].cpu().tolist()
                for r,v in zip(batch,values):
                    record=dict(key=r['key'],unit=r['unit'],label=r['label'],roberta=v);scored[part].append(record);freeze(out/'rows'/f"{r['key']}.json",record)
            if part=='calibration':
                cuts={str(q):threshold([r['roberta'] for r in scored[part] if not r['label']],q) for q in (.01,.05)};freeze(out/'CALIBRATION.json',cuts)
            if part=='development':freeze(out/'FROZEN_COMPARATOR.json',dict(cuts=cuts,recipe='single predeclared full-tuned comparator; no reserve selection',promotion_margin=.03))
        result=dict(status='complete',comparisons={p:detection_report(rs,'roberta',cuts) for p,rs in scored.items()},scope='full-tuned model, independent calibration thresholds, fixed 512 native tokens; comparator to predeclared A roster')
        freeze(out/'ANALYSIS.json',result);return result
    finally:
        if lock.exists() and lock.read_bytes()==contents:lock.unlink()
        if 'model' in locals():del model
        torch.cuda.empty_cache()
