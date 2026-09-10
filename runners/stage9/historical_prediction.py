"""Original exposed E03 prediction task, kept apart from Stage 9 choice admission.

DESIGN CHECK: C01/C02/C05/X01/X06/X11; LESSONS 3--5, CONTROLS 6.
NULL: changed historical sources, incomplete calls or failed calibration cannot
admit a package. ALTERNATIVE: identical next-action forecasts give zero paired gap.
The original action-only normalization and clipped historical score remain named;
proper unfloored scores are separate. No old registry or confirmation is updated.
"""
import argparse
from collections import Counter
import json
import math
from pathlib import Path
import time

from runners.stage7.reader.contracts import normalize
from runners.stage7.scoring.prospective import _ls as historical_log_score
from runners.stage8 import engines as original
from runners.stage8.reader import logfmt
from .common import REPO, ROOT, closure, digest, distribution, file_hash, freeze, read
from .queue import inside, verify_sources, writer
from .revision_predictions import sources
from .scoring import log_score, paired_extended
from .training_jobs import cell_identity

ARCHIVE = REPO / 'results/phase_2_4_stage_8'
PINS = {'E03/cases.jsonl': '6281de94b92b60b27f23a17ed44d4ad3b09f8e665d6398abaaa9907d661acb20',
        'E03/metrics.json': '684e3a21d2869dd4b02ed61a7a3378d89ae1ef42e2bf1c512c799d4ac9792d99',
        'DOM_FROZEN.json': '81bd25dfde522b4d2a186ccdad57a862914f4b42b184b5717e60eda6a9dda077'}


def archived_cases():
    for name, sha in PINS.items():
        if file_hash(ARCHIVE / name) != sha:
            raise ValueError('historical prediction source changed')
    rows = [json.loads(line) for line in (ARCHIVE / 'E03/cases.jsonl').read_text(encoding='utf8').splitlines()]
    baseline = [r for r in rows if r['arm'] == 'DOM']
    lineages = {r['lineage_id'] for r in baseline}
    if len(rows) != 576 or len(baseline) != len(lineages) or len(lineages) != 96:
        raise ValueError('complete original prediction roster required')
    for family in ('qwen', 'smollm'):
        own = [r['lineage_id'] for r in rows if r['arm'] == 'FM' and r['model_id'] == 'adapter:fm_' + family]
        if len(own) != 96 or set(own) != lineages:
            raise ValueError('original prediction reader cohort differs')
    parameters = read(ARCHIVE / 'DOM_FROZEN.json'); cases = []; paths = [ARCHIVE / name for name in PINS]
    for row in baseline:
        lid = row['lineage_id']; domain = row['factors']['domain']
        family = 'POP' if lid.startswith('POP|') else 'PU'
        world = (original.POP.sample_world(lid, finish=True) if family == 'POP' else
                 original.PU.make_pu_world(lid, domain, maker_free=True))
        truth_path = ARCHIVE / 'oracle/E03' / (lid.replace('|', '-') + '.json')
        pred_path = ARCHIVE / 'predictions/E03' / ('DOM_x_' + lid.replace('|', '-') + '.json')
        truth = read(truth_path); paths.extend((truth_path, pred_path))
        condition = original.build_condition(original.C.ALL['E03']['condition'], original._opaque(lid), 'E03')
        evidence = original.evidence_for(world, condition)
        probabilities = normalize(original.B.dom(evidence, parameters)['next_action'])
        if (world['degenerate'] or world['cut'] != truth['cut'] or world['state']['names'] != truth['state_names'] or
                world['hidden']['next_action'] != truth['hidden']['next_action'] or row['truth'] != truth['hidden']['next_action'] or
                original.evidence_sha(evidence) != row['evidence_sha'] or row['evidence_sha'] != truth['evidence_sha'] or
                probabilities != read(pred_path)['targets']['next_action']):
            raise ValueError('historical world, target, evidence or normalized baseline differs')
        cases.append({'unit': digest({'historical_prediction_lineage': lid}), 'lineage': lid,
                      'population': family, 'source_worlds': [world], 'evidence': evidence,
                      'target': row['truth'], 'baseline': probabilities})
    if Counter((c['population'], c['source_worlds'][0]['domain']) for c in cases) != {
            (f, d): n for f, n in (('POP', 23), ('PU', 25)) for d in original.POP.DOMAINS}:
        raise ValueError('original conditional allocation changed')
    return cases, closure(paths)


