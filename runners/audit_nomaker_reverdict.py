"""Audit L26 — re-adjudicate the eleven no-maker control runs whose verdict could not fail.

`run_layer_correlation.py` forced DEAD on the no-maker corpus before consulting any data: with no
specifications, the induction term is NaN and `abs(nan) > 0.2` is False, so the survivor list was
empty **under any data whatsoever**. The recorded "11 no-maker runs, all dead, zero false positives"
— the flagship's strongest control claim — was manufactured by that gate.

This re-reads the eleven saved JSONs and applies the computable rule (beats its random-direction
null AND |rho| > 0.2 AND |partial after length| > 0.2 — the full rule minus the inapplicable
induction term). CPU-only, no re-measurement: the per-layer numbers were always honest, only the
verdict gate was broken.

Chance context, stated up front: `beats_null` prices each layer against the 2.5th-97.5th percentile
band of only 12 random directions, so ~1-in-6 layers beat their null by luck alone; the joint rule
adds two |rho| > 0.2 cuts. The summary reports the observed joint rate against the base rates so a
"false positive" here is read against what luck supplies, not against zero.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

SRC = REPO / "results" / "layer_correlation"
OUT = REPO / "results" / "audit"


def main() -> None:
    files = sorted(SRC.glob("nomaker_*.json"))
    if not files:
        print("no nomaker files found")
        return
    rows = []
    total_layers = 0
    total_beats = 0
    print(f"{'model':<18}{'layers':>7}{'beats null':>11}{'joint rule':>11}   surviving layers")
    print("-" * 72)
    for f in files:
        d = json.loads(f.read_text(encoding="utf-8"))
        layers = d["layers"] if "layers" in d else d.get("per_layer", [])
        surv = [o for o in layers if o.get("beats_null")
                and abs(o.get("rho") or 0) > 0.2
                and abs(o.get("partial_length") or 0) > 0.2]
        beats = sum(1 for o in layers if o.get("beats_null"))
        total_layers += len(layers)
        total_beats += beats
        tag = f.stem.replace("nomaker_", "")
        rows.append({"model": tag, "n_layers": len(layers), "beats_null": beats,
                     "joint_pass_layers": [o["layer"] for o in surv],
                     "verdict": "FALSE-POSITIVE" if surv else "CLEAN"})
        print(f"{tag:<18}{len(layers):>7}{beats:>11}{len(surv):>11}   "
              f"{[o['layer'] for o in surv] or '—'}")

    n_fp = sum(1 for r in rows if r["verdict"] == "FALSE-POSITIVE")
    joint = sum(len(r["joint_pass_layers"]) for r in rows)
    print(f"\n  models with joint-rule layers: {n_fp}/{len(rows)}")
    print(f"  layers beating their null:     {total_beats}/{total_layers} "
          f"({total_beats / total_layers:.1%}; a 12-direction band passes ~15% by luck)")
    print(f"  layers passing the joint rule: {joint}/{total_layers} ({joint / total_layers:.1%})")
    print("\n  Reading: the honest claim is NOT 'zero false positives'. It is the rate above,")
    print("  against the luck rate — and any model whose ladder-surviving layers also pass here")
    print("  has a control problem at exactly those layers.")

    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "nomaker_reverdict.json").write_text(json.dumps(
        {"rule": "beats_null AND |rho|>0.2 AND |partial_length|>0.2 (no induction term)",
         "models": rows,
         "beats_null_rate": total_beats / total_layers,
         "joint_rate": joint / total_layers}, indent=2), encoding="utf-8", newline="\n")
    print(f"\nwrote {(OUT / 'nomaker_reverdict.json').relative_to(REPO)}")


if __name__ == "__main__":
    main()
