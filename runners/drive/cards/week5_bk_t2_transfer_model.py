"""Frozen all-CoAuthor target-b transfer model; no external labels are accepted.

Build preparation only until owner review and counted constructed qualification.
The commissioned task is retrospective process detection from final text.
"""
from pathlib import Path
import warnings
import numpy as np
import sklearn
from sklearn.linear_model import LogisticRegression
from sklearn.exceptions import ConvergenceWarning
from threadpoolctl import threadpool_limits
from . import week5_bk_t2_analysis as original
from . import week5_bk_t2_features as feature_source
from .timing_pmap_source import completed
from .timing_p6 import gzread, write_equal
from .timing_census import read, filehash

SCHEMA = 'week5-t2-transfer-ridge-v1'
FIXED = dict(C=1., solver='lbfgs', max_iter=2000, tol=1e-8,
             random_state=original.SEED)


def matrices(rows):
    selected = original.select(rows, 'b', 'primary')
    if not selected:
        raise ValueError('No CoAuthor target-b training support')
    y = np.asarray([r['labels']['b'] for r in selected], int)
    base = np.asarray([r['baseline'] for r in selected], float)
    full = np.asarray([r['features'] for r in selected], float)
    if (base.ndim != 2 or base.shape[1] != 3 or full.ndim != 2
            or full.shape[1] <= 271 or not np.array_equal(full[:, :3], base)
            or not np.isfinite(full).all() or len(set(y)) != 2):
        raise ValueError('Invalid target-b feature or class support')
    keys = [(r['session'], r['index']) for r in rows]
    if len(set(keys)) != len(keys):
        raise ValueError('Repeated CoAuthor final-sentence key')
    return selected, y, base, full


def fit_matrix(x, y):
    """Exactly the original pooled ridge fit, serialized without pickle."""
    x, y = np.asarray(x, float), np.asarray(y, int)
    if x.ndim != 2 or len(x) != len(y) or not np.isfinite(x).all() or set(y) != {0, 1}:
        raise ValueError('Invalid ridge training matrix')
    mean, scale = x.mean(0), x.std(0)
    keep = scale > 1e-12
    z = (x[:, keep] - mean[keep]) / scale[keep]
    if not keep.any():
        z = np.zeros((len(y), 1))
    estimator = LogisticRegression(**FIXED)
    with warnings.catch_warnings():
        warnings.simplefilter('error', ConvergenceWarning)
        estimator.fit(z, y)
    if np.any(estimator.n_iter_ >= FIXED['max_iter']):
        raise ValueError('Nonconverged transfer model')
    if estimator.classes_.tolist() != [0, 1]:
        raise ValueError('Unexpected positive-class mapping')
    return dict(width=x.shape[1], mean=mean.tolist(), scale=scale.tolist(),
                keep=keep.tolist(), coefficient=estimator.coef_[0].tolist(),
                intercept=float(estimator.intercept_[0]),
                zero_feature=not bool(keep.any()))


def probabilities(model, x):
    """Prediction takes only numeric text features, never outcome metadata."""
    x = np.asarray(x, float)
    if x.ndim != 2 or x.shape[1] != model['width'] or not np.isfinite(x).all():
        raise ValueError('Transfer feature width or finiteness mismatch')
    mean, scale = np.asarray(model['mean'], float), np.asarray(model['scale'], float)
    keep = np.asarray(model['keep'], bool)
    coefficient = np.asarray(model['coefficient'], float)
    if (mean.shape != (model['width'],) or scale.shape != mean.shape
            or keep.shape != mean.shape or not np.isfinite(mean).all()
            or not np.isfinite(scale).all() or (scale < 0).any()
            or not np.array_equal(keep, scale > 1e-12)
            or model['zero_feature'] != (not keep.any())
            or coefficient.shape != (max(1, int(keep.sum())),)
            or not np.isfinite(coefficient).all() or not np.isfinite(model['intercept'])):
        raise ValueError('Malformed serialized ridge model')
    z = (x[:, keep] - mean[keep]) / scale[keep]
    if not keep.any():
        z = np.zeros((len(x), 1))
    logits = z @ coefficient + model['intercept']
    # Stable sigmoid, including large values from domain-shifted external text.
    result = np.empty(len(logits), float)
    positive = logits >= 0
    result[positive] = 1. / (1. + np.exp(-logits[positive]))
    exp = np.exp(logits[~positive])
    result[~positive] = exp / (1. + exp)
    return result


def fit(rows, pins, check=lambda: None):
    selected, y, base, full = matrices(rows)
    check()
    baseline = fit_matrix(base, y)
    check()
    model = fit_matrix(full, y)
    check()
    return dict(schema=SCHEMA, target='b', feature_time='final_text',
                task='retrospective_process_detection', sklearn_version=sklearn.__version__,
                hyperparameters=FIXED, feature_pins=pins,
                baseline=baseline, full=model,
                counts=dict(all_final_sentences=len(rows), training_sentences=len(y),
                            undefined_target_b=len(rows)-len(y),
                            writers=len({r['writer'] for r in selected}),
                            positives=int(y.sum()), negatives=int(len(y)-y.sum())),
                evaluation_labels_used=False, external_training=False)


