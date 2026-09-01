"""The confidence series (READER_HEURISTICS: "the cheapest unbuilt instrument in the file"),
ordered built 2026-09-01. J03-S5 found the reader more confident and less right after an
exact contradiction, measured at one cut; this instrument measures the SERIES: the reader's
stated confidence after each revealed record, beside the exact posterior's information at
the same cut, on the S5R joint worlds. Three questions: does confidence rise when exact
information rises (slope agreement); what happens at each step's answer (correctness beside
confidence); is confidence calibrated over the series? Free path, both admitted readers.
Writes results/phase_2_4_stage_5r/post/CONF_SERIES.json.

DESIGN CHECK (2026-09-01)
lessons read: LESSONS §3 (short candidates: the confidence readout is three single common
  words, surface-matched in case, likelihood-read, never generated — the L139 acquiescence
  signature cannot arise from a likelihood readout; hold the nuisance fixed: option order
  fixed per world across every step; read the baseline marginal before interpreting: the
  three-option battery's marginal is written per reader beside every effect; a manipulation
  check needs dynamic range: worlds whose exact information series is flat are excluded
  from the slope statistic and counted; known answer: a reader emitting constant confidence
  lands slope agreement 0.5 exactly, the analytic chance floor, and the exact information
  series is itself the ruler), §4 (environment versions ride the shared receipt writer),
  §5 (produces guard; the GPU lock inside the runner).
expectations: slope agreement minus 0.5 inside ±0.05 under the null (confidence does not
  track information), at or above +0.05 under the alternative, cluster bootstrap at the
  world, both readers pooled and each apart; calibration is descriptive (ECE over the
  series with its bins written). Direction guarded: reading an artifact of option wording
  as confidence — the per-option marginals and the fixed order are the guards. 96 worlds
  per domain per reader, five cuts each.
"""
from __future__ import annotations

import math
import random
import sys
from pathlib import Path as _P

sys.path.insert(0, str(_P(__file__).resolve().parents[1]))
from runners import s5_receipts as R                                              # noqa: E402  (sets the environment first)
from runners import s5_lib, s5_worlds                                              # noqa: E402
from runners.s5_run_j import ask_latent, candidates, evidence_text                 # noqa: E402
from soundingline.s4 import now_iso                                                # noqa: E402

SEED = s5_lib.SEED0 + 490
OUT = "CONF_SERIES.json"
CONF = {"sure": "sure", "leaning": "leaning", "unsure": "unsure"}
CONF_W = {"sure": 1.0, "leaning": 0.5, "unsure": 0.0}
BAND = 0.05
STEPS = 5


def main() -> int:
    n = 3 if R.SMOKE else 96
    rows = []
    out = {"written_at": now_iso(), "design": "conf-series-1.0", "steps": STEPS,
           "per_option_marginal": {}}
    with s5_lib.GpuSession("s5_conf_series") as gs:
        for reader in s5_lib.READERS:
            model, tok, _ = s5_lib.load_model(reader)
            try:
                for domain in s5_worlds.DOMAINS:
                    for k in range(n):
                        lid = f"CONFS|{domain}|s0|w{k:04d}|series"
                        w = s5_worlds.make_joint_world(lid, domain)
                        cands = candidates(w)
                        rng = random.Random(SEED + k)
                        ent = []
                        for step in range(STEPS):
                            post = s5_worlds.posterior(w, ["contextual", "action"], n_records=step)
                            ent.append(-sum(p * math.log(max(p, 1e-12)) for p in post.values()))
                        info = [ent[0] - e for e in ent]
                        for step in range(STEPS):
                            ev, _ids = evidence_text(w, ("contextual", "action"), n_records=step)
                            aa = ask_latent(model, tok, ev, "episode_goal", cands, {}, rng)
                            correct = aa["valid"] and aa["pred"] == w["episode_goal"]
                            cq = s5_lib.candidate_likelihood(
                                model, tok,
                                f"Evidence about a maker:\n{ev}\nYou just answered a question about the maker's goal. How confident are you?",
                                CONF, rng, unknown=False)
                            conf = sum(CONF_W[o] * cq["probs"][o] for o in CONF) if cq["valid"] else None
                            rows.append({"reader": reader, "unit_id": lid, "domain": domain, "step": step,
                                         "valid": bool(cq["valid"] and aa["valid"]), "confidence": conf,
                                         "answer_correct": bool(correct), "exact_info": info[step],
                                         "probs": cq["probs"] if cq["valid"] else None})
                rd_rows = [r for r in rows if r["reader"] == reader and r["valid"] and r["probs"]]
                out["per_option_marginal"][reader] = {
                    o: sum(r["probs"][o] for r in rd_rows) / max(1, len(rd_rows)) for o in CONF}
            finally:
                s5_lib.free_model(model)
        out["gpu_lock_s"] = gs.held_s

    def analyze(rs):
        rs = [r for r in rs if r["valid"] and r["confidence"] is not None]
        by_world = {}
        for r in rs:
            by_world.setdefault(r["unit_id"], []).append(r)
        agree, flat = [], 0
        for uid, steps in by_world.items():
            steps = sorted(steps, key=lambda r: r["step"])
            moves = [(b["exact_info"] - a["exact_info"], b["confidence"] - a["confidence"])
                     for a, b in zip(steps, steps[1:])]
            moves = [(di, dc) for di, dc in moves if abs(di) > 1e-9]
            if not moves:
                flat += 1
                continue
            score = sum(1.0 if (di > 0) == (dc > 0) else 0.0 for di, dc in moves) / len(moves)
            agree.append({"unit_id": uid, "primary_score": score - 0.5})
        slope = s5_lib.cluster_bootstrap_ci(s5_lib.per_unit_means(agree, "unit_id", "primary_score"), SEED + 11)
        bins = {}
        for r in rs:
            b = round(r["confidence"] * 4) / 4
            bins.setdefault(b, []).append(1.0 if r["answer_correct"] else 0.0)
        ece = sum(len(v) * abs(bk - sum(v) / len(v)) for bk, v in bins.items()) / max(1, len(rs))
        return {"slope_agreement_minus_half": slope, "slope_band": R.classify(slope, BAND),
                "flat_info_worlds_excluded": flat, "ece": ece,
                "calibration_bins": {str(k): [round(sum(v) / len(v), 3), len(v)] for k, v in sorted(bins.items())}}

    out["pooled"] = analyze(rows)
    out["by_reader"] = {rd: analyze([r for r in rows if r["reader"] == rd]) for rd in s5_lib.READERS}
    out["verdict"] = dict(out["pooled"]["slope_band"])
    out["verdict"]["reading"] = ("confidence tracks exact information"
                                 if out["verdict"]["outcome"] == "SUPPORT_CANDIDATE"
                                 else "confidence does not track exact information (the J03 series form)")
    out["rows"] = rows
    R.write(OUT, out)
    p = out["pooled"]
    print("slope", p["slope_agreement_minus_half"].get("point"), "ece", round(p["ece"], 3),
          out["verdict"]["outcome"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
