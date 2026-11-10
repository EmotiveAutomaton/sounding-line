"""Bounded complete-grid GO3 numerical parity and actual bank-consumer fixture.

Constructed mathematical worlds and an actually completed counted feature
fixture are separate proofs. Neither is represented as a human result.
"""
from pathlib import Path
import hashlib
import json
import numpy as np
import pandas as pd
from . import week5_go3_bank_analysis as bank

FEATURE_FIXTURE = 'runners.drive.cards.week5_go3_features_collected_fixture'


def world(signal):
    rows = []
    reasons = list(bank.SOURCE.PRIMARY)
    for site in bank.features.collection.SITES:
        for user in range(45):
            editor = hashlib.sha256(f'constructed:{site}:u{user}'.encode()).hexdigest()
            for post in range(2):
                postkey = hashlib.sha256(f'constructed:{site}:p{post}'.encode()).hexdigest()
                for category, reason in enumerate(reasons + ['formatting', 'tags', 'other']):
                    row = dict(editor=editor, post=postkey, stamp=f'2024-01-01T00:{user:02d}:{category:02d}',
                               site=site, type=5 if category < 5 or category == 7 else 4 if category == 5 else 6,
                               reason=reason, self_edit=user % 2 == 0, owner_known=True)
                    row.update({f'diff_{i}': float(signal and i == category) for i in range(14)})
                    row.update({f'intent_{i}': 1 / 6 for i in range(6)})
                    rows.append(row)
    rows.sort(key=lambda row: (list(bank.features.collection.SITES).index(row['site']), row['post'], row['stamp']))
    return pd.DataFrame(rows)


def mathematical_parity(output, signal, specification):
    frame = world(signal)
    binding = bank.features.digest(dict(constructed=True, signal=signal, specification=specification,
                                       fixture_sha256=bank.core.sha(__file__)))
    result = bank.run_frame(output, frame, specification, binding, lambda: False)
    expected = bank.original.classify(frame, specification)
    if specification['cell'] == 'GO3':
        expected['habit_companion'] = bank.original.habits(frame, 2000, 1000)
    expected.update(card='GO3', scope='comment-stated editing reason categories; retrospective and descriptive')
    if result != expected:
        raise ValueError('Complete original GO3 model, interval or habit reference parity differs')
    if signal and result.get('gain', 0) < .7:
        raise ValueError('Constructed strongly informative feature instrument failed')
    if not signal and result.get('outcome') == 'supports':
        raise ValueError('Uninformative fixed-design classifier world passed')
    if specification['cell'] == 'GO3' and (result['habit_companion']['passes'] or result['habit_companion']['difference_interval'] != [0., 0.]):
        raise ValueError('Exact context-only habit world passed or was not exact zero')
    return result


def validate_actual_fixture(inputs):
    if set(inputs) != {'feature_run'}:
        raise ValueError('Exact counted feature fixture input required')
    root = Path(inputs['feature_run'])
    plan = bank.features.read(root / 'PLAN.json')
    if plan['module'] != FEATURE_FIXTURE:
        raise ValueError('Only an actual completed feature qualification is permitted')
    verified = bank.features.read(root / 'VERIFIED.json')
    if verified.get('constructed_only') is not True or verified.get('original_external_model_and_complete_feature_parity') is not True:
        raise ValueError('Complete counted original-model feature qualification required')


def execute(output, inputs, config):
    validate_actual_fixture(inputs)
    return bank.run(output, inputs, config, FEATURE_FIXTURE)


def verify(output, inputs, config):
    validate_actual_fixture(inputs)
    result = bank.verify_run(output, inputs, config, FEATURE_FIXTURE)
    if result.get('status') != 'yielded':
        root, source, _ = bank.authenticate_bank(inputs['feature_run'], lambda: False, FEATURE_FIXTURE)
        frame = bank.load_frame(root, source, lambda: False)
        specification = bank.cell_config(config['cell'])
        expected = bank.original.classify(frame, specification)
        if specification['cell'] == 'GO3':
            expected['habit_companion'] = bank.original.habits(frame, 2000, 1000)
        expected.update(card='GO3', scope='comment-stated editing reason categories; retrospective and descriptive')
        if expected != bank.features.read(Path(output) / 'RESULT.json'):
            raise ValueError('Actual bank consumer differs from frozen original complete analysis')
        result |= dict(constructed_only=True, original_complete_bank_analysis_exact=True)
    return result