def world_plan(scope):
    if scope not in ('pilot', 'scientific'):
        raise ValueError('undeclared historical prediction scope')
    cases, archive = archived_cases()
    if scope == 'pilot':
        cases = [next(c for c in cases if c['population'] == f and c['source_worlds'][0]['domain'] == d)
                 for f in ('POP', 'PU') for d in original.POP.DOMAINS]
    role = 'pilot' if scope == 'pilot' else 'historical_replay'
    return {'cases': [dict(c, role=role) for c in cases], 'role': role, 'original_archive': archive,
            'original_worlds': 96, 'previously_exposed': True, 'confirmation_eligible': False}


def checked_inputs(directory, scope):
    directory = inside(directory); done = read(directory / 'COMPLETE.json'); identity = read(directory / 'IDENTITY.json')
    if (done.get('accepted') is not True or done.get('construction_only') is not True or
            identity['operation'] != 'historical-prediction-source-v1' or identity['scope'] != scope or
            done['identity_sha256'] != digest(identity) or
            closure([REPO / p for p in done['outputs']['files']]) != done['outputs']):
        raise ValueError('historical prediction preparation identity or outputs differ')
    plan = read(directory / 'WORLD_PLAN.json')
    if digest(plan) != digest(world_plan(scope)):
        raise ValueError('historical prediction source plan changed')
    return plan['cases'], plan['role'], file_hash(directory / 'COMPLETE.json')


def prepare(directory, scope):
    directory = inside(directory)
    prefix = 'historical-prediction-pilots' if scope == 'pilot' else 'scientific-historical-prediction'
    if scope not in ('pilot', 'scientific') or not directory.is_relative_to(ROOT / 'private' / prefix):
        raise ValueError('historical prediction output scope differs')
    started = time.monotonic(); source = sources()
    identity = {'cell_identity': cell_identity(), 'operation': 'historical-prediction-source-v1',
                'scope': scope, 'source': source, 'pins': PINS}
    with writer(directory):
        freeze(directory / 'IDENTITY.json', identity)
        if (directory / 'COMPLETE.json').exists():
            checked_inputs(directory, scope); return read(directory / 'COMPLETE.json')
        plan = world_plan(scope); freeze(directory / 'WORLD_PLAN.json', plan); verify_sources(source)
        done = {'cell_identity': identity['cell_identity'], 'identity_sha256': digest(identity),
                'accepted': True, 'construction_only': True, 'scope': scope, 'role': plan['role'],
                'selected_units': len(plan['cases']), 'original_worlds': 96,
                'previously_exposed': True, 'confirmation_eligible': False, 'scientific_admission': False,
                'wall_seconds': time.monotonic() - started,
                'outputs': closure([directory / 'IDENTITY.json', directory / 'WORLD_PLAN.json'])}
        freeze(directory / 'COMPLETE.json', done); return done


def choice_input(case):
    evidence = case['evidence']; prefix = evidence['process_prefix']; boundary = len(prefix)
    options = {aid: logfmt.event_line(boundary, *aid.split(':')) for aid in evidence['query']['next_action_options']}
    if not options or 'stop' in options or (case['target'] is not None and case['target'] not in options):
        raise ValueError('historical next-action support differs')
    options['stop'] = logfmt.stop_line(boundary)
    return {'prefix': logfmt.compose([], logfmt.header_from_evidence(evidence), logfmt.prefix_lines(prefix)), 'options': options}


