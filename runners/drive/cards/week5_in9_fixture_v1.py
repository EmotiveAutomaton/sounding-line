"""Packet W controls: analytic Gaussian AUC and identical paired prompts.

Expected answers are analytic constants, not values computed by the handler.
The source boundary is explicitly replaced only with constructed rows.
"""
from contextlib import contextmanager
from pathlib import Path
import numpy as np
import pandas as pd
from . import week5_in9_v1 as study


def world(shifted_items, per_prompt=2000):
    rng = np.random.default_rng(13119)
    first = rng.normal(size=(per_prompt, 22))
    second = first.copy() if shifted_items == 0 else rng.normal(size=(per_prompt, 22))
    second[:, :shifted_items] += .5
    raw = np.concatenate((first, second))
    frame = pd.DataFrame(raw, columns=study.ITEMS)
    frame['emotion'] = np.repeat(['guilt', 'shame'], per_prompt)
    frame['text_id'] = [f'constructed-text-{i:05d}' for i in range(len(frame))]
    frame['prolific_id'] = [f'constructed-writer-{i:05d}' for i in range(per_prompt)]*2
    return frame


@contextmanager
def constructed_source(frame):
    old = study.load
    try:
        identity = study.digest(frame.to_dict(orient='list'))
        study.load = lambda inputs: (frame.copy(), {'constructed_table_digest': identity})
        yield
    finally:
        study.load = old


def packet_points():
    # Phi(sqrt(3)*.5/sqrt(2))=0.7298543127; Phi(.5/sqrt(2))=0.6381631951.
    expected = {3: .72985431269629, 1: .63816319508412, 0: .5}
    output = {}
    for shifted, truth in expected.items():
        frame = world(shifted); x = frame[list(study.ITEMS)].to_numpy(float)
        y = frame.emotion.eq('shame').to_numpy(int)
        folds, _, _ = study.math.fold_codes(frame.prolific_id.to_numpy(str))
        point = study.math.evaluate(x, y, folds, np.ones(len(frame)), [])
        alternate = study.reference.evaluate(x, y, folds, np.ones(len(frame)), [])
        if abs(point[0]-truth) > .04 or abs(point[0]-alternate[0]) > 2e-6:
            raise ValueError('Packet Gaussian discriminability fixture failed')
        output[str(shifted)] = {'expected_population_auc': truth, 'observed_constructed_auc': point[0],
                               'absolute_tolerance': .04, 'texts_per_prompt': 2000}
    return output


def null_chain(output):
    output = Path(output); frame = world(0)
    config = {'phase': 'IN9-items', 'draws': 2000, 'max_new_draws': 2000, 'max_wall_seconds': 160}
    with constructed_source(frame):
        paused = study.execute(output, {}, {**config, 'max_new_draws': 1})
        if paused.get('status') != 'yielded':
            raise ValueError('Constructed whole-writer pause missing')
        result = study.execute(output, {}, config)
        if result.get('status') == 'yielded':
            return result
        assert result['primary']['estimate'] == .5 and result['primary']['interval'] == [.5, .5]
        verify_pause = study.verify(output, {}, {**config, 'max_new_draws': 1})
        assert verify_pause.get('status') == 'yielded' and verify_pause['verified'] is False
        verified = study.verify(output, {}, config)
        if verified.get('verified') is not True:
            return verified
    return {'passed': True, 'complete_actual_2000_draw_bank': True,
            'independent_formula_replay': True, 'identical_prompts_auc_and_interval': [.5, .5, .5]}
