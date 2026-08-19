"""G158 — Phase 2.1.3 stage (a): realization adjudication of the G131 exploratory corpus.

The first corpus recorded what the generator was ASKED, not what it DID (~36% of mechanically
checkable surface instructions were not executed; L137). Before any recovery study can score
against realized choices, every assigned instruction needs a realization verdict:

    --mechanical   CPU, deterministic: every instruction with an exact or approximate string
                   test gets one, graded "exact" (the rule IS the instruction) or "approx"
                   (the rule is a conservative proxy; downstream filters may drop approx).
                   Non-checkable instructions are listed for the reader pass.
    --reader       GPU (ollama, temperature 0): each non-checkable instruction is adjudicated
                   realized / unrealized / ambiguous WITH a required verbatim evidence span
                   (or the word "none"). Model-judged and flagged as such in every record:
                   the adjudicator is the qwen-family reader judging qwen and llama output,
                   so its verdicts on qwen text share a lineage with the text. EXPLORATORY.

DESIGN CHECK (2026-08-19, at design time). Lessons read: LESSONS §3 (incl. the two banked
this pass: gate-met terms; assigned-is-not-realized), §4, §5; CONTROLS 6/7. This stage is
exploratory measurement, no verdict bands and no gates, so nothing here can VOID; the stated
expectations are still derived both ways: under a compliant generator, mechanical pass rates
approach 1.0 per instruction; under an ignoring generator, they approach each check's base
rate on zero-instruction control essays (measured here, from the amount=0 cells, and written
to disk beside the treatment rates). Failure direction of the instrument itself: APPROX
checks over-credit (a loose proxy passes text the instruction would fail), so every verdict
carries its grade and the base-rate column, and the reader pass requires an evidence span so
an over-reading adjudicator is auditable (the G129 A7 lesson: fabrication is measurable only
when the honest no option exists — "unrealized" with span "none" is that option here).

Outputs: results/g158/realization_mechanical.json, results/g158/realization_reader_{family}.json
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
CORPUS = REPO / "corpora" / "g131_factorial"
OUT = REPO / "results" / "g158"
OLLAMA = "http://127.0.0.1:11434/api/generate"
READER_MODEL = "qwen3.5:9b"
DECODING = {"temperature": 0.0, "num_predict": 400}

BUILD_SUFFIX = re.compile(r", and it must build directly on what instruction \d+ produced$")


def sentences(text: str) -> list[str]:
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if s.strip()]


def paragraphs(text: str) -> list[str]:
    return [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]


# every mechanically decidable instruction: name -> (grade, test). "exact" means the string
# rule is the instruction's own criterion; "approx" means a conservative proxy.
def mechanical_check(ins: str, text: str):
    low = ins.lower()
    paras = paragraphs(text)
    sents = sentences(text)
    if low.startswith("address the reader directly as 'you' at least twice"):
        return "exact", len(re.findall(r"\byou\b|\byour\b", text, re.I)) >= 2
    if low.startswith("open with a one-sentence paragraph"):
        return "exact", bool(paras) and len(sentences(paras[0])) == 1
    if low.startswith("use no sentence longer than twenty words"):
        return "exact", all(len(s.split()) <= 20 for s in sents)
    if low.startswith("include exactly one rhetorical question"):
        return "approx", text.count("?") == 1          # a quoted question would also count
    if low.startswith("use a numbered list for exactly one group"):
        starts = [i for i, ln in enumerate(text.splitlines())
                  if re.match(r"^\s*1[.)]\s", ln)]
        return "approx", len(starts) == 1
    if low.startswith("include exactly one parenthetical aside"):
        return "approx", text.count("(") == 1
    if low.startswith("use an em-dash-free, semicolon-free punctuation style"):
        return "exact", ";" not in text and "—" not in text and "--" not in text
    if low.startswith("repeat one chosen phrase at the start of two different paragraphs"):
        if len(paras) < 2:
            return "approx", False
        starts = [" ".join(p.split()[:3]).lower() for p in paras]
        return "approx", len(starts) != len(set(starts))
    if low.startswith("write the final paragraph in second person throughout"):
        last = paras[-1] if paras else ""
        return "approx", bool(re.search(r"\byou\b", last, re.I)) and not re.search(
            r"\b(I|we|my|our)\b", last)
    return None


ADJUDICATE_PROMPT = """You are auditing whether an essay actually executed a writing \
instruction it was given. Judge ONLY what is on the page.

INSTRUCTION: {ins}

ESSAY:
{text}

