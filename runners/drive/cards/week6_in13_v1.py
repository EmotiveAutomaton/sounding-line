"""IN13: frozen appraisal profiles, twin-label comparison and gated motives.

DESIGN CHECK: LESSONS 2-3, CONTROLS 6-7. The analytic normal AUC is
Phi(.5/sqrt(2)); a 30%-exclusive marker gives .65. Identical evidence gives
.5. Discovery signs never use confirmation writers. Five-pair contrasts use
the same writer draw; an empty fold is retained as an invalid draw.
"""
from __future__ import annotations
from pathlib import Path
import hashlib
import json
import csv
import re
import time
import warnings
from . import week6_in13_in15_common_v1 as common
import numpy as np
import pandas as pd
from scipy.stats import rankdata
from sklearn.exceptions import ConvergenceWarning
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import GroupKFold

MODULE = 'runners.drive.cards.week6_in13_v1'
EXCHANGE_ROOT = Path(__file__).resolve().parents[3]/'docs/exchange'
PAIRS = (('pride', 'joy'), ('guilt', 'shame'), ('fear', 'sadness'), ('anger', 'disgust'), ('trust', 'joy'))
MOTIVES = ('achievement', 'affiliation', 'power')
PREDICTED = ({'achievement': 1, 'power': 1}, {'affiliation': 1}, {'affiliation': -1}, {'power': 1}, {'affiliation': 1})


def settings(config):
    common.config_check(config, ('IN13A', 'IN13B', 'IN13C'), ('im1_primary_coder',))
    if config['scope'] == 'analyst_all6600' and config['phase'] != 'IN13B':
        raise ValueError('All-report scope is only the separately labelled IN13B analyst reference')
    if config['phase'] == 'IN13C' and not config.get('im1_primary_coder'):
        raise ValueError('Part C waits for IM1 and a prospectively frozen primary coder')
    if config['phase'] != 'IN13C' and 'im1_primary_coder' in config:
        raise ValueError('IM1 is read only by Part C')
    return {k: v for k, v in config.items() if k not in ('max_new_draws', 'max_wall_seconds')} | {'draws': 2000}


def load(inputs, config, independent=False):
    extra = {'im1_manifest', 'im1_manifest_sha256', 'im1_choice_manifest', 'im1_choice_manifest_sha256'} if config['phase'] == 'IN13C' else set()
    if set(inputs) != {'source_run', *extra}: raise ValueError('Unexpected IN13 source input')
    choice = read_choice(inputs, config) if config['phase'] == 'IN13C' else None
    frame, _, identity = common.canonical_source({'source_run': inputs['source_run']}, 'IN13', config['scope'])
    if config['phase'] == 'IN13C':
        frame, im1 = load_im1(frame, inputs, identity, choice, independent)
        identity['IM1'] = im1
    return frame, identity


def exact_fields(value, fields, description):
    if not isinstance(value, dict) or set(value) != set(fields):
        raise ValueError(f'{description} fields differ')


def valid_pin(value):
    return isinstance(value, str) and re.fullmatch('[0-9a-f]{64}', value) is not None


def pinned_json(path, expected, description):
    path = Path(path).resolve(); path.relative_to(EXCHANGE_ROOT.resolve())
    if not valid_pin(expected) or common.io.sha(path) != expected:
        raise ValueError(f'{description} pin differs')
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result: raise ValueError('Duplicate IM1 JSON field')
            result[key] = value
        return result
    def reject_constant(value): raise ValueError('Nonfinite IM1 JSON constant')
    return path, json.loads(path.read_text(encoding='utf8'), object_pairs_hook=unique, parse_constant=reject_constant)


def member_path(parent, name):
    if not isinstance(name, str) or not name or Path(name).is_absolute():
        raise ValueError('Relative IM1 member path required')
    path = (parent/name).resolve(); path.relative_to(parent)
    return path


