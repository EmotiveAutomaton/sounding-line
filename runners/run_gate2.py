"""Gate 2. Runs the falsifiers pre-registered in prereg/gate2.py.

Reads the corpus from the content-addressed store written by `fetch/fetcher.py`, plus the three
generated artifacts. Never touches the network: the analysis side has no fetcher and cannot get
one (`tests/test_fetch_isolation.py`).

Both arms run on every artifact, because N10 asks whether boundedness separates the corpus rows
better than free-form attribution does — which cannot be answered by running only one.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import statistics
import sys
from pathlib import Path

from soundingline.baselines.freeform import run_freeform
from soundingline.family.loader import FAMILY_PATH, load_family
from soundingline.hashlock import hash_file
from soundingline.locks import verify_all
from soundingline.loop.run import LoopRun, run_loop
from soundingline.probe.client import make_client
from soundingline.probe.render import Artifact

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))          # prereg/ is a sibling of the package, not inside it
STORE = REPO / "corpora" / "store"
MANIFEST = REPO / "corpora" / "manifests" / "gate2.json"
GENERATED = REPO / "docs" / "gate1" / "artifacts"
RESULTS = REPO / "results" / "gate2"


def load_corpus() -> list[tuple[str, int, str]]:
    """(id, row, text) for every fetched artifact plus the generated pair.

    Reads ONLY from the store. The manifest supplies ids and rows; the text comes from disk.
    """
    items: list[tuple[str, int, str]] = []
    man = json.loads(MANIFEST.read_text(encoding="utf-8"))
    for it in man["items"]:
        if "sha256" not in it:
            continue
        key = hashlib.sha256(it["requested_url"].encode("utf-8")).hexdigest()[:16]
        p = STORE / f"{key}.txt"
        if p.exists():
            items.append((it["id"], it["row"], p.read_text(encoding="utf-8")))
    for stem, row in (("item_A", 6), ("item_B", 7), ("item_C", 6)):
        items.append((stem, row, (GENERATED / f"{stem}.md").read_text(encoding="utf-8")))
    return items


def profile(runs: list[LoopRun]) -> dict:
    if not runs:
        return {}
    best_p = [r.reading.purpose.best for r in runs]
    named = [
        sum(1 for d in r.reading.decisions if d.alternative_rejected.strip())
        / max(1, len(r.reading.decisions))
        for r in runs
    ]
    return {
        "k": len(runs),
        "purpose_agreement": max(best_p.count(x) for x in set(best_p)) / len(best_p),
        "purposes": best_p,
        "named_alternative_rate": statistics.fmean(named),
        "mean_decisions": statistics.fmean(len(r.reading.decisions) for r in runs),
        "max_depth": max(r.reading.max_depth for r in runs),
        "machine": statistics.fmean(r.reading.audience.machine for r in runs),
        "audiences": [r.reading.audience.best for r in runs],
        "artifact_effort": [r.reading.artifact_effort for r in runs],
        "n_chars": 0,
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--k", type=int, default=3)
    ap.add_argument("--arm", default="local")
    ap.add_argument("--freeform", action="store_true", default=True)
    args = ap.parse_args()

    verify_all()
    from prereg.gate2 import card_hash
    print(f"locks ok | family v{load_family().version} | gate2 card {card_hash()[:12]} | "
          f"arm={args.arm} k={args.k}\n", flush=True)

    corpus = load_corpus()
    print(f"corpus: {len(corpus)} artifacts "
          f"({sum(1 for _, r, _ in corpus if r == 2)} row2, "
          f"{sum(1 for _, r, _ in corpus if r == 3)} row3, "
          f"{sum(1 for _, r, _ in corpus if r == 5)} row5, "
          f"{sum(1 for _, r, _ in corpus if r in (6, 7))} generated)\n", flush=True)

    out: dict[str, dict] = {}
    for aid, row, text in corpus:
        art = Artifact(text=text[:12000], source_id=aid)
        b_runs, f_runs, fails = [], [], []
        for s in range(args.k):
            c = make_client(args.arm, seed=s)
            try:
                b_runs.append(run_loop(c, art, seed=s))
            except Exception as e:                              # noqa: BLE001
                fails.append(f"bounded {s}: {type(e).__name__}")
            if args.freeform:
                try:
                    f_runs.append(run_freeform(c, art, seed=s))
                except Exception as e:                          # noqa: BLE001
                    fails.append(f"free {s}: {type(e).__name__}")
        b, f = profile(b_runs), profile(f_runs)
        for d in (b, f):
            if d:
                d["n_chars"] = len(text)
        out[aid] = {"row": row, "bounded": b, "freeform": f, "failures": fails}
        print(f"  {aid:<26} row{row} "
              f"bounded[agree={b.get('purpose_agreement', 0):.2f} "
              f"alt={b.get('named_alternative_rate', 0):.2f} "
              f"mach={b.get('machine', 0):.2f} depth={b.get('max_depth', 0)}] "
              f"free[agree={f.get('purpose_agreement', 0):.2f} "
              f"alt={f.get('named_alternative_rate', 0):.2f}]", flush=True)

    RESULTS.mkdir(parents=True, exist_ok=True)
    (RESULTS / f"gate2_{args.arm}_k{args.k}.json").write_text(
        json.dumps({"gate": 2, "card": card_hash(), "arm": args.arm, "k": args.k,
                    "family_sha256": hash_file(FAMILY_PATH), "artifacts": out}, indent=2),
        encoding="utf-8")
    print(f"\nwrote {(RESULTS / f'gate2_{args.arm}_k{args.k}.json').relative_to(REPO)}")


if __name__ == "__main__":
    main()
