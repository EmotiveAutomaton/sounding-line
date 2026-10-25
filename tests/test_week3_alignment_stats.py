"""Constructed conditional preference, null, dependence and fresh consumer checks."""
import copy
from collections import Counter
import json
from pathlib import Path
import numpy as np
import pytest
from scipy.special import softmax
from runners.drive.cards import week3_alignment_stats as card
from runners.drive.cards import week3_alignment_features as features
from runners.drive.cards.menus_io import read,write,sha256
from tests.test_week3_alignment_features import fixture as feature_fixture, complete


def world(seed=82, personal=3., writers=8, conversations=32):
    rng=np.random.default_rng(seed); rows=[]; values=[]; clusters={}
    for wi in range(writers):
        beta=np.zeros(4);beta[wi%4]=personal*(1 if wi<4 else -1)
        for c in range(conversations):
            for turn in range(1,3):
                prompt=f'p{c}t{turn}';x=rng.normal(size=(4,4));x-=x.mean(0)
                choice=int(rng.choice(4,p=softmax(x@beta)))
                rows.append(dict(writer=f'w{wi}',country='a',conversation=f'w{wi}c{c}',turn=turn,
                                 prompt=prompt,choice=choice,candidates=list(range(4))))
                clusters[prompt]=c%2;values.append(x)
    return rows,np.array(values),clusters


def test_conditional_logit_independent_finite_differences():
    rows,x,_=world(writers=2,conversations=4);y=np.array([r['choice'] for r in rows]);beta=np.arange(4)/4;prior=np.ones(4)/3
    value,g,h=card.objective(x,y,beta,prior,10);eps=1e-5;ng=[];nh=[]
    for j in range(4):
        shift=np.eye(4)[j]*eps
        a=card.objective(x,y,beta+shift,prior,10);b=card.objective(x,y,beta-shift,prior,10)
        ng.append((a[0]-b[0])/(2*eps));nh.append((a[1]-b[1])/(2*eps))
    np.testing.assert_allclose(g,ng,atol=1e-7);np.testing.assert_allclose(h,np.array(nh).T,atol=1e-7)
    assert np.linalg.eigvalsh(h).min()>=10-1e-8


def test_planted_own_directions_beat_country_on_disjoint_prompts():
    rows,x,clusters=world();people=sorted({r['writer'] for r in rows})
    actual=card.evaluate(rows,x,{},people)
    null=[card.evaluate(rows,x,card.assignment(rows,clusters,'country_50_clusters',card.SEED+j),people) for j in range(24)]
    report=card.summarize(actual,null,draws=300)
    assert report['state']=='positive' and report['heldout_log_loss_gain']>.2
    assert report['permutation_p_one_sided']<.05


def test_exact_indifferent_world_cannot_become_a_positive():
    rows,x,clusters=world();x[:]=0.;people=sorted({r['writer'] for r in rows})
    actual=card.evaluate(rows,x,{},people)
    null=[card.evaluate(rows,x,card.assignment(rows,clusters,'country_50_clusters',j),people) for j in range(3)]
    report=card.summarize(actual,null,draws=30)
    assert report['heldout_log_loss_gain']==0 and report['state']=='null'
    assert report['permutation_p_one_sided']==1


def test_whole_conversation_null_preserves_strata_and_rebuilds_disjoint_halves():
    rows,x,clusters=world();people=sorted({r['writer'] for r in rows});assigned=card.assignment(rows,clusters,'country_50_clusters',card.SEED)
    groups=card.conversations(rows)
    before=Counter();after=Counter()
    for convo,indices in groups.items():
        first=min(indices,key=lambda i:rows[i]['turn']);r=rows[first]
        before[r['country'],clusters[r['prompt']],r['writer']]+=1
        after[r['country'],clusters[r['prompt']],assigned[convo]]+=1
    assert before==after and any(assigned[c]!=rows[ix[0]]['writer'] for c,ix in groups.items())
    halves,owners,details=card.fixed_halves(rows,assigned,people)
    for person in people:
        prompts=[{r['prompt'] for i,r in enumerate(rows) if owners[i]==person and halves[i]==h} for h in (0,1)]
        assert not prompts[0]&prompts[1]
    for indices in groups.values():assert len(set(halves[indices]))==1


def test_heldout_choices_cannot_change_any_fitted_direction():
    rows,x,_=world(writers=4,conversations=12);people=sorted({r['writer'] for r in rows})
    halves,_,_=card.fixed_halves(rows,{},people);changed=copy.deepcopy(rows)
    for i,r in enumerate(changed):
        if halves[i]==1:r['choice']=(r['choice']+1)%4
    a=card.evaluate(rows,x,{},people);b=card.evaluate(changed,x,{},people)
    assert a['population']==b['population'] and a['country']==b['country']
    for w in people:assert a['profiles'][w]['individual']==b['profiles'][w]['individual']


def test_pca_uses_only_candidates_without_choices_or_prompt_vectors():
    rng=np.random.default_rng(1);v=rng.normal(size=(10,20));rows=[{'candidates':[0,1,2,3],'choice':0},{'candidates':[4,5,6,7],'choice':2}]
    a,p=card.candidate_features(rows,v,list(range(10)),dimensions=4)
    v[8:]=1e8;rows[0]['choice']=3
    b,q=card.candidate_features(rows,v,list(range(10)),dimensions=4)
    np.testing.assert_array_equal(a,b);assert p==q


def test_unsupported_fake_person_is_neither_redrawn_nor_dropped():
    rows,x,clusters=world(writers=2,conversations=2)
    with pytest.raises(ValueError,match='fixed annotator'):
        card.fixed_halves(rows,{r['conversation']:'w0' for r in rows},['w0','w1'])
    changed=copy.deepcopy(rows)
    for r in changed:r['prompt']='same'
    with pytest.raises(ValueError,match='unsupported connected'):
        card.fixed_halves(changed,{},['w0','w1'])


def fixture(root):
    root=Path(root);inputs=feature_fixture(root/'source');feature_root=root/'features'
    features.execute(feature_root/'output',inputs,{'mode':'fixture'});complete(feature_root)
    return {k:v for k,v in inputs.items() if k.startswith('prepared_')}|{
        'features_summary':str(feature_root/'output/SUMMARY.json'),'features_complete':str(feature_root/'COMPLETE.json')}


def test_actual_consumer_rebuilds_all_fits_and_detects_tampering(tmp_path):
    inputs=fixture(tmp_path/'inputs');config={'mode':'fixture','permutation_draws':2,'bootstrap_draws':20}
    output=tmp_path/'out';result=card.execute(output,inputs,config)
    assert result['literal_turn_level_reference'].startswith('unrun')
    assert card.verify(output,inputs,config)['verified']
    assert card.execute(output,inputs,config)==result
    path=output/'REAL.json';value=read(path);first=next(iter(value['profiles']))
    value['profiles'][first]['individual'][0]+=.1;path.write_text(json.dumps(value))
    with pytest.raises(ValueError,match='recomputation'):card.verify(output,inputs,config)


def test_full_bank_and_full_features_cannot_be_reduced(tmp_path):
    with pytest.raises(ValueError,match='1000'):
        card.execute(tmp_path/'out',{},dict(mode='full',permutation_draws=2))
    inputs=fixture(tmp_path/'inputs')
    with pytest.raises(ValueError,match='requires full features'):
        card.execute(tmp_path/'full',inputs,dict(mode='full',permutation_draws=1000))