def read_choice(inputs, config):
    _, choice = pinned_json(inputs['im1_choice_manifest'], inputs['im1_choice_manifest_sha256'], 'Prospective primary-coder choice')
    exact_fields(choice, ('schema', 'source_archive_sha256', 'primary_coder', 'coders', 'declared_before_outcomes'), 'Prospective primary-coder choice')
    if choice['schema'] != 'IN13C-choice-v1' or choice['source_archive_sha256'] != common.original.SOURCE_SHA:
        raise ValueError('Prospective choice source/schema differs')
    if choice['declared_before_outcomes'] is not True:
        raise ValueError('Prospective primary-coder declaration required')
    if choice['primary_coder'] != config['im1_primary_coder']:
        raise ValueError('Prospective primary coder differs from frozen configuration')
    coders = choice['coders']
    if not isinstance(coders, dict) or len(coders) != 2 or choice['primary_coder'] not in coders:
        raise ValueError('Prospective choice must bind exactly two coders')
    for coder, pins in coders.items():
        if not isinstance(coder, str) or re.fullmatch('[A-Za-z0-9_]+', coder) is None:
            raise ValueError('Invalid prospective coder key')
        exact_fields(pins, ('implementation_sha256', 'scale_sha256'), 'Prospective coder pins')
        if not all(valid_pin(pin) for pin in pins.values()): raise ValueError('Malformed prospective coder pin')
    return choice


