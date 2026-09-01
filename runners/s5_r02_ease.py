"""R02 re-run under a validated ease ruler (TODO (m), second half; 2026-08-30). L271 and
L301 could not realize the ease arm: the rendering meant to be harder was the more fluent
text by the mean per-token ruler, then by construction under an invalid ruler. Here the
rendering and the ruler come from EASE_RULER.json (s5_ease_ruler.py): the ruler that
passed the known-answer check, and the rendering it rates hardest. With that arm realized,
the card's question is asked again on both readers: does stated reliance follow a record's
exact information (six records against two, at equal rendering) rather than its ease (plain
against the hard rendering, at equal information)? Writes
results/phase_2_4_stage_5r/post/R02_EASE.json. If no ruler passed, the receipt is VOID and
says why; changes nothing landed.

DESIGN CHECK (2026-08-30)
lessons read: LESSONS §3 (a gate dependency is the gate's VERDICT, not its file: the ruler
  receipt is read at start and a failed validation voids this run; assigned is not
  realized: the fluency of every cell is written under the validated ruler), §5.
expectations: under the null (reliance follows ease, or nothing) the interaction
  (information effect minus ease effect on stated reliance) sits at zero or below; under
  the alternative it reaches 0.03 on the unit reliance scale with the ease effect itself
  reported beside it. The direction guarded is a support built from the quantity effect
  alone while the ease arm is again unrealized, so the ease effect at equal information is
  reported with its own band, and the realization check (the hard rendering's fluency
  under the validated ruler below the plain in at least 0.95 of worlds) is written before
  the contrast. Band: the R02 threshold 0.03; clusters at the world, both readers pooled
  and each apart; 256 worlds per reader.
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
from runners.s5_run_r import RENDERINGS                                            # noqa: E402
from soundingline.s4 import now_iso                                                # noqa: E402

SEED = s5_lib.SEED0 + 460
THRESHOLD = 0.03


def main() -> int:
    ruler_rep = R.read_ruler()
    v = (ruler_rep or {}).get("verdict") or {}
    out = {"written_at": now_iso(), "design": "2", "ruler_receipt": ruler_rep.get("written_at") if ruler_rep else None,
           "ruler": v.get("ruler"), "rendering": v.get("rendering")}
    if not v.get("realized"):
        out["verdict"] = {"outcome": "VOID", "reason": "no ease ruler passed the known-answer validation (EASE_RULER.json); the ease arm cannot be realized"}
        R.write("R02_EASE.json", out)
        print("VOID:", out["verdict"]["reason"])
        return 0
    ruler, render_fn = v["ruler"], RENDERINGS[v["rendering"]]
    n = 3 if R.SMOKE else 128
    rows = []
    with s5_lib.GpuSession("s5_r02_ease") as gs:
        for reader in s5_lib.READERS:
            model, tok, _ = s5_lib.load_model(reader)
            try:
                i = 0
                for domain in s5_worlds.DOMAINS:
                    for k in range(n):
                        i += 1
                        lid = f"R02E|{domain}|s0|w{k:04d}|ease"
                        w = s5_worlds.make_joint_world(lid, domain)
                        target = w["scenarios"][w["target_scenario"]]["draw"]
                        rng = random.Random(SEED + 300 + i)
                        for info_level, n_rec in (("high", 6), ("low", 2)):
                            ev, ids = evidence_text(w, ("contextual", "action"), n_records=n_rec)
                            exact = s5_worlds.predictive(w, s5_worlds.posterior(w, ["contextual", "action"], n_records=n_rec), w["target_scenario"])
                            for ease_level in ("plain", "hard"):
                                text = ev if ease_level == "plain" else render_fn(ev)
                                fluency = R.rulers(R.text_token_logps(model, tok, "A record:", text))[ruler]
                                rel = s5_lib.candidate_likelihood(model, tok, f"Evidence about a maker:\n{text}\nHow much would you rely on this record to predict the maker's next decision?",
                                                                  {"much": "a great deal", "some": "somewhat", "little": "hardly at all"}, rng, unknown=False)
                                reliance = (rel["probs"]["much"] + 0.5 * rel["probs"]["some"]) if rel["valid"] else None
                                p = ask_choice(model, tok, text, w, {}, w["target_scenario"], rng)
                                ls = s5_lib.log_score(p["probs"], target) if p["valid"] else None
                                rows.append({"reader": reader, "unit_id": lid, "domain": domain, "ease": ease_level, "information": info_level,
                                             "primary_score": reliance, "valid": rel["valid"], "prediction_log_score": ls,
                                             "exact_log_score": math.log(max(exact[target], 1e-12)), "fluency": fluency})
            finally:
                s5_lib.free_model(model)
        out["gpu_lock_s"] = gs.held_s

    def analyze(rs: list[dict]) -> dict:
        rs = [r for r in rs if r["valid"] and r["primary_score"] is not None]
        sel = lambda **k: [r for r in rs if all(r[a] == b for a, b in k.items())]        # noqa: E731
        info_eff = s5_lib.paired_contrast(sel(information="high", ease="plain"), sel(information="low", ease="plain"), "unit_id", "primary_score", SEED + 21)
        ease_eff = s5_lib.paired_contrast(sel(ease="plain", information="high"), sel(ease="hard", information="high"), "unit_id", "primary_score", SEED + 22)
        hi = s5_lib.per_unit_means(sel(information="high", ease="plain"), "unit_id", "primary_score")
        lo = s5_lib.per_unit_means(sel(information="low", ease="plain"), "unit_id", "primary_score")
        st = s5_lib.per_unit_means(sel(ease="hard", information="high"), "unit_id", "primary_score")
        inter = {u: (hi[u] - lo[u]) - (hi[u] - st[u]) for u in hi if u in lo and u in st}
        interaction = s5_lib.cluster_bootstrap_ci(inter, SEED + 23)
        # realization: the hard rendering under the validated ruler below the plain, per world
        fl_plain = s5_lib.per_unit_means([dict(r, primary_score=r["fluency"]) for r in sel(ease="plain", information="high")], "unit_id", "primary_score")
        fl_hard = s5_lib.per_unit_means([dict(r, primary_score=r["fluency"]) for r in sel(ease="hard", information="high")], "unit_id", "primary_score")
        harder = [fl_hard[u] < fl_plain[u] for u in fl_plain if u in fl_hard]
        realized_frac = (sum(harder) / len(harder)) if harder else None
        cells = {}
        for e in ("plain", "hard"):
            for inf in ("high", "low"):
                sub = sel(ease=e, information=inf)
                cells[f"{e}|{inf}"] = {"reliance": (sum(r["primary_score"] for r in sub) / len(sub)) if sub else None,
                                       "fluency": (sum(r["fluency"] for r in sub) / len(sub)) if sub else None,
                                       "prediction_log_score": (lambda x: (sum(x) / len(x)) if x else None)([r["prediction_log_score"] for r in sub if r["prediction_log_score"] is not None]),
                                       "n": len(sub)}
        verdict = R.classify(interaction, THRESHOLD)
        if realized_frac is None or realized_frac < 0.95:
            verdict = {"outcome": "INSTRUMENT_FAILED", "reason": f"the ease arm is unrealized under the validated ruler ({realized_frac})", **{k: verdict.get(k) for k in ("point", "ci", "n_units")}}
        return {"ease_arm_realized_fraction": realized_frac, "reliance_information_effect_at_equal_ease": info_eff,
                "reliance_ease_effect_at_equal_information": ease_eff, "ease_effect_band": R.classify(ease_eff, THRESHOLD),
                "interaction_information_minus_ease": interaction, "cells": cells, "verdict": verdict}

    out["pooled"] = analyze(rows)
    out["by_reader"] = {rd: analyze([r for r in rows if r["reader"] == rd]) for rd in s5_lib.READERS}
    out["verdict"] = out["pooled"]["verdict"]
    out["rows"] = rows
    R.write("R02_EASE.json", out)
    p = out["pooled"]
    print("realized", p["ease_arm_realized_fraction"], "info", p["reliance_information_effect_at_equal_ease"].get("point"),
          "ease", p["reliance_ease_effect_at_equal_information"].get("point"), "interaction", p["interaction_information_minus_ease"].get("point"), out["verdict"]["outcome"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
