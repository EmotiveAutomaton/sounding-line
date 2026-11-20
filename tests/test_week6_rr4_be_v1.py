from pathlib import Path

import numpy as np
import pytest

from runners.drive.cards import week6_rr4_runner_v1 as runner
from runners.drive.cards import week6_rr4_v1 as model


def test_two_earlier_repeats_and_latest_actual_eligible_play():
    people = np.repeat([0,1,2,3], [5,3,4,4])
    counters = np.array([1,2,3,4,6, 1,2,3, 1,2,4,5, 1,2,3,4])
    ok = people != 3
    groups, flow = model.split(people,counters,ok)
    assert groups == [([0,1,2,3],[1,2],3)]
    assert flow["too_few_recorded_repeats"] == 1
    assert flow["insufficient_repeats_with_preceding_attempt"] == 1
    assert flow["ambiguous_or_missing_history"] == 1
    assert flow["repeat_plays_missing_preceding_attempt"] == 2


def test_references_use_completed_earlier_scores_even_when_all_are_negative():
    games=np.zeros((4,30,10))
    games[:,0,7]=[-9,-4,-7,999]
    groups=[([0,1,2,3],[1,2],3)]
    _,_,tr,te=model.reference_rows(groups,games)
    assert tr.tolist()==[[0,-9,-9],[0,-4,-4]]
    assert te.tolist()==[[0,-7,-4]]
    games[-1,:,7]=np.nan
    assert model.reference_rows(groups,games)[3].tolist()==te.tolist()


def test_support_is_filed_before_access_to_any_outcomes(tmp_path):
    class Archive(dict):
        def __getitem__(self,key):
            if key not in {"person","counter","repeat_eligible"}:
                assert (tmp_path/"SUPPORT.json").is_file()
                raise AssertionError("unexpected outcome access")
            return super().__getitem__(key)
    archive=Archive(person=np.array([0,0,1]),counter=np.array([1,2,1]),repeat_eligible=np.ones(3,bool))
    assert runner.project(archive,{},tmp_path,False)[0] is None
    assert (tmp_path/"SUPPORT.json").is_file()
    proof=runner.read(tmp_path/"SUPPORT.receipt.json")
    assert proof["counts_sha256"]==runner.filehash(tmp_path/"SUPPORT.json")
    assert proof["registration"]==runner.REGISTRATION


def test_pair_specific_ties_and_99_versus_100_players():
    n=201
    scores=np.column_stack((np.zeros(n),np.ones(n),np.full(n,2.)))
    refs=np.zeros_like(scores)
    refs[:100,2]=1
    refs[0,1]=1
    delta,differ=model.paired_scores(scores,refs)
    row=model.draw_statistic(delta,differ,np.ones(n))
    results=model.summarize(scores,refs,[row]*2000)
    first,second=[results["comparisons"][model.pair_name(a,b)] for a,b in model.PAIRS[:2]]
    assert first["differ"]==100 and first["disposition"]=="above zero"
    assert second["differ"]==99 and second["disposition"]=="could not say"
    assert second["all_plays"]["interval"]==[1.,1.]
    assert results["primary"]=="could not say"


def test_conditional_scoring_uses_whole_player_weights_and_retains_other_pairs():
    scores=np.array([[0.,1.,1.],[0.,1.,6.],[0.,1.,3.]])
    refs=np.array([[0.,0.,0.],[0.,0.,2.],[0.,1.,3.]])
    delta,diff=model.paired_scores(scores,refs)
    values=model.draw_statistic(delta,diff,np.array([2.,1.,1.]))
    assert values[:2]==[4.5,2.75]
    scores[:,1]=np.nan
    delta,diff=model.paired_scores(scores,refs)
    values=model.draw_statistic(delta,diff,np.ones(3))
    assert values[0]==4.5 and values[2] is None


def test_training_only_intercepts_have_independent_score_roots():
    linear=np.array([-.2,.3,1.,-.7,1.,1.3])
    g=np.repeat([0,1],3)
    y=np.array([0.,1.,0.,1.,0.,1.])
    a=model.intercepts(linear,g,y)
    assert np.allclose(a,model.intercepts(linear,g,y,True),rtol=0,atol=1e-10)
    assert np.allclose(np.bincount(g,weights=1/(1+np.exp(-linear-a[g]))),[1,2])
    with pytest.raises(ValueError,match="both training choices"):
        model.intercepts(linear,g,np.zeros(6))


def test_execute_resume_replay_and_three_equal_model_dimensions(tmp_path,monkeypatch):
    n=12
    rng=np.random.default_rng(442)
    people=np.repeat(np.arange(n),5)
    counters=np.tile(np.arange(1,6),n)
    games=np.zeros((len(people),30,10))
    games[:,:,2]=rng.choice([-5.,0.,5.],size=games.shape[:2])
    games[:,:,3]=rng.integers(0,12,size=games.shape[:2])
    games[:,:,4]=-rng.integers(0,12,size=games.shape[:2])
    games[:,:,6]=rng.integers(0,2,size=games.shape[:2])
    games[:,:,7]=rng.choice([-5.,-2.,1.,7.],size=games.shape[:2])
    path=tmp_path/"constructed.npz"
    np.savez(path,plays=games,person=people,counter=counters,repeat_eligible=np.ones(len(people),bool),first=games[counters==1])
    parent={"primary":{"gamma":.65,"standing_sd":5.}}
    identity={"source_complete":"synthetic source","task":"synthetic archive","md3_complete":"synthetic parent"}
    monkeypatch.setattr(runner.original,"authenticate",lambda a:(path,parent,identity))
    reg=Path(__file__).resolve().parents[1]/"docs/design/stage-15/week6/D3_AMENDMENT_BE_20261120.json"
    inputs=dict(registration=str(reg),source_run="constructed",md3_run="constructed")
    config=dict(card="RR4",draws=2000,max_new_draws=37,max_wall_seconds=600)
    out=tmp_path/"result"
    assert runner.execute(out,inputs,config)["completed"]==37
    config["max_new_draws"]=2000
    assert runner.execute(out,inputs,config)["draws"]==2000
    assert runner.verify(out,inputs,config)["verified"]
    detail=runner.read(out/"verify/RESULT.json")
    assert detail["support"]["training_plays"]==n*3
    assert {x["estimated_free_parameters"] for x in detail["training_fits"]["arms"].values()}=={8+n}
    assert all(len(detail["comparisons"][model.pair_name(a,b)]["all_plays"]["interval"])==2 for a,b in model.PAIRS)
