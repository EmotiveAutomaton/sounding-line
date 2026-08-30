"""Stage 5 route reliability, ease, and conflict cards (brief §6 R01-R04, §1.3, §4.3).

DESIGN CHECK (2026-08-29)
lessons read: LESSONS §3 (the C03 lesson: a model-choice card is void where the menu's
  exact information does not diverge; fluency is not accuracy, so ease and information are
  crossed by construction; the plain route beside the matched one; a demonstration is
  familiarization, never expertise), CONTROLS §6.
gates and bands:
  - R01 primary: the exact information (nats about the hidden future choice) of the
    route the reader chose minus a random selector's expectation, only on worlds past the
    I04 divergence floor; NULL: 0; ALTERNATIVE: at or above 0.03; the first-listed and
    easiest-route selectors are reported beside it (position and fluency rivals); a world
    under the floor is void, never a failure of active reading.
  - R02 primary: the ease x information interaction on stated reliance: (reliance on the
    high-information route minus the low, at equal ease) minus (reliance on the plain
    rendering minus the stilted, at equal information); NULL: 0; ALTERNATIVE: at or above
    0.03 (reliance follows information, not fluency); reliance following ease alone reads
    as fluency masquerading as reliability, the pre-mortem-7 result.
  - R03 primary: the demonstration x diagnosticity interaction on diagnostic-route use:
    three worked demonstrations of the action route raise its use more on worlds where it
    is diagnostic than where it is not, and misleading demonstrations do the opposite;
    NULL: 0; ALTERNATIVE: at or above 0.05 on the use rate; calibration (expected
    calibration error of the prediction) reported beside it; the word for what changed
    is familiarization.
  - R04 primary: the reader's forensic purchases' realized net gain (log-score gain on
    the target minus the declared cost when bought) minus the random policy's; NULL: 0;
    ALTERNATIVE: at or above 0.03; the exact policy (buy iff expected gain exceeds cost)
    and the always-buy policy bracket it.
verdict bands per card, exhaustive (no silent interval), from the shared classifier on
  the primary's point and its cluster-bootstrap interval against the frozen threshold:
  COUNTEREVIDENCE when the whole interval sits below zero; SUPPORT_CANDIDATE when the
  interval excludes zero and the point reaches the threshold; INCONCLUSIVE when the
  interval excludes zero but the point falls short, or includes zero without excluding
  the threshold; VALID_NULL when the interval includes zero and excludes the threshold;
  every real interval lands in exactly one. Before any interval exists the cell carries
  VOID (no units, or every reader excluded by the gate), INSTRUMENT_FAILED (a validity
  or manipulation gate failed, named in the reason), or NOT_RUN (a dependency died);
  those three are states of the instrument, never evidence about the hypothesis.
"""

from __future__ import annotations

import argparse
import math
import random
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from runners import s5_lib, s5_worlds                                              # noqa: E402
from runners.s5_run_common import (CardRun, DeadlineReached, cluster_by_construction,   # noqa: E402
                                   construction_summary, mean_by, select_rows)
from runners.s5_run_j import ask_choice, evidence_text                             # noqa: E402
from soundingline.stage5 import S5, ece, read_json                                 # noqa: E402

SEED = s5_lib.SEED0 + 400
ROUTE_DESC = {"action": "the maker's record of six earlier decisions and what it chose",
              "semantic": "the maker's own note on the finished piece and what it emphasized",
              "forensic": "a costly close inspection of the piece establishing which step was taken first"}


def _route_info() -> dict:
    ri = read_json(S5 / "ROUTE_INFORMATION.json") if (S5 / "ROUTE_INFORMATION.json").exists() else {"worlds": {}}
    return ri.get("worlds", {})


def _ease(model, tok, text: str) -> float:
    """The ease proxy: mean per-token log-likelihood of the route's evidence text on its
    own (a model fluency measure, declared as such, never subjective fluency)."""
    return s5_lib.option_text_logprobs(model, tok, "A record:", {"t": text})["t"]


def _stilted(text: str) -> str:
    """A stilted rendering of the same records: identical facts, harder reading."""
    return (text.replace("It chose:", "the said maker did elect, as its resolution,")
                .replace("- [", "- Item, marked [").replace("Faced with", "Being confronted with"))


