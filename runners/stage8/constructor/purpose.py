"""The purpose family (brief §5 PU): each world carries a purpose p from a declared set
(persuade an audience; document a procedure; explore a question; teach a novice), which
determines the goal utility ordering together with the law, sets the required sections, and
is only partially visible in the brief (topic and audience; the required sections are
withheld with the purpose in the purpose-withheld condition, and the purpose is stated in
the purpose-supplied condition). The oracle carries p; the pull ordering is derived and
recorded beside it. Equivalence cases exist by construction: purposes are built in pairs
that agree on the writing and revising utilities (persuade with teach; document with
explore) and differ on the later diagnostic types, so an early prefix leaves two purposes
alive until a diagnostic event.

Implementation: a purpose is a goal-level object, a utility table registered into the law's
goal table at runtime (the Stage 7 file is untouched); every inventory action of a purpose
world belongs to the purpose, so the goal holds across the artifact (the walkthrough's rule);
the capsule's solver executes a supplied purpose through the supplied table (the law falls
back to the supplied table when the owner is not in its own table), so the SOL ceiling
comparator still equals the oracle on purpose worlds.

DESIGN CHECK (2026-09-04)
lessons read: LESSONS §3 (check that a known-answer design's known answer can exist: the
  purpose equivalence class is computed exactly from prefix likelihoods and the guard
  suite asserts the truth is in its own class and that pairs collide on early prefixes;
  target hiding: the purpose name and the required sections appear in no visible byte, and
  the canary test plants them), §5.
gates: the purpose leak check (I06's canaries): NULL of a leaky family is any visible byte
  carrying the purpose name or the required-section set (fails DOWN: the family is
  INSTRUMENT_FAILED); ALTERNATIVE: none. The equivalence construction: NULL is a family
  with no equivalence worlds (fails DOWN: G04 VOID); ALTERNATIVE: a nonzero share.
bands: exhaustive.
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO))

from runners.stage7.constructor import worlds as W                                 # noqa: E402
from runners.stage7.reader import law as LAW                                       # noqa: E402
from runners.stage8.constructor.gradient import make_world_ext, pull_ordering       # noqa: E402

PURPOSES = ("persuade", "teach", "document", "explore")
PAIRS = {"persuade": "teach", "teach": "persuade", "document": "explore", "explore": "document"}
# utility tables over action types. A pair agrees on every type that is always available and
# differs ONLY on the two tool-gated types (cite needs the library, consult needs source
# access), so while the maker perceives neither tool the two purposes' policies are
# IDENTICAL over the subjective option set (exact equivalence by construction) and the
# diagnostic later event is a tool arriving or a belief corrected; across pairs the
# always-available utilities differ, so an ordinary prefix separates persuade from document.
# the tables are scaled by two against the first draft: at scale one the exact-minus-DOM gap at
# the cut on purpose worlds was 0.35 nats (median 0.01), too thin a ruler for a fifth-of-the-gap
# floor; at scale two it is about 0.55 (median 0.3), the K family's order (validity pass,
# 2026-09-04, before any purpose cell ran)
PURPOSE_SCALE = 2.0
PURPOSE_UTILITY = {
    "persuade": {"write": 4.0, "revise": 3.2, "restructure": 2.0, "check": 0.0, "fix": 0.6, "probe": 0.0, "cite": 3.0, "consult": -1.0},
    "teach":    {"write": 4.0, "revise": 3.2, "restructure": 2.0, "check": 0.0, "fix": 0.6, "probe": 0.0, "cite": -1.0, "consult": 3.0},
    "document": {"write": 2.8, "revise": 0.6, "restructure": -0.4, "check": 3.6, "fix": 2.4, "probe": -0.8, "cite": 0.4, "consult": 2.8},
    "explore":  {"write": 2.8, "revise": 0.6, "restructure": -0.4, "check": 3.6, "fix": 2.4, "probe": -0.8, "cite": 2.8, "consult": 0.4},
}
PURPOSE_LANGUAGE = {
    "persuade": "The document is meant to persuade its audience of a position.",
    "teach": "The document is meant to teach a novice how something works.",
    "document": "The document is meant to record a procedure so it can be followed.",
    "explore": "The document is meant to explore an open question.",
}
AFFORDANCE = {"persuade": "convince someone of a position", "teach": "learn how something works from it",
              "document": "follow a procedure exactly", "explore": "see what is known and unknown about a question"}


def register() -> None:
    """Idempotent: the purposes enter the law's goal table (shared with the constructor)."""
    for p, u in PURPOSE_UTILITY.items():
        LAW.GOAL_UTILITY.setdefault(p, dict(u))


