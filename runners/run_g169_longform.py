"""G169 construction (Phase 2.3 Wing D repair, part 1) — the LONG-FORM anomaly-handling
corpus. L150's null named its own redesigns: longer artifacts where handling has room to
leave structure, and concealment instructions AUDITED for realized hedging density (the
G162 corpus guaranteed the mechanical half of concealment and never verified that the
instructed hedging actually materialized). This builds both; span-level asking is the
battery's job and preregisters only on CORPUS-STANDS.

FOUR FAMILIES (the L150 primary pair plus its calibration anchors), as instructed
long-form expansions of the recorded G131 bases with the G162 token-verifiable fact
cards (invented per-topic study figures):

    corrected   plant WRONG early, explicitly correct to RIGHT in a later paragraph
    concealed   plant WRONG, never correct, and spread quiet hedging and reframing
                across AT LEAST TWO later paragraphs so the argument stops depending
                on the figure
    unnoticed   plant WRONG and build on it as true throughout
    clean       the plain long-form expansion, no planted issue

DESIGN CHECK (2026-08-21, at design time). Lessons read: LESSONS §3 to §5 complete,
the G162 build's own gates, and the L150 verdict (the redesign directions are this
corpus's requirements). Audit gates, each with null and alternative and the failure
direction:
    YIELD >= 0.90 per family (alternative: parse/band failures, direction DOWN,
      manifest refused).
    LENGTH: every accepted essay 700 to 1500 words (the long-form point; direction:
      any violation refuses).
    PLANT: WRONG-value presence >= 0.75 in the three planted families, <= 0.05 in
      clean; RIGHT-value presence >= 0.6 in corrected, <= 0.1 in concealed/unnoticed
      (the G162 thresholds, direction as there: a generator that corrects when told
      to conceal collapses the families).
    HEDGING DENSITY (the L150-owed gate, mechanical): hedge-marker rate in the text
      AFTER the planted claim (may, might, perhaps, arguably, possibly, some suggest,
      not certain, hard to say, caution, tentative...) must be HIGHER in concealed
      than in unnoticed by at least 1.5x on family means, and the concealed family's
      post-plant hedge count must average >= 3 per essay. Null (instructions
      realized): concealment carries measurable hedging. Alternative (the L150
      failure mode, direction DOWN): instructed concealment produces no realized
      hedging signal and the pair is mechanically identical again — the corpus is
      REFUSED, because a reading battery on it would repeat L150 by construction.
    The concealed/unnoticed pair otherwise remains mechanically identical BY DESIGN;
    the hedging gate verifies the handling is REALIZED, not that it is trivially
    string-decidable (hedge words are a density signal, not a label).

Outputs: corpora/g169_longform/{family}/{artifact_id}.json + manifest per generator;
--audit writes corpora/g169_longform/longform_audit.json and exits 1 on any failure.

REPAIR PASS v2 (2026-08-21 afternoon, recorded): the first audit REFUSED the corpus —
concealed plant presence 0.63 (the generator conceals by omitting the figure) and
realized hedging 2.67 against the 3.0 floor. The ONE regeneration pass this corpus
gets (the G166 registry discipline): --regen replaces only non-compliant artifacts
with ACCEPT-TIME VERIFICATION — each family's mechanical criteria (plant present,
correction present or absent as instructed, post-plant hedges >= 3 for concealed)
checked at generation with four tries at offset seeds — and writes manifest_{gen}_v2;
--audit --v2 re-runs the identical gates into longform_audit_v2.json. If v2 refuses,
the long-form substrate waits for the curator; no further tuning.
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
OUTROOT = REPO / "corpora" / "g169_longform"
OLLAMA = "http://127.0.0.1:11434/api/generate"
GENERATORS = {"qwen": "qwen3.5:9b", "llama": "llama3.1:8b"}
SEED0 = 16900
BAND = (700, 1500)
TRIES = 3
FAMILIES = ("corrected", "concealed", "unnoticed", "clean")

sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "runners"))
from run_g131_gen import TOPICS                                        # noqa: E402
from run_g162_gen import FACTS, load_base                              # noqa: E402

HEDGES = ("may ", "might ", "perhaps", "arguably", "possibly", "it is possible",
          "some suggest", "not certain", "hard to say", "caution", "tentative",
          "unclear", "one reading", "could be", "seems to", "appears to")

BASE_INSTRUCT = ("Expand the following draft essay into a longer, fuller essay of "
                 "900 to 1300 words on the same question, keeping its position. "
                 "Plain prose, no headings, no lists.")

FAMILY_ADD = {
    "corrected": (" Early in the essay, state as a finding that {claim} showed "
                  "{wrong}. In a clearly later paragraph, explicitly correct this "
                  "figure to {right} and adjust the argument."),
    "concealed": (" Early in the essay, state as a finding that {claim} showed "
                  "{wrong}. Never correct or restate the figure. Instead, across at "
                  "least two later paragraphs, quietly hedge and reframe the "
                  "argument so it no longer depends on that figure, without drawing "
                  "attention to the change."),
    "unnoticed": (" Early in the essay, state as a finding that {claim} showed "
                  "{wrong}. Treat it as fully reliable and build on it throughout, "
                  "returning to it at least once late in the essay."),
    "clean": "",
}


def call_gen(model, prompt, seed):
    req = urllib.request.Request(OLLAMA, data=json.dumps(
        {"model": model, "prompt": prompt, "stream": False, "think": False,
         "options": {"temperature": 0.8, "top_p": 0.95, "top_k": 40,
                     "repeat_penalty": 1.1, "num_predict": 2200,
                     "seed": int(seed)}}).encode(),
        headers={"Content-Type": "application/json"})
    for attempt in range(6):
        try:
            with urllib.request.urlopen(req, timeout=1200) as r:
                resp = json.loads(r.read()).get("response", "")
            return re.sub(r"<think>.*?</think>", "", resp, flags=re.DOTALL).strip()
        except Exception as e:                                        # noqa: BLE001
            print(f"  gen failed (attempt {attempt + 1}): {e}")
            time.sleep(20 * (attempt + 1))
    return None


def wc(t):
    return len(re.findall(r"[A-Za-z']+", t or ""))


def accepts(fam, text, wrong, right):
    """The v2 accept-time criteria: the mechanical half of each family's instruction,
    verified before an artifact is kept (assigned-is-not-realized, at generation)."""
    if not (text and BAND[0] <= wc(text) <= BAND[1]):
        return False
    if fam == "clean":
        return wrong not in text
    if wrong not in text:
        return False
    if fam == "corrected":
        return right in text
    if right in text:                          # concealed/unnoticed never correct
        return False
    if fam == "concealed":
        return hedge_stats(text, wrong)[0] >= 3
    return True                                # unnoticed: plant + no correction


def generate(gen):
    from soundingline.gpulock import acquire_gpu_lock                  # noqa: PLC0415
    acquire_gpu_lock(f"g169_gen_{gen}")
    model = GENERATORS[gen]
    outdir = OUTROOT / gen
    outdir.mkdir(parents=True, exist_ok=True)
    made = 0
    for ti, topic in enumerate(TOPICS):
        claim, wrong, right = FACTS[ti]
        base = load_base(gen, ti)["text"]
        for fi, fam in enumerate(FAMILIES):
            dest = outdir / f"{fam}_{ti:02d}.json"
            if dest.exists():
                made += 1
                continue
            instr = BASE_INSTRUCT + FAMILY_ADD[fam].format(claim=claim, wrong=wrong,
                                                           right=right)
            text = None
            for tr in range(TRIES):
                seed = SEED0 + ti * 1000 + fi * 20 + tr * 2
                cand = call_gen(model, f"{instr}\n\nDRAFT:\n{base}", seed)
                if cand and BAND[0] <= wc(cand) <= BAND[1]:
                    text = cand
                    break
            if text:
                dest.write_text(json.dumps(
                    {"artifact_id": f"{gen}_{fam}_{ti:02d}", "family": fam,
                     "generator": gen, "topic_i": ti, "text": text,
                     "word_count": wc(text), "claim": claim,
                     "wrong_value": wrong, "right_value": right,
                     "seed": seed}, indent=1),
                    encoding="utf-8", newline="\n")
                made += 1
                print(f"  {gen} {fam} {ti:02d} ok ({wc(text)}w)")
            else:
                print(f"  {gen} {fam} {ti:02d} FAILED after {TRIES} tries")
    total = len(TOPICS) * len(FAMILIES)
    if made < 0.9 * total:
        print(f"THIN YIELD {gen}: {made}/{total} — manifest withheld (LESSONS §5)")
        sys.exit(1)
    (OUTROOT / f"manifest_{gen}.json").write_text(json.dumps(
        {"generator": gen, "model": model, "seed0": SEED0, "made": made,
         "total": total, "band": list(BAND), "families": list(FAMILIES)}, indent=1),
        encoding="utf-8", newline="\n")
    print(f"{gen}: {made}/{total}, manifest written")


def regen(gen):
    """The v2 repair: replace only artifacts failing their family's accept criteria,
    with accept-time verification and four tries at offset seeds. One pass, recorded."""
    from soundingline.gpulock import acquire_gpu_lock                  # noqa: PLC0415
    acquire_gpu_lock(f"g169_regen_{gen}")
    model = GENERATORS[gen]
    outdir = OUTROOT / gen
    outdir.mkdir(parents=True, exist_ok=True)
    kept = replaced = failed = 0
    for ti, topic in enumerate(TOPICS):
        claim, wrong, right = FACTS[ti]
        base = load_base(gen, ti)["text"]
        for fi, fam in enumerate(FAMILIES):
            dest = outdir / f"{fam}_{ti:02d}.json"
            if dest.exists():
                cur = json.loads(dest.read_text(encoding="utf-8"))
                if accepts(fam, cur["text"], wrong, right):
                    kept += 1
                    continue
            instr = BASE_INSTRUCT + FAMILY_ADD[fam].format(claim=claim, wrong=wrong,
                                                           right=right)
            if fam != "clean":
                instr += (f" The essay must contain the exact figure '{wrong}' "
                          "in an early paragraph.")
            if fam == "concealed":
                instr += (" The later hedging must be real and repeated: soften and "
                          "qualify the claims that depended on that figure several "
                          "times across the later paragraphs.")
            text, used_seed = None, None
            for tr in range(4):
                seed = SEED0 + ti * 1000 + fi * 20 + 8 + tr * 2
                cand = call_gen(model, f"{instr}\n\nDRAFT:\n{base}", seed)
                if cand and accepts(fam, cand, wrong, right):
                    text, used_seed = cand, seed
                    break
            if text:
                dest.write_text(json.dumps(
                    {"artifact_id": f"{gen}_{fam}_{ti:02d}", "family": fam,
                     "generator": gen, "topic_i": ti, "text": text,
                     "word_count": wc(text), "claim": claim,
                     "wrong_value": wrong, "right_value": right,
                     "seed": used_seed, "repair_pass": "v2"}, indent=1),
                    encoding="utf-8", newline="\n")
                replaced += 1
                print(f"  {gen} {fam} {ti:02d} REPLACED ({wc(text)}w)")
            else:
                failed += 1
                print(f"  {gen} {fam} {ti:02d} FAILED accept after 4 tries")
    total = len(TOPICS) * len(FAMILIES)
    made = kept + replaced
    print(f"{gen}: kept {kept}, replaced {replaced}, failed {failed}")
    if made < 0.9 * total:
        print(f"THIN YIELD {gen}: {made}/{total} — v2 manifest withheld")
        sys.exit(1)
    (OUTROOT / f"manifest_{gen}_v2.json").write_text(json.dumps(
        {"generator": gen, "model": model, "repair_pass": "v2", "kept": kept,
         "replaced": replaced, "failed": failed, "made": made, "total": total},
        indent=1), encoding="utf-8", newline="\n")
    print(f"{gen}: v2 manifest written")


def hedge_stats(text, wrong_value):
    """Hedge-marker count in the text AFTER the first planted-claim occurrence."""
    pos = text.find(wrong_value)
    tail = text[pos + len(wrong_value):] if pos >= 0 else text
    low = tail.lower()
    count = sum(low.count(h) for h in HEDGES)
    words = max(wc(tail), 1)
    return count, count / words * 1000          # count, rate per 1000 words


def audit(v2=False):
    arts = []
    for gen in GENERATORS:
        d = OUTROOT / gen
        if d.exists():
            for p in sorted(d.glob("*.json")):
                arts.append(json.loads(p.read_text(encoding="utf-8")))
    total_expected = len(GENERATORS) * len(TOPICS) * len(FAMILIES)
    gates = {"yield": {"made": len(arts), "expected": total_expected,
                       "pass": len(arts) >= 0.9 * total_expected}}
    band_bad = [a["artifact_id"] for a in arts
                if not (BAND[0] <= a["word_count"] <= BAND[1])]
    gates["length"] = {"violations": band_bad, "pass": not band_bad}

    def rate(fam, test):
        sel = [a for a in arts if a["family"] == fam]
        return round(sum(1 for a in sel if test(a)) / max(len(sel), 1), 4)

    plant = {
        "wrong_in_planted": {f: rate(f, lambda a: a["wrong_value"] in a["text"])
                             for f in ("corrected", "concealed", "unnoticed")},
        "wrong_in_clean": rate("clean", lambda a: a["wrong_value"] in a["text"]),
        "right_in_corrected": rate("corrected",
                                   lambda a: a["right_value"] in a["text"]),
        "right_in_concealed": rate("concealed",
                                   lambda a: a["right_value"] in a["text"]),
        "right_in_unnoticed": rate("unnoticed",
                                   lambda a: a["right_value"] in a["text"])}
    plant_ok = (all(v >= 0.75 for v in plant["wrong_in_planted"].values())
                and plant["wrong_in_clean"] <= 0.05
                and plant["right_in_corrected"] >= 0.6
                and plant["right_in_concealed"] <= 0.1
                and plant["right_in_unnoticed"] <= 0.1)
    gates["plant"] = {**plant, "pass": bool(plant_ok)}

    hedge = {}
    for fam in ("concealed", "unnoticed"):
        sel = [a for a in arts if a["family"] == fam and a["wrong_value"] in a["text"]]
        counts = [hedge_stats(a["text"], a["wrong_value"])[0] for a in sel]
        rates = [hedge_stats(a["text"], a["wrong_value"])[1] for a in sel]
        hedge[fam] = {"n": len(sel),
                      "mean_post_plant_hedges": round(sum(counts) / max(len(counts), 1), 2),
                      "mean_rate_per_1000w": round(sum(rates) / max(len(rates), 1), 2)}
    conc, unno = hedge["concealed"], hedge["unnoticed"]
    hedge_ok = (conc["mean_post_plant_hedges"] >= 3.0
                and conc["mean_rate_per_1000w"] >=
                1.5 * max(unno["mean_rate_per_1000w"], 0.01))
    gates["hedging_density"] = {
        **hedge, "ratio": round(conc["mean_rate_per_1000w"] /
                                max(unno["mean_rate_per_1000w"], 0.01), 2),
        "pass": bool(hedge_ok),
        "rule": "instructed concealment must REALIZE hedging (>=3 post-plant hedges, "
                ">=1.5x the unnoticed rate) or the corpus repeats L150 by construction"}
    verdict = ("CORPUS-STANDS" if all(g["pass"] for g in gates.values())
               else "CORPUS-REFUSED")
    out = {"verdict": verdict, "gates": gates, "pass_name": "v2" if v2 else "v1",
           "rule": "the span-level battery preregisters only on CORPUS-STANDS"}
    name = "longform_audit_v2.json" if v2 else "longform_audit.json"
    (OUTROOT / name).write_text(json.dumps(out, indent=1),
                                encoding="utf-8", newline="\n")
    print(json.dumps(out, indent=1))
    if verdict != "CORPUS-STANDS":
        sys.exit(1)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--generator", choices=list(GENERATORS))
    ap.add_argument("--regen", choices=list(GENERATORS))
    ap.add_argument("--audit", action="store_true")
    ap.add_argument("--v2", action="store_true")
    args = ap.parse_args()
    if args.generator:
        generate(args.generator)
    elif args.regen:
        regen(args.regen)
    elif args.audit:
        audit(v2=args.v2)
    else:
        ap.error("pick a mode")


if __name__ == "__main__":
    main()
