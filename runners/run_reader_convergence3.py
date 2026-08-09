"""G114b — the convergence discriminator, rebuilt so it can actually discriminate.

v2's failures, both fixed here: token-overlap read topical narrowness (fix: a judge model rates
each answer-pair's goal-similarity 0-10, graded, topic-blind by instruction), and topic varied
freely across groups (fix: the machine dose comparison holds TOPIC FIXED — the ladder reuses
topics across rungs, so low-rung and high-rung artifacts on the SAME topic are compared). The
essays group returns via the correct Draft3 path.

    H2 (paper)          human groups > dense-machine — no latent goal to converge on
    FLATTENED (traces)  dense-machine >= human, and dense > sparse AT FIXED TOPIC — agreement
                        tracks specified intent
    Either way the fixed-topic dose contrast is the number v2 never had.
"""

from __future__ import annotations

import argparse
import itertools
import json
import random
import re
import sys
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

RESULTS = REPO / "results" / "reader_convergence"
OLLAMA = "http://127.0.0.1:11434/api/generate"


def ask(model, prompt, seed, n_predict=200, temp=0.9):
    req = urllib.request.Request(OLLAMA, data=json.dumps(
        {"model": model, "prompt": prompt, "stream": False, "think": False,
         "options": {"temperature": temp, "seed": seed, "num_predict": n_predict}}).encode(),
        headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=300) as r:
        resp = json.loads(r.read()).get("response", "")
    return re.sub(r"<think>.*?</think>", "", resp, flags=re.DOTALL).strip()


def goal_guess(model, text, seed):
    return ask(model, "Read the passage below, then answer in ONE sentence and nothing else: "
                      "what was the maker of this passage trying to achieve?\n\n---\n" + text, seed)


def judge(model, a, b, seed):
    out = ask(model, "Two readers guessed the goal behind the same passage. Ignore topic and "
                     "wording; rate 0-10 how similar the GOALS they describe are. Answer with the "
                     f"number only.\nGuess A: {a}\nGuess B: {b}", seed, n_predict=8, temp=0.0)
    m = re.search(r"\d+", out)
    return min(int(m.group()), 10) / 10 if m else None


def convergence(model, answers, seed0):
    scores = [s for i, (a, b) in enumerate(itertools.combinations(answers, 2))
              if (s := judge(model, a, b, seed0 + i)) is not None]
    return sum(scores) / len(scores) if scores else None


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="qwen3.5:9b")
    ap.add_argument("--samples", type=int, default=5)
    ap.add_argument("--max-words", type=int, default=400)
    args = ap.parse_args()
    rng = random.Random(7)

    def take(t):
        return " ".join(t.split()[: args.max_words])

    d = REPO / "corpora" / "ladder2"
    man = json.loads((d / "manifest.json").read_text(encoding="utf-8"))
    by_topic: dict[int, dict] = {}
    for it in man["items"]:
        if not isinstance(it.get("rung"), int):
            continue
        topic = int(it["id"].split("_")[1]) % 5
        by_topic.setdefault(topic, {})[it["rung"]] = it["id"]

    groups: dict[str, list] = {"machine_dense_fixedtopic": [], "machine_sparse_fixedtopic": []}
    for topic, rungs in sorted(by_topic.items()):
        hi = rungs.get(10)
        lo = rungs.get(1, rungs.get(0))
        if hi and lo:
            groups["machine_dense_fixedtopic"].append(
                (hi, take((d / f"{hi}.txt").read_text(encoding="utf-8"))))
            groups["machine_sparse_fixedtopic"].append(
                (lo, take((d / f"{lo}.txt").read_text(encoding="utf-8"))))
    for g in ("machine_dense_fixedtopic", "machine_sparse_fixedtopic"):
        groups[g] = groups[g][:8]

    essays = sorted((REPO / "corpora" / "public" / "argrewrite" / "essays" / "Draft3").glob("*.txt"))
    groups["human_essays"] = [(p.stem, take(p.read_text(encoding="utf-8", errors="ignore")))
                              for p in rng.sample(essays, min(8, len(essays)))]
    lut = {}
    for m in (REPO / "corpora" / "store").glob("*.meta.json"):
        meta = json.loads(m.read_text(encoding="utf-8"))
        for k in ("requested_url", "final_url"):
            if meta.get(k):
                lut[meta[k]] = m.with_name(m.name.replace(".meta.json", ".txt"))
    books = json.loads((REPO / "corpora" / "manifests" / "books.json").read_text(encoding="utf-8"))
    bitems = rng.sample(books["items"] if isinstance(books, dict) else books, 8)
    groups["human_books"] = []
    for it in bitems:
        p = lut.get(it.get("url")) or lut.get(it.get("final_url"))
        if p and p.exists():
            groups["human_books"].append(
                (it["id"], take(p.read_text(encoding="utf-8", errors="ignore")[5000:40000])))

    out = {"model": args.model, "samples": args.samples, "groups": {}}
    for gname, arts in groups.items():
        vals = []
        for aid, text in arts:
            if not text.strip():
                continue
            answers = [a for a in (goal_guess(args.model, text, 1000 + i)
                                   for i in range(args.samples)) if a]
            if len(answers) < 3:
                continue
            c = convergence(args.model, answers, seed0=hash(aid) % 10000)
            if c is not None:
                vals.append({"id": aid, "convergence": c})
                print(f"  {gname:<26}{aid:<16}{c:.3f}", flush=True)
        mean = sum(v["convergence"] for v in vals) / max(len(vals), 1)
        out["groups"][gname] = {"n": len(vals), "mean": mean, "items": vals}
        print(f"{gname}: mean {mean:.3f} over {len(vals)}", flush=True)

    g = {k: v["mean"] for k, v in out["groups"].items()}
    dose = g.get("machine_dense_fixedtopic", 0) - g.get("machine_sparse_fixedtopic", 0)
    out["fixed_topic_dose_gap"] = dose
    human = max(g.get("human_books", 0), g.get("human_essays", 0))
    out["verdict"] = ("FLATTENED-INTENT" if dose > 0.1 and g.get("machine_dense_fixedtopic", 0) >= human
                      else "H2-PAPER" if human > g.get("machine_dense_fixedtopic", 0) + 0.1
                      else "NEITHER-CLEANLY")
    print(f"\n  fixed-topic dose gap: {dose:+.3f}\n  >>> {out['verdict']}")

    RESULTS.mkdir(parents=True, exist_ok=True)
    (RESULTS / "summary_v3.json").write_text(json.dumps(out, indent=2),
                                             encoding="utf-8", newline="\n")
    print(f"wrote {(RESULTS / 'summary_v3.json').relative_to(REPO)}")


if __name__ == "__main__":
    main()
