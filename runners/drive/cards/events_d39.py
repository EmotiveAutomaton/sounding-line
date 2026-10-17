"""D39: next-menu examination after model-span versus own-span deletion.

DESIGN CHECK: LESSONS 2-5. NULL: equal next-menu hover counts yield zero paired
writer effect; within-writer source-label shuffling breaks planted differences.
ALTERNATIVE: more hovers after model failures yields a positive contrast. The
80-percent threshold includes equality and counts original Unicode codepoints,
not UTF-16 units or later replacement text. Each accepted span crosses once.
Pure writer deletion runs are maximal adjacent spatially contiguous deletion
deltas; any other event closes the run. A replacement is its own event. No
keypress timing is inferred. Missing matches/next menus and fewer than two
writers are explicit exclusions/invalid support. Shared states_v2.py owns states.
Hover means observed examination behavior, not proof of reading or attention.
The next menu is the first opening strictly after the deletion boundary, within
the same session; an already open menu is never the next-menu outcome.
"""
from __future__ import annotations

import json
import math
import time
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

from runners.stage9.coauthor import units,text_of,delta_ops
from .events_p5 import filehash,read,write,freeze_or_equal
from . import states_v2 as states


def extract_failures(events,timeline,audit=None):
    if not events or events[0]["eventName"]!="system-initialize":
        raise ValueError("initialization required")
    times=[float(e["eventTimestamp"]) for e in events]
    if not all(map(math.isfinite,times)) or times!=sorted(times):
        raise ValueError("invalid source chronology")
    next_atom=0
    def mint(text,kind,origin):
        nonlocal next_atom
        labels=[]
        for char in text:
            labels.extend([(kind,origin,next_atom,char)]*len(units(char)))
            next_atom+=1
        return labels
    doc=units(events[0]["currentDoc"]); owners=mint(events[0]["currentDoc"],"prompt",0)
    current_menu=pending=None
    accepted={}; removed=defaultdict(set); crossed=set(); failures=[]; run=None
    request_at=None
    local_audit=Counter()
    def finish_run():
        nonlocal run
        if run is not None:
            failures.append(dict(kind="own",ordinal=run["ordinal"],seconds=(times[run["ordinal"]]-times[0])/1000,
                deleted_codepoints=len(run["ids"]),deleted_text=run["text"],
                request_gap_seconds=run["request_gap"],source_span_ordinal=run["first_ordinal"],
                deletion_deltas=run["deltas"]))
        run=None
    for ordinal,event in enumerate(events):
        name=event["eventName"]
        if name=="suggestion-get":
            request_at=times[ordinal]
        if name=="suggestion-open":
            current_menu=ordinal
        if name=="suggestion-select":
            pending=current_menu
        value=event.get("textDelta")
        ops=delta_ops(value)
        is_user=event.get("eventSource")=="user"
        deletes=[o for o in ops if o.get("delete",0)]
        inserts=[o for o in ops if o.get("insert","")]
        if not is_user or not deletes or inserts or len(deletes)!=1:
            finish_run()
        if not ops:
            continue
        before=text_of(doc); previous=owners
        kind="typed" if is_user else "accepted" if pending is not None else "api_unknown"
        origin=pending if kind=="accepted" else ordinal
        out=[]; updated=[]; position=0; deleted=[]; inserted=[]; starts=[]
        for op in ops:
            if "insert" in op:
                new=units(op["insert"]); labels=mint(op["insert"],kind,origin)
                out.extend(new);updated.extend(labels);inserted.extend(labels)
            else:
                n=op.get("retain",op.get("delete"))
                if type(n) is not int or n<0 or position+n>len(doc):
                    raise ValueError("invalid UTF-16 boundary")
                if "retain" in op:
                    out.extend(doc[position:position+n]);updated.extend(owners[position:position+n])
                elif n:
                    deleted.extend(owners[position:position+n]);starts.append(position)
                position+=n
        out.extend(doc[position:]);updated.extend(owners[position:])
        doc,owners=out,updated;after=text_of(doc)
        if kind=="accepted":
            if not before.endswith("\n") or not after.startswith(before[:-1]) or not after.endswith("\n"):
                raise ValueError("accepted insertion is not canonical append")
            if len(doc)-len(previous)!=len(inserted):
                raise ValueError("accepted insertion length differs")
            owners=previous[:-1]+inserted+previous[-1:]
            unique={v[2]:v[3] for v in inserted}
            accepted[pending]=dict(ids=set(unique),text="".join(unique.values()))
            local_audit["accepted_spans_tracked"]+=1
            pending=None
        if not is_user or not deleted:
            continue
        local_audit["user_deletion_deltas"]+=1
        request_gap=(times[ordinal]-request_at)/1000 if request_at is not None else None
        by_owner=defaultdict(set)
        for tag,origin,atom,char in deleted:
            if tag=="accepted":
                by_owner[origin].add(atom)
        for origin,atoms in by_owner.items():
            if origin not in accepted:
                raise ValueError("deleted model span has no acceptance")
            removed[origin].update(atoms)
            total=len(accepted[origin]["ids"])
            if total and origin not in crossed and 5*len(removed[origin])>=4*total:
                crossed.add(origin)
                failures.append(dict(kind="model",ordinal=ordinal,seconds=(times[ordinal]-times[0])/1000,
                    source_span_ordinal=origin,deleted_codepoints=len(removed[origin]),
                    original_codepoints=total,deleted_text=accepted[origin]["text"],
                    request_gap_seconds=request_gap,deletion_deltas=None))
        pure=all(v[0]=="typed" for v in deleted)
        if not pure:
            local_audit["not_pure_own_origin_deletion_deltas"]+=1
        if pure and len(deletes)!=1:
            local_audit["noncontiguous_own_deletion_deltas_excluded"]+=1
        if pure and len(deletes)==1:
            unique={v[2]:v[3] for v in deleted}
            chunk="".join(unique.values());start=starts[0]
            if inserts:
                failures.append(dict(kind="own",ordinal=ordinal,seconds=(times[ordinal]-times[0])/1000,
                    deleted_codepoints=len(unique),deleted_text=chunk,request_gap_seconds=request_gap,
                    source_span_ordinal=ordinal,deletion_deltas=1))
            else:
                if run is not None and start not in (run["start"],run["start"]-len(deleted)):
                    finish_run()
                if run is None:
                    run=dict(ordinal=ordinal,first_ordinal=ordinal,ids=set(unique),text=chunk,start=start,
                             deltas=1,request_gap=request_gap)
                else:
                    run["text"]=(chunk+run["text"]) if start<run["start"] else run["text"]+chunk
                    run.update(ordinal=ordinal,start=min(start,run["start"]),deltas=run["deltas"]+1,request_gap=request_gap)
                    run["ids"].update(unique)
        else:
            finish_run()
    finish_run()
    if text_of(doc)!=timeline["final_document"]:
        raise ValueError("P2 final replay differs")
    menus=sorted(timeline["decisions"],key=lambda r:r["ordinal"])
    for row in failures:
        later=[m for m in menus if m["ordinal"]>row["ordinal"]][:5]
        row["next_menus"]=[dict(key=m["key"],ordinal=m["ordinal"],
            hovers=sum(e["event"]=="suggestion-hover" for e in m["interactions"]),
            observed_latency_seconds=m["latency_seconds"] if m["latency_kind"]=="observed_selection_or_close" else None,
            latency_kind=m["latency_kind"],menu_size=m["menu_size"]) for m in later]
    local_audit["accepted_spans_not_crossing_eighty_percent"]+=len(accepted)-len(crossed)
    local_audit["model_failure_events"]+=sum(r["kind"]=="model" for r in failures)
    local_audit["own_failure_runs_or_replacements"]+=sum(r["kind"]=="own" for r in failures)
    local_audit["failures_without_later_menu"]+=sum(not r["next_menus"] for r in failures)
    local_audit["failures_without_prior_request"]+=sum(r["request_gap_seconds"] is None for r in failures)
    if audit is not None:
        audit.update(local_audit)
    return sorted(failures,key=lambda r:(r["ordinal"],r["kind"],r["source_span_ordinal"]))


