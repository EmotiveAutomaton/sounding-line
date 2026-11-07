import itertools
import numpy as np
import pandas as pd
import pytest
from runners.theory_days import emotions as e


def test_scale_order_line_and_off_line_oracles():
    increasing=[0,1,2,3,4]
    yes=e.scale_stats(increasing,increasing,[1,3,5,7,9])
    assert yes['verdict']=='supports' and yes['inversions']==0
    assert yes['spearman']==pytest.approx(1) and yes['off_line_ratio']<1e-12
    no=e.scale_stats([4,3,2,1,0],increasing,[1,3,5,7,9])
    assert no['verdict']=='against' and no['inversions']==4
    off=e.scale_stats(increasing,[.01,.02,.03,.04,.05],[0,1,0,1,0])
    assert off['off_line_ratio']>1 and off['verdict']=='against'
    assert e.scale_stats([1,1,1,1],[0,1,2,3],[0,1,2,3])['verdict']=='design cannot test'
    assert e.scale_stats([1,2,3],[1,2,3],[1,2,3])['verdict']=='design cannot test'


def test_ordered_pair_arithmetic_against_literal_enumeration():
    rng=np.random.default_rng(20261106)
    rows=[]
    for comment,count in enumerate([3,4,5]):
        for rater in range(count):
            row=dict(zip(e.LABELS,rng.integers(0,2,len(e.LABELS))))
            row.update(id=str(comment),rater_id=rater);rows.append(row)
    frame=pd.DataFrame(rows);matrix,pairs,n=e.pair_sufficient(frame);p=len(pairs)
    totals=matrix.sum(axis=0);got,expected=e.lifts(totals,p)
    for k,(i,j) in enumerate(pairs):
        x,y=e.LABELS[i],e.LABELS[j];observed=0
        for _,part in frame.groupby('id'):
            for a,b in itertools.permutations(part.to_dict('records'),2):
                observed+=bool(a[x] and not a[y] and b[y] and not b[x])
        ax=int(((frame[x]==1)&(frame[y]==0)).sum())
        by=int(((frame[y]==1)&(frame[x]==0)).sum())
        reference=sum(v*(v-1) for v in [3,4,5])*ax*by/len(frame)**2
        assert totals[k]==observed
        assert expected[k]==pytest.approx(reference)
        if reference:assert got[k]==pytest.approx(observed/reference)


def test_exact_null_and_signed_disagreement_controls():
    # Full binary factorial of three independent raters, repeated uniformly.
    # Conditional marginal exclusivity produces exact expected cross-rater counts.
    rows=[]
    for comment,labels in enumerate(itertools.product(range(4),repeat=3)):
        for rater,value in enumerate(labels):
            row={name:0 for name in e.LABELS};row.update(id=str(comment),rater_id=rater)
            row['anger']=value&1;row['annoyance']=int(bool(value&2));rows.append(row)
    matrix,pairs,n=e.pair_sufficient(pd.DataFrame(rows));point,_=e.lifts(matrix.sum(0),len(pairs))
    k=list(map(tuple,pairs)).index(tuple(sorted([e.LABELS.index('anger'),e.LABELS.index('annoyance')])))
    assert point[k]==pytest.approx(1)
    assert e.pair_decision(.3,[.2,.4])=='win'
    assert e.pair_decision(-.3,[-.4,-.2])=='loss'
    assert e.pair_decision(.03,[.01,.04])=='inconclusive'
    assert e.pair_decision(.3,None)=='invalid uncertainty'


def test_frozen_mind_pattern_boundaries():
    assert e.mind_counts('He really does think.')[0]==1
    assert e.mind_counts('He really does not think.')[0]==0
    assert e.mind_counts('[NAME] thinks she cares.')[0]==2
    assert e.mind_counts('I think we care.')[0]==0
    assert e.mind_counts("they don't care")[0]==1
    assert e.mind_counts('someone tries; everyone believed')[0]==2


def test_matched_bootstrap_known_null_and_both_directions():
    null=[('a',2,100,2,100,True,True)]*400
    assert e.mind_contrast(null,30)['relative_difference']==0
    down=[('a',1,100,2,100,True,True)]*400
    assert e.mind_contrast(down,30)['verdict']=='supports'
    up=[('a',3,100,2,100,True,True)]*400
    assert e.mind_contrast(up,30)['verdict']=='against'
    zero=[('a',1,100,0,100,True,True)]*400
    result=e.mind_contrast(zero,30)
    assert result['interval'] is None and result['relative_difference'] is None
    assert result['undefined_draws']==30


def test_matching_without_replacement_and_subreddit_boundary():
    rows=[]
    for index in range(12):
        arm='disgust' if index%2 else 'anger'
        for rater in range(3):
            rows.append(dict(id=f'c{index}',rater_id=rater,text='he thinks yes',
                subreddit='one' if index<10 else ('only_disgust' if index%2 else 'only_anger'),
                disgust=int(arm=='disgust'),anger=int(arm=='anger')))
    pairs,support=e.matched_pairs(pd.DataFrame(rows),2)
    assert len(pairs)==5 and support['disgust_candidates']==6 and support['anger_candidates']==6
    assert all(row[0]=='one' for row in pairs)


def test_literal_lexicon_handler_and_fresh_reentry(tmp_path):
    import zipfile
    from runners.stage14.common import filehash
    eil=['word\temotion\tintensity'];vad=['term\tvalence\tarousal\tdominance']
    for emotion,words in e.SCALES.values():
        for i,word in enumerate(words.split()):
            value=(i+1)/10
            if emotion:eil.append(f'{word}\t{emotion}\t{value}')
            vad.append(f'{word}\t0\t{value}\t{value}')
    inputs={}
    for key,member,rows in [('eil','NRC-Emotion-Intensity-Lexicon/NRC-Emotion-Intensity-Lexicon-v1.txt',eil),
                           ('vad','NRC-VAD-Lexicon-v2.1/NRC-VAD-Lexicon-v2.1.txt',vad)]:
        path=tmp_path/(key+'.zip')
        with zipfile.ZipFile(path,'w') as z:z.writestr(member,'\n'.join(rows)+'\n')
        inputs[key]=dict(path=str(path),sha256=filehash(path))
    out=tmp_path/'out';result=e.execute(out,inputs,dict(card='TD4'))
    assert len(result['scales'])==8
    assert all(r['verdict']=='supports' for r in result['scales'].values())
    assert e.verify(out,inputs,dict(card='TD4'))['verified']
