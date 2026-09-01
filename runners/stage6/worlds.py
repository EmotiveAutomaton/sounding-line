"""Stage 6 known-answer process worlds (brief §5.1, §1.3-§1.5): a maker works through a
document episode; every latent is explicit, every action likelihood is exact, and the
hidden targets (the next edit, the stopping decision, a changed-context choice) are draws
from the world's own policy, never annotations.

THE CHASSIS. A document of sections and slots defines a TARGET ACTION MULTISET (the writes
and revisions that produce the final artifact). A maker is an ORDER POLICY over the pending
set: at each step the scores of the pending actions are a declared function of the maker's
latents (goals, controller, habits, expertise, selection history, standing value, foraging
disposition) and the softmax over them is the exact likelihood of the observed order. The
controllers of §1.3 differ ONLY in how the foreground goal evolves and which residue terms
enter the scores, so every controller produces the SAME final artifact and the SAME
aggregate goal counts (C02 is true by construction), and the discriminating evidence is the
order: responses to planted interruptions, rereads, surprises, contradictions, cue events,
and the stopping opportunities. Exact posteriors come from enumerating the track's latent
grid and multiplying observed-step likelihoods; equifinal pairs are symmetry-constructed;
the oracle realization is the true configuration's own predictive distributions.

DESIGN CHECK (2026-08-30)
lessons read: LESSONS §3 (validate the ruler on known answers first: the self-tests below
  run at import in the guard suite; known-answer existence checked at construction; truth
  marginals vary within every cell; a counterfactual question is counterfactual in every
  cell; blind floors follow the truth's label marginal), §4 (no human labels; the worlds
  carry their own ground truth), CONTROLS (construction beats ablation).
gates and bands (enforced here or in I03/C01/A01/V01/F01):
  - identity: every world's construction enumerates from its lineage id; duplicates fail I03.
  - exactness: per-step likelihoods are softmax over the pending set and sum to one; the
    oracle posterior is the normalized product over the grid (self-test 1).
  - endpoint match (C02): all four controllers share the final document and per-goal action
    counts (self-test 2); the alternative (an endpoint leak) fails C02, never a reader.
  - separability with surface matching (C01/F01/V01): the oracle separates the planted
    generator from the order alone while cheap surface statistics sit at their floor
    (self-tests 3-5); a generator the oracle cannot separate closes its cards as VOID.
  - target hiding: renderers never print goal, controller, value, or foraging names; the
    hidden tail, the stop step, and the changed-context choice appear in no rendered
    string (I04 plants canaries to prove the check can fail).
bands: none here; the engines' verdict bands are exhaustive and stated there.
"""

from __future__ import annotations

import math
import random
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from runners.s3_lib import hash_stable                                             # noqa: E402
from soundingline.stage6 import maker_state                                        # noqa: E402

DOMAINS = ("essay", "workshop_doc")
SURFACE_FAMILIES = ("prose", "log")
MAKER_FAMILIES = ("steady", "erratic")            # policy temperature families (§5.1)
CONTROLLERS = ("strict_switch", "maintained", "focal_habit", "concurrent")
FORAGE = ("explore", "error", "habit_misuse", "hidden_goal")
VALUES = ("accuracy", "prestige")
GOALS = ("produce", "tighten", "audit", "attribute")   # goal names never appear in renderings or action types
EDIT_TYPES = ("write", "revise", "check", "consult", "cite", "probe", "fix")
TEMPERATURE = {"steady": 1.0, "erratic": 1.6}

# goal-specific utilities per action type (declared constants; the score chassis)
GOAL_UTIL = {
    "produce":  {"write": 2.2, "revise": 0.2, "check": -0.6, "consult": 0.1, "cite": -0.2, "probe": 0.0, "fix": 0.4},
    "tighten": {"write": -0.4, "revise": 2.0, "check": 0.4, "consult": -0.2, "cite": 0.0, "probe": 0.1, "fix": 0.6},
    "audit": {"write": -0.8, "revise": 0.3, "check": 2.1, "consult": 1.2, "cite": 0.2, "probe": 0.3, "fix": 1.4},
    "attribute": {"write": -0.5, "revise": 0.0, "check": 0.2, "consult": 0.8, "cite": 2.3, "probe": 0.0, "fix": 0.2},
}
READING_ORDER_BONUS = 0.5       # earlier sections slightly preferred (the position prior is live)
SWITCH_COST = 1.4               # strict_switch pays it; concurrent does not
HABIT_WEIGHT = 1.5              # focal_habit's residue term
CUE_BONUS = 6.0                 # maintained: a cued dormant intention takes the step
SURPRISE_PRECISION = 1.8        # C09: the precision variant sharpens within-goal scores
STOP_BASE = -2.2                # stop hazard intercept (sigmoid)
STOP_PROGRESS = 3.6             # hazard slope on progress fraction


def _rng(lid: str, salt: str = "") -> random.Random:
    return random.Random(hash_stable(f"{lid}|{salt}"))


def _widx(lid: str) -> int:
    for part in lid.split("|"):
        if part.startswith("w") and part[1:].isdigit():
            return int(part[1:])
    return hash_stable(lid + "|w") % 4096


