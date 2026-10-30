import copy,json
from pathlib import Path
import pytest
from runners.stage14.common import freeze,read,filehash
from runners.drive.cards import week3_v4c_mc_full as m


def test_admission_requires_complete_landed_source_bound_budget():
    a=dict(full_write_through=True,cost_admitted=True,scope='110x199 CPU only',cost_complete_sha256='cost',source_hashes={'s':'h'},fixed_total_cpu_seconds=100,prior_cpu_seconds_charged=10)
    m.validate_admission(a,'cost',90,{'s':'h'})
    for change,match in [({'full_write_through':False},'admission'),({'scope':'smaller'},'admission'),({'cost_complete_sha256':'other'},'binding'),({'fixed_total_cpu_seconds':99},'projection')]:
        with pytest.raises(ValueError,match=match):m.validate_admission(dict(a,**change),'cost',90,{'s':'h'})
    with pytest.raises(ValueError,match='projection'):m.validate_admission(a,'cost',float('nan'),{'s':'h'})
    with pytest.raises(ValueError,match='binding'):m.validate_admission(a,'cost',90,{'s':'changed'})


def worlds():
    return [dict(cell=c,reference_count=199,probability=.005 if c['delta']>=.4 and not c['permuted'] else 1.,detected=c['delta']>=.4 and not c['permuted']) for c in m.source.roster()]


def test_original_bands_complete_roster_and_failed_null_override_power():
    ws=worlds();s=m.full_summary(ws)
    assert set(s['labels'].values())=={'sees'} and not s['scientific_admission']
    for w in ws:
        if w['cell']['permuted']:w.update(probability=.005,detected=True)
    assert set(m.full_summary(ws)['labels'].values())=={'blind'}
    with pytest.raises(ValueError,match='roster'):m.full_summary(ws[:-1])
    changed=copy.deepcopy(ws);changed[0]=changed[1]
    with pytest.raises(ValueError,match='roster'):m.full_summary(changed)
    ws[0]['reference_count']=198
    with pytest.raises(ValueError,match='reference'):m.full_summary(ws)


def test_fixed_disjoint_shards_cover_original_matrix():
    roster=m.source.roster();parts=[roster[i::4] for i in range(4)]
    assert [len(x) for x in parts]==[28,28,27,27]
    assert len({m.source.world_name(c) for p in parts for c in p})==110
    seeds=[m.CONFIG['seed']+1000*i+j for i in range(110) for j in range(199)]
    assert len(set(seeds))==110*199


def test_complete_199_draw_orchestration_checkpoint_replay_and_tamper(tmp_path,monkeypatch):
    # Deterministic stand-ins isolate orchestration. The numerical core has its
    # own known-answer tests and full-source independently replayed cost probe.
    cell=m.source.roster()[0];old=tmp_path/'old';p=old/'output/worlds'/(m.source.world_name(cell)+'.json')
    freeze(p,dict(readers={'R-both':dict(likelihood_ratio=1.)}))
    fixture=tmp_path/'fixture.json';freeze(fixture,{})
    s=dict(worlds=[dict(cell=cell)],sessions=[],base={},geometry={},plan={'config':{'seed':1}},split_root=old,split_complete={'outputs':{p.relative_to(old).as_posix():filehash(p)}})
    monkeypatch.setattr(m,'load',lambda inputs,config:s)
    monkeypatch.setattr(m.source,'load_world',lambda s,w:({},{}));monkeypatch.setattr(m.source,'rebuild',lambda *a:[])
    monkeypatch.setattr(m.core,'fit_null',lambda *a:{'fixed':'model'})
    calls=[]
    def gen(rows,base,model,seed):calls.append(seed);return [seed],{'seed':seed}
    monkeypatch.setattr(m.core,'generate',gen)
    monkeypatch.setattr(m.core,'statistic',lambda rows,*a:dict(likelihood_ratio=float(rows[0]%2) if rows else 1.,halves=[]))
    config=dict(m.CONFIG,shard_index=0);out=tmp_path/'out';inputs={'fixture':str(fixture)}
    result=m.execute(out,inputs,config)
    assert len(calls)==199 and result['primary'] is None and result['aggregate_verdict_pending']
    assert result['worlds'][0]['probability']==(1+sum(seed%2 for seed in calls))/200
    assert m.execute(out,inputs,config)==result and len(calls)==199
    assert m.verify(out,inputs,config)['full_fresh_generation_and_refit'] and len(calls)==398
    target=next((out/'worlds').glob('*/null-000.json'));v=read(target);v['statistic']['likelihood_ratio']=9.
    target.write_text(json.dumps(v),encoding='utf8')
    with pytest.raises(ValueError,match='seal'):m.execute(out,inputs,config)
    with pytest.raises(ValueError,match='replay differs'):m.verify(out,inputs,config)


def test_partial_boundary_never_makes_verdict(tmp_path,monkeypatch):
    fixture=tmp_path/'fixture.json';freeze(fixture,{})
    monkeypatch.setattr(m,'load',lambda *a:dict(worlds=[{'cell':m.source.roster()[0]}]))
    out=tmp_path/'out';freeze(out/'YIELD_REQUEST.json',{})
    assert m.execute(out,{'fixture':str(fixture)},dict(m.CONFIG,shard_index=0))['status']=='yielded'
    assert not (out/'SUMMARY.json').exists()
