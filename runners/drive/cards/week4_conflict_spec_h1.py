"""Exact comparator reuse for S6.s, no model or bank change.

DESIGN CHECK: LESSONS3-5 / CONTROLS1-7 reread2026-11-04. NULL,
alternative and omitted-conflict outputs must equal the original exactly.
Every sufficient statistic enters the key; fresh verification starts empty.
Any changed input must miss. No rounded values or relaxed fit tolerance.
"""
import numpy as np
from threadpoolctl import threadpool_limits
from . import week4_conflict_spec as original
from . import week4_conflict_stats as parent
from .timing_stats import sufficient


def cache_key(groups):
    def array(a):
        a=np.asarray(a)
        return a.shape,a.dtype.str,a.tobytes(order='C')
    return tuple((g['n'],array(g['xx']),array(g['xy']),array(g['yy']),
                  array(g['sx']),array(g['sy'])) for g in groups)


class ParentFits:
    def __init__(self):
        self.cache={};self.calls=0;self.hits=0

    def fit(self,groups):
        key=cache_key(groups)
        if key in self.cache:
            self.hits+=1
        else:
            self.cache[key]=parent.adjusted_fit(groups);self.calls+=1
        return self.cache[key]


def paired_fit(groups,variant,cache):
    a,b=original.fit_variant(groups,variant),cache.fit(groups)
    return dict(adjusted_own=a['own'],original_own=b['own'],
                paired_difference=a['own']-b['own'],adjusted=a,original=b)


def run_variant(rows,variant,blocks=10,progress=None,cache=None):
    if cache is None:cache=ParentFits()
    original.columns(variant)
    run=parent.copied(parent.run,MEASURES=original.MEASURES,
        paired_fit=lambda groups,unused:paired_fit(groups,variant,cache),
        adjusted_fit=lambda groups:original.fit_variant(groups,variant))
    return run(rows,blocks=blocks,progress=progress,seed=20261102)


def known_answers():
    checks=original.known_answers()
    rows,_=original.world('conflict_only');groups=sufficient(*parent.design(rows))
    cache=ParentFits()
    for variant in original.VARIANTS:
        if paired_fit(groups,variant,cache)!=original.paired_fit(groups,variant):
            raise ValueError('Cached comparator changes native result')
    if cache.calls!=1 or cache.hits!=1:raise ValueError('Exact reuse not realized')
    return dict(checks,exact_comparator_reuse=True)


def configuration(mode):
    return dict(original.configuration(mode),card='W4-S6.s.h1-exact-comparator-cache')


human_rows=parent.copied(original.human_rows,__name__=__name__,configuration=configuration)


def one_pass(output,inputs,config,verifying=False):
    # Lifetime is one invocation only, including independently recomputed replay.
    cache=ParentFits()
    handler=parent.copied(original.one_pass,configuration=configuration,
        human_rows=human_rows,known_answers=known_answers,
        run_variant=lambda rows,variant,blocks,progress:run_variant(rows,variant,blocks,progress,cache))
    return handler(output,inputs,config,verifying)


def execute(output,inputs,config):
    with threadpool_limits(limits=1):return one_pass(output,inputs,config)


def verify(output,inputs,config):
    with threadpool_limits(limits=1):return one_pass(output,inputs,config,True)
