"""Constructed source-binding, checkpoint and replay checks for the shared diary entry."""
import csv
import json
from pathlib import Path

import pytest

from runners.drive.cards import week6_diary_rows_v1 as rows
from runners.drive.cards import week6_ld_draws_v1 as draws
from runners.drive.cards.batch_runtime import filehash


TABLE = Path(__file__).resolve().parents[1] / "docs/design/stage-15/week6/DIARY_ROWS_20261120.json"


def evidence(path):
    return {"path": str(path), "sha256": filehash(path)}


def write_json(path, value):
    path.write_text(json.dumps(value), encoding="utf8")
    return path


def constructed(tmp_path, monkeypatch):
    member = "0057"
    fields = ["id", "day", "created_esm", "ended_esm", "interaction", "communication",
              "type_interaction", *rows.source.ACTIVITY, *["occup_" + n for n in rows.source.feeling_names(member)]]
    source = tmp_path / "diary.tsv"
    with source.open("w", encoding="utf8", newline="") as stream:
        writer = csv.DictWriter(stream, fields, delimiter="\t")
        writer.writeheader()
        for who in range(22):
            for j in range(12):
                data = dict.fromkeys(fields, "3")
                stamp = f"2020-02-01T{8+j:02d}:00:00Z"
                data.update(id=str(who), day="1", created_esm=stamp, ended_esm=stamp,
                            interaction="2" if j % 2 == 0 else "1", communication="2", type_interaction="1")
                writer.writerow(data)
    pin = dict(sha256=filehash(source), bytes=source.stat().st_size)
    book = write_json(tmp_path/"book.json", {"dataset_id": member, "features": [{"name": f} for f in fields]})
    monkeypatch.setitem(rows.common.CODEBOOK_HASHES, member, filehash(book))
    schema = write_json(tmp_path/"layout.json", {"files": [{**pin, "columns": [{"name": f} for f in fields]}]})
    panel = dict(card="LD3", member=member, source_pin=pin, missing_tokens=["", "NA"],
                 draws=draws.DRAWS, source_seed=draws.SOURCE_SEEDS[member])
    review = {"schema": "LD_SOURCE_ADMISSION_V1", "owner_reviewed": True, "rights": "constructed",
              "source_path": str(source), "authority": evidence(TABLE), "panel_config": panel,
              "rows_table": evidence(TABLE), "codebook": evidence(book), "source_layout": evidence(schema)}
    receipt = write_json(tmp_path/"review.json", review)
    return review, {"source_path": str(source), "source_admission_path": str(receipt),
                    "source_admission_sha256": filehash(receipt)}, panel


def test_execute_checkpoint_and_independent_replay_do_not_repeat_descriptions(tmp_path, monkeypatch):
    monkeypatch.setattr(draws, "DRAWS", 2)
    review, inputs, panel = constructed(tmp_path, monkeypatch)
    config = dict(panel_config=panel, max_new_draws=1, max_wall_seconds=60)
    output = tmp_path/"output"
    assert rows.execute(output, inputs, config)["status"] == "yielded"
    support = json.loads((output/"ROW_SUPPORT.json").read_text())["values"]
    assert support["LD3.a"] == {"eligible_people": 22, "eligible_prompts": 132}
    assert support["LD3.b"] == support["LD3.a"]
    def repeated(*args, **kwargs):
        pytest.fail("Descriptive work ran again")
    monkeypatch.setattr(rows, "describe", repeated)
    monkeypatch.setattr(rows, "support_before_outcomes", repeated)
    assert rows.execute(output, inputs, config)["status"] == "computed"
    assert rows.verify(output, inputs, config)["status"] == "yielded"
    assert rows.verify(output, inputs, config)["verified"]
    assert json.loads((output/"verify"/"SCHEMA.json").read_text())["source_sha256"] == panel["source_pin"]["sha256"]
    (output/"NEXT_PROMPT_DESCRIPTION.json").write_text("{}", encoding="utf8")
    with pytest.raises((KeyError, ValueError)):
        rows.verify(output, inputs, config)


def test_missing_codebook_item_refuses_before_source_read(tmp_path, monkeypatch):
    review, _, panel = constructed(tmp_path, monkeypatch)
    book = Path(review["codebook"]["path"])
    data = json.loads(book.read_text())
    data["features"] = [f for f in data["features"] if f["name"] != "intellectual"]
    write_json(book, data)
    review["codebook"] = evidence(book)
    monkeypatch.setitem(rows.common.CODEBOOK_HASHES, "0057", filehash(book))
    with pytest.raises(ValueError, match="intellectual"):
        rows.bind_rows("LD3", "0057", review, panel["source_pin"])


def test_register_keeps_rank_and_felt_superiority_separate_from_conduct():
    registry = json.loads(TABLE.read_text())
    large = {r["id"]: r for r in registry["rows"] if r["operator"] == "LD2" and r["member"] == "0057"}
    assert {k: r["bar"] for k, r in large.items()} == {"LD2.a": .4, "LD2.b": .05, "LD2.c": .05}
    small = {r["id"] for r in registry["rows"] if r["operator"] == "LD2" and r["member"] == "0056" and r["registered"]}
    assert small == {"LD2.b"}
