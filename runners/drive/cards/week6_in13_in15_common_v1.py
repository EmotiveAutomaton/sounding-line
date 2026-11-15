"""Week 6 IN13/IN15 boundaries and resampling utilities.

DESIGN CHECK: LESSONS 2-3 and CONTROLS 6-7. Explicit column projection,
complete source authentication, whole-person draws, retained failed draws and
known-answer independent arithmetic precede any human inference.
"""
from __future__ import annotations
from pathlib import Path
import hashlib
import json
import os
import time
import zipfile
for _key in ('OMP_NUM_THREADS', 'MKL_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'NUMEXPR_NUM_THREADS'):
    os.environ[_key] = '2'
import numpy as np
import pandas as pd
from . import week5_in as original
from . import week5_engine_export_io as seal
from . import week5_qualification_io as io

SEED = 20261107  # Week 5 section 0.6, inherited by the Week 6 packet.
APPRAISALS = tuple(original.APPRAISALS)
FEELINGS = ('anger', 'boredom', 'disgust', 'fear', 'guilt', 'joy', 'pride',
            'relief', 'sadness', 'shame', 'surprise', 'trust')
LABELS = tuple(sorted((*FEELINGS, 'no-emotion')))
NEGATIVE = ('anger', 'boredom', 'disgust', 'fear', 'guilt', 'sadness', 'shame')
TABLE_PIN = '196fe2a4f72b36ae91516ee5caf762cb3ba04f7d69b6da4e53958587d44c1638'
SCOPES = ('qualified_real_events', 'analyst_all6600')


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, allow_nan=False).encode()).hexdigest()


def frame_digest(frame):
    return hashlib.sha256(frame.to_json(orient='split', double_precision=15).encode()).hexdigest()


def dependencies(*modules):
    paths = [Path(__file__), *(Path(m.__file__) for m in (original, seal, io, *modules))]
    return {p.as_posix(): io.sha(p) for p in paths}


def config_check(config, phases, extra=()):
    if set(config)-{'phase', 'scope', 'draws', 'max_new_draws', 'max_wall_seconds', *extra}:
        raise ValueError('Undeclared Week 6 configuration')
    if config.get('phase') not in phases or config.get('scope') not in SCOPES:
        raise ValueError('Explicit phase and prospectively resolved population scope required')
    if config.get('draws', 2000) != 2000:
        raise ValueError('Complete 2000 whole-person resamples required')
    if type(config.get('max_new_draws', 100)) is not int or config.get('max_new_draws', 100) < 1:
        raise ValueError('Positive whole-unit quantum required')
    if not np.isfinite(config.get('max_wall_seconds', 900)) or config.get('max_wall_seconds', 900) <= 0:
        raise ValueError('Positive finite wall bound required')


