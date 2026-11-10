"""Sealed-output checkpoint adapter for unchanged CH2--CH6 mathematics.

DESIGN CHECK: LESSONS 3-5. Execution may reuse only bound saved callback values.
Verification starts every callback at zero in a separate process, never granting
independent credit to copied execution or verification caches. Both phases honor
the owner's top-level yield request. Original scientific modules stay immutable.
"""
from contextlib import contextmanager
from pathlib import Path
import hashlib
import json
import time
from . import week5_ch_models as models
from . import week5_ch_histories as histories
from . import week5_ch_progress as legacy
from . import week5_ch_reserve_secondaries as secondaries
from .week5_ch_engine_bounded import requested
from .week5_ch_source import digest, write_json


def semantic(inputs, config):
    if 'resume_analysis' in inputs:
        raise ValueError('Use sealed runtime output-copy continuation, not a loose analysis cache')
    if config.get('card') not in ('CH2','CH3','CH4','CH5','CH6'):
        raise ValueError('Not a commissioned CH numerical card')
    quantum = config.get('max_new_draws')
    if quantum is not None and (type(quantum) is not int or quantum < 1):
        raise ValueError('Positive integral callback quantum required')
    return dict(inputs=inputs, config={k:v for k,v in config.items() if k != 'max_new_draws'},
                implementations={Path(m.__file__).name:digest(m.__file__)
                                 for m in (models,histories,secondaries,legacy)},
                adapter_sha256=digest(__file__))


class Progress:
    def __init__(self, output, request_root, inputs, config, operation):
        self.output = Path(output)
        self.request_root = Path(request_root)
        self.output.mkdir(parents=True,exist_ok=True)
        self.operation = operation
        self.binding = semantic(inputs,config)
        self.series = {}
        self.calls = 0
        self.new_calls = 0
        self.restored = 0
        self.seen = set()
        self.loop_start = {}
        self.loop_new = {}
        self.last = time.monotonic()
        self.quantum = config.get('max_new_draws') if operation == 'execute' else None
        self.path = self.output/'CHECKPOINT.json'
        if operation == 'execute' and self.path.exists():
            resume = self.request_root.parent/'RESUMED_FROM.json'
            if not resume.exists():
                raise ValueError('Saved analysis requires a new authenticated runtime attempt')
            relative = self.path.relative_to(self.request_root).as_posix()
            copied = json.loads(resume.read_text(encoding='utf8'))['copied']
            if copied.get(relative) != digest(self.path):
                raise ValueError('Copied checkpoint binding differs')
            prior = json.loads(self.path.read_text(encoding='utf8'))
            if prior['binding'] != self.binding or prior['operation'] != operation:
                raise ValueError('Changed analysis checkpoint contract')
            self.series = prior['series']
            self.restored = sum(len(s['values']) for s in self.series.values())

    def save(self):
        write_json(self.path,dict(binding=self.binding,operation=self.operation,
                                 series=self.series,complete=False),mutable=True)
        self.last = time.monotonic()

    def begin(self,label,total):
        name = str(self.calls)+':'+label
        self.calls += 1
        self.seen.add(name)
        prior = self.series.setdefault(name,dict(total=total,values=[]))
        if prior['total'] != total or len(prior['values']) > total:
            raise ValueError('Changed callback loop denominator')
        self.loop_start[name] = time.process_time()
        self.loop_new[name] = 0
        return name

    def value(self,name,index,compute):
        if requested(self.request_root):
            self.save()
            raise legacy.YieldRequested('Owner requested a sealed CH '+self.operation+' pause')
        values = self.series[name]['values']
        if index < len(values):
            return values[index]
        if index != len(values):
            raise ValueError('Nonconsecutive CH callback')
        if self.quantum is not None and self.new_calls >= self.quantum:
            self.save()
            raise legacy.YieldRequested('CH execute callback quantum')
        result = compute()
        values.append(result)
        self.new_calls += 1
        self.loop_new[name] += 1
        if self.new_calls % 25 == 0 or time.monotonic()-self.last >= 20:
            self.save()
        # This is one recorded loop's actual first-5% timing, not a forecast for
        # different loops, setup, or verification. Copied pilot bytes never move.
        pilot = self.output/'PILOT.json'
        total = self.series[name]['total']
        if len(values) >= max(1,(total+19)//20) and not pilot.exists():
            elapsed = time.process_time()-self.loop_start[name]
            write_json(pilot,dict(operation=self.operation,series=name,completed=len(values),
                                 total=total,new_this_invocation=self.loop_new[name],
                                 invocation_loop_cpu_seconds=elapsed,
                                 forecast_same_loop_cpu_seconds=elapsed*total/self.loop_new[name],
                                 basis='new callbacks in this loop only; not a whole-card or replay forecast'))
        return result

    def finish(self):
        if self.seen != set(self.series):
            raise ValueError('Saved callback loop was not revisited')
        if any(len(s['values']) != s['total'] for s in self.series.values()):
            raise ValueError('Successful science left an incomplete callback loop')


@contextmanager
def tracking(state):
    if legacy.ACTIVE is not None:
        raise RuntimeError('Nested CH analysis tracking')
    legacy.ACTIVE = state
    try:
        yield state
    finally:
        state.save()
        legacy.ACTIVE = None


def body(output,inputs,config):
    module = histories if config['card'] in ('CH4','CH6') else models
    return module.execute_body(output,inputs,config)


def sealed(output, inputs, config):
    seal = json.loads((Path(output)/'EXECUTE_SEAL.json').read_text(encoding='utf8'))
    if seal['binding'] != semantic(inputs,config) or seal['science_sha256'] != digest(Path(output)/'SCIENCE.json'):
        raise ValueError('Sealed scientific output changed')


def execute(output,inputs,config):
    output = Path(output)
    output.mkdir(parents=True,exist_ok=True)
    if (output/'EXECUTE_SEAL.json').exists():
        sealed(output,inputs,config)
        return dict(status='complete',card=config['card'],sealed_output_reused=True)
    state = Progress(output,output,inputs,config,'execute')
    try:
        with tracking(state):
            if requested(output):
                raise legacy.YieldRequested('Owner requested pause before analysis setup')
            body(output,inputs,config)
            state.finish()
    except legacy.YieldRequested as exc:
        return dict(status='yielded',reason=str(exc),phase='execute',new_callbacks=state.new_calls,
                    reused_callbacks=state.restored)
    write_json(output/'EXECUTE_SEAL.json',dict(binding=semantic(inputs,config),science_sha256=digest(output/'SCIENCE.json')))
    return dict(status='complete',card=config['card'],new_callbacks=state.new_calls,reused_callbacks=state.restored)


def verify(output,inputs,config):
    output = Path(output)
    sealed(output,inputs,config)
    # Deliberately ignore all saved callbacks, including a paused verifier's
    # own prefix. The old complete-recalculation contract is retained exactly.
    state = Progress(output/'replay',output,inputs,config,'verify')
    try:
        with tracking(state):
            if requested(output):
                raise legacy.YieldRequested('Owner requested pause before independent setup')
            body(output/'replay',inputs,config)
            state.finish()
    except legacy.YieldRequested as exc:
        return dict(status='yielded',reason=str(exc),phase='verify',new_callbacks=state.new_calls,
                    fresh_from_callback_zero=True)
    if digest(output/'SCIENCE.json') != digest(output/'replay/SCIENCE.json'):
        raise ValueError('Independent source-based statistical replay differs')
    return dict(verified=True,complete_recalculation=True,fresh_from_callback_zero=True,
                recomputed_callbacks=state.new_calls,restored_verification_callbacks=0)
