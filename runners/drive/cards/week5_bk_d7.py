"""Exact checkpointed continuation of the registered D7.s and D7.m follow-ups.

DESIGN CHECK: retain all original models, worlds, references and uncertainty.
Partition execution only; failed calibration never becomes human admission.
"""
from pathlib import Path
import os
import time
from threadpoolctl import threadpool_limits
from runners.stage14.common import read, atomic, digest, filehash
from . import week4_d7_calibration as calibration
from . import week4_d7_human_h1 as human
from . import week4_d7_specification as specification
from . import week4_d7_stability as stability
from .week5_at_source import authenticate
from .batch_runtime import check_files
from .timing_p6 import write_equal

CARDS = {'D7.s': specification, 'D7.m': stability}
REGIMES = ('null', 'nuisance', 'signed')
SEED = 20261026


def roster():
    return [(regime, ordinal, SEED + ordinal) for regime in REGIMES for ordinal in range(10)]


def configuration(card, operation, regime=None, ordinal=None):
    if card not in CARDS or operation not in ('world', 'fixture_world', 'pilot_reduce', 'calibration_reduce', 'human'):
        raise ValueError('Unknown registered D7 continuation')
    result = dict(card=card, operation=operation, references=200, bootstrap_draws=2000,
                  seed=SEED, max_wall_seconds=1200)
    if operation in ('world', 'fixture_world'):
        if (regime, ordinal, SEED + (ordinal if type(ordinal) is int else -1)) not in roster():
            raise ValueError('Unknown frozen calibration world')
        result.update(regime=regime, ordinal=ordinal, writers=3 if operation == 'fixture_world' else 12)
    return result


def world_source(card, regime, ordinal, writers=12):
    if card not in CARDS or (regime, ordinal, SEED + ordinal) not in roster():
        raise ValueError('Unknown world identity')
    producer = calibration if card == 'D7.s' else stability
    rows, dose = producer.world(regime, SEED + ordinal, writers, ordinal)
    bank = human.h.bank(rows, draws=200, seed=SEED + ordinal)
    if not bank['complete'] or len(bank['accepted']) != 200:
        raise ValueError('Complete original conditional bank required')
    return rows, bank['accepted'], dose


def due(root, began):
    return ((root / 'YIELD_REQUEST.json').exists() or (root.parent / 'STOP').exists()
            or time.monotonic() - began >= 1200)


def fitted_bank(root, card, rows, assignments, seed, verifying=False):
    """401 whole-writer arms, original global reference indices and RNG streams."""
    root = Path(root); root.mkdir(parents=True, exist_ok=True)
    began = time.monotonic(); module = CARDS[card]
    groups, excluded = calibration.support(rows)
    if excluded or len(groups) < 3 or len(assignments) != 200:
        raise ValueError('Exact original complete supported reference population required')
    if [a['draw'] for a in assignments] != list(range(200)):
        raise ValueError('Original ordered global assignment indices required')
    for assignment in assignments:
        other, bad = calibration.support(calibration.reassigned(rows, assignment['assignment']))
        if bad or sorted(other) != sorted(groups):
            raise ValueError('Reference changes original supported roster')
    binding = digest(dict(card=card, rows=rows, assignments=assignments, seed=seed,
                          producer_sha256=filehash(module.__file__), references=200, bootstrap_draws=2000))
    write_equal(root / 'BINDING.json', dict(binding=binding))
    arms = []; previous = binding
    for index in range(401):
        if due(root, began):
            return None
        path = root / f'arm-{index:03d}.json'
        seal_path = root / f'arm-{index:03d}.seal.json'
        family = 'real' if index == 0 else ('joint' if index % 2 else 'conditional')
        reference = None if index == 0 else (index - 1) // 2
        identity = dict(binding=binding, index=index, family=family, reference=reference, previous=previous)
        if path.exists() and seal_path.exists() and not verifying:
            seal = read(seal_path)
            if seal != dict(identity, sha256=filehash(path)):
                raise ValueError('Changed or wrongly bound fitted-arm checkpoint')
            value = read(path)
        else:
            selected = groups
            if family == 'conditional':
                selected, _ = calibration.support(calibration.reassigned(rows, assignments[reference]['assignment']))
            value, _ = module.fits(selected, reference if family == 'joint' else None, seed)
            if verifying:
                if read(path) != value or read(seal_path) != dict(identity, sha256=filehash(path)):
                    raise ValueError('Fresh complete original fit or seal differs')
            else:
                write_equal(path, value)
                write_equal(seal_path, dict(identity, sha256=filehash(path)))
        if sorted(value) != sorted(groups):
            raise ValueError('Saved fitted arm changes writer population')
        previous = digest(read(seal_path)); arms.append(value)
        atomic(root / 'PROGRESS.json', dict(phase='verify' if verifying else 'execute',
                                           arms_done=index + 1, arms_total=401))
    real, joint, fake = arms[0], arms[1::2], arms[2::2]
    summary = module.summarize(real, joint, fake, 2000, seed)
    result = dict(writers=len(groups), observations=len(rows), joint_draws=200, conditional_draws=200,
                  fit_bank_sha256=digest(dict(real=real, joint=joint, fake=fake)))
    result['curve' if card == 'D7.s' else 'summary'] = summary
    return result


