"""TODO (s6-t1), opened by the 2026-08-31 Stage-6 update errata and ordered built 2026-09-01:
consolidation-map worlds. The errata's K-update line (K_t+1 ~ L(K_t, E_t, A_t, C_t) + epsilon)
is testable only if attention is specified INDEPENDENTLY of its later effect on expertise.
These worlds do exactly that: an attention schedule is a generative INPUT (drawn from its own
seed, never inferred from K), expertise forms through a lossy consolidation transform (top-m
encoding with chunk reorganization) plus interference noise, and behavior in later episodes
is drawn from the formed expertise. The recoverability question is asked of the EXACT layer
first, before any reader: from behavior and contexts alone, does the exact posterior recover
the true attention schedule beyond the analytic floor, and does modeling the LOSSY map matter
(correct-model recovery minus lossless-assumed recovery)? Free path, CPU only.
Writes results/phase_2_4_aux/S6T1_CONSOLIDATION.json.

DESIGN CHECK (2026-09-01)
lessons read: LESSONS §3 (check that a known-answer design's known answer can exist: the
  eight candidate schedules per world are asserted pairwise behaviorally distinct — minimum
  pairwise TV between their implied final policies above 0.05, one redraw allowed and
  counted; check the criterion CAN fail: the lossless sanity gate below has a reachable
  failure; blind floors follow the truth marginal: one true schedule in eight, floor exactly
  0.125, analytic; validate the ruler on data whose answer you know: the interference-zero,
  top-m-complete arm must recover at 0.95 or better or the instrument is INSTRUMENT_FAILED
  before any claim), §5 (produces guard; CPU only, no GPU lock).
expectations: primary one, posterior mass on the true schedule minus the 0.125 floor at the
  full behavior stream, cluster bootstrap over 128 worlds per domain; under the null
  (behavior does not carry the attention history through the lossy map) inside ±0.05; under
  the alternative at or above +0.10. Primary two, the interference effect: recovery under
  the CORRECT consolidation model minus recovery under a lossless-assumed model of the same
  data; null inside ±0.05, alternative +0.05 or more. Failure directions guarded: exposure
  cannot explain recovery here BY CONSTRUCTION (every candidate schedule sees identical
  contexts, so exposure-only inference sits at the floor analytically), and circularity is
  excluded by seed lineage (the schedule seeds derive from the world id alone). Bands
  exhaustive via the shared classifier.
"""
from __future__ import annotations

import json
import math
import random
import sys
from pathlib import Path as _P

sys.path.insert(0, str(_P(__file__).resolve().parents[1]))
from runners import s5_lib                                                         # noqa: E402
from runners import s5_receipts as R                                               # noqa: E402
from soundingline.s4 import now_iso                                                # noqa: E402

SEED = 71000
OUT = _P(__file__).resolve().parents[1] / "results" / "phase_2_4_aux" / "S6T1_CONSOLIDATION.json"
SLOTS = 8
EPISODES = 10
ATTEND = 3
TOP_M = 2
ETA = 0.9
INTERFERE = 0.15
N_SCHED = 8
CHOICES = 6
DOMAINS = ("essay", "report")
N_WORLDS = 128
BAND = 0.05
FLOOR = 1.0 / N_SCHED
NOISE_DRAWS = 8


def softmax(w):
    m = max(w)
    e = [math.exp(x - m) for x in w]
    z = sum(e)
    return [x / z for x in e]


def form_expertise(schedule, contexts, rng, top_m=TOP_M, interfere=INTERFERE):
    """K after all episodes under the consolidation map: only the top-m attended slots
    encode (compression), an attended pair merges into a chunk (reorganization), and
    non-attended weights decay with rare swaps (interference)."""
    K = [0.0] * SLOTS
    for e in range(EPISODES):
        attended = [s for s in schedule[e] if s in contexts[e]]
        enc = sorted(attended, key=lambda s: K[s], reverse=True)[:top_m]
        for s in enc:
            K[s] += ETA
        if len(enc) >= 2:
            K[min(enc)] += 0.25
        for s in range(SLOTS):
            if s not in attended:
                K[s] *= (1.0 - interfere)
            if interfere > 0 and rng.random() < 0.02:
                j = rng.randrange(SLOTS)
                K[s], K[j] = K[j], K[s]
    return K


def behavior_loglik(schedule, contexts, choices, noise_seed, top_m=TOP_M, interfere=INTERFERE):
    """Exact log-likelihood of the observed choices under a candidate schedule,
    marginalized over interference noise by shared draws."""
    total = 0.0
    for d in range(NOISE_DRAWS):
        rng = random.Random(noise_seed + d)
        K = form_expertise(schedule, contexts, rng, top_m=top_m, interfere=interfere)
        lp = 0.0
        for (offered, picked) in choices:
            p = softmax([K[s] for s in offered])
            lp += math.log(max(p[offered.index(picked)], 1e-12))
        total += math.exp(lp / max(1, len(choices)))
    return math.log(max(total / NOISE_DRAWS, 1e-300))


