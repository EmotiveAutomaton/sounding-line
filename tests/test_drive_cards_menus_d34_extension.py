import joblib
import numpy as np
import pytest
from sklearn.decomposition import PCA

from runners.drive.cards import menus_d34_extension as extension
from runners.drive.cards.menus_io import read, write, sha256


def fixture_inputs(tmp_path, parent_state="positive", wrong_model=False):
    rng=np.random.default_rng(330); rows=[]; predictions=[]
    for writer in "abc":
        for number in range(3):
            for decision in range(12):
                key=f"{writer}-{number}-{decision}"
                rows.append(dict(key=key,writer=writer,session=f"{writer}{number}",session_time=number))
                predictions.append(dict(key=key,writer=writer,truth="accept" if decision%2 else "dismiss",
                                        probabilities={"content":[.25]*4}))
    n=len(rows); content=rng.normal(scale=.01,size=(n,16)); content[:,0]=[1. if r["truth"]=="accept" else -1. for r in predictions]
    primary=tmp_path/"d34"; primary.mkdir()
    np.savez(primary/"FEATURES.npz",content=content,state=rng.normal(size=(n,3)),reader=rng.normal(size=(n,9)))
    write(primary/"ROWS.json",rows)
    sources={key:"synthetic-source-identity" for key in ("sessions","records","vectors")}
    write(primary/"SUMMARY.json",dict(state=parent_state,positive_control_detections=5,input_hashes=sources,
        intermediate_hashes={name:sha256(primary/name) for name in ("FEATURES.npz","ROWS.json")}))
    write(primary/"COMPLETE.json",dict(status="COMPLETE",outputs={"SUMMARY.json":sha256(primary/"SUMMARY.json")}))
    p4=tmp_path/"p4"; (p4/"primary").mkdir(parents=True)
    base=np.ones((n,1)); scalars=rng.normal(size=(n,2)); embeddings=rng.normal(size=(n,4))
    np.savez(p4/"FEATURES.npz",backbone=base,scalars=scalars,embeddings=embeddings)
    write(p4/"FEATURE_ROWS.json",rows); write(p4/"PREDICTIONS.json",predictions)
    fits=[]
    for writer in "abc":
        projection=PCA(n_components=2).fit(embeddings)
        weights=np.zeros((5,4))
        if wrong_model and writer=="a": weights[0,0]=1.
        model=dict(projection=projection,scalar_mean=np.zeros(4),scalar_sd=np.ones(4),selected_booster=None,logistic_weights=weights)
        path=p4/"primary"/(writer+".joblib"); joblib.dump(model,path)
        fits.append(dict(writer=writer,pca_dimensions=2,test_keys=[r["key"] for r in rows if r["writer"]==writer],model_sha256=sha256(path)))
    write(p4/"FITS.json",fits)
    write(p4/"SUMMARY.json",dict(card="P4",input_hashes=sources,
        intermediate_hashes={name:sha256(p4/name) for name in ("FEATURES.npz","FEATURE_ROWS.json","PREDICTIONS.json","FITS.json")}))
    write(p4/"COMPLETE.json",dict(status="COMPLETE",outputs={"SUMMARY.json":sha256(p4/"SUMMARY.json")}))
    return dict(d34_summary=str(primary/"SUMMARY.json"),d34_completion=str(primary/"COMPLETE.json"),
                p4_summary=str(p4/"SUMMARY.json"),p4_completion=str(p4/"COMPLETE.json"))


def test_actual_saved_p4_design_replay_and_primary_recomputation(tmp_path):
    inputs=fixture_inputs(tmp_path); config=dict(seed=20261017,permutations=1000,bootstrap=200)
    report=extension.execute(tmp_path/"out",inputs,config)
    assert report["conditional_extension"] and report["primary"]["estimate"]>0
    assert extension.verify(tmp_path/"out",inputs,config)["verified"]
    assert report["matched_p4_positive_control_power"].startswith("not established")


def test_changed_augmented_prediction_is_refused_before_scoring(tmp_path):
    inputs=fixture_inputs(tmp_path,wrong_model=True)
    with pytest.raises(ValueError,match="forecast replay differs"):
        extension.execute(tmp_path/"out",inputs,{})
    assert not (tmp_path/"out/SUMMARY.json").exists()


def test_null_parent_cannot_run_extension(tmp_path):
    inputs=fixture_inputs(tmp_path,parent_state="null")
    with pytest.raises(ValueError,match="positive or marginal"):
        extension.execute(tmp_path/"out",inputs,{})