def load_im1(frame, inputs, identity, choice, independent=False):
    manifest_path, manifest = pinned_json(inputs['im1_manifest'], inputs['im1_manifest_sha256'], 'IM1 manifest')
    exact_fields(manifest, ('schema', 'source_archive_sha256', 'table', 'table_sha256', 'coders'), 'IM1 manifest')
    if manifest['schema'] != 'IM1-v2' or manifest['source_archive_sha256'] != common.original.SOURCE_SHA:
        raise ValueError('IM1 source/schema differs')
    coders = manifest['coders']
    if not isinstance(coders, list) or len(coders) != 2:
        raise ValueError('Exactly two individually pinned published coders required')
    for coder in coders:
        exact_fields(coder, ('id', 'publication', 'implementation_sha256', 'scale', 'scale_sha256'), 'IM1 coder')
        if not isinstance(coder['id'], str) or re.fullmatch('[A-Za-z0-9_]+', coder['id']) is None:
            raise ValueError('Invalid IM1 coder key')
    if len({c['id'] for c in coders}) != 2 or {c['id'] for c in coders} != set(choice['coders']):
        raise ValueError('Duplicate or unregistered IM1 coder')
    scales = {}
    for coder in coders:
        if not isinstance(coder['publication'], str) or not coder['publication'].strip() or not valid_pin(coder['implementation_sha256']):
            raise ValueError('Missing published-coder provenance/pin')
        if {k: coder[k] for k in ('implementation_sha256', 'scale_sha256')} != choice['coders'][coder['id']]:
            raise ValueError('Coder implementation/scale differs from prospective choice')
        _, scale = pinned_json(member_path(manifest_path.parent, coder['scale']), coder['scale_sha256'], 'Coder scale')
        exact_fields(scale, ('schema', 'coder', 'motives'), 'Coder scale')
        if scale['schema'] != 'IM1-scale-v1' or scale['coder'] != coder['id']:
            raise ValueError('Coder scale identity differs')
        exact_fields(scale['motives'], MOTIVES, 'Motive scale')
        for spec in scale['motives'].values():
            exact_fields(spec, ('units', 'direction', 'minimum', 'maximum'), 'Motive scale definition')
            if not isinstance(spec['units'], str) or not spec['units'].strip() or spec['direction'] != 'higher-is-more':
                raise ValueError('Documented motive units and higher-is-more direction required')
            for key in ('minimum', 'maximum'):
                if spec[key] is not None and (type(spec[key]) not in (int, float) or not np.isfinite(spec[key])):
                    raise ValueError('Malformed declared motive bound')
            if spec['minimum'] is not None and spec['maximum'] is not None and spec['minimum'] >= spec['maximum']:
                raise ValueError('Motive scale bounds are not ordered')
        scales[coder['id']] = scale
    table = member_path(manifest_path.parent, manifest['table'])
    if not valid_pin(manifest['table_sha256']) or common.io.sha(table) != manifest['table_sha256']:
        raise ValueError('IM1 table pin differs')
    columns = [f"{c['id']}__{m}" for c in coders for m in MOTIVES]
    with table.open(encoding='utf8', newline='') as stream:
        reader = csv.reader(stream, delimiter='\t'); header = next(reader, [])
        if len(header) != len(set(header)) or set(header) != {'text_id', *columns}:
            raise ValueError('IM1 table fields differ; duplicates and undeclared columns refused')
        records = []
        for values in reader:
            if len(values) != len(header): raise ValueError('Malformed IM1 row width')
            if independent:
                row = dict(zip(header, values, strict=True))
                for column in columns: row[column] = float(row[column])
                records.append(row)
        if independent:
            rows = pd.DataFrame(records, columns=header)
    if not independent:
        rows = pd.read_csv(table, sep='\t', usecols=['text_id', *columns], dtype={'text_id': str}, keep_default_na=False)
    # The trusted upstream boundary fixes this count (6600 in production).
    expected_rows = identity['source_rows']
    if len(rows) != expected_rows or rows.text_id.duplicated().any() or rows.text_id.str.strip().eq('').any() or not rows.text_id.eq(rows.text_id.str.strip()).all():
        raise ValueError('IM1 must cover exactly the unique original source reports')
    for column in columns: rows[column] = pd.to_numeric(rows[column], errors='raise')
    if not np.isfinite(rows[columns].to_numpy(float)).all(): raise ValueError('Nonfinite IM1 motive score')
    for coder in coders:
        for motive in MOTIVES:
            spec = scales[coder['id']]['motives'][motive]; values = rows[f"{coder['id']}__{motive}"]
            if spec['minimum'] is not None and values.lt(spec['minimum']).any(): raise ValueError('Score below declared coder scale')
            if spec['maximum'] is not None and values.gt(spec['maximum']).any(): raise ValueError('Score above declared coder scale')
    _, plan, _ = common.seal.complete(inputs['source_run'], 'runners.drive.cards.week5_in')
    salt_path = Path(plan['inputs']['salt'])
    if common.io.sha(salt_path) != identity['salt_sha256']: raise ValueError('IM1 join salt differs')
    salt = salt_path.read_bytes()
    rows.text_id = rows.text_id.map(lambda x: common.original.salted(x, salt, 'crowd-text'))
    if common.digest(sorted(rows.text_id)) != identity['full_text_roster_sha256']:
        raise ValueError('IM1 complete original text roster differs')
    if independent:
        records = {row['text_id']: row for row in rows.to_dict('records')}
        if frame.text_id.duplicated().any() or not set(frame.text_id).issubset(records): raise ValueError('Missing or duplicate primary IM1 join')
        merged = frame.copy()
        for column in columns: merged[column] = [records[key][column] for key in frame.text_id]
    else:
        merged = frame.merge(rows, on='text_id', how='left', validate='one_to_one')
    if merged[columns].isna().any().any(): raise ValueError('Missing IM1 primary row')
    return merged, {'manifest_sha256': inputs['im1_manifest_sha256'], 'table_sha256': manifest['table_sha256'],
                    'coders': coders, 'rows': expected_rows, 'score_averaging': False, 'scales': scales,
                    'choice_manifest_sha256': inputs['im1_choice_manifest_sha256'], 'primary_coder': choice['primary_coder'],
                    'prospective_status': 'pinned owner declaration before outcomes; not an independent historical-timing audit'}


