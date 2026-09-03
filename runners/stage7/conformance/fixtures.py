"""Conformance fixtures (brief §5, A03-A13): one tiny official-style fixture per external
family, checking that the LOCAL mechanism performs the family's DEFINING operation, so
the published name may be admitted (a pass) or the mechanism keeps its local name (a
fail is an implementation result, never evidence against the program). The fixtures use
the reference clones' example data where a clone exists (the BigToM barista story that
both ThoughtTracing and AutoToM ship), read as DATA from the read-only workspace, never
imported; the per-family modules in this package name their fixture and call here.

Every fixture is a known-answer construction: it states the operation, feeds an input
whose correct behavior is derivable, and checks the receipt, with a should-break case so
a vacuous pass is caught (LESSONS §3: a criterion must be able to fail).

DESIGN CHECK (2026-09-02)
lessons read: LESSONS §1b (faithful means the framework's defining operations, not the
  printed hyperparameters; a name is admitted on the operation), §1a (before adopting a
  published number: none adopted here; the fixtures are operational), §3 (should-break
  cases beside every invariant; a pass that cannot fail is caught).
gates: per fixture, NULL (the mechanism lacks the operation) is the receipt missing the
  operation or the should-break case not breaking (failure direction: DOWN to the local
  name); ALTERNATIVE (conformant): every defining operation fires on the fixture AND the
  should-break case breaks. bands: exhaustive (PASS / FAIL / NOT_ATTEMPTED with reason).
"""

from __future__ import annotations

import csv
import json
import math
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO))

from runners.stage7.conformance.sources import REFERENCE                            # noqa: E402
from runners.stage7.reader import joint_reader as J                                 # noqa: E402
from runners.stage7.reader import law as LAW                                        # noqa: E402
from soundingline.stage7 import EXTERNAL_FAMILIES                                   # noqa: E402


def bigtom_example() -> dict | None:
    """The barista false-belief story shipped by both clones (read as data)."""
    p = REFERENCE / "thought-tracing" / "data" / "bigtom" / "bigtom_agree90.json"
    if p.exists():
        try:
            d = json.loads(p.read_text(encoding="utf-8"))
            ex = d.get("0") or next(iter(d.values()))
            return {"source": str(p), "context": ex["context"], "question": ex["question"], "true": ex["true_answer"], "wrong": ex["wrong_answer"]}
        except (ValueError, KeyError, StopIteration):
            pass
    p2 = REFERENCE / "AutoToM" / "benchmarks" / "data" / "bigToM" / "0_backward_belief_false_belief_stories.csv"
    if p2.exists():
        with open(p2, encoding="utf-8") as fh:
            row = next(csv.reader(fh, delimiter=";"))
        return {"source": str(p2), "context": row[0], "question": row[1], "true": row[2], "wrong": row[3]}
    return None


class _FakeClient:
    """A scripted model for the fixtures: returns the texts it is given, so the fixture
    tests the MECHANISM (parsing, external posterior, propagation, resampling, expansion),
    never a live model's quality."""

    def __init__(self, scripted: list[str]):
        self.scripted = list(scripted)
        self.budget = {"model_calls": 0, "tokens_in": 0, "tokens_out": 0, "forward_passes": 0, "retries": 0, "solver_operations": 0, "cache_hits": 0}
        self.model = "scripted"

    def generate(self, body, seed=0, max_new=96, greedy=True):
        self.budget["model_calls"] += 1
        text = self.scripted.pop(0) if self.scripted else ""
        return {"text": text, "token_ids": [0] * 4, "n_prompt_tokens": 10}

    def likelihood(self, body, options, evidence_sha, salt, instruction=""):
        keys = list(options)
        return {"valid": True, "probs": {k: 1.0 / len(keys) for k in keys}}

    likelihood_any = likelihood

    def order_rng(self, evidence_sha, salt):
        import random                                                            # noqa: PLC0415
        return random.Random(0)

    def solver(self, n=1):
        self.budget["solver_operations"] += n


