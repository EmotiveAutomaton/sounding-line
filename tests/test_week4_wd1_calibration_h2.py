import copy
import numpy as np
import pytest
from runners.drive.cards import week4_wd1_calibration_h2 as m


def record(values):
    return dict(profiles={str(i):dict(halves=[dict(sensitivity=float(v),criterion=-float(v)/2) for v in pair]) for i,pair in enumerate(values)})


def near(a,b):
    if isinstance(a,dict):
        assert set(a)==set(b)
        for k in a:near(a[k],b[k])
    elif isinstance(a,list):
        assert len(a)==len(b)
        for x,y in zip(a,b):near(x,y)
    elif isinstance(a,float):assert a==pytest.approx(b,abs=1e-12,rel=1e-12)
    else:assert a==b


def test_original_summary_agreement_and_invalidity_guards():
    rng=np.random.default_rng(99);fake=[record(rng.normal(size=(12,2))) for _ in range(60)]
    for sign in (1,-1,0):
        x=np.arange(12);real=record(np.c_[x,sign*x+rng.normal(size=12)])
        near(m.summarize(real,fake,200,34),m.old.summarize(real,fake,200,34))
    flat=record(np.ones((12,2)))
    near(m.summarize(flat,fake,10,34),m.old.summarize(flat,fake,10,34))
    bad=copy.deepcopy(fake);bad[0]['profiles'].pop('0')
    near(m.summarize(real,bad,10,34),m.old.summarize(real,bad,10,34))


def test_constructed_truth_has_exact_declared_relationships_and_sparse_support():
    for family in m.FAMILIES:
        sessions,rows,scalar,embedding,truth=m.world(family,20261104)
        assert len(sessions)==96 and len(rows)==2304
        assert sum(not s['rows'] for s in sessions)==24
        assert len(m.support.support(sessions)[0])==12
        slopes=np.array([[next(t['slope'] for t in truth if t['key'].startswith(f'w{w}:s{p}:')) for p in range(2)] for w in range(12)])
        intercepts=[t['intercept'] for t in truth]
        if family in ('null','criterion'):assert np.all(slopes==1.)
        else:assert m.old.correlation(slopes)==pytest.approx(1 if family=='stable' else -1)
        assert (len(set(intercepts))>1)==(family=='criterion')
    b=m.support.bank(sessions,100,200,20261104)
    assert b['complete'] and len(b['proposals'])>100


def test_gate_requires_complete_families_and_all_checks():
    rs=[dict(family=f,primary=dict(state='positive' if f=='stable' else 'negative' if f=='reversed' else 'null')) for f,n in zip(m.FAMILIES,(10,10,5,5)) for _ in range(n)]
    assert m.gate(rs)['passes']
    assert not m.gate(rs[:-1])['passes']
    rs[0]['primary']['state']='invalid';assert not m.gate(rs)['passes']
    rs[0]['primary']['state']='positive';rs[1]['primary']['state']='positive';assert not m.gate(rs)['passes']


def test_full_native_consumer_and_fresh_refits(tmp_path):
    cfg=m.configuration('constructed');r=m.execute(tmp_path,{},cfg)
    assert r['worlds']==4 and not r['calibration']['complete']
    assert m.verify(tmp_path,{},cfg)['full_fresh_calibration_refit']
    path=next((tmp_path/'worlds').glob('*/fits/0000.json'));path.write_text('{}')
    with pytest.raises(ValueError,match='replay differs'):m.verify(tmp_path,{},cfg)


def test_altered_contract_and_human_inputs_refused(tmp_path):
    with pytest.raises(ValueError,match='Frozen'):m.execute(tmp_path,{},dict(m.configuration('full'),permutation_draws=20))
    with pytest.raises(ValueError,match='Frozen'):m.execute(tmp_path,{'human':'file'},m.configuration('constructed'))
