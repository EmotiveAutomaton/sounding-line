"""Stage 5 process and physical-trace cards (brief §6 P01-P03, §4.4).

DESIGN CHECK (2026-08-29)
lessons read: LESSONS §3 (length and cheap-scalar priors before any representation
  claim; blind floors follow the truth marginal; split near-duplicates together; the
  per-item best of several comparators is an oracle; every statistic written), §5 (CPU
  caps), CONTROLS §6.
gates and bands:
  - P01 primary: the held-out log score of the next stroke's start quadrant at each
    access level (final geometry, unordered stroke set, partial order, true prefix) minus
    the best cheap prior (category marginal, bounding-box corner), paired by drawing;
    NULL: 0 at every level; ALTERNATIVE: at or above 0.03 nats at the richer levels with
    the curve monotone in access; a level whose gain does not exceed the priors reads as
    the boundary of the information in that access.
  - P02: two scores that cannot alias: ENACTABILITY (the reader's proposed order
    respects the shown partial order) and HISTORICAL CORRESPONDENCE (it equals the one
    true order among the valid ones); every artifact is equifinal by construction (four
    valid orders), so the reader's answer to "can the exact order be determined?" must
    be no; NULL for enactability: the rate a random valid proposal achieves (1.0 for a
    valid-by-construction proposer, 0.25 blind); primary: enactability minus the blind
    rate, with correspondence and the abstention rate reported apart; a reader claiming
    the exact order on equifinal artifacts is confident projection, counted.
  - P03 primary: the competence x access interaction: the high-competence classifier's
    gain over the low-competence one at rich access (prefix) minus at poor access
    (unordered set); NULL: 0; ALTERNATIVE: at or above 0.03; competence is a training
    fraction, measured, never a human claim.
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
import hashlib
import itertools
import json
import math
import random
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from runners import s5_lib                                                        # noqa: E402
from runners.s4_run_p import (CATEGORIES, fetch_prefix, load_drawings, quadrant,    # noqa: E402
                              render, split_of, stroke_features)
from runners.s5_run_common import SMOKE, CardRun, DeadlineReached                   # noqa: E402
from soundingline.stage5 import S5                                                 # noqa: E402

SEED = s5_lib.SEED0 + 500
RAW4 = REPO / "results" / "phase_2_4_stage_4" / "P01" / "raw"
K_PREFIX = 2
LEVELS = ("final_geometry", "unordered_set", "partial_order", "true_prefix")


def _data() -> dict:
    raw = RAW4 if any(RAW4.glob("*.ndjson.prefix")) else S5 / "P01" / "raw"
    data = {}
    for cat in CATEGORIES:
        p = raw / f"{cat}.ndjson.prefix"
        if not p.exists():
            fetch_prefix(cat, p)
        dl = [d for d in load_drawings(cat, p) if len(d["strokes"]) >= K_PREFIX + 2]
        data[cat] = dl[:80] if SMOKE else dl
    return data


def _features(d: dict) -> dict:
    """Per access level, a feature vector for predicting the start quadrant of stroke
    K_PREFIX+1 (the third stroke)."""
    import numpy as np                                                            # noqa: PLC0415
    F = stroke_features(d["strokes"])
    n = len(F)
    order = sorted(range(n), key=lambda i: (F[i][4], F[i][5]))            # canonical, order-free
    unordered = np.concatenate([F[order].mean(0), F[order].std(0), [n]])
    first_half = set(range(n // 2))
    ph = np.concatenate([F[[i for i in order if i in first_half]].mean(0) if any(i in first_half for i in order) else np.zeros(12),
                         F[[i for i in order if i not in first_half]].mean(0) if any(i not in first_half for i in order) else np.zeros(12), [n]])
    prefix = np.concatenate([F[0], F[1], [n]])
    return {"final_geometry": render(d["strokes"]), "unordered_set": unordered, "partial_order": ph, "true_prefix": prefix,
            "target": quadrant(d["strokes"][K_PREFIX][0][0], d["strokes"][K_PREFIX][1][0]),
            "bbox": quadrant(min(x for xs, _ in d["strokes"] for x in xs), min(y for _, ys in d["strokes"] for y in ys))}


def parse_order_lenient(text: str):
    """The first four distinct stroke numbers 1-4 in the reply, in the order written; None
    if fewer than four appear (design 2's comma format, and the JSON fallback)."""
    seen = []
    for ch in text:
        if ch in "1234" and int(ch) not in seen:
            seen.append(int(ch))
        if len(seen) == 4:
            return seen
    return None


def _fit_levels(data: dict, train_frac: float = 1.0, seed: int = 0):
    import numpy as np                                                            # noqa: PLC0415
    from sklearn.linear_model import LogisticRegression                           # noqa: PLC0415
    X = {lv: [] for lv in LEVELS}
    y, cats, splits, keys, bbox = [], [], [], [], []
    cat_list = sorted(data)
    for cat, dl in data.items():
        for d in dl:
            f = _features(d)
            rh = hashlib.md5(f["final_geometry"].astype(np.uint8).tobytes()).hexdigest()
            # design 2 (TODO (d)): the category and the ink's placement quadrant enter every
            # level's model as one-hot features, so the ladder is tested above the priors
            extra = ([1.0 if c == cat else 0.0 for c in cat_list] + [1.0 if q == f["bbox"] else 0.0 for q in range(4)]) if s5_lib.DESIGN == "2" else []
            for lv in LEVELS:
                X[lv].append(list(np.asarray(f[lv], dtype=float).ravel()) + extra)
            y.append(f["target"])
            cats.append(cat)
            splits.append(split_of(d["key_id"], rh))
            keys.append(d["key_id"])
            bbox.append(f["bbox"])
    y = np.asarray(y)
    splits = np.asarray(splits)
    cats = np.asarray(cats)
    tr = splits == "train"
    if train_frac < 1.0:
        rng = np.random.RandomState(seed)
        idx = np.where(tr)[0]
        keep = rng.choice(idx, int(len(idx) * train_frac), replace=False)
        tr = np.zeros_like(tr)
        tr[keep] = True
    te = splits == "discovery"
    models = {}
    for lv in LEVELS:
        Xl = np.asarray(X[lv])
        models[lv] = LogisticRegression(max_iter=3000, C=0.1, class_weight="balanced").fit(Xl[tr], y[tr])
    return X, y, cats, splits, keys, np.asarray(bbox), tr, te, models


def arm_p01() -> int:
    import numpy as np                                                            # noqa: PLC0415
    run = CardRun("P01", "s5_run_p.py")
    t0 = time.time()
    data = _data()
    counts = {c: len(v) for c, v in data.items()}
    if any(c < (30 if SMOKE else 300) for c in counts.values()):
        run.finish({"counts": counts}, {"exec": "BLOCKED", "outcome": "VOID", "reason": "DATA_BLOCKED"}, 0.0)
        return 0
    X, y, cats, splits, keys, bbox, tr, te, models = _fit_levels(data)
    labels = [0, 1, 2, 3]
    cat_marg = {cat: np.bincount(y[tr & (cats == cat)], minlength=4) / max(1, np.sum(tr & (cats == cat))) for cat in CATEGORIES}
    bbox_marg = {q: np.bincount(y[tr & (bbox == q)], minlength=4) / max(1, np.sum(tr & (bbox == q))) for q in labels}
    per_level = {}
    for lv in LEVELS:
        Xl = np.asarray(X[lv])
        P = models[lv].predict_proba(Xl[te])
        cls = list(models[lv].classes_)
        for k, t, c, b, pr in zip(np.asarray(keys)[te], y[te], cats[te], bbox[te], P):
            p_model = float(pr[cls.index(t)]) if t in cls else 1e-9
            p_cat = float(cat_marg[c][t])
            p_bbox = float(bbox_marg[int(b)][t])
            best_prior = max(p_cat, p_bbox)
            run.row("cpu-logistic", str(k), f"P01|{c}|{k}", lv, {"domain": "all", "access": lv, "category": str(c)},
                    int(t), "recorded_drawing", {"final_geometry": "artifact_only", "unordered_set": "unordered_process", "partial_order": "unordered_process", "true_prefix": "ordered_history"}[lv],
                    {"valid": True, "validity_reason": "ok", "pred": int(cls[int(np.argmax(pr))]), "probs": None, "labels": None},
                    math.log(max(p_model, 1e-9)) - math.log(max(best_prior, 1e-9)),
                    extra={"log_score": math.log(max(p_model, 1e-9)), "category_prior_log": math.log(max(p_cat, 1e-9)), "bbox_prior_log": math.log(max(p_bbox, 1e-9))})
        run.flush()
        rows = [r for r in run.rows() if r["factors"]["access"] == lv]
        per_level[lv] = s5_lib.cluster_bootstrap_ci({r["unit_id"]: r["primary_score"] for r in rows}, SEED + 11)
    mono = all((per_level[LEVELS[i]]["point"] or 0) <= (per_level[LEVELS[i + 1]]["point"] or 0) + 0.02 for i in range(len(LEVELS) - 1))
    best = max(per_level, key=lambda lv: per_level[lv]["point"] or -9)
    verdict = run.classify(per_level[best], run.threshold(0.03))
    verdict["best_access_level"] = best
    verdict["monotone_in_access"] = mono
    run.finish({"counts": counts, "per_access_level_gain_over_best_prior": per_level, "monotone_in_access": mono,
                "attribution": "Quick, Draw! dataset, Google Creative Lab, CC BY 4.0", "cpu_minutes": round((time.time() - t0) / 60, 2),
                "n_test": int(te.sum())},
               {"exec": "COMPLETE", "primary": "next-stroke log score by access level beyond the best cheap prior", **verdict}, 0.0,
               rival="the category and bounding-box priors")
    return 0


# ── P02: enactability against historical correspondence ──────────────────────────────

def _stroke_desc(F, i: int) -> str:
    f = F[i]
    return (f"stroke {i + 1}: from the {['upper-left', 'upper-right', 'lower-left', 'lower-right'][quadrant(f[8], f[9])]} to the "
            f"{['upper-left', 'upper-right', 'lower-left', 'lower-right'][quadrant(f[10], f[11])]}, length {int(f[6])}")


def arm_p02() -> int:
    run = CardRun("P02", "s5_run_p.py")
    data = _data()
    rng = random.Random(SEED + 2)
    pool = [d for cat in data for d in data[cat] if len(d["strokes"]) >= 4]
    rng.shuffle(pool)
    n = 12 if SMOKE else 120
    items = pool[:n]
    with s5_lib.GpuSession("s5_p02") as gs:
        for reader in run.readers:
            model, tok, _ = s5_lib.load_model(reader)
            try:
                for i, d in enumerate(items):
                    uid = f"P02|{d['cat']}|{d['key_id']}"
                    if run.is_done(reader, uid):
                        continue
                    run.check_deadline()
                    F = stroke_features(d["strokes"][:4])
                    shown = list(range(4))
                    rng2 = random.Random(SEED + 3 + i)
                    rng2.shuffle(shown)                      # the listing hides the true order
                    listing = "\n".join(_stroke_desc(F, i_) for i_ in shown)
                    phase1 = {0, 1}
                    early = [shown.index(k) + 1 for k in phase1]
                    late = [shown.index(k) + 1 for k in (2, 3)]
                    constraint = f"It is known that strokes {early[0]} and {early[1]} (as listed) were both made before strokes {late[0]} and {late[1]}."
                    body = (f"A {d['cat']} was drawn in four strokes, listed here in NO particular order:\n{listing}\n{constraint}\n"
                            + ("Propose an order in which it was drawn: reply with the four stroke numbers in order, separated by commas, and nothing else."
                               if s5_lib.DESIGN == "2" else
                               "Propose an order in which it was drawn: reply with one JSON object {{\"order\": [a, b, c, d]}} using the listed stroke numbers."))
                    g = s5_lib.generate(model, tok, body, seed=SEED + 10 + i, max_new=40, greedy=True)
                    proposal = None
                    try:
                        m = json.loads(g["text"][g["text"].index("{"):g["text"].rindex("}") + 1])
                        if isinstance(m.get("order"), list) and sorted(int(x) for x in m["order"]) == [1, 2, 3, 4]:
                            proposal = [int(x) for x in m["order"]]
                    except Exception:                                                # noqa: BLE001
                        proposal = None
                    if proposal is None:
                        proposal = parse_order_lenient(g["text"])                    # design 2's format, and a fallback
                    ref = run.raw(reader, uid, body, g, validity_reason="ok" if proposal else "malformed_order")
                    valid_orders = [list(p) + list(q) for p in itertools.permutations(early) for q in itertools.permutations(late)]
                    true_order = [shown.index(k) + 1 for k in range(4)]
                    enactable = bool(proposal) and proposal in valid_orders
                    historical = bool(proposal) and proposal == true_order
                    # the abstention question
                    r = s5_lib.candidate_likelihood(model, tok, body.split("Propose")[0] + "Can the exact order be determined from what is given?",
                                                    {"yes": "yes, it can", "no": "no, more than one order fits"}, rng2, unknown=False)
                    run.row(reader, uid, uid, "propose", {"domain": "all", "pair": "equifinal", "category": d["cat"]},
                            json.dumps(true_order), "recorded_drawing", "unordered_process",
                            {"valid": proposal is not None, "validity_reason": "ok" if proposal else "malformed_order", "pred": json.dumps(proposal), "probs": None, "labels": None},
                            float(enactable) - 0.25 if proposal else None, raw_ref=ref,
                            extra={"enactable": enactable, "historical": historical, "n_valid_orders": len(valid_orders),
                                   "blind_valid_rate": len(valid_orders) / 24, "abstained": r["valid"] and r["pred"] == "no",
                                   "p_determinable": r["probs"]["yes"] if r["valid"] else None})
                    run.unit_complete(reader, uid)
            finally:
                s5_lib.free_model(model)
    rows = [r for r in run.rows() if r["valid"] and r["primary_score"] is not None]
    primary = s5_lib.cluster_bootstrap_ci(s5_lib.per_unit_means(rows, "unit_id", "primary_score"), SEED + 21)
    stats = {"enactability": sum(r["extra"]["enactable"] for r in rows) / max(1, len(rows)),
             "historical_correspondence": sum(r["extra"]["historical"] for r in rows) / max(1, len(rows)),
             "chance_historical_among_valid": 0.25, "blind_valid_rate": 4 / 24,
             "abstention_rate": sum(1 for r in rows if r["extra"]["abstained"]) / max(1, len(rows)),
             "proposal_validity": len(rows) / max(1, len(run.rows())), "n": len(rows)}
    verdict = run.classify(primary, run.threshold(0.05))
    verdict["confident_projection_rate"] = 1 - stats["abstention_rate"]
    run.finish({"scores": stats, "primary_enactability_minus_blind": primary},
               {"exec": "COMPLETE", "primary": "enactability minus the blind valid rate on equifinal artifacts; correspondence and abstention apart", **verdict}, gs.held_s,
               rival="historical correspondence read as enactability (they cannot alias: two scores)")
    return 0


# ── P03: competence x access ──────────────────────────────────────────────────────────

def arm_p03() -> int:
    import numpy as np                                                            # noqa: PLC0415
    run = CardRun("P03", "s5_run_p.py")
    t0 = time.time()
    data = _data()
    out = {}
    per_unit = {}
    for comp, frac in (("low", 0.25), ("high", 1.0)):
        X, y, cats, splits, keys, bbox, tr, te, models = _fit_levels(data, train_frac=frac, seed=SEED)
        out[comp] = {"n_train": int(tr.sum())}
        for lv in ("unordered_set", "partial_order", "true_prefix"):
            Xl = np.asarray(X[lv])
            P = models[lv].predict_proba(Xl[te])
            cls = list(models[lv].classes_)
            acc = float(np.mean(np.asarray(cls)[np.argmax(P, 1)] == y[te]))
            out[comp][lv] = {"held_out_accuracy": acc}
            for k, t, pr in zip(np.asarray(keys)[te], y[te], P):
                ls = math.log(max(float(pr[cls.index(t)]) if t in cls else 1e-9, 1e-9))
                per_unit.setdefault((comp, lv), {})[str(k)] = ls
                run.row("cpu-logistic", str(k), f"P03|{k}", f"{comp}|{lv}", {"domain": "all", "competence": comp, "access": lv},
                        int(t), "recorded_drawing", "unordered_process" if lv != "true_prefix" else "ordered_history",
                        {"valid": True, "validity_reason": "ok", "pred": int(cls[int(np.argmax(pr))]), "probs": None, "labels": None}, ls)
        run.flush()
    gain = {}
    for lv in ("unordered_set", "partial_order", "true_prefix"):
        hi, lo = per_unit[("high", lv)], per_unit[("low", lv)]
        gain[lv] = {u: hi[u] - lo[u] for u in hi if u in lo}
    inter = {u: gain["true_prefix"][u] - gain["unordered_set"][u] for u in gain["true_prefix"] if u in gain["unordered_set"]}
    interaction = s5_lib.cluster_bootstrap_ci(inter, SEED + 31)
    verdict = run.classify(interaction, run.threshold(0.03))
    run.finish({"competence_by_access": out, "competence_gain_by_access": {lv: s5_lib.cluster_bootstrap_ci(g, SEED + 32) for lv, g in gain.items()},
                "interaction_prefix_minus_unordered": interaction, "cpu_minutes": round((time.time() - t0) / 60, 2)},
               {"exec": "COMPLETE", "primary": "competence x access interaction (competence gain at prefix minus at unordered set)", **verdict}, 0.0,
               rival="a uniform competence gain at every access level")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--card", required=True, choices=["P01", "P02", "P03"])
    a = ap.parse_args()
    try:
        return {"P01": arm_p01, "P02": arm_p02, "P03": arm_p03}[a.card]()
    except DeadlineReached:
        return 3


if __name__ == "__main__":
    sys.exit(main())
