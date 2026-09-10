"""Known answers for the separate quantities and independent-unit estimand."""
import math

import pytest

from runners.stage9.scoring import individual_quantities, paired_interval, classify, holm, confirmation_size


def test_predictable_signature_is_more_useful_than_rarer_noise():
    population = dict(signature=.25, noise=.01, ordinary=.74)
    individual = dict(signature=.80, noise=.02, ordinary=.18)
    signature = individual_quantities(population, individual, 'signature')
    noise = individual_quantities(population, individual, 'noise')
    assert noise['raw_surprise'] > signature['raw_surprise']
    assert signature['individual_uplift'] > noise['individual_uplift'] > 0
    assert individual_quantities(population, population, 'noise')['individual_uplift'] == 0


def test_targets_and_duplicate_stimuli_do_not_multiply_independent_support():
    rows = [{'unit': 'a', 'task': 'x', 'difference': 1.0}] * 100
    rows += [{'unit': 'b', 'task': t, 'difference': 0.0} for t in ('x', 'y', 'z')]
    one = paired_interval(rows, draws=1000)
    crossed = paired_interval(rows, second_cluster='task', draws=1000)
    assert one['mean'] == crossed['mean'] == .5
    assert crossed['n_units'] == 2
    assert crossed['n_cells'] == 4
    assert crossed['second_groups'] == 3


def test_known_null_alternative_and_negative_bands():
    for difference, expected in [(0, 'PRACTICALLY SMALL'), (.1, 'SUPPORT CANDIDATE'), (-.1, 'COUNTEREVIDENCE')]:
        result = paired_interval([{'unit': i, 'difference': difference} for i in range(60)], draws=200)
        assert classify(result) == expected
    assert classify({'mean': .2, 'ci': [-.01, .4]}) == 'INCONCLUSIVE'
    assert classify({'mean': 0, 'ci': None}) == 'DESCRIPTIVE'
    assert classify({'mean': 0, 'ci': [float('nan'), 1]}) == 'IMPLEMENTATION INVALID'


def test_equifinal_distributions_do_not_invent_identifiability():
    same = dict(a=.5, b=.5)
    assert individual_quantities(same, same, 'a')['individual_uplift'] == 0
    with pytest.raises(ValueError):
        individual_quantities(same, dict(a=float('nan'), b=.5), 'a')


def test_holm_retains_family_of_three_when_only_one_candidate_runs():
    assert holm({'one': .02})['one']['reject'] is False
    values = holm({'a': .01, 'b': .03, 'c': .04})
    assert values['a']['reject'] is True
    assert values['b']['reject'] is values['c']['reject'] is False
    assert values['b']['adjusted_p'] == values['c']['adjusted_p'] == .06
    assert confirmation_size(.2)['n'] > 60
    with pytest.raises(ValueError):
        confirmation_size(.2, power=1)


def test_log_score_is_the_actual_normalized_forecast_including_rare_and_zero_events():
    from runners.stage9.scoring import log_score
    assert log_score({'rare':1e-30,'ordinary':1.},'rare')==math.log(1e-30)
    assert log_score({'impossible':0.,'ordinary':1.},'impossible')==-math.inf
    truth={'a':.8,'b':.2}
    own=sum(p*log_score(truth,k) for k,p in truth.items())
    for forecast in ({'a':.5,'b':.5},{'a':.95,'b':.05}):
        assert own>sum(p*log_score(forecast,k) for k,p in truth.items())


def test_both_zero_is_undefined_not_zero_uplift_and_all_scores_are_json_safe():
    import json
    from runners.stage9.common import canonical
    same = {'a':0.,'b':1.}
    result = individual_quantities(same,same,'a')
    assert result['individual_uplift'] is None
    assert result['uplift_status'] == 'undefined_both_zero'
    assert result['raw_surprise'] == {'extended_real':'positive_infinity'}
    assert json.loads(canonical(result)) == result


def test_zero_forecasts_cannot_be_dropped_to_promote_a_finite_subset():
    from runners.stage9.common import canonical
    from runners.stage9.scoring import paired_log_comparison
    good = {'a':.8,'b':.2}; prior = {'a':.5,'b':.5}; zero = {'a':0.,'b':1.}
    rows = [{'unit':str(i),'individual':good,'population':prior,'truth':'a'} for i in range(60)]
    assert classify(paired_log_comparison(rows,draws=100)) == 'SUPPORT CANDIDATE'
    for bad_left,bad_right,status in [(zero,prior,'negative_infinity'),(good,zero,'positive_infinity'),(zero,zero,'undefined')]:
        result = paired_log_comparison(rows+[{'unit':'bad','individual':bad_left,'population':bad_right,'truth':'a'}])
        assert result['n_targets'] == result['n_units'] == 61
        assert result['excluded_targets'] == 0 and result['extended_mean'] == status
        assert not result['promotion_eligible']
        assert classify(result) == 'DESCRIPTIVE'
        canonical(result)


def test_mixed_infinities_are_undefined_and_nan_and_support_mismatch_fail():
    from runners.stage9.scoring import paired_extended, score_json, paired_log_comparison
    result = paired_extended([{'unit':'a','difference':math.inf},{'unit':'b','difference':-math.inf}])
    assert result['extended_mean'] == 'undefined'
    for operation in (lambda: score_json(float('nan')),
                      lambda: paired_extended([{'unit':'a','difference':float('nan')}]),
                      lambda: paired_log_comparison([{'unit':'a','individual':{'a':1.},'population':{'a':.5,'b':.5},'truth':'a'}])):
        with pytest.raises(ValueError): operation()
