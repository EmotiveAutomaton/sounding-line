"""G131 — the factorial choice-structure benchmark, generation arm (the construct test's corpus).

The program's dose-responsive quantities have only ever seen "dose" as instruction count to one
generator; G131 crosses the constructs so recovery can be tested against WHAT KIND of choice was
planted, not just how many. Axes, per the TODO's method detail:

    TARGET       surface (reader-directed: style, address, cadence) vs problem-directed
                 (content decisions: comparisons, concessions, grounded examples)
    AMOUNT       0 / 3 / 8 instructions
    COUPLING     independent (instructions unrelated) vs interlocked (each references the
                 previous one's product, so the choices depend on each other)
    REALIZATION  every artifact records its exact instruction set at generation time; the
                 recovery study then asks whether a bounded reader identifies WHICH
                 instructions were active against matched decoys from the same pool, which is
                 the event-level question with constructs separated

Design controls: same 10 topics in every cell (the G153 argument set), same register, length
banded by rejection sampling (300-600 words, 4 tries), both local families, instruction sets
drawn deterministically per cell so every family sees identical instructions. Ground truth is
the record, not an annotation. Cells: (2 targets x {3,8} x 2 couplings) + zero-control = 9 per
topic per family = 180 artifacts.

Output: corpora/g131_factorial/{family}/{artifact_id}.json, checkpointed; manifest withheld
under 90% yield (the L133-era lessons all apply: retry on 500s, explicit decoding, one shared
filename helper).
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OLLAMA = "http://127.0.0.1:11434/api/generate"

FAMILIES = {"qwen": "qwen3.5:9b", "llama": "llama3.1:8b"}
DECODING = {"temperature": 0.8, "top_p": 0.95, "top_k": 40,
            "repeat_penalty": 1.1, "num_predict": 1200}
SEED0 = 13100
BAND = (300, 600)
TRIES = 4

TOPICS = ["whether cities should ban private cars from their centers",
          "whether schools should teach handwriting",
          "whether professional sports teams should be publicly owned",
          "whether social media accounts should require age verification",
          "whether space exploration deserves public funding",
          "whether museums should return colonial-era artifacts",
          "whether tipping should be abolished",
          "whether voting should be compulsory",
          "whether remote work should be a legal right",
          "whether zoos should exist"]

SURFACE = [
    "address the reader directly as 'you' at least twice",
    "open with a one-sentence paragraph",
    "use no sentence longer than twenty words",
    "include exactly one rhetorical question",
    "end every paragraph with a short punchy sentence",
    "use a numbered list for exactly one group of points",
    "include one deliberate sentence fragment for emphasis",
    "repeat one chosen phrase at the start of two different paragraphs",
    "close with a single-sentence call to action",
    "use an em-dash-free, semicolon-free punctuation style",
    "include exactly one parenthetical aside",
    "write the final paragraph in second person throughout",
]
PROBLEM = [
    "compare exactly two named alternatives before taking a side",
    "concede one specific counterargument and rebut it",
    "ground one claim in a concrete named example",
    "state one measurable criterion your position could be judged by",
    "distinguish a short-term effect from a long-term effect",
    "identify the strongest stakeholder against your position and address them",
    "commit to one explicit tradeoff your position accepts",
    "derive one implication your position has for a neighboring policy area",
    "state one condition under which you would change your mind",
    "separate an empirical claim from a value claim explicitly",
    "rank two of your own reasons and justify the ranking",
    "identify one piece of missing evidence that would settle the question",
]


def interlock(base: list[str]) -> list[str]:
    """Chain each instruction onto the previous one's product."""
    out = [base[0]]
    for i, ins in enumerate(base[1:], start=2):
        out.append(f"{ins}, and it must build directly on what instruction {i - 1} produced")
    return out


def cells():
    for target, pool in (("surface", SURFACE), ("problem", PROBLEM)):
        for amount in (3, 8):
            for coupling in ("independent", "interlocked"):
                yield target, amount, coupling, pool
    yield "none", 0, "none", []


