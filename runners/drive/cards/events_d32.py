"""D32: offered branches outside a writer's earlier typed repertoire.

DESIGN CHECK: LESSONS 2-5. NULL: repertoire labels independent of acceptances
give zero adjusted log odds; planted negative log odds must be recovered with
the declared sign. Repertoire uses strictly ended earlier sessions; no target
session or later sentence can enter its writer history. A cluster needs ten
other typed writers. Failed convergence, absent contrast support and fewer than
two eligible writers are invalid, not scientific nulls. Shared states_v2.py owns
the direction-aware interval bands. The writer bootstrap refits the binomial
model and leave-writer-out cluster appeal, conditional on the unsupervised
clustering and source-defined repertoire labels. Specifications k=20/100 and
within-writer label/outcome shuffles retain their own separate results.
"""
from __future__ import annotations

import gzip
import json
import math
import time
from collections import Counter,defaultdict
from pathlib import Path

import numpy as np
from scipy.optimize import minimize
from scipy.special import expit,logit

from .events_p5 import read,write,freeze_or_equal,filehash
from . import states_v2 as states


def checkpoint_read(path):
    path=Path(path);hashpath=path.with_name(path.name+".sha256")
    if not hashpath.exists() or filehash(path)!=hashpath.read_text(encoding="ascii").strip():
        raise ValueError("checkpoint hash mismatch")
    return read(path)


def checkpoint_write(path,value):
    path=Path(path);hashpath=path.with_name(path.name+".sha256")
    if path.exists() and hashpath.exists():
        if checkpoint_read(path)!=value:
            raise ValueError("checkpoint value differs")
        return
    if path.exists():
        incomplete=path.with_name(path.name+".incomplete")
        if incomplete.exists():
            raise ValueError("second incomplete checkpoint not retried")
        path.rename(incomplete)
    write(path,value)
    with hashpath.open("x",encoding="ascii",newline="\n") as f:
        f.write(filehash(path)+"\n")


def repertoire_flags(session_meta,typed_clusters,offered_clusters,minimum_others=10):
    """Inputs are independent of handling labels; future own text is forbidden."""
    if minimum_others<1:
        raise ValueError("positive support count required")
    cluster_writers=defaultdict(set)
    for session,clusters in typed_clusters.items():
        for c in set(clusters):
            cluster_writers[int(c)].add(session_meta[session]["writer"])
    result={}
    for session in sorted(offered_clusters):
        current=session_meta[session]
        earlier=[s for s,m in session_meta.items() if m["writer"]==current["writer"] and m["end_at"]<current["timestamp"] and s!=session]
        own=set(c for s in earlier for c in typed_clusters.get(s,[]))
        result[session]=[dict(cluster=int(c),in_repertoire=int(c) in own,
            other_typed_writers=len(cluster_writers[int(c)]-{current["writer"]}),
            eligible=int(c) in own or len(cluster_writers[int(c)]-{current["writer"]})>=minimum_others,
            outside=int(c) not in own) for c in offered_clusters[session]]
    return result


def selected_option(row):
    """Original selected text must uniquely match the frozen displayed menu."""
    if row["handling"] not in ("accept","edit"):
        return None
    matches=[i for i,text in enumerate(row["menu"]) if text==row["inserted"]]
    if len(matches)!=1:
        raise ValueError("selected option text is absent or ambiguous")
    return matches[0]


