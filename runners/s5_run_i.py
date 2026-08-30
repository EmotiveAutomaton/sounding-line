"""Stage 5 integrity and calibration cards (brief §6 I01-I04, §8.3 pilot and workload lock).

DESIGN CHECK (2026-08-29)
lessons read: LESSONS §1a (a published or prior number is a gate only when regenerated
  from committed inputs), §3 (the criterion must be able to fail; a gate's band derived
  from its probe count; leakage baselines before readers; count identities against unit
  counts; a dead control reports what it checked), §5 (produces guards, one writer for
  the manifest, workload sized from measured rates with the 2-3x rule).
gates and bands:
  - I01 receipt: the Stage-4 confirmation primaries (A01, T01) and the L255 fold-1
    congruent effect recomputed from the committed rows must match the committed verdicts
    to 1e-6 and the input files must hash to the committed values; NULL: match;
    ALTERNATIVE: mismatch, which BLOCKS reuse of that anchor and blocks nothing else.
  - I02 parser: every fixture (negation, quotation, unknown, malformed, evidence spans,
    label permutations) returns its expected reason; NULL: all pass; ALTERNATIVE: any
    failure closes every structured readout. Reader gate on 48 record-supported items per
    reader and domain, the candidate-likelihood readout with `unknown` listed: validity
    at least 0.95, accuracy at least 0.75, no option under 0.50, a position/paraphrase
    swing under 10 points (bands from the Stage-4 gate, frozen before results); the
    second checkpoint is gated the same way for the bridge. A reader failing is excluded;
    if both admitted readers fail, the model tracks close INSTRUMENT_FAILED.
  - workload lock: the pilot's measured seconds per likelihood call and per generation
    set the throughput multiplier; the tier is the largest whose GPU estimate leaves the
    closure allowance; the lock is written before any discovery output.
  - I03: every factor level present in every lane (liveness); surface length matched
    across regions within 10 percent; the leakage classifier from bag-of-words to each
    hidden factor within 0.10 of chance on held-out worlds (else that attribution is
    LEAKED); collision registry: every A lineage has its twin, natural surface
    collisions among roots are zero; construction audit: all root constructions distinct.
  - I04: the route information matrix; a world enters a model-choice card only if the
    best route's exact information exceeds the second's by the 0.05-nat floor; the
    regime confusion floor: the fraction of source worlds whose region is identifiable
    from surface factors alone (by construction below one; reported, never gated).
  every gate above is directional in the same sense. under the null (no defect) the
  receipts match, the parser passes every fixture, the readers clear validity, accuracy,
  per-option, and permutation-swing floors, and the leakage classifier sits at chance;
  under the alternative (a defect) the named floor is crossed and the failure is a
  downward one on the named quantity, so a reader or construction that fails is excluded
  and the failure is written, never averaged over.
verdict bands per card, exhaustive (no silent interval), from the shared classifier on
  the primary's point and its cluster-bootstrap interval against the frozen threshold:
  COUNTEREVIDENCE when the whole interval sits below zero; SUPPORT_CANDIDATE when the
  interval excludes zero and the point reaches the threshold; INCONCLUSIVE when the
  interval excludes zero but the point falls short, or includes zero without excluding
  the threshold; VALID_NULL when the interval includes zero and excludes the threshold;
  every real interval lands in exactly one. Before any interval exists the cell carries
  VOID (no units, or every reader excluded by the gate), INSTRUMENT_FAILED (a validity
  or manipulation gate failed, named in the reason), or NOT_RUN (a dependency died);
  those three are states of the instrument, never evidence about the hypothesis.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from runners import s5_cards, s5_lib, s5_sources, s5_worlds                        # noqa: E402
from runners.s4_run_i import GATE, gate_items                                      # noqa: E402
from runners.s4_worlds import construction_hash                                    # noqa: E402
from runners.s5_run_common import SMOKE                                            # noqa: E402
from soundingline.stage5 import (S5, Lineages5, RunContract5, completion_marker,    # noqa: E402
                                 expand_expected_cells, now_iso, read_json, read_jsonl,
                                 sha256_file, write_json, write_registry)

SEED = s5_lib.SEED0


def _card_dir(card: str) -> Path:
    """The card's directory, or the repair cell's when S5_CELL names one for this card
    (TODO (v), 2026-08-29: I03/v2 wrote into I03/ and was recorded FAILED)."""
    override = os.environ.get("S5_CELL")
    if override and override.split("/")[0] == card:
        return s5_lib.card_dir(override)
    return s5_lib.card_dir(card)


# ── I01: regenerate the Stage-4 anchors and the L255 rows ─────────────────────────────

def arm_i01() -> int:
    t0 = time.time()
    out = _card_dir("I01")
    from runners.s4_run_f import _unit_values, PRIMARY_DEF                         # noqa: PLC0415
    from runners import s4_lib                                                      # noqa: PLC0415
    s4root = REPO / "results" / "phase_2_4_stage_4"
    receipts = {}
    ok_all = True
    for card in ("A01", "T01"):
        cases = s4root / card / "confirmation" / "cases.jsonl"
        verdict = s4root / "F01" / "verdict.json"
        if not cases.exists() or not verdict.exists():
            receipts[card] = {"status": "MISSING_INPUT"}
            ok_all = False
            continue
        rows = read_jsonl(cases)
        fa, fb, key = PRIMARY_DEF[card]
        vals = _unit_values(rows, fa, fb, key)
        ci = s4_lib.cluster_bootstrap_ci(vals, 51000, alpha=0.025)
        committed = read_json(verdict)["results"][card]["estimate"]
        match = abs(ci["point"] - committed["point"]) < 1e-6 and ci["n_units"] == committed["n_units"]
        receipts[card] = {"recomputed": ci, "committed": committed, "match": match,
                          "input_sha256": sha256_file(cases)}
        ok_all &= match
    a07 = REPO / "results" / "phase_2_4_stage_3" / "A" / "A07" / "rows_b.jsonl"
    a07v = REPO / "results" / "phase_2_4_stage_3" / "A" / "A07" / "verdict_b.json"
    if a07.exists() and a07v.exists():
        rows = read_jsonl(a07)
        fold = "smollm->qwen"
        zero = {r["art"]: r for r in rows if r["fold"] == fold and r["cond"] == "zero" and r["valid"]}
        diffs = [r["log_score_truth"] - zero[r["art"]]["log_score_truth"] for r in rows
                 if r["fold"] == fold and r["cond"] == "congruent" and r["valid"] and r["art"] in zero]
        obs = sum(diffs) / len(diffs)
        committed = read_json(a07v)["per_fold"][fold]["conditions"]["congruent"]["log_score_minus_zero"]
        match = abs(obs - committed) < 1e-6
        receipts["L255"] = {"recomputed": obs, "committed": committed, "n": len(diffs), "match": match,
                            "input_sha256": sha256_file(a07)}
        ok_all &= match
    else:
        receipts["L255"] = {"status": "MISSING_INPUT"}
        ok_all = False
    contract = RunContract5.load() or RunContract5.create()
    write_json(out / "receipt.json", {"receipts": receipts, "all_match": ok_all, "written_at": now_iso()})
    write_json(out / "verdict.json", {"card": "I01", "exec": "COMPLETE", "outcome": "INFRASTRUCTURE",
                                      "reason": "receipt" + ("" if ok_all else "; a mismatch BLOCKS reuse of that anchor"),
                                      "anchors_match": ok_all, "minutes": round((time.time() - t0) / 60, 2),
                                      "marker": completion_marker({}, {"receipt": str(out / "receipt.json")}, contract)})
    print(f"I01: anchors match={ok_all} {json.dumps({k: v.get('match', v.get('status')) for k, v in receipts.items()})}")
    return 0


# ── I02: parser fixtures, the reader gate, the throughput pilot, and the freeze ───────

def arm_i02pilot() -> int:
    """The discarded pilot on pilot lineages: seconds per likelihood call and per
    generation, per reader, peak memory. Nothing here selects a design."""
    t0 = time.time()
    out = _card_dir("I02")
    pilot = {"card": "I02pilot", "written_at": now_iso(), "readers": {}}
    with s5_lib.GpuSession("s5_i02pilot") as gs:
        for reader in s5_lib.READERS + [s5_lib.CHECKPOINT2]:
            import torch                                                          # noqa: PLC0415
            torch.cuda.reset_peak_memory_stats()
            model, tok, rev = s5_lib.load_model(reader)
            try:
                rng = random.Random(1)
                items = gate_items("workshop", 5, "s5pilot")[:16]
                t1 = time.time()
                for it in items:
                    s5_lib.candidate_likelihood(model, tok, it["body"], it["options"], rng)
                lik_s = (time.time() - t1) / len(items)
                t1 = time.time()
                for i in range(4):
                    s5_lib.generate(model, tok, items[i]["body"] + "\nReply with a JSON record.", seed=100 + i, max_new=96)
                gen_s = (time.time() - t1) / 4
                pilot["readers"][reader] = {"revision": rev, "likelihood_s": lik_s, "gen96_s": gen_s,
                                            "peak_vram_gb": round(torch.cuda.max_memory_allocated() / 2**30, 2)}
                print(f"pilot {reader}: lik {lik_s:.3f}s gen96 {gen_s:.2f}s")
            finally:
                s5_lib.free_model(model)
    pilot["gpu_lock_min"] = round(gs.held_s / 60, 2)
    pilot["minutes"] = round((time.time() - t0) / 60, 2)
    write_json(out / "PILOT.json", pilot)
    contract = RunContract5.load() or RunContract5.create()
    pout = _card_dir("I02pilot")
    write_json(pout / "verdict.json", {"card": "I02pilot", "exec": "COMPLETE", "outcome": "INFRASTRUCTURE",
                                       "gpu_lock_min": pilot["gpu_lock_min"], "minutes": pilot["minutes"],
                                       "marker": completion_marker({}, {"pilot": str(out / "PILOT.json")}, contract)})
    return 0


def _gate_source(model, tok, rng: random.Random, n: int | None = None) -> dict:
    """Design 2, TODO (j): can the reader read the source world's visible register? Two
    two-option questions (calm against alarmed; asks for action against informs only) on
    fresh source worlds; the band is accuracy at or above 0.75 on both, validity 0.95."""
    from runners import s5_sources as S                                            # noqa: PLC0415
    n = n or (8 if SMOKE else 32)
    rep = {"n_per_domain": n, "domains": {}}
    for domain in (getattr(S, "DOMAINS", None) or sorted(S.TOPICS)):
        acc = {"arousal": 0, "action": 0}
        valid = 0
        for k in range(n):
            w = S.make_source_world(f"GATE|{domain}|s0|w{k:04d}|gate", domain)
            body = f"A notice you received:\n\"{w['text']}\"\n\n"
            r1 = s5_lib.candidate_likelihood(model, tok, body + "What is the notice's tone?",
                                             {"low": "calm and matter-of-fact", "high": "alarmed and urgent"}, rng, unknown=False)
            r2 = s5_lib.candidate_likelihood(model, tok, body + "Does the notice ask the reader to do something?",
                                             {"present": "yes, it asks for an action", "absent": "no, it only informs"}, rng, unknown=False)
            valid += int(r1["valid"] and r2["valid"])
            acc["arousal"] += int(r1["valid"] and r1["pred"] == w["factors"]["arousal_goal"])
            acc["action"] += int(r2["valid"] and r2["pred"] == w["factors"]["action_goal"])
        rep["domains"][domain] = {"validity": valid / n, "arousal_acc": acc["arousal"] / n, "action_acc": acc["action"] / n}
    rep["passed"] = all(d["validity"] >= 0.95 and d["arousal_acc"] >= 0.75 and d["action_acc"] >= 0.75 for d in rep["domains"].values())
    return rep


def _gate_latent_to_choice(model, tok, rng: random.Random, n: int | None = None) -> dict:
    """Design 2, TODO (p): told the true latents, does the reader predict the held-out choice
    above a uniform guess? The band is the mean log score above uniform on fresh joint worlds."""
    import math                                                                   # noqa: PLC0415
    from runners import s5_run_j as J                                             # noqa: PLC0415
    from runners import s5_worlds as W                                            # noqa: PLC0415
    n = n or (8 if SMOKE else 24)
    lp, unif, acc, valid = [], [], 0, 0
    for domain in W.DOMAINS:
        for k in range(n):
            w = W.make_joint_world(f"GATE|{domain}|s0|w{k:04d}|gate", domain)
            ev, _ = J.evidence_text(w)
            truth = {"episode_goal": w["episode_goal"], "process_plan": " > ".join(w["process_plan"]),
                     "standing_preference": w["standing_preference"]}
            ti = w["target_scenario"]
            body, cands = J.choice_prompt(w, truth, ti, "", ev, version="2")
            r = s5_lib.candidate_likelihood(model, tok, body, cands, rng, unknown=False)
            target = w["scenarios"][ti]["draw"]
            if r["valid"]:
                valid += 1
                lp.append(math.log(max(r["probs"][target], 1e-9)))
                acc += int(r["pred"] == target)
            unif.append(math.log(1 / len(w["scenarios"][ti]["feasible"])))
    total = 2 * n
    rep = {"n": total, "validity": valid / total, "mean_log_score": (sum(lp) / len(lp)) if lp else None,
           "uniform": sum(unif) / total, "accuracy": acc / total}
    rep["passed"] = bool(lp) and rep["validity"] >= 0.95 and rep["mean_log_score"] > rep["uniform"]
    return rep


def _gate_reader(model, tok, reader: str, rng: random.Random, n_per_axis: int | None = None,
                 seed_key: str = "s5gate") -> dict:
    """The reader gate. `n_per_axis` and `seed_key` exist for the post-run re-gate at more
    items on fresh items (TODO (a), 2026-08-29); the stage's gate used the defaults."""
    n = n_per_axis or (6 if SMOKE else (24 if s5_lib.DESIGN == "2" else 12))   # design 2: the 96-item gate (L282)
    rep = {"reader": reader, "domains": {}}
    for domain in s5_cards.DOMAINS:
        items = gate_items(domain, n, f"{seed_key}|{domain}")
        valid = correct = correct2 = valid2 = 0
        per_opt = {ax: [0, 0] for ax in ("robust", "cheap", "fast", "precedent")}
        prob_swings = []
        for it in items:
            r = s5_lib.candidate_likelihood(model, tok, it["body"], it["options"], rng)
            if not r["valid"]:
                continue
            valid += 1
            pred = r["pred"]
            hit = pred == it["truth"]
            correct += hit
            per_opt[it["truth"]][0] += hit
            per_opt[it["truth"]][1] += 1
            # position control: the same items under a second permutation; the gate's swing is
            # the ACCURACY difference between the two passes (the Stage-4 band), and the
            # per-item probability wobble is reported as an instrument fact, not gated
            r2 = s5_lib.candidate_likelihood(model, tok, it["body"], it["options"], rng)
            if r2["valid"]:
                valid2 += 1
                correct2 += r2["pred"] == it["truth"]
                prob_swings.append(abs(float(r["probs"].get(it["truth"], 0)) - float(r2["probs"].get(it["truth"], 0))))
        acc = correct / max(1, valid)
        acc2 = correct2 / max(1, valid2)
        rep["domains"][domain] = {"n": len(items), "validity": valid / len(items), "accuracy": acc, "accuracy_second_permutation": acc2,
                                  "per_option": {k: (v[0] / v[1] if v[1] else None) for k, v in per_opt.items()},
                                  "position_swing": abs(acc - acc2),
                                  "probability_swing_mean": (sum(prob_swings) / len(prob_swings)) if prob_swings else None}
    v = min(d["validity"] for d in rep["domains"].values())
    a = min(d["accuracy"] for d in rep["domains"].values())
    po = min((x for d in rep["domains"].values() for x in d["per_option"].values() if x is not None), default=0)
    sw = max((d["position_swing"] or 0) for d in rep["domains"].values())
    rep["admitted"] = v >= GATE["validity"] and a >= GATE["accuracy"] and po >= GATE["per_option"] and sw <= GATE["swing_pp"]
    rep["gate"] = dict(GATE)
    return rep


