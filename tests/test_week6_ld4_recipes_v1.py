"""Constructed, original-format and direct-row checks for the LD4 recipe analysis."""
import hashlib

import numpy as np
import pandas as pd
import pytest

from runners.drive.cards import week6_ld4_panel_v1 as panel
from runners.drive.cards import week6_ld4_recipes_v1 as recipe
from runners.drive.cards import week6_ld_draws_v1 as draws
from runners.drive.cards.week6_lattice_bindings_v1 import form_l


def guard():
    return None


def artificial(member="0057", seed=71, people=24, rows=7):
    rng = np.random.default_rng(seed)
    words = panel.feeling_names(member)
    anchors, other = recipe.anchors_and_others(member)
    mix = rng.normal(size=(len(other),len(anchors)))
    weights = np.array([np.eye(len(anchors))[anchors.index(w)] if w in anchors else mix[other.index(w)] for w in words])
    contexts = {}
    for name,features in panel.features(member).items():
        units = np.repeat(np.arange(people),rows)
        x = rng.normal(size=(len(units),len(features)))
        basis = np.linalg.qr(rng.normal(size=(len(features),len(anchors))))[0]
        y = x @ basis @ weights.T + rng.normal(size=(people,len(words)))[units]
        contexts[name] = units,x,y
    return contexts


def build(data, member="0057", reference=False):
    n = max(int(np.max(ids)) for ids,_,_ in data.values())+1
    return panel.prepare_arrays(member,n,data,{},guard,reference=reference)


def test_known_recipes_and_rival():
    rng = np.random.default_rng(108)
    anchors,other = recipe.anchors_and_others("0057")
    words = panel.feeling_names("0057")
    mix = rng.normal(size=(len(other),len(anchors)))
    for dim in (8,14):
        basis = np.linalg.qr(rng.normal(size=(dim,5)))[0].T
        coeff = np.vstack([basis[anchors.index(w)] if w in anchors else mix[other.index(w)] @ basis for w in words])
        for reference in (False,True):
            cond,weights = recipe.fit_recipe(coeff,"0057",reference=reference)
            assert cond==pytest.approx(1)
            np.testing.assert_allclose(weights,mix,atol=1e-12)
    assert recipe.agreement(mix,mix)==pytest.approx(1)
    assert recipe.agreement(mix,-mix)==pytest.approx(-1)


def test_anchors_excluded_and_four_anchor_sample():
    for m,counts in (("0057",(5,9)),("0056",(4,8))):
        a,o=recipe.anchors_and_others(m)
        assert not set(a)&set(o)
        assert (len(a),len(o))==counts
    assert "excluded" not in recipe.anchors_and_others("0056")[1]


def test_rank_loss_and_flat_correlation():
    assert recipe.fit_recipe(np.ones((14,8)),"0057")== (None,None)
    assert recipe.agreement(np.ones((9,5)),np.ones((9,5))) is None
    w = np.ones((9,5));w[2,0]=np.nan
    assert recipe.agreement(w,w) is None


def test_known_sanity_contrasts():
    anchors,other=recipe.anchors_and_others("0057")
    w=np.zeros((9,5))
    for word,a,delta in (("resentful","angry",.7),("insecure","ashamed",.4),("insecure","anxious",.2),("excluded","lonely",.6)):
        w[other.index(word),anchors.index(a)]=delta
    assert recipe.sanity(w,"0057")==pytest.approx({"resentful_angry_above_others":.7,"insecure_anxious_above_angry":.2,"insecure_ashamed_above_angry":.4,"excluded_lonely_above_others":.6})


def test_masked_rows_match_literal_weighted_form_l():
    data=artificial()
    ids,x,y=data["interaction"]
    y[::8,0]=np.nan
    x[::23,0]=np.nan
    masses=np.tile([2,0,1],8)
    for ref in (False,True):
        prepared=build(data,reference=ref)
        observed=panel.coefficient_table(prepared.groups["interaction"],masses,x.shape[1],y.shape[1],ref)
        for j in (0,1,10):
            use=np.isfinite(y[:,j])&np.isfinite(x).all(axis=1)&(masses[ids]>0)
            expected=form_l(ids[use],x[use],{"y":y[use,j]},masses[ids[use]])["y"]
            np.testing.assert_allclose(observed[j],expected,rtol=1e-8,atol=1e-10)
        assert prepared.metadata["support"]["interaction"]["proud"]["rows"]<prepared.metadata["support"]["interaction"]["success"]["rows"]


