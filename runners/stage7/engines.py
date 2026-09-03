"""Stage 7 engines (brief §10-§12): the dispatch for every question and attack, the
shared batch machinery (worlds to evidence and oracle bundles, capsules per unit and arm,
the model server inside ONE GPU session per invocation, scoring after the reader process
exits, rows at the independent unit), the frozen common-domain model, and the isolation
(I) and dependency (D) trunks. The supplied-state, reconstruction, and architecture
trunks live in engine_supplied.py; the prospective, history, and closure trunks in
engine_prospective.py; the attacks in attacks.py; confirmations in confirmation.py.

DESIGN CHECK (2026-09-02)
lessons read: LESSONS §3 (a gate dependency is the verdict: every downstream engine reads
  the GATES registry; the criterion can fail: every invariance question carries a
  should-break case; blind floors: U and DOM rows sit beside every arm; power before
  verdicts: unit counts come from the workload lock), §4 (instruct readers only; measured
  revisions recorded), §5 (one GPU session per invocation; produces guards; retries;
  the deadline is checked between units; kill by pid).
gates and bands (this module's):
  - I04 (access): NULL of a broken boundary is any probe attempt not raised; ALTERNATIVE:
    all raised; failure direction: one un-raised attempt fails DOWN and blocks the lock.
  - I05/I06/I07 (mutation invariance): NULL of a leaking arm is any non-oracle prediction
    whose canonical bytes differ between a world and its twin (fails DOWN,
    INSTRUMENT_FAILED); ALTERNATIVE: every pair identical; the should-break case: the
    ORACLE's numbers differ across the twins (an invariance that holds for the oracle too
    would mean the mutation did nothing).
  - I08 (sensitivity): NULL of a blind reader is a total-variation move under the
    diagnostic visible flip under 0.02 (fails DOWN); ALTERNATIVE: at or above 0.02; DOM
    is exempt by construction (it reads no outcomes) and reported, never gated.
  - I10 (canaries): NULL of a leaky detector is any planted canary uncaught (fails DOWN)
    or a clean-null detector above chance plus two standard errors (fails UP);
    ALTERNATIVE: every canary caught and the clean null at floor.
  bands: exhaustive (INFRASTRUCTURE / INSTRUMENT_FAILED / VOID when no rows).
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import secrets
import subprocess
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from runners import s5_lib                                                         # noqa: E402
from runners.stage7 import cards as C                                              # noqa: E402
from runners.stage7 import runtime as RT                                           # noqa: E402
from runners.stage7.cardrun import SMOKE, CardRun7, DeadlineReached                # noqa: E402
from runners.stage7.constructor import oracle as ORC                               # noqa: E402
from runners.stage7.constructor import worlds as W                                 # noqa: E402
from runners.stage7.manifest import lineage_ids                                    # noqa: E402
from runners.stage7.scoring import prospective as PS                               # noqa: E402
from soundingline.stage7 import (S7, MIN_GAP_NATS, RunContract7, canonical_prediction,  # noqa: E402
                                 evidence_sha, gate_state, ghost_receipt, now_iso,
                                 prediction_sha, read_json, read_jsonl, read_registry,
                                 set_gate, tv, validate_prediction, validate_visible_evidence,
                                 write_json, write_registry, update_registry)

SEED = 71000
PY = sys.executable
MODEL_ARMS = {"DIR", "DIRS", "SLJ", "HDIR", "CDIR", "SDIR", "weighted_language_hypotheses", "sequential_hypothesis_particles",
              "adaptive_factor_expansion", "synthesized_agent_model", "epistemic_translation"}
FACTOR_SIG = {"proximal_goal": "goal", "belief_state": "belief", "expertise_law": "law", "history_residue": "residue"}


def n_units(card: str) -> int:
    return C.units_for(card, "minimum", smoke=SMOKE)


# ── the model server inside one GPU session ──────────────────────────────────────────

class ModelServer:
    """Starts runners/stage7/model_server.py inside the engine's GPU session; the capsule
    endpoint and token; the per-token ledger read at close (I13)."""

    def __init__(self, tag: str, models: list[str]):
        self.tag = tag
        self.models = [m for m in models if m]
        self.proc = None
        self.port = None
        self.token = secrets.token_hex(12)
        self.gs = None
        self.ledger: dict = {}
        self.held_s = 0.0

    def __enter__(self):
        if not self.models:
            return self
        fake = bool(os.environ.get("S7_FAKE_SERVER"))
        if not fake:
            self.gs = s5_lib.GpuSession(self.tag)
            self.gs.__enter__()
        self.port = RT.free_port()
        ready = S7 / f".model_server_{self.tag}.json"
        if ready.exists():
            ready.unlink()
        log = open(S7 / f"model_server_{self.tag}.log", "a", encoding="utf-8")
        self.proc = subprocess.Popen([PY, str(REPO / "runners" / "stage7" / "model_server.py"), "--port", str(self.port),
                                      "--token", self.token, "--models", ",".join(self.models), "--ready-file", str(ready)]
                                     + (["--fake"] if fake else []),
                                     cwd=str(REPO), stdout=log, stderr=subprocess.STDOUT)
        for _ in range(120):
            if ready.exists():
                break
            time.sleep(1)
        if not ready.exists():
            raise RuntimeError("model server did not start")
        return self

    @property
    def endpoint(self) -> str:
        return f"http://127.0.0.1:{self.port}" if self.port else "http://127.0.0.1:1"

    def stats(self) -> dict:
        if not self.port:
            return {}
        import urllib.request                                                     # noqa: PLC0415
        try:
            opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
            return json.loads(opener.open(f"{self.endpoint}/stats", timeout=30).read())
        except Exception:                                                         # noqa: BLE001
            return {}

    def __exit__(self, *exc):
        if self.proc is not None:
            self.ledger = self.stats().get("ledger", {})
            import urllib.request                                                 # noqa: PLC0415
            try:
                opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
                req = urllib.request.Request(f"{self.endpoint}/shutdown", data=b"{}",
                                             headers={"Content-Type": "application/json", "X-S7-Token": self.token})
                opener.open(req, timeout=30).read()
                self.proc.wait(timeout=120)
            except Exception:                                                     # noqa: BLE001
                self.proc.kill()
        if self.gs is not None:
            self.gs.__exit__(*exc)
            self.held_s = self.gs.held_s
        return False


# ── the frozen common-domain model (K03, DOM) ────────────────────────────────────────

def fit_dom(n: int = 96) -> dict:
    """Fit on the dedicated dom-fit family (discovery lane, offset band 60000): type
    transitions by progress bucket and last type, section position by bucket, stop rate
    by bucket and over-length, decision marginals, all with add-one smoothing."""
    tt: dict = {}
    sp: dict = {}
    stop: dict = {}
    lens = []
    inval = {"correct": 1, "retain": 1, "rewrite": 1}
    bt = {"satisfaction": 1, "deadline": 1, "fatigue": 1, "equivalent": 1}
    for dom in C.DOMAINS:
        for i in range(n):
            w = W.make_world(f"WD|{dom}|s0|w{60000 + i:05d}|discovery", dom)
            if w["degenerate"]:
                continue
            steps = w["trajectory"]["steps"]
            lens.append(len(steps))
            total = len(w["inventory"])
            done = 0
            last = "none"
            sections = [s["name"] for s in w["doc"]["sections"]]
            for k, s in enumerate(steps):
                b = "early" if done / total < 0.34 else ("mid" if done / total < 0.67 else "late")
                tt.setdefault(f"{b}|{last}", {}).setdefault(s["type"], 0)
                tt[f"{b}|{last}"][s["type"]] += 1
                idx = str(min(sections.index(s["section"]), 3))
                sp.setdefault(b, {}).setdefault(idx, 0)
                sp[b][idx] += 1
                over = "over" if k + 1 > 12 else "under"
                key = f"{b}|{over}"
                stop.setdefault(key, [0, 0])
                stop[key][1] += 1
                if w["trajectory"]["stopped_at"] == s["i"]:
                    stop[key][0] += 1
                if s["outcome"] == "done":
                    done += 1
                last = s["type"]
            inv = w["hidden"]["invalidation"]["choice"]
            inval[inv] = inval.get(inv, 0) + 1
            if w["hidden"]["stop_next"] and w["hidden"]["boundary_type"] in bt:
                bt[w["hidden"]["boundary_type"]] += 1
    out = {"type_trans": {k: {t: (v.get(t, 0) + 1) / (sum(v.values()) + len(W.ACTION_TYPES)) for t in W.ACTION_TYPES} for k, v in tt.items()},
           "section_pos": {b: {i: (c + 1) / (sum(v.values()) + 4) for i, c in v.items()} for b, v in sp.items()},
           "stop": {k: (a + 1) / (b + 2) for k, (a, b) in stop.items()},
           "mean_len": sum(lens) / max(1, len(lens)),
           "invalidation": {k: v / sum(inval.values()) for k, v in inval.items()},
           "boundary": {k: v / sum(bt.values()) for k, v in bt.items()},
           "fitted_on": {"family": "WD", "n_per_domain": n, "lane": "discovery", "at": now_iso()}}
    out["stop"]["all"] = sum(a for a, b in stop.values()) / max(1, sum(b for a, b in stop.values()))
    return out


def dom_params() -> dict | None:
    return read_registry("DOM_FROZEN")


# ── the shared batch: worlds to rows ─────────────────────────────────────────────────

def build_condition(spec_cond: dict, unit_ref: str, condition_ref: str, regime: str | None = None,
                    render: str = "prose") -> dict:
    c = dict(spec_cond)
    c.update({"unit_ref": unit_ref, "condition_ref": condition_ref, "render": render})
    if regime:
        c["regime"] = regime
    if c.get("regime") == "maker_familiar" and not c.get("demos"):
        c["demos"] = 2
    return c


def run_unit(run: CardRun7, server: ModelServer, w: dict, ev: dict, bundle: dict, arm: str, reader: str | None,
             task_extra: dict | None = None, factors: dict | None = None, unit_id: str | None = None,
             targets: list | None = None) -> dict | None:
    """One (world, arm, reader): capsule, prediction, score, row. Returns the score dict."""
    uid = unit_id or w["lid"]
    if run.is_done(reader, uid, arm):
        return None
    run.check_deadline()
    task = {"arm": arm, "model": reader or "", "seed": SEED + W._widx(uid) if "|" in uid else SEED,
            "withheld": [f for f in C.ALL7 if f != "external_context" and f not in (ev.get("supplied_factors") or {}).get("factors", {})]}
    if targets:
        task["targets"] = list(targets)
    task.update(task_extra or {})
    cap = RT.materialize(run.cell_id, f"{uid.replace('|', '-')}__{arm}__{(reader or 'x').split('/')[-1].replace(':', '-')}", ev, task, dom_params())
    res = RT.run_capsule(cap, server.endpoint, server.token, reader or "", timeout_s=1800 if arm in MODEL_ARMS else 300)
    pred = res.get("prediction")
    valid, why = True, "ok"
    sc: dict = {}
    if pred is None:
        valid, why = False, f"no prediction: {(res.get('error') or {}).get('error', res.get('stderr_tail', ''))[:200]}"
    else:
        probs = validate_prediction(pred)
        if probs:
            valid, why = False, f"invalid prediction: {probs[:3]}"
        else:
            sc = PS.score(pred, bundle)
    pref = run.save_prediction(uid, arm, reader, pred) if pred else None
    ORC.save(run.cell_id, f"{uid.replace('|', '-')}", bundle, ev)
    run.row(uid, reader=reader, arm=arm, factors=dict(factors or {}, prefix_len=len(ev.get("process_prefix", []))),
            truth=bundle["hidden"].get("next_action") if "hidden" in bundle else None,
            truth_ref=str(ORC.bundle_path(run.cell_id, uid.replace("|", "-"))),
            scores=sc, primary_score=sc.get("primary") if sc else None, valid=valid, validity_reason=why,
            budget=(pred or {}).get("compute"), evidence_sha=evidence_sha(ev), pred_ref=pref,
            extra={"abstain": (pred or {}).get("abstain"), "equivalence_class": (pred or {}).get("equivalence_class"),
                   "notes": {k: v for k, v in ((pred or {}).get("notes") or {}).items() if k in ("proposals", "posterior", "factor_marginals", "unrealized", "receipt", "subjective_ids", "mixture", "candidate_preds", "proposed", "unparsed")},
                   "canonical_sha": prediction_sha(pred) if pred else None, "access": (res.get("access") or {}).get("counts")})
    run.unit_complete(reader, uid, arm)
    RT.cleanup_unit(cap) if hasattr(RT, "cleanup_unit") else None
    return sc


def worlds_for(run: CardRun7, card: str, n: int, family: str | None = None, offset: int = 0, **forced) -> list[dict]:
    """Constructed worlds for a card: deterministic lineages, degenerate ones counted and
    skipped (the kept fraction is reported beside every effect)."""
    out = []
    degenerate = 0
    tried = 0
    for dom in C.DOMAINS:
        kept = 0
        # the walk leaves some lineages without a cut; the band is over-generated (never past
        # the next offset band) and the first n live worlds are kept, deterministically
        for lid in lineage_ids(card, dom, int(n * 1.6) + 2, split=run.split, offset=offset, family=family):
            if kept >= n:
                break
            tried += 1
            w = W.make_world(lid, dom, **forced)
            if w["degenerate"]:
                degenerate += 1
                continue
            run.register_world(lid, {"lid": lid, "names": w["state"]["names"], "cut": w["cut"], "n_steps": len(w["trajectory"]["steps"])})
            out.append(w)
            kept += 1
    run._degenerate = degenerate
    run._kept_fraction = round(len(out) / tried, 4) if tried else None
    return out


def unit_contrast(run: CardRun7, rows: list[dict], arm_a: str, arm_b: str, key: str = "primary_score",
                  reader: str | None = None, seed: int = SEED) -> dict:
    """Paired contrast at the world between two arms (optionally one reader)."""
    ra = [r for r in rows if r["arm"] == arm_a and r.get("valid") and r.get(key) is not None and (reader is None or r["model_id"] == reader)]
    rb = [r for r in rows if r["arm"] == arm_b and r.get("valid") and r.get(key) is not None and (reader is None or r["model_id"] in (reader, "-"))]
    return s5_lib.paired_contrast(ra, rb, "unit_id", key, seed)


def rows_valid(rows: list[dict], arm: str | None = None, reader: str | None = None) -> list[dict]:
    return [r for r in rows if r.get("valid") and r.get("primary_score") is not None
            and (arm is None or r["arm"] == arm) and (reader is None or r["model_id"] == reader)]


def mean_score(rows: list[dict], key: str = "primary_score") -> float | None:
    vals = [float(r[key]) for r in rows if r.get(key) is not None]
    return sum(vals) / len(vals) if vals else None


def oracle_rows(run: CardRun7, worlds: list[dict], conds: dict) -> None:
    """The exact oracle's scores per world (the OR rows), from the bundles alone."""
    for w in worlds:
        uid = w["lid"]
        if run.is_done("-", uid, "OR"):
            continue
        bundle = W.oracle_bundle(w, conds)
        sc = PS.oracle_scores(bundle)
        run.row(uid, arm="OR", factors={"domain": w["domain"]}, truth=w["hidden"]["next_action"], scores=sc,
                primary_score=sc.get("primary"))
        run.unit_complete("-", uid, "OR")


