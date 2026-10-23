"""GEN1 fixed-gallery comparison and complete empirical controls.

DESIGN CHECK: LESSONS 3-5 and CONTROLS 1-7 read 2026-10-23. Identical
profiles tie at chance; planted genre fingerprints reverse when genres swap.
Fixed common real-writer support is chosen before scoring. Unsupported null
draws remain invalid, never redrawn. Gallery writers are never bootstrapped.
Permutation bias and same-row fake-writer controls can forbid a positive claim.
Null, negative, unresolved, marginal, positive and invalid remain distinct.
"""
from collections import Counter, defaultdict
from pathlib import Path
import time

import numpy as np

from .timing_census import read, filehash
from .timing_p6 import gzread, gzip_equal, write_equal, progress
from .timing_pmap_source import completed
from .timing_pmap_stats import split_sessions, identify, interval, distribution, median

CONFIG = dict(card='GEN1', schema=1, permutations=200, bootstrap_draws=2000, seed=20261018)
GENRES = ('creative','argumentative')
CHANNELS = ('style','rhythm')


def profile(rows, dictionary):
    words, punctuation = Counter(), Counter()
    for r in rows:
        words.update(r['word_counts']); punctuation.update(r['punctuation_counts'])
    total = sum(words.values())+sum(punctuation.values())
    timing = [r for r in rows if r['tc_timing_mode'] != 'invalid']
    return dict(style=[words[k]/total if total else None for k in dictionary['words']]+
                     [punctuation[k]/total if total else None for k in dictionary['punctuation']],
        rhythm=[median([x for r in timing for x in r['within_intervals']]),
                median([x for r in timing for x in r['onset_intervals']])]+
                [median([x for r in timing for x in r['bigram_intervals'].get(k,[])])
                 for k in dictionary['character_bigrams']])


def profiles(rows, dictionary, mode):
    groups = {}; splits = {}
    if mode == 'primary':
        for genre in GENRES:
            halves, _ = split_sessions([r for r in rows if r['genre'] == genre])
            for writer, parts in halves.items():
                groups[writer,genre] = [profile(part,dictionary) for part in parts]
                splits[writer,genre] = [[r['session'] for r in part] for part in parts]
    elif mode == 'exploratory_mixed_genre_fallback':
        halves, _ = split_sessions(rows)
        for writer, parts in halves.items():
            for genre in GENRES:
                kept = [[r for r in part if r['genre'] == genre] for part in parts]
                groups[writer,genre] = [profile(part,dictionary) for part in kept]
                splits[writer,genre] = [[r['session'] for r in part] for part in kept]
    else: raise ValueError('Unknown genre population mode')
    return groups, splits


def support(values, writers, channel):
    return [w for w in writers if all((w,g) in values and all(
        any(x is not None for x in part[channel]) for part in values[w,g]) for g in GENRES)]


def evaluate(values, writers, channel):
    if len(writers) < 3 or support(values,writers,channel) != writers:
        return dict(valid=False, reason='fixed common genre-by-half support absent', writers=writers)
    result = {g:identify([values[w,g][0][channel] for w in writers],
                        [values[w,g][1][channel] for w in writers]) for g in GENRES}
    return dict(valid=True, writers=writers, by_genre=result,
                scores=(np.array(result['creative']['scores'])-result['argumentative']['scores']).tolist())


def permute_genres(rows, rng):
    grouped = defaultdict(list)
    for r in rows: grouped[r['writer'],r['pair']].append(r)
    changed = {}
    for key, pair in sorted(grouped.items()):
        if len(pair) != 2 or {r['genre'] for r in pair} != set(GENRES) or len({r['typed_words'] for r in pair}) != 1:
            raise ValueError('Incomplete or unbalanced matched session pair')
        flip = bool(rng.integers(2))
        for r in pair: changed[r['session']] = GENRES[1-GENRES.index(r['genre'])] if flip else r['genre']
    return [dict(r,genre=changed[r['session']]) for r in rows]


def fake_writers(rows, rng):
    changed = {}
    for g in GENRES:
        members = [r for r in rows if r['genre'] == g]
        for r, w in zip(members,rng.permutation([r['writer'] for r in members])):
            changed[r['session']] = str(w)
    return [dict(r,writer=changed[r['session']]) for r in rows]


