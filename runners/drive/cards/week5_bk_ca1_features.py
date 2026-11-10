"""Bounded exact CA1.s1 encoding; original model, batches and source stay fixed.

DESIGN CHECK: LESSONS 3-5. All original prompts and whole sampled annotators
remain. Every retained vector is independently re-encoded. No pilot can create
a full feature summary and no unverified old pilot vector is reused.
"""
from pathlib import Path
import gzip, hashlib, json, time
import numpy as np
from sklearn.cluster import KMeans
from threadpoolctl import threadpool_limits
from . import week3_alignment_features as old
from . import week4_alignment_sample_features as sample
from . import week5_go as core

CHUNK = 512


def wanted(output):
    return (output/'YIELD_REQUEST.json').exists() or (output.parent/'YIELD_REQUEST.json').exists()


def scope(inputs, config):
    fixture = config.get('fixture', False)
    report, root, rows, splits = (old.source(inputs) if fixture else sample.source(inputs))
    if not fixture and (report.get('sample_annotators') != 1036 or report.get('mandatory_annotators') != 836
                        or report.get('random_annotators') != 200):
        raise ValueError('frozen CA1.s1 population required')
    selected, ids, prompts = sample.select_ids(rows, splits, 'full', old.SEED)
    if len(prompts) < 50 and not fixture:
        raise ValueError('full original prompt reference is incomplete')
    return report, root, rows, splits, selected, ids, prompts


