"""R2: two bounded direct forecasts, with explicit reader-only reconsideration.

DESIGN CHECK: LESSONS sections 2-5 and Stage 10 section 5. Both NULL and
ALTERNATIVE receive exactly the same original task and choices, two calls and
at most 768 generated tokens in total. The second call sees only its own first
unverified draft in addition to original evidence. It never sees an evaluator
answer or an induced maker program. Failed intermediate replies remain charged.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from dataclasses import replace
from pathlib import Path

from runners.stage9.process_identity import native_identity
from soundingline.gpulock import GPU_LOCK, acquire_gpu_lock, release_gpu_lock
from .contracts import digest
from .ollama import call, now, write_new
from .queue import read, source_identity as direct_source_identity, status
from .reader import from_record


def identity() -> dict:
    return {**direct_source_identity(), "runners/stage10/deliberation.py": hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}


def route(task, output):
    first = call(task, output / "draft", generated_tokens=384, context_tokens=16384)
    first_raw = read(output / "draft/RAW.json")
    scratchpad = {"origin": "this reader's earlier unverified response to the same task; not an observation",
                  "parse_status": first["status"], "draft": first_raw.get("message", {}).get("content", "")}
    second_task = replace(task, evidence={"original_source_evidence": task.evidence, "reader_scratchpad": scratchpad})
    if digest(second_task.evidence["original_source_evidence"]) != digest(task.evidence):
        raise AssertionError("reconsideration changed original source evidence")
    final = call(second_task, output / "reconsidered", generated_tokens=384, context_tokens=16384,
                 instruction="Reconsider the original evidence and the earlier reader draft. The draft may be wrong and is not an observed outcome. Return your final direct forecast without inventing a latent maker narrative.")
    generated = sum(row["cost"]["eval_count"] for row in (first, final))
    if generated > 768:
        raise ValueError("reconsideration exceeded its total output allowance")
    result = {"finished_at": now(), "arm": "R2", "task_id": task.task_id, "status": final["status"],
              "forecast": final["forecast"], "original_public_sha256": digest(task.public()),
              "calls": [{"binding": row["binding"], "status": row["status"], "cost": row["cost"],
                         "wall_seconds": row["wall_seconds"]} for row in (first, final)],
              "total_generated_tokens": generated, "maximum_generated_tokens": 768,
              "protocol": "two direct calls, 384 output tokens each; only own draft added on reconsideration"}
    if (output / "ROUTE.json").exists():
        saved = read(output / "ROUTE.json")
        for key in result.keys() - {"finished_at"}:
            if saved[key] != result[key]:
                raise ValueError("saved R2 route differs from retained calls")
        return saved
    write_new(output / "ROUTE.json", result)
    return result


def run(prepared: Path, output: Path):
    frozen = read(prepared / "FROZEN.json")
    public = read(prepared / "development-public.json")
    if digest(public) != frozen["public_sha256"]["development"]:
        raise ValueError("frozen development requests changed")
    tasks = [from_record(row) for row in public["tasks"]]
    manifest = {"schema": "stage10.r2-queue.1", "sources": identity(), "prepared_sha256": digest(frozen),
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
        acquire_gpu_lock("stage10-R2-development")
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
    parser.add_argument("--prepared", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        result = run(args.prepared, args.output)
        print(json.dumps({key: result[key] for key in ("status", "completed_tasks", "model_calls")}), flush=True)
    except Exception as exc:
        if not (args.output / "FAILED.json").exists():
            write_new(args.output / "FAILED.json", {"at": now(), "error": repr(exc)})
        raise


if __name__ == "__main__":
    main()
