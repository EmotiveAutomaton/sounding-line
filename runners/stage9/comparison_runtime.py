"""Immutable-source transport for an explicitly enumerated comparison matrix.

DESIGN CHECK: M01/M04/X02/X06; LESSONS 3--5. NULL: altered copied inputs,
source mismatch, missing outputs or invalid components refuse the entire matrix.
ALTERNATIVE: every explicit input reaches one verified copied-source worker. The
300-second bound permits a complete long series; throughput must be measured.
"""
from pathlib import Path
import shutil
import uuid

from runners.stage7.runtime import BOOTSTRAP
from .capsule_host import run_capsule
from .common import REPO,ROOT,canonical,digest,file_hash,freeze,read,write
from .mark_runtime import SOURCES as MARK_SOURCES

SOURCES = {**MARK_SOURCES,'reader/worker.py':'runners/stage9/comparison_worker.py',
    'reader/single_worker.py':'runners/stage9/mark_worker.py',
    'reader/likelihood_table.py':'runners/stage9/likelihood_table.py',
    'reader/grouped_erasure.py':'runners/stage9/grouped_erasure.py',
    'reader/grouped_table.py':'runners/stage9/grouped_table.py',
    'reader/particle_erasure.py':'runners/stage9/particle_erasure.py',
    'reader/particle_table.py':'runners/stage9/particle_table.py',
    'reader/purpose_reader.py':'runners/stage9/purpose_reader.py',
    'reader/proposal_reader.py':'runners/stage9/proposal_reader.py',
    'reader/context_reader.py':'runners/stage9/context_reader.py',
    'reader/goal_reader.py':'runners/stage9/goal_reader.py',
    'reader/cue_reader.py':'runners/stage9/cue_reader.py',
    'reader/ambiguity_reader.py':'runners/stage9/ambiguity_reader.py',
    'reader/constraint_reader.py':'runners/stage9/constraint_reader.py',
    'reader/familiarity_reader.py':'runners/stage9/familiarity_reader.py',
    'reader/selection_reader.py':'runners/stage9/selection_reader.py',
    'reader/information_selection.py':'runners/stage9/information_selection.py'}


def execute(bundle, *, budget=500000,exact_limit=8,permutations=16,seed=0,
            adaptation_strength=16.,estimator='uniform',exact_states=4096,draws=128,particles=512,task=None,root=None,
            operation='comparison_matrix'):
    if operation not in ('comparison_matrix','purpose_comparison','proposal_evaluation','context_transfer','goal_transfer','context_cue','offered_history','bounded_creation','maker_familiarity','select_observation','select_familiar_observation'):
        raise ValueError('unknown comparison operation')
    if bundle is not None and len(canonical(bundle).encode('utf-8'))>4*1024**2:
        raise ValueError('comparison input exceeds transport envelope')
    root = Path(root or ROOT/'private/capsule-comparisons')
    task = task or {'operation':operation,'budget':budget,'information_sha256':digest(bundle),
        'exact_limit':exact_limit,'permutations':permutations,'seed':seed,'adaptation_strength':adaptation_strength,
        'estimator':estimator,'exact_states':exact_states,'draws':draws,'particles':particles}
    from .saved_replay import active
    replay = active()
    if replay is not None:
        return replay.request(bundle, task, root, SOURCES, runtime='comparison_runtime')
    cap = root/uuid.uuid4().hex[:16]
    for name in ('reader','out','tmp'):
        (cap/name).mkdir(parents=True)
    (cap/'reader/__init__.py').write_text('',encoding='utf-8')
    for destination,source in SOURCES.items():
        shutil.copyfile(REPO/source,cap/destination)
    (cap/'bootstrap.py').write_text(BOOTSTRAP,encoding='utf-8',newline='\n')

    write(cap/'task.json',task)
    if bundle is not None:
        write(cap/'evidence.json',bundle)
    files = {p.relative_to(cap).as_posix():file_hash(p) for p in sorted(cap.rglob('*.py'))}
    copied = {'files':files,'sha256':digest(files),'task_sha256':digest(task),'evidence_sha256':digest(bundle),
              'bootstrap_owner_sha256':file_hash(REPO/'runners/stage7/runtime.py')}
    freeze(root/'closures'/(cap.name+'.json'),copied)
    result = run_capsule(cap,'http://127.0.0.1:0','','',timeout_s=300)
    expected = {('reader' if p=='reader/__init__.py' else p[:-3].replace('/','.')):sha
                for p,sha in files.items() if p.startswith('reader/')}
    unchanged = (all(file_hash(cap/p)==sha for p,sha in files.items()) and
                 digest(read(cap/'task.json'))==digest(task) and
                 (bundle is None or read(cap/'evidence.json')==bundle))
    valid = ((result.get('receipt') or {}).get('all_raised') is True if task.get('probe') else
        (result.get('prediction') or {}).get('valid') is True and
        (result.get('receipt') or {}).get('loaded_sources')==expected)
    return {**result,'accepted':result['rc']==0 and valid and unchanged and result.get('access') is not None,
            'copied_sources':copied,'inputs_and_sources_unchanged':unchanged}
