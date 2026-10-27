import json
import numpy as np
import pytest
from runners.drive.cards import week3_pp3_analysis as m


def test_simplex_known_projection_and_translation():
    a=np.array([[1.,0.,0.],[-1.,-1.,-1.],[2.,2.,-9.]])
    assert np.allclose(m.simplex(a),[[1,0,0],[1/3]*3,[.5,.5,0]])
    assert np.allclose(m.simplex(a),m.simplex(a+18))
    with pytest.raises(ValueError):m.simplex([[float('nan'),0,0]])


def test_macro_f1_fixed_classes_and_cluster_sum():
    assert m.f1(np.eye(3)*10)==1
    assert m.f1(np.diag([5,0,0]))==pytest.approx(1/3)
    assert m.f1(np.zeros((3,3)))==0
    cm=np.array([[[2,1,0],[0,1,0],[0,0,0]],[[0,0,0],[0,1,1],[0,0,2]]])
    assert m.f1(cm.sum(axis=0))!=pytest.approx(m.f1(cm).mean())


def test_project_holdout_cannot_change_training_preprocessing():
    x,c,y,p,a=m.fixture();train=np.flatnonzero(p!=0);test=np.flatnonzero(p==0)
    d=m.fit_design(x,train,test);alter=x.copy();alter[test]+=100
    q=m.fit_design(alter,train,test)
    assert np.array_equal(d[0],q[0]) and np.array_equal(d[2][0],q[2][0])
    assert not np.array_equal(d[1],q[1])


def test_ridge_matches_direct_normal_equations():
    x,c,y,p,a=m.fixture();train=np.flatnonzero(p!=0);test=np.flatnonzero(p==0)
    d=m.fit_design(x,train,test);p3,p15,prior=m.predict(d,y[train])
    z,t,_=d;target=np.eye(len(m.CLASSES))[y[train]]
    coef=np.linalg.solve(z.T@z+np.eye(z.shape[1]),z.T@(target-prior))
    raw=t@coef+prior
    assert np.allclose(p15,m.simplex(raw),atol=1e-12)
    assert np.allclose(p3,m.simplex(np.column_stack([raw[:,m.MAP==j].sum(axis=1) for j in range(3)])))


def test_reassignment_preserves_each_group_counts_and_prefix():
    x,c,y,p,a=m.fixture()
    for groups in [p,a]:
        out=m.permute(y,groups,np.random.default_rng(3))
        assert not np.array_equal(y,out)
        for g in np.unique(groups):assert np.array_equal(np.sort(y[groups==g]),np.sort(out[groups==g]))
    assert np.array_equal(m.permute(y,p,np.random.default_rng(3)),m.permute(y,p,np.random.default_rng(3)))


def test_constructed_signal_null_and_probabilities():
    assert all(m.known_answers().values())


def test_project_bootstrap_keeps_authors_together():
    x,c,y,p,a=m.fixture();w=m.resample_weights(a,p,'project',np.random.default_rng(7),2000)
    assert w.shape==(2000,10)
    assert np.array_equal(w[:,::2],w[:,1::2])
    assert (w[:,::2].sum(axis=1)==5).all()


def test_fold_census_all_rows_and_all_classes():
    x,c,y,p,a=m.fixture();d=m.build_designs(x,c,p)
    assert sorted(np.concatenate([test for _,_,test,_ in d]).tolist())==list(range(len(y)))
    for project,train,test,arms in d:assert not set(train)&set(test)
    r=m.evaluate(d,y,p,a)
    assert r['cm3'].sum()==len(y)*2 and r['cm15'].sum()==len(y)


def test_full_native_contract_roundtrip_and_corruption(tmp_path):
    out=tmp_path/'new';config=dict(mode='constructed',permutations=8)
    r=m.execute(out,{},config);assert r['rows']==450 and 'summaries' not in r
    assert m.verify(out,{},config)['full_source_models_references_bootstrap_replay']
    check=json.loads((out/'CHECKPOINT_0_000.json').read_text())
    assert set(check)=={'bank','draw','fingerprints'}
    data=json.loads((out/'SUMMARY.json').read_text());data['rows']-=1
    (out/'SUMMARY.json').write_text(json.dumps(data))
    with pytest.raises(ValueError):m.verify(out,{},config)


def test_nonfrozen_banks_refused(tmp_path):
    with pytest.raises(ValueError):m.execute(tmp_path,{},dict(mode='main',permutations=20))
    with pytest.raises(ValueError):m.read_source({'unexpected':'x'},'constructed')
