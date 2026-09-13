"""Finite earlier-draft development, frozen fit and evaluation continuation.

DESIGN CHECK: LESSONS3-5. No labels before complete development; no evaluation
outcomes in calls. Failure stops the chain and retains every previous attempt.
A complete replay cannot spend new calls. No timer, automatic retry or refill.
"""
import argparse
import os
from pathlib import Path
from . import earlier_effort_queue as queue, earlier_effort_fit as fitter, earlier_effort_evaluation as evaluation
from .contracts import digest
from .ollama import now, write_new
from .queue import read, status
from runners.stage9.process_identity import native_identity

def run(prepared, output, pilot):
    if (output/'OWNER.json').exists() and not (output/'COMPLETE.json').exists():
        raise RuntimeError('interrupted chain requires explicit ownership inspection')
    if not (output/'OWNER.json').exists():
        write_new(output/'OWNER.json', {'at': now(), 'native': native_identity(os.getpid())})
    stages = [('development', lambda: queue.run(prepared, prepared, output/'development', 'development', pilot)),
              ('fit', lambda: fitter.fit(prepared, prepared, output/'development', output/'fit', pilot)),
              ('evaluation', lambda: evaluation.run(prepared, prepared, output/'development', output/'fit', output/'evaluation', pilot))]
    rows = []
    for name, call in stages:
        if not (output/'COMPLETE.json').exists():
            status(output/'STATUS.json', {'at': now(), 'phase': name, 'status': 'RUNNING'})
        result = call()
        rows.append({'stage': name, 'terminal_sha256': digest(result)})
    result = {'at': now(), 'status': 'COMPLETE', 'stages': rows, 'scope': 'prediction producers and development policy only; common scientific comparison pending'}
    if (output/'COMPLETE.json').exists():
        saved = read(output/'COMPLETE.json')
        if any(saved[k] != result[k] for k in result.keys()-{'at'}):
            raise ValueError('complete earlier effort chain changed')
        return saved
    write_new(output/'COMPLETE.json', result)
    status(output/'STATUS.json', {'at': now(), 'status': 'COMPLETE'})
    return result

if __name__ == '__main__':
    p = argparse.ArgumentParser()
    for name in ('prepared', 'output', 'pilot'):
        p.add_argument('--'+name, type=Path, required=True)
    a = p.parse_args()
    try:
        run(a.prepared, a.output, a.pilot)
    except Exception as exc:
        if not (a.output/'FAILED.json').exists():
            write_new(a.output/'FAILED.json', {'at': now(), 'error': repr(exc)})
        raise
