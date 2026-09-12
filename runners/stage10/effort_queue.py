"""Finite reserved-budget opportunity pilot/development producer.

DESIGN CHECK: LESSONS3-5. Explicit discarded pilot precedes development. Every
selected envelope must equal its public archive source. Training labels only;
no development/evaluation outcomes. Missing completed records forbid new calls.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
from runners.stage9.process_identity import native_identity
from soundingline.gpulock import GPU_LOCK, acquire_gpu_lock, release_gpu_lock
from .contracts import digest
from .effort_readers import Readers, read
from .ghost import envelopes, task_from
from .ollama import now, write_new
from .queue import status

PILOT = "0d05b2bb1da2427b90e3a8236302666f"


def run(root, prepared, output, phase, pilot_receipt=None):
    if phase not in {"pilot", "development"}:
        raise ValueError("undeclared phase")
    frozen = read(prepared / "FROZEN.json")
    train = read(prepared / "train-public.json")
    answers = read(prepared / "train-evaluator.json")
    if digest(train) != frozen["public_sha256"]["train"] or digest(answers) != frozen["evaluator_sha256"]["train"]:
        raise ValueError("frozen training input changed")
    exported, _ = envelopes(root)
    archive = {row["envelope"]["task_id"]: row["envelope"] for row in exported}
    if phase == "pilot":
        selected = [archive[PILOT]]
    else:
        if pilot_receipt is None:
            raise ValueError("literal pilot required before development")
        pilot = read(pilot_receipt)
        if pilot["phase"] != "pilot" or pilot["status"] != "PASS" or pilot["runner_sha256"] != hashlib.sha256(Path(__file__).read_bytes()).hexdigest():
            raise ValueError("pilot verdict or source does not admit development")
        public = read(prepared / "development-public.json")
        if digest(public) != frozen["public_sha256"]["development"]:
            raise ValueError("frozen development input changed")
        selected = read(prepared / "development-envelopes.json")["envelopes"]
        if [task_from(e).task_id for e in selected] != [r["task_id"] for r in public["tasks"]]:
            raise ValueError("development envelope roster differs")
        for env, obj in zip(selected, public["tasks"]):
            from .reader import from_record
            if task_from(env) != from_record(obj):
                raise ValueError("public development rendering differs")
    if not selected or len({e["task_id"] for e in selected}) != len(selected):
        raise ValueError("empty or duplicate task roster")
    for env in selected:
        if env != archive[env["task_id"]] or (phase == "development" and env["task_id"] == PILOT):
            raise ValueError("task source changed or pilot leaked")
    readers = [Readers(root, e, train["tasks"], answers["targets"]) for e in selected]
    runner_hash = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    manifest = {"schema":"stage10.effort-producer.1", "phase":phase, "runner_sha256":runner_hash,
                "readers":[r.sources for r in readers], "task_ids":[e["task_id"] for e in selected],
                "prepared_sha256":digest(frozen), "pilot_receipt_sha256":None if pilot_receipt is None else digest(read(pilot_receipt)),
                "route_allowances":{"R0":256,"R1":512,"R3":[256,256]}, "scope":"prediction producer only; no target outcomes opened"}
    output.mkdir(parents=True,exist_ok=True)
    if (output / "MANIFEST.json").exists():
        if read(output / "MANIFEST.json") != manifest: raise ValueError("producer manifest changed")
    else:write_new(output / "MANIFEST.json",manifest)
    complete = (output / "COMPLETE.json").exists()
    if not complete:
        if GPU_LOCK.exists():raise RuntimeError("GPU already owned; inspection required")
        owner=native_identity(os.getpid())
        if owner is None:raise RuntimeError("native identity unavailable")
        write_new(output / "OWNER.json", {"at":now(),"native":owner})
        acquire_gpu_lock("stage10-effort-"+phase)
    results=[]
    try:
        for reader,env in zip(readers,selected):
            task=task_from(env)
            for arm,callback,allowance in [("R0",reader.initial,256),("R1",reader.retrieval,512),("R3",reader.structured,512)]:
                if hashlib.sha256(Path(__file__).read_bytes()).hexdigest()!=runner_hash:raise ValueError("running producer source changed")
                path=output / "attempts" / task.task_id / arm
                if complete and not (path / "BUDGET_ATTEMPT.json").is_file():raise ValueError("completed record missing; no new call")
                result=callback(task,path,allowance)
                results.append({"task_id":task.task_id,"arm":arm,"status":result["status"],"cost":result["cost"],"attempt_sha256":digest(result)})
                if not complete:status(output / "STATUS.json",{"at":now(),"status":"RUNNING","completed_routes":len(results),"planned_routes":3*len(selected),"worker":owner})
        summary={"at":now(),"status":"PASS" if all(r["status"]=="VALID" for r in results) else "COMPLETE_WITH_INVALID", "phase":phase,
                 "runner_sha256":runner_hash,"manifest_sha256":digest(manifest),"routes":results,
                 "model_calls":sum(r["cost"]["model_calls"] for r in results),"generated_tokens":sum(r["cost"]["output_tokens"] for r in results),
                 "scope":"literal reader producer; no scientific accuracy or routing benefit evaluated"}
        if complete:
            saved=read(output / "COMPLETE.json")
            if any(saved[k]!=summary[k] for k in summary.keys()-{"at"}):raise ValueError("completed producer changed")
            return saved
        write_new(output / "COMPLETE.json",summary)
        status(output / "STATUS.json",{"at":now(),"status":"COMPLETE","completed_routes":len(results)})
        return summary
    finally:
        if not complete:release_gpu_lock()


if __name__ == "__main__":
    parser=argparse.ArgumentParser()
    for key in ["root","prepared","output"]:parser.add_argument("--"+key,type=Path,required=True)
    parser.add_argument("--phase",choices=["pilot","development"],required=True)
    parser.add_argument("--pilot-receipt",type=Path)
    args=parser.parse_args()
    try:
        result=run(args.root,args.prepared,args.output,args.phase,args.pilot_receipt)
        print(json.dumps({k:result[k] for k in ["status","phase","model_calls"]}),flush=True)
    except Exception as exc:
        write_new(args.output / "FAILED.json",{"at":now(),"error":repr(exc)})
        raise
