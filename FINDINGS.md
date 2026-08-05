# FINDINGS — the rolling record

**The source of truth.** Everything else in this repository is working material. If this file and
another file disagree, this file is wrong and should be fixed, but it is the one to read first.

**Last updated: 2026-08-05.** Updated at the end of every working session, not per result.

---

## How this file works

Results move through three tiers and **compress as they go**. The point is that the list of things
we already know stays short, while anything still contestable keeps its method visible.

| tier | what it means | how much text |
|---|---|---|
| **1 · LIVE** | still contestable. Being worked on, or its method has not been examined | full paragraph, method visible |
| **2 · SETTLED** | has a verdict file and passed its required controls. **Not yet method-checked by the curator** | 1–2 sentences |
| **3 · CLOSED** | **the curator has read the method and could not poke a hole in it.** Never revisited unless something contradicts it | one line, forever |

**Promotion 1 → 2 is automatic** when a verdict file and the required controls exist.
**Promotion 2 → 3 requires the curator's explicit sign-off**, dated, in the table. Not mine. That is
the whole mechanism: *I* cannot decide something is settled enough to stop describing.

**Nothing skips a tier, and nothing is deleted.** A ruled-out result stays in the list at one line.

**Verdict labels**

| | |
|---|---|
| **POSITIVE** | the effect is real and survived its controls |
| **RULED OUT** | measured properly, failed, and we know why |
| **VOID** | the test could not answer its own question. **Not a negative result** — no information either way |
| **OPEN** | ran, ambiguous, needs more |

---

## Where we are, in one paragraph

Twenty-five tests across four gates and two simulation batches. **Ten measures are ruled out, four
tests are void, and there are three real positives — none of which measures the thing the project was
built to measure.** Every measure that reads *the artifact* has died to length, register, or
vocabulary. The only signals that have ever survived are read out of *the reader*. There is one
order-dependent effect and **it sits at p = 0.053**, which is not significant. The binding constraint
is no longer a measure; it is that **we have never once had a controlled comparison on human text.**

---

## ⚠ Known weaknesses — read before trusting anything below

You said you keep uncovering little issues in the methods. You are right to, and here is the list I
would use to attack this project. **None of these are resolved.**

**1 · ~~No multiple-comparison correction anywhere.~~ RESOLVED 2026-08-05, and it held up.**
19 primary tests corrected together (`results/audit/multiplicity.json`; controls excluded, because
correcting a test whose job is to *kill* one of our measures would make measures harder to kill).
**12 significant uncorrected → 12 under Benjamini-Hochberg → 10 under Benjamini-Yekutieli.** Only
`tentative_rate vs rung` and `causal_rate transfer vs thin` were lost, and neither is load-bearing.
**Everything load-bearing survives.** It also confirms in writing that the layer ratio vs rung was
never significant at n = 50 — BY p = 0.274. Standing rule now: new tests get added to that family.

**2 · ~~The headline effect is not statistically significant.~~ RESOLVED 2026-08-05 by replication.**
It was rho = −0.275, **p = 0.0529, n = 50**. On a held-out 100-artifact ladder with hyperparameters
frozen: **rho = −0.247 raw (p = 0.0132), and rho = −0.405 length-controlled (p < 0.0001).**
The curator's rule — *near-significance means raise the power* — worked exactly as stated.
See `results/ladder2/VERDICT.md`. **The effect is still modest and still only on machine text.**

**3 · Researcher degrees of freedom in the layer ratio. PARTLY RESOLVED.** `ratio_for()` splits the
model at `0.07 × depth` and `0.76 × depth`, and those loci were **chosen by looking at a prior result
on the same model**. They were **frozen and held out** on ladder 2 and produced a *larger* effect on
data they had never seen, which is the strongest available answer. **Still unresolved:** the choice
of measure *family* was ours, and no held-out set fixes that.

**3b · Length is a suppressor on the layer ratio, not a confound — and this was found late.**
Longer texts have a *higher* ratio (+0.248) while higher rungs produce longer texts (+0.401), so
length pushes the ratio **against** the effect. This is the first time in the project a length
correlation has not been a cause of death, and it explains ladder 1's marginal p. **Every measure
killed on a length correlation was killed without checking the direction of the relationship.**
That is a methodological hole in past work, and it is not yet closed.

