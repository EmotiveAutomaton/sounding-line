"""Stage 7 execution boundary (brief §6.2, §14; his ruling 2026-09-02: the interpreter
capsule). Every non-oracle reader runs in a FRESH process whose working capsule holds only
the frozen reader package, the immutable contract, one visible-evidence file, one task
file, the frozen DOM parameters, and a write-only output directory. The process is the
BASE interpreter (never the venv) in isolated mode (-I -S -E -B: no site, no environment,
no bytecode), its path reduced to the capsule plus the standard library, its environment
scrubbed to what Windows needs to start a process plus the loopback endpoint, and an
IRREMOVABLE audit hook (CPython guarantees hooks cannot be removed once added) that
RAISES on any open outside the capsule and the standard library, any write outside the
capsule's out/ and tmp/, any socket other than the loopback endpoint, any subprocess,
exec, spawn, ctypes load, environment mutation, directory listing outside the capsule,
or import whose file lies outside the capsule and the standard library. The access
receipt every run returns counts what the hook saw. Honest label: an interpreter-level
boundary; the operating system does not deny the files, the interpreter does, which is
why I04/X04 fire the forbidden attempts INSIDE the real reader process and require every
one to raise.

DESIGN CHECK (2026-09-02)
lessons read: LESSONS §5 (a clean exit that wrote no produce is a failure: a capsule run
  without prediction.json or receipt.json is an error with its stderr tail; every
  subprocess is joined with a timeout; kill by pid on timeout), §3 (the criterion can
  fail: the probe task lists accesses that MUST raise, and a probe with no raised
  attempt is the defect the receipt reports).
gates: the access gate (I04): NULL of a broken boundary is any probe attempt that does
  not raise; ALTERNATIVE (the boundary holds) is every attempt raised; failure direction:
  a single un-raised attempt fails the gate DOWNWARD (blocks the scientific lock). bands:
  exhaustive (all raised, or not).
"""

from __future__ import annotations

import json
import hashlib
import os
import shutil
import socket
import subprocess
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from soundingline.stage7 import S7, now_iso, read_json, write_json                # noqa: E402

READER_SRC = REPO / "runners" / "stage7" / "reader"
CAPSULES = S7 / "capsules"
BASE_PY = Path(sys.base_prefix) / "python.exe"
if not BASE_PY.exists():
    BASE_PY = Path(sys.base_prefix) / "bin" / "python3"

BOOTSTRAP = r'''
import os, sys
CAP = os.path.normcase(os.path.abspath(os.getcwd()))
STD = [os.path.normcase(os.path.abspath(sys.base_prefix)), os.path.normcase(os.path.abspath(sys.exec_prefix))]
OUT = os.path.join(CAP, "out")
TMP = os.path.join(CAP, "tmp")
_ep = os.environ.get("S7_ENDPOINT", "http://127.0.0.1:0")
_hp = _ep.split("//", 1)[-1].split("/", 1)[0]
HOST, PORT = _hp.split(":")[0], int(_hp.split(":")[1])
DENY_MODULES = ("runners", "soundingline", "constructor", "scoring", "oracle", "torch", "numpy", "transformers", "ctypes", "subprocess", "multiprocessing")
COUNTS = {"allowed": 0, "denied": 0, "events": {}}

def _norm(p):
    if isinstance(p, bytes):
        p = p.decode("utf-8", "replace")
    return os.path.normcase(os.path.abspath(str(p)))

def _under(p, roots):
    p = _norm(p)
    return any(p == r or p.startswith(r.rstrip("\\/") + os.sep) for r in roots)

def _deny(event, why):
    COUNTS["denied"] += 1
    COUNTS["events"][event] = COUNTS["events"].get(event, 0) + 1
    raise RuntimeError("capsule boundary: %s (%s)" % (event, why))

WRITE_FLAGS = os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_APPEND | os.O_TRUNC

def _hook(event, args):
    if event == "open":
        path, mode, flags = args
        if path is None or isinstance(path, int):
            return
        writing = (mode and any(c in mode for c in "wax+")) or (flags and (flags & WRITE_FLAGS))
        if writing:
            if not _under(path, [OUT, TMP]):
                _deny(event, "write outside out/ and tmp/: %s" % path)
        elif not _under(path, [CAP] + STD):
            _deny(event, "read outside the capsule: %s" % path)
        COUNTS["allowed"] += 1
    elif event in ("os.listdir", "os.scandir", "glob.glob", "os.walk"):
        p = args[0] if args else None
        if p is not None and not isinstance(p, int) and not _under(p, [CAP] + STD):
            _deny(event, str(p))
    elif event in ("os.mkdir", "os.rename", "os.remove", "os.unlink", "os.rmdir", "os.truncate", "shutil.rmtree", "shutil.move", "shutil.copyfile"):
        for p in args[:2]:
            if isinstance(p, (str, bytes)) and not _under(p, [OUT, TMP]):
                _deny(event, str(p))
    elif event == "socket.connect":
        addr = args[1] if len(args) > 1 else None
        if not (isinstance(addr, tuple) and len(addr) >= 2 and addr[0] in (HOST, "127.0.0.1", "localhost") and int(addr[1]) == PORT):
            _deny(event, str(addr))
    elif event == "socket.getaddrinfo":
        host = args[0]
        if host not in (HOST, "127.0.0.1", "localhost"):
            _deny(event, str(host))
    elif event in ("subprocess.Popen", "os.system", "os.exec", "os.spawn", "os.fork", "os.posix_spawn",
                   "os.startfile", "ctypes.dlopen", "ctypes.cdll", "ctypes.seh_exception", "os.putenv",
                   "os.unsetenv", "os.chdir", "os.kill", "os.killpg", "winreg.OpenKey", "winreg.CreateKey",
                   "webbrowser.open", "socket.bind", "socket.sendto", "os.link", "os.symlink", "os.chmod"):
        _deny(event, "forbidden operation")
    elif event == "import":
        module, filename = args[0], args[1]
        top = str(module).split(".")[0]
        if top in DENY_MODULES:
            _deny(event, str(module))
        if filename and not _under(filename, [CAP] + STD):
            _deny(event, "%s from %s" % (module, filename))
    elif event == "sys.addaudithook":
        _deny(event, "a second hook")

sys.addaudithook(_hook)
sys.path[:] = [CAP] + [p for p in sys.path if p and _under(p, STD)]
import json
try:
    from reader import worker
    rc = worker.main()
finally:
    try:
        os.makedirs(OUT, exist_ok=True)
        with open(os.path.join(OUT, "access.json"), "w", encoding="utf-8") as fh:
            json.dump({"counts": COUNTS, "sys_path": sys.path, "cwd": CAP, "env": sorted(os.environ)}, fh, indent=1, sort_keys=True)
    except Exception:
        pass
sys.exit(rc)
'''