def prepare_arrays(rows):
    if not rows:
        raise ValueError("empty eligible suggestion support")
    writers=sorted({r["writer"] for r in rows})
    if len(writers)<2:
        raise ValueError("fewer than two eligible writers")
    groups=np.array([writers.index(r["writer"]) for r in rows],int)
    clusters=np.array([r["cluster"] for r in rows],int)
    y=np.array([r["accepted"] for r in rows],float)
    outside=np.array([r["outside"] for r in rows],float)
    if not set(np.unique(y))<={0.,1.} or len(np.unique(y))<2 or len(np.unique(outside))<2:
        raise ValueError("outcome or repertoire contrast lacks support")
    positions=sorted({r["position"] for r in rows})
    numeric=np.array([[math.log1p(r["length"]),r["menu_dissimilarity"],r["session_index"]] for r in rows],float)
    mean=numeric.mean(0);std=numeric.std(0);std=np.where(std>0,std,1.)
    numeric=(numeric-mean)/std
    # Leave-writer-out appeal occupies column 2 and is replaced on each fit.
    x=np.column_stack([np.ones(len(rows)),outside,np.zeros(len(rows)),numeric,
        *[groups==i for i in range(1,len(writers))],
        *[np.array([r["position"]==p for r in rows]) for p in positions[1:]]]).astype(float)
    if not np.isfinite(x).all():
        raise ValueError("nonfinite covariates")
    return dict(x=x,y=y,groups=groups,clusters=clusters,writers=writers,
                numeric_mean=mean.tolist(),numeric_scale=std.tolist(),position_levels=positions)


def appeal_covariate(y,groups,clusters,multiplicity,prior=.5):
    """Exclude every resampled copy of the target writer's outcomes."""
    n_w=len(multiplicity); n_c=int(clusters.max())+1
    offers=np.zeros((n_w,n_c)); accepts=np.zeros_like(offers)
    np.add.at(offers,(groups,clusters),1.)
    np.add.at(accepts,(groups,clusters),y)
    total_offer=multiplicity@offers;total_accept=multiplicity@accepts
    copies=multiplicity[groups]
    numer=total_accept[clusters]-copies*accepts[groups,clusters]+prior
    denom=total_offer[clusters]-copies*offers[groups,clusters]+2*prior
    # Absent writers have zero fit weight; keep their unused design rows finite.
    active=multiplicity[groups]>0
    rates=np.full(len(y),.5)
    rates[active]=numer[active]/denom[active]
    if np.any(rates[active]<=0) or np.any(rates[active]>=1):
        raise ValueError("invalid leave-writer-out appeal")
    return logit(rates)


def logistic_fit(x,y,weights,initial=None):
    weights=np.asarray(weights,float)
    if not np.isfinite(x).all() or not np.isfinite(y).all() or not np.isfinite(weights).all() or np.any(weights<0) or weights.sum()<=0:
        raise ValueError("invalid weighted logistic input")
    weights=weights/weights.sum()
    if np.sum(weights*y)<=0 or np.sum(weights*(1-y))<=0:
        raise ValueError("resampled outcome lacks support")
    def objective(beta):
        eta=x@beta
        value=float(weights@(np.logaddexp(0,eta)-y*eta))
        gradient=x.T@(weights*(expit(eta)-y))
        return value,gradient
    initial=np.zeros(x.shape[1]) if initial is None else np.asarray(initial,float)
    fit=minimize(objective,initial,jac=True,method="L-BFGS-B",
                 options=dict(maxiter=1000,ftol=1e-14,gtol=1e-8,maxls=40))
    loss,gradient=objective(fit.x)
    gradient_gap=float(np.max(np.abs(gradient)))
    if (not fit.success or not np.isfinite(fit.x).all() or gradient_gap>1e-6
            or float(np.max(np.abs(fit.x)))>100):
        raise ValueError("logit lacks a finite convergence certificate")
    return fit.x,dict(gradient_max=gradient_gap,iterations=int(fit.nit),loss=loss)


def fitted_contrast(arrays,multiplicity=None,initial=None,y=None,outside=None):
    y=arrays["y"] if y is None else np.asarray(y,float)
    if multiplicity is None:
        multiplicity=np.ones(len(arrays["writers"]),int)
    x=arrays["x"].copy()
    if outside is not None:
        x[:,1]=outside
    x[:,2]=appeal_covariate(y,arrays["groups"],arrays["clusters"],multiplicity)
    beta,certificate=logistic_fit(x,y,multiplicity[arrays["groups"]],initial)
    return float(beta[1]),beta,certificate


