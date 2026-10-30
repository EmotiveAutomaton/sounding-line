"""WB1.h1 effects: same windows/contrasts with physical insertion provenance.

DESIGN CHECK: LESSONS 3-5/CONTROLS reread 2026-10-25. Effects are measured
after each occurrence using original source ordinals. Missing full sixty-second
follow-up and no accepted characters are missing support, never zero outcomes.
Classes fit discovery writers only; held-out effect consistency is compared with
200 within-writer piece-label permutations. Reversed/no-effect plants must not
become support. A complete source replay verifies every effect and embedding.
The exact MiniLM revision is inherited from CONTENT_V2; CPU only, <=2 threads.
"""
from __future__ import annotations

from collections import Counter, defaultdict
import hashlib
import json
import re
from pathlib import Path

import numpy as np
from sklearn.cluster import KMeans

from runners.drive.cards import events_p5
from runners.drive.cards import week3_pieces_coverage as coverage
from runners.drive.cards import week3_pieces_input as source
from runners.drive.cards.week3_pieces_input_recovery import checked_clock
from runners.drive.cards.timing_census import read, filehash
from runners.drive.cards.timing_events import source_sessions
from runners.drive.cards.week3_insertion_provenance_h1 import reconstruct
from runners.drive.cards.timing_p6 import write_equal
from runners.stage9.coauthor import units, text_of, delta_ops, apply_delta

EFFECTS = ("net_characters", "sentence_completed", "accepted_retained_share", "prompt_similarity_change")
END_SENTENCE = re.compile(r"[.!?](?:[\"'\u2019\u201d)]*)(?:\s+|$)")


def effect_windows(events, timeline, occurrences):
    """Exact original document states at anchor and last event <=anchor+60s."""
    clocks = checked_clock(events)
    lifetime = reconstruct(events, timeline)["eligible"]
    required = set()
    spans = []
    for occurrence in occurrences:
        at = occurrence["source_ordinal"]
        if not 0 <= at < len(events) or not np.isclose(clocks[at], occurrence["seconds"], atol=1e-7, rtol=0):
            raise ValueError("piece anchor differs from original source")
        target = clocks[at]+60
        end = int(np.searchsorted(clocks, target, side="right"))-1
        required.update((at, end))
        spans.append((at,end,clocks[-1] >= target))
    snapshots, completed = {}, []
    doc = units(events[0]["currentDoc"])
    for ordinal,event in enumerate(events):
        before=text_of(doc)
        ops=delta_ops(event.get("textDelta"))
        if ops:
            doc,_,_=apply_delta(doc,[None]*len(doc),event.get("textDelta"))
        after=text_of(doc)
        if len(END_SENTENCE.findall(after)) > len(END_SENTENCE.findall(before)):
            completed.append(ordinal)
        if ordinal in required:
            snapshots[ordinal]=after
    if text_of(doc)!=timeline["final_document"]:
        raise ValueError("effect replay differs from P2")
    accepted=[d for d in timeline["decisions"] if d["handling"] in {"accept","edit"}]
    results=[]
    for occurrence,(at,end,full) in zip(occurrences,spans):
        menus=[d["ordinal"] for d in accepted if at < d["resolution_ordinal"] <= end]
        original=sum(lifetime[k]["original_utf16"] for k in menus)
        surviving=sum(lifetime[k]["surviving_utf16"] for k in menus)
        results.append(dict(**occurrence, full_followup=full, end_ordinal=end,
            before=snapshots[at],after=snapshots[end],
            net_characters=len(snapshots[end])-len(snapshots[at]) if full else None,
            sentence_completed=int(any(at < i <= end for i in completed)) if full else None,
            accepted_original_utf16=original,accepted_surviving_utf16=surviving,
            accepted_retained_share=surviving/original if full and original else None))
    return results


class FrozenEncoder:
    def __init__(self,path,mode):
        self.mode=mode
        self.encoder=None if mode=="constructed" else events_p5.Encoder(path,2,16)

    def vectors(self,texts,context=False):
        if self.mode=="constructed":
            vectors=np.array([[1+text.lower().count(c) for c in "abcd"] for text in texts],float)
            return vectors/np.linalg.norm(vectors,axis=1,keepdims=True),[dict(truncated=False,constructed=True) for _ in texts]
        trimmed, scopes=[],[]
        tok=self.encoder.tokenizer
        for text in texts:
            encoded=tok(text,add_special_tokens=False,return_offsets_mapping=True,truncation=False)
            n=len(encoded["input_ids"])
            start=max(0,n-254) if context else 0
            # Match CONTENT_V2's context view, including its tokenizer offsets.
            if n > 254 and context:
                text=text[encoded["offset_mapping"][start][0]:]
            trimmed.append(text)
            scopes.append(dict(full_tokens=n,used_tokens=min(n,254),truncated=n>254,token_start=start))
        vectors,_=self.encoder.encode(trimmed)
        return vectors,scopes