def free_port() -> int:
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    p = s.getsockname()[1]
    s.close()
    return p


def materialize(cell: str, unit_ref: str, evidence: dict | None, task: dict, dom_params: dict | None = None) -> Path:
    """Build one capsule: reader package copied file by file (never the repository),
    contracts, evidence, task, DOM parameters, bootstrap, out/ and tmp/."""
    safe = "".join(ch if (ch.isalnum() or ch in "._-") else "-" for ch in unit_ref)
    if len(safe) > 40:
        # the Windows path limit: a long root plus a confirmation-lane unit plus an external
        # arm name crossed 260 characters and CreateProcess refused the capsule as cwd
        safe = safe[:28] + "-" + hashlib.sha1(unit_ref.encode("utf-8")).hexdigest()[:10]
    cap = CAPSULES / cell.replace("/", "_") / safe
    if cap.exists():
        shutil.rmtree(cap, ignore_errors=True)
    (cap / "reader").mkdir(parents=True, exist_ok=True)
    (cap / "out").mkdir(exist_ok=True)
    (cap / "tmp").mkdir(exist_ok=True)
    for p in sorted(READER_SRC.glob("*.py")):
        shutil.copyfile(p, cap / "reader" / p.name)
    if evidence is not None:
        write_json(cap / "evidence.json", evidence)
    write_json(cap / "task.json", task)
    if dom_params is not None:
        write_json(cap / "dom.json", dom_params)
    (cap / "bootstrap.py").write_text(BOOTSTRAP, encoding="utf-8", newline="\n")
    return cap


def scrubbed_env(cap: Path, endpoint: str, token: str, model: str) -> dict:
    env = {"S7_ENDPOINT": endpoint, "S7_TOKEN": token, "S7_MODEL": model,
           "TEMP": str(cap / "tmp"), "TMP": str(cap / "tmp"), "PATH": ""}
    for k in ("SystemRoot", "SYSTEMROOT", "windir", "WINDIR", "SystemDrive", "COMSPEC"):
        if k in os.environ:
            env[k] = os.environ[k]
    if os.name != "nt":
        env["PATH"] = "/usr/bin:/bin"
    return env


def run_capsule(cap: Path, endpoint: str, token: str, model: str, timeout_s: float = 1800.0) -> dict:
    """Run the capsule's bootstrap in the base interpreter under isolated mode; collect
    the prediction, the access receipt, the error, and the stderr tail."""
    t0 = time.time()
    cmd = [str(BASE_PY), "-I", "-S", "-E", "-B", "-X", "utf8", "bootstrap.py"]
    try:
        proc = subprocess.run(cmd, cwd=str(cap), env=scrubbed_env(cap, endpoint, token, model),
                              capture_output=True, text=True, timeout=timeout_s)
        rc, err = proc.returncode, proc.stderr[-2000:]
    except subprocess.TimeoutExpired as e:
        rc, err = 124, f"timeout after {timeout_s}s: {str(e)[-500:]}"
    out = {"rc": rc, "wall_s": round(time.time() - t0, 3), "stderr_tail": err, "capsule": str(cap)}
    for name in ("prediction", "receipt", "error", "access"):
        p = cap / "out" / f"{name}.json"
        out[name] = read_json(p) if p.exists() else None
    return out


def probe(cell: str, endpoint: str, token: str, forbidden_paths: list[str], other_port: int) -> dict:
    """I04/X04: the forbidden-access probe inside a real capsule process."""
    task = {"probe": True, "forbidden_paths": forbidden_paths, "other_port": other_port,
            "forbidden_modules": ["runners", "soundingline", "torch", "numpy", "ctypes", "subprocess"]}
    cap = materialize(cell, "probe", None, task)
    res = run_capsule(cap, endpoint, token, "", timeout_s=300)
    rec = res.get("receipt") or {}
    return {"at": now_iso(), "all_raised": bool(rec.get("all_raised")), "attempts": rec.get("attempts"),
            "sys_path": rec.get("sys_path"), "env_keys": rec.get("env_keys"), "rc": res["rc"],
            "stderr_tail": res["stderr_tail"], "access": res.get("access"), "interpreter": str(BASE_PY),
            "mechanism": "interpreter capsule: base python -I -S -E -B, capsule-only path, scrubbed env, raising audit hook"}


def cleanup(cell: str) -> None:
    d = CAPSULES / cell.replace("/", "_")
    if d.exists():
        shutil.rmtree(d, ignore_errors=True)


def cleanup_unit(cap: Path) -> None:
    """A finished capsule is removed (its prediction and access receipt were copied out);
    disk stays bounded across thousands of units."""
    try:
        shutil.rmtree(cap, ignore_errors=True)
    except OSError:
        pass
