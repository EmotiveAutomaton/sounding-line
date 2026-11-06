import copy
import numpy as np
import pytest
from runners.drive.cards import week4_auth_auc_ruler as a


def brute(rows,weights,genre):
    positive=[];negative=[]
    for r in rows:
        if r['genre']!=genre:continue
        w=weights[r['left_writer']]
        if not r['same_writer']:w*=weights[r['right_writer']]
        (positive if r['same_writer'] else negative).extend([r['score']]*w)
    if not positive or not negative:return float('nan')
    return sum((p>n)+.5*(p==n) for p in positive for n in negative)/(len(positive)*len(negative))


def test_exact_weighted_auc_against_explicit_pair_replication():
    base=a.fixture_geometry();rows=a.world(base,'positive',1,20261102)
    writers,p,n=a.histories(rows);weights=np.array([i%3 for i in range(len(writers))])
    actual=a.aucs(p,n,weights[None,:])[0]
    lookup=dict(zip(writers,weights.tolist()))
    assert list(actual)==[brute(rows,lookup,g) for g in a.GENRES]


@pytest.mark.parametrize('regime,target',[('null',0),('positive',.5),('negative',-.5)])
def test_ties_sign_and_degenerate_inference_refusal(regime,target):
    rows=a.world(a.fixture_geometry(),regime,0,20261102,True)
    result=a.evaluate(rows,resamples=2000)
    assert result['difference']==target and result['interval']==[target,target]
    assert result['unsupported_draws']==0 and result['degenerate_interval'] and not result['inference_valid']


def test_both_roles_change_weighted_result_and_reordering_is_exact():
    rows=a.world(a.fixture_geometry(),'null',2,20261102)
    writers,p,n=a.histories(rows);counts=np.ones((1,len(writers)));counts[0,0]=7
    assert list(a.aucs(p,n,counts)[0])==[brute(rows,dict(zip(writers,counts[0].astype(int))),g) for g in a.GENRES]
    assert a.evaluate(rows,resamples=100)==a.evaluate(list(reversed(rows)),resamples=100)


def test_empty_resample_class_not_redrawn_or_filled():
    rows=a.world(a.fixture_geometry(),'null',2,20261102)
    writers,p,n=a.histories(rows);counts=np.zeros((1,len(writers)));counts[0,0]=24
    assert np.isnan(a.aucs(p,n,counts)).all()


@pytest.mark.parametrize('change',['score','truth','duplicate','missing_class'])
def test_malformed_inputs_refuse(change):
    rows=a.world(a.fixture_geometry(),'null',2,20261102)
    if change=='score':rows[0]['score']=True
    if change=='truth':rows[0]['same_writer']=not rows[0]['same_writer']
    if change=='duplicate':rows.append(copy.deepcopy(rows[0]))
    if change=='missing_class':rows=[r for r in rows if r['same_writer']]
    with pytest.raises(ValueError):a.histories(rows)


def test_constructed_handler_reentry_and_mutation(tmp_path):
    cfg=a.configuration('constructed');a.execute(tmp_path,{},cfg)
    assert a.verify(tmp_path,{},cfg)['complete_constructed_replay']
    before=(tmp_path/'SUMMARY.json').read_bytes();a.execute(tmp_path,{},cfg)
    assert before==(tmp_path/'SUMMARY.json').read_bytes()
    (tmp_path/'world-null-000.json').write_text('{}',encoding='utf8')
    with pytest.raises(ValueError):a.verify(tmp_path,{},cfg)


def test_synthetic_world_never_uses_original_scores():
    base=a.fixture_geometry()
    decorated=[dict(r,score=999999) for r in base]
    assert a.world(base,'null',3,20261102)==a.world(decorated,'null',3,20261102)
