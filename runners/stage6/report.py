"""Stage 6 reporter (brief §11.1, §17): the ONE curator-facing file, written after hour
168 and successful validation, in the two-pass form (Pass A: the world-model movement, the
nine-architecture table, the seven direct answers, at most six open questions, STOP; Pass
B: the analyst appendix). The reporter REFUSES to write before the deadline or without
validation; there is no other packet path (I10 and X24 verify both).

DESIGN CHECK (2026-08-30)
lessons read: LESSONS §3 (verdict-only reporting is the named leak: the packet carries
  every conditional matrix in Pass B), §5 (the packet path is guarded by refuse_packet_path).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from runners.stage6 import cards as CARDS_MOD                                      # noqa: E402
from soundingline.stage6 import (S6, ARCH_NAMES, PacketGuard, RunContract6,        # noqa: E402
                                 read_json, read_registry, write_packet)


class PacketRefused(PacketGuard):
    pass


SEVEN = [
    ("Did contextual realization add anything beyond proposal and likelihood scoring?", ["M08", "M02", "M03"]),
    ("Could any reader predict both next edit and stopping from a supplied or inferred state?", ["I05", "P01", "P03"]),
    ("Which control architecture best explained held-out process behavior?", ["C03", "C11", "C12"]),
    ("Was expertise history reducible to selected attention under the tested interventions?", ["A01", "A03", "A04", "A14"]),
    ("Could value change be separated from concealment, context change, and lagging habit?", ["V08", "V09", "V10", "V14"]),
    ("Could exploration be separated from error, habit, and hidden artifact goal?", ["F11", "F02", "F12"]),
    ("What transferred to recorded process, and what remained a constructed ruler?", ["T05", "T10"]),
]


def _v(card: str) -> dict:
    p = S6 / card / "verdict.json"
    return read_json(p) if p.exists() else {}


def _fmt(x, nd=3):
    return "not measured" if x is None else (f"{x:+.{nd}f}" if isinstance(x, (int, float)) else str(x))


def write_final_packet(force_before_deadline_check: bool = False) -> Path:
    contract = RunContract6.load()
    if contract is None:
        raise PacketRefused("no run contract; nothing to report")
    if not contract.data.get("execution_start"):
        raise PacketRefused("the clock has not started; no packet before the pilot, let alone the deadline")
    if not force_before_deadline_check and not contract.deadline_passed():
        raise PacketRefused(f"the 168-hour window has not elapsed (elapsed {contract.elapsed_h():.1f} h); no early packet exists (§11.1)")
    cov = read_registry("COVERAGE")
    if not cov:
        raise PacketRefused("validation has not run; the packet requires the coverage registry")
    if cov.get("missing_mandatory"):
        raise PacketRefused(f"validation incomplete: {len(cov['missing_mandatory'])} mandatory dispositions missing")
    verdicts = {c: _v(c) for c in list(CARDS_MOD.CARDS) + list(CARDS_MOD.ATTACKS) if _v(c)}
    m09 = read_json(S6 / "M09" / "metrics.json") if (S6 / "M09" / "metrics.json").exists() else {}
    gaps = m09.get("oracle_gap_closed_by_card") or {}
    i05 = read_json(S6 / "I05" / "metrics.json") if (S6 / "I05" / "metrics.json").exists() else {}
    p12 = read_json(S6 / "P12" / "metrics.json") if (S6 / "P12" / "metrics.json").exists() else {}
    b04 = read_json(S6 / "B04" / "metrics.json") if (S6 / "B04" / "metrics.json").exists() else {}

    lines = ["# Stage 6 curator packet (final, the only one)", "",
             f"Run {contract.data.get('execution_start')} to {contract.data.get('deadline')}; elapsed "
             f"{contract.elapsed_h():.1f} h; label {contract.data.get('run_label')}; contract {contract.hash()}.", "",
             "## Pass A", "", "### How the world model moved (machine draft; the analyst synthesis is written above this after the run)", ""]
    support = [c for c, v in verdicts.items() if v.get("outcome") == "SUPPORT_CANDIDATE"]
    nulls = [c for c, v in verdicts.items() if v.get("outcome") in ("VALID_NULL", "COUNTEREVIDENCE")]
    instr = [c for c, v in verdicts.items() if v.get("outcome") == "INSTRUMENT_FAILED"]
    passed = [r.split("/")[-1] for r, x in (i05.get("readers") or {}).items() if x.get("passed")]
    lines.append(f"Capability: readers passing the supplied-true-state gate: {passed or 'none'}. "
                 f"Support candidates: {', '.join(support) or 'none'}. Valid nulls or counterevidence: {', '.join(nulls) or 'none'}. "
                 f"Instrument failures: {', '.join(instr) or 'none'}. Understanding criterion met by: {p12.get('met_by') or 'none'}.")
    lines += ["", "### The nine architectures", "",
              "| arm | what it is | tournament card | outcome | point | gap closed |", "|---|---|---|---|---|---|"]
    arm_card = {"D": "M01", "L": "M02", "LD": "M03", "TT": "M04", "GS": "M05", "EX": "M06", "AD": "M07", "CR": "M08", "OR": "M09"}
    for arm, card in arm_card.items():
        v = verdicts.get(card, {})
        g = (gaps.get(card) or {}).get("mean_gap_closed")
        lines.append(f"| {arm} | {ARCH_NAMES[arm]} | {card} | {v.get('outcome', 'not run')} | {_fmt(v.get('point'))} | {_fmt(g, 2)} |")
    lines += ["", "### The seven answers", ""]
    for i, (q, cards) in enumerate(SEVEN, 1):
        ans = "; ".join(f"{c}: {verdicts[c].get('outcome')} ({_fmt(verdicts[c].get('point'))})" for c in cards if c in verdicts) or "not measured"
        lines.append(f"{i}. {q} {ans}.")
    lines += ["", "### Open theory questions (at most six; the analyst prunes)", ""]
    open_qs = []
    if not passed:
        open_qs.append("Every local reader fails to use supplied true states: is the latents-to-choice interface a scale question or a representation question?")
    if verdicts.get("M08", {}).get("outcome") not in ("SUPPORT_CANDIDATE", None):
        open_qs.append("Contextual realization did not beat the scaffolds here: is the realizer's exactness doing the work the reader should do?")
    for c, q in (("C11", "Which control representation should later designs carry?"),
                 ("A14", "Which object best predicted the novel action, and does it survive a new constraint discriminator?"),
                 ("V14", "Do dated trajectories deserve a longitudinal program?"),
                 ("F11", "Is the foraging tetrad worth importing into the process analysis of natural records?")):
        if c in verdicts:
            open_qs.append(q)
    for q in open_qs[:6]:
        lines.append(f"- {q}")
    lines += ["", "> **STOP READING HERE** (the theory pass is yours; Pass B is the appendix)", "",
              "## Pass B — analyst appendix", ""]
    dur = contract.duration_report((read_registry("RUNTIME") or {}).get("gpu_lock_seconds", 0.0))
    lines.append(f"Elapsed {dur['elapsed_hours']} h; GPU lock held {dur['gpu_lock_held_hours']} h; lost time {dur['lost_hours_recorded']} h; window elapsed: {dur['completed_full_window']}.")
    lines.append(f"Coverage: {cov.get('complete')}/{cov.get('expected')} expected cells; outcomes {json.dumps(cov.get('outcomes'))}; "
                 f"short run: {bool(read_registry('SHORT_RUN'))}.")
    conf = read_registry("CONFIRMATION_REGISTRY") or {}
    lines.append(f"Confirmations: {json.dumps(conf.get('selected'))}.")
    lines.append(f"Corpus dispositions: {json.dumps((read_json(S6 / 'CORPUS_DISPOSITIONS.json') or {}).get('openreview', {}).get('status')) if (S6 / 'CORPUS_DISPOSITIONS.json').exists() else 'unwritten'} (openreview).")
    lines.append(f"Ghost bridge: {json.dumps((read_registry('GHOST_BRIDGE') or {}).get('v14_coverage'))}.")
    lines.append(f"Routing (B04): {json.dumps(b04.get('routing'))[:1500]}.")
    lines += ["", "### Per-card verdicts", ""]
    for c in list(CARDS_MOD.CARDS) + list(CARDS_MOD.ATTACKS):
        v = verdicts.get(c)
        if not v:
            lines.append(f"- **{c}**: NO VERDICT")
            continue
        lines.append(f"- **{c}** {v.get('exec')} / {v.get('outcome')}: {v.get('primary', '')[:140]}; point {_fmt(v.get('point'))}, "
                     f"ci {v.get('ci')}, n {v.get('n_units')}; {str(v.get('reason', ''))[:200]}"
                     + (f"; capability: {v['capability_note']}" if v.get("capability_note") else ""))
    return write_packet("\n".join(lines) + "\n", contract, exhausted=bool(contract.data.get("exhausted")))


if __name__ == "__main__":
    try:
        p = write_final_packet()
        print("packet written:", p)
    except PacketGuard as e:
        print("REFUSED:", e)
        sys.exit(2)
