"""Discarded whole-queue checks using constructed model responses.

DESIGN CHECK: LESSONS2-5. All routes must preserve response/execution/cost records
and replay without transport or executor calls. Missing evidence and corrupted
raw output must refuse under NULL and ALTERNATIVE. No scientific labels used.
"""
import argparse
from dataclasses import asdict
from pathlib import Path
from . import human_memory as memory, human_memory_checks as fixtures, human_memory_routes as routes
from .contracts import canonical, digest
from .ollama import now, write_new
from .queue import read


def run(output):
    output.mkdir(parents=True, exist_ok=False)
    prepared = output/'prepared'; prepared.mkdir()
    training, answers = fixtures.rows()
    tasks = [asdict(fixtures.task(100, 2)), asdict(fixtures.task(101, 10))]
    records = {'train-public.json': {'tasks': training}, 'train-evaluator.json': {'targets': answers},
               'development-public.json': {'tasks': tasks}}
    records['FROZEN.json'] = {'scope': routes.PILOT_SCOPE,
        'public_sha256': {'train': digest(records['train-public.json']), 'development': digest(records['development-public.json'])},
        'evaluator_sha256': {'train': digest(records['train-evaluator.json'])}}
    for name, value in records.items():
        write_new(prepared/name, value)
    learned = memory.fit(prepared, output/'memory')
    old = (routes.ollama.api, routes.ollama.identity, routes.GPU_LOCK, routes.acquire_gpu_lock, routes.release_gpu_lock, routes.programs.evaluate)
    calls = []; executions = []
    def api(path, request):
        import json
        body = json.loads(request['messages'][1]['content']); choices = body['task']['choices']; choice = choices[0]['id']
        if 'candidates' in request['format']['properties']:
            response = {'candidates': [{'goal_hypothesis': 'constructed handling hypothesis', 'program': {'feature': 'draft_words', 'threshold': 6.5, 'below': 'accept', 'otherwise': 'edit'}}], 'choice': choice, 'insufficient_support': False}
        else:
            response = {'choice': choice, 'probabilities': {c['id']: .25 for c in choices}, 'insufficient_evidence': True, 'explanation': 'constructed no-information forecast'}
        calls.append(request)
        return {'fixture': 'constructed response; no actual model inference', 'done': True, 'done_reason': 'stop',
                'message': {'content': canonical(response)}, 'eval_count': 100, 'prompt_eval_count': 1000,
                'total_duration': 1, 'load_duration': 0, 'prompt_eval_duration': 0, 'eval_duration': 1}
    def evaluate(*args):
        result = old[-1](*args); executions.append(result); return result
    def forbidden(*args, **kwargs):
        raise AssertionError('unexpected transport or executor during completed replay')
    try:
        routes.ollama.api = api; routes.ollama.identity = lambda: {'fixture': True}
        routes.GPU_LOCK = output/'unused-fixture-lock'; routes.acquire_gpu_lock = lambda *a: None; routes.release_gpu_lock = lambda: None
        routes.programs.evaluate = evaluate
        first = routes.run(prepared, prepared, output/'memory', output/'queue', ('pilot',))
        assert len(first['rows']) == 6 and len(calls) == 10 and len(executions) == 8
        assert all(r['status'] == 'VALID' for r in first['rows'])
        routes.ollama.api = forbidden; routes.programs.evaluate = forbidden
        assert routes.run(prepared, prepared, output/'memory', output/'queue', ('pilot',)) == first
        raw = next((output/'queue').rglob('RAW.json')); original = raw.read_bytes()
        raw.write_text('{}', encoding='utf8')
        try:
            try:
                routes.run(prepared, prepared, output/'memory', output/'queue', ('pilot',))
            except ValueError:
                pass
            else:
                raise AssertionError('corrupt raw accepted')
        finally:
            raw.write_bytes(original)
        assert routes.run(prepared, prepared, output/'memory', output/'queue', ('pilot',)) == first
    finally:
        (routes.ollama.api, routes.ollama.identity, routes.GPU_LOCK, routes.acquire_gpu_lock, routes.release_gpu_lock, routes.programs.evaluate) = old
    result = {'at': now(), 'status': 'PASS', 'sources': routes.identity(), 'memory_sha256': digest(learned),
              'checks': ['all three routes through whole producer', 'actual rule execution', 'complete no-call replay', 'raw corruption refusal', 'restored original raw replays'],
              'constructed_transport_responses': len(calls), 'actual_model_calls': 0,
              'actual_executor_evaluations': sum(e['executor_evaluations'] for e in executions),
              'scope': 'constructed route integration only; actual discarded model pilot required'}
    write_new(output/'COMPLETE.json', result)
    return result


if __name__ == '__main__':
    p = argparse.ArgumentParser(); p.add_argument('--output', type=Path, required=True)
    print(canonical(run(p.parse_args().output)))
