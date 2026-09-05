"""Stage 7 maker law (brief §3, §7.2): the ONE executable semantics of a maker state,
shared by the constructor (which simulates and scores with it) and the capsule solver
(which executes a SUPPLIED state from visible evidence). STDLIB ONLY, NO REPOSITORY
IMPORTS: this file is copied into every capsule. Exactness by construction: there is one
code path for the policy, the stop hazard, the subjective action space, and the maker
context, so an executable supplied state reproduces the oracle's numbers through the
evidence file alone, and an omitted factor cannot be silently re-derived (the solver
raises when a factor it needs is absent).

The objects (§3): external_context C_ext, belief_state B, expertise_law K (the maker's
learned transition/action structure: feasibility thresholds, costs, chain bonuses,
fluency temperature, success rates), maker_context C_m = phi(C_ext, B, K),
subjective_action_space A_tilde = A(C_m, B, K), proximal_goal G (a utility table over
action types), history_residue H (habit biases and a maintained intention). The realized
process tau is the trajectory, never a factor. An external transition model is NOT a
sixth latent: the transition structure lives inside K.

DESIGN CHECK (2026-09-02)
lessons read: LESSONS §3 (an exact ruler is validated on the construction it rules: the
  constructor's self-tests print one world per class and check that per-step likelihoods
  sum to one; the stop law must be able to vary with the maker state it tests, so the
  hazard has explicit goal, belief, and expertise terms and the constructor asserts a
  nontrivial oracle gap per world), §5 (no gate here).
gates: none here; the constructor and engines own the bands. bands: none.
"""

from __future__ import annotations

import math

ACTION_TYPES = ("write", "revise", "check", "consult", "cite", "restructure", "probe", "fix")
GOALS = ("produce", "tighten", "audit", "attribute")
TOOLS = ("library", "source_access")
# goal utilities per action type: the executable content of a proximal goal (a goal is
# supplied to a reader as this table, never as its name; §2.1.11 and pre-mortem 11)
GOAL_UTILITY = {
    "produce":   {"write": 2.2, "revise": 0.2, "check": -0.6, "consult": 0.1, "cite": -0.2, "restructure": 0.3, "probe": 0.0, "fix": 0.4},
    "tighten":   {"write": -0.4, "revise": 2.0, "check": 0.4, "consult": -0.2, "cite": 0.0, "restructure": 1.2, "probe": 0.1, "fix": 0.6},
    "audit":     {"write": -0.8, "revise": 0.3, "check": 2.1, "consult": 1.2, "cite": 0.2, "restructure": -0.3, "probe": 0.3, "fix": 1.4},
    "attribute": {"write": -0.5, "revise": 0.0, "check": 0.2, "consult": 0.8, "cite": 2.3, "restructure": -0.2, "probe": 0.0, "fix": 0.2},
}
READING_ORDER_BONUS = 0.5
SWITCH_COST = 1.2
STOP_BASE = -4.2      # the base hazard per boundary (1.5 percent); stops concentrate where the state puts them
STOP_SATISFIED = 3.8      # a satisfied goal is a 40-percent stop
STOP_DEADLINE = 2.4      # scaled by progress under a PERCEIVED tight deadline (belief-dependent)
STOP_FATIGUE = 1.8      # past the law's expected length (expertise-dependent)
STOP_AUDIENCE_SELF = 0.3      # no external audience lowers the bar to stop


class LawError(ValueError):
    pass


def _need(state: dict, key: str) -> dict:
    v = state.get(key)
    if v is None:
        raise LawError(f"the law needs {key}; it is not supplied")
    return v


# ── the derived factors (§3): C_m and A_tilde ─────────────────────────────────────────

def maker_context(c_ext: dict, belief: dict, law: dict) -> dict:
    """C_m = phi(C_ext, B, K): the objective context as the maker perceives it. Tools and
    deadline come through belief; the required sections come through the brief; the
    audience's weight is discounted by expertise confidence."""
    perceived_tools = {t: bool(belief.get("believed_tools", {}).get(t, c_ext.get("tools", {}).get(t, False))) for t in TOOLS}
    conf = float(law.get("confidence", 0.5))
    return {"perceived_tools": perceived_tools,
            "perceived_deadline": belief.get("believed_deadline", c_ext.get("deadline", "loose")),
            "perceived_required": list(c_ext.get("brief_sections", [])),
            "audience": c_ext.get("audience", "peer"),
            "audience_weight": round((1.0 - 0.6 * conf) if c_ext.get("audience") != "self" else 0.0, 4),
            "believed_checked": sorted(belief.get("believed_checked", []))}


