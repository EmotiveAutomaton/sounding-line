import json
from pathlib import Path
import subprocess
import sys
import time

import pytest

from runners.drive.cards import timing_p7_hybrid_pilot as card
from runners.drive.cards.timing_census import read, write, filehash
from runners.drive.cards.timing_p7 import CachedScorer
from tests.test_drive_cards_p7_admission import tiny_model


def fixture(tmp_path):
    model, tokenizer, torch = tiny_model(None)
    scalar = CachedScorer(model, tokenizer, torch)
    units = []
    for domain in ("typed", "jester"):
        rows = [dict(index=i, is_word=True, prefix=p, target=t) for i,(p,t) in enumerate(
            [("", "red"), ("red ", "cat"), ("red cat ", "sat"), ("red ", "dog")])]
        expected = [dict(index=r["index"], is_word=True, **scalar.score(r["prefix"],r["target"])) for r in rows]
        units.append(dict(domain=domain, rows=rows, expected=expected))
    path = tmp_path/"fixture.json"
    write(path, units)
    return dict(fixture=str(path), sha256=filehash(path))


def fixture_reference(inputs, config):
    assert config == card.CONFIG
    if filehash(inputs["fixture"]) != inputs["sha256"]:
        raise ValueError("fixture changed")
    return dict(fixture=inputs["sha256"]), read(inputs["fixture"]), {}, dict(typed=8,jester=8)


def execute(output, inputs, config):
    card.reference = fixture_reference
    card.old.load_model = tiny_model
    return card.execute(output, inputs, config)


def verify(output, inputs, config):
    card.reference = fixture_reference
    card.old.load_model = tiny_model
    return card.verify(output, inputs, config)


def test_resume_fresh_replay_immutable_reentry_and_corruption(tmp_path, monkeypatch):
    inputs = fixture(tmp_path)
    monkeypatch.setattr(card, "reference", fixture_reference)
    monkeypatch.setattr(card.old, "load_model", tiny_model)
    output = tmp_path/"output"
    write(output/"YIELD_REQUEST.json", dict(fixture=True))
    assert card.execute(output, inputs, card.CONFIG)["status"] == "yielded"
    saved = (output/"typed.json.gz").read_bytes()
    (output/"YIELD_REQUEST.json").unlink()
    result = card.execute(output, inputs, card.CONFIG)
    assert result["targets"] == 8 and not result["main_admitted"]
    assert saved == (output/"typed.json.gz").read_bytes()
    assert card.verify(output, inputs, card.CONFIG)["verified"]
    hashes = {str(p):filehash(p) for p in output.rglob("*") if p.is_file()}
    assert card.execute(output, inputs, card.CONFIG) == result
    assert hashes == {str(p):filehash(p) for p in output.rglob("*") if p.is_file()}
    args = tmp_path/"args.json"; write(args, dict(inputs=inputs,output=str(output)))
    script = "from tests.test_drive_cards_p7_hybrid_pilot import verify; import json,sys; x=json.load(open(sys.argv[1])); assert verify(x['output'],x['inputs'],{'phase':'hybrid_pilot'})['verified']"
    proc = subprocess.run([sys.executable,"-X","utf8","-B","-c",script,str(args)],capture_output=True,text=True,timeout=60)
    assert proc.returncode == 0, proc.stderr
    data = read(output/"BATCH_PRIMARY.json"); data["targets"] += 1
    (output/"BATCH_PRIMARY.json").write_text(json.dumps(data), encoding="utf8")
    with pytest.raises(ValueError, match="primary/timing"): card.verify(output,inputs,card.CONFIG)


def test_main_and_unverified_source_refuse(tmp_path):
    with pytest.raises(ValueError, match="fixed pilot"): card.reference({}, dict(phase="main"))
    write(tmp_path/"COMPLETE.json", dict(status="FAILED"))
    write(tmp_path/"PLAN.json", {})
    with pytest.raises(ValueError, match="verified original"): card.reference(dict(original_pilot=str(tmp_path)),card.CONFIG)


def test_actual_counted_runtime(tmp_path):
    inputs = fixture(tmp_path); root=tmp_path/"runtime"
    write(root/"PLAN.json",dict(card="P7-hybrid-fixture",module="tests.test_drive_cards_p7_hybrid_pilot",
          inputs=inputs,config=card.CONFIG,pins={inputs["fixture"]:inputs["sha256"]},
          forecast_cpu_seconds=600,max_wall_seconds=180,max_output_bytes=16*1024**2,smoke=True))
    with (root/"runtime.log").open("w") as stream:
        proc=subprocess.Popen([sys.executable,"-X","utf8","-B","-m","runners.drive.cards.batch_runtime_v2","run",str(root)],stdout=stream,stderr=stream)
        try:
            deadline=time.monotonic()+40
            while not (root/"OWNER.json").exists():
                if proc.poll() is not None or time.monotonic()>deadline:
                    raise RuntimeError("P7 batch smoke owner handshake failed")
                time.sleep(.1)
            write(root/"MONITOR_READY.json",dict(owner_sha256=filehash(root/"OWNER.json")))
            assert proc.wait(timeout=180)==0,(root/"runtime.log").read_text()
            assert read(root/"COMPLETE.json")["fresh_process_verified"]
            assert read(root/"VERIFIED.json")["verified"]
            assert not Path(read(root/"ADMISSION.json")["lease"]).exists()
        finally:
            if proc.poll() is None:
                proc.terminate();proc.wait(timeout=30)
