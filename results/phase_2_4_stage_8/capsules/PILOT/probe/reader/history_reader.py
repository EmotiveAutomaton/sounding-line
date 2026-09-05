"""Process-discontinuity readers inside the capsule (brief §7.3, §16.4, P11-P12).
STDLIB ONLY. Arms:
  HPROC   the maker-model process reader: a two-regime segmentation of the actor-blind
          event log under a parametric process law (geometric edit sizes, Bernoulli
          revisit, Bernoulli revert), each side's parameters fitted by maximum likelihood,
          a complexity penalty for the extra regime, a posterior over the boundary and
          'none'; the change TYPE follows which parameters moved (proposal control moves
          the size and revert statistics; selection control moves revisit and revert)
  HSTYLE  character-trigram divergence between sides (stylometry-only rival)
  HPERS   edit persistence and position rival
  HDIR    the direct model reader: the event log rendered, the boundary asked as a grouped
          letter-likelihood question over the candidate positions and 'none'
  HSTACK  the frozen stacked surface baseline (weights supplied by the task)
  HFINAL  the final-only interface's stylometry (no log; sections' final texts compared)

DESIGN CHECK (2026-09-02)
lessons read: LESSONS §3 (an order-sensitive statistic can see movement: the
  segmentation is order-sensitive by construction; a falsifier's baseline arm is a
  known-answer gate: the stylometry arm must catch a plain style switch, checked by the
  constructor's self-test), §5.
gates: none here. bands: none.
"""

from __future__ import annotations

import math
from collections import Counter

from .client import Client

MIN_SEG = 3


def _fit(evs: list[dict]) -> dict:
    n = max(1, len(evs))
    mean_size = max(1.0, sum(max(1, int(e["size"])) for e in evs) / n)
    revisit = min(max(sum(1 for e in evs if e.get("revisit")) / n, 0.02), 0.98)
    revert = min(max(sum(1 for e in evs if e.get("reverted")) / n, 0.02), 0.98)
    return {"size_mean": mean_size, "revisit": revisit, "revert": revert}


def _ll(evs: list[dict], par: dict) -> float:
    p = 1.0 / par["size_mean"]
    total = 0.0
    for e in evs:
        k = max(1, int(e["size"]))
        total += math.log(p) + (k - 1) * math.log(max(1 - p, 1e-9))
        total += math.log(par["revisit"] if e.get("revisit") else 1 - par["revisit"])
        total += math.log(par["revert"] if e.get("reverted") else 1 - par["revert"])
    return total


def process_posterior(events: list[dict], penalty: float = 3.0) -> dict:
    """Posterior over the boundary and 'none' from per-side maximum-likelihood fits with
    a fixed complexity penalty (three extra parameters) for the two-regime model."""
    n = len(events)
    lls = {}
    types = {}
    for k in range(MIN_SEG, n - MIN_SEG + 1):
        a, b = _fit(events[:k]), _fit(events[k:])
        lls[str(k)] = _ll(events[:k], a) + _ll(events[k:], b) - penalty
        size_move = abs(math.log(a["size_mean"]) - math.log(b["size_mean"]))
        rev_move = abs(a["revisit"] - b["revisit"])
        types[str(k)] = "proposal" if size_move >= rev_move else "selection"
    one = _fit(events)
    lls["none"] = _ll(events, one)
    mx = max(lls.values())
    ex = {k: math.exp(v - mx) for k, v in lls.items()}
    z = sum(ex.values())
    post = {k: v / z for k, v in ex.items()}
    best = max(post, key=post.get)
    return {"boundary": post, "type": {"none": post["none"], "proposal": sum(p for k, p in post.items() if k != "none" and types[k] == "proposal"),
                                       "selection": sum(p for k, p in post.items() if k != "none" and types[k] == "selection")},
            "best": best}


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


def stylometry_posterior(events: list[dict], sharpness: float = 6.0) -> dict:
    n = len(events)
    texts = [e.get("text", "") for e in events]
    scores = {}
    for k in range(MIN_SEG, n - MIN_SEG + 1):
        scores[str(k)] = _js(_char_profile(" ".join(texts[:k])), _char_profile(" ".join(texts[k:])))
    if not scores:
        return {"none": 1.0}
    scores["none"] = sum(scores.values()) / len(scores)
    mx = max(scores.values())
    ex = {k: math.exp(sharpness * (v - mx)) for k, v in scores.items()}
    z = sum(ex.values())
    return {k: v / z for k, v in ex.items()}


