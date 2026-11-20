"""Source projection and independent arithmetic for LD1 and LD2.

DESIGN CHECK (LESSONS 2–5). A full-source person roster precedes every mask.
Changing a source byte, dropping one member of a registered outcome comparison,
or sending non-person weights must fail the affected operation. Singular and
one-class fits produce an explicit missing metric. Numerical guards must pass
under both a true association and a null. The alternative verifier constructs
its own within-person residuals and solves independent weighted regressions.
"""
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.linalg import lstsq
from scipy.special import expit

from . import week6_lattice_diary_v1 as fits
from . import week6_lattice_source_v1 as source
from .es_source_v1 import sha256


CODEBOOK_HASHES = {
    "0056": "2fb4a0678e834593a2dd17fbb6e4eddafcb9fcf14b5884779fea55454189303f",
    "0057": "3083cef2b8a430ea18c6ac2ca54f09af65d6ef6c3c75ba5432aa6adeaf914c20",
}
COMMUNICATION_LABELS = {1: "directly/in person", 2: "via phone/chat"}
INTERACTION_TYPE_LABELS = {1: "job-related task/chore", 2: "private task/chore", 3: "leisure activity"}
PARTNER_COUNT_CODES = (1, 2, 3, 4, 5)


@dataclass
class Projection:
    people: int
    units: np.ndarray
    ordinals: np.ndarray
    values: dict
    counts: dict


@dataclass
class Prepared:
    people: int
    metadata: dict
    specs: dict = field(default_factory=dict)
    panels: dict = field(default_factory=dict)


def next_prompt_frames(member, path, pin, missing_tokens, guard):
    """Authenticated original-order chunks for the descriptive LD3 prompt pairs.

    Preserve literal strings and all prompts, even when the context, clock or
    boredom value is missing. Pairing and whole-person clock exclusions occur
    in LD3 after assembling that complete chronology.
    """
    if member not in ("0057", "0056") or not callable(guard):
        raise ValueError("Unreviewed next-prompt source")
    if not isinstance(missing_tokens, (list, tuple, set, frozenset)) or not missing_tokens:
        raise ValueError("A declared source missing-token list is required")
    path = Path(path)
    columns = ("id", "day", "created_esm", "ended_esm", "interaction", "bored", "type_interaction", "communication")
    guard()
    if path.stat().st_size != pin["bytes"] or sha256(path, guard) != pin["sha256"]:
        raise ValueError("Next-prompt source pin mismatch")
    with pd.read_csv(path, sep="\t", dtype=str, usecols=list(columns), keep_default_na=False,
                     na_filter=False, chunksize=20000) as reader:
        for frame in reader:
            guard()
            yield frame.loc[:, list(columns)].rename(columns={"bored": "occup_bored"})
    guard()
    if path.stat().st_size != pin["bytes"] or sha256(path, guard) != pin["sha256"]:
        raise ValueError("Next-prompt source changed during projection")


def source_projection(member, path, pin, missing_tokens, guard, route, extra=()):
    """Use exact source bytes. Pair cards by the complete sorted literal-ID roster."""
    if not callable(guard):
        raise ValueError("Source guard required")
    if not isinstance(missing_tokens, (list, tuple)) or not missing_tokens or not all(isinstance(v, str) for v in missing_tokens):
        raise ValueError("An explicit reviewed missing-token sequence is required")
    missing_tokens = list(missing_tokens)
    wanted = source.columns(member, route)
    extra = tuple(extra)
    if extra and (route != "LD1" or extra != ("communication", "no_interactionpartner")):
        raise ValueError("Unregistered source projection")
    path = Path(path)
    identities, added = [], {key: [] for key in extra}

    def extended_frames():
        guard()
        if path.stat().st_size != pin["bytes"] or sha256(path, guard) != pin["sha256"]:
            raise ValueError("Source pin mismatch before extended projection")
        aliases = {"occup_" + name: name for name in source.ACTIVITY} if route == "LD3" else {}
        names = [aliases.get(key, key) for key in wanted + extra]
        with pd.read_csv(path, sep="\t", usecols=names, dtype=str, keep_default_na=False,
                         na_filter=False, chunksize=20000) as reader:
            for frame in reader:
                yield frame.rename(columns={literal: key for key, literal in aliases.items()})
        guard()
        if path.stat().st_size != pin["bytes"] or sha256(path, guard) != pin["sha256"]:
            raise ValueError("Source changed during extended projection")

    def frames():
        stream = (extended_frames() if extra or route == "LD3" else
                  source.selected_frames(path, pin, member, route, guard))
        for frame in stream:
            guard()
            identities.extend(frame["id"].tolist())
            for key in extra:
                added[key].extend(frame[key].tolist())
            yield frame.loc[:, list(wanted)]

    people, counts = source.prepare_people(frames(), member, route, missing_tokens, guard)
    index = {key: j for j, key in enumerate(sorted(set(identities) - set(missing_tokens)))}
    ordinals, units = [], []
    values = {}
    for person in people:
        rows = person["source_ordinals"]
        unit = index[identities[rows[0]]]
        if any(index[identities[row]] != unit for row in rows):
            raise ValueError("Source identity changed within person")
        units.extend([unit] * len(rows))
        ordinals.extend(rows)
        for key, observations in person["ratings"].items():
            values.setdefault(key, []).extend(observations)
    invalid = {}
    for key in extra:
        accepted = COMMUNICATION_LABELS if key == "communication" else PARTNER_COUNT_CODES
        values[key] = []
        invalid[key] = 0
        for j, row in enumerate(ordinals):
            value = np.nan
            if values["company"][j] == 1 and added[key][row] not in missing_tokens:
                try:
                    value = float(added[key][row])
                except (ValueError, TypeError):
                    pass
                if value not in accepted:
                    invalid[key] += 1
                    value = np.nan
            values[key].append(value)
    counts["invalid_optional_codes"] = invalid
    counts.update(complete_source_people=len(index))
    return Projection(len(index), np.asarray(units, dtype=np.int64),
                      np.asarray(ordinals, dtype=np.int64),
                      {key: np.asarray(value, float) for key, value in values.items()}, counts)