def run(output, inputs, config):
    output = Path(output); output.mkdir(parents=True, exist_ok=True)
    allowed = {'fixture','actual_encoder','max_new_chunks','max_wall_seconds','allow_clustering'}
    if set(config)-allowed: raise ValueError('unknown CA1 configuration')
    report, root, rows, splits, selected, ids, prompts = scope(inputs, config)
    binding = {'inputs': {k:core.sha(v) for k,v in inputs.items()}, 'fixture':bool(config.get('fixture')),
               'actual_encoder':bool(config.get('actual_encoder')),
               'modules':{Path(m.__file__).name:core.sha(m.__file__) for m in (old,sample)},
               'module_sha256':core.sha(__file__), 'chunk_size':CHUNK, 'seed':old.SEED}
    bp=output/'BINDINGS.json'
    if bp.exists() and json.loads(bp.read_text('utf8')) != binding: raise ValueError('CA1 binding changed')
    core.write(bp,binding)
    needed=set(ids); texts={}
    with gzip.open(root/'TEXTS.jsonl.gz','rt',encoding='utf8') as stream:
        for line in stream:
            row=json.loads(line)
            if row['index'] in needed:
                if row['index'] in texts or hashlib.sha256(row['text'].encode()).hexdigest()!=row['sha256']:
                    raise ValueError('duplicate or altered CA1 text')
                texts[row['index']]=row['text']
    if set(texts)!=needed:raise ValueError('missing complete CA1 text')
    start=time.monotonic(); cpu=time.process_time(); new=0; parts=[]; encode=None
    for begin in range(0,len(ids),CHUNK):
        local=ids[begin:begin+CHUNK]; path=output/'chunks'/f'{begin//CHUNK:05}.npy'; seal=path.with_suffix('.json')
        if seal.exists():
            receipt=json.loads(seal.read_text('utf8'))
            if receipt['binding']!=binding or receipt['indices']!=local or receipt['sha256']!=core.sha(path):
                raise ValueError('CA1 checkpoint changed')
            values=np.load(path,allow_pickle=False)
        else:
            if new>=config.get('max_new_chunks',10**9) or wanted(output) or time.monotonic()-start>=config.get('max_wall_seconds',900):
                value={'status':'yielded','phase':'encoding','texts_completed':begin,'texts_total':len(ids),
                       'new_chunks':new,'new_cpu_seconds':time.process_time()-cpu,'full_chunks':int(np.ceil(len(ids)/CHUNK))}
                core.write(output/'PROGRESS.json',value);return value
            if encode is None:encode=old.encoder(inputs, {'mode':'fixture' if config.get('fixture') and not config.get('actual_encoder') else 'full'})
            before=time.process_time()
            with threadpool_limits(limits=2):values=encode([texts[i] for i in local])
            if values.shape!=(len(local),384) or values.dtype!=np.float32 or not np.isfinite(values).all():
                raise ValueError('CA1 vector shape or values invalid')
            path.parent.mkdir(parents=True,exist_ok=True)
            if path.exists():
                if not np.array_equal(values,np.load(path,allow_pickle=False)):raise ValueError('unsealed CA1 vector differs')
            else:
                with path.open('xb') as f:np.save(f,values,allow_pickle=False)
            core.write(seal,{'binding':binding,'indices':local,'sha256':core.sha(path),'cpu_seconds':time.process_time()-before})
            new+=1
        if not np.allclose(np.linalg.norm(values,axis=1),1,rtol=0,atol=1e-6):raise ValueError('CA1 vector normalization differs')
        parts.append(path)
        core.write(output/'PROGRESS.json',{'phase':'encoding','texts_completed':begin+len(local),'texts_total':len(ids),
                                         'new_chunks':new,'new_cpu_seconds':time.process_time()-cpu})
    if not config.get('allow_clustering',True) or wanted(output) or time.monotonic()-start>=config.get('max_wall_seconds',900):
        return {'status':'yielded','phase':'clustering_pending','texts_completed':len(ids),'texts_total':len(ids)}
    matrix=np.concatenate([np.load(p,allow_pickle=False) for p in parts]);vp=output/'EMBEDDINGS.npy'
    if vp.exists():
        if not np.array_equal(matrix,np.load(vp,allow_pickle=False)):raise ValueError('complete CA1 vector array changed')
    else:
        with vp.open('xb') as f:np.save(f,matrix,allow_pickle=False)
    lookup={i:j for j,i in enumerate(ids)};count=min(50,len(prompts));before=time.process_time()
    with threadpool_limits(limits=2):
        labels=KMeans(n_clusters=count,random_state=old.SEED,n_init=10,algorithm='lloyd').fit_predict(
            matrix[[lookup[splits['prompt_text_indices'][p]] for p in prompts]])
    index={'text_indices':ids,'comparison_indices':selected,'prompt_clusters':{p:int(v) for p,v in zip(prompts,labels)}}
    ip=output/'INDEX.json'
    if ip.exists() and json.loads(ip.read_text('utf8'))!=index:raise ValueError('CA1 full prompt clusters changed')
    core.write(ip,index)
    value={'card':'CA1-features','variant':'CA1.s1','mode':'full','execution_only':bool(config.get('fixture')),
           'constructed_only':bool(config.get('fixture')),
           'input_hashes':binding['inputs'],'encoder':old.ENCODER,'texts':len(ids),'comparisons':len(rows),
           'dimensions':384,'normalized':True,'maximum_tokens':128,'prompt_clusters':count,
           'all_original_prompts':len(prompts),'permutation_route':report['permutation_route'],
           'output_hashes':{'EMBEDDINGS.npy':core.sha(vp),'INDEX.json':core.sha(ip)},
           'scope':'Representation preparation only; no preference result or value interpretation.'}
    sp=output/'SUMMARY.json'
    if sp.exists() and json.loads(sp.read_text('utf8'))!=value:raise ValueError('CA1 summary changed')
    core.write(sp,value);core.write(output/'CLUSTER_COST.json',{'cpu_seconds':time.process_time()-before})
    return value


def execute(output,inputs,config):return run(output,inputs,config)


def verify(output,inputs,config):
    output=Path(output); result=run(output/'independent-replay',inputs,config)
    if result.get('status')=='yielded':return {**result,'verified':False}
    if result!=json.loads((output/'SUMMARY.json').read_text('utf8')):raise ValueError('complete CA1 independent replay differs')
    return {'verified':True,'every_vector_and_prompt_cluster_independently_recomputed':True}
