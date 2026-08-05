"""Rung -1 — the ceiling control, and a shuffle-granularity sweep to replace the binary one.

── WHY THIS EXISTS ───────────────────────────────────────────────────────────────────────────

The curator challenged the shuffle test on 2026-08-05:

    I actually don't think the shuffle test is going to be correct... shuffling inherently is a
    whole bunch of decisions. But obviously randomness can't be the thing that we're detecting,
    because randomness is kind of the part of the problem.

His framing does not hold literally — a seeded permutation is maximum-entropy and goal-free, so it
is decision-FREE rather than decision-dense. **But the version one step over is a real threat to
every measure here:**

    A reader cannot tell "many decisions" from "unpredictable" without a model of what the
    decisions were FOR. Any measure whose implicit definition of intent is departure-from-
    expectation will score NOISE as maximally intentional.

That is N28 with the sign flipped. N28 asks whether a measure MOVES where there is nothing to
measure. This asks whether it PEAKS there — which the no-maker corpus can never catch, because
no-maker artifacts are quiet, not chaotic.

── TEST 1 · RUNG -1, PRE-REGISTERED BEFORE THE RUN ───────────────────────────────────────────

Word-shuffled ladder text is scored as a sixth rung sitting BELOW rung 0. Direction is taken from
the measure's own sign against rung, so nothing here assumes which way a measure should point.

    PASS    shuffled sits at or beyond the rung-0 end     it reads noise as intent-free
    DEAD    shuffled sits beyond the rung-10 end          it is reading unpredictability
    WEAK    shuffled lands inside the rung range          ambiguous; report position as a fraction

**The ablation is reused as a CALIBRATION POINT rather than as a subtraction**, which
`docs/theory/CONTROLS.md` §3 argues is the only role it is actually valid for.

── TEST 2 · THE GRANULARITY SWEEP ────────────────────────────────────────────────────────────

Full word-shuffling is the most violent possible perturbation and it throws a model-internal
measure out of distribution entirely (both arms of the layer-ratio comparison moved UP ~14%). Ask
the question at granularities that stay closer to real text:

    paragraph   destroys argument order          keeps everything else
    sentence    destroys discourse flow          keeps grammar, local coherence, register
    phrase      destroys syntax                  keeps local co-occurrence
    word        destroys everything              keeps the multiset only

A curve instead of a verdict: the granularity at which a measure lives. One extra pass.

**Nothing here can revive a dead measure.** Six of the ten deaths were lexical statistics where the
shuffle test is exact. This changes what we are entitled to conclude about the model-internal ones.
"""

from __future__ import annotations

import argparse
import json
import random
import re
import statistics
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

RESULTS = REPO / "results" / "rung_minus1"
LADDER = REPO / "corpora" / "ladder"


# ── the four granularities ────────────────────────────────────────────────────────────────────

def shuffle_words(t: str, rng: random.Random) -> str:
    w = t.split()
    rng.shuffle(w)
    return " ".join(w)


def shuffle_phrases(t: str, rng: random.Random, n: int = 5) -> str:
    w = t.split()
    chunks = [w[i:i + n] for i in range(0, len(w), n)]
    rng.shuffle(chunks)
    return " ".join(x for c in chunks for x in c)


def shuffle_sentences(t: str, rng: random.Random) -> str:
    s = [x for x in re.split(r"(?<=[.!?])\s+", t) if x.strip()]
    rng.shuffle(s)
    return " ".join(s)


def shuffle_paragraphs(t: str, rng: random.Random) -> str:
    p = [x for x in t.split("\n\n") if x.strip()]
    if len(p) < 2:                       # no paragraph structure to destroy
        return t
    rng.shuffle(p)
    return "\n\n".join(p)


GRAINS = {"paragraph": shuffle_paragraphs, "sentence": shuffle_sentences,
          "phrase": shuffle_phrases, "word": shuffle_words}


def load_ladder() -> list[dict]:
    man = json.loads((LADDER / "manifest.json").read_text(encoding="utf-8"))
    out = []
    for it in man["items"]:
        p = LADDER / f"{it['id']}.txt"
        if p.exists():
            out.append({"id": it["id"], "rung": it["rung"],
                        "text": p.read_text(encoding="utf-8")})
    return out


