"""Constructed range coverage only. Mock native records are never admission.

DESIGN CHECK: LESSONS 3-5. The independent expected stream is literal ordinals;
under null/alternative each requested ordinal occurs exactly twice, once for
execute and once for independent replay. The prefix, tail, gaps, duplicates,
altered pins and unfinished handover must never be silently accepted.
"""
from copy import deepcopy
from pathlib import Path
import shutil

import pytest

from runners.drive.cards import week5_ch_queue_range_v1 as queue
from runners.drive.cards import week5_ch_manifest_range_v1 as ranges
from runners.drive.cards import week5_ch_engine_bounded as engine
from runners.drive.cards.week5_ch_source import digest, write_json


class FakeScorer:
    calls = []

    def __init__(self, path, nodes):
        self.nodes = nodes

    def score(self, row):
        self.calls.append(row['ordinal'])
        return dict(position=row, node_limit=self.nodes, threads=1, hash_mb=64,
                    engine=dict(k50=1))

    def close(self):
        pass


def world(tmp_path, monkeypatch, count=11):
    rows = [dict(ordinal=i, fen='constructed', uci='e2e4',
                 month='2017-04', player='constructed-' + str(i)) for i in range(count)]
    queue.write_positions(tmp_path / 'positions.gz', rows)
    (tmp_path / 'engine').write_bytes(b'constructed-only')
    inputs = {n: queue.spec(tmp_path / p) for n, p in
              [('positions', 'positions.gz'), ('engine', 'engine')]}
    manifest = dict(schema=ranges.SCHEMA, status='CONSTRUCTED_ONLY', begin=2,
                    expected_positions=11, nodes=1000000, **inputs,
                    ranges=[dict(id='shard-1', begin=2, end=5, pause_rank=1),
                            dict(id='shard-2', begin=5, end=8, pause_rank=2),
                            dict(id='shard-3', begin=8, end=11, pause_rank=3)],
                    implementation_pins=ranges.implementation_pins())
    write_json(tmp_path / 'manifest.json', manifest)
    inputs['range_manifest'] = queue.spec(tmp_path / 'manifest.json')
    config = dict(offset=2, range_end=5, shard_id='shard-1', expected_positions=11,
                  nodes=1000000, unit_positions=2, queue_wall_seconds=3600,
                  constructed_fixture=True)
    monkeypatch.setattr(engine, 'Scorer', FakeScorer)
    FakeScorer.calls = []

    def native(unit, operation, output):
        invocation = unit / 'native' / (operation + '-000001')
        invocation.mkdir(parents=True)
        plan = queue.read(unit / 'UNIT.json')
        result = getattr(engine, operation)(unit / 'output', plan['inputs'], plan['config'])
        write_json(invocation / 'RESULT.json', result)
        write_json(invocation / 'NATIVE.json', dict(pid=11 if operation == 'execute' else 12,
                                                  constructed_mock=True))
        write_json(invocation / (operation.upper() + '_JOB_USAGE.json'),
                   dict(cpu_seconds=0., exit_code=0,
                        includes_all_descendants_and_exited_processes=True, constructed_mock=True))
        return result, invocation.relative_to(unit).as_posix()

    monkeypatch.setattr(queue, 'native_operation', native)
    return inputs, config, manifest


def copied(old, new):
    before = {p.relative_to(old).as_posix(): digest(p) for p in old.rglob('*') if p.is_file()}
    shutil.copytree(old, new)
    write_json(new.parent / 'RESUMED_FROM.json', dict(copied=before))
    return before


def test_partition_known_answer_and_reverse_pause():
    # Independent literal arithmetic: 9 positions into 2-row units, 3 shards.
    expected = [dict(id='shard-1', begin=2, end=6, pause_rank=1),
                dict(id='shard-2', begin=6, end=10, pause_rank=2),
                dict(id='shard-3', begin=10, end=11, pause_rank=3)]
    assert ranges.partition(2, 11, 3, 2) == expected
    manifest = dict(schema=ranges.SCHEMA, begin=2, expected_positions=11, ranges=expected)
    assert ranges.validate_partition(manifest) == expected
    assert ranges.reverse_pause_order(manifest, ['shard-1', 'shard-3']) == ['shard-3', 'shard-1']
    with pytest.raises(ValueError):
        ranges.reverse_pause_order(manifest, ['unknown'])


