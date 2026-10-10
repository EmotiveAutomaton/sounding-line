"""R02/SL6: local HF sequence and legal-token readout with coherence controls.

DESIGN CHECK: LESSONS 3-5. NULL: vocabulary preferences, spelling or order drive
scores rather than explicit facts; negation and partitions disagree. ALTERNATIVE:
native candidate support survives and complementary facts remain coherent.
These are named diagnostic readouts, not an Ollama sequence-likelihood claim.
"""
import time,numpy as np
from .common import freeze,digest
from .adaptive import device,guard,proper
from runners.stage13.detectors import cached_model,model_pins
from scipy.special import softmax

def score_choices(model,tok,prompt,labels,torch):
    prefix=tok.encode(prompt,add_special_tokens=False);options=[tok.encode(' '+l,add_special_tokens=False) for l in labels]
    if not prefix or any(not ids for ids in options):raise ValueError('empty native support')
    if max(len(prefix)+len(o) for o in options)>512:raise ValueError('native context bound exceeded')
    total=[];mean=[];first=[]
    with torch.inference_mode():
        startlogits=model(input_ids=torch.tensor([prefix],device='cuda')).logits[0,-1].float()
        first=[float(startlogits[ids[0]]) for ids in options]
        for option in options:
            ids=torch.tensor([prefix+option],device='cuda');logits=model(input_ids=ids).logits[0,len(prefix)-1:-1].float()
            ll=torch.log_softmax(logits,-1).gather(1,ids[0,len(prefix):,None]).sum();total.append(float(ll));mean.append(float(ll)/len(option))
    if not all(np.isfinite(total)):raise ValueError('nonfinite likelihood')
    first_valid=len({ids[0] for ids in options})==len(options)
    return dict(sequence=softmax(total).tolist(),length_normalized=softmax(mean).tolist(),first_legal_token=softmax(first).tolist() if first_valid else None,
        native_prefix=prefix,native_options=options,first_token_support_valid=first_valid)

def run(card,out,raw,tick):
    from transformers import AutoTokenizer,AutoModelForCausalLM
    path=cached_model(card['backbone']);identity=model_pins(path)
    if identity!=card['model_files']:raise ValueError('model identity changed')
    tok=AutoTokenizer.from_pretrained(path,local_files_only=True,trust_remote_code=False);rows=[];actions=['accept','edit','dismiss','ignore']
    with device(out,card['memory_MiB']) as torch:
        torch.manual_seed(141010);model=AutoModelForCausalLM.from_pretrained(path,local_files_only=True,trust_remote_code=False,torch_dtype=torch.bfloat16).to('cuda').eval();guard(model)
        for i in range(64):
            action=actions[i%4];base=f'Record {i}: the recorded handling was {action}. '
            query=actions[(i//4)%4]
            for negated in (False,True):
                statement=f'Was the handling {"not " if negated else ""}{query}? Answer:'
                y=int(not ((action!=query) if negated else (action==query)))
                for labels in (['yes','no'],['no','yes'],['true','false'],['false','true']):
                    expected=('yes' if y==0 else 'no') if 'yes' in labels else ('true' if y==0 else 'false')
                    label_truth=labels.index(expected)
                    start=time.monotonic();value=score_choices(model,tok,base+statement,labels,torch)
                    rows.append(dict(case=i,negated=negated,labels=labels,truth=label_truth,readout=value,seconds=time.monotonic()-start,
                        scores={k:proper(value[k] or [],label_truth) for k in ('sequence','length_normalized','first_legal_token')}))
            if i%8==0:guard(model)
            tick(dict(completed_cases=i+1,total_cases=64))
        # Exact unchanged-input repeat is contemporaneous; no extra label tuning.
        repeats=[score_choices(model,tok,'The recorded action was accept. Was it accept? Answer:',['yes','no'],torch) for _ in range(2)]
        del model
    summary={k:dict(mean_half_brier=float(np.mean([r['scores'][k]['half_brier'] for r in rows])),accuracy=float(np.mean([r['scores'][k]['correct'] for r in rows])),valid=sum(r['scores'][k]['valid'] for r in rows)) for k in ('sequence','length_normalized','first_legal_token')}
    coherence={}
    for k in summary:
        gaps=[]
        for i in range(64):
            for labels in (['yes','no'],['no','yes'],['true','false'],['false','true']):
                pair=[r['readout'][k] for r in rows if r['case']==i and r['labels']==labels]
                if all(p is not None for p in pair):gaps.append(abs(pair[0][0]+pair[1][0]-1))
        coherence[k]=dict(mean_negation_gap=float(np.mean(gaps)),maximum_negation_gap=float(max(gaps)))
    partitions={}
    for k in summary:
        masses=[]
        for a in range(4):
            block=[r for r in rows if r['case']<16 and r['case']%4==a and not r['negated'] and r['labels']==['yes','no']]
            if all(r['readout'][k] is not None for r in block):masses.append(sum(r['readout'][k][0] for r in block))
        partitions[k]=dict(action_partition_masses=masses,maximum_partition_gap=max(abs(m-1) for m in masses) if masses else None)
    freeze(out/'MODEL.json',dict(backbone=card['backbone'],files=identity,precision='bfloat16',context_bound=512))
    freeze(out/'PREDICTIONS.json',rows);freeze(out/'SUMMARY.json',dict(readouts=summary,coherence=coherence,partitions=partitions,repeat_equal=repeats[0]==repeats[1],scope='constructed explicit-action diagnostic; no human task or complete graph admission'))
    freeze(out/'ADMISSION.json',dict(admitted=summary['sequence']['accuracy']>=.95 and coherence['sequence']['mean_negation_gap']<=.1 and partitions['sequence']['maximum_partition_gap'] is not None and partitions['sequence']['maximum_partition_gap']<=.1 and repeats[0]==repeats[1],scope='explicit-action sequence readout only; natural calibration still required'))