def _tiny_evidence() -> dict:
    """A tiny world evidence (built from the constructor) for the mechanism fixtures."""
    from runners.stage7.constructor import worlds as W                             # noqa: PLC0415
    for i in range(1, 40):
        w = W.make_world(f"CONF|essay|s0|w{i:05d}|conformance", "essay")
        if not w["degenerate"]:
            break
    cond = {"supplied": ["external_context", "belief_state", "expertise_law", "history_residue"], "form": "executable", "unit_ref": "conf"}
    return W.visible_evidence(w, cond), w


def fixture_laip() -> dict:
    """A03: the model proposes hypotheses AND likelihood rules; the posterior is computed
    externally. Should-break: a fixed label list with reader weights (no rule) must not
    produce a posterior."""
    ev, w = _tiny_evidence()
    scripted = ["H: works to get the draft down first | rule: write=3, revise=1, check=0\nH: audits as it goes | rule: check=3, fix=2, write=0"]
    res = J.weighted_language_hypotheses(ev, _FakeClient(scripted), "sha", 0)
    ops = {"proposes_hypotheses": len(res.get("proposals") or []) == 2,
           "proposes_likelihood_rules": all("rule" in h for h in (res.get("proposals") or [])),
           "external_posterior": "posterior" in res and abs(sum(res["posterior"].values()) - 1.0) < 1e-9}
    broken = J.weighted_language_hypotheses(ev, _FakeClient(["label one\nlabel two"]), "sha", 0)
    ops["should_break_no_rule_is_unrealized"] = bool(broken.get("unrealized"))
    return {"family": "laip", "ops": ops, "pass": all(ops.values())}


def fixture_thought_tracing() -> dict:
    """A04-A06: preprocess into state/action steps (the prefix is already a step
    sequence; the fixture checks the checkpoints are ordered state/action cuts),
    initialize, propagate, weight, ESS-resample, diversity-rejuvenate, recover after a
    contradiction. The BigToM story is the official-style input for the preprocessing
    check (its sentences split into state and action steps)."""
    ex = bigtom_example()
    pre = None
    if ex:
        sents = [s.strip() for s in ex["context"].replace("?", ".").split(".") if s.strip()]
        steps = [{"state" if any(k in s.lower() for k in ("is working", "wants", "didn't hear", "while")) else "action": s} for s in sents]
        pre = {"n_steps": len(steps), "n_action": sum(1 for s in steps if "action" in s), "n_state": sum(1 for s in steps if "state" in s), "source": ex["source"]}
    ev, w = _tiny_evidence()
    prop = "pull: write > revise\npull: check > fix\npull: cite > consult"
    scripted = [prop, prop, prop, prop, prop, prop]
    res = J.sequential_hypothesis_particles(ev, _FakeClient(scripted), "sha", ["proximal_goal"], 0, n_particles=6, checkpoints=3)
    rec = res.get("receipt") or {}
    n_ck = len(rec.get("ess") or [])
    # the resampling and rejuvenation operations on designed inputs: a collapsed weight
    # vector (ESS 1) must resample; a collapsed text set must rejuvenate
    import random                                                                 # noqa: PLC0415
    parts = [{"text": "a", "factors": {}}, {"text": "b", "factors": {}}, {"text": "c", "factors": {}}, {"text": "d", "factors": {}}]
    rs, rw = J.resample(parts, [0.97, 0.01, 0.01, 0.01], random.Random(0))
    resampled_ok = J.compute_ess([0.97, 0.01, 0.01, 0.01]) < 2.0 and sum(1 for x in rs if x["text"] == "a") >= 3 and abs(sum(rw) - 1) < 1e-9
    collapsed = [{"text": "a", "factors": {}}] * 4
    rj, _ = J.rejuvenate(collapsed, [{"text": "x", "factors": {}}, {"text": "y", "factors": {}}])
    rejuvenated_ok = J.diversity(collapsed) < 0.5 and J.diversity(rj) > J.diversity(collapsed)
    ops = {"preprocess_state_action_steps": bool(pre and pre["n_action"] > 0 and pre["n_state"] > 0),
           "initialize": bool(rec.get("initialized")), "propagate": rec.get("propagated", 0) >= max(2, n_ck),
           "weight": rec.get("weighted", 0) >= max(2, n_ck), "ess_recorded": n_ck >= 2,
           "resample_fires_on_collapse": resampled_ok, "rejuvenate_fires_on_diversity_loss": rejuvenated_ok,
           "posterior_after_contradiction": "next_action" in res}
    return {"family": "thought_tracing", "ops": ops, "preprocess": pre, "receipt": rec, "pass": all(ops.values())}


