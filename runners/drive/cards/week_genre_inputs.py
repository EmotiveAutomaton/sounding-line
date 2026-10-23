"""GEN1 source-bound session/typed-word matching; no scientific readout.

DESIGN CHECK (2026-10-22): LESSONS sections2-5 and CONTROLS1-7 reread.
Under null and alternative, matching uses only genre, prompt, chronology and
typed-word counts. Exact session and word parity must hold. Unknown identities,
changed dependencies and malformed word boundaries fail closed. Insufficient
support is reported separately, never imputed or called a negative result.
Known-answer checks cover balanced/unequal genres, prompt diversity, fallback,
zero support, ties, Unicode and source/output tampering. This component does
not implement or waive GEN1's full-gallery controls or scientific admission.
"""
from __future__ import annotations

from collections import defaultdict
import math
from pathlib import Path

from .timing_census import read, filehash
from .timing_p6 import gzread, gzip_equal, write_equal
from .timing_pmap_source import completed, indexed, bound_record
from .timing_pmap_stats import split_sessions

CONFIG = dict(card='GEN1-inputs', schema=1, primary_sessions=4,
              primary_prompts=2, primary_writers=15, seed=20261018)
GENRES = ('creative', 'argumentative')


def validate_words(words):
    if not isinstance(words, list):
        raise ValueError('Word ledger must be a list')
    for i, row in enumerate(words):
        if row['index'] != i or type(row['index']) is not int or type(row['is_word']) is not bool:
            raise ValueError('Noncanonical word ledger index/type')
        if not isinstance(row['token'], str) or not row['token']:
            raise ValueError('Empty token')
        if any(type(row[k]) is not int or row[k] < 0 for k in ('ordinal', 'completed_ordinal')):
            raise ValueError('Invalid event boundary')
        if row['ordinal'] > row['completed_ordinal'] or not math.isfinite(row['seconds']):
            raise ValueError('Invalid occurrence timing')
    return [row for row in words if row['is_word']]


def diverse_prefix(rows, count):
    """Round-robin prompts ordered by their first session; no feature values."""
    prompts = defaultdict(list)
    for row in sorted(rows, key=lambda r: (r['timestamp'], r['session'])):
        prompts[row['prompt']].append(row)
    order = sorted(prompts, key=lambda p: (prompts[p][0]['timestamp'], p))
    result = []
    for rank in range(max(map(len, prompts.values()), default=0)):
        for prompt in order:
            if rank < len(prompts[prompt]):
                result.append(prompts[prompt][rank])
    return result[:count]


def match(rows, config=CONFIG):
    if config != CONFIG:
        raise ValueError('Frozen GEN1 input policy differs')
    grouped = defaultdict(lambda: defaultdict(list))
    seen, excluded_sessions = set(), []
    for row in sorted(rows, key=lambda r: r['session']):
        if any(not isinstance(row[k], str) or not row[k] for k in ('session', 'writer', 'prompt')):
            raise ValueError('Invalid session identity')
        if row['session'] in seen or row['genre'] not in GENRES:
            raise ValueError('Duplicate session or unknown genre')
        seen.add(row['session'])
        if not math.isfinite(row['timestamp']):
            raise ValueError('Invalid session chronology')
        words = validate_words(row['words'])
        grouped[row['writer']][row['genre']].append(dict(row, typed_count=len(words)))
    support = {}
    for writer, genres in sorted(grouped.items()):
        support[writer] = {g: dict(sessions=len(genres[g]),
            positive_word_sessions=sum(r['typed_count'] > 0 for r in genres[g]),
            prompts=len({r['prompt'] for r in genres[g]})) for g in GENRES}
    eligible = [w for w, genres in support.items() if all(
        genres[g]['sessions'] >= 4 and genres[g]['prompts'] >= 2 for g in GENRES)]
    primary = len(eligible) >= 15
    candidates = eligible if primary else sorted(grouped)
    matched, writer_exclusions = [], {}
    for writer in candidates:
        genres = grouped[writer]
        positive = {g: [r for r in genres[g] if r['typed_count'] > 0] for g in GENRES}
        for g in GENRES:
            excluded_sessions.extend(dict(session=r['session'], writer=writer,
                reason='zero_completed_typed_words') for r in genres[g] if not r['typed_count'])
        count = min(len(positive[g]) for g in GENRES)
        selected = {g: diverse_prefix(positive[g], count) for g in GENRES}
        if count < (4 if primary else 2) or primary and any(
                len({r['prompt'] for r in selected[g]}) < 2 for g in GENRES):
            writer_exclusions[writer] = 'insufficient matched positive-word sessions/prompts'
            continue
        selected_rows = []
        for pair, (left, right) in enumerate(zip(selected['creative'], selected['argumentative'])):
            quota = min(left['typed_count'], right['typed_count'])
            for row in (left, right):
                actual = [w for w in row['words'] if w['is_word']][:quota]
                end = actual[-1]['index']
                # Keep trailing punctuation only when every typed word is retained.
                stop = len(row['words']) if quota == row['typed_count'] else end + 1
                token_rows = row['words'][:stop]
                assert sum(w['is_word'] for w in token_rows) == quota
                ordinal = actual[-1]['completed_ordinal']
                selected_rows.append(dict(session=row['session'], writer=writer,
                    genre=row['genre'], prompt=row['prompt'], timestamp=row['timestamp'],
                    pair=pair, typed_words=quota, original_typed_words=row['typed_count'],
                    token_stop_exclusive=stop, word_indices=[w['index'] for w in actual],
                    boundary_completed_ordinal=ordinal,
                    boundary_splits_event=any(w['completed_ordinal'] == ordinal
                        for w in row['words'][stop:] if w['is_word']),
                    original_token_count=len(row['words'])))
        halves, excluded = split_sessions(selected_rows)
        if writer in excluded:
            writer_exclusions[writer] = 'matched fallback cannot form original prompt split'
            continue
        if primary:
            for g in GENRES:
                parts, dropped = split_sessions([r for r in selected_rows if r['genre'] == g])
                if dropped:
                    raise ValueError('Primary support changed during matching')
                for h, part in enumerate(parts[writer]):
                    for r in part: r['half'] = h
        else:
            for h, part in enumerate(halves[writer]):
                for r in part: r['half'] = h
        for g in GENRES:
            assert len([r for r in selected_rows if r['genre'] == g]) == count
        assert len({sum(r['typed_words'] for r in selected_rows if r['genre'] == g) for g in GENRES}) == 1
        matched.extend(selected_rows)
        kept = {r['session'] for r in selected_rows}
        excluded_sessions.extend(dict(session=r['session'], writer=writer,
            reason='session_count_match') for g in GENRES for r in positive[g] if r['session'] not in kept)
    for writer in sorted(set(grouped)-set(candidates)):
        writer_exclusions[writer] = 'below original per-genre eligibility'
    retained = len({r['writer'] for r in matched})
    result = dict(card=CONFIG['card'], mode='primary' if primary else 'exploratory_mixed_genre_fallback',
        original_sessions=len(rows), original_writers=len(grouped),
        original_eligible_writers=len(eligible), retained_writers=retained,
        primary_population_supported=primary and retained >= CONFIG['primary_writers'],
        retained_sessions=len(matched), retained_typed_words=sum(r['typed_words'] for r in matched),
        support=support, excluded_writers=writer_exclusions,
        excluded_sessions=sorted(excluded_sessions,key=lambda r:r['session']),
        scientific_admission=False, feature_reconstruction_complete=False,
        limitations=['Prefix matching changes retained exposure and is a separately specified input policy.',
            'Rhythm bigram atoms must be reconstructed at retained occurrence boundaries; full-session aggregates cannot be reused.',
            'Matching balances each writer across whole genres, not each prompt half. Missing genre-by-half cells remain missing; the consumer must report fixed common support before fitting.',
            'Falling below primary support after zero-word exclusions does not silently select a new fallback.',
            'Completion-order prefixes are not necessarily raw-event prefixes; event ordinal alone must not truncate the replay.',
            'No genre accuracy, empirical control or scientific contrast has been computed.'])
    return result, sorted(matched, key=lambda r:(r['writer'],r['genre'],r['pair']))