def test_two_fits_use_the_same_full_roster():
    data=artificial()
    a=build(data)
    b=build(data,reference=True)
    ids=np.arange(a.people)
    weights=draws.person_draw(ids,source_seed=draws.SOURCE_SEEDS["0057"],draw=16)
    x=panel.evaluate(a,weights,guard)
    y=panel.evaluate(b,weights,guard,verify=True)
    assert set(x)==set(y) and len([k for k in x if k.startswith("interaction/recipe/")])==45
    draws.compare(list(x.values()),[y[k] for k in x])
    assert x["cross_context"]>.95
    with pytest.raises(ValueError,match="whole-person"):
        panel.evaluate(a,np.ones(a.people,dtype=int)*2,guard)


def test_unreadable_context_preserves_the_other():
    data=artificial()
    names=panel.feeling_names("0057")
    y=data["interaction"][2]
    y[:,names.index("anxious")]=y[:,names.index("angry")]
    d=build(data)
    observed=panel.evaluate(d,None,guard)
    assert observed["cross_context"] is None
    assert all(v is None for k,v in observed.items() if k.startswith("interaction/recipe/"))
    assert all(v is not None for k,v in observed.items() if k.startswith("solitary/recipe/"))
    assert observed["interaction/singular/01"]>0


def test_missing_mixed_word_preserves_other_weights():
    data=artificial()
    data["interaction"][2][:,0]=np.nan
    d=build(data)
    r=panel.evaluate(d,None,guard)
    assert r["cross_context"] is None and r["interaction/noise"] is None
    assert r["interaction/recipe/proud/angry"] is None
    assert r["interaction/recipe/success/angry"] is not None


def test_registered_boundaries_and_noise():
    keys=["cross_context"]
    for ctx in recipe.CONTEXTS:
        keys.extend([ctx+"/condition",ctx+"/noise",ctx+"/singular/01",ctx+"/singular/02"])
    raw={key:{"estimate":value,"interval":[.31,.8]} for key,value in zip(keys,[.60,14.99,0.,.8,.2,14.99,0.,.8,.2])}
    rows=[[.55,15.1,.2,.81,.21,14.0,.2,.79,.19] for _ in range(2000)]
    result={"member":"0057","metrics":raw}
    assert recipe.summarize(result,rows,keys)["registered_reading"]=="meets the registered agreement bar"
    assert result["context_checks"]["interaction"]["directions"]==1
    assert result["context_checks"]["interaction"]["draws_at_or_above_15_or_singular"]==2000
    raw["cross_context"]["interval"]=[.30,.80]
    assert recipe.summarize(result,rows,keys)["registered_reading"].startswith("does not")
    raw["interaction/condition"]["estimate"]=15
    assert recipe.summarize(result,rows,keys)["registered_reading"]=="unreadable anchor system"
    result["member"]="0056"
    assert recipe.summarize(result,rows,keys)["registered_reading"]=="descriptive four-anchor sample"


def test_original_format_only_registered_columns(tmp_path):
    m="0056";fs=panel.features(m);words=panel.feeling_names(m);rng=np.random.default_rng(700)
    n=160
    ids=np.repeat(np.arange(20),8).astype(str)
    df=pd.DataFrame({"id":ids,"interaction":np.tile(["1","2"],n//2)})
    for col in (*fs["interaction"],*fs["solitary"],*("int_"+w for w in words),*("occup_"+w for w in words)):
        df[col]=rng.integers(1,7,n)
    df["unused_private_field"]="does not parse as a rating"
    df.loc[0,"interaction"]="NA"
    df.loc[1,"id"]="NA"
    path=tmp_path/"invented.tsv";df.to_csv(path,sep="\t",index=False)
    pin=dict(bytes=path.stat().st_size,sha256=hashlib.sha256(path.read_bytes()).hexdigest())
    d=panel.prepare(m,path,pin,["NA",""],guard)
    assert d.people==20 and d.metadata["source"]["missing_id"]==1 and d.metadata["source"]["missing_context"]==1
    assert d.metadata["weight_pairs"]==32 and len(fs["interaction"])==12
    with pytest.raises(ValueError,match="pin"):
        panel.prepare(m,path,{**pin,"sha256":"0"*64},["NA",""],guard)
    df.loc[4,"beh_reserved"]=7
    df.to_csv(path,sep="\t",index=False)
    with pytest.raises(ValueError,match="rating"):
        panel.prepare(m,path,dict(bytes=path.stat().st_size,sha256=hashlib.sha256(path.read_bytes()).hexdigest()),["NA",""],guard)
