"""WB1 missing effects/encoder/bootstrap cost probe; never scientific admission.

DESIGN CHECK: LESSONS 3-5 reread 2026-10-26. Identical admission for null and
alternative data: this measures work, not an effect or routing gate. Authenticate
the full source population, enumerate ALL eligible candidate occurrences, and
time a fixed first tenth of sessions. This is an upper-work candidate superset,
not a reduced scientific population. A full fresh replay must match every work
digest; changed sources or missing sampled units refuse. Threefold projections
remain estimates and never grant full-card admission automatically. No GPU.
"""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
import time

from runners.drive.cards import week3_pieces_coverage as coverage
from runners.drive.cards import week3_pieces_effects as effects
from runners.drive.cards import week3_pieces_stats as stats
from runners.drive.cards.timing_census import read, filehash
from runners.drive.cards.timing_events import source_sessions
from runners.drive.cards.timing_p6 import write_equal
from runners.stage14.common import atomic

PREP_KEYS = {'preparation_complete', 'preparation_index', 'writer_split', 'bin_edges', 'preparation_result'}


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def validate(config):
    required = {'mode', 'seed', 'sample_denominator', 'minimum_occurrences', 'minimum_writers',
                'permutation_draws', 'bootstrap_draws', 'safety_multiplier'}
    if set(config) != required or config['mode'] not in {'constructed', 'corpus'} or config['seed'] != stats.SEED:
        raise ValueError('frozen effects cost configuration required')
    for key in required - {'mode'}:
        if type(config[key]) is not int or config[key] < 1:
            raise ValueError('positive integer cost configuration required')
    if config['mode'] == 'corpus' and [config[k] for k in ['sample_denominator', 'minimum_occurrences',
            'minimum_writers', 'permutation_draws', 'bootstrap_draws', 'safety_multiplier']] != [10, 30, 10, 20, 2000, 3]:
        raise ValueError('corpus first tenth and original counts required')


def occurrences(row, candidates):
    for size in range(3, 7):
        for start in range(len(row['symbols']) - size + 1):
            piece = tuple(row['symbols'][start:start+size])
            if piece in candidates:
                stop = start + size - 1
                yield dict(session=row['session'], writer=row['writer'], side=row['side'], start=start,
                           stop=stop+1, symbols=list(piece), source_ordinal=row['source_ordinals'][stop][-1],
                           seconds=row['seconds'][stop])


def selection(rows, denominator):
    # Uses session identity and fixed seed only, never candidate/effect outcomes.
    ordered = sorted(rows, key=lambda r: (stats.derived_seed('effects-cost', 0, r['session']), r['session']))
    return {r['session'] for r in ordered[:math.ceil(len(ordered)/denominator)]}


