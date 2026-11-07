import itertools,math,copy
import numpy as np
import pytest
from runners.theory_days import moral_exposure as m

def test_both_exposures_against_literal_subsets():
    for n in range(3,9):
        for s in range(n+1):
            for k in (3,n):
                choices=list(itertools.combinations([1]*s+[0]*(n-s),k))
                expected=sum(len(set(x))==1 for x in choices)/math.comb(n,k)
                assert float(m.expectation(n,s,k))==pytest.approx(expected,abs=1e-10)

def test_signed_and_identical_and_three_choice_identity():
    r=m.fixtures();assert r['0']['paired_change']['difference']==0
    a=np.tile([[3,1],[3,3],[3,0],[3,2]],(1200,1,1))
    s=m.summarize(a,np.zeros((1200,4)),64)
    assert s['minimum_rates']==s['three_rates']
    assert s['paired_change']['difference']==0 and s['paired_change']['interval'][0]<0<s['paired_change']['interval'][1]
    assert s['share_minimum_three']==1 and s['minimum_count_histogram']=={'3':1200}

def test_joint_interval_tails_and_exact_pairing():
    v=np.r_[np.tile([0,1,1],(400,1)),np.tile([1,0,-1],(800,1))]
    result,n=m.summaries(v,2000);rng=np.random.default_rng(20261106)
    w=rng.multinomial(1200,[1/3,2/3],size=2000);b=w@np.array([[0,1,1],[1,0,-1]])/1200
    assert n==2
    for j,alpha in enumerate((.025,.025,.05)):
        assert result[j]['interval']==pytest.approx(np.quantile(b[:,j],[alpha/2,1-alpha/2]))

def test_corrupt_parent_and_bad_counts_refuse():
    r=m.fixtures()['1'];p=dict(common_fingerprints=1200,equal_exposure_rates=r['original_subset_rates'],primary=dict(difference=0))
    q=dict(common_fingerprints=1200,expected_rates=r['minimum_rates'],primary=dict(difference=r['minimum']['difference']))
    m.check_parents(r,p,q);bad=copy.deepcopy(q);bad['expected_rates']['Species']=.5
    with pytest.raises(AssertionError):m.check_parents(r,p,bad)
    with pytest.raises(ValueError):m.summarize(np.tile([[2,1]]*4,(1200,1,1)),np.zeros((1200,4)))
    with pytest.raises(ValueError):m.summarize(np.tile([[3,4]]*4,(1200,1,1)),np.zeros((1200,4)))
    assert m.summarize(np.tile([[3,1]]*4,(999,1,1)),np.zeros((999,4)))['status']=='design cannot test'

def test_native_handlers_and_immutable_reentry(tmp_path):
    m.execute(tmp_path,{},dict(constructed=True));before=(tmp_path/'SCIENCE.json').read_bytes()
    assert m.verify(tmp_path,{},dict(constructed=True))['complete_recalculation']
    m.execute(tmp_path,{},dict(constructed=True));assert (tmp_path/'SCIENCE.json').read_bytes()==before
