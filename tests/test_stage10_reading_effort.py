from contextlib import nullcontext
from pathlib import Path
import json
import pytest
from runners.stage10 import reading_effort as bank, ollama
from runners.stage10.queue import read


def test_native_reserved_reading_chain_budget_replay_and_phase_boundary(tmp_path,monkeypatch):
    prepared=Path('results/phase_2_4_stage_10/raw/reading-screen-v1')
    if not prepared.exists():pytest.skip('private reviewed native source unavailable')
    original=ollama.request_for;calls=[]
    def device(output,replay):
        output.mkdir(parents=True,exist_ok=True)
        return nullcontext()
    monkeypatch.setattr(bank,'device',device)
    monkeypatch.setattr(ollama,'identity',lambda:{'model':ollama.MODEL,'digest':ollama.MODEL_DIGEST})
    def api(path,request=None,**kwargs):
        assert path=='/api/chat';calls.append(request)
        fields=request['format']['properties'];keys=fields['choice']['enum']
        if 'hypotheses' in fields:
            response={'hypotheses':{'0':[],'1':[],'2':[],'3':[]},'choice':keys[0],'insufficient_support':True}
        else:response={'probabilities':{k:1/len(keys) for k in keys},'choice':keys[0],'insufficient_evidence':True,'explanation':'known uniform null'}
        return {'done':True,'done_reason':'stop','message':{'content':json.dumps(response)},'eval_count':12,'prompt_eval_count':20,
            'total_duration':10,'load_duration':1,'prompt_eval_duration':2,'eval_duration':7}
    monkeypatch.setattr(ollama,'api',api)
    pilot=tmp_path/'pilot';dev=tmp_path/'development';policy=tmp_path/'policy';evaluation=tmp_path/'evaluation'
    assert bank.predict(prepared,pilot,'pilot')['admitted']
    assert [r['options']['num_predict'] for r in calls]==[256,512,256,256]
    assert ollama.request_for is original
    bank.predict(prepared,dev,'development',pilot)
    bank.fit(prepared,dev,pilot,policy)
    bank.predict(prepared,evaluation,'evaluation',pilot,policy)
    assert all(r['result']['cost']['output_tokens']<=768 for r in read(evaluation/'ROSTER.json')['rows'])
    monkeypatch.setattr(ollama,'api',lambda *a,**k:pytest.fail('replay must not infer'))
    bank.predict(prepared,dev,'development',pilot)
    bank.predict(prepared,evaluation,'evaluation',pilot,policy)
    with pytest.raises(ValueError,match='phase population'):
        bank.truths(prepared,'evaluation',bank.Readers(prepared).tasks('development'))
    with pytest.raises(RuntimeError),bank.token_budget(256):raise RuntimeError('restore wrapper on failure')
    assert ollama.request_for is original
