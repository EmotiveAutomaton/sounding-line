import copy
import json
from pathlib import Path

import pytest

from runners.drive import week3_val as val


def fixture(root):
    items = [dict(item_id=val.digest({'VAL-text':f'Constructed item {i}'}), text=f'Constructed item {i}') for i in range(205)]
    joins = {r['item_id']:[dict(writer='private-writer', prompt='private-prompt')] for r in items}
    val.write_preparation(root, items, joins, {'constructed':True}, {}, 0)
    rows = val.selected(root, 'calibration')
    gold = [dict(custom_id=r['custom_id'], v='1'+'0'*9 if i%2 else '0'*10, o=i%3 == 0) for i,r in enumerate(rows)]
    for row in gold: row['o'] = int(row['o'])
    val.freeze(root/'GOLD.json', dict(provenance='agent-made blind before provider access', labels=gold))
    return rows, gold


def message(v='1000000000', o=0):
    return dict(model=val.MODEL,stop_reason='end_turn',content=[dict(type='text',text=json.dumps(dict(v=v,o=o)))],
                usage=dict(input_tokens=150,output_tokens=20))


def test_all_dimensions_compact_schema_and_private_egress():
    p = val.params('Visible source text')
    assert len(val.VALUES) == 10 and set(p['output_config']['format']['schema']['properties']) == {'v','o'}
    assert p['output_config']['format']['schema']['properties']['v']['pattern'] == '^[01]{10}$'
    assert json.loads(p['messages'][0]['content']) == {'text':'Visible source text'}
    assert p['max_tokens'] == 32 and p['thinking'] == {'type':'disabled'} and 'tools' not in p
    for name in val.VALUES: assert name in p['system']


@pytest.mark.parametrize('bad', ['{"v":"111","o":0}', '{"v":"1111111111","o":true}',
    '{"v":"1111111111","o":0,"extra":1}', '{"v":"1111111111","v":"0000000000","o":0}',
    '{"v":"0000000002","o":0}', '{"v":"0000000000\\n","o":0}'])
def test_parser_refuses_malformed_output(bad):
    m = message(); m['content'][0]['text'] = bad; assert val.parse(m) is None


def test_parser_refuses_truncation_model_or_tool_blocks():
    assert val.parse(message()) == {'v':'1000000000','o':0}
    m=message(); m['stop_reason']='max_tokens'; assert val.parse(m) is None
    m=message(); m['model']='other'; assert val.parse(m) is None
    m=message(); m['content'].append({'type':'tool_use'}); assert val.parse(m) is None


def test_known_null_and_planted_kappa_and_prevalence_gate(tmp_path):
    _,gold = fixture(tmp_path/'root'); labels={g['custom_id']:{k:g[k] for k in ('v','o')} for g in gold}
    result=val.agreement(gold,labels)
    assert result['passes'] and result['pooled_kappa'] == 1
    assert result['per_value']['self_direction']['reportable']
    assert not result['per_value']['stimulation']['reportable']
    assert val.kappa([0,0,1,1],[0,1,0,1]) == 0
    assert val.kappa([0,1],[1,0]) == -1 and val.kappa([0,0],[0,0]) is None
    for value in labels.values(): value['v']='1'*10; value['o']=1
    assert not val.agreement(gold,labels)['passes']


def test_fresh_repair_retains_entire_original_population_and_stops_at_one(tmp_path):
    root=tmp_path/'original'; rows,_=fixture(root)
    val.freeze(root/'calibration/COMPLETE.json',dict(passes=False))
    val.freeze(root/'calibration/RECONCILED.json',dict(booked_cents=1))
    repair=tmp_path/'repair'; val.prepare_repair(repair,root,'Do not treat mere topic mentions as endorsement.')
    before=val.read(root/'REQUESTS.json'); after=val.read(repair/'REQUESTS.json')
    assert {r['item_id'] for r in before} == {r['item_id'] for r in after}
    assert not {r['item_id'] for r in before[:100]} & {r['item_id'] for r in after[:100]}
    assert not {r['custom_id'] for r in before} & {r['custom_id'] for r in after}
    with pytest.raises(ValueError, match='one recorded'): val.prepare_repair(tmp_path/'third',repair,'again')


