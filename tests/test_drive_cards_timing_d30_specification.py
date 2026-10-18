import copy
import json
import time
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch
import numpy as np
import pytest
from runners.drive.cards import timing_d30_specification as card
from runners.drive.cards import timing_d30 as original
from runners.drive.cards.timing_stats import sufficient, fit
from runners.drive.cards.timing_census import read, write, filehash
from runners.drive.cards.timing_p6 import gzwrite
from tests.test_drive_cards_timing_d30 import known_rows

SMALL = dict(card.CONFIG, bootstrap_draws=200, permutations=200)


def matrix(signal=1):
    rng = np.random.default_rng(71)
    owners = np.repeat(np.arange(12).astype(str), 40).tolist()
    x = np.column_stack([np.tile(np.arange(40)%2,12), rng.normal(size=480)])
    count = rng.normal(size=480)
    y = signal*x[:,0] + .05*rng.normal(size=480)
    return dict(designs=[x.tolist(), np.column_stack([x,count]).tolist()],
                y=y.tolist(), writers=owners, timing_mode="per_character", direction=1)


def fixture_sources(tmp_path):
    rows = known_rows()
    rows += [dict(r, marker=r["marker"]+":extra") for r in rows.copy()
             if r["marker"].startswith("word:habit") and r["index"]%2==0]
    inputs = {}
    for name, extension in [("primary",False),("extension",True)]:
        root = tmp_path/name; cfg = dict(card.prior.ORIGINAL_CONFIG, extension=extension)
        m, markers = card.designs(rows, "per_character")
        x = m["designs"][int(extension)]
        baseline = dict(effect=fit(sufficient(x,m["y"],m["writers"],True))[0],
                        observations=len(m["y"]),writers=len(set(m["writers"])))
        write(root/"PLAN.json",dict(config=cfg,module="runners.drive.cards.timing_d30",pins={}))
        gzwrite(root/"output/D30_INTERMEDIATES.json.gz",dict(rows=rows,config=cfg,timing_mode="per_character"))
        write(root/"output/D30_PRIMARY.json",baseline)
        write(root/"output/D30_MARKERS.json",markers)
        write(root/"COMPLETE.json",dict(status="COMPLETE",fresh_process_verified=True,
            outputs={p.relative_to(root).as_posix():filehash(p) for p in root.rglob("*") if p.is_file()}))
        inputs[name+"_completion"] = str(root/"COMPLETE.json")
    return inputs


@pytest.mark.parametrize("extension", [False,True])
def test_exact_design_matches_original_handler(extension):
    rows = known_rows(); captured = {}
    def capture(x,y,writers,**kwargs):
        captured.update(x=x,y=y,writers=writers)
        return dict(state="null")
    with patch.object(original,"regression",capture):
        original.analyze(rows,dict(card.prior.ORIGINAL_CONFIG,extension=extension),"per_character",controls=False)
    m,_ = card.designs(rows,"per_character")
    assert captured == dict(x=m["designs"][int(extension)],y=m["y"],writers=m["writers"])


def test_weights_equal_independent_demeaned_lstsq():
    m = matrix(); y=np.array(m["y"]); owners=np.array(m["writers"])
    for x in m["designs"]:
        a=np.array(x); b=y.copy()
        for w in sorted(set(owners)):
            ix=owners==w; a[ix]-=a[ix].mean(0); b[ix]-=b[ix].mean()
        expected=np.linalg.lstsq(a,b,rcond=None)[0][0]
        assert card.coefficient_weights(x,m["writers"])@y == pytest.approx(expected,abs=1e-12)


@pytest.mark.parametrize("signal,state",[(1,"positive"),(-1,"negative")])
def test_planted_direction_and_null_reference(signal,state):
    r=card.compute(matrix(signal),SMALL)
    assert r["primary"]["state"]==state
    assert abs(r["primary"]["null_mean_effect"]) < .1
    if signal==1: assert r["primary"]["upper_tail_permutation_p"]==1/201
    else: assert r["primary"]["upper_tail_permutation_p"]>.95


def test_zero_signal_exact_null_and_shared_resamples():
    m=matrix(); m["y"]=[0.]*len(m["y"])
    r=card.compute(m,SMALL)
    assert r["primary"]["state"]=="null"
    assert r["primary"]["upper_tail_permutation_p"]==1
    assert r["primary"]["effect"]==r["primary"]["ci_low"]==r["primary"]["ci_high"]==0
    m=matrix(); m["designs"][1]=copy.deepcopy(m["designs"][0])
    r=card.compute(m,SMALL)
    a,b=r["specifications"]
    assert {k:v for k,v in a.items() if k!="name"}=={k:v for k,v in b.items() if k!="name"}
    assert r["primary"]["effect"]==a["effect"]


