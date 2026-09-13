"""Storage-matched retrieval and human procedure-memory prediction routes.

DESIGN CHECK: LESSONS2-5. NULL/ALTERNATIVE keep all invalid rows and costs; no
uniform fallback. Exact task/view, training inputs, rules and source versions
bind every attempt. A discarded literal pilot admits science, never accuracy.
Two R4 calls share the original 768-token budget; R1 uses one 768-token call.
Known-answer and completed no-call replay precede the actual model pilot.
"""
from __future__ import annotations
import argparse
import hashlib
import os
from pathlib import Path
import time
from . import human_memory as memory, human_programs as programs, human_memory_proposal as proposal, human_routes, ollama
from .contracts import canonical, digest, parse_forecast
from .queue import read, status, native_identity
from .reader import from_record
from soundingline.gpulock import GPU_LOCK, acquire_gpu_lock, release_gpu_lock

ARMS = ('R1-memory', 'R4-opaque', 'R4-grounded')
PILOT_SCOPE = 'discarded legacy pilot writer, excluded from the scientific cohort'
FEEDBACK_BYTES = 4096


def identity():
    return {**human_routes.identity(), **memory.identity(),
            'runners/stage10/human_memory_proposal.py': hashlib.sha256(Path(proposal.__file__).read_bytes()).hexdigest(),
            'runners/stage10/human_memory_routes.py': hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}


def representation_for(task, training, answers, learned, arm, *, profile=None):
    started = time.perf_counter()
    # Charge a common allowance derived from the larger structured request,
    # reserving feedback before selecting memory. No target evidence is removed.
    base = proposal.request_for(task, **ollama.profile_kwargs(profile))
    used = sum(len(m['content'].encode('utf8')) for m in base['messages'])
    cap = min(memory.STORE_BYTES, 16384 - used - 384 - 512 - FEEDBACK_BYTES - 128)
    if cap <= 0:
        raise ValueError('target leaves no safe memory/refinement allowance')
    # Pack the longer grounded representation for BOTH naming conditions, so
    # names cannot alter selected definitions or concrete episodes.
    selected_arm = 'R4-grounded' if arm.startswith('R4-') else arm
    rep, receipt = memory.represent(task, training, answers, learned, selected_arm)
    removed = []
    while len(canonical(rep).encode('utf8')) > cap:
        if rep['examples']:
            rep['examples'].pop(); removed.append(receipt['selected_ids'].pop())
        elif rep['procedures']:
            rep['procedures'].pop()
        else:
            raise ValueError('even empty representation exceeds target allowance')
    if arm == 'R4-opaque':
        rep['procedures'] = [{k: v for k,v in p.items() if k != 'description'} if profile is not None
                             else {k: p[k] for k in ('id', 'program')} for p in rep['procedures']]
    receipt.update(arm=arm, context_removed_ids=removed, effective_store_limit_bytes=cap,
                   reserved_feedback_bytes=FEEDBACK_BYTES, store_bytes=len(canonical(rep).encode('utf8')),
                   representation_sha256=digest(rep))
    receipt['exception_ids'] = [i for i in receipt['exception_ids'] if i in receipt['selected_ids']]
    receipt['wall_seconds'] = time.perf_counter() - started
    return rep, receipt


