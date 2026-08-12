"""One GPU job at a time, whatever shard or runner asks.

Extracted from run_scholawrite.py (NIGHT12) so every GPU-hungry runner serializes through the
same file, results/.gpu.lock. Stale after five hours (no training here runs that long; a crashed
holder's lock is reclaimed). Release is registered atexit and runs on normal interpreter death,
which covers stage kills by the queue but not hard taskkills, hence the staleness rule.
"""

from __future__ import annotations

import atexit
import os
import time
from pathlib import Path

GPU_LOCK = Path(__file__).resolve().parents[1] / "results" / ".gpu.lock"
STALE_S = 5 * 3600


def release_gpu_lock() -> None:
    try:
        GPU_LOCK.unlink()
    except OSError:
        pass


def acquire_gpu_lock(tag: str = "") -> None:
    GPU_LOCK.parent.mkdir(parents=True, exist_ok=True)
    while True:
        try:
            fd = os.open(GPU_LOCK, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            os.write(fd, f"{os.getpid()} {tag}".encode())
            os.close(fd)
            atexit.register(release_gpu_lock)
            return
        except FileExistsError:
            try:
                age = time.time() - GPU_LOCK.stat().st_mtime
            except OSError:
                continue
            if age > STALE_S:
                release_gpu_lock()
                continue
            print("  gpu lock held, waiting 120s", flush=True)
            time.sleep(120)
