import sys
from pathlib import Path
import uuid
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import codex_queue_api as api
import codex_watch as watch
from codex_common import database, put

OWNER='01a077b0-3653-7bc3-a3f3-95926baafee7'

class Fake:
    def __init__(self): self.rows=[]; self.methods=[]; self.fail=False
    def call(self,method,params):
        self.methods.append(method)
        assert params['threadId']==OWNER
        if method=='thread/queue/list': return {'data':self.rows,'nextCursor':None}
        assert method=='thread/queue/add'
        row={k:params[k] for k in ('input','clientUserMessageId')}; row['id']=str(uuid.uuid4())
        self.rows.append(row)
        if self.fail: raise TimeoutError('accepted then connection lost')
        return {'queuedSubmission':row}

def test_acceptance_and_reconciled_retry_do_not_duplicate():
    c=Fake(); first=api.enqueue(c,OWNER,'completed experiment',['event'])
    assert api.enqueue(c,OWNER,'completed experiment',['event'])==first
    assert c.methods.count('thread/queue/add')==1

def test_lost_receipt_reconciles_existing_submission():
    c=Fake(); c.fail=True
    with pytest.raises(TimeoutError): api.enqueue(c,OWNER,'completed experiment',['event'])
    c.fail=False
    assert api.enqueue(c,OWNER,'completed experiment',['event'])==c.rows[0]['id']
    assert c.methods.count('thread/queue/add')==1

def test_changed_message_refuses_existing_identity():
    c=Fake(); api.enqueue(c,OWNER,'first',['event'])
    with pytest.raises(ValueError): api.enqueue(c,OWNER,'changed',['event'])
    assert len(c.rows)==1

def test_cancellation_before_write():
    c=Fake()
    with pytest.raises(RuntimeError): api.enqueue(c,OWNER,'first',['event'],lambda:True)
    assert c.methods==['thread/queue/list']

def test_duplicate_identity_refuses():
    c=Fake(); api.enqueue(c,OWNER,'first',['event']); c.rows.append(dict(c.rows[0]))
    with pytest.raises(ValueError): api.enqueue(c,OWNER,'first',['event'])

@pytest.mark.parametrize('bad',[{}, {'id':'invalid','input':[],'clientUserMessageId':'wrong'}])
def test_malformed_receipt_refuses(bad):
    c=Fake(); original=c.call
    c.call=lambda m,p: {'queuedSubmission':bad} if m=='thread/queue/add' else original(m,p)
    with pytest.raises((ValueError,KeyError)): api.enqueue(c,OWNER,'first',['event'])

@pytest.mark.parametrize('failure',[False,True])
def test_watch_acceptance_unknown_and_outbox(tmp_path,failure):
    state=tmp_path/'.agent-state'
    with database(state) as db:
        put(db,'owner',OWNER); watch.add_event(db,'results/COMPLETE.json','hash',100)
    def sender(*args):
        if failure: raise TimeoutError('ambiguous')
        return '01a077b0-3653-7bc3-a3f3-95926baafee7'
    config={'codex':'unused','transition_only':True,'queue_transport':'native-api'}
    assert watch.deliver(config,state=state,repo=tmp_path,now=101,native_sender=sender)==('unknown' if failure else 'queued')
    def forbidden(*a): raise AssertionError('duplicate send')
    assert watch.deliver(config,state=state,repo=tmp_path,now=200,native_sender=forbidden)=='awaiting-acknowledgement'
    with database(state) as db:
        row=dict(db.execute('SELECT * FROM events').fetchone())
        assert row['acknowledged'] is None and row['attempts']==1

def test_repeated_pagination_refuses():
    c=Fake(); c.call=lambda m,p:{'data':[],'nextCursor':'same'}
    with pytest.raises(ValueError): api.inventory(c,OWNER)
