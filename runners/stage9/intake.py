"""Bounded acquisition only; never imports a reader or executes acquired source.

DESIGN CHECK: LESSONS sections 2 and 5; CONTROLS section 6; Stage 9 section 4.
NULL: forbidden redirect, oversized stream, traversal, symlink or decompression bomb
must fail before publication. ALTERNATIVE: complete allowed bytes round-trip by hash.
gates: all intake limits are conjunctive; bands: complete receipt or explicit refusal.
Existing fetch.MAX_BYTES is unchanged. Dataset permission requires a reviewed receipt.
"""
from __future__ import annotations

import argparse
from contextlib import contextmanager
from functools import wraps
import io
import json
import os
from pathlib import Path, PurePosixPath
import stat
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
import urllib.robotparser
import zipfile

from runners.stage9.common import ROOT, digest, file_hash, freeze, read, write

ASSET_LIMIT = 64 * 1024**2
TOTAL_DOWNLOAD = 512 * 1024**2
TOTAL_EXTRACTED = 1024**3
EXTRACTED_MEMBER_LIMIT = 256 * 1024**2
MAX_MEMBERS = 20000
CHUNK = 64 * 1024
USER_AGENT = "SoundingLine/0.1 (bounded public research intake)"
SUFFIXES = {".md", ".txt", ".py", ".jl", ".json", ".jsonl", ".csv", ".tsv", ".xml", ".tei", ".yaml", ".yml", ".toml", ".r", ".ipynb", ".html"}


class Refused(ValueError):
    pass


def transaction(method):
    @wraps(method)
    def wrapped(self, *args, **kwargs):
        with self.writer():
            return method(self, *args, **kwargs)
    return wrapped


def check_url(url, hosts):
    p = urllib.parse.urlsplit(url)
    if p.scheme != "https" or p.hostname not in hosts or p.username or p.password or p.port not in (None, 443):
        raise Refused("URL must be HTTPS on a reviewed host with no credentials or custom port")
    return p.hostname


def bounded_copy(source, destination, limit, charge=lambda n: None):
    """Read through EOF; the first byte beyond the limit fails, never truncates."""
    total = 0
    while True:
        block = source.read(min(CHUNK, limit - total + 1))
        if not block:
            return total
        charge(len(block))
        total += len(block)
        if total > limit:
            raise Refused("complete stream exceeds byte limit")
        destination.write(block)


class RedirectPolicy(urllib.request.HTTPRedirectHandler):
    def __init__(self, hosts, before):
        super().__init__()
        self.hosts, self.before = frozenset(hosts), before

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        # urllib calls this BEFORE issuing the redirected request.
        check_url(newurl, self.hosts)
        self.before(newurl)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def member_path(name):
    if not name or "\\" in name or ":" in name or "\x00" in name:
        raise Refused("unsafe archive member spelling")
    path = PurePosixPath(name)
    if path.is_absolute() or ".." in path.parts:
        raise Refused("archive member escapes staging")
    if any(part.lower().split(".")[0] in {"con", "prn", "aux", "nul", *[f"com{i}" for i in range(10)], *[f"lpt{i}" for i in range(10)]} or part.endswith((" ", ".")) for part in path.parts):
        raise Refused("ambiguous Windows archive member")
    return path


def inspect_zip(path):
    with zipfile.ZipFile(path) as archive:
        members = archive.infolist()
        if len(members) > MAX_MEMBERS:
            raise Refused("too many archive members")
        seen, total = set(), 0
        for member in members:
            p = member_path(member.filename)
            name = p.as_posix().casefold()
            if name in seen:
                raise Refused("duplicate/case-colliding archive member")
            seen.add(name)
            mode = member.external_attr >> 16
            if stat.S_ISLNK(mode) or (stat.S_IFMT(mode) not in (0, stat.S_IFREG, stat.S_IFDIR)) or member.flag_bits & 1:
                raise Refused("link, special, or encrypted archive member")
            total += member.file_size
            if total > TOTAL_EXTRACTED:
                raise Refused("declared archive expansion exceeds cap")
        return [{"path": m.filename, "bytes": m.file_size, "compressed": m.compress_size, "directory": m.is_dir()} for m in members]


