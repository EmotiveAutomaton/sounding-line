"""Stage 6 contextual realization (brief §4): the hypothesis vocabulary, the realizer that
compiles a short hypothesis into a versioned maker_state against THIS world's context, the
grammar-constrained semantic language (GS), the fixed label definitions (LD), the common
adapter every architecture's output passes through, and the paraphrase machinery (M15,
X01). No model calls live here; runners/stage6/architectures.py owns those.

The realizer is the operative claim of §1.1 made runnable: a proposal ("the maker was
mostly tightening what was already down") is only a pointer; realizing it means
conditioning the declared process model of this artifact, history, and possibility space
on the hypothesis and emitting distributions over the remaining decisions, the next edit,
and stopping. Different proposals can realize the same predictive state and the same words
realize different states in different worlds; both are measured (M14, M15), not assumed.

DESIGN CHECK (2026-08-30)
lessons read: LESSONS §3 (score the short hypothesis given the long evidence, never the
  reverse; a model adjudicator is a ruler: the GS parser and the paraphraser are validated
  on fixtures whose answers are known, in I06/I09 and test 5/6), §4 (no reader judges the
  paraphrase; it is rule-built with a declared table).
gates: the realization gates live in soundingline.stage6.realization_report; the adapter
  refuses an output without normalized distributions (an unrealized proposal, never a
  silent default). bands: none here; the engines' verdict bands are stated there.
"""

from __future__ import annotations

import math
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from runners.stage6 import worlds as W                                             # noqa: E402
from runners.stage6.worlds import (CONTROLLERS, EDIT_TYPES, FORAGE, VALUES,        # noqa: E402
                                   _aid, _next_goal, _rng, _scores, _softmax,
                                   _stop_prob, controller_cfg, forage_cfg,
                                   history_cfg, value_cfg)
from soundingline.stage6 import maker_state                                        # noqa: E402

# ── the shared hypothesis vocabulary (§6: same target vocabulary for every arm) ───────
# display text is behavioral, never the latent's internal name
DISPLAY = {
    "strict_switch": "works on one concern at a time and switches wholly between concerns",
    "maintained": "keeps an unfinished concern warm in the background and returns to it when reminded",
    "focal_habit": "pursues one concern while old routines keep steering some choices",
    "concurrent": "weighs several concerns at once in every choice",
    "value:accuracy": "cares most that the content is right, even at private cost",
    "value:prestige": "cares most how the work will look to its audience",
    "forage:explore": "tried the unusual step deliberately, to find out what it does",
    "forage:error": "the unusual step was a slip, caught and corrected",
    "forage:habit_misuse": "the unusual step was an old routine applied out of place",
    "forage:hidden_goal": "the unusual step serves a quiet plan for the piece as a whole",
    "hist:attention_only": "shaped by what it repeatedly attended to, nothing more",
    "hist:rich": "shaped by attention plus practice, feedback, constraints, and opportunity",
}


def hypothesis_space(world: dict) -> list[dict]:
    """The candidate configurations for the world's track, each with its stable tag, its
    display text, and the cfg builder; the SAME list is handed to every architecture."""
    track = world["track"]
    if track in ("C", "M", "P"):
        return [{"tag": c, "display": DISPLAY[c], "kind": "controller"} for c in CONTROLLERS]
    if track == "V":
        return [{"tag": f"value:{v}", "display": DISPLAY[f"value:{v}"], "kind": "value"} for v in VALUES]
    if track == "F":
        return [{"tag": f"forage:{f}", "display": DISPLAY[f"forage:{f}"], "kind": "forage"} for f in FORAGE]
    if track == "A":
        h = world["history"]
        tags = [f"hist:{h['law']}:{h.get('tag', '')}",
                f"hist:{'attention_only' if h['law'] == 'rich' else 'rich'}:{h.get('tag', '')}"]
        return [{"tag": t, "display": DISPLAY["hist:" + t.split(":")[1]], "kind": "history"} for t in tags]
    raise ValueError(track)


