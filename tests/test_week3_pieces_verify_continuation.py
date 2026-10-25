import json
from pathlib import Path
import shutil
import subprocess
import sys

import pytest

from runners.drive.cards import week3_pieces_input_recovery as original
from runners.drive.cards import week3_pieces_verify_continuation as w
from runners.drive.cards.timing_census import read, write, filehash
from runners.drive.cards.timing_p6 import gzread, gzwrite
from tests.test_week3_pieces_input import fixture_inputs


CONFIG = dict(mode="constructed", expected_sessions=8, seed=20261026)


def fixture(root):
    root = Path(root).resolve()
    source = fixture_inputs(root / "source")
    previous = root / "previous"
    result = original.execute(previous / "output", source, CONFIG)
    pins = {}
    for name in ("week3_pieces_input.py", "week3_pieces_input_recovery.py"):
        rel = "runners/drive/cards/" + name
        target = previous / "source_capsule" / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(w.CODE_ROOT / rel, target)
        pins[rel] = filehash(target)
    # Actual runtime pins its launcher although the child never imports it.
    pins["runners/drive/week3_launch.py"] = "launch-only-not-in-child-capsule"
    write(previous / "PLAN.json", dict(module=w.MODULE, inputs=source, config=CONFIG,
          pins=pins, prior_cpu_seconds_charged=5, original_cpu_ceiling_seconds=10800))
    write(previous / "RESULT.json", result)
    write(previous / "FAILED.json", dict(status="FAILED", failure_class="cost", cpu_seconds=7))
    write(previous / "PROGRESS.json", dict(phase="verify"))
    write(previous / "EXECUTE_JOB_USAGE.json", dict(cpu_seconds=4, exit_code=0,
          includes_all_descendants_and_exited_processes=True))
    write(previous / "VERIFY_JOB_USAGE.json", dict(cpu_seconds=3, exit_code=None,
          includes_all_descendants_and_exited_processes=True))
    return {key:str(previous/name) for key,name in w.RECEIPTS.items()}


def test_exact_bytes_reentry_and_fresh_original_replay(tmp_path):
    inputs = fixture(tmp_path)
    previous = Path(inputs["previous_plan"]).parent
    old = {str(p.relative_to(previous)):filehash(p) for p in previous.rglob("*") if p.is_file()}
    output = tmp_path / "continued"
    result = w.execute(output, inputs, CONFIG)
    assert result["sessions"] == 8
    assert w.execute(output, inputs, CONFIG) == result
    assert read(output / "CONTINUATION.json")["prior_cpu_seconds_charged"] == 12
    manifest = tmp_path / "manifest.json"
    write(manifest, dict(output=str(output), inputs=inputs, config=CONFIG))
    script = "import json,sys;from runners.drive.cards.week3_pieces_verify_continuation import verify;x=json.load(open(sys.argv[1]));assert verify(x['output'],x['inputs'],x['config'])['verified']"
    subprocess.run([sys.executable,"-X","utf8","-B","-c",script,str(manifest)], check=True, timeout=60)
    assert old == {str(p.relative_to(previous)):filehash(p) for p in previous.rglob("*") if p.is_file()}
    for name, digest in read(output / "CONTINUATION.json")["unchanged_output_files"].items():
        assert filehash(output / name) == digest == filehash(previous / "output" / name)


@pytest.mark.parametrize("field,value,match", [
    ("FAILED.json",dict(status="FAILED",failure_class="engineering",cpu_seconds=7),"cost interruption"),
    ("EXECUTE_JOB_USAGE.json",dict(cpu_seconds=4,exit_code=1,includes_all_descendants_and_exited_processes=True),"complete execution"),
    ("VERIFY_JOB_USAGE.json",dict(cpu_seconds=4,exit_code=None,includes_all_descendants_and_exited_processes=True),"CPU receipts"),
])
def test_invalid_interruption_refused(tmp_path,field,value,match):
    inputs = fixture(tmp_path)
    (Path(inputs["previous_plan"]).parent/field).write_text(json.dumps(value),encoding="utf-8")
    with pytest.raises(ValueError, match=match):
        w.execute(tmp_path/"new",inputs,CONFIG)


def test_copy_mutation_refused(tmp_path):
    inputs = fixture(tmp_path)
    output = tmp_path/"new"
    w.execute(output,inputs,CONFIG)
    path = output/"WB1_BIN_EDGES.json"
    path.write_text(path.read_text()+" ",encoding="utf-8")
    with pytest.raises(ValueError,match="output bytes"):
        w.verify(output,inputs,CONFIG)


def test_resealed_false_checkpoint_still_fails_original_replay(tmp_path):
    inputs = fixture(tmp_path)
    previous = Path(inputs["previous_plan"]).parent/"output"
    index = read(previous/"WB1_INPUT_INDEX.json")
    path = previous/index[0]["file"]
    unit = gzread(path)
    unit["actions"][0]["length"] += 100
    path.unlink()
    gzwrite(path,unit)
    index[0]["sha256"] = filehash(path)
    (previous/"WB1_INPUT_INDEX.json").write_text(json.dumps(index),encoding="utf-8")
    output = tmp_path/"new"
    w.execute(output,inputs,CONFIG)
    with pytest.raises(ValueError,match="reproduce original source"):
        w.verify(output,inputs,CONFIG)


def test_source_capsule_and_population_changes_refused(tmp_path):
    inputs = fixture(tmp_path)
    with pytest.raises(ValueError,match="configuration"):
        w.execute(tmp_path/"new",inputs,{**CONFIG,"expected_sessions":9})
    capsule = Path(inputs["previous_plan"]).parent/"source_capsule/runners/drive/cards/week3_pieces_input.py"
    capsule.write_text(capsule.read_text()+"\n",encoding="utf-8")
    with pytest.raises(ValueError,match="capsule changed"):
        w.execute(tmp_path/"new",inputs,CONFIG)
