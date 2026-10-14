import json
import pytest
from runners.stage14_midweek import api

def test_all_reader_postures_are_tool_free_and_supported():
    for reader in api.MODELS:
        p=api.params(reader,{'history':[]})
        assert not set(p)&{'tools','tool_choice','temperature','top_p','top_k','mcp_servers'}
        assert p['output_config']['effort']=='low'
    assert api.params('RS',{})['thinking']=={'type':'between_tools'}
    assert api.params('RH',{})['thinking']=={'type':'disabled'}
    assert api.params('RO',{})['thinking']=={'type':'adaptive'}

def test_budget_counts_all_output_including_hidden_thinking():
    rows=[dict(custom_id='x',reader='RO',params=api.params('RO',{}))]
    assert api.ceiling(rows,{'x':1000})==4  # ceil(1.3*.2 + 1.024) cents + 2
    with pytest.raises(ValueError):api.ceiling(rows,{'x':100000})

def test_disallowed_api_path_never_reads_credential(monkeypatch):
    monkeypatch.setattr(api,'credential',lambda:pytest.fail('credential accessed'))
    with pytest.raises(ValueError):api.request('https://attacker.invalid/collect')

def test_profile_refusal_and_length_contract():
    assert api.profile_text({'stop_reason':'max_tokens','content':[{'type':'text','text':'x'}]}) is None
    msg={'stop_reason':'end_turn','content':[{'type':'thinking','thinking':'private'},{'type':'text','text':'A pattern.'}]}
    assert api.profile_text(msg)=='A pattern.'

def test_batch_lifecycle_saved_replay_and_no_resubmit(tmp_path,monkeypatch):
    from runners.stage14.common import freeze,read
    root=tmp_path/'raw';folder=root/'api-readers-pilot-v1';folder.mkdir(parents=True)
    monkeypatch.setattr(api,'RAW',root)
    row=dict(custom_id='one',reader='RH',arm='H0',params=api.params('RH',{}))
    freeze(folder/'REQUESTS.json',[row])
    freeze(folder/'PLAN.json',dict(at=api.time.time(),source_pins={},reserved_cents=3))
    paid=[];reservations=[]
    def reserve(*args):
        if reservations:raise ValueError('prior attempt; retrieval only')
        reservations.append(args);return {'reserved_cents':3}
    monkeypatch.setattr(api,'reserve',reserve)
    probabilities={name:.25 for name in api.SCHEMA['properties']['choice']['enum']}
    reply=dict(custom_id='one',result=dict(type='succeeded',message=dict(model=api.MODELS['RH'],usage=dict(input_tokens=120,output_tokens=50),stop_reason='end_turn',content=[dict(type='text',text=json.dumps(dict(probabilities=probabilities,choice='accept')))])))
    def request(path,value=None):
        if value is not None:paid.append(path);return b'{"id":"batch_test"}'
        if path.endswith('/results'):return json.dumps(reply).encode()+b'\n'
        return b'{"id":"batch_test","processing_status":"ended"}'
    monkeypatch.setattr(api,'request',request)
    api.submit('readers','pilot')
    with pytest.raises(ValueError):api.submit('readers','pilot')
    assert paid==['/v1/messages/batches']
    assert api.retrieve('readers','pilot')['valid']==1
    monkeypatch.setattr(api,'request',lambda *a:pytest.fail('replay attempted inference'))
    assert api.replay('readers','pilot')['usage_complete']
    from runners.stage14_midweek import budget
    reconciled=[];monkeypatch.setattr(budget,'reconcile_tokens',lambda *a:reconciled.append(a))
    assert api.reconcile('readers','pilot')['status']=='RECONCILED'
    assert reconciled[0][1]==1

def test_unknown_batch_never_resubmits_or_releases(tmp_path,monkeypatch):
    from runners.stage14.common import freeze,read
    root=tmp_path/'raw';folder=root/'api-profiles-pilot-v1';folder.mkdir(parents=True)
    monkeypatch.setattr(api,'RAW',root)
    freeze(folder/'REQUESTS.json',[]);freeze(folder/'PLAN.json',dict(at=api.time.time(),source_pins={},reserved_cents=3))
    calls=[]
    def reserve(*args):
        if calls:raise ValueError('prior attempt')
        calls.append(args);return {'reserved_cents':3}
    monkeypatch.setattr(api,'reserve',reserve)
    monkeypatch.setattr(api,'request',lambda *a:(_ for _ in ()).throw(TimeoutError()))
    with pytest.raises(TimeoutError):api.submit('profiles','pilot')
    assert read(folder/'UNKNOWN.json')['reservation_retained']
    with pytest.raises(ValueError):api.submit('profiles','pilot')
    assert len(calls)==1
