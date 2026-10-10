"""P03 preregistered CPU readouts of frozen native likelihoods, no new fitting.

DESIGN CHECK: LESSONS 3-5; SL6/9. NULL: total-length preference or calibration
selection explains apparent adaptation. ALTERNATIVE: normalized and residual
signals improve later choice. Raw sum remains a named sensitivity. Temperature
uses only the same writer's earlier calibration, with no evaluation optimization.
This consumer was defined before corrected main cells completed.
"""
import numpy as np
from .common import read,freeze
from .adaptive_v2 import prepare_cases,proper,probs
from .uncertainty_v2 import contrast
from runners.stage13.detectors import cached_model

def run(card,out,raw,tick):
    from transformers import AutoTokenizer
    parent=raw/'jobs'/card['requires'][0];data=raw/'jobs'/card['requires'][1]
    source_card=read(raw/'cards'/f"{card['requires'][0]}.json");tok=AutoTokenizer.from_pretrained(cached_model(source_card['backbone']),local_files_only=True,trust_remote_code=False)
    rows=read(data/'READER.json');truth={r['key']:r for r in read(data/'EVALUATOR.json')};costs=read(parent/'COSTS.json');results=[];calibration={}
    for writer,cost in sorted(costs.items()):
        cc,_=prepare_cases(rows,truth,tok,writer,'calibration');ev,_=prepare_cases(rows,truth,tok,writer,'evaluation');d=cost['details'];derived={}
        for arm in ('base','own','pooled','donor'):
            for kind in ('sum','mean','delta_mean'):
                if kind=='delta_mean' and arm=='base':continue
                values=[]
                for partition,cases in [('calibration',cc),('evaluation',ev)]:
                    raw_values=d[arm][partition+'_raw'];base=d['base'][partition+'_raw']
                    if len(raw_values)!=len(cases):raise ValueError('retained likelihood roster mismatch')
                    current=[]
                    for a,b,c in zip(raw_values,base,cases):
                        lens=np.array([len(x) for x in c['choices']]);a=np.array(a);b=np.array(b)
                        if len(a)!=len(lens) or len(a)!=len(b):raise ValueError('native option support mismatch')
                        current.append((a if kind=='sum' else a/lens if kind=='mean' else (a-b)/lens).tolist())
                    values.append(current)
                temperatures=(.01,.025,.05,.1,.25,.5,1.,2.,4.) if kind!='sum' else (.25,.5,1.,2.,4.)
                temp=min(temperatures,key=lambda t:(np.mean([proper(probs(v,t),c['truth'])['half_brier'] for v,c in zip(values[0],cc)]),t))
                name=arm+'_'+kind;derived[name]=[probs(v,temp) for v in values[1]];calibration.setdefault(writer,{})[name]=dict(temperature=temp,calibration_cases=len(cc))
        for i,c in enumerate(ev):
            ps={m:v[i] for m,v in derived.items()};ps['uniform']=[1/len(c['choices'])]*len(c['choices'])
            results.append({k:c[k] for k in ('key','writer','prompt','truth')}|dict(probabilities=ps,scores={k:proper(p,c['truth']) for k,p in ps.items()}))
        tick(dict(writers=len(calibration),total_writers=len(costs)))
    if not results:raise ValueError('no complete native likelihoods')
    freeze(out/'PREDICTIONS.json',results);freeze(out/'CALIBRATION.json',calibration)
    comparisons=[('own_mean',b) for b in ('base_mean','pooled_mean','donor_mean','uniform')]+[('own_delta_mean',b) for b in ('donor_delta_mean','pooled_delta_mean','uniform')]+[('own_sum','base_sum')]
    freeze(out/'SUMMARY.json',dict(writers=len(costs),cases=len(results),contrasts=[contrast(results,a,b) for a,b in comparisons],primary='native length-normalized conditional candidate likelihood',sensitivities=['raw sum','adapted-minus-base length-normalized likelihood signal'],scope='exposed known-writer later choices; no large-reader fusion; one-writer pilots cannot license inference'))
