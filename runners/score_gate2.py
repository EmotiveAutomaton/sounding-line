"""Score Gate 2 against the criteria locked in prereg/gate2.py.

Written before the run finished, so the scoring cannot be shaped by the numbers. Each hypothesis
and null is evaluated exactly as the card states it, and reported as PASS, FAIL or UNDECIDABLE —
the third being a real outcome when the corpus cannot answer the question, which is different
from the question being answered negatively.
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
    src = REPO / "results" / "gate2" / "gate2_local_k3.json"
    d = json.loads(src.read_text(encoding="utf-8"))
    arts = d["artifacts"]

    def rows(n):
        return {k: v for k, v in arts.items() if v["row"] == n and v.get("bounded")}

    r2, r3, r5 = rows(2), rows(3), rows(5)
    A, B, C = arts.get("item_A", {}), arts.get("item_B", {}), arts.get("item_C", {})

    def g(group, arm, field):
        return [v[arm][field] for v in group.values() if v.get(arm)]

    print(f"GATE 2 — card {d['card'][:12]} — {d['arm']} arm, k={d['k']}")
    print(f"corpus: row2={len(r2)}  row3={len(r3)}  row5={len(r5)}  generated=3")
    print("=" * 88)

    verdicts = {}

    # ── F1: real makers vs commercial filler (INSTRUMENT falsifier) ──────────────────────────
    alt2, alt3 = mean(g(r2, "bounded", "named_alternative_rate")), mean(g(r3, "bounded", "named_alternative_rate"))
    verdicts["F1.1"] = ("PASS" if alt2 > alt3 else "FAIL",
                        f"named-alternative rate  row2 {alt2:.2f}  vs  row3 {alt3:.2f}")

    ag2, ag3 = mean(g(r2, "bounded", "purpose_agreement")), mean(g(r3, "bounded", "purpose_agreement"))
    verdicts["F1.2"] = ("PASS" if ag2 > ag3 else "FAIL",
                        f"purpose agreement       row2 {ag2:.2f}  vs  row3 {ag3:.2f}")

    m2, m3 = mean(g(r2, "bounded", "machine")), mean(g(r3, "bounded", "machine"))
    verdicts["F1.3"] = ("PASS" if m3 > m2 else "FAIL",
                        f"machine-audience        row3 {m3:.2f}  vs  row2 {m2:.2f}")

    # ── F2: rich vs thin (CLAIM falsifier) ───────────────────────────────────────────────────
    if A.get("bounded") and B.get("bounded"):
        a, b = A["bounded"], B["bounded"]
        checks = {
            "named_alternative_rate": a["named_alternative_rate"] > b["named_alternative_rate"],
            "purpose_agreement": a["purpose_agreement"] > b["purpose_agreement"],
            "max_depth": a["max_depth"] > b["max_depth"],
            "machine (lower is richer)": a["machine"] < b["machine"],
            "artifact_effort": mean(a["artifact_effort"]) > mean(b["artifact_effort"]),
        }
        won = sum(checks.values())
        verdicts["F2.1"] = ("PASS" if won >= 2 else "FAIL",
                            f"A separated from B on {won}/5 tuple dimensions: " +
                            ", ".join(k for k, v in checks.items() if v))
        ea, eb = a["artifact_effort"], b["artifact_effort"]
        verdicts["F2.2"] = ("PASS" if min(ea) > max(eb) else "FAIL",
                            f"artifact_effort A={ea} B={eb} (no-overlap required)")
    else:
        verdicts["F2.1"] = verdicts["F2.2"] = ("UNDECIDABLE", "generated pair missing")

    # ── Nulls ────────────────────────────────────────────────────────────────────────────────
    lens2, lens3 = mean(g(r2, "bounded", "n_chars")), mean(g(r3, "bounded", "n_chars"))
    verdicts["N7"] = ("REPORTED", f"mean chars  row2 {lens2:.0f}  row3 {lens3:.0f} "
                                  f"(direction of any length confound)")

    all_p = {p for v in arts.values() if v.get("bounded") for p in v["bounded"]["purposes"]}
    all_a = {x for v in arts.values() if v.get("bounded") for x in v["bounded"]["audiences"]}
    verdicts["N8"] = ("PASS" if len(all_p) >= 3 and len(all_a) >= 3 else "FAIL",
                      f"{len(all_p)} distinct purposes {sorted(all_p)}, "
                      f"{len(all_a)} distinct audiences {sorted(all_a)}")

    m5 = mean(g(r5, "bounded", "machine"))
    verdicts["N9"] = ("PASS" if m5 < 0.30 else "FAIL",
                      f"row5 (pre-2020 human) machine-audience {m5:.2f}; must stay below 0.30")

    fa2, fa3 = mean(g(r2, "freeform", "named_alternative_rate")), mean(g(r3, "freeform", "named_alternative_rate"))
    b_gap, f_gap = alt2 - alt3, fa2 - fa3
    verdicts["N10"] = ("PASS" if b_gap > f_gap else "FAIL",
                       f"row2-row3 separation on named-alternative rate: "
                       f"bounded {b_gap:+.2f}  free-form {f_gap:+.2f}")

    for k in ("F1.1", "F1.2", "F1.3", "F2.1", "F2.2", "N7", "N8", "N9", "N10"):
        v, why = verdicts[k]
        print(f"{k:<6} {v:<12} {why}")

    print("=" * 88)
    claim = verdicts["F2.1"][0]
    if claim == "FAIL":
        print("F2.1 FAILED — this is the pre-registered STOP condition for SPEC §1's reframe.")
        print("Every downstream document must state this before stating anything else.")
    elif claim == "PASS":
        print("F2.1 held. On this corpus, at this n, the reframe is not falsified.")
        print("That is not the same as established — see the card's may_not_claim.")

    (REPO / "results" / "gate2" / "scored.json").write_text(
        json.dumps({k: {"verdict": v, "detail": w} for k, (v, w) in verdicts.items()}, indent=2),
        encoding="utf-8")


if __name__ == "__main__":
    main()
