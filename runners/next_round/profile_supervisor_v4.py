"""One bounded R3 launch, no automatic main or resubmission.

DESIGN CHECK: LESSONS 3-5. NULL/ALTERNATIVE use identical exact-native watches.
Missing terminal, unknown POST or expired retrieval retains accounting and wakes
the owner. A completed format pilot is never scientific feature admission.
"""
import argparse
import os
import subprocess
import sys
import time
from pathlib import Path
from runners.stage14.common import REPO, freeze, atomic, read, filehash
from runners.stage9.process_identity import native_identity
from runners.next_round import profiles_v4 as profiles


def worker(phase):
    root = profiles.ROOT/phase
    native = native_identity()
    freeze(root/'OWNER.json', dict(native=native, at=time.time()))
    try:
        plan = profiles.validate_plan(root)
        cfgpath = REPO/'.agent-state/watch.json'
        before = filehash(cfgpath); cfg = read(cfgpath)
        rel = root.relative_to(REPO).as_posix()
        terminal = [rel+'/'+n+'.json' for n in ('COMPLETE', 'FAILED')]
        name = 'stage15-r3-profiles-'+phase+'-v4'
        if any(w.get('name') == name for w in cfg['process_watches']):
            raise ValueError('existing supervised attempt')
        cfg['process_watches'].append(dict(name=name, native=native, terminal_paths=terminal,
                                          failure_output=rel+'/MONITOR_FAILED.json'))
        for path in terminal+[rel+'/UNKNOWN.json', rel+'/MONITOR_FAILED.json']:
            if path not in cfg['paths']: cfg['paths'].append(path)
        if filehash(cfgpath) != before: raise ValueError('concurrent watch configuration change')
        atomic(cfgpath, cfg)
        freeze(root/'SUPERVISION.json', dict(native=native, watch_sha256=filehash(cfgpath),
                                           supervisor_sha256=filehash(Path(__file__)),
                                           automatic_main=False, automatic_resubmission=False))
        profiles.submit(phase)
        expires = read(root/'SUBMITTED.json')['at']+plan['max_seconds']
        while time.time() < expires:
            result = profiles.retrieve(phase)
            atomic(root/'PROGRESS.json', dict(at=time.time(), status=result['status'], expires=expires))
            if result['status'] == 'COMPLETE':
                profiles.reconcile(phase)
                freeze(root/'EXIT.json', dict(status='COMPLETE', at=time.time()))
                return
            time.sleep(min(120, max(0, expires-time.time())))
        raise TimeoutError('bounded retrieval expired; inspect existing provider batch')
    except BaseException as exc:
        freeze(root/'FAILED.json', dict(status='FAILED', at=time.time(), error_type=type(exc).__name__,
                                        reservation_retained_unless_reconciled=True))
        raise


def launch(phase):
    root = profiles.ROOT/phase
    profiles.validate_plan(root)
    if any((root/n).exists() for n in ('LAUNCH.json','OWNER.json','RESERVATION.json','SUBMITTED.json','UNKNOWN.json')):
        raise ValueError('existing attempt; inspect only')
    env = dict(os.environ, PYTHONPATH=str(REPO)+os.pathsep+str(REPO/'.venv/Lib/site-packages'),
               PYTHONIOENCODING='utf8', OMP_NUM_THREADS='1', MKL_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1')
    command = [sys._base_executable, '-B', '-m', 'runners.next_round.profile_supervisor_v4', phase, '--worker']
    with (root/'stdout.log').open('xb') as out, (root/'stderr.log').open('xb') as err:
        child = subprocess.Popen(command, cwd=REPO, env=env, stdout=out, stderr=err,
                                 creationflags=subprocess.CREATE_NO_WINDOW|subprocess.BELOW_NORMAL_PRIORITY_CLASS)
    freeze(root/'LAUNCH.json', dict(pid=child.pid, at=time.time(), command=command))
    print('R3 '+phase+' supervisor started; verify actual provider acceptance.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('phase', choices=['canary','pilot','main'])
    parser.add_argument('--worker', action='store_true'); args = parser.parse_args()
    (worker if args.worker else launch)(args.phase)