**4 · Every positive rides on machine-written or public-domain text.** The ladder is 50 artifacts,
all generated. Author ID is books. **We have never had a controlled corpus of human artifacts**, which
is why every uncontrolled human comparison has died.

**5 · One human reader.** C-20 has been outstanding since the beginning. Eleven artifacts, one
person, and the readings have outperformed every measure — which means the most load-bearing evidence
in the project has a sample size of one.

**6 · The no-maker corpus is generated by the same model family we read with.** A shared-representation
artifact would look exactly like a human/machine difference. Untested.

**7 · A scale gap remains in the affect directions.** They are fitted on 12-word sentences and applied
to 200-word windows. We caught a worse version of this (4,000-character documents) and fixed it by
windowing, but a ~16× gap is still there and its effect is unmeasured.

**8 · The Gate 3 corpus has been read repeatedly.** It is a diagnostic corpus now, not a test corpus.
Nothing new should be claimed on it.

---

## TIER 1 · LIVE — contestable, method visible

### The one order-dependent effect — **replicated held-out 2026-08-05**

**What we did.** Generated 50 articles from one model on 12 topics, varying only how many situational
specifications the prompt carried (0/1/3/6/10, drawn at random, so no two prompts alike), then
measured the ratio of low-order to high-order affective activation in a reading model across the
rungs. When it came back at p = 0.0529, generated **100 more at fresh seeds and rotated topics** and
re-ran it once with **every hyperparameter frozen**.

**What we found.**

| | rho | p |
|---|---|---|
| ladder 1, n = 50 | −0.275 | 0.0529 |
| **ladder 2 held out, n = 100, raw** | **−0.247** | 0.0132 |
| **ladder 2, length-controlled ← primary** | **−0.405** | **<0.0001** |

Shuffling paragraphs or sentences leaves it alone; shuffling 5-word phrases costs a full ladder span.
**It lives at or below the sentence and it needs local word order — the only effect in this project
that has ever required order.**

**And length turned out to be hiding it, not causing it.** I wrote the opposite prediction into the
runner in advance. Longer texts have a higher ratio while higher rungs produce longer texts, so
length works *against* the effect; removing it nearly doubles it.

**Verdict: OPEN, replicated.** It does **not** move to POSITIVE, and the reason is not statistical:
**every rung is machine-written by the same model.** It shows the measure tracks specified intent
within one generator. Whether it does anything on human artifacts is weakness 4, which is a corpus
problem, not a measurement problem.

### Stacking weak effects into a detector — your idea, evaluated

**The proposal:** combine the small surviving effects into one detection algorithm.

**Worth testing, with one specific warning.** Stacking only helps if the components fail
*independently*. Ours may not: function-word geometry and affect directions are both read from the
same model on the same text, and both are at least partly lexical. **Stacking effects that share a
confound produces a strong confound, not a strong signal** — and it would look exactly like success.

**Two conditions before believing any stack:** (a) it must beat its own best single component on a
**held-out** corpus, not the fitting one; (b) its errors must not correlate with the components'
errors. Both are cheap to check and neither has been done.

**Also worth knowing:** ensembling weak stylometric features is precisely what commercial AI
detectors do, and it hits the ceiling this project already named (E38: a machine-matched reader scores
1.000 on machine text and 0.280 on human). **A stack is likely to rediscover a machine detector.** That
is not fatal — but the ladder is the test that tells the difference, because a machine detector must
see all five rungs as identical.

**Verdict: OPEN.** Not yet run.

---

## TIER 2 · SETTLED — verdict and controls exist, method not yet checked by you

### Positives

