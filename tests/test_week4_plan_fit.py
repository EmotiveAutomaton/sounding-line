import copy
import json
import pytest
from runners.drive import week4_plan_fit as p
from runners.drive import week4_plan_fit_monitor as monitor


def population():
    sessions=[]; plans={}; joins={}
    for i in range(30):
        key='proposal-'+str(i);sid='private-session-'+str(i)
        plans[key]={k:f'Direction {i} {k}' for k in p.KEYS};joins[key]=[sid]
        sessions.append(dict(session=sid,writer='PRIVATE_WRITER',private_choices=['PRIVATE_CHOICE'],
            provider_text_only=dict(midpoint_text='UNSENT_MIDPOINT',later_options=[[f'Option {i} {j}' for j in range(n)] for n in [1,3,5]])))
    return sessions,plans,joins


def test_selection_is_deduplicated_rebuildable_choice_blind():
    s,plans,joins=population();answer=p.build_selection(s,plans,joins)
    rows,pairs,bindings,support=answer
    assert len(pairs)==len({x['id'] for x in pairs})==100
    assert support['unique_menus']==90 and support['unique_pairs']==750
    s.reverse()
    for x in s:x['private_choices']=[1000];x['writer']='OTHER';x['provider_text_only']['midpoint_text']='OTHER'
    assert p.build_selection(s,plans,joins)==answer
    wire=json.dumps(rows)
    assert all(t not in wire for t in ['PRIVATE_WRITER','PRIVATE_CHOICE','UNSENT_MIDPOINT','private-session-'])
    assert all(r['params']['max_tokens']==120 for r in rows)
    assert set(bindings)=={r['custom_id'] for r in rows}
    s.append(s[0])
    with pytest.raises(ValueError,match='duplicate'):p.build_selection(s,plans,joins)
    with pytest.raises(ValueError,match='100 distinct'):p.build_selection(*([population()[0][0]],{'proposal-0':plans['proposal-0']},{'proposal-0':joins['proposal-0']}))


def message(n=5,rating=3):
    return dict(model=p.MODEL,stop_reason='end_turn',content=[dict(type='text',text=json.dumps({k:[rating]*n for k in p.KEYS}))],usage=dict(input_tokens=100,output_tokens=100))


@pytest.mark.parametrize('kind',['model','stop','block','missing','extra','row_length','float','bool','low','high','suffix','duplicate'])
def test_complete_matrix_refusal(kind):
    m=message();assert p.parse(m,5) is not None
    v=json.loads(m['content'][0]['text'])
    if kind=='model':m['model']='other'
    if kind=='stop':m['stop_reason']='max_tokens'
    if kind=='block':m['content'].append(dict(type='tool_use'))
    if kind=='missing':del v['p4']
    if kind=='extra':v['p5']=[3]*5
    if kind=='row_length':v['p0'].pop()
    if kind=='float':v['p0'][0]=3.0
    if kind=='bool':v['p0'][0]=True
    if kind=='low':v['p0'][0]=0
    if kind=='high':v['p0'][0]=6
    m['content'][0]['text']=json.dumps(v)
    if kind=='suffix':m['content'][0]['text']+=' trailing'
    if kind=='duplicate':m['content'][0]['text']=m['content'][0]['text'][:-1]+',"p0":[3,3,3,3,3]}'
    assert p.parse(m,5) is None


def fixture(tmp_path,monkeypatch):
    monkeypatch.setattr(p,'ROOT',tmp_path);monkeypatch.setattr(p,'check_sources',lambda:None)
    rows=[];pairs=[];blind={};ratings={}
    for i in range(100):
        plans={k:f'Plan {i} {k}' for k in p.KEYS};options=[f'Option {i} {j}' for j in range(5)]
        q=p.params(plans,options);rid=p.digest(q);content=dict(plan=plans['p0'],option=options[0]);key=p.digest(content)
        rows.append(dict(custom_id=rid,params=q));pairs.append(dict(id=key,request_id=rid,plan_key='p0',option_index=0,**content))
        rating=[1,3,5][i%3];blind[key]=dict(rating=rating,rationale='Constructed reference');ratings[rid]=rating
    p.freeze(tmp_path/'REQUESTS.json',rows);p.freeze(tmp_path/'PAIRS.json',pairs)
    p.freeze(tmp_path/'SOURCE.json',{'fixture':True});p.freeze(tmp_path/'BLIND_ITEMS.json',[{k:x[k] for k in ('id','plan','option')} for x in pairs])
    p.freeze(tmp_path/'BLIND_LABELS.json',dict(labeler='operating agent',provider_ratings_unseen=True,blind_items_sha256=p.filehash(tmp_path/'BLIND_ITEMS.json'),labels=blind))
    calls=[]
    def reserve(*args):calls.append('reserve');return {'fixture':True}
    def reconcile(*args):calls.append('reconcile')
    monkeypatch.setattr(p.budget,'reserve',reserve);monkeypatch.setattr(p.budget,'reconcile',reconcile)
    def request(path,payload=None):
        calls.append(path)
        if '/models/' in path:return json.dumps(dict(id=p.MODEL)).encode()
        if path.endswith('count_tokens'):return b'{"input_tokens":100}'
        if path.endswith('/batches'):
            assert calls[-2]=='reserve';assert len(payload['requests'])==100
            return b'{"id":"msgbatch_fixture"}'
        if path.endswith('/results'):
            return '\n'.join(json.dumps(dict(custom_id=r['custom_id'],result=dict(type='succeeded',message=message(rating=ratings[r['custom_id']])))) for r in rows).encode()
        return b'{"id":"msgbatch_fixture","processing_status":"ended"}'
    monkeypatch.setattr(p,'request',request)
    return calls


