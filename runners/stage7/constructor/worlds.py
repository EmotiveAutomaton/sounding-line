"""Stage 7 known-answer factor worlds (brief §3, §7.1, §7.2): a maker revises a document
episode under a state whose seven factors vary SEPARATELY, and every hidden target is a
draw from the world's own law, never an annotation.

THE CHASSIS. A document of sections and slots defines an OBJECTIVE action inventory
(writes, revisions, checks, consults, cites, restructurings, probes, fixes), some of it
tool-gated. The external context C_ext names the brief, audience, objective tools, and
deadline, plus one scheduled context change. The belief state B may misperceive tools,
the deadline, or which sections are already checked. The expertise law K (runners/
stage7/reader/law.py, the ONE code path) gives feasibility thresholds, costs, chain
bonuses, a fluency temperature, and an expected episode length. The maker context C_m and
the subjective action space A_tilde are DERIVED by the law from those three; the proximal
goal G is a utility table; the history residue H is a habit bias plus a maintained
intention cued at a later step. The policy is a softmax over A_tilde; an attempt on an
objectively unavailable action FAILS visibly and corrects the belief. The stop hazard has
explicit satisfaction, perceived-deadline, fatigue, and audience terms, so it VARIES with
G, B, and K (test 10). Hidden targets after the cut: the next feasible action, its type
and section, the stop at the next boundary and its type, the whole tail, the rejected
alternative, the changed-context choice recomputed under the same law, the response to a
later-invalidated source, and the exact equivalence class over the factor grid.

Twins: per-factor swaps with the prefix held identical (the visible-prefix collision;
belief, action-space, and residue swaps are inert on the prefix by construction and
collide exactly; goal and law swaps hold the prefix fixed with matched surface and the
oracle posterior records what the prefix already separates). Mutations: the hidden tail,
the stop parameters, and the future events re-drawn with the prefix fixed (I05-I07).

DESIGN CHECK (2026-09-02)
lessons read: LESSONS §3 (validate the ruler on known answers first: self-tests run at
  import in the guard suite; known-answer existence checked at construction: a world
  whose oracle gap is under the floor is DEGENERATE and counted, never scored; truth
  marginals vary within every cell; a counterfactual is counterfactual in every cell;
  count the construction's identity space against the unit count and hash every
  construction onto its lineage; a distinctness gate sized by identifiability at the
  observation count, not a nominal epsilon), §5 (no gate here).
gates and bands (enforced here or in the K/R engines):
  - exactness: per-step likelihoods are a softmax over A_tilde and sum to one; the
    supplied complete state executed by the capsule solver reproduces the oracle's
    numbers (test 13); NULL of a broken law: mismatch above 1e-9; ALTERNATIVE: identity.
  - oracle gap: the exact next-action log score minus the frozen DOM's must be at or
    above MIN_GAP_NATS on a world for the world to count (K01); direction: a gap that
    fails is BELOW the floor; bands exhaustive (degenerate under, live at or above).
  - target hiding: renderers never print goal, law, belief, or residue names; the tail,
    stop, and changed-context truth appear in no visible field (I10's canaries prove the
    check can fail).
"""

from __future__ import annotations

import copy
import hashlib
import math
import random
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO))

from runners.stage7.reader import law as LAW                                       # noqa: E402
from runners.stage7.reader.law import (ACTION_TYPES, GOALS, GOAL_UTILITY, TOOLS,   # noqa: E402
                                       action_id, boundary_type, maker_context, policy,
                                       stop_hazard, subjective_options)
from soundingline.stage7 import EVIDENCE_VERSION, MIN_GAP_NATS                     # noqa: E402

DOMAINS = ("essay", "workshop_doc")
RENDERS = ("prose", "log")
REGIMES = ("cold", "domain_expert", "maker_familiar")
TOPICS = {"essay": ["the kiln schedule", "the flood notice", "the survey method", "the archive index",
                    "the delivery route", "the glaze recipe"],
          "workshop_doc": ["the lathe manual", "the bench layout", "the tool inventory",
                           "the safety sheet", "the order ledger", "the finishing guide"]}

# ── the factor grids (§7.2): named executable laws, beliefs, residues ────────────────

LAWS = {
    "novice": {"skill": {"write": 0.5, "revise": 0.4, "check": 0.4, "consult": 0.3, "cite": 0.3, "restructure": 0.2, "probe": 0.2, "fix": 0.3},
               "feasible_min_skill": {"restructure": 0.6, "probe": 0.4, "fix": 0.3},
               "cost": {"write": 0.3, "revise": 0.4, "check": 0.3, "consult": 0.5, "cite": 0.5, "restructure": 0.9, "probe": 0.6, "fix": 0.4},
               "chain": {}, "fluency": 1.6, "expected_len": 10.0, "confidence": 0.3},
    "expert": {"skill": {"write": 0.9, "revise": 0.9, "check": 0.8, "consult": 0.7, "cite": 0.7, "restructure": 0.8, "probe": 0.6, "fix": 0.9},
               "feasible_min_skill": {"restructure": 0.6, "probe": 0.4, "fix": 0.3},
               "cost": {"write": 0.1, "revise": 0.1, "check": 0.1, "consult": 0.3, "cite": 0.3, "restructure": 0.3, "probe": 0.3, "fix": 0.1},
               "chain": {"write>revise": 0.5, "check>fix": 0.9, "restructure>revise": 0.6}, "fluency": 0.9, "expected_len": 14.0, "confidence": 0.8},
    "specialist": {"skill": {"write": 0.6, "revise": 0.5, "check": 0.7, "consult": 0.9, "cite": 0.9, "restructure": 0.4, "probe": 0.5, "fix": 0.6},
                   "feasible_min_skill": {"restructure": 0.6, "probe": 0.4, "fix": 0.3},
                   "cost": {"write": 0.3, "revise": 0.3, "check": 0.2, "consult": 0.1, "cite": 0.1, "restructure": 0.7, "probe": 0.4, "fix": 0.3},
                   "chain": {"consult>cite": 1.0, "check>consult": 0.5}, "fluency": 1.1, "expected_len": 12.0, "confidence": 0.6},
}
LAW_NAMES = tuple(LAWS)
BELIEFS = ("accurate", "false_library", "false_deadline", "checked_illusion")
RESIDUES = ("none", "habit_check", "habit_write", "maintained_cite")
TENDENCIES = ("care", "speed")                      # the bounded persistent-tendency rival (V)
GRID_SIZE = len(GOALS) * len(LAW_NAMES) * len(BELIEFS) * len(RESIDUES)


def _rng(lid: str, salt: str = "") -> random.Random:
    return random.Random(int(hashlib.md5(f"{lid}|{salt}".encode()).hexdigest()[:8], 16))


def _widx(lid: str) -> int:
    for part in lid.split("|"):
        if part.startswith("w") and part[1:].isdigit():
            return int(part[1:])
    return int(hashlib.md5(lid.encode()).hexdigest()[:6], 16) % 4096


