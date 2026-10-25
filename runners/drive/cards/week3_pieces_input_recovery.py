"""WB1-input healing 1: preserve canonical P2 elapsed-clock arithmetic.

DESIGN CHECK: LESSONS 3-5, 2026-10-25. The original handler divided two epoch
millisecond floats before subtraction, losing up to 1.57e-7 seconds on its first
corpus session. P2 subtracts milliseconds first then divides. Use that exact
operation without widening any agreement tolerance or changing any event/interval
definition. Historical source and FAILED receipt remain immutable. A large epoch
known-answer fixture must reproduce canonical elapsed times exactly; corrupt P2
clocks must still fail. Existing source and complete replay checks remain active.
"""
from __future__ import annotations

from contextlib import contextmanager
import math

from runners.drive.cards import week3_pieces_input as original


def checked_clock(events):
    if not events or events[0].get("eventName") != "system-initialize":
        raise ValueError("source initialization required")
    values=[float(e["eventTimestamp"]) for e in events]
    if not all(math.isfinite(v) for v in values) or values!=sorted(values):
        raise ValueError("invalid source chronology")
    return [(v-values[0])/1000 for v in values]


@contextmanager
def canonical_clock():
    previous=original.checked_clock
    original.checked_clock=checked_clock
    try:
        yield
    finally:
        original.checked_clock=previous


def execute(output,inputs,config):
    with canonical_clock():
        return original.execute(output,inputs,config)


def verify(output,inputs,config):
    with canonical_clock():
        return original.verify(output,inputs,config)
