"""Unchanged complete collector with explicitly bound lossless storage input.

DESIGN CHECK: LESSONS 3-5. All four verified shards and all references required
under null and alternative. Mixed storage bindings and incomplete shards refuse.
"""
from pathlib import Path
from unittest.mock import patch
from runners.stage14.common import read,freeze
from . import week3_v4c_mc_collect as original
from . import week3_v4c_mc_compressed as full
from . import week3_v4c_storage as storage
CONFIG=original.CONFIG


def gather(inputs,config):
    if config!=CONFIG or set(inputs)!={f'shard{i}' for i in range(4)}:raise ValueError('All four declared shards required')
    for p in inputs.values():
        if read(Path(p).parent/'output/STORAGE_BINDING.json')!=full.storage_binding():raise ValueError('Storage binding differs')
    with patch.object(original,'full',full),patch.object(original,'read',storage.read):
        return original.gather(inputs,config)


def execute(output,inputs,config):
    result=gather(inputs,config);freeze(Path(output)/'SUMMARY.json',result);return result


def verify(output,inputs,config):
    if read(Path(output)/'SUMMARY.json')!=gather(inputs,config):raise ValueError('Fresh complete collection differs')
    return dict(verified=True,complete_110_world_199_reference_collection=True)