def persistence_posterior(events: list[dict], sharpness: float = 4.0) -> dict:
    n = len(events)
    sizes = [float(e.get("size", 0)) for e in events]
    revisit = [1.0 if e.get("revisit") else 0.0 for e in events]
    scores = {}
    for k in range(MIN_SEG, n - MIN_SEG + 1):
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


def final_only_posterior(final: dict, options: list[str]) -> dict:
    """No log: the sections' final texts compared pairwise; the posterior over boundaries
    is flat (no positions exist) and 'none' carries one minus the mean divergence share."""
    secs = list(final)
    if len(secs) < 2:
        return {k: 1.0 / len(options) for k in options}
    divs = [_js(_char_profile(final[a]), _char_profile(final[b])) for i, a in enumerate(secs) for b in secs[i + 1:]]
    d = min(1.0, sum(divs) / len(divs) * 4)
    pos = [k for k in options if k != "none"]
    out = {k: d / max(1, len(pos)) for k in pos}
    out["none"] = 1.0 - d
    return out


def render_log(events: list[dict]) -> str:
    lines = []
    for e in events:
        lines.append(f"{e['i'] + 1:02d} {e['op']} {e['section']}@{e['pos']} size={e['size']}"
                     f"{' revisit' if e.get('revisit') else ''}{' REVERTED' if e.get('reverted') else ''}: {e.get('text', '')[:60]}")
    return "\n".join(lines)


def direct(ev: dict, client: Client, evidence_sha: str) -> dict:
    h = ev["history"]
    options = ev["query"]["boundary_options"]
    if h.get("interface") == "final_only":
        body = "The final document, by section:\n" + "\n".join(f"{s}: {t[:300]}" for s, t in h["final"].items())
    else:
        body = "A revision log (step, operation, place, size, text):\n" + render_log(h["events"])
    words = {k: ("no change in who or what is driving the work" if k == "none" else f"after step {k}") for k in options}
    r = client.likelihood_any(body + "\n\nAt which step does the way the work is being driven change?", words, evidence_sha, "boundary")
    post = r["probs"] if r.get("valid") else {k: 1.0 / len(options) for k in options}
    r2 = client.likelihood(body + "\n\nIf the driving changes, what changes?", {"proposal": "who proposes the edits", "selection": "who selects among proposals", "none": "nothing changes"},
                           evidence_sha, "change_type")
    typ = r2["probs"] if r2.get("valid") else {"proposal": 1 / 3, "selection": 1 / 3, "none": 1 / 3}
    return {"boundary": post, "type": typ}


def stacked(posts: list[dict], weights: list[float]) -> dict:
    keys = set()
    for p in posts:
        keys |= set(p)
    out = {k: sum(w * float(p.get(k, 0.0)) for p, w in zip(posts, weights)) for k in keys}
    z = sum(out.values()) or 1.0
    return {k: v / z for k, v in out.items()}


def run(ev: dict, arm: str, client: Client, evidence_sha: str, task: dict) -> dict:
    h = ev["history"]
    options = ev["query"]["boundary_options"]
    if h.get("interface") == "final_only":
        if arm == "HDIR":
            return direct(ev, client, evidence_sha)
        post = final_only_posterior(h["final"], options)
        return {"boundary": post, "type": {"none": post.get("none", 0.0), "proposal": (1 - post.get("none", 0.0)) / 2, "selection": (1 - post.get("none", 0.0)) / 2}}
    events = h["events"]
    if arm == "HPROC":
        r = process_posterior(events)
        client.solver(len(events))
        return r
    if arm == "HSTYLE":
        post = stylometry_posterior(events)
    elif arm == "HPERS":
        post = persistence_posterior(events)
    elif arm == "HDIR":
        return direct(ev, client, evidence_sha)
    elif arm == "HSTACK":
        w = task.get("stack_weights") or {"style": 0.5, "pers": 0.5}
        post = stacked([stylometry_posterior(events), persistence_posterior(events)], [w.get("style", 0.5), w.get("pers", 0.5)])
    elif arm == "HU":
        post = {k: 1.0 / len(options) for k in options}
    else:
        raise ValueError(arm)
    none = post.get("none", 0.0)
    return {"boundary": post, "type": {"none": none, "proposal": (1 - none) / 2, "selection": (1 - none) / 2}}
