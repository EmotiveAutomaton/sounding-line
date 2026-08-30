"""Stage 5 world constructors (brief §4): the structured latent record every controlled
world defines without exposing by label, built deterministically from a lineage id with
the identity ENUMERATED over each construction's space (no world is a relabeled copy of
another; every root construction is content-hashed onto its lineage by the runners).

Part 1 (here): the joint-reconstruction world (J and R tracks) on the Stage-4 commission
graph, with an exact joint posterior over episode goal, process plan, and standing
preference from the world's own likelihood; the four evidence routes with exact
information about the hidden future choice; the conflict (strategic-source) variant; the
foraging items (F track) with exact learning-progress rulers. Part 2 (further down): the
surface-matched source-regime worlds (A track).

DESIGN CHECK (2026-08-29)
lessons read: LESSONS §3 (known-answer existence checked at construction; truth-marginal
  variance inside every cell; assigned is not realized, so every hidden truth here is a
  realized draw from the world's own process or a construction fact the reader predicts;
  count a construction's identity space against its unit count; a matched comparator and
  the plain route both reported; the oracle direction is one leg of a signature), §4
  (instruct readers only), CONTROLS §6 (construction beats ablation; analytic floors).
gates and bands:
  - identity gate: every world's identity is a seeded permutation of its space indexed by
    the lineage's world index inside its lane block (over-allocation raises); NULL (a
    correct construction): all allocated worlds distinct by content hash; ALTERNATIVE: a
    collision; band: any duplicate among allocated roots fails I03 (the R7 lesson).
  - truth-marginal gate: within each card's factorial cell the hidden truths vary (at
    least two labels per cell); a constant cell is unusable, never a pass.
  - exact-posterior gate (J): the world's own likelihood gives a joint posterior over
    goal x plan x preference; NULL (a live latent): each latent's marginal entropy over
    allocated worlds exceeds 0.5 nats and its truth's posterior mass after all routes
    exceeds the prior in at least 0.7 of worlds; ALTERNATIVE: a latent the evidence does
    not touch, which closes its recovery card as VOID rather than reading a null.
  - route-divergence gate (I04, R01, R04): exact information of the best route minus the
    second-best about the target must exceed the frozen 0.05-nat floor for a world to
    enter a model-choice card; NULL: the routes differ; ALTERNATIVE (a flat menu): the
    world is void for choice, never a failure of active reading (the C03 lesson).
  - equifinality gate (J01, P02): an equifinal world is one where two plans are
    observation-equivalent under the artifact and unordered actions; the reader is scored
    on abstention there (mass on unknown or split), never on picking the historical one.
bands: none here; the card runners' verdict bands are exhaustive (no silent interval).
"""

from __future__ import annotations

import itertools
import json
import math
import os
import random
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from runners import s4_worlds as W                                                # noqa: E402
from runners.s3_lib import AXES, PROFILE_W, choice_probs, hash_stable             # noqa: E402

DOMAINS = ("workshop", "civic")
CONFIRMATION_WORLD_OFFSET = W.CONFIRMATION_WORLD_OFFSET
TRANSFER_WORLD_OFFSET = 20000


def _rng(lid: str, salt: str = "") -> random.Random:
    return random.Random(hash_stable(lid + "|" + salt))


def lineage_index(lid: str) -> tuple[int, str]:
    """(world index inside its lane block, lane) from card|domain|s<seed>|w<index>|lane."""
    parts = lid.split("|")
    try:
        if parts[3].startswith("w") and parts[4] in ("discovery", "transfer", "confirmation", "pilot"):
            widx = int(parts[3][1:])
            lane = parts[4]
            if lane == "confirmation" and widx >= CONFIRMATION_WORLD_OFFSET:
                widx -= CONFIRMATION_WORLD_OFFSET
            elif lane == "transfer" and widx >= TRANSFER_WORLD_OFFSET:
                widx -= TRANSFER_WORLD_OFFSET
            return widx, lane
    except (IndexError, ValueError):
        pass
    return hash_stable(lid + "|index") % 64, "discovery"


