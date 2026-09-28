from contextlib import contextmanager
from copy import deepcopy
import json
import sysconfig
import pytest
from runners.stage13 import development_repair as repair, worker, gpu, dispatch
from runners.stage13.common import freeze, read
from runners.stage13.reconstruction import admission_fixture, model_fit, predict


def test_corrected_fixture_does_not_change_reader_evidence():
    old=admission_fixture(); new=repair.fixture(old)
    assert new['views']['D']==old['views']['D']
    assert new['target']==old['target']
    assert 'A' not in old['views']
    req=repair.request(new['views']['D'],'direct')
    assert 'summing to 1' in req['messages'][1]['content']
    assert req['options']==gpu.request(old['views']['D'],'direct')['options']
    assert req['format']==gpu.schema()
    assert len(req['messages'][1]['content'].encode('utf-8'))<=5300


@pytest.mark.parametrize('valid',[True,False])
def test_actual_handler_valid_and_invalid(tmp_path,monkeypatch,valid):
    r=repair.fixture(admission_fixture()); r['writer']='fixture'; freeze(tmp_path/'rows.json',[r])
    pred,_=predict(r['views']['D'],model_fit([r]),'observed-extraction')
    pred.pop('attributes'); pred.update(goal_support=[.5]*4,unknown_history=.2)
    if not valid:pred['handling']=[0,1,2,3]
    response=dict(done=True,done_reason='stop',prompt_eval_count=500,eval_count=1000,message=dict(content=json.dumps(pred)))
    @contextmanager
    def service(*a):yield {}
    monkeypatch.setattr(gpu,'service',service)
    calls=[]
    def call(e,arm,*a):
        calls.append(gpu.request(e,arm))
        try:p=gpu.parse(response,len(e['endpoint']))
        except ValueError:p=None
        return dict(parsed=p)
    monkeypatch.setattr(gpu,'call',call)
    original=gpu.request
    card=dict(action='qwen-development-repair',args=dict(rows='rows.json',views=['D'],arms=['direct']))
    result=worker.handle(card,tmp_path/'out',tmp_path,lambda:None)
    assert read(tmp_path/'out/ADMISSION.json')['admitted'] is valid
    assert len(calls)==1 and gpu.request is original
    if not valid:assert result['rows'][0]['scores']['handling']['brier']==2


def test_per_card_capsules_preserve_existing_workers(tmp_path):
    plan=dict(source_capsule='original',source_capsules={'new':'corrected'},python_site_packages=sysconfig.get_paths()['purelib'])
    assert repr(str(tmp_path/'original')) in dispatch.worker_command(dict(id='old'),plan,tmp_path)[3]
    assert repr(str(tmp_path/'corrected')) in dispatch.worker_command(dict(id='new'),plan,tmp_path)[3]


def test_development_and_payload_refusals(monkeypatch):
    with pytest.raises(ValueError,match='development-only'):repair.realization([],[],None)
    r=repair.fixture(admission_fixture());r['partition']='reserve'
    with pytest.raises(ValueError,match='development-only'):repair.realization([r],[],None)
    class CharTokenizer:
        def encode(self,s,**kw):return list(s)
        def decode(self,t):return ''.join(t)
    t=deepcopy(r);t['key']='train';t['unit']='train';t['views']['A']['endpoint']='long endpoint'
    monkeypatch.setattr(repair,'_original_intervention',lambda *a:('old',['train']))
    with pytest.raises(ValueError,match='100-token'):repair.memory(CharTokenizer(),r,[t],'linked-memory')


def test_collapsed_treatment_is_not_admitted(monkeypatch):
    r=repair.fixture(admission_fixture());r['partition']='development';r['views']['C']=r['views']['D']
    class Tokenizer:
        def encode(self,s,**kw):return list(s)
        def decode(self,t):return ''.join(t)
    monkeypatch.setattr(repair,'memory',lambda *a:('same',[]))
    result=repair.realization([r],[],Tokenizer())
    assert result['admitted'] is False
    assert any('treatment meaning' in e['error'] for e in result['errors'])


def test_repaired_context_is_in_report_replay(tmp_path):
    from runners.stage13.report import semantic_replay
    freeze(tmp_path/'PREDICTIONS.json',dict(rows=[dict(probabilities=[1.,0.],truth=0,scores={'wrong':True})]))
    with pytest.raises(ValueError,match='proper-score replay'):
        semantic_replay(dict(action='memory-development-batch'),tmp_path,tmp_path)
