"""LD4 anchored word profiles from registered Form L tables.

DESIGN CHECK (LESSONS 2–5). In a planted shared recipe the two contexts agree.
Different recipes can separate despite similar outcome scales. A repeated or
weak anchor fails the context check. The gate excludes all identity-anchor rows
from the correlation and leaves unavailable dimensions explicit in both samples.
"""
import numpy as np
from scipy import linalg

from .week6_lattice_source_v1 import feeling_names


ANCHORS = ("angry", "anxious", "lonely", "ashamed", "enthusiastic")
CONTEXTS = ("interaction", "solitary")


def anchors_and_others(member):
    words = feeling_names(member)
    return (tuple(w for w in ANCHORS if w in words),
            tuple(w for w in words if w not in ANCHORS))


def spectrum(table):
    if not np.isfinite(table).all():
        return None
    return np.linalg.svd(table, compute_uv=False)


def fit_recipe(table, member, *, reference=False):
    words = feeling_names(member)
    anchors, mixed = anchors_and_others(member)
    if table.ndim != 2 or table.shape[0] != len(words):
        raise ValueError("Word-by-feature table does not match the approved member")
    basis = table[[words.index(w) for w in anchors]].T
    sv = spectrum(basis)
    if sv is None or len(sv) < len(anchors) or sv[-1] <= np.finfo(float).eps * max(basis.shape) * sv[0]:
        return None, None
    condition = float(sv[0] / sv[-1])
    weights = np.full((len(mixed), len(anchors)), np.nan)
    for i, name in enumerate(mixed):
        slopes = table[words.index(name)]
        if not np.isfinite(slopes).all():
            continue
        if reference:
            solution, _, rank, _ = linalg.lstsq(basis, slopes, lapack_driver="gelsy")
        else:
            solution, _, rank, _ = np.linalg.lstsq(basis, slopes, rcond=None)
        if rank == len(anchors):
            weights[i] = solution
    return condition, weights


def agreement(left, right, reference=False):
    if left is None or right is None or left.shape != right.shape:
        return None
    a, b = left.ravel(), right.ravel()
    if not np.isfinite(a).all() or not np.isfinite(b).all():
        return None
    a, b = a-a.mean(), b-b.mean()
    denominator = np.linalg.norm(a)*np.linalg.norm(b)
    if denominator <= np.finfo(float).eps:
        return None
    return float(np.corrcoef(left.ravel(), right.ravel())[0, 1] if reference else (a @ b)/denominator)


def sanity(weights, member):
    anchors, mixed = anchors_and_others(member)
    def contrast(name, first, rival=None):
        row = weights[mixed.index(name)]
        if not np.isfinite(row).all():
            return None
        j = anchors.index(first)
        other = row[anchors.index(rival)] if rival else np.max(np.delete(row, j))
        return float(row[j] - other)
    result = {"resentful_angry_above_others": contrast("resentful", "angry"),
              "insecure_anxious_above_angry": contrast("insecure", "anxious", "angry"),
              "insecure_ashamed_above_angry": contrast("insecure", "ashamed", "angry")}
    if "excluded" in mixed:
        result["excluded_lonely_above_others"] = contrast("excluded", "lonely")
    return result


def summarize(result, draw_rows, keys):
    """Apply the registered boundaries to the original point and complete bank."""
    if len(draw_rows) != 2000:
        raise ValueError("Every registered draw is required")
    metrics = result["metrics"]
    summaries = {}
    for context in CONTEXTS:
        noise_key = context+"/noise"
        noise = [row[keys.index(noise_key)] for row in draw_rows]
        limit = None if None in noise else float(np.quantile(noise, .95))
        singular = [v["estimate"] for k,v in metrics.items() if k.startswith(context+"/singular/")]
        condition = metrics[context+"/condition"]["estimate"]
        flags = [row[keys.index(context+"/condition")] for row in draw_rows]
        summaries[context] = dict(observed_condition=condition, readable=condition is not None and condition<15,
                                  draws_at_or_above_15_or_singular=sum(x is None or x>=15 for x in flags),
                                  singular_values=singular, spectral_noise_95=limit,
                                  directions=None if limit is None or None in singular else sum(v>limit for v in singular))
    result["context_checks"] = summaries
    row = metrics["cross_context"]
    if result["member"] == "0056":
        decision = "descriptive four-anchor sample"
    elif not all(v["readable"] for v in summaries.values()):
        decision = "unreadable anchor system"
    elif row["estimate"] is None or row["interval"] is None:
        decision = "could not identify agreement"
    elif row["estimate"] >= .6 and row["interval"][0] > .3:
        decision = "meets the registered agreement bar"
    else:
        decision = "does not meet the registered agreement bar"
    result["registered_reading"] = decision
    return result
