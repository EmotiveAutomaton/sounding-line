"""Seeded idea generation with forced diversity — the anti-hivemind loop.

── THE PROBLEM THIS EXISTS FOR ───────────────────────────────────────────────────────────────

The curator, repeatedly: **"you tend to fall into paths that people have explored already."**

That is not a hunch about me, it is a measured property. The idea-generation literature calls it the
**Artificial Hivemind** effect: intramodel repetition, intermodel homogeneity, and *"conceptual
narrowness, clustering outputs around seed literature rather than introducing genuinely new research
paths."* It is exactly what produced ten near-identical lexical measures here.

His proposed fix, and it is the right one:

    One of the solutions is literally to write theory documents and then have you over-index on
    them.

So the seed is **his** theory rather than the field's, and the diversity pressure is structural
rather than a request. Asking a model for "ten diverse ideas" returns ten variations on one idea.
Asking it for **one idea per cell of a grid it cannot collapse** does not.

── THE GRID ──────────────────────────────────────────────────────────────────────────────────

Every candidate is generated at the intersection of a **seed claim** (from
`docs/theory/CURATOR_GUESSES.md`) and a **structural lens**. The lenses are not topics — they are
*shapes a measure can have*, drawn from this project's own failure modes:

    variance        the quantity is a WITHIN-ARTIFACT VARIANCE, not a mean       <- B1, never tried
    trajectory      it is an ordered series, not a scalar                        <- B3, never tried
    relation        it needs two artifacts, or an artifact and a domain          <- A2
    reader          it is read from the READER's internals, not the artifact     <- the only survivors
    inversion       it is a RATIO between two measures that should disagree      <- C2
    absence         it is about what is NOT there
    contrast        it needs a second work by the same maker                     <- G-2's design

Seven lenses x N seeds, one idea per cell. **The grid is the diversity mechanism**; nothing is asked
to "be creative".

── WHAT IT WILL NOT DO ───────────────────────────────────────────────────────────────────────

It cannot judge. Output is candidates for the curator and the control battery, and every candidate
must still pass length, echo, construction, transfer and rung -1 before it means anything. It is also
told what has already died, because regenerating `scale_gain` for the eleventh time is the specific
failure being designed against.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

OUT = REPO / "results" / "ideas"

LENSES = {
    "variance": "The quantity is a WITHIN-ARTIFACT VARIANCE across windows, not a mean. "
                "The curator's primary detector is the *variation* of the veneer, and not one "
                "measure in this project has ever kept a within-artifact spread.",
    "trajectory": "The quantity is an ORDERED SERIES across the artifact, not a scalar. "
                  "Confidence in a maker moves while reading; the trajectory carries what the "
                  "endpoint does not.",
    "relation": "The quantity is a RELATION requiring two things — an artifact and a domain, or a "
                "maker and a subject — not a property of one artifact. Depth is defined as a "
                "property of the writer WITH RESPECT TO the domain.",
    "reader": "The quantity is read from the READER's internal state while reading, not computed "
              "from the text. Every artifact-side measure in this project has died; both survivors "
              "are reader-side.",
    "inversion": "The quantity is a RATIO or DISAGREEMENT between two measures that should track "
                 "together and do not. Dense surface over thin depth is the predicted inversion.",
    "absence": "The quantity is about what is NOT in the artifact — the option not taken, the "
               "objection not raised, the thing a maker would have said and didn't.",
    "contrast": "The quantity requires a SECOND WORK BY THE SAME MAKER, so maker identity is "
                "controlled by construction. This is the design of the only within-human positive "
                "the project has (2.05x).",
}

SYSTEM = (
    "You propose concrete, runnable measurements for a research instrument. "
    "You are not writing prose and not hedging. For each request you return exactly one candidate. "
    "It must be computable from the stated inputs by a short Python function or a probe prompt, and "
    "it must be falsifiable. Never propose something on the DEAD list. Never propose a measure whose "
    "value is determined by the multiset of words alone — those are already ruled out."
)

TEMPLATE = """SEED CLAIM (from the project's own theory, treat as given, do not re-litigate):
{seed}

STRUCTURAL LENS — the candidate MUST have this shape:
{lens}

ALREADY DEAD, do not propose these or near-variants:
{dead}

AVAILABLE INPUTS:
- 342 off-the-shelf linguistic features per text (LFTK, BiberPlus, TextDescriptives)
- activations from a local reading model at any layer, and fitted affect directions
- a 5-rung ladder of machine text where specified intent is the only systematic variable
- 34 public-domain books by 10 authors, several works each
- 51 human web artifacts, 36 no-maker artifacts
- 11 artifacts read aloud by one human with recorded judgements

Return JSON only:
{{"name": "<short_snake_case>",
  "measures": "<one sentence: what quantity, concretely>",
  "computation": "<2-3 sentences: exactly how, from which input>",
  "prediction": "<what it does if the seed claim is true>",
  "falsifier": "<what result would kill it>",
  "why_not_already_dead": "<one sentence: why this is not a near-variant of the dead list>"}}"""

DEAD = ("decision density / scale_gain (it was word count, then type-token ratio); "
        "raw function-word rates (bag-of-words); purpose_breadth (tracks difficulty); "
        "the low/high layer affect ratio on human-vs-machine (register); "
        "causal connective rate (measures explicitness, inverts on humans); "
        "reader displacement from baseline (null); count of recovered decisions (undefined "
        "denominator); any whole-document mean of a lexical statistic")


def load_seeds(path: Path, limit: int | None = None) -> list[dict]:
    """Pull the curator's claims out of CURATOR_GUESSES.md by its own heading convention."""
    txt = path.read_text(encoding="utf-8")
    seeds = []
    for m in re.finditer(r"^### ((?:[A-D]\d+) · .+?) — \*\*(.+?)\*\*$(.*?)(?=^### |\Z)",
                         txt, re.M | re.S):
        title, status, body = m.group(1), m.group(2), m.group(3)
        quote = re.findall(r"^> (.+)$", body, re.M)
        seeds.append({"id": title.split(" · ")[0], "title": title, "status": status,
                      "claim": " ".join(quote)[:900] or body.strip()[:900]})
    # the point is the OPEN ones; a settled claim does not need new instruments
    seeds = [s for s in seeds if "REFRAMED" not in s["status"] or "PARTLY" in s["status"]]
    return seeds[:limit] if limit else seeds


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--arm", default="local")
    ap.add_argument("--seeds", type=int, default=None, help="cap number of seed claims")
    ap.add_argument("--lenses", default=None, help="comma-separated subset")
    ap.add_argument("--dry-run", action="store_true", help="print the grid, generate nothing")
    args = ap.parse_args()

    from soundingline.probe.client import make_client                  # noqa: PLC0415

    seeds = load_seeds(REPO / "docs" / "theory" / "CURATOR_GUESSES.md", args.seeds)
    lenses = ({k: LENSES[k] for k in args.lenses.split(",")} if args.lenses else LENSES)
    print(f"{len(seeds)} seed claims x {len(lenses)} lenses = {len(seeds) * len(lenses)} cells\n")
    for s in seeds:
        print(f"  {s['id']:<4} {s['status']:<16} {s['title'][:60]}")
    if args.dry_run:
        return

    OUT.mkdir(parents=True, exist_ok=True)
    ideas, n = [], 0
    for s in seeds:
        for lname, ldesc in lenses.items():
            n += 1
            prompt = TEMPLATE.format(seed=f"[{s['id']}] {s['claim']}", lens=ldesc, dead=DEAD)
            c = make_client(args.arm, seed=4000 + n)
            try:
                raw = c.read_text(SYSTEM, prompt)
            except Exception as e:                                     # noqa: BLE001
                print(f"  {s['id']}/{lname}: {type(e).__name__}", flush=True)
                continue
            m = re.search(r"\{.*\}", raw, re.S)
            try:
                idea = json.loads(m.group(0)) if m else None
            except json.JSONDecodeError:
                idea = None
            if not idea:
                print(f"  {s['id']}/{lname}: unparseable", flush=True)
                continue
            idea.update({"seed": s["id"], "lens": lname})
            ideas.append(idea)
            print(f"  {s['id']}/{lname:<11} {idea.get('name', '?')}", flush=True)
            (OUT / "ideas.json").write_text(json.dumps(ideas, indent=2), encoding="utf-8",
                                            newline="\n")

    print(f"\n{len(ideas)} candidates -> results/ideas/ideas.json")
    print("Nothing here is a result. Every candidate still has to clear the control battery.")


if __name__ == "__main__":
    main()