| | what we did | what we found | |
|---|---|---|---|
| **G-2** | Held the author fixed and asked whether function words separate *different works by the same person* — 34 books, 10 authors | **2.05× chance**, every one of ten authors above chance, permutation null 31.0% ± 1.7% | **POSITIVE** — the channel carries more than identity, so there is capacity for state |
| **B** | Fitted affect directions from contrast sentences inside a reading model and tested them on held-out sentences | **4× chance**, and **bag-of-words on the identical sentences scores exactly chance** — so it is not lexical. Accuracy is bimodal across depth | **POSITIVE** — the cleanest result in the project, with a built-in control |
| **G-1 / PC-1** | Ran author identification via Burrows' Delta as a known-answer check on the pipeline | **7.6×** (6.89× at today's windowing), and **identical to the digit at all four shuffle granularities** | **POSITIVE** — a solved field result, now used as a standing positive control that validates the harness |
| **GRAIN** | Measured what word-shuffling actually does, by shuffling at four granularities | Three in-distribution grains agree within 5 points; the word grain diverges by **27** | **POSITIVE** — the word shuffle inflates model-internal measures; quantified, not argued |
| **R−1** | Scored word salad as a rung below rung 0, to see whether any measure reads noise as intent | Nothing places noise at or above the most-specified rung | **POSITIVE** — a failure mode we do not have |

### Ruled out

| | what we did | what we found | |
|---|---|---|---|
| **density v1** | Counted decision density per artifact | It was word count: rho = **+0.877** | **RULED OUT** — length |
| **density v2** | Same, length-controlled | It became type-token ratio: rho = **−0.879**, permutation-invariant | **RULED OUT** — vocabulary |
| **rich > thin** | Compared machine text written *with* a purpose against *without* | Perfect theory-shaped ordering at p = 0.0005, then died to length and register | **RULED OUT** — confounded |
| **ladder, overall** | Asked whether any measure ranks five rungs of specified intent | Voided on length: rung vs output length **rho = +0.403** against a pre-registered 0.400 threshold | **RULED OUT** — by a hair, and the hair counts |
| **`purpose_breadth`** | Used posterior entropy over goals as a measure of motivational variety | Simulation showed it tracks **difficulty**: at matched difficulty, excess breadth from diversity is **−0.013 to −0.025** | **RULED OUT** — confounded with difficulty |
| **`separability()`** | Our own statistic for whether a feature vector separates groups | Said "no group information" on **author identification** | **RULED OUT** — wrong statistic; replaced by Burrows' Delta |
| **document activations** | Read activations over whole 4,000-character documents | Every artifact peaked on the concept that scored **0%** in validation | **RULED OUT** — scale mismatch |
| **W-1, the wall** | Asked whether a reader moves further from its resting state for a human maker | **−0.0049, p = 0.53** — machine content displaced it slightly *more*. Clean measure, no length confound | **RULED OUT** — a real null |
| **D-0b** | Properly powered retest of function words against maker state | The channel carries identity, not state | **RULED OUT** |
| **layer ratio, human vs machine** | Compared the low/high-order affect ratio on human against generated text | Gap keeps **99%** of itself when every sentence is reordered; commercial copy sits **26%** of the way from essays toward machine (p = 0.0033) | **RULED OUT** — lexical and register. Never report it as a human/machine discriminator |
| **`causal_rate`** | Rate of causal connectives, which ranked the ladder at **+0.659** with **zero** prompt echo and survived length control | Inverts on real text: human **3.162**, machine **5.35–6.08**, the purposeful arm highest | **RULED OUT as depth** — but a **POSITIVE about legibility**: it is E37's *legible and empty* wall, seen on real text |

### Void — could not answer their own question

| | what we did | why it means nothing | |
|---|---|---|---|
| **Gate 3** | The project's primary: split 51 web artifacts into halves, compare recovered method | Stability null failed — within-artifact sd **0.808** against between-half **0.087**. The simulation then showed the statistic reads **17.65** where truth is 0 and is undefined in 378 of 467 cases | **VOID** — not a negative result |
| **D-0** | Function words vs maker state on 380-word samples | **38% power.** Its median outcome under a true effect was below its own threshold | **VOID** |
| **R-1** | Five-component refusal battery | Pass condition was "3 of 5 higher" — a **50% false-positive rate** by arithmetic | **VOID** |
| **W-2** | Spread of reader displacement | n = 3 | **VOID** |

### What the simulation established (ground truth, which we do not have here)

