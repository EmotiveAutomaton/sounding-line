import copy,math
import numpy as np
import pytest
from runners.drive.cards import week4_d7_stability as d


def test_parent_fit_and_independent_two_partition_oracles():
    for dose in (0,.8,-.8):
        assert d.native_oracles(d.m.world(writers=1,dose=dose))


def test_constant_null_exact_and_undefined_correlation():
    rows=d.m.world(writers=4)
    for r in rows:r['dwell_seconds']=math.expm1(2)
    fits,_=d.fits(d.m.writers(rows))
    assert all(v['earlier']==v['later']==v['delta']==0 for v in fits.values())
    summary=d.summarize(fits,[fits]*2,[fits]*2,20,0)
    assert summary['delta']==summary['ci_low']==summary['ci_high']==0
    assert not summary['directional_call']
    assert summary['correlation'] is None and summary['correlation_interval'] is None
    assert summary['correlation_undefined_resamples']==20


def test_test_outcome_never_selects_penalty_or_training_fit():
    rows=d.m.world(writers=1);before=d.compare(rows)
    changed=copy.deepcopy(rows);test=d.m.partition(rows)[0][2]
    for i in test:changed[i]['dwell_seconds']+=100
    after=d.compare(changed)
    for key in ('training_coefficients','penalty','calibration_loss'):assert before[key]==after[key]
    assert before['later_coefficients']!=after['later_coefficients']


def test_stationary_template_and_signed_shift_geometry():
    for regime in ('null','nuisance'):
        rows,_=d.world(regime,1,writers=6)
        values,_=d.fits(d.m.writers(rows))
        assert max(abs(v['delta']) for v in values.values())<1e-10
    for ordinal,sign in ((0,1),(1,-1)):
        rows,shift=d.world('signed',1,writers=6,ordinal=ordinal)
        values,_=d.fits(d.m.writers(rows))
        assert shift*sign>0 and all(v['delta']*sign>0 for v in values.values())


def test_signed_correlation_not_absolute_and_zero_variance_explicit():
    a=np.arange(5,dtype=float)
    assert d.correlation(a,2*a+1)==pytest.approx(1)
    assert d.correlation(a,-a)==pytest.approx(-1)
    assert d.correlation(a,np.zeros(5)) is None
    with pytest.raises(ValueError,match='Nonfinite'):d.correlation(a,np.full(5,np.nan))


def test_duplicate_writer_bootstrap_matches_complete_refits():
    rows,_=d.world('signed',1,writers=3);groups=d.m.writers(rows);fits,_=d.fits(groups)
    selected=['2','0','2'];direct=[]
    for i,w in enumerate(selected):direct.append(d.compare([dict(r,writer=str(i)) for r in groups[w]]))
    for key in ('earlier','later','delta'):
        assert np.mean([fits[w][key] for w in selected])==np.mean([r[key] for r in direct])


def test_two_sided_tail_and_negative_direction():
    real={str(w):dict(earlier=float(w),later=float(w)-1,delta=-1.) for w in range(4)}
    null={str(w):dict(earlier=float(w),later=float(w),delta=0.) for w in range(4)}
    v=d.summarize(real,[null]*200,[real]*200,20,1)
    assert v['joint_permutation']['two_sided_p']==1/201 and v['directional_call']
    assert v['ci_high']<0 and v['fake_writer']['mean']==-1


def test_support_change_and_incomplete_bank_rejected_before_fitting(tmp_path,monkeypatch):
    rows,_=d.world('null',1,writers=6);cfg=d.configuration('constructed')
    bank=d.h.h.bank(rows,draws=2)['accepted'];bank[0]['assignment']={k:'one' for k in bank[0]['assignment']}
    monkeypatch.setattr(d,'fits',lambda *a,**k:(_ for _ in ()).throw(AssertionError('premature fit')))
    with pytest.raises(ValueError,match='roster changed'):d.analyze(tmp_path,'x',rows,bank,cfg)
    with pytest.raises(ValueError,match='complete support'):d.analyze(tmp_path,'x',rows,bank[:1],cfg)


def test_actual_handler_replay_reentry_and_corrupt_checkpoint(tmp_path):
    cfg=d.configuration('constructed');first=d.execute(tmp_path,{},cfg)
    assert not first['human_scored'] and not first['calibration']['passes']
    assert d.verify(tmp_path,{},cfg)['full_fresh_fit_replay']
    assert d.execute(tmp_path,{},cfg)==first
    next(tmp_path.glob('*-joint-0.json')).write_text('{}')
    with pytest.raises(ValueError,match='record replay'):d.verify(tmp_path,{},cfg)
    with pytest.raises(ValueError,match='Frozen'):d.execute(tmp_path,{},dict(cfg,references=1))
    with pytest.raises(ValueError,match='Exact D7.m'):d.human_source({},True)


def test_full_calibration_gate_rejects_false_stationarity_and_wrong_direction():
    worlds=[]
    for regime,doses in [('null',[0]*10),('nuisance',[0]*10),('signed',[.8,-.8]*5)]:
        for dose in doses:
            worlds.append(dict(regime=regime,dose=dose,analysis=dict(summary=dict(delta=dose,directional_call=bool(dose)))))
    assert d.assess(worlds)['passes']
    assert not d.assess(worlds[:-1])['passes']
    bad=copy.deepcopy(worlds);bad[0]['analysis']['summary']['delta']=1e-5
    assert not d.assess(bad)['passes']
    for row in worlds:
        if row['dose']<0:row['analysis']['summary']['delta']*=-1
    assert not d.assess(worlds)['passes']


def test_timing_replaces_human_labels_and_requires_complete_sources():
    rows=d.m.world(writers=1);changed=copy.deepcopy(rows)
    for r in changed:r['dwell_seconds']+=100;r['accepted']=not r['accepted']
    assert d.h.generated(rows,1)==d.h.generated(changed,1)
    with pytest.raises(ValueError,match='Exact D7.m'):d.human_source({},False)
