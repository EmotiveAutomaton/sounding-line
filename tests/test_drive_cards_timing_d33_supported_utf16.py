"""Exact UTF16/source parity and measured source-only speed; owner window."""
from copy import copy,deepcopy
import json
from pathlib import Path
import time
from types import MethodType
import pytest

from runners.drive.cards import timing_d33_supported_utf16 as fast
from runners.drive.cards import timing_d33_supported_recovery as scalar
from runners.drive.cards import timing_revision_events as revision
from runners.drive.cards.timing_revision_source import Sources as RawSources,INPUTS as RAW_INPUTS
from runners.drive.cards.timing_pmap_source import bound_record
from runners.drive.cards.timing_census import read,write,filehash
from runners.stage9 import coauthor

REPO=Path(__file__).resolve().parents[1]
PRIVATE=REPO/'.agent-state/drive-20261017/builder2'


def test_every_unicode_scalar_roundtrips_exactly_without_changing_globals():
    before=(coauthor.units,coauthor.text_of,revision.replay_revision_events)
    text=''.join(chr(n) for n in range(0x110000) if not 0xD800<=n<=0xDFFF)
    expected=coauthor.units(text)
    assert fast.units(text)==expected
    assert fast.text_of(expected)==coauthor.text_of(expected)==text
    assert before==(coauthor.units,coauthor.text_of,revision.replay_revision_events)


@pytest.mark.parametrize('values',[[0xD800],[0xDC00],[0xD800,65],[0xDC00,0xD800],[-1],[65536],[1.5],[None]])
def test_surrogate_range_and_type_errors_remain_errors(values):
    try:coauthor.text_of(values)
    except Exception as expected:
        with pytest.raises(type(expected)):fast.text_of(values)
    else:raise AssertionError('constructed invalid unit unexpectedly decoded')


def test_nontext_and_unpaired_source_strings_refuse_and_unusual_iterables_preserve_protocol():
    for value in [None,123,[],chr(0xD800),chr(0xDC00)]:
        try:coauthor.units(value)
        except Exception as expected:
            with pytest.raises(type(expected)):fast.units(value)
        else:raise AssertionError('constructed source unexpectedly encoded')
    assert fast.text_of(iter([65,66]))=='AB'
    assert fast.text_of([True,False])==coauthor.text_of([True,False])
    class Text(str):pass
    assert fast.units(Text('emoji\U0001f600'))==coauthor.units(Text('emoji\U0001f600'))


def test_complete_revision_and_screen_ledgers_match_with_surrogates_internal_edits_and_reopen():
    assert fast.apply_delta.__kwdefaults__==coauthor.apply_delta.__kwdefaults__
    assert fast.apply_delta.__kwdefaults__ is not coauthor.apply_delta.__kwdefaults__
    events=[dict(eventName='system-initialize',eventTimestamp=0,currentDoc='P\U0001f600 '),
        dict(eventName='suggestion-open',eventTimestamp=1,currentSuggestions=[dict(index=4,original='typed',trimmed='shown')]),
        dict(eventName='insert',eventTimestamp=2,eventSource='user',textDelta={'ops':[{'retain':4},{'insert':'hello \U0001f603 cat '}]}),
        dict(eventName='suggestion-reopen',eventTimestamp=3,currentSuggestions=[]),
        dict(eventName='insert',eventTimestamp=4,eventSource='user',textDelta={'ops':[{'retain':5},{'insert':'X'}]}),
        dict(eventName='delete',eventTimestamp=5,eventSource='user',textDelta={'ops':[{'retain':11},{'delete':2}]}),
        dict(eventName='insert',eventTimestamp=6,eventSource='api',textDelta={'ops':[{'retain':12},{'insert':'model '} ]})]
    before=deepcopy(events)
    assert fast.replay_revision_events(events)==revision.replay_revision_events(events)
    words=[dict(index=i,token=w,ordinal=4,population_probability=.05,context=[],is_word=True) for i,w in enumerate(['shown','cat','model'])]
    assert fast.screen_covariates(events,words)==scalar.screen_covariates(events,words)
    assert events==before
    broken=deepcopy(events);broken[4]['textDelta']={'ops':[{'retain':11},{'delete':1}]}
    for function in (revision.replay_revision_events,fast.replay_revision_events):
        with pytest.raises(UnicodeDecodeError):function(broken)


def test_actual_complete_source_parity_and_measured_speed(tmp_path):
    # Bounded owner-authorized measurement, not a scientific fit or corpus run.
    start=time.perf_counter();failed=REPO/'results/phase_2_4_stage_15/raw/drive-wave-20261017-w1/D33.pair-supported'
    base=read(failed/'PLAN.json')['inputs'];raw=RawSources({k:base[k] for k in RAW_INPUTS})
    diag=read(PRIVATE/'D33_SCREEN_SOURCE_DIAGNOSIS_20261018.json')
    ids=sorted({p.name.removesuffix('.json.gz') for p in (failed/'output/sessions').glob('*.json.gz')}|{v['session'] for v in diag['exception_events']})
    lookup={sid:bound_record(base['p6_index'],raw.p6[sid]) for sid in ids}
    arms={}
    for name,cls in [('scalar',scalar.Sources),('native_array',fast.Sources)]:
        obj=object.__new__(cls);obj.raw=copy(raw);obj.inputs=base;obj.lookup=lookup;obj.output=tmp_path/name;obj.verifying=False;obj.audits={}
        if name=='native_array':obj.raw.session=MethodType(fast.raw_session,obj.raw)
        arms[name]=obj
    times=[]
    for number,sid in enumerate(ids):
        answers={};durations={}
        # Alternate order, retaining the identical fixed source sample.
        for name in (['scalar','native_array'] if number%2==0 else ['native_array','scalar']):
            t=time.perf_counter();answers[name]=arms[name].covariates(sid);durations[name]=time.perf_counter()-t
        assert answers['scalar']==answers['native_array']
        assert arms['scalar'].audits[sid]==arms['native_array'].audits[sid]
        times.append(dict(session=sid,**durations))
    totals={name:sum(v[name] for v in times) for name in arms}
    write(tmp_path/'SOURCE_SPEED_PARITY.json',dict(seconds=time.perf_counter()-start,source_sessions=len(ids),
        parity='Every raw-derived P6 occurrence and every screen covariate/audit equal; no tolerance.',
        totals=totals,native_to_scalar_ratio=totals['native_array']/totals['scalar'],per_session=times,
        frozen_original_hashes={str(Path(m.__file__).resolve()):filehash(m.__file__) for m in [scalar,revision,coauthor]},
        order='Alternating arm order on the same fixed14session source sample; no source/outcome selection.',
        scientific_fit=False,source_text_disclosed=False))
