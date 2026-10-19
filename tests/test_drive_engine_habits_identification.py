import copy
import json
import os
from pathlib import Path
import subprocess
import sys
from collections import Counter
import numpy as np
import pytest
from runners.drive.cards import engine_habits_identification as card
from runners.stage14.common import read,filehash


def fixture(kind='planted',writers=24,sessions=12):
    rng=np.random.default_rng(712);habits=[];chronology={}
    for w in range(writers):
        counts=rng.integers(1,40,14).tolist() if kind=='planted' else [4]*14
        raw=dict(words=1000,quotedWords=10 if kind=='null' else 10+w,sentenceCount=20,
            sentenceMean=50.,sentenceSpread=2. if kind=='null' else float(w+1),repeats={},
            connectives=dict(zip(card.CONNECTIVES,counts[:8])),punctuation=dict(zip(card.PUNCTUATION,counts[8:])))
        for n in range(sessions):
            keys=dict(writer=f'w{w:02d}',session=f'w{w:02d}-s{n:02d}',prompt=f'p{n//2}')
            value=card.project(copy.deepcopy(raw),card.CONNECTIVES)
            habits.append(dict(keys=keys,final=value,typed=copy.deepcopy(value)))
            chronology[keys['session']]=dict(keys=keys,timestamp=100+n)
    return dict(habits=habits,chronology=chronology)


def rows(kind='planted',**kwargs):
    f=fixture(kind,**kwargs);return card.population(f['habits'],f['chronology'])


def save(path,value):
    path.write_text(json.dumps(value,ensure_ascii=False,allow_nan=False),encoding='utf8');return str(path)


def test_planted_profiles_and_paired_arithmetic():
    s,d=card.analyze(rows(),card.CONFIG)
    result=s['variants']['final']['original'];scores=np.array(d['variants']['final']['original']['probe_scores'])
    assert result['real']['accuracy']==1 and np.all(scores[0]==1)
    assert result['primary']['effect']==pytest.approx((scores[0]-scores[1:].mean(0)).mean())
    assert result['primary']['ci_low']>0
    assert result['fake_mean_accuracy']<.2
    assert len(d['assignments'])==200 and len(result['reliability'])==17


def test_identical_profiles_are_fractional_chance_not_identifier_ties():
    s,d=card.analyze(rows('null'),card.CONFIG)
    r=s['variants']['final']['original']
    assert r['real']['accuracy']==pytest.approx(1/24)
    assert np.all(np.array(d['variants']['final']['original']['probe_scores'])==1/24)
    assert r['primary']['effect']==0 and r['state']=='null'
    assert r['real']['tied_probes']==24
    assert all(x['spearman_brown'] is None for x in r['reliability'])


def test_control_that_keeps_identity_cannot_pass():
    values,_,_,_=card.profiles(rows())
    result,_=card.comparison([values]*201,'final',sorted(values),card.CONFIG)
    assert result['fake_chance_centered']['bias_flag'] and result['state']=='invalid'


def test_exact_pmap_geometry_wrong_gallery_and_partial_missing():
    a=np.eye(5)
    assert card.pmap.identify(a,a)['accuracy']==1
    assert card.pmap.identify(a,np.roll(a,1,axis=0))['accuracy']==0
    a[0,0]=np.nan
    r=card.pmap.identify(a,np.eye(5))
    assert r['missing_A']==1 and r['missing_B']==0


def test_split_is_whole_prompt_and_half_means_are_session_weighted():
    r=rows(writers=3);r[0]['final'][0]=1000.;r[2]['final'][0]=2000.
    p,excluded,halves,support=card.profiles(r)
    a,b=halves['w00'];lookup={x['session']:x for x in r}
    assert {lookup[s]['prompt'] for s in a}.isdisjoint({lookup[s]['prompt'] for s in b})
    assert p['w00']['final'][0][0]==np.mean([lookup[s]['final'][0] for s in a])
    assert support['w00']['final'][0][0]==6


