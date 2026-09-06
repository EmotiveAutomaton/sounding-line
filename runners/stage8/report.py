"""Stage 8 reporter (brief §16): the ONE curator-facing file, written after closure and
validation in the two-pass form: Pass A (world-model movement in three to seven sentences,
the gate ladder as one table over DOM, DIR0, FM, FM+P, FM+N, FR, and the oracle, whole and
tail; the purpose table; the accumulation table; the testbed summary; direct answers to the
four executive questions; three to six open theory questions; STOP) and Pass B (every
disposition, class, interval, receipt, repair, lineage, dollar, and fresh-clone result). No
recommended Stage 9 before the curator's Pass A response. The reporter REFUSES before
closure or without validation.

DESIGN CHECK (2026-09-04)
lessons read: LESSONS §3 (verdict-only reporting is the named leak: Pass B carries every
  cell), §5 (the packet path is guarded).
gates: refusal conditions in write_final_packet. bands: none.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from runners.stage8 import cards as C                                              # noqa: E402
from soundingline.stage8 import (S8, PacketGuard, RunContract8, interrupts,          # noqa: E402
                                 read_json, read_registry, write_packet)


class PacketRefused(PacketGuard):
    pass


FOUR = [
    ("Can the reader make?", ["E02", "E03", "E04", "E05", "E07"]),
    ("Does it look in the right places?", ["D01", "D02", "D03", "D04", "D05", "D06"]),
    ("Does it recover the goal as a purpose?", ["G01", "G02", "G03", "G04", "G05", "G06", "G07", "G08"]),
    ("Does the maker accumulate?", ["A01", "A02", "A03", "A04", "A05"]),
]


def _v(card: str) -> dict:
    p = S8 / card / "verdict.json"
    return read_json(p) if p.exists() else {}


def _m(card: str) -> dict:
    p = S8 / card / "metrics.json"
    return read_json(p) if p.exists() else {}


def _fmt(x, nd=3):
    return "not measured" if x is None else (f"{x:+.{nd}f}" if isinstance(x, (int, float)) else str(x))


def write_final_packet(force: bool = False) -> Path:
    from runners.stage8.validate import validate
    from runners.stage8.admission import admitted_readers
    from runners.stage8.claims import eligible_support_readers
    contract = RunContract8.load()
    if contract is None or not contract.data.get("execution_start"):
        raise PacketRefused("the clock has not started; no packet before the pilot")
    cov = validate()
    if cov.get("ok") is not True or cov.get("phase") != "final":
        raise PacketRefused(f"integrity failed under {cov.get('validator_version')}: {json.dumps(cov.get('reasons'))}")
    if not (contract.data.get("exhausted") or contract.deadline_passed()):
        raise PacketRefused("closure has not been recorded; no early packet exists (§12.2)")
    verdicts = {c: _v(c) for c in list(C.QUESTIONS) + list(C.ATTACKS) if _v(c)}
    gates = read_registry("GATES") or {}
    eg = admitted_readers()
    lines = ["# Stage 8 curator packet (final, the only one)", "",
             f"Run {contract.data.get('execution_start')} to closure; elapsed {contract.elapsed_h():.1f} h of the 48-hour ceiling; label {contract.data.get('run_label')}; contract {contract.hash()}.", "",
             "## Pass A", "", "### How the world model moved (machine draft; the analyst synthesis is written above this after the run)", ""]
    reader_claims = {c for c in C.ALL if c[0] in "DGA" or c in ("E06", "E08")} - {"D05", "G08"}
    support = [c for c, v in verdicts.items() if v.get("outcome") == "SUPPORT_CANDIDATE" and not v.get("diagnosis_only")
               and (c not in reader_claims or eligible_support_readers(v, eg))]
    nulls = [c for c, v in verdicts.items() if v.get("outcome") in ("VALID_NULL", "COUNTEREVIDENCE")]
    instr = [c for c, v in verdicts.items() if v.get("outcome") == "INSTRUMENT_FAILED"]
    lines.append(f"Reader admission: {json.dumps({k: {f: v.get(f) for f in ('prediction_passed', 'generation_passed', 'admission', 'reasons')} for k, v in eg.items()})}. "
                 f"Gates: {json.dumps({k: v.get('passed') for k, v in gates.items() if isinstance(v, dict) and 'passed' in v})}. "
                 f"Support candidates: {', '.join(support) or 'none'}. Valid nulls or counterevidence: {', '.join(nulls) or 'none'}. "
                 f"Instrument failures: {', '.join(instr) or 'none'}. Interrupts: {json.dumps([i['name'] for i in interrupts()])}.")
    lines += ["", "### The gate ladder", "", "| cell | arm | outcome | whole (nats) | tail (nats) |", "|---|---|---|---|---|"]
    for card, arm in (("E03", "FM vs DOM"), ("E05", "DIR0 and base vs DOM"), ("E07", "FR vs DOM"), ("E08", "FM with state vs DOM"), ("E06", "true vs false context"),
                      ("G02", "FM+P vs DOM"), ("A03", "FM+3 vs DOM"), ("A05", "FM+3 plus a factor")):
        v = verdicts.get(card, {})
        lines.append(f"| {card} | {arm} | {v.get('outcome', 'not run')} | {_fmt(v.get('point'))} {v.get('ci') or ''} | {_fmt(v.get('tail_point'))} {v.get('tail_ci') or ''} |")
    lines += ["", "*Table: one row per ladder cell; whole is the paired contrast at the world over all units, tail over the units whose cut event's exact-minus-DOM gap exceeds the family's threshold; the oracle's gap is in each cell's metrics.*", ""]
    lines += ["### Surprise localization", "", "| cell | reader minus DOM AUROC | outcome |", "|---|---|---|"]
    for card in ("D01", "D02", "D04", "D05"):
        v = verdicts.get(card, {})
        lines.append(f"| {card} | {_fmt(v.get('point'))} {v.get('ci') or ''} | {v.get('outcome', 'not run')} |")
    lines += ["", "*Table: per-world paired differences of the surprise AUROC (the reader's surprise identifying the maker's events) against DOM's own; D03 is descriptive in Pass B.*", ""]
    lines += ["### The purpose table", "", "| cell | question | outcome | point |", "|---|---|---|---|"]
    for card in ("G01", "G02", "G03", "G04", "G05", "G06", "G07", "G08"):
        v = verdicts.get(card, {})
        lines.append(f"| {card} | {C.ALL[card]['question'][:90]} | {v.get('outcome', 'not run')} | {_fmt(v.get('point'))} |")
    g05 = _m("G05").get("per_reader") or {}
    lines += ["", f"*Table: the purpose trunk; G05's comparison per reader: {json.dumps({k: v.get('difference_purpose_minus_pull') for k, v in g05.items()})} (positive means the purpose was easier than the pull ordering).*", ""]
    lines += ["### The accumulation table", "", "| cell | question | outcome | point |", "|---|---|---|---|"]
    for card in ("A01", "A02", "A03", "A04", "A05"):
        v = verdicts.get(card, {})
        lines.append(f"| {card} | {C.ALL[card]['question'][:90]} | {v.get('outcome', 'not run')} | {_fmt(v.get('point'))} |")
    a1 = _m("A01").get("per_reader") or {}
    lines += ["", f"*Table: the accumulation trunk; A01's alignment by N per reader: {json.dumps({k: v.get('means_by_n') for k, v in a1.items()})}.*", ""]
    tb = read_registry("TESTBED_SOURCES") or {}
    cm = read_registry("CORPUS_MANIFESTS") or {}
    lines += ["### The testbed", "", f"Clones pinned: {sum(1 for v in (tb.get('clones') or {}).values() if v.get('status') == 'CLONED_PINNED')} of {len(tb.get('clones') or {})}; corpora manifested or in hand: {sum(1 for v in (cm.get('items') or {}).values() if v in ('MANIFESTED', 'IN_HAND'))} of {len(cm.get('items') or {})}; the catalog is in docs/TOOLS.md (T03 {verdicts.get('T03', {}).get('outcome')}).", ""]
    lines += ["### The four answers", ""]
    for i, (q, cards) in enumerate(FOUR, 1):
        ans = "; ".join(f"{c}: {verdicts[c].get('outcome')} ({_fmt(verdicts[c].get('point'))})" for c in cards if c in verdicts) or "not measured"
        lines.append(f"{i}. {q} {ans}.")
    lines += ["", "### Open theory questions (three to six; the analyst prunes)", ""]
    qs = []
    if not any(v.get("passed") for v in eg.values()):
        qs.append("No trained reader passed both prediction and generation with matching identity: which measured failure needs explaining, and what evidence distinguishes its competing explanations?")
    if verdicts.get("E05", {}).get("outcome") == "SUPPORT_CANDIDATE":
        qs.append("An untrained reader passed a gate: what did Stage 7's boundary measure?")
    if (gates.get("difference") or {}).get("passed") is False and any(v.get("admitted") for v in eg.values()):
        qs.append("An admitted reader's surprise did not localize the maker: is the tail threshold, the shape, or the reader the reason?")
    g05d = [v.get("difference_purpose_minus_pull") for v in g05.values() if v.get("difference_purpose_minus_pull") is not None]
    if g05d:
        qs.append(f"The purpose was {'easier' if max(g05d) > 0 else 'not easier'} than the pull ordering: which goal object is the theory's?")
    if verdicts.get("A01", {}).get("outcome") in ("VALID_NULL", "COUNTEREVIDENCE"):
        qs.append("Accumulation did not rise with N: does the maker's share reach the reader only through the law, as Stage 7 found?")
    if verdicts.get("E07", {}).get("outcome") == "SUPPORT_CANDIDATE":
        qs.append("The frontier probe passed the gate cold: is the Stage 7 boundary a small-model boundary?")
    for q in qs[:6]:
        lines.append(f"- {q}")
    lines += ["", "> **STOP READING HERE** (the theory pass is yours; Pass B is the appendix)", "", "## Pass B: analyst appendix", ""]
    dur = contract.duration_report((read_registry("RUNTIME") or {}).get("gpu_lock_seconds", 0.0))
    fr = read_registry("FRONTIER_LEDGER") or {}
    lines.append(f"Elapsed {dur['elapsed_hours']} h; GPU lock held {dur['gpu_lock_held_hours']} h; lost time {dur['lost_hours_recorded']} h; short run {bool(read_registry('SHORT_RUN'))}.")
    lines.append(f"Coverage: {cov.get('complete')}/{cov.get('mandatory_total')} mandatory; outcomes {json.dumps(cov.get('outcomes'))}; rows {cov.get('rows_total')}.")
    lines.append(f"Administrative integrity passed under {cov['validator_version']}; validator source hashes {json.dumps(cov['validator_sources'])}. This does not confer scientific warrant or record curator processing.")
    lines.append(f"Confirmation warrant by explicit claim identity: {json.dumps(cov.get('warrant'))}.")
    lines.append(f"Confirmations: {json.dumps((read_registry('CONFIRMATION_REGISTRY') or {}).get('selected'))}.")
    lines.append(f"Adapters: {json.dumps({k: {'sha': v.get('sha'), 'epoch': v.get('epoch'), 'band_ok': v.get('band_ok'), 'heldout_gap': (v.get('heldout') or {}).get('gap_fm_minus_dom')} for k, v in (read_registry('ADAPTERS') or {}).items()})}.")
    lines.append(f"Frontier: model {json.dumps((fr.get('model') or {}).get('model'))}; total {fr.get('total_usd')} USD of the {fr.get('cap_usd')} cap; by cell {json.dumps(fr.get('by_cell'))}; fixture {json.dumps(fr.get('fixture'))}.")
    lines.append(f"Tail thresholds: {json.dumps(read_registry('TAIL_THRESHOLDS'))}.")
    lines.append(f"Construction facts: {json.dumps(read_registry('CONSTRUCTION_FACTS'))[:1500]}.")
    lines.append(f"Access receipt: all raised {(read_registry('ACCESS_RECEIPT') or {}).get('all_raised')}; boundary {(read_registry('INFORMATION_BOUNDARY') or {}).get('honest_label')}.")
    lines.append(f"Workload lock: {json.dumps({k: v for k, v in (read_registry('WORKLOAD_LOCK') or {}).items() if k in ('base_forecast_h', 'ladder_forecast_h', 'total_forecast_h', 'target_h')})}; re-lock {json.dumps(read_registry('RELOCK'))}.")
    lines.append(f"Repairs: {json.dumps(read_registry('REPAIRS'))}. Interrupts: {json.dumps(interrupts())}.")
    lines.append(f"Fresh clone: {json.dumps((_v('X12') or {}).get('reason'))}. Ledgers: {json.dumps((_v('B03') or {}).get('reason'))}.")
    lines += ["", "### Per-question verdicts", ""]
    for c in list(C.QUESTIONS) + list(C.ATTACKS):
        v = verdicts.get(c)
        if not v:
            lines.append(f"- **{c}**: NO VERDICT")
            continue
        lines.append(f"- **{c}** {v.get('exec')} / {v.get('outcome')}; diagnosis only {bool(v.get('diagnosis_only'))}: {str(v.get('primary', ''))[:140]}; point {_fmt(v.get('point'))}, ci {v.get('ci')}, n {v.get('n_units')}; tail {_fmt(v.get('tail_point'))} {v.get('tail_outcome') or ''}; {str(v.get('reason', ''))[:240]}"
                     + (f"; cells {json.dumps({k: x.get('outcome') for k, x in (v.get('conditional_cells') or {}).items()})[:400]}" if v.get("conditional_cells") else ""))
    return write_packet("\n".join(lines) + "\n", contract, exhausted=bool(contract.data.get("exhausted")))


if __name__ == "__main__":
    try:
        print("packet written:", write_final_packet())
    except PacketGuard as e:
        print("REFUSED:", e)
        sys.exit(2)
