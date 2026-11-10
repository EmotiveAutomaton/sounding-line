import numpy as np
from runners.drive.cards import week5_md_level_diagnostic as d


def test_multiple_correlation_known_answers_and_alias():
    rng=np.random.default_rng(2);q,_=np.linalg.qr(np.column_stack([np.ones(30),rng.normal(size=(30,6))]))
    x=q[:,1:5]
    for r in [0.,.5,.9,1.]:
        y=r*q[:,1]+np.sqrt(1-r*r)*q[:,5]
        value=d.multiple_r(np.column_stack([x,y]))
        assert abs(value['r']-r)<1e-8
        assert value['aliased']==(r==1.)
    assert d.multiple_r(np.column_stack([x,np.ones(30)]))['constant_level']


def test_gamma_one_task_level_alias():
    from runners.drive.cards.week5_md_analysis_fixture import constructed
    from runners.drive.cards import week5_md as md
    p=constructed(n=12);x,_=md.rating_history(p,1.)
    assert np.allclose(x[:,:,:3].sum(axis=2),x[:,:,4])
    assert all(d.multiple_r(a[:10,:5])['aliased'] for a in x)
