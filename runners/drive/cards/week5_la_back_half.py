"""LA3/LA4: temporal repetition and social-layer joining, without reader LMs.

DESIGN CHECK: LESSONS3--5. Known signed/null effects and dense dummy-regression
oracles validate absorbed regressions. Missing chronology is not a zero; laugh
fixed effects absorb starter-only properties. Preserve whole-meeting draws.
"""
from collections import defaultdict
from pathlib import Path
import bisect
import hashlib
import json
import math
import os
import time
for _key in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
    os.environ[_key] = "2"
import numpy as np
from . import week5_la as original
from . import week5_la_back_half_source as source
from .timing_p6 import gzread

SEED = 20261107


class RuntimeYield(Exception):
    pass


def check_yield(output):
    if output is not None and source.requested(output):
        raise RuntimeYield()


def columns(values):
    names = sorted(set(map(str, values)))
    return np.column_stack([np.array(values, str) == n for n in names[1:]]).astype(float) if len(names) > 1 else np.empty((len(values), 0))


def within(values, groups, weights=None):
    values = np.asarray(values, float)
    groups = np.asarray(groups, str)
    _, code = np.unique(groups, return_inverse=True)
    w = np.ones(len(code)) if weights is None else np.asarray(weights, float)
    sums = np.zeros((code.max() + 1, values.shape[1]))
    total = np.bincount(code, weights=w)
    np.add.at(sums, code, values * w[:, None])
    means = np.divide(sums, total[:, None], out=np.zeros_like(sums), where=total[:, None] > 0)
    return values - means[code]


def absorb_laugh_person(values, laughs, persons):
    """Exact two-way projection; person dummy width is meeting roster size."""
    v = within(values, laughs)
    p = columns(persons)
    if p.shape[1]:
        p = within(p, laughs)
        v -= p @ np.linalg.lstsq(p, v, rcond=1e-12)[0]
    return v


def partial(xx, xy, target=0):
    others = [i for i in range(len(xy)) if i != target]
    if others:
        a = xx[np.ix_(others, others)]
        b = xx[others, target]
        projected = np.linalg.pinv(a, rcond=1e-12)
        denominator = xx[target, target] - b @ projected @ b
        numerator = xy[target] - b @ projected @ xy[others]
    else:
        denominator, numerator = xx[target, target], xy[target]
    if denominator <= 1e-10 * max(1., abs(xx[target, target])):
        return None
    result = float(numerator / denominator)
    return result if np.isfinite(result) else None


def scalar_speaker_fit(x, y, persons, meetings, counts=None, universe=None, weights=None):
    """Speaker effects refit with multiplicities when people cross meetings."""
    universe = sorted(set(meetings)) if universe is None else universe
    lookup = {m: i for i, m in enumerate(universe)}
    count = np.ones(len(universe)) if counts is None else np.asarray(counts)
    w = np.array([count[lookup[m]] for m in meetings], float)
    if weights is not None:
        w *= weights
    z = within(np.column_stack((x, y)), persons, w)
    return partial(z[:, :-1].T @ (z[:, :-1] * w[:, None]), z[:, :-1].T @ (z[:, -1] * w))


def event_stats(x, y, events, persons, meetings, person_effect=True, output=None):
    result = {}
    meetings = np.asarray(meetings, str)
    for meeting in sorted(set(meetings)):
        check_yield(output)
        keep = meetings == meeting
        value = np.column_stack((x[keep], y[keep]))
        value = absorb_laugh_person(value, np.asarray(events)[keep], np.asarray(persons)[keep]) if person_effect else within(value, np.asarray(events)[keep])
        result[meeting] = (value[:, :-1].T @ value[:, :-1], value[:, :-1].T @ value[:, -1], float(value[:, -1] @ value[:, -1]))
    return result


def event_fit(stats, counts=None, universe=None, target=0):
    universe = sorted(stats) if universe is None else universe
    count = np.ones(len(universe)) if counts is None else counts
    selected = [(stats[m], count[i]) for i, m in enumerate(universe) if m in stats and count[i]]
    if not selected:
        return None
    return partial(sum(s[0] * w for s, w in selected), sum(s[1] * w for s, w in selected), target)