def linear_coefficient(x, y, weights, independent=False):
    if independent:
        root = np.sqrt(weights)
        beta, _, rank, _ = np.linalg.lstsq(x*root[:, None], y*root, rcond=1e-12)
        return None if rank != x.shape[1] else float(beta[1])
    gram = x.T@(weights[:, None]*x); rhs = x.T@(weights*y)
    if np.linalg.matrix_rank(gram, tol=1e-10) != x.shape[1]: return None
    return float(np.linalg.solve(gram, rhs)[1])


def prepare_profiles(frame):
    if frame.text_id.duplicated().any() or not frame.emotion.isin(common.LABELS).all():
        raise ValueError('Invalid IN13 profile roster')
    discovery = frame.loc[frame.discovery_half].copy(); confirmation = frame.loc[~frame.discovery_half].copy()
    if set(discovery.prolific_id) & set(confirmation.prolific_id): raise ValueError('Writer split leakage')
    keys, codes = np.unique(confirmation.prolific_id, return_inverse=True)
    panels = []
    for label in common.LABELS:
        for item in common.APPRAISALS:
            style = [k for k in common.original.STYLE if k != item]
            mu = float(discovery[item].mean()); sd = float(discovery[item].std(ddof=1))
            train_style = discovery[style].mean(axis=1).to_numpy(float)
            sm = float(train_style.mean()); ss = float(train_style.std(ddof=1))
            base = {'label': label, 'item': item, 'style': style, 'scale_mean': mu, 'scale_SD': sd,
                    'style_mean': sm, 'style_SD': ss, 'replication': label in ('fear', 'anger', 'sadness', 'disgust')}
            if not all(np.isfinite(v) for v in (mu, sd, sm, ss)) or sd <= 1e-12 or ss <= 1e-12:
                panels.append({**base, 'supported': False, 'reason': 'constant/missing discovery scale'}); continue
            tx = np.column_stack([np.ones(len(discovery)), discovery.emotion.eq(label), (train_style-sm)/ss])
            ty = (discovery[item].to_numpy(float)-mu)/sd
            coef = linear_coefficient(tx, ty, np.ones(len(discovery)))
            if coef is None:
                panels.append({**base, 'supported': False, 'reason': 'discovery rank failure'}); continue
            x = np.column_stack([np.ones(len(confirmation)), confirmation.emotion.eq(label),
                                 (confirmation[style].mean(axis=1).to_numpy(float)-sm)/ss])
            y = (confirmation[item].to_numpy(float)-mu)/sd
            xx = np.zeros((len(keys), 3, 3)); xy = np.zeros((len(keys), 3))
            np.add.at(xx, codes, x[:, :, None]*x[:, None, :]); np.add.at(xy, codes, x*y[:, None])
            panels.append({**base, 'supported': True, 'discovery_coefficient': coef,
                'direction': int(np.sign(coef)) if abs(coef) > 1e-12 else 0,
                'x': x, 'y': y, 'xx': xx, 'xy': xy})
    return {'keys': keys.tolist(), 'codes': codes, 'panels': panels,
        'split_counts': {'discovery_reports': len(discovery), 'confirmation_reports': len(confirmation),
                         'discovery_writers': discovery.prolific_id.nunique(), 'confirmation_writers': len(keys)}}


def profile_values(prepared, weights, independent=False):
    values = []
    for panel in prepared['panels']:
        if not panel['supported']: values.append(None); continue
        if independent:
            coef = linear_coefficient(panel['x'], panel['y'], weights[prepared['codes']], True)
        else:
            gram = np.einsum('n,nij->ij', weights, panel['xx']); rhs = weights@panel['xy']
            coef = None if np.linalg.matrix_rank(gram, tol=1e-10) < 3 else float(np.linalg.solve(gram, rhs)[1])
        values.append(None if coef is None else panel['direction']*coef)
    return values


