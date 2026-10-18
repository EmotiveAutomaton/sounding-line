"""D12 rank reliability and paired real-writer permutation-graph bootstrap.

DESIGN CHECK: LESSONS3-5 and original D12 read. Stable rank preferences yield
positive split reliability; reversed halves yield negative reliability; no
variation makes it undefined. Fake edges keep both original writer endpoints:
cross-writer weights are products, same-writer weights count a copy once.
Undefined permutations/replicates never redraw or silently change denominators.
More than5percent undefined bootstrap replicates invalidates that interval.
"""
from collections import Counter
import math
import numpy as np
from . import states_v2 as states


def correlation(x,y,weights=None):
    x,y=np.asarray(x,float),np.asarray(y,float)
    if weights is None:weights=np.ones((1,len(x)))
    w=np.asarray(weights,float);total=w.sum(-1)
    with np.errstate(divide="ignore",invalid="ignore"):
        mx=(w*x).sum(-1)/total;my=(w*y).sum(-1)/total
        dx=x-mx[...,None];dy=y-my[...,None]
        denominator=np.sqrt((w*dx*dx).sum(-1)*(w*dy*dy).sum(-1))
        value=(w*dx*dy).sum(-1)/denominator
    return np.where((total>0)&(denominator>1e-14),np.clip(value,-1,1),np.nan)


def interval(point,draws,config):
    values=np.asarray(draws,float);good=values[np.isfinite(values)];missing=len(values)-len(good)
    valid=np.isfinite(point) and missing<=config["maximum_undefined_fraction"]*len(values) and len(good)>1
    if not valid:return dict(effect=float(point) if np.isfinite(point) else None,ci95=[None,None],standard_error=None,p_approx=None,
        state="invalid",draws=len(values),undefined_draws=missing)
    ci=np.quantile(good,[.025,.975]).tolist();se=float(good.std(ddof=1));point=float(point)
    p=math.erfc(abs(point)/se/math.sqrt(2)) if se else float(point==0.)
    return dict(effect=point,ci95=ci,standard_error=se,p_approx=p,state=states.contrast_state(point,*ci),
                draws=len(values),undefined_draws=missing)


def fake_weights(counts,permutation):
    count=np.asarray(counts,float);p=np.asarray(permutation,int)
    weights=count*count[:,p]
    same=p==np.arange(len(p));weights[:,same]=count[:,same]
    return weights


def controls(observed,values):
    values=np.asarray(values,float);defined=np.isfinite(values)
    if not defined.all() or not np.isfinite(observed):
        return dict(state="invalid",draws=len(values),undefined_draws=int(np.sum(~defined)),
                    p_one_sided=None,mean=None,sd=None,quantiles95=[None,None],biased_pipeline_flag=None)
    mean=float(values.mean());sd=float(values.std(ddof=1))
    return dict(state="valid_reference",draws=len(values),undefined_draws=0,
        p_one_sided=float((1+np.sum(values>=observed))/(len(values)+1)),mean=mean,sd=sd,
        quantiles95=np.quantile(values,[.025,.975]).tolist(),biased_pipeline_flag=abs(mean)>.25*sd)


def summarize(units,config):
    profiles=[];excluded=Counter();unsupported=[];census=Counter()
    for unit in sorted(units,key=lambda u:u["writer"]):
        excluded.update(unit["exclusions"]);halves=[]
        for half in (0,1):
            all_rows=[r for r in unit["rows"] if r["half"]==half];chosen=[r for r in all_rows if r["selected"]]
            halves.append(dict(decisions=len(all_rows),selections=len(chosen),
                rank=float(np.mean([r["centered_rank"] for r in chosen])) if chosen else None,
                uniform=float(np.mean([r["uniform_rank"] for r in chosen])) if chosen else None,
                accept=float(np.mean([r["accepted"] for r in all_rows])) if all_rows else None))
            for r in chosen:
                census["selected"]+=1;census["canonical_choice_changed"]+=r["canonical_choice_changed"]
                for name in ("favorite","least","favorite_tied","least_tied"):census[name]+=r[name]
                if r["size"]==5:
                    census["five_item_selected"]+=1;census["five_item_favorite"]+=r["favorite"];census["five_item_least"]+=r["least"]
        if any(h["rank"] is None for h in halves):unsupported.append(dict(writer=unit["writer"],reason="no eligible choice in one complete-roster session half"))
        else:profiles.append(dict(writer=unit["writer"],halves=halves))
    n=len(profiles)
    if n<config["minimum_writers"]:
        raise ValueError("insufficient supported writers for D12 rank reliability")
    arrays={name:np.asarray([[p["halves"][h][name] for h in (0,1)] for p in profiles]) for name in ("rank","uniform","accept")}
    rng=np.random.default_rng(config["seed"])
    indices=rng.integers(n,size=(config["bootstrap"],n))
    counts=np.zeros((len(indices),n),int)
    for i,index in enumerate(indices):counts[i]=np.bincount(index,minlength=n)
    points={name:float(correlation(v[:,0],v[:,1])[0]) for name,v in arrays.items()}
    draws={name:correlation(v[:,0],v[:,1],counts) for name,v in arrays.items()}
    primary=interval(points["rank"],draws["rank"],config)
    above=interval(points["rank"]-.3,draws["rank"]-.3,config)
    random=np.random.default_rng(config["seed"]);fake_points=[];fake_draws=[];permutations=[]
    for _ in range(config["permutations"]):
        permutation=random.permutation(n);permutations.append(permutation.tolist())
        fake_points.append(float(correlation(arrays["rank"][:,0],arrays["rank"][permutation,1])[0]))
        fake_draws.append(correlation(arrays["rank"][:,0],arrays["rank"][permutation,1],fake_weights(counts,permutation)))
    fake_points=np.asarray(fake_points);fake_draws=np.asarray(fake_draws)
    # A replicate needs all200 fixed graphs; no dropping undefined graphs.
    paired_draws=draws["rank"]-fake_draws.mean(0)
    paired_point=points["rank"]-float(fake_points.mean())
    return dict(primary=primary,state=primary["state"],above_point_three=above,
        accept_reliability=interval(points["accept"],draws["accept"],config),
        uniform_control=interval(points["uniform"],draws["uniform"],config),
        reliability_minus_accept=interval(points["rank"]-points["accept"],draws["rank"]-draws["accept"],config),
        own_minus_fake=interval(paired_point,paired_draws,config),
        writer_label_permutation=dict(**controls(points["rank"],fake_points),
            values=[float(v) if np.isfinite(v) else None for v in fake_points],permutations=permutations,
            bootstrap_undefined_by_graph=np.sum(~np.isfinite(fake_draws),axis=1).tolist()),
        profiles=profiles,writers=n,unsupported_writers=unsupported,excluded=dict(excluded),census=dict(census),
        rank_definition="(ascending average rank-1)/(menu size-1)-.5; higher logged score gives higher centered rank; all-tied menus excluded",
        semantics="unchanged finite raw logged score ranks only; backend probability/logprob semantics remain unknown",
        weighting="equal writers in odd/even correlation, decision-weighted mean ranks within complete-roster session halves",
        pairing="same rows in each fixed even-half writer permutation; real-writer node bootstrap weights distinct endpoints by product and equal endpoints once",
        uncertainty="conditional on200 fixed permutation graphs and source roster; all200 graphs required in each paired bootstrap replicate; no redraw or Spearman-Brown correction")
