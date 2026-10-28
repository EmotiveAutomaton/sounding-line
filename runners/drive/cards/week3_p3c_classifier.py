"""Local CPU edit-intent validation and complete frozen calibration.

DESIGN CHECK: LESSONS 2-5 read for P3c 2026-10-27, statistic/model clauses
reread before this execution adapter. NULL agreement is near zero; useful
agreement must reach the unchanged binary kappa >= .6. Constant reference,
missing predictions and overlength selected inputs never pass. No clipping,
sample replacement, tuning, GPU, remote model code or paid fallback is used.
"""
from collections import Counter
import gzip
import importlib.metadata
import json
from pathlib import Path
import time
import numpy as np
from runners.stage14.common import read, filehash, freeze, atomic
from .week3_p3c_inputs import terminal, authenticated, digest
from .week3_p3c_model import inventory, REVISION

LABELS = ['clarity', 'fluency', 'coherence', 'style', 'meaning-changed']
CONFIGS = {mode:dict(version=1,mode=mode,threads=1,precision='float32',batch_size=1,
    max_tokens=512,seed=20261026) for mode in ('validation','calibration')}
CHECK_PAIRS = [dict(key=str(i),before=a,after=b) for i,(a,b) in enumerate([
    ('I likes coffee.','I like coffee.'), ('The result was 64%.','The result was 83%.'),
    ('café — naïve 🙂','café — naïve'), ('A word.','')])]


def kappa(labels, predictions):
    if len(labels)!=len(predictions) or len(labels)!=200:
        raise ValueError('all two hundred paired labels required')
    if any(x not in LABELS for x in labels+predictions): raise ValueError('unknown intent label')
    table=[[0]*5 for _ in range(5)]; binary=[[0,0],[0,0]]
    for a,b in zip(labels,predictions):
        table[LABELS.index(a)][LABELS.index(b)]+=1
        binary[int(a=='meaning-changed')][int(b=='meaning-changed')]+=1
    n=len(labels); observed=(binary[0][0]+binary[1][1])/n
    expected=sum(sum(binary[i])*sum(r[i] for r in binary) for i in range(2))/(n*n)
    reference_varies=all(sum(row)>0 for row in binary)
    value=(observed-expected)/(1-expected) if reference_varies and expected<1 else None
    return dict(binary_table=binary,five_class_table=table,label_order=LABELS,
        binary_order=['not-meaning-changed','meaning-changed'],agreement=observed,
        expected_agreement=expected,kappa=value,gate_passed=value is not None and value>=.6,
        reference_varies=reference_varies)


class LocalModel:
    def __init__(self,path):
        import torch
        from transformers import AutoTokenizer, AutoModelForSequenceClassification
        torch.set_num_threads(1); torch.set_num_interop_threads(1); torch.manual_seed(20261026)
        torch.use_deterministic_algorithms(True)
        self.torch=torch
        self.tokenizer=AutoTokenizer.from_pretrained(str(path),local_files_only=True,trust_remote_code=False)
        self.model=AutoModelForSequenceClassification.from_pretrained(str(path),local_files_only=True,
            trust_remote_code=False,use_safetensors=False,weights_only=True,torch_dtype=torch.float32,
            attn_implementation='eager').to('cpu').eval()
        if [self.model.config.id2label[i] for i in range(5)]!=LABELS:
            raise ValueError('checkpoint label mapping differs')
        if self.model.config.max_position_embeddings!=514 or self.model.config.pad_token_id!=1:
            raise ValueError('checkpoint positional support differs')
        if any(p.device.type!='cpu' or p.dtype!=torch.float32 for p in self.model.parameters()):
            raise ValueError('CPU float32 parameters required')
        if any(m.training for m in self.model.modules()): raise ValueError('all modules must be in evaluation mode')
        self.environment={n:importlib.metadata.version(n) for n in ('torch','transformers','tokenizers','numpy','scikit-learn')}

    def encode(self,row):
        return self.tokenizer(row['before'],row['after'],truncation=False,padding=False)

    def token_count(self,row): return len(self.encode(row)['input_ids'])

    def predict(self,row):
        encoded=self.encode(row); length=len(encoded['input_ids'])
        if length>512: raise ValueError('unclipped input exceeds model support')
        inputs={k:self.torch.tensor([v],dtype=self.torch.long) for k,v in encoded.items()}
        with self.torch.inference_mode(): logits=self.model(**inputs).logits[0].cpu().numpy().astype(float)
        if logits.shape!=(5,) or not np.isfinite(logits).all(): raise ValueError('finite complete classifier output required')
        values=np.exp(logits-logits.max()); probabilities=values/values.sum(); index=int(np.argmax(logits))
        return dict(key=row['key'],tokens=length,logits=logits.tolist(),probabilities=probabilities.tolist(),label=LABELS[index])


