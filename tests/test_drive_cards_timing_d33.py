import numpy as np
import pytest

from runners.drive.cards.timing_d33 import cache, cache_probability, analyze


def records_fixture():
    from runners.drive.cards.timing_d33 import make_rows
    rng = np.random.default_rng(192)
    records = []
    for writer in range(8):
        for session in range(5):
            words = []
            for i in range(24):
                words.append(dict(index=i, token=f"w{writer}" if i % 2 else "shared",
                                  context=["shared"] if i % 3 else [], is_word=True,
                                  population_probability=float(rng.uniform(.001, .08)),
                                  population_log_frequency=float(rng.normal()),
                                  pause_seconds=1., first_delta_characters=1,
                                  length=int(rng.integers(2, 12)), sentence_start=i % 5 == 0,
                                  after_punctuation=i % 3 == 0))
            records.append(dict(writer=str(writer), session=f"w{writer}s{session}",
                                timestamp=10 * session, end_at=10 * session + 1,
                                training_sequences=[["shared", f"w{writer}"] * (writer + 2)], words=words))
    rows, _, _ = make_rows(records, "per_character")
    lookup = {r["session"]: r for r in records}
    for row in rows:
        # A known positive effect is planted only in held-out pauses, after the
        # model history/tuning is fixed. Source-derived execution must recover it.
        value = .5 * row["personal_surprise"] + .02 * row["length"] + .1 * int(row["writer"])
        lookup[row["session"]]["words"][row["index"]]["pause_seconds"] = float(np.exp(value + rng.normal(0, .01)))
    return records


def serialized_inputs(tmp_path):
    from runners.drive.cards.timing_p6 import gzwrite
    from runners.drive.cards.timing_census import write, filehash
    p6, tc = tmp_path / "p6", tmp_path / "tc"
    index = []
    for record in records_fixture():
        path = p6 / "output" / (record["session"] + ".json.gz")
        gzwrite(path, record)
        index.append(dict(file=path.name, sha256=filehash(path)))
    write(p6 / "output/P6_INDEX.json", index)
    write(tc / "output/TC_PRIMARY.json", dict(timing_mode="per_character"))
    inputs = dict(p6_index=str(p6 / "output/P6_INDEX.json"), tc_primary=str(tc / "output/TC_PRIMARY.json"))
    for key, directory, name in (("p6", p6, "P6_INDEX.json"), ("tc", tc, "TC_PRIMARY.json")):
        write(directory / "COMPLETE.json", dict(status="COMPLETE", fresh_process_verified=True,
              outputs={"output/" + name: filehash(directory / "output" / name)}))
        inputs[key + "_completion"] = str(directory / "COMPLETE.json")
    return inputs, dict(bootstrap_draws=2000, seed=20261017, extension=False)


def test_cache_refuses_current_future_and_same_timestamp_completion():
    sessions = [dict(end_at=1, training_sequences=[["old", "word"]]),
                dict(end_at=2, training_sequences=[["current"]]),
                dict(end_at=3, training_sequences=[["future"]])]
    counts = cache(sessions, 2)
    assert counts[0] == {"old": 1, "word": 1}
    word = dict(token="word", context=["old"])
    assert cache_probability(word, counts, .01) > .01
    assert cache_probability(dict(token="future", context=[]), counts, .01) < .01


def test_personal_surprise_pipeline_recovers_planted_effect_with_quiet_donor():
    rng = np.random.default_rng(41)
    rows = []
    for writer in range(8):
        for i in range(50):
            personal, donor = rng.normal(size=2)
            rows.append(dict(writer=str(writer), personal_surprise=personal, donor_surprise=donor,
                             population_surprisal=float(rng.uniform(1, 5)), log_pause=writer + .7 * personal + rng.normal(0, .1),
                             length=int(rng.integers(2, 10)), log_frequency=float(rng.normal()),
                             sentence_start=i % 5 == 0, after_punctuation=i % 3 == 0))
    result = analyze(rows, dict(seed=20261017, bootstrap_draws=30, extension=False))
    assert .65 < result["effect"] < .75
    assert result["state"] == "positive"
    assert abs(result["controls"]["donor"]["effect"]) < .2
    assert abs(result["controls"]["within_writer_surprise_shuffle"]["effect"]) < .2


