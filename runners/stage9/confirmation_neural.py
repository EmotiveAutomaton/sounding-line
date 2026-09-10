"""Execute frozen paired prospective choices for all three original training seeds.

DESIGN CHECK: B02/C08/X01/X02/X06/X11/X12; LESSONS 3--5, CONTROLS 6--7.
NULL: equal paired forecasts give zero; missing/duplicated seeds, substituted fits,
different targets/support, failed calls and nonfinite contrasts cannot yield a
finite-only confirmation. ALTERNATIVE: all three checkpoints of one family/recipe
run the frozen evidence views on the same reserved source units. Seeds average
within units, never add independent units. Completed reentry uses saved calls only.
This adapter covers the information contrast within a fitted recipe; comparing
different recipes, generation success, human selections or maker-dose interventions
requires their own execution contracts. No scientific admission follows execution.
"""
import argparse
import math
from pathlib import Path
import time
import uuid

from .artifact_comparisons import audit_execution, checkpoint_call, validate_cases
from .common import REPO, Units, digest, distribution, file_hash, freeze, read
from .confirmation_access import frozen_claim, pointer_path, reservation
from .confirmation_statistics import CONTRACT
from .launch import checked
from .neural_operations import request_task, training_package
from .prospective_choice import choice_input
from .revision_predictions import finish, reentry, sources
from .runtime import execute
from .scoring import log_score, score_json
from .service_owner import resident
from .training_jobs import cell_identity
from .train import BASES

SEEDS = (9001, 9002, 9003)
OPERATIONS = {'artifact_choice', 'process_choice'}


def seed_grid(scope):
    if scope not in ('pilot', 'scientific'):
        raise ValueError('explicit neural execution scope required')
    # None denotes no training-seed claim, not an untrained reader. The actual
    # discarded fit identity remains in the original package and fitting record.
    return (None,) if scope == 'pilot' else SEEDS


def validate_rehearsal_contract(contract, packet):
    """One already registered discarded reader; never synthetic scientific seeds."""
    if (set(contract) != {'adapter', 'resource', 'readers', 'reserve', 'contrast'}
            or contract['adapter'] != 'neural-choice-rehearsal-v1' or contract['resource'] != 'gpu'
            or packet['analysis_contract'] != CONTRACT
            or packet['planning']['discovery']['seeds'] != [None]
            or packet['candidate']['target'] != 'proper_log_score'
            or packet['candidate']['seed_evidence'] != {}
            or set(contract['readers']) != {'None'}
            or set(contract['contrast']) != {'left', 'right'}
            or set(contract['contrast'].values()) != OPERATIONS):
        raise ValueError('discarded neural rehearsal cannot carry a scientific seed claim')
    item = contract['readers']['None']
    if set(item) != {'training', 'forecasts', 'package'} or set(item['forecasts']) != {'left', 'right'}:
        raise ValueError('rehearsal needs its actual fit and both original forecast identities')
    for pointer in (item['training'], item['package'], *item['forecasts'].values()):
        pointer_path(pointer); checked(pointer)
    package = checked(item['package']); training = pointer_path(item['training']).parent
    identity = read(training / 'IDENTITY.json'); family = identity['family']
    _, adapter_sha, fit_sha = training_package(training, family, 'pilot')
    candidates = packet['candidate']['reader_packages']
    if (len(candidates) != 1 or candidates[0]['path'] != item['package']['path']
            or packet['reader_package_content_hashes'] != [digest(package)]
            or fit_sha != item['training']['sha256'] or package['adapter_sha256'] != adapter_sha
            or any(package.get(k) != v for k, v in BASES[family].items())):
        raise ValueError('rehearsal must retain its exact actual discarded checkpoint/package')
    observed = {side: checked(p) for side, p in item['forecasts'].items()}
    for side, own in observed.items():
        expected = (REPO / packet['candidate']['seed_forecasts']['None'][side]['path']).parent
        if (pointer_path(item['forecasts'][side]) != expected / 'IDENTITY.json'
                or own.get('scope') != 'pilot' or own.get('role') != 'pilot'
                or own.get('operation') != contract['contrast'][side] or own.get('package_kind') != 'fitted'
                or own.get('family') != family or own.get('training_complete_sha256') != fit_sha
                or own.get('adapter_sha256') != adapter_sha or read(expected / 'PACKAGE.json') != package):
            raise ValueError('rehearsal forecasts differ from their actual reader or paired views')
    if (not observed['left'].get('units') or observed['left']['units'] != observed['right'].get('units')
            or observed['left']['cases_complete_sha256'] != observed['right'].get('cases_complete_sha256')
            or pointer_path(item['package']).parent not in {pointer_path(p).parent for p in item['forecasts'].values()}):
        raise ValueError('rehearsal pairing or selected package directory differs')
    if any(package.get(k) != v for k, v in {'precision': 'float16', 'device': 'cuda', 'batch_size': 4,
            'max_context': 4096, 'max_support': 128, 'max_new_tokens': 32}.items()):
        raise ValueError('rehearsal must use the actual confirmation service envelope')
    if package.get('generation', {}).get('requested') != {'do_sample': False}:
        raise ValueError('rehearsal must retain greedy service settings')