def test_whole_transport_monitor_settlement_and_reentry(tmp_path,monkeypatch):
    calls=fixture(tmp_path,monkeypatch);plan=p.count(p.PHASE)
    n=len(calls);assert p.count(p.PHASE)==plan and len(calls)==n
    p.submit(p.PHASE);p.freeze(tmp_path/p.PHASE/'MONITOR_PLAN.json',dict(pins={}))
    monitor.run();result=p.read(tmp_path/p.PHASE/'COMPLETE.json')
    assert result['valid_menus']==result['valid_pairs']==100 and result['kappa']==1 and result['node_calibration_complete']
    assert not result['main_admission'] and not result['scientific_admission'] and result['prompt_corrections_remaining']==0
    assert calls[-1]=='reconcile'
    before=len(calls);assert p.retrieve(p.PHASE)==result and len(calls)==before
    assert p.replay(p.PHASE)==result
    with pytest.raises(ValueError,match='consumed'):p.submit(p.PHASE)
    with pytest.raises(ValueError,match='blocked'):p.selected('main')


@pytest.mark.parametrize('mutation',['blind','wire','pairs'])
def test_admission_mutation_before_reserve(tmp_path,monkeypatch,mutation):
    calls=fixture(tmp_path,monkeypatch);p.count(p.PHASE)
    if mutation=='blind':
        path=tmp_path/'BLIND_LABELS.json';v=p.read(path);next(iter(v['labels'].values()))['rating']=2
    elif mutation=='wire':
        path=tmp_path/p.PHASE/'WIRE.json';v=p.read(path);v['requests'][0]['params']['max_tokens']=121
    else:
        path=tmp_path/'PAIRS.json';v=p.read(path);v[0]['option']='changed'
    p.atomic(path,v)
    with pytest.raises(ValueError):p.submit(p.PHASE)
    assert 'reserve' not in calls


def test_unknown_retains_reservation_and_never_retries(tmp_path,monkeypatch):
    calls=fixture(tmp_path,monkeypatch);p.count(p.PHASE)
    def unknown(*args):raise TimeoutError('uncertain')
    monkeypatch.setattr(p,'request',unknown)
    with pytest.raises(TimeoutError):p.submit(p.PHASE)
    with pytest.raises(ValueError,match='consumed'):p.submit(p.PHASE)
    p.freeze(tmp_path/p.PHASE/'MONITOR_PLAN.json',dict(pins={}))
    with pytest.raises(RuntimeError,match='unknown'):monitor.run()
    assert calls.count('reserve')==1


def test_agreement_known_answers_and_whole_matrix_loss(tmp_path,monkeypatch):
    fixture(tmp_path,monkeypatch);pairs=p.read(tmp_path/'PAIRS.json');blind=p.blind_labels()
    matrices={x['request_id']:{k:[blind[x['id']]['rating']]*5 for k in p.KEYS} for x in pairs}
    assert p.agreement(pairs,blind,matrices)['kappa']==1
    swapped={rid:{k:[6-v for v in row] for k,row in m.items()} for rid,m in matrices.items()}
    assert p.agreement(pairs,blind,swapped)['kappa']<0
    for x in pairs[:2]:del matrices[x['request_id']]
    assert p.agreement(pairs,blind,matrices)['passes']
    del matrices[pairs[2]['request_id']]
    assert not p.agreement(pairs,blind,matrices)['passes']
    for value in blind.values():value['rating']=3
    constant={x['request_id']:{k:[3]*5 for k in p.KEYS} for x in pairs}
    assert p.agreement(pairs,blind,constant)['kappa'] is None
    assert not p.agreement(pairs,blind,constant)['passes']


def test_full_coverage_and_post_submission_label_mutation(tmp_path,monkeypatch):
    fixture(tmp_path,monkeypatch);p.count(p.PHASE);p.submit(p.PHASE);p.retrieve(p.PHASE)
    folder=tmp_path/p.PHASE;raw=(folder/'RESULTS.jsonl').read_text().splitlines()
    (folder/'RESULTS.jsonl').write_text('\n'.join(raw[:-1]))
    with pytest.raises(ValueError,match='coverage'):p.replay(p.PHASE)
    (folder/'RESULTS.jsonl').write_text('\n'.join(raw))
    path=tmp_path/'BLIND_LABELS.json';v=p.read(path);next(iter(v['labels'].values()))['rating']=2;p.atomic(path,v)
    with pytest.raises(ValueError,match='blind labels changed'):p.replay(p.PHASE)
