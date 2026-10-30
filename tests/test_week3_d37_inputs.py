from copy import deepcopy
from pathlib import Path
import math
import numpy as np
import pytest
from runners.drive.cards import week3_d37_inputs as card
from runners.drive.cards.timing_p6 import write_equal
from runners.drive.cards.timing_census import read
from tests.test_drive_cards_menus_p4 import minimal_sessions


def fixture():
    events=[dict(eventName='system-initialize',eventTimestamp=0),
      dict(eventName='insert',eventTimestamp=1,eventSource='user',textDelta={'ops':[{'insert':'\U0001f600x'}]}),
      dict(eventName='suggestion-get',eventTimestamp=1000),
      dict(eventName='suggestion-open',eventTimestamp=1500),
      dict(eventName='suggestion-hover',eventTimestamp=1600),
      dict(eventName='delete',eventTimestamp=1700,eventSource='user',textDelta={'ops':[{'delete':2}]}),
      dict(eventName='suggestion-get',eventTimestamp=1800),
      dict(eventName='suggestion-get',eventTimestamp=1900),
      dict(eventName='suggestion-open',eventTimestamp=2000),
      dict(eventName='suggestion-open',eventTimestamp=70000)]
    rows=[dict(key=str(i),ordinal=i,open_at=events[i]['eventTimestamp']) for i in (3,8,9)]
    return events,rows


def page_fixture():
    sessions=minimal_sessions();records=[]
    for s in sessions:
        for r in s['rows']:
            records.append(dict(key=r['key'],writer=r['writer'],session=r['session'],context=0,options=[1],cosine=[.5],scalars=[[10.,1.,1.,0.]]))
    return sessions,records,np.eye(4)


def native_result():
    events,rows=fixture();result=card.process_features(events,rows)
    assert result[0]['process']==[math.log1p(.5),0.,0.,math.log1p(2),0.,math.log1p(1)]
    assert result[1]['request_missing_reason']=='ambiguous_requests'
    assert result[1]['process'][2:]==[math.log1p(1),math.log1p(2),math.log1p(2),math.log1p(2)]
    assert result[2]['request_missing_reason']=='missing_request' and result[2]['process'][3:]==[0.,0.,0.]
    sessions,records,vectors=page_fixture();out,page,embedding=card.page_features(sessions,records,vectors)
    changed=deepcopy(sessions)
    for s in changed:
        for r in s['rows']:r.update(handling='ignore',decision_index=99999)
    _,other,other_embedding=card.page_features(changed,records,vectors)
    assert np.array_equal(page,other) and np.array_equal(embedding,other_embedding)
    return dict(source_only=True,process=result,page=page.tolist(),embedding=embedding.tolist(),rows=len(out),future_isolated=True)


def execute(output,inputs,config):
    if config!=card.CONFIG:raise ValueError('Fixture config differs')
    write_equal(Path(output)/'SUMMARY.json',native_result())
    return dict(status='complete',constructed=True)


def verify(output,inputs,config):
    if read(Path(output)/'SUMMARY.json')!=native_result():raise ValueError('Fresh transform replay differs')
    return dict(verified=True,full_fresh_transform_replay=True,source_only=True)


def test_unicode_request_support_and_recent_window():
    native_result()


def test_own_and_future_interactions_never_enter_predecision_features():
    events,rows=fixture();before=card.process_features(events,rows)
    changed=deepcopy(events)
    changed[4]['eventName']='suggestion-close';changed[5]['textDelta']={'ops':[{'delete':99999}]}
    assert card.process_features(changed,rows)[0]==before[0]
    changed[3].update(eventSource='user',textDelta={'ops':[{'insert':'future'}]})
    assert card.process_features(changed,rows)[0]==before[0]


@pytest.mark.parametrize('defect',['clock','ordinal','duplicate','open_clock'])
def test_malformed_source_refuses(defect):
    events,rows=fixture()
    if defect=='clock':events[-1]['eventTimestamp']=-1
    elif defect=='ordinal':rows[0]['ordinal']=2
    elif defect=='duplicate':rows.append(rows[0])
    else:rows[0]['open_at']+=1
    with pytest.raises(ValueError):card.process_features(events,rows)


def test_fresh_transform_handlers_and_mutation(tmp_path):
    execute(tmp_path,{},card.CONFIG);assert verify(tmp_path,{},card.CONFIG)['full_fresh_transform_replay']
    p=tmp_path/'SUMMARY.json';v=read(p);v['rows']+=1;p.write_text(__import__('json').dumps(v),encoding='utf8')
    with pytest.raises(ValueError,match='replay differs'):verify(tmp_path,{},card.CONFIG)


def test_source_and_configuration_refuse_before_access(tmp_path):
    with pytest.raises(ValueError,match='Exact D37'):card.load({})
    with pytest.raises(ValueError,match='Frozen D37'):card.build({},dict(card.CONFIG,recent_ms=1),tmp_path)