def profile_result(prepared, bank):
    rows = []
    valid = [i for i, p in enumerate(prepared['panels']) if p['supported'] and p['direction'] != 0
             and bank['point'][i] is not None and all(d[i] is not None for d in bank['draws'])]
    simultaneous = {}
    if valid:
        values = np.array([[d[i] for i in valid] for d in bank['draws']]); point = np.array([bank['point'][i] for i in valid])
        se = values.std(axis=0, ddof=1); nonzero = se > 1e-12
        maximum = np.max(np.abs((values[:, nonzero]-point[nonzero])/se[nonzero]), axis=1) if nonzero.any() else np.zeros(2000)
        critical = float(np.quantile(maximum, .95))
        simultaneous = {i: [float(point[j]-critical*se[j]), float(point[j]+critical*se[j])] for j, i in enumerate(valid)}
    for i, panel in enumerate(prepared['panels']):
        info = {k: v for k, v in panel.items() if k not in ('x', 'y', 'xx', 'xy')}
        result = common.summary(bank['point'][i], [d[i] for d in bank['draws']], len(prepared['keys']), .10)
        result.pop('outcome', None)
        if i in simultaneous:
            result['simultaneous_interval'] = simultaneous[i]
            if len(prepared['keys']) >= 20: result['outcome'] = common.classify(simultaneous[i], .10)
        if panel.get('direction') == 0: result['status'] = 'no discovery direction, descriptive'
        rows.append({**info, **result})
    return {'table': rows, 'split_counts': prepared['split_counts'], 'primary_scalar': None,
        'multiplicity': 'one simultaneous 95% max-standardized-bootstrap-error band across supported nonzero-direction cells',
        'simultaneous_cells': len(simultaneous), 'total_cells': 273,
        'partial_family': len(simultaneous) != 273, 'nominal_intervals_are_descriptive': True}


def logistic(x, y, c=1., max_iter=2000):
    with warnings.catch_warnings():
        warnings.simplefilter('error', ConvergenceWarning)
        return LogisticRegression(C=c, max_iter=max_iter, solver='lbfgs', random_state=common.SEED).fit(x, y)


def numeric_predictions(train, test, y):
    mu = train.mean(axis=0); sd = train.std(axis=0)+1e-9
    model = logistic((train-mu)/sd, y, 1., 1000)
    return model.decision_function((test-mu)/sd)


def weighted_auc(y, score, weight, independent=False):
    y = np.asarray(y, int); score = np.asarray(score, float); weight = np.asarray(weight, float)
    if np.any(weight < 0) or not np.isfinite(score).all(): raise ValueError('Malformed AUC input')
    if weight[y == 0].sum() <= 0 or weight[y == 1].sum() <= 0: return None
    if independent:
        if np.array_equal(weight, weight.astype(int)):
            yy = np.repeat(y, weight.astype(int)); ss = np.repeat(score, weight.astype(int))
            ranks = rankdata(ss, method='average'); positive = int(yy.sum()); negative = len(yy)-positive
            return float((ranks[yy == 1].sum()-positive*(positive+1)/2)/(positive*negative))
        return float(roc_auc_score(y, score, sample_weight=weight))
    _, code = np.unique(score, return_inverse=True)
    pos = np.bincount(code, weights=weight*y); neg = np.bincount(code, weights=weight*(1-y))
    return float(np.dot(pos, np.cumsum(neg)-neg/2)/(pos.sum()*neg.sum()))


def folds(frame):
    # Raw-ID lexical rank preserves GroupKFold's original group ordering without retaining IDs.
    return list(GroupKFold(5).split(frame, frame.emotion, frame.writer_order))


