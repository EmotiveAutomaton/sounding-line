import math
import json
import os
import subprocess
import sys
import gzip
import numpy as np
import pytest

from scipy.special import expit
from runners.drive.cards.events_d32 import (
    repertoire_flags,selected_option,prepare_arrays,appeal_covariate,logistic_fit,
    fitted_contrast,summarize_bootstrap,within_writer_shuffle,checkpoint_read,checkpoint_write,run_arm)
from runners.drive.cards.events_d32 import cluster_rows
from runners.drive.cards.events_p5 import write,filehash


def test_repertoire_strict_past_and_ten_other_writers():
    meta={"early":dict(writer="a",timestamp=0,end_at=1),"now":dict(writer="a",timestamp=3,end_at=4),
          "future":dict(writer="a",timestamp=5,end_at=6),"overlap":dict(writer="a",timestamp=2,end_at=3)}
    typed={"early":[0],"future":[1],"overlap":[2]}
    for i in range(10):
        meta[f"other{i}"]=dict(writer=str(i),timestamp=0,end_at=1);typed[f"other{i}"]=[1]
    flags=repertoire_flags(meta,typed,{"now":[0,1,2]})["now"]
    assert flags[0]["in_repertoire"] and flags[0]["eligible"]
    assert flags[1]["outside"] and flags[1]["eligible"] and flags[1]["other_typed_writers"]==10
    assert flags[2]["outside"] and not flags[2]["eligible"]


def test_selected_text_join_never_guesses_ambiguous_option():
    assert selected_option(dict(handling="edit",menu=["a","b"],inserted="b"))==1
    assert selected_option(dict(handling="dismiss",menu=["a","b"],inserted="")) is None
    with pytest.raises(ValueError,match="ambiguous"):
        selected_option(dict(handling="accept",menu=["a","a"],inserted="a"))


def test_leave_writer_out_appeal_cannot_read_own_outcomes():
    y=np.array([0,1,0,1]);groups=np.array([0,0,1,1]);clusters=np.array([0,0,0,0])
    a=appeal_covariate(y,groups,clusters,np.ones(2))
    b=appeal_covariate(np.array([1,1,0,1]),groups,clusters,np.ones(2))
    assert np.array_equal(a[:2],b[:2])
    assert not np.array_equal(a[2:],b[2:])
    assert np.isfinite(appeal_covariate(y,groups,clusters,np.array([2,0]))).all()


def test_bootstrap_duplicate_writers_never_become_their_own_donors():
    y=np.array([0,1,0,1]);groups=np.array([0,0,1,1]);clusters=np.zeros(4,dtype=int)
    multiplicity=np.array([3,1])
    a=appeal_covariate(y,groups,clusters,multiplicity)
    b=appeal_covariate(np.array([1,1,0,1]),groups,clusters,multiplicity)
    np.testing.assert_array_equal(a[:2],b[:2])
    assert not np.array_equal(a[2:],b[2:])
    only_self=appeal_covariate(y,groups,clusters,np.array([4,0]))
    np.testing.assert_array_equal(only_self[:2],np.zeros(2))


