"""Week 5 channel trigger/intensity instruments on the licensed Crowd-enVENT source.

DESIGN CHECK: LESSONS 2–5, CONTROLS 6–7. Explicit column projection excludes
demographics/personality. Planted signed/null slopes test the actual statistic;
writer resampling preserves all her texts. Reader agreement excludes self pairs.
Prompts are sampling labels, not validated biological channel measurements.
"""
from __future__ import annotations
import hashlib
import hmac
import io
import json
import os
from pathlib import Path
import time
import zipfile
for k in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
    os.environ[k] = "2"
import numpy as np
import pandas as pd

SEED = 20261107
SOURCE_SHA = "61c22527795669a0556df8d7441d3a7bf13ef8b2266b0433881645e92bf885e6"
APPRAISALS = ["suddenness", "familiarity", "predict_event", "pleasantness", "unpleasantness",
              "goal_relevance", "chance_responsblt", "self_responsblt", "other_responsblt",
              "predict_conseq", "goal_support", "urgency", "self_control", "other_control",
              "chance_control", "accept_conseq", "standards", "social_norms", "attention", "not_consider", "effort"]
PROFILES = {
    "fear": {"goal_support": -1, "predict_conseq": 1, "urgency": 1, "self_control": -1},
    "anger": {"other_responsblt": 1, "other_control": 1, "goal_support": -1, "urgency": 1, "self_control": 1},
    "sadness": {"goal_support": -1, "self_control": -1, "accept_conseq": -1},
    "disgust": {"standards": 1, "social_norms": 1, "other_responsblt": 1, "not_consider": 1},
    "joy": {"goal_support": 1, "urgency": -1},
    "boredom": {"familiarity": 1, "attention": -1},
}
CHANNELS = {"fear": "FEAR", "anger": "RAGE", "sadness": "PANIC/GRIEF", "disgust": "DISGUST",
            "joy": "PLAY (partial)", "boredom": "low SEEKING (partial)"}
PRIMARY = ["fear", "anger", "sadness", "disgust"]
STYLE = ["suddenness", "familiarity", "predict_event", "goal_relevance", "chance_responsblt",
         "self_responsblt", "chance_control", "attention", "effort"]
OUTSIDE = [a for a in APPRAISALS if a not in set().union(*(set(p) for p in PROFILES.values()))
           and a not in ("pleasantness", "unpleasantness")]


def digest(path: Path) -> str:
    with path.open("rb") as f: return hashlib.file_digest(f, "sha256").hexdigest()


def write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + f".{os.getpid()}.tmp")
    temp.write_text(json.dumps(value, indent=2, allow_nan=False)+"\n", encoding="utf8")
    for attempt in range(10):
        try: os.replace(temp, path); break
        except PermissionError:
            if attempt == 9: raise
            time.sleep(.02*(attempt+1))


def salted(value: str, salt: bytes, namespace: str) -> str:
    return hmac.new(salt, (namespace+":"+str(value)).encode("utf8"), hashlib.sha256).hexdigest()


