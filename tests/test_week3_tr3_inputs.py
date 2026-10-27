import copy
import json
import pytest
from runners.drive.cards import week3_tr3_inputs as m


def fixture():
    sessions=[]
    for n,(writer,start,end) in enumerate([('a',0,10),('a',20,30),('b',0,15),('b',15,25)]):
        identity=dict(session=str(n),writer=writer,prompt='p')
        options=[dict(index=3,original=' a suggestion',trimmed='a suggestion')]
        events=[dict(eventName='system-initialize',eventTimestamp=start,currentDoc='\n'),
                dict(eventName='suggestion-open',eventTimestamp=start+1,currentSuggestions=options),
                dict(eventName='suggestion-reopen',eventTimestamp=start+2,currentSuggestions=options),
                dict(eventName='text-insert',eventTimestamp=start+3,eventSource='api',textDelta={'ops':[{'insert':'machine'}]}),
                dict(eventName='text-insert',eventTimestamp=start+4,eventSource='user',textDelta={'ops':[{'insert':'é😀'}, {'delete':1}]})]
        sessions.append(dict(meta=dict(**identity,timestamp=start,end_at=end),events=events,timeline=identity,
            canonical=dict(events=[dict(ordinal=1,options=options,decision='accept',usable=False,exclusion='ambiguous')]),
            p6=dict(**identity,timestamp=start,end_at=end,words=[])))
    return dict(sessions=sessions,split=dict(seed=20261026,writers={'a':'discovery','b':'test'},session_counts={'a':2,'b':2}))


def test_all_displays_and_ambiguous_handling_retained():
    r=m.prepare(**fixture()['sessions'][0])
    assert len(r['displays'])==2 and r['displays'][1]['reopened']
    assert all(d['handling'] is None for d in r['displays'])
    assert r['displays'][0]['options'][0]['original']==' a suggestion'
    assert r['displays'][0]['options'][0]['trimmed']=='a suggestion'
    assert r['typed_inserted_characters']==2
    assert len(r['user_edits'])==1
    assert not r['outcome_features_prepared']


@pytest.mark.parametrize('mutation',['missing','changed','clock','reopen'])
def test_source_defects_refused(mutation):
    f=copy.deepcopy(fixture()['sessions'][0])
    if mutation=='missing':f['canonical']['events']=[]
    elif mutation=='changed':f['events'][1]['currentSuggestions']=[dict(index=3,original='different',trimmed='different')]
    elif mutation=='clock':f['events'][4]['eventTimestamp']=2
    else:f['events'][1]['eventName']='suggestion-reopen'
    with pytest.raises(ValueError):m.prepare(**f)


def test_chronology_never_uses_overlapping_or_future_sessions():
    f=fixture();rows=[m.prepare(**r) for r in f['sessions']]
    result=m.assemble(rows,f['split']);by={r['session']:r for r in result['roster']}
    assert by['0']['strict_prior_sessions']==[]
    assert by['1']['strict_prior_sessions']==['0']
    assert by['3']['strict_prior_sessions']==[]
    assert by['3']['overlapping_or_touching_sessions']==['2']
    assert result['summary']['sessions']==4 and result['summary']['repeat_writers']==2
    rows[1]['start']=0;rows[1]['end']=10
    assert all(not r['strict_prior_sessions'] for r in m.assemble(rows,f['split'])['roster'])


def test_split_population_cannot_change():
    f=fixture();rows=[m.prepare(**r) for r in f['sessions']]
    f['split']['session_counts']['a']=1
    with pytest.raises(ValueError,match='population'):m.assemble(rows,f['split'])


def test_serialized_reentry_complete_replay_and_tamper(tmp_path):
    p=tmp_path/'fixture.json';p.write_text(json.dumps(fixture()),encoding='utf8')
    inputs={'fixture':str(p)};config=dict(mode='constructed',seed=20261026);output=tmp_path/'output'
    first=m.execute(output,inputs,config)
    assert m.execute(output,inputs,config)==first
    assert m.verify(output,inputs,config)['complete_source_replay']
    summary=json.loads((output/'SUMMARY.json').read_text());summary['sessions']=3
    (output/'SUMMARY.json').write_text(json.dumps(summary))
    with pytest.raises(ValueError,match='aggregate replay'):m.verify(output,inputs,config)
