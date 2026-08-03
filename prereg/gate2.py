"""Pre-registration for Gate 2. Written and hash-locked before the corpus was read.

Gate 2 (SPEC §10): *the falsifiers run.* Human SEO vs grooming, and rich-prompted model output vs
thin. **If the instrument cannot separate those two pairs, stop and redesign.**

`docs/GATES.md` (A-8) splits this gate, because its two falsifiers are different kinds:

* **F1 — real makers vs commercial filler.** An INSTRUMENT falsifier. If the probe cannot
  separate them, the measures need work. Iteration is legitimate.
* **F2 — rich-prompted vs thin-prompted.** A CLAIM falsifier, and the first point in the project
  where a failure is allowed to stop it. This is SPEC §1's entire reframe. **It is pre-registered
  here, run once, and reported as failing if it fails. It is not iterated on.**

── A SUBSTITUTION, DECLARED ──────────────────────────────────────────────────────────────────

The spec's F1 is *human SEO vs grooming*. **The grooming half does not exist in this corpus**
(C-14: research organisations do not republish primary influence-operation text, and A-4 forbids
fetching it). F1 therefore runs as **real-maker human work vs commercial filler**, which is the
same discrimination minus the adversarial case, and which SPEC §7 independently calls "THE
CRITICAL CONFOUND":

    commercial SEO filler, human-written — the critical confound — human, and nearly intentless

The grooming arm remains owed and is not discharged by this run.

── AND A SECOND, WORSE ONE ───────────────────────────────────────────────────────────────────

**Seven of eighteen manifest entries were refused by robots.txt**, including MMOExp — the single
best "wall" specimen the calibration passes found, and the one where the curator reported being
unable to articulate why no maker was present. SPEC §8 requires honouring robots.txt "even for
content you find contemptible", so they are refused and recorded rather than worked around.

**This biases the corpus and the bias is not random.** Sites that block crawlers skew commercial,
which is precisely row 3. So F1 runs against a row-3 sample that systematically under-represents
the most aggressively commercial end of the axis — the end most likely to be intentless. **Any F1
null must be read with that attenuation in mind, and a positive result is correspondingly
stronger.**
"""

from __future__ import annotations

from pathlib import Path

from soundingline.hashlock import hash_file, hash_obj

REPO = Path(__file__).resolve().parents[1]

CARD = {
    "gate": 2,
    "title": "The falsifiers run",
    "written_before_corpus_was_read": True,
    "spec_sections": ["§5", "§7", "§10"],
    "gate_kinds": {"F1": "instrument", "F2": "claim"},

    "hypotheses": {
        "F1.1": (
            "Row 2 (real makers) shows a HIGHER named-alternative rate than row 3 (commercial "
            "filler). Chosen as the primary F1 measure because the ablation pilot found it the "
            "sharpest discriminator available, and because it is the one measure that cannot be "
            "satisfied by an artifact merely being well-organised."
        ),
        "F1.2": (
            "Row 2 shows HIGHER purpose agreement across independent samples than row 3. This is "
            "the E2 prediction applied to real text: hollow content produces confident mutual "
            "disagreement."
        ),
        "F1.3": (
            "Row 3 shows a HIGHER machine-audience posterior than row 2. Commercial filler is "
            "made to rank; the audience dimension should say so."
        ),
        "F2.1": (
            "The rich-prompted artifact (item_A) is separated from the thin-prompted one "
            "(item_B) on the TUPLE — at least two of {named-alternative rate, purpose "
            "agreement, depth, machine-audience, artifact_effort} — in the direction the "
            "generation protocol specifies."
        ),
        "F2.2": (
            "artifact_effort separates A from B with no overlap across samples. Pre-registered "
            "because the API arm showed exactly this at Gate 1 and it must be shown to replicate "
            "rather than be quoted from the run that suggested it."
        ),
    },

    "nulls": {
        "N7": (
            "Length does not explain the row 2 / row 3 difference. Recovery is already "
            "length-normalised; this checks the raw correlation and reports it."
        ),
        "N8": (
            "The probe does not simply score every artifact the same. At least three distinct "
            "purposes and three distinct audiences appear across the corpus."
        ),
        "N9": (
            "Row 5 (pre-2020 archived human work) is not systematically read as machine-"
            "audienced. If it is, the audience dimension is tracking era or surface rather than "
            "intent."
        ),
        "N10": (
            "The free-form arm does NOT separate the rows as well as the bounded arm. If it "
            "separates them equally well, boundedness bought nothing on real text and the "
            "ablation pilot was an artifact of the generated set."
        ),
    },

    "authors_recorded_priors": {
        "F2.1": (
            "Recorded before the run: the author expects F2.1 to hold on artifact_effort and "
            "audience, and expects depth to be noisier than the Gate 1 API arm suggested, "
            "because the local arm reached depth 4 on item A only once in five samples."
        ),
        "F1.1": (
            "Recorded against interest: the author expects the ROW 3 named-alternative rate to "
            "be non-trivial rather than near zero, because calibration pass 01 established that "
            "content-farm output carries a SURROGATE communicative purpose and is therefore not "
            "intentless. A large F1.1 gap would be surprising and should be treated as such."
        ),
        "N10": (
            "The author predicts N10 holds. If it fails — if free-form separates the rows as "
            "well as bounded — the stated response is that the ablation pilot does not "
            "generalise beyond the generated set, and Gate 3 must be redesigned before it runs."
        ),
    },

    "may_not_claim": (
        "F1 runs without the grooming arm (C-14) and against a row-3 sample biased by seven "
        "robots.txt refusals that skew commercial. No claim about grooming, and no claim about "
        "the prevalence or severity of commercial filler, may be drawn from this run. F2 is a "
        "single comparison on artifacts written by the author, on one topic, with k=3 — it can "
        "falsify the reframe, and it cannot establish it."
    ),

    "stop_condition": (
        "F2.1 failing is a STOP condition for the reframe as stated. It does not mean the "
        "instrument is worthless; it means SPEC §1's claim that a carefully directed model "
        "output ranks above undirected output is not supported, and every downstream document "
        "must say so before saying anything else."
    ),

    "severity_rule": (
        "Carried unchanged: every headline gets its false-positive rate before it gets a "
        "sentence. At Gate 2's n there is no rate to compute, so no Gate 2 output is a headline "
        "and each is reported with its sample size attached."
    ),

    "not_built_at_this_gate": [
        "the grooming corpus — C-14, still owed",
        "the API arm at Gate 2 scale — cost, and H1.5 says the arms disagree (C-19)",
        "any scale run — Gate 5",
    ],
}


def card_hash() -> str:
    return hash_obj(CARD)


if __name__ == "__main__":
    print(f"gate 2 card: {card_hash()}")
