"""The per-layer intent correlation — the thing that survived when the profile died.

── WHY THIS REPLACES THE RATIO ───────────────────────────────────────────────────────────────

The depth sweep established two things. The **shape** of the affective-response profile across layers
is identical whether you feed the model intent-laden text or no-maker text — it is a property of the
architecture and carries no information. But the **correlation with specified intent, computed layer
by layer**, is not: two independently generated ladders agree at 0.97 on which layers carry it, and
the strongest single layer beats anything the old two-locus ratio produced.

**The old measure threw away 27 of 29 layers to compute one number from two of them, and the two were
hand-picked by looking at a prior result.** This measures every layer and picks none.

── WHAT IS MEASURED, PER LAYER ───────────────────────────────────────────────────────────────

    rho          correlation between specified intent and affective signal at that layer
    null rho     the same, for matched random directions. Every layer priced against its own null,
                 because the magnitude of the old ratio was NOT distinguishable from random
    partial      the same, with the number of words removed -- length has been a suppressor here
                 rather than a confound, so this can go up
    induction    the same, with the identity of the drawn specifications removed out-of-fold.
                 This is the control that killed all three text-feature candidates

── PRE-REGISTERED ────────────────────────────────────────────────────────────────────────────

    SURVIVES    at least one layer where the correlation clears its own random-direction null AND
                survives removing both length and specification identity
    ARCHITECTURE the correlation appears at the same layers regardless of corpus, including the
                 no-maker corpus -- meaning it too is a property of the model
    DEAD        no layer survives the controls

**The no-maker corpus is the sharpest control here.** It has rungs by construction only — the "intent"
labels are arbitrary for text with no maker. **A correlation there is a correlation with nothing**, and
if it appears, the measure is reading the label rather than the text.
"""

from __future__ import annotations

import argparse
import json
import random
import statistics
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

RESULTS = REPO / "results" / "layer_correlation"