def subjective_options(objective_options: list[dict], c_m: dict, belief: dict, law: dict) -> list[dict]:
    """A_tilde = A(C_m, B, K): the objective options the maker believes available AND
    perceives as executable: tool requirements met under PERCEIVED tools, skill at or
    above the law's feasibility threshold, and no check on a section believed checked."""
    out = []
    skill = law.get("skill", {})
    thr = law.get("feasible_min_skill", {})
    for a in objective_options:
        req = a.get("requires", [])
        if any(not c_m["perceived_tools"].get(t, False) for t in req):
            continue
        if float(skill.get(a["type"], 0.0)) < float(thr.get(a["type"], 0.0)):
            continue
        if a["type"] == "check" and a["section"] in c_m.get("believed_checked", []):
            continue
        out.append(a)
    return out


# ── the policy: exact action likelihoods over A_tilde ────────────────────────────────

def action_id(a: dict) -> str:
    return f"{a['type']}:{a['section']}:{a['slot']}"


def scores(options: list[dict], goal: dict, law: dict, residue: dict, c_m: dict,
           sections: list[str], last_type: str | None, step: int) -> dict:
    """Every option's score under the state; softmax over these is the exact likelihood.
    goal: {"utility": {type: u}}; law: {"cost": {type: c}, "chain": {(prev,next): b} as
    "prev>next" keys, "fluency": temperature}; residue: {"habit": {type: b},
    "maintained": {"cue_step": s, "option": action_id}}."""
    util = goal["utility"]
    cost = law.get("cost", {})
    chain = law.get("chain", {})
    habit = residue.get("habit", {})
    maintained = residue.get("maintained") or {}
    out = {}
    for a in options:
        t = a["type"]
        s = float(util.get(t, 0.0)) - float(cost.get(t, 0.0))
        if last_type is not None:
            s += float(chain.get(f"{last_type}>{t}", 0.0))
        s += float(habit.get(t, 0.0))
        idx = sections.index(a["section"]) if a["section"] in sections else len(sections)
        s += READING_ORDER_BONUS * (1.0 - idx / max(1, len(sections)))
        if a["section"] in c_m.get("perceived_required", []):
            s += 0.4 * float(c_m.get("audience_weight", 0.0))
        if maintained and maintained.get("cue_step") == step and maintained.get("option") == action_id(a):
            s += 6.0
        out[action_id(a)] = s
    return out


def softmax(sc: dict, temperature: float) -> dict:
    if not sc:
        return {}
    mx = max(sc.values())
    ex = {k: math.exp((v - mx) / max(temperature, 1e-6)) for k, v in sc.items()}
    z = sum(ex.values())
    return {k: v / z for k, v in ex.items()}


def policy(options: list[dict], goal: dict, law: dict, residue: dict, c_m: dict,
           sections: list[str], last_type: str | None, step: int) -> dict:
    sc = scores(options, goal, law, residue, c_m, sections, last_type, step)
    return softmax(sc, float(law.get("fluency", 1.0)))


# ── the stop law: a hazard that depends on the maker state (§7.1, test 10) ───────────

def stop_hazard(goal_pending_empty: bool, progress: float, steps: int, law: dict, c_m: dict) -> tuple[float, dict]:
    """p_stop at a boundary and the contribution of each term (the boundary type P06
    reads is the largest positive contributor)."""
    expected_len = float(law.get("expected_len", 12.0))
    terms = {"satisfaction": STOP_SATISFIED if goal_pending_empty else 0.0,
             "deadline": STOP_DEADLINE * progress if c_m.get("perceived_deadline") == "tight" else 0.0,
             "fatigue": STOP_FATIGUE * max(0.0, steps / expected_len - 1.0),
             "audience": STOP_AUDIENCE_SELF if c_m.get("audience") == "self" else 0.0}
    z = STOP_BASE + sum(terms.values())
    return 1.0 / (1.0 + math.exp(-z)), terms


def boundary_type(terms: dict) -> str:
    live = {k: v for k, v in terms.items() if k in ("satisfaction", "deadline", "fatigue") and v > 0}
    if not live:
        return "none"
    top = sorted(live.items(), key=lambda kv: -kv[1])
    if len(top) > 1 and abs(top[0][1] - top[1][1]) < 0.15:
        return "equivalent"
    return top[0][0]


# ── the solver: execute a SUPPLIED complete or partial state at a cut ────────────────

