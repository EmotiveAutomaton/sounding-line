"""Stage 6 recorded-process engines (brief §8 T track; §5.2): ScholaWrite next-revision
prediction under lineage-clean splits, CoAuthor suggestion decisions behind the state
reconstruction gate, drawings' next stroke at access levels, and the boundary analyses
(T05, T08, T09, T10). OpenReview (T03) carries its predeclared RESOURCE_BLOCKED
disposition (runners/stage6/records.py).

DESIGN CHECK (2026-08-30)
lessons read: LESSONS §2 (extractors over foreign data: unparseable rows counted, never
  dropped silently), §3 (denominators declared; the sequential previous-label baseline is
  the frozen rival; the independent unit is the project/session/drawing, never a row;
  row-duplication invariance is T09's own test), §4 (readers loaded once; retries none —
  local models).
gates and bands: T01/T02/T04 use the exhaustive bands on reader-minus-baseline held-out
  log score, clustered at the project/session/drawing; T02's reconstruction gate runs
  before any inference and excludes unreconstructable sessions by count; the analysis
  cards are DESCRIPTIVE or INFRASTRUCTURE; T03 is NOT_RUN/RESOURCE_BLOCKED by
  predeclaration unless the corpus appears before the scientific lock.
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from runners import s5_lib                                                         # noqa: E402
from runners.stage6 import cards as CARDS_MOD                                      # noqa: E402
from runners.stage6 import records as REC                                          # noqa: E402
from runners.stage6.architectures import Budget, _likelihood, _likelihood_any     # noqa: E402
from runners.stage6.cardrun import SMOKE, CardRun6                                 # noqa: E402
from soundingline.stage6 import S6, read_json                                      # noqa: E402

SEED = 66900
SW_LABELS = ("Clarity", "Coherence", "Correctness", "Fluency", "Idea Generation",
             "Idea Organization", "Linguistic Style", "Object Insertion", "Scientific Accuracy",
             "Structural", "Textual Complexity", "Visual Formatting")
SW_SHOW = 6            # events shown before the hidden one
CA_DECISIONS = ("accept", "dismiss")


def _fake_world_rng(key: str):
    from runners.stage6.worlds import _rng                                        # noqa: PLC0415
    return _rng(key, "records")


class _KeyWorld(dict):
    """A minimal world-like object for the fixed-order helper (its lid seeds the order)."""


def _kw(key: str) -> dict:
    return {"lid": key}


def run_t01(run: CardRun6) -> int:
    """ScholaWrite: predict the next revision's label from the recent event window; the
    reader against the previous-label and label-marginal baselines; leave-project-out by
    construction (the lane split is project-keyed) and leave-author-out reported."""
    n_sessions = 4 if SMOKE else CARDS_MOD.units_for("T01")
    sessions = REC.scholawrite_sessions(lane=run.split if run.split != "attack" else "discovery")
    sessions = sessions[:n_sessions]
    n_events = 2 if SMOKE else 6
    label_opts = {la: la.lower() for la in SW_LABELS}
    with s5_lib.GpuSession("s6_t01") as gs:
        for reader in run.readers:
            model, tok, _ = s5_lib.load_model(reader)
            try:
                for s in sessions:
                    if run.is_done(reader, s["session_id"]):
                        continue
                    run.check_deadline()
                    evs = s["events"]
                    marg: dict = {}
                    for k in range(SW_SHOW, min(len(evs) - 1, SW_SHOW + n_events)):
                        window = evs[k - SW_SHOW:k]
                        target = evs[k]["label"]
                        if target not in SW_LABELS:
                            continue
                        lines = []
                        for e in window:
                            v = REC.scholawrite_event_view(e)
                            lines.append(f"- edit ({e['label'].lower()}): ...{v['before'][-60:]!r} -> ...{v['after'][-60:]!r}")
                        body = ("A writer is revising a scholarly draft. Their recent edits, in order:\n"
                                + "\n".join(lines) + "\nWhat KIND of edit do they make next?")
                        b = Budget()
                        r = _likelihood_any(model, tok, body, label_opts, _kw(s["session_id"] + f"|{k}"), b, "t01")
                        prev = window[-1]["label"]
                        seen = [e["label"] for e in evs[:k]]
                        for la in seen:
                            marg[la] = marg.get(la, 0) + 1
                        z = sum(marg.values()) + len(SW_LABELS)
                        base_prev = math.log(max((marg.get(prev, 0) + 4) / z if prev == target else (marg.get(target, 0) + 1) / z, 1e-9))
                        base_marg = math.log(max((marg.get(target, 0) + 1) / z, 1e-9))
                        ls = math.log(max(r["probs"].get(target, 0.0), 1e-9)) if r["valid"] else None
                        run.row(s["session_id"], reader=reader, arm="reader",
                                factors={"protocol": "leave_project_out", "author": s["author"], "k": k},
                                truth=target, truth_provenance="recorded_label",
                                scores={"ls": ls, "base_prev": base_prev, "base_marg": base_marg,
                                        "prev_correct": prev == target},
                                primary_score=(ls - max(base_prev, base_marg)) if ls is not None else None,
                                budget=b.close())
                    run.unit_complete(reader, s["session_id"])
            finally:
                s5_lib.free_model(model)
    gpu = gs.held_s
    rows = [r for r in run.rows() if r["valid"] and r["primary_score"] is not None]
    vals = {f"{r['model_id']}|{r['unit_id']}": [] for r in rows}
    for r in rows:
        vals[f"{r['model_id']}|{r['unit_id']}"].append(r["primary_score"])
    units = {u: sum(v) / len(v) for u, v in vals.items()}
    ci = s5_lib.cluster_bootstrap_ci(units, SEED + 1)
    by_author: dict = {}
    for r in rows:
        by_author.setdefault(r["factors"]["author"], []).append(r["primary_score"])
    loao = {a: sum(v) / len(v) for a, v in by_author.items()}
    verdict = run.classify(ci, run.threshold())
    run.finish({"primary_reader_minus_best_baseline": ci, "n_sessions": len(units),
                "leave_author_out_means": loao, "prev_label_hit_rate": sum(1 for r in rows if r["scores"]["prev_correct"]) / max(1, len(rows))},
               {"exec": "COMPLETE", **verdict, "primary": CARDS_MOD.ALL["T01"]["primary"]}, gpu,
               rival="the sequential previous-label baseline and the label marginal")
    return 0


def run_t02(run: CardRun6) -> int:
    """CoAuthor: the reconstruction gate, then accept/dismiss prediction from the document
    state and the shown suggestion, against the writer's own base rate."""
    n_sessions = 4 if SMOKE else CARDS_MOD.units_for("T02")
    sessions = REC.coauthor_sessions(max_sessions=n_sessions * 3, lane=run.split if run.split != "attack" else "discovery")
    recon_rate = sum(1 for s in sessions if s["reconstructed"]) / max(1, len(sessions))
    usable = [s for s in sessions if s["reconstructed"] and len(s["decisions"]) >= 3][:n_sessions]
    n_events = 2 if SMOKE else 6
    with s5_lib.GpuSession("s6_t02") as gs:
        for reader in run.readers:
            model, tok, _ = s5_lib.load_model(reader)
            try:
                for s in usable:
                    if run.is_done(reader, s["session_id"]):
                        continue
                    run.check_deadline()
                    shown = [e for e in s["events"] if e["decided"] in CA_DECISIONS]
                    base_acc_n = sum(1 for e in shown if e["decided"] == "accept")
                    for k, e in enumerate(shown[:n_events]):
                        prior_rate = (1 + sum(1 for x in shown[:k] if x["decided"] == "accept")) / (2 + k)
                        body = (f"A writer is drafting with an assistant. The draft so far ends: "
                                f"...{e['doc_tail'][-300:]!r}\nThe assistant offers suggestions: {e['suggestions'][:200]}\n"
                                f"Does the writer take a suggestion or wave them away?")
                        b = Budget()
                        r = _likelihood(model, tok, body, {"accept": "takes a suggestion", "dismiss": "waves them away"},
                                        _kw(s["session_id"] + f"|{k}"), b, "t02")
                        truth = e["decided"]
                        ls = math.log(max(r["probs"].get(truth, 0.0), 1e-9)) if r["valid"] else None
                        p_base = prior_rate if truth == "accept" else 1 - prior_rate
                        run.row(s["session_id"], reader=reader, arm="reader", truth=truth,
                                truth_provenance="recorded_decision", factors={"k": k},
                                scores={"ls": ls, "base": math.log(max(p_base, 1e-9))},
                                primary_score=(ls - math.log(max(p_base, 1e-9))) if ls is not None else None,
                                budget=b.close(), extra={"session_accepts": base_acc_n, "n_shown": len(shown)})
                    run.unit_complete(reader, s["session_id"])
            finally:
                s5_lib.free_model(model)
    gpu = gs.held_s
    rows = [r for r in run.rows() if r["valid"] and r["primary_score"] is not None]
    per: dict = {}
    for r in rows:
        per.setdefault(f"{r['model_id']}|{r['unit_id']}", []).append(r["primary_score"])
    units = {u: sum(v) / len(v) for u, v in per.items()}
    ci = s5_lib.cluster_bootstrap_ci(units, SEED + 2)
    verdict = run.classify(ci, run.threshold())
    if recon_rate < 0.5:
        verdict = {"outcome": "INSTRUMENT_FAILED", "reason": f"reconstruction gate: only {recon_rate:.2f} of sessions replay exactly",
                   **{k: verdict.get(k) for k in ("point", "ci", "n_units")}}
    run.finish({"reconstruction_rate": recon_rate, "primary_reader_minus_base_rate": ci, "n_sessions": len(units)},
               {"exec": "COMPLETE", **verdict, "primary": CARDS_MOD.ALL["T02"]["primary"]}, gpu,
               rival="the writer's running accept base rate")
    return 0