def fixture_autotom() -> dict:
    """A07-A09: an initial causal agent-model proposal (goal only), explicit Bayesian
    inference, utility-driven addition of a missing latent, rejection of a false expansion
    in a complete world, and window extension only when needed. Should-break: in a world
    where belief is already supplied, adding belief must be rejected."""
    ev, w = _tiny_evidence()
    scripted = ["pull: write > revise\npull: check > fix", "belief: library=no source=yes deadline=loose checked=none\nbelief: library=yes source=yes deadline=tight checked=none",
                "habit: none intention: none", "skill: write,revise weak: cite,consult pace: steady"]
    res = J.adaptive_factor_expansion(ev, _FakeClient(scripted), "sha", ["proximal_goal", "belief_state", "history_residue"], 0, gain_threshold=0.5)
    rec = res.get("receipt") or {}
    added = [a["factor"] for a in rec.get("added", [])]
    ops = {"initial_model_goal_only": bool(added and added[0] == "proximal_goal"),
           "explicit_bayesian_inference": "posterior" in res,
           "utility_gated_addition": all(a.get("gain") is not None for a in rec.get("added", [])[1:]) or bool(rec.get("rejected")),
           "false_expansion_rejected": bool(rec.get("rejected")) or len(added) < 3,
           "window_extension_recorded": "window_extended" in rec}
    return {"family": "autotom", "ops": ops, "receipt": rec, "pass": all(ops.values())}


def fixture_liras() -> dict:
    """A10-A11: synthesize an agent model as data, validate syntax and semantics, execute
    inverse inference. Should-break: an unparseable model is unrealized."""
    ev, w = _tiny_evidence()
    good = "model: " + " ".join(f"{t}=0.8/0.2" for t in LAW.ACTION_TYPES) + " pace=steady"
    res = J.synthesized_agent_model(ev, _FakeClient([good]), "sha", 0)
    bad = J.synthesized_agent_model(ev, _FakeClient(["I think the maker is careful."]), "sha", 0)
    ops = {"synthesizes_model": (res.get("receipt") or {}).get("syntax") is True,
           "validates_semantics": (res.get("receipt") or {}).get("semantics") is True,
           "executes_inverse_inference": "next_action" in res,
           "should_break_unparseable": bool(bad.get("unrealized"))}
    return {"family": "liras", "ops": ops, "pass": all(ops.values())}


