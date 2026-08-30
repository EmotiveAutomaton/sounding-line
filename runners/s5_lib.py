"""Stage 5 shared model, scoring, and record helpers, on top of the Stage-4 library.

DESIGN CHECK (2026-08-29)
lessons read: LESSONS §3 (a criterion must be able to fail; the readout class must match
  the behavior moved; short hypothesis given long evidence; every statistic written to
  disk; the matched comparator and the plain route both reported; the oracle direction is
  one leg of a selective signature), §4 (instruct readers only; record measured values),
  §5 (produces guards; GPU lock inside the runner), CONTROLS §6.
gates and bands (instrument level, frozen here):
  - candidate-likelihood readout: normalized next-token likelihood over balanced letter
    labels with an explicit `unknown` candidate listed among them in randomized order.
    NULL for the readout (a working instrument): the label tokens are single tokens and
    the probabilities sum to one; ALTERNATIVE (a dead instrument): a multi-token label,
    which marks the row invalid rather than silently mis-scoring; failure direction
    guarded: a reader that answers by position is exposed by the per-call permutation.
  - the structured record parser: exactly one JSON object with one entry per requested
    latent, each carrying a choice in the allowed set or `unknown`, a confidence in [0,1],
    and a list of evidence ids from the shown set. NULL (a valid record): all present;
    ALTERNATIVE: absent, malformed, out-of-range, or prose-only mentions, each an
    exhaustive reason (`malformed_or_absent`, `missing_latent`, `out_of_range`,
    `bad_confidence`, `bad_evidence`, `ok`); failure direction guarded: prose that names a
    candidate never counts, so a fluent rationale cannot pass as a posterior (pre-mortem 1).
  - trajectory statistics: first-useful point (truth mass above 0.5 and never below
    after), reversal count (the argmax changing), overconfidence after a contradiction
    (truth mass rising after an item that contradicts the leading hypothesis); each is a
    count or an index and cannot alias.
"""

from __future__ import annotations

import json
import math
import os
import random
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from runners import s4_lib                                                        # noqa: E402
from runners.s3_lib import hash_stable, perm_p                                    # noqa: E402,F401
from runners.s4_lib import (GpuSession, auroc, balanced_accuracy, brier,          # noqa: E402,F401
                            build_listing, chat_prefix_ids, cluster_bootstrap_ci,
                            env_versions, free_model, generate, hooks_present, is_oom,
                            label_token_ids, likelihood_choice, load_model, log_score,
                            model_available, model_revision, option_text_logprobs,
                            paired_contrast, per_unit_means, raw_output_row, safe_id,
                            steer_positions, stratum_balanced, world_rng)
from soundingline.stage5 import UNKNOWN, card_dir, ece, calibration_slope, now_iso   # noqa: E402,F401

PARSER_VERSION = "s5-record-1.0"
READOUT_VERSION = "s5-candidate-likelihood-1.0"
DESIGN = os.environ.get("S5_DESIGN", "1")      # "2": the second contract (2026-08-29): every post-run repair
READERS = ["Qwen/Qwen2.5-1.5B-Instruct", "HuggingFaceTB/SmolLM2-1.7B-Instruct"]
CHECKPOINT2 = "Qwen/Qwen2.5-3B-Instruct"        # the second checkpoint the bridge owes (B01)
LETTERS = s4_lib.LETTERS
SEED0 = 55000
UNKNOWN_TEXT = "cannot be determined from the evidence given"

__all__ = ['GpuSession', 'UNKNOWN', 'auroc', 'balanced_accuracy', 'brier', 'build_listing', 'calibration_slope', 'card_dir', 'chat_prefix_ids', 'cluster_bootstrap_ci', 'ece', 'env_versions', 'free_model', 'generate', 'hash_stable', 'hooks_present', 'is_oom', 'label_token_ids', 'likelihood_choice', 'load_model', 'log_score', 'model_available', 'model_revision', 'now_iso', 'option_text_logprobs', 'paired_contrast', 'per_unit_means', 'perm_p', 'raw_output_row', 'safe_id', 'steer_positions', 'stratum_balanced', 'world_rng']



# ── candidate-likelihood readouts ─────────────────────────────────────────────────────