def test_fake_labels_preserve_counts_order_and_seed():
    r=rows(writers=8);s,d=card.analyze(r,card.CONFIG)
    labels=Counter(x['writer'] for x in r)
    assert all(Counter(p)==labels for p in d['assignments'])
    assert (s,d)==card.analyze(list(reversed(r)),card.CONFIG)


def test_unsupported_original_and_explicit_S1_no_redraw():
    s,d=card.analyze(rows('null',writers=4,sessions=4),card.CONFIG)
    v=s['variants']['final']
    assert v['original']['state']=='invalid'
    assert v['selected_population']=='S1-common-supported-gallery'
    assert v['original_question_open'] and v['dropped_for_common_support']>0
    assert len(d['assignments'])==200
    assert 'primary' not in v['original']


@pytest.mark.parametrize('mutation',['duplicate','identity','timestamp','rate','count','nan'])
def test_source_and_feature_corruption_refused(mutation):
    f=fixture();v=f['habits'][0]
    if mutation=='duplicate':f['habits'].append(copy.deepcopy(v))
    elif mutation=='identity':f['chronology'][v['keys']['session']]['keys']=dict(v['keys'],writer='wrong')
    elif mutation=='timestamp':f['chronology'][v['keys']['session']]['timestamp']=float('nan')
    elif mutation=='rate':v['final']['ratesPer1000UnquotedWords']['and']+=1
    elif mutation=='count':v['final']['raw']['words']=-1
    else:v['final']['raw']['sentenceMean']=v['final']['sentenceMean']=float('nan')
    with pytest.raises(ValueError):card.population(f['habits'],f['chronology'])


def test_absent_typed_support_is_not_zero_and_primary_is_not_switched():
    r=rows(writers=4)
    for row in r:row['typed']=[None]*17
    s,_=card.analyze(r,card.CONFIG)
    assert s['variants']['typed']['original']['state']=='unsupported'
    assert s['primary']==s['variants']['final']['original']['primary']


def test_fresh_serialized_replay_reentry_and_mutation_refusal(tmp_path):
    inputs=dict(fixture=save(tmp_path/'fixture.json',fixture(writers=8)))
    out=tmp_path/'out';s=card.execute(out,inputs,card.CONSTRUCTED)
    hashes=read(out/'TIMING_BINDINGS.json')['outputs']
    script='from runners.drive.cards import engine_habits_identification as c; import json,sys; assert c.verify(sys.argv[1],json.loads(sys.argv[2]),c.CONSTRUCTED)["verified"]'
    subprocess.run([sys.executable,'-X','utf8','-B','-c',script,str(out),json.dumps(inputs)],env=dict(os.environ,PYTHONHASHSEED='401'),check=True,timeout=90)
    assert card.execute(out,inputs,card.CONSTRUCTED)==s
    assert hashes=={n:filehash(out/n) for n in hashes}
    save(out/'SUMMARY.json',dict(s,state='forged'))
    with pytest.raises(ValueError):card.verify(out,inputs,card.CONSTRUCTED)


def test_config_changed_source_and_stop_refused(tmp_path):
    inputs=dict(fixture=save(tmp_path/'fixture.json',fixture(writers=4)))
    out=tmp_path/'out';card.execute(out,inputs,card.CONSTRUCTED)
    save(Path(inputs['fixture']),fixture('null',writers=4))
    with pytest.raises(ValueError):card.verify(out,inputs,card.CONSTRUCTED)
    with pytest.raises(ValueError):card.load(inputs,dict(card.CONSTRUCTED,draws=2))
    with pytest.raises(ValueError):card.load(inputs,card.CONFIG)
    (tmp_path/'STOP').write_text('stop')
    with pytest.raises(RuntimeError,match='stop'):card.execute(out,inputs,card.CONSTRUCTED)
