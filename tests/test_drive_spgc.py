import copy

import pytest

from runners.drive import spgc


def fixture():
    frame = {f"author{i}": [{"id": f"PG{i * 4 + j}", "title": f"book{j}", "birth": 1800,
                             "subjects": [f"subject{j}"]} for j in range(4)] for i in range(5)}
    audit = {author: {"complete": True, "evidence": "bibliography", "english_language_novelist": True,
                     "books": {book["id"]: {"novel": True, "evidence": "title page and complete text",
                                             "work_or_protagonist_group": book["title"],
                                             "work_id": book["title"], "edition_id": book['id'],
                                             "part_number": 1, "part_count": 1} for book in books}}
             for author, books in frame.items()}
    return frame, audit


def test_seeded_draw_refuses_missing_earlier_review_and_collapses_series():
    frame, audit = fixture()
    first = spgc.author_order(frame)[0]
    for book in audit[first]["books"].values():
        book["work_or_protagonist_group"] = "one recurring protagonist"
    value = spgc.draw_cohort(frame, audit, count=3)
    assert first not in [r["author"] for r in value["cohort"]]
    assert len(value["cohort"]) == 3
    assert value == spgc.draw_cohort(dict(reversed(list(frame.items()))), audit, count=3)
    del audit[first]
    with pytest.raises(ValueError, match="missing complete"):
        spgc.draw_cohort(frame, audit, count=3)


def test_incomplete_book_review_is_not_three_books():
    frame, audit = fixture()
    first = spgc.author_order(frame)[0]
    changed = copy.deepcopy(audit)
    changed[first]["books"].pop(next(iter(changed[first]["books"])))
    with pytest.raises(ValueError, match="all candidate"):
        spgc.draw_cohort(frame, changed, count=3)


def test_multivolume_novel_is_complete_and_sampled_once():
    frame, audit = fixture()
    author = spgc.author_order(frame)[0]
    first, second = frame[author][:2]
    for i, book in enumerate((first, second), 1):
        audit[author]['books'][book['id']].update(work_or_protagonist_group='paired novel',
            work_id='paired novel', edition_id='edition A', part_number=i, part_count=2)
    result = spgc.draw_cohort(frame, audit, count=1)['cohort'][0]
    assert len(result['books']) == 3
    bundle = next(book for book in result['books'] if book['work_id']=='paired novel')
    assert [p['id'] for p in bundle['parts']] == [first['id'], second['id']]
    audit[author]['books'][second['id']]['part_number'] = 1
    with pytest.raises(ValueError, match='duplicated novel volume'):
        spgc.draw_cohort(frame, audit, count=1)


def test_missing_part_cannot_be_counted_as_complete_novel():
    frame, audit = fixture()
    author = spgc.author_order(frame)[0]
    book = frame[author][0]
    audit[author]['books'][book['id']]['part_count'] = 2
    with pytest.raises(ValueError, match='incomplete or duplicated'):
        spgc.draw_cohort(frame, audit, count=1)


def test_passage_boundaries_nonoverlap_determinism_and_immutable_bytes(tmp_path):
    body = " ".join("fear" if i % 350 == 2 else f"word{i}" for i in range(40000))
    result = spgc.passages(body, "PG12")
    assert len(result) == 100
    assert result == spgc.passages(body, "PG12")
    for i, row in enumerate(result):
        assert row["word_end"] - row["word_start"] == 300
        assert "fear" in row["text"]
        assert row["text"] == body[row["char_start"]:row["char_end"]]
        if i:
            assert result[i - 1]["word_end"] <= row["word_start"]
    assert spgc.passages("nothing threatening here", "PG1") == []
    path = tmp_path / "bytes"
    spgc.save_equal(path, b"original\n")
    spgc.save_equal(path, b"original\n")
    with pytest.raises(ValueError, match="immutable"):
        spgc.save_equal(path, b"changed\n")


def test_release_delimiters_and_unknown_host_refusal(tmp_path):
    source = "license\n*** START OF THE PROJECT GUTENBERG EBOOK TEST ***\nfear\n*** END OF THE PROJECT GUTENBERG EBOOK TEST ***\nlicense"
    assert spgc.book_body(source).strip() == "fear"
    with pytest.raises(ValueError, match="delimiters"):
        spgc.book_body("fear")
    with pytest.raises(ValueError, match="unapproved"):
        spgc.fetch("https://example.com/x", tmp_path / "x", 100)
    with pytest.raises(ValueError, match="identity"):
        spgc.metadata(b"untrusted")
