"""G94 — the Taramsa test: does spec-style reconstruction posit decisions that were not
made, measured where the truth is known (the intent ladder).

Owed since the methods pass (L93 rerun plan). Newly sharpened by L140: the reader picks
semantic familiarity, which is exactly the mechanism that would invent decisions on
unspecified text. The ladder gives ground truth: every rung-r artifact was generated from
exactly r specifications drawn deterministically (seed 70000 + rung*1000 + i, stdlib
Random), so the true specs are RECONSTRUCTED here and verified against the manifest's
recorded prompt word count before anything runs (the join check; abort on any mismatch).

Arms (forced choice, the L139/L140 format lesson: candidate sets with an explicit none
option are the honest form, yes/no verification is not):
  fabrication   rung-0 artifacts (written from "Write about {topic}." alone): 4 spec
                candidates + "none of these was requested". Correct behavior is the none
                option; the fabrication rate is the Taramsa number
  recovery      rung 1/3/6/10 artifacts: per true spec, k = 4 (the spec + 3 decoys drawn
                from the pool minus the item's own set), artifact-only; per-rung accuracy
                is the dose curve
  blind         identical candidate sets, no artifact: the floor
  echo (CPU)    max content-word-overlap pick on identical sets: the trivia bar (L138)

DESIGN CHECK (2026-08-19, at design time). Lessons read: LESSONS §3 to §5 (including all
four of today's entries), CONTROLS 6/7. Exploratory, no verdict bands, nothing VOIDs.
Expectations both ways with directions: fabrication under the null (honest reader) = the
none option at the L140-observed rate (~0.05); under the alternative (Taramsa failure) =
spec assertions on unspecified text, direction UP — this is the claim arm. Recovery under
the alternative = above blind and above echo, falling with rung if dilution dominates or
flat if each spec leaves independent trace (both stated; the curve is the finding).
Blind = 1/k both ways (truth position seeded-uniform; the truth marginal is near-uniform
by construction since decoys draw from the same pool), guarded failure UP = construction
leak. Echo = the bar recovery must beat; specs are stylistic instructions whose wording
may echo into text, so echo above 1/k is expected, measured, and subtracted in prose.
Instrument failure direction: the reconstruction join check aborts the run on any
prompt-word mismatch, so wrong-truth scoring cannot happen silently.

Output: results/g94/taramsa.json (+ per-arm partial jsonl, checkpointed; done markers for
the produces guard).
"""

from __future__ import annotations

import argparse
import json
import random
import re
import sys
import time
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
LADDER = REPO / "corpora" / "ladder"
OUT = REPO / "results" / "g94"
OLLAMA = "http://127.0.0.1:11434/api/generate"
MODEL = "qwen3.5:9b"
DECODING = {"temperature": 0.0, "num_predict": 200}
SEED = 9400
K = 4
NONE_OPT = "none of these was requested"

sys.path.insert(0, str(REPO / "runners"))
from make_intent_ladder import SPECS, build                            # noqa: E402

STOP = set("the a an and or but if of to in on for with as by at from is are was were be "
           "been being it its this that these those not no than then so such your you "
           "one two about write".split())


def content_words(s: str) -> set:
    return {w.lower() for w in re.findall(r"[a-zA-Z']+", s)} - STOP


def call_reader(prompt: str) -> str | None:
    req = urllib.request.Request(OLLAMA, data=json.dumps(
        {"model": MODEL, "prompt": prompt, "stream": False, "think": False,
         "options": DECODING}).encode(), headers={"Content-Type": "application/json"})
    for attempt in range(6):
        try:
            with urllib.request.urlopen(req, timeout=600) as r:
                resp = json.loads(r.read()).get("response", "")
            return re.sub(r"<think>.*?</think>", "", resp, flags=re.DOTALL).strip()
        except Exception as e:                                        # noqa: BLE001
            print(f"  call failed (attempt {attempt + 1}): {e}")
            time.sleep(20 * (attempt + 1))
    return None


