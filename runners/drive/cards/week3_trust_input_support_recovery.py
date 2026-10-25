"""TR5 shared engineering repair2: singleton menus keep timed atom survival.

DESIGN CHECK: LESSONS3-5 read 2026-10-25. Both null and alternative require
the complete canonical acceptance history. An absent unchosen option does not
invalidate an accepted span or its survival at the failure/control anchor.
Reuse the first repair's exact Unicode-atom history, changing only its shared
source dependency. Ambiguous choices and document/count disagreements still
fail. Every threshold, population, seed and match remains unchanged. Second
and final shared repair; prior source and native costs remain cumulative.
"""
from contextlib import contextmanager

from . import week3_trust_inputs as original
from . import week3_trust_input_recovery as first_repair
from . import week3_outcome_blocks_support_recovery as repaired

CONFIG=original.CONFIG
PILOT=original.PILOT


def history(events,timeline,canonical):
    previous=first_repair.repaired;first_repair.repaired=repaired
    try:return first_repair.history(events,timeline,canonical)
    finally:first_repair.repaired=previous


@contextmanager
def canonical_survival():
    previous=original.history;original.history=history
    try:yield
    finally:original.history=previous


def execute(output,inputs,config):
    with canonical_survival():return original.execute(output,inputs,config)


def verify(output,inputs,config):
    with canonical_survival():return original.verify(output,inputs,config)
