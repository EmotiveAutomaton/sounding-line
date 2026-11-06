import json,hashlib
import pytest
from runners.drive import week4_proc_prompt_h1 as p

def doc(sid,text):
 return dict(keys={'session':sid},text=text,textSha256=hashlib.sha256(text.encode()).hexdigest())

def test_complete_context_dedup_and_private_identity():
 text=''.join(f'Sentence {i}. ' for i in range(220))
 rows,links=p.rows_from_documents([doc('a',text),doc('b',text)],[dict(session='a',domain='creative'),dict(session='b',domain='creative')])
 assert len(rows)==220 and sum(map(len,links.values()))==440
 wire=json.loads(rows[100]['params']['messages'][0]['content'])
 assert wire['preceding_context']==''.join(f'Sentence {i}. ' for i in range(100))
 assert set(wire)=={'genre','roles','preceding_context','sentence'}
 assert rows[0]['params']['max_tokens']==32 and rows[0]['params']['thinking']=={'type':'disabled'}

def test_complete_message_validation():
 m=dict(model=p.MODEL,stop_reason='end_turn',content=[dict(type='text',text='{"r":2,"c":1}')])
 assert p.parse(m,'creative')=={'r':2,'c':1}
 for text in ('{"r":2,"c":true}','{"r":6,"c":1}','{"r":2,"c":1} trailing'):
  m['content'][0]['text']=text;assert p.parse(m,'creative') is None
 m['content'][0]['text']='{"r":2,"c":1}';m['stop_reason']='max_tokens';assert p.parse(m,'creative') is None

def test_kappa_known_null_and_signal():
 assert p.kappa([0,0,1,1],[0,0,1,1])==1
 assert p.kappa([0,0,1,1],[0,1,0,1])==0
 assert p.kappa([0]*4,[0]*4) is None
 assert p.kappa([0,1],[1,0])==-1

def test_submit_reserves_before_post_unknown_retained(tmp_path,monkeypatch):
 monkeypatch.setattr(p,'ROOT',tmp_path);monkeypatch.setattr(p,'check_sources',lambda:None)
 monkeypatch.setattr(p,'selected',lambda phase:[])
 folder=tmp_path/'calibration';folder.mkdir()
 p.freeze(folder/'PLAN.json',dict(at=p.time.time(),pins={},reserved_cents=3))
 p.freeze(folder/'WIRE.json',{'requests':[]});events=[]
 def reserve(*args):events.append('reserved');return {'reserved_cents':3}
 def request(*args):events.append('post');raise TimeoutError('uncertain')
 monkeypatch.setattr(p.budget,'reserve',reserve);monkeypatch.setattr(p,'request',request)
 with pytest.raises(TimeoutError):p.submit('calibration')
 assert events==['reserved','post'] and p.read(folder/'UNKNOWN.json')['reservation_retained']
 with pytest.raises(ValueError,match='consumed'):p.submit('calibration')
 assert events==['reserved','post']

def test_main_requires_calibration(tmp_path,monkeypatch):
 monkeypatch.setattr(p,'ROOT',tmp_path);p.freeze(tmp_path/'REQUESTS.json',[{'custom_id':str(i)} for i in range(110)])
 p.freeze(tmp_path/'calibration/COMPLETE.json',{'passes':False})
 with pytest.raises(ValueError,match='did not pass'):p.selected('main')

def test_gold_complete_and_typed(tmp_path,monkeypatch):
 monkeypatch.setattr(p,'ROOT',tmp_path);rows=[{'custom_id':str(i),'genre':'creative'} for i in range(100)]
 p.freeze(tmp_path/'GOLD.json',dict(provenance='agent-made blind before provider access',labels=[dict(custom_id=str(i),r=i%6,c=i%2) for i in range(100)]))
 assert len(p.gold_check(rows))==100


def test_schema_role_domains_and_ceiling():
 for genre,n in [('argumentative',8),('creative',6)]:
  q=p.params(genre,'prior','target')
  schema=q['output_config']['format']['schema']
  assert schema['properties']['r']['enum']==list(range(n))
  assert schema['properties']['c']['enum']==[0,1]
  assert schema['additionalProperties'] is False
  assert q['max_tokens']==32 and q['thinking']=={'type':'disabled'}
  assert set(json.loads(q['messages'][0]['content'])['roles'])==set(map(str,range(n)))


