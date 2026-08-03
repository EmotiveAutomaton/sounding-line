"""Gate 1. Reads the calibration artifacts and writes the results.

The pre-registered criterion this exists to settle is C-18, fixed in CALIBRATION_03 §6 **before
this script was written**:

    A > C > B   the probe recovered direction an expert human reader could not.
    B > C > A   the probe shares the human's surface heuristic; bounded inference has not
                escaped the arms race and the architecture needs rebuilding.
    anything else — the probe is measuring a third thing and neither account holds.

The curator ranked B > C > A. The protocol order is A > C > B. Those disagree, which is what
makes this worth running: whichever way the instrument falls, it falls against something.

Everything is verified locked before a single model call is made.
"""

from __future__ import annotations

import argparse
import json
import time
from dataclasses import asdict
from pathlib import Path

from soundingline.family.loader import FAMILY_PATH, load_family
from soundingline.hashlock import hash_file
from soundingline.locks import verify_all
from soundingline.loop.run import run_loop
from soundingline.measures.reading import measure
from soundingline.probe.client import LocalClient, make_client
from soundingline.probe.render import Artifact

REPO = Path(__file__).resolve().parents[1]
ARTIFACT_DIR = REPO / "docs" / "gate1" / "artifacts"
RESULTS = REPO / "results" / "gate1"

# The three generated artifacts. Named A/B/C rather than thin/draft/final so that nothing in the
# run path knows the protocol ordering — the same blinding the curator got.
ITEMS = ["item_A", "item_B", "item_C"]


def load_artifact(stem: str) -> tuple[Artifact, str]:
    path = ARTIFACT_DIR / f"{stem}.md"
    text = path.read_text(encoding="utf-8")
    return Artifact(text=text, source_id=stem, trust_level="untrusted",
                    sha256=hash_file(path)), text


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--k", type=int, default=3,
                    help="independent reconstructions per artifact; convergence needs >= 2")
    ap.add_argument("--arm", default="local", choices=["local", "api"])
    args = ap.parse_args()

    # SPEC discipline: nothing runs until every locked artifact still matches.
    verify_all()
    fam = load_family()
    print(f"locks verified | family v{fam.version} "
          f"({hash_file(FAMILY_PATH)[:12]}) | arm={args.arm} k={args.k}\n")

    RESULTS.mkdir(parents=True, exist_ok=True)
    summary: dict[str, dict] = {}
    t_start = time.time()

    for stem in ITEMS:
        artifact, text = load_artifact(stem)
        runs, failures = [], []
        for s in range(args.k):
            client = make_client(args.arm, seed=s) if args.arm == "local" else make_client(args.arm)
            try:
                run = run_loop(client, artifact, seed=s)
                runs.append(run)
                print(f"  {stem} sample {s}: purpose={run.reading.purpose.best:<10} "
                      f"audience={run.reading.audience.best:<20} "
                      f"decisions={len(run.reading.decisions)} "
                      f"depth={run.reading.max_depth} "
                      f"converged={run.converged} iters={run.iterations}")
            except Exception as e:                       # noqa: BLE001
                # Recorded, never silently dropped. A failure rate is a property of the
                # instrument and hiding it would bias the sample toward readable artifacts.
                failures.append(f"{type(e).__name__}: {e}")
                print(f"  {stem} sample {s}: FAILED {type(e).__name__}: {str(e)[:90]}")

        if len(runs) < 2:
            print(f"  {stem}: fewer than 2 valid samples; convergence undefined\n")
            summary[stem] = {"valid": len(runs), "failures": failures}
            continue

        m = measure(runs, text)
        summary[stem] = {
            "valid": len(runs),
            "failures": failures,
            "fit": asdict(m.fit),
            "convergence": asdict(m.convergence),
            "depth": {k: v for k, v in asdict(m.depth).items() if k != "profile"},
            "audience": asdict(m.audience),
            "artifact_effort": [r.reading.artifact_effort for r in runs],
            "demonstrated_work": [r.reading.demonstrated_work for r in runs],
            "settling_rate": [round(r.settling_rate, 4) for r in runs],
            "converged": [r.converged for r in runs],
        }
        fit_str = f"{m.fit.combined:.3f}" + ("" if m.fit.verifiable else " [UNTRACED]")
        print(f"  {stem}: fit={fit_str} (conc={m.fit.concentration:.2f} "
              f"ground={m.fit.grounding:.2f} supp={m.fit.support:.2f}) "
              f"agree={m.convergence.purpose_agreement:.2f} "
              f"depth={m.depth.max_level} machine={m.audience.machine:.2f}\n")

    # ── The pre-registered criterion ─────────────────────────────────────────────────────────
    # Only verifiable readings may be ranked. An unverifiable one is not a low score, it is an
    # absence of one, and sorting it as zero would silently rank "we could not check this"
    # below "the family explained nothing" — which is exactly backwards.
    ranked = sorted(
        (s for s in summary if "fit" in summary[s]),
        key=lambda s: summary[s]["fit"]["combined"],
        reverse=True,
    )
    # Flagged rather than excluded: a reading whose claims did not trace still has a fit, and it
    # is low for a reason the reader of these results needs told apart from an empty artifact.
    unverifiable = [s for s in summary
                    if "fit" in summary[s] and not summary[s]["fit"]["verifiable"]]
    order = " > ".join(r.replace("item_", "") for r in ranked)
    verdicts = {
        "A > C > B": "PROTOCOL ORDER — the probe recovered direction the curator could not",
        "B > C > A": "CURATOR ORDER — the probe shares the surface heuristic; architecture at fault",
    }
    verdict = verdicts.get(order, "NEITHER — the probe is measuring a third thing")

    out = {
        "gate": 1,
        "family_version": fam.version,
        "family_sha256": hash_file(FAMILY_PATH),
        "arm": args.arm,
        "k": args.k,
        "elapsed_s": round(time.time() - t_start, 1),
        "ranking_by_fit": order,
        "unverifiable": unverifiable,
        "verdict_C18": verdict,
        "protocol_order": "A > C > B",
        "curator_order": "B > C > A",
        "per_artifact": summary,
    }
    (RESULTS / f"gate1_{args.arm}_k{args.k}.json").write_text(
        json.dumps(out, indent=2), encoding="utf-8")

    print("=" * 78)
    print(f"RANKING BY FIT : {order}")
    if unverifiable:
        print(f"UNTRACED       : {', '.join(unverifiable)} "
              f"(claims made, not found in artifact — low fit for fabrication, not emptiness)")
    print(f"protocol       : A > C > B")
    print(f"curator        : B > C > A")
    print(f"VERDICT (C-18) : {verdict}")
    print("=" * 78)


if __name__ == "__main__":
    main()
