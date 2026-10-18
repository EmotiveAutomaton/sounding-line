"""Exact-prefix match reuse; separate native and corpus admission pending.

DESIGN CHECK: LESSONS3-5. The frozen raw replay fully tokenizes a prefix, then
immediately scans the same string again to find the previous token. A private
per-replay cache retains the first scan's immutable regex matches for that one
identical string object. Fragment scans and every delta, occurrence field,
source check and error path remain. No inference or population changes.
Admission requires exact whole-ledger parity and refusal behavior, measured
source speed, and full independent source/inference verification. Focused
checks establish source parity, not corpus admission. Frozen globals stay intact.
"""
from __future__ import annotations

from types import MethodType

from . import timing_d33_supported_utf16 as utf16
from . import timing_revision_events as revision


class PrefixMatches:
    """Reuse only the complete tokenization just performed on this object."""
    def __init__(self,pattern):
        self.pattern=pattern
        self._text=object()
        self._matches=()

    def tokens(self,text):
        matches=list(self.pattern.finditer(text))
        result=[match.group().casefold() for match in matches]
        # Publish the cache only after the same complete normalization succeeds.
        self._text=text
        self._matches=matches
        return result

    def finditer(self,text):
        if text is self._text:return iter(self._matches)
        return self.pattern.finditer(text)


def replay_revision_events(events):
    scanner=PrefixMatches(revision.TOKEN)
    function=utf16.copied(utf16.replay_revision_events,
        TOKEN=scanner,tokens=scanner.tokens)
    return function(events)


raw_session=utf16.copied(utf16.raw_session,
    replay_revision_events=replay_revision_events)


class Sources(utf16.Sources):
    def __init__(self,inputs,output,verifying):
        super().__init__(inputs,output,verifying)
        self.raw.session=MethodType(raw_session,self.raw)


execute=utf16.copied(utf16.execute,Sources=Sources)
verify=utf16.copied(utf16.verify,Sources=Sources)
