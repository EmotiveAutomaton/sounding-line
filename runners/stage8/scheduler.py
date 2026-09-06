"""Stage 8 scheduler (brief §9, §12): prepare, pilot, run, lock, freeze, relock, validate,
final-packet, status, reset. ONE immutable 48-hour ceiling started when the discarded pilot
begins and persisted across restarts; the gate order of §9 (record, construction, isolation,
keystone, expertise, difference, explanation, accumulation, confirmation) enforced as
dependencies plus the scientific lock; the workload locked from the pilot's measured unit
costs and RE-LOCKED from the base run's actual per-card costs before any ladder rung is
admitted (§12.3); the theory-change interrupts (§9.1) close their gated branches and let
everything else run (an unattended run cannot idle on a ruling; the packet carries the
interrupt for the curator); the closure tail in the order each cell reads (B04, then the
fresh clone, then the ledgers last); exhaustion before the 36-hour floor writes SHORT_RUN.

DESIGN CHECK (2026-09-04)
lessons read: LESSONS §5 (all of it: produces guards; one manifest writer; retries with a
  cap; the exists() poll; kill by Windows pid; the deadline is a wake-and-decide event;
  the governor reads Ghost's status read-only; reset refuses a live engine; useless
  compute stops mid-cell; the ledger cell runs after what it counts), §3 (a gate
  dependency is the verdict).
gates: admission by dependency; the workload lock before any discovery output; the
  scientific lock before discovery GPU cells beyond the integrity block; the confirmation
  freeze before B01 and B02; the packet only after closure plus validation; the re-lock
  before any rung. Under the NULL, incomplete integrity or a failed packet write
  returns a nonzero closure exit and records the failure; the failure direction is
  DOWN. Under the ALTERNATIVE, resolved valid evidence writes the packet and exits
  successfully. These closure bands are exhaustive; scientific bands remain the engines'.
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

from runners.stage8 import cards as C                                              # noqa: E402
from runners.stage8.manifest import prepare_manifest                               # noqa: E402
from runners.stage8.validate import validate                                       # noqa: E402
from soundingline.stage8 import (S8, CLOSURE_HOUR, FLOOR_HOUR, USEFUL_TARGET_H, Manifest8,  # noqa: E402
                                 RunContract8, gate_state, ghost_status, interrupts,
                                 now_iso, read_json, read_registry, write_registry)

PY = str(REPO / ".venv" / "Scripts" / "python.exe")
ENGINE = str(REPO / "runners" / "stage8" / "engines.py")
LOG = S8 / "scheduler.log"
MAX_ATTEMPTS = 3
SMOKE = bool(os.environ.get("S7_SMOKE"))
PILOT_MARGIN = 1.6
RESERVE_H = 6.0
INTEGRITY_FIRST = C.INTEGRITY_FIRST
LOCK_GATES = ("record", "construction", "isolation", "mutation", "sensitivity", "canaries", "splits", "keystone")
RUNG_ENV = {3: {"S8_READER_SET": "qwen05"}, 5: {"S8_LONG_PREFIX": "1"}, 6: {"S8_STUDENT": "1"}, 7: {"S8_REVEAL_BALANCED": "1"}}


def log(msg: str) -> None:
    S8.mkdir(parents=True, exist_ok=True)
    line = f"[{now_iso()}] {msg}"
    print(line, flush=True)
    with open(LOG, "a", encoding="utf-8", newline="\n") as fh:
        fh.write(line + "\n")


def _fresh(contract: RunContract8) -> RunContract8:
    return RunContract8.load(contract.path) or contract


def verdict_path(cell: str) -> Path:
    return S8 / cell / "verdict.json"


# ── prepare ───────────────────────────────────────────────────────────────────────────

def prepare() -> int:
    S8.mkdir(parents=True, exist_ok=True)
    for sub in ("raw", "predictions", "oracle", "capsules", "adapters"):
        (S8 / sub).mkdir(exist_ok=True)
    contract = RunContract8.create()
    info = prepare_manifest()
    write_registry("STRUCTURAL_LOCK", {"written_at": now_iso(), "questions": len(C.QUESTIONS), "attacks": len(C.ATTACKS),
                                       "contract_hash": contract.hash(), "expected_cells": info["expected"], "duplicate_identities": info["duplicates"]})
    write_registry("PREPARED", {"at": now_iso(), "cells": info["cells"], "contract_hash": contract.hash()})
    log(f"prepared: {info['cells']} cells, {info['expected']} expected cells, contract {contract.hash()}")
    return 0


# ── the discarded pilot (§12.6): starts the ONE clock ────────────────────────────────

def pilot() -> int:
    contract = RunContract8.load() or RunContract8.create()
    contract.start()
    log(f"PILOT begins; THE 48-HOUR CEILING STARTS: {contract.data['execution_start']} (deadline {contract.data['deadline']})")
    t0 = time.time()
    os.environ["S7_SPLIT"] = "pilot"
    timings: dict = {}
    fake = bool(os.environ.get("S7_FAKE_SERVER"))
    from runners.stage8 import engines as E                                       # noqa: PLC0415
    from runners.stage8 import runtime as RT                                      # noqa: PLC0415
    from runners.stage8.constructor import population as POP                      # noqa: PLC0415
    from runners.stage8.constructor import purpose as PU                          # noqa: PLC0415
    from runners.stage8.cardrun import CardRun8                                   # noqa: PLC0415
    from soundingline.stage7 import validate_prediction                           # noqa: PLC0415
    from runners.stage7.scoring import prospective as PS                          # noqa: PLC0415
    if not read_registry("DOM_FROZEN"):
        t1 = time.time()
        write_registry("DOM_FROZEN", E.fit_dom_pop(20 if SMOKE else 120))
        timings["dom_fit_s"] = time.time() - t1
    # (1) one adapter training epoch on the smallest reader: the cost the lock is sized from
    t1 = time.time()
    if fake or os.environ.get("S8_SKIP_TRAIN"):
        run = CardRun8("E02", require_lock=False)
        os.environ["S7_FAKE_SERVER"] = "1"
        E.run_E02(run)                                                            # fake adapters for the rehearsal
        timings["train_epoch_s"] = 60.0
        timings["train_fake"] = True
        pilot_reader = "adapter:fm_qwen"
    else:
        rc = E._train("fm_qwen05", ["--pilot"])
        curve = ((read_registry("TRAINING") or {}).get("fm_qwen05") or {}).get("curve") or []
        timings["train_epoch_s"] = float(curve[-1].get("epoch_s") or (time.time() - t1)) if curve else time.time() - t1
        timings["train_rc"] = rc
        pilot_reader = "adapter:fm_qwen05"
    timings["train_wall_s"] = time.time() - t1
    # (2) one unit of each arm class through the capsule on the pilot adapter
    ws = []
    for i in range(30):
        w = PU.make_pu_world(f"PILOT|essay|s0|w{9000 + i:05d}|pilot", "essay")
        if not w["degenerate"] and w["hidden"]["next_action"] is not None:
            ws.append(w)
        if len(ws) >= (1 if SMOKE else 2):
            break
    if ws:
        with E.ModelServer("s8_pilot", [pilot_reader]) as server:
            t1 = time.time()
            pr = RT.probe("PILOT", server.endpoint, server.token, [str(REPO / "soundingline" / "stage8.py"), str(S8 / "adapters")], other_port=RT.free_port())
            timings["probe_s"] = time.time() - t1
            timings["probe_all_raised"] = pr["all_raised"]
            for w in ws:
                for arm, extra, per_event in (("FM", {}, False), ("DOM", {}, False), ("DIR0", {}, False), ("PUR", {"purpose_candidates": PU.purpose_candidates()}, False),
                                              ("FMP", {"propose": True, "purpose_candidates": PU.purpose_candidates()}, False), ("GEN", {"max_lines": 30}, False), ("FM", {}, True)):
                    cond = E.build_condition(C.ALL["G02"]["condition"], "pilot", "PILOT")
                    if per_event:
                        cond["per_event"] = True
                    ev = E.evidence_for(w, cond)
                    b = E.bundle_for(w, cond, ev)
                    task = {"arm": arm, "model": (C.base_of(pilot_reader) if arm == "DIR0" else (pilot_reader if arm in C.MODEL_ARMS else "")), "seed": 1, "withheld": [], **extra}
                    if per_event:
                        task["per_event"] = True
                    t2 = time.time()
                    cap = RT.materialize("PILOT", f"{arm}{'_pe' if per_event else ''}_{w['lid'][-11:]}", ev, task, read_registry("DOM_FROZEN"))
                    res = RT.run_capsule(cap, server.endpoint, server.token, task["model"], timeout_s=1800)
                    pred = res.get("prediction")
                    ok = bool(pred) and not validate_prediction(pred)
                    if ok and not per_event:
                        PS.score(pred, b)
                    key = f"unit|{arm}{'|per_event' if per_event else ''}"
                    timings.setdefault(key, []).append(time.time() - t2)
                    if not ok:
                        timings.setdefault("failures", []).append(f"{key}: {(res.get('error') or {}).get('error', res.get('stderr_tail', ''))[:160]}")
                    RT.cleanup_unit(cap)
            timings["gpu_lock_held_s"] = server.held_s
    # (3) the frontier calibration fixture
    if not fake and os.environ.get("GEMINI_API_KEY") and not os.environ.get("S8_SKIP_FR"):
        from runners.stage8 import frontier as FR                                 # noqa: PLC0415
        t1 = time.time()
        try:
            fx = FR.calibration_fixture(4 if SMOKE else 8)
            timings["frontier_fixture"] = {k: v.get("pass") for k, v in fx.items()}
            timings["frontier_usd"] = (read_registry("FRONTIER_LEDGER") or {}).get("total_usd")
        except Exception as e:                                                    # noqa: BLE001
            timings["frontier_error"] = repr(e)[:300]
        timings["frontier_s"] = time.time() - t1
    # (4) one testbed receipt and one fetch
    t1 = time.time()
    try:
        from runners.stage8.testbed import clones as CL                           # noqa: PLC0415
        timings["clone_receipt"] = CL.receipt("thought-tracing").get("present")
        if not fake and not SMOKE:
            from fetch.fetcher import Fetcher                                     # noqa: PLC0415
            r = Fetcher(allow_hosts={"raw.githubusercontent.com"}).fetch("https://raw.githubusercontent.com/skywalker023/thought-tracing/main/README.md")
            timings["fetch_chars"] = r.n_chars
    except Exception as e:                                                        # noqa: BLE001
        timings["testbed_error"] = repr(e)[:200]
    timings["testbed_s"] = time.time() - t1
    for k, v in list(timings.items()):
        if isinstance(v, list) and v and isinstance(v[0], float):
            timings[k] = sum(v) / len(v)
    write_registry("PILOT", {"written_at": now_iso(), "timings": timings, "wall_s": time.time() - t0, "discarded": True,
                             "note": "pilot outputs are not promotable (§12.6); pilot lineages never enter science; the pilot adapter is the cost measurement only"})
    _workload_lock(contract, timings)
    os.environ.pop("S7_SPLIT", None)
    log(f"pilot done in {(time.time() - t0) / 60:.1f} min; workload locked")
    return 0


def _unit_costs(timings: dict) -> dict:
    def pick(prefixes, default):
        vals = [v for k, v in timings.items() if isinstance(v, (int, float)) and any(k.startswith(p) for p in prefixes)]
        return (max(vals) if vals else default) * PILOT_MARGIN
    return {"model": pick(["unit|FM", "unit|FMP"], 4.0), "per_event": pick(["unit|FM|per_event"], 12.0), "gen": pick(["unit|GEN"], 8.0),
            "proposal": pick(["unit|PUR"], 3.0), "dir0": pick(["unit|DIR0"], 6.0), "solver": pick(["unit|DOM"], 1.5), "fr": 25.0,
            "train_epoch_s": float(timings.get("train_epoch_s") or 600.0) * PILOT_MARGIN}


def _card_hours(card: str, costs: dict, mult: float = 1.0) -> float:
    spec = C.ALL[card]
    n = C.units_for(card) * mult
    if spec["engine"] == "attack" and not spec["gpu"] and card != "X12":
        return 0.05
    if spec["unit"] in ("audit", "analysis", "receipt", "ledger", "fixture", "probe"):
        return spec["est_s_per_unit"] * C.units_for(card) / 3600 * 0.5
    if spec["unit"] == "training":
        return costs["train_epoch_s"] * 4 * 3 * 2 * 1.3 / 3600      # the pilot epoch (400 examples, the 0.5B) scaled to 1600 examples and a 1.5B reader, three epochs, two readers, the held-out evaluations
    readers = len(spec.get("readers") or [1])
    corners = 1
    for lv in (spec.get("factors") or {}).values():
        corners *= max(1, len(lv))
    arms = spec.get("arms") or ["FM"]
    per_unit = 0.0
    per_event = bool((spec.get("condition") or {}).get("per_event"))
    for a in arms:
        if a == "FR":
            per_unit += costs["fr"] * (6 if per_event else 1)
        elif a in ("PUR", "PULL", "LAWR", "RESR"):
            per_unit += costs["proposal"] * readers
        elif a == "GEN":
            per_unit += costs["gen"] * readers
        elif a == "DIR0":
            per_unit += costs["dir0"] * readers
        elif a in C.MODEL_ARMS:
            per_unit += (costs["per_event"] if per_event else costs["model"]) * readers
        else:
            per_unit += costs["solver"]
    doms = 2 if spec["unit"] in ("world", "maker") else 1
    variants = {"E06": 2, "D04": 2, "G06": 3, "A05": 4, "A03": 2, "X05": 2, "X06": 2}.get(card, 1)
    return per_unit * n * doms * corners * variants / 3600


def _workload_lock(contract: RunContract8, timings: dict) -> None:
    costs = _unit_costs(timings)

    def _weighted(card: str) -> float:
        h = _card_hours(card, costs)
        return h if C.ALL[card]["gpu"] else h / 2.0
    nominal_h = sum(_weighted(card) for card in C.ALL)
    target_mid = sum(USEFUL_TARGET_H) / 2
    base_target = min(USEFUL_TARGET_H[0], 48.0 - RESERVE_H - 4.0)
    factor = 1.0 if nominal_h <= base_target else max(0.25, base_target / nominal_h)
    write_registry("WORKLOAD_LOCK", {"tier_factor": factor, "written_at": now_iso(), "provisional": True})
    base_h = 0.0
    card_h = {}
    for card in C.ALL:
        h = _card_hours(card, costs)
        card_h[card] = round(h, 3)
        base_h += h if C.ALL[card]["gpu"] else h / 2.0
    budget = max(0.0, min(target_mid, 48.0 - RESERVE_H) - base_h)
    rungs = _size_ladder(card_h, budget)
    write_registry("WORKLOAD_LOCK", {"written_at": now_iso(), "tier": "minimum", "tier_factor": round(factor, 4), "nominal_forecast_h": round(nominal_h, 1),
                                     "unit_costs_s": {k: round(v, 2) for k, v in costs.items()},
                                     "card_hours": card_h, "base_forecast_h": round(base_h, 1), "ladder": rungs, "ladder_forecast_h": round(sum(r["forecast_h"] for r in rungs), 1),
                                     "target_h": list(USEFUL_TARGET_H), "ceiling_h": 48, "margin": PILOT_MARGIN, "reserve_h": RESERVE_H,
                                     "relocked": False,
                                     "note": "provisional from the pilot's measured unit costs; the ladder is RE-LOCKED from the base run's actual per-card costs before any rung is admitted (§12.3)"})


def _size_ladder(card_h: dict, budget: float) -> list[dict]:
    rungs = []
    total = 0.0
    for rung in C.EXPANSION_LADDER:
        rn = rung["rung"]
        rung_base = max(0.2, sum(card_h.get(c, 0.2) for c in rung["cards"]))
        cap = 4 if rn == 1 else (2 if rn <= 3 else 1)
        mult = 0
        while mult < cap and total + rung_base * (mult + 1) <= budget:
            mult += 1
        rung_h = rung_base * mult
        rungs.append({**rung, "n_mult": mult, "forecast_h": round(rung_h, 1), "admitted": mult > 0})
        total += rung_h
    return rungs


def relock(contract: RunContract8, m: Manifest8) -> dict:
    """§12.3: when the base completes, re-lock the ladder from the base run's ACTUAL per-card
    costs (the manifest's charged minutes) and the remaining budget to the useful-work target."""
    wl = read_registry("WORKLOAD_LOCK") or {}
    actual = {}
    for cell, c in m.cells.items():
        if "/" in cell:
            continue
        mins = float(c.get("budget_charged_min") or 0.0)
        actual[cell] = round(mins / 60.0, 3)
    forecast = wl.get("card_hours") or {}
    ratio = {}
    for card, h in actual.items():
        f = forecast.get(card)
        if f and h > 0:
            ratio[card] = round(h / f, 2)
    elapsed = contract.elapsed_h()
    budget = max(0.0, min(USEFUL_TARGET_H[1], 48.0 - RESERVE_H) - elapsed)
    rungs = _size_ladder({k: max(v, 0.02) for k, v in actual.items()}, budget)
    wl.update({"ladder": rungs, "relocked": True, "relocked_at": now_iso(), "actual_card_hours": actual, "forecast_to_actual_ratio": ratio,
               "relock_elapsed_h": round(elapsed, 2), "relock_budget_h": round(budget, 2), "ladder_forecast_h": round(sum(r["forecast_h"] for r in rungs), 1)})
    write_registry("WORKLOAD_LOCK", wl)
    write_registry("RELOCK", {"at": now_iso(), "elapsed_h": round(elapsed, 2), "budget_h": round(budget, 2), "ladder": rungs, "ratio": ratio,
                              "note": "rung multipliers computed at admission from measured costs, never frozen from the pilot forecast"})
    log(f"RE-LOCK at {elapsed:.1f} h: budget {budget:.1f} h; ladder {[(r['rung'], r['n_mult']) for r in rungs]}")
    return wl


def scientific_lock() -> bool:
    contract = RunContract8.load()
    missing = [g for g in LOCK_GATES if not (gate_state(g) or {}).get("passed")]
    key = read_registry("KEYSTONE_LOCK") or {}
    if missing or not key.get("signed"):
        write_registry("SCIENTIFIC_LOCK", {"written_at": now_iso(), "locked": False, "missing_gates": missing, "keystone_signed": bool(key.get("signed"))})
        return False
    adapters = read_registry("ADAPTERS") or {}
    readers = {}
    for rid in C.READERS.values():
        name = rid.split(":", 1)[1]
        rec = adapters.get(name) or {}
        readers[rid] = f"{rec.get('revision', rec.get('base', ''))}+adapter:{rec.get('sha', '?')}"
    design = {"readers": readers, "tier": "minimum", "thresholds": {c: C.ALL[c]["threshold"] for c in C.ALL},
              "gates": {g: (gate_state(g) or {}).get("passed") for g in LOCK_GATES}, "keystone": key,
              "dom_frozen": bool(read_registry("DOM_FROZEN")), "tail_thresholds": read_registry("TAIL_THRESHOLDS"),
              "expertise_band_nats": -0.05, "generation_percentile": 20,
              "gain_floor_rule": "a fifth of the relevant oracle-minus-DOM gap, whole and tail separately, fixed before reader outcomes"}
    if not contract.frozen("design"):
        contract.freeze("design", design)
    write_registry("SCIENTIFIC_LOCK", {"written_at": now_iso(), "locked": True, "design_hash": contract.data["frozen"]["design"]["hash"], "gates": design["gates"]})
    log("scientific lock written")
    return True


# ── the run loop ──────────────────────────────────────────────────────────────────────

GEAR_FILE = S8.parent / ".gear"


def gear() -> str:
    """The gear he called (results/.gear: one | two; absent means two). Read between units so
    a shift takes effect on the next start without stopping anything."""
    try:
        g = GEAR_FILE.read_text(encoding="utf-8").strip().lower()
    except OSError:
        return "two"
    return "one" if g in ("one", "1", "first") else "two"


def _cpu_cap() -> int:
    if gear() == "one":
        return 1
    return 2 if ghost_status().get("live") else 3


def _child_flags() -> int:
    """Gear one starts every cell below normal priority (Windows); affinity is inherited from
    the wrapper, which tools/gear1_throttle.ps1 pins at launch."""
    if gear() == "one" and os.name == "nt":
        return getattr(subprocess, "BELOW_NORMAL_PRIORITY_CLASS", 0x4000)
    return 0


def _blocked_by_interrupt(cell: str) -> str | None:
    card = cell.split("/")[0]
    for it in interrupts():
        if card in (it.get("blocks") or []) and not it.get("ruled"):
            return it["name"]
    return None


def _blocked_disposition(m: Manifest8, cell: str, why: str) -> None:
    from soundingline.stage8 import write_json                                     # noqa: PLC0415
    vp = verdict_path(cell)
    if not vp.exists():
        write_json(vp, {"card": cell.split("/")[0], "cell_id": cell, "exec": "BLOCKED", "outcome": "NOT_RUN", "reason": why, "written_at": now_iso()})


def _admissible(m: Manifest8, cell: str) -> bool:
    c = m.cells.get(cell)
    if not c or c["exec_state"] != "PLANNED":
        return False
    if m.deps_dead(cell):
        m.set_exec(cell, "BLOCKED", "a dependency failed or was blocked")
        m.set_outcome(cell, "NOT_RUN", "BLOCKED_DEPENDENCY")
        dead = [d for d in c["depends_on"] if m.cells[d]["exec_state"] in ("FAILED", "BLOCKED", "DEFERRED")]
        _blocked_disposition(m, cell, f"BLOCKED_DEPENDENCY: {dead}")
        log(f"blocked {cell}: a dependency failed or was blocked")
        return False
    if not m.deps_complete(cell):
        return False
    it = _blocked_by_interrupt(cell)
    if it:
        m.set_exec(cell, "BLOCKED", f"theory-change interrupt: {it}")
        m.set_outcome(cell, "NOT_RUN", f"INTERRUPT: {it}")
        _blocked_disposition(m, cell, f"theory-change interrupt {it}: the gated branch is closed pending the curator's ruling (§9.1)")
        log(f"blocked {cell} by the interrupt {it}")
        return False
    return True


def _rung_env(cell: str) -> dict:
    env = {}
    if "/x" in cell:
        rn = int(cell.split("/x")[1])
        env["S7_WORLD_OFFSET"] = str(5000 * rn)
        env["S7_UNITS_MULT"] = str(_rung_mult(rn))
        env.update(RUNG_ENV.get(rn, {}))
    return env


def _run_cell(m: Manifest8, contract: RunContract8, cell: str, extra_env: dict | None = None) -> str:
    m.set_exec(cell, "RUNNING")
    t0 = time.time()
    card = cell.split("/")[0]
    log(f"start {cell}")
    env = dict(os.environ)
    if "/" in cell:
        env["S7_CELL"] = cell
    env.update(extra_env or {})
    logf = open(S8 / f"{cell.replace('/', '_')}.log", "a", encoding="utf-8")
    try:
        rc = subprocess.call([PY, ENGINE, "--card", card], cwd=str(REPO), env=env, stdout=logf, stderr=subprocess.STDOUT,
                             creationflags=_child_flags())
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
    if rc == 4:
        # endpoint starvation (503 out of memory under a shared card): not an attempt; wait, then rerun the lost units
        m.cells[cell]["attempts"] = max(0, m.cells[cell]["attempts"] - 1)
        m.set_exec(cell, "PLANNED", "endpoint starved; rows checkpointed; the lost units rerun after a five-minute wait")
        contract.record_lost_time(f"{cell} endpoint starved", 300)
        log(f"STARVED {cell}: a model arm lost more than a fifth of its rows to the endpoint; waiting 300 s, then rerunning the lost units")
        time.sleep(300)
        return "RETRY"
    if rc != 0 or not produced:
        attempts = m.cells[cell]["attempts"]
        tail = ""
        try:
            tail = (S8 / f"{cell.replace('/', '_')}.log").read_text(encoding="utf-8", errors="replace")[-500:]
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
            from soundingline.stage8 import write_json                             # noqa: PLC0415
            write_json(vp, {"card": card, "cell_id": cell, "exec": "FAILED", "outcome": "INSTRUMENT_FAILED",
                            "reason": f"exit {rc} after {attempts} attempts: {tail[-300:]}", "written_at": now_iso()})
        return "FAILED"
    v = read_json(vp)
    m.set_exec(cell, v.get("exec", "COMPLETE"), v.get("reason"))
    oc = v.get("outcome")
    from soundingline.stage8 import OUTCOMES7                                     # noqa: PLC0415
    m.set_outcome(cell, oc if oc in OUTCOMES7 or oc == "NOT_RUN" else "VOID", v.get("reason"))
    m.charge(cell, wall / 60, float(v.get("gpu_lock_min") or 0.0))
    log(f"done {cell}: {m.cells[cell]['exec_state']}/{m.cells[cell]['outcome']} wall={wall / 60:.1f}min")
    return m.cells[cell]["exec_state"]


CONF_CELLS = C.CONF_CELLS
LATE_CELLS = C.LATE_CELLS


def _next_gpu(m: Manifest8, allow_conf: bool, locked: bool) -> str | None:
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
        for cell in CONF_CELLS + tuple(k for k in m.cells if k.startswith("B01/")):
            if m.cells.get(cell, {}).get("gpu") and _admissible(m, cell):
                return cell
    return None


def _cpu_starts(m: Manifest8, running: dict, cap: int, allow_conf: bool, locked: bool, allow_late: bool) -> list[str]:
    out = []
    for cell in C.PRESERVATION_ORDER + list(LATE_CELLS) + [k for k in m.cells if "/" in k]:
        if len(running) + len(out) >= cap:
            break
        c = m.cells.get(cell)
        if not c or c["gpu"] or cell in running or cell in out:
            continue
        card = cell.split("/")[0]
        if card in LATE_CELLS and not allow_late:
            continue
        if not locked and card not in INTEGRITY_FIRST:
            continue
        if _admissible(m, cell):
            out.append(cell)
    return out


def _freeze_confirmations(m: Manifest8) -> None:
    if read_registry("CONFIRMATION_REGISTRY"):
        return
    from runners.stage8 import confirmation as CF                                 # noqa: PLC0415
    reg = CF.freeze_confirmations()
    log(f"confirmation freeze: {json.dumps(reg.get('selected'))}")


def _rung_mult(rn: int) -> int:
    wl = read_registry("WORKLOAD_LOCK") or {}
    for rung in (wl.get("ladder") or []):
        if rung.get("rung") == rn:
            return int(rung.get("n_mult", 1))
    return 1


def _base_done(m: Manifest8) -> bool:
    return not any(c["exec_state"] in ("PLANNED", "RUNNING") for k, c in m.cells.items() if "/" not in k and k.split("/")[0] not in CONF_CELLS + LATE_CELLS)


def _ladder_exhausted(m: Manifest8) -> bool:
    wl = read_registry("WORKLOAD_LOCK") or {}
    if not wl.get("relocked"):
        return False
    for rung in (wl.get("ladder") or []):
        rn = rung.get("rung")
        if not rung.get("n_mult"):
            continue
        for card in rung.get("cards") or []:
            if card in CONF_CELLS or not verdict_path(card).exists():
                continue
            if read_json(verdict_path(card)).get("outcome") in ("INSTRUMENT_FAILED", "NOT_RUN"):
                continue                                        # never admitted (a failed or blocked base card)
            c = m.cells.get(f"{card}/x{rn}")
            if c is None or c["exec_state"] in ("PLANNED", "RUNNING"):
                return False
    return True


def _ladder_next(m: Manifest8, contract: RunContract8) -> str | None:
    wl = read_registry("WORKLOAD_LOCK") or {}
    if any(c["exec_state"] in ("PLANNED", "RUNNING") for k, c in m.cells.items() if k.split("/")[0] not in CONF_CELLS + LATE_CELLS):
        return None
    if not wl.get("relocked"):
        wl = relock(contract, m)
    if contract.elapsed_h() >= CLOSURE_HOUR - 2:
        return None
    for rung in (wl.get("ladder") or []):
        rn = rung["rung"]
        mult = int(rung.get("n_mult", 1))
        if mult <= 0:
            continue
        for card in rung.get("cards") or []:
            cell = f"{card}/x{rn}"
            if cell in m.cells:
                continue
            if card in CONF_CELLS:
                continue                                        # rung 8's second confirmation lineage is admitted after the freeze
            if not verdict_path(card).exists() or read_json(verdict_path(card)).get("outcome") in ("INSTRUMENT_FAILED", "NOT_RUN"):
                continue
            deps = [card]
            if rn == 3 and card != "E02":
                deps = ["E02/x3"] if "E02/x3" in m.cells else [card]
            m.add(cell, card, deps, str(verdict_path(cell)), C.est_minutes(card) * 0.6 * mult, C.ALL[card]["gpu"], f"expansion rung {rn} (x{mult} units): {rung['axis']}")
            log(f"ladder rung {rn} admitted: {cell} (x{mult} units)")
            return cell
    return None


def _second_confirmation(m: Manifest8) -> None:
    wl = read_registry("WORKLOAD_LOCK") or {}
    rung8 = next((r for r in (wl.get("ladder") or []) if r.get("rung") == 8), None)
    if rung8 and rung8.get("n_mult") and "B01/x8" not in m.cells and verdict_path("B01").exists() and read_json(verdict_path("B01")).get("outcome") not in ("NOT_RUN",):
        m.add("B01/x8", "B01", ["B01"], str(verdict_path("B01/x8")), 40.0, True, "expansion rung 8: a second untouched confirmation lineage")
        log("ladder rung 8 admitted: B01/x8")


def run() -> int:
    contract = RunContract8.load()
    if contract is None or not contract.data.get("execution_start"):
        raise SystemExit("run: the pilot has not started the clock; run `pilot` first (§12.2)")
    m = Manifest8()
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
                from soundingline.stage8 import OUTCOMES7 as OC                   # noqa: PLC0415
                m.set_outcome(cell, v.get("outcome") if v.get("outcome") in OC or v.get("outcome") == "NOT_RUN" else "VOID", v.get("reason"))
            elif rc == 4:
                m.cells[cell]["attempts"] = max(0, m.cells[cell]["attempts"] - 1)
                m.set_exec(cell, "PLANNED", "endpoint starved; rows checkpointed; the lost units rerun")
                log(f"STARVED {cell} (cpu): a model arm lost more than a fifth of its rows to the endpoint; the lost units rerun")
            else:
                attempts = m.cells[cell]["attempts"]
                if attempts < MAX_ATTEMPTS:
                    m.set_exec(cell, "PLANNED", f"cpu exit {rc}; retry {attempts}")
                else:
                    m.set_exec(cell, "FAILED", f"cpu exit {rc}")
                    m.set_outcome(cell, "INSTRUMENT_FAILED")
                    if not vp.exists():
                        from soundingline.stage8 import write_json                 # noqa: PLC0415
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
            pending_i = [c for c in INTEGRITY_FIRST if m.cells[c]["exec_state"] in ("PLANNED", "RUNNING") and c[0] != "T"]
            if not pending_i and not running_cpu:
                locked = scientific_lock()
                if not locked:
                    _status(m, contract, running_cpu, f"integrity block landed; the scientific lock waits on {(read_registry('SCIENTIFIC_LOCK') or {}).get('missing_gates')} and the keystone")
                    if any(m.cells[c]["exec_state"] in ("FAILED", "BLOCKED") for c in INTEGRITY_FIRST if c[0] != "T")                             or all(m.cells[c]["exec_state"] not in ("PLANNED", "RUNNING") for c in INTEGRITY_FIRST if c[0] != "T"):
                        log("the integrity block is complete and a lock gate failed; the lock cannot open; closing for repair (stop, repair, reset, relaunch)")
                        break
                    time.sleep(60)
                    continue
        if elapsed >= CLOSURE_HOUR:
            _freeze_confirmations(m)
        allow_conf = bool(read_registry("CONFIRMATION_REGISTRY"))
        conf_done = allow_conf and all(m.cells[c]["exec_state"] not in ("PLANNED", "RUNNING") for c in CONF_CELLS + tuple(k for k in m.cells if k.startswith("B01/")))
        cap = _cpu_cap()
        for cell in _cpu_starts(m, running_cpu, cap, allow_conf, locked, allow_late=conf_done):
            m.set_exec(cell, "RUNNING")
            env = dict(os.environ)
            if "/" in cell:
                env["S7_CELL"] = cell
                env.update(_rung_env(cell))
            logf = open(S8 / f"{cell.replace('/', '_')}.log", "a", encoding="utf-8")
            proc = subprocess.Popen([PY, ENGINE, "--card", cell.split("/")[0]], cwd=str(REPO), env=env, stdout=logf, stderr=subprocess.STDOUT,
                                    creationflags=_child_flags())
            running_cpu[cell] = (proc, time.time(), logf)
            log(f"cpu start {cell} (cap {cap}, gear {gear()}, ghost {'live' if ghost_status().get('live') else 'quiet'})")
        cell = _next_gpu(m, allow_conf, locked)
        if cell is None and locked and not allow_conf:
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
            if any(m.cells[c]["exec_state"] == "PLANNED" for c in CONF_CELLS if c in m.cells):
                time.sleep(5)
                continue
            _second_confirmation(m)
            if any(m.cells[c]["exec_state"] == "PLANNED" for c in m.cells if c.startswith("B01/")):
                continue
            if any(m.cells[c]["exec_state"] == "PLANNED" for c in LATE_CELLS if c in m.cells):
                time.sleep(5)
                continue
            if contract.elapsed_h() < FLOOR_HOUR:
                write_registry("SHORT_RUN", {"written_at": now_iso(), "elapsed_h": round(contract.elapsed_h(), 2),
                                             "cause": "the admitted workload and the re-locked ladder exhausted before the 36-hour useful-work floor; nothing padded"})
                log(f"SHORT RUN at {contract.elapsed_h():.1f} h: the re-locked ladder is exhausted; honest cause written")
            break
        env = _rung_env(cell)
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
                               "gpu_lock_seconds": sum(float((v or {}).get("gpu_held_s") or 0.0) for v in (read_registry("COMPUTE_LEDGER") or {}).values() if isinstance(v, dict)),
                               "cells": m.state_counts()})
    return finalize_report()


