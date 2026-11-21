import numpy as np
from runners.drive.cards import week6_br_pairs_v1 as pairs


def test_shared_and_independent_pairs():
    rng=np.random.default_rng(517)
    n=110
    a,b=rng.normal(size=(2,n))
    def make(signal):
        level=rng.normal(size=n)
        return [dict(b=signal+rng.normal(0,.05,n),L=level+rng.normal(0,.1,n),S=np.ones(n),sxx=np.full(n,8.)) for _ in range(2)]
    left=make(a)
    for right,expected in [(make(a),'one'),(make(b),'several')]:
        entry,draws=pairs.estimate_pair((left,right),n,[34,1],lambda:None)
        assert entry['reading']=='estimable'
        covariance=entry['covariance']['estimate']
        denominator=np.sqrt(np.prod([v['estimate'] for v in entry['variances']]))
        assert np.isclose(covariance/denominator,draws[0])
        assert len(draws)==2001 and pairs.pool([draws])['reading']==expected


def test_missing_and_empty_strata():
    assert pairs.pool([])['reading']=='no verdict'
    assert pairs.pool([[.3,.2,np.nan]])['reading']=='undecided'