def fit_pair(frame, pair, coder=None):
    data = frame.loc[frame.emotion.isin(pair)].sort_values('source_ordinal').reset_index(drop=True)
    if data.prolific_id.nunique() < 5: return {'status': 'unsupported', 'pair': list(pair), 'reason': 'fewer than five writers'}
    y = data.emotion.eq(pair[0]).to_numpy(int); ratings = data[list(common.APPRAISALS)].to_numpy(float)
    scores = {'ratings': np.zeros(len(data)), 'augmented' if coder else 'words': np.zeros(len(data))}
    fold_number = np.zeros(len(data), int)
    for number, (tr, te) in enumerate(folds(data)):
        if len(np.unique(y[tr])) != 2 or len(np.unique(y[te])) != 2:
            return {'status': 'unsupported', 'pair': list(pair), 'reason': 'both labels required in each training and held-out fold'}
        if set(data.prolific_id.iloc[tr]) & set(data.prolific_id.iloc[te]): raise ValueError('Writer fold leakage')
        scores['ratings'][te] = numeric_predictions(ratings[tr], ratings[te], y[tr]); fold_number[te] = number
        if coder:
            combined = np.column_stack([ratings, data[[f'{coder}__{m}' for m in MOTIVES]].to_numpy(float)])
            scores['augmented'][te] = numeric_predictions(combined[tr], combined[te], y[tr])
        else:
            vectorizer = TfidfVectorizer(ngram_range=(1, 2), min_df=2, sublinear_tf=True)
            try: train_text = vectorizer.fit_transform(data.hidden_emo_text.iloc[tr])
            except ValueError as error:
                if 'empty vocabulary' not in str(error) and 'no terms remain' not in str(error).lower(): raise
                # Frozen intercept-only fallback, with explicit no-vocabulary disclosure.
                scores['words'][te] = np.log((y[tr].sum()+.5)/((1-y[tr]).sum()+.5)); continue
            model = logistic(train_text, y[tr], 10.)
            scores['words'][te] = model.decision_function(vectorizer.transform(data.hidden_emo_text.iloc[te]))
    return {'status': 'complete', 'pair': list(pair), 'writers': data.prolific_id.tolist(), 'y': y.tolist(),
            'fold': fold_number.tolist(), 'scores': {k: v.tolist() for k, v in scores.items()}}


def pair_values(pair_fits, keys, weights, independent=False):
    lookup = dict(zip(keys, weights, strict=True)); pairs = []
    for fit in pair_fits:
        if fit['status'] != 'complete': pairs.append(None); continue
        w = np.array([lookup[k] for k in fit['writers']]); fold = np.array(fit['fold']); y = np.array(fit['y'])
        values = {}
        for arm, score in fit['scores'].items():
            score = np.array(score)
            aucs = [weighted_auc(y[fold == k], score[fold == k], w[fold == k], independent) for k in range(5)]
            values[arm] = None if any(v is None for v in aucs) else float(np.mean(aucs))
        other = 'augmented' if 'augmented' in values else 'words'
        gap = None if values['ratings'] is None or values[other] is None else values[other]-values['ratings']
        pairs.append({**values, 'gap': gap})
    gaps = [None if p is None else p['gap'] for p in pairs]
    return {'pairs': pairs, 'mean_gap': None if any(v is None for v in gaps) else float(np.mean(gaps))}


