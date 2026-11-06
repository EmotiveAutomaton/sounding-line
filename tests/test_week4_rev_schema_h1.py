import json
from collections import Counter
import pytest
from runners.drive import week4_rev_schema_h1 as p
from runners.drive import week4_rev_schema_h1_monitor as monitor


def message(value,stop='end_turn'):
    return dict(model=p.MODEL,stop_reason=stop,content=[dict(type='text',text=json.dumps(value))],
                usage=dict(input_tokens=100,output_tokens=20))


def row(kind,text='First sentence. Second sentence.'):
    q=p.params(kind,text)
    return dict(kind=kind,text=text,custom_id=p.digest(q),params=q)


@pytest.mark.parametrize('kind,valid,invalid',[
    ('piece',{'g':[]},[{'g':['G01','G01']},{'g':['G13']},{'g':['G01','G02','G03']},{'g':None},{'g':[True]},{'g':[],'extra':0}]),
    ('document',{'s':[[0,9,0],[9,0,9]]},[{'s':[[0,0,0]]},{'s':[[0,0,0],[0,0,10]]},{'s':[[True,0,0],[0,0,0]]},{'s':[[0,0],[0,0,0]]},{'s':[[0.,0,0],[0,0,0]]}]),
])
def test_complete_messages(kind,valid,invalid):
    r=row(kind)
    assert p.parse(message(valid),r)==valid
    for value in invalid:assert p.parse(message(value),r) is None
    assert p.parse(message(valid,'max_tokens'),r) is None
    m=message(valid);m['content'][0]['text']+=' extra'
    assert p.parse(m,r) is None
    m=message(valid);m['content'].append(dict(type='thinking',thinking='private'))
    assert p.parse(m,r) is None
    m=message(valid);m['model']='other'
    assert p.parse(m,r) is None
    m=message(valid);m['content'][0]['text']='{"g":[],"g":["G01"]}'
    assert p.parse(m,r) is None


def test_source_projection_and_fresh_disjoint_selection():
    text='  A\U0001f642 sentence.\n\nNext \u00e9 sentence!  '
    assert ''.join(r['text'] for r in p.numbered(text))==text
    docs=[('d'+str(i),text+str(i)) for i in range(110)]
    pieces=[('p'+str(i),'Piece '+str(i)) for i in range(600)]
    rows,joins,banks=p.build_bank(docs,pieces)
    assert len(rows)==710 and sum(map(len,joins.values()))==710
    assert len(set(banks['calibration'])&set(banks['fresh_correction']))==0
    assert p.build_bank(list(reversed(docs)),list(reversed(pieces)))==(rows,joins,banks)
    for r in rows:
        payload=json.loads(r['params']['messages'][0]['content'])
        if r['kind']=='piece':
            assert set(payload)=={'piece','goal_library'} and payload['goal_library']==p.GOALS
            assert r['params']['max_tokens']==32
        else:
            assert set(payload)=={'sentences'} and ''.join(s['text'] for s in payload['sentences'])==r['text']
            assert r['params']['max_tokens']==10*len(payload['sentences'])+20
    # Deduplicate provider payloads while preserving every original source join.
    r2,j2,b2=p.build_bank(docs+[('duplicate',docs[0][1])],pieces)
    assert r2==rows and b2==banks and sum(map(len,j2.values()))==711


def setup(tmp_path,monkeypatch,invalid=(),missing=False):
    monkeypatch.setattr(p,'ROOT',tmp_path)
    monkeypatch.setattr(p,'check_sources',lambda:None)
    rows,joins,banks=p.build_bank([('d'+str(i),'Document '+str(i)+'.') for i in range(110)],
        [('p'+str(i),'Piece '+str(i)) for i in range(600)])
    p.freeze(tmp_path/'REQUESTS.json',rows);p.freeze(tmp_path/'SELECTION.json',banks)
    p.freeze(tmp_path/'SOURCE.json',dict(fixture=True))
    selected=p.selected(p.PHASE);events=[]
    def reserve(*args):
        assert args[1]=='REV';events.append('reserve');return dict(fixture=True)
    monkeypatch.setattr(p.budget,'reserve',reserve)
    monkeypatch.setattr(p.budget,'reconcile',lambda *a:events.append('reconcile'))
    def request(path,payload=None):
        events.append(path)
        if path.startswith('/v1/models/'):return json.dumps(dict(id=p.MODEL)).encode()
        if path.endswith('count_tokens'):return b'{"input_tokens":100}'
        if path.endswith('/batches'):
            assert events[-2]=='reserve' and len(payload['requests'])==100
            return b'{"id":"msgbatch_fixture"}'
        if path.endswith('/results'):
            results=[]
            for i,r in enumerate(selected[:99] if missing else selected):
                value={'g':[]} if r['kind']=='piece' else {'s':[[0,0,0] for _ in p.numbered(r['text'])]}
                results.append(dict(custom_id=r['custom_id'],result=dict(type='succeeded',message=message(value,'max_tokens' if i in invalid else 'end_turn'))))
            return '\n'.join(json.dumps(x) for x in results).encode()
        return b'{"id":"msgbatch_fixture","processing_status":"ended"}'
    monkeypatch.setattr(p,'request',request)
    return events


