"""Separate D3 source-provenance recovery; all original sources stay frozen.

DESIGN CHECK: repeated/empty API transforms absent from P2 are skipped only
when error-free canonical replay proves that exact menu unusable for the observed
repeated-selection reason and its first insertion verified. Every document edit and
UTF16 boundary still replays. Eligible accepted spans retain exact original
survival, deletion, internal-insertion counts and mandatory unique identity.
The raw excluded insertion ledger remains complete, including repeated appends.
"""
from __future__ import annotations
import hashlib
import json
import math
import time
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

from . import timing_events as original
from .timing_census import read, filehash
from .timing_stats import bind, check_binding
from runners.stage9.coauthor import units, text_of, delta_ops, apply_delta, replay as canonical_replay
from runners.stage14.common import atomic, freeze

EXTRA_INPUTS = {"failed_plan", "failed_record"}
FORECAST_SECONDS = 600

def accepted_lifetimes(events, timeline):
    if not events or events[0]["eventName"] != "system-initialize":
        raise ValueError("D3 initialization required")
    doc = units(events[0]["currentDoc"])
    owners = [None] * len(doc)
    current, pending = None, None
    original, deleted, inserted = Counter(), defaultdict(set), Counter()
    accepted = {r["ordinal"] for r in timeline["decisions"] if r["handling"] in {"accept", "edit"}}
    canonical, exclusions = None, []
    for ordinal, event in enumerate(events):
        if event["eventName"] == "suggestion-open":
            current = ordinal
        if event["eventName"] == "suggestion-select":
            pending = current
        ops = delta_ops(event.get("textDelta"))
        if not ops:
            continue
        is_user = event.get("eventSource") == "user"
        position, next_owners = 0, []
        for op in ops:
            if "delete" in op:
                if is_user:
                    for identity in owners[position:position + op["delete"]]:
                        if identity is not None and identity[1] is not None:
                            deleted[identity[0]].add(identity[1])
                position += op["delete"]
            elif "retain" in op:
                next_owners.extend(owners[position:position + op["retain"]])
                position += op["retain"]
            else:
                inside = is_user and 0 < position < len(doc) and owners[position - 1] is not None and owners[position] is not None and owners[position - 1][0] == owners[position][0]
                if inside:
                    inserted[owners[position][0]] += len(units(op["insert"]))
                next_owners.extend([(owners[position][0], None) if inside else None] * len(units(op["insert"])))
        next_owners.extend(owners[position:])
        before, old_owners = text_of(doc), owners
        doc, owners, _ = apply_delta(doc, owners, event.get("textDelta"), insertion_owner=None)
        owners = next_owners
        if not is_user and pending is not None:
            after = text_of(doc)
            if not before.endswith("\n") or not after.startswith(before[:-1]) or not after.endswith("\n"):
                raise ValueError("accepted insertion is not canonical append")
            extra = len(doc) - len(old_owners)
            if pending in accepted:
                if extra <= 0 or original[pending]:
                    raise ValueError("empty/repeated eligible accepted span")
                original[pending] = extra
                owners = old_owners[:-1] + [(pending, i) for i in range(extra)] + old_owners[-1:]
            else:
                if canonical is None:
                    checked = canonical_replay(events)
                    if checked["errors"] or not checked["reconstructed"] or checked["final_document"] != timeline["final_document"]:
                        raise ValueError("excluded menu canonical reconstruction differs")
                    canonical = {d["ordinal"]: d for d in checked["events"]}
                decision = canonical.get(pending)
                if (decision is None or decision["usable"] or decision["verified_insertion"] is not True
                        or decision["exclusion"] != "selection has no active undecided set" or extra < 0):
                    raise ValueError("omitted accepted span lacks canonical exclusion")
                # Preserve the complete transform without giving an excluded
                # API span an eligible accepted-marker identity.
                owners = old_owners[:-1] + [None] * extra + old_owners[-1:]
                exclusions.append(dict(menu_ordinal=pending, insertion_ordinal=ordinal,
                    inserted_utf16=extra, reason=decision["exclusion"]))
            pending = None
    surviving = Counter(identity[0] for identity in owners if identity is not None and identity[1] is not None)
    if text_of(doc) != timeline["final_document"]:
        raise ValueError("D3 final document differs from authenticated P2 replay")
    if set(original) != accepted:
        raise ValueError("eligible P2 accepted-span coverage differs")
    spans = {ordinal: dict(original_utf16=n, surviving_utf16=surviving[ordinal], deleted_original_utf16=len(deleted[ordinal]),
                          inserted_inside_utf16=inserted[ordinal],
                          reversed=surviving[ordinal] == 0 or len(deleted[ordinal]) + inserted[ordinal] >= n / 2)
            for ordinal, n in original.items()}
    return spans, exclusions


