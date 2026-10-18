"""Constructed spreadsheet cells exercise the actual isolated XLS parser."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import struct
import subprocess
import sys
import time
import zipfile

import numpy as np
import pytest

from runners.drive.cards import timing_jester_ratings as card


REPO = Path(__file__).resolve().parents[1]
WHEEL = REPO / ".agent-state/drive-20261017/builder2/jester-parser/xlrd-2.0.2-py2.py3-none-any.whl"


def save(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, sort_keys=True, allow_nan=False), encoding="utf8")


def biff(sheets):
    """Small numeric BIFF8 workbook with independent, declared cell coordinates."""
    def record(code, data):
        return struct.pack("<HH", code, len(data)) + data
    def bof(kind):
        return record(0x0809, struct.pack("<HHHHII", 0x0600, kind, 0x0DBB, 0x07CC, 0, 6))
    end = record(0x000A, b"")
    sheet_bytes = []
    for name, rows in sheets:
        records = [bof(0x0010), record(0x0200, struct.pack("<IIHHH", 0, len(rows), 0, 151, 0))]
        for i, row in enumerate(rows):
            for j, value in enumerate(row):
                records.append(record(0x0203, struct.pack("<HHHd", i, j, 0, float(value))))
        sheet_bytes.append(b"".join(records) + end)
    header = bof(0x0005) + record(0x0042, struct.pack("<H", 1200))
    # XF0 is a general numeric format, avoiding any inferred date conversion.
    header += record(0x00E0, b"\0" * 20)
    total_header = len(header) + sum(4 + 8 + len(name) for name, _ in sheets) + len(end)
    offset = total_header
    for (name, _), raw in zip(sheets, sheet_bytes):
        header += record(0x0085, struct.pack("<IBBBB", offset, 0, 0, len(name), 0) + name.encode("ascii"))
        offset += len(raw)
    return header + end + b"".join(sheet_bytes)


def fixture_rows():
    # Both signed endpoints, exact zero, duplicate independent raters, and one
    # wholly unrated rater. All other columns preserve exact missingness.
    rows = np.full((5, 151), 99., dtype=float)
    rows[:, 0] = 0
    rows[0, 1:5] = [-10., 0., 10., 3.125]
    rows[0, 0] = 4
    rows[1] = rows[0]
    rows[2, 150] = -0.125
    rows[2, 0] = 1
    rows[3, 1:3] = [-9.75, 8.5]
    rows[3, 0] = 2
    return rows.tolist()


def make_fixture(root, *, long=False):
    import openpyxl
    root = Path(root)
    root.mkdir(parents=True, exist_ok=True)
    rows = fixture_rows()
    first = [rows[0], rows[1], rows[4]]
    if long:
        first = first * 350
    sheets = [("first", first), ("second", rows[2:4])]
    raw = biff(sheets)
    archive = root / "ratings.zip"
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as z:
        z.writestr("constructed.xls", raw)
    texts = [dict(joke_id=i, text=f"Constructed joke {i}. Literal ending.") for i in range(1, 151)]
    texts_json = root / "texts.json"
    save(texts_json, texts)
    book = openpyxl.Workbook()
    sheet = book.active
    sheet.title = "jokes"
    for row in texts:
        sheet.append([row["text"]])
    text_workbook = root / "texts.xlsx"
    book.save(text_workbook)
    text_archive = root / "texts.zip"
    with zipfile.ZipFile(text_archive, "w") as z:
        z.writestr("texts.xlsx", text_workbook.read_bytes())
    source_page = root / "source.html"
    source_page.write_text("Constructed numeric-rating fixture. Not a source population.", encoding="utf8")
    inputs = dict(ratings_archive=str(archive), source_page=str(source_page), parser_wheel=str(WHEEL),
                  texts_archive=str(text_archive), jester_texts=str(texts_json), source_manifest=str(root / "MANIFEST.json"))
    manifest = dict(schema=1, source_kind="constructed_fixture", ratings_member="constructed.xls",
        workbook_sha256=hashlib.sha256(raw).hexdigest(), advertised_raters=sum(len(r) for _, r in sheets),
        sheets=[dict(name=name, rows=len(r), columns=151) for name, r in sheets],
        texts_member="texts.xlsx", texts_sheet="jokes", texts_workbook_sha256=card.filehash(text_workbook),
        input_sha256={k: card.filehash(v) for k, v in inputs.items() if k != "source_manifest"})
    save(inputs["source_manifest"], manifest)
    return inputs, dict(card.CONFIG), np.array([r[1:] for _, rr in sheets for r in rr], dtype=float)


def test_signed_zero_missing_and_duplicate_raters_are_preserved():
    rows = fixture_rows()
    a = card.validate_rows(rows, np.full((5, 151), 2))
    assert a[0, :4].tolist() == [-10., 0., 10., 3.125]
    assert np.array_equal(a[0], a[1], equal_nan=True)
    assert np.isnan(a[4]).all()
    assert np.isfinite(a).sum(0)[[0, 1, 2, 3, 149]].tolist() == [3, 3, 2, 2, 1]


def test_invalid_values_counts_and_cell_types_refuse():
    rows = np.array(fixture_rows())
    types = np.full(rows.shape, 2)
    for value in [-11., 11., 98., np.inf, np.nan]:
        bad = rows.copy()
        bad[0, 1] = value
        with pytest.raises(ValueError):
            card.validate_rows(bad, types)
    bad = rows.copy()
    bad[0, 0] = 3
    with pytest.raises(ValueError, match="first-column count"):
        card.validate_rows(bad, types)
    for ctype in [0, 1, 3, 4, 5, 6]:
        badtypes = types.copy()
        badtypes[0, 4] = ctype
        with pytest.raises(ValueError, match="numeric cells"):
            card.validate_rows(rows, badtypes)


def test_serialized_multisheet_and_fresh_process(tmp_path):
    inputs, config, expected = make_fixture(tmp_path / "inputs")
    output = tmp_path / "output"
    start = time.perf_counter()
    primary = card.execute(output, inputs, config)
    assert primary["raters"] == 5 and primary["zero_rating_raters"] == 1
    assert primary["jokes_with_ratings"] == 5 and primary["scientific_admission"] is False
    assert primary["joke_observed_rating_counts"] == [3, 3, 2, 2] + [0] * 145 + [1]
    index = card.read(output / "RATINGS_INDEX.json")
    actual = np.concatenate([np.load(output / x["file"], allow_pickle=False) for x in index["chunks"]])
    expected[expected == 99] = np.nan
    assert np.array_equal(actual, expected, equal_nan=True)
    call = tmp_path / "call.json"
    save(call, dict(output=str(output), inputs=inputs, config=config))
    code = "import json,sys;from pathlib import Path;from runners.drive.cards import timing_jester_ratings as c;v=json.load(open(sys.argv[1],encoding='utf8'));r=c.verify(Path(v['output']),v['inputs'],v['config']);assert r['verified'];print(r['source_raters_reparsed'])"
    child = subprocess.run([sys.executable, "-c", code, str(call)], cwd=REPO, capture_output=True, text=True,
        timeout=60, creationflags=subprocess.BELOW_NORMAL_PRIORITY_CLASS if os.name == "nt" else 0)
    assert child.returncode == 0, child.stderr
    assert child.stdout.strip() == "5"
    save(tmp_path / "SMOKE.json", dict(seconds=time.perf_counter() - start,
        bytes=sum(p.stat().st_size for p in output.rglob("*") if p.is_file()), fresh_process_exit=child.returncode))


def test_cooperative_yield_resume_reuses_exact_chunks(tmp_path):
    inputs, config, _ = make_fixture(tmp_path / "inputs", long=True)
    output = tmp_path / "output"
    save(output / "YIELD_REQUEST.json", dict(reason="owner test checkpoint"))
    paused = card.execute(output, inputs, config)
    assert paused["status"] == "yielded" and paused["complete_raters"] == 1024
    chunk = output / "chunks/0000.npy"
    before = (card.filehash(chunk), chunk.stat().st_mtime_ns)
    (output / "YIELD_REQUEST.json").unlink()
    result = card.execute(output, inputs, config)
    assert result["raters"] == 1052
    assert (card.filehash(chunk), chunk.stat().st_mtime_ns) == before
    assert card.verify(output, inputs, config)["verified"]
    tenth = card.read(output / "FIRST_TENTH.json")
    assert tenth["projected_cpu_seconds"] >= 2 * tenth["active_seconds"]


def test_changed_input_and_exact_configuration_refuse(tmp_path):
    inputs, config, _ = make_fixture(tmp_path / "inputs")
    with pytest.raises(ValueError, match="exact Jester intake configuration"):
        card.execute(tmp_path / "bad", inputs, dict(config, extra=True))
    Path(inputs["source_page"]).write_text("changed", encoding="utf8")
    with pytest.raises(ValueError, match="input identity"):
        card.execute(tmp_path / "output", inputs, config)


def test_source_validation_time_is_charged_before_first_checkpoint(tmp_path, monkeypatch):
    inputs, config, _ = make_fixture(tmp_path / "inputs")
    clock = {"seconds": 0.}
    original_validate = card.validate

    def timed_validate(*args):
        result = original_validate(*args)
        clock["seconds"] += 7.
        return result

    monkeypatch.setattr(card.time, "monotonic", lambda: clock["seconds"])
    monkeypatch.setattr(card, "validate", timed_validate)
    output = tmp_path / "output"
    card.execute(output, inputs, config)
    assert card.read(output / "PROGRESS.json")["active_seconds"] == 7.
    tenth = card.read(output / "FIRST_TENTH.json")
    assert tenth["active_seconds"] == 7.
    assert tenth["projected_cpu_seconds"] == 2 * 7. * 5 / 3


def test_forged_saved_ratings_refused_even_with_rebound_hashes(tmp_path):
    inputs, config, _ = make_fixture(tmp_path / "inputs")
    output = tmp_path / "output"
    card.execute(output, inputs, config)
    dest = output / "chunks/0000.npy"
    array = np.load(dest, allow_pickle=False)
    array[0, 0] = 7.
    np.save(dest, array, allow_pickle=False)
    receipt = card.read(dest.with_suffix(".json"))
    receipt["sha256"] = card.filehash(dest)
    save(dest.with_suffix(".json"), receipt)
    binding = card.read(output / "TIMING_BINDINGS.json")
    for name in ["chunks/0000.npy", "chunks/0000.json"]:
        binding["outputs"][name] = card.filehash(output / name)
    save(output / "TIMING_BINDINGS.json", binding)
    with pytest.raises(ValueError, match="fresh source"):
        card.verify(output, inputs, config)


def test_official_source_cannot_be_replaced_with_fixture_or_dataset3(tmp_path):
    inputs, config, _ = make_fixture(tmp_path / "inputs")
    manifest = card.read(inputs["source_manifest"])
    manifest["source_kind"] = "official_dataset2plus"
    save(inputs["source_manifest"], manifest)
    with pytest.raises(ValueError, match="official Dataset2"):
        card.validate(inputs, config)


def test_text_identity_and_unlisted_sheet_refuse(tmp_path):
    inputs, config, _ = make_fixture(tmp_path / "inputs")
    m = card.read(inputs["source_manifest"])
    texts = card.read(inputs["jester_texts"])
    texts[0]["text"] = texts[0]["text"].lower()
    save(inputs["jester_texts"], texts)
    m["input_sha256"]["jester_texts"] = card.filehash(inputs["jester_texts"])
    save(inputs["source_manifest"], m)
    with pytest.raises(ValueError, match="text/ID differs"):
        card.execute(tmp_path / "output", inputs, config)
    m["sheets"] = m["sheets"][:1]
    with pytest.raises(ValueError, match="worksheets differ"):
        card.open_source(inputs, m)


def test_incorrect_dimensions_and_unsealed_chunk_refuse(tmp_path):
    inputs, config, _ = make_fixture(tmp_path / "inputs")
    m = card.read(inputs["source_manifest"])
    m["sheets"][0]["rows"] -= 1
    save(inputs["source_manifest"], m)
    with pytest.raises(ValueError, match="dimensions differ"):
        card.execute(tmp_path / "bad_dimensions", inputs, config)
    m["sheets"][0]["rows"] += 1
    save(inputs["source_manifest"], m)
    output = tmp_path / "output"
    (output / "chunks").mkdir(parents=True)
    (output / "chunks/0000.npy").write_bytes(b"unsealed")
    with pytest.raises(ValueError, match="unsealed"):
        card.execute(output, inputs, config)


def test_advertised_count_discrepancy_and_zero_columns_remain_explicit():
    manifest = dict(source_kind="official_dataset2plus", advertised_raters=66336)
    counts = np.zeros(150, dtype=int)
    counts[[4, 149]] = [7, 9]
    result = card.statistics(manifest, dict(jokes=150), 50692, counts, 0, "")
    assert result["advertised_count_matches"] is False
    assert result["raters"] == 50692 and result["advertised_raters"] == 66336
    assert result["jokes_with_ratings"] == 2 and len(result["unrated_joke_ids"]) == 148
    assert result["scientific_admission"] is False
