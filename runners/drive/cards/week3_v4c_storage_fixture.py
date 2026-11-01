"""Constructed byte/orchestration rehearsal, never a scientific admission.

DESIGN CHECK: LESSONS 3-5. Identical logical outputs under both storage paths;
all 199 references freshly replayed. No real-source or fitted scientific claim.
"""
from pathlib import Path
from contextlib import ExitStack
from unittest.mock import patch
from runners.stage14.common import freeze,read,filehash
from . import week3_v4c_mc_full as old,week3_v4c_mc_compressed as new


def setup(root,stack,calls):
    cell=old.source.roster()[0];split=root/'split';p=split/'output/worlds'/(old.source.world_name(cell)+'.json')
    freeze(p,dict(readers={'R-both':dict(likelihood_ratio=1.)}))
    fixture=root/'fixture.json';freeze(fixture,{})
    state=dict(worlds=[dict(cell=cell)],sessions=[],base={},geometry={},plan={'config':{'seed':1}},split_root=split,split_complete={'outputs':{p.relative_to(split).as_posix():filehash(p)}})
    def generate(rows,base,model,seed):calls.append(seed);return [seed],{'seed':seed}
    for obj,name,value in [(old,'load',lambda *a:state),(old.source,'load_world',lambda *a:({},{})),(old.source,'rebuild',lambda *a:[]),(old.core,'fit_null',lambda *a:{'fixed':'model'}),(old.core,'generate',generate),(old.core,'statistic',lambda rows,*a:dict(likelihood_ratio=float(rows[0]%2) if rows else 1.,halves=[]))]:
        stack.enter_context(patch.object(obj,name,value))
    return {'fixture':str(fixture)},dict(old.CONFIG,shard_index=0)


def execute(output,inputs,config):
    if inputs or config!={'references':199}:raise ValueError('Fixed constructed rehearsal')
    output=Path(output);calls=[]
    with ExitStack() as stack:
        ins,cfg=setup(output,stack,calls)
        a=old.execute(output/'plain',ins,cfg);b=new.execute(output/'packed',ins,cfg)
        assert a==b and len(calls)==398
        assert new.execute(output/'packed',ins,cfg)==b and len(calls)==398
        for p in (output/'plain').rglob('*.json'):
            if p.name in {'FIRST_TENTH.json','PROGRESS.json'}:continue
            assert new.storage.raw(output/'packed'/p.relative_to(output/'plain'))==p.read_bytes()
    result=dict(constructed_fixture_only=True,references=199,logical_parity=True,resume_reuses_seals=True,scientific_admission=False)
    freeze(output/'SUMMARY.json',result);return result


def verify(output,inputs,config):
    if inputs or config!={'references':199}:raise ValueError('Fixed constructed rehearsal')
    output=Path(output);calls=[]
    with ExitStack() as stack:
        ins,cfg=setup(output,stack,calls)
        old.verify(output/'plain',ins,cfg);new.verify(output/'packed',ins,cfg)
        assert len(calls)==398
    return dict(verified=True,constructed_fixture_only=True,full_199_reference_replay=True)
