"""Copied-source boundary for separately valid baseline selection matrices.

DESIGN CHECK: M01/C08/X02/X06; LESSONS 3--5. NULL: hidden fields or changed
copied sources invalidate the result. ALTERNATIVE: all supplied candidate fits
predict every explicit query under their original loaded source identities.
No program-inference or neural admission dependency is imposed on CPU baselines.
"""
from pathlib import Path
import shutil
import uuid
from runners.stage7.runtime import BOOTSTRAP
from .capsule_host import run_capsule
from .common import REPO,ROOT,canonical,digest,file_hash,freeze,read,write
from .mark_runtime import SOURCES as MARK_SOURCES

SOURCES={**MARK_SOURCES,'reader/worker.py':'runners/stage9/baseline_matrix_worker.py',
         'reader/single_worker.py':'runners/stage9/mark_worker.py'}


def execute(bundle,*,budget=10000,task=None,root=None):
    if bundle is not None and len(canonical(bundle).encode('utf-8'))>4*1024**2:
        raise ValueError('baseline input exceeds transport envelope')
    root=Path(root or ROOT/'private/capsule-baseline-matrices')
    task=task or {'operation':'baseline_matrix','budget':budget,'information_sha256':digest(bundle),'strengths':[8.,16.,32.]}
    from .saved_replay import active
    replay = active()
    if replay is not None:
        return replay.request(bundle, task, root, SOURCES, runtime='baseline_matrix_runtime')
    cap=root/uuid.uuid4().hex[:16]
    for name in ('reader','out','tmp'):(cap/name).mkdir(parents=True)
    (cap/'reader/__init__.py').write_text('',encoding='utf-8')
    for destination,source in SOURCES.items():shutil.copyfile(REPO/source,cap/destination)
    (cap/'bootstrap.py').write_text(BOOTSTRAP,encoding='utf-8',newline='\n')

    write(cap/'task.json',task)
    if bundle is not None:write(cap/'evidence.json',bundle)
    files={p.relative_to(cap).as_posix():file_hash(p) for p in sorted(cap.rglob('*.py'))}
    copied={'files':files,'sha256':digest(files),'task_sha256':digest(task),'evidence_sha256':digest(bundle),
            'bootstrap_owner_sha256':file_hash(REPO/'runners/stage7/runtime.py')}
    freeze(root/'closures'/(cap.name+'.json'),copied)
    result=run_capsule(cap,'http://127.0.0.1:0','','',timeout_s=120)
    expected={('reader' if p=='reader/__init__.py' else p[:-3].replace('/','.')):sha
              for p,sha in files.items() if p.startswith('reader/')}
    unchanged=(all(file_hash(cap/p)==sha for p,sha in files.items()) and digest(read(cap/'task.json'))==digest(task)
               and (bundle is None or read(cap/'evidence.json')==bundle))
    valid=((result.get('receipt') or {}).get('all_raised') is True if task.get('probe') else
           (result.get('prediction') or {}).get('valid') is True and (result.get('receipt') or {}).get('loaded_sources')==expected)
    return {**result,'accepted':result['rc']==0 and valid and unchanged and result.get('access') is not None,
            'copied_sources':copied,'inputs_and_sources_unchanged':unchanged}