def summarize(point, draws, bar, meetings, tag, scale=False, descriptive=False):
    result = {"record_kind": "texture" if descriptive or scale else "claim", "theory_tags": [tag],
              "by_construction": False, "estimate": point, "bar": bar, "meetings": meetings, "draws": len(draws)}
    if point is None or any(v is None for v in draws):
        return {**result, "status": "design cannot test", "reason": "target absorbed or unsupported draw; no omitted/redrawn samples"}
    if meetings < 2:
        return {**result, "status": "below floor, descriptive", "interval": None}
    interval = np.quantile(draws, [.025, .975]).tolist()
    se = float(np.std(draws, ddof=1))
    result.update(status="ok", interval=interval, bootstrap_se=se, sees=2.8 * se, supports_at=None if bar is None else bar + 2.8 * se,
                  sensitivity_approximation="normal approximation, slightly optimistic; same cluster resamples")
    if meetings < 20 or descriptive or scale or len(draws) < 2000 or bar is None:
        result["interpretation"] = "below floor, descriptive" if meetings < 20 else "scale only" if scale else "descriptive texture"
    else:
        lo, hi = interval
        result["outcome"] = "supports" if lo > bar else "against" if hi < 0 or (lo >= -bar and hi <= bar) else "inconclusive"
    if bar is not None and bar > 0 and result["sees"] > bar:
        result["first_line"] = f"limited sensitivity: sees effects of about {result['sees']:.3f} or more; the bar is {bar:g}"
    return result


def bootstrap(output, binding, draws, evaluate, config):
    values = []
    new_blocks = 0
    for start in range(0, draws, 16):
        if source.requested(output):
            return None
        end = min(draws, start + 16)
        path = output / "draws" / f"{start:05d}-{end:05d}.json"
        if path.exists():
            block = json.loads(path.read_text("utf8"))
            seal = json.loads(path.with_suffix(".seal.json").read_text("utf8"))
            if source.digest(path) != seal["sha256"] or block["binding"] != binding or block["range"] != [start, end]:
                raise ValueError("LA statistical checkpoint changed")
        else:
            if new_blocks >= config.get("max_new_blocks", 10**9):
                return None
            started = time.process_time()
            block_values = []
            for i in range(start, end):
                check_yield(output)
                block_values.append(evaluate(i))
            block = {"binding": binding, "range": [start, end], "values": block_values}
            source.write(path, block)
            source.write(path.with_suffix(".seal.json"), {"sha256": source.digest(path)})
            if not (output / "COST_PROBE.json").exists():
                source.write(output / "COST_PROBE.json", {"binding": binding, "range": [start, end],
                             "measured_cpu_seconds": time.process_time() - started, "forecast_cpu_seconds": None})
            new_blocks += 1
        values.extend(block["values"])
    return values


def same_order(a, b, count):
    """At least count distinct shared lemmas in common subsequence order."""
    if len(set(a) & set(b)) < count:
        return False
    frontier = {(0, frozenset())}
    for word in a:
        added = set()
        for position, used in frontier:
            if word in used:
                continue
            for j in range(position, len(b)):
                if b[j] == word:
                    next_used = used | {word}
                    if len(next_used) >= count:
                        return True
                    added.add((j + 1, next_used))
                    break
        frontier |= added
    return False


def act_speech(acts):
    """Constructed fixture convenience; production requires the complete track."""
    return [{"meeting": a["meeting"], "speaker": a["speaker"], "start": w["start"], "end": w["end"]}
            for a in acts for w in original.safe_words(a["words"])
            if w.get("start") is not None and w.get("end") is not None]


def absolute_bounds(meta, start, end):
    clock = meta.get("start_utc_seconds")
    if clock is None:
        clock = meta.get("source_local_calendar_seconds")
    if clock is not None:
        return [clock + start, clock + start], [clock + end, clock + end]
    day = meta.get("source_local_day_seconds")
    if day is None:
        return None, None
    return [day + start, day + 86400. + start], [day + end, day + 86400. + end]


