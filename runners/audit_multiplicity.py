"""Multiple-comparison audit — every p-value this project has ever quoted, corrected at last.

── WHY ───────────────────────────────────────────────────────────────────────────────────────

`FINDINGS.md`, known weakness 1: **this project has never corrected for multiple comparisons.**
Roughly twenty-five tests have been run and reported at p < 0.05 as though each were the only one.
At that rate at least one false positive is expected from chance alone, and we have no idea which
of our numbers it is.

This does the correction retrospectively. It is deliberately unflattering and it should be.

── HOW THE LIST WAS BUILT ────────────────────────────────────────────────────────────────────

**Hand-collected from the verdict files, with the source named for every row**, rather than scraped.
Scraping JSON for anything called "p" would silently mix primary tests with diagnostics and controls,
and the whole point is to be able to argue about what belongs in the family.

**Family definition matters more than the arithmetic here**, so it is explicit and contestable:

    PRIMARY     a test whose result was used to support or reject a claim about the instrument.
                These form the correction family.
    CONTROL     a test run to invalidate one of our own measures. EXCLUDED from the family --
                these are checks we WANT to fire, and correcting them makes it harder to kill a
                measure, which is backwards.
    DIAGNOSTIC  descriptive, never used to support a claim. Excluded.

Both Benjamini-Hochberg and Benjamini-Yekutieli are reported. **BY is the honest one here** -- our
tests reuse the same corpora and the same measures, so they are dependent in unknown directions, and
BH is only valid under independence or positive dependence.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

RESULTS = REPO / "results" / "audit"

# (name, p, family, source)  -- family: primary | control | diagnostic
TESTS = [
    # ── PRIMARY: used to support or reject a claim ────────────────────────────────────────────
    ("G3.1 method unlock, A vs B",        0.68,      "primary", "results/gate3/VERDICT.md"),
    ("W-1 wall as displacement",          0.53,      "primary", "results/wall/VERDICT.md"),
    ("rich vs thin, scale_gain",          0.0032,    "primary", "results/controls/VERDICT.md"),
    ("human vs no-maker, scale_gain",     0.0005,    "primary", "results/controls/VERDICT.md"),
    ("ladder: causal_rate vs rung",       1e-6,      "primary", "results/ladder/ladder.json"),
    ("ladder: you_rate vs rung",          1e-7,      "primary", "results/ladder/ladder.json"),
    ("ladder: insight_rate vs rung",      0.0009,    "primary", "results/ladder/ladder.json"),
    ("ladder: i_rate vs rung",            0.0034,    "primary", "results/ladder/ladder.json"),
    ("ladder: tentative_rate vs rung",    0.0133,    "primary", "results/ladder/ladder.json"),
    ("ladder: exclusive_rate vs rung",    0.0917,    "primary", "results/ladder/ladder.json"),
    ("ladder: TTR vs rung",               1e-5,      "primary", "results/ladder/ladder.json"),
    ("ladder: scale_gain vs rung",        1e-5,      "primary", "results/ladder/ladder.json"),
    ("layer ratio vs rung (THE ONE)",     0.0529,    "primary", "results/layer_ratio/layer_ratio.json"),
    ("layer ratio human vs machine",      1.96e-15,  "primary", "results/shuffle_sweep/VERDICT.md"),
    ("causal_rate transfer: vs rich",     0.0011,    "primary", "results/rung_minus1/VERDICT.md"),
    ("causal_rate transfer: vs thin",     0.025,     "primary", "results/rung_minus1/VERDICT.md"),
    ("causal_rate transfer: vs averaged", 0.069,     "primary", "results/rung_minus1/VERDICT.md"),
    ("diversity: career vs breadth",      0.65,      "primary", "results/diversity/VERDICT.md"),
    ("diversity: sign test",              0.62,      "primary", "results/diversity/VERDICT.md"),

    # ── CONTROL: run to invalidate our own measures. Excluded from the family. ─────────────────
    ("C2 layer ratio vs word count",      0.0102,    "control", "results/layer_ratio/VERDICT_CONTROL.md"),
    ("C3 register: half A vs half B",     0.0033,    "control", "results/layer_ratio/VERDICT_CONTROL.md"),
    ("ladder void: rung vs length",       0.0037,    "control", "results/ladder/VERDICT.md"),
    ("sweep: sentence-shuffled gap",      1.97e-14,  "control", "results/shuffle_sweep/VERDICT.md"),
    ("sweep: word-shuffled gap",          5.83e-16,  "control", "results/shuffle_sweep/VERDICT.md"),
]


def bh(ps: list[float]) -> list[float]:
    """Benjamini-Hochberg adjusted p-values (step-up, monotone-enforced)."""
    n = len(ps)
    order = sorted(range(n), key=lambda i: ps[i])
    adj = [0.0] * n
    prev = 1.0
    for rank, i in enumerate(reversed(order), start=1):
        k = n - rank + 1
        prev = min(prev, ps[i] * n / k)
        adj[i] = prev
    return adj


def by(ps: list[float]) -> list[float]:
    """Benjamini-Yekutieli: BH scaled by the harmonic number. Valid under arbitrary dependence."""
    n = len(ps)
    c = sum(1.0 / k for k in range(1, n + 1))
    return [min(1.0, p * c) for p in bh(ps)]


def main() -> None:
    fam = [t for t in TESTS if t[2] == "primary"]
    ps = [t[1] for t in fam]
    a_bh, a_by = bh(ps), by(ps)

    print(f"{len(TESTS)} tests collected; {len(fam)} in the correction family "
          f"(controls excluded, see module docstring)\n")
    print(f"{'test':<36}{'raw p':>11}{'BH':>11}{'BY':>11}  verdict")
    print("-" * 82)
    rows = []
    for (name, p, _, src), b, y in sorted(zip(fam, a_bh, a_by), key=lambda z: z[0][1]):
        keep_raw = p < 0.05
        keep_bh = b < 0.05
        keep_by = y < 0.05
        mark = ("survives" if keep_by else
                "SURVIVES BH ONLY" if keep_bh else
                ">>> LOST" if keep_raw else "was never significant")
        print(f"{name:<36}{p:>11.2e}{b:>11.3f}{y:>11.3f}  {mark}")
        rows.append({"test": name, "p_raw": p, "p_bh": b, "p_by": y,
                     "sig_raw": keep_raw, "sig_bh": keep_bh, "sig_by": keep_by, "source": src})

    n_raw = sum(r["sig_raw"] for r in rows)
    n_bh = sum(r["sig_bh"] for r in rows)
    n_by = sum(r["sig_by"] for r in rows)
    lost = [r["test"] for r in rows if r["sig_raw"] and not r["sig_by"]]

    print("\n" + "=" * 82)
    print(f"significant at p<0.05 uncorrected : {n_raw} of {len(fam)}")
    print(f"                    after BH      : {n_bh}")
    print(f"                    after BY      : {n_by}   <- the honest one")
    print(f"expected false positives, uncorrected: {0.05 * len(fam):.1f}")
    if lost:
        print("\nLOST TO CORRECTION:")
        for t in lost:
            print(f"  - {t}")
    print("=" * 82)

    RESULTS.mkdir(parents=True, exist_ok=True)
    (RESULTS / "multiplicity.json").write_text(json.dumps(
        {"n_family": len(fam), "n_sig_raw": n_raw, "n_sig_bh": n_bh, "n_sig_by": n_by,
         "lost_to_correction": lost, "tests": rows}, indent=2), encoding="utf-8", newline="\n")
    print(f"\nwrote {(RESULTS / 'multiplicity.json').relative_to(REPO)}")


if __name__ == "__main__":
    main()
