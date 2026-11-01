"""Bounded constructed native rehearsal of atomic telemetry and byte accounting.

DESIGN CHECK: LESSONS 3-5 reread 2026-10-30. NULL: vanished atomic temporary
files cannot crash accounting; real missing data and I/O errors still fail.
ALTERNATIVE: retained file bytes remain counted and the cap remains enforced.
No participant data, scientific estimand, model API or new research is involved.
"""
from pathlib import Path
import time
from runners.stage14.common import atomic, freeze, read
from .batch_runtime_v6 import output_bytes


def execute(output, inputs, config):
    if inputs or config != {'writes': 2000}:
        raise ValueError('Fixed constructed rehearsal required')
    output = Path(output)
    for index in range(config['writes']):
        atomic(output/'PROGRESS.json', {'index': index})
        if index % 100 == 0:
            time.sleep(.01)
    result = {'constructed_fixture_only': True, 'writes': config['writes'],
              'scientific_admission': False}
    freeze(output/'SUMMARY.json', result)
    return result


def verify(output, inputs, config):
    output = Path(output)
    if inputs or read(output/'PROGRESS.json') != {'index': config['writes']-1}:
        raise ValueError('Actual atomic writer did not finish')
    expected = sum((output/name).stat().st_size for name in ('PROGRESS.json', 'SUMMARY.json'))
    if output_bytes(output) != expected:
        raise ValueError('Output byte accounting differs')
    return {'verified': True, 'constructed_fixture_only': True}
