"""Durable Stage 9 identities and atomic records.

DESIGN CHECK: LESSONS sections 3 and 5; CONTROLS section 6.
NULL: interrupted writes or changed inputs must never count as completed work.
ALTERNATIVE: identical completed units resume once, with original source identity.
gates: missing/mismatched identity raises; bands: exact match or invalid, no fallback.
"""
from __future__ import annotations

import hashlib
import json
import math
import os
from pathlib import Path
import tempfile
import time

REPO = Path(__file__).resolve().parents[2]
ROOT = Path(os.environ.get("S9_ROOT", str(REPO / "results/phase_2_4_stage_9"))).resolve()
SPEC = REPO / "SOUNDING_LINE_STAGE9_FIVE_DAY_SPEC_2026-09-06.md"
VERSION = "stage9.1"


def canonical(obj):
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def digest(obj):
    return hashlib.sha256(canonical(obj).encode("utf-8")).hexdigest()


def file_hash(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def read(path):
    with Path(path).open(encoding="utf-8") as stream:
        return json.load(stream)


def write(path, obj):
    """Unique temporary file; atomic replace; last readable record survives failure."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = canonical(obj) + "\n"
    fd, name = tempfile.mkstemp(prefix="." + path.name + ".", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        for attempt in range(40):
            try:
                os.replace(name, path)
                break
            except OSError as exc:
                if (exc.errno not in (13, 22) and getattr(exc, "winerror", None) not in (5, 32, 33)) or attempt == 39:
                    raise
                time.sleep(0.05 * min(5, attempt + 1))
    finally:
        if os.path.exists(name):
            os.unlink(name)


def freeze(path, obj):
    path = Path(path)
    if path.exists():
        if read(path) != obj:
            raise ValueError(f"frozen record mismatch: {path}")
    else:
        write(path, obj)
    return file_hash(path)


def distribution(values):
    if not values or any(not isinstance(v, (int, float)) or isinstance(v, bool) or not math.isfinite(v) or v < 0 for v in values.values()):
        raise ValueError("invalid raw distribution")
    if abs(math.fsum(values.values()) - 1) > 1e-6:
        raise ValueError("distribution must already sum to one")
    return values


def closure(paths):
    """Hash actual regular files, rejecting symlinks; no inferred historical hashes."""
    found = {}
    for item in paths:
        item = Path(item)
        if not item.exists():
            raise FileNotFoundError(item)
        entries = sorted(item.rglob("*")) if item.is_dir() else [item]
        for path in entries:
            if path.is_symlink():
                raise ValueError(f"source symlink: {path}")
            if path.is_file() and "__pycache__" not in path.parts and path.suffix != ".pyc":
                key = path.relative_to(REPO).as_posix() if path.is_relative_to(REPO) else str(path)
                found[key] = file_hash(path)
    return {"files": found, "sha256": digest(found)}


class Units:
    """One writer per cell; complete units are independent atomic records."""
    def __init__(self, directory, identity):
        self.directory = Path(directory)
        self.identity = digest(identity)
        freeze(self.directory / "IDENTITY.json", identity)

    def path(self, key):
        return self.directory / "units" / (digest(key) + ".json")

    def get(self, key):
        path = self.path(key)
        if not path.exists():
            return None
        obj = read(path)
        if obj.get("identity") != self.identity or obj.get("key") != key or obj.get("complete") is not True:
            raise ValueError("unit completion identity mismatch")
        return obj["row"]

    def put(self, key, row):
        old = self.get(key)
        if old is not None and old != row:
            raise ValueError("refusing to overwrite completed unit")
        freeze(self.path(key), {"identity": self.identity, "key": key, "complete": True, "row": row})

    def all(self):
        return [read(p) for p in sorted((self.directory / "units").glob("*.json"))]
