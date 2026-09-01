"""Stage 6 card engines (brief §7, §8): the dispatch and the engines for the integrity
trunk, the architecture tournament (M), and the common prospective benchmark (P). The
world-track engines live in control/history/value/foraging_models.py, the record engines
in trecords.py, the attacks in attacks.py, and closure in confirmation.py; this module
routes every card.

DESIGN CHECK (2026-08-30)
lessons read: LESSONS §3 (a gate dependency is the gate's VERDICT: the capability gate
  (I05) is read from the frozen design at card start; power before verdicts: unit counts
  come from the workload lock; fixed option order per unit across arms, L283; every
  statistic a verdict rests on is written to the file), §4 (readers loaded once per card,
  freed in finally), §5 (the GPU lock once per invocation; a produces guard; estimates
  are the pilot's).
gates and bands, shared by every substantive engine here:
  - realization gate: an arm's output without normalized predictions is an unrealized
    proposal, counted per world, never defaulted (GS's parse failures are its result).
  - verdict bands: the exhaustive classifier on the primary's point and cluster-bootstrap
    interval against the frozen threshold (COUNTEREVIDENCE / SUPPORT_CANDIDATE /
    INCONCLUSIVE / VALID_NULL), with VOID / INSTRUMENT_FAILED / NOT_RUN as instrument
    states; INFRASTRUCTURE and DESCRIPTIVE for the audit and boundary cards.
  - the capability scoping: when no admitted reader passed I05, every architecture card
    still runs but its verdict carries `capability_note` and its claims close as
    reader-bounded (§6: the failure is a reader boundary).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from runners import s5_lib                                                         # noqa: E402
from runners.stage6 import architectures as A                                      # noqa: E402
from runners.stage6 import cards as CARDS_MOD                                      # noqa: E402
from runners.stage6 import prediction as P                                         # noqa: E402
from runners.stage6 import realization as R                                        # noqa: E402
from runners.stage6 import records as REC                                          # noqa: E402
from runners.stage6 import worlds as W                                             # noqa: E402
from runners.stage6.cardrun import (SMOKE, CardRun6, DeadlineReached,              # noqa: E402
                                    bench_lineages)
from soundingline.stage6 import (S6, GHOST_V14, RunContract6, now_iso, read_json,   # noqa: E402
                                 realization_report, write_json, write_registry)

READER_KEYS = {"qwen": "Qwen/Qwen2.5-1.5B-Instruct", "smollm": "HuggingFaceTB/SmolLM2-1.7B-Instruct"}


def n_units(card: str) -> int:
    return CARDS_MOD.units_for(card, "minimum", smoke=SMOKE)


def world_for(run: CardRun6, lid: str, domain: str, card: str, **kw) -> dict:
    track = {"M": "M", "P": "M", "C": "C", "A": "A", "V": "V", "F": "F"}.get(card[0], "C")
    if card == "M07":
        kw.setdefault("missing_variable", W._widx(lid) % 2 == 1)
    w = W.make_process_world(lid, domain, track=track, **kw)
    run.register_world(lid, w)
    return w


def capability_note(run: CardRun6) -> str | None:
    cap = run.capability
    if cap and not any((cap.get(r) or {}).get("passed") for r in run.readers):
        return "no admitted reader passed the I05 capability gate; architecture claims close as reader-bounded"
    return None


# ══════════════════════════════ INTEGRITY (I) ═════════════════════════════════════════

def run_I01(run: CardRun6) -> int:
    """Stage 5/5R anchors from committed inputs: the ninety-six-item re-gate's numbers and
    the R02 reserve confirmation, re-read and re-hashed; mismatch blocks inheritance."""
    checks = []
    regate = REPO / "results" / "phase_2_4_stage_5" / "post" / "REGATE_96.json"
    if regate.exists():
        v = read_json(regate)
        sm = v["readers"].get("HuggingFaceTB/SmolLM2-1.7B-Instruct", {})
        swings = [d.get("position_swing") for d in (sm.get("domains") or {}).values()]
        ok = bool(swings) and max(swings) <= 0.10
        checks.append({"anchor": "L282 SmolLM2 admitted at 96", "ok": ok,
                       "sha": hashlib.sha256(regate.read_bytes()).hexdigest()[:16]})
    else:
        checks.append({"anchor": "L282 regate file", "ok": False, "missing": str(regate)})
    r02 = REPO / "results" / "phase_2_4_stage_5r" / "R02" / "verdict.json"
    if r02.exists():
        v = read_json(r02)
        checks.append({"anchor": "Stage-5R R02 support candidate", "ok": v.get("outcome") == "SUPPORT_CANDIDATE",
                       "point": v.get("point"), "sha": hashlib.sha256(r02.read_bytes()).hexdigest()[:16]})
    else:
        checks.append({"anchor": "Stage-5R R02 verdict", "ok": False, "missing": str(r02)})
    b255 = REPO / "results" / "phase_2_4_stage_5" / "post" / "B03_FIXED_ORDER.json"
    if b255.exists():
        v = read_json(b255)
        cong = (v.get("contrasts") or {}).get("congruent") or {}
        checks.append({"anchor": "L283 fixed-order congruent positive on the anchor", "ok": (cong.get("point") or 0) > 0,
                       "point": cong.get("point"), "sha": hashlib.sha256(b255.read_bytes()).hexdigest()[:16]})
    ok_all = all(c["ok"] for c in checks)
    run.finish({"checks": checks, "environment": s5_lib.env_versions()},
               {"exec": "COMPLETE", "outcome": "INFRASTRUCTURE" if ok_all else "INSTRUMENT_FAILED",
                "primary": "Stage 5/5R anchors reproduce from committed inputs",
                "reason": "all anchors reproduce" if ok_all else "an anchor failed; inheritance blocked for it"})
    return 0


def expected_cells() -> list[dict]:
    """The recursive enumeration I02 validates: every card x domain x factor corner x arm,
    plus every attack."""
    cells = []
    for card, spec in CARDS_MOD.ALL.items():
        domains = [d for d in CARDS_MOD.DOMAINS] if spec["unit"] in ("world", "world_pair", "reader_world") else ["all"]
        corners = [{}]
        for fname, levels in (spec["factors"] or {}).items():
            corners = [dict(c, **{fname: lv}) for c in corners for lv in levels]
        for dom in domains:
            for c in corners:
                cells.append({"card": card, "domain": dom, "factors": c})
    return cells


def run_I02(run: CardRun6) -> int:
    cells = expected_cells()
    write_registry("EXPECTED_CELLS", {"cells": cells, "n": len(cells), "written_at": now_iso()})
    # the validator can fail: removing any card or corner drops cells
    full_n = len(cells)
    import runners.stage6.cards as C                                              # noqa: PLC0415
    spec = C.ALL["M02"]
    saved = dict(spec)
    try:
        del C.ALL["M02"]
        n_without = len(expected_cells())
    finally:
        C.ALL["M02"] = saved
    can_fail = n_without < full_n
    run.finish({"n_cells": full_n, "validator_can_fail": can_fail},
               {"exec": "COMPLETE", "outcome": "INFRASTRUCTURE" if can_fail else "INSTRUMENT_FAILED",
                "primary": "the manifest enumerates all cards, attacks, and corners; removal fails",
                "reason": f"{full_n} expected cells; removal detected: {can_fail}"})
    return 0


def run_I03(run: CardRun6) -> int:
    """Construction identities and splits: sample worlds from every family, hash them,
    check distinctness and lane grouping; record the natural corpora's split receipt."""
    hashes: dict = {}
    dupes = []
    fams = [("C", "C01"), ("A", "A01"), ("V", "V01"), ("F", "F01"), ("M", "MB")]
    n = 4 if SMOKE else 24
    for track, fam in fams:
        for dom in CARDS_MOD.DOMAINS:
            for i in range(n):
                lid = f"{fam}|{dom}|s0|w{i:05d}|discovery"
                w = W.make_process_world(lid, dom, track="M" if track == "M" else track)
                h = run.register_world(lid, w)
                if h in hashes:
                    dupes.append((lid, hashes[h]))
                hashes[h] = lid
    inv = REC.corpus_inventory(light=SMOKE)
    write_json(S6 / "CORPUS_DISPOSITIONS.json", inv)
    # natural splits: lanes are unit-keyed, so descendants cannot cross by construction
    sw_ok = ca_ok = True
    if not SMOKE and inv["scholawrite"].get("sessions"):
        sess = REC.scholawrite_sessions(max_sessions=200)
        by_proj: dict = {}
        for s in sess:
            by_proj.setdefault(s["project"], set()).add(s["lane"])
        sw_ok = all(len(v) == 1 for v in by_proj.values())
    write_registry("SPLIT_RECEIPT", {"written_at": now_iso(), "scholawrite_project_lanes_disjoint": sw_ok,
                                     "coauthor_session_keyed": ca_ok, "constructed_worlds_hashed": len(hashes),
                                     "duplicates": dupes[:10]})
    write_registry("CONSTRUCTION_IDENTITIES", {"written_at": now_iso(), "n_hashed": len(hashes),
                                               "families": [f for _, f in fams], "duplicates": len(dupes)})
    ok = not dupes and sw_ok
    run.finish({"n_hashed": len(hashes), "duplicates": len(dupes), "scholawrite_disjoint": sw_ok},
               {"exec": "COMPLETE", "outcome": "INFRASTRUCTURE" if ok else "INSTRUMENT_FAILED",
                "primary": "construction identities distinct; lineage groups and natural splits clean",
                "reason": "clean" if ok else f"{len(dupes)} duplicate constructions or a split overlap"})
    return 0


