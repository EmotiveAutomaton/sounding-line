"""Pinned base and preserved Stage 8 adapter references, without old registry writes.

DESIGN CHECK: I01/I03/C01/C05/X01/X02/X07; LESSONS 3--5.
NULL: missing/changed archive, pilot substitution, wrong base or missing weights
refuses before model loading. ALTERNATIVE: actual archived bytes satisfy the
original directory hash and receive an additional full Stage 9 file closure.
This preserves provenance, never borrows the old admission or precision judgment.
"""
import hashlib
from pathlib import Path
from runners.stage9.common import REPO,closure,digest,file_hash,read
from runners.stage9.train import BASES

ARCHIVES={'qwen':('fm_qwen','7dce6645c26923f9'),
          'smollm':('fm_smollm','69e7cb84b5c15c2f')}


def legacy_hash(path):
    """Original Stage 8 adapter_hash byte algorithm, independently reapplied."""
    h=hashlib.sha256()
    for p in sorted(x for x in Path(path).rglob('*') if x.is_file()):
        if p.is_symlink():raise ValueError('archive adapter symlink')
        h.update(p.name.encode('utf-8'));h.update(p.read_bytes())
    return h.hexdigest()[:16]


def reference_package(family,kind):
    if family not in BASES or kind not in ('base','archive'):
        raise ValueError('undeclared reference package')
    if kind=='base':
        return None,'base-no-adapter',digest({'kind':'base','base':BASES[family]})
    name,expected=ARCHIVES[family]
    registry=REPO/'results/phase_2_4_stage_8/ADAPTERS.json'
    row=read(registry)[name]
    path=REPO/'results/phase_2_4_stage_8/adapters'/name/'frozen'
    if (Path(row['path']).resolve()!=path.resolve() or row.get('pilot') is not False
        or row.get('seed')!=8001 or row.get('epoch')!=2
        or row.get('base')!=BASES[family]['model'] or row.get('revision')!=BASES[family]['revision']
        or row.get('sha')!=expected or legacy_hash(path)!=expected):
        raise ValueError('historical adapter differs from the preserved Stage 8 package')
    config=read(path/'adapter_config.json')
    if (config['base_model_name_or_path']!=BASES[family]['model']
        or not (path/'adapter_model.safetensors').is_file()):
        raise ValueError('historical adapter has no matching base/weight package')
    return path,closure([path])['sha256'],digest({'kind':'archive','record':row,
        'registry_sha256':file_hash(registry),'legacy_sha':expected})