def load(inputs):
    if set(inputs) != {'pmap_completion'}:
        raise ValueError('Exact completed PMAP input required')
    complete = Path(inputs['pmap_completion']).resolve()
    completed(complete, complete.parent/'PLAN.json')
    p = read(complete.parent/'PLAN.json')['inputs']
    fp = read(p['foundation_plan'])
    foundation = read(p['foundation_complete'])
    if foundation.get('status') != 'COMPLETE' or foundation['plan_sha256'] != filehash(p['foundation_plan']):
        raise ValueError('Foundation plan changed')
    root = Path(p['repo_root']).resolve()
    raw_roster = Path(p['raw_roster']).resolve()
    if fp['pins'].get(raw_roster.relative_to(root).as_posix()) != filehash(raw_roster):
        raise ValueError('Genre roster changed')
    completed(p['p6_completion'], p['p6_index'])
    roster, words = indexed(raw_roster), indexed(p['p6_index'])
    if roster.keys() != words.keys():
        raise ValueError('Genre and word populations differ')
    rows = []
    for sid, meta in sorted(roster.items()):
        row = bound_record(p['p6_index'], words[sid])
        if (row['session'],row['writer'],row['prompt'],row['timestamp']) != (
                sid,meta['writer'],meta['prompt'],meta['timestamp']):
            raise ValueError('Genre/word identity mismatch')
        rows.append(dict(row,genre=meta['domain']))
    paths = [complete, complete.parent/'PLAN.json', Path(p['foundation_complete']),
             Path(p['foundation_plan']), raw_roster, Path(p['p6_completion']), Path(p['p6_index'])]
    return rows, {str(path.resolve()): filehash(path) for path in paths}


def run(output, inputs, config, verify=False):
    output = Path(output)
    rows, bindings = load(inputs)
    summary, manifest = match(rows, config)
    if verify:
        if (read(output/'SUPPORT.json') != summary or gzread(output/'MATCHES.json.gz') != manifest
                or read(output/'BINDINGS.json') != bindings):
            raise ValueError('GEN1 matched input replay differs')
        return dict(verified=True, scientific_admission=False)
    output.mkdir(parents=True,exist_ok=True)
    write_equal(output/'BINDINGS.json',bindings)
    write_equal(output/'SUPPORT.json',summary)
    gzip_equal(output/'MATCHES.json.gz',manifest)
    return dict(status='COMPLETE_INPUT_MATCHING', scientific_admission=False)


def execute(output, inputs, config): return run(output,inputs,config)
def verify(output, inputs, config): return run(output,inputs,config,verify=True)
