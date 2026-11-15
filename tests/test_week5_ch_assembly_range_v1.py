"""Constructed-only exact-union evidence checks; no engine or native starts.

DESIGN CHECK: LESSONS 3-5. Literal expected ordinals 0..10 must be covered
once across retained COMPLETE, FAILED, PAUSED and range evidence. Native
identities are explicitly mocked only inside these isolated fixtures.
"""
import copy
import importlib.util
from pathlib import Path
from types import SimpleNamespace
import io

import pytest

from runners.drive.cards import week5_ch_assembly_range_v1 as assembly
from runners.drive.cards import week5_ch_queue_backhalf_v1 as original
from runners.drive.cards import week5_ch_queue_range_v1 as ranged
from runners.drive.cards import week5_ch_manifest_range_v1 as ranges
from runners.drive.cards import week5_ch_engine_bounded as engine
from runners.drive.cards.week5_ch_source import write_json, digest
from runners.drive.cards.week5_resume import output_manifest as original_pause_inventory


def test_metadata_reader_tiny_file_keeps_exact_json(tmp_path):
    path = tmp_path / 'tiny.json'
    path.write_bytes(b'{"small":true}')
    assert assembly.read(path) == {'small': True}


def test_metadata_reader_refuses_oversize_before_open(tmp_path, monkeypatch):
    path = tmp_path / 'too-big.json'
    path.write_bytes(b' ' * 17)
    monkeypatch.setattr(assembly, 'METADATA_CAP', 16)
    def forbidden_open(*args, **kwargs): raise AssertionError('Oversize metadata must not open')
    monkeypatch.setattr(Path, 'open', forbidden_open)
    with pytest.raises(ValueError, match='explicit bound'): assembly.read(path)


@pytest.mark.parametrize('changed', [b'{"x":1} ', b'{}'])
def test_metadata_reader_refuses_changed_size(tmp_path, monkeypatch, changed):
    path = tmp_path / 'changed.json'
    path.write_bytes(b'{"x":1}')
    real_open = Path.open
    monkeypatch.setattr(Path, 'open', lambda self, *a, **kw: io.BytesIO(changed) if self == path else real_open(self, *a, **kw))
    with pytest.raises(ValueError, match='size changed'): assembly.read(path)


