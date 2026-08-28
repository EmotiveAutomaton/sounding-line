"""Stage 4 physical-trace track (brief §7 P01-P02), CPU only: what action information a
final drawing carries beyond category-level priors, and what additional process
geometry buys. Quick, Draw! simplified drawings (Google Creative Lab, CC BY 4.0;
attribution retained in the verdict), a capped nonrandom prefix of four preselected
categories, disclosed as such.

DESIGN CHECK (2026-08-27)
lessons read: LESSONS §3 (length trap and cheap-scalar controls before any
  representation claim; blind floors follow the truth marginal; matching can raise the
  floor; split near duplicates together; every statistic written to disk), §5 (CPU
  caps), CONTROLS §6 (construction and analytic floors; collision fixtures).
gates and bands:
  - data gate: at least 500 usable drawings per category from the capped prefix, split
    by drawing id before fitting; fewer marks the scout DATA_BLOCKED, categories are
    never changed after seeing effects (they are fixed here: house, tree, bicycle, cat).
  - P01 primary: held-out balanced accuracy of the raster classifier minus the best
    cheap prior (category-only, ink-quadrant, bounding-box corner), paired by drawing.
    NULL: 0. ALTERNATIVE: >= 0.05. Failure direction guarded: a raster model that reads
    the drawing's overall placement is a cheap-prior effect, which the
    translation/scale normalization arm and the bounding-box prior expose; rotation
    sensitivity with transformed labels is reported.
  - P02 primary: the learned first-stroke identification (unordered stroke set) minus
    the geometry heuristic, then the prefix condition's gain, each labeled with its
    access level. Collision control: every ordering of the same strokes yields the same
    raster and the same unordered set, so a raster-only or set-only reader identifying
    the true order above the permutation floor by more than 0.05 marks a leak.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from runners import s4_lib                                                        # noqa: E402
from runners.s4_run_common import CardRun                                         # noqa: E402
from soundingline.s4 import S4, write_json                                        # noqa: E402

CATEGORIES = ("house", "tree", "bicycle", "cat")
URL = "https://storage.googleapis.com/quickdraw_dataset/full/simplified/{cat}.ndjson"
import os                                                                         # noqa: E402
SMOKE = bool(os.environ.get("S4_SMOKE"))
CAP_TOTAL_BYTES = 128 * 2**20
CAP_PER_CAT = 28 * 2**20
TARGET_PER_CAT = 120 if SMOKE else 900
MIN_PER_CAT = 50 if SMOKE else 500
RASTER = 32             # must divide the 256-pixel canvas (block max-pooling)
CPU_CAP_S = 2 * 3600
SEED = 50000


def fetch_prefix(cat: str, dest: Path) -> dict:
    """Stream the category file until enough usable drawings or the byte cap; disclose
    the prefix as nonrandom."""
    if dest.exists():
        return {"cached": True, "bytes": dest.stat().st_size}
    dest.parent.mkdir(parents=True, exist_ok=True)
    got, nbytes, usable = 0, 0, 0
    with urllib.request.urlopen(URL.format(cat=cat), timeout=60) as resp, open(dest, "wb") as fh:
        buf = b""
        while usable < TARGET_PER_CAT and nbytes < CAP_PER_CAT:
            chunk = resp.read(1 << 16)
            if not chunk:
                break
            nbytes += len(chunk)
            buf += chunk
            while b"\n" in buf:
                line, buf = buf.split(b"\n", 1)
                fh.write(line + b"\n")
                got += 1
                try:
                    d = json.loads(line)
                    if d.get("recognized") and len(d.get("drawing", [])) >= 2:
                        usable += 1
                except Exception:                                                # noqa: BLE001
                    pass
    return {"cached": False, "bytes": nbytes, "lines": got, "usable": usable,
            "prefix_nonrandom": True}


def load_drawings(cat: str, path: Path) -> list[dict]:
    out = []
    for line in path.read_text(encoding="utf-8").splitlines():
        try:
            d = json.loads(line)
        except Exception:                                                        # noqa: BLE001
            continue
        if not d.get("recognized") or len(d.get("drawing", [])) < 2:
            continue
        strokes = [(s[0], s[1]) for s in d["drawing"] if len(s[0]) >= 1]
        if len(strokes) < 2:
            continue
        out.append({"key_id": str(d["key_id"]), "cat": cat, "strokes": strokes})
    return out


def quadrant(x: float, y: float) -> int:
    return (1 if x >= 128 else 0) + (2 if y >= 128 else 0)


def render(strokes, size: int = RASTER, normalize: bool = False):
    """Binary union raster with constant stroke width; overpainting cannot leak order."""
    import numpy as np                                                            # noqa: PLC0415
    from PIL import Image, ImageDraw                                              # noqa: PLC0415
    img = Image.new("L", (256, 256), 0)
    dr = ImageDraw.Draw(img)
    pts_all = [(x, y) for xs, ys in strokes for x, y in zip(xs, ys)]
    if normalize and pts_all:
        xs_, ys_ = [p[0] for p in pts_all], [p[1] for p in pts_all]
        x0, x1, y0, y1 = min(xs_), max(xs_), min(ys_), max(ys_)
        sc = 240.0 / max(1.0, max(x1 - x0, y1 - y0))
        tf = lambda x, y: (8 + (x - x0) * sc, 8 + (y - y0) * sc)                 # noqa: E731
    else:
        tf = lambda x, y: (x, y)                                                  # noqa: E731
    for xs, ys in strokes:
        pts = [tf(x, y) for x, y in zip(xs, ys)]
        if len(pts) == 1:
            pts = pts * 2
        dr.line(pts, fill=255, width=6)
    a = np.asarray(img, dtype=np.uint8) > 0
    k = 256 // size
    a = a.reshape(size, k, size, k).max(axis=(1, 3))
    return a.astype(np.float32).ravel()


def split_of(key_id: str, raster_hash: str) -> str:
    h = int(hashlib.md5(raster_hash.encode()).hexdigest()[:8], 16) / 0xFFFFFFFF
    return "train" if h < 0.6 else ("discovery" if h < 0.8 else "reserve")


def stroke_features(strokes):
    import numpy as np                                                            # noqa: PLC0415
    feats = []
    for xs, ys in strokes:
        xs_, ys_ = np.asarray(xs, float), np.asarray(ys, float)
        length = float(np.sum(np.hypot(np.diff(xs_), np.diff(ys_)))) if len(xs_) > 1 else 0.0
        feats.append([xs_.min(), xs_.max(), ys_.min(), ys_.max(), xs_.mean(), ys_.mean(),
                      length, len(xs_), xs_[0], ys_[0], xs_[-1], ys_[-1]])
    return np.asarray(feats, float)


def arm_p01() -> int:
    import numpy as np                                                            # noqa: PLC0415
    from sklearn.linear_model import LogisticRegression                           # noqa: PLC0415
    run = CardRun("P01", "s4_run_p.py")
    t0 = time.time()
    raw = run.out / "raw"
    fetch = {}
    total = 0
    for cat in CATEGORIES:
        if total >= CAP_TOTAL_BYTES:
            fetch[cat] = {"skipped": "total cap"}
            continue
        fetch[cat] = fetch_prefix(cat, raw / f"{cat}.ndjson.prefix")
        total += fetch[cat].get("bytes", 0)
    data = {cat: load_drawings(cat, raw / f"{cat}.ndjson.prefix") for cat in CATEGORIES
            if (raw / f"{cat}.ndjson.prefix").exists()}
    counts = {cat: len(v) for cat, v in data.items()}
    if any(c < MIN_PER_CAT for c in counts.values()) or len(counts) < 4:
        run.finish({"fetch": fetch, "counts": counts, "attribution": "Quick, Draw! dataset, Google Creative Lab, CC BY 4.0"},
                   {"exec": "BLOCKED", "outcome": "VOID", "reason": f"DATA_BLOCKED: fewer than {MIN_PER_CAT} usable drawings in a category"}, 0.0)
        return 0
    # rasters, targets, splits (near-duplicates share a raster hash and therefore a split)
    X, Xn, y, cats, splits, keys = [], [], [], [], [], []
    for cat, dl in data.items():
        for d in dl:
            r = render(d["strokes"])
            rh = hashlib.md5(r.astype(np.uint8).tobytes()).hexdigest()
            X.append(r)
            Xn.append(render(d["strokes"], normalize=True))
            xs, ys = d["strokes"][0]
            y.append(quadrant(xs[0], ys[0]))
            cats.append(cat)
            splits.append(split_of(d["key_id"], rh))
            keys.append(d["key_id"])
    X, Xn, y = np.asarray(X), np.asarray(Xn), np.asarray(y)
    cats, splits = np.asarray(cats), np.asarray(splits)
    # the confirmation run (F01, S4_SPLIT=confirmation) evaluates on the RESERVE drawings,
    # allocated by hash before any fitting and never scored in discovery; the training
    # split is the same either way
    eval_split = "reserve" if run.split == "confirmation" else "discovery"
    tr, te = splits == "train", splits == eval_split
    marginal = {str(q): float(np.mean(y == q)) for q in range(4)}
    labels = [0, 1, 2, 3]

    def bacc(pred, truth):
        return s4_lib.balanced_accuracy(list(pred), list(truth), labels)
    # cheap priors
    cat_prior = {cat: int(np.bincount(y[tr & (cats == cat)], minlength=4).argmax()) for cat in CATEGORIES}
    pred_cat = np.array([cat_prior[c] for c in cats[te]])

    def ink_quadrant(r):
        g = r.reshape(RASTER, RASTER)
        h = RASTER // 2
        q = [g[:h, :h].sum(), g[:h, h:].sum(), g[h:, :h].sum(), g[h:, h:].sum()]
        return int(np.argmax(q)), int(np.argmin(q))
    ink_max = np.array([ink_quadrant(r)[0] for r in X[te]])
    ink_min = np.array([ink_quadrant(r)[1] for r in X[te]])

    def bbox_corner(d):
        pts = [(x, yv) for xs, ys in d["strokes"] for x, yv in zip(xs, ys)]
        return quadrant(min(p[0] for p in pts), min(p[1] for p in pts))
    all_d = [d for cat in data for d in data[cat]]
    bbox = np.array([bbox_corner(d) for d, s in zip(all_d, splits) if s == eval_split])
    priors = {"category_only": bacc(pred_cat, y[te]), "ink_max_quadrant": bacc(ink_max, y[te]),
              "ink_min_quadrant": bacc(ink_min, y[te]), "bbox_corner": bacc(bbox, y[te])}
    # the raster classifier, raw and normalized
    clf = LogisticRegression(max_iter=2000, C=0.05, class_weight="balanced").fit(X[tr], y[tr])
    pred = clf.predict(X[te])
    clf_n = LogisticRegression(max_iter=2000, C=0.05, class_weight="balanced").fit(Xn[tr], y[tr])
    pred_n = clf_n.predict(Xn[te])
    # rotation sensitivity: rotate rasters 90 degrees and labels accordingly
    rot_map = {0: 1, 1: 3, 3: 2, 2: 0}
    Xr = np.asarray([np.rot90(r.reshape(RASTER, RASTER), -1).ravel() for r in X[te]])
    yr = np.array([rot_map[int(v)] for v in y[te]])
    pred_r = clf.predict(Xr)
    best_prior = max(priors.values())
    # paired contrast by drawing on the FROZEN estimand, balanced accuracy: each drawing's
    # correctness is reweighted by its label's share of the discovery split so that the
    # mean over drawings is the balanced accuracy (the first landed version paired raw
    # correctness, which the 60-percent majority quadrant dominates; the raw contrast is
    # kept beside it)
    best_name = max(priors, key=priors.get)
    prior_pred = {"category_only": pred_cat, "ink_max_quadrant": ink_max, "ink_min_quadrant": ink_min, "bbox_corner": bbox}[best_name]
    n_te = int(te.sum())
    lab_w = {q: n_te / (4 * max(1, int(np.sum(y[te] == q)))) for q in labels}
    per_unit = {k: (float(p == t) - float(q == t)) * lab_w[int(t)]
                for k, p, q, t in zip(np.asarray(keys)[te], pred, prior_pred, y[te])}
    per_unit_raw = {k: float(p == t) - float(q == t) for k, p, q, t in zip(np.asarray(keys)[te], pred, prior_pred, y[te])}
    primary = s4_lib.cluster_bootstrap_ci(per_unit, SEED + 1)
    primary_raw = s4_lib.cluster_bootstrap_ci(per_unit_raw, SEED + 1)
    # provenance rows, one per scored drawing (the reader is the CPU classifier)
    for k, c, p, q, t in zip(np.asarray(keys)[te], cats[te], pred, prior_pred, y[te]):
        run.row("cpu-logistic-raster", str(k), f"P01|{c}|{k}", "raster",
                {"domain": str(c), "input": "raster"}, int(t), "recorded_drawing", "artifact_only",
                {"valid": True, "validity_reason": "ok", "pred": int(p), "probs": None, "labels": None},
                float(p == t), extra={"best_prior_pred": int(q), "best_prior": best_name})
    run.flush()
    per_cat = {cat: {"n_test": int(np.sum(te & (cats == cat))),
                     "raster_bacc": bacc(pred[cats[te] == cat], y[te][cats[te] == cat]),
                     "best_prior_bacc": bacc(prior_pred[cats[te] == cat], y[te][cats[te] == cat])} for cat in CATEGORIES}
    threshold = run.design.get("thresholds", {}).get("P01", 0.05) or 0.05
    verdict = run.classify(primary, threshold)
    if (time.time() - t0) > CPU_CAP_S:
        verdict["note"] = "CPU cap exceeded"
    write_json(run.out / "splits.json", {"n": int(len(y)), "train": int(tr.sum()), "evaluated": eval_split,
                                        "discovery": int((splits == "discovery").sum()),
                                        "reserve": int((splits == "reserve").sum())})
    run.finish({"fetch": fetch, "counts": counts, "attribution": "Quick, Draw! dataset, Google Creative Lab, CC BY 4.0",
                "target_marginal_discovery": marginal, "priors_balanced_accuracy": priors,
                "raster_balanced_accuracy": bacc(pred, y[te]), "raster_normalized_balanced_accuracy": bacc(pred_n, y[te]),
                "rotation_transformed_labels_balanced_accuracy": bacc(pred_r, yr),
                "primary_raster_minus_best_prior": {**primary, "best_prior": best_name, "best_prior_bacc": best_prior,
                                                    "estimand": "balanced accuracy, label-reweighted per drawing"},
                "raw_accuracy_raster_minus_best_prior": primary_raw,
                "label_weights_discovery": {str(q): round(w, 3) for q, w in lab_w.items()},
                "per_category": per_cat, "cpu_minutes": round((time.time() - t0) / 60, 2),
                "metadata_stripped": ["key_id", "timestamp", "countrycode", "recognized", "stroke order", "direction"]},
               {"exec": "COMPLETE", "primary": "first-stroke quadrant from the final raster minus the best cheap prior", **verdict}, 0.0)
    return 0


def arm_p02() -> int:
    import numpy as np                                                            # noqa: PLC0415
    from sklearn.linear_model import LogisticRegression                           # noqa: PLC0415
    run = CardRun("P02", "s4_run_p.py")
    t0 = time.time()
    raw = S4 / "P01" / "raw"
    data = {cat: load_drawings(cat, raw / f"{cat}.ndjson.prefix") for cat in CATEGORIES
            if (raw / f"{cat}.ndjson.prefix").exists()}
    if len(data) < 4:
        run.finish({}, {"exec": "BLOCKED", "outcome": "NOT_RUN", "reason": "P01 data absent"}, 0.0)
        return 0
    # unordered stroke sets: strokes sorted canonically (by centroid x, then y) so no order survives
    rows_tr, y_tr, rows_te, y_te, groups_te, heur_te, chance_te, prefix_tr, prefix_te = [], [], [], [], [], [], [], [], []
    heur_tr = []            # the geometry heuristics' hits on the TRAIN split choose the comparator
    # the confirmation run (F01) evaluates on the reserve drawings, never seen in discovery
    eval_split = "reserve" if run.split == "confirmation" else "discovery"
    skip_split = "discovery" if eval_split == "reserve" else "reserve"
    for cat, dl in data.items():
        for d in dl:
            r = render(d["strokes"])
            rh = hashlib.md5(r.astype(np.uint8).tobytes()).hexdigest()
            sp = split_of(d["key_id"], rh)
            if sp == skip_split:
                continue
            F = stroke_features(d["strokes"])
            order = sorted(range(len(F)), key=lambda i: (F[i][4], F[i][5]))   # canonical, order-free
            rel = []
            for i in order:
                f = F[i]
                rel.append(np.concatenate([f, [f[6] / (F[:, 6].sum() + 1e-9), f[7] / (F[:, 7].sum() + 1e-9),
                                               f[4] - F[:, 4].mean(), f[5] - F[:, 5].mean()]]))
            first = order.index(0)          # the true first stroke's position in the canonical set
            # geometry heuristics: top-left-most start, and longest stroke
            tl = int(np.argmin([F[i][8] + F[i][9] for i in order]))
            longest = int(np.argmax([F[i][6] for i in order]))
            # prefix condition: given the true first stroke, predict the next stroke's quadrant
            nxt = d["strokes"][1]
            q_next = quadrant(nxt[0][0], nxt[1][0])
            f0 = F[0]
            pf = np.concatenate([f0, [len(F)]])
            tgt = (rows_tr, y_tr, prefix_tr) if sp == "train" else (rows_te, y_te, prefix_te)
            for j, v in enumerate(rel):
                tgt[0].append(v)
                tgt[1].append(int(j == first))
            tgt[2].append((pf, q_next, quadrant(f0[10], f0[11])))
            if sp == eval_split:
                groups_te.append((len(rel), first, tl, longest))
                heur_te.append((tl == first, longest == first))
                chance_te.append(1.0 / len(rel))
            else:
                heur_tr.append((tl == first, longest == first))
    Xtr, ytr = np.asarray(rows_tr), np.asarray(y_tr)
    clf = LogisticRegression(max_iter=2000, C=0.5, class_weight="balanced").fit(Xtr, ytr)
    # per-drawing ranking on the discovery split
    scores = clf.decision_function(np.asarray(rows_te))
    pos = 0
    hits_learned, hits_tl, hits_long, chance = [], [], [], []
    for (n, first, tl, longest), (h_tl, h_long), ch in zip(groups_te, heur_te, chance_te):
        s = scores[pos:pos + n]
        pos += n
        hits_learned.append(float(int(np.argmax(s)) == first))
        hits_tl.append(float(h_tl))
        hits_long.append(float(h_long))
        chance.append(ch)
    # the comparator is the ONE geometry heuristic that does best on the train split (the
    # frozen estimand: learned prior minus the geometry heuristic); the per-drawing better
    # of the two heuristics is an oracle over heuristics and is kept as the severe form
    tl_train = sum(h[0] for h in heur_tr) / max(1, len(heur_tr))
    long_train = sum(h[1] for h in heur_tr) / max(1, len(heur_tr))
    best_heur = "longest" if long_train >= tl_train else "top_left"
    hits_best = hits_long if best_heur == "longest" else hits_tl
    per_unit = {str(i): hits_learned[i] - hits_best[i] for i in range(len(hits_learned))}
    per_unit_severe = {str(i): hits_learned[i] - max(hits_tl[i], hits_long[i]) for i in range(len(hits_learned))}
    primary = s4_lib.cluster_bootstrap_ci(per_unit, SEED + 2)
    primary_severe = s4_lib.cluster_bootstrap_ci(per_unit_severe, SEED + 2)
    for i in range(len(hits_learned)):
        run.row("cpu-logistic-strokes", f"d{i}", f"P02|{eval_split}|{i}", "unordered_strokes",
                {"domain": "all", "access": "unordered_strokes"}, "first_stroke", "recorded_drawing",
                "unordered_process", {"valid": True, "validity_reason": "ok", "pred": None, "probs": None, "labels": None},
                hits_learned[i], extra={"heuristic_hit": max(hits_tl[i], hits_long[i]),
                                        "best_heuristic_hit": hits_best[i], "best_heuristic": best_heur,
                                        "chance": chance[i]})
    run.flush()
    # collision floor: the permutation chance for a set-only reader without features is 1/n
    # prefix condition: learned transition prior vs nearest-continuation heuristic
    Ptr = np.asarray([p for p, _, _ in prefix_tr])
    qtr = np.asarray([q for _, q, _ in prefix_tr])
    Pte = np.asarray([p for p, _, _ in prefix_te])
    qte = np.asarray([q for _, q, _ in prefix_te])
    hte = np.asarray([h for _, _, h in prefix_te])            # heuristic: next starts where the first ended
    pclf = LogisticRegression(max_iter=2000, C=0.5, class_weight="balanced").fit(Ptr, qtr)
    ppred = pclf.predict(Pte)
    labels = [0, 1, 2, 3]
    prefix = {"learned_transition_bacc": s4_lib.balanced_accuracy(list(ppred), list(qte), labels),
              "end_of_first_heuristic_bacc": s4_lib.balanced_accuracy(list(hte), list(qte), labels),
              "n": int(len(qte))}
    for i, (p, t, h) in enumerate(zip(ppred, qte, hte)):
        run.row("cpu-logistic-transition", f"d{i}", f"P02|{eval_split}|{i}", "prefix",
                {"domain": "all", "access": "prefix"}, int(t), "recorded_drawing", "ordered_history",
                {"valid": True, "validity_reason": "ok", "pred": int(p), "probs": None, "labels": None},
                float(p == t), extra={"heuristic_pred": int(h)})
    run.flush()
    threshold = run.design.get("thresholds", {}).get("P02", 0.05) or 0.05
    verdict = run.classify(primary, threshold)
    run.finish({"access_levels": {"unordered_strokes": "privileged segmentation, order stripped by canonical sort",
                                  "prefix": "process-assisted: the true first stroke revealed"},
                "first_stroke_identification": {"learned": sum(hits_learned) / len(hits_learned),
                                                "top_left_heuristic": sum(hits_tl) / len(hits_tl),
                                                "longest_heuristic": sum(hits_long) / len(hits_long),
                                                "permutation_chance": sum(chance) / len(chance), "n": len(hits_learned)},
                "primary_learned_minus_best_heuristic": {**primary, "heuristic": best_heur,
                                                         "chosen_on": "train split",
                                                         "train_hit_rates": {"top_left": round(tl_train, 3), "longest": round(long_train, 3)}},
                "severe_learned_minus_per_drawing_best_heuristic": primary_severe,
                "prefix_condition": prefix,
                "collision_note": "every ordering of the same strokes gives the same raster and the same unordered set; the permutation chance is the collision floor",
                "cpu_minutes": round((time.time() - t0) / 60, 2)},
               {"exec": "COMPLETE", "primary": "learned first-stroke identification minus geometry heuristic (unordered access)", **verdict}, 0.0)
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--card", required=True, choices=["P01", "P02"])
    a = ap.parse_args()
    return {"P01": arm_p01, "P02": arm_p02}[a.card]()


if __name__ == "__main__":
    sys.exit(main())
