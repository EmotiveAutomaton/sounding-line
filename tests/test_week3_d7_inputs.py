from copy import deepcopy
from pathlib import Path
from unittest.mock import patch
import json
import numpy as np
import pytest
from runners.drive.cards import week3_d7_inputs as card
from runners.drive.cards import events_d6 as d6
from runners.stage14.common import read,freeze,filehash
from tests.test_drive_cards_events_d6 import fixture_session


def fixture():
    events,s,p2,domain=fixture_session()
    s.update(timestamp=0,end_at=6000,prompt='prompt')
    s['rows'][0]['open_at']=1000
    vectors=np.array([[1.,0.],[1.,0.],[0.,1.],[-1.,0.],[0.,-1.],[1.,0.]])
    record=dict(key='s-m',writer='w',session='s',context=0,options=[1,2,3,4,5],cosine=[1.,0.,-1.,0.,1.])
    saved=d6.extract_session(events,s,p2,domain)['rows']
    return events,s,p2,domain,saved,{'s-m':record},vectors


def checked_fixture():
    args=fixture();r=card.prepare_session(*args)[0]
    assert r['mean_novelty']==.8 and r['option_novelty']==[0.,1.,2.,1.,0.]
    assert r['dwell_seconds']==3 and r['dwell_observed'] and r['elapsed_seconds']==1
    assert r['accepted'] and r['reopenings']==0
    return r


def test_known_answer_and_choice_independent_novelty():
    checked_fixture();args=fixture();record=args[5]['s-m'];menu=args[1]['rows'][0]['menu']
    a=card.content(record,args[6],menu)
    b=card.content(dict(record,accepted=False,selected=999),args[6],menu)
    assert a==b


def test_reopenings_exclude_hidden_intervals_and_censoring_retained():
    args=list(fixture());events,s,p2,domain,saved,records,vectors=args
    events[2:4]=[dict(eventName=n,currentHoverIndex='',currentSuggestionIndex=0) for n in ('suggestion-close','suggestion-reopen')]
    events[3]['eventTimestamp']=10000
    for i,e in enumerate(events):e['eventTimestamp']=[0,1000,2000,10000,11000,12000][i]
    s['end_at']=12000;args[4]=d6.extract_session(events,s,p2,domain)['rows']
    r=card.prepare_session(*args)[0];assert r['dwell_seconds']==2 and r['reopenings']==1
    events[4]['eventName']='cursor-forward';events[5]['eventName']='cursor-forward';s['rows'][0]['handling']='ignore'
    args[4]=d6.extract_session(events,s,p2,domain)['rows']
    r=card.prepare_session(*args)[0];assert not r['dwell_observed'] and r['dwell_seconds']==3


@pytest.mark.parametrize('fault',['clock','join','cosine','vector','saved','duplicate'])
def test_source_defects_refuse(fault):
    args=list(fixture())
    if fault=='clock':args[1]['rows'][0]['open_at']=0
    elif fault=='join':args[5]['s-m']['writer']='other'
    elif fault=='cosine':args[5]['s-m']['cosine'][0]=0.
    elif fault=='vector':args[6][0]*=2
    elif fault=='saved':args[4][0]['dwell_seconds']+=1
    else:args[4].append(deepcopy(args[4][0]))
    with pytest.raises(ValueError):card.prepare_session(*args)


def load_fixture(directory):
    directory=Path(directory);directory.mkdir(parents=True,exist_ok=True)
    events,s,p2,domain,saved,records,vectors=fixture()
    raw=directory/'raw.jsonl';unit=directory/'p2.json'
    raw.write_text(''.join(json.dumps(e)+'\n' for e in events),encoding='utf8')
    freeze(unit,p2)
    roster={'s':dict(writer='w',path=str(raw.resolve()),source_sha256=filehash(raw),domain=domain)}
    index={'s':dict(writer='w',file='p2.json',sha256=filehash(unit))}
    return [s],records,{'s-m':saved[0]},vectors,roster,index,dict(source_root=str(directory),p2_index=str(directory/'index.json'))


def native(output,inputs,config,verification=False):
    if config!=card.CONFIG:raise ValueError('Fixture configuration differs')
    output=Path(output);output.mkdir(parents=True,exist_ok=True)
    # A constructed full-handler replay, with no population admission.
    fixture_input=load_fixture(output/'constructed-input')
    with patch.object(card,'load',return_value=fixture_input):
        if verification:
            result=card.verify(output/'constructed-output',inputs,config)
        else:
            checked_fixture()
            card.execute(output/'constructed-output',inputs,config)
            result=card.execute(output/'constructed-output',inputs,config)
    return dict(result,constructed=True,scientific_admission=False)


def execute(output,inputs,config):return native(output,inputs,config)
def verify(output,inputs,config):return native(output,inputs,config,True)


def test_full_handler_reentry_replay_and_tamper(tmp_path):
    execute(tmp_path,{},card.CONFIG);assert verify(tmp_path,{},card.CONFIG)['full_fresh_source_replay']
    path=tmp_path/'constructed-output/ROWS.json';value=read(path);value[0]['mean_novelty']=999
    path.write_text(json.dumps(value),encoding='utf8')
    with pytest.raises(ValueError,match='replay differs'):verify(tmp_path,{},card.CONFIG)


def test_resource_yield_and_bad_config(tmp_path):
    freeze(tmp_path/'constructed-output/YIELD_REQUEST.json',dict(stop=True))
    with pytest.raises(InterruptedError):execute(tmp_path,{},card.CONFIG)
    assert not (tmp_path/'constructed-output/SUMMARY.json').exists()
    with pytest.raises(ValueError,match='configuration'):card.execute(tmp_path,{},dict(card.CONFIG,schema=2))
