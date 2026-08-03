"""Gate 3. The claim gate.

Runs the corpus locked in `corpora/manifests/gate3.json` against the criteria locked in
`prereg/gate3.py`, and applies the pre-specified handling — domain cap, no outlier removal, no
retries — exactly as the card states it.

Both arms run on every artifact, because G3.3 (the boundedness ablation) needs them.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import statistics
import sys
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from soundingline.baselines.freeform import run_freeform          # noqa: E402
from soundingline.family.loader import FAMILY_PATH, load_family   # noqa: E402
from soundingline.hashlock import hash_file                       # noqa: E402
from soundingline.locks import verify_all                         # noqa: E402
from soundingline.loop.run import LoopRun, run_loop               # noqa: E402
from soundingline.probe.client import make_client                 # noqa: E402
from soundingline.probe.render import Artifact                    # noqa: E402

STORE = REPO / "corpora" / "store"
MANIFEST = REPO / "corpora" / "manifests" / "gate3.json"
RESULTS = REPO / "results" / "gate3"
DOMAIN_CAP = 3


def load_corpus() -> list[tuple[str, str, str]]:
    """(id, half, text) after the pre-registered domain cap.

    The cap is applied HERE, before any statistic, by sorted URL — deterministic and stated in
    the card, so it cannot be tuned after seeing a result.
    """
    from urllib.parse import urlparse
    man = json.loads(MANIFEST.read_text(encoding="utf-8"))
    by_host: dict[str, list[dict]] = defaultdict(list)
    for it in man["items"]:
        u = it["final_url"] if "final_url" in it else it["url"]
        host = urlparse(u).hostname or "?"
        # archived snapshots keep their original host in the path; cap on the ORIGIN, not on
        # web.archive.org, or every archived artifact would collapse into one bucket.
        if host == "web.archive.org":
            host = "archived:" + u.split("/http", 1)[-1][:40]
        by_host[host].append(it)

    out = []
    for host, items in sorted(by_host.items()):
        for it in sorted(items, key=lambda x: x["url"])[:DOMAIN_CAP]:
            key = hashlib.sha256(it["requested_url"].encode("utf-8")).hexdigest()[:16]
            p = STORE / f"{key}.txt"
            if p.exists():
                out.append((it["id"], it["half"], p.read_text(encoding="utf-8")))
    return out


def profile(runs: list[LoopRun], text: str) -> dict:
    if not runs:
        return {}
    before = statistics.fmean(r.decisions_before_settle for r in runs)
    after = statistics.fmean(r.decisions_after_settle for r in runs)
    unlocks = [(r.decisions_after_settle / r.decisions_before_settle)
               if r.decisions_before_settle > 0.05 else 1.0 for r in runs]
    best_p = [r.reading.purpose.best for r in runs]
    named = [sum(1 for d in r.reading.decisions if d.alternative_rejected.strip())
             / max(1, len(r.reading.decisions)) for r in runs]
    return {
        "k": len(runs),
        "unlock": statistics.fmean(unlocks),
        "unlock_sd": statistics.pstdev(unlocks),
        "unlock_trivial": all(abs(u - 1.0) < 1e-9 for u in unlocks),
        "before": before, "after": after,
        "named_alternative_rate": statistics.fmean(named),
        "purpose_agreement": max(best_p.count(x) for x in set(best_p)) / len(best_p),
        "machine": statistics.fmean(r.reading.audience.machine for r in runs),
        "max_depth": max(r.reading.max_depth for r in runs),
        "n_chars": len(text),
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--k", type=int, default=5)
    ap.add_argument("--arm", default="local")
    ap.add_argument("--limit", type=int, default=0)
    args = ap.parse_args()

    verify_all()
    from prereg.gate3 import card_hash
    corpus = load_corpus()
    if args.limit:
        corpus = corpus[: args.limit]

    nA = sum(1 for _, h, _ in corpus if h == "A")
    nB = sum(1 for _, h, _ in corpus if h == "B")
    print(f"locks ok | family v{load_family().version} | gate3 card {card_hash()[:12]}")
    print(f"corpus after domain cap ({DOMAIN_CAP}/host): A={nA} B={nB} total={len(corpus)} "
          f"| arm={args.arm} k={args.k}\n", flush=True)

    out: dict[str, dict] = {}
    for idx, (aid, half, text) in enumerate(corpus, 1):
        art = Artifact(text=text[:12000], source_id=aid)
        b_runs, f_runs, fails = [], [], []
        for s in range(args.k):
            c = make_client(args.arm, seed=s)
            try:
                b_runs.append(run_loop(c, art, seed=s))
            except Exception as e:                              # noqa: BLE001
                fails.append(f"bounded {s}: {type(e).__name__}")
            try:
                f_runs.append(run_freeform(c, art, seed=s))
            except Exception as e:                              # noqa: BLE001
                fails.append(f"free {s}: {type(e).__name__}")
        b = profile(b_runs, text)
        f = profile(f_runs, text)
        out[aid] = {"half": half, "bounded": b, "freeform": f, "failures": fails}
        print(f"  [{idx:>2}/{len(corpus)}] {aid:<14} {half} "
              f"unlock={b.get('unlock', 0):.2f} alt={b.get('named_alternative_rate', 0):.2f} "
              f"mach={b.get('machine', 0):.2f} valid={len(b_runs)}/{args.k}", flush=True)

        RESULTS.mkdir(parents=True, exist_ok=True)
        (RESULTS / f"gate3_{args.arm}_k{args.k}.json").write_text(
            json.dumps({"gate": 3, "card": card_hash(), "arm": args.arm, "k": args.k,
                        "domain_cap": DOMAIN_CAP,
                        "family_sha256": hash_file(FAMILY_PATH), "artifacts": out}, indent=2),
            encoding="utf-8")

    print(f"\nwrote {(RESULTS / f'gate3_{args.arm}_k{args.k}.json').relative_to(REPO)}")


if __name__ == "__main__":
    main()
