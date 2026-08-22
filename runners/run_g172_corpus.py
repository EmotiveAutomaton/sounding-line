"""G172 corpus generation — four open-weight makers write under assigned entity-order goals,
with realization verified inside the accept loop (the L156 rule: a non-compliant sample costs
one retry, never a corpus).

Card: prereg/g172.py (frozen; every constant imported, nothing redefined here).
Output: corpora/g172/{maker}/art_{t}_{g}_{k}.json, manifest at results/g172/corpus_manifest.json
        ONLY at >= 90 percent cell fill (else nonzero exit, no manifest, stage retries).
GPU; takes the gpu lock once per invocation.
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import torch

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from prereg.g172 import (ATTEMPTS, MAKERS, MAX_NEW_TOKENS, N_GOALS, SEED0,       # noqa: E402
                         TEMPERATURE, TOP_P, TOPICS, TRIALS, YIELD_FLOOR,
                         gen_prompt, goal_entities, realized, short)
from soundingline.gpulock import acquire_gpu_lock, release_gpu_lock              # noqa: E402

CORPUS = REPO / "corpora" / "g172"
OUT = REPO / "results" / "g172"
MANIFEST = OUT / "corpus_manifest.json"

# ── THE ONE PREDECLARED REPAIR (card, YIELD gate) — applied 2026-08-22 after the first
# pass recorded fill 152/256 = 0.594 (qwen25_05b 60/64, qwen25_15b 63/64, pythia_410m
# 11/64, pythia_14b 18/64; the base Pythia makers cannot satisfy four constraints at 16
# attempts). Per the card: redraw the one-shot example and raise attempts to 24 for the
# failing makers; a second failure retires the maker from the matrix, never the bar.
# Existing accepts are kept (dest.exists() resume); only unfilled cells rerun, with fresh
# seeds offset so no first-pass draw repeats.
REPAIR_MAKERS = {"EleutherAI/pythia-410m", "EleutherAI/pythia-1.4b"}
ATTEMPTS_V2 = 24
SEED_OFFSET_V2 = 500000

_EXAMPLE_V2 = (
    "Example task: Write one short informative paragraph about bread baking. The paragraph "
    "must mention yeast first and kneading later, and must not mention crust or oven.\n\n"
    "Example paragraph: Yeast is the starting point of most bread, waking in warm water "
    "before anything else happens. The dough only gains strength once kneading begins, and "
    "a patient baker then lets time do the rest, resting the dough until it doubles in "
    "size and the flavor deepens.\n\n"
)


def gen_prompt_v2(topic_i: int, goal_i: int) -> str:
    topic = TOPICS[topic_i][0]
    a, b, avoid = goal_entities(topic_i, goal_i)
    task = (f"Task: Write one short informative paragraph about {topic}. The paragraph must "
            f"mention {a} first and {b} later, and must not mention {avoid[0]} or {avoid[1]}.")
    return f"{task}\n\n{_EXAMPLE_V2}Now the task again: {task}\n\nParagraph:"


def generate_for_maker(maker: str) -> list[dict]:
    from transformers import AutoModelForCausalLM, AutoTokenizer                 # noqa: PLC0415
    tok = AutoTokenizer.from_pretrained(maker)
    model = AutoModelForCausalLM.from_pretrained(maker, dtype=torch.float16).to("cuda").eval()
    mdir = CORPUS / short(maker)
    mdir.mkdir(parents=True, exist_ok=True)
    rows, mi = [], MAKERS.index(maker)
    repair = maker in REPAIR_MAKERS
    attempts = ATTEMPTS_V2 if repair else ATTEMPTS
    for ti in range(len(TOPICS)):
        for gi in range(N_GOALS):
            for k in range(TRIALS):
                dest = mdir / f"art_{ti}_{gi}_{k}.json"
                if dest.exists():
                    rows.append(json.loads(dest.read_text(encoding="utf-8")))
                    continue
                prompt = gen_prompt_v2(ti, gi) if repair else gen_prompt(ti, gi)
                enc = tok(prompt, return_tensors="pt").to("cuda")
                accepted = None
                for attempt in range(attempts):
                    # v2 strides widen so 24 attempts never collide across trials/goals
                    seed = (SEED0 + SEED_OFFSET_V2 + mi * 100000 + ti * 1000
                            + gi * 128 + k * 32 + attempt) if repair else \
                           (SEED0 + mi * 4096 + ti * 256 + gi * 32 + k * 16 + attempt)
                    torch.manual_seed(seed)
                    with torch.no_grad():
                        out = model.generate(**enc, do_sample=True, temperature=TEMPERATURE,
                                             top_p=TOP_P, max_new_tokens=MAX_NEW_TOKENS,
                                             pad_token_id=tok.eos_token_id)
                    text = tok.decode(out[0][enc.input_ids.shape[1]:],
                                      skip_special_tokens=True)
                    text = text.split("\n\n")[0].strip()
                    if realized(text, ti, gi):
                        accepted = {"maker": maker, "topic_i": ti, "goal_i": gi, "trial": k,
                                    "attempt": attempt, "text": text}
                        break
                if accepted:
                    dest.write_text(json.dumps(accepted, ensure_ascii=False, indent=1),
                                    encoding="utf-8", newline="\n")
                    rows.append(accepted)
                else:
                    print(f"  CELL UNFILLED {short(maker)} t{ti} g{gi} k{k}")
    del model
    torch.cuda.empty_cache()
    return rows


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    acquire_gpu_lock("g172_corpus")
    try:
        all_rows = []
        for maker in MAKERS:
            print(f"== maker {short(maker)} ==")
            all_rows.extend(generate_for_maker(maker))
    finally:
        release_gpu_lock()
    n_target = len(MAKERS) * len(TOPICS) * N_GOALS * TRIALS
    fill = len(all_rows) / n_target
    print(f"fill {len(all_rows)}/{n_target} = {fill:.3f} in {(time.time() - t0) / 60:.0f} min")
    if fill < YIELD_FLOOR:
        print(f"YIELD GATE FAILED (< {YIELD_FLOOR}); manifest withheld, stage will retry")
        return 1
    import transformers                                                          # noqa: PLC0415
    MANIFEST.write_text(json.dumps({
        "prereg": "prereg/g172.py", "seed0": SEED0, "n": len(all_rows),
        "n_target": n_target, "fill": fill,
        "repair": {"applied_to": sorted(short(m) for m in REPAIR_MAKERS),
                   "attempts": ATTEMPTS_V2, "example": "v2",
                   "first_pass_fill": 0.594},
        "versions": {"torch": torch.__version__, "transformers": transformers.__version__},
        "cells": [{k: r[k] for k in ("maker", "topic_i", "goal_i", "trial", "attempt")}
                  for r in all_rows],
    }, indent=1), encoding="utf-8", newline="\n")
    print("manifest written")
    return 0


if __name__ == "__main__":
    sys.exit(main())
