"""Bounded constructed IN13/IN15 fixtures; no human source or native launch.

DESIGN CHECK: Packet W, LESSONS 2-3. Expected values come from analytic
normal/marker AUCs, independently specified linear effects and the supplied
corrected multinomial-choice construction, never from the adapter under test.
"""
from contextlib import contextmanager
import hashlib
import math
from pathlib import Path
import numpy as np
import pandas as pd
from . import week6_in13_v1 as in13
from . import week6_in15_v1 as in15
from . import week6_in13_in15_common_v1 as common


def packet_in13():
    rng = np.random.default_rng(13); n = 4000
    y = np.repeat([1, 0], n//2); writers = np.tile(np.arange(400), 10)[rng.permutation(n)]
    first = rng.normal(np.where(y == 1, .25, -.25), 1.)
    other = rng.normal(0, 1, (n, 20)); marker = ((y == 1) & (rng.random(n) < .30)).astype(float)
    return y, writers, np.column_stack([first, other]), marker


def profiles(people=32):
    rows = []
    for person in range(people):
        for label_number, label in enumerate(common.LABELS):
            style = np.sin(person*1.7)+.3*np.cos(label_number)
            row = {'text_id': f't-{person:03}-{label}', 'prolific_id': f'p-{person:03}', 'emotion': label,
                   'discovery_half': person % 2 == 0, 'writer_order': person, 'source_ordinal': len(rows),
                   'hidden_emo_text': 'ordinary common report'}
            row.update({item: float(3+.3*style+.1*np.sin(person*(i+1)+label_number)) for i, item in enumerate(common.APPRAISALS)})
            row['urgency'] = float(3+.3*style+.6*(label == 'fear'))
            rows.append(row)
    return pd.DataFrame(rows)


def null_pairs(people=24):
    frame = profiles(people)
    for column in common.APPRAISALS: frame[column] = 3.
    return frame


def profile_known_world(amplitude=.6, writers_per_half=20):
    """Balanced label opportunities give a separately derived exact answer.

    All writers supply every label. Every ordinary item is 3 + writer style;
    urgency additionally receives amplitude on fear. With style controlled,
    the raw label-v-rest gap is amplitude for fear and -amplitude/12 otherwise.
    Discovery SD follows the independent sum-of-squares decomposition below.
    """
    halves = {False: [], True: []}; ordinal = 0
    while min(map(len, halves.values())) < writers_per_half:
        person = f'constructed-profile-writer-{ordinal:04}'
        discovery = int(hashlib.sha256(person.encode()).hexdigest(), 16) % 2 == 0
        if len(halves[discovery]) < writers_per_half: halves[discovery].append(person)
        ordinal += 1
    styles = [.4*math.sin(index+.3) for index in range(writers_per_half)]
    style_mean = math.fsum(styles)/writers_per_half
    # Each writer has all 13 labels: cross term between style and label is zero.
    ss = 13*math.fsum((s-style_mean)**2 for s in styles)+writers_per_half*amplitude**2*12/13
    discovery_sd = math.sqrt(ss/(13*writers_per_half-1))
    roster = sorted(halves[False]+halves[True]); ranks = {person: i for i, person in enumerate(roster)}
    rows = []
    for discovery, people in halves.items():
        for person, style in zip(people, styles, strict=True):
            for label in common.LABELS:
                row = {'text_id': f'{person}-{label}', 'prolific_id': person, 'emotion': label,
                    'discovery_half': discovery, 'writer_order': ranks[person], 'source_ordinal': len(rows),
                    'hidden_emo_text': 'constructed ordinary report'}
                row.update({item: 3+style for item in common.APPRAISALS})
                row['urgency'] += amplitude*(label == 'fear')
                rows.append(row)
    expected = {label: abs(amplitude if label == 'fear' else -amplitude/12)/discovery_sd for label in common.LABELS}
    return pd.DataFrame(rows), {'signed_urgency': expected, 'discovery_SD': discovery_sd,
        'other_signed_cells': 0., 'writers_each_half': writers_per_half, 'reports': len(rows)}


def profile_chain(output, amplitude):
    frame, expected = profile_known_world(amplitude)
    result = chain(in13, frame, output, 'IN13A')
    assert result['total_cells'] == 273 and result['primary_scalar'] is None
    assert result['split_counts']['discovery_writers'] == 20
    assert result['split_counts']['confirmation_writers'] == 20
    answers = []
    for row in result['table']:
        target = expected['signed_urgency'][row['label']] if row['item'] == 'urgency' else 0.
        assert row['draws'] == 2000 and row['failed_draws'] == []
        assert abs(row['estimate']-target) < 1e-10
        assert np.allclose(row['interval'], [target, target], atol=1e-10, rtol=0)
        if row['item'] == 'urgency':
            assert abs(row['scale_SD']-expected['discovery_SD']) < 1e-12
        if target > .1: assert row['outcome'] == 'supports'
        else: assert row['direction'] == 0 and 'outcome' not in row
        answers.append(target)
    # Inspect every retained execute and independent draw, not only intervals.
    for relative in ('DRAWS.json', 'independent-replay/DRAWS.json'):
        bank = common.seal.read(Path(output)/relative)
        assert len(bank['draws']) == 2000
        assert np.allclose(bank['point'], answers, atol=1e-10, rtol=0)
        assert np.allclose(bank['draws'], np.array(answers)[None, :], atol=1e-10, rtol=0)
    proof = {'passed': True, 'constructed_amplitude': amplitude, 'expected': expected,
        'rows_checked': 273, 'execute_draws': 2000, 'independent_draws': 2000,
        'pause_reentry_both_paths': True, 'all_draw_values_checked': True,
        'record_kind': 'run', 'by_construction': True, 'theory_tags': ['H18-S1'], 'activation': []}
    common.io.write_json(Path(output)/'FIXTURE.json', proof)
    return proof


def packet_in15(slope=.4, seed=151, reports=20000):
    rng = np.random.default_rng(seed); k = 13
    baseline = rng.normal(0, 1, (reports, 1, k)); baseline[np.arange(reports), 0, rng.integers(0, k, reports)] += 2.
    prior = rng.normal(0, 1, (reports, 5, k)); choice = (baseline+slope*prior+rng.gumbel(size=prior.shape)).argmax(2)
    chosen = choice[:, :, None] == np.arange(k)[None, None, :]
    count = chosen.sum(axis=1); ok = (count > 0) & (count < 5)
    oracle = ((prior*chosen).sum(axis=1)/np.maximum(count, 1)-(prior*~chosen).sum(axis=1)/np.maximum(5-count, 1))[ok].mean()
    labels = (*common.FEELINGS, 'no-emotion')
    # Every reader occurs on multiple reports in bounded chain fixtures.
    frame = pd.DataFrame(prior[:, :, :12].reshape(-1, 12), columns=common.FEELINGS)
    frame['text_id'] = np.repeat([f't-{i:06}' for i in range(reports)], 5)
    frame['prolific_id'] = [f'p-{(t*3+r)%max(25, reports//2):06}' for t in range(reports) for r in range(5)]
    frame['emotion'] = [labels[i] for i in choice.ravel()]
    frame['original_emotion'] = np.repeat([labels[i] for i in baseline[:, 0].argmax(axis=1)], 5)
    frame['unpleasantness'] = 3+prior[:, :, :7].mean(axis=2).ravel()
    return frame, float(oracle)


@contextmanager
def table_boundary(module, frame):
    original = module.load
    try:
        module.load = lambda inputs, config: (frame.copy(), {'constructed': True, 'table': common.frame_digest(frame)})
        yield
    finally:
        module.load = original


def chain(module, frame, output, phase):
    small = {'phase': phase, 'scope': 'qualified_real_events', 'max_new_draws': 1, 'max_wall_seconds': 300}
    large = {**small, 'max_new_draws': 2000}
    with table_boundary(module, frame):
        assert module.execute(output, {}, small)['status'] == 'yielded'
        result = module.execute(output, {}, large)
        assert result['complete_card']
        assert module.verify(output, {}, small)['verified'] is False
        assert module.verify(output, {}, large)['verified'] is True
    return result