# ── I: isolation, integrity, execution gates ─────────────────────────────────────────

def record_ledger(run: CardRun7, server: "ModelServer") -> None:
    """The server's per-token ledger for this cell (read at the server's close), the I13
    receipt; every engine that opens a ModelServer writes one."""
    update_registry("COMPUTE_LEDGER", lambda led: {**led, run.cell_id.replace("/", "_"): {"ledger": server.ledger, "gpu_held_s": server.held_s, "at": now_iso()}})


def _finish_infra(run: CardRun7, metrics: dict, ok: bool | None, reason: str, gpu: float = 0.0, gate: str | None = None) -> int:
    oc = "VOID" if ok is None else ("INFRASTRUCTURE" if ok else "INSTRUMENT_FAILED")
    if gate:
        set_gate(gate, bool(ok), {"card": run.card, "reason": reason})
    run.finish(metrics, {"exec": "COMPLETE", "outcome": oc, "primary": C.ALL[run.card]["primary"], "reason": reason}, gpu,
               rival=C.ALL[run.card]["discriminator"])
    return 0


def run_I01(run: CardRun7) -> int:
    contract = RunContract7.load()
    head = subprocess.run(["git", "-C", str(REPO), "rev-parse", "--short", "HEAD"], capture_output=True, text=True, timeout=20).stdout.strip()
    reviewed = contract.data.get("reviewed_commit")
    in_history = subprocess.run(["git", "-C", str(REPO), "merge-base", "--is-ancestor", reviewed, "HEAD"], capture_output=True, timeout=20).returncode == 0
    s6 = REPO / "results" / "phase_2_4_stage_6"
    rt = read_json(s6 / "RUNTIME.json") if (s6 / "RUNTIME.json").exists() else {}
    cov = read_json(s6 / "COVERAGE.json") if (s6 / "COVERAGE.json").exists() else {}
    from soundingline.stage7 import sha256_file                                   # noqa: PLC0415
    hashes = {}
    for c in ("M02", "M08", "I05", "T02", "M14", "M15", "M09"):
        p = s6 / c / "verdict.json"
        if p.exists():
            hashes[c] = sha256_file(p)[:16]
    anchors = {"elapsed_h": rt.get("elapsed_h"), "cells": (rt.get("cells") or {}), "complete": cov.get("complete")}
    ok = in_history and bool(hashes) and anchors["elapsed_h"] is not None and abs(float(anchors["elapsed_h"]) - 47.07) < 0.5
    update_registry("PREPARED", lambda _r: {**_r, "I01": {"head": head, "reviewed": reviewed, "in_history": in_history,
                                                                            "stage6_anchors": anchors, "stage6_verdict_hashes": hashes, "at": now_iso()}})
    ghost = ghost_receipt()
    return _finish_infra(run, {"head": head, "reviewed": reviewed, "in_history": in_history, "stage6": anchors, "hashes": hashes, "ghost": ghost},
                         ok, f"head {head}; reviewed {reviewed} in history {in_history}; Stage 6 elapsed {anchors['elapsed_h']} h; ghost head {ghost.get('head')}")