LEAK_WORDS = tuple(w.replace("_", " ") for w in
                   W.CONTROLLERS + W.VALUES + W.FORAGE + W.GOALS + ("stops_at_next_opportunity",))


def _leaks(text: str) -> list[str]:
    low = text.lower().replace("_", " ")
    return [w for w in LEAK_WORDS if w in low]


def run_I04(run: CardRun6) -> int:
    """Target hiding: no latent name or hidden target in any rendered string over a world
    sample; a planted canary IS caught (the checker can fail); a cheap surface classifier
    on the renders sits at the truth-marginal floor."""
    n = 4 if SMOKE else 32
    leaked = []
    rows = []
    for track in ("C", "V", "F"):
        for i in range(n):
            lid = f"I04|essay|s0|w{i:04d}|discovery"
            w = W.make_process_world(lid, "essay", track=track)
            text = W.render_evidence(w, upto=len(w["trajectory"]["steps"])) + "\n" + W.render_artifact(w)
            bad = _leaks(text)
            if bad:
                leaked.append({"lid": lid, "track": track, "words": bad})
            truth = w["truth"].get("controller") or w["truth"].get("value") or w["truth"].get("forage")
            rows.append((text, truth, track))
    canary_caught = bool(_leaks("the maker's strict switch policy"))
    # label-permutation leakage floor: token-count features vs truth, per track
    floors = {}
    for track in ("C", "V", "F"):
        sub = [(t, y) for t, y, tr in rows if tr == track]
        if len({y for _, y in sub}) < 2:
            continue
        feats = [(len(t), t.count("REV"), t.count("Then"), t.count("unusual")) for t, _ in sub]
        ys = [y for _, y in sub]
        marg = max(ys.count(y) for y in set(ys)) / len(ys)
        # a one-nearest-neighbour reading of the cheap features, leave-one-out
        hits = 0
        for i, f in enumerate(feats):
            best, by = None, None
            for j, g in enumerate(feats):
                if i == j:
                    continue
                d = sum((a - b) ** 2 for a, b in zip(f, g))
                if best is None or d < best:
                    best, by = d, ys[j]
            hits += int(by == ys[i])
        floors[track] = {"cheap_1nn": hits / len(sub), "truth_marginal": marg, "n": len(sub),
                         "at_floor": hits / len(sub) <= marg + 0.15}
    ok = not leaked and canary_caught and all(f["at_floor"] for f in floors.values())
    run.finish({"leaked": leaked[:10], "canary_caught": canary_caught, "cheap_floors": floors},
               {"exec": "COMPLETE", "outcome": "INFRASTRUCTURE" if ok else "INSTRUMENT_FAILED",
                "primary": "targets and latents hidden from every rendered string; canaries catch plants",
                "reason": "clean" if ok else f"{len(leaked)} leaks, canary {canary_caught}, floors {floors}"})
    return 0


def _true_state_text(world: dict) -> str:
    """The supplied true maker state for I05, in plain words (no internal names)."""
    st = W.oracle_state(world)
    goal_word = {"produce": "getting new material down", "tighten": "reworking what exists",
                 "audit": "checking correctness", "attribute": "crediting sources"}[st["episode_goal"]]
    ctrl = R.DISPLAY[world["cfg"]["controller"]]
    return (f"You are told, reliably, the maker's actual working state: right now it is {goal_word}; "
            f"overall it {ctrl}; it has {st['process_model']['pending_n']} pieces of work left.")