def finalize_report() -> int:
    """Closed execution and successful packet validation are separate states."""
    from soundingline.stage8 import update_registry
    cov = validate(write=True)
    from runners.stage8 import report as REP                                      # noqa: PLC0415
    status = {"at": now_iso(), "execution_closed": True, "integrity_ok": cov.get("ok") is True,
              "integrity_reasons": cov.get("reasons", []), "packet_written": False, "packet_error": None,
              "validator_version": cov.get("validator_version"), "running_cpu": []}
    try:
        if cov.get("ok") is not True:
            raise REP.PacketRefused("final integrity failed; see COVERAGE reasons")
        p = REP.write_final_packet()
        status.update(packet_written=True, note="execution closed; final packet validated and written")
        log(f"final packet written: {p}")
    except Exception as e:                                                        # noqa: BLE001
        status.update(packet_error=str(e), note=f"execution closed; packet refused or failed: {e}")
        update_registry("SCHEDULER_STATUS", lambda previous: {**previous, **status})
        log(f"packet refused or failed: {e}")
        return 2
    update_registry("SCHEDULER_STATUS", lambda previous: {**previous, **status})
    return 0


def _status(m: Manifest8, contract: RunContract8, running_cpu: dict, note: str) -> None:
    g = ghost_status()
    write_registry("SCHEDULER_STATUS", {"at": now_iso(), "elapsed_h": round(contract.elapsed_h(), 2), "deadline": contract.data.get("deadline"),
                                        "counts": m.state_counts(), "running_cpu": list(running_cpu), "note": note,
                                        "ghost": {k: g.get(k) for k in ("live", "stage", "age_min", "program")},
                                        "frontier_usd": (read_registry("FRONTIER_LEDGER") or {}).get("total_usd"), "interrupts": [i["name"] for i in interrupts()]})


