import itertools, math, copy
import numpy as np
import pytest
from runners.theory_days import moral_texture as m


def test_literal_subset_expectations():
    for n in range(4,9):
        for s in range(n+1):
            for k in range(4,n+1):
                c=list(itertools.combinations([1]*s+[0]*(n-s),k))
                want=sum(len(set(x))==1 for x in c)/math.comb(n,k)
                assert float(m.expectation(n,s,k))==pytest.approx(want,abs=1e-10)


def test_signed_null_finite_uncertainty_and_stopping():
    r=m.fixtures()
    for c in r['0']['cards'][:5]:
        lo,hi=c['contrasts']['fixed']['interval'];assert lo<0<hi
    assert r['0']['cards'][4]['consecutive_stable']==5
    a=np.tile([[12,6]]*4,(1200,1,1))
    assert all(c['status']=='complete' for c in m.family(a,0,[-.1,.1],64,stop=False)['cards'])


def test_nested_selection_exposure_identity_and_support():
    a=np.concatenate([np.tile([[4,2]]*4,(200,1,1)),np.tile([[5,0],[5,0],[5,2],[5,3]],(1100,1,1))])
    four=m.card(a,4,64);five=m.card(a,5,64);six=m.card(a,6,64)
    assert [four['eligible_fingerprints'],five['eligible_fingerprints'],six['eligible_fingerprints']]==[1300,1100,0]
    assert five['rates']['fixed']==five['rates']['minimum']
    assert six['status']=='unsupported'
    r=m.family(a,0,[-.1,.1],64)
    assert r['cards'][2]['status']=='unsupported' and all(x['status']=='not run' for x in r['cards'][3:])


def test_order_invariance_and_invalid_excluded_counts():
    a=np.tile([[8,0],[8,4],[8,3],[8,6]],(1200,1,1));a[::2,0,1]=8
    r=m.card(a,4,64);back=m.card(a[::-1],4,64)
    assert r==back
    a[0]=[[2,1]]*4
    with pytest.raises(ValueError):m.card(a,4,64)
    with pytest.raises(ValueError):m.family(a,0,[1,-1],64)


def test_native_replay_reentry_and_changed_parent(tmp_path):
    m.execute(tmp_path,{},dict(constructed=True));b=(tmp_path/'SCIENCE.json').read_bytes()
    assert m.verify(tmp_path,{},dict(constructed=True))['complete_recalculation']
    m.execute(tmp_path,{},dict(constructed=True));assert (tmp_path/'SCIENCE.json').read_bytes()==b
    r=dict(status='complete',common_fingerprints=1200,original_subset_rates={},original_subset_difference=0,
           minimum_rates={},minimum=dict(difference=0))
    p=dict(common_fingerprints=1200,equal_exposure_rates={},primary=dict(difference=0))
    q=dict(common_fingerprints=1200,expected_rates={},primary=dict(difference=0))
    m.check_parents(r,p,q);bad=copy.deepcopy(q);bad['primary']['difference']=1
    with pytest.raises(AssertionError):m.check_parents(r,p,bad)
