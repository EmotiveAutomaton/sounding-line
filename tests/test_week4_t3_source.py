import pytest
from runners.drive.cards import week4_t3_source as t


def row(s,start,n,end=None):
    return dict(session=s,writer='w',prompt='p',genre='known',timestamp=start,end_at=start+1 if end is None else end,tokens=n)


def test_boundaries_counts_and_no_punctuation_symbols():
    assert t.skeletons([['the','cat',',','runs','.','a','dog','!'],['strange','words']],{'the','a'})==[['the','<content>','<content>'],['a','<content>'],['<content>','<content>']]
    assert t.skeletons([['the'],['a']],{'the','a'})==[['the'],['a']]


def test_exact_floor_and_odd_split():
    records=[row('c',30,1000),row('a',10,2000),row('b',20,1000)]
    support,counts=t.split_support(records)
    assert support['w']['training']['sessions']==['a'] and support['w']['evaluation']['sessions']==['b','c']
    assert counts['supported_writers']==1
    records[0]['tokens']=999
    assert not t.split_support(records)[0]['w']['supported']


def test_empty_sessions_remain_and_overlap_refuses():
    support,_=t.split_support([row('a',1,0),row('b',3,4000),row('c',5,4000)])
    assert support['w']['training']['sessions']==['a'] and not support['w']['supported']
    support,_=t.split_support([row('a',1,2000,end=3),row('b',3,2000)])
    assert support['w']['token_floor'] and not support['w']['strictly_separated']


def test_duplicates_and_invalid_clock_refuse():
    r=row('a',1,2000)
    with pytest.raises(ValueError,match='Duplicate'):t.split_support([r,r])
    with pytest.raises(ValueError,match='chronology'):t.split_support([row('a',1,2000,end=0)])


def test_complete_replay_and_tamper_refusal(tmp_path):
    config=t.configuration('constructed')
    t.execute(tmp_path,{},config)
    assert t.verify(tmp_path,{},config)['complete_source_replay']
    p=tmp_path/'SUMMARY.json';v=t.read(p);v['source_sessions']+=1
    import json
    p.write_text(json.dumps(v),encoding='utf8')
    with pytest.raises(ValueError,match='replay'):t.verify(tmp_path,{},config)
