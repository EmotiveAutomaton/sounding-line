import numpy as np
import pytest

from runners.drive.cards import week5_md as md


def test_native_fixture():
    assert md.fixture()["passed"]


def test_first_saved_is_not_necessarily_actual_first():
    data = np.zeros((30, 15)); data[:, 0] = np.arange(1, 31)
    data[:, 9] = np.nan
    data[[0, 3, 5, 8, 11, 13, 16, 18, 21, 24, 26, 29], 9] = 50
    subject = {"dataHdr": md.HEADER, "data": [data, data.copy()], "timesPlayed": [4, 2],
               "dayNumber": [3, 1], "timeOfDay": [.5, .2], "nPlays": 2}
    _, counter, _ = md.project_subject(subject)
    assert counter.tolist() == [2, 4]
    assert 1 not in counter


def test_missing_initial_rating_refuses():
    data = np.zeros((30, 15)); data[:, 0] = np.arange(1, 31); data[:, 9] = np.nan
    data[[1, 3, 5, 8, 11, 13, 16, 18, 21, 24, 26, 29], 9] = 50
    with pytest.raises(ValueError, match="rating support"):
        md.validate_play(data)


def test_sufficient_statistics_match_explicit_repeated_clusters():
    rng = np.random.default_rng(19)
    x = rng.normal(size=(7, 12, 5)); y = rng.normal(size=(7, 12))
    w = np.array([2, 0, 3, 1, 0, 0, 1])
    original = md.fit_stats(md.stats(x, y), [0, 2, 4], w)
    repeated = md.fit_stats(md.stats(np.repeat(x, w, axis=0), np.repeat(y, w, axis=0)), [0, 2, 4])
    assert np.allclose(original[0], repeated[0])
    assert np.allclose(original[1:], repeated[1:])


def test_projection_refuses_modified_mat_before_parse(tmp_path, monkeypatch):
    (tmp_path / "Rutledge_risk_and_happiness_task_2023.zip").write_bytes(b"zip")
    (tmp_path / "Rutledge_GBE_risk_data_TOD.mat").write_bytes(b"altered")
    monkeypatch.setattr(md, "sha", lambda p: md.ZIP_SHA if p.suffix == ".zip" else "wrong")
    monkeypatch.setattr(md, "loadmat", lambda *a, **k: pytest.fail("must refuse before parsing"))
    with pytest.raises(ValueError, match="member pin"):
        md.prepare(tmp_path, tmp_path / "out")
