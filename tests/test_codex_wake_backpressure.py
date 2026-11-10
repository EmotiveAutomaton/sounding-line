"""Native queue backpressure without real messages, model calls or research work."""
import sys
import uuid
from pathlib import Path

import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import codex_watch as watch
import codex_queue_api as api
import codex_hooks as hooks
from codex_common import database,put,get

OWNER='01a0735d-fef3-7ce2-aaee-5f0029701cca'


class Queue:
    def __init__(self): self.rows=[]; self.deleted=[]; self.adds=0
    def call(self,method,params):
        assert params['threadId']==OWNER
        if method=='thread/queue/list': return {'data':list(self.rows),'nextCursor':None}
        if method=='thread/queue/delete':
            qid=params['queuedSubmissionId'];self.deleted.append(qid)
            old=len(self.rows);self.rows=[r for r in self.rows if r['id']!=qid]
            return {'deleted':len(self.rows)!=old}
        assert method=='thread/queue/add'
        self.adds+=1
        row={k:params[k] for k in ['clientUserMessageId','input']};row['id']=str(uuid.uuid4())
        self.rows.append(row);return {'queuedSubmission':row}


@pytest.fixture
def env(tmp_path):
    state=tmp_path/'.agent-state'
    with database(state) as db:
        put(db,'owner',OWNER);put(db,'owner_phase','idle');put(db,'owner_seen',100)
    cfg=dict(codex='fake',queue_transport='native-api',single_pending_wake=True,
             wake_mode='events_and_idle',routine_interval_seconds=0,fallback_seconds=14400)
    q=Queue()
    def sender(exe,repo,state,owner,text,ids): return api.enqueue(q,owner,text,ids)
    def reconcile(exe,repo,state,owner,known,render): return api.reconcile(q,owner,known,render)
    return tmp_path,state,cfg,q,sender,reconcile


def add(state,name,at=100):
    with database(state) as db: return watch.add_event(db,name,name,at)


def row(state,eid):
    with database(state) as db: return dict(db.execute('SELECT * FROM events WHERE id=?',(eid,)).fetchone())


def deliver(env,at=101):
    repo,state,cfg,q,sender,_=env
    return watch.deliver(cfg,state=state,repo=repo,now=at,native_sender=sender)


def reconcile(env,at=102):
    repo,state,cfg,q,_,fn=env
    return watch.reconcile_native_queue(cfg,state=state,repo=repo,now=at,reconciler=fn)


def test_acked_but_unconsumed_wake_cannot_stack(env):
    _,state,_,q,_,_=env
    first=add(state,'first/COMPLETE.json');assert deliver(env)=='queued'
    watch.acknowledge(first,state=state,now=102)
    second=add(state,'second/FAILED.json',103)
    assert deliver(env,104)=='native-queue-pending'
    assert len(q.rows)==1 and row(state,second)['attempts']==0
    result=reconcile(env,105)
    assert len(result['retired'])==1 and q.rows==[]
    assert row(state,first)['acknowledged']==102
    assert deliver(env,106)=='queued' and len(q.rows)==1


def test_bursts_collect_while_owner_active_including_urgent(env):
    _,state,_,q,_,_=env
    with database(state) as db: put(db,'owner_phase','active')
    ids=[add(state,n,101) for n in ['a/COMPLETE.json','b/PAUSED.json','c/FAILED.json']]
    assert deliver(env,102)=='owner-active' and q.rows==[]
    with database(state) as db: put(db,'owner_phase','idle')
    assert deliver(env,103)=='queued' and len(q.rows)==1
    assert all(eid in api.wake_text(q.rows[0]) for eid in ids)
    add(state,'d/FAILED.json',104)
    assert deliver(env,105)=='awaiting-acknowledgement' and q.adds==1


