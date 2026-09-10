import copy
import pytest

from runners.stage9 import disposition_jobs as jobs
from runners.stage9.common import write, file_hash
from runners.stage9.launch import handler_operation


def decision(tmp_path, monkeypatch):
    import runners.stage9.launch as launch
    monkeypatch.setattr(launch, 'REPO', tmp_path)
    path = tmp_path / 'original.json'
    write(path, {'disposition': 'UNQUALIFIED', 'scope': 'known fixture'})
    return dict(card='C03', kind='failed_prerequisite', scope='fixture only',
                reason='The required independent quality gate failed.',
                evidence={'original': {'path': 'original.json', 'sha256': file_hash(path)}},
                retained_failures=['original'], finding='fixture',
                next_obligation='Retain the failed gate and inspect independent eligible branches.')


def test_failed_prerequisite_stays_unrun_and_changed_original_refuses(tmp_path, monkeypatch):
    value = decision(tmp_path, monkeypatch)
    result = jobs.validate_decision(value, 'C03')
    assert result['disposition'] == 'NOT RUN WITH REASON'
    assert not any(result[k] for k in ('scientific_execution', 'scientific_admission', 'scientific_launch_accepted'))
    assert result['retained_failures'] == ['original'] and 'scores' not in result
    write(tmp_path / 'original.json', {'disposition': 'PASSED'})
    with pytest.raises(ValueError, match='changed'):
        jobs.validate_decision(value, 'C03')


def test_not_run_cannot_omit_failure_or_smuggle_score(tmp_path, monkeypatch):
    value = decision(tmp_path, monkeypatch)
    for changed in (value | {'reason': ''}, value | {'retained_failures': []},
                    value | {'retained_failures': ['missing']}, value | {'score': 1.0},
                    value | {'evidence': {}}, value | {'card': 'M01'}):
        with pytest.raises(ValueError):
            jobs.validate_decision(copy.deepcopy(changed), 'C03')


def test_rehearsal_distinguishes_not_run_cards():
    def job(card):
        return {'module': 'runners.stage9.disposition_jobs', 'arguments': ['--card', card]}
    assert handler_operation(job('T05')) != handler_operation(job('T06'))
    assert handler_operation(job('T05'))[1] == 'not-run-T05'
    for args in ([], ['--card'], ['--card', 'unknown'], ['--card', 'T05', '--card', 'T06']):
        with pytest.raises(ValueError):
            handler_operation(job('T05') | {'arguments': args})
