import copy
import json
import pytest
from runners.next_round import history_texture as h, scope_diagnostic as s
from runners.next_round import literal_admission as original


def test_composition_is_not_within_writer_change():
    rows=[dict(writer='a',history_decisions=0,gain=.2),dict(writer='b',history_decisions=0,gain=-.2),
          dict(writer='a',history_decisions=2,gain=.2)]
    out=h.curves(rows)
    assert out['bins'][0]['mean_gain']==0 and out['bins'][1]['mean_gain']==.2
    assert out['adjacent_matched'][0]['difference']==0
    assert out['adjacent_matched'][1]['difference'] is None
    assert all(r['mean_gain'] is None for r in out['balanced'])


def test_planted_change_and_unbalanced_writer_weights():
    rows=[dict(writer='a',history_decisions=0,gain=0),dict(writer='b',history_decisions=0,gain=0)]
    rows += [dict(writer='a',history_decisions=3,gain=.1)]*9+[dict(writer='b',history_decisions=3,gain=.3)]
    out=h.curves(rows)['adjacent_matched'][0]
    assert out['difference']==pytest.approx(.2)
    assert out['leave_one_writer_out_range']==pytest.approx([.1,.3])
    assert out['positive']==2


def test_bad_probabilities_and_duplicate_keys_refuse():
    with pytest.raises(ValueError):h.loss([float('nan'),0,0,0],0)
    with pytest.raises(ValueError):h.loss([.1]*4,0)
    with pytest.raises(ValueError):h.analyze([{'key':'a'},{'key':'a'}])
    assert h.loss([.25]*4,0)==.375


def test_roster_prompt_scope_repeats_and_balancing():
    rows=s.roster();assert len(rows)==384
    assert len({r['id'] for r in rows})==192
    assert len({r['target'] for r in rows})==32
    assert len({r['slot'] for r in rows})==384
    for r in rows[:192]:
        twin=next(v for v in rows[192:] if v['id']==r['id'])
        assert (twin['prompt'],twin['schema'])==(r['prompt'],r['schema'])
        opposite=next(v for v in rows[:192] if v['target']==r['target'] and v['context']==r['context'] and v['arm']!=r['arm'])
        assert (r['prompt'] if r['arm']=='explicit' else opposite['prompt'])==s.SCOPE+(opposite['prompt'] if r['arm']=='explicit' else r['prompt'])
    for target in s.targets():
        assert target['matching']!=target['conflicting']
        rr=[r for r in rows if r['target']==target['id']]
        for r in rr:
            inputs=json.loads(r['prompt'].split('Input data: ')[1]);assert inputs['text']==target['text']


def test_oracle_context_copying_and_repeat_instability():
    rows=s.roster()
    oracle=[dict(r,valid=True,answer=r['label'],correct=True) for r in rows]
    result=s.summarize(oracle)
    assert all(v['disagree']==0 for v in result['repeat_disagreement'].values())
    assert all(v['prompt_by_conflict_difference']==0 for v in result['effects'].values())
    bad=copy.deepcopy(oracle)
    for r in bad:
        if r['context']=='conflicting' and r['arm']=='original':r.update(answer=None,valid=False,correct=False)
    result=s.summarize(bad)
    assert all(v['prompt_by_conflict_difference']==1 for v in result['effects'].values())
    bad[0].update(valid=False,answer=None,correct=False)
    # Repeat changes remain visible even if aggregate accuracy is very high.
    noisy=copy.deepcopy(oracle);noisy[0].update(valid=False,answer=None,correct=False)
    assert sum(v['disagree'] for v in s.summarize(noisy)['repeat_disagreement'].values())==1
    with pytest.raises(ValueError):s.summarize(oracle[:-1])


def test_exact_repeats_have_separate_raw_dispatches(tmp_path,monkeypatch):
    calls=[]
    def fake_api(path,body=None,timeout=600):
        calls.append(body)
        return dict(done=True,done_reason='stop',response='{"answer":"first"}',prompt_eval_count=80)
    monkeypatch.setattr(original,'api',fake_api)
    monkeypatch.setattr(original,'inspect_service',lambda *args:dict(resident=[dict(size_vram=0)]))
    b=s.RepeatedBackend(tmp_path,lambda:None)
    b.slot=0;b.complete('same prompt',{'type':'object'})
    b.slot=1;b.complete('same prompt',{'type':'object'})
    assert calls[0]==calls[1] and len(list(tmp_path.rglob('RAW.json')))==2
    with pytest.raises(RuntimeError,match='already dispatched'):b.complete('same prompt',{'type':'object'})
    assert len(calls)==2


def test_oversized_prompt_response_refuses_after_retention(tmp_path,monkeypatch):
    monkeypatch.setattr(original,'api',lambda *args,**kwargs:dict(done=True,done_reason='stop',response='{}',prompt_eval_count=1500))
    monkeypatch.setattr(original,'inspect_service',lambda *args:dict(resident=[dict(size_vram=0)]))
    b=s.RepeatedBackend(tmp_path,lambda:None);b.slot=0
    with pytest.raises(ValueError,match='token bound'):b.complete('prompt',{'type':'object'})
    assert len(list(tmp_path.rglob('RAW.json')))==1
