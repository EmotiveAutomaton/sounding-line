"""Constructed human effort queue, actual execution and policy integration.

DESIGN CHECK: LESSONS3-5. NULL: unsupported single-writer benefit stops; an
invalid proposal remains charged. ALTERNATIVE: supported gain buys the actual
rule route. Changed retained data and training pools refuse, with no inference
during replay. Fixtures never use the live GPU lock or real model transport.
"""
from copy import deepcopy
from dataclasses import asdict
from pathlib import Path
from unittest.mock import patch
import argparse
import json
from . import effort, human_effort_queue as queue, human_effort_readers as readers
from . import human_memory_checks as fixtures
from .contracts import canonical, digest
from .ollama import now, write_new
from .queue import read


def run(output):
    output.mkdir(parents=True, exist_ok=False)
    prepared = output/'prepared'; prepared.mkdir()
    training, answers = fixtures.rows()
    tasks = [fixtures.task(100, 2), fixtures.task(101, 10)]
    records = {'train-public.json': {'tasks': training}, 'train-evaluator.json': {'targets': answers},
               'development-public.json': {'tasks': [asdict(t) for t in tasks]}}
    records['FROZEN.json'] = {'scope': queue.PILOT_SCOPE,
        'public_sha256': {'train': digest(records['train-public.json']), 'development': digest(records['development-public.json'])},
        'evaluator_sha256': {'train': digest(records['train-evaluator.json'])}}
    for name, value in records.items():
        write_new(prepared/name, value)
    calls = []; executions = []; checks = []; malformed = [False]
    original_execute = readers.programs.evaluate
    def api(path, request):
        body = json.loads(request['messages'][1]['content']); choices = body['task']['choices']; choice = choices[0]['id']
        if 'candidates' in request['format']['properties']:
            candidate = {'goal_hypothesis': 'constructed', 'program': {'feature': 'draft_words', 'threshold': 6.5, 'below': 'accept', 'otherwise': 'edit'}}
            response = {'candidates': [candidate, candidate] if malformed[0] else [candidate], 'choice': choice, 'insufficient_support': False}
        else:
            response = {'choice': choice, 'probabilities': {c['id']: .25 for c in choices}, 'insufficient_evidence': True, 'explanation': 'constructed no-information forecast'}
        calls.append(request)
        return {'fixture': 'constructed transport, no actual model inference', 'done': True, 'done_reason': 'stop',
                'message': {'content': canonical(response)}, 'eval_count': 100, 'prompt_eval_count': 1000,
                'total_duration': 1, 'load_duration': 0, 'prompt_eval_duration': 0, 'eval_duration': 1}
    def execute(*a):
        result = original_execute(*a); executions.append(result); return result
    def forbidden(*a, **kw):
        raise AssertionError('transport/execution forbidden on replay')
    def check(name, value):
        if not value:
            raise AssertionError(name)
        checks.append(name)
    def refuse(name, callback):
        try:
            callback()
        except ValueError:
            checks.append(name)
        else:
            raise AssertionError(name)
    with patch.object(readers.ollama, 'api', api), patch.object(readers.ollama, 'identity', lambda: {'fixture': True}), \
         patch.object(readers.programs, 'evaluate', execute), patch.object(queue, 'GPU_LOCK', output/'unused-fixture-lock'), \
         patch.object(queue, 'acquire_gpu_lock', lambda *a: None), patch.object(queue, 'release_gpu_lock', lambda: None):
        first = queue.run(prepared, prepared, output/'queue', 'pilot')
        check('whole queue preserves all reserved routes and budgets', len(first['rows']) == 6 and len(calls) == 8 and all(r['status'] == 'VALID' for r in first['rows']))
        check('actual rule evaluations charged', sum(r['cost']['executor_evaluations'] for r in first['rows']) == 4)
        check('literal request budgets reserved', [r['options']['num_predict'] for r in calls] == [256, 512, 256, 256]*2)
        with patch.object(readers.ollama, 'api', forbidden), patch.object(readers.programs, 'evaluate', forbidden):
            check('completed queue replays without calls or execution', queue.run(prepared, prepared, output/'queue', 'pilot') == first)
            raw = next((output/'queue').rglob('RAW.json')); original = raw.read_bytes(); raw.write_text('{}', encoding='utf8')
            try:
                refuse('corrupted raw refuses reuse', lambda: queue.run(prepared, prepared, output/'queue', 'pilot'))
            finally:
                raw.write_bytes(original)
            check('restored original raw replays', queue.run(prepared, prepared, output/'queue', 'pilot') == first)
        reader = readers.Readers(training, answers)
        malformed[0] = True
        invalid = reader.structured(tasks[0], output/'invalid', 512)
        check('duplicate program invalid with actual cost and no executor', invalid['status'] == 'INVALID' and invalid['forecast'] is None and invalid['cost']['model_calls'] == 1 and invalid['cost']['output_tokens'] == 100 and invalid['cost']['executor_evaluations'] == 0)
        malformed[0] = False
        rows = []
        for i, task in enumerate(tasks):
            routes = {arm: read(output/'queue/attempts'/task.task_id/arm/'BUDGET_ATTEMPT.json')['result'] for arm in ('R0', 'R1', 'R3')}
            rows.append({'task': asdict(task), 'group': str(i), 'truth': max(routes['R3']['forecast']['probabilities'], key=routes['R3']['forecast']['probabilities'].get), 'routes': routes})
        bundle = {'schema': 'stage10.effort-development.1', 'phase': 'development', 'complete': True, 'producers': {'constructed': digest(first)}, 'rows': rows}
        learned = effort.fit(bundle)
        check('supported constructed improvement admits executable route', any(c['route'] == 'R3' and c['admitted'] for c in learned['policy']['cells']))
        unsupported = deepcopy(bundle)
        for row in unsupported['rows']:
            row['group'] = 'only-writer'
        stopped = effort.fit(unsupported)
        check('single-writer development admits no learned route', not any(c['admitted'] for c in stopped['policy']['cells']))
        task = fixtures.task(200, 2)
        for mode in ('fixed', 'confidence-only', 'benefit-cost'):
            result = effort.run(task, output/mode, learned, reader.initial, reader.additional, mode=mode, group='reserved', reader_sources=reader.sources)
            expected = 'R3' if mode == 'benefit-cost' else 'R1'
            check('actual controller dispatch '+mode, result['decision']['route'] == expected and result['cost']['output_tokens'] <= 768)
            with patch.object(readers.ollama, 'api', forbidden), patch.object(readers.programs, 'evaluate', forbidden):
                check('actual controller no-call replay '+mode, effort.run(task, output/mode, learned, reader.initial, reader.additional, mode=mode, group='reserved', reader_sources=reader.sources) == result)
        result = effort.run(task, output/'unsupported', stopped, reader.initial, reader.additional, group='reserved', reader_sources=reader.sources)
        check('unsupported policy actually stops after initial', result['decision']['route'] == 'R0' and result['cost']['model_calls'] == 1)
        reader.training[0]['evidence']['document'] += 'changed'
        refuse('mutated training pool rejected', lambda: reader.initial(task, output/'mutated', 256))
        refuse('uncommissioned evaluation phase refused', lambda: queue.inputs(prepared, prepared, 'evaluation'))
    result = {'at': now(), 'status': 'PASS', 'sources': queue.identity(), 'checks': checks,
              'constructed_transport_responses': len(calls), 'actual_model_calls': 0,
              'actual_executor_evaluations': sum(e['executor_evaluations'] for e in executions),
              'scope': 'constructed instrument and actual queue/controller integration; literal model pilot still required'}
    write_new(output/'COMPLETE.json', result)
    return result


if __name__ == '__main__':
    p = argparse.ArgumentParser(); p.add_argument('--output', type=Path, required=True)
    args = p.parse_args()
    try:
        print(canonical(run(args.output)))
    except Exception as exc:
        write_new(args.output/'FAILED.json', {'at': now(), 'error': repr(exc)})
        raise
