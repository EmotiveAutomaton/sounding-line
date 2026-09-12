"""Recorded invocation of the finite public Ghost hypothesis executor.

DESIGN CHECK: LESSONS2-5. Under NULL and ALTERNATIVE, source substitution,
changed frames and private access fail. Candidate fit is not historical truth.
"""
from __future__ import annotations
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
from .contracts import canonical, digest
from .ghost import task_from
from .ollama import now, write_new


def source_identity(root):
    consumer = root / "public/consumer"
    inventory = json.loads((root / "ARCHIVE_MEMBER_MANIFEST.json").read_text(encoding="utf8"))["files"]
    sources = {}
    for p in [consumer / "consumer.py", *sorted((consumer / "v16_reference").glob("*.py"))]:
        actual = hashlib.sha256(p.read_bytes()).hexdigest()
        member = p.relative_to(root).as_posix()
        if actual != inventory[member]["sha256"]:
            raise ValueError("exported executor source differs from archive manifest")
        sources[p.relative_to(consumer).as_posix()] = actual
    return {"public_sources": sources, "wrapper_sha256": hashlib.sha256(Path(__file__).with_name("executor_worker.py").read_bytes()).hexdigest()}


def execute(root: Path, envelope: dict, candidates: list, output: Path):
    task_from(envelope)  # Strict public boundary before handing input to child.
    frame = {"envelope": envelope, "candidates": candidates}
    sources = source_identity(root)
    binding = digest({"frame": frame, "sources": sources})
    if (output / "EXECUTION.json").exists():
        saved = json.loads((output / "EXECUTION.json").read_text(encoding="utf8"))
        original = json.loads((output / "INPUT.json").read_text(encoding="utf8"))
        raw = json.loads((output / "RAW.json").read_text(encoding="utf8"))
        if saved["binding"] != binding or original != {"binding": binding, "frame": frame, "sources": sources} or saved["raw_sha256"] != digest(raw):
            raise ValueError("saved executor binding changed")
        if saved["response"] != json.loads(raw["stdout"].splitlines()[1]):
            raise ValueError("saved executor response differs from raw output")
        return saved
    output.mkdir(parents=True, exist_ok=False)
    write_new(output / "INPUT.json", {"binding": binding, "frame": frame, "sources": sources})
    cmd = [sys.executable, "-s", "-B", "-u", str(Path(__file__).with_name("executor_worker.py").resolve()), str(root.resolve())]
    proc = subprocess.run(cmd, input=canonical(frame)+"\n"+canonical({"operation": "shutdown"})+"\n",
                          capture_output=True, text=True, encoding="utf8", timeout=120,
                          creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0)
    raw = {"command": cmd, "returncode": proc.returncode, "stdout": proc.stdout, "stderr": proc.stderr}
    write_new(output / "RAW.json", raw)
    lines = [json.loads(line) for line in proc.stdout.splitlines()]
    if proc.returncode or len(lines) != 2 or lines[0].get("ready") is not True or lines[0]["sources"] != sources["public_sources"] or lines[0]["wrapper_sha256"] != sources["wrapper_sha256"]:
        raise ValueError("executor source or output receipt mismatch")
    receipt = {"at": now(), "binding": binding, "raw_sha256": digest(raw), "response": lines[1]}
    write_new(output / "EXECUTION.json", receipt)
    return receipt
