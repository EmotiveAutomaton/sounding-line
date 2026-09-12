"""Serial source-separated reading development/evaluation producers.

DESIGN CHECK: LESSONS2-5. Both hypotheses retain source-bound literal pilot
admission, complete rosters and all invalid outputs. No target labels are read.
Completed child replay is inherited; this chain adds no model-facing behavior.
"""
from __future__ import annotations
import argparse
import hashlib
from pathlib import Path
from . import reading_routes
from .contracts import digest
from .ollama import now, write_new
from .queue import read, status


def run(root, prepared, pilot, output):
    sources = {**reading_routes.identity(root), "runners/stage10/reading_science_chain.py": hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    manifest = {"sources": sources, "prepared_sha256": digest(read(prepared / "FROZEN.json")),
                "pilot_sha256": digest(read(pilot)), "phases": ["development", "evaluation"],
                "scope": "complete prediction producers only; source-separated previously exposed cases"}
    output.mkdir(parents=True, exist_ok=True)
    if (output / "MANIFEST.json").exists():
        if read(output / "MANIFEST.json") != manifest:
            raise ValueError("reading chain source changed")
    else:
        write_new(output / "MANIFEST.json", manifest)
    complete = (output / "COMPLETE.json").exists()
    results = {}
    for phase in manifest["phases"]:
        if any(hashlib.sha256(Path(p).read_bytes()).hexdigest() != h for p, h in sources.items() if p != "exported-source-closure"):
            raise ValueError("reading chain source changed during execution")
        if complete and not (output / phase / "COMPLETE.json").exists():
            raise ValueError("completed reading phase missing; no new calls")
        status(output / "STATUS.json", {"at": now(), "status": "RUNNING", "active": phase, "finished": list(results)})
        r = reading_routes.run(root, prepared, output / phase, phase, pilot)
        results[phase] = {"sha256": digest(r), "status": r["status"], "model_calls": r["model_calls"]}
    result = {"at": now(), "status": "COMPLETE", "manifest_sha256": digest(manifest), "phases": results,
              "target_outcomes_opened": False, "scope": manifest["scope"]}
    if complete:
        saved = read(output / "COMPLETE.json")
        if any(saved[k] != result[k] for k in result.keys() - {"at"}):
            raise ValueError("completed reading chain changed")
        return saved
    write_new(output / "COMPLETE.json", result)
    status(output / "STATUS.json", {"at": now(), "status": "COMPLETE", "finished": list(results)})
    return result


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    for name in ("public-root", "prepared", "pilot", "output"):
        p.add_argument("--" + name, type=Path, required=True)
    a = p.parse_args()
    try:
        run(a.public_root, a.prepared, a.pilot, a.output)
    except Exception as exc:
        if not (a.output / "FAILED.json").exists():
            write_new(a.output / "FAILED.json", {"at": now(), "error": repr(exc)})
        raise