def options_at_cut(evidence: dict) -> list[dict]:
    """The objective option list at the cut; the evidence carries it as
    {"initial": [...], "at_cut": [...]} (a bare list is read as the at-cut list)."""
    oo = evidence.get("objective_options")
    if isinstance(oo, dict):
        return list(oo.get("at_cut", []))
    return list(oo or [])


def initial_inventory(evidence: dict) -> list[dict]:
    oo = evidence.get("objective_options")
    if isinstance(oo, dict) and oo.get("initial"):
        return list(oo["initial"])
    return options_at_cut(evidence)


def next_goal(goal_name: str, pending: list[dict], goals_order: list[str]) -> str:
    """The goal evolves when its pending set empties: the next goal in the order that
    still has pending actions (the shared, factor-free rule)."""
    if any(a.get("goal_owner") == goal_name for a in pending):
        return goal_name
    for g in goals_order:
        if any(a.get("goal_owner") == g for a in pending):
            return g
    return goal_name


def execute(state: dict, evidence: dict) -> dict:
    """Run a complete supplied state against the visible evidence: the predictive
    distributions at the cut (next action over the OBJECTIVE option ids with zero mass on
    subjectively unavailable ones, type and section marginals, the stop hazard, the
    boundary type) computed from supplied factors only. Raises LawError when a factor the
    computation needs is absent, so a rung that withholds a factor cannot be solved
    without a hypothesis for it."""
    c_ext = _need(state, "external_context")
    belief = _need(state, "belief_state")
    law = _need(state, "expertise_law")
    goal = _need(state, "proximal_goal")
    if not goal.get("owner"):
        raise LawError("the proximal goal needs its owner (the initial goal it governs)")
    residue = state.get("history_residue") or {"habit": {}, "maintained": None}
    c_m = state.get("maker_context") or maker_context(c_ext, belief, law)
    objective = options_at_cut(evidence)
    sections = [s["name"] for s in evidence["artifact_state"]["sections"]]
    prefix = evidence.get("process_prefix", [])
    # the goal evolves along the prefix by the shared rule: replay it from the initial goal
    pending = list(initial_inventory(evidence))
    gname = goal["owner"]
    g_last = gname
    for e in prefix:
        gname = next_goal(gname, pending, list(GOALS))
        g_last = gname                        # the goal that governed this visible step
        if e.get("outcome") != "failed":
            aid = f"{e['type']}:{e['section']}:{e['slot']}"
            pending = [a for a in pending if action_id(a) != aid]
    gname = next_goal(gname, pending, list(GOALS))
    goal_now = {"utility": GOAL_UTILITY[gname], "owner": gname} if gname in GOAL_UTILITY else goal
    a_tilde = state.get("subjective_action_space")
    if a_tilde is None:
        a_tilde = subjective_options(objective, c_m, belief, law)
    else:
        ids = set(a_tilde if isinstance(a_tilde, list) and a_tilde and isinstance(a_tilde[0], str) else [action_id(a) for a in a_tilde])
        a_tilde = [a for a in objective if action_id(a) in ids]
    last_type = prefix[-1]["type"] if prefix else None
    step = len(prefix)
    pol = policy(a_tilde, goal_now, law, residue, c_m, sections, last_type, step)
    nxt = {action_id(a): pol.get(action_id(a), 0.0) for a in objective}
    type_d = {t: 0.0 for t in ACTION_TYPES}
    sec_d = {s: 0.0 for s in sections}
    for a in objective:
        p = nxt[action_id(a)]
        type_d[a["type"]] += p
        sec_d[a["section"]] = sec_d.get(a["section"], 0.0) + p
    done_ids = {f"{e['type']}:{e['section']}:{e['slot']}" for e in prefix if e.get("outcome") != "failed"}
    # the stop at this boundary is judged on the goal that governed the last visible step
    # (the generator's rule: satisfaction fires when that goal's pending set just emptied)
    goal_pending = [a for a in objective if a.get("goal_owner") == g_last and action_id(a) not in done_ids]
    total = len(objective) + len(done_ids)
    progress = len(done_ids) / max(1, total)
    p_stop, terms = stop_hazard(not goal_pending, progress, step, law, c_m)
    return {"next_action": nxt, "next_type": type_d, "next_section": sec_d,
            "p_stop": p_stop, "stop_terms": terms, "boundary_type": boundary_type(terms),
            "subjective_ids": [action_id(a) for a in a_tilde], "goal_now": gname,
            "invalidation": invalidation_dist(law, goal_now["utility"], c_m)}


# ── the context change and the invalidation response (shared by constructor and capsule) ─

