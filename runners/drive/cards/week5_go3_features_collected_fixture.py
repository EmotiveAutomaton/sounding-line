"""Actual collected-source fixture and original GO3 feature/model equivalence.

Only completed counted constructed collection inputs are accepted. The released
IteraTeR train file remains at its original hard pin. No Stack classifier fit,
scientific outcome, source filtering, or per-user statistic is computed here.
"""
from pathlib import Path
import numpy as np
import pyarrow.parquet as pq
from . import week5_go3_features_collected as features

FIXTURE_COLLECTOR = 'runners.drive.cards.week5_go3_collection_counted_fixture_v2'


def known_features():
    cases = [('', '', [0.] * 14),
             ('same', 'same', [4., 4., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0.]),
             ('A cat.', 'A dog!', [6., 6., 0., 2., 2., 1., 2., 1 / 3, 0., 0., 0., 0., 0., 0.]),
             ('', 'X.', [0., 2., 2., 2., 0., 0., 2., 1., 1., 0., 0., 0., 0., 0.]),
             ('word', '', [4., 0., -4., 0., 1., 0., 1., .25, 0., 0., 0., 0., 0., 0.])]
    for before, after, expected in cases:
        if not np.array_equal(features.analysis.features(before, after), expected):
            raise ValueError('Fixed literal diff-feature known answer failed')


def validate(inputs):
    root = Path(inputs['collection_run'])
    plan = features.read(root / 'PLAN.json')
    if plan['module'] != FIXTURE_COLLECTOR or plan['config']['case'] not in ('supported', 'missing-category'):
        raise ValueError('Actual reviewed constructed collection chain required')
    manifest = features.read(plan['inputs']['fixture_manifest'])
    if manifest.get('constructed_only') is not True or manifest['case'] != plan['config']['case']:
        raise ValueError('Non-constructed feature qualification input refused')
    if plan['pins'][str(Path(plan['inputs']['fixture_manifest']).resolve())] != features.core.sha(plan['inputs']['fixture_manifest']):
        raise ValueError('Constructed collection declaration changed')
    return manifest


def original_parity(output, inputs, fixture):
    output = Path(output)
    result = features.read(output / 'FEATURES.json')
    known_features()
    model, report = features.analysis.external_intent(inputs['iterater_train'])
    saved = features.load_arrays(output / result['model']['path'])
    original = features.model_arrays(model)
    if set(saved) != set(original) or any(not np.array_equal(saved[key], original[key]) for key in saved):
        raise ValueError('Checkpointed external intent fit differs from frozen original')
    restored = features.restore_model(saved)
    index, total = 0, 0
    for info in result['binding']['provenance']['sources']:
        for batch in pq.ParquetFile(info['projection']).iter_batches(batch_size=features.BATCH):
            frame = batch.to_pandas()
            x = np.asarray([features.analysis.features(a, b) for a, b in zip(frame.before, frame.after)], float)
            probabilities = model.predict_proba(x)
            if not np.array_equal(restored.predict_proba(x), probabilities):
                raise ValueError('Restored external model changes probabilities')
            part = result['blocks'][index]
            actual = pq.read_table(output / part['path']).to_pandas()
            metadata = frame.drop(columns=['before', 'after'])
            if not actual[list(metadata.columns)].equals(metadata):
                raise ValueError('All-row metadata projection/order differs')
            for column in range(x.shape[1]):
                if not np.array_equal(actual[f'diff_{column}'], x[:, column]):
                    raise ValueError('Complete frozen diff feature parity failed')
            for column, label in enumerate(model.classes_):
                if not np.array_equal(actual['intent_' + label], probabilities[:, column]):
                    raise ValueError('Complete frozen intent probability parity failed')
            if any(name in actual for name in ('before', 'after', 'comment')):
                raise ValueError('Feature bank retained private raw text unexpectedly')
            total += len(actual)
            index += 1
    if total != fixture['rows'] or total != result['rows_projected'] or index != len(result['blocks']):
        raise ValueError('Whole constructed source population was not retained')
    if report != result['training'] or result['scientific_admission'] is not False:
        raise ValueError('External train scope or scientific gate changed')
    receipt = dict(verified=True, constructed_only=True, all_rows_retained=True,
                   original_external_model_parameters_exact=True, original_feature_and_probability_rows_exact=True,
                   fixed_literal_known_answers=True, no_stack_scientific_fit=True,
                   feature_result_sha256=features.core.sha(output / 'FEATURES.json'))
    features.core.write(output / 'FIXTURE_PARITY.json', receipt)
    return receipt


def execute(output, inputs, config):
    fixture = validate(inputs)
    result = features.run_features(output, inputs, config, FIXTURE_COLLECTOR)
    if result.get('status') != 'yielded':
        original_parity(output, inputs, fixture)
    return result


def verify(output, inputs, config):
    fixture = validate(inputs)
    result = features.verify_features(output, inputs, config, FIXTURE_COLLECTOR)
    if result.get('status') != 'yielded':
        original_parity(Path(output) / 'independent-replay', inputs, fixture)
        result |= dict(original_external_model_and_complete_feature_parity=True, constructed_only=True)
    return result
