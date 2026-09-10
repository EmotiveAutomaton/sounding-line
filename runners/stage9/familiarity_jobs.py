"""Complete familiarity predictions with separate recognition and future truths.

DESIGN CHECK: T02/X01/X02/X05/X06/X08/X11; LESSONS 3--5, CONTROLS 6--7.
NULL: hidden truth never alters permitted input; invalid calls cannot become valid
prior predictions. ALTERNATIVE: recognition, raw surprise and future gain can differ.
Four real calls per source unit; all conditions retained. Recognition comparisons
must balance same/different conditions inside each independent source unit.
"""
from pathlib import Path
from . import baseline_matrix_runtime, comparison_runtime
from .artifact_comparisons import checkpoint_call
from .common import digest,distribution
from .familiarity_cases import construct

QUESTIONS=tuple('q'+str(i)+'|'+kind for i in range(8) for kind in ('recognition','future'))
RECOGNITION=('inferred','prior','surface-8.0','surface-16.0','surface-32.0')
FUTURE=('recognition_mixture','assume_same','assume_different','program_prior')


def forecast_unit(case,package,purpose_groups,directory,*,resume_only=False):
    del purpose_groups
    cf=construct(case,case['role'])
    if cf!=case['familiarity']:raise ValueError('familiarity source or future changed')
    directory=Path(directory);questions,metrics,costs={},{},[]
    for view in ('artifact','process_record'):
        queries={q:e for q,e in cf['views'].items() if e['view']==view}
        base_input={'evidences':queries,'models':package['models'][view],'population_types':package['types'][view]}
        baseline=checkpoint_call(directory/(view+'-baseline.json'),base_input,
            lambda:baseline_matrix_runtime.execute(base_input,root=directory/'caps-baseline'),resume_only=resume_only)
        bundle={'evidences':queries,'maximum_actions':cf['maximum_actions'],**package['library'],
                'same_prior':.5,'population_types':package['types'][view]}
        result=checkpoint_call(directory/(view+'-maker.json'),bundle,
            lambda:comparison_runtime.execute(bundle,operation='maker_familiarity',budget=800000,root=directory/'caps-maker'),resume_only=resume_only)
        for operation,call in (('baselines',baseline),('maker_familiarity',result)):
            costs.append({'operation':operation,'view':view,'accepted':call['accepted'],'wall_seconds':call['wall_s'],'capsule':call['capsule']})
        for name,evidence in queries.items():
            metadata=cf['queries'][name];out=result['prediction']['queries'][name] if result['accepted'] else None
            for kind in ('recognition','future'):
                keys=RECOGNITION if kind=='recognition' else FUTURE
                predictions=dict(out['recognition_routes' if kind=='recognition' else 'predictions']) if out else {}
                validity={k:result['accepted'] and out['exact_within_declared_model'] for k in keys}
                hashes={k:digest(bundle) for k in keys}
                if kind=='future':
                    for model in package['models'][view]:
                        for route in ('population','brief','cheap-8.0','cheap-16.0','cheap-32.0'):
                            key=model+'|'+route;validity[key]=baseline['accepted'];hashes[key]=digest(base_input)
                            if baseline['accepted']:predictions[key]=baseline['prediction']['predictions'][name][key]
                offered=['same','different'] if kind=='recognition' else evidence['support']
                for p in predictions.values():
                    distribution(p)
                    if set(p)!=set(offered):raise ValueError('familiarity forecast support changed')
                questions[name+'|'+kind]={'truth':metadata['recognition_target' if kind=='recognition' else 'future_target'],
                    'support':offered,'predictions':predictions,'validity':validity,'model_input_sha256':hashes,
                    'evidence_sha256':digest(evidence),'unique_prior_works':cf['archive_work_count'],
                    'view':view,'condition':metadata['condition'],'kind':kind}
            metrics[name]={'valid':result['accepted'],'view':view,'condition':metadata['condition'],
                'values':{k:out[k] for k in ('raw_observation_surprise_nats','same_archive_observation_surprise_nats',
                    'population_observation_surprise_nats')} if out else {}}
    return {'unit':case['unit'],'role':case['role'],'questions':questions,'metrics':metrics,'costs':costs,
        'domain':case['private_factors']['domain'],'purpose':case['private_factors']['purpose'],
        'case_sha256':digest(case),'source_template_sha256':cf['source_template_sha256'],
        'scope':'balanced conditional expectedness; actual identity labels; separate prospective targets; entry selection still separate'}
