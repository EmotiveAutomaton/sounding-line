"""Source-bound WB1 coverage component; complete card also needs effects.

DESIGN CHECK: LESSONS 3-5, CONTROLS and Week3 WB1 read 2026-10-25.
Conditioning preserves each session's entire transition multiset, initial state
and length, plus time thirds in sensitivity. The null cannot license pieces
merely from menu grammar. Discovery never reads test writers; primary excludes
future-linked edit symbols. A fresh verifier regenerates every null draw rather
than accepting saved reference scores. Completion of this component is not a
full WB1 or downstream scientific admission; effect consistency/classes remain.
"""
from __future__ import annotations

from collections import Counter
import hashlib
import json
import math
from pathlib import Path
import time

import numpy as np

from runners.drive.cards.timing_census import read, filehash
from runners.drive.cards.timing_p6 import gzread, gzwrite, write_equal
from runners.drive.cards import week3_pieces_input as source
from runners.drive.cards import week3_pieces_stats as stats
from runners.stage14.common import atomic


def authenticated(complete_path, path):
    complete_path, path = Path(complete_path).resolve(), Path(path).resolve()
    complete = read(complete_path)
    if complete.get("status") != "COMPLETE" or complete.get("fresh_process_verified") is not True:
        raise ValueError("completed freshly verified event inputs required")
    if complete["outputs"].get(path.relative_to(complete_path.parent).as_posix()) != filehash(path):
        raise ValueError("completed input binding changed")


def load(inputs, config):
    expected={"preparation_complete", "preparation_index", "writer_split", "bin_edges", "preparation_result"}
    if config["coarse"] and config["mode"]=="corpus":
        expected|={"prior_wb1_complete","prior_wb1_result"}
    if set(inputs) != expected:
        raise ValueError("exact completed preparation input set required")
    for key in ("preparation_index","writer_split","bin_edges","preparation_result"):
        authenticated(inputs["preparation_complete"], inputs[key])
    if config["coarse"] and config["mode"]=="corpus":
        authenticated(inputs["prior_wb1_complete"],inputs["prior_wb1_result"])
        prior=read(inputs["prior_wb1_result"])
        if prior.get("full_card_complete") is not True or prior.get("card")!="WB1" or prior["coverage_route"]["next"]!="WB1b":
            raise ValueError("coarser variant lacks the original completed failure route")
    result = read(inputs["preparation_result"])
    if result["schema"] != source.SCHEMA or result["scientific_result"] is not False:
        raise ValueError("unrecognized event preparation schema")
    for path, digest in result["source_bindings"].items():
        if filehash(path) != digest:
            raise ValueError("original event source changed")
    by_digest={digest:path for path,digest in result["source_bindings"].items()}
    split, edges = read(inputs["writer_split"]), read(inputs["bin_edges"])
    if split["seed"] != stats.SEED:
        raise ValueError("writer split seed changed")
    rows = []
    index_path = Path(inputs["preparation_index"]).resolve()
    for item in sorted(read(index_path), key=lambda r:r["session"]):
        path = (index_path.parent/item["file"]).resolve()
        path.relative_to(index_path.parent)
        if filehash(path) != item["sha256"]:
            raise ValueError("prepared session changed")
        row = gzread(path)
        if (row["session"],row["writer"]) != (item["session"],item["writer"]):
            raise ValueError("prepared session identity differs")
        timeline=read(by_digest[row["p2_sha256"]])
        if (timeline["session"],timeline["writer"]) != (row["session"],row["writer"]):
            raise ValueError("time-third session identity differs")
        actions = [a for a in row["actions"] if not (config["coarse"] and a["kind"]=="revision")]
        rows.append(dict(session=row["session"], writer=row["writer"], side=split["writers"][row["writer"]],
            symbols=source.symbols(row["actions"],edges,coarse=config["coarse"]),
            seconds=[a["seconds"] for a in actions], duration=timeline["duration_seconds"],
            source_ordinals=[a["source_ordinals"] for a in actions]))
    if len(rows) != result["sessions"] or len({r["session"] for r in rows}) != len(rows):
        raise ValueError("prepared session census differs")
    if not all(side in {"discovery","test"} for side in (r["side"] for r in rows)):
        raise ValueError("unknown writer split membership")
    return rows


def validate_config(config):
    if set(config) != {"mode","coarse","seed","surrogate_draws","bootstrap_draws","minimum_occurrences","minimum_writers"}:
        raise ValueError("complete frozen WB1 coverage configuration required")
    if config["mode"] not in {"constructed","corpus"} or type(config["coarse"]) is not bool or config["seed"] != stats.SEED:
        raise ValueError("invalid WB1 scope")
    for key in ("surrogate_draws","bootstrap_draws","minimum_occurrences","minimum_writers"):
        if type(config[key]) is not int or config[key] < 1:
            raise ValueError("invalid WB1 fixed counts")
    if config["mode"]=="corpus" and [config[k] for k in ("surrogate_draws","bootstrap_draws","minimum_occurrences","minimum_writers")] != [200,2000,30,10]:
        raise ValueError("corpus WB1 threshold/draw counts changed")


class YieldRequested(Exception):
    pass


