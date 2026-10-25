"""WA1 saved adapter likelihoods and canonical-choice input preparation.

DESIGN CHECK: LESSONS 3-5 and CONTROLS 1-7. No inference or fit is run.
Every original completed cell, writer, calibration row and evaluation row is
retained. A changed target is explicit; ambiguous canonical targets refuse.
Native tokenizer filtering and original calibrated forecasts must reproduce.
"""
from collections import Counter
from pathlib import Path

import numpy as np
from scipy.special import softmax

from runners.stage14 import adaptive_v2 as original
from runners.stage13.detectors import cached_model
from .timing_census import read, filehash
from .timing_p6 import gzread, gzip_equal, write_equal, progress
from .timing_stats import bind, check_binding

CONFIG=dict(card='WA1-inputs',schema=1,mode='full',expected_cells=86)
CONSTRUCTED=dict(CONFIG,mode='constructed',expected_cells=1)
ARMS=('base','own','pooled','donor')
TEMPERATURES=(.01,.025,.05,.1,.25,.5,1.,2.,4.)

def authenticate(root,names,pins):
    root=Path(root);complete=read(root/'COMPLETE.json')
    if str(complete.get('status')).upper()!='COMPLETE':raise ValueError('source is not complete')
    pins[str((root/'COMPLETE.json').resolve())]=filehash(root/'COMPLETE.json')
    for name in names:
        path=root/name;digest=filehash(path)
        if complete['outputs'].get(name)!=digest:raise ValueError('completed source artifact changed')
        pins[str(path.resolve())]=digest
    return complete

def normalized(raw,lengths,temp):
    if any(type(x) is not int or x<=0 for x in lengths):raise ValueError('native token lengths must be positive integers')
    values=np.asarray(raw,float);lengths=np.asarray(lengths,int)
    if (values.ndim!=1 or values.shape!=lengths.shape or len(values)<2 or
        not np.isfinite(values).all() or np.any(lengths<=0)):
        raise ValueError('native likelihood option support differs')
    return softmax(values/lengths/temp).tolist()

def temperature(raw,cases):
    if len(raw)!=len(cases) or not cases:raise ValueError('calibration roster mismatch')
    return min(TEMPERATURES,key=lambda t:(np.mean([
        original.proper(normalized(v,c['lengths'],t),c['truth'])['half_brier']
        for v,c in zip(raw,cases)]),t))

def prepare_cell(name,cases,costs,predictions,calibration):
    """Bind raw arrays to original scored keys; never drop an affected row."""
    by_key={r['key']:r for r in predictions}
    if len(by_key)!=len(predictions):raise ValueError('duplicate original prediction key')
    out=[];consumed=set();counts=Counter()
    if set(cases)!=set(costs) or set(calibration)!=set(costs):raise ValueError('original writer roster differs')
    for writer,cost in sorted(costs.items()):
        phases=cases[writer]
        if set(phases)!={'calibration','evaluation'}:raise ValueError('required original partitions absent')
        for phase,rows in phases.items():
            if not rows or len({r['key'] for r in rows})!=len(rows):raise ValueError('empty or duplicate original partition')
            for r in rows:
                if (r['writer']!=writer or not 0<=r['truth']<len(r['lengths']) or
                    not 0<=r['canonical_truth']<len(r['lengths'])):raise ValueError('invalid original/canonical target')
                counts[phase+'_rows']+=1;counts[phase+'_changed']+=r['truth']!=r['canonical_truth']
        details=cost['details'];block=dict(writer=writer,donor=cost.get('donor'),cutoff=cost.get('cutoff'),
            cases=phases,raw={},old_temperatures={})
        for arm in ARMS:
            cc=details[arm]['calibration_raw'];ev=details[arm]['evaluation_raw']
            if len(cc)!=len(phases['calibration']) or len(ev)!=len(phases['evaluation']):raise ValueError('raw likelihood roster mismatch')
            t=temperature(cc,phases['calibration']);old=calibration[writer][arm+'_mean']
            if old['temperature']!=t or old['calibration_cases']!=len(cc):raise ValueError('original calibration does not reproduce')
            for v,row in zip(ev,phases['evaluation']):
                p=by_key.get(row['key'])
                if p is None or any(p[k]!=row[k] for k in ('writer','prompt','truth')):raise ValueError('original evaluation identity differs')
                actual=normalized(v,row['lengths'],t)
                if not np.allclose(actual,p['probabilities'][arm+'_mean'],rtol=0,atol=1e-12):raise ValueError('retained likelihood probabilities do not reproduce')
                consumed.add(row['key'])
            # Validate every calibration vector as well as every evaluation vector.
            for v,row in zip(cc,phases['calibration']):normalized(v,row['lengths'],t)
            block['raw'][arm]=dict(calibration=cc,evaluation=ev);block['old_temperatures'][arm]=t
        out.append(block)
    if consumed!=set(by_key):raise ValueError('original scored population not exhausted exactly')
    return dict(cell=name,writers=out,census=dict(counts))

