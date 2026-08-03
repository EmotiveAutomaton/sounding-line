"""Read artifacts, persist the full readings, and render them for a human to check.

Distinct from `run_gate1.py`, which computes a pre-registered criterion. This one exists to
produce something inspectable: it keeps every reading in full — decisions, quotes, trajectories —
rather than the summary statistics a criterion needs, and renders each one beside its artifact.

Both arms are run when asked, and the free-form baseline alongside the bounded arm, because A-2
says the baseline runs in parallel from Gate 1 and for a long time it did not.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path

from soundingline.baselines.freeform import run_freeform
from soundingline.family.loader import FAMILY_PATH, load_family
from soundingline.hashlock import hash_file
from soundingline.locks import verify_all
from soundingline.loop.run import LoopRun, run_loop
from soundingline.probe.client import make_client
from soundingline.probe.render import Artifact
from soundingline.report.reading_html import write_reports

REPO = Path(__file__).resolve().parents[1]
ARTIFACT_DIR = REPO / "docs" / "gate1" / "artifacts"
RESULTS = REPO / "results"


def serialise(run: LoopRun) -> dict:
    """Everything needed to re-render or re-audit a reading, without the artifact text."""
    return {
        "artifact_id": run.artifact_id,
        "arm": run.arm,
        "model": run.model,
        "seed": run.seed,
        "converged": run.converged,
        "iterations": run.iterations,
        "settling_rate": round(run.settling_rate, 4),
        "reading": run.reading.model_dump(mode="json"),
        "trajectory": [
            {"iteration": s.iteration, "movement": round(s.movement, 4),
             "n_decisions": s.n_decisions, "changed_because": s.changed_because[:400]}
            for s in run.trajectory
        ],
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--k", type=int, default=3)
    ap.add_argument("--arm", default="local", choices=["local", "api"])
    ap.add_argument("--items", nargs="*", default=["item_A", "item_B", "item_C"])
    ap.add_argument("--freeform", action="store_true",
                    help="also run the unbounded baseline (A-2)")
    ap.add_argument("--out", default="readings")
    args = ap.parse_args()

    verify_all()
    fam = load_family()
    print(f"locks ok | family v{fam.version} | arm={args.arm} k={args.k} "
          f"freeform={args.freeform}\n", flush=True)

    out_root = RESULTS / args.out
    bounded: dict[str, tuple[list[LoopRun], str]] = {}
    free: dict[str, tuple[list[LoopRun], str]] = {}
    record: dict[str, dict] = {}

    for stem in args.items:
        text = (ARTIFACT_DIR / f"{stem}.md").read_text(encoding="utf-8")
        artifact = Artifact(text=text, source_id=stem, sha256=hash_file(ARTIFACT_DIR / f"{stem}.md"))
        b_runs, f_runs, fails = [], [], []

        for s in range(args.k):
            client = make_client(args.arm, seed=s) if args.arm == "local" else make_client(args.arm)
            try:
                r = run_loop(client, artifact, seed=s)
                b_runs.append(r)
                print(f"  {stem} bounded {s}: {r.reading.purpose.best}/"
                      f"{r.reading.audience.best} dec={len(r.reading.decisions)} "
                      f"depth={r.reading.max_depth}", flush=True)
            except Exception as e:                                   # noqa: BLE001
                fails.append(f"bounded {s}: {type(e).__name__}: {e}")
                print(f"  {stem} bounded {s}: FAILED {type(e).__name__}", flush=True)

            if args.freeform:
                try:
                    r = run_freeform(client, artifact, seed=s)
                    f_runs.append(r)
                    print(f"  {stem} free    {s}: {r.reading.purpose.best}/"
                          f"{r.reading.audience.best} dec={len(r.reading.decisions)} "
                          f"depth={r.reading.max_depth}", flush=True)
                except Exception as e:                               # noqa: BLE001
                    fails.append(f"freeform {s}: {type(e).__name__}: {e}")
                    print(f"  {stem} free    {s}: FAILED {type(e).__name__}", flush=True)

        if b_runs:
            bounded[stem] = (b_runs, text)
        if f_runs:
            free[stem] = (f_runs, text)
        record[stem] = {
            "bounded": [serialise(r) for r in b_runs],
            "freeform": [serialise(r) for r in f_runs],
            "failures": fails,
        }
        print(flush=True)

    out_root.mkdir(parents=True, exist_ok=True)
    (out_root / f"readings_{args.arm}.json").write_text(
        json.dumps({"family_sha256": hash_file(FAMILY_PATH), "arm": args.arm,
                    "k": args.k, "items": record}, indent=2), encoding="utf-8")

    written = write_reports(bounded, out_root / f"{args.arm}_bounded")
    if free:
        written += write_reports(free, out_root / f"{args.arm}_freeform")
    for p in written:
        print("wrote", p.relative_to(REPO), flush=True)


if __name__ == "__main__":
    main()
