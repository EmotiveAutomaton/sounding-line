"""Run the frozen human effort policies with grouping metadata only.

DESIGN CHECK: LESSONS3-5; current central comparison freeze. Under NULL or
unsupported development groups the selector stops; supported benefits may buy
the declared extra route. All policies retain invalids and actual costs.
Changed fits, overlapping writers/events and modified inputs refuse before
inference. The label-file projection exposes identities only, never outcomes.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
from runners.stage9.process_identity import native_identity
from soundingline.gpulock import GPU_LOCK, acquire_gpu_lock, release_gpu_lock
from . import effort, human_effort_fit as fitter, human_effort_queue as queue
from . import human_effort_readers as readers
from .contracts import digest
from .ollama import now, write_new
from .queue import read, status
from .reader import from_record


def file_hash(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def metadata(prepared, phase, frozen):
    """Open the original sealed file, discard outcome fields during decoding.

    This is metadata access to an evaluator file, not an outcome comparison.
    The original canonical bytes are checked before the identity-only projection.
    """
    raw = (prepared/(phase+'-evaluator.json')).read_bytes()
    if hashlib.sha256(raw.rstrip(b'\n')).hexdigest() != frozen['evaluator_sha256'][phase]:
        raise ValueError('frozen grouping source changed')
    allowed = {'targets', 'task_id', 'writer_component', 'prompt_component', 'source_event'}
    projected = json.loads(raw, object_pairs_hook=lambda pairs: {k: v for k, v in pairs if k in allowed})
    rows = projected['targets']
    if any(set(r) != allowed-{'targets'} or any(not isinstance(v, str) or not v for v in r.values()) for r in rows):
        raise ValueError('incomplete original group identity')
    if not rows or len({r['task_id'] for r in rows}) != len(rows):
        raise ValueError('empty or duplicated grouping roster')
    return {r['task_id']: r for r in rows}


def inputs(prepared, training, producer, policy_root, pilot):
    # Reproduce the actual development fit before reading evaluation metadata.
    fit = fitter.fit(prepared, training, producer, policy_root, pilot)
    policy = read(policy_root/'POLICY.json'); effort.verify_policy(policy)
    frozen = read(prepared/'FROZEN.json'); trained = read(training/'FROZEN.json')
    public = read(prepared/'evaluation-public.json')
    train = read(training/'train-public.json'); answers = read(training/'train-evaluator.json')
    if digest(public) != frozen['public_sha256']['evaluation'] or digest(train) != trained['public_sha256']['train'] or digest(answers) != trained['evaluator_sha256']['train']:
        raise ValueError('frozen evaluation or training input changed')
    groups = metadata(prepared, 'evaluation', frozen)
    development = metadata(prepared, 'development', frozen)
    training_groups = metadata(training, 'train', trained)
    tasks = [from_record(r) for r in public['tasks']]
    if not tasks or len({t.task_id for t in tasks}) != len(tasks) or set(groups) != {t.task_id for t in tasks}:
        raise ValueError('evaluation task/group join differs')
    for field in ('task_id', 'writer_component', 'prompt_component', 'source_event'):
        target = {r[field] for r in groups.values()}
        if target & {r[field] for r in [*development.values(), *training_groups.values()]}:
            raise ValueError('evaluation dependency overlaps fitting or training')
    reader = readers.Readers(train['tasks'], answers['targets'])
    for task in tasks:
        reader.binding(task, 'R0', 256)
    pins = {str(p): file_hash(p) for p in [prepared/'FROZEN.json', training/'FROZEN.json',
        prepared/'evaluation-public.json', prepared/'evaluation-evaluator.json',
        training/'train-public.json', training/'train-evaluator.json',
        policy_root/'POLICY.json', policy_root/'COMPLETE.json', policy_root/'MANIFEST.json']}
    return tasks, reader, groups, policy, fit, pins


def identity():
    return {**queue.identity(), 'runners/stage10/human_effort_fit.py': file_hash(Path(fitter.__file__)),
            'runners/stage10/human_effort_evaluation.py': file_hash(Path(__file__))}


def run(prepared, training, producer, policy_root, output, pilot):
    tasks, reader, groups, policy, fit, pins = inputs(prepared, training, producer, policy_root, pilot)
    manifest = {'schema': 'stage10.human-effort-evaluation.1', 'sources': identity(), 'inputs': pins,
                'reader_sources': reader.sources, 'fit_sha256': digest(fit), 'policy_sha256': policy['policy_sha256'],
                'task_ids': [t.task_id for t in tasks], 'groups': groups,
                'modes': ['fixed', 'confidence-only', 'benefit-cost'], 'mode_order': 'hash rank per task before outcomes',
                'evaluator_access': 'identity-only projection; correct-choice values discarded during decoding',
                'scope': 'historically exposed human records; prediction producer only'}
    output.mkdir(parents=True, exist_ok=True)
    if (output/'MANIFEST.json').exists():
        if read(output/'MANIFEST.json') != manifest:
            raise ValueError('human policy evaluation sources changed')
    else:
        write_new(output/'MANIFEST.json', manifest)
    complete = (output/'COMPLETE.json').exists()
    if not complete:
        if (output/'OWNER.json').exists() or GPU_LOCK.exists():
            raise RuntimeError('human evaluation GPU ownership requires inspection')
        owner = native_identity(os.getpid())
        if owner is None:
            raise RuntimeError('native worker identity unavailable')
        write_new(output/'OWNER.json', {'at': now(), 'native': owner})
        acquire_gpu_lock('stage10-human-effort-evaluation')
    rows = []
    try:
        for task in tasks:
            for mode in sorted(manifest['modes'], key=lambda m: digest(['stage10-human-effort-order', task.task_id, m])):
                if identity() != manifest['sources'] or reader.current_sources() != reader.sources or any(file_hash(Path(p)) != h for p, h in pins.items()):
                    raise ValueError('active human policy evaluation inputs changed')
                folder = output/'attempts'/task.task_id/mode
                if complete and not (folder/'COMPLETE.json').is_file():
                    raise ValueError('completed policy route missing; no new calls')
                result = effort.run(task, folder, policy, reader.initial, reader.additional, mode=mode,
                    group=groups[task.task_id]['writer_component'], reader_sources={**reader.sources, **manifest['sources']})
                rows.append({'task_id': task.task_id, 'mode': mode, 'status': result['status'], 'cost': result['cost'], 'route_sha256': digest(result)})
                if not complete:
                    status(output/'STATUS.json', {'at': now(), 'status': 'RUNNING', 'completed_routes': len(rows), 'planned_routes': 3*len(tasks), 'native': owner})
        result = {'at': now(), 'status': 'COMPLETE', 'manifest_sha256': digest(manifest), 'rows': rows,
                  'model_calls': sum(r['cost']['model_calls'] for r in rows), 'generated_tokens': sum(r['cost']['output_tokens'] for r in rows),
                  'evaluation_outcomes_used': False, 'scope': 'frozen policy predictions; no scientific comparison'}
        if complete:
            saved = read(output/'COMPLETE.json')
            if any(saved[k] != result[k] for k in result.keys()-{'at'}):
                raise ValueError('completed human policy evaluation differs')
            return saved
        write_new(output/'COMPLETE.json', result)
        status(output/'STATUS.json', {'at': now(), 'status': 'COMPLETE', 'completed_routes': len(rows)})
        return result
    finally:
        if not complete:
            release_gpu_lock()


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    for name in ('prepared', 'training', 'producer', 'policy-root', 'output', 'pilot'):
        p.add_argument('--'+name, type=Path, required=True)
    a = p.parse_args()
    try:
        run(a.prepared, a.training, a.producer, a.policy_root, a.output, a.pilot)
    except Exception as exc:
        if not (a.output/'FAILED.json').exists():
            write_new(a.output/'FAILED.json', {'at': now(), 'error': repr(exc)})
        raise
