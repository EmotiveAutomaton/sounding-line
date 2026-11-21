"""Constructed checks for the curator's BG target and floor-time rules."""
import pytest

from runners.drive.cards.week6_la78_targets_v1 import SpeakerFloor, attribute, next_minute, rate_credits


def floor(*intervals):
    return SpeakerFloor([{"start":a, "end":b} for a,b in intervals])


def laugh(t, who="A"):
    return {"speaker":who, "start":t, "label":"vocal"}


def test_unique_self_boundary_and_nested_utterances():
    floors = {"A": floor((0,100)), "B": floor((10,20),(10,12)), "C": floor((25,30))}
    roles = dict(A="chair", B="speaker", C="designer")
    counts, pairs, events = attribute([laugh(22),laugh(22.001),laugh(25)],floors,roles)
    assert counts == {"single":2,"self":1} and not pairs
    assert [e[2] for e in events] == [("B",),(),("C",)]


def test_ambiguity_latest_fractional_and_conservation():
    floors = {"A":floor(), "B":floor((0,9)), "C":floor((4,10)), "D":floor((7,10))}
    roles = {"A":"chair","B":"design","C":"sales","D":"sales"}
    totals, pairs, events = attribute([laugh(10)],floors,roles)
    assert totals == {"multiple":1}
    assert pairs == {("design","sales"):1,("sales","sales"):1}
    credits = rate_credits(events,roles)
    assert not credits["single"]
    assert credits["latest"] == {("chair","sales"):1.}
    assert credits["fractional"][("chair","design")] == pytest.approx(1/3)
    assert sum(credits["fractional"].values()) == pytest.approx(1)


def test_only_unique_targets_have_paired_minutes_and_exact_join_window():
    floor_b = floor((20,50),(25,40),(59,61),(90,110),(95,100))
    floors = {"A":floor(),"B":floor_b}
    events = [("A",60,("B",),("B",)),("A",61,("B","C"),("B",)),("A",30,("B",),("B",))]
    rows, excluded = next_minute(events,{"B":[62]},floors,0,122)
    assert len(rows)==1 and excluded=={"incomplete paired minutes":1}
    assert rows[0]["joined"]
    assert rows[0]["before"]==pytest.approx(31/60)
    assert rows[0]["after"]==pytest.approx(21/60)
    assert not next_minute(events,{"B":[62.0001]},floors,0,122)[0][0]["joined"]


def test_invalid_or_missing_times_and_roster_fail_closed():
    with pytest.raises(ValueError): floor((0,float("inf")))
    with pytest.raises(ValueError): floor((5,4))
    with pytest.raises(ValueError): attribute([laugh(12)],{},{"A":"chair"})
    with pytest.raises(ValueError): attribute([laugh(float("nan"))],{"A":floor()},{"A":"chair"})
