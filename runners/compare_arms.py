"""The boundedness ablation. SPEC §7's most important experiment, and A-2's unmet commitment.

    the one that matters most: a model asked, free-form, WHY WAS THIS MADE. If unbounded
    attribution matches bounded inference, the boundedness bought nothing and §2 is wrong.

Reads the persisted readings from `run_reading.py --freeform` and compares the two arms on the
quantities SPEC §5 actually names, rather than on any aggregate.

── WHAT THIS IS AND IS NOT ───────────────────────────────────────────────────────────────────

This is the **Gate 3** comparison run early, on Gate 1's three artifacts, at k=3, on the local
arm. It is a *pilot*: enough to see whether the effect exists and which direction it points, not
enough to establish it. Gate 3 proper needs the full corpus and the API arm.

Under docs/GATES.md this is therefore reported as instrument evidence, not as a claim. The
claim-gate discipline — pre-registered, not iterated on — applies when it runs for real.

── THE PREDICTION, WRITTEN BEFORE THE NUMBERS WERE LOOKED AT ─────────────────────────────────

SPEC §2 says an unbounded reader asked an open question will always produce a coherent answer,
for anything, and that free-form attribution is therefore "confident fabrication with good
grammar". If that is right, the free-form arm should show, relative to bounded:

  P1  LOWER purpose agreement across independent samples — it invents, and invention differs
      every run. This is the E2 signature and it is the sharpest prediction available.
  P2  LOWER grounding — no bounded family forcing it back to the text.
  P3  NOT NECESSARILY fewer decisions. It may well report MORE, because nothing constrains it.
      A free-form arm that finds more decisions with less agreement is the predicted result, not
      a contradiction of it.

P3 matters: if the only difference were volume, the honest reading would be that boundedness
merely suppresses output. Agreement is the discriminating quantity.
"""

from __future__ import annotations

import json
import statistics
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]


def _modal_share(labels: list[str]) -> float:
    return max(labels.count(x) for x in set(labels)) / len(labels) if labels else 0.0


def summarise(runs: list[dict]) -> dict:
    if not runs:
        return {}
    purposes = [r["reading"]["purpose"]["distribution"] for r in runs]
    best_p = [max(d, key=d.get) for d in purposes]
    best_a = [max(r["reading"]["audience"]["distribution"],
                  key=r["reading"]["audience"]["distribution"].get) for r in runs]
    n_dec = [len(r["reading"]["decisions"]) for r in runs]
    depths = [max((d["level"] for d in r["reading"]["decisions"]), default=0) for r in runs]
    conf = [r["reading"]["confidence_100"] / 100 for r in runs]
    machine = [r["reading"]["audience"]["distribution"]["machine"] for r in runs]
    named_alt = [
        sum(1 for d in r["reading"]["decisions"] if d["alternative_rejected"].strip())
        / max(1, len(r["reading"]["decisions"]))
        for r in runs
    ]
    agree = _modal_share(best_p)
    return {
        "k": len(runs),
        "purpose_agreement": agree,
        "audience_agreement": _modal_share(best_a),
        "purposes": best_p,
        "mean_decisions": statistics.fmean(n_dec),
        "max_depth": max(depths),
        "mean_confidence": statistics.fmean(conf),
        "confident_disagreement": statistics.fmean(conf) * (1 - agree),
        "mean_machine": statistics.fmean(machine),
        "named_alternative_rate": statistics.fmean(named_alt),
    }


def main() -> None:
    src = REPO / "results" / "readings" / "readings_local.json"
    data = json.loads(src.read_text(encoding="utf-8"))

    rows = []
    for item, rec in data["items"].items():
        b, f = summarise(rec["bounded"]), summarise(rec["freeform"])
        if not b or not f:
            continue
        rows.append((item, b, f))

    print(f"BOUNDEDNESS ABLATION — {data['arm']} arm, k={data['k']}")
    print("=" * 92)
    hdr = f"{'item':<9}{'arm':<10}{'agree':>7}{'aud.ag':>8}{'conf':>7}{'conf.dis':>10}{'dec':>6}{'depth':>7}{'alt%':>7}{'mach':>7}"
    print(hdr)
    print("-" * len(hdr))
    for item, b, f in rows:
        for name, d in (("bounded", b), ("free-form", f)):
            print(f"{item.replace('item_',''):<9}{name:<10}"
                  f"{d['purpose_agreement']:>7.2f}{d['audience_agreement']:>8.2f}"
                  f"{d['mean_confidence']:>7.2f}{d['confident_disagreement']:>10.2f}"
                  f"{d['mean_decisions']:>6.1f}{d['max_depth']:>7d}"
                  f"{d['named_alternative_rate']:>7.2f}{d['mean_machine']:>7.2f}")
        print()

    ba = statistics.fmean(b["purpose_agreement"] for _, b, _ in rows)
    fa = statistics.fmean(f["purpose_agreement"] for _, _, f in rows)
    bcd = statistics.fmean(b["confident_disagreement"] for _, b, _ in rows)
    fcd = statistics.fmean(f["confident_disagreement"] for _, _, f in rows)
    bd = statistics.fmean(b["mean_decisions"] for _, b, _ in rows)
    fd = statistics.fmean(f["mean_decisions"] for _, _, f in rows)

    print("=" * 92)
    print(f"P1  purpose agreement      bounded {ba:.2f}   free-form {fa:.2f}   "
          f"{'BOUNDED HIGHER' if ba > fa else 'free-form higher or equal'}")
    print(f"    confident disagreement bounded {bcd:.2f}   free-form {fcd:.2f}   "
          f"{'BOUNDED LOWER (E2 signature weaker)' if bcd < fcd else 'bounded higher or equal'}")
    print(f"P3  mean decisions         bounded {bd:.1f}    free-form {fd:.1f}")
    print()
    print("Pilot only: 3 artifacts, k=3, local arm. Direction, not magnitude, and not a claim.")

    out = REPO / "results" / "ablation_summary.json"
    out.write_text(json.dumps({
        "arm": data["arm"], "k": data["k"],
        "bounded_purpose_agreement": ba, "freeform_purpose_agreement": fa,
        "bounded_confident_disagreement": bcd, "freeform_confident_disagreement": fcd,
        "bounded_mean_decisions": bd, "freeform_mean_decisions": fd,
        "per_item": {i: {"bounded": b, "freeform": f} for i, b, f in rows},
    }, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