def validate_reader_contract(contract, packet):
    """Validate already-open fitting/forecast provenance, before reserve access."""
    if (set(contract) != {'adapter', 'resource', 'readers', 'reserve', 'contrast'}
            or contract['adapter'] != 'neural-choice-v1' or contract['resource'] != 'gpu'
            or packet['analysis_contract'] != CONTRACT
            or packet['planning']['discovery']['seeds'] != list(SEEDS)
            or packet['candidate']['target'] != 'proper_log_score'):
        raise ValueError('exact three-seed neural choice confirmation contract required')
    readers, contrast = contract['readers'], contract['contrast']
    if not isinstance(readers, dict) or set(readers) != {str(s) for s in SEEDS}:
        raise ValueError('every original training seed is required exactly once')
    if (not isinstance(contrast, dict) or set(contrast) != {'left', 'right'}
            or set(contrast.values()) != OPERATIONS):
        raise ValueError('paired structured artifact/process choices required')
    candidates = packet['candidate']['reader_packages']
    hashes = packet['reader_package_content_hashes']
    if len(candidates) != 3 or len(hashes) != 3 or len({r['path'] for r in candidates}) != 3:
        raise ValueError('three distinct selected reader packages required')
    selected_packages = {r['path']: sha for r, sha in zip(candidates, hashes)}
    groups, fits, adapters = set(), set(), set()
    for seed in SEEDS:
        item = readers[str(seed)]
        if (not isinstance(item, dict) or set(item) != {'training', 'forecasts', 'package'}
                or not isinstance(item['forecasts'], dict) or set(item['forecasts']) != {'left', 'right'}):
            raise ValueError('each seed needs its actual fit, both forecast identities and package')
        for pointer in (item['training'], item['package'], *item['forecasts'].values()):
            pointer_path(pointer)
        checked(item['training'])
        observed = {side: checked(p) for side, p in item['forecasts'].items()}
        package = checked(item['package'])
        training = pointer_path(item['training']).parent
        identity = read(training / 'IDENTITY.json')
        scientific_input = read(training / 'SCIENTIFIC_INPUT.json')
        if (type(identity.get('seed')) is not int or identity['seed'] != seed
                or selected_packages.get(item['package']['path']) != digest(package)):
            raise ValueError('seed label differs from original discovery fit/package provenance')
        binding = packet['candidate']['seed_evidence'][str(seed)]['forecast_identity']
        if binding['path'] not in {p['path'] for p in item['forecasts'].values()}:
            raise ValueError('original B01 fit binding differs from execution forecasts')
        for side, forecast_identity in observed.items():
            reference = packet['candidate']['seed_forecasts'][str(seed)][side]
            expected = (REPO / reference['path']).parent / 'IDENTITY.json'
            if (pointer_path(item['forecasts'][side]) != expected.resolve()
                    or forecast_identity.get('scope') != 'scientific'
                    or forecast_identity.get('role') != 'discovery'
                    or forecast_identity.get('operation') != contrast[side]
                    or forecast_identity.get('package_kind') != 'fitted'
                    or forecast_identity.get('training_complete_sha256') != item['training']['sha256']):
                raise ValueError('both paired discovery forecasts must retain the exact fitted seed and views')
        if (pointer_path(item['package']).parent not in {pointer_path(p).parent for p in item['forecasts'].values()}
                or observed['left'].get('units') != observed['right'].get('units')
                or not observed['left'].get('units')
                or observed['left'].get('cases_complete_sha256') != observed['right'].get('cases_complete_sha256')):
            raise ValueError('paired discovery source assignment or package directory differs')
        if any(read(pointer_path(p).parent / 'PACKAGE.json') != package for p in item['forecasts'].values()):
            raise ValueError('both discovery views must use the same complete resident package')
        family = identity['family']
        adapter, adapter_sha, fit_sha = training_package(training, family, 'scientific')
        if (fit_sha != item['training']['sha256'] or package.get('adapter_sha256') != adapter_sha
                or any(o.get('family') != family or o.get('adapter_sha256') != adapter_sha for o in observed.values())
                or any(package.get(k) != v for k, v in BASES[family].items())):
            raise ValueError('selected checkpoint differs from the fitted/discovery package')
        if (package.get('precision') != 'float16' or package.get('device') != 'cuda'
                or package.get('batch_size') != 4 or package.get('max_context') != 4096
                or package.get('max_support') != 128 or package.get('max_new_tokens') != 32
                or package.get('generation', {}).get('requested') != {'do_sample': False}):
            raise ValueError('neural confirmation must retain the original service envelope')
        groups.add((family, scientific_input['recipe']))
        fits.add(str(training))
        adapters.add(adapter_sha)
    if len(groups) != 1 or len(fits) != 3 or len(adapters) != 3:
        raise ValueError('one complete recipe/family with three distinct fitted checkpoints required')


