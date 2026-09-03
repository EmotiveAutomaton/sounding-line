"""Stage 7 scheduler (brief §12.1, §13): prepare, pilot, run, sign-keystone, freeze,
validate, final-packet, status, reset. ONE immutable 72-hour ceiling started when the
discarded pilot begins and persisted across restarts; the gate order of §12.1 (record,
construction, isolation, keystone, supplied state, conformance, reconstruction,
ecological, confirmation) enforced as dependencies plus the scientific lock, which opens
only when the record gate (D01, D10), the isolation gates (I04-I10, I14), and the SIGNED
keystone lock exist; inside the ceiling the queue runs continuously (GPU cells serial in
the preservation order, CPU cells beside them under the Ghost V15 coexistence governor);
the confirmation freeze at hour 64 or on ladder exhaustion (at most three claims); on
exhaustion the RUNTIME record, validation, and the one packet; exhaustion before hour 54
writes SHORT_RUN.json with the honest cause.

DESIGN CHECK (2026-09-02)
lessons read: LESSONS §5 (all of it: produces guards; one manifest writer; retries with a
  cap; the exists() poll before declaring no-produce; kill by Windows pid; the deadline is
  a wake-and-decide event; a corrective stage list is audited like results; the governor
  reads Ghost's status read-only; reset refuses a live engine; useless compute stops
  mid-cell), §3 (a gate dependency is the verdict: the scientific lock reads the GATES
  registry, never a file's existence; the freeze precedes confirmation access).
gates: admission by dependency (a dead parent blocks the child); the workload lock before
  any discovery output; the scientific lock before discovery GPU cells beyond the
  integrity block; the confirmation freeze before B01-B03; the packet only after
  closure plus validation. bands: the engines'.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from runners.stage7 import cards as C                                              # noqa: E402
from runners.stage7.manifest import prepare_manifest                               # noqa: E402
from runners.stage7.validate import validate                                       # noqa: E402
from soundingline.stage7 import (S7, CLOSURE_HOUR, FLOOR_HOUR, USEFUL_TARGET_H,     # noqa: E402
                                 Manifest7, RunContract7, gate_state, ghost_status,
                                 now_iso, read_json, read_registry, write_registry)

PY = str(REPO / ".venv" / "Scripts" / "python.exe")
ENGINE = str(REPO / "runners" / "stage7" / "engines.py")
LOG = S7 / "scheduler.log"
MAX_ATTEMPTS = 3
SMOKE = bool(os.environ.get("S7_SMOKE"))
PILOT_MARGIN = 1.6
# the block that must land before the scientific lock (§12.1 gates 1-4)
INTEGRITY_FIRST = ["I01", "I02", "I03", "I11", "I14", "I04", "I10", "D07", "D08", "D01", "D03", "D04", "D06", "D09", "D05", "D02", "D10",
                   "A01", "A02", "A03", "A04", "A05", "A06", "A07", "A09", "A10", "A12", "A13",
                   "I05", "I06", "I07", "I08", "I09", "I12", "I13", "I15", "I16", "X04"]
LOCK_GATES = ("record", "record_written", "isolation", "mutation_tail", "mutation_stop", "mutation_event", "sensitivity", "canaries", "splits")


def log(msg: str) -> None:
    S7.mkdir(parents=True, exist_ok=True)
    line = f"[{now_iso()}] {msg}"
    print(line, flush=True)
    with open(LOG, "a", encoding="utf-8", newline="\n") as fh:
        fh.write(line + "\n")


def _fresh(contract: RunContract7) -> RunContract7:
    return RunContract7.load(contract.path) or contract


def verdict_path(cell: str) -> Path:
    return S7 / cell / "verdict.json"


# ── prepare ───────────────────────────────────────────────────────────────────────────

def prepare() -> int:
    S7.mkdir(parents=True, exist_ok=True)
    for sub in ("raw", "predictions", "posteriors", "confirmations", "oracle", "capsules"):
        (S7 / sub).mkdir(exist_ok=True)
    contract = RunContract7.create()
    info = prepare_manifest()
    from runners.stage7.conformance import sources as SRC                          # noqa: PLC0415
    SRC.write_manifest()
    write_registry("STRUCTURAL_LOCK", {"written_at": now_iso(), "questions": len(C.QUESTIONS), "attacks": len(C.ATTACKS),
                                       "contract_hash": contract.hash(), "expected_cells": info["expected"], "duplicate_identities": info["duplicates"]})
    write_registry("PREPARED", {"at": now_iso(), "cells": info["cells"], "contract_hash": contract.hash()})
    log(f"prepared: {info['cells']} cells, {info['expected']} expected cells, contract {contract.hash()}")
    return 0


# ── the discarded pilot (§13.3): starts the ONE clock ────────────────────────────────

def pilot() -> int:
    contract = RunContract7.load() or RunContract7.create()
    contract.start()
    log(f"PILOT begins; THE 72-HOUR CEILING STARTS: {contract.data['execution_start']} (deadline {contract.data['deadline']})")
    t0 = time.time()
    os.environ["S7_SPLIT"] = "pilot"
    timings: dict = {}
    from runners.stage7 import engines as E                                       # noqa: PLC0415
    from runners.stage7 import runtime as RT                                      # noqa: PLC0415
    from runners.stage7.constructor import worlds as W                            # noqa: PLC0415
    from runners.stage7.scoring import prospective as PS                          # noqa: PLC0415
    from runners.stage7.conformance import fixtures as F                          # noqa: PLC0415
    from runners.stage7.records import coauthor as CA                             # noqa: PLC0415
    from runners.stage7.records import scholawrite as SW                          # noqa: PLC0415
    from runners.stage7.records import mixed_control as MC                        # noqa: PLC0415
    from runners.stage7.constructor import histories as H                         # noqa: PLC0415
    from soundingline.stage7 import validate_prediction                           # noqa: PLC0415
    if not read_registry("DOM_FROZEN"):
        t1 = time.time()
        write_registry("DOM_FROZEN", E.fit_dom(24 if SMOKE else 96))
        timings["dom_fit_s"] = time.time() - t1
    readers = list(C.READERS.values()) + ([] if SMOKE else [C.SIZE_LADDER["qwen05"], C.SIZE_LADDER["qwen3"], C.SIZE_LADDER["qwen9b"]])
    n_pilot = 1 if SMOKE else 2
    worlds = [w for w in (W.make_world(f"PILOT|essay|s0|w{9000 + i:05d}|pilot", "essay") for i in range(12)) if not w["degenerate"]][:n_pilot]
    with E.ModelServer("s7_pilot", readers) as server:
        t1 = time.time()
        pr = RT.probe("PILOT", server.endpoint, server.token, [str(REPO / "soundingline" / "stage7.py"), str(S7 / "oracle")], other_port=RT.free_port())
        timings["probe_s"] = time.time() - t1
        timings["probe_all_raised"] = pr["all_raised"]
        for cond_card, arms in (("K04", ["SOL", "DOM", "DIR"]), ("R13", ["SLJ", "DIR"]), ("K14", ["LEARN", "KL"])):
            cond = E.build_condition(C.ALL[cond_card]["condition"], "pilot", cond_card)
            for w in worlds:
                ev = W.visible_evidence(w, cond)
                b = W.oracle_bundle(w, cond)
                for arm in arms:
                    for reader in (readers if arm in E.MODEL_ARMS else [None]):
                        t2 = time.time()
                        task = {"arm": arm, "model": reader or "", "seed": 1, "withheld": [f for f in C.ALL7 if f not in (ev.get("supplied_factors") or {}).get("factors", {})]}
                        cap = RT.materialize("PILOT", f"{cond_card}_{arm}_{(reader or 'x').split('/')[-1].replace(':', '-')}_{w['lid'][-11:]}", ev, task, read_registry("DOM_FROZEN"))
                        res = RT.run_capsule(cap, server.endpoint, server.token, reader or "", timeout_s=1800)
                        pred = res.get("prediction")
                        ok = bool(pred) and not validate_prediction(pred)
                        if ok:
                            PS.score(pred, b)
                        key = f"unit|{arm}|{(reader or 'solver').split('/')[-1]}"
                        timings.setdefault(key, []).append(time.time() - t2)
                        timings.setdefault("failures", []).append(f"{key}: {(res.get('error') or {}).get('error', res.get('stderr_tail', ''))[:120]}") if not ok else None
                        RT.cleanup_unit(cap)
        t1 = time.time()
        h = MC.unit("PILOT|human_then_model|h09000|pilot", "human_then_model")
        for arm in ("HPROC", "HDIR"):
            for reader in (readers[:1] if arm == "HDIR" else [None]):
                ev = MC.visible_evidence(h, "process", "pilot", "pilot")
                cap = RT.materialize("PILOT", f"hist_{arm}", ev, {"arm": arm, "model": reader or "", "seed": 1}, None)
                RT.run_capsule(cap, server.endpoint, server.token, reader or "", timeout_s=900)
                RT.cleanup_unit(cap)
        timings["history_s"] = time.time() - t1
        t1 = time.time()
        ss = CA.coauthor_sessions(max_sessions=1, lane="discovery")
        if ss:
            from runners.stage7 import engine_prospective as EP                   # noqa: PLC0415
            it = EP._coauthor_items(ss[0])[:1]
            if it:
                ev = {"version": "VisibleEvidenceV1", "unit_ref": "pilot", "condition_ref": "P13", "domain": "coauthor", "regime": "cold", "render": "log",
                      "history": {"interface": "coauthor", "doc_tail": it[0]["doc_tail"], "doc_len": it[0]["doc_len"], "suggestion": it[0]["suggestion"], "prior_decisions": []},
                      "query": {"decision_options": list(CA.DECISIONS)}}
                cap = RT.materialize("PILOT", "coauthor_CDIR", ev, {"arm": "CDIR", "model": readers[0], "seed": 1}, None)
                RT.run_capsule(cap, server.endpoint, server.token, readers[0], timeout_s=600)
                RT.cleanup_unit(cap)
        timings["coauthor_item_s"] = time.time() - t1
        t1 = time.time()
        try:
            sw = SW.sessions(max_sessions=1, lane="discovery")
            if sw:
                its = SW.switch_items(sw[0])[:1]
                if its:
                    ev = {"version": "VisibleEvidenceV1", "unit_ref": "pilot", "condition_ref": "P14", "domain": "scholawrite", "regime": "cold", "render": "log",
                          "history": {"interface": "scholawrite", "window": its[0]["context"], "current_category": its[0]["current"]}, "query": {"category_options": list(SW.CATEGORIES)}}
                    cap = RT.materialize("PILOT", "schola_SDIR", ev, {"arm": "SDIR", "model": readers[0], "seed": 1, "persistence_rate": 0.8}, None)
                    RT.run_capsule(cap, server.endpoint, server.token, readers[0], timeout_s=600)
                    RT.cleanup_unit(cap)
        except Exception as e:                                                    # noqa: BLE001
            timings["scholawrite_error"] = repr(e)[:200]
        timings["scholawrite_item_s"] = time.time() - t1
    timings["gpu_lock_held_s"] = server.held_s
    t1 = time.time()
    conf = F.run_all()
    timings["conformance_s"] = time.time() - t1
    timings["conformance_pass"] = {k: v.get("pass") for k, v in conf.items()}
    for k, v in list(timings.items()):
        if isinstance(v, list) and v and isinstance(v[0], float):
            timings[k] = sum(v) / len(v)
    write_registry("PILOT", {"written_at": now_iso(), "timings": timings, "wall_s": time.time() - t0, "discarded": True,
                             "note": "pilot outputs are not promotable (§13.3); pilot lineages never enter science"})
    _workload_lock(contract, timings)
    os.environ.pop("S7_SPLIT", None)
    log(f"pilot done in {(time.time() - t0) / 60:.1f} min; workload locked")
    return 0


def _unit_costs(timings: dict) -> dict:
    """Measured per-unit costs by arm class from the pilot, with the predeclared margin."""
    def pick(prefixes, default):
        vals = [v for k, v in timings.items() if isinstance(v, (int, float)) and any(k.startswith(p) for p in prefixes)]
        return (max(vals) if vals else default) * PILOT_MARGIN
    failures = " ".join(timings.get("failures") or [])
    model = pick(["unit|DIR", "unit|DIRS"], 20.0)
    joint = pick(["unit|SLJ"], 30.0)
    if "unit|SLJ" in failures:
        joint = max(joint, 1.2 * model)                 # a failed pilot arm is not a cheap arm
    # a record item is one likelihood call (the ScholaWrite pilot item carries the one-time
    # dataset load, which is not a per-item cost); the CoAuthor item measures the call
    return {"model": model, "joint": joint, "solver": pick(["unit|SOL", "unit|DOM", "unit|KL", "unit|LEARN"], 2.0),
            "history": max(timings.get("history_s", 20.0) / 2, 5.0) * PILOT_MARGIN,
            "record_item": max(float(timings.get("coauthor_item_s", 1.0)), 0.5) * PILOT_MARGIN}


def _card_hours(card: str, costs: dict, mult: float = 1.0) -> float:
    spec = C.ALL[card]
    n = C.units_for(card) * mult
    if spec["engine"] == "attack" and not spec["gpu"]:
        return 0.05
    if spec["unit"] in ("audit", "analysis", "receipt", "ledger", "fixture", "probe"):
        return spec["est_s_per_unit"] * C.units_for(card) / 3600 * 0.5
    readers = len(spec.get("readers") or [1])
    corners = 1
    for lv in (spec.get("factors") or {}).values():
        corners *= max(1, len(lv))
    arms = spec.get("arms") or ["DIR"]
    from runners.stage7.engines import MODEL_ARMS                                 # noqa: PLC0415
    per_unit = 0.0
    for a in arms:
        if a in ("SLJ", "sequential_hypothesis_particles", "adaptive_factor_expansion"):
            per_unit += costs["joint"] * readers
        elif a in MODEL_ARMS:
            per_unit += costs["model"] * readers
        elif a in ("HPROC", "HSTYLE", "HPERS", "HSTACK", "HU"):
            per_unit += costs["history"] / 4
        else:
            per_unit += costs["solver"]
    if spec["unit"] in ("session",):
        per_unit = costs["record_item"] * 10 * (1 if "CDIR" not in arms and "SDIR" not in arms else readers)
    twin = 2 if spec["unit"] == "world_pair" or spec["condition"].get("twin") else 1
    doms = 2 if spec["unit"] in ("world", "world_pair") else 1
    return per_unit * n * doms * twin * corners / 3600 / (corners if spec["engine"] in ("supplied", "architecture") and card in ("K16", "A16") else 1)


def _workload_lock(contract: RunContract7, timings: dict) -> None:
    """Freeze the admitted workload from measured costs: the minimum tier for every
    question; the ladder sized so base plus ladder lands in the 54-66 useful-hour target
    with the closure reserve; a residual shortfall closes under the short-run rule."""
    costs = _unit_costs(timings)

    def _weighted(card: str) -> float:
        # GPU cells serialize on the card; CPU cells run beside them under the governor's
        # cap of two or three, so they cost half their wall on the clock
        h = _card_hours(card, costs)
        return h if C.ALL[card]["gpu"] else h / 2.0
    nominal_h = sum(_weighted(card) for card in C.ALL)
    reserve_h = 8.0
    target_mid = sum(USEFUL_TARGET_H) / 2
    # the smallest complete tier: the registry's nominal counts scaled so the base lands
    # under the target's lower edge plus a ladder share, never past the ceiling (§13.1)
    base_target = min(USEFUL_TARGET_H[0], 72.0 - reserve_h - 6.0)
    factor = 1.0 if nominal_h <= base_target else max(0.25, base_target / nominal_h)
    write_registry("WORKLOAD_LOCK", {"tier_factor": factor, "written_at": now_iso(), "provisional": True})
    base_h = 0.0
    card_h = {}
    for card in C.ALL:
        h = _card_hours(card, costs)
        card_h[card] = round(h, 3)
        base_h += h if C.ALL[card]["gpu"] else h / 2.0
    budget = max(0.0, min(target_mid, 72.0 - reserve_h) - base_h)      # the ladder fills the target, never the ceiling
    rungs = []
    total = 0.0
    weights = {r["rung"]: sum(card_h.get(c, 0.2) for c in r["cards"]) for r in C.EXPANSION_LADDER}
    for rung in C.EXPANSION_LADDER:
        rn = rung["rung"]
        rung_base = max(0.2, weights.get(rn, 0.2))
        # rungs admitted IN ORDER while the budget lasts: the first rung takes up to 4x, later rungs 1x
        cap = 4 if rn == 1 else (2 if rn <= 3 else 1)
        mult = 0
        while mult < cap and total + rung_base * (mult + 1) <= budget:
            mult += 1
        rung_h = rung_base * mult
        rungs.append({**rung, "n_mult": mult, "forecast_h": round(rung_h, 1), "admitted": mult > 0})
        total += rung_h
    write_registry("WORKLOAD_LOCK", {"written_at": now_iso(), "tier": "minimum", "tier_factor": round(factor, 4), "nominal_forecast_h": round(nominal_h, 1),
                                     "unit_costs_s": {k: round(v, 2) for k, v in costs.items()},
                                     "card_hours": card_h, "base_forecast_h": round(base_h, 1), "ladder": rungs, "ladder_forecast_h": round(total, 1),
                                     "total_forecast_h": round(base_h + total + reserve_h, 1), "target_h": list(USEFUL_TARGET_H), "ceiling_h": 72,
                                     "margin": PILOT_MARGIN, "reserve_h": reserve_h,
                                     "shortfall_h": round(max(0.0, USEFUL_TARGET_H[0] - base_h - total), 1),
                                     "note": "gated branches may close; rung multipliers are additional independent units (power), capped at 8x per rung; a residual shortfall closes under the short-run rule"})


def scientific_lock() -> bool:
    """§12.1 gates 1-4 as VERDICTS: the record gate, the isolation gates, the splits, and
    the signed keystone; then freeze readers, thresholds, and gates into the design."""
    contract = RunContract7.load()
    missing = [g for g in LOCK_GATES if not (gate_state(g) or {}).get("passed")]
    key = read_registry("KEYSTONE_LOCK") or {}
    if missing or not key.get("signed"):
        write_registry("SCIENTIFIC_LOCK", {"written_at": now_iso(), "locked": False, "missing_gates": missing, "keystone_signed": bool(key.get("signed"))})
        return False
    from runners import s5_lib                                                    # noqa: PLC0415
    readers = {name: (s5_lib.model_revision(name) if not name.startswith("ollama:") else name) for name in C.READERS.values()}
    design = {"readers": readers, "tier": "minimum", "thresholds": {c: C.ALL[c]["threshold"] for c in C.ALL},
              "gates": {g: (gate_state(g) or {}).get("passed") for g in LOCK_GATES}, "keystone": key,
              "dom_frozen": bool(read_registry("DOM_FROZEN")), "gain_floor_rule": "20 percent of the oracle-minus-DOM gap, fixed before reader outcomes"}
    if not contract.frozen("design"):
        contract.freeze("design", design)
    write_registry("SCIENTIFIC_LOCK", {"written_at": now_iso(), "locked": True, "design_hash": contract.data["frozen"]["design"]["hash"], "gates": design["gates"]})
    log("scientific lock written")
    return True


def sign_keystone(by: str) -> int:
    v = read_json(verdict_path("I16")) if verdict_path("I16").exists() else {}
    audit = S7 / "KEYSTONE_AUDIT.md"
    if v.get("outcome") != "INFRASTRUCTURE" or not audit.exists():
        print(f"refused: I16 {v.get('outcome')}; audit exists {audit.exists()}")
        return 2
    from soundingline.stage7 import sha256_file                                   # noqa: PLC0415
    write_registry("KEYSTONE_LOCK", {"signed": True, "by": by, "at": now_iso(), "audit_sha": sha256_file(audit)[:16], "i16_reason": v.get("reason")})
    log(f"keystone signed by {by}")
    return 0


# ── the run loop ──────────────────────────────────────────────────────────────────────

def _cpu_cap() -> int:
    g = ghost_status()
    return 2 if g.get("live") else 3


def _blocked_disposition(m: Manifest7, cell: str) -> None:
    """A blocked cell still owns a disposition file: validation counts every mandatory cell,
    and the packet cannot be written while one is missing (the rehearsal's B02 crash left
    B03 and B06 without files and the packet refused, 2026-09-02)."""
    from soundingline.stage7 import write_json                                     # noqa: PLC0415
    dead = [d for d in m.cells[cell]["depends_on"] if m.cells[d]["exec_state"] in ("FAILED", "BLOCKED", "DEFERRED")]
    vp = verdict_path(cell)
    if not vp.exists():
        write_json(vp, {"card": cell.split("/")[0], "cell_id": cell, "exec": "BLOCKED", "outcome": "NOT_RUN",
                        "reason": f"BLOCKED_DEPENDENCY: {dead}", "written_at": now_iso()})


def _admissible(m: Manifest7, cell: str) -> bool:
    c = m.cells.get(cell)
    if not c or c["exec_state"] != "PLANNED":
        return False
    if m.deps_dead(cell):
        m.set_exec(cell, "BLOCKED", "a dependency failed or was blocked")
        m.set_outcome(cell, "NOT_RUN", "BLOCKED_DEPENDENCY")
        _blocked_disposition(m, cell)
        log(f"blocked {cell}: a dependency failed or was blocked")
        return False
    return m.deps_complete(cell)


def _run_cell(m: Manifest7, contract: RunContract7, cell: str, extra_env: dict | None = None) -> str:
    m.set_exec(cell, "RUNNING")
    t0 = time.time()
    card = cell.split("/")[0]
    log(f"start {cell}")
    env = dict(os.environ)
    if "/" in cell:
        env["S7_CELL"] = cell
    env.update(extra_env or {})
    logf = open(S7 / f"{cell.replace('/', '_')}.log", "a", encoding="utf-8")
    try:
        rc = subprocess.call([PY, ENGINE, "--card", card], cwd=str(REPO), env=env, stdout=logf, stderr=subprocess.STDOUT)
    finally:
        logf.close()
    wall = time.time() - t0
    contract.data = _fresh(contract).data
    vp = verdict_path(cell)
    produced = False
    for _ in range(10):
        if vp.exists() and vp.stat().st_mtime >= t0 - 1:
            produced = True
            break
        time.sleep(1)
    if rc == 3:
        m.set_exec(cell, "DEFERRED", "deadline reached mid-card; rows checkpointed")
        return "DEFERRED"
    if rc != 0 or not produced:
        attempts = m.cells[cell]["attempts"]
        tail = ""
        try:
            tail = (S7 / f"{cell.replace('/', '_')}.log").read_text(encoding="utf-8", errors="replace")[-500:]
        except OSError:
            pass
        if attempts < MAX_ATTEMPTS:
            m.set_exec(cell, "PLANNED", f"exit {rc}; retry {attempts}/{MAX_ATTEMPTS}")
            log(f"retry {cell}: exit {rc}, produced {produced}, attempt {attempts}/{MAX_ATTEMPTS}: {tail[-160:]!r}")
            if "out of memory" in tail.lower():
                contract.record_lost_time(f"{cell} OOM wait", 120)
                time.sleep(120)
            return "RETRY"
        m.set_exec(cell, "FAILED", f"exit {rc} after {attempts} attempts")
        m.set_outcome(cell, "INSTRUMENT_FAILED", tail[-300:])
        log(f"FAILED {cell}: exit {rc} after {attempts} attempts: {tail[-200:]!r}")
        if not vp.exists():
            from soundingline.stage7 import write_json                             # noqa: PLC0415
            write_json(vp, {"card": card, "cell_id": cell, "exec": "FAILED", "outcome": "INSTRUMENT_FAILED",
                            "reason": f"exit {rc} after {attempts} attempts: {tail[-300:]}", "written_at": now_iso()})
        return "FAILED"
    v = read_json(vp)
    m.set_exec(cell, v.get("exec", "COMPLETE"), v.get("reason"))
    oc = v.get("outcome")
    from soundingline.stage7 import OUTCOMES7                                     # noqa: PLC0415
    m.set_outcome(cell, oc if oc in OUTCOMES7 or oc == "NOT_RUN" else "VOID", v.get("reason"))
    m.charge(cell, wall / 60, float(v.get("gpu_lock_min") or 0.0))
    log(f"done {cell}: {m.cells[cell]['exec_state']}/{m.cells[cell]['outcome']} wall={wall / 60:.1f}min")
    return m.cells[cell]["exec_state"]


CONF_CELLS = ("B01", "B02", "B03")
LATE_CELLS = ("B05", "B06", "X24")        # closure ledgers: after the freeze, never before the science


def _next_gpu(m: Manifest7, allow_conf: bool, locked: bool) -> str | None:
    for cell in C.PRESERVATION_ORDER + [k for k in m.cells if "/" in k]:
        c = m.cells.get(cell)
        if not c or not c["gpu"]:
            continue
        card = cell.split("/")[0]
        if card in CONF_CELLS and not allow_conf:
            continue
        if not locked and card not in INTEGRITY_FIRST:
            continue
        if _admissible(m, cell):
            return cell
    if allow_conf:
        for cell in CONF_CELLS:
            if m.cells.get(cell, {}).get("gpu") and _admissible(m, cell):
                return cell
    return None


def _cpu_starts(m: Manifest7, running: dict, cap: int, allow_conf: bool, locked: bool) -> list[str]:
    out = []
    for cell in C.PRESERVATION_ORDER + list(LATE_CELLS) + [k for k in m.cells if "/" in k]:
        if len(running) + len(out) >= cap:
            break
        c = m.cells.get(cell)
        if not c or c["gpu"] or cell in running:
            continue
        card = cell.split("/")[0]
        if card in LATE_CELLS and not allow_conf:
            continue
        if not locked and card not in INTEGRITY_FIRST:
            continue
        if _admissible(m, cell):
            out.append(cell)
    return out


def _freeze_confirmations(m: Manifest7) -> None:
    if read_registry("CONFIRMATION_REGISTRY"):
        return
    def v(c):
        return read_json(verdict_path(c)) if verdict_path(c).exists() else {}
    def lower(x):
        return (x.get("ci") or [-1e9])[0] if x.get("ci") else -1e9
    sel = []
    k_cands = [(c, v(c)) for c in ("K04", "K05", "K06", "K07", "K08", "K09", "K10", "K11", "K12", "K13", "K14", "K15") if v(c).get("outcome") == "SUPPORT_CANDIDATE"]
    if k_cands:
        c, x = max(k_cands, key=lambda kv: lower(kv[1]))
        sel.append({"card": c, "what": f"the strongest supplied-state capability effect ({x.get('primary', '')[:100]})", "point": x.get("point"), "slot": 1})
    conf = read_registry("CONFORMANCE") or {}
    r_cands = []
    for c in ("R09", "R10", "R11", "R12", "R13", "R14", "A08", "A11", "A14", "A15", "A16"):
        x = v(c)
        if x.get("outcome") != "SUPPORT_CANDIDATE":
            continue
        r_cands.append((c, x))
    if r_cands:
        c, x = max(r_cands, key=lambda kv: lower(kv[1]))
        sel.append({"card": c, "what": f"the strongest qualified reconstruction or architecture effect ({x.get('primary', '')[:100]})", "point": x.get("point"), "slot": 2})
    if (gate_state("discontinuity") or {}).get("passed") and (gate_state("style_crossover") or {}).get("passed"):
        sel.append({"card": "P12", "what": "process-discontinuity localization beyond style (P11/P12 passed)", "point": v("P12").get("point"), "slot": 3})
    write_registry("CONFIRMATION_REGISTRY", {"written_at": now_iso(), "selected": sel[:3],
                                             "rule": "the strongest supplied-state effect; the strongest qualified reconstruction or architecture effect; discontinuity if P11 and P12 passed (§12.5); a failed confirmation is never replaced"})
    log(f"confirmation freeze: {json.dumps(sel[:3])}")


def _rung_mult(rn: int) -> int:
    wl = read_registry("WORKLOAD_LOCK") or {}
    for rung in (wl.get("ladder") or []):
        if rung.get("rung") == rn:
            return int(rung.get("n_mult", 1))
    return 1


def _ladder_exhausted(m: Manifest7) -> bool:
    wl = read_registry("WORKLOAD_LOCK") or {}
    for rung in (wl.get("ladder") or []):
        rn = rung.get("rung")
        if not rung.get("n_mult"):
            continue
        for card in rung.get("cards") or []:
            if card in CONF_CELLS or not verdict_path(card).exists():
                continue
            c = m.cells.get(f"{card}/x{rn}")
            if c is None or c["exec_state"] in ("PLANNED", "RUNNING"):
                return False
    return True


def _ladder_next(m: Manifest7, contract: RunContract7) -> str | None:
    wl = read_registry("WORKLOAD_LOCK") or {}
    if any(c["exec_state"] in ("PLANNED", "RUNNING") for k, c in m.cells.items() if k.split("/")[0] not in CONF_CELLS + LATE_CELLS):
        return None
    if contract.elapsed_h() >= CLOSURE_HOUR - 2:
        return None
    for rung in (wl.get("ladder") or []):
        rn = rung["rung"]
        mult = int(rung.get("n_mult", 1))
        if mult <= 0:
            continue
        for card in rung.get("cards") or []:
            cell = f"{card}/x{rn}"
            if cell in m.cells or not verdict_path(card).exists():
                continue
            if read_json(verdict_path(card)).get("outcome") in ("INSTRUMENT_FAILED", "NOT_RUN"):
                continue
            m.add(cell, card, [card], str(verdict_path(cell)), C.est_minutes(card) * 0.6 * mult, C.ALL[card]["gpu"], f"expansion rung {rn} (x{mult} units): {rung['axis']}")
            log(f"ladder rung {rn} admitted: {cell} (x{mult} units)")
            return cell
    return None


def run() -> int:
    contract = RunContract7.load()
    if contract is None or not contract.data.get("execution_start"):
        raise SystemExit("run: the pilot has not started the clock; run `pilot` first (§13.2)")
    m = Manifest7()
    for cell, c in m.cells.items():
        if c["exec_state"] == "RUNNING":
            m.set_exec(cell, "PLANNED", "re-planned at restart; resumes from its rows")
    log(f"run: elapsed {contract.elapsed_h():.2f} h of {contract.data['run_hours']}; deadline {contract.data['deadline']}")
    running_cpu: dict = {}
    locked = bool((read_registry("SCIENTIFIC_LOCK") or {}).get("locked"))
    while True:
        contract.data = _fresh(contract).data
        elapsed = contract.elapsed_h()
        deadline = contract.deadline_passed()
        for cell, (proc, t0, logf) in list(running_cpu.items()):
            rc = proc.poll()
            if rc is None:
                continue
            logf.close()
            del running_cpu[cell]
            vp = verdict_path(cell)
            if rc == 0 and vp.exists():
                v = read_json(vp)
                m.set_exec(cell, v.get("exec", "COMPLETE"), v.get("reason"))
                from soundingline.stage7 import OUTCOMES7 as OC                   # noqa: PLC0415
                m.set_outcome(cell, v.get("outcome") if v.get("outcome") in OC or v.get("outcome") == "NOT_RUN" else "VOID", v.get("reason"))
            else:
                attempts = m.cells[cell]["attempts"]
                if attempts < MAX_ATTEMPTS:
                    m.set_exec(cell, "PLANNED", f"cpu exit {rc}; retry {attempts}")
                else:
                    m.set_exec(cell, "FAILED", f"cpu exit {rc}")
                    m.set_outcome(cell, "INSTRUMENT_FAILED")
                    if not vp.exists():
                        from soundingline.stage7 import write_json                 # noqa: PLC0415
                        write_json(vp, {"card": cell.split("/")[0], "cell_id": cell, "exec": "FAILED", "outcome": "INSTRUMENT_FAILED",
                                        "reason": f"cpu exit {rc} after {attempts} attempts", "written_at": now_iso()})
            m.charge(cell, (time.time() - t0) / 60, 0.0)
            log(f"cpu done {cell}: {m.cells[cell]['exec_state']}/{m.cells[cell]['outcome']}")
        if deadline:
            if running_cpu:
                time.sleep(15)
                continue
            log("THE CEILING HAS ELAPSED: no new work; closing")
            break
        if not locked:
            pending_i = [c for c in INTEGRITY_FIRST if m.cells[c]["exec_state"] in ("PLANNED", "RUNNING")]
            if not pending_i and not running_cpu:
                if SMOKE and os.environ.get("S7_AUTO_SIGN") and not (read_registry("KEYSTONE_LOCK") or {}).get("signed"):
                    sign_keystone("dress rehearsal (auto-signed under S7_SMOKE; never a real signature)")
                locked = scientific_lock()
                if not locked:
                    _status(m, contract, running_cpu, f"integrity block landed; the scientific lock waits on {(read_registry('SCIENTIFIC_LOCK') or {}).get('missing_gates')} and the signed keystone")
                    time.sleep(60)
                    continue
        if elapsed >= CLOSURE_HOUR:
            _freeze_confirmations(m)
        allow_conf = bool(read_registry("CONFIRMATION_REGISTRY"))
        cap = _cpu_cap()
        for cell in _cpu_starts(m, running_cpu, cap, allow_conf, locked):
            m.set_exec(cell, "RUNNING")
            env = dict(os.environ)
            if "/" in cell:
                env["S7_CELL"] = cell
                if "/x" in cell:
                    rn = int(cell.split("/x")[1])
                    env["S7_WORLD_OFFSET"] = str(5000 * rn)
                    env["S7_UNITS_MULT"] = str(_rung_mult(rn))
            logf = open(S7 / f"{cell.replace('/', '_')}.log", "a", encoding="utf-8")
            proc = subprocess.Popen([PY, ENGINE, "--card", cell.split("/")[0]], cwd=str(REPO), env=env, stdout=logf, stderr=subprocess.STDOUT)
            running_cpu[cell] = (proc, time.time(), logf)
            log(f"cpu start {cell} (cap {cap}, ghost {'live' if cap == 2 else 'quiet'})")
        cell = _next_gpu(m, allow_conf, locked)
        if cell is None and locked:
            cell = _ladder_next(m, contract)
        if cell is None:
            if running_cpu:
                _status(m, contract, running_cpu, "no GPU cell; CPU running")
                time.sleep(20)
                continue
            if not locked:
                time.sleep(20)
                continue
            if not allow_conf:
                if contract.elapsed_h() >= CLOSURE_HOUR or _ladder_exhausted(m):
                    _freeze_confirmations(m)
                    continue
                _status(m, contract, running_cpu, "pre-closure lull: the ladder is not exhausted; waiting")
                time.sleep(20)
                continue
            if any(m.cells[c]["exec_state"] == "PLANNED" for c in CONF_CELLS + LATE_CELLS if c in m.cells):
                time.sleep(5)
                continue
            if contract.elapsed_h() < FLOOR_HOUR:
                write_registry("SHORT_RUN", {"written_at": now_iso(), "elapsed_h": round(contract.elapsed_h(), 2),
                                             "cause": "the admitted workload and the whole locked ladder exhausted before the 54-hour useful-work floor; gated branches closed more cells than the lock's conditional forecast; nothing padded"})
                log(f"SHORT RUN at {contract.elapsed_h():.1f} h: the locked ladder is exhausted; honest cause written")
            break
        env = {}
        if "/x" in cell:
            rn = int(cell.split("/x")[1])
            env["S7_WORLD_OFFSET"] = str(5000 * rn)
            env["S7_UNITS_MULT"] = str(_rung_mult(rn))
        _status(m, contract, running_cpu, f"running {cell}")
        _run_cell(m, contract, cell, env)
    for cell, (proc, t0, logf) in running_cpu.items():
        try:
            proc.wait(timeout=1800)
        except subprocess.TimeoutExpired:
            proc.kill()
        logf.close()
    contract.data["run_label"] = "CEILING_ELAPSED" if contract.deadline_passed() else ("RUN_TO_EMPTY_SHORT" if contract.elapsed_h() < FLOOR_HOUR else "RUN_TO_EMPTY")
    contract.data["exhausted"] = True
    contract.data["short_of_floor"] = contract.elapsed_h() < FLOOR_HOUR
    contract.save()
    write_registry("RUNTIME", {"written_at": now_iso(), "elapsed_h": round(contract.elapsed_h(), 2),
                               "gpu_lock_seconds": sum(c.get("gpu_lock_min", 0.0) * 60 for c in m.cells.values()), "cells": m.state_counts()})
    validate(write=True)
    from runners.stage7 import report as REP                                      # noqa: PLC0415
    try:
        p = REP.write_final_packet()
        log(f"final packet written: {p}")
    except Exception as e:                                                        # noqa: BLE001
        log(f"packet refused or failed: {e}")
    return 0


def _status(m: Manifest7, contract: RunContract7, running_cpu: dict, note: str) -> None:
    g = ghost_status()
    write_registry("SCHEDULER_STATUS", {"at": now_iso(), "elapsed_h": round(contract.elapsed_h(), 2), "deadline": contract.data.get("deadline"),
                                        "counts": m.state_counts(), "running_cpu": list(running_cpu), "note": note,
                                        "ghost": {k: g.get(k) for k in ("live", "stage", "age_min", "program")}})
    samples = read_registry("COEXISTENCE") or {"samples": []}
    samples["samples"] = (samples.get("samples") or [])[-500:] + [{"at": now_iso(), "ghost_live": g.get("live"), "ghost_stage": g.get("stage")}]
    write_registry("COEXISTENCE", samples)


def _engine_alive() -> str | None:
    p = S7.parent / ".gear2.lock"
    if not p.exists():
        return None
    try:
        winpid = p.read_text(encoding="utf-8").splitlines()[1].strip()
    except (OSError, IndexError):
        return None
    try:
        out = subprocess.run(["tasklist", "/FI", f"PID eq {winpid}"], capture_output=True, text=True, timeout=15).stdout
    except Exception:                                                             # noqa: BLE001
        return None
    return winpid if f" {winpid} " in out else None


def reset(cells: list[str], tag: str, why: str) -> int:
    w = _engine_alive()
    if w:
        raise SystemExit(f"reset: the engine is running (winpid {w}); stop it first (a live engine's in-memory manifest saves clobber resets)")
    m = Manifest7()
    reps = read_registry("REPAIRS") or {"repairs": []}
    for cell in cells:
        if cell not in m.cells:
            raise SystemExit(f"reset: unknown cell {cell}")
        d = S7 / cell
        sup = d / f"superseded_{tag}"
        sup.mkdir(parents=True, exist_ok=True)
        moved = []
        for p in sorted(d.iterdir()) if d.exists() else []:
            if p.is_dir() and p.name.startswith("superseded_"):
                continue
            shutil.move(str(p), str(sup / p.name))
            moved.append(p.name)
        c = m.cells[cell]
        before = {k: c.get(k) for k in ("exec_state", "outcome", "attempts")}
        n_prior = sum(1 for r in reps["repairs"] if r["cell"] == cell)
        if n_prior >= 1:
            log(f"reset {cell}: this is repair {n_prior + 1}; the one-repair rule (§12.3) closes the family after a second failure; recorded")
        c.update({"exec_state": "PLANNED", "outcome": "NOT_RUN", "attempts": 0, "reason": f"reset ({tag}): {why}; first attempt preserved under {sup.name}/"})
        c.setdefault("resets", []).append({"at": now_iso(), "tag": tag, "why": why, "before": before, "moved": moved})
        m.save()
        reps["repairs"].append({"cell": cell, "tag": tag, "why": why, "at": now_iso(), "preserved": sup.name, "before": before})
        log(f"reset {cell} ({tag}): {why}; {len(moved)} files preserved")
    write_registry("REPAIRS", reps)
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("op", choices=["prepare", "pilot", "run", "lock", "sign-keystone", "freeze", "validate", "final-packet", "status", "reset"])
    ap.add_argument("--cells", nargs="*", default=[])
    ap.add_argument("--tag", default="repair")
    ap.add_argument("--why", default="")
    ap.add_argument("--by", default="")
    a = ap.parse_args()
    if a.op == "prepare":
        return prepare()
    if a.op == "pilot":
        return pilot()
    if a.op == "run":
        return run()
    if a.op == "lock":
        print("locked" if scientific_lock() else f"not locked: {read_registry('SCIENTIFIC_LOCK')}")
        return 0
    if a.op == "sign-keystone":
        return sign_keystone(a.by or "the curator loop's agent")
    if a.op == "freeze":
        _freeze_confirmations(Manifest7())
        return 0
    if a.op == "validate":
        print(json.dumps({k: v for k, v in validate(write=True).items() if k != "cells"}, indent=1)[:3000])
        return 0
    if a.op == "final-packet":
        from runners.stage7 import report as REP                                  # noqa: PLC0415
        print(REP.write_final_packet())
        return 0
    if a.op == "status":
        p = S7 / "SCHEDULER_STATUS.json"
        print(p.read_text(encoding="utf-8") if p.exists() else "no status")
        return 0
    if a.op == "reset":
        if not a.cells:
            print("reset needs --cells")
            return 2
        return reset(a.cells, a.tag, a.why)
    return 1


if __name__ == "__main__":
    sys.exit(main())