def candidate_likelihood(model, tok, body: str, candidates: dict, rng: random.Random,
                         unknown: bool = True, instruction: str = "Answer with the letter only.") -> dict:
    """The primary Stage-5 readout: likelihood over the candidate set with an explicit
    `unknown` candidate among the options (§4.1), order randomized per call. Returns the
    Stage-4 readout dict plus `p_unknown` and `mass` (the candidates' masses, unknown
    apart)."""
    opts = dict(candidates)
    if unknown:
        opts[UNKNOWN] = UNKNOWN_TEXT
    if len(opts) > len(LETTERS):
        raise ValueError(f"{len(opts)} candidates exceed the {len(LETTERS)} balanced labels")
    r = likelihood_choice(model, tok, body, opts, rng, instruction=instruction)
    if not r["valid"]:
        return r
    probs = r["probs"]
    r["p_unknown"] = probs.get(UNKNOWN, 0.0) if unknown else 0.0
    r["mass"] = {k: v for k, v in probs.items() if k != UNKNOWN}
    r["readout"] = READOUT_VERSION
    return r


def latent_entry(readout: dict, evidence_ids) -> dict:
    """A latent-record entry from a candidate-likelihood readout (the evidence ids are the
    items the prompt showed; a likelihood readout cannot point at spans, so the record
    carries the shown set, declared as such)."""
    if not readout.get("valid"):
        return {"candidates": {}, "unknown": 1.0, "confidence": 0.0, "evidence": list(evidence_ids),
                "valid": False, "validity_reason": readout.get("validity_reason")}
    return {"candidates": dict(readout["mass"]), "unknown": readout.get("p_unknown", 0.0),
            "confidence": max(list(readout["mass"].values()) + [readout.get("p_unknown", 0.0)]),
            "evidence": list(evidence_ids), "pred": readout["pred"], "valid": True,
            "evidence_reference": "shown-set"}


# ── the structured record parser (generated records) ─────────────────────────────────

_JSON_OBJ = re.compile(r"\{(?:[^{}]|\{[^{}]*\})*\}", re.S)
RECORD_REASONS = ("malformed_or_absent", "missing_latent", "out_of_range", "bad_confidence",
                  "bad_evidence", "ok")


def parse_latent_record(text: str, schema: dict, evidence_ids) -> tuple[dict | None, str]:
    """schema: {latent: [allowed labels]} (the labels the reader saw, e.g. letters).
    Exactly one well-formed JSON object; every requested latent present with a choice in
    its allowed set or `unknown`, a confidence in [0, 1], and evidence ids from the shown
    set. Prose mentions never count."""
    objs = _JSON_OBJ.findall(text or "")
    parsed = None
    for o in objs:
        try:
            cand = json.loads(o)
        except Exception:                                                        # noqa: BLE001
            continue
        if isinstance(cand, dict) and any(k in cand for k in schema):
            if parsed is not None:
                return None, "malformed_or_absent"       # two candidate objects: ambiguous
            parsed = cand
    if parsed is None:
        return None, "malformed_or_absent"
    out = {}
    allowed_ev = set(str(e) for e in evidence_ids)
    for latent, labels in schema.items():
        e = parsed.get(latent)
        if not isinstance(e, dict):
            return None, "missing_latent"
        choice = str(e.get("choice", "")).strip()
        if choice.upper() in [str(x).upper() for x in labels]:
            choice = [str(x) for x in labels][[str(x).upper() for x in labels].index(choice.upper())]
        elif choice.lower() == UNKNOWN:
            choice = UNKNOWN
        else:
            return None, "out_of_range"
        conf = e.get("confidence")
        if not isinstance(conf, (int, float)) or isinstance(conf, bool) or not (0.0 <= float(conf) <= 1.0):
            return None, "bad_confidence"
        ev = e.get("evidence", [])
        if not isinstance(ev, list) or any(str(x) not in allowed_ev for x in ev):
            return None, "bad_evidence"
        out[latent] = {"choice": choice, "confidence": float(conf), "evidence": [str(x) for x in ev]}
    return out, "ok"