def route(task, output, arm, training, answers, learned, *, profile=None):
    representation, retrieval = representation_for(task, training, answers, learned, arm, **ollama.profile_kwargs(profile))
    binding = ollama.bind_route({'sources': identity(), 'task': task.public(), 'task_id': task.task_id, 'arm': arm,
                      'representation': representation, 'training': digest(training), 'answers': digest(answers), 'memory': digest(learned)}, profile)
    if (output/'COMPLETE.json').exists():
        saved = read(output/'COMPLETE.json')
        if saved['binding'] != binding:
            raise ValueError('human memory route binding changed')
        for relative, expected in saved['files'].items():
            p = output/relative
            if not p.resolve().is_relative_to(output.resolve()) or hashlib.sha256(p.read_bytes()).hexdigest() != expected:
                raise ValueError('human memory retained route changed')
        return read(output/'ROUTE.json')
    output.mkdir(parents=True, exist_ok=False)
    ollama.write_new(output/'INPUT.json', {'binding': binding, 'task': task.public(), 'representation': representation,
                                         'retrieval': retrieval, 'sources': identity()})
    start = time.perf_counter(); calls = []; executions = []; feedback = None
    if arm == 'R1-memory':
        attempt = ollama.call(task, output/'direct', examples=representation['examples'], context_tokens=16384, **ollama.profile_kwargs(profile),
                              instruction='Predict directly using these fixed concrete training episodes. No induced procedures are supplied.')
        calls.append(attempt); forecast = attempt['forecast']; state = attempt['status']
    else:
        for round_number in (1, 2):
            directory = output/('round-' + str(round_number))
            attempt = proposal.call(task, directory/'proposal', feedback, representation, **ollama.profile_kwargs(profile))
            calls.append(attempt)
            if attempt['status'] != 'VALID':
                break
            feedback = programs.evaluate(task, attempt['proposal']['candidates'])
            if len(canonical(feedback).encode('utf8')) > FEEDBACK_BYTES:
                raise ValueError('execution feedback exceeded reserved context allowance')
            executions.append(feedback); ollama.write_new(directory/'EXECUTION.json', feedback)
        state = 'INVALID'; forecast = None
        if len(calls) == 2 and calls[-1]['status'] == 'VALID':
            forecast = {'choice': calls[-1]['proposal']['choice'], 'probabilities': feedback['probabilities'],
                        'insufficient_evidence': calls[-1]['proposal']['insufficient_support'],
                        'explanation': 'Equal mixture of executed rules conditioned on permitted training procedures and concrete memory.'}
            parse_forecast(canonical(forecast), task); state = 'VALID'
    generated = sum(c['cost']['eval_count'] for c in calls)
    if generated > 768:
        raise ValueError('memory route exceeded common generated-token allowance')
    result = {'at': ollama.now(), 'binding': binding, 'task_id': task.task_id, 'arm': arm, 'status': state,
              'forecast': forecast, 'model_calls': len(calls), 'generated_tokens': generated,
              'input_tokens': sum(c['cost']['prompt_eval_count'] for c in calls),
              'reasoning_tokens': None, 'reasoning_tokens_status': 'not separately exposed',
              'executor_evaluations': sum(e['executor_evaluations'] for e in executions),
              'wall_seconds': time.perf_counter()-start+retrieval['wall_seconds'],
              'representation_seconds': retrieval['wall_seconds'], 'store_bytes': retrieval['store_bytes'],
              'target_outcomes_opened': False, 'readout': 'elicited vector' if arm == 'R1-memory' else 'equal executed-rule mixture with fixed 0.15 lapse'}
    ollama.write_new(output/'ROUTE.json', result)
    ollama.write_new(output/'COMPLETE.json', {'at': ollama.now(), 'binding': binding,
        'files': {p.relative_to(output).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in output.rglob('*') if p.is_file()}})
    return result


def inputs(training_root, memory_root):
    frozen = read(training_root/'FROZEN.json')
    public = read(training_root/'train-public.json'); labels = read(training_root/'train-evaluator.json')
    learned = read(memory_root/'MEMORY.json')
    if learned['manifest'] != {'sources': memory.identity(), 'frozen_sha256': digest(frozen)}:
        raise ValueError('human memory fit source changed')
    if digest(public) != frozen['public_sha256']['train'] or digest(labels) != frozen['evaluator_sha256']['train']:
        raise ValueError('training inputs changed')
    if digest(public['tasks']) != learned['training_sha256'] or digest(labels['targets']) != learned['answers_sha256']:
        raise ValueError('memory was fitted on a different training pool')
    return public['tasks'], labels['targets'], learned


