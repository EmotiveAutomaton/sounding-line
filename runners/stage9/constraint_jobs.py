"""Actual bounded-creation matrix with cheap, population and fitted-maker rivals.

DESIGN CHECK: M06/X01/X02/X05/X06/X08/X11; LESSONS 3--5, CONTROLS 6--7.
NULL: identical forecasts give zero paired gain; hidden target mutation cannot alter
reader evidence. ALTERNATIVE: realized freedom, stopping pressure and artifact loss
can affect prediction on the same separate target. Baselines and fitted programs
receive the same bounded earlier work. No failed component or short/stopped work
is silently omitted. Development selects rivals; scientific admission is separate.
"""
from pathlib import Path

from . import baseline_matrix_runtime, comparison_runtime
from .artifact_comparisons import checkpoint_call
from .common import digest, distribution
from .constraint_cases import construct


def forecast_unit(case, package, purpose_groups, directory, *, resume_only=False):
    del purpose_groups
    cf = construct(case)
    if cf != case['constraint_creation']:
        raise ValueError('bounded creation source or separate future changed')
    directory = Path(directory); rows, costs = {}, []
    for view in ('artifact','process_record'):
        queries = {k:v for k,v in cf['views'].items() if v['view'] == view}
        base_input = {'evidences':queries, 'models':package['models'][view], 'population_types':package['types'][view]}
        baseline = checkpoint_call(directory/(view+'-baseline.json'),base_input,
            lambda:baseline_matrix_runtime.execute(base_input,root=directory/'caps-baseline'),resume_only=resume_only)
        costs.append({'operation':'baselines','view':view,'accepted':baseline['accepted'],'wall_seconds':baseline['wall_s'],'capsule':baseline['capsule']})
        bundle = {'evidences':queries,'maximum_actions':cf['maximum_actions'],**package['library']}
        result = checkpoint_call(directory/(view+'-maker.json'),bundle,
            lambda:comparison_runtime.execute(bundle,operation='bounded_creation',budget=800000,root=directory/'caps-maker'),resume_only=resume_only)
        costs.append({'operation':'bounded_creation','view':view,'accepted':result['accepted'],'wall_seconds':result['wall_s'],'capsule':result['capsule']})
        for name, query in queries.items():
            predictions, validity, hashes = {}, {}, {}
            for model in package['models'][view]:
                for route in ('population','brief','cheap-8.0','cheap-16.0','cheap-32.0'):
                    key = model+'|'+route; validity[key] = baseline['accepted']; hashes[key] = digest(base_input)
                    if baseline['accepted']: predictions[key] = baseline['prediction']['predictions'][name][key]
            for key in ('program_prior','program_mixture','differentiated_maker'):
                validity[key] = result['accepted']; hashes[key] = digest(bundle)
                if result['accepted']:
                    output = result['prediction']['queries'][name]
                    validity[key] = output['exact_within_declared_model'] is True
                    if validity[key]: predictions[key] = output['predictions'][key]
            for p in predictions.values():
                distribution(p)
                if set(p) != set(query['support']): raise ValueError('bounded creation forecast support changed')
            rows[name] = {'predictions':predictions,'validity':validity,'model_input_sha256':hashes,
                'evidence_sha256':digest(query),'support':query['support'],'unique_prior_works':1,
                'maximum_actions':cf['maximum_actions'],'exact_within_declared_model':result['accepted']}
    return {'unit':case['unit'],'role':case['role'],'truth':cf['target'],
        'domain':case['private_factors']['domain'],'purpose':case['private_factors']['purpose'],
        'rows':rows,'costs':costs,'source_template_sha256':cf['source_template_sha256'],
        'creation_sha256':digest(cf),'assistance':'bounded earlier-work observation; same separate target; fitted approximate program'}