def record_equal(path, value, verifying):
    if verifying:
        if read(path) != value:
            raise ValueError('Fresh D7 reduction differs')
    else:
        write_equal(path, value)


def world_record(card, regime, ordinal, analysis, writers=12):
    dose = 0. if regime != 'signed' else (.8 if ordinal % 2 == 0 else -.8)
    return dict(card=card, label=regime + '-' + str(SEED + ordinal), regime=regime,
                ordinal=ordinal, seed=SEED + ordinal, dose=dose, writers=writers,
                analysis=analysis, references=200, bootstrap_draws=2000,
                producer_sha256=filehash(CARDS[card].__file__))


def campaign_result(card, worlds):
    if sorted((r['regime'], r['ordinal'], r['seed']) for r in worlds) != sorted(roster()):
        raise ValueError('All exact thirty distinct calibration worlds required')
    for value in worlds:
        if value['card'] != card or value['writers'] != 12 or value['references'] != 200 or value['bootstrap_draws'] != 2000:
            raise ValueError('Complete unchanged calibration design required')
        expected = world_record(card, value['regime'], value['ordinal'], value['analysis'])
        if value != expected:
            raise ValueError('Calibration world identity, dose or original producer changed')
        analysis = value['analysis']
        if analysis['writers'] != 12 or analysis['joint_draws'] != 200 or analysis['conditional_draws'] != 200:
            raise ValueError('Missing complete calibration arms')
        summaries = analysis['curve'].values() if card == 'D7.s' else [analysis['summary']]
        if any(s['bootstrap_draws'] != 2000 or s['joint_permutation']['attempted'] != 200
               or s['fake_writer']['attempted'] != 200 for s in summaries):
            raise ValueError('Incomplete uncertainty or reference denominator')
    worlds = sorted(worlds, key=lambda w: (REGIMES.index(w['regime']), w['ordinal']))
    return dict(card=card, calibration=CARDS[card].assess(worlds), worlds=worlds,
                original_estimator=True, human_scored=False, causal_claim=False)


def dependency(path, config):
    root = Path(path)
    if root.name == 'COMPLETE.json':
        root = root.parent
    root = authenticate(root)
    plan = read(root / 'PLAN.json')
    if plan['module'] != __name__ or plan['config'] != config:
        raise ValueError('Wrong D7 continuation dependency')
    check_files(plan['pins'])
    return root


def load_worlds(paths, card, required):
    if len(paths) != len(required):
        raise ValueError('Incomplete world completion list')
    records = []; timings = []
    for path in paths:
        root = Path(path)
        if root.name == 'COMPLETE.json':
            root = root.parent
        root = authenticate(root); plan = read(root / 'PLAN.json'); cfg = plan['config']
        if cfg.get('operation') != 'world' or cfg.get('card') != card:
            raise ValueError('Wrong world producer')
        root = dependency(path, configuration(card, 'world', cfg.get('regime'), cfg.get('ordinal')))
        record = read(root / 'output/RESULT.json')
        if (record['regime'], record['ordinal'], record['seed']) not in required:
            raise ValueError('Wrong frozen calibration identity')
        records.append(record)
        timings.append({phase: read(root / 'output' / (phase + '_COST.json'))['process_cpu_seconds']
                        for phase in ('EXECUTE', 'VERIFY')})
    if sorted((r['regime'], r['ordinal'], r['seed']) for r in records) != sorted(required):
        raise ValueError('Duplicated or missing calibration world')
    return records, timings


