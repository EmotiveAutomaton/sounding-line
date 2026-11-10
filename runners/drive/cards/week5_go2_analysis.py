"""GO2 whole comparison with sealed encoder-text checkpoints."""
from pathlib import Path
import json
import numpy as np
from . import week5_go as core
from . import week5_go_history as history
from .week5_go1_pipeline import vector_bank,Paused


def execute(output:Path,inputs:dict,config:dict):
    output.mkdir(parents=True,exist_ok=True)
    anchors=json.loads(Path(inputs['anchors']).read_text('utf8'))['anchors'];full=[r for r in anchors if r['three_each']]
    fallback=len(full)<100;selected=anchors if fallback else full
    if config.get('authors'):
        authors=sorted({r['author'] for r in selected});chosen=set(np.random.default_rng(core.SEED).permutation(authors)[:int(config['authors'])]);selected=[r for r in selected if r['author'] in chosen]
    if not selected:result={'card':'GO2','status':'unsupported','outcome':'below floor, descriptive','reason':'no bilateral observed-history anchors'}
    else:
        texts=[];slices=[]
        for row in selected:
            before=row['before'][-1:] if fallback else row['before'];after=row['after'][:1] if fallback else row['after']
            start=len(texts);texts.extend([row['old_goal'],row['new_goal'],*before,*after]);slices.append((start,len(before),len(after)))
        try:vectors=vector_bank(texts,inputs['encoder_manifest'],output/'vectors',config)
        except Paused:return {'status':'yielded','complete_card':False}
        before=[];after=[]
        for start,nb,na in slices:
            direction=vectors[start+1]-vectors[start];before.append(float(np.mean(vectors[start+2:start+2+nb]@direction)));after.append(float(np.mean(vectors[start+2+nb:start+2+nb+na]@direction)))
        result=history.reduce_contrasts(before,after,[r['author'] for r in selected],config.get('draws',2000))
        result.update(card='GO2',window='one before/one after fallback' if fallback else 'three before/three after',three_each_source_anchors=len(full),
                      scope='alignment with stated revised motivation; before contrast reports the reverse-direction rival',sample_scoped=bool(config.get('authors')))
        if len(selected)<100:result['outcome']='below floor, descriptive'
    core.write(output/'RESULT.json',result);return result


def verify(output:Path,inputs:dict,config:dict):
    result=execute(output/'independent-replay',inputs,config)
    if result.get('status')=='yielded':return {**result,'verified':False}
    if result!=json.loads((output/'RESULT.json').read_text('utf8')):raise ValueError('GO2 bounded independent comparison differs')
    for path in (output/'vectors').glob('*.json'):
        if path.name=='PROGRESS.json' or path.name.endswith('.seal.json'):continue
        if core.sha(path)!=core.sha(output/'independent-replay/vectors'/path.name):raise ValueError('GO2 individual encoder vector differs')
    return {'verified':True,'every_vector_and_comparison_replayed':True}
