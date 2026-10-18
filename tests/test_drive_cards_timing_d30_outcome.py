import json
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

import numpy as np
import pytest

from runners.drive.cards import timing_d30 as original
from runners.drive.cards import timing_d30_outcome as control
from runners.drive.cards.timing_census import write, filehash, read
from runners.drive.cards.timing_p6 import gzwrite
from runners.drive.cards.timing_checkpoint import regression
from tests.test_drive_cards_timing_d30 import known_rows


@pytest.mark.parametrize("mode", ["per_character", "per_word", "invalid"])
def test_design_exactly_matches_original_handler(mode):
    rows = known_rows()
    captured = {}
    def intercept(x, y, writers, **kwargs):
        captured.update(x=x, y=y, writers=writers, direction=kwargs["direction"])
        return dict(state="null")
    with patch.object(original, "regression", intercept):
        original.analyze(rows, control.ORIGINAL_CONFIG, mode, controls=False)
    actual, _ = control.design(rows, mode)
    assert actual == captured


def test_permutation_preserves_each_writer_multiset_and_is_not_identity():
    writers = ["b", "a", "b", "a"] * 30
    indices = control.permutation(writers, 20261017)
    assert indices == control.permutation(writers, 20261017)
    assert sorted(indices) == list(range(len(writers)))
    assert indices != list(range(len(writers)))
    assert all(writers[i] == writers[j] for i, j in enumerate(indices))


def synthetic_matrix():
    rng = np.random.default_rng(73)
    writers = np.repeat(np.arange(12).astype(str), 200).tolist()
    x = np.column_stack([np.tile(np.arange(200) % 2, 12), rng.normal(size=2400)]).tolist()
    y = (2 * np.asarray(x)[:, 0] + rng.normal(0, .1, 2400)).tolist()
    permutation = control.permutation(writers, 20261017)
    return dict(x=x, y=y, writers=writers, direction=1,
                shuffled_y=[y[i] for i in permutation], timing_mode="per_character")


def test_shuffle_removes_planted_alignment_and_positive_flag_can_fire():
    matrix = synthetic_matrix()
    baseline = regression(matrix["x"], matrix["y"], matrix["writers"], within=True, draws=200)
    assert baseline["state"] == "positive" and baseline["effect"] > 1.9
    result = control.compute(matrix, dict(control.CONFIG, bootstrap_draws=200))
    assert abs(result["effect"]) < .1 and not result["daily_screen_failure_flag"]
    matrix["shuffled_y"] = matrix["y"]
    assert control.compute(matrix, dict(control.CONFIG, bootstrap_draws=200))["daily_screen_failure_flag"]
    matrix["shuffled_y"] = [-y for y in matrix["y"]]
    reversed_result = control.compute(matrix, dict(control.CONFIG, bootstrap_draws=200))
    assert reversed_result["state"] == "negative" and not reversed_result["daily_screen_failure_flag"]


def fixture_source(tmp_path):
    root = tmp_path / "original"
    rows = known_rows()
    baseline, markers = original.analyze(rows, control.ORIGINAL_CONFIG, "per_character", controls=False)
    write(root / "PLAN.json", dict(config=control.ORIGINAL_CONFIG, module="runners.drive.cards.timing_d30", pins={}))
    gzwrite(root / "output/D30_INTERMEDIATES.json.gz", dict(rows=rows, config=control.ORIGINAL_CONFIG, timing_mode="per_character"))
    write(root / "output/D30_PRIMARY.json", baseline)
    write(root / "output/D30_MARKERS.json", markers)
    write(root / "COMPLETE.json", dict(status="COMPLETE", fresh_process_verified=True,
        outputs={p.relative_to(root).as_posix(): filehash(p) for p in root.rglob("*") if p.is_file()}))
    return dict(source_completion=str(root / "COMPLETE.json"))


def test_serialized_handler_resume_fresh_replay_and_immutable_reentry(tmp_path):
    inputs = fixture_source(tmp_path)
    output = tmp_path / "output"
    write(output / "YIELD_REQUEST.json", dict(reason="fixture"))
    assert control.execute(output, inputs, control.CONFIG)["status"] == "yielded"
    assert not (output / "PRIMARY.json").exists()
    block = output / "outcome_shuffle/block-00000.json"
    prior = block.read_bytes()
    (output / "YIELD_REQUEST.json").unlink()
    result = control.execute(output, inputs, control.CONFIG)
    assert block.read_bytes() == prior
    plan = tmp_path / "control.json"
    write(plan, dict(output=str(output), inputs=inputs, config=control.CONFIG))
    code = "import json,sys;from pathlib import Path;from runners.drive.cards.timing_d30_outcome import verify;p=json.load(open(sys.argv[1]));assert verify(Path(p['output']),p['inputs'],p['config'])['verified']"
    subprocess.run([sys.executable, "-X", "utf8", "-B", "-c", code, str(plan)], check=True)
    before = {p.relative_to(output).as_posix(): p.read_bytes() for p in output.rglob("*") if p.is_file()}
    assert control.execute(output, inputs, control.CONFIG) == result
    assert before == {p.relative_to(output).as_posix(): p.read_bytes() for p in output.rglob("*") if p.is_file()}
    saved = read(output / "PRIMARY.json")
    saved["effect"] += .1
    (output / "PRIMARY.json").write_text(json.dumps(saved), encoding="utf-8")
    with pytest.raises(ValueError, match="intermediate/output changed"):
        control.verify(output, inputs, control.CONFIG)


def test_incomplete_changed_source_and_configuration_refuse(tmp_path):
    inputs = fixture_source(tmp_path)
    complete_path = Path(inputs["source_completion"])
    complete = read(complete_path)
    complete_path.write_text(json.dumps(dict(complete, fresh_process_verified=False)), encoding="utf-8")
    with pytest.raises(ValueError, match="not verified complete"):
        control.source(inputs, control.CONFIG)
    complete_path.write_text(json.dumps(complete), encoding="utf-8")
    with pytest.raises(ValueError, match="configuration differs"):
        control.source(inputs, dict(control.CONFIG, permutation_seed=5))
    primary = complete_path.parent / "output/D30_PRIMARY.json"
    primary.write_bytes(primary.read_bytes() + b" ")
    with pytest.raises(ValueError, match="completion binding changed"):
        control.source(inputs, control.CONFIG)


def test_changed_saved_permutation_refuses_even_with_updated_output_hash(tmp_path):
    inputs = fixture_source(tmp_path)
    output = tmp_path / "output"
    control.execute(output, inputs, control.CONFIG)
    from runners.drive.cards.timing_p6 import gzread
    saved = gzread(output / "INTERMEDIATES.json.gz")
    saved["permutation"] = saved["permutation"][::-1]
    import gzip
    (output / "INTERMEDIATES.json.gz").write_bytes(gzip.compress(json.dumps(saved).encode()))
    bindings = read(output / "TIMING_BINDINGS.json")
    bindings["outputs"]["INTERMEDIATES.json.gz"] = filehash(output / "INTERMEDIATES.json.gz")
    (output / "TIMING_BINDINGS.json").write_text(json.dumps(bindings), encoding="utf-8")
    with pytest.raises(ValueError, match="design or permutation changed"):
        control.verify(output, inputs, control.CONFIG)