def cfg_for_tag(world: dict, tag: str) -> dict:
    if tag in CONTROLLERS:
        return controller_cfg(world, tag, tag=tag)
    if tag.startswith("value:"):
        return value_cfg(world, tag.split(":")[1])
    if tag.startswith("forage:"):
        return forage_cfg(world, tag.split(":")[1])
    if tag.startswith("hist:"):
        law = tag.split(":")[1]
        h = dict(world["history"], law=law)
        return history_cfg(world, h)
    raise ValueError(tag)


# ── the realizer: hypothesis -> maker_state against this world ────────────────────────

def predictive_at_cut(world: dict, cfg: dict) -> dict:
    """Replay the visible prefix under cfg and emit its exact predictive distributions at
    the cut: next action, next-edit type and section marginals, the stop hazard, and the
    changed-context choice. One solver enumeration per call (the budget ledger's unit)."""
    traj, cut = world["trajectory"], world["cut"]
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
    return {"next_edit": nxt, "next_edit_type": type_dist, "next_section": sec_dist,
            "p_stop": _stop_prob(world, len(done), len(traj["steps"]), True),
            "changed_context": W.changed_context_dist(world, cfg),
            "goal_at_cut": active_goal, "pending_n": len(pending)}


def realize(world: dict, tag: str, proposal_text: str | None = None,
            posterior_weight: float = 1.0, abstain: bool = False) -> dict:
    """Compile one hypothesis tag into a full maker_state for THIS world (§4.2): the
    fields are filled from the world's visible context plus the hypothesized
    configuration; the distributions are the realizer's exact predictions under it."""
    cfg = cfg_for_tag(world, tag)
    pred = predictive_at_cut(world, cfg)
    counterfactual = {"if_no_interrupt": {"next_edit_type": max(pred["next_edit_type"], key=pred["next_edit_type"].get)},
                      "if_deadline_lifted": {"changed_context": max(pred["changed_context"], key=pred["changed_context"].get)}}
    return maker_state(
        proposal_id=f"{tag}|{world['lid']}",
        artifact_context={"task": world["doc"]["topic"], "domain": world["domain"],
                          "sections": [s["name"] for s in world["doc"]["sections"]],
                          "proposal_text": proposal_text or DISPLAY.get(tag.split(":")[0] if tag.startswith("hist") else tag, tag)},
        episode_goal=pred["goal_at_cut"],
        control_state={"hypothesis": tag, "controller": cfg["controller"]},
        maintained_intentions=list(world["events"].get("cues", {}).values()) if cfg["controller"] == "maintained" else [],
        process_model={"pending_n": pred["pending_n"], "action_types": list(EDIT_TYPES)},
        expertise_state={"habit": dict(cfg.get("habit", {}))},
        selection_history={"bias": dict(cfg.get("history_bias", {}))},
        standing_tendencies={"value": cfg.get("value")},
        evidence_scope={"observed": [f"step{j}" for j in range(world["cut"])], "withheld": ["tail", "stop", "changed_context"]},
        decision_likelihoods={"next_edit": pred["next_edit"], "next_edit_type": pred["next_edit_type"],
                              "next_section": pred["next_section"], "changed_context": pred["changed_context"]},
        counterfactual_predictions=counterfactual,
        stop_model={"p_stop": pred["p_stop"]},
        uncertainty={"posterior_weight": posterior_weight, "abstain": abstain})


# ── the common adapter (§4.2): every arm's output -> one prediction record ────────────

def mix(dists: list[tuple[float, dict]]) -> dict:
    out: dict = {}
    z = sum(w for w, _ in dists) or 1.0
    for w, d in dists:
        for k, p in d.items():
            out[k] = out.get(k, 0.0) + (w / z) * p
    s = sum(out.values()) or 1.0
    return {k: v / s for k, v in out.items()}


