"""Constructed marker, person-denominator and layout checks for sealed SC1."""
import csv
import hashlib

import pyarrow as pa
import pyarrow.parquet as pq
import pytest

from runners.drive.sealed import week6_sc1_counts_v1 as sc


def test_people_conversations_and_overlapping_markers_are_distinct():
    turns = [(f"c{i // 2}", f"p{i}", "[laughter] UH, um, mm-hmm, haha; laugh") for i in range(12)]
    turns += [turns[0], ("c1", "p1", "museum laughs uhuru"), ("new", None, "uh")]
    coverage, rows = sc.text_cells("natural_turn", [turns[:2], turns[2:]])
    assert coverage == {"version":"natural_turn", "n":12, "conversations":6}
    assert len(rows) == 6
    assert all(x["n"] == 12 and x["conversations"] == 6 for x in rows)


def test_one_speaker_many_conversations_never_meets_the_people_floor():
    data = [(str(j), "one", "uh") for j in range(60)]
    coverage, rows = sc.text_cells("backbiter", [data])
    assert coverage["n"] == 1 and coverage["conversations"] == 60 and rows == []


def test_literal_mention_is_distinct_from_brackets_and_substrings():
    turns = [(str(i), str(i), "laugh laughter uhuru museum mm hmm") for i in range(11)]
    _, rows = sc.text_cells("audiophile", [turns])
    assert [x["marker"] for x in rows] == ["laugh"]


def test_survey_denominators_count_distinct_respondents_with_the_item():
    people = [f"p{i}" for i in range(12)] + ["p0", None]
    table = pa.table({"user_id":people, "full":[5]*14, "boundary":[4]*11 + [None,4,4],
                      "small":[3]*10 + [None,None,3,3]})
    counts = {x["column"]:x["n"] for x in sc.survey_cells(table)}
    assert counts == {"user_id":12,"full":12,"boundary":11}


def fixture(root):
    people = [f"p{i}" for i in range(16)]
    root.mkdir()
    raw = {"audiophile":pa.table({"conversation_id":people,"speaker":people,"utterance":["uh"]*16}),
           "survey":pa.table({"user_id":people,"field":[1]*16})}
    pins = {}
    for k, data in raw.items():
        name = k + ".parquet"
        pq.write_table(data,root/name)
        payload = (root/name).read_bytes()
        pins[k] = name, len(payload), hashlib.sha256(payload).hexdigest()
    return pins


def test_reviewed_single_pass_writes_expected_gated_files(tmp_path):
    source = tmp_path / "input"
    pins = fixture(source)
    out = tmp_path / "out"
    sc.run(source, out, pins)
    assert sorted(p.name for p in out.iterdir()) == ["markers.csv","source_status.csv","survey_columns.csv","transcript_coverage.csv"]
    with (out / "markers.csv").open() as f:
        assert list(csv.DictReader(f)) == [{"version":"audiophile","marker":"uh","n":"16","conversations":"16"}]
    assert "p0" not in "".join(p.read_text() for p in out.iterdir())


def test_changed_bytes_ambiguous_layout_and_small_exports_refuse(tmp_path):
    source = tmp_path / "input"
    pins = fixture(source)
    bad = dict(pins, survey=(*pins["survey"][:2], "0"*64))
    with pytest.raises(sc.Unavailable, match="23"):
        sc.source_layout(source, bad)
    fixture(source / "processed")
    with pytest.raises(sc.Unavailable, match="21"):
        sc.source_layout(source, pins)
    with pytest.raises(sc.Unavailable, match="26"):
        sc.write_tables(tmp_path / "out", {"test":[{"n":10}]})

def test_single_projection_and_writer_floor(tmp_path,monkeypatch):
    calls=[]
    def project(root,pins,batch_size):
        calls.append(batch_size)
        return {"support":[{"n":10,"field":1},{"n":11,"field":2}]}
    monkeypatch.setattr(sc,"project",project)
    sc.run(tmp_path,tmp_path/"out",{})
    assert calls==[16384]
    with (tmp_path/"out/support.csv").open() as stream:
        assert list(csv.DictReader(stream))==[{"n":"11","field":"2"}]


def test_missing_table_or_column_preserves_safe_sibling(tmp_path):
    src=tmp_path/"inputs"
    pins=fixture(src)
    (src/"survey.parquet").unlink()
    incomplete=pa.table({"speaker":[f"p{i}" for i in range(14)],"utterance":["uh"]*14})
    pq.write_table(incomplete,src/"third.parquet")
    data=(src/"third.parquet").read_bytes()
    pins["backbiter"]=("third.parquet",len(data),hashlib.sha256(data).hexdigest())
    tables=sc.project(src,pins,batch_size=7)
    assert "survey_columns" not in tables
    assert tables["source_status"]==[
        {"version":"audiophile","n":16,"required_fields":3,"present_fields":3},
        {"version":"backbiter","n":14,"required_fields":3,"present_fields":2}]
