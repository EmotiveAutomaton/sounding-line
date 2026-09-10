"""Stage 9 capsule materialization, immutable inputs, real access receipts.

DESIGN CHECK: inherited interpreter boundary is explicitly scoped, not an OS sandbox.
NULL: any forbidden access not denied by the actual capsule blocks lock.
ALTERNATIVE: all accesses denied and loaded file hashes match the copied closure.
No Stage 7/8 registry or capsule is changed by these wrappers.
"""
from pathlib import Path
import shutil
import uuid

from runners.stage7.runtime import BOOTSTRAP
from .capsule_host import run_capsule
from runners.stage9.common import REPO, ROOT, digest, file_hash, freeze, write


def materialize(evidence, task, root=None):
    # Unique paths retain interrupted fragments, avoid unsafe recursive replacement,
    # and prevent a previous prediction from satisfying a new execution.
    root = Path(root or ROOT / 'capsules')
    cap = root / uuid.uuid4().hex[:16]
    (cap / 'reader').mkdir(parents=True)
    (cap / 'out').mkdir()
    (cap / 'tmp').mkdir()
    (cap / 'reader/__init__.py').write_text('', encoding='utf-8')
    shutil.copyfile(REPO / 'runners/stage9/reader.py', cap / 'reader/worker.py')
    shutil.copyfile(REPO / 'runners/readout_repair.py', cap / 'reader/readout.py')
    shutil.copyfile(REPO / 'runners/stage9/features.py', cap / 'reader/features.py')
    (cap / 'bootstrap.py').write_text(BOOTSTRAP, encoding='utf-8', newline='\n')
    if evidence is not None:
        write(cap / 'evidence.json', evidence)
    write(cap / 'task.json', task)
    files = {p.relative_to(cap).as_posix(): file_hash(p) for p in sorted(cap.rglob('*.py'))}
    frozen = {'files': files, 'sha256': digest(files), 'evidence_sha256': digest(evidence), 'task_sha256': digest(task),
              'bootstrap_owner': 'runners/stage7/runtime.py', 'bootstrap_owner_sha256': file_hash(REPO / 'runners/stage7/runtime.py')}
    # Source receipts stay evaluator-side, outside the visible capsule.
    freeze(root / 'closures' / (cap.name + '.json'), frozen)
    return cap, frozen


def execute(evidence, task, endpoint='http://127.0.0.1:0', token='', root=None, timeout=900):
    cap, sources = materialize(evidence, task, root)
    result = run_capsule(cap, endpoint, token, task.get('identity', {}).get('model', ''), timeout_s=timeout)
    expected = {'reader': sources['files']['reader/__init__.py'], 'reader.worker': sources['files']['reader/worker.py'],
                'reader.readout': sources['files']['reader/readout.py'], 'reader.features': sources['files']['reader/features.py']}
    result['copied_sources'] = sources
    if task.get('probe'):
        result['accepted'] = result['rc'] == 0 and bool((result.get('receipt') or {}).get('all_raised'))
    else:
        result['accepted'] = (result['rc'] == 0 and bool((result.get('prediction') or {}).get('valid'))
                              and (result.get('receipt') or {}).get('loaded_sources') == expected)
    # Recheck immutable inputs and actual copied source bytes AFTER execution.
    unchanged = all(file_hash(cap / p) == sha for p, sha in sources['files'].items())
    from runners.stage9.common import read
    unchanged = unchanged and digest(read(cap / 'task.json')) == sources['task_sha256']
    if evidence is not None:
        unchanged = unchanged and digest(read(cap / 'evidence.json')) == sources['evidence_sha256']
    result['accepted'] = result['accepted'] and unchanged and result.get('access') is not None
    result['inputs_and_sources_unchanged'] = unchanged
    return result
