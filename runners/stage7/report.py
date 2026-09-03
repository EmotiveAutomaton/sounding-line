"""Stage 7 reporter (brief §13.2, §19): the ONE curator-facing file, written after
closure (every mandatory disposition, locked expansion, confirmation, and validation) in
the two-pass form: Pass A (how the world model moved; the minimum Stage 6 correction; the
capability-ladder table; the architecture table with conformance-passed names only; the
ecological table; the eight direct answers; three to six open questions; STOP) and Pass B
(the analyst appendix). The reporter REFUSES before closure or without validation; there
is no other packet path (X24 verifies). The machine draft is what this writes; the
analyst synthesis is written above it after the run, by hand, as in Stage 6.

DESIGN CHECK (2026-09-02)
lessons read: LESSONS §3 (verdict-only reporting is the named leak: Pass B carries every
  conditional matrix, ratio, recall, class, receipt, and repair), §5 (the packet path is
  guarded by refuse_packet_path).
gates: refusal conditions stated in write_final_packet. bands: none.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from runners.stage7 import cards as C                                              # noqa: E402
from soundingline.stage7 import (EXTERNAL_FAMILIES, S7, PacketGuard, RunContract7,  # noqa: E402
                                 read_json, read_registry, write_packet)


class PacketRefused(PacketGuard):
    pass


EIGHT = [
    ("Did the physical evidence boundary hold?", ["I04", "I05", "I06", "I07", "I08", "X04"]),
    ("Could any reader use a complete supplied maker model?", ["K04", "K05", "K15", "B01"]),
    ("Was the bottleneck proposal coverage, state representation, inference, or model capacity?", ["R01", "R02", "R03", "K16", "A16", "A15"]),
    ("Could the system learn a maker law rather than select one supplied in advance?", ["K14", "R09"]),
    ("Could it reconstruct the maker's perceived action space?", ["K13", "R04", "R08"]),
    ("Did joint factor reconstruction improve hidden behavior beyond common process?", ["R13", "R11", "R12", "B02"]),
    ("Could it localize a hidden human/model process discontinuity beyond style?", ["P11", "P12", "B03"]),
    ("Did dated histories add any prospective information beyond aggregate expertise/style?", ["V04", "V05", "V06"]),
]


def _v(card: str) -> dict:
    p = S7 / card / "verdict.json"
    return read_json(p) if p.exists() else {}


def _m(card: str) -> dict:
    p = S7 / card / "metrics.json"
    return read_json(p) if p.exists() else {}


def _fmt(x, nd=3):
    return "not measured" if x is None else (f"{x:+.{nd}f}" if isinstance(x, (int, float)) else str(x))


def write_final_packet(force: bool = False) -> Path:
    contract = RunContract7.load()
    if contract is None or not contract.data.get("execution_start"):
        raise PacketRefused("the clock has not started; no packet before the pilot")
    cov = read_registry("COVERAGE")
    if not cov:
        raise PacketRefused("validation has not run; the packet requires the coverage registry")
    if cov.get("missing_mandatory"):
        raise PacketRefused(f"validation incomplete: {len(cov['missing_mandatory'])} mandatory dispositions missing")
    if not force and not (contract.data.get("exhausted") or contract.deadline_passed()):
        raise PacketRefused("closure has not been recorded (no exhaustion, the ceiling not reached); no early packet exists (§13.2)")
    verdicts = {c: _v(c) for c in list(C.QUESTIONS) + list(C.ATTACKS) if _v(c)}
    gates = read_registry("GATES") or {}
    conf = read_registry("CONFORMANCE") or {}
    audit = read_registry("STAGE6_DEPENDENCY_AUDIT") or {}
    lines = ["# Stage 7 curator packet (final, the only one)", "",
             f"Run {contract.data.get('execution_start')} to closure; elapsed {contract.elapsed_h():.1f} h of the 72-hour ceiling; label {contract.data.get('run_label')}; contract {contract.hash()}.", "",
             "## Pass A", "", "### How the world model moved (machine draft; the analyst synthesis is written above this after the run)", ""]
    support = [c for c, v in verdicts.items() if v.get("outcome") == "SUPPORT_CANDIDATE"]
    nulls = [c for c, v in verdicts.items() if v.get("outcome") in ("VALID_NULL", "COUNTEREVIDENCE")]
    instr = [c for c, v in verdicts.items() if v.get("outcome") == "INSTRUMENT_FAILED"]
    lines.append(f"Gates: {json.dumps({k: v.get('passed') for k, v in gates.items() if isinstance(v, dict) and 'passed' in v})}. "
                 f"Support candidates: {', '.join(support) or 'none'}. Valid nulls or counterevidence: {', '.join(nulls) or 'none'}. "
                 f"Instrument failures: {', '.join(instr) or 'none'}.")
    lines += ["", "### The minimum Stage 6 correction needed to interpret Stage 7", ""]
    for k, v in (audit.get("D04_suspended") or {}).items():
        lines.append(f"- **{k}**: {v}")
    lines += ["", "### The capability ladder", "", "| rung | what is supplied | arm | outcome | gain (nats) | U_state or R | ",
              "|---|---|---|---|---|---|"]
    for card in ("K03", "K04", "K05", "K06", "K07", "K08", "K09", "K10", "K11", "K12", "K13", "K14", "K15", "R09", "R13"):
        v = verdicts.get(card, {})
        m = _m(card)
        u = m.get("u_state_by_reader") or {}
        lines.append(f"| {card} | {', '.join(C.ALL[card]['condition'].get('supplied') or ['none'])} | {'/'.join(C.ALL[card]['arms'])} | {v.get('outcome', 'not run')} | {_fmt(v.get('point'))} | {json.dumps({k: round(x, 3) for k, x in u.items() if x is not None}) if u else ''} |")
    lines += ["", "*Table: one row per ladder rung; gain is the headline paired contrast at the world with the reader named in the verdict; U_state per reader where defined.*", ""]
    lines += ["### The architectures (conformance-passed names only; local names otherwise)", "", "| mechanism | name used | fixture | A15 gain vs DIR | compute (calls, solver ops) |", "|---|---|---|---|---|"]
    a15 = _m("A15")
    for fam, rec in EXTERNAL_FAMILIES.items():
        cf = conf.get(fam, {})
        name = rec["published"] if cf.get("pass") else rec["local"]
        local = rec["local"]
        cell = (a15.get("all_cells") or {}).get(f"{local}|pooled") or next((v for k, v in (a15.get("all_cells") or {}).items() if k.startswith(local)), {})
        comp = (a15.get("compute_by_arm") or {}).get(local, {})
        lines.append(f"| {local} | {name} | {'PASS' if cf.get('pass') else ('FAIL' if fam in conf else 'not run')} | {_fmt(cell.get('point'))} | {comp.get('model_calls')}, {comp.get('solver_operations')} |")
    lines += ["", "*Table: one row per external family; the name column carries the published name only after its fixture passed.*", ""]
    lines += ["### The ecological table", "", "| record | question | outcome | point | detail |", "|---|---|---|---|---|"]
    for card, rec in (("P11", "mixed-control histories"), ("P12", "style-matched / style-shifted adversaries"), ("P13", "CoAuthor (repaired loader)"), ("P14", "ScholaWrite switches"), ("B03", "discontinuity confirmation")):
        v = verdicts.get(card, {})
        lines.append(f"| {rec} | {card} | {v.get('outcome', 'not run')} | {_fmt(v.get('point'))} | {str(v.get('reason', ''))[:120]} |")
    lines += ["", "*Table: the natural and controlled records; point is the headline contrast against the frozen surface or persistence rival.*", ""]
    lines += ["### The eight answers", ""]
    for i, (q, cards) in enumerate(EIGHT, 1):
        ans = "; ".join(f"{c}: {verdicts[c].get('outcome')} ({_fmt(verdicts[c].get('point'))})" for c in cards if c in verdicts) or "not measured"
        lines.append(f"{i}. {q} {ans}.")
    lines += ["", "### Open theory questions (three to six; the analyst prunes)", ""]
    open_qs = []
    if not (gates.get("supplied_state") or {}).get("passed"):
        open_qs.append("No reader used a complete executable supplied state: is the interface, the representation, or the capacity the boundary (K16, A16)?")
    if (gates.get("supplied_state") or {}).get("passed") and not (gates.get("infer_goal") or {}).get("passed"):
        open_qs.append("The state is usable when supplied but the proximal goal is not recovered: is proposal coverage (R01) or selection the failure?")
    if verdicts.get("R09", {}).get("outcome") not in ("SUPPORT_CANDIDATE", None):
        open_qs.append("Laws are selected but not learned from demonstrations: what evidence form would carry a law?")
    if (gates.get("discontinuity") or {}).get("passed"):
        open_qs.append("A process discontinuity localizes beyond style on controlled histories: what natural record carries logged control?")
    if verdicts.get("V05", {}).get("outcome") in ("VALID_NULL", "COUNTEREVIDENCE"):
        open_qs.append("Dated histories add nothing over the aggregate profile here: is the drift construction too weak or the claim wrong?")
    for q in open_qs[:6]:
        lines.append(f"- {q}")
    lines += ["", "> **STOP READING HERE** (the theory pass is yours; Pass B is the appendix)", "", "## Pass B: analyst appendix", ""]
    dur = contract.duration_report((read_registry("RUNTIME") or {}).get("gpu_lock_seconds", 0.0))
    lines.append(f"Elapsed {dur['elapsed_hours']} h; GPU lock held {dur['gpu_lock_held_hours']} h; lost time {dur['lost_hours_recorded']} h; window elapsed {dur['completed_full_window']}; short run {bool(read_registry('SHORT_RUN'))}.")
    lines.append(f"Coverage: {cov.get('complete')}/{cov.get('mandatory_total')} mandatory; outcomes {json.dumps(cov.get('outcomes'))}; rows {cov.get('rows_total')}.")
    lines.append(f"Confirmations: {json.dumps((read_registry('CONFIRMATION_REGISTRY') or {}).get('selected'))}.")
    lines.append(f"Access receipt: all raised {(read_registry('ACCESS_RECEIPT') or {}).get('all_raised')}; boundary {(read_registry('INFORMATION_BOUNDARY') or {}).get('honest_label')}.")
    lines.append(f"Sources: {json.dumps({k: v.get('status') for k, v in (read_registry('SOURCE_MANIFEST') or {}).get('sources', {}).items()})}.")
    lines.append(f"Ghost bridge: {json.dumps(read_registry('GHOST_BRIDGE'))}.")
    lines.append(f"Dependency audit class counts: {json.dumps(audit.get('class_counts'))}.")
    lines.append(f"Workload lock: {json.dumps({k: v for k, v in (read_registry('WORKLOAD_LOCK') or {}).items() if k in ('base_forecast_h', 'ladder_forecast_h', 'total_forecast_h', 'target_h')})}.")
    lines.append(f"Repairs: {json.dumps(read_registry('REPAIRS'))}.")
    lines.append(f"Fresh clone: {json.dumps((_v('X24') or {}).get('reason'))}.")
    lines += ["", "### Per-question verdicts", ""]
    for c in list(C.QUESTIONS) + list(C.ATTACKS):
        v = verdicts.get(c)
        if not v:
            lines.append(f"- **{c}**: NO VERDICT")
            continue
        lines.append(f"- **{c}** {v.get('exec')} / {v.get('outcome')}: {str(v.get('primary', ''))[:140]}; point {_fmt(v.get('point'))}, ci {v.get('ci')}, n {v.get('n_units')}; {str(v.get('reason', ''))[:220]}"
                     + (f"; cells {json.dumps({k: x.get('outcome') for k, x in (v.get('conditional_cells') or {}).items()})[:300]}" if v.get("conditional_cells") else ""))
    return write_packet("\n".join(lines) + "\n", contract, exhausted=bool(contract.data.get("exhausted")))


if __name__ == "__main__":
    try:
        p = write_final_packet()
        print("packet written:", p)
    except PacketGuard as e:
        print("REFUSED:", e)
        sys.exit(2)
