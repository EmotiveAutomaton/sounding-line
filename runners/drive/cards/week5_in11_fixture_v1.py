"""Packet IN11 known answers with 2,000 categorical-outcome synthetic rows."""
from contextlib import contextmanager
from pathlib import Path
import numpy as np
import pandas as pd
from . import week5_in11_v1 as study


def world(contrast=.3):
    rng = np.random.default_rng(131111); rows = []; offset = 0
    for prompt, size in zip(study.math.NEGATIVE, [325]*5+[375], strict=True):
        i = np.tile(np.repeat(np.arange(5), 5), size//25)
        d = np.tile(np.tile(np.arange(5), 5), size//25)
        intensity = i+1; duration = d+1; event = (i+d)%5+1
        unpleasant = (i-d)%5+1
        style = np.repeat(np.cos(np.arange(size//25)), 25)
        y = np.column_stack([study.math.z(intensity), study.math.z(duration)])
        controls = np.column_stack([np.ones(size), y, event, unpleasant, style])
        noises = []
        for number in range(2):
            x = np.column_stack([controls, *noises])
            value = rng.normal(size=size); value -= x@np.linalg.lstsq(x, value, rcond=None)[0]
            noises.append(value/value.std(ddof=1))
        half = contrast/2
        jump = half*y[:, 0]+np.sqrt(1-half**2)*noises[0]
        remedy = half*y[:, 1]+np.sqrt(1-half**2)*noises[1]
        for index in range(size):
            row = {'text_id': f'constructed-{offset+index:04}', 'prolific_id': f'person-{(offset+index)%100:03}',
                'emotion': prompt, 'intensity': float(intensity[index]), 'event_duration_rank': int(event[index]),
                'emotion_duration_rank': int(duration[index]), 'model_eligible': True,
                'no_emotion_reported': False, 'missing_duration': False, 'suddenness': 3+.35*jump[index],
                'predict_event': 3-.35*jump[index], 'chance_control': 3+.25*remedy[index],
                'self_control': 3-.25*remedy[index], 'accept_conseq': 3., 'unpleasantness': float(unpleasant[index])}
            row.update({k: float(3+.3*style[index]) for k in study.math.STYLE}); rows.append(row)
        offset += size
    return pd.DataFrame(rows)


@contextmanager
def table_boundary(frame):
    original = study.load_prepared
    try:
        identity = {'constructed': study.digest(frame.to_dict('records'))}
        study.load_prepared = lambda inputs: (frame.copy(), identity)
        yield
    finally:
        study.load_prepared = original


@contextmanager
def source_boundary():
    original = study.load_source
    frame = world(0.).iloc[:6].copy()
    extra = frame[['text_id', 'prolific_id']].copy()
    options = {v: k for k, v in study.math.RANKS.items()}
    extra['event_duration'] = frame.event_duration_rank.map(options)
    extra['emotion_duration'] = frame.emotion_duration_rank.map(options)
    extra.loc[0, 'emotion_duration'] = 'I had none'
    extra.loc[1, 'event_duration'] = ''
    base = frame.drop(columns=['event_duration_rank', 'emotion_duration_rank', 'no_emotion_reported', 'missing_duration', 'model_eligible'])
    try:
        study.load_source = lambda inputs: (base.copy(), extra.copy(), {'constructed': 'six category-only rows'})
        yield
    finally:
        study.load_source = original


def projection_chain(output):
    output = Path(output)
    small = {'phase': 'IN11-prepare', 'max_new_draws': 1}; full = {**small, 'max_new_draws': 100}
    with source_boundary():
        assert study.execute(output, {}, small)['status'] == 'yielded'
        result = study.execute(output, {}, full)
        assert result['counts'] == {'I_had_none': 1, 'missing_duration': 1, 'eligible_negative': 4}
        assert study.verify(output, {}, small)['verified'] is False
        assert study.verify(output, {}, full)['verified'] is True
    return {'passed': True, 'all_source_fields_independently_replayed': True}


def chain(output, planted):
    output = Path(output); frame = world(planted)
    small = {'phase': 'IN11', 'draws': 2000, 'max_new_draws': 1, 'max_wall_seconds': 160}
    full = {**small, 'max_new_draws': 2000}
    with table_boundary(frame):
        assert study.execute(output, {}, small)['status'] == 'yielded'
        result = study.execute(output, {}, full)
        assert result['complete_card'] and result['draws'] == 2000 and not result['failed_draws']
        assert abs(result['primary']['estimate']-planted) < 1e-9
        assert result['primary']['interval'][0] <= planted <= result['primary']['interval'][1]
        assert study.verify(output, {}, small)['verified'] is False
        assert study.verify(output, {}, full)['verified'] is True
    proof = {'passed': True, 'synthetic_rows': 2000, 'synthetic_writers': 100, 'planted_crossover': planted,
        'outcomes_are_five_ordered_categories': True, 'draws': 2000,
        'execute_and_independent_verify_pause_reentry': True, 'record_kind': 'run',
        'theory_tags': ['H14-rate-level', 'H15-Q2'], 'by_construction': True, 'activation': []}
    study.io.write_json(output/'FIXTURE.json', proof); return proof
