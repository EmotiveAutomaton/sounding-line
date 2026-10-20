"""Bounded real REML fixtures plus full-count storage/scheduling validation.

Real serialized fixtures use25 bootstrap draws per arm, explicitly a test-only
count; production source validation requires2000. A separate deterministic
kernel fixture exercises all2000 writer samples and resume/checkpoint coverage.
"""
import json
import os
from pathlib import Path
import subprocess
import sys
from unittest.mock import patch

import numpy as np
import pytest

from runners.drive.cards import timing_d30_crossed_main as card
from runners.drive.cards import timing_d30_crossed as pilot
from runners.drive.cards.timing_census import read, write, filehash
from runners.drive.cards.timing_p6 import gzread
from tests.test_drive_cards_timing_d30_crossed import constructed, serialized_sources


def admitted_sources(root,signal):
    """Real synthetic source reconstruction and original six-fit pilot."""
    root=Path(root)
    inputs=serialized_sources(root/"source",signal)
    attempt=root/"pilot"
    result=pilot.execute(attempt/"output",inputs,pilot.CONFIG)
    assert result["state"]=="positive" and result["instrument_only"]
    write(attempt/"VERIFIED.json",pilot.verify(attempt/"output",inputs,pilot.CONFIG))
    write(attempt/"PLAN.json",dict(module=pilot.__name__,config=pilot.CONFIG,inputs=inputs,
        at="2026-10-18T00:00:00+00:00",pins={str(Path(pilot.__file__).resolve()):filehash(pilot.__file__)}))
    write(attempt/"COMPLETE.json",dict(status="COMPLETE",fresh_process_verified=True,at="2026-10-18T00:00:10+00:00",
        outputs={p.relative_to(attempt).as_posix():filehash(p) for p in attempt.rglob("*") if p.is_file()}))
    return dict(inputs,pilot_completion=str(attempt/"COMPLETE.json"))


def test_control_designs_equal_frozen_original_and_shuffle_respects_writers(tmp_path):
    inputs=serialized_sources(tmp_path,1)
    saved=gzread(Path(inputs["extension_completion"]).parent/"output/D30_INTERMEDIATES.json.gz")
    primary=pilot.source(inputs,pilot.CONFIG)
    matrices,evidence=card.controls(saved["rows"],saved["timing_mode"],primary)
    captured=[]
    def capture(x,y,writers,**kwargs):
        captured.append(dict(x=np.asarray(x).tolist(),y=list(y),writers=list(writers)))
        return dict(state="null")
    with patch.object(pilot.original,"regression",capture):
        pilot.original.analyze(saved["rows"],dict(card="D30",extension=True,bootstrap_draws=2000,seed=20261017),saved["timing_mode"])
    for name,actual in zip(("primary","label_shuffle","writer_shuffle"),captured):
        assert {k:matrices[name][k] for k in ("x","y","writers")}==actual
    if len(captured)==2:
        assert matrices["writer_shuffle"] is None
        assert evidence["invalid_controls"]["writer_shuffle"].startswith("fewer than three")
    permutation=evidence["outcome_permutation"]
    assert sorted(permutation)==list(range(len(primary["y"])))
    assert all(primary["writers"][i]==primary["writers"][j] for i,j in enumerate(permutation))
    assert matrices["outcome_shuffle"]["y"]==[primary["y"][i] for i in permutation]
    assert matrices["outcome_shuffle"]["x"]==primary["x"]


def test_cached_row_groups_equal_frozen_resample_with_duplicate_writers():
    matrix=constructed()
    groups=card.writer_groups(matrix)
    for selection in ([0,0,1,2,3,4,5,6],[7]*8,[7,6,5,4,3,2,1,0]):
        value=card.resample(matrix,selection,groups)
        assert value==pilot.resample(matrix,selection)
        assert len(set(value["writers"]))==8
        assert set(value["markers"])==set(matrix["markers"])


def test_primary_states_and_invalid_control_remain_distinct():
    assert card.contrast(1,[.5,1,1.5],4,30)["state"]=="positive"
    null=card.contrast(0,[-1,0,1],4,30)
    assert null["state"]=="null" and null["wald_p_two_sided"]==1
    assert card.contrast(-1,[-1.5,-1,-.5],4,30)["state"]=="negative"
    assert card.contrast(0,[0,0,0],4,30)["z"] is None
    with pytest.raises(ValueError,match="complete crossed bootstrap"):
        card.contrast(0,[0,float("nan")],4,30)


def schedule_kernel(x,y,writers,markers):
    a=np.asarray(x)
    b=np.asarray(y)
    return dict(converged=True,effect=float(b[a[:,0]==1].mean()-b[a[:,0]==0].mean()),
                estimator="test-only scheduling kernel",writers=len(set(writers)))


