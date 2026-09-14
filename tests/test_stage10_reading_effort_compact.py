from contextlib import nullcontext
import json
from pathlib import Path
import pytest
from runners.stage10 import reading_effort as bank, reading_effort_compact as repair, ollama
from runners.stage10.queue import read


@pytest.fixture
def prepared():
    path = Path('results/phase_2_4_stage_10/raw/reading-screen-v1')
    if not path.exists():
        pytest.skip('reviewed private native source unavailable')
    return path


def test_compact_request_preserves_evidence_options_budget_and_restores(prepared):
    task = bank.Readers(prepared).tasks('pilot')[0]
    original = ollama.request_for
    expected = original(task, generated_tokens=256)
    with repair.profile():
        actual = ollama.request_for(task, generated_tokens=256)
        a, b = [json.loads(r['messages'][1]['content']) for r in [actual, expected]]
        a.pop('response_schema'); b.pop('response_schema')
        assert a == b
        assert actual['options'] == expected['options']
        assert actual['format']['properties']['probabilities'] == expected['format']['properties']['probabilities']
        assert actual['format']['properties']['explanation'] == {'type': 'string', 'const': ''}
        assert repair.Readers(prepared).sources != repair.OriginalReaders(prepared).sources
    assert ollama.request_for is original and bank.Readers is repair.OriginalReaders


@pytest.mark.parametrize('truncated', [False, True])
def test_literal_gate_complete_chain_and_immutable_replay(tmp_path, monkeypatch, prepared, truncated):
    calls = []
    def device(output, replay):
        output.mkdir(parents=True, exist_ok=True)
        return nullcontext()
    monkeypatch.setattr(bank, 'device', device)
    monkeypatch.setattr(ollama, 'identity', lambda: {'model': ollama.MODEL, 'digest': ollama.MODEL_DIGEST})
    def api(path, request=None, **kwargs):
        assert path == '/api/chat'
        calls.append(request)
        fields = request['format']['properties']; keys = fields['choice']['enum']
        if 'hypotheses' in fields:
            response = {'hypotheses': {'0': [], '1': [], '2': [], '3': []}, 'choice': keys[0], 'insufficient_support': True}
        else:
            assert fields['explanation']['const'] == ''
            response = {'probabilities': {k: 1/len(keys) for k in keys}, 'choice': keys[0], 'insufficient_evidence': True, 'explanation': ''}
        return {'done': True, 'done_reason': 'length' if truncated and len(calls) == 1 else 'stop',
                'message': {'content': json.dumps(response)}, 'eval_count': 12, 'prompt_eval_count': 20,
                'total_duration': 10, 'load_duration': 1, 'prompt_eval_duration': 2, 'eval_duration': 7}
    monkeypatch.setattr(ollama, 'api', api)
    pilot, dev, policy, evaluation = [tmp_path / name for name in ['pilot', 'dev', 'policy', 'evaluation']]
    with repair.profile():
        result = bank.predict(prepared, pilot, 'pilot')
        assert result['admitted'] is (not truncated)
        assert [r['options']['num_predict'] for r in calls] == [256, 512, 256, 256]
        if truncated:
            with pytest.raises(ValueError, match='literal reserved reading admission'):
                bank.predict(prepared, dev, 'development', pilot)
            assert len(calls) == 4 and not dev.exists()
            return
        bank.predict(prepared, dev, 'development', pilot)
        bank.fit(prepared, dev, pilot, policy)
        bank.predict(prepared, evaluation, 'evaluation', pilot, policy)
        assert all(r['result']['cost']['output_tokens'] <= 768 for r in read(evaluation/'ROSTER.json')['rows'])
        monkeypatch.setattr(ollama, 'api', lambda *a, **k: pytest.fail('immutable replay must not infer'))
        bank.predict(prepared, evaluation, 'evaluation', pilot, policy)
    with pytest.raises(ValueError, match='literal reserved reading admission'):
        bank.predict(prepared, tmp_path/'wrong-source', 'development', pilot)