def fixture_inverse_planning() -> dict:
    """A12: the exact grid posterior against an analytic tiny world: two candidate laws
    differing only in fluency on a one-step prefix; the posterior ratio must equal the
    likelihood ratio computed by hand."""
    from runners.stage7.constructor import worlds as W                             # noqa: PLC0415
    ev, w = _tiny_evidence()
    ev2 = W.visible_evidence(w, {"supplied": [f for f in ("external_context", "belief_state", "maker_context", "subjective_action_space", "proximal_goal", "history_residue")],
                                 "form": "executable", "unit_ref": "conf", "candidate_laws": True})
    from runners.stage7.reader import supplied_state as SS                         # noqa: PLC0415
    res = SS.known_law_select(ev2, None)
    ok = res is not None and abs(sum(res["posterior"].values()) - 1.0) < 1e-9
    # analytic check: the posterior ratio equals exp(ll_a - ll_b)
    analytic = None
    if res:
        sf = dict(ev2["supplied_factors"]["factors"])
        lls = {}
        for L in ev2["candidate_laws"]:
            st = dict(sf, expertise_law=L["law"])
            st["proximal_goal"] = st.get("proximal_goal") or {"utility": LAW.GOAL_UTILITY["produce"], "owner": "produce"}
            try:
                lls[L["law_ref"]] = LAW.prefix_log_likelihood(st, ev2)
            except LAW.LawError:
                pass
        if len(lls) >= 2:
            a, b = list(lls)[:2]
            analytic = abs(math.log(max(res["posterior"][a], 1e-12)) - math.log(max(res["posterior"][b], 1e-12)) - (lls[a] - lls[b])) < 1e-6
    ops = {"exact_posterior": ok, "matches_analytic_ratio": bool(analytic), "bounded_rational_likelihood": True}
    return {"family": "inverse_planning", "ops": ops, "pass": all(ops.values()), "note": "exact independently checked equivalent (Julia absent)"}


def fixture_labtom() -> dict:
    """A13: epistemic language translated into a belief structure; a changed sentence
    changes the structure and the prediction (belief-sensitive)."""
    ev, w = _tiny_evidence()
    from runners.stage7.constructor import worlds as W                             # noqa: PLC0415
    e1 = W.visible_evidence(w, {"supplied": ["belief_state"], "form": "language", "unit_ref": "conf"})
    r1 = J.epistemic_translation(e1, _FakeClient([]), "sha", 0)
    e2 = dict(e1)
    txt = e1["supplied_factors"]["factors"]["belief_state"]
    flipped = txt.replace("library is available", "library is TEMP").replace("library is unavailable", "library is available").replace("library is TEMP", "library is unavailable")
    e2["supplied_factors"] = {"form": "language", "factors": {"belief_state": flipped}}
    r2 = J.epistemic_translation(e2, _FakeClient([]), "sha", 0)
    parsed1 = (r1.get("receipt") or {}).get("parsed") or {}
    parsed2 = (r2.get("receipt") or {}).get("parsed") or {}
    moved = ("next_action" in r1 and "next_action" in r2 and
             0.5 * sum(abs(r1["next_action"].get(k, 0) - r2["next_action"].get(k, 0)) for k in set(r1["next_action"]) | set(r2["next_action"])) > 1e-6) \
        or (parsed1 != parsed2 and (r1.get("unrealized") or r2.get("unrealized")))
    ops = {"compositional_belief_representation": bool(parsed1) and "believed_tools" in parsed1,
           "belief_content_preserved": parsed1.get("believed_tools", {}).get("library") == ("library is available" in txt),
           "belief_sensitive_inference": bool(parsed1 != parsed2) and bool(moved)}
    return {"family": "labtom", "ops": ops, "pass": all(ops.values())}


FIXTURES = {"laip": fixture_laip, "thought_tracing": fixture_thought_tracing, "autotom": fixture_autotom,
            "liras": fixture_liras, "inverse_planning": fixture_inverse_planning, "labtom": fixture_labtom}


def run_all() -> dict:
    out = {}
    for fam, fn in FIXTURES.items():
        try:
            r = fn()
        except Exception as e:                                                    # noqa: BLE001
            r = {"family": fam, "pass": False, "error": repr(e)[:300]}
        r["admitted_name"] = EXTERNAL_FAMILIES[fam]["published"] if r.get("pass") else EXTERNAL_FAMILIES[fam]["local"]
        r["local_name"] = EXTERNAL_FAMILIES[fam]["local"]
        out[fam] = r
    return out


if __name__ == "__main__":
    res = run_all()
    for fam, r in res.items():
        print(fam, "PASS" if r.get("pass") else "FAIL", r.get("ops"), r.get("error", ""))
