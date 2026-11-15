"""Constructed-only acceptance candidate for the additive IN12 component report."""
from copy import deepcopy
from pathlib import Path
import hashlib
import numpy as np
import pandas as pd
import pytest
from runners.drive.cards import week5_in12_components_v1 as card


def literal_prepared(eligible=300):
    keys = ['a', 'b', 'c', 'd']
    x = [-1., -1., 1., 1.]
    y = [-1., 1., -1., 1.]
    nn = [(k, a, a, 1.) for k, a in zip(keys, x, strict=True)]
    cross = [(k, a, b, 1.) for k, a, b in zip(keys, x, y, strict=True)]
    return {'pairs': (nn, cross, eligible), 'keys': keys, 'scales': {}}


@pytest.fixture(scope='module')
def complete_fixture():
    # Entirely invented numeric rows. Nothing from an original source is loaded.
    rows = []
    for index in range(300):
        for prompt, offset in [('anger', 0), ('fear', 1), ('joy', 2)]:
            y = np.sin(index * (.31 + offset * .07)) + .4 * np.cos(index * .17) + (index % (7 + offset)) / 5
            rows.append({'text_id': f't{index:03}-{offset}', 'prolific_id': f'p{index:03}',
                         'emotion': prompt, 'N': 1. + index % 7, 'intensity': y,
                         'confidence': float(index % 5),
                         **{name: float((index + j) % 4) for j, name in enumerate(card.math.STYLE)}})
    frame = pd.DataFrame(rows)
    original = card.math.prepare(frame)
    # Only the original paired branch is the oracle for this reporting repair.
    # Regression panels deliberately remain absent and are never being qualified.
    original['panels'] = {name: None for name in ('pooled', *card.math.NEGATIVE, *card.math.POSITIVE)}
    bank = {'point': card.math.evaluate(original, dict.fromkeys(original['keys'], 1)),
            'draws': [card.math.evaluate(original, card.math.resample(original['keys'], d)) for d in range(2000)]}
    prepared = card.prepare_pairs(frame)
    result = {'paired_support': card.support_metadata(prepared), 'scales': original['scales']}
    return frame, bank, result, {'constructed_fixture': True, 'no_human_source': True}


def test_literal_signed_zero_and_independent_formula():
    prepared = literal_prepared()
    counts = dict.fromkeys(prepared['keys'], 1)
    for independent in (False, True):
        answer = card.evaluate(prepared, counts, independent)
        assert answer['value'][card.NEGATIVE] == 1.
        assert answer['value'][card.CROSS] == 0.
        assert answer['value'][card.DIFFERENCE] == 1.
        prepared['pairs'][1][:] = [(k, x, -x, w) for k, x, _, w in prepared['pairs'][1]]
        answer = card.evaluate(prepared, counts, independent)
        assert answer['value'][card.CROSS] == -1.
        assert answer['value'][card.DIFFERENCE] == 2.
        prepared = literal_prepared()


def test_prompt_means_equal_writer_pair_weight_and_original_keys():
    table = pd.DataFrame([
        ('a', 'anger', 1.), ('a', 'anger', 3.), ('a', 'fear', -1.), ('a', 'joy', 2.),
        ('b', 'anger', -2.), ('b', 'fear', 2.), ('b', 'guilt', 4.), ('b', 'joy', -1.), ('b', 'pride', 1.),
        ('c', 'anger', 0.), ('c', 'joy', 1.),
    ], columns=['prolific_id', 'emotion', 'intensity_z'])
    nn, cross, eligible = card.math.pair_rows(table)
    assert eligible == 2 and len(nn) == 8 and len(cross) == 8
    for pairs in (nn, cross):
        for person in ('a', 'b'):
            assert sum(row[3] for row in pairs if row[0] == person) == pytest.approx(1.)
    assert ('a', 2., -1., .5) in nn and not any(r[0] == 'c' for r in nn + cross)


def test_original_eligibility_common_support_and_undefined_component():
    prepared = literal_prepared(299)
    counts = dict.fromkeys(prepared['keys'], 1)
    assert all(v is None for v in card.evaluate(prepared, counts)['value'].values())
    prepared = literal_prepared()
    assert all(v is None for v in card.evaluate(prepared, {'a': 4})['value'].values())
    prepared['pairs'][1][:] = [(k, x, 1., w) for k, x, _, w in prepared['pairs'][1]]
    answer = card.evaluate(prepared, counts)
    assert answer['value'][card.NEGATIVE] == 1.
    assert answer['value'][card.CROSS] is None and answer['value'][card.DIFFERENCE] is None
    assert set(answer['failures']) == {card.CROSS, card.DIFFERENCE}


def test_original_difference_mismatch_or_missing_refused():
    prepared = literal_prepared(); answer = card.evaluate(prepared, dict.fromkeys(prepared['keys'], 1))
    original = {'value': {card.DIFFERENCE: answer['value'][card.DIFFERENCE]}, 'failures': {}}
    card.compare_difference(answer, original, 300)
    original['value'][card.DIFFERENCE] += .01
    with pytest.raises(ValueError): card.compare_difference(answer, original, 300)
    with pytest.raises(ValueError): card.compare_difference(answer, {'value': {}, 'failures': {}}, 300)
    absent = card.evaluate(literal_prepared(299), {})
    card.compare_difference(absent, {'value': {}, 'failures': {}}, 299)
    with pytest.raises(ValueError): card.compare_difference(absent, original, 299)


