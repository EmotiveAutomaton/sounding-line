"""D35: do early content-correction directions predict later untouched text?

DESIGN CHECK: LESSONS 3-5 reread 2026-10-17. NULL: unrelated correction/text directions give
zero own-minus-donor phase change; permuting writer directions breaks a planted
link. ALTERNATIVE: later text moving along its writer's direction yields a
positive contrast. Odd training sessions, even baseline sessions and the later
half are disjoint, and correction-touched sentences never enter either outcome.
Fewer than four sessions/five training corrections, empty phase support, fewer
than two eligible writers or an unidentified phase contrast are invalid support,
never scientific nulls. Shared states_v2.py maps intervals to campaign states.
The fitted prompt and model-share adjustments are descriptive, not forecasting.
Bootstrap donors exclude every sampled copy of the recipient. A one-distinct-
writer draw has no donor contrast and remains invalid. Checkpoint boundaries
permit forecast/resource yielding without turning interruption into a result.
"""
from __future__ import annotations

import gzip
import json
import math
import time
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

from .events_p5 import filehash, read, write, freeze_or_equal
from . import states_v2 as states


def chronological_partition(sessions):
    ordered = sorted(sessions,key=lambda x:(x["timestamp"],x["session"]))
    half=len(ordered)//2
    return {s["session"]:("direction" if i<half and i%2==0 else "baseline" if i<half else "later")
            for i,s in enumerate(ordered)}


def design_matrix(rows):
    writers=sorted({r["writer"] for r in rows})
    prompts=sorted({r["prompt"] for r in rows})
    if len(writers)<2:
        raise ValueError("fewer than two eligible writers")
    columns=[np.ones(len(rows))]
    columns += [np.array([r["writer"]==w for r in rows],float) for w in writers[1:]]
    columns += [np.array([r["prompt"]==p for r in rows],float) for p in prompts[1:]]
    columns += [np.array([r["model_share"] for r in rows],float)]
    nuisance=np.column_stack(columns)
    phase=np.array([r["phase"] for r in rows],float)
    groups=np.array([writers.index(r["writer"]) for r in rows])
    support=Counter((r["writer"],r["phase"]) for r in rows)
    if any(support[w,p]==0 for w in writers for p in (0,1)):
        raise ValueError("missing writer phase support")
    weights=np.array([1/(2*support[r["writer"],r["phase"]]) for r in rows])
    return nuisance,phase,groups,weights,writers


def adjusted_change(nuisance,phase,outcome,weights):
    """FWL with equal total weight in each writer/phase cell; no rank repair."""
    weights=np.asarray(weights,float)
    if (not np.isfinite(nuisance).all() or not np.isfinite(phase).all()
            or not np.isfinite(outcome).all() or not np.isfinite(weights).all() or np.any(weights<0)):
        raise ValueError("nonfinite or negative regression input")
    root=np.sqrt(weights)
    x=nuisance*root[:,None]
    y=np.column_stack([outcome,phase])*root[:,None]
    coefficients=np.linalg.lstsq(x,y,rcond=1e-10)[0]
    residual=y-x@coefficients
    denominator=residual[:,1]@residual[:,1]
    if denominator<=1e-10:
        raise ValueError("phase is unidentified after covariate adjustment")
    return float((residual[:,0]@residual[:,1])/denominator)


def refit_projection(rows,moments,multiplicity):
    """Refit shared prompt means and donor directions in a writer resample."""
    writers=sorted({r["writer"] for r in rows})
    weight=dict(zip(writers,map(int,multiplicity)))
    by_prompt=defaultdict(lambda:dict(total=None,count=0))
    for c in moments["corrections"]:
        n=weight[c["writer"]]
        if not n:
            continue
        bucket=by_prompt[c["prompt"]]
        value=np.asarray(c["unit_sum"],float)*n
        bucket["total"]=value if bucket["total"] is None else bucket["total"]+value
        bucket["count"]+=c["count"]*n
    means={p:b["total"]/b["count"] for p,b in by_prompt.items()}
    dimensions=len(moments["corrections"][0]["unit_sum"])
    sums={w:np.zeros(dimensions) for w in writers}; counts=Counter()
    for c in moments["corrections"]:
        if c["prompt"] not in means:
            continue
        sums[c["writer"]]+=np.asarray(c["unit_sum"])-c["count"]*means[c["prompt"]]
        counts[c["writer"]]+=c["count"]
    directions={w:sums[w]/counts[w] if counts[w] else sums[w] for w in writers}
    total=sum((weight[w]*directions[w] for w in writers),np.zeros(dimensions))
    count=sum(weight.values())
    if sum(n > 0 for n in weight.values()) < 2:
        raise ValueError("fewer than two distinct sampled writers")
    projected=[]
    for row in rows:
        own=directions[row["writer"]]
        copies=weight[row["writer"]]
        donor=(total-copies*own)/(count-copies)
        projected.append(float(np.asarray(moments["session_means"][row["session"]])@(own-donor)))
    return np.asarray(projected),directions


