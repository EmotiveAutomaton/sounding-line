"""Further capsule arms (brief K16, V02, V04-V06). STDLIB ONLY.
  GBLIND   the goal-blind mixture: the four goal utility tables mixed uniformly through
           the solver with the supplied other factors (V02's matched rival)
  DIRS     the direct reader with structured computation: the solver's execution of the
           supplied state is appended to the evidence text (K16's structured cell)
  POINT    forced point dating: the present law is the law fitted on the most recent dated
           demonstration alone (V04's penalized rival)
  MIX      the dated mixture: a law fitted per dated demonstration, weighted by a recency
           kernel over the dates; the present law posterior is that mixture (V04)
  AGG      one law fitted on all demonstrations pooled (V05/V06's aggregate profile)
  ORDERED  recency by order only (dates hidden): weights by rank (V05)
  DATED    recency by date gaps: weights exp(-age/tau) (V05/V06)

DESIGN CHECK (2026-09-02)
lessons read: LESSONS §3 (the per-item best of several comparators is an oracle over
  comparators: each history view is one arm, never a per-item max; a matched-cost
  comparator is read beside the plain route: AGG is the plain route for DATED).
gates: none here. bands: none.
"""

from __future__ import annotations

import math

from . import baselines as B
from . import joint_reader as J
from . import law as LAW
from .client import Client
from .supplied_state import direct, evidence_text

TYPES = list(LAW.ACTION_TYPES)
TAU_DAYS = 90.0


def _supplied(ev: dict) -> dict:
    sf = ev.get("supplied_factors") or {}
    if sf.get("form") != "executable":
        return {}
    return dict(sf.get("factors") or {})


def _execute_with(ev: dict, st: dict) -> dict | None:
    s = dict(st)
    s.pop("maker_context", None) if "maker_context" not in st else None
    try:
        ex = LAW.execute(s, ev)
        kind = ev["query"].get("context_change")
        cc = LAW.execute_changed(s, ev, kind)["next_action"] if kind else None
    except LAW.LawError:
        return None
    return {"next_action": ex["next_action"], "next_type": ex["next_type"], "next_section": ex["next_section"], "p_stop": ex["p_stop"],
            "changed_context": cc, "invalidation": ex.get("invalidation")}


def goal_blind(ev: dict, client: Client) -> dict | None:
    st = _supplied(ev)
    if "expertise_law" not in st or "belief_state" not in st or "external_context" not in st:
        return None
    na: dict = {}
    cc: dict = {}
    inv: dict = {}
    p_stop = 0.0
    n = 0
    for g in LAW.GOALS:
        s = dict(st, proximal_goal={"utility": dict(LAW.GOAL_UTILITY[g]), "owner": g})
        s.pop("subjective_action_space", None)
        ex = _execute_with(ev, s)
        client.solver(1)
        if ex is None:
            continue
        n += 1
        for k, p in ex["next_action"].items():
            na[k] = na.get(k, 0.0) + p
        for k, p in (ex.get("changed_context") or {}).items():
            cc[k] = cc.get(k, 0.0) + p
        for k, p in (ex.get("invalidation") or {}).items():
            inv[k] = inv.get(k, 0.0) + p
        p_stop += ex["p_stop"]
    if not n:
        return None
    na = {k: v / n for k, v in na.items()}
    cc = {k: v / n for k, v in cc.items()} or None
    inv = {k: v / n for k, v in inv.items()} or None
    opts = LAW.options_at_cut(ev)
    td = {t: 0.0 for t in TYPES}
    sd = {s: 0.0 for s in ev["query"]["sections"]}
    for a in opts:
        td[a["type"]] += na.get(LAW.action_id(a), 0.0)
        sd[a["section"]] += na.get(LAW.action_id(a), 0.0)
    return {"next_action": na, "next_type": td, "next_section": sd, "p_stop": p_stop / n, "changed_context": cc, "invalidation": inv}


def direct_structured(ev: dict, client: Client, evidence_sha: str, targets=None) -> dict:
    """DIR plus the solver's execution of the supplied state written into the evidence."""
    sol = B.solver(ev)
    if sol is None:
        return direct(ev, client, evidence_sha, targets)
    top = sorted(sol["next_action"].items(), key=lambda kv: -kv[1])[:3]
    line = ("\n\nA calculation from the given state predicts the next move: " +
            ", ".join(f"{k} ({p:.2f})" for k, p in top) + f"; chance of stopping at the next pause {sol['p_stop']:.2f}.")
    ev2 = dict(ev)
    ev2["artifact_state"] = dict(ev["artifact_state"], prefix_text=ev["artifact_state"].get("prefix_text", "") + line)
    return direct(ev2, client, evidence_sha, targets)


# ── dated histories (V04-V06) ────────────────────────────────────────────────────────

def _fit_on(demos: list[dict], client: Client) -> dict:
    fake = dict(demonstrations=demos)
    fit = J.fit_law_from_demos(fake, client)
    return fit["law"] if fit else None


def _weights(demos: list[dict], view: str) -> list[float]:
    n = len(demos)
    if view == "aggregate":
        return [1.0 / n] * n
    if view == "ordered":
        w = [math.exp(-(n - 1 - i) / 2.0) for i in range(n)]
    else:
        ages = [float(d.get("age_days", n - 1 - i)) for i, d in enumerate(demos)]
        w = [math.exp(-a / TAU_DAYS) for a in ages]
    z = sum(w)
    return [x / z for x in w]


def dated(ev: dict, client: Client, view: str) -> dict | None:
    """AGG / ORDERED / DATED / MIX / POINT: the present law from the demonstrations under
    one history view, executed with the supplied other factors."""
    demos = ev.get("demonstrations") or []
    if not demos:
        return None
    st = _supplied(ev)
    if view == "point":
        law = _fit_on([demos[-1]], client)
        mix = None
    elif view == "aggregate":
        law = _fit_on(demos, client)
        mix = None
    else:
        laws = [_fit_on([d], client) for d in demos]
        w = _weights(demos, "ordered" if view == "ordered" else "dated")
        law = {"skill": {}, "feasible_min_skill": laws[0]["feasible_min_skill"], "cost": {}, "chain": {},
               "fluency": sum(wi * L["fluency"] for wi, L in zip(w, laws)), "expected_len": 12.0, "confidence": 0.5}
        for t in TYPES:
            law["skill"][t] = sum(wi * L["skill"][t] for wi, L in zip(w, laws))
            law["cost"][t] = sum(wi * L["cost"][t] for wi, L in zip(w, laws))
        mix = {d.get("episode_ref", str(i)): wi for i, (d, wi) in enumerate(zip(demos, w))}
    if law is None:
        return None
    s = dict(st, expertise_law=law)
    s.pop("subjective_action_space", None)
    ex = _execute_with(ev, s)
    if ex is None:
        return None
    ex["fitted_law"] = law
    ex["mixture"] = mix
    return ex
