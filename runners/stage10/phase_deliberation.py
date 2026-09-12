"""Explicit-phase R2 producer, reusing the validated matched route unchanged.

DESIGN CHECK: LESSONS3-5. Both hypotheses use two 384-token calls. Evaluation
selects its frozen public file, never an evaluator or relabelled development
record. All original route bytes and costs survive; no score is calculated.
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
from .ollama import now, write_new
from .queue import read, status
from .reader import from_record
from .deliberation import route, identity as route_identity


def identity():
    return {**route_identity(), "runners/stage10/phase_deliberation.py": hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}


def run(prepared: Path, output: Path, phase: str):
    if phase not in {"development", "evaluation"}:
        raise ValueError("undeclared phase")
    frozen = read(prepared / "FROZEN.json")
    public = read(prepared / (phase + "-public.json"))
    if digest(public) != frozen["public_sha256"][phase]:
        raise ValueError("frozen development requests changed")
    tasks = [from_record(row) for row in public["tasks"]]
    manifest = {"schema": "stage10.r2-phase-queue.1", "phase": phase, "sources": identity(), "prepared_sha256": digest(frozen),
                "public_sha256": digest(public), "arm": "R2", "task_count": len(tasks),
                "calls_per_task": 2, "generated_tokens_per_call": 384, "context_tokens": 16384,
                "scope": frozen.get("scope", "historically exposed development; no evaluation labels opened")}
    output.mkdir(parents=True, exist_ok=True)
    if (output / "MANIFEST.json").exists():
        if read(output / "MANIFEST.json") != manifest:
            raise ValueError("R2 queue source or task binding changed")
    else:
        write_new(output / "MANIFEST.json", manifest)
    completed = (output / "COMPLETE.json").exists()
    if not completed:
        if GPU_LOCK.exists():
            raise RuntimeError("GPU ownership inspection required before retry")
        owner = native_identity(os.getpid())
        if owner is None:
            raise RuntimeError("native worker identity unavailable")
        write_new(output / "OWNER.json", {"at": now(), "native": owner})
        acquire_gpu_lock("stage10-R2-" + phase)
    results = []
    try:
        for task in tasks:
            if identity() != manifest["sources"]:
                raise ValueError("frozen R2 runner changed during execution")
            if completed:
                required = [output / "attempts" / task.task_id / "ROUTE.json"]
                required += [output / "attempts" / task.task_id / phase / filename
                             for phase in ("draft", "reconsidered")
                             for filename in ("ATTEMPT.json", "REQUEST.json", "RAW.json")]
                if not all(path.is_file() for path in required):
                    raise ValueError("completed R2 queue is missing a retained call; no recomputation permitted")
            results.append(route(task, output / "attempts" / task.task_id))
            if not completed:
                status(output / "STATUS.json", {"at": now(), "status": "RUNNING", "completed_tasks": len(results),
                                               "planned_tasks": len(tasks), "worker": owner})
        summary = {"at": now(), "status": "COMPLETE", "manifest_sha256": digest(manifest),
                   "routes": [{"task_id": row["task_id"], "status": row["status"], "route_sha256": digest(row)} for row in results],
                   "completed_tasks": len(results), "model_calls": 2 * len(results),
                   "generated_tokens": sum(row["total_generated_tokens"] for row in results),
                   "scope": "prediction producer only; scientific comparison and calibration pending"}
        if completed:
            saved = read(output / "COMPLETE.json")
            if any(saved[key] != summary[key] for key in summary.keys() - {"at"}):
                raise ValueError("R2 completed receipt differs from its retained routes")
            return saved
        write_new(output / "COMPLETE.json", summary)
        status(output / "STATUS.json", {"at": now(), "status": "COMPLETE", "completed_tasks": len(results)})
        return summary
    finally:
        if not completed:
            release_gpu_lock()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--phase", choices=["development", "evaluation"], required=True)
    parser.add_argument("--prepared", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        result = run(args.prepared, args.output, args.phase)
        print(json.dumps({key: result[key] for key in ("status", "completed_tasks", "model_calls")}), flush=True)
    except Exception as exc:
        if not (args.output / "FAILED.json").exists():
            write_new(args.output / "FAILED.json", {"at": now(), "error": repr(exc)})
        raise


if __name__ == "__main__":
    main()