def checkpoint(output, name, value, verify):
    path=Path(output)/name
    if path.exists():
        receipt=read(path.with_suffix(".receipt.json"))
        if receipt["sha256"]!=filehash(path) or gzread(path)!=value:
            raise ValueError("reference checkpoint does not reproduce: "+name)
    elif verify:
        raise ValueError("missing complete reference checkpoint")
    else:
        gzwrite(path,value)
        write_equal(path.with_suffix(".receipt.json"),dict(sha256=filehash(path)))


def component(rows, config, thirds, output, verify=False):
    scope="thirds" if thirds else "whole"
    discovery=[r for r in rows if r["side"]=="discovery"]
    test=[r for r in rows if r["side"]=="test"]
    candidate=stats.candidates(discovery,config["minimum_occurrences"],config["minimum_writers"])
    keys=sorted(candidate)
    bank={key:[] for key in keys}
    start=time.monotonic()
    for draw in range(config["surrogate_draws"]):
        counts=Counter()
        for row in discovery:
            seq=stats.surrogate(row["symbols"],row["seconds"],row["duration"],stats.derived_seed(scope,draw,row["session"]),thirds)
            counts.update(piece for piece in stats.ngrams(seq) if piece in candidate)
        values=[counts[key] for key in keys]
        checkpoint(output,f"references/{scope}-discovery-{draw:04d}.json.gz",values,verify)
        for key,value in zip(keys,values):
            bank[key].append(value)
        if not verify:
            atomic(Path(output)/"PROGRESS.json",dict(scope=scope,phase="discovery",draws=draw+1,total=config["surrogate_draws"],wall_seconds=time.monotonic()-start))
            if (Path(output)/"YIELD_REQUEST.json").exists():
                raise YieldRequested("complete discovery draw boundary")
    pieces=stats.discover(candidate,bank)
    primary=[p["symbols"] for p in pieces if p["primary_eligible"]]
    real=[stats.greedy_cover(r["symbols"],primary) for r in test]
    null=np.zeros(len(test),float)
    for draw in range(config["surrogate_draws"]):
        values=[]
        for row in test:
            seq=stats.surrogate(row["symbols"],row["seconds"],row["duration"],stats.derived_seed(scope,draw,row["session"]),thirds)
            values.append(stats.greedy_cover(seq,primary)[0])
        checkpoint(output,f"references/{scope}-test-{draw:04d}.json.gz",values,verify)
        null+=np.asarray(values,float)
        if not verify:
            atomic(Path(output)/"PROGRESS.json",dict(scope=scope,phase="test",draws=draw+1,total=config["surrogate_draws"],wall_seconds=time.monotonic()-start))
            if (Path(output)/"YIELD_REQUEST.json").exists():
                raise YieldRequested("complete test draw boundary")
    null/=config["surrogate_draws"]
    coverage=[dict(session=r["session"],writer=r["writer"],events=len(r["symbols"]),real_covered=a[0],reference_covered=float(b))
              for r,a,b in zip(test,real,null)]
    occurrences=[]
    all_pieces={tuple(p["symbols"]) for p in pieces}
    for row in rows:
        for size in range(3,7):
            for start in range(len(row["symbols"])-size+1):
                piece=tuple(row["symbols"][start:start+size])
                if piece not in all_pieces:
                    continue
                stop=start+size-1
                occurrences.append(dict(session=row["session"],writer=row["writer"],side=row["side"],
                    start=start,stop=stop+1,symbols=list(piece),source_ordinal=row["source_ordinals"][stop][-1],seconds=row["seconds"][stop]))
    return dict(scope=scope,candidates=len(keys),pieces=pieces,primary_pieces=len(primary),
        coverage=stats.coverage_interval(coverage,config["bootstrap_draws"],config["seed"]),
        writer_disjoint=True,reference_draws=config["surrogate_draws"],rows=coverage,occurrences=occurrences)


def run(output,inputs,config,verify=False):
    validate_config(config)
    output=Path(output)
    output.mkdir(parents=True,exist_ok=True)
    rows=load(inputs,config)
    binding=dict(inputs={k:filehash(v) for k,v in sorted(inputs.items())},config=config,
                 source_semantics="exact transition-conditional uniform Euler trails; time thirds preserve every cross-third boundary")
    if verify:
        if read(output/"WB1_COVERAGE_BINDING.json")!=binding:
            raise ValueError("coverage binding changed")
    else:
        write_equal(output/"WB1_COVERAGE_BINDING.json",binding)
    whole=component(rows,config,False,output,verify)
    thirds=component(rows,config,True,output,verify)
    result=dict(card="WB1b-coverage" if config["coarse"] else "WB1-coverage",status="component_complete",scientific_admission=False,
        full_card_complete=False,whole=whole,thirds=thirds,
        route=stats.route(whole["coverage"],thirds["coverage"],whole["primary_pieces"],config["coarse"]),
        effects_and_classes="required separate source-replayed consumer; no downstream launch licensed by this receipt alone")
    if verify:
        if read(output/"WB1_COVERAGE_RESULT.json")!=result:
            raise ValueError("coverage results do not reproduce")
    else:
        write_equal(output/"WB1_COVERAGE_RESULT.json",result)
    return result


def execute(output,inputs,config):
    try:
        return run(output,inputs,config)
    except YieldRequested as exc:
        return dict(status="yielded",reason=str(exc),scientific_admission=False)


def verify(output,inputs,config):
    result=run(output,inputs,config,True)
    return dict(verified=True,full_reference_regeneration=True,full_card_complete=False,
                primary_piece_count=result["whole"]["primary_pieces"])
