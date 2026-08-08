"""G31 — is the middle of the model high-activity and low-coherence? First isolated test.

The "noisy middle" claim rode along with the bimodal depth profile and died with it — but it was
**never isolated from that death**. The depth sweeps already recorded per-layer affective signal
(activity) and cross-window coherence for 11 families x up to 4 corpora, so this is a CPU readout
over saved results, no GPU.

── THE TEST ──────────────────────────────────────────────────────────────────────────────────

Split each model's layers into thirds. Rank signal and coherence across layers (ranks, so families
with different scales pool). The claim predicts, for the middle third:

    NOISY MIDDLE   mean signal rank ABOVE the outer thirds AND mean coherence rank BELOW them
    QUIET MIDDLE   signal rank below the outers — a dead middle instead
    NO PATTERN     anything else

Per family x corpus, then the count. The no-maker corpus runs alongside: if the signature is
identical there, it is architecture, not anything about makers — reported, not assumed.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

SWEEPS = REPO / "results" / "depth_sweep"
RESULTS = REPO / "results" / "noisy_middle"


def thirds(n: int) -> list[list[int]]:
    a, b = round(n / 3), round(2 * n / 3)
    return [list(range(0, a)), list(range(a, b)), list(range(b, n))]


def main() -> None:
    import numpy as np                                                # noqa: PLC0415
    from scipy.stats import rankdata                                  # noqa: PLC0415

    rows = []
    for f in sorted(SWEEPS.glob("*.json")):
        d = json.loads(f.read_text(encoding="utf-8"))
        sig, coh = d.get("signal"), d.get("coherence")
        if not sig or not coh or len(sig) != len(coh):
            print(f"  skip {f.name}: missing per-layer lists")
            continue
        n = len(sig)
        rs, rc = rankdata(sig), rankdata(coh)
        lo, mid, hi = thirds(n)
        outer = lo + hi
        m_sig = float(np.mean(rs[mid]) - np.mean(rs[outer]))   # >0: middle more active
        m_coh = float(np.mean(rc[mid]) - np.mean(rc[outer]))   # <0: middle less coherent
        if m_sig > 0 and m_coh < 0:
            verdict = "NOISY MIDDLE"
        elif m_sig < 0:
            verdict = "QUIET MIDDLE"
        else:
            verdict = "NO PATTERN"
        rows.append({"file": f.stem, "corpus": d["corpus"], "model": d["model"].split("/")[-1],
                     "n_layers": n, "mid_signal_rank_delta": m_sig,
                     "mid_coherence_rank_delta": m_coh, "verdict": verdict})

    print(f"{'corpus':<10}{'model':<16}{'mid activity':>13}{'mid coherence':>14}   verdict")
    print("-" * 68)
    for r in sorted(rows, key=lambda r: (r["corpus"], r["model"])):
        print(f"{r['corpus']:<10}{r['model']:<16}{r['mid_signal_rank_delta']:>+13.2f}"
              f"{r['mid_coherence_rank_delta']:>+14.2f}   {r['verdict']}")

    counts: dict[str, dict[str, int]] = {}
    for r in rows:
        kind = "nomaker" if r["corpus"] == "nomaker" else "ladder"
        counts.setdefault(kind, {}).setdefault(r["verdict"], 0)
        counts[kind][r["verdict"]] += 1
    print()
    for kind, c in sorted(counts.items()):
        total = sum(c.values())
        print(f"  {kind:<8} " + "  ".join(f"{k}: {v}/{total}" for k, v in sorted(c.items())))

    RESULTS.mkdir(parents=True, exist_ok=True)
    (RESULTS / "summary.json").write_text(
        json.dumps({"rows": rows, "counts": counts}, indent=2),
        encoding="utf-8", newline="\n")
    print(f"\nwrote {(RESULTS / 'summary.json').relative_to(REPO)}")


if __name__ == "__main__":
    main()
