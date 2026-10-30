import json
from pathlib import Path
import pytest
from runners.stage14.common import freeze,read
from runners.drive.cards import week3_v4c_mc_collect as m


def test_complete_collection_order_and_mixed_source_refusal(tmp_path,monkeypatch):
    # A minimal on-disk receipt graph isolates the collector boundary; original
    # source/statistic computation is tested and cost-replayed independently.
    monkeypatch.setattr(m.full,'checked_complete',lambda p:read(p))
    original_read=m.read
    def read_fixture(p):
        p=str(p)
        if Path(p).name.startswith('null-'):return dict(statistic={'likelihood_ratio':0.})
        return original_read(p)
    monkeypatch.setattr(m,'read',read_fixture)
    inputs={}
    for i in range(4):
        root=tmp_path/str(i);p=root/'COMPLETE.json';freeze(p,{});inputs[f'shard{i}']=str(p)
        config=dict(m.full.CONFIG,shard_index=i)
        freeze(root/'PLAN.json',dict(module=m.full.__name__,config=config,inputs={'source':'same'}))
        freeze(root/'VERIFIED.json',dict(full_fresh_generation_and_refit=True))
        freeze(root/'output/BINDING.json',dict(code={'core':'same'}))
        ws=[]
        for cell in m.full.source.roster()[i::4]:
            w=dict(cell=cell,reference_count=199,probability=1.,detected=False);ws.append(w)
            base=root/'output/worlds'/m.full.source.world_name(cell)
            freeze(base/'RESULT.json',w);freeze(base/'OBSERVED.json',dict(likelihood_ratio=0.))
        freeze(root/'output/SUMMARY.json',dict(config=config,worlds=ws))
    out=tmp_path/'out';result=m.execute(out,inputs,m.CONFIG)
    assert result['summary']['worlds']==110 and set(result['summary']['labels'].values())=={'blind'}
    assert m.verify(out,inputs,m.CONFIG)['complete_110_world_199_reference_collection']
    with pytest.raises(ValueError,match='four'):m.gather({k:v for k,v in inputs.items() if k!='shard3'},m.CONFIG)
    p=tmp_path/'1/PLAN.json';v=read(p);v['inputs']['source']='different';p.write_text(json.dumps(v),encoding='utf8')
    with pytest.raises(ValueError,match='Mixed-source'):m.gather(inputs,m.CONFIG)
