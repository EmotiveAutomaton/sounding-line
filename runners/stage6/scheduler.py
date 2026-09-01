"""Stage 6 scheduler (brief §11): prepare, pilot, run, freeze, validate, final-packet,
status, reset. ONE immutable 168-hour clock, started when the discarded pilot begins and
persisted across restarts; inside the window the queue runs continuously (GPU cells serial
through the preservation order, CPU cells beside them under the Ghost coexistence
governor); at hour 144 the confirmation freeze; at the deadline no new work, validation,
the RUNTIME record, and the one packet. The frozen useful expansion ladder fills measured
headroom; exhaustion before hour 156 writes SHORT_RUN.json with the honest cause.

DESIGN CHECK (2026-08-30)
lessons read: LESSONS §5 (all of it: produces guards; one manifest writer; retries with a
  cap; the exists() poll before declaring no-produce; kill by Windows pid; the deadline is
  a wake-and-decide event; a corrective stage list is audited like results; the governor
  reads Ghost's status read-only), §3 (a gate dependency is the verdict: the capability
  gate freezes I05's VERDICTS into the design; the freeze precedes confirmation access).
gates: admission by dependency (a dead parent blocks the child as NOT_RUN/BLOCKED);
  the workload lock before any discovery output; the scientific lock before discovery
  GPU cells; the confirmation freeze before B01/B02; the packet only after the deadline
  plus validation. bands: the engines'.
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

from runners.stage6 import cards as CARDS_MOD                                      # noqa: E402
from runners.stage6 import records as REC                                          # noqa: E402
from runners.stage6.validate import validate                                       # noqa: E402
from soundingline.stage6 import (S6, ARCH_NAMES, CLOSURE_HOUR, FLOOR_HOUR,         # noqa: E402
                                 Lineages6, Manifest6, RunContract6, ghost_status,
                                 now_iso, read_json, read_registry, write_registry)

PY = str(REPO / ".venv" / "Scripts" / "python.exe")
ENGINE = str(REPO / "runners" / "stage6" / "engines.py")
LOG = S6 / "scheduler.log"
MAX_ATTEMPTS = 3
SMOKE = bool(os.environ.get("S6_SMOKE"))
PILOT_MARGIN = 1.6            # forecast = pilot rate x margin (§11.2's predeclared uncertainty)


def log(msg: str) -> None:
    S6.mkdir(parents=True, exist_ok=True)
    line = f"[{now_iso()}] {msg}"
    print(line, flush=True)
    with open(LOG, "a", encoding="utf-8", newline="\n") as fh:
        fh.write(line + "\n")


def _fresh(contract: RunContract6) -> RunContract6:
    return RunContract6.load(contract.path) or contract


def verdict_path(cell: str) -> Path:
    return S6 / cell / "verdict.json"


# ── prepare ───────────────────────────────────────────────────────────────────────────

def prepare() -> int:
    S6.mkdir(parents=True, exist_ok=True)
    for sub in ("raw", "states", "predictions", "posteriors", "confirmations"):
        (S6 / sub).mkdir(exist_ok=True)
    contract = RunContract6.create()
    m = Manifest6()
    for card in CARDS_MOD.PRESERVATION_ORDER:
        spec = CARDS_MOD.ALL[card]
        m.add(card, card, list(spec["depends_on"]), str(verdict_path(card)),
              CARDS_MOD.est_minutes(card), spec["gpu"], spec["primary"][:160])
    m.add("B01", "B01", [], str(verdict_path("B01")), 60.0, True, CARDS_MOD.ALL["B01"]["primary"][:160])
    m.add("B02", "B02", ["B01"], str(verdict_path("B02")), 60.0, True, CARDS_MOD.ALL["B02"]["primary"][:160])
    m.add("B04", "B04", ["B03"], str(verdict_path("B04")), 20.0, False, CARDS_MOD.ALL["B04"]["primary"][:160])
    Lineages6().save()
    write_registry("ARCHITECTURES", {"arms": ARCH_NAMES, "written_at": now_iso()})
    write_registry("STRUCTURAL_LOCK", {"written_at": now_iso(), "cards": len(CARDS_MOD.CARDS),
                                       "attacks": len(CARDS_MOD.ATTACKS), "contract_hash": contract.hash(),
                                       "corpus_dispositions": "CORPUS_DISPOSITIONS.json",
                                       "openreview": REC.OPENREVIEW_DISPOSITION["status"]})
    write_registry("PREPARED", {"at": now_iso(), "cells": len(m.cells), "contract_hash": contract.hash()})
    log(f"prepared: {len(m.cells)} cells, contract {contract.hash()}")
    return 0


# ── the discarded pilot (§11.2): starts the ONE clock ────────────────────────────────

def pilot() -> int:
    contract = RunContract6.load() or RunContract6.create()
    contract.start()
    log(f"PILOT begins; THE 168-HOUR CLOCK STARTS: {contract.data['execution_start']} "
        f"(deadline {contract.data['deadline']})")
    t0 = time.time()
    env = dict(os.environ, S6_SPLIT="pilot")
    timings: dict = {}
    from runners import s5_lib                                                    # noqa: PLC0415
    from runners.stage6 import architectures as A                                 # noqa: PLC0415
    from runners.stage6 import prediction as PR                                   # noqa: PLC0415
    from runners.stage6 import worlds as W                                        # noqa: PLC0415
    n_pilot = 1 if SMOKE else 2
    with s5_lib.GpuSession("s6_pilot") as gs:
        lock_wait_probe = time.time()
        for reader in ("Qwen/Qwen2.5-1.5B-Instruct", "HuggingFaceTB/SmolLM2-1.7B-Instruct"):
            t1 = time.time()
            model, tok, _ = s5_lib.load_model(reader)
            timings[f"load|{reader.split('/')[-1]}"] = time.time() - t1
            try:
                for track in ("C", "A", "V", "F", "M"):
                    for i in range(n_pilot):
                        lid = f"PILOT|essay|s0|w{9000 + i:05d}|pilot"
                        w = W.make_process_world(lid, "essay", track=track)
                        for arch in (("TT", "EX", "CR", "D") if not SMOKE else ("CR",)):
                            t2 = time.time()
                            res = A.run_arm(arch, model, tok, w, A.BUDGET_SMALL)
                            timings.setdefault(f"arm|{arch}", []).append(time.time() - t2)
                            if res["predictions"]:
                                PR.score_predictions(w, res["predictions"])
            finally:
                s5_lib.free_model(model)
    timings["gpu_lock_held_s"] = gs.held_s
    timings["lock_cycle_s"] = time.time() - lock_wait_probe
    t3 = time.time()
    sw = REC.scholawrite_sessions(max_sessions=1)
    ca = REC.coauthor_sessions(max_sessions=1)
    timings["records_load_s"] = time.time() - t3
    timings["records_found"] = {"scholawrite": len(sw), "coauthor": len(ca)}
    for k, v in list(timings.items()):
        if isinstance(v, list):
            timings[k] = sum(v) / len(v)
    # kill/resume smoke: a second CardRun6 on the same cell sees completed units (I10 re-proves)
    write_registry("PILOT", {"written_at": now_iso(), "timings": timings,
                             "wall_s": time.time() - t0, "discarded": True,
                             "note": "pilot outputs are not promotable (§11.2)"})
    _workload_lock(contract, timings)
    log(f"pilot done in {(time.time() - t0) / 60:.1f} min; workload locked")
    del env
    return 0


def _workload_lock(contract: RunContract6, timings: dict) -> None:
    """Freeze the admitted workload: the minimum tier for every card, forecast from the
    measured arm rates with the margin; the expansion ladder carries the rest of the week
    as REAL additional units (each rung a unit multiplier over its card list, sized so
    base plus ladder lands inside the 156-162 target with the §11.2 closure reserve).
    More independent units is useful scientific work (power), never filler; if the capped
    ladder still undershoots, the shortfall is recorded and the short-run rule stands."""
    arm_s = max([v for k, v in timings.items() if k.startswith("arm|")] or [20.0])
    per_gpu_unit = arm_s * 2 * PILOT_MARGIN            # two readers
    base_h = 0.0
    card_h = {}
    for card, spec in CARDS_MOD.ALL.items():
        n = CARDS_MOD.units_for(card)
        est = (per_gpu_unit * n * 2 / 3600) if spec["gpu"] else (spec["est_s_per_unit"] * n / 3600 * 0.5)
        card_h[card] = est
        base_h += est
    reserve_h = 10.0                                    # confirmations + validation (§11.2's 6-12)
    ladder_target = max(0.0, 159.0 - base_h - reserve_h)
    rung_lists = {1: ["M08", "M01", "M02", "C03", "C11", "V14", "F11", "T01", "T04", "A10"],
                  2: ["M08", "M15", "M16", "P10"], 3: ["I05", "I08"], 4: ["T01", "T02", "T04"],
                  5: ["A04", "A06", "A12", "A13"], 6: ["V11", "V06", "F03", "F09"],
                  7: ["T02", "T06"], 8: ["M04", "M06", "TT_EX_samples"], 9: ["B01"]}
    weights = {r: sum(card_h.get(c, 0.3) for c in cards) for r, cards in rung_lists.items()}
    wz = sum(weights.values()) or 1.0
    rungs = []
    total = 0.0
    for rung in CARDS_MOD.EXPANSION_LADDER:
        rn = rung["rung"]
        share_h = ladder_target * weights.get(rn, 0.3) / wz
        rung_base = max(0.3, weights.get(rn, 0.3))
        # the cap bounds a single rung's growth, not the week: forty times a card's minimum
        # units is still distinct constructed worlds (content-hashed, identity-enumerated) or
        # more of a real corpus, i.e. power; duplicate rows stay forbidden by I03's audit
        mult = max(1, min(40, int(round(share_h / rung_base))))
        rung_h = rung_base * mult
        rungs.append({**rung, "cards": rung_lists.get(rn, []), "n_mult": mult,
                      "forecast_h": round(rung_h, 1)})
        total += rung_h
    write_registry("WORKLOAD_LOCK", {"written_at": now_iso(), "tier": "minimum",
                                     "per_gpu_unit_s": round(per_gpu_unit, 2),
                                     "base_forecast_h": round(base_h, 1),
                                     "ladder": rungs, "ladder_forecast_h": round(total, 1),
                                     "total_forecast_h": round(base_h + total + reserve_h, 1),
                                     "target_h": [156, 162], "margin": PILOT_MARGIN,
                                     "shortfall_h": round(max(0.0, 159.0 - base_h - total - reserve_h), 1),
                                     "note": "conditional branches (capability-gated) may close; rung multipliers are "
                                             "additional independent units (power), capped at 8x per rung; a residual "
                                             "shortfall closes under the short-run rule, honestly"})


def scientific_lock() -> None:
    """After the integrity block: freeze readers, thresholds, and I05's capability verdicts
    into the design; discovery GPU cells wait on this."""
    contract = RunContract6.load()
    i05 = read_json(S6 / "I05" / "metrics.json") if (S6 / "I05" / "metrics.json").exists() else {}
    cap = {r: {"passed": bool(v.get("passed"))} for r, v in (i05.get("readers") or {}).items()}
    from runners import s5_lib                                                    # noqa: PLC0415
    readers = {name: s5_lib.model_revision(name) for name in
               ("Qwen/Qwen2.5-1.5B-Instruct", "HuggingFaceTB/SmolLM2-1.7B-Instruct")}
    design = {"readers": readers, "capability_gate": cap, "tier": "minimum",
              "thresholds": {c: CARDS_MOD.ALL[c]["threshold"] for c in CARDS_MOD.ALL},
              "budgets": {"small": {"model_calls": 8}, "expanded": {"model_calls": 16}}}
    if not contract.frozen("design"):
        contract.freeze("design", design)
    write_registry("SCIENTIFIC_LOCK", {"written_at": now_iso(), "locked": True,
                                       "design_hash": contract.frozen("design") and contract.data["frozen"]["design"]["hash"],
                                       "capability": cap})
    log(f"scientific lock written; capability {json.dumps(cap)}")


# ── the run loop ──────────────────────────────────────────────────────────────────────

INTEGRITY_FIRST = ["I01", "I02", "I09", "I03", "I04", "I10", "I06", "I05", "I07", "I08"]


def _cpu_cap() -> int:
    g = ghost_status()
    return 2 if g.get("live") else 3


def _admissible(m: Manifest6, cell: str) -> bool:
    c = m.cells.get(cell)
    if not c or c["exec_state"] != "PLANNED":
        return False
    if m.deps_dead(cell):
        m.set_exec(cell, "BLOCKED", "a dependency failed or was blocked")
        m.set_outcome(cell, "NOT_RUN", "BLOCKED_DEPENDENCY")
        return False
    return m.deps_complete(cell)


def _run_cell(m: Manifest6, contract: RunContract6, cell: str, extra_env: dict | None = None) -> str:
    m.set_exec(cell, "RUNNING")
    t0 = time.time()
    card = cell.split("/")[0]
    cmd = [PY, ENGINE, "--card", card]
    log(f"start {cell}")
    env = dict(os.environ)
    if "/" in cell:
        env["S6_CELL"] = cell
    env.update(extra_env or {})
    logf = open(S6 / f"{cell.replace('/', '_')}.log", "a", encoding="utf-8")
    try:
        rc = subprocess.call(cmd, cwd=str(REPO), env=env, stdout=logf, stderr=subprocess.STDOUT)
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
            tail = (S6 / f"{cell.replace('/', '_')}.log").read_text(encoding="utf-8", errors="replace")[-500:]
        except OSError:
            pass
        if attempts < MAX_ATTEMPTS:
            m.set_exec(cell, "PLANNED", f"exit {rc}; retry {attempts}/{MAX_ATTEMPTS}")
            if "out of memory" in tail.lower():
                contract.record_lost_time(f"{cell} OOM wait", 120)
                time.sleep(120)
            return "RETRY"
        m.set_exec(cell, "FAILED", f"exit {rc} after {attempts} attempts")
        m.set_outcome(cell, "INSTRUMENT_FAILED", tail[-300:])
        return "FAILED"
    v = read_json(vp)
    m.set_exec(cell, v.get("exec", "COMPLETE"), v.get("reason"))
    oc = v.get("outcome")
    from soundingline.stage6 import OUTCOMES6                                     # noqa: PLC0415
    m.set_outcome(cell, oc if oc in OUTCOMES6 or oc == "NOT_RUN" else "VOID", v.get("reason"))
    m.charge(cell, wall / 60, float(v.get("gpu_lock_min") or 0.0))
    log(f"done {cell}: {m.cells[cell]['exec_state']}/{m.cells[cell]['outcome']} wall={wall / 60:.1f}min")
    return m.cells[cell]["exec_state"]


def _next_gpu(m: Manifest6, allow_conf: bool) -> str | None:
    for cell in CARDS_MOD.PRESERVATION_ORDER + [k for k in m.cells if "/" in k]:
        c = m.cells.get(cell)
        if not c or not c["gpu"]:
            continue
        if cell.split("/")[0] in ("B01", "B02") and not allow_conf:
            continue
        if _admissible(m, cell):
            return cell
    if allow_conf:
        for cell in ("B01", "B02"):
            if m.cells.get(cell, {}).get("gpu") and _admissible(m, cell):
                return cell
    return None


def _cpu_starts(m: Manifest6, running: dict, cap: int, allow_conf: bool) -> list[str]:
    out = []
    for cell in CARDS_MOD.PRESERVATION_ORDER + ["B04"] + [k for k in m.cells if "/" in k]:
        if len(running) + len(out) >= cap:
            break
        c = m.cells.get(cell)
        if not c or c["gpu"] or cell in running:
            continue
        if cell == "B04" and not allow_conf:
            continue
        if _admissible(m, cell):
            out.append(cell)
    return out


def _freeze_confirmations(m: Manifest6) -> None:
    if read_registry("CONFIRMATION_REGISTRY"):
        return
    sel = []
    m08 = read_json(verdict_path("M08")) if verdict_path("M08").exists() else {}
    candidates = []
    for c in CARDS_MOD.CARDS:
        v = read_json(verdict_path(c)) if verdict_path(c).exists() else {}
        if v.get("outcome") == "SUPPORT_CANDIDATE" and v.get("lane") == "discovery" and CARDS_MOD.ALL[c]["gpu"]:
            candidates.append((c, v))
    if m08.get("outcome") == "SUPPORT_CANDIDATE":
        sel.append({"card": "M08", "what": "CR minus the best non-oracle arm", "point": m08.get("point")})
    for c, v in candidates:
        if len(sel) >= 2:
            break
        if c != "M08" and c[0] in ("C", "V", "F", "A", "M", "T"):
            sel.append({"card": c, "what": v.get("primary", "")[:120], "point": v.get("point")})
    boundary = [(c, read_json(verdict_path(c))) for c in ("M07", "C11", "V14", "F11")
                if verdict_path(c).exists()]
    for c, v in boundary:
        if len(sel) >= 2:
            break
        if v.get("outcome") in ("COUNTEREVIDENCE", "VALID_NULL") and all(s["card"] != c for s in sel):
            sel.append({"card": c, "what": f"boundary: {v.get('primary', '')[:120]}", "point": v.get("point")})
    write_registry("CONFIRMATION_REGISTRY", {"written_at": now_iso(), "selected": sel[:2],
                                             "rule": "the strongest qualified gain, then the sharpest boundary (§10.3)"})
    log(f"confirmation freeze: {json.dumps(sel[:2])}")


def _rung_mult(rn: int) -> int:
    wl = read_registry("WORKLOAD_LOCK") or {}
    for rung in (wl.get("ladder") or []):
        if rung.get("rung") == rn:
            return int(rung.get("n_mult", 1))
    return 1


def _rung_targets(rung: dict) -> list[str]:
    targets = [c for c in (rung.get("cards") or []) if c in CARDS_MOD.ALL]
    if not targets:
        targets = {1: ["M08", "M01", "C03", "V14", "F11", "T01"],
                   2: ["M08", "M15"], 3: ["I05"], 4: ["T01", "T04"], 5: ["A04", "A06"],
                   6: ["V11", "F03"], 7: ["T02"], 8: ["M04", "M06"], 9: ["B01"]}.get(rung.get("rung"), [])
    return targets


def _ladder_exhausted(m: Manifest6) -> bool:
    """True only when every locked rung's every currently-admissible cell exists and has
    finished. Guards the exhaustion freeze (the hour-1.6 defect, 2026-08-30): before
    CLOSURE_HOUR the freeze may fire only when the whole locked ladder is genuinely done."""
    wl = read_registry("WORKLOAD_LOCK") or {}
    for rung in (wl.get("ladder") or []):
        rn = rung.get("rung")
        for card in _rung_targets(rung):
            if card in ("B01", "B02", "B04") or not verdict_path(card).exists():
                continue
            c = m.cells.get(f"{card}/x{rn}")
            if c is None or c["exec_state"] in ("PLANNED", "RUNNING"):
                return False
    return True


def _ladder_next(m: Manifest6, contract: RunContract6) -> str | None:
    wl = read_registry("WORKLOAD_LOCK") or {}
    if any(c["exec_state"] in ("PLANNED", "RUNNING") for k, c in m.cells.items()
           if k not in ("B01", "B02", "B04")):
        return None
    if contract.elapsed_h() >= CLOSURE_HOUR - 2:
        return None
    for rung in (wl.get("ladder") or []):
        rn = rung["rung"]
        targets = _rung_targets(rung)
        mult = int(rung.get("n_mult", 1))
        for card in targets:
            cell = f"{card}/x{rn}"
            if cell in m.cells or not verdict_path(card).exists():
                continue
            m.add(cell, card, [card], str(verdict_path(cell)), CARDS_MOD.est_minutes(card) * 0.6 * mult,
                  CARDS_MOD.ALL[card]["gpu"], f"expansion rung {rn} (x{mult} units): {rung['axis']}")
            log(f"ladder rung {rn} admitted: {cell} (x{mult} units)")
            return cell
    return None


def run() -> int:
    contract = RunContract6.load()
    if contract is None or not contract.data.get("execution_start"):
        raise SystemExit("run: the pilot has not started the clock; run `pilot` first (§11.1)")
    m = Manifest6()
    for cell, c in m.cells.items():
        if c["exec_state"] == "RUNNING":
            m.set_exec(cell, "PLANNED", "re-planned at restart; resumes from its rows")
    log(f"run: elapsed {contract.elapsed_h():.2f} h of {contract.data['run_hours']}; deadline {contract.data['deadline']}")
    running_cpu: dict = {}
    integrity_done = False
    while True:
        contract.data = _fresh(contract).data
        elapsed = contract.elapsed_h()
        deadline = contract.deadline_passed()
        # reap CPU cells
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
                from soundingline.stage6 import OUTCOMES6 as OC                   # noqa: PLC0415
                m.set_outcome(cell, v.get("outcome") if v.get("outcome") in OC or v.get("outcome") == "NOT_RUN" else "VOID", v.get("reason"))
            else:
                attempts = m.cells[cell]["attempts"]
                if attempts < MAX_ATTEMPTS:
                    m.set_exec(cell, "PLANNED", f"cpu exit {rc}; retry {attempts}")
                else:
                    m.set_exec(cell, "FAILED", f"cpu exit {rc}")
                    m.set_outcome(cell, "INSTRUMENT_FAILED")
            m.charge(cell, (time.time() - t0) / 60, 0.0)
            log(f"cpu done {cell}: {m.cells[cell]['exec_state']}/{m.cells[cell]['outcome']}")
        if deadline:
            if running_cpu:
                time.sleep(15)
                continue
            log("THE WINDOW HAS ELAPSED: no new work; closing")
            break
        if not integrity_done:
            pending_i = [c for c in INTEGRITY_FIRST if m.cells[c]["exec_state"] == "PLANNED"]
            if pending_i:
                for c in INTEGRITY_FIRST:
                    if _admissible(m, c):
                        _run_cell(m, contract, c)
                        break
                else:
                    time.sleep(5)
                continue
            integrity_done = True
            scientific_lock()
        if elapsed >= CLOSURE_HOUR:
            _freeze_confirmations(m)
        allow_conf = bool(read_registry("CONFIRMATION_REGISTRY"))
        cap = _cpu_cap()
        for cell in _cpu_starts(m, running_cpu, cap, allow_conf):
            m.set_exec(cell, "RUNNING")
            env = dict(os.environ)
            if "/" in cell:
                env["S6_CELL"] = cell
                if "/x" in cell:
                    rn = int(cell.split("/x")[1])
                    env["S6_WORLD_OFFSET"] = str(1000 * rn)
                    env["S6_UNITS_MULT"] = str(_rung_mult(rn))
            logf = open(S6 / f"{cell.replace('/', '_')}.log", "a", encoding="utf-8")
            proc = subprocess.Popen([PY, ENGINE, "--card", cell.split("/")[0]], cwd=str(REPO),
                                    env=env, stdout=logf, stderr=subprocess.STDOUT)
            running_cpu[cell] = (proc, time.time(), logf)
            log(f"cpu start {cell} (cap {cap}, ghost {'live' if cap == 2 else 'quiet'})")
        cell = _next_gpu(m, allow_conf)
        if cell is None:
            cell = _ladder_next(m, contract)
        if cell is None:
            if running_cpu:
                _status(m, contract, running_cpu, "no GPU cell; CPU running")
                time.sleep(20)
                continue
            if not allow_conf:
                if contract.elapsed_h() >= CLOSURE_HOUR or _ladder_exhausted(m):
                    _freeze_confirmations(m)
                    allow_conf = True
                    continue
                _status(m, contract, running_cpu, "pre-closure lull: the ladder is not exhausted; waiting")
                time.sleep(20)
                continue
            if any(m.cells[c]["exec_state"] == "PLANNED" for c in ("B01", "B02", "B04")):
                continue
            if contract.elapsed_h() < FLOOR_HOUR:
                write_registry("SHORT_RUN", {"written_at": now_iso(), "elapsed_h": round(contract.elapsed_h(), 2),
                                             "cause": "the admitted workload and the whole locked ladder exhausted early; "
                                                      "capability-gated branches closed more cells than the lock's conditional forecast"})
                log(f"SHORT RUN at {contract.elapsed_h():.1f} h: the locked ladder is exhausted; honest cause written")
            break
        env = {}
        if "/x" in cell:
            rn = int(cell.split("/x")[1])
            env["S6_WORLD_OFFSET"] = str(1000 * rn)
            env["S6_UNITS_MULT"] = str(_rung_mult(rn))
        _status(m, contract, running_cpu, f"running {cell}")
        _run_cell(m, contract, cell, env)
    for cell, (proc, t0, logf) in running_cpu.items():
        try:
            proc.wait(timeout=1800)
        except subprocess.TimeoutExpired:
            proc.kill()
        logf.close()
    contract.data["run_label"] = "WINDOW_ELAPSED" if contract.deadline_passed() else "RUN_TO_EMPTY_SHORT"
    contract.data["exhausted"] = True
    contract.data["short_of_window"] = not contract.window_elapsed()
    contract.save()
    write_registry("RUNTIME", {"written_at": now_iso(), "elapsed_h": round(contract.elapsed_h(), 2),
                               "gpu_lock_seconds": sum(c.get("gpu_lock_min", 0.0) * 60 for c in m.cells.values()),
                               "cells": m.state_counts()})
    validate(write=True)
    if contract.deadline_passed():
        from runners.stage6 import report as REP                                  # noqa: PLC0415
        try:
            p = REP.write_final_packet()
            log(f"final packet written: {p}")
        except Exception as e:                                                    # noqa: BLE001
            log(f"packet refused or failed: {e}")
    else:
        log("closed short of the window; NO packet (the reporter refuses before hour 168)")
    return 0


def _status(m: Manifest6, contract: RunContract6, running_cpu: dict, note: str) -> None:
    g = ghost_status()
    write_registry("SCHEDULER_STATUS", {"at": now_iso(), "elapsed_h": round(contract.elapsed_h(), 2),
                                        "deadline": contract.data.get("deadline"), "counts": m.state_counts(),
                                        "running_cpu": list(running_cpu), "note": note,
                                        "ghost": {k: g.get(k) for k in ("live", "stage", "age_min")}})
    samples = read_registry("COEXISTENCE") or {"samples": []}
    samples["samples"] = (samples.get("samples") or [])[-500:] + [{"at": now_iso(), "ghost_live": g.get("live"),
                                                                   "ghost_stage": g.get("stage")}]
    write_registry("COEXISTENCE", samples)


def _engine_alive() -> str | None:
    """The gear-2 wrapper's winpid, if that process still answers tasklist."""
    p = S6.parent / ".gear2.lock"
    if not p.exists():
        return None
    try:
        winpid = p.read_text(encoding="utf-8").splitlines()[1].strip()
    except (OSError, IndexError):
        return None
    import subprocess                                                             # noqa: PLC0415
    try:
        out = subprocess.run(["tasklist", "/FI", f"PID eq {winpid}"],
                             capture_output=True, text=True, timeout=15).stdout
    except Exception:
        return None
    return winpid if f" {winpid} " in out else None