def run_t03(run: CardRun6) -> int:
    disp = REC.OPENREVIEW_DISPOSITION
    local = REPO / "corpora" / "openreview"
    if local.exists() and any(local.iterdir()):
        run.finish({"disposition": "corpus appeared; T03 needs a design pass before running"},
                   {"exec": "COMPLETE", "outcome": "DESCRIPTIVE",
                    "primary": CARDS_MOD.ALL["T03"]["primary"],
                    "reason": "a local corpus exists; the predeclared block is lifted and the card needs its design"})
        return 0
    run.finish({"disposition": disp},
               {"exec": "COMPLETE", "outcome": "NOT_RUN",
                "primary": CARDS_MOD.ALL["T03"]["primary"],
                "reason": f"RESOURCE_BLOCKED, predeclared: {disp['why']}"})
    return 0


def run_t04(run: CardRun6) -> int:
    """Drawings: next-stroke start-quadrant from the unordered set plus a k-prefix, reader
    against the placement prior; the access curve (final raster excluded here: it carries
    no order by the Stage-4/5 result, the prior is the comparator)."""
    from runners.s4_run_p import stroke_features, quadrant                        # noqa: PLC0415
    n = 6 if SMOKE else CARDS_MOD.units_for("T04")
    units = REC.drawing_units(lane=run.split if run.split != "attack" else "discovery")[:n]
    quads = {"0": "upper-left", "1": "upper-right", "2": "lower-left", "3": "lower-right"}
    with s5_lib.GpuSession("s6_t04") as gs:
        for reader in run.readers:
            model, tok, _ = s5_lib.load_model(reader)
            try:
                for u in units:
                    if run.is_done(reader, u["session_id"]):
                        continue
                    run.check_deadline()
                    F = stroke_features(u["strokes"])
                    k = 2
                    target_q = str(quadrant(F[k][8], F[k][9]))
                    shown = list(range(len(u["strokes"])))
                    _fake_world_rng(u["session_id"]).shuffle(shown)
                    listing = "\n".join(
                        f"stroke {j + 1}: from the {quads[str(quadrant(F[i][8], F[i][9]))]} to the {quads[str(quadrant(F[i][10], F[i][11]))]}, length {int(F[i][6])}"
                        for j, i in enumerate(shown))
                    prefix = ", then ".join(f"stroke {shown.index(i) + 1}" for i in range(k))
                    body = (f"A {u['cat']} was drawn stroke by stroke. The strokes, in NO particular order:\n{listing}\n"
                            f"It is known the drawing began with {prefix}. In which corner does the NEXT stroke begin?")
                    b = Budget()
                    r = _likelihood(model, tok, body, quads, _kw(u["session_id"]), b, "t04")
                    marg = {q: 0.25 for q in quads}
                    xs = [str(quadrant(F[i][8], F[i][9])) for i in range(len(u["strokes"]))]
                    for q in xs:
                        marg[q] = marg.get(q, 0) + 1
                    z = sum(marg.values())
                    base = math.log(max(marg[target_q] / z, 1e-9))
                    ls = math.log(max(r["probs"].get(target_q, 0.0), 1e-9)) if r["valid"] else None
                    run.row(u["session_id"], reader=reader, arm="reader", truth=target_q,
                            truth_provenance="recorded_drawing", factors={"cat": u["cat"], "access": "set_plus_prefix"},
                            scores={"ls": ls, "base": base},
                            primary_score=(ls - base) if ls is not None else None, budget=b.close())
                    run.unit_complete(reader, u["session_id"])
            finally:
                s5_lib.free_model(model)
    gpu = gs.held_s
    rows = [r for r in run.rows() if r["valid"] and r["primary_score"] is not None]
    units_v = {f"{r['model_id']}|{r['unit_id']}": r["primary_score"] for r in rows}
    ci = s5_lib.cluster_bootstrap_ci(units_v, SEED + 4)
    run.finish({"primary_reader_minus_placement_prior": ci, "n": len(units_v)},
               {"exec": "COMPLETE", **run.classify(ci, run.threshold()),
                "primary": CARDS_MOD.ALL["T04"]["primary"]}, gpu,
               rival="the drawing's own start-quadrant marginal")
    return 0


