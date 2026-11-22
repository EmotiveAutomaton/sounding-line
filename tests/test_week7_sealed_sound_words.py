import csv
import json
from pathlib import Path
import subprocess
import sys

import numpy as np
import pandas as pd
import pytest
from runners.drive.sealed import week7_cad2 as words, week7_lgh1 as acoustics, week7_lgh2 as mood

GATE=Path('.agent-state/drive-20261115/lattice-20261119/intake/unpacked/PREFLIGHT_2026-11-19/spark/sealed_gate.py')


def gate(out):
    passed=subprocess.run([sys.executable,'-B',str(GATE),str(out)],capture_output=True)
    assert passed.returncode==0


def test_speech_attribution_and_join():
    u=[dict(speaker='a',start=0,end=30),dict(speaker='b',start=45,end=61),
       dict(speaker='b',start=70,end=113),dict(speaker='c',start=110,end=120)]
    marks=[dict(speaker='a',start=60,label='vocal'),dict(speaker='b',start=60.8,label='vocal')]
    a,b=acoustics.heldout_facts('test',u,marks,0,125,{'a':4})
    assert a['joined']==1 and a['speaking']==0 and a['overlap_other']==1
    assert a['target_share_change']==pytest.approx(44/54-15/45)
    assert b['joined']==0 and 'target_share_change' not in b


def test_laugh_groups_and_heldout_facts(tmp_path):
    rng=np.random.default_rng(16)
    x=[];metadata=[]
    for person in range(48):
        for step in range(16):
            label=step%2
            x.append(np.array([1,4,.5,3,2,.7])+label*3+rng.normal(0,.15,6))
            metadata.append(dict(speaker=person,conversation=person//2,speaking=label,
                                 joined=label,target_share_change=.3*label-.1,target_share_before=.5,
                                 target_share_after=.4+.3*label,partner_rating=3+label,
                                 overlap_other=step%3==0))
    # File-level replay of six non-identifying constructed measurements and metadata.
    path=tmp_path/'made.json'
    path.write_text(json.dumps({'x':np.asarray(x).tolist(),'meta':metadata}),'utf8')
    source=json.loads(path.read_text('utf8'))
    out=tmp_path/'out';out.mkdir()
    acoustics.evaluate(source['x'],source['meta'],out,shuffles=200,draws=12)
    gate(out)
    groups=pd.read_csv(out/'mixture.csv').iloc[0]
    assert groups.components==groups.dip_groups==2
    assert groups.half_agreement>.95
    facts=pd.read_csv(out/'facts.csv')
    assert len(facts)==4 and (facts.fraction_explained>facts.shuffle_95).all()
    assert np.allclose(sorted(pd.read_csv(out/'target_minutes.csv').share_after),[.4,.7])
    assert pd.read_csv(out/'overlap.csv').heldout_laughs.sum()==384
    assert all('speaker' not in p.read_text('utf8').splitlines()[0] for p in out.iterdir())


@pytest.mark.parametrize('marked',[False,True])
def test_mood_on_report_or_marks(tmp_path,marked):
    rng=np.random.default_rng(33)
    rows=[]
    for conv in range(36):
        for k in (0,1):
            before=rng.integers(1,6)
            intensity=before+rng.integers(0,3)
            rows.append(dict(conversation=conv,speaker=2*conv+k,pre_affect=before,
              affect=.3*before+.5*intensity,laugh_count=2*intensity,minutes=2,
              reported_own_relative_laughter=intensity))
    path=tmp_path/'made.csv'
    pd.DataFrame(rows).to_csv(path,index=False)
    out=tmp_path/'out';out.mkdir()
    mood.run(pd.read_csv(path),out,marked=marked,draws=20)
    gate(out)
    estimates=pd.read_csv(out/'mood.csv')
    assert estimates.source.tolist()==[int(marked)]*2
    assert estimates.estimate.iloc[0]<0 and estimates.estimate.iloc[1]==pytest.approx(.5)
    assert (estimates.n==72).all()


def word_fixture():
    rng=np.random.default_rng(713)
    source=[]
    lexicon=['a','bed','third','walkabout','leaf','market','stone','very','closer','go']
    for n in range(10):
        for p in range(18):
            t=0.;tokens=[]
            for j in range(36):
                typ=(p%6 if rng.random()<.55 else int(rng.integers(len(lexicon))))
                gap=float(rng.uniform(.05,.5))
                t+=gap
                tokens.append(dict(token=lexicon[typ],start=t,end=t+.1,
                                   sentence_start=int(j%7==0),after_punctuation=int(j%9==2)))
                t+=.1
            start=(18*n+p)*120
            source.append(dict(conversation=f'c{n}_{p}',start=start,end=start+100,
                               turns=[dict(speaker=f'p{p}',words=tokens)]))
    return source


def test_d33_prior_only_and_gate(tmp_path):
    source=word_fixture()
    path=tmp_path/'made.json';path.write_text(json.dumps(source),'utf8')
    sessions=words.project(json.loads(path.read_text('utf8')))
    first=next(s for s in sessions if s['session']=='c0_0')
    assert all(w['population_probability'] is None for w in first['words'])
    before=next(s for s in sessions if s['session']=='c2_0')
    source[-1]['turns'][0]['words'][0]['token']='future'
    after=next(s for s in words.project(source) if s['session']==before['session'])
    assert after==before
    out=tmp_path/'out';out.mkdir()
    words.run(source,out,draws=6)
    gate(out)
    with (out/'support.csv').open() as f:
        record=next(csv.DictReader(f))
    assert int(record['n'])==18 and int(record['evaluation_words'])==18*2*35
    assert {1,2}<=set(pd.read_csv(out/'timing.csv').measure)


def test_d33_requires_real_word_times():
    source=word_fixture()[:1]
    token=source[0]['turns'][0]['words'][1]
    token['start']=token['end']+1.
    with pytest.raises(ValueError,match='word time'):
        words.project(source)
