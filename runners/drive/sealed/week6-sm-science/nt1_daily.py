"""Wave-two NT1.s. Fit the registered relative change across consecutive diary days.

DESIGN CHECK. Establish prior-exposure support from the study clock, stressors
and trait before reading any feeling. A missing item with no observed
above-floor feeling is unknown. All repeated measurements of a sampled person
or family share one frequency weight.
"""
from collections import defaultdict
from math import isfinite

import numpy as np
from scipy.special import expit

import mi_source_contract_v1 as contract
import week6_lattice_diary_v1 as form


PARAMETERS = ("current_stressor", "previous_stressor", "trait", "trait_current",
              "trait_previous", "plain_product_difference", "relative_change_difference")
SEED = 2026112013


def identity(value):
    if not isinstance(value, (int, float)) or not isfinite(value) or value <= 0 or int(value) != value:
        raise ValueError("Invalid original person key")
    return int(value)


def support(tables, replay=False):
    """No outcome or risk appraisal is accessed here."""
    spec = contract.fields("M2")
    traits = {}
    for row in tables["survey"]:
        key = identity(row["M2ID"])
        if key in traits:
            raise ValueError("Duplicate survey key")
        value = row[spec["traits"]["neuroticism"]]
        if value is None or np.isnan(value) or value in (-1, 8):
            traits[key] = None
        elif not isfinite(value) or not 1 <= value <= 4:
            raise ValueError("Invalid dictionary trait code")
        else:
            traits[key] = float(value)
    days = defaultdict(dict)
    for row in tables["diary"]:
        key = identity(row["M2ID"])
        day = contract.valid_code(row[spec["study_day"]], range(1, 9), missing=())
        if day is None:
            continue
        if day in days[key]:
            raise ValueError("Duplicate original study day")
        weekday = contract.valid_code(row[spec["weekday"]], range(1, 8), missing=(8, 9))
        codes = [row[stressor["occurrence"]] for stressor in spec["stressors"]]
        if replay:
            decoded = [contract.valid_code(value, (1, 2)) for value in codes]
            event = 1 if any(value == 1 for value in decoded) else (0 if decoded.count(2) == len(decoded) else None)
        else:
            event = contract.occurrence(codes)
        days[key][int(day)] = (weekday, event)
    pairs = []
    for person in sorted(days):
        if traits.get(person) is None:
            continue
        daily = days[person]
        for current in sorted(daily):
            previous = current - 1
            if previous not in daily:
                continue
            now_week, now_stress = daily[current]
            past_week, past_stress = daily[previous]
            if now_stress is None or past_stress is None:
                continue
            if not contract.adjacent_days(previous, current, past_week, now_week, "M2"):
                continue
            pairs.append((person, current, now_stress, past_stress, traits[person]))
    exposed = [row for row in pairs if row[3] == 1]
    return pairs, {row[0] for row in exposed}, len(exposed)


def panel(tables, pairs, replay=False):
    fields = contract.fields("M2")
    outcomes = {}
    for row in tables["diary"]:
        key = identity(row["M2ID"])
        day = contract.valid_code(row[fields["study_day"]], range(1, 9), missing=())
        if day is None:
            continue
        values = [contract.valid_code(row[field], range(5)) for field in fields["negative"]]
        if replay:
            present = [value for value in values if value is not None]
            result = 1 if max(present, default=0) > 0 else (0 if len(present) == len(values) else None)
        else:
            result = 1 if any(v is not None and v > 0 for v in values) else (0 if all(v == 0 for v in values) else None)
        outcomes[key, int(day)] = result
    rows = [(p, now, yesterday, trait, outcomes[p, day]) for p, day, now, yesterday, trait in pairs
            if outcomes[p, day] is not None]
    if not rows:
        return None
    ids, inverse = np.unique([row[0] for row in rows], return_inverse=True)
    data = np.asarray([row[1:] for row in rows], dtype=float)
    return dict(ids=ids, group=inverse, exposures=data[:, :2], trait=data[:, 2], outcome=data[:, 3])


