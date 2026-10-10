"""Q02/Q05 conditional continuation, selected on earlier calibration only.

DESIGN CHECK: LESSONS 3-5. NULL: grossly harmful or sparse incomplete calibration
does not justify deeper training. ALTERNATIVE: an executable non-dominated recipe
with at least twelve writers warrants the predeclared dose/capacity question.
Passing licenses more experiments, never a positive scientific result. A refused
gate does not delete independent local reader or non-generative families.
"""
import numpy as np
from .common import read,freeze,filehash
from .adaptive_v2 import prepare_cases,proper,probs,run as adaptive_run
from runners.stage13.detectors import cached_model

def run(card,out,raw,tick):
    if card['mode']=='selected_adapter':
        selection=read(raw/'jobs'/card['selector']/'ADMISSION.json')
        if not selection['admitted']:raise ValueError('continuation gate refused')
        resolved=dict(card,rank=selection['selected_rank']);freeze(out/'RESOLVED_CARD.json',dict(rank=resolved['rank'],selection_sha256=filehash(raw/'jobs'/card['selector']/'ADMISSION.json'),reason='rank chosen on earlier calibration, never future evaluation'))
        return adaptive_run(resolved,out,raw,tick)
    from transformers import AutoTokenizer
    data=raw/'jobs'/card['data'];rows=read(data/'READER.json');truth={r['key']:r for r in read(data/'EVALUATOR.json')};options=[]
    for job in card['parents']:
        original=read(raw/'cards'/f'{job}.json');costs=read(raw/'jobs'/job/'COSTS.json');tok=AutoTokenizer.from_pretrained(cached_model(original['backbone']),local_files_only=True,trust_remote_code=False);values=[];delta=[]
        for writer,cost in sorted(costs.items()):
            cases,_=prepare_cases(rows,truth,tok,writer,'calibration');loss={}
            for arm in ('own','base','donor'):
                vals=[(np.array(v)/np.array([len(x) for x in c['choices']])).tolist() for v,c in zip(cost['details'][arm]['calibration_raw'],cases)]
                t=min((.01,.025,.05,.1,.25,.5,1,2,4),key=lambda t:np.mean([proper(probs(v,t),c['truth'])['half_brier'] for v,c in zip(vals,cases)]))
                loss[arm]=float(np.mean([proper(probs(v,t),c['truth'])['half_brier'] for v,c in zip(vals,cases)]))
            values.append(loss['own']);delta.append(loss['own']-min(loss['base'],loss['donor']))
        options.append(dict(parent=job,rank=original['rank'],writers=len(costs),calibration_loss=float(np.mean(values)),calibration_excess_over_best_rival=float(np.mean(delta)),training_tokens=original['training_tokens']))
    selected=min(options,key=lambda x:(x['calibration_loss'],x['rank']))
    admit=selected['writers']>=12 and selected['calibration_excess_over_best_rival']<=.05
    freeze(out/'SUMMARY.json',dict(options=options,selected=selected,scope='recipe selection for dose and capacity tests; calibration optimism retained; all future comparisons descriptive'))
    freeze(out/'ADMISSION.json',dict(admitted=admit,selected_rank=selected['rank'],reason='sufficient execution support and no gross calibration harm' if admit else 'insufficient support or gross calibration harm; no deeper text-only ladder',scientific_positive=False))
