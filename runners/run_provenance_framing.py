"""G115 — the paper's H1, run in the reader model: does being TOLD a text is machine-made change
the affective read of the very same text?

H1 predicts a human's engagement machinery drops on the AI label. Our reader is not a human — but
if a provenance frame alone moves its affective activations on identical text, then (a) the reader
carries a provenance prior that framing can trigger, and (b) every unframed measurement this
project has made sits on the neutral side of a knob nobody had turned. Either way the size of the
framing effect is a number the theory wants.

── THE TEST ──────────────────────────────────────────────────────────────────────────────────

Thirty held-out-ladder artifacts, each read twice per window with a one-line frame prepended:
"The following passage was written by a person." versus "The following passage was written by an
AI." (token-length matched). Per artifact: the early/late affective ratio (the flagship loci,
7%/76% of depth) and the mean affect magnitude, paired across frames.

    FRAMING-MOVES   paired Wilcoxon p < 0.01 on either quantity — the frame alone shifts the read
    NO-EFFECT       it does not; the reader's affect machinery ignores claimed provenance
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

RESULTS = REPO / "results" / "provenance_framing"
FRAME_H = "The following passage was written by a person.\n\n"
FRAME_M = "The following passage was written by an AI.\n\n"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus", default="ladder2")
    ap.add_argument("--n", type=int, default=30)
    ap.add_argument("--model", default=None)
    ap.add_argument("--device", default="cuda")
    args = ap.parse_args()

    import numpy as np                                                # noqa: PLC0415
    from scipy import stats                                           # noqa: PLC0415

    from runners.run_b import split                                   # noqa: PLC0415
    from runners.run_layer_ratio import windows                       # noqa: PLC0415
    from soundingline.probe.activations import (DEFAULT_MODEL, Reader,  # noqa: PLC0415
                                                fit_directions)

    model_name = args.model or DEFAULT_MODEL
    print(f"loading {model_name} ...", flush=True)
    reader = Reader(model_name, device=args.device)
    fit, _ = split()
    dirs = fit_directions(reader, fit)
    n = dirs.n_layers
    lo_hi = max(2, round(n * 0.07))
    hi_lo = round(n * 0.76)

    def read_framed(frame: str, w: str):
        p = dirs.project(reader.read(frame + w))
        early = statistics.fmean(abs(v[L]) for v in p.values() for L in range(lo_hi))
        late = statistics.fmean(abs(v[L]) for v in p.values() for L in range(hi_lo, n))
        mag = statistics.fmean(abs(v[L]) for v in p.values() for L in range(n))
        return (early / late if late > 1e-9 else float("nan")), mag

    d = REPO / "corpora" / args.corpus
    man = json.loads((d / "manifest.json").read_text(encoding="utf-8"))
    items = [it for it in man["items"] if isinstance(it.get("rung"), int)][: args.n]

    rows = []
    for it in items:
        text = (d / f"{it['id']}.txt").read_text(encoding="utf-8")
        rh, rm, mh, mm = [], [], [], []
        for w in windows(text):
            r1, m1 = read_framed(FRAME_H, w)
            r2, m2 = read_framed(FRAME_M, w)
            if r1 == r1 and r2 == r2:
                rh.append(r1); rm.append(r2)
            mh.append(m1); mm.append(m2)
        if not rh:
            continue
        rows.append({"id": it["id"], "rung": it["rung"],
                     "ratio_human": statistics.fmean(rh), "ratio_machine": statistics.fmean(rm),
                     "mag_human": statistics.fmean(mh), "mag_machine": statistics.fmean(mm)})
        print(f"  {it['id']}: ratio {rows[-1]['ratio_human']:.3f} vs "
              f"{rows[-1]['ratio_machine']:.3f}", flush=True)

    dr = [r["ratio_machine"] - r["ratio_human"] for r in rows]
    dm = [r["mag_machine"] - r["mag_human"] for r in rows]
    _, p_r = stats.wilcoxon(dr) if any(dr) else (None, 1.0)
    _, p_m = stats.wilcoxon(dm) if any(dm) else (None, 1.0)
    print(f"\n  n={len(rows)}  ratio delta (AI - person): {statistics.fmean(dr):+.4f}  p={p_r:.4f}")
    print(f"           magnitude delta:               {statistics.fmean(dm):+.5f}  p={p_m:.4f}")
    verdict = "FRAMING-MOVES" if min(p_r, p_m) < 0.01 else "NO-EFFECT"
    print(f"\n  >>> {verdict}")

    RESULTS.mkdir(parents=True, exist_ok=True)
    (RESULTS / f"{args.corpus}.json").write_text(json.dumps(
        {"corpus": args.corpus, "model": model_name, "n": len(rows),
         "ratio_delta_mean": statistics.fmean(dr), "p_ratio": float(p_r),
         "mag_delta_mean": statistics.fmean(dm), "p_mag": float(p_m),
         "verdict": verdict, "rows": rows}, indent=2), encoding="utf-8", newline="\n")
    print(f"wrote {(RESULTS / f'{args.corpus}.json').relative_to(REPO)}")


if __name__ == "__main__":
    main()
