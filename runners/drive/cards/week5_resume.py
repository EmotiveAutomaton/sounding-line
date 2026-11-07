"""Authenticated copies of stopped Week 5 checkpoints into fresh attempts.

DESIGN CHECK: LESSONS 3-5. A complete immutable manifest is required in both
scientific directions. Tampered, live, incompatible or partial copies refuse.
The predecessor is never edited. Operational quanta may change, not estimands.
"""
from pathlib import Path
import shutil
from .batch_runtime import read, freeze, filehash, check_files
from runners.stage9.process_identity import is_same_live_process

OPERATIONAL_KEYS = {'max_new_draws', 'max_wall_seconds'}

def semantic_config(config):
    return {k:v for k,v in config.items() if k not in OPERATIONAL_KEYS}

def output_manifest(output):
    output=Path(output)
    return {p.relative_to(output).as_posix():filehash(p) for p in sorted(output.rglob('*'))
            if p.is_file() and p.name not in {'YIELD_REQUEST.json','PROGRESS.json'}
            and not p.name.endswith('.tmp') and '.tmp.' not in p.name}

def copy_checkpoint(root, plan):
    spec=plan.get('resume')
    if not spec:return None
    old=Path(spec['root']).resolve(); root=Path(root).resolve()
    from .week5_policy import ROOT
    old.relative_to(ROOT); root.relative_to(ROOT)
    if old==root:raise ValueError('Resume requires a new attempt root')
    for name,key in [('PLAN.json','plan_sha256'),('PAUSED.json','paused_sha256')]:
        if filehash(old/name)!=spec[key]:raise ValueError('Resume receipt pin mismatch')
    prior=read(old/'PLAN.json'); paused=read(old/'PAUSED.json')
    if any((old/n).exists() for n in ('COMPLETE.json','FAILED.json')):raise ValueError('Ambiguous predecessor')
    if is_same_live_process(read(old/'OWNER.json')['native']):raise ValueError('Predecessor still live')
    if paused.get('status')!='PAUSED' or not paused.get('checkpoint_validation_required'):raise ValueError('Not a resumable pause')
    for key in ('module','inputs','family','campaign'):
        if plan[key]!=prior[key]:raise ValueError('Changed scientific resume contract: '+key)
    if semantic_config(plan['config'])!=semantic_config(prior['config']):raise ValueError('Changed scientific configuration')
    check_files(prior['pins']);check_files(plan['pins'])
    expected=paused.get('checkpoint_outputs')
    if not expected or output_manifest(old/'output')!=expected:raise ValueError('Incomplete or changed checkpoint manifest')
    target=root/'output'
    if target.exists() and any(target.iterdir()):raise ValueError('Resume target must be empty')
    for name,digest in expected.items():
        source=(old/'output'/name).resolve();source.relative_to(old/'output')
        dest=(target/name).resolve();dest.relative_to(target)
        dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,dest)
        if filehash(dest)!=digest:raise ValueError('Checkpoint copy mismatch')
    if output_manifest(target)!=expected:raise ValueError('Checkpoint copy incomplete')
    receipt=dict(predecessor=str(old),plan_sha256=spec['plan_sha256'],paused_sha256=spec['paused_sha256'],copied=expected)
    freeze(root/'RESUMED_FROM.json',receipt)
    return receipt
