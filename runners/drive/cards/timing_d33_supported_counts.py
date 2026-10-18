"""Separate per-matching-call token counts; validation/admission pending.

DESIGN CHECK: LESSONS3-5. Count only the same unchanged sequence lengths the
frozen matching algorithm already reads. Keep complete donor ordering, capacity
checks, chronology, allocations, saved proofs and fresh source authentication.
Each matching invocation owns its cache and retained object references; no
cross-target/process cache or frozen global mutation. Non-native protocols use
the scalar counter. Every output/refusal must match; no statistical change.
"""
from __future__ import annotations

from pathlib import Path
from types import MethodType,SimpleNamespace

from . import timing_d33_match as matching
from . import timing_d33_pair_intake as intake
from . import timing_d33_supported as original
from . import timing_d33_supported_source as source
from . import timing_d33_supported_prefix as prefix
from .timing_census import read

copied=prefix.utf16.copied


class TokenCounts:
    """Private to one immutable matching call; retain refs against id reuse."""
    def __init__(self,scalar=matching.token_count):
        self.scalar=scalar
        self.memo={}

    def __call__(self,session):
        held=self.memo.get(id(session))
        if held is not None and held[0] is session:return held[1]
        value=self.scalar(session) # Original failures occur before any caching.
        if (type(session) is dict and type(session.get('training_sequences')) is list
                and all(type(s) is list for s in session['training_sequences'])
                and all(type(session.get(k)) is str for k in ('writer','session','prompt'))
                and all(type(session.get(k)) in (int,float) for k in ('timestamp','end_at'))):
            self.memo[id(session)]=(session,value)
        return value


def matched_other(by_writer,target,exclude_prompt=False):
    counts=TokenCounts()
    select=copied(matching.select_sessions,token_count=counts)
    match=copied(matching.matched_other,token_count=counts,select_sessions=select)
    return match(by_writer,target,exclude_prompt)


unit=copied(intake.unit,matched_other=matched_other)
intake_view=SimpleNamespace(**dict(vars(intake),unit=unit))
source_constructor=copied(source.Sources.__init__,intake=intake_view)


class Sources(prefix.Sources):
    def __init__(self,inputs,output,verifying):
        # Original source constructor, replacing only intake.unit's matcher.
        source_constructor(self,{k:inputs[k] for k in original.INPUTS})
        # Exact frozen recovery constructor checks after its base initializer.
        self.output=Path(output);self.verifying=verifying;self.audits={}
        old=Path(inputs['failed_plan']).parent/'output';checkpoint=read(old/'PROGRESS.json')
        ids=sorted({sid for sid,_ in self.roster_for('pair')['retained_keys']})
        names=sorted(p.name for p in (old/'sessions').glob('*.json.gz'))
        if checkpoint['total']!=len(ids) or names!=[sid+'.json.gz' for sid in ids[:checkpoint['done']]]:
            raise ValueError('saved covariate population is not the exact supported prefix')
        self.raw.session=MethodType(prefix.raw_session,self.raw)


execute=copied(prefix.execute,Sources=Sources)
verify=copied(prefix.verify,Sources=Sources)
