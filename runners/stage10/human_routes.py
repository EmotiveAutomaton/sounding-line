"""Source-bound CoAuthor executable-hypothesis producer.

DESIGN CHECK: LESSONS2-5. NULL and ALTERNATIVE retain invalid forecasts and
all attempted costs. Completed replay makes no calls. Target outcomes remain
closed; public source identity and a literal pilot precede science. R3 rules
are approximate forward behavior hypotheses, not known human transition laws.
"""
from __future__ import annotations
import argparse
import hashlib
import os
from pathlib import Path
import time

from runners.stage9.process_identity import native_identity
from soundingline.gpulock import GPU_LOCK, acquire_gpu_lock, release_gpu_lock
from . import human_programs as programs, human_proposal as proposal, ollama
from .contracts import canonical, digest, parse_forecast
from .ollama import now, write_new
from .queue import read, source_identity, status
from .reader import from_record


def identity():
    files = ["runners/stage10/" + f for f in ("human_routes.py", "human_programs.py", "human_proposal.py", "coauthor.py")]
    files.append("runners/stage9/program_inference.py")
    return {**source_identity(), **{p: hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in files}}


def route(task, output, *, profile=None):
    binding = ollama.bind_route({"sources": identity(), "task": task.public(), "task_id": task.task_id, "arm": "R3"}, profile)
    if (output / "COMPLETE.json").exists():
        saved = read(output / "COMPLETE.json")
        if saved["binding"] != binding:
            raise ValueError("human route source or task changed")
        for relative, expected in saved["files"].items():
            p = output / relative
            if not p.resolve().is_relative_to(output.resolve()) or hashlib.sha256(p.read_bytes()).hexdigest() != expected:
                raise ValueError("human route retained evidence changed")
        return read(output / "ROUTE.json")
    output.mkdir(parents=True, exist_ok=False)
    write_new(output / "INPUT.json", {"binding": binding, "task": task.public(), "sources": identity()})
    start = time.perf_counter()
    feedback = None; calls = []; executions = []
    for index in range(2):
        directory = output / ("round-" + str(index+1))
        attempt = proposal.call(task, directory / "proposal", feedback, **ollama.profile_kwargs(profile))
        calls.append(attempt)
        if attempt["status"] != "VALID":
            break
        feedback = programs.evaluate(task, attempt["proposal"]["candidates"])
        executions.append(feedback)
        write_new(directory / "EXECUTION.json", feedback)
    forecast = None; state = "INVALID"
    if len(calls) == 2 and calls[-1]["status"] == "VALID":
        forecast = {"choice": calls[-1]["proposal"]["choice"], "probabilities": feedback["probabilities"],
                    "insufficient_evidence": calls[-1]["proposal"]["insufficient_support"],
                    "explanation": "Equal mixture of executed proposed handling rules with fixed lapse; generated choice retained separately."}
        parse_forecast(canonical(forecast), task)
        state = "VALID"
    generated = sum(c["cost"]["eval_count"] for c in calls)
    if generated > 768:
        raise ValueError("human route exceeded total output allowance")
    result = {"at": now(), "arm": "R3", "task_id": task.task_id, "binding": binding, "status": state,
              "forecast": forecast, "model_calls": len(calls), "generated_tokens": generated,
              "input_tokens": sum(c["cost"]["prompt_eval_count"] for c in calls),
              "reasoning_tokens": None, "reasoning_tokens_status": "not separately exposed",
              "executor_evaluations": sum(e["executor_evaluations"] for e in executions),
              "wall_seconds": time.perf_counter()-start, "target_outcomes_opened": False,
              "meaning": "hypothetical decision rules; no personal-goal or causal-process recovery claim"}
    write_new(output / "ROUTE.json", result)
    write_new(output / "COMPLETE.json", {"at": now(), "binding": binding,
              "files": {p.relative_to(output).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in output.rglob("*") if p.is_file()}})
    return result


