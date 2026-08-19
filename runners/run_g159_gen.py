"""G159 — the rebuilt factorial corpus (Phase 2.1.5 generation arm): paired transformations
of the same base material, with realization crossed as the intervention.

Every constraint here was MEASURED by the G158 foraging battery, not guessed:
  paired base material     the 20 recorded zero-instruction G131 essays are the bases
                           (lineage_id = base artifact id); every cell is a REWRITE of a
                           base, so a delta exists and both contract interfaces (I1
                           artifact-only, I2 paired-delta) can be scored on one corpus
  realization as arm       each (base, instruction set) generates TWO rewrites: R+ is
                           instructed to apply the set; R- is the same rewrite request
                           with NO instructions shown, while the set is recorded as the
                           COUNTERFACTUAL assignment. R- is the realization null: same
                           base, same rewrite pressure, zero execution and zero
                           assignment echo by construction (L140's inseparability, cut
                           at the root)
  echo equalized           candidate decoys are chosen at scoring time to match the
                           truth's content-word overlap with the text (the 0.80
                           assignment-echo bar, L138/L140, neutralized by construction)
  formal vs semantic       surface instructions score mechanically (the reader is chance
                           on constraint satisfaction, L140); problem instructions score
                           by forced choice with a none option (the honest format, L139)
  amounts 1 and 4          single-instruction cells give clean per-instruction
                           realization; coupling is DROPPED from this corpus (it was
                           never verified at output level in G131 and it multiplies
                           cells without serving the realization question)

Cells: 2 families x 10 topics x {surface, problem} x {1, 4} x {R+, R-} = 160 rewrites.
Instruction draws are deterministic per (topic, target, amount) and IDENTICAL across
families and across R+/R- (R- never sees them; they are recorded for candidate sets).

DESIGN CHECK (2026-08-19, at design time; the recovery study preregisters SEPARATELY
after this corpus's realization audit, so no verdict bands live here). Lessons read:
LESSONS §3 to §5 in full, including today's four entries; CONTROLS 6/7. The eventual
gates' expectations, derived now so the corpus is built to serve them: R- recovery
expectation = 1/k under BOTH null and alternative (nothing was executed and nothing
echoes; a read above chance on R- is a candidate-construction leak, direction UP — the
gate the recovery card will carry); R+ minus R- on echo-matched candidates = the
execution effect, the quantity 2.1.5 exists to measure; mechanical realization on R+
expected high (rewrites follow instructions better than cold generation) and measured,
never assumed (the L137 lesson: assigned is not realized — the audit stage gates the
corpus before any recovery study runs); mechanical realization on R- expected at the
unasked base rates already measured in L138. Failure directions of the instrument:
R+ under-realization shrinks usable events (measured by the audit, disclosed, never
padded); R- contamination (a rewrite spontaneously satisfying a counterfactual formal
instruction) is expected at base rates and every R- event's counterfactual set is
mechanically screened at audit time.

Outputs: corpora/g159_rebuild/{family}/{artifact_id}.json; manifest withheld under 90%
yield; --audit writes corpora/g159_rebuild/realization_audit.json (mechanical checks on
R+ and R-, per instruction, with base rates) and exits 1 if R+ exact-grade realization
lands under 0.5 (a corpus that thin repeats G131's defect and does not proceed).
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
OUTROOT = REPO / "corpora" / "g159_rebuild"
OLLAMA = "http://127.0.0.1:11434/api/generate"
FAMILIES = {"qwen": "qwen3.5:9b", "llama": "llama3.1:8b"}
DECODING = {"temperature": 0.8, "top_p": 0.95, "top_k": 40,
            "repeat_penalty": 1.1, "num_predict": 1400}
SEED0 = 15900
BAND = (250, 650)
TRIES = 3

sys.path.insert(0, str(REPO / "runners"))
from run_g131_gen import SURFACE, PROBLEM, TOPICS                      # noqa: E402
from run_g158_adjudicate import mechanical_check, BUILD_SUFFIX         # noqa: E402

REWRITE_PLUS = ("Below is an essay. Rewrite it as a stronger essay on the same topic, "
                "keeping its position. You MUST apply ALL of these revision "
                "instructions:\n{ins}\n\nESSAY:\n{base}\n\nWrite only the rewritten "
                "essay.")
REWRITE_MINUS = ("Below is an essay. Rewrite it as a stronger essay on the same topic, "
                 "keeping its position.\n\nESSAY:\n{base}\n\nWrite only the rewritten "
                 "essay.")


def call(model: str, prompt: str, seed: int) -> str | None:
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


def cells():
    """(cell_index, target, pool, amount, arm) — deterministic enumeration."""
    ci = 0
    for target, pool in (("surface", SURFACE), ("problem", PROBLEM)):
        for amount in (1, 4):
            for arm in ("plus", "minus"):
                yield ci, target, pool, amount, arm
                ci += 1


def draws_for(ti: int, target: str, amount: int, pool: list[str]):
    """Instruction draw deterministic per (topic, target, amount); identical across
    families and across R+/R- by construction."""
    import numpy as np
    key = ti * 100 + (0 if target == "surface" else 1) * 10 + amount
    rng = np.random.default_rng(SEED0 + key)
    idx = sorted(rng.choice(len(pool), size=amount, replace=False).tolist())
    return [pool[i] for i in idx]


def load_bases(family: str) -> dict[int, dict]:
    out = {}
    for ti in range(len(TOPICS)):
        p = BASES / family / f"none_0_none_{ti:02d}.json"
        out[ti] = json.loads(p.read_text(encoding="utf-8"))
    return out


def generate(family: str) -> None:
    from soundingline.gpulock import acquire_gpu_lock                 # noqa: PLC0415
    acquire_gpu_lock(f"g159_gen_{family}")            # once per invocation (LESSONS §5)
    model = FAMILIES[family]
    outdir = OUTROOT / family
    outdir.mkdir(parents=True, exist_ok=True)
    bases = load_bases(family)
    n_expected = 0
    for ti, topic in enumerate(TOPICS):
        base = bases[ti]
        for ci, target, pool, amount, arm in cells():
            n_expected += 1
            aid = f"{target}_{amount}_{arm}_{ti:02d}"
            dest = outdir / f"{aid}.json"
            if dest.exists():
                continue
            instructions = draws_for(ti, target, amount, pool)
            prompt = (REWRITE_PLUS.format(
                ins="\n".join(f"{i + 1}. {s}" for i, s in enumerate(instructions)),
                base=base["text"]) if arm == "plus"
                else REWRITE_MINUS.format(base=base["text"]))
            text = used_seed = None
            for t in range(TRIES):
                s = SEED0 + ti * 1000 + ci * 20 + t   # deterministic, recorded (LESSONS §4)
                cand = call(model, prompt, seed=s)
                if cand and BAND[0] <= len(cand.split()) <= BAND[1]:
                    text, used_seed = cand, s
                    break
                if cand and text is None:
                    text, used_seed = cand, s
            if not text:
                continue
            rec = {"artifact_id": aid, "lineage_id": f"{family}_{base['artifact_id']}",
                   "topic": topic, "target": target, "amount": amount,
                   "realization_arm": arm,
                   "instructions": instructions,
                   "instructions_role": ("applied" if arm == "plus"
                                         else "counterfactual_never_shown"),
                   "family": family, "model_tag": model,
                   "base_words": base["n_words"], "n_words": len(text.split()),
                   "in_band": BAND[0] <= len(text.split()) <= BAND[1],
                   "decoding": {**DECODING, "seed": used_seed},
                   "text": text,
                   "generated_at": time.strftime("%Y-%m-%d %H:%M:%S")}
            dest.write_text(json.dumps(rec, indent=1), encoding="utf-8", newline="\n")
            print(f"{aid}: {rec['n_words']}w in_band={rec['in_band']}")
    n_disk = len([p for p in outdir.glob("*.json") if p.name != "manifest.json"])
    if n_disk < int(0.9 * n_expected):
        print(f"INCOMPLETE: {n_disk}/{n_expected}; manifest withheld, stage retries")
        sys.exit(1)
    (outdir / "manifest.json").write_text(json.dumps(
        {"family": family, "n_on_disk": n_disk, "n_expected": n_expected,
         "design": "2 targets x (1,4) x (plus,minus realization) x 10 topics, "
                   "rewrites of the recorded G131 zero-instruction bases",
         "band": BAND, "seed_rule": "SEED0 + ti*1000 + ci*20 + try; draws "
                                    "SEED0 + ti*100 + target*10 + amount"},
        indent=1), encoding="utf-8", newline="\n")
    print(f"done: {n_disk}/{n_expected} rewrites for {family}")


def audit() -> None:
    """Mechanical realization on R+ (must clear 0.5 exact-grade or the corpus repeats
    G131's defect) and on R- (expected at unasked base rates)."""
    rows = []
    for fam in sorted(FAMILIES):
        d = OUTROOT / fam
        if not (d / "manifest.json").exists():
            print(f"{fam}: manifest missing; audit waits")
            sys.exit(1)
        for p in sorted(d.glob("*.json")):
            if p.name == "manifest.json":
                continue
            r = json.loads(p.read_text(encoding="utf-8"))
            for idx, ins in enumerate(r["instructions"]):
                chk = mechanical_check(BUILD_SUFFIX.sub("", ins), r["text"])
                if chk is None:
                    continue
                rows.append({"family": fam, "artifact_id": r["artifact_id"],
                             "arm": r["realization_arm"], "target": r["target"],
                             "amount": r["amount"], "instruction_index": idx,
                             "instruction": ins, "grade": chk[0], "passed": chk[1]})
    def rate(arm, grade=None):
        sel = [r for r in rows if r["arm"] == arm
               and (grade is None or r["grade"] == grade)]
        return {"n": len(sel),
                "rate": round(sum(1 for r in sel if r["passed"]) / max(len(sel), 1), 4)}
    summary = {"R+_exact": rate("plus", "exact"), "R+_all_checkable": rate("plus"),
               "R-_exact_counterfactual": rate("minus", "exact"),
               "R-_all_checkable_counterfactual": rate("minus")}
    (OUTROOT / "realization_audit.json").write_text(json.dumps(
        {"summary": summary, "rows": rows}, indent=1), encoding="utf-8", newline="\n")
    print(json.dumps(summary, indent=1))
    if summary["R+_exact"]["n"] and summary["R+_exact"]["rate"] < 0.5:
        print("CORPUS FAILS ITS OWN GATE: R+ exact-grade realization under 0.5 — the "
              "G131 defect repeated; the recovery study does NOT proceed on this corpus")
        sys.exit(1)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--family", choices=sorted(FAMILIES))
    ap.add_argument("--audit", action="store_true")
    args = ap.parse_args()
    if args.audit:
        audit()
    elif args.family:
        generate(args.family)
    else:
        ap.error("pass --family F or --audit")


if __name__ == "__main__":
    main()