def canonical_case(case,row,truth,audit,roster):
    proof=audit.get(case['key'])
    if proof is None:raise ValueError('original saved row lacks canonical proof')
    if (proof['writer']!=row['writer'] or proof['session']!=row['session'] or proof['ordinal']!=row['ordinal'] or
        proof['canonical_option_ids']!=row['option_indices'] or not proof['canonical_usable'] or
        not proof['verified_insertion'] or proof['canonical_handling'] not in ('accept','edit') or
        len(proof['canonical_positions'])!=1):raise ValueError('canonical proof or option identity differs')
    if proof['logged_selected_index']!=truth['selected_index']:raise ValueError('Stage14 label is not the bound logged choice')
    if roster[row['session']]['source_sha256']!=proof['raw_source_sha256']:raise ValueError('canonical/raw dataset identity differs')
    return dict(key=case['key'],writer=case['writer'],prompt=case['prompt'],session=row['session'],ordinal=row['ordinal'],
        truth=case['truth'],canonical_truth=proof['canonical_positions'][0],lengths=[len(x) for x in case['choices']],
        input_digest=case['input_digest'],canonical_sha256=proof['canonical_sha256'],raw_source_sha256=proof['raw_source_sha256'])

def load_full(inputs,checkpoint):
    if set(inputs)!={'stage14_final_table','stage14_raw','selection_complete'}:raise ValueError('fixed WA1 input contract required')
    root=Path(inputs['stage14_raw']);manifest=read(inputs['stage14_final_table']);pins={}
    pins[str(Path(inputs['stage14_final_table']).resolve())]=filehash(inputs['stage14_final_table'])
    entries=manifest['cells']
    if len(entries)!=86 or len({r['cell'] for r in entries})!=86:raise ValueError('original 86-cell population changed')
    auditroot=Path(inputs['selection_complete']).parent
    authenticate(auditroot,['ROWS.json','INPUT_PINS.json'],pins)
    audit_rows=read(auditroot/'ROWS.json');audit={r['key']:r for r in audit_rows}
    if len(audit)!=len(audit_rows):raise ValueError('duplicate canonical proof')
    tokens={};prepared={};datasets={};cells=[]
    for index,entry in enumerate(entries):
        name=entry['cell'];cardpath=root/'cards'/f'{name}.json';card=read(cardpath);pins[str(cardpath.resolve())]=filehash(cardpath)
        if card['handler']!='adapter_readouts':raise ValueError('original final cell is not the frozen readout')
        producer,data=card['requires'];job=root/'jobs'/name;complete=authenticate(job,['PREDICTIONS.json','CALIBRATION.json','SUMMARY.json'],pins)
        if complete['card_sha256']!=filehash(cardpath):raise ValueError('readout card identity changed')
        producerpath=root/'cards'/f'{producer}.json';pc=read(producerpath);pins[str(producerpath.resolve())]=filehash(producerpath)
        original_source=Path(original.__file__).resolve();source_relative='runners/stage14/adaptive_v2.py'
        if pc['source_pins'].get(source_relative)!=filehash(original_source):raise ValueError('original case-preparation source changed')
        pins[str(original_source)]=filehash(original_source)
        original_complete=authenticate(root/'jobs'/producer,['COSTS.json','MODEL.json','PREDICTIONS.json'],pins)
        if original_complete['card_sha256']!=filehash(producerpath):raise ValueError('adapter card identity changed')
        if data not in datasets:
            data_root=root/'jobs'/data;authenticate(data_root,['READER.json','EVALUATOR.json','SPLITS.json'],pins)
            dcpath=root/'cards'/f'{data}.json';dc=read(dcpath);pins[str(dcpath.resolve())]=filehash(dcpath)
            foundation=root/'jobs'/dc['requires'][0];authenticate(foundation,['ROSTER.json'],pins)
            rr=read(data_root/'READER.json');tt=read(data_root/'EVALUATOR.json');roster=read(foundation/'ROSTER.json')
            datasets[data]=(rr,{r['key']:r for r in tt},{r['session']:r for r in roster})
            if len(datasets[data][1])!=len(tt) or len({r['key'] for r in rr})!=len(rr):raise ValueError('duplicate original input key')
        rr,tt,roster=datasets[data];bykey={r['key']:r for r in rr};model=pc['backbone']
        if model not in tokens:
            from transformers import AutoTokenizer
            modelpath=cached_model(model)
            for fn in ('tokenizer.json','tokenizer_config.json','vocab.json','merges.txt','special_tokens_map.json','config.json'):
                if fn in pc['model_files']:
                    path=modelpath/fn
                    if filehash(path)!=pc['model_files'][fn]:raise ValueError('native tokenizer source changed')
                    pins[str(path.resolve())]=filehash(path)
            tokens[model]=AutoTokenizer.from_pretrained(modelpath,local_files_only=True,trust_remote_code=False)
        costs=read(root/'jobs'/producer/'COSTS.json');cases={}
        for writer in sorted(costs):
            key=(data,model,writer)
            if key not in prepared:
                phases={}
                for phase in ('calibration','evaluation'):
                    original_cases,_=original.prepare_cases(rr,tt,tokens[model],writer,phase)
                    phases[phase]=[canonical_case(c,bykey[c['key']],tt[c['key']],audit,roster) for c in original_cases]
                    for c in original_cases:
                        proof=audit[c['key']];path=Path(proof['canonical_path']);digest=filehash(path)
                        if digest!=proof['canonical_sha256']:raise ValueError('canonical source record changed')
                        pins[str(path.resolve())]=digest
                prepared[key]=phases
            cases[writer]=prepared[key]
        cell=prepare_cell(name,cases,costs,read(job/'PREDICTIONS.json'),read(job/'CALIBRATION.json'))
        if len(cell['writers'])!=entry['writers']:raise ValueError('final manifest writer count differs')
        cell.update(backbone=model,producer=producer,corpus=pc.get('corpus'),rank=pc.get('rank'),seed=pc['seed'])
        cells.append(cell);checkpoint(index+1,len(entries))
    if any(filehash(p)!=digest for p,digest in pins.items()):raise ValueError('source changed during preparation')
    return cells,pins

