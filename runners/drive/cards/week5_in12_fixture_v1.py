"""Constructed IN12 source/score/fit controls; no corpus or model access."""
from contextlib import contextmanager
from pathlib import Path
import numpy as np
import pandas as pd
from . import week5_in12_v1 as study


def world(slopes=(.2,)*6, people=64):
    rng = np.random.default_rng(131212)
    n = np.sin(np.arange(people)*1.618); n = (n-n.mean())/n.std(ddof=1)
    rows = []
    for number, label in enumerate((*study.math.NEGATIVE, *study.math.POSITIVE)):
        beta = slopes[number] if number < 6 else 0.
        nuisance = rng.normal(size=(people, 2))
        nuisance -= nuisance.mean(axis=0)
        nuisance -= n[:, None]*((n@nuisance)/(n@n))[None, :]
        nuisance[:, 1] -= nuisance[:, 0]*np.dot(nuisance[:, 0], nuisance[:, 1])/np.dot(nuisance[:, 0], nuisance[:, 0])
        nuisance /= nuisance.std(axis=0, ddof=1)
        confidence = 3+.35*nuisance[:, 0]; style = 3+.35*nuisance[:, 1]
        design = np.column_stack([np.ones(people), n, confidence, style])
        residual = rng.normal(size=people)
        residual -= design@np.linalg.lstsq(design, residual, rcond=None)[0]
        residual /= residual.std(ddof=1)
        y = beta*n+np.sqrt(1-beta**2)*residual
        for index in range(people):
            row = {'text_id': f'constructed-text-{number:02}-{index:04}', 'prolific_id': f'constructed-person-{index:04}',
                'emotion': label, 'intensity': float(3+.35*y[index]), 'confidence': float(confidence[index]),
                'N': float(4+n[index]), 'personality_support': 'available'}
            row.update({k: float(style[index]) for k in study.math.STYLE}); rows.append(row)
    return pd.DataFrame(rows)


@contextmanager
def table_boundary(frame):
    original = study.load_prepared
    try:
        identity = {'constructed_table': study.digest(frame.to_dict('records'))}
        study.load_prepared = lambda inputs: (frame.copy(), identity)
        yield
    finally:
        study.load_prepared = original


@contextmanager
def source_boundary():
    original = study.load_source
    base = world((0.,)*6, people=8).drop(columns=['N', 'personality_support'])
    base = base.loc[base.prolific_id.isin([f'constructed-person-{i:04}' for i in range(4)])].copy()
    extra = base[['text_id', 'prolific_id']].copy()
    extra['anxious'] = 3.; extra['calm'] = 5.
    extra.loc[extra.prolific_id.eq('constructed-person-0001'), ['anxious', 'calm']] = np.nan
    extra.loc[extra.text_id.eq('constructed-text-00-0002'), 'anxious'] = 4.
    try:
        identity = {'constructed': 'two exact items, one missing writer, one conflict, original rows retained'}
        study.load_source = lambda inputs: (base.copy(), extra.copy(), identity)
        yield
    finally:
        study.load_source = original


def projection_chain(output):
    output = Path(output)
    small = {'phase': 'IN12-prepare', 'max_new_draws': 1}; large = {**small, 'max_new_draws': 100}
    with source_boundary():
        assert study.execute(output, {}, small)['status'] == 'yielded'
        done = study.execute(output, {}, large)
        assert done['complete_preparation'] and done['rows'] == 32
        paused = study.verify(output, {}, small)
        assert paused['status'] == 'yielded' and paused['verified'] is False
        assert study.verify(output, {}, large)['verified'] is True
    assert done['personality_writer_counts'] == {'available': 2, 'missing': 1, 'conflicting_source_items': 1}
    return {'passed': True, 'all_rows_replayed': True}


def analytic_worlds():
    results = {}
    for name, slopes in [('common', (.2,)*6), ('mixed', (.4, .4, 0., 0., 0., 0.)), ('null', (0.,)*6)]:
        frame = world(slopes); prepared = study.math.prepare(frame)
        answer = study.math.evaluate(prepared, dict.fromkeys(prepared['keys'], 1))
        reference = study.math.evaluate(prepared, dict.fromkeys(prepared['keys'], 1), True)
        study.compare(answer, reference)
        # Per-prompt recovery is exact; the pooled fit shares the nuisance slopes.
        for prompt, expected in zip(study.math.NEGATIVE, slopes, strict=True):
            assert abs(answer['value'][prompt]-expected) < 1e-9
        assert abs(answer['value']['pooled']-np.mean(slopes)) < .01
        if name != 'mixed':
            assert answer['value']['spread'] < 1e-9
        results[name] = answer
    return results


def chain(output, slopes, people=64):
    output = Path(output); frame = world(slopes, people)
    small = {'phase': 'IN12', 'draws': 2000, 'max_new_draws': 1, 'max_wall_seconds': 160}
    large = {**small, 'max_new_draws': 2000}
    with table_boundary(frame):
        assert study.execute(output, {}, small)['status'] == 'yielded'
        done = study.execute(output, {}, large)
        assert done['complete_card'] is True
        paused = study.verify(output, {}, small)
        assert paused['status'] == 'yielded' and paused['verified'] is False
        verified = study.verify(output, {}, large)
        assert verified['verified'] is True
    for name, answer in [('pooled', done['primary']), *done['secondary'].items()]:
        if name == 'within_writer_correlation_difference' and people < 300:
            assert answer['status'] == 'unsupported'
        else:
            assert answer['draws'] == 2000 and answer['failed_draws'] == []
    if len(set(slopes)) == 1:
        assert abs(done['primary']['estimate']-slopes[0]) < 1e-9
    else:
        assert abs(done['primary']['estimate']-sum(slopes)/6) < .01
    proof = {'passed': True, 'all_supported_panels_full2000': True,
        'independent_complete_row_level_replay': True, 'execute_and_verify_pause_reentry': True,
        'constructed_slopes': list(slopes), 'record_kind': 'run', 'theory_tags': ['H15-T11'],
        'by_construction': True, 'activation': []}
    study.io.write_json(output/'FIXTURE.json', proof)
    return proof
