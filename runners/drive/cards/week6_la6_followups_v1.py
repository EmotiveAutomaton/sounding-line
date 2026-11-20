"""Strict onset windows and the length-held match commissioned on November 20.

Keep excluded utterances in linguistic history. Only case/control eligibility
changes. The original meeting folds and two feature arms consume these tables.
"""
from bisect import bisect_left, bisect_right
from collections import Counter, defaultdict
from math import isfinite

from . import week5_la as source_labels
from . import week6_la6_v2 as parent


def strict_labels(acts, laughs, seconds):
    if seconds not in (1, 2):
        raise ValueError("The frozen onset windows are one and two seconds")
    vocal = [event for event in laughs if event["label"] == "vocal"]
    events = defaultdict(list)
    for event in vocal:
        if not all(isfinite(event[k]) for k in ("start", "end")) or event["end"] < event["start"]:
            raise ValueError("Invalid vocal-laughter interval")
        events[event["meeting"]].append(event)
    timings = {}
    for meeting, group in events.items():
        group.sort(key=lambda e: (e["start"], e["end"]))
        starts, ends, last = [], [], float("-inf")
        for event in group:
            starts.append(event["start"])
            last = max(last, event["end"])
            ends.append(last)
        timings[meeting] = (starts, ends)
    rows = source_labels.labelled_acts(acts, [], window=seconds)
    parent.validate(rows)
    eligible = []
    for row in rows:
        starts, ends = timings.get(row["meeting"], ([], []))
        at = bisect_right(starts, row["end"])
        until = bisect_right(starts, row["end"] + seconds)
        hits = events[row["meeting"]][at:until]
        row.update(laughed_after=bool(hits),
                   own_laugh=any(e["speaker"] == row["speaker"] for e in hits),
                   other_laugh=any(e["speaker"] != row["speaker"] for e in hits))
        if at == 0 or ends[at - 1] < row["start"] - 1:
            eligible.append(row)
    return rows, eligible, vocal


def match_length(rows):
    """Parent's nearest 30-second control among those in the word-count band."""
    parent.validate(rows)
    groups = defaultdict(lambda: defaultdict(list))
    for row in rows:
        n = row["word_count"]
        if type(n) is not int or n < 0:
            raise ValueError("Original nonnegative word count required")
        if not row["laughed_after"]:
            groups[(row["meeting"], row["speaker"])][n].append((row["start"], row["id"]))
    for counts in groups.values():
        for controls in counts.values():
            controls.sort()
    lengths = {key: sorted(values) for key, values in groups.items()}
    pairs, unmatched = [], []
    cases = sorted((r for r in rows if r["laughed_after"]), key=lambda r: (r["meeting"], r["start"], r["id"]))
    for case in cases:
        key = (case["meeting"], case["speaker"])
        counts = lengths.get(key, [])
        n, t = case["word_count"], case["start"]
        width = max(2, n / 5)
        best = None
        for count in counts[bisect_left(counts, n-width):bisect_right(counts, n+width)]:
            controls = groups[key][count]
            left = bisect_right(controls, t-30, key=lambda c: c[0]) - 1
            right = bisect_left(controls, t+30, key=lambda c: c[0])
            candidates = []
            if left >= 0:
                candidates.append(controls[bisect_left(controls, controls[left][0], key=lambda c: c[0])])
            if right < len(controls):
                candidates.append(controls[right])
            for when, name in candidates:
                option = (abs(when-t), when, name)
                if best is None or option < best:
                    best = option
        if best is None:
            unmatched.append({"meeting":case["meeting"],"case":case["id"],"reason":"no_time_and_length_eligible_control"})
        else:
            pairs.append({"meeting":case["meeting"],"case":case["id"],"control":best[2],"distance_seconds":best[0]})
    reuse = Counter((p["meeting"],p["control"]) for p in pairs)
    return pairs, {"cases":len(cases),"matched":len(pairs),"unsupported":unmatched,
                   "unique_controls":len(reuse),"reused_control_copies":sum(n-1 for n in reuse.values())}


def project_meeting(acts, laughs, seconds):
    rows, eligible, vocal = strict_labels(acts, laughs, seconds)
    features = parent.feature_rows(rows, vocal)
    result = {"window_seconds":seconds, "source_utterances":len(rows),
              "excluded_preexisting_vocal_laugh":len(rows)-len(eligible)}
    for label, matcher in (("strict",parent.match),("length_held",match_length)):
        pairs, audit = matcher(eligible)
        table = [dict(features[(pair["meeting"],pair[role])],pair=pair["case"],role=role)
                 for pair in pairs for role in ("case","control")]
        result[label] = {"table":table,"audit":audit}
    return result


def retained_route(ordinary_pairs, length_pairs):
    if not 0 <= length_pairs <= ordinary_pairs:
        raise ValueError("Impossible length-match totals")
    if ordinary_pairs == 0:
        return "unsupported"
    return "matched" if 2*length_pairs >= ordinary_pairs else "covariate"


def omit_length(rows):
    """Zeroing the length column removes it under the parent's L2 fit in both arms."""
    return [dict(row, numeric=[0, *row["numeric"][1:]]) for row in rows]