# ── the document and the target multiset ──────────────────────────────────────────────

def _doc_plan(lid: str, domain: str) -> dict:
    r = _rng(lid, "doc")
    n_sec = 3 + r.randrange(2)                                  # 3-4 sections
    sections = []
    for s in range(n_sec):
        n_slots = 2 + r.randrange(2)                            # 2-3 slots
        sections.append({"name": f"sec{s + 1}", "slots": [f"s{s + 1}.{k + 1}" for k in range(n_slots)]})
    topic = ["the kiln schedule", "the flood notice", "the survey method", "the glaze recipe",
             "the archive index", "the delivery route"][r.randrange(6)]
    return {"domain": domain, "topic": topic, "sections": sections}


def _target_actions(lid: str, doc: dict) -> list[dict]:
    """The fixed multiset every controller realizes: one write per slot, a revision for
    about half the slots, one check per section, one consult, one cite. Goal ownership is
    fixed per action (write->draft, revise->polish, check/fix->verify, cite/consult->cite
    owner varies), so aggregate per-goal counts are controller-invariant."""
    r = _rng(lid, "target")
    acts = []
    for sec in doc["sections"]:
        for slot in sec["slots"]:
            acts.append({"type": "write", "section": sec["name"], "slot": slot, "goal": "produce"})
    slots = [(sec["name"], slot) for sec in doc["sections"] for slot in sec["slots"]]
    for sec_name, slot in r.sample(slots, max(2, len(slots) // 2)):
        acts.append({"type": "revise", "section": sec_name, "slot": slot, "goal": "tighten"})
    for sec in doc["sections"]:
        acts.append({"type": "check", "section": sec["name"], "slot": sec["slots"][0], "goal": "audit"})
    acts.append({"type": "consult", "section": doc["sections"][0]["name"], "slot": "src", "goal": "audit"})
    acts.append({"type": "cite", "section": doc["sections"][-1]["name"], "slot": "ref", "goal": "attribute"})
    return acts


def _aid(a: dict) -> str:
    return f"{a['type']}:{a['section']}:{a['slot']}"


# ── the order policy (exact) ──────────────────────────────────────────────────────────

def _available(pending: list[dict], done: set) -> list[dict]:
    """write before revise/check on the same slot; a check on a technique slot (the
    foraging outcome read) waits until no probe is pending — an outcome cannot be read
    before the act that produces it; everything else free."""
    out = []
    for a in pending:
        if a["type"] in ("revise", "check") and f"write:{a['section']}:{a['slot']}" not in done \
                and any(p["type"] == "write" and p["slot"] == a["slot"] for p in pending):
            continue
        if a["type"] == "check" and a["slot"].startswith("tech") \
                and any(p["type"] == "probe" for p in pending):
            continue
        if a["slot"] == "src-follow" and any(p["type"] == "consult" for p in pending):
            continue                                   # the follow-up waits for the discovery
        out.append(a)
    return out


def _sec_index(doc: dict, name: str) -> int:
    return next(i for i, s in enumerate(doc["sections"]) if s["name"] == name)


def _scores(cfg: dict, world: dict, pending: list[dict], done: set, step: int,
            active_goal: str, events: dict) -> dict:
    """Score every available action under the configuration; the softmax over these is the
    step's exact likelihood. cfg: controller, habit (per action type), weights (concurrent),
    salience targets, history_bias, value, temperature."""
    doc = world["doc"]
    out = {}
    for a in _available(pending, done):
        base = GOAL_UTIL[a["goal"]][a["type"]] if cfg["controller"] == "concurrent" else 0.0
        if cfg["controller"] == "concurrent":
            s = sum(cfg["weights"][g] * GOAL_UTIL[g][a["type"]] for g in GOALS)
        else:
            s = GOAL_UTIL[active_goal][a["type"]]
            if a["goal"] != active_goal:
                s -= SWITCH_COST if cfg["controller"] == "strict_switch" else SWITCH_COST * 0.5
        s += READING_ORDER_BONUS * (1.0 - _sec_index(doc, a["section"]) / max(1, len(doc["sections"])))
        if cfg["controller"] == "focal_habit":
            s += HABIT_WEIGHT * cfg["habit"].get(a["type"], 0.0)
        s += cfg.get("history_bias", {}).get(a["type"], 0.0)
        if a["slot"] in cfg.get("salient_slots", ()):
            s += cfg.get("salience", 0.0)
        if cfg["controller"] == "maintained" and step in events.get("cues", {}) \
                and a["goal"] == events["cues"][step]:
            s += CUE_BONUS                                       # the dormant intention takes the step
        if events.get("surprise_step") == step and cfg.get("surprise") == "precision":
            s *= SURPRISE_PRECISION
        out[_aid(a)] = s + base * 0.0
    return out


def _softmax(scores: dict, temperature: float) -> dict:
    if not scores:
        return {}
    mx = max(scores.values())
    ex = {k: math.exp((v - mx) / temperature) for k, v in scores.items()}
    z = sum(ex.values())
    return {k: v / z for k, v in ex.items()}


def _next_goal(cfg: dict, world: dict, active_goal: str, pending: list[dict], step: int,
               events: dict, rng_goal: random.Random) -> str:
    """How the foreground goal evolves; the controllers differ here (§1.3)."""
    remaining_goals = [g for g in GOALS if any(a["goal"] == g for a in pending)]
    if not remaining_goals:
        return active_goal
    if events.get("surprise_step") == step and cfg.get("surprise") == "switch":
        others = [g for g in remaining_goals if g != active_goal] or remaining_goals
        return others[rng_goal.randrange(len(others))]
    if active_goal not in remaining_goals:
        return remaining_goals[0]
    if cfg["controller"] in ("strict_switch", "focal_habit"):
        n_active = sum(1 for a in pending if a["goal"] == active_goal)
        if n_active == 0 or (rng_goal.random() < cfg.get("switch_rate", 0.12)):
            others = [g for g in remaining_goals if g != active_goal] or remaining_goals
            return others[rng_goal.randrange(len(others))]
        return active_goal
    if cfg["controller"] == "maintained":
        cue = events.get("cues", {}).get(step)
        if cue and any(a["goal"] == cue for a in pending):
            return cue
        return active_goal if any(a["goal"] == active_goal for a in pending) else remaining_goals[0]
    return active_goal                                            # concurrent: nominal only


def _stop_prob(world: dict, done_n: int, total_n: int, at_boundary: bool) -> float:
    if not at_boundary:
        return 0.0
    progress = done_n / max(1, total_n)
    z = STOP_BASE + STOP_PROGRESS * progress + world.get("stop_shift", 0.0)
    return 1.0 / (1.0 + math.exp(-z))


# ── simulate and score (one code path for both: exactness by construction) ───────────

def simulate(world: dict, cfg: dict, seed_salt: str = "traj") -> dict:
    """Roll the order policy to exhaustion or stop; returns the trajectory with per-step
    likelihoods (of the taken action under cfg) and the stop opportunities."""
    lid = world["lid"]
    rng = _rng(lid, f"{seed_salt}|{cfg['controller']}|{cfg.get('tag', '')}")
    rng_goal = _rng(lid, f"goalpath|{cfg['controller']}|0")        # shared with likelihood path 0
    pending = [dict(a) for a in world["target_actions"]]
    extra = [dict(a) for a in cfg.get("extra_actions", [])]
    pending += extra
    total_n = len(pending)
    done: set = set()
    steps = []
    active_goal = cfg.get("start_goal", "produce")
    events = world["events"]
    step = 0
    stopped_at = None
    while pending:
        active_goal = _next_goal(cfg, world, active_goal, pending, step, events, rng_goal)
        if events.get("interrupt_step") == step:
            urgent = dict(events["interrupt_action"])
            pending.append(urgent)
        sc = _scores(cfg, world, pending, done, step, active_goal, events)
        if not sc:                                                # blocked slots only: force writes
            sc = {_aid(a): 0.0 for a in pending if a["type"] == "write"} or {_aid(pending[0]): 0.0}
        probs = _softmax(sc, cfg.get("temperature", 1.0))
        u = rng.random()
        acc = 0.0
        chosen_id = None
        for k in sorted(probs):
            acc += probs[k]
            if u <= acc:
                chosen_id = k
                break
        chosen_id = chosen_id or sorted(probs)[-1]
        a = next(x for x in pending if _aid(x) == chosen_id)
        pending.remove(a)
        done.add(_aid(a))
        boundary = not any(p["section"] == a["section"] for p in pending)
        steps.append({"i": step, "action": dict(a), "goal_active": active_goal,
                      "p_taken": probs[chosen_id], "n_options": len(probs),
                      "boundary": boundary, "options": sorted(probs)})
        p_stop = _stop_prob(world, len(done), total_n, boundary and bool(pending))
        if p_stop > 0:
            steps[-1]["stop_opportunity"] = p_stop
            if rng.random() < p_stop:
                stopped_at = len([s for s in steps if "stop_opportunity" in s]) - 1
                break
        step += 1
    return {"steps": steps, "stopped_at": stopped_at, "cfg_tag": cfg.get("tag", cfg["controller"]),
            "final_done": sorted(done), "goal_counts": _goal_counts(steps)}


def _goal_counts(steps: list[dict]) -> dict:
    out = {g: 0 for g in GOALS}
    for s in steps:
        out[s["action"]["goal"]] = out.get(s["action"]["goal"], 0) + 1
    return out


def trajectory_log_lik(world: dict, cfg: dict, traj: dict, upto: int | None = None) -> float:
    """Exact log likelihood of the observed order under cfg: replay the pending sets and
    re-score each taken action. The goal path is marginalized identically for EVERY
    configuration over a small shared-seed sample (four paths per controller, path 0
    replaying the simulation's own path), so two configurations that differ only in a
    latent the scores never read (the value twins before their diagnostic event) have
    identical likelihoods by construction (self-test 4); the marginalization is exact in
    the limit and stable here (self-test 1)."""
    n_paths = 4
    lls = []
    for path in range(n_paths):
        rng_goal = _rng(world["lid"], f"goalpath|{cfg['controller']}|{path}")
        pending = [dict(a) for a in world["target_actions"]] + [dict(a) for a in cfg.get("extra_actions", [])]
        done: set = set()
        active_goal = cfg.get("start_goal", "produce")
        events = world["events"]
        ll = 0.0
        for s in traj["steps"][:upto]:
            step = s["i"]
            active_goal = _next_goal(cfg, world, active_goal, pending, step, events, rng_goal)
            if events.get("interrupt_step") == step:
                pending.append(dict(events["interrupt_action"]))
            sc = _scores(cfg, world, pending, done, step, active_goal, events)
            probs = _softmax(sc, cfg.get("temperature", 1.0))
            aid = _aid(s["action"])
            p = probs.get(aid)
            if p is None:
                ll += math.log(1e-9)
                a = dict(s["action"])
            else:
                ll += math.log(max(p, 1e-12))
                a = next(x for x in pending if _aid(x) == aid)
            if a in pending:
                pending.remove(a)
            done.add(aid)
            if "stop_opportunity" in s:
                p_stop = _stop_prob(world, len(done), len(traj["steps"]), True)
                is_stop = traj["stopped_at"] is not None and s is traj["steps"][-1]
                p_stop = min(max(p_stop, 1e-6), 1 - 1e-6)
                ll += math.log(p_stop if is_stop else 1 - p_stop)
        lls.append(ll)
    mx = max(lls)
    return mx + math.log(sum(math.exp(x - mx) for x in lls) / len(lls))


# ── configurations per track ──────────────────────────────────────────────────────────

def controller_cfg(world: dict, controller: str, tag: str | None = None, **over) -> dict:
    lid = world["lid"]
    r = _rng(lid, f"cfg|{controller}")
    cfg = {"controller": controller, "tag": tag or controller, "temperature": TEMPERATURE[world["maker_family"]],
           "start_goal": "produce", "switch_rate": 0.10 + 0.08 * r.random(),
           "habit": {"revise": 1.0, "write": 0.4} if controller == "focal_habit" else {},
           "weights": {g: 0.25 for g in GOALS} if controller == "concurrent" else {},
           "history_bias": {}, "salient_slots": (), "salience": 0.0}
    cfg.update(over)
    return cfg


def value_cfg(world: dict, value: str, **over) -> dict:
    """V track: the standing value enters ONLY after the diagnostic event. The event is the
    consult (the maker discovers the cited source's problem there); a follow-up revision on
    the source's slot becomes available only once the consult is done (the availability
    rule in _available), and the value sets its salience: the accuracy maker is drawn to
    the correction, the prestige maker leaves it late. Before the consult the two values
    share every score exactly (V01's collision is by construction); after it their ORDERS
    diverge, and the changed-context choice diverges besides (§1.4)."""
    cfg = controller_cfg(world, "strict_switch", tag=f"value:{value}")
    cfg["value"] = value
    sec0 = world["doc"]["sections"][0]["name"]
    cfg["extra_actions"] = [{"type": "revise", "section": sec0, "slot": "src-follow", "goal": "audit"}]
    cfg["salient_slots"] = ("src-follow",)
    cfg["salience"] = 2.2 if value == "accuracy" else -1.5
    cfg.update(over)
    return cfg


def forage_cfg(world: dict, forage: str, **over) -> dict:
    cfg = controller_cfg(world, "strict_switch", tag=f"forage:{forage}")
    cfg["forage"] = forage
    # the odd technique: a probe action injected into the queue; the generators differ in
    # how far it is carried and what follows (§1.5)
    sec = world["doc"]["sections"][1]["name"]
    probe = {"type": "probe", "section": sec, "slot": "tech", "goal": "audit"}
    fix = {"type": "fix", "section": sec, "slot": "tech", "goal": "audit"}
    if forage == "explore":
        cfg["extra_actions"] = [probe, {"type": "check", "section": sec, "slot": "tech.out", "goal": "audit"}]
        cfg["history_bias"] = {"probe": 1.2, "check": 0.4}
    elif forage == "error":
        cfg["extra_actions"] = [probe, fix]
        cfg["history_bias"] = {"fix": 1.6}                        # repaired fast, no outcome read
    elif forage == "habit_misuse":
        cfg["extra_actions"] = [probe, dict(probe, slot="tech2"), fix]
        cfg["history_bias"] = {"probe": 0.9, "fix": -0.8}         # weak monitoring: late repair
    else:                                                          # hidden_goal
        cfg["extra_actions"] = [probe, {"type": "revise", "section": world["doc"]["sections"][-1]["name"],
                                        "slot": "s-link", "goal": "tighten"}]
        cfg["history_bias"] = {"probe": 0.8}                       # the distant dependency integrates it
    cfg.update(over)
    return cfg


def history_cfg(world: dict, history: dict, **over) -> dict:
    """A track: a declared training history compiles into (habit, competence, bias). The
    update rules are the two candidate laws of §14.4: attention-only U(K, A) against the
    rich U(K, A, F, C, O, B); which one GENERATED the maker is the hidden truth."""
    K = {"habit": {}, "competence": {}, "bias": {}}
    for ev in history["events"]:
        t = ev["type"]
        K["habit"][t] = K["habit"].get(t, 0.0) + 0.25 * ev.get("attended", 1.0)
        if history["law"] == "rich":
            K["habit"][t] += 0.35 * ev.get("feedback", 0.0) + 0.2 * ev.get("practiced", 0.0)
            K["competence"][t] = K["competence"].get(t, 0.0) + 0.4 * ev.get("practiced", 0.0) * max(ev.get("feedback", 0.0), 0.0)
            K["bias"][t] = K["bias"].get(t, 0.0) + 0.15 * ev.get("constraint", 0.0) + 0.15 * ev.get("opportunity", 0.0)
    cfg = controller_cfg(world, "focal_habit", tag=f"hist:{history['law']}:{history.get('tag', '')}")
    cfg["habit"] = {t: min(2.0, v) for t, v in K["habit"].items()}
    cfg["history_bias"] = {t: min(1.5, K["bias"].get(t, 0.0) + K["competence"].get(t, 0.0)) for t in set(K["bias"]) | set(K["competence"])}
    cfg["compiled"] = K
    cfg.update(over)
    return cfg


def make_history(lid: str, *, attended: bool = True, practiced: bool = False,
                 feedback: float = 0.0, constraint: float = 0.0, opportunity: float = 0.0,
                 n: int = 12, focus: str = "revise", tag: str = "") -> dict:
    """A matched attention sequence (same items, same order) whose other factors vary by
    the arguments — the A track's crossings hold `focus` and n fixed and move the rest."""
    return {"law": "rich" if (practiced or feedback or constraint or opportunity) else "attention_only",
            "tag": tag, "events": [{"type": focus, "attended": 1.0 if attended else 0.2,
                                    "practiced": 1.0 if practiced else 0.0, "feedback": feedback,
                                    "constraint": constraint, "opportunity": opportunity}
                                   for _ in range(n)]}


# ── the world constructor ─────────────────────────────────────────────────────────────

def make_process_world(lid: str, domain: str, *, track: str = "C",
                       surface_family: str = "prose", maker_family: str | None = None,
                       controller: str | None = None, value: str | None = None,
                       forage: str | None = None, history: dict | None = None,
                       missing_variable: bool = False) -> dict:
    """One world: the document plan, the target multiset, the planted events, the true
    configuration (drawn by enumeration from the lineage id unless forced), the realized
    trajectory, the hidden targets, and the renderers' inputs. The true latents live under
    world['truth'] and appear in no rendered string."""
    r = _rng(lid, "world")
    widx = _widx(lid)
    doc = _doc_plan(lid, domain)
    maker_family = maker_family or MAKER_FAMILIES[widx % 2]
    world: dict = {"lid": lid, "track": track, "domain": domain, "doc": doc,
                   "surface_family": surface_family, "maker_family": maker_family,
                   "stop_shift": (r.random() - 0.5) * 0.8}
    world["target_actions"] = _target_actions(lid, doc)
    n_t = len(world["target_actions"])
    # planted events, identical across every configuration of the world
    world["events"] = {
        "interrupt_step": 3 + r.randrange(max(2, n_t // 3)),
        "interrupt_action": {"type": "fix", "section": doc["sections"][0]["name"], "slot": "urgent", "goal": "audit"},
        "cues": {5 + r.randrange(3): "attribute"},
        "surprise_step": 6 + r.randrange(3),
        "contradiction_step": 4 + r.randrange(4),
    }
    truth: dict = {}
    if track in ("C", "M", "P"):
        truth["controller"] = controller or CONTROLLERS[widx % 4]
        cfg = controller_cfg(world, truth["controller"])
        if track == "M" and missing_variable:
            cfg["salient_slots"] = (doc["sections"][0]["slots"][-1],)
            cfg["salience"] = 1.2
            truth["missing_variable"] = "salience"
    elif track == "V":
        truth["value"] = value or VALUES[widx % 2]
        cfg = value_cfg(world, truth["value"])
    elif track == "F":
        truth["forage"] = forage or FORAGE[widx % 4]
        cfg = forage_cfg(world, truth["forage"])
    elif track == "A":
        h = history or make_history(lid, practiced=bool(widx % 2), feedback=0.8 * (widx % 2), tag=f"w{widx}")
        truth["history_law"] = h["law"]
        cfg = history_cfg(world, h)
        world["history"] = h
    else:
        raise ValueError(f"unknown track {track}")
    truth["start_goal"] = cfg["start_goal"]
    world["truth"] = truth
    world["cfg"] = cfg
    traj = simulate(world, cfg)
    world["trajectory"] = traj
    # the evidence cut: the prefix the readers see; the tail is hidden
    n_steps = len(traj["steps"])
    world["cut"] = max(3, min(n_steps - 2, int(n_steps * (0.55 + 0.15 * r.random()))))
    world["hidden"] = hidden_targets(world)
    return world


def hidden_targets(world: dict) -> dict:
    """The prospective truths: the next action after the cut (type + section + slot), the
    stop decision at the next opportunity after the cut, and a changed-context choice
    drawn exactly from the true configuration."""
    traj, cut = world["trajectory"], world["cut"]
    nxt = traj["steps"][cut]["action"] if cut < len(traj["steps"]) else None
    stop_opps = [(j, s) for j, s in enumerate(traj["steps"]) if "stop_opportunity" in s]
    future_opps = [(j, s) for j, s in stop_opps if j >= cut]
    stopped_next = bool(future_opps and traj["stopped_at"] is not None
                        and future_opps[0][0] == len(traj["steps"]) - 1)
    cc = changed_context_choice(world)
    return {"next_edit": nxt, "next_edit_type": nxt["type"] if nxt else None,
            "next_section": nxt["section"] if nxt else None,
            "stops_at_next_opportunity": stopped_next,
            "n_future_stop_opportunities": len(future_opps),
            "changed_context": cc}


CC_OPTIONS = ("finish_quietly", "expand_scope", "recheck_sources", "polish_wording")
CC_UTIL = {  # per active-goal-at-cut utilities, shifted by value/forage/habit residues
    "produce": {"finish_quietly": 0.4, "expand_scope": 1.6, "recheck_sources": -0.2, "polish_wording": 0.0},
    "tighten": {"finish_quietly": 0.6, "expand_scope": -0.4, "recheck_sources": 0.0, "polish_wording": 1.8},
    "audit": {"finish_quietly": -0.2, "expand_scope": 0.0, "recheck_sources": 1.9, "polish_wording": 0.2},
    "attribute": {"finish_quietly": 0.5, "expand_scope": 0.1, "recheck_sources": 1.0, "polish_wording": 0.3},
}


def changed_context_dist(world: dict, cfg: dict) -> dict:
    """The changed context: the deadline is lifted and the audience becomes private. The
    choice distribution is exact under the configuration (P06, V14, A14)."""
    goal = world["trajectory"]["steps"][min(world["cut"], len(world["trajectory"]["steps"]) - 1)]["goal_active"]
    sc = dict(CC_UTIL[goal])
    if cfg.get("value") == "prestige":
        sc["polish_wording"] += 1.0                                # audience private: prestige polishes less...
        sc["recheck_sources"] -= 0.8                               # ...and rechecks less when unobserved
    if cfg.get("value") == "accuracy":
        sc["recheck_sources"] += 1.0
    if cfg.get("forage") == "explore":
        sc["expand_scope"] += 1.2
    if cfg["controller"] == "focal_habit":
        sc["polish_wording"] += HABIT_WEIGHT * cfg["habit"].get("revise", 0.0) * 0.5
    return _softmax(sc, cfg.get("temperature", 1.0))


def changed_context_choice(world: dict) -> dict:
    dist = changed_context_dist(world, world["cfg"])
    r = _rng(world["lid"], "cc")
    u, acc = r.random(), 0.0
    for k in sorted(dist):
        acc += dist[k]
        if u <= acc:
            return {"options": list(CC_OPTIONS), "choice": k, "context_change": "deadline lifted; audience private"}
    return {"options": list(CC_OPTIONS), "choice": sorted(dist)[-1], "context_change": "deadline lifted; audience private"}


# ── grids and oracle posteriors ───────────────────────────────────────────────────────

def grid_for(world: dict) -> list[dict]:
    track = world["track"]
    if track in ("C", "M", "P"):
        return [controller_cfg(world, c, tag=c) for c in CONTROLLERS]
    if track == "V":
        return [value_cfg(world, v) for v in VALUES]
    if track == "F":
        return [forage_cfg(world, f) for f in FORAGE]
    if track == "A":
        h = world["history"]
        alt = dict(h, law=("attention_only" if h["law"] == "rich" else "rich"))
        return [history_cfg(world, h), history_cfg(world, alt)]
    raise ValueError(track)


def oracle_posterior(world: dict, upto: int | None = None) -> dict:
    """Exact posterior over the track's grid from the observed order up to the cut."""
    upto = world["cut"] if upto is None else upto
    lls = {}
    for cfg in grid_for(world):
        lls[cfg["tag"]] = trajectory_log_lik(world, cfg, world["trajectory"], upto=upto)
    mx = max(lls.values())
    ex = {k: math.exp(v - mx) for k, v in lls.items()}
    z = sum(ex.values())
    return {k: v / z for k, v in ex.items()}


def oracle_state(world: dict) -> dict:
    """The construction ceiling (§6 OR): the true configuration's own exact predictive
    distributions wrapped as a realized maker_state."""
    cfg = world["cfg"]
    traj, cut = world["trajectory"], world["cut"]
    # next-action distribution: replay to the cut, score the pending set
    rng_goal = _rng(world["lid"], f"goalpath|{cfg['controller']}|0")
    pending = [dict(a) for a in world["target_actions"]] + [dict(a) for a in cfg.get("extra_actions", [])]
    done: set = set()
    active_goal = cfg.get("start_goal", "produce")
    for s in traj["steps"][:cut]:
        active_goal = _next_goal(cfg, world, active_goal, pending, s["i"], world["events"], rng_goal)
        if world["events"].get("interrupt_step") == s["i"]:
            pending.append(dict(world["events"]["interrupt_action"]))
        aid = _aid(s["action"])
        pending = [p for p in pending if _aid(p) != aid]
        done.add(aid)
    step_i = traj["steps"][cut]["i"] if cut < len(traj["steps"]) else (traj["steps"][-1]["i"] + 1)
    active_goal = _next_goal(cfg, world, active_goal, pending, step_i, world["events"], rng_goal)
    sc = _scores(cfg, world, pending, done, step_i, active_goal, world["events"])
    nxt = _softmax(sc, cfg.get("temperature", 1.0)) or {"stop:none:none": 1.0}
    type_dist: dict = {}
    sec_dist: dict = {}
    for k, p in nxt.items():
        t, sec = k.split(":")[0], k.split(":")[1]
        type_dist[t] = type_dist.get(t, 0.0) + p
        sec_dist[sec] = sec_dist.get(sec, 0.0) + p
    p_stop = _stop_prob(world, len(done), len(traj["steps"]), True)
    cc = changed_context_dist(world, cfg)
    return maker_state(
        proposal_id=f"oracle|{world['lid']}",
        artifact_context={"task": world["doc"]["topic"], "domain": world["domain"]},
        episode_goal=active_goal, control_state={"controller": cfg["controller"]},
        process_model={"pending_n": len(pending)},
        evidence_scope={"observed": [f"step{j}" for j in range(cut)], "withheld": ["tail"]},
        decision_likelihoods={"next_edit": nxt, "next_edit_type": type_dist,
                              "next_section": sec_dist, "changed_context": cc},
        counterfactual_predictions={"if_no_interrupt": {"next_edit_type": max(type_dist, key=type_dist.get)}},
        stop_model={"p_stop": p_stop},
        uncertainty={"posterior_weight": 1.0, "abstain": False})


def cheap_baselines(world: dict) -> dict:
    """The declared cheap comparators, computed from the visible prefix only (§5.1):
    last-edit-type repeat with add-one smoothing over observed types; the reading-order
    position prior for the section; a progress-only stop hazard; a uniform changed-context
    choice."""
    steps = world["trajectory"]["steps"][:world["cut"]]
    counts: dict = {}
    for s in steps:
        counts[s["action"]["type"]] = counts.get(s["action"]["type"], 0) + 1
    last = steps[-1]["action"]["type"] if steps else "write"
    counts[last] = counts.get(last, 0) + 2                         # last-edit bump
    z = sum(counts.values()) + len(EDIT_TYPES)
    type_dist = {t: (counts.get(t, 0) + 1) / z for t in EDIT_TYPES}
    secs = [s["name"] for s in world["doc"]["sections"]]
    done_by_sec = {name: sum(1 for s in steps if s["action"]["section"] == name) for name in secs}
    w = {name: 1.0 / (1 + i) * (1.0 + 0.3 * done_by_sec[name]) for i, name in enumerate(secs)}
    zz = sum(w.values())
    sec_dist = {k: v / zz for k, v in w.items()}
    progress = len(steps) / max(1, len(world["trajectory"]["steps"]))
    p_stop = 1.0 / (1.0 + math.exp(-(STOP_BASE + STOP_PROGRESS * progress)))
    return {"next_edit_type": type_dist, "next_section": sec_dist, "p_stop": p_stop,
            "changed_context": {k: 1.0 / len(CC_OPTIONS) for k in CC_OPTIONS}}


# ── rendering (two surface families; no latent name is ever printed) ─────────────────

_VERB = {"write": "drafted", "revise": "reworked", "check": "went back over", "consult": "looked something up for",
         "cite": "added a reference to", "probe": "tried an unusual step on", "fix": "corrected"}


def render_step(step: dict, family: str) -> str:
    a = step["action"]
    if family == "log":
        return f"[{step['i']:02d}] {a['type'].upper()} {a['section']}/{a['slot']}"
    return f"Then the maker {_VERB[a['type']]} {a['slot']} in {a['section']}."


def render_evidence(world: dict, upto: int | None = None, family: str | None = None) -> str:
    """The visible record: context header + the prefix of the process record. Hidden
    targets, goal names, controller names, values, and foraging labels never appear."""
    family = family or world["surface_family"]
    upto = world["cut"] if upto is None else upto
    doc = world["doc"]
    head = (f"A maker was producing a {doc['domain'].replace('_', ' ')} about {doc['topic']}, "
            f"organized as {len(doc['sections'])} sections "
            f"({', '.join(s['name'] for s in doc['sections'])}). The working record so far:")
    lines = [render_step(s, family) for s in world["trajectory"]["steps"][:upto]]
    return head + "\n" + "\n".join(lines)


def render_artifact(world: dict, family: str | None = None) -> str:
    """The finished-artifact view (whole-document state at the cut): which slots exist and
    which were reworked or checked; content is topic filler, never latent-bearing."""
    family = family or world["surface_family"]
    steps = world["trajectory"]["steps"][:world["cut"]]
    state: dict = {}
    for s in steps:
        a = s["action"]
        state.setdefault(a["slot"], []).append(a["type"])
    lines = []
    for sec in world["doc"]["sections"]:
        for slot in sec["slots"]:
            h = state.get(slot, [])
            if not h:
                lines.append(f"{slot}: (not yet written)")
            elif family == "log":
                lines.append(f"{slot}: {'>'.join(h)}")
            else:
                lines.append(f"{slot}: present" + (", reworked" if "revise" in h else "") + (", checked" if "check" in h else ""))
    return f"The document about {world['doc']['topic']} at this point:\n" + "\n".join(lines)


# ── self-tests (run by tools/test_s6.py; cheap, CPU only) ────────────────────────────

def _selftest() -> list[str]:
    fails = []
    w = make_process_world("C03|essay|s0|w0007|discovery", "essay", track="C")
    # 1 exactness: replaying the true cfg reproduces the recorded step probabilities
    ll = trajectory_log_lik(w, w["cfg"], w["trajectory"], upto=w["cut"])
    ll_rec = sum(math.log(s["p_taken"]) for s in w["trajectory"]["steps"][:w["cut"]])
    stop_terms = [s for s in w["trajectory"]["steps"][:w["cut"]] if "stop_opportunity" in s]
    if not (ll <= 0 and abs(ll - ll_rec) < math.log(4) + 2.0 + 1.2 * len(stop_terms)):
        fails.append(f"likelihood replay off: {ll:.2f} vs recorded {ll_rec:.2f}")
    # 2 endpoint match: all controllers share final doc and per-goal counts
    base = None
    for c in CONTROLLERS:
        t = simulate(w, controller_cfg(w, c, tag=c))
        key = (tuple(sorted(a for a in t["final_done"] if not a.startswith(("probe", "fix:sec1:urgent")))),)
        gc = {g: sum(1 for s in t["steps"] if s["action"]["goal"] == g and s["action"]["slot"] not in ("urgent",)) for g in GOALS}
        full = t["stopped_at"] is None
        if base is None:
            base = (key, gc) if full else None
        elif full and base and (key != base[0]):
            fails.append(f"endpoint mismatch under {c}")
    # 3 oracle separates controllers on average
    hits = 0
    for i in range(8):
        wi = make_process_world(f"C03|essay|s0|w{i:04d}|discovery", "essay", track="C")
        post = oracle_posterior(wi, upto=len(wi["trajectory"]["steps"]))
        hits += int(max(post, key=post.get) == wi["truth"]["controller"])
    if hits < 5:
        fails.append(f"oracle controller recovery {hits}/8")
    # 4 value twins collide up to the diagnostic consult and separate on the full order
    wv = make_process_world("V02|essay|s0|w0003|discovery", "essay", track="V", value="accuracy")
    consult_at = next((k for k, s in enumerate(wv["trajectory"]["steps"]) if s["action"]["type"] == "consult"),
                      len(wv["trajectory"]["steps"]))
    pv = oracle_posterior(wv, upto=consult_at)
    if abs(pv["value:accuracy"] - 0.5) > 1e-6:
        fails.append(f"value twins separated before the consult: {pv}")
    vhits = 0
    for i in range(6):
        wi = make_process_world(f"V02|essay|s0|w{i:04d}|discovery", "essay", track="V")
        pf = oracle_posterior(wi, upto=len(wi["trajectory"]["steps"]))
        if max(pf, key=pf.get) == f"value:{wi['truth']['value']}":
            vhits += 1
    if vhits < 4:
        fails.append(f"value twins not separable from the full order: {vhits}/6")
    # 5 foraging generators separable by the oracle from the full order
    hits = 0
    for i, f in enumerate(FORAGE * 2):
        wf = make_process_world(f"F11|essay|s0|w{i:04d}|discovery", "essay", track="F", forage=f)
        post = oracle_posterior(wf, upto=len(wf["trajectory"]["steps"]))
        hits += int(max(post, key=post.get) == f"forage:{f}")
    if hits < 5:
        fails.append(f"oracle forage recovery {hits}/8")
    # 6 no latent name leaks into any rendered string
    for wx in (w, wv):
        text = render_evidence(wx, upto=len(wx["trajectory"]["steps"])) + render_artifact(wx)
        for bad in CONTROLLERS + VALUES + FORAGE + GOALS:
            if bad.replace("_", " ") in text.lower().replace("_", " "):
                fails.append(f"latent name '{bad}' leaked into a rendering")
                break
    # 7 the oracle state passes the realization gates and scores the hidden targets
    st = oracle_state(w)
    from soundingline.stage6 import realization_report, state_log_score
    if not realization_report(st)["realized"]:
        fails.append("oracle state unrealized")
    if w["hidden"]["next_edit_type"] and state_log_score(st, "next_edit_type", w["hidden"]["next_edit_type"]) is None:
        fails.append("oracle state cannot score the hidden next edit")
    return fails


if __name__ == "__main__":
    f = _selftest()
    print("world self-tests:", "ALL OK" if not f else f)
    sys.exit(1 if f else 0)
