"""Known-answer boundary math, half isolation and serialized split fixture."""
import copy
import itertools
import json
import os
from pathlib import Path
import subprocess
import sys

import numpy as np
import pytest

from runners.drive.cards import menus_v4_split as m
from runners.drive.cards import menus_v4_split_stats as s
from runners.drive.cards.menus_io import read,write
from runners.drive.cards.menus_v4_stats import conditional_mode
from tests.test_drive_cards_menus_v4_saved_diagnostics import fixture


def test_information_matches_exhaustive_bernoulli_score_covariance():
    x=np.array([[1.,2.],[-.5,1.],[2.,-.3]])
    p=np.array([.2,.5,.7]); writer=np.array(["a","a","b"])
    scores=[];weights=[]
    for bits in itertools.product((0,1),repeat=3):
        y=np.array(bits); score=np.zeros(2)
        for w in ("a","b"):
            a=x[writer==w]; residual=y[writer==w]-p[writer==w]; v=p[writer==w]*(1-p[writer==w])
            score+=.5*((a.T@residual)**2-(a*a).T@v)
        scores.append(score);weights.append(np.prod(np.where(y,p,1-p)))
    score=np.array(scores);weights=np.array(weights)
    np.testing.assert_allclose(weights@score,0,atol=1e-15)
    np.testing.assert_allclose(s.score_information(x,p,writer),score.T@(weights[:,None]*score),atol=1e-15)


def test_orthogonal_chibar_exact_formula_correlated_projection_and_singular_refusal():
    normals=np.array([[-2.,-3.],[-2.,3.],[2.,-3.],[2.,3.]])
    values,_=s.cone_statistics(np.diag([2.,7.]),normals)
    np.testing.assert_allclose(values,np.maximum(normals,0).__pow__(2).sum(1))
    correlation=np.array([[1.,.6],[.6,1.]])
    result,_=s.cone_statistics(correlation,normals)
    scores=normals@np.linalg.cholesky(correlation).T
    expected=[]
    for z in scores:
        alternatives=[0.,max(0,z[0])**2,max(0,z[1])**2]
        unconstrained=np.linalg.inv(correlation)@z
        if np.all(unconstrained>=0):alternatives.append(float(z@unconstrained))
        expected.append(max(alternatives))
    np.testing.assert_allclose(result,expected)
    with pytest.raises(ValueError,match="singular"):
        s.cone_statistics(np.ones((2,2)),normals)


def test_one_variance_reference_and_exact_zero_likelihood():
    rng=np.random.default_rng(912); values,_=s.cone_statistics(np.array([[9.]]),rng.normal(size=(20000,1)))
    assert abs(np.mean(values==0)-.5)<.015
    # 95th percentile of the 50:50 point-zero/chi-square1 reference is 2.7055.
    assert np.quantile(values,.95)==pytest.approx(2.705543454,abs=.12)
    x=np.array([[1.],[2.],[-1.]]); y=np.array([1.,0.,1.]); offset=np.array([.3,-.2,.1])
    ll,coefficient=conditional_mode(x,y,offset,np.zeros(1))
    assert ll==pytest.approx(float(np.sum(y*offset-np.logaddexp(0,offset))),abs=1e-14)
    np.testing.assert_array_equal(coefficient,[0.])


def test_halves_nuisance_and_causal_history_ignore_other_half_labels(tmp_path):
    inputs,config=fixture(tmp_path/"fixture");source=m.sources.load(inputs,config)
    construction,saved=m.sources.load_world(source,source["worlds"][0])
    rows=m.sources.rebuild(source["sessions"],construction,20261017);halves=s.alternating_halves(rows)
    changed=copy.deepcopy(rows)
    for i,row in enumerate(changed):
        if halves[i]==1:row["handling"]="accept" if row["handling"]!="accept" else "ignore"
    original_population,_=s.population(rows,source["sessions"],halves,0)
    changed_population,_=s.population(changed,source["sessions"],halves,0)
    np.testing.assert_array_equal(original_population,changed_population)
    np.testing.assert_array_equal(s.half_kernels(rows,halves,source["base"],.8)[halves==0],
                                  s.half_kernels(changed,halves,source["base"],.8)[halves==0])
    old=s.separate_history(rows,halves);new=s.separate_history(changed,halves)
    assert [r["previous_handling"] for r,h in zip(old,halves) if h==0]==[r["previous_handling"] for r,h in zip(new,halves) if h==0]
    for session in source["sessions"]:
        earlier={v["session"] for v in source["sessions"] if v["end_at"]<session["timestamp"]}
        eligible=[s.ACTIONS.index(r["handling"]) for r,h in zip(rows,halves) if h==0 and r["session"] in earlier]
        expected=np.bincount(eligible,minlength=4)+1.;expected/=expected.sum()
        ids=[i for i,r in enumerate(rows) if r["session"]==session["session"]]
        np.testing.assert_array_equal(original_population[ids],np.tile(expected,(len(ids),1)))
    design,audit,_=s.select_half(rows,source["sessions"],saved,source["geometry"],source["base"],0)
    other_design,other_audit,_=s.select_half(changed,source["sessions"],saved,source["geometry"],source["base"],0)
    audit.pop("test_truth");other_audit.pop("test_truth")
    assert audit==other_audit
    for reader in s.READERS:
        np.testing.assert_array_equal(design[reader][halves==0],other_design[reader][halves==0])


def test_full_native_fixture_resume_fresh_refit_and_foreign_source_refusal(tmp_path):
    inputs,_=fixture(tmp_path/"source"); output=tmp_path/"output";output.mkdir()
    write(output/"YIELD_REQUEST.json",dict(reason="synthetic"))
    assert m.execute(output,inputs,m.FIXTURE_CONFIG)["status"]=="yielded"
    (output/"YIELD_REQUEST.json").unlink()
    report=m.execute(output,inputs,m.FIXTURE_CONFIG)
    assert report["primary"] is None and report["synthetic_fixture_only"]
    assert report["world_count"]==1 and not report["scientific_admission"]
    assert m.execute(output,inputs,m.FIXTURE_CONFIG)==report
    args=tmp_path/"REQUEST.json";write(args,dict(output=str(output),inputs=inputs,config=m.FIXTURE_CONFIG))
    code="import json,sys;from pathlib import Path;from runners.drive.cards.menus_v4_split import verify;a=json.load(open(sys.argv[1]));print(verify(Path(a['output']),a['inputs'],a['config']))"
    run=subprocess.run([sys.executable,"-B","-c",code,str(args)],capture_output=True,text=True,
        timeout=40,env={**os.environ,"PYTHONHASHSEED":"837"})
    assert run.returncode==0,run.stderr
    Path(inputs["predictions"]).write_text(Path(inputs["predictions"]).read_text()+" ",encoding="utf8")
    with pytest.raises(ValueError,match="pin changed"):
        m.verify(output,inputs,m.FIXTURE_CONFIG)


def test_null_failure_cannot_be_rescued_by_perfect_power():
    assert m.label(.2,1,1,0)=="blind"
    assert m.label(0,1,1,.15)=="blind"
    assert m.label(.1,.8,1,.1)=="sees"
    assert m.label(.1,.7,.8,.1)=="sees_large_only"
    assert m.difference([1]*10,[0]*10,20261018,2000,False)["state"]=="invalid"
    assert m.difference([1]*10,[0]*10,20261018,2000,True)["state"]=="positive"
    assert m.difference([0]*10,[1]*10,20261018,2000,True)["state"]=="negative"
