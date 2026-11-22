import csv
from hashlib import sha256
from pathlib import Path
import subprocess
import sys

import numpy as np
import pandas as pd
import pytest

from runners.drive.sealed import week7_cad1 as pace, week7_sld2 as purpose

GATE=Path('.agent-state/drive-20261115/lattice-20261119/intake/unpacked/PREFLIGHT_2026-11-19/spark/sealed_gate.py')


def gate(out):
    result=subprocess.run([sys.executable,'-B',str(GATE),str(out)],capture_output=True)
    assert result.returncode==0


def conversation_fixture():
    rng=np.random.default_rng(410)
    surveys=[];clock=[];speech=[]
    for j in range(240):
        i=j%24
        actors=(f'a{i}',f'b{(i+j//24)%24}')
        if j<12:actors=(actors[0],f'single{i}')
        conv=f'c{j}'
        clock.append((conv,10.))
        times=rng.uniform(.45,1.8,size=2)
        speech.extend([(conv,0,actors[0],0.,.2,'intro'),(conv,3,actors[1],9.,9.5,'outro')])
        for k,actor in enumerate(actors):
            start=1.+3*k
            speech.append((conv,k+1,actor,start,start+times[k],'two words [laughter]'))
            arousal,before,overall,liking,attention=rng.uniform(1,5,5)
            enjoyment=2/times[k]-.4*2/times[1-k]-.1*arousal+.2*before+i*.01 if k==0 else 2/times[k]-.4*2/times[0]-.1*arousal+.2*before
            surveys.append((conv,actor,actors[1-k],enjoyment,arousal,before,overall,liking,attention))
    return {key:pd.DataFrame.from_records(values,columns=pace.COLUMNS[key]) for key,values in (
        ('survey',surveys),('clock',clock),('speech',speech))}


def test_pace_two_readings_and_gate(tmp_path):
    tables=conversation_fixture()
    pins={}
    for key,frame in tables.items():
        p=tmp_path/(key+'.parquet')
        frame.to_parquet(p,index=False)
        pins[key]=(p.name,p.stat().st_size,sha256(p.read_bytes()).hexdigest())
    out=tmp_path/'out';out.mkdir()
    pace.run(tmp_path,out,pins,draws=8)
    gate(out)
    estimates=pd.read_csv(out/'pace.csv')
    assert estimates.reading.tolist()==[1,2]
    assert estimates.n.tolist()==[48,48]
    assert np.allclose(estimates.estimate,1.)
    assert np.allclose(estimates.lower,1.) and np.allclose(estimates.upper,1.)
    support=pd.read_csv(out/'support.csv')
    assert support[support.kind.eq(2)].n.tolist()==[12,12]


def test_pace_partner_and_missing_extra():
    tables=conversation_fixture()
    rows=pace.project(**tables)
    mapping=rows[rows.conversation_id.eq('c0')]
    assert mapping.iloc[0].own_rate==mapping.iloc[1].partner_rate
    assert mapping.iloc[1].own_rate==mapping.iloc[0].partner_rate
    rows['overall_affect']=np.nan
    out=pace.score(rows,draws=3)
    assert [r['reading'] for r in out['pace']]==[1]


def test_pace_no_unregistered_enjoyment_substitution(tmp_path):
    tables=conversation_fixture()
    tables['survey']=tables['survey'].rename(columns={'how_enjoyable':'overall_enjoyment'})
    pins={}
    for name,frame in tables.items():
        path=tmp_path/(name+'.parquet');frame.to_parquet(path,index=False)
        pins[name]=(path.name,path.stat().st_size,sha256(path.read_bytes()).hexdigest())
    out=tmp_path/'out';out.mkdir()
    with pytest.raises(pace.Unavailable):
        pace.run(tmp_path,out,pins,draws=2)
    assert not list(out.iterdir())


def test_purpose_trajectory_and_gate(tmp_path):
    ids=np.arange(80)
    waves=[]
    for i,delta in enumerate((0.,-.5,0.),1):
        frame=pd.DataFrame(dict(person=ids,item1=1.+(ids%5)/5+delta,item2=2.+(ids%3)/3+delta))
        if i==2:
            frame['role_loss']=(ids%4!=3).astype(int)
            frame['family']=ids//2
        frame.to_csv(tmp_path/f'made_wave_{i}.csv',index=False)
        waves.append(frame)
    out=tmp_path/'out';out.mkdir()
    purpose.rehearse(tmp_path,out,['item1','item2'],draws=8)
    gate(out)
    with (out/'purpose.csv').open() as stream:r=list(csv.DictReader(stream))
    assert len(r)==4 and all(int(x['n'])==60 for x in r)
    assert float(r[3]['lower'])==float(r[3]['upper'])==0
    assert float(r[1]['estimate'])==pytest.approx(float(r[0]['estimate'])-.5)
    waves[0]=pd.concat([waves[0],waves[0].iloc[:1]])
    with pytest.raises(ValueError,match='ambiguous'):
        purpose.projected(waves,['item1','item2'])
