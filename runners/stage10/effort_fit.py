"""Fit the effort controller from explicitly allocated original development outcomes.

DESIGN CHECK: LESSONS3-5. Complete source-bound producer replay precedes label
access. Only preallocated fitting cases can open private records; reserved
outcomes are never loaded. Actual enacted artifacts, not reference forecasts,
provide labels. Invalid attempts stay in the development denominator.
"""
from __future__ import annotations
import argparse
import hashlib
import time
from pathlib import Path
from unittest.mock import patch
from . import effort, effort_readers, effort_queue
from .contracts import digest
from .ollama import now, write_new
from .queue import read


def fit(root, prepared, producer, export, output, pilot):
    started=time.perf_counter()
    allocation=read(output / "ALLOCATION.json")
    original=read(prepared / "ALLOCATION.json")
    if allocation["source_allocation_sha256"]!=digest(original):raise ValueError("allocation source changed")
    fitting=set(allocation["fit_cases"]); reserved=set(allocation["evaluation_cases"])
    if not fitting or not reserved or fitting & reserved or fitting | reserved != set(original["development_cases"]):raise ValueError("invalid fit/reserve partition")
    if not (producer / "COMPLETE.json").is_file():raise ValueError("producer incomplete")
    with patch("runners.stage10.ollama.api",side_effect=AssertionError("fit cannot generate")),patch.object(effort_readers,"execute",side_effect=AssertionError("fit cannot execute")):
        complete=effort_queue.run(root,prepared,producer,"development",pilot)
    if digest(complete)!=allocation["source_producer_sha256"]:raise ValueError("completed producer changed")
    public=read(prepared / "development-public.json")
    membership={r["task_id"]:r["case_id"] for r in original["tasks"]}
    raw_manifest=read(export / "RAW_MANIFEST.json")
    public_manifest=read(root / "PUBLIC_MANIFEST.json")
    members={c["case_id"]:set(c["tasks_in_recorded_order"]) for c in public_manifest["cases"]}
    truths={}; observed_files={}
    for case in sorted(fitting):
        relative="private/"+case+"-evaluation.json"
        source=export / relative;payload=source.read_bytes()
        if hashlib.sha256(payload).hexdigest()!=raw_manifest["files"][relative]:raise ValueError("original evaluation source changed")
        import json
        record=json.loads(payload)
        if record["case_id"]!=case or set(record["task_ids"])!=members[case]:raise ValueError("original case/task join changed")
        outcome=record["hidden_continuations"]
        if type(outcome["artifact"]) is not int or outcome["artifact"] not in (0,1) or type(outcome["legal"]) is not bool or outcome["attempted_option"] not in (0,1):raise ValueError("not a recorded binary enacted artifact")
        truths[case]=outcome["artifact"];observed_files[relative]=hashlib.sha256(payload).hexdigest()
    rows=[]
    for obj in public["tasks"]:
        task_id=obj["task_id"];case=membership[task_id]
        if case not in fitting:continue
        truth=next(k for k,v in obj["choices"] if v==str(truths[case]))
        routes={arm:read(producer / "attempts" / task_id / arm / "BUDGET_ATTEMPT.json")["result"] for arm in ["R0","R1","R3"]}
        rows.append({"task":obj,"group":case,"truth":truth,"routes":routes})
    bundle={"schema":"stage10.effort-development.1","phase":"development","complete":True,
            "producers":{str(producer / "COMPLETE.json"):digest(complete),**observed_files},"rows":rows}
    policy=effort.fit(bundle)
    write_new(output / "DEVELOPMENT.json",bundle)
    write_new(output / "POLICY.json",policy)
    receipt={"at":now(),"status":"FITTED","policy_sha256":policy["policy_sha256"],"allocation_sha256":digest(allocation),
             "fit_groups":len(fitting),"fit_tasks":len(rows),"reserved_groups":len(reserved),"reserved_outcomes_opened":False,
             "original_sources":observed_files,"producer_replay_new_calls":0,"producer_replay_new_executions":0,
             "wall_seconds":time.perf_counter()-started,"fit_source_sha256":hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
             "scope":allocation["scope"],"scientific_acceptance":"pending actual reserved policy comparison"}
    write_new(output / "COMPLETE.json",receipt)
    return receipt


if __name__ == "__main__":
    p=argparse.ArgumentParser()
    for name in ["root","prepared","producer","export","output","pilot"]:p.add_argument("--"+name,type=Path,required=True)
    a=p.parse_args()
    result=fit(a.root,a.prepared,a.producer,a.export,a.output,a.pilot)
    import json
    print(json.dumps({k:result[k] for k in ["status","fit_groups","fit_tasks","reserved_groups","reserved_outcomes_opened"]}))
