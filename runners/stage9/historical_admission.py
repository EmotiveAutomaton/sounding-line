"""Combine original-distribution prediction, generation and own-package precision.

DESIGN CHECK: C01/C02/C05/X01/X06/X07; LESSONS 3--5, CONTROLS 6.
NULL: one failed component, wrong package, incomplete cohort or wrong calibration
cannot pass the historical conjunction. ALTERNATIVE: both complete criteria and
their own valid instrument satisfy the finite historical comparison. Pilot scope
never admits; no old registry or current scientific claim is changed here.
"""
import argparse
from pathlib import Path
import time

from .common import REPO, ROOT, Units, closure, digest, file_hash, freeze, read
from .historical_prediction import checked_inputs as prediction_inputs, summarize as prediction_summary
from .historical_generation import checked_inputs as generation_inputs
from .generation_analysis import summarize as generation_summary
from .neural_operations import validate_complete, unit_result, request_task
from .artifact_comparisons import checkpoint_call
from .package_calibration import score_package, checked_calibration
from .queue import inside, verify_sources, writer
from .revision_predictions import sources
from .scoring import score_json
from .training_jobs import cell_identity


def combine(prediction, generation, calibrated, scope):
    if scope not in ('pilot', 'scientific') or type(calibrated) is not bool:
        raise ValueError('explicit historical scope and calibration required')
    if (prediction['scope'] != scope or generation['scope'] != scope or
            prediction['assigned_units'] != (4 if scope == 'pilot' else 96) or
            generation['expected_attempts'] != (2 if scope == 'pilot' else 40) or
            generation['population'] != 'historical_replay' or
            prediction['historical_point_threshold'] != -.05 or prediction['historical_score_floor'] != 1e-9):
        raise ValueError('original complete historical criteria required')
    p, g = prediction['prediction_criterion_pass'], generation['comparison']['criterion_pass']
    if type(p) is not bool or type(g) is not bool:
        raise ValueError('explicit historical criterion decisions required')
    return {'scope': scope, 'prediction_criterion_pass': p, 'generation_criterion_pass': g,
            'instrument_accepted': calibrated, 'historical_criterion_pass': p and g and calibrated,
            'disposition': 'DESCRIPTIVE' if calibrated else 'IMPLEMENTATION INVALID',
            'pilot_eligible_for_admission': False, 'scientific_admission': False,
            'previously_exposed': True, 'confirmation_eligible': False,
            'limitation': 'finite historical task conjunction only; no retrospective Stage 8 admission or transfer to other operations'}