def source_units(inputs):
    for index, timeline, meta in original.source_sessions(inputs,"raw_roster"):
        path = Path(inputs["repo_root"])/meta["path"]
        events = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
        spans, excluded = accepted_lifetimes(events,timeline)
        unit = []
        for decision in timeline["decisions"]:
            if decision["handling"] not in {"accept","edit"}:continue
            if (decision["latency_kind"] != "observed_selection_or_close" or decision["ordinal"] not in spans
                    or not math.isfinite(decision["latency_seconds"]) or decision["latency_seconds"] < 0):
                raise ValueError("eligible accepted decision lacks observed latency/span")
            unit.append(dict(session=index["session"],writer=index["writer"],ordinal=decision["ordinal"],
                             latency=decision["latency_seconds"],**spans[decision["ordinal"]]))
        yield index, unit, [dict(session=index["session"],**r) for r in excluded]


def extract_rows(inputs, output=None, elapsed=None, charged_prior=0.):
    rows, exclusions = [], []
    total = len(read(inputs["session_index"]))
    for done, (index, unit, excluded) in enumerate(source_units(inputs),1):
        rows.extend(unit); exclusions.extend(excluded)
        if output is not None:
            checkpoint = Path(output)/"sessions"/(hashlib.sha256(index["session"].encode()).hexdigest()+".json")
            freeze(checkpoint,dict(session=index["session"],source_sha256=index["sha256"],rows=unit))
            freeze(checkpoint.with_suffix(".receipt.json"),dict(sha256=filehash(checkpoint)))
            active=elapsed();atomic(Path(output)/"EVENT_PROGRESS.json",dict(completed_sessions=done,total_sessions=total,active_seconds=active))
            if done==math.ceil(total/10) and not (Path(output)/"FIRST_TENTH.json").exists():
                projection=charged_prior+2*(active-charged_prior)*total/done+30
                freeze(Path(output)/"FIRST_TENTH.json",dict(completed_sessions=done,total_sessions=total,elapsed_seconds=active,
                    charged_prior_seconds=charged_prior,projected_cpu_seconds=projection,forecast_cpu_seconds=FORECAST_SECONDS,includes_fresh_source_replay=True))
                if projection>2*FORECAST_SECONDS:atomic(Path(output)/"YIELD_REQUEST.json",dict(reason="first_tenth_projection_exceeds_twice_forecast"))
            if active>3*FORECAST_SECONDS:raise RuntimeError("D3 recovery cumulative cap exceeded")
            if (Path(output)/"YIELD_REQUEST.json").exists():raise original.CooperativeYield("saved source-authenticated session")
    return rows, exclusions


def failure_identity(inputs,config,legacy,stem):
    source={k:v for k,v in inputs.items() if k not in EXTRA_INPUTS}
    if set(inputs)!=set(source)|EXTRA_INPUTS:raise ValueError("exact recovery inputs required")
    if stem=="EVENT":
        original.validate_config(config)
        if config["card"]!="D3" or set(source)!={"session_index","foundation_complete","foundation_plan","repo_root","raw_roster"}:
            raise ValueError("only exact D3 source recovery supported")
    elif stem=="CONTENT":
        if config!=legacy.CONFIG or set(config)!=set(legacy.CONFIG) or any(type(config[k]) is not type(v) for k,v in legacy.CONFIG.items()) or set(source)!=legacy.INPUTS:
            raise ValueError("exact D3 content recovery configuration required")
    else:raise ValueError("unknown recovery source")
    plan_path,failed_path=Path(inputs["failed_plan"]),Path(inputs["failed_record"])
    if plan_path.name!="PLAN.json" or failed_path!=plan_path.parent/"FAILED.json":raise ValueError("failure identity paths differ")
    plan,failed=read(plan_path),read(failed_path)
    if plan["module"]!=legacy.__name__ or plan["config"]!=config or plan["inputs"]!=source:
        raise ValueError("original failed source/config differs")
    if failed.get("status")!="FAILED" or failed.get("engineering_retry_available") is not True:
        raise ValueError("single engineering recovery unavailable")
    for path,expected in plan["pins"].items():
        if filehash(path)!=expected:raise ValueError("original source pin changed")
    old=plan_path.parent/"output"
    expected=dict(config=config,source_sha256=filehash(legacy.__file__),
        inputs={k:str(Path(v).resolve()) if Path(v).is_dir() else filehash(v) for k,v in source.items()})
    if read(old/f"{stem}_RUN_BINDINGS.json")!=expected:raise ValueError("original run binding changed")
    progress=read(old/f"{stem}_PROGRESS.json") if (old/f"{stem}_PROGRESS.json").exists() else dict(active_seconds=0.,completed_sessions=0)
    saved={}
    for path in sorted((old/"sessions").glob("*.json")):
        if path.name.endswith(".receipt.json"):continue
        if stem=="CONTENT":raise ValueError("this content recovery expects pre-checkpoint original failure")
        receipt=path.with_suffix(".receipt.json")
        if read(receipt)["sha256"]!=filehash(path):raise ValueError("original session checkpoint changed")
        for item in (path,receipt):saved[item.relative_to(old).as_posix()]=filehash(item)
    if stem=="EVENT" and len(saved)!=2*progress["completed_sessions"]:raise ValueError("original checkpoint coverage differs")
    prior=max(progress["active_seconds"],(datetime.fromisoformat(failed["at"])-datetime.fromisoformat(plan["at"])).total_seconds())
    if not math.isfinite(prior) or not 0<=prior<3*FORECAST_SECONDS:raise ValueError("original cumulative allowance unavailable")
    identity=dict(plan_sha256=filehash(plan_path),failure_sha256=filehash(failed_path),
        run_binding_sha256=filehash(old/f"{stem}_RUN_BINDINGS.json"),retained_files=saved,
        progress_sha256=filehash(old/f"{stem}_PROGRESS.json") if (old/f"{stem}_PROGRESS.json").exists() else None,
        charged_prior_seconds=prior,cumulative_cap_seconds=3*FORECAST_SECONDS)
    return source,old,identity


