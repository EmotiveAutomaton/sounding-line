"""Prepared native oracle/refusal fixture for bounded LA1 preparation.

Only constructed source data. The outer runtime supplies independent native
execute and verify. Local copied-checkpoint controls are labelled as such;
they do not impersonate a stopped native worker or claim a native resume.
"""
from pathlib import Path
from types import FunctionType
import gzip
import json
import shutil

from . import week5_la_prepare_v1 as bounded
from . import week5_la_pipeline_v3 as original
from .timing_census import read, filehash
from .timing_p6 import gzread, gzip_equal, write_equal


def source(root):
    root = Path(root)
    acts, laughs, metadata = [], [], {}
    for m, corpus, size in [('constructed-A', 'AMI', 29), ('constructed-B', 'ICSI', 28), ('constructed-C', 'AMI', 27)]:
        metadata[m] = dict(corpus=corpus, duration=200., speakers={})
        for j in range(size):
            # Overlapping acts and an exact stable-sort tie exercise the
            # completed-talk boundary and original input-order preservation.
            start = 3. * j
            end = start + (9. if j == 9 else 1.)
            if j == 15:
                start, end = 42., 43.
            speaker = 'speaker-' + str(j % 2)
            if j == 15:
                speaker = 'speaker-0'
            words = [dict(kind='word', text='constructed', start=start, end=start + .2),
                     dict(kind='word', text='laugh', start=start + .2, end=start + .4),
                     dict(kind='word', text=str(j), start=start + .4, end=end),
                     dict(kind='vocalsound', text='LAUGH_ANNOTATION', start=start, end=end),
                     dict(kind='word', text='DROP_MARK', annotation='while laughing', start=start, end=end)]
            acts.append(dict(id=m + '-act-' + str(j), meeting=m, speaker=speaker,
                             corpus=corpus, act_type='inform', start=start, end=end, words=words))
            metadata[m]['speakers'][speaker] = dict(native_language='constructed')
            if j % 4 == 0:
                laughs.append(dict(meeting=m, speaker=speaker, start=end, end=end + .3, label='vocal'))
            if j % 7 == 0:
                laughs.append(dict(meeting=m, speaker='speaker-1', start=end + 1., end=end + 1.5, label='speech_comment'))
    metadata['constructed-empty'] = dict(corpus='ICSI', duration=1., speakers={})
    # Preserve a nontrivial source order, including the source ordering of ties.
    acts = acts[29:] + acts[:29]
    for name, value in [('ACTS.json.gz', acts), ('LAUGHS.json.gz', laughs), ('METADATA.json.gz', metadata)]:
        gzip_equal(root / 'output' / name, value)
    outputs = {'output/' + n: filehash(root / 'output' / n)
               for n in ('ACTS.json.gz', 'LAUGHS.json.gz', 'METADATA.json.gz')}
    write_equal(root / 'COMPLETE.json', dict(status='COMPLETE', fresh_process_verified=True,
                constructed_dependency_fixture=True, not_a_production_runtime_admission=True, outputs=outputs))
    return root


def configs():
    primary = dict(card='LA1', operation='prepare')
    return [primary, dict(primary, window=1.), dict(primary, window=3.),
            dict(primary, window=5., left=5.), dict(primary, history_acts=3),
            dict(primary, history_acts=10), dict(primary, corpus='AMI'), dict(primary, corpus='ICSI'),
            dict(primary, laugh_scope='others'), dict(primary, laugh_scope='own'),
            dict(primary, label='vocal_and_speech')]


def finish(root, inputs, config, verifying=False):
    fn = bounded.verify if verifying else bounded.execute
    for _ in range(300):
        result = fn(root, inputs, config)
        finished = result.get('verified') if verifying else result.get('status') == 'complete'
        if finished:
            return result
        if result.get('status') != 'yielded':
            raise ValueError('Bounded handler neither completed nor checkpointed')
    raise ValueError('Constructed checkpoint continuation made insufficient progress')


