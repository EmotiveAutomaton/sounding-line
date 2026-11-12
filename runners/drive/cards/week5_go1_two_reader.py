"""R4: frozen GO1 roster, encoder-minus-TFIDF primary, two-reader support.

DESIGN CHECK: LESSONS 3-5 and CONTROLS 6-7. Preserve the original allocation,
author unit, full-text encoding and signed bar. A missing language-model bank
cannot remove a query. Actual two-bank differences supply amendment P's SE.
"""
from pathlib import Path
import hashlib
import json
import math
import numpy as np
from . import week5_go as core
from . import week5_go1_pipeline_v2 as original
from . import week5_qualification_io as io

MODULE = 'runners.drive.cards.week5_go1_two_reader'
READERS = {'tfidf', 'encoder'}
BAR = .05


def compare(rows, roster, bank, draws=2000):
    if set(bank) != READERS:
        raise ValueError('R4 primary requires exactly TFIDF and encoder banks')
    if draws not in (200, 2000):
        raise ValueError('Registered primary/texture draw count required')
    if not roster:
        return {'status': 'unsupported', 'outcome': 'below floor, descriptive', 'documents': 0}, np.empty(0)
    shape = (len(roster), len(roster[0]['candidates']))
    if any(np.asarray(v).shape != shape for v in bank.values()):
        raise ValueError('Reader bank shape differs from fixed roster')
    result = core.compare(rows, roster, bank, draws)
    result.update(primary_reader='encoder', primary_contrast='encoder minus tfidf',
                  primary_bar=BAR, support_readers=sorted(READERS),
                  language_model_secondary={'status': 'waiting_on_R1_verified_reader',
                      'same_roster_required': True, 'changes_primary_support': False},
                  record_kind='claim', theory_tags=[], by_construction=False)
    if result.get('status') != 'ok':
        result.update(primary_ready=False, outcome='below floor, descriptive')
        return result, np.empty(0)
    supported = np.logical_and.reduce([np.isfinite(bank[n]).all(axis=1) for n in sorted(READERS)])
    selected = [a for a, keep in zip(roster, supported) if keep]
    correct = {n: core.correctness(bank[n][supported], selected) for n in READERS}
    people = np.asarray([rows[a['query']]['author'] for a in selected])
    unique, code = np.unique(people, return_inverse=True)
    counts = np.bincount(code)
    sums = {n: np.bincount(code, weights=correct[n], minlength=len(unique)) for n in READERS}
    rng = np.random.default_rng(core.SEED)
    values = []
    for _ in range(draws):
        weight = np.bincount(rng.integers(0, len(unique), len(unique)), minlength=len(unique))
        denom = weight @ counts
        values.append(float(weight @ sums['encoder'] / denom) - float(weight @ sums['tfidf'] / denom))
    values = np.asarray(values)
    primary = result['gain_over_lexical']['encoder']
    if np.quantile(values, [.025, .975]).tolist() != primary['interval']:
        raise ValueError('Primary SE bank differs from original paired author bootstrap')
    se = float(np.std(values, ddof=1))
    lo, hi = primary['interval']
    outcome = 'supports' if lo > BAR else 'against' if hi < 0 or (lo >= -BAR and hi <= BAR) else 'inconclusive'
    if result['authors'] < 20:
        outcome = 'below floor, descriptive'
    result.update(primary_ready=True, outcome=outcome,
                  next_branch='GO1.r' if lo > BAR else 'GO1.d',
                  primary={**primary, 'bar': BAR, 'bootstrap_standard_error': se,
                           'sees': 2.8 * se, 'supports_at': BAR + 2.8 * se,
                           'approximation': 'normal approximation; may be optimistic',
                           'limited_sensitivity': bool(2.8 * se > BAR)})
    if result['primary']['limited_sensitivity']:
        result['report_first_line'] = f'limited sensitivity: sees effects of about {2.8 * se:.6g} or more; the bar is {BAR:g}'
    return result, values


def bank(path, name, rows, roster):
    path = Path(path).resolve()
    root = path.parent
    complete = json.loads((root / 'COMPLETE.json').read_text('utf8'))
    verified = json.loads((root / 'VERIFIED.json').read_text('utf8'))
    plan = json.loads((root / 'PLAN.json').read_text('utf8'))
    if path.name != 'output' or complete.get('status') != 'COMPLETE' or complete.get('fresh_process_verified') is not True or verified.get('verified') is not True:
        raise ValueError('Complete independently verified reader bank required')
    if plan.get('module') != MODULE or plan.get('config', {}).get('reader') != name:
        raise ValueError('Reader producer identity differs')
    receipt = json.loads((path / 'SCORED.json').read_text('utf8'))
    if receipt.get('reader') != name or receipt.get('r4_module_sha256') != io.sha(__file__):
        raise ValueError('Reader receipt identity differs')
    for filename, field in [('scores.npy', 'scores_sha256'), ('ALLOCATION.json', 'allocation_sha256'), ('ROWS.json', 'rows_sha256')]:
        actual = io.sha(path / filename)
        if actual != receipt.get(field) or actual != complete.get('outputs', {}).get('output/' + filename):
            raise ValueError('Reader output changed or is not bound by completion')
    if complete.get('outputs', {}).get('output/SCORED.json') != io.sha(path / 'SCORED.json'):
        raise ValueError('Reader receipt is not bound by completion')
    if json.loads((path / 'ALLOCATION.json').read_text('utf8'))['allocation'] != roster or json.loads((path / 'ROWS.json').read_text('utf8'))['documents'] != rows:
        raise ValueError('Reader source/roster/author sample differs')
    return np.load(path / 'scores.npy', allow_pickle=False)