def projection(source: Path, salt: bytes) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    if digest(source) != SOURCE_SHA: raise ValueError("Crowd-enVENT archive pin mismatch")
    if len(salt) != 32: raise ValueError("campaign salt must be 32 bytes")
    generation_cols = ["emotion", "text_id", "prolific_id", "generated_text", "intensity", "confidence", "did_you_lie?"]+APPRAISALS
    validation_cols = ["original_emotion", "text_id", "prolific_id", "intensity", "confidence"]+APPRAISALS
    with zipfile.ZipFile(source) as z:
        notice = z.read("LICENSE.txt").decode("utf8")
        if "Creative Commons Attribution 4.0" not in notice: raise ValueError("licence assertion changed")
        # pandas never decodes the excluded demographic/personality columns into a frame.
        with z.open("corpus/crowd-enVent_generation.tsv") as stream:
            gen = pd.read_csv(stream, sep="\t", usecols=generation_cols, dtype={"text_id": str, "prolific_id": str})
        with z.open("corpus/crowd-enVent_validation.tsv") as stream:
            val = pd.read_csv(stream, sep="\t", usecols=validation_cols, dtype={"text_id": str, "prolific_id": str})
    if len(gen) != 6600 or len(val) != 6000: raise ValueError("source row count mismatch")
    lies = gen["did_you_lie?"].eq("I never experienced that event, but I really imagined how it would make me feel.")
    known = gen["did_you_lie?"].isin(["The event really happened in my life.", "--", "I never experienced that event, but I really imagined how it would make me feel."])
    if not known.all(): raise ValueError("unmapped truthfulness answer")
    numeric = ["intensity", "confidence"]+APPRAISALS
    for frame in (gen, val):
        for col in numeric:
            frame[col] = pd.to_numeric(frame[col], errors="raise")
        if not np.isfinite(frame[numeric].to_numpy()).all() or not frame[numeric].isin([1,2,3,4,5]).all().all():
            raise ValueError("appraisal scale is malformed")
        if frame[["text_id", "prolific_id"]].isna().any().any(): raise ValueError("missing private join key")
    if gen["text_id"].duplicated().any(): raise ValueError("duplicate writer text")
    if val[["text_id", "prolific_id"]].duplicated().any(): raise ValueError("repeated reader on text")
    if not val.groupby("text_id").size().eq(5).all() or val.text_id.nunique() != 1200:
        raise ValueError("validation requires 1200 texts with five readers each")
    if not set(val.text_id).issubset(set(gen.text_id)): raise ValueError("unmatched validation text")
    excluded_texts = set(gen.loc[lies, "text_id"])
    report = {"source_rows": {"generation": len(gen), "validation": len(val)}, "invented_events_excluded": int(lies.sum()),
              "truthfulness_not_asked": int(gen["did_you_lie?"].eq("--").sum()),
              "validation_rows_for_excluded_events": int(val.text_id.isin(excluded_texts).sum()),
              "archive_sha256": SOURCE_SHA, "license": "CC BY 4.0", "citation": "doi:10.1162/coli_a_00461",
              "appraisal_columns": APPRAISALS, "demographics_personality_read": False}
    gen = gen.loc[~lies].copy(); val = val.loc[~val.text_id.isin(excluded_texts)].copy()
    gen["word_count"] = gen.generated_text.fillna("").str.split().str.len()
    gen = gen.drop(columns=["generated_text", "did_you_lie?"])
    for frame in (gen,val):
        frame["text_id"] = frame.text_id.map(lambda x: salted(x,salt,"crowd-text"))
        frame["prolific_id"] = frame.prolific_id.map(lambda x: salted(x,salt,"crowd-person"))
    gen = gen.sort_values("text_id").reset_index(drop=True)
    val = val.sort_values(["text_id", "prolific_id"]).reset_index(drop=True)
    report["retained_rows"] = {"generation": len(gen), "validation": len(val)}
    return gen,val,report


def standardize(values: np.ndarray) -> np.ndarray:
    values = np.asarray(values, dtype=float)
    sd = values.std(axis=0, ddof=1)
    return (values-values.mean(axis=0))/np.where(sd>1e-12,sd,1.)


def clustered_fit(x: np.ndarray, y: np.ndarray, clusters: np.ndarray, contrasts: np.ndarray,
                  draws: int = 2000, seed: int = SEED) -> dict:
    x=np.asarray(x,float); y=np.asarray(y,float); contrasts=np.atleast_2d(contrasts)
    if not np.isfinite(x).all() or not np.isfinite(y).all(): raise ValueError("nonfinite design")
    keys, code = np.unique(clusters, return_inverse=True)
    if len(keys)<2: return {"status":"unsupported", "clusters":len(keys), "rows":len(y)}
    xx=np.zeros((len(keys),x.shape[1],x.shape[1])); xy=np.zeros((len(keys),x.shape[1]))
    np.add.at(xx, code, x[:,:,None]*x[:,None,:]); np.add.at(xy,code,x*y[:,None])
    gram=xx.sum(axis=0); rhs=xy.sum(axis=0)
    if np.linalg.matrix_rank(gram,tol=1e-10)<x.shape[1]:
        return {"status":"rank_deficient", "clusters":len(keys), "rows":len(y)}
    beta=np.linalg.solve(gram,rhs); samples=[]; failures=0
    rng=np.random.default_rng(seed)
    for _ in range(draws):
        weight=np.bincount(rng.integers(0,len(keys),len(keys)),minlength=len(keys))
        g=np.einsum("n,nij->ij",weight,xx); r=np.einsum("n,ni->i",weight,xy)
        if np.linalg.matrix_rank(g,tol=1e-10)<x.shape[1]: failures+=1; continue
        samples.append(contrasts@np.linalg.solve(g,r))
    if failures: return {"status":"bootstrap_rank_failure", "failed_draws":failures,"clusters":len(keys),"rows":len(y)}
    b=np.asarray(samples)
    return {"status":"ok", "clusters":len(keys),"rows":len(y), "estimate":(contrasts@beta).tolist(),
            "interval":np.quantile(b,[.025,.975],axis=0).T.tolist(),"draws":draws}


