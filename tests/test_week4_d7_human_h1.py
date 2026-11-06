import copy
import pytest
from runners.drive.cards import week4_d7_human_h1 as m


def test_native_consumer_exact_original_parity_and_fresh_replay(tmp_path):
    cfg=m.configuration('constructed');s=m.execute(tmp_path,{},cfg)
    assert s['native_consumer_parity'] and not s['human_scored']
    assert m.verify(tmp_path,{},cfg)['full_fresh_fit_replay']


def test_generated_cost_ignores_all_actual_outcomes():
    rows,_=m.c.world('null',20261026,6);changed=copy.deepcopy(rows)
    for i,r in enumerate(changed):r['accepted']=not r['accepted'];r['dwell_seconds']=i*1000
    assert m.generated(rows,1)==m.generated(changed,1)


def test_bank_must_bind_complete_original_cohort():
    rows,_=m.c.world('null',20261026,6);b=m.h.bank(rows)
    assert len(m.validate_bank(rows,b))==200
    broken=copy.deepcopy(b);broken['accepted'][0]['assignment']['0:0']='broken'
    with pytest.raises(ValueError,match='proposal law'):m.validate_bank(rows,broken)
    broken=copy.deepcopy(b);broken['complete']=False
    with pytest.raises(ValueError,match='Incomplete'):m.validate_bank(rows,broken)


def test_changed_control_support_refuses_before_fit(tmp_path,monkeypatch):
    rows,_=m.c.world('null',20261026,6);a=m.h.bank(rows,draws=2)['accepted']
    a[0]['assignment']={s:'one' for s in a[0]['assignment']}
    monkeypatch.setattr(m.c,'fits',lambda *a,**k:(_ for _ in ()).throw(AssertionError('fit too early')))
    with pytest.raises(ValueError,match='roster changed'):m.analyze(tmp_path,'x',rows,a,m.configuration('constructed'))


def test_reference_tamper_and_configuration_refuse(tmp_path):
    cfg=m.configuration('constructed');m.execute(tmp_path,{},cfg)
    (tmp_path/'null-joint-0.json').write_text('{}')
    with pytest.raises(ValueError,match='fitted-arm replay'):m.verify(tmp_path,{},cfg)
    with pytest.raises(ValueError,match='Frozen'):m.execute(tmp_path,{},dict(cfg,references=1))
    with pytest.raises(ValueError,match='Exact D7'):m.source({})


def test_forecast_accounts_full_setup_and_scales_all_fitted_arms():
    a=dict(setup_cpu_seconds=10,fitting_cpu_seconds=5,max_complete_writer_cpu_seconds=.01)
    b=dict(setup_cpu_seconds=20,fitting_cpu_seconds=10,max_complete_writer_cpu_seconds=.02)
    f=m.forecast([a,b])
    assert f['whole_implementation_forecast']==6*(20+10*401/5)
    assert f['complete_writer_forecast']==6*(20+.02*38*401+60)
    assert f['full_cpu_seconds']==max(f['whole_implementation_forecast'],f['complete_writer_forecast'])
