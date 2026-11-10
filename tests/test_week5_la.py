import numpy as np
import pytest
from runners.drive.cards.week5_la import labelled_acts,matched_sets,conditional_fit,joining_pairs


def test_laughter_marks_never_change_text_length_and_boundaries():
    acts=[dict(id='a',meeting='m',speaker='s',start=0,end=5,act_type='inform',words=[
        dict(kind='word',text='real'),dict(kind='vocalsound',text='LAUGH',laugh=True),
        dict(kind='word',text='speech',annotation='while laughing')])]
    laughs=[dict(meeting='m',speaker='other',start=7,end=7.1)]
    a=labelled_acts(acts,laughs)[0]
    assert a['text']=='real' and a['word_count']==1 and a['other_laugh'] and not a['own_laugh']
    assert not labelled_acts(acts,[dict(laughs[0],start=7.01)])[0]['laughed_after']


def test_matching_uses_only_prespecified_metadata_and_length():
    base=dict(meeting='m',speaker='s',act_type='a',word_count=10,start=0)
    rows=[dict(base,id='case',laughed_after=True),dict(base,id='match',laughed_after=False),
          dict(base,id='other-speaker',speaker='q',laughed_after=False),
          dict(base,id='other-type',act_type='q',laughed_after=False)]
    groups,unsupported=matched_sets(rows)
    assert unsupported==0 and [a['id'] for a in groups[0]['members']]==['case','match']


def test_conditional_signed_and_exact_null_worlds():
    rng=np.random.default_rng(4);groups=[]
    for _ in range(120):
        x=rng.normal(size=(6,2));p=np.exp(x[:,0]);p/=p.sum();case=rng.choice(6,p=p)
        groups.append(np.vstack([x[case],np.delete(x,case,axis=0)]))
    assert conditional_fit(groups)[0]>.4
    reflected=[x*np.array([-1,1]) for x in groups]
    assert conditional_fit(reflected)[0]<-.4
    # Every member takes the case role once, giving exact null score equations.
    balanced=[np.roll(x,i,axis=0) for x in groups[:10] for i in range(6)]
    assert np.max(np.abs(conditional_fit(balanced)))<1e-10


def test_unidentifiable_resolution_refuses():
    with pytest.raises(ValueError,match='identifiable'):
        conditional_fit([[[0,0],[1,1]],[[1,1],[2,2]]])


def test_joining_has_no_self_pairs_and_missing_background_is_excluded():
    meta={'m':dict(duration=10,speakers={'a':{'native_language':'x'},'b':{'native_language':'x'},'c':{}})}
    events=[dict(meeting='m',speaker=s,start=t) for s,t in [('a',1),('b',1.5),('c',2)]]
    rows=joining_pairs(events,meta)
    assert len(rows)==1 and rows[0]['joined']==1 and rows[0]['same']==1
