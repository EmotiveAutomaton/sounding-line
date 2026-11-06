"""Three-session engineering profile; never a reduced scientific comparison.

DESIGN CHECK: LESSONS3-5 reread2026-11-04. Same source and selection under
NULL/ALTERNATIVE. Complete first-three source work and independent replay;
missing source or altered digest refuses. The full first-tenth probe remains.
"""
from pathlib import Path
from . import week4_pieces_windows_h1 as exact
from . import week3_pieces_effects_h1_pilot as original
from .timing_p6 import write_equal
from runners.stage14.common import read


def selection(rows,denominator):
    if len(rows)<3:raise ValueError('Three complete sessions required')
    ordered=sorted(rows,key=lambda r:(original.stats.derived_seed('effects-cost',0,r['session']),r['session']))
    return {r['session'] for r in ordered[:3]}


_measure=exact.copied(original.measure,effects=exact.effects,selection=selection)


def measure(output,inputs,config):
    work,timing=_measure(output,inputs,config)
    if work['sample_sessions']!=3:raise ValueError('Complete three-session profile required')
    work['selection']='Fixed first three sessions by original seed-and-session order; engineering profile only'
    work['full_first_tenth_probe']=False
    return work,timing


def execute(output,inputs,config):
    work,timing=measure(output,inputs,config)
    result=dict(card='WB1-exact-three-session-profile',work=work,timing=timing,scientific_admission=False)
    write_equal(Path(output)/'PROFILE_RESULT.json',result);return result


def verify(output,inputs,config):
    work,timing=measure(output,inputs,config)
    if read(Path(output)/'PROFILE_RESULT.json')['work']!=work:raise ValueError('Complete profile replay differs')
    return dict(verified=True,full_profile_replay=True,verification_timing=timing,scientific_admission=False)
