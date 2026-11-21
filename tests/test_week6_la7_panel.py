import numpy as np
import pytest

from runners.drive.cards.week6_la7_role_panel_v1 import design, table
from runners.drive.cards.week6_la7_run_v1 import encode, estimate


def example():
    roles = {"a": "lead", "b": "design", "c": "sales"}
    meta = dict(scenario=True, corpus="AMI", speakers={s: {"role": r} for s, r in roles.items()})
    acts = [dict(speaker="b", start=0., end=10.), dict(speaker="c", start=5., end=10.)]
    laughs = [dict(speaker=s, start=a, end=b, label="vocal")
              for s, a, b in (("c", 1, 2), ("c", 2, 3), ("a", 2, 2.2), ("a", 5, 6), ("a", 20, 21))]
    return acts, laughs, meta


def test_original_clock_counts_touching_intervals_ties_and_self():
    exposure, counts, ties = design(*example())
    assert counts["single"]["lead", "design", 0, 0] == 1
    assert counts["fractional"]["lead", "design", 1, 0] == .5
    assert counts["latest"]["lead", "sales", 0, 0] == .5
    assert sum(counts["single"].values()) == 3
    assert sum(counts["fractional"].values()) == 4
    assert ties == 1
    assert sum(t for (a,b,_,_),t in exposure.items() if (a,b)==("lead","design")) == pytest.approx(10/60)


def test_meeting_multiplicities_preserve_explicitly_repeated_meetings():
    exp, counts, _ = design(*example())
    original = [(exp, counts)]
    cells, matrix = encode(original)
    repeated = table(original * 2)
    assert estimate(cells, matrix, np.array([2])) == repeated
    with pytest.raises(ValueError):
        estimate(cells, matrix, [-1])
