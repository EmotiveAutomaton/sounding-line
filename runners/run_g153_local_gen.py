"""G153 free path, step 2 — the local-family pilot generation, process-recorded end to end.

Proves the crossed benchmark's generation loop on the two independent local lineages before
any dollar exists (his ruling, STATE standing ruling 7): every artifact carries the full
process record AT GENERATION TIME (model identity, explicit decoding, prompt, lineage), which
is the field the survey showed cannot be retrofitted. Regimes covered here are the fully
automatable ones: R1 thin-prompt direct generation and R3 human-to-model rewrite (sources:
ArgRewrite Draft1 essays, lineage-linked). R2's selection and R4/R5's human halves are human
decision dose by definition and are NEVER simulated by a second model (the survey objection,
adopted into the design).

Decoding is EXPLICIT, never inherited: the local defaults are model-card-supplied and
non-neutral, so every option is set and recorded. One artifact = one JSON record in
corpora/g153_pilot/{family}/, checkpointed, a kill loses nothing.

    python runners/run_g153_local_gen.py --family qwen    (qwen3.5:9b, SEEN)
    python runners/run_g153_local_gen.py --family llama   (llama3.1:8b, HELD OUT)
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
OLLAMA_SHOW = "http://127.0.0.1:11434/api/show"

FAMILIES = {"qwen": "qwen3.5:9b", "llama": "llama3.1:8b"}
DECODING = {"temperature": 0.8, "top_p": 0.95, "top_k": 40,
            "repeat_penalty": 1.1, "num_predict": 1600}
SEED0 = 5300

DOMAINS = {
    "argument": ("Write a ~{n}-word argumentative essay taking a clear position on: {t}. "
                 "Prose only, no headings."),
    "fiction": ("Write a ~{n}-word piece of literary short fiction about: {t}. "
                "Prose only, no headings."),
    "technical": ("Write a ~{n}-word technical explanation, for a general audience, of: {t}. "
                  "Prose only, no headings or lists."),
    "professional": ("Write a ~{n}-word professional workplace message about: {t}. "
                     "Plain prose."),
}
TOPICS = {
    "argument": ["whether cities should ban private cars from their centers",
                 "whether schools should teach handwriting",
                 "whether professional sports teams should be publicly owned",
                 "whether social media accounts should require age verification",
                 "whether space exploration deserves public funding",
                 "whether museums should return colonial-era artifacts",
                 "whether tipping should be abolished",
                 "whether voting should be compulsory",
                 "whether remote work should be a legal right",
                 "whether zoos should exist"],
    "fiction": ["a locksmith who keeps one uncut key",
                "a weather forecaster in a town where she is always wrong",
                "the last week of a village post office",
                "a piano tuner who hears a note nobody played",
                "two strangers repainting the same fence",
                "a night ferry that takes no passengers",
                "an archivist who finds her own handwriting in an old file",
                "a bricklayer building his last wall",
                "a child's map of a city that does not exist yet",
                "a bell that rings a day early"],
    "technical": ["how public-key cryptography works", "why bridges have expansion joints",
                  "how a refrigerator moves heat", "what a database index does",
                  "how vaccines train the immune system", "why the sky is blue",
                  "how noise-cancelling headphones work", "what happens during a compile",
                  "how GPS locates a phone", "why ships float"],
    "professional": ["announcing a change to the meeting schedule",
                     "requesting budget approval for new equipment",
                     "summarizing quarterly results for the team",
                     "onboarding notes for a new colleague",
                     "declining a vendor proposal politely",
                     "escalating a slipped deadline",
                     "documenting a process handover",
                     "proposing a change to the on-call rotation",
                     "thanking a team after a launch",
                     "reporting a minor security incident"],
}
LENGTHS = {"medium": 300, "long": 700}
ESSAYS = REPO / "corpora" / "public" / "argrewrite" / "essays" / "Draft1"
N_REWRITES = 40


def call(model: str, prompt: str, seed: int) -> str | None:
    req = urllib.request.Request(OLLAMA, data=json.dumps(
        {"model": model, "prompt": prompt, "stream": False, "think": False,
         "options": {**DECODING, "seed": seed}}).encode(),
        headers={"Content-Type": "application/json"})
    # transient ollama 500s under VRAM churn: retry with backoff before giving up
    for attempt in range(6):
        try:
            with urllib.request.urlopen(req, timeout=900) as r:
                resp = json.loads(r.read()).get("response", "")
            return re.sub(r"<think>.*?</think>", "", resp, flags=re.DOTALL).strip()
        except Exception as e:                                        # noqa: BLE001
            print(f"  call failed (attempt {attempt + 1}): {e}")
            time.sleep(20 * (attempt + 1))
    return None


def model_identity(model: str) -> dict:
    req = urllib.request.Request(OLLAMA_SHOW, data=json.dumps({"model": model}).encode(),
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            d = json.loads(r.read())
        return {"tag": model, "digest": d.get("modified_at", ""),
                "details": d.get("details", {})}
    except Exception:                                                 # noqa: BLE001
        return {"tag": model}


def main() -> None:
    sys.path.insert(0, str(REPO))
    from soundingline.gpulock import acquire_gpu_lock                 # noqa: PLC0415

    ap = argparse.ArgumentParser()
    ap.add_argument("--family", required=True, choices=sorted(FAMILIES))
    args = ap.parse_args()
    acquire_gpu_lock(f"g153_gen_{args.family}")        # sustained ollama serializes on the card
    model = FAMILIES[args.family]
    outdir = REPO / "corpora" / "g153_pilot" / args.family
    outdir.mkdir(parents=True, exist_ok=True)
    ident = model_identity(model)
    n_written = 0

    def record(aid: str, regime: str, prompt: str, text: str, extra: dict) -> None:
        nonlocal n_written
        rec = {"artifact_id": aid, "regime": regime, "family": args.family,
               "family_exposure": "seen" if args.family == "qwen" else "held_out",
               "generator": {**ident, "decoding": {**DECODING, "seed": extra.pop("seed")},
                             "decoding_schema_version": "g153.v1"},
               "prompt": prompt, "text": text, "n_words": len(text.split()),
               "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
               "binary_label": "positive", "binary_policy_version": "draft-v0.1",
               **extra}
        (outdir / f"{aid}.json").write_text(json.dumps(rec, indent=1),
                                            encoding="utf-8", newline="\n")
        n_written += 1

    # R1: thin-prompt direct generation, 4 domains x 10 topics x 2 lengths
    seed = SEED0
    for dom, tmpl in DOMAINS.items():
        for ti, topic in enumerate(TOPICS[dom]):
            for lname, n in LENGTHS.items():
                seed += 1
                aid = f"r1_{dom}_{ti:02d}_{lname}"
                if (outdir / f"{aid}.json").exists():
                    continue
                prompt = tmpl.format(n=n, t=topic)
                text = call(model, prompt, seed)
                if text and len(text.split()) >= n // 3:
                    record(aid, "direct_generation", prompt, text,
                           {"domain": dom, "topic": topic, "length_bin": lname,
                            "lineage_id": aid, "seed": seed})
                    print(f"{aid}: {len(text.split())}w")

    # R3: human-to-model rewrite over ArgRewrite Draft1 sources (lineage-linked)
    sources = sorted(ESSAYS.glob("*.txt"))[:N_REWRITES]
    for si, src in enumerate(sources):
        seed += 1
        aid = f"r3_rewrite_{si:02d}"
        if (outdir / f"{aid}.json").exists():
            continue
        source_text = src.read_text(encoding="utf-8", errors="replace").strip()[:6000]
        prompt = ("Rewrite the following essay in your own words. Preserve its meaning, "
                  "position, and overall structure, but produce fresh wording throughout.\n\n"
                  + source_text)
        text = call(model, prompt, seed)
        if text and len(text.split()) >= 100:
            record(aid, "human_to_model_rewrite", prompt[:400] + " [...source elided...]",
                   text, {"domain": "argument", "length_bin": "long",
                          "lineage_id": f"argrewrite_d1_{src.stem}",
                          "source_ref": str(src.relative_to(REPO)), "seed": seed})
            print(f"{aid}: {len(text.split())}w <- {src.name}")

    n_expected = len(DOMAINS) * 10 * len(LENGTHS) + N_REWRITES
    n_on_disk = len([p for p in outdir.glob("*.json") if p.name != "manifest.json"])
    if n_on_disk < int(0.9 * n_expected):
        # a transient failure must not satisfy the produces-guard with a thin corpus;
        # exit nonzero so the queue retries and the per-artifact checkpoints fill the gaps
        print(f"INCOMPLETE: {n_on_disk}/{n_expected} artifacts; manifest withheld, stage "
              f"will retry")
        sys.exit(1)
    manifest = {"family": args.family, "model": ident, "n_artifacts_on_disk": n_on_disk,
                "n_expected": n_expected, "n_written_this_pass": n_written,
                "decoding_schema_version": "g153.v1"}
    (outdir / "manifest.json").write_text(json.dumps(manifest, indent=1),
                                          encoding="utf-8", newline="\n")
    print(f"done: {n_on_disk} artifacts on disk for {args.family}")


if __name__ == "__main__":
    main()