def domain_generic_law() -> dict:
    """K_dom: the population-average law (the domain-expert regime's supplied law and the
    generic-law arm); every numeric field averaged over the three named laws."""
    out = {"skill": {}, "feasible_min_skill": dict(LAWS["novice"]["feasible_min_skill"]), "cost": {}, "chain": {}}
    for t in ACTION_TYPES:
        out["skill"][t] = round(sum(L["skill"][t] for L in LAWS.values()) / len(LAWS), 4)
        out["cost"][t] = round(sum(L["cost"][t] for L in LAWS.values()) / len(LAWS), 4)
    keys = set()
    for L in LAWS.values():
        keys |= set(L["chain"])
    for k in keys:
        out["chain"][k] = round(sum(L["chain"].get(k, 0.0) for L in LAWS.values()) / len(LAWS), 4)
    out["fluency"] = round(sum(L["fluency"] for L in LAWS.values()) / len(LAWS), 4)
    out["expected_len"] = round(sum(L["expected_len"] for L in LAWS.values()) / len(LAWS), 4)
    out["confidence"] = round(sum(L["confidence"] for L in LAWS.values()) / len(LAWS), 4)
    return out


# ── the document and the objective inventory ─────────────────────────────────────────

def _doc_plan(lid: str, domain: str) -> dict:
    r = _rng(lid, "doc")
    n_sec = 3 + r.randrange(2)
    sections = []
    for s in range(n_sec):
        n_slots = 2 + r.randrange(2)
        sections.append({"name": f"sec{s + 1}", "slots": [f"s{s + 1}.{k + 1}" for k in range(n_slots)]})
    topic = TOPICS[domain][r.randrange(len(TOPICS[domain]))]
    return {"domain": domain, "topic": topic, "sections": sections}


