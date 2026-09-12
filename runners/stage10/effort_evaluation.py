"""Actual reserved comparison of frozen effort policies, without outcome access.

DESIGN CHECK: LESSONS3-5. Fixed, confidence-only and benefit/cost policies all
pay for an initial256-token read and optional512-token work. Completed driver
replay makes no calls. Reserved source groups are disjoint from policy fitting;
old exposed development cases remain descriptive, not an untouched population.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
from runners.stage9.process_identity import native_identity
from soundingline.gpulock import GPU_LOCK, acquire_gpu_lock, release_gpu_lock
from . import effort
from .contracts import digest
from .effort_readers import Readers, read
from .ghost import task_from
from .ollama import now, write_new
from .queue import status
from .reader import from_record


def run(root,prepared,policy_root,output):
    allocation=read(policy_root / "ALLOCATION.json")
    fit=read(policy_root / "COMPLETE.json")
    policy=read(policy_root / "POLICY.json")
    effort.verify_policy(policy)
    if fit["status"]!="FITTED" or fit["allocation_sha256"]!=digest(allocation) or fit["policy_sha256"]!=policy["policy_sha256"]:raise ValueError("policy fit or allocation changed")
    source=read(prepared / "ALLOCATION.json");frozen=read(prepared / "FROZEN.json")
    if digest(source)!=allocation["source_allocation_sha256"]:raise ValueError("original allocation changed")
    fitting=set(allocation["fit_cases"]);reserve=set(allocation["evaluation_cases"])
    if fitting & reserve or fitting | reserve!=set(source["development_cases"]):raise ValueError("fit/reserve leak")
    training=read(prepared / "train-public.json");answers=read(prepared / "train-evaluator.json");public=read(prepared / "development-public.json")
    if digest(training)!=frozen["public_sha256"]["train"] or digest(answers)!=frozen["evaluator_sha256"]["train"] or digest(public)!=frozen["public_sha256"]["development"]:raise ValueError("prepared source changed")
    membership={r["task_id"]:r["case_id"] for r in source["tasks"]}
    envelopes={e["task_id"]:e for e in read(prepared / "development-envelopes.json")["envelopes"]}
    selected=[r for r in public["tasks"] if membership[r["task_id"]] in reserve]
    if not selected:raise ValueError("empty reserve")
    runner_hash=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    readers=[]
    for obj in selected:
        task=from_record(obj);env=envelopes[task.task_id]
        if task_from(env)!=task:raise ValueError("reserve task/envelope mismatch")
        readers.append(Readers(root,env,training["tasks"],answers["targets"]))
    manifest={"schema":"stage10.effort-evaluation.1","policy_sha256":policy["policy_sha256"],"fit_receipt_sha256":digest(fit),
              "runner_sha256":runner_hash,"readers":[r.sources for r in readers],"tasks":[r["task_id"] for r in selected],
              "modes":["fixed","confidence-only","benefit-cost"],"mode_order":"hash rank per task, before outcomes",
              "scope":allocation["scope"]}
    output.mkdir(parents=True,exist_ok=True)
    if (output / "MANIFEST.json").exists():
        if read(output / "MANIFEST.json")!=manifest:raise ValueError("evaluation sources changed")
    else:write_new(output / "MANIFEST.json",manifest)
    complete=(output / "COMPLETE.json").exists()
    if not complete:
        if GPU_LOCK.exists():raise RuntimeError("GPU ownership needs inspection")
        owner=native_identity(os.getpid())
        if owner is None:raise RuntimeError("native worker identity unavailable")
        write_new(output / "OWNER.json",{"at":now(),"native":owner})
        acquire_gpu_lock("stage10-effort-reserved")
    rows=[]
    try:
        for obj,reader in zip(selected,readers):
            task=from_record(obj)
            for mode in sorted(manifest["modes"],key=lambda m:digest(["stage10-effort-order",task.task_id,m])):
                if hashlib.sha256(Path(__file__).read_bytes()).hexdigest()!=runner_hash or reader.current_sources()!=reader.sources:raise ValueError("active evaluation source changed")
                folder=output / "attempts" / task.task_id / mode
                if complete and not (folder / "COMPLETE.json").is_file():raise ValueError("completed driver missing; no new call")
                result=effort.run(task,folder,policy,reader.initial,reader.additional,mode=mode,group=membership[task.task_id],reader_sources={**reader.sources,"evaluation-driver":runner_hash})
                rows.append({"task_id":task.task_id,"mode":mode,"status":result["status"],"cost":result["cost"],"route_sha256":digest(result)})
                if not complete:status(output / "STATUS.json",{"at":now(),"status":"RUNNING","completed_routes":len(rows),"planned_routes":3*len(selected),"worker":owner})
        result={"at":now(),"status":"COMPLETE","manifest_sha256":digest(manifest),"rows":rows,"model_calls":sum(r["cost"]["model_calls"] for r in rows),
                "generated_tokens":sum(r["cost"]["output_tokens"] for r in rows),"target_outcomes_opened":False,
                "scope":"actual policy prediction producer only; no scientific outcome comparison yet"}
        if complete:
            saved=read(output / "COMPLETE.json")
            if any(saved[k]!=result[k] for k in result.keys()-{"at"}):raise ValueError("completed policy evaluation changed")
            return saved
        write_new(output / "COMPLETE.json",result)
        status(output / "STATUS.json",{"at":now(),"status":"COMPLETE","completed_routes":len(rows)})
        return result
    finally:
        if not complete:release_gpu_lock()


if __name__ == "__main__":
    p=argparse.ArgumentParser()
    for name in ["root","prepared","policy-root","output"]:p.add_argument("--"+name,type=Path,required=True)
    a=p.parse_args()
    try:
        result=run(a.root,a.prepared,a.policy_root,a.output)
        print(json.dumps({k:result[k] for k in ["status","model_calls","generated_tokens"]}),flush=True)
    except Exception as exc:
        write_new(a.output / "FAILED.json",{"at":now(),"error":repr(exc)})
        raise
