"""CANDOR dyad keys and clock controls for SC2, with no model or export path.

DESIGN CHECK (LESSONS 2–5). A partner's answers describe the other speaker.
Swapped, duplicate or incomplete survey keys must never silently reverse a
rating. Nested speech runs count once for a speaker. The recording clock
bounds all intervals. These in-memory data never go to the aggregate writer.
"""
from collections import Counter, defaultdict
from math import isfinite
from numbers import Integral, Real


PINS = {
    "survey": ("surveys/survey.parquet", 1784918, "1002f2f06e2651180c38ed27c66145ca4f3a6fd8bb4833af351c76d2f6c45f39"),
    "clock": ("features/quality/row_trims.parquet", 62574, "ede97d732d580cd22951b5c09f0d32104fc5eacf07b328339952aafb46a42101"),
    "speech": ("transcripts/transcript_audiophile.parquet", 43399859, "037ec8d200f31d7f38980b19c3d1997a7eea4100d84e73b62f16d9d41fd5edb7"),
}
COLUMNS = {
    "survey": ("conversation_id", "user_id", "partner_id", "you_are_funny", "i_like_you", "i_think_your_status"),
    "clock": ("conversation_id", "ceil_recording_end_second"),
    "speech": ("conversation_id", "turn_id", "speaker", "start", "stop"),
}


def key(value):
    return isinstance(value, str) and bool(value.strip())


def finite(value):
    return isinstance(value, Real) and not isinstance(value, bool) and isfinite(value)


def seconds_union(intervals):
    total = 0.
    end = 0.
    for left, right in sorted(intervals):
        total += max(0., right - max(left, end))
        end = max(end, right)
    return total


def controls(turns, actors, duration):
    """Return talk shares in actor order or a fixed exclusion category."""
    if len(turns) < 3:
        return None, "insufficient_turns"
    if any(not isinstance(i, Integral) or isinstance(i, bool) or i < 0 for i, _, _, _ in turns):
        return None, "turn_index"
    numbers = [int(i) for i, _, _, _ in turns]
    if len(set(numbers)) != len(numbers):
        return None, "turn_index"
    first, last = min(numbers), max(numbers)
    spans = {actor: [] for actor in actors}
    for index, speaker, start, stop in turns:
        if index == first or index == last:
            continue
        if speaker not in spans:
            return None, "unmatched_speaker"
        if not finite(start) or not finite(stop) or start < 0 or stop < start:
            return None, "invalid_timing"
        left, right = min(start, duration), min(stop, duration)
        if right > left:
            spans[speaker].append((left, right))
    seconds = {actor: seconds_union(spans[actor]) for actor in actors}
    if any(t <= 0 for t in seconds.values()):
        return None, "missing_speaker_time"
    total = sum(seconds.values())
    return {actor: t / total for actor, t in seconds.items()}, None


def pair_rows(survey_rows, clock_rows, speech_rows):
    """Join reciprocal surveys; retain a complete two-person cluster or neither row.

    Input rows follow COLUMNS exactly. Returned rows are private job memory.
    The caller can resample whole clusters without disclosing any identifier.
    """
    surveys = defaultdict(list)
    clocks = defaultdict(list)
    speech = defaultdict(list)
    audit = Counter()
    for conversation, respondent, target, funny, liked, status in survey_rows:
        if key(conversation):
            surveys[conversation].append((respondent, target, funny, liked, status))
        else:
            audit["survey_rows_missing_conversation"] += 1
    for conversation, end in clock_rows:
        if conversation in surveys:
            clocks[conversation].append(end)
    for conversation, index, speaker, start, stop in speech_rows:
        if conversation in surveys:
            speech[conversation].append((index, speaker, start, stop))
    result = []
    audit["survey_conversations"] = len(surveys)
    for conversation, responses in sorted(surveys.items()):
        if len(responses) != 2:
            audit["non_dyadic_survey"] += 1
            continue
        (a, b), (c, d) = (r[:2] for r in responses)
        if not key(a) or not key(b) or a == b or (a, b) != (d, c):
            audit["nonreciprocal_survey"] += 1
            continue
        times = clocks[conversation]
        if len(times) != 1 or not finite(times[0]) or times[0] <= 0:
            audit["recording_clock"] += 1
            continue
        shares, reason = controls(speech[conversation], (a, b), float(times[0]))
        if reason:
            audit[reason] += 1
            continue
        if not all(finite(v) for row in responses for v in row[2:]):
            audit["incomplete_ratings"] += 1
            continue
        dyad = []
        for respondent, target, funny, liked, status in responses:
            dyad.append((target, respondent, float(funny), float(liked), float(status),
                         float(times[0]) / 60., shares[target]))
        result.append((conversation, tuple(sorted(dyad))))
    audit["retained_conversations"] = len(result)
    audit["retained_people"] = len({r[0] for _, pair in result for r in pair})
    return result, dict(audit)