def _stilted2(text: str) -> str:
    """A second candidate rendering (design 2): clause order inverted and hedged, identical facts."""
    out = []
    for line in text.split("\n"):
        if "It chose:" in line:
            a, b = line.split("It chose:", 1)
            line = f"{b.strip()} was, it is recorded, what the maker chose, when {a.strip().lstrip('- ')}"
        line = line.replace("Faced with", "Confronted, as it were, with")
        out.append(line)
    return "\n".join(out)


def _stilted3(text: str) -> str:
    """A third candidate rendering (design 2): every clause interrupted by a parenthetical."""
    return (text.replace(", ", " (so the record has it), ").replace("It chose:", "It chose (the ledger notes):")
                .replace("Faced with", "Faced (the entry states) with"))


def _stilted4(text: str) -> str:
    """A fourth candidate rendering (design 2): the same records in capitals, which fragments
    the reader's tokens; identical facts."""
    return text.upper()


def _stilted5(text: str) -> str:
    """A fifth candidate rendering (design 2): a mid-dot after every word, identical facts."""
    return "\n".join(" · ".join(line.split(" ")) for line in text.split("\n"))


RENDERINGS = {"stilted": _stilted, "stilted2": _stilted2, "stilted3": _stilted3, "stilted4": _stilted4, "stilted5": _stilted5}


def choose_hard_rendering(model, tok, samples: list) -> dict:
    """Design 2 (TODO (m)): the ease manipulation is checked before the card on the reader's
    own token probabilities; the rendering with the lowest fluency below the plain text is
    used, and if none is below the plain text the ease arm is declared unrealized."""
    flu = {"plain": sum(_ease(model, tok, s) for s in samples) / len(samples)}
    for name, fn in RENDERINGS.items():
        flu[name] = sum(_ease(model, tok, fn(s)) for s in samples) / len(samples)
    harder = {k: v for k, v in flu.items() if k != "plain" and v < flu["plain"]}
    chosen = min(harder, key=harder.get) if harder else None
    return {"fluency": flu, "chosen": chosen, "realized": chosen is not None}


# ── R01 ───────────────────────────────────────────────────────────────────────────────

def arm_r01() -> int:
    run = CardRun("R01", "s5_run_r.py")
    info_all = _route_info()
    with s5_lib.GpuSession("s5_r01") as gs:
        for reader in run.readers:
            model, tok, _ = s5_lib.load_model(reader)
            try:
                for domain in s5_worlds.DOMAINS:
                    for i, lid in enumerate(run.units(domain)):
                        if run.is_done(reader, lid):
                            continue
                        run.check_deadline()
                        root = run.parent_of(lid)
                        w = s5_worlds.make_joint_world(root, domain)
                        run.register_world(lid, w)
                        info = info_all.get(root) or s5_worlds.route_information(w)
                        passes = info.get("passes_floor", info["divergence"] >= 0.05)
                        rt = s5_worlds.route_texts(w)
                        rng = random.Random(SEED + i)
                        # design 2 (TODO (l)): each route's description is rendered plain or stilted per
                        # world, so the easiest route is not the same route in every world
                        desc = dict(ROUTE_DESC)
                        rendered = {}
                        if s5_lib.DESIGN == "2":
                            rr = random.Random(SEED + 900 + i)
                            for k in desc:
                                if rr.random() < 0.5:
                                    desc[k] = _stilted3(desc[k])
                                    rendered[k] = "stilted"
                                else:
                                    rendered[k] = "plain"
                        ease = {r: _ease(model, tok, desc[r]) for r in ROUTE_DESC}
                        body = (f"About a maker and one of its pieces you already know this:\n{rt['contextual']['text']}\n"
                                f"You may consult ONE more source before predicting the maker's next decision. Which would tell you most?")
                        r = s5_lib.candidate_likelihood(model, tok, body, desc, rng, unknown=False)
                        chosen = r["pred"] if r["valid"] else None
                        first = r["order"][0] if r["valid"] else None
                        kl = {k: info[k]["kl_from_prior"] for k in ROUTE_DESC}
                        rand = sum(kl.values()) / 3
                        easiest = max(ease, key=ease.get)
                        for name, route in (("model", chosen), ("random", None), ("first", first), ("easiest", easiest), ("exact", info["best"])):
                            val = (kl[route] if route else rand) - rand
                            run.row(reader, lid, lid, f"choice|{name}", {"domain": domain, "choice": name, "passes_floor": passes, **({"control": name} if name in ("random", "first", "easiest") else {})},
                                    info["best"], "construction", "artifact_plus_context", r if name == "model" else None, val if passes else None,
                                    valid=(r["valid"] if name == "model" else True), validity_reason="ok" if (name != "model" or r["valid"]) else r.get("validity_reason"),
                                    extra={"route": route, "kl": kl, "ease": ease, "divergence": info["divergence"], "chosen": chosen})
                        run.unit_complete(reader, lid)
            finally:
                s5_lib.free_model(model)
    rows = [r for r in run.rows() if r["valid"] and r["primary_score"] is not None and r["factors"]["passes_floor"]]
    sel = lambda name: cluster_by_construction(select_rows(rows, choice=name))       # noqa: E731
    primary = s5_lib.cluster_bootstrap_ci(s5_lib.per_unit_means(sel("model"), "unit_id", "primary_score"), SEED + 11)
    others = {n: s5_lib.paired_contrast(sel("model"), sel(n), "unit_id", "primary_score", SEED + 12) for n in ("first", "easiest", "exact")}
    rate = {}
    mrows = select_rows(rows, choice="model")
    for rt in ROUTE_DESC:
        rate[rt] = sum(1 for r in mrows if r["extra"]["chosen"] == rt) / max(1, len(mrows))
    n_void = sum(1 for r in run.rows() if r["factors"]["choice"] == "model" and not r["factors"]["passes_floor"])
    verdict = run.classify(primary, run.threshold(0.03)) if mrows else {"outcome": "VOID", "reason": "no world past the divergence floor"}
    verdict["worlds_void_under_floor"] = n_void
    run.finish({"primary_chosen_minus_random_nats": primary, "model_minus_others": others, "route_choice_rate": rate,
                "constructions": construction_summary(rows), "by_domain": mean_by(rows, ["domain", "choice"])},
               {"exec": "COMPLETE", "primary": "chosen route's exact information minus a random selector, worlds past the floor", **verdict}, gs.held_s,
               rival="position (the first-listed route) and fluency (the easiest route)")
    return 0


