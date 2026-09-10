"""Matched complete operative information for direct prediction and execution.

DESIGN CHECK: I06/X02/X06/X07/X08; LESSONS 3--5, CONTROLS 6.
NULL: equal forecasts give zero gain; missing code/state/support, changed copied
semantics or leaked future invalidates the comparison. ALTERNATIVE: explicit
execution can improve prospective consequences even with the entire same law and
state supplied to the neural reader. Code omission is a separate information
ablation, not matched execution. Every assigned prediction survives analysis;
invalid components invalidate its comparison. All arms are privileged diagnostics,
never ordinary artifact inference or a pure model-size comparison.
"""
import ast
import json
import math

from .common import REPO, digest, distribution, file_hash
from .construction import Replay
from .kernel import action_id, probabilities
from .kernel_preparation import supplied_program
from .scoring import log_score, paired_extended


def operative_source():
    path = REPO/'runners/stage9/kernel.py'
    tree = ast.parse(path.read_text(encoding='utf-8'))
    for node in ast.walk(tree):
        body = getattr(node, 'body', None)
        if (isinstance(body, list) and body and isinstance(body[0], ast.Expr)
                and isinstance(body[0].value, ast.Constant) and isinstance(body[0].value.value, str)):
            body.pop(0)
    return ast.unparse(tree), file_hash(path)


def inputs(case):
    """Render only the state at the prospective cut; do not read target/oracle."""
    world = case['source_worlds'][0]
    program = supplied_program(Replay(world, world['trajectory']['steps'][:case['requested_boundary']]))
    support = sorted({'stop'} | {action_id(a) for a in program['pending']})
    bundle = {'programs': [program], 'weights': [1.], 'support': support}
    code, source_sha = operative_source()
    payload = json.dumps(bundle, ensure_ascii=False, separators=(',', ':'))
    options = {key: key for key in support}
    full = {'prefix': 'Predict the next action using this complete supplied program and its executable semantics.\n'
            + code + '\nINPUT\n' + payload + '\nNEXT ACTION\n', 'options': options}
    partial = {'prefix': 'Predict the next action using these supplied numeric program parameters and state.\n'
               + 'INPUT\n' + payload + '\nNEXT ACTION\n', 'options': dict(options)}
    return {'bundle': bundle, 'full': full, 'parameters_only': partial,
            'kernel_source_sha256': source_sha, 'rendered_source_sha256': digest(code)}


def evaluate_unit(case, call):
    supplied = inputs(case)
    bundle = supplied['bundle']
    expected = probabilities(bundle['programs'][0])
    oracle = case['oracle']
    distribution(oracle)
    if (set(oracle) - set(bundle['support']) or case['target'] not in bundle['support']
            or max(abs(expected.get(k, 0.) - oracle.get(k, 0.)) for k in bundle['support']) > 1e-12):
        raise ValueError('supplied kernel and actual constructor consequences differ')
    executed = call(bundle, {'operation': 'execute_program_mixture'}, 'explicit-kernel')
    if (not executed['accepted']
            or executed['copied_sources']['files'].get('reader/kernel.py') != supplied['kernel_source_sha256']
            or executed['prediction']['probs'] != {k: expected.get(k, 0.) for k in bundle['support']}):
        raise ValueError('actual kernel execution does not match supplied operative semantics')
    calls = {'explicit': executed}
    for name in ('full', 'parameters_only'):
        calls[name] = call(supplied[name], {'operation': 'choice'}, name)
        if calls[name]['accepted']:
            distribution(calls[name]['prediction']['probs'])
            if set(calls[name]['prediction']['probs']) != set(bundle['support']):
                raise ValueError('direct reader omitted a supplied action')
    return {'calls': calls, 'target': case['target'], 'oracle': oracle,
            'information_sha256': digest(bundle), 'kernel_source_sha256': supplied['kernel_source_sha256'],
            'rendered_source_sha256': supplied['rendered_source_sha256'],
            'direct_inputs': {k: digest(supplied[k]) for k in ('full', 'parameters_only')},
            'scope': 'supplied complete state/law; full source is matched to the actual executor; '
                     'code-omitted arm removes procedural information; no ordinary maker inference'}


def profile(rows, draws=4000):
    if not rows or len({r['unit'] for r in rows}) != len(rows):
        raise ValueError('complete distinct assigned supplied-information units required')
    # Same operative question is one bootstrap unit even if source aliases differ.
    comparisons = {}
    for group in ('all', *sorted({r['domain'] for r in rows})):
        selected = [r for r in rows if group == 'all' or r['domain'] == group]
        estimates = {}
        for name, left, right in (('execution_vs_direct', 'explicit', 'full'),
                                  ('operative_code_added', 'full', 'parameters_only'),
                                  ('direct_vs_uniform', 'full', 'uniform')):
            scored, invalid = [], []
            for row in selected:
                result = row['result']
                if set(result['calls']) != {'explicit', 'full', 'parameters_only'}:
                    raise ValueError('supplied-information grid is incomplete')
                calls = result['calls']
                if any(not c['accepted'] for c in calls.values()):
                    invalid.append(row['unit'])
                    continue
                forecasts = {k: c['prediction']['probs'] for k, c in calls.items()}
                support = set(forecasts['explicit'])
                if any(set(p) != support for p in forecasts.values()):
                    raise ValueError('supplied-information supports differ')
                forecasts['uniform'] = {k: 1/len(support) for k in support}
                a, b = (log_score(forecasts[k], result['target']) for k in (left, right))
                scored.append({'unit': result['information_sha256'],
                               'difference': None if a == b == -math.inf else a-b})
            estimates[name] = ({'disposition': 'IMPLEMENTATION INVALID', 'invalid_units': invalid,
                                'assigned': len(selected), 'excluded': 0} if invalid else
                               {'estimate': paired_extended(scored, draws=draws),
                                'assigned': len(selected), 'excluded': 0, 'disposition': 'DESCRIPTIVE'})
        comparisons[group] = estimates
    return {'comparisons': comparisons, 'scientific_admission': False,
            'scope': 'prospective supplied-information diagnostic; calibration and final controls required; '
                     'source-code ablation is an information removal, not evidence of a specific internal mechanism'}
