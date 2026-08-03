"""Gate 3, scheduled concurrently instead of serially.

── WHAT THIS CHANGES, AND WHAT IT MUST NOT ───────────────────────────────────────────────────

The serial runner measured ~13 minutes per artifact and would have taken ~10 hours, because it
issues one Ollama request at a time and the GPU idles between them. That is a scheduling problem,
not a measurement problem, and it is fixed here by running the k seeds of one artifact
concurrently.

**The instrument is untouched.** Same corpus, same domain cap, same order, same `run_loop`, same
`run_freeform`, same `profile`, same per-seed client construction, same `num_ctx`. Every request
still carries its own explicit seed, so a given (artifact, seed) produces the same reading whether
it ran alone or beside four others — the seed is a property of the request, not of the scheduler.

`num_ctx` is deliberately NOT reduced to buy VRAM headroom. Shrinking the context would silently
truncate long artifacts and would make results incomparable with the seven already collected, and
a faster run of a different instrument is not a faster run.

── RESUME ────────────────────────────────────────────────────────────────────────────────────

Artifacts already present in the output file are skipped, not recomputed. The serial run's seven
completed artifacts are therefore kept rather than thrown away, and they are byte-identical to what
this runner would have produced for them.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from soundingline.baselines.freeform import run_freeform          # noqa: E402
from soundingline.family.loader import FAMILY_PATH, load_family   # noqa: E402
from soundingline.hashlock import hash_file                       # noqa: E402
from soundingline.locks import verify_all                         # noqa: E402
from soundingline.loop.run import run_loop                        # noqa: E402
from soundingline.probe.client import make_client                 # noqa: E402
from soundingline.probe.render import Artifact                    # noqa: E402

from runners.run_gate3 import DOMAIN_CAP, RESULTS, load_corpus, profile   # noqa: E402


def one_seed(arm: str, art: Artifact, s: int) -> tuple[int, object, object, list[str]]:
    """One seed's two readings. Returns (seed, bounded_or_None, freeform_or_None, failures).

    A fresh client per seed: the client holds only (model, seed, num_ctx, host) and builds a new
    `ollama.Client` per request, so there is no shared mutable state to race on.
    """
    fails: list[str] = []
    b = f = None
    c = make_client(arm, seed=s)
    try:
        b = run_loop(c, art, seed=s)
    except Exception as e:                                        # noqa: BLE001
        fails.append(f"bounded {s}: {type(e).__name__}")
    try:
        f = run_freeform(c, art, seed=s)
    except Exception as e:                                        # noqa: BLE001
        fails.append(f"free {s}: {type(e).__name__}")
    return s, b, f, fails


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--k", type=int, default=5)
    ap.add_argument("--arm", default="local")
    ap.add_argument("--workers", type=int, default=3,
                    help="concurrent seeds. Bounded by OLLAMA_NUM_PARALLEL on the server side; "
                         "asking for more than the server will run just queues them.")
    ap.add_argument("--limit", type=int, default=0)
    args = ap.parse_args()

    verify_all()
    from prereg.gate3 import card_hash
    corpus = load_corpus()
    if args.limit:
        corpus = corpus[: args.limit]

    out_path = RESULTS / f"gate3_{args.arm}_k{args.k}.json"
    out: dict[str, dict] = {}
    if out_path.exists():
        out = json.loads(out_path.read_text(encoding="utf-8")).get("artifacts", {})

    todo = [(aid, half, text) for aid, half, text in corpus if aid not in out]
    print(f"locks ok | family v{load_family().version} | gate3 card {card_hash()[:12]}")
    print(f"corpus {len(corpus)} after domain cap ({DOMAIN_CAP}/host) | "
          f"already done {len(out)} | to run {len(todo)} | "
          f"arm={args.arm} k={args.k} workers={args.workers}\n", flush=True)

    t_start = time.perf_counter()
    for idx, (aid, half, text) in enumerate(todo, 1):
        t0 = time.perf_counter()
        art = Artifact(text=text[:12000], source_id=aid)
        b_runs, f_runs, fails = [], [], []
        with ThreadPoolExecutor(max_workers=args.workers) as pool:
            for _s, b, f, fl in sorted(pool.map(lambda s: one_seed(args.arm, art, s),
                                                range(args.k))):
                if b is not None:
                    b_runs.append(b)
                if f is not None:
                    f_runs.append(f)
                fails.extend(fl)

        b = profile(b_runs, text)
        out[aid] = {"half": half, "bounded": b, "freeform": profile(f_runs, text),
                    "failures": fails}

        dt = time.perf_counter() - t0
        rate = (time.perf_counter() - t_start) / idx
        eta_min = rate * (len(todo) - idx) / 60.0
        print(f"  [{idx:>2}/{len(todo)}] {aid:<14} {half} "
              f"unlock={b.get('unlock', 0):.2f} alt={b.get('named_alternative_rate', 0):.2f} "
              f"mach={b.get('machine', 0):.2f} valid={len(b_runs)}/{args.k} "
              f"| {dt/60:.1f}m  ETA {eta_min/60:.1f}h", flush=True)

        RESULTS.mkdir(parents=True, exist_ok=True)
        out_path.write_text(
            json.dumps({"gate": 3, "card": card_hash(), "arm": args.arm, "k": args.k,
                        "domain_cap": DOMAIN_CAP, "scheduler": "parallel",
                        "workers": args.workers,
                        "family_sha256": hash_file(FAMILY_PATH), "artifacts": out}, indent=2),
            encoding="utf-8")

    print(f"\nwrote {out_path.relative_to(REPO)}  ({len(out)} artifacts)")


if __name__ == "__main__":
    main()