# ── R02 ───────────────────────────────────────────────────────────────────────────────

def arm_r02() -> int:
    run = CardRun("R02", "s5_run_r.py")
    render_check = {}
    with s5_lib.GpuSession("s5_r02") as gs:
        for reader in run.readers:
            model, tok, _ = s5_lib.load_model(reader)
            try:
                render_fn = _stilted
                if s5_lib.DESIGN == "2":
                    samples = [evidence_text(s5_worlds.make_joint_world(run.parent_of(lid), dom), ("contextual", "action"), n_records=6)[0]
                               for dom in s5_worlds.DOMAINS for lid in run.units(dom)[:8]]
                    render_check[reader] = choose_hard_rendering(model, tok, samples)
                    render_fn = RENDERINGS[render_check[reader]["chosen"]] if render_check[reader]["realized"] else _stilted
                for domain in s5_worlds.DOMAINS:
                    for i, lid in enumerate(run.units(domain)):
                        if run.is_done(reader, lid):
                            continue
                        run.check_deadline()
                        w = s5_worlds.make_joint_world(run.parent_of(lid), domain)
                        run.register_world(lid, w)
                        target = w["scenarios"][w["target_scenario"]]["draw"]
                        rng = random.Random(SEED + 300 + i)
                        for info_level, n_rec in (("high", 6), ("low", 2)):
                            ev, ids = evidence_text(w, ("contextual", "action"), n_records=n_rec)
                            exact = s5_worlds.predictive(w, s5_worlds.posterior(w, ["contextual", "action"], n_records=n_rec), w["target_scenario"])
                            for ease_level in ("plain", "stilted"):
                                text = ev if ease_level == "plain" else render_fn(ev)
                                fluency = _ease(model, tok, text)
                                rel = s5_lib.candidate_likelihood(model, tok, f"Evidence about a maker:\n{text}\nHow much would you rely on this record to predict the maker's next decision?",
                                                                  {"much": "a great deal", "some": "somewhat", "little": "hardly at all"}, rng, unknown=False)
                                reliance = (rel["probs"]["much"] + 0.5 * rel["probs"]["some"]) if rel["valid"] else None
                                p = ask_choice(model, tok, text, w, {}, w["target_scenario"], rng)
                                ls = s5_lib.log_score(p["probs"], target) if p["valid"] else None
                                run.row(reader, lid, lid, f"{ease_level}|{info_level}", {"domain": domain, "ease": ease_level, "information": info_level},
                                        target, "realized_draw", "artifact_plus_context", p, reliance,
                                        extra={"prediction_log_score": ls, "exact_log_score": math.log(max(exact[target], 1e-12)),
                                               "fluency": fluency, "confidence": max(p["probs"].values()) if p["valid"] else None, "evidence_ids": ids})
                        run.unit_complete(reader, lid)
            finally:
                s5_lib.free_model(model)
    rows = [r for r in run.rows() if r["valid"] and r["primary_score"] is not None]
    sel = lambda **k: cluster_by_construction(select_rows(rows, **k))                 # noqa: E731
    info_eff = s5_lib.paired_contrast(sel(information="high", ease="plain"), sel(information="low", ease="plain"), "unit_id", "primary_score", SEED + 21)
    ease_eff = s5_lib.paired_contrast(sel(ease="plain", information="high"), sel(ease="stilted", information="high"), "unit_id", "primary_score", SEED + 22)
    hi = s5_lib.per_unit_means(sel(information="high", ease="plain"), "unit_id", "primary_score")
    lo = s5_lib.per_unit_means(sel(information="low", ease="plain"), "unit_id", "primary_score")
    st = s5_lib.per_unit_means(sel(ease="stilted", information="high"), "unit_id", "primary_score")
    inter = {u: (hi[u] - lo[u]) - (hi[u] - st[u]) for u in hi if u in lo and u in st}
    interaction = s5_lib.cluster_bootstrap_ci(inter, SEED + 23)
    acc = {k: (lambda m: sum(m.values()) / len(m) if m else None)({u: v for u, v in s5_lib.per_unit_means([dict(r, primary_score=r["extra"]["prediction_log_score"]) for r in select_rows(rows, **dict(zip(("ease", "information"), k.split("|")))) if r["extra"]["prediction_log_score"] is not None], "unit_id", "primary_score").items()})
           for k in ("plain|high", "plain|low", "stilted|high", "stilted|low")}
    flu = mean_by([dict(r, primary_score=r["extra"]["fluency"]) for r in rows], ["ease", "information"])
    verdict = run.classify(interaction, run.threshold(0.03))
    run.finish({"render_check": render_check, "reliance_information_effect_at_equal_ease": info_eff, "reliance_ease_effect_at_equal_information": ease_eff,
                "interaction_information_minus_ease": interaction, "prediction_log_score_by_cell": acc, "fluency_by_cell": flu,
                "constructions": construction_summary(rows)},
               {"exec": "COMPLETE", "primary": "reliance follows exact information beyond fluency (the interaction)", **verdict}, gs.held_s,
               rival="fluency: reliance moving with the rendering at equal information")
    return 0


