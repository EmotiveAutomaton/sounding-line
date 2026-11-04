"""T4 complete text/role cache and bounded CPU encoder preparation.

DESIGN CHECK: LESSONS3-5. Exact legacy cache text/role digests and completed
sources bind reuse. Future histories are retained as source data, not selected
for a target; no model score exists here. Missing, altered and nonfinite
representations refuse. Native repeated/cached anchors precede new encoding.
"""
from pathlib import Path
import json,time
import numpy as np
from .timing_census import read,filehash
from .timing_p6 import gzread,gzip_equal,write_equal,progress
from .timing_pmap_source import completed,bound_record
from .events_p5 import Encoder
from runners.drive.content_features_v2 import token_view
from runners.stage14.common import digest

def configuration(mode):
    if mode not in ('constructed','timing','full'):raise ValueError('Unknown encoding scope')
    return dict(card='T4-encoding',mode=mode,batch_size=16,threads=1,pilot=128,tolerance=2e-6)

def inventory(menus,histories,visibility):
    cached={v['key']:i for i,v in enumerate(visibility)}
    if len(cached)!=len(visibility):raise ValueError('Duplicate cache key')
    jobs={};refs=[];hs=[];new_order=[]
    def add(text,role):
        key=digest([text,role])
        if key in cached:
            scope=visibility[cached[key]]
            if scope['text_sha256']!=digest(text) or scope['role']!=role:raise ValueError('Cached text/role binding differs')
            return dict(cached=cached[key],key=key)
        if key not in jobs:jobs[key]=dict(key=key,text=text,role=role);new_order.append(key)
        return dict(new=key)
    for s in sorted(menus,key=lambda x:x['session']):
        for m in s['menus']:
            refs.append(dict(key=m['key'],session=s['session'],options=[add(t,'suggestion') for t in m['options']],context=add(m['preceding_visible_sentence'],'context')))
    for s in sorted(histories,key=lambda x:x['session']):
        hs.append(dict(session=s['session'],writer=s['writer'],timestamp=s['timestamp'],end_at=s['end_at'],sequences=[add(' '.join(seq),'suggestion') for seq in s['training_sequences'] if seq]))
    return dict(jobs=[jobs[k] for k in new_order],menus=refs,histories=hs,cached_vectors=len(visibility))

def fixture():
    text='Known text';cache=[dict(key=digest([text,'suggestion']),text_sha256=digest(text),role='suggestion')]
    menus=[dict(session='s',menus=[dict(key='m',options=[text,'New choice'],preceding_visible_sentence=text)])]
    histories=[dict(session='s',writer='w',timestamp=1000,end_at=2000,training_sequences=[['New','choice'],[]])]
    return menus,histories,cache

def load(inputs,mode):
    if mode=='constructed':
        if inputs:raise ValueError('Constructed only')
        return inventory(*fixture()),None
    if set(inputs)!={'menus_completion','p6_index','p6_completion','content_completion'}:raise ValueError('Exact input registry required')
    mc=Path(inputs['menus_completion']);completed(mc,mc.parent/'output/MENUS.json.gz');menus=gzread(mc.parent/'output/MENUS.json.gz')
    if len(menus)!=1399 or len({s['session'] for s in menus})!=1399:raise ValueError('Whole menu population differs')
    index=Path(inputs['p6_index']);completed(inputs['p6_completion'],index);histories=[bound_record(index,r) for r in read(index)]
    if {s['session']:s['writer'] for s in menus}!={s['session']:s['writer'] for s in histories}:raise ValueError('Complete history/menu writer join differs')
    cc=Path(inputs['content_completion'])
    for name in ('MODEL.json','VECTORS.npy','VISIBILITY.json'):completed(cc,cc.parent/name,fresh=False)
    visibility=read(cc.parent/'VISIBILITY.json');vectors=np.load(cc.parent/'VECTORS.npy',allow_pickle=False)
    if vectors.shape!=(len(visibility),384) or not np.isfinite(vectors).all() or not np.allclose(np.linalg.norm(vectors,axis=1),1,atol=1e-5):raise ValueError('Legacy cache vector shape/norm invalid')
    return inventory(menus,histories,visibility),dict(root=cc.parent,vectors=vectors,visibility=visibility)

def forward(enc,ids):
    torch=enc.torch;width=max(map(len,ids));mask=torch.tensor([[1]*len(i)+[0]*(width-len(i)) for i in ids])
    tokens=torch.tensor([i+[enc.tokenizer.pad_token_id]*(width-len(i)) for i in ids])
    with torch.inference_mode():
        states=enc.model(input_ids=tokens,attention_mask=mask).last_hidden_state
        arr=((states*mask.unsqueeze(-1)).sum(1)/mask.sum(1,keepdim=True)).numpy().astype(np.float32)
    arr/=np.maximum(np.linalg.norm(arr,axis=1,keepdims=True),1e-12)
    if arr.shape!=(len(ids),384) or not np.isfinite(arr).all() or not np.allclose(np.linalg.norm(arr,axis=1),1,atol=1e-5):raise ValueError('Invalid new vector')
    return arr