def secondary(frame, pair):
    data = frame.loc[frame.emotion.isin(pair)]; y = data.emotion.eq(pair[0]).to_numpy(int)
    x = data[list(common.APPRAISALS)].to_numpy(float); sd = x.std(axis=0, ddof=1)
    gap = (x[y == 1].mean(axis=0)-x[y == 0].mean(axis=0))/np.where(sd > 1e-12, sd, 1)
    indices = sorted(range(21), key=lambda i: (-abs(gap[i]), common.APPRAISALS[i]))[:6]
    ratings = [{'item': common.APPRAISALS[i], 'standardized_first_minus_second': float(gap[i])} for i in indices]
    vectorizer = TfidfVectorizer(ngram_range=(1, 1), min_df=5, sublinear_tf=True, stop_words='english')
    try: xt = vectorizer.fit_transform(data.hidden_emo_text)
    except ValueError as error:
        if not any(t in str(error).lower() for t in ('empty vocabulary', 'no terms remain', 'max_df corresponds')): raise
        return {'ratings': ratings, 'words': [], 'word_status': 'unsupported vocabulary'}
    model = logistic(xt, y, 10.); words = vectorizer.get_feature_names_out(); coef = model.coef_[0]
    return {'ratings': ratings, 'words': {label: [{'word': str(words[i]), 'weight': float(coef[i])}
            for i in sorted(range(len(words)), key=lambda i: (sign*coef[i], words[i]))[:30]]
            for label, sign in ((pair[0], -1), (pair[1], 1))},
            'word_scope': 'descriptive full-pair unigram fit; private aggregate vocabulary output'}