def action_forecast(result, option_order):
    """Original FM action-only softmax, followed by original PredictionV1 normalization."""
    if result.get('accepted') is not True:
        return None
    components = result['prediction']['components']
    values = {r['option_id']: r['logprob'] for r in components}
    if (len(values) != len(components) or set(values) != set(option_order) | {'stop'} or
            any(type(v) not in (float, int) or not math.isfinite(v) or v > 0 for v in values.values())):
        raise ValueError('historical complete finite components required')
    maximum = max(values[k] for k in option_order)
    weights = [math.exp(values[k] - maximum) for k in option_order]; total = sum(weights)
    return normalize({key: weight / total for key, weight in zip(option_order, weights)})


def evaluate_unit(case, call):
    evidence = choice_input(case); result = call(evidence, {'operation': 'choice'}, 'historical-next-action')
    forecast = action_forecast(result, case['evidence']['query']['next_action_options'])
    return {'call': result, 'input_sha256': digest(evidence), 'next_action': forecast,
            'target': case['target'], 'scope': 'original action-only conditional prediction; stop scored separately, no altered-context claim'}


def summarize(cases, predictions, scope, draws=4000):
    count = 4 if scope == 'pilot' else 96 if scope == 'scientific' else 0
    if not count or len(cases) != count or len(predictions) != count or len({c['lineage'] for c in cases}) != count:
        raise ValueError('complete historical prediction cohort required')
    allocation = {(f, d): (1 if scope == 'pilot' else n)
                  for f, n in (('POP', 23), ('PU', 25)) for d in original.POP.DOMAINS}
    if Counter((c['population'], c['source_worlds'][0]['domain']) for c in cases) != allocation:
        raise ValueError('complete historical conditional allocation required')
    rows = []
    for case, prediction in zip(cases, predictions):
        if prediction['target'] != case['target']:
            raise ValueError('historical prediction target changed')
        forecast = prediction['next_action']; target = case['target']; baseline = case['baseline']
        valid = prediction['call'].get('accepted') is True and forecast is not None
        left = right = difference = proper = None
        if valid:
            distribution(forecast); distribution(baseline)
            if set(forecast) != set(baseline) or (target is not None and target not in baseline):
                raise ValueError('historical predicted support or target differs')
            if target is not None:
                left, right = historical_log_score(forecast, target), historical_log_score(baseline, target)
                difference = left - right; p, q = log_score(forecast, target), log_score(baseline, target)
                proper = None if p == q == -math.inf else p - q
        rows.append({'unit': case['lineage'], 'domain': case['source_worlds'][0]['domain'], 'population': case['population'],
                     'valid': valid, 'target_observed': target is not None,
                     'difference': difference, 'proper_difference': proper})
    groups = {'all': rows}
    for field in ('domain', 'population'):
        groups.update({field + '|' + name: [r for r in rows if r[field] == name] for name in sorted({r[field] for r in rows})})
    output = {}
    for name, members in groups.items():
        valid = all(r['valid'] for r in members)
        scored = [r for r in members if r['target_observed']]
        gap = paired_extended(scored, draws=draws, seed=9022) if valid and scored else None
        output[name] = {'assigned': len(members), 'invalid': sum(not r['valid'] for r in members),
                        'scored_targets': len(scored), 'unscored_terminal_boundaries': len(members) - len(scored),
                        'historical_clipped': gap,
                        'proper_unfloored': paired_extended(scored, value='proper_difference', draws=draws, seed=9022) if valid and scored else None}
    valid = all(r['valid'] for r in rows); overall = output['all']['historical_clipped']
    return {'scope': scope, 'assigned_units': count, 'groups': output, 'rows': rows,
            'prediction_criterion_pass': bool(valid and overall is not None and overall['mean'] >= -.05),
            'historical_score_floor': 1e-9, 'historical_point_threshold': -.05,
            'bootstrap': 'new deterministic seed 9022; original process-hash-dependent interval not reproduced',
            'terminal_policy': 'original null next-action targets remain assigned and explicitly unscored; every assigned call must be valid',
            'previously_exposed': True, 'confirmation_eligible': False, 'scientific_admission': False,
            'limitation': 'original prediction criterion only; matching generation and calibration still required; pilot never admits'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--scope', choices=('pilot', 'scientific'), required=True)
    args = parser.parse_args(); prepare(args.output, args.scope)
