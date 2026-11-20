"""R1.i original ISEAR questionnaire. DESIGN CHECK: LESSONS sections 2–5.

Under the null, adjustment leaves zero association. A planted association must
recover both independent slopes and their paired difference. An aliased target
or ambiguous person key cannot supply a directional result.
"""
from collections import Counter
from dataclasses import dataclass

import numpy as np

FEELINGS = (3, 4)
TERMS = ("anger", "sadness", "anger_minus_sadness")
DOMAINS = {"INTS": range(1, 5), "EXPC": range(1, 4), "PLEA": range(1, 4), "CAUS": range(1, 5)}
DRAWS = 2000
SEED = 20261120


def code(value):
    """Decode original integral response codes without rounding an invalid value."""
    if isinstance(value, (float, np.floating)):
        return int(value) if np.isfinite(value) and value.is_integer() else None
    value = str(value).strip() if value is not None else ""
    return int(value) if value.isascii() and value.isdecimal() else None


def person(row):
    key = tuple(str(row[field]).strip() if row[field] is not None else "" for field in ("COUN", "CITY", "SUBJ"))
    return key if all(key) else None


def source_roster(rows):
    """Consumes just identity and elicited feeling, before the response projection."""
    seen = Counter()
    reports = Counter()
    incomplete = Counter()
    for row in rows:
        feeling = code(row["EMOT"])
        if feeling not in FEELINGS:
            continue
        reports[feeling] += 1
        key = person(row)
        if key is None:
            incomplete[feeling] += 1
        else:
            seen[key, feeling] += 1
    rosters = [{key for key, item in seen if item == feeling} for feeling in FEELINGS]
    return seen, dict(reports=[reports[k] for k in FEELINGS],
                      missing_identity=[incomplete[k] for k in FEELINGS],
                      people_by_feeling=[len(keys) for keys in rosters],
                      people_both=len(rosters[0] & rosters[1]),
                      people_union=len(rosters[0] | rosters[1]),
                      ambiguous_person_feelings=sum(n > 1 for n in seen.values()),
                      duplicate_rows=sum(n - 1 for n in seen.values()))


@dataclass
class Sample:
    indices: np.ndarray
    # Reversed expectation, intensity, pleasantness, agency.
    values: np.ndarray


def prepare(rows, structure_rows, structural):
    if structural["ambiguous_person_feelings"]:
        raise ValueError("Ambiguous original person-by-feeling records")
    observed, structural_again = source_roster(rows)
    if observed != structure_rows or structural_again != structural:
        raise ValueError("Identity and response projections have different rosters")
    persons, missing, observations = set(), {c: Counter() for c in FEELINGS}, {c: [] for c in FEELINGS}
    for row in rows:
        feel, key = code(row["EMOT"]), person(row)
        if feel not in FEELINGS or key is None:
            continue
        items = {k: code(row[k]) for k in DOMAINS}
        absent = [k for k, limits in DOMAINS.items() if items[k] not in limits]
        if absent:
            missing[feel].update(absent)
            continue
        persons.add(key)
        observations[feel].append((key, (4-items["EXPC"], items["INTS"], items["PLEA"], items["CAUS"])))
    roster_index = {k: i for i, k in enumerate(sorted(persons))}
    samples = []
    for feel in FEELINGS:
        ordered = sorted(observations[feel])
        samples.append(Sample(np.array([roster_index[k] for k, _ in ordered], dtype=int),
                              np.array([values for _, values in ordered], dtype=float).reshape(-1,4)))
    overlap = len(set(samples[0].indices) & set(samples[1].indices))
    return samples, dict(complete=[len(s.indices) for s in samples], complete_both=overlap,
                         complete_union=len(persons),
                         invalid_items=[{k: missing[feel][k] for k in DOMAINS} for feel in FEELINGS])


def adjusted(sample, multiplicity):
    """Residual sums of products within agency, then adjustment for pleasantness."""
    w = multiplicity[sample.indices].astype(float)
    if not np.any(w):
        return None
    x, y, p, agency = sample.values.T
    values = np.column_stack((x,y,p))
    means = np.average(values, axis=0, weights=w)
    totals = w @ ((values-means)**2)
    if min(totals[:2]) <= 1e-12:
        return None
    a = agency.astype(int)
    counts = np.bincount(a, weights=w, minlength=5)
    group_means = np.column_stack([np.bincount(a, weights=w*col, minlength=5)
                                  for col in values.T]) / np.maximum(counts[:,None],1)
    residual = values - group_means[a]
    squares = residual.T @ (w[:,None]*residual)
    xx, xy = squares[0,0], squares[0,1]
    if squares[2,2] > 1e-12:
        xx -= squares[0,2]**2 / squares[2,2]
        xy -= squares[0,2]*squares[1,2] / squares[2,2]
    if xx <= 1e-11*max(1.,totals[0]):
        return None
    return float((xy/xx) * np.sqrt(totals[0]/totals[1]))


def adjusted_replay(sample, multiplicity):
    """Direct weighted least squares on standardized reports with agency indicators."""
    w = multiplicity[sample.indices]
    present = w > 0
    if not present.any():
        return None
    x,y,p,agency = sample.values[present].T
    weights = w[present]
    raw = np.column_stack((x,y,p))
    centered = raw - np.average(raw, axis=0, weights=weights)
    scale = np.sqrt(np.average(centered**2, axis=0, weights=weights))
    if min(scale[:2]) <= 1e-12:
        return None
    standardized = centered / np.where(scale > 1e-12,scale,1.)
    nuisance = np.column_stack([agency==a for a in np.unique(agency)])
    if scale[2] > 1e-12:
        nuisance = np.column_stack((nuisance,standardized[:,2]))
    root = np.sqrt(weights)
    controls = root[:, None]*nuisance
    predictor = root*standardized[:,0]
    errors = predictor-controls @ np.linalg.lstsq(controls,predictor,rcond=None)[0]
    if errors @ errors <= 1e-11*(predictor @ predictor):
        return None
    design = np.column_stack((predictor,controls))
    return float(np.linalg.lstsq(design,root*standardized[:,1],rcond=None)[0][0])


def draw_weights(people, index):
    if not 0 <= index < DRAWS or people < 1:
        raise ValueError("Invalid complete roster or draw index")
    rng = np.random.default_rng(np.random.SeedSequence((SEED, index)))
    return np.bincount(rng.integers(0, people, size=people), minlength=people)


def scores(samples, weights, replay=False):
    fit = adjusted_replay if replay else adjusted
    anger, sadness = [fit(sample, weights) for sample in samples]
    difference = None if anger is None or sadness is None else anger-sadness
    return [anger, sadness, difference]


def summarize(point, bank, analytic):
    if len(bank) != DRAWS:
        raise ValueError("Complete original draw bank required")
    result = {}
    floors = (analytic["complete"][0], analytic["complete"][1], min(analytic["complete"]))
    for i, (term, count) in enumerate(zip(TERMS, floors)):
        defined = [row[i] for row in bank if row[i] is not None]
        interval = (np.quantile(defined,[.025,.975]).tolist()
                    if count >= 20 and len(defined)==DRAWS and point[i] is not None else None)
        result[term] = dict(estimate=point[i],interval=interval,defined_draws=len(defined))
    primaries = [result[term] for term in (TERMS[0], TERMS[2])]
    if any(v["interval"] is None for v in primaries):
        result["joint_reading"] = "could not say"
    else:
        met = all(v["estimate"] >= .08 and v["interval"][0] > 0 for v in primaries)
        result["joint_reading"] = "both registered bars met" if met else "joint prediction did not clear both bars"
    return result
