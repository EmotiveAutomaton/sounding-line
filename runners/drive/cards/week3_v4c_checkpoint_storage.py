"""Authenticate and losslessly retain stopped V4.c prefixes in a new root.

DESIGN CHECK: LESSONS 3-5. NULL and ALTERNATIVE retain identical bytes, rows and
seeds. Changed sources, live owners, broken seals and nonconsecutive prefixes
refuse. Unsealed old work remains recorded and is recomputed by the consumer.
"""
from pathlib import Path
import time
from runners.stage14.common import read,freeze,atomic,filehash
from runners.stage9.process_identity import native_identity
from . import week3_v4c_mc_full as full,week3_v4c_storage as storage


def retain_prefix(oldroot,output,inputs,config):
    oldroot=Path(oldroot);output=Path(output)
    if oldroot.resolve()==output.parent.resolve():raise ValueError('Separate attempt required')
    plan=read(oldroot/'PLAN.json')
    if plan['module']!=full.__name__ or plan['config']!=config or plan['inputs']!=inputs:raise ValueError('Original plan differs')
    if (oldroot/'COMPLETE.json').exists() or not any((oldroot/n).exists() for n in ('FAILED.json','PAUSED.json')):raise ValueError('Stopped original attempt required')
    for name in ('OWNER.json','EXECUTE_NATIVE.json'):
        ident=read(oldroot/name)['native']
        try:
            if native_identity(ident['pid'])==ident:raise ValueError('Original owner still active')
        except ProcessLookupError:pass
    for p,h in plan['pins'].items():
        if filehash(p)!=h:raise ValueError('Original source pin changed')
    binding=read(oldroot/'output/BINDING.json')
    expected=dict(config=config,inputs={k:filehash(v) for k,v in inputs.items()},code={str(Path(m.__file__).resolve()):filehash(m.__file__) for m in (full.core,full.source,full.original)},consumer_sha256=filehash(full.__file__))
    if binding!=expected:raise ValueError('Original binding differs')
    freeze(output/'BINDING.json',binding);count=0;unsealed=0;started=time.process_time();manifest={}
    allowed={full.source.world_name(c):i for i,c in enumerate(full.source.roster()) if i%4==config['shard_index']}
    for folder in sorted((oldroot/'output/worlds').iterdir()):
        if folder.name not in allowed:raise ValueError('Wrong shard world')
        target=output/'worlds'/folder.name
        for name in ('NULL_MODEL.json','OBSERVED.json'):
            freeze(target/name,read(folder/name))
        seals=sorted(folder.glob('null-*.json.seal.json'))
        if [int(p.name[5:8]) for p in seals]!=list(range(len(seals))) or len(seals)>199:raise ValueError('Nonconsecutive sealed prefix')
        for j,seal in enumerate(seals):
            source=folder/f'null-{j:03d}.json';raw=source.read_bytes();h=storage.logical_hash(source)
            if read(seal)!=dict(binding=binding,sha256=h):raise ValueError('Retained seal differs')
            if read(source)['seed']!=config['seed']+1000*allowed[folder.name]+j:raise ValueError('Retained seed differs')
            storage.retain_bytes(target/source.name,raw);freeze(target/seal.name,read(seal))
            manifest[str(source.relative_to(oldroot))]=h;count+=1
            atomic(output/'STORAGE_PROGRESS.json',dict(references=count,phase='lossless_checkpoint_conversion',cpu_seconds=time.process_time()-started))
        unsealed+=len(list(folder.glob('null-???.json')))-len(seals)
        if (folder/'RESULT.json').exists():
            if len(seals)!=199:raise ValueError('Partial world result')
            freeze(target/'RESULT.json',read(folder/'RESULT.json'))
    receipt=dict(original_root=str(oldroot.resolve()),retained_references=count,unsealed_old_references_not_admitted=unsealed,original_hashes=manifest,byte_preserving=True)
    freeze(output/'CHECKPOINT_STORAGE.json',receipt)
    return receipt