def parity(a,b):
    if set(a)!=set(b) or any(a[k]!=b[k] for k in ('key','tokens','label')):
        raise ValueError('classifier identity or categorical replay differs')
    for k in ('logits','probabilities'):
        if not np.allclose(a[k],b[k],rtol=1e-5,atol=1e-6,equal_nan=False):
            raise ValueError('classifier numerical replay differs')


def save(path,value,verification):
    if verification or path.exists():
        if read(path)!=value: raise ValueError('immutable instrument output differs: '+path.name)
    else: freeze(path,value)


def model_inputs(inputs):
    source=terminal(inputs['model_completion']); gate=read(inputs['model_gate'])
    if not gate['full_write_through'] or gate['completion_sha256']!=filehash(inputs['model_completion']):
        raise ValueError('landed model intake required')
    summary=read(authenticated(source,'output/SUMMARY.json'))
    path=source[0]/'output/model'
    if summary['revision']!=REVISION or inventory(path,read(inputs['metadata']))!=summary['files']:
        raise ValueError('pinned model byte inventory differs')
    return path


def corpus(inputs,model):
    source=terminal(inputs['source_completion']); gate=read(inputs['source_gate'])
    if not gate['full_write_through'] or gate['completion_sha256']!=filehash(inputs['source_completion']):
        raise ValueError('landed complete pair source required')
    def get(name): return read(authenticated(source,'output/'+name))
    summary=get('SUMMARY.json'); mapping=get('CALIBRATION_MAP.json'); blind_path=authenticated(source,'output/BLIND_CALIBRATION.json')
    annotations=read(inputs['agent_labels']); blind=read(blind_path); timing=get('TIMING_ORDER.json')
    if summary['constructed'] or len(blind)!=200 or len(timing)!=1000 or len(set(timing))!=1000:
        raise ValueError('complete declared calibration and timing populations required')
    if annotations['predictions_seen'] or not annotations['agent_made'] or annotations['reviewed_pairs']!=200:
        raise ValueError('blind agent annotations required')
    if annotations['blind_sha256']!=filehash(blind_path) or annotations['criteria_sha256']!=filehash(inputs['criteria']):
        raise ValueError('annotation provenance differs')
    if [r['pair_id'] for r in annotations['rows']]!=[r['pair_id'] for r in blind] or [r['pair_id'] for r in mapping]!=[r['pair_id'] for r in blind]:
        raise ValueError('exact annotation identity and order required')
    if any(r['label'] not in LABELS or r['meaning_changed']!=(r['label']=='meaning-changed') for r in annotations['rows']):
        raise ValueError('invalid annotation category')
    calkeys=[r['key'] for r in mapping]
    if len(set(calkeys))!=200: raise ValueError('unique calibration events required')
    chosen=set(timing)|set(calkeys); selected={}; allkeys=[]; over=[]; maximum=0; token_hist=Counter()
    index=get('SESSION_INDEX.json')
    for entry in index:
        path=authenticated(source,'output/'+entry['file'])
        if filehash(path)!=entry['sha256']: raise ValueError('source unit seal differs')
        unit=json.loads(gzip.decompress(path.read_bytes()))
        if unit['session']!=entry['session'] or len(unit['rows'])!=entry['pairs']: raise ValueError('source unit identity differs')
        for r in unit['rows']:
            if digest([r['before'],r['after']])!=r['pair_content_sha256']: raise ValueError('pair content differs')
            allkeys.append(r['key']); length=model.token_count(r); maximum=max(maximum,length); token_hist[str(length)]+=1
            if length>512: over.append(dict(key=r['key'],tokens=length))
            if r['key'] in chosen: selected[r['key']]=r
    if len(allkeys)!=len(set(allkeys)) or len(allkeys)!=summary['counts']['pairs'] or set(selected)!=chosen:
        raise ValueError('complete unique pair census required')
    for b,m in zip(blind,mapping):
        r=selected[m['key']]
        if b['before']!=r['before'] or b['after']!=r['after'] or m['pair_content_sha256']!=r['pair_content_sha256']:
            raise ValueError('blind view differs from source')
    coverage=dict(pairs=len(allkeys),max_tokens=maximum,overlength=over,token_histogram=dict(sorted(token_hist.items(),key=lambda x:int(x[0]))),truncated=0,selected_overlength=[r for r in over if r['key'] in chosen])
    return selected,timing,calkeys,annotations,coverage