def calculate(frame, output, identity, config, independent=False):
    semantic = settings(config); output = Path(output); output.mkdir(parents=True, exist_ok=True)
    binding = common.digest({'source': identity, 'frame': common.frame_digest(frame), 'semantic': semantic,
                             'modules': common.dependencies(__import__(__name__, fromlist=[''])), 'independent': independent})
    base = {'card': config['phase'], 'record_kind': 'claim', 'theory_tags': ['H18-S1', 'TRIGGER-CONTENT'],
        'by_construction': identity.get('constructed', False), 'activation': [], 'source_identity': identity,
        'scope': 'adult prompted self-report; lowercase evidence', 'semantic': semantic,
        'analyst_exposure': 'Part B was seen before the packet; confirms a computation, not a blind test'}
    if config['phase'] == 'IN13A':
        prepared = prepare_profiles(frame); keys = prepared['keys']
        if len(keys) < 2: return {**base, 'status': 'unsupported', 'complete_card': True, 'reason': 'fewer than two confirmation writers'}
        evaluate = lambda w: profile_values(prepared, w, independent)
        bank, yielded = common.run_draws(output, binding, evaluate(np.ones(len(keys))), evaluate, keys, config)
        if yielded: return yielded
        return {**base, 'status': 'complete', 'complete_card': True, **profile_result(prepared, bank)}
    coders = [None] if config['phase'] == 'IN13B' else [c['id'] for c in identity['IM1']['coders']]
    if config['phase'] == 'IN13C' and config['im1_primary_coder'] not in coders:
        raise ValueError('Frozen primary coder absent from authenticated IM1')
    keys = sorted(frame.loc[frame.emotion.isin({label for pair in PAIRS for label in pair}), 'prolific_id'].unique())
    if len(keys) < 2: return {**base, 'status': 'unsupported', 'complete_card': True, 'reason': 'fewer than two pair writers'}
    fitted = common.seal.state(output/'FOLDS.json', binding, {'fits': []})
    started = time.monotonic(); added = 0
    tasks = [(coder, pair) for coder in coders for pair in PAIRS]
    while len(fitted['fits']) < len(tasks):
        if common.should_yield(output, started, config, added):
            common.seal.checkpoint(output/'FOLDS.json', fitted)
            return {'status': 'yielded', 'verified': False, 'phase': 'pair_fits', 'completed': len(fitted['fits']), 'total': len(tasks)}
        coder, pair = tasks[len(fitted['fits'])]
        fitted['fits'].append(fit_pair(frame, pair, coder)); added += 1
        common.seal.checkpoint(output/'FOLDS.json', fitted)
    def evaluate(weights):
        return {str(coder): pair_values(fitted['fits'][i*5:(i+1)*5], keys, weights, independent) for i, coder in enumerate(coders)}
    bank, yielded = common.run_draws(output, binding, evaluate(np.ones(len(keys))), evaluate, keys, config)
    if yielded: return yielded
    result = {}
    for ci, coder in enumerate(coders):
        point = bank['point'][str(coder)]; draws = [d[str(coder)] for d in bank['draws']]; pairs = []
        for j, pair in enumerate(PAIRS):
            fit = fitted['fits'][ci*5+j]; p = point['pairs'][j]
            count = len(set(fit.get('writers', [])))
            panel = common.summary(None if p is None else p['gap'],
                [None if d['pairs'][j] is None else d['pairs'][j]['gap'] for d in draws], count, .03 if coder else .05)
            if not coder: panel.pop('outcome', None)
            row = {'pair': list(pair), 'comparison': p, 'gain': panel}
            if coder:
                part = frame.loc[frame.emotion.isin(pair)]; sign = {}
                for motive, expected in PREDICTED[j].items():
                    column = f'{coder}__{motive}'
                    gap = float(part.loc[part.emotion.eq(pair[0]), column].mean()-part.loc[part.emotion.eq(pair[1]), column].mean())
                    sign[motive] = {'first_minus_second': gap, 'predicted_direction': expected, 'matches': gap*expected > 0}
                row['predicted_signs'] = sign
                row['point_criterion'] = p is not None and p['gap'] is not None and p['gap'] >= .03 and all(v['matches'] for v in sign.values())
            elif fit['status'] == 'complete': row['secondary'] = secondary(frame, pair)
            pairs.append(row)
        result[str(coder)] = {'pairs': pairs}
        if coder:
            result[str(coder)]['pairs_meeting_point_criterion'] = sum(p['point_criterion'] for p in pairs)
            result[str(coder)]['point_rule_clears'] = sum(p['point_criterion'] for p in pairs) >= 3
        else:
            result[str(coder)]['primary'] = common.summary(point['mean_gap'], [d['mean_gap'] for d in draws], len(keys), .05)
    if config['scope'] == 'analyst_all6600':
        for analysis in result.values():
            analysis.get('primary', {}).pop('outcome', None)
            for row in analysis['pairs']: row['gain'].pop('outcome', None)
        base['record_kind'] = 'run'
    return {**base, 'status': 'complete', 'complete_card': True, 'analyses': result,
        'analyst_reference_only': config['scope'] == 'analyst_all6600',
        'primary_coder': config.get('im1_primary_coder'),
        'conditional_inference': 'fixed writer-held-out trained folds; whole-writer bootstrap does not retrain learners',
        'auc_aggregation': 'equal mean of five held-out fold AUCs, then equal mean over all five pairs',
        'missing_fold_policy': 'any empty-label fold invalidates that draw; no redraw or changed denominator',
        'Part_C_rule': None if not coders[0] else 'point gain >= .03 and all predicted signs on >=3 pairs for frozen primary coder; intervals reported separately'}


def execute(output, inputs, config):
    settings(config); frame, identity = load(inputs, config)
    result = calculate(frame, output, identity, config)
    if result.get('status') != 'yielded': common.io.write_json(Path(output)/'RESULT.json', result)
    return result


def verify(output, inputs, config):
    settings(config); output = Path(output)
    frame, identity = load(inputs, config, independent=True) if config['phase'] == 'IN13C' else load(inputs, config)
    answer = calculate(frame, output/'independent-replay', identity, config, True)
    if answer.get('status') == 'yielded': return {**answer, 'verified': False}
    common.compare(common.seal.read(output/'RESULT.json'), answer)
    if (output/'DRAWS.json').exists():
        left = common.seal.read(output/'DRAWS.json'); right = common.seal.read(output/'independent-replay/DRAWS.json')
        common.compare(left['point'], right['point']); common.compare(left['draws'], right['draws'])
    common.io.write_json(output/'independent-replay/RESULT.json', answer)
    return {'verified': True, 'full_draw_bank_replayed': True,
        'independent_formula': 'weighted row least squares or expanded-observation Mann-Whitney rank AUC',
        'classifier_replay': 'fresh refit of the frozen sklearn estimator, not an independent optimization algorithm'}
