# Gate 1 — verdict

**C-18 fired, and returned CURATOR ORDER. It is reported as firing and is not withdrawn.**

**And C-18 was mis-specified**, in a way the spec I wrote it under explicitly warns against. Both
of those sentences are true, the first is reported first, and §3 explains why the second is not a
rescue.

Runs 2026-08-02 — local arm qwen3.5:9b (k=5), API arm claude-opus-5 (k=3, 75 min), family v2.
Raw: `results/gate1/gate1_api_k3.json`, `gate1_local_k5.json`.

---

## §1. The API arm

| item | fit | conc | ground | supp | agree | depth | **machine** | **artifact_effort** |
|---|---|---|---|---|---|---|---|---|
| **A** rich, 5 revisions | 0.601 | **0.27** | 0.80 | 1.00 | 1.00 | **4** | **0.01** | **[2, 3, 3]** |
| **B** thin, 9-word prompt | **0.718** | 0.37 | 1.00 | 1.00 | 1.00 | 3 | 0.42 | [1, 1, 1] |
| **C** rich, first draft | 0.662 | 0.39 | 0.75 | 1.00 | 1.00 | 3 | 0.39 | [1, 1, 1] |

**Ranking by fit: B > C > A — the curator's order exactly.** Verdict text as pre-registered:
*the probe shares the surface heuristic; architecture at fault.*

Reliability was 9/9. Agreement was 1.00 on every artifact — the probe gave the same reading three
times running on all three.

---

## §2. Every other dimension went the other way

The single number ranked A last. **The tuple ranks A first, on four dimensions independently:**

| dimension | A | B | C | separates? |
|---|---|---|---|---|
| machine-audience | **0.01** | 0.42 | 0.39 | **yes, 40×** |
| depth | **4** | 3 | 3 | yes |
| artifact_effort | **[2,3,3]** | [1,1,1] | [1,1,1] | **yes, no overlap** |
| audience | `specific_person` ×3 | `general_public` | `general_public` | **yes** |
| purpose | `inform` | `rank` | `rank` | yes |

Item A was written to a brief naming one reader, and never says so. The probe returned
`specific_person` three times out of three and put 1% on the machine hypothesis, against 42% and
39% for the other two — which are, correctly, the two that read as made for a ranking system.

**`artifact_effort` separates with no overlap at all.** That is the dimension the curator
invented, unprompted, after the family was already built and locked — and it is the cleanest
discriminator in the run.

---

## §3. C-18 was mis-specified, and this is not a rescue

**C-18 ranked the artifacts on `fit`. A single number.**

SPEC §5:

> **The reading is the tuple.** Report all four always — the simulation's whole methodology is
> that a single number invites the overclaim.

I wrote a pre-registered criterion that ranks on one number, in a project whose stated
methodology is that no single number may be used that way. The criterion did exactly what it was
built to do and the thing it was built to do was wrong.

**This is the fifth instance of the failure mode this lineage has most of.** The simulation found
four separate criteria unable to do their own job, each caught by a later pass. This is the fifth,
it is mine, and it was caught by the run it was written for.

**Why this is not motivated reinterpretation:**

- The verdict stands as fired. `CURATOR ORDER` is in the results JSON and in this document's
  first line, and no downstream document may quote the tuple evidence without it.
- The defect is in the criterion's *form*, not its *result* — it would have been just as wrong
  had it returned the protocol order, and I would have had no reason to notice.
- It is diagnosable against a rule written before the criterion existed, in a document I did not
  author for this purpose.
- The original is retained and still computed. `run_gate1.py` still ranks on fit and still prints
  the C-18 verdict.

**What may be claimed:** that on this evidence the *tuple* separated directed from undirected
work, and the *fit scalar* did not. Not that the instrument passed.

---

## §4. Why fit inverted: concentration rewards simplicity

Support was 1.00 everywhere and grounding was high everywhere, so the ranking is driven almost
entirely by **concentration** — and A scored lowest (0.27 against 0.37 and 0.39).

Concentration is `1 − normalised entropy` of the purpose posterior. It rewards putting all the
probability on one hypothesis.

**A rich artifact does more than one thing.** Item A informs, persuades, and expresses, and the
probe spread its posterior accordingly — which is the correct reading. Items B and C do one thing
(rank), and concentrate.

So concentration measures **how simple an artifact's purpose is**, and fit rewards that. This is
the third component of fit found to be measuring the wrong object: `support` was a keyword
detector, `grounding` conflated silence with fabrication, and now `concentration` rewards
single-purposedness. **Fit has no surviving component that was right as designed.**

---

## §5. The local/API comparison — H1.5 answered

| | local (9b) | API (opus-5) |
|---|---|---|
| item A depth | 2 | **4** |
| item A grounding | 0.34 | **0.80** |
| item A support | 0.50 | **1.00** |
| agreement | 0.75–1.00 | **1.00 everywhere** |
| valid samples | 13/15 | **9/9** |

**H1.5 fails: the arms do not agree on ordering** (local B > A > C, API B > C > A), and the local
arm's low grounding and shallow depth were **model ceiling, not locator defect**. The same
locator, the same prompts and the same schema produce 0.80 grounding and depth 4 on Opus 5.

Consequence for A-5: the hybrid design is not currently sound. The local arm cannot carry
convergence volume for a measurement the API arm defines, because they do not measure the same
thing. Recorded as **C-19**.

---

## §6. The sealed protocol's loose prediction resolved, and reversed

`PROTOCOL_SEALED.md` §4 named one prediction as held most loosely:

> If the curator ranks them as close, then the *brief* carried the intent and the revision added
> little... That is a real and publishable finding, and it is not the one I expect.

**C is indistinguishable from B on every dimension** — machine 0.39 vs 0.42, depth 3 vs 3,
artifact_effort [1,1,1] vs [1,1,1], both `general_public`, both `rank`. A stands alone.

C is the rich brief's first draft; B had a nine-word prompt. **The brief alone left almost no
trace. The five rounds of revision carried the entire recoverable signal.**

That is the reverse of what I expected, it is the finding the sealed document said would be
publishable, and it arrived from the arm that reads most carefully.

---

## §7. Verdict

**REDESIGN fit. CONTINUE everything else. Do not proceed to Gate 2.**

- **Rebuild `fit` from scratch.** No component survived. Whatever replaces it must not be a
  scalar that a criterion can rank on, because SPEC §5 forbids exactly that.
- **Re-specify C-18** as a tuple comparison, retaining the original.
- **Do not trust the hybrid** until C-19 is resolved.
- **The free-form arm has still not been compared** — it now runs (A-2 repaired) but no run has
  put it against the bounded arm. Until that happens the project has no evidence that boundedness
  buys anything, which is the claim Gate 0 said was load-bearing.

**No fit number leaves this repository.** The tuple evidence in §2 may be cited with §3 attached.