def fixture_rows(effect=-1.,seed=19,nwriters=8,n=160):
    rng=np.random.default_rng(seed);rows=[]
    for writer in range(nwriters):
        for i in range(n):
            outside=int(rng.integers(2));length=int(rng.integers(5,40));position=int(rng.integers(5))
            probability=expit(-.5+.1*writer+effect*outside-.1*position)
            rows.append(dict(writer=str(writer),session=str(writer)+"s",cluster=int(rng.integers(4)),outside=outside,
                accepted=int(rng.random()<probability),position=position,length=length,
                menu_dissimilarity=float(rng.random()),session_index=i//20))
    return rows


def test_planted_negative_log_odds_recovered_with_correct_sign():
    arrays=prepare_arrays(fixture_rows())
    effect,beta,certificate=fitted_contrast(arrays)
    assert effect==pytest.approx(-1,abs=.25)
    assert certificate["gradient_max"]<=1e-6
    outside=within_writer_shuffle(arrays["x"][:,1],arrays["groups"],20261017)
    shuffled,_,_=fitted_contrast(arrays,outside=outside)
    assert abs(shuffled)<.25


def test_zero_and_reverse_plants_are_not_negative_direction_positives():
    for effect in (0.,1.):
        observed,_,_=fitted_contrast(prepare_arrays(fixture_rows(effect)))
        assert observed==pytest.approx(effect,abs=.3)


def test_descriptive_wald_and_ci_state_are_separate():
    negative=summarize_bootstrap(-1.,[-1.2,-.8,-1.1,-.9])
    assert negative["state"]=="positive"
    assert negative["p_approx"]==pytest.approx(math.erfc(abs(negative["z"])/math.sqrt(2)))
    zero=summarize_bootstrap(0.,[0.,0.])
    assert zero["state"]=="null" and zero["z"] is None and zero["p_approx"] is None
    assert summarize_bootstrap(-1.,[-1.],invalid=1)["state"]=="invalid"


def test_checkpoint_mutation_is_refused(tmp_path):
    path=tmp_path/"checkpoint.json";checkpoint_write(path,dict(value=1))
    assert checkpoint_read(path)==dict(value=1)
    path.write_text('{"value":2}',encoding="utf8")
    with pytest.raises(ValueError,match="checkpoint hash"):
        checkpoint_read(path)


def test_bootstrap_checkpoint_yield_resume(tmp_path):
    rows=fixture_rows(nwriters=4,n=70)
    config=dict(bootstrap=100,seed=20261017)
    (tmp_path/"YIELD_REQUEST.json").write_text("{}",encoding="utf8")
    pause=run_arm(tmp_path/"k50",rows,config,"k50")
    assert pause["status"]=="yielded" and pause["bootstrap_saved"]==100
    block=(tmp_path/"k50"/"BOOTSTRAP_0000.json").read_bytes()
    (tmp_path/"YIELD_REQUEST.json").unlink()
    result=run_arm(tmp_path/"k50",rows,config,"k50")
    assert result["mode"]=="main"
    assert (tmp_path/"k50"/"BOOTSTRAP_0000.json").read_bytes()==block


def test_invalid_support_and_separation_refuse():
    with pytest.raises(ValueError,match="empty"):
        prepare_arrays([])
    with pytest.raises(ValueError):
        logistic_fit(np.ones((4,1)),np.zeros(4),np.ones(4))


def test_invalid_support_is_recorded_without_an_engineering_exception(tmp_path):
    result=run_arm(tmp_path/"k50",[],dict(bootstrap=100,seed=20261017),"k50")
    assert result["state"]=="invalid" and result["effect"] is None


def test_actual_kmeans_repertoire_joins_preserve_strict_history():
    typed=[];typed_sessions=[];meta={};offers=[];offered=[]
    for i in range(12):
        for phase in (0,1):
            s=f"{i}_{phase}";meta[s]=dict(writer=str(i),timestamp=phase*2,end_at=phase*2+1)
            typed.append([1.,0.] if phase==0 else [0.,1.]);typed_sessions.append(s)
        for v in ([1.,0.],[0.,1.]):
            offers.append(dict(session=f"{i}_1",writer=str(i)));offered.append(v)
    rows,centers,census=cluster_rows(dict(typed=np.array(typed),typed_sessions=typed_sessions,meta=meta,
        offers=offers,offered=np.array(offered)),2,20261017)
    assert [r["outside"] for r in rows]==[0,1]*12
    assert all(r["other_typed_writers"]==11 for r in rows)
    assert census["eligible_rows"]==24 and census["excluded_rare_outside_options"]==0


def test_fresh_process_recomputes_primary_from_saved_rows_and_bootstraps(tmp_path):
    rows=fixture_rows(nwriters=4,n=70);config=dict(bootstrap=100,seed=20261017)
    result=run_arm(tmp_path/"k50",rows,config,"k50")
    write(tmp_path/"ROWS_k50.json",rows)
    write(tmp_path/"SUMMARY.json",dict(primary=result))
    write(tmp_path/"INPUTS.json",dict(paths={},config=config,pins={}))
    write(tmp_path/"SOURCE_PINS.json",{})
    write(tmp_path/"OUTPUT_HASHES.json",{p.relative_to(tmp_path).as_posix():filehash(p) for p in tmp_path.rglob("*.json")})
    code="import ctypes,sys; from pathlib import Path; ctypes.windll.kernel32.SetPriorityClass(ctypes.windll.kernel32.GetCurrentProcess(),0x4000); from runners.drive.cards.events_d32 import verify; assert verify(Path(sys.argv[1]),{},dict(bootstrap=100,seed=20261017))['verified']"
    child=subprocess.run([sys.executable,"-B","-c",code,str(tmp_path)],capture_output=True,text=True,
        env=dict(os.environ,PYTHONHASHSEED="287"),timeout=60)
    assert child.returncode==0,child.stderr


def test_full_handler_source_schema_and_serialization_with_fit_stub(tmp_path,monkeypatch):
    """Real source joins/writes; numerical fit and k-means tested separately."""
    import runners.drive.cards.events_d32 as module
    index=[];sessions=[];content=[]
    write(tmp_path/"model.json",{})
    write(tmp_path/"p5_inputs.json",dict(sha256=dict(content_model=filehash(tmp_path/"model.json"))))
    np.save(tmp_path/"content.npy",np.eye(2),allow_pickle=False)
    for writer in ("a","b","c"):
        for phase in (0,1):
            stem=writer+str(phase)
            record=dict(writer=writer,sentences=[dict(writer_typed=True,vector=0)])
            with gzip.open(tmp_path/f"{stem}.json.gz","wt",encoding="utf8") as f:
                json.dump(record,f)
            np.save(tmp_path/f"{stem}.npy",np.array([[1.,0.]]),allow_pickle=False)
            index.append(dict(session=stem,file=f"{stem}.json.gz",sha256=filehash(tmp_path/f"{stem}.json.gz"),
                              vectors=f"{stem}.npy",vectors_sha256=filehash(tmp_path/f"{stem}.npy")))
            row=dict(key=stem,menu=["keep","avoid"],inserted="keep",handling="accept")
            sessions.append(dict(session=stem,writer=writer,timestamp=phase*2,end_at=phase*2+1,rows=[row]))
            content.append(dict(key=stem,options=[0,1]))
    for name,value in (("p5_index",index),("p5_summary",dict(sessions=len(index))),("sessions",sessions),("content_records",content)):
        write(tmp_path/f"{name}.json",value)
    inputs={name:str(tmp_path/f"{name}.json") for name in ("p5_index","p5_summary","p5_inputs","sessions","content_records")}
    inputs.update(content_model=str(tmp_path/"model.json"),content_vectors=str(tmp_path/"content.npy"))
    def clustering(source,k,seed):
        rows=[dict(r,cluster=i%2,outside=i%2,other_typed_writers=10) for i,r in enumerate(source["offers"])]
        return rows,np.eye(2),dict(clusters=k,eligible_rows=len(rows))
    def fitting(arrays,multiplicity=None,initial=None,y=None,outside=None):
        beta=np.zeros(arrays["x"].shape[1]);beta[1]=-.25
        return -.25,beta,dict(gradient_max=0.,iterations=1,loss=.5)
    monkeypatch.setattr(module,"cluster_rows",clustering)
    monkeypatch.setattr(module,"fitted_contrast",fitting)
    config=dict(bootstrap=2000,seed=20261017,clusters=[50,20,100])
    result=module.execute(tmp_path/"out",inputs,config)
    assert result["primary"]["state"]=="positive"
    assert set(result["controls"])=={"repertoire_shuffle","outcome_shuffle"}
    assert set(result["specifications"])=={"k20","k100"}
    assert module.verify(tmp_path/"out",inputs,config)["verified"]
    with pytest.raises(ValueError,match="completed output"):
        module.execute(tmp_path/"out",inputs,config)