def canonical_source(inputs, card, scope):
    """Only this function opens human tables; never called by constructed tests."""
    if set(inputs) != {'source_run'} or scope not in SCOPES or card not in ('IN13', 'IN15'):
        raise ValueError('Qualified original IN source and explicit scope required')
    root, plan, _ = seal.complete(inputs['source_run'], 'runners.drive.cards.week5_in')
    if plan['config'].get('phase') != 'prepare':
        raise ValueError('Original IN preparation phase required')
    source = Path(plan['inputs']['source']); salt_path = Path(plan['inputs']['salt'])
    if io.sha(source) != original.SOURCE_SHA or io.sha(salt_path) != plan['pins'].get(str(salt_path)):
        raise ValueError('Archive or original join-salt pin differs')
    salt = salt_path.read_bytes()
    if len(salt) != 32 or io.sha(root/'output/generation.parquet') != TABLE_PIN:
        raise ValueError('Qualified table or join salt differs')
    base = pd.read_parquet(root/'output/generation.parquet', columns=['text_id', 'prolific_id', 'emotion', *APPRAISALS])
    source_report = seal.read(root/'output/SOURCE.json')
    if source_report.get('archive_sha256') != original.SOURCE_SHA or source_report.get('retained_rows', {}).get('generation') != len(base):
        raise ValueError('Original population disposition record differs')
    gen_columns = ['text_id', 'prolific_id', 'emotion', *APPRAISALS] if card == 'IN13' else ['text_id', 'emotion']
    if card == 'IN13': gen_columns.append('hidden_emo_text')
    val_columns = ['text_id', 'prolific_id', 'original_emotion', 'emotion', *FEELINGS, *APPRAISALS]
    with zipfile.ZipFile(source) as archive:
        if 'Creative Commons Attribution 4.0' not in archive.read('LICENSE.txt').decode('utf8'):
            raise ValueError('Licence assertion differs')
        with archive.open('corpus/crowd-enVent_generation.tsv') as stream:
            gen = pd.read_csv(stream, sep='\t', usecols=gen_columns, dtype=str, keep_default_na=False)
        val = None
        if card == 'IN15':
            with archive.open('corpus/crowd-enVent_validation.tsv') as stream:
                val = pd.read_csv(stream, sep='\t', usecols=val_columns, dtype=str, keep_default_na=False)
    if len(gen) != 6600 or gen.text_id.duplicated().any() or not gen.emotion.isin(LABELS).all():
        raise ValueError('Generation source roster differs')
    if any(gen[k].eq('').any() for k in ('text_id', 'emotion')):
        raise ValueError('Empty source identity or label')
    gen['source_ordinal'] = np.arange(len(gen))
    if card == 'IN13':
        if gen.prolific_id.eq('').any(): raise ValueError('Empty writer identity')
        order = {k: i for i, k in enumerate(sorted(gen.prolific_id.unique()))}
        gen['writer_order'] = gen.prolific_id.map(order)
        gen['discovery_half'] = gen.prolific_id.map(lambda k: int(hashlib.sha256(k.encode()).hexdigest(), 16) % 2 == 0)
        gen['prolific_id'] = gen.prolific_id.map(lambda k: original.salted(k, salt, 'crowd-person'))
    gen['text_id'] = gen.text_id.map(lambda k: original.salted(k, salt, 'crowd-text'))
    full_roster = digest(sorted(gen.text_id))
    qualified = set(base.text_id)
    if not qualified.issubset(set(gen.text_id)): raise ValueError('Missing qualified generation rows')
    if card == 'IN13':
        numeric(gen, APPRAISALS)
        left = base.sort_values('text_id').reset_index(drop=True)
        right = gen.loc[gen.text_id.isin(qualified), left.columns].sort_values('text_id').reset_index(drop=True)
        if not left[['text_id', 'prolific_id', 'emotion']].equals(right[['text_id', 'prolific_id', 'emotion']]):
            raise ValueError('Qualified writer/text/label join differs')
        if not np.array_equal(left[list(APPRAISALS)], right[list(APPRAISALS)]):
            raise ValueError('Qualified appraisal values differ')
    else:
        if len(val) != 6000: raise ValueError('Validation source roster differs')
        for key, namespace in [('text_id', 'crowd-text'), ('prolific_id', 'crowd-person')]:
            if val[key].eq('').any(): raise ValueError('Empty validation identity')
            val[key] = val[key].map(lambda k: original.salted(k, salt, namespace))
        numeric(val, (*APPRAISALS, *FEELINGS))
        validate_readers(val)
        expected = gen.set_index('text_id').emotion
        if not val.text_id.isin(expected.index).all() or not np.array_equal(val.original_emotion, val.text_id.map(expected)):
            raise ValueError('Writer-label join differs')
    if scope == 'qualified_real_events':
        gen = gen.loc[gen.text_id.isin(qualified)].copy()
        if val is not None: val = val.loc[val.text_id.isin(qualified)].copy()
    identity = {'archive_sha256': original.SOURCE_SHA, 'source_complete': io.sha(root/'COMPLETE.json'),
        'qualified_table_sha256': TABLE_PIN, 'salt_sha256': io.sha(salt_path), 'scope': scope,
        'full_text_roster_sha256': full_roster,
        'source_rows': 6600, 'qualified_rows': len(base), 'selected_generation_rows': len(gen),
        'selected_validation_rows': None if val is None else len(val), 'generation_usecols': gen_columns,
        'validation_usecols': [] if val is None else val_columns, 'demographics_read': False,
        'inherited_dispositions': {k: source_report[k] for k in ('invented_events_excluded', 'truthfulness_not_asked', 'validation_rows_for_excluded_events')},
        'license': 'CC BY 4.0', 'citation': 'doi:10.1162/coli_a_00461',
        'scope_note': 'qualified scope excludes inherited invented-event rows; analyst reference used all 6600'}
    return gen.reset_index(drop=True), None if val is None else val.reset_index(drop=True), identity


def numeric(frame, columns):
    for name in columns: frame[name] = pd.to_numeric(frame[name], errors='raise')
    if not np.isfinite(frame[list(columns)].to_numpy(float)).all() or not frame[list(columns)].isin([1, 2, 3, 4, 5]).all().all():
        raise ValueError('Required 1-to-5 source scale malformed')


