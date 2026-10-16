"""Finite R6 successor queue; existing frozen scientific handlers, isolated outputs.

DESIGN CHECK: LESSONS 2-5 read 2026-10-14. NULL: drift, failed prerequisites,
duplicate attempts, inadequate memory or a reporting deadline refuse dispatch.
ALTERNATIVE: exact matched recipes run once, with both native likelihood readouts.
No scientific threshold changes, outcome-based retries or old-queue resumption.
"""
import os
for _key in ('OMP_NUM_THREADS', 'MKL_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'NUMEXPR_NUM_THREADS'):
    os.environ[_key] = '1'
import argparse
from datetime import datetime, timezone
from pathlib import Path
import subprocess
import sys
import time
import traceback

from runners.stage14.common import REPO, read, freeze, atomic, check_pins, filehash, limits, now, verify
from runners.stage9.process_identity import native_identity, is_same_live_process
from .queue import resource_snapshot, require_resources


def decision(card, states, raw, remaining, paused=False):
    if paused:
        return 'held', 'explicit pause'
    for dep in card['requires']:
        if states.get(dep) in ('failed', 'blocked', 'unknown'):
            return 'blocked', 'dependency did not complete: ' + dep
        if states.get(dep) != 'complete':
            return 'waiting', 'dependency: ' + dep
    for gate in card.get('gates', []):
        if read(raw / 'jobs' / gate / 'ADMISSION.json').get('admitted') is not True:
            return 'blocked', 'scientific prerequisite refused: ' + gate
    if remaining < card['wall_seconds']:
        return 'held', 'whole-card ceiling would cross reporting reserve'
    return 'eligible', 'dependencies and time admitted'


def readiness(card):
    snap = resource_snapshot()
    require_resources(snap)
    if card['resource'] == 'gpu':
        from runners.stage14.local import api
        from runners.stage12.local_api import snapshot
        if (REPO / 'results/.gpu.lock').exists():
            return False, 'shared GPU lock held', snap
        if api('/api/ps')['models']:
            return False, 'Ollama resident model; owner must release it', snap
        gpu = snapshot()
        snap['gpu'] = gpu
        if gpu['free_MiB'] < max(6000, card['memory_MiB']) or gpu['temperature_C'] > 78:
            return False, 'cold GPU reserve or temperature refused', snap
    return True, 'ready', snap


def worker(card_path, raw):
    # The scientific handler remains byte-identical to the original attempts.
    from runners.stage14.worker import run
    run(card_path, raw)


def run(plan_path, *, sleep=time.sleep, popen=subprocess.Popen, ready=readiness):
    limits()
    plan_path = Path(plan_path).resolve()
    raw = plan_path.parent
    plan = read(plan_path)
    check_pins(plan['pins'])
    with (raw / 'ATTEMPT.claim').open('x', encoding='utf8') as f:
        f.write(now())
    freeze(raw / 'OWNER.json', dict(at=now(), native=native_identity(), plan_sha256=filehash(plan_path)))
    states = {i: 'complete' for i in plan['imported_dependencies']}
    for i in plan['imported_dependencies']:
        verify(raw / 'jobs' / i, raw / 'cards' / (i + '.json'))
    cards = {i: read(raw / 'cards' / (i + '.json')) for i in plan['cards']}
    if len(cards) != len(plan['cards']):
        raise ValueError('duplicate identities')
    for i, c in cards.items():
        if c['id'] != i or filehash(raw / 'cards' / (i + '.json')) != plan['card_pins'][i]:
            raise ValueError('card binding mismatch')
        check_pins(c['source_pins'])
        check_pins(c.get('input_pins', {}))
        states[i] = 'pending'
    deadline = datetime.fromisoformat(plan['reporting']).timestamp()
    current = None
    try:
        for identifier, card in cards.items():
            current = identifier
            out = raw / 'jobs' / identifier
            out.mkdir(parents=True, exist_ok=True)
            cp = raw / 'cards' / (identifier + '.json')
            if any((out / p).exists() for p in ('DISPATCH.json', 'COMPLETE.json', 'FAILED.json', 'LAUNCH.json')):
                raise ValueError('attempt already exists: ' + identifier)
            while True:
                paused = any((raw / p).exists() for p in ('PAUSE.json', 'STOP.json'))
                state, reason = decision(card, states, raw, deadline - time.time(), paused)
                if state == 'blocked':
                    freeze(out / 'BLOCKED.json', dict(status='blocked', at=now(), reason=reason))
                    states[identifier] = state
                    break
                if state != 'eligible':
                    states[identifier] = state
                    atomic(raw / 'STATUS.json', dict(at=now(), states=states, current=identifier, reason=reason))
                    freeze(raw / 'EXIT.json', dict(status='COMPLETE', at=now(), disposition='held', states=states, reason=reason))
                    return
                try:
                    eligible, reason, snap = ready(card)
                except (RuntimeError, OSError) as exc:
                    eligible, reason, snap = False, str(exc), {}
                atomic(raw / 'STATUS.json', dict(at=now(), states=states, current=identifier, reason=reason, resources=snap))
                if eligible:
                    break
                # Cheap background resource waiting, no model polling or cleanup.
                sleep(30)
            if states[identifier] == 'blocked':
                continue
            check_pins(plan['pins'])
            env = dict(os.environ, PYTHONPATH=str(REPO) + os.pathsep + str(REPO / '.venv/Lib/site-packages'), PYTHONIOENCODING='utf-8')
            command = [sys._base_executable, '-B', '-m', 'runners.next_round.repair_queue', 'worker', '--plan', str(plan_path), '--card', str(cp)]
            with (out / 'stdout.log').open('xb') as stdout, (out / 'stderr.log').open('xb') as stderr:
                child = popen(command, cwd=REPO, env=env, stdout=stdout, stderr=stderr,
                              creationflags=subprocess.CREATE_NO_WINDOW | subprocess.BELOW_NORMAL_PRIORITY_CLASS)
            identity = native_identity(child.pid)
            freeze(out / 'LAUNCH.json', dict(at=now(), native=identity, card_sha256=filehash(cp)))
            if identity is None:
                raise RuntimeError('child ended before native identity verification')
            states[identifier] = 'running'
            start = time.monotonic()
            while child.poll() is None:
                reason = None
                try:
                    require_resources(resource_snapshot())
                except (RuntimeError, OSError) as exc:
                    reason = 'host resource guard: ' + str(exc)
                if time.monotonic() - start > card['wall_seconds'] or time.time() >= deadline:
                    reason = 'finite card/reporting deadline'
                if (raw / 'STOP.json').exists():
                    reason = 'explicit STOP'
                if reason:
                    # Popen retains the exact child handle; PID reuse cannot target a sibling.
                    if not is_same_live_process(identity):
                        raise RuntimeError('cannot prove ownership for bounded stop')
                    child.terminate()
                    child.wait(timeout=15)
                    freeze(out / 'SUPERVISOR_FAILED.json', dict(status='FAILED', at=now(), native=identity, reason=reason))
                    raise RuntimeError(reason + '; inspect retained GPU lock before any further dispatch')
                atomic(raw / 'STATUS.json', dict(at=now(), states=states, current=identifier, native=identity))
                sleep(15)
            if (out / 'COMPLETE.json').exists() and child.returncode == 0:
                verify(out, cp)
                states[identifier] = 'complete'
            else:
                states[identifier] = 'failed'
                if not (out / 'FAILED.json').exists():
                    freeze(out / 'FAILED.json', dict(status='failed', at=now(), returncode=child.returncode,
                                                    reason='child ended without valid completion'))
            atomic(raw / 'STATUS.json', dict(at=now(), states=states, current=identifier))
        freeze(raw / 'EXIT.json', dict(status='COMPLETE', at=now(), disposition='drained', states=states,
                                      provider_spend_cents=0, write_through_required=True))
    except BaseException as exc:
        freeze(raw / 'FAILED.json', dict(status='FAILED', at=now(), current=current, error=str(exc), traceback=traceback.format_exc()))
        raise


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['run', 'worker'])
    parser.add_argument('--plan', type=Path, required=True)
    parser.add_argument('--card', type=Path)
    args = parser.parse_args()
    if args.action == 'worker':
        worker(args.card, args.plan.resolve().parent)
    else:
        run(args.plan)