def discovery_forecasts(cases, units, operation):
    """Export complete audited neural choice units in the existing B01 row format.

    The producing neural operation audits its actual cached calls before this
    projection and commits the output in its own completion closure. This helper
    never infers a gate, refits, resamples, subsets or scores discovery.
    """
    if (operation not in OPERATIONS or not cases or len(units) != len(cases)
            or len({c['unit'] for c in cases}) != len(cases)
            or len({r['unit'] for r in units}) != len(units)
            or {r['unit'] for r in units} != {c['unit'] for c in cases}):
        raise ValueError('complete assigned prospective-choice source grid required')
    by_unit = {row['unit']: row for row in units}
    result = []
    for case in cases:
        row = by_unit[case['unit']]
        evidence = choice_input(case, operation)
        if (row['case_sha256'] != digest(case) or row['operation'] != operation
                or row['role'] != case['role'] or row['result']['target'] != case['target']
                or row['result']['input_sha256'] != digest(evidence)):
            raise ValueError('discovery projection differs from the original source/operation/target')
        call = row['result']['call']
        if type(call['accepted']) is not bool:
            raise ValueError('actual call validity must be boolean')
        probabilities = call['prediction']['probs'] if call['accepted'] else None
        if call['accepted']:
            distribution(probabilities)
            if set(probabilities) != set(evidence['options']) or case['target'] not in probabilities:
                raise ValueError('discovery forecast omits actual offered support')
        result.append({'unit': case['unit'], 'target': 'next_recorded_event', 'truth': case['target'],
                       'probabilities': probabilities, 'valid': call['accepted']})
    return result