def test_calibration_and_earlier_rows_are_unchanged_by_future_text():
    import copy
    from runners.drive.cards.timing_d33 import make_rows
    records = records_fixture()
    rows, tuning, _ = make_rows(records, "per_character")
    changed = copy.deepcopy(records)
    for record in changed:
        if record["session"].endswith("s4"):
            record["training_sequences"] = [["future"] * 1000]
    other, other_tuning, _ = make_rows(changed, "per_character")
    assert tuning == other_tuning and rows == other
    assert all(item["alpha"] > 0 for item in tuning)


def test_no_writer_is_its_own_donor():
    from runners.drive.cards.timing_d33 import make_rows
    records = records_fixture()
    _, tuning, _ = make_rows(records, "per_character")
    assert all(row["writer"] != row["donor"] for row in tuning)
    rows, tuning, exclusions = make_rows(records[:5], "per_character")
    assert not rows and not tuning and exclusions[0]["reason"] == "no independent donor writer"


def test_missing_personal_support_is_invalid_not_null():
    from runners.drive.cards.timing_d33 import make_rows
    rows, _, _ = make_rows(records_fixture(), "per_character")
    for row in rows:
        row["personal_surprise"] = 0.
    result = analyze(rows, dict(seed=20261017, bootstrap_draws=20, extension=False))
    assert result["state"] == "invalid"


def test_actual_serialized_handler_resume_fresh_replay_and_immutable_reentry(tmp_path):
    import json
    import subprocess
    import sys
    from runners.drive.cards.timing_d33 import execute
    from runners.drive.cards.timing_census import write
    inputs, config = serialized_inputs(tmp_path)
    output = tmp_path / "output"
    write(output / "YIELD_REQUEST.json", dict(reason="synthetic saved boundary"))
    assert execute(output, inputs, config)["status"] == "yielded"
    assert (output / "D33_INTERMEDIATES.json.gz").exists()
    assert not (output / "D33_PRIMARY.json").exists()
    first = output / "primary/block-00000.json"
    retained = first.read_bytes()
    (output / "YIELD_REQUEST.json").unlink()
    result = execute(output, inputs, config)
    assert result["state"] == "positive" and .48 < result["effect"] < .52
    assert first.read_bytes() == retained
    write(tmp_path / "plan.json", dict(output=str(output), inputs=inputs, config=config))
    script = "import json,sys;from pathlib import Path;from runners.drive.cards.timing_d33 import verify;p=json.load(open(sys.argv[1]));print(json.dumps({'verified':verify(Path(p['output']),p['inputs'],p['config'])['verified']}))"
    checked = subprocess.run([sys.executable, "-B", "-c", script, str(tmp_path / "plan.json")], capture_output=True, text=True, check=True)
    assert json.loads(checked.stdout)["verified"]
    snapshots = {str(p.relative_to(output)): p.read_bytes() for p in output.rglob("*") if p.is_file()}
    assert execute(output, inputs, config) == result
    assert snapshots == {str(p.relative_to(output)): p.read_bytes() for p in output.rglob("*") if p.is_file()}


def test_saved_input_mutation_refuses_resume(tmp_path):
    from runners.drive.cards.timing_d33 import execute
    from runners.drive.cards.timing_census import read, write
    from pathlib import Path
    inputs, config = serialized_inputs(tmp_path)
    output = tmp_path / "output"
    write(output / "YIELD_REQUEST.json", {})
    assert execute(output, inputs, config)["status"] == "yielded"
    path = Path(inputs["p6_index"]).parent / read(inputs["p6_index"])[0]["file"]
    path.write_bytes(b"changed")
    with pytest.raises(ValueError, match="P6 source changed"):
        execute(output, inputs, config)
    assert not (output / "D33_PRIMARY.json").exists()


def test_dependency_must_bind_actual_input(tmp_path):
    from runners.drive.cards.timing_d33 import validate_inputs
    from pathlib import Path
    inputs, config = serialized_inputs(tmp_path)
    Path(inputs["tc_primary"]).write_text('{"timing_mode":"invalid"}')
    with pytest.raises(ValueError, match="completion binding changed"):
        validate_inputs(inputs, config)


def test_index_cannot_escape_its_artifact_root(tmp_path):
    import json
    from pathlib import Path
    from runners.drive.cards.timing_d33 import source_data
    from runners.drive.cards.timing_census import read, write
    inputs, config = serialized_inputs(tmp_path)
    index = read(inputs["p6_index"])
    index[0]["file"] = "../../outside.json.gz"
    Path(inputs["p6_index"]).write_text(json.dumps(index))
    with pytest.raises(ValueError):
        source_data(inputs, config)
