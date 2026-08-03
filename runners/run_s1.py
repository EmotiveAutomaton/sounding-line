"""S-1 — does the surface move within an artifact while the depth stays put?

── THE DESIGN, AND WHY IT IS NOT A FULL LOOP PER SLICE ───────────────────────────────────────

The question is whether decision density BY TARGET varies with position, holding the purpose
fixed. Running the whole loop on each third would let the purpose drift between slices, and a
purpose that changed between thirds would produce a position effect that is really a purpose
effect. So:

  1. run the full loop ONCE on the whole artifact, to settle purpose and audience;
  2. run stage B alone on each third, UNDER that settled purpose, with v6's target field;
  3. compare surface and depth density across the thirds.

That also makes it cheap — three extra stage-B calls per artifact rather than three extra loops.

── WHAT IT CANNOT SHOW ───────────────────────────────────────────────────────────────────────

Nothing about a single artifact. One artifact gives one surface_sd and one depth_sd, and their
ordering on one artifact is noise. **S-1 is a corpus-level test**: across artifacts, is
`surface_sd > depth_sd` more often than chance? Reported as a paired comparison, per artifact,
with the count of ties, and never as a mean of ratios.

The slicing is not free of confounds and they are stated rather than controlled: the last third
of an artifact contains its conclusion, and conclusions differ from bodies for reasons that have
nothing to do with a tiring maker. **A significant S-1 with a monotone trend is much weaker
evidence than a significant S-1 with a non-monotone one**, because the monotone version is what a
structural section effect also predicts.
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from soundingline.family.loader import load_family                # noqa: E402
from soundingline.locks import verify_all                         # noqa: E402
from soundingline.loop.run import run_loop                        # noqa: E402
from soundingline.measures.position import position_profile, thirds   # noqa: E402
from soundingline.probe import render                             # noqa: E402
from soundingline.probe.client import make_client                 # noqa: E402
from soundingline.probe.render import Artifact                    # noqa: E402
from soundingline.probe.schema import StageBOutV6                 # noqa: E402

from runners.run_gate3 import load_corpus                         # noqa: E402

RESULTS = REPO / "results" / "s1"


def profile_one(client, aid: str, text: str) -> dict | None:
    slices = thirds(text)
    if not slices:
        return None

    whole = run_loop(client, Artifact(text=text[:12000], source_id=aid))
    purpose, audience = whole.reading.purpose.best, whole.reading.audience.best

    per_slice = []
    for i, s in enumerate(slices):
        art = Artifact(text=s[:12000], source_id=f"{aid}#s{i}")
        r = client.read(
            render.bounded_system(),
            render.stage_b(art, purpose, audience, spec_path=render.BOUNDED_V6_PATH),
            StageBOutV6,
        )
        per_slice.append((s, list(r.parsed.decisions)))     # type: ignore[union-attr]

    p = position_profile(per_slice)
    return {
        "artifact": aid, "purpose": purpose, "audience": audience,
        "surface_sd": p.surface_sd, "depth_sd": p.depth_sd,
        "surface_trend": p.surface_trend, "depth_trend": p.depth_trend,
        "surface_moves_more": p.surface_moves_more,
        "slices": [{"i": s.index, "chars": s.n_chars, "surface": s.surface,
                    "depth": s.depth, "n": s.n_decisions} for s in p.slices],
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--arm", default="local")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()

    verify_all()
    corpus = load_corpus()
    if args.limit:
        corpus = corpus[: args.limit]
    print(f"locks ok | family v{load_family().version} | S-1 on {len(corpus)} artifacts "
          f"| arm={args.arm}\n", flush=True)

    client = make_client(args.arm, seed=args.seed)
    out, skipped = [], []
    for i, (aid, half, text) in enumerate(corpus, 1):
        try:
            rec = profile_one(client, aid, text)
        except Exception as e:                                  # noqa: BLE001
            skipped.append(f"{aid}: {type(e).__name__}")
            continue
        if rec is None:
            skipped.append(f"{aid}: too short to third")
            continue
        rec["half"] = half
        out.append(rec)
        print(f"  [{i:>2}/{len(corpus)}] {aid:<14} {half}  "
              f"surface_sd={rec['surface_sd']:.2f} depth_sd={rec['depth_sd']:.2f} "
              f"{'S>D' if rec['surface_moves_more'] else 'D>=S'}", flush=True)
        RESULTS.mkdir(parents=True, exist_ok=True)
        (RESULTS / "s1.json").write_text(
            json.dumps({"arm": args.arm, "skipped": skipped, "artifacts": out}, indent=2),
            encoding="utf-8")

    if not out:
        print("nothing measurable")
        return

    wins = sum(1 for r in out if r["surface_moves_more"])
    ties = sum(1 for r in out if abs(r["surface_sd"] - r["depth_sd"]) < 1e-9)
    from scipy import stats                                     # noqa: PLC0415
    binom = stats.binomtest(wins, len(out), 0.5, alternative="greater").pvalue
    down = sum(1 for r in out if r["surface_trend"] < 0)

    print()
    print(f"S-1  surface_sd > depth_sd in {wins}/{len(out)}  (ties {ties})  "
          f"binomial p = {binom:.4f}")
    print(f"     mean surface_sd {statistics.fmean(r['surface_sd'] for r in out):.3f}  "
          f"mean depth_sd {statistics.fmean(r['depth_sd'] for r in out):.3f}")
    print(f"     surface DECLINES across the artifact in {down}/{len(out)} — the decay form")
    print(f"     monotone-decline share is the weak-evidence case: a conclusion differs from a "
          f"body for reasons unrelated to a tiring maker")
    if skipped:
        print(f"     skipped {len(skipped)}: {skipped[:5]}")


if __name__ == "__main__":
    main()
