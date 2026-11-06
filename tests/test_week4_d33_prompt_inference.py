import json
from pathlib import Path
import pytest
from threadpoolctl import threadpool_limits
from runners.drive.cards import week4_d33_prompt_inference as card
from runners.drive.cards.timing_census import read


@pytest.mark.parametrize('beta', [-.8, 0., .8])
def test_signed_points_and_independent_dense_arithmetic(beta):
    with threadpool_limits(limits=1):
        point = card.dense_check(card.fixture(beta))
    assert abs(point['own']-beta) < .04
    assert abs(point['donor']-.35) < .04


def test_complete_interleaved_cost_and_fresh_replay(tmp_path):
    def loader(inputs):
        return card.fixture(.8), dict(constructed=True)
    config = card.configuration('cost')
    card.one_pass(tmp_path, {}, config, loader=loader)
    assert card.one_pass(tmp_path, {}, config, True, loader)['full_fresh_inference_replay']
    block = read(tmp_path/'inference/block-00.json')
    assert len(block['samples']) == 200 and len(block['controls']) == 20
    assert all(set(r) == {'primary', 'original_own_sensitivity'} for r in block['samples'])
    assert all(set(r) == {'own_surprise', 'outcome'} for r in block['controls'])
    assert not (tmp_path/'SUMMARY.json').exists()
    changed = read(tmp_path/'PROBE.json'); changed['blocks'] = 2
    (tmp_path/'PROBE.json').write_text(json.dumps(changed), encoding='utf8')
    with pytest.raises(ValueError, match='Complete inference replay differs'):
        card.one_pass(tmp_path, {}, config, True, loader)


def test_changed_config_and_missing_source_refuse(tmp_path):
    with pytest.raises(ValueError, match='Frozen inference configuration'):
        card.execute(tmp_path, {}, dict(card.configuration('full'), bootstrap_draws=20))
    with pytest.raises(ValueError, match='Exact prepared inputs'):
        card.load({})


def test_collinear_focal_does_not_become_completed_cost(tmp_path):
    rows = card.fixture(.8)
    for row in rows:
        row['own_surprise'] = row['donor_surprise']
    with pytest.raises(ValueError, match='Cost block incomplete'):
        card.one_pass(tmp_path, {}, card.configuration('cost'), loader=lambda _: (rows, {}))


def test_known_null_checks_coverage_not_noise_point_sign():
    def result(low, high, state):
        return dict(state='complete', primary=dict(own=dict(ci_low=low, ci_high=high, state=state)))
    card.check_known_interval(result(-.1, .1, 'marginal'), 'null')
    card.check_known_interval(result(-.1, .1, 'null'), 'null')
    with pytest.raises(ValueError):
        card.check_known_interval(result(.01, .1, 'positive'), 'null')
    with pytest.raises(ValueError):
        card.check_known_interval(result(-.1, -.01, 'negative'), 'positive')