def run(prepared, output, phase, pilot=None):
    if phase not in {"pilot", "development", "evaluation"}:
        raise ValueError("undeclared human phase")
    frozen = read(prepared / "FROZEN.json")
    if phase == "pilot":
        if frozen.get("scope") != "discarded legacy pilot writer, excluded from the scientific cohort":
            raise ValueError("pilot must use the excluded source")
    else:
        admission = read(pilot) if pilot is not None else {}
        if admission.get("status") != "PASS" or admission.get("sources") != identity():
            raise ValueError("literal human program pilot required for these sources")
    lane = "development" if phase == "pilot" else phase
    public = read(prepared / (lane + "-public.json"))
    if digest(public) != frozen["public_sha256"][lane]:
        raise ValueError("human public cohort changed")
    tasks = [from_record(r) for r in public["tasks"]]
    if not tasks or len({t.task_id for t in tasks}) != len(tasks):
        raise ValueError("empty or duplicate human cohort")
    for task in tasks:
        programs.features(task)
    manifest = {"sources": identity(), "prepared_sha256": digest(frozen), "public_sha256": digest(public),
                "phase": phase, "arm": "R3", "tasks": len(tasks), "maximum_calls": 2*len(tasks),
                "maximum_generated_tokens_per_route": 768, "target_outcomes_opened": False}
    output.mkdir(parents=True, exist_ok=True)
    if (output / "MANIFEST.json").exists():
        if read(output / "MANIFEST.json") != manifest:
            raise ValueError("human queue manifest changed")
    else:
        write_new(output / "MANIFEST.json", manifest)
    complete = (output / "COMPLETE.json").exists()
    if not complete:
        if (output / "OWNER.json").exists() or GPU_LOCK.exists():
            raise RuntimeError("human queue ownership recovery requires inspection")
        owner = native_identity(os.getpid())
        if owner is None:
            raise RuntimeError("native human worker identity unavailable")
        write_new(output / "OWNER.json", {"at": now(), "native": owner})
        acquire_gpu_lock("stage10-human-" + phase)
    rows = []
    try:
        for task in tasks:
            if identity() != manifest["sources"]:
                raise ValueError("active human source changed")
            directory = output / "attempts" / task.task_id
            if complete and not (directory / "COMPLETE.json").exists():
                raise ValueError("completed human route missing; no new calls")
            result = route(task, directory)
            rows.append({k: result[k] for k in ("task_id", "status", "model_calls", "generated_tokens", "executor_evaluations", "wall_seconds")})
            rows[-1]["sha256"] = digest(result)
            if not complete:
                status(output / "STATUS.json", {"at": now(), "status": "RUNNING", "completed_routes": len(rows), "planned_routes": len(tasks), "native": owner})
        result = {"at": now(), "status": "COMPLETE", "phase": phase, "rows": rows, "manifest_sha256": digest(manifest),
                  "model_calls": sum(r["model_calls"] for r in rows), "generated_tokens": sum(r["generated_tokens"] for r in rows),
                  "target_outcomes_opened": False, "scope": "prediction producer; complete scientific comparisons pending"}
        if complete:
            saved = read(output / "COMPLETE.json")
            if any(saved[k] != result[k] for k in result.keys() - {"at"}):
                raise ValueError("human complete producer does not reproduce")
            return saved
        write_new(output / "COMPLETE.json", result)
        status(output / "STATUS.json", {"at": now(), "status": "COMPLETE", "completed_routes": len(rows)})
        return result
    finally:
        if not complete:
            release_gpu_lock()


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    for name in ("prepared", "output"):
        p.add_argument("--" + name, type=Path, required=True)
    p.add_argument("--phase", choices=["pilot", "development", "evaluation"], required=True)
    p.add_argument("--pilot", type=Path)
    a = p.parse_args()
    try:
        run(a.prepared, a.output, a.phase, a.pilot)
    except Exception as exc:
        if not (a.output / "FAILED.json").exists():
            write_new(a.output / "FAILED.json", {"at": now(), "error": repr(exc)})
        raise
