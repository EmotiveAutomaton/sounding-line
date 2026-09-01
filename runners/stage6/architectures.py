"""Stage 6 architecture arms (brief §6): the nine estimators, every one taking the SAME
evidence (the rendered artifact and process prefix) and target vocabulary, each with a
recorded compute-budget row. The model calls live here; the representation machinery is
runners/stage6/realization.py; the exact machinery is the world's own.

The arms:
  D   direct monolithic reader: forced-choice likelihoods on the targets, no state.
  L   label-only augmented inverse planning: the reader weighs the hypothesis labels
      given the evidence; each label is realized EXACTLY and the predictions are the
      posterior mixture (the comparator of arXiv:2507.03682, on our vocabulary).
  LD  L plus fixed definitions (length- and vocabulary-matched) appended to each label.
  TT  free-language weighted particles: the label posteriors re-weighed at three
      checkpoints along the prefix; collapse recorded (the ThoughtTracing comparator).
  GS  grammar-constrained semantic state: the reader must emit one clause of the bounded
      language; unparseable output is an unrealized proposal (the LaBToM warning).
  EX  synthesized executable maker model: a SIMPLIFIED fitted policy per hypothesis
      (type-frequency Markov policy with a goal-utility prior), inverted sequentially;
      distinct from the exact realizer by construction (the LIRAS comparator).
  AD  adaptive structure: starts controller-agnostic; adds the controller variable, then
      the history residue, only when the predeclared utility gate fails (the AutoToM
      comparator; false expansions on complete worlds are the M07 cost).
  CR  Sounding contextual realization: reader proposals in free language, mapped into
      the shared vocabulary, realized in full against the world context, weighed by the
      reader, with abstention exposed.
  OR  the exact oracle (construction ceiling, never a competitor).

DESIGN CHECK (2026-08-30)
lessons read: LESSONS §3 (match the readout class: the reader weighs SHORT hypothesis
  text given LONG evidence via next-token likelihood, the direction L278 proved usable;
  fixed option order per unit across arms — the L283 lesson — so every likelihood call
  seeds its order from the world id, never from arm identity), §4 (instruct readers only),
  §5 (one GPU session per card invocation, owned by the engine, not by the arms).
gates: budget parity is I07's (the ledger rows written per call); the realization gates
  are stage6's; the capability gate is I05's. bands: the engines'.
"""

from __future__ import annotations

import math
import random
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from runners import s5_lib                                                         # noqa: E402
from runners.stage6 import realization as R                                        # noqa: E402
from runners.stage6 import worlds as W                                             # noqa: E402
from runners.stage6.worlds import CC_OPTIONS, EDIT_TYPES                           # noqa: E402
from soundingline.stage6 import add_budget, budget_row                             # noqa: E402

BUDGET_SMALL = {"model_calls": 14, "tokens_out": 96}    # matched small budget (§6); sized for
BUDGET_EXPANDED = {"model_calls": 28, "tokens_out": 192}  # the order-marginalized label posterior
TT_CHECKPOINTS = 3


class Budget:
    def __init__(self, cap: dict | None = None):
        self.cap = cap or BUDGET_SMALL
        self.row = budget_row()
        self.t0 = time.time()

    def charge_call(self, tokens_in: int = 0, tokens_out: int = 0, forward: int = 1):
        self.row = add_budget(self.row, budget_row(model_calls=1, tokens_in=tokens_in,
                                                   tokens_out=tokens_out, forward_passes=forward))

    def charge_solver(self, n: int = 1):
        self.row = add_budget(self.row, budget_row(solver_enumerations=n))

    def over(self) -> bool:
        return self.row["model_calls"] > self.cap.get("model_calls", 10 ** 9)

    def close(self) -> dict:
        self.row["wall_s"] = round(time.time() - self.t0, 3)
        return dict(self.row)


def _order_rng(world: dict, salt: str = "order") -> random.Random:
    """Fixed option order PER WORLD shared by every arm (the L283 lesson): the seed never
    contains the arm's identity."""
    return W._rng(world["lid"], f"arm-{salt}")


