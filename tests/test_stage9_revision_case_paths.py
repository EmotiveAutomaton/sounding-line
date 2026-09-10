"""Exercise declared revision preparation paths with constructed source rows only."""
from pathlib import Path

import pytest

from runners.stage9 import common, iterater_cases, queue, revision_cases, revision_predictions, training_jobs


DECLARATIONS = [
    ('argrewrite-v1/main', None),
    ('iterater-v1/within', 'within'),
    ('iterater-v1/leave-arxiv', 'leave-arxiv'),
    ('iterater-v1/leave-news', 'leave-news'),
    ('iterater-v1/leave-wiki', 'leave-wiki'),
]


@pytest.fixture
def isolated(tmp_path, monkeypatch):
    root = tmp_path / 'results/phase_2_4_stage_9'
    for module in (common, revision_cases):
        monkeypatch.setattr(module, 'REPO', tmp_path)
    for module in (common, revision_cases, iterater_cases):
        monkeypatch.setattr(module, 'ROOT', root)
    real_inside = queue.inside
    for module in (queue, revision_cases):
        monkeypatch.setattr(module, 'inside', lambda p: real_inside(p, root=root))
    monkeypatch.setattr(queue, 'REPO', tmp_path)
    for module in (revision_cases, training_jobs):
        monkeypatch.setattr(module, 'cell_identity', lambda: 'constructed-path-contract')
    for name in ('runners/stage9', 'runners/stage7', 'runners/stage8', 'soundingline'):
        (tmp_path / name).mkdir(parents=True)
    for name in ('__init__.py', 'readout_repair.py', 'run_arg_replication.py', 's3_lib.py', 's4_lib.py', 's5_lib.py'):
        (tmp_path / 'runners' / name).write_text('# constructed source\n')
    monkeypatch.setattr(revision_predictions, 'sources', lambda: common.closure([tmp_path / 'runners']))
    common.freeze(root / 'private/prepared/cross-source-v2/COMPLETE.json', {'fixture': True})
    rows = {lane: [{'task': task, 'unit': lane + task} for task in ('retrospective', 'future')]
            for lane in ('train', 'development', 'evaluation')}
    metadata = {'allocation': {lane: lane for lane in rows}, 'scope': 'constructed source only',
                'counts': {lane: {'retrospective': 1, 'future': 1} for lane in rows}}
    monkeypatch.setattr(revision_cases, 'inputs', lambda scope: (rows, ['retained exclusion'], {}, metadata))
    monkeypatch.setattr(iterater_cases, 'study_inputs', lambda scope, study: (rows,
        {**metadata, 'study': study, 'active_tasks': ['retrospective', 'future'], 'task_dispositions': {}}))
    monkeypatch.setattr(iterater_cases, 'pilot_inputs', lambda: (rows, metadata))
    return root, rows


@pytest.mark.parametrize('relative,study', DECLARATIONS)
def test_declared_scientific_paths_materialize_and_reenter(isolated, relative, study):
    root, rows = isolated
    directory = root / 'private/scientific-revision-case' / relative
    run = (lambda: revision_cases.run(directory, 'scientific')) if study is None else (
        lambda: iterater_cases.run(directory, 'scientific', study))
    done = run()
    assert done['execution_complete'] and done['scientific_admission'] is False
    assert common.read(directory / 'CASES.json') == rows
    assert common.read(directory / 'COMPLETE.json') == done
    before = common.closure([directory])
    assert run() == done
    assert common.closure([directory]) == before


@pytest.mark.parametrize('module', [revision_cases, iterater_cases])
@pytest.mark.parametrize('scope,prefix', [
    ('scientific', 'revision-case-pilots'), ('pilot', 'scientific-revision-case'),
    ('scientific', 'scientific-revision-cases'), ('scientific', 'scientific-revision-case-other'),
    ('unknown', 'scientific-revision-case'),
])
def test_wrong_scope_or_sibling_refuses_before_source_access(isolated, monkeypatch, module, scope, prefix):
    root, _ = isolated
    def forbidden(*args):
        raise AssertionError('source rows must not be accessed for an invalid output scope')
    monkeypatch.setattr(revision_cases, 'inputs', forbidden)
    monkeypatch.setattr(iterater_cases, 'study_inputs', forbidden)
    monkeypatch.setattr(iterater_cases, 'pilot_inputs', forbidden)
    directory = root / 'private' / prefix / 'fixture'
    with pytest.raises(ValueError):
        module.run(directory, scope, 'within') if module is iterater_cases else module.run(directory, scope)
    assert not directory.exists()


@pytest.mark.parametrize('module', [revision_cases, iterater_cases])
def test_original_pilot_namespace_still_materializes(isolated, module):
    root, rows = isolated
    directory = root / 'private/revision-case-pilots' / module.__name__.split('.')[-1]
    assert module.run(directory, 'pilot')['execution_complete']
    assert common.read(directory / 'CASES.json') == rows
