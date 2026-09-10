"""Immutable restricted-interpreter boundary for public B-roll comparators.

DESIGN CHECK: H01/H02/X02/X06; LESSONS 3--5. NULL: missing or changed copied
sources/inputs refuse acceptance. ALTERNATIVE: every actual loaded source matches
its pre-execution bytes and the worker returns a complete distribution. This is
the existing CPython audit-hook boundary, not claimed operating-system isolation.
"""
from pathlib import Path
import shutil,uuid
from runners.stage7.runtime import BOOTSTRAP
from .capsule_host import run_capsule
from .common import REPO,ROOT,canonical,digest,file_hash,freeze,read,write

SOURCES={'reader/worker.py':'runners/stage9/broll_reader.py','reader/base.py':'runners/stage9/reader.py',
    'reader/readout.py':'runners/readout_repair.py','reader/features.py':'runners/stage9/features.py'}


def execute(bundle,*,root=None,task=None):
    if bundle is not None and len(canonical(bundle).encode())>4*1024**2:raise ValueError('B-roll evidence transport cap exceeded')
    if task is None or len(canonical(task).encode())>32*1024**2:raise ValueError('explicit bounded B-roll model task required')
    root=Path(root or ROOT/'private/capsule-broll');cap=root/uuid.uuid4().hex[:16]
    for name in ('reader','out','tmp'):(cap/name).mkdir(parents=True)
    (cap/'reader/__init__.py').write_text('',encoding='utf-8')
    for dst,src in SOURCES.items():shutil.copyfile(REPO/src,cap/dst)
    (cap/'bootstrap.py').write_text(BOOTSTRAP,encoding='utf-8',newline='\n')
    # Every task explicitly binds its complete fitted parameters and public evidence.
    write(cap/'task.json',task)
    if bundle is not None:write(cap/'evidence.json',bundle)
    files={p.relative_to(cap).as_posix():file_hash(p) for p in sorted(cap.rglob('*.py'))}
    copied={'files':files,'sha256':digest(files),'task_sha256':digest(task),'evidence_sha256':digest(bundle),
        'bootstrap_owner_sha256':file_hash(REPO/'runners/stage7/runtime.py')}
    freeze(root/'closures'/(cap.name+'.json'),copied)
    result=run_capsule(cap,'http://127.0.0.1:0','','',timeout_s=120)
    expected={('reader' if p=='reader/__init__.py' else p[:-3].replace('/','.')):sha for p,sha in files.items() if p.startswith('reader/')}
    unchanged=(all(file_hash(cap/p)==sha for p,sha in files.items()) and digest(read(cap/'task.json'))==digest(task)
        and (bundle is None or digest(read(cap/'evidence.json'))==digest(bundle)))
    valid=((result.get('receipt') or {}).get('all_raised') is True if task.get('probe') else
        (result.get('prediction') or {}).get('valid') is True and (result.get('receipt') or {}).get('loaded_sources')==expected)
    return {**result,'accepted':result['rc']==0 and valid and unchanged and result.get('access') is not None,
        'copied_sources':copied,'inputs_and_sources_unchanged':unchanged}