CHANGE_KINDS = ("library_arrives", "library_withdrawn", "deadline_lifted", "deadline_imposed", "audience_changes")


def apply_change(c_ext: dict, belief: dict, kind: str) -> tuple[dict, dict]:
    """The five external changes and what the maker learns of each (a tool arriving or
    leaving is seen; a deadline lifted or imposed is seen; an audience change is external
    only). Deep copies; the ONE semantics the constructor's worlds and the capsule share."""
    import copy                                                                    # noqa: PLC0415
    c2 = copy.deepcopy(c_ext)
    b2 = copy.deepcopy(belief)
    if kind == "library_arrives":
        c2.setdefault("tools", {})["library"] = True
        b2.setdefault("believed_tools", {})["library"] = True
    elif kind == "library_withdrawn":
        c2.setdefault("tools", {})["library"] = False
        b2.setdefault("believed_tools", {})["library"] = False
    elif kind == "deadline_lifted":
        c2["deadline"] = "loose"
        b2["believed_deadline"] = "loose"
    elif kind == "deadline_imposed":
        c2["deadline"] = "tight"
        b2["believed_deadline"] = "tight"
    elif kind == "audience_changes":
        c2["audience"] = "editor" if c_ext.get("audience") != "editor" else "self"
    return c2, b2


def execute_changed(state: dict, evidence: dict, kind: str) -> dict:
    """The changed-context counterfactual: the change applied to the (supplied or proposed)
    context and beliefs, the maker context and the subjective set re-derived, the policy
    read at the cut (the target P07 and K06 score; the oracle computes it the same way)."""
    st = dict(state)
    c2, b2 = apply_change(_need(st, "external_context"), _need(st, "belief_state"), kind)
    st["external_context"], st["belief_state"] = c2, b2
    st.pop("maker_context", None)
    st.pop("subjective_action_space", None)
    return execute(st, evidence)


def invalidation_dist(law: dict, goal_utility: dict, c_m: dict) -> dict:
    """After a consulted source is invalidated: correct, rewrite, or retain, from the law
    (correction follows fix skill and the audit utility, rewrite follows revise utility and
    restructure feasibility, retention is the residual and rises under a tight perceived
    deadline and with confidence)."""
    sc = {"correct": goal_utility["fix"] - law["cost"]["fix"] + 1.5 * law["skill"]["fix"],
          "rewrite": goal_utility["revise"] - law["cost"]["revise"] + (0.6 if law["skill"]["restructure"] >= law["feasible_min_skill"]["restructure"] else -0.4),
          "retain": 0.2 - 0.8 * law["confidence"] + (0.5 if c_m.get("perceived_deadline") == "tight" else 0.0)}
    return softmax(sc, law["fluency"])


def prefix_log_likelihood(state: dict, evidence: dict) -> float:
    """The exact log likelihood of the observed prefix under a (complete) state: the
    known-law selector's likelihood function (§4.2), replayed step by step from the
    evidence's own initial option inventory."""
    c_ext = _need(state, "external_context")
    belief = _need(state, "belief_state")
    law = _need(state, "expertise_law")
    goal = _need(state, "proximal_goal")
    if not goal.get("owner"):
        raise LawError("the proximal goal needs its owner (the initial goal it governs)")
    residue = state.get("history_residue") or {"habit": {}, "maintained": None}
    c_m = state.get("maker_context") or maker_context(c_ext, belief, law)
    sections = [s["name"] for s in evidence["artifact_state"]["sections"]]
    pending = list(initial_inventory(evidence))
    total = 0.0
    last_type = None
    gname = goal["owner"]
    order = list(GOALS)
    for step, e in enumerate(evidence.get("process_prefix", [])):
        gname = next_goal(gname, pending, order)
        g = {"utility": GOAL_UTILITY[gname], "owner": gname} if gname in GOAL_UTILITY else goal
        opts = subjective_options(pending, c_m, belief, law)
        pol = policy(opts, g, law, residue, c_m, sections, last_type, step)
        aid = f"{e['type']}:{e['section']}:{e['slot']}"
        if e.get("outcome") == "failed":
            # an attempted, objectively unavailable action: likelihood under the policy that
            # perceived it available; a state that did not perceive it cannot explain it
            p = pol.get(aid, 0.0)
        else:
            p = pol.get(aid, 0.0)
        total += math.log(max(p, 1e-9))
        if e.get("outcome") != "failed":
            pending = [a for a in pending if action_id(a) != aid]
        last_type = e["type"]
    return total