def run(output,inputs,config,verification=False):
    if config not in (CONFIG,CONSTRUCTED):raise ValueError('fixed WA1 source configuration required')
    output=Path(output);output.mkdir(parents=True,exist_ok=True)
    def tick(done,total):
        if (output.parent/'STOP').exists() or (output/'YIELD_REQUEST.json').exists():raise InterruptedError('WA1 source stop requested')
        progress(output/'PROGRESS.json',dict(phase='verify' if verification else 'prepare',done=done,total=total))
    if config==CONSTRUCTED:
        if set(inputs)!={'fixture'}:raise ValueError('constructed fixture contract differs')
        data=read(inputs['fixture']);cells=[prepare_cell(**data)];pins={str(Path(inputs['fixture']).resolve()):filehash(inputs['fixture'])}
    else:cells,pins=load_full(inputs,tick)
    if len(cells)!=config['expected_cells']:raise ValueError('required full cell roster absent')
    summary=dict(card='WA1-inputs',cells=len(cells),cell_census=[dict(cell=c['cell'],writers=len(c['writers']),**c['census']) for c in cells],
        no_new_inference=True,no_new_performance_results=True,canonical_labels_prepared=True,
        original_calibrated_probabilities_reproduced=True,
        scope='Complete original Stage14 final 86-cell roster; later Stage15 repairs remain separate; original saved/model-filtered populations retained')
    sources=dict(config=config,pins=pins)
    if verification:
        check_binding(output,inputs,config)
        if gzread(output/'LIKELIHOODS.json.gz')!=cells or read(output/'SOURCE_BINDINGS.json')!=sources or read(output/'SUMMARY.json')!=summary:
            raise ValueError('fresh WA1 source preparation differs')
        return dict(verified=True,original_scores_reproduced=True)
    gzip_equal(output/'LIKELIHOODS.json.gz',cells);write_equal(output/'SOURCE_BINDINGS.json',sources);write_equal(output/'SUMMARY.json',summary)
    bind(output,inputs,config,['LIKELIHOODS.json.gz','SOURCE_BINDINGS.json','SUMMARY.json'])
    return dict(status='complete',no_new_inference=True)

def execute(output,inputs,config):return run(output,inputs,config)
def verify(output,inputs,config):return run(output,inputs,config,True)
