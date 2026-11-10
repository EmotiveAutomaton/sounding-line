"""Explicit guarded-v5 producer admission with unchanged complete collection.

DESIGN CHECK: LESSONS 3-5. Only the literal reviewed wrapper joins the exact
v4/v5 numerical bank. Missing native guard evidence or pins refuses, regardless
of effect direction. The original precision/source/context/model gates remain.
"""
from pathlib import Path
from types import FunctionType
from . import week5_at_collect_v4 as original
from . import week5_at_scoring_guard_v1 as guarded
from .timing_census import read, filehash

CORE = dict(original.CORE, **{
    'week5_at_precision_guard.py': 'eb17e798b204d1efc4fb2cebeca42d6cdb5a42f2f3a10adadba69dad8386ef77',
    'week5_at_scoring_guard_v1.py': '6eafffde683832820170615df32789847f140feac62f5906d3f387dc3467dd52',
})
PRODUCERS = original.PRODUCERS | {guarded.__name__}


def producer(root, plan):
    fn = FunctionType(original.producer.__code__,
                      dict(original.producer.__globals__, PRODUCERS=PRODUCERS),
                      original.producer.__name__, original.producer.__defaults__,
                      original.producer.__closure__)
    result = fn(root, plan)
    if plan['module'] != guarded.__name__:
        return result
    pins = {str(Path(p).resolve()).casefold(): s for p, s in plan['pins'].items()}
    for name, digest in CORE.items():
        p = Path(__file__).parent/name
        if filehash(p) != digest or pins.get(str(p.resolve()).casefold()) != digest:
            raise ValueError('Unreviewed or unpinned guarded producer')
    evidence = {}
    phases = set()
    # Only the immutable completed producer manifest defines its provenance.
    # A later independent replay may append new invocation/guard accounting;
    # it must not rewrite the original completed producer binding.
    done = read(root/'COMPLETE.json')
    paths = [root/name for name in sorted(done['outputs'])
             if Path(name).parent.as_posix() == 'output' and Path(name).name.startswith('GUARD_')]
    for p in paths:
        value = read(p)
        if value.get('status') != 'returned':
            continue  # Retained prior resource refusals remain in the output manifest.
        phase = value.get('phase')
        if phase not in {'execute', 'verify'} or value.get('limits') != guarded.LIMITS:
            raise ValueError('Guard phase or immutable resource thresholds differ')
        native = value['identity']
        if type(native.get('pid')) is not int or native['pid'] <= 0 or not native.get('creation_time') or not native.get('executable'):
            raise ValueError('Guard lacks exact owned native identity')
        start = value['initial']
        if (start['commit_headroom_bytes'] < guarded.LIMITS['start_commit_bytes'] or
                start['ram_available_bytes'] < guarded.LIMITS['start_ram_bytes']):
            raise ValueError('Guarded model started below its admission boundary')
        phases.add(phase)
        evidence[p.name] = filehash(p)
    if phases != {'execute', 'verify'}:
        raise ValueError('Complete guarded execute and independent verification evidence required')
    return dict(result, core=CORE, native_guard_receipts=evidence)


def validate(inputs, config):
    fn = FunctionType(original.validate.__code__,
                      dict(original.validate.__globals__, producer=producer),
                      original.validate.__name__, original.validate.__defaults__,
                      original.validate.__closure__)
    return fn(inputs, config)


def call(name, output, inputs, config):
    inherited = getattr(original, name)
    fn = FunctionType(inherited.__code__, dict(inherited.__globals__, validate=validate),
                      inherited.__name__, inherited.__defaults__, inherited.__closure__)
    return fn(output, inputs, config)


def execute(output, inputs, config):
    return call('execute', output, inputs, config)


def verify(output, inputs, config):
    return call('verify', output, inputs, config)
