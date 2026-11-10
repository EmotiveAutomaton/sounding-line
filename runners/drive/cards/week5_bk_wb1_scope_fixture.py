"""Whole-writer sample through original raw/statistical kernels and refusals."""
from pathlib import Path
from types import SimpleNamespace
import copy
import json
import shutil
import time
from threadpoolctl import threadpool_limits

from . import week5_bk_wb1_source as full_source
from . import week5_bk_wb1_scope as source
from . import week5_bk_wb1_encode_scoped as encode
from . import week5_bk_wb1_coverage_scoped as coverage
from . import week5_bk_wb1_reduce_scoped as reduce
from . import week5_bk_wb1_coverage_pilot_scoped as pilot
from . import week5_bk_wb1_pilot_forecast_scoped as forecast
from . import week3_pieces_coverage as old_coverage
from . import week3_pieces_effects_h1 as effects
from . import week4_pieces_windows_h1 as exact
from . import week3_pieces_stats as stats
from .timing_census import read, filehash
from .timing_p6 import write_equal, gzread, gzwrite
from runners.stage14.common import digest
from tests.test_week4_pieces_windows_h1 import canonical_fixture


def sealed(root, module, inputs, config):
    if (root / 'COMPLETE.json').exists():
        return
    write_equal(root / 'PLAN.json', dict(module=module.__name__, inputs=inputs, config=config,
        pins={str(Path(module.__file__).resolve()): filehash(module.__file__)}))
    outputs = {p.relative_to(root).as_posix(): filehash(p) for p in root.rglob('*')
               if p.is_file() and p.name not in ('COMPLETE.json', 'PROGRESS.json', 'YIELD_REQUEST.json')}
    write_equal(root / 'COMPLETE.json', dict(status='COMPLETE', fresh_process_verified=True, outputs=outputs,
        constructed_dependency_fixture=True, not_a_production_runtime_admission=True))


def stage(module, root, inputs, config, verifying):
    target = root / 'output'
    if verifying:
        if module is encode:
            target = root / 'independent_replays' / str(time.time_ns())
            shutil.copytree(root / 'output', target, ignore=shutil.ignore_patterns('*.verified.json'))
        if module.verify(target, inputs, config).get('verified') is not True:
            raise ValueError('Actual sample handler independent verification failed')
    else:
        if module.execute(target, inputs, config).get('status') != 'complete':
            raise ValueError('Actual sample handler did not complete')
        if module.verify(target, inputs, config).get('verified') is not True:
            raise ValueError('Actual sample handler replay failed')
        sealed(root, module, inputs, config)
    return root


def refuse(call):
    try:
        call()
    except (ValueError, KeyError):
        return
    raise ValueError('Malformed sample or mixed source was accepted')


def changed_rows(root, original_root, name, rows):
    target = root / name
    if not target.exists():
        shutil.copytree(original_root, target)
        path = target / 'output/COVERAGE_ROWS.json.gz'
        gzwrite(path, rows)
        manifest_path = target / 'output/SOURCE.json'
        manifest = read(manifest_path)
        manifest['rows_sha256'] = digest(rows)
        manifest_path.write_text(json.dumps(manifest, sort_keys=True) + '\n', encoding='utf8')
        done_path = target / 'COMPLETE.json'
        done = read(done_path)
        for changed in (path, manifest_path):
            done['outputs'][changed.relative_to(target).as_posix()] = filehash(changed)
        done_path.write_text(json.dumps(done, sort_keys=True) + '\n', encoding='utf8')
    return target


