"""Enforce canonical D4's declared numerical thread count without changing its fit.

DESIGN CHECK: LESSONS 3-5 reread 2026-10-18. Under both NULL and ALTERNATIVE,
all loaded numerical pools must report one thread before and after delegation.
Absent pools, changed configuration or an unenforced limit fail closed. This
operational guard supplies no scientific verdict and changes no source or score.
"""
from pathlib import Path

from threadpoolctl import threadpool_info, threadpool_limits

from . import menus_d4_predictive as original

CONFIG = original.CONFIG


def _pools():
    pools = threadpool_info()
    if not pools or any(pool['num_threads'] != 1 for pool in pools):
        raise RuntimeError('Canonical D4 one-thread numerical limit not established')
    return pools


def _call(operation, output, inputs, config):
    if config != CONFIG:
        raise ValueError('Canonical D4 frozen configuration differs')
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    with threadpool_limits(limits=1):
        before = _pools()
        result = getattr(original, operation)(output, inputs, config)
        after = _pools()
        original.storage.save(output / f'THREAD_LIMIT_{operation.upper()}.json', dict(
            requested_threads=1, measured_before=before, measured_after=after,
            scope='all loaded BLAS/OpenMP pools during the delegated operation'))
        return result


def execute(output, inputs, config):
    return _call('execute', output, inputs, config)


def verify(output, inputs, config):
    return _call('verify', output, inputs, config)