def run_I02(run: CardRun7) -> int:
    from runners.stage7 import manifest as M                                      # noqa: PLC0415
    exp = read_registry("EXPECTED_CELLS") or {}
    cells = exp.get("cells") or M.expected_cells()
    dup = C.duplicate_identities()
    removal = M.removal_fails(cells)
    counts = {}
    for e in cells:
        counts[e["question"][0]] = counts.get(e["question"][0], 0) + 1
    ok = bool(cells) and not dup and removal and len(set(e["question"] for e in cells)) == 124
    return _finish_infra(run, {"n_cells": len(cells), "by_trunk": counts, "duplicate_identities": dup, "removal_fails": removal},
                         ok, f"{len(cells)} expected cells over 124 questions and attacks; duplicates {dup}; removal fails coverage {removal}")


def run_I03(run: CardRun7) -> int:
    """Allowlist validation across every rung's condition, plus planted undeclared fields
    and nested callables that must be rejected."""
    n = n_units("I03")
    rejected = accepted = planted_caught = 0
    problems_seen = []
    for i in range(n):
        w = W.make_world(f"WX|essay|s0|w{50000 + i:05d}|conformance", "essay")
        if w["degenerate"]:
            continue
        for q in ("K04", "K05", "K06", "K11", "K13", "K14", "R13"):
            cond = build_condition(C.ALL[q]["condition"], "u", q)
            ev = W.visible_evidence(w, cond)
            probs = validate_visible_evidence(ev)
            if probs:
                rejected += 1
                problems_seen.append((q, probs[:2]))
            else:
                accepted += 1
        bad = W.visible_evidence(w, build_condition(C.ALL["K04"]["condition"], "u", "K04"))
        bad["hidden_tail"] = ["x"]
        bad2 = copy.deepcopy(W.visible_evidence(w, build_condition(C.ALL["K04"]["condition"], "u", "K04")))
        bad2["query"]["stop_shift"] = 1.0
        bad3 = copy.deepcopy(W.visible_evidence(w, build_condition(C.ALL["K04"]["condition"], "u", "K04")))
        bad3["brief"]["callback"] = (lambda: 0)
        planted_caught += sum(1 for b in (bad, bad2, bad3) if validate_visible_evidence(b))
    ok = rejected == 0 and planted_caught == 3 * (accepted // 7 if accepted else 0) and accepted > 0
    return _finish_infra(run, {"accepted": accepted, "rejected": rejected, "planted_caught": planted_caught, "problems": problems_seen[:5]},
                         ok, f"{accepted} rung evidences accepted, {rejected} rejected; planted fields caught {planted_caught}")


def run_I04(run: CardRun7) -> int:
    with ModelServer("s7_i04", []) as server:
        forbidden = [str(REPO / "soundingline" / "stage7.py"), str(S7 / "oracle"), str(REPO), str(S7 / "RUN_CONTRACT.json"),
                     str(REPO / "runners" / "stage7" / "constructor" / "worlds.py")]
        rec = RT.probe(run.cell_id, server.endpoint, server.token, forbidden, other_port=RT.free_port())
    write_registry("ACCESS_RECEIPT", rec)
    write_registry("INFORMATION_BOUNDARY", {"written_at": now_iso(), "mechanism": rec["mechanism"],
                                            "honest_label": "interpreter-level boundary (his ruling 2026-09-02); the operating system does not deny the files, the interpreter does",
                                            "all_raised": rec["all_raised"], "attempts": rec["attempts"], "env_keys": rec["env_keys"], "sys_path": rec["sys_path"]})
    not_raised = [k for k, v in (rec["attempts"] or {}).items() if not v["raised"]]
    return _finish_infra(run, {"receipt": rec}, bool(rec["all_raised"]) and rec["rc"] == 0,
                         f"{len(rec['attempts'] or {})} forbidden attempts; not raised: {not_raised}", gate="isolation")


def _mutation_card(run: CardRun7, kind: str) -> int:
    """I05/I06/I07: every non-oracle arm on a world and its mutant; canonical bytes must be
    identical; the oracle's numbers must DIFFER on at least some pairs (should-break)."""
    n = n_units(run.card)
    spec = C.ALL[run.card]
    cond = build_condition(spec["condition"], "u", run.card)
    readers = run.readers
    arms = spec["arms"]
    pairs_identical = {a: 0 for a in arms}
    pairs_total = {a: 0 for a in arms}
    oracle_differs = 0
    n_pairs = 0
    with ModelServer(f"s7_{run.card.lower()}", readers) as server:
        for w in worlds_for(run, run.card, n, family="worlds_attack"):
            run.check_deadline()
            m = W.mutate(w, kind, 1)
            ev, evm = W.visible_evidence(w, cond), W.visible_evidence(m, cond)
            if evidence_sha(ev) != evidence_sha(evm):
                run.row(w["lid"], arm="construction", valid=False, validity_reason="mutation changed visible evidence")
                run.unit_complete("-", w["lid"], "construction")
                continue
            b, bm = W.oracle_bundle(w, cond), W.oracle_bundle(m, cond)
            n_pairs += 1
            if tv(b["oracle"]["next_action"], bm["oracle"]["next_action"]) > 1e-9 or abs(b["oracle"]["p_stop"] - bm["oracle"]["p_stop"]) > 1e-9 \
                    or b["hidden"]["next_action"] != bm["hidden"]["next_action"] or b["hidden"]["stop_next"] != bm["hidden"]["stop_next"] \
                    or b["hidden"]["tail"] != bm["hidden"]["tail"]:
                oracle_differs += 1
            for arm in arms:
                for reader in (readers if arm in MODEL_ARMS else [None]):
                    uid_a, uid_b = w["lid"], m["lid"]
                    if run.is_done(reader, uid_b, arm):
                        continue
                    run_unit(run, server, w, ev, b, arm, reader, factors={"domain": w["domain"], "pair": "original"}, unit_id=uid_a)
                    run_unit(run, server, m, evm, bm, arm, reader, factors={"domain": w["domain"], "pair": "mutant"}, unit_id=uid_b)
    record_ledger(run, server)
    rows = run.rows()
    by = {}
    for r in rows:
        if r.get("arm") in arms and r.get("valid"):
            by[(r["arm"], r["model_id"], r["unit_id"])] = (r.get("extra") or {}).get("canonical_sha")
    for (arm, reader, uid), sha in by.items():
        if "|mut-" in uid:
            continue
        other = by.get((arm, reader, f"{uid}|mut-{kind}-1"))
        if other is None:
            continue
        pairs_total[arm] += 1
        pairs_identical[arm] += int(other == sha)
    rates = {a: (pairs_identical[a] / pairs_total[a]) if pairs_total[a] else None for a in arms}
    ok = all(v == 1.0 for v in rates.values() if v is not None) and any(v is not None for v in rates.values()) and oracle_differs > 0
    leaking = [a for a, v in rates.items() if v is not None and v < 1.0]
    return _finish_infra(run, {"identity_rate_by_arm": rates, "pairs_total": pairs_total, "oracle_differs": oracle_differs, "n_pairs": n_pairs,
                               "degenerate": getattr(run, "_degenerate", 0)},
                         ok, f"identity rates {rates}; oracle differs on {oracle_differs}/{n_pairs}; leaking arms {leaking}",
                         gate=f"mutation_{kind}")


def run_I08(run: CardRun7) -> int:
    """The visible-sensitivity control: flip the visible outcome of a tool-requiring prefix
    step to 'failed' (a belief-diagnostic observation); every reader that claims the
    channel must move; DOM is exempt and reported."""
    n = n_units("I08")
    cond = build_condition(C.ALL["I08"]["condition"], "u", "I08")
    arms = C.ALL["I08"]["arms"]
    moved = {a: [] for a in arms}
    with ModelServer("s7_i08", run.readers) as server:
        for w in worlds_for(run, "I08", n, family="worlds_attack"):
            run.check_deadline()
            ev = W.visible_evidence(w, cond)
            ev2 = copy.deepcopy(ev)
            flipped = False
            for e in ev2["process_prefix"]:
                if e["type"] in ("cite", "consult") and e["outcome"] == "done":
                    e["outcome"] = "failed"
                    flipped = True
                    break
            if not flipped:
                ev2["process_prefix"][-1]["outcome"] = "failed"
            ev2["artifact_state"]["prefix_text"] = W.render_prefix_text(ev2["process_prefix"], cond.get("render", "prose"), w["doc"]["topic"])
            b = W.oracle_bundle(w, cond)
            for arm in arms:
                for reader in (run.readers if arm in MODEL_ARMS else [None]):
                    if run.is_done(reader, f"{w['lid']}|flip", arm):
                        continue
                    run_unit(run, server, w, ev, b, arm, reader, factors={"domain": w["domain"], "variant": "base"}, unit_id=w["lid"])
                    run_unit(run, server, w, ev2, b, arm, reader, factors={"domain": w["domain"], "variant": "flip"}, unit_id=f"{w['lid']}|flip")
    record_ledger(run, server)
    rows = run.rows()
    preds = {}
    shas = {}
    for r in rows:
        if r.get("valid") and r.get("pred_ref"):
            preds[(r["arm"], r["model_id"], r["unit_id"])] = read_json(Path(r["pred_ref"]))["targets"]["next_action"]
            shas[(r["arm"], r["model_id"], r["unit_id"])] = (r.get("extra") or {}).get("canonical_sha")
    changed = {a: [] for a in arms}
    for (arm, reader, uid), d in preds.items():
        if uid.endswith("|flip"):
            continue
        d2 = preds.get((arm, reader, f"{uid}|flip"))
        if d2 is not None:
            moved[arm].append(tv(d, d2))
            changed[arm].append(int(shas.get((arm, reader, uid)) != shas.get((arm, reader, f"{uid}|flip"))))
    mean_tv = {a: (sum(v) / len(v)) if v else None for a, v in moved.items()}
    changed_rate = {a: (sum(v) / len(v)) if v else None for a, v in changed.items()}
    # the gate proves the PIPELINE carries the flip: the solver's exact distribution moves
    # (the flip is belief-diagnostic under the law) and every model arm's canonical bytes
    # change on nearly every pair (the flipped text reached the model); a model reader's
    # SIZE of response is reported, never gated (a blind reader is a finding, not a broken
    # instrument, and an instrument gate must not depend on a reader's competence)
    sol_ok = mean_tv.get("SOL") is not None and mean_tv["SOL"] >= 0.02
    model_ok = all((changed_rate.get(a) or 0.0) >= 0.9 for a in arms if a in MODEL_ARMS and changed_rate.get(a) is not None) \
        and any(a in MODEL_ARMS and changed_rate.get(a) is not None for a in arms)
    ok = sol_ok and model_ok
    return _finish_infra(run, {"mean_tv_by_arm": mean_tv, "bytes_changed_rate_by_arm": changed_rate,
                               "band": "SOL TV at or above 0.02; model arms' canonical bytes change on at least 90 percent of pairs; DOM exempt; model TV reported"},
                         ok, f"sensitivity TV {mean_tv}; bytes changed {changed_rate}", gate="sensitivity")


def run_I09(run: CardRun7) -> int:
    """Serialization invariance: the same evidence with shuffled key order, extra
    whitespace in the JSON file, and relabeled opaque ids must give identical canonical
    predictions; a semantic change (a different prefix step) must still move them."""
    n = n_units("I09")
    cond = build_condition(C.ALL["I09"]["condition"], "u", "I09")
    arms = C.ALL["I09"]["arms"]
    ident = {a: [0, 0] for a in arms}
    semantic_moved = 0
    sem_total = 0
    with ModelServer("s7_i09", run.readers) as server:
        for w in worlds_for(run, "I09", n, family="worlds_attack"):
            run.check_deadline()
            ev = W.visible_evidence(w, cond)
            ev_r = json.loads(json.dumps({k: ev[k] for k in sorted(ev, reverse=True)}))
            ev_r["unit_ref"] = "opaque-" + secrets.token_hex(3)
            ev_r["condition_ref"] = "cond-" + secrets.token_hex(2)
            b = W.oracle_bundle(w, cond)
            for arm in arms:
                for reader in (run.readers if arm in MODEL_ARMS else [None]):
                    if run.is_done(reader, f"{w['lid']}|relabel", arm):
                        continue
                    run_unit(run, server, w, ev, b, arm, reader, factors={"domain": w["domain"], "variant": "base"}, unit_id=w["lid"])
                    run_unit(run, server, w, ev_r, b, arm, reader, factors={"domain": w["domain"], "variant": "relabel"}, unit_id=f"{w['lid']}|relabel")
    record_ledger(run, server)
    rows = run.rows()
    preds = {}
    for r in rows:
        if r.get("valid") and r.get("pred_ref"):
            p = read_json(Path(r["pred_ref"]))
            preds[(r["arm"], r["model_id"], r["unit_id"])] = p["targets"]
    for (arm, reader, uid), t in preds.items():
        if uid.endswith("|relabel"):
            continue
        t2 = preds.get((arm, reader, f"{uid}|relabel"))
        if t2 is None:
            continue
        ident[arm][1] += 1
        ident[arm][0] += int(json.dumps(t, sort_keys=True) == json.dumps(t2, sort_keys=True) or tv(t["next_action"], t2["next_action"]) < 1e-6)
    rates = {a: (v[0] / v[1]) if v[1] else None for a, v in ident.items()}
    ok = all(v == 1.0 for v in rates.values() if v is not None) and any(v is not None for v in rates.values())
    return _finish_infra(run, {"identity_rate_by_arm": rates, "note": "unit_ref and condition_ref enter no prompt; the model reader sees the same bytes"},
                         ok, f"serialization identity {rates}")


def run_I10(run: CardRun7) -> int:
    """Canaries: plant target words into identifiers, key names, ordering, lengths, and
    seeds of otherwise clean evidence; the allowlist validator and the identifier detector
    must catch each; a clean-null detector (a classifier from evidence identifiers to the
    hidden truth) must sit at chance."""
    n = 24 if not SMOKE else 4
    caught = 0
    planted = 0
    clean_hits = 0
    clean_total = 0
    for i in range(n):
        w = W.make_world(f"WX|essay|s0|w{51000 + i:05d}|conformance", "essay")
        if w["degenerate"] or w["hidden"]["next_action"] is None:
            continue                                    # a terminal cut carries no next action to plant
        cond = build_condition(C.ALL["K04"]["condition"], "u", "K04")
        ev = W.visible_evidence(w, cond)
        truth = w["hidden"]["next_action"]
        # planted canaries
        c1 = copy.deepcopy(ev)
        c1["unit_ref"] = f"u-{truth}"
        c2 = copy.deepcopy(ev)
        c2["query"]["answer_hint"] = truth
        c3 = copy.deepcopy(ev)
        opts = list(c3["query"]["next_action_options"])
        rest = [o for o in opts if o != truth]
        # the order canary must CHANGE the order: the truth to the front, or to the end when it
        # already leads; a one-option query carries no order to plant
        c3["query"]["next_action_options"] = ([truth] + rest) if opts and opts[0] != truth else (rest + [truth])
        c4 = copy.deepcopy(ev)
        c4["render"] = "prose" + str(len(truth))
        for cz in ((c1, c2, c3, c4) if len(opts) > 1 else (c1, c2, c4)):
            planted += 1
            probs = validate_visible_evidence(cz)
            leak = _identifier_leak(cz, truth)
            if probs or leak:
                caught += 1
        clean_total += 1
        clean_hits += int(_identifier_leak(ev, truth))
    ok = planted > 0 and caught == planted and clean_hits == 0
    return _finish_infra(run, {"planted": planted, "caught": caught, "clean_hits": clean_hits, "clean_total": clean_total},
                         ok, f"canaries caught {caught}/{planted}; clean identifier hits {clean_hits}/{clean_total}", gate="canaries")


def _identifier_leak(ev: dict, truth: str) -> bool:
    """The identifier detector: does any opaque field, key name, option ORDER, or render
    tag encode the truth string or its length? The order check: the query's option list
    must be the declared at-cut option list in the same order (the first attempt's check
    ended in a tautology and never fired; I10 caught 60 of 80 on 2026-09-02)."""
    ids = [str(ev.get("unit_ref", "")), str(ev.get("condition_ref", "")), str(ev.get("render", ""))]
    if any(truth in x or (x.startswith("prose") and x[5:].isdigit()) for x in ids):
        return True
    q = ev.get("query") or {}
    if any(k not in ("next_action_options", "type_vocabulary", "sections", "stop", "context_change", "invalidation_responses", "boundary_types") for k in q):
        return True
    opts = list(q.get("next_action_options") or [])
    oo = ev.get("objective_options") or {}
    declared = [f"{a['type']}:{a['section']}:{a['slot']}" for a in (oo.get("at_cut", []) if isinstance(oo, dict) else oo)]
    if declared and set(declared) == set(opts) and declared != opts:
        return True
    return False


def run_I11(run: CardRun7) -> int:
    """The contract builder normalizes what it is given, so the NEGATIVE fixtures are raw
    objects that bypass it (a malformed distribution must fail validation); the positive
    fixtures go through the builder (the first attempt sent a negative fixture through the
    builder, which repaired it, and landed 3 of 4 on 2026-09-02)."""
    from runners.stage7.contracts import prediction as mkpred                     # noqa: PLC0415
    raw = lambda t, **kw: {"version": "PredictionV1", "evidence_sha": "x", "targets": t, "equivalence_class": [], "abstain": False, "confidence": 0.5, **kw}  # noqa: E731
    fx = [(mkpred({"version": "VisibleEvidenceV1"}, {"next_action": {"a": 0.2, "b": 0.8}}, confidence=0.7), True),
          (mkpred({"version": "VisibleEvidenceV1"}, {"next_action": {"a": 1.0, "b": 0.0}, "stop": 1.7}, confidence=0.7), True),
          (raw({"next_action": {"a": -0.1, "b": 1.1}}), False),
          (raw({"next_action": {"a": 0.5, "b": 0.6}}), False),
          (raw({}), False),
          (raw({"stop": 1.3}), False),
          (raw({"next_action": {"a": 1.0}}, confidence=1.5), False)]
    passes = 0
    for p, should in fx:
        ok = not validate_prediction(p)
        passes += int(ok == should)
    parity = validate_prediction({"version": "PredictionV1", "evidence_sha": "x", "targets": {"stop": 0.3}, "equivalence_class": ["c"], "abstain": True, "confidence": 0.9}) == []
    ok = passes == len(fx) and parity
    return _finish_infra(run, {"fixtures": len(fx), "passes": passes, "hazard_parity": parity}, ok, f"{passes}/{len(fx)} fixtures; hazard form {parity}")


def run_I12(run: CardRun7) -> int:
    """Paired arms saw identical evidence bytes within each unit and condition (from the
    landed rows of the mutation cards), and the supplied-field difference between
    conditions is exactly the declared one."""
    eq = tot = 0
    for card in ("I05", "I06", "I07"):
        rows = [r for r in (read_jsonl(S7 / card / "cases.jsonl") if (S7 / card / "cases.jsonl").exists() else []) if r.get("valid")]
        by: dict = {}
        for r in rows:
            by.setdefault(r["unit_id"], set()).add(r.get("evidence_sha"))
        for u, shas in by.items():
            tot += 1
            eq += int(len(shas) == 1)
    diff_ok = True
    w = next((x for x in (W.make_world(f"WX|essay|s0|w{52000 + i:05d}|conformance", "essay") for i in range(20)) if not x["degenerate"]), None)
    if w:
        a = W.visible_evidence(w, build_condition(C.ALL["K04"]["condition"], "u", "K04"))
        b = W.visible_evidence(w, build_condition(C.ALL["K11"]["condition"], "u", "K11"))
        da = set((a.get("supplied_factors") or {}).get("factors", {}))
        db = set((b.get("supplied_factors") or {}).get("factors", {}))
        diff_ok = (da - db) == {"proximal_goal"} and all(a[k] == b[k] for k in ("artifact_state", "process_prefix", "brief", "objective_options"))
    ok = tot > 0 and eq == tot and diff_ok
    return _finish_infra(run, {"units": tot, "equal_evidence": eq, "declared_difference_ok": diff_ok}, ok, f"{eq}/{tot} units with one evidence hash across arms; declared difference {diff_ok}")


def run_I13(run: CardRun7) -> int:
    """The capsule-side budgets summed per cell reconcile to the server ledger written at
    the cell's close (COMPUTE_LEDGER), within the retries the client recorded."""
    led = read_registry("COMPUTE_LEDGER") or {}
    checks = []
    for cell, rec in led.items():
        if not isinstance(rec, dict) or "ledger" not in rec:
            continue                                    # A15_priced and other summaries
        d1, d2 = S7 / cell.replace("_", "/", 1), S7 / cell
        rows = read_jsonl(d1 / "cases.jsonl") if (d1 / "cases.jsonl").exists() else (read_jsonl(d2 / "cases.jsonl") if (d2 / "cases.jsonl").exists() else [])
        if not rows:
            continue
        caps = sum(int((r.get("budget") or {}).get("model_calls", 0) or 0) for r in rows)
        srv = sum(int(v.get("model_calls", 0)) for v in (rec.get("ledger") or {}).values())
        retries = sum(int((r.get("budget") or {}).get("retries", 0) or 0) for r in rows)
        checks.append({"cell": cell, "capsule_calls": caps, "server_calls": srv, "retries": retries,
                       "match": caps == srv or (srv >= caps and srv - caps <= retries)})
    ok = bool(checks) and all(c["match"] for c in checks)
    return _finish_infra(run, {"checks": checks[:40], "n": len(checks)}, ok if checks else None, f"{sum(1 for c in checks if c['match'])}/{len(checks)} cells reconcile")


def run_I14(run: CardRun7) -> int:
    from runners.stage7 import manifest as M                                      # noqa: PLC0415
    rec = M.split_receipt()
    return _finish_infra(run, rec, rec["clean"], f"{rec['n_lineages']} lineages, {rec['n_roots']} roots, {len(rec['violations'])} violations", gate="splits")


def run_I15(run: CardRun7) -> int:
    """Kill/resume in a scratch root: a small SOL-only cell interrupted after its first
    unit resumes without duplicating it; row duplication and reordering leave the
    unit-level mean unchanged; the deadline survives a restart."""
    import shutil                                                                 # noqa: PLC0415
    import tempfile                                                               # noqa: PLC0415
    scratch = Path(tempfile.mkdtemp(prefix="s7_i15_"))
    env = dict(os.environ, S7_ROOT=str(scratch), S7_SMOKE="1", S7_SPLIT="pilot")
    code = ("import sys; sys.path.insert(0, %r); from runners.stage7 import scheduler as S; S.prepare(); "
            "from soundingline.stage7 import RunContract7; c=RunContract7.load(); c.start(); "
            "from runners.stage7 import scheduler as S2; S2._workload_lock(c, {'unit_s': 1.0}); "
            "from runners.stage7 import engine_supplied as ES; from runners.stage7.cardrun import CardRun7; "
            "ES.run_K01(CardRun7('K01'))") % str(REPO)
    p1 = subprocess.Popen([PY, "-c", code], cwd=str(REPO), env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(8)
    p1.kill()
    p1.wait()
    cases = scratch / "K01" / "pilot" / "cases.jsonl"          # the pilot lane's cell directory
    rows1 = read_jsonl(cases) if cases.exists() else []
    deadline1 = (read_json(scratch / "RUN_CONTRACT.json") or {}).get("deadline")
    p2 = subprocess.run([PY, "-c", code], cwd=str(REPO), env=env, capture_output=True, text=True, timeout=900)
    rows2 = read_jsonl(cases) if cases.exists() else []
    deadline2 = (read_json(scratch / "RUN_CONTRACT.json") or {}).get("deadline")
    keys = [(r["model_id"], r["unit_id"], r["arm"]) for r in rows2]
    dup = len(keys) - len(set(keys))
    # reorder/duplication invariance on the unit mean
    valid = [r for r in rows2 if r.get("valid") and r.get("primary_score") is not None and r["arm"] == "DOM"]
    m1 = s5_lib.per_unit_means(valid, "unit_id", "primary_score")
    m2 = s5_lib.per_unit_means(list(reversed(valid)) + valid[:3], "unit_id", "primary_score")
    same = all(abs(m1[u] - m2[u]) < 1e-12 for u in m1) if m1 else False
    ok = dup == 0 and deadline1 == deadline2 and deadline1 is not None and p2.returncode == 0 and len(rows2) >= max(1, len(rows1)) and same
    shutil.rmtree(scratch, ignore_errors=True)
    return _finish_infra(run, {"rows_after_kill": len(rows1), "rows_after_resume": len(rows2), "duplicates": dup, "deadline_kept": deadline1 == deadline2,
                               "rc": p2.returncode, "reorder_invariant": same, "stderr": p2.stderr[-400:]},
                         ok, f"{len(rows1)} rows before the kill, {len(rows2)} after resume, {dup} duplicates; deadline kept {deadline1 == deadline2}; reorder invariant {same}")


def run_I16(run: CardRun7) -> int:
    """The keystone: one world traced end to end and written for the manual audit. The
    verdict here is the trace's completeness; the SIGNED lock (KEYSTONE_LOCK) is written by
    the curator loop after reading KEYSTONE_AUDIT.md, and the scientific lock waits on it."""
    cond = build_condition(C.ALL["I16"]["condition"], "keystone", "I16")
    w = next(x for x in (W.make_world(f"WX|essay|s0|w{53000 + i:05d}|conformance", "essay") for i in range(40))
             if not x["degenerate"] and x["hidden"]["next_action"] is not None)
    ev = W.visible_evidence(w, cond)
    b = W.oracle_bundle(w, cond)
    trace = {"lid": w["lid"], "evidence_sha": evidence_sha(ev), "evidence_keys": sorted(ev), "prefix_len": len(ev["process_prefix"]),
             "supplied": sorted(ev["supplied_factors"]["factors"]), "hidden_keys_in_bundle": sorted(b["hidden"])}
    with ModelServer("s7_i16", [run.readers[0]]) as server:
        for arm in ("SOL", "DIR"):
            reader = run.readers[0] if arm in MODEL_ARMS else None
            task = {"arm": arm, "model": reader or "", "seed": SEED, "withheld": []}
            cap = RT.materialize(run.cell_id, f"keystone__{arm}", ev, task, dom_params())
            listing = sorted(str(p.relative_to(cap)) for p in cap.rglob("*") if p.is_file())
            res = RT.run_capsule(cap, server.endpoint, server.token, reader or "", timeout_s=900)
            pred = res.get("prediction")
            sc = PS.score(pred, b) if pred else None
            trace[arm] = {"capsule_files": listing, "access_counts": (res.get("access") or {}).get("counts"), "rc": res["rc"],
                          "prediction_sha": prediction_sha(pred) if pred else None,
                          "next_action_top": sorted(pred["targets"]["next_action"].items(), key=lambda kv: -kv[1])[:3] if pred else None,
                          "compute": (pred or {}).get("compute"), "score": sc}
            # the keystone's rows, like every substantive cell's (the fresh-clone verifier reads them)
            pref = run.save_prediction(w["lid"], arm, reader, pred) if pred else None
            ORC.save(run.cell_id, w["lid"].replace("|", "-"), b, ev)
            run.row(w["lid"], reader=reader, arm=arm, factors={"domain": w["domain"], "keystone": True, "prefix_len": len(ev["process_prefix"])},
                    truth=b["hidden"].get("next_action"), truth_ref=str(ORC.bundle_path(run.cell_id, w["lid"].replace("|", "-"))),
                    scores=sc or {}, primary_score=(sc or {}).get("primary"), valid=bool(pred), validity_reason="ok" if pred else "no prediction",
                    budget=(pred or {}).get("compute"), evidence_sha=evidence_sha(ev), pred_ref=pref,
                    extra={"canonical_sha": prediction_sha(pred) if pred else None, "access": (res.get("access") or {}).get("counts")})
            run.unit_complete(reader, w["lid"], arm)
        trace["server_ledger"] = server.stats().get("ledger")
    record_ledger(run, server)
    trace["truth"] = {"next_action": b["hidden"]["next_action"], "stop_next": b["hidden"]["stop_next"], "class_size": len(b["hidden"]["equivalence_class"])}
    trace["oracle_score"] = PS.oracle_scores(b)
    lines = ["# Keystone audit (I16): one world, constructor to score", "",
             f"Written {now_iso()}. World `{w['lid']}`; evidence sha `{trace['evidence_sha']}`; prefix {trace['prefix_len']} steps; supplied {trace['supplied']}.", "",
             "## Checklist (each item is read against the trace below, then signed in KEYSTONE_LOCK.json)", "",
             "1. Inputs: the capsule holds only reader/*.py, contracts, evidence.json, task.json, dom.json, bootstrap.py, out/, tmp/.",
             "2. Process access: the access counts show zero denials and no read outside the capsule and the standard library.",
             "3. Model calls: the DIR arm's compute receipt equals the server ledger for the run.",
             "4. Output: one PredictionV1 per arm, normalized, with the evidence sha it answered.",
             "5. Truth lookup: the oracle bundle lives under oracle/, never in the capsule listing.",
             "6. Score: the SOL arm's next-action distribution reproduces the oracle's and its score equals the oracle score.", "",
             "## Trace", "", "```json", json.dumps(trace, indent=1, default=str)[:12000], "```", ""]
    (S7 / "KEYSTONE_AUDIT.md").write_text("\n".join(lines), encoding="utf-8", newline="\n")
    sol_ok = trace["SOL"]["score"] is not None and abs(trace["SOL"]["score"]["next_action_ls"] - trace["oracle_score"]["next_action_ls"]) < 1e-6
    no_oracle_in_capsule = all("oracle" not in f.lower() for f in trace["SOL"]["capsule_files"] + trace["DIR"]["capsule_files"])
    denials = sum(int((trace[a]["access_counts"] or {}).get("denied", 0)) for a in ("SOL", "DIR"))
    ok = sol_ok and no_oracle_in_capsule and denials == 0 and trace["DIR"]["rc"] == 0
    return _finish_infra(run, {"trace": trace, "sol_reproduces_oracle": sol_ok, "denials": denials, "audit_path": str(S7 / "KEYSTONE_AUDIT.md")},
                         ok, f"keystone trace written; SOL reproduces oracle {sol_ok}; denials {denials}; awaiting the signed lock")


# ── D: the dependency trunk ──────────────────────────────────────────────────────────

def _audit() -> dict:
    a = read_registry("STAGE6_DEPENDENCY_AUDIT")
    if a and a.get("D02_decomposition"):
        return a
    from runners.stage7 import dependency_audit as DA                             # noqa: PLC0415
    return DA.write_audit(light=SMOKE)


def _finish_desc(run: CardRun7, metrics: dict, reason: str, outcome: str = "DESCRIPTIVE") -> int:
    run.finish(metrics, {"exec": "COMPLETE", "outcome": outcome, "primary": C.ALL[run.card]["primary"], "reason": reason},
               rival=C.ALL[run.card]["discriminator"])
    return 0


def run_D(run: CardRun7) -> int:
    card = run.card
    if card == "D01":
        a = _audit()
        arms = a["D01_static"]["arm_transitive_hidden_reach"]
        touched = a["D01_dynamic"].get("hidden_touched_by_realize")
        return _finish_infra(run, {"arm_reach": arms, "dynamic": touched, "direct": list(a["D01_static"]["direct_hidden_reads"])[:20]},
                             bool(arms) and bool(touched), f"non-oracle arms reach {sorted(set(sum(arms.values(), [])))}; realize touched {touched}", gate="record")
    if card == "D02":
        a = _audit()
        d = a.get("D02_decomposition") or {}
        return _finish_desc(run, {"decomposition": d}, json.dumps({k: round(v, 4) for k, v in d.items() if isinstance(v, (int, float))}))
    if card == "D03":
        a = _audit()
        return _finish_desc(run, {"counts": a["class_counts"], "dispositions": a["D03_dispositions"]}, json.dumps(a["class_counts"]))
    if card == "D04":
        a = _audit()
        return _finish_desc(run, {"suspended": a["D04_suspended"]}, "five conclusions suspended; supplied-law selection retained under its name")
    if card == "D05":
        a = _audit()
        d = a.get("D05_supplied_law_selection") or {}
        return _finish_desc(run, {"selection": d}, json.dumps({k: round(v, 3) for k, v in d.items() if isinstance(v, (int, float))}))
    if card == "D06":
        a = _audit()
        d = a["D06_identity"]
        return _finish_desc(run, {"identity": d}, f"identical vectors {d['identical_unit_vectors']}; constant {d.get('constant_vectors')}")
    if card == "D07":
        from runners.stage7.records import coauthor as CA                         # noqa: PLC0415
        f = CA.run_fixtures()
        ss = CA.coauthor_sessions(max_sessions=60)
        marg = {d: sum(s["marginal"][d] for s in ss) for d in CA.DECISIONS}
        zero = [d for d, v in marg.items() if v == 0 and d != "ignore"]
        ok = not f and not zero
        return _finish_infra(run, {"fixture_failures": f, "marginal_60_sessions": marg, "zero_classes": zero}, ok,
                             f"fixtures {'all exact' if not f else f}; marginal {marg}", gate="coauthor_loader")
    if card == "D08":
        from runners.stage7.records import coauthor as CA                         # noqa: PLC0415
        ss = CA.coauthor_sessions(max_sessions=200, require_reconstructed=False)
        rec = sum(1 for s in ss if s["reconstructed"])
        fields = {"final_document_reference": False, "suggestion_text": True, "selection_event": True, "close_event": True, "text_deltas": True}
        return _finish_desc(run, {"sessions": len(ss), "reconstructed": rec, "rate": rec / max(1, len(ss)), "licensed_fields": fields,
                                  "claim": "internal delta consistency only; no final-text equality claim (the source carries no final reference)"},
                            f"{rec}/{len(ss)} sessions reconstruct under standard delta semantics; no final reference exists in the source")
    if card == "D09":
        a = _audit()
        return _finish_desc(run, {"natural": a["D09_natural"]}, json.dumps(a["D09_natural"].get("scholawrite_previous_category_persistence")))
    if card == "D10":
        lint = subprocess.run([PY, str(REPO / "tools" / "theory_lint.py")] + [str(p) for p in (REPO / "docs" / "theory").glob("*.md")],
                              capture_output=True, text=True, timeout=120, cwd=str(REPO))
        mult = subprocess.run([PY, str(REPO / "runners" / "audit_multiplicity.py")], capture_output=True, text=True, timeout=300, cwd=str(REPO))
        findings = (REPO / "FINDINGS.md").read_text(encoding="utf-8", errors="replace")
        theory = "".join(p.read_text(encoding="utf-8", errors="replace") for p in (REPO / "docs" / "theory").glob("*.md"))
        marker = "SUSPENDED (Stage 7 D04"
        marker2 = "(Stage 7 D01 to D06, L330)"           # the errata's VOID status carries the audit pointer
        has_entry = "L330" in findings and (marker in findings or marker2 in findings)
        theory_marked = theory.count(marker) + theory.count(marker2) >= 3
        ok = lint.returncode == 0 and mult.returncode == 0 and has_entry and theory_marked
        return _finish_infra(run, {"theory_lint_rc": lint.returncode, "multiplicity_rc": mult.returncode, "findings_entry": has_entry,
                                   "theory_markers": theory.count(marker) + theory.count(marker2), "lint_tail": lint.stdout[-300:] + lint.stderr[-300:]},
                             ok, f"lint {lint.returncode}; multiplicity {mult.returncode}; findings entry {has_entry}; theory markers {theory.count(marker) + theory.count(marker2)}", gate="record_written")
    raise ValueError(card)


# ── dispatch ─────────────────────────────────────────────────────────────────────────

ISOLATION = {"I01": run_I01, "I02": run_I02, "I03": run_I03, "I04": run_I04, "I08": run_I08, "I09": run_I09, "I10": run_I10,
             "I11": run_I11, "I12": run_I12, "I13": run_I13, "I14": run_I14, "I15": run_I15, "I16": run_I16}


def run_card(card: str) -> int:
    spec = C.ALL[card]
    run = CardRun7(card, require_lock=(spec["engine"] not in ("isolation", "dependency", "architecture") or card in ("A08", "A11", "A14", "A15", "A16")))
    engine = spec["engine"]
    try:
        if card in ISOLATION:
            return ISOLATION[card](run)
        if card in ("I05", "I06", "I07"):
            return _mutation_card(run, {"I05": "tail", "I06": "stop", "I07": "event"}[card])
        if engine == "dependency":
            return run_D(run)
        if engine in ("supplied", "reconstruct", "architecture"):
            from runners.stage7 import engine_supplied as ES                      # noqa: PLC0415
            return ES.run_card(run)
        if engine in ("prospective", "history"):
            from runners.stage7 import engine_prospective as EP                   # noqa: PLC0415
            return EP.run_card(run)
        if engine == "closure":
            from runners.stage7 import confirmation as CF                         # noqa: PLC0415
            return CF.run_card(run)
        if engine == "attack":
            from runners.stage7 import attacks as X                               # noqa: PLC0415
            return X.run_card(run)
        raise ValueError(f"unknown engine {engine}")
    except DeadlineReached:
        run.flush()
        print(f"{card}: deadline reached; rows checkpointed")
        return 3


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--card", required=True, choices=sorted(C.ALL))
    a = ap.parse_args()
    return run_card(a.card)


if __name__ == "__main__":
    sys.exit(main())
