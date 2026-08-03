# Gate 1 — verdict: **INCOMPLETE**. Not passed, not failed.

**Run 2026-08-02, local arm, qwen3.5:9b, k=3, family v2.**
Raw output: `results/gate1/gate1_local_k3.json`, `results/gate1/clean_run.log`.

Gate 1's honest options are continue, redesign, or stop. The answer is **continue, with the
headline measure rebuilt first** — and the reason is that one dimension worked and one did not,
in a way that separates cleanly.

---

## §1. What the run produced

| artifact | valid | fit | conc | ground | supp | agree | depth | audience |
|---|---|---|---|---|---|---|---|---|
| **A** (rich, 5 revisions) | 3/3 | **0.000** | 0.19 | **0.00** | 0.00 | 0.67 | 0 | `specific_person` ×3 |
| **B** (thin, 9-word prompt) | 3/3 | **0.600** | 0.65 | 0.33 | 1.00 | 0.67 | 3 | `known_group` / `general_public` |
| **C** (rich, first draft) | 1/3 | — | — | — | — | — | — | `general_public` |

**7 of 9 samples valid.** C fell below the k≥2 that convergence requires, so the three-way
ranking the gate was built to test could not be computed. `B > A` is what remains, and it is not
the pre-registered comparison.

**Verdict against C-18: NEITHER.** The probe is measuring a third thing, and §3 says what.

---

## §2. The one clean positive, and it is the interesting one

**All three samples on item A independently returned `audience = specific_person`.**

Item A was written to a brief naming one reader — a friend who had bounced off the game twice,
plays in forty-minute chunks, and had been defeated by a stat calculator. Nothing in the artifact
says "this is for one person." The probe recovered it three times out of three, with the
machine-audience hypothesis at 0.02.

Items B and C, from the same generator on the same topic, returned `known_group` and
`general_public`. The dimension **separated the artifacts by their actual direction**, and it did
so in the direction the *protocol* says is correct — which is the direction **the human curator
did not go**. The curator ranked A dead last, blocked by surface AI markers (CALIBRATION_03 §2).

This is the C-18 "protocol order" outcome appearing on **one dimension**. It is not the verdict —
fit is the headline and fit failed — but it is the first evidence in the project that the
instrument can recover something a domain-expert human reader could not, which is the entire
argument for building it.

**It must not be over-read.** One dimension, one artifact, k=3, one model, and the person who
wrote the brief also wrote the code. It is a signal to test properly, not a result.

---

## §3. Why fit failed, and why it is not the model's fault

`fit` is the geometric mean of concentration, grounding and support. **Item A scored 0.00 on
grounding** — not one quote the probe offered could be located in the artifact — so fit went to
zero regardless of everything else.

That is not the probe hallucinating. Item B, the *thinner* artifact, scored 0.33 on the same
measure. The pattern across the run is that grounding is low everywhere and collapses where the
prose is densest, which points at the locator rather than the reader: whitespace-normalised exact
substring matching is too brittle for a model that paraphrases lightly while quoting.

**Consequence:** fit currently punishes artifacts whose language is hardest to quote back
verbatim, which correlates with exactly the revision-toward-directness that item A received. A
measure that penalises careful prose is measuring the wrong thing, and the ranking it produced
cannot be trusted in either direction.

This is a **fixable measurement defect, not an architecture failure**, and it is the reason the
verdict is incomplete rather than redesign.

---

## §4. Reliability, stated plainly

**7/9 samples valid (78%).** The two failures were a truncated JSON string and a quote exceeding
its length cap. Both are generation-budget problems on a 9B local model, both are recorded, and
neither was retried — retrying would bias the sample toward artifacts the model finds easy.

The bring-up cost, honestly: **six distinct failure classes** between the model being installed
and the run completing, each one recorded in the code where it was fixed —

1. thinking collides with constrained decoding (18,889 chars of reasoning, zero of output);
2. grammar cannot enforce a simplex (a distribution summing to 2.50);
3. an open object lets the grammar drop hypotheses (`machine` omitted entirely);
4. the model switches to percentages unprompted;
5. **asking a model for character offsets is asking it to count characters** — the single worst
   design error in the build, now replaced by model-quotes / code-locates;
6. pydantic docstrings bloated the grammar past what the sampler could compile.

Every one is evidence for the two-stage rewrite, which is now in and which raised single-call
reliability from 4/6 to 6/6 on the smoke test.

---

## §5. What happens next, in order

1. **Rebuild grounding.** Fuzzy match with a stated threshold, or score locatability per claim
   rather than as a hard binary. Until then, no fit number leaves this repository.
2. **Re-run Gate 1** with grounding fixed and k=5, so a single sample failure cannot drop an
   artifact below the convergence floor.
3. **Run the API arm** (H1.5). The local arm's 78% and its zero-grounding behaviour are exactly
   what the reference arm exists to bound — if Opus 5 grounds cleanly on item A, the defect is
   the 9B model's quoting fidelity rather than the locator, and the fix is different.

**No Gate 1 number may be quoted anywhere until step 1 lands.** The audience finding in §2 is the
sole exception, and only with §2's final paragraph attached.
