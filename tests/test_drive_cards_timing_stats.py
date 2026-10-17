import numpy as np

from runners.drive.cards.timing_stats import regression


def test_within_writer_adjustment_recovers_planted_effect_despite_writer_offsets():
    rng = np.random.default_rng(10)
    x, y, writers = [], [], []
    for w in range(8):
        for i in range(30):
            treatment = i % 2
            nuisance = rng.normal()
            x.append([treatment, nuisance])
            y.append(w * 30 + 2 * treatment - .8 * nuisance + rng.normal(0, .1))
            writers.append(str(w))
    checkpoints = []
    result = regression(x, y, writers, within=True, draws=100, on_tenth=checkpoints.append)
    assert 1.9 < result["effect"] < 2.1
    assert result["ci_low"] > 0
    assert result["state"] == "positive"
    assert result["bootstrap_se"] > 0
    assert result["wald_p_two_sided"] < .001
    assert checkpoints[0]["completed_draws"] == 10


def test_random_intercept_recovers_personal_effect_and_never_uses_one_writer_ci():
    rng = np.random.default_rng(12)
    x, y, writers = [], [], []
    for w in range(6):
        for i in range(20):
            surprise = rng.normal()
            x.append([surprise, 1])
            y.append(w * 2 + surprise * .5 + rng.normal(0, .1))
            writers.append(str(w))
    result = regression(x, y, writers, random_intercept=True, draws=30)
    assert .45 < result["effect"] < .55
    assert result["variance_ratio"] > 1
    assert regression(x[:20], y[:20], writers[:20], within=True)["state"] == "invalid"