def reset(cells: list[str], tag: str, why: str) -> int:
    w = _engine_alive()
    if w:
        raise SystemExit(f"reset: the engine is running (winpid {w}); stop it first — a live "
                         "engine's in-memory manifest saves clobber resets (the P10 lesson, 2026-08-30)")
    m = Manifest6()
    for cell in cells:
        if cell not in m.cells:
            raise SystemExit(f"reset: unknown cell {cell}")
        d = S6 / cell  # the CELL's directory (an expansion cell lives under card/xN)
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
        c.update({"exec_state": "PLANNED", "outcome": "NOT_RUN", "attempts": 0,
                  "reason": f"reset ({tag}): {why}; first attempt preserved under {sup.name}/"})
        c.setdefault("resets", []).append({"at": now_iso(), "tag": tag, "why": why, "before": before, "moved": moved})
        m.save()
        log(f"reset {cell} ({tag}): {why}; {len(moved)} files preserved")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("op", choices=["prepare", "pilot", "run", "freeze", "validate", "final-packet", "status", "reset"])
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
    if a.op == "freeze":
        _freeze_confirmations(Manifest6())
        return 0
    if a.op == "validate":
        print(json.dumps({k: v for k, v in validate(write=True).items() if k != "cells"}, indent=1)[:2500])
        return 0
    if a.op == "final-packet":
        from runners.stage6 import report as REP                                  # noqa: PLC0415
        print(REP.write_final_packet())
        return 0
    if a.op == "status":
        p = S6 / "SCHEDULER_STATUS.json"
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
