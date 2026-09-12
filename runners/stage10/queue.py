"""Finite Stage 10 development queue with immutable attempts and native ownership.

DESIGN CHECK: LESSONS 2-5. Under NULL/ALTERNATIVE, identical frozen requests
resume without model calls, changed sources cannot resume, and every attempted
prediction remains counted. Evaluation labels are never opened by this worker.
Science is scored only by a separate complete-cell consumer, not this producer.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import time
from pathlib import Path

from runners.stage9.process_identity import native_identity
from soundingline.gpulock import GPU_LOCK, acquire_gpu_lock, release_gpu_lock
from .contracts import canonical, digest
from .ollama import call, now, write_new
from .reader import build, from_record


def read(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def source_identity() -> dict:
    root = Path(__file__).resolve().parent
    repo = root.parents[1]
    paths = [root / name for name in ("__init__.py", "contracts.py", "ollama.py", "reader.py", "queue.py")]
    paths += [repo / "runners/stage9/process_identity.py", repo / "soundingline/gpulock.py"]
    return {path.relative_to(repo).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest() for path in paths}


def status(path: Path, value: dict):
    temporary = path.with_suffix(".tmp")
    temporary.write_text(canonical(value) + "\n", encoding="utf-8")
    temporary.replace(path)


def run(prepared: Path, output: Path, arms: list[str], maximum: int | None = None):
    frozen = read(prepared / "FROZEN.json")
    training_record = read(prepared / "train-public.json")
    answer_record = read(prepared / "train-evaluator.json")
    task_record = read(prepared / "development-public.json")
    for lane, value, kind in (("train", training_record, "public"), ("train", answer_record, "evaluator"),
                              ("development", task_record, "public")):
        if digest(value) != frozen[kind + "_sha256"][lane]:
            raise ValueError("frozen source binding differs")
    if len(arms) != len(set(arms)) or not set(arms) <= {"R0", "R1"}:
        raise ValueError("duplicate or unimplemented arm")
    tasks = task_record["tasks"] if maximum is None else task_record["tasks"][:maximum]
    if not tasks:
        raise ValueError("empty cohort")
    manifest = {"schema": "stage10.development-queue.1", "sources": source_identity(),
                "prepared_sha256": digest(frozen), "tasks_sha256": digest(tasks), "arms": arms,
                "task_count": len(tasks), "planned_calls": len(tasks) * len(arms),
                "scope": "development only; historically exposed, no evaluation labels opened",
                "context_tokens": 16384, "maximum_generated_tokens_per_route": 768}
    output.mkdir(parents=True, exist_ok=True)
    if (output / "MANIFEST.json").exists():
        if read(output / "MANIFEST.json") != manifest:
            raise ValueError("queue cannot resume changed sources or selection")
    else:
        write_new(output / "MANIFEST.json", manifest)
    if (output / "COMPLETE.json").exists():
        saved = read(output / "COMPLETE.json")
        if saved["manifest_sha256"] != digest(manifest) or saved["attempted_calls"] != manifest["planned_calls"]:
            raise ValueError("completed queue receipt differs from its frozen manifest")
        expected_pairs = {(row["task_id"], arm) for row in tasks for arm in arms}
        if len(saved["attempts"]) != len(expected_pairs) or {(row["task_id"], row["arm"]) for row in saved["attempts"]} != expected_pairs:
            raise ValueError("completed queue attempt roster differs")
        for row in saved["attempts"]:
            directory = output / "attempts" / row["task_id"] / row["arm"]
            attempt = read(directory / "ATTEMPT.json")
            request = read(directory / "REQUEST.json")
            raw = read(directory / "RAW.json")
            if attempt["binding"] != row["binding"] or request["binding"] != row["binding"] or digest(raw) != attempt["raw_sha256"]:
                raise ValueError("completed queue raw attempt changed")
            if attempt["status"] != row["status"] or attempt["cost"] != row["cost"]:
                raise ValueError("completed queue status or cost differs")
        return saved
    owner = native_identity(os.getpid())
    if owner is None:
        raise RuntimeError("native worker identity unavailable")
    status(output / "OWNER.json", {"native": owner, "at": now()})
    if GPU_LOCK.exists():
        raise RuntimeError("GPU lock already held; requires an ownership inspection before retry")
    acquire_gpu_lock("stage10-coauthor-development")
    started = time.perf_counter()
    attempts = []
    try:
        for task_record in tasks:
            task = from_record(task_record)
            for arm in arms:
                if source_identity() != manifest["sources"]:
                    raise RuntimeError("active stage source changed; original attempts retained")
                target = output / "attempts" / task.task_id / arm
                kwargs, retrieval = build(task, arm, training_record["tasks"], answer_record["targets"])
                if not (target.parent / (arm + "-RETRIEVAL.json")).exists():
                    write_new(target.parent / (arm + "-RETRIEVAL.json"), retrieval)
                status(output / "STATUS.json", {"at": now(), "status": "RUNNING", "completed_calls": len(attempts),
                       "planned_calls": manifest["planned_calls"], "current_task": task.task_id, "current_arm": arm,
                       "worker": owner, "elapsed_seconds": time.perf_counter() - started})
                result = call(task, target, **kwargs)
                attempts.append({"task_id": task.task_id, "arm": arm, "binding": result["binding"],
                                 "status": result["status"], "wall_seconds": result["wall_seconds"], "cost": result["cost"]})
        complete = {"finished_at": now(), "status": "COMPLETE", "manifest_sha256": digest(manifest),
                    "attempted_calls": len(attempts), "valid_calls": sum(row["status"] == "VALID" for row in attempts),
                    "invalid_calls": sum(row["status"] != "VALID" for row in attempts),
                    "attempts": attempts, "session_wall_seconds": time.perf_counter() - started,
                    "scope": "prediction producer complete; scientific comparison and final acceptance pending"}
        write_new(output / "COMPLETE.json", complete)
        status(output / "STATUS.json", {"at": now(), "status": "COMPLETE", "completed_calls": len(attempts)})
        return complete
    finally:
        release_gpu_lock()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--prepared", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--arms", nargs="+", default=["R0", "R1"])
    parser.add_argument("--maximum", type=int)
    args = parser.parse_args()
    try:
        result = run(args.prepared, args.output, args.arms, args.maximum)
        print(canonical({key: result[key] for key in ("status", "attempted_calls", "valid_calls", "invalid_calls")}), flush=True)
    except Exception as exc:
        failure = args.output / "FAILED.json"
        if not failure.exists():
            write_new(failure, {"at": now(), "error": repr(exc)})
        raise


if __name__ == "__main__":
    main()