def run_record_fixtures() -> list[str]:
    """I02 fixture set (§9.1 test 1): negation, quotation, unknown, malformed, evidence
    spans, label permutations. Returns the failures (empty means the parser passes)."""
    schema = {"episode_goal": ["A", "B", "C"], "standing_preference": ["A", "B", "C", "D"]}
    ev = ["e1", "e2", "e3"]
    ok = '{"episode_goal": {"choice": "B", "confidence": 0.7, "evidence": ["e1"]}, "standing_preference": {"choice": "unknown", "confidence": 0.4, "evidence": []}}'
    fails = []

    def expect(text, reason, label=None, latent="episode_goal"):
        rec, why = parse_latent_record(text, schema, ev)
        if why != reason:
            fails.append(f"{text[:50]!r}: expected {reason}, got {why}")
        elif reason == "ok" and label is not None and rec[latent]["choice"] != label:
            fails.append(f"{text[:50]!r}: expected choice {label}, got {rec[latent]['choice']}")
    expect(ok, "ok", "B")
    expect("I would not say A; " + ok, "ok", "B")                              # negation in prose
    expect('The answer "A" is tempting but ' + ok, "ok", "B")                  # quotation in prose
    expect(ok.replace('"B"', '"unknown"'), "ok", UNKNOWN)                      # explicit unknown
    expect("The goal is B and the preference is C.", "malformed_or_absent")   # prose only
    expect('{"episode_goal": {"choice": "B", "confidence": 0.7, "evidence": ["e1"]}}', "missing_latent")
    expect(ok.replace('"B"', '"E"'), "out_of_range")
    expect(ok.replace("0.7", "1.7"), "bad_confidence")
    expect(ok.replace('"confidence": 0.7', '"confidence": "high"'), "bad_confidence")
    expect(ok.replace('["e1"]', '["e9"]'), "bad_evidence")
    expect(ok + "\n" + ok.replace('"B"', '"A"'), "malformed_or_absent")        # two objects: ambiguous
    expect(ok.replace('"B"', '"b"'), "ok", "B")                                # case-insensitive label
    # permutation invariance: the same record under a relabeling maps back to the same key
    rec1, _ = parse_latent_record(ok, schema, ev)
    perm = {"A": "C", "B": "A", "C": "B"}
    rec2, _ = parse_latent_record(ok.replace('"B"', '"A"'), schema, ev)
    if perm[rec2["episode_goal"]["choice"]] != rec1["episode_goal"]["choice"] and rec2["episode_goal"]["choice"] != "A":
        fails.append("permutation mapping broken")
    return fails


# ── trajectories (J03) ────────────────────────────────────────────────────────────────

def trajectory_stats(traj: list[dict], truth: str, contradiction_at: int | None = None,
                     useful: float = 0.5) -> dict:
    """traj: per evidence step, a {candidate: mass, unknown: mass} dict. Reports the first
    step at which the truth's mass is above `useful` and stays there, the number of argmax
    reversals, and whether the truth's mass ROSE right after the contradiction item (the
    overconfidence signature: a leading hypothesis that absorbs contradicting evidence)."""
    masses = [t.get(truth, 0.0) for t in traj]
    first = None
    for i, m in enumerate(masses):
        if m > useful and all(x > useful for x in masses[i:]):
            first = i + 1
            break
    argmax = [max(t, key=t.get) if t else None for t in traj]
    reversals = sum(1 for a, b in zip(argmax, argmax[1:]) if a != b)
    over = None
    if contradiction_at is not None and 0 < contradiction_at < len(masses):
        over = masses[contradiction_at] >= masses[contradiction_at - 1]
    return {"first_useful_step": first, "reversals": reversals,
            "final_truth_mass": masses[-1] if masses else None,
            "overconfident_after_contradiction": over}


# ── information ──────────────────────────────────────────────────────────────────────

def entropy(p: dict) -> float:
    return -sum(v * math.log(max(v, 1e-12)) for v in p.values() if v > 0)


def kl(p: dict, q: dict) -> float:
    return sum(v * (math.log(max(v, 1e-12)) - math.log(max(q.get(k, 0.0), 1e-12))) for k, v in p.items() if v > 0)


def expected_info_gain(prior: dict, likelihood_by_outcome: dict) -> float:
    """Mutual information between the target (prior over its values) and an observation
    with likelihood_by_outcome[value] = {obs: p(obs | value)} (nats)."""
    p_obs: dict = {}
    for v, pv in prior.items():
        for o, po in likelihood_by_outcome[v].items():
            p_obs[o] = p_obs.get(o, 0.0) + pv * po
    mi = 0.0
    for v, pv in prior.items():
        for o, po in likelihood_by_outcome[v].items():
            if po > 0 and pv > 0:
                mi += pv * po * math.log(po / max(p_obs[o], 1e-12))
    return mi


def confidence_correct(readout: dict, truth) -> tuple[float, bool] | None:
    if not readout.get("valid"):
        return None
    probs = readout["probs"]
    pred = readout["pred"]
    return float(probs[pred]), pred == truth