def summarize_bootstrap(point,draws,invalid=0):
    if invalid or not len(draws):
        return dict(effect=point,ci95=None,state="invalid",bootstrap_invalid=int(invalid),reason="one or more bootstrap fits failed")
    a=np.asarray(draws,float)
    low,high=np.quantile(a,[.025,.975]).tolist()
    se=float(np.std(a,ddof=1));z=point/se if se>0 else None
    return dict(effect=point,ci95=[low,high],standard_error=se,z=z,
                p_approx=math.erfc(abs(z)/math.sqrt(2)) if z is not None else None,
                p_method="two-sided normal-reference Wald approximation; descriptive, not permutation p",
                state=states.contrast_state(point,low,high,expected_direction=-1),bootstrap_invalid=0)


def within_writer_shuffle(values,groups,seed):
    rng=np.random.default_rng(seed);out=np.array(values,copy=True)
    for group in sorted(set(groups)):
        mask=np.flatnonzero(groups==group);out[mask]=rng.permutation(out[mask])
    return out


def load_source(inputs):
    p5=read(inputs["p5_index"]);summary=read(inputs["p5_summary"])
    if summary["sessions"]!=len(p5) or read(inputs["p5_inputs"])["sha256"]["content_model"]!=filehash(inputs["content_model"]):
        raise ValueError("P5 incomplete or different encoder")
    sessions=read(inputs["sessions"]);meta={s["session"]:s for s in sessions}
    if len(meta)!=len(sessions) or set(meta)!={r["session"] for r in p5}:
        raise ValueError("P5/session cohort differs")
    pins={str(Path(p)):filehash(p) for p in inputs.values()}
    typed=[];typed_sessions=[];exclusions=Counter()
    for item in sorted(p5,key=lambda r:r["session"]):
        root=Path(inputs["p5_index"]).parent
        for name,key in (("file","sha256"),("vectors","vectors_sha256")):
            path=root/item[name]
            if filehash(path)!=item[key]:
                raise ValueError("P5 session changed")
            pins[str(path)]=item[key]
        with gzip.open(root/item["file"],"rt",encoding="utf8") as f:
            record=json.load(f)
        if record["writer"]!=meta[item["session"]]["writer"]:
            raise ValueError("writer join differs")
        vectors=np.load(root/item["vectors"],allow_pickle=False)
        for row in record["sentences"]:
            if row["writer_typed"]:
                typed.append(vectors[row["vector"]]);typed_sessions.append(item["session"])
            else:
                exclusions["mixed_prompt_or_api_sentences"]+=1
    vectors=np.load(inputs["content_vectors"],allow_pickle=False,mmap_mode="r")
    content=read(inputs["content_records"])
    lookup={r["key"]:r for r in content}
    if len(lookup)!=len(content):
        raise ValueError("duplicate CONTENT_V2 decision")
    session_number={}
    for writer in sorted({s["writer"] for s in sessions}):
        ordered=sorted((s for s in sessions if s["writer"]==writer),key=lambda s:(s["timestamp"],s["session"]))
        session_number.update({s["session"]:i for i,s in enumerate(ordered)})
    offers=[];offer_vectors=[]
    seen=set()
    for s in sorted(sessions,key=lambda r:r["session"]):
        for row in s["rows"]:
            if row["key"] not in lookup or row["key"] in seen:
                raise ValueError("CONTENT_V2 decision coverage differs")
            seen.add(row["key"]);encoded=lookup[row["key"]]
            if len(encoded["options"])!=len(row["menu"]):
                raise ValueError("candidate coverage differs")
            try:
                chosen=selected_option(row)
            except ValueError:
                exclusions["ambiguous_selected_option_menus"]+=1
                continue
            vs=vectors[encoded["options"]]
            gram=vs@vs.T
            upper=np.triu_indices(len(vs),1)
            dissimilarity=float(np.mean(1-gram[upper])) if len(vs)>1 else 0.
            for slot,text in enumerate(row["menu"]):
                offers.append(dict(writer=s["writer"],session=s["session"],session_index=session_number[s["session"]],
                                   key=row["key"],position=slot,length=len(text),menu_dissimilarity=dissimilarity,accepted=int(slot==chosen)))
                offer_vectors.append(vs[slot])
    if seen!=set(lookup):
        raise ValueError("CONTENT_V2 contains unjoined decisions")
    typed=np.asarray(typed,float);offered=np.asarray(offer_vectors,float)
    if typed.ndim!=2 or offered.ndim!=2 or typed.shape[1]!=offered.shape[1] or not np.isfinite(typed).all() or not np.isfinite(offered).all():
        raise ValueError("invalid embedding source")
    return dict(typed=typed,typed_sessions=typed_sessions,offers=offers,offered=offered,meta=meta,pins=pins,exclusions=dict(exclusions))