@pytest.mark.parametrize('kind', ['gap', 'overlap', 'duplicate', 'empty', 'tail', 'bool', 'rank'])
def test_partition_refusals(kind):
    manifest = dict(schema=ranges.SCHEMA, begin=2, expected_positions=11,
                    ranges=ranges.partition(2, 11, 3, 2))
    rows = manifest['ranges']
    if kind == 'gap': rows[1]['begin'] += 1
    if kind == 'overlap': rows[1]['begin'] -= 1
    if kind == 'duplicate': rows[1]['id'] = rows[0]['id']
    if kind == 'empty': rows[1]['end'] = rows[1]['begin']
    if kind == 'tail': rows[-1]['end'] -= 1
    if kind == 'bool': rows[0]['begin'] = True
    if kind == 'rank': rows[0]['pause_rank'] = 3
    with pytest.raises(ValueError): ranges.validate_partition(manifest)


def test_complete_shards_exact_union_no_prefix_or_tail(tmp_path, monkeypatch):
    inputs, config, manifest = world(tmp_path, monkeypatch)
    for shard in manifest['ranges']:
        cfg = dict(config, offset=shard['begin'], range_end=shard['end'], shard_id=shard['id'])
        output = tmp_path / shard['id'] / 'output'
        assert queue.execute(output, inputs, cfg)['range_complete']
        assert queue.verify(output, inputs, cfg)['range_complete']
        assert queue.read(output / 'QUEUE_BATCHES.json')['end'] == shard['end']
    assert sorted(FakeScorer.calls) == [2, 2, 3, 3, 4, 4, 5, 5, 6, 6, 7, 7, 8, 8, 9, 9, 10, 10]


def test_execute_pause_copy_resume_preserves_original(tmp_path, monkeypatch):
    inputs, config, _ = world(tmp_path, monkeypatch)
    old = tmp_path / 'old/output'
    assert queue.execute(old, inputs, dict(config, max_new_draws=2))['status'] == 'yielded'
    assert queue.read(old / 'QUEUE_STATE.json')['next_offset'] == 4
    new = tmp_path / 'new/output'
    before = copied(old, new)
    assert queue.execute(new, inputs, config)['end'] == 5
    assert queue.verify(new, inputs, config)['verified']
    assert before == {p.relative_to(old).as_posix(): digest(p) for p in old.rglob('*') if p.is_file()}
    assert sorted(FakeScorer.calls) == [2, 2, 3, 3, 4, 4]


def test_verifier_pause_copy_resume(tmp_path, monkeypatch):
    inputs, config, _ = world(tmp_path, monkeypatch)
    old = tmp_path / 'old/output'
    queue.execute(old, inputs, config)
    assert queue.verify(old, inputs, dict(config, max_new_draws=2))['status'] == 'yielded'
    new = tmp_path / 'new/output'
    copied(old, new)
    assert queue.execute(new, inputs, config)['sealed_queue_reused']
    assert queue.verify(new, inputs, config)['range_complete']
    assert sorted(FakeScorer.calls) == [2, 2, 3, 3, 4, 4]


@pytest.mark.parametrize('count', [10, 12])
def test_full_denominator_checked_beyond_shard_tail(tmp_path, monkeypatch, count):
    inputs, config, _ = world(tmp_path, monkeypatch, count)
    with pytest.raises(ValueError, match='denominator'):
        queue.execute(tmp_path / 'attempt/output', inputs, config)


@pytest.mark.parametrize('key,value', [('range_end', 6), ('offset', 3), ('shard_id', 'shard-2'),
                                       ('nodes', 300000), ('constructed_fixture', False)])
