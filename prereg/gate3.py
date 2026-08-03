"""Pre-registration for Gate 3. Hash-locked BEFORE the corpus was read by the instrument.

Gate 3 is a **CLAIM gate** (`docs/GATES.md` §2). A failure here is allowed to stop the project,
iterating until it passes would be p-hacking, and the stop condition is written below rather than
decided afterwards.

── WHAT IS BEING TESTED, IN ONE SENTENCE ─────────────────────────────────────────────────────

Whether the instrument can tell work made by a person who cared from commercial filler, using
**method unlock** — how much more of the maker's execution chain becomes recoverable once the
purpose is pinned.

── WHY THIS MEASURE AND NOT THE ONES GATE 2 USED ─────────────────────────────────────────────

Gate 2 failed on purpose-based measures, and the simulation had already established why. E36:

    Every measure of what a reader takes on, in every version of this project, has scored how
    much of the maker's PURPOSE it got. Depth is built so the purpose is equally readable however
    deep the work is, so that measure could not move with depth whatever was true... On the
    maker's method, depth moves uptake: 0.179 [0.099, 0.267]. On the maker's purpose, measured on
    the same cells, it does not: -0.028 [-0.116, 0.058].
    **The experiment was not wrong; it was pointed at the wrong quantity.**

The direction of the prediction was fixed by that finding, in a different codebase, on different
data, before this project began. **This is a theory-derived prediction, not a post-hoc pattern**,
and the effect size used for the power calculation (d = 0.87) comes from a seven-artifact pilot
whose sign was predicted in advance.

── WHAT THE INSTRUMENT AND THE HUMAN WILL EACH BE READING ────────────────────────────────────

**Plain extracted text, both.** Every previous calibration reading was of a rendered web page
while the probe read extracted text, so the two were never scored on the same object (C-21). The
curator's later reading uses `to_be_read/`, which is written from the same bytes the probe sees.
"""

from __future__ import annotations

from pathlib import Path

from soundingline.hashlock import hash_file, hash_obj

REPO = Path(__file__).resolve().parents[1]

