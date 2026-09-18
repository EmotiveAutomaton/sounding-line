"""Hard admission boundaries and no-call final consumer checks."""
import copy
import pytest
from runners.stage11 import core, run
from runners.stage11_packet import packet


@pytest.mark.parametrize('boundary,status',[('deadline','DEADLINE'),('calls','CALL_CAP'),('gpu','GPU_CAP'),('stop','STOPPED')])
def test_preflight_refuses_without_neural_call(tmp_path,monkeypatch,boundary,status):
    rows=run.synthetic_rows();cohort=dict(train=rows,development=rows,evaluation=rows)
    contract=dict(admissions_end='2099-01-01T00:00:00+00:00',gpu_seconds=14400,total_calls=256,development_calls=32,evaluation_calls=192)
    if boundary=='deadline':contract['admissions_end']='2000-01-01T00:00:00+00:00'
    if boundary=='calls':contract['total_calls']=0
    if boundary=='gpu':contract['gpu_seconds']=0
    if boundary=='stop':(tmp_path/'STOP').write_text('stop')
    core.freeze(tmp_path/'CONTRACT.json',contract);core.freeze(tmp_path/'COHORT.json',cohort)
    core.freeze(tmp_path/'PREPARED.json',dict(cohort_digest=core.digest(cohort)))
    core.freeze(tmp_path/'PILOT.json',dict(status='COMPLETE'))
    monkeypatch.setattr(run,'identity',lambda:{})
    monkeypatch.setattr(run,'api',lambda *a,**k:pytest.fail('preflight made neural request'))
    result=run.execute(tmp_path)
    assert result['status']==status and not (tmp_path/'calls').exists()


def test_fixed_feature_fit_recovers_planted_visible_relation():
    rows=[]
    for i in range(12):
        r=copy.deepcopy(run.synthetic_rows()[0]);long=i%2==0
        r.update(key=str(i),writer=str(i),truth='accept' if long else 'dismiss')
        for v in core.VIEWS:r['views'][v]['episode_end_document']='word '* (80 if long else 2)
        rows.append(r)
    fitted=core.fit(rows)
    for r in rows:
        for v in core.VIEWS:
            p=core.predict(r['views'][v],v,fitted,'features')
            assert core.ACTIONS[max(range(4),key=lambda j:p[j])]==r['truth']


def test_terminal_packet_exact_rebuild_and_private_text_boundary(tmp_path):
    raw=tmp_path/'raw';run.rehearse(raw)
    core.freeze(raw/'COMPLETE.json',dict(status='COMPLETE'))
    core.freeze(raw/'CONTRACT.json',dict(gpu_seconds=14400,total_calls=256))
    core.freeze(raw/'SOURCE.json',dict(exclusions=[]))
    first=packet(raw,tmp_path);saved=(tmp_path/'REPORT.md').read_bytes()
    assert packet(raw,tmp_path)==first and (tmp_path/'REPORT.md').read_bytes()==saved
    assert b'A small' not in saved
    assert 'A small' in (raw/'contribution-map.html').read_text(encoding='utf-8')
    assert core.read(tmp_path/'INTEGRITY.json')['within_caps']
