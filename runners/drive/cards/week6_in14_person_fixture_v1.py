"""Frozen whole-survey calibration, not independent simulated pair rows."""
import numpy as np
import pandas as pd
from .week6_in14_math_v1 import FEELINGS, NEGATIVE
from . import week6_in14_person_v1 as person

FAMILIES = ('iid_innovations', 'ar1_innovations', 'survey_measurement_ma1')
TARGETS = (0., .5, 1.)


def world(target, family, writers=600):
    if target not in TARGETS or family not in FAMILIES or writers % 3 or writers < 12:
        raise ValueError('Frozen balanced calibration world required')
    rng = np.random.default_rng(np.random.SeedSequence([20261115, FAMILIES.index(family), int(target * 10)]))
    half = np.empty((writers, 2)); inventory = np.empty(writers)
    sizes = np.tile([4, 8, 12], writers // 3)
    for size in (4, 8, 12):
        indices = np.flatnonzero(sizes == size); n = len(indices)
        vectors = rng.normal(size=(n, 3)); vectors -= vectors.mean(axis=0)
        q, _ = np.linalg.qr(vectors)
        left = .6 * np.sqrt(n - 1) * q[:, 0]
        right = .6 * np.sqrt(n - 1) * (target * q[:, 0] + np.sqrt(1 - target ** 2) * q[:, 1])
        full = (left + right) / 2
        inventory[indices] = .4 * full / np.std(full, ddof=1) + np.sqrt(.84) * np.sqrt(n - 1) * q[:, 2]
        half[indices] = np.column_stack([left, right])
    rows = []
    for i, size in enumerate(sizes):
        order = rng.permutation(11)
        prompts = [int(order[t % 11]) for t in range(size + 1)]
        innovation = np.sqrt(.35) * rng.normal(size=(size + 1, 1)) + np.sqrt(.65) * rng.normal(size=(size + 1, 11))
        if family == 'ar1_innovations':
            for t in range(1, size + 1):
                innovation[t] = .4 * innovation[t - 1] + np.sqrt(.84) * innovation[t]
        latent = np.empty((size + 1, 11)); latent[0] = rng.normal(size=11)
        for t in range(size):
            first, second = prompts[t:t + 2]
            prompt = np.arange(11) == first
            same = np.array([(feeling in NEGATIVE) == (FEELINGS[first] in NEGATIVE) for feeling in FEELINGS]) & ~prompt
            latent[t + 1] = .6 * latent[t] + half[i, int(t >= size // 2)] * prompt + .2 * same + .15 * (np.arange(11) == second)
            if family != 'survey_measurement_ma1':
                latent[t + 1] += innovation[t + 1]
        observed = latent + innovation if family == 'survey_measurement_ma1' else latent
        for t in range(size):
            first, second = prompts[t:t + 2]
            for j, feeling in enumerate(FEELINGS):
                rows.append({'prolific_id': f'w{i}', 'pair_id': f'w{i}s{t}:w{i}s{t+1}',
                    'first_text_id': f'w{i}s{t}', 'second_text_id': f'w{i}s{t+1}',
                    'raw_pair_ordinal': t, 'feeling': feeling, 'gap_minutes': 6.,
                    'baseline': observed[t, j], 'outcome': observed[t + 1, j],
                    'prompt': float(j == first), 'same_valence': float(j != first and (feeling in NEGATIVE) == (FEELINGS[first] in NEGATIVE)),
                    'second_prompt': float(j == second), 'N': inventory[i]})
    truth = {'half_correlation': float(np.corrcoef(half.T)[0, 1]),
             'full_trait_correlation': float(np.corrcoef(half.mean(axis=1), inventory)[0, 1]),
             'writers': writers, 'pair_counts': {str(n): int(np.sum(sizes == n)) for n in (4, 8, 12)}}
    return pd.DataFrame(rows), truth


def calibration():
    worlds = []; qualified = True
    for family in FAMILIES:
        for target in TARGETS:
            frame, truth = world(target, family)
            estimate = person.evaluate(person.prepare(frame))
            half = estimate.get('half_diagnostic')
            trait = estimate.get('trait', {}).get('adjusted_relation')
            half_pass = half is not None and np.isfinite(half) and abs(half - target) <= .1
            trait_pass = trait is not None and np.isfinite(trait) and abs(trait - .4) <= .1
            passed = estimate['status'] == 'ok' and bool(half_pass and trait_pass)
            worlds.append({'family': family, 'target': target, 'truth': truth, 'estimate': estimate,
                           'half_gate_pass': bool(half_pass), 'trait_gate_pass': bool(trait_pass), 'passed': passed})
            qualified = qualified and passed
    return {'constructed_only': True, 'candidate': 'covariance-aware-AR1-by-feeling-v1',
            'qualified': qualified, 'all_nine_worlds_retained': len(worlds) == 9,
            'fixed_absolute_tolerance': .1, 'worlds': worlds,
            'human_secondary': 'held pending complete integration' if qualified else 'instrument hold: fixed calibration failed'}
