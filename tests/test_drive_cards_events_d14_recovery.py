import copy
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import numpy as np
import pytest
from runners.drive.cards import events_d14 as original
from runners.drive.cards import events_d14_features as old_features
from runners.drive.cards import events_d14_recovery as recovery
from runners.drive.cards import events_d14_recovery_features as features
from runners.drive.cards import events_d14_reuse as reuse

spec = importlib.util.spec_from_file_location('d14_fixture', Path(__file__).with_name('test_drive_cards_events_d14.py'))
fixture = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fixture)


def actual_schema_fixture():
    sessions, records, vectors, p8 = fixture.sessions_fixture(3)
    for session in sessions:
        session['writer'] = 'w0'
        for row in session['rows']:
            row['writer'] = 'w0'
            row.pop('session_end')  # Matches actual prepared row schema.
    for row in records:
        row['writer'] = 'w0'
    return sessions, records, vectors, p8


def test_real_prepared_schema_reproduces_failure_and_exact_p4_repair():
    sessions, records, vectors, p8 = actual_schema_fixture()
    before = copy.deepcopy(sessions)
    rows = old_features.extract_writer(sessions, records, vectors, fixture.FakeEncoder(), fixture.FakeNLP())['rows']
    with pytest.raises(KeyError, match='session_end'):
        old_features.nuisance_matrix(rows, sessions, records, vectors, p8, 20261017)
    actual, projection = features.nuisance_matrix(rows, sessions, records, vectors, p8, 20261017)
    normalized = features.prepared_sessions(sessions)
    expected, expected_projection = old_features.nuisance_matrix(rows, normalized, records, vectors, p8, 20261017)
    assert np.array_equal(actual, expected)
    assert projection == expected_projection
    assert sessions == before
    assert all(row['session_end'] == session['end_at'] for session in normalized for row in session['rows'])


def test_prior_session_history_is_strict_and_never_invents_end_time():
    sessions, records, vectors, p8 = actual_schema_fixture()
    normalized = features.prepared_sessions(sessions)
    rows, base, _, _ = old_features.prefix_features(normalized, records, vectors, p8)
    first_second = next(i for i, r in enumerate(rows) if r['session'] == sessions[1]['session'])
    assert base[first_second, -4:].tolist() == [0., 0., 0., 1.]  # Prior session ended strictly earlier.
    sessions[0]['end_at'] = sessions[1]['timestamp']
    rows, base, _, _ = old_features.prefix_features(features.prepared_sessions(sessions), records, vectors, p8)
    assert base[first_second, -4:].tolist() == [0., 0., 0., 0.]  # Equality is still unavailable.
    sessions[0]['end_at'] = sessions[1]['timestamp'] + 50
    rows, base, _, _ = old_features.prefix_features(features.prepared_sessions(sessions), records, vectors, p8)
    assert base[first_second, -4:].tolist() == [0., 0., 0., 0.]
    sessions[0]['rows'][0]['session_end'] = 999999
    with pytest.raises(ValueError, match='conflicts'):
        features.prepared_sessions(sessions)


def test_authenticated_failed_extraction_reuse_yield_and_fresh_verify(tmp_path, monkeypatch):
    (tmp_path / 'sources').mkdir()
    inputs = fixture.handler_inputs(tmp_path / 'sources')
    config = dict(phase='pilot', threads=2, batch_size=16, bootstrap=2000, seed=20261017, pca_dimensions=16)
    pins = lambda inp: {str(Path(v)): original.filehash(v) for k, v in inp.items() if k != 'spacy_model'}
    monkeypatch.setattr(original, 'input_pins', pins)
    monkeypatch.setattr(recovery, 'input_pins', pins)
    monkeypatch.setattr(old_features, 'ParagraphEncoder', fixture.FakeEncoder)
    import spacy
    monkeypatch.setattr(spacy, 'load', lambda _: fixture.FakeNLP())
    calls = []
    def extract(own, *args):
        calls.append(own[0]['writer'])
        return dict(rows=[dict(r, writer=own[0]['writer'], session=own[0]['session']) for r in fixture.known_rows(.6, 1)], audit={})
    monkeypatch.setattr(old_features, 'extract_writer', extract)
    def failure(*args, **kwargs):
        raise KeyError('session_end')
    monkeypatch.setattr(old_features, 'nuisance_matrix', failure)
    failed = tmp_path / 'failed'
    with pytest.raises(KeyError, match='session_end'):
        original.execute(failed / 'output', inputs, config)
    assert len(calls) == 2
    fixture.write(failed / 'PLAN.json', dict(module='runners.drive.cards.events_d14', inputs=inputs, config=config,
        pins={str(Path(original.__file__)): original.filehash(original.__file__)}))
    fixture.write(failed / 'FAILED.json', dict(status='FAILED', reason="KeyError('session_end')"))
    recovered_inputs = dict(inputs, failed_plan=str(failed / 'PLAN.json'), failed_binding=str(failed / 'output/INPUTS.json'),
                            failed_receipt=str(failed / 'FAILED.json'))
    monkeypatch.setattr(features, 'nuisance_matrix', lambda rows, *args: (np.zeros((len(rows), 1)), {}))
    monkeypatch.setattr(features, 'ParagraphEncoder', lambda *args: pytest.fail('reused pilot must not load model'))
    output = tmp_path / 'recovery'
    # Yield exactly after the first copied complete writer, without unbound files.
    save = recovery.save
    def save_then_yield(path, value):
        save(path, value)
        if path.parent.name == 'writers' and not (output / 'YIELD_REQUEST.json').exists():
            fixture.write(output / 'YIELD_REQUEST.json', {})
    monkeypatch.setattr(recovery, 'save', save_then_yield)
    assert recovery.execute(output, recovered_inputs, config)['status'] == 'yielded'
    monkeypatch.setattr(recovery, 'save', save)
    (output / 'YIELD_REQUEST.json').unlink()
    result = recovery.execute(output, recovered_inputs, config)
    assert result['primary']['effect'] == pytest.approx(.6)
    assert len(calls) == 2
    receipt = original.read(output / 'RECOVERY.json')
    assert len(receipt['reusable_checkpoints']) == 2 and not receipt['scientific_change']
    for writer, saved in receipt['reusable_checkpoints'].items():
        assert original.filehash(output / 'writers' / (writer + '.json')) == saved['sha256']
    assert recovery.verify(output, recovered_inputs, config)['verified']
    args = tmp_path / 'verify_args.json'
    fixture.write(args, dict(output=str(output), inputs=recovered_inputs, config=config))
    script = "import json,sys; from pathlib import Path; from runners.drive.cards.events_d14_recovery import verify; a=json.load(open(sys.argv[1])); print(json.dumps(verify(Path(a['output']),a['inputs'],a['config'])))"
    child = subprocess.run([sys.executable, '-B', '-c', script, str(args)], capture_output=True, text=True,
        env=dict(os.environ, PYTHONHASHSEED='441'), check=True)
    assert json.loads(child.stdout)['verified']
    old_path = Path(next(iter(receipt['reusable_checkpoints'].values()))['path'])
    old_path.write_text('{}', encoding='utf8')
    with pytest.raises(ValueError, match='seal differs'):
        reuse.authenticate(recovered_inputs, config)

