"""Bounded local detector implementations and frozen statistical calibration.

DESIGN CHECK: LESSONS 3-5. NULL: identical text yields identical features and a
label shuffle cannot validate provenance. ALTERNATIVE: pinned model forward and
saved-output replay agree. CPU always stays single-threaded; full tuning is GPU
held. Log-rank is a named variant, never a claimed Fast-DetectGPT reproduction.
"""
from __future__ import annotations
import math
import re
import time
from pathlib import Path
import numpy as np
from .common import RAW,freeze,read,filehash,atomic,now,limit_process,SEED
from .scoring import threshold,detection_report,span_scores

SURFACE_NAMES=['characters','words','mean_word_length','type_token_ratio','punctuation','uppercase','newlines','digits','sentence_length','function_words']
FEATURE_NAMES=SURFACE_NAMES+['e5_logit','lm_nll','lm_logrank']


def surface(text):
    words=re.findall(r'\w+',text.lower());n=max(1,len(words));size=max(1,len(text))
    return [math.log1p(len(text)),math.log1p(len(words)),sum(map(len,words))/n,len(set(words))/n,
        sum(not c.isalnum() and not c.isspace() for c in text)/size,sum(c.isupper() for c in text)/size,
        text.count('\n')/size,sum(c.isdigit() for c in text)/size,len(words)/max(1,len(re.findall(r'[.!?]',text))),
        sum(w in {'the','a','an','and','of','in','to','is','for','that','it','with','as'} for w in words)/n]


def cached_model(name):
    from huggingface_hub import snapshot_download
    path=Path(snapshot_download(name,local_files_only=True))
    return path


def model_pins(path):
    return {p.name:filehash(p) for p in sorted(Path(path).iterdir()) if p.is_file() and p.suffix in ('.json','.txt','.safetensors','.bin')}


class Detector:
    def __init__(self,arm,raw=RAW,device='cpu'):
        limit_process()
        import torch
        from transformers import AutoTokenizer,AutoModelForSequenceClassification,AutoModelForCausalLM
        torch.set_num_threads(1);self.torch=torch;self.arm=arm;self.device=device
        if device!='cpu':raise ValueError('baseline inference is CPU only')
        if arm=='e5':self.path=raw/'assets/e5'
        elif arm=='gpt2-medium-logrank':self.path=cached_model('openai-community/gpt2-medium')
        else:raise ValueError('unknown detector arm')
        self.tokenizer=AutoTokenizer.from_pretrained(self.path,local_files_only=True,trust_remote_code=False)
        cls=AutoModelForSequenceClassification if arm=='e5' else AutoModelForCausalLM
        self.model=cls.from_pretrained(self.path,local_files_only=True,trust_remote_code=False).to('cpu').eval()
        self.identity=dict(arm=arm,path=str(self.path),revision=self.path.name if arm!='e5' else '483fc4969592dc20e00e5130e7187b5dd25dbcc7',files=model_pins(self.path),device='cpu',dtype='float32',max_tokens=512,threads=1)
        if arm=='e5' and self.model.config.num_labels!=2:raise ValueError('e5 head is not binary')

    def score(self,text):
        torch=self.torch
        full=self.tokenizer(text,add_special_tokens=True)['input_ids']
        inputs=self.tokenizer(text,return_tensors='pt',truncation=True,max_length=512,return_offsets_mapping=True)
        offsets=inputs.pop('offset_mapping')[0].tolist()
        with torch.inference_mode():logits=self.model(**inputs).logits.float()
        if not torch.isfinite(logits).all():raise ValueError('nonfinite model logits')
        visibility=dict(full_tokens=len(full),used_tokens=int(inputs['input_ids'].shape[1]),visible_char_end=max(b for a,b in offsets),truncated=len(full)>512)
        if self.arm=='e5':
            p=torch.softmax(logits,dim=-1)[0,1].item()
            return dict(e5_probability=p,e5_logit=float(logits[0,1]-logits[0,0]),**visibility)
        target=inputs['input_ids'][0,1:];l=logits[0,:-1]
        if not len(target):raise ValueError('no causal scoring tokens')
        selected=l.gather(1,target[:,None]).squeeze(1)
        nll=(torch.logsumexp(l,dim=-1)-selected).mean().item()
        ranks=(l>selected[:,None]).sum(dim=-1).float()+1
        return dict(lm_nll=nll,lm_logrank=torch.log(ranks).mean().item(),**visibility)


def admission(arm,out,raw=RAW):
    start=time.perf_counter();model=Detector(arm,raw)
    texts=['A small lamp stood on the table. Its light reached the open book.','A small lamp stood on the table. Its light reached the open book.','xqz vvvv 9384 zxzx 7?!']
    values=[model.score(t) for t in texts]
    if values[0]!=values[1]:raise ValueError('deterministic repeat differs')
    if arm=='gpt2-medium-logrank' and values[0]['lm_nll']>=values[2]['lm_nll']:raise ValueError('language versus corruption direction control failed')
    result=dict(status='complete',admitted=True,identity=model.identity,controls=values,elapsed_seconds=time.perf_counter()-start,
        evidence='actual CPU model forward, repeated text equality, finite native-token readout; no provenance performance claim')
    freeze(out/'ADMISSION.json',result);return result