def independent_logit(matrix, outcome, weights):
    """Working-response least squares and line search, independent of the Newton solver."""
    keep = weights > 0
    x, y, w = matrix[keep], outcome[keep], weights[keep]
    if len(np.unique(y)) != 2 or np.linalg.matrix_rank(x) < x.shape[1]:
        raise form.InvalidFit("Singular independent fit")
    beta = np.zeros(x.shape[1])
    for _ in range(100):
        eta = x @ beta
        probability = expit(eta)
        root = np.sqrt(w * probability * (1 - probability))
        weighted = x * root[:, None]
        if np.linalg.cond(weighted) > 1e6:
            raise form.InvalidFit("Separated independent fit")
        delta = np.divide(w * (y - probability), root, out=np.zeros_like(w), where=root > 0)
        step, _, rank, _ = np.linalg.lstsq(weighted, delta, rcond=None)
        score = x.T @ (w * (y - probability))
        if rank != x.shape[1]:
            raise form.InvalidFit("Invalid independent design")
        if np.max(np.abs(step)) <= 1e-7 and np.max(np.abs(score)) / w.sum() <= 1e-9:
            return beta
        current = float(w @ (np.logaddexp(0, eta) - y * eta))
        gain = float(score @ step)
        rate = 1.
        for _ in range(40):
            new = beta + rate * step
            eta_new = x @ new
            if w @ (np.logaddexp(0, eta_new) - y * eta_new) <= current - 1e-4 * rate * gain + 1e-12 * max(1., current):
                beta = new
                break
            rate *= .5
        else:
            raise form.InvalidFit("Independent line search failed")
        if not np.isfinite(beta).all() or np.max(np.abs(beta)) > 100:
            raise form.InvalidFit("Unbounded independent fit")
    raise form.InvalidFit("Independent fit did not converge")


def score(panel, frequencies, replay=False):
    """Standardize the trait across people and the stressors within people on each draw."""
    if panel is None:
        return None
    counts = np.asarray(frequencies, dtype=float)
    group, exposure = panel["group"], panel["exposures"]
    if (counts.shape != (len(panel["ids"]),) or not np.isfinite(counts).all()
            or np.any(counts < 0) or np.any(counts != np.floor(counts)) or counts.sum() == 0):
        raise ValueError("Invalid whole-person frequencies")
    w = counts[group]
    trait = panel["trait"]
    try:
        if replay:
            totals = np.zeros((len(counts), 2))
            np.add.at(totals, group, exposure)
            means = (totals / np.bincount(group)[:, None])[group]
            residual = exposure - means
            scale = np.sqrt(np.average(residual**2, weights=w, axis=0))
            if np.any(scale <= np.finfo(float).eps):
                return None
            standardized = residual / scale
            trait_values = trait[np.unique(group, return_index=True)[1]]
        else:
            standardized, means, _ = form.within(exposure, group, w)
            trait_values = np.bincount(group, weights=trait) / np.bincount(group)
        center = np.average(trait_values, weights=counts)
        sd = np.sqrt(np.average((trait_values - center)**2, weights=counts))
        if sd <= np.finfo(float).eps:
            return None
        z = (trait - center) / sd
        x = np.column_stack((np.ones(len(w)), standardized, means, z, z[:, None] * standardized))
        beta = (independent_logit if replay else form.logit_fit)(x, panel["outcome"], w)
    except (form.InvalidFit, np.linalg.LinAlgError):
        return None
    b1, b2, baseline, c1, c2 = beta[[1, 2, 5, 6, 7]]
    ratio = None if b1 == 0 or b2 == 0 else float(c2/b2 - c1/b1)
    if ratio is not None and not isfinite(ratio):
        ratio = None
    return [float(b1), float(b2), float(baseline), float(c1), float(c2), float(c2-c1), ratio]


def interpretation(ratio, trait, current_interval):
    """The six predeclared outcomes. The plain difference has no verdict."""
    if ratio is None or trait is None or current_interval is None:
        return "could_not_say"
    if ratio[0] > 0:
        return "slower_decay" if trait > 0 else "unread_lower_baseline"
    if ratio[1] < 0:
        return "stronger_first" if current_interval[0] > 0 else "saturation"
    return "proportional_strength" if current_interval[0] > 0 else "no_placement"
