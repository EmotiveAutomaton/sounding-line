"""B4.ic observed-design conditional wild-game sensitivity.

DESIGN CHECK: LESSONS 3-5 and CONTROLS 6-7. Exact dose-shift parity must
hold for both stages and full intervals. Invalid worlds invalidate the grid;
null and signed worlds retain the original gates. No human exclusion claim.
"""
from pathlib import Path
from copy import deepcopy
import math
import numpy as np
from runners.stage14.common import freeze,read,filehash
from . import chess_model as model

DOSES=(-5.,0.,1.,5.,10.)

def design(values):
    _,r,t,_,middle,late,difficulty=values.T
    r=model.standardize(r);t=model.standardize(t)
    return np.column_stack([np.ones(len(r)),r,t,model.standardize(r*t),middle,late,model.standardize(difficulty)])

def shift(result,dose):
    out=deepcopy(result)
    if out['status']!='complete':return out
    for key in ('iv_product','ols_product'):out['fit'][key]+=dose
    for key in ('interval','ols_interval'):out[key]=[v+dose for v in out[key]]
    lo,hi=out['interval'];out['verdict']='supports' if lo>1 else 'against' if hi<=0 else 'inconclusive'
    return out

def wilson(successes,n):
    if not isinstance(successes,int) or not 0<=successes<=n or n<1:raise ValueError('Invalid count')
    z=1.959963984540054;q=successes/n;den=1+z*z/n
    center=(q+z*z/(2*n))/den;radius=z*math.sqrt(q*(1-q)/n+z*z/(4*n*n))/den
    return dict(successes=successes,total=n,rate=q,interval=[max(0.,center-radius),min(1.,center+radius)])

def validate():
    values,groups=model.constructed(0);x=design(values);zero=model.calculate(values,groups,64)
    comparisons=[]
    for dose in DOSES:
        changed=values.copy();changed[:,0]+=dose*x[:,3]
        actual=model.calculate(changed,groups,64);expected=shift(zero,dose)
        assert actual['status']==expected['status']=='complete' and actual['verdict']==expected['verdict']
        for key in ('iv_product','ols_product'):assert abs(actual['fit'][key]-expected['fit'][key])<1e-8
        for key in ('interval','ols_interval'):assert np.allclose(actual[key],expected[key],rtol=0,atol=1e-8)
        comparisons.append(dict(dose=dose,full_recomputation_parity=True))
    return dict(exact_shift_parity=comparisons,zero_world=zero)

def wild_outcome(baseline,residual,inverse,signs):
    if not np.isin(signs,[-1.,1.]).all():raise ValueError('Invalid game signs')
    return baseline+residual*signs[inverse]

def calculate(values,groups,worlds=100,draws=2000):
    x=design(values);beta=np.linalg.lstsq(x,values[:,0],rcond=None)[0]
    residual=values[:,0]-x@beta;baseline=x@beta-beta[3]*x[:,3]
    unique,inverse=np.unique(groups,return_inverse=True);rng=np.random.default_rng(20261106)
    results=[];invalid=0
    for world in range(worlds):
        signs=rng.choice(np.array([-1.,1.]),size=len(unique));synthetic=values.copy()
        synthetic[:,0]=wild_outcome(baseline,residual,inverse,signs)
        base=model.calculate(synthetic,groups,draws)
        if base['status']!='complete':invalid+=1
        results.append(dict(world=world,zero=base))
    if invalid:return dict(status='invalid calibration',invalid_worlds=invalid,worlds=worlds,records=results)
    rows=[]
    for dose in DOSES:
        shifted=[shift(r['zero'],dose) for r in results]
        counts=dict(positive_zero_exclusion=sum(r['interval'][0]>0 for r in shifted),negative_zero_exclusion=sum(r['interval'][1]<0 for r in shifted),
            clears_practical_bar=sum(r['interval'][0]>1 for r in shifted),coverage=sum(r['interval'][0]<=dose<=r['interval'][1] for r in shifted),
            either_sign_zero_exclusion=sum(r['interval'][0]>0 or r['interval'][1]<0 for r in shifted))
        for verdict in ('supports','against','inconclusive'):counts['verdict_'+verdict]=sum(r['verdict']==verdict for r in shifted)
        rows.append(dict(dose=dose,counts={k:wilson(int(v),worlds) for k,v in counts.items()}))
    null=next(r for r in rows if r['dose']==0)['counts'];practical=next(r for r in rows if r['dose']==1)['counts']
    adequate=practical['positive_zero_exclusion']['interval'][0]>=.8 and null['either_sign_zero_exclusion']['interval'][1]<=.1
    return dict(status='complete',worlds=worlds,bootstrap_draws_per_world=draws,games=len(unique),moves=len(values),invalid_worlds=0,
        directional_sensitivity_at_practical_size='adequate in construction' if adequate else 'limited in construction',
        construction='Fixed observed predictors; independent whole-game residual sign flips under a zero-interaction linear nuisance model',
        causal_claim=False,rows=rows,records=results)

def execute(output,inputs,config):
    output=Path(output);output.mkdir(parents=True,exist_ok=True)
    if config.get('constructed'):result=validate()
    else:
        source=Path(inputs['source']['path']);assert filehash(source)==inputs['source']['sha256']
        with np.load(source) as s:result=calculate(s['values'],s['groups'],config.get('worlds',100),2000)
    freeze(output/'CALIBRATION.json',result);return dict(status='complete',constructed=bool(config.get('constructed')))

def verify(output,inputs,config):
    if config.get('constructed'):result=validate()
    else:
        source=Path(inputs['source']['path']);assert filehash(source)==inputs['source']['sha256']
        with np.load(source) as s:result=calculate(s['values'],s['groups'],config.get('worlds',100),2000)
    assert result==read(Path(output)/'CALIBRATION.json')
    return dict(verified=True,complete_recalculation=True)
