"""D2's single engineering retry: canonical aggregation, unchanged saved fits.

DESIGN CHECK 2026-10-17: lessons read: LESSONS 3-5, especially unordered
bootstrap input. NULL and ALTERNATIVE retain identical forecasts and primary
contrasts. Only writer iteration order for the five descriptive bin means is
canonicalized. Failure direction is any changed source, score or saved summary;
all original states and exhaustive bands remain. No refit, new seed or tolerance.
"""
from pathlib import Path
from collections import defaultdict
import math

from . import menus_d2 as original
from .menus_io import read, sha256, input_hashes, assert_equal


def summarize(predictions, config):
    # Stable within-writer order preserves the original execute accumulation.
    return original.summarize(sorted(predictions, key=lambda row: row['writer']), config)


def verify(output, inputs, config):
    output=Path(output);report=read(output/'SUMMARY.json')
    assert_equal(report['input_hashes'],input_hashes(inputs));assert_equal(report['config'],config)
    original.authenticated(inputs);predictions=defaultdict(list)
    for name,expected in sorted(report['recipient_hashes'].items()):
        if sha256(output/name)!=expected:raise ValueError('changed saved recipient')
        saved=read(output/name)
        assert_equal(saved['binding'],dict(inputs=report['input_hashes'],config=config))
        if saved['result']:
            for arm,record in saved['result']['arms'].items():
                for row in record['predictions']:
                    if not 0<=row['truth']<row['size'] or row['size']<2:raise ValueError('saved choice outside offer set')
                    if not math.isfinite(row['log_probability']) or row['log_probability']>1e-12:raise ValueError('invalid saved log probability')
                    if row['gain']!=row['log_probability']+math.log(row['size']):raise ValueError('saved gain differs from probability')
                predictions[arm].extend(record['predictions'])
    for arm in ('primary','uniform_control'):
        actual=summarize(predictions[arm],config)
        expected=report if arm=='primary' else report['uniform_control']
        assert_equal(actual,{k:expected[k] for k in actual})
    return dict(verified=True,primary_recomputed=report['primary'],state=report['state'],
                canonical_writer_order=True,refitted=False)


def execute(output, inputs, config):
    verify(output,inputs,config)
    return read(Path(output)/'SUMMARY.json')