def execute(output, inputs, config):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    phase = config.get('phase')
    if phase == 'GO1-prepare':
        rows, roster = original.prepared_rows(inputs, config)
        field, rest = config.get('field', 'motivation'), config.get('rest', 'rest')
        texts = [r[rest] for r in rows] + [r[field] for r in rows]
        count = len(set(texts))
        digest = lambda value: hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
        result = {'source_only': True, 'documents': len(rows), 'queries': len(roster),
                  'author_clusters': len({rows[a['query']]['author'] for a in roster}),
                  'unique_encoder_texts': count, 'first_five_percent_texts': math.ceil(.05 * count),
                  'rows_binding': digest(rows), 'allocation_binding': digest(roster),
                  'module_sha256': io.sha(__file__), 'no_scientific_result': True}
        io.write_json(output / 'PREPARED.json', result)
        return result
    if phase == 'GO1-score':
        if config.get('reader') not in READERS:
            raise ValueError('R4 primary has no language-model scoring dependency')
        with io.publication([(core, 'write')]):
            result = original.execute(output, inputs, config)
        if result.get('status') == 'yielded':
            progress = json.loads((output / 'vectors/PROGRESS.json').read_text('utf8')) if (output / 'vectors/PROGRESS.json').exists() else {}
            io.write_json(output / 'PROGRESS.json', {'phase': 'encoder_vectors',
                'completed': progress.get('cached', 0) + progress.get('new', 0), 'total': progress.get('total', 0)})
            return {**result, 'phase': phase, 'reason': 'sealed encoder vector boundary'}
        if result.get('status') != 'unsupported':
            result['r4_module_sha256'] = io.sha(__file__)
            result['primary_role'] = 'encoder-minus-tfidf; language model secondary only'
            io.write_json(output / 'SCORED.json', result)
        return result
    if phase != 'GO1-collect':
        raise ValueError('GO1 R4 phase is unsupported')
    if set(inputs.get('readers', {})) != READERS:
        raise ValueError('R4 collection requires exactly two reader banks')
    rows, roster = original.prepared_rows(inputs, config)
    scores = {name: bank(inputs['readers'][name], name, rows, roster) for name in sorted(READERS)}
    draws = int(config.get('draws', 2000))
    cell = config.get('cell', 'GO1')
    if cell in ('GO1', 'GO1.r', 'GO1.d') and draws != 2000:
        raise ValueError('Primary/conditional claim requires 2000 draws')
    result, values = compare(rows, roster, scores, draws)
    np.save(output / 'PRIMARY_BOOTSTRAP.npy', values, allow_pickle=False)
    result.update(card=cell, primary_bootstrap_sha256=io.sha(output / 'PRIMARY_BOOTSTRAP.npy'),
                  allocation_sha256=io.sha(Path(inputs['readers']['tfidf']) / 'ALLOCATION.json'),
                  rows_sha256=io.sha(Path(inputs['readers']['tfidf']) / 'ROWS.json'),
                  source_variant={k: v for k, v in config.items() if k not in ('phase', 'draws')})
    if draws == 200:
        result['record_kind'] = 'texture'
        result['descriptive_only'] = True
    io.write_json(output / 'RESULT.json', result)
    return result


def verify(output, inputs, config):
    output = Path(output)
    actual = execute(output / 'independent-replay', inputs, config)
    if actual.get('status') == 'yielded':
        return {**actual, 'verified': False}
    name = 'PREPARED.json' if config['phase'] == 'GO1-prepare' else 'SCORED.json' if config['phase'] == 'GO1-score' and actual.get('status') != 'unsupported' else 'RESULT.json'
    if actual != json.loads((output / name).read_text('utf8')):
        raise ValueError('Complete R4 independent replay differs')
    numeric = 'scores.npy' if name == 'SCORED.json' else 'PRIMARY_BOOTSTRAP.npy'
    if (output / numeric).exists() and not np.array_equal(np.load(output / numeric, allow_pickle=False), np.load(output / 'independent-replay' / numeric, allow_pickle=False), equal_nan=True):
        raise ValueError('Every R4 score/draw must independently replay')
    return {'verified': True, 'complete_replay': True, 'two_reader_support': True}