def bank_hashes(root):
    root = Path(root)
    files = ['BATCHES.json', 'SUMMARY.json'] + [r['file'] for r in read(root / 'BATCHES.json')]
    return {name: filehash(root / name) for name in files}


def copied(root, name, source_root):
    target = Path(root) / name
    if target.exists():
        raise ValueError('Fixture copy destination must be fresh')
    shutil.copytree(source_root, target)
    return target


def refuse(fn):
    try:
        fn()
    except (ValueError, KeyError, FileNotFoundError):
        return
    raise ValueError('Changed constructed source/checkpoint was accepted')


def local_controls(root, inputs, config):
    root = Path(root)
    root.mkdir(parents=True, exist_ok=True)
    base = root / 'partial-buffer'
    calls = 0
    def stop_during_buffer(output, began, wall):
        nonlocal calls
        calls += 1
        return calls >= 15
    fn = FunctionType(bounded.prepare.__code__, dict(bounded.prepare.__globals__, interrupted=stop_during_buffer),
                      bounded.prepare.__name__, bounded.prepare.__defaults__, bounded.prepare.__closure__)
    first = fn(base, inputs, config)
    state, _, _ = bounded.restore(base, 'execute', read(base / 'PREPARATION_BINDING.json'))
    if first.get('status') != 'yielded' or not 0 < len(state['buffer']) < 8:
        raise ValueError('Constructed mid-block continuation did not preserve pending source rows')
    continuation = copied(root, 'copied-partial', base)
    finish(continuation, inputs, config)
    finish(continuation, inputs, config, True)
    expected = root / 'original'
    original.prepare(expected, inputs, config)
    if bank_hashes(expected) != bank_hashes(continuation):
        raise ValueError('Copied partial-block continuation differs from original')
    retained = bank_hashes(continuation)
    finish(continuation, inputs, config)
    if retained != bank_hashes(continuation):
        raise ValueError('Complete source execute reentry rewrote numeric/source bytes')

    early = root / 'preload'
    early.mkdir()
    write_equal(early / 'YIELD_REQUEST.json', dict(reason='constructed before-source control'))
    result = bounded.execute(early, inputs, config)
    if result.get('status') != 'yielded' or (early / 'batches').exists():
        raise ValueError('Pre-source resource request was not honored')
    # Only the fixture's own control marker is removed; production markers
    # and native identities are never manipulated by this fixture.
    (early / 'YIELD_REQUEST.json').unlink()
    finish(early, inputs, config)

    bad_batch = copied(root, 'bad-batch', continuation)
    row = read(bad_batch / 'BATCHES.json')[0]
    with (bad_batch / row['file']).open('ab') as stream:
        stream.write(b'changed')
    refuse(lambda: bounded.execute(bad_batch, inputs, config))
    bad_state = copied(root, 'bad-checkpoint', base)
    entry = next((bad_state / 'checkpoints/execute').glob('*.json.gz'))
    with entry.open('ab') as stream:
        stream.write(b'changed')
    refuse(lambda: bounded.execute(bad_state, inputs, config))
    bad_cursor = copied(root, 'bad-cursor', base)
    data_path = next((bad_cursor / 'checkpoints/execute').glob('*.json.gz'))
    data = gzread(data_path)
    data['state']['cursor'] = [100000, 0]
    data_path.write_bytes(gzip.compress(json.dumps(data, ensure_ascii=False, sort_keys=True, allow_nan=False).encode(), mtime=0))
    seal_path = data_path.with_name(data_path.name.replace('.json.gz', '.seal.json'))
    seal = read(seal_path)
    seal['sha256'] = filehash(data_path)
    seal_path.write_text(json.dumps(seal, sort_keys=True) + '\n', encoding='utf8')
    refuse(lambda: bounded.execute(bad_cursor, inputs, config))
    changed_config = copied(root, 'changed-config', base)
    refuse(lambda: bounded.execute(changed_config, inputs, dict(config, history_acts=3)))
    refuse(lambda: bounded.execute(root / 'extra-reader', dict(inputs, selection_root='not-required'), config))
    extra_batch = copied(root, 'extra-batch', continuation)
    gzip_equal(extra_batch / 'batches/acts-999999.json.gz', [])
    refuse(lambda: bounded.verify(extra_batch, inputs, config))
    damaged_source = copied(root, 'changed-source', inputs['source_root'])
    with (damaged_source / 'output/ACTS.json.gz').open('ab') as stream:
        stream.write(b'changed')
    refuse(lambda: bounded.execute(root / 'changed-source-output', dict(source_root=str(damaged_source)), config))
    return dict(partial_buffer_copied_exactly=True, completed_execute_reentry=True,
                pre_source_yield=True, modified_batch_checkpoint_cursor_config_source_refused=True,
                unexpected_batch_and_extra_reader_input_refused=True,
                local_copy_control_only_not_a_native_resume=True)


