"""Static/preflight/publication refusals; no native or scientific launches."""
from pathlib import Path
import json
import types
import numpy as np
import pytest
from runners.drive.cards import week5_qualification_driver as driver
from runners.drive.cards import week5_qualification_io as io
from runners.drive.cards import week5_output_size as monitor
from runners.drive.cards import week5_in_sensitivity_fixture_v2 as in_fixture
from runners.drive.cards import week5_sp3_ic_fixture_v2 as sp_fixture
from runners.drive.cards import week5_md3_followup_fixture_v2 as md_fixture


def admission(tmp_path):
    module = 'runners.drive.cards.week5_in_sensitivity_fixture_v2'
    component, source, cost, data = (tmp_path / name for name in ('component.json', 'source.json', 'cost.json', 'data.txt'))
    io.write_json(component, {'passed': True})
    io.write_json(source, dict(passed=True, constructed_only=True, IN3_IN4_actual_execute_verify=True,
                              calibration_worlds_per_effect=5, draws=2000, reachable_sensitivity_failure=True,
                              module_sha256=io.sha(driver.REPO / 'runners/drive/cards/week5_in_followup.py')))
    io.write_json(cost, {'constructed_test_accounting': True})
    data.write_text('constructed', encoding='utf8')
    design = driver.REPO / 'docs/design/stage-15/week5/QUALIFICATION_STAGING.md'
    return dict(reviewed=True, attempt='constructed-preflight-only', card='IN3.ic', operation='qualification',
                module=module, module_sha256=io.sha(driver.REPO / (module.replace('.', '/') + '.py')),
                inputs={'generation': str(data), 'fixture_manifest': str(component)},
                input_sha256={'generation': io.sha(data), 'fixture_manifest': io.sha(component)},
                config={'case': 'IN3', 'worlds': 100, 'draws': 2000}, design=str(design), design_sha256=io.sha(design),
                design_commit='constructed-preflight-only-not-a-native-admission',
                evidence=[dict(role='component', path=str(component), sha256=io.sha(component)),
                          dict(role='source', path=str(source), sha256=io.sha(source))],
                expected_terminal='PAUSED', expected_operation='execute', cpu_seconds=60, wall_seconds=300,
                ram_GiB=1, card_charged_cpu_seconds=0, family_charged_cpu_seconds=0,
                cost_evidence=[dict(path=str(cost), sha256=io.sha(cost))], resume=None)


def test_preflight_accepts_exact_evidence_without_launch(tmp_path):
    receipt = admission(tmp_path)
    assert driver.check_admission(receipt)[0] == 'IN'


@pytest.mark.parametrize('damage', ['no_source', 'false_component', 'changed_input', 'reduced_draws',
                                   'wrong_branch', 'exceeds_card', 'exceeds_family', 'no_cost', 'boundary'])
def test_preflight_refuses_missing_or_changed_evidence(tmp_path, damage):
    receipt = admission(tmp_path)
    if damage == 'no_source':
        receipt['evidence'] = receipt['evidence'][:1]
    elif damage == 'false_component':
        path = Path(receipt['evidence'][0]['path']); io.write_json(path, {'passed': False})
        receipt['evidence'][0]['sha256'] = io.sha(path)
    elif damage == 'changed_input':
        Path(receipt['inputs']['generation']).write_text('changed')
    elif damage == 'reduced_draws':
        receipt['config']['draws'] = 1999
    elif damage == 'wrong_branch':
        receipt['config']['case'] = 'IN4'
    elif damage == 'exceeds_card':
        receipt['card_charged_cpu_seconds'] = 2490
    elif damage == 'exceeds_family':
        receipt['family_charged_cpu_seconds'] = 59990
    elif damage == 'no_cost':
        receipt['cost_evidence'] = []
    else:
        receipt['expected_operation'] = None
    with pytest.raises(ValueError):
        driver.check_admission(receipt)


def test_json_publication_uses_existing_monitor_uuid_contract(tmp_path, monkeypatch):
    replace = io.os.replace
    observed = []
    def inspected(source, destination):
        observed.append(Path(source).name)
        assert monitor.ATOMIC_JSON.fullmatch(Path(source).name)
        assert monitor.output_bytes(tmp_path) > 0
        replace(source, destination)
    monkeypatch.setattr(io.os, 'replace', inspected)
    io.write_json(tmp_path / 'a.json', {'constructed': True})
    assert json.loads((tmp_path / 'a.json').read_text('utf8')) == {'constructed': True}
    assert len(observed) == 1
    assert b'\r' not in (tmp_path / 'a.json').read_bytes()


def test_direct_fit_bytes_are_sealed_without_rename(tmp_path, monkeypatch):
    path = tmp_path / 'POINT.npz'
    fit = {'beta': np.array([1., -2.]), 'alpha': np.array([np.nan, .5])}
    io.save_fit(path, 'constructed', fit)
    with np.load(path, allow_pickle=False) as saved:
        assert all(np.array_equal(saved[key], value, equal_nan=True) for key, value in fit.items())
    assert not list(tmp_path.glob('*.tmp.npz'))
    assert json.loads(path.with_suffix('.sha256.json').read_text('utf8'))['sha256'] == io.sha(path)
    with pytest.raises(ValueError, match='overwrite'):
        io.save_fit(path, 'constructed', fit)


def test_publication_adapter_restores_original_on_failure():
    original = lambda *args: None
    module = types.SimpleNamespace(write=original)
    with pytest.raises(RuntimeError):
        with io.publication([(module, 'write')]):
            assert module.write is io.write_json
            raise RuntimeError('constructed')
    assert module.write is original


def test_orphan_world_records_refuse(tmp_path):
    root = tmp_path / 'worlds'; root.mkdir()
    (root / '-2-000.seal.json').write_text('{}')
    with pytest.raises(ValueError, match='orphaned'):
        in_fixture.world_bank(tmp_path)
    with pytest.raises(ValueError, match='orphaned'):
        sp_fixture.world_bank(tmp_path)


def test_md_complete_bank_cannot_be_short(tmp_path):
    with pytest.raises(ValueError, match='entire declared'):
        md_fixture.bank_census(tmp_path, 'MD3.s', True)