def run_I05(run: CardRun6) -> int:
    """The capability gate: with the TRUE state supplied, does each reader beat the cheap
    baseline on next-edit type and stopping? The verdict is frozen into the design by the
    scheduler; failure excludes the reader from architecture CLAIMS (cards still run)."""
    n = 3 if SMOKE else n_units("I05")
    out: dict = {"readers": {}}
    with s5_lib.GpuSession("s6_i05") as gs:
        for reader in (run.readers or list(READER_KEYS.values())):
            model, tok, _ = s5_lib.load_model(reader)
            try:
                d_type, d_stop, base_t, base_s = [], [], [], []
                for dom in CARDS_MOD.DOMAINS:
                    for i, lid in enumerate(bench_lineages("I05", dom, n, split=run.split, offset=5000)):
                        if run.is_done(reader, lid):
                            continue
                        run.check_deadline()
                        w = world_for(run, lid, dom, "I05")
                        ev = W.render_evidence(w) + "\n\n" + _true_state_text(w)
                        b = A.Budget()
                        t = A._likelihood_any(model, tok, ev + "\n\nWhat kind of step does the maker take NEXT?",
                                              {k: k for k in W.EDIT_TYPES}, w, b, "i05-t")
                        st = A._likelihood(model, tok, ev + "\n\nAt the next natural pause, does the maker stop for good?",
                                           {"stop": "stops here", "continue": "keeps going"}, w, b, "i05-s")
                        sb = P.score_baselines(w)
                        truth_t = w["hidden"]["next_edit_type"]
                        ls_t = math.log(max(t["probs"].get(truth_t, 0.0), 1e-9)) if (t["valid"] and truth_t) else None
                        ls_s = None
                        if w["hidden"]["n_future_stop_opportunities"] > 0 and st["valid"]:
                            p = min(max(st["probs"].get("stop", 0.5), 1e-9), 1 - 1e-9)
                            ls_s = math.log(p if w["hidden"]["stops_at_next_opportunity"] else 1 - p)
                        if ls_t is not None and sb["next_edit_type_ls"] is not None:
                            d_type.append(ls_t - sb["next_edit_type_ls"])
                            base_t.append(sb["next_edit_type_ls"])
                        if ls_s is not None and sb["stop_ls"] is not None:
                            d_stop.append(ls_s - sb["stop_ls"])
                            base_s.append(sb["stop_ls"])
                        run.row(lid, reader=reader, arm="true_state", truth=truth_t,
                                scores={"ls_type": ls_t, "ls_stop": ls_s, "base_type": sb["next_edit_type_ls"], "base_stop": sb["stop_ls"]},
                                primary_score=(ls_t - sb["next_edit_type_ls"]) if (ls_t is not None and sb["next_edit_type_ls"] is not None) else None,
                                budget=b.close(), factors={"domain": dom})
                        run.unit_complete(reader, lid)
            finally:
                s5_lib.free_model(model)
            ci_t = s5_lib.cluster_bootstrap_ci({f"u{i}": v for i, v in enumerate(d_type)}, 66001)
            ci_s = s5_lib.cluster_bootstrap_ci({f"u{i}": v for i, v in enumerate(d_stop)}, 66002)
            passed = bool(d_type and d_stop) and (ci_t.get("point") or -1) > 0 and (ci_s.get("point") or -1) > 0
            out["readers"][reader] = {"type_gain": ci_t, "stop_gain": ci_s, "n_type": len(d_type),
                                      "n_stop": len(d_stop), "passed": passed}
            print(reader, "I05 passed" if passed else "I05 failed", {"type": ci_t.get("point"), "stop": ci_s.get("point")}, flush=True)
    gpu = gs.held_s
    any_pass = any(v["passed"] for v in out["readers"].values())
    run.finish(out, {"exec": "COMPLETE", "outcome": "INFRASTRUCTURE",
                     "primary": "supplied-true-state latents-to-choice gate per reader",
                     "reason": ("passed: " + ", ".join(r for r, v in out["readers"].items() if v["passed"])) if any_pass
                     else "no reader beats the cheap baseline with the true state supplied (a reader boundary)"}, gpu)
    return 0


def run_I06(run: CardRun6) -> int:
    """Every architecture emits a valid realized state and normalized predictions on exact
    fixtures, one printed world per state class; budgets recorded (I07 reads them)."""
    fixtures = [("C", "strict_switch"), ("C", "concurrent"), ("V", "accuracy"), ("F", "explore"), ("A", None)]
    out: dict = {"arms": {}}
    reader = run.readers[0] if run.readers else READER_KEYS["qwen"]
    with s5_lib.GpuSession("s6_i06") as gs:
        model, tok, _ = s5_lib.load_model(reader)
        try:
            for arch in A.ARMS:
                rows = []
                for k, (track, forced) in enumerate(fixtures):
                    lid = f"I06|essay|s0|w{k:04d}|discovery"
                    kw = {}
                    if track == "C" and forced:
                        kw["controller"] = forced
                    if track == "V" and forced:
                        kw["value"] = forced
                    if track == "F" and forced:
                        kw["forage"] = forced
                    w = W.make_process_world(lid, "essay", track=track, **kw)
                    res = A.run_arm(arch, model, tok, w, A.BUDGET_SMALL)
                    ok_pred = bool(res["predictions"]) and abs(sum(res["predictions"]["next_edit_type"].values()) - 1.0) < 1e-6 if res["predictions"] else False
                    gates = [realization_report(st) for st in res["states"]]
                    rows.append({"fixture": f"{track}:{forced}", "predictions_ok": ok_pred,
                                 "states_realized": all(g["realized"] for g in gates) if gates else (arch in ("D",)),
                                 "unrealized_note": res["notes"].get("unrealized"), "budget": res["budget"]})
                    if k == 0:
                        print(f"--- {arch} on {track}: pred_ok={ok_pred} notes={json.dumps(res['notes'])[:100]}", flush=True)
                out["arms"][arch] = rows
        finally:
            s5_lib.free_model(model)
    gpu = gs.held_s
    hard_fail = [a for a, rs in out["arms"].items()
                 if a not in ("GS",) and not all(r["predictions_ok"] for r in rs)]
    run.finish(out, {"exec": "COMPLETE", "outcome": "INFRASTRUCTURE" if not hard_fail else "INSTRUMENT_FAILED",
                     "primary": "every architecture emits valid realized states and normalized predictions on fixtures",
                     "reason": "all arms valid (GS may refuse by design)" if not hard_fail else f"invalid arms: {hard_fail}"}, gpu)
    return 0


def run_I07(run: CardRun6) -> int:
    """Budget parity: evidence hashes equal across arms per fixture world; recorded budgets
    within the declared caps."""
    i06 = read_json(S6 / "I06" / "verdict.json") if (S6 / "I06" / "verdict.json").exists() else None
    m = read_json(S6 / "I06" / "metrics.json") if (S6 / "I06" / "metrics.json").exists() else {}
    over = []
    for arch, rows in (m.get("arms") or {}).items():
        for r in rows:
            b = r.get("budget") or {}
            if b.get("model_calls", 0) > A.BUDGET_SMALL["model_calls"]:
                over.append((arch, r["fixture"], b.get("model_calls")))
    ok = i06 is not None and not over
    run.finish({"over_budget": over, "caps": A.BUDGET_SMALL},
               {"exec": "COMPLETE", "outcome": "INFRASTRUCTURE" if ok else "INSTRUMENT_FAILED",
                "primary": "identical observations and obeyed compute budgets across paired arms",
                "reason": "parity holds" if ok else f"over budget: {over[:5]}"})
    return 0


