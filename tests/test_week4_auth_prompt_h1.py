import json
import pytest
from runners.drive import week4_auth_prompt_h1 as a


def message(text,stop='end_turn'):
    return dict(model=a.MODEL,stop_reason=stop,content=[dict(type='text',text=text)],usage=dict(input_tokens=200,output_tokens=5))


@pytest.mark.parametrize('text,expected',[('{"score":0}',0),('{"score":9}',9),('{"score":true}',None),('{"score":10}',None),('{"score":-1}',None),('{"score":3.0}',None),('{"score":2,"score":8}',None),('{"score":4,"extra":0}',None),('```json\n{"score":8}\n```',None),('8',None)])
def test_complete_strict_score(text,expected):assert a.parse(message(text))==expected


def test_stop_and_payload_restrictions():
    assert a.parse(message('{"score":4}','refusal')) is None
    m=message('{"score":4}');m['model']='foreign';assert a.parse(m) is None
    m=message('{"score":4}');m['content'].append(m['content'][0]);assert a.parse(m) is None
    p=a.params(['Writer text','Other text'])
    assert set(json.loads(p['messages'][0]['content']))=={'text_a','text_b'}
    assert p['max_tokens']==32 and p['thinking']=={'type':'disabled'}
    for bad in (['text'],['text',''],['word '*401,'text']):
        with pytest.raises(ValueError):a.params(bad)


def truth():return [dict(custom_id=str(i),same_writer=i<50) for i in range(100)]


def test_auc_known_answers_ties_and_missing_bound():
    gold=truth();perfect={str(i):9 if i<50 else 0 for i in range(100)}
    assert a.agreement(gold,perfect)['auc_lower_bound']==1
    assert a.agreement(gold,{k:9-v for k,v in perfect.items()})['auc_lower_bound']==0
    constant=a.agreement(gold,{str(i):5 for i in range(100)})
    assert constant['auc_lower_bound']==.5 and not constant['agreement_passes']
    perfect.pop('0');perfect.pop('99');r=a.agreement(gold,perfect)
    assert r['valid_comparisons']==2401 and r['valid_only_auc']==1 and r['auc_lower_bound']==2401/2500
    assert a.agreement(gold,{})['auc_lower_bound']==0
    with pytest.raises(ValueError):a.agreement(gold,{'foreign':9})


@pytest.fixture
def prepared(tmp_path,monkeypatch):
    monkeypatch.setattr(a,'ROOT',tmp_path/'AUTH');a.ROOT.mkdir();rows=[];gold=[]
    for i in range(100):
        texts=[f'Constructed left {i}.',f'Constructed right {i}.'];p=a.params(texts);item=a.digest(sorted(texts));cid=a.digest(['AUTH',1,item,p])
        rows.append(dict(item_id=item,custom_id=cid,params=p));gold.append(dict(custom_id=cid,same_writer=i<50))
    a.freeze(a.ROOT/'REQUESTS.json',rows);a.freeze(a.ROOT/'GOLD.json',dict(provenance='recorded writer identity from sealed original cohort',labels=gold))
    a.freeze(a.ROOT/'SOURCE.json',dict(pins={},prepared={n:a.filehash(a.ROOT/n) for n in ('REQUESTS.json','GOLD.json')}))
    calls=[]
    def request(path,payload=None):
        calls.append((path,payload))
        if path.startswith('/v1/models/'):return json.dumps(dict(id=a.MODEL)).encode()
        if path.endswith('count_tokens'):return b'{"input_tokens":200}'
        raise AssertionError('No generation in test')
    monkeypatch.setattr(a,'request',request)
    return rows,gold,calls


