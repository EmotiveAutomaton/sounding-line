"""Unrun constructed full-output and interruption fixture for CH1 collection.

No engine, human source, statistical association or live runtime is invoked.
Literal constructed scores exercise the full original collector and successor.
In-process copy/request cases qualify handler semantics only; counted native
exit/lease/watch and runtime-copy integration remain separate owner gates.
"""
from pathlib import Path
import gzip
import json
import math
import os
import shutil

from . import week5_ch_collection as original
from . import week5_ch_collection_bounded_v1 as bounded
from . import week5_ch_pipeline_checkpoint as ck
from .week5_ch_engine import score_key
from .week5_ch_source import digest, write_json


def spec(path):
    return dict(path=str(path), sha256=digest(path))


def snapshot(root):
    return {path.relative_to(root).as_posix(): digest(path)
            for path in sorted(root.rglob('*')) if path.is_file()}


def clone(source, attempt):
    target = attempt / 'output'
    shutil.copytree(source, target)
    write_json(attempt / 'RESUMED_FROM.json', dict(
        constructed_handler_copy_only=True, copied=snapshot(target)))
    return target


def request(root, number):
    write_json(root / 'YIELD_REQUEST.json', dict(
        reason='owner_cancel', requested_at='2026-11-08T08:00:00Z',
        constructed_fixture=True, request_number=number), mutable=True)


def world(root, defect=None, single_month=False):
    root.mkdir(parents=True, exist_ok=False)
    positions = []
    months = ('2017-04',) if single_month else ('2017-04', '2017-05', '2026-07')
    for month in months:
        for i in range(60):
            positions.append(dict(
                player=f'constructed-{i%12:02}', month=month, ordinal=i,
                rating=1600 if i<40 else 2000 if i<50 else 2400,
                uci='a2a3' if i%13==0 else 'e2e4' if i%3 else 'd2d4',
                fen='constructed-no-engine-source'))
    if defect == 'duplicate_roster':
        positions.append(dict(positions[0]))
    original.write_rows(root / 'positions.gz', positions)
    batches = []
    # Small disjoint batches exercise stable sorted file order independently
    # from roster order and batch order. The final joined order is key-sorted.
    for start in range(0, len(positions), 17):
        directory = root / f'batch-{start:04}'
        directory.mkdir()
        scores = directory / 'scores'
        scores.mkdir()
        bindings = {}
        for offset, row in enumerate(positions[start:start+17], start):
            if defect == 'missing_score' and offset == len(positions)-1:
                continue
            mating = row['ordinal'] >= 50 or row['ordinal']%11 == 0
            top = [dict(move='e2e4', cp=0.), dict(move='d2d4', cp=0. if row['ordinal']%2 else -50.)]
            value = dict(position=row, node_limit=1000000,
                         engine=dict(mate_sentinel_used=mating, top=top, k50=2))
            path = scores / (score_key(row, 1000000)+'.json')
            write_json(path, value)
            bindings[path.name] = digest(path)
        if defect == 'extra_score' and start == 0:
            row = dict(positions[0], ordinal=99999)
            value = dict(position=row, node_limit=1000000,
                         engine=dict(mate_sentinel_used=False, top=top, k50=2))
            path = scores / (score_key(row, 1000000)+'.json')
            write_json(path, value)
            bindings[path.name] = digest(path)
        write_json(directory / 'VERIFY.json', dict(
            all_scores_equal=not (defect=='failed_replay' and start==0),
            verified_positions=len(bindings)))
        write_json(directory / 'BATCH.json', dict(
            node_limit=300000 if defect=='wrong_nodes' and start==0 else 1000000,
            new_positions=len(bindings), reused_positions=0))
        write_json(directory / 'SCORE_BINDINGS.json', bindings)
        batches.append(dict(path=str(scores), verify=spec(directory/'VERIFY.json'),
                            report=spec(directory/'BATCH.json'), score_bindings=spec(directory/'SCORE_BINDINGS.json')))
        if defect == 'changed_score' and start == 0:
            first = sorted(scores.glob('*.json'))[0]
            first.write_text('{}\n', encoding='utf8', newline='\n')
    if defect == 'duplicate_batch':
        batches.append(batches[0])
    write_json(root / 'BATCHES.json', dict(batches=batches))
    return dict(positions=spec(root/'positions.gz'), batches=spec(root/'BATCHES.json')), dict(
        constructed_fixture=True, expected_positions=len(positions), nodes=1000000)


def compare(left, right):
    for name in bounded.FILES:
        if (left/name).read_bytes() != (right/name).read_bytes():
            raise AssertionError('Original full-output parity differs: '+name)


def refuses(call):
    try:
        call()
    except ValueError:
        return
    raise AssertionError('Malformed source or false output was accepted')