def test_count_freezes_blind_gold_and_only_emits_text_schema(tmp_path,monkeypatch):
    root=tmp_path/'root'; fixture(root); calls=[]
    def request(path,body=None):
        calls.append(path)
        assert (root/'GOLD_FROZEN.json').exists()
        if body is not None: assert set(json.loads(body['messages'][0]['content'])) == {'text'}
        return json.dumps({'id':val.MODEL} if body is None else {'input_tokens':100}).encode()
    monkeypatch.setattr(val,'request',request)
    plan=val.count(root,'calibration')
    assert plan['attempted'] == 100 and plan['reserved_cents'] > 0 and len(calls) == 101
    wire=val.read(root/'calibration/WIRE.json')
    assert all(set(r)=={'custom_id','params'} for r in wire['requests'])
    assert 'private-writer' not in json.dumps(wire) and 'private-prompt' not in json.dumps(wire)
    assert val.count(root,'calibration') == plan and len(calls) == 101


def test_submit_reserves_before_post_and_never_retries_unknown(tmp_path,monkeypatch):
    root=tmp_path/'root'; fixture(root); folder=root/'calibration'
    val.freeze(folder/'PLAN.json',dict(at=val.time.time(),pins={},reserved_cents=3,invocation='fixture-VAL'))
    val.freeze(folder/'WIRE.json',{'requests':[]}); calls=[]
    def reserve(*args): calls.append('reserved'); return {'reserved_cents':3}
    def request(*args): calls.append('post'); raise TimeoutError('uncertain')
    monkeypatch.setattr(val.budget,'reserve',reserve); monkeypatch.setattr(val,'request',request)
    with pytest.raises(TimeoutError): val.submit(root,'calibration')
    assert calls == ['reserved','post'] and val.read(folder/'UNKNOWN.json')['reservation_retained']
    with pytest.raises(ValueError,match='consumed'): val.submit(root,'calibration')
    assert calls == ['reserved','post']


def test_complete_replay_reconciles_only_on_explicit_owner_action(tmp_path,monkeypatch):
    root=tmp_path/'root'; rows,gold=fixture(root); folder=root/'calibration'
    val.freeze(folder/'PLAN.json',dict(pins={},invocation='fixture-VAL'))
    val.freeze(folder/'STATUS.json',dict(processing_status='ended',id='batch_fixture'))
    val.freeze(folder/'SUBMITTED.json',dict(batch_id='batch_fixture'))
    results=[dict(custom_id=g['custom_id'],result=dict(type='succeeded',message=message(g['v'],g['o']))) for g in gold]
    (folder/'RESULTS.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in results),encoding='utf8')
    called=[]; monkeypatch.setattr(val.budget,'reconcile',lambda *args:called.append(args))
    result=val.replay(root,'calibration')
    assert result['passes'] and result['valid'] == 100 and not called
    assert val.replay(root,'calibration') == result
    with pytest.raises(ValueError,match='settle'): val.selected(root,'main')
    val.reconcile(root,'calibration'); assert len(called)==1 and len(val.selected(root,'main'))==105


def test_missing_result_or_mutated_join_refuses(tmp_path):
    root=tmp_path/'root'; fixture(root); folder=root/'calibration'
    val.freeze(folder/'PLAN.json',dict(pins={}))
    val.freeze(folder/'STATUS.json',dict(processing_status='ended',id='batch_fixture'))
    val.freeze(folder/'SUBMITTED.json',dict(batch_id='batch_fixture'))
    (folder/'RESULTS.jsonl').write_text('',encoding='utf8')
    with pytest.raises(ValueError,match='coverage'): val.replay(root,'calibration')
    (root/'PRIVATE_JOIN.json').write_text('{}',encoding='utf8')
    with pytest.raises(ValueError,match='artifact'): val.check_sources(root)