def restore(output,old,identity):
    freeze(Path(output)/"RECOVERY_SOURCE.json",identity)
    for name,expected in identity["retained_files"].items():
        path=Path(output)/name
        if path.exists():
            if filehash(path)!=expected:raise ValueError("retained original checkpoint bytes differ")
        else:
            path.parent.mkdir(parents=True,exist_ok=True)
            with path.open("xb") as stream:stream.write((old/name).read_bytes())


def execute(output:Path,inputs:dict,config:dict)->dict:
    output=Path(output);started=time.monotonic()
    source,old,identity=failure_identity(inputs,config,original,"EVENT")
    if (output/"TIMING_BINDINGS.json").exists():return verify(output,inputs,config)["primary"]
    restore(output,old,identity)
    freeze(output/"RECOVERY_RUN_BINDINGS.json",dict(config=config,source_sha256=filehash(__file__),inputs={k:str(Path(v).resolve()) if Path(v).is_dir() else filehash(v) for k,v in inputs.items()}))
    prior=read(output/"EVENT_PROGRESS.json")["active_seconds"] if (output/"EVENT_PROGRESS.json").exists() else identity["charged_prior_seconds"]
    elapsed=lambda:prior+time.monotonic()-started
    try:rows,exclusions=extract_rows(source,output,elapsed,identity["charged_prior_seconds"])
    except original.CooperativeYield as exc:return dict(status="yielded",card="D3",reason=str(exc))
    result,details=original.d3(rows,config)
    if elapsed()>3*FORECAST_SECONDS:raise RuntimeError("D3 cumulative cap exceeded")
    for name,value in (("EVENT_ROWS.json",rows),("EVENT_PRIMARY.json",result),("EVENT_DETAILS.json",details),("SOURCE_EXCLUSIONS.json",exclusions)):
        freeze(output/name,value)
    freeze(output/"EVENT_TIMING.json",dict(cumulative_seconds=elapsed(),charged_prior_seconds=identity["charged_prior_seconds"],cap_seconds=3*FORECAST_SECONDS))
    bind(output,inputs,config,["EVENT_ROWS.json","EVENT_PRIMARY.json","EVENT_DETAILS.json","SOURCE_EXCLUSIONS.json","EVENT_TIMING.json","RECOVERY_SOURCE.json"])
    return result


def verify(output:Path,inputs:dict,config:dict)->dict:
    output=Path(output);started=time.monotonic()
    source,_,identity=failure_identity(inputs,config,original,"EVENT");check_binding(output,inputs,config)
    if read(output/"RECOVERY_SOURCE.json")!=identity:raise ValueError("recovery source identity changed")
    rows,exclusions=extract_rows(source);result,details=original.d3(rows,config)
    for name,value in (("EVENT_ROWS.json",rows),("EVENT_PRIMARY.json",result),("EVENT_DETAILS.json",details),("SOURCE_EXCLUSIONS.json",exclusions)):
        if read(output/name)!=value:raise ValueError("D3 recovered source/output does not reconstruct")
    if read(output/"EVENT_TIMING.json")["cumulative_seconds"]+time.monotonic()-started>3*FORECAST_SECONDS:
        raise RuntimeError("D3 execute/verify cumulative cap exceeded")
    return dict(verified=True,primary=result,excluded_api_insertions=len(exclusions),preserved_checkpoint_files=len(identity["retained_files"]))
