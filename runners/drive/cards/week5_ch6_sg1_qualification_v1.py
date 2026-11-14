"""Constructed-only integration of the preserved CH6 model and SG1 bridge.

DESIGN CHECK: LESSONS 3-5. This is an exact regression/integration check,
not a new effect estimator. The original independently validated numerical
answer and all player-game rows are preserved. Execute and verify must each
honor a real native pause, the continuation must reuse exactly its authenticated
execute prefix, and final verification starts at callback zero. Any changed
answer, input, missing native transition or cached verifier fails this check.
Null/alternative numerical coverage belongs to the original retained fixture;
this check adds no sensitivity or human inference claim.
"""
from pathlib import Path
from unittest.mock import patch
from . import week5_ch_analysis_qualification_adapter_v1 as original
from . import week5_sg1_carried_v1 as bridge
from . import week5_ch_history_index as index
from . import week5_sg1_source_v1 as source
from .batch_runtime import read, filehash, check_files

MODULE = 'runners.drive.cards.week5_ch6_sg1_qualification_v1'
CONFIG = dict(constructed_fixture=True, card='CH6', max_new_draws=1000000000)


def expected_case(inputs, config):
    if config != CONFIG or set(inputs) != {'constructed_manifest'}:
        raise ValueError('Exact constructed-only integration configuration required')
    spec = inputs['constructed_manifest']
    if set(spec) != {'path', 'sha256'} or filehash(spec['path']) != spec['sha256']:
        raise ValueError('Constructed manifest pin changed')
    manifest = read(spec['path'])
    if manifest.get('constructed_only') is not True or manifest.get('scientific_admission') is not False:
        raise ValueError('No human study admission through this fixture')
    check_files(manifest['pins'])
    receipt, pins = original.input_pins()
    if manifest['original_input_inventory_sha256'] != original.INPUT_SHA256:
        raise ValueError('Original qualification inventory changed')
    cases = list(original.reference_fixture.cases(receipt['fixture_inputs']))
    _, old_inputs, settings, old_expected = next(c for c in cases if c[0] == 'CH6')
    database = Path(manifest['database'])
    expected = Path(manifest['expected_science'])
    checkpoint = expected.parent / 'CHECKPOINT.json'
    if any(str(p) not in manifest['pins'] for p in (database, expected, checkpoint)):
        raise ValueError('Unpinned constructed evidence')
    if index.contents_hash(database) != index.contents_hash(old_inputs['histories']['path']):
        raise ValueError('Original player-game values changed')
    with source.HistoryStore(database, True) as histories:
        if not len(histories):
            raise ValueError('Empty constructed source')
    answer = read(old_expected)
    if 'activation' in answer:
        raise ValueError('Original numerical answer unexpectedly changed')
    answer['activation'] = bridge.activation()
    if read(expected) != answer or filehash(checkpoint) != filehash(old_expected.parent/'CHECKPOINT.json'):
        raise ValueError('Original complete numerical truth or callback count changed')
    return 'CH6', {'histories': dict(path=str(database), sha256=filehash(database))}, settings, expected


def case_run(output, inputs, config, operation):
    # Process-local binding only. The actual bridge and runtime request handler
    # run unchanged; every binding is restored even if a gate raises.
    with patch.object(original, 'MODULE', MODULE), patch.object(original, 'expected_case', expected_case):
        with bridge.adapted('CH6'):
            return original.case_run(output, inputs, config, operation)


def execute(output, inputs, config):
    return case_run(output, inputs, config, 'execute')


def verify(output, inputs, config):
    return case_run(output, inputs, config, 'verify')
