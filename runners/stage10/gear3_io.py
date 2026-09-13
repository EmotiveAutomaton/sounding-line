"""Durable bounded attempts and complete checked archives for the cloud adapter.

DESIGN CHECK: LESSONS3-5. Null and alternative preserve the same raw evidence.
Missing/corrupt members, changed reservations, symlinks and escaping paths refuse.
Interrupted requests remain uncertain; completion never substitutes for raw bytes.
"""
from __future__ import annotations
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import stat
import time
import zipfile
from .contracts import canonical, digest

_ACTIVE = ContextVar("gear3_attempt_journal", default=None)
ARCHIVE_MANIFEST = "__gear3_archive_manifest__.json"
MAX_ARCHIVE_BYTES = 1024 * 1024 * 1024


@dataclass
class AttemptJournal:
    root: Path
    reservation: dict
    commit: object
    prepared: str | None = None

    def before_write(self, path: Path, value: dict):
        if not path.resolve().is_relative_to(self.root.resolve()):
            raise ValueError("attempt write escapes invocation output")
        if path.name == "REQUEST.json":
            if time.time() >= self.reservation["expires_at"] - 5:
                raise TimeoutError("original invocation deadline reached before request")
            value = {**value, "cloud_reservation": self.reservation}
        return value

    def after_write(self, path: Path, value: dict):
        self.commit()  # backend durability, not merely container-local fsync
        if path.name == "REQUEST.json":
            self.prepared = digest(value["request"])

    def before_api(self, path: str, payload, timeout):
        remaining = self.reservation["expires_at"] - time.time() - 5
        if remaining < 1:
            raise TimeoutError("original invocation deadline reached")
        if path == "/api/chat":
            if self.prepared != digest(payload):
                raise ValueError("model request has no matching durable reservation")
            self.prepared = None  # no duplicate transmission even on ambiguous failure
        return min(timeout, int(remaining))


@contextmanager
def durable_attempts(root: Path, reservation: dict, commit):
    if reservation.get("reserved_cents", 0) <= 0 or not reservation.get("invocation_id"):
        raise ValueError("paid attempts require a concrete reservation")
    token = _ACTIVE.set(AttemptJournal(root, reservation, commit))
    try:
        yield
    finally:
        _ACTIVE.reset(token)


def journal():
    return _ACTIVE.get()


def inventory(root: Path):
    found = {}
    for path in sorted(root.rglob("*")):
        if path.is_symlink(): raise ValueError("archive symlink forbidden")
        if path.is_file():
            name = path.relative_to(root).as_posix()
            if name == ARCHIVE_MANIFEST: raise ValueError("reserved archive member")
            raw = path.read_bytes()
            found[name] = {"bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}
    return found


def make_archive(root: Path, target: Path):
    if target.resolve().is_relative_to(root.resolve()):
        raise ValueError("archive must be outside its source tree")
    files = inventory(root)
    if sum(r["bytes"] for r in files.values()) > MAX_ARCHIVE_BYTES:
        raise ValueError("complete archive exceeds bounded transport; retain original files")
    target.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(target, "x", compression=zipfile.ZIP_DEFLATED) as z:
        for name in files: z.write(root/name, name)
        z.writestr(ARCHIVE_MANIFEST, canonical({"schema": "gear3.archive.1", "files": files}))
    return verify_archive(target)


def verify_archive(path: Path, destination: Path | None = None):
    with zipfile.ZipFile(path) as z:
        members = z.infolist()
        if len({i.filename for i in members}) != len(members): raise ValueError("duplicate archive members")
        if sum(i.file_size for i in members) > MAX_ARCHIVE_BYTES + 10000000:
            raise ValueError("archive size exceeds transport bound")
        manifest = json.loads(z.read(ARCHIVE_MANIFEST))
        if manifest["schema"] != "gear3.archive.1" or set(z.namelist()) != set(manifest["files"]) | {ARCHIVE_MANIFEST}:
            raise ValueError("archive member roster differs")
        # Verify every member before extracting any byte.
        for item in members:
            n=PurePosixPath(item.filename)
            if n.is_absolute() or ".." in n.parts or "\\" in item.filename or ":" in item.filename or stat.S_ISLNK(item.external_attr >> 16):
                raise ValueError("unsafe archive member")
            if item.filename == ARCHIVE_MANIFEST: continue
            raw=z.read(item.filename); expected=manifest["files"][item.filename]
            if len(raw) != expected["bytes"] or hashlib.sha256(raw).hexdigest() != expected["sha256"]:
                raise ValueError("archive content changed")
            if destination is not None:
                out=destination.joinpath(*n.parts)
                if not out.resolve().is_relative_to(destination.resolve()): raise ValueError("archive path escapes destination")
                if out.exists() and out.read_bytes() != raw: raise ValueError("retrieval would overwrite prior evidence")
        if destination is not None:
            for name in manifest["files"]:
                out=destination/PurePosixPath(name)
                if not out.exists():
                    out.parent.mkdir(parents=True,exist_ok=True)
                    with out.open("xb") as stream:
                        stream.write(z.read(name)); stream.flush(); os.fsync(stream.fileno())
    return {"archive_sha256": hashlib.sha256(path.read_bytes()).hexdigest(), "files": manifest["files"]}
