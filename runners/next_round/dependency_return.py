"""Relay one external completed dependency into the existing local watcher.

DESIGN CHECK: LESSONS 3-5 read 2026-10-15. Missing or unfinished evidence
never grants admission. A complete return (including failure) is copied byte
for byte and requests operator review. This helper cannot fit, spend or ACK.
"""
import argparse
import hashlib
import json
import time
from pathlib import Path

from runners.stage14.common import REPO, atomic, freeze, now
from runners.stage9.process_identity import native_identity


def completed_return(source):
    """Inspect only a terminal witness; never summarize partial scientific scores."""
    try:
        blob = Path(source).read_bytes()
    except FileNotFoundError:
        return None
    value = json.loads(blob)
    if not isinstance(value, dict):
        raise ValueError('dependency witness must be an object')
    if value.get('scope') != 'ghost':
        raise ValueError('unexpected dependency scope')
    if value.get('status') in ('RUNNING', 'PENDING', 'PREPARED'):
        return None
    if value.get('status') not in ('PASS', 'FAIL', 'FAILED', 'INCONCLUSIVE', 'BLOCKED'):
        raise ValueError('unknown dependency disposition')
    return blob


def run(source, output, max_seconds=86400, poll_seconds=30):
    output = Path(output).resolve()
    if not output.is_relative_to(REPO.resolve()):
        raise ValueError('local output required')
    if not 1 <= max_seconds <= 86400 or not 1 <= poll_seconds <= 60:
        raise ValueError('invalid finite monitoring bounds')
    output.mkdir(parents=True, exist_ok=True)
    with (output/'ATTEMPT.claim').open('x', encoding='utf8') as f:
        f.write(now()+'\n')
    freeze(output/'OWNER.json', dict(at=now(), native=native_identity(), source=str(source)))
    started = time.monotonic()
    try:
        while True:
            if (output/'CANCEL').exists():
                freeze(output/'CANCELLED.json', dict(at=now(), status='CANCELLED', scientific_admission=False))
                return
            blob = completed_return(source)
            if blob is not None:
                with (output/'SOURCE_WITNESS.json').open('xb') as f:
                    f.write(blob)
                freeze(output/'RETURN_READY.json', dict(at=now(), status='REVIEW_REQUIRED',
                    source_sha256=hashlib.sha256(blob).hexdigest(),
                    source_witness='SOURCE_WITNESS.json', scientific_admission=False,
                    instruction='Inspect full companion evidence before admitting the queued profile comparison.'))
                return
            if time.monotonic()-started >= max_seconds:
                raise TimeoutError('dependency return not available within finite monitoring window')
            time.sleep(poll_seconds)
    except BaseException as exc:
        atomic(output/'FAILED.json', dict(at=now(), status='FAILED', error=str(exc), scientific_admission=False))
        raise


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--source', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    run(a.source, a.output)