Answer in exactly this format, three lines:
VERDICT: one word, realized OR unrealized OR ambiguous
EVIDENCE: a verbatim quote from the essay that shows the instruction was executed, or the \
single word none
WHY: one sentence."""


def call_reader(prompt: str) -> str | None:
    req = urllib.request.Request(OLLAMA, data=json.dumps(
        {"model": READER_MODEL, "prompt": prompt, "stream": False, "think": False,
         "options": DECODING}).encode(), headers={"Content-Type": "application/json"})
    for attempt in range(6):
        try:
            with urllib.request.urlopen(req, timeout=600) as r:
                resp = json.loads(r.read()).get("response", "")
            return re.sub(r"<think>.*?</think>", "", resp, flags=re.DOTALL).strip()
        except Exception as e:                                        # noqa: BLE001
            print(f"  reader call failed (attempt {attempt + 1}): {e}")
            time.sleep(20 * (attempt + 1))
    return None


def load_corpus():
    arts = []
    for fam_dir in sorted(CORPUS.iterdir()):
        if not fam_dir.is_dir():
            continue
        for p in sorted(fam_dir.glob("*.json")):
            if p.name != "manifest.json":
                arts.append(json.loads(p.read_text(encoding="utf-8")))
    return arts


def run_mechanical() -> None:
    arts = load_corpus()
    rows, base_rows = [], []
    for a in arts:
        for idx, ins in enumerate(a["instructions"]):
            base = BUILD_SUFFIX.sub("", ins)
            r = mechanical_check(base, a["text"])
            rows.append({"family": a["family"], "artifact_id": a["artifact_id"],
                         "target": a["target"], "amount": a["amount"],
                         "coupling": a["coupling"], "instruction_index": idx,
                         "instruction": ins,
                         "checkable": r is not None,
                         "grade": r[0] if r else None,
                         "realized": r[1] if r else None})
        # base rates: every check evaluated on the zero-instruction control essays,
        # which were never asked for any of this (the DESIGN CHECK's null column)
        if a["amount"] == 0:
            for ins in _all_checkable_surface():
                grade, passed = mechanical_check(ins, a["text"])
                base_rows.append({"family": a["family"],
                                  "artifact_id": a["artifact_id"],
                                  "instruction": ins, "grade": grade,
                                  "passed_unasked": passed})
    checkable = [r for r in rows if r["checkable"]]
    n_pass = sum(1 for r in checkable if r["realized"])
    summary = {
        "n_artifacts": len(arts),
        "n_assignments": len(rows),
        "n_checkable": len(checkable),
        "n_realized": n_pass,
        "checkable_pass_rate": round(n_pass / max(len(checkable), 1), 4),
        "pass_rate_by_grade": {
            g: round(sum(1 for r in checkable if r["grade"] == g and r["realized"])
                     / max(sum(1 for r in checkable if r["grade"] == g), 1), 4)
            for g in ("exact", "approx")},
        "base_rate_unasked": {
            ins: round(sum(1 for b in base_rows if b["instruction"] == ins
                           and b["passed_unasked"])
                       / max(sum(1 for b in base_rows if b["instruction"] == ins), 1), 4)
            for ins in sorted({b["instruction"] for b in base_rows})},
        "n_for_reader": sum(1 for r in rows if not r["checkable"]),
    }
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "realization_mechanical.json").write_text(json.dumps(
        {"summary": summary, "rows": rows, "base_rows": base_rows}, indent=1),
        encoding="utf-8", newline="\n")
    print(json.dumps(summary, indent=1))


def _all_checkable_surface() -> list[str]:
    probe = [
        "address the reader directly as 'you' at least twice",
        "open with a one-sentence paragraph",
        "use no sentence longer than twenty words",
        "include exactly one rhetorical question",
        "use a numbered list for exactly one group of points",
        "include exactly one parenthetical aside",
        "use an em-dash-free, semicolon-free punctuation style",
        "repeat one chosen phrase at the start of two different paragraphs",
        "write the final paragraph in second person throughout",
    ]
    return probe


def run_reader(family: str) -> None:
    sys.path.insert(0, str(REPO))
    from soundingline.gpulock import acquire_gpu_lock                 # noqa: PLC0415
    acquire_gpu_lock(f"g158_reader_{family}")

    mech = json.loads((OUT / "realization_mechanical.json").read_text(encoding="utf-8"))
    todo = [r for r in mech["rows"] if not r["checkable"] and r["family"] == family]
    arts = {a["artifact_id"]: a for a in load_corpus() if a["family"] == family}
    dest = OUT / f"realization_reader_{family}.json"
    done = {}
    if dest.exists():                                   # checkpoint resume
        done = {(r["artifact_id"], r["instruction_index"]): r
                for r in json.loads(dest.read_text(encoding="utf-8"))["rows"]}
    rows = list(done.values())
    for r in todo:
        key = (r["artifact_id"], r["instruction_index"])
        if key in done:
            continue
        text = arts[r["artifact_id"]]["text"]
        base = BUILD_SUFFIX.sub("", r["instruction"])
        resp = call_reader(ADJUDICATE_PROMPT.format(ins=base, text=text))
        verdict = evidence = why = None
        if resp:
            m_v = re.search(r"VERDICT:\s*(realized|unrealized|ambiguous)", resp, re.I)
            m_e = re.search(r"EVIDENCE:\s*(.+)", resp)
            m_w = re.search(r"WHY:\s*(.+)", resp)
            verdict = m_v.group(1).lower() if m_v else None
            evidence = m_e.group(1).strip() if m_e else None
            why = m_w.group(1).strip() if m_w else None
        span_found = bool(evidence) and evidence.lower() != "none" and \
            evidence.strip('"').strip() in text
        rows.append({**r, "verdict": verdict, "evidence": evidence,
                     "evidence_span_verbatim": span_found, "why": why,
                     "adjudicator": READER_MODEL, "model_judged": True,
                     "same_lineage_as_text": family == "qwen"})
        dest.write_text(json.dumps({"rows": rows}, indent=1),
                        encoding="utf-8", newline="\n")
        print(f"{r['artifact_id']}[{r['instruction_index']}]: {verdict} "
              f"(span verbatim: {span_found})")
    counts = {}
    for r in rows:
        counts[r["verdict"] or "no_parse"] = counts.get(r["verdict"] or "no_parse", 0) + 1
    summary = {"family": family, "n": len(rows), "verdicts": counts,
               "span_verbatim_rate": round(sum(1 for r in rows
                                               if r["evidence_span_verbatim"])
                                           / max(len(rows), 1), 4),
               "decoding": DECODING, "adjudicator": READER_MODEL}
    dest.write_text(json.dumps({"summary": summary, "rows": rows}, indent=1),
                    encoding="utf-8", newline="\n")
    print(json.dumps(summary, indent=1))


def run_validate(n_sample: int = 80, seed: int = 15801) -> None:
    """Instrument validation: the reader adjudicates a stratified sample of the
    MECHANICALLY decidable assignments, blind to the mechanical verdicts, and agreement is
    scored. The over-credit direction (reader realized where mechanics say unrealized) is
    the failure the DESIGN CHECK named; zero ambiguous calls in the live arms made this
    the binding check before stage (c) consumes any reader verdict."""
    sys.path.insert(0, str(REPO))
    from soundingline.gpulock import acquire_gpu_lock                 # noqa: PLC0415
    import numpy as np                                                # noqa: PLC0415
    acquire_gpu_lock("g158_reader_validate")

    mech = json.loads((OUT / "realization_mechanical.json").read_text(encoding="utf-8"))
    decided = [r for r in mech["rows"] if r["checkable"]]
    rng = np.random.default_rng(seed)
    # stratify: half mechanically realized, half not, to power both agreement directions
    pos = [r for r in decided if r["realized"]]
    neg = [r for r in decided if not r["realized"]]
    take = lambda pool, k: [pool[i] for i in rng.choice(len(pool), size=min(k, len(pool)),
                                                        replace=False)]
    sample = take(pos, n_sample // 2) + take(neg, n_sample // 2)
    arts = {(a["family"], a["artifact_id"]): a for a in load_corpus()}
    rows = []
    for r in sample:
        text = arts[(r["family"], r["artifact_id"])]["text"]
        base = BUILD_SUFFIX.sub("", r["instruction"])
        resp = call_reader(ADJUDICATE_PROMPT.format(ins=base, text=text))
        m_v = re.search(r"VERDICT:\s*(realized|unrealized|ambiguous)", resp or "", re.I)
        rv = m_v.group(1).lower() if m_v else None
        rows.append({**r, "reader_verdict": rv,
                     "agree": rv == ("realized" if r["realized"] else "unrealized")})
        print(f"{r['artifact_id']}[{r['instruction_index']}] mech="
              f"{'realized' if r['realized'] else 'unrealized'} reader={rv}")
    n = len(rows)
    over = sum(1 for r in rows if not r["realized"] and r["reader_verdict"] == "realized")
    under = sum(1 for r in rows if r["realized"] and r["reader_verdict"] == "unrealized")
    n_neg = sum(1 for r in rows if not r["realized"])
    n_pos = n - n_neg
    summary = {"n": n, "seed": seed,
               "agreement": round(sum(1 for r in rows if r["agree"]) / max(n, 1), 4),
               "over_credit_rate": round(over / max(n_neg, 1), 4),
               "under_credit_rate": round(under / max(n_pos, 1), 4),
               "ambiguous_rate": round(sum(1 for r in rows
                                           if r["reader_verdict"] == "ambiguous")
                                       / max(n, 1), 4),
               "note": "over_credit_rate is the share of mechanically UNREALIZED "
                       "assignments the reader calls realized -- the direction that "
                       "would corrupt stage (c) ground truth; approx-grade mechanical "
                       "verdicts are themselves proxies, so disagreement on approx rows "
                       "is reported but only exact-grade rows are decisive",
               "agreement_exact_grade_only": round(
                   sum(1 for r in rows if r["grade"] == "exact" and r["agree"])
                   / max(sum(1 for r in rows if r["grade"] == "exact"), 1), 4)}
    (OUT / "reader_validation.json").write_text(json.dumps(
        {"summary": summary, "rows": rows}, indent=1), encoding="utf-8", newline="\n")
    print(json.dumps(summary, indent=1))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--mechanical", action="store_true")
    ap.add_argument("--reader", choices=("qwen", "llama"))
    ap.add_argument("--validate", action="store_true")
    args = ap.parse_args()
    if args.mechanical:
        run_mechanical()
    elif args.reader:
        run_reader(args.reader)
    elif args.validate:
        run_validate()
    else:
        ap.error("pass --mechanical, --reader FAMILY, or --validate")


if __name__ == "__main__":
    main()
