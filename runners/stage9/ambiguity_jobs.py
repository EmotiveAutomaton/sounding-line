"""Three real numerical calls for six separately targeted ambiguity questions.

DESIGN CHECK: M05/X02/X05/X08; LESSONS 3--5, CONTROLS 6--7.
NULL: a later observation cannot enter a forecast of itself; hidden historical
truth cannot enter the artifact arm. ALTERNATIVE: uncertainty over offered histories
can aid prediction and narrow after observation. Invalid calls retain their units
and invalidate their required comparisons. History and future have distinct truths;
the explicit process record is a privileged diagnostic, never artifact recovery.
"""
import copy
from pathlib import Path
from . import comparison_runtime
from .artifact_comparisons import checkpoint_call
from .ambiguity_cases import construct
from .common import digest,distribution

QUESTIONS=('history_artifact','history_after','history_record','future_old','future_changed','future_record')


def public_queries(case):
    a=case['ambiguity'];artifact=copy.deepcopy(a['artifact'])
    record=copy.deepcopy(artifact);record['view']='process_record'
    record['current'].update(events=copy.deepcopy(a['offered_histories'][a['true_history']]),observed_stop=None)
    target=a['outcomes']['changed']['target']
    observed={'action':target,'outcome':'stop' if target=='stop' else 'done'}
    return {'before':{'evidence':artifact,'observed_future':None},
            'after':{'evidence':copy.deepcopy(artifact),'observed_future':observed},
            'record':{'evidence':record,'observed_future':None}}


def targets(case):
    a=case['ambiguity']
    return {q:(a['true_history'] if q.startswith('history_') else
               a['outcomes']['old' if q=='future_old' else 'changed']['target']) for q in QUESTIONS}


def forecast_unit(case,package,purpose_groups,directory,*,resume_only=False):
    if construct(case)!=case['ambiguity']:raise ValueError('prepared ambiguity history or future changed')
    directory=Path(directory);a=case['ambiguity'];calls={};costs=[];inputs={}
    for name,query in public_queries(case).items():
        bundle={**query,'histories':a['offered_histories'],
                'candidates':package['library']['candidates'],'prior':package['library']['prior']}
        inputs[name]=digest(bundle)
        result=checkpoint_call(directory/(name+'.json'),bundle,
            lambda:comparison_runtime.execute(bundle,operation='offered_history',budget=800000,
                                              root=directory/'caps-ambiguity'),resume_only=resume_only)
        calls[name]=result
        costs.append({'operation':name,'accepted':result['accepted'],'wall_seconds':result['wall_s'],'capsule':result['capsule']})
    mapping={'history_artifact':('before',None),'history_after':('after',None),'history_record':('record',None),
             'future_old':('before','old'),'future_changed':('before','changed'),'future_record':('record','changed')}
    questions={};truth=targets(case)
    for q,(call,condition) in mapping.items():
        result=calls[call];keys=('inferred','uniform','committed') if condition is None else ('inferred','population','committed')
        predictions={}
        if result['accepted']:
            predictions=result['prediction']['history_predictions'] if condition is None else result['prediction']['future_predictions'][condition]
        support=sorted(a['offered_histories'] if condition is None else a['artifact']['support'])
        if set(predictions)!=(set(keys) if result['accepted'] else set()):raise ValueError('ambiguity forecast grid incomplete')
        for p in predictions.values():
            distribution(p)
            if set(p)!=set(support):raise ValueError('ambiguity forecast support changed')
        questions[q]={'truth':truth[q],'support':support,'predictions':predictions,
            'validity':{k:result['accepted'] for k in keys},'evidence_sha256':digest(public_queries(case)[call]),
            'model_input_sha256':inputs[call],'unique_prior_works':0,'privileged_record':call=='record'}
    return {'unit':case['unit'],'role':case['role'],'questions':questions,'costs':costs,
            'domain':case['private_factors']['domain'],'purpose':case['private_factors']['purpose'],
            'case_sha256':digest(case),'source_template_sha256':a['content_sha256'],
            'scope':'offered complete finite histories; historical calibration and prospective targets scored separately'}
