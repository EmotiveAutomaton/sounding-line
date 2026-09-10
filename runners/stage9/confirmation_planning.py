"""B01 allocation for paired independent units, retaining the complete seed grid.

DESIGN CHECK: B01/B02/X05; LESSONS 3--5, CONTROLS 6--7.
NULL: missing seeds/targets, repeated targets, nonfinite values, absent variance
or a reserve shortfall cannot acquire confirmatory status. ALTERNATIVE: averaging
within each independent unit before estimating variance supports one fixed sample
plan for a positive, negative or centered equivalence claim. Target observations
and adapters never become independent source units. Exhaustive outcomes are a
valid allocation (adequate or exploratory) or explicit refusal; none is a result.

This is the allocation component, not a claim selector or a confirmation executor.
The caller must verify source grouping, complete producer receipts, gate scope,
untouched reserve and the pre-discovery practical threshold before freezing B01.
Crossed person/stimulus designs require their own planning model; this component
must not erase that dependence by accepting a person-only variance estimate.
"""
import math
from collections import defaultdict
from statistics import NormalDist, stdev

from .scoring import confirmation_size

SCIENTIFIC_SEEDS = (9001, 9002, 9003)
KINDS = ('positive', 'negative', 'equivalence')


def unit_estimates(rows, seeds):
    """Equal target means within seed/unit, then equal seed means within unit.

    Each independent unit must have identical target coverage for every seed.
    Different units may contain different numbers of targets. The complete grid
    and each seed's mean remain available for the final packet and audit.
    """
    if tuple(seeds) not in ((None,), SCIENTIFIC_SEEDS):
        raise ValueError('use the full three scientific seeds or the untrained arm')
    cells = defaultdict(dict)
    for row in rows:
        if set(row) != {'unit', 'target', 'seed', 'difference'}:
            raise ValueError('exact independent-unit/target/seed/difference fields required')
        if any(not isinstance(row[k], str) or not row[k].strip() for k in ('unit', 'target')):
            raise ValueError('nonempty source-unit and target identities required')
        seed, value = row['seed'], row['difference']
        if (seed not in seeds or seed is not None and type(seed) is not int
                or type(value) not in (int, float) or not math.isfinite(value)):
            raise ValueError('missing seed or nonfinite/invalid paired difference')
        key = (row['unit'], seed)
        if row['target'] in cells[key]:
            raise ValueError('repeated target cannot increase the independent sample')
        cells[key][row['target']] = float(value)
    units = sorted({key[0] for key in cells})
    if len(units) < 2:
        raise ValueError('at least two independent discovery units required')
    seed_values = {str(seed): [] for seed in seeds}
    values = []
    for unit in units:
        target_sets = [set(cells[(unit, seed)]) for seed in seeds]
        if not target_sets[0] or any(own != target_sets[0] for own in target_sets):
            raise ValueError('every unit needs the same complete target set for every seed')
        means = [math.fsum(cells[(unit, seed)].values()) / len(target_sets[0]) for seed in seeds]
        for seed, value in zip(seeds, means):
            seed_values[str(seed)].append(value)
        values.append(math.fsum(means) / len(seeds))
    return {'units': units, 'values': values, 'n_units': len(units),
            'n_observations': sum(len(v) for v in cells.values()),
            'mean': math.fsum(values) / len(values), 'standard_deviation': stdev(values),
            'seeds': list(seeds), 'seed_means': {
                seed: math.fsum(own) / len(own) for seed, own in seed_values.items()},
            'estimand': 'equal independent-unit mean of equal-seed within-unit target means'}


def allocate(rows, *, seeds, threshold, available_units, kind, design='one_way'):
    """Normal-approximation planning under the brief's fixed family of three.

    Directional claims use the existing conservative two-sided sizing at the
    practical threshold. Equivalence uses two one-sided tests at alpha/3 and
    assumes the true paired difference is zero: P(|Z| < margin/SE - zcrit)=.9.
    This centered planning assumption is explicit and is not an observed result.
    Reserve size limits execution, never changes the practical threshold or power
    target. A short reserve remains exploratory with its detectable effect shown.
    """
    if design != 'one_way':
        raise ValueError('crossed dependence requires a separately validated planning model')
    if kind not in KINDS or type(threshold) not in (int, float) or not math.isfinite(threshold) or threshold <= 0:
        raise ValueError('explicit claim kind and positive predeclared threshold required')
    if type(available_units) is not int or available_units < 1:
        raise ValueError('a positive count of independently verified reserve units is required')
    summary = unit_estimates(rows, seeds)
    sd = summary['standard_deviation']
    if sd <= 0:
        raise ValueError('zero discovery variance needs an exact-case analysis, not normal planning')
    normal, alpha, family, power = NormalDist(), .05, 3, .90
    if kind == 'equivalence':
        critical = normal.inv_cdf(1 - alpha / family)
        planning_constant = critical + normal.inv_cdf((1 + power) / 2)
        required = max(60, math.ceil((planning_constant * sd / threshold) ** 2))
        method = 'normal approximation to two one-sided equivalence tests; centered true effect; Holm family of three'
    else:
        prior = confirmation_size(sd, effect=threshold, power=power, family=family)
        required = prior['n']
        critical = normal.inv_cdf(1 - alpha / (2 * family))
        planning_constant = critical + normal.inv_cdf(power)
        method = prior['planning']
    planned = min(required, available_units)
    signal = threshold * math.sqrt(planned) / sd
    achieved = (max(0., 2 * normal.cdf(signal - critical) - 1) if kind == 'equivalence'
                else 1 - normal.cdf(critical - signal) + normal.cdf(-critical - signal))
    return {'discovery': summary, 'claim_kind': kind, 'practical_threshold': threshold,
            'required_units': required, 'available_units': available_units, 'planned_units': planned,
            'planning_power_target': power, 'normal_approximation_power_at_planned_units': achieved,
            'detectable_effect_or_centered_equivalence_margin': planning_constant * sd / math.sqrt(planned),
            'power_adequate': available_units >= required,
            'allocation_scope': 'adequately sized; admission and confirmation still required' if available_units >= required else 'exploratory reserve shortfall',
            'planning_assumed_true_difference': 0. if kind == 'equivalence' else (threshold if kind == 'positive' else -threshold),
            'familywise_alpha': alpha, 'family': family, 'planning_method': method,
            'scientific_confirmation': False, 'reserve_outcomes_read': False}
