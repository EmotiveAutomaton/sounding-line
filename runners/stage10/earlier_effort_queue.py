"""Reserved-budget human pilot/development producer; no target labels opened.

DESIGN CHECK: LESSONS3-5. Source-bound literal admission precedes development.
Under NULL and ALTERNATIVE all attempts remain charged, malformed forecasts stay
invalid, changed training/target/implementation sources refuse. Complete replay
never makes new calls; interrupted ownership requires explicit inspection.
"""
from __future__ import annotations
import argparse
import hashlib
import os
from pathlib import Path
from runners.stage9.process_identity import native_identity
from soundingline.gpulock import GPU_LOCK, acquire_gpu_lock, release_gpu_lock
from . import earlier_effort_readers as readers, earlier_effort_source as source
from .contracts import digest
from .ollama import now, write_new
from .queue import read, status
from .reader import from_record

PILOT_SCOPE = 'discarded legacy pilot writer, excluded from the scientific cohort'


def identity():
    return {**readers.identity(), 'runners/stage10/earlier_effort_source.py': source.sha(source.__file__), 'runners/stage10/earlier_effort_queue.py': hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}


def inputs(prepared, training, phase, pilot=None):
    if phase not in {'pilot', 'development'}:
        raise ValueError('reserved development producer cannot open evaluation')
    frozen = source.verify(prepared); trained = source.verify(training)
    public = read(prepared/'development-public.json')
    train = read(training/'train-public.json'); answers = read(training/'train-evaluator.json')
    if digest(public) != frozen['public_sha256']['development'] or digest(train) != trained['public_sha256']['train'] or digest(answers) != trained['evaluator_sha256']['train']:
        raise ValueError('frozen human effort inputs changed')
    if phase == 'pilot':
        if frozen.get('scope') != PILOT_SCOPE:
            raise ValueError('excluded pilot writer required')
    else:
        admission = read(pilot) if pilot is not None else {}
        if admission.get('status') != 'PASS' or admission.get('sources') != identity() or admission.get('training_sha256') != digest(trained):
            raise ValueError('literal human effort pilot required for this source and training')
    tasks = [from_record(r) for r in public['tasks']]
    if not tasks or len({t.task_id for t in tasks}) != len(tasks):
        raise ValueError('empty or duplicated task roster')
    reader = readers.Readers(train['tasks'], answers['targets'])
    for task in tasks:
        reader.binding(task, 'R0', 256)
    return tasks, reader, frozen, trained, public


def run(prepared, training, output, phase, pilot=None):
    tasks, reader, frozen, trained, public = inputs(prepared, training, phase, pilot)
    manifest = {'schema': 'stage10.earlier-effort-producer.1', 'sources': identity(), 'readers': reader.sources,
                'prepared_sha256': digest(frozen), 'training_sha256': digest(trained), 'public_sha256': digest(public),
                'phase': phase, 'task_ids': [t.task_id for t in tasks], 'route_allowances': {'R0': 256, 'R1': 512, 'R3': [256, 256]},
                'scope': 'budget-reserved development predictions; no outcome access or scientific comparison'}
    output.mkdir(parents=True, exist_ok=True)
    if (output/'MANIFEST.json').exists():
        if read(output/'MANIFEST.json') != manifest:
            raise ValueError('human effort manifest changed')
    else:
        write_new(output/'MANIFEST.json', manifest)
    complete = (output/'COMPLETE.json').exists()
    if not complete:
        if (output/'OWNER.json').exists() or GPU_LOCK.exists():
            raise RuntimeError('human effort ownership requires inspection')
        owner = native_identity(os.getpid())
        if owner is None:
            raise RuntimeError('native worker identity unavailable')
        write_new(output/'OWNER.json', {'at': now(), 'native': owner})
        acquire_gpu_lock('stage10-earlier-effort-'+phase)
    rows = []
    try:
        for task in tasks:
            for arm, callback, allowance in [('R0', reader.initial, 256), ('R1', reader.retrieval, 512), ('R3', reader.structured, 512)]:
                if identity() != manifest['sources'] or reader.current_sources() != reader.sources:
                    raise ValueError('active human effort sources changed')
                directory = output/'attempts'/task.task_id/arm
                if complete and not (directory/'BUDGET_ATTEMPT.json').exists():
                    raise ValueError('completed budget attempt missing; no new calls')
                result = callback(task, directory, allowance)
                rows.append({'task_id': task.task_id, 'arm': arm, 'status': result['status'], 'cost': result['cost'], 'attempt_sha256': digest(result)})
                if not complete:
                    status(output/'STATUS.json', {'at': now(), 'status': 'RUNNING', 'completed_routes': len(rows), 'planned_routes': 3*len(tasks), 'native': owner})
        result = {'at': now(), 'status': 'COMPLETE', 'phase': phase, 'rows': rows, 'manifest_sha256': digest(manifest),
                  'model_calls': sum(r['cost']['model_calls'] for r in rows), 'generated_tokens': sum(r['cost']['output_tokens'] for r in rows),
                  'target_outcomes_opened': False, 'scope': 'prediction producer only; scientific comparison pending'}
        if complete:
            saved = read(output/'COMPLETE.json')
            if any(saved[k] != result[k] for k in result.keys()-{'at'}):
                raise ValueError('human effort completed producer differs')
            return saved
        write_new(output/'COMPLETE.json', result)
        status(output/'STATUS.json', {'at': now(), 'status': 'COMPLETE', 'completed_routes': len(rows)})
        return result
    finally:
        if not complete:
            release_gpu_lock()


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    for name in ('prepared', 'training', 'output'):
        p.add_argument('--'+name, type=Path, required=True)
    p.add_argument('--phase', choices=['pilot', 'development'], required=True); p.add_argument('--pilot', type=Path)
    a = p.parse_args()
    try:
        run(a.prepared, a.training, a.output, a.phase, a.pilot)
    except Exception as exc:
        if not (a.output/'FAILED.json').exists():
            write_new(a.output/'FAILED.json', {'at': now(), 'error': repr(exc)})
        raise
