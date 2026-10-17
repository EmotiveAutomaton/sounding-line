from pathlib import Path
import numpy as np
import pytest

from runners.drive.cards import menus_v4 as pilot
from runners.drive.cards import menus_v4_full as full
from runners.drive.cards import menus_v4_stats as stats
from runners.drive.cards.menus_io import read, sha256, write


def protocol_fixture(tmp_path, monkeypatch):
    """Cheap deterministic reader double: tests orchestration, not calibration."""
    sessions = []; keys = []
    for writer in "abc":
        for number in range(5):
            name = f"{writer}{number}"; rows = []
            for decision in range(4):
                key = f"{name}-{decision}"; keys.append(key)
                rows.append(dict(key=key, writer=writer, session=name, handling="ignore", menu=["one", "two"],
                    open_at=number * 1000 + decision * 10, resolved_at=number * 1000 + decision * 10 + 1))
            sessions.append(dict(writer=writer, session=name, timestamp=number * 1000, end_at=number * 1000 + 100, rows=rows))
    keys.sort(); rng = np.random.default_rng(122); lexical = rng.normal(size=(len(keys) * 2, 16))
    mini = rng.normal(size=lexical.shape); basis, _ = np.linalg.qr(rng.normal(size=(16, 4)))
    geometry = dict(keys=keys, slices=np.asarray([(i*2, i*2+2) for i in range(len(keys))]),
        lexical=lexical, mini=mini, basis=basis, menu_lexical=lexical.reshape(-1, 2, 16).mean(1),
        menu_mini=mini.reshape(-1, 2, 16).mean(1), vocabulary_size=30, lexical_explained=[1.], mini_explained=[1.])
    monkeypatch.setattr(pilot, "make_geometry", lambda *args: geometry)
    monkeypatch.setattr(pilot, "read_world", lambda sessions, trace, *args: dict(rows=len(trace)))
    monkeypatch.setattr(pilot, "score_world", lambda saved, seed: dict(readers={name: dict(detected=False) for name in pilot.READERS}, scored_decisions=saved["rows"], writers=3))
    write(tmp_path / "sessions.json", sessions); write(tmp_path / "records.json", [])
    write(tmp_path / "predictions.json", [dict(key=key, probabilities={"B-pop": [.25]*4}) for key in keys])
    np.save(tmp_path / "vectors.npy", mini)
    inputs = {key: str(tmp_path / (key + (".npy" if key == "vectors" else ".json"))) for key in full.SOURCES}
    config = dict(seed=20261017, optimizer_maxiter=100)
    pilot.execute(tmp_path / "pilot", inputs, dict(config, mode="pilot"))
    write(tmp_path / "PLAN.json", dict(module="runners.drive.cards.menus_v4", config=dict(config, mode="pilot"), inputs=inputs,
        pins={str(Path(module.__file__).resolve()): sha256(module.__file__) for module in (pilot, stats)}))
    return dict(inputs, pilot_summary=str(tmp_path / "pilot/SUMMARY.json"), pilot_plan=str(tmp_path / "PLAN.json")), config


def test_complete_protocol_reuses_pilot_yields_and_resumes_without_refit(tmp_path, monkeypatch):
    inputs, config = protocol_fixture(tmp_path, monkeypatch); output = tmp_path / "full"; calls = []
    def reader(sessions, trace, *args):
        calls.append(True)
        if len(calls) == 5:
            write(output / "YIELD_REQUEST.json", {"reason": "synthetic protocol test"})
        return dict(rows=len(trace))
    monkeypatch.setattr(pilot, "read_world", reader)
    yielded = full.execute(output, inputs, config)
    assert yielded == dict(status="yielded", card="V4", completed_worlds=5)
    assert not (output / "SUMMARY.json").exists() and not (output / "WORLDS.json").exists()
    first = output / "worlds/taste_lexical-0.0-0/RESULT.json"; identity = sha256(first)
    (output / "YIELD_REQUEST.json").unlink()  # Only this test-owned request, not a production owner request.
    report = full.execute(output, inputs, config)
    assert len(calls) == 107  # 110 declared units, three copied exact pilot worlds.
    assert report["checkpoint_count"] == 110 and report["reused_pilot_worlds"] == 3
    assert len(read(output / "NULL_WORLDS.json")) == 20
    assert sha256(first) == identity
    assert read(output / "FIRST_TENTH.json")["projected_seconds"] > 0
    assert full.verify(output, inputs, config)["verified"]
    for plant in pilot.PLANTS:
        name = f"{plant}-0.4-0"
        assert read(output / "worlds" / name / "CHECKPOINT.json")["reused_pilot"]
        for filename in full.WORLD_FILES:
            assert sha256(output / "worlds" / name / filename) == sha256(tmp_path / "pilot/worlds" / name / filename)
    with first.open("ab") as stream:
        stream.write(b" ")
    with pytest.raises(ValueError, match="checkpoint changed"):
        full.verify(output, inputs, config)


def test_full_refuses_changed_pilot_model_configuration(tmp_path, monkeypatch):
    inputs, config = protocol_fixture(tmp_path, monkeypatch)
    with pytest.raises(ValueError, match="model configuration differs"):
        full.execute(tmp_path / "full", inputs, dict(config, seed=2))


def test_size_failure_stays_blind_despite_perfect_planted_recovery():
    worlds = []
    for plant in pilot.PLANTS:
        for delta in pilot.SIZES:
            for replicate in range(10 if delta in (0., .4) else 5):
                worlds.append(dict(cell=dict(plant=plant, delta=delta, replicate=replicate),
                    readers={name: dict(detected=delta > 0) for name in pilot.READERS}))
    nulls = [dict(readers={name: dict(detected=i < 3) for name in pilot.READERS}) for i in range(20)]
    report = pilot.summarize(worlds, nulls, "full")
    assert report["state"] == "blind"
    assert set(report["labels"].values()) == {"blind"}
    assert all(row["estimate"] == 1 for row in report["primary"])
    with pytest.raises(ValueError, match="all 20"):
        pilot.summarize(worlds, nulls[:19], "full")
