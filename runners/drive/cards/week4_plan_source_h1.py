"""Exact UTF-16 conversion successor; original attempts and semantics retained.

DESIGN CHECK: LESSONS 2-5, PLAN_SOURCE_H1. Valid conversions/full histories must
equal the original; malformed boundaries/Unicode still refuse under either null
or alternative. Cost admission unchanged; no source or scientific gate relaxed.
"""
from array import array
import sys
from types import FunctionType
from runners.stage9 import coauthor
from . import week4_plan_source as original


def units(text):
    if not isinstance(text, str):
        raise ValueError('non-text document or insertion')
    values = array('H')
    values.frombytes(text.encode('utf-16-le'))
    if sys.byteorder != 'little': values.byteswap()
    return values.tolist()


def text_of(values):
    result = array('H', values)
    if sys.byteorder != 'little': result.byteswap()
    return result.tobytes().decode('utf-16-le')


def clone(fn, **changes):
    result = FunctionType(fn.__code__, dict(fn.__globals__, **changes), fn.__name__, fn.__defaults__, fn.__closure__)
    result.__kwdefaults__ = fn.__kwdefaults__
    return result


apply_delta = clone(coauthor.apply_delta, units=units, text_of=text_of)
replay = clone(coauthor.replay, units=units, text_of=text_of, apply_delta=apply_delta)
source_session = clone(original.source_session, replay=replay)


def configuration(mode):
    return dict(original.configuration(mode), implementation='utf16-array-h1')


run = clone(original.run, source_session=source_session, configuration=configuration)
def execute(output, inputs, config): return run(output, inputs, config)
def verify(output, inputs, config): return run(output, inputs, config, True)