def classify(estimate: float, interval: list[float], bar: float, direction: int=1) -> str:
    lo,hi=sorted(direction*np.array(interval))
    if lo>bar: return "supports"
    if hi<0 or (lo>=-bar and hi<=bar): return "against"
    return "inconclusive"


def in1(frame: pd.DataFrame, config: dict) -> dict:
    frames=[]; exposures={}; variant=config.get("variant","primary")
    for label in config.get("channels", PRIMARY):
        part=frame.loc[frame.emotion.eq(label)].copy(); exposures[label]=len(part)
        if variant=="min10": part=part.loc[part.word_count>=10]
        if len(part)<2: continue
        items=PROFILES[label]; signed=standardize(part[list(items)].to_numpy())*np.array(list(items.values()))
        if variant=="double_first": signed[:,0]*=2
        if variant=="reverse": signed*=-1
        index=standardize(signed.mean(axis=1))
        intensity=(part.intensity>=4).astype(float) if variant=="binary4" else part.intensity.to_numpy()
        y=standardize(intensity)
        valence="pleasantness" if label=="joy" else "unpleasantness"
        controls=standardize(np.column_stack([part[valence],part.confidence,part[STYLE].mean(axis=1)]))
        prompt=np.column_stack([np.full(len(part),float(label==k)) for k in config.get("channels",PRIMARY)])
        x=np.column_stack([prompt,index,controls]); frames.append((x,y,part.prolific_id.to_numpy()))
    if not frames:return {"status":"unsupported","exposure":exposures}
    x=np.concatenate([f[0] for f in frames]);y=np.concatenate([f[1] for f in frames]);ids=np.concatenate([f[2] for f in frames])
    contrast=np.zeros(x.shape[1]);contrast[len(config.get("channels",PRIMARY))]=1
    answer=clustered_fit(x,y,ids,contrast,config.get("draws",2000))
    answer["exposure"]=exposures;answer["variant"]=variant
    if answer["status"]=="ok":
        answer["outcome"]=classify(answer["estimate"][0],answer["interval"][0],.1)
        if answer["clusters"]<20 or (len(config.get("channels",PRIMARY))==1 and len(y)<300):
            answer["outcome"]="below floor, descriptive"
    return answer


def in2(frame: pd.DataFrame, config: dict) -> dict:
    d=frame.loc[frame.emotion.eq("fear")]
    z=standardize(d[["unpleasantness","predict_conseq","urgency","confidence"]].to_numpy())
    interaction=standardize(z[:,0]*z[:,1]);x=np.column_stack([np.ones(len(d)),z,interaction]);c=np.zeros(6);c[-1]=1
    a=clustered_fit(x,standardize(d.intensity.to_numpy()),d.prolific_id.to_numpy(),c,config.get("draws",2000))
    if a["status"]=="ok": a["outcome"]=classify(a["estimate"][0],a["interval"][0],.1)
    a["negative_cannot_separate"]="uncertainty-sensitive FEAR versus stress in a single rating"
    return a