def cluster_rows(source,k,seed):
    from sklearn.cluster import KMeans
    if len(source["typed"])<k:
        raise ValueError("fewer typed sentences than frozen clusters")
    fit=KMeans(n_clusters=k,random_state=seed,n_init=10,max_iter=300,algorithm="lloyd")
    labels=fit.fit_predict(source["typed"])
    if len(np.unique(labels))!=k:
        raise ValueError("fewer distinct realized clusters than requested")
    offered=fit.predict(source["offered"])
    typed=defaultdict(list);menus=defaultdict(list)
    for session,cluster in zip(source["typed_sessions"],labels):
        typed[session].append(int(cluster))
    for row,cluster in zip(source["offers"],offered):
        menus[row["session"]].append(int(cluster))
    flags=repertoire_flags(source["meta"],typed,menus)
    cursor=Counter();rows=[];excluded=0
    for row in source["offers"]:
        session=row["session"];flag=flags[session][cursor[session]];cursor[session]+=1
        if not flag["eligible"]:
            excluded+=1
            continue
        rows.append(dict(**row,cluster=flag["cluster"],outside=int(flag["outside"]),other_typed_writers=flag["other_typed_writers"]))
    return rows,fit.cluster_centers_,dict(clusters=k,inertia=float(fit.inertia_),iterations=int(fit.n_iter_),
        offered_rows=len(source["offers"]),eligible_rows=len(rows),excluded_rare_outside_options=excluded,
        in_repertoire=sum(not r["outside"] for r in rows),out_of_repertoire=sum(r["outside"] for r in rows))


