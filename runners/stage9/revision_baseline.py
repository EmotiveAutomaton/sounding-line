"""Training-only lexical baseline; sealed predictions precede evaluator label access.

DESIGN CHECK: Stage 9 I02/H02; development readiness, not published-model reproduction.
NULL: shuffled labels on balanced synthetic text remove lexical predictive benefit.
ALTERNATIVE: a known training-only text association predicts held-out examples.
Every real development record is predicted in the interpreter capsule, then evaluated.
"""
from collections import Counter, defaultdict
import math
from pathlib import Path
import time

from runners.stage9.common import ROOT, Units, closure, digest, freeze, read, write
from runners.stage9.data import INTENTS, visible_revision
from runners.stage9.features import features
from runners.stage9.runtime import execute
from runners.stage9.scoring import log_score, paired_interval


def fit(rows, view, max_features=5000, alpha=1.0, uniform_mixture=.01):
    if not rows or any(r['split'] != 'train' for r in rows):
        raise ValueError('baseline fitting requires training split only')
    group_counts = Counter(r['independent_unit'] for r in rows)
    vocabulary_counts = Counter()
    for row in rows:
        vocabulary_counts.update(features(visible_revision(row, view)))
    vocabulary = sorted(sorted(vocabulary_counts, key=lambda k: (-vocabulary_counts[k], k))[:max_features])
    vocabulary_set = set(vocabulary)
    terms, totals, classes = defaultdict(Counter), Counter(), Counter()
    for row in rows:
        if not row['labels']:
            continue
        frequencies = Counter(row['labels'])
        x = features(visible_revision(row, view))
        for label, n in frequencies.items():
            if label not in INTENTS:
                raise ValueError('unknown annotation')
            weight = n / len(row['labels']) / group_counts[row['independent_unit']]
            classes[label] += weight
            for word, count in x.items():
                if word in vocabulary_set:
                    terms[label][word] += count * weight
                    totals[label] += count * weight
    if not vocabulary or not classes:
        raise ValueError('no training vocabulary or targets')
    prior = {c: math.log((classes[c] + alpha) / (sum(classes.values()) + alpha * len(INTENTS))) for c in INTENTS}
    likelihood = {c: {w: math.log((terms[c][w] + alpha) / (totals[c] + alpha * len(vocabulary))) for w in vocabulary} for c in INTENTS}
    return {'classes': list(INTENTS), 'log_prior': prior, 'log_likelihood': likelihood,
            'uniform_mixture': uniform_mixture, 'view': view, 'alpha': alpha,
            'training_groups': len(group_counts), 'training_rows': len(rows),
            'method': 'multinomial lexical naive Bayes, equal document-lineage training mass, vocabulary selected on train only'}


def run(prepared, output, receipt_path=None):
    started = time.monotonic()
    prepared, output = Path(prepared), Path(output)
    train = read(prepared / 'train/records.json')
    dev = read(prepared / 'development/records.json')
    if any(row['split'] != 'development' for row in dev):
        raise ValueError('readiness uses development only')
    source = closure([Path(__file__), Path(__file__).with_name('features.py'), Path(__file__).with_name('runtime.py'), Path(__file__).with_name('reader.py')])
    identity = {'prepared': digest(read(prepared / 'IDENTITY.json')), 'train': digest(train), 'development': digest(dev),
                'source': source, 'purpose': 'ordinary predictive baseline readiness on development; not published model reproduction',
                'views': ['artifact', 'process_pair'], 'alpha': 1.0, 'max_features': 5000, 'uniform_mixture': .01}
    units = Units(output, identity)
    if (output / 'COMPLETE.json').exists():
        complete = read(output / 'COMPLETE.json')
        if complete['identity_sha256'] != digest(identity):
            raise ValueError('completed baseline identity mismatch')
        return complete
    all_results = []
    for view in identity['views']:
        params = fit(train, view)
        freeze(output / 'private' / (view + '-parameters.json'), params)
        prior = {k: math.exp(v) for k, v in params['log_prior'].items()}
        for row in dev:
            key = {'unit': row['key'], 'view': view}
            saved = units.get(key)
            if saved is None:
                evidence = visible_revision(row, view)
                task = {'operation': 'text_baseline', 'view': view, 'parameters': params, 'parameters_sha256': digest(params)}
                # The model output is atomically frozen BEFORE labels are scored.
                prediction_path = output / 'predictions' / (digest(key) + '.json')
                if prediction_path.exists():
                    prediction = read(prediction_path)
                    if prediction['task_sha256'] != digest(task) or prediction['evidence_sha256'] != digest(evidence):
                        raise ValueError('stored prediction has different input identity')
                else:
                    result = execute(evidence, task)
                    prediction = {'accepted': result['accepted'], 'prediction': result['prediction'],
                                  'capsule': result['capsule'], 'sources': result['copied_sources'], 'error': result['error'],
                                  'task_sha256': digest(task), 'evidence_sha256': digest(evidence)}
                    freeze(prediction_path, prediction)
                if not prediction['accepted']:
                    raise RuntimeError('baseline capsule failed: ' + str(prediction['error']))
                labels = row['labels']
                if not labels:
                    saved = {'unit': row['independent_unit'], 'record': row['key'], 'view': view, 'excluded': 'no annotated edit', 'labels': 0}
                else:
                    model_score = math.fsum(log_score(prediction['prediction']['probs'], y) for y in labels) / len(labels)
                    prior_score = math.fsum(log_score(prior, y) for y in labels) / len(labels)
                    saved = {'unit': row['independent_unit'], 'record': row['key'], 'view': view, 'model_score': model_score,
                             'prior_score': prior_score, 'difference': model_score - prior_score, 'labels': len(labels)}
                units.put(key, saved)
            all_results.append(saved)
    summaries = {}
    for view in identity['views']:
        included = [r for r in all_results if r['view'] == view and 'excluded' not in r]
        summaries[view] = {'contrast': paired_interval(included), 'included_records': len(included),
                           'excluded_records': len(dev) - len(included), 'target_labels': sum(r['labels'] for r in included)}
    result = {'identity_sha256': digest(identity), 'completed': True, 'source': 'IteraTeR-HUMAN', 'split': 'development',
              'ordinary_predictive_baseline_executed': True, 'published_model_reproduction': False,
              'independent_units': len({r['independent_unit'] for r in dev}), 'views': summaries,
              'wall_seconds': time.monotonic() - started, 'scientific_claim': 'none; development readiness only',
              'not_yet_tested': ['complete cross-source duplicate closure', 'domain transfer', 'model readers', 'held-out discovery', 'confirmation']}
    freeze(output / 'COMPLETE.json', result)
    write(Path(receipt_path) if receipt_path else ROOT / 'intake/ITERATER_BASELINE.json', result)
    return result


if __name__ == '__main__':
    import argparse
    import json
    parser = argparse.ArgumentParser()
    parser.add_argument('prepared', type=Path)
    parser.add_argument('output', type=Path)
    parser.add_argument('--receipt', type=Path, help='versioned summary path; preserves prior public receipts')
    args = parser.parse_args()
    print(json.dumps(run(args.prepared, args.output, args.receipt), sort_keys=True))
