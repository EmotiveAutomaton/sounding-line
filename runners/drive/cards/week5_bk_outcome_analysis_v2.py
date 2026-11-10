"""Companion-only one-writer interval guard; original points/primary retained.

DESIGN CHECK: LESSONS3 one-independent-unit rule, 2026-11-07. A one-writer
bootstrap supplies no population uncertainty. The exact frozen interval and
reference RNG remain unchanged for every originally supported multiwriter arm.
"""
from types import FunctionType,SimpleNamespace
from . import week5_bk_outcome_analysis as original
from . import week3_frames_stats as stats
from . import week3_frames_analysis_cluster as cluster
from .week5_bk_outcome_features_v2 import interval


def analyze(card,data,vectors,style):
    namespace=SimpleNamespace(**dict(stats.__dict__,interval=interval))
    namespace.analyze=FunctionType(stats.analyze.__code__,dict(stats.__dict__,interval=interval))
    reference=FunctionType(cluster.contrast.__code__,dict(cluster.__dict__,stats=namespace))
    fn=FunctionType(original.analyze.__code__,dict(original.__dict__,fr=namespace,cluster=SimpleNamespace(contrast=reference)))
    return fn(card,data,vectors,style)


def run(output,inputs,config,verifying=False):
    fn=FunctionType(original.run.__code__,dict(original.__dict__,analyze=analyze))
    return fn(output,inputs,config,verifying)

def execute(output,inputs,config):return run(output,inputs,config)
def verify(output,inputs,config):return run(output,inputs,config,True)
