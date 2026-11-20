"""Constructed daily trait checks. No investigator or participant tables are opened."""
from pathlib import Path
import sys

import numpy as np
from scipy.special import expit

ROOT = Path(__file__).resolve().parents[1]
for directory in (ROOT / "runners/drive/sealed/week6-sm-science", ROOT / "runners/drive/cards",
                  ROOT / ".agent-state/drive-20261115/full-week-extension/mi"):
    sys.path.insert(0, str(directory))
import nt1_daily as daily


def make_days(n=420, seed=871):
    rng = np.random.default_rng(seed)
    raw = {"survey": [], "diary": []}
    spec = daily.contract.fields("M2")
    for person in range(1, n + 1):
        z = rng.uniform(-1, 1)
        trait = 2.5 + z
        raw["survey"].append({"M2ID": person, "B1SNEURO": trait})
        event = rng.binomial(1, rng.uniform(.20, .72), 8)
        for day in range(1, 9):
            now, prev = event[day-1], event[max(0, day-2)]
            yes = rng.random() < expit(-.9 + .9*now + .55*prev + .55*z + .6*z*now + .25*z*prev)
            row = {"M2ID": person, "B2DDAY": day, "B2DWEEKD": (day-1) % 7 + 1}
            row.update({item["occurrence"]: 2 for item in spec["stressors"]})
            row["B2DF1"] = 1 if now else 2
            row.update({column: int(yes) for column in spec["negative"]})
            raw["diary"].append(row)
    return raw


def test_exposure_support_precedes_outcome_and_cannot_bridge_missing_days():
    data = make_days(4)
    spec = daily.contract.fields("M2")
    pred = {"survey": data["survey"], "diary": [
        {k: v for k, v in row.items() if k not in spec["negative"]}
        for row in data["diary"] if row["B2DDAY"] != 3]}
    rows, people, hits = daily.support(pred)
    assert rows == daily.support(pred, True)[0]
    assert {row[1] for row in rows} == {2, 5, 6, 7, 8}
    assert hits == sum(row[3] == 1 for row in rows)
    assert people == {row[0] for row in rows if row[3]}
    pred["diary"][2]["B2DWEEKD"] = 9
    assert len(daily.support(pred)[0]) == len(rows) - 1


def test_floor_and_unknown_are_distinct_in_both_decoders():
    data = make_days(3)
    pairs = daily.support(data)[0]
    fields = daily.contract.fields("M2")["negative"]
    target = data["diary"][1]
    for key in fields:
        target[key] = 0
    panel = daily.panel(data, pairs)
    assert panel["outcome"][0] == 0
    target[fields[0]] = 8
    assert len(daily.panel(data, pairs)["outcome"]) == len(panel["outcome"]) - 1
    target[fields[1]] = 3
    for replay in (False, True):
        result = daily.panel(data, pairs, replay)
        assert len(result["outcome"]) == len(panel["outcome"]) and result["outcome"][0] == 1


def test_registered_fit_and_draws_match_fresh_weighted_scoring():
    raw = make_days()
    rows, exposed, observations = daily.support(raw)
    assert observations >= 300 and len(exposed) >= 150
    actual = daily.panel(raw, rows)
    check = daily.panel(raw, daily.support(raw, True)[0], True)
    rng = np.random.default_rng(900)
    for weights in (np.ones(len(actual["ids"])), rng.multinomial(len(actual["ids"]), np.full(len(actual["ids"]), 1/len(actual["ids"])))):
        first, second = daily.score(actual, weights), daily.score(check, weights, True)
        assert first and second and first[0] > 0 and first[1] > 0 and first[2] > 0
        np.testing.assert_allclose(first, second, rtol=1e-8, atol=1e-10)
        assert first[-1] == first[4]/first[1] - first[3]/first[0]
    bad = dict(actual, outcome=np.zeros_like(actual["outcome"]))
    assert daily.score(bad, np.ones(len(actual["ids"]))) is None


def test_six_rulings_preserve_saturation_and_missing_intervals():
    assert daily.interpretation([.1,.2], .4, [0,.2]) == "slower_decay"
    assert daily.interpretation([.1,.2], -.4, [0,.2]) == "unread_lower_baseline"
    assert daily.interpretation([-.1,.2], .4, [.1,.2]) == "proportional_strength"
    assert daily.interpretation([-.1,.2], .4, [-.1,.2]) == "no_placement"
    assert daily.interpretation([-.2,-.1], .4, [.1,.2]) == "stronger_first"
    assert daily.interpretation([-.2,-.1], .4, [-.1,.2]) == "saturation"
    assert daily.interpretation(None, .4, [.1,.2]) == "could_not_say"
