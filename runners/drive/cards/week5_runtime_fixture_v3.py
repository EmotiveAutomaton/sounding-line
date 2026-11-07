"""Actual verification-pause/resume fixture, with no scientific observations.

DESIGN CHECK: LESSONS 3-5. False verification must fail, partial verification
must pause, and complete exact replay after authenticated copy must pass.
"""
from . import week5_runtime_fixture as base
from .batch_runtime import freeze

def execute(output,inputs,config):
    if inputs:raise ValueError('Constructed only')
    return base.execute(output,{},dict(fixture=True))

def verify(output,inputs,config):
    if config.get('invalid_verify'):return dict(verified=False)
    base.verify(output,{},dict(fixture=True))
    freeze(output/'verify-checkpoint.json',dict(exact_zero=0))
    if config.get('max_new_draws',2)<2:
        return dict(status='yielded',verified=False,reason='constructed verification quantum')
    return dict(verified=True,constructed_fixture_only=True,exact_resume=True)