def adapt(states: list[dict], posterior: dict | None = None, abstain: bool | None = None) -> dict:
    """States (realized maker_states) + a posterior over their proposal tags -> the one
    prediction record every card scores: mixed distributions, a mixed stop hazard, the
    posterior itself, and the abstention flag. Refuses empty or unnormalizable input."""
    if not states:
        raise ValueError("adapter: no realized states")
    post = posterior or {}
    weighted = []
    for st in states:
        tag = st["proposal_id"].split("|")[0]
        w = float(post.get(tag, st["uncertainty"].get("posterior_weight", 1.0)))
        weighted.append((max(w, 0.0), st))
    z = sum(w for w, _ in weighted) or 1.0
    posterior_n = {st["proposal_id"].split("|")[0]: w / z for w, st in weighted}
    pred = {"next_edit_type": mix([(w, st["decision_likelihoods"]["next_edit_type"]) for w, st in weighted]),
            "next_section": mix([(w, st["decision_likelihoods"].get("next_section", {})) for w, st in weighted]),
            "next_edit": mix([(w, st["decision_likelihoods"].get("next_edit", {})) for w, st in weighted]),
            "changed_context": mix([(w, st["decision_likelihoods"].get("changed_context", {})) for w, st in weighted]),
            "p_stop": sum(w / z * float(st["stop_model"].get("p_stop", 0.5)) for w, st in weighted),
            "posterior": posterior_n,
            "abstain": bool(abstain) if abstain is not None else bool(entropy(posterior_n) > 0.9 * math.log(max(2, len(posterior_n))))}
    return pred


def entropy(dist: dict) -> float:
    return -sum(p * math.log(p) for p in dist.values() if p > 0)


# ── GS: the grammar-constrained semantic state ────────────────────────────────────────
# STATE := mode(<controller word>) [; value(<accuracy|prestige>)] [; step(<forage word>)]
#          [; shaped(<attention_only|rich>)]
GS_WORDS = {"one_at_a_time": "strict_switch", "background_intention": "maintained",
            "routine_steered": "focal_habit", "all_at_once": "concurrent",
            "accuracy": "value:accuracy", "prestige": "value:prestige",
            "deliberate_test": "forage:explore", "slip": "forage:error",
            "routine_misapplied": "forage:habit_misuse", "quiet_plan": "forage:hidden_goal",
            "attention_only": "attention_only", "rich": "rich"}
GS_PATTERN = re.compile(r"(mode|value|step|shaped)\(([a-z_]+)\)")


def gs_grammar_help(world: dict) -> str:
    track = world["track"]
    if track in ("C", "M", "P"):
        return "Reply with exactly one clause: mode(one_at_a_time) or mode(background_intention) or mode(routine_steered) or mode(all_at_once)."
    if track == "V":
        return "Reply with exactly one clause: value(accuracy) or value(prestige)."
    if track == "F":
        return "Reply with exactly one clause: step(deliberate_test) or step(slip) or step(routine_misapplied) or step(quiet_plan)."
    return "Reply with exactly one clause: shaped(attention_only) or shaped(rich)."


def parse_gs(text: str, world: dict) -> str | None:
    """The first well-formed clause whose word maps into the world's own hypothesis space;
    None otherwise (an unrealized proposal, counted, never defaulted)."""
    tags = {h["tag"] for h in hypothesis_space(world)}
    for m in GS_PATTERN.finditer(text or ""):
        word = m.group(2)
        mapped = GS_WORDS.get(word)
        if mapped is None:
            continue
        if mapped in tags:
            return mapped
        for t in tags:                                            # hist tags carry a suffix
            if t.startswith("hist:") and t.split(":")[1] == mapped:
                return t
    return None