def forecast(case, seed, contrast, call, *, scope='scientific'):
    if seed not in seed_grid(scope) or seed is not None and type(seed) is not int:
        raise ValueError('undeclared confirmation training seed')
    evidences = {side: choice_input(case, operation) for side, operation in contrast.items()}
    if (set(evidences) != {'left', 'right'}
            or evidences['left']['options'] != evidences['right']['options']
            or case['target'] not in evidences['left']['options']):
        raise ValueError('paired confirmation must preserve exact offered strings and target')
    sides = {}
    for side, evidence in evidences.items():
        result = call(evidence, side)
        probabilities = result['prediction']['probs'] if result['accepted'] else None
        if result['accepted']:
            distribution(probabilities)
            if set(probabilities) != set(evidence['options']):
                raise ValueError('neural confirmation omits complete offered support')
        sides[side] = {'valid': result['accepted'], 'probabilities': probabilities,
                       'evidence_sha256': digest(evidence), 'operation': contrast[side], 'call': result}
    return {'unit': case['unit'], 'target': 'next_recorded_event', 'truth': case['target'],
            'seed': seed, 'role': case['role'], 'sides': sides}


def calculation_input(rows, expected, *, scope='scientific'):
    grid = {(unit, seed) for unit in expected for seed in seed_grid(scope)}
    if (not expected or len(expected) != len(set(expected)) or len(rows) != len(grid)
            or {(r['unit'], r['seed']) for r in rows} != grid
            or any(r['seed'] is not None and type(r['seed']) is not int or r['target'] != 'next_recorded_event'
                   or set(r['sides']) != {'left', 'right'} for r in rows)):
        raise ValueError('complete original source-by-training-seed grid required')
    differences, scores, limitations = [], [], []
    for unit in expected:
        own = [r for r in rows if r['unit'] == unit]
        if len({r['truth'] for r in own}) != 1 or len({r['role'] for r in own}) != 1:
            raise ValueError('target or source role differs across training seeds')
        for side in ('left', 'right'):
            if len({r['sides'][side]['evidence_sha256'] for r in own}) != 1:
                raise ValueError('training seeds received different confirmation evidence')
    for row in rows:
        if set(row['sides']) != {'left', 'right'}:
            raise ValueError('neural confirmation omits a paired side')
        if any(side['valid'] is not True for side in row['sides'].values()):
            limitations.append({'unit': row['unit'], 'seed': row['seed'], 'reason': 'required forecast failed; no seed or unit deletion'})
            continue
        a, b = [row['sides'][side]['probabilities'] for side in ('left', 'right')]
        distribution(a); distribution(b)
        if set(a) != set(b) or row['truth'] not in a:
            raise ValueError('paired neural confirmation support or truth differs')
        left, right = log_score(a, row['truth']), log_score(b, row['truth'])
        difference = None if left == right == -math.inf else left - right
        scores.append({'unit': row['unit'], 'seed': row['seed'], 'left_log_score': left,
                       'right_log_score': right, 'difference': difference})
        if difference is None or not math.isfinite(difference):
            limitations.append({'unit': row['unit'], 'seed': row['seed'], 'reason': 'nonfinite paired contrast; no finite-only subset'})
        else:
            differences.append({'unit': row['unit'], 'target': row['target'], 'seed': row['seed'], 'difference': difference})
    return score_json({'calculation_status': 'NOT_RUN' if limitations else 'READY',
        'assigned_units': len(expected), 'assigned_targets': {u: ['next_recorded_event'] for u in expected},
        'limitations': limitations, 'paired_rows': None if limitations else differences,
        'all_available_scores': scores, 'excluded_units': 0, 'excluded_targets': 0,
        'excluded_seeds': 0, 'scientific_confirmation': False})


