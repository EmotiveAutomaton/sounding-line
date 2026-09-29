"""Complete the strong comparator and paired diagnostic uncertainty, no refit.

DESIGN CHECK: LESSONS 3-5. NULL: identical predictions give zero paired gain;
changed frozen checkpoints/cuts or missing rows refuse comparison. ALTERNATIVE:
known improvement yields positive recall gain on both declared estimands. Human
error differences are paired separately. Post-exposure intervals are descriptive.
"""
from pathlib import Path
from collections import defaultdict
import os
import time
import uuid
import numpy as np
from .common import REPO, read, freeze, atomic, now, bound
from .detectors import model_pins
from .scoring import detection_report


def paired(rows,left,right,left_cut,right_cut,draws=4000,seed=130929):
    if not rows or len({r['key'] for r in rows})!=len(rows):raise ValueError('duplicate or missing rows')
    groups=defaultdict(list)
    for r in rows:
        if r['label'] not in (0,1):raise ValueError('invalid label')
        for name in (left,right):
            if not 0<=r[name]<=1:raise ValueError('invalid probability')
        groups[r['unit']].append(r)
    units=sorted(groups);values=[]
    for unit in units:
        rs=groups[unit];pos=[r for r in rs if r['label']];neg=[r for r in rs if not r['label']]
        delta=lambda r:int(r[left]>left_cut)-int(r[right]>right_cut)
        values.append([sum(map(delta,pos)),len(pos),sum(map(delta,neg)),len(neg)])
    a=np.array(values,dtype=float);rng=np.random.default_rng(seed)
    def metrics(v):
        total=v.sum(0);positive=v[:,1]>0;negative=v[:,3]>0
        return dict(pooled_recall_gain=float(total[0]/total[1]) if total[1] else None,
            source_average_recall_gain=float(np.mean(v[positive,0]/v[positive,1])) if positive.any() else None,
            human_false_positive_difference=float(total[2]/total[3]) if total[3] else None)
    point=metrics(a);boots=defaultdict(list)
    if len(units)>1:
        for _ in range(draws):
            for k,v in metrics(a[rng.integers(0,len(units),len(units))]).items():
                if v is not None:boots[k].append(v)
    result={k:dict(mean=v,low=float(np.quantile(boots[k],.025)) if boots[k] else None,
                   high=float(np.quantile(boots[k],.975)) if boots[k] else None,
                   defined_resamples=len(boots[k])) for k,v in point.items()}
    return dict(units=len(units),rows=len(rows),draws=draws,seed=seed,estimates=result,
        method='paired source-component bootstrap; pooled ratio and equal-source mean kept separate',
        scope='post-exposure descriptive diagnostic; not a retroactive promotion gate')