def controlled(rows, dictionary, summary, checkpoint=lambda *args:None):
    rows = sorted(rows,key=lambda r:r['session'])
    if len({r['session'] for r in rows}) != len(rows): raise ValueError('Duplicate matched session')
    writers = sorted({r['writer'] for r in rows}); mode = summary['mode']
    values, splits = profiles(rows,dictionary,mode)
    for r in rows:
        if (r['writer'],r['genre']) in splits and r['session'] not in splits[r['writer'],r['genre']][r['half']]:
            raise ValueError('Original prompt halves differ from matching manifest')
    rosters = {c:support(values,writers,c) for c in CHANNELS}
    observed = {c:evaluate(values,rosters[c],c) for c in CHANNELS}
    rng_p, rng_f = np.random.default_rng(CONFIG['seed']), np.random.default_rng(CONFIG['seed']+1)
    banks = {'within_writer':[], 'fake_writer':[]}
    for index in range(CONFIG['permutations']):
        for name, altered in [('within_writer',permute_genres(rows,rng_p)),('fake_writer',fake_writers(rows,rng_f))]:
            transformed,_ = profiles(altered,dictionary,mode)
            banks[name].append({c:evaluate(transformed,rosters[c],c) for c in CHANNELS})
        checkpoint(index+1,CONFIG['permutations'])
    results = {}
    for c in CHANNELS:
        real = observed[c]; missing = {name:sum(not b[c]['valid'] for b in bank) for name,bank in banks.items()}
        if not real['valid']:
            results[c] = dict(state='invalid', observed=real, invalid_draws=missing); continue
        own = np.array(real['scores']); primary = interval(own,CONFIG['bootstrap_draws'],CONFIG['seed'])
        controls = dict(invalid_draws=missing)
        for name, bank in banks.items():
            contrasts = [float(np.mean(b[c]['scores'])) for b in bank if b[c]['valid']]
            controls[name] = distribution(contrasts,float(own.mean())) if not missing[name] else dict(valid=False,reason='invalid fixed-support draws; no reference probability')
        if not missing['fake_writer']:
            bank = banks['fake_writer']
            reference = np.mean([b[c]['scores'] for b in bank],axis=0)
            controls['own_minus_fake'] = interval(own-reference,CONFIG['bootstrap_draws'],CONFIG['seed']+2)
            controls['genre_own_minus_fake'] = {}
            for g in GENRES:
                fake = np.asarray([b[c]['by_genre'][g]['scores'] for b in bank])
                own_g = np.array(real['by_genre'][g]['scores'])
                controls['genre_own_minus_fake'][g] = interval(own_g-fake.mean(axis=0),CONFIG['bootstrap_draws'],CONFIG['seed']+3)
                controls['genre_own_minus_fake'][g]['chance_centered_fake'] = distribution(
                    fake.mean(axis=1)-1/len(own_g),real['by_genre'][g]['accuracy']-1/len(own_g))
        gates = dict(complete_reference=not any(missing.values()),
            within_writer_centered=not missing['within_writer'] and not controls['within_writer']['bias_flag'],
            fake_difference_centered=not missing['fake_writer'] and not controls['fake_writer']['bias_flag'],
            fake_genres_centered=not missing['fake_writer'] and all(not controls['genre_own_minus_fake'][g]['chance_centered_fake']['bias_flag'] for g in GENRES),
            paired_own_exceeds_fake=not missing['fake_writer'] and controls['own_minus_fake']['state']=='positive')
        results[c] = dict(state=primary['state'], primary=primary, observed=real, controls=controls, gates=gates,
            positive_claim_licensed=primary['state']=='positive' and all(gates.values()) and summary['primary_population_supported'])
    return dict(card=CONFIG['card'], status='complete', mode=mode, primary_channel='style', channels=results,
        matched_writers=len(writers), common_writers={c:len(rosters[c]) for c in CHANNELS},
        excluded_writers={c:sorted(set(writers)-set(rosters[c])) for c in CHANNELS},
        permutations=CONFIG['permutations'], bootstrap_draws=CONFIG['bootstrap_draws'],
        genre_weighting='retain_equal_pending_controls_and_Ghost_N18',
        limitations=['Prompt, topic, device and recording context remain alternative explanations.',
            'Fixed gallery and partial-feature B-only mean imputation are inherited from PMAP.',
            'Matched rhythm includes only retained occurrence atoms and adjoining whitespace; logged deltas are not keypresses.',
            'All probabilities descriptive; no family counter change.']), banks


def run(output, inputs, config, verify=False):
    if config != CONFIG or set(inputs) != {'features_completion'}: raise ValueError('Frozen GEN1 configuration required')
    complete = Path(inputs['features_completion']).resolve(); output = Path(output); output.mkdir(parents=True,exist_ok=True)
    for name in ('output/FEATURES.json.gz','output/DICTIONARY.json','output/SUMMARY.json','output/BINDINGS.json'):
        completed(complete,complete.parent/name)
    if any(filehash(p) != h for p,h in read(complete.parent/'output/BINDINGS.json').items()):
        raise ValueError('Feature source changed after completion')
    started = time.perf_counter()
    def checkpoint(done,total):
        progress(output/'PROGRESS.json',dict(phase='verify-controls' if verify else 'controls',done=done,total=total))
    primary,banks = controlled(gzread(complete.parent/'output/FEATURES.json.gz'),
        read(complete.parent/'output/DICTIONARY.json'),read(complete.parent/'output/SUMMARY.json'),checkpoint)
    if verify:
        if read(output/'PRIMARY.json') != primary or gzread(output/'CONTROLS.json.gz') != banks:
            raise ValueError('Full fresh GEN1 replay differs')
    else:
        write_equal(output/'PRIMARY.json',primary); gzip_equal(output/'CONTROLS.json.gz',banks)
    write_equal(output/('VERIFY_TIME.json' if verify else 'EXECUTE_TIME.json'),dict(seconds=time.perf_counter()-started))
    return dict(verified=True, complete_controls=True) if verify else dict(status='complete',complete_controls=True)


def execute(output,inputs,config): return run(output,inputs,config)
def verify(output,inputs,config): return run(output,inputs,config,True)