def adjudicate(by_rung: dict[int, float], shuffled: float) -> dict:
    """Where does noise sit, relative to the rungs, in the measure's own direction?"""
    rungs = sorted(by_rung)
    lo, hi = by_rung[rungs[0]], by_rung[rungs[-1]]      # rung 0 end, rung 10 end
    span = hi - lo
    if abs(span) < 1e-12:
        return {"verdict": "FLAT", "position": None,
               "note": "measure does not separate the rungs at all; rung -1 is not askable"}
    # position 0.0 == the rung-0 (least intent) end, 1.0 == the rung-10 (most intent) end
    pos = (shuffled - lo) / span
    verdict = ("PASS" if pos <= 0.0 else
               "DEAD" if pos >= 1.0 else
               "WEAK")
    return {"verdict": verdict, "position": pos, "rung0_end": lo, "rung10_end": hi}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--device", default="cuda")
    ap.add_argument("--model", default=None)
    ap.add_argument("--seed", type=int, default=31)
    ap.add_argument("--skip-gpu", action="store_true",
                    help="lexical measures only; no reader is loaded")
    args = ap.parse_args()

    rows = load_ladder()
    rungs = sorted({r["rung"] for r in rows})
    print(f"ladder: {len(rows)} artifacts, rungs {rungs}\n", flush=True)

    from scipy import stats                                             # noqa: PLC0415
    from soundingline.measures.leakage import profile                   # noqa: PLC0415

    def ttr(t: str) -> float:
        w = t.lower().split()
        return len(set(w)) / max(len(w), 1)

    measures = {
        "type_token_ratio": ttr,
        "i_rate": lambda t: profile(t).rates["i"],
        "exclusive_rate": lambda t: profile(t).rates["exclusive"],
        "tentative_rate": lambda t: profile(t).rates["tentative"],
        "insight_rate": lambda t: profile(t).rates["insight"],
        "causal_rate": lambda t: profile(t).rates["causal"],
    }

    # ── the measure that actually matters here, and it needs the GPU ──────────────────────────
    if not args.skip_gpu:
        from soundingline.probe.activations import (DEFAULT_MODEL,      # noqa: PLC0415
                                                    Reader, fit_directions)
        from runners.run_b import split                                 # noqa: PLC0415
        from runners.run_layer_ratio import ratio_for                   # noqa: PLC0415

        name = args.model or DEFAULT_MODEL
        print(f"loading {name} on {args.device} ...", flush=True)
        reader = Reader(name, device=args.device)
        fit, _ = split()
        print("fitting affect directions ...", flush=True)
        dirs = fit_directions(reader, fit)
        print(f"  {len(dirs.concepts)} concepts x {dirs.n_layers} layers\n", flush=True)
        measures["layer_ratio"] = lambda t: ratio_for(reader, dirs, t)

    out: dict = {"n": len(rows), "rungs": rungs, "seed": args.seed, "measures": {}}

    for mname, f in measures.items():
        print(f"-- {mname}", flush=True)
        intact = {r["id"]: f(r["text"]) for r in rows}
        by_rung = {g: statistics.fmean(intact[r["id"]] for r in rows if r["rung"] == g)
                   for g in rungs}
        rho, pv = stats.spearmanr([r["rung"] for r in rows],
                                  [intact[r["id"]] for r in rows])
        print("   rungs: " + "  ".join(f"{g}={by_rung[g]:.4f}" for g in rungs))
        print(f"   rho vs rung = {rho:+.3f}  p={pv:.4f}")

        entry = {"rho_vs_rung": float(rho), "p": float(pv),
                 "by_rung": {str(g): by_rung[g] for g in rungs}, "grains": {}}

        for gname, gfun in GRAINS.items():
            rng = random.Random(args.seed)
            vals = [f(gfun(r["text"], rng)) for r in rows]
            mean = statistics.fmean(vals)
            adj = adjudicate(by_rung, mean)
            entry["grains"][gname] = {"mean": mean, **adj}
            pos = adj.get("position")
            postxt = "n/a" if pos is None else f"{pos:+.2f}"
            flag = {"PASS": "ok", "DEAD": ">>> READS NOISE AS INTENT",
                    "WEAK": "inside the rung range", "FLAT": "-"}[adj["verdict"]]
            print(f"   {gname:<10} {mean:.4f}   position {postxt:>6}   "
                  f"{adj['verdict']:<5} {flag}")

        # the sweep's own summary: does the effect need order, and at what scale?
        entry["needs_order_at"] = [g for g, v in entry["grains"].items()
                                   if v.get("position") is not None
                                   and abs(v["position"]) > 0.5]
        out["measures"][mname] = entry
        print(flush=True)

    RESULTS.mkdir(parents=True, exist_ok=True)
    (RESULTS / "rung_minus1.json").write_text(
        json.dumps(out, indent=2, default=float), encoding="utf-8")
    print(f"wrote {(RESULTS / 'rung_minus1.json').relative_to(REPO)}")

    dead = [m for m, v in out["measures"].items()
            if any(g["verdict"] == "DEAD" for g in v["grains"].values())]
    print("\n" + "=" * 72)
    if dead:
        print(f">>> READS NOISE AS INTENT, at some granularity: {', '.join(dead)}")
        print("    These score word salad at or beyond the most-specified rung. Whatever their")
        print("    rho against rung was, they are measuring unpredictability.")
    else:
        print(">>> No measure places noise above the ladder. The ceiling control is clean.")
    print("=" * 72)


if __name__ == "__main__":
    main()
