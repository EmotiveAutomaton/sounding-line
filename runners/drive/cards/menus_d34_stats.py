"""D34's residual-direction statistic and exhaustive descriptive verdicts.

DESIGN CHECK: LESSONS 3-5, 17 October. Independent residuals have no persistent
direction beyond the within-session/decile permutation reference. A stable
omitted content slope makes session directions agree and predicts held-out
residual signs. Center residuals and features BEFORE multiplying; centering the
products would force their mean to zero. Zero-length directions contribute zero
alignment (no directional evidence), are counted, and cannot support transfer.
Hidden goal requires positive content, positive paired content-minus-each-rival
intervals, and positive last-session balanced sign accuracy above .5. Variant
only positives are state/misfit. Null with >=4/5 planted detections is noise at
this power. Everything else is undetermined; invalid support is never null.
"""
from __future__ import annotations

import math
import numpy as np
from . import states_v2 as states


def unit(values):
    values = np.asarray(values, float)
    lengths = np.linalg.norm(values, axis=-1, keepdims=True)
    return np.divide(values, lengths, out=np.zeros_like(values), where=lengths > 1e-12)


def pair_cosine(vectors):
    """Mean all unordered cross-session cosines; zero vectors contribute zero."""
    normalized = unit(vectors); n = normalized.shape[-2]
    if n < 2:
        raise ValueError("two sessions required")
    return ((normalized.sum(axis=-2) ** 2).sum(axis=-1) - (normalized ** 2).sum(axis=(-1, -2))) / (n * (n - 1))


def writer_statistic(residuals, probabilities, session_ids, session_times, features, permutations=1000, seed=20261017):
    residuals = np.asarray(residuals, float); probabilities = np.asarray(probabilities, float)
    names = np.asarray(session_ids); times = np.asarray(session_times, float)
    if (residuals.ndim != 1 or probabilities.shape != residuals.shape or names.shape != residuals.shape
            or not np.isfinite(residuals).all() or not np.isfinite(probabilities).all()
            or np.any((probabilities < 0) | (probabilities > 1))):
        raise ValueError("invalid D34 residual/probability support")
    ordered = sorted(set(names.tolist()), key=lambda s: (float(times[names == s].min()), s))
    if len(ordered) < 2:
        raise ValueError("fewer than two sessions")
    rng = np.random.default_rng(seed); draws = np.tile(residuals, (permutations + 1, 1))
    deciles = np.minimum(9, np.searchsorted(np.asarray([0., .1, .2, .3, .4, .5, .6, .7, .8, .9, 1.]), probabilities, side="right") - 1)
    movable = 0
    for session in ordered:
        mask = names == session
        draws[:, mask] -= draws[:, mask].mean(axis=1, keepdims=True)
        for decile in range(10):
            indices = np.flatnonzero(mask & (deciles == decile))
            if len(indices) > 1 and np.ptp(residuals[indices]) > 0:
                movable += len(indices)
                for draw in range(1, permutations + 1):
                    draws[draw, indices] = rng.permutation(draws[0, indices])
    result = dict(sessions=len(ordered), decisions=len(residuals), movable_residuals=movable, arms={})
    for arm, values in features.items():
        values = np.asarray(values, float)
        if values.ndim != 2 or len(values) != len(residuals) or not np.isfinite(values).all():
            raise ValueError("invalid D34 feature matrix")
        vectors = []
        for session in ordered:
            mask = names == session; centered = values[mask] - values[mask].mean(axis=0)
            vectors.append(draws[:, mask] @ centered / mask.sum())
        vectors = np.stack(vectors, axis=1); scores = pair_cosine(vectors)
        saved = dict(observed=float(scores[0]), null=scores[1:].tolist(),
                     session_vectors=vectors[0].tolist(), zero_vectors=int(np.sum(np.linalg.norm(vectors[0], axis=1) <= 1e-12)))
        if arm == "content":
            direction = vectors[0, :-1].mean(axis=0)
            last = names == ordered[-1]; z = values[last] - values[last].mean(axis=0)
            truth = np.sign(residuals[last]); forecast = np.sign(z @ direction)
            supported = bool(np.linalg.norm(direction) > 1e-12 and np.any(truth > 0) and np.any(truth < 0))
            accuracy = float(.5 * ((forecast[truth > 0] == 1).mean() + (forecast[truth < 0] == -1).mean())) if supported else None
            saved["last_session"] = dict(session=ordered[-1], balanced_accuracy=accuracy,
                margin=None if accuracy is None else accuracy - .5, direction=direction.tolist(),
                residual_signs=truth.tolist(), predicted_signs=forecast.tolist(),
                source_sessions=ordered[:-1], method="earlier session directions only; balanced sign accuracy; ties count incorrect")
        result["arms"][arm] = saved
    return result


