"""The reader-free systems of §8 inside the capsule: U (uniform over the live option set),
PERS (persistence, last event, position), DOM (the frozen common-domain process model,
whose parameters arrive in the capsule as data fitted on a dedicated dom-fit lineage at
the scientific lock, DOM_FROZEN.json copied verbatim), and SOL (the supplied executable
state run through the law: the interface ceiling). STDLIB ONLY.

DESIGN CHECK (2026-09-02)
lessons read: LESSONS §3 (blind floors follow the truth's label marginal: DOM's stop
  base rate and type transitions are fitted, never assumed; the strongest cheap rival is
  the best frozen PERS/DOM combination chosen inside discovery and then fixed), §5.
gates: none here; the engines compare arms. bands: none.
"""

from __future__ import annotations

import json
import os

from . import law as LAW

TYPES = list(LAW.ACTION_TYPES)


def _query(ev: dict) -> dict:
    return ev["query"]


def _induced(next_action: dict, options: list[dict], sections: list[str]) -> tuple[dict, dict]:
    type_d = {t: 0.0 for t in TYPES}
    sec_d = {s: 0.0 for s in sections}
    for a in options:
        p = next_action.get(LAW.action_id(a), 0.0)
        type_d[a["type"]] += p
        sec_d[a["section"]] = sec_d.get(a["section"], 0.0) + p
    return type_d, sec_d


def uniform(ev: dict) -> dict:
    q = _query(ev)
    opts = LAW.options_at_cut(ev)
    ids = q["next_action_options"]
    na = {k: 1.0 / len(ids) for k in ids}
    td, sd = _induced(na, opts, q["sections"])
    return {"next_action": na, "next_type": td, "next_section": sd, "p_stop": 0.5,
            "changed_context": {k: 1.0 / len(ids) for k in ids},
            "invalidation": {k: 1 / 3 for k in q["invalidation_responses"]},
            "boundary_type": {k: 0.25 for k in q["boundary_types"]}}


def persistence(ev: dict) -> dict:
    """Last-event persistence with a position prior: the next type repeats the last with
    0.55, the section stays with 0.55, the stop rate is a flat 0.15."""
    q = _query(ev)
    opts = LAW.options_at_cut(ev)
    prefix = ev.get("process_prefix", [])
    last_t = prefix[-1]["type"] if prefix else None
    last_s = prefix[-1]["section"] if prefix else None
    w = {}
    for a in opts:
        s = 1.0
        if last_t is not None:
            s *= 0.55 if a["type"] == last_t else 0.45 / max(1, len(TYPES) - 1)
        if last_s is not None:
            s *= 0.55 if a["section"] == last_s else 0.45 / max(1, len(q["sections"]) - 1)
        w[LAW.action_id(a)] = s
    z = sum(w.values()) or 1.0
    na = {k: v / z for k, v in w.items()}
    td, sd = _induced(na, opts, q["sections"])
    return {"next_action": na, "next_type": td, "next_section": sd, "p_stop": 0.15,
            "changed_context": dict(na), "invalidation": {"correct": 0.4, "retain": 0.4, "rewrite": 0.2},
            "boundary_type": {"satisfaction": 0.4, "deadline": 0.3, "fatigue": 0.2, "equivalent": 0.1}}


def load_dom(path: str | None = None) -> dict | None:
    p = path or os.path.join(os.getcwd(), "dom.json")
    if not os.path.exists(p):
        return None
    with open(p, encoding="utf-8") as fh:
        return json.load(fh)


def _bucket(progress: float) -> str:
    return "early" if progress < 0.34 else ("mid" if progress < 0.67 else "late")


def dom(ev: dict, params: dict | None = None) -> dict | None:
    """The frozen common-domain model: P(type | last type, progress bucket) with add-one
    smoothing, P(section index | progress bucket), P(stop | progress bucket, over-length),
    and the next action as the product restricted to live options."""
    params = params or load_dom()
    if not params:
        return None
    q = _query(ev)
    opts = LAW.options_at_cut(ev)
    prefix = ev.get("process_prefix", [])
    init = LAW.initial_inventory(ev)
    done = sum(1 for e in prefix if e.get("outcome") != "failed")
    progress = done / max(1, len(init))
    b = _bucket(progress)
    last_t = prefix[-1]["type"] if prefix else "none"
    tt = params["type_trans"].get(f"{b}|{last_t}") or params["type_trans"].get(f"{b}|none") or {}
    type_p = {t: float(tt.get(t, 0.0)) + 1e-3 for t in TYPES}
    z = sum(type_p.values())
    type_p = {t: v / z for t, v in type_p.items()}
    n_sec = len(q["sections"])
    sp = params["section_pos"].get(b) or {}
    sec_p = {}
    for i, s in enumerate(q["sections"]):
        key = str(min(i, 3))
        sec_p[s] = float(sp.get(key, 1.0 / n_sec)) + 1e-3
    z = sum(sec_p.values())
    sec_p = {s: v / z for s, v in sec_p.items()}
    w = {LAW.action_id(a): type_p[a["type"]] * sec_p.get(a["section"], 1e-3) for a in opts}
    z = sum(w.values()) or 1.0
    na = {k: v / z for k, v in w.items()}
    td, sd = _induced(na, opts, q["sections"])
    over = "over" if len(prefix) > float(params.get("mean_len", 12.0)) else "under"
    p_stop = float(params["stop"].get(f"{b}|{over}", params["stop"].get("all", 0.15)))
    cc = params.get("changed_context") or {}
    inval = params.get("invalidation") or {"correct": 1 / 3, "retain": 1 / 3, "rewrite": 1 / 3}
    bt = params.get("boundary") or {k: 0.25 for k in q["boundary_types"]}
    return {"next_action": na, "next_type": td, "next_section": sd, "p_stop": p_stop,
            "changed_context": dict(na) if not cc else {k: na.get(k, 0.0) for k in na},
            "invalidation": dict(inval), "boundary_type": dict(bt)}


def solver(ev: dict) -> dict | None:
    """SOL: the supplied executable state run through the law. None when the state is
    incomplete (a withheld factor cannot be re-derived: LawError)."""
    sf = (ev.get("supplied_factors") or {})
    if sf.get("form") != "executable":
        return None
    st = dict(sf.get("factors") or {})
    try:
        ex = LAW.execute(st, ev)
    except LAW.LawError:
        return None
    q = _query(ev)
    bt = {k: 0.0 for k in q["boundary_types"]}
    bt[ex["boundary_type"] if ex["boundary_type"] in bt else "equivalent"] = 1.0
    cc = None
    if q.get("context_change"):
        try:
            cc = LAW.execute_changed(st, ev, q["context_change"])["next_action"]
        except LAW.LawError:
            cc = None
    return {"next_action": ex["next_action"], "next_type": ex["next_type"], "next_section": ex["next_section"],
            "p_stop": ex["p_stop"], "changed_context": cc, "invalidation": ex.get("invalidation"), "boundary_type": bt,
            "subjective_ids": ex["subjective_ids"]}
