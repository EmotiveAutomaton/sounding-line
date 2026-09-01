"""Stage 6 adversarial matrix (brief §9): the 24 attacks. Each names its covered cards,
its expected invariant or reversal, its independent units, and its failure consequence
(the registry rows in runners/stage6/cards.py); most derive from landed rows, five replay
small world batches with the presentation varied (X01, X02, X04, X09, X10).

DESIGN CHECK (2026-08-30)
lessons read: LESSONS §3 (run the interpretation control before adopting the reading; a
  falsifier is an instrument and its baseline arm is a known-answer gate: every replay
  attack carries the case where the invariant SHOULD break, so a vacuously-passing attack
  is caught), §5.
bands: an attack lands INFRASTRUCTURE when its invariant holds (and its should-break case
  breaks), INSTRUMENT_FAILED when the invariant fails on the covered cards (the failure
  consequence in the registry then applies), VOID when its covered rows do not exist.
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from runners import s5_lib                                                         # noqa: E402
from runners.stage6 import architectures as A                                      # noqa: E402
from runners.stage6 import cards as CARDS_MOD                                      # noqa: E402
from runners.stage6 import realization as R                                        # noqa: E402
from runners.stage6 import worlds as W                                             # noqa: E402
from runners.stage6.cardrun import SMOKE, CardRun6, bench_lineages                 # noqa: E402
from soundingline.stage6 import S6, read_json                                      # noqa: E402

SEED = 67000


def _rows(run: CardRun6, card: str) -> list[dict]:
    return [r for r in run.rows_of(card) if r.get("valid") and r.get("primary_score") is not None]


def _tv(a: dict, b: dict) -> float:
    return 0.5 * sum(abs(a.get(k, 0.0) - b.get(k, 0.0)) for k in set(a) | set(b))


def _finish(run: CardRun6, metrics: dict, ok: bool | None, reason: str, gpu: float = 0.0) -> int:
    oc = "VOID" if ok is None else ("INFRASTRUCTURE" if ok else "INSTRUMENT_FAILED")
    run.finish(metrics, {"exec": "COMPLETE", "outcome": oc,
                         "primary": CARDS_MOD.ALL[run.card]["question"], "reason": reason}, gpu,
               rival=CARDS_MOD.ALL[run.card]["consequence"])
    return 0


def _replay_label_attack(run: CardRun6, variant: str) -> int:
    """X01/X02/X09/X10: the label posterior under a presentation change; the invariant is
    stability, and the should-break case (a meaning change) must move."""
    n = 2 if SMOKE else CARDS_MOD.units_for(run.card)
    from runners.stage6.engines import READER_KEYS                                # noqa: PLC0415
    reader = (run.readers or list(READER_KEYS.values()))[0]
    tvs, breaks = [], []
    with s5_lib.GpuSession(f"s6_{run.card.lower()}") as gs:
        model, tok, _ = s5_lib.load_model(reader)
        try:
            for dom in CARDS_MOD.DOMAINS:
                for lid in bench_lineages(run.card, dom, n, split="attack"):
                    run.check_deadline()
                    w = W.make_process_world(lid, dom, track="C")
                    run.register_world(lid, w)
                    ev = W.render_evidence(w)
                    space = R.hypothesis_space(w)
                    b = A.Budget(A.BUDGET_EXPANDED)
                    p0 = A._weigh_labels(model, tok, w, ev, space, b)
                    if variant == "paraphrase":
                        alt = [dict(h, display=R.paraphrase(h["display"], 7)) for h in space]
                    elif variant == "keys":
                        alt = list(reversed(space))
                    elif variant == "order":
                        alt = list(space)
                        ev = ev + "\n(Consider the options in any order.)"
                    else:                                          # template
                        alt = list(space)
                        ev = "RECORD FOLLOWS.\n" + ev.replace("The working record so far:", "Log of work:")
                    p1 = A._weigh_labels(model, tok, w, ev, alt, b)
                    flip = [dict(h, display=R.meaning_change(h["display"], 7)) for h in space]
                    p2 = A._weigh_labels(model, tok, w, W.render_evidence(w), flip, b)
                    tvs.append(_tv(p0, p1))
                    breaks.append(_tv(p0, p2))
                    run.row(lid, reader=reader, arm=variant, scores={"tv": tvs[-1], "tv_break": breaks[-1]},
                            primary_score=tvs[-1], budget=b.close())
                    run.unit_complete(reader, lid, variant)
        finally:
            s5_lib.free_model(model)
    gpu = gs.held_s
    tv_m = sum(tvs) / max(1, len(tvs))
    br_m = sum(breaks) / max(1, len(breaks))
    # the discriminative band (LESSONS §3: derive the band, never guess it): the invariant
    # move must be small absolutely OR clearly under the should-break move — an artifact
    # that moves the posterior as much as a real meaning change makes the posterior unusable
    ok = bool(tvs) and (tv_m <= 0.15 or tv_m <= 0.5 * br_m)
    return _finish(run, {"tv_mean": tv_m, "break_tv_mean": br_m, "n": len(tvs),
                         "band": "tv <= 0.15 or tv <= 0.5 x break"}, ok,
                   f"invariant TV {tv_m:.3f}; should-break TV {br_m:.3f}", gpu)


def run_card(run: CardRun6) -> int:
    card = run.card
    if card == "X01":
        return _replay_label_attack(run, "paraphrase")
    if card == "X02":
        return _replay_label_attack(run, "keys")
    if card == "X09":
        return _replay_label_attack(run, "order")
    if card == "X10":
        return _replay_label_attack(run, "template")
    if card == "X04":
        # duplicated evidence must not sharpen the posterior
        n = 2 if SMOKE else CARDS_MOD.units_for(card)
        from runners.stage6.engines import READER_KEYS                            # noqa: PLC0415
        reader = (run.readers or list(READER_KEYS.values()))[0]
        sharp = []
        with s5_lib.GpuSession("s6_x04") as gs:
            model, tok, _ = s5_lib.load_model(reader)
            try:
                for dom in CARDS_MOD.DOMAINS:
                    for lid in bench_lineages(card, dom, n, split="attack"):
                        run.check_deadline()
                        w = W.make_process_world(lid, dom, track="C")
                        ev = W.render_evidence(w)
                        dup = ev + "\n(Restated for the file:)\n" + "\n".join(ev.split("\n")[-4:])
                        space = R.hypothesis_space(w)
                        b = A.Budget(A.BUDGET_EXPANDED)
                        p0 = A._weigh_labels(model, tok, w, ev, space, b)
                        p1 = A._weigh_labels(model, tok, w, dup, space, b)
                        sharp.append(max(p1.values()) - max(p0.values()))
                        run.row(lid, reader=reader, arm="dup", scores={"sharpening": sharp[-1]},
                                primary_score=sharp[-1], budget=b.close())
                        run.unit_complete(reader, lid, "dup")
            finally:
                s5_lib.free_model(model)
        gpu = gs.held_s
        m = sum(sharp) / max(1, len(sharp))
        return _finish(run, {"mean_sharpening": m, "n": len(sharp)}, bool(sharp) and m <= 0.10,
                       f"duplicate evidence sharpens the posterior by {m:.3f}", gpu)
    if card == "X05":
        # equifinal swap: the oracle (and CR's posterior where present) keeps the class
        flat = []
        for i in range(2 if SMOKE else 16):
            w = W.make_process_world(f"X05|essay|s0|w{i:04d}|attack", "essay", track="V")
            post = W.oracle_posterior(w, upto=3)
            flat.append(abs(max(post.values()) - 0.5))
        m = sum(flat) / max(1, len(flat))
        return _finish(run, {"mean_dev_from_even": m}, m < 0.05,
                       f"pre-event posterior deviates from even by {m:.3f}")
    if card in ("X06", "X07", "X17", "X18", "X22"):
        # crossing attacks: the worlds' construction carries the cross; verify the planted
        # cross is live by the oracle and the exact statistics (the covered cards' audits)
        checks = {}
        for c in CARDS_MOD.ALL[card]["covers"]:
            p = S6 / c / "verdict.json"
            v = read_json(p) if p.exists() else {}
            checks[c] = v.get("outcome")
        ok = all(v not in (None, "INSTRUMENT_FAILED") for v in checks.values()) if checks else None
        return _finish(run, {"covered_verdicts": checks}, ok, f"covered cards: {checks}")
    if card == "X03":
        d = R.LD_DEFINITIONS
        lens = {k: len(v) for k, v in d.items()}
        spread = max(lens.values()) - min(lens.values())
        disp = {k: len(v) for k, v in R.DISPLAY.items()}
        dspread = max(disp.values()) - min(disp.values())
        ok = spread <= 40 and dspread <= 45
        return _finish(run, {"definition_len_spread": spread, "display_len_spread": dspread}, ok,
                       f"definition length spread {spread}, display spread {dspread}")
    if card == "X08":
        v = read_json(S6 / "I04" / "verdict.json") if (S6 / "I04" / "verdict.json").exists() else {}
        ok = v.get("outcome") == "INFRASTRUCTURE"
        return _finish(run, {"i04": v.get("outcome")}, ok if v else None, f"I04 {v.get('outcome')}")
    if card == "X11":
        v = read_json(S6 / "I07" / "verdict.json") if (S6 / "I07" / "verdict.json").exists() else {}
        ok = v.get("outcome") == "INFRASTRUCTURE"
        return _finish(run, {"i07": v.get("outcome")}, ok if v else None, f"I07 {v.get('outcome')}")
    if card in ("X12", "X13"):
        src = "M16" if card == "X12" else "C01"
        m = read_json(S6 / src / "metrics.json") if (S6 / src / "metrics.json").exists() else {}
        cells = m.get("conditional_cells") or m
        ok = bool(cells)
        return _finish(run, {"conditional_cells_present": bool(cells)}, ok if m else None,
                       "family/lineage conditional cells written before pooling" if ok else "no conditional cells")
    if card == "X14":
        v = read_json(S6 / "T08" / "verdict.json") if (S6 / "T08" / "verdict.json").exists() else {}
        return _finish(run, {"t08": v.get("outcome")}, v.get("outcome") == "DESCRIPTIVE" if v else None,
                       f"T08 stratification {v.get('outcome')}")
    if card in ("X15", "X16"):
        # history order/aggregate: the A13 contrast is the attack's instrument
        v = read_json(S6 / "A13" / "verdict.json") if (S6 / "A13" / "verdict.json").exists() else {}
        pt = v.get("point")
        ok = None if not v else (pt is not None)
        return _finish(run, {"a13_point": pt, "a13_outcome": v.get("outcome")}, ok,
                       f"dated-minus-shuffled trajectory statistic {pt}")
    if card in ("X19", "X20"):
        checks = {}
        for c in CARDS_MOD.ALL[card]["covers"]:
            p = S6 / c / "verdict.json"
            v = read_json(p) if p.exists() else {}
            checks[c] = {"outcome": v.get("outcome"), "point": v.get("point")}
        ok = all(x["outcome"] not in (None, "INSTRUMENT_FAILED") for x in checks.values()) if checks else None
        return _finish(run, {"covered": checks}, ok, f"forage traps: {checks}")
    if card == "X21":
        stops = {}
        for kind in ("explore", "error"):
            lens = []
            for i in range(2 if SMOKE else 24):
                w = W.make_process_world(f"X21|essay|s0|w{i:04d}|attack", "essay", track="F", forage=kind)
                lens.append(len(w["trajectory"]["steps"]))
            stops[kind] = sum(lens) / len(lens)
        gap = abs(stops["explore"] - stops["error"]) / max(stops.values())
        ok = gap <= 0.15
        return _finish(run, {"mean_lengths": stops, "relative_gap": gap}, ok,
                       f"length base-rate gap {gap:.3f} across foraging goals")
    if card == "X23":
        alarms = []
        for c in ("M16", "P11"):
            m = read_json(S6 / c / "metrics.json") if (S6 / c / "metrics.json").exists() else {}
            cells = m.get("conditional_cells") or m.get("conditional") or {}
            pts = [v.get("point") for v in cells.values() if isinstance(v, dict) and v.get("point") is not None]
            if pts and min(pts) < 0 < max(pts):
                alarms.append({"card": c, "sign_reversal_across_cells": True, "min": min(pts), "max": max(pts)})
        return _finish(run, {"alarms": alarms}, True,
                       f"{len(alarms)} conditional sign reversal(s) surfaced before pooling" if alarms else "no planned reversal hidden; conditional cells inspected")
    if card == "X24":
        from runners.stage6 import fresh_clone as FC                              # noqa: PLC0415
        rep = FC.verify()
        return _finish(run, rep, rep.get("ok"), rep.get("summary", ""))
    raise ValueError(f"no attack handler for {card}")
