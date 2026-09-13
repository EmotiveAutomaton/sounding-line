"""Whole-cell descriptive comparisons under STAGE10_COMPARISON_FREEZE.

DESIGN CHECK: LESSONS3-5, CONTROLS1-6, READER_HEURISTICS4/5/10 reread.
NULL: identical forecasts have exactly zero paired benefit, independent of row
order or writer replication. ALTERNATIVE: a correct forecast improves Brier
and finite log loss. Invalid predictions remain worst system loss; zero true
support remains infinite log loss. Neither is silently dropped or repaired.
Incomplete, duplicated or mismatched populations refuse before any comparison.
"""
from collections import Counter, defaultdict
import math
import random

from .contracts import canonical, parse_forecast


def score(task, truth, status, forecast):
    if truth not in dict(task.choices):
        raise ValueError('truth outside declared choices')
    if status not in {'VALID', 'INVALID'}:
        raise ValueError('undeclared prediction status')
    if status == 'INVALID':
        if forecast is not None:
            raise ValueError('invalid prediction has a substituted forecast')
        return dict(valid=False, brier_system=1.0, brier=None, log_loss=None,
                    zero_support=False, generated_correct=0, probability_correct=None,
                    confidence=None, probability_confidence=None)
    parsed = parse_forecast(canonical(forecast), task)
    probabilities = parsed['probabilities']
    brier = sum((p - (key == truth)) ** 2 for key, p in probabilities.items()) / 2
    support = probabilities[truth]
    best = max(probabilities.values())
    maxima = [key for key, p in probabilities.items() if p == best]
    # A tied probability prediction receives fractional accuracy, invariant to IDs.
    return dict(valid=True, brier_system=brier, brier=brier,
                log_loss=-math.log(support) if support else 'infinite',
                zero_support=support == 0, generated_correct=int(parsed['choice'] == truth),
                probability_correct=int(truth in maxima) / len(maxima),
                confidence=probabilities[parsed['choice']], probability_confidence=best)


def balanced(rows, key):
    """Equal group weight; each group's available observations share its weight."""
    groups = defaultdict(list)
    for row in rows:
        value = row[key]
        if value is not None:
            groups[row['group']].append(value)
    if not groups:
        return None
    return sum(sum(values) / len(values) for values in groups.values()) / len(groups)


def components(rows):
    """Connect writer/case groups through any shared prompt/constructor identity."""
    parent = {row['group']: row['group'] for row in rows}
    def root(group):
        while parent[group] != group:
            parent[group] = parent[parent[group]]
            group = parent[group]
        return group
    owners = {}
    for row in rows:
        for dependency in row['dependencies']:
            if dependency in owners:
                left, right = sorted((root(row['group']), root(owners[dependency])))
                parent[right] = left
            else:
                owners[dependency] = row['group']
    return {group: root(group) for group in parent}


def calibration(rows, confidence, correct):
    valid = [row for row in rows if row['valid']]
    counts = Counter(row['group'] for row in valid)
    bins = defaultdict(list)
    for row in valid:
        bins[min(9, int(10 * row[confidence]))].append(row)
    result = []
    for index, items in sorted(bins.items()):
        weights = [1 / (len(counts) * counts[r['group']]) for r in items]
        mass = sum(weights)
        result.append(dict(index=index, observations=len(items), writer_or_case_mass=mass,
                           confidence=sum(w*r[confidence] for w, r in zip(weights, items))/mass,
                           accuracy=sum(w*r[correct] for w, r in zip(weights, items))/mass))
    return dict(valid_observations=len(valid), valid_groups=len(counts), bins=result,
                expected_calibration_error=sum(b['writer_or_case_mass'] * abs(b['confidence']-b['accuracy']) for b in result) if valid else None)


