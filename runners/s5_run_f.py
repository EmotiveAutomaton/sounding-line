"""Stage 5 interest and epistemic-foraging cards (brief §6 F01-F03, §1.6).

DESIGN CHECK (2026-08-29)
lessons read: LESSONS §3 (a criterion that can fail: random noise must not read as
  interesting; the readout is evidence CHOICE, never a stated interest; exact rulers
  before any reader; the matched comparator and the raw baselines both reported),
  CONTROLS §6.
gates and bands:
  - F01: the reader's likelihood over which of six items to examine next, against the
    exact rulers (novelty, complexity, prediction error, learning progress, reducible
    structure); descriptive: the rank correlation with each ruler within a set,
    averaged over sets, and the mean rank of each item class; no outcome band, but the
    instrument fails if the ranking is flat (the top item's mass under 0.25 on average).
  - F02 primary: the realized held-out gain per unit cost of the reader's selection
    minus the best raw-signal baseline (novelty, surprise, random); NULL: 0;
    ALTERNATIVE: at or above 0.03 nats; the exact learning-progress policy is the
    ceiling; a reader that picks the random-unlearnable item for its surprise realizes
    nothing, which is the pre-mortem-11 result read correctly.
  - F03 primary: pursuit of the attractive explanation on hope-incongruent worlds
    (where it is weakly supported) under the plain prompt minus under the counter-bias
    prompt; NULL: 0 (hope does not steer selection); ALTERNATIVE: pursuit above support
    with a false-discovery rate above 0.25 that the counter-bias prompt reduces; posterior
    confidence is reported beside selection so that pursuit and warrant stay apart.
  under the null the reader's examination choice is flat over the six items (every
  ruler's rank correlation 0, realized gain equal to a random selector's); under the
  alternative the choice tracks a named ruler with a positive rank correlation and the
  realized gain exceeds the random selector's by at least the threshold; the failure
  direction guarded is a preference for the random item (noise read as interesting),
  which the reducible-structure ruler and the random-selector baseline expose.
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
import random
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from runners import s5_lib, s5_worlds                                              # noqa: E402
from runners.s5_run_common import (CardRun, DeadlineReached, cluster_by_construction,   # noqa: E402
                                   construction_summary, mean_by, select_rows)

SEED = s5_lib.SEED0 + 600
CLASSES = s5_worlds.ITEM_CLASSES


def _spearman(a: list, b: list) -> float | None:
    n = len(a)
    if n < 3:
        return None
    ra = {v: i for i, v in enumerate(sorted(range(n), key=lambda i: a[i]))}
    rb = {v: i for i, v in enumerate(sorted(range(n), key=lambda i: b[i]))}
    d2 = sum((ra[i] - rb[i]) ** 2 for i in range(n))
    return 1 - 6 * d2 / (n * (n * n - 1))


def _listing(fs: dict, show: int = s5_worlds.FORAGE_SHOWN) -> tuple[str, dict]:
    opts = {}
    text = []
    for k, (name, it) in enumerate(fs["items"].items()):
        opts[name] = f"sequence {k + 1}"
        text.append(f"sequence {k + 1}: " + ", ".join(str(x) for x in it["seq"][:show]) + ", ..." +
                    (f" (rule stated: {it['rule']})" if it["stated"] else ""))
    return "\n".join(text), opts


def _next_options(it: dict, rng: random.Random, at: int) -> dict:
    truth = it["seq"][at]
    pool = {truth}
    while len(pool) < 4:
        pool.add(truth + rng.choice([-7, -3, -1, 1, 2, 5, 9, 11]))
    return {str(v): str(v) for v in sorted(pool)}


# ── F01 ───────────────────────────────────────────────────────────────────────────────

def arm_f01() -> int:
    run = CardRun("F01", "s5_run_f.py")
    with s5_lib.GpuSession("s5_f01") as gs:
        for reader in run.readers:
            model, tok, _ = s5_lib.load_model(reader)
            try:
                for i, lid in enumerate(run.units("all")):
                    if run.is_done(reader, lid):
                        continue
                    run.check_deadline()
                    fs = s5_worlds.make_foraging_set(lid)
                    run.register_world(lid, fs)
                    listing, opts = _listing(fs)
                    rng = random.Random(SEED + i)
                    body = (f"Six number sequences, three elements shown of each:\n{listing}\n"
                            f"You may examine ONE of them further (two more elements) to learn its rule. Which would you examine?")
                    r = s5_lib.candidate_likelihood(model, tok, body, opts, rng, unknown=False)
                    if not r["valid"]:
                        run.unit_complete(reader, lid)
                        continue
                    names = list(fs["items"])
                    probs = [r["probs"][n] for n in names]
                    corr = {}
                    for ruler in ("novelty", "complexity", "prediction_error", "learning_progress"):
                        corr[ruler] = _spearman(probs, [fs["rulers"][n][ruler] for n in names])
                    corr["reducible"] = _spearman(probs, [1.0 if fs["rulers"][n]["reducible"] else 0.0 for n in names])
                    for n in names:
                        run.row(reader, lid, lid, f"rank|{n}", {"domain": "all", "item_class": n}, None, "construction", "artifact_only", r,
                                r["probs"][n], extra={"rulers": fs["rulers"][n], "correlations": corr, "top": r["pred"],
                                                      "rank": sorted(names, key=lambda x: -r["probs"][x]).index(n) + 1})
                    run.unit_complete(reader, lid)
            finally:
                s5_lib.free_model(model)
    rows = [r for r in run.rows() if r["valid"] and r["primary_score"] is not None]
    per_class = mean_by(rows, ["item_class"])
    ranks = {c: sum(r["extra"]["rank"] for r in rows if r["factors"]["item_class"] == c) / max(1, sum(1 for r in rows if r["factors"]["item_class"] == c)) for c in CLASSES}
    corr = {}
    firsts = [r for r in rows if r["factors"]["item_class"] == CLASSES[0]]
    for ruler in ("novelty", "complexity", "prediction_error", "learning_progress", "reducible"):
        vals = [r["extra"]["correlations"][ruler] for r in firsts if r["extra"]["correlations"].get(ruler) is not None]
        corr[ruler] = (sum(vals) / len(vals)) if vals else None
    top_mass = [max(r["probs"].values()) for r in firsts]
    flat = (sum(top_mass) / len(top_mass) < 0.25) if top_mass else True
    run.finish({"selection_mass_by_class": per_class, "mean_rank_by_class": ranks, "rank_correlation_with_rulers": corr,
                "top_item_mass_mean": (sum(top_mass) / len(top_mass)) if top_mass else None, "constructions": construction_summary(rows)},
               {"exec": "COMPLETE", "outcome": "INSTRUMENT_FAILED" if flat else "DESCRIPTIVE", "primary": "evidence ranking against the exact rulers (descriptive)",
                "reason": "flat ranking: the top item carries under a quarter of the mass" if flat else "descriptive card; no outcome band",
                "random_unlearnable_mean_rank": ranks.get("random_unlearnable")}, gs.held_s,
               rival="raw surprise: the random-unlearnable item ranked high for being unpredictable")
    return 0


# ── F02 ───────────────────────────────────────────────────────────────────────────────

def arm_f02() -> int:
    run = CardRun("F02", "s5_run_f.py")
    with s5_lib.GpuSession("s5_f02") as gs:
        for reader in run.readers:
            model, tok, _ = s5_lib.load_model(reader)
            try:
                for i, lid in enumerate(run.units("all")):
                    if run.is_done(reader, lid):
                        continue
                    run.check_deadline()
                    fs = s5_worlds.make_foraging_set(run.parent_of(lid))
                    run.register_world(lid, fs)
                    listing, opts = _listing(fs)
                    rng = random.Random(SEED + 300 + i)
                    r = s5_lib.candidate_likelihood(model, tok, f"Six number sequences, three elements shown of each:\n{listing}\nYou may examine ONE further (two more elements). Which?", opts, rng, unknown=False)
                    names = list(fs["items"])
                    picks = {"model": r["pred"] if r["valid"] else None,
                             "learning_progress": max(names, key=lambda n: fs["rulers"][n]["learning_progress"]),
                             "novelty": max(names, key=lambda n: fs["rulers"][n]["novelty"]),
                             "surprise": max(names, key=lambda n: fs["rulers"][n]["prediction_error"]),
                             "random": rng.choice(names)}
                    # realized gain of examining an item: the reader's log score on the item's
                    # sixth element before (three shown) and after (five shown), cost one per item
                    gains = {}
                    for n in set(v for v in picks.values() if v):
                        it = fs["items"][n]
                        cand = _next_options(it, rng, 5)
                        truth = str(it["seq"][5])
                        b = s5_lib.candidate_likelihood(model, tok, f"Sequence: {', '.join(str(x) for x in it['seq'][:3])}, ... What is its sixth element?", cand, rng, unknown=False)
                        a = s5_lib.candidate_likelihood(model, tok, f"Sequence: {', '.join(str(x) for x in it['seq'][:5])}, ... What is its sixth element?", cand, rng, unknown=False)
                        if a["valid"] and b["valid"]:
                            gains[n] = s5_lib.log_score(a["probs"], truth) - s5_lib.log_score(b["probs"], truth)
                    for pol, n in picks.items():
                        if n is None or n not in gains:
                            continue
                        run.row(reader, lid, lid, f"policy|{pol}", {"domain": "all", "policy": pol, **({"control": pol} if pol in ("novelty", "surprise", "random") else {})},
                                n, "construction", "artifact_plus_context", r if pol == "model" else None, gains[n], valid=True, validity_reason="ok",
                                extra={"picked": n, "picked_class_rulers": fs["rulers"][n]})
                    run.unit_complete(reader, lid)
            finally:
                s5_lib.free_model(model)
    rows = [r for r in run.rows() if r["valid"] and r["primary_score"] is not None]
    sel = lambda p: cluster_by_construction(select_rows(rows, policy=p))              # noqa: E731
    level = {p: (lambda m: sum(m.values()) / len(m) if m else None)(s5_lib.per_unit_means(sel(p), "unit_id", "primary_score")) for p in ("model", "learning_progress", "novelty", "surprise", "random")}
    best = max(("novelty", "surprise", "random"), key=lambda p: level[p] if level[p] is not None else -9)
    primary = s5_lib.paired_contrast(sel("model"), sel(best), "unit_id", "primary_score", SEED + 21)
    picked = mean_by([dict(r, primary_score=1.0) for r in select_rows(rows, policy="model")], ["policy"])
    classes = {}
    for r in select_rows(rows, policy="model"):
        classes[r["extra"]["picked"]] = classes.get(r["extra"]["picked"], 0) + 1
    verdict = run.classify(primary, run.threshold(0.03))
    verdict["best_raw_baseline"] = best
    run.finish({"realized_gain_by_policy": level, "primary_model_minus_best_raw": primary, "model_picks_by_class": classes,
                "picked_rows": picked, "constructions": construction_summary(rows)},
               {"exec": "COMPLETE", "primary": "realized held-out gain per cost of the model's selection minus the best raw-signal baseline", **verdict}, gs.held_s,
               rival=f"the {best} baseline; the exact learning-progress policy is the ceiling")
    return 0


# ── F03 ───────────────────────────────────────────────────────────────────────────────

def arm_f03() -> int:
    run = CardRun("F03", "s5_run_f.py")
    with s5_lib.GpuSession("s5_f03") as gs:
        for reader in run.readers:
            model, tok, _ = s5_lib.load_model(reader)
            try:
                for i, lid in enumerate(run.units("all")):
                    if run.is_done(reader, lid):
                        continue
                    run.check_deadline()
                    fs = s5_worlds.make_foraging_set(run.parent_of(lid))
                    run.register_world(lid, fs)
                    rng = random.Random(SEED + 600 + i)
                    it = fs["items"]["structured_residual"]
                    seq = it["seq"][:5]
                    for hope in ("congruent", "incongruent"):
                        # the attractive explanation is supported (congruent) or not (incongruent):
                        # in the incongruent world the shown elements contradict it at one place
                        shown = list(seq)
                        if hope == "incongruent":
                            shown[3] += 4
                        attractive = "a hidden prime-number pattern governs the sequence"
                        dull = "a plain linear rule with a small alternating residual governs it"
                        support = {"attractive": 0.15 if hope == "incongruent" else 0.6, "dull": 0.7 if hope == "incongruent" else 0.3}
                        for prompt in ("plain", "counter_bias"):
                            prefix = "" if prompt == "plain" else "A striking explanation is not more likely for being striking; weigh only how well each fits the elements.\n"
                            body = (f"{prefix}Sequence: {', '.join(str(x) for x in shown)}, ...\nTwo explanations are on offer: (i) {attractive}; (ii) {dull}. "
                                    f"Which would you pursue further?")
                            r = s5_lib.candidate_likelihood(model, tok, body, {"attractive": "the prime-number pattern", "dull": "the linear rule with a residual"}, rng, unknown=True)
                            c = s5_lib.candidate_likelihood(model, tok, body.replace("Which would you pursue further?", "Which is better supported by the elements shown?"),
                                                            {"attractive": "the prime-number pattern", "dull": "the linear rule with a residual"}, rng, unknown=True)
                            pursuit = r["probs"]["attractive"] if r["valid"] else None
                            run.row(reader, lid, lid, f"{hope}|{prompt}", {"domain": "all", "hope": hope, "prompt": prompt},
                                    "dull" if hope == "incongruent" else "attractive", "construction", "artifact_only", r, pursuit,
                                    extra={"warrant_p_attractive": c["probs"]["attractive"] if c["valid"] else None, "support": support,
                                           "false_discovery": bool(r["valid"] and hope == "incongruent" and r["pred"] == "attractive"),
                                           "p_unknown": r.get("p_unknown")})
                    run.unit_complete(reader, lid)
            finally:
                s5_lib.free_model(model)
    rows = [r for r in run.rows() if r["valid"] and r["primary_score"] is not None]
    sel = lambda **k: cluster_by_construction(select_rows(rows, **k))                 # noqa: E731
    primary = s5_lib.paired_contrast(sel(hope="incongruent", prompt="plain"), sel(hope="incongruent", prompt="counter_bias"), "unit_id", "primary_score", SEED + 31)
    fdr = {p: sum(1 for r in rows if r["factors"]["hope"] == "incongruent" and r["factors"]["prompt"] == p and r["extra"]["false_discovery"]) /
              max(1, sum(1 for r in rows if r["factors"]["hope"] == "incongruent" and r["factors"]["prompt"] == p)) for p in ("plain", "counter_bias")}
    warrant = mean_by([dict(r, primary_score=r["extra"]["warrant_p_attractive"]) for r in rows if r["extra"]["warrant_p_attractive"] is not None], ["hope", "prompt"])
    pursuit = mean_by(rows, ["hope", "prompt"])
    gap = {}
    for k in pursuit:
        if k in warrant:
            gap[k] = pursuit[k]["mean"] - warrant[k]["mean"]
    verdict = run.classify(primary, run.threshold(0.05))
    verdict["false_discovery_rate"] = fdr
    run.finish({"primary_pursuit_plain_minus_counter_bias_incongruent": primary, "pursuit_of_attractive": pursuit, "warrant_for_attractive": warrant,
                "pursuit_minus_warrant": gap, "false_discovery_rate": fdr, "constructions": construction_summary(rows)},
               {"exec": "COMPLETE", "primary": "pursuit of the hoped-for explanation beyond its support on incongruent worlds, and what the counter-bias prompt removes", **verdict}, gs.held_s,
               rival="pursuit that simply tracks warrant (gap near zero)")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--card", required=True, choices=["F01", "F02", "F03"])
    a = ap.parse_args()
    try:
        return {"F01": arm_f01, "F02": arm_f02, "F03": arm_f03}[a.card]()
    except DeadlineReached:
        return 3


if __name__ == "__main__":
    sys.exit(main())
