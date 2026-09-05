"""The artful gradient (brief §5 AG) and the general extended world builder every Stage 8
family uses. Three task shapes under the same law family: a required-sections report
(structured: five sections of two slots, every section required, an editor audience), the
Stage 7 essay shape between, and a free draft with few requirements (two sections of four
slots, one required, the maker's own audience). The oracle-minus-DOM gap per shape, declared
before any reader, is the stage's first measurement of the maker's share as a function of
admitted decisions and sets the tail floors per shape (a construction fact, never a claim).

`make_world_ext` is the Stage 7 `make_world` with a shape, an optional goal that may be a
purpose (a registered utility table; every inventory action then belongs to it so the goal
holds across the artifact, the walkthrough's rule), and a residue scale (the maker series'
reveal parameter). Everything else (state, simulation, cut, hidden targets, oracle) is Stage
7's own code.

DESIGN CHECK (2026-09-04)
lessons read: LESSONS §3 (an exact ruler is validated on the construction it rules: the guard
  suite prints one world per shape and per purpose and checks the oracle gap; count the
  truth marginal of every hidden target on the constructed worlds before the clock: the
  construction facts cell counts stop truth, class sizes, and the tail share per shape;
  a counterfactual is counterfactual in every cell), §5.
gates: the construction gate (E01/construction facts): NULL of a dead ruler on a shape is a
  mean oracle-minus-DOM gap under MIN_GAP_NATS on next action (fails DOWN: that shape's
  tail floor is void and no reader is tested on it); ALTERNATIVE: at or above the floor.
bands: exhaustive (under / at or above).
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO))

from runners.stage7.constructor import worlds as W                                 # noqa: E402
from runners.stage7.reader import law as LAW                                       # noqa: E402

SHAPES = ("structured", "essay", "free")


def doc_plan(lid: str, domain: str, shape: str) -> dict:
    if shape == "essay":
        return W._doc_plan(lid, domain)
    r = W._rng(lid, f"doc|{shape}")
    topic = W.TOPICS[domain][r.randrange(len(W.TOPICS[domain]))]
    if shape == "structured":
        sections = [{"name": f"sec{s + 1}", "slots": [f"s{s + 1}.{k + 1}" for k in range(2)]} for s in range(5)]
    elif shape == "free":
        sections = [{"name": f"sec{s + 1}", "slots": [f"s{s + 1}.{k + 1}" for k in range(4)]} for s in range(2)]
    else:
        raise ValueError(shape)
    return {"domain": domain, "topic": topic, "sections": sections, "shape": shape}


def shape_forced_cext(doc: dict, shape: str) -> dict:
    names = [s["name"] for s in doc["sections"]]
    if shape == "structured":
        return {"brief_sections": list(names), "audience": "editor"}
    if shape == "free":
        return {"brief_sections": names[:1], "audience": "self"}
    return {}


def make_world_ext(lid: str, domain: str, shape: str = "essay", goal: str | None = None, law_name: str | None = None,
                   belief: str | None = None, residue: str | None = None, tendency: str | None = None,
                   forced_cext: dict | None = None, owner_all: str | None = None, residue_scale: float = 1.0,
                   finish: bool = True, salt: str = "traj", no_change: bool = False) -> dict:
    """A world of any shape; `owner_all` assigns every inventory action to one goal owner (a
    purpose world); `residue_scale` multiplies the habit strength (the reveal parameter);
    `finish=False` skips the cut and the hidden targets (training logs need the trajectory
    only)."""
    r = W._rng(lid, "factors")
    doc = doc_plan(lid, domain, shape)
    inventory = W._inventory(lid, doc)
    goal = goal or W.GOALS[r.randrange(len(W.GOALS))]
    law_name = law_name or W.LAW_NAMES[r.randrange(len(W.LAW_NAMES))]
    belief = belief or W.BELIEFS[r.randrange(len(W.BELIEFS))]
    residue = residue or W.RESIDUES[r.randrange(len(W.RESIDUES))]
    tendency = tendency or W.TENDENCIES[r.randrange(2)]
    if owner_all:
        for a in inventory:
            a["goal_owner"] = owner_all
    forced = dict(shape_forced_cext(doc, shape))
    forced.update(forced_cext or {})
    state = W.make_state(lid, doc, inventory, goal, law_name, belief, residue, tendency, forced)
    if residue_scale != 1.0:
        h = state["history_residue"]
        h["habit"] = {k: round(v * residue_scale, 4) for k, v in (h.get("habit") or {}).items()}
        if h.get("maintained") and residue_scale < 0.5:
            h["maintained"] = None
        state["reveal_scale"] = residue_scale
    traj = W.simulate(lid, doc, inventory, state, salt=salt, changes=([] if no_change else None))
    world = {"lid": lid, "domain": domain, "doc": doc, "inventory": inventory, "state": state,
             "trajectory": traj, "degenerate": None, "shape": shape, "no_change": no_change}
    if not finish:
        return world
    cut, weight = W._choose_cut(traj, lid)
    if cut is None:
        world["degenerate"] = "the boundary walk selected no cut"
        return world
    world = W._finish_world(world, cut, weight)
    if not world["degenerate"] and sum(world["oracle"]["next_action"].values()) < 0.5:
        world["degenerate"] = "no subjective option at the cut (the oracle has no next-action mass)"
    return world


def pull_ordering(utility: dict, law: dict) -> list[str]:
    """The derived pull ordering: action types by utility minus cost under the law."""
    cost = law.get("cost", {})
    return [t for t, _ in sorted(((t, float(utility.get(t, 0.0)) - float(cost.get(t, 0.0))) for t in LAW.ACTION_TYPES), key=lambda kv: -kv[1])]


def _selftest() -> list[str]:
    fails = []
    for shape in SHAPES:
        w = next((x for x in (make_world_ext(f"S8T|essay|s0|w{i:05d}|pilot", "essay", shape) for i in range(1, 30)) if not x["degenerate"]), None)
        if w is None:
            fails.append(f"no live world for shape {shape}")
            continue
        if abs(sum(w["oracle"]["next_action"].values()) - 1.0) > 1e-9:
            fails.append(f"{shape}: oracle does not sum to one")
        n_sec = len(w["doc"]["sections"])
        if (shape, n_sec) not in (("structured", 5), ("free", 2)) and shape != "essay":
            fails.append(f"{shape}: wrong section count {n_sec}")
    return fails
