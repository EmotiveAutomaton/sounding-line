import json
import numpy as np
import pytest
from threadpoolctl import threadpool_limits
from runners.drive.cards import week3_jester_preference as m
from runners.drive.cards import week3_jester_topics as topics
from runners.drive.cards import week3_jester_comparison as runner


@pytest.fixture(autouse=True)
def limit_threads():
    with threadpool_limits(limits=2):
        yield


def text_fixture():
    words=['orchard apple pear', 'doctor patient hospital', 'lawyer judge court',
           'computer software keyboard', 'teacher student classroom',
           'musician guitar piano', 'farmer tractor wheat', 'pilot plane airport']
    return [dict(joke_id=i+1,text=words[(i//2)%8]+' '+words[(i//16+2)%8]+
        ' friend asks surprising story '+str(i//3)) for i in range(150)]


def world(seed=77, n=160, effect=0, reverse=False):
    rng=np.random.default_rng(seed)
    w=np.exp(rng.normal(size=(40,8)));w/=w.sum(1,keepdims=True)
    person=rng.normal(size=(n,1));item=rng.normal(size=(1,40))
    # Exposure correlated with generosity and item identity, plus guaranteed support.
    mask=rng.random((n,40)) < 1/(1+np.exp(-(person+item)))
    mask[:,:4]=True
    taste=rng.normal(size=(n,8)) @ w.T
    if reverse:taste[:,1::2]*=-1
    y=person+item+effect*taste+rng.normal(size=(n,40))*.08
    return np.where(mask,y,np.nan),w


def test_exact_sparse_additive_null_and_invariance():
    y,w=world();mask=np.isfinite(y);rng=np.random.default_rng(901)
    additive=rng.normal(size=(len(y),1))+rng.normal(size=(1,y.shape[1]))
    halves,res=m.prepare(np.where(mask,additive,np.nan),w)
    assert all(np.count_nonzero(e)==0 for e in res)
    _,a=m.prepare(y,w);_,b=m.prepare(y+additive,w)
    for x,z in zip(a,b):np.testing.assert_allclose(x,z,atol=1e-10,rtol=0)


def test_sparse_solver_matches_explicit_dummy_matrix():
    y,w=world(n=13);part=m.Half(np.isfinite(y),w);e=part.residuals(y)
    rows,cols=np.where(np.isfinite(y))
    design=np.concatenate([np.eye(len(y))[rows],np.eye(y.shape[1])[cols]],axis=1)
    expected=y[rows,cols]-design @ np.linalg.lstsq(design,y[rows,cols],rcond=1e-12)[0]
    np.testing.assert_allclose(e[rows,cols],expected,atol=1e-10,rtol=0)


def test_stable_and_reversed_preferences_and_actual_references():
    y,w=m.planted_world(effect=4)
    positive=m.calculate(y,w,item_draws=50,person_draws=20,bootstrap_draws=200)
    assert positive['state']=='positive' and positive['item']['paired_interval'][0]>.5
    y,w=m.planted_world(effect=4,reverse=True)
    negative=m.calculate(y,w,item_draws=50,person_draws=20,bootstrap_draws=200)
    assert negative['state']=='negative' and negative['item']['paired_interval'][1]<-.5


def test_noise_across_fixed_seeds_and_heteroscedasticity():
    values=[]
    for seed in range(20):
        y,w=world(seed=seed,n=160)
        rng=np.random.default_rng(seed+700)
        mask=np.isfinite(y)
        noise=rng.normal(size=y.shape)*np.exp(rng.uniform(-1,1,size=(len(y),1)))
        h,e=m.prepare(np.where(mask,noise,np.nan),w)
        values.append(m.correlations(*(a.profiles(b) for a,b in zip(h,e)))[0].mean())
    assert abs(np.mean(values))<.03


def test_permutations_keep_observed_cells_and_count_every_person():
    y,w=world(n=15);h,e=m.prepare(y,w)
    for kind in ['item','person']:
        for a,b in zip(h,e):
            s=a.shuffle(b,np.random.default_rng(1),kind)
            assert s.shape==b.shape and np.all(s[~a.mask]==0)
            np.testing.assert_allclose(s.sum(1),0,atol=1e-9)
    result=m.calculate(np.ones((15,40)),w,5,5,20)
    assert result['constant_profiles']==15 and result['item']['paired_difference']==0


def test_text_only_order_invariance_full_text_and_replay(tmp_path):
    records=text_fixture()
    result=m.text_features(records)
    assert m.text_features(records[::-1])==result
    assert np.asarray(result['weights']).shape==(150,8)
    assert np.all(np.asarray(result['weights'])>0)
    # Terms after a long prefix still enter the complete-text vocabulary.
    records[0]['text']+=' filler'*2000+' tailword'
    records[1]['text']+=' tailword'
    assert 'tailword' in m.text_features(records)['vocabulary']
    p=tmp_path/'text.json';p.write_text(json.dumps(records),encoding='utf8')
    inp={'jester_texts':str(p)};cfg={'source_sha256':m.filehash(p)}
    out=tmp_path/'out';topics.execute(out,inp,cfg)
    assert topics.verify(out,inp,cfg)['complete_feature_replay']
    before=(out/'TOPICS.json').read_bytes();topics.execute(out,inp,cfg)
    assert before==(out/'TOPICS.json').read_bytes()
    (out/'TOPICS.json').write_text('{}',encoding='utf8')
    with pytest.raises(ValueError,match='replay'):topics.verify(out,inp,cfg)
    p.write_text('[]',encoding='utf8')
    with pytest.raises(ValueError,match='source changed'):topics.build(inp,cfg)


def test_invalid_support_and_topics_refuse():
    y,w=world();y[0,::2]=np.nan
    with pytest.raises(ValueError,match='unsupported'):m.prepare(y,w)
    records=text_fixture();records[-1]['joke_id']=1
    with pytest.raises(ValueError,match='unique'):m.text_features(records)


def test_paired_bootstrap_matches_scalar_oracle():
    real=np.array([.3,.5,-.2,.8]);fake=np.array([.1,-.2,0.,.1])
    rng=np.random.default_rng(m.SEED+200000)
    draws=[sum(real[j]-fake[j] for j in rng.integers(0,4,4))/4 for _ in range(70)]
    np.testing.assert_allclose(m.paired_interval(real,fake,70),np.quantile(draws,[.025,.975]))


def fixture(root):
    """Explicit constructed predecessor receipts, never corpus-admissible."""
    from tests.test_week3_jester_support import put, seal
    from pathlib import Path
    root=Path(root);root.mkdir(parents=True)
    source=root/'source';out=source/'output';out.mkdir(parents=True)
    text=root/'texts.json';put(text,text_fixture())
    troot=root/'topics';tinput={'jester_texts':str(text)};tconfig={'source_sha256':m.filehash(text)}
    topics.execute(troot/'output',tinput,tconfig)
    assert topics.verify(troot/'output',tinput,tconfig)['verified']
    put(troot/'PLAN.json',dict(module='runners.drive.cards.week3_jester_topics',inputs=tinput,config=tconfig,pins={str(text):m.filehash(text)},constructed_fixture=True))
    put(troot/'COMPLETE.json',dict(status='COMPLETE',fresh_process_verified=True,constructed_fixture=True,
        outputs={'output/TOPICS.json':m.filehash(troot/'output/TOPICS.json')}))
    weights=np.array(m.read(troot/'output/TOPICS.json')['weights']);rng=np.random.default_rng(434)
    values=.2*rng.normal(size=(160,1))+.2*rng.normal(size=(1,150))+2*(rng.normal(size=(160,8))@weights.T)
    values+=rng.normal(size=values.shape)*.05
    put(out/'INPUT_BINDING.json',dict(constructed=True))
    put(out/'QUARANTINE.json',dict(numeric_cells=123,blank_cells=28))
    p=out/'chunks/0000.npy';p.parent.mkdir();np.save(p,values)
    unit=dict(rows=160,rater_offset=0,excel_row_first=1,excel_row_last=160,sheet='constructed',sheet_index=0)
    put(p.with_suffix('.json'),dict(unit=unit,sha256=m.filehash(p),input_binding_sha256=m.filehash(out/'INPUT_BINDING.json')))
    put(out/'RATINGS_INDEX.json',dict(schema=1,dtype='float64',missing='NaN',joke_ids=list(range(1,151)),rows=160,
        chunks=[dict(file='chunks/0000.npy',receipt='chunks/0000.json',**unit)]))
    put(source/'PLAN.json',dict(module='runners.drive.cards.timing_jester_complete_records',config=dict(card='Jester2plus-complete-records',rows_per_chunk=1024),
        inputs=dict(jester_texts=str(text)),pins={str(text):m.filehash(text)},constructed_fixture=True))
    seal(source)
    return dict(source_complete=str(source/'COMPLETE.json'),source_plan=str(source/'PLAN.json'),jester_texts=str(text),
        topics_complete=str(troot/'COMPLETE.json'),topics_plan=str(troot/'PLAN.json'),topics=str(troot/'output/TOPICS.json'))


def test_full_source_feature_consumer_and_tamper_refusal(tmp_path):
    inputs=fixture(tmp_path/'fixture')
    y,w,s,b=runner.load(inputs,dict(mode='constructed'))
    assert y.shape==(160,150) and s['population_records']==160
    assert runner.mask_calibration(np.isfinite(y),w)['exact_additive_zero']
    changed=m.read(inputs['topics']);changed['weights'][0][0]+=.1
    from tests.test_week3_jester_support import put
    put(__import__('pathlib').Path(inputs['topics']),changed)
    with pytest.raises(ValueError,match='topic output'):runner.load(inputs,dict(mode='constructed'))


def test_full_reference_known_answers():
    answers=runner.known_answers()
    assert answers['positive']['state']=='positive'
    assert answers['reversed']['state']=='negative'
    assert answers['noise']['state']=='null'
    assert all(v['item']['draws']==1000 and v['person']['draws']==200 for v in answers.values())
