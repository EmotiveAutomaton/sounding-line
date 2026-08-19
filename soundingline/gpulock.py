"""One GPU job at a time, whatever shard or runner asks.

Extracted from run_scholawrite.py (NIGHT12) so every GPU-hungry runner serializes through the
same file, results/.gpu.lock. Stale after NINE hours: the window must exceed the longest
queued training or a live holder's lock is reclaimed mid-run and two trainings collide on the
card (the 5h window sat under the 5-7h framework arms and produced the deberta OOM,
2026-08-14). A crashed holder's lock is reclaimed after the window. Release is registered
atexit and runs on normal interpreter death, which covers stage kills by the queue but not
hard taskkills, hence the staleness rule.
"""

from __future__ import annotations

import atexit
import os
import time
from pathlib import Path

GPU_LOCK = Path(__file__).resolve().parents[1] / "results" / ".gpu.lock"
# 9h reclaimed a LIVE 620-minute deberta rung at hour nine and put an ollama generation on
# the card beside it (2026-08-17), the same failure mode as the original 5h window. The
# window must exceed the longest queued stage's REAL runtime (est x 2-3 underestimate), so
# it tracks the queue's longest est, currently 620 min -> 22h.
STALE_S = 22 * 3600


def release_gpu_lock() -> None:
    try:
        GPU_LOCK.unlink()
    except OSError:
        pass


def acquire_gpu_lock(tag: str = "") -> None:
    GPU_LOCK.parent.mkdir(parents=True, exist_ok=True)
    while True:
        # reentrant by pid: a process re-acquiring under a new tag already owns the card.
        # Without this, a runner taking per-arm locks deadlocks on ITSELF (five hours of
        # a live gear window, 2026-08-19; LESSONS §5)
        try:
            holder = GPU_LOCK.read_text(encoding="utf-8").split()
            if holder and int(holder[0]) == os.getpid():
                GPU_LOCK.write_text(f"{os.getpid()} {tag}", encoding="utf-8")
                return
        except (OSError, ValueError):
            pass
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
