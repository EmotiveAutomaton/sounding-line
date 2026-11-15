"""IN15: the prior state brought to a five-reader report.

DESIGN CHECK: LESSONS 2-3, CONTROLS 6-7. A 0.4 multinomial-logit utility
plant yields about 0.395 chooser-minus-nonchooser SD; zero plant is near zero.
The actual primary is a difference of means, never a fitted logit slope.
Only twelve observed prior feelings map to the thirteen possible labels.
"""
from __future__ import annotations
from pathlib import Path
from . import week6_in13_in15_common_v1 as common
import numpy as np
import pandas as pd

MODULE = 'runners.drive.cards.week6_in15_v1'


def settings(config):
    common.config_check(config, ('IN15',))
    if config['scope'] != 'qualified_real_events': raise ValueError('IN15 retains the qualified real-event primary cohort')
    return {k: v for k, v in config.items() if k not in ('max_new_draws', 'max_wall_seconds')} | {'draws': 2000}


def load(inputs, config):
    _, frame, identity = common.canonical_source(inputs, 'IN15', config['scope'])
    return frame, identity


def prepare(frame):
    required = {'text_id', 'prolific_id', 'emotion', 'original_emotion', 'unpleasantness', *common.FEELINGS}
    if not required.issubset(frame.columns): raise ValueError('Missing prior feeling; no no-emotion prior may be imputed')
    common.validate_readers(frame)
    data = frame.sort_values(['text_id', 'prolific_id']).reset_index(drop=True)
    if not data.original_emotion.isin(common.LABELS).all() or not data.groupby('text_id').original_emotion.nunique().eq(1).all():
        raise ValueError('Inconsistent writer label within report')
    raw = data[list(common.FEELINGS)].to_numpy(float)
    if not np.isfinite(raw).all(): raise ValueError('Missing/nonfinite prior ratings are not imputed')
    means = raw.mean(axis=0); sd = raw.std(axis=0, ddof=1); supported = sd > 1e-12
    z = (raw-means)/np.where(supported, sd, 1)
    keys, code = np.unique(data.prolific_id, return_inverse=True)
    choice = data.emotion.to_numpy(); groups = len(data)//5
    negative = z[:, [common.FEELINGS.index(k) for k in common.NEGATIVE]].mean(axis=1)
    load = z.mean(axis=1); n_sd = float(negative.std(ddof=1)); l_sd = float(load.std(ddof=1))
    return {'keys': keys.tolist(), 'code': code.reshape(groups, 5), 'z': z.reshape(groups, 5, 12),
        'chosen': (choice[:, None] == np.array(common.FEELINGS)[None, :]).reshape(groups, 5, 12),
        'supported': supported, 'scales': {label: {'mean': float(means[i]), 'SD': float(sd[i]), 'supported': bool(supported[i])}
            for i, label in enumerate(common.FEELINGS)},
        'negative': (negative/np.where(n_sd > 1e-12, n_sd, 1)).reshape(groups, 5),
        'load': (load/np.where(l_sd > 1e-12, l_sd, 1)).reshape(groups, 5),
        'unpleasantness': data.unpleasantness.to_numpy(float).reshape(groups, 5),
        'correct': (choice == data.original_emotion.to_numpy()).astype(float).reshape(groups, 5),
        'secondary_scale_supported': {'negative': n_sd > 1e-12, 'load': l_sd > 1e-12},
        'counts': {'reports': groups, 'reader_rows': len(data), 'readers': len(keys),
                   'no_emotion_choices_without_prior': int(np.sum(choice == 'no-emotion'))}}


def centered_slope(x, y, w, independent=False):
    if independent:
        # Independent weighted within-report covariance from scalar sums.
        sw = w.sum(axis=1); sx = (w*x).sum(axis=1); sy = (w*y).sum(axis=1)
        valid = sw > 0
        numerator = float((w*x*y).sum()-np.sum(sx[valid]*sy[valid]/sw[valid]))
        denominator = float((w*x*x).sum()-np.sum(sx[valid]**2/sw[valid]))
    else:
        total = w.sum(axis=1, keepdims=True); safe = np.maximum(total, 1)
        xc = x-(w*x).sum(axis=1, keepdims=True)/safe
        yc = y-(w*y).sum(axis=1, keepdims=True)/safe
        numerator = float(np.sum(w*xc*yc)); denominator = float(np.sum(w*xc*xc))
    return None if denominator <= 1e-10 else numerator/denominator