def test_fresh_rung_reconstructs_every_join_and_refuses_prior_content():
 rows=[];joins={}
 for i in range(320):
  q=p.params('creative','prefix',f'Sentence {i}.');key=p.digest(q)
  rows.append(dict(custom_id=key,genre='creative',params=q));joins[key]=[dict(session='PRIVATE_SESSION_SENTINEL_6ff8a2',sentence_index=i)]
 repaired,links=p.repair_rows(rows,joins,{p.content_key(r) for r in rows[:200]})
 assert len(repaired)==320 and sum(map(len,links.values()))==320
 assert [p.content_key(r) for r in repaired[:100]]==[p.content_key(r) for r in rows[200:300]]
 assert {p.content_key(r) for r in repaired}=={p.content_key(r) for r in rows}
 for r in repaired:assert 'PRIVATE_SESSION_SENTINEL_6ff8a2' not in json.dumps(r['params'])
 with pytest.raises(ValueError,match='previously exposed'):p.repair_rows(rows,joins,{p.content_key(rows[200])})


def test_prepared_payload_tamper_refuses_before_count(tmp_path,monkeypatch):
 monkeypatch.setattr(p,'ROOT',tmp_path)
 p.freeze(tmp_path/'REQUESTS.json',[{'original':True}]);p.freeze(tmp_path/'SOURCE.json',dict(pins={},artifact_hashes={'REQUESTS.json':p.filehash(tmp_path/'REQUESTS.json')}))
 p.check_sources();(tmp_path/'REQUESTS.json').write_text('[]')
 monkeypatch.setattr(p,'request',lambda *a:(_ for _ in ()).throw(AssertionError('unexpected network')))
 with pytest.raises(ValueError,match='artifact changed'):p.count('calibration')


def fake_complete(tmp_path,monkeypatch,bad=0):
 monkeypatch.setattr(p,'ROOT',tmp_path);monkeypatch.setattr(p,'check_sources',lambda:None)
 rows=[dict(custom_id=str(i),genre='creative') for i in range(100)]
 p.freeze(tmp_path/'REQUESTS.json',rows)
 p.freeze(tmp_path/'GOLD.json',dict(provenance='agent-made blind before provider access',labels=[dict(custom_id=str(i),r=i%6,c=i%2) for i in range(100)]))
 folder=tmp_path/'calibration';p.freeze(folder/'PLAN.json',dict(pins={str(tmp_path/'GOLD.json'):p.filehash(tmp_path/'GOLD.json')}))
 p.freeze(folder/'STATUS.json',dict(processing_status='ended',id='synthetic'))
 p.freeze(folder/'SUBMITTED.json',dict(batch_id='synthetic'))
 results=[]
 for i in range(100):
  message=dict(model=p.MODEL,stop_reason='end_turn',content=[dict(type='text',text=json.dumps(dict(r=i%6,c=i%2)) if i>=bad else 'invalid')],usage=dict(input_tokens=20,output_tokens=8))
  results.append(dict(custom_id=str(i),result=dict(type='succeeded',message=message)))
 (folder/'RESULTS.jsonl').write_text('\n'.join(json.dumps(x) for x in results),encoding='utf8')
 return folder


def test_complete_calibration_replay_reentry_and_gold_binding(tmp_path,monkeypatch):
 folder=fake_complete(tmp_path,monkeypatch);settlements=[]
 monkeypatch.setattr(p.budget,'reconcile',lambda *a:settlements.append(a))
 result=p.replay('calibration');assert result['passes'] and result['valid']==100
 assert result['role_kappa']==result['centrality_kappa']==1
 monkeypatch.setattr(p,'request',lambda *a:(_ for _ in ()).throw(AssertionError('unexpected network')))
 assert p.retrieve('calibration')==result and len(settlements)==1
 (tmp_path/'GOLD.json').write_text('{}')
 with pytest.raises(ValueError,match='binding changed'):p.replay('calibration')


@pytest.mark.parametrize('bad,passes',[(2,True),(3,False)])
def test_actual_format_floor_handler(tmp_path,monkeypatch,bad,passes):
 fake_complete(tmp_path,monkeypatch,bad);monkeypatch.setattr(p.budget,'reconcile',lambda *a:None)
 result=p.replay('calibration');assert result['valid']==100-bad and result['passes']==passes


def test_full_response_coverage_required(tmp_path,monkeypatch):
 folder=fake_complete(tmp_path,monkeypatch)
 data=(folder/'RESULTS.jsonl').read_text().splitlines();(folder/'RESULTS.jsonl').write_text('\n'.join(data[:-1]))
 with pytest.raises(ValueError,match='full result coverage'):p.replay('calibration')
