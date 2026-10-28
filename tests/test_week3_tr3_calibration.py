import copy
import json
import pytest
from runners.drive.cards import week3_tr3_calibration as m


def cells():
    return [dict(effect=e,seed=s,result=dict(metrics=dict(primary=dict(route='not-detected' if e==0 else 'positive' if e==1 else 'negative')))) for e,s in m.WORLDS]


def test_complete_gate_boundaries_and_wrong_direction():
    c=cells();assert m.summarize(c,'full')['calibration_passed']
    for x in c[:10]:x['result']['metrics']['primary']['route']='positive'
    for x in c[100:102]+c[120:122]:x['result']['metrics']['primary']['route']='unsupported'
    assert m.summarize(c,'full')['calibration_passed']
    d=copy.deepcopy(c);d[10]['result']['metrics']['primary']['route']='negative'
    assert not m.summarize(d,'full')['calibration_passed']
    d=copy.deepcopy(c);d[102]['result']['metrics']['primary']['route']='negative'
    assert not m.summarize(d,'full')['calibration_passed']
    with pytest.raises(ValueError):m.summarize(c[:-1],'full')
    assert m.summarize(c[:1],'timing')['calibration_passed'] is None


def test_handler_replay_reentry_and_mutation(tmp_path,monkeypatch):
    gate=tmp_path/'gate.json';gate.write_text(json.dumps(dict(full_write_through=True,fixture_hold_cleared=True,implementation_sha256=m.filehash(m.stats.__file__))))
    inputs=dict(fixture_landing=str(gate));out=tmp_path/'out';config=m.CONFIGS['timing'];calls=[]
    def describe(study,**kw):
        calls.append(kw);assert kw==dict(permutations=200,bootstraps=2000,seed=20261026)
        return dict(metrics=dict(primary=dict(route='not-detected')),values=(1,2))
    monkeypatch.setattr(m.stats,'describe',describe)
    m.execute(out,inputs,config);m.execute(out,inputs,config);assert len(calls)==1
    assert m.verify(out,inputs,config)['all_worlds_recomputed'] and len(calls)==2
    p=out/'cells/000.json';v=m.read(p);v['result']['values'][0]=3;p.write_text(json.dumps(v))
    with pytest.raises(ValueError,match='replay'):m.verify(out,inputs,config)
    gate.write_text(json.dumps(dict(full_write_through=True,fixture_hold_cleared=False)))
    with pytest.raises(ValueError,match='not admitted'):m.execute(out,inputs,config)