def strong_extension(card,out,raw,tick):
    from runners.stage12.local_api import snapshot
    original=raw.parent;args=card['args'];checkpoint=original/'jobs'/args['training']/'best'
    trained=read(checkpoint.parent/'TRAINED.json')
    if model_pins(checkpoint)!=trained['checkpoint_files']:raise ValueError('checkpoint changed')
    cuts=read(original/'jobs'/args['calibration']/'CALIBRATION.json')
    rows=read(original/args['rows'])
    bound(raw,dict(resource='gpu',wall_seconds=card['wall_seconds']))
    if snapshot()['free_MiB']<7500:raise RuntimeError('unchanged strong-comparator memory floor')
    import torch
    from transformers import AutoTokenizer,AutoModelForSequenceClassification
    torch.set_num_threads(1)
    lock=REPO/'results/.gpu.lock';owner=f'{os.getpid()} stage13-healing:{uuid.uuid4().hex}'.encode()
    fd=os.open(lock,os.O_WRONLY|os.O_CREAT|os.O_EXCL)
    try:os.write(fd,owner)
    finally:os.close(fd)
    try:
        tok=AutoTokenizer.from_pretrained(checkpoint,local_files_only=True)
        model=AutoModelForSequenceClassification.from_pretrained(checkpoint,local_files_only=True).to('cuda').eval()
        freeze(out/'FROZEN_COMPARATOR.json',dict(checkpoint_files=trained['checkpoint_files'],cuts=cuts,
            scope='existing selected model and original cuts; no refit; extension selected before this new comparison'))
        records=[]
        for i in range(0,len(rows),8):
            tick();batch=rows[i:i+8]
            inputs=tok([r['text'] for r in batch],padding=True,truncation=True,max_length=512,return_tensors='pt').to('cuda')
            with torch.inference_mode():values=torch.softmax(model(**inputs).logits.float(),-1)[:,1].cpu().tolist()
            for r,v in zip(batch,values):
                if not 0<=v<=1:raise ValueError('invalid strong-detector output')
                row=dict(key=r['key'],unit=r['unit'],label=r['label'],roberta=v)
                freeze(out/'rows'/f"{r['key']}.json",row);records.append(row)
            atomic(out/'PROGRESS.json',dict(at=now(),done=len(records),total=len(rows)))
        result=dict(rows=records,cuts=cuts)
        freeze(out/'PREDICTIONS.json',result)
        freeze(out/'ANALYSIS.json',detection_report(records,'roberta',cuts))
        return result
    finally:
        if lock.exists() and lock.read_bytes()==owner:lock.unlink()
        if 'model' in locals():del model
        torch.cuda.empty_cache()


def comparison(card,out,raw,tick):
    from . import detectors,located,calibration
    original=raw.parent;reports={}
    for part,name in [('core','core-v1-A-reserve-summary-g2r1'),('extension','reserve-extension-v1-summary-g2r1')]:
        tick();source=read(original/'manifests'/f'{name}.json')['args']
        rows=detectors.merge_predictions(read(original/source['rows']),[original/'jobs'/n/'PREDICTIONS.json' for n in source['blocks']])
        rows=located.features(rows,read(original/'jobs'/source['located']/'MODEL.json'))
        selection=read(original/'jobs'/source['selection']/'SELECTION.json')
        for name,model in selection['models'].items():
            for r,v in zip(rows,detectors.apply_linear(model,rows)):r[name]=v
        for r in rows:
            r['released-e5']=r['e5_probability']
            for name in selection['cuts']:r[name]=calibration.temper([1-r[name],r[name]],selection['calibration'][name]['temperature'])[1]
        if part=='core':
            base=original/'jobs/core-v1-roberta-evaluate-g2r1'
            roberta={r['key']:read(base/'rows'/f"{r['key']}.json") for r in rows}
            rcuts=read(base/'CALIBRATION.json')
        else:
            result=read(raw/'jobs'/card['args']['strong']/'PREDICTIONS.json')
            roberta={r['key']:r for r in result['rows']};rcuts=result['cuts']
            if len(roberta)!=len(result['rows']):raise ValueError('duplicate strong-detector rows')
        if set(roberta)!={r['key'] for r in rows}:raise ValueError('strong comparison coverage differs')
        for r in rows:
            p=roberta[r['key']]
            if p['unit']!=r['unit'] or p['label']!=r['label']:raise ValueError('paired truth differs')
            r['roberta']=p['roberta']
        cuts=dict(selection['cuts'],roberta=rcuts)
        aggregate={n:detection_report(rows,n,c) for n,c in cuts.items()}
        differences={}
        for target in ('0.01','0.05'):
            for rival in ('matched-window-direct','roberta'):
                differences[target+'/'+rival]=paired(rows,'reconstruction-feature-fusion',rival,
                    cuts['reconstruction-feature-fusion'][target],cuts[rival][target])
        reports[part]=dict(aggregate=aggregate,paired=differences,rows=len(rows),units=len({r['unit'] for r in rows}))
    result=dict(status='complete',partitions=reports,scope='post-exposure paired diagnostics; all frozen rivals; no formal promotion or human historical claim')
    freeze(out/'ANALYSIS.json',result);return result
