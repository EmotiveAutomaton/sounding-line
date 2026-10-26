import copy
import hashlib
import importlib.metadata
import json
from pathlib import Path
import subprocess
import sys

import numpy as np
import pytest

from runners.drive.cards import week3_stability_inputs as source
from runners.drive.cards import week3_stability_stats as stats
from runners.drive.cards import week3_stability_analysis as analysis
from runners.drive.cards.timing_census import write,read
from runners.drive.cards.timing_census import filehash
from tests.test_week3_trust_inputs import session


def source_fixture():
    s=session();meta=s['meta']
    s['p6']={'words':[dict(is_word=True,ordinal=37,index=0),dict(is_word=True,ordinal=38,index=1)]}
    s['wb1']=dict(**meta,raw_events=len(s['events']),final_document_sha256=hashlib.sha256(s['timeline']['final_document'].encode()).hexdigest(),
                  actions=[dict(kind='burst',source_ordinals=[37,38]),dict(kind='burst',source_ordinals=[39])],
                  intervals=[dict(location='before_sentence',interval_seconds=2),dict(location='before_paragraph',interval_seconds=4)])
    s['annotation']=dict(sentence_length=10.,lexical_density=.6,punctuation_rate=.1,artifact_words=20,artifact_sentences=2)
    return s


def statistical_fixture(mode='positive'):
    rng=np.random.default_rng(47);variance=rng.uniform(.5,1.5,(12,8));variance+=2-variance.mean(0);profile=np.sqrt(variance);rows=[]
    for w in range(12):
        for prompt in range(8):
            scale=profile[w].copy()
            if mode=='reversed' and prompt%2:scale=np.sqrt(4-scale**2)
            if mode=='null':scale=np.sqrt(2+.4*np.array([np.sin(2*np.pi*w/12+j) if prompt%2==0 else np.cos(2*np.pi*w/12+j) for j in range(8)]))
            if mode=='constant':scale=np.ones(8)
            for repeat in range(4):
                sign=(-1,-1,1,1)[repeat]
                x=100+3*prompt+sign*scale
                rows.append(dict(session=f'{w:02}-{prompt}-{repeat}',writer=f'w{w:02}',prompt=f'p{prompt}',timestamp=prompt*10+repeat,
                                 properties=dict(zip(source.PROPERTIES,x.tolist())),events=100,event_eligible=True,missing=[]))
    return rows


def test_source_opportunities_and_missing_not_zero():
    f=source_fixture();s=source.prepare_session(**f)
    assert s['event_eligible']
    assert s['properties']['words_per_burst']==1
    assert s['properties']['pause_before_sentence']==3
    assert s['properties']['acceptance_rate']==1
    assert s['properties']['retained_share']==pytest.approx(172/180)
    f['wb1']['actions']=[];f['wb1']['intervals']=[]
    s=source.prepare_session(**f)
    assert {'words_per_burst','pause_before_sentence'}<=set(s['missing'])
    f['wb1']['final_document_sha256']='wrong'
    with pytest.raises(ValueError,match='final document'):source.prepare_session(**f)


def test_lexical_density_counts_pos_not_word_length():
    tokens=[[dict(text='The',pos='DET'),dict(text='tiny',pos='ADJ'),dict(text='cat',pos='NOUN'),dict(text='sleeps',pos='VERB'),dict(text='.',pos='PUNCT')],
            [dict(text='It',pos='PRON'),dict(text='is',pos='AUX'),dict(text='here',pos='ADV'),dict(text='!',pos='PUNCT')]]
    r=source.summarize_tokens(tokens)
    assert r['sentence_length']==3.5 and r['lexical_density']==4/7 and r['punctuation_rate']==2/9


def test_profile_null_positive_and_reversal():
    c=analysis.CONSTRUCTED
    a=stats.analyze(statistical_fixture(),c);b=stats.analyze(statistical_fixture('reversed'),c);n=stats.analyze(statistical_fixture('null'),c)
    assert a['primary']['real_reliability']==pytest.approx(1)
    assert a['primary']['real_minus_permutation_mean']>.8
    assert a['primary']['paired_writer_ci95'][0]>0 and a['primary']['reference']['one_sided_p']<.05
    assert a['state']=='positive'
    assert b['primary']['real_reliability']==pytest.approx(-1)
    assert b['primary']['paired_writer_ci95'][1]<0
    assert b['state']=='negative'
    assert n['primary']['real_reliability']==pytest.approx(0,abs=1e-12)
    assert n['state']=='not_detected_sensitivity_unquantified'
    assert stats.analyze(statistical_fixture('constant'),c)['state']=='unsupported_between_writer_variation'