def test_partial_ack_keeps_batch_and_unrelated_user_message(env):
    _,state,_,q,_,_=env
    a=add(state,'a/COMPLETE.json');b=add(state,'b/COMPLETE.json')
    assert deliver(env)=='queued'
    user={'id':str(uuid.uuid4()),'clientUserMessageId':str(uuid.uuid4()),
          'input':[{'type':'text','text':'My ordinary question','text_elements':[]}]}
    q.rows.append(user);watch.acknowledge(a,state=state,now=102)
    assert reconcile(env)['retired']==[] and len(q.rows)==2
    watch.acknowledge(b,state=state,now=103)
    reconcile(env,104);assert q.rows==[user]


def test_deleted_unlanded_wake_recovers_without_ack_or_new_clock(env):
    _,state,_,q,_,_=env
    eid=add(state,'a/COMPLETE.json');assert deliver(env)=='queued'
    q.rows.clear();reconcile(env,110);assert row(state,eid)['state']=='queued'
    reconcile(env,169);assert row(state,eid)['state']=='queued'
    with database(state) as db: put(db,'owner_phase','active');put(db,'owner_seen',170)
    reconcile(env,171);assert row(state,eid)['state']=='queued'
    with database(state) as db: put(db,'owner_phase','idle')
    reconcile(env,172);assert row(state,eid)['state']=='pending'
    assert row(state,eid)['acknowledged'] is None
    assert deliver(env,173)=='queued' and len(q.rows)==1
    with database(state) as db:
        assert get(db,'last_acknowledged') is None and get(db,'wake_plan') is None


def test_delivered_unacknowledged_is_not_requeued_when_absent(env):
    _,state,_,q,_,_=env
    eid=add(state,'a/COMPLETE.json');assert deliver(env)=='queued';q.rows.clear()
    with database(state) as db: db.execute('INSERT INTO deliveries VALUES (?,?,?)',(eid,102,OWNER))
    reconcile(env,110);reconcile(env,1000)
    assert row(state,eid)['state']=='queued' and row(state,eid)['acknowledged'] is None


def test_late_submission_hook_records_already_acked_delivery(env):
    repo,state,_,q,_,_=env
    eid=add(state,'a/COMPLETE.json');assert deliver(env)=='queued'
    text=api.wake_text(q.rows[0]);watch.acknowledge(eid,state=state,now=102)
    hooks.handle(dict(hook_event_name='UserPromptSubmit',cwd=str(repo),session_id=OWNER,prompt=text),repo=repo,state=state)
    with database(state) as db:
        assert db.execute('SELECT event_id FROM deliveries').fetchone()['event_id']==eid
    assert row(state,eid)['acknowledged']==102


def test_concurrent_send_after_ack_still_has_transport_lock(env):
    repo,state,cfg,q,_,_=env
    first=add(state,'a/COMPLETE.json')
    def sender(*args):
        watch.acknowledge(first,state=state,now=102);add(state,'b/COMPLETE.json',103)
        assert deliver(env,104)=='delivery-in-progress'
        return api.enqueue(q,args[3],args[4],args[5])
    assert watch.deliver(cfg,state=state,repo=repo,now=101,native_sender=sender)=='queued'
    assert q.adds==1


def test_unknown_or_changed_wake_is_preserved_and_blocks(env):
    _,state,_,q,_,_=env
    eid=add(state,'a/COMPLETE.json');assert deliver(env)=='queued'
    watch.acknowledge(eid,state=state,now=102)
    q.rows[0]['input'][0]['text']+=' changed'
    assert reconcile(env)['unrecognized_wakes']==[q.rows[0]['id']]
    add(state,'b/COMPLETE.json',103)
    assert deliver(env,104)=='native-queue-pending' and not q.deleted


def test_inspection_failure_does_not_change_event(env):
    repo,state,cfg,_,_,_=env
    eid=add(state,'a/COMPLETE.json');assert deliver(env)=='queued';before=row(state,eid)
    def fail(*args): raise OSError('offline')
    with pytest.raises(OSError): watch.reconcile_native_queue(cfg,state=state,repo=repo,now=200,reconciler=fail)
    assert row(state,eid)==before