def predict(bank, baseline, features):
    if (bank['schema'] != SCHEMA or bank['target'] != 'b'
            or bank['hyperparameters'] != FIXED
            or bank['task'] != 'retrospective_process_detection'):
        raise ValueError('Unregistered transfer model')
    base, full = np.asarray(baseline, float), np.asarray(features, float)
    if (base.ndim != 2 or base.shape[1] != 3 or full.ndim != 2
            or not np.array_equal(full[:, :3], base)):
        raise ValueError('Transfer baseline differs from full feature prefix')
    return probabilities(bank['baseline'], base), probabilities(bank['full'], full)


def dependencies(inputs):
    if set(inputs) != {'feature_completion', 'source_completion', 'dictionary_completion',
                       'encoder_manifest', 'evaluation_completion'}:
        raise ValueError('Unexpected transfer-export dependency')
    c = Path(inputs['feature_completion'])
    path, summary_path, plan_path = (c.parent/'output/PRIVATE_FEATURES.json.gz',
                                    c.parent/'output/SUMMARY.json', c.parent/'PLAN.json')
    for artifact in (path, summary_path, plan_path):
        completed(c, artifact)
    plan, summary = read(plan_path), read(summary_path)
    if (plan['module'] != 'runners.drive.cards.week5_bk_t2_features'
            or plan['config'] != dict(card='BK-T2-features', phase='collect')
            or filehash(plan['inputs']['source_completion']) != filehash(inputs['source_completion'])
            or summary.get('complete_collection') is not True):
        raise ValueError('Transfer requires the exact complete T2 feature collection')
    s = Path(inputs['source_completion'])
    source_path, source_summary = s.parent/'output/PRIVATE_SENTENCES.json.gz', s.parent/'output/SUMMARY.json'
    completed(s, source_path)
    completed(s, source_summary)
    support = read(source_summary)
    if support['constructed'] or support['sessions'] != 1399 or support['writers'] != 61:
        raise ValueError('Complete original CoAuthor population required for transfer training')
    rows, source_rows = gzread(path), gzread(source_path)
    if ([{k:v for k,v in r.items() if k not in ('baseline', 'features')} for r in rows]
            != [{k:v for k,v in r.items() if k != 'text'} for r in source_rows]
            or summary['source_sha256'] != filehash(source_path)
            or summary['sentences'] != len(rows)):
        raise ValueError('Transfer training changed T2 sentence or label coverage')
    _, dictionary_hash = feature_source.dictionary(inputs['dictionary_completion'])
    pins = [dictionary_hash, filehash(inputs['encoder_manifest']), len(rows[0]['features'])]
    if summary['feature_pins'] != pins:
        raise ValueError('Transfer dictionary/encoder/feature pins differ')
    evaluation = Path(inputs['evaluation_completion'])
    ep, es = evaluation.parent/'PLAN.json', evaluation.parent/'output/SCIENCE.json'
    completed(evaluation, ep)
    completed(evaluation, es)
    evaluation_plan, evaluation_summary = read(ep), read(es)
    ec = evaluation_plan['config']
    if (evaluation_plan['module'] != 'runners.drive.cards.week5_bk_t2_analysis'
            or ec.get('card') != 'BK-T2' or ec.get('target') != 'b'
            or ec.get('cell') != 'primary' or ec.get('draws') != 2000
            or ec.get('permutations') != 200
            or filehash(evaluation_plan['inputs']['feature_completion']) != filehash(c)
            or evaluation_summary['target'] != 'b'
            or evaluation_summary['cell'] != 'primary'
            or evaluation_summary['control_complete'] is not True):
        raise ValueError('Complete controlled T2(b) writer-separated evaluation required')
    # A useful result is deliberately NOT required. A valid null transfers too;
    # an invalid original instrument is held before external interpretation.
    return rows, pins


def run(output, inputs, config, verification=False):
    if config != dict(card='BK-T2.r-transfer-export', target='b', phase='export'):
        raise ValueError('Unregistered transfer export')
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    rows, pins = dependencies(inputs)
    def check():
        if (output/'YIELD_REQUEST.json').exists():
            raise InterruptedError('Owner request between complete ridge fits')
    try:
        with threadpool_limits(limits=2):
            result = fit(rows, pins, check)
    except InterruptedError:
        return dict(status='yielded', reason='bounded export restart required; fresh empty output')
    binding = dict(inputs={k:filehash(v) for k,v in inputs.items()}, config=config,
                   implementation=filehash(__file__),
                   original_analysis=filehash(original.__file__),
                   original_features=filehash(feature_source.__file__))
    if verification:
        if (binding != read(output/'BINDING.json')
                or not original.same(result, read(output/'PRIVATE_MODEL.json'))):
            raise ValueError('Fresh complete CoAuthor model refit differs')
        return dict(verified=True, full_coauthor_models_refitted=True, external_labels_read=False)
    write_equal(output/'BINDING.json', binding)
    write_equal(output/'PRIVATE_MODEL.json', result)
    return dict(status='complete', external_labels_read=False)


def execute(output, inputs, config):
    return run(output, inputs, config)


def verify(output, inputs, config):
    return run(output, inputs, config, True)