def cell(tasks, answers, predictions, population):
    """Inputs must be a complete, explicitly frozen, single-view population."""
    ids = {t.task_id for t in tasks}
    if not ids or len(ids) != len(tasks) or len(ids) != len(answers) or len(ids) != len(predictions):
        raise ValueError('empty, incomplete or duplicated comparison cell')
    if ids != set(answers) or ids != set(predictions):
        raise ValueError('comparison roster mismatch')
    dimensions = {(t.family, t.evidence_view, t.contributor_role, t.exposure) for t in tasks}
    if len(dimensions) != 1 or not population:
        raise ValueError('mixed substrate, view or population')
    rows = []
    for task in sorted(tasks, key=lambda t: t.task_id):
        target, prediction = answers[task.task_id], predictions[task.task_id]
        if not target.get('group') or not isinstance(target.get('dependencies'), list):
            raise ValueError('missing grouping/dependency metadata')
        if not target.get('event') or prediction['task_public'] != task.public():
            raise ValueError('missing event or changed paired task evidence/options')
        row = score(task, target['truth'], prediction['status'], prediction['forecast'])
        row.update(task_id=task.task_id, truth=target['truth'], group=target['group'], event=target['event'],
                   dependencies=target['dependencies'], public=task.public())
        rows.append(row)
    if len({(r['group'], r['event']) for r in rows}) != len(rows):
        raise ValueError('repeated source event in a single-view population')
    groups = components(rows)
    for row in rows:
        row['component'] = groups[row['group']]
    finite = [r for r in rows if isinstance(r['log_loss'], (float, int))]
    valid = [r for r in rows if r['valid']]
    zero = sum(r['zero_support'] for r in rows)
    summary = dict(population=population, dimensions=list(next(iter(dimensions))),
                   attempted=len(rows), valid=len(valid), invalid=len(rows)-len(valid),
                   groups=len(groups), dependency_components=len(set(groups.values())),
                   zero_true_support=zero, finite_log_observations=len(finite),
                   log_loss_valid='infinite' if zero else balanced(valid, 'log_loss'),
                   log_loss_finite=balanced(finite, 'log_loss'),
                   brier_system=balanced(rows, 'brier_system'), brier_valid=balanced(valid, 'brier'),
                   generated_accuracy_system=balanced(rows, 'generated_correct'),
                   generated_accuracy_valid=balanced(valid, 'generated_correct'),
                   probability_accuracy_valid=balanced(valid, 'probability_correct'),
                   generated_calibration=calibration(rows, 'confidence', 'generated_correct'),
                   probability_calibration=calibration(rows, 'probability_confidence', 'probability_correct'))
    return dict(summary=summary, rows=rows)


def uncertainty(rows, key):
    kept = [r for r in rows if r[key] is not None]
    if not kept:
        return dict(observations=0, estimate=None, components=0, method='unavailable')
    labels = sorted({r['component'] for r in kept})
    estimate = balanced(kept, key)
    per_component = {c: balanced([r for r in kept if r['component'] == c], key) for c in labels}
    excluded = [balanced([r for r in kept if r['component'] != c], key) for c in labels] if len(labels) > 1 else []
    result = dict(observations=len(kept), groups=len({r['group'] for r in kept}),
                  estimate=estimate, components=len(labels), component_contrasts=per_component,
                  leave_one_component_out_range=[min(excluded), max(excluded)] if excluded else None,
                  method='descriptive; no population confidence claim')
    if len(labels) >= 10:
        # Resample dependency components; their constituent groups retain equal weight.
        group_means = defaultdict(list)
        for group in sorted({r['group'] for r in kept}):
            subset = [r for r in kept if r['group'] == group]
            group_means[subset[0]['component']].append(sum(r[key] for r in subset)/len(subset))
        rng = random.Random(1001); draws = []
        for _ in range(2000):
            values = [v for c in rng.choices(labels, k=len(labels)) for v in group_means[c]]
            draws.append(sum(values)/len(values))
        draws.sort()
        result.update(method='descriptive component bootstrap; seed 1001; 2000 draws',
                      bootstrap_percentile_95=[draws[49], draws[1949]])
    return result


def paired(treated, comparator):
    a, b = treated['summary'], comparator['summary']
    if a['population'] != b['population'] or a['dimensions'] != b['dimensions']:
        raise ValueError('paired populations differ')
    left = {r['task_id']: r for r in treated['rows']}
    right = {r['task_id']: r for r in comparator['rows']}
    if set(left) != set(right):
        raise ValueError('paired row roster differs')
    rows = []
    for key in sorted(left):
        x, y = left[key], right[key]
        if any(x[k] != y[k] for k in ('public', 'truth', 'group', 'event', 'dependencies', 'component')):
            raise ValueError('paired evidence, options or grouping differs')
        rows.append(dict(group=x['group'], component=x['component'],
                         brier_benefit=y['brier_system']-x['brier_system'],
                         generated_accuracy_benefit=x['generated_correct']-y['generated_correct'],
                         log_benefit=y['log_loss']-x['log_loss'] if isinstance(x['log_loss'], (float,int)) and isinstance(y['log_loss'], (float,int)) else None))
    return dict(direction='positive favors treated; comparator loss minus treated loss',
                attempted_pairs=len(rows), treated_invalid=a['invalid'], comparator_invalid=b['invalid'],
                treated_zero_support=a['zero_true_support'], comparator_zero_support=b['zero_true_support'],
                brier=uncertainty(rows, 'brier_benefit'), finite_log=uncertainty(rows, 'log_benefit'),
                generated_accuracy=uncertainty(rows, 'generated_accuracy_benefit'))