def run_arm(output,rows,config,name,mode="main",started=None):
    """Checkpoint exact deterministic bootstrap blocks; no redraw on resume."""
    output=Path(output);output.mkdir(parents=True,exist_ok=True)
    try:
        arrays=prepare_arrays(rows)
    except ValueError as exc:
        result=dict(effect=None,ci95=None,state="invalid",reason=str(exc),mode=mode,rows=len(rows))
        checkpoint_write(output/"SUMMARY.json",result)
        return result
    y=arrays["y"];outside=arrays["x"][:,1]
    if mode=="outcome_shuffle":
        y=within_writer_shuffle(y,arrays["groups"],config["seed"]+2)
    elif mode=="repertoire_shuffle":
        outside=within_writer_shuffle(outside,arrays["groups"],config["seed"]+1)
    elif mode!="main":
        raise ValueError("unknown arm")
    try:
        point,beta,certificate=fitted_contrast(arrays,y=y,outside=outside)
    except ValueError as exc:
        result=dict(effect=None,ci95=None,state="invalid",reason=str(exc),mode=mode,rows=len(rows))
        checkpoint_write(output/"SUMMARY.json",result)
        return result
    point_record=dict(effect=point,beta=beta.tolist(),certificate=certificate,writers=len(arrays["writers"]),rows=len(rows))
    checkpoint_write(output/"FIT.json",point_record)
    rng=np.random.default_rng(config["seed"])
    selections=rng.integers(len(arrays["writers"]),size=(config["bootstrap"],len(arrays["writers"])))
    draws=[];invalid=0;elapsed=0.
    for start in range(0,config["bootstrap"],100):
        path=output/f"BOOTSTRAP_{start:04d}.json"
        if path.exists() and path.with_name(path.name+".sha256").exists():
            block=checkpoint_read(path)
        else:
            clock=time.monotonic();estimates=[];failures=[]
            for i in range(start,min(start+100,config["bootstrap"])):
                m=np.bincount(selections[i],minlength=len(arrays["writers"]))
                try:
                    estimate,_,_=fitted_contrast(arrays,m,beta,y=y,outside=outside)
                    estimates.append(estimate)
                except ValueError as exc:
                    estimates.append(None);failures.append(dict(draw=i,reason=str(exc)))
            block=dict(start=start,estimates=estimates,failures=failures,elapsed_seconds=time.monotonic()-clock)
            checkpoint_write(path,block)
        if block["start"]!=start or len(block["estimates"])!=min(100,config["bootstrap"]-start):
            raise ValueError("bootstrap checkpoint coverage differs")
        if [r["draw"] for r in block["failures"]] != [start+i for i,v in enumerate(block["estimates"]) if v is None]:
            raise ValueError("bootstrap failure ledger differs")
        draws.extend(v for v in block["estimates"] if v is not None);invalid+=len(block["failures"]);elapsed+=block["elapsed_seconds"]
        done=start+len(block["estimates"])
        if name=="k50" and done==200 and not (output.parent/"FIRST_TENTH.json").exists():
            total_elapsed=(time.monotonic()-started) if started is not None else elapsed
            write(output.parent/"FIRST_TENTH.json",dict(bootstrap_fits=done,elapsed_seconds=elapsed,
                projected_seconds=max(elapsed*config["bootstrap"]/done*5,total_elapsed*10),forecast_cpu_seconds=3600,
                projection_scope="larger of five bootstrap-arm projection and ten times measured setup-plus-first-tenth"))
        if (output.parent/"YIELD_REQUEST.json").exists():
            return dict(status="yielded",arm=name,bootstrap_saved=done)
    result=summarize_bootstrap(point,draws,invalid)
    result.update(writers=len(arrays["writers"]),rows=len(rows),certificate=certificate,mode=mode)
    checkpoint_write(output/"SUMMARY.json",result)
    return result