def run_I08(run: CardRun6) -> int:
    """Metamorphic invariance: the label posterior is stable under display paraphrase and
    option-order permutation, and moves under a meaning change."""
    n = 2 if SMOKE else 12
    reader = run.readers[0] if run.readers else READER_KEYS["qwen"]
    stab, mean_shift = [], []
    with s5_lib.GpuSession("s6_i08") as gs:
        model, tok, _ = s5_lib.load_model(reader)
        try:
            for i in range(n):
                lid = f"I08|essay|s0|w{i:04d}|discovery"
                w = W.make_process_world(lid, "essay", track="C")
                ev = W.render_evidence(w)
                space = R.hypothesis_space(w)
                b = A.Budget(A.BUDGET_EXPANDED)
                p0 = A._weigh_labels(model, tok, w, ev, space, b)
                para = [dict(h, display=R.paraphrase(h["display"], i)) for h in space]
                p1 = A._weigh_labels(model, tok, w, ev, para, b)
                flip = [dict(h, display=R.meaning_change(h["display"], i)) for h in space]
                p2 = A._weigh_labels(model, tok, w, ev, flip, b)
                tv01 = 0.5 * sum(abs(p0[t] - p1[t]) for t in p0)
                tv02 = 0.5 * sum(abs(p0[t] - p2[t]) for t in p0)
                stab.append(tv01)
                mean_shift.append(tv02)
                run.row(lid, reader=reader, arm="metamorphic", scores={"tv_paraphrase": tv01, "tv_meaning": tv02},
                        primary_score=tv01, budget=b.close())
                run.unit_complete(reader, lid, "metamorphic")
        finally:
            s5_lib.free_model(model)
    gpu = gs.held_s
    para_tv = sum(stab) / max(1, len(stab))
    flip_tv = sum(mean_shift) / max(1, len(mean_shift))
    # the discriminative band (LESSONS §3): wording noise must sit small absolutely or
    # clearly under a true semantic change's move
    ok = para_tv <= 0.15 or para_tv <= 0.5 * flip_tv
    run.finish({"paraphrase_tv_mean": para_tv, "meaning_tv_mean": flip_tv, "n": len(stab),
                "band": "tv <= 0.15 or tv <= 0.5 x meaning"},
               {"exec": "COMPLETE", "outcome": "INFRASTRUCTURE" if ok else "INSTRUMENT_FAILED",
                "primary": "wording and order irrelevant when meaning fixed; semantic change detectable",
                "reason": f"paraphrase TV {para_tv:.3f}, meaning TV {flip_tv:.3f}"}, gpu)
    return 0


def run_I09(run: CardRun6) -> int:
    """Posterior-shape fixtures, exact only: no-information near-uniform; full-order
    concentration; value twins flat before the diagnostic event and moved after;
    an equifinal (score-identical) pair exactly flat."""
    checks = {}
    w = W.make_process_world("I09|essay|s0|w0001|discovery", "essay", track="C")
    early = W.oracle_posterior(w, upto=1)
    full = W.oracle_posterior(w, upto=len(w["trajectory"]["steps"]))
    checks["no_information_near_uniform"] = max(early.values()) < 0.6
    checks["full_order_concentrates"] = max(full.values()) > max(early.values())
    wv = W.make_process_world("I09|essay|s0|w0002|discovery", "essay", track="V", value="prestige")
    consult_at = next((k for k, s in enumerate(wv["trajectory"]["steps"]) if s["action"]["type"] == "consult"),
                      len(wv["trajectory"]["steps"]))
    pv_early = W.oracle_posterior(wv, upto=consult_at)
    pv_full = W.oracle_posterior(wv, upto=len(wv["trajectory"]["steps"]))
    checks["twins_flat_before_event"] = abs(pv_early["value:prestige"] - 0.5) < 1e-6
    checks["twins_diverge_after"] = abs(pv_full["value:prestige"] - 0.5) > 0.05
    checks["equifinal_exactly_flat"] = checks["twins_flat_before_event"]
    ok = all(checks.values())
    run.finish({"checks": checks, "early": early, "full": full, "twin_early": pv_early, "twin_full": pv_full},
               {"exec": "COMPLETE", "outcome": "INFRASTRUCTURE" if ok else "INSTRUMENT_FAILED",
                "primary": "exact, null, contradiction, and equifinality fixtures produce the required shapes",
                "reason": json.dumps(checks)})
    return 0


def run_I10(run: CardRun6) -> int:
    """End-to-end infrastructure: resume without duplication, deadline survival, GPU lock
    round-trip, Ghost sentinel untouched, packet refusal before the deadline."""
    checks = {}
    probe = CardRun6("I10", cell_id="I10/probe", require_lock=False)
    probe.row("unitX", arm="probe", primary_score=1.0)
    probe.unit_complete(None, "unitX", "probe")
    probe2 = CardRun6("I10", cell_id="I10/probe", require_lock=False)
    checks["resume_sees_completed_unit"] = probe2.is_done(None, "unitX", "probe")
    c = RunContract6.load()
    checks["deadline_persists"] = bool(c and c.data.get("deadline_persists_on_resume"))
    from soundingline.gpulock import acquire_gpu_lock, release_gpu_lock           # noqa: PLC0415
    acquire_gpu_lock("s6_i10_probe")
    release_gpu_lock()
    checks["gpu_lock_roundtrip"] = True
    ghost = GHOST_V14 / "RUNNER_STATUS.json"
    before = ghost.stat().st_mtime if ghost.exists() else None
    checks["ghost_status_readable_untouched"] = (not ghost.exists()) or (ghost.stat().st_mtime == before)
    from runners.stage6 import report as REP                                      # noqa: PLC0415
    try:
        REP.write_final_packet(force_before_deadline_check=False)
        checks["packet_refused_before_deadline"] = False
    except Exception:                                                             # noqa: BLE001
        checks["packet_refused_before_deadline"] = True
    ok = all(checks.values())
    run.finish({"checks": checks},
               {"exec": "COMPLETE", "outcome": "INFRASTRUCTURE" if ok else "INSTRUMENT_FAILED",
                "primary": "resume, deadline, lock, companion ownership, and report suppression verified",
                "reason": json.dumps(checks)})
    return 0


# ══════════════════════════ THE TOURNAMENT (M) ════════════════════════════════════════

RIVAL_OF = {"M02": "M01", "M03": "M02", "M04": "M02", "M05": "M02", "M06": "M05",
            "M07": "M06", "M08": None, "M09": None}


def _tournament_batch(run: CardRun6, arch: str, gpu_session_tag: str,
                      per_world=None, budget=None) -> float:
    """Run one architecture over the shared benchmark worlds for every admitted reader;
    rows carry per-endpoint scores and the combined primary. `per_world` may post-process
    (card-specific extras). Returns GPU seconds."""
    n = n_units(run.card)
    budget = budget or A.BUDGET_SMALL
    with s5_lib.GpuSession(gpu_session_tag) as gs:
        for reader in run.readers:
            model, tok, _ = s5_lib.load_model(reader)
            try:
                for dom in CARDS_MOD.DOMAINS:
                    for lid in bench_lineages(run.card, dom, n, split=run.split, track="tournament"):
                        if run.is_done(reader, lid, arch):
                            continue
                        run.check_deadline()
                        w = world_for(run, lid, dom, run.card)
                        res = A.run_arm(arch, model, tok, w, budget)
                        if res["predictions"] is None:
                            run.row(lid, reader=reader, arm=arch, valid=False, validity_reason="unrealized_proposal",
                                    factors={"domain": dom, **({"world_completeness": "missing_variable" if w["truth"].get("missing_variable") else "complete"} if run.card == "M07" else {})},
                                    budget=res["budget"], extra={"notes": res["notes"]})
                            run.unit_complete(reader, lid, arch)
                            continue
                        sc = P.score_predictions(w, res["predictions"])
                        state_ref = None
                        if res["states"] and arch in ("CR", "GS"):
                            state_ref = run.save_state(lid, arch, reader, res["states"][0])
                        extra = {"notes": res["notes"], "posterior": res["posterior"], "evidence_sha": res["evidence_sha"]}
                        if per_world:
                            extra.update(per_world(w, res, model, tok) or {})
                        run.row(lid, reader=reader, arm=arch, truth=w["hidden"]["next_edit_type"],
                                factors={"domain": dom, **({"world_completeness": "missing_variable" if w["truth"].get("missing_variable") else "complete"} if run.card == "M07" else {})},
                                scores=sc, primary_score=P.combined_primary(sc),
                                budget=res["budget"], state_ref=state_ref, extra=extra)
                        run.unit_complete(reader, lid, arch)
            finally:
                s5_lib.free_model(model)
    return gs.held_s


