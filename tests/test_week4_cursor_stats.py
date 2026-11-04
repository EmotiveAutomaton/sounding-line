import numpy as np
from runners.drive.cards.week4_cursor_stats import arrays,writer_effects,analyze

def sample(kind='positive'):
    sessions=[]
    for w in range(20):
        rows=[]
        for j in range(20):
            rows.extend([dict(bin='1',kind='jump',edit_near=kind=='positive' or (kind=='zero' and j%2==0)),
                         dict(bin='1',kind='step',edit_near=kind=='negative' or (kind=='zero' and j%2==0))])
        sessions.append(dict(writer=str(w),session=str(w),landings=rows,genre='constructed'))
    return sessions

def test_signed_known_answers_and_exact_null_decision():
    for kind,value,state in [('positive',1,'positive'),('negative',-1,'negative'),('zero',0,'null')]:
        r,p=analyze(sample(kind));assert r['estimate']==value and r['interval']==[value,value] and r['state']==state
        assert r['control_status']=='passes'
        if kind=='positive':assert r['reference']['positive_probability']<.05

def test_distance_standardization_blocks_composition_artifact():
    rows=[]
    for g,n1,n2 in [('jump',90,10),('step',10,90)]:
        rows += [dict(bin='1',kind=g,edit_near=True)]*n1+[dict(bin='2',kind=g,edit_near=False)]*n2
    a=arrays([dict(writer='a',session='a',landings=rows)]);effect,support,counts=writer_effects(a)
    assert effect[0]==0 and support[0] and counts['weights']==[20.]

def test_permutation_support_fixed_and_small_population_not_null():
    r,p=analyze(sample()[:19]);assert r['state']=='design cannot test' and 'estimate' not in r
    a=arrays(sample());rng=np.random.default_rng(1);before=writer_effects(a)[1];labels=a['group'].copy()
    for idx in a['strata']:labels[idx]=rng.permutation(labels[idx])
    assert np.array_equal(before,writer_effects(a,labels)[1])

def test_nonexchangeable_session_label_reference_stays_visible():
    s=[]
    for w in range(20):
        for kind in ['jump','step']:
            s.append(dict(writer=str(w),session=str(w)+kind,landings=[dict(bin='1',kind=kind,edit_near=kind=='jump')]*20))
    r,p=analyze(s)
    assert r['reference']['biased'] and r['control_status']=='biased reference'
    assert r['reference']['positive_probability']==1