def run(output, inputs, config, verifying=False):
    if inputs or config:
        raise ValueError('Constructed WB1 sample fixture takes no human input')
    root = Path(output)
    root.mkdir(parents=True, exist_ok=True)
    if (root / 'YIELD_REQUEST.json').exists():
        return dict(status='yielded', reason='before constructed sample pipeline')
    inputfile = root / 'INPUTS.json'
    if not inputfile.exists():
        write_equal(inputfile, canonical_fixture(root / 'original-inputs'))
    original = read(inputfile)
    parent = stage(full_source, root / 'full-source', original, full_source.configuration('constructed'), verifying)
    _, full_manifest, full_rows = full_source.load(parent)
    # Three of four constructed writers is a validation case, not a human size.
    cfg = dict(writers=3, seed=source.SAMPLE_SEED, trigger='constructed_fixture')
    scope_inputs = dict(source_root=str(parent))
    sampled = stage(source, root / 'sample-source', scope_inputs, cfg, verifying)
    _, manifest, rows = source.load(sampled)
    chosen = set(source.choose(full_rows, 3))
    expected = [r for r in full_rows if r['writer'] in chosen]
    if rows != expected or len(rows) != 6 or any(sum(r['writer'] == w for r in rows) != 2 for w in chosen):
        raise ValueError('Sample lost a whole writer session or changed source rows')
    if source.choose(full_rows[::-1], 3) != sorted(chosen):
        raise ValueError('Writer selection depends on source ordering')
    changed_outcomes = [dict(r, symbols=['changed'], seconds=[0], duration=1) for r in full_rows]
    if source.choose(changed_outcomes, 3) != sorted(chosen):
        raise ValueError('Writer selection depends on observed symbols or timing')
    all_scope = stage(source, root / 'all-writers', scope_inputs,
        dict(writers=4, seed=source.SAMPLE_SEED, trigger='constructed_fixture'), verifying)
    if source.load(all_scope)[2] != full_rows:
        raise ValueError('All-writer projection differs from the original source')
    for wrong in (dict(cfg, writers=0), dict(cfg, writers=5), dict(cfg, seed=1), dict(cfg, trigger='measured_E')):
        refuse(lambda c=wrong: source.projection(scope_inputs, c))
    # These numbers exist only as a known-answer arithmetic control. They are
    # never written as a human sizing decision or passed to corpus projection.
    arithmetic = dict(charged_cpu_seconds=30000, full_projected_cpu_seconds=530000,
                      projected_sample_cpu_seconds=200000, sample_budget_cpu_seconds=490000,
                      sizing_note='Constructed arithmetic control, not a measured forecast')
    if source.budget(arithmetic, 300000, 200000) != (530000, 490000, 200000, 30000):
        raise ValueError('Doubled-ceiling arithmetic differs')
    for wrong in (dict(arithmetic, charged_cpu_seconds=0),
                  dict(arithmetic, full_projected_cpu_seconds=520000),
                  dict(arithmetic, projected_sample_cpu_seconds=490001),
                  dict(arithmetic, sample_budget_cpu_seconds=520000),
                  dict(arithmetic, sizing_note='')):
        refuse(lambda d=wrong: source.budget(d, 300000, 200000))
    below_trigger = dict(arithmetic, full_projected_cpu_seconds=330000)
    refuse(lambda: source.budget(below_trigger, 200000, 100000))
    refuse(lambda: source.load(parent))
    refuse(lambda: full_source.load(sampled))
    missing = changed_rows(root, sampled, 'missing-writer-session', rows[:-1])
    extra = changed_rows(root, sampled, 'unselected-session', rows + [next(r for r in full_rows if r['writer'] not in chosen)])
    changed_side = copy.deepcopy(rows)
    changed_side[0]['side'] = 'test' if changed_side[0]['side'] == 'discovery' else 'discovery'
    partition = changed_rows(root, sampled, 'changed-partition', changed_side)
    for invalid in (missing, extra, partition):
        refuse(lambda p=invalid: source.load(p))
    src_inputs = dict(source_root=str(sampled))
    blocks = []
    for start in range(0, len(manifest['sessions']), 2):
        if (root / 'YIELD_REQUEST.json').exists():
            return dict(status='yielded', reason='sealed constructed encoding block')
        block = root / f'cost-{start}'
        stage(encode, block, src_inputs, dict(phase='cost', start=start, count=2), verifying)
        blocks.append(str(block))
    write_equal(root / 'COST_BANK.json', blocks)
    cost = stage(reduce, root / 'cost-reduce', dict(**src_inputs, blocks=str(root / 'COST_BANK.json')),
                 dict(operation='cost_reduce'), verifying)
    # Actual original cost function, with its load boundary supplied the exact
    # constructed whole-writer projection. No original module global is changed.
    oracle_coverage = SimpleNamespace(**dict(old_coverage.__dict__, load=lambda _i, _c: copy.deepcopy(rows)))
    measure = exact.copied(exact.measure, coverage=oracle_coverage)
    oracle_dir = root / 'original-cost'
    oracle_dir.mkdir(parents=True, exist_ok=True)
    original_config = dict(mode='constructed', seed=stats.SEED, sample_denominator=1,
        minimum_occurrences=1, minimum_writers=1, permutation_draws=20, bootstrap_draws=2000, safety_multiplier=3)
    work, _ = measure(oracle_dir, original, original_config)
    if read(cost / 'output/WORK.json') != work:
        raise ValueError('Sample complete cost work differs from the original handler')
    refuse(lambda: encode.collect(src_inputs, 'cost', blocks[:-1]))
    refuse(lambda: encode.collect(src_inputs, 'cost', blocks + blocks[:1]))
    refuse(lambda: encode.collect(dict(source_root=str(all_scope)), 'cost', blocks))
    reductions, testlists = {}, {}
    for scope in ('whole', 'thirds'):
        paths = []
        for start in range(0, 200, 10):
            if (root / 'YIELD_REQUEST.json').exists():
                return dict(status='yielded', reason='sealed constructed reference block')
            block = root / f'{scope}-discovery-{start:03d}'
            stage(coverage, block, src_inputs,
                  dict(operation='reference_block', scope=scope, side='discovery', start=start, count=10), verifying)
            paths.append(str(block))
        listing = root / (scope + '-DISCOVERY.json')
        write_equal(listing, paths)
        reductions[scope] = stage(coverage, root / (scope + '-discovery'), dict(**src_inputs, blocks=str(listing)),
                                  dict(operation='discovery_reduce', scope=scope), verifying)
        paths = []
        args = dict(**src_inputs, discovery_root=str(reductions[scope]))
        for start in range(0, 200, 10):
            if (root / 'YIELD_REQUEST.json').exists():
                return dict(status='yielded', reason='sealed constructed held-out block')
            block = root / f'{scope}-test-{start:03d}'
            stage(coverage, block, args,
                  dict(operation='reference_block', scope=scope, side='test', start=start, count=10), verifying)
            paths.append(str(block))
        listing = root / (scope + '-TEST.json')
        write_equal(listing, paths)
        testlists[scope] = str(listing)
    cov = stage(coverage, root / 'coverage', dict(**src_inputs,
        whole_discovery=str(reductions['whole']), thirds_discovery=str(reductions['thirds']),
        whole_blocks=testlists['whole'], thirds_blocks=testlists['thirds']), dict(operation='coverage_reduce'), verifying)
    cfg_old = dict(mode='constructed', coarse=False, seed=stats.SEED, surrogate_draws=200,
                   bootstrap_draws=2000, minimum_occurrences=1, minimum_writers=1)
    original_run = exact.copied(old_coverage.run, load=lambda _i, _c: copy.deepcopy(rows))
    old_cov = original_run(root / 'original-coverage', {k: original[k] for k in exact.pilot.PREP_KEYS}, cfg_old, verifying)
    if read(cov / 'output/WB1_COVERAGE_RESULT.json') != old_cov:
        raise ValueError('Complete original coverage output differs at sample scope')
    probe = stage(pilot, root / 'coverage-pilot', src_inputs, {}, verifying)
    stage(forecast, root / 'pilot-forecast', dict(pilot_root=str(probe)), {}, verifying)
    for scope in ('whole', 'thirds'):
        for draw in range(10):
            if read(probe / 'output' / f'{scope}-discovery-{draw:02d}.json')['values'] != read(
                    root / f'{scope}-discovery-000/output/draw-{draw:03d}.json')['values']:
                raise ValueError('Sample pilot changed an original global reference index')
    # Independent constructed occurrences exercise every selected raw session,
    # even when tiny-world discovered primary pieces are unsupported.
    legacy = Path(original['preparation_complete']).parent.parent / 'coverage'
    observed = copy.deepcopy(read(legacy / 'output/WB1_COVERAGE_RESULT.json'))
    observed['whole']['occurrences'] = [r for r in observed['whole']['occurrences'] if r['writer'] in chosen]
    effect_cov = root / 'constructed-occurrences'
    write_equal(effect_cov / 'output/WB1_COVERAGE_RESULT.json', observed)
    sealed(effect_cov, coverage, src_inputs, dict(operation='coverage_reduce'))
    effect_args = dict(**src_inputs, coverage_root=str(effect_cov))
    effect_blocks = []
    for start in range(0, 6, 2):
        block = root / f'effects-{start}'
        stage(encode, block, effect_args, dict(phase='effects', start=start, count=2), verifying)
        effect_blocks.append(str(block))
    write_equal(root / 'EFFECT_BANK.json', effect_blocks)
    final = stage(reduce, root / 'effects', dict(**effect_args, blocks=str(root / 'EFFECT_BANK.json')),
                  dict(operation='effects_reduce'), verifying)
    oracle_cov = root / 'original-occurrences'
    write_equal(oracle_cov / 'output/WB1_COVERAGE_RESULT.json', observed)
    sealed(oracle_cov, old_coverage, {k: original[k] for k in exact.pilot.PREP_KEYS}, cfg_old)
    oracle_effect_args = dict(coverage_complete=str(oracle_cov / 'COMPLETE.json'),
        coverage_result=str(oracle_cov / 'output/WB1_COVERAGE_RESULT.json'),
        **{k: original[k] for k in ('source_inputs', 'content_model', 'content_complete')})
    oracle_effect = root / 'original-effects'
    oracle_effect.mkdir(parents=True, exist_ok=True)
    original_result = effects.calculate(oracle_effect, oracle_effect_args,
        dict(mode='constructed', permutation_draws=200, seed=stats.SEED), verifying)
    actual = read(final / 'output/WB1_RESULT.json')
    if any(actual[k] != value for k, value in original_result.items() if k != 'bindings'):
        raise ValueError('Sample effects or classes differ from the original full handler')
    if gzread(final / 'output/WB1_EFFECT_ROWS.json.gz') != read(oracle_effect / 'WB1_EFFECT_ROWS.json'):
        raise ValueError('Original sample raw effect rows or encoder values differ')
    for stage_root in (cost, cov, final):
        scope = read(stage_root / 'output/SAMPLE_SCOPE.json')
        if scope['writers'] != 3 or scope['sessions'] != 6 or not scope['sample_scoped'] or 'selected_writers' in scope:
            raise ValueError('Sample scope was lost or identity entered aggregate sidecar')
    result = dict(fixture_only=True, constructed_writers=4, selected_constructed_writers=3, selected_sessions=6,
                  human_sample_count_or_forecast_chosen=False, whole_writer_and_partition_preserved=True,
                  constructed_budget_arithmetic_and_nontrigger_overbudget_reset_refusals=True,
                  selection_order_and_outcome_independent=True, full_population_projection_equal=True,
                  original_cost_work_equal=True, original_complete_coverage_equal=True,
                  all_four_reference_banks=200, requested_bootstrap_draws=2000,
                  below_floor_original_disposition_preserved=True, original_effect_rows_and_classes_equal=True,
                  original_five_percent_reference_indices_equal=True,
                  original_and_scoped_module_identities_not_interchangeable=True,
                  missing_session_extra_writer_changed_partition_refused=True,
                  missing_duplicate_mixed_scope_blocks_and_bad_scope_configs_refused=True,
                  constructed_dependency_receipts_not_production_admission=True)
    source.checked(root / 'FIXTURE.json', result, verifying)
    return dict(verified=True, complete_sample_original_handler_replay=True) if verifying else dict(status='complete', fixture_only=True)


def execute(output, inputs, config):
    with threadpool_limits(limits=2):
        return run(output, inputs, config)


def verify(output, inputs, config):
    with threadpool_limits(limits=2):
        return run(output, inputs, config, True)