def primary_from_rows(rows,bootstrap=2000,seed=20261017,moments=None,checkpoint=None,on_tenth=None):
    started=time.monotonic()
    if bootstrap<2:
        raise ValueError("bootstrap needs at least two draws")
    try:
        x,phase,groups,weights,writers=design_matrix(rows)
        outcome=np.array([r["projection_gap"] for r in rows],float)
        if moments is not None:
            reconstructed,_=refit_projection(rows,moments,np.ones(len(writers),int))
            if not np.allclose(outcome,reconstructed,atol=1e-12,rtol=1e-12):
                raise ValueError("saved projection differs from training moments")
            outcome=reconstructed
        point=adjusted_change(x,phase,outcome,weights)
    except ValueError as exc:
        return dict(effect=None,ci95=None,state="invalid",reason=str(exc),sessions=len(rows),bootstrap_draws=bootstrap)
    rng=np.random.default_rng(seed)
    saved=[]
    if checkpoint is not None:
        import hashlib
        checkpoint=Path(checkpoint)
        binding=hashlib.sha256(json.dumps(dict(rows=rows,moments=moments,bootstrap=bootstrap,seed=seed),sort_keys=True,allow_nan=False).encode()).hexdigest()
        paths=sorted(checkpoint.glob('D35_BOOT_*.json'))
        for j,path in enumerate(paths):
            receipt=path.with_suffix('.sha256')
            if path.name!=f'D35_BOOT_{j:05d}.json' or not receipt.exists() or receipt.read_text().strip()!=filehash(path):
                raise ValueError('D35 bootstrap checkpoint hash/sequence changed')
            record=read(path)
            if record['binding']!=binding or record['start']!=len(saved) or len(record['fits'])!=min(100,bootstrap-len(saved)):
                raise ValueError('D35 bootstrap checkpoint binding changed')
            saved.extend(record['fits'])
    retained=len(saved)
    for draw in range(bootstrap):
        multiplicity=np.bincount(rng.integers(len(writers),size=len(writers)),minlength=len(writers))
        if draw<retained:
            continue
        try:
            resampled=refit_projection(rows,moments,multiplicity)[0] if moments is not None else outcome
            saved.append(adjusted_change(x,phase,resampled,weights*multiplicity[groups]))
        except ValueError:
            saved.append(None)
        boundary=(draw+1)%100==0 or draw+1==bootstrap
        if checkpoint is not None and boundary:
            path=checkpoint/f'D35_BOOT_{draw//100:05d}.json'
            write(path,dict(binding=binding,start=(draw//100)*100,fits=saved[(draw//100)*100:]))
            path.with_suffix('.sha256').write_bytes((filehash(path)+'\n').encode('ascii'))
        if on_tenth is not None and draw+1==math.ceil(bootstrap/10):
            on_tenth(dict(primary_seconds=time.monotonic()-started,completed_draws=draw+1,total_draws=bootstrap))
        if checkpoint is not None and boundary and (checkpoint/'YIELD_REQUEST.json').exists():
            return dict(status='yielded',completed_draws=draw+1,total_draws=bootstrap)
    invalid=sum(v is None for v in saved)
    estimates=[v for v in saved if v is not None]
    # Do not silently drop a bootstrap draw whose resample cannot identify phase.
    if invalid:
        return dict(effect=point,ci95=None,state="invalid",bootstrap_invalid=invalid,
                    writers=len(writers),sessions=len(rows),bootstrap_draws=bootstrap)
    low,high=np.quantile(estimates,[.025,.975]).tolist()
    se=float(np.std(estimates,ddof=1))
    z=point/se if se>0 else None
    p=math.erfc(abs(z)/math.sqrt(2)) if z is not None else None
    shuffled=np.array([r["shuffled_projection_gap"] for r in rows],float)
    control=adjusted_change(x,phase,shuffled,weights)
    return dict(effect=point,ci95=[low,high],state=states.contrast_state(point,low,high,expected_direction=1),
                standard_error=se,z=z,p_approx=p,p_method="two-sided normal-reference Wald approximation; descriptive, not permutation p",
                writer_shuffled_direction_effect=control,bootstrap_invalid=0,
                writers=len(writers),sessions=len(rows),bootstrap_draws=bootstrap)


def build_metrics(sessions,seed=20261017,retain_moments=False):
    """Sessions contain saved vectors and source-derived corrections only."""
    by_writer=defaultdict(list)
    for s in sessions:
        by_writer[s["writer"]].append(s)
    corrections=[]
    exclusions=Counter()
    eligible=[]
    selected=[]
    for writer in sorted(by_writer):
        ss=by_writer[writer]
        if len(ss)<4:
            exclusions["fewer_than_four_sessions"]+=1
            continue
        part=chronological_partition(ss)
        training=[(s,e) for s in ss if part[s["session"]]=="direction"
                  for e in s["edits"] if e["split"]=="content" and e["origin"] in ("own","model")]
        if len(training)<5:
            exclusions["fewer_than_five_training_content_corrections"]+=1
            continue
        nonzero=[]
        for s,e in training:
            delta=s["vectors"][e["after_vector"]]-s["vectors"][e["before_vector"]]
            norm=float(np.linalg.norm(delta))
            if norm>1e-12:
                nonzero.append(dict(writer=writer,prompt=s["prompt"],unit=delta/norm))
        if len(nonzero)<5:
            exclusions["fewer_than_five_nonzero_training_corrections"]+=1
            continue
        rows=[]
        for s in sorted(by_writer[writer],key=lambda x:(x["timestamp"],x["session"])):
            phase=part[s["session"]]
            if phase=="direction":
                continue
            sentences=[r for r in s["sentences"] if r["writer_typed"] and not r["content_correction_touched"]]
            if not sentences:
                continue
            rows.append(dict(writer=writer,session=s["session"],prompt=s["prompt"],phase=int(phase=="later"),
                             model_share=s["model_share"],sentences=len(sentences),
                             mean_vector=np.mean([s["vectors"][r["vector"]] for r in sentences],axis=0)))
        if {r["phase"] for r in rows}!={0,1}:
            exclusions["empty_untouched_typed_phase"]+=1
            continue
        eligible.append(writer); selected.extend(rows); corrections.extend(nonzero)
    if len(eligible)<2:
        result=([],dict(exclusions=dict(exclusions),eligible_writers=len(eligible),reason="fewer than two eligible writers"),{})
        return result+({},) if retain_moments else result
    grouped=defaultdict(list)
    for c in corrections:
        grouped[c["writer"],c["prompt"]].append(c["unit"])
    moments=dict(corrections=[dict(writer=w,prompt=p,count=len(values),unit_sum=np.sum(values,axis=0).tolist())
                              for (w,p),values in sorted(grouped.items())],
                 session_means={r["session"]:r["mean_vector"].tolist() for r in selected})
    projected,directions=refit_projection(selected,moments,np.ones(len(eligible),int))
    # Fixed derangement: every shuffled direction comes from a different writer.
    rng=np.random.default_rng(seed)
    order=list(np.asarray(eligible)[rng.permutation(len(eligible))])
    shuffled={w:order[(i+1)%len(order)] for i,w in enumerate(order)}
    direction_sum=sum((directions[w] for w in eligible),np.zeros_like(directions[eligible[0]]))
    rows=[]
    for i,row in enumerate(selected):
        w=row["writer"]; v=row.pop("mean_vector")
        own=directions[w]; donor=(direction_sum-own)/(len(eligible)-1)
        swapped=directions[shuffled[w]]; other=(direction_sum-swapped)/(len(eligible)-1)
        rows.append(dict(**row,own_projection=float(v@own),donor_projection=float(v@donor),
                         projection_gap=float(projected[i]),shuffled_projection_gap=float(v@(swapped-other))))
    result=(rows,dict(exclusions=dict(exclusions),eligible_writers=len(eligible),
                     training_corrections=len(corrections),direction_norms=[float(np.linalg.norm(directions[w])) for w in eligible]),
                     {w:directions[w] for w in eligible})
    return result+(moments,) if retain_moments else result


def load_sessions(inputs):
    if set(inputs)!={"p5_index","p5_summary","p2_index","p5_completion","p2_completion"}:
        raise ValueError("explicit D35 inputs differ")
    for terminal,names in (("p5_completion",("p5_index","p5_summary")),("p2_completion",("p2_index",))):
        complete=Path(inputs[terminal]);record=read(complete)
        if record.get('status')!='COMPLETE':
            raise ValueError('D35 dependency incomplete')
        for name in names:
            source=Path(inputs[name]).resolve()
            if record['outputs'].get(source.relative_to(complete.parent.resolve()).as_posix())!=filehash(source):
                raise ValueError('D35 dependency completion binding changed')
    p5_summary=read(inputs["p5_summary"])
    index=read(inputs["p5_index"])
    if p5_summary["sessions"]!=len(index):
        raise ValueError("P5 is incomplete")
    p2={r["session"]:r for r in read(inputs["p2_index"])}
    if set(p2)!={r["session"] for r in index}:
        raise ValueError("P2/P5 cohort differs")
    pins={str(Path(v)):filehash(v) for v in inputs.values()}
    sessions=[]
    for item in index:
        path=Path(inputs["p5_index"]).parent/item["file"]
        vp=Path(inputs["p5_index"]).parent/item["vectors"]
        timeline_path=Path(inputs["p2_index"]).parent/p2[item["session"]]["file"]
        for source,expected in ((path,item["sha256"]),(vp,item["vectors_sha256"]),(timeline_path,p2[item["session"]]["sha256"])):
            source.resolve().relative_to(Path(inputs['p2_index' if source==timeline_path else 'p5_index']).parent.resolve())
            if filehash(source)!=expected:
                raise ValueError("source changed")
            pins[str(source)]=expected
        with gzip.open(path,"rt",encoding="utf8") as f:
            s=json.load(f)
        vectors=np.load(vp,allow_pickle=False)
        if not np.isfinite(vectors).all():
            raise ValueError("nonfinite saved vectors")
        s["vectors"]=vectors
        spans=read(timeline_path)["final_spans"]
        own=[r for r in spans if r["origin"]!="prompt"]
        denom=sum(r["end_utf16"]-r["start_utf16"] for r in own)
        accepted=sum(r["end_utf16"]-r["start_utf16"] for r in own if r["origin"].startswith("accepted"))
        s["model_share"]=accepted/denom if denom else 0.
        sessions.append(s)
    return sessions,pins


def execute(output: Path,inputs: dict,config: dict)->dict:
    started=time.monotonic()
    output=Path(output)
    if config!={"bootstrap":2000,"seed":20261017}:
        raise ValueError("frozen D35 config differs")
    output.mkdir(parents=True,exist_ok=True)
    if (output/'SUMMARY.json').exists():
        verify(output,inputs,config)
        return read(output/'SUMMARY.json')
    sessions,pins=load_sessions(inputs)
    rows,support,directions,moments=build_metrics(sessions,config["seed"],retain_moments=True)
    for name,value in {'INPUTS.json':dict(paths=inputs,config=config,pins=pins),'SESSION_METRICS.json':rows,
                       'SUPPORT.json':support,'DIRECTIONS.json':{w:v.tolist() for w,v in directions.items()},'TRAINING_MOMENTS.json':moments}.items():
        freeze_or_equal(output/name,value)
    def first_tenth(receipt):
        if (output/'FIRST_TENTH.json').exists():
            return
        elapsed=time.monotonic()-started
        write(output/'FIRST_TENTH.json',dict(card='D35',active_seconds=elapsed,**receipt,
              projected_cpu_seconds=elapsed-receipt['primary_seconds']+receipt['primary_seconds']*10,
              forecast_cpu_seconds=3600))
    primary=primary_from_rows(rows,**config,moments=moments,checkpoint=output,on_tenth=first_tenth) if rows else dict(state="invalid",effect=None,ci95=None,reason=support["reason"])
    if primary.get('status')=='yielded':
        return dict(primary,card='D35',scientific_admission=False)
    result=dict(card="D35",question="Do early content corrections predict the direction of later untouched typed text?",
                primary=primary,support=support,descriptive=True,scientific_admission=False,
                elapsed_seconds=time.monotonic()-started,
                extension_run=False,extension="Rate of corrections aligned above cosine .5, later versus even first-half sessions; direction negative",
                route="Positive opens the frozen extension then texture; null leaves corrections as local fixes at this scale.")
    write(output/"SUMMARY.json",result)
    write(output/"OUTPUT_HASHES.json",{name:filehash(output/name) for name in ("INPUTS.json","SESSION_METRICS.json","SUPPORT.json","DIRECTIONS.json","TRAINING_MOMENTS.json","SUMMARY.json")})
    return result


def verify(output:Path,inputs:dict,config:dict)->dict:
    output=Path(output); binding=read(output/"INPUTS.json")
    if binding["paths"]!=inputs or binding["config"]!=config:
        raise ValueError("verification binding differs")
    for path,expected in binding["pins"].items():
        if filehash(path)!=expected:
            raise ValueError("input changed")
    for name,expected in read(output/"OUTPUT_HASHES.json").items():
        if filehash(output/name)!=expected:
            raise ValueError("output changed")
    rows=read(output/"SESSION_METRICS.json"); result=read(output/"SUMMARY.json")
    sessions,_=load_sessions(inputs)
    rebuilt,support,directions,moments=build_metrics(sessions,config['seed'],retain_moments=True)
    if rebuilt!=rows or support!=read(output/'SUPPORT.json') or moments!=read(output/'TRAINING_MOMENTS.json') or {w:v.tolist() for w,v in directions.items()}!=read(output/'DIRECTIONS.json'):
        raise ValueError('D35 source-derived metrics differ')
    primary=primary_from_rows(rows,**config,moments=read(output/"TRAINING_MOMENTS.json")) if rows else dict(state="invalid",effect=None,ci95=None,reason=read(output/"SUPPORT.json")["reason"])
    if primary!=result["primary"]:
        raise ValueError("primary recomputation differs")
    return dict(verified=True,primary=primary)
