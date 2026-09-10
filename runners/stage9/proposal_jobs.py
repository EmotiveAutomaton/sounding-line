"""Actual paired proposal-pool/evaluator grid over permitted maker records.

DESIGN CHECK: M02/X02/X05/X06; LESSONS 3--5. NULL: shared pools and equal
programs cannot acquire a gain from relabeling or copying. ALTERNATIVE: bounded
new programs or stateful evaluation can improve held-out forecasts independently.
All three pools and both evaluators are retained, including invalid components.
The complete fitted catalogue is not true constructor support. The separate
supplied-state/law oracle is an information/execution ceiling, not an isolated
proposal-quality contrast. No LLM proposal or exact global posterior is claimed.
"""
from pathlib import Path

from . import baseline_matrix_runtime, comparison_runtime, mark_runtime
from .artifact_comparisons import checkpoint_call
from .common import digest,distribution
from .series_cases import dose_view

POOLS = (('narrow',16,False),('expanded',16,True),('catalogue',48,False))


def forecast_unit(case,package,purpose_groups,directory,*,resume_only=False):
    directory=Path(directory);query=dose_view(case,7,'process_record')
    library=package['library'];costs=[];predictions={};validity={};quality={}
    base_input={'evidences':{'dose7':query},'models':package['models']['process_record'],
                'population_types':package['types']['process_record']}
    base=checkpoint_call(directory/'baselines.json',base_input,
        lambda:baseline_matrix_runtime.execute(base_input,root=directory/'caps-baseline'),resume_only=resume_only)
    costs.append({'operation':'baselines','accepted':base['accepted'],'wall_seconds':base['wall_s'],'capsule':base['capsule']})
    for model in package['models']['process_record']:
        for route in ('population','brief','cheap-8.0','cheap-16.0','cheap-32.0'):
            key=model+'|'+route;validity[key]=base['accepted']
            if base['accepted']:predictions[key]=base['prediction']['predictions']['dose7'][key]
    proposal_input={'evidence':query,**library,'population':next(iter(package['models']['process_record'].values())),
                    'population_types':package['types']['process_record']}
    for name,width,expand in POOLS:
        setting={'bundle':proposal_input,'maximum_candidates':width,'expand':expand,'budget':200000}
        proposed=checkpoint_call(directory/(name+'-proposals.json'),setting,
            lambda:mark_runtime.execute(proposal_input,'numerical_proposals',maximum_candidates=width,
                                         expand=expand,budget=200000,root=directory/'caps-proposal'),resume_only=resume_only)
        costs.append({'operation':'proposal-'+name,'accepted':proposed['accepted'],'wall_seconds':proposed['wall_s'],'capsule':proposed['capsule']})
        for evaluator in ('stateful','bag'):
            key=name+'|'+evaluator;validity[key]=False
            if not proposed['accepted']:
                quality[key]={'accepted':False,'reason':'proposal operation invalid'}
                continue
            pool=proposed['prediction']
            bundle={'evidence':query,'candidates':pool['candidates'],'prior':pool['prior'],'evaluator':evaluator}
            result=checkpoint_call(directory/(name+'-'+evaluator+'.json'),bundle,
                lambda:comparison_runtime.execute(bundle,operation='proposal_evaluation',budget=800000,
                                                   root=directory/'caps-evaluation'),resume_only=resume_only)
            costs.append({'operation':key,'accepted':result['accepted'],'wall_seconds':result['wall_s'],'capsule':result['capsule']})
            validity[key]=result['accepted']
            quality[key]={'accepted':result['accepted'],'pool_sha256':digest({'candidates':pool['candidates'],'prior':pool['prior']}),
                          'candidate_count':pool['selected_candidates'],'proposal_density_known':False,
                          'full_fitted_catalogue':pool['fixed_complete_catalogue'],'exact_global_posterior':False}
            if result['accepted']:
                if result['prediction']['pool_sha256']!=quality[key]['pool_sha256'] or result['prediction']['evidence_sha256']!=digest(query):
                    raise ValueError('evaluators did not receive the same pool and evidence')
                predictions[key]=result['prediction']['forecast']['prediction']
    # Evaluator-owned ceiling only: these values never enter any reader input.
    if set(case['oracle'])-set(query['support']):raise ValueError('oracle support omitted from common query')
    predictions['supplied_state_law_ceiling']={a:case['oracle'].get(a,0.) for a in query['support']}
    validity['supplied_state_law_ceiling']=True
    quality['supplied_state_law_ceiling']={'assistance':'actual constructor state and law; cannot isolate proposal coverage',
                                         'fitted_catalogue_contains_true_constructor':False}
    for p in predictions.values():
        distribution(p)
        if set(p)!=set(query['support']):raise ValueError('proposal forecast support differs')
    return {'unit':case['unit'],'role':case['role'],'truth':case['target'],'domain':case['private_factors']['domain'],
        'purpose':case['private_factors']['purpose'],'costs':costs,
        'rows':{'process_record|dose7':{'predictions':predictions,'validity':validity,'quality':quality,
          'evidence_sha256':digest(query),'support':query['support'],'unique_prior_works':len({digest(w) for w in query['earlier']})}},
        'assistance':'numerical heuristic proposals and fixed evaluators; privileged ceiling separate'}
