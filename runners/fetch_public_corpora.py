"""Fetch the three public corpora that address weakness 1 — no controlled human text.

── WHAT AND WHY ──────────────────────────────────────────────────────────────────────────────

Every positive this project has rides on machine-written or public-domain text, and every
uncontrolled human comparison has died. These three are the public data that changes that, ranked by
how well each matches the design we specified ourselves:

    ArgRewrite     paired drafts by the SAME author on the SAME prompt, before and after feedback.
                   Only the intent state differs. Construction-controlled by design, and it is the
                   public version of the dwell corpus we wrote a spec for.
    Wikipedia      articles graded FA / GA / B / C / Start / Stub by human editors. A human ladder,
                   with register held by Wikipedia's own conventions. Severe length confound.
    RAID           6M generations, 11 models, 8 domains. NOT an intent corpus -- external validity
                   for the layer ratio, which so far is one model and one format.

**Deliberately not fetched: HC3 and M4.** They are human-versus-machine sets and that problem is
closed in the literature at near-perfect accuracy. `CLAUDE.md` forbids reinventing it.

── ROBUSTNESS ────────────────────────────────────────────────────────────────────────────────

Dataset identifiers move. Each target lists several candidates and the first that loads wins; a
target that cannot be resolved is recorded as unavailable rather than crashing the run, because this
is queued unattended and one dead identifier must not cost the others.

RAID is large, so only a capped sample is materialised — enough for an external-validity check, not
the whole benchmark.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
OUT = REPO / "corpora" / "public"

TARGETS = [
    {"key": "argrewrite", "cap": 4000, "why": "same author, same prompt, two intent states",
     "candidates": [("ArgRewrite/ArgRewrite_v2", None), ("tafseer-nayeem/argrewrite", None),
                    ("pitt-nlp/ArgRewrite", None)]},
    {"key": "wikipedia_quality", "cap": 6000, "why": "human-graded quality ladder",
     "candidates": [("wikimedia/wikipedia-quality", None), ("nbroad/wikipedia-quality", None),
                    ("Tevatron/wikipedia-quality", None), ("wiki_qa_quality", None)]},
    {"key": "raid", "cap": 8000, "why": "external validity across 11 models and 8 domains",
     "candidates": [("liamdugan/raid", "raid"), ("liamdugan/raid", None),
                    ("RAID-Bench/raid", None)]},
]


def text_field(row: dict) -> str | None:
    for k in ("text", "generation", "content", "article", "body", "draft", "sentence",
              "output", "answer"):
        v = row.get(k)
        if isinstance(v, str) and len(v.split()) > 50:
            return v
    return None


def main() -> None:
    from datasets import load_dataset                                 # noqa: PLC0415

    OUT.mkdir(parents=True, exist_ok=True)
    manifest = {}

    for t in TARGETS:
        key = t["key"]
        dest = OUT / key
        if (dest / "data.jsonl").exists():
            print(f"{key}: already fetched, skipping")
            manifest[key] = {"status": "cached", "why": t["why"]}
            continue
        got = None
        for name, cfg in t["candidates"]:
            try:
                print(f"{key}: trying {name}" + (f" [{cfg}]" if cfg else ""), flush=True)
                ds = load_dataset(name, cfg, split="train", streaming=True) if cfg else \
                    load_dataset(name, split="train", streaming=True)
                got = (name, cfg, ds)
                break
            except Exception as e:                                    # noqa: BLE001
                print(f"   no: {type(e).__name__}: {str(e)[:90]}", flush=True)
        if got is None:
            print(f"{key}: UNAVAILABLE — all candidates failed\n")
            manifest[key] = {"status": "unavailable", "why": t["why"],
                             "tried": [c[0] for c in t["candidates"]]}
            continue

        name, cfg, ds = got
        dest.mkdir(parents=True, exist_ok=True)
        n = 0
        with (dest / "data.jsonl").open("w", encoding="utf-8", newline="\n") as fh:
            for row in ds:
                txt = text_field(row)
                if not txt:
                    continue
                meta = {k: v for k, v in row.items()
                        if isinstance(v, (str, int, float, bool)) and k != "text"
                        and len(str(v)) < 200}
                fh.write(json.dumps({"text": txt, **meta}) + "\n")
                n += 1
                if n >= t["cap"]:
                    break
        print(f"{key}: {n} records from {name}\n", flush=True)
        manifest[key] = {"status": "ok", "source": name, "config": cfg, "n": n,
                         "why": t["why"]}

    (OUT / "MANIFEST.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8",
                                       newline="\n")
    ok = [k for k, v in manifest.items() if v["status"] in ("ok", "cached")]
    print("=" * 70)
    print(f"fetched: {', '.join(ok) if ok else 'none'}")
    bad = [k for k, v in manifest.items() if v["status"] == "unavailable"]
    if bad:
        print(f"UNAVAILABLE (identifiers need checking by hand): {', '.join(bad)}")
    print("=" * 70)


if __name__ == "__main__":
    main()