CARD = {
    "gate": 3,
    "kind": "claim",
    "title": "Does method unlock separate work made with care from commercial filler?",
    "locked_before_run": True,

    # ── CORPUS, FIXED NOW ────────────────────────────────────────────────────────────────────
    "corpus": {
        "manifest": "corpora/manifests/gate3.json",
        "half_A": "made by an identifiable person who cared — technical postmortems, personal "
                  "essays, craft writing, a solo developer's account of his own game",
        "half_B": "commercial filler — template local-service pages, brand content that answers "
                  "a question in order to sell, affiliate roundups, aggregator pages",
        "n_A": 30,
        "n_B": 23,
        "domain_cap": 3,
        "domain_cap_rule": (
            "At most 3 artifacts per host, selected by sorted URL, applied BEFORE any statistic. "
            "Artifacts by one maker are not independent observations of 'a maker who cared', and "
            "five Paul Graham essays would otherwise carry Half A."
        ),
        "k": 5,
        "arm": "local",
    },

    # ── THE PRIMARY TEST ─────────────────────────────────────────────────────────────────────
    "primary": {
        "id": "G3.1",
        "statement": "Mean method unlock is higher in Half A than in Half B.",
        "statistic": "Welch's t-test, two-sided, alpha = 0.05, on per-artifact mean unlock",
        "direction_predicted": "A > B",
        "direction_source": "E36, established before this project existed",
        "pass": "p < 0.05 AND the difference is in the predicted direction",
    },

    # ── HANDLING DECIDED IN ADVANCE, NOT AFTER SEEING THE NUMBERS ────────────────────────────
    "prespecified_handling": {
        "trivial_unlock": (
            "Where the posterior settles on the first pass, before and after use the same purpose "
            "and unlock is 1.0 by construction. These are NOT excluded from the primary test — "
            "excluding them would be a choice made to help. They are reported separately as a "
            "secondary, and the primary stands whichever way that secondary falls."
        ),
        "failed_samples": (
            "An artifact with fewer than 2 valid samples is dropped and counted in the report. "
            "No retries: retrying biases the sample toward artifacts the model finds easy."
        ),
        "outliers": "None removed. No rule, no judgement, no exceptions.",
        "length": (
            "Artifact length is regressed against unlock and reported. If length explains the "
            "separation, G3.1 is reported as confounded even if p < 0.05."
        ),
    },

    # ── SECONDARY, REPORTED WHATEVER THE PRIMARY DOES ────────────────────────────────────────
    "secondary": {
        "G3.2": "Half A shows higher named-alternative rate than Half B. Gate 2 found this "
                "REVERSED on purpose-based reading; the unlock pass appeared to fix it and that "
                "must be shown to replicate.",
        "G3.3": "The free-form arm separates the halves LESS well than the bounded arm. This is "
                "the boundedness ablation on real text at power — SPEC §7's most important "
                "experiment and Gate 0's load-bearing claim.",
        "G3.4": "Machine-audience posterior is higher in Half B than Half A.",
        "G3.5": "Unlock does not correlate with artifact length (r reported regardless).",
    },

    "nulls": {
        "N11": "Half A and Half B differ on SOMETHING. If no measure separates them at all, the "
               "corpus split is not a real distinction and the whole design is void.",
        "N12": "The instrument returns at least 3 distinct purposes and 3 distinct audiences "
               "across the corpus — it is not scoring everything alike.",
        "N13": "Per-artifact unlock is stable enough to measure: within-artifact spread across "
               "k=5 is smaller than the between-half difference. If not, k must rise before any "
               "claim is made.",
    },

    # ── THE STOP CONDITION ───────────────────────────────────────────────────────────────────
    "stop_condition": (
        "If G3.1 fails — no significant separation, or separation in the wrong direction — then "
        "the last remaining candidate from the Gate 2 diagnosis becomes the answer: that "
        "recoverable intent, as this project defines and measures it, is not more present in work "
        "made with care than in competent commercial work. "
        "\n\n"
        "That is a stop for SPEC §1's reframe. It does not condemn the reader, the loop, the "
        "security architecture or the corpus method, all of which work. It condemns the claim "
        "that the instrument measures what the theory says it measures, and every downstream "
        "document must state it before stating anything else. "
        "\n\n"
        "Explicitly NOT permitted after a G3.1 failure: rebuilding the measure and re-running on "
        "this corpus. A fourth measure fitted to the same 53 artifacts would be unfalsifiable. "
        "Any successor measure requires a corpus this project has not seen."
    ),

    "authors_recorded_priors": {
        "G3.1": (
            "The author predicts G3.1 holds, at a smaller effect than the pilot's d = 0.87, "
            "because the pilot's seven artifacts were chosen after the fact from a corpus that "
            "had already been read and the 53 here have not been filtered that way."
        ),
        "G3.3": (
            "Recorded against interest: the author is LESS confident in G3.3 than in G3.1. The "
            "ablation pilot's boundedness effect was measured on three generated artifacts, and "
            "Gate 2's N10 — free-form separating the halves better than bounded — FAILED on real "
            "text. If G3.3 fails again here, boundedness is not doing the work Gate 0 said was "
            "load-bearing, and that is a separate problem from G3.1."
        ),
        "N13": (
            "The author expects N13 to be the tightest null. Per-artifact unlock at k=3 was "
            "visibly noisy; k=5 may still be too few, and if N13 fails the correct response is to "
            "raise k and re-run rather than to report G3.1 at any p-value."
        ),
    },

    "may_not_claim": (
        "One curator, one model, one arm, 53 artifacts, English only, and a Half B sample biased "
        "by crawler-blocking — commercial operators refused at 74% against individual makers' "
        "43%, so the filler that could be collected honestly skews toward the least optimised "
        "end. No claim about prevalence, about grooming networks (never sourced, C-14), or about "
        "what a general-public reader recovers."
    ),

    "severity_rule": (
        "Every headline gets its false-positive rate before it gets a sentence. Gate 3 reports a "
        "p-value and an effect size with a confidence interval, or it reports nothing."
    ),
}


def card_hash() -> str:
    return hash_obj(CARD)


if __name__ == "__main__":
    print(f"gate 3 card: {card_hash()}")
