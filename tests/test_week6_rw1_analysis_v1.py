"""Prospective constructed-only RW1 rulers; no human source or genuine annotation.

The factorial finite distribution supplies exact residual correlations. It is
an arithmetic fixture, not Monte Carlo evidence of interval coverage.
"""
import copy
from pathlib import Path

import numpy as np
import pytest

from runners.drive.cards import week6_rw1_v1 as rw
from runners.drive.cards import week6_rw1_context_v1 as context
from runners.drive.cards import week6_rw1_source_v1 as source
from runners.drive.cards import week6_rw1_source_v2 as forms
from runners.drive.cards import week6_rw1_runner_v1 as runner


def constructed_records(rho=-.15):
    assert rho in (-.15, 0)
    # Each half has the same finite distribution: E[P*E]=rho, independently
    # crossed with two balanced nuisance signs. All source ratings are integers.
    pattern = []
    for p in (-1, 1):
        for e in (-1, 1):
            count = 20 if rho == 0 else 17 if p == e else 23
            for b in (-1, 1):
                for length in (-1, 1): pattern.extend([(p, e, b, length)] * count)
    people = [f'constructed-{i:04d}' for i in range(640)]
    halves = rw.fixed_halves(people); records = [None] * len(people)
    suffixes = [chr(97 + i // 26) + chr(97 + i % 26) for i in range(200)]
    for half in (0, 1):
        for ordinal, (p, e, b, length) in zip(np.flatnonzero(halves == half), pattern, strict=True):
            sentences = [('I will act' if j < (3 if p == 1 else 1) else 'People can wait') + ' neutral' for j in range(4)]
            words = [(('zbad' if b == 1 else 'aneutral') + s) for s in suffixes]
            sentences[0] += ' ' + ' '.join(words) + (' neutral' * (40 if length == 1 else 0))
            worry = 5 + e + b + length
            values = {'text_long': '. '.join(sentences) + '.', 'worry': str(worry), 'anxiety': str(worry),
                      'fear': str(5 + p * e), 'relaxation': str(10 - worry), 'sadness': str(5 + b * length)}
            item = source.person_record(values, int(ordinal), b'c' * 32, 'constructed-only')
            item['person'] = people[ordinal]; records[ordinal] = item
    return records


@pytest.mark.parametrize('rho', [-.15, 0])
def test_complete_sentence_vocabulary_primary_known_answers(rho):
    data = rw.prepare(constructed_records(rho)); point = rw.estimate(data, np.ones(640), keep_words=True)
    assert point['targets']['worry']['status'] == 'ok'
    assert point['targets']['worry']['estimate'] == pytest.approx(rho, abs=1e-12)
    assert point['targets']['relaxation']['estimate'] == pytest.approx(-rho, abs=1e-12)
    assert all(len(v['words']) == 200 and all(w.startswith('zbad') for w in v['words']) for v in point['vocabularies'])
    assert point['targets']['time_place_difference']['status'] == 'instrument-held'


def test_weighted_partial_matches_independent_expanded_dense_oracle():
    data = rw.prepare(constructed_records()); weights = np.random.default_rng(72).integers(1, 4, 640)
    news, _ = rw.bad_news(data, weights); z = np.column_stack((data['length'], news))
    result = rw.partial_correlation(data['plan'], data['ratings'][:, 0], z, weights)
    ii = np.repeat(np.arange(640), weights); design = np.column_stack((np.ones(len(ii)), z[ii]))
    target = np.column_stack((data['plan'][ii], data['ratings'][ii, 0]))
    residual = target - design @ np.linalg.lstsq(design, target, rcond=None)[0]
    assert result['estimate'] == pytest.approx(np.corrcoef(residual.T)[0, 1], abs=1e-12)


def test_qualified_literal_time_place_contrast_has_known_answer():
    records = constructed_records()
    for i, row in enumerate(records):
        if sum(source.marker.plan_candidate(s['text']) for s in row['sentences']) == 3:
            values = {key: str(value) for key, value in row['ratings'].items()}
            values['text_long'] = row['text_long'].replace('act neutral', 'act tomorrow')
            changed = source.person_record(values, row['source_row'], b'c' * 32, 'constructed-only')
            changed['person'] = row['person']; records[i] = changed
    # This fixture flag does not claim that real hand annotations exist.
    data = rw.prepare(records, time_place_qualified=True)
    result = rw.estimate(data, np.ones(640))['targets']
    assert result['time_place_named_worry']['estimate'] == pytest.approx(-.15, abs=1e-12)
    assert result['time_place_other_worry']['estimate'] == pytest.approx(.15, abs=1e-12)
    assert result['time_place_difference']['estimate'] == pytest.approx(-.30, abs=1e-12)
    assert result['time_place_named_worry']['people'] == result['time_place_other_worry']['people'] == 640


def test_held_out_worry_cannot_change_its_applied_vocabulary():
    data = rw.prepare(constructed_records()); original, before = rw.learned_vocabulary(data, np.ones(640), 1)
    changed = copy.deepcopy(data); changed['ratings'][data['halves'] == 0, 0] = 10 - changed['ratings'][data['halves'] == 0, 0]
    selected, after = rw.learned_vocabulary(changed, np.ones(640), 1)
    assert np.array_equal(original, selected) and before == after
    assert all(w.startswith('zbad') for w in after['words'])


def test_every_person_draw_relearns_both_vocabularies(monkeypatch):
    data = rw.prepare(constructed_records()); calls = []; original = rw.learned_vocabulary
    def spy(d, w, half):
        calls.append((half, np.asarray(w).copy())); return original(d, w, half)
    monkeypatch.setattr(rw, 'learned_vocabulary', spy)
    a = rw.bootstrap_draw(data, 7); b = rw.bootstrap_draw(data, 7)
    assert a == b and [h for h, _ in calls] == [0, 1, 0, 1]
    assert all(w.sum() == 640 and not np.all(w == 1) for _, w in calls)
    assert np.array_equal(data['halves'], rw.fixed_halves(data['people']))


def test_missing_people_remain_and_support_failure_is_not_null():
    records = constructed_records(); records[0]['ratings']['fear'] = None
    data = rw.prepare(records); point = rw.estimate(data, np.ones(640))
    assert len(data['people']) == 640 and 'missing_fear' in data['dispositions'][0]['reasons']
    assert point['targets']['worry']['people'] == 640 and point['targets']['fear']['people'] == 639
    data['ratings'][:, 0] = 5
    failed = rw.estimate(data, np.ones(640))
    assert failed['status'] == 'design cannot test' and failed['targets']['worry']['status'] == 'unsupported'


@pytest.mark.parametrize('interval,expected', [([-.3, -.06], 'supports'), ([-.06, -.05], 'inconclusive'),
    ([-.05, .05], 'against'), ([.001, .2], 'against'), ([0, .2], 'inconclusive'), ([-.2, .1], 'inconclusive')])
def test_negative_primary_boundary_states(interval, expected):
    assert rw.classify_interval(interval) == expected


def test_summary_keeps_failed_draw_and_separate_instrument_states():
    data = rw.prepare(constructed_records()); point = rw.estimate(data, np.ones(640))
    bank = []
    for value in np.linspace(-.18, -.12, 2000):
        draw = copy.deepcopy(point); draw['targets']['worry']['estimate'] = float(value); bank.append(draw)
    summary = rw.summarize(point, bank)
    assert summary['worry']['outcome'] == 'supports'
    assert summary['time_place_difference']['status'] == 'instrument-held'
    bank[17]['targets']['worry'] = {'status': 'unsupported', 'reason': 'constructed failed draw'}
    summary = rw.summarize(point, bank)
    assert summary['worry']['status'] == 'invalid uncertainty'
    assert summary['worry']['failed_draw_ordinals'] == [17] and summary['worry']['outcome'] is None


@pytest.mark.parametrize('text,named,unknown', [('I will call tomorrow.', True, False),
    ('We plan to meet at the park.', True, False), ('I intend to phone at 10:30.', True, False),
    ('I will finish in May.', True, False), ('I will march, and may stop.', False, True),
    ('I will travel to Zorbia.', False, True), ('Yesterday was sunny.', False, False)])
def test_declared_context_markers_and_unknowns(text, named, unknown):
    result = context.classify(text)
    assert result['literal_named'] is named and result['unknown_or_absent'] is unknown


def context_sample():
    rows = []
    for i in range(200):
        rows.append({'id': f'constructed-sentence-{i}', 'text': 'I will call tomorrow.' if i % 2 else 'I will call.'})
    return rows, source.marker.manifest_digest(rows)


def test_successor_blank_forms_do_not_replace_qualified_V1():
    rows, binding = context_sample(); original = source.annotation_form(rows, binding, 'hand')
    successor = forms.annotation_form(rows, binding, 'hand')
    assert all('time_place_label' not in r for r in original['annotations'])
    assert all(r['time_place_label'] is None for r in successor['annotations'])


def test_context_unknowns_use_all_200_as_denominator():
    rows, _ = context_sample(); pairs = []
    for _ in range(2):
        labels = [{'time_place_label': context.classify(r['text'])['literal_named']} for r in rows]
        hand = copy.deepcopy(labels)
        for r in hand[:41]: r['time_place_label'] = 'unknown'
        pairs.append(({'annotations': hand}, {'annotations': labels}))
    result = context.qualification(rows, pairs)
    assert result['status'] == 'instrument-unqualified' and result['unknown_hand_counts'] == [41, 41]
    assert result['list_hand_agreements'] == [159 / 200, 159 / 200]
    assert not result['production_admitted']


def test_successor_sealed_constructed_pairs_still_need_owner_review(tmp_path, monkeypatch):
    rows, binding = context_sample(); source.io.write_json(tmp_path / 'COMPLETE.json', {'constructed_only': True})
    monkeypatch.setattr(forms, 'prepared', lambda root: (Path(root), rows, binding))
    inputs = {'prepared_run': str(tmp_path)}
    for builder in ('builder_a', 'builder_b'):
        hand = forms.annotation_form(rows, binding, 'hand')
        hand.update(builder_id=builder, independently_annotated=True, provenance_sha256='constructed-only',
                    automatic_labels_seen_before_hand_seal=False)
        for row in hand['annotations']:
            row.update(label=source.marker.plan_candidate(row['text']), time_place_label=context.classify(row['text'])['literal_named'])
        hp = tmp_path / (builder + '-hand.json'); source.seal.checkpoint(hp, hand)
        listed = forms.annotation_form(rows, binding, 'list')
        listed.update(builder_id=builder, independently_annotated=True, provenance_sha256='constructed-only', hand_receipt_sha256=source.io.sha(hp))
        for row in listed['annotations']:
            row.update(label=source.marker.plan_candidate(row['text']), time_place_label=context.classify(row['text'])['literal_named'])
        lp = tmp_path / (builder + '-list.json'); source.seal.checkpoint(lp, listed)
        inputs[builder + '_hand'], inputs[builder + '_list'] = str(hp), str(lp)
    result = forms.review(inputs)
    assert result['status'] == result['context_qualification']['status'] == 'reviewable'
    assert not result['production_admitted'] and result['owner_identity_and_provenance_review_required']
    inputs['builder_b_hand'], inputs['builder_b_list'] = inputs['builder_a_hand'], inputs['builder_a_list']
    with pytest.raises(ValueError, match='distinct'): forms.review(inputs)


def test_analysis_refuses_missing_admission_and_yields_without_completion(tmp_path, monkeypatch):
    with pytest.raises(ValueError, match='owner review'): runner.load({})
    data = rw.prepare(constructed_records()); point = rw.estimate(data, np.ones(640))
    monkeypatch.setattr(runner, 'load', lambda inputs: (data, {'constructed_only': True}))
    monkeypatch.setattr(source, 'private_output', lambda path: Path(path))
    monkeypatch.setattr(rw, 'bootstrap_draw', lambda data, ordinal: copy.deepcopy(point))
    config = {'phase': 'RW1', 'draws': 2000, 'max_new_draws': 1, 'max_wall_seconds': 600}
    output = tmp_path / 'run'
    assert runner.execute(output, {}, config)['completed'] == 1
    assert runner.execute(output, {}, config)['completed'] == 2
    assert not (output / 'RESULT.json').exists()
    state = source.seal.read(output / 'STATE.json'); assert state['completed'] == 2


def test_explicit_unidentified_route_has_complete_fresh_replay(tmp_path, monkeypatch):
    data = rw.prepare(constructed_records()); data['ratings'][:, 0] = 5
    monkeypatch.setattr(runner, 'load', lambda inputs: (data, {'constructed_only': True}))
    monkeypatch.setattr(source, 'private_output', lambda path: Path(path))
    config = {'phase': 'RW1', 'draws': 2000, 'max_new_draws': 1, 'max_wall_seconds': 600}
    output = tmp_path / 'run'; result = runner.execute(output, {}, config)
    assert result['targets']['worry']['status'] == 'unsupported' and result['targets']['worry']['outcome'] is None
    assert result['draws'] == 0 and runner.verify(output, {}, config)['verified']