def run(prepared, training_root, memory_root, output, phases, pilot=None):
    if phases not in [('pilot',), ('development', 'evaluation')]:
        raise ValueError('undeclared memory queue phases')
    frozen = read(prepared/'FROZEN.json'); training, answers, learned = inputs(training_root, memory_root)
    if phases == ('pilot',):
        if frozen.get('scope') != PILOT_SCOPE:
            raise ValueError('memory pilot requires excluded writer')
    else:
        admission = read(pilot) if pilot is not None else {}
        if admission.get('status') != 'PASS' or admission.get('sources') != identity() or admission.get('memory_sha256') != digest(learned):
            raise ValueError('source-bound literal memory pilot required')
    tasks = []; public_hashes = {}
    for phase in phases:
        lane = 'development' if phase == 'pilot' else phase
        public = read(prepared/(lane+'-public.json'))
        if digest(public) != frozen['public_sha256'][lane]:
            raise ValueError('memory target source changed')
        current = [from_record(r) for r in public['tasks']]
        if not current or len({t.task_id for t in current}) != len(current):
            raise ValueError('empty or duplicate target cohort')
        for task in current:
            programs.features(task)
            if task.task_id in {r['task_id'] for r in training}:
                raise ValueError('target in global training')
        tasks.extend((phase, t) for t in current); public_hashes[phase] = digest(public)
    manifest = {'sources': identity(), 'frozen_sha256': digest(frozen), 'public_sha256': public_hashes,
                'memory_sha256': digest(learned), 'training_sha256': digest(training), 'answers_sha256': digest(answers),
                'phases': list(phases), 'arms': list(ARMS), 'planned_routes': len(tasks)*len(ARMS),
                'maximum_model_calls': len(tasks)*5, 'maximum_generated_tokens_per_route': 768,
                'common_store_bytes': memory.STORE_BYTES, 'target_outcomes_opened': False}
    output.mkdir(parents=True, exist_ok=True)
    if (output/'MANIFEST.json').exists():
        if read(output/'MANIFEST.json') != manifest:
            raise ValueError('memory queue manifest changed')
    else:
        ollama.write_new(output/'MANIFEST.json', manifest)
    complete = (output/'COMPLETE.json').exists()
    if not complete:
        if (output/'OWNER.json').exists() or GPU_LOCK.exists():
            raise RuntimeError('memory queue ownership recovery requires inspection')
        owner = native_identity(os.getpid())
        if owner is None:
            raise RuntimeError('native memory worker unavailable')
        ollama.write_new(output/'OWNER.json', {'at': ollama.now(), 'native': owner})
        acquire_gpu_lock('stage10-human-memory')
    rows = []
    try:
        for phase, task in tasks:
            for arm in ARMS:
                if identity() != manifest['sources']:
                    raise ValueError('active memory source changed')
                directory = output/'attempts'/digest([phase, task.task_id, arm])[:32]
                if complete and not (directory/'COMPLETE.json').exists():
                    raise ValueError('completed memory row missing; no new calls')
                r = route(task, directory, arm, training, answers, learned)
                rows.append({k: r[k] for k in ('task_id', 'arm', 'status', 'model_calls', 'generated_tokens', 'executor_evaluations', 'wall_seconds')})
                rows[-1].update(phase=phase, sha256=digest(r))
                if not complete:
                    status(output/'STATUS.json', {'at': ollama.now(), 'status': 'RUNNING', 'phase': phase,
                                                  'completed_routes': len(rows), 'planned_routes': manifest['planned_routes'], 'native': owner})
        result = {'at': ollama.now(), 'status': 'COMPLETE', 'manifest_sha256': digest(manifest), 'rows': rows,
                  'model_calls': sum(r['model_calls'] for r in rows), 'generated_tokens': sum(r['generated_tokens'] for r in rows),
                  'fit_cost': {k: learned[k] for k in ('wall_seconds', 'executor_evaluations', 'model_calls')},
                  'fit_charge': 'shared setup cost counted once, not per task or arm', 'target_outcomes_opened': False}
        if complete:
            saved = read(output/'COMPLETE.json')
            if any(saved[k] != result[k] for k in result.keys()-{'at'}):
                raise ValueError('completed memory producer does not reproduce')
            return saved
        ollama.write_new(output/'COMPLETE.json', result)
        status(output/'STATUS.json', {'at': ollama.now(), 'status': 'COMPLETE', 'completed_routes': len(rows)})
        return result
    finally:
        if not complete:
            release_gpu_lock()


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    for name in ('prepared', 'training', 'memory', 'output'):
        p.add_argument('--'+name, type=Path, required=True)
    p.add_argument('--phase', choices=['pilot', 'science'], required=True); p.add_argument('--pilot', type=Path)
    a = p.parse_args()
    try:
        run(a.prepared, a.training, a.memory, a.output, ('pilot',) if a.phase == 'pilot' else ('development', 'evaluation'), a.pilot)
    except Exception as exc:
        if not (a.output/'FAILED.json').exists():
            ollama.write_new(a.output/'FAILED.json', {'at': ollama.now(), 'error': repr(exc)})
        raise