def match_failures(failures,length_ratio=1.25):
    if length_ratio<1:
        raise ValueError("invalid length caliper")
    valid=[r for r in failures if r["next_menus"] and r["request_gap_seconds"] is not None and r["deleted_codepoints"]>0]
    by_writer=defaultdict(list)
    for row in valid:
        by_writer[row["writer"]].append(row)
    matched=[]; exclusions=Counter()
    exclusions["missing_next_menu_or_request"]=len(failures)-len(valid)
    for writer,rows in sorted(by_writer.items()):
        scale=np.std([[math.log(r["deleted_codepoints"]),math.log1p(r["request_gap_seconds"]),r["session_index"]] for r in rows],axis=0)
        scale=np.where(scale>1e-12,scale,1.)
        controls=[r for r in rows if r["kind"]=="own"]
        for model in sorted((r for r in rows if r["kind"]=="model"),key=lambda r:(r["session_index"],r["ordinal"])):
            candidates=[r for r in controls if 1/length_ratio <= r["deleted_codepoints"]/model["deleted_codepoints"] <= length_ratio]
            if not candidates:
                exclusions["no_length_matched_own_deletion"]+=1
                continue
            def distance(other):
                a=np.array([math.log(model["deleted_codepoints"]),math.log1p(model["request_gap_seconds"]),model["session_index"]])
                b=np.array([math.log(other["deleted_codepoints"]),math.log1p(other["request_gap_seconds"]),other["session_index"]])
                return float(np.sum(((a-b)/scale)**2)),other["session_index"],other["ordinal"]
            own=min(candidates,key=distance)
            matched.append(dict(writer=writer,model_session=model["session"],model_ordinal=model["ordinal"],
                own_session=own["session"],own_ordinal=own["ordinal"],
                hover_difference=model["next_menus"][0]["hovers"]-own["next_menus"][0]["hovers"],
                model_hovers=model["next_menus"][0]["hovers"],own_hovers=own["next_menus"][0]["hovers"],
                length_ratio=own["deleted_codepoints"]/model["deleted_codepoints"],
                request_gap_difference=model["request_gap_seconds"]-own["request_gap_seconds"],
                session_index_difference=model["session_index"]-own["session_index"],match_distance=distance(own)[0]))
    return matched,dict(exclusions)


