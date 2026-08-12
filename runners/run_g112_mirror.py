"""G112 — characterise the gpt2 mirror from the saved per-layer maps. CPU only.

L28: the fair-control ratio's sign is a family constant (Qwen negative, gpt2 and SmolLM2
positive, pythia positive fading to zero), and the 7%/76% loci were chosen in the home family.
The question this answers: does the per-layer dose-correlation profile, banded at those loci,
carry the family sign — i.e. do the fixed depth fractions straddle opposite-signed machinery
in the mirror families?

Method: for each family's saved held-out-ladder map (results/layer_correlation/ladder2_*.json),
average the per-layer rho (signal against rung) inside the early band (layers at or below 7% of
depth, minimum two) and the late band (at or above 76%). The ratio statistic is early over
late, so its dose sign should follow sign(early-band tracking minus late-band tracking) if the
banded decomposition explains the mirror. Each family's predicted sign is compared with the
L28 map.

    MIRROR-EXPLAINED    predicted sign matches the measured fair-control sign in >= 8 of the
                        mapped families
    MIRROR-PARTIAL      5 to 7 match
    MIRROR-UNEXPLAINED  fewer — the band decomposition does not carry the family sign and the
                        characterisation needs the subspace route (G124) instead

Output: results/audit/g112_mirror.json
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

SRC = REPO / "results" / "layer_correlation"
OUT = REPO / "results" / "audit"

# the L28/L28-completion fair-control sign map on the held-out ladder (0 = null cell)
RATIO_SIGN = {
    "Qwen2.5-0.5B": -1, "Qwen2.5-1.5B": -1, "Qwen2.5-3B": -1,
    "gpt2-medium": +1, "gpt2-large": +1, "gpt2-xl": 0,
    "SmolLM2-360M": +1, "SmolLM2-1.7B": +1,
    "pythia-410m": +1, "pythia-1.4b": +1, "pythia-2.8b": 0,
}


def main() -> None:
    import numpy as np                                                # noqa: PLC0415

    rows = {}
    matches = misses = 0
    for fam, want in RATIO_SIGN.items():
        f = SRC / f"ladder2_{fam}.json"
        if fam == "Qwen2.5-1.5B" and not f.exists():
            f = SRC / "ladder2.json"          # the home model's map predates model-tagged names
        if not f.exists():
            rows[fam] = {"status": "no saved map"}
            continue
        d = json.loads(f.read_text(encoding="utf-8"))
        rhos = np.array([o["rho"] for o in d["layers"]])
        n = len(rhos)
        lo_hi = max(2, round(n * 0.07))
        hi_lo = round(n * 0.76)
        early = float(rhos[:lo_hi].mean())
        late = float(rhos[hi_lo:].mean())
        pred = int(np.sign(early - late)) if abs(early - late) > 0.02 else 0
        ok = pred == want
        matches += ok
        misses += (not ok)
        rows[fam] = {"n_layers": n, "early_band_rho": round(early, 3),
                     "late_band_rho": round(late, 3),
                     "predicted_sign": pred, "measured_sign": want, "match": bool(ok)}
        print(f"{fam:16s} early {early:+.3f} late {late:+.3f} -> pred {pred:+d} "
              f"vs measured {want:+d} {'OK' if ok else 'MISS'}")

    mapped = matches + misses
    verdict = ("MIRROR-EXPLAINED" if matches >= 8
               else "MIRROR-PARTIAL" if matches >= 5 else "MIRROR-UNEXPLAINED")
    out = {"families": rows, "matches": matches, "mapped": mapped, "verdict": verdict}
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "g112_mirror.json").write_text(json.dumps(out, indent=1),
                                          encoding="utf-8", newline="\n")
    print(f"\n{matches}/{mapped} family signs predicted by the band decomposition")
    print(f">>> {verdict}")
    print(f"wrote {(OUT / 'g112_mirror.json').relative_to(REPO)}")


if __name__ == "__main__":
    main()