def temporal_rows(acts, laughs, metadata, lemma_rows, config, output=None, speech_rows=None):
    check_yield(output)
    corpus = config.get("corpus")
    selected = [a for a in acts if corpus is None or a["corpus"] == corpus]
    bad = sorted({a["meeting"] for a in selected if not metadata[a["meeting"]]["order_qualified"]})
    if bad:
        return None, {"status": "source-held", "reason": "cross-meeting order has no documented source", "held_meetings": len(bad)}
    tokens = {r["id"]: r["content_lemmas"] for r in lemma_rows}
    if any(a["id"] not in tokens for a in selected):
        raise ValueError("incomplete lemma bank")
    vocal = [e for e in laughs if e.get("label") == "vocal"]
    labelled = original.labelled_acts(selected, vocal, window=2., left=1., others_only=True)
    by_meeting = defaultdict(list)
    for ordinal, word in enumerate(act_speech(selected) if speech_rows is None else speech_rows):
        if ordinal % 256 == 0:
            check_yield(output)
        by_meeting[word["meeting"]].append((word["start"], word["end"], word["speaker"]))
    speech = {}
    for meeting, values in by_meeting.items():
        ordered = sorted(set(values))
        best, prefix = None, []
        for word in ordered:
            if best is None or (word[1], word[0], word[2]) > (best[1], best[0], best[2]):
                best = word
            prefix.append(best)
        speech[meeting] = ([v[0] for v in ordered], prefix)
    earlier_laughs = defaultdict(list)
    for laugh in vocal:
        earlier_laughs[laugh["meeting"]].append((laugh["start"], laugh["end"]))
    laugh_clock = {}
    for meeting, values in earlier_laughs.items():
        values.sort()
        laugh_clock[meeting] = ([v[0] for v in values], np.maximum.accumulate([v[1] for v in values]).tolist())
    rows = []
    for ordinal, act in enumerate(labelled):
        if ordinal % 128 == 0:
            check_yield(output)
        meta = metadata[act["meeting"]]
        person = meta["speakers"][act["speaker"]].get("person")
        if person is None:
            continue
        starts, prior_speech = speech.get(act["meeting"], ([], []))
        i = bisect.bisect_left(starts, act["start"]) - 1
        previous = prior_speech[i] if i >= 0 else None
        starts, prior_laugh = laugh_clock.get(act["meeting"], ([], []))
        j = bisect.bisect_right(starts, act["start"]) - 1
        last_laugh = prior_laugh[j] if j >= 0 else None
        gap = max(0., act["start"] - previous[1]) if previous else act["start"]
        recency = max(0., act["start"] - last_laugh) if last_laugh is not None else act["start"]
        first = reword(act["text"].split()[0]) if act["text"].split() else ""
        start_bounds, end_bounds = absolute_bounds(meta, act["start"], act["end"])
        rows.append({**act, "person": person, "group": meta["group"], "order": meta["series_rank"],
                     "absolute_start_bounds": start_bounds, "absolute_end_bounds": end_bounds,
                     "content": tokens[act["id"]], "log_pause": math.log1p(gap), "previous_same": bool(previous and previous[2] == act["speaker"]),
                     "no_previous_speech": previous is None, "log_laugh_recency": math.log1p(max(0., recency)),
                     "laugh_recency": recency, "no_previous_laugh": last_laugh is None, "filled_pause": float(first in ("um", "uh"))})
    return rows, {"source_acts": len(selected), "speaker_identity_missing": len(selected) - len(rows),
                  "zero_content_acts": sum(not r["content"] for r in rows)}


def reword(value):
    return "".join(c for c in value.casefold() if c.isalpha())