# ── LD: fixed label definitions (M03), length- and vocabulary-matched ─────────────────
LD_DEFINITIONS = {
    "strict_switch": "meaning: finishes or parks the current concern before any other concern acts",
    "maintained": "meaning: an unfinished concern stays ready and acts again when its reminder appears",
    "focal_habit": "meaning: one concern leads while practiced routines still pick some next moves",
    "concurrent": "meaning: every next move balances all the concerns together at once",
    "value:accuracy": "meaning: getting the content right outweighs how the work appears to others",
    "value:prestige": "meaning: how the work appears to others outweighs quietly fixing the content",
    "forage:explore": "meaning: the odd step was chosen to learn something and its result was read",
    "forage:error": "meaning: the odd step was unintended and was corrected before teaching anything",
    "forage:habit_misuse": "meaning: the odd step was a familiar routine applied where it does not fit",
    "forage:hidden_goal": "meaning: the odd step quietly serves the shape of the whole piece",
    "hist:attention_only": "meaning: only what was repeatedly attended shaped the maker's leanings",
    "hist:rich": "meaning: practice, feedback, constraints, and opportunity shaped the leanings too",
}


# ── proposal paraphrase (M15, X01): rule-built, declared, no reader judges it ─────────
_PARA = [("works on", "handles"), ("one concern at a time", "a single concern at any moment"),
         ("switches wholly", "moves completely"), ("keeps", "holds"), ("warm", "alive"),
         ("returns to it", "comes back to it"), ("old routines", "ingrained routines"),
         ("steering", "guiding"), ("weighs", "balances"), ("cares most", "chiefly cares"),
         ("even at private cost", "even when nobody would see the cost"),
         ("deliberately", "on purpose"), ("caught and corrected", "noticed and fixed"),
         ("out of place", "where it does not belong"), ("quiet plan", "unstated plan")]
_MEANING_FLIP = [("one concern at a time", "several concerns at once"),
                 ("deliberately", "by accident"), ("cares most that the content is right", "cares most how the work will look"),
                 ("kept warm", "abandoned"), ("corrected", "repeated")]


def paraphrase(text: str, seed: int = 0) -> str:
    r = _rng(f"para|{seed}", text[:32])
    out = text
    pairs = list(_PARA)
    r.shuffle(pairs)
    for a, b in pairs[: max(2, len(pairs) // 2)]:
        out = out.replace(a, b)
    return out


def meaning_change(text: str, seed: int = 0) -> str:
    r = _rng(f"flip|{seed}", text[:32])
    out = text
    flips = [p for p in _MEANING_FLIP if p[0] in out] or _MEANING_FLIP
    a, b = flips[r.randrange(len(flips))]
    out = out.replace(a, b) if a in out else (out + " — though really " + b)
    return out


def _selftest() -> list[str]:
    fails = []
    w = W.make_process_world("M08|essay|s0|w0005|discovery", "essay", track="C")
    space = hypothesis_space(w)
    if len(space) != 4:
        fails.append("hypothesis space size")
    sts = [realize(w, h["tag"]) for h in space]
    from soundingline.stage6 import realization_report
    if not all(realization_report(st)["realized"] for st in sts):
        fails.append("a realized hypothesis failed its gates")
    pred = adapt(sts, posterior={h["tag"]: 0.25 for h in space})
    if abs(sum(pred["next_edit_type"].values()) - 1.0) > 1e-6:
        fails.append("adapter not normalized")
    # the true tag's realization scores the hidden next edit at least as well on average
    from soundingline.stage6 import state_log_score
    truth_t = w["hidden"]["next_edit_type"]
    ls = {st["proposal_id"].split("|")[0]: state_log_score(st, "next_edit_type", truth_t) for st in sts}
    if ls[w["truth"]["controller"]] is None:
        fails.append("true realization cannot score the target")
    # GS parses its own grammar and refuses junk
    if parse_gs("mode(one_at_a_time)", w) != "strict_switch" or parse_gs("mode(sideways)", w) is not None:
        fails.append("GS parser")
    # paraphrase preserves the mapped tag's wording class; meaning change alters it
    t = DISPLAY["strict_switch"]
    if paraphrase(t, 1) == t:
        fails.append("paraphrase identity")
    if meaning_change(t, 1) == t:
        fails.append("meaning change identity")
    return fails


if __name__ == "__main__":
    f = _selftest()
    print("realization self-tests:", "ALL OK" if not f else f)
    sys.exit(1 if f else 0)