def test_prompt_adjustment_and_fixed_support():
    rows=statistical_fixture();p=stats.prepare(rows);variance,ratio=stats.profiles(p,p['labels'])
    shifted=copy.deepcopy(rows)
    for r in shifted:
        for k in r['properties']:r['properties'][k]+=10000*int(r['prompt'][1:])
    q=stats.prepare(shifted)
    assert np.allclose(stats.profiles(q,q['labels'])[1],ratio,rtol=0,atol=1e-9)
    labels=p['labels'].copy();rng=np.random.default_rng(2)
    for idx in p['prompts'].values():labels[idx]=rng.permutation(labels[idx])
    assert stats.profiles(p,labels)[1].shape==ratio.shape
    for w in p['names']:
        assert len(set(p['split'][w]))==8
    short=copy.deepcopy(rows)
    for r in short:r['event_eligible']=False
    assert stats.analyze(short,analysis.CONSTRUCTED)['state']=='unsupported_writers'


def test_source_full_reentry_fresh_process_and_binding(tmp_path):
    f=tmp_path/'fixture.json';write(f,[source_fixture()]);inputs={'fixture':str(f)}
    config=dict(source.CONFIG,mode='constructed',expected_sessions=1,session_limit=1);out=tmp_path/'out'
    assert source.execute(out,inputs,config)==source.execute(out,inputs,config)
    manifest=tmp_path/'manifest.json';write(manifest,dict(output=str(out),inputs=inputs,config=config))
    code="import json,sys;from runners.drive.cards.week3_stability_inputs import verify;d=json.load(open(sys.argv[1]));assert verify(**d)['verified']"
    subprocess.run([sys.executable,'-X','utf8','-B','-c',code,str(manifest)],check=True,timeout=60)
    f.write_text(f.read_text()+' ',encoding='utf8')
    with pytest.raises(ValueError,match='replay differs'):source.verify(out,inputs,config)


def test_analysis_full_reentry_fresh_process_and_mutation(tmp_path):
    f=tmp_path/'fixture.json';write(f,statistical_fixture());inputs={'fixture':str(f)};config=analysis.CONSTRUCTED;out=tmp_path/'out'
    a=analysis.execute(out,inputs,config);assert analysis.execute(out,inputs,config)==a
    manifest=tmp_path/'manifest.json';write(manifest,dict(output=str(out),inputs=inputs,config=config))
    code="import json,sys;from runners.drive.cards.week3_stability_analysis import verify;d=json.load(open(sys.argv[1]));assert verify(**d)['verified']"
    subprocess.run([sys.executable,'-X','utf8','-B','-c',code,str(manifest)],check=True,timeout=60)
    result=read(out/'WC4_RESULT.json');result['primary']['real_reliability']=0;(out/'WC4_RESULT.json').write_text(json.dumps(result),encoding='utf8')
    with pytest.raises(ValueError,match='statistical replay'):analysis.verify(out,inputs,config)
    with pytest.raises(ValueError,match='complete source'):analysis.execute(tmp_path/'bad',inputs,analysis.CONFIG)


def test_actual_cpu_tagger_known_answers_and_fresh_process(tmp_path):
    import en_core_web_sm
    from runners.drive.cards import week3_stability_tagger_smoke as smoke
    root=Path(en_core_web_sm.__file__).parent/'en_core_web_sm-3.8.0'
    pin=dict(model='en_core_web_sm',model_version='3.8.0',model_root=str(root.resolve()),
             versions={k:importlib.metadata.version(k) for k in ['spacy','thinc','numpy','en-core-web-sm']},
             files={f.relative_to(root).as_posix():filehash(f) for f in sorted(root.rglob('*')) if f.is_file()})
    path=tmp_path/'model.json';write(path,pin);inputs={'model_manifest':str(path)};out=tmp_path/'out'
    assert smoke.execute(out,inputs,smoke.CONFIG)['constructed']
    manifest=tmp_path/'manifest.json';write(manifest,dict(output=str(out),inputs=inputs,config=smoke.CONFIG))
    code="import json,sys;from runners.drive.cards.week3_stability_tagger_smoke import verify;d=json.load(open(sys.argv[1]));assert verify(**d)['verified']"
    subprocess.run([sys.executable,'-X','utf8','-B','-c',code,str(manifest)],check=True,timeout=60)
    pin['files']['config.cfg']='changed';path.write_text(json.dumps(pin),encoding='utf8')
    with pytest.raises(ValueError,match='tagger bytes changed'):source.LocalTagger(path)


def test_paired_correlation_bootstrap_equals_literal_rebuild():
    bank=np.random.default_rng(11).uniform(.1,2,(5,6,2,8))
    draws=np.asarray([[0,0,1,3,4,5],[5,4,3,2,1,0],[0,0,0,0,0,0]])
    real,delta,invalid=stats.paired_bootstrap(bank,draws)
    assert invalid==1
    for j,draw in enumerate(draws[:2]):
        literal=[stats.agreement(arm[draw]).mean() for arm in bank]
        assert real[j]==pytest.approx(literal[0],abs=1e-12)
        assert delta[j]==pytest.approx(literal[0]-np.mean(literal[1:]),abs=1e-12)
