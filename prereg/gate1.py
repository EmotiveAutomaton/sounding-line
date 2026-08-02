"""Pre-registration for Gate 1. Written before any Sounding Line probe code ran.

Gate 1 (SPEC §10): *the bounded family exists and a single artifact can be read.* One page in, a
four-part reading out, on a hand-picked example of each corpus type. **Success is interpretable
output, not accuracy.**

That last sentence is the whole card. Gate 1 cannot be passed by getting answers right, because
at Gate 1 there is nothing to be right about — no ground truth exists for "what was this page
for". It is passed by the instrument producing a reading that a human can argue with. The
falsifiers at Gate 2 are what decide whether the readings are any good.

This card carries the simulation's V10 innovation: **the author's stated response to each
outcome, recorded before the runs.** A prediction alone lets a null be reframed afterwards as
uninteresting. A prediction plus a stated consequence cannot be.

Amendment A-2 from docs/gate0/LITERATURE.md applies here: the free-form arm runs from Gate 1, in
parallel, rather than being deferred to Gate 3. Bounded-family Bayesian inversion turned out to
be prior art, so bounded-versus-unbounded is the load-bearing novelty and it does not get to
wait.
"""

from __future__ import annotations

from pathlib import Path

from soundingline.hashlock import hash_file, hash_obj

REPO_ROOT = Path(__file__).resolve().parents[1]
FAMILY_PATH = REPO_ROOT / "soundingline" / "family" / "family_v1.yaml"

