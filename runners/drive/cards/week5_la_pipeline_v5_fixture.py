"""Prepared actual tiny paired-model oracle, pause and refusal qualification.

Constructed AT selection only; copied local checkpoints are not a native
continuation claim. Actual paired pretrained latency/peak remain unmeasured.
"""
from pathlib import Path
from types import FunctionType
import json
import shutil
import time

from . import week5_la_pipeline_v3 as original
from . import week5_la_pipeline_v4 as old_collector
from . import week5_la_pipeline_v5 as paired
from . import week5_la_scoring_guard_v1 as guarded
from .week5_at_source import authenticate
from .week5_la_pipeline_v4_fixture import causal_loader, old_score
from .week5_la_score_fixture import masked_loader
from .timing_census import read, filehash
from .timing_p6 import gzip_equal, write_equal


def high_memory():
    # Constructed guard-control input, explicitly not a memory measurement.
    return dict(commit_headroom_bytes=100 * 2**30, ram_available_bytes=100 * 2**30)


def paired_call(root, inputs, config, verifying=False, *, gate=None, loads=None):
    loads = [] if loads is None else loads
    def causal(manifest):
        loads.append('causal')
        return causal_loader(manifest)
    def masked(manifest):
        loads.append('masked')
        return masked_loader(manifest)
    private_gate = FunctionType(guarded.load_gate.__code__, dict(guarded.load_gate.__globals__, memory=high_memory),
                               guarded.load_gate.__name__, guarded.load_gate.__defaults__, guarded.load_gate.__closure__)
    private_gate.__kwdefaults__ = guarded.load_gate.__kwdefaults__
    def admission(destination, stage):
        if gate is not None:
            return gate(destination, stage)
        return private_gate(destination, stage)
    fn = FunctionType(guarded.run.__code__, dict(guarded.run.__globals__, memory=high_memory,
                      load_model=causal, load_masked=masked, load_gate=admission), guarded.run.__name__,
                      guarded.run.__defaults__, guarded.run.__closure__)
    return fn(root, inputs, config, verifying)


def refuse(call):
    try:
        call()
    except (ValueError, KeyError, FileNotFoundError):
        return
    raise ValueError('Changed paired fixture condition was accepted')


def production_copy(source, destination):
    """Private execute-only copy; independent masked/causal replay starts empty."""
    source, destination = Path(source), Path(destination)
    for path in source.rglob('*'):
        if not path.is_file():
            continue
        relative = path.relative_to(source)
        if any(part in ('invocation_costs', 'guard_invocations', 'load_admissions', 'verified_acts', 'verify')
               for part in relative.parts):
            continue
        if path.name in ('PROGRESS.json', 'YIELD_REQUEST.json', 'VERIFY_INDEX.json') or path.name.startswith('causal-verify.'):
            continue
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists():
            if filehash(target) != filehash(path):
                raise ValueError('Copied fixture production checkpoint differs')
        else:
            shutil.copyfile(path, target)


def mutate_copy(source, destination, filename, change):
    if not destination.exists():
        shutil.copytree(source, destination)
        path = destination / filename
        path.write_text(json.dumps(change(read(path)), sort_keys=True) + '\n', encoding='utf8')
    return destination


def finish(root, inputs, config, verifying, outer):
    pauses = 0
    for _ in range(128):
        if (outer / 'YIELD_REQUEST.json').exists():
            return dict(status='yielded', reason='outer native request at constructed paired boundary')
        result = paired_call(root, inputs, config, verifying)
        if result.get('verified') or result.get('status') == 'complete':
            return dict(result, observed_quantum_pauses=pauses)
        if result.get('status') != 'yielded' or (root / 'YIELD_REQUEST.json').exists():
            raise ValueError('Constructed pair unexpectedly failed or requested native resource recovery')
        pauses += 1
    raise ValueError('Bounded constructed pair did not finish')


