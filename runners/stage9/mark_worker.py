"""Run artifact-based comparator packages inside the restricted interpreter.

DESIGN CHECK: M01/M02/X02; LESSONS 3--5. NULL: incomplete evidence/parameters,
budget exhaustion or unsupported routes invalidate execution. ALTERNATIVE: all
four comparator routes emit complete distributions from the same permitted view.
Numerical program execution is visible assistance, never unaided neural competence.
"""
import json
import math
import time
import traceback

from .base import loaded_sources, probe, save
from .choice_features import cheap_adaptation, predict
from .erased_inference import infer
from .program_inference import Budget, identity
from .program_proposals import propose


def extended_json(value):
    # Same explicit extended-real record convention as evaluator scoring. A zero
    # candidate likelihood is retained, even when another candidate remains valid.
    if isinstance(value, float) and not math.isfinite(value):
        if math.isnan(value):
            raise ValueError('NaN inference output')
        return {'extended_real': 'positive_infinity' if value > 0 else 'negative_infinity'}
    if isinstance(value, dict):
        return {k: extended_json(v) for k, v in value.items()}
    if isinstance(value, (tuple, list)):
        return [extended_json(v) for v in value]
    return value


def main():
    started = time.monotonic()
    try:
        with open('task.json', encoding='utf-8') as stream:
            task = json.load(stream)
        if task.get('probe'):
            save('receipt', probe(task))
            return 0
        with open('evidence.json', encoding='utf-8') as stream:
            bundle = json.load(stream)
        if set(bundle) != {'evidence', 'candidates', 'prior', 'shared_groups', 'population', 'population_types'}:
            raise ValueError('undeclared comparator evidence')
        if task['information_sha256'] != identity(bundle):
            raise ValueError('comparator information identity mismatch')
        if type(task['budget']) is not int or not 1 <= task['budget'] <= 2000000:
            raise ValueError('evaluation budget outside capsule envelope')
        budget = Budget(task['budget'])
        operation = task['operation']
        if operation in ('population', 'cheap_individual'):
            if bundle['population']['individual']:
                raise ValueError('population comparator cannot silently use maker history features')
            budget.charge()
            offsets = (cheap_adaptation(bundle['evidence'], bundle['population_types'], task['adaptation_strength'])
                       if operation == 'cheap_individual' else None)
            result = {'prediction': predict(bundle['evidence'], bundle['population'], offsets),
                      'evaluations_used': budget.used}
        elif operation in ('program_mixture', 'differentiated_maker'):
            result = infer(bundle['evidence'], bundle['candidates'], bundle['prior'], budget,
                           exact_limit=task['exact_limit'], permutations=task['permutations'], seed=task['seed'],
                           shared_groups=bundle['shared_groups'] if operation == 'differentiated_maker' else None)
            if operation == 'differentiated_maker' and bundle['shared_groups'] is None:
                raise ValueError('differentiated route requires declared persistent/per-work factorization')
        elif operation == 'numerical_proposals':
            result = propose(bundle['evidence'], list(bundle['candidates'].values()), budget,
                             maximum=task['maximum_candidates'], expand=task['expand'])
        else:
            raise ValueError('unknown artifact comparator operation')
        save('prediction', extended_json({**result, 'valid': True, 'information_sha256': task['information_sha256'],
                            'operation': operation, 'assistance': 'declared numeric model execution'}))
        save('receipt', {'valid': True, 'wall_seconds': time.monotonic()-started, 'loaded_sources': loaded_sources()})
        return 0
    except Exception:
        save('error', {'valid': False, 'traceback': traceback.format_exc()})
        return 1
