"""Process-discontinuity scoring (brief §7.3, §16.4, P11-P12, B03): the full posterior
over boundary locations (event indices plus 'none') scored by log mass on the true
location, the expected absolute boundary error, tolerance accuracy, and the surface
rivals the maker-model reader must beat: character/token stylometry divergence, edit
persistence and position, a direct change-point prompt (the model arm, run in a
capsule), and the strongest stacked surface baseline frozen in discovery.

DESIGN CHECK (2026-09-02)
lessons read: LESSONS §3 (a representation-space separation claim needs the cheap
  scalars in its surface control; a transformer used as an eraser has an echo gate:
  style normalization is measured per history, and un-normalized histories are
  excluded from the survival claim; a falsifier's baseline arm is a known-answer gate:
  the stylometry rival must catch the style-switch adversary), §5.
gates: none here; the P engine states the bands. bands: none.
"""

from __future__ import annotations

import math
from collections import Counter

FLOOR = 1e-9


def changepoint_ls(post: dict, truth) -> float:
    return math.log(max(float(post.get(str(truth), 0.0)), FLOOR))


def expected_abs_error(post: dict, truth, n_events: int) -> float | None:
    if str(truth) == "none":
        return None
    t = int(truth)
    return sum(float(p) * (n_events if k == "none" else abs(int(k) - t)) for k, p in post.items())


def tolerance_hit(post: dict, truth, tol: int = 2) -> bool | None:
    if str(truth) == "none":
        return max(post, key=post.get) == "none"
    best = max(post, key=post.get)
    if best == "none":
        return False
    return abs(int(best) - int(truth)) <= tol


def _char_profile(text: str, n: int = 3) -> Counter:
    t = text.lower()
    return Counter(t[i:i + n] for i in range(max(0, len(t) - n + 1)))


def _js(a: Counter, b: Counter) -> float:
    keys = set(a) | set(b)
    za, zb = sum(a.values()) or 1, sum(b.values()) or 1
    m = {k: 0.5 * (a.get(k, 0) / za + b.get(k, 0) / zb) for k in keys}

    def kl(p, z):
        return sum((p.get(k, 0) / z) * math.log((p.get(k, 0) / z) / m[k]) for k in keys if p.get(k, 0) > 0)
    return 0.5 * kl(a, za) + 0.5 * kl(b, zb)


def stylometry_posterior(events: list[dict], min_seg: int = 3, sharpness: float = 6.0) -> dict:
    """Character-trigram divergence between the two sides of every candidate boundary,
    softmaxed with a 'none' option whose score is the mean divergence (a flat profile
    reads as no boundary)."""
    n = len(events)
    texts = [e.get("text", "") for e in events]
    scores = {}
    for k in range(min_seg, n - min_seg + 1):
        a = _char_profile(" ".join(texts[:k]))
        b = _char_profile(" ".join(texts[k:]))
        scores[str(k)] = _js(a, b)
    if not scores:
        return {"none": 1.0}
    mean = sum(scores.values()) / len(scores)
    scores["none"] = mean
    mx = max(scores.values())
    ex = {k: math.exp(sharpness * (v - mx)) for k, v in scores.items()}
    z = sum(ex.values())
    return {k: v / z for k, v in ex.items()}


def persistence_posterior(events: list[dict], min_seg: int = 3, sharpness: float = 4.0) -> dict:
    """Edit persistence and position: a boundary where the edit-size and revisit pattern
    changes most (the process-shaped cheap rival)."""
    n = len(events)
    sizes = [float(e.get("size", 0)) for e in events]
    revisit = [1.0 if e.get("revisit") else 0.0 for e in events]
    scores = {}
    for k in range(min_seg, n - min_seg + 1):
        d = abs(sum(sizes[:k]) / k - sum(sizes[k:]) / (n - k)) / (max(sizes) or 1.0)
        d += abs(sum(revisit[:k]) / k - sum(revisit[k:]) / (n - k))
        scores[str(k)] = d
    if not scores:
        return {"none": 1.0}
    scores["none"] = sum(scores.values()) / len(scores)
    mx = max(scores.values())
    ex = {k: math.exp(sharpness * (v - mx)) for k, v in scores.items()}
    z = sum(ex.values())
    return {k: v / z for k, v in ex.items()}


def stack(posts: list[dict], weights: list[float]) -> dict:
    keys = set()
    for p in posts:
        keys |= set(p)
    out = {k: sum(w * float(p.get(k, 0.0)) for p, w in zip(posts, weights)) for k in keys}
    z = sum(out.values()) or 1.0
    return {k: v / z for k, v in out.items()}