def test_changed_contract_refuses_before_scoring(tmp_path, monkeypatch, key, value):
    inputs, config, _ = world(tmp_path, monkeypatch)
    with pytest.raises(ValueError):
        queue.execute(tmp_path / 'attempt/output', inputs, dict(config, **{key: value}))
    assert FakeScorer.calls == []


def test_changed_source_and_sealed_score_refuse(tmp_path, monkeypatch):
    inputs, config, _ = world(tmp_path, monkeypatch)
    output = tmp_path / 'attempt/output'
    queue.execute(output, inputs, config)
    unit = next((output / 'units').iterdir())
    score = next((unit / 'output/PRIVATE_SCORES').glob('*.json'))
    score.write_bytes(b'{}')
    with pytest.raises(ValueError, match='changed'): queue.verify(output, inputs, config)
    Path(inputs['positions']['path']).write_bytes(b'changed')
    with pytest.raises(ValueError, match='changed'): queue.execute(tmp_path / 'other/output', inputs, config)


def test_production_requires_real_handover(tmp_path, monkeypatch):
    inputs, config, manifest = world(tmp_path, monkeypatch)
    manifest.update(status='FROZEN_FOR_OWNER_ADMISSION', handover=queue.spec(tmp_path / 'engine'))
    write_json(tmp_path / 'production.json', manifest)
    inputs['range_manifest'] = queue.spec(tmp_path / 'production.json')
    with pytest.raises((ValueError, KeyError)):
        queue.execute(tmp_path / 'attempt/output', inputs, dict(config, constructed_fixture=False))
    assert FakeScorer.calls == []


def handover_world(tmp_path, monkeypatch, change=None):
    inputs, _, manifest = world(tmp_path, monkeypatch)
    original = ranges.original
    monkeypatch.setattr(original, 'native_operation', queue.native_operation)
    old = tmp_path / 'original'
    base_inputs = {k: inputs[k] for k in ('positions', 'engine')}
    config = dict(offset=0, expected_positions=11, nodes=1000000,
                  unit_positions=2, queue_wall_seconds=3600, constructed_fixture=True)
    assert original.execute(old / 'output', base_inputs, dict(config, max_new_draws=2))['status'] == 'yielded'
    plan = dict(module=ranges.ORIGINAL_MODULE, inputs=base_inputs, config=config)
    write_json(old / 'PLAN.json', plan)
    native = dict(pid=123, created_ticks=456, executable='constructed-only.exe')
    write_json(old / 'OWNER.json', dict(native=native))
    write_json(old / 'EXECUTE_NATIVE.json', dict(native=dict(native, pid=124)))
    state = original.read(old / 'output/QUEUE_STATE.json')
    if change == 'active':
        state['active'] = dict(path='unclosed', execute_native=None)
    if change == 'cursor':
        state['next_offset'] = 3
    if change in ('active', 'cursor'):
        write_json(old / 'output/QUEUE_STATE.json', state, mutable=True)
    checkpoint = {p.relative_to(old / 'output').as_posix(): digest(p)
                  for p in (old / 'output').rglob('*') if p.is_file()}
    terminal = dict(status='PAUSED', checkpoint_outputs=checkpoint, cpu_seconds=0.)
    if change == 'terminal': terminal['status'] = 'COMPLETE'
    write_json(old / 'PAUSED.json', terminal)
    names = ['PLAN.json', 'OWNER.json', 'EXECUTE_NATIVE.json', 'output/QUEUE_STATE.json', 'PAUSED.json']
    handover = dict(status='CLEAN_PREDECESSOR_RETIRED', root=str(old.resolve()),
                    terminal='PAUSED.json', files={n: digest(old / n) for n in names},
                    all_sealed_units_authenticated=True, all_checkpoint_outputs_authenticated=True,
                    all_descendant_jobs_exited=True, leases_released=True,
                    all_prior_attempt_costs_retained=True, historical_prefix_inventory=['constructed-only'])
    if change == 'hash': handover['files']['PLAN.json'] = '0' * 64
    if change == 'prior_audit': handover['all_prior_attempt_costs_retained'] = False
    if change == 'omitted_native': del handover['files']['EXECUTE_NATIVE.json']
    write_json(tmp_path / 'handover.json', handover)
    manifest['handover'] = queue.spec(tmp_path / 'handover.json')
    return manifest


