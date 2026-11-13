"""R1 native peak recording around the unchanged AT-FP64-1 scorer.

DESIGN CHECK: LESSONS 3-5. Signed/null score parity is inherited unchanged;
resource-boundary fixtures must prove refusal before model load, exact seven/
six-GiB request/hard floors, peak provenance, and owned-process termination.
"""
from pathlib import Path
from types import FunctionType
import os, psutil
from . import week5_at_precision_guard as guard
from . import week5_at_scoring_guard_v1 as scorer
from . import week5_at_memory_r1 as memory_rules
from .timing_p6 import write_equal

NUMERICAL_SPEC = scorer.NUMERICAL_SPEC
memory = guard.memory
invoke = scorer.invoke


def peak_memory():
    info = psutil.Process(os.getpid()).memory_info()
    if os.name != 'nt' or not hasattr(info, 'peak_pagefile'):
        raise ValueError('Native Windows peak private commit is required')
    return dict(peak_private_commit_bytes=memory_rules.positive(info.peak_pagefile),
                peak_working_set_bytes=memory_rules.positive(info.peak_wset))


def run(output, inputs, config, verifying=False):
    if set(inputs) != {'rows', 'model_manifest', 'memory_profile'}:
        raise ValueError('Exact R1 inputs required')
    if set(config) - {'context', 'context_length', 'max_wall_seconds'}:
        raise ValueError('Unknown R1 scoring configuration')
    profile = memory_rules.profile(inputs['memory_profile'], inputs['model_manifest'], config)
    limits = profile['limits']
    action = FunctionType(guard.action.__code__, dict(guard.action.__globals__, LIMITS=limits),
                          guard.action.__name__, guard.action.__defaults__)
    def publish(path, value):
        if Path(path).name.startswith('GUARD_') or Path(path).name == 'NATIVE_GUARD_TERMINATION.json':
            value = dict(value, **peak_memory(), memory_profile=profile, numerical_spec=NUMERICAL_SPEC)
        return write_equal(path, value)
    def terminate(root, receipt):
        publish(Path(root) / 'NATIVE_GUARD_TERMINATION.json', receipt)
        os._exit(75)
    fn = FunctionType(guard.run.__code__, dict(guard.run.__globals__, LIMITS=limits,
        action=action, memory=memory, invoke=invoke, write_equal=publish, hard_exit=terminate),
        guard.run.__name__, guard.run.__defaults__, guard.run.__closure__)
    return fn(output, {k: inputs[k] for k in ('rows', 'model_manifest')}, config, verifying)


def execute(output, inputs, config):
    return run(output, inputs, config)


def verify(output, inputs, config):
    return run(output, inputs, config, True)
