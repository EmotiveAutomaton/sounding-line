"""Paired LA v5 under the unchanged self-owned native AT memory monitor.

This is conservative qualification scaffolding, not a measured paired envelope.
The original 26 GiB commit/20 GiB RAM start gate is checked before EACH load.
"""
from pathlib import Path
from types import FunctionType
import os
import time
from . import week5_at_precision_guard as guard
from . import week5_la_pipeline_v5 as scorer
from .timing_census import filehash
from .timing_p6 import write_equal

GUARD_SHA256 = 'eb17e798b204d1efc4fb2cebeca42d6cdb5a42f2f3a10adadba69dad8386ef77'
LIMITS = guard.LIMITS
memory = guard.memory
load_model = scorer.load_model
load_masked = scorer.load_masked


def load_gate(root, stage, *, memory_reader=None):
    """Native admission recheck while the first reader is already resident."""
    if stage not in ('causal', 'masked'):
        raise ValueError('Unknown paired load stage')
    root = Path(root)
    if (root / 'YIELD_REQUEST.json').exists():
        raise scorer.PairedLoadYield('Existing cooperative request before paired load')
    snapshot = (memory if memory_reader is None else memory_reader)()
    choice = guard.action(snapshot, admission=True)
    owned = guard.identity()
    write_equal(root / 'load_admissions' / f'{os.getpid()}-{time.time_ns()}-{stage}.json',
        dict(identity=owned, stage=stage, snapshot=snapshot, action=choice, limits=LIMITS,
             guard_sha256=GUARD_SHA256, paired_peak_measured=False))
    if choice != 'admit':
        if not (root / 'YIELD_REQUEST.json').exists():
            write_equal(root / 'YIELD_REQUEST.json', dict(reason='paired model-load admission refused',
                        stage=stage, snapshot=snapshot, identity=owned))
        raise scorer.PairedLoadYield('Paired load-stage native headroom refusal')


def run(output, inputs, config, verifying=False):
    scorer.validate(inputs, config)
    if filehash(guard.__file__) != GUARD_SHA256:
        raise ValueError('Original self-owned native guard changed')
    root = Path(output)
    root.mkdir(parents=True, exist_ok=True)
    stamp = f'{os.getpid()}-{time.time_ns()}'
    def invoke(destination, args, options, verify_phase):
        fn = FunctionType(scorer.score.__code__, dict(scorer.score.__globals__,
            load_model=load_model, load_masked=load_masked), scorer.score.__name__,
            scorer.score.__defaults__, scorer.score.__closure__)
        fn.__kwdefaults__ = scorer.score.__kwdefaults__
        return fn(destination, args, options, verify_phase,
                  before_model_load=lambda stage: load_gate(destination, stage))
    def receipt_write(destination, value):
        # The original monitor names a receipt by native identity and phase.
        # Separate invocations in one constructed fixture must retain each one;
        # only its receipt destination is namespaced, never monitor behavior.
        path = Path(destination)
        if path.parent.resolve() == root.resolve() and path.name.startswith('GUARD_'):
            path = root / 'guard_invocations' / stamp / path.name
        return write_equal(path, value)
    fn = FunctionType(guard.run.__code__, dict(guard.run.__globals__, invoke=invoke,
        memory=memory, write_equal=receipt_write), guard.run.__name__, guard.run.__defaults__, guard.run.__closure__)
    return fn(root, inputs, config, verifying)


def execute(output, inputs, config):
    return run(output, inputs, config)


def verify(output, inputs, config):
    return run(output, inputs, config, True)
