import json,hashlib
import pytest
from runners.drive import week3_proc as p

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
