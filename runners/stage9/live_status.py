"""Bounded reads of a concurrently replaced scheduler record.

DESIGN CHECK: LESSONS 3--5; CONTROLS 6.
NULL: permanent denial, missing or malformed evidence must still fail.
ALTERNATIVE: temporary Windows access/sharing errors resolve at the same path.
gates: eight attempts, then original error; no alternate path or evidence fallback.
Historical preparation-source bytes remain unchanged by this scheduler wrapper.
"""
import os
from pathlib import Path
import time

from .common import read as read_once


def read(path):
    """Retry only Windows access/sharing errors, for at most 0.55 seconds of waits."""
    path = Path(path)
    for attempt in range(8):
        try:
            return read_once(path)
        except OSError as exc:
            retryable = os.name == 'nt' and (
                exc.errno == 13 or getattr(exc, 'winerror', None) in (5, 32, 33)
            )
            if not retryable or attempt == 7:
                raise
            time.sleep(0.025 * min(4, attempt + 1))
