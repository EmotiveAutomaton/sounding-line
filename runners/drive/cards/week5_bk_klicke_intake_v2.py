"""Runtime-compatible success receipt over the unchanged KLICKE source replay.

DESIGN CHECK: LESSONS 2/3/5; BK_KLICKE_VERIFY.md. A successful independent
whole-archive replay alone sets verified=True. Source, projection and collection
rules are inherited without modification; an exception never becomes success.
"""
from . import week5_bk_klicke_intake as original


def execute(output, inputs, config):
    return original.execute(output, inputs, config)


def verify(output, inputs, config):
    result = original.verify(output, inputs, config)
    if result.get('status') != 'complete' or result.get('independent_source_replay') is not True:
        raise ValueError('Complete independent KLICKE replay required')
    return {**result, 'verified': True}
