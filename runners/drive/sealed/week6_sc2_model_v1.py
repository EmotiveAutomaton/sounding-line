"""SC2. Two standardized humor slopes on the same conversations and controls.

DESIGN CHECK (LESSONS 3–5). Matching two identical outcomes implies zero
difference. A common predictor and paired resamples preserve the covariance
of the slopes. Cross-product fits are checked against weighted least squares
on independently reconstructed directed rows. No identifiers leave the job.
"""
import numpy as np

SEED = 202611200044
DRAWS = 2000
BAR = .05
RANK_RCOND = 1e-7
NAMES = ("humor_liking", "humor_status", "liking_minus_status")


def matrix(pairs):
    """Keep each conversation as one block of two reciprocal reports."""
    blocks = []
    seen = set()
    people = set()
    for conversation, pair in pairs:
        if conversation in seen or len(pair) != 2:
            raise ValueError("Invalid or repeated conversation")
        a, b = pair
        if a[0] == b[0] or a[:2] != (b[1], b[0]):
            raise ValueError("Nonreciprocal conversation")
        seen.add(conversation)
        people.update((a[0], b[0]))
        blocks.append([[r[2], r[5], r[6], r[3], r[4]] for r in pair])
    data = np.asarray(blocks, dtype=float).reshape(-1, 2, 5)
    if not np.isfinite(data).all():
        raise ValueError("Nonfinite directed report")
    return data, len(people)


def indexed_weights(n):
    random = np.random.default_rng(SEED)
    yield np.ones(n, dtype=int)
    for _ in range(DRAWS):
        yield np.bincount(random.integers(n, size=n), minlength=n)


def _paired(coefs):
    return np.asarray((coefs[0], coefs[1], coefs[0] - coefs[1]))


def _crossproduct_fit(blocks, minima, maxima, weights):
    gram = np.tensordot(weights, blocks, axes=1)
    cov = gram[1:, 1:] - np.outer(gram[0, 1:], gram[0, 1:]) / gram[0, 0]
    standard = np.sqrt(np.maximum(0., cov.diagonal()))
    selected = weights > 0
    fixed = minima[selected].min(axis=0) == maxima[selected].max(axis=0)
    standard[fixed] = 0.
    coefs = np.full(2, np.nan)
    if np.all(standard[:3] > 0):
        xx = cov[:3, :3] / np.outer(standard[:3], standard[:3])
        values = np.linalg.eigvalsh(xx)
        if values[0] > RANK_RCOND**2 * values[-1]:
            for i in range(2):
                j = i + 3
                if standard[j] > 0:
                    xy = cov[:3, j] / (standard[:3] * standard[j])
                    coefs[i] = np.linalg.solve(xx, xy)[0]
    return _paired(coefs)


def _direct_fit(data, weights):
    chosen = np.repeat(weights, 2) > 0
    w = np.repeat(weights, 2)[chosen]
    rows = data.reshape(-1, 5)[chosen]
    centered = rows - np.average(rows, axis=0, weights=w)
    scaled = centered * np.sqrt(w)[:, None]
    norm = np.sqrt(np.sum(scaled * scaled, axis=0))
    norm[np.ptp(rows, axis=0) == 0.] = 0.
    coefs = np.full(2, np.nan)
    if np.all(norm[:3] > 0):
        x = scaled[:, :3] / norm[:3]
        for i in range(2):
            j = i + 3
            if norm[j] > 0:
                beta, _, rank, _ = np.linalg.lstsq(x, scaled[:, j] / norm[j], rcond=RANK_RCOND)
                if rank == 3:
                    coefs[i] = beta[0]
    return _paired(coefs)


def distribution(data, *, replay=False):
    """The first entry is the observed sample. All other entries are indexed draws."""
    if not len(data):
        return np.full((DRAWS + 1, 3), np.nan)
    if replay:
        return np.asarray([_direct_fit(data, w) for w in indexed_weights(len(data))])
    # A fixed shift reduces roundoff in the sufficient statistics. Each fit
    # subsequently centers and scales all five columns within its own draw.
    shifted = data - data.mean(axis=(0, 1))
    ones = np.ones((*shifted.shape[:2], 1))
    augmented = np.concatenate((ones, shifted), axis=2)
    blocks = np.einsum("cpi,cpj->cij", augmented, augmented)
    minima, maxima = data.min(axis=1), data.max(axis=1)
    return np.asarray([_crossproduct_fit(blocks, minima, maxima, w) for w in indexed_weights(len(data))])


def aggregate(original, replay, n, conversations):
    if original.shape != (DRAWS + 1, 3) or replay.shape != original.shape:
        raise ValueError("Incomplete matched banks")
    if not np.allclose(original, replay, equal_nan=True, rtol=1e-7, atol=1e-8):
        raise ValueError("Matched replay differs")
    rows = []
    for i, metric in enumerate(NAMES):
        point, draws = original[0, i], original[1:, i]
        valid = np.isfinite(draws)
        count = int(valid.sum())
        lower, upper, spread = None, None, None
        if count == DRAWS:
            lower, upper = map(float, np.quantile(draws, (.025, .975)))
            spread = float(draws.std(ddof=1))
        rows.append(dict(n=n, conversations=conversations, metric=metric,
                         estimate=float(point) if np.isfinite(point) else None,
                         lower=lower, upper=upper, bootstrap_sd=spread,
                         valid_draws=count, invalid_draws=DRAWS-count,
                         sufficient_conversations=int(conversations >= 20)))
    return rows
