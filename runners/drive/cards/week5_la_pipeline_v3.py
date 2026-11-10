"""LA v3 inherits the completed AT2 common-bank numerical specification.

Frozen model selection is an input, not chosen from a partial LA score bank.
All text and individual rows stay private; only final supported aggregates land.
"""
from collections import Counter,defaultdict
from pathlib import Path
import math,time
import numpy as np
from .week5_la import labelled_acts,joining_pairs,ResolutionScorer
from .week5_at_source import authenticate
from .week5_at_scoring import CausalScorer,SEED,digest
from .week5_at_scoring_v4 import load_model,NUMERICAL_SPEC
from .week5_at_selection import selected_reader
from .timing_census import read,filehash
from .timing_p6 import gzread,gzip_equal,write_equal,progress


def prepare(output,inputs,config,verifying=False):
    if set(inputs)!={'source_root'}:raise ValueError('Exact verified LA source required')
    source=authenticate(inputs['source_root'])/'output';root=Path(output);root.mkdir(parents=True,exist_ok=True)
    acts=gzread(source/'ACTS.json.gz');laughs=gzread(source/'LAUGHS.json.gz');metadata=gzread(source/'METADATA.json.gz')
    card=config['card'];corpus=config.get('corpus','both' if card=='LA1' else 'AMI')
    if corpus not in ('AMI','ICSI','both'):raise ValueError('Unregistered corpus')
    if config.get('label','vocal')=='vocal':laughs=[e for e in laughs if e['label']=='vocal']
    elif config['label']!='vocal_and_speech':raise ValueError('Unregistered laugh label')
    if corpus!='both':
        keep={m for m,v in metadata.items() if v['corpus']==corpus}
        acts=[a for a in acts if a['meeting'] in keep];laughs=[e for e in laughs if e['meeting'] in keep]
        metadata={m:v for m,v in metadata.items() if m in keep}
    if card=='LA2':
        background=config.get('background','native_language' if corpus=='AMI' else 'english_variety')
        if background not in ('native_language','english_variety','region'):raise ValueError('Unregistered background')
        rows=joining_pairs(laughs,metadata,background)
        possible=sum(len(v['speakers'])*(len(v['speakers'])-1)//2 for v in metadata.values())
        summary=dict(card=card,corpus=corpus,background=background,all_participant_pairs=possible,
                     supported_pairs=len(rows),unsupported_pairs=possible-len(rows),meetings=len(metadata))
        values={'ROWS.json.gz':rows};index=None
    elif card=='LA1':
        history=config.get('history_acts',5);window=config.get('window',2.);left=config.get('left',1.)
        if history not in (3,5,10) or (left,window) not in ((1.,1.),(1.,2.),(1.,3.),(5.,5.)):
            raise ValueError('Unregistered context/window')
        scope=config.get('laugh_scope','others' if config.get('others_only',False) else 'all')
        if scope not in ('all','own','others'):raise ValueError('Unregistered laughter ownership')
        labelled=labelled_acts(acts,laughs,window,left,scope=='others');past=defaultdict(list)
        if scope=='own':
            for act in labelled:act['laughed_after']=act['own_laugh']
        rows=[];counts=Counter();index=[]
        def flush():
            name=f'batches/acts-{len(index):06d}.json.gz'
            if verifying:
                if gzread(root/name)!=rows:raise ValueError('LA preparation replay differs')
            else:gzip_equal(root/name,rows)
            index.append(dict(file=name,rows=len(rows),sha256=filehash(root/name)));rows.clear()
        for a in labelled:
            previous=past[a['meeting']];counts['acts']+=1
            if len(previous)>=history:
                # Past means preceding completed acts. Concurrent ongoing acts
                # never contribute their as-yet-unspoken tail to the context.
                completed=[p for p in previous if p['end']<=a['start']]
                if len(completed)>=history:
                    row=dict(a,previous=' '.join(p['text'] for p in completed[-history:]),
                             causal_prefix=' '.join(p['text'] for p in completed)+' ',target=a['text'])
                    rows.append(row);counts['supported_history']+=1
                    if len(rows)==8:flush()
                else:counts['insufficient_completed_history']+=1
            else:counts['insufficient_prior_history']+=1
            past[a['meeting']].append(a)
        if rows:flush()
        values={}
        summary=dict(card=card,corpus=corpus,history_acts=history,window=window,left=left,counts=dict(counts),
                     meetings=len(metadata),source_sha256=filehash(Path(inputs['source_root'])/'COMPLETE.json'))
    else:raise ValueError('Unknown laughter preparation')
    for name,value in values.items():
        if verifying:
            if gzread(root/name)!=value:raise ValueError('LA preparation replay differs')
        else:gzip_equal(root/name,value)
    if index is not None:
        for row in index:row['sha256']=filehash(root/row['file'])
        if verifying:
            if read(root/'BATCHES.json')!=index:raise ValueError('LA batch roster changed')
        else:write_equal(root/'BATCHES.json',index)
    if verifying:
        if read(root/'SUMMARY.json')!=summary:raise ValueError('LA preparation reduction differs')
        return dict(verified=True,complete_source_projection=True)
    write_equal(root/'SUMMARY.json',summary);return dict(status='complete',card=card,scientific_admission=False)


def load_masked(manifest):
    if manifest['model'] not in ('distilroberta-base','distilbert/distilroberta-base') or not manifest.get('revision') or not manifest.get('licence'):
        raise ValueError('Pinned commissioned masked model required')
    for path,sha in manifest['files'].items():
        if filehash(path)!=sha:raise ValueError('Masked model snapshot changed')
    import torch
    from transformers import AutoTokenizer,AutoModelForMaskedLM
    torch.set_num_threads(2)
    tokenizer=AutoTokenizer.from_pretrained(manifest['tokenizer_path'],local_files_only=True,trust_remote_code=False)
    model=AutoModelForMaskedLM.from_pretrained(manifest['model_path'],local_files_only=True,trust_remote_code=False,
                                             use_safetensors=True,dtype=torch.float32).cpu().eval()
    return model,tokenizer,torch


def score(output,inputs,config,verifying=False):
    if set(inputs)!={'rows','causal_manifest','masked_manifest','selection_root'} or config.get('operation')!='score':
        raise ValueError('Exact LA scoring input/config required')
    selection=authenticate(inputs['selection_root']);selected=read(selection/'output/RESULT.json')
    causal=read(inputs['causal_manifest']);masked=read(inputs['masked_manifest'])
    if selected.get('card')!='AT2' or selected.get('selected_model')!=causal['model'] or selected.get('screening_only') or not selected.get('selection_admissible'):
        raise ValueError('LA requires completed primary AT2 reader selection')
    reader_binding=selected_reader(inputs['selection_root'],causal)
    root=Path(output);root.mkdir(parents=True,exist_ok=True);rows=gzread(inputs['rows'])
    binding=digest(dict(inputs={k:filehash(Path(v)/'COMPLETE.json') if k.endswith('_root') else filehash(v) for k,v in inputs.items()},config=config,numerical_spec=NUMERICAL_SPEC))
    started=time.monotonic();cpu=time.process_time()
    if (root/'YIELD_REQUEST.json').exists():
        return dict(status='yielded',reason='resource request before loading',completed=0,total=len(rows))
    model,tok,torch=load_model(causal);reader=CausalScorer(model,tok,torch,1024)
    masked_model,masked_tok,_=load_masked(masked);resolution=ResolutionScorer(masked_model,masked_tok,torch,mask_batch=8)
    load_seconds=time.monotonic()-started;values=[]
    for i,row in enumerate(rows):
        path=root/f'act-{i:03d}.json';seal=path.with_suffix('.receipt.json')
        if path.exists() and not verifying:
            if read(seal)['sha256']!=filehash(path):raise ValueError('LA score checkpoint seal differs')
            value=read(path)
        else:
            try:
                s=reader.score(row['causal_prefix'],row['target'])
                r=resolution.score(row['previous'],row['target'])
                value=dict(id=row['id'],binding=binding,status='supported',causal=s,resolution=r)
            except ValueError as error:
                # Length/support failures are explicit censored observations;
                # numerical or model failures are never converted to exclusions.
                if not any(t in str(error) for t in ('leaves no masked old support','Target loses its predictor','target exceeds')):raise
                value=dict(id=row['id'],binding=binding,status='unsupported',reason=str(error))
            if verifying:
                saved=read(path)
                if saved['status']!=value['status'] or saved['id']!=value['id'] or saved['binding']!=binding:
                    raise ValueError('LA scoring support differs')
                if value['status']=='supported':
                    old=saved['resolution'];new=value['resolution']
                    if any(old[k]!=new[k] for k in ('old_tokens','old_tokens_dropped','current_tokens')) or any(
                       np.max(np.abs(np.asarray(old[k])-np.asarray(new[k])))>1e-5 for k in ('before_logprobs','after_logprobs')):
                        raise ValueError('Masked paired score fresh-forward mismatch')
                    reader.direct_check(row['causal_prefix'],row['target'],saved['causal'])
                value=saved
            else:
                write_equal(path,value);write_equal(seal,dict(sha256=filehash(path)))
        if value['binding']!=binding or value['id']!=row['id']:raise ValueError('LA score identity differs')
        values.append(dict(file=path.name,sha256=filehash(path),id=row['id'],status=value['status']))
        progress(root/'PROGRESS.json',dict(phase='verify' if verifying else 'score',acts=i+1,total=len(rows),cold_load_seconds=load_seconds))
        if i+1<len(rows) and ((root/'YIELD_REQUEST.json').exists() or
                             (not verifying and time.monotonic()-started>config.get('max_wall_seconds',600))):
            return dict(status='yielded',reason='resource request or complete paired act checkpoint',completed=i+1,total=len(rows))
    summary=dict(causal_model=causal['model'],causal_revision=causal['revision'],causal_manifest_sha256=digest(causal),
                 masked_model=masked['model'],masked_revision=masked['revision'],masked_manifest_sha256=digest(masked),
                 numerical_spec=NUMERICAL_SPEC,masked_precision='float32_original',selected_reader_binding=reader_binding,
                 rows=len(rows),scientific_admission=False)
    if verifying:
        if read(root/'INDEX.json')!=values or read(root/'SUMMARY.json')!=summary:raise ValueError('LA scoring reduction differs')
        return dict(verified=True,complete_paired_mask_reforward=True)
    write_equal(root/'INDEX.json',values);write_equal(root/'SUMMARY.json',summary)
    write_equal(root/'COST.json',dict(elapsed_wall_seconds=time.monotonic()-started,process_cpu_seconds=time.process_time()-cpu,cold_load_seconds=load_seconds))
    return dict(status='complete',scientific_admission=False)


def collect(output,inputs,config,verifying=False):
    if set(inputs)!={'prepared_root','score_bank'}:raise ValueError('Exact full laughter bank required')
    source=authenticate(inputs['prepared_root'])/'output';bank=read(inputs['score_bank']);index=read(source/'BATCHES.json')
    if set(bank)!=set(x['file'] for x in index):raise ValueError('Incomplete laughter score bank')
    rows=[];unsupported=[];models=set();reader_banks=set()
    for item in index:
        path=source/item['file']
        if filehash(path)!=item['sha256']:raise ValueError('LA prepared source changed')
        score_root=authenticate(bank[item['file']]);root=score_root/'output';plan=read(score_root/'PLAN.json')
        summary=read(root/'SUMMARY.json')
        if plan['module']!='runners.drive.cards.week5_la_pipeline_v3' or filehash(plan['inputs']['rows'])!=filehash(path):raise ValueError('LA scorer/source binding differs')
        if summary.get('numerical_spec')!=NUMERICAL_SPEC or summary.get('masked_precision')!='float32_original':raise ValueError('Mixed LA reader numerical specification')
        reader_banks.add(digest({k:summary[k] for k in ('causal_manifest_sha256','masked_manifest_sha256','selected_reader_binding','numerical_spec')}))
        expected_binding=digest(dict(inputs={k:filehash(Path(v)/'COMPLETE.json') if k.endswith('_root') else filehash(v) for k,v in plan['inputs'].items()},config=plan['config'],numerical_spec=NUMERICAL_SPEC))
        values=read(root/'INDEX.json');original=gzread(path)
        if [r['id'] for r in original]!=[r['id'] for r in values]:raise ValueError('LA scored row population differs')
        models.add(read(root/'SUMMARY.json')['causal_model'])
        for row,value in zip(original,values):
            score_path=root/value['file']
            if filehash(score_path)!=value['sha256']:raise ValueError('LA scored act changed')
            score=read(score_path)
            if score['binding']!=expected_binding:raise ValueError('LA scored act numerical/input binding differs')
            if score['status']!='supported':unsupported.append(dict(id=row['id'],reason=score['reason']));continue
            projected={k:v for k,v in row.items() if k not in ('text','previous','causal_prefix','target')}
            rows.append(dict(projected,resolution=score['resolution']['resolution_nats_per_token'],
                             surprise=score['causal']['surprisal_nats']/row['word_count']))
    if len(models)!=1 or len(reader_banks)!=1:raise ValueError('Mixed selected causal/masked readers or numerical bindings')
    if len(unsupported)>max(0,(len(rows)+len(unsupported))*.01):
        raise ValueError('Laughter score collection exceeds one-percent unsupported allowance')
    root=Path(output);summary=dict(supported=len(rows),unsupported=len(unsupported),model=next(iter(models)),numerical_spec=NUMERICAL_SPEC,reader_bank_binding=next(iter(reader_banks)))
    for name,value in [('ROWS.json.gz',rows),('UNSUPPORTED.json.gz',unsupported)]:
        if verifying:
            if gzread(root/name)!=value:raise ValueError('LA complete bank projection differs')
        else:gzip_equal(root/name,value)
    if verifying:
        if read(root/'SUMMARY.json')!=summary:raise ValueError('LA complete bank reduction differs')
        return dict(verified=True,complete_bank_reduction=True)
    write_equal(root/'SUMMARY.json',summary);return dict(status='complete',scientific_admission=False)


def execute(output,inputs,config):
    operation=config.get('operation','prepare')
    return {'prepare':prepare,'score':score,'collect':collect}[operation](output,inputs,config)
def verify(output,inputs,config):
    operation=config.get('operation','prepare')
    return {'prepare':prepare,'score':score,'collect':collect}[operation](output,inputs,config,True)
