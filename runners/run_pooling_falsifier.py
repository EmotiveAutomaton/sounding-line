"""G127 — the pooling falsifier: does the early/late story survive a different extraction?

Extraction choice systematically biases layer-wise conclusions (Hadidi 2025, via the analogue
research). Every profile this project owns mean-pools. This re-reads the flagship quantities on
the held-out ladder under mean, last-token, and max pooling.

v2 (2026-08-12, after the L93 methods pass). v1 truncated the rung-ordered manifest to its first
forty items, so every ratio-versus-rung cell was computed on rungs 0 and 1 only and its verdict
was withdrawn (L44 correction). v2: all items by default, the rung composition recorded in the
output, and a REPRODUCE-GATE per the falsifier-baseline lesson — the mean-pooling arm must land
within tolerance of the known length-controlled value (held-out ladder: -0.405, L1) before the
last-token and max arms are interpreted. If the gate fails, the verdict is BASELINE-MISMATCH and
no pooling claim is made in either direction.

    ROBUST      the per-block |projection| profile correlates > 0.8 across poolings AND the
                ratio-vs-rung correlation keeps its sign and significance class under all three
    POOLING-BOUND  either fails — every address claim inherits the caveat, in bold
    BASELINE-MISMATCH  the mean arm failed to reproduce the known value; hunt, do not interpret
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

RESULTS = REPO / "results" / "pooling_falsifier"


KNOWN_MEAN_POOLING = -0.405     # held-out ladder, length-controlled (L1); the reproduce-gate target
GATE_TOL = 0.15


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default=None)
    ap.add_argument("--device", default="cuda")
    ap.add_argument("--n", type=int, default=0, help="0 = every rung-labelled item (v2 default)")
    ap.add_argument("--tag", default="_v2", help="output filename suffix; keeps v1's record intact")
    args = ap.parse_args()

    import numpy as np                                                # noqa: PLC0415
    from scipy import stats                                           # noqa: PLC0415
    from scipy.stats import rankdata                                  # noqa: PLC0415

    from runners.run_b import split                                   # noqa: PLC0415
    from runners.run_layer_ratio import windows                       # noqa: PLC0415
    from soundingline.gpulock import acquire_gpu_lock, release_gpu_lock  # noqa: PLC0415
    from soundingline.probe.activations import (DEFAULT_MODEL, Reader,  # noqa: PLC0415
                                                fit_directions)

    acquire_gpu_lock("pooling_falsifier")
    model_name = args.model or DEFAULT_MODEL
    print(f"loading {model_name} ...", flush=True)
    reader = Reader(model_name, device=args.device)
    fit, _ = split()
    dirs = fit_directions(reader, fit)
    n = dirs.n_layers
    lo_hi = max(2, round(n * 0.07))
    hi_lo = round(n * 0.76)

    d = REPO / "corpora" / "ladder2"
    man = json.loads((d / "manifest.json").read_text(encoding="utf-8"))
    items = [it for it in man["items"] if isinstance(it.get("rung"), int)]
    if args.n:
        items = items[: args.n]
    from collections import Counter                                   # noqa: PLC0415
    rung_comp = dict(sorted(Counter(it["rung"] for it in items).items()))
    print(f"items {len(items)}, rung composition {rung_comp}", flush=True)

    def rres(a, b):
        a, b = rankdata(a), rankdata(b)
        return a - np.polyval(np.polyfit(b, a, 1), b)

    out = {"model": model_name, "poolings": {}}
    profiles = {}
    for pooling in ("mean", "last", "max"):
        prof = np.zeros(n)
        ratios, rungs, wds = [], [], []
        for it in items:
            text = (d / f"{it['id']}.txt").read_text(encoding="utf-8")
            per = np.zeros(n)
            rs = []
            nw = 0
            for w in windows(text):
                p = dirs.project(reader.read(w, pooling=pooling))
                for L in range(n):
                    per[L] += statistics.fmean(abs(v[L]) for v in p.values())
                early = statistics.fmean(abs(v[L]) for v in p.values() for L in range(lo_hi))
                late = statistics.fmean(abs(v[L]) for v in p.values() for L in range(hi_lo, n))
                if late > 1e-9:
                    rs.append(early / late)
                nw += 1
            if nw and rs:
                prof += per / nw
                ratios.append(statistics.fmean(rs))
                rungs.append(it["rung"])
                wds.append(len(text.split()))
        prof /= len(ratios)
        rho, p = stats.spearmanr(rres(np.array(ratios), np.array(wds, float)),
                                 rres(np.array(rungs, float), np.array(wds, float)))
        profiles[pooling] = prof
        out["poolings"][pooling] = {"profile": prof.tolist(),
                                    "ratio_vs_rung": float(rho), "p": float(p)}
        print(f"{pooling:<5}: ratio-vs-rung {rho:+.3f} (p={p:.4f})  profile peak block "
              f"{int(np.argmax(prof))}")

    cors = {}
    for a, b in (("mean", "last"), ("mean", "max"), ("last", "max")):
        c = float(stats.spearmanr(profiles[a], profiles[b]).statistic)
        cors[f"{a}-{b}"] = c
        print(f"profile corr {a} vs {b}: {c:+.3f}")
    out["profile_correlations"] = cors
    out["n_items"] = len(items)
    out["rung_composition"] = {str(k): v for k, v in rung_comp.items()}

    # the reproduce-gate: no pooling claim about the ratio unless the mean arm lands on the
    # known length-controlled value first (the falsifier-baseline lesson, L93)
    mean_rho = out["poolings"]["mean"]["ratio_vs_rung"]
    gate_ok = abs(mean_rho - KNOWN_MEAN_POOLING) <= GATE_TOL
    out["reproduce_gate"] = {"known": KNOWN_MEAN_POOLING, "observed": mean_rho,
                             "tolerance": GATE_TOL, "pass": bool(gate_ok)}
    if not gate_ok:
        out["verdict"] = "BASELINE-MISMATCH"
    else:
        signs = {k: (v["ratio_vs_rung"] < 0, v["p"] < 0.05) for k, v in out["poolings"].items()}
        same_class = len({s for s in signs.values()}) == 1
        robust = min(cors.values()) > 0.8 and same_class
        out["verdict"] = "ROBUST" if robust else "POOLING-BOUND"
    print(f"\n  reproduce-gate: mean arm {mean_rho:+.3f} vs known {KNOWN_MEAN_POOLING:+.3f} "
          f"-> {'PASS' if gate_ok else 'FAIL'}")
    print(f"  >>> {out['verdict']}")

    RESULTS.mkdir(parents=True, exist_ok=True)
    tag = model_name.split("/")[-1] + args.tag
    (RESULTS / f"{tag}.json").write_text(json.dumps(out, indent=2),
                                         encoding="utf-8", newline="\n")
    print(f"wrote {(RESULTS / f'{tag}.json').relative_to(REPO)}")
    release_gpu_lock()


if __name__ == "__main__":
    main()
