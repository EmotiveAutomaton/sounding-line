"""The sign-funnel, step one: register-matched machine long-form fiction, two generators.

L90 found the sign of the positional polish trend separating human from machine long-form,
but the machine corpus there is specification-stacked essays, not register-matched prose. The
funnel's first demand is machine FICTION against the books corpus: same register family, two
different generator families (LESSONS: the shared-representation warning), so a rise that
survives is a provenance fact and not a register or family artifact.

Writes corpora/machine_fiction_{qwen,ds}/piece_NN.txt (~1,100+ words each), checkpointed so a
kill loses nothing. Reasoning-model output has its think-blocks stripped.
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

OLLAMA = "http://127.0.0.1:11434/api/generate"

PREMISES = [
    "a lighthouse keeper who discovers the lamp has been guiding something inland",
    "two sisters dividing their late mother's house room by room",
    "a court scribe who begins editing the king's speeches",
    "a retired surgeon teaching his granddaughter to mend nets",
    "a cartographer mapping a coastline that will not stay still",
    "a landlady who reads her tenants' discarded letters",
    "an apprentice bellfounder casting his master's funeral bell",
    "a botanist returning to a glasshouse abandoned in the war",
    "a ferryman on the last week before the bridge opens",
    "a portrait painter whose sitter keeps changing the story of her life",
    "a night watchman in a museum of instruments nobody plays",
    "a schoolteacher rewriting the town's centenary pageant",
    "a beekeeper moving hives ahead of the motorway works",
    "a translator meeting the author she has translated for twenty years",
    "an organist learning the parish is to be deconsecrated",
]

PROMPT = ("Write a chapter of literary fiction, roughly 1,200 words, third person, about "
          "{premise}. Prose only, no headings, no lists. Write it in full.")


def gen(model: str, premise: str, seed: int) -> str | None:
    req = urllib.request.Request(OLLAMA, data=json.dumps(
        {"model": model, "prompt": PROMPT.format(premise=premise), "stream": False,
         "think": False,
         "options": {"temperature": 0.9, "seed": seed, "num_predict": 2400}}).encode(),
        headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=900) as r:
            txt = json.loads(r.read()).get("response", "")
    except Exception:                                                  # noqa: BLE001
        return None
    txt = re.sub(r"<think>.*?</think>", "", txt, flags=re.S).strip()
    return txt if len(txt.split()) >= 700 else None


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--models", default="qwen3.5:9b=machine_fiction_qwen,"
                                        "deepseek-r1:7b=machine_fiction_ds")
    args = ap.parse_args()

    from soundingline.gpulock import acquire_gpu_lock                 # noqa: PLC0415
    acquire_gpu_lock("gen_fiction")

    manifest = []
    for spec in args.models.split(","):
        model, dirname = spec.split("=")
        out_dir = REPO / "corpora" / dirname
        out_dir.mkdir(parents=True, exist_ok=True)
        for i, premise in enumerate(PREMISES):
            p = out_dir / f"piece_{i:02d}.txt"
            if p.exists():
                continue
            txt = gen(model, premise, seed=8000 + i)
            if txt is None:
                txt = gen(model, premise, seed=8500 + i)
            if txt is None:
                print(f"  {model} piece {i}: failed twice, skipped", flush=True)
                continue
            p.write_text(txt, encoding="utf-8", newline="\n")
            manifest.append({"model": model, "piece": i, "words": len(txt.split())})
            print(f"  {model} piece {i}: {len(txt.split())} words", flush=True)
    out = REPO / "corpora" / "machine_fiction_manifest.json"
    out.write_text(json.dumps(manifest, indent=1), encoding="utf-8", newline="\n")
    print(f"wrote {out.relative_to(REPO)} ({len(manifest)} new pieces)")


if __name__ == "__main__":
    main()