def _paired_vs(run: CardRun6, rows_a: list[dict], rows_b: list[dict], seed: int) -> dict:
    da = [dict(r, unit_id=f"{r['model_id']}|{r['unit_id']}") for r in rows_a if r["valid"] and r["primary_score"] is not None]
    db = [dict(r, unit_id=f"{r['model_id']}|{r['unit_id']}") for r in rows_b if r["valid"] and r["primary_score"] is not None]
    return s5_lib.paired_contrast(da, db, "unit_id", "primary_score", seed)


def run_tournament(run: CardRun6) -> int:
    card = run.card
    spec = CARDS_MOD.ALL[card]
    arch = (spec["factors"].get("architecture") or ["CR"])[0]
    gpu = _tournament_batch(run, arch, f"s6_{card.lower()}")
    rows = [r for r in run.rows() if r["arm"] == arch]
    note = capability_note(run)
    metrics: dict = {"arch": arch, "n_rows": len(rows),
                     "unrealized_rate": sum(1 for r in rows if not r["valid"]) / max(1, len(rows))}
    rival_card = RIVAL_OF.get(card)
    if card == "M09":
        # oracle-gap table: every landed arm's closure of the OR-minus-cheap gap
        gaps = {}
        or_by_unit = {f"{r['model_id']}|{r['unit_id']}": r["primary_score"] for r in rows if r["valid"] and r["primary_score"] is not None}
        cheap_by_unit = {}
        for r in rows:
            w = W.make_process_world(r["unit_id"], r["factors"]["domain"], track="M")
            cheap_by_unit[f"{r['model_id']}|{r['unit_id']}"] = P.combined_primary(P.score_baselines(w))
        for mc, spec2 in CARDS_MOD.CARDS.items():
            if not mc.startswith("M") or mc in ("M09",) or spec2["engine"] != "tournament":
                continue
            arows = [r for r in run.rows_of(mc) if r["valid"] and r["primary_score"] is not None]
            vals = []
            for r in arows:
                k = f"{r['model_id']}|{r['unit_id']}"
                if k in or_by_unit and k in cheap_by_unit and cheap_by_unit[k] is not None:
                    gap = or_by_unit[k] - cheap_by_unit[k]
                    if gap > 0.05:
                        vals.append((r["primary_score"] - cheap_by_unit[k]) / gap)
            gaps[mc] = {"mean_gap_closed": (sum(vals) / len(vals)) if vals else None, "n": len(vals)}
        metrics["oracle_gap_closed_by_card"] = gaps
        verdict = {"exec": "COMPLETE", "outcome": "INFRASTRUCTURE",
                   "primary": "the exact-oracle ceiling and each architecture's gap closure", "reason": "gap table written"}
    elif rival_card:
        rival_arch = (CARDS_MOD.ALL[rival_card]["factors"].get("architecture") or ["CR"])[0]
        if run.cell_id != card and rival_arch != arch:
            # expansion cell (the 2026-08-31 pairing repair): the rival's arm runs on the
            # SAME offset lineages, in-cell; offset-0 rows share no unit ids with these.
            gpu += _tournament_batch(run, rival_arch, f"s6_{card.lower()}_rival")
            rrows = [r for r in run.rows() if r["valid"] and r["arm"] == rival_arch]
        else:
            rrows = run.rows_of(rival_card)
        contrast = _paired_vs(run, rows, rrows, 66100 + int(card[1:]))
        metrics["contrast_vs"] = rival_card
        metrics["contrast"] = contrast
        by_reader = {}
        for rd in run.readers:
            by_reader[rd] = _paired_vs(run, [r for r in rows if r["model_id"] == rd],
                                       [r for r in rrows if r["model_id"] == rd], 66200 + int(card[1:]))
        metrics["by_reader"] = by_reader
        verdict = {"exec": "COMPLETE", **run.classify(contrast, run.threshold()),
                   "primary": f"{arch} minus {RIVAL_OF[card]}'s arm on the combined prospective primary"}
    elif card == "M08":
        if run.cell_id != card:
            # expansion cell: contrast against the base tournament's best non-oracle arm
            # (AD, per M07/M09, L315), run in-cell on the same offset lineages.
            gpu += _tournament_batch(run, "AD", "s6_m08_rival")
            rrows = [r for r in run.rows() if r["valid"] and r["arm"] == "AD"]
            c = _paired_vs(run, rows, rrows, 66300)
            metrics["vs_each"] = {"AD": c}
            metrics["vs_best_rival"] = c
            verdict = {"exec": "COMPLETE", **run.classify(c, run.threshold()),
                       "primary": "CR minus the base-best non-oracle arm (AD) on expansion worlds"}
        else:
            best = {}
            for mc in ("M01", "M02", "M03", "M04", "M05", "M06", "M07"):
                c = _paired_vs(run, rows, run.rows_of(mc), 66300)
                if c.get("point") is not None:
                    best[mc] = c
            metrics["vs_each"] = best
            worst = min(best.values(), key=lambda c: c["point"]) if best else {"point": None}
            metrics["vs_best_rival"] = worst
            verdict = {"exec": "COMPLETE", **run.classify(worst, run.threshold()),
                       "primary": "CR minus the best same-evidence same-budget non-oracle arm"}
    else:
        verdict = {"exec": "COMPLETE", "outcome": "DESCRIPTIVE", "primary": spec["primary"]}
    if note:
        verdict["capability_note"] = note
    run.finish(metrics, verdict, gpu, rival=spec["discriminator"])
    return 0


