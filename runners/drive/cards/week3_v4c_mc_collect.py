"""Collect only four complete, independently refitted V4.c reference shards.

DESIGN CHECK: LESSONS 3-5 and CONTROLS 1-7 read 2026-10-30.
Incomplete/duplicated/mixed-source shards fail closed under null and alternative.
Original false-alarm gates override planted sensitivity; all 110 worlds and all
199 references survive. This collector does no extra fitting or human inference.
"""
from pathlib import Path
from runners.stage14.common import read,freeze,filehash
from . import week3_v4c_mc_full as full
CONFIG=dict(shards=4,worlds=110,references=199)


def gather(inputs,config):
    if config!=CONFIG or set(inputs)!={f'shard{i}' for i in range(4)}:raise ValueError('All four declared shards required')
    worlds=[];common=None;bindings={}
    for i in range(4):
        p=Path(inputs[f'shard{i}']);full.checked_complete(p);root=p.parent
        plan=read(root/'PLAN.json');v=read(root/'VERIFIED.json');summary=read(root/'output/SUMMARY.json')
        expected=dict(full.CONFIG,shard_index=i)
        if plan['module']!=full.__name__ or plan['config']!=expected or summary['config']!=expected or not v.get('full_fresh_generation_and_refit'):
            raise ValueError('Shard identity or independent replay differs')
        current=dict(inputs=plan['inputs'],code=read(root/'output/BINDING.json')['code'])
        if common is None:common=current
        if current!=common:raise ValueError('Mixed-source shard collection')
        expected_cells=full.source.roster()[i::4]
        if [w['cell'] for w in summary['worlds']]!=expected_cells:raise ValueError('Incomplete or reassigned shard')
        for w in summary['worlds']:
            base=root/'output/worlds'/full.source.world_name(w['cell'])
            if read(base/'RESULT.json')!=w:raise ValueError('World summary differs')
            values=[read(base/f'null-{j:03d}.json')['statistic']['likelihood_ratio'] for j in range(199)]
            probability=full.core.reference_probability(read(base/'OBSERVED.json')['likelihood_ratio'],values)
            if probability!=w['probability']:raise ValueError('Complete reference probability differs')
        worlds+=summary['worlds'];bindings[str(p.resolve())]=filehash(p)
    # Source order, never completion or shard order, controls bootstrap inputs.
    worlds.sort(key=lambda w:full.source.roster().index(w['cell']))
    return dict(summary=full.full_summary(worlds),completion_hashes=bindings,source_binding=common)


def execute(output,inputs,config):
    result=gather(inputs,config);freeze(Path(output)/'SUMMARY.json',result);return result


def verify(output,inputs,config):
    result=gather(inputs,config)
    if read(Path(output)/'SUMMARY.json')!=result:raise ValueError('Fresh complete collection differs')
    return dict(verified=True,complete_110_world_199_reference_collection=True)
