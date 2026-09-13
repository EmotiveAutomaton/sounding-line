"""Whole human effort evaluation through constructed transport and real rules.

DESIGN CHECK: LESSONS3-5. Known-answer supported benefits buy execution;
unsupported or invalid initial strata stop. Evaluation outcomes cannot change
group projections or enter requests. Altered fits, cross-split dependencies and
corrupted attempts refuse. No live GPU lock or actual inference is used.
"""
from copy import deepcopy
from dataclasses import asdict
from pathlib import Path
from unittest.mock import patch
import argparse
import json
from . import human_effort_evaluation as evaluation, human_effort_queue as queue
from . import human_effort_readers as readers, human_memory_checks as fixtures
from .contracts import canonical, digest
from .ollama import now, write_new
from .queue import read


def run(output):
    output.mkdir(parents=True, exist_ok=False)
    prepared = output/'prepared'; prepared.mkdir()
    training, answers = fixtures.rows()
    for row in answers:
        row['prompt_component'] = 'train-prompt'
    dev = [fixtures.task(100, 2), fixtures.task(101, 10)]
    targets = [fixtures.task(200, 3), fixtures.task(201, 9)]
    records = {'train-public.json': {'tasks': training}, 'train-evaluator.json': {'targets': answers}}
    for phase, tasks in [('development', dev), ('evaluation', targets)]:
        records[phase+'-public.json'] = {'tasks': [asdict(t) for t in tasks]}
        labels = []
        for i, task in enumerate(tasks):
            correct = next(k for k, v in task.choices if v == readers.programs.DESCRIPTIONS['accept' if i == 0 else 'edit'])
            labels.append({'task_id': task.task_id, 'source_event': task.task_id,
                           'writer_component': phase+str(i), 'prompt_component': phase+'-prompt',
                           'correct_choice': correct, 'private_note': 'SENTINEL_EVALUATION_TRUTH' if phase == 'evaluation' else ''})
        records[phase+'-evaluator.json'] = {'targets': labels}
    frozen = {'public_sha256': {p: digest(records[p+'-public.json']) for p in ('train', 'development', 'evaluation')},
              'evaluator_sha256': {p: digest(records[p+'-evaluator.json']) for p in ('train', 'development', 'evaluation')}}
    records['FROZEN.json'] = frozen
    for name, value in records.items():
        write_new(prepared/name, value)
    pilot = output/'PILOT.json'
    write_new(pilot, {'status': 'PASS', 'sources': queue.identity(), 'training_sha256': digest(frozen),
                     'scope': 'constructed admission, never a literal scientific pilot'})
    checks = []; calls = []; executions = []; invalid = [False]
    original_execute = readers.programs.evaluate
    original_text = Path.read_text
    def guarded_text(p, *a, **kw):
        if p.name == 'evaluation-evaluator.json':
            raise AssertionError('outcome-bearing evaluation object access forbidden')
        return original_text(p, *a, **kw)
    def forbidden(*a, **kw):
        raise AssertionError('new inference/execution forbidden')
    def check(name, value):
        if not value:
            raise AssertionError(name)
        checks.append(name)
    def refuse(name, f):
        try:
            f()
        except ValueError:
            checks.append(name)
        else:
            raise AssertionError(name)
    def api(path, request):
        encoded = canonical(request)
        assert all(x not in encoded for x in ('SENTINEL_EVALUATION_TRUTH', 'writer_component', 'prompt_component', 'source_event'))
        body = json.loads(request['messages'][1]['content']); choices = body['task']['choices']; choice = choices[0]['id']
        if 'candidates' in request['format']['properties']:
            result = {'candidates': [{'goal_hypothesis': 'constructed', 'program': {'feature': 'draft_words', 'threshold': 6.5, 'below': 'accept', 'otherwise': 'edit'}}], 'choice': choice, 'insufficient_support': False}
        else:
            result = {'choice': choice, 'probabilities': {c['id']: .25 for c in choices}, 'insufficient_evidence': True, 'explanation': 'constructed no-information forecast'}
        calls.append(request)
        return {'fixture': 'constructed transport; no actual model inference', 'done': True, 'done_reason': 'stop',
                'message': {'content': '{}' if invalid[0] else canonical(result)}, 'eval_count': 100, 'prompt_eval_count': 1000,
                'total_duration': 1, 'load_duration': 0, 'prompt_eval_duration': 0, 'eval_duration': 1}
    def execute(*a):
        result = original_execute(*a); executions.append(result); return result
    producer = output/'development'; policy = output/'policy'; target = output/'evaluation'
    args = (prepared, prepared, producer, policy, pilot)
    def evaluate(destination=target):
        return evaluation.run(prepared, prepared, producer, policy, destination, pilot)
    with patch.object(Path, 'read_text', guarded_text), patch.object(readers.ollama, 'api', api), \
         patch.object(readers.ollama, 'identity', lambda: {'fixture': True}), patch.object(readers.programs, 'evaluate', execute), \
         patch.object(queue, 'GPU_LOCK', output/'unused-lock'), patch.object(queue, 'acquire_gpu_lock', lambda *a: None), \
         patch.object(queue, 'release_gpu_lock', lambda: None), patch.object(evaluation, 'GPU_LOCK', output/'unused-lock'), \
         patch.object(evaluation, 'acquire_gpu_lock', lambda *a: None), patch.object(evaluation, 'release_gpu_lock', lambda: None):
        queue.run(prepared, prepared, producer, 'development', pilot)
        first = evaluate()
        check('whole evaluation covers every task and policy', len(first['rows']) == 6 and first['model_calls'] == 14)
        for task in targets:
            for mode in ('fixed', 'confidence-only', 'benefit-cost'):
                route = read(target/'attempts'/task.task_id/mode/'ROUTE.json')
                check(mode+' dispatch '+task.task_id, route['decision']['route'] == ('R3' if mode == 'benefit-cost' else 'R1') and route['cost']['output_tokens'] <= 768)
        check('evaluation object never accessed and identity fields absent from all requests', len(calls) == 22)
        with patch.object(readers.ollama, 'api', forbidden), patch.object(readers.programs, 'evaluate', forbidden):
            check('entire completed evaluation replays without calls', evaluate() == first)
            raw = next(target.rglob('RAW.json')); saved = raw.read_bytes(); raw.write_bytes(b'{}')
            try:
                refuse('corrupt raw evidence refuses complete replay', evaluate)
            finally:
                raw.write_bytes(saved)
            check('restored original evidence replays', evaluate() == first)
            path = policy/'POLICY.json'; saved = path.read_bytes(); path.write_bytes(b'{}')
            try:
                with patch.object(evaluation, 'metadata', side_effect=AssertionError('metadata before fit validation')):
                    refuse('changed fit refuses before evaluation metadata', lambda: evaluation.inputs(*args))
            finally:
                path.write_bytes(saved)
            baseline = evaluation.metadata(prepared, 'evaluation', frozen)
            labels = deepcopy(records['evaluation-evaluator.json'])
            for row in labels['targets']:
                row['correct_choice'] = 'CHANGED_OUTCOME_CANARY'
            path = prepared/'evaluation-evaluator.json'; saved = path.read_bytes()
            changed = deepcopy(frozen); changed['evaluator_sha256']['evaluation'] = digest(labels)
            path.write_text(canonical(labels)+'\n', encoding='utf8', newline='\n')
            try:
                check('outcome changes cannot alter grouping projection', evaluation.metadata(prepared, 'evaluation', changed) == baseline)
                refuse('unfrozen label source refuses', lambda: evaluation.metadata(prepared, 'evaluation', frozen))
            finally:
                path.write_bytes(saved)
            for field in ('writer_component', 'prompt_component', 'source_event'):
                wrong = deepcopy(baseline)
                wrong[targets[0].task_id][field] = records['development-evaluator.json']['targets'][0][field]
                original_metadata = evaluation.metadata
                with patch.object(evaluation, 'metadata', lambda p, phase, f: wrong if phase == 'evaluation' else original_metadata(p, phase, f)):
                    refuse('cross-split '+field+' overlap refuses before calls', lambda: evaluation.inputs(*args))
        invalid[0] = True
        failed_predictions = evaluate(output/'invalid-evaluation')
        check('invalid forecasts retain all attempted policies and charges', len(failed_predictions['rows']) == 6 and all(r['status'] == 'INVALID' and r['cost']['model_calls'] >= 1 for r in failed_predictions['rows']))
    result = {'at': now(), 'status': 'PASS', 'sources': evaluation.identity(), 'checks': checks,
              'constructed_transport_responses': len(calls), 'actual_model_calls': 0,
              'actual_executor_evaluations': sum(e['executor_evaluations'] for e in executions),
              'scope': 'constructed end-to-end human policy evaluation; no scientific result'}
    write_new(output/'COMPLETE.json', result)
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    try:
        print(canonical(run(args.output)))
    except Exception as exc:
        write_new(args.output/'FAILED.json', {'at': now(), 'error': repr(exc)})
        raise
