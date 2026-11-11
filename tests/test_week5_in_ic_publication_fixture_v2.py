import json
import sys
from pathlib import Path
import pytest
from runners.drive.cards import week5_in_ic_publication_fixture_v2 as fixture
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from codex_watch import valid_json


@pytest.mark.parametrize('operation', ['execute', 'verify'])
def test_actual_handler_pause_accepted_by_production_watcher(tmp_path, monkeypatch, operation):
    monkeypatch.setattr(fixture, 'args', lambda *args: ({}, {}))
    monkeypatch.setattr(fixture, 'compare', lambda *args, **kwargs: 25)
    monkeypatch.setattr(fixture.baseline, operation, lambda *args: dict(status='yielded'))
    if operation == 'execute':
        monkeypatch.setattr(fixture, 'candidate_execute', lambda *args: dict(status='yielded'))
    else:
        monkeypatch.setattr(fixture.candidate, 'verify', lambda *args: dict(status='yielded'))
    producer = getattr(fixture, operation)(tmp_path / 'output', {}, {'case': 'IN3'})
    envelope = dict(status='PAUSED', scientific_admission=False,
        checkpoint_validation_required=True, card='constructed-IN', at='2026-11-11T00:00:00Z',
        cpu_seconds=1, paused_operation=operation, checkpoint_outputs={'saved.json': 'a' * 64},
        reason=dict(reason='Producer checkpoint quantum', producer=producer))
    path = tmp_path / 'PAUSED.json'
    path.write_text(json.dumps(envelope), encoding='utf8')
    assert valid_json(path)
    del producer['phase']
    path.write_text(json.dumps(envelope), encoding='utf8')
    assert not valid_json(path)