def validate_readers(frame):
    if frame[['text_id', 'prolific_id']].duplicated().any(): raise ValueError('Duplicate reader within report')
    if not frame.groupby('text_id').size().eq(5).all(): raise ValueError('Exactly five distinct readers per report required')
    if not frame.emotion.isin(LABELS).all(): raise ValueError('Unknown reader label')


def resample(keys, index):
    keys = list(keys)
    rng = np.random.default_rng(np.random.SeedSequence([SEED, index]))
    return np.bincount(rng.integers(0, len(keys), len(keys)), minlength=len(keys)).astype(float)


def should_yield(output, started, config, added):
    root = Path(output).parent if Path(output).name == 'independent-replay' else Path(output)
    return (added >= config.get('max_new_draws', 100) or time.monotonic()-started >= config.get('max_wall_seconds', 900)
            or any((root/name).exists() for name in ('YIELD_REQUEST.json', 'STOP_REQUEST.json')))


def summary(point, draws, clusters, bar, *, required=2000):
    if len(draws) != required: raise ValueError('Complete draw bank required')
    bad = [i for i, value in enumerate(draws) if value is None or not np.isfinite(value)]
    out = {'estimate': point, 'clusters': int(clusters), 'draws': len(draws), 'failed_draws': bad, 'bar': bar}
    if point is None: return {**out, 'status': 'unsupported'}
    if clusters < 2: return {**out, 'status': 'unsupported', 'reason': 'fewer than two independent people'}
    if bad: return {**out, 'status': 'invalid_uncertainty', 'reason': 'failed draws retained; no redraw or subset interval'}
    values = np.array(draws, float); interval = np.quantile(values, [.025, .975]).tolist()
    se = float(values.std(ddof=1))
    out.update(status='complete' if clusters >= 20 else 'below floor, descriptive', interval=interval,
               bootstrap_SE=se, sees=2.8*se, supports_at=bar+2.8*se,
               limited_sensitivity=2.8*se > bar, approximation='normal; conditional on fixed full-source metric')
    if clusters >= 20: out['outcome'] = classify(interval, bar)
    return out


def classify(interval, bar, direction=1):
    """Week 5 section 0.6: strict positive/opposite side, closed practical band."""
    if len(interval) != 2 or direction not in (-1, 1):
        raise ValueError('An ordered interval and a signed prediction are required')
    lo, hi = map(float, interval)
    if not np.isfinite([lo, hi, bar]).all() or bar <= 0 or lo > hi:
        raise ValueError('Finite ordered interval and positive practical bar required')
    if direction == -1: lo, hi = -hi, -lo
    return ('supports' if lo > bar else 'against' if hi < 0 or (lo >= -bar and hi <= bar)
            else 'inconclusive')


def compare(left, right):
    if isinstance(left, dict):
        if not isinstance(right, dict) or set(left) != set(right): raise ValueError('Independent field inventory differs')
        for key in left: compare(left[key], right[key])
    elif isinstance(left, list):
        if not isinstance(right, list) or len(left) != len(right): raise ValueError('Independent list coverage differs')
        for a, b in zip(left, right, strict=True): compare(a, b)
    elif isinstance(left, (int, float)) and not isinstance(left, bool):
        if not isinstance(right, (int, float)) or not np.isclose(left, right, atol=1e-7, rtol=0):
            raise ValueError('Independent numerical value differs')
    elif left != right: raise ValueError('Independent value differs')


def run_draws(output, binding, point, evaluate, keys, config):
    output = Path(output); output.mkdir(parents=True, exist_ok=True)
    state = seal.state(output/'DRAWS.json', binding, {'point': point, 'draws': []})
    compare(state['point'], point)
    started = time.monotonic(); cpu = time.process_time(); added = 0
    while len(state['draws']) < 2000:
        if should_yield(output, started, config, added):
            seal.checkpoint(output/'DRAWS.json', state)
            return None, {'status': 'yielded', 'verified': False, 'completed': len(state['draws']), 'total': 2000}
        state['draws'].append(evaluate(resample(keys, len(state['draws'])))); added += 1
        if added == 1 and not (output/'COST_PREFIX.json').exists():
            io.write_json(output/'COST_PREFIX.json', {'first_draw_CPU_seconds': time.process_time()-cpu,
                'excludes_source_preparation_fits_and_complete_replay': True})
        if len(state['draws']) % 10 == 0:
            seal.checkpoint(output/'DRAWS.json', state)
            io.write_json(output/'PROGRESS.json', {'phase': 'whole_person_draws', 'completed': len(state['draws']), 'total': 2000})
    seal.checkpoint(output/'DRAWS.json', state)
    return state, None