def arm_i02() -> int:
    t0 = time.time()
    out = _card_dir("I02")
    fixtures = s5_lib.run_record_fixtures() + s5_lib.s4_lib.run_parser_fixtures()
    contract = RunContract5.load() or RunContract5.create()
    if fixtures:
        write_json(out / "verdict.json", {"card": "I02", "exec": "FAILED", "outcome": "INSTRUMENT_FAILED",
                                          "reason": f"parser fixtures failed: {fixtures}",
                                          "marker": completion_marker({}, {}, contract)})
        return 1
    gates = {}
    with s5_lib.GpuSession("s5_i02") as gs:
        for reader in s5_lib.READERS + [s5_lib.CHECKPOINT2]:
            model, tok, rev = s5_lib.load_model(reader)
            try:
                gates[reader] = _gate_reader(model, tok, reader, random.Random(SEED + 7))
                gates[reader]["revision"] = rev
                print(f"gate {reader}: admitted={gates[reader]['admitted']} {json.dumps({d: round(x['accuracy'], 3) for d, x in gates[reader]['domains'].items()})}")
            finally:
                s5_lib.free_model(model)
    admitted = [r for r in s5_lib.READERS if gates[r]["admitted"]]
    ckpt2_ok = gates[s5_lib.CHECKPOINT2]["admitted"]
    # design 2: the track gates (TODO (j), (p)): the source-world register (calm against alarmed,
    # act against inform) for the appraisal track, and latents-to-choice (true latents stated,
    # the future choice predicted above a uniform guess) for the joint track
    track_gates = {}
    if s5_lib.DESIGN == "2" and admitted:
        with s5_lib.GpuSession("s5_i02_tracks") as gs2:
            for reader in admitted:
                model, tok, _ = s5_lib.load_model(reader)
                try:
                    track_gates[reader] = {"A": _gate_source(model, tok, random.Random(SEED + 17)),
                                           "J": _gate_latent_to_choice(model, tok, random.Random(SEED + 19))}
                    print(f"track gates {reader}: A {track_gates[reader]['A']['passed']} J {track_gates[reader]['J']['passed']}")
                finally:
                    s5_lib.free_model(model)
        gs.held_s += gs2.held_s
    pilot = read_json(out / "PILOT.json")
    liks = [v["likelihood_s"] for v in pilot["readers"].values()]
    gens = [v["gen96_s"] for v in pilot["readers"].values()]
    mult = max((sum(liks) / len(liks)) / 0.15, (sum(gens) / len(gens)) / 2.5) * (max(1, len(admitted)) / 2)
    est_min = s5_cards.gpu_estimate_hours("minimum", mult, units_override=3 if SMOKE else None)
    est_exp = s5_cards.gpu_estimate_hours("expanded", mult, units_override=6 if SMOKE else None)
    closure = contract.data["allocation_hours"]["confirmation"]
    window = contract.data["run_hours"]
    tier = "minimum" if SMOKE else ("expanded" if est_exp["total"] <= window - closure else "minimum")   # the smoke exercises the rung
    label = "FULL" if est_min["total"] <= window - closure else "OVER_WINDOW_RUN_TO_EMPTY"
    spec = s5_cards.expected_spec(tier)
    cells = expand_expected_cells(spec)
    write_registry("EXPECTED_CELLS", {"tier": tier, "label": label, "cells": cells, "written_at": now_iso()})
    # lineages: roots for J01 (the J and R cards derive), A01 (the A cards derive), F01 (F02/F03
    # derive); discovery, transfer, and confirmation lanes
    L = Lineages5()
    alloc = {}
    n_units = (3 if SMOKE else None)
    for card, doms in (("J01", s5_cards.DOMAINS), ("A01", s5_cards.SOURCE_DOMAINS), ("F01", ("all",))):
        unit = s5_cards.CARDS[card]["unit"]
        for dom in doms:
            n = n_units or s5_cards.units_for(card, tier)
            alloc[f"{card}|{dom}|discovery"] = len(L.allocate(card, dom, list(s5_cards.SEEDS), n, "discovery"))
            nt = n_units or s5_cards.TRANSFER_UNITS[unit]
            alloc[f"{card}|{dom}|transfer"] = len(L.allocate(card, dom, list(s5_cards.TRANSFER_SEEDS), nt, "transfer",
                                                              world_offset=s5_worlds.TRANSFER_WORLD_OFFSET))
            nc = n_units or s5_cards.CONFIRMATION_UNITS[unit]
            alloc[f"{card}|{dom}|confirmation"] = len(L.allocate(card, dom, list(s5_cards.CONFIRMATION_SEEDS), nc, "confirmation",
                                                                  world_offset=s5_worlds.CONFIRMATION_WORLD_OFFSET))
    for card, parent in s5_cards.DERIVED.items():
        for dom in (s5_cards.CARDS[card]["domains"] or ["all"]):
            for split in ("discovery", "transfer", "confirmation"):
                parents = [lid for lid, r in L.rows.items() if r["card"] == parent and r["domain"] == dom
                           and r["split"] == split and r.get("parent") is None]
                alloc[f"{card}|{dom}|{split}"] = len([L.derive(p, card.lower(), card=card) for p in parents])
    frozen = {"readers": {r: gates[r]["revision"] for r in admitted},
              "checkpoint2": {"reader": s5_lib.CHECKPOINT2, "admitted": ckpt2_ok, "revision": gates[s5_lib.CHECKPOINT2]["revision"]},
              "design_version": s5_lib.DESIGN, "track_gates": track_gates,
              "tier": tier, "label": label, "throughput_multiplier": round(mult, 3),
              "gpu_estimate_hours": {"minimum": est_min, "expanded": est_exp},
              "primary_contrasts": {c: s5_cards.CARDS[c]["primary"] for c in s5_cards.CARDS},
              "thresholds": {c: s5_cards.CARDS[c]["threshold"] for c in s5_cards.CARDS},
              "gates": {"reader": GATE, "route_information_floor_nats": 0.05, "leakage_tolerance": 0.10,
                        "realization_floor": 0.80},
              "parser_version": s5_lib.PARSER_VERSION, "readout_version": s5_lib.READOUT_VERSION,
              "construction_seeds": list(s5_cards.SEEDS), "transfer_seeds": list(s5_cards.TRANSFER_SEEDS),
              "confirmation_seeds": list(s5_cards.CONFIRMATION_SEEDS), "output_root": str(S5),
              "lineages_allocated": alloc}
    contract.freeze("design", frozen)
    write_registry("WORKLOAD_LOCK", {"tier": tier, "label": label, "multiplier": round(mult, 3),
                                     "estimate_hours": est_min if tier == "minimum" else est_exp,
                                     "closure_allowance_hours": closure, "written_at": now_iso(),
                                     "note": "written before any discovery output; run-until-empty governs the clock"})
    write_json(out / "gates.json", gates)
    outcome = "INFRASTRUCTURE" if admitted else "INSTRUMENT_FAILED"
    write_json(out / "verdict.json", {"card": "I02", "exec": "COMPLETE", "outcome": outcome,
                                      "readers_admitted": admitted, "checkpoint2_admitted": ckpt2_ok,
                                      "tier": tier, "label": label, "n_expected_cells": len(cells),
                                      "gpu_lock_min": round(gs.held_s / 60, 2), "minutes": round((time.time() - t0) / 60, 2),
                                      "reason": None if admitted else "both readers failed the gate; model tracks close",
                                      "marker": completion_marker({"pilot": str(out / "PILOT.json")},
                                                                  {"gates": str(out / "gates.json")}, contract)})
    print(f"I02: admitted {admitted}, checkpoint2 {ckpt2_ok}, tier {tier} ({label}), est {est_min['total']}h / {est_exp['total']}h")
    return 0


