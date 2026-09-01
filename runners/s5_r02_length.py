"""TODO (m2), opened by L314 (2026-08-30): the R02 quantity effect (stated reliance rises
with six records over two, Qwen +0.15) confounds INFORMATION with LENGTH, since six records
are three times the text of two. This receipt separates them with an information-at-equal-
length construction: a third arm of six records that are the two records repeated three
times, interleaved, verbatim, at plain rendering. The padded arm has the length and count of
six and the information of two. Writes results/phase_2_4_stage_5r/post/R02_LENGTH.json;
changes nothing landed.

DESIGN CHECK (2026-09-01)
lessons read: LESSONS §3 (denominators are declared opportunities: the padded arm's
  length match is measured under each reader's own tokenizer and written before any
  contrast; check that a known-answer construction can exist: a verbatim repeat carries no
  new information by construction, so the padded arm's exact posterior equals the
  two-record arm's, and that identity is asserted at build; a menu whose options differ in
  surface form carries a bias: every record keeps its surface form, only the count of
  distinct records moves; a gate dependency is the gate's verdict: the ease ruler receipt
  is read only for its ruler name, and this run uses plain rendering throughout), §5.
expectations: three paired contrasts on stated reliance at the world. Under the null
  (reliance tracks length or count) six minus padded sits inside ±0.03 and padded minus two
  is at or above +0.03. Under the alternative (reliance tracks information) six minus padded
  is at or above +0.03 and padded minus two inside ±0.03. A third outcome the construction
  can produce: the reader discounts visible repetition, padded minus two at or below −0.03,
  reported as its own band. The direction guarded: crediting information for a quantity
  effect that was length. Bands exhaustive: R.classify at the R02 threshold 0.03 on each
  contrast, both readers pooled and each apart; the length-match check requires the padded
  text within 15 percent of the six-record text in tokens on each reader, else the arm is
  unrealized and the receipt says so. 128 worlds per domain per reader.
"""
from __future__ import annotations

import math
import random
import sys

from pathlib import Path as _P
sys.path.insert(0, str(_P(__file__).resolve().parents[1]))
from runners import s5_receipts as R                                              # noqa: E402  (sets the environment first)
from runners import s5_lib, s5_worlds                                              # noqa: E402
from runners.s5_run_j import ask_choice, evidence_text                             # noqa: E402
from soundingline.s4 import now_iso                                                # noqa: E402

SEED = s5_lib.SEED0 + 480
THRESHOLD = 0.03
OUT = "R02_LENGTH.json"
MATCH_TOL = 0.15


def padded_text(world: dict) -> tuple[str, dict]:
    """Six records that are the two-record evidence repeated three times, interleaved. The
    context block is kept once; the record lines (bullets) are what repeat. Returns the text
    and a construction audit (how the record lines were found)."""
    rt = s5_worlds.route_texts(world, 2)
    ctx = rt["contextual"]["text"]
    act = rt["action"]["text"]
    lines = act.split("\n")
    rec = [ln for ln in lines if ln.lstrip().startswith("- ")]
    head = [ln for ln in lines if not ln.lstrip().startswith("- ")]
    if len(rec) >= 2:
        body = head + rec * 3                                  # a, b, a, b, a, b
        audit = {"path": "bullet_lines", "n_record_lines": len(rec)}
    else:
        body = lines * 3                                       # fallback: the whole block thrice
        audit = {"path": "whole_block", "n_record_lines": len(rec)}
    return ctx + "\n" + "\n".join(body), audit