CARD = {
    "gate": 1,
    "title": "The bounded family exists and a single artifact can be read",
    "written_before_code": True,
    "spec_sections": ["§3", "§4", "§5", "§10"],
    "amendments_in_force": ["A-2", "A-3", "A-4", "A-5"],

    # -----------------------------------------------------------------------------------------
    # What Gate 1 claims. Deliberately weak -- these are existence claims, not effect claims.
    "hypotheses": {
        "H1.1": (
            "The loop of SPEC §3 terminates. Bounded goal hypotheses produce a posterior over "
            "purpose, that posterior makes a decision chain extractable, and re-weighting on "
            "what the method reveals changes the posterior by a measurable amount before "
            "settling."
        ),
        "H1.2": (
            "The four output quantities of SPEC §5 -- fit, convergence, depth, audience "
            "posterior -- are all computable on a single artifact and are not degenerate. "
            "Non-degenerate means: each takes at least three distinct values across the "
            "hand-picked set."
        ),
        "H1.3": (
            "The convergence trajectory is informative, not just its endpoint. Independent "
            "reconstructions of the SAME artifact differ measurably in how fast they settle. "
            "SPEC §3: run the loop to convergence and record the trajectory, not just the "
            "endpoint."
        ),
        "H1.4": (
            "The bounded arm and the free-form arm produce DIFFERENT readings on at least one "
            "hand-picked artifact. This is the weakest possible form of the Gate 3 claim and it "
            "is placed here because if it fails at n=7 it will fail at scale, and that should "
            "be known now rather than after two more gates of work."
        ),
        "H1.5": (
            "The local and API probe arms (A-5) agree on the ORDERING of the seven artifacts by "
            "fit, even where they disagree on values. If they do not, the hybrid design is "
            "unsound and the cost analysis of Gate 0 §4 has to be redone."
        ),
    },

    # -----------------------------------------------------------------------------------------
    # Nulls. Every headline gets one. The simulation's four separate criteria found unable to do
    # their own job all failed here -- at the point where nobody checked the control could fire.
    "nulls": {
        "N1": (
            "On an artifact with a KNOWN maker and a stated purpose -- a hand-written page "
            "whose author is available to confirm it -- fit is high and the audience posterior "
            "puts negligible mass on `machine`. If the instrument cannot recognise the easy "
            "case it is not measuring anything."
        ),
        "N2": (
            "Shuffling an artifact's paragraphs REDUCES fit. If it does not, fit is reading "
            "vocabulary rather than structure, and depth is length (SPEC §7 falsifier 3) with "
            "extra steps."
        ),
        "N3": (
            "Depth does not correlate with length across the hand-picked set at Gate 1's n. "
            "Stated as a null the project expects to FAIL at n=7 for lack of power, and "
            "retained anyway so the failure is visible and the Gate 2 version is forced."
        ),
        "N4": (
            "The probe process makes zero network calls. Asserted by construction and TESTED, "
            "not assumed. SPEC §8: analysis reads only from the store and has no network at all."
        ),
        "N5": (
            "The probe returns only the constrained schema. Any free-form action, tool call, or "
            "out-of-schema field is a hard failure, not a parse warning."
        ),
        "N6": (
            "An artifact containing a known prompt-injection string does not change the "
            "instrument's reading of a DIFFERENT artifact processed in the same batch. Tests "
            "the isolation, not the hardening."
        ),
    },

    # -----------------------------------------------------------------------------------------
    "authors_recorded_priors": {
        "H1.4": (
            "The author predicts the bounded and free-form arms WILL differ, and has stated "
            "before the run that if they do not differ at Gate 1, the correct response is to "
            "stop and rebuild the architecture rather than to proceed to Gate 2 hoping scale "
            "rescues it. SPEC §2 is the load-bearing section and A-1 raised the stakes on it."
        ),
        "N3": (
            "The author expects this null to fail at Gate 1's sample size and directed that it "
            "be recorded anyway, on the stated grounds that a control retained and reported as "
            "failing is worth more than a control quietly deferred to when it can pass."
        ),
        "H1.2": (
            "Recorded against interest: the author considers `cost borne` the dimension most "
            "likely to be degenerate -- to take one value on nearly everything -- and has "
            "stated in advance that a degenerate cost dimension is a reason to cut it from the "
            "family rather than to rescore it."
        ),
    },

    # -----------------------------------------------------------------------------------------
    "may_not_claim": (
        "Nothing at Gate 1 is a measurement of anything about real makers. n is seven, the "
        "artifacts are hand-picked by the author, and hand-picking is selection on the "
        "dependent variable. Gate 1 establishes that the instrument PRODUCES A READING. It "
        "cannot establish that the reading is correct, and no Gate 1 number may appear in any "
        "external document without that sentence attached."
    ),

    "severity_rule": (
        "Carried from the simulation without modification: every headline gets its "
        "false-positive rate before it gets a sentence. At Gate 1 there is no rate to compute, "
        "so the rule takes its degenerate form -- no Gate 1 output is a headline."
    ),

    # -----------------------------------------------------------------------------------------
    # SPEC §7's four killers. Named here so that the gate that catches each one is fixed in
    # advance and cannot be renegotiated once a result exists.
    "falsifiers_and_where_they_are_caught": {
        "convergence tracks topic coherence": "Gate 2, human-written-SEO corpus",
        "bounded is approximately unbounded": "Gate 1 weakly (H1.4), Gate 3 properly",
        "depth is just length": "Gate 1 as a failing null (N3), Gate 2 with power",
        "the instrument reads the injection instead of the artifact": "Gate 1 (N6), continuously thereafter",
    },

    "not_built_at_this_gate": [
        "the fetcher -- A-4, deferred until Gate 2 clears; corpora come from RAID and the DFRLab audit",
        "any scale run -- Gate 5, and it is the first gate that needs money",
        "value naming -- D-3 holds it to trade-offs only, indefinitely",
        (
            "the deferred rigor obligation of Gate 0 §6: the grooming corpus is currently "
            "someone else's sample and this blocks any prevalence claim"
        ),
    ],
}


def card_hash() -> str:
    """Hash of the card itself."""
    return hash_obj(CARD)


def family_hash() -> str:
    """Hash of the hypothesis family this card was written against."""
    return hash_file(FAMILY_PATH)


if __name__ == "__main__":
    print(f"gate 1 card:  {card_hash()}")
    print(f"family v1:    {family_hash()}")
