"""Immutable copied-source transport for the artifact comparator worker.

DESIGN CHECK: M01/X02; LESSONS 3--5. Actual copied/loaded sources and immutable
inputs must agree, and forbidden access must fail. This is a restricted interpreter
boundary, not operating-system isolation. Evaluator projection/fitting stays outside.
"""
from pathlib import Path
import shutil
import uuid

from runners.stage7.runtime import BOOTSTRAP
from .capsule_host import run_capsule
from runners.stage9.common import REPO, ROOT, canonical, digest, file_hash, freeze, read, write

SOURCES = {'reader/worker.py': 'runners/stage9/mark_worker.py',
           'reader/base.py': 'runners/stage9/reader.py',
           'reader/readout.py': 'runners/readout_repair.py',
           **{'reader/'+name+'.py': 'runners/stage9/'+name+'.py' for name in
              ('features', 'artifact_view', 'choice_features', 'mark_program', 'erased_inference',
               'program_inference', 'program_proposals')}}


def execute(bundle, operation=None, *, budget=200000, exact_limit=8, permutations=16, seed=0,
            adaptation_strength=16., maximum_candidates=16, expand=False, task=None, root=None):
    if bundle is not None and len(canonical(bundle).encode('utf-8')) > 4*1024**2:
        raise ValueError('comparator evidence exceeds bounded transport envelope')
    root = Path(root or ROOT/'private/capsule-mark')
    task = task or {'operation': operation, 'budget': budget, 'information_sha256': digest(bundle),
                    'exact_limit': exact_limit, 'permutations': permutations, 'seed': seed,
                    'adaptation_strength': adaptation_strength, 'maximum_candidates': maximum_candidates, 'expand': expand}
    from .saved_replay import active
    replay = active()
    if replay is not None:
        return replay.request(bundle, task, root, SOURCES, runtime='mark_runtime')
    cap = root/uuid.uuid4().hex[:16]
    for name in ('reader', 'out', 'tmp'):
        (cap/name).mkdir(parents=True)
    (cap/'reader/__init__.py').write_text('', encoding='utf-8')
    for destination, source in SOURCES.items():
        shutil.copyfile(REPO/source, cap/destination)
    (cap/'bootstrap.py').write_text(BOOTSTRAP, encoding='utf-8', newline='\n')

    write(cap/'task.json', task)
    if bundle is not None:
        write(cap/'evidence.json', bundle)
    files = {p.relative_to(cap).as_posix(): file_hash(p) for p in sorted(cap.rglob('*.py'))}
    receipt = {'files': files, 'sha256': digest(files), 'task_sha256': digest(task), 'evidence_sha256': digest(bundle),
               'bootstrap_owner_sha256': file_hash(REPO/'runners/stage7/runtime.py')}
    freeze(root/'closures'/(cap.name+'.json'), receipt)
    result = run_capsule(cap, 'http://127.0.0.1:0', '', '', timeout_s=120)
    expected_loaded = {('reader' if p == 'reader/__init__.py' else p[:-3].replace('/', '.')): sha
                       for p, sha in files.items() if p.startswith('reader/')}
    unchanged = all(file_hash(cap/p) == sha for p, sha in files.items()) and digest(read(cap/'task.json')) == digest(task)
    if bundle is not None:
        unchanged = unchanged and digest(read(cap/'evidence.json')) == digest(bundle)
    valid = ((result.get('receipt') or {}).get('all_raised') is True if task.get('probe') else
             (result.get('prediction') or {}).get('valid') is True and
             (result.get('receipt') or {}).get('loaded_sources') == expected_loaded)
    return {**result, 'accepted': result['rc'] == 0 and valid and unchanged and result.get('access') is not None,
            'copied_sources': receipt, 'inputs_and_sources_unchanged': unchanged}
