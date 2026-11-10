from pathlib import Path
import json
import numpy as np
import pytest
from runners.drive.cards import week5_bk_v1 as v1
from runners.drive.cards import week5_bk_ca1_fixture as native


def test_whole_conversation_assignment_and_comparator_groups():
    rows=[dict(writer=f'w{i}',country='a',conversation=f'c{i}-{j//2}',prompt='p',turn=j%2) for i in range(4) for j in range(12)]
    membership={'mandatory':['w0','w1'],'random':['w2','w3']}
    people,halves,details=v1.allocation(rows,{'p':2},membership)
    for c in {r['conversation'] for r in rows}:
        assert len({halves[i] for i,r in enumerate(rows) if r['conversation']==c})==1
    profiles={w:[[1.,2.],[1.,2.]] for w in people}
    scores,counts=v1.contrast(profiles,details)
    assert len(scores)==4 and all(r['comparators']==1 and r['gain']==0 for r in scores)
    modified=[dict(r,choice=3) for r in rows]
    assert np.array_equal(v1.allocation(modified,{'p':2},membership)[1],halves)


def test_focal_choice_never_enters_country_prior(monkeypatch):
    rng=np.random.default_rng(12);x=rng.normal(size=(24,4,3));choices=rng.integers(4,size=24)
    owners=np.array(['a']*8+['b']*8+['c']*8);countries=np.array(['country']*24);halves=np.tile(np.repeat([0,1],4),3)
    original=v1.old.fit;seen=[]
    def capture(x,y,prior=None,penalty=10.):
        seen.append((x.copy(),y.copy()));return original(x,y,prior,penalty)
    monkeypatch.setattr(v1.old,'fit',capture)
    v1.one_person(x,choices,owners,countries,halves,'a');before=seen[:];seen.clear()
    choices[:8]=(choices[:8]+1)%4
    v1.one_person(x,choices,owners,countries,halves,'a')
    for i in (0,1,3,4):
        assert np.array_equal(before[i][0],seen[i][0]) and np.array_equal(before[i][1],seen[i][1])


def test_bounded_v1_checkpoint_tamper_and_whole_replay(tmp_path):
    inputs=native.analysis_source(tmp_path/'source','positive');out=tmp_path/'out'
    cfg={'fixture':True,'draws':2000,'permutations':2,'max_new_fits':1}
    assert v1.execute(out,inputs,cfg)['status']=='yielded'
    cfg['max_new_fits']=1000;result=v1.execute(out,inputs,cfg)
    assert min(g['mean_cosine_excess'] for g in result['groups'].values())>.1
    assert v1.verify(out,inputs,cfg)['verified']
    p=next((out/'fits').glob('*.json'));p.write_text('[]')
    with pytest.raises(ValueError,match='checkpoint changed'):v1.execute(out,inputs,cfg)


def test_singleton_country_has_no_invented_prior():
    x=np.ones((4,4,2));owners=np.array(['a','a','b','b']);countries=np.array(['x','x','y','y'])
    assert v1.one_person(x,np.zeros(4,int),owners,countries,np.array([0,1,0,1]),'a') is None


def test_full_floor_signed_and_exact_null_classification():
    details={f'w{i:02}':{'group':'random','country':'a','cluster':0} for i in range(30)}
    same={w:[[1.,0.],[1.,0.]] for w in details};null=v1.contrast(same,details)
    for sign,state in ((1,'supports'),(-1,'against')):
        profiles={w:[np.array([np.cos(i),np.sin(i)]).tolist(),
                     (sign*np.array([np.cos(i),np.sin(i)])).tolist()] for i,w in enumerate(details)}
        result=v1.summary(v1.contrast(profiles,details),[null]*200,2000)['random']
        assert result['state']==state and sign*result['mean_cosine_excess']>.5
    result=v1.summary(null,[null]*200,2000)['random']
    assert result['state']=='inconclusive' and result['mean_cosine_excess']==0
    assert result['cluster_95_interval']==[0.,0.] and not result['control_pass']
