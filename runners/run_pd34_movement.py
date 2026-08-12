"""PD-34 — polish movement, the order-sensitive form.

PD-1's dispersion statistics could not measure movement in principle (L53/L55): variance is
order-invariant, so a within-item shuffle can never fail it and the shuffle ratio cannot exceed
one. The order-sensitive form can. The curator's restated account (2026-08-10) is attention
reallocating across concurrent sub-goals over a long stay with a piece, observable as readable
goals moving through the paper, and he pointed at exactly this instrument class.

Statistic per (item, feature): |Spearman rho| between the feature's window series and window
position. Null: within-item shuffles of the same series, which is valid here because the
statistic is order-sensitive. Question: do polish-side features carry more positional structure
than depth-side features?

Gate (validate the ruler before the signal): a planted linear-trend series must beat its shuffle
null decisively; a planted iid-noise series must not. VOID if either fails.

Verdicts: POLISH-MOVES-MORE / DEPTH-MOVES-MORE at Mann-Whitney p < 0.05 on per-feature mean
shuffle-z; NO-DIFFERENCE otherwise.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
from scipy import stats

REPO = Path(__file__).resolve().parents[1]

# The same side banks the PD-33 family uses, so the sides mean the same thing everywhere.
POLISH_PATTERNS = ("readability", "flesch", "ttr", "type_token", "punct", "exclam",
                   "quote", "emph", "amp", "smog", "kincaid", "coleman", "ari",
                   "uword", "sent_len", "word_len", "syll")
DEPTH_PATTERNS = ("caus", "conc", "cond", "osub", "whcl", "whsub", "whobj", "thac",
                  "thvc", "tobj", "tsub", "presp", "pastp", "nomz", "gerund")

N_PERM = 100
MIN_WINDOWS = 6
RNG = np.random.default_rng(2026)
SIGNED = False


def abs_rho(series: np.ndarray) -> float:
    pos = np.arange(len(series), dtype=float)
    r = stats.spearmanr(series, pos).statistic
    if not np.isfinite(r):
        return 0.0
    return float(r) if SIGNED else float(abs(r))


def shuffle_z(series: np.ndarray) -> float | None:
    """z of the real |rho| against its own within-item shuffle null."""
    if len(series) < MIN_WINDOWS or np.allclose(series, series[0]):
        return None
    real = abs_rho(series)
    null = np.empty(N_PERM)
    s = series.copy()
    for k in range(N_PERM):
        RNG.shuffle(s)
        null[k] = abs_rho(s)
    sd = float(null.std())
    if sd == 0.0:
        return None
    return (real - float(null.mean())) / sd


def main() -> None:
    global SIGNED
    ap = argparse.ArgumentParser()
    ap.add_argument("--cache", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--signed", action="store_true",
                    help="PD-2's decay form: signed trend instead of |trend|; negative "
                         "medians mean the side falls across the artifact")
    args = ap.parse_args()
    SIGNED = bool(args.signed)

    # ── the ruler gate, before any data
    trend = np.arange(12, dtype=float) + RNG.normal(0, 0.1, 12)
    noise_z = [shuffle_z(RNG.normal(0, 1, 12)) for _ in range(50)]
    noise_z = [z for z in noise_z if z is not None]
    trend_z = shuffle_z(trend)
    gate = {"planted_trend_z": trend_z, "planted_noise_mean_z": float(np.mean(noise_z))}
    if trend_z is None or trend_z < 3.0 or abs(np.mean(noise_z)) > 0.5:
        out = {"verdict": "VOID", "reason": "ruler gate failed", "gate": gate}
        Path(args.out).write_text(json.dumps(out, indent=1), encoding="utf-8",
                                  newline="\n")
        print(f">>> VOID: ruler gate failed {gate}")
        sys.exit(1)
    print(f"gate ok: planted trend z {trend_z:.1f}, planted noise mean z "
          f"{np.mean(noise_z):+.2f}")

    d = json.loads(Path(args.cache).read_text(encoding="utf-8"))
    items = [it for it in d["items"] if it.get("n_windows", 0) >= MIN_WINDOWS]
    keys = list(items[0]["windows"][0])
    pol = [k for k in keys if any(p in k.lower() for p in POLISH_PATTERNS)]
    dep = [k for k in keys if any(p in k.lower() for p in DEPTH_PATTERNS)]
    print(f"{len(items)} items, {len(pol)} polish / {len(dep)} depth features")

    def feature_mean_z(feat: str) -> float | None:
        zs = []
        for it in items:
            series = np.array([w.get(feat, np.nan) for w in it["windows"]], dtype=float)
            if np.isnan(series).any():
                continue
            z = shuffle_z(series)
            if z is not None:
                zs.append(z)
        return float(np.mean(zs)) if len(zs) >= 10 else None

    pz = np.array([z for z in (feature_mean_z(k) for k in pol) if z is not None])
    dz = np.array([z for z in (feature_mean_z(k) for k in dep) if z is not None])
    _, p = stats.mannwhitneyu(pz, dz, alternative="two-sided")
    pm, dm = float(np.median(pz)), float(np.median(dz))
    if SIGNED:
        _, p_pol = stats.wilcoxon(pz) if len(pz) >= 10 else (None, 1.0)
        if p_pol < 0.05:
            verdict = "POLISH-DECAYS" if pm < 0 else "POLISH-RISES"
        else:
            verdict = "NO-SIGNED-TREND"
    elif p < 0.05:
        verdict = "POLISH-MOVES-MORE" if pm > dm else "DEPTH-MOVES-MORE"
    else:
        verdict = "NO-DIFFERENCE"
    print(f"positional structure (mean shuffle-z per feature): polish {pm:.2f} vs "
          f"depth {dm:.2f} (p={p:.2e})\n  >>> {verdict}")

    out = {"corpus": d.get("corpus"), "signed": SIGNED, "n_items": len(items),
           "n_polish_features": int(len(pz)), "n_depth_features": int(len(dz)),
           "polish_median_z": pm, "depth_median_z": dm, "p": float(p),
           "gate": gate, "verdict": verdict}
    op = Path(args.out)
    op.parent.mkdir(parents=True, exist_ok=True)
    op.write_text(json.dumps(out, indent=1), encoding="utf-8", newline="\n")
    print(f"wrote {op}")


if __name__ == "__main__":
    main()