def run(output,inputs,config,verification=False):
    mode=config.get('mode')
    if mode not in CONFIGS or config!=CONFIGS[mode]: raise ValueError('frozen classifier configuration required')
    required={'model_completion','model_gate','metadata'}
    if mode=='calibration': required|={'source_completion','source_gate','agent_labels','criteria','native_completion','native_gate'}
    if set(inputs)!=required: raise ValueError('explicit classifier bindings required')
    output=Path(output);output.mkdir(parents=True,exist_ok=True)
    save(output/'BINDING.json',dict(config=config,inputs={k:filehash(v) for k,v in inputs.items()}),verification)
    if mode=='calibration':
        gate=read(inputs['native_gate'])
        if not gate['full_write_through'] or not gate['native_model_validated'] or gate['completion_sha256']!=filehash(inputs['native_completion']):
            raise ValueError('native model validation required')
    model=LocalModel(model_inputs(inputs)); save(output/'ENVIRONMENT.json',model.environment,verification)
    checks=[model.predict(r) for r in CHECK_PAIRS]
    for row,first in zip(CHECK_PAIRS,checks): parity(first,model.predict(row))
    if model.token_count(dict(before='word '*600,after='word '*600))<=512: raise ValueError('overlength fixture is not overlength')
    try: model.predict(dict(key='long',before='word '*600,after='word '*600))
    except ValueError as exc:
        if 'exceeds model support' not in str(exc): raise
    else: raise ValueError('overlength input was not refused')
    if verification or (output/'MODEL_CHECKS.json').exists():
        old=read(output/'MODEL_CHECKS.json')
        if len(old)!=len(checks): raise ValueError('incomplete numerical checks')
        for a,b in zip(old,checks): parity(a,b)
    else: freeze(output/'MODEL_CHECKS.json',checks)
    if mode=='validation':
        save(output/'SUMMARY.json',dict(native_model_validated=True,constructed_pairs=4,repeat_parity=True,overlength_refused=True,corpus_inference=False,scientific_admission=False),verification)
    else:
        selected,timing,calkeys,annotations,coverage=corpus(inputs,model)
        save(output/'TOKEN_COVERAGE.json',coverage,verification)
        if coverage['selected_overlength']:
            summary=dict(calibration_complete=False,gate_passed=False,reason='selected inputs exceed exact model support',scientific_admission=False)
        else:
            predictions={}; elapsed={}
            for group,keys in [('timing',timing),('calibration',calkeys)]:
                start=time.process_time()
                for i,key in enumerate(keys):
                    value=model.predict(selected[key]); path=output/group/(key+'.json');path.parent.mkdir(exist_ok=True)
                    if verification or path.exists(): parity(read(path),value)
                    else: freeze(path,value)
                    predictions[(group,key)]=value
                    if (i+1)%25==0: atomic(output/'PROGRESS.json',dict(phase=('verify-' if verification else '')+group,done=i+1,total=len(keys)))
                    if (output.parent/'STOP').exists() or (output/'YIELD_REQUEST.json').exists(): raise InterruptedError('classifier yields at pair boundary')
                elapsed[group]=time.process_time()-start
            if not verification and not (output/'TIMING.json').exists(): freeze(output/'TIMING.json',dict(cpu_seconds=elapsed,first_pairs=1000,calibration_pairs=200,batch_size=1,full_replay_required=True))
            # Compare duplicate event predictions across the two independent passes.
            for key in set(timing)&set(calkeys): parity(predictions['timing',key],predictions['calibration',key])
            agreement=kappa([r['label'] for r in annotations['rows']],[predictions['calibration',k]['label'] for k in calkeys])
            summary=dict(calibration_complete=True,agent_made_reference=True,agreement=agreement,
                gate_passed=agreement['gate_passed'],model_revision=REVISION,full_population_pairs=coverage['pairs'],
                overlength_population_pairs=len(coverage['overlength']),truncated=0,calibration_pairs=200,timing_pairs=1000,
                full_population_labels_complete=False,scientific_admission=False)
        save(output/'SUMMARY.json',summary,verification)
    if verification: return dict(verified=True,complete_input_replay=True,full_classifier_replay=True)
    return dict(status='complete',scientific_admission=False)


def execute(output,inputs,config): return run(output,inputs,config)
def verify(output,inputs,config): return run(output,inputs,config,True)
