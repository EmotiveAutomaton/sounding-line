"""G76 — the induction control the function-word separation (L16) has been owed since it landed.

L16: closed-class function-word rates classify rung on all three ladders (SEPARATES, up to 2.3x
chance single-artifact). The owed control: is the classifier reading style the prompt INDUCED
rather than a maker state? The original TODO spec said regress on raw specification identity —
the dose-eating construction L22 killed (row-sum of the indicator IS the rung). This runner
builds the control in the fair form (L23): centre the specification indicators WITHIN RUNG so
they carry only which-specs-given-how-many, residualize every function-word rate out-of-fold,
and re-classify rung from the residuals.

Known-answer gates, run before any real read (LESSONS §3):
  RAW BASELINE   the raw arm must reproduce L16's single-artifact cells (0.320/0.330/0.467)
                 within tolerance — the falsifier-baseline lesson (L93) applied to ourselves
  PLANTED-DOSE   a synthetic feature bank carrying rung+noise must SURVIVE the fair control
                 (the control must not eat a true dose response)
  PLANTED-IDENTITY  a bank built purely from the centred indicators must classify at chance in
                 both arms (centred identity carries no rung information by construction)

Arms per corpus:
  raw            classify rung from the 130 function-word rates (5-fold, logistic)
  fair-residual  the same, after oof-ridge removal of within-rung specification identity
  old-residual   the same, after removal on the RAW indicators — the dose-eating form, kept as
                 the measured demonstration of why the old spec was wrong

Verdict per corpus:
  SURVIVES   fair-residual margin over chance > 0.10 and beats its 200-permutation floor (p<.05)
  REDUCED    fair-residual above the permutation floor but margin ≤ 0.10 where raw was above
  COLLAPSES  fair-residual inside its permutation floor band

Inherited caveat, stated once (L22): induction that operates through the COUNT of specifications
is indistinguishable from a dose response by any regression control; survival here licenses
"not explained by which-specs identity", the same license L23/L24 carry.

CPU-only; no GPU lock. Output: results/g76_fw_induction.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

OUT = REPO / "results" / "g76_fw_induction.json"

# L16's single-artifact cells — the raw arm's known answer (restored rows, seeded pooling)
L16_SINGLE = {"ladder": 0.320, "ladder2": 0.330, "ladder3": 0.467}
BASELINE_TOL = 0.08


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpora", default="ladder,ladder2,ladder3")
    ap.add_argument("--perms", type=int, default=200)
    args = ap.parse_args()

    import random                                                     # noqa: PLC0415

    import numpy as np                                                # noqa: PLC0415
    from sklearn.linear_model import LogisticRegression, RidgeCV      # noqa: PLC0415
    from sklearn.model_selection import KFold, StratifiedKFold        # noqa: PLC0415
    from sklearn.preprocessing import StandardScaler                  # noqa: PLC0415

    from runners.make_intent_ladder import SPECS as BASE              # noqa: PLC0415
    from runners.run_induction_v2 import LADDERS                      # noqa: PLC0415
    from runners.run_void_power import FUNCTION_WORDS, load_corpus    # noqa: PLC0415

    def fw_vector(text: str) -> np.ndarray:
        from collections import Counter                               # noqa: PLC0415
        toks = [w.strip(".,;:!?\"'()[]—-").lower() for w in text.split()]
        toks = [w for w in toks if w]
        n = max(len(toks), 1)
        c = Counter(toks)
        return np.array([c[w] / n * 1000 for w in FUNCTION_WORDS])

    def classify(F: np.ndarray, y: np.ndarray, seed: int = 0) -> float:
        folds = min(5, int(np.bincount(np.searchsorted(sorted(set(y)), y)).min()))
        if folds < 2:
            return float("nan")
        sc, accs = StandardScaler(), []
        for tr, te in StratifiedKFold(folds, shuffle=True, random_state=seed).split(F, y):
            clf = LogisticRegression(max_iter=3000, C=1.0)
            clf.fit(sc.fit_transform(F[tr]), y[tr])
            accs.append(float((clf.predict(sc.transform(F[te])) == y[te]).mean()))
        return float(np.mean(accs))

    def oof_residual(F: np.ndarray, M: np.ndarray) -> tuple[np.ndarray, float]:
        """Residualize every feature on M out-of-fold; return residuals and the dose leak
        (median |spearman| of the per-feature predictions against rung is computed by caller)."""
        pred = np.zeros_like(F)
        for tr, te in KFold(5, shuffle=True, random_state=0).split(M):
            model = RidgeCV(alphas=np.logspace(-2, 3, 20))
            model.fit(M[tr], F[tr])
            pred[te] = model.predict(M[te])
        return F - pred, pred

    rng = np.random.default_rng(29)
    out = {"function_words": len(FUNCTION_WORDS), "corpora": {}, "gates": {}}

    # ---- gates on synthetic banks (one corpus's design matrix suffices; use ladder2's shape)
    def build_design(corpus: str):
        cfg = LADDERS[corpus]
        if cfg["pool"] == "extended":
            from runners.make_ladder3 import SPECS as POOL            # noqa: PLC0415
        else:
            POOL = BASE
        pool = list(POOL)
        rows = []
        d = REPO / "corpora" / corpus
        man = json.loads((d / "manifest.json").read_text(encoding="utf-8"))
        for it in man["items"]:
            p = d / f"{it['id']}.txt"
            rung = it.get("rung")
            if not p.exists() or not isinstance(rung, int):
                continue
            idx = int(it["id"].split("_")[1])
            drawn = (random.Random(cfg["seed"] + rung * 1000 + idx).sample(pool, rung)
                     if rung > 0 else [])
            rows.append({"rung": rung, "spec_idx": sorted(pool.index(s) for s in drawn),
                         "text_path": p})
        n = len(rows)
        rung = np.array([r["rung"] for r in rows], dtype=float)
        X = np.zeros((n, len(pool)))
        for i, r in enumerate(rows):
            X[i, r["spec_idx"]] = 1.0
        Xc = X.copy()
        for g in sorted(set(rung)):
            m = rung == g
            Xc[m] -= Xc[m].mean(0)
        return rows, rung, X, Xc

    g_rows, g_rung, g_X, g_Xc = build_design("ladder2")
    y_g = g_rung.astype(int)

    F_dose = np.column_stack([g_rung + rng.normal(0, 1.0, len(g_rung)) for _ in range(8)]
                             + [rng.normal(0, 1.0, len(g_rung)) for _ in range(24)])
    Rd, _ = oof_residual(F_dose, g_Xc)
    gate_dose_raw = classify(F_dose, y_g)
    gate_dose_fair = classify(Rd, y_g)
    W = rng.normal(0, 1.0, (g_Xc.shape[1], 32))
    F_id = g_Xc @ W + rng.normal(0, 0.1, (len(g_rung), 32))
    gate_id_raw = classify(F_id, y_g)
    gate_id_fair = classify(oof_residual(F_id, g_Xc)[0], y_g)
    chance_g = 1.0 / len(set(y_g))
    gates_pass = (gate_dose_fair - chance_g > 0.10) and (abs(gate_id_raw - chance_g) < 0.12) \
        and (abs(gate_id_fair - chance_g) < 0.12)
    out["gates"] = {"planted_dose_raw": gate_dose_raw, "planted_dose_fair": gate_dose_fair,
                    "planted_identity_raw": gate_id_raw, "planted_identity_fair": gate_id_fair,
                    "chance": chance_g, "pass": bool(gates_pass)}
    print(f"gates: planted-dose fair {gate_dose_fair:.3f} (raw {gate_dose_raw:.3f}), "
          f"planted-identity raw/fair {gate_id_raw:.3f}/{gate_id_fair:.3f} vs chance "
          f"{chance_g:.3f} -> {'PASS' if gates_pass else 'FAIL'}", flush=True)
    if not gates_pass:
        out["verdict"] = "GATES-FAILED"
        OUT.write_text(json.dumps(out, indent=2), encoding="utf-8", newline="\n")
        print(">>> GATES-FAILED — no real read taken")
        return

    # ---- the real arms
    from scipy import stats                                           # noqa: PLC0415
    for corpus in args.corpora.split(","):
        rows, rung, X, Xc = build_design(corpus)
        y = rung.astype(int)
        F = np.array([fw_vector(r["text_path"].read_text(encoding="utf-8")) for r in rows])
        chance = 1.0 / len(set(y))

        # the raw baseline is fold-seed sensitive at n=50, so the known-answer comparison uses
        # the mean over ten fold seeds and records the spread rather than one draw
        raw_sweep = [classify(F, y, seed=s) for s in range(10)]
        acc_raw = float(np.mean(raw_sweep))
        R_fair, pred_fair = oof_residual(F, Xc)
        R_old, pred_old = oof_residual(F, X)
        acc_fair = float(np.mean([classify(R_fair, y, seed=s) for s in range(10)]))
        acc_old = float(np.mean([classify(R_old, y, seed=s) for s in range(10)]))
        with np.errstate(invalid="ignore"):
            leak_fair = float(np.nanmedian([abs(stats.spearmanr(pred_fair[:, j], rung).statistic)
                                            for j in range(F.shape[1])]))
            leak_old = float(np.nanmedian([abs(stats.spearmanr(pred_old[:, j], rung).statistic)
                                           for j in range(F.shape[1])]))

        null = []
        for i in range(args.perms):
            yp = np.array(y)
            rng.shuffle(yp)
            null.append(classify(R_fair, yp, seed=i + 1))
        null = np.array(null)
        p_perm = float((null >= acc_fair).mean())

        base = L16_SINGLE.get(corpus)
        base_ok = base is None or abs(acc_raw - base) <= BASELINE_TOL
        margin = acc_fair - chance
        if not base_ok:
            verdict = "BASELINE-MISMATCH"
        elif margin > 0.10 and p_perm < 0.05:
            verdict = "SURVIVES"
        elif p_perm < 0.05:
            verdict = "REDUCED"
        else:
            verdict = "COLLAPSES"
        out["corpora"][corpus] = {
            "n": len(y), "chance": chance, "acc_raw": acc_raw,
            "acc_raw_seed_range": [float(min(raw_sweep)), float(max(raw_sweep))],
            "l16_reference": base, "baseline_ok": bool(base_ok),
            "acc_fair_residual": acc_fair, "acc_old_residual": acc_old,
            "dose_leak_fair_median": leak_fair, "dose_leak_old_median": leak_old,
            "perm_null_mean": float(null.mean()), "perm_p": p_perm, "verdict": verdict}
        print(f"{corpus}: raw {acc_raw:.3f} (L16 {base}) | fair {acc_fair:.3f} "
              f"(perm p={p_perm:.3f}, leak {leak_fair:.3f}) | old {acc_old:.3f} "
              f"(leak {leak_old:.3f}) | chance {chance:.3f} -> {verdict}", flush=True)

    verdicts = [c["verdict"] for c in out["corpora"].values()]
    out["verdict"] = "/".join(verdicts)
    OUT.write_text(json.dumps(out, indent=2), encoding="utf-8", newline="\n")
    print(f"\n>>> G76 {out['verdict']}\nwrote {OUT.relative_to(REPO)}")


if __name__ == "__main__":
    main()
