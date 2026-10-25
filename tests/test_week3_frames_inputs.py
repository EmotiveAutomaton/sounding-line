import copy
import json
from pathlib import Path
import subprocess
import sys

import pytest

from runners.drive.cards import week3_frames_inputs as w
from runners.drive.cards.timing_census import read,write
from runners.drive.cards.timing_text import replay_words
from runners.stage9.coauthor import units


def session(sid='a',writer='a',with_events=True):
    events=[dict(eventName='system-initialize',eventTimestamp=0,currentDoc='\n',eventSource='system')]
    canonical=[];decisions=[];document=''
    def add(name,source='system',**kw):
        events.append(dict(eventName=name,eventTimestamp=len(events)*1000,eventSource=source,**kw))
    def menu(handling):
        add('suggestion-open');origin=len(events)-1
        add('suggestion-dismiss' if handling=='dismiss' else 'suggestion-close')
        canonical.append(dict(ordinal=origin,usable=True,decision=handling,options=[dict(index=0,original='offered words')]))
        decisions.append(dict(ordinal=origin,resolution_ordinal=len(events)-1,handling=handling,latency_kind='observed'))
    def text(words):
        nonlocal document
        value=' '.join(words)+'. '
        add('text-insert','user',textDelta={'ops':[{'retain':len(units(document))},{'insert':value}]})
        document+=value
    if with_events:
        for _ in range(4):menu('dismiss')
        text(['and' if writer=='a' else 'the']*55)
        menu('ignore');menu('dismiss')
        text(['but']*55)
        menu('ignore')
    else:text(['and' if writer=='a' else 'the']*150)
    return dict(meta=dict(session=sid,writer=writer,prompt='p',timestamp=1),events=events,
                canonical=dict(events=canonical,final_document=document+'\n'),
                timeline=dict(decisions=decisions,final_document=document+'\n'),p6=replay_words(events))


def fixture():
    return [session(w+str(i),w,i==0) for w in ('a','b') for i in range(5)]


def test_maximal_runs_and_complete_punctuation_window():
    rows=[dict(handling=v) for v in ['dismiss']*4+['ignore','dismiss','dismiss','accept','dismiss']]
    assert [len(r) for r in w.dismissal_runs(rows)]==[4,2,1]
    p=w.prepare_session(**session())
    assert [r['kind'] for r in p['events']]==['frustration','single']
    assert p['events'][0]['run_length']==4
    assert p['events'][0]['window']['words']==50
    assert len(p['events'][0]['window']['word_indices'])==50
    assert p['events'][0]['window']['first_ordinal']>p['events'][0]['ordinal']


def test_profile_and_calibration_are_disjoint_and_context_separate():
    result=w.assemble([w.prepare_session(**s) for s in fixture()])
    assert result['summary']['complete_matched_frustration']==2
    assert result['summary']['support_state']=='unsupported'
    for writer,profile in result['profiles'].items():
        assert len(profile['heldout_sessions'])==1
        assert profile['excluded_window_token_count']==100
        assert profile['support']
    for pair in result['pairs']:
        assert set(pair['context'])=={'event','control'}
        assert all(r['writer']!=pair['event']['writer'] for arm in pair['context'].values() for r in arm)
        assert pair['event']['session']==pair['control']['session']


def test_source_census_reentry_full_fresh_process_and_mutation(tmp_path):
    source=tmp_path/'fixture.json';write(source,fixture());inputs={'fixture':str(source)}
    config=dict(w.CONFIG,mode='constructed',expected_sessions=10,session_limit=10)
    output=tmp_path/'out'
    assert w.execute(output,inputs,config)==w.execute(output,inputs,config)
    manifest=tmp_path/'manifest.json';write(manifest,dict(output=str(output),inputs=inputs,config=config))
    code="import json,sys;from runners.drive.cards.week3_frames_inputs import verify;x=json.load(open(sys.argv[1]));assert verify(x['output'],x['inputs'],x['config'])['verified']"
    subprocess.run([sys.executable,'-X','utf8','-B','-c',code,str(manifest)],check=True,timeout=60)
    source.write_text(source.read_text()+' ',encoding='utf-8')
    with pytest.raises(ValueError,match='replay differs'):w.verify(output,inputs,config)


def test_boundary_partial_window_and_wrong_canonical_handling():
    f=session();f['p6']['words']=f['p6']['words'][:49]
    assert all(r['window'] is None for r in w.prepare_session(**f)['events'])
    f=session();f['timeline']['decisions'][0]['handling']='accept'
    with pytest.raises(ValueError,match='handling join'):w.prepare_session(**f)