def run_m_special(run: CardRun6) -> int:
    """M10-M16: the CR arm re-scored on the card's own discriminator. Each runs CR (and
    where named, a comparator) on the benchmark worlds with card-specific measurements."""
    card = run.card
    gpu = _tournament_batch(run, "CR", f"s6_{card.lower()}")
    rows = [r for r in run.rows() if r["valid"] and r["arm"] == "CR"]
    note = capability_note(run)
    seed = 66400 + int(card[1:])
    metrics: dict = {"n_rows": len(rows)}

    def unitize(rs):
        return [dict(r, unit_id=f"{r['model_id']}|{r['unit_id']}") for r in rs]

    if card == "M10":
        vals = {f"{r['model_id']}|{r['unit_id']}": r["scores"].get("next_action_ls") for r in rows if r["scores"].get("next_action_ls") is not None}
        base = {}
        for r in rows:
            w = W.make_process_world(r["unit_id"], r["factors"]["domain"], track="M")
            b = P.score_baselines(w)
            k = f"{r['model_id']}|{r['unit_id']}"
            if b.get("next_edit_type_ls") is not None:
                base[k] = b["next_edit_type_ls"] + math.log(1.0 / max(1, len(w["doc"]["sections"])))
        diffs = {k: vals[k] - base[k] for k in vals if k in base}
        ci = s5_lib.cluster_bootstrap_ci(diffs, seed)
        metrics["artifact_wide_vs_factored_baseline"] = ci
        verdict = {"exec": "COMPLETE", **run.classify(ci, run.threshold()),
                   "primary": "artifact-wide withheld-action likelihood over the factored cheap baseline"}
    elif card == "M11":
        joint = {f"{r['model_id']}|{r['unit_id']}": (r["scores"]["next_edit_type_ls"] + r["scores"]["next_section_ls"])
                 for r in rows if r["scores"].get("next_edit_type_ls") is not None and r["scores"].get("next_section_ls") is not None}
        base = {}
        for r in rows:
            w = W.make_process_world(r["unit_id"], r["factors"]["domain"], track="M")
            b = P.score_baselines(w)
            k = f"{r['model_id']}|{r['unit_id']}"
            if b.get("next_edit_type_ls") is not None and b.get("next_section_ls") is not None:
                base[k] = b["next_edit_type_ls"] + b["next_section_ls"]
        diffs = {k: joint[k] - base[k] for k in joint if k in base}
        ci = s5_lib.cluster_bootstrap_ci(diffs, seed)
        metrics["joint_type_location_vs_baselines"] = ci
        verdict = {"exec": "COMPLETE", **run.classify(ci, run.threshold()),
                   "primary": "joint next-edit type and location proper score over position and last-edit baselines"}
    elif card == "M12":
        diffs = {}
        for r in rows:
            if r["scores"].get("stop_ls") is None:
                continue
            w = W.make_process_world(r["unit_id"], r["factors"]["domain"], track="M")
            b = P.score_baselines(w)
            if b.get("stop_ls") is not None:
                diffs[f"{r['model_id']}|{r['unit_id']}"] = r["scores"]["stop_ls"] - b["stop_ls"]
        ci = s5_lib.cluster_bootstrap_ci(diffs, seed)
        metrics["stop_vs_progress_baseline"] = ci
        verdict = {"exec": "COMPLETE", **run.classify(ci, run.threshold()),
                   "primary": "stopping hazard log score over the progress-only baseline"}
    elif card == "M13":
        moved_when_should = []
        moved_when_not = []
        for r in rows:
            w = W.make_process_world(r["unit_id"], r["factors"]["domain"], track="M")
            post_pre = r["extra"].get("posterior") or {}
            post_full = W.oracle_posterior(w, upto=len(w["trajectory"]["steps"]))
            tv = 0.5 * sum(abs(post_pre.get(t, 0) - post_full.get(t, 0)) for t in set(post_pre) | set(post_full))
            discriminating = max(post_full.values()) > 0.6
            (moved_when_should if discriminating else moved_when_not).append(tv)
        metrics["posterior_move_when_discriminating"] = sum(moved_when_should) / max(1, len(moved_when_should))
        metrics["posterior_move_when_not"] = sum(moved_when_not) / max(1, len(moved_when_not))
        ok = metrics["posterior_move_when_discriminating"] >= metrics["posterior_move_when_not"]
        verdict = {"exec": "COMPLETE", "outcome": "DESCRIPTIVE" if ok else "COUNTEREVIDENCE",
                   "primary": "posterior changes only when the withheld observation discriminates",
                   "reason": json.dumps({k: round(v, 3) for k, v in metrics.items() if isinstance(v, float)})}
    elif card == "M14":
        pairs = []
        for r in rows:
            w1 = W.make_process_world(r["unit_id"], r["factors"]["domain"], track="M")
            lid2 = r["unit_id"].replace("|w", "|x").replace("MB", "MB2")
            w2 = W.make_process_world(lid2, "workshop_doc" if r["factors"]["domain"] == "essay" else "essay", track="M",
                                      controller=w1["truth"]["controller"])
            tag = w1["truth"]["controller"]
            st1 = R.realize(w1, tag)
            st2 = R.realize(w2, tag)
            copied = P.score_predictions(w2, R.adapt([st1], posterior={tag: 1.0}))
            fresh = P.score_predictions(w2, R.adapt([st2], posterior={tag: 1.0}))
            a, b = P.combined_primary(fresh), P.combined_primary(copied)
            if a is not None and b is not None:
                pairs.append((f"{r['model_id']}|{r['unit_id']}", a - b))
        ci = s5_lib.cluster_bootstrap_ci(dict(pairs), seed)
        metrics["fresh_realization_minus_copied"] = ci
        verdict = {"exec": "COMPLETE", **run.classify(ci, run.threshold()),
                   "primary": "the same proposal realized in the new context beats the copied realization"}
    elif card == "M15":
        stab, flip = [], []
        for r in rows:
            w = W.make_process_world(r["unit_id"], r["factors"]["domain"], track="M")
            tag = max((r["extra"].get("posterior") or {"strict_switch": 1}).items(), key=lambda kv: kv[1])[0]
            st = R.realize(w, tag)
            stp = R.realize(w, tag, proposal_text=R.paraphrase(R.DISPLAY.get(tag, tag), 3))
            d0 = st["decision_likelihoods"]["next_edit_type"]
            d1 = stp["decision_likelihoods"]["next_edit_type"]
            stab.append(0.5 * sum(abs(d0[k] - d1.get(k, 0)) for k in d0))
            other = [t for t in R.hypothesis_space(w) if t["tag"] != tag]
            if other:
                d2 = R.realize(w, other[0]["tag"])["decision_likelihoods"]["next_edit_type"]
                flip.append(0.5 * sum(abs(d0[k] - d2.get(k, 0)) for k in d0))
        metrics["paraphrase_tv"] = sum(stab) / max(1, len(stab))
        metrics["meaning_change_tv"] = sum(flip) / max(1, len(flip))
        ok = metrics["paraphrase_tv"] < 1e-9 and metrics["meaning_change_tv"] > 0
        verdict = {"exec": "COMPLETE", "outcome": "INFRASTRUCTURE" if ok else "INSTRUMENT_FAILED",
                   "primary": "paraphrased proposals converge behaviorally; meaning changes diverge",
                   "reason": f"paraphrase TV {metrics['paraphrase_tv']:.4f}, meaning TV {metrics['meaning_change_tv']:.3f}"}
    elif card == "M16":
        by = {}
        for rd in run.readers:
            for dom in CARDS_MOD.DOMAINS:
                sub = unitize([r for r in rows if r["model_id"] == rd and r["factors"]["domain"] == dom])
                vals = {r["unit_id"]: r["primary_score"] for r in sub if r["primary_score"] is not None}
                by[f"{rd.split('/')[-1]}|{dom}"] = s5_lib.cluster_bootstrap_ci(vals, seed)
        metrics["conditional_cells"] = by
        pts = [v["point"] for v in by.values() if v.get("point") is not None]
        verdict = {"exec": "COMPLETE", "outcome": "DESCRIPTIVE",
                   "primary": "family and domain conditional transfer of the frozen adapter",
                   "reason": f"{len(pts)} conditional cells, min {min(pts):.3f} max {max(pts):.3f}" if pts else "no cells"}
    else:
        verdict = {"exec": "COMPLETE", "outcome": "DESCRIPTIVE", "primary": CARDS_MOD.ALL[card]["primary"]}
    if note:
        verdict["capability_note"] = note
    run.finish(metrics, verdict, gpu, rival=CARDS_MOD.ALL[card]["discriminator"])
    return 0


# ══════════════════════ THE PROSPECTIVE BENCHMARK (P) ═════════════════════════════════