def run(output, inputs, config, verifying=False):
    if inputs or config:
        raise ValueError('Bounded preparation fixture accepts no human or model inputs')
    root = Path(output)
    root.mkdir(parents=True, exist_ok=True)
    src = source(root / 'constructed-source')
    supplied = dict(source_root=str(src.resolve()))
    records = []
    for i, semantic in enumerate(configs()):
        expected, produced = root / f'case-{i:02d}/original', root / f'case-{i:02d}/bounded'
        operational = dict(semantic, max_new_blocks=1, max_wall_seconds=600)
        if not verifying:
            original.prepare(expected, supplied, semantic)
            finish(produced, supplied, operational)
        else:
            original.prepare(expected, supplied, semantic, True)
            # First independent outer verification starts from the actual
            # executed source bank, with no prior verification checkpoints.
            finish(produced, supplied, operational, True)
        if bank_hashes(expected) != bank_hashes(produced):
            raise ValueError('Original full source rows, global blocks or summary changed')
        if i == 0:
            summary = read(produced / 'SUMMARY.json')
            index = read(produced / 'BATCHES.json')
            rows = [row for item in index for row in gzread(produced / item['file'])]
            if summary['counts'] != dict(acts=84, insufficient_prior_history=15, supported_history=69) or summary['meetings'] != 4:
                raise ValueError('Constructed primary source census differs from known support')
            if (len(index) != 9 or index[-1]['rows'] != 5 or
                    not any(len({r['meeting'] for r in gzread(produced / item['file'])}) > 1 for item in index)):
                raise ValueError('Global eight-act boundary did not cross meetings as constructed')
            if any('LAUGH_ANNOTATION' in r['target'] or 'DROP_MARK' in r['target'] or 'laugh' not in r['target'] for r in rows):
                raise ValueError('Annotation removal or literal spoken laugh preservation differs')
        records.append(dict(case=i, semantic_config=semantic, source_bank=bank_hashes(produced)))
    controls = local_controls(root / ('independent-controls' if verifying else 'execute-controls'),
                              supplied, dict(card='LA1', operation='prepare', max_new_blocks=1, max_wall_seconds=600))
    value = dict(fixture_only=True, no_human_input=True, no_model_or_selected_reader=True,
                 original_v3_byte_identical_source_banks=records, declared_variant_count=len(records),
                 independently_replayed_original_and_bounded_handlers=True, controls=controls,
                 actual_stopped_native_checkpoint_chain_still_requires_owner_admission=True)
    if verifying:
        if read(root / 'FIXTURE.json') != value:
            raise ValueError('Preparation fixture evidence differs on independent replay')
        return dict(verified=True, complete_original_source_projection=True,
                    all_declared_source_variants=True, authentic_local_checkpoint_refusals=True)
    write_equal(root / 'FIXTURE.json', value)
    return dict(status='complete', scientific_admission=False)


def execute(output, inputs, config):
    return run(output, inputs, config)


def verify(output, inputs, config):
    return run(output, inputs, config, True)
