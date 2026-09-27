"""Same-model likelihood and literal elicitation admission and paired comparison.

DESIGN CHECK: LESSONS 3-5. NULL: malformed, capped and non-unit probability arrays
are invalid and charged; a failed real reader admission holds its successors.
ALTERNATIVE: same tokenizer/model and evidence permit a scoped readout contrast.
CPU SmolLM is a named variant; it cannot replace the primary held Qwen comparison.
"""
import json,time
import numpy as np
from .common import freeze,limit_process,read
from .detectors import cached_model,model_pins
from .context import conditional,evidence
from .scoring import probabilities,proper_loss,interval
from .reconstruction import ACTIONS

class Reader:
    def __init__(self):
        limit_process();import torch
        from transformers import AutoTokenizer,AutoModelForCausalLM
        self.torch=torch;torch.set_num_threads(1)
        path=cached_model('HuggingFaceTB/SmolLM2-360M-Instruct');self.tokenizer=AutoTokenizer.from_pretrained(path,local_files_only=True)
        self.model=AutoModelForCausalLM.from_pretrained(path,local_files_only=True).float().eval()
        self.identity=dict(model='SmolLM2-360M-Instruct',files=model_pins(path),revision=path.name,device='cpu',threads=1)

    def elicited(self,prompt,n):
        text=self.tokenizer.apply_chat_template([dict(role='user',content=prompt+f'\nReturn only a JSON array of {n} probabilities in the stated order, summing to one.')],tokenize=False,add_generation_prompt=True)
        encoded=self.tokenizer(text,return_tensors='pt')
        if encoded['input_ids'].shape[1]>512:raise ValueError('elicited native-token input cap')
        start=time.perf_counter()
        with self.torch.inference_mode():out=self.model.generate(**encoded,max_new_tokens=96,do_sample=False,pad_token_id=self.tokenizer.eos_token_id)
        tail=out[0,encoded['input_ids'].shape[1]:];raw=self.tokenizer.decode(tail,skip_special_tokens=True)
        try:value=json.loads(raw);p=probabilities(value,n) if len(tail)<96 else None
        except (ValueError,TypeError):p=None
        return p,dict(raw=raw,generated_tokens=len(tail),input_tokens=int(encoded['input_ids'].shape[1]),elapsed_seconds=time.perf_counter()-start,capped=len(tail)>=96)


def admission(out):
    model=Reader();controls=[]
    for text,label in [('The recorded action was accept.',0),('The recorded action was ignore.',3)]:
        prompt=text+'\nActions in order: accept, edit, dismiss, ignore.\nAction:'
        p,trace=conditional(model,prompt,list(ACTIONS));q,raw=model.elicited(prompt,4)
        controls.append(dict(likelihood=p,elicited=q,raw=raw,truth=label,likelihood_trace=trace))
    result=dict(admitted=all(c['elicited'] is not None and int(np.argmax(c['elicited']))==c['truth'] and int(np.argmax(c['likelihood']))==c['truth'] for c in controls),controls=controls,identity=model.identity,
        scope='real CPU readout admission on explicit observed facts; no human-inference validity claim')
    freeze(out/'ADMISSION.json',result);return result


def run(rows,out,tick):
    model=Reader();records=[]
    for r in rows:
        for view in ('A','C'):
            tick();e=evidence(r,view);bounded=model.tokenizer.decode(model.tokenizer.encode(json.dumps(e,ensure_ascii=False))[:260]);prompt='Completed writing episode: '+bounded+'\nActions in order: accept, edit, dismiss, ignore.\nAction:'
            start=time.perf_counter();p,t=conditional(model,prompt,list(ACTIONS));t['elapsed_seconds']=time.perf_counter()-start
            q,u=model.elicited(prompt,4)
            for method,v,trace in [('likelihood',p,t),('elicited',q,u)]:
                record=dict(key=r['key'],unit=r['unit'],partition=r['partition'],view=view,method=method,probabilities=v,truth=ACTIONS.index(r['target']['handling']),n=4,trace=trace,scores=proper_loss(v,ACTIONS.index(r['target']['handling']),4))
                freeze(out/'rows'/f"{r['key']}-{view}-{method}.json",record);records.append(record)
    result=dict(rows=records,identity=model.identity,scope='same-model readout contrast, common bounded evidence; different decoding work is measured, not claimed cost-equivalent')
    freeze(out/'PREDICTIONS.json',result);return result


def summarize(records):
    from .calibration import fit,evaluate
    results={}
    for view in ('A','C'):
        for method in ('likelihood','elicited'):
            cal=[r for r in records if r['partition']=='calibration' and r['view']==view and r['method']==method]
            test=[r for r in records if r['partition']=='reserve' and r['view']==view and r['method']==method]
            model=fit(cal);results[view+'/'+method]=dict(calibration=model,evaluation=evaluate(test,model),elapsed_seconds=sum(r['trace']['elapsed_seconds'] for r in test))
    return dict(status='complete',comparisons=results,scope='all attempts; historically exposed sources; component-limited uncertainty')