def test_complete_bank_prefix_reentry_and_independent_replay(tmp_path, monkeypatch, complete_fixture):
    frame, bank, result, identity = complete_fixture
    monkeypatch.setattr(card, 'load_original', lambda inputs, output: (frame, bank, result, identity))
    monkeypatch.setattr(card, 'check_origin', lambda *args: None)
    output = tmp_path / 'additive'
    prefix = {'phase': 'IN12-components', 'draws': 2000, 'max_new_draws': 100, 'max_wall_seconds': 90}
    answer = card.execute(output, {}, prefix)
    assert answer['status'] == 'yielded' and answer['completed'] == 100
    before = card.seal.read(output / 'COMPONENT_DRAWS.json')['draws']
    full = {**prefix, 'max_new_draws': 2000}
    answer = card.execute(output, {}, full)
    saved = card.seal.read(output / 'COMPONENT_DRAWS.json')
    assert saved['draws'][:100] == before and len(saved['draws']) == 2000
    assert set(answer['secondary_components']) == set(card.COMPONENTS)
    for component in answer['secondary_components'].values():
        assert component['draws'] == 2000 and component['descriptive'] is True
        assert component['failed_draws'] == [] and 'interval' in component
        assert 'outcome' not in component and 'bar' not in component
    replay_prefix = card.verify(output, {}, prefix)
    assert replay_prefix['status'] == 'yielded' and replay_prefix['verified'] is False
    assert card.verify(output, {}, full)['verified'] is True
    assert (output / 'independent-replay/RESULT.json').exists()
    # This is a hostile complete-bank mutation, preserving the difference itself.
    saved['draws'][7]['value'][card.NEGATIVE] += .1
    saved['draws'][7]['value'][card.CROSS] += .1
    card.seal.checkpoint(output / 'COMPONENT_DRAWS.json', saved)
    with pytest.raises(ValueError): card.verify(output, {}, full)


def test_owned_yield_stop_and_checkpoint_mutation(tmp_path, complete_fixture):
    frame, bank, result, identity = complete_fixture
    config = {'phase': 'IN12-components', 'max_new_draws': 1, 'max_wall_seconds': 90}
    output = tmp_path / 'yield'; output.mkdir()
    (output / 'YIELD_REQUEST.json').write_text('{}')
    answer = card.calculate(frame, output, bank, result, identity, config)
    assert answer['status'] == 'yielded' and answer['completed'] == 0
    (output / 'YIELD_REQUEST.json').unlink()
    answer = card.calculate(frame, output, bank, result, identity, config)
    assert answer['completed'] == 1
    (output / 'STOP_REQUEST.json').write_text('{}')
    replay = output / 'independent-replay'
    answer = card.calculate(frame, replay, bank, result, identity, config, True)
    assert answer['status'] == 'yielded' and answer['completed'] == 0
    with pytest.raises(ValueError):
        card.calculate(frame, output, bank, result, {'changed_source': True}, config)
    path = output / 'COMPONENT_DRAWS.json'
    path.write_text(path.read_text() + ' ')
    with pytest.raises(ValueError): card.calculate(frame, output, bank, result, identity, config)


def test_ordinal_and_failed_draw_dispositions(tmp_path, complete_fixture):
    frame, bank, result, identity = complete_fixture
    config = {'phase': 'IN12-components', 'max_new_draws': 1}
    output = tmp_path / 'ordinal'
    card.calculate(frame, output, bank, result, identity, config)
    path = output / 'COMPONENT_DRAWS.json'; saved = card.seal.read(path)
    saved['draws'][0]['ordinal'] = 1; card.seal.checkpoint(path, saved)
    with pytest.raises(ValueError): card.calculate(frame, output, bank, result, identity, config)
    point = {'value': {card.CROSS: .2}, 'failures': {}}
    draws = [{'value': {card.CROSS: .2}, 'failures': {}} for _ in range(2000)]
    draws[13]['value'][card.CROSS] = None
    answer = card.old.summarize(card.CROSS, point, draws, 20)
    assert answer['status'] == 'invalid_uncertainty' and answer['failed_draws'] == [13]
    assert 'interval' not in answer and 'outcome' not in answer
    answer = card.old.summarize(card.CROSS, point, [point] * 2000, 19)
    assert answer['status'] == 'below floor, descriptive' and 'outcome' not in answer


def test_frozen_origin_checks_and_original_output_is_never_destination(tmp_path, monkeypatch):
    monkeypatch.setattr(card, 'REPO', tmp_path)
    monkeypatch.setattr(card, 'ORIGINAL_ROOT', 'original')
    monkeypatch.setattr(card, 'SOURCE_ROOT', 'source')
    original = tmp_path / 'original'; original.mkdir()
    (tmp_path / 'source').mkdir()
    pin = original / 'COMPLETE.json'; pin.write_text('{}')
    monkeypatch.setattr(card, 'ORIGIN_PINS', {'original/COMPLETE.json': hashlib.sha256(pin.read_bytes()).hexdigest()})
    monkeypatch.setattr(card, 'SCIENCE_PINS', {})
    inputs = {'analysis_run': str(original)}
    card.check_origin(inputs, tmp_path / 'supplement')
    with pytest.raises(ValueError): card.check_origin(inputs, original / 'output')
    with pytest.raises(ValueError): card.check_origin(inputs, tmp_path)
    with pytest.raises(ValueError): card.check_origin({'analysis_run': str(tmp_path / 'other')})
    pin.write_text('{"mutated":true}')
    with pytest.raises(ValueError): card.check_origin(inputs)


@pytest.mark.parametrize('patch', [{'phase': 'IN12'}, {'draws': 100}, {'max_new_draws': 0},
                                  {'max_new_draws': True}, {'seed': 20261107}])
def test_no_scientific_or_partial_bank_configuration(patch):
    with pytest.raises(ValueError): card.settings({'phase': 'IN12-components', **patch})