def execute(output:Path,inputs:dict,config:dict)->dict:
    if set(inputs)!={"p5_index","p5_summary","p5_inputs","content_records","content_vectors","content_model","sessions"}:
        raise ValueError("explicit D32 inputs differ")
    if config!={"bootstrap":2000,"seed":20261017,"clusters":[50,20,100]}:
        raise ValueError("frozen D32 config differs")
    output=Path(output);output.mkdir(parents=True,exist_ok=True);started=time.monotonic()
    binding=dict(paths=inputs,config=config,pins={str(Path(p)):filehash(p) for p in inputs.values()})
    if (output/"INPUTS.json").exists():
        if read(output/"INPUTS.json")!=binding:
            raise ValueError("resume binding differs")
        if (output/"SUMMARY.json").exists():
            raise ValueError("completed output is verified, never rerun")
    elif any(output.iterdir()):
        raise ValueError("unbound existing output")
    else:
        write(output/"INPUTS.json",binding)
    if (output/"SOURCE_PINS.json").exists():
        for path,expected in read(output/"SOURCE_PINS.json").items():
            if filehash(path)!=expected:
                raise ValueError("resume source changed")
    source=None;results={};support={}
    for k in config["clusters"]:
        path=output/f"ROWS_k{k}.json"
        cluster_files=[path,output/f"CENTERS_k{k}.json",output/f"SUPPORT_k{k}.json"]
        if all(p.exists() and p.with_name(p.name+".sha256").exists() for p in cluster_files):
            rows=checkpoint_read(path);support[str(k)]=checkpoint_read(output/f"SUPPORT_k{k}.json")
            checkpoint_read(output/f"CENTERS_k{k}.json")
        else:
            if source is None:
                source=load_source(inputs)
                freeze_or_equal(output/"SOURCE_PINS.json",source["pins"])
                freeze_or_equal(output/"SOURCE_EXCLUSIONS.json",source["exclusions"])
            rows,centers,census=cluster_rows(source,k,config["seed"])
            checkpoint_write(path,rows);checkpoint_write(output/f"CENTERS_k{k}.json",centers.tolist());checkpoint_write(output/f"SUPPORT_k{k}.json",census)
            support[str(k)]=census
        arms=[(f"k{k}","main")]+([("repertoire_shuffle","repertoire_shuffle"),("outcome_shuffle","outcome_shuffle")] if k==50 else [])
        for name,mode in arms:
            result=run_arm(output/name,rows,config,name,mode,started)
            if result.get("status")=="yielded":
                return result
            results[name]=result
    result=dict(card="D32",question="Are offered branches absent from earlier typed text less likely to be accepted?",
        primary=results["k50"],specifications={k:results[k] for k in ("k20","k100")},
        controls={k:results[k] for k in ("repertoire_shuffle","outcome_shuffle")},support=support,
        source_exclusions=read(output/"SOURCE_EXCLUSIONS.json"),elapsed_seconds_this_invocation=time.monotonic()-started,
        descriptive=True,scientific_admission=False,extension_run=False,
        extension="Examination split among declined out-of-repertoire offers, including keyboard/default exposure audit",
        route="Negative-direction support leaves absent branches unexplained until the frozen examination extension distinguishes unseen from declined.")
    write(output/"SUMMARY.json",result)
    write(output/"OUTPUT_HASHES.json",{p.relative_to(output).as_posix():filehash(p) for p in output.rglob("*") if p.is_file() and p.name not in ("YIELD_REQUEST.json","OUTPUT_HASHES.json")})
    return result


def verify(output:Path,inputs:dict,config:dict)->dict:
    output=Path(output);binding=read(output/"INPUTS.json")
    if binding["paths"]!=inputs or binding["config"]!=config:
        raise ValueError("verification binding differs")
    for path,expected in read(output/"SOURCE_PINS.json").items():
        if filehash(path)!=expected:
            raise ValueError("source changed")
    for path,expected in read(output/"OUTPUT_HASHES.json").items():
        if filehash(output/path)!=expected:
            raise ValueError("output changed")
    rows=read(output/"ROWS_k50.json")
    saved=read(output/"SUMMARY.json")["primary"]
    if saved["effect"] is None:
        try:
            fitted_contrast(prepare_arrays(rows))
        except ValueError as exc:
            if str(exc)!=saved["reason"]:
                raise ValueError("invalid primary reason changed") from exc
            return dict(verified=True,primary=saved)
        raise ValueError("retained invalid primary unexpectedly fits")
    arrays=prepare_arrays(rows)
    point,_,certificate=fitted_contrast(arrays)
    if not math.isclose(point,saved["effect"],rel_tol=1e-10,abs_tol=1e-10):
        raise ValueError("primary fit does not reproduce")
    draws=[];invalid=0
    for start in range(0,config["bootstrap"],100):
        block=read(output/"k50"/f"BOOTSTRAP_{start:04d}.json")
        draws.extend(x for x in block["estimates"] if x is not None);invalid+=len(block["failures"])
    rebuilt=summarize_bootstrap(point,draws,invalid)
    if any(rebuilt[k]!=saved[k] for k in rebuilt):
        raise ValueError("primary interval/state does not reproduce")
    return dict(verified=True,primary=rebuilt,certificate=certificate)
