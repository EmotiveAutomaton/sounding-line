"""Four manually commissioned discarded pilots after the current Smol training fit.

DESIGN CHECK: Stage 9 pilot-before-lock. This is preparation, not the scientific queue.
Each exact produces is guarded by its pilot's identity; any failed job stops the chain.
Waiting for the existing fit is separately timed and capped at one hour. No expansion.
"""
from pathlib import Path
import time

from runners.stage9.common import ROOT, file_hash, read, write
from runners.stage9.model_pilot import run as model_pilot
from runners.stage9.learner import pilot as learner_pilot


def main():
    output = ROOT / 'private/prelaunch-chain-1'
    output.mkdir(parents=True, exist_ok=False)
    started = time.time()
    training = ROOT / 'pilot/smollm-run1'
    while not (training / 'COMPLETE.json').exists():
        if time.time() - started > 3600:
            write(output / 'FAILED.json', {'at': time.time(), 'reason': 'existing Smol pilot did not complete in the one-hour wait bound'})
            return 1
        time.sleep(2)
    write(output / 'WAIT.json', {'started_at': started, 'ended_at': time.time(),
                                'training_complete_sha256': file_hash(training / 'COMPLETE.json')})
    jobs = [('qwen-model-v3', model_pilot, 'qwen', ROOT / 'pilot/qwen-run2', ROOT / 'private/pilot-model/qwen-v3'),
            ('smollm-model-v1', model_pilot, 'smollm', training, ROOT / 'private/pilot-model/smollm-v1'),
            ('qwen-learner-v1', learner_pilot, 'qwen', ROOT / 'pilot/qwen-run2', ROOT / 'private/pilot-learner/qwen-v1'),
            ('smollm-learner-v1', learner_pilot, 'smollm', training, ROOT / 'private/pilot-learner/smollm-v1')]
    write(output / 'JOBS.json', [{'name': name, 'family': family, 'training': str(fit), 'produces': str(destination / 'COMPLETE.json')}
                               for name, _, family, fit, destination in jobs])
    for name, runner, family, fit, destination in jobs:
        write(output / 'STATUS.json', {'job': name, 'status': 'running', 'at': time.time()})
        try:
            runner(family, fit, destination)
        except Exception as exc:
            write(output / 'FAILED.json', {'job': name, 'at': time.time(), 'error': repr(exc),
                                          'note': 'retained failure; no automatic substitution or second version'})
            raise
        write(output / (name + '.json'), {'job': name, 'completed_at': time.time(),
                                         'produces_sha256': file_hash(destination / 'COMPLETE.json')})
    write(output / 'COMPLETE.json', {'completed_at': time.time(), 'jobs': [j[0] for j in jobs], 'scientific_launch_accepted': False})
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