def batch(arm,rows,out,raw=RAW,tick=None,expected_identity=None):
    model=Detector(arm,raw)
    if expected_identity is not None and model.identity!=expected_identity:raise ValueError('model/tokenizer changed since admission')
    start=time.perf_counter();values=[]
    for i,r in enumerate(rows):
        if tick:tick()
        t=time.perf_counter();v=model.score(r['text'])
        values.append(dict(key=r['key'],unit=r['unit'],features=v,surface=surface(r['text']),elapsed_seconds=time.perf_counter()-t))
        atomic(out/'PROGRESS.json',dict(at=now(),done=i+1,total=len(rows),elapsed_seconds=time.perf_counter()-start))
        # Every expensive reply persists before another attempt.
        freeze(out/'rows'/(r['key']+'.json'),values[-1])
    result=dict(rows=values,identity=model.identity,total_seconds=time.perf_counter()-start)
    freeze(out/'PREDICTIONS.json',result);return result


def merge_predictions(rows,paths):
    by={r['key']:dict(r) for r in rows};coverage={k:set() for k in by}
    for p in paths:
        result=read(p)
        for r in result['rows']:
            if r['key'] not in by:continue
            arm=result['identity']['arm']
            if arm in coverage[r['key']]:raise ValueError('duplicate prediction')
            coverage[r['key']].add(arm);by[r['key']].update(r['features']);by[r['key']]['surface']=r['surface']
    if any(v!={'e5','gpt2-medium-logrank'} for v in coverage.values()):raise ValueError('incomplete detector family; no survivor-only fit')
    return [by[r['key']] for r in rows]


def matrix(rows,names):
    return np.array([[dict(r,**dict(zip(SURFACE_NAMES,r['surface'])))[k] for k in names] for r in rows],dtype=float)


def fit_linear(rows,names):
    from sklearn.linear_model import LogisticRegression
    x=matrix(rows,names);y=np.array([r['label'] for r in rows]);mean=x.mean(0);scale=x.std(0);scale[scale<1e-8]=1
    from collections import Counter
    counts=Counter(r['unit'] for r in rows)
    weights=[1/counts[r['unit']] for r in rows]
    fit=LogisticRegression(C=1.,max_iter=1000,random_state=SEED,class_weight='balanced').fit((x-mean)/scale,y,sample_weight=weights)
    return dict(names=names,mean=mean.tolist(),scale=scale.tolist(),coef=fit.coef_[0].tolist(),intercept=float(fit.intercept_[0]),training_units=len(counts))


def apply_linear(model,rows):
    z=(matrix(rows,model['names'])-np.array(model['mean']))/np.array(model['scale'])
    logits=z@np.array(model['coef'])+model['intercept']
    return (1/(1+np.exp(-np.clip(logits,-60,60)))).tolist()


def fit_and_select(train,dev,cal,out):
    # All rivals retained; at most two promoted operational finalists.
    models={name:fit_linear(train,names) for name,names in [('surface-rival',SURFACE_NAMES),('statistical',['lm_nll','lm_logrank']),('direct-feature-fusion',FEATURE_NAMES),('reconstruction-feature-fusion',FEATURE_NAMES+['located_mean','located_max','located_entropy','located_transitions','located_fraction']),('matched-window-direct',FEATURE_NAMES+['direct_mean','direct_max','direct_entropy','direct_transitions','direct_fraction'])]}
    scored={part:[dict(r) for r in rows] for part,rows in [('development',dev),('calibration',cal)]}
    for rs in scored.values():
        for name,m in models.items():
            for r,s in zip(rs,apply_linear(m,rs)):r[name]=s
        for r in rs:r['released-e5']=r['e5_probability']
    from .calibration import fit as calibrate,temper
    names=list(models)+['released-e5'];cuts={};reports={};calibration={}
    for name in names:
        calibration[name]=calibrate([dict(probabilities=[1-r[name],r[name]],truth=r['label'],unit=r['unit']) for r in scored['calibration']])
        for rs in scored.values():
            for r in rs:r[name]=temper([1-r[name],r[name]],calibration[name]['temperature'])[1]
    for name in names:
        human=[r[name] for r in scored['calibration'] if not r['label']]
        cuts[name]={str(q):threshold(human,q) for q in (.01,.05)}
        reports[name]=detection_report(scored['development'],name,cuts[name])
    order=sorted(names,key=lambda n:(-(reports[n]['thresholds']['0.01']['tpr'] or 0),n))
    result=dict(status='complete',models=models,calibration=calibration,cuts=cuts,development=reports,finalists=order[:2],
        selection_rule='development TPR at independently calibrated 1% FPR threshold; fixed name tie break; all rivals still reported',
        promotion_margin=.03,contribution_promotion_margin=.03,reserve_opened=False,
        missing=['full-tuned RoBERTa until separate Gear 2 completion','source annotation operations are not mental-goal truth'],
        direct_features='surface plus calibrated score fusion, not decision reconstruction')
    freeze(out/'SELECTION.json',result);return result


def evaluate(selection,rows):
    rs=[dict(r) for r in rows]
    for name,m in selection['models'].items():
        for r,s in zip(rs,apply_linear(m,rs)):r[name]=s
    for r in rs:r['released-e5']=r['e5_probability']
    from .calibration import temper
    names=list(selection['cuts'])
    for r in rs:
        for name in names:r[name]=temper([1-r[name],r[name]],selection['calibration'][name]['temperature'])[1]
    slices={'all':rs}
    for field in ('domain','generator','version','operation'):
        for value in sorted({r[field] for r in rs},key=str):
            part=[r for r in rs if r[field]==value or (field in ('generator','version','operation') and not r['label'])]
            slices[field+':'+str(value)]=part
    slices['short']=[r for r in rs if len(r['text'].split())<150]
    return dict(status='complete',comparisons={slice_name:{n:detection_report(part,n,selection['cuts'][n]) for n in names} for slice_name,part in slices.items() if part},
        scope='binary any-AI participation on released English source families; truncated-native-token evidence; upstream exposure unresolved',
        missing=selection['missing'],selected_finalists=selection['finalists'])
