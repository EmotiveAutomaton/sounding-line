"""G129-pilot — event-level choice recovery on ArgRewrite, zero-shot arm.

PILOT, not the confirmatory run. The confirmatory analysis stays gated on this pilot's
measurement lessons and the curator's read. Pre-registered here before the run:

    QUESTION    given the revision delta (old -> new sentence), can a bounded reader pick the
                recorded purpose from a bounded candidate set, above chance and above its own
                controls?
    READER      the local model, zero-shot (no training pass, so author leakage is impossible)
    CANDIDATES  the true purpose plus k-1 decoys drawn from the OTHER purposes present in the
                corpus at the same grain, sampled by corpus frequency (so decoys are not rare
                strawmen); the harness lesson applies, ties break randomly
    ARMS        recovery (delta shown) / blind (no delta, candidates only) / shuffled-truth
                (delta shown, truth replaced by another event's label)
    GRAINS      coarse (2-way) and fine (top-8 labels), candidate sizes k=4 and k=8 for fine
    REPORT      accuracy vs 1/k chance per arm; per-author spread; per-purpose confusion
    GATES       blind at chance, shuffle at chance, else the arm's number is not believed

The delta lesson from L59 is built in: the prompt shows added and removed words explicitly,
since sentence text alone encodes topic. Checkpointed per event; resumes across queue passes.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

RESULTS = REPO / "results" / "arg_recovery"
EVENTS = REPO / "results" / "arg_baselines" / "events.json"
OLLAMA = "http://127.0.0.1:11434/api/generate"
MODEL = "qwen3.5:9b"


def ask(prompt: str, seed: int) -> str:
    req = urllib.request.Request(OLLAMA, data=json.dumps(
        {"model": MODEL, "prompt": prompt, "stream": False, "think": False,
         "options": {"temperature": 0.0, "seed": seed, "num_predict": 30}}).encode(),
        headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=300) as r:
        resp = json.loads(r.read()).get("response", "")
    return re.sub(r"<think>.*?</think>", "", resp, flags=re.DOTALL).strip()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--grain", required=True, choices=["coarse", "fine"])
    ap.add_argument("--k", type=int, default=4)
    ap.add_argument("--arm", required=True, choices=["recovery", "blind", "shuffle"])
    ap.add_argument("--uniform", action="store_true",
                    help="uniform decoy sampling -- the pilot's blind arm ran above chance "
                         "because frequency-weighted decoys leak the label prior (L62)")
    args = ap.parse_args()

    import numpy as np                                                # noqa: PLC0415

    rng = np.random.default_rng(23)
    events = json.loads(EVENTS.read_text(encoding="utf-8"))["events"]
    labs_all = [e[args.grain] for e in events]
    keep = sorted({l for l in set(labs_all) if labs_all.count(l) >= 30})
    sub = [e for e in events if e[args.grain] in keep]
    freq = {l: labs_all.count(l) for l in keep}
    k = min(args.k, len(keep))
    shuffled = list(rng.permutation([e[args.grain] for e in sub]))

    tag = f"{args.grain}_k{k}{'u' if args.uniform else ''}_{args.arm}"
    part = RESULTS / f"{tag}_partial.jsonl"
    RESULTS.mkdir(parents=True, exist_ok=True)
    done = set()
    if part.exists():
        for line in part.read_text(encoding="utf-8").splitlines():
            done.add(json.loads(line)["i"])
    print(f"{tag}: {len(sub)} events, {len(keep)} labels, k={k}, {len(done)} done")

    def delta(e):
        o, n = e["old"].lower().split(), e["new"].lower().split()
        added = [w for w in n if w not in set(o)][:25]
        removed = [w for w in o if w not in set(n)][:25]
        return (f"ADDED: {' '.join(added) or '(nothing)'}\n"
                f"REMOVED: {' '.join(removed) or '(nothing)'}\n"
                f"BEFORE: {e['old'][:250]}\nAFTER: {e['new'][:250]}")

    with part.open("a", encoding="utf-8", newline="\n") as fh:
        for i, e in enumerate(sub):
            if i in done:
                continue
            truth = shuffled[i] if args.arm == "shuffle" else e[args.grain]
            decoys = [l for l in keep if l != truth]
            if args.uniform:
                picks = list(rng.choice(decoys, size=min(k - 1, len(decoys)),
                                        replace=False))
            else:
                w = np.array([freq[l] for l in decoys], float)
                picks = list(rng.choice(decoys, size=min(k - 1, len(decoys)),
                                        replace=False, p=w / w.sum()))
            cands = picks + [truth]
            rng.shuffle(cands)
            body = "" if args.arm == "blind" else delta(e) + "\n"
            opts = "\n".join(f"- {l}" for l in cands)
            ans = ask(f"A student revised one sentence of an argumentative essay.\n{body}"
                      f"Which revision purpose fits best? Answer with exactly one label "
                      f"from:\n{opts}\nLabel:", seed=500 + i).lower()
            got = [l for l in cands if l in ans]
            pick = got[0] if len(got) == 1 else str(rng.choice(got or cands))
            fh.write(json.dumps({"i": i, "truth": truth, "pick": pick,
                                 "author": e["author"], "cands": len(cands)}) + "\n")
            fh.flush()
            if (i + 1) % 200 == 0:
                print(f"  {i + 1}/{len(sub)}", flush=True)

    rows = [json.loads(x) for x in part.read_text(encoding="utf-8").splitlines()]
    acc = sum(r["truth"] == r["pick"] for r in rows) / max(len(rows), 1)
    per_a: dict[str, list[bool]] = {}
    conf: dict[str, dict[str, int]] = {}
    for r in rows:
        per_a.setdefault(r["author"], []).append(r["truth"] == r["pick"])
        conf.setdefault(r["truth"], {})
        conf[r["truth"]][r["pick"]] = conf[r["truth"]].get(r["pick"], 0) + 1
    out = {"grain": args.grain, "k": k, "arm": args.arm, "n": len(rows),
           "accuracy": acc, "chance": 1.0 / k,
           "per_author_acc": {a: sum(v) / len(v) for a, v in per_a.items()},
           "confusion": conf}
    (RESULTS / f"{tag}.json").write_text(json.dumps(out, indent=1),
                                         encoding="utf-8", newline="\n")
    print(f"{tag}: accuracy {acc:.3f} vs chance {1.0 / k:.3f} on {len(rows)}")
    print(f"wrote {(RESULTS / f'{tag}.json').relative_to(REPO)}")


if __name__ == "__main__":
    main()
