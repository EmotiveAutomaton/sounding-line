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
                         gen_prompt, realized, short)
from soundingline.gpulock import acquire_gpu_lock, release_gpu_lock              # noqa: E402

CORPUS = REPO / "corpora" / "g172"
OUT = REPO / "results" / "g172"
MANIFEST = OUT / "corpus_manifest.json"


def generate_for_maker(maker: str) -> list[dict]:
    from transformers import AutoModelForCausalLM, AutoTokenizer                 # noqa: PLC0415
    tok = AutoTokenizer.from_pretrained(maker)
    model = AutoModelForCausalLM.from_pretrained(maker, dtype=torch.float16).to("cuda").eval()
    mdir = CORPUS / short(maker)
    mdir.mkdir(parents=True, exist_ok=True)
    rows, mi = [], MAKERS.index(maker)
    for ti in range(len(TOPICS)):
        for gi in range(N_GOALS):
            for k in range(TRIALS):
                dest = mdir / f"art_{ti}_{gi}_{k}.json"
                if dest.exists():
                    rows.append(json.loads(dest.read_text(encoding="utf-8")))
                    continue
                prompt = gen_prompt(ti, gi)
                enc = tok(prompt, return_tensors="pt").to("cuda")
                accepted = None
                for attempt in range(ATTEMPTS):
                    torch.manual_seed(SEED0 + mi * 4096 + ti * 256 + gi * 32 + k * 16 + attempt)
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
        "versions": {"torch": torch.__version__, "transformers": transformers.__version__},
        "cells": [{k: r[k] for k in ("maker", "topic_i", "goal_i", "trial", "attempt")}
                  for r in all_rows],
    }, indent=1), encoding="utf-8", newline="\n")
    print("manifest written")
    return 0


if __name__ == "__main__":
    sys.exit(main())