def paired_primary(matched,bootstrap=2000,seed=20261017):
    by_writer=defaultdict(list)
    for row in matched:
        by_writer[row["writer"]].append(float(row["hover_difference"]))
    means=np.array([np.mean(by_writer[w]) for w in sorted(by_writer)])
    if len(means)<2 or not np.isfinite(means).all():
        return dict(effect=None,ci95=None,state="invalid",reason="fewer than two finite matched writers",writers=len(means),pairs=len(matched))
    rng=np.random.default_rng(seed)
    point=float(means.mean())
    replicates=np.mean(means[rng.integers(len(means),size=(bootstrap,len(means)))],axis=1)
    low,high=np.quantile(replicates,[.025,.975]).tolist()
    se=float(np.std(replicates,ddof=1));z=point/se if se>0 else None
    p=math.erfc(abs(z)/math.sqrt(2)) if z is not None else None
    return dict(effect=point,ci95=[low,high],state=states.contrast_state(point,low,high,expected_direction=1),
                standard_error=se,z=z,p_approx=p,p_method="two-sided normal-reference Wald approximation; descriptive, not permutation p",
                writers=len(means),pairs=len(matched))


def statistics(failures,config):
    matches,exclusions=match_failures(failures,config["length_ratio"])
    primary=paired_primary(matches,config["bootstrap"],config["seed"])
    rng=np.random.default_rng(config["seed"])
    shuffled=[dict(r) for r in failures]
    for writer in sorted({r["writer"] for r in shuffled}):
        ix=[i for i,r in enumerate(shuffled) if r["writer"]==writer]
        labels=rng.permutation([shuffled[i]["kind"] for i in ix])
        for i,label in zip(ix,labels):
            shuffled[i]["kind"]=str(label)
    null_matches,_=match_failures(shuffled,config["length_ratio"])
    # The named writer shuffle asks whether within-person pairing matters. It is
    # not expected to erase a genuinely population-wide source effect.
    shuffled_writers=[dict(r) for r in failures]
    labels=rng.permutation([r["writer"] for r in shuffled_writers])
    for r,label in zip(shuffled_writers,labels):
        r["writer"]=str(label)
    writer_matches,_=match_failures(shuffled_writers,config["length_ratio"])
    result=dict(card="D39",question="Do writers examine the next menu more after deleting model text than their own text?",
        primary=primary,failures=dict(Counter(r["kind"] for r in failures)),exclusions=exclusions,
        controls=dict(within_writer_source_shuffle=paired_primary(null_matches,config["bootstrap"],config["seed"]),
                      writer_shuffle=paired_primary(writer_matches,config["bootstrap"],config["seed"])),
        matching="Within writer, with replacement; length within factor 1.25, nearest standardized log length/log request gap/session index",
        descriptive=True,scientific_admission=False,extension_run=False,
        extension="Difference decay over next five menus; falling direction; saved next-menu series retained",
        route="Positive opens its frozen decay extension and texture; null leaves the hover/trust relation unsupported here.",
        interpretation="Observed menu examination, not verified reading or a causal trust manipulation")
    return result,matches


