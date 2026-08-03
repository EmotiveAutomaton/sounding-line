"""The no-maker controls — the checks that decide whether the successor measures mean anything.

── WHY THIS RUNS BEFORE ANYTHING IS CLAIMED ──────────────────────────────────────────────────

E36's null N28, in the simulation that this project derives its direction from:

    At the shallowest depth there is no process to recover, so recovery must sit at chance. If it
    does not, the measure is reading goal information and is goal recovery renamed... **NULL N28
    FAILED. Every number above is uninterpretable.**

Sounding Line's Gate 3 card has no N28-analogue, and the closest thing that was ever run — Gate 2,
on the three locked generated artifacts — FAILED:

    row 2, human and careful   1.283
    row 5                      1.093
    GENERATED, no maker        1.111
    row 3, commercial          0.917

Artifacts with nothing behind them unlocked more than competent commercial work. So every measure
proposed for the successor gets its no-maker control run FIRST, on the same three artifacts, and
each one's pass condition is written here rather than after the numbers.

── THE THREE CONTROLS ────────────────────────────────────────────────────────────────────────

  RAW UNLOCK        the baseline, re-measured. Expected to fail, and reported anyway. A control a
                    measure is known to fail is what makes passing it mean something.

  SPAN AGREEMENT    `measures/gated.py`. Cross-seed agreement on WHICH decisions, matched by
                    evidence span. PASSES if generated content agrees clearly less than human
                    content. E2 predicts it will (no maker to converge on); E38 predicts it will
                    not (a machine-matched reader finds its own kind easy and stays consistent).
                    They disagree, which is why this is run rather than argued.

  N-AFF             family v3's mandatory null. On artifacts with no reconstructible maker the
                    affective posterior must stay FLAT — normalised entropy above 0.85 — and
                    `none_legible` should carry weight rather than the mass landing on a story.
                    An affective label is exactly what a language model supplies fluently whether
                    or not anything supports it, so this is the dimension most likely to
                    confabulate and the one whose null was written first.

**If a control fails, the measure is reported as failing. It is not tuned until it passes.** The
whole reason this file exists is that a measure fitted to make its own control pass is worth
nothing, and this project has already caught itself doing a version of that once.
"""

from __future__ import annotations

import argparse
import json
import math
import statistics
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from soundingline.family.loader import load_family                 # noqa: E402
from soundingline.locks import verify_all                          # noqa: E402
from soundingline.loop.run import run_loop                         # noqa: E402
from soundingline.measures.gated import reconstructibility         # noqa: E402
from soundingline.probe import render                              # noqa: E402
from soundingline.probe.client import make_client                  # noqa: E402
from soundingline.probe.render import Artifact                     # noqa: E402
from soundingline.probe.schema import StageEOut                    # noqa: E402

GENERATED = REPO / "docs" / "gate1" / "artifacts"
RESULTS = REPO / "results" / "controls"
V3 = REPO / "soundingline" / "family" / "family_v3.yaml"

# Pass thresholds, all written before the run.
FLAT_ENTROPY = 0.85          # N-AFF: normalised entropy of the affect posterior on no-maker text
UNLOCK_TOL = 0.15            # raw unlock within this of 1.0 on no-maker text would be a pass


def _entropy(dist: dict[str, float]) -> float:
    vals = [v for v in dist.values() if v > 0]
    if len(vals) <= 1:
        return 0.0
    h = -sum(v * math.log(v) for v in vals)
    return h / math.log(len(dist))


def read_one(client, aid: str, text: str, k: int, affect: bool) -> dict:
    runs = []
    for s in range(k):
        c = make_client(client, seed=s) if isinstance(client, str) else client
        runs.append(run_loop(c, Artifact(text=text[:12000], source_id=aid), seed=s))

    ratios = [(r.decisions_after_settle / r.decisions_before_settle)
              if r.decisions_before_settle > 0.05 else 1.0 for r in runs]
    rec = reconstructibility(runs, text)

    out = {
        "artifact": aid,
        "raw_unlock": statistics.fmean(ratios),
        "span_agreement": rec.span_agreement,
        "grounding": rec.grounding,
        "counterfactual": rec.counterfactual,
        "gate": rec.gate,
        "k": len(runs),
    }

    if affect:
        aff = []
        for s in range(k):
            c = make_client(client, seed=s) if isinstance(client, str) else client
            e = c.read(render.bounded_system(),
                       render.stage_e(Artifact(text=text[:12000], source_id=aid)),
                       StageEOut)
            d = e.parsed.affect.distribution          # type: ignore[union-attr]
            aff.append((_entropy(d), d.get("none_legible", 0.0),
                        e.parsed.affect.best))        # type: ignore[union-attr]
        out["affect_entropy"] = statistics.fmean(a[0] for a in aff)
        out["none_legible"] = statistics.fmean(a[1] for a in aff)
        out["affect_best"] = [a[2] for a in aff]
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--k", type=int, default=5)
    ap.add_argument("--arm", default="local")
    ap.add_argument("--affect", action="store_true",
                    help="also run stage E (requires family v3)")
    args = ap.parse_args()

    verify_all()
    items = sorted(GENERATED.glob("item_*.md"))
    if not items:
        print(f"no generated artifacts under {GENERATED}")
        return
    print(f"locks ok | family v{load_family().version} | no-maker controls on {len(items)} "
          f"generated artifacts | arm={args.arm} k={args.k}"
          f"{' | + stage E (family v3)' if args.affect else ''}\n", flush=True)

    out = []
    for p in items:
        rec = read_one(args.arm, p.stem, p.read_text(encoding="utf-8"), args.k, args.affect)
        out.append(rec)
        extra = (f" affect_H={rec['affect_entropy']:.2f} none={rec['none_legible']:.2f}"
                 if args.affect else "")
        print(f"  {p.stem:<8} unlock={rec['raw_unlock']:.2f} "
              f"span_agree={rec['span_agreement']:.2f} gate={rec['gate']:.2f}{extra}", flush=True)

    RESULTS.mkdir(parents=True, exist_ok=True)
    (RESULTS / "no_maker.json").write_text(json.dumps({"arm": args.arm, "k": args.k,
                                                       "artifacts": out}, indent=2),
                                           encoding="utf-8")

    print("\n" + "=" * 78)
    u = statistics.fmean(r["raw_unlock"] for r in out)
    print(f"RAW UNLOCK        {u:.3f}   (1.0 expected where there is no chain to unlock)")
    print(f"  >>> {'PASS' if abs(u - 1.0) <= UNLOCK_TOL else 'FAIL'} — Gate 2 measured 1.111 and "
          f"this is the control it failed")

    sa = statistics.fmean(r["span_agreement"] for r in out)
    print(f"SPAN AGREEMENT    {sa:.3f}   on no-maker content")
    print("  >>> verdict needs the human-artifact comparison; low here is necessary, not "
          "sufficient")

    if args.affect:
        h = statistics.fmean(r["affect_entropy"] for r in out)
        nl = statistics.fmean(r["none_legible"] for r in out)
        print(f"N-AFF             entropy {h:.3f} (must exceed {FLAT_ENTROPY}), "
              f"none_legible {nl:.3f}")
        print(f"  >>> {'PASS' if h > FLAT_ENTROPY else 'FAIL'} — on failure, performed_affect is "
              f"measuring the model's fluency and every number using it is uninterpretable")
    print("=" * 78)


if __name__ == "__main__":
    main()