# ── I03: liveness, surface matching, leakage, collisions, lineage audit ───────────────

def arm_i03() -> int:
    t0 = time.time()
    out = _card_dir("I03")
    contract = RunContract5.load()
    L = Lineages5()
    identities: dict = {}
    dup = []
    live: dict = {}
    lengths: dict = {}
    twins = 0
    natural_collisions = 0
    surfaces: dict = {}
    X, yb, yc = [], [], []
    for lid, r in sorted(L.rows.items()):
        if r.get("parent"):
            continue
        card, dom, split = r["card"], r["domain"], r["split"]
        if card == "J01":
            w = s5_worlds.make_joint_world(lid, dom)
            h = construction_hash({k: v for k, v in w.items() if k != "base"} | {"base": construction_hash(w["base"])})
            for k in ("episode_goal", "standing_preference"):
                live.setdefault(f"J01|{split}|{k}", set()).add(w[k])
            live.setdefault(f"J01|{split}|plan_first_step", set()).add(w["process_plan"][0])
        elif card == "A01":
            w = s5_sources.make_source_world(lid, dom)
            h = construction_hash(w)
            t = s5_sources.collision_twin(w)
            twins += 1
            assert t["text"] == w["text"]
            surfaces.setdefault((dom, split, w["text"]), []).append(lid)
            for k in s5_sources.FACTORS:
                live.setdefault(f"A01|{split}|{k}", set()).add(w["factors"][k])
            lengths.setdefault(w["region"], []).append(len(w["text"].split()))
            if split == "discovery":
                X.append(w["text"])
                yb.append(w["factors"]["belief"])
                yc.append(w["factors"]["correction"])
        elif card == "F01":
            w = s5_worlds.make_foraging_set(lid)
            h = construction_hash(w)
        else:
            continue
        if h in identities:
            dup.append((identities[h], lid))
        identities[h] = lid
    natural_collisions = sum(1 for v in surfaces.values() if len(v) > 1)
    # leakage: bag-of-words logistic regression to each hidden factor, 5-fold
    leak = {}
    try:
        from sklearn.feature_extraction.text import CountVectorizer                # noqa: PLC0415
        from sklearn.linear_model import LogisticRegression                       # noqa: PLC0415
        from sklearn.model_selection import cross_val_score                       # noqa: PLC0415
        import numpy as np                                                        # noqa: PLC0415
        Xv = CountVectorizer(min_df=2).fit_transform(X)
        for name, y in (("belief", yb), ("correction", yc)):
            y = np.asarray(y)
            if len(set(y)) < 2 or len(y) < 10:
                leak[name] = {"status": "too few worlds"}
                continue
            acc = float(cross_val_score(LogisticRegression(max_iter=1000), Xv, y, cv=min(5, len(y) // 4)).mean())
            chance = max(float(np.mean(y == v)) for v in set(y))
            leak[name] = {"cv_accuracy": acc, "chance": chance, "leaked": acc > chance + 0.10}
    except Exception as e:                                                       # noqa: BLE001
        leak = {"error": repr(e)}
    dead = {k: sorted(v) for k, v in live.items() if len(v) < 2}
    length_ok = True
    if lengths:
        means = {k: sum(v) / len(v) for k, v in lengths.items()}
        m = sum(means.values()) / len(means)
        length_ok = all(abs(x - m) / m <= 0.10 for x in means.values())
    audit = {"root_constructions": len(identities), "duplicates": dup, "dead_levels": dead,
             "surface_length_by_region": {k: round(sum(v) / len(v), 1) for k, v in lengths.items()},
             "surface_length_matched_10pct": length_ok, "leakage": leak,
             "collision_twins": twins, "natural_surface_collisions": natural_collisions,
             "written_at": now_iso()}
    write_registry("CONSTRUCTION_IDENTITIES", audit)
    leaked = [k for k, v in leak.items() if isinstance(v, dict) and v.get("leaked")]
    ok = not dup and not dead and not leaked
    write_json(out / "verdict.json", {"card": "I03", "exec": "COMPLETE", "outcome": "INFRASTRUCTURE" if ok else "INSTRUMENT_FAILED",
                                      "reason": None if ok else f"duplicates={len(dup)} dead={list(dead)} leaked={leaked}",
                                      "leaked_attributions": leaked, "minutes": round((time.time() - t0) / 60, 2),
                                      "marker": completion_marker({}, {"identities": str(S5 / "CONSTRUCTION_IDENTITIES.json")}, contract)})
    print(f"I03: roots {len(identities)}, dups {len(dup)}, dead {list(dead)}, leak {json.dumps(leak)}, length ok {length_ok}")
    return 0


# ── I04: route information matrix and regime confusion floor ─────────────────────────

def arm_i04() -> int:
    t0 = time.time()
    out = _card_dir("I04")
    contract = RunContract5.load()
    floor = (contract.frozen("design") or {}).get("gates", {}).get("route_information_floor_nats", 0.05)
    L = Lineages5()
    matrix = {}
    passing = 0
    total = 0
    for lid, r in sorted(L.rows.items()):
        if r["card"] != "J01" or r.get("parent"):
            continue
        w = s5_worlds.make_joint_world(lid, r["domain"])
        info = s5_worlds.route_information(w)
        matrix[lid] = {k: (v if not isinstance(v, dict) else {kk: round(vv, 4) if isinstance(vv, float) else vv for kk, vv in v.items()})
                       for k, v in info.items()}
        matrix[lid]["passes_floor"] = info["divergence"] >= floor
        passing += matrix[lid]["passes_floor"]
        total += 1
    # regime confusion floor: how many regions are consistent with a source world's surface
    regions_by_surface: dict = {}
    for lid, r in L.rows.items():
        if r["card"] != "A01" or r.get("parent") or r["split"] != "discovery":
            continue
        w = s5_sources.make_source_world(lid, r["domain"])
        t = s5_sources.collision_twin(w)
        regions_by_surface[lid] = sorted({w["region"], t["region"]})
    identifiable = sum(1 for v in regions_by_surface.values() if len(v) == 1)
    write_registry("ROUTE_INFORMATION", {"floor_nats": floor, "worlds": matrix, "n_worlds": total,
                                         "n_passing_floor": passing, "fraction_passing": (passing / total) if total else None,
                                         "regime_confusion": {"n_source_worlds": len(regions_by_surface),
                                                              "surface_identifiable": identifiable,
                                                              "fraction_identifiable": (identifiable / len(regions_by_surface)) if regions_by_surface else None},
                                         "written_at": now_iso()})
    ok = total > 0 and passing >= min(8, max(1, total // 2))
    write_json(out / "verdict.json", {"card": "I04", "exec": "COMPLETE", "outcome": "INFRASTRUCTURE" if ok else "INSTRUMENT_FAILED",
                                      "reason": None if ok else "fewer than eight worlds pass the route divergence floor; model-choice cards void",
                                      "n_passing_floor": passing, "n_worlds": total, "minutes": round((time.time() - t0) / 60, 2),
                                      "marker": completion_marker({}, {"routes": str(S5 / "ROUTE_INFORMATION.json")}, contract)})
    print(f"I04: {passing}/{total} worlds pass the {floor}-nat divergence floor; regime surface-identifiable {identifiable}/{len(regions_by_surface)}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--card", required=True, choices=["I01", "I02pilot", "I02", "I03", "I04"])
    a = ap.parse_args()
    return {"I01": arm_i01, "I02pilot": arm_i02pilot, "I02": arm_i02, "I03": arm_i03, "I04": arm_i04}[a.card]()


if __name__ == "__main__":
    sys.exit(main())