def _ntokens(text: str) -> int:
    return max(1, len(text) // 4)


def _likelihood(model, tok, body: str, options: dict, world: dict, budget: Budget, salt: str) -> dict:
    r = s5_lib.candidate_likelihood(model, tok, body, options, _order_rng(world, salt), unknown=False)
    budget.charge_call(tokens_in=_ntokens(body))
    return r


def _likelihood_any(model, tok, body: str, options: dict, world: dict, budget: Budget, salt: str) -> dict:
    """The letter readout for candidate sets past the six balanced labels: the set is split
    into seeded groups of at most six, each group scored, the top three of each group meet
    in a final of at most six, and every candidate's probability is its group mass times
    its final mass (non-finalists carry their group mass times the final's floor share).
    One declared composition rule for every arm; the group split is seeded by the world id,
    never by the arm (the L283 lesson)."""
    if len(options) <= len(s5_lib.LETTERS):
        return _likelihood(model, tok, body, options, world, budget, salt)
    keys = sorted(options)
    _order_rng(world, salt + "|split").shuffle(keys)
    groups = [keys[i::2] for i in range(2)] if len(keys) <= 12 else [keys[i::3] for i in range(3)]
    group_probs: dict = {}
    finalists: list = []
    for gi, g in enumerate(groups):
        rr = _likelihood(model, tok, body, {k: options[k] for k in g}, world, budget, f"{salt}|g{gi}")
        probs = rr["probs"] if rr["valid"] else {k: 1.0 / len(g) for k in g}
        for k in g:
            group_probs[k] = probs.get(k, 0.0)
        finalists += [k for k, _ in sorted(probs.items(), key=lambda kv: -kv[1])[:3]]
    fr = _likelihood(model, tok, body, {k: options[k] for k in finalists[:len(s5_lib.LETTERS)]},
                     world, budget, f"{salt}|final")
    fprobs = fr["probs"] if fr["valid"] else {k: 1.0 / len(finalists) for k in finalists}
    floor = min(fprobs.values()) * 0.5 if fprobs else 0.1
    out = {}
    for k in keys:
        out[k] = max(group_probs.get(k, 0.0), 1e-9) * (fprobs.get(k, floor) if k in fprobs else floor)
    z = sum(out.values())
    out = {k: v / z for k, v in out.items()}
    return {"valid": True, "probs": out, "pred": max(out, key=out.get),
            "labels": None, "parser": "s6-tournament-likelihood-1.0",
            "validity_reason": "ok", "composed": True}


def _weigh_labels(model, tok, world: dict, evidence: str, space: list[dict], budget: Budget,
                  with_definitions: bool = False, upto: int | None = None) -> dict:
    """The reader's posterior over the hypothesis labels given the evidence:
    forced-choice likelihood over the display texts (short hypotheses scored given the
    long evidence), POSITION-BALANCED: the candidates are canonically ordered by tag and
    scored under every cyclic rotation of that order (each candidate in each position
    exactly once, deterministic, no shuffle), the probabilities averaged. These readers
    carry a letter-position effect of order two nats (the Stage-5 L283/L260 record; the
    first Stage-6 smokes measured a single-order posterior moving by 0.74 TV under a bare
    permutation and 0.37 under three sampled orders), so the position component is
    cancelled by balance rather than sampled; the input list's order cannot matter at all
    (the canonical sort makes the estimator order-invariant by construction, which is the
    property X02 then guards against regression)."""
    ordered = sorted(space, key=lambda h: h["tag"])
    opts_txt = {}
    for h in ordered:
        txt = h["display"]
        if with_definitions:
            d = R.LD_DEFINITIONS.get(h["tag"])
            if d is None and ":" in h["tag"]:
                d = R.LD_DEFINITIONS.get("hist:" + h["tag"].split(":")[1])
            txt = f"{txt} ({d or ''})"
        opts_txt[h["tag"]] = txt
    tags = [h["tag"] for h in ordered]
    body = (f"{evidence}\n\nWhich description best fits how this maker was working?")
    acc = {t: 0.0 for t in tags}
    got = 0
    for k in range(len(tags)):
        rot = tags[k:] + tags[:k]
        rr = s5_lib.likelihood_choice(model, tok, body, {t: opts_txt[t] for t in rot},
                                      _order_rng(world, f"labels|{upto}|r{k}"), shuffle=False)
        budget.charge_call(tokens_in=_ntokens(body))
        if rr["valid"]:
            got += 1
            for t in acc:
                acc[t] += rr["probs"].get(t, 0.0)
    if not got:
        return {t: 1.0 / len(tags) for t in tags}
    return {t: v / got for t, v in acc.items()}


# ── the arms ──────────────────────────────────────────────────────────────────────────

def arm_D(model, tok, world: dict, budget: Budget) -> dict:
    ev = W.render_evidence(world) + "\n\n" + W.render_artifact(world)
    t = _likelihood_any(model, tok, ev + "\n\nWhat kind of step does the maker take NEXT?",
                        {k: {"write": "putting down a new part", "revise": "reworking an existing part",
                             "check": "going back over a part", "consult": "looking something up",
                             "cite": "adding a reference", "probe": "trying an unusual step",
                             "fix": "correcting something"}[k] for k in EDIT_TYPES}, world, budget, "d-type")
    secs = {s["name"]: f"the part called {s['name']}" for s in world["doc"]["sections"]}
    sc = _likelihood(model, tok, ev + "\n\nWhere does the maker work next?", secs, world, budget, "d-sec")
    st = _likelihood(model, tok, ev + "\n\nAt the next natural pause, does the maker stop for good?",
                     {"stop": "stops here", "continue": "keeps going"}, world, budget, "d-stop")
    cc = _likelihood(model, tok, ev + f"\n\nSuppose {world['hidden']['changed_context']['context_change']}. What does the maker do?",
                     {k: k.replace("_", " ") for k in CC_OPTIONS}, world, budget, "d-cc")
    pred = {"next_edit_type": t["probs"] if t["valid"] else {k: 1 / len(EDIT_TYPES) for k in EDIT_TYPES},
            "next_section": sc["probs"] if sc["valid"] else {k: 1 / len(secs) for k in secs},
            "next_edit": {}, "changed_context": cc["probs"] if cc["valid"] else {k: 1 / len(CC_OPTIONS) for k in CC_OPTIONS},
            "p_stop": (st["probs"].get("stop", 0.5) if st["valid"] else 0.5),
            "posterior": {}, "abstain": False}
    return {"predictions": pred, "states": [], "posterior": {}, "notes": {"valid": all(x["valid"] for x in (t, sc, st, cc))}}


def _label_arm(model, tok, world: dict, budget: Budget, with_definitions: bool) -> dict:
    ev = W.render_evidence(world) + "\n\n" + W.render_artifact(world)
    space = R.hypothesis_space(world)
    post = _weigh_labels(model, tok, world, ev, space, budget, with_definitions=with_definitions)
    states = []
    for h in space:
        budget.charge_solver()
        states.append(R.realize(world, h["tag"], posterior_weight=post.get(h["tag"], 0.0)))
    pred = R.adapt(states, posterior=post)
    return {"predictions": pred, "states": states, "posterior": post, "notes": {}}


def arm_L(model, tok, world: dict, budget: Budget) -> dict:
    return _label_arm(model, tok, world, budget, with_definitions=False)


def arm_LD(model, tok, world: dict, budget: Budget) -> dict:
    return _label_arm(model, tok, world, budget, with_definitions=True)


def arm_TT(model, tok, world: dict, budget: Budget) -> dict:
    """Weighted particles: the label posterior re-weighed at three prefix checkpoints by
    multiplying the reader's per-checkpoint weights; collapse = the entropy path."""
    space = R.hypothesis_space(world)
    cut = world["cut"]
    weights = {h["tag"]: 1.0 / len(space) for h in space}
    entropy_path = []
    for k in range(1, TT_CHECKPOINTS + 1):
        upto = max(2, int(cut * k / TT_CHECKPOINTS))
        ev = W.render_evidence(world, upto=upto)
        post = _weigh_labels(model, tok, world, ev, space, budget, upto=upto)
        weights = {t: weights[t] * max(post.get(t, 1e-6), 1e-6) for t in weights}
        z = sum(weights.values())
        weights = {t: v / z for t, v in weights.items()}
        entropy_path.append(round(R.entropy(weights), 4))
    states = []
    for h in space:
        budget.charge_solver()
        states.append(R.realize(world, h["tag"], posterior_weight=weights[h["tag"]]))
    pred = R.adapt(states, posterior=weights)
    collapsed = entropy_path[-1] < 0.15 * math.log(len(space))
    return {"predictions": pred, "states": states, "posterior": weights,
            "notes": {"entropy_path": entropy_path, "collapsed": collapsed}}


def arm_GS(model, tok, world: dict, budget: Budget) -> dict:
    ev = W.render_evidence(world) + "\n\n" + W.render_artifact(world)
    body = f"{ev}\n\nDescribe how this maker was working, in the fixed form. {R.gs_grammar_help(world)}"
    g = s5_lib.generate(model, tok, body, seed=W._widx(world["lid"]) + 61000, max_new=24, greedy=True)
    budget.charge_call(tokens_in=_ntokens(body), tokens_out=24)
    tag = R.parse_gs(g["text"], world)
    if tag is None:
        return {"predictions": None, "states": [], "posterior": {},
                "notes": {"unrealized": True, "raw": g["text"][:120]}}
    budget.charge_solver()
    st = R.realize(world, tag, posterior_weight=1.0)
    pred = R.adapt([st], posterior={tag: 1.0}, abstain=False)
    return {"predictions": pred, "states": [st], "posterior": {tag: 1.0}, "notes": {"raw": g["text"][:120]}}


def _fit_markov_policy(world: dict, upto: int) -> dict:
    """EX's simplified executable model: type-transition counts from the visible prefix
    with add-one smoothing (the synthesized local model; deliberately weaker than the
    exact realizer)."""
    steps = world["trajectory"]["steps"][:upto]
    trans: dict = {}
    for a, b in zip(steps, steps[1:]):
        key = a["action"]["type"]
        trans.setdefault(key, {})
        trans[key][b["action"]["type"]] = trans[key].get(b["action"]["type"], 0) + 1
    return trans


def arm_EX(model, tok, world: dict, budget: Budget) -> dict:
    """Executable synthesis: reader posterior over hypotheses (as L), but predictions from
    the fitted Markov policy modulated by the hypothesis's goal-utility prior."""
    ev = W.render_evidence(world) + "\n\n" + W.render_artifact(world)
    space = R.hypothesis_space(world)
    post = _weigh_labels(model, tok, world, ev, space, budget)
    trans = _fit_markov_policy(world, world["cut"])
    budget.charge_solver(len(space))
    last = world["trajectory"]["steps"][world["cut"] - 1]["action"]["type"]
    row = trans.get(last, {})
    states = []
    for h in space:
        cfg = R.cfg_for_tag(world, h["tag"])
        goal = cfg.get("start_goal", "produce")
        dist = {}
        for t in EDIT_TYPES:
            prior = math.exp(0.5 * W.GOAL_UTIL[goal][t])
            dist[t] = (row.get(t, 0) + 1.0) * prior
        z = sum(dist.values())
        dist = {k: v / z for k, v in dist.items()}
        exact = R.realize(world, h["tag"], posterior_weight=post.get(h["tag"], 0.0))
        exact["decision_likelihoods"]["next_edit_type"] = dist          # the simplified model's marginal
        exact["proposal_id"] = f"{h['tag']}|{world['lid']}"
        states.append(exact)
    pred = R.adapt(states, posterior=post)
    return {"predictions": pred, "states": states, "posterior": post, "notes": {"model": "markov+goal-prior"}}


AD_GATE_NATS = 0.10     # predeclared utility gate: expand only when the simpler model trails by this


def arm_AD(model, tok, world: dict, budget: Budget) -> dict:
    """Adaptive expansion: level 0 is controller-agnostic (uniform mixture); level 1 adds
    the controller variable when level 0's prefix likelihood trails the best single
    hypothesis by the gate; the expansions taken are recorded (M07's cost measure)."""
    space = R.hypothesis_space(world)
    budget.charge_solver(len(space) + 1)
    lls = {h["tag"]: W.trajectory_log_lik(world, R.cfg_for_tag(world, h["tag"]), world["trajectory"], upto=world["cut"])
           for h in space}
    mx = max(lls.values())
    mixture_ll = mx + math.log(sum(math.exp(v - mx) for v in lls.values()) / len(lls))
    expansions = []
    if mx - mixture_ll > AD_GATE_NATS:
        expansions.append("controller_variable")
        if model is not None:
            ev = W.render_evidence(world) + "\n\n" + W.render_artifact(world)
            post = _weigh_labels(model, tok, world, ev, space, budget)
        else:
            post = {h["tag"]: 1.0 for h in space}                 # no reader: the exact likelihoods carry it
        z = sum(post.get(h["tag"], 0) * math.exp(lls[h["tag"]] - mx) for h in space) or 1.0
        post = {h["tag"]: post.get(h["tag"], 0) * math.exp(lls[h["tag"]] - mx) / z for h in space}
    else:
        post = {h["tag"]: 1.0 / len(space) for h in space}
    states = [R.realize(world, h["tag"], posterior_weight=post[h["tag"]]) for h in space]
    pred = R.adapt(states, posterior=post)
    return {"predictions": pred, "states": states, "posterior": post,
            "notes": {"expansions": expansions, "gate_margin_nats": round(mx - mixture_ll, 4)}}


def arm_CR(model, tok, world: dict, budget: Budget) -> dict:
    """Sounding contextual realization: a free-language proposal from the reader, mapped
    into the shared vocabulary; the reader's label posterior; every candidate realized in
    full against the world context; abstention exposed when the posterior stays flat."""
    ev = W.render_evidence(world) + "\n\n" + W.render_artifact(world)
    body = (f"{ev}\n\nIn one short sentence: what was driving how this maker worked "
            f"(its way of handling concerns, not the topic)?")
    g = s5_lib.generate(model, tok, body, seed=W._widx(world["lid"]) + 62000, max_new=40, greedy=True)
    budget.charge_call(tokens_in=_ntokens(body), tokens_out=40)
    proposal = (g["text"] or "").strip().split("\n")[0][:200]
    space = R.hypothesis_space(world)
    post = _weigh_labels(model, tok, world, ev + f"\n\nYour own reading was: \"{proposal}\"", space, budget)
    states = []
    for h in space:
        budget.charge_solver()
        states.append(R.realize(world, h["tag"], proposal_text=proposal, posterior_weight=post.get(h["tag"], 0.0)))
    abstain = R.entropy(post) > 0.9 * math.log(len(space))
    pred = R.adapt(states, posterior=post, abstain=abstain)
    return {"predictions": pred, "states": states, "posterior": post,
            "notes": {"proposal": proposal, "abstain": abstain}}


def arm_OR(model, tok, world: dict, budget: Budget) -> dict:
    budget.charge_solver(len(R.hypothesis_space(world)))
    st = W.oracle_state(world)
    post = W.oracle_posterior(world)
    pred = R.adapt([st], posterior=None, abstain=max(post.values()) < 0.5)
    pred["posterior"] = post
    return {"predictions": pred, "states": [st], "posterior": post, "notes": {"oracle": True}}


ARMS = {"D": arm_D, "L": arm_L, "LD": arm_LD, "TT": arm_TT, "GS": arm_GS,
        "EX": arm_EX, "AD": arm_AD, "CR": arm_CR, "OR": arm_OR}


def run_arm(arch: str, model, tok, world: dict, budget_cap: dict | None = None) -> dict:
    """One architecture on one world under one budget; returns predictions, realized
    states, the posterior, the notes, and the closed budget row. The evidence hash the
    I07 parity audit compares is the rendered evidence string's hash."""
    import hashlib                                                                # noqa: PLC0415
    b = Budget(budget_cap)
    out = ARMS[arch](model, tok, world, b)
    out["arch"] = arch
    out["budget"] = b.close()
    out["evidence_sha"] = hashlib.sha256((W.render_evidence(world) + W.render_artifact(world)).encode()).hexdigest()[:16]
    out["over_budget"] = b.over()
    return out


def _selftest() -> list[str]:
    """CPU-only: the no-model arms (OR, AD's exact half) run without a reader; the model
    arms are exercised in I06's fixtures with a loaded reader."""
    fails = []
    w = W.make_process_world("M09|essay|s0|w0002|discovery", "essay", track="C")
    out = run_arm("OR", None, None, w)
    p = out["predictions"]
    if abs(sum(p["next_edit_type"].values()) - 1.0) > 1e-6 or not (0 <= p["p_stop"] <= 1):
        fails.append("OR adapter shape")
    if out["budget"]["solver_enumerations"] < 1:
        fails.append("OR budget row")
    truth = w["truth"]["controller"]
    full_post = W.oracle_posterior(w, upto=len(w["trajectory"]["steps"]))
    if max(full_post, key=full_post.get) != truth and full_post[truth] < 0.2:
        fails.append(f"oracle posterior far from truth: {full_post}")
    return fails


if __name__ == "__main__":
    f = _selftest()
    print("architecture self-tests:", "ALL OK" if not f else f)
    sys.exit(1 if f else 0)
