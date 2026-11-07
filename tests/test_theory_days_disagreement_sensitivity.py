from itertools import product
from collections import Counter
from math import comb
import numpy as np
import pandas as pd
import pytest
from runners.theory_days import disagreement_sensitivity as s
from runners.theory_days import emotions as e

def frame_from_counts(counts):
    rows=[];comment=0
    for t,n in zip(s.PATTERNS,counts):
        for _ in range(int(n)):
            for rater,k in enumerate(t):
                row={x:0 for x in e.LABELS};row[s.NAMES[k]]=1
                row.update(id=str(comment),rater_id=rater);rows.append(row)
            comment+=1
    return pd.DataFrame(rows)

def test_population_null_both_signs_and_marginals():
    mat=s.features()
    for delta in s.DOSES:
        p=s.probabilities(delta);r=s.population(delta)
        counts=np.array([np.bincount(t,minlength=14) for t in s.PATTERNS])
        assert np.allclose(p@counts/3,np.full(14,1/14),rtol=0,atol=1e-14)
        assert all(abs(row['difference']-delta)<1e-12 for row in r['pairs'])
    assert s.population(0)['packet']['fixed']=='inconclusive'
    assert s.population(.2)['packet']['fixed']=='supports'
    assert s.population(-.2)['packet']['fixed']=='against'

def test_pattern_counts_against_literal_ordered_raters():
    counts=np.zeros(len(s.PATTERNS),dtype=int)
    for t,n in [((0,0,1),2),((0,1,2),3),((5,5,5),1)]:counts[s.PATTERNS.index(t)]=n
    frame=frame_from_counts(counts);matrix,pairs,_=e.pair_sufficient(frame);full=matrix.sum(0)
    actual=counts@s.features();p=len(s.PAIRS);q=len(pairs)
    for k,(a,b) in enumerate(s.PAIRS):
        i=e.LABELS.index(s.NAMES[a]);j=e.LABELS.index(s.NAMES[b]);idx=list(map(tuple,pairs)).index((i,j))
        assert [actual[k],actual[p+k],actual[2*p+k]]==[full[idx],full[q+idx],full[2*q+idx]]
    assert np.array_equal(actual[-2:],full[-2:])

def test_grouping_preserves_exhaustive_bootstrap_law():
    # Three original comments: two identical patterns and one different.
    mat=s.features()[[0,1]];original=mat[[0,0,1]]
    literal=Counter(tuple(original[list(ids)].sum(0)) for ids in product(range(3),repeat=3))
    grouped=Counter()
    for k in range(4):grouped[tuple(k*mat[0]+(3-k)*mat[1])]+=comb(3,k)*2**k
    assert literal==grouped and sum(literal.values())==27

def test_actual_original_consumer_point_and_competitor_parity():
    counts=np.random.default_rng(20261106).multinomial(4000,s.probabilities(.2))
    original=e.disagreement(frame_from_counts(counts),draws=16)
    grouped=s.analyze(counts,draws=16)
    for a,b in zip(original['pairs'],grouped['pairs']):
        assert a['channel']==b['channel'] and a['within_expected']==b['within_expected']
        assert a['within_lift']==b['within_lift']
        assert a['cross_channel']['competitor']==b['competitor']
        assert a['cross_channel']['difference']==b['difference']
        assert a['unassigned']['status']==b['unassigned']=='unsupported competitor'

def test_complete_rule_and_unsupported_not_zero():
    sums=np.ones(len(s.PAIRS)*3+2);sums[-2:]=[3,6]
    r=s.summarize(sums,np.ones((2,len(s.PAIRS))))
    assert all(x['status']=='unsupported competitor' and x['difference'] is None for x in r['pairs'])
    assert r['packet']==dict(fixed='inconclusive',reselected='inconclusive')
    with pytest.raises(ValueError):s.analyze(np.zeros(len(s.PATTERNS),dtype=int),16)

def test_native_handler_reentry(tmp_path):
    config=dict(constructed=True)
    s.execute(tmp_path,{},config);before=(tmp_path/'CALIBRATION.json').read_bytes()
    s.execute(tmp_path,{},config);assert s.verify(tmp_path,{},config)['complete_recalculation']
    assert (tmp_path/'CALIBRATION.json').read_bytes()==before