def in3(frame: pd.DataFrame, config: dict) -> dict:
    arrays=[]
    for label in ["fear","anger"]:
        d=frame.loc[frame.emotion.eq(label)];rage=float(label=="anger")
        z=standardize(d[["self_control","unpleasantness"]].to_numpy())
        x=np.column_stack([np.ones(len(d)),np.full(len(d),rage),z[:,0],z[:,0]*rage,z[:,1],z[:,1]*rage])
        arrays.append((x,standardize(d.intensity.to_numpy()),d.prolific_id.to_numpy()))
    x=np.concatenate([a[0] for a in arrays]);y=np.concatenate([a[1] for a in arrays]);ids=np.concatenate([a[2] for a in arrays])
    c=np.array([[0,0,0,1,0,0],[0,0,1,0,0,0],[0,0,1,1,0,0]])
    a=clustered_fit(x,y,ids,c,config.get("draws",2000));a["contrasts"]=["RAGE_minus_FEAR","FEAR","RAGE"]
    if a["status"]=="ok": a["outcome"]=classify(a["estimate"][0],a["interval"][0],.15)
    return a


def agreement_rows(generation: pd.DataFrame, validation: pd.DataFrame) -> pd.DataFrame:
    writers=generation.set_index("text_id"); rows=[]
    for text, reader in validation.groupby("text_id",sort=True):
        writer=writers.loc[text]; label=writer.emotion
        if label not in PROFILES: continue
        values=reader[APPRAISALS].to_numpy(float);target=writer[APPRAISALS].to_numpy(float)
        if len(values)!=5: raise ValueError("incomplete reader set")
        wr=np.abs(values-target).mean(axis=0)
        # Exactly the ten unordered distinct reader pairs; self-pairs are excluded.
        rr=np.mean([np.abs(values[i]-values[j]) for i in range(5) for j in range(i+1,5)],axis=0)
        excess=wr-rr; pi=[APPRAISALS.index(k) for k in PROFILES[label]]; oi=[APPRAISALS.index(k) for k in OUTSIDE]
        rows.append({"text":text,"emotion":label,"word_count":int(writer.word_count),
                     "contrast":float(excess[pi].mean()-excess[oi].mean()),
                     "profile_excess":float(excess[pi].mean()),"outside_excess":float(excess[oi].mean()),
                     **{f"excess_{k}":float(excess[i]) for i,k in enumerate(APPRAISALS)}})
    return pd.DataFrame(rows)