def required_sections(doc: dict, purpose: str) -> list[str]:
    names = [s["name"] for s in doc["sections"]]
    if purpose == "persuade":
        return names[:2]
    if purpose == "teach":
        return names[-2:]
    if purpose == "document":
        return list(names)
    return names[:1]


def make_pu_world(lid: str, domain: str, purpose: str | None = None, shape: str = "essay", maker_free: bool = False,
                  law_name: str | None = None, belief: str | None = None, residue: str | None = None,
                  tendency: str | None = None, residue_scale: float = 1.0, finish: bool = True, salt: str = "traj") -> dict:
    register()
    r = W._rng(lid, "purpose")
    purpose = purpose or PURPOSES[r.randrange(len(PURPOSES))]
    doc = W._doc_plan(lid, domain) if shape == "essay" else None
    from runners.stage8.constructor.gradient import doc_plan                       # noqa: PLC0415
    doc = doc_plan(lid, domain, shape)
    forced = {"brief_sections": required_sections(doc, purpose)}
    if maker_free:
        belief, residue = "accurate", "none"
    w = make_world_ext(lid, domain, shape, goal=purpose, law_name=law_name, belief=belief, residue=residue,
                       tendency=tendency, forced_cext=forced, owner_all=purpose, residue_scale=residue_scale,
                       finish=finish, salt=salt)
    w["purpose"] = purpose
    w["pull_ordering"] = pull_ordering(PURPOSE_UTILITY[purpose], w["state"]["expertise_law"])
    if finish and not w["degenerate"]:
        w["hidden"]["equivalence_class"] = purpose_class(w)
        w["hidden"]["purpose_class"] = sorted({k.split("|")[0] for k in w["hidden"]["equivalence_class"]})
    return w


def purpose_class(world: dict) -> list[str]:
    """Configurations (purpose x law x belief x residue, the world's tendency) that match the
    truth's prefix likelihood AND predictive distribution at the cut within 1e-6."""
    register()
    truth = world["state_at_cut"]
    sections = [s["name"] for s in world["doc"]["sections"]]
    cut, traj, inv = world["cut"], world["trajectory"], world["inventory"]
    t_ll = W._prefix_ll(world["state"], traj, cut, inv, sections)
    t_pred = world["oracle"]["next_action"]
    out = []
    tend = world["state"]["names"]["tendency"]
    for p in PURPOSES:
        inv_p = [dict(a, goal_owner=p) for a in inv]
        for ln in W.LAW_NAMES:
            for b in W.BELIEFS:
                for h in W.RESIDUES:
                    st = W.make_state(world["lid"], world["doc"], inv_p, p, ln, b, h, tend, {"brief_sections": world["state"]["external_context"]["brief_sections"]})
                    if world["state"].get("reveal_scale") is not None:
                        st["history_residue"]["habit"] = {k: round(v * world["state"]["reveal_scale"], 4) for k, v in st["history_residue"].get("habit", {}).items()}
                    ll = W._prefix_ll(st, traj, cut, inv_p, sections)
                    if abs(ll - t_ll) > 1e-6:
                        continue
                    sac = W._state_at(st, traj, cut, inv_p)
                    pred = W._predictive(sac, truth["pending"], sections, traj["steps"][cut - 1]["type"], cut,
                                         sum(1 for s in traj["steps"][:cut] if s["outcome"] == "done"), len(inv_p))
                    if 0.5 * sum(abs(pred["next_action"].get(k, 0.0) - t_pred.get(k, 0.0)) for k in set(pred["next_action"]) | set(t_pred)) < 1e-6:
                        out.append(f"{p}|{ln}|{b}|{h}")
    return sorted(out)


