"""Known answers for V4.c saved-only diagnostics; synthetic receipts explicit."""
from __future__ import annotations
import copy
import json
import os
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest

from runners.drive.cards import menus_v4_saved_diagnostics as m
from runners.drive.cards.menus_io import read, sha256, write
from runners.drive.statistics import cluster_interval


CONFIG = dict(bootstrap_draws=2000, bootstrap_seed=20261017)


def fixture(root):
    root = Path(root); source = root / "source"; upstream = root / "V4"; output = upstream / "output"
    source.mkdir(parents=True, exist_ok=False); output.mkdir(parents=True)
    sessions = []
    for w in range(4):
        for s in range(5):
            rows = []
            for j in range(4):
                key = f"w{w}s{s}j{j}"
                rows.append(dict(key=key, writer=f"w{w}", session=f"w{w}s{s}", ordinal=j,
                    open_at=s*100+w*10+j*2, resolved_at=s*100+w*10+j*2+1,
                    handling=m.ACTIONS[(j+w)%4], previous_handling=None, menu=["a", "b"]))
            sessions.append(dict(writer=f"w{w}", session=f"w{w}s{s}", timestamp=s*100+w*10,
                                 end_at=s*100+w*10+10, rows=rows))
    rows = sorted([r for s in sessions for r in s["rows"]], key=lambda r:r["key"])
    keys = [r["key"] for r in rows]
    arrays = np.random.default_rng(731).normal(size=(len(rows), 16))
    geometry = dict(keys=keys)
    write(source / "SESSIONS.json", sessions)
    write(source / "PREDICTIONS.json", [dict(key=k, probabilities={"B-pop":[.25]*4}) for k in keys])
    write(output / "GEOMETRY.json", geometry)
    np.savez(output / "GEOMETRY.npz", menu_mini=arrays)
    likelihood = source / "original_likelihood_source.py"
    likelihood.write_text("# Synthetic source pin; fixture only. No historical corpus run claimed.\n", encoding="utf8")
    plan = dict(module="runners.drive.cards.menus_v4_full", config=dict(seed=20261017),
                inputs={k:str(source / name) for k,name in (("sessions","SESSIONS.json"),("predictions","PREDICTIONS.json"))},
                pins={str(p.resolve()):sha256(p) for p in (source/"SESSIONS.json",source/"PREDICTIONS.json",likelihood)},
                synthetic_fixture_only=True)
    write(upstream / "PLAN.json", plan); binding = dict(synthetic_fixture_only=True)
    write(output / "BINDING.json", binding)
    worlds, nulls = [], []
    for cell in m.roster():
        scalar = arrays[:,0] + arrays[:,1]
        trace = [dict(key=r["key"], writer=r["writer"], session=r["session"], outcome=m.ACTIONS.index(r["handling"]),
                      previous_key=None, scalar=float(z), probabilities=[.25]*4) for r,z in zip(rows,scalar)]
        construction = dict(cell=cell, rows=trace, oracle={k:[float(z)] for k,z in zip(keys,scalar)})
        rebuilt = m.rebuild(sessions, construction, 20261017)
        held = [r for r in rebuilt if "s4j" in r["key"]]
        truth = [m.ACTIONS.index(r["handling"]) for r in held]
        direction = np.eye(16)[:,:2]
        trained = [r["key"] for r in rows if any(f"s{s}j" in r["key"] for s in (0,1,2))]
        probability = np.full((len(held),4), .25)
        if cell["delta"] > 0 and not cell["permuted"]:
            probability[:] = .1
            selected = np.asarray(truth) if cell["delta"] >= .4 else (np.asarray(truth)+1)%4
            probability[np.arange(len(held)),selected] = .7
        saved = dict(keys=[r["key"] for r in held], writers=[r["writer"] for r in held], truth=truth,
                     population=np.full((len(held),4),.25).tolist(),
                     predictions={name:probability.tolist() for name in m.READERS},
                     selected_taste="taste_2", selected_kernel="kernel_0.8", taste_directions={"2":direction.tolist()},
                     train_keys=trained, calibration_keys=[r["key"] for r in rows if "s3j" in r["key"]], fits={})
        gains = m.half_brier(saved["population"], np.asarray(truth))-m.half_brier(probability,np.asarray(truth))
        use = m.interval(gains,saved["writers"],**dict(seed=CONFIG["bootstrap_seed"],draws=2000))
        statistic = float(cell["replicate"]) if cell["delta"] == 0 else 20*cell["delta"]
        readers = {}
        for name in m.READERS:
            if name != "R-Phase0":
                saved["fits"][name] = dict(null_log_likelihood=-100., fitted_log_likelihood=-100+statistic/2,
                    method="Laplace marginal likelihood; centered normal writer coefficients")
            readers[name] = dict(likelihood_ratio=None if name == "R-Phase0" else statistic,
                detected=statistic > 5, usefulness={key:use[key] for key in ("estimate","interval95")})
        world = dict(cell=cell, readers=readers)
        folder = output / "worlds" / m.world_name(cell)
        for name,data in (("CONSTRUCTION.json",construction),("READERS.json",saved),("RESULT.json",world)):
            write(folder / name,data)
        write(folder / "CHECKPOINT.json",dict(binding=dict(run=binding,cell=cell),
              hashes={name:sha256(folder/name) for name in ("CONSTRUCTION.json","READERS.json","RESULT.json")}))
        (nulls if cell["permuted"] else worlds).append(world)
    write(output / "WORLDS.json",worlds); write(output / "NULL_WORLDS.json",nulls)
    write(output / "SUMMARY.json",dict(synthetic_fixture_only=True))
    write(upstream / "COMPLETE.json",dict(status="COMPLETE",fresh_process_verified=True, synthetic_fixture_only=True,
          outputs={p.relative_to(upstream).as_posix():sha256(p) for p in upstream.rglob("*") if p.is_file()}))
    inputs = dict(sessions=str(source/"SESSIONS.json"), predictions=str(source/"PREDICTIONS.json"),
        likelihood_source=str(likelihood),v4_plan=str(upstream/"PLAN.json"),v4_complete=str(upstream/"COMPLETE.json"),
        v4_summary=str(output/"SUMMARY.json"),worlds=str(output/"WORLDS.json"),null_worlds=str(output/"NULL_WORLDS.json"),
        geometry=str(output/"GEOMETRY.json"),geometry_arrays=str(output/"GEOMETRY.npz"))
    return {k:str(Path(v).resolve()) for k,v in inputs.items()}, CONFIG.copy()


