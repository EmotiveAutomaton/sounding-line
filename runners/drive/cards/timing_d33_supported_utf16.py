"""Separate exact UTF16 materialization optimization; native admission pending.

DESIGN CHECK: LESSONS3-5. Native unsigned-short arrays replace only repeated
Python per-code-unit byte assembly. Same strict UTF16LE encoding/decoding,
surrogate failures, raw deltas, occurrence ledger, exposure policy and fits.
Full raw/P6 and fresh-process inference verification remain mandatory. Pinned
original/recovery modules and their globals are never modified. Validity bands:
every source field must equal the scalar replay exactly; any difference or
changed refusal behavior fails admission. This supplies no scientific verdict.
"""
from __future__ import annotations

from array import array
import sys
from types import FunctionType,MethodType

from . import timing_d33_supported_recovery as recovery
from . import timing_d33_supported_source as source
from . import timing_revision_events as revision
from . import timing_revision_source as raw_source
from runners.stage9 import coauthor


def units(text):
    # Preserve exotic subclass/error behavior through the original function.
    if type(text) is not str:return coauthor.units(text)
    values=array('H')
    if values.itemsize!=2:return coauthor.units(text)
    values.frombytes(text.encode('utf-16-le'))
    if sys.byteorder!='little':values.byteswap()
    return values.tolist()


def text_of(values):
    # Raw replay creates ordinary lists of ordinary ints. Other iterable/value
    # types keep the original to_bytes protocol and its refusal behavior.
    if type(values) not in (list,tuple) or any(type(v) is not int for v in values):
        return coauthor.text_of(values)
    packed=array('H',values)
    if packed.itemsize!=2:return coauthor.text_of(values)
    if sys.byteorder!='little':packed.byteswap()
    return packed.tobytes().decode('utf-16-le')


def copied(function,**changes):
    result=FunctionType(function.__code__,dict(function.__globals__,**changes),function.__name__,
        function.__defaults__,function.__closure__)
    result.__kwdefaults__=None if function.__kwdefaults__ is None else dict(function.__kwdefaults__)
    return result


apply_delta=copied(coauthor.apply_delta,units=units,text_of=text_of)
canonical_replay=copied(coauthor.replay,units=units,text_of=text_of,apply_delta=apply_delta)
replay_revision_events=copied(revision.replay_revision_events,units=units,text_of=text_of)
raw_session=copied(raw_source.Sources.session,replay_revision_events=replay_revision_events)
visible_sequences=copied(source.visible_sequences,text_of=text_of)


def screen_function(code,namespace):
    # The frozen recovery first validates its exact reopen-only schema. It then
    # constructs the unchanged screen algorithm with these materializers.
    return FunctionType(code,dict(namespace,units=units,text_of=text_of,
        apply_delta=apply_delta,visible_sequences=visible_sequences))


screen_covariates=copied(recovery.screen_covariates,FunctionType=screen_function)


class Sources(recovery.Sources):
    def __init__(self,inputs,output,verifying):
        super().__init__(inputs,output,verifying)
        # This newly allocated source instance is private to this invocation.
        self.raw.session=MethodType(raw_session,self.raw)

    covariates=copied(recovery.Sources.covariates,screen_covariates=screen_covariates,
        canonical_replay=canonical_replay)


execute=copied(recovery.execute,Sources=Sources)
verify=copied(recovery.verify,Sources=Sources)