@pytest.mark.parametrize('invalid,passes',[((),True),((0,1),True),((0,2),False),((0,1,2),False)])
def test_actual_handlers_and_interface_floors(tmp_path,monkeypatch,invalid,passes):
    events=setup(tmp_path,monkeypatch,invalid)
    assert p.count(p.PHASE)['attempted']==100
    p.submit(p.PHASE)
    folder=tmp_path/p.PHASE;p.freeze(folder/'MONITOR_PLAN.json',dict(pins={}))
    monitor.run();receipt=p.read(folder/'COMPLETE.json')
    assert receipt['format_passes']==passes and receipt['valid']==100-len(invalid)
    assert not receipt['accuracy_computed'] and not receipt['scientific_admission']
    assert events[-1]=='reconcile'
    n=len(events);assert p.retrieve(p.PHASE)==receipt and len(events)==n
    assert p.replay(p.PHASE)==receipt
    with pytest.raises(ValueError,match='consumed'):p.submit(p.PHASE)
    with pytest.raises(ValueError,match='only initial'):p.selected('main')


def test_missing_coverage_no_receipt(tmp_path,monkeypatch):
    events=setup(tmp_path,monkeypatch,missing=True);p.count(p.PHASE);p.submit(p.PHASE)
    with pytest.raises(ValueError,match='coverage'):p.retrieve(p.PHASE)
    assert 'reconcile' not in events and not (tmp_path/p.PHASE/'COMPLETE.json').exists()


def test_unknown_delivery_no_retry(tmp_path,monkeypatch):
    events=setup(tmp_path,monkeypatch);p.count(p.PHASE)
    monkeypatch.setattr(p,'request',lambda *args:(_ for _ in ()).throw(TimeoutError('unknown')))
    with pytest.raises(TimeoutError):p.submit(p.PHASE)
    with pytest.raises(ValueError,match='consumed'):p.submit(p.PHASE)
    assert (tmp_path/p.PHASE/'UNKNOWN.json').exists()


def test_counted_wire_mutation_before_reservation(tmp_path,monkeypatch):
    events=setup(tmp_path,monkeypatch);p.count(p.PHASE)
    path=tmp_path/p.PHASE/'WIRE.json';wire=p.read(path);wire['requests'][0]['params']['max_tokens']=999
    p.atomic(path,wire)
    with pytest.raises(ValueError):p.submit(p.PHASE)
    assert 'reserve' not in events


def test_actual_dependency_and_false_landing(tmp_path,monkeypatch):
    p.admitted()
    landing=p.read(p.LANDING);landing['pieces_sha256']='0'*64
    path=tmp_path/'bad-landing.json';p.freeze(path,landing);monkeypatch.setattr(p,'LANDING',path)
    with pytest.raises(ValueError,match='binding'):p.admitted()


def test_actual_source_rebuild_and_mutation(tmp_path,monkeypatch):
    monkeypatch.setattr(p,'ROOT',tmp_path/'prepared')
    result=p.prepare();p.check_sources()
    assert result['source_pieces']==600 and result['source_documents']==1399
    assert Counter(r['kind'] for r in p.selected(p.PHASE))==dict(piece=50,document=50)
    rows,joins,banks=p.rebuild()
    assert rows==p.read(p.ROOT/'REQUESTS.json') and joins==p.read(p.ROOT/'PRIVATE_JOIN.json') and banks==p.read(p.ROOT/'SELECTION.json')
    rows[0]['text']+=' changed';p.atomic(p.ROOT/'REQUESTS.json',rows)
    with pytest.raises(ValueError,match='bank changed'):p.check_sources()


def test_same_prompt_payload_and_evidence_selection():
    original_rows=p.original.selected(p.PHASE)
    rows,_,banks=p.rebuild();by={r['custom_id']:r for r in rows}
    current=[by[k] for k in banks['calibration']]
    assert [(r['kind'],r['text']) for r in current]==[(r['kind'],r['text']) for r in original_rows]
    for a,b in zip(original_rows,current):
        assert {k:v for k,v in a['params'].items() if k!='output_config'}=={k:v for k,v in b['params'].items() if k!='output_config'}
        schema=b['params']['output_config']['format']['schema']
        def check(x):
            if isinstance(x,dict):
                assert not {'minItems','maxItems','minimum','maximum'}&set(x)
                for value in x.values():check(value)
            elif isinstance(x,list):
                for value in x:check(value)
        check(schema)
