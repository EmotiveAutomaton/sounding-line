import itertools,math
import numpy as np
import pytest
from runners.theory_days import moral_expectation as m

def test_expectation_against_literal_subsets():
    for n in range(3,11):
        for s in range(n+1):
            for k in range(1,n+1):
                row=[1]*s+[0]*(n-s)
                choices=list(itertools.combinations(row,k))
                wanted=sum(len(set(c))==1 for c in choices)/math.comb(n,k)
                assert float(m.expectation(n,s,k))==pytest.approx(wanted,abs=1e-10)

def test_signed_and_identical_worlds():
    assert m.fixture(1)['primary']['verdict']=='supports'
    assert m.fixture(-1)['primary']['verdict']=='against'
    r=m.fixture(0)['primary'];assert r['difference']==0 and r['interval'][0]<0<r['interval'][1]

def test_invalid_counts_refuse():
    for args in ((3,4,2),(3,-1,2),(3,1,4),(0,0,0),(3.5,1,2)):
        with pytest.raises(ValueError):m.expectation(*args)

def test_compression_is_exact_and_retains_pairing():
    vectors=np.repeat(np.array([[-1,1],[0,0],[1,-1]],float),[100,500,400],axis=0)
    result,classes=m.intervals(vectors,2000,[(-1,1),(-1,1)])
    assert classes==3 and result[0]['difference']==pytest.approx(.3)
    assert result[1]['difference']==pytest.approx(-.3)
    assert result[0]['interval']==pytest.approx([-x for x in result[1]['interval'][::-1]])

def test_native_handler_and_independent_replay(tmp_path):
    out=tmp_path/'absent';m.execute(out,{},dict(constructed=True))
    assert m.verify(out,{},dict(constructed=True))['complete_recalculation']
