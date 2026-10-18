"""Exact prefix reuse and bounded same-source timing; owner window only."""
from copy import deepcopy

import pytest

from runners.drive.cards import timing_d33_supported_prefix as draft
from runners.drive.cards import timing_d33_supported_utf16 as utf16
from runners.drive.cards import timing_revision_events as revision
from tests import test_drive_cards_timing_d33_supported_utf16 as original_tests


class CountedPattern:
    def __init__(self):self.calls=[]
    def finditer(self,text):
        self.calls.append(text)
        return revision.TOKEN.finditer(text)


@pytest.mark.parametrize('text',['','Hello, Straße!','P\U0001f600 naïve\nnext','a\u0301 — can’t / two.'])
def test_exact_matches_offsets_casefold_and_one_scan(text):
    counted=CountedPattern();scan=draft.PrefixMatches(counted)
    assert scan.tokens(text)==revision.tokens(text)
    expected=[(m.group(),m.start(),m.end()) for m in revision.TOKEN.finditer(text)]
    assert [(m.group(),m.start(),m.end()) for m in scan.finditer(text)]==expected
    assert [(m.group(),m.start(),m.end()) for m in scan.finditer(text)]==expected
    assert counted.calls==[text]


def test_different_object_and_fragment_scan_do_not_reuse_or_evict_prefix():
    text='a sufficiently long prefix with repeated words words '
    other=('!'+text)[1:];assert text==other and text is not other
    counted=CountedPattern();scan=draft.PrefixMatches(counted)
    scan.tokens(text)
    list(scan.finditer(other));assert len(counted.calls)==2
    list(scan.finditer('fragment'));assert len(counted.calls)==3
    list(scan.finditer(text));assert len(counted.calls)==3
    scan.tokens('replacement');list(scan.finditer(text));assert len(counted.calls)==5


def test_regex_type_refusal_and_failed_tokenization_leave_prior_cache_intact():
    counted=CountedPattern();scan=draft.PrefixMatches(counted);text='good prefix '
    scan.tokens(text)
    for value in (None,3,[],b'bytes'):
        with pytest.raises(TypeError):revision.tokens(value)
        with pytest.raises(TypeError):scan.tokens(value)
        with pytest.raises(TypeError):list(scan.finditer(value))
    before=len(counted.calls);assert [m.group() for m in scan.finditer(text)]==['good','prefix']
    assert len(counted.calls)==before


def test_complete_ledger_internal_edits_deletions_unicode_and_invalid_boundaries():
    events=[dict(eventName='system-initialize',eventTimestamp=0,currentDoc='P\U0001f600 '),
        dict(eventName='insert',eventTimestamp=1,eventSource='user',textDelta={'ops':[{'retain':4},{'insert':'Straße \U0001f603 cat '}]}),
        dict(eventName='insert',eventTimestamp=2,eventSource='user',textDelta={'ops':[{'retain':5},{'insert':'X'}]}),
        dict(eventName='delete',eventTimestamp=3,eventSource='user',textDelta={'ops':[{'retain':12},{'delete':2}]}),
        dict(eventName='insert',eventTimestamp=4,eventSource='api',textDelta={'ops':[{'retain':13},{'insert':'model '}]}),
        dict(eventName='insert',eventTimestamp=5,eventSource='user',textDelta={'ops':[{'retain':4},{'insert':'New. '} ]})]
    unchanged=deepcopy(events)
    assert draft.replay_revision_events(events)==utf16.replay_revision_events(events)==revision.replay_revision_events(events)
    assert events==unchanged
    # Original emoji occupies UTF16 positions11:13 before the internal insert.
    broken=deepcopy(events);broken[2]['textDelta']={'ops':[{'retain':11},{'delete':1}]}
    for function in (revision.replay_revision_events,utf16.replay_revision_events,draft.replay_revision_events):
        with pytest.raises(UnicodeDecodeError):function(broken)
    broken=deepcopy(events);broken[2]['textDelta']={'ops':[{'retain':1000}]}
    for function in (revision.replay_revision_events,utf16.replay_revision_events,draft.replay_revision_events):
        with pytest.raises(ValueError):function(broken)


def test_actual_complete_source_parity_and_measured_speed(tmp_path):
    # Reuse the exact already-reviewed fourteen-session test, swapping only its
    # optimized arm. All source selection, authentication, equality and timing
    # fields remain identical. This test is NOT run without the owner window.
    function=utf16.copied(original_tests.test_actual_complete_source_parity_and_measured_speed,fast=draft)
    function(tmp_path)
