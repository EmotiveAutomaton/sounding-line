import math

import pytest

from runners.stage9.information_selection import acquisition, choose_observation, maximin_regret
from runners.stage9.program_inference import Budget

FACTOR = 'observation_and_future_given_hypothesis'


def fixture():
    prior = {str(i): .25 for i in range(4)}
    future = {str(i): {'a': float(i < 2), 'b': float(i >= 2)} for i in range(4)}
    likelihoods = {
        'noise': {h: {'a': 1/3, 'b': 1/3, 'c': 1/3} for h in prior},
        'irrelevant': {str(i): {'a': float(i % 2 == 0), 'b': float(i % 2 != 0)} for i in range(4)},
        'useful': {str(i): {'a': .75 if i < 2 else .25, 'b': .25 if i < 2 else .75} for i in range(4)}}
    offers = {k: {'content_id': k, 'likelihoods': v, 'cost_nats': 0.} for k, v in likelihoods.items()}
    return prior, future, offers


def test_noise_model_uncertainty_and_consequence_have_different_exact_answers():
    prior, future, offers = fixture()
    noise = acquisition(prior, offers['noise']['likelihoods'], future, Budget(100), conditional_independence=FACTOR)
    irrelevant = acquisition(prior, offers['irrelevant']['likelihoods'], future, Budget(100), conditional_independence=FACTOR)
    useful = acquisition(prior, offers['useful']['likelihoods'], future, Budget(100), conditional_independence=FACTOR)
    assert noise['observation_entropy_nats'] == pytest.approx(math.log(3))
    assert noise['expected_model_information_nats'] == 0
    assert noise['expected_future_log_gain_nats'] == 0
    assert irrelevant['expected_model_information_nats'] == pytest.approx(math.log(2))
    assert irrelevant['expected_future_log_gain_nats'] == 0
    # Independent Bernoulli-channel calculation.
    expected = .75*math.log(1.5)+.25*math.log(.5)
    assert useful['expected_future_log_gain_nats'] == pytest.approx(expected, abs=1e-14)
    assert choose_observation(prior, offers, future, 'entropy', Budget(100))['selected'] == 'noise'
    assert choose_observation(prior, offers, future, 'model_information', Budget(100))['selected'] == 'irrelevant'
    assert choose_observation(prior, offers, future, 'future_prediction', Budget(100))['selected'] == 'useful'


def test_expected_gain_equals_direct_joint_log_score_difference():
    prior, future, offers = fixture()
    value = acquisition(prior, offers['useful']['likelihoods'], future, Budget(100), conditional_independence=FACTOR)
    # Enumerate the complete joint distribution independently: P(H)P(O|H)P(Y|H).
    gain = 0.
    for h, weight in prior.items():
        for observation, likelihood in offers['useful']['likelihoods'][h].items():
            for target, target_probability in future[h].items():
                if target_probability:
                    gain += weight*likelihood*target_probability*(
                        math.log(value['outcomes'][observation]['future'][target])-math.log(.5))
    assert gain == pytest.approx(value['expected_future_log_gain_nats'], abs=1e-14)


def test_duplicate_evidence_cannot_be_bought_twice_and_cost_changes_stopping():
    prior, future, offers = fixture()
    offers['z_duplicate'] = dict(offers['useful'])
    selected = choose_observation(prior, offers, future, 'future_prediction', Budget(100))
    assert selected['excluded']['z_duplicate'] == 'duplicate offered evidence'
    stopped = choose_observation(prior, offers, future, 'future_prediction', Budget(100), seen=['useful'])
    assert stopped['stop']
    offers['useful']['cost_nats'] = 1.
    assert choose_observation(prior, offers, future, 'future_prediction', Budget(100))['stop']


def test_changed_reader_objective_changes_valuable_evidence():
    prior, _, offers = fixture()
    other_target = {str(i): {'a': float(i % 2 == 0), 'b': float(i % 2 != 0)} for i in range(4)}
    assert choose_observation(prior, offers, other_target, 'future_prediction', Budget(100))['selected'] == 'irrelevant'


def test_maximin_regret_matches_hand_computed_policy_values():
    environments = {
        'degenerate': {'h1': {'left': 1., 'right': 1.}, 'h2': {'left': 1., 'right': 1.}},
        'weak': {'h1': {'left': .6, 'right': .4}, 'h2': {'left': .4, 'right': .6}},
        'diagnostic': {'h1': {'left': 1., 'right': 0.}, 'h2': {'left': 0., 'right': 1.}}}
    result = maximin_regret({'h1': .5, 'h2': .5}, environments, Budget(100))
    assert result['selected'] == 'diagnostic'
    assert result['environments']['degenerate']['minimum_bayesian_regret'] == 0.
    assert result['environments']['weak']['minimum_bayesian_regret'] == pytest.approx(.1)
    assert result['environments']['diagnostic']['minimum_bayesian_regret'] == .5
    # If uncertainty vanishes, every environment has zero regret under its best policy.
    settled = maximin_regret({'h1': 1., 'h2': 0.}, environments, Budget(100))
    assert all(v['minimum_bayesian_regret'] == 0. for v in settled['environments'].values())


def test_selection_refuses_omitted_support_unknown_factorization_and_conflicting_ids():
    prior, future, offers = fixture()
    with pytest.raises(ValueError, match='factorization'):
        acquisition(prior, offers['useful']['likelihoods'], future, Budget(100), conditional_independence=None)
    offers['noise']['content_id'] = 'useful'
    with pytest.raises(ValueError, match='conflicting likelihood'):
        choose_observation(prior, offers, future, 'future_prediction', Budget(100))
    with pytest.raises(ValueError, match='missing shared policy'):
        maximin_regret({'h1': .5, 'h2': .5}, {'a': {'h1': {'left': 1.}, 'h2': {'right': 1.}}}, Budget(100))
