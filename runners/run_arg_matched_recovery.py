"""G130c — does the pilot's recovery margin survive the matching that killed content-ness?

L65: fine purposes recover at 0.477 against a verified 0.25 floor. L66: coarse content-ness
collapses to chance once revisions are matched on size, rarity shift, position, and difficulty.
The collision: rerun purpose recovery ON the matched common-support subset. If the margin
survives, purpose information is more than the covariates; if it collapses, the pilot's margin
was riding the same magnitudes that carried L42.

Same CEM construction as `run_arg_matched.py` (same seed, identical strata), then the recovery
and blind arms with uniform candidates on the matched events only.

    SURVIVES    matched-subset recovery margin over its blind floor >= 0.10
    COLLAPSES   the margin falls under 0.05
    (between: WEAKENED, reported as such)
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

COMMON = None


def rare_rate(text: str) -> float:
    global COMMON
    if COMMON is None:
        from wordfreq import top_n_list                               # noqa: PLC0415
        COMMON = set(top_n_list("en", 5000))
    ws = [w.strip(".,;:!?\"'()").lower() for w in text.split()]
    ws = [w for w in ws if w]
    return sum(w not in COMMON for w in ws) / len(ws) if ws else 0.0


def ask(prompt: str, seed: int) -> str:
    req = urllib.request.Request(OLLAMA, data=json.dumps(
        {"model": "qwen3.5:9b", "prompt": prompt, "stream": False, "think": False,
         "options": {"temperature": 0.0, "seed": seed, "num_predict": 30}}).encode(),
        headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=300) as r:
        resp = json.loads(r.read()).get("response", "")
    return re.sub(r"<think>.*?</think>", "", resp, flags=re.DOTALL).strip()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--arm", required=True, choices=["recovery", "blind"])
    args = ap.parse_args()

    import numpy as np                                                # noqa: PLC0415

    all_events = [e for e in json.loads(EVENTS.read_text(encoding="utf-8"))["events"]
                  if e["coarse"] in ("surface", "content")]

    def covs(e):
        o, n = e["old"].split(), e["new"].split()
        os_, ns_ = set(w.lower() for w in o), set(w.lower() for w in n)
        return [len(ns_ - os_), len(os_ - ns_), len(n) - len(o),
                rare_rate(e["new"]) - rare_rate(e["old"]),
                min(len(o), 60), rare_rate(e["old"])]

    C = np.array([covs(e) for e in all_events], float)
    y = np.array([e["coarse"] == "content" for e in all_events])
    Z = (C - C.mean(0)) / (C.std(0) + 1e-9)
    rng_m = np.random.default_rng(41)                                 # SAME seed as G130b v2
    bins = np.stack([np.digitize(Z[:, j], np.quantile(Z[:, j], [1 / 3, 2 / 3]))
                     for j in range(Z.shape[1])], axis=1)
    strata: dict = {}
    for i, b in enumerate(bins):
        strata.setdefault(tuple(b), {"c": [], "s": []})["c" if y[i] else "s"].append(i)
    keep = set()
    for st in strata.values():
        n = min(len(st["c"]), len(st["s"]))
        if n == 0:
            continue
        keep.update(rng_m.permutation(st["c"])[:n].tolist())
        keep.update(rng_m.permutation(st["s"])[:n].tolist())
    sub_all = [all_events[i] for i in sorted(keep)]

    labs_all = [e["fine"] for e in sub_all]
    keep_lab = sorted({l for l in set(labs_all) if labs_all.count(l) >= 20})
    sub = [e for e in sub_all if e["fine"] in keep_lab]
    k = min(4, len(keep_lab))
    rng = np.random.default_rng(23)
    print(f"matched subset: {len(sub_all)} events, {len(sub)} with kept labels "
          f"({len(keep_lab)} labels), k={k}")

    def delta(e):
        o, n = e["old"].lower().split(), e["new"].lower().split()
        added = [w for w in n if w not in set(o)][:25]
        removed = [w for w in o if w not in set(n)][:25]
        return (f"ADDED: {' '.join(added) or '(nothing)'}\n"
                f"REMOVED: {' '.join(removed) or '(nothing)'}\n"
                f"BEFORE: {e['old'][:250]}\nAFTER: {e['new'][:250]}")

    tag = f"matched_k{k}_{args.arm}"
    part = RESULTS / f"{tag}_partial.jsonl"
    RESULTS.mkdir(parents=True, exist_ok=True)
    done = set()
    if part.exists():
        for line in part.read_text(encoding="utf-8").splitlines():
            done.add(json.loads(line)["i"])
    with part.open("a", encoding="utf-8", newline="\n") as fh:
        for i, e in enumerate(sub):
            if i in done:
                continue
            truth = e["fine"]
            decoys = [l for l in keep_lab if l != truth]
            picks = list(rng.choice(decoys, size=min(k - 1, len(decoys)), replace=False))
            cands = picks + [truth]
            rng.shuffle(cands)
            body = "" if args.arm == "blind" else delta(e) + "\n"
            opts = "\n".join(f"- {l}" for l in cands)
            ans = ask(f"A student revised one sentence of an argumentative essay.\n{body}"
                      f"Which revision purpose fits best? Answer with exactly one label "
                      f"from:\n{opts}\nLabel:", seed=900 + i).lower()
            got = [l for l in cands if l in ans]
            pick = got[0] if len(got) == 1 else str(rng.choice(got or cands))
            fh.write(json.dumps({"i": i, "truth": truth, "pick": pick}) + "\n")
            fh.flush()

    rows = [json.loads(x) for x in part.read_text(encoding="utf-8").splitlines()]
    acc = sum(r["truth"] == r["pick"] for r in rows) / max(len(rows), 1)
    out = {"arm": args.arm, "n": len(rows), "k": k, "accuracy": acc, "chance": 1.0 / k}
    (RESULTS / f"{tag}.json").write_text(json.dumps(out, indent=1),
                                         encoding="utf-8", newline="\n")
    print(f"{tag}: accuracy {acc:.3f} vs 1/k {1.0 / k:.3f} on {len(rows)}")
    print(f"wrote {(RESULTS / f'{tag}.json').relative_to(REPO)}")


if __name__ == "__main__":
    main()
