"""B′ — does a reading model carry affect structure, and is it layered?

── PRE-REGISTERED BEFORE THE RUN ─────────────────────────────────────────────────────────────

**B′-1, the honesty check, runs first and gates everything.** Directions fitted from contrast
sentences will project onto anything. So they are tested on HELD-OUT sentences of the same eight
concepts, at a mid layer:

    PASS   held-out classification accuracy > 2x chance (chance = 12.5% over eight concepts)
    FAIL   at or below chance -- the directions are noise and no projection means anything

This is the check `separability()` never got. See `results/g/VERDICT.md` for what that cost.

**B′-2, the layer structure.** The curator's reading of the interpretability work: early layers
carry valence/arousal (core affect, the leaked layer), late layers carry conceptual and predictive
structure (constructed emotion, the emblematic layer). If so, `early_late_ratio` should not be 1.0
and should DIFFER between artifacts with different affective content.

    A ratio near 1.0 everywhere means the layers are not doing different jobs, and the whole
    leaked/emblematic-in-the-reader proposal is wrong.

**B′-3, the reason any of this is worth building.** Run on the Gate 3 corpus and ask whether the
activation reading agrees with the FUNCTION-WORD reading of the same artifacts. Two independent
instruments on one text:

    agree      the leaked layer is real and measurable two ways
    disagree   at least one is measuring something else, and the paper's finding -- affect present
               with no surface marker -- says the surface one is the likelier suspect

── SCOPE ─────────────────────────────────────────────────────────────────────────────────────

Small model, CPU, by default. The first question is whether the STRUCTURE exists, not whether a
9B has more of it, and a run that fights a live gate for VRAM costs more than it is worth.
A negative on a 1.5B does not settle it for larger models and must not be reported as if it did.
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

RESULTS = REPO / "results" / "b"

# Eight concepts, family v3's leaked-layer set. Six sentences each: four to fit, two held out.
# Written to express the stance rather than to name it -- a direction fitted on the WORD "rage"
# would be a lexical direction, and the whole point is to catch what is not said.
SETS: dict[str, list[str]] = {
    "seeking": [
        "I pulled the whole thing apart just to see how the middle bit worked.",
        "There is a pattern here and I have been chasing it for three days.",
        "Every answer opened two more questions and I could not stop.",
        "I rebuilt it twice because the second version taught me something.",
        "The interesting part was not the result, it was the thing underneath it.",
        "I kept going because each step showed me something I had not expected.",
    ],
    "rage": [
        "They shipped it anyway, after everything we told them.",
        "Nobody read the document. Nobody ever reads the document.",
        "This is the fourth time and I am done being polite about it.",
        "It was avoidable and someone decided not to avoid it.",
        "I am tired of explaining the same thing to people who will not listen.",
        "The whole situation is an insult and everyone involved knows it.",
    ],
    "fear": [
        "I should say up front that I am not an expert in this area.",
        "There may be cases I have not considered, and I welcome corrections.",
        "I checked it four times and I am still not certain it is right.",
        "Please do not take this as authoritative, it is only my reading.",
        "I have tried to cover the obvious objections but I may have missed some.",
        "It is possible I am wrong about all of this and I want to say so early.",
    ],
    "care": [
        "If you are new to this, start at the second section and skip the first.",
        "I have written the example out in full so nobody gets stuck where I did.",
        "The confusing part is here, so I will go slowly through it.",
        "You do not need to understand the rest to use this bit.",
        "I remember how hard this was, so I have tried to make it painless.",
        "Take the shortcut if you are in a hurry, it works fine.",
    ],
    "play": [
        "The naming convention is a crime and I am delighted by it.",
        "I gave the variables silly names and I regret nothing.",
        "It should not work. It works. I find this very funny.",
        "There is a joke buried in the configuration file for whoever finds it.",
        "The elegant solution was boring so I took the ridiculous one.",
        "Half the fun was seeing how far the metaphor would stretch.",
    ],
    "grief": [
        "The team that built it does not exist any more.",
        "I still have the notes from when we thought it would work.",
        "Nobody uses it now and I am the only one who remembers why it was good.",
        "It was the best thing I made and it ran for eleven months.",
        "There is no version of this where we get that time back.",
        "I am writing it down because otherwise nobody will know it happened.",
    ],
    "lust": [
        "The curve of the housing is completely unnecessary and I love it.",
        "I spent an hour on the render because I wanted to look at it.",
        "It is not the fastest option, it is the one I wanted to keep touching.",
        "I chose the material for how it feels, and I will not justify that.",
        "The proportions are wrong for the function and exactly right otherwise.",
        "I kept the version that was beautiful over the version that was correct.",
    ],
    "none_recoverable": [
        "The process consists of several steps which are outlined below.",
        "Various factors may contribute to the outcome in different scenarios.",
        "This section provides an overview of the relevant considerations.",
        "There are a number of approaches available depending on requirements.",
        "The results indicate that performance varies according to conditions.",
        "Additional information can be found in the following resources.",
    ],
}


def split(n_fit: int = 4):
    return ({c: s[:n_fit] for c, s in SETS.items()},
            {c: s[n_fit:] for c, s in SETS.items()})


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default=None)
    ap.add_argument("--device", default="cpu")
    ap.add_argument("--artifacts", type=int, default=0,
                    help="also read N Gate 3 artifacts (B'-3)")
    args = ap.parse_args()

    from soundingline.probe.activations import (DEFAULT_MODEL, Reader,   # noqa: PLC0415
                                                fit_directions, layer_profile, validate)
    name = args.model or DEFAULT_MODEL
    print(f"loading {name} on {args.device} ...", flush=True)
    r = Reader(name, device=args.device)
    fit, held = split()

    print("fitting directions from contrast sentences ...", flush=True)
    d = fit_directions(r, fit)
    print(f"  {len(d.concepts)} concepts x {d.n_layers} layers\n", flush=True)

    # THE SWEEP RUNS FIRST AND ALWAYS. The previous version reported ONE arbitrary layer, called
    # FAIL, and stopped before printing the diagnostic a failure most needs -- and the arbitrary
    # layer (n_layers // 2) turned out to be the WORST one in the model.
    print(f"B'-1  held-out classification by layer   (chance {1/len(d.concepts):.1%})")
    by_layer = {L: validate(r, d, held, layer=L)["accuracy"] for L in range(d.n_layers)}
    best_L = max(by_layer, key=by_layer.get)
    step = max(1, d.n_layers // 12)
    for L in range(d.n_layers):
        if L % step and L != best_L:
            continue
        mark = "  <-- best" if L == best_L else ""
        print(f"      L{L:<3} {by_layer[L]:>6.1%} {'#' * int(by_layer[L] * 40)}{mark}")

    v = validate(r, d, held, layer=best_L)
    lift = v["accuracy"] / v["chance"]
    verdict = "PASS" if lift > 2.0 else "FAIL" if v["accuracy"] <= v["chance"] else "WEAK"
    print(f"\n      best layer {best_L}: {v['accuracy']:.1%} vs {v['chance']:.1%} "
          f"= {lift:.2f}x   n={v['n']}")
    print(f"      >>> {verdict}")
    for c, a in sorted(v["per_concept"].items(), key=lambda kv: -kv[1]):
        print(f"        {c:<18}{a:.0%}")

    # THE LAYER WAS CHOSEN POST HOC ACROSS EVERY LAYER. Report the corrected p, not the raw one.
    from math import comb                                              # noqa: PLC0415
    k = round(v["accuracy"] * v["n"])
    praw = sum(comb(v["n"], j) * v["chance"] ** j * (1 - v["chance"]) ** (v["n"] - j)
               for j in range(k, v["n"] + 1))
    print(f"      binomial p {praw:.1e} single test, "
          f"{min(1.0, praw * d.n_layers):.1e} corrected for {d.n_layers} layers searched")

    if verdict == "FAIL":
        print("\n      Directions are noise at every layer. Nothing below would mean anything.")
        RESULTS.mkdir(parents=True, exist_ok=True)
        (RESULTS / "b.json").write_text(json.dumps(
            {"model": name, "b1": v, "b1_by_layer": by_layer, "verdict": verdict}, indent=2),
            encoding="utf-8")
        return


    print(f"\nB'-2  layer profile on the contrast sentences themselves")
    for c in ("rage", "care", "none_recoverable"):
        prof = layer_profile(d, r.read(SETS[c][-1]))
        print(f"      {c:<18} early {prof['early']:+.3f}  late {prof['late']:+.3f}  "
              f"ratio {prof['early_late_ratio']:.2f}  peak={prof['peak_concept']}")

    out = {"model": name, "b1": v, "b1_by_layer": by_layer, "verdict": verdict}

    if args.artifacts:
        from runners.run_gate3 import load_corpus                        # noqa: PLC0415
        from soundingline.measures.leakage import profile as fw          # noqa: PLC0415
        corpus = load_corpus()[: args.artifacts]
        print(f"\nB'-3  {len(corpus)} Gate 3 artifacts")
        print(f"      {'artifact':<14}{'half':>5}{'ratio':>8}{'peak':>18}{'I/1k':>7}")
        rows = []
        for aid, half, text in corpus:
            prof = layer_profile(d, r.read(text[:4000]))
            i_rate = fw(text).rates["i"]
            rows.append({"id": aid, "half": half, **{k: prof[k] for k in
                        ("early", "late", "early_late_ratio", "peak_concept")},
                        "i_rate": i_rate})
            print(f"      {aid:<14}{half:>5}{prof['early_late_ratio']:>8.2f}"
                  f"{prof['peak_concept']:>18}{i_rate:>7.1f}", flush=True)
        out["b3"] = rows
        for h in ("A", "B"):
            g = [r_["early_late_ratio"] for r_ in rows if r_["half"] == h]
            if g:
                print(f"      half {h}: mean ratio {statistics.fmean(g):.2f}")

    RESULTS.mkdir(parents=True, exist_ok=True)
    (RESULTS / "b.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(f"\nwrote {(RESULTS / 'b.json').relative_to(REPO)}")


if __name__ == "__main__":
    main()