def evaluate(prepared, weights, independent=False):
    w = weights[prepared['code']]; z = prepared['z']; chosen = prepared['chosen']
    if independent:
        # Flattened report/label bins independently reconstruct the two means.
        groups = z.shape[0]; index = np.repeat(np.arange(groups)*12, 5*12)+np.tile(np.arange(12), groups*5)
        weights_flat = np.broadcast_to(w[:, :, None], z.shape).ravel(); c = chosen.ravel(); values = z.ravel()
        n1 = np.bincount(index, weights=weights_flat*c, minlength=groups*12).reshape(groups, 12)
        n0 = np.bincount(index, weights=weights_flat*~c, minlength=groups*12).reshape(groups, 12)
        s1 = np.bincount(index, weights=weights_flat*c*values, minlength=groups*12).reshape(groups, 12)
        s0 = np.bincount(index, weights=weights_flat*~c*values, minlength=groups*12).reshape(groups, 12)
    else:
        n1 = (w[:, :, None]*chosen).sum(axis=1); n0 = (w[:, :, None]*~chosen).sum(axis=1)
        s1 = (w[:, :, None]*chosen*z).sum(axis=1); s0 = (w[:, :, None]*~chosen*z).sum(axis=1)
    eligible = (n1 > 0) & (n0 > 0) & prepared['supported'][None, :]
    difference = s1/np.maximum(n1, 1)-s0/np.maximum(n0, 1)
    count = int(eligible.sum()); value = None if count == 0 else float(difference[eligible].mean())
    by_label = {label: None if not eligible[:, i].any() else float(difference[eligible[:, i], i].mean())
                for i, label in enumerate(common.FEELINGS)}
    return {'primary': value, 'eligible_cells': count,
        'eligible_by_label': {label: int(eligible[:, i].sum()) for i, label in enumerate(common.FEELINGS)},
        'by_label': by_label,
        'negative_to_unpleasantness': centered_slope(prepared['negative'], prepared['unpleasantness'], w, independent)
            if prepared['secondary_scale_supported']['negative'] else None,
        'brought_amount_to_writer_match': centered_slope(prepared['load'], prepared['correct'], w, independent)
            if prepared['secondary_scale_supported']['load'] else None}


def calculate(frame, output, identity, config, independent=False):
    semantic = settings(config); prepared = prepare(frame); keys = prepared['keys']
    base = {'card': 'IN15', 'record_kind': 'claim', 'theory_tags': ['H18-SCHEMA', 'READER-CEILING'],
        'by_construction': identity.get('constructed', False), 'activation': [], 'source_identity': identity,
        'semantic': semantic, 'scope': 'adult prompted reports and crowd-reader self-report; lowercase evidence',
        'standing_habits_count_as_brought': True, 'state_and_setting_separated': False,
        'scales': prepared['scales'], 'counts': prepared['counts'],
        'no_emotion_rule': 'no prior no-emotion rating exists; no-emotion cells are absent, never imputed',
        'metric': 'per-feeling sample-SD standardization over all reader-response rows, frozen through resampling',
        'resampling': 'whole reader identities with multiplicity; all their reports travel together; eligibility recomputed each draw'}
    if len(keys) < 2: return {**base, 'status': 'unsupported', 'complete_card': True, 'reason': 'fewer than two readers'}
    binding = common.digest({'source': identity, 'frame': common.frame_digest(frame), 'semantic': semantic,
        'modules': common.dependencies(__import__(__name__, fromlist=[''])), 'independent': independent})
    score = lambda w: evaluate(prepared, w, independent)
    bank, yielded = common.run_draws(output, binding, score(np.ones(len(keys))), score, keys, config)
    if yielded: return yielded
    primary = common.summary(bank['point']['primary'], [d['primary'] for d in bank['draws']], len(keys), .10)
    if not prepared['supported'].all():
        primary.pop('outcome', None); primary['status'] = 'constant prior feeling, incomplete descriptive primary'
    by_label = {label: common.summary(bank['point']['by_label'][label], [d['by_label'][label] for d in bank['draws']], len(keys), .10)
                for label in common.FEELINGS}
    for value in by_label.values(): value.pop('outcome', None)
    secondary = {}
    for name in ('negative_to_unpleasantness', 'brought_amount_to_writer_match'):
        secondary[name] = common.summary(bank['point'][name], [d[name] for d in bank['draws']], len(keys), .10)
        secondary[name].pop('outcome', None)
    return {**base, 'status': 'complete', 'complete_card': True, 'primary': primary, 'by_label': by_label,
        'secondary': secondary,
        'secondary_definitions': {'negative_to_unpleasantness': 'within-report unpleasantness points per SD of mean seven standardized negative priors',
            'brought_amount_to_writer_match': 'within-report correct-label probability per SD of mean all twelve standardized prior feelings'},
        'cell_support': {'point': bank['point']['eligible_cells'], 'point_by_label': bank['point']['eligible_by_label'],
            'every_draw': [d['eligible_cells'] for d in bank['draws']],
            'every_draw_by_label': [d['eligible_by_label'] for d in bank['draws']]},
        'failed_draw_policy': 'zero eligible cells is retained as failure; no redraw or selected-valid interval',
        'secondary_is_descriptive': True}


def execute(output, inputs, config):
    settings(config); frame, identity = load(inputs, config)
    result = calculate(frame, output, identity, config)
    if result.get('status') != 'yielded': common.io.write_json(Path(output)/'RESULT.json', result)
    return result


def verify(output, inputs, config):
    settings(config); output = Path(output); frame, identity = load(inputs, config)
    answer = calculate(frame, output/'independent-replay', identity, config, True)
    if answer.get('status') == 'yielded': return {**answer, 'verified': False}
    common.compare(common.seal.read(output/'RESULT.json'), answer)
    if (output/'DRAWS.json').exists():
        left = common.seal.read(output/'DRAWS.json'); right = common.seal.read(output/'independent-replay/DRAWS.json')
        common.compare(left['point'], right['point']); common.compare(left['draws'], right['draws'])
    common.io.write_json(output/'independent-replay/RESULT.json', answer)
    return {'verified': True, 'complete_2000_reader_draws_replayed': True,
            'independent_formula': 'flattened weighted cell bins and within-report raw-moment covariance'}