def test_clean_handover_checks_sealed_prefix(tmp_path, monkeypatch):
    manifest = handover_world(tmp_path, monkeypatch)
    seen = []
    assert ranges.check_handover(manifest, lambda n: seen.append(n) or False)['leases_released']
    assert sorted(n['pid'] for n in seen) == [123, 124]


@pytest.mark.parametrize('change', ['active', 'cursor', 'terminal', 'hash', 'prior_audit', 'omitted_native'])
def test_handover_refusals(tmp_path, monkeypatch, change):
    manifest = handover_world(tmp_path, monkeypatch, change)
    with pytest.raises(ValueError): ranges.check_handover(manifest, lambda _: False)


def test_handover_live_and_unknown_identity_refuse(tmp_path, monkeypatch):
    manifest = handover_world(tmp_path, monkeypatch)
    with pytest.raises(ValueError, match='live or unproved'):
        ranges.check_handover(manifest, lambda _: True)

    def unknown(_):
        raise OSError('constructed access denial')

    with pytest.raises(OSError, match='access denial'):
        ranges.check_handover(manifest, unknown)


def test_original_one_unit_quantum_seals_existing_active_unit(tmp_path, monkeypatch):
    inputs, _, _ = world(tmp_path, monkeypatch)
    original = ranges.original
    native = queue.native_operation

    def interrupt_verify(unit, operation, output):
        if operation == 'verify':
            return dict(status='yielded'), 'constructed-no-invocation'
        return native(unit, operation, output)

    monkeypatch.setattr(original, 'native_operation', interrupt_verify)
    base_inputs = {k: inputs[k] for k in ('positions', 'engine')}
    config = dict(offset=0, expected_positions=11, nodes=1000000,
                  unit_positions=2, queue_wall_seconds=3600, constructed_fixture=True)
    old = tmp_path / 'old/output'
    assert original.execute(old, base_inputs, config)['status'] == 'yielded'
    assert original.read(old / 'QUEUE_STATE.json')['active'] is not None
    new = tmp_path / 'new/output'
    before = copied(old, new)
    monkeypatch.setattr(original, 'native_operation', native)
    assert original.execute(new, base_inputs, dict(config, max_new_draws=1))['status'] == 'yielded'
    state = original.read(new / 'QUEUE_STATE.json')
    assert state['active'] is None and state['next_offset'] == 2 and len(state['units']) == 1
    assert before == {p.relative_to(old).as_posix(): digest(p) for p in old.rglob('*') if p.is_file()}
    assert sorted(FakeScorer.calls) == [0, 0, 1, 1]


def test_range_wall_boundary_yields_without_partial_complete(tmp_path, monkeypatch):
    from types import SimpleNamespace
    inputs, config, _ = world(tmp_path, monkeypatch)
    old = tmp_path / 'old/output'
    real_time = queue.time
    clock = SimpleNamespace(monotonic=lambda: 1800. if (old / 'PROGRESS.json').exists() else 0.)
    monkeypatch.setattr(queue, 'time', clock)
    result = queue.execute(old, inputs, config)
    assert result['status'] == 'yielded' and result['reason'] == 'Clean range wall checkpoint'
    assert result['next_offset'] == 4 and result['range_complete'] is False
    assert not (old / 'QUEUE.json').exists()
    assert queue.read(old / 'QUEUE_STATE.json')['active'] is None
    monkeypatch.setattr(queue, 'time', real_time)
    new = tmp_path / 'new/output'
    copied(old, new)
    assert queue.execute(new, inputs, config)['range_complete']
    assert queue.verify(new, inputs, config)['range_complete']
    assert sorted(FakeScorer.calls) == [2, 2, 3, 3, 4, 4]
