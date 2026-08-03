"""Score the method-unlock measure. **Exploratory, and labelled as such.**

── THE PROVENANCE OF THIS HYPOTHESIS, STATED BEFORE ANY NUMBER ───────────────────────────────

The measure was built AFTER Gate 2 failed, which makes the decision to look here post-hoc, and
post-hoc measures are how projects talk themselves into results. Two things separate this from
that, and one of them does not:

**Does not:** the choice to examine method rather than purpose was made in response to a failure.
That is exactly the shape of motivated analysis and it cannot be argued away.

**Does:** the DIRECTION was fixed by prior work that predates this project. E36 predicted, before
Sounding Line existed, that intent density moves method uptake (0.179, interval excluding zero)
and provably cannot move purpose (-0.028). Sounding Line then measured purpose and found nothing.
Predicting the sign in advance is the part that matters, and E36 did it in a different codebase on
different data.

**Does:** it is a real prediction that could fail. If row 2 does not unlock more than row 3, the
diagnosis is wrong and the last candidate standing is that the construct does not survive contact
with real artifacts.

**Status: EXPLORATORY.** Whatever this returns, it is a hypothesis for Gate 3 to test on data it
has not seen, under claim-gate discipline. It cannot rehabilitate Gate 2, whose failure stands.
"""

from __future__ import annotations

import json
import statistics
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))


def mean(xs):
    xs = [x for x in xs if x is not None]
    return statistics.fmean(xs) if xs else float("nan")


def main() -> None:
    d = json.loads((REPO / "results" / "gate2" / "gate2_local_k3.json").read_text(encoding="utf-8"))
    arts = d["artifacts"]

    def group(n):
        return {k: v for k, v in arts.items() if v["row"] == n and v.get("bounded")}

    r2, r3, r5 = group(2), group(3), group(5)
    gen = {k: v for k, v in arts.items() if v["row"] in (6, 7) and v.get("bounded")}

    print("METHOD UNLOCK — E36's temporal quantity, measured on real artifacts")
    print("=" * 90)
    print(f"{'artifact':<28}{'row':>4}{'before':>8}{'after':>7}{'unlock':>8}{'settled':>9}{'alt%':>7}")
    print("-" * 90)
    for k, v in sorted(arts.items(), key=lambda x: (x[1]["row"], x[0])):
        b = v.get("bounded")
        if not b:
            continue
        print(f"{k:<28}{v['row']:>4}{b.get('method_before', 0):>8.1f}"
              f"{b.get('method_after', 0):>7.1f}{b.get('method_unlock', 0):>8.2f}"
              f"{b.get('settled', 0):>9.2f}{b.get('named_alternative_rate', 0):>7.2f}")

    def u(g):
        return mean(v["bounded"].get("method_unlock", 0) for v in g.values())

    u2, u3, u5, ug = u(r2), u(r3), u(r5), u(gen)
    print("=" * 90)
    print(f"row 2  real makers        unlock {u2:.2f}   (n={len(r2)})")
    print(f"row 3  commercial filler  unlock {u3:.2f}   (n={len(r3)})")
    print(f"row 5  pre-2020 human     unlock {u5:.2f}   (n={len(r5)})")
    print(f"gen    A/B/C              unlock {ug:.2f}   (n={len(gen)})")
    print()

    # The comparison E36's sign predicts. Reported with the previous run's purpose result beside
    # it, because the contrast between the two is the actual finding.
    print(f"E36 PREDICTION  row2 unlock > row3 unlock : "
          f"{'HOLDS' if u2 > u3 else 'FAILS'}  ({u2:.2f} vs {u3:.2f}, gap {u2 - u3:+.2f})")
    a2 = mean(v["bounded"]["named_alternative_rate"] for v in r2.values())
    a3 = mean(v["bounded"]["named_alternative_rate"] for v in r3.values())
    print(f"  for contrast, the PURPOSE-side measure that failed at Gate 2:")
    print(f"  named-alternative rate  row2 {a2:.2f} vs row3 {a3:.2f}  (gap {a2 - a3:+.2f})")
    print()
    print("EXPLORATORY. Gate 2's failure stands. This is a hypothesis for Gate 3 to test on data")
    print("it has not seen, and it cannot be quoted as a result.")

    (REPO / "results" / "gate2" / "unlock_scored.json").write_text(json.dumps({
        "status": "exploratory",
        "row2_unlock": u2, "row3_unlock": u3, "row5_unlock": u5, "generated_unlock": ug,
        "e36_prediction_holds": bool(u2 > u3),
        "purpose_side_gap": a2 - a3,
        "per_artifact": {k: {"row": v["row"],
                             "unlock": v["bounded"].get("method_unlock"),
                             "before": v["bounded"].get("method_before"),
                             "after": v["bounded"].get("method_after")}
                         for k, v in arts.items() if v.get("bounded")},
    }, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
