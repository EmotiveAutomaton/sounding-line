"""A complete synthetic packet replays; partial cells and target tampering fail."""
import pytest
from runners.stage11_1 import run_v3 as run,report_v3 as report
from runners.stage11_1.common import contract,allocation,freeze,digest,read
from runners.stage11.replay import replay
from runners.stage11.run import fixture
from runners.stage11_1.targets import project,public


def test_complete_scoring_replay_and_private_target_binding(tmp_path,monkeypatch):
    contract(tmp_path);allocation(tmp_path);lines=fixture();e=replay(lines)['events'][0]
    row=dict(key='case',writer='writer',session='session',prompt='prompt',target=project(e,lines),views={'artifact':public(e,'artifact')})
    cohort=dict(train=[dict(row,key='training')],discovery=[row]);freeze(tmp_path/'COHORT-v3.json',cohort)
    job=dict(id='known',branch='S1',partition='constructed',keys=['case'],views=['artifact'],methods=['direct','review','account'],
        threads=4,pursuit='known scoring',warrant='instrument only',next_action='real pilot',cohort_file='COHORT-v3.json')
    plan=dict(id='known',cohort_file='COHORT-v3.json',cohort_digest=digest(cohort),jobs=[job],next_action='real pilot')
    path=tmp_path/'plans/known.json';freeze(path,plan)
    with pytest.raises(FileNotFoundError):report.analyze('known',tmp_path)
    run.execute(tmp_path,path,fake=True)
    def forbidden(*a,**kw):raise AssertionError('scoring made a network call')
    monkeypatch.setattr(run,'api',forbidden)
    first=report.analyze('known',tmp_path)
    assert first==report.analyze('known',tmp_path) and len(first['cells'])==5
    assert first['units']=='constructed instrument rehearsal'
    changed=read(tmp_path/'COHORT-v3.json');changed['discovery'][0]['target']['handling']='ignore'
    (tmp_path/'COHORT-v3.json').write_text(__import__('json').dumps(changed),encoding='utf-8')
    with pytest.raises(ValueError,match='private targets'):report.analyze('known',tmp_path)
