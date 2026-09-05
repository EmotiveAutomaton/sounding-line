"""The population corpus (brief §5 POP): process logs sampled from the population prior over
laws, goals (the four Stage 7 goals and the four purposes, uniform), beliefs, residues,
tendencies, shapes, and domains, with the maker-specific factors integrated out by sampling,
rendered in the one log grammar. It is the training material for the forward-model readers,
the fitting material for DOM, and it is lineage-tagged (bands 70000 and 80000, discovery
lane) so the split attack can prove no test lineage descends from it. Half the training
examples carry the goal line (the conditioned form the purpose arm uses); two in five carry
one to three earlier artifacts by the same FRESHLY SAMPLED maker (the accumulation format;
every maker is a new draw, so nothing maker-specific is trained in).

Also here: the exact standard process (the population-marginal likelihood of a log under the
uniform prior over the factor grid), the per-event oracle-minus-DOM gaps along whole
trajectories (the tail threshold tau, the 80th percentile per family, written before any
reader runs), and the visible evidence at an arbitrary cut (per-event scoring).

DESIGN CHECK (2026-09-04)
lessons read: LESSONS §1d (benchmark hygiene: training and test lineages in disjoint index
  bands and lanes, checked by hash in I07), §3 (blind floors follow the truth marginal: the
  tail threshold is a quantile of the population's own gap distribution, declared before
  reader outcomes; a per-token mean is not an ease ruler: the generation gate compares
  per-event mean log-likelihoods of same-kind objects and reports the total beside it),
  §5.
gates: the tail threshold: NULL is a family whose 80th-percentile gap is under
  MIN_GAP_NATS in probability terms (no maker's share to localize; fails DOWN: D cells on
  that family are VOID); ALTERNATIVE: a threshold above it. bands: exhaustive.
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO))

from runners.stage7.constructor import worlds as W                                 # noqa: E402
from runners.stage7.reader import baselines as B                                   # noqa: E402
from runners.stage7.reader import law as LAW                                       # noqa: E402
from runners.stage8.constructor.gradient import SHAPES, make_world_ext             # noqa: E402
from runners.stage8.constructor.purpose import PURPOSES, register, required_sections  # noqa: E402
from runners.stage8.reader import logfmt as LF                                     # noqa: E402
from soundingline.stage7 import EVIDENCE_VERSION                                   # noqa: E402

TRAIN_BAND = 70000
HELDOUT_BAND = 80000
GOAL_SPACE = tuple(W.GOALS) + tuple(PURPOSES)
DOMAINS = ("essay", "workshop_doc")


def pop_lid(i: int, domain: str, band: int = TRAIN_BAND) -> str:
    return f"POP|{domain}|s0|w{band + i:05d}|discovery"


def sample_world(lid: str, finish: bool = False, salt: str = "traj") -> dict:
    register()
    r = W._rng(lid, "pop")
    goal = GOAL_SPACE[r.randrange(len(GOAL_SPACE))]
    shape = SHAPES[r.randrange(len(SHAPES))]
    domain = next(p for p in lid.split("|") if p in DOMAINS)
    forced = None
    owner = None
    if goal in PURPOSES:
        owner = goal
        from runners.stage8.constructor.gradient import doc_plan                   # noqa: PLC0415
        forced = {"brief_sections": required_sections(doc_plan(lid, domain, shape), goal)}
    w = make_world_ext(lid, domain, shape, goal=goal, forced_cext=forced, owner_all=owner, finish=finish, salt=salt)
    w["goal_name"] = goal
    return w


def world_log(w: dict, with_goal: bool) -> str:
    c = w["state"]["external_context"]
    head = LF.header(w["doc"]["topic"], c["audience"], c["tools"], c["deadline"], w["doc"]["sections"],
                     goal=w["goal_name"] if with_goal else None)
    steps = [{"i": s["i"], "type": s["type"], "section": s["section"], "slot": s["slot"], "outcome": s["outcome"]} for s in w["trajectory"]["steps"]]
    return LF.render_log(head, steps, w["trajectory"].get("stop_kind") == "hazard")


def training_example(i: int, domain: str, band: int = TRAIN_BAND) -> dict:
    """One rendered example with its lineage tags: the log alone (goal line on half), or
    one to three earlier logs by the same sampled maker then the current log."""
    lid = pop_lid(i, domain, band)
    w = sample_world(lid)
    r = W._rng(lid, "render")
    with_goal = r.random() < 0.5
    earlier = []
    lids = [lid]
    if r.random() < 0.4:
        names = w["state"]["names"]
        n_prev = 1 + r.randrange(3)
        for k in range(n_prev):
            plid = f"{lid}|prev{k}"
            rk = W._rng(plid, "pop")
            g = GOAL_SPACE[rk.randrange(len(GOAL_SPACE))]
            shape = SHAPES[rk.randrange(len(SHAPES))]
            forced = None
            owner = g if g in PURPOSES else None
            if owner:
                from runners.stage8.constructor.gradient import doc_plan           # noqa: PLC0415
                forced = {"brief_sections": required_sections(doc_plan(plid, domain, shape), g)}
            pw = make_world_ext(plid, domain, shape, goal=g, law_name=names["law"], residue=names["residue"],
                                tendency=names["tendency"], forced_cext=forced, owner_all=owner, finish=False, salt="prev")
            pw["goal_name"] = g
            earlier.append(world_log(pw, False))
            lids.append(plid)
    log = world_log(w, with_goal)
    if earlier:
        text = "\n".join([LF.EARLIER] + earlier + [LF.NOW, log])
    else:
        text = log
    return {"lid": lid, "lineages": lids, "text": text, "goal": w["goal_name"], "with_goal": with_goal,
            "n_earlier": len(earlier), "shape": w["shape"], "domain": domain, "n_events": len(w["trajectory"]["steps"]),
            "names": dict(w["state"]["names"])}


def corpus(n_per_domain: int, band: int = TRAIN_BAND) -> list[dict]:
    out = []
    for d in DOMAINS:
        for i in range(n_per_domain):
            out.append(training_example(i, d, band))
    return out


# ── the exact standard process: the population-marginal likelihood of a log ─────────

def _grid_states(w: dict, inv: list[dict] | None = None):
    inv = inv if inv is not None else w["inventory"]
    tend = w["state"]["names"]["tendency"]
    for g in GOAL_SPACE:
        inv_g = [dict(a, goal_owner=g) for a in inv] if g in PURPOSES else inv
        forced = {"brief_sections": w["state"]["external_context"]["brief_sections"]}
        for ln in W.LAW_NAMES:
            for b in W.BELIEFS:
                for h in W.RESIDUES:
                    yield g, W.make_state(w["lid"], w["doc"], inv_g, g, ln, b, h, tend, forced), inv_g


def marginal_log_likelihood(w: dict, events: list[dict] | None = None, extend: bool = False) -> dict:
    """log P_pop(log | document, context) under the uniform prior over the grid (goal in
    eight, law, belief, residue; the world's tendency), for the world's own trajectory or a
    supplied event list; total and per-event mean."""
    register()
    sections = [s["name"] for s in w["doc"]["sections"]]
    if events is None:
        traj = w["trajectory"]
    else:
        traj = {"steps": [{"i": k, "type": e["type"], "section": e["section"], "slot": e["slot"], "outcome": e.get("outcome", "done")} for k, e in enumerate(events)],
                "changes": w["trajectory"].get("changes"), "change_step": w["trajectory"].get("change_step")}
    n = len(traj["steps"])
    if n == 0:
        return {"total": None, "per_event": None, "n_events": 0}
    lls = []
    inv = extended_inventory(w, events) if (extend and events is not None) else None
    for g, st, inv_g in _grid_states(w, inv):
        lls.append(W._prefix_ll(st, traj, n, inv_g, sections))
    mx = max(lls)
    total = mx + math.log(sum(math.exp(v - mx) for v in lls) / len(lls))
    return {"total": total, "per_event": total / n, "n_events": n}


TYPE_REQUIRES = {"consult": ["source_access"], "cite": ["library"]}
TYPE_OWNER = {"write": "produce", "probe": "produce", "revise": "tighten", "restructure": "tighten", "check": "audit",
              "consult": "audit", "fix": "audit", "cite": "attribute"}


def feasible_visible(w: dict, events: list[dict]) -> dict:
    """The generation gate's feasibility against what the header shows: the section exists and
    the slot is within its count (or the type's fixed slot: src, ref, order, tech); a slot is
    written at most once and revised, checked, or fixed only once it exists; the outcome agrees
    with the header's tools (cite needs the library, consult needs source access, under the
    world's own schedule). Events off the hidden inventory but legal under this rule are
    feasible; the exact process scores them under the extended inventory."""
    secs = {s["name"]: list(s["slots"]) for s in w["doc"]["sections"]}
    fixed = {"consult": "src", "cite": "ref", "restructure": "order", "probe": "tech"}
    c_ext = dict(w["state"]["external_context"])
    changes = [tuple(c) for c in (w["trajectory"].get("changes") or [])]
    written: set = set()
    used: set = set()
    n_ok = 0
    first_bad = None
    for k, e in enumerate(events):
        for step_c, kind_c in changes:
            if step_c == k:
                c_ext, _b = LAW.apply_change(c_ext, {}, kind_c)
        t, sec, slot = e["type"], e["section"], e["slot"]
        aid = f"{t}:{sec}:{slot}"
        why = None
        if t not in LAW.ACTION_TYPES or sec not in secs:
            why = "no such type or section"
        elif t in fixed:
            if slot != fixed[t]:
                why = f"{t} takes the slot {fixed[t]}"
        elif slot not in secs[sec]:
            why = "no such slot"
        # the standard process itself revises, checks, and fixes slots before they are written (the
        # inventory carries those actions from the start), so no order clause: only repetition
        if why is None and aid in used and e.get("outcome", "done") == "done":
            why = "action repeated"
        if why is None:
            avail = all(c_ext["tools"].get(x, False) for x in TYPE_REQUIRES.get(t, []))
            oc = e.get("outcome", "done")
            if (oc == "done") != avail:
                why = f"outcome {oc} disagrees with the header's tools"
        if why:
            first_bad = first_bad or {"i": k, "why": why, "id": aid}
            continue
        n_ok += 1
        used.add(aid)
        if t == "write" and e.get("outcome", "done") == "done":
            written.add((sec, slot))
    return {"n_events": len(events), "n_feasible": n_ok, "all_feasible": n_ok == len(events) and len(events) > 0, "first_bad": first_bad, "rule": "visible"}


def extended_inventory(w: dict, events: list[dict]) -> list[dict]:
    """The world's inventory plus every visibly valid action the reader used that the inventory
    lacks (requires and goal owner by type, as the constructor assigns them)."""
    inv = [dict(a) for a in w["inventory"]]
    ids = {LAW.action_id(a) for a in inv}
    for e in events:
        aid = f"{e['type']}:{e['section']}:{e['slot']}"
        if aid in ids or e["type"] not in LAW.ACTION_TYPES:
            continue
        inv.append({"type": e["type"], "section": e["section"], "slot": e["slot"], "requires": list(TYPE_REQUIRES.get(e["type"], [])),
                    "goal_owner": TYPE_OWNER.get(e["type"], "produce")})
        ids.add(aid)
    return inv


def feasible(w: dict, events: list[dict]) -> dict:
    """The generation gate's feasibility: every event's action is in the pending inventory at
    its step and its outcome agrees with the objective tools (a done on an unavailable tool,
    or a failed on an available one, is infeasible)."""
    pending = {LAW.action_id(a): a for a in w["inventory"]}
    c_ext = dict(w["state"]["external_context"])
    changes = [tuple(c) for c in (w["trajectory"].get("changes") or [])]
    n_ok = 0
    first_bad = None
    for k, e in enumerate(events):
        for step_c, kind_c in changes:
            if step_c == k:
                c_ext, _b = LAW.apply_change(c_ext, {}, kind_c)      # the schedule the world ran under
        tools = c_ext["tools"]
        aid = f"{e['type']}:{e['section']}:{e['slot']}"
        a = pending.get(aid)
        if a is None:
            first_bad = first_bad or {"i": k, "why": "not pending", "id": aid}
            continue
        avail = all(tools.get(t, False) for t in a.get("requires", []))
        oc = e.get("outcome", "done")
        if (oc == "done") != avail:
            first_bad = first_bad or {"i": k, "why": f"outcome {oc} disagrees with tools", "id": aid}
            continue
        n_ok += 1
        if oc == "done":
            pending.pop(aid, None)
    return {"n_events": len(events), "n_feasible": n_ok, "all_feasible": n_ok == len(events) and len(events) > 0, "first_bad": first_bad}


# ── per-event evidence and the tail threshold ───────────────────────────────────────

def evidence_at(w: dict, i: int, cond: dict, render: str = "log") -> dict:
    """VisibleEvidenceV1 at boundary i (i steps visible), for per-event scoring."""
    steps = w["trajectory"]["steps"]
    prefix = [{"step": s["i"], "type": s["type"], "section": s["section"], "slot": s["slot"], "outcome": s["outcome"]} for s in steps[:i]]
    pending = [dict(a) for a in w["inventory"]]
    for s in steps[:i]:
        if s["outcome"] == "done":
            aid = f"{s['type']}:{s['section']}:{s['slot']}"
            pending = [p for p in pending if LAW.action_id(p) != aid]
    c = w["state"]["external_context"]
    filled: dict = {}
    for s in steps[:i]:
        if s["outcome"] == "done":
            filled.setdefault(s["section"], []).append(f"{s['type']}@{s['slot']}")
    ev = {"version": EVIDENCE_VERSION, "unit_ref": cond.get("unit_ref", "u"), "condition_ref": cond.get("condition_ref", "c"),
          "domain": w["domain"],
          "artifact_state": {"topic": w["doc"]["topic"],
                             "sections": [{"name": sec["name"], "slots": list(sec["slots"]), "filled": filled.get(sec["name"], [])} for sec in w["doc"]["sections"]],
                             "prefix_text": W.render_prefix_text(prefix, render, w["doc"]["topic"])},
          "process_prefix": prefix,
          "query": {"next_action_options": [LAW.action_id(a) for a in pending], "type_vocabulary": list(LAW.ACTION_TYPES),
                    "sections": [s["name"] for s in w["doc"]["sections"]], "stop": ["stop", "continue"],
                    "context_change": None, "invalidation_responses": ["correct", "retain", "rewrite"],
                    "boundary_types": ["satisfaction", "deadline", "fatigue", "equivalent"]},
          "regime": cond.get("regime", "cold"), "render": render,
          "brief": {"required_sections": list(c["brief_sections"]), "audience": c["audience"],
                    "tools_available": {t: bool(v) for t, v in c["tools"].items()}, "deadline": c["deadline"]},
          "objective_options": {"initial": [{k: a[k] for k in ("type", "section", "slot", "requires", "goal_owner")} for a in w["inventory"]],
                                "at_cut": [{k: a[k] for k in ("type", "section", "slot", "requires", "goal_owner")} for a in pending]}}
    return ev


def per_event_gaps(w: dict, dom_params: dict, cond: dict | None = None) -> list[dict]:
    """For every event of the trajectory: the exact policy's probability of the taken action
    (the oracle), DOM's probability from the evidence at that boundary, and the gap."""
    out = []
    cond = cond or {"unit_ref": "u", "condition_ref": "c"}
    for i, s in enumerate(w["trajectory"]["steps"]):
        ev = evidence_at(w, i, cond)
        aid = f"{s['type']}:{s['section']}:{s['slot']}"
        d = B.dom(ev, dom_params) or {}
        p_dom = float((d.get("next_action") or {}).get(aid, 0.0))
        out.append({"i": i, "id": aid, "p_or": float(s["lik"]), "p_dom": p_dom, "gap": float(s["lik"]) - p_dom,
                    "n_options": len(ev["query"]["next_action_options"])})
    return out


def tail_threshold(dom_params: dict, n_per_domain: int = 40, band: int = HELDOUT_BAND, shape: str | None = None, pct: int = 80) -> dict:
    """tau per family: the pct-th percentile of the per-event oracle-minus-DOM gap over POP
    worlds (held-out band), written before any reader runs."""
    gaps = []
    n_worlds = 0
    for d in DOMAINS:
        for i in range(n_per_domain):
            lid = pop_lid(i, d, band)
            w = sample_world(lid)
            if shape and w["shape"] != shape:
                continue
            n_worlds += 1
            gaps.extend(g["gap"] for g in per_event_gaps(w, dom_params))
    if not gaps:
        return {"tau": None, "n_events": 0, "n_worlds": 0}
    gaps.sort()
    k = min(len(gaps) - 1, max(0, int(round(pct / 100 * (len(gaps) - 1)))))
    return {"tau": gaps[k], "percentile": pct, "n_events": len(gaps), "n_worlds": n_worlds, "shape": shape,
            "mean_gap": sum(gaps) / len(gaps), "share_above_zero": sum(1 for g in gaps if g > 0) / len(gaps)}


def _selftest() -> list[str]:
    fails = []
    ex = training_example(1, "essay")
    if "log:" not in ex["text"] or ex["n_events"] < 1:
        fails.append("training example malformed")
    w = sample_world(pop_lid(3, "essay"), finish=True)
    if not w["degenerate"]:
        m = marginal_log_likelihood(w)
        if m["total"] is None or m["total"] > 0:
            fails.append("marginal likelihood is not a log probability")
        steps = [{"type": s["type"], "section": s["section"], "slot": s["slot"], "outcome": s["outcome"]} for s in w["trajectory"]["steps"]]
        if not feasible(w, steps)["all_feasible"]:
            fails.append("the world's own log is not feasible")
        bad = list(steps)
        bad[0] = dict(bad[0], slot="nowhere")
        if feasible(w, bad)["all_feasible"]:
            fails.append("an infeasible log passed the feasibility check")
        if not feasible_visible(w, steps)["all_feasible"]:
            fails.append("the world's own log fails the visible feasibility rule")
        if feasible_visible(w, bad)["all_feasible"]:
            fails.append("an off-plan slot passed the visible rule")
    return fails