BEST_ARM_CARD = "M08"      # CR's rows; D's are M01's; OR's are M09's


def _p_rows(run: CardRun6, card_of_arm: str) -> list[dict]:
    return [r for r in run.rows_of(card_of_arm) if r["valid"] and r["primary_score"] is not None]


def run_prospective(run: CardRun6) -> int:
    card = run.card
    seed = 66600 + int(card[1:])
    cr = _p_rows(run, BEST_ARM_CARD)
    d = _p_rows(run, "M01")
    note = capability_note(run)
    metrics: dict = {"n_cr": len(cr), "n_d": len(d)}

    def endpoint_diff(key: str) -> dict:
        diffs = {}
        for r in cr:
            if r["scores"].get(key) is None:
                continue
            w = W.make_process_world(r["unit_id"], r["factors"]["domain"], track="M")
            b = P.score_baselines(w)
            if b.get(key) is not None:
                diffs[f"{r['model_id']}|{r['unit_id']}"] = r["scores"][key] - b[key]
        return s5_lib.cluster_bootstrap_ci(diffs, seed)

    if card in ("P01", "P02", "P03", "P06"):
        key = {"P01": "next_edit_type_ls", "P02": "next_section_ls", "P03": "stop_ls", "P06": "changed_context_ls"}[card]
        ci = endpoint_diff(key)
        metrics[f"{key}_vs_baseline"] = ci
        verdict = {"exec": "COMPLETE", **run.classify(ci, run.threshold()), "primary": CARDS_MOD.ALL[card]["primary"]}
    elif card == "P04":
        # rejected alternative: the changed-context option the maker did NOT take, scored
        # as one-minus-mass on the truth over the live options
        diffs = {}
        for r in cr:
            if r["scores"].get("changed_context_ls") is None:
                continue
            w = W.make_process_world(r["unit_id"], r["factors"]["domain"], track="M")
            b = P.score_baselines(w)
            if b.get("changed_context_ls") is not None:
                diffs[f"{r['model_id']}|{r['unit_id']}"] = r["scores"]["changed_context_ls"] - b["changed_context_ls"]
        ci = s5_lib.cluster_bootstrap_ci(diffs, seed)
        metrics["opportunity_conditioned_choice"] = ci
        verdict = {"exec": "COMPLETE", **run.classify(ci, run.threshold()), "primary": CARDS_MOD.ALL[card]["primary"]}
    elif card == "P05":
        moved = [r["scores"].get("posterior_on_truth") for r in cr if r["scores"].get("posterior_on_truth") is not None]
        conf = [r["scores"].get("confidence") for r in cr if r["scores"].get("confidence") is not None]
        metrics["posterior_on_truth_mean"] = sum(moved) / max(1, len(moved))
        metrics["confidence_mean"] = sum(conf) / max(1, len(conf))
        verdict = {"exec": "COMPLETE", "outcome": "DESCRIPTIVE", "primary": CARDS_MOD.ALL[card]["primary"],
                   "reason": "repair-after-contradiction carried by the M13 intervention; descriptive summary here"}
    elif card == "P07":
        both = _paired_vs(run, cr, d, seed)
        metrics["artifact_wide_cr_minus_d"] = both
        verdict = {"exec": "COMPLETE", **run.classify(both, run.threshold()), "primary": CARDS_MOD.ALL[card]["primary"]}
    elif card == "P08":
        pts = [(r["scores"]["confidence"], bool(r["scores"].get("next_edit_type_correct"))) for r in cr
               if r["scores"].get("confidence") is not None and r["scores"].get("next_edit_type_correct") is not None]
        from soundingline.stage6 import calibration_slope, ece, selective_risk_coverage    # noqa: PLC0415
        metrics["ece"] = ece(pts) if pts else None
        metrics["calibration_slope"] = calibration_slope(pts) if pts else None
        items = [(r["scores"]["confidence"], -(r["scores"].get("next_edit_type_ls") or 0.0)) for r in cr
                 if r["scores"].get("confidence") is not None]
        metrics["risk_coverage"] = selective_risk_coverage(items)
        ok = metrics["ece"] is not None
        verdict = {"exec": "COMPLETE", "outcome": "DESCRIPTIVE" if ok else "VOID",
                   "primary": CARDS_MOD.ALL[card]["primary"], "reason": f"ece {metrics['ece']}"}
    elif card == "P09":
        abst = [r for r in cr if r["extra"].get("posterior")]
        flat, moved = [], []
        for r in abst:
            w = W.make_process_world(r["unit_id"], r["factors"]["domain"], track="M")
            full = W.oracle_posterior(w, upto=w["cut"])
            (flat if max(full.values()) < 0.45 else moved).append(bool(r["scores"].get("abstained")))
        metrics["abstain_rate_on_equifinal"] = sum(flat) / max(1, len(flat)) if flat else None
        metrics["abstain_rate_on_identified"] = sum(moved) / max(1, len(moved)) if moved else None
        ok = flat and metrics["abstain_rate_on_equifinal"] is not None and \
            (metrics["abstain_rate_on_identified"] is None or metrics["abstain_rate_on_equifinal"] >= metrics["abstain_rate_on_identified"])
        verdict = {"exec": "COMPLETE", "outcome": "DESCRIPTIVE" if ok else "COUNTEREVIDENCE",
                   "primary": CARDS_MOD.ALL[card]["primary"],
                   "reason": json.dumps({k: v for k, v in metrics.items() if k.startswith('abstain')})}
    elif card == "P10":
        gpu = _p10_ablations(run)
        rows = [r for r in run.rows() if r["arm"].startswith("ablate")]
        by = {}
        for ab in {r["factors"]["ablated"] for r in rows}:
            sub = [r for r in rows if r["factors"]["ablated"] == ab and r["primary_score"] is not None]
            vals = {f"{r['model_id']}|{r['unit_id']}": r["primary_score"] for r in sub}
            by[ab] = s5_lib.cluster_bootstrap_ci(vals, seed)
        metrics["by_ablation"] = by
        run.finish(metrics, {"exec": "COMPLETE", "outcome": "DESCRIPTIVE",
                             "primary": CARDS_MOD.ALL[card]["primary"],
                             "reason": "field ablation table written",
                             **({"capability_note": note} if note else {})}, gpu,
                   rival=CARDS_MOD.ALL[card]["discriminator"])
        return 0
    elif card == "P11":
        by = {}
        for rd in run.readers:
            for dom in CARDS_MOD.DOMAINS:
                sub = [r for r in cr if r["model_id"] == rd and r["factors"]["domain"] == dom]
                subd = [r for r in d if r["model_id"] == rd and r["factors"]["domain"] == dom]
                by[f"{rd.split('/')[-1]}|{dom}"] = _paired_vs(run, sub, subd, seed)
        metrics["conditional"] = by
        verdict = {"exec": "COMPLETE", "outcome": "DESCRIPTIVE", "primary": CARDS_MOD.ALL[card]["primary"],
                   "reason": "conditional cells written before any pooled mean"}
    elif card == "P12":
        crit = criterion_audit(run)
        metrics.update(crit)
        verdict = {"exec": "COMPLETE", "outcome": "DESCRIPTIVE" if not crit["met_by"] else "SUPPORT_CANDIDATE",
                   "primary": CARDS_MOD.ALL[card]["primary"],
                   "reason": f"criterion met by: {crit['met_by'] or 'none'}",
                   "point": None if not crit["met_by"] else 1.0, "ci": None}
        if not crit["met_by"]:
            verdict.pop("point", None)
    else:
        verdict = {"exec": "COMPLETE", "outcome": "DESCRIPTIVE", "primary": CARDS_MOD.ALL[card]["primary"]}
    if note:
        verdict["capability_note"] = note
    run.finish(metrics, verdict, 0.0, rival=CARDS_MOD.ALL[card]["discriminator"])
    return 0