def balanced_code(lid: str, space: int, salt: str) -> int:
    """A code in [0, space) that CYCLES through a seeded permutation of the space by the
    world's index inside its lane, offset per lane: the factor levels it encodes are
    balanced across allocated worlds without limiting how many worlds a lane may hold
    (distinctness comes from the rest of the construction, seeded by the id)."""
    widx, lane = lineage_index(lid)
    perm = list(range(space))
    random.Random(hash_stable(f"{salt}|space")).shuffle(perm)
    off = {"discovery": 0, "pilot": 0, "transfer": 1, "confirmation": 2}[lane]
    return perm[(widx + off * (space // 3)) % space]


def enumerate_identity(lid: str, space: int, salt: str, blocks: int = 3) -> int:
    """A code in [0, space) unique to the world's index inside its lane block: the space is
    split into `blocks` equal parts (discovery, transfer, confirmation), each a seeded
    permutation; over-allocation raises."""
    widx, lane = lineage_index(lid)
    block = {"discovery": 0, "pilot": 0, "transfer": 1, "confirmation": 2}[lane]
    per = space // blocks
    if widx >= per:
        raise ValueError(f"{lid}: world index {widx} exceeds the {lane} block ({per} constructions) of {salt}")
    perm = list(range(space))
    random.Random(hash_stable(f"{salt}|space")).shuffle(perm)
    return perm[block * per + widx]


# ── J: the joint-reconstruction world ─────────────────────────────────────────────────
#
# On the Stage-4 commission graph (institution facts, patron lean prior, a standing
# preference profile over four axes, ten scenarios with exact utilities and realized
# draws) the episode adds: an EPISODE GOAL that reweights the maker's axis weights for
# the episode's decisions, a PROCESS PLAN (three production steps in order, chosen from
# six by a policy that depends on goal and preference under feasibility and a partial
# order), a semantic route (the artifact's own account of its emphasis, a noisy channel
# from goal and preference, or a strategic misdirection), and a forensic route (a costly
# observation of which step came first). The target is a hidden future choice.

GOALS = ("deadline", "thrift", "reputation", "durability")
GOAL_AXIS = {"deadline": "fast", "thrift": "cheap", "reputation": "precedent", "durability": "robust"}
GOAL_TEXT = {"deadline": "to have it finished before the fixed date, whatever it costs",
             "thrift": "to bring it in well under the sum set aside",
             "reputation": "to be seen to have done it the way the guild's best do it",
             "durability": "to have it outlast every other piece in the building"}
GOAL_BONUS = 1.0        # tuned 2026-08-29: goal truth mass 0.82, preference 0.64, 65% of worlds past the route floor
PROCESS_STEPS = ("cast the parts", "carve the parts", "assemble from stock", "commission outside",
                 "test under load", "finish by hand")
# step attributes on the four axes (robust, cheap, fast, precedent), from the workshop's
# point of view: casting is fast and cheap, carving traditional and strong, stock assembly
# fast and cheap, outside commission precedent-heavy, load testing robust and slow, hand
# finish precedent and robust
STEP_ATTR = {"cast the parts": (0.3, 0.8, 0.8, 0.2), "carve the parts": (0.7, 0.2, 0.2, 0.9),
             "assemble from stock": (0.3, 0.9, 0.9, 0.1), "commission outside": (0.5, 0.3, 0.6, 0.8),
             "test under load": (0.9, 0.3, 0.1, 0.4), "finish by hand": (0.7, 0.2, 0.3, 0.8)}
# the partial order: a load test cannot precede the making step; hand finish comes last
PRECEDES = {("cast the parts", "test under load"), ("carve the parts", "test under load"),
            ("assemble from stock", "test under load"), ("commission outside", "test under load"),
            ("cast the parts", "finish by hand"), ("carve the parts", "finish by hand"),
            ("assemble from stock", "finish by hand"), ("commission outside", "finish by hand"),
            ("test under load", "finish by hand")}
MAKING = ("cast the parts", "carve the parts", "assemble from stock", "commission outside")
PLAN_TEMP = 0.25
SEMANTIC_FIDELITY = 0.75      # the honest artifact names the true goal's emphasis this often
EMPHASIS_TEXT = {"deadline": "the piece was got done in the time allowed and no later",
                 "thrift": "the piece was made with an eye on every coin",
                 "reputation": "the piece was made the way the trade's best would judge it",
                 "durability": "the piece was made to stand for a lifetime"}
FORENSIC_COST_NATS = 0.08     # declared cost of the forensic observation (R04)
# design 2 (2026-08-29): the step pays in about half the worlds (its exact information has
# median 0.0155 nats over 128 worlds), the second episode's goal weighs twice (ceiling −0.50
# against −0.90 at 1.0), and half the worlds relax the plan's partial order so equifinal
# twins exist for the abstention ruler
DESIGN2 = os.environ.get("S5_DESIGN", "1") == "2"
if DESIGN2:
    FORENSIC_COST_NATS = 0.015
GOAL_BONUS2 = 2.0 if DESIGN2 else None


def effective_weights(profile: str, goal: str, bonus: float | None = None) -> tuple:
    w = list(PROFILE_W[profile])
    w[AXES.index(GOAL_AXIS[goal])] += (GOAL_BONUS if bonus is None else bonus)
    return tuple(w)


def episode_bonus(scen_i: int) -> float | None:
    """Episode 2's goal (scenario 9) weighs GOAL_BONUS2 under design 2, GOAL_BONUS otherwise."""
    return GOAL_BONUS2 if (scen_i >= 9 and GOAL_BONUS2 is not None) else None


def plan_candidates(feasible_steps: list[str], relaxed: bool = False) -> list[tuple]:
    """Every ordered triple of distinct feasible steps that respects the partial order and
    contains exactly one making step; `relaxed` (design 2, half the worlds) drops the
    partial order so orders of one step set are all candidates and equifinal twins exist."""
    out = []
    for trip in itertools.permutations(feasible_steps, 3):
        if sum(s in MAKING for s in trip) != 1:
            continue
        ok = relaxed or all(not ((b, a) in PRECEDES) for i, a in enumerate(trip) for b in trip[i + 1:])
        if ok:
            out.append(trip)
    return out


def plan_probs(cands: list[tuple], w: tuple) -> list[float]:
    vals = [sum(sum(wi * a for wi, a in zip(w, STEP_ATTR[s])) for s in c) / 3 for c in cands]
    m = max(vals)
    e = [math.exp((v - m) / PLAN_TEMP) for v in vals]
    z = sum(e)
    return [x / z for x in e]


def plan_artifact(plan: tuple) -> frozenset:
    """What the finished artifact shows of its plan: the SET of steps, no order (two plans
    with the same set are equifinal under artifact-only and unordered access)."""
    return frozenset(plan)


def make_joint_world(lid: str, domain: str, conflict: bool = False) -> dict:
    """The base commission graph (the Stage-4 world, seeded by the id and distinct per
    id) carries the identity; the balanced code cycles goal (4) x episode-2 goal (3, never
    the same) x semantic channel draw (4) across the lane's worlds so the goal factors are
    balanced; the plan, the decisions, and the description are then REALIZED draws. The plan, the decisions, and the description are REALIZED
    draws from the world's own process."""
    base = W.make_world(lid, domain)
    code = balanced_code(lid, 4 * 3 * 4, f"joint|{domain}")
    goal = GOALS[code % 4]
    code //= 4
    goal2 = [g for g in GOALS if g != goal][code % 3]
    code //= 3
    sem_draw = code % 4                         # which emphasis the channel names if unfaithful
    rng = _rng(lid, "joint")
    profile = base["profile"]
    w_eff = effective_weights(profile, goal)
    feasible = [s for s in PROCESS_STEPS if s not in base["blocked_steps"]]
    relaxed = DESIGN2 and _rng(lid, "relax").random() < 0.5
    cands = plan_candidates(feasible, relaxed=relaxed)
    pp = plan_probs(cands, w_eff)
    r = rng.random()
    acc = 0.0
    plan = cands[-1]
    for c, p in zip(cands, pp):
        acc += p
        if r <= acc:
            plan = c
            break
    # episode decisions: the first eight scenarios re-drawn under the episode's effective
    # weights (the Stage-4 draws used the profile alone); scenario 8 is the held-out future
    # choice of THIS episode, scenario 9 the future choice of episode 2 under goal2
    scen = []
    for s in base["scenarios"]:
        U = s["utilities"]
        g = goal if s["i"] < 9 else goal2
        wv = effective_weights(profile, g, episode_bonus(s["i"]))
        probs = choice_probs(U, wv)
        z = sum(p for p, ax in zip(probs, AXES) if ax in s["feasible"])
        dist = {ax: (p / z if ax in s["feasible"] else 0.0) for p, ax in zip(probs, AXES)}
        rr = _rng(lid, f"jdraw{s['i']}").random()
        a = 0.0
        draw = s["feasible"][-1]
        for ax in AXES:
            a += dist[ax]
            if rr <= a and dist[ax] > 0:
                draw = ax
                break
        scen.append({**s, "goal": g, "draw": draw, "distribution": dist})
    # the semantic route: the artifact's own account of its emphasis
    faithful = rng.random() < SEMANTIC_FIDELITY
    named = goal if faithful else GOALS[sem_draw]
    communicative_goal = "inform"
    if conflict:
        # a strategic maker names an emphasis that is NOT its goal, to steer the reader
        named = [g for g in GOALS if g != goal][sem_draw % 3]
        faithful = False
        communicative_goal = "mislead"
    description = (f"The maker's own note on the finished {base['item']}: {EMPHASIS_TEXT[named]}.")
    equifinal_set = plan_artifact(plan)
    twins = [c for c in cands if plan_artifact(c) == equifinal_set and c != plan]
    return {"lineage_id": lid, "domain": domain, "base": base, "item": base["item"],
            "institution": base["institution"],
            "standing_preference": profile, "episode_goal": goal, "episode2_goal": goal2,
            "process_plan": list(plan), "plan_candidates": [list(c) for c in cands],
            "plan_probs_under_truth": pp, "feasible_steps": feasible,
            "scenarios": scen, "semantic_named_goal": named, "semantic_faithful": faithful,
            "description": description, "communicative_goal": communicative_goal,
            "relaxed_order": relaxed, "conflict": conflict, "equifinal_twins": [list(t) for t in twins],
            "equifinal": bool(twins), "forensic_first_step": plan[0],
            "forensic_cost_nats": FORENSIC_COST_NATS,
            "target_scenario": 8, "target2_scenario": 9}


# evidence routes -----------------------------------------------------------------------

def route_texts(world: dict, n_records: int = 6) -> dict:
    """The four routes as text blocks, each with its evidence ids."""
    base = world["base"]
    recs = world["scenarios"][:n_records]
    action = "\n".join(f"- [{'a' + str(i + 1)}] {s['context']} It chose: {s['options'][s['draw']]}."
                       for i, s in enumerate(recs))
    facts, _ = W.render_fact_list(base)
    contextual = "[c1] " + facts.replace("\n", " ")
    semantic = "[s1] " + world["description"]
    forensic = (f"[f1] A costly close inspection of the finished {world['item']} establishes "
                f"which step was taken first: {world['forensic_first_step']}.")
    return {"action": {"text": action, "ids": [f"a{i + 1}" for i in range(len(recs))]},
            "contextual": {"text": contextual, "ids": ["c1"]},
            "semantic": {"text": semantic, "ids": ["s1"]},
            "forensic": {"text": forensic, "ids": ["f1"]}}


# exact inference over the hypothesis space ------------------------------------------

def hypotheses(world: dict) -> list[tuple]:
    return [(g, pf, tuple(c)) for g in GOALS for pf in AXES for c in world["plan_candidates"]]


def log_prior(world: dict, h: tuple) -> float:
    g, pf, plan = h
    base = world["base"]
    lp = math.log(0.25) + math.log(base["prior"][pf])
    cands = [tuple(c) for c in world["plan_candidates"]]
    pp = plan_probs(cands, effective_weights(pf, g))
    lp += math.log(max(pp[cands.index(plan)], 1e-12))
    return lp


def log_lik_action(world: dict, h: tuple, n_records: int = 6) -> float:
    g, pf, _ = h
    wv = effective_weights(pf, g)
    lp = 0.0
    for s in world["scenarios"][:n_records]:
        probs = choice_probs(s["utilities"], wv)
        z = sum(p for p, ax in zip(probs, AXES) if ax in s["feasible"])
        p = probs[AXES.index(s["draw"])] / z
        lp += math.log(max(p, 1e-12))
    return lp


def log_lik_semantic(world: dict, h: tuple) -> float:
    """The channel: an honest artifact names the true goal's emphasis with fidelity
    SEMANTIC_FIDELITY, else a uniform other; the reader's hypothesis space includes the
    strategic channel only when the conflict card opens it (J04)."""
    g, _, _ = h
    named = world["semantic_named_goal"]
    p = SEMANTIC_FIDELITY if named == g else (1 - SEMANTIC_FIDELITY) / 3
    return math.log(p)


def log_lik_semantic_strategic(world: dict, h: tuple) -> float:
    """Under the missing-goal hypothesis the note names anything but the goal."""
    g, _, _ = h
    named = world["semantic_named_goal"]
    return math.log(1e-6 if named == g else 1 / 3)


def log_lik_forensic(world: dict, h: tuple) -> float:
    _, _, plan = h
    return 0.0 if plan[0] == world["forensic_first_step"] else math.log(1e-9)


def log_lik_artifact(world: dict, h: tuple) -> float:
    """Artifact-only: the set of steps is visible, the order is not."""
    _, _, plan = h
    return 0.0 if plan_artifact(plan) == plan_artifact(tuple(world["process_plan"])) else math.log(1e-9)


def posterior(world: dict, routes: list[str], n_records: int = 6, strategic: bool = False) -> dict:
    """Exact joint posterior over hypotheses given the named routes ('action',
    'contextual', 'semantic', 'forensic', 'artifact'); contextual = the world's own prior
    (without it the preference prior is flat)."""
    hs = hypotheses(world)
    lps = []
    for h in hs:
        lp = 0.0
        g, pf, plan = h
        if "contextual" in routes:
            lp += log_prior(world, h)
        else:
            cands = [tuple(c) for c in world["plan_candidates"]]
            pp = plan_probs(cands, effective_weights(pf, g))
            lp += math.log(0.25) + math.log(0.25) + math.log(max(pp[cands.index(plan)], 1e-12))
        if "action" in routes:
            lp += log_lik_action(world, h, n_records)
        if "semantic" in routes:
            lp += (log_lik_semantic_strategic if strategic else log_lik_semantic)(world, h)
        if "forensic" in routes:
            lp += log_lik_forensic(world, h)
        if "artifact" in routes:
            lp += log_lik_artifact(world, h)
        lps.append(lp)
    m = max(lps)
    e = [math.exp(x - m) for x in lps]
    z = sum(e)
    return {h: v / z for h, v in zip(hs, e)}


def marginal(post: dict, which: int) -> dict:
    out: dict = {}
    for h, p in post.items():
        k = h[which] if which != 2 else " > ".join(h[2])
        out[k] = out.get(k, 0.0) + p
    return out


def predictive(world: dict, post: dict, scen_i: int) -> dict:
    s = world["scenarios"][scen_i]
    out = {ax: 0.0 for ax in AXES}
    for (g, pf, _), p in post.items():
        gg = g if scen_i < 9 else world["episode2_goal"]      # episode 2's goal is given (J05)
        probs = choice_probs(s["utilities"], effective_weights(pf, gg, episode_bonus(scen_i)))
        z = sum(q for q, ax in zip(probs, AXES) if ax in s["feasible"])
        for q, ax in zip(probs, AXES):
            if ax in s["feasible"]:
                out[ax] += p * q / z
    return out


def route_information(world: dict, n_records: int = 6) -> dict:
    """Exact information (nats) each route adds about the hidden future choice on top of
    the contextual prior: KL between the predictive with and without the route, in
    expectation approximated at the realized evidence (the realized-evidence information,
    what a reader of THIS world could gain). The forensic entry carries its declared
    cost; the matrix is the I04/R01 ruler."""
    base_post = posterior(world, ["contextual"], n_records)
    base_pred = predictive(world, base_post, world["target_scenario"])
    info = {}
    for r in ("action", "semantic", "forensic"):
        post = posterior(world, ["contextual", r], n_records)
        pred = predictive(world, post, world["target_scenario"])
        truth = world["scenarios"][world["target_scenario"]]["draw"]
        info[r] = {"kl_from_prior": sum(pred[a] * math.log(max(pred[a], 1e-12) / max(base_pred[a], 1e-12)) for a in AXES),
                   "truth_log_score_gain": math.log(max(pred[truth], 1e-12)) - math.log(max(base_pred[truth], 1e-12))}
    info["contextual"] = {"kl_from_prior": 0.0, "truth_log_score_gain": 0.0}
    info["forensic"]["cost_nats"] = world["forensic_cost_nats"]
    ranked = sorted(("action", "semantic", "forensic"), key=lambda r: -info[r]["kl_from_prior"])
    info["best"], info["second"] = ranked[0], ranked[1]
    info["divergence"] = info[ranked[0]]["kl_from_prior"] - info[ranked[1]]["kl_from_prior"]
    return info


# ── F: foraging items with exact rulers ───────────────────────────────────────────────

ITEM_CLASSES = ("novel_explained", "complex_compressible", "random_unlearnable",
                "structured_residual", "trivial_known", "learnable_intermediate")


# a small exact rule family for the foraging rulers: a learner that keeps every rule
# consistent with the seen prefix; learning progress is the hypothesis reduction (bits) on
# observing the fifth element, prediction error is one minus the consistent rules' vote for
# the truth; an item whose rule is not in the family is unlearnable (error 1, progress 0),
# an item whose rule is stated has one hypothesis from the start (progress 0)
def _fib(a: int, b: int, k: int) -> int:
    x, y = a, b
    for _ in range(k):
        x, y = y, (x + y) % 30
    return x


def _rule_family() -> list:
    rules = []
    for c in range(0, 100):
        rules.append(("constant", c, lambda k, c=c: c))
    for a in range(0, 30):
        for d in range(-9, 12):
            if d:
                rules.append(("arithmetic", (a, d), lambda k, a=a, d=d: a + d * k))
    for a in range(0, 20):
        for d1 in range(1, 8):
            for d2 in range(-4, 5):
                rules.append(("alternating", (a, d1, d2), lambda k, a=a, d1=d1, d2=d2: a + (k // 2) * (d1 + d2) + (k % 2) * d1))
    for p0 in range(1, 10):
        for p1 in range(1, 10):
            for p2 in range(1, 10):
                rules.append(("period3", (p0, p1, p2), lambda k, p=(p0, p1, p2): p[k % 3]))
    for a in range(1, 6):
        for b in range(1, 6):
            rules.append(("fibmod", (a, b), lambda k, a=a, b=b: _fib(a, b, k)))
    return rules


_RULES = None
FORAGE_SHOWN = 3        # elements shown before the reader chooses what to examine


def consistent_rules(seq: list, k: int) -> list:
    global _RULES
    if _RULES is None:
        _RULES = _rule_family()
    out = []
    for name, par, f in _RULES:
        if all(f(j) == seq[j] for j in range(k)):
            out.append((name, par, f))
    return out


def make_foraging_set(lid: str) -> dict:
    """Six number-sequence items, one per class, each with an exact ruler from the rule
    family: prediction error (one minus the consistent rules' vote for the true fifth
    element), learning progress (bits of hypothesis reduction on observing the fifth
    element), novelty (distinct values in the prefix, zero when stated), description
    length, and whether the structure is reducible (a family rule, not stated). Truths are
    construction facts of the generating rule."""
    rng = _rng(lid, "forage")
    items = {}
    a, d = rng.randint(2, 9), rng.randint(2, 7)
    items["novel_explained"] = {"seq": [a + d * i for i in range(8)], "rule": f"add {d} each time", "stated": True, "learnable": True}
    p = [rng.randint(1, 9) for _ in range(3)]
    items["complex_compressible"] = {"seq": (p * 4)[:8], "rule": "a block of three repeats", "stated": False, "learnable": True}
    items["random_unlearnable"] = {"seq": [rng.randint(0, 99) for _ in range(8)], "rule": "none", "stated": False, "learnable": False}
    a2, d1 = rng.randint(0, 9), rng.randint(2, 7)
    d2 = rng.choice([x for x in range(-3, 4) if x not in (0, d1)])       # a real alternation, never plain arithmetic
    items["structured_residual"] = {"seq": [a2 + (i // 2) * (d1 + d2) + (i % 2) * d1 for i in range(8)], "rule": "two alternating steps", "stated": False, "learnable": True}
    k = rng.randint(1, 9)
    items["trivial_known"] = {"seq": [k] * 8, "rule": "constant", "stated": True, "learnable": True}
    fa, fb = rng.randint(1, 5), rng.randint(1, 5)
    items["learnable_intermediate"] = {"seq": [_fib(fa, fb, i) for i in range(8)], "rule": "each element is the sum of the two before it, modulo thirty", "stated": False, "learnable": True}
    rulers = {}
    for name, it in items.items():
        seq = it["seq"]
        if it["stated"]:
            h3 = h4 = 1
            err3 = err4 = 0.0
        else:
            c3 = consistent_rules(seq, FORAGE_SHOWN)
            c4 = consistent_rules(seq, FORAGE_SHOWN + 1)
            h3, h4 = len(c3), len(c4)
            # the consistent rules' vote on the next unseen element, before and after one more
            err3 = (1.0 - sum(1 for _, _, f in c3 if f(FORAGE_SHOWN) == seq[FORAGE_SHOWN]) / h3) if h3 else 1.0
            err4 = (1.0 - sum(1 for _, _, f in c4 if f(FORAGE_SHOWN + 1) == seq[FORAGE_SHOWN + 1]) / h4) if h4 else 1.0
        progress = max(0.0, err3 - err4) if it["learnable"] else 0.0
        novelty = 0.0 if it["stated"] else min(1.0, len(set(seq[:FORAGE_SHOWN + 1])) / (FORAGE_SHOWN + 1))
        complexity = len(json.dumps(seq)) / 40
        rulers[name] = {"prediction_error": round(err3, 3), "learning_progress": round(progress, 3),
                        "novelty": round(novelty, 3), "complexity": round(complexity, 3),
                        "consistent_after_shown": h3, "consistent_after_one_more": h4,
                        "reducible": it["learnable"] and not it["stated"], "stated": it["stated"]}
    return {"lineage_id": lid, "items": items, "rulers": rulers}


def foraging_item_text(name: str, it: dict, show: int = FORAGE_SHOWN) -> str:
    shown = ", ".join(str(x) for x in it["seq"][:show])
    stated = f" (the rule is given: {it['rule']})" if it["stated"] else ""
    return f"Sequence {name.replace('_', ' ')}: {shown}, ...{stated}"


# ── self-test ─────────────────────────────────────────────────────────────────────────

def self_test(n: int = 24) -> None:
    for domain in DOMAINS:
        seen = set()
        goals, prefs, plans = set(), set(), set()
        live_plan = 0
        for i in range(n):
            lid = f"J01|{domain}|s{i % 3}|w{i:04d}|discovery"
            w = make_joint_world(lid, domain)
            h = W.construction_hash({k: v for k, v in w.items() if k != "base"} | {"base_hash": W.construction_hash(w["base"])})
            assert h not in seen, (domain, i)
            seen.add(h)
            goals.add(w["episode_goal"])
            prefs.add(w["standing_preference"])
            plans.add(tuple(w["process_plan"]))
            assert tuple(w["process_plan"]) in {tuple(c) for c in w["plan_candidates"]}
            post = posterior(w, ["contextual", "action", "semantic", "forensic"])
            assert abs(sum(post.values()) - 1) < 1e-9
            mg = marginal(post, 0)
            assert abs(sum(mg.values()) - 1) < 1e-9
            pred = predictive(w, post, 8)
            assert abs(sum(pred.values()) - 1) < 1e-9
            info = route_information(w)
            assert info["forensic"]["cost_nats"] > 0
            # the plan latent is live: with the forensic route the plan's truth mass rises
            m_plan_before = marginal(posterior(w, ["contextual"]), 2)
            m_plan_after = marginal(posterior(w, ["contextual", "forensic", "artifact"]), 2)
            key = " > ".join(w["process_plan"])
            live_plan += m_plan_after.get(key, 0) > m_plan_before.get(key, 0)
            wc = make_joint_world(lid, domain, conflict=True)
            assert wc["semantic_named_goal"] != wc["episode_goal"]
            rt = route_texts(w)
            assert set(rt) == {"action", "contextual", "semantic", "forensic"}
        assert len(goals) == 4 and len(prefs) >= 3 and len(plans) >= 4, (domain, goals, prefs, len(plans))
        assert live_plan >= 0.7 * n, (domain, live_plan)
        # goals cycle in balance over the first 48 worlds of a lane
        gs = [make_joint_world(f"J01|{domain}|s0|w{i:04d}|discovery", domain)["episode_goal"] for i in range(48)]
        assert all(gs.count(g) == 12 for g in GOALS), (domain, {g: gs.count(g) for g in GOALS})
    f = make_foraging_set("F01|all|s0|w0000|discovery")
    assert set(f["items"]) == set(ITEM_CLASSES)
    assert f["rulers"]["trivial_known"]["learning_progress"] == 0.0
    assert f["rulers"]["random_unlearnable"]["learning_progress"] == 0.0
    assert f["rulers"]["structured_residual"]["learning_progress"] > 0.0, "the learning-progress ruler cannot fire"
    print(f"s5_worlds part-1 self-tests pass: {2 * n} joint worlds, routes, posteriors, foraging items")


if __name__ == "__main__":
    self_test()
