from copy import deepcopy
import numpy as np
import pytest
from runners.drive.cards import week4_pp3_project_cost as card


def test_whole_project_selection_and_author_remapping():
    arrays=card.original.wide_fixture();before=deepcopy(arrays)
    selected,census=card.subset(arrays)
    chosen=census['selected_project_ids'];keep=np.isin(arrays[3],chosen)
    assert census['source_rows']==450 and census['selected_rows']==270
    assert census['selected_projects']==3 and census['selected_authors']==6
    assert all(np.array_equal(selected[i],arrays[i][keep]) for i in range(3))
    assert np.array_equal(selected[3],np.unique(arrays[3][keep],return_inverse=True)[1])
    assert np.array_equal(np.unique(selected[3]),np.arange(3))
    assert np.array_equal(np.unique(selected[4]),np.arange(6))
    assert all(np.array_equal(a,b) for a,b in zip(arrays,before))
    for i in range(6):assert len(np.unique(selected[3][selected[4]==i]))==1
    assert card.subset(arrays)[1]==census


def test_reject_incomplete_source_or_different_floor():
    arrays=card.original.wide_fixture()
    with pytest.raises(ValueError,match='five-project'):card.subset(tuple(v[arrays[3]!=4] for v in arrays))
    with pytest.raises(ValueError,match='three-project'):card.subset(arrays,2)
    changed=list(arrays);changed[4]=np.zeros_like(arrays[4])
    with pytest.raises(ValueError,match='project scoped'):card.subset(changed)


def test_selected_model_keeps_held_projects_and_known_signal():
    (x,c,y,p,a),_=card.subset(card.original.wide_fixture())
    design=card.original.designs(x,c,p,'p',1.)
    for project,train,test,_ in design:
        assert not np.any(p[train]==project) and np.all(p[test]==project)
    actual=card.original.evaluate(design,y,p,a,True)
    assert card.model.f1(actual['cm3'][0].sum(axis=0))>.95
    constant=card.original.evaluate(card.original.designs(np.zeros_like(x),np.zeros_like(c),p,'p',1.),y,p,a,True)
    assert np.array_equal(constant['cm3'][0],constant['base3'])


def test_complete_constructed_replay_and_tamper(tmp_path):
    cfg=card.configuration('constructed')
    assert card.execute(tmp_path,{},cfg)['status']=='complete'
    assert card.verify(tmp_path,{},cfg)['complete_source_and_timing_replay']
    probe=card.read(tmp_path/'PROBE.json');assert not probe['empirical_scores_reported']
    assert card.read(tmp_path/'FORECAST.json')['full_actual_refits']==401
    probe['census']['selected_rows']-=1
    (tmp_path/'PROBE.json').write_text(__import__('json').dumps(probe))
    with pytest.raises(ValueError,match='replay differs'):card.verify(tmp_path,{},cfg)


def test_config_and_human_input_refuse(tmp_path):
    with pytest.raises(ValueError,match='Frozen'):card.execute(tmp_path,{},dict(card.configuration('constructed'),projects=2))
    with pytest.raises(ValueError,match='human inputs'):card.execute(tmp_path,{'prepared':'no'},card.configuration('constructed'))
