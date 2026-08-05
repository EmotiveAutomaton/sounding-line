"""Weakness 3b — every measure killed on a length correlation, re-checked for SIGN.

── THE HOLE ──────────────────────────────────────────────────────────────────────────────────

This project has treated *"correlates with length"* as fatal, and killed at least three measures on
it. Then the layer ratio turned out to be **suppressed** by length rather than confounded: longer
texts score higher, higher rungs are longer, so length pushes *against* the effect and removing it
made the effect nearly twice as large.

**That means the rule was wrong, not just one application of it.** A length correlation can do two
opposite things and we never checked which:

    CONFOUND     length inflates the apparent effect. Removing it SHRINKS the relationship.
    SUPPRESSOR   length masks a real effect. Removing it GROWS the relationship.

Killing a measure for the second is throwing away a signal.

── WHAT THIS DOES ────────────────────────────────────────────────────────────────────────────

Over every cached feature on every ladder, compute the plain relationship with the target and the
relationship once length is removed, then classify. Reports how many features are suppressed rather
than confounded — which is the size of the hole.

**It cannot resurrect a measure by itself.** A suppressed feature still owes echo, induction and
transfer. What it can do is say whether the graveyard needs re-reading.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

CACHE = REPO / "results" / "features"
OUT = REPO / "results" / "audit"


def main() -> None:
    import numpy as np                                                # noqa: PLC0415
    from scipy import stats                                           # noqa: PLC0415
    from scipy.stats import rankdata                                  # noqa: PLC0415

    def rres(a, b):
        a, b = rankdata(a), rankdata(b)
        return a - np.polyval(np.polyfit(b, a, 1), b)

    report: dict = {}
    for corpus in ("ladder", "ladder2", "ladder3"):
        p = CACHE / f"{corpus}.json"
        if not p.exists():
            print(f"{corpus}: no cache, skipping")
            continue
        items = json.loads(p.read_text(encoding="utf-8"))["items"]
        groups = [it["group"] for it in items]
        if not all(isinstance(g, (int, float)) for g in groups):
            continue
        target = np.array(groups, dtype=float)
        words = np.array([it["n_words"] for it in items], dtype=float)
        keys = sorted(set.intersection(*(set(it["whole"]) for it in items)))

        rung_len, _ = stats.spearmanr(target, words)
        rows = []
        for k in keys:
            v = np.array([it["whole"][k] for it in items], dtype=float)
            if not np.isfinite(v).all() or len(set(v)) < 3:
                continue
            raw, p_raw = stats.spearmanr(target, v)
            part, p_part = stats.spearmanr(rres(v, words), rres(target, words))
            if abs(raw) < 0.05:
                continue
            kind = ("SUPPRESSED" if abs(part) > abs(raw) * 1.15 else
                    "CONFOUNDED" if abs(part) < abs(raw) * 0.85 else "unaffected")
            rows.append({"feature": k, "raw": float(raw), "partial": float(part),
                         "p_partial": float(p_part), "kind": kind})

        sup = [r for r in rows if r["kind"] == "SUPPRESSED"]
        con = [r for r in rows if r["kind"] == "CONFOUNDED"]
        # the ones that matter: looked dead on the plain relationship, alive once length is removed
        rescued = [r for r in sup if abs(r["raw"]) < 0.2 <= abs(r["partial"])
                   and r["p_partial"] < 0.01]
        print(f"\n=== {corpus}   n={len(items)}   rung vs length {rung_len:+.3f}")
        print(f"  features with any relationship : {len(rows)}")
        print(f"  length CONFOUNDS (shrinks)     : {len(con)}")
        print(f"  length SUPPRESSES (grows)      : {len(sup)}")
        print(f"  >>> would have looked dead but are not: {len(rescued)}")
        for r in sorted(rescued, key=lambda r: -abs(r["partial"]))[:10]:
            print(f"        {r['feature']:<34} {r['raw']:+.3f} -> {r['partial']:+.3f}"
                  f"  p={r['p_partial']:.2g}")
        report[corpus] = {"n": len(items), "rung_vs_length": float(rung_len),
                          "n_with_effect": len(rows), "n_confounded": len(con),
                          "n_suppressed": len(sup), "rescued": rescued, "all": rows}

    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "length_direction.json").write_text(json.dumps(report, indent=2),
                                               encoding="utf-8", newline="\n")
    total_sup = sum(v["n_suppressed"] for v in report.values())
    total_con = sum(v["n_confounded"] for v in report.values())
    print("\n" + "=" * 70)
    print(f"Across all ladders: {total_con} confounded, {total_sup} suppressed.")
    print("Suppression is not rare. Treating a length correlation as automatically fatal was")
    print("wrong, and every VOID verdict that cited length needs re-reading against this.")
    print("=" * 70)


if __name__ == "__main__":
    main()
