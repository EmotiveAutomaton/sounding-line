import copy
import json
import pytest
from runners.drive import week4_val_prompt_h1 as val


def inputs():
    rows=[dict(writer=f'w{w:02}',conversation=f'c{w}-{j}',turn=j,prompt='p',half=j%2,
               explanation=f'Constructed explanation {w} {j}') for w in range(25) for j in range(12)]
    people=sorted({r['writer'] for r in rows})
    chosen,census=val.choice_sample(rows,people)
    # An out-of-scope duplicate shares text; its private link must not survive.
    chosen.append(dict(text=chosen[0]['text'],link=dict(kind='argumentative-typed',writer='private-outsider')))
    items,joins=val.deduplicate(chosen)
    return items,joins,dict(choice=census),dict(selected=people,mandatory=people[:20]),rows


def fixture(tmp_path,monkeypatch):
    root=tmp_path/'val';monkeypatch.setattr(val,'ROOT',root)
    items,joins,population=val.restricted(*inputs());rows=val.original.requests_for(items,1,val.CORRECTION)
    for name,value in [('REQUESTS.json',rows),('PRIVATE_JOIN.json',joins),('PRIVATE_POPULATION.json',population),
                       ('SELECTION.json',dict(calibration=[r['custom_id'] for r in rows[:100]],fresh=[r['custom_id'] for r in rows[100:200]]))]:
        val.freeze(root/name,value)
    val.freeze(root/'SOURCE.json',dict(pins={},prepared={n:val.filehash(root/n) for n in ['REQUESTS.json','PRIVATE_JOIN.json','PRIVATE_POPULATION.json','SELECTION.json']}))
    gold=[dict(custom_id=r['custom_id'],v=('1' if i%2 else '0')*10,o=i%2,rationale='Constructed known answer') for i,r in enumerate(rows[:100])]
    val.freeze(root/'GOLD.json',dict(provenance='agent-made blind before provider access',labels=gold))
    def request(path,body=None):
        assert (root/'GOLD_FROZEN.json').exists()
        if body is not None:assert set(json.loads(body['messages'][0]['content']))=={'text'}
        return json.dumps({'id':val.MODEL} if body is None else {'input_tokens':150}).encode()
    monkeypatch.setattr(val,'request',request);val.count('calibration')
    return root,rows[:100],gold


def message(v,o):
    return dict(model=val.MODEL,stop_reason='end_turn',content=[dict(type='text',text=json.dumps(dict(v=v,o=o)))],usage=dict(input_tokens=150,output_tokens=20))


