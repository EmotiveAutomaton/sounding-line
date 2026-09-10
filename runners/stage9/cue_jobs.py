"""Freeze all reported-context forecasts before comparing to the new actual future.

DESIGN CHECK: T04/X02/X06/X08; LESSONS 3--5, CONTROLS 6--7.
NULL: changed source truth, missing assigned calls or altered support invalidates;
a true/false evaluation label may never enter the reader. ALTERNATIVE: prospective
correction and susceptibility differ even on the same historical evidence and target.
True, false and redundant reports have separate actual capsules, identical model
support and explicit reliability. Whole-cell analysis alone computes scores.
"""
from pathlib import Path
from . import comparison_runtime
from .artifact_comparisons import checkpoint_call
from .common import digest,distribution
from .series_cases import dose_view
from .cue_cases import counterfactual


def forecast_unit(case,package,purpose_groups,directory,*,resume_only=False):
    del purpose_groups
    declared=case['context_cue'];truth=counterfactual(case,declared['condition'])
    if truth!=declared:raise ValueError('context-cue source future changed')
    evidence=dose_view(case,7,'process_record');rows={};costs=[]
    names=('inferred_cued','population_cued','inferred_uncued','cheap-8.0','cheap-16.0','cheap-32.0')
    for treatment in ('true','false','redundant'):
        bundle={'evidence':evidence,**package['library'],'population_types':package['types']['process_record'],
                'cue':truth['cues'][treatment]}
        result=checkpoint_call(Path(directory)/(treatment+'.json'),bundle,
            lambda:comparison_runtime.execute(bundle,operation='context_cue',budget=800000,
                                               root=Path(directory)/'caps-cue'),resume_only=resume_only)
        predictions=result['prediction']['predictions'] if result['accepted'] else {}
        for prediction in predictions.values():
            distribution(prediction)
            if set(prediction)!=set(evidence['support']):raise ValueError('context-cue prediction changed support')
        rows['process_record|'+treatment]={'predictions':predictions,'validity':{n:result['accepted'] for n in names},
            'model_input_sha256':{n:digest(bundle) for n in names},'evidence_sha256':digest(evidence),'support':evidence['support'],
            'unique_prior_works':len({digest(w) for w in evidence['earlier']})}
        costs.append({'operation':'context_cue','treatment':treatment,'accepted':result['accepted'],
                      'wall_seconds':result['wall_s'],'capsule':result['capsule']})
    return {'unit':case['unit'],'role':case['role'],'truth':truth['target'],'domain':case['private_factors']['domain'],
            'purpose':case['private_factors']['purpose'],'rows':rows,'costs':costs,'condition':truth['condition'],
            'counterfactual_sha256':digest(truth),'assistance':'same past and actual future; true/false/redundant context reports with declared reliability'}
