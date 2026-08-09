"""G114 — the paper's H2, run with model readers: does goal-inference converge on human artifacts
and scatter on machine ones?

The virus paper (H2) predicts that independent readers asked to reverse-engineer a goal will
**cluster** on human artifacts (a true latent reward exists) and **scatter toward noise** on
generated ones (no latent to converge on — each reader hallucinates an idiosyncratic fit). The
theory folder holds a live counter-prediction: **flattened/specified intent is *immediately*
reconstructable** (PD-6), so a machine artifact written under dense stacked specifications should
produce HIGH agreement, and the crash should appear only where intent was never specified.

── THE TEST ──────────────────────────────────────────────────────────────────────────────────

Five groups, ~10 artifacts each: human books, human student essays, machine rung-10 (dense
specified intent), machine rung-0/1 (minimal intent), no-maker text. For each artifact, ask the
local model eight times (temperature 0.9): *"In one sentence: what was the maker of this passage
trying to achieve?"* Convergence = mean pairwise content-word Jaccard across the eight answers.

    H2 (essay)            human groups > both machine groups > nomaker
    FLATTENED (PD-6)      rung-10 >= human > rung-0 ~ nomaker — agreement tracks specified
                          intent, not species of maker
    NEITHER               no stable ordering. Report the group means with bootstrap CIs either way
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
STOP = set("the a an and or but of to in on for with as at by from is are was were be been this "
           "that it its their his her they he she you your i we our not no so if then than".split())


def ask(model: str, text: str, seed: int) -> str:
    prompt = ("Read the passage below, then answer in ONE sentence and nothing else: "
              "what was the maker of this passage trying to achieve?\n\n---\n" + text)
    req = urllib.request.Request(OLLAMA, data=json.dumps(
        {"model": model, "prompt": prompt, "stream": False,
         "options": {"temperature": 0.9, "seed": seed, "num_predict": 80}}).encode(),
        headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=300) as r:
        return json.loads(r.read())["response"].strip()


def content(s: str) -> set[str]:
    return {w for w in re.findall(r"[a-z']+", s.lower()) if w not in STOP and len(w) > 2}


def jaccard_mean(answers: list[str]) -> float:
    sets = [content(a) for a in answers]
    pairs = [(len(a & b) / len(a | b)) if (a | b) else 0.0
             for a, b in itertools.combinations(sets, 2)]
    return sum(pairs) / len(pairs)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="qwen3.5:9b")
    ap.add_argument("--per-group", type=int, default=10)
    ap.add_argument("--samples", type=int, default=8)
    ap.add_argument("--max-words", type=int, default=400)
    args = ap.parse_args()
    rng = random.Random(7)

    def take(txt: str) -> str:
        return " ".join(txt.split()[: args.max_words])

    groups: dict[str, list[tuple[str, str]]] = {}
    books = json.loads((REPO / "corpora" / "manifests" / "books.json").read_text(encoding="utf-8"))
    items = books["items"] if isinstance(books, dict) else books
    picks = rng.sample(items, min(args.per_group, len(items)))
    groups["human_books"] = [
        (it["id"], take((REPO / "corpora" / "store" / f"{it['id']}.txt")
                        .read_text(encoding="utf-8", errors="ignore")[5000:40000]))
        for it in picks if (REPO / "corpora" / "store" / f"{it['id']}.txt").exists()]

    arg_dir = REPO / "corpora" / "public" / "argrewrite" / "essays"
    essays = sorted(arg_dir.glob("*.txt")) if arg_dir.exists() else []
    groups["human_essays"] = [(p.stem, take(p.read_text(encoding="utf-8", errors="ignore")))
                              for p in rng.sample(essays, min(args.per_group, len(essays)))]

    lad = json.loads((REPO / "corpora" / "ladder2" / "manifest.json").read_text(encoding="utf-8"))
    hi = [it for it in lad["items"] if it.get("rung") == 10]
    lo = [it for it in lad["items"] if it.get("rung") in (0, 1)]
    for name, pool in (("machine_rung10", hi), ("machine_rung01", lo)):
        sel = rng.sample(pool, min(args.per_group, len(pool)))
        groups[name] = [(it["id"], take((REPO / "corpora" / "ladder2" / f"{it['id']}.txt")
                                        .read_text(encoding="utf-8"))) for it in sel]

    nm = json.loads((REPO / "corpora" / "nomaker" / "manifest.json").read_text(encoding="utf-8"))
    sel = rng.sample(nm["items"], min(args.per_group, len(nm["items"])))
    groups["nomaker"] = [(it["id"], take((REPO / "corpora" / "nomaker" / f"{it['id']}.txt")
                                         .read_text(encoding="utf-8"))) for it in sel]

    out = {"model": args.model, "samples": args.samples, "groups": {}}
    for gname, arts in groups.items():
        vals = []
        for aid, text in arts:
            if not text.strip():
                continue
            answers = [ask(args.model, text, seed=1000 + i) for i in range(args.samples)]
            c = jaccard_mean(answers)
            vals.append({"id": aid, "convergence": c, "answers": answers})
            print(f"  {gname:<16}{aid:<18}{c:.3f}", flush=True)
        mean = sum(v["convergence"] for v in vals) / max(len(vals), 1)
        out["groups"][gname] = {"n": len(vals), "mean_convergence": mean, "items": vals}
        print(f"{gname}: mean convergence {mean:.3f} over {len(vals)}", flush=True)

    means = {g: v["mean_convergence"] for g, v in out["groups"].items()}
    order = sorted(means, key=means.get, reverse=True)
    print("\n  ordering:", " > ".join(f"{g}({means[g]:.2f})" for g in order))
    h2 = (means.get("human_books", 0) > means.get("machine_rung10", 0)
          and means.get("human_essays", 0) > means.get("machine_rung10", 0))
    flat = means.get("machine_rung10", 0) >= max(means.get("human_books", 0),
                                                 means.get("human_essays", 0))
    out["verdict"] = ("H2-ESSAY" if h2 else "FLATTENED-INTENT" if flat else "NEITHER-CLEANLY")
    print(f"\n  >>> {out['verdict']}")

    RESULTS.mkdir(parents=True, exist_ok=True)
    (RESULTS / "summary.json").write_text(json.dumps(out, indent=2),
                                          encoding="utf-8", newline="\n")
    print(f"wrote {(RESULTS / 'summary.json').relative_to(REPO)}")


if __name__ == "__main__":
    main()