def run(output,inputs,config,verification=False):
    if config!=configuration(config['mode']):raise ValueError('Frozen encoder configuration required')
    output=Path(output);started=time.process_time();data,cache=load(inputs,config['mode']);source_cpu=time.process_time()-started
    base=dict(source=data,inputs={k:filehash(v) for k,v in inputs.items()})
    if config['mode']=='constructed':
        assert len(data['jobs'])==2 and len(data['histories'][0]['sequences'])==1
        assert data['menus'][0]['options'][0]['cached']==0 and data['menus'][0]['context']['new']!=data['menus'][0]['options'][1]['new']
        summary=dict(known_cache_join=True,scientific_effect_computed=False)
        payload={'SUMMARY.json':summary,'INVENTORY.json.gz':base}
    else:
        load_start=time.process_time();enc=Encoder(cache['root']/'MODEL.json',1,16);model_cpu=time.process_time()-load_start
        jobs=data['jobs'];views={j['key']:token_view(enc.tokenizer,j['text'],j['role']) for j in jobs}
        order=sorted(jobs,key=lambda j:(len(views[j['key']][0]),j['key']))
        if config['mode']=='timing':
            indices=np.unique(np.linspace(0,len(order)-1,min(128,len(order)),dtype=int));order=[order[int(i)] for i in indices]
        # Cached anchor strings are recovered from current menus only, never
        # reconstructed by decoding tokenizer IDs or invented from vector keys.
        mc=Path(inputs['menus_completion']);menus=gzread(mc.parent/'output/MENUS.json.gz');anchors={}
        cache_index={s['key']:i for i,s in enumerate(cache['visibility'])}
        for s in menus:
            for m in s['menus']:
                for text in m['options']:
                    key=digest([text,'suggestion'])
                    if key in cache_index:anchors.setdefault(key,(text,cache_index[key]))
            if len(anchors)>=64:break
        chosen=[anchors[k] for k in sorted(anchors)[:64]]
        if len(chosen)!=64:raise ValueError('Insufficient exact cached anchors')
        for start in range(0,64,16):
            part=chosen[start:start+16];ids=[token_view(enc.tokenizer,t,'suggestion')[0] for t,i in part];arr=forward(enc,ids)
            if not np.allclose(arr,cache['vectors'][[i for t,i in part]],rtol=0,atol=config['tolerance']):raise ValueError('Actual cached encoder disagreement')
            if not np.array_equal(arr,forward(enc,ids)):raise ValueError('Encoder repeat changed')
        setup_cpu=time.process_time()-started;begin=time.process_time();vectors=[];scope=[]
        for start in range(0,len(order),16):
            batch=order[start:start+16];arr=forward(enc,[views[j['key']][0] for j in batch]);vectors.extend(arr)
            scope.extend(dict(key=j['key'],**views[j['key']][1]) for j in batch)
            progress(output/'PROGRESS.json',dict(phase='verify-encode' if verification else 'encode',done=min(start+16,len(order)),total=len(order)))
        encoding_cpu=time.process_time()-begin;vectors=np.asarray(vectors,np.float32).reshape((-1,384))
        if verification:
            if not np.allclose(np.load(output/'VECTORS.npy',allow_pickle=False),vectors,rtol=0,atol=config['tolerance']):raise ValueError('Complete fresh encoder replay differs')
        else:np.save(output/'VECTORS.npy',vectors,allow_pickle=False)
        summary=dict(mode=config['mode'],source_sessions=len(data['histories']),menus=len(data['menus']),cached_vectors=len(cache['vectors']),new_texts=len(jobs),encoded_texts=len(order),truncated=sum(s['truncated'] for s in scope),cached_anchors=64,repeat_passed=True,scientific_effect_computed=False,history_selection_performed=False,device='cpu',threads=1)
        payload={'SUMMARY.json':summary,'INVENTORY.json.gz':base,'VISIBILITY.json':scope}
        if not verification:
            full_tokens=sum(len(v[0]) for v in views.values());pilot_tokens=sum(len(views[j['key']][0]) for j in order)
            write_equal(output/'TIMING.json',dict(source_cpu_seconds=source_cpu,model_load_cpu_seconds=model_cpu,setup_cpu_seconds=setup_cpu,encoding_cpu_seconds=encoding_cpu,encoded_tokens=pilot_tokens,full_tokens=full_tokens,full_forecast_cpu_seconds=3*(setup_cpu+encoding_cpu*full_tokens/max(1,pilot_tokens))))
    for n,v in payload.items():
        if verification:
            old=gzread(output/n) if n.endswith('.gz') else read(output/n)
            if old!=v:raise ValueError('Encoder inventory replay differs')
        elif n.endswith('.gz'):gzip_equal(output/n,v)
        else:write_equal(output/n,v)
    return dict(verified=True,complete_source_replay=True,complete_encoder_replay=True) if verification else dict(status='complete')

def execute(output,inputs,config):return run(output,inputs,config)
def verify(output,inputs,config):return run(output,inputs,config,True)