def execute(output:Path,inputs:dict,config:dict)->dict:
    started=time.monotonic()
    if set(inputs)!={"p2_index","source_roster","source_root","sessions"}:
        raise ValueError("explicit D39 inputs differ")
    if config!={"length_ratio":1.25,"bootstrap":2000,"seed":20261017}:
        raise ValueError("frozen D39 config differs")
    output=Path(output)
    output.mkdir(parents=True,exist_ok=True)
    index=read(inputs["p2_index"]); roster={r["session"]:r for r in read(inputs["source_roster"])}
    sessions=read(inputs["sessions"])
    if {s["session"] for s in sessions}!={r["session"] for r in index}:
        raise ValueError("session cohort differs")
    session_index={}
    for writer in sorted({s["writer"] for s in sessions}):
        ordered=sorted((s for s in sessions if s["writer"]==writer),key=lambda s:(s["timestamp"],s["session"]))
        session_index.update({s["session"]:i for i,s in enumerate(ordered)})
    pins={str(Path(v)):filehash(v) for v in inputs.values() if Path(v).is_file()}
    binding=dict(paths=inputs,config=config,pins=dict(pins))
    if (output/"INPUTS.json").exists():
        if read(output/"INPUTS.json")!=binding:
            raise ValueError("resume inputs/config differ")
        if (output/"SUMMARY.json").exists():
            raise ValueError("completed output is verified, never rerun")
    elif any(output.iterdir()):
        raise ValueError("unbound existing output")
    else:
        write(output/"INPUTS.json",binding)
    failures=[];audit=Counter()
    checkpoints=[];saved_elapsed=0.
    for item in sorted(index,key=lambda r:r["session"]):
        unit_started=time.monotonic()
        meta=roster[item["session"]]
        source=Path(inputs["source_root"])/meta["path"]
        p2path=Path(inputs["p2_index"]).parent/item["file"]
        for path,expected in ((source,meta["source_sha256"]),(p2path,item["sha256"])):
            if filehash(path)!=expected:
                raise ValueError("source changed")
            pins[str(path)]=expected
        relative=f"sessions/{item['session']}.json"
        path=output/relative;receipt=path.with_suffix(".receipt.json")
        if receipt.exists():
            checkpoint=read(receipt)
            if (checkpoint["source_sha256"]!=meta["source_sha256"] or checkpoint["p2_sha256"]!=item["sha256"]
                    or filehash(path)!=checkpoint["sha256"]):
                raise ValueError("checkpoint source/content changed")
            saved=read(path)
        else:
            with source.open(encoding="utf8") as f:
                events=[json.loads(line) for line in f]
            local_audit=Counter()
            rows=[dict(**row,writer=item["writer"],session=item["session"],session_index=session_index[item["session"]])
                  for row in extract_failures(events,read(p2path),local_audit)]
            saved=dict(failures=rows,audit=dict(local_audit))
            if path.exists():
                retained=path.with_name(path.name+".incomplete")
                if retained.exists():
                    raise ValueError("second incomplete unit is not retried")
                path.rename(retained)
            write(path,saved)
            checkpoint=dict(file=relative,sha256=filehash(path),source_sha256=meta["source_sha256"],
                            p2_sha256=item["sha256"],elapsed_seconds=time.monotonic()-unit_started)
            write(receipt,checkpoint)
        failures.extend(saved["failures"]);audit.update(saved["audit"])
        saved_elapsed+=checkpoint["elapsed_seconds"];checkpoints.append(checkpoint)
        if len(checkpoints)==max(1,math.ceil(.1*len(index))) and not (output/"FIRST_TENTH.json").exists():
            write(output/"FIRST_TENTH.json",dict(sessions=len(checkpoints),elapsed_seconds=saved_elapsed,
                projected_seconds=saved_elapsed*len(index)/len(checkpoints),forecast_cpu_seconds=3600))
        if (output/"YIELD_REQUEST.json").exists():
            return dict(status="yielded",sessions_saved=len(checkpoints),sessions_total=len(index),scientific_admission=False)
    result,matches=statistics(failures,config)
    result["extraction_audit"]=dict(audit)
    result["elapsed_seconds_this_invocation"]=time.monotonic()-started
    result["source_checkpoint_elapsed_seconds"]=saved_elapsed
    freeze_or_equal(output/"SOURCE_PINS.json",pins);freeze_or_equal(output/"SESSION_INDEX.json",checkpoints)
    freeze_or_equal(output/"FAILURES.json",failures);freeze_or_equal(output/"MATCHES.json",matches);freeze_or_equal(output/"EXTRACTION_AUDIT.json",dict(audit));write(output/"SUMMARY.json",result)
    write(output/"OUTPUT_HASHES.json",{name:filehash(output/name) for name in ("INPUTS.json","SOURCE_PINS.json","SESSION_INDEX.json","FAILURES.json","MATCHES.json","EXTRACTION_AUDIT.json","SUMMARY.json")})
    return result


def verify(output:Path,inputs:dict,config:dict)->dict:
    output=Path(output); binding=read(output/"INPUTS.json")
    if binding["paths"]!=inputs or binding["config"]!=config:
        raise ValueError("verification binding differs")
    for path,expected in read(output/"SOURCE_PINS.json").items():
        if filehash(path)!=expected:
            raise ValueError("input changed")
    for name,expected in read(output/"OUTPUT_HASHES.json").items():
        if filehash(output/name)!=expected:
            raise ValueError("output changed")
    for checkpoint in read(output/"SESSION_INDEX.json"):
        if filehash(output/checkpoint["file"])!=checkpoint["sha256"]:
            raise ValueError("checkpoint changed")
    result,matches=statistics(read(output/"FAILURES.json"),config)
    result["extraction_audit"]=read(output/"EXTRACTION_AUDIT.json")
    saved=read(output/"SUMMARY.json")
    for key in ("elapsed_seconds_this_invocation","source_checkpoint_elapsed_seconds"):
        result[key]=saved[key]
    if result!=saved or matches!=read(output/"MATCHES.json"):
        raise ValueError("saved primary/matches differ")
    return dict(verified=True,primary=result["primary"])