def human_source(inputs, card):
    expected = human.SOURCE_KEYS | {'support_completion', 'calibration_completion', 'cost_completion'}
    if set(inputs) != expected:
        raise ValueError('Exact original human source and gated dependencies required')
    root = dependency(inputs['calibration_completion'], configuration(card, 'calibration_reduce'))
    calibration_result = read(root / 'output/RESULT.json')
    if campaign_result(card, calibration_result['worlds']) != calibration_result or not calibration_result['calibration']['passes']:
        raise ValueError('Complete unchanged calibration did not pass')
    base = {k:v for k,v in inputs.items() if k not in ('calibration_completion', 'cost_completion')}
    module = CARDS[card]
    cost_root, _ = human.authenticated(inputs['cost_completion'], module.__name__, module.configuration('human-cost'))
    if read(cost_root / 'PLAN.json')['inputs'] != base:
        raise ValueError('Original cost used different human source')
    return human.source(base)


def run(output, inputs, config, verifying=False):
    root = Path(output); root.mkdir(parents=True, exist_ok=True)
    card = config.get('card'); operation = config.get('operation')
    if config != configuration(card, operation, config.get('regime'), config.get('ordinal')):
        raise ValueError('Frozen D7 configuration required')
    binding = dict(config=config, inputs={k:filehash(v) for k,v in inputs.items()})
    record_equal(root / 'INPUT_BINDING.json', binding, verifying)
    if operation in ('world', 'fixture_world'):
        if inputs:
            raise ValueError('Constructed worlds accept no human inputs')
        rows, assignments, _ = world_source(card, config['regime'], config['ordinal'], config['writers'])
        analysis = fitted_bank(root, card, rows, assignments, SEED + config['ordinal'], verifying)
        if analysis is None:
            return dict(status='yielded', reason='sealed complete fitted-arm boundary')
        result = world_record(card, config['regime'], config['ordinal'], analysis, config['writers'])
    elif operation in ('pilot_reduce', 'calibration_reduce'):
        if set(inputs) != {'worlds'}:
            raise ValueError('Exact completed world bank required')
        required = roster()[:2] if operation == 'pilot_reduce' else roster()
        records, timings = load_worlds(read(inputs['worlds']), card, required)
        if operation == 'calibration_reduce':
            result = campaign_result(card, records)
        else:
            # Timing complete worlds avoids coarse sub-writer timer quantization.
            # Both passes, source reconstruction, serialization and setup are included.
            worst_pass = max(t[phase] for t in timings for phase in ('EXECUTE', 'VERIFY'))
            result = dict(card=card, complete_worlds=2, total_worlds=30, coverage=2/30,
                          fitted_arms_per_world=401, bootstrap_draws=2000, timings=timings,
                          calibration_forecast_cpu_seconds=3*2*30*worst_pass,
                          safety_factor=3, both_passes=True, human_scored=False,
                          prior_charges_and_human_forecast_additional=True,
                          scientific_admission=False)
    else:
        rows, assignments, excluded = human_source(inputs, card)
        analysis = fitted_bank(root, card, rows, assignments, SEED, verifying)
        if analysis is None:
            return dict(status='yielded', reason='sealed complete fitted-arm boundary')
        result = dict(card=card, analysis=analysis, original_exclusions=excluded,
                      human_scored=True, scope='original 38 supported writers; descriptive',
                      causal_claim=False, original_estimator=True)
    record_equal(root / 'RESULT.json', result, verifying)
    if verifying:
        return dict(verified=True, full_fresh_original_fit_replay=operation in ('world', 'fixture_world', 'human'),
                    complete_reduction=operation in ('pilot_reduce', 'calibration_reduce'))
    return dict(status='complete', card=card, operation=operation)


def invocation(output, inputs, config, verifying):
    root = Path(output); phase = 'VERIFY' if verifying else 'EXECUTE'
    began = time.process_time(); stamp = time.time_ns(); value = None
    try:
        with threadpool_limits(limits=2):
            value = run(output, inputs, config, verifying)
        return value
    finally:
        ledger = root / 'cost_ledger'; ledger.mkdir(parents=True, exist_ok=True)
        write_equal(ledger / f'{phase}-{os.getpid()}-{stamp}.json',
                    dict(process_cpu_seconds=time.process_time()-began, phase=phase,
                         outcome='exception' if value is None else value.get('status', 'verified')))
        completed = value is not None and (value.get('verified') is True or value.get('status') == 'complete')
        path = root / (phase + '_COST.json')
        if completed and not path.exists():
            write_equal(path, dict(process_cpu_seconds=sum(read(p)['process_cpu_seconds'] for p in ledger.glob(phase+'-*.json')),
                                   includes_prior_phase_invocations=True,
                                   authoritative_cost='runtime all-attempt accounting including startup'))


def execute(output, inputs, config):
    return invocation(output, inputs, config, False)


def verify(output, inputs, config):
    return invocation(output, inputs, config, True)