def repetition(rows, min_gap=30., shared=2, ordered=True, output=None):
    history = defaultdict(list)
    by_lemma = defaultdict(lambda: defaultdict(set))
    results = []
    for ordinal, row in enumerate(sorted(rows, key=lambda a: (a["group"], a["order"], a["start"], a["end"], a["id"]))):
        if ordinal % 128 == 0:
            check_yield(output)
        key = (row["group"], row["laughed_after"])
        candidates = sorted({i for word in set(row["content"]) for i in by_lemma[key][word]
                             if history[key][i]["meeting"] != row["meeting"] or history[key][i]["start"] < row["start"]})
        overlap, uncertain = [], []
        for i in candidates:
            prior = history[key][i]
            if prior["meeting"] == row["meeting"]:
                low = high = row["start"] - prior["end"]
            elif row.get("absolute_start_bounds") is not None and prior.get("absolute_end_bounds") is not None:
                low = row["absolute_start_bounds"][0] - prior["absolute_end_bounds"][1]
                high = row["absolute_start_bounds"][1] - prior["absolute_end_bounds"][0]
            else:
                low, high = -math.inf, math.inf
            if low >= min_gap:
                overlap.append(prior)
            elif high >= min_gap:
                uncertain.append(prior)
        def repeats(prior):
            return same_order(row["content"], prior["content"], shared) if ordered else len(set(row["content"]) & set(prior["content"])) >= shared
        repeated = any(repeats(p) for p in overlap)
        # Fresh has no shared content with ANY earlier act. A too-recent
        # overlap is middle, never relabelled fresh by the repeat exclusion.
        category = ("repeat" if repeated else "timing_unsupported" if any(repeats(p) for p in uncertain)
                    else "between" if candidates else "fresh")
        results.append({**row, "category": category, "repeat": float(repeated)})
        for word in set(row["content"]):
            by_lemma[key][word].add(len(history[key]))
        history[key].append(row)
    return results


def pause_design(rows, predictor="fresh", outcome="log_pause"):
    if not rows:
        return None
    if predictor == "fresh":
        interest = np.array([r["category"] == "fresh" for r in rows], float)
    else:
        interest = np.array([r[predictor] for r in rows], float)
    nuisance = np.column_stack(([math.log1p(r["word_count"]) for r in rows], [r["start"] / 60 for r in rows],
                                [r["previous_same"] for r in rows], [r["log_laugh_recency"] for r in rows],
                                [r["no_previous_laugh"] for r in rows], [r["no_previous_speech"] for r in rows]))
    x = np.column_stack((interest, nuisance, columns([r["act_type"] for r in rows]), columns([r["corpus"] for r in rows])))
    return x, np.array([r[outcome] for r in rows]), [r["person"] for r in rows], [r["meeting"] for r in rows], np.array([r.get("weight", 1.) for r in rows])


