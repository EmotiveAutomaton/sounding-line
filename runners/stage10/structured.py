"""R3: propose, execute, refine, and retain a conditional candidate mixture.

DESIGN CHECK: LESSONS2-5; Stage10 sections4-6. Two proposal rounds each allow
384 generated tokens, matching R2's allowance. NULL: impossible observations
produce mismatch, not fallback. ALTERNATIVE: consequences run on Ghost's public
APIs. Generated choice and executor-derived probabilities remain distinct.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
from . import ollama
from .contracts import digest, parse_forecast, canonical
from .executor import execute, source_identity as executor_identity
from .ghost import task_from
from .ollama import now, write_new
from .proposal import call as propose
from .queue import read, source_identity as core_identity, status
from runners.stage9.process_identity import native_identity
from soundingline.gpulock import GPU_LOCK, acquire_gpu_lock, release_gpu_lock


def identity():
    files = ("ghost.py", "proposal.py", "executor.py", "executor_worker.py", "structured.py")
    return {**core_identity(), **{"runners/stage10/"+f: hashlib.sha256(Path(__file__).with_name(f).read_bytes()).hexdigest() for f in files}}


def route(root, envelope, output, *, profile=None):
    task = task_from(envelope)
    rounds = []
    feedback = None
    for index in range(2):
        folder = output / ("round-"+str(index+1))
        proposal = propose(task, envelope, folder / "proposal", feedback, **ollama.profile_kwargs(profile))
        item = {"proposal_binding": proposal["binding"], "status": proposal["status"], "cost": proposal["cost"], "wall_seconds": proposal["wall_seconds"]}
        rounds.append(item)
        if proposal["status"] != "VALID":
            break
        execution = execute(root, envelope, proposal["proposal"]["candidates"], folder / "execution")
        item["execution_binding"] = execution["binding"]
        response = execution["response"]
        item["execution"] = response
        if not response["ok"]:
            item["status"] = "EXECUTOR_INVALID"
            break
        feedback = response["result"]
    forecast = None
    last = rounds[-1]
    state = last["status"]
    if len(rounds) == 2 and state == "VALID":
        if feedback["model_mismatch"]:
            state = "MISMATCH"
        else:
            probabilities = feedback["conditional_candidate_mixture"]
            forecast = {"choice": proposal["proposal"]["choice"],
                        "probabilities": {key: probabilities[int(description)] for key, description in task.choices},
                        "insufficient_evidence": proposal["proposal"]["insufficient_support"],
                        "explanation": "Likelihood-weighted mixture conditional on the proposed candidate set; generated choice retained separately from its argmax."}
            parse_forecast(canonical(forecast), task)
    generated = sum(r["cost"]["eval_count"] for r in rounds)
    if generated > 768:
        raise ValueError("structured route exceeded output allowance")
    result = {"at": now(), "arm": "R3", "task_id": task.task_id, "status": state, "forecast": forecast,
              "instrument": "executed-candidate-mixture-v1 with independently generated choice",
              "mixture_rule": "uniform distinct candidate prior times allowed-evidence likelihood, normalized only within proposed support",
              "coverage_limit": "true maker may be omitted; candidate coverage must be evaluated separately on synthetic ground truth",
              "rounds": rounds, "model_calls": len(rounds), "total_generated_tokens": generated,
              "executor_api_evaluations": sum(r.get("execution",{}).get("result",{}).get("executor_api_evaluations",0) for r in rounds)}
    if (output / "ROUTE.json").exists():
        saved = read(output / "ROUTE.json")
        if any(saved[k] != result[k] for k in result.keys()-{"at"}):
            raise ValueError("retained structured route changed")
        return saved
    write_new(output / "ROUTE.json", result)
    return result


def run(root, input_path, output):
    inputs = read(input_path)
    manifest = {"schema": "stage10.structured-queue.1", "sources": identity(), "executor_sources": executor_identity(root),
                "inputs_sha256": digest(inputs), "task_ids": [e["task_id"] for e in inputs["envelopes"]],
                "scope": inputs["scope"], "calls_per_task": 2, "generated_tokens_per_call": 384}
    if len(set(manifest["task_ids"])) != len(manifest["task_ids"]):
        raise ValueError("duplicate task")
    output.mkdir(parents=True, exist_ok=True)
    if (output / "MANIFEST.json").exists():
        if read(output / "MANIFEST.json") != manifest:
            raise ValueError("structured source or input changed")
    else:
        write_new(output / "MANIFEST.json", manifest)
    complete = (output / "COMPLETE.json").exists()
    if not complete:
        if GPU_LOCK.exists():
            raise RuntimeError("GPU ownership inspection required")
        owner = native_identity(os.getpid())
        if owner is None:
            raise RuntimeError("native identity unavailable")
        write_new(output / "OWNER.json", {"at": now(), "native": owner})
        acquire_gpu_lock("stage10-R3")
    routes = []
    try:
        for envelope in inputs["envelopes"]:
            if identity() != manifest["sources"]:
                raise ValueError("live structured source changed")
            target = output / "attempts" / envelope["task_id"]
            if complete:
                saved = read(target / "ROUTE.json")
                for index, item in enumerate(saved["rounds"], 1):
                    folder = target / ("round-"+str(index))
                    needed = [folder/"proposal"/name for name in ("ATTEMPT.json","REQUEST.json","RAW.json")]
                    if "execution_binding" in item:
                        needed += [folder/"execution"/name for name in ("EXECUTION.json","INPUT.json","RAW.json")]
                    if not all(p.is_file() for p in needed):
                        raise ValueError("completed structured route missing evidence; no recomputation")
            routes.append(route(root,envelope,target))
            if not complete:
                status(output / "STATUS.json", {"at": now(), "status": "RUNNING", "completed_tasks":len(routes), "planned_tasks":len(inputs["envelopes"]), "worker":owner})
        result = {"at":now(), "status":"COMPLETE", "manifest_sha256":digest(manifest), "tasks":len(routes),
                  "model_calls":sum(r["model_calls"] for r in routes), "generated_tokens":sum(r["total_generated_tokens"] for r in routes),
                  "routes":[{"task_id":r["task_id"],"status":r["status"],"sha256":digest(r)} for r in routes],
                  "scope":inputs["scope"]}
        if complete:
            saved=read(output/"COMPLETE.json")
            if any(saved[k]!=result[k] for k in result.keys()-{"at"}):
                raise ValueError("structured completed summary changed")
            return saved
        write_new(output/"COMPLETE.json",result)
        status(output/"STATUS.json",{"at":now(),"status":"COMPLETE","completed_tasks":len(routes)})
        return result
    finally:
        if not complete:
            release_gpu_lock()


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--public-root",type=Path,required=True)
    p.add_argument("--inputs",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    a=p.parse_args()
    try:
        result=run(a.public_root,a.inputs,a.output)
        print(json.dumps({k:result[k] for k in ("status","tasks","model_calls")}),flush=True)
    except Exception as exc:
        if not (a.output/"FAILED.json").exists():
            write_new(a.output/"FAILED.json",{"at":now(),"error":repr(exc)})
        raise


if __name__ == "__main__":
    main()
