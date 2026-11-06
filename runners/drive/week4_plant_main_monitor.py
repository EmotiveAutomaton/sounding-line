"""Finite retrieval-only PLANT main monitor; no submission, correction or retry.

DESIGN CHECK: LESSONS 5. Unknown or changed identities stop. Completion wakes
the owner for write-through; format completion grants no semantic admission.
"""
from datetime import datetime, timezone
import time
from runners.stage14.common import atomic, filehash, freeze, now, read
from runners.stage9.process_identity import native_identity
from runners.drive import week4_plant_main as plan


def run():
    folder = plan.ROOT / plan.PHASE
    binding = read(folder / 'MONITOR_PLAN.json')
    for path, sha in binding['pins'].items():
        if filehash(path) != sha:
            raise ValueError('monitor source changed')
    freeze(folder / 'MONITOR_OWNER.json', dict(native=native_identity(), at=now()))
    try:
        deadline = time.monotonic() + 300
        while not (folder / 'SUBMITTED.json').exists():
            if (folder / 'UNKNOWN.json').exists():
                raise RuntimeError('unknown submission; reservation retained, no retry')
            if time.monotonic() > deadline:
                raise TimeoutError('submission not observed; monitor cannot submit')
            time.sleep(2)
        submission_hash = filehash(folder / 'SUBMITTED.json')
        while True:
            if filehash(folder / 'SUBMITTED.json') != submission_hash:
                raise ValueError('submission identity changed')
            result = plan.retrieve(plan.PHASE)
            atomic(folder / 'MONITOR_HEARTBEAT.json', dict(at=now(), status=result.get('status')))
            if result.get('status') == 'COMPLETE':
                return
            if datetime.now(timezone.utc) >= datetime.fromisoformat('2026-11-09T07:00:00+00:00'):
                raise TimeoutError('finite retrieval window ended; retrieve only')
            time.sleep(60)
    except BaseException as exc:
        freeze(folder / 'MONITOR_FAILED.json', dict(at=now(), error_type=type(exc).__name__,
               error=str(exc), submission_retry_authorized=False))
        raise


if __name__ == '__main__':
    run()
