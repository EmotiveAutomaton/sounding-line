"""FR1 engineering healing1: exact canonical append provenance only.

DESIGN CHECK: LESSONS3-5, 2026-10-25. Quill may shift the terminal newline
or replace the whole document while performing exactly the canonical append.
Use the separately validated WC2 recovery for accepted-atom proof; preserve
every FR1 event, matching, profile, calibration, seed and support definition.
Original failed attempt and original modules remain unchanged.
"""
from contextlib import contextmanager

from . import week3_frames_inputs as original
from . import week3_outcome_blocks_inputs as old_source
from . import week3_outcome_blocks_recovery as repaired

CONFIG=original.CONFIG
PILOT=original.PILOT


@contextmanager
def canonical_append():
    previous=old_source.spans;old_source.spans=repaired.spans
    try:yield
    finally:old_source.spans=previous


def execute(output,inputs,config):
    with canonical_append():return original.execute(output,inputs,config)


def verify(output,inputs,config):
    with canonical_append():return original.verify(output,inputs,config)
