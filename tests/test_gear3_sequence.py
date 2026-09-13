"""Finite sequence ownership and independent-failure checks; no provider calls."""
import hashlib,json
from pathlib import Path
import pytest
from runners import gear3_sequence as sequence,gear3_campaign as cost
from runners.stage10 import gear3_io as storage
from runners.stage10.contracts import digest

@pytest.mark.parametrize('outcome',['complete','failed','unknown','changed-input'])
def test_finite_sequence_retirement_replay_and_uncertain_owner(tmp_path,monkeypatch,outcome):
    repo=tmp_path/'repo';repo.mkdir();ledger=repo/'ledger.json'
    monkeypatch.setattr(sequence,'authoritative_ledger',lambda _:ledger)
    pilot={'status':'PASS','scope':'constructed only'};(repo/'pilot.json').write_text(json.dumps(pilot))
    jobs=[]
    for name,node,domain,deps in [('a1','A','human',[]),('a2','A','human',[]),('b1','B','history',['a1']),('c1','C','ghost',[])]:
        blob=(name+' fixture').encode();(repo/(name+'.zip')).write_bytes(blob)
        jobs.append({'invocation':name,'node':node,'failure_domain':domain,'dependencies':deps,'bundle':name+'.zip',
            'bundle_sha256':hashlib.sha256(blob).hexdigest(),'seconds':60,'startup_seconds':30,'overhead_cents':0})
    plan={'schema':'gear3.execution_plan.1','approval':'constructed only','pilot':'pilot.json','pilot_sha256':digest(pilot),
        'allowed_bundle_sha256':[j['bundle_sha256'] for j in jobs],'jobs':jobs}
    path=repo/'plan.json';path.write_text(json.dumps(plan));calls=[]
    if outcome=='changed-input':(repo/'a1.zip').write_bytes(b'changed')
    def dispatch(root,args):
        calls.append(args.invocation);status='FAILED' if outcome=='failed' and args.invocation=='a1' else 'COMPLETE'
        if outcome=='unknown':status='UNKNOWN'
        with cost.CampaignLedger(ledger).transaction() as data:
            data['runs'].append({'campaign_id':cost.CAMPAIGN,'invocation_id':args.invocation,'owner_ended':status!='UNKNOWN',
                'status':status,'command':['fixture',hashlib.sha256(args.bundle.read_bytes()).hexdigest()]})
        if status=='UNKNOWN':raise RuntimeError('constructed uncertain owner')
        local=root/'private/gear3/G3-S10-READER-1/invocations'/args.invocation;raw=local/'raw';raw.mkdir(parents=True)
        terminal={'status':status};(raw/'TERMINAL.json').write_text(json.dumps(terminal))
        receipt=storage.make_archive(raw,local/'OUTPUT.zip')
        (local/'RETRIEVAL.json').write_text(json.dumps(receipt));(local/'REMOTE_TERMINAL.json').write_text(json.dumps(terminal))
        return terminal
    monkeypatch.setattr(sequence,'dispatch',dispatch)
    if outcome in {'unknown','changed-input'}:
        with pytest.raises((ValueError,RuntimeError)):sequence.run_plan(repo,path,repo/'unused-account.json')
        assert calls==(['a1'] if outcome=='unknown' else [])
        with pytest.raises((ValueError,RuntimeError)):sequence.run_plan(repo,path,repo/'unused-account.json')
        assert calls==(['a1'] if outcome=='unknown' else [])
        return
    result=sequence.run_plan(repo,path,repo/'unused-account.json')
    assert [r['status'] for r in result['jobs']]==(['FAILED','NOT_RUN','NOT_RUN','COMPLETE'] if outcome=='failed' else ['COMPLETE']*4)
    assert calls==(['a1','c1'] if outcome=='failed' else ['a1','a2','b1','c1'])
    assert sequence.run_plan(repo,path,repo/'unused-account.json')==result
    assert calls==(['a1','c1'] if outcome=='failed' else ['a1','a2','b1','c1'])
    (repo/'private/gear3/G3-S10-READER-1/invocations/a1/OUTPUT.zip').write_bytes(b'corrupt')
    with pytest.raises(Exception):sequence.run_plan(repo,path,repo/'unused-account.json')