def piece_key(symbols):
    return json.dumps(symbols,separators=(",",":"))


def r_squared(values,labels):
    x=np.asarray(values,float)
    if len(x)<2 or not np.isfinite(x).all():
        return None
    total=float(np.square(x-x.mean()).sum())
    if total==0:
        return 0.0
    groups=defaultdict(list)
    for label,value in zip(labels,x):
        groups[label].append(value)
    within=sum(float(np.square(np.asarray(v)-np.mean(v)).sum()) for v in groups.values())
    return float(np.clip(1-within/total,0,1))


def consistency(records,draws=200,seed=source.SEED):
    """Descriptive test-half variance share; labels permuted within real writer."""
    out={}
    for effect in EFFECTS:
        rows=[r for r in records if r["side"]=="test" and r[effect] is not None]
        rows.sort(key=lambda r:(r["writer"],r["session"],r["source_ordinal"],piece_key(r["symbols"])))
        if len(rows)<2 or len({r["writer"] for r in rows})<3:
            out[effect]=dict(state="unsupported",observations=len(rows),reason="fewer than three supported held-out writers")
            continue
        labels=np.array([piece_key(r["symbols"]) for r in rows],object)
        values=[r[effect] for r in rows]
        observed=r_squared(values,labels)
        groups=defaultdict(list)
        for i,row in enumerate(rows):
            groups[row["writer"]].append(i)
        rng=np.random.default_rng(seed)
        bank=[]
        for _ in range(draws):
            shuffled=labels.copy()
            for writer in sorted(groups):
                ix=groups[writer]
                shuffled[ix]=rng.permutation(shuffled[ix])
            bank.append(r_squared(values,shuffled))
        out[effect]=dict(variance_explained=observed,reference_mean=float(np.mean(bank)),
            reference_interval=np.quantile(bank,[.025,.975]).tolist(),
            permutation_p=(1+sum(v>=observed for v in bank))/(draws+1),
            reference_draws=bank,observations=len(rows),writers=len(groups),
            scope="descriptive held-out grouping, not out-of-sample effect prediction")
    return out


def classes(records,seed=source.SEED):
    """Discovery-only piece means; each dimension uses its observed support."""
    discovery=[r for r in records if r["side"]=="discovery"]
    groups=defaultdict(list)
    for row in discovery:
        groups[piece_key(row["symbols"])].append(row)
    means,counts,excluded={}, {}, {}
    for key,rows in sorted(groups.items()):
        present={effect:[r[effect] for r in rows if r[effect] is not None] for effect in EFFECTS}
        counts[key]={k:len(v) for k,v in present.items()}
        if all(present.values()):
            means[key]=[float(np.mean(present[k])) for k in EFFECTS]
        else:
            excluded[key]=[k for k,v in present.items() if not v]
    if not means:
        return dict(state="unsupported",reason="no discovery piece has all four effects observed",support=counts,excluded=excluded,assignments={})
    keys=sorted(means)
    values=np.asarray([means[k] for k in keys])
    center=values.mean(0)
    scale=values.std(0)
    varying=scale>0
    if not np.any(varying):
        labels=np.zeros(len(keys),int)
        centers=np.zeros((1,0))
    else:
        z=(values[:,varying]-center[varying])/scale[varying]
        n=min(10,len(keys),len(np.unique(z,axis=0)))
        fit=KMeans(n_clusters=n,random_state=seed,n_init=10,algorithm="lloyd").fit(z)
        labels,centers=fit.labels_,fit.cluster_centers_
    return dict(state="fitted",training_side="discovery writers only",feature_order=list(EFFECTS),means=means,support=counts,
        excluded=excluded,center=center.tolist(),scale=scale.tolist(),varying_columns=varying.tolist(),
        standardized_centers=centers.tolist(),assignments={k:int(v) for k,v in zip(keys,labels)},seed=seed)


def validate_config(config):
    if set(config)!={"mode","permutation_draws","seed"} or config["mode"] not in {"constructed","corpus"} or config["seed"]!=source.SEED:
        raise ValueError("frozen effect configuration required")
    if type(config["permutation_draws"]) is not int or config["permutation_draws"]<1 or (config["mode"]=="corpus" and config["permutation_draws"]!=200):
        raise ValueError("full effect permutation count required")