def hide_purpose(ev: dict) -> dict:
    """The purpose-withheld brief: topic and audience stay; the required sections (the
    purpose's) leave; the key stays so every reader parses the same shape."""
    ev = dict(ev)
    if ev.get("brief"):
        b = dict(ev["brief"])
        b["required_sections"] = []
        ev["brief"] = b
    return ev


def purpose_supplied(ev: dict, purpose: str, form: str = "language") -> dict:
    """The purpose-supplied condition: the brief as withheld plus the purpose as a supplied
    proximal-goal factor (language form: the purpose sentence; executable: the table with
    the owner), the visible bytes otherwise equal to the withheld condition."""
    ev = hide_purpose(ev)
    sf = dict(ev.get("supplied_factors") or {"form": form, "factors": {}})
    factors = dict(sf.get("factors") or {})
    factors["proximal_goal"] = PURPOSE_LANGUAGE[purpose] if form == "language" else {"utility": dict(PURPOSE_UTILITY[purpose]), "owner": purpose}
    ev["supplied_factors"] = {"form": form, "factors": factors}
    return ev


def purpose_candidates() -> dict:
    """The closed candidate set for the affordance question (what could a reader use this
    document to do), one short option per purpose in the option's surface form."""
    return {p: AFFORDANCE[p] for p in PURPOSES}


def leak_check(ev: dict, world: dict) -> list[str]:
    """Visible bytes must carry neither the purpose name (in any identifier, tag, or key) nor
    the required-section set nor a purpose in an option's goal owner."""
    problems = []
    p = world.get("purpose")
    if p:
        for k in ("unit_ref", "condition_ref", "render", "domain", "regime"):
            if p in str(ev.get(k, "")).lower():
                problems.append(f"purpose name in {k}")

        def keys(o):
            if isinstance(o, dict):
                for kk, vv in o.items():
                    yield kk
                    yield from keys(vv)
            elif isinstance(o, list):
                for vv in o:
                    yield from keys(vv)
        if any(p in str(k).lower() for k in keys(ev)):
            problems.append("purpose name in a key")
    if (ev.get("brief") or {}).get("required_sections"):
        problems.append("required sections visible in a purpose world")
    for a in ((ev.get("objective_options") or {}).get("initial") or []) + ((ev.get("objective_options") or {}).get("at_cut") or []):
        if isinstance(a, dict) and a.get("goal_owner") in PURPOSES:
            problems.append("purpose in an option's goal owner")
            break
    return problems


def _selftest() -> list[str]:
    fails = []
    register()
    seen = set()
    eq = 0
    n = 0
    for i in range(1, 60):
        w = make_pu_world(f"S8P|essay|s0|w{i:05d}|pilot", "essay")
        if w["degenerate"]:
            continue
        n += 1
        seen.add(w["purpose"])
        key = f"{w['purpose']}|{w['state']['names']['law']}|{w['state']['names']['belief']}|{w['state']['names']['residue']}"
        if key not in w["hidden"]["equivalence_class"]:
            fails.append(f"{w['lid']}: the truth is not in its own purpose class")
        if len(w["hidden"]["purpose_class"]) > 1:
            eq += 1
        if n >= 20:
            break
    if seen != set(PURPOSES):
        fails.append(f"purposes seen {sorted(seen)}")
    if eq == 0:
        fails.append("no equivalence world among twenty (the pair construction failed)")
    return fails
