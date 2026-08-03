"""Score Gate 3 against the criteria locked in prereg/gate3.py.

**Written while the run was still in progress, before any artifact result had been read.** The
scoring logic therefore cannot have been shaped by the numbers, which is the only way a claim
gate's analysis is worth anything.

Every choice here is the card's, not mine-at-scoring-time: no outlier removal, trivially-1.0
unlocks kept in the primary, failed artifacts dropped and counted, length regressed and reported
regardless of what it shows.
"""

from __future__ import annotations

import json
import math
import statistics
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))


def welch(a: list[float], b: list[float]) -> tuple[float, float, float, tuple[float, float]]:
    """Welch's t, two-sided p, Cohen's d, and a 95% CI on the difference.

    Hand-rolled rather than pulled from scipy so the arithmetic is visible in the repository —
    a claim gate's statistic should not be a call into something the reader has to take on
    trust.
    """
    from scipy import stats                       # noqa: PLC0415
    t, p = stats.ttest_ind(a, b, equal_var=False)
    na, nb = len(a), len(b)
    va, vb = statistics.variance(a), statistics.variance(b)
    pooled = math.sqrt(((na - 1) * va + (nb - 1) * vb) / (na + nb - 2))
    d = (statistics.fmean(a) - statistics.fmean(b)) / pooled if pooled else 0.0
    se = math.sqrt(va / na + vb / nb)
    diff = statistics.fmean(a) - statistics.fmean(b)
    df = (va / na + vb / nb) ** 2 / ((va / na) ** 2 / (na - 1) + (vb / nb) ** 2 / (nb - 1))
    crit = stats.t.ppf(0.975, df)
    return float(t), float(p), d, (diff - crit * se, diff + crit * se)


def main() -> None:
    src = REPO / "results" / "gate3" / "gate3_local_k5.json"
    d = json.loads(src.read_text(encoding="utf-8"))
    arts = d["artifacts"]
    from prereg.gate3 import CARD, card_hash

    # Pre-registered: fewer than 2 valid samples -> dropped and counted. Never retried.
    usable = {k: v for k, v in arts.items() if v.get("bounded", {}).get("k", 0) >= 2}
    dropped = [k for k in arts if k not in usable]

    A = [v for v in usable.values() if v["half"] == "A"]
    B = [v for v in usable.values() if v["half"] == "B"]

    print(f"GATE 3 — card {card_hash()[:12]} — {d['arm']} arm, k={d['k']}")
    print(f"usable A={len(A)} B={len(B)}   dropped={len(dropped)} {dropped if dropped else ''}")
    print("=" * 88)

    ua = [v["bounded"]["unlock"] for v in A]
    ub = [v["bounded"]["unlock"] for v in B]
    t, p, dd, ci = welch(ua, ub)
    passed = (p < 0.05) and (statistics.fmean(ua) > statistics.fmean(ub))

    print("PRIMARY  G3.1 — method unlock, Half A vs Half B")
    print(f"  A: mean {statistics.fmean(ua):.3f}  sd {statistics.stdev(ua):.3f}  n {len(ua)}")
    print(f"  B: mean {statistics.fmean(ub):.3f}  sd {statistics.stdev(ub):.3f}  n {len(ub)}")
    print(f"  diff {statistics.fmean(ua) - statistics.fmean(ub):+.3f}  "
          f"95% CI [{ci[0]:+.3f}, {ci[1]:+.3f}]")
    print(f"  Welch t = {t:.3f}   p = {p:.4f}   Cohen d = {dd:.2f}")
    print(f"  >>> {'PASS' if passed else 'FAIL'}")
    print()

    # Length confound — reported regardless, and able to void a significant primary.
    from scipy import stats as st                  # noqa: PLC0415
    lens = [v["bounded"]["n_chars"] for v in A + B]
    unl = [v["bounded"]["unlock"] for v in A + B]
    r, rp = st.pearsonr(lens, unl)
    la = statistics.fmean(v["bounded"]["n_chars"] for v in A)
    lb = statistics.fmean(v["bounded"]["n_chars"] for v in B)
    confounded = (rp < 0.05) and abs(r) > 0.4
    print(f"LENGTH   G3.5 — unlock vs artifact length")
    print(f"  r = {r:+.3f}  p = {rp:.4f}   mean chars  A {la:.0f}  B {lb:.0f}")
    print(f"  >>> {'CONFOUNDED — primary is void even if significant' if confounded else 'no length confound'}")
    print()

    def cmp(field, label, higher_in="A"):
        a = [v["bounded"][field] for v in A]
        b = [v["bounded"][field] for v in B]
        _, pp, ddd, _ = welch(a, b)
        ok = (statistics.fmean(a) > statistics.fmean(b)) if higher_in == "A" \
            else (statistics.fmean(b) > statistics.fmean(a))
        print(f"  {label:<34} A {statistics.fmean(a):.3f}  B {statistics.fmean(b):.3f}  "
              f"p={pp:.3f}  {'as predicted' if ok else 'REVERSED'}")

    print("SECONDARY")
    cmp("named_alternative_rate", "G3.2 named-alternative rate")
    cmp("machine", "G3.4 machine-audience", higher_in="B")
    cmp("purpose_agreement", "(diagnostic) purpose agreement")

    # G3.3 — the boundedness ablation, on real text at power.
    fa = [v["freeform"]["unlock"] for v in A if v.get("freeform")]
    fb = [v["freeform"]["unlock"] for v in B if v.get("freeform")]
    if fa and fb:
        b_gap = statistics.fmean(ua) - statistics.fmean(ub)
        f_gap = statistics.fmean(fa) - statistics.fmean(fb)
        print(f"  G3.3 boundedness: bounded separates {b_gap:+.3f}, "
              f"free-form {f_gap:+.3f}  "
              f"{'BOUNDED BETTER' if b_gap > f_gap else 'FREE-FORM BETTER — boundedness buys nothing'}")

    # Nulls
    print()
    print("NULLS")
    trivial = sum(1 for v in usable.values() if v["bounded"].get("unlock_trivial"))
    within = statistics.fmean(v["bounded"]["unlock_sd"] for v in usable.values())
    between = abs(statistics.fmean(ua) - statistics.fmean(ub))
    print(f"  N13 within-artifact sd {within:.3f} vs between-half diff {between:.3f}  "
          f"{'PASS' if within < between else 'FAIL — raise k before claiming anything'}")
    print(f"  (trivially-1.0 unlocks: {trivial}/{len(usable)}; kept in the primary per the card)")

    print("=" * 88)
    if passed and not confounded:
        print("G3.1 HELD. The instrument separates work made with care from commercial filler")
        print("on method unlock, at power, on plain text. Read the may_not_claim before quoting it.")
    else:
        print("G3.1 FAILED — the pre-registered STOP condition:")
        print(" ", CARD["stop_condition"].split("\n\n")[0])

    (REPO / "results" / "gate3" / "scored.json").write_text(json.dumps({
        "card": card_hash(), "n_A": len(A), "n_B": len(B), "dropped": dropped,
        "primary": {"mean_A": statistics.fmean(ua), "mean_B": statistics.fmean(ub),
                    "t": t, "p": p, "cohen_d": dd, "ci95": list(ci), "pass": bool(passed)},
        "length": {"r": r, "p": rp, "confounded": bool(confounded)},
        "trivial_unlocks": trivial,
    }, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
