"""FR1 shared engineering repair2: preserve valid single-option events.

DESIGN CHECK: LESSONS3-5 read 2026-10-25. Under both null and alternative,
a unique canonical append is valid even when no unchosen option was offered.
FR1 uses dismissal history and accepted-text deletion, not the absent WC2
comparison. Preserve all events, matching, profiles, seeds and thresholds;
ambiguous choices or non-replaying documents still fail. This is the second
and final shared source repair, not a fresh retry allowance for this consumer.
"""
from contextlib import contextmanager

from . import week3_frames_inputs as original
from . import week3_outcome_blocks_inputs as old_source
from . import week3_outcome_blocks_support_recovery as repaired

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
