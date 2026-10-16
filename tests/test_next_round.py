import copy
import numpy as np
import pytest
from runners.next_round.statistics import (simplex, losses, random_effects, em_shift,
    fit_calibrator, calibrate, outer_fold, stack_weight)
from runners.next_round.phase0 import completed_before, prequential_session
from runners.next_round.queue import require_resources


def test_variance_known_null_and_planted_cluster_offsets():
    groups=np.repeat(['a','b','c','d'],40)
    null=np.tile([-.1,.1],80)
    assert random_effects(null,groups)['between_variance']==0
    signal=null+np.repeat([-.4,-.2,.2,.4],40)
    fit=random_effects(signal,groups)
    assert fit['between_variance']>.12 and fit['within_variance']<.011
    assert random_effects(np.zeros(160),groups)['icc']==0


def test_probability_validation_and_invalid_penalty():
    with pytest.raises(ValueError): simplex([[1,1,1,1]])
    with pytest.raises(ValueError): simplex([[float('nan'),0,0,1]])
    b,ll=losses([[.25]*4],[0],[False])
    assert b[0]==1 and ll[0]==pytest.approx(-np.log(.01))


def test_em_identity_and_constant_predictions_no_discrimination():
    p=np.tile([.5,.2,.2,.1],(40,1)); q,info=em_shift(p,p.mean(0))
    assert info['converged']; np.testing.assert_allclose(p,q)
    y=np.tile(np.arange(4),10); fit=fit_calibrator(p,y,np.repeat(np.arange(4),10))
    calibrated=calibrate(p,fit)
    assert np.max(np.ptp(calibrated,axis=0))==0
    assert losses(calibrated,y)[0].mean()==pytest.approx(.375,abs=.003)


@pytest.mark.parametrize('mode',['BCTS','EM_TS'])
def test_outer_labels_cannot_change_predictions_or_meta_weights(mode):
    rng=np.random.default_rng(501); groups=np.repeat(np.arange(4).astype(str),12)
    p=rng.dirichlet(np.ones(4),len(groups)); base=np.full_like(p,.25)
    y=rng.integers(0,4,len(groups))
    first=outer_fold(p,base,y,groups,'0',mode)
    altered=y.copy();altered[groups=='0']=(altered[groups=='0']+1)%4
    second=outer_fold(p,base,altered,groups,'0',mode)
    np.testing.assert_array_equal(first['stacked'],second['stacked'])
    assert first['weight']==second['weight']
    for inner in first['audit']:
        assert '0' not in inner['fit_writers']
        assert inner['validation_writer'] not in inner['fit_writers']


def test_calibrator_known_bias_and_stack_alternative():
    rng=np.random.default_rng(43); y=np.tile(np.arange(4),100)
    p=np.full((400,4),.1);p[np.arange(400),y]=.7
    biased=p*np.array([8,1,1,1]);biased/=biased.sum(1,keepdims=True)
    fit=fit_calibrator(biased[:200],y[:200],np.repeat(np.arange(10),20))
    assert losses(calibrate(biased[200:],fit),y[200:])[0].mean()<losses(biased[200:],y[200:])[0].mean()
    assert stack_weight(np.full_like(p,.25),p,y,np.repeat(np.arange(20),20))==1
    wrong=np.roll(p,1,axis=1)
    assert stack_weight(np.full_like(p,.25),wrong,y,np.repeat(np.arange(20),20))==0


def test_completed_session_chronology_strictly_excludes_overlap_future_and_self():
    sessions=[dict(session='past',timestamp=0,end_at=5),dict(session='overlap',timestamp=1,end_at=20),
              dict(session='now',timestamp=10,end_at=30),dict(session='equal',timestamp=2,end_at=10)]
    assert [s['session'] for s in completed_before(sessions,sessions[2])]==['past']


def test_future_session_labels_do_not_change_prequential_predictions():
    rows=[]; sessions=[]
    for i in range(3):
        rr=[dict(key=f'{i}:{j}',writer='a',prompt='p',handling='accept',
                 open_at=i*100+j+1,resolved_at=i*100+j+2) for j in range(10)]
        sessions.append(dict(session=str(i),writer='a',prompt='p',timestamp=i*100,end_at=i*100+20,rows=rr))
        rows+=rr
    x=np.ones((30,2));index={r['key']:i for i,r in enumerate(rows)}
    first,fit=prequential_session(sessions,sessions[1],x,index)
    changed=copy.deepcopy(sessions)
    for s in changed[1:]:
        for r in s['rows']:r['handling']='dismiss'
    second,fit2=prequential_session(changed,changed[1],x,index)
    assert [r['probabilities'] for r in first]==[r['probabilities'] for r in second]
    assert fit==fit2 and fit['max_training_resolution']<fit['cutoff']


def test_resource_boundaries():
    require_resources(dict(ram_available_GiB=8,commit_headroom_GiB=8,disk_free_GiB=20))
    for field in ['ram_available_GiB','commit_headroom_GiB','disk_free_GiB']:
        row=dict(ram_available_GiB=8,commit_headroom_GiB=8,disk_free_GiB=20);row[field]-=.01
        with pytest.raises(RuntimeError):require_resources(row)