def la3(acts, laughs, metadata, lemmas, output, binding, config, speech_rows=None):
    rows, audit = temporal_rows(acts, laughs, metadata, lemmas, config, output, speech_rows)
    if rows is None:
        return {"card": "LA3", **audit, "complete_card": False, "record_kind": "run", "theory_tags": ["H12-T4"], "by_construction": False}
    classified = repetition(rows, config.get("min_gap", 30.), config.get("shared", 2), output=output)
    cases = [r for r in classified if r["laughed_after"] and r["category"] in ("fresh", "repeat")]
    repeats = [r for r in cases if r["category"] == "repeat"]
    below_case_floor = len(repeats) < 200 or len({r["meeting"] for r in repeats}) < 30
    fallback = below_case_floor and not config.get("texture", False)
    primary_case = {"repeat_acts": len(repeats), "repeat_meetings": len({r["meeting"] for r in repeats})}
    if fallback:
        classified = repetition(rows, 10., 2, ordered=False, output=output)
        cases = [r for r in classified if r["laughed_after"] and r["category"] in ("fresh", "repeat")]
    if config.get("drop_laugh_recency") is not None:
        cases = [r for r in cases if r["no_previous_laugh"] or r["laugh_recency"] >= config["drop_laugh_recency"]]
    if config.get("own_silent_gap"):
        cases = [r for r in cases if r["previous_same"]]
    case_ids = {r["id"] for r in cases}
    pool = [r for r in classified if r["category"] in ("fresh", "repeat") and (not r["laughed_after"] or r["id"] in case_ids)]
    matches, unmatched = original.matched_sets(pool)
    controls, fresh_pairs = [], []
    for group in matches:
        case = group["members"][0]
        eligible = group["members"][1:]
        controls.extend({**r, "weight": 1. / len(eligible)} for r in eligible)
        fresh = [r for r in eligible if r["category"] == "fresh"]
        if case["category"] == "fresh" and fresh:
            fresh_pairs.append({**case, "case_indicator": 1., "weight": 1.})
            fresh_pairs.extend({**r, "case_indicator": 0., "weight": 1. / len(fresh)} for r in fresh)
    designs = {"fresh_minus_repeat": pause_design(cases), "unlaughed_fresh_minus_repeat": pause_design(controls),
               "fresh_laughed_minus_unlaughed": pause_design(fresh_pairs, "case_indicator"),
               "filled_pause_fresh_minus_repeat": pause_design(cases, outcome="filled_pause")}
    universe = sorted({r["meeting"] for r in cases + controls + fresh_pairs})
    def fit(design, weights=None):
        return None if design is None else scalar_speaker_fit(*design[:4], counts=weights, universe=universe, weights=design[4])
    point = {name: fit(d) for name, d in designs.items()}
    rate_groups = {"filled_pause_" + kind + "_rate": [r for r in cases if r["category"] == kind] for kind in ("fresh", "repeat")}
    meeting_positions = {m: i for i, m in enumerate(universe)}
    def rate(rows, weights=None):
        ww = np.array([1. if weights is None else weights[meeting_positions[r["meeting"]]] for r in rows])
        return float(np.dot(ww, [r["filled_pause"] for r in rows]) / ww.sum()) if ww.sum() else None
    point.update({name: rate(group) for name, group in rate_groups.items()})
    point["laugh_minus_unlaughed_contrast"] = None if any(point[k] is None for k in ("fresh_minus_repeat", "unlaughed_fresh_minus_repeat")) else point["fresh_minus_repeat"] - point["unlaughed_fresh_minus_repeat"]
    nulls = []
    primary = designs["fresh_minus_repeat"]
    if primary is not None:
        blocks = defaultdict(list)
        for i, r in enumerate(cases):
            blocks[(r["speaker"], r["meeting"])].append(i)
        for draw in range(20):
            check_yield(output)
            rng = np.random.default_rng(np.random.SeedSequence([SEED, 330, draw]))
            x = primary[0].copy()
            for group in blocks.values():
                x[group, 0] = rng.permutation(x[group, 0])
            nulls.append(fit((x, *primary[1:])))
    bar = None if len(nulls) != 20 or any(n is None for n in nulls) else max(.1, 2 * float(np.mean(np.abs(nulls))) + 3 * float(np.std(nulls, ddof=1)))
    def one(draw):
        rng = np.random.default_rng(np.random.SeedSequence([SEED, 331, draw]))
        weights = np.bincount(rng.integers(0, len(universe), len(universe)), minlength=len(universe))
        row = {name: fit(d, weights) for name, d in designs.items()}
        row.update({name: rate(group, weights) for name, group in rate_groups.items()})
        row["laugh_minus_unlaughed_contrast"] = None if row["fresh_minus_repeat"] is None or row["unlaughed_fresh_minus_repeat"] is None else row["fresh_minus_repeat"] - row["unlaughed_fresh_minus_repeat"]
        return row
    if not universe or bar is None:
        return {"card": "LA3", "status": "design cannot test", "reason": "unidentified primary or null contrast", "case": primary_case,
                "fallback": fallback, "point": point, "nulls": nulls, "complete_card": True}
    samples = bootstrap(output, binding, config["draws"], one, config)
    if samples is None:
        return {"status": "yielded", "complete_card": False}
    counts = {name: len(set(d[3])) if d is not None else 0 for name, d in designs.items()}
    counts.update({name: len({r["meeting"] for r in group}) for name, group in rate_groups.items()})
    counts["laugh_minus_unlaughed_contrast"] = len(universe)
    results = {k: summarize(v, [r[k] for r in samples], bar if k == "fresh_minus_repeat" else None,
                            counts[k], "H12-T4", descriptive=k != "fresh_minus_repeat" or below_case_floor or config.get("texture", False)) for k, v in point.items()}
    return {"card": "LA3", "primary": results.pop("fresh_minus_repeat"), "secondary": results, "case": primary_case,
            "fallback": fallback, "below_case_floor": below_case_floor,
            "fallback_reading": "below floor, descriptive" if below_case_floor else None,
            "working_bar": bar, "null": {"permutations": 20, "contrasts": nulls}, "between_acts": sum(r["category"] == "between" for r in classified),
            "timing_unsupported_acts": sum(r["category"] == "timing_unsupported" for r in classified),
            "matched_sets": len(matches), "unmatched_laughed_acts": unmatched, "source_audit": audit,
            "rival_limit": "a null cannot separate no attention cost from slow jokes failing to elicit laughter", "complete_card": True}


