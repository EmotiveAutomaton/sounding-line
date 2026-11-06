import copy
import math
import numpy as np
import pytest
from runners.drive.cards import week4_d7_specification as s


def writer_rows(dose=.8):
    return s.m.world(writers=1,dose=dose)


def test_fixed_curve_exact_original_and_independent_oracle():
    for dose in (0,.8,-.8):
        rows=writer_rows(dose)
        assert s.native_oracles(rows)
        if dose:
            assert all(v['gain']>0 and v['fits'][1]['coefficients'][-1]*dose>0 for v in s.compare(rows).values())


def test_constant_null_is_exact_zero_and_no_selected_penalty():
    rows=writer_rows()
    for row in rows:row['dwell_seconds']=math.expm1(2)
    curve=s.compare(rows)
    assert tuple(curve)==s.KEYS
    for key,penalty in zip(s.KEYS,s.PENALTIES):
        assert curve[key]['gain']==0
        assert [f['penalty'] for f in curve[key]['fits']]==[penalty,penalty]


def test_test_outcome_and_calibration_outcome_never_fit_or_select():
    rows=writer_rows();before=s.compare(rows);changed=copy.deepcopy(rows)
    _,cal,test=s.m.partition(rows)[0]
    for i in np.r_[cal,test]:changed[i]['dwell_seconds']+=1000
    after=s.compare(changed)
    for key in s.KEYS:
        assert before[key]['predictions']==after[key]['predictions']
        assert [f['coefficients'] for f in before[key]['fits']]==[f['coefficients'] for f in after[key]['fits']]


def test_duplicate_writer_resampling_equals_complete_refits():
    rows=s.m.world(writers=3);groups=s.m.writers(rows);fits,_=s.fits(groups)
    selected=['2','0','2'];direct=[]
    for i,w in enumerate(selected):
        duplicate=[dict(r,writer=str(i)) for r in groups[w]]
        direct.append(s.compare(duplicate))
    for key in s.KEYS:
        assert float(np.mean([fits[w][key]['gain'] for w in selected]))==float(np.mean([r[key]['gain'] for r in direct]))


def test_support_change_and_incomplete_reference_refuse_before_fit(tmp_path,monkeypatch):
    rows=s.m.world(writers=6);cfg=s.configuration('constructed');bank=s.h.h.bank(rows,draws=2)['accepted']
    bank[0]['assignment']={name:'one' for name in bank[0]['assignment']}
    monkeypatch.setattr(s,'fits',lambda *a,**k:(_ for _ in ()).throw(AssertionError('premature fit')))
    with pytest.raises(ValueError,match='roster changed'):s.analyze(tmp_path,'x',rows,bank,cfg)
    with pytest.raises(ValueError,match='complete support'):s.analyze(tmp_path,'x',rows,bank[:1],cfg)


def test_native_full_handler_replay_reentry_and_tamper(tmp_path):
    cfg=s.configuration('constructed');first=s.execute(tmp_path,{},cfg)
    assert not first['human_scored'] and not first['calibration']['passes']
    assert s.verify(tmp_path,{},cfg)['full_fresh_fit_replay']
    assert s.execute(tmp_path,{},cfg)==first
    next(tmp_path.glob('*-joint-0.json')).write_text('{}')
    with pytest.raises(ValueError,match='fitted-arm replay'):s.verify(tmp_path,{},cfg)
    with pytest.raises(ValueError,match='Frozen'):s.execute(tmp_path,{},dict(cfg,references=1))
    with pytest.raises(ValueError,match='Exact D7.s'):s.human_source({},True)


def test_all_penalties_must_pass_complete_calibration():
    worlds=[]
    for regime,doses in [('null',[0]*10),('nuisance',[0]*10),('signed',[.8,-.8]*5)]:
        for i,dose in enumerate(doses):
            curve={key:dict(positive=bool(dose),mean_added_coefficient=dose) for key in s.KEYS}
            worlds.append(dict(label=regime+str(i),regime=regime,dose=dose,analysis=dict(curve=curve)))
    assert s.assess(worlds)['passes']
    worlds[0]['analysis']['curve'][s.KEYS[0]]['positive']=True
    worlds[1]['analysis']['curve'][s.KEYS[0]]['positive']=True
    assert not s.assess(worlds)['passes']
    assert not s.assess(worlds[:-1])['passes']


def test_cost_preserves_setup_counts_both_phases_and_full_banks():
    times=[dict(setup_cpu_seconds=10,fitting_cpu_seconds=2,max_complete_writer_cpu_seconds=.001,fitted_arm_bytes=100)]
    f=s.forecast(times,True)
    assert f['whole_implementation_forecast']==6*(10+2*401*30/15)
    assert f['complete_writer_forecast']==6*(10+.001*12*401*30+60)
    assert f['full_cpu_seconds']==max(f['whole_implementation_forecast'],f['complete_writer_forecast'])
    rows=writer_rows();changed=copy.deepcopy(rows)
    for r in changed:r['accepted']=not r['accepted'];r['dwell_seconds']+=1000
    assert s.h.generated(rows,1)==s.h.generated(changed,1)