def interval(values, seed=20261017, bootstrap=2000):
    values = np.asarray(values, float)
    if len(values) < 2 or not np.isfinite(values).all():
        return dict(state="invalid", estimate=None, interval95=None, reason="fewer than two finite writer units")
    rng = np.random.default_rng(seed)
    draws = values[rng.integers(len(values), size=(bootstrap, len(values)))].mean(axis=1)
    effect = float(values.mean()); bounds = np.quantile(draws, [.025, .975]).tolist()
    se = float(np.std(draws, ddof=1)); p = math.erfc(abs(effect / se) / math.sqrt(2)) if se > 0 else 1. if effect == 0 else None
    return dict(state=states.classify(effect, *bounds), estimate=effect, interval95=bounds,
                standard_error=se, p_value_approx=p, p_value_method="two-sided Wald approximation; descriptive",
                writers=len(values), direction="positive")


def summarize(metrics, config):
    names = sorted(metrics)
    if len(names) < 2 or not any(metrics[name]["movable_residuals"] for name in names):
        return dict(state="invalid", primary=dict(state="invalid", estimate=None, interval95=None),
                    reason="fewer than two writers or no movable residuals")
    if all(metrics[name]["arms"]["content"]["zero_vectors"] == metrics[name]["sessions"] for name in names):
        return dict(state="invalid", primary=dict(state="invalid", estimate=None, interval95=None), reason="no nonzero content directions")
    arm_names = sorted(set.intersection(*(set(metrics[name]["arms"]) for name in names)))
    arms = {}; effects = {}
    for arm in arm_names:
        observed = np.asarray([metrics[name]["arms"][arm]["observed"] for name in names])
        null = np.asarray([metrics[name]["arms"][arm]["null"] for name in names])
        effects[arm] = observed - null.mean(axis=1)
        arms[arm] = interval(effects[arm], config.get("seed", 20261017), config.get("bootstrap", 2000))
        arms[arm].update(observed=float(observed.mean()), null_mean=float(null.mean()),
            permutation_p=float((1 + np.sum(null.mean(axis=0) >= observed.mean())) / (null.shape[1] + 1)),
            permutations=null.shape[1], zero_session_vectors=sum(metrics[name]["arms"][arm]["zero_vectors"] for name in names))
    contrasts = {arm: interval(effects["content"] - effects[arm], config.get("seed", 20261017), config.get("bootstrap", 2000))
                 for arm in arm_names if arm != "content"}
    margins = [metrics[name]["arms"]["content"]["last_session"]["margin"] for name in names
               if metrics[name]["arms"]["content"]["last_session"]["margin"] is not None]
    transfer = interval(margins, config.get("seed", 20261017), config.get("bootstrap", 2000))
    transfer.update(excluded_writers=len(names) - len(margins), chance=.5)
    return dict(state=arms["content"]["state"], primary=arms["content"], variants=arms,
                content_minus_variants=contrasts, last_session_transfer=transfer, writers=len(names))


def verdict(summary, control_detections):
    if summary["state"] == "invalid":
        return "UNDETERMINED"
    contrasts = summary["content_minus_variants"]
    if (summary["state"] == "positive" and set(contrasts) == {"state", "reader"}
            and all(value["state"] == "positive" for value in contrasts.values())
            and summary["last_session_transfer"]["state"] == "positive"):
        return "HIDDEN GOAL"
    if summary["state"] != "positive" and any(value["state"] == "positive" for name, value in summary["variants"].items() if name != "content"):
        return "STATE OR MISFIT"
    if summary["state"] == "null" and control_detections >= 4:
        return "NOISE AT THIS POWER"
    return "UNDETERMINED"
