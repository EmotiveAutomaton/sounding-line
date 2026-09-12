"""Serial frozen human development/evaluation prediction production.

DESIGN CHECK: LESSONS2-5. Both phases retain source-bound literal admission,
actual native ownership and all invalid rows. No target outcomes are opened.
Complete child replay is inherited; no new model-facing behavior is added.
"""
import argparse
import hashlib
from pathlib import Path
from . import human_routes
from .contracts import digest
from .ollama import now, write_new
from .queue import read, status


def run(prepared, pilot, output):
    sources = {**human_routes.identity(), "runners/stage10/human_science_chain.py": hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    manifest = {"sources": sources, "prepared_sha256": digest(read(prepared / "FROZEN.json")),
                "pilot_sha256": digest(read(pilot)), "phases": ["development", "evaluation"]}
    output.mkdir(parents=True, exist_ok=True)
    if (output / "MANIFEST.json").exists():
        if read(output / "MANIFEST.json") != manifest:
            raise ValueError("human chain source changed")
    else:
        write_new(output / "MANIFEST.json", manifest)
    complete = (output / "COMPLETE.json").exists()
    results = {}
    for phase in manifest["phases"]:
        if any(hashlib.sha256(Path(p).read_bytes()).hexdigest() != h for p, h in sources.items()):
            raise ValueError("human chain source changed during execution")
        if complete and not (output / phase / "COMPLETE.json").exists():
            raise ValueError("completed human phase missing; no new calls")
        if not complete:
            status(output / "STATUS.json", {"at": now(), "status": "RUNNING", "active": phase, "finished": list(results)})
        r = human_routes.run(prepared, output / phase, phase, pilot)
        results[phase] = {"sha256": digest(r), "status": r["status"], "model_calls": r["model_calls"]}
    result = {"at": now(), "status": "COMPLETE", "manifest_sha256": digest(manifest), "phases": results,
              "target_outcomes_opened": False, "scope": "complete prediction producers only; scientific comparisons pending"}
    if complete:
        saved = read(output / "COMPLETE.json")
        if any(saved[k] != result[k] for k in result.keys() - {"at"}):
            raise ValueError("completed human chain changed")
        return saved
    write_new(output / "COMPLETE.json", result)
    status(output / "STATUS.json", {"at": now(), "status": "COMPLETE", "finished": list(results)})
    return result


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    for name in ("prepared", "pilot", "output"):
        p.add_argument("--" + name, type=Path, required=True)
    a = p.parse_args()
    try:
        run(a.prepared, a.pilot, a.output)
    except Exception as exc:
        if not (a.output / "FAILED.json").exists():
            write_new(a.output / "FAILED.json", {"at": now(), "error": repr(exc)})
        raise
