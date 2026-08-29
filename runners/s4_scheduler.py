"""Stage 4 scheduler (brief §5, §9.4): prepare, calibrate, run, validate, final-packet.

One continuous window. The deadline is written once when the discarded pilot begins and
survives restarts; the loop admits work by dependency and preservation order, runs GPU
cells one at a time through the card runners (which take the GPU lock themselves) and up
to two CPU cells beside them, records elapsed and lock-held time apart, begins the
confirmation-and-closure block at hour 20, walks the predeclared expansion ladder while
the window has room, stops admitting at the deadline, validates coverage, and writes the
single final packet. Routine card failure sends the loop to other admitted work; a CUDA
out-of-memory is retried after a pause. No interim packets exist; a status file for
internal use is rewritten every loop.
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

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from runners import s4_cards                                                      # noqa: E402
from soundingline.s4 import (S4, ClaimLedger, Lineages, Manifest, RunContract,    # noqa: E402
                             coverage, now_iso, packet_allowed, read_json, read_jsonl,
                             write_json, write_packet)

PY = str(REPO / ".venv" / "Scripts" / "python.exe")
RUNNER_OF = {"I": "s4_run_i.py", "C": "s4_run_c.py", "A": "s4_run_a.py", "T": "s4_run_t.py",
             "H": "s4_run_h.py", "P": "s4_run_p.py", "F": "s4_run_f.py"}
LOG = S4 / "scheduler.log"
STATUS = S4 / "SCHEDULER_STATUS.json"
MAX_ATTEMPTS = 3
SMOKE = bool(os.environ.get("S4_SMOKE"))       # scratch-root smoke: the ladder shrinks too


def log(msg: str) -> None:
    S4.mkdir(parents=True, exist_ok=True)
    line = f"[{now_iso()}] {msg}"
    print(line, flush=True)
    with open(LOG, "a", encoding="utf-8", newline="\n") as fh:
        fh.write(line + "\n")


def runner_cmd(cell: str) -> list[str]:
    card = cell.split("/")[0]
    key = "I" if card.startswith("I") else card[0]
    return [PY, str(REPO / "runners" / RUNNER_OF[key]), "--card", card]


def verdict_path(cell: str) -> Path:
    if cell.endswith("/expand"):
        return S4 / cell.split("/")[0] / "verdict.json"
    return S4 / cell / "verdict.json"


# ── prepare ───────────────────────────────────────────────────────────────────────────

def prepare() -> int:
    S4.mkdir(parents=True, exist_ok=True)
    contract = RunContract.create()
    m = Manifest()
    for card, c in s4_cards.CARDS.items():
        deps = list(c["depends_on"])
        m.add(card, card if card != "I03pilot" else "I03", deps, str(S4 / card / "verdict.json"),
              c["est_s_per_unit"] * s4_cards.units_for(card, "minimum") / 60, c["gpu"], c["primary"])
    Lineages().save()
    write_json(S4 / "PREPARED.json", {"at": now_iso(), "contract_hash": contract.hash(),
                                      "cells": len(m.cells)})
    log(f"prepared: {len(m.cells)} cells, contract {contract.hash()}")
    return 0


# ── reset ─────────────────────────────────────────────────────────────────────────────

def reset(cells: list[str], tag: str, why: str, root: Path | None = None) -> int:
    """Re-plan cells whose landed output is superseded by a construction repair (the
    T-track lesson pool, TODO R7, 2026-08-28): the first attempt is PRESERVED under
    <card>/superseded_<tag>/ (rows, raw outputs, metrics, verdict, log, a note), the
    manifest cell returns to PLANNED / NOT_RUN with the reset recorded on it, and the
    card's expansion cell (if any) is dropped because it resumed rows that are gone.
    Never used on a running loop: stop the gear first."""
    root = root or S4
    m = Manifest(root / "QUEUE_MANIFEST.json")
    for cell in cells:
        if cell not in m.cells:
            raise SystemExit(f"reset: unknown cell {cell}")
        card = cell.split("/")[0]
        d = root / card
        sup = d / f"superseded_{tag}"
        sup.mkdir(parents=True, exist_ok=True)
        moved = []
        for p in sorted(d.iterdir()) if d.exists() else []:
            if p.is_dir() and p.name.startswith("superseded_"):
                continue
            shutil.move(str(p), str(sup / p.name))
            moved.append(p.name)
        logp = root / f"{cell.replace('/', '_')}.log"
        if logp.exists():
            shutil.move(str(logp), str(sup / logp.name))
            moved.append(logp.name)
        c = m.cells[cell]
        before = {k: c.get(k) for k in ("exec_state", "outcome", "attempts", "budget_charged_min",
                                         "gpu_lock_min", "started_at", "finished_at")}
        c.update({"exec_state": "PLANNED", "outcome": "NOT_RUN", "attempts": 0,
                  "started_at": None, "finished_at": None, "detail": None,
                  "reason": f"reset ({tag}): {why}; first attempt preserved under {sup.name}/"})
        c.setdefault("resets", []).append({"at": now_iso(), "tag": tag, "why": why,
                                            "before": before, "moved": moved})
        dropped = m.cells.pop(f"{card}/expand", None)
        m.save()
        write_json(sup / "RESET_NOTE.json", {"cell": cell, "tag": tag, "why": why, "at": now_iso(),
                                             "before": before, "moved": moved,
                                             "expansion_cell_dropped": dropped is not None})
        line = (f"reset {cell} ({tag}): {why}; {len(moved)} files preserved under {sup.name}/"
                + ("; expansion cell dropped" if dropped else ""))
        if root == S4:
            log(line)
        else:                       # a scratch root (the guard test) never writes the live log
            with open(root / "scheduler.log", "a", encoding="utf-8", newline="\n") as fh:
                fh.write(f"[{now_iso()}] {line}\n")
    return 0


# ── run ───────────────────────────────────────────────────────────────────────────────

def _fresh(contract: RunContract) -> RunContract:
    """The contract as it is ON DISK. Card subprocesses write it (the freeze writes the
    design, F01 the confirmations); a loop holding the object it loaded at start-up
    reads an empty design for the whole run and, on its first lost-time record, saves
    that stale object back over the frozen design (the loop smoke: deferred cards ran,
    no expansion rung was ever admitted). Timing fields are already persisted, so a
    reload loses nothing the loop set."""
    return RunContract.load(contract.path) or contract


def _run_cell(m: Manifest, contract: RunContract, cell: str, env_extra: dict | None = None) -> str:
    """Run one cell as a subprocess; returns the resulting exec state."""
    m.set_exec(cell, "RUNNING")
    t0 = time.time()
    env = dict(os.environ, **(env_extra or {}))
    cmd = runner_cmd(cell)
    log(f"start {cell}: {' '.join(cmd[2:])}")
    logf = open(S4 / f"{cell.replace('/', '_')}.log", "a", encoding="utf-8")
    try:
        rc = subprocess.call(cmd, cwd=str(REPO), env=env, stdout=logf, stderr=subprocess.STDOUT)
    finally:
        logf.close()
    wall = time.time() - t0
    contract.data = _fresh(contract).data          # the subprocess may have frozen a section
    vp = verdict_path(cell)
    # a clean exit without a produce is a failure (LESSONS §5); poll briefly for visibility;
    # an expansion cell reuses its card's verdict path, so the produce must be NEWER than
    # the cell's start or the old discovery verdict would pass as the expansion's
    produced = False
    for _ in range(10):
        if vp.exists() and (not cell.endswith("/expand") or vp.stat().st_mtime >= t0 - 1):
            produced = True
            break
        time.sleep(1)
    if rc == 3:
        m.set_exec(cell, "DEFERRED", "deadline reached mid-card; rows checkpointed")
        return "DEFERRED"
    if rc != 0 or not produced:
        tail = ""
        try:
            tail = (S4 / f"{cell.replace('/', '_')}.log").read_text(encoding="utf-8", errors="replace")[-600:]
        except OSError:
            pass
        oom = "out of memory" in tail.lower()
        attempts = m.cells[cell]["attempts"]
        if attempts < MAX_ATTEMPTS:
            m.set_exec(cell, "PLANNED", f"exit {rc}{' (OOM)' if oom else ''}; retry {attempts}/{MAX_ATTEMPTS}")
            if oom:
                contract.record_lost_time(f"{cell} OOM wait", 120)
                time.sleep(120)
            return "RETRY"
        m.set_exec(cell, "FAILED", f"exit {rc} after {attempts} attempts")
        m.set_outcome(cell, "INSTRUMENT_FAILED", tail[-300:])
        return "FAILED"
    v = read_json(vp)
    m.set_exec(cell, "COMPLETE" if v.get("exec", "COMPLETE") == "COMPLETE" else v.get("exec", "COMPLETE"),
               v.get("reason"))
    m.set_outcome(cell, v.get("outcome", "VOID") if v.get("outcome") in
                  ("SUPPORT_CANDIDATE", "COUNTEREVIDENCE", "VALID_NULL", "INCONCLUSIVE", "HETEROGENEOUS",
                   "INSTRUMENT_FAILED", "VOID", "NOT_RUN") else "VOID", v.get("reason"))
    gpu_min = float(v.get("gpu_lock_min") or 0.0)
    m.charge(cell, wall / 60, gpu_min)
    if m.cells[cell]["gpu"] and gpu_min > 0 and wall / 60 - gpu_min > 5:
        contract.record_lost_time(f"{cell} wall minus lock", (wall / 60 - gpu_min) * 60)
    log(f"done {cell}: exec={m.cells[cell]['exec_state']} outcome={m.cells[cell]['outcome']} "
        f"wall={wall / 60:.1f}min gpu_lock={gpu_min:.1f}min")
    return m.cells[cell]["exec_state"]


def _status(m: Manifest, contract: RunContract, running_cpu: dict, note: str = "") -> None:
    write_json(STATUS, {"at": now_iso(), "elapsed_h": round(contract.elapsed_h(), 3),
                        "remaining_h": round(contract.remaining_h(), 3),
                        "deadline": contract.data.get("deadline"), "counts": m.state_counts(),
                        "running_cpu": list(running_cpu), "note": note,
                        "gpu_lock_hours_total": round(m.total_gpu_lock_seconds() / 3600, 3)})


def _next_gpu_cell(m: Manifest, design: dict) -> str | None:
    deferred = set(design.get("deferred", []))
    order = [c for c in s4_cards.PRESERVATION_ORDER if c != "F01"] + \
        [c for c in s4_cards.CARDS if c not in s4_cards.PRESERVATION_ORDER]
    for cell in order:
        c = m.cells.get(cell)
        if not c or not c["gpu"] or cell in deferred:
            continue
        if c["exec_state"] != "PLANNED":
            continue
        if m.deps_dead(cell):
            m.set_exec(cell, "BLOCKED", "a dependency failed or was deferred")
            m.set_outcome(cell, "NOT_RUN", "BLOCKED_DEPENDENCY")
            continue
        if m.deps_complete(cell):
            return cell
    return None


def _cpu_cells_to_start(m: Manifest, running: dict, cap: int) -> list[str]:
    out = []
    for cell in s4_cards.CPU_CARDS:
        if len(running) + len(out) >= cap:
            break
        c = m.cells.get(cell)
        if not c or c["exec_state"] != "PLANNED" or cell in running:
            continue
        if m.deps_dead(cell):
            m.set_exec(cell, "BLOCKED", "a dependency failed")
            continue
        if m.deps_complete(cell):
            out.append(cell)
    return out


def _expansion_rung(m: Manifest, contract: RunContract, design: dict, L: Lineages) -> str | None:
    """Rung 1 of the predeclared ladder: more independent worlds for the strongest C/A/T
    cards, in bridge order, allocated fresh and run as a resume of the same card (the
    runner skips scored units). Rungs 2 and 3 (harder context conflicts, a second
    rendering family) are predeclared and recorded as not reached."""
    if design.get("tier") == "expanded":
        return None
    for card in ("C01", "C02", "A01", "A02", "T01", "T02", "T03", "C03", "H02"):
        cell = f"{card}/expand"
        if cell in m.cells or m.cells.get(card, {}).get("exec_state") != "COMPLETE":
            continue
        extra = (2 if SMOKE else
                 s4_cards.TIERS["expanded"][s4_cards.CARDS[card]["unit"]] - s4_cards.TIERS["minimum"][s4_cards.CARDS[card]["unit"]])
        parent_card = {"A02": "A01", "A03": "A01", "T02": "T01", "T03": "T01"}.get(card)
        for dom in s4_cards.CARDS[card]["domains"]:
            if parent_card:
                parents = [lid for lid, r in L.rows.items() if r["card"] == parent_card and r["domain"] == dom
                           and r["split"] == "discovery" and r.get("parent") is None]
                for p in parents:
                    L.derive(p, card.lower(), card=card)
            else:
                L.allocate(card, dom, list(s4_cards.SEEDS), extra, "discovery",
                           world_offset=s4_cards.TIERS["minimum"][s4_cards.CARDS[card]["unit"]])
        m.add(cell, card, [card], str(S4 / card / "verdict.json"),
              s4_cards.CARDS[card]["est_s_per_unit"] * extra / 60, True,
              f"expansion rung 1: {extra} more units per domain for {card}")
        log(f"expansion rung 1 admitted: {cell}")
        return cell
    return None


def run(cpu_cap: int = 2) -> int:
    contract = RunContract.load() or RunContract.create()
    m = Manifest()
    if not m.cells:
        prepare()
        m = Manifest()
    contract.start()
    log(f"run: start {contract.data['execution_start']} deadline {contract.data['deadline']} "
        f"(elapsed {contract.elapsed_h():.2f}h); "
        + ("stops at the deadline" if contract.stops_at_deadline else
           "runs until the queue is empty (his ruling 2026-08-28); the deadline is accounting only"))
    # a restart finds no cell running: whatever the previous loop left RUNNING is
    # re-planned and resumes from its checkpointed rows (without this a killed card
    # would sit RUNNING forever and its dependents would never be admitted)
    for cell, c in m.cells.items():
        if c["exec_state"] == "RUNNING":
            m.set_exec(cell, "PLANNED", "re-planned at restart; resumes from its rows")
            log(f"restart: {cell} re-planned")
    running_cpu: dict[str, tuple[subprocess.Popen, float, object]] = {}
    try:
        from tools.s4_construction_audit import audit as _construction_audit         # noqa: PLC0415
        aud = _construction_audit(Lineages())
        log(f"construction audit: {aud['summary']}")
    except Exception as e:                                                       # noqa: BLE001
        log(f"construction audit unavailable: {e!r}")
    f01_done = False
    exhausted = False
    while True:
        contract.data = _fresh(contract).data
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
                m.set_outcome(cell, v.get("outcome", "VOID") if v.get("outcome") else "VOID", v.get("reason"))
            else:
                m.set_exec(cell, "FAILED", f"cpu cell exit {rc}")
                m.set_outcome(cell, "INSTRUMENT_FAILED")
            m.charge(cell, (time.time() - t0) / 60, 0.0)
            log(f"cpu done {cell}: {m.cells[cell]['exec_state']} / {m.cells[cell]['outcome']}")
        design = contract.frozen("design") or {}
        if contract.deadline_passed():
            log("deadline passed: stop admitting; closing")
            break
        # closure block at hour 20 (brief §5.3): F01 runs FIRST, before any further
        # discovery cell, on whatever is complete by then; what is still planned resumes
        # after it with the remaining hours (F01's closure clause: the allowance goes to
        # admitted work and predeclared extensions, the run does not end). The smoke's
        # version let discovery run on past hour 20 until every cell had finished.
        if contract.closure_due() and not f01_done:
            if m.cells.get("F01", {}).get("exec_state") == "PLANNED":
                _status(m, contract, running_cpu, "closure block: F01")
                state = _run_cell(m, contract, "F01")
                if state == "RETRY":
                    continue
            f01_done = True
            log("closure block done; admitted work and the expansion ladder resume until the deadline")
            continue
        # CPU cells
        for cell in _cpu_cells_to_start(m, running_cpu, cpu_cap):
            m.set_exec(cell, "RUNNING")
            logf = open(S4 / f"{cell}.log", "a", encoding="utf-8")
            proc = subprocess.Popen(runner_cmd(cell), cwd=str(REPO), stdout=logf, stderr=subprocess.STDOUT)
            running_cpu[cell] = (proc, time.time(), logf)
            log(f"cpu start {cell}")
        # GPU cell: discovery in preservation order, then the expansion ladder
        cell = _next_gpu_cell(m, design)
        if cell is None and design and (not contract.closure_due() or f01_done):
            cell = _expansion_rung(m, contract, design, Lineages())
        if cell is None:
            if running_cpu:
                _status(m, contract, running_cpu, "no GPU cell runnable; CPU cells running")
                time.sleep(30)
                continue
            if not f01_done:
                # discovery and the ladder ran dry before hour 20: the closure block
                # begins early on genuine exhaustion (§5.2), never by waiting idle
                log("admitted work exhausted before the closure hour: closure block begins now")
                if m.cells.get("F01", {}).get("exec_state") == "PLANNED":
                    state = _run_cell(m, contract, "F01")
                    if state == "RETRY":
                        continue
                f01_done = True
                continue
            exhausted = True
            log("all admitted work and the expansion ladder are exhausted before the deadline: SHORT_RUN")
            break
        _status(m, contract, running_cpu, f"running {cell}")
        _run_cell(m, contract, cell)
    # closure
    for cell, (proc, t0, logf) in running_cpu.items():
        try:
            proc.wait(timeout=1800)
        except subprocess.TimeoutExpired:
            proc.kill()
        logf.close()
    # run-until-empty (his standing ruling, 2026-08-28): the run ends on exhaustion of the
    # admitted work and its ladder, labeled as such with the elapsed hours beside it; the
    # windowed labels apply only to a contract that stops at its deadline
    if not contract.stops_at_deadline:
        label = "RUN_TO_EMPTY"
    else:
        label = "SHORT_RUN" if exhausted and not contract.deadline_passed() else "COMPLETE_24H"
    contract.data["run_label"] = label
    contract.data["exhausted"] = exhausted
    contract.save()
    validate(write=True)
    final_packet(exhausted=exhausted)
    log(f"closed: {label}")
    return 0


# ── validate ──────────────────────────────────────────────────────────────────────────

# how each card's controls show up: a row predicate on the factors, or a metrics key
CONTROL_ROWS = {
    ("C01", "context_mismatched_targets"): lambda f: f.get("profile_matches_context") is False,
    ("C02", "constraint_change"): lambda f: f.get("control") == "constraint_change",
    ("A01", "withheld_context"): lambda f: f.get("withheld") is True,
    ("A02", "own_choice_no_target"): lambda f: f.get("control") == "own_choice_no_target",
    ("A02", "zero_baseline"): lambda f: f.get("intervention") == "zero" and "control" not in f,
    ("T02", "oracle_intention"): lambda f: f.get("route") == "oracle",
    ("T03", "held_out_family"): lambda f: "held_out_family" in f,
    ("H02", "exact_collision"): lambda f: f.get("history") in ("stable", "marker_removed") and f.get("access") == "artifact_only",
}
CONTROL_METRICS = {
    ("C03", "random_selector"): "primary_selection_minus_random_exact",
    ("C03", "first_listed"): "selection_minus_first_listed",
    ("C03", "exact_selector"): "selection_minus_oracle",
    ("H01", "constraint_flip"): "causal_reach_flip",
    ("P01", "category_prior"): "priors_balanced_accuracy",
    ("P01", "ink_prior"): "priors_balanced_accuracy",
    ("P01", "geometry_prior"): "priors_balanced_accuracy",
    ("P01", "rotation"): "rotation_transformed_labels_balanced_accuracy",
    ("P02", "geometry_heuristic"): "first_stroke_identification",
    ("P02", "exact_collision"): "collision_note",
    ("H03", "majority"): "per_project", ("H03", "markov"): "per_project", ("H03", "duration"): "per_project",
    ("I02", "position_swap"): "per_reader", ("I02", "paraphrase"): "per_reader",
    ("F01", "severe_rival"): "results", ("F01", "negative_control"): "results",
}


def validate(write: bool = False) -> dict:
    m = Manifest()
    exp_p = S4 / "EXPECTED_CELLS.json"
    expected = read_json(exp_p)["cells"] if exp_p.exists() else []
    realized = {}
    from soundingline.s4 import canonical                                         # noqa: PLC0415
    for card in s4_cards.CARDS:
        rows = read_jsonl(S4 / card / "cases.jsonl")
        spec = s4_cards.CARDS[card]
        for r in rows:
            f = dict(r["factors"])
            keys = []
            if "control" not in f and all(k in f for k in spec["factors"]):
                keys.append({k: f.get(k) for k in spec["factors"]} | {"domain": f.get("domain")})
            for ctl in spec["controls"]:
                pred = CONTROL_ROWS.get((card, ctl))
                if pred and pred(f):
                    keys.append({"domain": f.get("domain"), "control": ctl})
            for key_f in keys:
                k = canonical({"card": card, "factors": key_f})
                c = realized.setdefault(k, {"attempted": 0, "realized": 0, "valid": 0, "scored": 0, "units": set()})
                c["attempted"] += 1
                c["realized"] += int(r.get("realized", False))
                c["valid"] += int(r.get("valid", False))
                # a control cell whose rows carry no primary score by design (A02's own-choice
                # control records a probability vector, not a score) counts its VALID rows;
                # the live run's first coverage read flagged that cell under floor for this
                if r.get("primary_score") is not None or ("control" in key_f and r.get("valid")):
                    c["scored"] += 1
                    c["units"].add(r["unit_id"])
        # metrics-carried controls count as complete for every domain when their key exists
        mp = S4 / card / "metrics.json"
        vp = S4 / card / "verdict.json"
        src = {}
        if mp.exists():
            src.update(read_json(mp))
        if vp.exists():
            src.update(read_json(vp))
        for ctl in spec["controls"]:
            mk = CONTROL_METRICS.get((card, ctl))
            if mk and mk in src and src[mk] is not None:
                for dom in (spec["domains"] or ["all"]):
                    k = canonical({"card": card, "factors": {"domain": dom, "control": ctl}})
                    c = realized.setdefault(k, {"attempted": 0, "realized": 0, "valid": 0, "scored": 0, "units": set()})
                    c["metric_present"] = True
    for c in realized.values():
        c["scored"] = len(c.pop("units")) if not c.get("metric_present") else 10 ** 9
    cov = coverage(expected, realized)
    L = Lineages()
    cov["duplicate_lineages"] = L.duplicate_content()
    # the duplicate control reports what it could check (2026-08-28: it had returned an
    # empty list over an unmarked ledger); the construction audit rebuilds every root
    # world from its id and counts distinct constructions and cross-split twins
    cov["generation_hash_coverage"] = L.generation_coverage()
    try:
        from tools.s4_construction_audit import audit as _construction_audit         # noqa: PLC0415
        cov["construction_audit"] = _construction_audit(L)
    except Exception as e:                                                       # noqa: BLE001
        cov["construction_audit"] = {"error": repr(e)}
    cov["cells"] = m.state_counts()
    cov["outcomes"] = {}
    for c in m.cells.values():
        cov["outcomes"][c["outcome"]] = cov["outcomes"].get(c["outcome"], 0) + 1
    if write:
        write_json(S4 / "COVERAGE.json", cov)
    return cov


# ── final packet ──────────────────────────────────────────────────────────────────────

TRACK_QUESTIONS = {
    "context": "Did contextual adjustment improve new predictions beyond the same facts, and did individual evidence correct a wrong adjustment?",
    "appraisal": "Did appraisal steering help predict someone else, or only change the reader's own answers?",
    "transmission": "Did a message's transmissibility, usefulness, and source transparency come apart, and did the reader preserve useful uptake while resisting misleading selection?",
    "hierarchy": "Did relay/edit dependencies identify historical choices beyond conventions, superficial anomalies, and annotation persistence?",
    "physical": "Did a final physical artifact provide action information beyond cheap shape priors, and how much extra information came from process records?",
}


def _fmt(x, nd=3):
    return "not measured" if x is None else (f"{x:+.{nd}f}" if isinstance(x, (int, float)) else str(x))


def final_packet(exhausted: bool = False) -> int:
    contract = RunContract.load()
    if not packet_allowed(contract, exhausted):
        log("final packet refused: deadline not passed and no exhaustion recorded")
        return 2
    m = Manifest()
    cov = read_json(S4 / "COVERAGE.json") if (S4 / "COVERAGE.json").exists() else validate(write=True)
    verdicts = {c: read_json(S4 / c / "verdict.json") for c in s4_cards.CARDS if (S4 / c / "verdict.json").exists()}
    lines = ["# Stage 4 curator packet (final, the only one)", "",
             f"Run {contract.data.get('execution_start')} to {contract.data.get('deadline')}; label "
             f"{contract.data.get('run_label')}; contract {contract.hash()}.", ""]
    lines += ["## What changed in the model of the world", ""]
    support = [c for c, v in verdicts.items() if v.get("outcome") == "SUPPORT_CANDIDATE"]
    nulls = [c for c, v in verdicts.items() if v.get("outcome") in ("VALID_NULL", "COUNTEREVIDENCE")]
    instr = [c for c, v in verdicts.items() if v.get("outcome") == "INSTRUMENT_FAILED"]
    lines.append(f"Support candidates: {', '.join(support) or 'none'}. Valid nulls or counterevidence: "
                 f"{', '.join(nulls) or 'none'}. Instrument failures: {', '.join(instr) or 'none'}. "
                 f"(Plain-language synthesis is written by the analyst after the run from these classes; "
                 f"this section is the machine draft.)")
    lines += ["", "## Tracks", "", "| track | asked | observed | leading explanation | strongest rival | pursuit | warrant | next decision |",
              "|---|---|---|---|---|---|---|---|"]
    ledger = ClaimLedger()
    for track, q in TRACK_QUESTIONS.items():
        cards = [c for c in s4_cards.CARDS if s4_cards.CARDS[c]["track"] == track]
        obs = "; ".join(f"{c} {verdicts[c].get('outcome')} ({_fmt(verdicts[c].get('point'))})" for c in cards if c in verdicts) or "not run"
        pursuit = "PROMISING" if any(verdicts.get(c, {}).get("outcome") == "SUPPORT_CANDIDATE" for c in cards) else "OPENED"
        warrant = "BOUNDED_MODEL_EFFECT" if pursuit == "PROMISING" else "NONE"
        lines.append(f"| {track} | {q} | {obs} | see appendix | see card controls | {pursuit} | {warrant} | analyst |")
    lines += ["", "*Table: one row per track; the analyst's synthesis replaces the placeholder cells after the run.*", ""]
    lines += ["## The five questions", ""]
    for i, (track, q) in enumerate(TRACK_QUESTIONS.items(), 1):
        cards = [c for c in s4_cards.CARDS if s4_cards.CARDS[c]["track"] == track and c in verdicts]
        ans = "; ".join(f"{c}: {verdicts[c].get('outcome')}" for c in cards) or "not measured"
        lines.append(f"{i}. {q} {ans}.")
    lines += ["", "## Appendix: execution", ""]
    dur = contract.duration_report(m.total_gpu_lock_seconds())
    lines.append(f"Elapsed {dur['elapsed_hours']} h; GPU lock held {dur['gpu_lock_held_hours']} h; recorded lost time "
                 f"{dur['lost_hours_recorded']} h; full window completed: {dur['completed_full_window']}.")
    lines.append(f"Cells: {json.dumps(cov.get('cells'))}. Outcomes: {json.dumps(cov.get('outcomes'))}. "
                 f"Coverage: {cov.get('complete')}/{cov.get('expected')} expected cells complete; "
                 f"{len(cov.get('missing', []))} missing; {len(cov.get('under_floor', []))} under floor.")
    design = contract.frozen("design") or {}
    lines.append(f"Tier {design.get('tier')}; label {design.get('label')}; deferred {design.get('deferred')}; "
                 f"readers {list((design.get('readers') or {}).keys())}.")
    lines.append("Expansion ladder: rung 1 (more worlds) implemented; rungs 2 and 3 predeclared and not reached unless listed above.")
    lines += ["", "## Appendix: per-card verdicts", ""]
    for c, v in verdicts.items():
        lines.append(f"- **{c}** {v.get('exec')} / {v.get('outcome')}: {v.get('primary', '')}; point {_fmt(v.get('point'))}, "
                     f"ci {v.get('ci')}, n {v.get('n_units')}; {v.get('reason', '')}")
    lines += ["", f"Claims in the ledger: {len(ledger.claims)}.", ""]
    p = write_packet("\n".join(lines) + "\n", contract, exhausted)
    log(f"final packet written: {p}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("op", choices=["prepare", "calibrate", "run", "validate", "final-packet", "status", "reset"])
    ap.add_argument("--cells", nargs="*", default=[], help="reset: cells to re-plan")
    ap.add_argument("--tag", default="repair", help="reset: folder tag for the preserved attempt")
    ap.add_argument("--why", default="", help="reset: the reason, recorded on the cell")
    a = ap.parse_args()
    if a.op == "reset":
        if not a.cells:
            print("reset needs --cells")
            return 2
        return reset(a.cells, a.tag, a.why)
    if a.op == "prepare":
        return prepare()
    if a.op == "calibrate":
        contract = RunContract.load() or RunContract.create()
        contract.start()
        m = Manifest()
        for cell in ("I03pilot", "I02", "I03"):
            if m.cells[cell]["exec_state"] == "PLANNED":
                _run_cell(m, contract, cell)
        return 0
    if a.op == "run":
        return run()
    if a.op == "validate":
        print(json.dumps(validate(write=True), indent=1)[:3000])
        return 0
    if a.op == "final-packet":
        c = RunContract.load()
        return final_packet(exhausted=bool(c and c.data.get("exhausted")))
    if a.op == "status":
        print(STATUS.read_text(encoding="utf-8") if STATUS.exists() else "no status")
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())