class Intake:
    """Single fetch-process writer. Total budgets include failed requests and retries."""
    def __init__(self, directory=ROOT / "private/intake", hosts=()):
        self.directory = Path(directory)
        self.directory.mkdir(parents=True, exist_ok=True)
        self.hosts = frozenset(hosts)
        self.ledger_path = self.directory / "BUDGET.json"
        self.ledger = read(self.ledger_path) if self.ledger_path.exists() else {"downloaded": 0, "extracted": 0}
        self.last, self.robots = {}, {}
        self.opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), RedirectPolicy(self.hosts, self.before))
        self.resolving_robots = False

    @contextmanager
    def writer(self):
        """OS-owned lease releases on process death; no stale PID file takeover."""
        path = self.directory / "WRITER.lock"
        with path.open("a+b") as handle:
            if path.stat().st_size == 0:
                handle.write(b"0")
                handle.flush()
            handle.seek(0)
            try:
                if os.name == "nt":
                    import msvcrt
                    msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
                else:
                    import fcntl
                    fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except OSError as exc:
                raise Refused("another intake writer owns the campaign budget") from exc
            try:
                self.ledger = read(self.ledger_path) if self.ledger_path.exists() else {"downloaded": 0, "extracted": 0}
                yield
            finally:
                handle.seek(0)
                if os.name == "nt":
                    msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
                else:
                    fcntl.flock(handle, fcntl.LOCK_UN)

    def charge(self, kind, amount):
        self.ledger[kind] += amount
        write(self.ledger_path, self.ledger)
        if self.ledger[kind] > {"downloaded": TOTAL_DOWNLOAD, "extracted": TOTAL_EXTRACTED}[kind]:
            raise Refused("campaign intake budget exceeded")

    def before(self, url):
        host = check_url(url, self.hosts)
        delay = 2 - (time.monotonic() - self.last.get(host, 0))
        if delay > 0:
            time.sleep(delay)
        self.last[host] = time.monotonic()
        if self.resolving_robots or urllib.parse.urlsplit(url).path == "/robots.txt":
            return
        if host not in self.robots:
            robots_url = "https://" + host + "/robots.txt"
            # Same redirect policy and bounded streaming apply to robots itself.
            self.before(robots_url)
            try:
                self.resolving_robots = True
                with self.opener.open(urllib.request.Request(robots_url, headers={"User-Agent": USER_AGENT}), timeout=30) as response:
                    out = io.BytesIO()
                    bounded_copy(response, out, 1024**2, lambda n: self.charge("downloaded", n))
                parser = urllib.robotparser.RobotFileParser()
                parser.parse(out.getvalue().decode("utf-8", "replace").splitlines())
                self.robots[host] = parser
            except urllib.error.HTTPError as exc:
                if exc.code not in (404, 410):
                    raise Refused(f"robots unavailable: HTTP {exc.code}") from exc
                self.robots[host] = None
            finally:
                self.resolving_robots = False
        parser = self.robots[host]
        if parser is not None and not parser.can_fetch(USER_AGENT, url):
            raise Refused("robots disallows requested path")

    @transaction
    def fetch(self, url, rights, limit=ASSET_LIMIT):
        if not isinstance(rights, dict) or rights.get("reviewed") is not True or not rights.get("basis") or not rights.get("source"):
            raise Refused("reviewed permission basis and primary source required")
        if not 0 < limit <= ASSET_LIMIT:
            raise Refused("invalid asset limit")
        check_url(url, self.hosts)
        meta = self.directory / "receipts" / (digest(url) + ".json")
        if meta.exists():
            receipt = read(meta)
            if file_hash(self.directory / "objects" / receipt["sha256"]) != receipt["sha256"]:
                raise Refused("cached source hash mismatch")
            return receipt
        self.before(url)
        fd, tmp = tempfile.mkstemp(dir=self.directory, suffix=".partial")
        try:
            request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept-Encoding": "identity"})
            with os.fdopen(fd, "wb") as out, self.opener.open(request, timeout=60) as response:
                encoding = response.headers.get("Content-Encoding", "identity").lower()
                if encoding not in ("identity", ""):
                    raise Refused("HTTP content encoding refused; fetch a complete explicit archive")
                announced = response.headers.get("Content-Length")
                if announced and int(announced) > limit:
                    raise Refused("announced asset exceeds limit")
                count = bounded_copy(response, out, limit, lambda n: self.charge("downloaded", n))
                if announced and count != int(announced):
                    raise Refused("incomplete Content-Length")
                final_url, content_type = response.geturl(), response.headers.get("Content-Type")
            sha = file_hash(tmp)
            obj = self.directory / "objects" / sha
            obj.parent.mkdir(parents=True, exist_ok=True)
            os.replace(tmp, obj)
            receipt = {"requested_url": url, "final_url": final_url, "sha256": sha, "bytes": count,
                       "complete_eof": True, "content_type": content_type, "rights": rights, "fetched_at": time.time()}
            freeze(meta, receipt)
            return receipt
        finally:
            if os.path.exists(tmp):
                os.unlink(tmp)

    @transaction
    def extract_zip(self, sha, allowed_members):
        source = self.directory / "objects" / sha
        if file_hash(source) != sha:
            raise Refused("archive hash mismatch")
        inventory = inspect_zip(source)
        actual = {m["path"] for m in inventory if not m["directory"]}
        if not allowed_members or not set(allowed_members) <= actual:
            raise Refused("explicit existing member allowlist required")
        for name in allowed_members:
            p = member_path(name)
            if p.suffix.lower() not in SUFFIXES and p.name.upper() not in ("LICENSE", "COPYING", "NOTICE"):
                raise Refused("member is not an allowed source/data format")
        dest = self.directory / "materialized" / sha
        prior_path = dest / "MATERIALIZATION.json"
        prior = read(prior_path) if prior_path.exists() else {"materialized": {}}
        out_receipts = dict(prior["materialized"])
        with zipfile.ZipFile(source) as archive:
            for name in sorted(allowed_members):
                target = dest.joinpath(*member_path(name).parts)
                target.parent.mkdir(parents=True, exist_ok=True)
                if not target.resolve().is_relative_to(dest.resolve()) or any(p.is_symlink() for p in (target, *target.parents)):
                    raise Refused("materialization path escapes staging")
                if name in out_receipts:
                    if file_hash(target) != out_receipts[name]["sha256"]:
                        raise Refused("cached materialization hash mismatch")
                    continue
                fd, tmp = tempfile.mkstemp(dir=target.parent, suffix=".partial")
                try:
                    with os.fdopen(fd, "wb") as out, archive.open(name) as stream:
                        # Downloaded assets and expanded members have different caps.
                        # The named B-roll release has an 84 MB expanded CSV inside an
                        # 18 MB ZIP; the approved 1 GiB aggregate expansion still binds.
                        count = bounded_copy(stream, out, EXTRACTED_MEMBER_LIMIT, lambda n: self.charge("extracted", n))
                    os.replace(tmp, target)
                    out_receipts[name] = {"sha256": file_hash(target), "bytes": count}
                finally:
                    if os.path.exists(tmp):
                        os.unlink(tmp)
        receipt = {"archive": sha, "inventory": inventory, "materialized": out_receipts, "executed": False}
        write(dest / "MATERIALIZATION.json", receipt)
        return receipt


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("request", help="reviewed JSON request: URL, hosts, rights; one asset per process")
    parser.add_argument("--root", type=Path, default=ROOT / "private/intake")
    args = parser.parse_args()
    request = read(args.request)
    result = Intake(args.root, request["hosts"]).fetch(request["url"], request["rights"], request.get("limit", ASSET_LIMIT))
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