def results(root,gold,invalid=0):
    f=root/'calibration';val.freeze(f/'SUBMITTED.json',dict(batch_id='msgbatch_fixture'))
    val.freeze(f/'STATUS.json',dict(id='msgbatch_fixture',processing_status='ended'))
    rows=[dict(custom_id=g['custom_id'],result=dict(type='succeeded',message=message(g['v'],g['o']))) for g in gold]
    for r in rows[:invalid]:r['result']['message']['stop_reason']='max_tokens'
    (f/'RESULTS.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in rows),encoding='utf8')
    return rows


def test_restriction_rebuild_excludes_foreign_and_typed_links():
    items,joins,population=val.restricted(*inputs())
    assert len(items)==250 and all(j['kind']=='choice-explanation' for v in joins.values() for j in v)
    assert len(population['choice'])==25 and all(c['selected_explanations']==10 for c in population['choice'])


@pytest.mark.parametrize('defect',['text','join','census','missing','duplicate'])
def test_source_defects_refuse(defect):
    args=list(inputs())
    if defect=='text':args[0][0]['text']='altered'
    elif defect=='join':args[1][args[0][0]['item_id']][0]['half']=7
    elif defect=='census':args[2]['choice'][0]['selected_explanations']=9
    elif defect=='missing':args[0].pop()
    else:args[4].append(args[4][0])
    with pytest.raises(ValueError):val.restricted(*args)


def test_wire_blindness_idempotence_and_main_refusal(tmp_path,monkeypatch):
    root,rows,gold=fixture(tmp_path,monkeypatch)
    def no_call(*args):raise AssertionError('preflight should be reused')
    monkeypatch.setattr(val,'request',no_call);plan=val.count('calibration')
    wire=val.read(root/'calibration/WIRE.json')
    assert plan['attempted']==100 and 'private-outsider' not in json.dumps(wire)
    assert all(set(r)=={'custom_id','params'} and r['params']['max_tokens']==32 and 'tools' not in r['params'] for r in wire['requests'])
    with pytest.raises(ValueError,match='only fresh'):val.selected('main')
    (root/'GOLD.json').write_text('{}',encoding='utf8')
    with pytest.raises(ValueError):val.preflight('calibration')


def test_known_null_swapped_exact_and_abstention(tmp_path,monkeypatch):
    root,_,gold=fixture(tmp_path,monkeypatch)
    labels={g['custom_id']:{k:g[k] for k in ['v','o']} for g in gold}
    assert val.agreement(gold,labels)['pooled_kappa']==1
    const={k:dict(v='0'*10,o=0) for k in labels}
    assert val.agreement(gold,const)['pooled_kappa']==0
    swapped={k:dict(v=''.join(str(1-int(b)) for b in v['v']),o=1-v['o']) for k,v in labels.items()}
    assert val.agreement(gold,swapped)['pooled_kappa']==-1
    labels.pop(gold[0]['custom_id']);r=val.agreement(gold,labels)
    assert r['denominator']==1100 and r['pooled_kappa']<1 and r['per_category']['power']['invalid']==1
    zeros=[dict(g,v='0'*10,o=0) for g in gold]
    assert not val.agreement(zeros,const)['agreement_passes']


@pytest.mark.parametrize('invalid,passes',[(0,True),(2,True),(3,False)])
def test_complete_transport_floor_billing_and_reentry(tmp_path,monkeypatch,invalid,passes):
    root,_,gold=fixture(tmp_path,monkeypatch);results(root,gold,invalid)
    calls=[];monkeypatch.setattr(val.budget,'reconcile',lambda *args:calls.append(args))
    r=val.replay('calibration')
    assert r['passes']==passes and r['valid']==100-invalid and r['denominator']==1100
    assert r['tokens']==dict(input_tokens=15000,output_tokens=2000) and r['measured_token_cents']==1
    assert (root/'calibration/RECONCILED.json').exists() and calls
    assert val.replay('calibration')==r
    assert val.retrieve('calibration')==r


def test_missing_or_duplicate_provider_row_refuses(tmp_path,monkeypatch):
    root,_,gold=fixture(tmp_path,monkeypatch);rs=results(root,gold)
    rs[-1]=rs[0]
    (root/'calibration/RESULTS.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in rs),encoding='utf8')
    with pytest.raises(ValueError,match='coverage'):val.replay('calibration')
    assert not (root/'calibration/COMPLETE.json').exists()


def test_reservation_before_post_and_uncertain_no_retry(tmp_path,monkeypatch):
    root,_,_=fixture(tmp_path,monkeypatch);calls=[]
    def reserve(*args):calls.append('reserve');return dict(reserved_cents=3)
    def fail(*args):calls.append('post');raise TimeoutError('uncertain')
    monkeypatch.setattr(val.budget,'reserve',reserve);monkeypatch.setattr(val,'request',fail)
    with pytest.raises(TimeoutError):val.submit('calibration')
    with pytest.raises(ValueError,match='consumed'):val.submit('calibration')
    assert calls==['reserve','post'] and val.read(root/'calibration/UNKNOWN.json')['reservation_retained']


def test_real_submit_retrieve_handlers(tmp_path,monkeypatch):
    root,_,gold=fixture(tmp_path,monkeypatch);calls=[]
    monkeypatch.setattr(val.budget,'reserve',lambda *args:dict(reserved_cents=3))
    monkeypatch.setattr(val.budget,'reconcile',lambda *args:calls.append('settled'))
    rs=[dict(custom_id=g['custom_id'],result=dict(type='succeeded',message=message(g['v'],g['o']))) for g in gold]
    def request(path,body=None):
        if body is not None:
            assert (root/'calibration/RESERVATION.json').exists()
            return b'{"id":"msgbatch_fixture"}'
        if path.endswith('/results'):return ('\n'.join(json.dumps(r) for r in rs)).encode()
        return b'{"id":"msgbatch_fixture","processing_status":"ended"}'
    monkeypatch.setattr(val,'request',request)
    assert val.submit('calibration')['status']=='SUBMITTED'
    assert val.retrieve('calibration')['passes'] and calls==['settled']


def test_unknown_usage_keeps_reservation(tmp_path,monkeypatch):
    root,_,gold=fixture(tmp_path,monkeypatch);rs=results(root,gold)
    rs[0]['result']=dict(type='errored',error=dict(type='fixture'))
    (root/'calibration/RESULTS.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in rs),encoding='utf8')
    monkeypatch.setattr(val.budget,'reconcile',lambda *args:pytest.fail('must retain reservation'))
    r=val.replay('calibration')
    assert not r['usage_complete'] and not (root/'calibration/RECONCILED.json').exists()


def test_actual_source_exact_rebuild():
    (items,joins,population),paths=val.rebuild()
    assert len(population['membership']['mandatory'])==836 and len(population['choice'])==1036
    assert len(items)>=200 and all(j['kind']=='choice-explanation' for v in joins.values() for j in v)
    assert paths


def test_fresh_selection_is_exact_and_refuses_changed_parent():
    items,_,_=val.restricted(*inputs());old=val.original.requests_for(items,0)
    selection=dict(calibration=[r['custom_id'] for r in old[:100]],fresh=[r['custom_id'] for r in old[100:200]])
    fresh=val.fresh_items(items,old,selection)
    assert fresh[:100]==items[100:200] and fresh[100:200]==items[:100] and fresh[200:]==items[200:]
    assert set(i['item_id'] for i in fresh[:100]).isdisjoint(i['item_id'] for i in items[:100])
    selection['fresh'][0]=selection['calibration'][0]
    with pytest.raises(ValueError,match='fresh selection'):val.fresh_items(items,old,selection)


def test_actual_parent_admission_and_unchanged_interface(monkeypatch,tmp_path):
    paths=val.parent_check();assert paths
    for j,name in enumerate(val.VALUES):
        bits='0'*j+'1'+'0'*(9-j)
        assert name+'='+bits in val.CORRECTION
    p=val.original.params('Constructed explanation',val.CORRECTION)
    old=val.original.params('Constructed explanation')
    assert {k:v for k,v in p.items() if k!='system'}=={k:v for k,v in old.items() if k!='system'}
    assert p['system'].startswith(old['system'])
    bad=tmp_path/'wrong.json';value=val.read(val.PARENT_LANDING);value['complete_sha256']='wrong';val.freeze(bad,value)
    monkeypatch.setattr(val,'PARENT_LANDING',bad)
    with pytest.raises(ValueError,match='exact first'):val.parent_check()
