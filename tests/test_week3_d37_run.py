"""D37 actual complete-reference consumer validation and admission refusals.

DESIGN CHECK: LESSONS 3-5. Full banks and identical rows precede inference;
failing calibration cannot admit human scoring. Native execution exercises a
complete 201-arm constructed comparison, distinct from the 30-world gate.
"""
from pathlib import Path
from copy import deepcopy
import pytest
from runners.stage14.common import REPO
from runners.drive.cards import week3_d37_run as r
from runners.drive.cards import week3_d37_workload as w
from runners.drive.cards.timing_census import read,filehash
from runners.drive.cards.timing_p6 import write_equal


def test_checkpoint_identity_and_corruption(tmp_path):
    path=tmp_path/'one.json.gz'; value=dict(arm=0,values=[0.,1.])
    r.checkpoint(path,value);assert r.checkpoint(path)==value
    before=path.read_bytes();r.checkpoint(path,value);assert path.read_bytes()==before
    with pytest.raises(ValueError,match='Fresh fitted'):r.checkpoint(path,dict(arm=0,values=[1.,0.]))
    path.write_bytes(before+b'changed')
    with pytest.raises(ValueError,match='changed'):r.checkpoint(path)


def test_full_fitted_refits_and_retained_reentry(tmp_path,monkeypatch):
    rows,a,p,y,_=w.world(20)
    first=r.run_comparison(tmp_path,rows,a,p,y,arms=3)
    assert first['complete_arms']==3 and len(first['arm_hashes'])==3
    assert r.run_comparison(tmp_path,rows,a,p,y,verifying=True,arms=3)==first
    with monkeypatch.context() as mp:
        mp.setattr(r.core,'fit_recipient',lambda *args: (_ for _ in ()).throw(AssertionError('Must reuse sealed checkpoint')))
        assert r.run_comparison(tmp_path,rows,a,p,y,arms=3)==first


def test_binding_change_refuses_without_new_fit(tmp_path):
    rows,a,p,y,_=w.world(20);r.run_comparison(tmp_path,rows,a,p,y,arms=1)
    changed=y.copy();changed[0]=(changed[0]+1)%4
    with pytest.raises(ValueError):r.run_comparison(tmp_path,rows,a,p,changed,arms=1)


def results():
    return [dict(world=i,kind=('common','page_only','complementary')[i//10],
                 result=dict(licensed_positive=i>=20,useful_licensed_detection=i>=20)) for i in range(30)]


def test_calibration_gate_exact_bounds_and_missing_matrix():
    a=results();assert r.calibration_gate(a)['passes']
    for i in (0,1):a[i]['result']['licensed_positive']=True
    assert r.calibration_gate(a)['passes']
    a[2]['result']['licensed_positive']=True;assert not r.calibration_gate(a)['passes']
    a=results()
    for i in (20,21):a[i]['result']['useful_licensed_detection']=False
    assert r.calibration_gate(a)['passes']
    a[22]['result']['useful_licensed_detection']=False;assert not r.calibration_gate(a)['passes']
    with pytest.raises(ValueError,match='Incomplete'):r.calibration_gate(a[:-1])


def test_actual_cost_admission_and_changed_receipt(tmp_path):
    path=REPO/'.agent-state/drive-20261029/D37_COST_CORPUS_LANDED.json'
    assert r.admission(dict(cost_landing=str(path)),r.CONFIG|dict(mode='calibration'))['full_write_through']
    altered=tmp_path/'cost.json';write_equal(altered,read(path)|dict(forecast_sha256='0'*64))
    with pytest.raises(ValueError,match='Changed measured'):r.admission(dict(cost_landing=str(altered)),r.CONFIG|dict(mode='calibration'))
    with pytest.raises(ValueError,match='Frozen full'):r.admission(dict(cost_landing=str(path)),r.CONFIG|dict(mode='calibration',permutations=199))


def test_failed_calibration_refuses_human(tmp_path):
    root=tmp_path/'cal';(root/'output').mkdir(parents=True)
    write_equal(root/'COMPLETE.json',dict(status='COMPLETE'))
    write_equal(root/'output/SUMMARY.json',dict(config=r.CONFIG|dict(mode='calibration'),calibration=dict(passes=False)))
    landing=tmp_path/'landing.json';write_equal(landing,dict(full_write_through=True,completion=str(root/'COMPLETE.json'),
               completion_sha256=filehash(root/'COMPLETE.json'),summary_sha256=filehash(root/'output/SUMMARY.json')))
    from tests.test_week3_d37_cost import inputs
    given=inputs()|dict(cost_landing=str(REPO/'.agent-state/drive-20261029/D37_COST_CORPUS_LANDED.json'),calibration_landing=str(landing))
    with pytest.raises(ValueError,match='Failed full calibration'):r.admission(given,r.CONFIG|dict(mode='human'))


def execute(output,inputs,config):
    if config!=r.CONFIG|dict(mode='calibration') or set(inputs)!={'fixture'} or read(inputs['fixture'])!={'constructed':True}:raise ValueError('Invalid native fixture')
    rows,a,p,y,meta=w.world(20)
    r.run_comparison(Path(output)/'reference',rows,a,p,y)
    write_equal(Path(output)/'SUMMARY.json',dict(constructed=True,worlds=1,reference_arms=201,scientific_admission=False,calibration_complete=False))
    return dict(status='complete',constructed=True)


def verify(output,inputs,config):
    rows,a,p,y,_=w.world(20)
    r.run_comparison(Path(output)/'reference',rows,a,p,y,verifying=True)
    return dict(verified=True,full_constructed_reference_replay=True,calibration_complete=False)
