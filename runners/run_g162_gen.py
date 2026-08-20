"""G162 — the process-recorded anomaly-handling text corpus (Phase 2.2D generation arm).

The 2.2C ruler passed (L147), licensing this: the six handling families as INSTRUCTED
REWRITES of the twenty recorded G131 bases, on the G159 machinery, with the planted
issue MECHANICALLY VERIFIABLE wherever the family's definition permits. The load-bearing
construct question, named before generation: does an instructed concealment actually
conceal, and does an instructed correction actually correct? The corpus self-audits on
the mechanically decidable parts before any reading battery preregisters (the L137
assigned-is-not-realized rule; the G159 precedent).

THE PLANTED ISSUE is token-verifiable by design: each essay's instruction embeds one
FALSE NUMERIC CLAIM from a per-topic fact card ("state that <fact> is <WRONG>", truth
<RIGHT> recorded), so presence, correction, and repetition are string-testable:

    corrected    plant the false claim early, then later explicitly correct it to the
                 recorded true value ("in fact", "correction", or restating <RIGHT>)
                 -- audit: WRONG appears, RIGHT appears later
    concealed    plant the false claim, never correct it, and hedge or reframe around
                 it so the essay still works -- audit: WRONG appears, RIGHT absent;
                 the hedging itself is the reading battery's object, not the audit's
    unnoticed    plant the false claim and simply continue -- audit: WRONG appears,
                 RIGHT absent (separated from concealed only by the reading battery;
                 the corpus records the INSTRUCTED handling as ground truth)
    repeated     plant the false claim at least three times -- audit: WRONG appears
                 three or more times
    deliberate   include one unusual-but-purposeful construction (a one-sentence
                 paragraph refrain) serving a declared secondary purpose -- audit:
                 the refrain is string-testable; no false claim planted
    clean        the plain rewrite, no issue (the G159 R- machinery verbatim)

DESIGN CHECK (2026-08-20, at design time). Lessons read: LESSONS §3 to §5 complete,
CONTROLS 6/7, the L147 iteration lessons (categorical span-level anomalies, consequence
structure, negative-class-heavy validation) and L148's echo-split standing rule.
Expectations both ways for the audit gates: under compliant generation the WRONG-claim
presence rate approaches 1.0 in the five planted families and 0.0 in clean; under the
G131 failure mode it falls toward the low compliance rates already measured (0.586-ish),
and the corpus self-gate REFUSES the reading battery below 0.6 presence in planted
families or above 0.05 contamination in clean. Correction-marker audit: RIGHT-value
presence must be >= 0.6 in corrected and <= 0.1 in concealed/unnoticed (direction of the
failure: a generator that corrects when told to conceal collapses the families).
Repetition: >= 3 occurrences in repeated at >= 0.6. The concealed/unnoticed pair is
DELIBERATELY not mechanically separable (concealment is low-visibility by definition);
their separation is the reading battery's question and the corpus only guarantees their
shared mechanical half. Seeds deterministic (SEED0 + indices), recorded; yield guard at
90%; families identical across generators; lineage to bases.

Outputs: corpora/g162_anomaly/{family}/{artifact_id}.json + manifest; --audit writes
corpora/g162_anomaly/handling_audit.json and exits 1 on any gate failure.
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
BASES = REPO / "corpora" / "g131_factorial"
OUTROOT = REPO / "corpora" / "g162_anomaly"
OLLAMA = "http://127.0.0.1:11434/api/generate"
GENERATORS = {"qwen": "qwen3.5:9b", "llama": "llama3.1:8b"}
DECODING = {"temperature": 0.8, "top_p": 0.95, "top_k": 40,
            "repeat_penalty": 1.1, "num_predict": 1400}
SEED0 = 16200
BAND = (250, 700)
TRIES = 3

sys.path.insert(0, str(REPO / "runners"))
from run_g131_gen import TOPICS                                        # noqa: E402

# per-topic fact cards: (claim template, WRONG value, RIGHT value). Values are invented
# study figures so no real-world fact is misstated outside the construction; WRONG and
# RIGHT are distinctive strings a tokenizer cannot produce by accident.
FACTS = [("a recent survey of city-center car bans", "73 percent", "37 percent"),
         ("a study of handwriting instruction hours", "88 minutes", "48 minutes"),
         ("a review of publicly owned clubs", "61 clubs", "16 clubs"),
         ("a report on age-verification uptake", "92 percent", "29 percent"),
         ("an analysis of space-agency budgets", "54 billion", "45 billion"),
         ("a museum repatriation census", "77 institutions", "27 institutions"),
         ("a tipping-abolition trial", "83 restaurants", "38 restaurants"),
         ("a compulsory-voting comparison", "95 percent", "59 percent"),
         ("a remote-work legislation tally", "66 countries", "26 countries"),
         ("a zoo-accreditation audit", "84 facilities", "44 facilities")]

REFRAIN = "The point stands."

FAMILY_INSTRUCTIONS = {
    "corrected": ("While rewriting, early in the essay cite {src} as finding {wrong}. "
                  "Later in the essay, explicitly correct that figure to {right}, "
                  "acknowledging the earlier number was mistaken."),
    "concealed": ("While rewriting, early in the essay cite {src} as finding {wrong}. "
                  "Do NOT correct the figure anywhere. Instead, later in the essay, "
                  "quietly hedge and reframe the argument so it no longer depends on "
                  "that figure, without drawing attention to it."),
    "unnoticed": ("While rewriting, early in the essay cite {src} as finding {wrong}. "
                  "Treat the figure as correct throughout and build on it."),
    "repeated": ("While rewriting, cite {src} as finding {wrong}, and repeat that "
                 "figure at least three separate times across the essay."),
    "deliberate": ("While rewriting, end at least three different paragraphs with the "
                   "exact standalone sentence '" + REFRAIN + "' as a deliberate "
                   "rhetorical refrain."),
    "clean": None,
}
FAMILIES = list(FAMILY_INSTRUCTIONS)

REWRITE = ("Below is an essay. Rewrite it as a stronger essay on the same topic, keeping "
           "its position.{extra}\n\nESSAY:\n{base}\n\nWrite only the rewritten essay.")


def call(model, prompt, seed):
    req = urllib.request.Request(OLLAMA, data=json.dumps(
        {"model": model, "prompt": prompt, "stream": False, "think": False,
         "options": {**DECODING, "seed": seed}}).encode(),
        headers={"Content-Type": "application/json"})
    for attempt in range(6):
        try:
            with urllib.request.urlopen(req, timeout=900) as r:
                resp = json.loads(r.read()).get("response", "")
            return re.sub(r"<think>.*?</think>", "", resp, flags=re.DOTALL).strip()
        except Exception as e:                                        # noqa: BLE001
            print(f"  call failed (attempt {attempt + 1}): {e}")
            time.sleep(20 * (attempt + 1))
    return None


def load_base(gen, ti):
    p = BASES / gen / f"none_0_none_{ti:02d}.json"
    return json.loads(p.read_text(encoding="utf-8"))


def generate(gen: str) -> None:
    sys.path.insert(0, str(REPO))
    from soundingline.gpulock import acquire_gpu_lock                 # noqa: PLC0415
    acquire_gpu_lock(f"g162_gen_{gen}")                # once per invocation (LESSONS §5)
    model = GENERATORS[gen]
    n_expected = 0
    for ti, topic in enumerate(TOPICS):
        base = load_base(gen, ti)
        src, wrong, right = FACTS[ti]
        for fi, fam in enumerate(FAMILIES):
            n_expected += 1
            outdir = OUTROOT / fam
            outdir.mkdir(parents=True, exist_ok=True)
            aid = f"{fam}_{gen}_{ti:02d}"
            dest = outdir / f"{aid}.json"
            if dest.exists():
                continue
            tpl = FAMILY_INSTRUCTIONS[fam]
            extra = ("" if tpl is None else
                     " " + tpl.format(src=src, wrong=wrong, right=right))
            prompt = REWRITE.format(extra=extra, base=base["text"])
            text = used_seed = None
            for t in range(TRIES):
                s = SEED0 + ti * 1000 + fi * 20 + t
                cand = call(model, prompt, seed=s)
                if cand and BAND[0] <= len(cand.split()) <= BAND[1]:
                    text, used_seed = cand, s
                    break
                if cand and text is None:
                    text, used_seed = cand, s
            if not text:
                continue
            rec = {"artifact_id": aid, "family": fam, "generator": gen,
                   "lineage_id": f"{gen}_{base['artifact_id']}", "topic": topic,
                   "fact_source": src, "wrong_value": wrong, "right_value": right,
                   "refrain": REFRAIN if fam == "deliberate" else None,
                   "instructed_handling": fam,
                   "decoding": {**DECODING, "seed": used_seed},
                   "n_words": len(text.split()),
                   "in_band": BAND[0] <= len(text.split()) <= BAND[1],
                   "text": text, "generated_at": time.strftime("%Y-%m-%d %H:%M:%S")}
            dest.write_text(json.dumps(rec, indent=1), encoding="utf-8", newline="\n")
            print(f"{aid}: {rec['n_words']}w in_band={rec['in_band']}")
    n_disk = sum(1 for fam in FAMILIES
                 for p in (OUTROOT / fam).glob(f"*_{gen}_*.json"))
    if n_disk < int(0.9 * n_expected):
        print(f"INCOMPLETE: {n_disk}/{n_expected}; manifest withheld, stage retries")
        sys.exit(1)
    (OUTROOT / f"manifest_{gen}.json").write_text(json.dumps(
        {"generator": gen, "n_on_disk": n_disk, "n_expected": n_expected,
         "families": FAMILIES, "band": BAND,
         "seed_rule": "SEED0 + ti*1000 + fi*20 + try"}, indent=1),
        encoding="utf-8", newline="\n")
    print(f"done: {n_disk}/{n_expected} for {gen}")


def audit() -> None:
    """Mechanical handling audit; exits 1 on any self-gate failure (the corpus refuses
    the reading battery)."""
    for gen in GENERATORS:
        if not (OUTROOT / f"manifest_{gen}.json").exists():
            print(f"{gen}: manifest missing; audit waits")
            sys.exit(1)
    rows = []
    for fam in FAMILIES:
        for p in sorted((OUTROOT / fam).glob("*.json")):
            r = json.loads(p.read_text(encoding="utf-8"))
            text = r["text"]
            rows.append({
                "family": fam, "artifact_id": r["artifact_id"],
                "wrong_present": r["wrong_value"] in text,
                "wrong_count": text.count(r["wrong_value"]),
                "right_present": r["right_value"] in text,
                "refrain_count": text.count(REFRAIN)})

    def rate(fam, fn):
        sel = [r for r in rows if r["family"] == fam]
        return round(sum(1 for r in sel if fn(r)) / max(len(sel), 1), 4)

    summary = {
        "wrong_presence": {f: rate(f, lambda r: r["wrong_present"])
                           for f in FAMILIES if f not in ("deliberate", "clean")},
        "clean_contamination": rate("clean", lambda r: r["wrong_present"]),
        "corrected_has_right": rate("corrected", lambda r: r["right_present"]),
        "concealed_has_right": rate("concealed", lambda r: r["right_present"]),
        "unnoticed_has_right": rate("unnoticed", lambda r: r["right_present"]),
        "repeated_3plus": rate("repeated", lambda r: r["wrong_count"] >= 3),
        "deliberate_refrain_3plus": rate("deliberate", lambda r: r["refrain_count"] >= 3),
    }
    gates = {
        "presence": all(v >= 0.6 for v in summary["wrong_presence"].values()),
        "clean": summary["clean_contamination"] <= 0.05,
        "corrected": summary["corrected_has_right"] >= 0.6,
        "concealment_not_corrected": summary["concealed_has_right"] <= 0.1
                                     and summary["unnoticed_has_right"] <= 0.1,
        "repetition": summary["repeated_3plus"] >= 0.6,
        "deliberate": summary["deliberate_refrain_3plus"] >= 0.6,
    }
    verdict = "CORPUS-STANDS" if all(gates.values()) else "CORPUS-FAILS-SELF-GATE"
    (OUTROOT / "handling_audit.json").write_text(json.dumps(
        {"summary": summary, "gates": gates, "verdict": verdict, "rows": rows},
        indent=1), encoding="utf-8", newline="\n")
    print(json.dumps({"summary": summary, "gates": gates, "verdict": verdict}, indent=1))
    if verdict != "CORPUS-STANDS":
        print("the reading battery does NOT preregister on this corpus")
        sys.exit(1)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--generator", choices=sorted(GENERATORS))
    ap.add_argument("--audit", action="store_true")
    args = ap.parse_args()
    if args.audit:
        audit()
    elif args.generator:
        generate(args.generator)
    else:
        ap.error("pass --generator G or --audit")


if __name__ == "__main__":
    main()
