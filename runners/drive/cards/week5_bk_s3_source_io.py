"""S3 source successor: bounded telemetry sharing retries only.

DESIGN CHECK: LESSONS 3-5 reread 2026-11-07. Null and alternative use
the identical original source function, matching and verification. Transient
Windows sharing refusal may retry for five seconds; persistent or unrelated
errors still fail. Original attempts, scientific gates and source pins remain.
"""
from types import FunctionType
from . import week5_bk_s3_source as original
from .week3_tr4_sensitivity_recovery import progress

run = FunctionType(original.run.__code__,
                   dict(original.run.__globals__, progress=progress),
                   original.run.__name__, original.run.__defaults__,
                   original.run.__closure__)


def execute(output, inputs, config):
    return run(output, inputs, config)


def verify(output, inputs, config):
    return run(output, inputs, config, True)