def multiplicities(count, weights):
    if weights is None:
        return np.ones(count, dtype=float)
    values = np.asarray(weights)
    if (values.shape != (count,) or values.dtype.kind not in "ifu"
            or not np.isfinite(values).all() or np.any(values < 0)
            or np.any(values != np.floor(values)) or values.sum() <= 0):
        raise ValueError("One finite nonnegative whole multiplicity per source person required")
    return values.astype(float, copy=False)


def denominator(units, keep):
    return {"rows": int(np.count_nonzero(keep)),
            "people": int(np.unique(units[keep]).size)}


def metric(prepared, key, label, counts, *, role="table", bar=None, disposition=None):
    if key in prepared.specs:
        raise ValueError("Duplicate metric key")
    spec = dict(label=label, role=role, rows=int(counts["rows"]), people=int(counts["people"]))
    if bar is not None:
        spec["bar"] = bar
        spec["direction"] = "positive"
    if disposition is not None:
        spec["disposition"] = disposition
    prepared.specs[key] = spec


def record_point_dispositions(prepared, estimates, weights):
    if weights is None:
        prepared.metadata["point_dispositions"] = {
            key: prepared.specs[key].get("disposition", "unidentified_full_sample")
            for key, value in estimates.items() if value is None
        }


def reference_within(values, units, weight):
    """Separate group totals and weighted residual second moments for replay."""
    x = np.asarray(values, float)
    if not len(x):
        raise fits.InvalidFit("Empty replay panel")
    x = x.reshape(len(x), -1)
    w = np.asarray(weight, float)
    if not len(x) or w.sum() <= 0:
        raise fits.InvalidFit("Empty weighted panel")
    _, inv = np.unique(units, return_inverse=True)
    totals = np.zeros((int(inv.max()) + 1, x.shape[1]))
    np.add.at(totals, inv, x)
    repeated_means = (totals / np.bincount(inv)[:, None])[inv]
    residual = x - repeated_means
    scale = np.sqrt(np.average(np.square(residual), axis=0, weights=w))
    if not np.isfinite(scale).all() or np.any(scale <= np.finfo(float).eps):
        raise fits.InvalidFit("No within-person variation")
    return residual / scale, repeated_means, scale


def reference_linear(design, outcome, weight):
    w = np.asarray(weight, float)
    keep = w > 0
    if not np.any(keep):
        raise fits.InvalidFit("Empty weighted panel")
    mult = np.sqrt(w[keep])
    matrix = np.asarray(design)[keep] * mult[:, None]
    coefficients, _, rank, _ = lstsq(matrix, outcome[keep] * mult, lapack_driver="gelsy")
    if rank != design.shape[1]:
        raise fits.InvalidFit("Rank-deficient replay design")
    return coefficients


def reference_logit(design, observed, weight):
    """Independent Fisher scoring via a weighted working-response least squares."""
    weight = np.asarray(weight, dtype=float)
    active = weight > 0
    x, y, w = design[active], np.asarray(observed, float)[active], weight[active]
    if not len(x) or np.unique(y).size < 2 or np.linalg.matrix_rank(x) != x.shape[1]:
        raise fits.InvalidFit("One-class or singular replay design")
    coef = np.zeros(x.shape[1])
    for _ in range(100):
        eta = x @ coef
        prob = expit(eta)
        var = prob * (1. - prob)
        root = np.sqrt(var * w)
        matrix = x * root[:, None]
        singular = np.linalg.svd(matrix, compute_uv=False)
        if (singular[-1] <= 0 or singular[0] / singular[-1] > 1e6):
            raise fits.InvalidFit("Separated or singular replay information")
        target = np.divide((y - prob) * w, root, out=np.zeros_like(w), where=root > 0)
        step, _, rank, _ = lstsq(matrix, target, lapack_driver="gelsy")
        score = x.T @ (w * (y - prob))
        if rank != x.shape[1]:
            raise fits.InvalidFit("Singular replay update")
        if np.max(np.abs(step)) <= 1.e-7 and np.max(np.abs(score)) / w.sum() <= 1.e-9:
            return coef
        current = float(w @ (np.logaddexp(0., eta) - y * eta))
        slope = float(score @ step)
        rate = 1.
        for _ in range(40):
            trial = coef + rate * step
            eta_trial = x @ trial
            loss = float(w @ (np.logaddexp(0., eta_trial) - y * eta_trial))
            if loss <= current - 1.e-4 * rate * slope + 1.e-12 * max(1., current):
                coef = trial
                break
            rate *= .5
        else:
            raise fits.InvalidFit("Replay line search failed")
        if not np.isfinite(coef).all() or np.max(np.abs(coef)) > 100:
            raise fits.InvalidFit("Separated replay fit")
    raise fits.InvalidFit("Replay fit did not converge")


def arithmetic(verify):
    if verify:
        return reference_within, reference_logit, reference_linear
    return fits.within, fits.logit_fit, fits.linear_fit


def contrast(left, right):
    return None if left is None or right is None else float(left - right)


def average_difference(values):
    if any(value is None for value in values):
        return None
    return float(np.mean([values[0] - other for other in values[1:]]))