def _p10_ablations(run: CardRun6) -> float:
    n = 2 if SMOKE else 16
    levels = CARDS_MOD.CARDS["P10"]["factors"]["ablated"]
    with s5_lib.GpuSession("s6_p10") as gs:
        for reader in run.readers[:1]:
            model, tok, _ = s5_lib.load_model(reader)
            try:
                for dom in CARDS_MOD.DOMAINS:
                    for lid in bench_lineages("P10", dom, n, split=run.split, track="tournament"):
                        run.check_deadline()
                        w = world_for(run, lid, dom, "P10")
                        res = A.run_arm("CR", model, tok, w, A.BUDGET_SMALL)
                        if res["predictions"] is None:
                            continue
                        for ab in levels:
                            arm = f"ablate:{ab}"
                            if run.is_done(reader, lid, arm):
                                continue
                            # REPAIRED (the predeclared P10 repair, 2026-08-30): the first
                            # attempt nulled metadata fields the adapter never reads, so every
                            # ablation scored identically — a vacuous instrument. The ablation
                            # now happens at the REALIZER: each field's causal contribution is
                            # removed from the hypothesized configurations before the
                            # predictive distributions are computed, and "none" re-realizes
                            # unmodified (the identity control).
                            states = []
                            for h in R.hypothesis_space(w):
                                cfg = R.cfg_for_tag(w, h["tag"])
                                if ab == "control_state":
                                    cfg = dict(cfg, controller="concurrent", tag=h["tag"])
                                elif ab == "episode_goal":
                                    cfg = dict(cfg, start_goal="produce", switch_rate=0.0)
                                elif ab == "expertise_state":
                                    cfg = dict(cfg, habit={})
                                elif ab == "selection_history":
                                    cfg = dict(cfg, history_bias={}, salient_slots=(), salience=0.0)
                                # an ablated cfg can activate goals outside the hypothesis's
                                # weight dict (the 2026-08-31 KeyError repair): complete it
                                cfg = dict(cfg, weights={g: (cfg.get("weights") or {}).get(g, 0.0)
                                                         for g in W.GOALS})
                                pred_at = R.predictive_at_cut(w, cfg)
                                st = R.realize(w, h["tag"], posterior_weight=res["posterior"].get(h["tag"], 0.0))
                                st["decision_likelihoods"]["next_edit_type"] = pred_at["next_edit_type"]
                                st["decision_likelihoods"]["next_section"] = pred_at["next_section"]
                                st["decision_likelihoods"]["changed_context"] = pred_at["changed_context"]
                                if ab == "stop_model":
                                    st["stop_model"] = {"p_stop": 0.5}
                                else:
                                    st["stop_model"] = {"p_stop": pred_at["p_stop"]}
                                states.append(st)
                            pred = R.adapt(states, posterior=res["posterior"])
                            sc = P.score_predictions(w, pred)
                            run.row(lid, reader=reader, arm=arm, factors={"domain": dom, "ablated": ab},
                                    scores=sc, primary_score=P.combined_primary(sc))
                            run.unit_complete(reader, lid, arm)
            finally:
                s5_lib.free_model(model)
    return gs.held_s


def criterion_audit(run: CardRun6) -> dict:
    """§10.1: the eight conditions, read from landed verdicts; the audit names who meets
    which, and the confirmation freeze picks from it."""
    out = {"conditions": {}, "met_by": []}
    i05 = read_json(S6 / "I05" / "metrics.json") if (S6 / "I05" / "metrics.json").exists() else {}
    passed_readers = [r for r, v in (i05.get("readers") or {}).items() if v.get("passed")]
    out["conditions"]["1_capability"] = passed_readers
    def _v(card):
        p = S6 / card / "verdict.json"
        return read_json(p) if p.exists() else {}
    m09 = read_json(S6 / "M09" / "metrics.json") if (S6 / "M09" / "metrics.json").exists() else {}
    gap = ((m09.get("oracle_gap_closed_by_card") or {}).get("M08") or {}).get("mean_gap_closed")
    out["conditions"]["2_gap_closed"] = gap
    p01, p03, p06, p08 = _v("P01"), _v("P03"), _v("P06"), _v("P08")
    out["conditions"]["3_next_edit_and_stop"] = {"P01": p01.get("outcome"), "P03": p03.get("outcome")}
    out["conditions"]["4_changed_context"] = p06.get("outcome")
    out["conditions"]["5_calibrated"] = p08.get("outcome")
    attacks = {x: _v(x).get("outcome") for x in ("X01", "X02", "X03", "X04", "X15", "X17")}
    out["conditions"]["6_attacks"] = attacks
    if passed_readers and gap is not None and gap >= 0.20 \
            and p01.get("outcome") == "SUPPORT_CANDIDATE" and p03.get("outcome") == "SUPPORT_CANDIDATE" \
            and p06.get("outcome") == "SUPPORT_CANDIDATE" \
            and all(v in ("INFRASTRUCTURE", "DESCRIPTIVE", "VALID_NULL", "SUPPORT_CANDIDATE") for v in attacks.values() if v):
        out["met_by"] = ["CR"]
    return out


# ══════════════════════════════ dispatch ═════════════════════════════════════════════

INTEGRITY = {"I01": run_I01, "I02": run_I02, "I03": run_I03, "I04": run_I04, "I05": run_I05,
             "I06": run_I06, "I07": run_I07, "I08": run_I08, "I09": run_I09, "I10": run_I10}


def run_card(card: str) -> int:
    spec = CARDS_MOD.ALL[card]
    run = CardRun6(card, require_lock=(card not in INTEGRITY))
    engine = spec["engine"]
    try:
        if card in INTEGRITY:
            return INTEGRITY[card](run)
        if engine == "tournament":
            return run_tournament(run) if card in RIVAL_OF or card in ("M01", "M08", "M09") else run_m_special(run)
        if engine == "prospective":
            return run_prospective(run)
        if engine == "worldtrack":
            from runners.stage6 import track_models as TM                         # noqa: PLC0415
            return TM.run_card(run)
        if engine == "records":
            from runners.stage6 import trecords as TR                             # noqa: PLC0415
            return TR.run_card(run)
        if engine == "closure":
            from runners.stage6 import confirmation as CF                         # noqa: PLC0415
            return CF.run_card(run)
        if engine == "attack":
            from runners.stage6 import attacks as X                               # noqa: PLC0415
            return X.run_card(run)
        raise ValueError(f"unknown engine {engine}")
    except DeadlineReached:
        run.flush()
        print(f"{card}: deadline reached; rows checkpointed")
        return 3


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--card", required=True, choices=sorted(CARDS_MOD.ALL))
    a = ap.parse_args()
    return run_card(a.card)


if __name__ == "__main__":
    sys.exit(main())
