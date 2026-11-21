"""Laughter-target attribution frozen under amendment BG.

DESIGN CHECK: LESSONS 3–5. A planted single speaker keeps one credit, concurrent
targets receive no primary credit, and deleting future speech cannot change the
support census. Timing ties and windows have explicit deterministic handling.
"""
from bisect import bisect_left, bisect_right
from collections import Counter
from itertools import combinations
from math import isfinite


class SpeakerFloor:
    """Original utterance boundaries for attribution and merged intervals for time."""

    def __init__(self, utterances):
        intervals = sorted((float(row["start"]), float(row["end"])) for row in utterances)
        if any(not isfinite(start) or not isfinite(end) or end < start for start, end in intervals):
            raise ValueError("Invalid utterance interval")
        self.starts = [start for start, _ in intervals]
        self.latest_ends = []
        self.merged = []
        for start, end in intervals:
            self.latest_ends.append(max(end, self.latest_ends[-1] if self.latest_ends else end))
            if self.merged and start <= self.merged[-1][1]:
                previous, last = self.merged[-1]
                self.merged[-1] = (previous, max(last, end))
            else:
                self.merged.append((start, end))
        self.merged_ends = [end for _, end in self.merged]

    def qualifying_end(self, onset, window):
        index = bisect_right(self.starts, onset) - 1
        if index >= 0 and self.latest_ends[index] >= onset - window:
            return self.latest_ends[index]
        return None

    def seconds(self, start, end):
        if not isfinite(start) or not isfinite(end) or end < start:
            raise ValueError("Invalid exposure window")
        result = 0.0
        for index in range(bisect_left(self.merged_ends, start), len(self.merged)):
            left, right = self.merged[index]
            if left >= end:
                break
            result += max(0.0, min(right, end) - max(left, start))
        return result


def attribute(laughs, floors, roles, window=2.0):
    """Return a support census and private assignments without consulting next-minute talk."""
    if not isfinite(window) or window < 0 or set(floors) != set(roles):
        raise ValueError("Invalid window or incomplete speaker roster")
    totals = Counter()
    role_pairs = Counter()
    events = []
    for laugh in laughs:
        if laugh["label"] != "vocal":
            continue
        actor, onset = laugh["speaker"], float(laugh["start"])
        if actor not in roles or not isfinite(onset):
            raise ValueError("Unbound laugh onset or speaker")
        endings = {}
        for speaker, floor in floors.items():
            if speaker != actor:
                end = floor.qualifying_end(onset, window)
                if end is not None:
                    endings[speaker] = end
        targets = tuple(sorted(endings))
        kind = ("self", "single")[len(targets)] if len(targets) < 2 else "multiple"
        totals[kind] += 1
        if kind == "multiple":
            # One vote per distinct role-pair per ambiguous laugh.
            pairs = {tuple(sorted((roles[a], roles[b]))) for a,b in combinations(targets, 2)}
            role_pairs.update(pairs)
        last = max(endings.values(), default=None)
        most_recent = tuple(target for target in targets if endings[target] == last)
        events.append((actor, onset, targets, most_recent))
    return totals, role_pairs, events


def rate_credits(events, roles):
    counts = {rule: Counter() for rule in ("single", "latest", "fractional")}
    for actor, _, targets, most_recent in events:
        if len(targets) == 1:
            counts["single"][roles[actor], roles[targets[0]]] += 1
        for rule, group in (("latest", most_recent), ("fractional", targets)):
            for target in group:
                counts[rule][roles[actor], roles[target]] += 1 / len(group)
    return counts


def next_minute(events, vocal_onsets, floors, start, end, window=2.0):
    """Single-target rows only. Denominator is the fixed 60 seconds of recording."""
    clocks = {speaker: sorted(times) for speaker,times in vocal_onsets.items()}
    excluded = Counter()
    rows = []
    for _, onset, targets, _ in events:
        if len(targets) != 1:
            continue
        if onset - 60 < start or onset + 60 > end:
            excluded["incomplete paired minutes"] += 1
            continue
        target, = targets
        times = clocks.get(target, ())
        joined = bisect_left(times, onset) < bisect_right(times, onset + window)
        rows.append(dict(target=target, onset=onset, joined=joined,
                         phase=(onset-start)/(end-start),
                         before=floors[target].seconds(onset-60,onset)/60,
                         after=floors[target].seconds(onset,onset+60)/60))
    return rows, excluded