def joining_rows(acts, laughs, metadata, window=1., output=None, speech_rows=None):
    by_meeting = defaultdict(list)
    by_act = defaultdict(list)
    for laugh in laughs:
        if laugh.get("label") == "vocal":
            by_meeting[laugh["meeting"]].append(laugh)
    for act in acts:
        by_act[act["meeting"]].append(act)
    by_speech = defaultdict(list)
    for word in act_speech(acts) if speech_rows is None else speech_rows:
        by_speech[word["meeting"]].append(word)
    rows, audit = [], defaultdict(int)
    for meeting, events in sorted(by_meeting.items()):
        check_yield(output)
        times = sorted({(e["start"], e["end"], e["speaker"]) for e in events})
        last_end = 0.
        grouped = defaultdict(list)
        for start, end, speaker in times:
            grouped[start].append((end, speaker))
        for start, coincident in sorted(grouped.items()):
            quiet = start - last_end >= 3.
            last_end = max([last_end] + [e for e, _ in coincident])
            if not quiet:
                continue
            if len({s for _, s in coincident}) != 1:
                audit["ambiguous_simultaneous_starters"] += 1
                continue
            starter = coincident[0][1]
            before = [a for a in by_act[meeting] if a["end"] <= start]
            latest_end = max((a["end"] for a in before), default=None)
            line_speakers = {a["speaker"] for a in before if a["end"] == latest_end}
            event = hashlib.sha256(source.canonical([meeting, start, starter])).hexdigest()[:24]
            roster = metadata[meeting]["speakers"]
            if starter not in roster:
                raise ValueError("starter absent from source roster")
            for person in sorted(roster):
                if person == starter:
                    continue
                joined = any(s == person and start <= t <= start + window for t, _, s in times)
                spoke_recently = any(a["speaker"] == person and a["start"] < start and a["end"] >= start - 10 for a in by_speech[meeting])
                count = sum(s == person and start - 60 <= t < start for t, _, s in times)
                rows.append({"meeting": meeting, "corpus": metadata[meeting]["corpus"], "event": event,
                             "person": person, "starter": starter, "joined": float(joined),
                             "spoke_line": float(person in line_speakers), "spoke_recently": float(spoke_recently),
                             "recent_laugh_count": float(count), "starter_spoke_line": bool(starter in line_speakers),
                             "role": roster[person].get("role"), "start": start})
    return rows, dict(audit)