def check_counts(output, single_month=False):
    temperatures = json.loads((output/'TEMPERATURES.json').read_text(encoding='utf8'))
    fits = temperatures['fits']
    assert temperatures['counts']['mating_entropy_excluded'] > 0
    assert temperatures['counts']['uncalibrated_entropy'] > 0
    if single_month:
        assert all(fit['calibration_month'] is None and fit['supported']==0 for fit in fits)
    else:
        assert any(fit['status']=='fitted' and fit['supported']>=20 for fit in fits)
        assert any(0<fit['supported']<20 for fit in fits)
        assert any(fit['outside_top_five']>0 for fit in fits)
        assert all(fit['calibration_month'] != fit['target_month'] for fit in fits)
    uniform = 0
    with gzip.open(output/bounded.FILES[0], 'rt', encoding='utf8') as stream:
        for line in stream:
            row = json.loads(line)
            if row['mate_sentinel_used']:
                assert row['entropy'] is None and row['entropy_fixed100'] is None
            elif row['top'][0]['cp'] == row['top'][1]['cp']:
                assert abs(row['entropy_fixed100']-math.log(2)) < 1e-15
                uniform += 1
    assert uniform > 0


def exercise(root, owner_root):
    root.mkdir(parents=True, exist_ok=False)
    check = lambda: ck.require(owner_root)
    check()
    inputs, config = world(root/'inputs')
    original.execute(root/'original', inputs, config)
    assert bounded.execute(root/'uninterrupted', inputs, config)['status']=='complete'
    compare(root/'original', root/'uninterrupted')
    check_counts(root/'uninterrupted')
    assert bounded.verify(root/'uninterrupted', inputs, config)['verified']
    check()

    # Actual exact handler row quantum, not a synthesized yielded return.
    paused = root/'execute_pilot'
    result = bounded.execute(paused, inputs, dict(config, max_new_draws=3))
    assert result['status']=='yielded' and result['new_completed_units']==3
    request(paused, 1)
    before = snapshot(paused)
    resumed = clone(paused, root/'continued_attempt')
    assert bounded.execute(resumed, inputs, config)['status']=='complete'
    compare(root/'original', resumed)
    assert snapshot(paused)==before
    verification = bounded.verify(resumed, inputs, dict(config, max_new_draws=3))
    assert verification['status']=='yielded' and verification['operation']=='verify'
    assert verification['new_completed_units']==3 and not verification['verification_prefix_credited']
    saved_verification = snapshot(resumed/'independent_collection-000001')
    assert bounded.verify(resumed, inputs, config)['verified']
    assert snapshot(resumed/'independent_collection-000001')==saved_verification
    assert (resumed/'independent_collection-000002/COLLECTION.json').exists()
    request(resumed, 2)
    assert bounded.verify(resumed, inputs, config)['status']=='yielded'
    check()

    # Inject only a genuine owner request while the real objective iterates.
    # The original numeric objective and scipy optimizer remain unchanged.
    saved_fit = bounded.fit_stream
    calls = 0
    def interrupted_fit(con, target, donor, band, original_check):
        def observed_check():
            nonlocal calls
            calls += 1
            if calls == 100:
                request(root/'fit_pause', 3)
            original_check()
        return saved_fit(con, target, donor, band, observed_check)
    bounded.fit_stream = interrupted_fit
    try:
        interrupted = bounded.execute(root/'fit_pause', inputs, config)
    finally:
        bounded.fit_stream = saved_fit
    assert interrupted['status']=='yielded' and interrupted['phase']=='fits'
    assert calls>=100
    fits_before = snapshot(root/'fit_pause')
    fit_resume = clone(root/'fit_pause', root/'fit_continued_attempt')
    assert bounded.execute(fit_resume, inputs, config)['status']=='complete'
    compare(root/'original', fit_resume)
    assert snapshot(root/'fit_pause')==fits_before
    check()

    saved_advance = bounded.Control.advance
    def interrupted_export(self, phase, done, total):
        saved_advance(self, phase, done, total)
        if phase=='gzip_rows_restart_on_interrupt' and done==3:
            request(root/'gzip_pause', 4)
    bounded.Control.advance = interrupted_export
    try:
        interrupted = bounded.execute(root/'gzip_pause', inputs, config)
    finally:
        bounded.Control.advance = saved_advance
    assert interrupted['status']=='yielded' and interrupted['phase']=='gzip'
    assert not (root/'gzip_pause/COLLECTION.json').exists()
    gzip_before = snapshot(root/'gzip_pause')
    gzip_resume = clone(root/'gzip_pause', root/'gzip_continued_attempt')
    # Exact N-row publication quantum must complete, not require N+1 units.
    assert bounded.execute(gzip_resume, inputs, dict(config, max_new_draws=config['expected_positions']))['status']=='complete'
    compare(root/'original', gzip_resume)
    assert snapshot(root/'gzip_pause')==gzip_before
    assert bounded.verify(gzip_resume, inputs, config)['verified']
    check()

    single_inputs, single_config = world(root/'single_inputs', single_month=True)
    original.execute(root/'single_original', single_inputs, single_config)
    assert bounded.execute(root/'single_bounded', single_inputs, single_config)['status']=='complete'
    compare(root/'single_original', root/'single_bounded')
    check_counts(root/'single_bounded', True)
    assert bounded.verify(root/'single_bounded', single_inputs, single_config)['verified']

    negative = ('duplicate_roster', 'missing_score', 'extra_score', 'duplicate_batch',
                'wrong_nodes', 'failed_replay', 'changed_score')
    for defect in negative:
        check()
        bad_inputs, bad_config = world(root/('inputs_'+defect), defect)
        refuses(lambda: bounded.execute(root/('refused_'+defect), bad_inputs, bad_config))
    refuses(lambda: bounded.execute(root/'wrong_count', inputs, dict(config, expected_positions=config['expected_positions']+1)))
    wrong_pin = dict(inputs, positions=dict(inputs['positions'], sha256='0'*64))
    refuses(lambda: bounded.execute(root/'wrong_pin', wrong_pin, config))
    damaged = clone(paused, root/'damaged_checkpoint_attempt')
    with (damaged/'PRIVATE_COLLECTION.sqlite').open('ab') as stream:
        stream.write(b'constructed checkpoint corruption')
    refuses(lambda: bounded.execute(damaged, inputs, config))
    check()

    # A self-consistent false seal must still fail fresh raw-score replay.
    tampered = root/'tampered_publication'
    shutil.copytree(root/'uninterrupted', tampered)
    with gzip.open(tampered/bounded.FILES[0], 'rt', encoding='utf8') as stream:
        rows = [json.loads(line) for line in stream]
    rows[0]['entropy_fixed100'] = 123.0
    replacement = tampered/'constructed_replacement.gz'
    original.write_rows(replacement, rows)
    os.replace(replacement, tampered/bounded.FILES[0])
    collection = json.loads((tampered/'COLLECTION.json').read_text(encoding='utf8'))
    collection['rows_sha256'] = digest(tampered/bounded.FILES[0])
    write_json(tampered/'COLLECTION.json', collection, mutable=True)
    seal = json.loads((tampered/'SOURCE_SEAL.json').read_text(encoding='utf8'))
    seal['files'] = {name:digest(tampered/name) for name in seal['files']}
    write_json(tampered/'SOURCE_SEAL.json', seal, mutable=True)
    refuses(lambda: bounded.verify(tampered, inputs, config))
    result = dict(
        constructed=True, positions=config['expected_positions'],
        original_all_three_files_byte_equal=True,
        exact_numeric_order_and_temperature_fits=True,
        complete_fresh_source_replay=True, exact_row_quantum_execute_and_verify=True,
        unchanged_predecessors=True, optimizer_and_gzip_actual_owner_yield=True,
        partial_optimizer_and_gzip_not_reused=True,
        exact_final_gzip_quantum=True, single_month_fallback=True,
        uniform_two_choice_closed_form=True, mating_entropy_unavailable=True,
        malformed_inputs_refused=len(negative)+3, resealed_false_output_refused=True,
        native_runtime_integration=False, scale_qualification=False,
        scientific_admission=False)
    write_json(root/'FIXTURE.json', result)
    return result


def execute(output, inputs, config):
    if inputs or config != {'constructed_fixture':True}:
        raise ValueError('Exact source-free fixture configuration required')
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    try:
        result = exercise(output/'constructed_execution', output)
    except ck.YieldRequested:
        return dict(status='yielded', reason='Owner request during constructed fixture; restart fresh',
                    native_runtime_integration=False)
    return dict(status='complete', **result)


def verify(output, inputs, config):
    if inputs or config != {'constructed_fixture':True}:
        raise ValueError('Exact source-free fixture configuration required')
    output = Path(output)
    try:
        replay = exercise(output/'constructed_independent_replay', output)
    except ck.YieldRequested:
        return dict(status='yielded', reason='Owner request during constructed replay; restart fresh',
                    verification_prefix_credited=False)
    original_result = json.loads((output/'constructed_execution/FIXTURE.json').read_text(encoding='utf8'))
    if replay != original_result:
        raise ValueError('Independent complete collection fixture differs')
    return dict(verified=True, complete_recalculation=True, scientific_admission=False,
                native_runtime_integration=False)
