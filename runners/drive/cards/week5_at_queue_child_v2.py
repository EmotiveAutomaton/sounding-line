"""Bound actual scorer identity to its owned Job before unchanged child work.

DESIGN CHECK: LESSONS 3-5. All outcomes require the same native handshake.
Missing, changed, uncontained or expired acknowledgements refuse before scoring.
No numerical, source, memory-guard or scorer change; no test has run.
"""
import argparse
from pathlib import Path
import time
from .batch_runtime import freeze, read, filehash, now, native_identity
from . import week5_child_v7


def handshake(root, operation):
    prefix = operation.upper(); native = native_identity()
    ready = dict(at=now(), native=native, phase=operation, plan_sha256=filehash(root/'PLAN.json'))
    path = root/(prefix+'_READY.json'); freeze(path, ready)
    acknowledgement = root/(prefix+'_MEMBER.json'); deadline = time.monotonic() + 60
    while not acknowledgement.is_file():
        if time.monotonic() >= deadline: raise TimeoutError('Owned Job membership acknowledgement absent')
        time.sleep(.05)
    value = read(acknowledgement)
    if not (value['native'] == native and value['ready_sha256'] == filehash(path) and
            value['member_of_exact_owned_job'] is True and
            value['identity_checked_on_membership_handle'] is True and
            value['known_live_when_authenticated'] is True):
        raise ValueError('Owned Job membership acknowledgement differs')
    return native


def run(root, operation):
    handshake(root, operation)
    week5_child_v7.run(root, operation)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('operation', choices=['execute', 'verify']); parser.add_argument('root', type=Path)
    args = parser.parse_args(); run(args.root.resolve(), args.operation)