def _inventory(lid: str, doc: dict) -> list[dict]:
    """The objective action inventory: one write per slot (produce), a revision on about
    half the slots (tighten), one check per section (audit), one consult on the first
    section (audit, needs source access), one cite on the last section (attribute, needs
    the library), one restructure on a middle section (tighten, skill-gated), one probe
    (produce, skill-gated), one fix on a checked section (audit, skill-gated)."""
    r = _rng(lid, "inventory")
    acts = []
    for sec in doc["sections"]:
        for slot in sec["slots"]:
            acts.append({"type": "write", "section": sec["name"], "slot": slot, "requires": [], "goal_owner": "produce"})
    slots = [(sec["name"], slot) for sec in doc["sections"] for slot in sec["slots"]]
    for sec_name, slot in r.sample(slots, max(2, len(slots) // 2)):
        acts.append({"type": "revise", "section": sec_name, "slot": slot, "requires": [], "goal_owner": "tighten"})
    for sec in doc["sections"]:
        acts.append({"type": "check", "section": sec["name"], "slot": sec["slots"][0], "requires": [], "goal_owner": "audit"})
    acts.append({"type": "consult", "section": doc["sections"][0]["name"], "slot": "src", "requires": ["source_access"], "goal_owner": "audit"})
    acts.append({"type": "cite", "section": doc["sections"][-1]["name"], "slot": "ref", "requires": ["library"], "goal_owner": "attribute"})
    mid = doc["sections"][len(doc["sections"]) // 2]["name"]
    acts.append({"type": "restructure", "section": mid, "slot": "order", "requires": [], "goal_owner": "tighten"})
    acts.append({"type": "probe", "section": doc["sections"][0]["name"], "slot": "tech", "requires": [], "goal_owner": "produce"})
    acts.append({"type": "fix", "section": doc["sections"][1]["name"], "slot": doc["sections"][1]["slots"][0], "requires": [], "goal_owner": "audit"})
    return acts


# ── the maker state ───────────────────────────────────────────────────────────────────

def _external_context(lid: str, doc: dict, forced: dict) -> dict:
    r = _rng(lid, "cext")
    names = [s["name"] for s in doc["sections"]]
    k = max(2, len(names) - 1)
    brief = sorted(r.sample(names, k), key=names.index)
    tools = {"library": r.random() < 0.5, "source_access": r.random() < 0.7}
    audience = ["editor", "peer", "self"][r.randrange(3)]
    deadline = "tight" if r.random() < 0.5 else "loose"
    change_kind = ["library_arrives" if not tools["library"] else "library_withdrawn",
                   "deadline_lifted" if deadline == "tight" else "deadline_imposed",
                   "audience_changes"][r.randrange(3)]
    out = {"brief_sections": brief, "audience": audience, "tools": tools, "deadline": deadline,
           "scheduled_change": change_kind}
    out.update({k: v for k, v in forced.items() if k in out})
    return out


def _belief(name: str, c_ext: dict, doc: dict) -> dict:
    tools = dict(c_ext["tools"])
    b = {"believed_tools": tools, "believed_deadline": c_ext["deadline"], "believed_checked": []}
    if name == "false_library":
        b["believed_tools"] = dict(tools, library=not tools["library"])
    elif name == "false_deadline":
        b["believed_deadline"] = "loose" if c_ext["deadline"] == "tight" else "tight"
    elif name == "checked_illusion":
        b["believed_checked"] = [doc["sections"][1]["name"]]
    return b


def _residue(name: str, inventory: list[dict], cue_step: int) -> dict:
    if name == "habit_check":
        return {"habit": {"check": 0.9}, "maintained": None}
    if name == "habit_write":
        return {"habit": {"write": 0.9}, "maintained": None}
    if name == "maintained_cite":
        cite = next((a for a in inventory if a["type"] == "cite"), None)
        return {"habit": {}, "maintained": {"cue_step": cue_step, "option": action_id(cite) if cite else None}}
    return {"habit": {}, "maintained": None}


def _goal(name: str) -> dict:
    return {"utility": dict(GOAL_UTILITY[name]), "name_ref": name}


def _tendency_law(law: dict, tendency: str) -> dict:
    """The persistent-tendency rival shifts every cost by a small constant: 'care' pays
    more attention (higher check/fix utility through lower cost), 'speed' the reverse. A
    bounded rival that is policy-equivalent on most prefixes (V-trunk)."""
    out = copy.deepcopy(law)
    d = -0.15 if tendency == "care" else 0.15
    for t in ("check", "fix", "consult"):
        out["cost"][t] = round(out["cost"][t] + d, 4)
    return out


def make_state(lid: str, doc: dict, inventory: list[dict], goal: str, law_name: str, belief: str,
               residue: str, tendency: str, forced_cext: dict | None = None) -> dict:
    c_ext = _external_context(lid, doc, forced_cext or {})
    b = _belief(belief, c_ext, doc)
    law = _tendency_law(LAWS[law_name], tendency)
    c_m = maker_context(c_ext, b, law)
    h = _residue(residue, inventory, cue_step=_rng(lid, "cue").randrange(4, 9))
    return {"external_context": c_ext, "belief_state": b, "expertise_law": law, "maker_context": c_m,
            "proximal_goal": _goal(goal), "history_residue": h, "persistent_tendency": {"tradeoff": tendency},
            "names": {"goal": goal, "law": law_name, "belief": belief, "residue": residue, "tendency": tendency}}


# ── simulation: exact likelihoods, visible failures, the stop law ─────────────────────

def _apply_change(c_ext: dict, belief: dict, kind: str) -> tuple[dict, dict]:
    return LAW.apply_change(c_ext, belief, kind)          # the ONE semantics (law.py)


def simulate(lid: str, doc: dict, inventory: list[dict], state: dict, salt: str = "traj",
             forced_prefix: list[dict] | None = None, change_step: int | None = None,
             stop_shift: float = 0.0, max_steps: int = 40, changes: list | None = None) -> dict:
    """Roll the policy to stop or exhaustion. Returns steps (with per-step likelihood of
    the taken action and the stop hazard at the following boundary), the stop index, the
    boundary type, and the context-change step. `forced_prefix` replays given steps (a twin
    holds the prefix fixed and simulates its own tail); `stop_shift` is the hidden stop
    mutation (I06)."""
    r = _rng(lid, salt)
    sections = [s["name"] for s in doc["sections"]]
    c_ext = copy.deepcopy(state["external_context"])
    belief = copy.deepcopy(state["belief_state"])
    law = state["expertise_law"]
    residue = state["history_residue"]
    gname = state["proximal_goal"]["name_ref"]
    pending = [dict(a) for a in inventory]
    done: set = set()
    steps = []
    last_type = None
    stopped_at = None
    btype = "none"
    cs = change_step if change_step is not None else _rng(lid, "change").randrange(5, 10)
    changes = [tuple(c) for c in changes] if changes is not None else [(cs, c_ext["scheduled_change"])]
    total_n = len(inventory)
    stop_kind = "max_steps"
    for i in range(max_steps):
        if not pending:
            stop_kind = "exhausted"
            break
        if i == 0:
            for (step_c, kind_c) in changes:
                if step_c == 0:
                    c_ext, belief = _apply_change(c_ext, belief, kind_c)
        c_m = maker_context(c_ext, belief, law)
        gname = LAW.next_goal(gname, pending, list(GOALS))
        goal = _goal(gname)
        opts = subjective_options(pending, c_m, belief, law)
        if not opts:
            # nothing perceived feasible: the maker stops (a satisfaction-free boundary)
            stopped_at = i - 1 if steps else None
            btype = "fatigue"
            stop_kind = "no_options"
            break
        pol = policy(opts, goal, law, residue, c_m, sections, last_type, i)
        if forced_prefix and i < len(forced_prefix):
            aid = f"{forced_prefix[i]['type']}:{forced_prefix[i]['section']}:{forced_prefix[i]['slot']}"
            if aid not in pol:
                return {"steps": steps, "stopped_at": None, "boundary_type": "none", "change_step": cs,
                        "changes": changes, "impossible_prefix": True}
        else:
            u = r.random()
            acc = 0.0
            aid = list(pol)[-1]
            for k, p in pol.items():
                acc += p
                if u <= acc:
                    aid = k
                    break
        a = next(x for x in opts if action_id(x) == aid)
        objectively_available = all(c_ext["tools"].get(t, False) for t in a.get("requires", []))
        outcome = "done" if objectively_available else "failed"
        steps.append({"i": i, "type": a["type"], "section": a["section"], "slot": a["slot"],
                      "outcome": outcome, "goal": gname, "lik": pol[aid], "goal_owner": a["goal_owner"]})
        if outcome == "done":
            pending = [p for p in pending if action_id(p) != aid]
            done.add(aid)
        else:
            for t in a.get("requires", []):
                belief["believed_tools"][t] = bool(c_ext["tools"].get(t, False))   # the failure corrects the belief
        last_type = a["type"]
        # a change scheduled at step i + 1 takes effect at the boundary after step i, BEFORE
        # the stop decision, so the hazard and the next policy see the same context (and the
        # state at a cut placed there, which applies the change, matches the generator)
        for (step_c, kind_c) in changes:
            if i + 1 == step_c:
                c_ext, belief = _apply_change(c_ext, belief, kind_c)
        c_m = maker_context(c_ext, belief, law)
        # satisfaction is judged on the goal that governed the step just taken
        goal_pending = [p for p in pending if p["goal_owner"] == gname]
        progress = len(done) / max(1, total_n)
        p_stop, terms = stop_hazard(not goal_pending, progress, i + 1, law, c_m)
        p_stop = 1.0 / (1.0 + math.exp(-(math.log(p_stop / (1 - p_stop)) + stop_shift)))
        steps[-1]["p_stop"] = p_stop
        steps[-1]["stop_terms"] = terms
        if forced_prefix and i < len(forced_prefix) - 1:
            continue
        if pending and r.random() < p_stop:
            stopped_at = i
            btype = boundary_type(terms)
            stop_kind = "hazard"
            break
    return {"steps": steps, "stopped_at": stopped_at, "boundary_type": btype, "change_step": cs,
            "changes": changes, "final_belief": belief, "final_context": c_ext,
            "stop_kind": stop_kind, "stop_shift": stop_shift}


# ── the cut and the hidden targets ────────────────────────────────────────────────────

def _changes_of(traj: dict, c_ext: dict) -> list:
    return [tuple(c) for c in traj.get("changes") or [(traj["change_step"], c_ext["scheduled_change"])]]


# The cut design (the stop repair, 2026-09-02). A boundary c means "c steps visible"; the
# maker stops AT boundary c when the trajectory ended after step c-1 by the hazard draw.
# The old rule always left two future steps, so the stop truth was never true. Now the
# constructor walks the boundaries 3..n in order and selects boundary c with a probability
# that depends on the PREFIX only (base rate, ramped with depth, boosted right after the
# first diagnostic step); the terminal boundary of a hazard-stopped trajectory is selected
# with its own higher rate. Because selection never reads the outcome at the selected
# boundary, P(stop | selected, prefix) is exactly the generator's hazard, so the oracle stays
# the Bayes ceiling; the terminal oversampling is undone at scoring by the recorded weight
# q(c) / Q_TERMINAL on stop rows (scoring.prospective writes it; engine_supplied._score_key
# applies it to stop_ls), so every stop contrast estimates the natural-boundary expectation.
# Two modes, chosen by a prefix-free coin: the WALK (probability 1 - terminal_mode) selects
# boundary c with q(c) as it passes, the terminal boundary included when the trajectory
# ended there by the hazard; the TERMINAL mode (probability terminal_mode) selects the
# terminal boundary outright (or nothing). The natural design is the walk alone. With
# S(c) the walk's survival to c, the sampled stop-row mass at c is h(c) [pi + (1-pi) S q]
# against the natural h(c) S q, and the continue-row mass (1-h) (1-pi) S q against
# (1-h) S q; the weights below restore the natural design exactly (continue rows 1, stop
# rows (1-pi) S q / (pi + (1-pi) S q)), so every stop contrast estimates the natural
# expectation with the generator's hazard as its exact ceiling.
CUT_DESIGN = {"base": 0.10, "ramp": 0.02, "max": 0.30, "diag": 0.45, "terminal_mode": 0.22}


def _cut_rate(c: int, first_diag: int | None) -> float:
    if first_diag is not None and c - 1 == first_diag:
        return CUT_DESIGN["diag"]
    return min(CUT_DESIGN["max"], CUT_DESIGN["base"] + CUT_DESIGN["ramp"] * (c - 3))


def _stop_weight(c: int, first_diag: int | None) -> float:
    pi = CUT_DESIGN["terminal_mode"]
    s = 1.0
    for k in range(3, c):
        s *= 1.0 - _cut_rate(k, first_diag)
    q = _cut_rate(c, first_diag)
    return (1.0 - pi) * s * q / (pi + (1.0 - pi) * s * q)


def _choose_cut(traj: dict, lid: str) -> tuple[int | None, float | None]:
    """Returns (cut, stop_weight) or (None, None) when the design selects nothing."""
    steps = traj["steps"]
    n = len(steps)
    if n < 4:
        return None, None
    r = _rng(lid, "cut")
    terminal_ok = traj.get("stop_kind") == "hazard" and traj.get("stopped_at") == n - 1
    first_diag = next((s["i"] for s in steps if s["outcome"] == "failed" or s["type"] in ("cite", "consult", "restructure", "probe")), None)
    if r.random() < CUT_DESIGN["terminal_mode"]:
        if not terminal_ok:
            return None, None
        return n, _stop_weight(n, first_diag)
    for c in range(3, n + 1):
        if c == n and not terminal_ok:
            break
        if r.random() < _cut_rate(c, first_diag):
            return c, (_stop_weight(c, first_diag) if c == n else 1.0)
    return None, None


def _state_at(state: dict, traj: dict, cut: int, inventory: list[dict]) -> dict:
    """The state as it stands at the cut: context after any scheduled change, belief after
    any visible failure, the goal then governing, and the subjective option set."""
    c_ext = copy.deepcopy(state["external_context"])
    belief = copy.deepcopy(state["belief_state"])
    law = state["expertise_law"]
    pending = [dict(a) for a in inventory]
    gname = state["proximal_goal"]["name_ref"]
    for s in traj["steps"][:cut]:
        for (step_c, kind_c) in _changes_of(traj, c_ext):
            if s["i"] == step_c:
                c_ext, belief = _apply_change(c_ext, belief, kind_c)
        gname = LAW.next_goal(gname, pending, list(GOALS))
        aid = f"{s['type']}:{s['section']}:{s['slot']}"
        if s["outcome"] == "done":
            pending = [p for p in pending if action_id(p) != aid]
        else:
            a = next(x for x in inventory if action_id(x) == aid)
            for t in a.get("requires", []):
                belief["believed_tools"][t] = bool(c_ext["tools"].get(t, False))
    for (step_c, kind_c) in _changes_of(traj, c_ext):
        if cut == step_c:
            c_ext, belief = _apply_change(c_ext, belief, kind_c)
    goal_last = gname                         # the goal that governed step cut-1 (the stop is judged on it)
    gname = LAW.next_goal(gname, pending, list(GOALS))
    c_m = maker_context(c_ext, belief, law)
    a_tilde = subjective_options(pending, c_m, belief, law)
    return {"external_context": c_ext, "belief_state": belief, "expertise_law": law, "maker_context": c_m,
            "subjective_action_space": [action_id(a) for a in a_tilde], "proximal_goal": _goal(gname),
            "goal_last": goal_last,
            "history_residue": state["history_residue"], "persistent_tendency": state["persistent_tendency"],
            "pending": pending, "names": state["names"]}


def _predictive(st: dict, pending: list[dict], sections: list[str], last_type: str | None, step: int,
                n_done: int, total_n: int, stop_shift: float = 0.0) -> dict:
    opts = [a for a in pending if action_id(a) in st["subjective_action_space"]]
    pol = policy(opts, st["proximal_goal"], st["expertise_law"], st["history_residue"], st["maker_context"],
                 sections, last_type, step)
    nxt = {action_id(a): pol.get(action_id(a), 0.0) for a in pending}
    type_d = {t: 0.0 for t in ACTION_TYPES}
    sec_d = {s: 0.0 for s in sections}
    for a in pending:
        type_d[a["type"]] += nxt[action_id(a)]
        sec_d[a["section"]] += nxt[action_id(a)]
    # the stop at this boundary is judged on the goal that governed the last visible step
    # (exactly the generator's rule); the policy above already runs on the evolved goal
    g_last = st.get("goal_last") or st["proximal_goal"]["name_ref"]
    goal_pending = [p for p in pending if p["goal_owner"] == g_last]
    p_stop, terms = stop_hazard(not goal_pending, n_done / max(1, total_n), step, st["expertise_law"], st["maker_context"])
    if stop_shift:
        p_stop = 1.0 / (1.0 + math.exp(-(math.log(p_stop / (1 - p_stop)) + stop_shift)))
    return {"next_action": nxt, "next_type": type_d, "next_section": sec_d, "p_stop": p_stop,
            "stop_terms": terms, "boundary_type": boundary_type(terms)}


def _prefix_ll(state: dict, traj: dict, cut: int, inventory: list[dict], sections: list[str]) -> float:
    """Exact log likelihood of the visible prefix under a (possibly hypothetical) state,
    replayed with that state's own beliefs and goal evolution."""
    c_ext = copy.deepcopy(state["external_context"])
    belief = copy.deepcopy(state["belief_state"])
    law = state["expertise_law"]
    residue = state["history_residue"]
    pending = [dict(a) for a in inventory]
    gname = state["proximal_goal"]["name_ref"]
    total = 0.0
    last_type = None
    for s in traj["steps"][:cut]:
        i = s["i"]
        for (step_c, kind_c) in _changes_of(traj, c_ext):
            if i == step_c:
                c_ext, belief = _apply_change(c_ext, belief, kind_c)
        c_m = maker_context(c_ext, belief, law)
        gname = LAW.next_goal(gname, pending, list(GOALS))
        opts = subjective_options(pending, c_m, belief, law)
        pol = policy(opts, _goal(gname), law, residue, c_m, sections, last_type, i)
        aid = f"{s['type']}:{s['section']}:{s['slot']}"
        total += math.log(max(pol.get(aid, 0.0), 1e-9))
        if s["outcome"] == "done":
            pending = [p for p in pending if action_id(p) != aid]
        else:
            a = next(x for x in inventory if action_id(x) == aid)
            for t in a.get("requires", []):
                belief["believed_tools"][t] = bool(c_ext["tools"].get(t, False))
        last_type = s["type"]
    return total


def grid_states(lid: str, doc: dict, inventory: list[dict], tendency: str) -> dict[str, dict]:
    """Every configuration of the factor grid (goal x law x belief x residue) with the
    world's own context: the known-law selector's candidate set and the equivalence-class
    ruler's enumeration."""
    out = {}
    for g in GOALS:
        for ln in LAW_NAMES:
            for b in BELIEFS:
                for h in RESIDUES:
                    out[f"{g}|{ln}|{b}|{h}"] = make_state(lid, doc, inventory, g, ln, b, h, tendency)
    return out


def oracle_posterior(world: dict, upto: int | None = None) -> dict:
    """Exact posterior over the grid from the prefix likelihoods (uniform prior)."""
    cut = world["cut"] if upto is None else upto
    sections = [s["name"] for s in world["doc"]["sections"]]
    lls = {k: _prefix_ll(st, world["trajectory"], cut, world["inventory"], sections)
           for k, st in grid_states(world["lid"], world["doc"], world["inventory"], world["state"]["names"]["tendency"]).items()}
    mx = max(lls.values())
    ex = {k: math.exp(v - mx) for k, v in lls.items()}
    z = sum(ex.values())
    return {k: v / z for k, v in ex.items()}


def _equivalence_class(world: dict) -> list[str]:
    """Configurations that match the truth's prefix likelihood AND its predictive
    distribution at the cut within 1e-6 (exactly unresolved by the visible evidence)."""
    truth = world["state_at_cut"]
    sections = [s["name"] for s in world["doc"]["sections"]]
    cut = world["cut"]
    traj = world["trajectory"]
    t_ll = _prefix_ll(world["state"], traj, cut, world["inventory"], sections)
    t_pred = world["oracle"]["next_action"]
    out = []
    for key, st in grid_states(world["lid"], world["doc"], world["inventory"], world["state"]["names"]["tendency"]).items():
        ll = _prefix_ll(st, traj, cut, world["inventory"], sections)
        if abs(ll - t_ll) > 1e-6:
            continue
        sac = _state_at(st, traj, cut, world["inventory"])
        pred = _predictive(sac, truth["pending"], sections, traj["steps"][cut - 1]["type"], cut,
                           sum(1 for s in traj["steps"][:cut] if s["outcome"] == "done"), len(world["inventory"]))
        if 0.5 * sum(abs(pred["next_action"].get(k, 0.0) - t_pred.get(k, 0.0)) for k in set(pred["next_action"]) | set(t_pred)) < 1e-6:
            out.append(key)
    return sorted(out)


def _changed_context_choice(world: dict, kind: str) -> dict:
    """The changed-context counterfactual computed from the same law: apply the change at
    the cut and read the policy (P07/K06's target)."""
    st = copy.deepcopy(world["state_at_cut"])
    c2, b2 = _apply_change(st["external_context"], st["belief_state"], kind)
    st["external_context"], st["belief_state"] = c2, b2
    st["maker_context"] = maker_context(c2, b2, st["expertise_law"])
    a_tilde = subjective_options(st["pending"], st["maker_context"], b2, st["expertise_law"])
    st["subjective_action_space"] = [action_id(a) for a in a_tilde]
    sections = [s["name"] for s in world["doc"]["sections"]]
    cut = world["cut"]
    pred = _predictive(st, st["pending"], sections, world["trajectory"]["steps"][cut - 1]["type"], cut,
                       sum(1 for s in world["trajectory"]["steps"][:cut] if s["outcome"] == "done"), len(world["inventory"]))
    r = _rng(world["lid"], f"cc|{kind}")
    u, acc, choice = r.random(), 0.0, None
    for k, p in pred["next_action"].items():
        acc += p
        if u <= acc:
            choice = k
            break
    return {"change": kind, "dist": pred["next_action"], "choice": choice or max(pred["next_action"], key=pred["next_action"].get)}


def _invalidation_response(world: dict) -> dict:
    """P08: after a consulted source is invalidated, the maker's response distribution
    (correct, retain, rewrite) from the same law: correction follows fix skill and the
    audit utility, rewrite follows revise utility and restructure feasibility, retention is
    the residual."""
    st = world["state_at_cut"]
    dist = LAW.invalidation_dist(st["expertise_law"], st["proximal_goal"]["utility"], st["maker_context"])   # the ONE formula (law.py)
    r = _rng(world["lid"], "inval")
    u, acc, choice = r.random(), 0.0, "retain"
    for k, p in dist.items():
        acc += p
        if u <= acc:
            choice = k
            break
    return {"dist": dist, "choice": choice}


def _finish_world(world: dict, cut: int, weight: float) -> dict:
    """The hidden targets, the oracle, and the equivalence class of a world whose
    trajectory is fixed: shared by make_world, factor_twin, and mutate so every construct
    reads the same rule. At a terminal cut (the maker stopped by the hazard after step
    cut-1) there is no next action and the stop truth is true; a construct that reaches
    the cut with neither a next step nor a hazard stop is degenerate."""
    traj = world["trajectory"]
    state = world["state"]
    inventory = world["inventory"]
    steps = traj["steps"]
    world["cut"] = cut
    world["cut_weight"] = weight
    sections = [s["name"] for s in world["doc"]["sections"]]
    st = _state_at(state, traj, cut, inventory)
    world["state_at_cut"] = st
    n_done = sum(1 for s in steps[:cut] if s["outcome"] == "done")
    world["oracle"] = _predictive(st, st["pending"], sections, steps[cut - 1]["type"], cut, n_done, len(inventory),
                                  stop_shift=float(traj.get("stop_shift") or 0.0))
    nxt = steps[cut] if cut < len(steps) else None
    tail = steps[cut:]
    stop_next = bool(traj.get("stop_kind") == "hazard" and traj["stopped_at"] == cut - 1)
    nid = f"{nxt['type']}:{nxt['section']}:{nxt['slot']}" if nxt else None
    alt = sorted(((k, p) for k, p in world["oracle"]["next_action"].items() if k != nid), key=lambda kv: -kv[1]) if nxt else []
    world["hidden"] = {
        "next_action": nid,
        "next_type": nxt["type"] if nxt else None, "next_section": nxt["section"] if nxt else None,
        "next_slot": nxt["slot"] if nxt else None,
        "stop_next": stop_next, "stopped_at": traj["stopped_at"], "boundary_type": traj["boundary_type"] if stop_next else "none",
        "stop_weight": weight,
        "tail": [{"type": s["type"], "section": s["section"], "slot": s["slot"], "outcome": s["outcome"]} for s in tail],
        "tail_stop": [bool(traj["stopped_at"] == s["i"]) for s in tail],
        "rejected_alternative": alt[0][0] if alt else None,
        "changed_context": _changed_context_choice(world, query_change(world)),
        "invalidation": _invalidation_response(world),
        "subjective_ids": list(st["subjective_action_space"]),
        "unavailable_ids": [action_id(a) for a in st["pending"] if action_id(a) not in st["subjective_action_space"]],
    }
    world["hidden"]["equivalence_class"] = _equivalence_class(world)
    if nxt is None and not stop_next:
        world["degenerate"] = "no next action and no hazard stop at the cut"
    return world


def make_world(lid: str, domain: str, goal: str | None = None, law_name: str | None = None,
               belief: str | None = None, residue: str | None = None, tendency: str | None = None,
               forced_cext: dict | None = None, salt: str = "traj", law: str | None = None) -> dict:
    """One world: factors drawn from the lineage id unless forced; simulated; cut; hidden
    targets; oracle; equivalence class. A world too short for a cut or under the oracle
    gap floor is returned with `degenerate` set and its cause (never scored)."""
    r = _rng(lid, "factors")
    doc = _doc_plan(lid, domain)
    inventory = _inventory(lid, doc)
    goal = goal or GOALS[r.randrange(len(GOALS))]
    law_name = law_name or law or LAW_NAMES[r.randrange(len(LAW_NAMES))]
    belief = belief or BELIEFS[r.randrange(len(BELIEFS))]
    residue = residue or RESIDUES[r.randrange(len(RESIDUES))]
    tendency = tendency or TENDENCIES[r.randrange(2)]
    state = make_state(lid, doc, inventory, goal, law_name, belief, residue, tendency, forced_cext)
    traj = simulate(lid, doc, inventory, state, salt=salt)
    world = {"lid": lid, "domain": domain, "doc": doc, "inventory": inventory, "state": state,
             "trajectory": traj, "degenerate": None}
    cut, weight = _choose_cut(traj, lid)
    if cut is None:
        world["degenerate"] = "the boundary walk selected no cut"
        return world
    return _finish_world(world, cut, weight)


# ── twins and mutations ───────────────────────────────────────────────────────────────

def factor_twin(world: dict, factor: str, value: str) -> dict:
    """A world identical in document, inventory, context, and VISIBLE PREFIX, with one
    factor swapped; its own tail simulated under the swapped state. Returns None when the
    prefix is impossible under the swap (the twin cannot collide)."""
    names = dict(world["state"]["names"])
    names[factor] = value
    lid = f"{world['lid']}|twin-{factor}-{value}"
    state = make_state(world["lid"], world["doc"], world["inventory"], names["goal"], names["law"],
                       names["belief"], names["residue"], names["tendency"])
    prefix = [{"type": s["type"], "section": s["section"], "slot": s["slot"]} for s in world["trajectory"]["steps"][:world["cut"]]]
    traj = simulate(world["lid"], world["doc"], world["inventory"], state, salt=f"twin|{factor}|{value}",
                    forced_prefix=prefix, change_step=world["trajectory"]["change_step"],
                    changes=world["trajectory"].get("changes"))
    if traj.get("impossible_prefix") or len(traj["steps"]) < world["cut"]:
        return None
    w = {"lid": lid, "domain": world["domain"], "doc": world["doc"], "inventory": world["inventory"],
         "state": state, "trajectory": traj, "degenerate": None, "twin_of": world["lid"],
         "swapped": {factor: value}}
    w = _finish_world(w, world["cut"], float(world.get("cut_weight") or 1.0))
    if w["degenerate"]:
        return None
    sections = [s["name"] for s in world["doc"]["sections"]]
    w["prefix_collides"] = abs(_prefix_ll(state, traj, w["cut"], world["inventory"], sections)
                               - _prefix_ll(world["state"], world["trajectory"], world["cut"], world["inventory"], sections)) < 1e-9
    return w


def mutate(world: dict, kind: str, salt: int = 1) -> dict:
    """I05-I07: the same visible prefix with the hidden future replaced. `tail`: the tail
    re-drawn; `stop`: the stop parameters shifted and the stop outcome re-drawn; `event`:
    the future context change and the invalidation replaced. The visible evidence of the
    mutant must be byte-identical to the original's (the constructor asserts it)."""
    prefix = [{"type": s["type"], "section": s["section"], "slot": s["slot"]} for s in world["trajectory"]["steps"][:world["cut"]]]
    kwargs = {"forced_prefix": prefix, "change_step": world["trajectory"]["change_step"],
              "changes": [tuple(c) for c in (world["trajectory"].get("changes") or [])]}
    state = copy.deepcopy(world["state"])
    if kind == "stop":
        kwargs["stop_shift"] = 1.5 * (1 if salt % 2 else -1)
    if kind == "event":
        kinds = ["library_arrives", "library_withdrawn", "deadline_lifted", "deadline_imposed", "audience_changes"]
        cut = world["cut"]
        kept = [(s_, k_) for (s_, k_) in kwargs["changes"] if s_ < cut]
        future = [(s_, k_) for (s_, k_) in kwargs["changes"] if s_ >= cut]
        cur = future[0][1] if future else state["external_context"]["scheduled_change"]
        new_kind = kinds[(kinds.index(cur) + salt) % len(kinds)]
        kwargs["changes"] = kept + [(cut + 1 + (salt % 3), new_kind)]
    traj = simulate(world["lid"], world["doc"], world["inventory"], state, salt=f"mut|{kind}|{salt}", **kwargs)
    w = copy.deepcopy(world)
    w["lid"] = f"{world['lid']}|mut-{kind}-{salt}"
    w["state"] = state
    w["trajectory"] = traj
    w["mutation"] = {"kind": kind, "salt": salt}
    w["degenerate"] = None
    # the hidden targets, the oracle, and the class are RECOMPUTED from the mutant
    # trajectory (the first attempt copied the original's, so the should-break case never
    # broke and I05/I06 landed INSTRUMENT_FAILED on 2026-09-02)
    return _finish_world(w, world["cut"], float(world.get("cut_weight") or 1.0))


# ── rendering: the visible evidence (allowlist) ──────────────────────────────────────

_TYPE_WORDS = {"write": "drafts", "revise": "reworks", "check": "checks", "consult": "consults a source for",
               "cite": "adds a reference to", "restructure": "reorders", "probe": "tries a technique in", "fix": "repairs"}


def artifact_state(world: dict, upto: int) -> dict:
    filled = {}
    for s in world["trajectory"]["steps"][:upto]:
        if s["outcome"] == "done":
            filled.setdefault(s["section"], []).append(f"{s['type']}@{s['slot']}")
    return {"topic": world["doc"]["topic"],
            "sections": [{"name": sec["name"], "slots": list(sec["slots"]), "filled": filled.get(sec["name"], [])}
                         for sec in world["doc"]["sections"]]}


def process_prefix(world: dict, upto: int) -> list[dict]:
    return [{"step": s["i"], "type": s["type"], "section": s["section"], "slot": s["slot"], "outcome": s["outcome"]}
            for s in world["trajectory"]["steps"][:upto]]


def render_prefix_text(prefix: list[dict], render: str, topic: str) -> str:
    if render == "log":
        return "\n".join(f"{p['step']:02d} {p['type']} {p['section']} {p['slot']} {p['outcome']}" for p in prefix)
    lines = [f"The maker is working on {topic}."]
    for p in prefix:
        w = _TYPE_WORDS[p["type"]]
        tail = "" if p["outcome"] == "done" else " but cannot (the attempt fails)"
        lines.append(f"Step {p['step'] + 1}: the maker {w} {p['section']} ({p['slot']}){tail}.")
    return "\n".join(lines)


def brief_text(c_ext: dict) -> dict:
    return {"required_sections": list(c_ext["brief_sections"]), "audience": c_ext["audience"],
            "tools_available": {t: bool(v) for t, v in c_ext["tools"].items()}, "deadline": c_ext["deadline"]}


def factor_executable(name: str, st: dict) -> dict | list:
    v = st[name]
    if name == "proximal_goal":
        g0 = st["names"]["goal"]                                     # the initial goal: the content is its table
        return {"utility": dict(GOAL_UTILITY[g0]), "owner": g0}
    if name == "expertise_law":
        return {k: v[k] for k in ("skill", "feasible_min_skill", "cost", "chain", "fluency", "expected_len", "confidence")}
    if name == "belief_state":
        return {"believed_tools": dict(v["believed_tools"]), "believed_deadline": v["believed_deadline"],
                "believed_checked": list(v["believed_checked"])}
    if name == "external_context":
        # the law's own field names (the solver derives C_m from these); the visible brief
        # is the same content under the reader-facing names (brief_text)
        return {"brief_sections": list(v["brief_sections"]), "audience": v["audience"],
                "tools": {t: bool(x) for t, x in v["tools"].items()}, "deadline": v["deadline"]}
    if name == "maker_context":
        return dict(v)
    if name == "subjective_action_space":
        return list(v)
    if name == "history_residue":
        return {"habit": dict(v.get("habit", {})), "maintained": dict(v["maintained"]) if v.get("maintained") else None}
    raise KeyError(name)


def factor_language(name: str, st: dict) -> str:
    """The natural-language rendering of the same content (K05), length-matched across
    factor values by construction (fixed sentence frames)."""
    v = st[name]
    if name == "proximal_goal":
        order = sorted(GOAL_UTILITY[st["names"]["goal"]].items(), key=lambda kv: -kv[1])
        return (f"Right now the maker is pulled most strongly toward {_TYPE_WORDS[order[0][0]].split()[0]}ing work, "
                f"then toward {_TYPE_WORDS[order[1][0]].split()[0]}ing, and least toward {_TYPE_WORDS[order[-1][0]].split()[0]}ing.")
    if name == "expertise_law":
        strong = sorted(v["skill"].items(), key=lambda kv: -kv[1])[:2]
        weak = sorted(v["skill"].items(), key=lambda kv: kv[1])[:2]
        feas = [t for t, m in v["feasible_min_skill"].items() if v["skill"].get(t, 0) >= m]
        chain = ", ".join(f"after {a} the maker tends to {b}" for a, b in (k.split(">") for k in v["chain"])) or "no fixed sequence habits"
        return (f"The maker is strongest at {strong[0][0]} and {strong[1][0]}, weakest at {weak[0][0]} and {weak[1][0]}; "
                f"of the skilled moves, the maker can carry out {', '.join(feas) or 'none'}; {chain}; "
                f"choices are {'steady' if v['fluency'] < 1.2 else 'erratic'} and an episode usually runs about {int(v['expected_len'])} moves.")
    if name == "belief_state":
        t = v["believed_tools"]
        return (f"The maker believes the library is {'available' if t.get('library') else 'unavailable'} and source access is "
                f"{'available' if t.get('source_access') else 'unavailable'}, believes the deadline is {v['believed_deadline']}, and "
                f"believes {', '.join(v['believed_checked']) if v['believed_checked'] else 'no section'} is already checked.")
    if name == "external_context":
        b = brief_text(v)
        return (f"The brief requires {', '.join(b['required_sections'])}; the audience is {b['audience']}; the library is "
                f"{'available' if b['tools_available']['library'] else 'unavailable'} and source access is "
                f"{'available' if b['tools_available']['source_access'] else 'unavailable'}; the deadline is {b['deadline']}.")
    if name == "maker_context":
        return (f"As the maker sees it, the library is {'usable' if v['perceived_tools']['library'] else 'not usable'}, source access is "
                f"{'usable' if v['perceived_tools']['source_access'] else 'not usable'}, the deadline feels {v['perceived_deadline']}, "
                f"the audience matters {'a lot' if v['audience_weight'] > 0.5 else 'a little' if v['audience_weight'] > 0 else 'not at all'}, "
                f"and {', '.join(v['believed_checked']) if v['believed_checked'] else 'no section'} is taken as already checked.")
    if name == "subjective_action_space":
        return "The moves the maker sees as open right now: " + ", ".join(v) + "."
    if name == "history_residue":
        h = v.get("habit", {})
        m = v.get("maintained")
        hab = ", ".join(f"a standing habit of {t}" for t in h) or "no standing habit"
        return f"The maker carries {hab} and {'a held intention to ' + m['option'] + ' when cued at step ' + str(m['cue_step'] + 1) if m else 'no held intention'}."
    raise KeyError(name)


def demonstrations(world: dict, n: int = 2, render: str = "log") -> list[dict]:
    """Prior episodes under the SAME expertise law on other document plans with other
    goals and accurate beliefs (K14/R09: the law is what transfers)."""
    out = []
    names = world["state"]["names"]
    for k in range(n):
        lid = f"{world['lid']}|demo{k}"
        doc = _doc_plan(lid, world["domain"])
        inv = _inventory(lid, doc)
        g = GOALS[(GOALS.index(names["goal"]) + 1 + k) % len(GOALS)]
        st = make_state(lid, doc, inv, g, names["law"], "accurate", "none", names["tendency"])
        traj = simulate(lid, doc, inv, st, salt="demo")
        pre = [{"step": s["i"], "type": s["type"], "section": s["section"], "slot": s["slot"], "outcome": s["outcome"]} for s in traj["steps"]]
        out.append({"episode_ref": f"prior-{k + 1}", "topic": doc["topic"], "sections": [s["name"] for s in doc["sections"]],
                    "events": pre, "text": render_prefix_text(pre, render, doc["topic"])})
    return out


def candidate_laws(world: dict, relabel_seed: int = 0) -> list[dict]:
    """The bounded executable law set for known-law selection (KL), under OPAQUE refs in a
    seeded order (X13 relabels; behavior, not tags, must drive selection)."""
    r = _rng(world["lid"], f"laws|{relabel_seed}")
    names = list(LAW_NAMES)
    r.shuffle(names)
    return [{"law_ref": f"law_{chr(97 + i)}", "law": factor_executable("expertise_law", {"expertise_law": LAWS[n]})}
            for i, n in enumerate(names)]


def candidate_law_truth(world: dict, relabel_seed: int = 0) -> str:
    r = _rng(world["lid"], f"laws|{relabel_seed}")
    names = list(LAW_NAMES)
    r.shuffle(names)
    return f"law_{chr(97 + names.index(world['state']['names']['law']))}"


def query_change(world: dict) -> str:
    """The counterfactual the query asks about, a function of the VISIBLE context at the
    cut (never of the hidden scheduled change): lift a tight deadline, else bring the
    library, else change the audience."""
    c = world["state_at_cut"]["external_context"]
    if c["deadline"] == "tight":
        return "deadline_lifted"
    if not c["tools"].get("library"):
        return "library_arrives"
    return "audience_changes"


def query_block(world: dict) -> dict:
    """The target vocabulary the reader answers over: the live objective option ids at the
    cut (the reader must learn which are subjectively unavailable), the type vocabulary,
    the section list, the stop question, the changed-context option set (under the change
    the condition names), the invalidation responses, and the boundary types."""
    st = world["state_at_cut"]
    return {"next_action_options": [action_id(a) for a in st["pending"]],
            "type_vocabulary": list(ACTION_TYPES),
            "sections": [s["name"] for s in world["doc"]["sections"]],
            "stop": ["stop", "continue"],
            "context_change": query_change(world),
            "invalidation_responses": ["correct", "retain", "rewrite"],
            "boundary_types": ["satisfaction", "deadline", "fatigue", "equivalent"]}


def visible_evidence(world: dict, condition: dict) -> dict:
    """The VisibleEvidenceV1 for one world under one condition. condition keys:
    supplied (list of factor names), form ('executable'|'language'), regime, render,
    with_options (bool), candidate_laws (bool), demos (int), unit_ref (opaque)."""
    cut = world["cut"]
    prefix = process_prefix(world, cut)
    render = condition.get("render", "prose")
    ev = {"version": EVIDENCE_VERSION,
          "unit_ref": condition.get("unit_ref", "u"),
          "condition_ref": condition.get("condition_ref", "c"),
          "domain": world["domain"],
          "artifact_state": artifact_state(world, cut),
          "process_prefix": prefix,
          "query": query_block(world),
          "regime": condition.get("regime", "cold"),
          "render": render}
    ev["artifact_state"]["prefix_text"] = render_prefix_text(prefix, render, world["doc"]["topic"])
    if condition.get("with_brief", True):
        ev["brief"] = brief_text(world["state_at_cut"]["external_context"])
    if condition.get("with_options", True):
        st = world["state_at_cut"]
        ev["objective_options"] = {"initial": [{k: a[k] for k in ("type", "section", "slot", "requires", "goal_owner")} for a in world["inventory"]],
                                   "at_cut": [{k: a[k] for k in ("type", "section", "slot", "requires", "goal_owner")} for a in st["pending"]]}
    supplied = list(condition.get("supplied") or [])
    if supplied:
        form = condition.get("form", "executable")
        st = world["state_at_cut"]
        sf = {}
        for name in supplied:
            sf[name] = factor_executable(name, st) if form == "executable" else factor_language(name, st)
        ev["supplied_factors"] = {"form": form, "factors": sf}
    if condition.get("candidate_laws"):
        ev["candidate_laws"] = candidate_laws(world, condition.get("relabel_seed", 0))
    if condition.get("demos"):
        ev["demonstrations"] = demonstrations(world, int(condition["demos"]), render)
    if condition.get("regime") == "domain_expert":
        ev.setdefault("supplied_factors", {"form": condition.get("form", "executable"), "factors": {}})
        ev["supplied_factors"]["generic_law"] = domain_generic_law()
    return ev


def oracle_bundle(world: dict, condition: dict) -> dict:
    """OracleBundleV1: everything the scorer needs and the reader must never see."""
    return {"version": "OracleBundleV1", "lid": world["lid"], "cut": world["cut"], "hidden": world["hidden"],
            "oracle": world["oracle"], "state_names": world["state"]["names"], "state_at_cut": {
                k: world["state_at_cut"][k] for k in ("external_context", "belief_state", "expertise_law", "maker_context",
                                                       "subjective_action_space", "proximal_goal", "history_residue")},
            "condition": dict(condition), "n_options": len(world["state_at_cut"]["pending"])}


# ── self-tests (the guard suite calls these) ─────────────────────────────────────────

def _selftest() -> list[str]:
    fails = []
    w = next((x for x in (make_world(f"S7T|essay|s0|w{i:05d}|pilot", "essay") for i in range(1, 16))
              if not x["degenerate"] and x["hidden"]["next_action"] is not None), None)
    if w is None:
        return ["no live self-test world with a next action in fifteen lineages"]
    # 1. exactness: the per-step likelihoods are probabilities and the oracle sums to one
    if abs(sum(w["oracle"]["next_action"].values()) - 1.0) > 1e-9:
        fails.append("oracle next-action distribution does not sum to one")
    if any(not 0 < s["lik"] <= 1 for s in w["trajectory"]["steps"]):
        fails.append("a step likelihood is outside (0, 1]")
    # 2. the supplied complete state executed by the solver reproduces the oracle
    cond = {"supplied": list(LAW.__dict__.get("FACTOR_ORDER", ("external_context", "belief_state", "expertise_law",
                                                               "maker_context", "subjective_action_space", "proximal_goal", "history_residue"))),
            "form": "executable", "unit_ref": "u1"}
    ev = visible_evidence(w, cond)
    sf = dict(ev["supplied_factors"]["factors"])
    ex = LAW.execute(sf, ev)
    diff = max(abs(ex["next_action"].get(k, 0.0) - w["oracle"]["next_action"].get(k, 0.0)) for k in w["oracle"]["next_action"])
    if diff > 1e-9 or abs(ex["p_stop"] - w["oracle"]["p_stop"]) > 1e-9:
        fails.append(f"solver on supplied state differs from the oracle by {diff:.2e}")
    cc = LAW.execute_changed(sf, ev, ev["query"]["context_change"])["next_action"]
    tcc = w["hidden"]["changed_context"]["dist"]
    if max(abs(cc.get(k, 0.0) - tcc.get(k, 0.0)) for k in set(cc) | set(tcc)) > 1e-9:
        fails.append("the capsule's changed-context execution differs from the oracle's")
    inv, tinv = ex["invalidation"], w["hidden"]["invalidation"]["dist"]
    if max(abs(inv[k] - tinv[k]) for k in tinv) > 1e-9:
        fails.append("the capsule's invalidation response differs from the oracle's")
    # 3. unavailable options get zero mass
    if any(w["oracle"]["next_action"].get(k, 0.0) > 0 for k in w["hidden"]["unavailable_ids"]):
        fails.append("a subjectively unavailable option carries mass")
    # 4. target hiding: no factor name in the evidence
    import re
    text = str(ev)
    for word in list(LAW_NAMES) + list(BELIEFS) + list(RESIDUES) + ["stop_next", "tail", "stopped_at", "equivalence_class"]:
        if word != "none" and re.search(r"\b" + re.escape(word) + r"\b", text):
            fails.append(f"visible evidence contains {word!r}")
    # 5. mutations leave the visible evidence byte-identical
    for kind in ("tail", "stop", "event"):
        m = mutate(w, kind, 1)
        ev2 = visible_evidence(m, cond)
        if str(ev2) != str(ev):
            fails.append(f"{kind} mutation changed the visible evidence")
    # 6. a belief twin collides on the prefix
    alt = next(b for b in BELIEFS if b != w["state"]["names"]["belief"])
    t = factor_twin(w, "belief", alt)
    if t is None:
        fails.append("belief twin impossible")
    # 7. the stop truth exists, and at a terminal cut the oracle's hazard is exactly the
    #    hazard the generator drew the stop from
    stops = 0
    seen = 0
    for i in range(3, 80):
        ww = make_world(f"S7T|essay|s0|w{i:05d}|pilot", "essay")
        if ww["degenerate"]:
            continue
        seen += 1
        if ww["hidden"]["stop_next"]:
            stops += 1
            drawn = ww["trajectory"]["steps"][ww["cut"] - 1]["p_stop"]
            if abs(drawn - ww["oracle"]["p_stop"]) > 1e-9:
                fails.append(f"oracle hazard {ww['oracle']['p_stop']:.4f} differs from the generator's {drawn:.4f} at a terminal cut")
                break
            if ww["hidden"]["next_action"] is not None:
                fails.append("a terminal cut carries a next action")
                break
    if seen and stops == 0:
        fails.append("no world in 77 carries a true stop at its cut")
    # 8. a mutant's hidden targets differ from the original's on some world
    differs = 0
    for i in range(3, 40):
        ww = make_world(f"S7T|essay|s0|w{i:05d}|pilot", "essay")
        if ww["degenerate"]:
            continue
        m = mutate(ww, "tail", 1)
        if m["hidden"]["next_action"] != ww["hidden"]["next_action"] or m["hidden"]["tail"] != ww["hidden"]["tail"] or m["hidden"]["stop_next"] != ww["hidden"]["stop_next"]:
            differs += 1
    if differs == 0:
        fails.append("no tail mutant differs from its original in 37 worlds")
    return fails


if __name__ == "__main__":
    f = _selftest()
    print("worlds self-tests:", "ALL OK" if not f else f)
    sys.exit(1 if f else 0)
