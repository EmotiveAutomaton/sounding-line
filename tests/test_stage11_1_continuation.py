"""Literal queue rehearsal and causal/privacy/restart boundaries, never GPU calls."""
import copy
import json
from pathlib import Path
import pytest
from runners.stage11_1 import branch_runtime as run, preflight as prep, continuation as queue
from runners.stage11_1.common import freeze,read,digest,contract,allocation
from runners.stage11_1.construct import twins
from runners.stage11_1.cheap import fit


def setup(root):
    contract(root);allocation(root)
    for m in ('DIRECT','REVIEW','ACCOUNT'):
        freeze(root/(m+'_PILOT_PASSED-v3.json'),dict(status='COMPLETE',fake=True,sources=run.base.source_pin()))
    rows=twins()[:2];freeze(root/'CHEAP_FIT.json',fit(rows))
    return rows


def save(root,p):
    path=root/'branch_plans'/f"{p['id']}.json";freeze(path,p);return path


def test_real_queue_rehearsal_and_reentry_no_extra_attempt(tmp_path,monkeypatch):
    rows=setup(tmp_path)
    pilot=prep.auxiliary_pilots()[0];pp=save(tmp_path,pilot)
    science=prep.s2_plan([dict(rows[0],observations=rows[0]['observations'])],['direct','review']);sp=save(tmp_path,science)
    manifest=dict(items=[dict(id=p['id'],runner='branch',path=str(path.relative_to(tmp_path)),digest=digest(p),calls=p['maximum_calls'],requires=p['requires'],next_action=p['next_action']) for p,path in [(pilot,pp),(science,sp)]])
    mp=tmp_path/'manifest.json';freeze(mp,manifest)
    monkeypatch.setattr(run,'api',lambda *a,**k:pytest.fail('fake transport escaped'))
    queue.run(tmp_path,mp,True)
    count=run.base.budget(tmp_path)['attempts']
    assert read(tmp_path/'continuation/setup-v1/AWAITING_SELECTION.json')['status']=='AWAITING_SELECTION'
    assert read(tmp_path/'branch_analysis/S2-evidence-v1/COMPLETE.json')['status']=='COMPLETE'
    queue.run(tmp_path,mp,True)
    assert run.base.budget(tmp_path)['attempts']==count
    tasks=science['tasks'];_,outputs=run.execute(tmp_path,sp,True,True)
    for condition in ('human-fixed','human-random','human-chosen'):
        own=[outputs[t['id']]['evidence'] for t in tasks if t.get('condition')==condition]
        assert own[0]==own[1]


def test_semantic_raw_and_private_target_tampering_refused(tmp_path):
    rows=setup(tmp_path);p=prep.plan('known','S2',[prep.forecast(rows[0],'known')],'known','constructed','next')
    path=save(tmp_path,p);run.execute(tmp_path,path,True)
    original=read(path);changed=copy.deepcopy(original);changed['tasks'][0]['evaluator']['target']['handling']='ignore'
    path.write_text(json.dumps(changed))
    with pytest.raises(ValueError,match='immutable record'):run.execute(tmp_path,path,True)
    path.write_text(json.dumps(original))
    raw=next((tmp_path/'calls').rglob('RAW.json'));content=read(raw);content['message']['content']='{}';raw.write_text(json.dumps(content))
    with pytest.raises(ValueError,match='changed request or response'):run.execute(tmp_path,path,True)


def test_partial_blocks_and_resource_stop_do_not_retry(tmp_path):
    rows=setup(tmp_path);p=prep.plan('partial','S4',[prep.forecast(rows[0],'known','review')],'known','constructed','next');path=save(tmp_path,p)
    task=p['tasks'][0];partial=tmp_path/'calls'/p['id']/task['id']/'0';partial.mkdir(parents=True)
    with pytest.raises(ValueError,match='partial block'):run.execute(tmp_path,path,True)
    other=prep.plan('stopped','S4',[prep.forecast(rows[0],'none')],'known','constructed','next');op=save(tmp_path,other)
    (tmp_path/'PAUSE').touch();result,_=run.execute(tmp_path,op,True)
    assert result['status']=='STOPPED' and run.base.budget(tmp_path)['attempts']==0
    (tmp_path/'PAUSE').unlink()
    with pytest.raises(ValueError,match='explicit continuation'):run.execute(tmp_path,op,True)
    assert run.base.budget(tmp_path)['attempts']==0


