import pytest

from tools.week7_ami_intake import compare


def test_only_new_complete_meetings_advance():
    mapping = {"A/1": ("A", "x"), "B/1": ("B", "x"), "B/2": ("B", "y")}
    pin = {"bytes": 80, "sha256": "a" * 64}
    previous = dict(source="ami-close-talk", required=3, files={"A/1": pin}, complete={"A": ["A/1"]})
    rows = [dict(path="open/ami-close-talk/raw/" + k, assigned_in_annotation_metadata=True, **pin)
            for k in mapping]
    source = dict(slug="ami-close-talk", license="CC BY 4.0",
                  coverage={"required_channel_paths": list(mapping)}, local_files=rows[:2])
    source["class"] = "open-clean"
    assert compare(mapping, previous, source)[2] == []
    source["local_files"] = rows
    assert compare(mapping, previous, source)[2] == ["B"]
    source["local_files"] = [*rows, rows[-1]]
    with pytest.raises(ValueError, match="invalid assigned"):
        compare(mapping, previous, source)
    source["local_files"] = rows[1:]
    with pytest.raises(ValueError, match="missing or changed"):
        compare(mapping, previous, source)
    source["local_files"] = [dict(rows[0], sha256="b" * 64), *rows[1:]]
    with pytest.raises(ValueError, match="missing or changed"):
        compare(mapping, previous, source)