def test_full_2000_draw_schedule_checkpoint_resume_and_coverage(tmp_path,monkeypatch):
    matrix=constructed()
    matrix={k:v[:60]+v[-60:] for k,v in matrix.items()}
    matrices={name:matrix for name in card.ARMS}
    monkeypatch.setattr(pilot,"fit",schedule_kernel)
    output=tmp_path/"run"
    def yield_once(done):
        if done==25:raise card.Yield("fixture checkpoint")
    with pytest.raises(card.Yield):card.fit_series(matrices,card.CONFIG,output,yield_once)
    checkpoint=output/"draws/block-00000.json"
    prior=checkpoint.read_bytes()
    points,fits=card.fit_series(matrices,card.CONFIG,output)
    assert checkpoint.read_bytes()==prior
    assert all(len(fits[name])==2000 for name in card.ARMS)
    assert (points,fits)==card.fit_series(matrices,card.CONFIG)
    assert len(list((output/"draws").glob("*.receipt.json")))==80
    record=read(checkpoint)
    record["fits"]["primary"].pop()
    checkpoint.write_text(json.dumps(record),encoding="utf-8")
    checkpoint.with_suffix(".receipt.json").write_text(json.dumps(dict(sha256=filehash(checkpoint))),encoding="utf-8")
    with pytest.raises(ValueError,match="arm coverage"):
        card.fit_series(matrices,card.CONFIG,output)
    write(output/"draws/block-02000.receipt.json",{})
    with pytest.raises(ValueError,match="receipt coverage"):
        card.fit_series(matrices,card.CONFIG,output)


@pytest.mark.parametrize("signal,state",[(1,"positive"),(0,None),(-1,"negative")])
def test_actual_serialized_crossed_refits_and_fresh_process(tmp_path,monkeypatch,signal,state):
    inputs=admitted_sources(tmp_path,signal)
    small=dict(card.CONFIG,bootstrap_draws=25)
    # The real source gate refuses reduced counts until this explicit local
    # test-only patch. No production configuration or kernel changes.
    with pytest.raises(ValueError,match="configuration"):
        card.source(inputs,small)
    monkeypatch.setattr(card,"CONFIG",small)
    output=tmp_path/"main"
    write(output/"YIELD_REQUEST.json",{})
    assert card.execute(output,inputs,small)["status"]=="yielded"
    retained=(output/"draws/block-00000.json").read_bytes()
    (output/"YIELD_REQUEST.json").unlink()
    result=card.execute(output,inputs,small)
    assert (output/"draws/block-00000.json").read_bytes()==retained
    if state is not None:assert result["state"]==state
    else:assert result["ci_low"]<=0<=result["ci_high"]
    assert result["effect"]==pytest.approx(signal,abs=.02)
    assert result["bootstrap_draws"]==25 and not result["scientific_admission"]
    assert set(result["controls"])=={"label_shuffle","writer_shuffle","outcome_shuffle","timing_positive_control"}
    manifest=tmp_path/"verify.json"
    write(manifest,dict(output=str(output),inputs=inputs,config=small))
    code="import json,sys; from pathlib import Path; from runners.drive.cards import timing_d30_crossed_main as c; x=json.load(open(sys.argv[1])); c.CONFIG=x['config']; print(json.dumps(c.verify(Path(x['output']),x['inputs'],x['config'])))"
    child=subprocess.run([sys.executable,"-c",code,str(manifest)],capture_output=True,text=True,timeout=120,
        env=dict(os.environ,PYTHONHASHSEED="431"),creationflags=subprocess.BELOW_NORMAL_PRIORITY_CLASS if os.name=="nt" else 0)
    assert child.returncode==0,child.stderr
    assert json.loads(child.stdout)["primary"]==result


def test_missing_admission_source_mutation_and_exact_config(tmp_path):
    with pytest.raises(ValueError,match="configuration"):
        card.source({},dict(card.CONFIG,seed=True))
    inputs=admitted_sources(tmp_path,1)
    terminal=Path(inputs["pilot_completion"])
    complete=read(terminal)
    terminal.write_text(json.dumps(dict(complete,fresh_process_verified=False)),encoding="utf-8")
    with pytest.raises(ValueError,match="verified original crossed pilot"):
        card.source(inputs,card.CONFIG)
    terminal.write_text(json.dumps(complete),encoding="utf-8")
    design=terminal.parent/"output/CROSSED_DESIGN.json"
    design.write_bytes(design.read_bytes()+b" ")
    with pytest.raises(ValueError,match="completion binding changed"):
        card.source(inputs,card.CONFIG)
