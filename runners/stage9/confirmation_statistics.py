"""B02 calculations over an already executed, frozen paired reserve allocation.

DESIGN CHECK: B02/X05/X11; LESSONS 3--5, CONTROLS 6--7.
NULL: zero gain cannot pass a directional claim; a wide interval cannot establish
equivalence. Missing targets, seeds, units or failed selected claims cannot shrink
the tested family. ALTERNATIVE: independent-unit paired gains of the declared sign,
or an adequately precise equivalence, can pass the frozen statistical calculation.
All results, including failure and inadequate power, remain in the family of three.
This numerical component does not execute readers, verify untouched provenance or
grant scientific confirmation. Its contract must be frozen before reserve access.
"""
import math

from .confirmation_planning import unit_estimates
from .scoring import holm, paired_interval

CONTRACT = {
    'version': 1, 'design': 'one_way', 'target': 'proper_log_score',
    'directional_test': 'two-sided paired independent-unit Student t against zero; declared sign and practical magnitude also required',
    'equivalence_test': 'maximum of two one-sided paired independent-unit Student t tests at the fixed practical bounds',
    'assumption': 'independent source-unit means; Student t calibration exact for normal unit differences, approximate otherwise',
    'interval': 'paired independent-unit percentile bootstrap',
    'bootstrap_seed': 9011, 'bootstrap_draws': 4000,
    'familywise_alpha': .05, 'family': 3,
    'practical_threshold': .05,
}


def tail_probability(mean, standard_error, degrees_freedom, kind, threshold):
    """Stable Student-t tails; equivalence is an intersection-union test."""
    from scipy.stats import t
    if (kind not in ('positive', 'negative', 'equivalence')
            or any(type(v) not in (int, float) or not math.isfinite(v) for v in (mean, standard_error, threshold))
            or standard_error <= 0 or threshold <= 0
            or type(degrees_freedom) is not int or degrees_freedom < 1):
        raise ValueError('finite positive variance, threshold and independent degrees of freedom required')
    if kind == 'equivalence':
        return float(max(t.sf((mean + threshold) / standard_error, degrees_freedom),
                         t.cdf((mean - threshold) / standard_error, degrees_freedom)))
    return float(min(1., 2 * t.sf(abs(mean / standard_error), degrees_freedom)))


def evaluate(packet, rows, assigned_targets):
    """No finite-only subset, re-sizing, seed selection or target deletion."""
    if packet.get('analysis_contract') != CONTRACT:
        raise ValueError('the exact analysis contract must be frozen before reserve access')
    units = packet['reserve_units']
    planning = packet['planning']
    if (not units or len(units) != len(set(units)) or set(assigned_targets) != set(units)
            or len(units) != planning['planned_units'] or planning['practical_threshold'] != .05
            or planning['family'] != 3 or planning['familywise_alpha'] != .05
            or type(planning['power_adequate']) is not bool):
        raise ValueError('complete original reserve allocation and planning contract required')
    if any(not isinstance(v, list) or not v or len(v) != len(set(v))
           or any(not isinstance(k, str) or not k for k in v) for v in assigned_targets.values()):
        raise ValueError('every source unit requires its complete assigned target roster')
    seeds = planning['discovery']['seeds']
    expected = {(u, target, seed) for u, targets in assigned_targets.items() for target in targets for seed in seeds}
    if len(rows) != len(expected) or {(r['unit'], r['target'], r['seed']) for r in rows} != expected:
        raise ValueError('reserve outcomes omit, repeat or add assigned unit/target/seed cells')
    summary = unit_estimates(rows, seeds)
    kind, threshold = planning['claim_kind'], planning['practical_threshold']
    if kind not in ('positive', 'negative', 'equivalence'):
        raise ValueError('unknown frozen claim kind')
    # A degenerate sample is not proof that the whole population is deterministic.
    if summary['standard_deviation'] == 0:
        return {'status': 'UNSUPPORTED_VARIANCE', 'summary': summary,
                'reason': 'zero reserve variance requires a separately validated exact-case analysis',
                'raw_p': None, 'statistical_pass': False, 'scientific_confirmation': False}
    interval = paired_interval([{'unit': u, 'difference': v} for u, v in zip(summary['units'], summary['values'])],
                               seed=CONTRACT['bootstrap_seed'], draws=CONTRACT['bootstrap_draws'])
    mean = summary['mean']
    p = tail_probability(mean, summary['standard_deviation'] / math.sqrt(summary['n_units']),
                         summary['n_units'] - 1, kind, threshold)
    low, high = interval['ci']
    practical = (mean >= threshold and low > 0 if kind == 'positive' else
                 mean <= -threshold and high < 0 if kind == 'negative' else
                 low >= -threshold and high <= threshold)
    return {'status': 'CALCULATED', 'summary': summary, 'interval': interval, 'raw_p': p,
            'practical_criterion_met': practical, 'power_adequate': planning['power_adequate'],
            'statistical_pass': False, 'scientific_confirmation': False,
            'analysis_contract': CONTRACT, 'excluded_units': 0, 'excluded_targets': 0}


def family(packets, outcomes):
    """Retain every frozen claim and failed execution; no replacement slot."""
    ids = [p['id'] for p in packets]
    if len(ids) > 3 or len(ids) != len(set(ids)) or set(outcomes) != set(ids):
        raise ValueError('every frozen selected claim needs exactly one terminal outcome')
    calculations, p_values = {}, {}
    for packet in packets:
        key, outcome = packet['id'], outcomes[packet['id']]
        status = outcome.get('status')
        if status == 'COMPLETE':
            if set(outcome) != {'status', 'rows', 'assigned_targets'}:
                raise ValueError('complete execution needs the exact paired rows and assigned target roster')
            result = evaluate(packet, outcome['rows'], outcome['assigned_targets'])
        elif status in ('FAILED', 'NOT_RUN'):
            if set(outcome) != {'status', 'reason', 'receipt_sha256'} or not outcome['reason']:
                raise ValueError('failed or unrun claim requires its retained execution disposition')
            sha = outcome['receipt_sha256']
            if not isinstance(sha, str) or len(sha) != 64 or any(c not in '0123456789abcdef' for c in sha):
                raise ValueError('retained disposition content hash required')
            result = {**outcome, 'raw_p': None, 'statistical_pass': False, 'scientific_confirmation': False}
        else:
            raise ValueError('unfinished claim cannot enter a final family calculation')
        calculations[key] = result
        # A missing/undefined test occupies its original family slot, never shrinks m.
        p_values[key] = result['raw_p'] if result['raw_p'] is not None else 1.
    correction = holm(p_values, alpha=.05, family=3)
    for key, result in calculations.items():
        result['multiplicity'] = correction[key]
        result['statistical_pass'] = (result['status'] == 'CALCULATED' and correction[key]['reject']
            and result['practical_criterion_met'] and result['power_adequate'])
    return {'claims': calculations, 'selected_count': len(ids), 'family': 3,
            'all_frozen_outcomes_retained': True, 'scientific_confirmation': False,
            'scope': 'numerical calculation only; execution, lineage and live admission are separate obligations'}