def test_auxiliary_boundary_and_no_target_history():
    pilots=prep.auxiliary_pilots()
    for p in pilots[:3]:
        for t in p['tasks']:
            q=run.auxiliary_request(t)
            assert run.parse(run.fake_raw(q,t['kind']),q,{},t['kind']) is not None
            changed=copy.deepcopy(t);changed['public']['target']='private answer'
            with pytest.raises(ValueError):run.auxiliary_request(changed)
    t=copy.deepcopy(pilots[0]['tasks'][0]);t['public']['menu'][0]['value']='hidden observation'
    with pytest.raises(ValueError,match='private observation'):run.auxiliary_request(t)


def test_twins_match_requests_until_declared_observation():
    rows=twins();assert len(rows)==48
    for a,b in zip(rows[::2],rows[1::2]):
        assert a['views']==b['views'] and a['target']!=b['target']
        assert run.model.request_for(a['views']['artifact'])==run.model.request_for(b['views']['artifact'])
        assert a['cues']['true']['source']!=b['cues']['true']['source']
    p=prep.s2_plan(rows,['direct'],True)
    assert p['maximum_calls']==192 and {t['condition'] for t in p['tasks']}=={'twins-blind','twins-true','twins-irrelevant','twins-misleading'}


def test_queue_gate_verdict_and_plan_binding(tmp_path):
    setup(tmp_path);freeze(tmp_path/'BAD.json',dict(status='FAILED',fake=True))
    assert not queue.admitted(tmp_path,'BAD.json',True)
    p=prep.auxiliary_pilots()[0];path=save(tmp_path,p)
    with pytest.raises(ValueError,match='plan changed'):queue.checked_plan(tmp_path,dict(path=str(path.relative_to(tmp_path)),digest='bad'))
    item=dict(id='one',runner='branch',path='x')
    with pytest.raises(ValueError,match='duplicate'):queue.validate_manifest(dict(items=[item,item]))


def test_history_uses_strict_earlier_cutoffs_and_matched_text():
    examples=twins();cohort=dict(discovery=[],breadth=[]);sources={}
    for writer,start in [('w1',10),('w2',11),('w3',12)]:
        for n,stamp in enumerate([start,100,200]):
            row=copy.deepcopy(examples[0]);row.update(key=f'{writer}-{n}',writer=writer,session=f'{writer}-{n}',ordinal=0,cutoff_ordinal=4)
            trace=copy.deepcopy(row['trace']);trace=trace[:4]
            for i,e in enumerate(trace):e['eventTimestamp']=stamp+i
            event=__import__('runners.stage11.replay',fromlist=['replay']).replay(trace)['events'][0]
            sources[row['session']]=(trace,{0:event});cohort['discovery'].append(row)
    p,audit=prep.history_plan(cohort,sources)
    assert len(audit['admission'])==3
    for r in audit['admission']:assert r['history_cutoff']<r['first_target'] and r['donor_cutoff']<r['first_target']
    hypotheses={t['id']:t for t in p['tasks'] if t['kind']=='history'}
    for t in p['tasks']:
        if 'history_ref' in t:
            assert set(hypotheses[t['history_ref']]['public'])=={'earlier_history'}
    by={}
    for t in p['tasks']:
        if t.get('condition') in ('history-own-raw','history-donor-raw'):by.setdefault(t['evaluator']['key'],[]).append(len(t['public']['history']['record_excerpt']))
    assert all(len(v)==2 and v[0]==v[1] for v in by.values())


def test_invalid_literal_method_does_not_admit_it(tmp_path,monkeypatch):
    setup(tmp_path);p=prep.auxiliary_pilots()[0];path=save(tmp_path,p)
    monkeypatch.setattr(run,'fake_raw',lambda *a:dict(done=True,done_reason='stop',message=dict(content='{}'),fake=True))
    result,_=run.execute(tmp_path,path,True)
    assert result['status']=='INSTRUMENT_FAILED' and result['invalid']==2
    assert not (tmp_path/p['pilot_gate']).exists()


