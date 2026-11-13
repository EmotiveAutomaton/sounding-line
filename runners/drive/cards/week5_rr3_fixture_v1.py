"""Constructed RR3 formula and complete-state-machine packet fixtures.

The null chain substitutes a prepared numerical table at the source boundary;
new source-feature formulas are independently checked on hand-answer plays and
synthetic source-shaped arrays. No source waiver exists in the production API.
"""
from pathlib import Path
from contextlib import contextmanager
import numpy as np
from scipy.special import expit
from . import week5_rr3_v1 as study


def hand_play():
    play = np.zeros((1, 30, 15)); play[:, :, 2] = 1
    play[:, :, 3] = 4; play[:, :, 4] = -2; play[:, :, 7] = 1
    play[0, 0, [2, 3, 4, 6, 7]] = [2, 6, -2, 1, 6]
    play[0, 1, [2, 6, 7]] = [3, 0, 3]
    play[0, 2, [3, 4, 6, 7]] = [5, -3, 1, -3]
    play[0, 3, [2, 6, 7]] = [-1, 0, -1]
    return play


def source_shaped(people=24):
    rng = np.random.default_rng(13133)
    p = np.zeros((people*3, 30, 15))
    p[:, :, 2] = rng.choice([-2., -1., 1., 2.], size=p.shape[:2])
    p[:, :, 3] = rng.uniform(2, 12, p.shape[:2]); p[:, :, 4] = -rng.uniform(2, 12, p.shape[:2])
    p[:, :, 6] = rng.integers(0, 2, p.shape[:2])
    gamble_outcome = np.where(rng.integers(0, 2, p.shape[:2]), p[:, :, 3], p[:, :, 4])
    p[:, :, 7] = np.where(p[:, :, 6], gamble_outcome, p[:, :, 2])
    return {'first': p[::3], 'plays': p, 'person': np.repeat(np.arange(people), 3),
            'counter': np.tile([1, 2, 3], people), 'repeat_eligible': np.ones(len(p), bool)}


def planted(which):
    rng = np.random.default_rng(131330)
    people, trials = 100, 24
    x = rng.normal(size=(people*trials, 9)); person = np.repeat(np.arange(people), trials)
    beta = np.zeros(9); beta[8 if which == 'recent' else 3] = .3
    alpha = rng.normal(0, .2, people)
    y = (rng.random(len(x)) < expit(x@beta+alpha[person])).astype(float)
    return x, y, person, .3 if which == 'recent' else -.3


def paired_null():
    rng = np.random.default_rng(131331); rows = []
    for person in range(20):
        for attempt in (1, 2, 3):
            for features in rng.normal(size=(4, 9)):
                rows.extend([(features, 0., person, attempt), (features, 1., person, attempt)])
    return {'x': np.array([r[0] for r in rows]), 'y': np.array([r[1] for r in rows]),
            'person': np.array([r[2] for r in rows]), 'attempt': np.array([r[3] for r in rows]),
            'census': {'constructed_people': 20, 'constructed_choices': len(rows)}, 'scales': [1.]*9}


@contextmanager
def prepared_boundary(table):
    old_load, old_prepare = study.load, study.prepare
    try:
        identity = {'constructed': study.digest({k: v.tolist() if isinstance(v, np.ndarray) else v for k, v in table.items()}),
                    'implementation': study.dependencies()}
        study.load = lambda inputs: ({}, np.array([], int), table['census'], 1., identity)
        study.prepare = lambda *args, **kwargs: table
        yield
    finally:
        study.load, study.prepare = old_load, old_prepare


def signed_proofs(output):
    output = Path(output); output.mkdir(parents=True, exist_ok=True); results = {}
    old = study.fit.CLOCK
    try:
        for world in ('recent', 'distance'):
            path = output/world; path.mkdir(exist_ok=True)
            study.fit.CLOCK = study.bounded.clock_state(path, {'max_wall_seconds': 165})
            x, y, person, expected = planted(world)
            result = study.panel(path, x, y, person, 'constructed-'+world, {'added': 0, 'limit': 2000})
            assert result['status'] == 'ok', result
            estimate = result['primary']['estimate']; lo, hi = result['primary']['interval']
            assert estimate*expected > 0 and lo <= expected <= hi, (world, estimate, lo, hi, expected)
            bank = study.seal.read(path/'DRAWS.json')
            assert len(bank['draws']) == 2000 and not any(d.get('failure') for d in bank['draws'])
            # Independent absolute-value formula on every fitted coefficient row.
            for draw in [bank['point'], *bank['draws']]:
                beta = np.zeros(9); beta[[8, 3, 4]] = draw['value'][:3]
                assert np.allclose(study.math.reference_contrast(beta), draw['value'], atol=1e-15, rtol=0)
            results[world] = {'expected': expected, 'result': result}
    finally:
        study.fit.CLOCK = old
    study.io.write_json(output/'SIGNED_FIXTURE.json', {'passed': True, 'worlds': results,
        'record_kind': 'run', 'theory_tags': ['H15-T6'], 'by_construction': True, 'activation': [],
        'all_2000_draws_per_world': True, 'expectations_prespecified_not_generated_by_adapter': True})
    return results


def null_chain(output):
    output = Path(output); table = paired_null()
    small = {'phase': 'RR3', 'draws': 2000, 'max_new_draws': 1, 'max_wall_seconds': 165}
    full = {**small, 'max_new_draws': 10000}
    with prepared_boundary(table):
        first = study.execute(output, {}, small)
        assert first['status'] == 'yielded' and first['completed'] == 1
        complete = study.execute(output, {}, full)
        assert complete['complete_card'] is True
        paused = study.verify(output, {}, small)
        assert paused['status'] == 'yielded' and paused['verified'] is False
        verified = study.verify(output, {}, full)
        assert verified['verified'] is True
    for row in [complete['primary_panel'], *complete['secondary_actual_attempt_panels'].values()]:
        if row['status'] == 'ok':
            assert row['draws'] == 2000
            assert abs(row['primary']['estimate']) < 1e-10
            assert max(map(abs, row['primary']['interval'])) < 1e-10
            assert row['primary']['outcome'] == 'band-null'
    proof = {'passed': True, 'execute_paused_then_complete': True, 'verify_paused_then_complete': True,
        'record_kind': 'run', 'theory_tags': ['H15-T6'], 'by_construction': True, 'activation': [],
        'intended_draws_each_supported_panel': 2000, 'verified': verified,
        'source_boundary': 'constructed prepared numerical table; source formula verified separately'}
    study.io.write_json(output/'FIXTURE.json', proof)
    return proof
