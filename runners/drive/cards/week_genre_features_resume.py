"""Retain completed GEN1 extraction and finish its fresh source verification.

DESIGN CHECK: LESSONS 3-5 and CONTROLS 1-7 read 2026-10-23. NULL and
ALTERNATIVE outputs are retained byte-for-byte and verified by the original
source reconstruction. Only a combined wall-cap interruption during verify is
eligible; incomplete extraction, other failures, changed pins and output drift
refuse continuation. Failure direction: no unverified checkpoint becomes science.
No feature, support, timing, dictionary, control or scoring rule changes.
"""
from pathlib import Path

from . import week_genre_features_paths as base
from .timing_census import read, filehash
from .timing_p6 import gzread, write_equal

CONFIG = dict(card='GEN1-feature-verification-continuation',schema=1)
NAMES = ('FEATURES.json.gz','DICTIONARY.json','SUMMARY.json','BINDINGS.json','SUPPORT.json','EXECUTE_TIME.json')


def original(inputs):
    if set(inputs) != {'interrupted_root'}: raise ValueError('Exact interrupted extraction required')
    root = Path(inputs['interrupted_root']).resolve(); plan=read(root/'PLAN.json')
    if plan['module'] != base.__name__ or plan['config'] != base.CONFIG:
        raise ValueError('Original extractor/configuration differs')
    if (root/'COMPLETE.json').exists(): raise ValueError('Do not restart a completed component')
    if read(root/'FAILED.json')['error'] != "TimeoutError('Combined execution/replay bound exceeded')":
        raise ValueError('Only a documented combined wall-cap interruption is eligible')
    if read(root/'PROGRESS.json')['phase'] != 'verify': raise ValueError('Extraction did not reach verification')
    if any(filehash(p) != h for p,h in plan['pins'].items()): raise ValueError('Original pinned source changed')
    if read(root/'RESULT.json') != read(root/'output/SUMMARY.json'):
        raise ValueError('Original extraction did not produce its complete result')
    summary=read(root/'output/SUMMARY.json');rows=gzread(root/'output/FEATURES.json.gz')
    if summary['sessions'] != len(rows) or summary['typed_words'] != sum(r['typed_words'] for r in rows):
        raise ValueError('Extraction checkpoint is incomplete')
    for p,h in read(root/'output/BINDINGS.json').items():
        if filehash(p) != h: raise ValueError('Original input bytes changed')
    return root,plan


def execute(output,inputs,config):
    if config != CONFIG: raise ValueError('Frozen continuation configuration required')
    root,plan=original(inputs);output=Path(output);output.mkdir(parents=True,exist_ok=True)
    hashes={}
    for name in NAMES:
        data=(root/'output'/name).read_bytes();dest=output/name
        if dest.exists() and dest.read_bytes()!=data: raise ValueError('Retained extraction changed')
        if not dest.exists(): dest.write_bytes(data)
        hashes[name]=filehash(dest)
    write_equal(output/'CONTINUATION.json',dict(original_plan_sha256=filehash(root/'PLAN.json'),
        original_failure_sha256=filehash(root/'FAILED.json'),retained=hashes,
        completed_extraction_reused=True,verification_pending=True))
    return dict(status='retained_complete_extraction',scientific_admission=False)


def verify(output,inputs,config):
    if config != CONFIG: raise ValueError('Frozen continuation configuration required')
    root,plan=original(inputs);output=Path(output);binding=read(output/'CONTINUATION.json')
    if any(filehash(output/name)!=h or filehash(root/'output'/name)!=h for name,h in binding['retained'].items()):
        raise ValueError('Retained extraction drifted')
    result=base.verify(output,plan['inputs'],base.CONFIG)
    return dict(result,completed_extraction_reused=True,full_source_reconstruction=True)