def run(directory, freeze_directory, manifest_path, queue_path, claim_id, scope):
    started, cpu = time.monotonic(), time.process_time()
    frozen = frozen_claim(freeze_directory, manifest_path, queue_path, claim_id, scope)
    seeds = seed_grid(scope); role = 'pilot' if scope == 'pilot' else 'reserve'
    adapter_kind = 'neural-choice-rehearsal-v1' if scope == 'pilot' else 'neural-choice-v1'
    if frozen['contract']['adapter'] != adapter_kind:
        raise ValueError('neural execution scope differs from its frozen reader contract')
    with reservation(directory, frozen) as access:
        packet, contract = access['packet'], access['contract']
        cases = [access['payloads'][unit] for unit in packet['reserve_units']]
        validate_cases(cases, role)
        for unit, case in zip(packet['reserve_units'], cases):
            if case['unit'] != unit or digest(case['sources']) != contract['reserve'][unit]['content_sha256']:
                raise ValueError('reserved source differs from its reconstructed maker series')
        work = Path(directory) / 'work'
        identity = {'cell_identity': cell_identity(), 'operation': 'frozen-neural-choice-confirmation-v1',
            'scope': scope, 'role': role, 'source': sources(), 'claim_id': claim_id,
            'freeze_complete_sha256': frozen['freeze_complete_sha256'], 'claims_sha256': frozen['claims_sha256'],
            'execution_contract_sha256': digest(contract), 'selected_units': packet['reserve_units'],
            'seeds': list(seeds), 'access_identity_sha256': digest(access['identity']),
            'access_opened_sha256': file_hash(Path(directory) / 'OPENED.json')}
        units = Units(work, identity)
        prior = reentry(work, identity)
        rows = []
        for seed in seeds:
            item = contract['readers'][str(seed)]
            package = checked(item['package'])
            def saved_call(case, evidence, side, invoke=None):
                task = request_task(evidence, {'operation': 'choice'}, package)
                path = work / 'calls' / str(seed) / digest(case['unit'])[:16] / (side + '.json')
                result = checkpoint_call(path, {'evidence': evidence, 'task': task}, invoke, resume_only=invoke is None)
                audit_execution(result)
                return result
            pending = [c for c in cases if units.get([c['unit'], seed]) is None]
            if prior is not None and pending:
                raise ValueError('completed neural confirmation omits assigned seed units')
            if pending:
                training = pointer_path(item['training']).parent
                family = read(training / 'IDENTITY.json')['family']
                adapter, adapter_sha, _ = training_package(training, family, scope)
                config = {'family': family, 'adapter': str(adapter), 'adapter_sha256': adapter_sha,
                    'precision': 'float16', 'device': 'cuda', 'batch_size': 4, 'max_context': 4096,
                    'max_support': 128, 'max_new_tokens': 32, 'generation': {'do_sample': False}}
                with resident(work / 'services' / uuid.uuid4().hex[:12], config) as (ready, token):
                    if ready['identity'] != package:
                        raise ValueError('loaded confirmation package differs from selected discovery package')
                    for case in pending:
                        def call(evidence, side):
                            task = request_task(evidence, {'operation': 'choice'}, package)
                            return saved_call(case, evidence, side,
                                lambda: execute(evidence, task, ready['endpoint'], token, root=work / 'capsules'))
                        units.put([case['unit'], seed], forecast(case, seed, contract['contrast'], call, scope=scope))
            for case in cases:
                rebuilt = forecast(case, seed, contract['contrast'], lambda evidence, side: saved_call(case, evidence, side), scope=scope)
                if units.get([case['unit'], seed]) != rebuilt:
                    raise ValueError('saved neural confirmation failed complete reconstruction')
                rows.append(rebuilt)
        if len(units.all()) != len(cases) * len(seeds):
            raise ValueError('extra or missing completed neural confirmation units')
        outcome = calculation_input(rows, packet['reserve_units'], scope=scope)
        freeze(work / 'PREDICTIONS.json', rows); freeze(work / 'OUTCOME.json', outcome)
        if prior is not None:
            return prior
        return finish(work, identity, started, cpu,
            ['PREDICTIONS.json', 'OUTCOME.json', 'units', 'calls', 'capsules', 'services', '../OPENED.json', '../IDENTITY.json'],
            assigned_units=len(cases), completed_units=len(cases), training_seeds=list(seeds),
            calculation_status=outcome['calculation_status'], scientific_confirmation=False, role=role)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    for key in ('output', 'freeze', 'manifest', 'queue'):
        parser.add_argument('--' + key, type=Path, required=True)
    parser.add_argument('--claim', required=True)
    parser.add_argument('--scope', choices=('pilot', 'scientific'), required=True)
    args = parser.parse_args()
    run(args.output, args.freeze, args.manifest, args.queue, args.claim, args.scope)
