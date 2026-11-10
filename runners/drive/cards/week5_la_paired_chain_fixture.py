"""Counted A/B/C pause chain over one constructed paired act; never human data.

Same input/config on each attempt. A pauses execute after its two mask batches;
B reenters completed execute and pauses fresh verify after two fresh batches;
C reenters execute and completes retained independent verify. This adapter does
not copy, launch or authenticate native continuation; the reviewed runtime must.
"""
from pathlib import Path
from . import week5_la_pipeline_v5_fixture as fixture
from .week5_at_source import authenticate
from .timing_census import read, filehash
from .timing_p6 import write_equal


def run(output, inputs, config, verifying=False):
    if set(inputs) != {'constructed_fixture_root'} or config:
        raise ValueError('Completed constructed paired integration fixture only')
    prior = authenticate(inputs['constructed_fixture_root'])
    if read(prior / 'PLAN.json').get('module') != fixture.__name__:
        raise ValueError('Only the exact constructed paired integration proof is accepted')
    proof = read(prior / 'output/FIXTURE.json')
    if not proof.get('no_human_input') or not proof.get('original_numeric_bytes_equal'):
        raise ValueError('Full constructed original-output comparison required')
    root, source = Path(output), prior / 'output'
    root.mkdir(parents=True, exist_ok=True)
    if (root / 'YIELD_REQUEST.json').exists():
        return dict(status='yielded', reason='native request before constructed paired continuation')
    args, options = read(source / 'CHAIN_INPUTS.json'), read(source / 'CHAIN_CONFIG.json')
    if options != dict(operation='score', max_new_mask_batches=2, max_wall_seconds=600):
        raise ValueError('Exact native fixture mask quantum required')
    # Bind these actual payload files through the predecessor's complete tree;
    # they always retain their original source paths across native attempts.
    complete = read(prior / 'COMPLETE.json')
    for name in ('CHAIN_INPUTS.json', 'CHAIN_CONFIG.json', 'CHAIN_ROWS.json.gz'):
        if complete['outputs'].get('output/' + name) != filehash(source / name):
            raise ValueError('Constructed native chain input is not authenticated')
    if Path(args['rows']).resolve() != (source / 'CHAIN_ROWS.json.gz').resolve():
        raise ValueError('Native chain source path changed')
    result = fixture.paired_call(root, args, options, verifying)
    if result.get('status') == 'yielded':
        return result
    if verifying and result.get('verified') is not True:
        raise ValueError('Native paired chain verification did not complete')
    oracle = source / 'chain-original-v3'
    for name in ('act-000.json', 'INDEX.json', 'SUMMARY.json'):
        if filehash(root / name) != filehash(oracle / name):
            raise ValueError('Counted paired continuation differs from original output')
    value = dict(fixture_only=True, no_human_input=True,
                 qualification_complete_sha256=filehash(prior / 'COMPLETE.json'),
                 original_numeric_bytes_equal=True, native_continuation_requires_external_identity_and_copy_audit=True,
                 paired_human_memory_qualified=False, collector_admission=False)
    if verifying:
        if read(root / 'CHAIN.json') != value:
            raise ValueError('Native paired continuation reduction changed')
        return dict(verified=True, constructed_paired_continuation=True)
    write_equal(root / 'CHAIN.json', value)
    return dict(status='complete', fixture_only=True)


def execute(output, inputs, config):
    return run(output, inputs, config)


def verify(output, inputs, config):
    return run(output, inputs, config, True)
