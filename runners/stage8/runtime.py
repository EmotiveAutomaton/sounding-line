"""Stage 8 execution boundary: the Stage 7 interpreter capsule (runtime.py, unchanged) with
the Stage 8 reader package overlaid: the Stage 7 reader files are copied beside the Stage 8
ones (its worker as worker7.py, so the Stage 8 worker is the capsule's entry point and can
reuse the Stage 7 helpers), the shared log grammar rides along, and the capsule still sees
no torch, no repository, no oracle, no training corpus: the adapter is the loopback
server's, named by id and hash.

DESIGN CHECK (2026-09-04)
lessons read: LESSONS §5 (a capsule run without prediction.json or receipt.json is a
  failure with its stderr tail; every subprocess joined with a timeout), §3 (the probe task
  lists accesses that MUST raise, including the training corpus and the adapter directory).
gates: I03 (access): NULL of a broken boundary is any probe attempt that does not raise
  (fails DOWN, blocks the lock); ALTERNATIVE: every attempt raised. bands: exhaustive.
"""

from __future__ import annotations

import hashlib
import json
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from runners.stage7 import runtime as RT7                                          # noqa: E402
from runners.stage7.runtime import (BOOTSTRAP, cleanup, cleanup_unit, free_port,    # noqa: E402,F401
                                    run_capsule, scrubbed_env)
from soundingline.stage8 import S8, now_iso, write_json, update_registry           # noqa: E402

READER7 = REPO / "runners" / "stage7" / "reader"
READER8 = REPO / "runners" / "stage8" / "reader"
CAPSULES = S8 / "capsules"


def copied_sources(cap: Path) -> dict:
    """Hash the bytes actually copied, including inherited direct-reader helpers."""
    files = {p.relative_to(cap).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
             for p in sorted((cap / "reader").glob("*.py"))}
    files["bootstrap.py"] = hashlib.sha256((cap / "bootstrap.py").read_bytes()).hexdigest()
    return {"files": files, "sha256": hashlib.sha256(json.dumps(files, sort_keys=True).encode()).hexdigest()}


def materialize(cell: str, unit_ref: str, evidence: dict | None, task: dict, dom_params: dict | None = None) -> Path:
    safe = "".join(ch if (ch.isalnum() or ch in "._-") else "-" for ch in unit_ref)
    if len(safe) > 40:
        safe = safe[:28] + "-" + hashlib.sha1(unit_ref.encode("utf-8")).hexdigest()[:10]
    cap = CAPSULES / cell.replace("/", "_") / safe
    if cap.exists():
        shutil.rmtree(cap, ignore_errors=True)
    (cap / "reader").mkdir(parents=True, exist_ok=True)
    (cap / "out").mkdir(exist_ok=True)
    (cap / "tmp").mkdir(exist_ok=True)
    for p in sorted(READER7.glob("*.py")):
        name = "worker7.py" if p.name == "worker.py" else p.name
        shutil.copyfile(p, cap / "reader" / name)
    for p in sorted(READER8.glob("*.py")):
        shutil.copyfile(p, cap / "reader" / p.name)
    if evidence is not None:
        write_json(cap / "evidence.json", evidence)
    write_json(cap / "task.json", task)
    if dom_params is not None:
        write_json(cap / "dom.json", dom_params)
    (cap / "bootstrap.py").write_text(BOOTSTRAP, encoding="utf-8", newline="\n")
    receipt = copied_sources(cap)
    update_registry("SOURCE_MANIFEST", lambda previous: {**previous,
                    "capsule_closures": {**previous.get("capsule_closures", {}), receipt["sha256"]: receipt["files"]}})
    return cap


def probe(cell: str, endpoint: str, token: str, forbidden_paths: list[str], other_port: int) -> dict:
    task = {"probe": True, "forbidden_paths": forbidden_paths, "other_port": other_port,
            "forbidden_modules": ["runners", "soundingline", "torch", "numpy", "ctypes", "subprocess", "peft", "transformers"]}
    cap = materialize(cell, "probe", None, task)
    res = run_capsule(cap, endpoint, token, "", timeout_s=300)
    rec = res.get("receipt") or {}
    return {"at": now_iso(), "all_raised": bool(rec.get("all_raised")), "attempts": rec.get("attempts"),
            "sys_path": rec.get("sys_path"), "env_keys": rec.get("env_keys"), "rc": res["rc"],
            "stderr_tail": res["stderr_tail"], "access": res.get("access"), "interpreter": str(RT7.BASE_PY),
            "mechanism": "interpreter capsule: base python -I -S -E -B, capsule-only path, scrubbed env, raising audit hook; adapters loaded by the loopback server, hash in the manifest"}
