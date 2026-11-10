"""Manifest-bound CPU GO readers and author-floor-aware GO1 collection.

DESIGN CHECK: LESSONS 2–5, CONTROLS 6–7. Exact identities reproduce identical
encoder vectors; true-goal removal is checked separately. No fixed selected LM
exists until the complete AT2 selection is admissible. Scores use shared rosters
and full-context support. Fewer than twenty author clusters is descriptive.
"""
from pathlib import Path
import json
import numpy as np
from . import week5_go as core


def embeddings(texts,manifest_path,cache=None,on_vector=None):
    import torch
    from transformers import AutoModel,AutoTokenizer
    path=Path(manifest_path);manifest=json.loads(path.read_text('utf8'))
    if manifest['model']!=core.ENCODER or manifest['revision']!=core.ENCODER_REVISION:
        raise ValueError('CA1 encoder identity changed')
    for name,record in manifest['files'].items():
        asset=path.parent/name;asset.resolve().relative_to(path.parent.resolve())
        if core.sha(asset)!=record['sha256']:raise ValueError('encoder asset hash mismatch')
    if 'model.safetensors' not in manifest['files']:raise ValueError('safe model asset required')
    torch.set_num_threads(2)
    tokenizer=AutoTokenizer.from_pretrained(str(path.parent),local_files_only=True,trust_remote_code=False)
    model=AutoModel.from_pretrained(str(path.parent),local_files_only=True,trust_remote_code=False,use_safetensors=True).to('cpu').eval()
    special=tokenizer.encode('',add_special_tokens=True)
    if len(special)!=2:raise ValueError('pinned single-sequence special-token template changed')
    unique=list(dict.fromkeys(texts));vectors=[];cache={} if cache is None else cache
    with torch.inference_mode():
        for text in unique:
            if text in cache:
                vectors.append(np.asarray(cache[text]));continue
            ids=tokenizer.encode(text,add_special_tokens=False);chunks=[]
            if tokenizer.encode(text,add_special_tokens=True)!=[special[0],*ids,special[1]]:
                raise ValueError('pinned chunk boundary token template changed')
            for start in range(0,max(1,len(ids)),126):
                token_ids=torch.tensor([[special[0],*ids[start:start+126],special[1]]],dtype=torch.long)
                encoded={'input_ids':token_ids,'attention_mask':torch.ones_like(token_ids)}
                state=model(**encoded).last_hidden_state;mask=encoded['attention_mask'][:,:,None]
                chunks.append(((state*mask).sum(dim=1)/mask.sum(dim=1)).numpy()[0])
            vector=np.mean(chunks,axis=0);norm=np.linalg.norm(vector)
            if not np.isfinite(vector).all() or norm<=0:raise ValueError('invalid encoder output')
            normalized=vector/norm;vectors.append(normalized)
            if on_vector is not None:on_vector(text,normalized)
    lookup={value:i for i,value in enumerate(unique)}
    return np.asarray(vectors)[[lookup[value] for value in texts]]


def collect(rows,roster,bank,draws=2000):
    result=core.compare(rows,roster,bank,draws)
    if result.get('authors',0)<20 and 'outcome' in result:result['outcome']='below floor, descriptive'
    return result


def execute(output:Path,inputs:dict,config:dict):
    phase=config['phase'];output.mkdir(parents=True,exist_ok=True)
    if phase=='GO1-score' and config['reader']=='encoder':
        rows=json.loads(Path(inputs['documents']).read_text('utf8'))['documents'];field=config.get('field','motivation');rest=config.get('rest','rest')
        roster=core.allocate(rows,config.get('distractors',49),field=field,other_types=config.get('other_types',False))
        if not roster:raise ValueError('no supported proposal roster')
        vectors=embeddings([r[rest] for r in rows]+[r[field] for r in rows],inputs['encoder_manifest'])
        scores=np.asarray([vectors[a['query']]@vectors[[len(rows)+j for j in a['candidates']]].T for a in roster]);np.save(output/'scores.npy',scores)
        core.write(output/'ALLOCATION.json',{'allocation':roster})
        result={'reader':'encoder','rows':len(roster),'candidate_count':scores.shape[1],'scores_sha256':core.sha(output/'scores.npy'),
                'allocation_sha256':core.sha(output/'ALLOCATION.json'),'complete_card':False,'encoder_manifest_sha256':core.sha(inputs['encoder_manifest'])}
        core.write(output/'SCORED.json',result);return result
    if phase=='GO1-collect':
        rows=json.loads(Path(inputs['documents']).read_text('utf8'))['documents'];bank={};roster=None
        for name,directory in inputs['readers'].items():
            path=Path(directory);allocation=json.loads((path/'ALLOCATION.json').read_text('utf8'))['allocation']
            if roster is not None and roster!=allocation:raise ValueError('reader rosters differ')
            receipt=json.loads((path/'SCORED.json').read_text('utf8'))
            if core.sha(path/'scores.npy')!=receipt['scores_sha256'] or core.sha(path/'ALLOCATION.json')!=receipt['allocation_sha256']:raise ValueError('reader source changed')
            roster=allocation;bank[name]=np.load(path/'scores.npy',allow_pickle=False)
        if set(bank)!={'tfidf','encoder','language_model'}:raise ValueError('whole GO1 primary requires all three readers')
        result=collect(rows,roster,bank,config.get('draws',2000));core.write(output/'RESULT.json',result);return result
    return core.execute(output,inputs,config)


def verify(output:Path,inputs:dict,config:dict):
    result=execute(output/'independent-replay',inputs,config);name='SCORED.json' if config['phase']=='GO1-score' else 'RESULT.json'
    if result!=json.loads((output/name).read_text('utf8')):raise ValueError('whole GO reader replay differs')
    if config['phase']=='GO1-score':
        if not np.array_equal(np.load(output/'scores.npy'),np.load(output/'independent-replay/scores.npy'),equal_nan=True):raise ValueError('every reader score must reproduce')
    return {'verified':True,'full_replay':True}