def fixture_class():
    path = Path(__file__).with_name('test_week5_ch_queue_range_v1.py')
    spec = importlib.util.spec_from_file_location('constructed_range_fixture_only', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.FakeScorer


def world(tmp_path, monkeypatch):
    scorer = fixture_class()
    scorer.calls = []
    monkeypatch.setattr(engine, 'Scorer', scorer)
    monkeypatch.setattr(assembly, 'is_same_live_process', lambda _: False)
    rows = [dict(ordinal=i, fen='constructed', uci='e2e4', month='2017-04',
                 player='constructed-' + str(i)) for i in range(11)]
    original.write_positions(tmp_path / 'positions.gz', rows)
    (tmp_path / 'engine').write_bytes(b'constructed-only')
    inputs = dict(positions=original.spec(tmp_path / 'positions.gz'), engine=original.spec(tmp_path / 'engine'))
    counter = [100]

    def native(unit, operation, output):
        invocation = unit / 'native' / (operation + '-000001')
        invocation.mkdir(parents=True)
        plan = original.read(unit / 'UNIT.json')
        result = getattr(engine, operation)(unit / 'output', plan['inputs'], plan['config'])
        counter[0] += 1
        ident = dict(pid=counter[0], created_ticks=counter[0] * 100, executable='constructed-mock-only.exe')
        write_json(invocation / 'RESULT.json', result)
        write_json(invocation / 'NATIVE.json', ident)
        write_json(invocation / (operation.upper() + '_JOB_USAGE.json'),
                   dict(cpu_seconds=.01, exit_code=0, includes_all_descendants_and_exited_processes=True))
        return result, invocation.relative_to(unit).as_posix()

    monkeypatch.setattr(original, 'native_operation', native)
    monkeypatch.setattr(ranged, 'native_operation', native)
    entries = []
    for index, (begin, end, status, module) in enumerate([
            (0, 2, 'COMPLETE', original), (2, 4, 'FAILED', original),
            (4, 6, 'PAUSED', original), (6, 11, 'COMPLETE', ranged)]):
        root = tmp_path / ('attempt-' + str(index))
        output = root / 'output'
        inp = dict(inputs)
        config = dict(offset=begin, expected_positions=11, nodes=1000000,
                      unit_positions=2, queue_wall_seconds=3600, constructed_fixture=True)
        if module is ranged:
            manifest = dict(schema=ranges.SCHEMA, status='CONSTRUCTED_ONLY', begin=6,
                            expected_positions=11, nodes=1000000, **inputs,
                            ranges=[dict(id='shard-1', begin=6, end=11, pause_rank=1)],
                            implementation_pins=ranges.implementation_pins())
            write_json(tmp_path / 'ranges.json', manifest)
            inp['range_manifest'] = original.spec(tmp_path / 'ranges.json')
            config.update(range_end=11, shard_id='shard-1')
        if status == 'COMPLETE' and module is original:
            real_time = original.time
            monkeypatch.setattr(original, 'time', SimpleNamespace(
                monotonic=lambda: 1800. if (output / 'PROGRESS.json').exists() else 0.))
            module.execute(output, inp, config)
            monkeypatch.setattr(original, 'time', real_time)
            module.verify(output, inp, config)
        elif status == 'COMPLETE':
            module.execute(output, inp, config)
            module.verify(output, inp, config)
        else:
            assert module.execute(output, inp, dict(config, max_new_draws=2))['status'] == 'yielded'
        plan = dict(module=module.__name__, inputs=inp, config=config)
        write_json(root / 'PLAN.json', plan)
        ident = dict(pid=1000 + index, created_ticks=10000 + index, executable='constructed-outer-only.exe')
        write_json(root / 'OWNER.json', dict(native=ident, plan_sha256=digest(root / 'PLAN.json')))
        write_json(root / 'EXECUTE_NATIVE.json', dict(native=dict(ident, pid=2000 + index)))
        write_json(root / 'EXECUTE_JOB_USAGE.json', dict(cpu_seconds=1., exit_code=0,
                   includes_all_descendants_and_exited_processes=True))
        terminal = dict(status=status, cpu_seconds=1.)
        if status == 'COMPLETE':
            write_json(root / 'VERIFY_NATIVE.json', dict(native=dict(ident, pid=3000 + index)))
            write_json(root / 'VERIFY_JOB_USAGE.json', dict(cpu_seconds=.5, exit_code=0,
                       includes_all_descendants_and_exited_processes=True))
            terminal.update(fresh_process_verified=True, outputs={
                p.relative_to(root).as_posix(): digest(p) for p in root.rglob('*') if p.is_file()})
        if status == 'PAUSED':
            terminal.update(checkpoint_validation_required=True,
                            checkpoint_outputs=original_pause_inventory(output))
        write_json(root / (status + '.json'), terminal)
        audit = tmp_path / ('audit-' + str(index) + '.json')
        assembly.capture_post_exit_audit(root, audit)
        entries.append(dict(begin=begin, end=end, terminal=assembly.spec(root / (status + '.json')),
                            plan=assembly.spec(root / 'PLAN.json'), audit=assembly.spec(audit)))
    write_json(tmp_path / 'attempts.json', dict(schema=assembly.SCHEMA, attempts=entries))
    inputs['attempts'] = assembly.spec(tmp_path / 'attempts.json')
    return inputs, dict(expected_positions=11, nodes=1000000, constructed_fixture=True), entries, scorer


def rewrite_attempts(tmp_path, inputs, entries, suffix='changed'):
    path = tmp_path / (suffix + '.json')
    write_json(path, dict(schema=assembly.SCHEMA, attempts=entries))
    return dict(inputs, attempts=assembly.spec(path))


def test_full_union_preserves_dispositions_and_true_denominator(tmp_path, monkeypatch):
    inputs, config, entries, scorer = world(tmp_path, monkeypatch)
    snapshots = {e['terminal']['path']: digest(e['terminal']['path']) for e in entries}
    output = tmp_path / 'assembly'
    assert assembly.execute(output, inputs, config)['population_complete']
    assert assembly.verify(output, inputs, config)['population_complete']
    report = assembly.read(output / 'BATCHES.json')
    assert report['positions'] == 11 and len(report['batches']) == 6
    assert [b['source_disposition'] for b in report['batches']] == ['COMPLETE', 'FAILED', 'PAUSED', 'COMPLETE', 'COMPLETE', 'COMPLETE']
    assert all('native_complete' not in b for b in report['batches'])
    assert snapshots == {path: digest(path) for path in snapshots}
    assert sorted(scorer.calls) == [n for n in range(11) for _ in range(2)]


def test_partial_is_operational_and_cannot_emit_batches(tmp_path, monkeypatch):
    inputs, config, entries, _ = world(tmp_path, monkeypatch)
    partial = rewrite_attempts(tmp_path, inputs, entries[:3])
    output = tmp_path / 'prefix-audit'
    assert assembly.execute(output, partial, dict(config, operational_prefix_only=True))['operational_only']
    assert not (output / 'BATCHES.json').exists()
    assert assembly.verify(output, partial, dict(config, operational_prefix_only=True))['operational_only']
    with pytest.raises(ValueError, match='Full original ordinal'):
        assembly.execute(tmp_path / 'refused', partial, config)


@pytest.mark.parametrize('kind', ['duplicate', 'gap', 'cut-unit', 'wrong-end'])
def test_exact_once_coverage_refusals(tmp_path, monkeypatch, kind):
    inputs, config, entries, _ = world(tmp_path, monkeypatch)
    changed = copy.deepcopy(entries)
    if kind == 'duplicate': changed.append(changed[1])
    if kind == 'gap': changed.pop(1)
    if kind == 'cut-unit': changed[1]['begin'] = 3
    if kind == 'wrong-end': changed[1]['end'] = 5
    with pytest.raises(ValueError):
        assembly.execute(tmp_path / 'refused', rewrite_attempts(tmp_path, inputs, changed), config)


@pytest.mark.parametrize('kind', ['engine', 'nodes', 'denominator', 'scope', 'live', 'unknown', 'score', 'audit', 'terminal', 'missing-job'])
def test_binding_native_hash_refusals(tmp_path, monkeypatch, kind):
    inputs, config, entries, _ = world(tmp_path, monkeypatch)
    if kind == 'engine':
        (tmp_path / 'engine').write_bytes(b'changed')
    if kind == 'nodes': config['nodes'] = 300000
    if kind == 'denominator': config['expected_positions'] = 10
    if kind == 'scope': config['constructed_fixture'] = False
    if kind == 'live': monkeypatch.setattr(assembly, 'is_same_live_process', lambda _: True)
    if kind == 'unknown':
        def unknown(_): raise OSError('constructed access denial')
        monkeypatch.setattr(assembly, 'is_same_live_process', unknown)
    if kind == 'score':
        p = next((tmp_path / 'attempt-1/output/units').glob('*/output/PRIVATE_SCORES/*.json'))
        p.write_bytes(b'{}')
    if kind == 'audit': Path(entries[1]['audit']['path']).write_bytes(b'{}')
    if kind == 'terminal': Path(entries[1]['terminal']['path']).write_bytes(b'{}')
    if kind == 'missing-job':
        (tmp_path / 'attempt-1/EXECUTE_JOB_USAGE.json').unlink()
        audit = tmp_path / 'missing-job-audit.json'
        assembly.capture_post_exit_audit(tmp_path / 'attempt-1', audit)
        entries[1]['audit'] = assembly.spec(audit)
        inputs = rewrite_attempts(tmp_path, inputs, entries)
    with pytest.raises((ValueError, OSError)):
        assembly.execute(tmp_path / 'refused', inputs, config)


def test_failed_active_unit_is_retained_but_never_accepted(tmp_path, monkeypatch):
    inputs, config, entries, _ = world(tmp_path, monkeypatch)
    root = tmp_path / 'attempt-1'
    state = assembly.read(root / 'output/QUEUE_STATE.json')
    state['active'] = dict(path='units/unsealed', execute_native=None)
    write_json(root / 'output/QUEUE_STATE.json', state, mutable=True)
    (root / 'output/units/unsealed').mkdir()
    (root / 'output/units/unsealed/unverified.txt').write_text('Unverified position4; must remain excluded.')
    audit = tmp_path / 'failed-active-audit.json'
    assembly.capture_post_exit_audit(root, audit)
    entries[1]['audit'] = assembly.spec(audit)
    changed = rewrite_attempts(tmp_path, inputs, entries)
    output = tmp_path / 'accepted-seals-only'
    assert assembly.execute(output, changed, config)['population_complete']
    prefix = assembly.read(output / 'PREFIX_AUDIT.json')
    assert prefix['intervals'][1]['excluded_active_unit'] is True
    assert all('unsealed' not in b['path'] for b in assembly.read(output / 'BATCHES.json')['batches'])


def test_changed_original_ordinal_refuses_even_with_new_inventory(tmp_path, monkeypatch):
    inputs, config, entries, _ = world(tmp_path, monkeypatch)
    # A proposed replacement source can pass its own hash while disagreeing
    # with every original unit's already sealed full-roster binding.
    rows = list(original.scorer.iter_positions(inputs['positions']['path']))
    rows[0], rows[1] = rows[1], rows[0]
    path = tmp_path / 'reordered.gz'
    original.write_positions(path, rows)
    changed = dict(inputs, positions=assembly.spec(path))
    with pytest.raises(ValueError, match='different source'):
        assembly.execute(tmp_path / 'refused', changed, config)


def test_paused_telemetry_uses_original_filter_but_full_audit_retains_it(tmp_path, monkeypatch):
    inputs, config, entries, _ = world(tmp_path, monkeypatch)
    root = tmp_path / 'attempt-2'
    terminal_before = digest(root / 'PAUSED.json')
    names = ['YIELD_REQUEST.json', 'PROGRESS.json', 'telemetry/PROGRESS.json',
             'telemetry/uncommitted.tmp', 'telemetry/atomic.tmp.abc']
    for name in names:
        path = root / 'output' / name
        path.parent.mkdir(exist_ok=True)
        path.write_text('{"retained_telemetry":true}', encoding='utf8')
    audit_path = tmp_path / 'pause-telemetry-audit.json'
    audit = assembly.capture_post_exit_audit(root, audit_path)
    assert all(name in audit['checkpoint_outputs'] for name in names)
    assert assembly.paused_terminal_inventory(audit['checkpoint_outputs']) == original_pause_inventory(root / 'output')
    entries[2]['audit'] = assembly.spec(audit_path)
    changed = rewrite_attempts(tmp_path, inputs, entries)
    assert assembly.execute(tmp_path / 'accepted-telemetry', changed, config)['population_complete']
    assert digest(root / 'PAUSED.json') == terminal_before


def test_paused_terminal_cannot_omit_scientific_output_even_with_fresh_audit(tmp_path, monkeypatch):
    inputs, config, entries, _ = world(tmp_path, monkeypatch)
    root = tmp_path / 'attempt-2'
    terminal = assembly.read(root / 'PAUSED.json')
    scientific = next(name for name in terminal['checkpoint_outputs'] if '/PRIVATE_SCORES/' in name)
    terminal['checkpoint_outputs'].pop(scientific)
    write_json(root / 'PAUSED.json', terminal, mutable=True)
    entries[2]['terminal'] = assembly.spec(root / 'PAUSED.json')
    audit = tmp_path / 'scientific-omission-audit.json'
    assembly.capture_post_exit_audit(root, audit)
    entries[2]['audit'] = assembly.spec(audit)
    changed = rewrite_attempts(tmp_path, inputs, entries)
    with pytest.raises(ValueError, match='Original PAUSED inventory differs'):
        assembly.execute(tmp_path / 'refused-scientific-omission', changed, config)