LADDERS = {
    "ladder":  {"seed": 70000,  "topic_off": 0, "pool": "base"},
    "ladder2": {"seed": 90000,  "topic_off": 5, "pool": "base"},
    "ladder3": {"seed": 110000, "topic_off": 3, "pool": "extended"},
}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--save-signals", action="store_true",
                    help="write to a _sig-suffixed file (fresh, never guarded-skipped) — the "
                         "permutation null (G107) needs the per-artifact signal matrix")
    ap.add_argument("--corpus", default="ladder2")
    ap.add_argument("--model", default=None)
    ap.add_argument("--n-random", type=int, default=12)
    ap.add_argument("--device", default="cuda")
    args = ap.parse_args()

    import numpy as np                                               # noqa: PLC0415
    from scipy import stats                                          # noqa: PLC0415
    from scipy.stats import rankdata                                 # noqa: PLC0415
    from sklearn.linear_model import RidgeCV                         # noqa: PLC0415
    from sklearn.model_selection import KFold                        # noqa: PLC0415

    from soundingline.probe.activations import (DEFAULT_MODEL, Reader,  # noqa: PLC0415
                                                fit_directions)
    from runners.run_b import split                                  # noqa: PLC0415
    from runners.run_layer_ratio import windows                      # noqa: PLC0415
    from runners.make_intent_ladder import SPECS as BASE, TOPICS     # noqa: PLC0415

    model_name = args.model or DEFAULT_MODEL
    print(f"loading {model_name} ...", flush=True)
    reader = Reader(model_name, device=args.device)
    fit, _ = split()
    dirs = fit_directions(reader, fit)
    n_layers = dirs.n_layers
    concepts = list(dirs.concepts)

    d = REPO / "corpora" / args.corpus
    man = json.loads((d / "manifest.json").read_text(encoding="utf-8"))
    cfg = LADDERS.get(args.corpus)
    if cfg and cfg["pool"] == "extended":
        from runners.make_ladder3 import SPECS as POOL               # noqa: PLC0415
    else:
        POOL = BASE

    rows = []
    for it in man["items"]:
        p = d / f"{it['id']}.txt"
        if not p.exists():
            continue
        text = p.read_text(encoding="utf-8")
        group = it.get("rung", it.get("kind"))
        specs = set()
        if cfg and isinstance(group, int) and group:
            idx = int(it["id"].split("_")[1])
            rng = random.Random(cfg["seed"] + group * 1000 + idx)
            _ = TOPICS[(idx + cfg["topic_off"]) % len(TOPICS)]
            specs = set(rng.sample(POOL, group))
        rows.append({"group": group, "text": text, "specs": specs,
                     "words": len(text.split())})
    # non-numeric groups (the no-maker kinds) get an arbitrary index: that is the point of the control
    if not all(isinstance(r["group"], (int, float)) for r in rows):
        order = {k: i for i, k in enumerate(sorted({str(r["group"]) for r in rows}))}
        for r in rows:
            r["group"] = order[str(r["group"])]
    print(f"{args.corpus}: {len(rows)} artifacts, {n_layers} layers\n", flush=True)

    rng = np.random.default_rng(3)
    probe = reader.read("shape probe")
    widths = [len(probe.acts[L]) for L in range(n_layers)]
    rand = [[rng.standard_normal(widths[L]) for L in range(n_layers)]
            for _ in range(args.n_random)]

    sig = np.zeros((len(rows), n_layers))
    nul = np.zeros((len(rows), n_layers, args.n_random))
    for i, r in enumerate(rows):
        ws = windows(r["text"])
        s = np.zeros((len(ws), n_layers))
        nn = np.zeros((len(ws), n_layers, args.n_random))
        for wi, w in enumerate(ws):
            acts = reader.read(w)
            p = dirs.project(acts)
            s[wi] = np.abs(np.array([[p[c][L] for L in range(n_layers)]
                                     for c in concepts])).mean(0)
            for L in range(n_layers):
                h = np.asarray(acts.acts[L], dtype=float)
                mu = np.asarray(dirs.mu[L], dtype=float)
                sd = np.asarray(dirs.sd[L], dtype=float)
                z = (h - mu) / np.where(sd == 0, 1.0, sd)
                zn = np.linalg.norm(z)
                for k in range(args.n_random):
                    u = rand[k][L]
                    nn[wi, L, k] = abs(float(z @ u) / (zn * np.linalg.norm(u))) if zn else 0.0
        sig[i] = s.mean(0)
        nul[i] = nn.mean(0)
        if (i + 1) % 25 == 0:
            print(f"  {i + 1}/{len(rows)}", flush=True)

    grp = np.array([r["group"] for r in rows], dtype=float)
    wds = np.array([r["words"] for r in rows], dtype=float)
    has_specs = any(r["specs"] for r in rows)
    if has_specs:
        X = np.array([[1.0 if s in r["specs"] else 0.0 for s in POOL] for r in rows])

    def rres(a, b):
        a, b = rankdata(a), rankdata(b)
        return a - np.polyval(np.polyfit(b, a, 1), b)

    print(f"{'layer':>6}{'rho':>9}{'null 95%':>18}{'beats':>7}{'len ctrl':>10}{'induction':>11}")
    print("-" * 62)
    out = []
    for L in range(n_layers):
        r, p = stats.spearmanr(grp, sig[:, L])
        nr = [stats.spearmanr(grp, nul[:, L, k]).statistic for k in range(args.n_random)]
        lo, hi = float(np.percentile(nr, 2.5)), float(np.percentile(nr, 97.5))
        beats = not (lo <= r <= hi)
        pr, _ = stats.spearmanr(rres(sig[:, L], wds), rres(grp, wds))
        ind = float("nan")
        if has_specs:
            pred = np.zeros(len(rows))
            for tr, te in KFold(5, shuffle=True, random_state=0).split(X):
                pred[te] = RidgeCV(alphas=np.logspace(-2, 3, 20)).fit(
                    X[tr], sig[tr, L]).predict(X[te])
            resid = sig[:, L] - pred
            ind, _ = stats.spearmanr(rres(resid, wds), rres(grp, wds))
        out.append({"layer": L, "rho": float(r), "p": float(p), "null_lo": lo, "null_hi": hi,
                    "beats_null": bool(beats), "partial_length": float(pr),
                    "after_induction": float(ind)})
        print(f"{L:>6}{r:>+9.3f}  [{lo:+.3f},{hi:+.3f}]{'  yes' if beats else '   no':>7}"
              f"{pr:>+10.3f}{ind:>+11.3f}")

    if has_specs:
        surv = [o for o in out if o["beats_null"] and abs(o["after_induction"]) > 0.2
                and abs(o["rho"]) > 0.2]
    else:
        # No specifications exist (the no-maker corpus): the induction term is undefined, and
        # requiring abs(nan) > 0.2 silently forced surv empty — a control that could not fail
        # (audit L26). The computable rule: a layer correlating with arbitrary labels on
        # maker-less text, with length removed, is a false positive.
        surv = [o for o in out if o["beats_null"] and abs(o["partial_length"]) > 0.2
                and abs(o["rho"]) > 0.2]
    print(f"\n  layers beating their null: {sum(o['beats_null'] for o in out)}/{n_layers}")
    print(f"  layers surviving BOTH length and induction: {len(surv)}")
    if surv:
        b = max(surv, key=lambda o: abs(o["after_induction"]))
        print(f"  strongest survivor: layer {b['layer']}  raw {b['rho']:+.3f}  "
              f"after both controls {b['after_induction']:+.3f}")
    if has_specs:
        verdict = "SURVIVES" if surv else "DEAD"
    else:
        verdict = "FALSE-POSITIVE" if surv else "CLEAN"
    print(f"\n  >>> {verdict}")

    RESULTS.mkdir(parents=True, exist_ok=True)
    tag = f"{args.corpus}_{model_name.split('/')[-1]}" + ("_sig" if args.save_signals else "")
    (RESULTS / f"{tag}.json").write_text(json.dumps(
        {"corpus": args.corpus, "model": model_name, "n": len(rows),
         "control_rule": "full" if has_specs else "no-induction-term",
         "signals": sig.tolist(), "groups": grp.tolist(), "words": wds.tolist(),
         "layers": out, "n_survivors": len(surv), "verdict": verdict},
        indent=2), encoding="utf-8", newline="\n")
    print(f"\nwrote {(RESULTS / f'{tag}.json').relative_to(REPO)}")


if __name__ == "__main__":
    main()
