"""Same-day diary sequencing on constructed UTC source rows."""
from runners.drive.cards.week6_ld3_follow_v1 import describe


def row(hour, context, *, day=5, boredom="3", mode="2"):
    clock = f"2020-01-{day:02d}T{hour:02d}:00:00Z"
    return dict(id="subject", created_esm=clock, ended_esm=clock,
                interaction=context, occup_bored=boredom, communication=mode)


def test_original_order_and_overnight_gaps_do_not_create_successors():
    result = describe([row(18, "2", boredom="6"), row(14, "1"), row(10, "2"),
                       row(8, "1", day=6)], ["", "NA"], lambda: None)
    assert result["by_boredom"]["3"] == {"anchors": 1, "next_interaction": 1}
    assert result["next_interaction_communication_codes"]["3"] == {"2": 1}
    assert result["by_boredom"]["6"] == {"anchors": 1, "last_answered_prompt_of_day": 1}
    assert len(result["by_boredom"]) == 6


def test_missing_next_context_cannot_be_bridged():
    result = describe([row(10, "2"), row(13, "NA"), row(18, "1")],
                      ["", "NA"], lambda: None)
    assert result["by_boredom"]["3"] == {"anchors": 1, "next_context_missing": 1}


def test_tied_times_are_not_broken_by_source_order():
    result = describe([row(10, "2"), row(12, "1"), row(12, "2")],
                      ["", "NA"], lambda: None)
    assert result["coverage"]["ambiguous_day_prompts"] == 3
    assert all(not counts for counts in result["by_boredom"].values())


def test_unknown_answer_time_cannot_bridge_a_recorded_prompt():
    unknown = row(12, "1")
    unknown["ended_esm"] = "NA"
    result = describe([row(10, "2"), unknown, row(15, "1")], ["", "NA"], lambda: None)
    assert result["coverage"]["without_answered_clock"] == 1
    assert all(not counts for counts in result["by_boredom"].values())
