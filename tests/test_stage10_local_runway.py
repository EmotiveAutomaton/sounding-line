import copy
from pathlib import Path
import pytest

from runners.stage10 import local_runway as runway
from runners.stage10.ollama import write_new


def fixture_plan(tmp_path, monkeypatch):
    monkeypatch.setattr(runway, 'GPU_LOCK', tmp_path / 'gpu.lock')
    source = tmp_path / 'runners/stage10/example.py'
    source.parent.mkdir(parents=True); source.write_text('fixture')
    jobs = []
    for name, dependencies in [('first', []), ('dependent', ['first']), ('independent', [])]:
        output = 'results/phase_2_4_stage_10/raw/' + name
        jobs.append({'id': name, 'module': 'runners.stage10.example', 'args': ['--output', output],
                     'requires': dependencies, 'output': output, 'resource': 'cpu', 'purpose': 'constructed queue check'})
    plan = {'schema': 'stage10.local-runway.1', 'gear': 2, 'scope': 'constructed',
            'sources': {'runners/stage10/example.py': runway.file_hash(source)}, 'jobs': jobs}
    path = tmp_path / 'PLAN.json'; write_new(path, plan)
    return path, plan


def test_failure_blocks_dependants_but_runs_independent_and_replays_without_work(tmp_path, monkeypatch):
    path, plan = fixture_plan(tmp_path, monkeypatch); called = []
    def execute(job, target):
        called.append(job['id'])
        if job['id'] == 'first':
            write_new(target / 'FAILED.json', {'error': 'known injected fault'})
            return 1
        write_new(target / 'COMPLETE.json', {'status': 'COMPLETE'})
        write_new(target / 'RAW.json', {'known': 'retained'})
        return 0
    result = runway.run(path, tmp_path / 'queue', repo=tmp_path, execute=execute)
    assert called == ['first', 'independent']
    assert [r['status'] for r in result['jobs'].values()] == ['FAILED', 'BLOCKED', 'COMPLETE']
    assert result['all_jobs_succeeded'] is False
    def forbidden(*args):
        raise AssertionError('replay attempted new work')
    assert runway.run(path, tmp_path / 'queue', repo=tmp_path, execute=forbidden) == result
    (tmp_path / plan['jobs'][2]['output'] / 'RAW.json').write_text('{}')
    with pytest.raises(ValueError, match='evidence changed'):
        runway.run(path, tmp_path / 'queue', repo=tmp_path, execute=forbidden)


def test_cloud_escape_overlap_and_forward_dependencies_refuse(tmp_path, monkeypatch):
    _, plan = fixture_plan(tmp_path, monkeypatch)
    for change in ['cloud', 'escape', 'overlap', 'forward']:
        broken = copy.deepcopy(plan)
        if change == 'cloud': broken['jobs'][0]['module'] = 'runners.stage10.gear3_worker'
        if change == 'escape': broken['jobs'][0]['output'] = '../foreign'
        if change == 'overlap': broken['jobs'][1]['output'] = broken['jobs'][0]['output'] + '/nested'
        if change == 'forward': broken['jobs'][0]['requires'] = ['independent']
        with pytest.raises(ValueError): runway.validate(broken, tmp_path)


def test_interrupted_owner_and_clean_exit_without_output_are_not_success(tmp_path, monkeypatch):
    path, _ = fixture_plan(tmp_path, monkeypatch)
    out = tmp_path / 'queue'
    out.mkdir();write_new(out / 'OWNER.json', {'native': {'pid': 1}})
    with pytest.raises(ValueError, match='ownership inspection'):
        runway.run(path, out, repo=tmp_path, execute=lambda *a: 0)
    other = tmp_path / 'other'
    result = runway.run(path, other, repo=tmp_path, execute=lambda *a: 0)
    assert result['jobs']['first']['status'] == 'FAILED'
    assert result['jobs']['dependent']['status'] == 'BLOCKED'
    assert result['jobs']['independent']['status'] == 'FAILED'


def test_actual_native_finite_dispatch(tmp_path,monkeypatch):
    path,plan=fixture_plan(tmp_path,monkeypatch)
    source=tmp_path/'runners/stage10/example.py'
    source.write_text("import argparse,json\nfrom pathlib import Path\np=argparse.ArgumentParser();p.add_argument('--output');a=p.parse_args();d=Path(a.output);d.mkdir(parents=True);(d/'COMPLETE.json').write_text(json.dumps({'status':'COMPLETE'}))\n")
    plan['sources']['runners/stage10/example.py']=runway.file_hash(source)
    path.write_text(__import__('json').dumps(plan))
    result=runway.run(path,tmp_path/'queue',repo=tmp_path)
    assert result['all_jobs_succeeded'] is True and len(result['jobs'])==3
