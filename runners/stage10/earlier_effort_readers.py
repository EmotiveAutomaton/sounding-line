"""Earlier-draft R5 callbacks using the existing 256 + 512 token reservation.

DESIGN CHECK: LESSONS sections 3-5; READER_HEURISTICS sections 4, 5, 10.
NULL: extra effort with no benefit remains costly; invalid proposals retain
their cost and absent forecast. ALTERNATIVE: a proposed rule executes on actual
public features. Training-source changes and corrupted raw evidence refuse
reuse. No full-budget historical prediction substitutes for these requests.
"""
from __future__ import annotations
import hashlib
import time
from pathlib import Path
from . import effort, earlier_effort_proposal as proposal, earlier_programs as programs, ollama
from .contracts import canonical, digest, parse_forecast
from .earlier_routes import identity as human_identity
from .queue import read
from .reader import build, from_record


def identity():
    names = ('effort.py', 'earlier_effort_proposal.py', 'human_memory_proposal.py', 'earlier_effort_readers.py')
    return {**human_identity(), **{'runners/stage10/'+n: hashlib.sha256(Path(__file__).with_name(n).read_bytes()).hexdigest() for n in names}}


def cached(output, binding, task, allowance):
    path = output/'BUDGET_ATTEMPT.json'
    if not path.exists():
        return None
    saved = read(path)
    if saved['binding'] != binding:
        raise ValueError('human reserved-budget input changed')
    for relative, expected in saved['files'].items():
        p = output/relative
        if not p.resolve().is_relative_to(output.resolve()) or hashlib.sha256(p.read_bytes()).hexdigest() != expected:
            raise ValueError('human reserved-budget retained evidence changed')
    effort.check_attempt(task, saved['result'], allowance)
    return saved['result']


def finish(task, output, binding, allowance, state, forecast, calls, executions, start):
    result = {'status': state, 'forecast': forecast, 'evidence_sha256': digest(task.public()),
              'maximum_generated_tokens': allowance,
              'cost': {'wall_seconds': time.perf_counter()-start, 'model_calls': len(calls),
                       'input_tokens': sum(c['cost']['prompt_eval_count'] for c in calls),
                       'output_tokens': sum(c['cost']['eval_count'] for c in calls),
                       'executor_evaluations': sum(e['executor_evaluations'] for e in executions),
                       'reasoning_tokens': None, 'reasoning_tokens_status': 'not separately exposed'}}
    effort.check_attempt(task, result, allowance)
    files = {p.relative_to(output).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in output.rglob('*') if p.is_file()}
    ollama.write_new(output/'BUDGET_ATTEMPT.json', {'at': ollama.now(), 'binding': binding, 'result': result, 'files': files,
                      'wall_scope': 'entire callback including retrieval, model service, actual rule execution and local overhead'})
    return result


class Readers:
    def __init__(self, training, answers):
        ids = [r['task_id'] for r in training]
        if not ids or len(set(ids)) != len(ids) or len(answers) != len(ids) or {r['task_id'] for r in answers} != set(ids):
            raise ValueError('training examples and answers must join uniquely')
        for row in training:
            programs.features(from_record(row))
        self.training, self.answers = training, answers
        self.sources = self.current_sources()

    def current_sources(self):
        return {**identity(), 'training-public': digest(self.training), 'training-answers': digest(self.answers)}

    def binding(self, task, arm, allowance):
        programs.features(task)
        if self.current_sources() != self.sources or task.task_id in {r['task_id'] for r in self.training}:
            raise ValueError('frozen training changed or target in training')
        return digest({'task': task.public(), 'task_id': task.task_id, 'arm': arm, 'allowance': allowance, 'sources': self.sources})

    def direct(self, task, output, allowance, arm):
        if arm not in {'R0', 'R1'} or allowance != (256 if arm == 'R0' else 512):
            raise ValueError('human reserved direct budget changed')
        binding = self.binding(task, arm, allowance)
        saved = cached(output, binding, task, allowance)
        if saved is not None:
            return saved
        start = time.perf_counter()
        kwargs, retrieval = build(task, arm, self.training, self.answers)
        output.mkdir(parents=True, exist_ok=False)
        ollama.write_new(output/'RETRIEVAL.json', retrieval)
        result = ollama.call(task, output/'call', generated_tokens=allowance, **kwargs)
        raw = read(output/'call/RAW.json')
        state, forecast = 'INVALID', None
        try:
            if raw.get('done') is not True or raw.get('done_reason') != 'stop':
                raise ValueError('incomplete response')
            forecast = parse_forecast(raw['message']['content'], task); state = 'VALID'
        except (ValueError, TypeError, KeyError):
            pass
        if result['status'] != state or result['forecast'] != forecast or result['cost'] != {k: raw.get(k) for k in result['cost']}:
            raise ValueError('human direct raw parse or cost differs')
        return finish(task, output, binding, allowance, state, forecast, [result], [], start)

    def initial(self, task, output, allowance):
        return self.direct(task, output, allowance, 'R0')

    def retrieval(self, task, output, allowance):
        return self.direct(task, output, allowance, 'R1')

    def structured(self, task, output, allowance):
        if allowance != 512:
            raise ValueError('human reserved structured budget changed')
        binding = self.binding(task, 'R3', allowance)
        saved = cached(output, binding, task, allowance)
        if saved is not None:
            return saved
        output.mkdir(parents=True, exist_ok=False)
        start = time.perf_counter(); calls = []; executions = []; feedback = None
        for index in range(2):
            folder = output/('round-'+str(index+1))
            attempt = proposal.call(task, folder/'proposal', feedback)
            calls.append(attempt)
            raw = read(folder/'proposal/RAW.json')
            if (attempt['status'], attempt['proposal'], attempt['error']) != proposal.parsed(raw, task) or attempt['cost'] != {k: raw.get(k) for k in attempt['cost']}:
                raise ValueError('human structured raw parse or cost differs')
            if attempt['status'] != 'VALID':
                break
            feedback = programs.evaluate(task, attempt['proposal']['candidates'])
            executions.append(feedback)
            ollama.write_new(folder/'EXECUTION.json', feedback)
        state, forecast = 'INVALID', None
        if len(calls) == 2 and calls[-1]['status'] == 'VALID':
            forecast = {'choice': calls[-1]['proposal']['choice'], 'probabilities': feedback['probabilities'],
                        'insufficient_evidence': calls[-1]['proposal']['insufficient_support'],
                        'explanation': 'Executed approximate handling-rule mixture; generated choice retained separately.'}
            parse_forecast(canonical(forecast), task); state = 'VALID'
        return finish(task, output, binding, allowance, state, forecast, calls, executions, start)

    @property
    def additional(self):
        return {'R1': self.retrieval, 'R3': self.structured}