def _engine_alive() -> str | None:
    p = S8.parent / ".gear2.lock"
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
        raise SystemExit(f"reset: the engine is running (winpid {w}); stop it first")
    m = Manifest8()
    reps = read_registry("REPAIRS") or {}
    reps.setdefault("resets", [])
    for cell in cells:
        if cell not in m.cells:
            raise SystemExit(f"reset: unknown cell {cell}")
        d = S8 / cell
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
        c.update({"exec_state": "PLANNED", "outcome": "NOT_RUN", "attempts": 0, "reason": f"reset ({tag}): {why}; first attempt preserved under {sup.name}/"})
        c.setdefault("resets", []).append({"at": now_iso(), "tag": tag, "why": why, "before": before, "moved": moved})
        m.save()
        reps["resets"].append({"cell": cell, "tag": tag, "why": why, "at": now_iso(), "preserved": sup.name, "before": before})
        log(f"reset {cell} ({tag}): {why}; {len(moved)} files preserved")
    write_registry("REPAIRS", reps)
    return 0


def main() -> int:
    # the root guard (2026-09-04 18:16): a reset issued without S7_STAGE=phase_2_4_stage_8 resolved to the
    # closed Stage 7 root and moved four of its cells; every op refuses a root that is not this stage's
    if not os.environ.get("S7_ROOT") and S8.name != "phase_2_4_stage_8":
        raise SystemExit(f"stage8 scheduler: S8 root is {S8}; set S7_STAGE=phase_2_4_stage_8 (the wrapper does); refusing")
    ap = argparse.ArgumentParser()
    ap.add_argument("op", choices=["prepare", "pilot", "run", "lock", "freeze", "relock", "validate", "final-packet", "status", "reset"])
    ap.add_argument("--cells", nargs="*", default=[])
    ap.add_argument("--tag", default="repair")
    ap.add_argument("--why", default="")
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
    if a.op == "freeze":
        _freeze_confirmations(Manifest8())
        return 0
    if a.op == "relock":
        relock(RunContract8.load(), Manifest8())
        return 0
    if a.op == "validate":
        print(json.dumps({k: v for k, v in validate(write=True).items() if k != "cells"}, indent=1)[:3000])
        return 0
    if a.op == "final-packet":
        from runners.stage8 import report as REP                                  # noqa: PLC0415
        print(REP.write_final_packet())
        return 0
    if a.op == "status":
        p = S8 / "SCHEDULER_STATUS.json"
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