def make_world(lid, dom, top_m=TOP_M, interfere=INTERFERE):
    rng = random.Random(f"{lid}|{dom}|world")
    contexts = [tuple(sorted(rng.sample(range(SLOTS), 5))) for _ in range(EPISODES)]
    schedules = [tuple(tuple(sorted(rng.sample(range(SLOTS), ATTEND))) for _ in range(EPISODES))
                 for _ in range(N_SCHED)]
    true_i = rng.randrange(N_SCHED)
    noise_seed = rng.randrange(10 ** 9)
    K_true = form_expertise(schedules[true_i], contexts, random.Random(noise_seed),
                            top_m=top_m, interfere=interfere)
    beh_rng = random.Random(f"{lid}|beh")
    choices = []
    for _e in range(EPISODES):
        for _ in range(CHOICES // 2):
            offered = tuple(sorted(beh_rng.sample(range(SLOTS), 3)))
            p = softmax([K_true[s] for s in offered])
            r = beh_rng.random()
            acc, picked = 0.0, offered[-1]
            for s, ps in zip(offered, p):
                acc += ps
                if r <= acc:
                    picked = s
                    break
            choices.append((offered, picked))
    return {"lid": lid, "dom": dom, "contexts": contexts, "schedules": schedules,
            "true_i": true_i, "noise_seed": noise_seed, "choices": choices}


def distinctness(w, top_m=TOP_M, interfere=INTERFERE):
    pols = [softmax(form_expertise(sc, w["contexts"], random.Random(w["noise_seed"]),
                                   top_m=top_m, interfere=interfere)) for sc in w["schedules"]]
    mins = 1.0
    for i in range(len(pols)):
        for j in range(i + 1, len(pols)):
            mins = min(mins, 0.5 * sum(abs(a - b) for a, b in zip(pols[i], pols[j])))
    return mins


def posterior_true_mass(w, top_m=TOP_M, interfere=INTERFERE):
    lls = [behavior_loglik(sc, w["contexts"], w["choices"], w["noise_seed"],
                           top_m=top_m, interfere=interfere) for sc in w["schedules"]]
    m = max(lls)
    ps = [math.exp(x - m) for x in lls]
    return ps[w["true_i"]] / sum(ps)


def main() -> int:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    sane = [posterior_true_mass(make_world(f"S6T1SANE|w{k:03d}", "essay", top_m=ATTEND, interfere=0.0),
                                top_m=ATTEND, interfere=0.0) for k in range(16)]
    sanity = sum(sane) / len(sane)
    out = {"written_at": now_iso(), "todo": "s6-t1", "sanity_lossless_recovery": sanity,
           "sanity_pass": sanity >= 0.95, "floor": FLOOR,
           "constants": {"slots": SLOTS, "episodes": EPISODES, "attend": ATTEND, "top_m": TOP_M,
                         "eta": ETA, "interfere": INTERFERE, "n_sched": N_SCHED}}
    if sanity < 0.95:
        out["verdict"] = {"outcome": "INSTRUMENT_FAILED",
                          "reason": f"the lossless arm recovers only {sanity:.2f}; the exact layer cannot see its own known answer"}
        OUT.write_text(json.dumps(out, indent=1), encoding="utf-8", newline="\n")
        print("INSTRUMENT_FAILED", round(sanity, 3))
        return 0
    rows, redraws = [], 0
    for dom in DOMAINS:
        for k in range(N_WORLDS):
            w = make_world(f"S6T1|{dom}|w{k:04d}", dom)
            if distinctness(w) < 0.05:
                redraws += 1
                w = make_world(f"S6T1|{dom}|w{k:04d}|r1", dom)
            p_correct = posterior_true_mass(w)
            p_lossless_assumed = posterior_true_mass(w, top_m=ATTEND, interfere=0.0)
            rows.append({"unit_id": w["lid"], "dom": dom,
                         "primary_score": p_correct - FLOOR,
                         "interference_effect": p_correct - p_lossless_assumed})
    prim = s5_lib.cluster_bootstrap_ci(s5_lib.per_unit_means(rows, "unit_id", "primary_score"), SEED + 1)
    intf = s5_lib.cluster_bootstrap_ci(s5_lib.per_unit_means(
        [dict(r, primary_score=r["interference_effect"]) for r in rows], "unit_id", "primary_score"), SEED + 2)
    out.update({"n_worlds": len(rows), "redraws": redraws,
                "recovery_minus_floor": prim, "recovery_band": R.classify(prim, 2 * BAND),
                "interference_effect": intf, "interference_band": R.classify(intf, BAND)})
    out["verdict"] = dict(out["recovery_band"],
                          reading=("the attention history is recoverable from behavior through the lossy map"
                                   if out["recovery_band"]["outcome"] == "SUPPORT_CANDIDATE" else
                                   "the lossy map erases the attention history at these constants"))
    out["rows"] = rows
    OUT.write_text(json.dumps(out, indent=1), encoding="utf-8", newline="\n")
    print("sanity", round(sanity, 3), "recovery", prim.get("point"), "interference", intf.get("point"),
          out["verdict"]["outcome"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
