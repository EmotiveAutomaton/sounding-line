import os
from pathlib import Path
import subprocess
import sys

import pytest

from runners.drive.cards import week3_pieces_input as prep
from runners.drive.cards import week3_pieces_coverage as w
from runners.drive.cards.timing_census import read, write, filehash
from tests.test_week3_pieces_input import fixture_inputs


def prepared(root):
    inputs=fixture_inputs(root/"source")
    base=root/"preparation"
    output=base/"output"
    prep.execute(output,inputs,dict(mode="constructed",expected_sessions=8,seed=prep.SEED))
    prep.verify(output,inputs,dict(mode="constructed",expected_sessions=8,seed=prep.SEED))
    write(base/"COMPLETE.json",dict(status="COMPLETE",fresh_process_verified=True,
        outputs={p.relative_to(base).as_posix():filehash(p) for p in output.rglob("*") if p.is_file() and p.name!="PROGRESS.json"}))
    return dict(preparation_complete=str(base/"COMPLETE.json"),preparation_index=str(output/"WB1_INPUT_INDEX.json"),
        writer_split=str(output/"WB1_WRITER_SPLIT.json"),bin_edges=str(output/"WB1_BIN_EDGES.json"),preparation_result=str(output/"WB1_INPUT_RESULT.json"))


def config():
    return dict(mode="constructed",coarse=False,seed=prep.SEED,surrogate_draws=4,bootstrap_draws=20,minimum_occurrences=1,minimum_writers=1)


def test_full_source_bound_coverage_and_fresh_replay(tmp_path):
    inputs=prepared(tmp_path)
    output=tmp_path/"coverage"
    result=w.execute(output,inputs,config())
    assert result["full_card_complete"] is False and result["scientific_admission"] is False
    assert result["whole"]["scope"]=="whole" and result["thirds"]["scope"]=="thirds"
    assert w.verify(output,inputs,config())["verified"]
    manifest=tmp_path/"verification.json"
    write(manifest,dict(output=str(output),inputs=inputs,config=config()))
    script="import json,sys;from pathlib import Path;from runners.drive.cards.week3_pieces_coverage import verify;x=json.load(open(sys.argv[1]));assert verify(Path(x['output']),x['inputs'],x['config'])['verified']"
    subprocess.run([sys.executable,"-X","utf8","-B","-c",script,str(manifest)],check=True,env=dict(os.environ,PYTHONHASHSEED="83"),timeout=60)


def test_changed_input_or_reference_refused(tmp_path):
    inputs=prepared(tmp_path)
    output=tmp_path/"coverage"
    w.execute(output,inputs,config())
    path=next((output/"references").glob("*.json.gz"))
    path.write_bytes(path.read_bytes()+b"changed")
    with pytest.raises(ValueError,match="checkpoint"):
        w.verify(output,inputs,config())
    p=Path(inputs["writer_split"])
    p.write_text(p.read_text()+" ")
    with pytest.raises(ValueError,match="binding changed"):
        w.load(inputs,config())


def test_corpus_thresholds_are_not_fixture_thresholds():
    with pytest.raises(ValueError,match="threshold/draw"):
        w.validate_config(dict(config(),mode="corpus"))


def test_operational_yield_not_scientific_null(tmp_path):
    inputs=prepared(tmp_path)
    output=tmp_path/"coverage"
    write(output/"YIELD_REQUEST.json",dict(reason="constructed interruption"))
    result=w.execute(output,inputs,config())
    assert result["status"]=="yielded"
    assert not (output/"WB1_COVERAGE_RESULT.json").exists()
    (output/"YIELD_REQUEST.json").unlink()
    assert w.execute(output,inputs,config())["status"]=="component_complete"
    assert w.verify(output,inputs,config())["verified"]
