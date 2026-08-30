"""Stage 5 scheduler (brief §8, §9): prepare, calibrate, run, validate, final-packet,
reset, status. The Stage-4 loop generalized to the Stage-5 records and card registry.

One clock, persisted at the discarded pilot's start and kept across restarts as
ACCOUNTING (his standing ruling 2026-08-28: second gear runs until the queue is empty;
the brief's 24 hours and hour-20 freeze are reported against, never stopped on). The
loop admits work by dependency and preservation order, runs GPU cells one at a time
through the card runners (which take the GPU lock themselves) and up to two CPU cells
beside them, records elapsed and lock-held time apart, walks the predeclared expansion
ladder once discovery is exhausted (rung 1 only while the elapsed clock is under the
freeze hour), runs the two confirmation cards on exhaustion, validates coverage, and
writes the single final packet. No interim packets exist.

DESIGN CHECK (2026-08-29)
lessons read: LESSONS §5 (produces guards; one writer for the manifest; a lock held by a
  dead process is released by Windows pid, never by an msys pid; a change-only watcher
  hangs without a deadline; the log is the record), §3 (a gate dependency is the verdict,
  not the file; power before verdicts).
gates: the scheduler holds three. admission by dependency, where under the null (every
  parent COMPLETE with a usable outcome) the child is admitted and under the alternative
  (a parent FAILED, BLOCKED, or repeatedly crashed) the child is NOT_RUN with the reason
  BLOCKED_DEPENDENCY, the direction guarded being a child run on a parent's missing
  output. the expansion rung, admitted only after every discovery cell is resolved and
  while the elapsed clock is under the freeze hour, so a late rung cannot dilute the
  confirmation reserve. the closure block, which under the null of no eligible
  candidate runs C01 and C02 as NOT_RUN with the reason written, and under the
  alternative runs each on frozen, untouched confirmation lineages at the corrected
  alpha. verdict bands are the card runners' (exhaustive there, no silent interval);
  the scheduler adds only the execution states COMPLETE, FAILED, RUNNING, PLANNED.
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

from runners import s5_cards                                                      # noqa: E402
from soundingline.stage5 import (S5, ClaimLedger5, Lineages5, Manifest5, RunContract5,   # noqa: E402
                                 coverage, now_iso, read_json, read_jsonl, read_registry,
                                 write_json, write_packet, write_registry)

PY = str(REPO / ".venv" / "Scripts" / "python.exe")
RUNNER_OF = {"I": "s5_run_i.py", "B": "s5_run_b.py", "J": "s5_run_j.py", "A": "s5_run_a.py",
             "R": "s5_run_r.py", "P": "s5_run_p.py", "F": "s5_run_f.py", "C": "s5_run_c.py"}
LOG = S5 / "scheduler.log"
STATUS = S5 / "SCHEDULER_STATUS.json"
MAX_ATTEMPTS = 3
SMOKE = bool(os.environ.get("S5_SMOKE"))


def log(msg: str) -> None:
    S5.mkdir(parents=True, exist_ok=True)
    line = f"[{now_iso()}] {msg}"
    print(line, flush=True)
    with open(LOG, "a", encoding="utf-8", newline="\n") as fh:
        fh.write(line + "\n")


def runner_cmd(cell: str) -> list[str]:
    card = cell.split("/")[0]
    return [PY, str(REPO / "runners" / RUNNER_OF[card[0]]), "--card", card]


def verdict_path(cell: str) -> Path:
    if cell.endswith("/expand"):
        return S5 / cell.split("/")[0] / "verdict.json"
    return S5 / cell / "verdict.json"


def _fresh(contract: RunContract5) -> RunContract5:
    return RunContract5.load(contract.path) or contract


# ── prepare ───────────────────────────────────────────────────────────────────────────

def prepare() -> int:
    S5.mkdir(parents=True, exist_ok=True)
    contract = RunContract5.create()
    m = Manifest5()
    m.add("I02pilot", "I02", [], str(S5 / "I02pilot" / "verdict.json"), 6.0, True, "the discarded throughput pilot")
    for card, c in s5_cards.CARDS.items():
        deps = list(c["depends_on"])
        if card == "I02":
            deps = ["I02pilot"]
        if card in ("C01", "C02"):
            continue                        # the closure block admits them on exhaustion
        m.add(card, card, deps, str(S5 / card / "verdict.json"),
              c["est_s_per_unit"] * s5_cards.units_for(card, "minimum") * max(1, len(c["domains"])) / 60, c["gpu"], c["primary"])
    m.add("C01", "C01", [], str(S5 / "C01" / "verdict.json"), 60.0, True, s5_cards.CARDS["C01"]["primary"])
    m.add("C02", "C02", ["C01"], str(S5 / "C02" / "verdict.json"), 60.0, True, s5_cards.CARDS["C02"]["primary"])
    Lineages5().save()
    write_registry("PREPARED", {"at": now_iso(), "contract_hash": contract.hash(), "cells": len(m.cells)})
    log(f"prepared: {len(m.cells)} cells, contract {contract.hash()}")
    return 0


# ── run ───────────────────────────────────────────────────────────────────────────────

def _run_cell(m: Manifest5, contract: RunContract5, cell: str) -> str:
    m.set_exec(cell, "RUNNING")
    t0 = time.time()
    cmd = runner_cmd(cell)
    log(f"start {cell}: {' '.join(cmd[2:])}")
    logf = open(S5 / f"{cell.replace('/', '_')}.log", "a", encoding="utf-8")
    env = dict(os.environ)
    if "/" in cell and not cell.endswith("/expand"):
        env["S5_CELL"] = cell                                  # a repair cell writes beside the withdrawn one
        if cell.endswith("/v2"):
            env["S5_READOUT_VERSION"] = "2"
    try:
        rc = subprocess.call(cmd, cwd=str(REPO), env=env, stdout=logf, stderr=subprocess.STDOUT)
    finally:
        logf.close()
    wall = time.time() - t0
    contract.data = _fresh(contract).data
    vp = verdict_path(cell)
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
            tail = (S5 / f"{cell.replace('/', '_')}.log").read_text(encoding="utf-8", errors="replace")[-600:]
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
    exec_state = v.get("exec", "COMPLETE")
    m.set_exec(cell, exec_state if exec_state in ("COMPLETE", "FAILED", "BLOCKED", "DEFERRED") else "COMPLETE", v.get("reason"))
    oc = v.get("outcome")
    m.set_outcome(cell, oc if oc in ("SUPPORT_CANDIDATE", "COUNTEREVIDENCE", "VALID_NULL", "INCONCLUSIVE", "HETEROGENEOUS", "INFRASTRUCTURE", "DESCRIPTIVE",
                                     "INSTRUMENT_FAILED", "VOID", "NOT_RUN") else "VOID", v.get("reason"))
    gpu_min = float(v.get("gpu_lock_min") or 0.0)
    m.charge(cell, wall / 60, gpu_min)
    log(f"done {cell}: exec={m.cells[cell]['exec_state']} outcome={m.cells[cell]['outcome']} wall={wall / 60:.1f}min gpu_lock={gpu_min:.1f}min")
    return m.cells[cell]["exec_state"]


def _status(m: Manifest5, contract: RunContract5, running_cpu: dict, note: str = "") -> None:
    write_registry("SCHEDULER_STATUS", {"at": now_iso(), "elapsed_h": round(contract.elapsed_h(), 3),
                                        "deadline_accounting": contract.data.get("deadline"), "counts": m.state_counts(),
                                        "running_cpu": list(running_cpu), "note": note,
                                        "gpu_lock_hours_total": round(m.total_gpu_lock_seconds() / 3600, 3)})


def _admissible(m: Manifest5, cell: str) -> bool:
    c = m.cells.get(cell)
    if not c or c["exec_state"] != "PLANNED":
        return False
    if m.deps_dead(cell):
        m.set_exec(cell, "BLOCKED", "a dependency failed or was deferred")
        m.set_outcome(cell, "NOT_RUN", "BLOCKED_DEPENDENCY")
        return False
    return m.deps_complete(cell)


def _next_gpu_cell(m: Manifest5) -> str | None:
    order = (["I02pilot"] + [c for c in s5_cards.PRESERVATION_ORDER]
             + [c for c in m.cells if "/" in c and not c.endswith("/expand")]      # repair cells
             + [c for c in m.cells if c.endswith("/expand")])
    for cell in order:
        c = m.cells.get(cell)
        if not c or not c["gpu"]:
            continue
        if _admissible(m, cell):
            return cell
    return None


def _cpu_cells_to_start(m: Manifest5, running: dict, cap: int) -> list[str]:
    out = []
    for cell in s5_cards.CPU_CARDS:
        if len(running) + len(out) >= cap:
            break
        if cell in running:
            continue
        if _admissible(m, cell):
            out.append(cell)
    return out


def _admit_repairs(m: Manifest5) -> None:
    """Repair cells (S5/REPAIR_CELLS.json) are admitted beside the cells they replace, and
    withdrawn cells (S5/WITHDRAWN_CELLS.json) are closed as NOT_RUN with the reason written,
    both at run start so a restart carries them (his ruling 2026-08-28: useless compute
    stops, is repaired, and re-runs; the withdrawn cell's rows stay on disk)."""
    wp = S5 / "WITHDRAWN_CELLS.json"
    if wp.exists():
        for w in read_json(wp):
            c = m.cells.get(w["cell"])
            if c and c["exec_state"] in ("PLANNED", "RUNNING"):
                m.set_exec(w["cell"], "BLOCKED", w["reason"])
                m.set_outcome(w["cell"], "NOT_RUN", w["reason"])
                log(f"withdrawn: {w['cell']}: {w['reason']}")
    rp = S5 / "REPAIR_CELLS.json"
    if rp.exists():
        for r in read_json(rp):
            if r["cell"] in m.cells:
                continue
            m.add(r["cell"], r["card"], r.get("depends_on", []), str(S5 / r["cell"] / "verdict.json"),
                  float(r.get("est_minutes", 30.0)), True, r["why"])
            log(f"repair cell admitted: {r['cell']}: {r['why']}")


def _expansion_rung(m: Manifest5, contract: RunContract5, design: dict, L: Lineages5) -> str | None:
    """Rung 1 of the frozen ladder (§8.3, item 1: more independent makers and sources):
    more discovery worlds for the cards in the expansion order, admitted only while the
    elapsed clock is under the freeze hour (an accounting rule the ladder honors) and
    only after every discovery cell has resolved."""
    if design.get("tier") == "expanded" or contract.elapsed_h() >= contract.data["closure_hour"]:
        return None
    if any(c["exec_state"] in ("PLANNED", "RUNNING") for k, c in m.cells.items() if not k.endswith("/expand") and k not in ("C01", "C02")):
        return None
    for card in s5_cards.EXPANSION_ORDER:
        cell = f"{card}/expand"
        if cell in m.cells or m.cells.get(card, {}).get("exec_state") != "COMPLETE":
            continue
        if any(k.startswith(card + "/") and not k.endswith("/expand") for k in m.cells):
            continue                                            # a replaced card is not expanded on its withdrawn readout
        unit = s5_cards.CARDS[card]["unit"]
        if unit not in s5_cards.TIERS["minimum"]:
            continue
        extra = 2 if SMOKE else s5_cards.TIERS["expanded"][unit] - s5_cards.TIERS["minimum"][unit]
        parent = s5_cards.DERIVED.get(card)
        root_card = parent or card
        for dom in (s5_cards.CARDS[card]["domains"] or ["all"]):
            if parent:
                # the root card gets its own extra worlds first, then the derived children
                existing = [lid for lid, r in L.rows.items() if r["card"] == root_card and r["domain"] == dom and r["split"] == "discovery" and r.get("parent") is None]
                have = len(existing)
                new_roots = L.allocate(root_card, dom, list(s5_cards.SEEDS), extra, "discovery", world_offset=have)
                for p in new_roots:
                    L.derive(p, card.lower(), card=card)
            else:
                existing = [lid for lid, r in L.rows.items() if r["card"] == card and r["domain"] == dom and r["split"] == "discovery" and r.get("parent") is None]
                L.allocate(card, dom, list(s5_cards.SEEDS), extra, "discovery", world_offset=len(existing))
        m.add(cell, card, [card], str(S5 / card / "verdict.json"), s5_cards.CARDS[card]["est_s_per_unit"] * extra / 60, True,
              f"expansion rung 1: {extra} more units per domain for {card}")
        log(f"expansion rung 1 admitted: {cell}")
        return cell
    return None


def run(cpu_cap: int = 2) -> int:
    contract = RunContract5.load() or RunContract5.create()
    m = Manifest5()
    if not m.cells:
        prepare()
        m = Manifest5()
    contract.start()
    log(f"run: start {contract.data['execution_start']} accounting deadline {contract.data['deadline']} (elapsed {contract.elapsed_h():.2f}h); "
        f"runs until the queue is empty (his ruling 2026-08-28)")
    for cell, c in m.cells.items():
        if c["exec_state"] == "RUNNING":
            m.set_exec(cell, "PLANNED", "re-planned at restart; resumes from its rows")
            log(f"restart: {cell} re-planned")
    _admit_repairs(m)
    try:
        from tools.s5_construction_audit import audit as _audit                   # noqa: PLC0415
        log(f"construction audit: {_audit(Lineages5())['summary']}")
    except Exception as e:                                                       # noqa: BLE001
        log(f"construction audit unavailable: {e!r}")
    running_cpu: dict = {}
    exhausted = False
    while True:
        contract.data = _fresh(contract).data
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
                m.set_outcome(cell, v.get("outcome") or "VOID", v.get("reason"))
            else:
                m.set_exec(cell, "FAILED", f"cpu cell exit {rc}")
                m.set_outcome(cell, "INSTRUMENT_FAILED")
            m.charge(cell, (time.time() - t0) / 60, 0.0)
            log(f"cpu done {cell}: {m.cells[cell]['exec_state']} / {m.cells[cell]['outcome']}")
        design = contract.frozen("design") or {}
        for cell in _cpu_cells_to_start(m, running_cpu, cpu_cap):
            m.set_exec(cell, "RUNNING")
            logf = open(S5 / f"{cell}.log", "a", encoding="utf-8")
            proc = subprocess.Popen(runner_cmd(cell), cwd=str(REPO), stdout=logf, stderr=subprocess.STDOUT)
            running_cpu[cell] = (proc, time.time(), logf)
            log(f"cpu start {cell}")
        cell = _next_gpu_cell(m)
        if cell is None and design:
            cell = _expansion_rung(m, contract, design, Lineages5())
        if cell is None:
            if running_cpu:
                _status(m, contract, running_cpu, "no GPU cell runnable; CPU cells running")
                time.sleep(30)
                continue
            # discovery and the ladder are exhausted: the closure block (C01 then C02)
            if any(m.cells[c]["exec_state"] == "PLANNED" for c in ("C01", "C02")):
                log("admitted work and the ladder are exhausted: closure block begins (C01, C02)")
                for c in ("C01", "C02"):
                    if _admissible(m, c):
                        state = _run_cell(m, contract, c)
                        if state == "RETRY":
                            break
                continue
            exhausted = True
            log("all admitted work, the ladder, and the closure block are exhausted: RUN_TO_EMPTY")
            break
        _status(m, contract, running_cpu, f"running {cell}")
        _run_cell(m, contract, cell)
    for cell, (proc, t0, logf) in running_cpu.items():
        try:
            proc.wait(timeout=1800)
        except subprocess.TimeoutExpired:
            proc.kill()
        logf.close()
    contract.data["run_label"] = "RUN_TO_EMPTY"
    contract.data["exhausted"] = exhausted
    contract.data["short_of_window"] = not contract.window_elapsed()
    contract.save()
    validate(write=True)
    final_packet(exhausted=exhausted)
    log("closed: RUN_TO_EMPTY")
    return 0


# ── reset ─────────────────────────────────────────────────────────────────────────────

def reset(cells: list[str], tag: str, why: str, root: Path | None = None) -> int:
    root = root or S5
    m = Manifest5(root / "QUEUE_MANIFEST.json")
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
        c = m.cells[cell]
        before = {k: c.get(k) for k in ("exec_state", "outcome", "attempts", "budget_charged_min", "gpu_lock_min")}
        c.update({"exec_state": "PLANNED", "outcome": "NOT_RUN", "attempts": 0, "started_at": None, "finished_at": None, "detail": None,
                  "reason": f"reset ({tag}): {why}; first attempt preserved under {sup.name}/"})
        c.setdefault("resets", []).append({"at": now_iso(), "tag": tag, "why": why, "before": before, "moved": moved})
        m.cells.pop(f"{card}/expand", None)
        m.save()
        write_json(sup / "RESET_NOTE.json", {"cell": cell, "tag": tag, "why": why, "at": now_iso(), "before": before, "moved": moved})
        line = f"reset {cell} ({tag}): {why}; {len(moved)} files preserved under {sup.name}/"
        if root == S5:
            log(line)
        else:
            with open(root / "scheduler.log", "a", encoding="utf-8", newline="\n") as fh:
                fh.write(f"[{now_iso()}] {line}\n")
    return 0


# ── validate ──────────────────────────────────────────────────────────────────────────

def validate(write: bool = False) -> dict:
    m = Manifest5()
    exp = read_registry("EXPECTED_CELLS") or {"cells": []}
    expected = exp["cells"]
    realized: dict = {}
    from soundingline.stage5 import canonical                                     # noqa: PLC0415
    for card, spec in s5_cards.CARDS.items():
        rows = read_jsonl(S5 / card / "cases.jsonl")
        for r in rows:
            f = dict(r["factors"])
            keys = []
            if "control" not in f and spec["factors"] and all(k in f for k in spec["factors"]):
                keys.append({k: f.get(k) for k in spec["factors"]} | {"domain": f.get("domain")})
            for ctl in spec["controls"]:
                if f.get("control") == ctl:
                    keys.append({"domain": f.get("domain"), "control": ctl})
            for key_f in keys:
                k = canonical({"card": card, "factors": key_f})
                c = realized.setdefault(k, {"attempted": 0, "realized": 0, "valid": 0, "scored": 0, "units": set()})
                c["attempted"] += 1
                c["realized"] += int(r.get("realized", False))
                c["valid"] += int(r.get("valid", False))
                if r.get("primary_score") is not None or ("control" in key_f and r.get("valid")):
                    c["scored"] += 1
                    c["units"].add(r["unit_id"])
        # controls carried by metrics count as complete for every domain when present
        vp = S5 / card / "verdict.json"
        if vp.exists():
            v = read_json(vp)
            for ctl in spec["controls"]:
                for dom in (spec["domains"] or ["all"]):
                    k = canonical({"card": card, "factors": {"domain": dom, "control": ctl}})
                    if k not in realized and v.get("exec") == "COMPLETE":
                        realized[k] = {"attempted": 0, "realized": 0, "valid": 0, "scored": 10 ** 9, "units": set(), "metric_present": True}
    for c in realized.values():
        if not c.get("metric_present"):
            c["scored"] = len(c.pop("units"))
        else:
            c.pop("units", None)
    cov = coverage(expected, realized)
    L = Lineages5()
    cov["duplicate_lineages"] = L.duplicate_content()
    cov["generation_hash_coverage"] = L.generation_coverage()
    try:
        from tools.s5_construction_audit import audit as _audit                   # noqa: PLC0415
        cov["construction_audit"] = _audit(L)
    except Exception as e:                                                       # noqa: BLE001
        cov["construction_audit"] = {"error": repr(e)}
    cov["cells"] = m.state_counts()
    cov["outcomes"] = {}
    for c in m.cells.values():
        cov["outcomes"][c["outcome"]] = cov["outcomes"].get(c["outcome"], 0) + 1
    cov["written_at"] = now_iso()
    if write:
        write_registry("COVERAGE", cov)
        write_registry("COMPLETION", {"cells": {k: {"exec_state": c["exec_state"], "outcome": c["outcome"], "produces": c["produces"],
                                                     "produced": Path(c["produces"]).exists()} for k, c in m.cells.items()},
                                      "written_at": now_iso()})
    return cov


# ── the final packet (machine draft) ──────────────────────────────────────────────────

SEVEN = [
    ("bridge", "Did L255's selective causal-use result survive a second checkpoint and domain?", ["B01", "B02", "B03"]),
    ("joint", "Did joint reconstruction improve a hidden future choice beyond same-evidence staged readers?", ["J01", "J02", "J05"]),
    ("joint", "Which latent became useful first, and did contradictions revise it appropriately?", ["J03", "J04"]),
    ("appraisal", "Could the reader distinguish who owned an affective appraisal and why a maker tried to induce it?", ["A01", "A03"]),
    ("appraisal", "Could it distinguish sincere alarm from strategic influence by predicting divergent behavior?", ["A02", "A04", "A05"]),
    ("route", "Did it choose reliable evidence routes rather than easy ones, and did forensic access buy enough information to justify its cost?", ["R01", "R02", "R03", "R04", "P01", "P02", "P03"]),
    ("foraging", "Did learning progress or structured reducible uncertainty explain useful foraging better than novelty, complexity, and raw error?", ["F01", "F02", "F03"]),
]


def _fmt(x, nd=3):
    return "not measured" if x is None else (f"{x:+.{nd}f}" if isinstance(x, (int, float)) else str(x))


def final_packet(exhausted: bool = False) -> int:
    contract = RunContract5.load()
    m = Manifest5()
    cov = read_registry("COVERAGE") or validate(write=True)
    verdicts = {c: read_json(S5 / c / "verdict.json") for c in s5_cards.CARDS if (S5 / c / "verdict.json").exists()}
    lines = ["# Stage 5 curator packet (final, the only one)", "",
             f"Run {contract.data.get('execution_start')}; accounting deadline {contract.data.get('deadline')}; label "
             f"{contract.data.get('run_label')}; elapsed {contract.elapsed_h():.2f} h; contract {contract.hash()}.", "",
             "## What changed in the model of the world", ""]
    support = [c for c, v in verdicts.items() if v.get("outcome") == "SUPPORT_CANDIDATE"]
    nulls = [c for c, v in verdicts.items() if v.get("outcome") in ("VALID_NULL", "COUNTEREVIDENCE")]
    instr = [c for c, v in verdicts.items() if v.get("outcome") == "INSTRUMENT_FAILED"]
    lines.append(f"Support candidates: {', '.join(support) or 'none'}. Valid nulls or counterevidence: {', '.join(nulls) or 'none'}. "
                 f"Instrument failures: {', '.join(instr) or 'none'}. (The plain-language synthesis is written by the analyst after the run; this section is the machine draft.)")
    lines += ["", "## Tracks", "", "| track | asked | observed | leading explanation | strongest rival | pursuit | warrant | next decision |", "|---|---|---|---|---|---|---|---|"]
    for track in ("bridge", "joint", "appraisal", "route", "process", "foraging"):
        cards = [c for c in s5_cards.CARDS if s5_cards.CARDS[c]["track"] == track]
        obs = "; ".join(f"{c} {verdicts[c].get('outcome')} ({_fmt(verdicts[c].get('point'))})" for c in cards if c in verdicts) or "not run"
        rival = "; ".join(str(verdicts[c].get("strongest_surviving_rival")) for c in cards if c in verdicts and verdicts[c].get("strongest_surviving_rival"))
        pursuit = "PROMISING" if any(verdicts.get(c, {}).get("outcome") == "SUPPORT_CANDIDATE" for c in cards) else "OPENED"
        lines.append(f"| {track} | see the seven questions | {obs} | analyst | {rival[:200] or 'see cards'} | {pursuit} | {'BOUNDED_MODEL_EFFECT' if pursuit == 'PROMISING' else 'NONE'} | analyst |")
    lines += ["", "## The seven answers", ""]
    for i, (_, q, cards) in enumerate(SEVEN, 1):
        ans = "; ".join(f"{c}: {verdicts[c].get('outcome')} ({_fmt(verdicts[c].get('point'))})" for c in cards if c in verdicts) or "not measured"
        lines.append(f"{i}. {q} {ans}.")
    lines += ["", "> **STOP READING HERE**", "", "## Appendix: execution", ""]
    dur = contract.duration_report(m.total_gpu_lock_seconds())
    lines.append(f"Elapsed {dur['elapsed_hours']} h; GPU lock held {dur['gpu_lock_held_hours']} h; lost time {dur['lost_hours_recorded']} h; "
                 f"the 24-hour window elapsed: {dur['completed_full_window']} (accounting only under the run-until-empty rule).")
    lines.append(f"Cells: {json.dumps(cov.get('cells'))}. Outcomes: {json.dumps(cov.get('outcomes'))}. Coverage: {cov.get('complete')}/{cov.get('expected')} expected cells; "
                 f"{len(cov.get('missing', []))} missing; {len(cov.get('under_floor', []))} under floor. Construction audit: {cov.get('construction_audit', {}).get('summary')}.")
    design = contract.frozen("design") or {}
    lines.append(f"Tier {design.get('tier')}; label {design.get('label')}; readers {list((design.get('readers') or {}).keys())}; second checkpoint {design.get('checkpoint2', {}).get('admitted')}.")
    conf = read_registry("CONFIRMATION_REGISTRY") or {}
    lines.append(f"Confirmations: {json.dumps(conf.get('selected'))}.")
    lines += ["", "## Appendix: per-card verdicts", ""]
    for c, v in verdicts.items():
        lines.append(f"- **{c}** {v.get('exec')} / {v.get('outcome')}: {v.get('primary', '')}; point {_fmt(v.get('point'))}, ci {v.get('ci')}, n {v.get('n_units')}; {v.get('reason', '')}; rival: {v.get('strongest_surviving_rival', '')}")
    lines += ["", f"Claims in the ledger: {len(ClaimLedger5().claims)}.", ""]
    p = write_packet("\n".join(lines) + "\n", contract, exhausted)
    log(f"final packet written: {p}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("op", choices=["prepare", "calibrate", "run", "validate", "final-packet", "status", "reset"])
    ap.add_argument("--cells", nargs="*", default=[])
    ap.add_argument("--tag", default="repair")
    ap.add_argument("--why", default="")
    a = ap.parse_args()
    if a.op == "prepare":
        return prepare()
    if a.op == "calibrate":
        contract = RunContract5.load() or RunContract5.create()
        contract.start()
        m = Manifest5()
        for cell in ("I01", "I02pilot", "I02", "I03", "I04"):
            if m.cells[cell]["exec_state"] == "PLANNED":
                _run_cell(m, contract, cell)
        return 0
    if a.op == "run":
        return run()
    if a.op == "validate":
        print(json.dumps(validate(write=True), indent=1)[:3000])
        return 0
    if a.op == "final-packet":
        c = RunContract5.load()
        return final_packet(exhausted=bool(c and c.data.get("exhausted")))
    if a.op == "status":
        print(STATUS.read_text(encoding="utf-8") if STATUS.exists() else "no status")
        return 0
    if a.op == "reset":
        if not a.cells:
            print("reset needs --cells")
            return 2
        return reset(a.cells, a.tag, a.why)
    return 1


if __name__ == "__main__":
    sys.exit(main())