def background_design(rows, metadata, corpus, field, roles=False, situational=True, starter_stratum=None, permutation=None, output=None):
    check_yield(output)
    selected = []
    if field == "prior_coattendance":
        members = {m: {p.get("person") for p in meta["speakers"].values()} for m, meta in metadata.items() if meta["corpus"] == corpus}
        if any(metadata[m].get("start_utc_seconds") is None or None in people for m, people in members.items()):
            return {}, [], {"status": "source-held", "reason": "documented meeting chronology or global person identity missing"}
    labels = {m: {p: info.get(field) for p, info in meta["speakers"].items()} for m, meta in metadata.items() if meta["corpus"] == corpus}
    if permutation is not None:
        for ordinal, meeting in enumerate(sorted(labels)):
            persons = sorted(p for p, value in labels[meeting].items() if value is not None)
            rng = np.random.default_rng(np.random.SeedSequence([SEED, 440, permutation, ordinal]))
            values = rng.permutation([labels[meeting][p] for p in persons])
            labels[meeting].update(zip(persons, values.tolist()))
    for ordinal, row in enumerate(rows):
        if ordinal % 256 == 0:
            check_yield(output)
        if row["corpus"] != corpus or (starter_stratum is not None and row["starter_spoke_line"] != starter_stratum):
            continue
        if field == "prior_coattendance":
            meta = metadata[row["meeting"]]
            a, b = [meta["speakers"][row[key]]["person"] for key in ("starter", "person")]
            value = math.log1p(sum(metadata[m]["start_utc_seconds"] < meta["start_utc_seconds"] and a in people and b in people for m, people in members.items()))
        else:
            a, b = labels[row["meeting"]][row["starter"]], labels[row["meeting"]][row["person"]]
            if a is None or b is None:
                continue
            value = float(a == b)
        if roles and row["role"] is None:
            continue
        selected.append({**row, "background": value})
    if not selected:
        return {}, [], {"eligible_rows": 0, "source_rows": len(rows)}
    names = ["shared_" + field]
    arrays = [[r["background"] for r in selected]]
    if situational:
        for name in ("spoke_line", "spoke_recently", "recent_laugh_count"):
            names.append(name)
            arrays.append([r[name] for r in selected])
    x = np.column_stack(arrays)
    if roles:
        unique_roles = sorted({r["role"] for r in selected})
        x = np.column_stack((x, columns([r["role"] for r in selected])))
        names.extend("role_" + r for r in unique_roles[1:])
    stats = event_stats(x, np.array([r["joined"] for r in selected]), [r["event"] for r in selected],
                        [r["person"] for r in selected], [r["meeting"] for r in selected], person_effect=not roles, output=output)
    return stats, names, {"eligible_rows": len(selected), "events": len({r["event"] for r in selected}),
                          "meetings": len(stats), "background_missing_or_role_unavailable": sum(r["corpus"] == corpus for r in rows) - len(selected)}


def la4(acts, laughs, metadata, output, binding, config, speech_rows=None):
    rows, audit = joining_rows(acts, laughs, metadata, config.get("window", 1.), output, speech_rows)
    specs = {"AMI_native_language": ("AMI", "native_language", False, True, None),
             "ICSI_english_variety": ("ICSI", "english_variety", False, True, None),
             "ICSI_region": ("ICSI", "region", False, True, None),
             "ICSI_prior_coattendance": ("ICSI", "prior_coattendance", False, True, None),
             "AMI_starter_spoke": ("AMI", "native_language", False, True, True),
             "AMI_other_starter": ("AMI", "native_language", False, True, False),
             "AMI_roles_with_situation": ("AMI", "native_language", True, True, None),
             "AMI_roles_without_situation": ("AMI", "native_language", True, False, None)}
    designs = {name: background_design(rows, metadata, *spec, output=output) for name, spec in specs.items()}
    universe = sorted({m for stats, _, _ in designs.values() for m in stats})
    point = {name: [event_fit(stats, universe=universe, target=i) for i in range(len(names))] for name, (stats, names, _) in designs.items()}
    nulls = {}
    for name in ("AMI_native_language", "ICSI_english_variety", "ICSI_region"):
        nulls[name] = [event_fit(background_design(rows, metadata, *specs[name], permutation=i, output=output)[0]) for i in range(20)]
    def one(draw):
        weights = np.zeros(len(universe), int)
        for ordinal, corpus in enumerate(("AMI", "ICSI")):
            positions = [i for i, m in enumerate(universe) if metadata[m]["corpus"] == corpus]
            if not positions:
                continue
            rng = np.random.default_rng(np.random.SeedSequence([SEED, 441, draw, ordinal]))
            weights[positions] = np.bincount(rng.integers(0, len(positions), len(positions)), minlength=len(positions))
        return {name: [event_fit(stats, weights, universe, i) for i in range(len(names))] for name, (stats, names, _) in designs.items()}
    if not universe:
        return {"card": "LA4", "status": "design cannot test", "reason": "no labelled eligible joining events", "complete_card": True}
    samples = bootstrap(output, binding, config["draws"], one, config)
    if samples is None:
        return {"status": "yielded", "complete_card": False}
    fits = {}
    for name, (stats, terms, counts) in designs.items():
        fits[name] = {"counts": counts, "coefficients": {term: summarize(point[name][i], [r[name][i] for r in samples], .02 if i == 0 and "roles_" not in name and name != "ICSI_prior_coattendance" else None,
                       counts.get("meetings", 0), "H12-T5", scale="roles_" in name,
                       descriptive=i != 0 or name != "AMI_native_language" or config.get("texture", False)) for i, term in enumerate(terms)}}
        if "roles_" in name and stats:
            xx, xy, yy = [sum(s[i] for s in stats.values()) for i in range(3)]
            fits[name]["within_laugh_R_squared"] = None if yy <= 1e-12 else float(xy @ np.linalg.pinv(xx, rcond=1e-12) @ xy / yy)
    return {"card": "LA4", "primary": fits.pop("AMI_native_language"), "secondary": fits,
            "starter_spoke_main_effect": {"status": "non-identifiable", "reason": "constant within laugh and absorbed by required laugh fixed effects"},
            "null_permutations": nulls, "primary_bar": .02, "bar_not_changed_by_null": True, "source_audit": audit,
            "attendance_scope": "source meeting roster; arrival/departure times are not observed", "complete_card": True}


