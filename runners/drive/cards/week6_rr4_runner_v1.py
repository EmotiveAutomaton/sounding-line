"""RR4/D3. Execute and independently replay the fixed BE late-play comparison."""
from pathlib import Path
from hashlib import sha256
import time

import numpy as np
from threadpoolctl import threadpool_limits

from . import week5_md_analysis as features
from . import week5_rr1 as original
from . import week5_rr3_v1 as check
from . import week6_rr4_v1 as model
from .batch_runtime import filehash, freeze, read
from .week6_es_v2 import preserve_inherited_yield

MODULE = "runners.drive.cards.week6_rr4_runner_v1"
REGISTRATION = "7a7e690731331e6dc247950be7d72cd24d289f8e39630fd21e4382f454226404"


def record(path, payload, compare=False):
    if path.exists():
        previous = read(path)
        if compare:
            check.compare_record(previous, payload)
        elif previous != payload:
            raise ValueError("Recorded D3 support or binding differs")
    else:
        freeze(path, payload)


def settings(inputs, config):
    if set(inputs) != {"source_run", "md3_run", "registration"} or filehash(inputs["registration"]) != REGISTRATION:
        raise ValueError("Original choice inputs and frozen amendment BE are required")
    if set(config) != {"card","draws","max_new_draws","max_wall_seconds"} or config["card"] != "RR4" or config["draws"] != model.DRAWS:
        raise ValueError("Unregistered phone-game model")
    limit,seconds=config["max_new_draws"],config["max_wall_seconds"]
    if type(limit) is not int or not 1 <= limit <= model.DRAWS or type(seconds) not in (int,float) or not 0 < seconds <= 14400:
        raise ValueError("Invalid D3 operational quantum")
    return limit,seconds


def project(bundle,parent,folder,checking):
    people=bundle["person"]
    groups,flow=model.split(people,bundle["counter"],bundle["repeat_eligible"])
    # This durable support record must exist before the first reward or choice is accessed.
    record(folder/"SUPPORT.json",flow)
    roster = sha256()
    for history, training, test in groups:
        for indices in (history, training, [test]):
            roster.update(np.array([len(indices), *indices], dtype="<i8").tobytes())
    record(folder/"SUPPORT.receipt.json", {"counts_sha256":filehash(folder/"SUPPORT.json"),
                                         "split_sha256":roster.hexdigest(),"registration":REGISTRATION})
    if not groups:
        return None,flow,{},None
    plays=bundle["plays"]
    tr,te,train_refs,test_refs=model.reference_rows(groups,plays)
    availability=model.reference_counts(test_refs)
    record(folder/"REFERENCE_SUPPORT.json",availability)
    record(folder/"REFERENCE_SUPPORT.receipt.json", {"counts_sha256":filehash(folder/"REFERENCE_SUPPORT.json"),
                                                    "split_sha256":roster.hexdigest()})
    gamma=float(parent["primary"]["gamma"])
    first=features.dynamic_features(bundle["first"],gamma)
    scale=first.reshape(-1,8).std(axis=0,ddof=1).clip(1e-10)
    del first
    scale[3:5]=float(parent["primary"]["standing_sd"])
    if not np.isfinite(scale).all() or (scale<=0).any():
        raise ValueError("Original first-play reference scale is invalid")
    scores,keep,fits=model.fitted_scores(plays,people,(tr,te),(train_refs,test_refs),gamma,scale,independent=checking)
    record(folder/"FIT_SUPPORT.json",fits)
    return scores,flow,{"reference_support_before_scoring":availability,"training_fits":fits},test_refs[keep]


def checked_bank(folder):
    rows=[]
    for path in sorted(folder.glob("draws-*.json")):
        block=read(path)
        if (path.name!=f"draws-{len(rows):04d}.json" or block["start"]!=len(rows)
                or not 1<=len(block["values"])<=50 or any(len(v)!=6 for v in block["values"])):
            raise ValueError("Noncontiguous player draw bank")
        rows.extend(block["values"])
    if len(rows)>model.DRAWS:
        raise ValueError("Excess player draws")
    return rows


def operation(output,inputs,config,checking):
    limit,seconds=settings(inputs,config)
    output=Path(output)
    if not checking:
        preserve_inherited_yield(output)
    phase=output/("verify" if checking else "execute")
    phase.mkdir(parents=True,exist_ok=True)
    clock=time.monotonic()
    task,parent,identity=original.authenticate({k:inputs[k] for k in ("source_run","md3_run")})
    binding={"registration":REGISTRATION,"source":identity["source_complete"],"task":identity["task"],
             "parent":identity["md3_complete"],"model":filehash(model.__file__),"runner":filehash(__file__)}
    record(phase/"BINDING.json",binding)
    with np.load(task,allow_pickle=False) as bundle, threadpool_limits(limits=2):
        scores,flow,fit_info,refs=project(bundle,parent,phase,checking)
    if checking:
        check.compare_record(read(output/"execute/SUPPORT.json"),flow)
        if fit_info:
            check.compare_record(read(output/"execute/REFERENCE_SUPPORT.json"),fit_info["reference_support_before_scoring"])
            check.compare_record(read(output/"execute/FIT_SUPPORT.json"),fit_info["training_fits"])
    result={"card":"RR4","row":"D3","amendment":"BE","binding":binding,"support":flow,**fit_info,
            "limit":"The test is each player's latest eligible repeat and speaks to late plays. A game score is not anyone's meaning."}
    if scores is None:
        result.update(primary="could not say",draws=0,reason="No eligible common scoring population")
    else:
        delta,differ=model.paired_scores(scores,refs)
        n=len(scores)
        with threadpool_limits(limits=2):
            rows=checked_bank(phase)
            reference=checked_bank(output/"execute") if checking else None
            if checking:
                if len(reference)!=model.DRAWS:raise ValueError("Incomplete execution bank")
                check.compare_record(rows,reference[:len(rows)])
            began_at=len(rows)
            while len(rows)<model.DRAWS:
                if (len(rows)-began_at>=limit or time.monotonic()-clock>=seconds or
                        any((output/k).exists() for k in ("YIELD_REQUEST.json","STOP_REQUEST.json"))):
                    return dict(status="yielded",phase=phase.name,completed=len(rows),total=model.DRAWS,verified=False)
                start=len(rows)
                values=[]
                for j in range(start,min(start+50,began_at+limit,model.DRAWS)):
                    rng=np.random.default_rng(np.random.SeedSequence([model.SEED,j,4]))
                    weights=np.bincount(rng.integers(n,size=n),minlength=n)
                    values.append(model.draw_statistic(delta,differ,weights))
                if checking:check.compare_record(values,reference[start:start+len(values)])
                record(phase/f"draws-{start:04d}.json",{"start":start,"values":values})
                rows.extend(values)
        result.update(model.summarize(scores,refs,rows),draws=model.DRAWS,scored_players=n,
                      resampling="whole held-out players with all models paired; conditional on training fits")
    record(phase/"RESULT.json",result,compare=True)
    if checking:
        check.compare_record(read(output/"execute/RESULT.json"),result)
    return dict(status="verified" if checking else "complete",verified=checking,
                draws=result["draws"],aggregate_sha256=filehash(phase/"RESULT.json"),
                fresh_whole_player_replay=checking)


def execute(output,inputs,config):
    return operation(output,inputs,config,False)


def verify(output,inputs,config):
    return operation(output,inputs,config,True)
