"""Known edit histories and complete serialized D30 classification handlers."""
from copy import deepcopy
from pathlib import Path
import pytest

from runners.drive.cards import timing_revision_bursts as card
from runners.drive.cards.timing_revision_events import replay_revision_events
from runners.drive.cards.timing_revision_input import relative
from runners.drive.cards.timing_p6 import gzip_equal, gzread
from runners.drive.cards.batch_runtime import read,filehash,atomic
from tests.test_drive_cards_timing_revision_events import event

CONFIG=dict(mode='constructed',expected_sessions=4,cumulative_wall_seconds=120)

def source(events,sid='s'):
    replay=replay_revision_events(events)
    return dict(session=sid,occurrence_count=len(replay['revision_events']),
                revision_events=replay['revision_events'],delta_clock=replay['delta_clock'])

def deletion(ms,origin='user'):
    return [event(0,doc=''),event(100,[{'insert':'cat '}]),event(ms,[{'delete':1}],source=origin)]

@pytest.mark.parametrize('milliseconds,label',[(2099,'immediate_user_deletion'),(2100,'later_user_edit'),(2101,'later_user_edit')])
def test_exact_pause_boundary(milliseconds,label):
    r=card.classify(source(deletion(milliseconds)))['rows'][0]
    assert r['counts'][label]==1 and sum(r['counts'].values())==1

def test_boundary_is_a_gap_not_total_age():
    events=[event(0,doc=''),event(100,[{'insert':'cat '}]),event(1500,[{'retain':4},{'insert':'x '}]),event(2900,[{'delete':1}])]
    r=card.classify(source(events))['rows'][0]
    assert r['counts']['immediate_user_deletion']==1 and r['next_pause_ordinal'] is None

def test_immediate_and_late_are_retained_together():
    events=deletion(200)+[event(3000,[{'delete':1}])]
    r=card.classify(source(events))['rows'][0]
    assert r['counts']['immediate_user_deletion']==r['counts']['later_user_edit']==1

def test_insertion_and_api_are_not_human_immediate_deletions():
    events=[event(0,doc=''),event(100,[{'insert':'cat '}]),event(200,[{'retain':1},{'insert':'h'}]),event(3000,[{'delete':1}],source='api')]
    r=card.classify(source(events))['rows'][0]
    assert r['counts']==dict(immediate_user_deletion=0,later_user_edit=0,within_burst_user_insertion=1,non_user_change=1)
    assert [c['before_next_pause'] for c in r['changes']]==[True,False]

def test_clock_is_the_original_logged_delta_clock():
    events=[event(0,doc=''),event(100,[{'insert':'cat '}]),event(1500,[{'retain':4},{'insert':'x '}],source='api'),event(2900,[{'delete':1}])]
    assert card.classify(source(events))['rows'][0]['counts']['immediate_user_deletion']==1

def test_unicode_identity_and_tied_timestamps():
    events=[event(0,doc=''),event(100,[{'insert':'\U0001f600 cat '}]),event(100,[{'delete':2}])]
    r=card.classify(source(events));assert r['occurrence_count']==2
    assert r['rows'][0]['counts']['immediate_user_deletion']==1

@pytest.mark.parametrize('bad',['missing_clock','changed_time','lost_occurrence','foreign_character'])
def test_source_consistency_refusals(bad):
    value=source(deletion(200))
    if bad=='missing_clock':value['delta_clock'].pop()
    if bad=='changed_time':value['revision_events'][0]['changes'][0]['seconds']+=1
    if bad=='lost_occurrence':value['occurrence_count']+=1
    if bad=='foreign_character':value['revision_events'][0]['changes'][0]['affected_character_ids']=[999]
    with pytest.raises(ValueError):card.classify(value)

def fixture(root):
    root=Path(root);out=root/'output';out.mkdir(parents=True)
    events=[deletion(2099),deletion(2100),deletion(2101,'api'),
            [event(0,doc=''),event(100,[{'insert':'cat '}]),event(200,[{'retain':1},{'insert':'h'}])]]
    index=[]
    for i,raw in enumerate(events):
        sid=str(i);value=source(raw,sid);target=out/relative(sid);gzip_equal(target,value)
        index.append(dict(session=sid,file=relative(sid),sha256=filehash(target)))
    atomic(out/'INDEX.json',index)
    complete=root/'COMPLETE.json';atomic(complete,dict(status='COMPLETE',fresh_process_verified=True,synthetic_fixture=True,
        outputs={p.relative_to(root).as_posix():filehash(p) for p in out.rglob('*') if p.is_file()}))
    proof=root/'PROOF.json';atomic(proof,dict(verified=True,write_through_complete=True,complete_sha256=filehash(complete)))
    return dict(source_complete=str(complete.resolve()),source_proof=str(proof.resolve()))

def test_complete_handler_reentry_and_tamper(tmp_path):
    inputs=fixture(tmp_path/'source');out=tmp_path/'out';summary=card.execute(out,inputs,CONFIG)
    assert summary['sessions']==4 and summary['event_counts']=={k:1 for k in card.LABELS}
    assert card.verify(out,inputs,CONFIG)['full_classifier_replay']
    original=(out/'SUMMARY.json').read_bytes();assert card.execute(out,inputs,CONFIG)==summary
    assert (out/'SUMMARY.json').read_bytes()==original
    p=out/relative('0');p.write_bytes(b'changed')
    with pytest.raises(ValueError):card.verify(out,inputs,CONFIG)

def test_unadmitted_source_and_scope_refuse(tmp_path):
    inputs=fixture(tmp_path/'source');proof=read(inputs['source_proof']);proof['write_through_complete']=False;atomic(inputs['source_proof'],proof)
    with pytest.raises(ValueError):card.execute(tmp_path/'out',inputs,CONFIG)
    with pytest.raises(ValueError):card.execute(tmp_path/'out2',inputs,dict(CONFIG,pause_seconds=1))

def test_exhausted_allowance_refuses(tmp_path):
    inputs=fixture(tmp_path/'source');out=tmp_path/'out';out.mkdir();atomic(out/'ACTIVE_TIME.json',dict(seconds=121))
    with pytest.raises(TimeoutError):card.execute(out,inputs,CONFIG)

def execute(output,inputs,config):
    result=card.execute(output,inputs,config)
    assert result['sessions']==4 and result['event_counts']=={k:1 for k in card.LABELS}
    return result

def verify(output,inputs,config):return card.verify(output,inputs,config)