def call(model: str, prompt: str, seed: int) -> str | None:
    req = urllib.request.Request(OLLAMA, data=json.dumps(
        {"model": model, "prompt": prompt, "stream": False, "think": False,
         "options": {**DECODING, "seed": seed}}).encode(),
        headers={"Content-Type": "application/json"})
    for attempt in range(6):
        try:
            with urllib.request.urlopen(req, timeout=900) as r:
                resp = json.loads(r.read()).get("response", "")
            return re.sub(r"<think>.*?</think>", "", resp, flags=re.DOTALL).strip()
        except Exception as e:                                        # noqa: BLE001
            print(f"  call failed (attempt {attempt + 1}): {e}")
            time.sleep(20 * (attempt + 1))
    return None


def main() -> None:
    sys.path.insert(0, str(REPO))
    from soundingline.gpulock import acquire_gpu_lock                 # noqa: PLC0415
    import numpy as np                                                # noqa: PLC0415

    ap = argparse.ArgumentParser()
    ap.add_argument("--family", required=True, choices=sorted(FAMILIES))
    args = ap.parse_args()
    acquire_gpu_lock(f"g131_gen_{args.family}")
    model = FAMILIES[args.family]
    outdir = REPO / "corpora" / "g131_factorial" / args.family
    outdir.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(SEED0)                # instruction draws: identical per family
    n_expected = 0

    for ti, topic in enumerate(TOPICS):
        for target, amount, coupling, pool in cells():
            n_expected += 1
            aid = f"{target}_{amount}_{coupling}_{ti:02d}"
            dest = outdir / f"{aid}.json"
            draw = (sorted(rng.choice(len(pool), size=amount, replace=False).tolist())
                    if amount else [])
            instructions = [pool[i] for i in draw]
            if coupling == "interlocked" and len(instructions) > 1:
                instructions = interlock(instructions)
            if dest.exists():
                continue
            body = ("Write a 400-word argumentative essay taking a clear position on: "
                    f"{topic}.")
            if instructions:
                body += "\nFollow ALL of these instructions:\n" + "\n".join(
                    f"{i + 1}. {s}" for i, s in enumerate(instructions))
            text = None
            for t in range(TRIES):
                cand = call(model, body, seed=SEED0 + ti * 100 + hash(aid) % 50 + t)
                if cand and BAND[0] <= len(cand.split()) <= BAND[1]:
                    text = cand
                    break
                text = text or cand                    # keep best-effort if band never hits
            if not text:
                continue
            rec = {"artifact_id": aid, "topic": topic, "target": target,
                   "amount": amount, "coupling": coupling,
                   "instructions": instructions, "instruction_pool": target,
                   "family": args.family, "model_tag": model,
                   "decoding": {**DECODING, "seed_base": SEED0},
                   "in_band": BAND[0] <= len(text.split()) <= BAND[1],
                   "n_words": len(text.split()), "text": text,
                   "generated_at": time.strftime("%Y-%m-%d %H:%M:%S")}
            dest.write_text(json.dumps(rec, indent=1), encoding="utf-8", newline="\n")
            print(f"{aid}: {len(text.split())}w in_band={rec['in_band']}")

    n_disk = len([p for p in outdir.glob("*.json") if p.name != "manifest.json"])
    if n_disk < int(0.9 * n_expected):
        print(f"INCOMPLETE: {n_disk}/{n_expected}; manifest withheld, stage retries")
        sys.exit(1)
    (outdir / "manifest.json").write_text(json.dumps(
        {"family": args.family, "n_on_disk": n_disk, "n_expected": n_expected,
         "cells": "2 targets x (3,8) x 2 couplings + zero control, 10 topics",
         "band": BAND}, indent=1), encoding="utf-8", newline="\n")
    print(f"done: {n_disk}/{n_expected} artifacts for {args.family}")


if __name__ == "__main__":
    main()
