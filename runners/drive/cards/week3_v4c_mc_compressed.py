"""V4.c storage .h1: execute the unchanged scientific consumer with lossless I/O.

DESIGN CHECK: LESSONS 3-5 reread 2026-10-30. Logical checkpoint bytes, seeds,
bindings, original comparisons and fresh full refits remain identical under
null and alternative. Only storage representation changes. A failed seal,
missing reference or changed wrapper identity cannot license completion.
"""
from contextlib import contextmanager
from pathlib import Path
from runners.stage14.common import freeze,read,filehash
from . import week3_v4c_mc_full as original
from . import week3_v4c_storage as storage
from . import week3_v4c_checkpoint_storage as checkpoints

CONFIG=original.CONFIG
source=original.source
core=original.core
full_summary=original.full_summary
def physical_manifest(output):
    output=Path(output)
    return {p.relative_to(output).as_posix():filehash(p) for p in sorted(output.rglob('*.xz'))}


def check_manifest(output):
    if read(Path(output)/'XZ_MANIFEST.json')!=physical_manifest(output):
        raise ValueError('Compressed physical manifest differs')


def checked_complete(path):
    result=original.checked_complete(path)
    output=Path(path).parent/'output'
    if 'output/XZ_MANIFEST.json' not in result['outputs']:raise ValueError('Bound physical manifest required')
    check_manifest(output)
    return result


@contextmanager
def lossless_io():
    old=original.read,original.freeze,original.filehash
    original.read,original.freeze,original.filehash=storage.read,storage.freeze,storage.logical_hash
    try:yield
    finally:original.read,original.freeze,original.filehash=old


def storage_binding():
    return dict(format='xz-canonical-json-v1',preset=3,logical_bytes_unchanged=True,
        numerical_consumer_sha256=filehash(original.__file__),
        wrapper_sha256=filehash(__file__),storage_sha256=filehash(storage.__file__),checkpoint_sha256=filehash(checkpoints.__file__))


def execute(output,inputs,config):
    freeze(Path(output)/'STORAGE_BINDING.json',storage_binding())
    resume=Path(output).parent/'CHECKPOINT_SOURCE.json'
    if resume.exists():
        source=read(resume)
        if filehash(Path(source['root'])/'PLAN.json')!=source['plan_sha256']:raise ValueError('Checkpoint source plan changed')
        retained=checkpoints.retain_prefix(source['root'],output,inputs,config)
        cost=read(Path(output).parent/'RESUME_COST.json')
        if retained['retained_references']!=cost['retained_references']:raise ValueError('Resume cost checkpoint count differs')
        freeze(Path(output)/'FIRST_TENTH.json',cost)
    with lossless_io():result=original.execute(output,inputs,config)
    if result.get('status')=='complete':freeze(Path(output)/'XZ_MANIFEST.json',physical_manifest(output))
    return result


def verify(output,inputs,config):
    if read(Path(output)/'STORAGE_BINDING.json')!=storage_binding():
        raise ValueError('Compressed storage binding differs')
    check_manifest(output)
    with lossless_io():return original.verify(output,inputs,config)