def test_known_corrected_claims_and_identity_null_are_distinct():
    row=twins()[0];truth=row['target']
    oracle=dict(facts=[dict(slot=f['slot'],span_ids=f['span_ids'],span_state=f['span_state'],
                    **{k:[float(x==f[k]) for x in labels] for k,labels in run.model.FIELDS.items()}) for f in truth['facts']],
                handling=[float(x==truth['handling']) for x in run.model.ACTIONS],attributes=truth['attributes'])
    good=run.episode(row,oracle);unknown=run.episode(row,None)
    identity=run.paired_transitions([good],[good]);correction=run.paired_transitions([unknown],[good])
    assert identity['forecast_moved_per_episode']==0 and identity['new_errors_per_episode']==0
    assert correction['corrected_per_episode']==6 and correction['useful_change_per_episode']>0
    harm=run.paired_transitions([good],[unknown]);assert harm['new_errors_per_episode']==6


def test_real_profile_pin_and_uncertain_transport_charge(tmp_path,monkeypatch):
    setup(tmp_path);p=prep.auxiliary_pilots()[0];t=p['tasks'][0]
    monkeypatch.setattr(run,'api',lambda *a,**k:{'models':[{'name':'llama3.1:8b','digest':'wrong'}]})
    with pytest.raises(ValueError,match='identity differs'):run.profile_check('llama')
    monkeypatch.setattr(run.base,'acquire',lambda:None);monkeypatch.setattr(run.base,'release_gpu_lock',lambda:None)
    def transport(path,*args,**kwargs):
        if path=='/api/chat':raise TimeoutError('unknown server execution')
        return {}
    monkeypatch.setattr(run,'api',transport)
    with pytest.raises(RuntimeError,match='uncertain transport'):run.execute_task(tmp_path,p,t,{},False)
    assert run.base.budget(tmp_path)['attempts']==1 and run.base.budget(tmp_path)['charged_seconds']==330
    with pytest.raises(ValueError,match='partial block'):run.execute_task(tmp_path,p,t,{},False)


def test_literal_cli_namespace_singleton_and_terminal_receipt(tmp_path):
    import subprocess,sys
    setup(tmp_path);p=prep.auxiliary_pilots()[0];path=save(tmp_path,p)
    manifest=dict(id='cli-rehearsal',items=[dict(id=p['id'],runner='branch',path=str(path.relative_to(tmp_path)),digest=digest(p),calls=2,requires=[],next_action='done')])
    mp=tmp_path/'queue.json';freeze(mp,manifest)
    proc=subprocess.run([sys.executable,'-B','-m','runners.stage11_1.continuation',str(mp),'--root',str(tmp_path),'--fake'],capture_output=True,text=True,timeout=30)
    assert proc.returncode==0,proc.stderr
    exit_record=next((tmp_path/'continuation').glob('EXIT-*.json'))
    assert read(exit_record)['scientific_verdict'] is False
    assert read(tmp_path/'continuation/cli-rehearsal/AWAITING_SELECTION.json')['status']=='AWAITING_SELECTION'


def test_end_receipt_failure_releases_owned_gpu_but_keeps_reservation(tmp_path,monkeypatch):
    setup(tmp_path);p=prep.auxiliary_pilots()[0];t=p['tasks'][0];released=[]
    monkeypatch.setattr(run.base,'acquire',lambda:None);monkeypatch.setattr(run.base,'release_gpu_lock',lambda:released.append(True))
    monkeypatch.setattr(run,'api',lambda path,payload,**kw:run.fake_raw(payload,'query') if path=='/api/chat' else {})
    original=run.write_new
    def failing(path,value):
        if path.name=='END.json':raise OSError('injected receipt write failure')
        original(path,value)
    monkeypatch.setattr(run,'write_new',failing)
    with pytest.raises(OSError,match='receipt write failure'):run.execute_task(tmp_path,p,t,{},False)
    assert released==[True] and run.base.budget(tmp_path)['charged_seconds']==330