def inputs(prediction, generation, calibration, prediction_cases, generation_cases, scope):
    paths = list(map(inside, (prediction, generation, calibration, prediction_cases, generation_cases)))
    prediction, generation, calibration, prediction_cases, generation_cases = paths
    identities = []; packages = []
    for directory, operation in ((prediction, 'historical_prediction'), (generation, 'broad_historical')):
        identity = read(directory / 'IDENTITY.json'); done = validate_complete(directory, identity)
        if identity['operation'] != operation or identity['scope'] != scope or done.get('execution_complete') is not True:
            raise ValueError('complete original historical neural operations required')
        identities.append(identity); packages.append(read(directory / 'PACKAGE.json'))
    pi, gi = identities
    for field in ('family', 'package_kind', 'adapter_sha256', 'training_complete_sha256', 'precision'):
        if pi[field] != gi[field]:
            raise ValueError('historical prediction and generation package identities differ')
    if score_package(packages[0]) != score_package(packages[1]):
        raise ValueError('historical scoring packages differ')
    pc, pr, ps = prediction_inputs(prediction_cases, scope)
    gc, gr, gs, gp = generation_inputs(generation_cases, scope)
    if (pi['cases_complete_sha256'] != ps or gi['cases_complete_sha256'] != gs or
            pi['role'] != pr or gi['role'] != gr or pi['units'] != [c['unit'] for c in pc] or gi['units'] != [c['unit'] for c in gc]):
        raise ValueError('historical source cohorts differ')
    pu, gu = Units(prediction, pi), Units(generation, gi)
    # The original completed execution retains every call and source-case identity.
    for cases, units, operation, directory, package in (
            (pc, pu, 'historical_prediction', prediction, packages[0]),
            (gc, gu, 'broad_historical', generation, packages[1])):
        if len(units.all()) != len(cases):
            raise ValueError('historical units missing or repeated')
        for case in cases:
            row = units.get(case['unit'])
            if row is None or row['case_sha256'] != digest(case) or row['operation'] != operation:
                raise ValueError('historical prediction/generation unit changed')
            def call(evidence, arguments, index):
                path = directory / 'calls' / case['unit'][:16] / ('call-' + digest(index)[:16] + '.json')
                return checkpoint_call(path, {'evidence': evidence, 'task': request_task(evidence, arguments, package)},
                                       None, resume_only=True)
            if digest(unit_result(case, operation, call)) != digest(row):
                raise ValueError('historical unit does not reconstruct from complete saved calls')
    p = prediction_summary(pc, [pu.get(c['unit'])['result'] for c in pc], scope)
    g = generation_summary([c['source_worlds'][0] for c in gc], [gu.get(c['unit'])['result']['call'] for c in gc],
                           gp['reference_scores'], population='historical_replay', scope=scope)
    if score_json(p) != read(prediction / 'HISTORICAL_PREDICTION.json') or score_json(g) != read(generation / 'GENERATION.json'):
        raise ValueError('historical full profiles do not reconstruct')
    ci, cd = read(calibration / 'IDENTITY.json'), read(calibration / 'COMPLETE.json')
    if (ci['operation'] != 'actual-package-calibration-consumer-v1' or ci['scope'] != scope or
            ci['package'] != packages[0] or ci['target_complete_sha256'] != file_hash(prediction / 'COMPLETE.json') or
            inside(ci['target']) != prediction or cd.get('execution_complete') is not True or
            cd['cell_identity'] != ci['cell_identity'] or
            cd['identity_sha256'] != digest(ci) or closure([REPO / path for path in cd['outputs']['files']]) != cd['outputs']):
        raise ValueError('historical comparison requires its own calibration consumer')
    actual_calibration = inside(ci['calibration'])
    decision = checked_calibration(actual_calibration, packages[0])
    if (file_hash(actual_calibration / 'COMPLETE.json') != ci['calibration_complete_sha256'] or
            decision != read(calibration / 'DECISION.json') or
            decision['instrument_accepted'] != cd['instrument_accepted']):
        raise ValueError('historical calibration decision does not reconstruct')
    decision = decision['instrument_accepted']
    return p, g, decision, {name: {'path': str(path), 'complete_sha256': file_hash(path / 'COMPLETE.json')}
                           for name, path in zip(('prediction', 'generation', 'calibration', 'prediction_cases', 'generation_cases'), paths)}


def run(directory, prediction, generation, calibration, prediction_cases, generation_cases, scope):
    started = time.monotonic(); directory = inside(directory)
    prefix = 'historical-admission-pilots' if scope == 'pilot' else 'scientific-historical-admission'
    if scope not in ('pilot', 'scientific') or not directory.is_relative_to(ROOT / 'private' / prefix):
        raise ValueError('historical admission output scope differs')
    p, g, calibrated, provenance = inputs(prediction, generation, calibration, prediction_cases, generation_cases, scope)
    source = sources(); identity = {'cell_identity': cell_identity(), 'operation': 'historical-admission-comparison-v1',
                                   'scope': scope, 'source': source, 'inputs': provenance}
    with writer(directory):
        Units(directory, identity)
        if (directory / 'COMPLETE.json').exists():
            done = read(directory / 'COMPLETE.json')
            if done['identity_sha256'] != digest(identity) or closure([REPO / path for path in done['outputs']['files']]) != done['outputs']:
                raise ValueError('completed historical comparison changed')
            return done
        freeze(directory / 'COMPARISON.json', combine(p, g, calibrated, scope)); verify_sources(source)
        done = {'cell_identity': identity['cell_identity'], 'identity_sha256': digest(identity), 'execution_complete': True,
                'wall_seconds': time.monotonic() - started, 'scientific_admission': False,
                'outputs': closure([directory / 'IDENTITY.json', directory / 'COMPARISON.json'])}
        freeze(directory / 'COMPLETE.json', done); return done


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    for name in ('output', 'prediction', 'generation', 'calibration', 'prediction-cases', 'generation-cases'):
        parser.add_argument('--' + name, type=Path, required=True)
    parser.add_argument('--scope', choices=('pilot', 'scientific'), required=True)
    a = parser.parse_args(); run(a.output, a.prediction, a.generation, a.calibration, a.prediction_cases, a.generation_cases, a.scope)