def test_nonidentifiable_and_invalid_timing_refuse():
    m=matrix(); m["designs"][1]=[[r[0],r[0]] for r in m["designs"][0]]
    with pytest.raises(ValueError,match="not identifiable"):card.compute(m,SMALL)
    with pytest.raises(ValueError,match="valid pause timing"):card.designs(known_rows(),"invalid")


def test_checkpoint_resume_preserves_rng_and_refuses_mutation(tmp_path):
    m=matrix(); output=tmp_path/"output";write(output/"YIELD_REQUEST.json",{})
    assert card.compute(m,SMALL,output/"draws")["status"]=="yielded"
    block=output/"draws/bootstrap/block-00000.json";prior=block.read_bytes()
    (output/"YIELD_REQUEST.json").unlink()
    resumed=card.compute(m,SMALL,output/"draws")
    assert resumed==card.compute(m,SMALL) and block.read_bytes()==prior
    block.write_bytes(prior+b" ")
    with pytest.raises(ValueError,match="checkpoint hash"):card.compute(m,SMALL,output/"draws")


def test_source_configuration_and_mutation_refuse(tmp_path):
    inputs=fixture_sources(tmp_path)
    assert card.source(inputs,card.CONFIG)["designs"]
    with pytest.raises(ValueError,match="configuration"):card.source(inputs,SMALL)
    p=Path(inputs["extension_completion"]);r=read(p);p.write_text(json.dumps(dict(r,fresh_process_verified=False)),encoding="utf8")
    with pytest.raises(ValueError,match="not verified complete"):card.source(inputs,card.CONFIG)
    p.write_text(json.dumps(r),encoding="utf8");target=p.parent/"output/D30_PRIMARY.json";target.write_bytes(target.read_bytes()+b" ")
    with pytest.raises(ValueError,match="binding changed"):card.source(inputs,card.CONFIG)


def test_actual_serialized_handler_fresh_process_and_reentry(tmp_path):
    inputs=fixture_sources(tmp_path);output=tmp_path/"output"
    write(output/"YIELD_REQUEST.json",{})
    assert card.execute(output,inputs,card.CONFIG)["status"]=="yielded"
    (output/"YIELD_REQUEST.json").unlink()
    result=card.execute(output,inputs,card.CONFIG)
    plan=tmp_path/"check.json";write(plan,dict(inputs=inputs,output=str(output),config=card.CONFIG))
    code="import sys,json;from runners.drive.cards.timing_d30_specification import verify;p=json.load(open(sys.argv[1]));assert verify(p['output'],p['inputs'],p['config'])['verified']"
    subprocess.run([sys.executable,"-X","utf8","-B","-c",code,str(plan)],check=True)
    before={p.relative_to(output):p.read_bytes() for p in output.rglob("*") if p.is_file()}
    assert card.execute(output,inputs,card.CONFIG)==result
    assert before=={p.relative_to(output):p.read_bytes() for p in output.rglob("*") if p.is_file()}
    saved=read(output/"SUMMARY.json");saved["primary"]["effect"]+=.1;(output/"SUMMARY.json").write_text(json.dumps(saved),encoding="utf8")
    with pytest.raises(ValueError,match="output changed"):card.verify(output,inputs,card.CONFIG)


def test_actual_counted_runtime_and_fresh_process(tmp_path):
    inputs=fixture_sources(tmp_path/"sources");root=tmp_path/"runtime"
    write(root/"PLAN.json",dict(card="D30.s-fixture",module=card.__name__,inputs=inputs,
        config=card.CONFIG,pins={v:filehash(v) for v in inputs.values()},
        forecast_cpu_seconds=600,max_wall_seconds=180,max_output_bytes=256*1024**2,smoke=True))
    log=root/"runtime.log"
    with log.open("w") as stream:
        proc=subprocess.Popen([sys.executable,"-X","utf8","-B","-m",
            "runners.drive.cards.batch_runtime_v2","run",str(root)],stdout=stream,stderr=stream)
        try:
            deadline=time.monotonic()+40
            while not (root/"OWNER.json").exists():
                if proc.poll() is not None or time.monotonic()>deadline:
                    raise RuntimeError("smoke handshake failed: "+log.read_text())
                time.sleep(.1)
            write(root/"MONITOR_READY.json",dict(owner_sha256=filehash(root/"OWNER.json")))
            assert proc.wait(timeout=180)==0,log.read_text()
            assert read(root/"COMPLETE.json")["fresh_process_verified"]
            assert read(root/"VERIFIED.json")["verified"]
            assert not Path(read(root/"ADMISSION.json")["lease"]).exists()
        finally:
            if proc.poll() is None:
                proc.terminate();proc.wait(timeout=30)