def run(output, inputs, config, verifying=False):
    if set(inputs) != {'constructed_root', 'prior_paired_fixture_root'} or config:
        raise ValueError('Completed constructed AT selection and LA idempotence proofs only')
    prior = authenticate(inputs['constructed_root'])
    paired_prior = authenticate(inputs['prior_paired_fixture_root'])
    if (read(prior / 'PLAN.json').get('module') != 'runners.drive.cards.week5_at_collect_v4_fixture' or
            not read(prior / 'output/FIXTURE.json').get('constructed_receipts_not_production_admission')):
        raise ValueError('Human selection inputs are excluded from paired fixture')
    if (read(paired_prior / 'PLAN.json').get('module') != 'runners.drive.cards.week5_la_pipeline_v4_fixture' or
            not read(paired_prior / 'output/FIXTURE.json').get('v3_v4_numeric_bytes_equal') or
            not read(paired_prior / 'VERIFIED.json').get('verified')):
        raise ValueError('Prior actual complete paired lifecycle qualification required')
    root = Path(output)
    root.mkdir(parents=True, exist_ok=True)
    if (root / 'YIELD_REQUEST.json').exists():
        return dict(status='yielded', reason='outer native request before paired fixture')
    selection = prior / 'output/selection'
    model = read(selection / 'output/RESULT.json')['selected_model']
    bank = read(prior / 'output/BANK.json')
    model_plan = read(Path(next(iter(bank[model].values()))) / 'PLAN.json')
    write_equal(root / 'masked.json', dict(model='constructed-masked', revision='fixture'))
    rows = [dict(id=f'constructed-pair-{i}', causal_prefix='a ' * (i + 1), target='b',
                 previous=previous, word_count=1, meeting='constructed')
            for i, previous in enumerate(('old words', 'older words here', ''))]
    gzip_equal(root / 'ROWS.json.gz', rows)
    args = dict(rows=str(root / 'ROWS.json.gz'), causal_manifest=model_plan['inputs']['model_manifest'],
                masked_manifest=str(root / 'masked.json'), selection_root=str(selection))
    options = dict(operation='score', max_new_mask_batches=1, max_wall_seconds=600)
    gzip_equal(root / 'CHAIN_ROWS.json.gz', [dict(rows[0], previous='x')])
    chain_args = dict(args, rows=str(root / 'CHAIN_ROWS.json.gz'))
    chain_options = dict(operation='score', max_new_mask_batches=2, max_wall_seconds=600)
    write_equal(root / 'CHAIN_INPUTS.json', chain_args)
    write_equal(root / 'CHAIN_CONFIG.json', chain_options)
    old_score(root / 'chain-original-v3', chain_args, chain_options,
              verifying=(root / 'chain-original-v3/COST.json').exists())
    target = root / 'paired'
    oracle = root / 'original-v3'
    old_score(oracle, args, options, verifying=(oracle / 'COST.json').exists())
    if not (target / 'COST.json').exists():
        first = paired_call(target, args, options)
        if first.get('status') != 'yielded' or first.get('completed') != 0 or first.get('new_mask_batches') != 1:
            raise ValueError('First masked tensor boundary did not preserve a partial act')
        if (target / 'act-000.json').exists():
            raise ValueError('Partial masked act incorrectly became a completed act')
        first_batch = target / 'within_act/act-000/masked/execute/before/000000.json'
        write_equal(root / 'FIRST_PARTIAL.json', dict(sha256=filehash(first_batch),
                    no_completed_act=True, native_continuation_proof=False))
        copied = root / 'partial-local-copy'
        production_copy(target, copied)
        copied_result = finish(copied, args, options, False, root)
        if copied_result.get('status') == 'yielded':
            return copied_result
    outcome = finish(target, args, options, False, root)
    if outcome.get('status') == 'yielded':
        return outcome
    numeric_names = [x['file'] for x in read(target / 'INDEX.json')] + ['INDEX.json', 'SUMMARY.json']
    if any(filehash(target / name) != filehash(oracle / name) for name in numeric_names):
        raise ValueError('Original and within-act paired numerical bytes differ')
    if filehash(target / 'within_act/act-000/masked/execute/before/000000.json') != read(root / 'FIRST_PARTIAL.json')['sha256']:
        raise ValueError('Original first masked checkpoint changed')
    original_cost = filehash(target / 'COST.json')
    if paired_call(target, args, options).get('status') != 'complete' or filehash(target / 'COST.json') != original_cost:
        raise ValueError('Complete execute reentry changed retained original cost')
    # Outer verification gets a NEW replay prefix and recomputes every original
    # masked batch. Execute prefixes are copied, never verification prefixes.
    replay = target
    if verifying:
        replay = root / 'outer_replays' / str(time.time_ns())
        production_copy(target, replay)
    replay_result = finish(replay, args, options, True, root)
    if replay_result.get('status') == 'yielded':
        return replay_result
    if filehash(replay / 'COST.json') != original_cost or any(filehash(replay / name) != filehash(oracle / name) for name in numeric_names):
        raise ValueError('Independent bounded replay changed completed numeric/cost bytes')

    # The original collection contract MUST refuse this new unreviewed identity.
    refuse(lambda: old_collector.producer(target, dict(module=guarded.__name__)))
    refuse(lambda: paired.score(root / 'unguarded', args, options))
    refuse(lambda: paired_call(root / 'unknown-config', args, dict(options, skip_masks=True)))
    refuse(lambda: paired_call(root / 'partial-selection', dict(args, selection_root=str(root / 'missing-selection')), options))
    bad_causal = mutate_copy(target, root / 'bad-causal-seal', 'within_act/act-000/causal-execute.seal.json',
                            lambda value: dict(value, sha256='0' * 64))
    # A full act skips execute internals by design. Exercise its incomplete
    # phase by copying only the retained partial tree, not by deleting outputs.
    partial = root / 'partial-local-copy'
    bad_phase = root / 'bad-phase-partial'
    if not bad_phase.exists():
        bad_phase.mkdir(parents=True)
        for name in ('CHECKPOINT_PRODUCER.json', 'within_act/act-000/causal-execute.json',
                     'within_act/act-000/causal-execute.seal.json'):
            destination = bad_phase / name
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(bad_causal / name, destination)
    refuse(lambda: paired_call(bad_phase, args, options))
    bad_mask = mutate_copy(replay, root / ('bad-mask-verify' if verifying else 'bad-mask'),
                          'within_act/act-000/masked/verify/before/000000.seal.json', lambda value: dict(value, sha256='0' * 64))
    refuse(lambda: paired_call(bad_mask, args, options, True))
    bad_rows = dict(args, rows=str(root / 'CHANGED_ROWS.json.gz'))
    gzip_equal(bad_rows['rows'], [dict(rows[0], previous='different')]+rows[1:])
    refuse(lambda: paired_call(target, bad_rows, options))
    write_equal(root / 'CHANGED_MASKED.json', dict(model='constructed-masked', revision='different'))
    refuse(lambda: paired_call(target, dict(args, masked_manifest=str(root / 'CHANGED_MASKED.json')), options))

    loads = []
    control_root = root / 'load_refusal_controls' / str(time.time_ns())
    before = control_root / 'before'
    def refuse_first(destination, stage):
        guarded.load_gate(destination, stage, memory_reader=lambda: dict(commit_headroom_bytes=25 * 2**30,
                                                                       ram_available_bytes=100 * 2**30))
    pre = paired_call(before, args, options, gate=refuse_first, loads=loads)
    if pre.get('status') != 'yielded' or loads:
        raise ValueError('Before-load refusal loaded a model')
    between = control_root / 'between'
    loads = []
    def refuse_second(destination, stage):
        guarded.load_gate(destination, stage, memory_reader=high_memory if stage == 'causal' else
            lambda: dict(commit_headroom_bytes=25 * 2**30, ram_available_bytes=100 * 2**30))
    middle = paired_call(between, args, options, gate=refuse_second, loads=loads)
    if middle.get('status') != 'yielded' or loads != ['causal']:
        raise ValueError('Between-load refusal did not prevent the second model load')
    costs = [read(p) for p in (target / 'invocation_costs').glob('*.json')]
    if not {'yielded', 'complete', 'verified'} <= {x['status'] for x in costs}:
        raise ValueError('Complete paired invocation history is missing')
    result = dict(fixture_only=True, no_human_input=True, actual_tiny_paired_models=True,
        prior_at_complete_sha256=filehash(prior / 'COMPLETE.json'), prior_la_complete_sha256=filehash(paired_prior / 'COMPLETE.json'),
        original_numeric_bytes_equal=True, within_act_execute_and_verify_pause=True,
        retained_causal_and_masked_checkpoints=True, complete_cost_reentry=True,
        original_support_refusal_unchanged=True, changed_input_and_checkpoint_refusals=True,
        missing_selection_unknown_config_unguarded_refusals=True, old_collector_refuses_new_producer=True,
        before_and_between_load_refusal=True, synthetic_guard_control_not_memory_measurement=True,
        local_copy_not_native_continuation_proof=True, every_outer_verify_reforwards_all_masks=True,
        human_paired_load_or_latency_qualified=False, collector_admission=False)
    if verifying:
        if read(root / 'FIXTURE.json') != result:
            raise ValueError('Constructed paired integration replay differs')
        return dict(verified=True, complete_constructed_paired_checkpoint_integration=True)
    write_equal(root / 'FIXTURE.json', result)
    return dict(status='complete', fixture_only=True)


def execute(output, inputs, config):
    return run(output, inputs, config)


def verify(output, inputs, config):
    return run(output, inputs, config, True)
