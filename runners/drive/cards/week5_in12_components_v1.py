"""Add the two omitted IN12 paired-correlation reports; preserve all old draws.

DESIGN CHECK: LESSONS 2, 3 and 5; CONTROLS 6-7. Literal signed/null pairs,
writer weighting, original seed/ordinal parity, complete replay and hostile
checkpoint/source mutations qualify this reporting adapter before human use.
No primary, model, resample, scientific gate or original output is replaced.
"""
from pathlib import Path
import os
import time
for _key in ('OMP_NUM_THREADS', 'MKL_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'NUMEXPR_NUM_THREADS'):
    os.environ[_key] = '2'
import numpy as np
from . import week6_in12_reporting_v1 as old
from . import week5_in12_math_v1 as math
from . import week5_engine_export_io as seal
from . import week5_qualification_io as io

MODULE = 'runners.drive.cards.week5_in12_components_v1'
REPO = Path(__file__).resolve().parents[3]
BASE = 'results/phase_2_4_stage_15/raw/drive-week5-20261107/'
ORIGINAL_ROOT = BASE + 'IN12-reporting-v1-full-continuation-1-20261115'
SOURCE_ROOT = BASE + 'IN12-source-reporting-v1-continuation-1-20261115'
NEGATIVE = 'negative_negative_correlation'
CROSS = 'negative_positive_correlation'
DIFFERENCE = 'within_writer_correlation_difference'
COMPONENTS = (NEGATIVE, CROSS)
ORIGIN_PINS = {
    ORIGINAL_ROOT + '/PLAN.json': 'df375f2b2ca334b4a7da207209a63417a416058f78a98913c030ba05de7cc177',
    ORIGINAL_ROOT + '/COMPLETE.json': 'd679899944f80f14725087d75255ecc2d20b8a39fe38a3bf2be531da02c19207',
    ORIGINAL_ROOT + '/VERIFIED.json': '48322d7666ae11d6e704b957f4ecc95da3514e70d89878c57982352662ad7ca4',
    ORIGINAL_ROOT + '/output/RESULT.json': '1a9d94d4da5806a91702f8f3be742482e8822978b88a284123b9a575f4f63ca6',
    ORIGINAL_ROOT + '/output/DRAWS.json': 'af62d7949318d4b3949b2490891707b249ed40b0de9e41aa0946bb19e515c59d',
    ORIGINAL_ROOT + '/output/independent-replay/DRAWS.json': '651bd8978764923bbae0babc4a394c687a65069dd772a2122aa410c5bddc4c99',
    SOURCE_ROOT + '/PLAN.json': 'efefb0d35f7ed8b9871ba6ee041f6f321d7ae8f72199e4a9610d452f90006be2',
    SOURCE_ROOT + '/COMPLETE.json': '7a6cbd7eba2946c366bf78e1612e1aabcd9122786168880c1d7240dd0cdb25ba',
    SOURCE_ROOT + '/VERIFIED.json': 'c78e76f97e74e117d23a7b27995f8d0c22f860d5897bc3b60f4c7ccec47fb0b2',
    SOURCE_ROOT + '/output/TABLE.json': 'cb29e056201acbf54c5f7e04b163f78654f2a42943151757d57d61e53d74c8e3',
    SOURCE_ROOT + '/output/RESULT.json': 'a6a5d2e76e0c30ef256fafd99e5664960daa3ff72fd96d1ea61abb2d3e4cbb6b',
}
SCIENCE_PINS = {
    'docs/design/stage-15/week5/IN12_TWO_DAY_V1.md': 'c7b9b9abe9d4ff76eea61981e6b523ed72e53cc7a2e9a2b736ce4bef5c1bef26',
    'runners/drive/cards/week5_in12_math_v1.py': 'b1ee02d3131bd6447fab083118dda0dc40b55c640183fd0a6b745e9d9daa643f',
    'runners/drive/cards/week6_in12_reporting_v1.py': '7872fe9d710fe236c66136ba42a59e8ab04d2e95d53a33660e903d464d9d9044',
    'runners/drive/cards/week5_in.py': '5490623534a23153d31af670e99b0802079f74c57d6cfbf629fcc3ad278dbcfc',
    'runners/drive/cards/week5_engine_export_io.py': '4b2453c1e1b2a2a107295af2e452187f302ae823cce4c2eb4bd041fc881da924',
    'runners/drive/cards/week5_qualification_io.py': '3f517e7ff462aef51a905085507295bfccc4272e84c57d24a7e1f6dcb62f2b7c',
}


def dependencies():
    return old.dependencies() | {Path(__file__).as_posix(): io.sha(__file__)}


def settings(config):
    if set(config) - {'phase', 'draws', 'max_new_draws', 'max_wall_seconds'}:
        raise ValueError('Undeclared component reporting setting')
    if config.get('phase') != 'IN12-components' or type(config.get('draws', 2000)) is not int or config.get('draws', 2000) != 2000:
        raise ValueError('Only the complete original 2000-draw component supplement')
    quantum = config.get('max_new_draws', 100)
    if type(quantum) is not int or not 1 <= quantum <= 2000:
        raise ValueError('Whole-draw quantum must be between 1 and 2000')
    wall = config.get('max_wall_seconds', 900)
    if isinstance(wall, bool) or not np.isfinite(wall) or wall <= 0:
        raise ValueError('Positive finite producer wall bound required')
    return {'phase': 'IN12-components', 'draws': 2000, 'seed': [20261113, 12, 'zero-based draw ordinal'],
            'report_only': list(COMPONENTS), 'difference_check': 'point and every original draw',
            'original_estimand_and_gates_unchanged': True}


def check_origin(inputs, output=None):
    if set(inputs) != {'analysis_run'} or Path(inputs['analysis_run']).resolve() != (REPO / ORIGINAL_ROOT).resolve():
        raise ValueError('Exact completed original IN12 analysis required')
    if output is not None:
        target = Path(output).resolve()
        for name in (ORIGINAL_ROOT, SOURCE_ROOT):
            source = (REPO / name).resolve()
            if target == source or source in target.parents or target in source.parents:
                raise ValueError('Additive output must be separate from original dependencies')
    for name, expected in (ORIGIN_PINS | SCIENCE_PINS).items():
        path = REPO / name
        if path.is_symlink() or io.sha(path) != expected:
            raise ValueError('Frozen original IN12 source, science or output differs: ' + name)


def load_original(inputs, output):
    check_origin(inputs, output)
    root, plan, _ = seal.complete(inputs['analysis_run'], old.MODULE)
    if plan['config'].get('phase') != 'IN12' or plan['config'].get('draws') != 2000:
        raise ValueError('Original complete IN12 analysis phase required')
    if set(plan['inputs']) != {'prepared_run'} or Path(plan['inputs']['prepared_run']).resolve() != (REPO / SOURCE_ROOT).resolve():
        raise ValueError('Original prepared-source linkage differs')
    result = seal.read(root / 'output/RESULT.json')
    if result.get('complete_card') is not True or result.get('status') != 'complete':
        raise ValueError('Completed original analysis result required')
    bank = seal.read(root / 'output/DRAWS.json')
    if not isinstance(bank.get('point'), dict) or len(bank.get('draws', [])) != 2000:
        raise ValueError('Complete original point and 2000 retained draws required')
    frame, source_identity = old.load_prepared(plan['inputs'])
    old.compare(source_identity, result['source_identity'])
    identity = {'original_run': ORIGINAL_ROOT, 'prepared_run': SOURCE_ROOT,
                'original_pins': ORIGIN_PINS, 'science_pins': SCIENCE_PINS,
                'prepared_source_identity': source_identity}
    return frame, bank, result, identity


def prepare_pairs(frame, independent=False):
    # Same eligibility, fixed prompt scales, prompt means, pair ordering and keys.
    # Building regression matrices is unnecessary for these two omitted reports.
    table, scales = math.fixed_table(frame, independent)
    return {'pairs': math.pair_rows(table), 'keys': sorted(table.prolific_id.unique()), 'scales': scales}


def evaluate(prepared, counts, independent=False):
    nn, cross, eligible = prepared['pairs']
    support = {name: len({row[0] for row in rows if counts.get(row[0], 0) > 0})
               for name, rows in zip(COMPONENTS, (nn, cross), strict=True)}
    values = dict.fromkeys((*COMPONENTS, DIFFERENCE))
    failures = {}
    if eligible < 300:
        failures = dict.fromkeys(values, 'fewer than 300 writers with at least two distinct negative prompts')
    elif min(support.values()) < 2:
        failures = dict.fromkeys(values, 'paired intensity variance/support absent')
    else:
        for name, rows in zip(COMPONENTS, (nn, cross), strict=True):
            values[name] = math.correlation(rows, counts, independent)
            if values[name] is None:
                failures[name] = 'paired intensity variance/support absent'
        if all(values[name] is not None for name in COMPONENTS):
            values[DIFFERENCE] = values[NEGATIVE] - values[CROSS]
        else:
            failures[DIFFERENCE] = 'paired intensity variance/support absent'
    return {'value': values, 'failures': failures, 'contributing_writers': support}


def compare_difference(actual, original, eligible):
    if eligible < 300:
        if DIFFERENCE in original['value'] or actual['value'][DIFFERENCE] is not None:
            raise ValueError('Original paired-secondary eligibility differs')
        return
    if DIFFERENCE not in original['value']:
        raise ValueError('Original paired-secondary draw absent')
    old.compare(actual['value'][DIFFERENCE], original['value'][DIFFERENCE])
    if original['value'][DIFFERENCE] is None:
        if original['failures'].get(DIFFERENCE) != actual['failures'].get(DIFFERENCE):
            raise ValueError('Original paired-secondary failure disposition differs')


def support_metadata(prepared):
    nn, cross, eligible = prepared['pairs']
    return {'eligible_writers': eligible, 'negative_pairs': len(nn), 'negative_positive_pairs': len(cross),
            'negative_pair_writers': len({r[0] for r in nn}),
            'negative_positive_pair_writers': len({r[0] for r in cross}),
            'interpretation': 'cross-prompt paired-report association, not within-person time-series correlation'}


def calculate(frame, output, original_bank, original_result, identity, config, independent=False):
    semantic = settings(config)
    output = Path(output); output.mkdir(parents=True, exist_ok=True)
    prepared = prepare_pairs(frame, independent)
    if len(prepared['keys']) < 2 or len(original_bank['draws']) != 2000:
        raise ValueError('Original complete multi-writer analysis bank required')
    support = support_metadata(prepared)
    old.compare(support, original_result['paired_support'])
    old.compare(prepared['scales'], original_result['scales'])
    binding = old.digest({'source': identity, 'semantic': semantic, 'modules': dependencies(),
                          'frame': frame.to_json(orient='split'), 'independent': independent})
    path = output / 'COMPONENT_DRAWS.json'
    saved = seal.state(path, binding, {'point': None, 'draws': []})
    if len(saved['draws']) > 2000:
        raise ValueError('Extra component draw ordinals refused')
    if saved['point'] is None:
        if saved['draws']:
            raise ValueError('Draw prefix without its original point')
        saved['point'] = evaluate(prepared, dict.fromkeys(prepared['keys'], 1), independent)
        compare_difference(saved['point'], original_bank['point'], prepared['pairs'][2])
        seal.checkpoint(path, saved)
    compare_difference(saved['point'], original_bank['point'], prepared['pairs'][2])
    for ordinal, draw in enumerate(saved['draws']):
        if draw.get('ordinal') != ordinal:
            raise ValueError('Component checkpoint ordinals are not a complete prefix')
        compare_difference(draw, original_bank['draws'][ordinal], prepared['pairs'][2])
    started = time.monotonic(); cpu = time.process_time(); added = 0
    while len(saved['draws']) < 2000:
        if old.should_yield(output, started, config, added):
            seal.checkpoint(path, saved)
            return {'status': 'yielded', 'verified': False, 'phase': 'IN12_component_draws',
                    'completed': len(saved['draws']), 'total': 2000}
        ordinal = len(saved['draws'])
        value = evaluate(prepared, math.resample(prepared['keys'], ordinal), independent)
        compare_difference(value, original_bank['draws'][ordinal], prepared['pairs'][2])
        saved['draws'].append({'ordinal': ordinal, **value}); added += 1
        if added == 1 and not (output / 'COST_PREFIX.json').exists():
            io.write_json(output / 'COST_PREFIX.json', {'first_draw_CPU_seconds': time.process_time() - cpu,
                'excludes_source_IO_point_and_complete_independent_replay': True})
        if len(saved['draws']) % 10 == 0:
            seal.checkpoint(path, saved)
            io.write_json(output / 'PROGRESS.json', {'phase': 'IN12_component_draws',
                          'completed': len(saved['draws']), 'total': 2000})
    seal.checkpoint(path, saved)
    answers = {}
    for name, support_key in zip(COMPONENTS, ('negative_pair_writers', 'negative_positive_pair_writers'), strict=True):
        answer = old.summarize(name, saved['point'], saved['draws'], support[support_key], independent)
        answers[name] = {**answer, 'descriptive': True, 'units': 'weighted Pearson correlation'}
    return {'card': 'IN12', 'record_kind': 'claim', 'theory_tags': ['H15-T11', 'DISAGREE-6'],
            'by_construction': False, 'activation': [], 'status': 'complete', 'complete_supplement': True,
            'correction_class': 'reporting omission', 'source_identity': identity, 'semantic': semantic,
            'scope': 'descriptive cross-prompt paired-report associations; adult prompted self-report',
            'secondary_components': answers, 'paired_support': support, 'scales': prepared['scales'],
            'original_difference_check': {'point': True, 'draws': 2000, 'all_ordinals': True,
                'comparison_absolute_tolerance': 1e-7, 'relative_tolerance': 0,
                'original_failure_dispositions_retained': True},
            'original_primary_and_difference_not_replaced': True, 'failed_draws_never_removed': True,
            'new_source_or_model': False, 'new_scientific_outcome_category': False}


def execute(output, inputs, config):
    settings(config)
    frame, bank, result, identity = load_original(inputs, output)
    answer = calculate(frame, output, bank, result, identity, config)
    check_origin(inputs, output)
    if answer.get('status') != 'yielded':
        io.write_json(Path(output) / 'RESULT.json', answer)
    return answer


def verify(output, inputs, config):
    settings(config); output = Path(output)
    frame, bank, result, identity = load_original(inputs, output)
    replay = output / 'independent-replay'
    answer = calculate(frame, replay, bank, result, identity, config, True)
    if answer.get('status') == 'yielded':
        return {**answer, 'verified': False}
    left = seal.read(output / 'COMPONENT_DRAWS.json')
    right = seal.read(replay / 'COMPONENT_DRAWS.json')
    if len(left['draws']) != 2000 or len(right['draws']) != 2000:
        raise ValueError('Complete producer and independent component banks required')
    old.compare(left['point'], right['point']); old.compare(left['draws'], right['draws'])
    old.compare(seal.read(output / 'RESULT.json'), answer)
    check_origin(inputs, output)
    io.write_json(replay / 'RESULT.json', answer)
    return {'verified': True, 'all_2000_component_draws_independently_replayed': True,
            'original_point_and_every_difference_verified': True,
            'independent_scalar_correlation_and_interval_formulas': True,
            'original_science_and_outputs_preserved': True, 'no_demographics_read': True}