def calculate(output,inputs,config,verify=False):
    validate_config(config)
    required={"coverage_complete","coverage_result","source_inputs","content_model","content_complete"}
    if set(inputs)!=required:
        raise ValueError("exact WB1 effect inputs required")
    coverage.authenticated(inputs["coverage_complete"],inputs["coverage_result"])
    cov=read(inputs["coverage_result"])
    if cov.get("status")!="component_complete" or cov.get("full_card_complete") is not False:
        raise ValueError("unrecognized complete coverage component")
    if config["mode"]=="corpus":
        # Historical content receipts predate fresh_process_verified; retain
        # their original completed model hash, then verify every model byte.
        complete=read(inputs["content_complete"])
        model_path=Path(inputs["content_model"]).resolve()
        if complete.get("status")!="COMPLETE" or complete["outputs"].get(model_path.relative_to(Path(inputs["content_complete"]).resolve().parent).as_posix())!=filehash(model_path):
            raise ValueError("CONTENT_V2 model identity not authenticated")
        events_p5.model_identity(model_path)
    source_inputs=read(inputs["source_inputs"])
    if set(source_inputs)!={"repo_root","session_index","foundation_complete","foundation_plan","raw_roster","prepared_sessions"}:
        raise ValueError("source input bundle has wrong shape")
    # Authenticate the sources against the exact preparation consumed by coverage.
    coverage_plan=read(Path(inputs["coverage_complete"]).resolve().parent/"PLAN.json")
    coverage_inputs=coverage_plan["inputs"]
    coverage.authenticated(inputs["coverage_complete"],Path(inputs["coverage_complete"]).resolve().parent/"PLAN.json")
    prep_result=read(coverage_inputs["preparation_result"])
    coverage.authenticated(coverage_inputs["preparation_complete"],coverage_inputs["preparation_result"])
    for key,path in source_inputs.items():
        if key!="repo_root" and prep_result["source_bindings"].get(str(Path(path).resolve()))!=filehash(path):
            raise ValueError("effect source bundle differs from preparation")
    occurrences=defaultdict(list)
    for occurrence in cov["whole"]["occurrences"]:
        occurrences[occurrence["session"]].append(occurrence)
    records=[]
    encoder=None
    for row,timeline,meta in source_sessions(source_inputs,"raw_roster"):
        if row["session"] not in occurrences:
            continue
        raw=Path(source_inputs["repo_root"])/meta["path"]
        events=[json.loads(s) for s in raw.read_text(encoding="utf-8").splitlines()]
        windows=effect_windows(events,timeline,occurrences[row["session"]])
        if encoder is None:
            encoder=FrozenEncoder(inputs["content_model"],config["mode"])
        prompt,pscope=encoder.vectors([timeline["initial_document"]])
        unique=sorted({r[k] for r in windows if r["full_followup"] for k in ("before","after")})
        mapping={}
        if unique:
            vectors,scope=encoder.vectors(unique,context=True)
            mapping={s:(float(v@prompt[0]),sc) for s,v,sc in zip(unique,vectors,scope)}
        for record in windows:
            before,after=record.pop("before"),record.pop("after")
            record["prompt_similarity_change"]=mapping[after][0]-mapping[before][0] if record["full_followup"] else None
            record["embedding_scope"]={"prompt":pscope[0],"before":mapping[before][1],"after":mapping[after][1]} if record["full_followup"] else None
            records.append(record)
    if len(records)!=sum(map(len,occurrences.values())):
        raise ValueError("occurrence session missing from full canonical source")
    records.sort(key=lambda r:(r["session"],r["source_ordinal"],r["start"],r["stop"],piece_key(r["symbols"])))
    result=dict(card="WB1b" if cov["card"]=="WB1b-coverage" else "WB1",status="analysis_complete",full_card_complete=True,
        scientific_admission=config["mode"]=="corpus" and cov["route"]["coverage_gate_passed"],
        constructed=config["mode"]=="constructed",coverage_route=cov["route"],
        effects=consistency(records,config["permutation_draws"],config["seed"]),piece_classes=classes(records,config["seed"]),
        occurrences=len(records),censored_followups=sum(not r["full_followup"] for r in records),
        effect_definitions=dict(net_characters="all-origin Unicode document length change in the next full 60 seconds",
            sentence_completed="any increase in punctuation-bounded sentence endings during the next 60 seconds",
            accepted_retained_share="original accepted UTF-16 units inserted strictly after anchor through +60s that survive at session end; no acceptance means missing",
            prompt_similarity_change="cosine change to initial prompt, pinned MiniLM; last 254 document tokens and first 254 prompt tokens"),
        bindings={k:filehash(v) for k,v in sorted(inputs.items())})
    output=Path(output)
    for name,value in (("WB1_EFFECT_ROWS.json",records),("WB1_RESULT.json",result)):
        if verify:
            if read(output/name)!=value:
                raise ValueError("WB1 effects fail full source replay: "+name)
        else:
            write_equal(output/name,value)
    return result


def execute(output,inputs,config):
    return calculate(output,inputs,config)


def verify(output,inputs,config):
    result=calculate(output,inputs,config,True)
    return dict(verified=True,full_occurrence_replay=True,full_embedding_replay=True,occurrences=result["occurrences"])
