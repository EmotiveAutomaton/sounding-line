"""Common reading screen including native procedures and exception memory.

DESIGN CHECK: LESSONS2-5. All routes see the same public target. R1 and R4
share training examples and representation ceiling; R2 and R3/R4 share two
384-token calls. NULL failures stay invalid and charged; ALTERNATIVE success
must execute through native Ghost APIs. Completed replay makes no new calls.
The keyed R3 instrument is versioned separately from the failed list version.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import time

from runners.stage9.process_identity import native_identity
from soundingline.gpulock import GPU_LOCK, acquire_gpu_lock, release_gpu_lock
from . import deliberation, ollama, reading_memory as memory, reading_proposal as proposal
from .contracts import canonical, digest, parse_forecast
from .executor import execute, source_identity as executor_identity
from .ghost import envelopes, task_from
from .queue import read, status
from .reading_source import PILOT_CASE
from .structured import identity as base_identity

ARMS = ("R0", "R1", "R2", "R3", "R4-opaque", "R4-grounded")


def identity(root):
    files = ("reading_routes.py", "reading_proposal.py", "reading_memory.py", "reading_source.py", "deliberation.py")
    return {**base_identity(), **{"runners/stage10/" + f: hashlib.sha256(Path(__file__).with_name(f).read_bytes()).hexdigest() for f in files},
            "exported-source-closure": digest(executor_identity(root))}


def route(root, envelope, output, training, answers, arm, group):
    if arm not in ARMS:
        raise ValueError("undeclared reading arm")
    task = task_from(envelope)
    binding = digest({"task": task.public(), "envelope": envelope, "training": training, "answers": answers,
                      "arm": arm, "group": group, "sources": identity(root)})
    if (output / "COMPLETE.json").exists():
        saved = read(output / "COMPLETE.json")
        if saved["binding"] != binding:
            raise ValueError("reading route source or input changed")
        for relative, expected in saved["files"].items():
            path = output / relative
            if not path.resolve().is_relative_to(output.resolve()) or hashlib.sha256(path.read_bytes()).hexdigest() != expected:
                raise ValueError("retained reading route evidence changed")
        return read(output / "ROUTE.json")
    output.mkdir(parents=True, exist_ok=False)
    ollama.write_new(output / "INPUT.json", {"binding": binding, "public_task": task.public(), "sources": identity(root)})
    started = time.perf_counter()
    calls, executions = [], []
    training_calls, representation_bytes = 0, 0
    if arm in {"R0", "R1"}:
        kwargs = {"context_tokens": 16384}
        if arm == "R1":
            episodes, selection = memory.examples(task, training, answers)
            representation_bytes = selection["actual_store_bytes"]
            ollama.write_new(output / "MEMORY.json", selection)
            kwargs.update(examples=episodes, instruction="Use these concrete earlier training episodes; their evidence views are labelled. Predict the new case directly.")
        final = ollama.call(task, output / "call", **kwargs)
        calls.append(final); state, forecast = final["status"], final["forecast"]
    elif arm == "R2":
        result = deliberation.route(task, output / "deliberation")
        calls = result["calls"]; state, forecast = result["status"], result["forecast"]
    else:
        representation = None
        if arm.startswith("R4"):
            library = memory.induce(root, training, answers,
                                    prior_observations=task.evidence["permitted_prior_artifacts"], prior_group=group)
            procedures = memory.representation(library, arm.removeprefix("R4-"))
            episodes, selection = memory.examples(task, training, answers, reserved_bytes=len(canonical(procedures).encode("utf8")))
            representation = {"procedures": procedures, "episodes": episodes,
                              "scope": "training/prior-artifact reconstructions, not the maker's known procedures"}
            representation_bytes = len(canonical(representation).encode("utf8"))
            if representation_bytes > memory.STORE_BYTES:
                raise ValueError("combined representation exceeds common cap")
            training_calls = library["training_execution_calls"]
            ollama.write_new(output / "MEMORY.json", {"library": library, "selection": selection, "representation": representation})
        feedback, forecast, state = None, None, "INVALID"
        for index in range(2):
            folder = output / ("round-" + str(index + 1))
            proposed = proposal.call(task, envelope, folder / "proposal", feedback, memory=representation)
            calls.append(proposed); state = proposed["status"]
            if state != "VALID":
                break
            execution = execute(root, envelope, proposed["proposal"]["candidates"], folder / "execution")
            executions.append(execution)
            if not execution["response"]["ok"]:
                state = "EXECUTOR_INVALID"; break
            feedback = execution["response"]["result"]
        if len(calls) == 2 and state == "VALID":
            if feedback["model_mismatch"]:
                state = "MISMATCH"
            else:
                probabilities = feedback["conditional_candidate_mixture"]
                forecast = {"choice": proposed["proposal"]["choice"],
                            "probabilities": {k: probabilities[int(v)] for k, v in task.choices},
                            "insufficient_evidence": proposed["proposal"]["insufficient_support"],
                            "explanation": "Executed likelihood mixture conditional on proposed libraries; generated choice retained separately."}
                parse_forecast(canonical(forecast), task)
    generated = sum(c["cost"]["eval_count"] for c in calls)
    if generated > 768:
        raise ValueError("reading route exceeded generated-token allowance")
    result = {"at": ollama.now(), "binding": binding, "arm": arm, "task_id": task.task_id,
              "status": state, "forecast": forecast, "model_calls": len(calls), "generated_tokens": generated,
              "input_tokens": sum(c["cost"]["prompt_eval_count"] for c in calls),
              "reasoning_tokens": None, "reasoning_tokens_status": "not separately exposed",
              "executor_evaluations": training_calls + sum(e["response"].get("result", {}).get("executor_api_evaluations", 0) for e in executions),
              "procedure_induction_evaluations": training_calls, "representation_bytes": representation_bytes,
              "common_representation_ceiling_bytes": memory.STORE_BYTES,
              "wall_seconds": time.perf_counter() - started,
              "scope": "literal prediction/reconstruction producer; no evaluator outcomes opened"}
    ollama.write_new(output / "ROUTE.json", result)
    files = {p.relative_to(output).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in output.rglob("*") if p.is_file()}
    ollama.write_new(output / "COMPLETE.json", {"at": ollama.now(), "binding": binding, "files": files})
    return result


def run(root, prepared, output, phase, pilot_receipt=None):
    if phase not in {"pilot", "development", "evaluation"}:
        raise ValueError("undeclared reading phase")
    frozen = read(prepared / "FROZEN.json")
    training = read(prepared / "train-public.json"); answers = read(prepared / "train-evaluator.json")
    if digest(training) != frozen["public_sha256"]["train"] or digest(answers) != frozen["evaluator_sha256"]["train"]:
        raise ValueError("reading training source changed")
    allocation = read(prepared / "ALLOCATION.json")
    if digest(allocation) != frozen["allocation_sha256"]:
        raise ValueError("reading allocation changed")
    if phase == "pilot":
        rows, _ = envelopes(root)
        selected = [min((r for r in rows if r["case_id"] == PILOT_CASE), key=lambda r: r["envelope"]["task_id"])]
    else:
        if pilot_receipt is None:
            raise ValueError("literal branch pilot required")
        pilot = read(pilot_receipt)
        if pilot["status"] != "PASS" or pilot["sources"] != identity(root) or pilot["prepared_sha256"] != digest(frozen):
            raise ValueError("literal pilot not admitted for current sources")
        public = read(prepared / (phase + "-public.json"))
        if digest(public) != frozen["public_sha256"][phase]:
            raise ValueError("reading public phase changed")
        members = {r["task_id"]: r for r in allocation["tasks"]}
        frames = read(prepared / (phase + "-envelopes.json"))["envelopes"]
        selected = [{"case_id": members[e["task_id"]]["case_id"], "envelope": e} for e in frames]
        if [digest(task_from(e).public()) for e in frames] != [digest(memory.from_record(r).public()) for r in public["tasks"]]:
            raise ValueError("reading task/envelope mismatch")
        if any(members[e["task_id"]]["lane"] != phase or members[e["task_id"]]["case_id"] not in allocation[phase + "_cases"] for e in frames):
            raise ValueError("reading phase crosses allocation")
    manifest = {"phase": phase, "sources": identity(root), "prepared_sha256": digest(frozen),
                "inputs_sha256": digest(selected), "arms": list(ARMS), "tasks": len(selected),
                "maximum_generated_tokens_per_route": 768, "scope": "source-separated previously exposed reading cases"}
    output.mkdir(parents=True, exist_ok=True)
    if (output / "MANIFEST.json").exists():
        if read(output / "MANIFEST.json") != manifest:
            raise ValueError("reading producer source or input changed")
    else:
        ollama.write_new(output / "MANIFEST.json", manifest)
    complete = (output / "COMPLETE.json").exists()
    if not complete:
        if GPU_LOCK.exists():
            raise RuntimeError("GPU ownership inspection required")
        owner = native_identity(os.getpid())
        if owner is None:
            raise RuntimeError("native process identity unavailable")
        ollama.write_new(output / "OWNER.json", {"at": ollama.now(), "native": owner})
        acquire_gpu_lock("stage10-reading-" + phase)
    rows = []
    try:
        for item in selected:
            for arm in ARMS:
                if identity(root) != manifest["sources"]:
                    raise ValueError("active reading source changed")
                out = output / "attempts" / item["envelope"]["task_id"] / arm
                if complete and not (out / "COMPLETE.json").exists():
                    raise ValueError("completed route missing; no new calls")
                r = route(root, item["envelope"], out, training["tasks"], answers["targets"], arm, item["case_id"])
                rows.append({k: r[k] for k in ("arm", "task_id", "status", "model_calls", "generated_tokens", "wall_seconds", "executor_evaluations")})
                rows[-1]["sha256"] = digest(r)
                if not complete:
                    status(output / "STATUS.json", {"at": ollama.now(), "status": "RUNNING", "completed_routes": len(rows), "planned_routes": len(selected)*len(ARMS), "worker": owner})
        result = {"at": ollama.now(), "status": "COMPLETE", "phase": phase, "manifest_sha256": digest(manifest), "rows": rows,
                  "model_calls": sum(r["model_calls"] for r in rows), "generated_tokens": sum(r["generated_tokens"] for r in rows),
                  "target_outcomes_opened": False}
        if complete:
            saved = read(output / "COMPLETE.json")
            if any(saved[k] != result[k] for k in result.keys() - {"at"}):
                raise ValueError("completed reading producer changed")
            return saved
        ollama.write_new(output / "COMPLETE.json", result)
        status(output / "STATUS.json", {"at": ollama.now(), "status": "COMPLETE", "completed_routes": len(rows)})
        return result
    finally:
        if not complete:
            release_gpu_lock()


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    for name in ("public-root", "prepared", "output"):
        p.add_argument("--" + name, type=Path, required=True)
    p.add_argument("--phase", choices=["pilot", "development", "evaluation"], required=True)
    p.add_argument("--pilot-receipt", type=Path)
    a = p.parse_args()
    try:
        result = run(a.public_root, a.prepared, a.output, a.phase, a.pilot_receipt)
        print(json.dumps({k: result[k] for k in ("status", "model_calls", "generated_tokens")}), flush=True)
    except Exception as exc:
        if not (a.output / "FAILED.json").exists():
            ollama.write_new(a.output / "FAILED.json", {"at": ollama.now(), "error": repr(exc)})
        raise
