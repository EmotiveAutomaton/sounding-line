import pytest
from runners.drive.cards import week6_la9_classes_v1 as classes


MAPS = {"AMI": {"ami_da_4":"information_exchange"},
        "ICSI":{"br^rt":"statement", "fg^tc|s^cs":"statement", "s.x":"disruption", "z":None}}


def test_dictionary_applies_to_the_entire_tag_and_its_own_corpus():
    assert classes.pooled_class("ICSI", "br^rt", MAPS) == "ICSI/statement"
    assert classes.pooled_class("ICSI", "fg^tc|s^cs", MAPS) == "ICSI/statement"
    assert classes.pooled_class("ICSI", "s.x", MAPS) == "ICSI/disruption"
    assert classes.pooled_class("ICSI", "s.unknown", MAPS) is None
    assert classes.pooled_class("ICSI", "z", MAPS) is None
    assert classes.pooled_class("AMI", "id(ami_da_4)", MAPS) == "AMI/information_exchange"
    assert classes.pooled_class("ICSI", "id(ami_da_4)", MAPS) is None


def test_control_reuse_cannot_push_49_utterances_over_the_floor():
    rows = [dict(meeting="m", id=str(i), act_type="br^rt") for i in range(49)]
    changed, support, _ = classes.relabel(rows+[rows[0]], {"m":"ICSI"}, MAPS)
    assert len(changed)==50 and support["ICSI/statement"]=={"distinct_utterances":49, "eligible":False}
    _, support, _ = classes.relabel(rows+[dict(rows[0],id="new")], {"m":"ICSI"}, MAPS)
    assert support["ICSI/statement"]=={"distinct_utterances":50, "eligible":True}


def test_unmapped_annotations_preserve_pairs_and_keep_their_distinct_levels():
    rows = [dict(meeting="m", id=i, act_type=tag) for i,tag in enumerate(("z","missing"))]
    changed, _, unavailable = classes.relabel(rows, {"m":"ICSI"}, MAPS)
    assert len(changed)==2 and unavailable==2 and changed[0]["act_type"]!=changed[1]["act_type"]
    with pytest.raises(ValueError,match="Inconsistent"):
        classes.relabel([rows[0],dict(rows[0],act_type="s.x")], {"m":"ICSI"}, MAPS)