def execute(output, inputs, config):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    if source.requested(output):
        return {"status": "yielded", "complete_card": False, "reason": "resource request before source load"}
    if config["phase"] not in ("LA3", "LA4"):
        raise ValueError("uncommissioned LA extension phase")
    required = {"acts", "laughs", "metadata", "speech"} | ({"lemmas"} if config["phase"] == "LA3" else set())
    if not required.issubset(inputs) or set(config["pins"]) != set(inputs):
        raise ValueError("LA complete input pins required")
    for name, value in config["pins"].items():
        if source.digest(inputs[name]) != value:
            raise ValueError("LA analysis source changed")
    acts, laughs, metadata = [gzread(inputs[n]) for n in ("acts", "laughs", "metadata")]
    if config.get("constructed_fixture"):
        if not all(a["id"].startswith("constructed-") for a in acts):
            raise ValueError("fixture configuration cannot analyze human acts")
    elif config["draws"] != (200 if config.get("texture") else 2000):
        raise ValueError("human draw contract changed")
    scientific = {k: v for k, v in config.items() if k != "max_new_blocks"}
    binding = hashlib.sha256(source.canonical({"module": source.digest(Path(__file__)), "source_module": source.digest(Path(source.__file__)),
                                             "original_module": source.digest(Path(original.__file__)), "config": scientific})).hexdigest()
    source.write(output / "BINDING.json", {"binding": binding})
    try:
        check_yield(output)
        if config["phase"] == "LA3":
            result = la3(acts, laughs, metadata, gzread(inputs["lemmas"]), output, binding, config, gzread(inputs["speech"]))
        else:
            result = la4(acts, laughs, metadata, output, binding, config, gzread(inputs["speech"]))
    except RuntimeYield:
        return {"status": "yielded", "complete_card": False, "reason": "resource request during source preparation or inference"}
    if result.get("status") != "yielded":
        result.setdefault("record_kind", "texture" if config.get("texture") or result.get("fallback") or result.get("status") == "design cannot test" else "claim")
        result.setdefault("theory_tags", ["H12-T4" if config["phase"] == "LA3" else "H12-T5"])
        result.setdefault("by_construction", False)
        source.write(output / "RESULT.json", {**result, "source_binding": binding})
    return result


def verify(output, inputs, config):
    replay = Path(output) / "independent-replay"
    result = execute(replay, inputs, {k: v for k, v in config.items() if k != "max_new_blocks"})
    if result.get("status") == "yielded":
        return {**result, "verified": False}
    if (replay / "RESULT.json").read_bytes() != (Path(output) / "RESULT.json").read_bytes():
        raise ValueError("LA complete independent analysis replay differs")
    return {"verified": True, "complete_source_and_inference_replay": True, "phase": config["phase"]}