def in4(generation: pd.DataFrame, validation: pd.DataFrame, config: dict) -> dict:
    data=agreement_rows(generation,validation); labels=config.get("channels",PRIMARY)
    data=data.loc[data.emotion.isin(labels)].copy()
    if "length_tercile" in config:
        # Stable rank breaks tied lengths by already sorted hashed text key.
        band=np.minimum(2,(data.word_count.rank(method="first").to_numpy()-1)*3//len(data)).astype(int)
        data=data.loc[band==int(config["length_tercile"])]
    # Saturated prompt intercepts, equal prompt weights, each text one cluster.
    x=np.column_stack([data.emotion.eq(k).astype(float) for k in labels])
    c=np.ones(len(labels))/len(labels)
    a=clustered_fit(x,data.contrast.to_numpy(),data.text.to_numpy(),c,config.get("draws",2000))
    a["outside_profile_columns"]=OUTSIDE;a["channel_counts"]=data.emotion.value_counts().to_dict()
    a["item_excess_for_scale_only"]={k:float(data[f"excess_{k}"].mean()) for k in APPRAISALS}
    if a["status"]=="ok":
        a["outcome"]=classify(a["estimate"][0],a["interval"][0],.1)
        if a["clusters"]<20:a["outcome"]="below floor, descriptive"
    return a


def grid() -> list[dict]:
    rows=[{"cell":card,"phase":card,"draws":2000} for card in ["IN1","IN2","IN3","IN4"]]
    for variant in ["double_first","binary4","min10","reverse"]:
        rows.append({"cell":"IN1."+variant,"phase":"IN1","variant":variant,"draws":200})
    for label in PROFILES:
        rows.append({"cell":"IN1.reverse."+label,"phase":"IN1","variant":"reverse","channels":[label],"draws":200})
    for tercile in range(3):
        rows.append({"cell":f"IN4.length{tercile+1}","phase":"IN4","length_tercile":tercile,"draws":200})
    return rows


def fixture() -> dict:
    rng=np.random.default_rng(31);x=np.column_stack([np.ones(120),rng.normal(size=(120,2))]);ids=np.repeat(np.arange(40),3)
    for sign in [-1,0,1]:
        y=2+sign*.3*x[:,1]+.2*x[:,2]
        fit=clustered_fit(x,y,ids,[0,1,0],draws=30)
        assert fit["status"]=="ok" and abs(fit["estimate"][0]-sign*.3)<1e-10
    assert classify(0.,[0.,0.],.1)=="against"
    assert classify(.3,[.2,.4],.1)=="supports"
    assert classify(.05,[-.05,.15],.1)=="inconclusive"
    g=pd.DataFrame([{**dict.fromkeys(APPRAISALS,3),"text_id":"t","emotion":"fear","word_count":12}])
    v=pd.DataFrame([{**dict.fromkeys(APPRAISALS,i+1),"text_id":"t","prolific_id":str(i)} for i in range(5)])
    result=agreement_rows(g,v)
    assert np.isclose(result.contrast.iloc[0],0)
    assert np.isclose(result.profile_excess.iloc[0],-0.8)
    return {"passed":True,"signed_and_null_OLS":True,"reader_pairs_exclude_self":True,"exact_null_classification":True}


def execute(output: Path, inputs: dict, config: dict) -> dict:
    phase=config.get("phase","prepare");output.mkdir(parents=True,exist_ok=True)
    if phase=="fixture":a=fixture();write_json(output/"FIXTURE.json",a);return a
    if phase=="prepare":
        g,v,a=projection(Path(inputs["source"]),Path(inputs["salt"]).read_bytes())
        g.to_parquet(output/"generation.parquet",index=False);v.to_parquet(output/"validation.parquet",index=False)
        a["generation_sha256"]=digest(output/"generation.parquet");a["validation_sha256"]=digest(output/"validation.parquet")
        write_json(output/"SOURCE.json",a);return a
    g=pd.read_parquet(inputs["generation"])
    if phase=="IN1":
        a=in1(g,config)
        if "channels" not in config and config.get("variant","primary")=="primary":
            a["secondary_channels"]={k:in1(g,{**config,"channels":[k]}) for k in PRIMARY}
    elif phase=="IN2":a=in2(g,config)
    elif phase=="IN3":a=in3(g,config)
    elif phase=="IN4":
        v=pd.read_parquet(inputs["validation"]);a=in4(g,v,config)
        if "channels" not in config and "length_tercile" not in config:
            a["secondary_channels"]={k:in4(g,v,{**config,"channels":[k]}) for k in PRIMARY}
    else:raise ValueError("unknown phase")
    a["card"]=phase;a["scope"]="descriptive, prompted-event self-reports; channel mapping unvalidated biologically"
    write_json(output/"RESULT.json",a);return a


def verify(output: Path, inputs: dict, config: dict) -> dict:
    phase=config.get("phase","prepare")
    if phase=="fixture":
        if fixture()!=json.loads((output/"FIXTURE.json").read_text("utf8")):raise ValueError("fixture mismatch")
    elif phase=="prepare":
        g,v,_=projection(Path(inputs["source"]),Path(inputs["salt"]).read_bytes())
        pd.testing.assert_frame_equal(g,pd.read_parquet(output/"generation.parquet"))
        pd.testing.assert_frame_equal(v,pd.read_parquet(output/"validation.parquet"))
    else:
        g=pd.read_parquet(inputs["generation"])
        fn={"IN1":in1,"IN2":in2,"IN3":in3}
        a=fn[phase](g,config) if phase in fn else in4(g,pd.read_parquet(inputs["validation"]),config)
        if phase=="IN1" and "channels" not in config and config.get("variant","primary")=="primary":
            a["secondary_channels"]={k:in1(g,{**config,"channels":[k]}) for k in PRIMARY}
        if phase=="IN4" and "channels" not in config and "length_tercile" not in config:
            v=pd.read_parquet(inputs["validation"])
            a["secondary_channels"]={k:in4(g,v,{**config,"channels":[k]}) for k in PRIMARY}
        expected=json.loads((output/"RESULT.json").read_text("utf8"))
        for key,value in a.items():
            if value!=expected[key]:raise ValueError("complete analysis replay mismatch")
    return {"verified":True,"phase":phase,"full_replay":True}