def test_actual_count_binding_and_private_truth_never_in_wire(prepared):
    rows,gold,calls=prepared;plan=a.count(a.PHASE)
    assert plan['node']=='AUTH' and plan['attempted']==100 and len(calls)==101
    wire=a.read(a.ROOT/a.PHASE/'WIRE.json')
    assert wire==dict(requests=[{k:r[k] for k in ('custom_id','params')} for r in rows])
    assert 'same_writer' not in json.dumps(wire)
    assert a.count(a.PHASE)==plan and len(calls)==101
    (a.ROOT/'GOLD.json').write_text('{}',encoding='utf8')
    with pytest.raises(ValueError):a.bound_plan(a.PHASE)


def test_submit_reserves_once_and_unknown_cannot_retry(prepared,monkeypatch):
    rows,gold,calls=prepared;a.count(a.PHASE);reserved=[]
    def reserve(*args):reserved.append(args);return dict(booked_cents=args[2])
    monkeypatch.setattr(a.budget,'reserve',reserve)
    def fail(path,payload):
        assert len(reserved)==1 and path=='/v1/messages/batches'
        raise TimeoutError('constructed unknown delivery')
    monkeypatch.setattr(a,'request',fail)
    with pytest.raises(TimeoutError):a.submit(a.PHASE)
    assert a.read(a.ROOT/a.PHASE/'UNKNOWN.json')['reservation_retained']
    with pytest.raises(ValueError):a.submit(a.PHASE)
    assert len(reserved)==1


def test_complete_replay_accounting_and_coverage(prepared,monkeypatch):
    rows,gold,calls=prepared;a.count(a.PHASE);f=a.ROOT/a.PHASE
    a.freeze(f/'SUBMITTED.json',dict(batch_id='msgbatch_fixture'));a.freeze(f/'STATUS.json',dict(id='msgbatch_fixture',processing_status='ended'))
    results=[dict(custom_id=r['custom_id'],result=dict(type='succeeded',message=message(json.dumps(dict(score=9 if i<50 else 0))))) for i,r in enumerate(rows)]
    p=f/'RESULTS.jsonl';p.write_text('\n'.join(json.dumps(r) for r in results),encoding='utf8');settled=[]
    monkeypatch.setattr(a.budget,'reconcile',lambda *args:settled.append(args))
    receipt=a.replay(a.PHASE)
    assert receipt['passes'] and receipt['auc_lower_bound']==1 and receipt['valid']==100
    assert receipt['tokens']==dict(input_tokens=20000,output_tokens=500) and receipt['measured_token_cents']==1
    assert settled[0][0]==a.INVOCATION and settled[0][1]==1 and len(settled[0][2])==64
    p.write_text('\n'.join(json.dumps(r) for r in results[:-1]),encoding='utf8')
    with pytest.raises(ValueError):a.replay(a.PHASE)


def test_frozen_fresh_partition_and_refusals():
    pairs=[dict(pair_id=str(i),genre='argumentative',same_writer=i%2==0) for i in range(200)]
    selection=dict(calibration=[str(i) for i in range(100)],fresh=[str(i) for i in range(100,200)])
    assert a.fresh_selection(pairs,selection,selection['calibration'])==pairs[100:]
    with pytest.raises(ValueError):a.fresh_selection(pairs,selection,selection['fresh'])
    broken=dict(selection,fresh=list(reversed(selection['fresh'])))
    with pytest.raises(ValueError):a.fresh_selection(pairs,broken,selection['calibration'])
    pairs[100]['same_writer']=False
    with pytest.raises(ValueError):a.fresh_selection(pairs,selection,selection['calibration'])


def test_original_gate_and_format_unchanged():
    from runners.drive import week4_auth as original
    gold=truth()
    labels={str(i):(i*7)%10 for i in range(100)}
    assert a.agreement(gold,labels)==original.agreement(gold,labels)
    for text in ('{"score":0}','{"score":9}','{"score":true}','{"score":1.0}'):
        assert a.parse(message(text))==original.parse(message(text))
    texts=['First excerpt.','Second excerpt.']
    before=original.params(texts);after=a.params(texts)
    assert before.pop('system')!=after.pop('system')
    assert before==after
