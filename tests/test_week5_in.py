import numpy as np
from runners.drive.cards import week5_in as m


def test_fixture():
    assert m.fixture()["passed"]


def test_cluster_fit_equals_direct_and_preserves_clusters():
    rng=np.random.default_rng(53)
    x=np.column_stack([np.ones(120),rng.normal(size=(120,2))]);y=rng.normal(size=120)
    fit=m.clustered_fit(x,y,np.repeat(np.arange(40),3),[0,1,0],draws=30)
    assert abs(fit["estimate"][0]-np.linalg.lstsq(x,y,rcond=None)[0][1])<1e-12
    order=rng.permutation(120)
    other=m.clustered_fit(x[order],y[order],np.repeat(np.arange(40),3)[order],[0,1,0],draws=30)
    assert np.allclose(fit["interval"],other["interval"],atol=1e-12)


def test_privacy_projection_column_allowlist():
    assert not set(m.APPRAISALS)&{'age','gender','education','ethnicity','extravert','anxious','original_demographics'}
    assert m.salted('example',b'a'*32,'text') != m.salted('example',b'a'*32,'person')


def test_exhaustive_three_way_bands():
    assert m.classify(0,[-.01,.01],.1)=='against'
    assert m.classify(-.1,[-.2,-.01],.1)=='against'
    assert m.classify(.2,[.11,.3],.1)=='supports'
    assert m.classify(.1,[.05,.15],.1)=='inconclusive'


def test_every_grid_cell_has_actual_handler():
    assert {r['phase'] for r in m.grid()}=={'IN1','IN2','IN3','IN4'}