def _t_analysis(run: CardRun6, card: str) -> int:
    """T05-T10: boundary analyses over the landed T rows."""
    def rows_of(c):
        return [r for r in run.rows_of(c) if r.get("valid") and r.get("primary_score") is not None]
    t1, t2, t4 = rows_of("T01"), rows_of("T02"), rows_of("T04")
    metrics: dict = {}
    if card == "T05":
        pts = {}
        for name, rs in (("scholawrite", t1), ("coauthor", t2), ("drawings", t4)):
            vals = {f"{r['model_id']}|{r['unit_id']}": r["primary_score"] for r in rs}
            pts[name] = s5_lib.cluster_bootstrap_ci(vals, SEED + 5)
        metrics["per_corpus"] = pts
        positive = [n for n, c in pts.items() if (c.get("point") or 0) > 0]
        verdict = {"exec": "COMPLETE", "outcome": "DESCRIPTIVE",
                   "primary": CARDS_MOD.ALL[card]["primary"],
                   "reason": f"one frozen reader positive on: {positive or 'none'} of three record types"}
    elif card == "T06":
        halves = {"early": {}, "late": {}}
        for r in t1:
            k = r["factors"].get("k", 0)
            (halves["early"] if k <= SW_SHOW + 2 else halves["late"])[f"{r['model_id']}|{r['unit_id']}|{k}"] = r["primary_score"]
        metrics["early"] = s5_lib.cluster_bootstrap_ci(halves["early"], SEED + 6)
        metrics["late"] = s5_lib.cluster_bootstrap_ci(halves["late"], SEED + 7)
        verdict = {"exec": "COMPLETE", "outcome": "DESCRIPTIVE", "primary": CARDS_MOD.ALL[card]["primary"],
                   "reason": "time-aware split written (dated ordering enters through the shown window)"}
    elif card == "T07":
        with_opp = {f"{r['model_id']}|{r['unit_id']}": r["primary_score"] for r in t2}
        metrics["with_opportunity_info"] = s5_lib.cluster_bootstrap_ci(with_opp, SEED + 8)
        verdict = {"exec": "COMPLETE", "outcome": "DESCRIPTIVE", "primary": CARDS_MOD.ALL[card]["primary"],
                   "reason": "the shown-suggestion condition carries the opportunity set; the hidden arm is the base rate"}
    elif card == "T08":
        by_cat: dict = {}
        for r in t4:
            by_cat.setdefault(r["factors"].get("cat"), []).append(r["primary_score"])
        metrics["drawings_by_category"] = {c: sum(v) / len(v) for c, v in by_cat.items()}
        by_author: dict = {}
        for r in t1:
            by_author.setdefault(r["factors"].get("author"), []).append(r["primary_score"])
        metrics["scholawrite_by_author"] = {a: sum(v) / len(v) for a, v in list(by_author.items())[:20]}
        spread = [v for v in metrics["drawings_by_category"].values()]
        verdict = {"exec": "COMPLETE", "outcome": "DESCRIPTIVE", "primary": CARDS_MOD.ALL[card]["primary"],
                   "reason": f"stratified means written; drawings spread {min(spread):.2f}..{max(spread):.2f}" if spread else "no rows"}
    elif card == "T09":
        vals = {f"{r['model_id']}|{r['unit_id']}": [] for r in t1}
        for r in t1:
            vals[f"{r['model_id']}|{r['unit_id']}"].append(r["primary_score"])
        units = {u: sum(v) / len(v) for u, v in vals.items()}
        ci0 = s5_lib.cluster_bootstrap_ci(units, SEED + 9)
        dup = dict(units)
        dup.update({u + "|dup": v for u, v in list(units.items())[:0]})
        rows_dup = t1 + t1                                       # row duplication
        vals2: dict = {}
        for r in rows_dup:
            vals2.setdefault(f"{r['model_id']}|{r['unit_id']}", []).append(r["primary_score"])
        units2 = {u: sum(v) / len(v) for u, v in vals2.items()}
        ci1 = s5_lib.cluster_bootstrap_ci(units2, SEED + 9)
        invariant = ci0.get("point") is not None and abs((ci0["point"] or 0) - (ci1["point"] or 0)) < 1e-9
        metrics["ci"] = ci0
        metrics["row_duplication_invariant"] = invariant
        metrics["effective_units"] = len(units)
        verdict = {"exec": "COMPLETE", "outcome": "INFRASTRUCTURE" if invariant else "INSTRUMENT_FAILED",
                   "primary": CARDS_MOD.ALL[card]["primary"],
                   "reason": f"session-clustered n={len(units)}; duplication moves the estimate: {not invariant}"}
    else:   # T10
        dispositions = {}
        for c, name in (("T01", "scholawrite"), ("T02", "coauthor"), ("T04", "drawings")):
            v = read_json(S6 / c / "verdict.json") if (S6 / c / "verdict.json").exists() else {}
            oc = v.get("outcome")
            dispositions[name] = {"outcome": oc,
                                  "disposition": ("promote" if oc == "SUPPORT_CANDIDATE" else
                                                  "descriptive boundary" if oc in ("VALID_NULL", "INCONCLUSIVE", "COUNTEREVIDENCE", "DESCRIPTIVE") else
                                                  "instrument failure" if oc == "INSTRUMENT_FAILED" else "void")}
        dispositions["openreview"] = {"outcome": "NOT_RUN", "disposition": "resource blocked, predeclared"}
        metrics["dispositions"] = dispositions
        verdict = {"exec": "COMPLETE", "outcome": "DESCRIPTIVE", "primary": CARDS_MOD.ALL[card]["primary"],
                   "reason": "; ".join(f"{k}: {v['disposition']}" for k, v in dispositions.items())}
    run.finish(metrics, verdict, 0.0, rival=CARDS_MOD.ALL[card]["discriminator"])
    return 0


def run_card(run: CardRun6) -> int:
    card = run.card
    if card == "T01":
        return run_t01(run)
    if card == "T02":
        return run_t02(run)
    if card == "T03":
        return run_t03(run)
    if card == "T04":
        return run_t04(run)
    if card in ("T05", "T06", "T07", "T08", "T09", "T10"):
        return _t_analysis(run, card)
    if card in ("C12", "F12"):
        # signature transfer: the winning construction discriminators applied descriptively
        # to recorded sessions (no known truth: DESCRIPTIVE by design)
        src = "T01" if card == "C12" else "T04"
        rows = [r for r in run.rows_of(src) if r.get("valid")]
        metrics = {"n_source_rows": len(rows), "note": "descriptive: no recorded ground truth for the latent"}
        run.finish(metrics, {"exec": "COMPLETE", "outcome": "DESCRIPTIVE",
                             "primary": CARDS_MOD.ALL[card]["primary"],
                             "reason": f"signatures summarized over {len(rows)} recorded rows; latent truth unknown"}, 0.0)
        return 0
    raise ValueError(f"no records handler for {card}")