def test_writer_weighted_interval_matches_original_bootstrap():
    y=[.3,-.1,.2,.4,-.7,.8]; w=["a","a","b","c","c","c"]
    old=cluster_interval(y,w,seed=20261017,draws=2000)
    new=m.interval(y,w,20261017,2000)
    np.testing.assert_allclose([new["estimate"],*new["interval95"]],[old["estimate"],*old["interval95"]],atol=1e-15)
    assert m.interval(np.zeros(6),w,20261017,2000)["state"] == "null"


def test_overlap_writer_slopes_orthogonal_and_constant():
    x=np.tile([-1.,0.,1.,0.],2)[:,None]; w=np.repeat(["a","b"],4)
    y=x[:,0]*np.repeat([3.,-7.],4)+np.repeat([10.,20.],4)
    assert m.overlap(x,y,w)["r_squared"] == pytest.approx(1)
    assert m.overlap(x,np.tile([0.,1.,0.,-1.],2),w)["r_squared"] == pytest.approx(0)
    assert m.overlap(x,np.repeat([10.,20.],4),w)["r_squared"] is None


def test_kernel_delays_unresolved_labels_and_keeps_source_unchanged():
    rows=[dict(key=str(i),writer="w",open_at=i,resolved_at=i+2,handling="accept") for i in range(4)]
    before=copy.deepcopy(rows); values=m.kernel(rows,{str(i):[.25]*4 for i in range(4)},.5)[:,0]
    np.testing.assert_allclose(values,[0,0,.375,.5625]); assert rows==before


def test_full_serialized_replay_resume_and_tamper(tmp_path):
    inputs,config=fixture(tmp_path/"inputs"); output=tmp_path/"output"; output.mkdir()
    write(output/"YIELD_REQUEST.json",dict(reason="fixture"))
    assert m.execute(output,inputs,config)["status"] == "yielded"
    (output/"YIELD_REQUEST.json").unlink()
    result=m.execute(output,inputs,config)
    assert result["primary"] is None and not result["scientific_admission"]
    assert result["world_count"] == 110
    cells=result["cells"]["R-both"]["cells"]
    assert next(c for c in cells if c["plant"]=="taste_matched" and c["delta"]==.4)["predictive_detection_share"]==1
    assert next(c for c in cells if c["plant"]=="taste_matched" and c["delta"]==.2)["predictive_detection_share"]==0
    assert m.execute(output,inputs,config)==result
    args=tmp_path/"arguments.json"; write(args,dict(output=str(output),inputs=inputs,config=config))
    code="import json,sys; from pathlib import Path; from runners.drive.cards.menus_v4_saved_diagnostics import verify; a=json.load(open(sys.argv[1])); print(verify(Path(a['output']),a['inputs'],a['config']))"
    run=subprocess.run([sys.executable,"-B","-c",code,str(args)],capture_output=True,text=True,
                       env={**os.environ,"PYTHONHASHSEED":"721"},timeout=30)
    assert run.returncode==0,run.stderr
    path=Path(inputs["worlds"]).parent/"worlds/taste_matched-0.0-0/READERS.json"
    path.write_text(path.read_text()+" ",encoding="utf8")
    with pytest.raises(ValueError,match="artifact changed"):
        m.verify(output,inputs,config)


def test_empirical_threshold_can_fail_and_is_not_primary():
    rows=[]
    for cell in m.roster():
        values={name:dict(likelihood_ratio=None if name=="R-Phase0" else float(cell["replicate"]),
            predictive=dict(detected=False),overlap_test=None) for name in m.READERS}
        rows.append(dict(cell=cell,readers=values))
    report=m.aggregate(rows)
    expected=np.quantile([c["cell"]["replicate"] for c in rows if c["cell"]["permuted"] or c["cell"]["delta"]==0],.95)
    assert report["R-both"]["empirical_95th_percentile"]==expected
    assert report["R-Phase0"]["empirical_95th_percentile"] is None
