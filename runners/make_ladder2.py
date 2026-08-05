"""Ladder 2 — a held-out replication corpus, generated at fresh seeds.

── WHY THIS EXISTS ───────────────────────────────────────────────────────────────────────────

Two of the eight known weaknesses in `FINDINGS.md` are about the same result, and one corpus fixes
both at once.

    weakness 2   the layer ratio on the ladder is rho = -0.275, p = 0.0529, n = 50.
                 Above 0.05 UNCORRECTED. It is the only order-dependent effect in the project and
                 it is one artifact's worth of noise from nothing.

    weakness 3   `ratio_for()` splits the model at 0.07 and 0.76 of depth. Those loci were chosen
                 by LOOKING AT A PRIOR RESULT ON THE SAME MODEL and were never held out. That is a
                 forking path, and it is the kind of thing that manufactures a p = 0.053.

The curator's rule, stated 2026-08-05 and adopted as standing policy:

    For issues that are near significance, like 0.0529, we can just increase the power and rerun.
    That's worth doing as a rule we follow in general, because we're working with such low sample
    sizes.

**More power alone would entrench weakness 3** — it would give a tighter estimate of a quantity
chosen on this data. So the replication is built as a **held-out set**: new artifacts, fresh seeds,
and the loci frozen at the values the old data produced. Nothing about the measure may be re-tuned.

── PRE-REGISTERED, BEFORE ANY GENERATION ─────────────────────────────────────────────────────

    n            100 new artifacts, 20 per rung, seed base 90000 (ladder 1 used 70000)
    measure      layer ratio with loci FROZEN at round(n*0.07) and round(n*0.76). Not refitted.
    test         ONE test, on ladder 2 alone, after all 100 exist. No peeking, no optional stopping.

    REPLICATES   rho < -0.2 with p < 0.01 on ladder 2 alone
    FAILS        rho >= -0.1, or p > 0.05
    AMBIGUOUS    between — and at n = 100 that would mean the effect is too small to chase

**The pooled n = 150 estimate is reported but is NOT the test.** Pooling fitting and held-out data
would reintroduce exactly the problem this corpus exists to remove.

Also re-checked on the new corpus because they are free: length (rho vs word count must stay under
0.4), and the ladder's own void condition (rung vs output length, which killed ladder 1 at +0.403).
"""

from __future__ import annotations

import argparse
import json
import random
import statistics
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from runners.make_intent_ladder import RUNGS, SPECS, SYSTEM, TOPICS, build   # noqa: E402
from soundingline.probe.client import make_client                            # noqa: E402

OUT = REPO / "corpora" / "ladder2"
SEED_BASE = 90000            # ladder 1 used 70000; no seed is shared


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--arm", default="local")
    ap.add_argument("--per-rung", type=int, default=20)
    args = ap.parse_args()

    OUT.mkdir(parents=True, exist_ok=True)
    items = []
    done = {p.stem for p in OUT.glob("*.txt")}
    for rung in RUNGS:
        for i in range(args.per_rung):
            name = f"r{rung}_{i:02d}"
            if name in done:                       # resumable
                items.append(json.loads((OUT / f"{name}.json").read_text(encoding="utf-8")))
                continue
            seed = SEED_BASE + rung * 1000 + i
            rng = random.Random(seed)
            # rotate the topic offset so ladder 2 is not topic-aligned with ladder 1
            topic = TOPICS[(i + 5) % len(TOPICS)]
            prompt = build(topic, rung, rng)
            c = make_client(args.arm, seed=seed)
            try:
                text = c.read_text(SYSTEM, prompt)
            except Exception as e:                                    # noqa: BLE001
                print(f"  rung {rung} #{i}: {type(e).__name__}", flush=True)
                continue
            (OUT / f"{name}.txt").write_text(text, encoding="utf-8", newline="\n")
            rec = {"id": name, "rung": rung, "topic": topic, "n_specs": rung,
                   "seed": seed, "prompt_words": len(prompt.split()),
                   "n_words": len(text.split())}
            (OUT / f"{name}.json").write_text(json.dumps(rec), encoding="utf-8", newline="\n")
            items.append(rec)
            (OUT / "manifest.json").write_text(json.dumps(
                {"why": "held-out replication of the ladder; see runners/make_ladder2.py",
                 "seed_base": SEED_BASE, "rungs": list(RUNGS), "items": items},
                indent=2), encoding="utf-8", newline="\n")
        got = [m for m in items if m["rung"] == rung]
        if got:
            print(f"  rung {rung:>2}: n={len(got)}  "
                  f"output median {statistics.median(m['n_words'] for m in got):.0f}w", flush=True)

    print("\nVOID CHECK — rung vs output length (ladder 1 died here at +0.403)")
    from scipy import stats                                            # noqa: PLC0415
    rho, p = stats.spearmanr([m["rung"] for m in items], [m["n_words"] for m in items])
    print(f"  rho={rho:+.3f} p={p:.4f}   "
          f"{'>>> VOID — length ladder again' if abs(rho) > 0.4 else 'ok'}")


if __name__ == "__main__":
    main()
