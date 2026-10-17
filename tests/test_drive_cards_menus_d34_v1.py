import gzip
import json
import numpy as np
import pytest

from runners.drive.cards import menus_d34_v1 as v1
from runners.drive.cards.menus_io import read, write, sha256


def test_surprisal_is_simulated_from_actual_handling_reader_and_zero_is_explicit():
    assert v1.unexplained([.8, .05, .1, .05], "rare")["unexplained"]
    assert not v1.unexplained([.05, .85, .05, .05], "common")["unexplained"]
    impossible = v1.unexplained([.8, 0., .1, .1], "impossible")
    assert impossible["unexplained"] and impossible["surprisal"] is None and impossible["impossible_under_reader"]
    with pytest.raises(ValueError, match="four-class"):
        v1.unexplained([.5, .8, .1, .1], "invalid")


def test_linkage_never_uses_nearest_menu_and_counts_mixed_own_and_unsupported():
    edits = []
    for ordinal, origin, owners, deleted in [(1,"own",[],{"typed":1}), (2,"model",[10],{"accepted":1,"typed":1}),
            (3,"model",[10,20],{"accepted":1}), (4,"model",[99],{"accepted":1}), (5,"model",[10],{"accepted":1})]:
        edits.append(dict(ordinal=ordinal, origin=origin, accepted_owners_touched=owners, deleted_origin_counts=deleted, before_vector=0, after_vector=1))
    session = dict(session="s",writer="w",edits=edits)
    decisions = {("s",10):dict(key="known",handling="edit")}
    forecasts = {"known":dict(writer="w",truth="edit",probabilities={"B-mixlogit":[.8,.05,.1,.05]})}
    rows, audit = v1.linked_corrections(session,np.eye(2),decisions,forecasts,{})
    assert len(rows)==1 and rows[0]["ordinal"]==5
    assert audit==dict(all_corrections=5,unsupported_own=1,unsupported_mixed=1,unsupported_multiple_owners=1,
                       unsupported_missing_forecast_link=1,supported_corrections=1,unexplained=1)


def test_cohesion_uses_only_cross_session_pairs_and_matching_is_exact():
    rows=[]
    for session in "ab":
        for ordinal in range(5):
            rows.append(dict(session=session,ordinal=ordinal,key=str(ordinal),unexplained=ordinal<3,
                unit=np.array([1.,0.]),surprisal=1.,threshold80=.5,impossible_under_reader=False))
    moments, selected=v1.matched_moments(rows,"writer",20261017)
    assert [r["count"] for r in moments["unexplained"]]==[2,2]
    assert [r["count"] for r in moments["explained"]]==[2,2]
    assert v1.cohesion(moments["unexplained"])==1.
    assert len(selected)==8
    assert v1.cohesion(moments["unexplained"][:1]) is None


def fixture_inputs(tmp_path):
    sessions=[]; predictions=[]; index=[]
    for wi,writer in enumerate("abcde"):
        for number in range(3):
            name=writer+str(number); rows=[]; edits=[]; vectors=[np.zeros(8)]
            for j,probability in enumerate(([.8,.05,.1,.05],[.05,.85,.05,.05])):
                key=name+str(j); owner=10+j
                rows.append(dict(key=key,writer=writer,session=name,ordinal=owner,handling="edit"))
                predictions.append(dict(key=key,writer=writer,truth="edit",probabilities={"B-mixlogit":probability}))
                vector=np.zeros(8)
                if j==0: vector[wi]=1
                else:
                    angle=(number+1)*(1.3+wi*.07); vector[6:]=[np.cos(angle),np.sin(angle)]
                vectors.append(vector)
                edits.append(dict(ordinal=20+j,origin="model",accepted_owners_touched=[owner],deleted_origin_counts={"accepted":1},before_vector=0,after_vector=j+1))
            edits.append(dict(ordinal=30,origin="own",accepted_owners_touched=[],deleted_origin_counts={"typed":1},before_vector=0,after_vector=1))
            sessions.append(dict(session=name,writer=writer,rows=rows))
            folder=tmp_path/"p5"; folder.mkdir(exist_ok=True)
            path=folder/(name+".json.gz"); vp=folder/(name+".npy")
            with gzip.open(path,"wt",encoding="utf8") as stream:
                json.dump(dict(session=name,writer=writer,edits=edits),stream)
            np.save(vp,vectors)
            index.append(dict(session=name,file=path.name,sha256=sha256(path),vectors=vp.name,vectors_sha256=sha256(vp)))
    write(tmp_path/"sessions.json",sessions); write(tmp_path/"PREDICTIONS.json",predictions)
    write(tmp_path/"COMPLETE.json",dict(status="COMPLETE",outputs={"PREDICTIONS.json":sha256(tmp_path/"PREDICTIONS.json")}))
    write(tmp_path/"p5/SESSION_INDEX.json",index); write(tmp_path/"p5/SUMMARY.json",dict(sessions=len(index)))
    write(tmp_path/"p5/COMPLETE.json",dict(status="COMPLETE",outputs={name:sha256(tmp_path/"p5"/name) for name in ("SESSION_INDEX.json","SUMMARY.json")}))
    return dict(sessions=str(tmp_path/"sessions.json"),predictions=str(tmp_path/"PREDICTIONS.json"),prediction_completion=str(tmp_path/"COMPLETE.json"),
                p5_summary=str(tmp_path/"p5/SUMMARY.json"),p5_index=str(tmp_path/"p5/SESSION_INDEX.json"),p5_completion=str(tmp_path/"p5/COMPLETE.json"))


def test_complete_supported_subset_positive_and_saved_recompute(tmp_path):
    inputs=fixture_inputs(tmp_path); config=dict(scope="linked_model_corrections",simulations=1000,seed=20261017,bootstrap=200)
    report=v1.execute(tmp_path/"out",inputs,config)
    assert report["state"]=="positive"
    assert report["donor_control"]["state"]=="positive"
    assert report["audit"]["all_corrections"]==45 and report["audit"]["supported_corrections"]==30
    assert report["audit"]["unsupported_own"]==15 and report["unexplained_correction_rate"]==.5
    assert report["broader_question"].startswith("OPEN")
    assert v1.verify(tmp_path/"out",inputs,config)["verified"]


def test_equal_explained_and_unexplained_directions_return_exact_null():
    units={}
    for writer in "abcd":
        moments=[dict(session="s1",count=2,unit_sum=[2.,0.]),dict(session="s2",count=2,unit_sum=[2.,0.])]
        units[writer]=dict(audit=dict(supported_corrections=8,unexplained=4),moments={"unexplained":moments,"explained":moments})
    report=v1.summarize(units,dict(bootstrap=200,seed=20261017))
    assert report["primary"]["estimate"]==0 and report["state"]=="null"
    assert report["donor_control"]["estimate"]==0
