"""Actual loaded numerical pools, restoration and refusal at the D20 boundary."""
import json
import numpy as np
import pytest
from threadpoolctl import threadpool_info, threadpool_limits
from runners.drive.cards import events_d20_one_thread_v3 as card


@pytest.mark.parametrize('operation', ['execute', 'verify'])
def test_actual_pool_limit_and_restoration(tmp_path, monkeypatch, operation):
    inputs = {'identity': 'unchanged'}
    answer = {'verified': True}

    def delegated(output, actual_inputs, actual_config):
        assert actual_inputs is inputs
        assert actual_config is card.CONFIG
        np.dot(np.eye(8), np.eye(8))
        assert threadpool_info()
        assert all(p['num_threads'] == 1 for p in threadpool_info())
        return answer

    monkeypatch.setattr(card.original, operation, delegated)
    with threadpool_limits(limits=2):
        before = threadpool_info()
        assert getattr(card, operation)(tmp_path, inputs, card.CONFIG) is answer
        assert threadpool_info() == before
        receipt_bytes = (tmp_path.parent / f'{tmp_path.name}_THREAD_LIMIT_{operation.upper()}.json').read_bytes()
        assert getattr(card, operation)(tmp_path, inputs, card.CONFIG) is answer
        assert (tmp_path.parent / f'{tmp_path.name}_THREAD_LIMIT_{operation.upper()}.json').read_bytes() == receipt_bytes
    receipt = json.loads((tmp_path.parent / f'{tmp_path.name}_THREAD_LIMIT_{operation.upper()}.json').read_text())
    assert all(p['num_threads'] == 1 for p in receipt['measured_after'])


def test_failure_restores_pools_without_success_receipt(tmp_path, monkeypatch):
    def fail(*args):
        assert all(p['num_threads'] == 1 for p in threadpool_info())
        raise ValueError('retained source failure')

    monkeypatch.setattr(card.original, 'execute', fail)
    with threadpool_limits(limits=2):
        before = threadpool_info()
        with pytest.raises(ValueError, match='retained source failure'):
            card.execute(tmp_path, {}, card.CONFIG)
        assert threadpool_info() == before
    assert not (tmp_path.parent / f'{tmp_path.name}_THREAD_LIMIT_EXECUTE.json').exists()
    with pytest.raises(ValueError, match='configuration differs'):
        card.execute(tmp_path, {}, dict(card.CONFIG, threads=2))


def test_unenforced_limit_refuses_before_scoring(tmp_path, monkeypatch):
    monkeypatch.setattr(card, 'threadpool_info', lambda: [{'num_threads': 2}])
    monkeypatch.setattr(card.original, 'execute', lambda *args: pytest.fail('must not score'))
    with pytest.raises(RuntimeError, match='not established'):
        card.execute(tmp_path, {}, card.CONFIG)


def test_complete_source_inventory_and_reentry(tmp_path):
    import runpy
    from pathlib import Path
    factory = runpy.run_path(str(Path('tests/test_drive_cards_events_d20_extension.py')))['fixture']
    inputs, _ = factory(tmp_path / 'sources')
    output = tmp_path / 'output'
    result = card.execute(output, inputs, card.CONFIG)
    before = {str(p):p.read_bytes() for p in tmp_path.rglob('*') if p.is_file()}
    assert card.verify(output, inputs, card.CONFIG)['all_draws_recomputed']
    assert card.execute(output, inputs, card.CONFIG) == result
    for p, data in before.items():
        assert Path(p).read_bytes() == data
    assert not list(output.glob('*THREAD_LIMIT*'))
