"""Separate capsules for explicit program execution; model capsules remain unchanged.

DESIGN CHECK: I06/X02. Actual copied and loaded sources, immutable evidence and access
receipts are checked. The interpreter boundary is not an OS security claim.
NULL: unsupported/missing input or forbidden constructor access invalidates execution.
ALTERNATIVE: complete numeric programs execute inside the restricted reader process.
"""
from pathlib import Path
import shutil
import uuid

from runners.stage7.runtime import BOOTSTRAP
from .capsule_host import run_capsule
from runners.stage9.common import REPO, ROOT, canonical, digest, file_hash, freeze, read, write

SOURCES = {'reader/worker.py': 'runners/stage9/kernel_worker.py', 'reader/kernel.py': 'runners/stage9/kernel.py',
           'reader/base.py': 'runners/stage9/reader.py', 'reader/readout.py': 'runners/readout_repair.py',
           'reader/features.py': 'runners/stage9/features.py'}


def execute(evidence, task=None, root=None):
    if evidence is not None and len(canonical(evidence).encode('utf-8')) > 2 * 1024**2:
        raise ValueError('numeric program evidence exceeds the bounded transport envelope')
    root = Path(root or ROOT / 'private/capsule-kernel')
    cap = root / uuid.uuid4().hex[:16]
    (cap / 'reader').mkdir(parents=True)
    (cap / 'out').mkdir()
    (cap / 'tmp').mkdir()
    (cap / 'reader/__init__.py').write_text('', encoding='utf-8')
    for destination, source in SOURCES.items():
        shutil.copyfile(REPO / source, cap / destination)
    (cap / 'bootstrap.py').write_text(BOOTSTRAP, encoding='utf-8', newline='\n')
    task = task or {'operation': 'execute_program_mixture', 'information_sha256': digest(evidence)}
    write(cap / 'task.json', task)
    if evidence is not None:
        write(cap / 'evidence.json', evidence)
    files = {p.relative_to(cap).as_posix(): file_hash(p) for p in sorted(cap.rglob('*.py'))}
    source_receipt = {'files': files, 'sha256': digest(files), 'task_sha256': digest(task),
                      'evidence_sha256': digest(evidence), 'bootstrap_owner_sha256': file_hash(REPO / 'runners/stage7/runtime.py')}
    freeze(root / 'closures' / (cap.name + '.json'), source_receipt)
    result = run_capsule(cap, 'http://127.0.0.1:0', '', '', timeout_s=60)
    expected_loaded = {('reader' if p == 'reader/__init__.py' else p[:-3].replace('/', '.')): sha
                       for p, sha in files.items() if p.startswith('reader/')}
    unchanged = all(file_hash(cap / p) == sha for p, sha in files.items())
    unchanged = unchanged and digest(read(cap / 'task.json')) == digest(task)
    if evidence is not None:
        unchanged = unchanged and digest(read(cap / 'evidence.json')) == digest(evidence)
    if task.get('probe'):
        valid = (result.get('receipt') or {}).get('all_raised') is True
    else:
        valid = ((result.get('prediction') or {}).get('valid') is True
                 and (result.get('receipt') or {}).get('loaded_sources') == expected_loaded)
    return {**result, 'accepted': result['rc'] == 0 and valid and unchanged and result.get('access') is not None,
            'copied_sources': source_receipt, 'inputs_and_sources_unchanged': unchanged}