# ── R03 ───────────────────────────────────────────────────────────────────────────────

def _demos(world: dict, misleading: bool) -> str:
    """Three worked examples: consult the record and predict (helpful), or consult the
    note and predict (misleading, since the note is the weaker route here)."""
    lines = []
    for k in range(3):
        s = world["scenarios"][k]
        if not misleading:
            lines.append(f"Example {k + 1}: consulting the record of decisions, the maker had chosen {s['options'][s['draw']]} when {s['context'][:60]}...; so predict from the record.")
        else:
            lines.append(f"Example {k + 1}: consulting the maker's own note, which stressed {s5_worlds.EMPHASIS_TEXT[world['semantic_named_goal']]}; so predict from the note.")
    return "\n".join(lines) + "\n"


def arm_r03() -> int:
    run = CardRun("R03", "s5_run_r.py")
    info_all = _route_info()
    with s5_lib.GpuSession("s5_r03") as gs:
        for reader in run.readers:
            model, tok, _ = s5_lib.load_model(reader)
            try:
                for domain in s5_worlds.DOMAINS:
                    for i, lid in enumerate(run.units(domain)):
                        if run.is_done(reader, lid):
                            continue
                        run.check_deadline()
                        root = run.parent_of(lid)
                        w = s5_worlds.make_joint_world(root, domain)
                        run.register_world(lid, w)
                        info = info_all.get(root) or s5_worlds.route_information(w)
                        diag = "high" if info["action"]["kl_from_prior"] > info["semantic"]["kl_from_prior"] + 0.05 else "low"
                        rt = s5_worlds.route_texts(w)
                        target = w["scenarios"][w["target_scenario"]]["draw"]
                        rng = random.Random(SEED + 600 + i)
                        for demo in ("none", "three", "misleading"):
                            prefix = "" if demo == "none" else _demos(w, demo == "misleading")
                            body = (f"{prefix}About a maker and one of its pieces you already know this:\n{rt['contextual']['text']}\n"
                                    f"You may consult ONE more source before predicting the maker's next decision. Which would tell you most?")
                            r = s5_lib.candidate_likelihood(model, tok, body, {k: ROUTE_DESC[k] for k in ("action", "semantic")}, rng, unknown=False)
                            chosen = r["pred"] if r["valid"] else None
                            ev = f"{rt['contextual']['text']}\n{rt[chosen]['text']}" if chosen else rt["contextual"]["text"]
                            p = ask_choice(model, tok, prefix + ev, w, {}, w["target_scenario"], rng)
                            run.row(reader, lid, lid, f"{demo}|{diag}", {"domain": domain, "demonstrations": demo, "diagnosticity": diag, **({"control": "misleading"} if demo == "misleading" else {})},
                                    "action", "construction", "artifact_plus_context", r, float(chosen == "action") if chosen else None,
                                    extra={"chosen": chosen, "prediction_log_score": s5_lib.log_score(p["probs"], target) if p["valid"] else None,
                                           "confidence": max(p["probs"].values()) if p["valid"] else None, "correct": p["valid"] and p["pred"] == target})
                        run.unit_complete(reader, lid)
            finally:
                s5_lib.free_model(model)
    rows = [r for r in run.rows() if r["valid"] and r["primary_score"] is not None]
    sel = lambda **k: cluster_by_construction(select_rows(rows, **k))                 # noqa: E731
    use = mean_by(rows, ["demonstrations", "diagnosticity"])
    hi = s5_lib.paired_contrast(sel(demonstrations="three", diagnosticity="high"), sel(demonstrations="none", diagnosticity="high"), "unit_id", "primary_score", SEED + 31)
    lo = s5_lib.paired_contrast(sel(demonstrations="three", diagnosticity="low"), sel(demonstrations="none", diagnosticity="low"), "unit_id", "primary_score", SEED + 32)
    inter_units = {}
    a = s5_lib.per_unit_means(sel(demonstrations="three"), "unit_id", "primary_score")
    b = s5_lib.per_unit_means(sel(demonstrations="none"), "unit_id", "primary_score")
    diag_of = {r["unit_id"]: r["factors"]["diagnosticity"] for r in cluster_by_construction(rows)}
    lo_mean = (lo.get("point") or 0.0)
    for u in a:
        if u in b and diag_of.get(u) == "high":
            inter_units[u] = (a[u] - b[u]) - lo_mean
    interaction = s5_lib.cluster_bootstrap_ci(inter_units, SEED + 33)
    mis = s5_lib.paired_contrast(sel(demonstrations="misleading"), sel(demonstrations="none"), "unit_id", "primary_score", SEED + 34)
    calib = {}
    for demo in ("none", "three", "misleading"):
        sub = select_rows(rows, demonstrations=demo)
        pt = [(r["extra"]["confidence"], r["extra"]["correct"]) for r in sub if r["extra"]["confidence"] is not None]
        calib[demo] = {"ece": ece(pt) if pt else None, "n": len(pt)}
    verdict = run.classify(interaction, run.threshold(0.05))
    run.finish({"diagnostic_route_use": use, "demo_effect_high_diagnosticity": hi, "demo_effect_low_diagnosticity": lo,
                "interaction": interaction, "misleading_minus_none": mis, "calibration": calib, "constructions": construction_summary(rows)},
               {"exec": "COMPLETE", "primary": "demonstration x diagnosticity interaction on diagnostic-route use (familiarization)", **verdict}, gs.held_s,
               rival="a demonstration effect that is confidence only (calibration unchanged, use unchanged)")
    return 0