def measure(output, inputs, config):
    validate(config)
    if set(inputs) != PREP_KEYS | {'source_inputs', 'content_model', 'content_complete'}:
        raise ValueError('exact effects cost source bundle required')
    output = Path(output)
    started_cpu, started_wall = time.process_time(), time.monotonic()
    prep = {k: inputs[k] for k in PREP_KEYS}
    rows = coverage.load(prep, dict(mode=config['mode'], coarse=False))
    sources = read(inputs['source_inputs'])
    if set(sources) != {'repo_root', 'session_index', 'foundation_complete', 'foundation_plan', 'raw_roster', 'prepared_sessions'}:
        raise ValueError('source bundle shape differs')
    bound = read(inputs['preparation_result'])['source_bindings']
    for key, path in sources.items():
        if key != 'repo_root' and bound.get(str(Path(path).resolve())) != filehash(path):
            raise ValueError('effect source bundle differs from preparation')
    if config['mode'] == 'corpus':
        model = Path(inputs['content_model']).resolve()
        complete = Path(inputs['content_complete']).resolve()
        receipt = read(complete)
        if receipt.get('status') != 'COMPLETE' or receipt['outputs'].get(model.relative_to(complete.parent).as_posix()) != filehash(model):
            raise ValueError('CONTENT_V2 model identity changed')
        effects.events_p5.model_identity(model)
    candidates = stats.candidates([r for r in rows if r['side'] == 'discovery'],
                                  config['minimum_occurrences'], config['minimum_writers'])
    selected = selection(rows, config['sample_denominator'])
    counts, sampled = {}, {}
    for row in rows:
        found = list(occurrences(row, candidates))
        counts[row['session']] = len(found)
        if row['session'] in selected:
            sampled[row['session']] = found
    setup_cpu = time.process_time() - started_cpu
    records, session_digests, seen = [], [], set()
    encoder = None
    effect_cpu = 0.0
    source_start = time.process_time()
    for row, timeline, metadata in source_sessions(sources, 'raw_roster'):
        if row['session'] not in selected:
            continue
        seen.add(row['session'])
        unit_start = time.process_time()
        events = [json.loads(s) for s in (Path(sources['repo_root'])/metadata['path']).read_text(encoding='utf8').splitlines()]
        windows = effects.effect_windows(events, timeline, sampled[row['session']])
        if windows:
            if encoder is None:
                encoder = effects.FrozenEncoder(inputs['content_model'], config['mode'])
            prompt, _ = encoder.vectors([timeline['initial_document']])
            texts = sorted({w[k] for w in windows if w['full_followup'] for k in ('before', 'after')})
            similarities = {}
            if texts:
                vectors, _ = encoder.vectors(texts, context=True)
                similarities = {s: float(v @ prompt[0]) for s, v in zip(texts, vectors)}
            for w in windows:
                before, after = w.pop('before'), w.pop('after')
                w['prompt_similarity_change'] = similarities[after]-similarities[before] if w['full_followup'] else None
        records.extend(windows)
        session_digests.append(dict(session=row['session'], occurrences=len(windows), sha256=digest(windows)))
        effect_cpu += time.process_time() - unit_start
        atomic(output/'PROGRESS.json', dict(phase='effects_cost', sessions=len(seen), total=len(selected),
            occurrences=len(records), cpu_seconds=time.process_time()-started_cpu,
            wall_seconds=time.monotonic()-started_wall, scientific_admission=False))
        if (output/'YIELD_REQUEST.json').exists():
            raise coverage.YieldRequested('complete sampled session boundary')
    source_cpu = time.process_time() - source_start - effect_cpu
    if seen != selected or len(records) != sum(counts[s] for s in selected):
        raise ValueError('sampled source census differs')
    kernel_start = time.process_time()
    consistency = effects.consistency(records, config['permutation_draws'], config['seed'])
    consistency_cpu = time.process_time() - kernel_start
    kernel_start = time.process_time()
    classes = effects.classes(records, config['seed'])
    classes_cpu = time.process_time() - kernel_start
    kernel_start = time.process_time()
    # Full unit shape, neutral counts: bootstrap operation cost is value-independent.
    boot_rows = [dict(session=r['session'], writer=r['writer'], events=len(r['symbols']),
                     real_covered=0, reference_covered=0) for r in rows if r['side'] == 'test']
    boot = [stats.coverage_interval(boot_rows, config['bootstrap_draws'], config['seed']) for _ in range(2)]
    bootstrap_cpu = time.process_time() - kernel_start
    population_occurrences = sum(counts.values())
    scale = max(len(rows)/max(1, len(selected)), population_occurrences/max(1, len(records)),
                len(candidates)/max(1, len({effects.piece_key(r['symbols']) for r in records})))
    projected = 2*config['safety_multiplier']*(setup_cpu+source_cpu+bootstrap_cpu +
        scale*(effect_cpu+classes_cpu+consistency_cpu*200/config['permutation_draws']))
    work = dict(sessions=len(rows), writers=len({r['writer'] for r in rows}), candidates=len(candidates),
        population_candidate_occurrences=population_occurrences, sample_sessions=len(selected), sample_occurrences=len(records),
        selected_sessions=sorted(selected), session_digests=sorted(session_digests,key=lambda r:r['session']),
        kernel_digest=digest(dict(consistency=consistency, classes=classes, bootstrap=boot)),
        selection='fixed seed and session identity; first ceiling(N/10) in corpus mode',
        scientific_admission=False, upper_work_candidate_superset=True)
    timing = dict(cpu_seconds=time.process_time()-started_cpu, wall_seconds=time.monotonic()-started_wall,
        setup_cpu_seconds=setup_cpu, source_iteration_cpu_seconds=source_cpu, sampled_effect_cpu_seconds=effect_cpu,
        consistency_cpu_seconds=consistency_cpu, classes_cpu_seconds=classes_cpu, full_shape_bootstrap_cpu_seconds=bootstrap_cpu,
        scale=scale, safety_multiplier=config['safety_multiplier'], projected_missing_work_cpu_seconds=projected,
        includes_fresh_replay=True, excludes='prior charges, this pilot charge, and separately measured full coverage',
        admission=False, limitation='Projection from a candidate superset and fixed first tenth, not a proven upper bound; owner must check tail coverage and complete cumulative budget.')
    return work, timing


def execute(output, inputs, config):
    try:
        work, timing = measure(output, inputs, config)
    except coverage.YieldRequested as exc:
        return dict(status='yielded', reason=str(exc), scientific_admission=False)
    result = dict(card='WB1-effects-cost-pilot', status='cost_probe_complete', scientific_admission=False,
                  work=work, timing=timing)
    write_equal(Path(output)/'EFFECTS_PILOT_RESULT.json', result)
    return result


def verify(output, inputs, config):
    work, timing = measure(output, inputs, config)
    saved = read(Path(output)/'EFFECTS_PILOT_RESULT.json')
    if saved['work'] != work:
        raise ValueError('effects cost full work replay differs')
    return dict(verified=True, full_probe_replay=True, scientific_admission=False, verification_timing=timing)