def main() -> int:
    ruler_rep = R.read_ruler()
    v = (ruler_rep or {}).get("verdict") or {}
    out = {"written_at": now_iso(), "design": "2", "todo": "m2", "ruler": v.get("ruler"), "rendering": "plain"}
    n = 3 if R.SMOKE else 128
    rows = []
    out["length_match"] = {}
    with s5_lib.GpuSession("s5_r02_length") as gs:
        for reader in s5_lib.READERS:
            model, tok, _ = s5_lib.load_model(reader)
            try:
                i = 0
                ratios = []
                audits = {}
                for domain in s5_worlds.DOMAINS:
                    for k in range(n):
                        i += 1
                        lid = f"R02L|{domain}|s0|w{k:04d}|length"
                        w = s5_worlds.make_joint_world(lid, domain)
                        target = w["scenarios"][w["target_scenario"]]["draw"]
                        rng = random.Random(SEED + 300 + i)
                        ev6, _ = evidence_text(w, ("contextual", "action"), n_records=6)
                        ev2, _ = evidence_text(w, ("contextual", "action"), n_records=2)
                        evp, audit = padded_text(w)
                        audits[audit["path"]] = audits.get(audit["path"], 0) + 1
                        ex6 = s5_worlds.predictive(w, s5_worlds.posterior(w, ["contextual", "action"], n_records=6), w["target_scenario"])
                        ex2 = s5_worlds.predictive(w, s5_worlds.posterior(w, ["contextual", "action"], n_records=2), w["target_scenario"])
                        t6 = len(tok(ev6)["input_ids"])
                        tp = len(tok(evp)["input_ids"])
                        ratios.append(tp / max(1, t6))
                        for arm, text, exact in (("six", ev6, ex6), ("two", ev2, ex2), ("padded", evp, ex2)):
                            rel = s5_lib.candidate_likelihood(model, tok, f"Evidence about a maker:\n{text}\nHow much would you rely on this record to predict the maker's next decision?",
                                                              {"much": "a great deal", "some": "somewhat", "little": "hardly at all"}, rng, unknown=False)
                            reliance = (rel["probs"]["much"] + 0.5 * rel["probs"]["some"]) if rel["valid"] else None
                            p = ask_choice(model, tok, text, w, {}, w["target_scenario"], rng)
                            ls = s5_lib.log_score(p["probs"], target) if p["valid"] else None
                            rows.append({"reader": reader, "unit_id": lid, "domain": domain, "arm": arm,
                                         "primary_score": reliance, "valid": rel["valid"], "prediction_log_score": ls,
                                         "exact_log_score": math.log(max(exact[target], 1e-12)), "tokens": len(tok(text)["input_ids"])})
                mean_ratio = sum(ratios) / len(ratios)
                out["length_match"][reader] = {"padded_over_six_tokens": mean_ratio, "matched": abs(mean_ratio - 1.0) <= MATCH_TOL,
                                               "tolerance": MATCH_TOL, "construction_paths": audits}
                print(reader, "padded/six tokens", round(mean_ratio, 3), "matched", abs(mean_ratio - 1.0) <= MATCH_TOL, audits, flush=True)
            finally:
                s5_lib.free_model(model)
        out["gpu_lock_s"] = gs.held_s

    def analyze(rs: list[dict]) -> dict:
        rs = [r for r in rs if r["valid"] and r["primary_score"] is not None]
        sel = lambda **k: [r for r in rs if all(r[a] == b for a, b in k.items())]        # noqa: E731
        info_eq_len = s5_lib.paired_contrast(sel(arm="six"), sel(arm="padded"), "unit_id", "primary_score", SEED + 21)
        len_eq_info = s5_lib.paired_contrast(sel(arm="padded"), sel(arm="two"), "unit_id", "primary_score", SEED + 22)
        quantity = s5_lib.paired_contrast(sel(arm="six"), sel(arm="two"), "unit_id", "primary_score", SEED + 23)
        pred = {arm: s5_lib.cluster_bootstrap_ci(s5_lib.per_unit_means([dict(r, primary_score=r["prediction_log_score"]) for r in sel(arm=arm) if r["prediction_log_score"] is not None],
                                                                        "unit_id", "primary_score"), SEED + 24) for arm in ("six", "two", "padded")}
        bands = {"information_at_equal_length": R.classify(info_eq_len, THRESHOLD),
                 "length_at_equal_information": R.classify(len_eq_info, THRESHOLD),
                 "quantity_total": R.classify(quantity, THRESHOLD)}
        a, b = bands["information_at_equal_length"]["outcome"], bands["length_at_equal_information"]["outcome"]
        if a == "SUPPORT_CANDIDATE" and b in ("VALID_NULL", "INCONCLUSIVE"):
            reading = "reliance tracks information: six beats padded, padded matches two"
        elif b == "SUPPORT_CANDIDATE" and a in ("VALID_NULL", "INCONCLUSIVE"):
            reading = "reliance tracks length or count: padded matches six and beats two"
        elif b == "COUNTEREVIDENCE":
            reading = "the reader discounts visible repetition: padded falls below two"
        elif a == "SUPPORT_CANDIDATE" and b == "SUPPORT_CANDIDATE":
            reading = "both: information and length each raise reliance"
        else:
            reading = "no effect resolved at the band"
        verdict = dict(bands["information_at_equal_length"], reading=reading)
        return {"reliance_information_at_equal_length": info_eq_len, "reliance_length_at_equal_information": len_eq_info,
                "reliance_quantity_six_minus_two": quantity, "prediction_log_score_by_arm": pred, "bands": bands, "verdict": verdict}

    matched = [rd for rd, x in out["length_match"].items() if x["matched"]]
    out["matched_readers"] = matched
    out["pooled"] = analyze([r for r in rows if r["reader"] in matched]) if matched else None
    out["by_reader"] = {rd: analyze([r for r in rows if r["reader"] == rd]) for rd in s5_lib.READERS}
    if not matched:
        out["verdict"] = {"outcome": "INSTRUMENT_FAILED", "reason": f"the padded arm is not length-matched to six records on any reader ({out['length_match']})"}
    else:
        out["verdict"] = out["pooled"]["verdict"]
    out["verdict"]["matched_readers"] = matched
    out["rows"] = rows
    R.write(OUT, out)
    p = out["pooled"] or out["by_reader"][s5_lib.READERS[0]]
    print("matched", matched, "info@len", p["reliance_information_at_equal_length"].get("point"),
          "len@info", p["reliance_length_at_equal_information"].get("point"), "six-two", p["reliance_quantity_six_minus_two"].get("point"),
          out["verdict"].get("outcome"), out["verdict"].get("reading") or out["verdict"].get("reason"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