def parse_pick(resp: str | None, n: int) -> int | None:
    if not resp:
        return None
    m = re.search(r"\b([1-9]|10)\b", resp)
    if m and 1 <= int(m.group(1)) <= n:
        return int(m.group(1)) - 1
    return None


PICK_PROMPT = """The piece of writing below was produced from a prompt that included \
exactly one of the numbered requests. Read it and decide which request was given.

TEXT:
{text}

REQUESTS:
{cands}

Answer with the number only."""

FAB_PROMPT = """The piece of writing below may have been produced from a prompt that \
included one of the numbered requests, or from a plain prompt with none of them. Read it \
and decide.

TEXT:
{text}

OPTIONS:
{cands}

Answer with the number only."""


def reconstruct() -> list[dict]:
    """Rebuild every item's true specs from the generator's deterministic seeds and verify
    against the manifest's recorded prompt word count. Abort on any mismatch."""
    man = json.loads((LADDER / "manifest.json").read_text(encoding="utf-8"))
    items = []
    for it in man["items"]:
        rung, i = it["rung"], int(it["id"].split("_")[1])
        rng = random.Random(70000 + rung * 1000 + i)
        prompt = build(it["topic"], rung, rng)
        if len(prompt.split()) != it["prompt_words"]:
            print(f"JOIN CHECK FAILED on {it['id']}: rebuilt prompt {len(prompt.split())}w "
                  f"vs recorded {it['prompt_words']}w — specs NOT trustworthy, aborting")
            sys.exit(1)
        rng2 = random.Random(70000 + rung * 1000 + i)
        specs = [] if rung == 0 else rng2.sample(SPECS, rung)
        text = (LADDER / f"{it['id']}.txt").read_text(encoding="utf-8")
        items.append({**it, "specs": specs, "text": text})
    print(f"join check clean on {len(items)} items")
    return items


def build_events(items):
    import numpy as np
    rng = np.random.default_rng(SEED)
    rec_events, fab_events = [], []
    for it in items:
        if it["rung"] == 0:
            pool = [s for s in SPECS]
            cands = [pool[j] for j in rng.choice(len(pool), size=K, replace=False)]
            fab_events.append({"item": it["id"], "rung": 0,
                               "cands": cands + [NONE_OPT], "text": it["text"]})
            continue
        for truth in it["specs"]:
            decoys_pool = [s for s in SPECS if s not in it["specs"]]
            decoys = [decoys_pool[j] for j in
                      rng.choice(len(decoys_pool), size=K - 1, replace=False)]
            cands = decoys + [truth]
            cands = [cands[j] for j in rng.permutation(len(cands))]
            rec_events.append({"item": it["id"], "rung": it["rung"], "truth": truth,
                               "cands": cands, "truth_idx": cands.index(truth),
                               "text": it["text"]})
    return rec_events, fab_events