# ── R04 ───────────────────────────────────────────────────────────────────────────────

def arm_r04() -> int:
    run = CardRun("R04", "s5_run_r.py")
    info_all = _route_info()
    with s5_lib.GpuSession("s5_r04") as gs:
        for reader in run.readers:
            model, tok, _ = s5_lib.load_model(reader)
            try:
                for domain in s5_worlds.DOMAINS:
                    for i, lid in enumerate(run.units(domain)):
                        if run.is_done(reader, lid):
                            continue
                        run.check_deadline()
                        root = run.parent_of(lid)
                        w = s5_worlds.make_joint_world(root, domain)
                        run.register_world(lid, w)
                        info = info_all.get(root) or s5_worlds.route_information(w)
                        cost = w["forensic_cost_nats"]
                        target = w["scenarios"][w["target_scenario"]]["draw"]
                        rng = random.Random(SEED + 900 + i)
                        ev0, _ = evidence_text(w, ("contextual", "action", "semantic"))
                        ev1, _ = evidence_text(w, ("contextual", "action", "semantic", "forensic"))
                        body = (f"Evidence about a maker and one of its pieces:\n{ev0}\nA close inspection of the piece can be bought that would establish "
                                f"which production step was taken first, at a cost worth about {cost:.2f} units of prediction quality. Buy it?")
                        r = s5_lib.candidate_likelihood(model, tok, body, {"buy": "yes, buy the inspection", "decline": "no, predict without it"}, rng, unknown=False)
                        p0 = ask_choice(model, tok, ev0, w, {}, w["target_scenario"], rng)
                        p1 = ask_choice(model, tok, ev1, w, {}, w["target_scenario"], rng)
                        ls0 = s5_lib.log_score(p0["probs"], target) if p0["valid"] else None
                        ls1 = s5_lib.log_score(p1["probs"], target) if p1["valid"] else None
                        if ls0 is None or ls1 is None or not r["valid"]:
                            run.unit_complete(reader, lid)
                            continue
                        realized_gain = ls1 - ls0
                        eig = info["forensic"]["kl_from_prior"]
                        policies = {"model": r["pred"] == "buy", "exact": eig >= cost, "random": rng.random() < 0.5, "always": True}
                        for name, buy in policies.items():
                            net = (realized_gain - cost) if buy else 0.0
                            run.row(reader, lid, lid, f"policy|{name}", {"domain": domain, "policy": name, **({"control": name} if name in ("random", "always") else {})},
                                    target, "realized_draw", "ordered_history" if buy else "artifact_plus_context", r if name == "model" else None, net,
                                    valid=True, validity_reason="ok",
                                    extra={"bought": buy, "realized_gain": realized_gain, "cost": cost, "exact_eig": eig, "p_buy": r["probs"]["buy"]})
                        run.unit_complete(reader, lid)
            finally:
                s5_lib.free_model(model)
    rows = [r for r in run.rows() if r["valid"] and r["primary_score"] is not None]
    sel = lambda name: cluster_by_construction(select_rows(rows, policy=name))       # noqa: E731
    primary = s5_lib.paired_contrast(sel("model"), sel("random"), "unit_id", "primary_score", SEED + 41)
    level = {n: (lambda m: sum(m.values()) / len(m) if m else None)(s5_lib.per_unit_means(sel(n), "unit_id", "primary_score")) for n in ("model", "exact", "random", "always")}
    buy_rate = sum(1 for r in select_rows(rows, policy="model") if r["extra"]["bought"]) / max(1, len(select_rows(rows, policy="model")))
    eig_buy = [(r["extra"]["exact_eig"], r["extra"]["bought"]) for r in select_rows(rows, policy="model")]
    sensitivity = s5_lib.auroc([e for e, b in eig_buy if b], [e for e, b in eig_buy if not b])
    verdict = run.classify(primary, run.threshold(0.03))
    run.finish({"net_gain_by_policy": level, "primary_model_minus_random": primary, "model_buy_rate": buy_rate,
                "buy_decision_tracks_exact_gain_auroc": sensitivity, "constructions": construction_summary(rows)},
               {"exec": "COMPLETE", "primary": "realized net gain per cost of the model's forensic purchases minus random", **verdict}, gs.held_s,
               rival="always buying (the cost-blind policy) and never buying")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--card", required=True, choices=["R01", "R02", "R03", "R04"])
    a = ap.parse_args()
    try:
        return {"R01": arm_r01, "R02": arm_r02, "R03": arm_r03, "R04": arm_r04}[a.card]()
    except DeadlineReached:
        return 3


if __name__ == "__main__":
    sys.exit(main())