| | | |
|---|---|---|
| **S-1** | The unlock statistic is broken — reads 17.65 where truth is 0 | explains Gate 3 |
| **S-3 / T-4** | The leak is readable at 0.899, and divergence survives a reader that is wrong about almost everything — including a **50% channel swap**. But it **fails at 25% concealment** | the affect leg transports, with a narrow target |
| **S-4/5** | Reordering the probe's stages changes the answer by **exactly 0.000** | a ~5% cost win, nothing more |
| **S-6** | Practised surface decays **6.5× faster** than depth; synthetic surface is flat | supports surface≠depth |
| **T-1** | **The triangle is not a triangle.** Three of six edges are exactly zero, goal is a sink already at ceiling (1.000), edges are additive not superadditive, and the **values vertex does not exist** (H(values\|goal) = 0) | reframes the theory |
| **T-2** | Kills `purpose_breadth`; also retracted the simulation's own S-2 | see above |
| **T-3** | **Decision-counting is well-defined where mode dwell is long** — dwell moves posterior concentration **2×** what artifact length does | specifies a corpus |
| **T-5** | Process-side and goal-side statistics **tie** as detectors | T-1's asymmetry has no instrument consequence — do not rebuild |

### The human readings — the most load-bearing evidence, and n = 1 reader

Eleven artifacts, two sessions, read aloud. **These have outperformed every measure.** The three
findings that keep mattering: **the variation of the veneer** is the primary detector (surface
*change*, not surface level); **depth is a property of the writer with respect to the domain** — a
relation, not an attribute; and **reading enters at an anomaly**, never at the whole artifact.

---

## TIER 3 · CLOSED — signed off, one line each

*Empty. Nothing has been method-checked and signed off yet.*

To close an item: read its method, and if you cannot poke a hole, say so. It gets a date, drops to one
line, and is never re-litigated.

---

## Reversal log — every verdict that has changed

Because the reversals are confusing and the fix is to make them auditable rather than to stop having
them.

| date | what | from | to | why | who caught it |
|---|---|---|---|---|---|
| 08-04 | Gate 3 | FAIL | **VOID** | the stability null outranks the p-value, per its own card | me |
| 08-04 | D-0 | FAIL | **VOID** | post-hoc power simulation: 38% | me |
| 08-04 | `separability()` | trusted | **wrong** | failed a known-answer task (author ID) | me |
| 08-05 | layer ratio | "vocabulary, 121% survival" | **reason retracted** | the shuffle test is invalid for model-internal measures | **you** |
| 08-05 | layer ratio | "unresolved" | **ruled out as h/m discriminator** | the granularity sweep confirmed the original conclusion for a valid reason | me |
| 08-05 | `purpose_breadth` | alive, sim-validated | **ruled out** | confounded with difficulty | simulation |
| 08-05 | sim S-2 | valid | **retracted** | its emitter never wired up | simulation, auditing itself |
| 08-05 | the triangle | three coupled problems | **a directed graph with a sink** | three edges exactly zero | simulation |
| 08-05 | ladder | "no measure ranks the rungs" | **five do; two are echo-free** | the auto-`VOCAB` label was over-firing | **you** |

**The pattern worth noting:** of nine reversals, **two were caught by you challenging a framing**, two
by the simulation auditing itself, and five by me applying a control I had not applied before. None
came from more data.

---

## Where the files live

| | |
|---|---|
| **this file** | the record. Read first |
| `TODO.md` | ideas not yet run |
| **`docs/TOOLS.md`** | **what is installed, what each thing does, and what it does not solve** |
| **`docs/theory/CURATOR_GUESSES.md`** | **your active guesses, extracted from my commentary, with status and what would test each** |
| `docs/method/` | LEDGER (every test in a table), CONTROLS (what a control licenses), DEVIATIONS |
| `docs/theory/` | the frame, the affect architecture, the triangle, the essays |
| `docs/gates/` | gate 0–3 material |
| `docs/sim/` | traffic with the Ghost Scale Simulation, both directions |
| `docs/design/` | what gets built next — SUCCESSOR, QUEUE, ENGINEERING_LOOP, DWELL_CORPUS |
| `docs/archive/` | superseded summaries. Kept, not read |
| `docs/STATE.md` | agent orientation after a context loss. Not for you |
| `results/*/VERDICT.md` | the primary record of each run, with its retraction banners |