def run_arm(name, events, prompt_tpl, with_text=True):
    part = OUT / f"{name}_partial.jsonl"
    done = {}
    if part.exists():
        done = {json.loads(x)["i"]: json.loads(x)
                for x in part.read_text(encoding="utf-8").splitlines()}
    with part.open("a", encoding="utf-8", newline="\n") as fh:
        for i, e in enumerate(events):
            if i in done:
                continue
            cands = "\n".join(f"{j + 1}. {c}" for j, c in enumerate(e["cands"]))
            p = (prompt_tpl.format(text=e["text"][:6000], cands=cands) if with_text
                 else PICK_PROMPT.format(text="(no text shown)", cands=cands))
            resp = call_reader(p)
            pick = parse_pick(resp, len(e["cands"]))
            row = {"i": i, **{k: e[k] for k in e if k not in ("cands", "text")},
                   "n_cands": len(e["cands"]), "pick": pick}
            fh.write(json.dumps(row) + "\n")
            fh.flush()
            done[i] = row
    return [done[i] for i in sorted(done)]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--arm", choices=["gpu", "summarize"], required=True)
    args = ap.parse_args()
    items = reconstruct()
    rec_events, fab_events = build_events(items)
    OUT.mkdir(parents=True, exist_ok=True)

    if args.arm == "gpu":
        from soundingline.gpulock import acquire_gpu_lock              # noqa: PLC0415
        acquire_gpu_lock("g94_taramsa")               # once per invocation (LESSONS §5)
        rec = run_arm("recovery", rec_events, PICK_PROMPT)
        fab = run_arm("fabrication", fab_events, FAB_PROMPT)
        blind = run_arm("blind", rec_events, PICK_PROMPT, with_text=False)
        for nm, rows, exp in (("recovery", rec, len(rec_events)),
                              ("fabrication", fab, len(fab_events)),
                              ("blind", blind, len(rec_events))):
            if len(rows) < exp:
                print(f"INCOMPLETE {nm}: {len(rows)}/{exp}")
                sys.exit(1)
        (OUT / "gpu_done.json").write_text(json.dumps(
            {"recovery": len(rec), "fabrication": len(fab), "blind": len(blind)}),
            encoding="utf-8", newline="\n")
        return

    # summarize (CPU): echo bar + per-rung tables, everything on disk
    rows = lambda n: [json.loads(x) for x in                            # noqa: E731
                      (OUT / f"{n}_partial.jsonl").read_text(encoding="utf-8").splitlines()]
    rec, fab, blind = rows("recovery"), rows("fabrication"), rows("blind")
    texts = {it["id"]: it["text"] for it in items}
    echo = []
    for e in rec_events:
        tw = content_words(texts[e["item"]])
        scores = [len(content_words(c) & tw) / max(len(content_words(c)), 1)
                  for c in e["cands"]]
        echo.append({"rung": e["rung"], "hit": scores.index(max(scores)) == e["truth_idx"]})

    def acc(rows_, key=None, val=None):
        sel = [r for r in rows_ if r["pick"] is not None
               and (key is None or r[key] == val)]
        hit = sum(1 for r in sel if r["pick"] == r["truth_idx"])
        return {"n": len(sel), "accuracy": round(hit / max(len(sel), 1), 4)}

    fab_ok = [r for r in fab if r["pick"] is not None]
    n_fab = sum(1 for r in fab_ok if r["pick"] != K)      # index K is the none option
    summary = {
        "prereg": "runner docstring DESIGN CHECK (exploratory; no verdict bands)",
        "seed": SEED, "k": K, "model": MODEL, "decoding": DECODING,
        "join_check": "clean (prompt word counts reproduce for all 50 items)",
        "fabrication": {"n": len(fab_ok), "rate": round(n_fab / max(len(fab_ok), 1), 4),
                        "note": "share of rung-0 items where the reader asserted a spec "
                                "instead of the none option; the Taramsa number"},
        "recovery_overall": acc(rec),
        "recovery_by_rung": {str(r): acc(rec, "rung", r) for r in (1, 3, 6, 10)},
        "blind_overall": acc(blind),
        "blind_by_rung": {str(r): acc(blind, "rung", r) for r in (1, 3, 6, 10)},
        "echo_bar_overall": {"n": len(echo),
                             "accuracy": round(sum(1 for e in echo if e["hit"])
                                               / max(len(echo), 1), 4)},
        "echo_bar_by_rung": {str(r): round(
            sum(1 for e in echo if e["rung"] == r and e["hit"])
            / max(sum(1 for e in echo if e["rung"] == r), 1), 4) for r in (1, 3, 6, 10)},
    }
    (OUT / "taramsa.json").write_text(json.dumps(summary, indent=1),
                                      encoding="utf-8", newline="\n")
    print(json.dumps(summary, indent=1))


if __name__ == "__main__":
    main()
