"""Two manually enumerated discarded full generation pilots, then stop.

DESIGN CHECK: I03/X12. A failure closes this preparation chain, never substitutes
a package or admits a reader. Each child owns immutable complete-attempt units.
"""
import subprocess
import sys
import time
from runners.stage9.common import REPO, ROOT, freeze, write


def run():
    output = ROOT / 'private/generation-chain-2'
    jobs = [('qwen', 'qwen-run2', 'qwen-v2'), ('smollm', 'smollm-run1', 'smollm-v2')]
    for _, training, _ in jobs:
        if not (ROOT / 'pilot' / training / 'COMPLETE.json').is_file():
            raise ValueError('missing completed training input: ' + training)
    freeze(output / 'PLAN.json', {'jobs': jobs, 'scientific_launch_accepted': False})
    for family, training, destination in jobs:
        write(output / 'STATUS.json', {'job': family, 'status': 'running', 'at': time.time()})
        command = [sys.executable, '-B', '-m', 'runners.stage9.generation_pilot',
                   '--family', family, '--training', str(ROOT / 'pilot' / training),
                   '--output', str(ROOT / 'private/pilot-generation' / destination)]
        with (output / (family+'.stdout.log')).open('ab') as stdout, (output / (family+'.stderr.log')).open('ab') as stderr:
            result = subprocess.run(command, cwd=REPO, stdout=stdout, stderr=stderr,
                                    creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
        if result.returncode:
            write(output / 'FAILED.json', {'job': family, 'returncode': result.returncode, 'at': time.time()})
            return result.returncode
    freeze(output / 'COMPLETE.json', {'jobs': jobs, 'completed_at': time.time(), 'scientific_launch_accepted': False})
    return 0


if __name__ == '__main__':
    raise SystemExit(run())
