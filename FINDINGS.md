# FINDINGS — the method archive

**The method archive.** How each test was actually run, kept so a hypothesis row in `docs/theory/`
can be looked up rather than reconstructed. **It used to be the claims index; it is not any more** —
[`docs/theory/`](docs/theory/) holds the claims, organised by what we believe rather than by when we
ran it.

**Last updated: 2026-08-26.**

---

## How this file works

**Every entry states a hypothesis first.** A result without the question it was answering is not
readable a week later, and most of this file is now more than a week old in effect.

| | |
|---|---|
| **TIER 1 · LIVE** | still contestable, being worked on, or its method has not been examined. Full detail |
| **TIER 2 · SETTLED** | has a verdict file and passed its controls. Compressed to a few lines, grouped by outcome |

Promotion from 1 to 2 happens **when the curator has read the entry and responded to it at length** — his verbal response counts as processing it. **Nothing
is deleted** — a ruled-out result stays at one line. **Reversals live inside the entry they belong
to**, not in a separate log, so the current state and how it got there are read together.

**Outcome labels**

| | |
|---|---|
| **POSITIVE** | the effect is real and survived its controls |
| **RULED OUT** | measured properly, failed, and we know why |
| **VOID** | the test could not answer its own question. **Not a negative result** — no information either way |

## Definitions used in this file

Written out because this project borrows from stylometry, psychometrics, information theory and
interpretability at once, and the same word means different things in each.

| term | what it means here |
|---|---|
| **correlation strength** | how consistently two things rise and fall together. 0 = no relationship, 1 = perfect. Above ~0.4 is a strong relationship in this kind of data |
| **length-controlled** | the relationship that remains after the effect of how long the text is has been mathematically removed |
| **survives correction** | still significant after accounting for the fact that we ran many tests at once, so some would look significant by luck |
| **held out** | measured on data that played no part in choosing the measure or its settings |
| **echo** | the artifact simply repeating something the prompt said. Not a maker signal |
| **within-artifact variation** | how much a quantity wobbles between the beginning, middle and end of one piece, rather than its average |
| **register** | the *kind* of writing — an essay, a legal notice, ad copy. Register carries a whole bundle of word choices that follow from the category rather than from the person, which is why it imitates a maker signal so well |
| **legibility** | how recoverable the maker's *goal* is |
| **induction** | the prompt *causing* a feature without *containing* it. Distinct from echo, and harder to see |

---

## Where we are, in one paragraph

**2026-08-09.** Fifty-odd tests across four gates, three simulation batches, an eleven-family
replication and a standing integrity audit. **The flagship result, stated at its licensed
strength.** Within three machine-generated ladders, specified constraint dose reliably moves an
activation ratio and three linguistic features after a fair within-rung control (L23, L24). That
is a within-generator dose response. It is not yet a measure of human intent, depth, or decisions,
and specification recovery no longer corroborates it, since that score turned out to be carried by
lexical echo (L36). The recurring failure mode has been **criteria that could not do their own
jobs**; four were caught and each changed verdicts. The binding constraints now are **one reader's
readings as the only human ground truth** and **no corpus with one maker across different kinds of
artifact**, and the program's next unit of analysis is the individual recorded choice rather than
any per-artifact scalar.

---

## ⚠ Known weaknesses — open ones only

Resolved weaknesses have been folded into the entries they affected and are no longer listed here.

**1 · The human corpora now exist, and the weakness has changed shape.** It used to read *"we have
never had a controlled corpus of human artifacts."* **That is no longer true** — we hold 86 university
students writing the same essay three times, six years of a topic-controlled style-change task with
test labels, and 43,000 human-labelled emotion comments. **Two controlled human comparisons have now
been run and both came back negative or partial** (L5, L7).

**What remains is narrower and harder.** Every *positive* still rides on machine-written or
public-domain text: the ladder is one model's output, author identification is books. **And the thing
none of the human corpora supply is one maker across DIFFERENT KINDS of artifact**, which is the
diversity-of-conditions requirement that every dead thread arrives at — depth as a relation to a
domain, values needing many episodes, the polish that only slips when the performance is costly.

**2 · One human reader.** **Fifteen artifacts across two sessions, sixteen readings**, one person.
Those readings are the richest hypothesis source the project has, and no independent ground truth
has ever scored them, so the most generative evidence in the project has a sample size of one
unvalidated reader.

**3 · A criterion we trusted returned 335 components on pure noise.** Parallel analysis, applied
to raw high-dimensional activations, counts structure in data that has none. **Every number it
produced is void** (L8). The general lesson is now a hard rule in `CLAUDE.md`: **run every measure on
data whose answer you already know before running it on data whose answer you don't.** No other
criterion in this repository has been checked that way yet, and several should be.

**4 · The no-maker corpus is generated by the same model family we read with.** A shared-representation
artifact would look exactly like a human/machine difference. **Narrowed 2026-08-12 (L99): the
load-bearing cell is tested and clean** — the reader's null behavior on maker-less text is the
same whether its own family or the reasoning family generated it, so the no-maker *control* does
not carry the artifact. What remains untested is the positive direction: machine-versus-human
comparisons where the machine arm is home-family text; the second-family fiction corpus now
supplies the guard arm for those.

**5 · A scale gap remains in the affect directions.** Fitted on 12-word sentences, applied to
200-word windows. A worse version of this was caught and fixed; roughly a 16× gap remains and its
effect is unmeasured.

**6 · Feature banks may be the wrong tool, and we just installed one.** Simulation T-8 found that ten
hand-picked features combined reach near-perfect discrimination, while adding sixty more from a
generic bank gains a little on average and **loses more than it gains in the worst case**. Our
342-feature sweep is exactly the thing it warns about.

**7 · The similarity wing's circularity is broken at three points but two residues stand.**
The original Qwen-circularity (one maker family, a same-family eraser, a same-family top
reader) was dissolved by the second maker family, the independent eraser, and the mirror
arm: the advantage reverses with origin and follows the original maker through cross-family
rewriting (L165, L166). What remains: erasure is measurably partial (a surface classifier
still reads maker family at 0.58 against 0.50 chance after the strongest eraser), and both
surviving maker families are modern instruction-tuned models while both losing reader
families are older architectures, so instruction-tuning-era commonality is an uneliminated
ingredient of what "family" means here.

**8 · The prospective interface has no validated prompted or likelihood reader.** Both
failed powered validation at or near chance (L161), and a cheap probe of even the realized
edit carries almost nothing (0.048) — while the recorded fine-tuned grid (L82) shows
trained encoders reach 0.26 to 0.61 on the same task family, so the boundary belongs to the
reader families tried, not to the annotation. The anti-projection interface has floors, one
demonstrated-but-unvalidated instrument class (trained encoders), and no calibrated
zero-shot instrument.

---

# TIER 1 · LIVE

## L1 · Does a reader's low-order affective response fall as intent rises?

**Hypothesis.** *(The curator's.)* A language model carries lower-order, sensory-adjacent affective
processing near its input and higher-order, predictive processing deeper in. Human-made or
intent-dense text should provoke relatively **more** low-order response. So as specified intent
rises, the ratio of low-order to high-order affective activation should **fall**.

**Research context.** The two-layer affective architecture is the field's live reconciliation between
basic-emotion and constructed-emotion theories. **The application to reading a language model as an
instrument is not in the literature** — this is genuinely unclaimed ground.

**What we did.** Generated 50 articles from one model on 12 topics, varying only how many situational
specifications the prompt carried, with specifications drawn at random so no two prompts were alike.
Measured the ratio at two depths in a reading model. When the result came back marginal, generated
**100 more at fresh seeds and rotated topics** and re-ran once with every setting frozen.

**What we found.**

| | correlation strength | significance |
|---|---|---|
| first ladder, 50 artifacts | −0.275 | marginal, *p* = 0.053 |
| **held-out ladder, 100 artifacts** | **−0.247** | *p* = 0.013 |
| **held out, length-controlled** | **−0.405** | *p* < 0.0001 |

Reordering paragraphs or whole sentences leaves it untouched; scrambling five-word phrases costs a
full ladder's worth of effect. **It lives at or below the sentence and it needs local word order —
the only effect in this project that has ever required order.**

Length **hides** this effect rather than causing it: longer texts score higher and higher rungs are
slightly longer, so length pushes against it.

**Its established limits.** It is **not** a human-versus-machine discriminator: on that comparison it
keeps 99% of its size when every sentence is reordered, and commercial copy sits a quarter of the way
toward machine text — so on uncontrolled populations it reads **register**, not maker. It only means
anything where register is fixed by construction, which is what the ladder does.

**It survives the induction check** — the one that killed all three text-feature candidates. Learning
out-of-fold how well the identity of the drawn specifications predicts the ratio, and removing both
that and length, the relationship holds at **−0.26, *p* = 0.009**. Specification identity explains
0.39 of the ratio on its own, so it is entangled but not explained by it. **One awkward detail worth
keeping visible:** removing specification identity *alone* weakens the effect to −0.13 and it stops
being significant; it only firms up when length is removed as well. That is consistent with length
suppressing it, but it is not a clean pattern.

**Fair-control update, 2026-08-08 (L23):** under the rebuilt induction control with the dose removed from its regressors, the effect survives **all three ladders at −0.42 to −0.52, every *p* ≤ 0.0004** — stronger than the old numbers, which a dose-eating control had suppressed.

**Verdict: OPEN, replicated, and it has now passed every control we own** — held-out replication with
settings frozen, length, word-order granularity, noise ceiling, and induction. It does not become
POSITIVE for a non-statistical reason: **every rung is machine-written by the same model.** Whether it
does anything on human artifacts is weakness 1.

**How to read any process-side number from this project:** the simulation found that **how recoverable
the goal is governs how readable everything else is** — a threefold to tenfold difference — so a
process-side reading quoted without a legibility figure beside it is not interpretable. **The curator
disputes that it is the only governor**, and the argument, his counter-mechanism and the missing test
now live in [`docs/theory/THE_TRIANGLE.md`](docs/theory/THE_TRIANGLE.md) §8c rather than here.

## L2 · Three candidate measures from the feature sweep

**Hypothesis.** If ~350 published linguistic features are screened against known increasing intent,
and the ones that merely detect machine text are removed, something may remain that tracks intent
without tracking provenance.

**Research context.** Detecting machine text from linguistic features is **solved** — the literature
reaches near-perfect discrimination, and function words alone exceed 98%. **Detecting how much intent
was specified, within one generator, is not addressed anywhere we can find.** That gap is the whole
reason this is worth running.

**What we did.** Extracted 342 features per artifact, screened them against the ladder with a
correction for having run many tests, kept only those that **replicated on the held-out ladder**,
then removed any that also separate human from machine text, then any that echo the prompt, then any
that fail once length is accounted for.

**What we found.** 342 → 89 → **81 replicated** → 20 that are not machine-detectors → 6 that do not
echo → **3 that survive length.**

> **61 of the 81 replicated features were machine-detectors.** Without that filter we would have
> adopted the solved problem as our result.

Then we asked the harder question the echo check could not: does the prompt *cause* the feature
without *containing* it? The specifications are drawn at random, so we could learn out-of-fold how
well the identity of the drawn specifications alone predicts each feature, and test whether the
amount of intent still predicted what that could not explain.

| feature | length-controlled | after specification identity | after **both** |
|---|---|---|---|
| **conditional constructions** (*if*, *unless*) | +0.49 | +0.25 | **+0.18, not significant** |
| contractions | +0.37 | +0.03 | — |
| phrasal coordination | −0.25 | −0.18 | — |

**Specification identity alone explains most of the conditional effect** (0.54 of it). Contractions
collapse entirely — *"warmly, as though to someone you like"* contains no contractions and produces
them.

**Reversal, completed 2026-08-08 (L24):** under the fair control **all three revive, on all three ladders** — conditionals **+0.65 / +0.51 / +0.73**, contractions **+0.43 / +0.48 / +0.32**, phrasal coordination **−0.41 / −0.27 / −0.44**, nine of nine tests *p* ≤ 0.007. The kills were the dose-eating control's (L22). The contraction key that first "could not be re-tested" was Biber's uppercase tag `biber_CONT`, which a lowercase search pattern missed — a string-matching artifact stacked on a control artifact.

**Verdict: REVERSED (2026-08-09 relabel).** The original RULED OUT was the broken control's verdict
and cannot stand beneath a nine-of-nine reversal. Current state, per L24 above, is that all three
features track specified constraint dose under the fair control on all three ladders. What the
reversal does not license is any claim past the ladders, since dose is instruction count to one
generator, not human intent.

The one durable result is the funnel itself: **61 of 81 replicated features were machine-detectors**,
and the filter that removed them is now standard.

## L3 · Does the variation of the veneer carry the maker?

**Hypothesis.** *(The curator's, and his primary detector when reading by hand.)* Surface performance
costs effort, so it is the thing that slips. **Within-artifact variation** should carry the maker,
where the average does not.

**Research context — CORRECTED 2026-08-05, and the previous entry here was badly wrong.** This file
said within-document variance was "not a standard approach" and that "we found no established
treatment of it." **That is false, and it was load-bearing.** It is:

- **`burstiness`** — GPTZero's second headline metric is literally the standard deviation of
  per-sentence perplexity across one document. Our hypothesis, shipped commercially since 2023.
- **`unmasking`** (Koppel & Schler, 2004) — chunk a document, separate the chunks, and read the
  *shape of the degradation curve*. Canonical in authorship verification for 22 years.
- **intrinsic plagiarism detection** — find a passage anomalous relative to the rest of its own
  document, with no reference corpus.
- **PAN Style Change Detection**, a CLEF shared task running **continuously 2018–2025**.

**The bar is F1 ≈ 0.86** on PAN 2024's topic-controlled HARD split. Anything we produce below that on
a comparable setup is not a finding. **And PAN's HARD split is the topic-controlled human corpus this
entry says it needs** — it exists, it is free, and it has seven years of baselines.

Two further cautions from the same audit: PAN 2024 reports pure stylometry has *virtually
disappeared* in favour of fine-tuned transformers, and a 2025 study of hidden states as author
representations found **document-level mean pooling best**, which is evidence against the
within-window variance idea at the representation level.

**What is *not* pre-empted:** within-artifact variance of **probe activations** rather than of
perplexity or surface style. Burstiness does this with perplexity, PAN with surface style, nobody
found doing it with probe outputs. That is the narrow version worth keeping.

**What we did.** Computed all 342 features per window as well as per document, and compared what each
form finds.

**What we found.** Within-artifact variation finds **almost nothing on machine text** (1 and 0
surviving features across 150 artifacts) and **something on human text** (20 surviving on 35, of
which 7 are found by no document-level form).

**Two readings and we cannot separate them.** Either the mechanism is real — a machine has no
performance to slip — or it is register, since the human corpus contrasts essays against commercial
copy, and genres differ in how much they vary internally. **Register is the likelier reading.**

**Important limit:** the ladder **cannot test this hypothesis at all.** It is a claim about a human
performance decaying under cost, and every ladder artifact is machine-written. A null there is the
absence of the thing, not evidence against it.

**Verdict: OPEN, and now sharper.** Needs human artifacts with register held constant.

## L5 · Does anything move within one author as they revise?

**Hypothesis.** If revision adds intent, some measurable property of the text should change as the
same person redrafts the same essay — and because the maker, prompt, topic, register and genre are
all held fixed by construction, whatever moves cannot be explained by any of them.

**Research context.** This is the first controlled comparison on **human** text in the project's
history. Known weakness 1 has said since the beginning that every positive rides on machine-written
or public-domain text. ArgRewrite V.2 (86 university students, one prompt, three drafts each,
CC-BY-4.0) fixes it. The corpus is used in the literature for **revision-purpose classification**,
not for this question.

**What we did.** Extracted 342 linguistic features from every draft of every author. Compared draft 1
against draft 3 **paired within author**, so between-person variation contributes nothing, using a
signed-rank test with Benjamini-Yekutieli correction for having tested ~320 features. Then re-ran it
with every author's drafts **truncated to their own shortest draft**, so word count is identical
across the comparison by construction.

**What we found.**

| | features surviving correction |
|---|---|
| raw, drafts as written | **94 of 325** |
| **length-matched** | **17 of 315** |

**The raw result was length.** Drafts grow 27% (493 → 627 words) and every survivor was a *count* —
nouns, characters, words, sentences, punctuation. The pre-registered trap fired exactly as written.

**What survives length-matching is one coherent thing.** Words get **longer** (+0.06 characters per
word), **more polysyllabic** (+0.02 syllables per word), and **rarer** (word-frequency down 0.04);
**stopwords fall** (−5 per draft); reading-difficulty index rises (+0.38). Sign agreement 70–78%
across the 86 authors.

> **Within one author, at matched length, revision raises lexical sophistication.** Longer, rarer,
> fewer function words. That is a single factor showing up under six names.

**What it means.** This is a real within-human effect and it is **not** what the project is looking
for. It is a *polish* result — plausibly the "Surface" half of ArgRewrite's own annotation scheme,
which distinguishes Surface revisions (word usage, spelling, organization) from Content revisions
(claim, evidence, reasoning). **The corpus can settle that**, because 5,834 revisions are
hand-labelled Surface or Content with 0.71–0.92 agreement. If the effect is carried by
Surface-annotated revisions, we have measured polish and confirmed it. If it survives among
Content-only revisions, that is a depth signal on human text and the first one.

**Verdict: OPEN.** The Surface/Content split is the next test and it is the reason this corpus is
worth more than its size.

**A reporting error found in our own runner, and fixed.** It printed the count surviving *correction*
next to `0.05 × n_tested` as "expected by chance". Those are not comparable — the second is the
**uncorrected** expectation. Among 17 corrected survivors the expected false discoveries are at most
**0.85**, not 16. The first draft of this entry nearly called a real result nothing.

## L6 · Does the reader's internal state move as an author revises?

**Hypothesis.** The surface result in L5 is polish. If revision also changes something in *the
reader* — the low-order to high-order affective activation ratio, the project's only replicated
effect — that is a different quantity moving in the same corpus, and it is the one we care about.
His framing: *"I find surface-level feature analysis not as interesting. I'm wondering whether we can
go deeper — probing, mechanistic interpretability."*

**Research context.** The technique is a **probing classifier** on model activations; the field is
mechanistic interpretability. Reading activations to infer properties of an *author* has been done
(hidden states as author representations, 2025). Reading the **low-order/high-order affective ratio**
as a function of maker state has not.

**What we did.** Same instrument as the ladder, loci frozen, directions fitted identically. Scored
draft 1 against draft 3 **paired within author** across 86 authors. Pre-registered: pass needs
*p* < 0.01 **and** sign agreement above 60%, surviving length-matching. No direction predicted.

**What we found.**

| | ratio | median length |
|---|---|---|
| draft 1 | 0.7669 | 493w |
| draft 2 | 0.7822 | 562w |
| draft 3 | 0.7827 | 627w |

    draft 1 -> 3    +0.0100   sign agreement 58%   p = 0.053     <- the pre-registered test
    draft 1 -> 2                                   p = 0.0039
    change vs length change   -0.08 (p = 0.45)     <- not length

**Verdict: FAIL.** The pre-registered contrast misses both bars — *p* = 0.053 against 0.01, and 58%
sign agreement against 60%.

**What is underneath it, reported as suggestive and not as a finding.** Almost all of the movement
happens at the **first** revision and then stops: 0.7669 → 0.7822 → 0.7827. The first contrast is
*p* = 0.0039, which survives correcting for having looked at two. But it was not the pre-registered
primary, so it is **post-hoc** and cannot be claimed. The honest route is a fresh pre-registration on
a held-out corpus, not a promotion of this one.

**One thing worth noting even so, because it is a sign and not a magnitude.** The ratio moves **up**
with revision. On the ladder it moves **down** as specified intent rises. If both are real, revision
is not the same axis as specification — which would mean *revising* and *being told more about the
situation* are different operations on a text, and the instrument distinguishes them. That is a
prediction, from a *p* = 0.053 result, and it should be treated as one.

**And it is not length.** The change in ratio does not correlate with the change in word count
(−0.08, *p* = 0.45), which is the first time in this project that a length control has come back
uninteresting on the first attempt.

## L7 · Does the wobble inside a piece carry the maker, on human text?

**Hypothesis.** The curator's own primary detector when reading by hand is not how polished a piece
is but **how much the polish varies from beginning to end** — a writer reaching for a professional
register and then relaxing out of it. Keeping up a performance costs effort, so the performance is
what slips. Every measure this project has built takes a whole-document average and throws that
variation away.

**Research context.** Within-document variation is a mature field — GPTZero's *burstiness* is the
standard deviation of per-sentence perplexity, Koppel's *unmasking* dates to 2004, and PAN has run a
shared task on it since 2018. **What none of them measures is the variance of arbitrary features**,
and the version tried here — variance of 342 linguistic features, on human text with the maker held
fixed — is the one the literature has not pre-empted.

**What we did.** 86 students writing the same essay three times — **59 of whom clear the windowing
requirement and enter the analysis** (the recorded n; the undisclosed drop was an audit find, L26).
**Audit correction (L26): the hand-rolled Benjamini–Yekutieli ran its monotonicity pass in the wrong
direction** — strictly more conservative than BY, so "0 wobble survivors" was never established under
the pre-registered procedure; corrected and re-run 2026-08-08, raw p-values now persisted. **Outcome: the verdict stands — 0
wobble survivors and 12 average survivors under correct BY too. The conclusion was right; its
arithmetic was not.**
Split each draft into fixed windows,
computed each feature's **coefficient of variation** across windows — its wobble relative to its own
size — and compared draft 1 against draft 3, paired within author. Also computed the ordinary
**average** as a control, since anything the wobble finds that the average also finds is a windowing
effect rather than a variation effect.

**What we found. Nothing.**

    wobble    313 features tested   0 survive correction
    average   313 features tested   12 survive correction
    wobble-only: 0

**What it means.** On human text, with maker, prompt, topic and register all held fixed, **the
within-document wobble carries nothing the average does not.** This is the corpus the hypothesis
needed — the previous attempt was on machine text, where there is no performance to slip, so that
null was uninformative. This one is not.

**What it does not settle.** The claim is about a performance under *cost*, and revision may be the
wrong axis: a student redrafting an assignment three times may not be varying their veneer at all.
The remaining honest version is within-document variation across artifacts of **different kinds** by
one maker — which is the same diversity-of-conditions requirement everything else keeps arriving at.

## L8 · How many affective components are there, when nothing is imposed?

**Hypothesis.** *(The curator's.)* The field probes language models for six or seven emotion
categories because that is what a person can name and read off a face — *"let's not presume we can
pre-PCA if we can't identify the six. But if a PCA pops out a seventh, that makes the seventh really
interesting."* If the middle layers hold more structure than seven categories, everyone fitting seven
labels is fitting too few.

**Research context, and it is the sharpest part.** A literature check across four targeted searches
found: **Panksepp has never been probed in a language model — zero hits.** And **nobody has run an
unsupervised decomposition on activations of emotional text without a taxonomy baked in.** Every
decomposition in the field is applied to vectors *built from a labelled emotion word list*, so the
taxonomy enters before the maths — which is why they all recover a two-dimensional valence/arousal
circumplex. They cannot recover anything else. One paper does decompose raw activations at every
layer, and **never inspects how many components it kept or what they are.**

**What we did.** Took the corpus from the study that found the mid-layer peak, kept **only the
untouched human Reddit portion** — their other rows were machine-rewritten or synthesised — and
ignored their labels entirely, since those were assigned by a language model rather than people. Read
1,200 human utterances at every layer and decomposed with **no taxonomy at all**. The stopping rule
was fixed before running: keep components whose eigenvalue beats the 95th percentile of eigenvalues
from shuffled data of identical shape.

**What we found first, and it was wrong.** 49.3 components in the middle layers at 1,200 utterances,
against 7 for Ekman's six plus neutral. Verdict by the pre-registered criterion: RICHER.

**What we found when we checked it. The number was counting the sample, not the text.**

| | middle-layer component count |
|---|---|
| 1,200 utterances | 49.3 |
| **5,000 utterances, same model, every setting frozen** | **92.9** |

*Identical model, identical corpus, identical code. The only thing that changed is how much text was
read. Roughly doubling the count for roughly quadrupling the sample.*

| model, 1,500 utterances each | count |
|---|---|
| Qwen 0.5B · SmolLM2 360M · GPT-2 medium · Pythia 1.4B | 73.5 · 83.0 · 88.1 · 115.5 |

*Four more families. A 1.6× spread with no relationship to model size or family — no convergence on
anything.*

**Why, and it was predictable.** Parallel analysis prices each component against shuffled data of the
same shape, and **shuffling preserves the shape that causes the problem.** With more dimensions than
samples the eigenvalue spectrum is noise-dominated and the null does not correct for it. The
criterion is sample-size dependent by construction.

**And the deeper fault, which the criterion only exposed.** The decomposition ran on raw activations
of arbitrary Reddit text, so most of that structure is topic, syntax, length and register. **Nothing
in the method isolated affect.** It answered "how many dimensions of structure are in these
activations", not the question we asked.

**A correction to this entry's own research context, 2026-08-07.** The previous version cited *"a
Harvard group reporting roughly 10–17 effective dimensions for mid-layer affect using affect-specific
contrasts."* **A targeted search could not locate that paper**, across author, phrasing and method
variants. It should not have been written down as a number and it is withdrawn. **It was reported to
the curator as fact and that was an error.**

**What the literature does support, verified at source.** Three separate questions, three answers,
and the field routinely conflates them:

| question | answer | strength |
|---|---|---|
| **primary-process subcortical channels** | **7, with 9 the most anyone has defended** (Toronchuk & Ellis 2013 add power/dominance and disgust, on review evidence rather than stimulation and lesion work). LeDoux argues for 5 and no anger circuit | nothing in neuroanatomy reaches 27 |
| **distinguishable reportable affective states** | **20–30, converging near 25** | the strongest result raised the offered word list from 34 to **80** and the count did **not** move — 19 to 32 across subjects, median 25, recovered against brain data on held-out timepoints |
| **dimensions in the variance-explained sense** | **2 to 4** | Russell's 2, and Han & Adolphs' 3 from the same videos Cowen & Keltner got 27 from |

**Verdict: VOID. The test could not answer its own question**, and the criterion that produced its
number has been shown to fail on our own data. Nothing here is evidence either way about how many
affective components exist.

**What replaced it ran on 2026-08-07 and returned VOID in all five runs — and the audit (L26) found
the instrument itself quadruple-broken (G106): its "corrected participation ratio" is not the cited
estimator and collapses on scale-outlier channels (recorded counts of ~1.0 beside parallel-analysis
counts of 25-38); its bi-cross-validation argmin sat on the max_k=40 cap in 135 of 138 fits, a
boundary recorded as a rank; its shuffled-label gate demanded the statistic *shrink* below a
threshold that was under the statistic's arithmetic floor in every recorded run, so VOID was decided
before the shuffle ran; and its frozen VAD reference was written from memory — 18 of 28 entries
differ from the real NRC-VAD by more than 0.1, so the replication gate was judged against a
fabricated reference. The five VOIDs stand, but VOID-for-the-right-reason holds in at most two.**
`run_affect_dimensions.py` isolates affect the way the field
isolates it — average activations over many topics per emotion, then subtract the mean across
emotions, so the taxonomy selects which items to average and never supplies a basis. Human-labelled
categories, three counting criteria including two with a real stopping point, and three controls
including **the same pipeline on an untrained model of identical shape.** It gates on reproducing the
published valence and arousal correlations before any count is read.

## L10 · How much of the prompt's specification survives into the artifact?

**Hypothesis.** *(The curator's, against our own verdict.)* Machine text written *with* purpose was
recorded RULED OUT. He disputed it on grounds of manipulation strength: *"we should start at the
extremes — three pages of different motivations stacked on top of each other."* If the effect is real,
**strengthening the manipulation should strengthen it.**

**What we did.** For each artifact, ask whether its true specification can be picked out from **48
decoys matched on topic**. Reported as bits recovered and as win rate. Run on three ladders of
increasing manipulation strength, with length band-targeted by rejection sampling on the extreme one
(the band held in absolute terms — 1.9% spread — **but the rank-space check failed at +0.414**, and
`score.json` records that honestly; the prose here previously claimed achieved control — audit L26).

| ladder | specifications per prompt | n | win rate vs 48 decoys | correlation with rung | *p* |
|---|---|---|---|---|---|
| first ladder — 50 artifacts, **40 scorable** (rung 0 carries no specification) | 0/1/3/6/10 | 40 | 52.5% | 0.205 | 0.20 |
| held-out, 100 | 0/1/3/6/10 | 80 | 66.3% | 0.366 | 0.0008 |
| **extreme, 75** | **0/2/10/30/60** | 60 | **91.7%** | **0.435** | **0.0005** |

*Chance is 2%. "Correlation with rung" is how strongly recovered information tracks how many
specifications the prompt carried.* **Audit note (L26): at the extreme ladder's rungs 30 and 60 the
decoy pool is exhausted and those contests are not 49-way — see L19's correction.**

**Not echo, not length.** On the extreme ladder, correlation with prompt-echo is **−0.236** —
negative — and with length **+0.061**.

**Verdict: OPEN and strong.** The effect scales with the manipulation exactly as predicted, which
means the earlier ruled-out verdict was premature rather than wrong. **Owed: the no-maker control**,
which the layer correlation passed and this has never been given.

## L12 · Does the per-layer intent correlation transfer across architectures?

**Hypothesis.** The only measure that has replicated is the per-layer correlation between specified
intent and affective signal. **If it reads something real about the text it should appear in other
models; if it reads an artifact of one architecture it should not.**

**What we did.** Ran it on **11 model families from 0.35B to 3B parameters**, on three ladders and the
no-maker control, with 48 matched random directions per layer and both length and specification
identity removed.

| | |
|---|---|
| ladder runs | **25 across 11 families — 18 survive** |
| **no-maker runs** | **11 — re-adjudicated (audit L26): the DEAD verdicts were forced by a broken gate. Under the computable rule, 5 of 11 fire — at luck-level rates overall, concentrated in the flagship** |
| fails everywhere | **gpt2-large**, on all three ladders |
| weakest family | GPT-2 (medium 2/3, large 0/3, xl 0/1) |
| strongest | Qwen and SmolLM2 |

**The failures cluster by family, not by scale.** gpt2-large sits between pythia-410m and pythia-1.4b
in size, and both of those survive.

**Verdict: OPEN — and the control claim is retracted (audit L26, 2026-08-08).** "Zero false
positives" was manufactured: on the no-maker corpus no specifications exist, the induction term is
NaN, and the survivor gate required `abs(nan) > 0.2` — **DEAD was the only reachable verdict, a
criterion that could not fail.** Re-adjudicated under the computable rule (beats its null + strength
+ length), the eleven runs fire at **2.9% of layers, roughly what the three stacked cuts supply by
luck** (16.9% beat their 12-direction nulls; ~15% would by chance). The exception is the flagship:
**Qwen-1.5B fires at layers [5, 7, 13, 17, 21], overlapping its held-out-ladder survivors three of
five where chance gives under one — and layer 21 fires on all three ladders *and* on maker-less
text.** A label-permutation null (G107) decides whether that is clustered luck or a real label leak.
**What does not transfer is the location** — the surviving layers move by model and by corpus, so
every headline layer number in this project is Qwen-specific.

## L13 · Does affect-concept agreement rise or fall as intent is specified?

**Hypothesis.** *(The curator's, pre-registered.)* *"You might also have more agreement in the late,
**if the goal is clear.**"* So coherence — how much the eight affect concepts point the same way at a
layer — should **rise** with rung at late depths, and the middle should be convergent regardless. **A
conditional prediction, not a flat one.**

**What we did.** Split every ladder artifact into windows, projected the eight affect concepts at every
layer, and computed agreement among them per layer. Averaged into early, middle and late thirds and
correlated against rung. Three ladders, same model, settings frozen.

| band | first ladder (50) | held-out (100) | extreme (75) |
|---|---|---|---|
| **early** | **−0.694** (*p* < 0.0001) | **−0.640** (*p* < 0.0001) | **−0.726** (*p* < 0.0001) |
| **middle** | +0.136 (*p* = 0.35) | +0.118 (*p* = 0.24) | −0.149 (*p* = 0.20) |
| **late** | **−0.356** (*p* = 0.011) | **−0.253** (*p* = 0.011) | **−0.612** (*p* < 0.0001) |

*Correlation between rung — how many specifications the prompt carried — and agreement among the eight
affect concepts at that depth. Negative means the concepts scatter more as intent rises.*

**Verdict: REJECTED, and the direction is inverted.** Coherence **falls** with specified intent, not
rises, and it does so at both ends.

**The useful part is the null.** The middle band does not move in any of the three corpora, while early
and late both drop hard and replicate. **That is a dissociation between the middle and the rest, found
by a test that was not looking for one.** Whether it reflects the noisy middle the architecture
predicts, or an insensitivity of this coherence measure at that depth, this run cannot say.

**And a second prediction died in the same run.** The layer where affect magnitude peaks sits at
**layer 2 in every rung of every ladder** — it does not move with intent. **The moving numbers reported
earlier (layers 14, 19, 23) were the layer that best *correlates* with rung, which is a different
quantity; the runner conflated them and that was my error.**

**Cross-family replication, 2026-08-07 — and the clean story does not survive it.** The same readout
on three more families, three ladders each:

| band × rung correlation | Qwen-1.5B | SmolLM2-360M | gpt2-medium | pythia-1.4b |
|---|---|---|---|---|
| early | −0.69 / −0.64 / −0.73 | **+0.67 / +0.57 / +0.56** | +0.74 / +0.65 / +0.74 | +0.18 / −0.07 / −0.41 |
| middle | +0.14 / +0.12 / −0.15 | +0.46 / +0.33 / +0.17 | **+0.73 / +0.64 / +0.77** | +0.49 / +0.46 / +0.31 |
| **late** | **−0.36 / −0.25 / −0.61** | +0.59 / +0.46 / +0.28 | **−0.36 / −0.31 / −0.53** | **−0.58 / −0.46 / −0.60** |

*Correlation between rung and agreement among the eight affect concepts, per depth band, for the
three ladders in each model family.*

**Four things move.** The inversion is **Qwen-specific** — SmolLM2 shows the *predicted* positive
relationship at every band. The Qwen dissociation — "the middle does not move" — **does not
generalise**: the middle moves strongly in gpt2 and pythia. The only near-universal pattern is that
**late-band coherence falls with rung in three of four families**. And the depth-of-peak verdicts
split: FIXED in Qwen, **SHIFTS — the peak moves deeper as rung rises — in SmolLM2 and pythia**, NOISE
in gpt2. **So the earlier rejection of "deeper intent needs deeper machinery" was premature: the claim
is family-conditional, not false.**

**Audit corrections, 2026-08-08 (L26), and they cut deep.** **The coherence statistic cannot measure
what this table says it measures.** The eight fitted directions sum to exactly zero by construction
(global centring, equal sentences per concept), so eight-way agreement is geometrically impossible —
the recorded number is a projection onto an arbitrary axis that exists only through noise in the
eight four-sentence fits, and its sign flipped in 11 of 20 refit simulations. Every cell in the table
above, and the coherence half of every depth-sweep middle verdict, is read from that instrument:
**VOID-INSTRUMENT until a statistic valid under the sum-zero constraint replaces it (G105).** And
**the SHIFTS verdicts were an argmax artifact**: two static near-tied loci — the embedding layer and
layer 4 — with opposite rung correlations swap rank by under 4% of amplitude. A crossover between
fixed loci, not a peak moving deeper, at p = 0.058 which gated nothing. **The revival of "deeper
intent needs deeper machinery" is withdrawn to VOID-INSTRUMENT**; verdict logic fixed (v2: prominence,
significance, a TIED-LOCI category), all four families re-queued. **Regenerated the same day:
TIED-LOCI on every ladder in both families — the crossover reading confirmed by the fixed
instrument.** One inoculation worth recording:
SmolLM2's all-bands-positive pattern was machine-labelled FLAT by a taxonomy hole — the prose here
quoted the numbers and routed around the wrong token, but the JSONs carried it.

**Verdict unchanged for the universal claims — REJECTED — and the family-conditional versions are
OPEN.** The readout code itself goes to the audit before any of this hardens: a sign convention or a
band-boundary artifact could manufacture exactly this kind of family difference.

## L14 · Does the affective-response profile across depth carry any information about the maker?

**Hypothesis.** *(The curator's.)* A model reconstructs human affective structure at three depths, so
the *shape* of its affective response across layers should be a fingerprint of that structure — and
should differ between text with a maker and text without one.

**Method.** For each artifact, project the eight affect concepts at every layer, average the absolute
projections into a per-layer signal, and price each layer against matched random directions. Detect
peaks in the resulting profile with a prominence criterion fixed before the run. **Run on three
ladders and on the no-maker corpus — 36 runs across nine model families from 0.35B to 3B.** The
no-maker corpus is the control: it is text with no maker, so any profile feature that appears there
cannot be about a maker.

**What we found.**

| | |
|---|---|
| **peak location, ladder vs no-maker** | **identical or within one layer in every model** (gpt2-medium differs by one on the extreme ladder — audit L26) |
| shape | **27 of 36 runs UNIMODAL** |
| multimodality | **gpt2-large** (5–6 peaks) and **pythia-410m** (2–3), in their no-maker runs too — **and pythia-1.4b's no-maker run alone is bimodal** while its three ladder runs are unimodal (audit L26) |
| **peak depth across families** | **layer 2 of 29 in Qwen-1.5B, layer 47 of 49 in gpt2-xl** — 3, 4, 5, 8, 13 elsewhere |
| layers beating the random null | **all of them, in 28 of 36 runs** |
| middle-band verdict | 16 NOISY, 20 COHERENT — no consistency |

**Verdict: RULED OUT.** The depth profile is a property of the architecture. **It is identical with and
without a maker in every model tested**, which is as clean as this control gets.

**Two things it settles beyond the original question.** The **bimodal** profile this project once
reported was a two-model artifact — gpt2-large and pythia-410m — and does not generalise. And **the
peak sits anywhere from the second layer to the forty-seventh depending on family**, with no relation
to size or depth, which means **no claim naming a specific depth transfers across architectures.**

**What survives is the per-layer *correlation* with specified intent (L12), not the profile.** How much
a layer responds is architectural; how much its response tracks the maker is not.

## L15 · Is the component-count criterion measuring anything?

**Hypothesis.** The unsupervised decomposition that returned 49 affective components, then 93 on the
same data at a larger sample, was using a criterion that could not do its job.

**Method.** Read activations once at 4,000 utterances, cache them, then subsample at six sizes so every
criterion sees identical text and only the sample size varies. Five criteria — parallel analysis,
eigenvalue > 1, 90%-of-variance, cross-validated reconstruction, and participation ratio — plus a null
in which every dimension is independently permuted across utterances, which destroys all cross-dimension
structure and must return nothing.

**What we found**, across three model families:

| criterion | growth from smallest to largest sample |
|---|---|
| cross-validated rank | 14.3× · 3.2× · 2.8× |
| parallel analysis | 6.2× · 4.0× · 3.2× |
| 90% of variance | 5.4× · 5.5× · 4.1× |
| eigenvalue > 1 | 1.5× · 2.4× · 1.5× |
| **participation ratio** | **1.0× · 1.6× · 1.6×** |

*A 27-fold increase in sample size, on identical text. A criterion measuring the text should not move.*

**And the null fails outright.** Parallel analysis returns **160 components on 600 rows of pure Gaussian
noise and 335 on 4,000** — data with no structure whatsoever. Participation ratio separates the two
cleanly: **1,109 on noise against 6.9 on real activations.**

**Verdict: VOID, all three runs.** Not biased — broken. **Every number that criterion produced is
withdrawn**, and the participation ratio is the only one of the five that behaves.

## L16 · Do function words separate specified maker states, at power?

**Hypothesis.** Function words — pronouns, articles, prepositions, auxiliaries — are produced
non-consciously and are topic-independent, so texts written under different specified states should
separate on their function-word distribution. **This was recorded VOID at 38% power**: the original ran
on ~380-word texts, where a first-person rate of 13.8 per 1,000 words gives **five tokens**, and the
statistic divides by a within-group variance made almost entirely of Poisson noise on five counts.

**Method.** Compute the rate per 1,000 words of 130 closed-class function words for each artifact,
then classify which rung it came from, cross-validated, against a chance rate of 1/5. Run at three
pooling levels — single artifacts, and artifacts concatenated in threes and fives within a rung — so
the token count and the sample size trade off visibly rather than being chosen. **Each ladder is run
separately**, because rung schemes differ between them and pooling the corpora would let the
classifier identify the rung by identifying the corpus. **The runner's own default did exactly that
pooling until 2026-08-08 (audit L26) — and it wrote every run to one filename, so the held-out and
extreme raw files were overwritten before their only commit. The held-out and extreme rows below
survived only in this text.** Both defects fixed (single-corpus default, per-corpora filenames,
corpora recorded inside the JSON); both arms re-run 2026-08-08 to restore primary records. **Restored: held-out 0.330/0.333/0.350,
extreme 0.467/0.600/0.600 — matching the destroyed rows to the digit** (seeded pooling), so every
number in the table below has a file behind it again.

**What we found.**

| ladder | max specifications | single artifacts | pooled in 3s | pooled in 5s | chance |
|---|---|---|---|---|---|
| first, 50 | 10 | 0.320 | 0.400 | 0.300 | 0.200 |
| held-out, 100 | 10 | 0.330 | 0.333 | 0.350 | 0.200 |
| **extreme, 75** | **60** | **0.467** | **0.600** | **0.600** | **0.200** |

*Cross-validated accuracy at predicting which rung an artifact came from, from function-word rates
alone. Chance is 0.200 because there are five rungs.*

**Verdict: SEPARATES on all three, and it scales with the manipulation.** 1.6× chance at ten
specifications, **2.3× at sixty without pooling and 3.0× pooled.** That is the same scaling the
specification-recovery measure showed, arrived at through a completely different channel — one reads
the model's internals, this reads closed-class word rates with no model at all.

**The void was a power failure and the redesign fixed it, but not the way the power analysis
predicted.** Pooling was supposed to raise the first-person token count; **the ladder is written in
the third person and has essentially no first-person content at all** — 0 to 17 tokens even pooled.
**The separating information is in other function words entirely**, which means the original
first-person-rate diagnosis was right about that design and wrong as a general precondition. **My
verdict gate imported it and had to be corrected.**

**Owed before this counts as a positive: the induction control.** Rung is how many specifications the
prompt carried, so the classifier may be reading style the prompt *induced* rather than a maker state.
**That control killed all three text-feature candidates last time and this has not had it.**
**The control ran 2026-08-12 (L94): SURVIVES on the held-out and extreme ladders in the fair
within-rung form, COLLAPSES on this table's weakest corpus** — the license is granted where the
manipulation is strong, and the first ladder's cell is a power casualty, not an exoneration.

## L17 · The founding question, re-scored on the extreme ladder

**Hypothesis.** Some measure ranks five rungs of specified intent. **This was voided in 2026 on its own
pre-registered ceiling** — rung and output length correlating at 0.40 against a 0.40 limit. The audit
found that ceiling used a *rank* correlation to gate a question about *magnitude*, and the actual
length spread is 4.2% of a 1,400-word median.

**Method.** Score the extreme ladder — 0/2/10/30/60 specifications, length held by rejection sampling —
with the low-order to high-order affective ratio, reporting the relationship raw, with length removed,
with the identity of the drawn specifications removed out-of-fold, and with both removed. **The last
column is the induction control that killed all three text-feature candidates.**

| | strength | *p* |
|---|---|---|
| raw | **−0.565** | < 0.0001 |
| length removed | **−0.524** | < 0.0001 |
| specification identity removed | −0.192 | 0.100 |
| **both removed** | **−0.207** | **0.074** |

*Correlation between how many specifications the prompt carried and the reader's low-order/high-order
affective ratio. Negative was the prediction.*

**What we found. The raw effect is more than twice the size of the held-out ladder's** (−0.565 against
−0.247) — **and it does not survive the induction control** (−0.207, *p* = 0.074), where on the
held-out ladder it did (−0.26, *p* = 0.009).

**The asymmetry is probably in the control, not in the effect.** The induction check regresses the
ratio on *which specifications were drawn*. The held-out ladder draws from a pool of 30; the extreme
ladder draws from a pool of 60. **With twice the regressors and fewer artifacts, the control
removes far more, and it would do so whether or not induction is what is happening.** That is a real
confound in the control itself and it has not been characterised.

**Two other things fell out.** The scorer's own length check fires at +0.414 and prints *"length still
varies with rung"* — **it is the same scale-free statistic on the same 1.9% spread**, so that check
inherits the flaw the audit found — the honest phrasing everywhere is *band-targeted*, not
*controlled*, since the rank-space criterion failed even where the absolute spread is 1.9%. And the **acceleration** prediction — that the effect should
steepen at the top of the ladder, which would be evidence for values as a constraint on the goal
mixture — **is not supported**: +0.104 on the lower half, −0.007 on the upper.

**Verdict: OPEN, and the void is lifted without the question being answered.** The design limitation
that voided it was misdiagnosed; the effect is large and length-robust; **and whether it survives
induction now depends on a control whose aggressiveness scales with the specification pool.**
**Resolved by L23:** the fair within-rung control removes the pool-scaling confound entirely, and the
extreme ladder survives it at **−0.516, p < 0.0001**. This entry's worry was the control's fault,
exactly as suspected.

**Resolved, 2026-08-08 (L23).** Under the within-rung control the extreme ladder survives at **−0.516, *p* < 0.0001** — the failure was entirely the control's, whose dose leak here was −0.778.

## L18 · Does depth move when the domain moves? — a pilot, and it measured the wrong thing

**Hypothesis.** *(The curator's.)* Depth is a property of the writer **with respect to the domain** —
a relation, not an attribute. **Falsifier: depth moves where domain moves.**

**Method.** Three authors in the book corpus who wrote across genuinely different kinds — Darwin's
scientific treatises against the *Voyage of the Beagle*; Twain's novels against *Innocents Abroad*;
Wollstonecraft's *Vindication* against her Swedish letters. For each maker, compare the distance
between two works of the **same** kind against two works of **different** kinds, with the maker held
fixed in both. Plus a control that should not move — **function-word rates, which carry identity**,
because the person did not change.

| maker | "depth" within-kind | across-kind | ratio | identity within | across | ratio |
|---|---|---|---|---|---|---|
| Darwin | 0.0004 | 0.0002 | **0.46** | 0.0236 | 0.0115 | **0.49** |
| Twain | 0.0010 | 0.0017 | **1.68** | 0.0477 | 0.0810 | **1.70** |
| Wollstonecraft | — | 0.0003 | — | — | 0.0664 | — |

**Verdict: VOID, and for a reason the pre-registration did not anticipate.**

**The control moved exactly as much as the measure.** Darwin 0.46 against 0.49, Twain 1.68 against
1.70. Whatever separates these works is not specific to the quantity being tested — it is whatever
separates any two texts by one person written for different purposes. **That is the GENRE outcome,
pre-registered as a void, arriving disguised as ATTRIBUTE because the verdict logic checked the
makers-majority condition before checking the control.**

**And the deeper fault: the column labelled "depth" was not depth.** It was the affect-projection
profile — the eight affect concepts projected at every layer — which is the only reader-side quantity
this project has. **Labelling it depth was reaching for the hypothesis's vocabulary and attaching it
to whichever instrument happened to be built.** The curator caught it by asking how we were measuring
depth on Darwin, and the honest answer is that we were not.

**What this does establish.** The design needs the identity control to be **decoupled** from the
depth measure before it can answer anything, and two usable makers cannot do that. **It is a design
finding rather than a result about depth**, and it makes the corpus question more urgent rather than
less — but it also shows the corpus is downstream, because a better corpus read by a non-depth
measure answers nothing.

## L19 · Specification recovery passes its hardest control, and doubling the difficulty barely moves it

**Hypothesis.** If the artifact really carries information about the specification that produced it,
then (a) breaking the artifact–specification link must destroy the effect, and (b) making the
discrimination twice as hard should not.

**Method.** Two runs. **The control:** give each artifact *another artifact's real specification* and
score it the same way — everything is preserved except the link between artifact and specification,
so the win rate must collapse to chance. **The harder test:** score against **96** topic-matched
decoys instead of 48, halving the chance rate.

| run | decoys | chance | win rate | correlation with rung | *p* |
|---|---|---|---|---|---|
| **shuffled specifications**, held-out ladder | 48 | 2.08% | **1.3%** | −0.298 | 0.007 |
| extreme ladder | 48 | 2.04% | 91.7% | +0.435 | 0.0005 |
| **extreme ladder** | **96** | **1.03%** | **90.0%** | **+0.454** | **0.0003** |

**What we found. The control collapses to chance exactly** — 1.3% against an expected 2.0%. **And
doubling the decoys cost 1.7 points**, from 91.7% to 90.0%, while chance halved. **The effect is not
a discrimination artifact.**

**One oddity worth keeping visible.** Under shuffling the correlation with rung is **significantly
negative** (−0.298, *p* = 0.007) where it should be nothing. The likely reading is that higher-rung
artifacts are *more constrained*, so a wrong specification fits them **worse** — which is a
second-order confirmation rather than a problem, but it was not predicted and it should not be
reported as if it had been.

**Verdict: OPEN, under active suspicion — two of its three newest controls flag it.** The strict
echo restriction fires its kill (below), and **the no-maker control awards it wins where nothing is
true (L32: 3 of 36 against 0.37 expected, *p* = 0.006)**, on top of the decoy-degeneracy bound.
Best-supported-in-the-project status withdrawn; its numbers are not quoted as recovery until the
graded-echo curve (G113) and a wider pool (G108) adjudicate.

**Second audit hit, 2026-08-08 (L26): decoy-pool exhaustion.** The extreme ladder's pool holds 60
specifications and its top rungs *are* 30 and 60 of them. At rung 60 the complement is empty — **all
96 "decoys" are the same bare prompt** — and at rung 30 every decoy is the one 30-spec complement
reordered. **Half the extreme-ladder items were never a 97-way contest**, the printed "chance 1.03%"
does not apply to them, and their bits pin at the 6.6 cap by construction. **The clean rungs (2 and
10) carry the effect alone: +0.529, p = 0.0027** — so a rung-bits relationship survives on the
non-degenerate half; what the exhaustion manufactured was the 97-way framing and the top-rung curve.
The runner now counts distinct decoy sets, appends `-DEGENERATE-RUNGS` to any verdict they touch, and
scores exact ties as losses (they counted as wins). A wider pool is the real fix (G108). **And the
echo restriction the pre-registration made mandatory — "survives the echo restriction" — was never
implemented**; it exists now (`--no-echo`) and ran the same evening.

**The echo restriction fires the pre-registered kill.** Method: score each artifact only against
specifications sharing **zero content words** with its text — the strict reading of the docstring —
decoys size-matched, 96 decoys, held-out ladder. **Only 50 of 100 artifacts retain any unechoed
specification at all** (rung 1 keeps 5 of 20 — a single honoured specification almost always shares
a word), and on those, recovery collapses: correlation with rung **−0.15, p = 0.31** (was +0.37,
p = 0.001 unrestricted), win rate **8%**, bits near floor at every rung above 1. **This is one of two
things.** Either the measure's information is carried by lexical echo — or **honouring a
specification inevitably shares its words**, in which case zero-overlap exclusion removes exactly the
executed specifications and the strict test is over-harsh by construction. The unrestricted run's
near-zero echo–bits correlations (+0.10 / −0.24) sit with the second reading; the pre-registration
named this condition, so the record shows the failure either way. **G113 separates the readings:
graded overlap thresholds, and scoring on function words only, where echo is impossible.**

**Resolution limit found by the audit, 2026-08-08.** Per-item bits are **saturated**: 35 of 40, 57 of
80 and 52 of 60 artifacts sit at one of the two extremes, because the per-token re-normalisation
exponentiates log-probability differences over ~1,400-word texts. **"Bits recovered" is effectively
binary at these lengths; the honest statistic is the win rate**, and the rung correlations should be
read as rank-coded win/lose rather than a graded information measure.

**A queue defect found in the Fable audit pass, 2026-08-07.** The 96-decoy stage writes the **same
file** as the 48-decoy run, so `results/spec_recovery/ladder3.json` now holds the 96-decoy result and
the 48-decoy raw file is gone — its numbers survive only in this entry. And with no output guard the
stage re-ran on **every** loop pass at ~20 GPU-minutes each; three passes burned an hour recomputing a
result that existed. Guarded now; *same-output-path-different-parameters* goes to the audit as a
class.

## L20 · Two queue stages that did not test what they were queued to test

**Recorded because a stage that runs to completion and reports a verdict is more dangerous than one
that crashes.**

**The induction control on the extreme ladder did not run.** The stage passed `--corpus ladder3` to a
runner that **has no `--corpus` argument at all.** It ran its hardcoded default and reproduced the
held-out ladder's numbers exactly — raw −0.247, length-removed −0.405, both-removed −0.259
(*p* = 0.009), verdict SURVIVES. **Those are real numbers and they are a re-run of a result we already
had.** The extreme ladder's induction figure comes from a different runner and is −0.207, *p* = 0.074.

**And the function-word result still has no induction control of its own**, which is what that stage
was supposed to supply. Classifying rung from function words could be reading style the prompt
*induced* rather than a maker state, and **the control that would settle it does not exist yet.**

**The refusal re-run used the threshold that voided it.** The original was VOID because its pass
condition — *generated exceeds the human mean on at least 3 of 5 components* — has a **50%
false-positive rate by arithmetic**: five independent comparisons under a null of no difference is
five coin flips, and P(at least 3 of 5) is exactly 0.5. **The re-run reports PASS with 3 of 5, which
is the modal outcome of a fair coin.** Raising the sample from 5 to 20 does nothing, because the
sample was never the problem.

**Verdict: both VOID.** Neither is a result. **The queueing error was mine in both cases** — one
stage assumed an argument that does not exist, the other assumed the void was about power when the
diagnosis on record says it was about arithmetic.

## L21 · Does a reader's state move more erratically over machine text? — the void, resolved

**Hypothesis.** *(V2, voided at three artifacts.)* A reader's affective state should wobble more
between consecutive windows on text with no maker than on ladder text.

**Method.** For each artifact, project the eight affect concepts at every layer per window; take the
size of the step between consecutive windows; displacement variance is the spread of those steps
within one artifact, **normalised by its own mean step** so a text that merely moves more does not
read as more erratic. Permutation test against the no-maker corpus, 5,000 label shuffles.

| corpus | n | displacement variance | *p* against no-maker |
|---|---|---|---|
| first ladder | 50 | 0.209 | 0.958 |
| held-out ladder | 100 | 0.216 | 0.711 |
| extreme ladder | 75 | 0.209 | 0.919 |
| **no-maker** | 36 | 0.210 | — |

*Mean within-artifact variability of the reader's affect trajectory. The no-maker corpus is text with
no maker; identical values there mean the wobble carries nothing about a maker.*

**Verdict: REJECTED, cleanly, at n = 261.** The four corpora are indistinguishable to two decimal
places. This is the informative null the three-artifact void could not supply, and the third
confirmation of the reader-side lesson: **a reader's state does not carry the signal; ratios between
the reader's own layers on the same text do.**

## L22 · The induction control's regressors contain the dose — found by the integrity audit

**Hypothesis.** The induction control — regress a measure on *which specifications were drawn*,
out-of-fold, and test what survives — removes only specification *identity*, leaving the effect of
specification *count* (the rung) intact to be tested.

**Method.** Read the control's construction directly. Its regressor matrix is the binary indicator of
drawn specifications: one column per specification in the pool, one row per artifact.

**What we found. The row-sum of that matrix IS the rung.** An artifact at rung 6 has exactly six ones
in its row. A ridge model over those columns can recover the dose from the sum alone — so **what the
control removes is not chosen by the design; it is chosen by the regulariser.** With light shrinkage
it eats the entire rung-linked component, including any true effect. And on the extreme ladder it is
worse by construction: **the pool holds exactly 60 specifications, so every rung-60 artifact draws all
of them** — the top rung's regressor block is constant, perfectly collinear with membership of the
top rung.

**What this changes about three recorded results.**

| | before | after |
|---|---|---|
| **L1** — the ratio survives induction on the held-out ladder (−0.26, *p* = 0.009) | survival | **survival against a control that can absorb the true effect — stronger evidence than the design intended** |
| **L17** — the extreme ladder fails induction (−0.207, *p* = 0.074) | read as the effect failing | **expected by construction and uninterpretable as evidence against** — the control is at its most absorbent exactly there |
| **L2** — the three text-feature candidates killed by this control | read as induction | **the control cannot distinguish *induced by which specs* from *responds to how many***, so the kills are sound but the mechanism stated for them is not established |

**The fix, and it is cheap:** centre the indicator within rung — equivalently, test whether *which*
specifications were drawn predicts the measure **orthogonally to how many**. That is the control the
design intended. Queued as the sharpened G75.

**Verdict: CONFIRMED defect in the control's construction; no verdict changes sign, but two verdicts
change meaning.** Found by reading, verified by arithmetic, and it is the most useful thing the audit
day produced.

## L23 · The fair induction control — the effect survives all three ladders, and gets stronger

**Hypothesis.** L22 showed the induction control's regressors contain the dose (row-sum of the
spec-indicator = rung), so every prior induction verdict was set by the regulariser. **If the effect
is real, it should survive a control with the dose arithmetically removed; if the old control was
eating it, the effect should come back *stronger* under the fair one.**

**Method.** `run_induction_v2.py`: centre the specification-indicator matrix **within each rung
stratum**, so it carries only *which* specifications were drawn given *how many*. Out-of-fold ridge
prediction from the centred matrix, removed along with length; old control run alongside. The
smoking-gun diagnostic is each control's own prediction correlated with rung — **the dose leak,
measured directly.** Per-artifact rows saved, so re-analyses are CPU-only.

| ladder | old control's dose leak | old both-removed | **fair both-removed** | *p* |
|---|---|---|---|---|
| first (n=50) | −0.476 | −0.386 (*p* = 0.006) | **−0.484** | **0.0004** |
| held-out (n=100) | −0.450 | −0.259 (*p* = 0.009) | **−0.422** | **< 0.0001** |
| **extreme (n=75)** | **−0.778** | −0.207 (*p* = 0.074) | **−0.516** | **< 0.0001** |

*"Dose leak" is the correlation between the control's own prediction and rung — how much of the
treatment the control was absorbing. The fair control's leak is +0.10 / +0.06 / −0.02: ~zero by
construction, as designed.*

**What we found.** Everything L22 predicted, quantitatively. The old control was predicting the dose
— at **−0.778** on the extreme ladder, it was mostly a rung detector. **Under the fair control the
effect survives on all three ladders at −0.42 to −0.52, every *p* ≤ 0.0004, and is *stronger* after
the control than the old numbers suggested** — including on the first ladder, whose raw correlation
was only marginal (*p* = 0.053).

**What it re-adjudicates.** **L17's extreme-ladder "failure" was entirely the control's** — with the
dose removed from the regressors, the strongest manipulation shows the strongest controlled effect,
which is the dose-response shape the founding question wanted. **L1 now survives a fair control, not
merely a conservative one.** And **L2's three killed candidates were killed by the dose-eating
control** — they are owed a CPU-only re-test under the fair one (G100) before their deaths stand.

**Verdict: OPEN and the strongest result in the project.** The low-order/high-order ratio tracks
specified intent after removing length and within-rung specification identity, replicated across
three independently generated corpora at three manipulation strengths.

## L24 · All three of L2's executed candidates revive under the fair control — nine of nine

**Hypothesis.** L2's three text features were killed by the induction control that L22 showed contains
the dose. **A feature genuinely tracking dose would have been executed exactly like an induced one**,
so the deaths were suspended pending a re-test under the within-rung fair control.

**Method.** CPU-only (`run_fair_features.py`): feature values from the cached 342-feature extractions,
specifications from the verified reconstruction, and the same within-rung centring as L23 — remove
length and *which-specs-given-how-many*, then test the residual against rung.

| feature | corpus | raw | old control | **fair control** | *p* |
|---|---|---|---|---|---|
| conditional constructions | first ladder | +0.692 | +0.224 (n.s.) | **+0.649** | **< 0.0001** |
| conditional constructions | held-out | +0.579 | +0.180 (n.s.) | **+0.513** | **< 0.0001** |
| conditional constructions | extreme | +0.780 | +0.105 (n.s.) | **+0.727** | **< 0.0001** |
| contractions | first ladder | +0.435 | +0.112 (n.s.) | **+0.433** | **0.0017** |
| contractions | held-out | +0.484 | +0.005 (n.s.) | **+0.479** | **< 0.0001** |
| contractions | extreme | +0.354 | −0.069 (n.s.) | **+0.319** | **0.0053** |
| phrasal coordination | first ladder | −0.531 | −0.039 (n.s.) | **−0.406** | **0.0034** |
| phrasal coordination | held-out | −0.349 | −0.132 (n.s.) | **−0.268** | **0.0070** |
| phrasal coordination | extreme | −0.547 | −0.073 (n.s.) | **−0.442** | **< 0.0001** |

*"Old control" is what L2 used — the dose-eating regressors. "Fair control" removes length and
within-rung specification identity. Signs match L2's original directions.*

**Verdict: REVIVED — all three, on all three ladders, nine of nine tests significant, every sign
matching L2's original directions.** The artifact-side route L2 closed is open: **three published
linguistic features track specified intent through a fair control**, including on the extreme
ladder's doubled specification pool.

**Both caveats from the first report closed the same day.** The missing contraction key was
`biber_CONT` — Biber's own uppercase tag, which a lowercase search pattern missed; one-line fix, and
the feature revives on all three ladders. And the extreme ladder's stale quarter-corpus cache was
rebuilt (75 artifacts, 13 min) — far from checking the revivals, it produced the strongest single
result in the set (conditionals **+0.727**). Held-out confirmation, not contradiction.

**Originality, his call 2026-08-08:** *"It seems like no one else is tracking layer ratio with respect
to intent — it feels like an obvious hit."* Recorded as believed-original; **a prior-art sweep (G102)
is owed before any public claim.**

## L25 · The noisy middle, isolated at last — and rejected

**Hypothesis.** The middle of the model is high-activity and low-coherence (G31) — a claim that rode
along with the bimodal depth profile, died with it, and was **never tested on its own**.

**Method.** `run_noisy_middle.py`, CPU-only over the 36 saved depth sweeps (11 families × up to 4
corpora): rank each layer's affective signal (activity) and cross-window coherence within its own
model, split the layers into thirds, and ask whether the middle third sits **above** the outer thirds
on activity while sitting **below** them on coherence.

**Verdict: REJECTED.** The predicted signature appears in **2 of 25 maker-corpus sweeps** — both the
same small model (pythia-410m). The modal pattern is the **opposite: a *quiet* middle** (12/25 — all
of gpt2, the larger pythias, Qwen 3B), with the Qwen and SmolLM families flat. **And the no-maker
control shows the same distribution (6/11 quiet)**, so whatever middle structure exists is
architecture, not anything about makers. One more layer-location claim that is family-conditional
rather than universal — the running theme of the cross-family replication.

**Same-day caveat (L26):** the audit voided the coherence statistic (sum-zero constraint, G105),
which is the "low-coherence" half of the NOISY criterion here. **The activity half — and therefore
the quiet-middle finding, which is signal-rank only — stands**; the 2/25 NOISY count can only shrink.
**And it did — extended the same evening over the completed 11-family matrix: 2 of 33 maker runs
NOISY, 18 of 33 QUIET, no-maker distribution unchanged.** The majority pattern is the claim's
opposite.

## L26 · The adversarial audit — sixteen claims verified, fifteen confirmed

**Hypothesis.** *(His, standing: "search the entire repo for problems we're not aware of.")* Does the
battery contain more criteria that cannot fail, silent overwrites, or claims the saved data
contradicts?

**Method.** Subagent fleet, conservatively sized: four read-only finders (reader-side mathematics;
decomposition and spec recovery; docs versus data; corpora, features and queue), 34 raw findings
deduplicated, the 16 most severe handed to an independent adversarial verifier instructed to refute
each. **15 confirmed, 1 refuted**, 18 lower-severity findings passed through unverified.

**Confirmed, by class.** *Criteria that could not fail:* the no-maker verdict gate (NaN — corrected
in L12); the affect-count shuffle gate (threshold below the statistic's arithmetic floor in every
recorded run). *Instruments measuring something else:* the coherence statistic (sum-zero directions
— G105); SHIFTS-by-argmax (withdrawn in L13); the participation-ratio "correction" (not the cited
estimator; collapses on scale-outlier channels; its bi-cross-validation pinned at the cap in 135 of
138 fits); the VAD reference written from memory (G106). *Degenerate contests:* extreme-ladder decoy
exhaustion (corrected in L19). *Wrong arithmetic:* the argrewrite Benjamini–Yekutieli ran backwards
(corrected in L7, re-run). *Destruction and races:* v4's single-filename overwrite destroyed two of
three raw files (L16, restored); the feature cache was written incrementally under its final name, so
a concurrent audit committed prefix statistics three times, including at HEAD (atomic writes and
completeness checks now in place); the same cache silently froze three days of empty extractions
behind a bare `except` (validation added).

**Also from the sweep, the clearances.** Every corpus manifest matches disk exactly; zero duplicate
texts across ladders; the PAN splits are leak-free and the macro-F1 implementation matches the
official evaluator to 1e-12. **G99 resolved:** the 78-second re-score was honest determinism — same
code path, same inputs, bit-identical floats — though for that very reason it verified nothing; a
real re-check must vary something. **And one orphan surfaced:** a PAN *easy-split* run from 08-06
recorded **macro-F1 0.969 against a published best of 0.959** — the 342-feature bank beats the
published bar on the split where topic is available. The easy split is not topic-controlled, so the
win may ride topic; recorded beside L11 as split-conditional rather than overturning its rejection.

**What this means.** Five of the six deepest hits are one failure class, the one this file already
names: **a criterion that cannot fail is not a control.** They were found by evaluating saved outputs
against the code that produced them — something no amount of re-running does, which is why the audit
caught what the battery could not. Same-day: eight runners repaired, four readout re-runs and the
pre-registered echo restriction queued, instrument rebuilds and the permutation null opened as
G105–G108.

## L27 · Is the first layer binary salience? No — it already knows which emotion

**Hypothesis.** *(His, asked directly: "the initial layer is binary saliency, do you think?")* Layer
0 should carry *whether* affect is present at near-full strength while carrying *which* emotion at
chance — a double dissociation.

**Method.** `run_binary_salience.py`: per layer, two cross-validated linear probes on 1,113
human-labelled GoEmotions comments — emotional-versus-neutral (balanced binary, chance 50%) and
27-way which-emotion among the emotional items (chance 3.7%).

**Verdict: NO DISSOCIATION — and the failure runs in the informative direction.** Layer 0 carries
*category* at **8.4× chance** (31.2% of 27-way) — the first layer is not category-blind, which the
salience hypothesis requires. Presence at layer 0 read as a coin flip (48.7%), but on 40 neutral
items only.

**Powered re-run, same evening (G21b: 500 neutral items, n = 1,573).** The presence curve was upside
down at low power: **layer 0 is the presence *peak* — 0.637, the best in the entire model** — and
category still peaks at layer 10 with layer-0 category unchanged at 8.4× chance. **So his intuition
is half right, and it is the architecturally interesting half: the strongest
is-there-affect-here signal in the model sits at the very first layer.** What fails is only the
blindness clause — layer 0 knows *which* emotion too, so early presence is not a *separate*
salience stage. NO DISSOCIATION stands; "binary" falls, "salience-first" survives. Feeds G20a/G20b
with the corrected ordering: presence earliest, category mid.

## L28 · The fair-control flagship outside Qwen: the sign is a family property

**Hypothesis.** L23's flagship — the early/late affective-activation ratio tracking specified intent
through the fair within-rung control — should replicate in other reader families if it reads makers
rather than one architecture.

**Method.** `run_induction_v2.py --model` on the held-out ladder for three non-Qwen families, same
relative loci (7% and 76% of depth), same fair control, model-tagged output files.

| family | first ladder | held-out | extreme |
|---|---|---|---|
| Qwen-1.5B (flagship) | **−0.484** ★ | **−0.422** ★ | **−0.516** ★ |
| gpt2-medium | **+0.552** ★ | **+0.514** ★ | **+0.377** ★ |
| SmolLM2-360M | +0.010 | +0.014 | **+0.298** ★ |
| pythia-1.4b | +0.201 | +0.163 | +0.204 |

*Fair-control correlations between the early/late activation ratio and specified intent, per reader
family per corpus. ★ = p < 0.01. The dose-leak diagnostic behaved in all twelve runs (old control
leaks up to +0.81; fair control ≤ |0.30|).*

**Verdict: REJECTED as universal — and completed 2026-08-08 evening across all three corpora, the
picture sharpens into something better than a mirror.** All non-Qwen arms record DEAD because the
pre-registered rule requires Qwen's negative direction. But **gpt2-medium runs positive
three-for-three at Qwen's strength** — a replicated phenomenon, not a fluke — **SmolLM2 joins the
positive side exactly where the manipulation is strongest**, and pythia trends positive n.s. on all
three. **No family shares Qwen's sign. The flagship's negative direction — the one the verdict rule
enshrines — is the outlier, not the norm.** Where the ratio reads intent outside Qwen, it rises with
it. Same lesson as the per-layer map, now with teeth: the measure is real in at least three
architectures and **the pre-registered direction was an artifact of which family we explored first**
(G112 characterises what the fixed depth fractions straddle per family).

**The map at eleven families, updated as cells land (2026-08-09).** Qwen runs negative at **all
three of its sizes** — 0.5B (3/3 negative, ★ on the extreme), 1.5B (3/3 ★), and now 3B (−0.376,
*p* = 0.007 on the first ladder) — **the only negative family, everywhere it is measured.** The
positive camp: gpt2 strong at medium and large (5/5 ★), **null at xl on all three ladders** (the
extreme arm landed at +0.05 n.s.); SmolLM2 positive at both sizes and on two corpora at 1.7B
(+0.345, *p* = 0.014 and +0.229, *p* = 0.022); pythia positive at 410m, fading through 1.4b to zero
at 2.8b (−0.115 n.s.). Two patterns stand: **the sign is a family constant, and the biggest member
of gpt2 and pythia goes quiet while SmolLM2's larger size holds its sign** — so the fade is a
top-of-family phenomenon with one exemption, and the characterisation work (G112) has three facts
to explain: the sign, the fade, and the exemption. Three cells still running.

## L29 · The essays' two information-theory claims, first contact — both miss as operationalised

**Hypothesis.** From the essays, untested until tonight: machine text lacks the Kolmogorov
complexity "inherent to biological constraint satisfaction," and generation is "a regression toward
the mean — the average fish."

**Method.** `run_compression_ladder.py`, CPU: (1) per-artifact incompressibility (lzma output/input
bytes) against rung with length partialled, three ladders; (2) distance from each artifact's
342-feature vector to the pooled z-scored centroid, machine (held-out ladder) versus human (student
essays).

**Found.** Incompressibility does not track specified intent: +0.04 / +0.05 / +0.19, all n.s. — 60
stacked specifications add no measurable description length. And the centroid test came back
**backwards: machine text sits *farther* from the mean than human text (23.2 vs 15.3)** —
though register and length are uncontrolled in that comparison and the books group was empty on the
first pass (store-mapping bug, fixed, re-queued). **Means:** whatever the ladder's specifications
add, it is not lzma-visible structure; and "the average fish" needs a register-matched test before
it survives contact — as run, the *human* essays hug the centroid.

**Books arm landed overnight: no Kolmogorov gap.** Human long-form and machine ladder text are
equally compressible at matched length — **0.4552 versus 0.4562** — with no-maker text slightly
*less* compressible than either. Both essay claims stay missed with the clean comparison in.

## L30 · No detected relationship between placement quality and scale, at eleven points

**Hypothesis.** *(His, §8: "Is there evidence of worse models having more poorly placed emotional
concepts?")* If placement improves with capability, placement is learned and the amplification
story needs a scale story.

**Method.** `run_placement_scale.py`, CPU over the 11 saved subspace matrices: per family, the
sharpness of the early two-band break and the lawfulness of alignment decay (R² of log-alignment on
layer distance), each correlated with parameter count.

**Found: NO DETECTED SCALE RELATIONSHIP (2026-08-09 relabel; was "ARCHITECTURAL").** Break
sharpness against size, rho +0.05 (p = 0.89); decay lawfulness, rho +0.40 (p = 0.22); eleven
families, 0.35B–3B. **Means exactly that and no more.** At n = 11 an undetected relationship is
not proof that training scale is irrelevant, and the old label claimed the stronger thing. What
survives for §8's build is the weaker, honest form, which is that placement quality gave no sign
of tracking capability in the one range measured.

## L31 · The early break is universal; the rotation composes everywhere except Qwen

**Hypothesis.** G42's two-band break (found in four families) should hold in the seven
audit-surfaced runs; and if one lawful transform carries the affect subspace through depth (G44),
alignment should *compose* — align(i,k) predictable from align(i,j)·align(j,k).

**Method.** `run_subspace_bands11.py`, CPU over the 11 alignment matrices: best two-way split per
family; composability R² over all layer triples.

**Found.** The best split sits at the **earliest boundary in all eleven families** (layer 1 by this
runner's indexing — an off-by-one against the original's "layer 2" convention is flagged, not
resolved). And composability splits by family, hard: **pythia 0.88–0.92, gpt2 0.78–0.84, SmolLM2
0.45–0.58, Qwen 0.20–0.30.** **Means:** the very-early break is universal — the one
location claim in the project that transfers — and **the depth transform is lawful enough to fit in
pythia and gpt2 but not in the flagship family.** G44's fit-the-transform build should start in
pythia; **Qwen, where all the flagship results live, is the wrong place to look for a lawful
rotation — one more way the flagship family is the outlier (after L28).**

## L32 · Specification recovery awards wins on maker-less text — the third strike

**Hypothesis.** The no-maker control the measure never had (owed explicitly in the theory
afterword): on text with no maker, where a randomly assigned "true" specification set is exactly as
false as its 96 decoys, the contest should win at the 1-in-97 chance rate and recover ~zero bits.

**Method.** `run_nomaker_specrec.py`: every no-maker artifact gets a pseudo-true set (rung 2, 6 or
10) plus 96 disjoint decoys — a ladder item's contest with no true candidate anywhere in it.

**Verdict: READS-STYLE.** The pseudo-true set wins **3 of 36 contests against an expected 0.37**
(binomial *p* = 0.0061), and mean recovered bits sit at 0.89 rather than near zero. **Means:** the
contest can award wins for something that is not executed specifications — on three artifacts the
arbitrary set fit maker-less text better than 96 equally false alternatives. Three artifacts is a
thin base and the pseudo-prompt template differs from the ladder's; but **this is the second live
control to flag the measure in two days** (after the strict echo kill, L19), on top of the decoy
bound. Specification recovery's evidence now runs through the graded-echo curve (G113) and a wider
pool (G108) before any of its numbers are quoted as recovery.

## L33 · The reader carries a provenance prior — framing alone moves the affective read

**Hypothesis.** *(The paper's H1, run in the reader model.)* If a one-line frame — "The following
passage was written by a person." versus "…by an AI." — changes the reader's affective activations
on identical text, the reader has a provenance prior, and every unframed measurement in this
project sits on the neutral setting of a knob nobody had turned.

**Method.** `run_provenance_framing.py`: 30 held-out-ladder artifacts, every 200-word window read
under both frames (token-length matched), paired per artifact: the flagship early/late ratio and
mean affect magnitude.

**Verdict: FRAMING-MOVES.** The ratio shifts **+0.0066 under the AI frame** (paired Wilcoxon
*p* = 5.6e-9) and affect magnitude drops −0.0006 (*p* = 1.9e-9). **Means:** tiny in absolute terms,
unambiguous in sign — **the reading machinery itself responds to claimed provenance**, the
model-side analogue of granting text a teacher (G67). The early-relative shift under the AI frame
is the opposite direction of a human's engagement collapse, which is worth its own thought.
Replication arms on the other two ladders run today.

## L34 · The convergence curve exists — recovery sharpens with works, flattens, and leaves a residual

**Hypothesis.** *(§8's disagreement with the impossibility proofs, stated measurably: G60.)*
Recovery of a maker should improve with more artifacts by that maker, approach an asymptote, and
leave the residual the theorems demand — *"report the asymptote, not just the slope."*

**Method.** `run_author_convergence.py`: function-word centroids per author from k = 1, 2, 3
reference books; held-out 1,000-word chunks classified by nearest centroid; 20 random splits.

**Verdict: EARLY PLATEAU, one channel (2026-08-09 relabel; this does not estimate an asymptote).**
Accuracy 0.541 → 0.614 → 0.604 against a 0.20 chance rate. Recovery rises from one to two
reference works and does not improve at three. That is a plateau in one author-identification
channel on five authors, and three points cannot locate an asymptote. The limit-framing language
the entry used to carry claimed more than the curve shows.

## L35 · Goal-guess convergence discriminates nothing as built — and maker-less text converges hardest

**Hypothesis.** The virus paper's H2 and the flattened-intent claim collide head-on: H2 predicts
independent readers *scatter* when reverse-engineering a machine artifact's goal (no latent reward
to converge on), while the corporate-text account predicts dense specified intent produces *high*
agreement. The ordering across groups was to discriminate them.

**Method.** `run_reader_convergence.py` v2: eight independent local-model readings per artifact
("in one sentence: what was the maker trying to achieve?"), convergence as mean pairwise
content-word overlap of the answers, ten artifacts per group. (v1 returned all-empty answers — the
thinking model spent its whole token budget on its hidden channel; fixed with think-off, a real
budget, and empty-answer guards. The student-essay group was lost to a file-extension assumption
and returned n = 0.)

| group | convergence |
|---|---|
| no-maker text | **0.285** |
| machine, ten stacked specifications | 0.222 |
| machine, zero-or-one specification | 0.219 |
| human books | 0.184 |

*Higher = the eight goal-guesses share more content words.*

**Verdict: the discriminator did not discriminate — instrument, not answer.** The pre-registered
label fires on its letter (dense-machine ≥ human), but the spirit fails twice: there is **no dose
response at all** (0.222 versus 0.219 across a ten-specification gap), and **maker-less text
converges hardest**, which neither account predicts. **Means:** as operationalised, agreement
between goal-guesses reads *topical narrowness* before it reads latent intent — no-maker texts
afford one obvious surface description, and rich human prose affords many true ones. The collision
between the two accounts remains live and untested. The fix is named (G114b): topic-matched groups,
graded answer-similarity instead of token overlap, and the essays-path repair.

## L36 · The graded echo curve — specification recovery is an echo detector

**Hypothesis.** The strict echo kill left two readings: the measure's information is carried by
lexical echo, or honouring a specification inevitably shares its words and the strict test is
over-harsh. The graded curve separates them: if honouring-inevitably-echoes were the story,
partially-echoed specifications should still carry signal.

**Method.** `run_spec_recovery` at 96 decoys on the held-out ladder, scoring restricted to
specifications whose content-word overlap with the artifact is ≤ 100% (unrestricted), ≤ 50%, ≤ 25%,
and 0%; plus the strict arm replicated on the first ladder.

| overlap allowed | n | correlation with rung | win rate |
|---|---|---|---|
| everything (unrestricted) | 80 | **+0.344** (*p* = 0.002) | 61% |
| ≤ half | 75 | +0.041 (*p* = 0.73) | 37% |
| ≤ quarter | 62 | −0.132 (*p* = 0.31) | 24% |
| zero | 50 | −0.147 (*p* = 0.31) | 8% |

*The first-ladder strict arm lands negative (−0.430, p = 0.046, 5% win) — below-chance recovery on
unechoed specifications.*

**Verdict: ECHO-CARRIED.** The signal does not degrade gracefully as echo is restricted — **it
vanishes between full and half overlap** and trends negative below that. With the no-maker control
already awarding it wins where nothing is true (L32), the conclusion is one sentence:
**specification recovery, as built, is a lexical-echo detector whose echo happens to track dose.**
The dose-tracking is real but it is a property of the *echo*, not of recovery. Every number the
measure produced is re-read under that light; the honest instrument here would measure echo
directly and own it.

## L37 · The provenance prior replicates on all three corpora

**Hypothesis.** L33's framing effect — telling the reader identical text is machine-made shifts its
affective read — was one corpus; the standing rule says near-armed results replicate before they
harden.

**Method.** Same paired design, thirty artifacts per corpus, both remaining ladders.

**Verdict: FRAMING-MOVES, three for three.** The ratio shift is +0.0071 / +0.0066 / +0.0097 and the
affect-magnitude drop −0.00064 / −0.00063 / −0.00075, every arm at *p* < 2×10⁻⁸ paired. **Means:
the provenance prior in the reading machinery is now replicated and controlled** — small, fixed in
direction, and present on every corpus we can ask. Unframed measurements sit on a neutral knob;
disclosure is not affect-neutral even for a machine reader.

## L38 · The presence peak is not an architecture fact — the address lesson again

**Hypothesis.** G21b found layer 0 is the model's strongest is-affect-present signal in the home
family; if that is an architecture fact it should hold in other families.

**Method.** The powered probe (500 neutral items) on gpt2-medium and pythia-1.4b.

**Verdict: family-specific, like every address claim.** gpt2-medium's presence curve is nearly flat
(layer 0 at 0.628 versus a 0.636 peak at layer 8); pythia's peak sits *late* (0.657 at layer 19,
layer 0 at 0.598). Category still far above chance at layer 0 in both (8.8× and 8.7×), category
peaks mid. NO DISSOCIATION everywhere. **Means: salience-first was a home-family fact.** The
one address claim that looked like it might travel does not — the address umbrella's
mostly-no hardens.

## L39 · Within-artifact activation variance: the human series moves, the machine one is flat

**Hypothesis.** The §1 heuristic's untried operationalisation (HH-3, pre-empted by nobody): the
within-artifact variance of the reader's own affective series should be higher for human long-form
than machine ladder text (the flat-machine-polish signature), and might track dose.

**Method.** `run_activation_variance.py`: the early/late ratio per 200-word window as a positional
series, variance at matched series length (subsampled to six windows), books versus both machine
ladders, plus rung-versus-variance within ladders.

**Verdict: HUMAN-MOVES; RUNG-FLAT.** Books' median within-artifact variance is 0.0102 against the
machine ladders' 0.0065, one-sided *p* = 0.0024; variance does not track dose within machine text
(−0.14 / −0.17, both n.s.). **Means: the first positive instrument number the primary-detector
heuristic has ever had** — the human affective series moves and the machine one is comparatively
flat, exactly the signature the theory names. Register and genre ride along uncontrolled, so this
is one corpus-pairing away from hardening, not there.

## L40 · The flagship's no-maker concentration — the permutation test could not decide leak from luck

**Hypothesis.** The audit's open question: the home family's false fires on maker-less text overlap
its own surviving layers — real label leak, or clustering luck?

**Method.** `run_nomaker_permutation.py`: 2,000 label permutations over the saved per-artifact
signal matrix; joint-rule pass count and overlap with the ladder survivor set, conditioned on the
observed direction-null passes.

**Verdict: UNDECIDED (2026-08-09 relabel; was "CLUSTERED-LUCK").** Observed 7 joint layers against
a null mean of 1.9 (*p* = 0.095) and overlap 4 against 0.79 (*p* = 0.089). Failure to reject
leakage is not evidence for luck, and the old label converted a non-result into an exoneration.
The honest state is that the experiment could not distinguish a real label leak from clustering
luck at this power. The survivor list keeps its layers only in the sense that nothing convicted
them; the concentration stands as an open liability against the flagship family, and any claim
that leans on those layers inherits it.

## L41 · Low-visibility features carry *who*, high-visibility features carry *what* — the pottery prediction, first pass

**Hypothesis.** *(The archaeology harvest's structural claim, G87 — Gosselain's stage-differentiated
signal.)* Features acquired early and invisible to the maker (function words, syntactic reflexes,
punctuation habits) should carry deep identity; visible, easily-copied features (lexical richness,
readability) should carry the situation instead.

**Method.** `run_feature_visibility.py`: partition the feature bank by named visibility patterns;
leave-one-out nearest-centroid on two tasks — author identification (34 books, ten authors, two
chunks each) and draft-stage separation (student essays, three drafts).

| task | low-visibility features | high-visibility features |
|---|---|---|
| author identification (chance ~0.10) | **0.779** | 0.382 |
| draft-stage separation (chance 0.33) | 0.302 | **0.477** |

**Verdict: STAGE-DIFFERENTIATED — a clean double crossover on the first pass.** The invisible
habits identify the maker at eight times chance while barely seeing the situation; the visible
features do the reverse. **Means:** the pottery import is not an analogy — the partition carries
exactly the structure it predicts, and it hands the leakage channel a principled feature split for
free. One corpus pairing, crude partitions by name-pattern; one bad test away.

## L42 · Lexical sophistication also rises inside content-labelled revisions

**Hypothesis.** *(PD-28, the highest-value unrun row in the traces file.)* The one controlled human
comparison found revision raises lexical sophistication (L5). If that effect lives in
surface-labelled revisions it is polish; **if it survives among content-labelled revisions, it is a
depth signal on human text — demonstrated rather than argued.**

**Method.** `run_revision_purpose.py`: the ArgRewrite annotation workbooks (172 parsed; two-sheet
aligned-sentence schema with purpose labels at two levels; the files carry a broken dimension
record that silently truncates naive readers — found and handled). Sentence-level sophistication
deltas (word length, rare-word rate, stopword rate) per purpose class, ArgRewrite's own
surface/content taxonomy.

| class | n | word-length delta | rare-word delta |
|---|---|---|---|
| surface-labelled revisions | 1,347 | +0.038 | +0.0035 |
| content-labelled revisions | 364 | +0.034 | **+0.0054** |

**Verdict: CONTENT-REVISION-ASSOCIATED LEXICAL CHANGE (2026-08-09 relabel; was "DEPTH-SIGNAL").**
The sophistication shift holds at full strength among content-labelled revisions, and the
rare-word component is stronger there. What that licenses is exactly the title. What it does not
license is "the first measured depth signal on human text", because the result shows lexical
change travelling with a content label, not recovery of problem-directed choice structure. The
discriminating test is the choice-recovery design now at the head of the program, with these
features demoted to explanatory variables. If recovery disappears once revisions are matched on
lexical sophistication, this was another sophistication measure.

## The family-sign map is complete — 33 of 33 cells (folds into L28)

Final cells: gpt2-large +0.227 (*p* = 0.0499) on the extreme — six of six positive; SmolLM2-1.7B
+0.283 (*p* = 0.014) — starred on two corpora; pythia-2.8b −0.061 n.s. — zero at the family's top.
And the depth-readout matrix completed under v2 rules: **FIXED peaks in every remaining family —
zero SHIFTS anywhere in eleven families.** The map's standing sentence is unchanged and now rests
on every cell: the sign is a family constant, no family shares the home family's negative, and the
positive camp's largest members go quiet.

**The per-block correlation matrix also completed (folds into L12): 33 of 33 ladder cells.** The
eight new cells: Qwen-3B SURVIVES on both remaining ladders (12 and 3 surviving blocks), SmolLM2-1.7B
both (9 and 5), pythia-2.8b both (8 and 2), gpt2-xl one survivor on the first ladder and DEAD on
the extreme — completing gpt2's family-wide weakness (large 0/3, xl now effectively 0-1 surviving
blocks across corpora). L12's totals update: **of 33 ladder runs across eleven families, 25
survive**, failures still clustering in the gpt2 family, surviving blocks still moving by model and
corpus — the address never transfers, the tracking usually does.

## L43 · PD-1's first run scored zero essays — two instrument faults, caught by the n field

**Hypothesis.** None adjudicated — this is an instrument record. The definitional polish/depth test
(PD-1) appeared to complete and returned NO-ASYMMETRY.

**What actually happened.** Two faults stacked. The small-window feature cache was built at the OLD
window size while stamping the new one in its own metadata — the window override set a module
global after Python had already bound the old value as the function's default argument, so every
essay got 1–2 windows instead of 5–10 and the runner's ≥4-window filter passed **zero essays**.
Then the verdict logic, lacking a zero-data guard, fired its no-difference verdict on an empty
comparison — the criterion-that-cannot-fail class again, in a runner built after the audit that
named it. A third fault surfaced in the same landing window: the revision-homogeneity runner (G81)
found zero authors because the draft folders disagree on file stems (draft-1 files carry a
`draft1_` prefix; draft-3 files do not), and crashed on the empty set.

**Fixes, all applied before any valid run existed.** Window size now passed explicitly at the call
site; the runner exits without writing its summary below 12 usable essays, so the produces-guard
refires after the cache rebuild; the depth-side feature list was remapped from descriptive words to
the actual Biber tag codes (v1 matched 3 features of ~20 intended — also caught by a printed
count); draft stems normalised before pairing. The zero-window cache and the empty verdict are
quarantined (`argrewrite_w80_broken_wbind.json`, `positional_polish/v1_zerowindow/`). Both stages
re-queued. **PD-1 remains unrun; no result of any kind exists for it yet.**

## L44 · The block geography survives pooling; the flagship ratio does not

**Hypothesis.** *(G127, from the neural-analogues review: extraction choice systematically biases
layer-wise conclusions — Hadidi 2025 — and every profile this project owns mean-pools.)* If the
early/late story is an artifact of mean pooling, it should move under last-token and max pooling.

**Method.** `run_pooling_falsifier.py`: the home model re-read with all three poolings — the mean
over token positions (ours), the last token only, and the elementwise maximum. Two quantities per
pooling: the per-block affect-work profile (correlated across poolings — does the *shape* move?),
and the flagship early/late ratio against ladder rung (does the *dose statistic* move?).

| pooling | profile r vs mean | peak block | ratio-vs-rung | p |
|---|---|---|---|---|
| mean (ours) | — | 2 of 28 | −0.045 | 0.78 |
| last token | 0.992 | 2 of 28 | +0.218 | 0.18 |
| max | 0.979 | 2 of 28 | −0.335 | 0.034 |

*Columns: correlation of the 29-block profile with the mean-pooled profile; which block peaks;
correlation of the early/late ratio with induction rung; its uncorrected p.*

**Verdict: POOLING-BOUND — for the ratio; the geography is pooling-invariant.** The profile keeps
its shape (r ≥ 0.98) and its peak block under every pooling — so the address results, all measured
under mean pooling, do not hang on that choice. The ratio-vs-rung statistic lands in a different
(sign, significance) class under each pooling: null-negative, null-positive, significantly
negative. **Means: the flagship dose ratio, already fair-control-dead and family-sign-bound, is
also an artifact of the pooling choice within its home model.** The one significant cell (max,
p = 0.034) is one of three uncorrected looks and gets no weight on its own.

**Correction, found by the methods pass (2026-08-12, L93): the ratio half of this verdict is
withdrawn to VOID — a selection artifact.** The runner truncated the held-out ladder's manifest to
its first forty items, and that manifest is ordered by rung, so every ratio-versus-rung cell above
was computed on **rungs 0 and 1 only** — a dose-response correlation with eighty percent of the
dose axis absent by selection. The tell was in plain sight: the mean-pooling arm's own baseline
(−0.045) reproduces neither the raw held-out value (−0.247, n = 100) nor the length-controlled one
(−0.405), and instead of hunting that failed reproduction, the entry explained it away. The clause
"already fair-control-dead" was also wrong on its face — the home family survives the fair control
on all three ladders (L23) and no entry anywhere says otherwise. What stands: the profile-shape
half (pooling-invariant geography), which is not a dose statistic and holds on any text sample.
The rerun is queued: all 100 items, rung composition recorded, gated on the mean-pooling arm
reproducing the known value before the last-token and max arms are read. Until it lands, no
pooling claim about the dose ratio exists in either direction.

**The v2 rerun landed the same day, and the gate passed to the third decimal.** All 100 items,
twenty per rung; the mean-pooling arm reproduces the known length-controlled value exactly
(−0.4052 observed against −0.405 recorded), which licenses reading the other two arms. At full
dose range the ratio-versus-rung correlation is **negative under every pooling** — mean −0.405
(p < 10⁻⁴), max −0.295 (p = 0.003), last-token −0.109 (p = 0.28) — so **v1's sign-flip claim was
the selection artifact talking** (its last-token cell read +0.22 on rungs 0 and 1). What
survives as a real caveat is attenuation: the dose relationship weakens to null when only the
final token position is read, and holds under mean and max pooling. The profile-shape invariance
reconfirms at full n (r ≥ 0.98 across poolings). The recorded verdict stays POOLING-BOUND under
the pre-set rule, because the significance class moves even though the sign does not; the
honest sentence is that the ratio's direction is pooling-stable and its detectability is not.

## L45 · Aligned by computational events, the early locus is early everywhere but one family

**Hypothesis.** *(G124.)* Block addresses never transfer as fractions of depth — the loci are
Qwen-shaped. If families are aligned by what the blocks *compute* rather than where they sit, the
reference loci should land somewhere lawful in each family.

**Method.** `run_cka_alignment.py`: linear CKA (centered-kernel similarity between block
activations, 0–1) between the home model and five others on 30 shared texts; for each home-model
block, the best-matching block in each family; then read off where the home early locus (block 2)
and late locus (block 22 of 28) land, as a fraction of the target's depth.

| family | early locus lands at | late locus lands at |
|---|---|---|
| gpt2-medium | block 1 — 4% deep | block 20 — 83% |
| gpt2-large | block 0 — 0% | block 30 — 83% |
| pythia-1.4b | block 3 — 13% | block 15 — 63% |
| Qwen2.5-0.5B | block 4 — 17% | block 16 — 67% |
| SmolLM2-360M | **block 9 — 28%** | block 24 — 75% |

*Columns: the target-family block whose activity best matches the home model's locus block, and
that block's relative depth.*

**Verdict: the events are portable even though the addresses are not.** In four of five families
the home early locus matches a block in the first sixth of the stack, and the late locus lands at
62–83% depth in all five — a lawful coordinate system where raw block numbers gave none. The
exception is SmolLM2, whose best match to our block-2 events sits over a quarter of the way in —
**the odd family again** (it is also the family exempted in the sign map's fade pattern). **Means:
"where things sit is a fact about the model" now has a translation table; cross-family claims can
be stated at aligned stages instead of raw depths.** No permutation null yet — the best-match
assignment has not been tested against label-shuffled texts — so this is one bad test away
(follow-on filed as G128).

## L46 · The third convergence design still cannot see the dose — readers agree about everything

**Hypothesis.** *(G114b, third build; the claim under test is G60/G114: independent readers'
goal-guesses converge more where intent is dense.)* v1 died to empty answers, v2's token overlap
read topic. v3 fixes both: a judge model rates answer-pair goal-similarity directly, and the dose
comparison holds topic fixed.

**Method.** `run_reader_convergence3.py`: five independent one-sentence goal-guesses per artifact
(local 9B model), convergence = mean judge-rated pairwise similarity of the guesses (0–1). Groups:
ladder rung 1 versus rung 10 **on the same five topics** (the fixed-topic dose contrast v2 never
had), eight human essays, eight books.

| group | n | convergence |
|---|---|---|
| machine, ten stacked specifications (fixed topics) | 5 | 0.908 |
| machine, one specification (same topics) | 5 | 0.932 |
| human essays | 8 | 0.933 |
| human books | 8 | 0.864 |

*Convergence: mean judge-rated similarity of five readers' goal-guesses, 0 = unrelated, 1 =
identical.*

**Verdict: NEITHER-CLEANLY.** The fixed-topic dose gap is −0.02 — wrong sign, negligible size. The
judge saturates near 0.9 on every coherent text; the only structure it saw is books scoring lower,
which reads most naturally as long-form summarisation difficulty, not intent. **Means: three
independent operationalisations — bits recovered, token overlap, judge-rated similarity — have now
each failed to make reader convergence move with intent density.** The claim is not
instrument-dead this time; the instrument produced orderly numbers and the dose is simply not in
them. The row moves to NOT SUPPORTED in this design; whether the convergence family retires
entirely is his call (filed as a decision item).

## L47 · The rebuilt agreement statistic works — and agreement falls where the goal is clearest

**Hypothesis.** *(G105 rebuilding the instrument; G33 is the claim under test — his conditional:
"you might also have more agreement in the late, if the goal is clear.")* The original coherence
statistic was geometrically incapable of measuring agreement (globally centred directions sum to
zero — L26). The rebuild: mean pairwise sign agreement of block responses across texts, on
uncentred per-concept contrasts, gated on synthetic known-answer data before any real read.

**Method.** `run_coherence_v2.py`, all eight families: the gate first — constructed agreeing texts
must score high and random vectors near 0.5 — then agreement at early, middle, and late blocks
correlated against induction rung on all three ladders.

| family | gate (agree / random) | ladder | ladder2 | ladder3 | late-block correlations |
|---|---|---|---|---|---|
| Qwen2.5-1.5B (home) | 1.00 / 0.49 | falls | falls | falls | −0.43, −0.29, −0.41 |
| Qwen2.5-0.5B | 1.00 / 0.49 | falls | falls | falls | −0.61, −0.44, −0.63 |
| gpt2-large | 1.00 / 0.49 | flat | falls | falls | −0.23, −0.38, −0.40 |
| gpt2-medium | 1.00 / 0.49 | flat | flat | falls | −0.13, +0.05, −0.47 |
| pythia-410m | 1.00 / 0.49 | falls | flat | flat | −0.33, −0.16, −0.20 |
| pythia-1.4b | 1.00 / 0.49 | flat | flat | flat | −0.03, +0.01, −0.01 |
| SmolLM2-360M | 1.00 / 0.49 | flat | flat | flat | −0.08, +0.14, 0.00 |
| SmolLM2-1.7B | 1.00 / 0.49 | flat | falls | flat | −0.21, −0.20, −0.01 |

*Gate: the statistic's score on texts built to agree versus random vectors — 1.00/0.49 means it
separates perfectly, so unlike its predecessor it can measure agreement. Corpus columns: the
per-ladder verdict on whether agreement rises with specification dose. Last column: the rank
correlation of late-block agreement with rung on each ladder (negative = agreement falls as
specifications stack).*

**Verdict: the claim's direction is dead — 0 of 24 corpus-cells rise; 11 fall, 13 are flat.** In
the home family agreement falls robustly at every depth (home-model late cells p = 0.0019, 0.0038,
0.0002). The family structure repeats the sign map's shape: strongest in Qwen, weaker in gpt2,
absent in pythia's larger member and SmolLM2. **Means: where the goal is clearest, late-block
responses agree *less* across texts, not more** — as constraints stack, states differentiate
rather than converge. Two cautions before leaning on the reversal: the contrasts are uncentred by
design (agreement needs raw signs), so the induction confound is not partialled here; and one
observation goes unclaimed — real-text agreement sits slightly *below* the random baseline
everywhere (≈0.43 vs 0.49), which the gate's synthetic construction does not explain. The
instrument is validated; the direction is one bad test away.

## L48 · The defensible per-block units retell both standing facts — first two families

**Hypothesis.** *(G126, from the neural-analogues review.)* The per-block profiles this project has
argued from were never the quantities a neural analogy licenses. The three that are: the **write
norm** (how much a block actually changes the stream — what BOLD-style signals track), the
**affect work** (the signed movement along the affect projection, telescoping to the final read),
and **per-block d′** (the probe's honest signal-to-noise), plus a **rogue-share alarm** (does one
dimension dominate the projection — the standard artifact).

**Method.** `run_block_contribution.py`, all eight families: cached block states over 160
specification-ladder windows and 144 maker-less windows; the three quantities per block per
corpus; QC threshold at half the projection carried by one dimension.

| family | signal-to-noise peak | work peak | maker-vs-none gap | rogue share |
|---|---|---|---|---|
| Qwen2.5-1.5B (home) | block 6 of 27 — 22% deep, 2.76 | block 1 | ≤ 0.15 | 0.02 |
| Qwen2.5-0.5B | block 3 of 23 — 13%, 3.38 | block 2 | 0.06 | 0.03 |
| gpt2-medium | block 22 of 23 — 96%, 2.37 | block 0 | 0.01 | 0.22 |
| gpt2-large | block 16 of 35 — 46%, 2.21 | block 0 | 0.02 | 0.05 |
| SmolLM2-360M | block 18 of 31 — 58%, 2.82 | block 3 | 0.16 | 0.03 |
| SmolLM2-1.7B | block 23 of 23 — 100%, 3.06 | block 7 | 0.06 | 0.02 |
| pythia-410m | block 21 of 23 — 91%, 2.69 | block 5 | 0.11 | 0.03 |
| pythia-1.4b | block 11 of 23 — 48%, 2.29 | block 3 | 0.08 | 0.01 |

*Columns: where the probe's per-block d′ peaks (block, relative depth, value); which block does
the most signed affect work (raw write magnitude peaks in the same place in every family); the
largest difference any block shows between ladder text and maker-less text, against work values
running 4–77; and the QC alarm (below 0.5 = no single dimension dominates).*

**Verdict: two universals and one lawless quantity, on the complete set.** Universal one: the
write/work geography is *maker-blind* — the ladder-vs-maker-less gap is negligible at every block
in all eight families, the address-umbrella rejection (L14) in honest units. Universal two: the
signed affect work concentrates at the input edge (blocks 0–7, mostly 0–3) everywhere, right where
the control-subspace question (G43) put the boundary. The lawless one: where discriminability
peaks follows neither family nor size — Qwen sits early at both sizes (13–22%), but pythia goes
late-to-mid as it grows (91% → 48%), SmolLM2 mid-to-late (58% → 100%), gpt2 late-to-mid (96% →
46%). **The home family's consistently early d′ is the exception, not a law — and it is exactly
where this project's loci were chosen, a selection caution the cross-family failures keep
confirming.** All eight QC-clean, so none of this is a rogue-dimension artifact.

## L49 · The early break is the adapter's edge — every control subspace snaps in the same place

**Hypothesis.** *(G43, the test he ordered first.)* The affect subspace's one sharp boundary sits
at the very front of every model. If it is an *affective* boundary it should be absent for
non-affective content; if syntax, topic, and frequency subspaces all break at the same place, the
boundary is the input adapter's edge and says nothing about the affect mappings.

**Method.** `run_control_subspaces.py`, three families landed of eleven: topic, syntax, and
frequency subspaces authored and fitted identically to the affect one (same rank, same fitting
path, same block grid), then the location of each subspace's sharpest adjacent-block overlap drop.

| family | affect breaks at | topic | syntax | frequency | verdict |
|---|---|---|---|---|---|
| Qwen2.5-1.5B (home) | block 1 | block 1 | block 1 | block 1 | ADAPTER-EDGE |
| Qwen2.5-0.5B | block 1 | block 1 | block 1 | block 1 | ADAPTER-EDGE |
| gpt2-medium | block 1 | block 1 | block 1 | block 1 | ADAPTER-EDGE |
| pythia-1.4b | block 1 | block 1 | block 1 | block 1 | ADAPTER-EDGE |
| SmolLM2-360M | block 1 | block 1 | block 1 | block 1 | ADAPTER-EDGE |

*Columns: the block index of the sharpest break in each content type's subspace continuity — the
same place for all four content types, in all five families so far.*

**Verdict: ADAPTER-EDGE, unanimous in the first five families.** The break the affect subspace
shows is shared by every content type measured — it is the seam where the input representation
hands over to the residual stream, not a fact about affect. **Means: any reading of the two-way
split (G42) as an affective boundary is dead; the front break carries no mapping information.**
The deflationary arm of his gating question, exactly as he posed it. **Complete: eleven of eleven
families, unanimous** — the remaining six landed identically (every subspace type, block 1, every
family).

## L50 · The affect subspace's depth rotation survives its own repair — rank-truncated, against a matched null

**Hypothesis.** *(G111.)* Every subspace-continuity number so far carried a known dilution: the
fitted basis spans rank 7 in eight columns. The repair — rank-truncated bases and a
distant-pairs-matched null — must not flip the verdicts, or the rotation story was an artifact of
the fit.

**Method.** `run_subspace_alignment.py` v2, three families landed of eleven: subspace overlap
between adjacent blocks, between distant blocks, and over all pairs, against a null built from
matched random subspaces of the same rank on the same grid.

| family | adjacent overlap | distant overlap | null | verdict |
|---|---|---|---|---|
| Qwen2.5-1.5B (home) | 0.82 | 0.31 | 0.056 | DEPTH |
| Qwen2.5-0.5B | 0.78 | 0.26 | 0.074 | DEPTH |
| gpt2-medium | 0.92 | 0.42 | 0.069 | DEPTH |
| pythia-1.4b | 0.87 | 0.28 | 0.049 | DEPTH |
| SmolLM2-360M | 0.85 | 0.27 | 0.071 | DEPTH |

*Columns: mean shared fraction of the 7-dimensional affect subspace between neighbouring blocks;
between the most separated blocks; what matched random subspaces share by chance; and the
per-family verdict that the structure is depth-organised.*

**Verdict: DEPTH, eleven of eleven — the rotation is real and the repair changes nothing.**
Across the complete set neighbouring blocks share 0.78–0.96 of the subspace, distant blocks
0.21–0.42, chance ~0.05–0.07 — everything four to eight times above a properly matched null, in
every family (the six later landings: gpt2-large 0.95/0.41, gpt2-xl 0.96/0.40, pythia-410m
0.86/0.24, pythia-2.8b 0.90/0.28, Qwen-3B 0.84/0.22, SmolLM2-1.7B 0.81/0.21). The v1 rank caveat
retires entirely: the structure was never the fit's artifact.

## L51 · At power, the salience gate is dead everywhere — presence is flat and block 0 always knows the category

**Hypothesis.** *(G21b, the powered cross-family map; G21 is the claim: block 0 is a pure salience
gate — presence without category.)* The underpowered pass left a home-family survival ("salience-
first was a home-family fact") and scattered presence peaks elsewhere. At 500 neutral items and
1,573 total, family by family: does any model hold presence early while staying category-blind?

**Method.** `run_binary_salience.py --neutral-per 500`, all eleven families: per-block decodability
of *whether* affect is present (binary) and of *which* category (27-way, chance 3.7%); the
dissociation gate requires block 0 to carry presence at ≥ 90% of its best-block level while
carrying category at under twice chance.

| family | presence at block 0 | best presence anywhere | category at block 0 | verdict |
|---|---|---|---|---|
| Qwen2.5-1.5B (home) | 0.637 | 0.637 (block 0) | 0.312 — 8.4× chance | NO DISSOCIATION |
| Qwen2.5-0.5B | 0.621 | 0.633 | 0.281 — 7.6× | NO DISSOCIATION |
| Qwen2.5-3B | 0.607 | 0.642 | 0.335 — 9.0× | NO DISSOCIATION |
| gpt2-medium | 0.628 | 0.636 | 0.325 — 8.8× | NO DISSOCIATION |
| gpt2-large | 0.622 | 0.643 | 0.322 — 8.7× | NO DISSOCIATION |
| gpt2-xl | 0.617 | 0.633 | 0.336 — 9.1× | NO DISSOCIATION |
| pythia-410m | 0.593 | 0.641 | 0.309 — 8.3× | NO DISSOCIATION |
| pythia-1.4b | 0.598 | 0.657 | 0.322 — 8.7× | NO DISSOCIATION |
| pythia-2.8b | 0.589 | 0.651 | 0.337 — 9.1× | NO DISSOCIATION |
| SmolLM2-360M | 0.610 | 0.622 | 0.297 — 8.0× | NO DISSOCIATION |
| SmolLM2-1.7B | 0.616 | 0.655 | 0.334 — 9.0× | NO DISSOCIATION |

*Columns: how well block 0 decodes affect-present-versus-neutral (0.5 is chance); the best any
block manages; how well block 0 decodes the 27-way affect category against 3.7% chance; the
dissociation verdict.*

**Verdict: NO DISSOCIATION, eleven of eleven.** Two facts replace the old reading. **Presence is
near-flat through every stack** — block 0 sits within a few points of the best block in every
family (0.59–0.64 against bests of 0.62–0.66), so the "presence peak locations" that scattered
across families in the underpowered pass were argmaxes of level curves, noise on flatness — the
home family's block-0 peak included. **And block 0 always knows the category** — eight to nine
times chance in every family, so no model has a presence-only stage at its front door. **Means:
the salience-gate hypothesis is dead at power across the entire map, home family included; what
exists instead is weak, depth-uniform presence information with category information everywhere.**
The two curves' *relative* placement (category peaking mid-stack, blocks 7–18) stays available to
the layer-ordering question.

## L52 · Self-revision is homogeneous, splices are lumpy — perfect separation, against the weakest adversary

**Hypothesis.** *(G81, the connoisseurship import.)* A maker's own revisions are "of like kind"
throughout while imposed changes arrive in distinct steps — operationalised distributionally: the
dispersion of paragraph-level change magnitudes between drafts should be low for real
self-revision and high where change was imposed.

**Method.** `run_revision_homogeneity.py`: 66 essay authors with both first and third drafts
(pairable after the stem-normalisation fix of L43); per author, the spread of per-paragraph change
magnitudes across the revision; the control is a synthetic splice — paragraphs from another author
inserted into the first draft at the same total change volume.

| | dispersion of change magnitudes |
|---|---|
| real self-revision (66 authors) | 0.45 |
| synthetic splice, same change volume | 1.94 |

*Dispersion: spread of per-paragraph change sizes relative to their mean — low means the revision
touched the artifact evenly, "of like kind"; the two distributions separate with no overlap
(AUC 1.0, where 0.5 is chance and 1.0 is perfect).*

**Verdict: SEPARATES, at ceiling — and the ceiling is the caveat.** The pre-registered bar (0.7)
is cleared at 1.0, which mostly measures how weak the adversary is: a cross-author paragraph
splice produces near-zero local similarity, so the statistic may be reading *different author
present* rather than *imposed change lumpy*. What the first pass establishes: the homogeneity
statistic works and real self-revision genuinely sits low. What it cannot yet claim: separating
self-revision from *realistic* imposition — an editor's same-register touch — which is the mixed-
provenance case the import exists for. One bad test away, and the next test is a subtler splice.

## L53 · The definitional test's first valid run inverts the prediction, with a named confound

**Hypothesis.** *(PD-1, the polish/depth split's own falsifier, first valid run after two
instrument faults.)* Depth-side quantities should show smaller between-position variance than
polish-side quantities within one artifact. The traces file's own words say that if both move
equally the distinction is not real.

**The second fault first.** The rebuilt runner's v2 statistic z-scored each feature series by its
own spread before taking variance, and the variance of a z-scored series is 1 by construction.
Both medians landed at 0.9999999 and the p-value of 10⁻⁴⁴ measured epsilon arithmetic. A criterion
that could not fail, quarantined (`v2_zvar_degenerate/`), and the class the audit named now has a
member written by the auditor. v3 normalizes each series by its feature's corpus-level spread
instead, and ships a known-answer gate. A planted flat series must score near zero and a planted
moving series high, before any real read (flat 0.0000, moving 1.52, gate passed).

**Method.** `run_positional_polish.py` v3 over the rebuilt 80-word window cache (258 essays, five
to eight windows each). 28 polish-side features (readability indices, type-token, punctuation)
against 20 depth-side features (Biber's causal, conditional, concessive, relative, nominalization
and participial tags, plus dependency distance); per essay, the mean within-artifact positional
variance of each side in corpus-scale units; paired comparison across essays.

| side | median positional variance |
|---|---|
| polish-side features | 0.583 |
| depth-side features | 0.744 |

*Positional variance: how much a feature moves between an essay's windows, in units of that
feature's corpus-wide spread; the paired difference is significant at p = 2.6 × 10⁻⁸.*

**Verdict: DEPTH-MOVES, the inverted direction, first pass, one confound named before anyone
leans on it.** Depth-side features move *more* across positions than polish-side features on this
corpus, and the prediction ran the other way. The confound is mechanical. The depth side is built
from sparse count features (a window with one conditional against a window with none is a rate
spike), while readability indices are dense over every word and smooth by construction, so the
sides differ in sampling variance per window regardless of what the maker did. The discriminating
follow-up (PD-1b) compares each feature's within-artifact variance to its between-artifact
variance at matched window counts, which cancels the sampling floor. Until that runs, the licensed
statement is narrow. On student essays the polish/depth feature sides do not move equally, and the
excess sits on the depth side.

## L54 · The length re-audit confirms the named weakness: one in six killed effects was suppressed, not confounded

**Hypothesis.** *(Known weakness 3b, the direction re-audit.)* Every measure killed on "correlates
with length" was killed without checking the sign of the length relationship against the sign of
the effect. Length can work *against* an effect (suppression), in which case the kill was the
method's error.

**Method.** `length_direction_audit`: for every feature with a dose effect on each ladder, the raw
correlation against the length-partialled correlation, classified as confounded (effect shrinks
when length is removed) or suppressed (effect emerges or strengthens).

| corpus | features with an effect | length-confounded | length-suppressed |
|---|---|---|---|
| first ladder | 295 | 120 | 56 |
| second ladder | 284 | 128 | 73 |
| third ladder | 299 | 148 | 34 |

*Confounded means length was inflating the effect and the kill was right; suppressed means length
was masking it and the kill logic was backwards for that feature.*

**Verdict: the weakness was real at scale.** Roughly one in six effect-bearing features per corpus
was in the suppression regime, and the recurring rescue is the readability-ease family (Flesch
reading ease appears in the strict rescue list on two of three ladders). What this does not do is
revive anything by itself. The rescued quantities are dose correlates within one generator, the
class the program has stopped chasing, so the audit's value is bookkeeping. Deaths pronounced on
raw length correlation carry a one-in-six method error, recorded here so no old kill is cited as
clean. Diagnostic entry; no claim family touched.

## L55 · The dispersion route to the definitional test is void in principle, and it leaked one real fact on the way out

**Hypothesis.** *(PD-1b, the matched null for L53's inversion.)* If depth-side features only
"moved more" because sparse counts are noisier per window, dividing each feature's within-essay
variance by its own across-essay shuffle null should cancel the sampling floor and reveal which
side carries genuine positional structure.

**Method.** `run_positional_polish_b.py`: per feature, observed mean within-essay variance over
its value under 200 window shuffles across essays; the two feature sides' ratio distributions
compared. Its between-essay-only planted control behaved (ratio 0.00 as required).

**What came back, and what it actually means.** Polish-side median ratio 0.802, depth-side 0.923,
difference significant at p < 10⁻⁴. Both sit *below* one, and working the algebra afterward shows
they must. Mean within-essay variance equals the pool variance minus the between-essay variance,
so the ratio is one minus the between-essay share and **cannot exceed one for any data**. The
"depth moves" branch of my own verdict rule was unreachable, the criterion-that-cannot-fire class
again, caught by derivation this time rather than by a zero. Worse and more useful: **variance is
order-invariant, so no dispersion statistic can measure positional movement at all.** The entire
window-dispersion operationalisation of PD-1, v3 included, was structurally unable to see the
quantity the hypothesis names.

**Verdicts, three of them.** For PD-1 as operationalised: **VOID in principle**, the L53 inversion
now fully explained as per-window sampling noise plus this identity, and a movement claim needs an
order-sensitive statistic (positional trend, lag differences) or the program's event level. For
the instrument class: dispersion ratios measure **essay-boundness**, a real quantity. And the
incidental finding: **at fixed topic and assignment, polish-side features are two and a half times
more essay-bound than depth-side features** (between-essay variance share 20% against 8%,
p < 10⁻⁴, 258 drafts). With topic held constant by construction, between-essay variance is
author-and-draft variance, which makes this the first artifact-side evidence for the
maker-signature half of the traces claim, that polish variation carries *who* while depth-side
features run corpus-generic. First pass, one corpus, and the draft/author decomposition is the
obvious next cut.

## L56 · The event-recovery harness passes its five gates, and two of the gates earned their keep during the build

**Hypothesis.** *(G130, the program's shared instrument.)* Every choice-recovery test will run
through one harness, so the harness itself must first recover known synthetic decisions and fail
correctly on every null, per the standing known-answer rule.

**Method.** `run_event_harness.py`: a synthetic world of 40 makers × 12 decision events, each
event one purpose-linked phrasing choice among four (signal rate 0.7, so noisy like real text); a
bag-of-evidence reader trained on a disjoint maker split; five pre-set gates.

| arm | what it must show | result |
|---|---|---|
| oracle | real access scores above chance | 0.796 against 0.25 chance |
| shuffled labels | chance | 0.225 |
| unchanged passages | chance | 0.282 (n = 1,200) |
| blind reader | chance | 0.227 (n = 1,200) |
| decoy symmetry | no candidate structurally favoured on null text | picks 0.23 to 0.28 |

*Chance is 0.25 throughout; the chance arms carry a fixed ±0.06 band that was never widened.*

**Verdict: HARNESS-VALID, with two catches recorded.** The build's first decoy arm scored a
remapped truth, which with real signal present must land below chance, so it re-measured signal
upside down and was replaced by the candidate-symmetry check before any real corpus was touched.
That symmetry check then immediately caught a real fault, deterministic tie-breaking handing
every null-text pick to the first candidate, the strict-ties class the audit found once before in
specification recovery. Ties now break randomly. One eyebrow stays recorded: the unchanged arm
sits slightly above chance at power (0.282, about 2.6 standard deviations) while inside its
pre-set band; if it persists across the harness's future runs it gets hunted. **Settled
(2026-08-19, the TODO's cheap-settle row): at five times the makers (n = 6,000 unchanged
reads) across three fresh seeds the arm reads 0.249 / 0.249 / 0.240 — dead on chance, all
five gates green all three times (`results/event_harness/scale5_seed{18,19,20}.json`). The
0.282 was seed-17 sampling noise; the eyebrow closes.** **Means: G129's
ArgRewrite analysis has a validated instrument to run through, which was the program's stated
gate for touching the real corpus.**

## L57 · The essay-boundness split follows the author, not the draft — the maker-signature reading stands

**Hypothesis.** *(PD-33's decomposition; L55 found polish-side features 2.5× more essay-bound
than depth-side at fixed topic, and "essay" conflated author with draft stage.)* If the polish
side's excess boundness follows the author, polish variation carries the maker; if it follows the
draft, it carries revision state.

**Method.** `run_pd33_decomposition.py` over the 258-draft cache (86 authors × up to 3 drafts,
topic and assignment constant): per feature, the share of pool variance lying between authors,
then between drafts within authors; the two feature sides compared on each share. Known-answer
gates first: a planted author-constant feature must land all-author (it did, 1.00/0.00), a
planted draft-varying feature must land majority-draft (it did, 0.68 draft share).

| variance share | polish-side median | depth-side median | difference |
|---|---|---|---|
| between authors | 0.262 | 0.174 | p = 6 × 10⁻⁷ |
| between drafts, within author | 0.042 | 0.036 | p = 0.98 |

*Shares are fractions of each feature's total variance; author share is what a feature knows
about who wrote it, draft share what it knows about which revision pass it came from.*

**Verdict: MAKER.** The polish side's excess boundness is author-boundness, half again the depth
side's, while draft-stage information is small and identical on both sides. **Means: "polish
variance is a maker signature" now has a second, sharper artifact-side number, and it is
specifically the maker.** The near-zero draft shares also bound how much these window features
can know about revision state, which sits consistently with L42's relabel. One corpus, one
window size; the cross-corpus check rides along free whenever another windowed cache exists.

## L58 · The alignment null lands split: the late locus is real, the early landings are partly generic geometry

**Hypothesis.** *(G128, the null L45 owed.)* If the event alignment's lawful landing depths are an
artifact of similarity-matrix smoothness, they should survive breaking text correspondence; if
they are carried by shared per-text computation, the null should scatter.

**Method.** `run_cka_null.py`: the block-matching recomputed 100 times per family with reference
activations of text i paired against target activations of a permuted text j; the observed
early/late landing depths tested against the null's central 95% band.

| family | early locus | late locus |
|---|---|---|
| gpt2-medium | inside the null band | **REAL** (0.83 against a band topping at 0.31) |
| gpt2-large | inside the null band | **REAL** (0.83 against a collapsed band) |
| pythia-1.4b | **REAL** | **REAL** |
| Qwen2.5-0.5B | **REAL** | **REAL** |
| SmolLM2-360M | undecidable | undecidable |

*REAL means the observed landing depth falls outside what mismatched-text pairings produce;
"inside" means smoothness alone reproduces it; SmolLM2's null bands span nearly the whole stack,
so nothing could fall outside them.*

**Verdict: 6 of 10 cells REAL, and the split is informative.** The **late** locus survives the
null in all four decidable families, so the deep event alignment is carried by genuine shared
per-text computation. The **early** landings survive only where the null is tight (pythia, small
Qwen) and are reproduced by smoothness in both gpt2 members, which makes sense of itself, since
early blocks process input generically and match early-to-early even for mismatched texts. L45
softens accordingly. The lawful late-locus table keeps its evidential weight; the early-locus
lawfulness is partly generic geometry; and the family that refused the alignment (SmolLM2) is
also the one whose null cannot decide, consistent with its odd-family record. One caution rides
the whole battery: thirty texts, one corpus.

## L59 · The ArgRewrite recreation, first two arms: the purpose signal lives in the delta

**Hypothesis.** *(G136, Phase 1's first owed recreation.)* Reproduce the corpus's own published
classification task (revision purpose at coarse and fine grain) with our tooling, so the
published numbers become our known answer and the event extraction becomes G129's dataset.

**Method.** `run_arg_baselines.py`. The extract arm parses every annotation workbook on the real
two-sheet schema (Old Draft / New Draft, aligned sentence indices, purpose columns at two
levels), yielding **2,806 labelled revision events across 86 authors and 26 fine labels**, cached
as the choice-event dataset. The features arm runs bag-of-words logistic classification under
author-split five-fold cross-validation, first on the raw sentence pair, then with explicit diff
tokens (words added, words removed) featured.

| arm | coarse (surface/content) | fine (8 labels ≥ 30 support) |
|---|---|---|
| sentence pair only | 0.503 macro-F1 | 0.109 |
| with diff tokens | **0.857 macro-F1** | 0.233 |
| chance floor | ~0.5 (binary) | 0.125 |

*Macro-F1 averages per-class accuracy so frequent classes cannot carry it; author-split means no
writer appears in both train and test.*

**The published bar, fetched and read the same night.** The paper reports XGBoost with USE
embeddings at **F1 0.93 on the binary task and 0.51 on nine fine classes** (sentential), on 86
writers and 3,238 sentential revisions; our extraction found the same 86 writers and 2,806
labelled events, the shortfall plausibly unlabelled and identical-pair rows. Against that bar our
crude arms sit **below**: features-with-diff at 0.857 coarse and 0.233 fine, and the zero-shot
reader's first arm at 0.664 accuracy on cycle-one coarse against 0.5 chance (per-author spread
0.23 to 1.0). The recreation gate is therefore **not yet matched**; the owed push is a features
arm with embeddings and revision-operation features, and until it closes the gap our known-answer
for G129 is the published number, not our own.

**And the design fact for everything downstream.** On the raw sentence pair the classifier learns
nothing, because every essay answers one prompt and sentence text encodes topic; **the entire
signal is in the delta.** G129's candidate scoring reads deltas or it reads nothing, and the
pilot's prompts are built that way. Reader arms, complete: cycle-one coarse 0.664 and fine 0.254
(against 0.5 and 0.125 chance), cycle-two coarse 0.648 and fine 0.249 (against 0.143), the two
cycles replicating each other's level at both grains.

**Addendum, the raised standard (2026-08-10, his ruling).** The comparison above does not count
as a pass. A recreation passes by reproducing the published exact values, and 0.857 against 0.93
means our model of their pipeline was wrong, which the protocol details confirm on the fetch.
Three identified divergences: their five-fold has **no author grouping** (ours was author-split,
strictly harder), their features are length, position, POS-tag and transition-word frequencies
with **Universal Sentence Encoder** embeddings of the pair, and their classifier is **XGBoost**
over a stated grid. The exact-replication runner reproduces all of it (their encoder downloaded
to a local cache for the run), extraction v2 closes the dataset gap (3,365 examples against
their 3,238, within four percent, purposes unioned across both sheets and multi-purpose cells
split), and the pass gate is a two-decimal match on the Features+USE cells of both tasks. In the
queue; the zero-shot reader arms (0.664 coarse, 0.254 fine against 0.125 chance so far) stand as
a separate arm and are not the pass.

## L60 · The impossibility construction reproduces exactly, and the bounded family is the prior that does the work

**Hypothesis.** *(G138, Phase 1's sharpest recreate-then-push.)* First reproduce Armstrong &
Mindermann's reward/planner degeneracy exactly; then add the three human priors §7 of the triple
inference leans on, one at a time, and measure posterior narrowing.

**Method.** `run_am_construction.py`: a seven-state chain world, exact enumeration over 2,186
reward functions × four planners (optimal, anti-optimal, lazy, weakly rational), posterior over
pairs from the observed policy; 20 seeds per cell, observation noise swept 0 to 0.2.

| condition | posterior mass on the true reward (clean observations) |
|---|---|
| no priors (the theorem's setting) | 0.008 |
| A: bounded, human-shaped reward family | 0.156 |
| B: planner known near-optimal | 0.015 |
| C: both | 0.308 |

*Mass 1.0 would be unique identification; the theorem's two-reward construction first reproduced
at exactly 0.5/0.5, the recreation gate, passed to the digit.*

**Verdict: RECREATED+NARROWS.** The recreation is exact, and the push orders the three
assumptions. **The bounded hypothesis family is the load-bearing prior**, worth twenty times the
baseline alone, while a known planner barely doubles it, and the two compound to forty times,
holding under noise. Read against §7's table, "convergent midbrains" is the assumption doing the
heavy lifting in this toy, and near-optimality only pays once the family is already bounded.
Means: the project's convergence position now has a running existence proof at toy scale, that
substantive priors buy large posterior narrowing without unique identification (0.31 is nowhere
near 1.0, exactly as the position claims). A seven-state chain with one-step lookahead is the
loudest caveat; the gridworld recreation (G137) is where this grows teeth.

## L61 · The recreation re-audit: one true pass, exact gates fetched for the rest, and a coverage sweep of this file

**What was asked.** Pre-verify the planned recreations with precise pass gates; re-verify every
claimed recreation against its paper's specific numbers; and verify every entry in this file
appears in the theory table that interprets it.

**The recreation re-audit.** Under the exact-value standard, none of the six previously claimed
anchors was a value pass; the Phase 1 table now carries per-row honest statuses. One true pass
exists, the impossibility construction's analytic 0.5/0.5 (L60). ArgRewrite is NOT PASSED with
the exact pipeline in the queue. The BST gates were fetched from the paper itself (Experiment 1
best-fit correlations .83/.98/.94 for the three models; Experiment 2 cross-validated .57/.95/.58
with the heuristic at .91; Experiment 3 subgoal model .96), with the scope note that the human
side lives in figures, so the pass is on model predictions and parameter dependence. The
ScholaWrite gates were fetched (fine-tuned BERT and RoBERTa at weighted F1 0.64, Llama-8B 0.13,
GPT-4o 0.08, agreement 0.71, 61,504 keystrokes, ten writers, five preprints). Four rows are
EXEMPT with reasons, method or protocol imports with no foreign number to hit (the pottery
partition, revision homogeneity, the pooling attack, our own attribution calibration).

**The CKA sanity check, run as part of closing its row.** Self-similarity, isotropic scaling, and
orthogonal invariance all pass at machine precision. The check also surfaced a real fact:
**independent random matrices score 0.985 at thirty samples in two thousand dimensions**, so raw
similarity magnitudes in our alignment work were never interpretable, only the null-tested match
structure was, which is what the permutation null (L58) enforced and why the odd family's null
band spanned the stack. Recorded into the alignment row.

**The coverage sweep.** All 58 entries checked against the five theory files at content level.
Twenty-seven hypothesis rows gained explicit L-citations so the mapping is auditable by grep.
Five entries are method-archive-only by design and carry no theory row: the stage audit (L20),
the adversarial audit (L26), the instrument false start (L43), the length-direction bookkeeping
(L54), and the harness validation (L56), each an audit or instrument record rather than a claim
adjudication. Zero-shot reader arms completed meanwhile: cycle-two fine 0.249 against 0.143
chance, closing the four-arm set (0.664/0.254/0.648/0.249).

## L62 · The pilot's five arms: recovery beats its floor, and the controls caught the floor being crooked

**Hypothesis.** *(G129-pilot, preregistered in the runner.)* Can a bounded zero-shot reader pick
the recorded revision purpose from a bounded candidate set, above chance and above its own
controls?

**Method.** `run_arg_recovery.py` on the 2,806-event dataset: the true purpose plus
frequency-weighted decoys, delta shown; blind (candidates only) and shuffled-truth controls.

| arm | accuracy | nominal chance |
|---|---|---|
| coarse, two candidates | 0.585 | 0.50 |
| fine, four candidates | 0.529 | 0.25 |
| fine, eight candidates | 0.290 | 0.125 |
| fine k=4, **blind** | **0.325** | 0.25 |
| fine k=4, **shuffled truth** | **0.310** | 0.25 |

*Blind shows the reader candidates with no revision; shuffled swaps in another event's label.
Both should sit at nominal chance and neither does.*

**Verdict: the controls fired, exactly as designed.** Frequency-weighted decoys leak the label
prior, since the true label is drawn from the real distribution and is more often the globally
common one than any single decoy, so a reader can beat nominal chance knowing nothing. The
honest read is therefore recovery against the crooked floor the controls measured: **0.529
against 0.325 at four candidates, a twenty-point margin carried by the delta**, consistent
across candidate-set sizes. Per the preregistration's own gate the nominal numbers are not
believed, and the redesign (uniform candidate sampling, pilot-b) is built and in the night
queue with its own controls. The pilot did what pilots are for; the measurement lesson is now
code.

## L63 · The inverse-planning models pass their analytic gates — the recreation's model side stands up

**Hypothesis.** *(G137 v1.)* Before any figure-level comparison, the three models must pass
gates the mathematics fixes in advance: the switching model at zero switch rate must equal the
static model exactly; the posterior must converge on the true goal as action noise vanishes;
and after a mid-path goal switch, the switching model must track while the static model stays
stuck.

**Method.** `run_bst_gridworld.py`: exact value iteration on a reconstructed maze-world (the
published stimuli are figures; the reconstruction is the recorded deviation), Boltzmann action
noise, online posteriors for the static, switching, and subgoal models; forty sampled paths per
gate cell.

**Found.** The zero-rate identity holds at a maximum gap of 10⁻¹²; true-goal mass rises 0.63 →
0.89 → 1.00 → 1.00 as noise falls, monotone; after a switch the switching model puts 0.899 on
the new goal while the static model holds 0.158. **GATES-PASSED.** The best-fit parameter
curves from the paper's three experiments are saved for the figure-level half, which is the
remaining part of the pass and is not claimed. Means: the substrate the estimator tournament
(G134) needs now exists and behaves lawfully.

## L64 · The night batch: the matching refused to be theatre, and the pilot's floor followed the truth

**The matched control (G130b) returned MATCHING-FAILED, by its own gate.** Content and surface
revisions differ enormously on the matching covariates (standardized mean differences 0.49 to
1.29 before matching), and greedy one-to-one matching with a caliper improved balance without
reaching the pre-set 0.25 bar (worst covariate 0.486 after, 640 pairs). No verdict was issued on
the survives-or-collapses question, which is the instrument behaving correctly, since a
classification run on unbalanced "matched" sets would have been theatre. The v2 design is
coarsened exact matching on binned covariates, which buys guaranteed balance at the price of
sample, queued today.

**Pilot-b (uniform candidates) taught the second construction lesson.** Uniform decoy sampling
did not flatten the blind floor (blind 0.348, shuffle 0.328 against nominal 0.25), because the
leak was never only the decoys, the *truth* follows the corpus label marginal while decoys do
not, whichever way decoys are drawn. The estimand that survives both lessons is the **margin
over the measured blind floor**, and it is stable: 0.204 under weighted candidates, 0.189 under
uniform (recovery 0.537 against floor 0.348). The coarse arm's controls landed too (blind 0.511,
shuffle 0.510 against recovery 0.585), putting the coarse margin at a modest 0.074, so **the
delta carries roughly nineteen points of fine-grained purpose information and seven points of
coarse**, on 2,748 and 2,806 events. Pilot-c (truth-balanced subsampling, where the blind floor
is analytic) is the quotable-number design, queued today.

**The night's failures, all diagnosed.** ScholaWrite is a gated dataset and needs an
authenticated token, his side, moved to blocked. The books cache died on a flag typo (the
builder takes a plural flag), fixed and re-queued. The twelve-candidate stage wrote its output
under the true capped name while the queue watched for the guessed one, a produces-name
mismatch, fixed; its result landed regardless (0.307 at eight candidates against 0.125 nominal,
consistent with the margin story). The exact replication ran all night on the grid and its
interim numbers already tell the story: binary close but not matched (0.874 to 0.878 against
0.90 to 0.93), fine catastrophically off (0.27 against 0.44 to 0.49), with the label-conflicting
duplicates from comma-splitting as the prime suspect, since first-purpose-only extraction lands
at 3,323 against their 3,238. The v3 extraction reruns today with per-cycle counts against
their published split.

## L65 · Pilot-c: the floor comes clean and the margin survives it — the pilot's quotable number

**Hypothesis.** *(G129-pilot-c, the third construction.)* With truth labels balanced by
subsampling, the blind floor is analytic at one over the candidate count; if blind lands there,
the construction has stopped leaking and the recovery margin is quotable.

**Method.** `run_arg_recovery.py --uniform --balance`: 77 events per fine label, 616 total, four
candidates, recovery and blind arms.

| arm | accuracy | floor |
|---|---|---|
| blind (candidates only) | 0.232 | 0.25 analytic |
| recovery (delta shown) | **0.477** | 0.25 verified |

**Verdict: the construction is clean and the margin is real.** Blind sits at chance (0.232
against 0.25, within one standard error at this n), so the two earlier leaks are gone, and
recovery holds **0.477 against a verified 0.25 floor, a 22.7-point margin on 616 balanced
events**, consistent with the 0.19 to 0.20 margins the crooked-floor constructions implied.
The pilot concludes: **recorded fine-grained revision purposes are recoverable from deltas by a
zero-shot bounded reader at roughly twenty points over chance**, with three construction lessons
banked in the instruments ledger. What the margin is made of is the next question, and L66 makes
it urgent.

## L66 · The matched control landed COLLAPSES — "content" does not survive its covariates

**Hypothesis.** *(G130b v2; L42's relabel hangs on it.)* If content revisions stop being
identifiable once matched to surface revisions on size, rarity, position, and difficulty, the
content-associated lexical effect was those covariates, not recoverable content-ness.

**Method.** `run_arg_matched.py` v2, coarsened exact matching on terciled covariates: 342 pairs
across the common-support strata, balance verified (worst standardized difference 0.20, the rest
at or under 0.09, gate 0.25), then the same diff-features classifier that scores 0.857 unmatched.

**Verdict: COLLAPSES.** Matched-set macro-F1 **0.507 against 0.5 chance**, from 0.857 unmatched.
Within the covariate-overlap region, nothing in the diff text identifies content beyond what
revision size, rarity shift, and position already say. **Means: PD-28 resolves in its own stated
direction — the surviving revision effect is sophistication and magnitude, not recoverable
depth** (L42's demotion was right, and is now the verdict rather than a caution). Two scope notes
carried honestly: coarsened matching kept only the common-support fifth of the corpus (684 of
3,046 events), so the claim is about comparable revisions, exactly where the claim matters; and
the pilot's fine-grained margin (L65) is untested under matching, so whether *purpose* recovery
also rides these covariates is now the sharpest open question (G130c, filed).

## L67 · The replication's v1 full verdict: the majority baselines match exactly, the model arms do not

**Hypothesis.** *(G136-exact, v1 extraction.)* The overnight grid completed before the engine
swap; this is its full verdict on the split extraction (n = 3,365).

| cell | ours | published |
|---|---|---|
| binary majority | 0.369 / 0.584 | 0.37 / 0.58 |
| fine majority | 0.053 / 0.313 | 0.05 / 0.29 |
| binary features / USE / both | 0.878 / 0.874 / 0.874 | 0.90 / 0.92 / 0.93 |
| fine features / USE / both | 0.278 / 0.267 / 0.276 | 0.44 / 0.49 / 0.51 |

*Each cell is macro-F1 / accuracy.*

**Verdict: NOT-MATCHED, with the informative half being what does match.** The majority
baselines land on the published numbers to two decimals, which validates the extraction's class
composition, so the defect is in the model arms, not the dataset. Binary sits 0.02 to 0.06 low
(candidate causes: the USE variant, the unspecified embedding combination, grid selection); fine
sits 0.16+ low, with label-conflicting duplicate pairs still the prime suspect, and v3
(one purpose per pair) is re-queued behind the running fine-tune. The pass standard stands;
nothing here is claimed passed.

## L68 · The first ScholaWrite arm overshoots its gate, and the split audit explains why

**Hypothesis.** *(G141, the recreation's first fine-tune.)* BERT fine-tuned on the shipped
train split should land on the published weighted F1 of 0.64.

**Found.** Weighted F1 **0.741 on the shipped test split** (49,212 train / 12,292 test, three
epochs), overshooting the gate by ten points. NOT-MATCHED, and overshooting diagnoses
differently from falling short. The immediate structural audit of the local dataset: **all five
projects appear in both train and test in proportional counts** (a within-project split), and
**1,060 of 1,241 unique test before-text prefixes also occur in train**, 85 percent overlap.
Keystroke-adjacent writing states are near-duplicates, so the shipped split leaks text across
the boundary and inflates any model evaluated on it.

**Means.** Our pipeline is not vindicated by the higher number; the published 0.64 was earned
on some stricter protocol the paper's evaluation section must pin down (candidates: the
test_small split of 3,238, a project-held-out design, or different training length), and the
recreation is not passed until that protocol is identified and matched. The RoBERTa arm is
running under the identical shipped-split protocol and now serves as a replication of the
anomaly rather than an independent gate attempt. Next: fetch the paper's exact evaluation
paragraph, add an evaluation arm on test_small, and a leave-one-project-out arm, which the
five-project structure makes cheap to define.

## L69 · RoBERTa replicates the overshoot, which pins the inflation on the split rather than the pipeline

**Hypothesis.** *(G141, the recreation's second fine-tune.)* If the BERT overshoot (L68) comes
from the leaky shipped split rather than from a fault in our fine-tuning pipeline, a second
architecture trained under the identical protocol should overshoot by a similar amount.

**Method.** RoBERTa fine-tuned three epochs on the shipped train split (49,212 events),
evaluated on the shipped test split (12,292 events), weighted F1 against the published 0.64.

| arm | weighted F1 | published gate | verdict |
|---|---|---|---|
| BERT (L68) | 0.741 | 0.64 | NOT-MATCHED, overshoot |
| RoBERTa (this entry) | 0.730 | 0.64 | NOT-MATCHED, overshoot |

*Caption: the two fine-tuned encoder arms of the ScholaWrite recreation, identical protocol, on
the shipped train/test split. The gate is the paper's published weighted F1 for both models.*

**Found.** Weighted F1 **0.730**, nine points over the gate and within 1.1 points of BERT. Two
architectures, one protocol, one overshoot.

**Means.** The inflation is a property of the split, not of either model or of our pipeline,
which is what the L68 audit predicted (a within-project split with 85 percent unique
before-text overlap across the boundary). The recreation stays NOT-PASSED until the paper's
actual evaluation protocol is pinned and matched; the owed arms are the fetch of their exact
evaluation paragraph, an evaluation on the test_small split, and a leave-one-project-out
design.

## L70 · The zero-shot reader arm lands in the published collapse regime, and cannot match the value by construction

**Hypothesis.** *(G141, the baseline arm.)* The paper's zero-shot baseline (Llama-8B, weighted
F1 0.13) collapses far below the fine-tuned encoders; a local model run zero-shot on the same
task should land in that collapse regime.

**Method.** The local nine-billion-parameter reader, zero-shot with the paper's fifteen
intention labels, on 1,500 events sampled from the shipped test split, weighted F1 against
their Llama-8B's 0.13.

**Found.** Weighted F1 **0.172**. NOT-MATCHED under the exact-value standard, and this arm
cannot pass that standard as run, because it uses a different model than the paper's.

**Means.** The paper's headline contrast reproduces qualitatively: fine-tuned encoders sit near
0.73 here while a zero-shot reader sits near 0.17, so the intention taxonomy is learnable from
the data and not available by prompting. Two honesty notes. The 0.042 excess over their 0.13
is owned by the model difference, and closing it exactly would mean downloading, running, and
removing their exact Llama-8B, held as an option and low priority since this arm is a baseline
rather than the claim. And unlike the fine-tuned arms, no train/test leak can inflate a
zero-shot reader, so this number does not ride the split caveat.

## L71 · The polish-side author-share excess replicates on books

**Hypothesis.** *(PD-33b.)* The L57 finding, polish-side features carrying more author-bound
variance than depth-side features at fixed topic, should hold in the same direction on a second
corpus of a different register and genre, the 34-book fiction corpus.

**Method.** Window features (80-word windows) over book segments, 10 authors, 102 segments. For
each feature, the between-author share of its variance; the polish-side and depth-side feature
banks then compared as two distributions of that share (Mann-Whitney, two-sided). On books the
author share includes topic, since each author's books carry their own subjects, so the
polish-against-depth contrast within the corpus is the comparison that survives that
contamination, and the absolute shares are not comparable to the essay corpus's.

| feature side | median between-author variance share |
|---|---|
| polish-side | 0.061 |
| depth-side | 0.020 |

*Caption: between-author share of variance per feature, medians over each feature bank, on the
books corpus. Mann-Whitney two-sided p = 2.8 × 10⁻⁷. Verdict REPLICATES.*

**Found.** The polish side carries three times the depth side's author-bound share, same
direction as the essays, p = 2.8 × 10⁻⁷.

**Means.** The maker-signature reading of the polish side holds beyond student essays, now on
two corpora with different registers, genres, and topic structures. What this corpus cannot
speak to is the absolute size of the effect, since author and topic are confounded here by
construction; the direction and the contrast are the replication. Still one window size.

## L72 · The exact replication, v3: binary side nearly theirs, fine side still structurally short

**Hypothesis.** *(G136.)* With multi-purpose cells reduced to one purpose per revision pair
(v3), their features, their sentence encoder, their classifier grid, and their five folds should
reproduce all eight published cells to two decimals.

**Method.** 3,323 sentence pairs, XGBoost over their published grid, the large Universal
Sentence Encoder, plain five-fold cross-validation, unweighted-average F1 and accuracy per arm,
each against the paper's number.

| arm | our F1 / acc | published F1 / acc | delta (F1, acc) |
|---|---|---|---|
| binary, majority | 0.367 / 0.580 | 0.37 / 0.58 | −0.003, −0.000 |
| binary, features | 0.879 / 0.880 | 0.90 / 0.90 | −0.021, −0.020 |
| binary, USE | 0.874 / 0.875 | 0.92 / 0.92 | −0.046, −0.045 |
| binary, features+USE | 0.874 / 0.875 | 0.93 / 0.93 | −0.056, −0.055 |
| fine, majority | 0.053 / 0.316 | 0.05 / 0.29 | +0.003, +0.026 |
| fine, features | 0.281 / 0.504 | 0.44 / 0.58 | −0.159, −0.076 |
| fine, USE | 0.270 / 0.537 | 0.49 / 0.62 | −0.220, −0.083 |
| fine, features+USE | 0.277 / 0.537 | 0.51 / 0.63 | −0.233, −0.093 |

*Caption: all eight cells of the ArgRewrite sentential replication, one purpose per pair, against
the published values. Verdict NOT-MATCHED.*

**Found.** The binary majority baseline matches to rounding and the fine majority F1 does too,
while the fine majority *accuracy* runs 2.6 points high; binary model arms sit 2 to 6 points
short; fine model arms remain 16 to 23 F1 points short.

**Means.** The extraction's class composition is nearly theirs but not exactly: 3,323 pairs
against their 3,238, and the majority-accuracy excess says the class marginal still differs,
so a dedup or filtering rule of theirs is still unmodeled. The n is the search map: find the
rule that yields exactly 3,238 and the fine-task composition should follow. The binary side is
close enough that only the composition hunt separates it from a pass; the fine side's gap is
structural, not tuning.

## L73 · The collision: the recovery margin survives matching in reduced form, inside the prereg's silent band

**Hypothesis.** *(G130c.)* Does the pilot's 22.7-point purpose-recovery margin survive the same
covariate matching that collapsed content identifiability (L66)? Pre-registered bands: SURVIVES
at margin ≥ 0.10, COLLAPSES under 0.05.

**Method.** The coarsened-exact-matched event subset reconstructed by shared seed (674 events on
common support, four candidates, analytic chance 0.25); the recovery arm (sees the revision
delta) and the blind arm (does not) run identically to pilot-c; the arms compared pairwise on
the same events (exact McNemar).

| construction | blind floor | recovery | margin over blind |
|---|---|---|---|
| full pilot-c set (L65) | 0.232 | 0.477 | 22.7 points |
| matched subset (this run) | 0.402 | 0.484 | 8.2 points |

*Caption: purpose recovery against its text-blind floor, on the full truth-balanced set and on
the covariate-matched subset. Chance is 0.25 in both.*

**Found.** Recovery barely moves under matching (0.477 to 0.484). The floor is what moves: the
blind arm jumps from 0.232 to 0.402, so the margin falls from 22.7 to 8.2 points. The remaining
margin is real, 147 events right only with the delta against 92 right only without it, exact
McNemar p = 4.5 × 10⁻⁴.

**Means.** On common support, purposes are substantially guessable without ever seeing the
revision, so most of the headline margin was carried by the covariates that matching balances,
and what seeing the delta itself adds is roughly eight points, significant and 2.8× smaller.
The pre-registration's own bands leave 0.05 to 0.10 silent, so the formal verdict is neither
SURVIVES nor COLLAPSES; the number landed in the gap the prereg left. Follow-ups filed: a
powered replication of the matched construction, and a floor decomposition asking which
covariates raised the blind arm to 0.40.

## L74 · Polish moves and depth stays, on books; both flat on short essays — the movement claim's first valid instrument

**Hypothesis.** *(PD-34.)* The restated movement account, attention reallocating across
sub-goals over a long stay with a piece, predicts polish-side features carry positional
structure while depth-side features are stationary. PD-1's void showed dispersion statistics
cannot ask this; an order-sensitive statistic can.

**Method.** Per item and feature, the absolute Spearman trend of the 80-word-window series
against window position, z-scored against 100 within-item shuffles (a null that is valid here
precisely because the statistic is order-sensitive); planted-trend and planted-noise ruler gates
run before any data (passed: planted trend z 4.8, planted noise mean z 0.14); polish-side and
depth-side feature banks compared across features by Mann-Whitney.

| corpus | items | polish median z | depth median z | p | verdict |
|---|---|---|---|---|---|
| books | 102 | 0.52 | 0.013 | 1.3 × 10⁻⁵ | POLISH-MOVES-MORE |
| student essays | 197 | 0.024 | 0.005 | 0.42 | NO-DIFFERENCE |

*Caption: positional structure per feature side, mean shuffle-z per feature, medians over each
bank. Higher z means the series carries more order than its own shuffles.*

**Found.** On books, polish-side features carry real positional structure while depth-side
features sit at their shuffle null, forty-fold apart at p = 1.3 × 10⁻⁵. On the short student
essays both sides are flat.

**Means.** The section-closing claim, depth stationary within an artifact while polish is not,
has its first support from an instrument that can actually see movement, and only on long-form.
The essays' double-flat is what the mechanism itself predicts, since attention reallocation
needs a long stay and an eight-window essay barely has one, but corpus length is confounded
with genre and editing here, so the moderation reading stays a hypothesis. Banks are 34 against
14 features, one window size.

## L75 · The protocol arms' first returns: 0.64 matches neither obvious split, and the leak is worth twenty points

**Hypothesis.** *(G141.)* The published 0.64 was earned on one of the candidate protocols the
shipped dataset supports: the leaky shipped test split, the small test split, or a
project-held-out design.

**Method.** Identical fine-tuning (three epochs, same hyperparameters as the L68/L69 arms),
evaluated per protocol. Leave-one-project-out trains on the combined shipped splits minus one
project and tests on that project.

| protocol | model | weighted F1 | against the published 0.64 |
|---|---|---|---|
| shipped test (within-project, leaks) | BERT / RoBERTa | 0.741 / 0.730 | +10 / +9 |
| shipped test_small | RoBERTa | 0.468 | −17 |
| held-out project 1 | RoBERTa | 0.520 | −12, no published analogue |
| held-out project 3 | BERT | 0.512 | −13, no published analogue |

*Caption: the same training recipe under four evaluation protocols. The remaining test_small
and leave-one-project-out folds land through the day.*

**Found.** The small split undershoots the published number by seventeen points; leak-free
cross-project evaluation sits at 0.51 to 0.52 for both architectures.

**Means, recorded as part of the experiment record per the standing directive.** What we now
know about their construction: the published 0.64 sits strictly between the leaky
within-project protocol (nine to ten points above) and every leak-free protocol we can build
from the shipped data (twelve to seventeen below), so their evaluation was neither of the
obvious candidates run with this recipe. The remaining candidates are a different training
regime (more epochs, dev-set early stopping, different windowing) or an unshipped split. Two
structural facts came out regardless: the within-project leak is worth about twenty points at
matched architecture, and cross-project intention transfer at 0.51 is the honest difficulty of
the task, far above the 0.13 zero-shot floor. The exact-evaluation-paragraph fetch is now the
blocking item for this recreation.

## L76 · The n hunt: no dedup rule exists, one label is exactly the excess, and their own F1 pins their majority share

**Hypothesis.** *(G136.)* Some deduplication or filtering rule yields the paper's 3,238
sentential examples from our 3,323.

**Method.** Fourteen extraction-rule variants enumerated on the raw event stream (dedup keys
over pair, sentence, and cycle; no-op, pure-addition, and pure-deletion drops), each reporting
its n and majority shares; then per-raw-label counts inside the fine classes; run as
`run_arg_dedup_hunt.py`, composition arithmetic only.

| rule family | n | note |
|---|---|---|
| split-all purposes (v2) | 3,365 | |
| first-per-pair (v3) and every dedup variant of it | 3,323 | a fixed point; there are no duplicates left to remove |
| structural drops (additions, deletions, aligned-only) | 2,236 / 2,812 / 1,725 | all overshoot far past the target |
| v3 minus the raw label 'precision' | **3,238** | exact, the label carries exactly 85 events |

*Caption: the hunt for the paper's n. No dedup rule reaches it; one label exclusion does,
exactly.*

**Found.** The +85 excess is composition, not duplication. The raw purpose 'precision' carries
exactly 85 events. Separately, the paper's published majority F1 of 0.05 pins their majority
share arithmetically: the unweighted nine-class F1 of a majority-only predictor is
(2s/(1+s))/9, which equals 0.0500 at share s = 0.290 exactly.

**Means, the model-structure record.** Their construction differs from ours in at least two
places, and the two are now separable. Dropping 'precision' hits their n exactly but moves our
majority share the wrong way (0.316 to 0.325 against their 0.290), so beyond the 85-event
exclusion there is a redistribution out of the word-usage/clarity class (ours 1,051 events,
theirs about 939 by the F1 identity). The suspects for the redistribution are our
first-listed-purpose pick among multi-purpose pairs against some other priority of theirs, and
the level-0 fallback our extractor uses where level-1 annotation is empty. The confirmation arm
(fine task with 'precision' dropped, n = 3,238) is queued; the multi-purpose pick-priority
census is the next cheap diagnostic if it falls short.

**Reversal (2026-08-11, L79).** Both working inferences above died to the paper's own Table 4.
'Precision' is a real class carrying 85 examples (two different 85s, a coincidence), and the
0.290 majority share was derived from a printed Majority row that contradicts the paper's own
class table; the true construction is the Revision-Index unit with multi-purpose discard. The
noprecision arm was withdrawn before running.

## L77 · The ScholaWrite protocol, pinned at source: two missing levers, a published bug, and a self-inconsistent target

**Hypothesis.** *(G141.)* The published training and evaluation protocol, recovered from
primary sources, explains why 0.64 matched no shipped protocol under our recipe (L75).

**Method.** Research subagent over primary sources: the arXiv LaTeX for four paper versions
read directly, the authors' repository cloned with its git history, the HF dataset API, and
the project's GitHub issues. Every load-bearing claim below is from a READ source.

**Found.**
1. **The shipped train/test is the published split**, random over keystrokes, so the
   within-project leak we measured is inherent to the published protocol; no leak-free
   variant exists in the paper. The small test split is the 300-per-label budget subset built
   for the LLM baselines (GPT-4o's 0.08 is on it, definitively), not the agreement subset;
   the 0.71 agreement number is a 12-class, 1,011-item quantity including an Artifact class,
   not comparable to the model F1s.
2. **Two protocol levers our recipe lacked.** Balanced class-weighted cross-entropy (built
   with an arange hack that adds one phantom instance per class, then weight-sum
   normalization), and input equal to the FULL before-text right-truncated at 512 tokens,
   which keeps the near-invariant head of the LaTeX document, wrapped in special tags whose
   mismatched closing tag is a real bug in the published run; the senior author's own open
   issue says it "silently corrupts all training samples" and calls for retraining the
   affected checkpoints (verbatim: "Retrain any checkpoints that were produced with the
   buggy tokenization"; the earlier paraphrase here wore quote marks it had not earned —
   corrected 2026-08-16 against the fetched issue text). Also: 10 epochs, weight decay 0.01, no dev set, no early
   stopping, the final-epoch checkpoint, and the reported metric read off a printed
   classification report's weighted-average row.
3. **The published 0.64 is not self-consistent.** The paper's own per-class table (14 classes
   listed; Scientific Accuracy silently absent) reweights to about 0.59 under the full test
   distribution and about 0.51 under the small split. No *plausible* test distribution
   reaches 0.64 from the paper's own per-class values (the referee's correction, L107: the
   literal maximum over arbitrary distributions is 0.83, so the original "no class
   distribution" wording overstated).
4. The training code pins a dataset revision (`anonymous_data`) that outsiders cannot read;
   our gated access can, so the membership diff is runnable here and gates interpretation.

**Means, the model-structure record.** Our overshoot decomposes into three named causes: our
tail-of-text input saw the live editing region where theirs saw the document head, our
unweighted loss rode the 57 percent majority class where theirs sacrificed it, and both
recipes share the split leak. The recreation's gate is redefined honestly: matching a printed
digit the paper's own table contradicts is not a pass, so the faithful arms reproduce their
exact pipeline, bug included, and the pass comparison is the per-class F1 profile against
their table, with the headline expected in the 0.59 to 0.64 band. Queued: the revision diff,
then both faithful arms.

## L78 · The BST figure-level half becomes runnable: the human data digitized from vector figures and validated eight for eight

**Hypothesis.** *(G137.)* The figure-level half of the inverse-planning recreation needs the
paper's human judgment data, which no archive supplies; the question was whether it is
recoverable at all.

**Method.** Research subagent over primary sources: both PDF versions of the paper, the
11-page supplementary appendix (the formal model specification, freely hosted by the
publisher's CDN), and the first author's successor codebase. The decisive move: every figure
in the paper is pure vector, the scatter markers are zero-length dot paths whose coordinates
decode to data units, so the agent extracted the marker sets and rebuilt the data. Validation
is threefold in the source and re-run locally: recomputing Pearson r from the extracted
columns reproduces every printed correlation; consecutive rating triples sum to 1.000,
matching the paper's per-stimulus normalization; and the human coordinates are identical
across model panels to five decimal places.

| experiment | recomputed r (M1 / M2 / M3 / H) | printed |
|---|---|---|
| Exp 1 (Fig 5, 100 triples) | .8271 / .9780 / .9424 / .9658 | .83 / .98 / .94 / .97 |
| Exp 2 (Fig 8, 285 points) | .5804 / .9501 / .5892 / .9178 | .58 / .95 / .59 / .92 |

*Caption: correlations recomputed from the digitized human and model columns against the
paper's printed values; the local re-check (`run_bst_refcheck.py`) passes all eight. The
reference data lives at `results/bst2009_reference/` with the extraction scripts.*

**Found.** The behavioral data is recovered, not approximated: 100 Experiment-1 stimuli, 95
Experiment-2 points, and the complete 32-value Experiment-3 human side, with the
targeted-analysis subset recoverable as a flag. The exact fitting procedure is pinned from
the appendix: plain Pearson pooled over all conditions and judgment points; grids of ten
beta values 0.5 to 5 and twenty gamma or kappa values 0.05 to 1; bootstrap cross-validation
resampling data points (not subjects), ten thousand iterations, training size 50 for
Experiments 1 and 2 and 20 for Experiment 3; Experiment 3 alone maps model log-odds through
z-scores and the normal CDF before correlating.

**Means, the model-structure record.** Four of our recorded gate facts were wrong or
incomplete and are corrected in the same pass: the M3 parameters we carried for Experiment 1
were Experiment 3's; best-fit and cross-validated values are different numbers per cell and
must never be crossed; the H heuristic (M2 with gamma exactly 1) was missing from our
implementation plan entirely, and it beats M3 in both experiments, a headline of the paper;
and the goal prior is uniform over all non-obstacle grid squares, not the three marked
goals. Two contradictions live in the source itself, the text's 99 stimuli against the
figure's 100 distinct triples, and Fig 5 against Fig 6f on M3's beta, so an off-by-one in
stimulus alignment is expected rather than alarming. Owed to the figure arm now: the H
model, the exact gamma parameterization with its self-transition mass, the wide prior, the
Experiment-3 pipeline, and the stimulus geometry extraction from Fig 3 (walls are filled
rects, paths are positioned glyphs, so it decodes the same way). No independent quantitative
replication of this paper exists anywhere the agent could find; ours would be the first.

## L79 · The ArgRewrite construction, pinned at source: the unit was wrong, two candidates die, and the published majority row contradicts the paper's own table

**Hypothesis.** *(G136.)* The paper's exact sentential construction, recovered from primary
sources, explains the remaining composition gap (L72/L76).

**Method.** Research subagent over the paper's LaTeX source (the accepted manuscript's actual
markup, not a rendering), the corpus's canonical Java toolkit, a third-party notebook using
the same corpus, and our local spreadsheets, with the candidate rules executed against them.

**Found.**
1. **The unit is the Revision Index.** One example per group of rows sharing 'Revision Index
   Level 0', purposes unioned across the group, many-to-many texts joined; and units carrying
   more than one distinct purpose are **discarded outright** (the paper: annotation-guideline
   violations, 54 of them), not resolved to a first or priority label. The corpus's own
   toolkit and an independent third-party notebook both implement exactly this.
2. **Both of our L76 candidates are dead.** 'Precision' is one of the nine classes with 85
   examples in the paper's own Table 4, so our 85-event excess matching it was a coincidence
   of two different 85s. And the .29 fine-majority target was arithmetic on a bad row: Table 4
   puts word-usage at 1,030 of 3,238 (share .318, implying Majority .32/.48), so the printed
   .29/.45 contradicts the paper's own table, the same defect appearing in three of the four
   Majority cells. **Our measured 0.316 was correct behavior, not a composition error.**
3. **Our extractor's rebuilt v4 lands at 3,236 of their 3,238**, cycle-1 count exact at
   1,627, three fine classes exact (a fourth only if the binary Content cell counts, L109), and the residual is a known ~11-unit word-usage/organization
   label difference between the released spreadsheets and the authors' snapshot, unrecoverable
   and worth 0.3 percent. Our old aligned-index parsing also had a real bug (comma-separated
   many-to-many indices truncated to the first, orphaning sentences into fake deletions).
4. **The rest of the pipeline is pinned.** Features: per sentence, length, position, a
   19-tag POS term frequency (their worked example fixes the tag order), and one count per
   transition-word **group** (six groups, their Appendix C list). Classifier: the final
   hyperparameters are published in table footnotes (binary 500 estimators, depth 4, rate
   .05; fine 750, depth 5, .05), so no grid search is needed; evaluation is plain 5-fold,
   macro F1, mean over folds. The USE embedding channel was independently health-checked and
   is not the problem.
5. **The remaining fine-arm gap has a named suspect.** The paper's per-class fine F1s (.54 on
   an 85-example class, .45 on precision) are implausible from unweighted training under
   plain 5-fold; undescribed class rebalancing is the leading candidate, queued as an arm.

**Means, the model-structure record.** Composition is now pinned to two examples out of
3,238 against a corpus release that itself differs from the authors' snapshot by about
fourteen units, which is as exact as the public data permits. The fine Majority gate is
corrected to the table-implied .05/.32, with the printed row's contradiction recorded rather
than chased. What remains between us and the model-arm numbers is protocol, not data: the v4
arms run with the published hyperparameters, with and without balanced weighting, and if the
fine arms stay near .28 after that, the residual lives in an evaluation choice the paper does
not describe. The lesson that generalizes: both of yesterday's plausible inferences (an
exclusion rule and a pinned share) were killed by one table read at source, which is exactly
why the recreation standard demands the fetch before the chase.

**Supplement (same day, the agent's own runs on the corrected construction).** Balanced
sample weighting is falsified as the missing ingredient, moving fine macro F1 by at most
0.02; the corrected feature spec lifts the binary features arm to .887 against their .90; and
the per-class breakdown localizes the entire fine gap to the six small classes, with the
model never emitting organization, rebuttal, or precision at all, and grammar/spelling at .12
against their .39 despite 239 examples, so scarcity alone is not the story. Two mechanism
candidates follow. Concatenated embeddings never state *what changed*, so explicit difference
features are one arm; and an arithmetic single-cause hypothesis, that their fine experiment
mildly oversampled (about 1.49×) exactly the five classes their own §5.4.1 calls
underrepresented, would simultaneously produce the printed .29 majority, the .45 word-usage
F1, and rare-class F1s of .35 to .54, none of which are otherwise reproducible. That
hypothesis is inference from arithmetic, marked as such, and it predicts the fine row cannot
be faithfully reproduced from the released 3,238 without the rebalancing; both arms are
queued, and the oversample arm's three predictions make it self-gating.

## L80 · v4 under the published hyperparameters: both majority baselines exact, large classes reproduce, small classes collapse

**Hypothesis.** *(G136.)* With the pinned construction (L79) and the paper's published
footnote hyperparameters, the eight cells should land on the published values, against the
corrected fine-majority gate.

**Method.** The v4 extraction (3,236 units), their features (POS-19, six transition groups,
both positions), USE-large embeddings, XGBoost at the footnote settings (binary 500/4/.05,
fine 750/5/.05), plain five-fold, macro F1 and accuracy averaged over folds, per-class F1
from pooled out-of-fold predictions.

| arm | our F1 / acc | target F1 / acc | delta F1 |
|---|---|---|---|
| binary majority | 0.369 / 0.585 | .37 / .58 | −0.001 |
| binary features | 0.883 / 0.884 | .90 / .90 | −0.017 |
| binary USE | 0.875 / 0.876 | .92 / .92 | −0.045 |
| binary features+USE | 0.872 / 0.873 | .93 / .93 | −0.058 |
| fine majority | 0.054 / 0.321 | .05 / .32 (table-implied) | +0.004 |
| fine features | 0.246 / 0.513 | .44 / .58 | −0.194 |
| fine USE | 0.249 / 0.553 | .49 / .62 | −0.241 |
| fine features+USE | 0.249 / 0.550 | .51 / .63 | −0.261 |

*Caption: all eight cells under the pinned construction and published hyperparameters. The
fine majority gate is the Table-4-implied value per L79; the printed .29 row stands confirmed
unreachable from the released data.*

**Found.** Both majority baselines now match their self-consistent published values to
rounding, so composition is validated end to end. The per-class profile reproduces the
agent's localization in our own pipeline: word-usage 0.75, general-content 0.54, reasoning
0.48 (their .79/.60/.60), while organization and rebuttal sit at exactly zero, precision at
0.02, grammar/spelling at 0.06.

**Means.** The recreation has split into a solved half and a sharply-posed half. Everything
about the data is now right, and the binary arms sit two to six points short, close enough
that encoder-version drift is a live explanation. The fine model arms are not short, they are
structurally different: the accuracy gap is seven points while the macro-F1 gap is
twenty-six, which is exactly the signature of rare classes the published row somehow scores
and ours never predicts. The two queued mechanism arms (explicit difference features; the
1.49× five-class oversample with its three self-gating predictions) are the discriminators,
and if both miss, the honest close of this row is that the published fine numbers are not
reproducible from the released corpus as described.

**Supplement (same day, the agent's final diagnosis).** Difference features are a partial
fix with the mechanism confirmed: adding the explicit delta and cosine to the embedding block
buys +.036 macro, and the gain lands exactly where the mechanism says, grammar/spelling
rising from .12 to .47 and overtaking the paper's own .39, since a spelling fix is defined by
a small surface change a bare concatenation never states. The decisive finding is a perfect
partition: across the nine classes, our mean gap against the paper is −.025 on the four
classes their §5.4.1 does NOT list for augmentation and −.338 on the five it does, and the
split is not a size effect, since grammar/spelling (239 examples, not listed) is one we now
beat while claim (234, listed) trails by 21 points. With three facts converging, the fine
majority row implying ~314 extra examples outside word-usage, the binary majority matching
the unaugmented table exactly, and the gap partitioning along the augmentation list, the
inference (marked as inference) is that their fine BASE rows were computed on an
already-oversampled set, with +DA a further augmentation on top. The prediction: the
published fine rows are not reproducible from the released 3,238, and roughly .30 is the
correct unaugmented number for their feature set. The gates are re-scoped accordingly in the
TODO row, and the binary arms, where the released data supports the target, get the
difference features next.

## L81 · The oversample arm reproduces the "unreachable" majority row exactly and brackets their fine model rows; the diff mechanism confirms in-house

**Hypothesis.** *(G136.)* The augmentation inference is self-gating: a 1.49× oversample of
the five §5.4.1 classes predicts the printed fine majority .05/.29 (shown unreachable from
the released corpus in L79), the majority word-usage F1 of .45, and raised rare classes; the
difference-features mechanism should reproduce in our pipeline.

**Method.** The v4 construction with a seeded 0.49× duplication of the five named classes
before cross-validation (3,544 examples), published hyperparameters, plain five-fold, with
the difference-features arm run beside it unaugmented.

| arm | fine features+USE F1 / acc | fine majority F1 / acc |
|---|---|---|
| unaugmented v4 (L80) | .249 / .550 | .054 / .321 |
| + difference features | .299 / .584 | same |
| 1.49× oversample | .568 / .628 | **.050 / .293** |
| paper, base row | .51 / .63 | .05 / .29 (printed) |
| paper, +DA row | .56 | |

*Caption: the two discriminator arms against the paper's printed rows. The oversample arm's
majority cell reproduces the printed row that the released corpus cannot produce.*

**Found.** Two of the three self-gating predictions hit exactly: the printed majority row
comes back to the digit (.050/.293 against .05/.29, with the majority word-usage F1 at .45
by the same arithmetic), and model-arm accuracy lands on their .63. The third overshoots in
the diagnostic direction: rare classes come back at .55 to .72 rather than their .35 to .54,
and the overall macro (.568) overshoots their base .51 while landing within .008 of their
+DA row (.56), which is the signature of duplicated examples leaking across
cross-validation folds. The difference arm confirms the agent's mechanism in-house:
+.05 macro, grammar/spelling .064 to .490, overtaking the paper's own .39, with the three
never-predicted classes unmoved.

**The third arm, for completeness.** Balanced class weighting confirmed in-house as the
agent found it: fine macro rises from .246/.249/.249 to .278/.269/.273, two to three points
against a twenty-four point gap, so it is a real but minor effect and not the mechanism.

**Means, the model-structure record.** The composition claim graduates from arithmetic
inference to in-pipeline demonstration: their fine experiment ran on an oversampled set, and
a plain pre-CV duplication reproduces their +DA cell to a hundredth, suggesting +DA itself
was duplication with fold contamination. Their base fine row (.51) sits between our
unaugmented .30 and our duplicated .57, consistent with rebalancing confined to training
folds or a milder operation, and the released corpus cannot decide which. The fine half of
this recreation closes on that evidence: majority and composition demonstrated, the four
non-augmented classes within a dime of published, the five augmented classes exempt with the
mechanism shown rather than merely inferred. The binary .93 gate stays live, with the
difference features queued there as the last lever.

**Referee downgrade (2026-08-14, L107): the demonstration reverts to inference, with
counter-evidence logged.** The paper's §5.4.1 names training-fold synonym replacement at
about 3.4×, a mechanism that cannot leak across folds, where this arm was pre-CV exact
duplication at 1.49× — hitting their cell by a mechanism the source disclaims is a
coincidence, not a confirmation. And the inference fails on the sibling table: the
subsentential fine and binary Majority cells deviate in the wrong direction for a systematic
oversample. What survives: the released 3,238 cannot produce the printed fine-Majority row
under any construction yet found, and the four non-augmented classes are within a dime.

## L82 · The full leak-free grid: cross-project transfer is project-dependent and far below the published number, and the small split fails for both architectures

**Hypothesis.** *(G141.)* The leave-one-project-out folds give the leak-free difficulty of
intention prediction, and the second small-split arm tests whether the published 0.64 lives
there.

**Method.** All ten leave-one-project-out folds (both architectures, three epochs, identical
recipe), plus BERT trained on the shipped train and evaluated on the shipped small split, as
RoBERTa was in L75.

| held-out project | test n | BERT F1 | RoBERTa F1 |
|---|---|---|---|
| 1 | 14,217 | 0.458 | 0.520 |
| 2 | 5,059 | 0.263 | 0.355 |
| 3 | 6,641 | 0.512 | 0.608 |
| 4 | 8,348 | 0.378 | 0.381 |
| 5 | 27,239 | 0.348 | 0.359 |
| mean | | 0.392 | 0.445 |

*Caption: weighted F1 per leave-one-project-out fold. For reference, the same recipe scores
0.741/0.730 on the leaky shipped split and the paper prints 0.64. The small split: BERT
0.526, RoBERTa 0.468, both far under 0.64 and six points apart.*

**Found.** Leak-free transfer ranges 0.26 to 0.61 by project, means 0.39 and 0.44, so the
within-project leak is worth roughly thirty points on average, not the twenty the first two
folds suggested. The small split fails as the 0.64 protocol for both architectures, and the
six-point architecture disagreement there sits oddly against the paper's identical 0.64/0.64
pair. One infrastructure fact closes an arm: the dataset revision pinned by their training
code no longer exists on the Hub even under our gated access, so the shipped main revision is
the only canonical data anyone can now train on, and the revision caveat becomes permanent
but soft.

**Means.** The recreation's remaining hope is the faithful arms now training (their exact
protocol, bug included, per-class gate). What the grid contributes regardless is the honest
structure of the task: intention prediction transfers across projects at 0.4-ish with high
project dependence, everything above that is memorization of a writer-project's local
patterns, and any future use of this dataset in the program (G132) must be leave-one-project-out
by construction.

## L83 · Phase-1 lessons: what three recreations taught about modeling, recorded as method

**Hypothesis.** *(The curator's directive: lessons learned in modeling from the duplication
efforts are part of the experiment record.)* The recreation phase should yield transferable
method, not only verdicts.

**Method.** Synthesis over L60 to L82, the three subagent source-pins, and the discriminator
arms.

**Found, five lessons.**
1. **Composition before tuning, always.** Every gap that closed in this phase closed through
   construction, the unit rule, the split, the oversample, never through hyperparameters; the
   one grid search we ran over-selected (picking a learning rate the authors' own footnote
   contradicts) and still explained nothing.
2. **Published tables fail their own arithmetic at working rates.** Three of four majority
   rows in ArgRewrite contradict its own class table; ScholaWrite's headline is unreachable
   from its own per-class table; BST's text and figures disagree on a count and a parameter.
   Three papers, three internal inconsistencies. The standing step this adds: before gating
   on a published number, check it against every other number in the paper that constrains it
   (the F1 identity, distribution reweighting, subtotal sums). It cost minutes and caught all
   three.
3. **Protocol leverage dwarfs model leverage.** Measured on these tasks: split leakage twenty
   to thirty points; pre-evaluation oversampling thirty-two macro points; class weighting
   two; architecture choice one to six. A benchmark number is mostly its construction, which
   is this project's own thesis (the reading lives in the making) arriving from an unexpected
   direction.
4. **Pair tasks need the change stated.** Explicit difference features rescued exactly the
   classes defined by small surface edits (grammar/spelling .06 to .49). The transfer to our
   own instruments is direct: any reader arm judging a revision must see the delta
   explicitly, which the G129 candidate-set design already does by construction and must
   keep through every redesign.
5. **Deliberate contamination is an instrument.** Reproducing an "impossible" published cell
   by seeded pre-CV duplication (L81) turned an inference into a demonstration. The
   duplication probe enters the toolkit with its signature named: exact majority-row
   reproduction plus rare-class overshoot above the published band.

**Means.** Phase 1's product is not the verdicts alone but a recreation protocol: pin the
construction at source, self-consistency-check the paper's numbers, reproduce bug-for-bug,
and when a number resists, try to reproduce it by breaking your own pipeline in the way you
suspect theirs was broken. That last move is what separates "we failed to match" from "we
know why the number is what it is."

## L84 · Difference features on the binary task: a point and a half, gap narrowed to three to four, encoder version now the sole candidate

**Hypothesis.** *(G136.)* The explicit-change features that rescued grammar/spelling on the
fine task should also help the binary surface/content split, the one gate still live from
the released data.

**Method.** The v4 construction, binary task, published hyperparameters, with the USE block
extended by the embedding delta, its absolute value, and the cosine.

| arm | without diff (L80) | with diff | target |
|---|---|---|---|
| binary features | .883 | .883 | .90 |
| binary USE | .875 | .888 | .92 |
| binary features+USE | .872 | .887 | .93 |

*Caption: the difference features buy 1.3 to 1.5 points on the embedding arms and nothing on
the feature-only arm they do not touch. Majority stays exact.*

**Found.** The gap narrows to 1.7 points on features and 3.2 to 4.3 on the embedding arms.

**Means.** Every in-corpus lever is now spent: composition exact, features theirs,
hyperparameters theirs, the change stated explicitly. What remains between .887 and .93 had
one named candidate left at the time of this entry, the encoder version (their 2021-era
sentence encoder against our current export). **That candidate was then refuted rather than
confirmed (L85): the two plausible checkpoints agree to a quarter point, so the gap is not
encoder-version indeterminacy and must not be recorded as such.** The live account is
upstream of the encoder entirely.

## L85 · The binary gap is not the encoder: two checkpoints agree, and nineteen string-diff features reach their Features row

**Hypothesis.** *(G136.)* The residual 3 to 4 point binary shortfall (L84) is encoder-version
drift between their 2021-era sentence encoder and our current export.

**Method.** Research subagent, but this one tested rather than argued: our exact numbers
reproduced first, then each candidate run directly on the real task with the published
hyperparameters and five folds. Encoder variants swapped (the transformer export against the
deep-averaging export, the only two readings of their one-sentence description, both released
before their submission), classifier families compared on identical embeddings, tree method
and fold stratification varied, duplicate and author leakage audited, then a headroom probe
with nineteen cheap surface features measuring what changed.

| candidate | effect on binary macro F1 |
|---|---|
| encoder variant (deep-averaging against transformer) | ≤ 0.3 points, mixed sign |
| classifier family (logistic, linear and radial SVM against boosted trees) | boosted trees already best; ceiling ~.876 |
| tree method (histogram, exact, approximate) | 0 to 0.3 points |
| stratified folds | −0.4, the wrong direction |
| duplicate pairs, author leakage | zero; ±0.7 mixed |
| **nineteen string-diff features alone** | **.8968 F1 / .8993 accuracy** |

*Caption: each candidate measured on our own pipeline. The last row is nineteen integer
features, no embeddings, against their published Features row of .90/.90.*

**Found.** The encoder hypothesis is refuted: the two candidate checkpoints agree to a
quarter point on every arm, and no classifier family exceeds .876 on either. Meanwhile
nineteen surface measures of the delta beat all thousand-dimensional embedding
representations and land on their Features row, and **adding embeddings to them costs a
point**. Forty-eight percent of these pairs have one empty side, so how much changed is most
of the available signal. The distinguishing signature is structural: their arms rise
monotonically (.90, .92, .93) while ours plateau and invert, embeddings never beating counts.

**Confirmed in-house, same day.** The change block reimplemented in our own pipeline with a
known-answer check (identical sentences give unit similarity and zero edits; an emptied
sentence gives zero similarity and the right delete count) reproduces the effect: change
features alone .892/.895, the features arm rising .883 to **.895 against their .90**, and the
combined arm .896 against their .93. So their feature row is effectively reproduced and the
embedding rows are not, in our hands as in the agent's. One defect of ours fired and was
fixed in the same pass: the new arm has no published target and the reporting line assumed
every arm had one, which crashed the first run after all four numbers had been computed.

**Means, the model-structure record.** The irreducible unknown is upstream of everything we
had been varying. At the time of this entry the leading candidate was the sentence alignment
behind their pairs, named in a deleted line of the paper's source; the two-vector combination
and possible search optimism rode behind it. So the close was **the Features row is
reproducible and the embedding rows are not reproducible from the published description**,
gap bounded at 3.3 points best against best. Two hazards of ours were fixed in the same
pass: thread count was tied to whatever else the host was running (now pinned), and the
change-feature finding transfers directly to our own instruments, since a revision is defined
by its delta and no representation that fails to state the delta will carry the task.

**The alignment candidate refuted at source (next day).** A follow-up agent read Zhang &
Litman 2014, both corpus papers, and both public aligner repositories, then reimplemented the
aligner and measured it against the released spreadsheets. Three published statements pin the
provenance: sentences were "first automatically aligned (Zhang and Litman, 2014), then
manually corrected by human"; the alignment was "performed semi-manually"; and the
experiments "assume revisions are pre-segmented and pre-aligned." The purpose labels are
physically attached to the human-corrected alignment (the deleted line was a redundant
restatement of a surviving sentence), so **the released alignment IS the experiments'
alignment and no tighter set of pairs exists**; the reimplemented aligner agrees with the
release at 94 to 96 percent, exactly the aligner's own published accuracy band, and every
disagreement is an error relative to the human correction. The remaining unpinned surface was
the evaluation protocol itself: the source carries a stray "10-fold cross-validation" comment
against the published "5-fold", and the cells may be randomized-search maxima. **The 10-fold
arm ran and missed**: fold count moves every arm by at most half a point with mixed sign
(features .8948, embeddings .887 to .891 against .92/.93). That exhausts every public route:
composition exact, features theirs, hyperparameters theirs, encoder refuted, alignment
refuted at source, folds refuted. Final state, corrected by the consensus fleet (L109): the faithful Features arm lands at
.883 against their .90 (gap .017); the .895 previously labeled "the Features row" carries our
19-dimension change block, which the paper's 5.1 does not include, so it is our
features-plus-delta arm, not their row. For the embedding rows the honest label is
**we did not reproduce them** (the referee's relabel, L107) with the gap bounded near three
points — and the two surviving candidates turn out to be locally measurable after all:
max-over-their-published-grid is queued, and the standard four-block pair encoding
[u; v; |u−v|; u⊙v] is the owed build. "Reachable only through the authors" was premature;
the two arms are the last word; author contact is off the table, his ruling 2026-08-14. An
exhaustive follow-up sweep confirmed no processed pair file for this corpus exists anywhere
public (their project domain is dead and was never archived with data), and found one
corroboration: the only public third-party preprocessor for these spreadsheets reads exactly
the columns and purpose mapping our v4 construction reads, an independent implementation
agreeing with ours.

## L86 · The faithful ScholaWrite arm lands on the paper's self-consistent value, not on its printed one

**Hypothesis.** *(G141.)* Reproducing their exact protocol, published bug included, should
land the headline in the 0.59 to 0.64 band and put the per-class profile beside their table,
which is the gate this recreation was re-scoped to after the printed 0.64 proved unreachable
from the paper's own per-class values (L77).

**Method.** Their pipeline as pinned from their repository: the full before-text wrapped in
their tag sequence with its published closing-tag typo, six added special tokens with resized
embeddings, right truncation keeping the first 512 tokens (the document head), balanced
class-weighted cross-entropy built with their arange hack and sum normalization, ten epochs,
weight decay 0.01, no dev set, no early stopping, the final checkpoint, seed 42, evaluated on
the shipped test split with the weighted average of a classification report.

| quantity | ours | the paper |
|---|---|---|
| headline weighted F1 | **0.580** | 0.64 printed; **~0.59** implied by its own per-class table |
| our earlier recipe (tail input, unweighted loss, 3 epochs) | 0.741 | |
| Text Production (57% of the data) | 0.63 | 0.63 |
| mean absolute per-class deviation, 14 shared classes | **0.116** | |
| Scientific Accuracy | 0.27 | absent from their table |

*Caption: the faithful arm against the paper's printed headline and against the value implied
by reweighting the paper's own per-class table. Full per-class comparison in
`results/scholawrite/bert_faithful.json`.*

**Found.** The two protocol levers we had been missing moved the headline sixteen points, from
0.741 to 0.580, landing inside the predicted band and **within 0.01 of the paper's own
self-consistent value**. The largest class reproduces exactly. Per-class agreement is
respectable but uneven: eight of fourteen classes within 0.1, with Section Planning and
Citation Integration low by about 0.2 and Cross-reference and Visual Formatting high by about
0.2. And a prediction of the source audit is confirmed: Scientific Accuracy, silently absent
from their fourteen-row table, is a class our model does predict, at 0.27.

**Means.** Under the exact-value standard this is **not a pass at the printed digit and
cannot be**, because the printed digit is contradicted by the paper's own table. What it is:
the protocol reproduced faithfully enough to land on the number the paper's internals
actually support, with the residual per-class scatter of about 0.12 the honest measure of
what remains unspecified (data-order effects, their unstated seed, and the ambiguity over
which test set the published cell used). The recreation's contribution is therefore a
correction to the literature rather than a matched number: the published 0.64 is not
reachable from the released data under the authors' own code, and roughly 0.58 to 0.59 is
what that pipeline produces.

**The replication landed (same day).** RoBERTa under the identical faithful protocol:
weighted F1 **0.546**, against its printed 0.64, with mean per-class disagreement between the
two architectures of 0.044. Both faithful arms land in the mid-to-high 0.5s, both far from
the printed digit, and their three-point spread is the same architecture spread the leaky and
small-split protocols showed. The claim replicates: this pipeline, run as published, produces
0.55 to 0.58, and the paper's identical 0.64/0.64 pair is not a reachable outcome of the
released materials. The ScholaWrite recreation row closes on that finding. *(Superseded: CLOSURE-PENDING per L107/L109; the correction stands, the closure awaits the framework-faithful seed interval.)*

**The provenance hunt completed the chain (next day).** A follow-up agent traced the 0.64 to
its source and it is a **stale first-version number never recomputed**: byte-identical across
four arXiv revisions and into the ACL camera-ready while models were added around it, and
silently contradicted by the per-class table that first appears in the fifth revision, whose
weighted reweighting is **0.5939 on the full test split**, within 0.014 of our faithful BERT,
with no per-label-capped subsample able to exceed it. The vanished private evaluation repo is
identified by composition (it is the 300-per-label subsample, verified as exactly the shipped
small split's construction and a strict subset of test), and it moves scores DOWN, so it
cannot be the 0.64's source; the vanished dataset revision had the shipped composition (the
camera-ready's per-project table totals the shipped corpus exactly), so no earlier-data story
survives either. The tag typo's status is corrected by the second referee (L108): the
paper-era code carried the same wrong closing tag on BOTH sides, so there was never a
train/eval mismatch to reproduce, 89 percent of inputs truncate the tag away entirely, and
the current repository's one-sided "fix" created the mismatch it appears to document. The
typo is inert; nothing about the 0.64 gap can be attributed to it, which strengthens the
irreproducibility reading. One ambiguity remains in
their sources and it is testable: their inference script's checkpoint number factorizes as
epoch 10 at effective batch 16 or **epoch 5 at effective batch 8**, the appendix's
one-GPU-batch-8 wording supports the second reading, and epoch 5 sits precisely where our
3-epoch (0.741) to 10-epoch (0.580) bracket crosses 0.64. That arm is running; if it lands
near 0.64, the printed number was an epoch-5 checkpoint read, and the recreation closes
matched rather than corrected.

**The epoch-5 arm landed (2026-08-12): 0.6094, NOT-MATCHED, and the correction is final.**
The last live route to a matched close misses by three points — the epoch axis is now swept
end to end under the faithful protocol (3 epochs 0.741, 5 epochs 0.609, 10 epochs 0.580,
RoBERTa at 10 epochs 0.546) and the printed 0.64/0.64 is unreachable from the released
materials at any checkpoint reading. The reproducible band from their own code and data is
0.55 to 0.61, bracketing the value their own per-class table implies (0.5939) from both
sides; the epoch-5 cell sits at the top of that band, closest to the print and still short.
Scientific Accuracy is again predicted (0.328) while absent from their table. The only
residue left is their unstated seed and data order, which no public lever reaches. **The
ScholaWrite recreation closes as a correction to the literature: roughly 0.58 to 0.61 is
what the published pipeline produces, and the printed digit is a stale first-version number.**
One process note rides along (L93): this arm took two days to land a three-hour training
because it ran as a standalone process that every engine relaunch's orphan sweep killed
mid-epoch; the lesson is banked in LESSONS §5.

## L87 · The mapping sweep: neither G20a nor G20b in any of eleven families, and one new universal

**Hypothesis.** *(G20a/G20b, with G143 riding along.)* The two candidate block-mappings, never
tested directly: under A, valence decodability peaks early and category mid; under B, valence
mid and category late. G143's operational form: the block where decodability beyond the
lexicon starts rising is the interface handoff candidate.

**Method.** Per family, per block: valence probes (positive against negative single-label
emotion sentences), category probes (among the emotional classes), and the same valence probe
on word-shuffled copies, whose gap against the original is decodability beyond the lexicon.
Pre-registered thirds for the mapping verdict, a peak-prominence rule (0.03 over the curve
median, else FLAT and no address claimed), and a label-permutation ruler gate per family.
Eleven families, 0.35B to 3B, four architectures.

| verdict | families |
|---|---|
| FLAT, no address claimable | six |
| NEITHER band pattern | five |
| G20a or G20b | **zero** |

*Caption: all gates clean (permuted-label probes 0.49 to 0.54). Valence decodability sits
near 0.78 to 0.81 at nearly every depth in every family, category near 0.31 to 0.38; peak
prominences hover at 0.02 to 0.05 and peak locations scatter from 0.17 to 0.71 of depth with
no cross-family law. Full curves in `results/g20_mapping/`.*

**Found.** Affect information is distributed nearly uniformly through depth everywhere.
Neither mapping survives contact with a direct test, in the same deflationary way every
address claim in the project has resolved. The one positive universal: a beyond-lexicon
component exists in **all eleven families**, the original-text probe pulling ahead of the
lexicon-preserving shuffled probe by a sustained margin somewhere between 0.11 and 0.53 of
depth, onset obeying no law.

**Means.** The G20 question dissolves rather than resolves: the rotating-subspace picture
(one coherent affect structure decodable almost everywhere, rotating with depth) was already
the standing account, and this sweep confirms there is no address for the mappings to
disagree over. G143's handoff, read as an address, fails like every address; read as an
existence claim, it survives, since composition-beyond-lexicon is real and universal. The
word-shuffle condition carries its known caveat as an out-of-distribution input; here it
defines the lexical bound rather than controlling a fixed measure, and the bound is the
comparison both curves share.

## L88 · Two layers, not one question twice: the leak battery's standing caveat resolves in its favor

**Hypothesis.** *(G28.)* The leaked and emblematic reads may be one question asked twice;
until tested, every leak result was equally compatible with that.

**Method.** 150 complete triples over book segments: a leaked-layer read, an emblematic-layer
read, and a second leaked read at a different seed as the built-in test-retest ceiling; each
read distributes 100 points over the eight concepts; per-text profile correlations, paired
bootstrap on the difference.

| comparison | mean profile correlation |
|---|---|
| leaked against emblematic | 0.597 |
| leaked against leaked, retest | 0.725 |
| difference | 0.128, CI [0.069, 0.188] |

*Caption: the between-layer agreement sits clearly below the same prompt's own test-retest
agreement. Verdict TWO-LAYERS.*

**Found.** The two prompts return reliably different affect distributions from the same
texts, beyond reader noise.

**Means.** The probe is not asking one question twice, which un-hedges every leaked-layer
result in the battery by exactly the amount that caveat was worth. The modest retest ceiling
(0.725) prices the reader's own noise, and the open successor is G29, which layer carries the
maker signal, predicted in advance to be the leaked one if either fails.

## L89 · Polish decays, machines move most, and the movement asymmetry is window-bound: three corrections in one family

**Hypothesis.** *(PD-2, PD-3, and the robustness caveats on PD-33/PD-34.)* The signed form
of the movement statistic tests decay specifically; machine long-form tests the no-maker
prediction of flatness; and the second window size tests whether the family's results are
window artifacts.

**Method.** The PD-34 instrument in signed mode (mean signed trend per feature, Wilcoxon on
the polish bank against zero, ruler gates passing in both modes), on books, essays, and the
machine extreme-specification corpus; the unsigned form and the author-share split rerun at a
40-word window.

| test | result | verdict |
|---|---|---|
| PD-2, books | polish median signed z −0.30, p = 0.012 | POLISH-DECAYS |
| PD-2, essays | polish −0.17, p = 3.6 × 10⁻⁶ | POLISH-DECAYS |
| PD-3, machine long-form | polish z **+0.65** against depth −0.05, p = 2 × 10⁻⁶ | **REVERSED: machine moves most** |
| PD-34 at w40, books | polish 0.15 vs depth −0.02, p = 0.15 | NO-DIFFERENCE, the w80 asymmetry does not transfer |
| PD-33 at w40, books | shares 0.033 vs 0.017, p = 3.6 × 10⁻⁶ | REPLICATES |

*Caption: the signed arm, the machine control, and the window-robustness arms. Note the
essays showed no |trend| asymmetry yet decay cleanly in signed form: many small
sign-consistent trends are invisible to magnitude statistics.*

**Found.** Polish-side features fall across position on both human corpora, the direction the
original get-lazy quote predicted before its restatement. But the machine corpus, predicted
flat, shows the **largest** polish movement in the family, and the books movement asymmetry
vanishes at the smaller window while the author-share split survives it untouched.

**Means, and the afterword-level correction.** The attention-reallocation reading of L74 is
now contested by its own control: a corpus with no maker and no attention moves more than the
books do, so generic position-register structure (openings, closings, and specification
scaffolding differing in readability-class features) is a live rival account for all
positional polish movement, and the long-stay story cannot claim the books result until a
design separates position-register from reallocation. The decay direction (PD-2) survives
this reinterpretation, since it holds on both human corpora including where magnitude showed
nothing, but its meaning inherits the same ambiguity. Meanwhile the maker-signature half of
the family (PD-33) is the robust one: two corpora, two window sizes, four results, no
exceptions. Window size joins the lessons as a member of the statistic family rather than a
nuisance choice.

## L90 · The account separator: human polish falls, machine polish rises, on the same instrument

**Hypothesis.** *(The PD-2/PD-3 collision's separator.)* If positional polish movement is
generic document-register geography, machine long-form should share the human direction; if
the movement carries the maker, the directions may dissociate.

**Method.** The signed movement arm on the machine extreme-specification corpus, plus
window-robustness arms for every signed result.

| arm | polish signed z | test against zero | verdict |
|---|---|---|---|
| essays, 80-word window | −0.17 | p = 3.6 × 10⁻⁶ | decays |
| essays, 40-word window | −0.14 | p = 4 × 10⁻⁶ | decays, window-robust |
| books, 80-word window | −0.30 | p = 0.012 | decays |
| books, 40-word window | +0.01 | p = 1.0 | null; the books decay is window-bound |
| machine, 80-word window | **+0.92** | p = 3 × 10⁻⁶ | **RISES** |
| machine, 40-word window (unsigned) | +0.31 | p = 2 × 10⁻⁴ | movement window-robust |

*Caption: signed positional trend of polish-side features, per corpus and window. Human
corpora fall; the machine corpus rises, strongly, at both windows.*

**Found.** The direction dissociates by provenance. Both human corpora trend downward (the
essays at both windows; the books only at the wide one), while machine polish climbs across
position with the largest magnitude in the family.

**Means.** The simple register-geography account predicted a shared direction and is
weakened; attention-reallocation regains the essays evidence it lost to yesterday's reversal.
And an unplanned instrument fell out of the collision: **the sign of the polish trend
separates human from machine long-form** on this instrument, a candidate discriminator that
now owes the full funnel (register-matched pairs, length control, a second machine generator)
before it is believed, since the machine corpus here is specification-stacked essays rather
than register-matched prose, and this project has buried ten cheap discriminators for less.
The books' fragility keeps the human-side claim modest: the robust human decay is the essays'.

## L91 · Which layer carries the maker: both do, weakly, and the predicted asymmetry does not appear

**Hypothesis.** *(G29, predicted in advance: if one layer fails to separate, it is leaked.)*
Author classification from the eight-concept profiles of the G28 triples, per layer.

**Method.** 150 book segments, 9 authors, logistic classification of author from the 8-dim
profile per arm, five-fold; floor is the measured majority share (0.133); sixty
label-permutations per arm as the null; the leaked-retest arm doubles as the stability
reference.

| arm | author accuracy | permutation p |
|---|---|---|
| leaked | 0.193 | 0.033 |
| emblematic | 0.227 | 0.016 |
| leaked, retest | 0.240 | 0.016 |

*Caption: all three arms beat the floor and their permutation nulls; none is strong. Chance
under permutation ~0.12.*

**Found.** Both layers carry author identity above floor and null, at 1.4 to 1.8 times the
floor; neither fails, so the advance prediction's trigger condition never fires. The nuance
runs slightly against the Morellian expectation: the emblematic (performed) layer carries as
much or more identity than the leaked layer here.

**Means.** A first-pass answer with named limits: eight numbers per text from one reader is a
narrow pipe, and "author" on this corpus is confounded with era and genre, so the performed
layer may be carrying period convention rather than person, which would explain the
direction. The two-layers result (L88) stands unaffected, since distinctness was established
against retest, not against identity-carrying. The clean next form is the same analysis at
fixed era, or on the function-word side where identity machinery is already validated.

## L92 · Abandoned scaffolding, first pass: the instrument works, and machine text carries the most debris

**Hypothesis.** *(G80, reserve versus overpaint's cheapest observable.)* Abandoned
scaffolding (promised counts unfulfilled, orphan "first"s, dangling forward references) is
computable on one static text.

**Method.** Three regex-family counters, ruler-gated (a planted document with two known
abandonments and a clean document score 2 and 0 before any corpus is read); run over human
first drafts (86 whole documents), book segments (170 mid-book excerpts), and machine
long-form (75 whole documents).

| corpus | mean abandoned per doc | share with any |
|---|---|---|
| human first drafts | 0.186 | 0.19 |
| books (excerpts) | 0.271 | 0.27 |
| machine long-form | **0.400** | 0.40 |

*Caption: human-vs-machine p = 0.0028; human-vs-books p = 0.16. The books number is inflated
by construction, since mid-book excerpts truncate enumeration chains and orphan their
ordinals, so the clean whole-document comparison is drafts against machine.*

**Found.** The instrument passes its gate and separates on first use: machine long-form
leaves abandoned scaffolding at twice the human-draft rate.

**Means.** Read within its limits, this is the overpaint side of the cue made countable, and
the direction is theory-consistent: a generator plants structural promises (the
specification-stacked corpus promises much) and does not track their fulfilment the way a
maker revising toward a reader does. First pass only: regex counters, one machine corpus, and
the books-excerpt confound named above; the fiction-register machine corpus now being
generated gives this instrument its cleaner second comparison for free.

## L93 · The methods pass: one live entry rests on a selection artifact, one positive still runs uncontrolled, and the void shelf sorts into four flippable and two not

**Hypothesis.** *(His directive, 2026-08-12: go through the findings very carefully, informed by
the method section; report mistakes given current knowledge, plan the reruns, and try to flip
voids.)* The record, read against the lessons file it postdates, should contain entries whose
methods violate what we now know.

**Method.** The five method-shelf files re-read in full, then every Tier-1 entry and the Tier-2
tables read against them: each verdict checked for the lesson classes (known-answer gates,
criteria that can fail, selection and range restriction, owed interpretation controls, power
versus verdict, statistics written to disk), each owed follow-up traced into TODO.md and the
queue, and every VOID assessed for a flip route. Suspicious cells re-derived from the runners and
raw outputs rather than from the entries' prose.

**Found, in severity order.**

1. **L44 (the pooling falsifier) rested on a selection artifact and is corrected this pass.** The
   runner took the first forty manifest items of a rung-ordered manifest: every ratio-versus-rung
   cell was computed on rungs 0 and 1 only, the mean-pooling baseline (−0.045) reproduced no known
   value of the quantity it attacked, and the failed reproduction was explained away in prose that
   also mis-stated the fair-control record. The recreation standard we apply to other people's
   papers (a large shortfall means your pipeline model is wrong, hunt it) was not applied to our
   own falsifier. Correction folded into L44; theory row and afterword corrected; rerun queued
   with a reproduce-gate.
2. **L16's function-word separation still has no induction control (G76), and the TODO spec for
   that control is itself stale** — it specifies regressing on raw specification identity, the
   dose-eating construction L22 proved absorbs the true effect. The control must be built in the
   within-rung form (L23). Until it runs, a three-corpus SEPARATES verdict on the second
   artifact-side channel is uncontrolled against induction, the exact confound that killed three
   candidates before the fair control revived them.
3. **The choice-recovery margin's verdict sits in its prereg's silent band with both filed
   follow-ups unrun** (L73: powered matched replication; floor decomposition). The program's head
   result (8.2-point margin, p = 4.5 × 10⁻⁴) is real but unadjudicated by its own bands.
4. **Two standing weaknesses have no queue presence at all.** Weakness 5 (the 16× scale gap
   between the affect directions' 12-word fitting sentences and the 200-word windows they score)
   is marked "effect unmeasured" and touches every affect-projection result in the project.
   Weakness 6 (the no-maker corpus generated by the reading model's own family) now has its
   second-family generator confirmed available and still no consumer stage.
5. **L40 (the flagship's no-maker layer concentration) is UNDECIDED at power** (p = 0.095/0.089)
   with 36 no-maker artifacts; the standing near-significance policy (raise n, freeze everything)
   was never applied to it. Expanding the no-maker corpus with the second family flips this and
   tests weakness 6 in one stage.
6. **Cheap owed methods checks never run:** G112 (characterise the gpt2 mirror, saved maps
   suffice), G94 (the Taramsa test — does our reconstruction posit decisions that were not
   there, runnable on the ladder where truth is known), G97 (maker as a random effect —
   our within-maker positives pool artifacts within makers and have never been re-fit
   hierarchically), G102 (the prior-art sweep owed before any public ratio-versus-dose claim),
   and L39's register-matched machine arm (the fiction corpus now generating supplies it).
7. **One infrastructure defect, mechanism pinned:** the night loop's startup orphan sweep kills
   any stage python no live loop owns; the standalone epoch-5 ScholaWrite arm was exactly such an
   orphan, so every engine relaunch killed the training mid-epoch and the waiter restarted it
   from zero — roughly two days of Sisyphus for a three-hour job. Long standalone GPU arms need
   either checkpoint-resume, queue membership, or a keep-list entry in the sweep.

**The void shelf, assessed for flips.** Four flippable: **the refusal test** (V3/G77 — the
question is intact, the 50%-false-positive threshold just needs replacing with a permutation
test); **the affect-count instrument** (V6/G106 — four named defects, all repairable, plus
topic-controlled generation replacing found text); **L40's undecided permutation null** (power,
per item 5); **and the L44 ratio cells** (rerun queued). Two not flippable as posed: **Gate 3's
half-corpus question** (the corpus is burned — over-read and broadly confounded; the question
re-poses honestly only at the event level, which is G129's preregistration, so the program IS the
flip); **L18's depth-follows-domain pilot** (blocked on the one-maker-many-kinds corpus, the
sourcing problem, not a method fix). Already flipped by earlier work and needing nothing: V1
(L17/L23), V2 (L21), V4/V5 (L16 at power; PD-11's powered rerun running now), the coherence
instrument (G105 → L47), and PD-1's dispersion void (the movement statistic, L74).

**Verified clean while looking.** The multiplicity audit is current (reran this morning, no
flips); the Tier-2 settled tables contradict nothing in Tier 1; the 08-11 result files that
looked like silent re-runs were first landings committed the same day (no wasted compute); and
the L47 sub-chance agreement baseline (0.43 against a 0.49 random floor) stands as the one open
instrument anomaly, recorded, unclaimed, and not load-bearing for any verdict.

**Means.** The record holds one defective live entry (corrected), one uncontrolled positive
(control queued), and a backlog whose common shape is controls-owed-but-unscheduled rather than
wrong verdicts. The reruns are queued in cost order: the pooling rerun and G76 first (hours,
cached inputs), then the no-maker expansion serving L40 and weakness 6 together, the G130c floor
decomposition, and the cheap CPU checks (G112, G94, G97); the scale-gap measurement (weakness 5)
is the largest build and the deepest reach, since it underlies every affect-projection number in
the file.

## L94 · The function-word channel survives its owed induction control on the two strong ladders, and the old control form is shown killing everything

**Hypothesis.** *(G76, owed since L16 landed; built this pass in the fair form after the methods
audit found the filed spec still described the dose-eating construction L22 killed.)* The
function-word separation may be reading style the prompt induced rather than a maker state; if
the separation is not explained by which specifications were drawn, it should survive
residualization on the within-rung-centred specification indicators.

**Method.** `run_g76_fw_induction.py`, CPU. Per ladder: the 124 closed-class rates per artifact
(L16's frozen list), the seeded specification-indicator reconstruction (verified arithmetic from
the fair-control runner), within-rung centring, out-of-fold ridge residualization of every rate,
then rung classification from the residuals (logistic, stratified folds, accuracies averaged
over ten fold seeds because the n = 50 corpus proved fold-seed fragile). Floors measured by 200
label permutations. Known-answer gates before any real read: a planted dose bank must survive
the control (it does, 0.52 against 0.20 chance), a planted pure-identity bank must classify at
chance in both arms (it does, 0.17/0.24). The raw arm doubles as a reproduce-gate against L16's
recorded cells.

| ladder | raw (L16 reference) | fair-residual | permutation p | old-form residual | verdict |
|---|---|---|---|---|---|
| first (n = 50) | 0.288 (0.32) | 0.252 | 0.22 | 0.130 | **COLLAPSES** |
| held-out (n = 100) | 0.359 (0.33) | **0.439** | < 0.005 | 0.134 | **SURVIVES** |
| extreme (n = 75) | 0.435 (0.467) | **0.443** | < 0.005 | 0.167 | **SURVIVES** |

*Caption: accuracy classifying which of five rungs an artifact came from (chance 0.200), from
raw function-word rates, from the rates after fair (within-rung) specification-identity removal,
and from the rates after the old dose-eating removal. All three raw baselines reproduce L16
within tolerance.*

**Found.** On the held-out and extreme ladders the separation survives the fair control at full
strength — the controlled accuracy even sits above raw, the suppression signature the ratio
showed under the same control. On the first ladder (the weakest manipulation, ten
specifications, fifty artifacts) it collapses to chance. And the old form of the control, the
one the TODO spec still described, lands every corpus at or below chance with dose leaks of
0.45 to 0.71 — it would have killed a channel the fair form passes, exactly as L22 predicted.

**Means.** The second artifact-side channel now carries the same license as the ratio and the
three revived features: on the strong ladders, what the function words separate is not explained
by which specifications were drawn. The inherited caveat travels with it (L22): induction
operating through the count of specifications is indistinguishable from a dose response by any
regression control. The first-ladder collapse reads most naturally as power at the weakest dose,
consistent with L16's own effect-size ordering; it is recorded as COLLAPSES on that corpus, not
explained away. Theory row updated (DECISION_TRACES §3); the old-form demonstration closes the
stale G76 spec permanently.

## L95 · PD-11 at power: function words separate specified affect states at the pre-registered bar

**Hypothesis.** *(PD-11, the test the standing near-significance policy was adopted for and never
re-run on.)* Function-word rates separate texts generated under four specified maker affect
states. The original came back at 1.80× chance (p = 0.0047) against a pre-registered 2.0× bar —
significant, below threshold — and the policy says raise the power with everything frozen.

**Method.** `run_d0b.py --arm local --k 20 --seed-base 9000`: the original design held out and
frozen (same four affect specifications, same generator, same Burrows-Delta leave-one-out
classifier over closed-class rates), fresh seeds, twenty generations per state against the
original ten — doubled scored n (80 against 40). The verdict statistic was recomputed inline as
an exact binomial (the runner printed its verdict on the lift alone and now writes the p, the
L89 lesson applied).

| arm | accuracy | chance | lift | exact binomial p |
|---|---|---|---|---|
| original (k = 10) | 0.450 | 0.25 | 1.80× | 0.0047 |
| **powered rerun (k = 20)** | **0.5625** | 0.25 | **2.25×** | **2.6 × 10⁻⁹** |

*Caption: leave-one-out accuracy assigning each generated text to its specified affect state from
function-word rates alone. Per-class on the rerun: seeking 0.85, fear 0.55, rage 0.50, care 0.35.
First-person rates run 14.5 to 19.0 per thousand words, so the Poisson-floor failure that voided
the first attempt is gone.*

**Found.** The powered rerun clears the pre-registered bar: 2.25× chance, forty-five of eighty
correct where chance expects twenty. Seeking is nearly ceiling; care is the weak class.

**Means.** The standing policy earns its keep on the test that created it: what was recorded as
"significant but below its bar" is a clean pass at doubled n with everything frozen. Function
words track specified maker *state* on generated text, at the bar, with no model in the loop.
The scope limits stand unchanged: generated text only (the E38 warning that this does not
license the human claim), one generator family, and states specified by prompt. Theory row
updated (DECISION_TRACES §3).

## L96 · The gpt2 mirror is not mysterious: the fixed loci straddle opposite-signed machinery, and the band decomposition predicts the family sign in eight of eleven

**Hypothesis.** *(G112, owed since the sign map completed.)* The fair-control ratio's sign is a
family constant with no family sharing the home family's negative (L28). If the per-layer
dose-correlation profile, banded at the home-chosen 7% and 76% loci, carries each family's sign,
the mirror is band structure and no deeper mystery.

**Method.** `run_g112_mirror.py`, CPU over the saved held-out-ladder per-layer maps: per family,
the mean per-layer correlation between the affective signal and rung inside the early band
(layers at or below 7% of depth) and the late band (at or above 76%). The ratio statistic is
early over late, so the banded prediction for its dose sign is the sign of early-band tracking
minus late-band tracking, compared against the measured sign map.

| family | early band | late band | predicted | measured | match |
|---|---|---|---|---|---|
| Qwen 0.5B / 1.5B / 3B | −0.29 / −0.13 / −0.04 | +0.03 / +0.27 / +0.02 | − / − / − | − / − / − | 3/3 |
| gpt2 medium / large | +0.50 / +0.05 | −0.42 / −0.41 | + / + | + / + | 2/2 |
| gpt2-xl | +0.00 | −0.20 | + | null | miss |
| SmolLM2 360M / 1.7B | −0.40 / +0.00 | −0.08 / −0.18 | − / + | + / + | 1/2 |
| pythia 410m / 1.4b | −0.24 / −0.17 | −0.40 / −0.27 | + / + | + / + | 2/2 |
| pythia-2.8b | −0.25 | +0.01 | − | null | miss |

*Caption: mean per-layer rung correlation of the affective signal inside each band, the sign the
band difference predicts for the ratio's dose relationship, and the fair-control sign the family
actually measures. Eight of eleven match.*

**Found.** MIRROR-EXPLAINED. The home family's negativity comes from early machinery tracking
dose negatively while late machinery tracks positively; gpt2 is the exact mirror (early strongly
positive, late strongly negative), and the ratio inherits the sign of the difference. The two
null-cell misses are directionally consistent with the fade: gpt2-xl's early band sits at
+0.003 and pythia-2.8b's bands nearly cancel, so the ratio goes quiet where the band difference
does. The one genuine miss is SmolLM2-360M, whose bands predict negative while the family
measures positive — the odd family for the third time, after the alignment refusal and the fade
exemption.

**Means.** Two of G112's three facts now have an account: the sign is band structure at the
chosen loci, and the fade lands where the bands cancel. What the decomposition does not explain
is SmolLM2, which now carries three independent oddities and is the right single target for the
subspace route (G124's aligned-stage form) if the characterisation is pushed further. The
selection caution sharpens: the loci were chosen where the home family's bands happen to
diverge most, which is exactly the anatomy of an accidental family-specific instrument.

## L97 · The sign-funnel's decisive cells: the machine polish rise is register-robust inside one generator family and absent in the other

**Hypothesis.** *(The L90 discriminator's owed funnel, step 2.)* If the rising positional polish
trend is a machine signature, register-matched machine fiction should rise like the
specification-stacked essays did; if it is register or prompt structure, fiction should not.

**Method.** The movement instrument in both forms on the two fiction corpora (28 whole chapters,
two generator families, same fifteen premises), 80-word windows, ruler gates passing as always
(planted trend z 3.4, planted noise 0.20). Signed form: mean signed trend per polish feature,
Wilcoxon against zero. Unsigned form: the |trend| shuffle-z asymmetry between polish and depth
banks.

| cell | polish signed z | Wilcoxon p | verdict |
|---|---|---|---|
| fiction, home generator (n = 15) | **+1.03** | 0.0088 | **POLISH-RISES** |
| fiction, second family (n = 13) | −0.28 | 0.055 | NO-SIGNED-TREND, marginal in the *human* direction |
| unsigned asymmetry, home generator | polish 1.17 vs depth 0.33 | 5.3 × 10⁻⁴ | POLISH-MOVES-MORE |
| unsigned asymmetry, second family | polish 0.32 vs depth 0.10 | 0.16 | NO-DIFFERENCE |

*Caption: positional polish movement on register-matched machine fiction, by generator family.
For reference: the home generator's essays rose at +0.92, human essays fall at −0.17, books at
−0.30 (L89/L90).*

**Found.** The rise is real and it is not register: the home generator's fiction rises as
strongly as its essays did, in both the signed and magnitude forms. And the rise is not
machine-universal: the second family's fiction is positionally quiet in magnitude and trends
weakly *downward* in signed form, the human direction, at marginal significance on thirteen
chapters.

**Means.** The candidate provenance discriminator dies as a universal — a second-family text
would pass as human on this sign — and what replaces it is sharper as a characterization: the
rising-polish signature is a **generator-family fingerprint**, robust across register within the
family that carries it. Because this instrument is artifact-side (features, no reader model),
the family split is a property of the generators' outputs themselves, immune to the
shared-representation worry. The second family's marginal downward trend is exactly the
near-significance case the standing policy covers: round 2 is queued, same premises, fresh
seeds, both families, and the decisive powered cell is whether the second family's fiction
*decays* like human text at doubled n.

## L98 · The register-matched comparison deflates the scaffolding instrument: it reads prompt burden, not provenance

**Hypothesis.** *(L92's named next step.)* If abandoned scaffolding is a machine signature, the
register-matched fiction corpora should carry it at the specification-stacked corpus's rate; if
it is prompt structure, whole-document fiction from a one-line premise should not.

**Method.** The ruler-gated counters (gate passing: planted 2, clean 0) over the two fiction
corpora, against the standing human-draft and specification-stacked machine cells.

| corpus | mean abandoned per doc | vs human drafts |
|---|---|---|
| human first drafts (n = 86) | 0.186 | — |
| fiction, home generator (n = 15) | 0.267 | p = 0.48 |
| fiction, second family (n = 13) | 0.077 | p = 0.34 |
| specification-stacked essays (n = 75) | 0.400 | p = 0.0028 |

*Caption: the L92 comparison completed with register-matched machine arms. Only the
specification-stacked corpus separates from human drafts.*

**Found.** Machine fiction leaves abandoned scaffolding at human rates — both families,
indistinguishable from drafts — while the specification-stacked corpus keeps its 2× separation.

**Means.** L92's direction is deflated, exactly along the fault line its own entry named: a
prompt that stacks sixty specifications plants promises the artifact does not fulfil, and the
instrument was counting that burden, not machineness. Re-scoped honestly, the instrument
measures **unfulfilled prompt burden** — a real, countable quantity with a plausible use
(estimating how loaded the instruction was from the artifact alone), but not a provenance cue.
The reserve-versus-overpaint import goes back to needing a subtler observable.

## L99 · At power, the no-maker control comes back clean: zero fires at n = 108, and the reader's null behavior is family-neutral

**Hypothesis.** *(L40's owed powered rerun, plus weakness 6's first cell.)* The flagship's
no-maker concentration (7 joint layers at n = 36, overlap 3 of 5 with its survivors, p ≈ 0.09)
is either a real label leak or small-n noise; and if the no-maker control's cleanliness is a
same-family artifact, second-family no-maker text should behave differently under the same
reader.

**Method.** The permutation instrument on the merged frozen-construction corpus (36 original +
72 expansion, fresh seeds), 5,000 permutations; and the same joint rule on the second family's
no-maker corpus (59 artifacts generated by the reasoning-family model under the identical
construction), 2,000 permutations.

| arm | n | joint layers firing | null mean | p | verdict |
|---|---|---|---|---|---|
| original (L40) | 36 | 7 | 1.9 | 0.095 | UNDECIDED |
| **powered, same family** | **108** | **0** | 0.21 | 1.0 | **NO-LEAK-DETECTED** |
| second family | 59 | 2 | 0.79 | 0.17 | NO-LEAK-DETECTED |

*Caption: layers passing the computable joint rule on maker-less text, against label-permutation
nulls. Overlap with the flagship's ladder survivors is zero in both new arms.*

**Found.** At three times the data under the same rule, the concentration vanishes entirely —
zero firing layers, zero survivor overlap — and the fixed correlation threshold explains the
original seven: at n = 36 a rho of 0.2 is barely over one standard error, at n = 108 it is over
two, so the small-n arm was counting noise the powered arm cannot. The second family's arm sits
inside its null the same way.

**Means.** The open liability against the flagship family's survivor list resolves: no label
leak is detectable at power, and the layers keep their standing without the asterisk L40
attached. And weakness 6 loses its load-bearing cell: the reader's null behavior on maker-less
text does not depend on whether its own family generated that text, so the no-maker control's
cleanliness is not a shared-representation artifact. The weakness narrows to the *positive*
results that compare machine and human text directly, where the second-family fiction corpus
now supplies the control arm (L97 already uses it).

## L100 · At power, the second family's fiction decays like human text — the two generators sit on opposite sides of the human sign

**Hypothesis.** *(L97's queued round 2, per the near-significance policy.)* The second family's
marginal downward trend (−0.28, p = 0.055, n = 13) either firms into a significant decay at
doubled n, putting one machine family on the human side of the sign, or dissolves as noise.

**Method.** Fifteen more chapters per family, same fifteen premises at fresh seeds, both-round
feature caches, the signed movement instrument frozen; the powered cells are the pre-registered
second look the policy licenses.

| cell | n | polish signed z | Wilcoxon p | verdict |
|---|---|---|---|---|
| home generator, round 1 | 15 | +1.03 | 0.0088 | POLISH-RISES |
| **home generator, powered** | **30** | **+1.01** | **0.0070** | **POLISH-RISES** |
| second family, round 1 | 13 | −0.28 | 0.055 | marginal |
| **second family, powered** | **27** | **−0.20** | **0.0445** | **POLISH-DECAYS** |

*Caption: signed positional trend of polish-side features on register-matched machine fiction,
first round and powered round. Human reference points: essays −0.17, books −0.30 (L89).*

**Found.** Both cells hold their direction at doubled n. The home generator's rise is stable to
the second decimal; the second family's decay crosses its threshold — its fiction's polish
falls across position at human-comparable magnitude, sitting between the essays' and books'
decay values.

**Means.** The family split is confirmed at power, and it is stronger than a split: **one
machine family carries the human decay signature**. Any provenance use of the sign is now dead
conclusively, since a second-family text does not merely fail to rise, it falls where humans
fall. What remains is a sharp characterization question, filed as G146: the two generators
differ in training lineage (a reasoning-RL model against an instruction-tuned one), and
whichever training difference flips this sign is a mechanism question the parent simulation and
the literature can both bite on. The attention-reallocation account of human decay also
inherits a constraint it did not ask for: whatever produces decay in the second family's
output has no attention and no fatigue, so decay alone cannot carry the reallocation reading
without a design that separates the mechanisms.

## L101 · The reader-side variance signature splits by family too — and its provenance reading deflates to register plus family

**Hypothesis.** *(L39's owed register-matched arm.)* The reader's affective series moves more
within human long-form than machine text (books 0.0102 against ladder text 0.0065, L39), with
register uncontrolled. Register-matched: does the reader's series still sit flat on machine
*fiction*?

**Method.** The same instrument (early/late ratio per 200-word window as a positional series,
variance at matched series length), books against the two fiction corpora, per generator
family, one-sided in L39's direction.

| comparison | books median | fiction median | n | p |
|---|---|---|---|---|
| books vs home-generator fiction | 0.0102 | **0.0117** | 34 / 30 | 0.56 |
| books vs second-family fiction | 0.0102 | **0.0045** | 34 / 23 | 0.0003 |

*Caption: within-artifact variance of the reader's affective series. The home generator's
fiction moves as much as the books do; the second family's sits flat below everything. One
honesty note: the runner's pre-set verdict string keyed on any cell reaching significance and
printed HUMAN-MOVES; the finding is the split, and the label under-describes it.*

**Found.** Register-matched, the home generator's fiction is as dynamically mobile as human
books — the original flat-machine reading was carried by comparing books against essay-register
ladder text. The second family is genuinely flat even at matched register.

**Means.** L39's provenance reading deflates the same way the artifact-side sign did: what
looked like human-versus-machine was register plus generator family. And the convergence is
now the result: **two independent instruments — the artifact-side polish trend and the
reader-side affective series — split identically by family**, the home generator mobile on
both, the second family quiet on both, humans mobile-and-decaying. Whatever G146's mechanism
turns out to be, it moves both the text's surface statistics and a reader model's internal
trajectory together, which is what a real generation-dynamics difference should do. The
sharpened base-versus-post-training fact belongs here too: the second family's local build is
a distillation onto the home family's own base architecture, so the flip tracks
post-training, not the base — and the 2×2 that separates base from post-training is now
queued (G146).

## L102 · The PAN winner pinned at source: the printed target is unreachable by construction, the metric's prose is falsified by its own evaluator, and the reachable gates are the notebook's validation table

**Hypothesis.** *(G147, opened at his ruling reinstating the PAN recreation.)* The 2024
hard-split winner's system and exact numbers, recovered from primary sources, define what a
faithful local recreation can and cannot hit.

**Method.** Research subagent over READ sources: both task overview papers (2024, 2025), the
winner's notebook and the runner-up's, the 2023 overview for a data ambiguity, the official
evaluator's source code verbatim, and an adversarial released-code hunt across GitHub, lab
pages, and archives.

**Found.**
1. **The metric's published prose is wrong about its own evaluator.** All three overview papers
   describe per-document F1 macro-averaged over documents; the evaluator pools every decision
   from every document into one flat list and takes two-class macro-F1, silently dropping any
   document whose prediction length mismatches. The pooled reading is confirmed by six exact
   back-calculations of published baselines from the implied change rates (both years, all
   splits) — the fourth paper this phase whose printed methods contradict a checkable artifact.
2. **The headline 0.863 is on the held-back TIRA test set** (15% of the data, never released),
   so no local recreation can touch it. The notebook publishes its own validation table, and
   that becomes the honest gate: single arms 0.8423 / 0.8567 / 0.8490 (roberta / deberta /
   ernie), majority vote 0.8658.
3. **The hard-split system is smaller than its reputation:** three base-size encoders,
   consecutive-paragraph pairs at max length 256, lr 5e-5, dropout 0.25, ten epochs, effective
   batch 60, two-of-three vote — and the LaBSE similarity stage applies to easy and medium
   only, so the hard result needs none of it. Training data is PAN24 hard plus PAN23 hard
   (4,200 documents each; a typo in the notebook resolved against the 2023 overview). Six
   hyperparameters are unstated (optimizer, warmup, weight decay, schedule, seed, loss) and
   are recorded as named assumptions in our runner.
4. **No released code or weights exist for either year's winner**; the 2024 runner-up released
   partial training code with no license. The winner's notebook also mis-states its own ranks
   twice (team counts and easy-split rank), settled against the overview's table.
5. A calibration fact from the runner-up's own tables: one plain deberta-base, fully
   fine-tuned, scores 0.821 hard on the held-back test set — within 0.042 of the winning
   ensemble — so the single-model reference point is strong and cheap.

**Means.** The recreation is running with honest targets: four queued arms (three members plus
the vote) against the validation gates, per-epoch validation recorded so the unstated
checkpoint rule is measurable, our pooled-form scorer smoke-tested against the published
predict-all-one baseline (0.313 local validation against 0.320 printed test). The metric
correction is banked for LESSONS: an evaluator's source outranks its paper's prose, and the
self-consistency check now includes back-calculating baselines from class priors.

## L103 · The 2×2 lands: three of four machine cells rise, and the human-side decay is one model's exception, not a lineage law

**Hypothesis.** *(G146.)* The sign flip between the first two generator families tracks either
the base architecture or the post-training lineage; a 2×2 crossing base (qwen / llama) with
post-training (instruct / reasoning-distill) separates them.

**Method.** The two llama-base cells generated on the same fifteen premises, two rounds each
(the llama-base reasoning cell is the R1 distillation onto llama-8B, the same post-training as
the qwen-base reasoning cell; llama-instruct is llama3.1-8B), then the signed movement
instrument, frozen, ruler gates passing.

| cell (base × post-training) | n | polish signed z | Wilcoxon p | verdict |
|---|---|---|---|---|
| qwen × instruct | 30 | +1.01 | 0.007 | RISES |
| qwen × reasoning-distill | 27 | **−0.20** | 0.044 | **DECAYS** |
| llama × instruct | 23 | +0.82 | 3.8 × 10⁻⁵ | RISES |
| llama × reasoning-distill | 30 | +0.32 | 0.0028 | RISES |

*Caption: the completed cross. Human references: essays −0.17, books −0.30.*

**Found.** Neither factor explains the flip. The same R1 distillation that decays on the qwen
base rises on the llama base, and both instruct cells rise. Three of four machine cells rise;
the human-direction decay is confined to exactly one model.

**Means.** The G146 question sharpens rather than resolves: the decay is a property of one
model (the qwen-7B R1 distill), an interaction or an idiosyncrasy, not a lineage law. Two
consequences. The "machine polish rises" regularity is rehabilitated as a strong default —
three of four cells, two bases, two post-trainings — with one named exception, which is a
better shape for a characterization than a 2×2 main effect would have been, and a worse shape
for any provenance use, which stays dead (the exception exists and generalization is
unknowable per family). And the human-decay constraint on the reallocation account (L100)
softens back: the one machine cell that decays is a single model, so machine decay is rare
rather than generic, and the reallocation reading regains some of its footing. Window
robustness for all four cells is queued (every cell so far is the 80-word window, the exact
caveat the books result taught); the reader-side instrument's four-family arm is queued
alongside. The adversarial lit check on positional structure under different post-trainings
stays owed.

## L104 · The PAN recreation, first two members: both land above their gates, and the third's crash is the encoder's own fp16 incompatibility

**Hypothesis.** *(G147.)* The winner's three single-encoder arms, trained under their stated
recipe with our named assumptions, should land on the notebook's validation table.

**Method.** Consecutive-paragraph pairs from PAN24-hard plus PAN23-hard train (their
augmentation), max length 256, lr 5e-5, dropout 0.25, ten epochs, effective batch 60, pooled
two-class macro-F1 on the released validation split, per-epoch scores recorded.

| member | our final (best epoch) | their validation gate | delta |
|---|---|---|---|
| roberta-base | 0.8558 (0.8620) | 0.8423 | **+0.014** |
| ernie-2.0-base-en | 0.8650 (0.8701) | 0.8490 | **+0.016** |
| deberta-base (v1) | rerunning fp32 | 0.8567 | — |

*Caption: two of three members land one to two points above the notebook's own numbers. The
majority vote (gate 0.8658) runs when the third lands.*

**Found.** Two members reproduce above gate on the first working run each. Two instrument
facts came out of the failures: roberta-base collapses to constant predictions at the paper's
learning rate without warmup (the paper states none; a 6% warmup is recorded as the
divergence-fix assumption, and their own result implies their run had some equivalent), and
DeBERTa-v1's disentangled attention overflows under fp16 autocast (a masked-fill at half
precision's minimum), so that arm runs fp32.

**Means.** The recipe reconstruction is sound: with six unstated hyperparameters guessed at
defaults, both completed members sit slightly above the printed validation cells, the
direction expected if the authors' unstated choices were near-default and our per-epoch
best-checkpoint numbers bracket their unstated selection rule. The overshoot is one to two
points, not the twenty of a leak; nothing here has the inflation signature. Entry extends
when the deberta arm and the vote land.

## L105 · The window sweep and the four-family completion: the lone decay is window-bound, the two instruments dissociate, and no fiction family carries scaffolding after correction

**Hypothesis.** *(The missed-test audit's catches: every fiction movement cell ran at one
window; the reader-side and scaffolding arms had two-family coverage.)* Window robustness for
all four signed cells; the reader-side variance across the full 2×2; scaffolding rates for
the two new families.

**Method.** The frozen instruments at the 40-word window (signed cells, four families); the
reader-side series variance, books against each family; the ruler-gated scaffolding counters
across all four fiction corpora.

| cell | w80 (established) | w40 | reader-side variance vs books | scaffolding vs drafts |
|---|---|---|---|---|
| qwen instruct | +1.01, p = .007 | +0.64, p = .13 | **parity** (0.0096 vs 0.0099, p = .58) | 0.300, n.s. |
| qwen reasoning | **−0.20, p = .044** | +0.20, p = .18 | flat (0.0045, p = .0005) | 0.148, n.s. |
| llama reasoning | +0.32, p = .003 | **+0.42, p = .006** | flat (0.0031, p < 10⁻⁴) | 0.367, p = .045 uncorrected |
| llama instruct | +0.82, p = 4×10⁻⁵ | **+0.37, p = 10⁻⁴** | flat (0.0026, n = 3, underpowered) | 0.217, n.s. |

*Caption: the four generator families across three instruments. The llama reader-side cell has
three usable chapters only (its pieces run short of the four-window floor) and stays that way:
the top-up failed outright — zero of forty-five pieces met the floor at 900 then at 800 words,
each retried twice — so the model's own chapter length is the ceiling, and scaffolding the
prompt to force length would break the same-prompt construction across families (the L98
lesson). The cell is permanently underpowered at this model.*

**Found.** Three corrections in one sweep. **The lone human-direction decay is window-bound**:
at 40 words the qwen-reasoning cell flips to a positive nonsignificant trend, exactly how the
books decay behaved (L89), while both llama rises are window-robust and the qwen-instruct rise
weakens below significance. **The two instruments dissociate at four families**: the
artifact-side rise holds in three of four, but reader-side mobility at book level belongs to
qwen-instruct alone, so the earlier lockstep claim (two families, L101) does not survive its
own extension, and what the reader's trajectory tracks is not what the surface trend tracks.
**And no fiction family separates from human drafts on scaffolding once four comparisons are
corrected** (the one nominal 0.045 does not survive), leaving the prompt-burden reading of
L98 intact.

**Means.** The movement family's honest summary shrinks to what is window-robust: llama-base
fiction rises at both windows, humans decay where they decay (essays both windows, books wide
only), and every other cell is window- or instrument-conditional. The decay exception of L103
is now doubly qualified (one model, one window). The dissociation is the interesting new
fact: surface polish trend and reader-trajectory mobility are different quantities with
different family structure, which the theory afterword now carries, and it argues for
reporting the two instruments separately rather than as one "movement" story.

## L106 · The PAN overshoot explained: cross-year contamination, with the leaked pairs scored at exactly 1.0

**Hypothesis.** *(The curator's discomfort with L104's overshoot, made testable.)* PAN datasets
are rebuilt from the same Reddit source across years; if the PAN23-hard training documents the
winner's recipe adds overlap the PAN24-hard validation split, every validation number trained
under that recipe — theirs and ours — is inflated by memorization.

**Method.** Exact-hash overlap at three granularities (whole documents, paragraphs, consecutive
pairs) between each training set and the validation split; then the landed members' saved
predictions rescored on the leaked and leak-free pair subsets separately.

| overlap with PAN24-hard validation | PAN24-hard train | PAN23-hard train |
|---|---|---|
| whole documents (verbatim) | 0 | **49** |
| paragraphs | 0.2% | **20.5%** |
| consecutive pairs | 0.2% | **15.8% (651 of 4,131 scored)** |

| member | blended (L104) | leak-free pairs | leaked pairs |
|---|---|---|---|
| roberta | 0.8558 | 0.8273 | **1.0000** |
| ernie | 0.8650 | 0.8381 | **0.9984** |

*Caption: organizer dedup never crosses years (and L108 later showed within-year dedup held
only on the hard split). On the 651 pairs seen
verbatim in training, both members are perfect or one decision short of it — the memorization
signature — while leak-free capability sits at 0.83 to 0.84.*

**Found.** The overshoot's mechanism is measured: about sixteen percent of validation pairs are
verbatim training pairs under the winner's own augmentation recipe, and the models simply
recall them. The winner's published validation table (our gates) carries the same blend by
construction. Whether the held-back test set shares the contamination is unknowable from
outside, and the printed 0.863 inherits that question.

**Means.** Three readings, kept separate. As a recreation, the gate comparison stands and
sharpens: same recipe, same leak, both sides blended the same way, our members one to two
points over their cells. As a capability claim, the honest numbers are the leak-free 0.827 and
0.838, and those are what any layering experiment builds on. And as a literature fact, this is
the fifth paper artifact of the phase: a shared task whose cross-year augmentation (used by its
winners, encouraged by continuity) silently overlaps its own evaluation split at sixteen
percent of decisions. The lesson is banked: any augmentation from a sibling edition gets
exact-hash dedup against every evaluation split before training, and a leaked-subset score of
1.0 is the memorization signature to check for. The deberta arm and the vote will be rescored
on both subsets when they land.

## L107 · The adversarial referee: three of four Phase-1 verdicts move, and the demanded arms are queued

**Hypothesis.** *(His order: an Opus referee, mandated to disagree, over the four assessments
he was uncomfortable with.)* The closures survive independent adversarial reading of the
primary sources, or they don't.

**Method.** One Opus subagent, primary sources fetched and read end to end (five papers, two
supplements, three code repositories, version histories, issue trackers), our runners read as
code, its own contamination check run blind to L106's.

**Found, by assessment.**

1. **ScholaWrite: the correction is CONFIRMED and strengthened, the closure is PREMATURE.**
   Confirmed: the reweighting arithmetic reproduces (0.5947 full test, 0.5059 small); two new
   internal checks land (the printed macro-average is exactly the mean of the fourteen listed
   classes, proving the absent class is genuinely absent; the paper's own printed accuracy of 0.56
   sits 0.08 below its printed F1 — **corrected by the second referee (L108): our arms never
   recorded accuracy, so the "sits where ours sits" half compared their accuracy to our F1
   and is struck; the internal inversion in their own numbers stands, and the framework arms
   now record accuracy so the real check can run**); the 0.64 is
   byte-identical across revisions; the bug attribution to the senior author holds. Broken:
   our "faithful" loop dropped three things their Trainer supplied silently — **linear LR
   decay to zero, gradient clipping at 1.0, and weight-decay exclusion of bias/LayerNorm** —
   so the schedule axis was never swept; the released `include_prev_label` input variant was
   never run; every arm is one seed; and our runner persisted neither predictions nor
   accuracy. One overstatement corrected in place: L77's "no class distribution reaches 0.64"
   is literally false (the claim is no *plausible* distribution). One live alternative logged:
   the per-class table first appears in the paper version posted eleven days after the bug
   fix, so it may describe a post-fix run while 0.64 describes the pre-fix one. **Three
   framework-faithful seeds are queued tonight.**
2. **ArgRewrite: the oversampling *demonstration* is DOWNGRADED to inference with
   counter-evidence.** The paper's own §5.4.1 names training-fold synonym replacement at
   ~3.4× — a mechanism that cannot leak across folds — where our arm was pre-CV exact
   duplication at 1.49×; reproducing their cell by a mechanism the source disclaims is a
   coincidence read as confirmation, the modeling face of the criterion-that-cannot-fail. And
   the inference fails on the sibling table: two of the three defective Majority cells deviate
   in the *wrong* direction for a systematic oversample. What stands: the released corpus
   cannot produce the printed fine-Majority row under any known construction, composition is
   exact, and the four non-augmented classes are within a dime. For the embedding rows the
   honest label is "we did not reproduce it": two locally reachable routes were never run —
   **max-over-their-published-grid** (queued) and the standard four-block pair encoding
   `[u; v; |u−v|; u⊙v]` (build owed).
3. **PAN: L106 independently confirmed** (its own blind check: 20.5% of validation paragraphs,
   0.982/0.981 on doubly-seen pairs), L104's "nothing here has the inflation signature"
   formally falsified, and **two defects of ours caught**: the two landed members trained
   under different LR schedules (a conditional scheduler bug — constant-LR ernie archived, the
   consistent rerun queued), and a dead ternary in the augmentation path. The settling test is
   queued: a no-augmentation member; if it lands at the leak-free level, the winning recipe's
   augmentation is pure memorization. The roberta epoch-4 coincidence
   first noted here is retracted (L108): ernie's ten epochs come nowhere near its own gate,
   so no checkpoint rule explains both members and the match is noise.
4. **BST: three design corrections before the model was built.** The MDP has **nine actions
   including Stay at cost −1** (the eight-move set is the stimulus-generation description, a
   different object); the 36 conditions factor as 4 goal configurations × 3 path groups × 3
   obstacle/route conditions; and the goal prior is a **fourth internal source contradiction**
   (main text: the three marked goals; appendix: all non-obstacle squares), which silently
   sets K in the γ reparameterization (1.5 versus ~1.007) — both readings will run as arms.
   Confirmed correct: the γ footnote, the Boltzmann convention, H = M2 at γ = 1, the BSCV
   parameters, the Exp-3 pipeline. And the Fig-3 extraction now has its decisive known-answer
   gate: it must produce the paper's own 99 unique stimuli, which the current chained decode
   (34) does not yet.

**Means.** The referee's nine missing concepts are banked in LESSONS (multi-seed verdicts;
framework-faithful means the framework, not the printed hyperparameters; contamination as a
pre-training gate with a near-duplicate pass still owed; the reproduce/replicate/robustness
vocabulary per row; specification curves over point verdicts; confirmatory arms implement the
named mechanism; predictions persisted always; artifact versions re-checked before closing;
author contact SUPERSEDED by the curator's ruling (2026-08-14: off the table, never suggested again); irreproducibility stated as
a bounded effect). Every demanded test is queued or built into today's plan; the Phase-1
table rows carry their reopened statuses; and the assessment package for the curator now
includes this audit beside the closures it moved.

## L108 · The second referee's residue register: twenty-five findings, four of them live fire, and the corrective arms themselves needed correcting

**Hypothesis.** *(His order: a second Opus referee, mandated to find every remaining edge case,
auditing the first referee and the corrective arms as code.)* The corrections were themselves
clean, or they weren't.

**Method.** Second adversarial subagent: corpora re-hashed at three granularities with
normalization, runners executed against live models to test their own patches, the queue's
stage wiring audited for collisions, the first referee's load-bearing claims re-verified at
source, the digitized BST reference validated computationally.

**Found — the live fire, all fixed in this pass.**
1. The fp32 deberta arm was training *at that moment* without warmup — the exact configuration
   that collapsed roberta. Killed mid-epoch, stage corrected to the shared recipe.
2. The superseded ernie stage and its corrective replacement shared one produces path; the old
   one would have run first and blocked the fix forever. Deleted, and a permanent guard now
   asserts no two stages ever share a produces.
3. **The landed roberta member never received the paper's dropout** — roberta's dropout lives
   at a different attribute, the setter silently missed it, and the result file recorded 0.25
   while the model ran 0.1: a false provenance record, not a missing one. Dropout is now set
   structurally over every module, asserted, and recorded as measured; the member is archived
   and reruns.
4. The vote sat before the corrective arms and would have frozen a mixed-recipe number behind
   its guard. Relocated behind three same-recipe members.

**Found — the design corrections.** The queued settling arm was not identified: removing the
whole PAN23 augmentation confounds the leak with a fifty-percent data cut, while dropping only
the 210 contaminated documents keeps 97.3 percent of the data — the arm is replaced with the
identified form. The ArgRewrite macro-F1 ran without a fixed label set, so folds missing a
near-empty class inflated their scores — a one-line fix that may move every fine cell,
including a majority gate claimed as met. The grid arm would have returned one uninterpretable
maximum; it now persists all thirty-six candidates with the published config's rank. The
ScholaWrite program gained the missing roberta framework arm and the batch-8 reading of the
checkpoint arithmetic (a ten-epoch schedule read at half decay — a different pipeline, not a
different stopping point), with per-epoch history now recorded for the specification curve.

**Found — the record corrections.** Two first-referee claims retracted: the roberta epoch-four
coincidence is noise (ernie's ten epochs come nowhere near its own gate, so no checkpoint rule
explains both), and L107's "their accuracy sits where our arm sits" compared their accuracy to
our F1 with our accuracy never recorded — struck, with the real check (does our F1-minus-
accuracy gap reproduce their inversion) assigned to the framework arms. The ScholaWrite tag
typo is **inert and was never a train/eval mismatch**: the paper-era code used the same wrong
tag on both sides, 89 percent of inputs truncate it away entirely, and the current repo's
"fix" created the mismatch it appears to document — so "we reproduce their bug" is vacuous
and the irreproducibility reading strengthens. The teacher-forcing input variant is gold-label
by construction and dead code besides; it enters the specification curve only as a labelled
upper bound. And a BST claim of this entry was itself REVERSED by the consensus fleet (L109): the
Experiment-2 reference file is fully valid — its triples are three contiguous 95-row goal
blocks (stimulus i = rows i, i+95, i+190), all 95 sum to one within the digitization band, all
four model columns likewise, and 285 equals the paper's own 95 stimuli times three, complete.
The "all fail" result here was a grouping-stride artifact.

**Found — the clean sweeps, as results.** The framework-faithful reimplementation is verified
equivalent to their Trainer (parameter grouping identical against the reference implementation,
step counts exact to their released checkpoint number, optimizer defaults matched; batch 16 is
the correct reading of their two-GPU arithmetic). Near-duplicate contamination residue is nil —
normalization moves no overlap figure by more than a tenth of a point, so the owed MinHash pass
is answered cheaply and negatively. The label space is fifteen everywhere; the weighted-F1
readings agree across methods; alphabetical label ordering matches their encoder. And two new
contamination facts for any future PAN use: the 2023 validation split adds 4.8 points of
overlap on top of train's, and **the easy and medium splits leak within-year** (13.5 percent of
medium validation pairs from medium's own training set; 18.9 percent of easy paragraphs) — the
organizers' dedup held only on hard.

**Means.** The register's pattern is the same one twice over: every defect that mattered was a
correction applied at lower rigor than the finding it corrected. The fixes are in; the BST
build stays blocked behind its decode gate (the second referee confirms: six of thirty-six
panels fully chained, two of three route conditions recovered, seventy-six judgment points
against the paper's ninety-nine) exactly so a nine-action model is never fitted to a
one-sixth-decoded stimulus set. Environment versions now ride in every model-arm output. The
GPU program the two referees have queued exceeds one night on one card; the ordering puts the
PAN member corrections first, the ScholaWrite framework arms second, and the batch-8 and grid
arms behind them.

## L109 · The consensus fleet: twenty-one claims settled unanimously, three record corrections, and a reachable test-set gate found in our own corpus store

**Hypothesis.** *(His order: a fleet of Opus agents returning one cohesive picture instead of
serial upheavals.)* The Phase-1 record, stated as twenty-five numbered claims, survives
independent multi-agent adjudication — or the dissents localize what doesn't.

**Method.** Nine Opus specialists on a fixed ballot, every claim deep-verified at source by at
least two where coverage allowed, a meta-auditor verifying that previously claimed fixes exist
in the code, new findings capped at three per agent and severity-gated. Nine of nine returned;
1.1M agent tokens; the tally is the deliverable.

**The tally.** **Twenty-one of twenty-five claims CONFIRMED with no dissent**, most with
computed or read evidence stronger than the record's own: the ScholaWrite stale-number chain
(now with an adversarial-distribution analysis showing only implausible concentrations reach
0.64), the tag-typo inertness (both scripts, both paper-era commits, ~89 percent truncation),
the framework-arm equivalence, the teacher-forcing dead code, the ArgRewrite composition and
Majority contradictions (STRENGTHENED: the printed binary and fine Majority rows are mutually
incompatible with each other — disjoint implied corpus sizes — independent of Table 4, which
removes the last motivation for the oversampling inference), every PAN contamination and
metric claim, the BST action set, factorization, goal-prior contradiction, and decode gate,
and both methods standards.

**The three refutations, all of our record, all corrected this pass.**
1. **The ".895 Features row reproduced" claim was wrong** (two agents, independently): the
   .895 runs carry our nineteen-dimension change block, which the paper's feature list does
   not include. The faithful Features arm is 0.883 against their 0.90 — a 1.7-point gap, not
   a reproduction. Entry, TODO row, and the phase scorecard corrected.
2. **The Experiment-2 reference file is VALID after all** (two agents, decisively): its rows
   are three contiguous 95-row goal blocks — stimulus i lives at rows i, i+95, i+190 — and
   under that grouping all 95 human triples and all four model columns sum to one within the
   digitization band. The second referee's "all fail" was a grouping-stride artifact, its
   printed range was wrong besides, and 285 equals the paper's own 95 stimuli times three,
   complete. My README narrowing is reversed; as a bonus, the Experiment-1 collision caveat
   is discharged (all twelve collisions are cross-stimulus), so all 300 Exp-1 rows are usable.
3. **The lessons file carried two wrong statements** — the unqualified "unreachable from its
   own per-class table" survived in the shelf after being corrected in the entries, and the
   "~16 points for truncation side" credited one lever with a three-lever composite. Both
   folded.

**The capped findings channel, triaged.** The largest: **the PAN 2025 test split, with truth
labels, is in our corpus store and verified genuine** (the printed test baselines reproduce
from it to 0.0004) — so a published *test-set* exact-value gate is locally reachable after
all, and the fully-specified 2025 winner (single deberta-base, every hyperparameter stated) is
the cleanest recreation target the phase has ever had; the build is filed. Wiring: the
grid-max stage pointed at the wrong output directory (fixed before it burned 150 minutes per
pass) and the settling filter upgraded to paragraph keys (245 documents dropped, residual
overlap at the within-year floor). Numbers: the labels= fix is verified INERT on v4 (no class
ever misses a fold at these sizes — a clean null), the truncation figure corrects 87→89
percent, the pair denominator 4,132→4,131, the reweight 0.5939→0.5947, "four classes exact"
→ three, and the strict-tier PAN leak-free numbers are 0.8235/0.8355 (neither-paragraph-seen,
n = 3,127). Closure-language residue in two entries struck. Table 4 carries two internal
arithmetic errors of its own, recorded. Easy's within-year leak is paragraph-level only
(pair-level 0.24 percent), and the held-back easy/medium test priors are shifted from the
released splits, both recorded for any future use.

**Means.** This is the cohesive picture the fleet was sent for: the record's *findings about
the papers* are now settled to a depth no single referee reached, the residue is three
localized corrections all applied, and the go-forward set is short — the corrected GPU arms
already queued, the BST decode-to-99 gate, and the newly-found 2025 test-gate build. Nothing
in the tally reopens a settled claim, and the claim list itself becomes the Phase-1
assessment's spine.

## L110 · The framework arms land above the print: the 0.64 sits inside this pipeline's own training trajectory, not outside it

**Hypothesis.** *(The referee's demanded closure arms, L107; the ScholaWrite row closes on the
seed interval.)* The framework-faithful recipe — their split, their recipe reading, and the HF
Trainer defaults our hand-rolled loop dropped (parameter-grouped weight decay excluding
bias/LayerNorm, linear decay to zero, clipping at 1.0) — either reproduces the printed 0.64
within the seed interval or fixes the direction of the correction.

**Method.** The faithful arm with `--hf-defaults`, ten epochs at batch 16, seeds 42 and 43
(44 in the queue), per-epoch test weighted-F1 recorded for the specification curve, predictions
and accuracy persisted (the L108 requirements).

| arm | weighted F1 | accuracy | vs the print (F1 .64 / acc .56) |
|---|---|---|---|
| **framework, seed 42** | **0.6595** | 0.6288 | **+0.020** / +0.069 |
| **framework, seed 43** | **0.6592** | 0.6274 | **+0.019** / +0.067 |
| hand-rolled faithful (L86) | 0.580 | never recorded | −0.060 |
| epoch-5-at-batch-8 reading, pre-framework | 0.6094 | — | −0.031 |
| non-faithful recipe (L68) | 0.741 | — | +0.101 |

*Caption: the specification curve around the printed cell. The two framework seeds differ by
0.0003 final; their per-epoch paths differ normally and converge at the end.*

**Found.** Three things. **Restoring the Trainer defaults is worth +0.079** — the framework was
the hand-rolled gap, and the faithful arm now lands two points ABOVE the print, not six below.
**Both seeds cross 0.64 mid-trajectory** (seed 42 reads 0.637 at epoch four, seed 43 reads
0.640 at epoch six), and the camera-ready per-class table's implied 0.5947 also sits on these
trajectories (epoch five reads 0.591) — so an unstated earlier stopping rule prints their
headline from exactly this pipeline. And **the F1-above-accuracy inversion reproduces in
direction but not size** (ours 0.659 against 0.628, a 0.031 gap; theirs 0.64 against 0.56,
a 0.080 gap) — the real check L108 assigned, half-passed.

**Means.** The correction stands but its shape changes. The paper's numbers remain internally
inconsistent — the camera-ready table and the headline cannot describe the same run — and no
configuration we have run *produces* 0.64 at its stated final-epoch reading. But "stale and
unreachable" softens to **bracketed**: the print sits inside the specification range
(hand-rolled 0.580, batch-8 0.609, framework 0.659, non-faithful 0.741), and the
checkpoint-rule reading reproduces it from inside the framework trajectory. That reading
carries an explicit caution: it is the same shape as the PAN epoch-four coincidence L108
retracted, and its discriminating test is already running — the paper prints 0.64 for BOTH
architectures, so the roberta framework arm either also crosses 0.64 mid-trajectory (the
reading survives) or never reaches it (the reading dies the same death). Closure waits on seed
44, the roberta arm, and the batch-8 framework reading.

## L111 · The corrected members split three ways: ernie above gate, roberta killed by the all-module reading of the printed dropout, deberta stopped by memory

**Hypothesis.** *(L108's corrective arms: one recipe for all three members before the vote.)*
Under the shared recipe — linear decay, warmup 0.06, and the stated dropout 0.25 now applied
structurally and recorded as measured — all three members land above their validation gates.

**Method.** Same-recipe reruns of the ernie and roberta members; dropout set over every Dropout
module (the L108 false-provenance fix) and the achieved values written to the result file.

| member | dropout actually applied | final (best) | gate | delta |
|---|---|---|---|---|
| **ernie, rescheduled** | all modules 0.25 | **0.8798 (0.8800)** | 0.8490 | **+0.031** |
| roberta, structural | all modules 0.25 | 0.5890, flatlined at 0.352 through epoch nine | 0.8423 | −0.253 |
| roberta, archived (L108) | pretrained defaults, 0.1 | 0.8558 (0.8620) | 0.8423 | +0.014 |
| deberta, fp32 refit (all-scope) | all modules 0.25 | 0.3522, flat all ten epochs | 0.8567 | −0.504 |

*Caption: the member set after the referee's corrections. The archived roberta row is the run
whose recorded 0.25 was false provenance; it is kept as the default-dropout data point.*

**Found.** Ernie reproduces above its gate under the corrected schedule, higher than its
archived constant-LR run (0.8650), so the schedule fix cost nothing and the third member is
landed. Roberta cannot train at all under the all-module reading of the winner's 0.25 — nine
epochs at the constant-prediction floor with one late escape — while ernie trains fine under
the identical setting, so the fragility is model-conditional, roberta's second knife-edge
after the no-warmup collapse (L104). Deberta's refit all-scope arm landed flat at the
constant floor for all ten epochs (fold 2026-08-16 evening) — matching its head-scope twin
exactly, so BOTH scope readings collapse in fp32 at these hyperparameters locally: three
distinct deberta failures now (fp16 overflow, and both fp32 scopes flat), against the
paper's printed 0.8567 for this member.

**Means.** The printed "dropout 0.25" is scope-ambiguous, and the scopes are not
interchangeable. **Corrected by L118: the collapse is stochastic, not deterministic** — the
leak-free arm ran the identical all-module setting and trained normally — so the scope
inference downgrades from "their run cannot have been all-module" to "all-module is
knife-edge unstable at these hyperparameters," which is itself the reason it cannot anchor
a comparison. All three members now rerun under the head-only scope (the usual meaning of a
notebook's classifier dropout, encoder dropouts at pretrained defaults), the vote sits
behind those three so it compares one recipe to one recipe, and deberta refits at
micro-batch 12 with accumulation 5, preserving the effective batch and step count. The
scope fork enters the record as a specification-curve axis, not a tuning choice.

## L112 · Grid-max does not close the embedding rows: search optimism dies as the explanation, one local route left

**Hypothesis.** *(Referee route 1, L107.)* If the published embedding cells are maxima over the
paper's own printed hyperparameter grid, our maximum over the same 36-point grid is the
like-for-like comparison and should close the roughly three-point gap.

**Method.** The v4 extraction, binary task, all 36 grid points fitted per arm under the
standard fold protocol, every candidate persisted with the published configuration's rank.

| arm | grid max (F1 / acc) | their print | gap after grid | fixed config's rank |
|---|---|---|---|---|
| majority | .3688 / .5847 | .37 / .58 | exact | — |
| features | .8836 / .8850 | .90 / .90 | −.016 | 4 of 36 |
| use | .8774 / .8782 | .92 / .92 | **−.043** | 15 of 36 |
| features + use | .8783 / .8792 | .93 / .93 | **−.052** | 26 of 36 |

*Caption: the maximum any of their 36 printed hyperparameter settings can produce from the
released corpus under our construction, against the printed cells.*

**Found.** The grid maximum moves the Features cell by less than a point over the fixed
config and leaves both embedding rows more than four points short. The published cells sit
above every one of the 36 candidates on both embedding arms.

**Means.** Search optimism over their own printed grid is refuted as the explanation of the
embedding rows. "Not reproduced by us" stands, now with the gap bounded UNDER their grid, and
one locally reachable route remains: the standard four-block pair encoding [u; v; |u−v|; u⊙v],
queued at the published configuration. If it also lands short, the irreproducibility wording
rests where the standing evidence already put it — the sentence aligner named only in a
deleted line of their own source, the vector combination unstated — on exhausted public
routes.

## L113 · The unsigned mobility square completes: movement magnitude tracks post-training lineage exactly, and the three movement instruments measure three different things

**Hypothesis.** *(The unsigned form's missing half; L103 completed the signed square, these
are the two llama cells for the magnitude square.)* The magnitude instrument — does the
polish bank MOVE more than the depth bank across position, sign ignored — either follows the
signed form's three-of-four rise or draws its own family structure.

**Method.** The frozen unsigned instrument (per-feature absolute-trend shuffle-z, polish
against depth banks, Mann-Whitney), 80-word windows, on the two llama fiction cells; the qwen
cells stand from L97.

| cell (base × post-training) | n | polish z | depth z | p | verdict |
|---|---|---|---|---|---|
| qwen × instruct (L97) | 15 | 1.17 | 0.33 | 5.3 × 10⁻⁴ | MOVES-MORE |
| qwen × reasoning-distill (L97) | 13 | 0.32 | 0.10 | 0.16 | NO-DIFFERENCE |
| **llama × instruct** | 23 | 0.47 | −0.04 | **0.0081** | **MOVES-MORE** |
| **llama × reasoning-distill** | 30 | 0.003 | −0.14 | 0.38 | **NO-DIFFERENCE** |

*Caption: the completed magnitude square. Both instruct cells mobile on the polish side, both
reasoning-distill cells positionally quiet, across two bases.*

**Found.** A clean two-by-two alignment: instruction-tuned output carries mobile surface
polish and R1-distilled output does not, on either base architecture. The unsigned form is
the first movement instrument whose family structure IS the post-training lineage.

**Means. Superseded on the window axis by its own robustness test (L116): the lineage
alignment is wide-window-only** — at 40 words the square scrambles into a nominal base
split, so neither alignment is a law, and the two-window-robust residue is qwen-instruct's
mobility alone, converging with the reader-side instrument's isolation of the same model
(L105). The original reading, kept for the record: the three movement instruments
dissociate three ways (signed trend a machine default with one exception, L103; magnitude
apparently tracking post-training, this entry; reader-side one model, L105), with the
cautions that the llama cells were one-window and the weakest cell fails the record-wide
correction. The caution was the operative half.

## L114 · The Fig-3 decode passes its known-answer gate: 99 of 99 stimuli, label-perfect, every path a legal walk

**Hypothesis.** *(The decode gate the referees fixed, L107/L108: the extraction must produce
the paper's own 99 unique stimuli before any model is fitted to it.)* The remaining 108-vs-99
residue was conjectured to be cross-panel single-cell jitter breaking nine dedup merges.

**Method.** Ruler validation at the glyph level, then a rebuilt extraction. Four mechanisms
found, each measured at source before being coded against:
1. **The figure's long runs are not on the grid.** Stimulus rows are drawn at a ~5.0-5.2 pt
   glyph advance against the 4.60 pt wall/goal-calibrated cell pitch, so per-glyph lattice
   snapping accumulates drift and rounds the tail of a long run one column right (a '7' at
   fractional column 6.53 whose truth is 6). Columns are now line-relative: cumulative
   rounding of consecutive gaps, drift-free by construction, anchored at each line's first
   character.
2. **Goal letters share text lines with judgment numbers.** Sorting such a line by x
   interleaves the letter between the number's digits and splits it into phantom labels
   (a '15' became labels 1 and 5). Lines now cluster by y before grouping.
3. **Adjacent two-digit numbers pack without a delimiter** ('1011' is 10 then 11), and the
   intra- and inter-number gap distributions overlap, so no distance threshold separates
   them. Digit runs of even length chunk in pairs; chunks advance exactly one cell.
4. **A two-digit number anchoring its own line pulls the anchor half a cell right** (the
   group spans ~1.5 cells); anchors now use the first character. Residually ambiguous
   anchors (fractional column 0.35-0.65) are resolved by chain validity: every shift
   combination is tried and the winner is the one whose atoms form the best single chain.
Identity across panels is then decided at the glyph, not the snapped cell: prefixes are the
same stimulus iff equal, or differing only at judgment cells whose raw panel-local
coordinates agree sub-point (repeat-draws land within 0.6 pt; different placements sit a
full 4.6 pt pitch apart).

| state | chained panels | label anomalies | unique stimuli | illegal steps |
|---|---|---|---|---|
| greedy chaining (pre-L108) | 6/36 | — | — | — |
| exhaustive DFS, per-glyph snap | 36/36 | 0 | 108 vs 99 | 31 paths |
| **line-aware decode + glyph identity** | **36/36** | **0** | **99 vs 99** | **0** |

*Caption: the decode gate's progression. 170 judgment instances across 36 panels resolve to
exactly the paper's 99 unique stimuli; 96 canonical paths are strictly 8-adjacent as
decoded and three repair uniquely under the one-column judgment-cell slack.*

**Found.** The gate passes exactly: 99 unique (world, prefix) stimuli, every judgment label
at precisely its own step index in all 36 panels, and every canonical path a legal
8-connected walk. The conjectured jitter was real but the mechanism was richer: a figure
whose text layer is systematically off its own grid, plus three typography traps.

**Means.** The BST stimulus extraction is done and validated against the paper's own count —
the first time the full 99-stimulus set has existed outside the authors' lost originals, to
our knowledge. The nine-action model rebuild is unblocked: `fig3_stimuli_canon.json` carries
worlds (goals, walls, start), canonical legal paths, judgment labels, and member panels, and
the content-based alignment check against the reference model predictions (the M2 column)
remains the rebuild's own first gate, so an extraction error that survived this pass would
still be caught downstream. The ruler lesson is the entry's method: every mechanism was
measured in the raw glyph coordinates before being coded against, and the final identity
rule needed no tolerance at all for 96 of 99 because the corrected decode made same-stimulus
prefixes byte-identical.

## L115 · The four-block arm lands short too: the embedding rows close as not reproducible, every public route now measured

**Hypothesis.** *(Referee route 2, the last locally runnable candidate for ArgRewrite's
embedding cells.)* The standard four-block sentence-pair encoding [u; v; |u−v|; u⊙v] at the
published configuration closes the roughly three-point gap the bare concatenation leaves.

**Method.** The v4 extraction, binary task, four-block USE encoding, standard fold protocol.

| arm | four-block (F1 / acc) | bare concat | grid max | their print | remaining gap |
|---|---|---|---|---|---|
| use | **.8866 / .8884** | .8809 | .8774 | .92 / .92 | **−.033** |
| features + use | **.8860 / .8878** | .8783* | .8783 | .93 / .93 | **−.044** |
| features (unchanged arm) | .8828 / .8844 | — | .8836 | .90 / .90 | −.017 |
| majority (sanity) | .3688 / .5847 | — | — | .37 / .58 | exact |

*Caption: the last local route. Four-block beats both the bare concatenation and the grid
maximum by about a point and still lands three to four points short of the printed cells.*

**Found.** The encoding upgrade is real but small: plus one point, minus the gap. No
locally runnable construction reaches the printed embedding rows.

**Means.** The embedding rows close as **not reproduced by us from the released materials**,
with the gap bounded at three to four points and every public route now measured rather than
presumed: composition exact, features theirs, hyperparameters theirs, encoder refuted across
checkpoints, sentence alignment refuted at source, folds refuted, grid-max refuted, and now
the standard pair encoding refuted. The surviving candidates (search optimism beyond their
printed grid, an unstated vector combination) are not publicly resolvable, and the wording
stands on that exhausted-routes evidence per the standing ruling. The ArgRewrite recreation
is fully settled: everything reachable reproduced or bounded, nothing left to run.

## L116 · The magnitude square does not survive its window test: the lineage alignment is wide-window-only, and one model is the only constant

**Hypothesis.** *(L113's own named robustness test.)* The clean post-training alignment of
the magnitude instrument (instruct cells mobile, distill cells quiet) holds at the 40-word
window, or it is window-bound like most of the movement family.

**Method.** The frozen unsigned instrument over the four fiction families at the 40-word
window, cached features, ruler gates as always.

| cell (base × post-training) | w80 verdict | w40 polish z / depth z | w40 p | w40 verdict |
|---|---|---|---|---|
| qwen × instruct | MOVES-MORE | 0.83 / 0.11 | **0.0008** | **MOVES-MORE** |
| qwen × reasoning-distill | no difference | 0.22 / 0.01 | 0.037 | MOVES-MORE (uncorr.) |
| llama × instruct | MOVES-MORE | 0.08 / 0.29 | 0.27 | NO-DIFFERENCE |
| llama × reasoning-distill | no difference | 0.19 / 0.09 | 0.081 | NO-DIFFERENCE |

*Caption: the magnitude square at both windows. At 40 words the qwen-base cells move and the
llama-base cells sit quiet, the mirror of the wide window's post-training split.*

**Found.** The alignment scrambles: at the narrow window the square reads as a BASE split
(both qwen cells nominally mobile, both llama cells quiet), where the wide window read as a
post-training split. Two windows produce two different clean alignments, so neither is a
lineage law. The one cell robust at both windows is qwen-instruct.

**Means.** L113's lineage claim retracts to window-bound, exactly the outcome its own
caution named — the correction is folded there. What survives is sharper than what died:
**qwen-instruct's positional mobility is the movement family's one two-window-robust
magnitude fact, and it is the same single model the reader-side instrument isolated
(L105)** — the two instruments that dissociated across families reconverge on this one
model. G146's question updates a second time: not what distillation removes, but what makes
this one model's output positionally mobile in ways every other cell shows only
conditionally. The ds cell's nominal 0.037 does not survive the standing correction and is
recorded as uncorrected.

## L117 · ScholaWrite closes: the seed interval contains the print, one seed lands on it to the third decimal, and the checkpoint reading survives its discriminating test

**Hypothesis.** *(L110's named closure conditions: seed 44 completes the interval, and the
roberta framework arm is the discriminating test for the checkpoint-rule reading — the paper
prints 0.64 for BOTH architectures, so the reading survives only if roberta's trajectory
also crosses it.)*

**Method.** The framework-faithful recipe, seeds 42/43/44 for bert and seed 42 for roberta,
per-epoch test weighted-F1 recorded, accuracy and predictions persisted.

| arm | final weighted F1 | accuracy | crosses 0.64 mid-trajectory? |
|---|---|---|---|
| bert seed 42 | 0.6595 | 0.6288 | yes (epoch 4 reads 0.637) |
| bert seed 43 | 0.6592 | 0.6274 | yes (epoch 6 reads 0.640) |
| **bert seed 44** | **0.6391** | 0.6089 | yes (jumps 0.608 → 0.655 across epoch 7) |
| **roberta seed 42** | **0.6512** | 0.6177 | **yes (epoch 7 reads 0.6414)** |

*Caption: the closure arms. The bert three-seed interval is [0.639, 0.660]; the printed 0.64
sits inside it, and seed 44's final lands within 0.0009 of the print.*

**Found.** Three things, each moving the verdict. **The seed interval contains the print**:
the tight two-seed spread of L110 broke open at seed 44, which finals at 0.6391 — the
printed 0.64 to the third decimal, a pass under the exact-value standard's own tolerance
and under the interval rule both. **The discriminating test came back positive**: all four
framework trajectories cross 0.64 mid-training, roberta's at epoch seven within 0.0014 of
the print, so the identical printed 0.64/0.64 pair is consistent with one pipeline read at
unstated stopping points, and the refutation that killed the same-shaped PAN coincidence
did not occur. And **the accuracy residue stays**: every arm's final accuracy (0.609 to
0.629) sits well above their printed 0.56, which remains unexplained at the final-epoch
reading and consistent with an earlier-checkpoint reading that per-epoch accuracy was not
recorded to check.

**Means. The ScholaWrite row closes.** The F1 headline is REPRODUCED: within the three-seed
framework interval, on the print at one seed, and on every trajectory as a crossing. What
the correction keeps is the paper's internal story, now sharper for being explicable: its
own camera-ready per-class table (implying 0.59) and printed accuracy (0.56) cannot
describe the same run as its 0.64 headline — but all three numbers are consistent with
different checkpoints and seeds of the one described pipeline, which our specification
curve produces end to end (0.58 to 0.74 across recipe readings, 0.59 at mid-trajectory,
0.64 at crossings and at seed 44's final, 0.66 at the interval's top). The stale-number
narrative softens accordingly: nothing needs to have been stale; the paper's numbers are a
sampler of one pipeline's readings, published without the stopping rule that indexes them.
The batch-8 protocol arm landed as promised (0.7496 final, accuracy 0.7454) and gates
nothing: it extends the specification curve's top (hand-rolled 0.580, framework batch-16
0.639 to 0.660, non-faithful 0.741, framework batch-8 0.750), its trajectory crosses 0.64
at epoch two like every other framework arm, and the print stays inside the family's span.

## L118 · The identified settling arm confirms the contamination account from a third direction, and the roberta collapse turns out stochastic

**Hypothesis.** *(The second referee's identified settling arm.)* Retraining the roberta
member with only the 245 leaked documents removed (94 percent of the augmentation kept)
lands at the leak-free capability level if the recipe's above-gate margin is memorization,
or at the blended level if the augmentation carries real signal.

**Method.** Same recipe, paragraph-keyed leak filter, 36,897 training pairs (against
38,109 blended), per-epoch validation recorded.

| arm | validation macro-F1 | vs winner's gate (0.8423) |
|---|---|---|
| blended member (L106) | 0.8558 | +0.014 |
| blended member, leak-free pairs rescored | 0.8273 | — |
| strict-tier rescoring (L109) | 0.8235 | — |
| **retrained leak-free** | **0.8108** | **−0.032** |

*Caption: the same capability question asked three ways — rescore the blended model on
clean pairs, rescore strictly, retrain clean — answering 0.81 to 0.83 from every
direction.*

**Found.** Removing six percent of training documents erases the member's entire above-gate
margin and 4.5 points besides: the winning recipe's edge over its own validation gates is
the contamination, and honest capability sits in the 0.81 to 0.83 band whichever way it is
measured. One instrument surprise: this arm ran the all-module dropout 0.25 that flatlined
the blended rerun for nine epochs (L111) — and trained normally, climbing smoothly from
epoch one.

**Means.** The contamination story is now closed from three independent directions, and any
layering experiment on this benchmark builds on 0.81-0.83, never the printed gates. The
L111 fold-in: the all-module collapse is **stochastic fragility, not determinism** — one
run flatlines, a near-identical run trains — so the scope inference ("their cell exists,
therefore their run was not all-module") downgrades from proof to plausibility, and the
one-recipe head-scope member set stays the right vote design for exactly this reason: a
recipe that sometimes collapses cannot anchor a comparison either way.

## L119 · The BST Experiment-1 recreation lands at exact-value grade: four models, four printed correlations, all at printed precision, and the 99-versus-100 contradiction located

**Hypothesis.** *(G137's figure-level half, the phase's last open implementation.)* The four
models rebuilt under the referee-corrected design, run on the decoded 99-stimulus set,
reproduce the paper's Figure-5 best-fit correlations (M1 .83, M2 .98, M3 .94, H .97).

**Method.** Full rebuild against the formal appendix, read at source this pass: nine actions
with blocked moves UNAVAILABLE (their words), costs −1/−√2/−1 with Stay at −1, the SOFT
Bellman fixed point (the value function of the Boltzmann policy itself, iterated to a 10⁻⁹
residual — hard-max iteration, the v1 form, is a different pipeline), state-sequence
observation with actions marginalized, M2's exact goal-chain parameterization from footnote
1, M3 as 0-or-1 subgoal uniform over all squares with segment likelihoods, H as M2 at γ = 1,
goal support per the Exp-1 main text (the three marked goals; the appendix's all-squares
reading runs as the second arm, queued). Readout renormalized over the marked goals,
matching the paper's own subject-side normalization; judgment label ℓ reads the path prefix
to index ℓ−1 (the decode's label-perfect invariant). Alignment to the digitized reference is
a Hungarian assignment on the twelve-number four-model signature per stimulus — all four
models at once, so no single model's fit is circular.

| gate | printed | ours | delta |
|---|---|---|---|
| M1 best-fit r | .83 | 0.8281 | −0.002 |
| M2 best-fit r | .98 | 0.9780 | −0.002 |
| M3 best-fit r | .94 | 0.9440 | +0.004 |
| H best-fit r | .97 | 0.9661 | −0.004 |

*Caption: correlations with the 297 human judgment cells under the fixed content-based
alignment. Every value rounds to the printed two decimals.*

**Found.** Three results in one run. **The alignment is total**: 99 of 99 stimuli matched
with a median twelve-number assignment cost of 0.002 (sub-digitization), and the paper's
99-versus-100 stimulus-count contradiction is now LOCATED — reference index 92 is the one
Figure-5 stimulus with no counterpart in Figure 3's panels. **The pipeline is verified cell
by cell, not just by correlation**: our model predictions match the paper's own digitized
prediction columns to a maximum absolute difference of 0.0003 (M1), 0.0002 (M2), 0.001
(M3), 0.0002 (H) across all 297 cells — agreement at the digitization band itself. And
**all four human-correlation gates land at printed precision** on the first complete run.

**Means.** The Experiment-1 half of the BST recreation PASSES at exact-value grade — the
strictest pass in the phase after the analytic Armstrong–Mindermann cell, and the first on
real behavioral data. The load-bearing choices were all referee catches or source reads
that a plausible implementation would have missed: the soft value function (Eq. 4 is the
Boltzmann policy's own fixed point), blocked-action masking, marginalized state
transitions, the goal-chain parameterization, and the decode gate that supplied the
stimulus set (L114). Remaining for the anchor: the parameter-grid and BSCV gates (appendix
Fig. 2 and Table 1), the all-squares goal-prior arm, and Experiments 2 and 3, which need
their own stimulus extractions (the same decode machinery applies). Filed as queue stages;
the maze-world engine is done.

## L120 · The goal-prior contradiction resolves empirically: the paper computed with the three marked goals, and only the cell-level gate could tell

**Hypothesis.** *(The referee's fourth source contradiction, both readings as arms: the
Exp-1 main text says the three marked goals; the appendix's general prior says every
non-obstacle square.)* The two supports produce distinguishable predictions, and the
paper's own digitized numbers identify which one their computation used.

**Method.** The v2 engine's second arm: all-squares support (K ≈ 140 per world), same
best-fit parameters, same alignment, against the marked arm (L119).

| model | marked arm vs their digitized predictions (max abs) | all-squares arm |
|---|---|---|
| M1 | 0.0003 | 0.0003 |
| M2 | 0.0002 | **0.1289** |
| M3 | 0.001 | 0.001 |
| H | 0.0002 | 0.0002 |

*Caption: agreement with the paper's own prediction columns under the two goal-prior
readings. M1, M3 and H are readout-invariant to the support (per-goal likelihoods do not
depend on it, and the marked-goal renormalization cancels the prior's size); M2 is the one
model where K enters the dynamics, through the switch mixture.*

**Found.** The marked arm matches their M2 column to two ten-thousandths; the all-squares
arm deviates by up to thirteen points of probability. The paper's numbers were computed
under the three-marked-goals reading, as its Experiment-1 text states; the appendix's
all-squares prose does not describe the Experiment-1 computation. A methods note worth
keeping: the human-correlation gate barely notices the fork (0.9774 against 0.9780), so
only the cell-level comparison discriminates — correlation gates are too coarse to catch a
wrong prior support.

**Means.** The fourth source contradiction closes with a winner rather than a caveat, and
the K in M2's switch factor is settled at 3 for any Exp-1 use. The cell-level-outranks-
correlation lesson is banked. Remaining on this anchor: the grid and BSCV gates, then
Experiments 2 and 3 behind their own stimulus extractions.

## L121 · The head-scope member set, first returns: roberta lands above gate with the scope verified in the record, and deberta collapses its second way

**Hypothesis.** *(L111's one-recipe design: all three members under head-only dropout 0.25,
the vote behind them.)* Each member lands above its validation gate under the shared
recipe.

**Method.** Head-scope structural dropout (encoder modules at pretrained defaults, head at
0.25 — the measured record reads [0.1, 0.25], the scope verified, the L108 false-provenance
class closed), warmup 0.06, one recipe.

| member | config | final (best) | gate | delta |
|---|---|---|---|---|
| **roberta, head-scope** | fp16, batch 30 × 2 | **0.8633 (0.8633)** | 0.8423 | **+0.021** |
| deberta, head-scope | fp32, micro-batch 12 × 5 | 0.3522, flat all ten epochs | 0.8567 | −0.504 |
| ernie, head-scope | queued behind the running arms | — | 0.8490 | — |

*Caption: the one-recipe set's first two returns. Roberta's head-scope member sits above
its archived default-dropout run (0.8558) and above gate.*

**Found.** Roberta reproduces above gate under the head-only reading, its third
above-gate configuration (default dropout 0.8558, leak-free-retrained 0.811 against a
different question, head-scope 0.8633). Deberta never escaped the constant-prediction
floor: ten epochs flat at 0.3522 in fp32 — its second distinct failure mode after the fp16
overflow, so the paper's strongest member (their 0.8567) is the one we cannot yet train at
all under the shared recipe reading.

**Means.** The L118 fragility lesson applies verbatim: a collapse is an instability draw,
not a verdict, so the stabilizer ladder runs in the recipe-preserving order — seed change
first (queued), then a warmup raise, then the learning rate, each recorded as a named
assumption if it becomes the divergence fix. The vote waits on deberta by construction.
Nothing in this changes the PAN science (L106/L118 closed the contamination account); what
hangs on deberta is the recreation completeness of the member set and the vote's gate
comparison.

## L122 · Experiment 1 completes: the grid maxima and the bootstrap table land at printed precision, and the sweep independently selects the paper's own best-fit parameters

**Hypothesis.** *(L119's named remaining gates.)* The parameter grid (10 β × 20 γ/κ, the
appendix's own lattice) and the bootstrap cross-validation (N = 10,000, k = 50) reproduce
the appendix Figure-2 maxima and the Table-1 values.

**Method.** The full grid on the marked arm (K = 3 settled by L120), row alignment FIXED
from the best-fit pass so the sweep cannot steer its own mapping; BSCV per the paper's
protocol: fifty rows sampled with replacement as training, argmax-correlation parameters
selected on them, scored on the untouched complement, ten thousand iterations.

| model | grid max r (printed floor) | grid argmax | their best-fit | BSCV ⟨r⟩ (printed) |
|---|---|---|---|---|
| M1 | 0.8281 (>.82) | β 0.5 | β 0.5 | 0.8212 (.82) |
| M2 | 0.9780 (>.97) | β 2.0, γ 0.25 | β 2.0, γ 0.25 | 0.9743 (.97) |
| M3 | 0.9440 (>.94) | β 2.5, κ 0.5 | β 2.5, κ 0.5 | 0.9345 (.93) |
| H | 0.9661 (>.96) | β 2.5 | β 2.5 | 0.9653 (.96) |

*Caption: every cell at printed precision, and the grid's argmax IS the paper's published
best-fit parameter set, model for model — our sweep re-derives their parameter choices
independently.*

**Found.** All eight remaining gates land. The parameter sweep's argmaxes reproduce the
paper's best-fit choices exactly on all four models, which is the strongest available form
of the parameter-level recreation: their fits fall out of our pipeline rather than being
assumed into it.

**Means.** **Experiment 1 of the BST anchor is COMPLETE at exact-value grade across every
published number it carries**: the Figure-5 correlations (L119), the cell-level prediction
columns (L119), the goal-prior resolution (L120), the appendix Figure-2 grid, and the
Table-1 bootstrap values — fourteen printed values, all at printed precision. What remains
for the anchor is Experiments 2 and 3, each behind its own stimulus extraction; the engine,
the alignment method, and the analysis pipelines are all validated inventory now.

## L123 · The external-verification fleet: the contradictions survive independent re-derivation, the "someone would have noticed" prior dissolves on contact, and one of our own strengthenings is downgraded

**Hypothesis.** *(His suspicion, made testable: "finding internal contradictions in nearly
every paper is too many coincidences — others must have found them, or explanations must
exist.")* Eight Sonnet verifiers, read-only, snippets-with-sources: external corroboration
per claim family, an adversarial audit of every irreproducibility claim, the base-rate
literature, and falsification attempts on our negative claims.

**Found, by question.**

1. **"Waves of reviewers would have caught this" — the waves do not exist.** ScholaWrite:
   zero OpenReview notes, one bot post on the dataset hub, twelve citing papers none of
   which use its labels, no benchmark page, no third-party fine-tune number anywhere — the
   only external 0.64 is the authors' own model cards. ArgRewrite: no classification code
   ever released, zero repo issues, no citing work restating the disputed rows, the
   original lab's own 2025 follow-up building a new corpus instead. BST: no independent
   replication, no data release found (course reimplementations use toy grids), no
   erratum. PAN: the metric mismatch appears in no issue, forum, or paper through the 2026
   overview, and participants reproduce the evaluator's output and call it by the prose's
   name. Nobody ran the numbers; there was no one to notice.
2. **The base rates say a clean sweep would have been the anomaly.** statcheck: 49.6
   percent of psychology articles carry at least one internal reporting inconsistency
   (12.9 percent a gross one); GRIM: 50.7 percent; an ML-paper audit: 44.9 percent with
   demonstrable errors. Under any of those per-check rates, five to ten checks per paper
   make at-least-one-hit the modal outcome; our one clean paper is the analytic one with
   no empirical tables to fail.
3. **Independent re-derivations, all passed**: the PAN evaluator (all three years read
   verbatim: one pooled two-class call, no per-document scoring, silent dropping) against
   all three overview papers' per-document prose — no reconciling reading; BST's M3 β
   contradiction (Fig 5 caption 2.5 vs Fig 6f caption 2.0) and the Exp-1 marked-goals
   sentence, both from the primary PDF; ArgRewrite's Table-4 contradiction re-derived from
   freshly fetched tables (three of four Majority rows contradict Table 4, matching L83);
   the ScholaWrite issue confirmed verbatim and authored by the senior author, the 0.64
   byte-identical in v1 and v5 re-confirmed. The 99-vs-100 framing is corrected: no "100"
   is printed anywhere — text and caption both say 99, and the 100th datum exists only in
   the plotted vector content, which only a decoder would ever see.
4. **Our own record took five corrections**: a paraphrase wearing unearned quote marks
   (replaced with the verbatim issue text); the L106 caption's over-credit of organizer
   dedup; the TOOLS negative claim's missing hedge; the TODO ArgRewrite row's unfolded
   superseded language (the audit's one OVERSTATED rating — a fold-discipline violation,
   not an evidence defect); and **one substantive downgrade: L109's strengthening that the
   printed Majority rows are "mutually incompatible independent of Table 4" could not be
   reconstructed by a second derivation** (the natural containment check passes), so that
   clause is UNVERIFIED pending its arithmetic being spelled out, and the fine-half
   account rests on the independently confirmed Table-4 contradiction alone.
5. **Named open leads, honestly carried**: Kashefi's dissertation (403-blocked) and the
   Zhang–Litman predecessor tables are where a dissolving explanation for ArgRewrite would
   most plausibly hide; archive.org and MIT DSpace were unreachable for the BST negative
   claims; the ScholaWrite paper's current arXiv table may carry a revised zero-shot row
   (version re-check owed at next touch).

**Means.** The suspicion was the right instinct pointed at the wrong layer: the
contradictions are real and now independently re-derived, but they were never findings
reviewers missed — they are arithmetic nobody runs, in papers nobody re-ran, at exactly
the base rate the meta-research literature predicts. What the audit actually caught was
ours: interim reports that overstated (three verdict swings a reader could reasonably
have taken as final), one appended-not-folded row, one unearned quotation, one
fleet-strengthening that outran its recorded derivation. All corrected in place. The
standing lessons are banked: check whether anyone ever ran the numbers before weighting
the no-one-noticed prior, and a strengthened claim whose derivation is not written into
the record is not yet a claim.

## L124 · Gear 3 validates: the cloud rerun lands within two thousandths of the local answer for seventy-three cents

**Hypothesis.** *(The curator's wiring test, his approval 2026-08-16.)* The gear-3 pipeline —
the guardrail wrapper, the corpus volume, the serialized remote stage — reproduces a known
local result within hardware-and-precision noise (the pre-stated band: ±0.01).

**Method.** The head-scope roberta member (local answer 0.8633, seed 42, same recipe) rerun
on a Modal A100 through `runners/gear3.py` under his recorded approval; scope asserted in
the measured record; versions recorded (the container runs newer transformers and CUDA than
local, which is precisely why recreation gates stay local).

| | final macro-F1 | best epoch | wall | cost |
|---|---|---|---|---|
| local (RTX 3060, 08-16) | 0.8633 | 0.8633 | ~27 min train | $0 |
| **gear 3 (A100)** | **0.8651** | 0.8681 | **16.8 min incl. setup** | **~$0.73** |

*Caption: delta +0.0018 at the final epoch, inside the band; the dropout scope reads
[0.1, 0.25] in both records; the ledger's first entry carries the run and his approval.*

**Found.** The wiring works end to end on first cloud contact — all five failures en route
were Windows-client defects, each now fixed in the wrapper permanently (MSYS path conversion
mangles /-prefixed remote paths; thousands of small files upload poorly, ship a zip; rich
console output crashes cp1252, force utf-8; background shells drift directories; serialized
functions require matching Python minors). Cross-hardware drift for this arm class is
measured at +0.002, the empirical justification for the recreation-gates-stay-local rule.

**Means.** Gear 3 is OPERATIONAL under the stone rules (per-use approval, the $10 window
with the final-approval-request refusal, the ledger) and costs what the assessment said it
would: this validation ran 1.6x faster than local end to end for under a dollar, and the
fan-out capability waits for a Phase-2 fleet on his call. Rotation of the in-chat token
stays owed on his side.

## L125 · The first Phase-2 A/B returns a null: the channels do not improve the substrate, and the fusion arm is less stable

**Hypothesis.** *(G150, preregistered before any result: the fusion arm wins only if its
mean test score beats the substrate's mean across three seeds, with error-overlap reported;
the show-stopper claim additionally required beating the printed 0.830.)* The 158-dim
motivation-shift channels, concatenated to the encoder representation, improve the 2025
style-change substrate.

**Method.** Six A100 runs on gear 3 under his package approval: substrate (A) and
substrate-plus-channels (B) at seeds 42/43/44, channels standardized on train statistics
only, best-val checkpointing within arm, test read once per run by the recreation runner's
own design. The channels-only reference arm ran locally first (boosted trees: 0.6283 test,
real standalone signal far below the substrate).

| seed | A (substrate) test | B (fusion) test | delta |
|---|---|---|---|
| 42 | 0.8280 | 0.8296 | +0.0016 |
| 43 | 0.8352 | 0.8372 | +0.0020 |
| 44 | 0.8398 | 0.8167 | **−0.0231** |
| **mean** | **0.8343** | **0.8278** | **−0.0065** |

*Caption: the preregistered read. Two small consistent gains erased by one large fusion
failure; the fusion arm's seed spread (0.021) runs nearly double the substrate's (0.012).*

**Found.** THE FUSION ARM LOSES under the preregistered rule: B's mean sits 0.65 points
below A's, the two positive seeds erased by seed 44's collapse to 0.8167. The informative
residue: (a) the substrate itself averaged 0.8343 with the printed 0.830 inside its seed
spread — the cloud-side echo of the G148 gate, with the official recreation read still
owed locally per the hardware rule; (b) the fusion arm doubles the seed variance, so
whatever the channels contribute, they buy instability at this integration point; (c) the
error-overlap half of the read could NOT be computed: the wrapper retrieved only the
produces file and the prediction siblings died with the containers — a gear-3 wiring
defect, fixed the same pass (siblings now come home with every produce).

**Means.** The honest first Phase-2 result is a null with a lesson attached, not a
show-stopper: naive late-fusion of the channels into the classifier head does not beat the
encoder at these seeds, exactly the outcome the L4 stacking conditions exist to catch, and
the channels-alone 0.63 says the information is real but largely subsumed. The next
designs, in cost order: more seeds to settle whether seed 44 is an unlucky draw or the
arm's true variance; earlier fusion or channel-gated attention rather than head
concatenation; and the document-grain 2024 task where the movement channels the sentence
grain excluded can participate. Package cost ~$8.20 total, window honest at every step,
and the whole cycle - preregister, fire, land, verdict - took one afternoon, which is the
gear-3 iteration speed working as intended even when the answer is no.

## L126 · The matched blind floor decomposed: 87% of its rise was label composition meeting the reader's default guesses

**Hypothesis.** *(The G130c follow-up owed by L73: which covariates raised the matched blind
arm from the analytic 0.25 to 0.402?)* Since the blind arm never sees text, the rise must
travel through label composition rather than through any covariate the reader could read.

**Method.** Reconstructed the L73 matched subset exactly (same seed, same code path, join
verified event by event against the recorded blind arm), then decomposed the floor three
ways on the existing 674 records: the truth and pick label marginals; a Monte Carlo
"alignment floor" (expected accuracy if the reader picks by its own empirical label
preference restricted to each candidate set, fresh uniform decoy draws, 200 repetitions per
event); and logistic regression of blind correctness on the six matching covariates, with
and without truth-label dummies. CPU only, no model calls, every statistic on disk
(`results/arg_recovery/floor_decomp.json`).

| quantity | value |
|---|---|
| blind accuracy (the L73 floor) | 0.402 |
| analytic floor at k = 4 | 0.250 |
| marginal-alignment floor (Monte Carlo) | 0.382 |
| share of the rise explained by alignment alone | **0.866** |
| largest truth share in the matched subset | word-usage/clarity, 0.405 |
| blind accuracy on that label | 0.652 |
| blind accuracy on "evidence" (n = 36) | 0.000 |

*Caption: the floor rise decomposed. "Alignment floor" is what a reader with the observed
label preferences would score by guessing labels alone, never seeing text; it reaches 0.382
of the observed 0.402, so 86.6 percent of the rise above chance is label-marginal
alignment. The per-label rows show the mechanism: matching concentrated the subset onto
word-usage/clarity, exactly the label the blind reader guesses most and best.*

**Found.** DECOMPOSED, and the answer is composition, not covariates: matching reweighted
the truth marginal toward the labels the blind reader guesses by default (two labels,
word-usage/clarity and precision, carry 52 percent of matched truth and the reader's
highest blind hit rates), and that alignment alone reproduces 87 percent of the floor's
rise. The covariate logistic reaches 0.60 training accuracy only by proxying the truth
label; the blind reader never saw a covariate, so residual covariate coefficients after
label dummies are label-correlation artifacts, not information flow.

**Means.** The L73 "floor jumps under matching" phenomenon is now mechanically explained
and it changes the confirmatory design before its freeze: the G129 matched draw is
truth-balanced WITHIN common support, which restores the analytic 1/k floor and makes the
matched margin directly readable instead of margin-over-a-moving-floor. The lesson
generalizes the L62/L64 chain one step: matching is a reweighting, and any reweighting
moves the blind floor through the label marginal, so every matched design either
re-balances truth or re-measures its floor (LESSONS §3 already carries the rule; this is
its mechanism).

### Curator roll-up

- **Theory group:** Decision Traces
- **Question in plain language:** Was the raised floor under covariate matching hiding real
  text information, or was it an artifact of how matching reshuffled the labels?
- **Outcome class:** Narrows
- **Result:** 87 percent of the matched blind floor's rise is label-marginal alignment; no
  text information was involved.
- **Project meaning:** The delta-specific recovery margin (8.2 points, L73) stands against a
  floor now known to be compositional; the confirmatory design balances truth within the
  matched support so its floor is analytic.
- **Next engineering obligation:** Run the G129 confirmatory battery per its preregistration
  once the queue clears the wqd gates.
- **Public claim:** Unchanged.
- **Curator decision required:** No.
- **Detail pointer:** G130c follow-up → `results/arg_recovery/floor_decomp.json`,
  `runners/run_g130c_floor_decomp.py`, prereg amendment in `prereg/g129.py`.

## L127 · The motivation-shift sampler finds planted switches: G149's ruler gate passes on the validated gridworld

**Hypothesis.** *(G149, his reframe: the movement instruments sample shifting motivations
over time, the policy-propensity landscape's peaks moving. Before any such sampler touches
text, it must find motivation shifts where they are REAL by construction.)* A window-local
shift statistic, blind to the generative parameters, can detect and localize goal switches
planted in Boltzmann paths on the validated BST engine.

**Method.** Paths sampled from the exact-value-validated gridworld engine (L119/L122
inventory) on the four decoded stimulus worlds: the active goal switches at a known step in
the planted arm, never in the null arm. The sampler computes, at each interior step, the
best two-goal split likelihood minus the best single-goal likelihood (summed step
log-likelihoods over the marked goals); detection threshold = the 95th percentile of the
null arm's maxima, so false alarms are priced at 5% by construction; a detection counts
only if localized within two steps of the planted switch. Two hundred paths per cell,
rationality crossed at four levels.

| walker rationality (β) | detected AND localized | localization error (steps) | null paths behind the threshold |
|---|---|---|---|
| 0.5 (noisy) | 58.5% | 1.13 | 200 |
| 1.0 | 72.5% | 0.48 | 199 |
| **2.0 (the paper's own fit)** | **89.5%** | **0.30** | 137 |
| 4.0 (near-deterministic) | 98.4% | 0.10 | 13 |

*Caption: each row is one rationality level. "Detected and localized" is the share of 200
planted-switch paths where the sampler's peak clears the 5%-false-alarm threshold and lands
within two steps of the true switch. The last column counts the no-switch paths that set
each threshold; the β = 4 row rests on only 13 nulls (near-deterministic single-goal
walkers reach their goal before twenty steps, so full-length no-switch paths are rare
there) and its threshold is correspondingly soft.*

**Found.** THE RULER PASSES. At the rationality the paper itself fitted to humans, nine of
ten planted switches are found and placed within a fraction of a step, against a threshold
that holds the quiet worlds quiet at 5%. Detection is monotone in rationality exactly as
the framing predicts: the more coherent the walker, the more legible the moment its
motivation moved. The β = 4 cell's threshold is underpowered (13 nulls) and is reported,
not leaned on; the load-bearing cell (β = 2) has 137 nulls behind it.

**Means.** The motivation-shift sampling concept has its first known-answer license: a
window-local statistic CAN locate real motivation shifts with priced false alarms, in the
one environment where the shifts are ground truth. What this does not license is any claim
about text: the next step is the same sampler ported to stimuli with known specified-state
shifts (the ladder corpora), and only after that does it earn a place among the
detector-facing channels. This is the first positive result of the free path under
standing ruling 7 — zero dollars, one afternoon, the validated Phase-1 inventory doing the
work.

### Curator roll-up

- **Theory group:** Decision Traces
- **Question in plain language:** Can a motivation-shift sampler actually find the moment a
  maker's goal changed, where we know the truth?
- **Outcome class:** Strengthens
- **Result:** 89.5% of planted goal switches detected and localized within two steps at the
  paper's own fitted rationality, false alarms priced at 5%.
- **Project meaning:** The movement family's reframe (sampling motivation shifts, not
  measuring depth) now has a validated instrument in principle; the text port is what stands
  between it and the detector stack.
- **Next engineering obligation:** Port the sampler to the ladder corpora, where specified
  states shift at known points in text.
- **Public claim:** Unchanged (constructed world only).
- **Curator decision required:** No.
- **Detail pointer:** G149 → `results/g149/switch_sampler.json`,
  `runners/run_g149_switch_sampler.py`.

## L128 · The 2025 hard test gate lands seven ten-thousandths from the print: the phase's cleanest anchor is matching

**Hypothesis.** *(G148: the PAN 2025 winner's printed TEST scores are reachable exactly from
its fully specified recipe, on the genuine labeled test split in our store, contamination-
gated clean — the phase's only test-set exact-value gates.)*

**Method.** The winner's own sentence-level recipe (deberta-base, every hyperparameter
stated in their notebook), trained locally in fp32 at seed 42, best-validation checkpoint,
scored with the pooled two-class macro-F1 the evaluator's source defines, test read once.
The runner's contamination gate aborts above 1% train-test overlap; both splits measured
well under it.

| gate | printed test | our test (seed 42, local) | delta | contamination |
|---|---|---|---|---|
| **hard** | 0.830 | **0.8293** | **−0.0007** | 0.39% |
| easy | 0.958 | 0.9535 | −0.0045 | 0.84% |
| medium | 0.823 | training now | — | — |

*Caption: each row is one difficulty's official local read against the winner's printed
test score. Hard lands inside the exact-value tolerance on the first seed; easy lands half
a point short, inside ordinary fine-tune seed noise, so the standing interval rule grades
it on three seeds (43/44 queued for both, plus medium's pair when its first read lands).
One residue recorded: our best validation on hard reads 0.8244 against their printed
validation 0.8331, the same kind of secondary-number gap ScholaWrite's accuracy showed.*

**Found.** THE HARD GATE MATCHES at exact-value tolerance: 0.8293 against 0.830, and the
cloud three-seed spread from the A/B (0.8280 to 0.8398, hardware caveat attached) brackets
the print, so the number is not a lucky seed. This is the contamination-clean anchor the
PAN 2024 work could never supply — the 2025 splits carry 0.4 to 0.8% overlap against
PAN 2024's ~16%, and the gate read is on a genuine held-out test set rather than a blended
validation. Easy sits at −0.0045 pending its interval; the formal G148 verdict completes
when medium and the six seed arms land.

**Means.** The recreation phase's cleanest target is behaving exactly as a faithful
recreation should: first-seed agreement to the third decimal on the primary number, with
the secondary-number residue recorded rather than explained away. For Phase 2.0 this
matters twice — the recipe is now a validated candidate for the detector substrate's
trained component (2.0E), and the clean 2025 splits are the natural first scoring ground
for the free-path stack.

### Curator roll-up

- **Theory group:** Infrastructure only
- **Question in plain language:** Can we hit the 2025 winner's held-out test numbers
  exactly, on clean data, from their published recipe?
- **Outcome class:** Infrastructure
- **Result:** Hard test gate matched at −0.0007; easy at −0.0045 pending its three-seed
  interval; medium training.
- **Project meaning:** The phase's cleanest anchor validates our training pipeline at
  test-set grade, and the recipe graduates to candidate substrate for the Phase 2.0
  detector.
- **Next engineering obligation:** Land medium and the six interval seeds; then the G148
  verdict block.
- **Public claim:** Unchanged until the full verdict.
- **Curator decision required:** No.
- **Detail pointer:** G148 → `results/pan25_winner/wqd_hard.json`, `wqd_easy.json`,
  L125's cloud seed spread, prediction siblings on disk.

## L129 · The third member clears its gate under the corrected scope, and the vote re-gates on the stabilizer rung

**Hypothesis.** *(The PAN 2024 scope fork, member 2: ernie under head-scope dropout 0.25
should hold its above-gate margin, having tolerated both scope readings.)*

**Method.** The winner's recipe with dropout confined to the classification head (the
notebook's usual meaning), ten epochs, seed 42, validation macro-F1 against the notebook's
own member gate; the blended-leak caveat (L118) rides every PAN 2024 validation number,
theirs and ours alike.

**Found.** Ernie head-scope reads 0.8792 at the final epoch (best 0.8795) against the 0.849
member gate: +0.030 above, the third member confirmed under the one-recipe rule. The system
vote could not run — the deberta member's collapsed run wrote no prediction files — and is
retargeted to gate on the seed-43 stabilizer rung now training; if that rung collapses too,
the ladder's next rungs (warmup 0.10, then lr 4e-5) decide whether the vote ever gets its
third member.

**Means.** Two of three members now sit above their gates under the corrected scope with
the third blocked on the one model this card keeps failing to train; the vote, and with it
the last PAN 2024 comparison, waits on the deberta ladder.

### Curator roll-up

- **Theory group:** Infrastructure only
- **Question in plain language:** Does the ensemble's third member hold up under the
  corrected dropout reading, and can the vote run?
- **Outcome class:** Infrastructure
- **Result:** Ernie +0.030 above its member gate; the vote re-gated on the deberta
  stabilizer rung.
- **Project meaning:** The PAN 2024 member set is one trainable deberta away from its vote.
- **Next engineering obligation:** The stabilizer ladder (rung 1 training; rungs 2 and 3
  queue on its result; rung 4 remains the priced cloud diagnostic pending approval).
- **Public claim:** Unchanged.
- **Curator decision required:** No.
- **Detail pointer:** `results/pan_winner/ernie_hard_headdrop25.json`; the vote stage's
  retarget in `runners/run_queue.py`.

## L130 · The 2025 test gates on their seed intervals: easy lands a ten-thousandth from the print, medium brackets it from above

**Hypothesis.** *(G148, the interval half: the fine-tune verdict rule grades each printed
test gate on a three-seed local interval, not one read.)*

**Method.** The winner's recipe at seeds 43 and 44 beside the seed-42 official reads, same
local card, same evaluator, test read once per run.

| gate | printed | seed 42 | seed 43 | seed 44 | verdict |
|---|---|---|---|---|---|
| hard | 0.830 | 0.8293 | 0.8248 | 0.8276 | **MATCHED at tolerance**: the seed-42 read sits 0.0007 under the print; the local interval tops 0.0007 under it and the cloud spread (L125, hardware caveat) brackets it |
| easy | 0.958 | 0.9535 | **0.9579** | 0.9541 | **REPRODUCED**: seed 43 lands one ten-thousandth from the print, the interval edge touching it |
| medium | 0.823 | **0.8303** | 0.8173 | running | **REPRODUCED pending seed 44**: the print sits inside the seed interval, the official read 0.0073 ABOVE it |

*Caption: each row is one difficulty's printed held-out test score against three local
seeds. The interval rule (the ScholaWrite precedent) asks whether the print sits inside or
at typo distance from the seed spread; all three gates satisfy it on the seeds landed so
far, with medium's third seed still training.*

**Found.** The phase's cleanest anchor reproduces across all three difficulties at seed
grade: one gate touched at the fourth decimal, one bracketed from above, one at typo
distance below. The G148 verdict block formally closes when medium's third seed lands.

**Means.** The 2025 winner's pipeline is fully in hand at test-set precision on
contamination-clean data, which closes the recreation question and hands Phase 2.0 a
validated trained substrate.

### Curator roll-up

- **Theory group:** Infrastructure only
- **Question in plain language:** Do the 2025 test gates hold on proper seed intervals?
- **Outcome class:** Infrastructure
- **Result:** All three printed gates sit inside or at typo distance from their local seed
  intervals (closest: easy at one ten-thousandth).
- **Project meaning:** The recreation's cleanest anchor is closed in substance; the formal
  block waits on one seed.
- **Next engineering obligation:** Fold the final seed, write the G148 verdict block.
- **Public claim:** The recreation claim in the README stands, now on intervals.
- **Curator decision required:** No.
- **Detail pointer:** `results/pan25_winner/wqd_*_s4*.json`.

## L131 · The paper's strongest member finally trains: seed 43 lands deberta above its gate, and the collapse account closes as seed fragility

**Hypothesis.** *(The stabilizer ladder, rung 1: if the deberta head-scope collapse is
stochastic rather than recipe-driven, an identical run at a fresh seed should train.)*

**Method.** The identical recipe (fp32, micro-batch 12 by accumulation 5, head-scope
dropout 0.25, warmup 0.06) at seed 43, after seed 42 collapsed flat twice and the
all-module twin collapsed too; ten epochs to the notebook's schedule.

**Found.** IT TRAINS: final and best validation 0.8612 against the 0.8567 member gate,
0.0045 above. Three prior failures (fp16 overflow, two fp32 flatlines) resolve into one
account: the member is seed-fragile under this recipe on this card, not untrainable. The
outage's restart cost the run one full repeat, and the second attempt landed. Rungs 2 and 3
of the ladder are moot; **rung 4, the priced cloud diagnostic, is moot and dies unspent** —
the free path answered the question the $1.30 was budgeted for. The vote's needs are now
satisfied and it fires on the next queue pass.

**Means.** All three 2024 members now sit above their gates under the corrected one-recipe
scope (roberta +0.021, ernie +0.030, deberta +0.0045), all still carrying the blended-leak
caveat every 2024 validation number carries (L118). The vote is the last 2024 read.

### Curator roll-up

- **Theory group:** Infrastructure only
- **Question in plain language:** Was the untrainable member a recipe problem or a seed
  problem?
- **Outcome class:** Narrows
- **Result:** Seed fragility: the identical recipe trains at seed 43, 0.0045 above gate.
- **Project meaning:** The member set is complete; the cloud diagnostic is never needed;
  training-stability failures on this card get a seed rung before any recipe surgery.
- **Next engineering obligation:** Land the vote.
- **Public claim:** Unchanged.
- **Curator decision required:** No.
- **Detail pointer:** `results/pan_winner/deberta_hard_headdrop25_s43.json`.

## L132 · The confirmatory battery lands: purposes recover far above every floor, the reader never fabricates, and the nineteen cheap features beat it head to head

**Hypothesis.** *(G129 confirmatory, preregistered in `prereg/g129.py` with Amendment 1:
recorded revision purposes are recoverable from the delta beyond matched alternatives and
beyond a cheap change-feature baseline, with exhaustive verdict bands and a fabrication
arm.)*

**Method.** Eight arms off one shared manifest (identical events, candidate sets, and
seeds per arm): recovery, blind, and shuffled-truth on the truth-balanced full set
(616 events, analytic floor 0.25); recovery and blind on the truth-balanced matched draw
(176 events, the L126 amendment restoring its analytic floor); brief-alone and
source-alone context arms; the no-op-delta fabrication arm with an explicit no-revision
option (200 unchanged + 200 real as the symmetric control); and the 19-dimension
change-feature classifier under author-grouped cross-validation restricted to the same
candidate sets. Verdict computed once, all statistics on disk.

| arm | read | floor | verdict band |
|---|---|---|---|
| recovery, full set | **0.4854** | 0.25 | **H-A REPLICATES** (margin 0.235, band ≥ 0.15) |
| recovery, matched + balanced | **0.4148** | 0.25 | **H-B SURVIVES** (margin 0.165, band ≥ 0.08; n = 176 of the powered 283, the shortfall clause disclosed) |
| blind / blind matched | 0.2419 / 0.2216 | 0.25 | both within the floor's CI, gates clean |
| brief alone | 0.2744 | 0.25 | context supplies almost nothing |
| source alone | 0.3052 | 0.25 | topic supplies a little; the delta supplies the rest |
| fabrication (200 no-op deltas) | **0.000** | — | **A7 CLEAN**: the reader asserted a purpose on zero unchanged sentences; the symmetric control missed 1 of 200 real revisions and recovered at 0.53 with the extra option present |
| reader vs change block | 111 vs 154 exclusive wins | — | **H-C: the reader LOSES** (exact McNemar p = 0.0097; the block read 0.5552 on identical events) |
| shuffled truth | 0.1104 | 0.25 | flagged by the gate as written; see below |

*Caption: each row is one preregistered arm on the shared manifest. "Floor" is the
analytic chance rate under truth balancing. The margin bands are the card's, exhaustive by
construction. The change block is the nineteen string-diff features (L85) trained with
authors held out.*

**The shuffle flag, faced squarely.** The card said the shuffled-truth arm must land at
chance or the run is void, and it landed BELOW chance, so the gate as written fires. The
gate's failure model is a scoring leak, and a leak pushes shuffled accuracy UP toward the
recovery number, never down. The below-chance read is the a-priori-derivable signature of
a delta-tracking reader: shuffled labels are drawn from all eight while candidate sets are
anchored on the original truth, so the expected match rate for a reader that follows the
real delta is 0.125, and the observed 0.110 sits beside it. The gate encoded the null
hypothesis's expectation without stating a direction, the same specification defect class
as the L73 bands, and it is recorded as such (LESSONS §3): leakage is NOT indicated, the
flag is disclosed rather than waived, and every future void gate states its direction and
its expectation under the alternative.

**Found.** The three questions the battery was built to ask all answered. Recorded
purposes ARE recoverable from the delta: far above the analytic floor at power on the full
set, and the delta-specific margin that survived covariate matching at 8 points in L73
doubles to 16.5 points once the matched floor is balanced back to analytic, though that
arm runs at 176 of its powered 283 and says so. The reader does NOT fabricate: zero
asserted purposes on two hundred no-op deltas, with the symmetric control proving the
no-revision option is not a magnet (one miss in two hundred real revisions). And the
zero-shot reader is NOT the best instrument for the job it just validated: nineteen
string-diff features beat it by seven points head to head on identical events, the L85
lesson landing at full strength on the confirmatory stage.

**Means.** The 2.0D real-text gate is MET on its substance: choice recovery is real,
controlled, calibrated against fabrication, and not explained by context, topic, or label
composition. And the phase's stated response to H-C executes as preregistered: the
decision layer's compact detector-facing features start from the change-feature block,
with the LLM reader retained where it is uniquely strong (the fabrication-bounded
abstention behavior the block cannot supply). The construct question (does any of this
track decision structure rather than this corpus's particulars) belongs to G131's
factorial, which is now the core program's next build.

**Reclassified (2026-08-19, curator-ratified; the full audit is L137).** "Gate MET" was
over-claiming under the card's own terms, and the correction is a demotion of the label,
not the data. Two clauses of the frozen card were disclosed but not applied: the shuffle
arm's void condition fired (0.110 against the written 0.25 expectation), and a
post-hoc-derived corrected expectation (~0.125, the label-marginal rate for a
delta-tracking reader) repairs the next card but cannot restore this run's confirmatory
grade; and the matched arm's power clause says a shortfall (176 of 283) downgrades that
verdict to the pilot evidence tier, which is now applied rather than merely disclosed.
Standing status: strong replication-tier evidence for paired-delta purpose recovery, with
zero fabrication; confirmatory grade owed to the fresh G129b battery whose gates carry
both expectations and a direction from birth. One further scope correction from the same
audit: the winning change block reads BOTH the old and new text, so it is a paired-delta
interface feature, not an inference feature for a final-artifact detector; the interface
assignment is now in the evaluation contract.

### Curator roll-up

- **Theory group:** Decision Traces
- **Question in plain language:** Do recorded revision purposes survive a powered,
  fully-controlled recovery battery, and is the language-model reader the right instrument?
- **Outcome class:** Strengthens
- **Result:** Recovery replicates at 0.4854 against a 0.25 analytic floor with zero
  fabrication on no-op deltas; the cheap feature block beats the reader head to head.
- **Project meaning:** *(amended 2026-08-19)* The decision-recovery claim is confirmed on
  real text at strong-replication tier, confirmatory grade owed to G129b; the
  detector-facing representation builds on the feature block, with the reader supplying
  abstention, inside the paired-delta interface only.
- **Next engineering obligation:** *(amended 2026-08-19)* The G129b fresh confirmatory and
  the Phase 2.1 program; stacking (2.0F) re-gated behind the contract's four decision gates.
- **Public claim:** *(amended 2026-08-19)* The README's opening claim stays at
  replication-tier wording; "confirmatory" is forbidden until G129b lands clean.
- **Curator decision required:** No.
- **Detail pointer:** G129 → `results/g129/verdict.json`, `prereg/g129.py`, all arm files
  and partials on disk.

## L133 · The vote clears its gate and the medium interval completes: the fifth anchor closes, and with it the recreation phase's scorecard

**Hypothesis.** *(The PAN anchor's last two reads: the three-member majority vote against
the notebook's own 0.8658 vote gate, and medium's third seed completing the G148 interval.)*

**Method.** Majority vote over the three head-scope members' validation predictions
(roberta seed 42, ernie seed 42, deberta seed 43 — the seed the member trains at), scored
with the pooled evaluator; medium seed 44 under the wqd recipe, test read once.

| read | value | gate | delta |
|---|---|---|---|
| the 2024 majority vote | **0.8799** | 0.8658 | **+0.0141** |
| medium, seed 44 | 0.8253 | printed 0.823 | +0.0023 |

*Caption: the vote is a validation-split read and carries the blended-leak caveat every
2024 validation number carries, ours and theirs alike (L118); the honest leak-free
capability stays 0.81 to 0.83. Medium's third seed completes its interval
[0.8173, 0.8303] with the print inside it and two of three seeds above.*

**Found.** The vote clears its gate by 1.4 points, the last member-set read the 2024 half
owed, and the G148 interval table completes: hard at typo distance (print 0.0007 over the
seed-42 read), easy touched at one ten-thousandth, medium bracketed with the print inside
the spread. THE PAN ANCHOR CLOSES: 2024's members and vote all above their gates under the
corrected one-recipe scope with the contamination account closed from three directions,
and 2025's three test gates reproduced on seed intervals over contamination-clean data.
One infrastructure defect surfaced and died on the way: the vote's member-file path was
hand-built with a different tag position than the trainer writes, so it failed on every
tagged member until the construction was unified (LESSONS §5).

**Means.** The recreation phase's scorecard is complete: Armstrong-Mindermann passed
exactly and extended; ScholaWrite reproduced on its interval; ArgRewrite settled with its
embedding rows terminally bounded; BST Experiment 1 complete at printed precision
(Experiments 2 and 3 stay open behind their stimulus decodes as the anchor's noted
extension); and PAN closed on both halves. Every anchor's number is now our known answer,
which was the phase's entire purpose.

### Curator roll-up

- **Theory group:** Infrastructure only
- **Question in plain language:** Does the ensemble clear its own published gate, and does
  the last seed complete the interval?
- **Outcome class:** Infrastructure
- **Result:** Vote 0.8799 against 0.8658; medium's interval closes with the print inside.
- **Project meaning:** The fifth anchor and the recreation scorecard are closed; Phase 1's
  remaining open item is the BST Experiment 2 and 3 extension.
- **Next engineering obligation:** The G148/PAN verdict lines are final; the phase's
  formal wrap note is his to call.
- **Public claim:** The README's recreation row stands, now complete.
- **Curator decision required:** No.
- **Detail pointer:** `results/pan_winner/vote_hard.json`,
  `results/pan25_winner/wqd_medium_s44.json`.

## L134 · The shift sampler's first text port is blind: surface-feature windows see neither specification shifts nor topic changes

**Hypothesis.** *(G149's text port: the sampler concept licensed on the gridworld, applied
to text where the known shift is a same-topic splice between ladder artifacts at
specification doses 0 and 60.)*

**Method.** Per 40-word window, the nine static surface features plus the 40-word
function-word profile; shift score = z-scored cosine distance between adjacent windows;
threshold at the 95th percentile of unspliced texts (60 nulls); planted arm = 12
same-topic rung-crossed splices at known boundaries; confound arm = 12 same-rung
topic-crossed splices.

**Found.** NOTHING. Zero of twelve rung-crossed splices detected (over-threshold rate
0.083, the false-alarm rate itself), and the topic-crossed confound arm is equally blind,
so the instrument fails even on the change it was expected to over-detect. The
surface-feature windowed distance is not a shift sampler at this window size on these
texts. The methods audit (L136) then challenged the null on the bounded-statistic ground
(within-item z-scoring of a thirteen-point series caps the reachable maximum near 3.5
against a 2.44 threshold, the L53 defect class) and reran the same splices under two
un-handicapped forms, raw distances and population-standardized distances, each against
its own null-population threshold: zero of twelve both times, false alarms at rate. The
null is the features, not the normalization, and it now stands on three statistic forms.

**Means.** The gridworld license (L127) does not transfer through cheap features: the
gridworld version read per-step LIKELIHOODS under competing hypotheses, and the text port
substituted feature distances, which was the actual change and the apparent cause of
death. The next form is likelihood-grade: per-window scores under competing specification
hypotheses (a model-based reader), or the change-feature block applied between windows
rather than raw statics. Narrows the instrument class; the framing is untouched.

### Curator roll-up

- **Theory group:** Decision Traces
- **Question in plain language:** Does the motivation-shift sampler work on text the way
  it worked on the gridworld?
- **Outcome class:** Kills (this instrument form, not the concept)
- **Result:** Zero of twelve planted specification shifts detected; the confound arm is
  equally blind.
- **Project meaning:** The text sampler must carry likelihood-grade evidence per window;
  surface distances are not it.
- **Next engineering obligation:** The likelihood-form design, after the G131 build.
- **Public claim:** Unchanged.
- **Curator decision required:** No.
- **Detail pointer:** G149 → `results/g149/text_port.json`,
  `runners/run_g149_text_port.py`.

## L135 · The leakage reference nearly solves the unmatched pilot: forty-nine surface features read provenance at 0.98

**Hypothesis.** *(2.0E's reference component: a bare surface-feature model whose job is to
reveal how much provenance the benchmark gives away for free.)*

**Method.** Nine document statics plus forty function-word rates, gradient-boosted trees,
five-fold grouped cross-validation with rewrites lineage-locked to their human sources; the
240 pilot machine artifacts against the 86 human first drafts.

**Found.** Accuracy 0.9785, area under the curve 0.9921; the seen local family separates
perfectly and rewrites separate at 1.0. On the pilot as currently composed, provenance is
nearly free from surface statistics.

**Means.** The reference model is doing its designed job on its first read: this number is
the floor every detector claim must beat FOR REASONS THE SLICES CAN SHOW, and at 0.98 it
says the current pilot cannot yet test anything interesting, because register and quality
are unmatched (clean machine prose against student drafts with typos). The benchmark's
shortcut-breaking cells (quality-matched pairs, register-matched negatives, low-effort
human work) are what make the task non-trivial, and this measurement converts them from
design intentions into requirements with a number attached.

### Curator roll-up

- **Theory group:** Infrastructure only
- **Question in plain language:** How much provenance does the free-path pilot give away to
  trivially cheap features?
- **Outcome class:** Infrastructure
- **Result:** Nearly all of it: 0.98 accuracy from surface statistics on the unmatched
  pilot.
- **Project meaning:** The leakage reference is live, and the matched counterexample cells
  are now a measured requirement before any detector number means anything.
- **Next engineering obligation:** Quality- and register-matched negative cells in the
  benchmark build.
- **Public claim:** Unchanged.
- **Curator decision required:** No.
- **Detail pointer:** `results/g153_pilot/surface_ref.json`,
  `runners/run_g153_surface_ref.py`.

## L136 · The Phase 2.0 methods audit: every built test against the lesson record, one defect found and fixed, one null re-verified three ways, two retroactive derivations recorded

**Hypothesis.** *(His directive: verify that every currently built Phase 2.0 test, and the
earlier Phase 2.0 work, actually implements what the recreation phase paid to learn — the
LESSONS, the CONTROLS, and the design contracts.)*

**Method.** Artifact-by-artifact compliance sweep over the eleven Phase 2.0 runners,
corpora, and cards (the G129 battery and card, the floor decomposition, both G149 forms,
both G153 arms, the G131 generator, the G150 A/B chain), each checked against the
applicable LESSONS sections (§3 statistics, §4 model arms, §5 infrastructure, §1d data
hygiene), the CONTROLS taxonomy, and the phase brief's constraints; suspect findings
re-run rather than argued.

| artifact | verdict | detail |
|---|---|---|
| G129 battery + card | **CLEAN, one known defect already on record** | Analytic floors, uniform decoys, shared manifest, per-arm seeds, author-grouped CV, disk statistics, exhaustive bands all present; the shuffle gate's missing direction is L132's finding and now carries its retroactive DESIGN CHECK derivation |
| G149 text port (L134) | **NULL RE-VERIFIED, three statistic forms** | The audit raised the bounded-statistic challenge (within-item z on a 13-point series caps near 3.5 vs a 2.44 threshold, the L53 class) and reran with raw and population-standardized distances: zero of twelve on all three forms. The null belongs to the features |
| G131 generation corpus | **ONE DEFECT FOUND AND FIXED** | Per-call seeds were routed through Python's process-salted hash(), so the actual seeds were non-deterministic and unrecorded, violating the pin-determinism lesson (§4). The runner now derives seeds from the stable cell enumeration and records the seed actually used; the existing 180-artifact corpus stands as recorded data (text plus instruction ground truth is the record) with the regenerability limitation written into both manifests |
| G153 generation + surface reference | **CLEAN** | Deterministic recorded seeds, model digests, lineage-locked grouped CV, imbalance disclosed via AUC, manifest yield guard |
| G149 gridworld, G130c decomposition, G150 A/B chain | **CLEAN** | Directional thresholds, preregistered rule, train-only standardization, seed separation; the A/B's one wiring defect (lost prediction siblings) was found and fixed at the time |
| smaller folds | recorded | The verdict gates' p-values stay classed as controls outside the multiplicity family (noted, defensible either way); the fixed-label-list rule gets an explicit line at the evaluation contract's freeze; G131 records gain the model digest going forward |

**Found.** The lesson record is substantially implemented: of eleven artifacts, nine are
clean against every applicable rule, one carried the already-receipted gate defect that
created the DESIGN CHECK rule, and one (the G131 generator's seed path) carried a genuine
new violation of a named lesson, now fixed with the damage honestly bounded. The audit's
challenge to its own strongest null made that null stronger.

**Means.** The painstakingly-earned rules are mostly crossing into the new phase's code,
and the two places they did not cross share one shape: both were single lines whose
correctness could not be seen locally (a gate without its alternative, a seed through a
salted hash). The DESIGN CHECK block and the design_lint hook exist for exactly that
shape, and the G131 recovery study, the next gate-bearing design, is the first build that
will carry the block from birth.

### Curator roll-up

- **Theory group:** Infrastructure only
- **Question in plain language:** Did the lessons the recreation phase paid for actually
  make it into the Phase 2.0 builds?
- **Outcome class:** Infrastructure
- **Result:** Nine of eleven artifacts clean; one new defect (non-deterministic generation
  seeds) fixed with its damage bounded; the L134 null re-verified on three statistic forms.
- **Project meaning:** The method transfer is real but not free; the enforcement layer
  (DESIGN CHECK + lint) covers the failure shape both misses shared.
- **Next engineering obligation:** The G131 recovery study, designed under the new block.
- **Public claim:** Unchanged.
- **Curator decision required:** No.
- **Detail pointer:** manifests' determinism notes, `prereg/g129.py` DESIGN CHECK,
  `runners/run_g131_gen.py` seed fix, this entry's table.

## L4 · Can weak effects be stacked into a detector?

**Hypothesis.** *(The curator's.)* Several small real effects combined may produce a usable
instrument where none alone is enough.

**Research context.** This is what commercial machine-text detectors already do, and it reaches
near-perfect accuracy on that problem. **Simulation T-8 now adds a caution from our own side:** ten
hand-picked features combined lifted the hardest cases to near-perfect, while adding sixty generic
bank features gained little on average and **lost more in the worst case**. So: combine, but curate.

**Verdict: OPEN, not yet run.** Two conditions before believing any stack — it must beat its best
single component **on held-out data**, and its errors must not be the same errors.

## L137 · An external audit he commissioned survives verification: the confirmatory label demotes, the factorial corpus is exploratory, and the missing piece is an input contract

**Hypothesis.** *(The curator ran an independent read-only analysis agent over commit
96a8b3c and brought its verdict for adjudication: that G129's confirmatory grade cannot
stand on a run whose own shuffle gate voided; that the G131 corpus fails its construct
because assigned instructions were not verified as executed; and that the program
conflates three products because inference-time inputs were never frozen. The question:
do its factual claims survive independent verification against the repo?)*

**Method.** Every checkable claim re-verified from primary artifacts rather than the
agent's reasoning: the G129 verdict file read directly for the void flag and power
shortfall; the STATE claim language grepped; the contract draft searched for any
inference-input section; and the G131 compliance numbers re-derived with an independently
written mechanical checker (different instruction coverage from the agent's: 366
checkable surface-instruction assignments vs their 244) over all 180 artifacts.

| agent's claim | independent check |
|---|---|
| shuffle gate recorded void at 0.110 | confirmed on disk, `"void": true`, p vs floor 0.0 |
| matched arm underpowered, 176 of 283 | confirmed, `"powered": false` on disk |
| repo claims "real-text gate is met" | confirmed, STATE.md said exactly that |
| contract never froze inference inputs | confirmed, no such section existed |
| ~62% of checkable assigned surface instructions executed | confirmed at 64.2% on my checker (235 of 366); 66 of 80 surface artifacts carry at least one unexecuted instruction |
| 17 length-band violations, all surface-target | confirmed exactly, 17 of 17 surface |

*Caption: left column is the external agent's factual assertion; right column is what the
repo itself returned when checked from scratch. The two compliance checkers differ in
which instructions they can verify mechanically, and land within 2.3 points of each
other.*

**Found.** The audit is right on substance everywhere it was checkable, and four
pushbacks (accepted by the curator) bound its reach: nothing decisive was queued, so the
"pause" is a redesign before first build; the demotion is of the label, not the data
(recovery, matched survival, and zero fabrication keep replication-tier standing); the
change-morphology reading of the reader's loss was the preregistered response, not a
discovery; and the surface-leakage 0.98 was built by us as the warning it is now cited
as. The deepest finding is structural: the 19-dimension change block that beat the reader
requires both old and new text, so it cannot be an inference feature for a final-artifact
detector, and no document said so because inference-time inputs were never part of the
contract.

**Means.** Curator-ratified same day, with the phase named by him: **Phase 2.1**, the
repair-and-foraging program. The reclassification landed this pass (STATE, the L132
addendum, theory rows, TODO); the evaluation contract gains the three-interface
inference-input section and the four stacking gates; the G131 corpus is reclassified
exploratory and becomes the foraging substrate (G158: realization adjudication, cheap
baselines, artifact-only recovery against realized choices, family transfer);
confirmatory grade is owed to G129b under a card whose gates carry both expectations and
a direction from birth; the decisive factorial rebuilds on paired base material only
after foraging reports. Two lessons banked: "gate met" language only follows all gates
passing under the card's own terms, and assigned is not realized.

### Curator roll-up

- **Theory group:** Decision Traces
- **Question in plain language:** Does an outside audit of the Phase 2.0 evidence hold up,
  and what does the program owe if it does?
- **Outcome class:** Narrows
- **Result:** Every checkable claim verified (compliance checkers agree within 2.3
  points); G129 demotes to strong replication and G131's corpus to exploratory.
- **Project meaning:** The recovery evidence stands, but confirmatory language, the
  known-answer construct test, and any stacking all wait on Phase 2.1's repairs.
- **Next engineering obligation:** The G158 foraging battery on the existing corpus, then
  G129b, then the decisive rebuild.
- **Public claim:** Weakened; "confirmatory" is forbidden until G129b lands clean.
- **Curator decision required:** No (ratified 2026-08-19, phase named 2.1 by him).
- **Detail pointer:** L137 ← `results/g129/verdict.json`, the scratchpad checker promoted
  to `runners/run_g131_adjudicate.py`, `docs/design/EVAL_CONTRACT_2_0.md` §3b.

## L138 · The foraging battery's first two stages land: two-thirds realization at best, and cheap features read the factorial cells almost completely

**Hypothesis.** *(G158 stages a and b, Phase 2.1.3, exploratory by declaration: how much of
the G131 corpus's assigned ground truth was actually executed, and how much of its cell
structure is readable from features nobody would call decision recovery — the bar any
later recovery claim must beat.)*

**Method.** Stage (a): every one of the 880 instruction-assignments across all 180
artifacts run through graded mechanical checks (exact where the string rule is the
instruction's own criterion, approximate where it is a conservative proxy), with every
check's base rate measured on the zero-instruction control essays; the 556 semantic
assignments listed for the queued reader-adjudication arms. Stage (b): logistic
classifiers on single cheap feature sets, leave-one-topic-out so topic never carries the
answer, predicting the target axis (surface vs problem, instructed cells) and the amount
axis (0/3/8, all cells); permutation p-values from 200 within-topic label shuffles
(resolution floor 0.005), all registered in the multiplicity audit as diagnostics.

| measurement | read | meaning |
|---|---|---|
| checkable realization rate | **0.586** (324 of 880 checkable; exact-grade 0.68, approx 0.51) | roughly a third to two-fifths of checkable asks were not executed; assigned truth is invalid as a known answer |
| base rates on unasked controls | 0.0 to 0.5 by instruction | the punctuation-style instruction passes unasked half the time (weak signal); the you-twice and twenty-word instructions never do (strong signal) — the decoy-design input for the rebuild |
| target from length alone | **0.725** (p 0.005) | reproduces the external audit's 73.1% probe within a point |
| target from punctuation / lexical echo | 0.8625 / **0.9187** (both p 0.005) | instruction products (question marks, lists) and instruction WORDS echoed in the text nearly solve the axis |
| target from all combined | **0.950** (p 0.005) | the cell structure is almost fully readable from trivia |
| amount from length alone | 0.400 (p 0.87) | length alone does not carry dose |
| amount from all combined | 0.756 (p 0.005) | but the combined trivia carry most of it |

*Caption: each row is one leave-one-topic-out classifier on one cheap feature family
(majority base rates 0.5 for target, 0.44 for amount). "Lexical echo" is the share of each
instruction pool's content words appearing in the essay — pure word overlap, no reading.*

**Found.** The corpus's construct failure now has its full measurement. Ground truth
executed at 58.6% where checkable, and the axes the recovery study was meant to probe are
almost entirely recoverable from length, punctuation marks, and echoed instruction
vocabulary. A reader could score 95% on target identification while reading nothing about
choices at all.

**Means.** Two binding numbers for everything downstream. Any artifact-only recovery
result on this corpus (stage c) is interesting only in the margin ABOVE these baselines on
realization-verified instructions; and the 2.1.5 rebuild must match length and register by
construction, use consequence-matched decoys drawn to equalize lexical echo, and prefer
instructions whose unasked base rate is near zero. The queued reader arms complete the
realization table; stage (c) is designed after they land.

### Curator roll-up

- **Theory group:** Decision Traces
- **Question in plain language:** How much of the factorial corpus is real, and how much of
  its structure can trivial features read?
- **Outcome class:** Infrastructure
- **Result:** Checkable instructions were executed at 58.6%, and cheap features identify
  the instruction-type axis at 95%.
- **Project meaning:** The corpus supports foraging only; every recovery claim on it must
  clear the now-measured trivial-feature bar on realization-verified truth.
- **Next engineering obligation:** The queued reader-adjudication arms, then stage (c)
  scored against realized instructions.
- **Public claim:** Unchanged (nothing here was ever claimable).
- **Curator decision required:** No.
- **Detail pointer:** `results/g158/realization_mechanical.json`,
  `results/g158/baselines.json`, runners `run_g158_adjudicate.py` / `run_g158_baselines.py`.

## L139 · The reader adjudicator fails its own validation: it credits two-thirds of provably ignored instructions

**Hypothesis.** *(G158 instrument validation, run before stage (c) may consume any reader
verdict: does the local reader's realized/unrealized adjudication agree with mechanical
string checks on the assignments where a string test is decisive?)*

**Method.** The adjudicator re-judged a stratified sample of 80 mechanically decidable
assignments blind (half mechanically realized, half not, seeded draw), same prompt,
temperature 0, evidence spans required; agreement scored overall and on the exact-grade
subset where the string rule IS the instruction's own criterion.

| measure | read |
|---|---|
| overall agreement with mechanics | 0.6125 |
| over-credit rate (reader says realized where mechanics say not) | **0.725**; **0.688 on exact-grade rows** (11 of 16) |
| under-credit rate | 0.05 |
| ambiguous calls | 0 of 80 (and 0 of 556 in the live arms) |
| reader said "realized", all rows | 67 of 80 |

*Caption: exact-grade rows are instructions like "no sentence over twenty words" where the
mechanical verdict is not a proxy but the criterion itself; over-credit there is proof of
adjudicator failure, not check disagreement.*

**Found.** The adjudicator is a yes-machine. It asserted realization on two-thirds of
assignments an exact string test proves were ignored, never once used its ambiguous
option across 636 total judgments, and the required evidence span did not prevent
over-credit (a verbatim quote can exist without satisfying the instruction). The
symmetric direction is nearly clean (under-credit 5%), which is the signature of
acquiescence, not noise.

**Means.** The 556 reader-adjudicated verdicts (95% "realized" in both families) carry no
evidentiary weight and are retained only as raw records with this warning label. Stage
(c)'s ground truth is the mechanical exact-grade subset only; the semantic instructions
either get a redesigned adjudication instrument (validated against the decidable subset
BEFORE its verdicts are consumed, per the ruler-validation rule) or stay out of the
known-answer set. The 2.1.5 rebuild inherits the same constraint: prefer instructions
whose realization is mechanically decidable, and treat model adjudication as an
instrument that must pass validation, never a default. Lesson banked (LESSONS §4).

### Curator roll-up

- **Theory group:** Decision Traces (instrument)
- **Question in plain language:** Can the local reader be trusted to audit whether an
  instruction was actually executed?
- **Outcome class:** Kills
- **Result:** The adjudicator credited 69% of provably ignored instructions on the
  decisive subset.
- **Project meaning:** Realization ground truth is mechanical-only until an adjudication
  instrument passes this validation; the corpus's semantic instructions currently have no
  usable realization labels.
- **Next engineering obligation:** Stage (c) designed on the mechanical exact-grade
  subset; adjudicator redesign optional, validation-gated.
- **Public claim:** Unchanged.
- **Curator decision required:** No.
- **Detail pointer:** `results/g158/reader_validation.json`; live-arm verdicts in
  `realization_reader_{qwen,llama}.json`, warning-labeled.

## L140 · Stage (c) lands both ways at once: the reader recovers surface constraints at exactly chance while word-echo scores above it, and clears the problem-pool echo bar by eleven points in both families

**Hypothesis.** *(G158 stage (c), exploratory: given only the final essay and four
same-pool candidates, can a bounded reader identify which instruction was given — on
surface events where the truth is mechanically verified executed and every decoy verified
unsatisfied, and on problem-pool events scored against assignment with the null
preregistered uninterpretable?)*

**Method.** Forced choice at k = 4, artifact only. Surface arm: 100 events (exact-grade
realized truths, decoys mechanically unsatisfied in the same essay, 2 thin-decoy skips
disclosed); banded read on the truth-balanced 48 (12 per instruction, CONTROLS entry 6);
blind floor and the L138 word-echo baseline on identical candidate sets; a mechanical
oracle as the wiring check; 20 zero-instruction essays with an explicit none option as
the fabrication control. Problem arm: all 440 assignments, decoys drawn unassigned from
the same pool, echo bar on identical sets.

| arm | raw | truth-balanced | meaning |
|---|---|---|---|
| surface recovery (reader) | 0.41 | **0.25** | exactly chance once label frequency cannot carry it |
| surface blind floor | 0.24 | 0.21 | construction clean |
| surface echo bar | 0.30 | **0.375** | word overlap beats the reader on the balanced read |
| mechanical oracle | 1.00 | — | zero wiring defects: the answer IS in the text |
| fabrication control | 0.05 | — | the none option is used honestly (19 of 20) |
| problem recovery (reader) | **0.9091** | — | qwen 0.950, llama 0.868 |
| problem echo bar | 0.7977 | — | assignment is mostly readable from word overlap alone |

*Caption: forced choice among four candidates, chance 0.25. The balanced column
subsamples to equal events per true instruction; the reader's raw-to-balanced collapse
(0.41 to 0.25) and the echo bar's rise (0.30 to 0.375) move in opposite directions, which
is the signature of the reader riding label frequency while echo rides content. The
problem arm is scored against ASSIGNMENT (realization unverifiable, L139); its
preregistered rule is that only above-bar positives are actionable.*

**Found.** Two clean reads with opposite signs. The reader CANNOT do the thing that is
provably doable: on surface constraints whose satisfaction a string test verifies at
100%, balanced recovery is 0.25 — the zero-shot reader does not check whether text
satisfies a formal constraint, it picks the semantically familiar candidate, and pure
word-echo does better (0.375). And the reader CAN do something echo cannot fully explain:
on problem-pool assignments it clears the echo bar by 11.4 points in the seen family and
10.9 in the held-out family — the margin transfers. What this corpus cannot separate is
realization from assignment-echo inside that margin: the essays' vocabulary leaks the
assignment (echo bar 0.80, exactly the L138 named leak), and whether the reader's 11
points above it track executed choices is precisely the question the 2.1.5 rebuild
exists to answer.

**Means.** Foraging delivered its design constraints. For the rebuild: the reader is a
semantic-correspondence instrument, not a constraint verifier — decoys must be
consequence-matched so semantic correspondence alone cannot separate truth from decoy,
and formal-constraint instructions belong to mechanical scoring, never reader scoring.
Phase 2.1's stacking gate 1 (artifact-only recovery of REALIZED problem-directed choices
above a matched floor) remains unmet — not failed, unmeasurable on this corpus — so
stacking stays gated. Gates 2 and 4 look good in exploratory form (family transfer holds;
fabrication clean); gate 3 is the open contest (11 points above echo, echo at 0.80).

### Curator roll-up

- **Theory group:** Decision Traces
- **Question in plain language:** Reading only the finished essay, can the reader tell
  which instruction was given?
- **Outcome class:** Narrows
- **Result:** Chance on mechanically verified surface constraints once frequency is
  balanced away, but 11 points above the word-echo bar on problem-pool assignments in
  both families.
- **Project meaning:** The reader reads meaning-correspondence, not constraint
  satisfaction; whether its above-echo margin tracks executed choices needs the rebuilt
  corpus, so stacking stays gated on 2.1.5.
- **Next engineering obligation:** The 2.1.5 decisive rebuild with consequence-matched
  decoys and echo equalized by construction.
- **Public claim:** Unchanged (exploratory by declaration).
- **Curator decision required:** No.
- **Detail pointer:** `results/g158/recovery_summary.json`, per-arm partials on disk.

## L141 · The fresh confirmatory lands with every gate quiet: recovery replicates at the new seed, the shuffle arm sits beside its preregistered expectation, and confirmatory grade is earned

**Hypothesis.** *(G129b, `prereg/g129b.py`: the L132 battery re-run under gates carrying
both expectations and a direction from birth, fresh seed 37 — does recovery replicate and
do all gates stay quiet in their guarded directions, earning the confirmatory grade the
first run's voided gate denied?)*

**Method.** Identical construction to G129 (truth-balanced, uniform decoys, k = 4,
Amendment-1 fabrication arm), fresh seed, one-sided gates in the leak direction, the
shuffle arm's alternative expectation (0.125) frozen on the card, and the matched arm's
power handling pre-committed (one caliper relaxation fired at manifest build: matched
200 of the powered 283, so H-B declared at pilot tier before any arm ran).

| arm | read | gate / band |
|---|---|---|
| recovery, full set | **0.4805** | **H-A REPLICATES** (margin 0.2305; L132 read 0.4854 — seed-stable) |
| recovery, matched + balanced | 0.415 | H-B 16.5 points, band SURVIVES, **pilot tier as pre-committed** |
| blind / blind matched | 0.2354 / 0.27 | quiet (one-sided p 0.81 / 0.28) |
| shuffled truth | **0.1136** | quiet (p 1.0 upward); sits beside the card's 0.125 alternative expectation |
| brief / source alone | 0.2468 / 0.3182 | context near floor; topic supplies a little |
| fabrication (200 no-ops) | **0.000** | A7 CLEAN; symmetric control missed 0 of 200 real revisions (accuracy 0.40 with the extra option) |
| reader vs change block | 117 vs 158 exclusive wins | H-C LOSES again (block 0.5471, exact McNemar p = 0.0157) |

*Caption: each row one preregistered arm, chance 0.25 under truth balancing. The gates
void only one-sided in the direction a leak would push. The shuffle read near 0.125 is
the delta-tracking signature predicted on the card, not explained after the fact.*

**Found.** Everything the first battery claimed, now under gates that were specified
before the run: recovery replicates within half a point of L132 at a fresh seed, no gate
fires in its guarded direction, the fabrication bound holds at zero, and the change block
beats the zero-shot reader a second time (seven points, significant), settling that
result as seed-stable too. The shuffle arm's below-chance read — the thing that voided
L132 — landed within a point of the expectation this card carried at freeze.

**Means.** Confirmatory grade is EARNED per the card's preregistered response: the
demotion language lifts, the real-text half of the 2.0D gate is formally met, and the
public claim may say confirmatory with its scope attached (one corpus, one reader family,
matched arm at pilot tier). The representation conclusions are unchanged and now
confirmed twice: delta-interface features build on the change block, the reader supplies
fabrication-bounded abstention, and nothing here licenses artifact-only claims — that
boundary lives in the contract's interface table and stage (c)'s L140.

### Curator roll-up

- **Theory group:** Decision Traces
- **Question in plain language:** Does the choice-recovery result survive a fresh
  confirmatory run whose gates were specified correctly before it ran?
- **Outcome class:** Strengthens
- **Result:** Recovery 0.4805 against the 0.25 analytic floor with every gate quiet and
  fabrication at zero.
- **Project meaning:** The paired-delta recovery claim stands at confirmatory grade; the
  2.0D real-text gate is formally met; the L137 demotion is cured the way it demanded.
- **Next engineering obligation:** The 2.1.5 rebuild (the construct question), then the
  compact decision-feature block under the contract's interfaces.
- **Public claim:** Newly licensed — "confirmatory" with scope (one corpus, one reader
  family; matched arm pilot tier).
- **Curator decision required:** No.
- **Detail pointer:** `results/g129b/verdict.json`, `prereg/g129b.py` (sha256 recorded at
  the lifting commit), all arms and partials on disk.

## L142 · Maker as a random effect: the polish side carries ten times the depth side's author variance, and one arm of my own design voids itself

**Hypothesis.** *(G97, owed since the methods pass: the within-maker positives (the PD-33
family) compare means over windows, pseudo-replicating artifacts within makers. Refit with
author as a random effect — if the effects vanish under proper clustering, we have been
measuring individuals rather than the quantity.)*

**Method.** From the decomposition's own feature cache (1,687 eighty-word windows over 258
essays, 86 authors), every polish and depth feature z-scored over the pool, per-window
side composites formed, and mixed models fit by restricted maximum likelihood with author
random intercepts (author-by-draft as the nested check): the polish composite, the depth
composite, and their difference, each with variance components and intraclass
correlations on disk.

| quantity | polish side | depth side |
|---|---|---|
| author-level variance | **0.0975** | 0.0094 (fit at the boundary) |
| residual (within) variance | 0.2361 | 0.0406 |
| intraclass correlation | **0.2924** | 0.1874 |

*Caption: the intraclass correlation is the share of a composite's variance that lives
between authors — the maker-signature quantity itself. The depth side's author component
sits at the estimation boundary, meaning barely distinguishable from zero.*

**Found.** The maker signature survives the hierarchical form, stated more strongly than
the share decomposition put it: the polish composite carries ten times the author-level
variance of the depth composite, and the depth side's author component is boundary-small.
Who you are lives in the polish channel; the depth channel barely carries identity at
all. One arm of this runner voided itself by my own construction: the fixed-effect
intercept test (is the polish-minus-depth difference nonzero under clustering) is
meaningless after pool z-scoring, which forces the pool mean to zero — its p = 0.87 is an
artifact of the design, not a null, and it is recorded as VOID-BY-CONSTRUCTION rather
than reported as a collapse. The proper carrier of the L57 claim was always the variance
structure, and that is what the refit delivers.

**Means.** The pseudo-replication worry the row was opened for does not overturn the
PD-33 family: the author-signal is in the variance components, which clustering measures
rather than destroys. The L57/L71 rows gain a hierarchical confirmation line. Standing
scope: this cache is the essay corpus; the books corpus refit is the follow-up if ever
needed (its author-topic confound limits what it could add).

### Curator roll-up

- **Theory group:** Decision Traces
- **Question in plain language:** Do the maker-signature results survive giving every
  author their own baseline, or were we measuring individuals?
- **Outcome class:** Strengthens
- **Result:** The polish composite carries ten times the depth composite's author-level
  variance under a mixed model (intraclass correlation 0.29 vs 0.19 at the boundary).
- **Project meaning:** The polish channel carries maker identity; the depth channel
  barely does — the hierarchical form of the standing claim, not a revision of it.
- **Next engineering obligation:** None new; the void intercept arm is disclosed, and
  any future location test must run on unstandardized or anchored scales.
- **Public claim:** Unchanged.
- **Curator decision required:** No.
- **Detail pointer:** `results/g97/maker_effect.json`; cache
  `results/features/argrewrite_w80.json`.

## L143 · Our own Taramsa test: the reader invents a specification on one of ten unspecified texts, and recovers real ones above the trivia bar with a dose that dilutes

**Hypothesis.** *(G94, owed since the methods pass, sharpened by L140: at Taramsa the
standard reconstruction method invented a production stage that never happened. Our
analogue — on the intent ladder, where every artifact's true specifications are known,
does spec-style reconstruction posit decisions that were not there, and can it find the
ones that were?)*

**Method.** Ladder ground truth reconstructed from the generator's deterministic seeds and
join-checked against every item's recorded prompt word count (50 of 50 reproduce) before
any call. Forced choice at k = 4, artifact only: fabrication arm on the ten rung-0 texts
(four spec candidates plus an explicit "none of these was requested"); recovery per true
spec on rungs 1/3/6/10 against same-pool decoys; blind floor and word-echo bar on
identical candidate sets.

| arm | read | meaning |
|---|---|---|
| fabrication (rung 0) | **0.10** (1 of 10) | the reader asserted one spec that was never given; nine honest nones |
| recovery overall | **0.52** | against blind 0.225 and echo 0.40 |
| recovery by rung 1/3/6/10 | 0.50 / 0.77 / 0.53 / **0.44** | falls with dose while the echo bar stays flat (~0.40): dilution, not echo, shapes the curve |

*Caption: chance 0.25 throughout; the echo bar picks the candidate whose words overlap
the text most, no reading involved. n = 10 fabrication events (every rung-0 item), 200
recovery events (every true spec on the specified rungs).*

**Found.** The Taramsa failure exists but is bounded in this format: one invention in ten
at forced-choice-with-none, consistent with the honest-format finding (L140) and nothing
like the yes/no adjudicator's 0.69 over-credit (L139). Recovery of real specifications
clears the trivia bar by 12 points overall — a third substrate for above-echo recovery
after the ArgRewrite deltas and the essay corpora — and the dose curve falls as
specifications multiply while echo stays flat, which is dilution of per-spec trace, not
vocabulary leakage.

**Means.** The reconstruction instrument does not hallucinate freely when given an honest
no-option, and its per-spec signal thins as instruction count rises — both directly
usable by the G159 recovery card (amounts 1 and 4 sit on the informative side of the
curve). Small-n caveat carried: the fabrication arm is ten events; the rung-1 cell is ten.

### Curator roll-up

- **Theory group:** Decision Traces
- **Question in plain language:** Where the true instructions are known, does
  reconstruction invent ones that were never given?
- **Outcome class:** Narrows
- **Result:** One invention in ten unspecified texts, with real-spec recovery 12 points
  above the word-overlap bar and diluting with dose.
- **Project meaning:** The Taramsa worry is real but format-bounded; honest-option forced
  choice keeps fabrication near the L140 rate on a third substrate.
- **Next engineering obligation:** None new; feeds the G159 recovery card's dose choices.
- **Public claim:** Unchanged (exploratory).
- **Curator decision required:** No.
- **Detail pointer:** `results/g94/taramsa.json`, partials on disk, join check in-file.

## L144 · The rebuilt factorial corpus lands and passes its own gate: instructed rewrites execute at 62.5% exact-grade, and the uninstructed twins satisfy the same checks at 28%

**Hypothesis.** *(G159, Phase 2.1.5 generation: 160 rewrites of the twenty recorded
zero-instruction bases — every cell a rewrite of the same base material, with realization
crossed as the intervention: R+ instructed to apply the drawn set, R- the identical
rewrite request with no instructions shown and the set recorded as counterfactual. The
corpus self-gates: R+ exact-grade mechanical realization must clear 0.5 or the G131
defect repeats and nothing proceeds.)*

**Method.** Both families generated at full yield (80 + 80, deterministic seeds recorded,
manifests written), then the mechanical realization audit over every checkable
instruction on both arms.

| audit read | rate | meaning |
|---|---|---|
| R+ exact-grade realization | **0.625** (n = 32) | the gate clears (threshold 0.5); rewrites execute formal instructions better than G131's cold generation (0.586) but far from fully |
| R+ all checkable | 0.628 (n = 78) | consistent across grades |
| R- exact-grade, counterfactual | **0.281** | uninstructed twins spontaneously satisfy the same checks at base rate — the number R+ must be read against |
| R- all checkable, counterfactual | 0.154 | lower once approximate checks join |

*Caption: R+ artifacts were told to apply the instructions; R- artifacts never saw them.
The R- column is the spontaneous-satisfaction floor that makes R+ interpretable.*

**Found.** The corpus stands: realization is verified rather than assumed, the R+/R-
contrast is live (62.5% against a 28% spontaneous floor on identical checks), and the
usable exact-grade event count is honest but thin (20 realized exact-grade R+ events), so
the recovery card's known-answer core is the semantic pool with the R- null arm, with the
formal instructions scored mechanically as the side channel.

**Means.** 2.1.5's corpus obligation is met at $0 and the recovery card is the next
gate-bearing design: forced choice with echo-matched decoys, R+ vs R- as the execution
contrast, R- doubling as the leak gate (any above-chance read on R- is a
candidate-construction leak, direction up, preregistered).

### Curator roll-up

- **Theory group:** Decision Traces
- **Question in plain language:** Did the rebuilt corpus actually execute its
  instructions, unlike the first one?
- **Outcome class:** Infrastructure
- **Result:** Instructed rewrites execute at 62.5% exact-grade against a 28% spontaneous
  floor in their uninstructed twins; the self-gate clears.
- **Project meaning:** The construct test finally has a corpus whose ground truth is
  verified; the execution contrast (instructed vs uninstructed twins) is the design's
  engine.
- **Next engineering obligation:** The G159 recovery card, preregistered, DESIGN CHECK
  from birth.
- **Public claim:** Unchanged.
- **Curator decision required:** No.
- **Detail pointer:** `corpora/g159_rebuild/realization_audit.json`, manifests per family.

## L145 · Matching length and register does not defeat the leakage reference: the trivia detector holds at 0.966

**Hypothesis.** *(2.1.6's first matched cell: L135 read the unmatched pilot at 0.9785 with
nine statics and forty function-word rates — does that number collapse when length and
register are matched by construction, which would mean it was carried by the two most
obvious confounds?)*

**Method.** Machine side G153 thin-prompt essays plus G159 rewrites, human side ArgRewrite
Draft1 essays (register matched by class: argumentative essays both sides), length matched
by equal-count quintile strata inside the shared word-count overlap (88 per side kept,
drops counted), same features and model as L135, GroupKFold by lineage.

| cell | accuracy | AUC |
|---|---|---|
| unmatched pilot (L135) | 0.9785 | 0.9921 |
| length + register matched | **0.9659** | **0.9897** |

*Caption: identical feature list and cross-validation; the only change is the matching.
A collapse here would have licensed length-banding as the main repair; it did not come.*

**Found.** The reference barely moves. Whatever the statics and function words read, it is
not length and it is not register-by-class. The honest suspects on this pilot are quality
and era: polished 2026 model prose against 2016 student drafts with their typos and
disfluencies — precisely the quality axis the contract lists as a matching requirement
and this cell does not control.

**Means.** 2.1.6's priorities reorder on a measurement: quality matching and the
identical-source different-transformation lineages (one source, many process histories)
are the binding repairs; length banding is necessary but nearly worthless alone. Every
benchmark cell keeps this reference's per-cell read as its standing shortcut label, and
no detector number on quality-unmatched cells means anything.

### Curator roll-up

- **Theory group:** Infrastructure (the benchmark)
- **Question in plain language:** Does the cheap-feature detector die when we match text
  length and genre?
- **Outcome class:** Narrows
- **Result:** 0.9659 matched against 0.9785 unmatched — matching the two obvious
  confounds removes almost nothing.
- **Project meaning:** The pilot's shortcut lives in quality and era, so those are what
  the human-negative assembly must match; length bands alone buy nothing.
- **Next engineering obligation:** Quality-matched cells and identical-source lineages in
  the 2.1.6 assembly.
- **Public claim:** Unchanged.
- **Curator decision required:** No.
- **Detail pointer:** `results/g153_pilot/matched_ref.json`; L135's
  `surface_ref.json` beside it.

## L146 · The realized-choice battery lands SUPPORTED: executed instructions leave massive artifact-only evidence in both families, most of it vocabulary-borne, with a thirteen-point reader margin above the word-overlap bar

**Hypothesis.** *(G159, `prereg/g159.py`, frozen before the run — Phase 2.1.5's decisive
study and Phase 2.2A's closure boundary: can the artifact-only reader distinguish verified
executed instructions from uninstructed twins when echo and consequence are controlled?)*

**Method.** Forced choice at k = 4 on the rebuilt corpus: 100 assigned problem
instructions on instructed rewrites (P+) against 100 counterfactual sets on their
uninstructed twins (P−, the leak gate whose expectation is chance under BOTH null and
alternative), echo-matched decoys chosen at construction, blind floor, fabrication arm
with a none option, the surface-mechanical side channel, and the paired-delta arm
reported separately under the interface rule.

| arm | read | meaning |
|---|---|---|
| P+ recovery (artifact only) | **0.86** | llama 0.86, qwen 0.86 — identical in seen and held-out families |
| P− twins (the leak gate) | 0.22 | quiet: nothing executed reads at chance |
| **execution effect (the primary)** | **0.64** (z = 9.1) | band **SUPPORTED** (threshold 0.15) |
| echo bar on P+ | **0.73** | the matching disclosure fired: word overlap alone recovers executed instructions at 0.73 |
| reader margin above echo | **+0.13** | what the reader demonstrably adds beyond vocabulary |
| blind floor | 0.32 (one-sided p 0.069) | inside its gate, elevated; a candidate-popularity prior worth noting |
| paired-delta arm (I2) | 0.83 | the delta does NOT help here — the whole rewrite realizes the instructions, so the final text already carries the evidence |
| fabrication on twins (none option) | **0.40 over-attribution** | far above L140's 0.05 on cold essays: a visibly rewritten text pulls the reader into asserting intent |
| surface-mechanical arm | 0.25 (oracle 1.0, zero wiring defects) | replicates L140 on a second corpus: the reader cannot verify formal constraints that a string test verifies trivially |

*Caption: chance 0.25 throughout. P+ texts were instructed to apply the choice; P− twins
got the identical rewrite request with nothing shown. The echo bar picks the candidate
whose content words overlap the text most.*

**Found.** Realized choices leave artifact-only evidence, decisively: 64 points over the
twin control, transferring perfectly across families, with every preregistered gate quiet
in its guarded direction. The honest cap, disclosed by the card's own rule: most of that
evidence is vocabulary-borne. Executing a semantic instruction embeds its words — the
0.73 echo bar on executed text is not purely a leak, it is partly what execution looks
like — so the demonstrated reader contribution beyond word overlap is thirteen points,
not sixty-four. Three sharp secondary reads: the delta interface adds nothing when the
final artifact already realizes the choices (the ArgRewrite situation inverts); the
reader's fabrication is context-dependent (0.05 on cold essays, 0.40 on visibly rewritten
text — a rewrite invites intent attribution); and the constraint-verification null
replicates on a second corpus.

**Means.** Phase 2.1 closes with its question answered as posed, and per the brief's
routing (2.2 §11.1) the positive licenses continued trajectory recovery, never provenance
attribution. What 2.2's batteries inherit: echo cannot be matched away at this pool size
— it must be decomposed instead (echo-consistent versus echo-independent evidence as
separate reported quantities); fabrication controls must use un-rewritten baselines or
the none option under-reads honesty; formal constraints stay mechanically scored forever.
The thirteen-point above-echo margin, family-stable, is the quantity 2.2C's anomaly
ruler and 2.2E's context conditioning now try to grow or kill.

### Curator roll-up

- **Theory group:** Decision Traces
- **Question in plain language:** Do choices a model actually executed leave evidence in
  the finished text that a reader can find, compared against identical twins where nothing
  was executed?
- **Outcome class:** Strengthens
- **Result:** A 64-point execution effect with all gates quiet, of which 13 points exceed
  what word overlap alone recovers, identically in both model families.
- **Project meaning:** Realized choices are recoverable from final artifacts; the
  recoverable part is largely vocabulary-borne, so the representation program's next job
  is separating echo-consistent from echo-independent evidence.
- **Next engineering obligation:** 2.2C's anomaly-handling ruler (the next evidence
  channel), with echo decomposition folded into every future card.
- **Public claim:** Newly licensed at exploratory-confirmed scope: "verified executed
  instructions are recoverable from the final artifact against matched uninstructed
  controls" — never a provenance claim.
- **Curator decision required:** No.
- **Detail pointer:** `results/g159/verdict.json`, `prereg/g159.py` (sha256 at the landing
  commit), all arms and partials on disk.

## L147 · The anomaly-handling ruler passes all six gates in the constructed world, and its six build iterations are the finding

**Hypothesis.** *(G161, Phase 2.2C: before any natural-text anomaly battery, a
likelihood-grade ruler must prove on known answers that it can abstain on clean walks,
never call unfamiliar order an error, recover every planted handling class, separate
repair from concealment, refuse to read recurrence as intent, and shift with declared
context — the brief's gates, thresholds preregistered in the DESIGN CHECK.)*

**Method.** The BST gridworld machinery (walled world, soft-Bellman policies at the
fitted human rationality) generates seven ground-truth handling classes mechanically:
clean walks, waypoint-ordered detours, wrong turns left unnoticed (open-loop replay),
repaired (backtrack), concealed (closed-loop re-plan), habitual repetition (separated
biased pairs), and the context arm scored with the waypoint withheld and declared. The
ruler is per-step log-probability under the declared account with three detection tiers
(episode-calibrated hard threshold, run detector for sustained mild deviation,
mid-threshold recurrence), then handling classification from post-cluster structure.

| gate | read | threshold |
|---|---|---|
| no-signal (clean walks honest) | 0.98 | ≥ 0.95 |
| unfamiliar order labeled error | 0.000 | ≤ 0.05 |
| known answer, all five planted classes | **1.00 each** | > 1/7 |
| repair-vs-concealment confusion | 0.00 / 0.00 | ≤ 0.20 |
| repeated read as intent | 0.00 | ≤ 0.05 |
| context flip when waypoint declared | 1.00 | ≥ 0.80 |
| **fresh-seed replication** | **all gates pass again** (clean 0.96, classes 1.00) | rules untouched |

*Caption: fifty episodes per class; the verdict is the gate battery, not an aggregate.
The fresh-seed run replicates the pass with the classifier frozen.*

**Found.** RULER-PASSES, replicated on fresh seeds — the 2.2D text battery is licensed.
The six build iterations are recorded in the runner and are the transferable knowledge:
a one-step anomaly cannot be honestly separated from a rational walker's own softmax
noise, so real anomalies are categorical multi-step objects (a wrong turn, not a
stumble — in text, a span, not a word); an anomaly-free world makes handling classes
collapse (consequence structure, the wall and door, is what separates open-loop drift
from re-planning); detection thresholds must be episode-calibrated on a disjoint null or
the false-anomaly rate is structural; recurrence must require separated clusters or
every wrong turn reads as habit; and handling evidence begins after the anomaly
cluster ends, not after its first step.

**Means.** 2.2C is met in construction and 2.2D unlocks: the text battery's families now
inherit five measured design constraints. The scope boundary stands as the brief's
pre-mortem demands: a constructed-world pass validates the ruler and the feasibility
regime, never human cognition.

### Curator roll-up

- **Theory group:** Reader Heuristics (instrument) / Decision Traces (the trace classes)
- **Question in plain language:** Can a likelihood ruler tell repaired from concealed
  from unnoticed from habitual from merely-unfamiliar, where the truth is planted?
- **Outcome class:** Strengthens
- **Result:** All six preregistered gates pass at fifty episodes per class and replicate
  on fresh seeds.
- **Project meaning:** Error handling graduates from intuition to a validated instrument
  in construction; the natural-text port is licensed and inherits the iteration lessons.
- **Next engineering obligation:** The 2.2D process-recorded text battery's corpus
  design (careful pass, not rushed — the G131 lesson governs).
- **Public claim:** Unchanged (constructed world only).
- **Curator decision required:** No.
- **Detail pointer:** `results/g161/ruler.json`, `results/g161_freshseed/ruler.json`,
  the iteration record in `runners/run_g161_ruler.py`.

## L148 · The echo decomposition overturns L146's cap: where word overlap points wrong, the reader still recovers executed instructions at 0.85

**Hypothesis.** *(The decomposition L146 made mandatory: is the P+ recovery
word-overlap in disguise? Split every P+ event by whether the echo pick agrees with the
truth; reader accuracy on the echo-wrong subset is recovery that word overlap cannot
explain.)*

**Method.** Pure re-scoring of the recorded G159 arms, no new reader calls: per event,
the echo pick is the candidate with maximum content-word overlap with the text; events
split into echo-right and echo-wrong cells, the twins re-scored on the same split as the
baseline.

| cell | P+ reader | twins baseline |
|---|---|---|
| echo-right (n = 73 / 32) | 0.863 | 0.219 |
| **echo-wrong (n = 27 / 68)** | **0.852** | 0.221 |

*Caption: chance 0.25. On echo-wrong events the word-overlap heuristic actively points
at a decoy; the reader finds the executed instruction anyway.*

**Found.** The reader's recovery is not word-matching. Where echo misleads, accuracy is
statistically unchanged (0.852 against 0.863), while the twins sit at chance in both
cells. L146's thirteen-point above-echo margin was the aggregate floor of the story: the
correct reading is that the reader's evidence is echo-independent semantic realization,
which happens to correlate with echo in aggregate because executing an instruction
usually embeds its words.

**Means.** The honest cap on L146 lifts into a sharper claim: artifact-only recovery of
executed choices survives the strongest cheap-feature challenge the corpus can pose.
Stacking gate 3 (cheap baselines do not explain the effect) now looks passed in
exploratory form on this corpus; gates 1 and 2 already behaved; gate 4's abstention
evidence stands at L140/L143's rates. The 2.2 batteries inherit the split as a standing
report: every recovery table carries echo-right and echo-wrong cells from now on.

### Curator roll-up

- **Theory group:** Decision Traces
- **Question in plain language:** Is the recovery result just word matching?
- **Outcome class:** Strengthens
- **Result:** Reader accuracy 0.852 on the events where word overlap points at the
  wrong answer, against 0.22 in the uninstructed twins.
- **Project meaning:** The realized-choice evidence is semantic, not lexical; the
  detector-facing stacking gates are now three-quarters green in exploratory form.
- **Next engineering obligation:** Echo-split cells become a standing column in every
  2.2 recovery report.
- **Public claim:** Strengthened within the existing scope wording.
- **Curator decision required:** No.
- **Detail pointer:** `results/g159/echo_decomp.json`.

## L149 · The anomaly-text corpus stands: planted issues land at 0.75 to 0.95, correction markers separate the families perfectly, and the clean family is uncontaminated

**Hypothesis.** *(G162 generation self-gate, the L137 rule applied before use: did the
instructed handling families actually realize their mechanically decidable halves —
issue presence, correction, repetition, refrain — or does the G131 failure repeat?)*

**Method.** 120 rewrites of the recorded bases (six families × two generators × ten
topics), each planting a token-verifiable invented study figure per its family's
handling instruction; string audit over every artifact.

| audit read | rate | gate |
|---|---|---|
| planted-issue presence (four planted families) | 0.75 / 0.75 / 0.90 / 0.95 | ≥ 0.6 each |
| clean-family contamination | **0.00** | ≤ 0.05 |
| corrected family carries the true value | 0.75 | ≥ 0.6 |
| concealed / unnoticed carry the true value | **0.00 / 0.00** | ≤ 0.1 |
| repeated at three-plus occurrences | 0.90 | ≥ 0.6 |
| deliberate refrain at three-plus | 0.85 | ≥ 0.6 |

*Caption: every value is a string test against the recorded planted tokens; the
concealed/unnoticed mechanical identity is by design — their separation is the reading
battery's question, never assumed ground truth.*

**Found.** CORPUS-STANDS on all six gates. The correction-marker separation is the
important one: told to correct, the generator corrects (0.75); told to conceal or leave
unnoticed, it never corrects (0.00 both) — the families did not collapse.

**Means.** The 2.2D reading battery is preregistered on it same pass (`prereg/g162.py`):
validation-first order (the reader validates on 360 negative-heavy decidable questions
BEFORE its semantic verdicts are interpreted — the L139 lesson in the right order this
time), and the primary quantity is the one thing mechanics cannot decide, artifact-only
concealed-versus-unnoticed separation. Battery queued.

### Curator roll-up

- **Theory group:** Infrastructure (Decision Traces' corpus)
- **Question in plain language:** Did the error-handling corpus actually do what its
  instructions asked, where we can check?
- **Outcome class:** Infrastructure
- **Result:** All six self-gates pass, with correction markers at 0.75 where instructed
  and 0.00 where forbidden.
- **Project meaning:** The first process-recorded text corpus with verified handling
  ground truth; the reading battery runs tonight.
- **Next engineering obligation:** Land G162-R's verdict through the loop.
- **Public claim:** Unchanged.
- **Curator decision required:** No.
- **Detail pointer:** `corpora/g162_anomaly/handling_audit.json`, `prereg/g162.py`.

## L150 · The handling reader is honest and blind: validation passes at 0.95, and concealment does not separate from non-recognition in text at this grain, on either interface

**Hypothesis.** *(G162-R, `prereg/g162.py`, frozen before the run: can a reader separate
a concealed error from an unnoticed one — the one distinction the corpus deliberately
cannot decide mechanically — from the final artifact, with the paired-delta arm reported
separately and a validation-first gate deciding whether any semantic verdict is
interpretable at all?)*

**Method.** 120 artifacts, six families, forced choice over handling descriptions plus an
explicit cannot-tell; 360 negative-heavy mechanically decidable questions as the V gate;
context-only floor; both interfaces; verdict scored once.

| read | value | meaning |
|---|---|---|
| V gate (decidable questions) | **0.95 accuracy, 0.054 false-yes on 260 negatives** | PASSES — the instrument is honest in this format, so the nulls below are nulls of signal, not of the reader |
| **primary: concealed vs unnoticed, artifact only** | **0.417** on 24 committed of 40 | **BLIND** (chance 0.5) |
| the same pair, paired delta | 0.571 on 35 committed | noise-compatible at this n; not a positive |
| corrected family, artifact only | 0.90 | the reader reads explicit corrections — the mechanically decidable case |
| deliberate family, artifact only | 0.05 (read as clean at 0.60) | the purposeful refrain is invisible as purpose |
| clean-family fabrication | 0.30 | above the 0.15 band; the L146 rewritten-text over-attribution replicates at 0.30 |
| context-only floor | 0.008 | label-marginal behavior, no leak |

*Caption: committed means the reader chose one of the pair's two labels rather than a
third class; the pair accuracy is scored on those. The V gate ran first by prereg and
its pass is what licenses interpreting everything else.*

**Found.** The preregistered response tree's harshest branch executes, stated without
softening: the reader cannot read error handling at this grain, on either interface. A
concealed error — recognition expressed as quiet reframing — does not separate from
simple non-recognition in a 400-word essay, artifact-only OR with the original text
beside it. The validation gate is what makes this a finding rather than an instrument
failure: the same reader in the same format answers decidable questions at 0.95 with a
5% false-yes rate, so the signal is absent or below this resolution, not misread. Two
sharp secondaries: an explicitly deliberate construction reads as nothing (the
unfamiliar-order hazard's text form, direction as the pre-mortem predicted), and
rewritten clean text pulls over-attribution at 0.30, replicating L146's context effect.

**Means.** Per the card: the anomaly channel narrows to the constructed world, and the
ruler's license does not extend to text at this resolution. The redesign directions the
null itself names (owed as designs, not promises): span-level asking (WHERE is the
handling, not WHICH class — the hedging in these essays is a single clause a
whole-artifact question dilutes), longer artifacts where handling has room to leave
structure, and richer concealment instructions audited for realized hedging density.
The trace-class ontology stands (its constructed-world instrument is validated); its
text feasibility at essay grain is now measured at no.

### Curator roll-up

- **Theory group:** Reader Heuristics / Decision Traces
- **Question in plain language:** Can the reader tell a covered-up error from an
  unnoticed one in a short essay?
- **Outcome class:** Narrows
- **Result:** Blind at 0.417 against 0.5 chance on the committed pair, with the
  validation gate passing at 0.95 — an honest instrument finding no signal.
- **Project meaning:** Error-handling recovery is real in construction and unmeasurable
  in short text at current resolution; the channel needs span-level or longer-form
  redesign before it can feed the Triple Inference on text.
- **Next engineering obligation:** The span-level redesign of the text form; 2.2E
  context conditioning proceeds on the channels that DO read (realization, correction).
- **Public claim:** Unchanged (nothing was claimable here yet).
- **Curator decision required:** No.
- **Detail pointer:** `results/g162/verdict.json`, `prereg/g162.py` (sha256 at this
  commit), all partials on disk.

## L151 · Explicit route generation adds exactly nothing where direct reading is strong: the first Phase 2.3 root lands NO-GAIN on both arms with every gate quiet

**Hypothesis.** *(G165, Phase 2.3 Wing G root, `prereg/g165.py`, frozen before the run:
does a reader that first GENERATES process structure — its own production route for the
essay, or predicted evidence for each candidate instruction — recover recorded executed
choices better than the same reader reading directly? The project's central untested
assumption is that readers model the generating process; this is its cheapest honest
form, run on the events where direct reading is already validated.)*

**Method.** The frozen realized-choice event set (100 events, verified executed
instructions, echo-matched decoys), with the recorded direct arm (0.86) and context-only
floor (0.32) reused as paired baselines at temperature zero. Two new arms: self-route
(the reader writes three production decisions it would have made, candidate-blind, then
classifies with its own route in context) and candidate-and-discriminate (the reader
predicts each candidate's visible evidence, essay-blind and cached, then classifies with
the predictions beside the candidates). Both arms also ran on a seeded 50-event
subsample of the twins where nothing was executed, as the leak gate. Paired exact
McNemar against the recorded direct picks on identical events.

| arm | accuracy | delta vs direct | McNemar p | band |
|---|---|---|---|---|
| direct (recorded anchor) | 0.86 | — | — | — |
| **self-route** | **0.86** | **0.000** (3 vs 3 discordant) | 1.0 | **NO-GAIN** |
| **candidate-and-discriminate** | **0.84** | **−0.020** (6 vs 8) | 0.79 | **NO-GAIN** |
| self-route on twins (leak gate) | 0.24 | vs 0.25 floor | 0.62 one-sided | quiet |
| candidate-discriminate on twins | 0.22 | vs 0.25 floor | 0.74 one-sided | quiet |

*Caption: delta is the new arm's accuracy minus the recorded direct arm's on the same
100 events; discordant counts are events where exactly one of the pair was right.
The leak gates ask whether generated routes recover instructions that were never
executed, which would mean construction leakage; both sit at or below chance. The
pipeline-purity gate (prompts byte-identical under permuted hidden metadata) passed
before any arm ran. Echo-split cells per the standing L148 rule: recovery where the
generated text's word overlap points at the WRONG candidate is 0.87 (self-route) and
0.83 (candidate-discriminate) — indistinguishable from the echo-right cells, so the
generation stage adds no vocabulary shortcut either.*

**Found.** Explicit generation contributes nothing on this substrate, in either
direction: not a point of accuracy, not a leak, not an echo artifact, not a fabrication
channel. The discordant counts are tiny and symmetric (three-and-three,
six-and-eight), which is what "the same instrument with extra steps" looks like. The
0.80-power detectable delta at this n is roughly ten points, so small gains inside
that window are not excluded; a gain worth building a stage around is.

**Means.** ROOT-NULL under the card's exhaustive bands, with the ceiling passed — so
the single predeclared discriminator executes and nothing else: the same ablation on
the delta event set where the cheap change block beats the direct reader by seven
points (0.5471 against 0.4805, L141). That is the substrate where generation has
something to add if it adds anything; if it is null there too, Wing G narrows to
"direct reading is this reader's best form" and the brief's own cheap-baseline routing
row stands. No prompt search follows a null by card.

### Curator roll-up

- **Theory group:** Reader Heuristics
- **Question in plain language:** Does making the reader spell out how the essay could
  have been made help it recover what was actually done?
- **Outcome class:** Narrows
- **Result:** No gain on either generation arm (0.86 against 0.86 direct), all gates
  quiet.
- **Project meaning:** Where direct reading is already strong, an explicit
  self-simulation stage is redundant; whether it helps where direct reading is WEAK is
  exactly the predeclared follow-up now queued.
- **Next engineering obligation:** The discriminator on the revision-delta events (the
  change-block gap substrate), already built and queued.
- **Public claim:** Unchanged.
- **Curator decision required:** No.
- **Detail pointer:** `results/g165/verdict.json`, `prereg/g165.py`, all partials on
  disk.

## L152 · The route-varied corpus stands at full yield: five recorded production routes to surface-matched essays, both families, every gate green

**Hypothesis.** *(G166, Phase 2.3 Wing B construction: can five distinct recorded
production routes — direct composition, outline-then-realize, rewrite-of-recorded-draft,
propose-then-seeded-select, draft-critique-revise — produce surface-matched essays on
identical briefs, with the full route logged as schema-validated process events, so the
equifinality root can ask whether any reader separates routes from final artifacts?)*

**Method.** Ten topics × five routes × two generator families, identical briefs,
register, and length band; every intermediate (outlines, thesis candidates, seeded
selections with recorded rejections, critiques, base drafts) logged as ProcessEvents
under the new schema; self-audit with four gates, each derived with null and alternative
before generation.

| gate | result | meaning |
|---|---|---|
| yield | **100 of 100** | full yield, both families, no manifest withheld |
| length band | 0 violations | every essay inside 300 to 700 words |
| route-log completeness | 0 violations | every case carries its route's required operations and validates under the schema |
| cross-route degeneracy | 0 pairs over 0.90 overlap | no route collapsed into another; equifinality is a real question here |
| surface report | route means 508 to 545 words | within seven percent of each other; the battery's surface baseline decides whether anything cheap separates them |

*Caption: degeneracy is content-word Jaccard between essays of different routes on the
same topic and family; a high value would mean two routes produced near-identical text
and the reading question would be trivial. The surface report is descriptive only; the
binding surface-matched baseline runs inside the reading battery.*

**Found.** CORPUS-STANDS. The construction did what the brief requires: the same topic
reached five ways, with the differences living in the recorded process rather than in
gross surface properties.

**Means.** The B0-near reading battery is licensed and its card freezes now (the
G162 precedent: corpus first, card only on CORPUS-STANDS): artifact-only route
recovery against chance and against a mechanical surface baseline, a process-aware
ceiling gating interpretation, per-route confusion never aggregate, and the
exact-equivalence discipline carried by the pipeline gate.

### Curator roll-up

- **Theory group:** Decision Traces (construction infrastructure)
- **Question in plain language:** Do we now have essays where we know exactly which of
  five production routes made each one, without the routes being tellable apart by
  cheap surface features?
- **Outcome class:** Infrastructure
- **Result:** One hundred of one hundred artifacts at full yield with all four
  self-gates green.
- **Project meaning:** The equifinality question — can a reader recover HOW a text was
  made when several ways were possible — is now askable on known answers.
- **Next engineering obligation:** The reading battery (card frozen this pass, arms
  queued).
- **Public claim:** Unchanged.
- **Curator decision required:** No.
- **Detail pointer:** `corpora/g166_routes/routes_audit.json`, both manifests, every
  route log on disk.

## L153 · The discriminator closes Wing G, and it closes it downward: self-route generation actively hurts where direct reading is weak, and induces fabrication the direct reader never showed

**Hypothesis.** *(G165-D, `prereg/g165d.py`, frozen before the run — the single
predeclared follow-up of L151's root null: on the revision-delta events where the cheap
change block beats the direct reader by seven points, does explicit route generation
contribute the missing representation, or is it rhetoric?)*

**Method.** The frozen revision event set (616 events, recorded delta-interface direct
arm 0.4805 as the paired baseline; the change block's 0.5471 as the reported
reference), same two generation arms as the root, plus the new stage's own fabrication
gate: self-route on the 200 recorded no-revision events with the explicit no-revision
option, where the direct reader's recorded rate is 0.000 twice.

| arm | accuracy | delta vs direct | McNemar p | band |
|---|---|---|---|---|
| direct (recorded anchor) | 0.4805 | — | — | — |
| change block (reference) | 0.5471 | +0.067 | — | the instrument to beat |
| **self-route** | **0.4075** | **−0.073** (61 vs 106 discordant) | **0.0006** | **HURTS** |
| **candidate-and-discriminate** | 0.5114 | +0.031 | 0.16 | NO-GAIN |
| self-route fabrication on unrevised text | 0.065 | vs 0.000 direct | — | WARNING band |

*Caption: discordant counts are events exactly one arm got right; the fabrication rate
is how often the route-generating reader invented a revision purpose on text where no
revision was made, against the same reader's recorded zero without the generation
stage. The pipeline-purity and anchor gates passed before any arm ran.*

**Found.** The self-simulation stage is not neutral where the task is hard — it is
harmful, seven points down at p = 0.0006, and it manufactures purposes on unrevised
text at 6.5 percent where the direct form invented none. The reader talks itself out
of right answers: it writes a plausible route, then follows its own rhetoric over the
evidence. Candidate-evidence prediction is the interesting near-miss: plus three
points, closing most of the gap to the change block (0.5114 against 0.5471) but below
both the band threshold and significance, so it lands NO-GAIN with the direction
noted.

**Means.** Wing G closes, per the card, with the sharper sentence: direct reading is
this reader's best form; explicit self-simulation adds nothing where reading is strong
and actively damages where it is weak, which is the brief's "cognitive preemption by
rhetoric" routing row measured rather than feared. The theory consequence is a bound
on STRATEGY, not on the self-model prior: whatever implicit self-anchoring the direct
reader does, externalizing it into generated prose makes the bounded reader worse. The
fabrication finding travels: any future reader stage that generates before judging
owes its own fabrication gate, because generation induces invention the same reader
does not otherwise commit. The null-discriminator rule is spent; no further Wing G
work exists on this card or its parent.

### Curator roll-up

- **Theory group:** Reader Heuristics
- **Question in plain language:** When reading is hard, does making the reader spell
  out how it would have done the revision help it see what was done?
- **Outcome class:** Kills
- **Result:** Self-route generation costs seven points (p 0.0006) and invents purposes
  on unrevised text at 6.5 percent where the direct reader invented none.
- **Project meaning:** The explicit self-simulation stage is retired phase-wide; the
  reader's value is direct reading plus calibrated refusal, and the change-feature
  block remains the best instrument on the delta interface.
- **Next engineering obligation:** None on this wing — it is closed; the fabrication
  gate becomes standard for any future generate-then-judge stage.
- **Public claim:** Unchanged.
- **Curator decision required:** No.
- **Detail pointer:** `results/g165d/verdict.json`, `prereg/g165d.py`, all partials on
  disk.

## L154 · The equifinality root: the reader abstains on route identity almost completely while cheap surface features read it at 0.48 — final artifacts are semantically silent and statistically loud about how they were made

**Hypothesis.** *(G166-R, `prereg/g166.py`, frozen on CORPUS-STANDS: when five
recorded production routes reach surface-matched essays, can a reader recover WHICH
route made an essay from the final artifact — and is whatever it recovers process
evidence rather than a surface tell?)*

**Method.** 100 artifacts, five routes, forced choice over route descriptions plus an
explicit cannot-tell; the process-aware ceiling (essay plus recorded intermediates)
gating interpretation validation-first; context-only floor; the mechanical
nearest-centroid surface baseline on five cheap features, leave-one-topic-out; verdict
scored once.

| read | value | meaning |
|---|---|---|
| P ceiling (records shown) | **0.78** | PASSES — the route taxonomy is answerable when the record is visible, so the null below is of signal, not of the reader |
| **primary: artifact only** | **0.07**, cannot-tell chosen 0.70 to 0.85 per route | **BLIND** — the reader declines the question almost everywhere |
| surface baseline | **0.48** vs 0.2 chance | five cheap features (length, sentence shape, type-token, paragraphs, first person) read route identity far above chance |
| context-only floor | 0.00 | no leak; the blind reader also abstains |

*Caption: the primary counts a route correct only when the reader committed to it; the
abstention option is what makes 0.07 honest rather than broken. The surface baseline is
mechanical and disclosed; the card's bands required the reader to beat it before any
process-reading claim.*

**Found.** The preregistered BLIND branch executes with its most interesting possible
shape. The semantic reader, shown a finished essay, says it cannot tell how the essay
was produced — at 70 to 85 percent abstention per route — and it is RIGHT to be
humble about the semantic question while being beaten four-to-one by a
nearest-centroid on paragraph counts. Route identity survives in the artifact as
statistical residue (production routes bend surface shape: outlines leave structure,
critique-revision leaves length and person shifts) but not as semantically readable
process structure at this reader and grain. The process-aware arm at 0.78 confirms
the question is well-posed when the record exists.

**Means.** Per the card: final artifacts do not carry semantically readable route
identity at this construction — the W4 boundary lands its first measured instance
(process records auditable at 0.78, artifacts silent at 0.07), and the artifact-only
equifinality claim narrows to the audit interface, stated without softening. The
surface residue is the live thread the card did not anticipate in this strength: a
mechanical instrument reads production route at 0.48 five-way, which is a
trace-existence result — the routes DO mark their artifacts — and the open question
becomes whether that marking is route structure or generation-style covariates
(paragraphing habits per prompt form), which is exactly a trace-erasure or
covariate-matching follow-up shaped like the brief's B1. The reader's mass abstention
is also the observational-equivalence prediction behaving: where histories genuinely
underdetermine, the calibrated output is the equivalence class, and this reader
chose it unprompted.

### Curator roll-up

- **Theory group:** Decision Traces / The Triple Inference
- **Question in plain language:** Can anything tell, from a finished essay alone,
  which of five ways it was written?
- **Outcome class:** Narrows
- **Result:** The semantic reader abstains (0.07 committed-correct) while a
  five-feature mechanical baseline reads route at 0.48 against 0.2 chance, with the
  process-aware ceiling passing at 0.78.
- **Project meaning:** Route identity is a statistical trace, not a readable story:
  process auditing needs records, and whatever surface residue routes leave needs a
  trace-erasure test before it counts as process evidence.
- **Next engineering obligation:** The B1-shaped follow-up (does the surface residue
  survive trace erasure or covariate matching), to be designed as its own card.
- **Public claim:** Unchanged.
- **Curator decision required:** No.
- **Detail pointer:** `results/g166/verdict.json`, `prereg/g166.py`, per-route
  confusion on disk.

## L155 · Context is an instruction to this reader, not evidence: a false production fact steers exactly as hard as a true one, wiping out the abstention that made L154 look calibrated

**Hypothesis.** *(G167, Phase 2.3 Wing A root, `prereg/g167.py`, frozen before the run:
does a true production-context card — a feasibility fact that narrows five routes to
two or three without naming one — move the route reading toward the truth, where a
false card must not? The curator's reweighting model says context shifts the
distribution over maker models; the rival is the brief's W3, suggestion that steers
regardless of truth.)*

**Method.** The route corpus with the recorded no-card reading as baseline; three arms
of 100: the true draft-availability card, the false one (draft claimed where none
existed and vice versa), and an irrelevant card; movement measured as committed
probability mass on the card-compatible route subset, with the card-leak audit
(no shared content words with any route description) and pipeline purity passed
before any arm.

| read | value | meaning |
|---|---|---|
| no card (recorded) | committed 0.22, compatible mass 0.16 | the L154 abstention baseline |
| irrelevant card | committed 0.26 | stable — mere card presence changes little |
| **true card** | committed **0.82**, compatible mass **0.82** (movement +0.66) | the feasibility claim obliterates abstention |
| **false card** | committed 0.70, wrong-subset mass **0.69** (movement +0.63) | **the false card steers 95 percent as hard as the true one** |

*Caption: committed means the reader chose a route rather than cannot-tell; compatible
mass is the fraction of ALL events where it committed to a route consistent with the
card's claim. The movement floor for a real effect was 0.15; both cards moved four
times that, in their own directions, regardless of truth.*

**Found.** PROJECTION, the card's named rival, by its harshest margin. A stated
production fact does not reweight this reader's route posterior — it overwrites it.
The same reader that honestly abstained at 78 percent with no card commits at 82
percent the moment any feasibility claim appears, and it commits to whatever the
claim licenses, true or false, at statistically indistinguishable strength (0.66
against 0.63). The irrelevant-card arm proves it is the claim's CONTENT doing this,
not the presence of a context block. The true-card accuracy of 0.34 is subset
narrowing arithmetic, not artifact evidence.

**Means.** The Wing A root routes to W3: context-conditioned projection. For this
reader at this grain, declared context functions as an instruction, which is exactly
the failure the curator's reweighting quote warns against reading as inference. The
predeclared single follow-up (A5, the evidence-conflict test) is the right next
question and now has a sharp form: L154 showed route evidence is unreadable, which is
WHY suggestion meets no resistance — so A5 runs where artifact evidence is
demonstrably strong (the realized-choice events, direct reading 0.86) and asks
whether a false production note can override evidence the reader provably reads.
After A5 the wing pauses per the brief's W3 row. One theory-side note for the
curator's pass rather than a unilateral edit: the communicative-assumption hazard
(confident inference from structure placed to mislead) now has a measured
reader-model instance — supplied context is trusted absolutely, which is a
trust-calibration gap, not an inference gap.

### Curator roll-up

- **Theory group:** Reader Heuristics
- **Question in plain language:** When we tell the reader a fact about how a text was
  made, does it weigh that fact against the text, or just obey it?
- **Outcome class:** Narrows
- **Result:** A false production fact moves the reader's answers 95 percent as much
  as a true one (movements 0.63 against 0.66 in opposite directions), erasing its
  own abstention both times.
- **Project meaning:** Context conditioning on this reader is suggestion, not
  evidence integration; every context-bearing design in the phase must treat
  supplied context as an override channel until the evidence-conflict test says
  otherwise.
- **Next engineering obligation:** The A5 evidence-conflict battery on the
  realized-choice substrate (built and queued this pass); the wing pauses after it.
- **Public claim:** Unchanged.
- **Curator decision required:** No.
- **Detail pointer:** `results/g167/verdict.json`, `prereg/g167.py`, all partials on
  disk.

## L156 · The hedging-density gate fires on its first corpus: the long-form construction refused itself before a battery could repeat L150

**Hypothesis.** *(G169 construction audit: does instructed long-form concealment
actually realize its plant and its hedging?)*

**Method.** The four-family long-form corpus (78 of 80 generated, both families) against
the preregistered audit gates, hedging measured mechanically after each planted claim.

**Found.** CORPUS-REFUSED, on two gates. The generator conceals by OMISSION — the
planted figure never lands in 37 percent of concealment essays (presence 0.63 against
the 0.75 floor) — and where it does land, realized hedging averages 2.67 post-plant
hedges against the 3.0 floor (the 1.77x ratio over unnoticed passes). Yield and length
were clean. This is exactly the failure that made L150 blind, caught at the corpus gate
for the price of an audit instead of a battery.

**Means.** The one recorded repair pass runs now: regenerate only the accept-failing
artifacts with the family criteria verified mechanically AT GENERATION (plant present,
correction present or absent as instructed, three-plus realized hedges for
concealment), four tries at offset seeds. If the v2 audit refuses too, the long-form
substrate waits for the curator — no further tuning. The transferable lesson lands in
LESSONS §3 territory: an instructed-handling corpus verifies REALIZED handling at
accept time, not at audit time, because audit-time discovery costs a regeneration
pass.

**Outcome of the repair (same day).** v2 CORPUS-STANDS on every gate with room: 80 of
80 at full yield, plant presence 0.95 to 1.0, corrections 0.95 where instructed and
0.00 where forbidden, and realized concealment hedging at 3.79 post-plant markers,
2.3 times the unnoticed rate. Accept-time verification closed the whole defect class
in one pass; the span-level battery preregisters on this audit.

### Curator roll-up

- **Theory group:** Decision Traces (construction infrastructure)
- **Question in plain language:** Did the longer essays actually contain the planted
  error and the quiet cover-up we asked for?
- **Outcome class:** Infrastructure
- **Result:** Refused — the planted figure is missing from 37 percent of concealment
  essays and realized hedging sits just under its floor.
- **Project meaning:** The gate built from L150's post-mortem caught the same defect
  pre-battery; the repair with accept-time verification is queued and is the corpus's
  one allowed regeneration.
- **Next engineering obligation:** The v2 audit; the span-level battery preregisters
  only if it stands.
- **Public claim:** Unchanged.
- **Curator decision required:** No.
- **Detail pointer:** `corpora/g169_longform/longform_audit.json`.

## L157 · Evidence pulls the reader back to a coin flip, no further: a false note costs half the readable-evidence performance, and the reader almost never names the conflict

**Hypothesis.** *(G167-A5, `prereg/g167a5.py`, frozen on L155's PROJECTION — the Wing A
root's single follow-up: can a false production note override artifact evidence the
reader provably reads? The realized-choice events are the substrate: direct instruction
recovery 0.86, echo-independent.)*

**Method.** Three arms of 100 on the frozen realized-choice events: an explicitly
unverified note naming the TRUE instruction (sanity), the same note naming a seeded
decoy (primary, forced choice), and the false note with an added "the note does not
match the essay" option (can it NAME the conflict?).

| arm | accuracy on the truth | note following | meaning |
|---|---|---|---|
| direct, recorded | 0.86 | — | the evidence anchor |
| true note | **0.99** | — | agreement is additive: the note even fixes the reader's own errors |
| **false note, forced choice** | **0.44** | **0.53** | the note wins about as often as the evidence |
| false note with conflict flag | 0.36 | 0.48 | flag used **0.15**; the option does not rescue it |

*Caption: note following is the rate of picking exactly the instruction the false note
named. The card's bands: EVIDENCE-HOLDS at 0.70 and above, SUGGESTIBLE at 0.40 and
below; 0.44 lands MIXED, stated with the number.*

**Found.** MIXED, four points above the suggestible line. Where L155's reader followed
a false claim almost absolutely because it could read nothing to resist with, readable
evidence buys back only half the loss: the false note still costs forty-two points and
wins the toss-up more often than not. The true-note ceiling at 0.99 sharpens the
diagnosis — the reader treats any supplied note as high-grade evidence, which HELPS
when the note is true and poisons when it is false. And offered an explicit way to say
"these disagree," it says so fifteen percent of the time while silently resolving the
rest.

**Means.** Wing A pauses, per the card, in every branch — with the measured trade
curve as the record: supplied context is worth roughly one direct-reading's weight to
this reader regardless of its truth. The product guidance that survives the pause:
context may enter a reading only labeled as untrusted AND only where the interface can
audit it against records, because the reader will not police it; and any calibration
story for this reader family must treat context-trust as a separate defect from
evidence-reading, since the same instrument that is honest about its own uncertainty
(L154's abstention) is credulous about supplied assertions. Lifting the pause is a
curator decision at the root map.

### Curator roll-up

- **Theory group:** Reader Heuristics
- **Question in plain language:** If we tell the reader something false about how a
  text was made, can what it reads in the text itself win?
- **Outcome class:** Narrows
- **Result:** Half-wins: accuracy falls from 0.86 to 0.44 under a false note, and the
  reader names the conflict only 15 percent of the time when given the option.
- **Project meaning:** Context is a trust hole in this reader family — useful when
  true, uncorrected when false; every context-bearing interface treats supplied
  context as an override channel until a reader passes this test.
- **Next engineering obligation:** None — the wing is paused by design; the result
  feeds the Stage-1 root map.
- **Public claim:** Unchanged.
- **Curator decision required:** Not yet; the root map carries the pause-lift
  question.
- **Detail pointer:** `results/g167a5/verdict.json`, `prereg/g167a5.py`.

## L158 · The L150 wall falls at long form: the reader separates concealed from unnoticed at 0.77 — and cannot point at the sentence that told it

**Hypothesis.** *(G169-R, `prereg/g169r.py`, frozen on the v2 CORPUS-STANDS — the
L150-owed redesign run: on long-form artifacts whose concealment verifiably realizes
hedging, does the reader separate concealed from unnoticed where essay grain was
blind, and can it LOCATE the handling?)*

**Method.** 80 long-form artifacts (900 to 1300 words), validation-first (160
mechanically decidable questions, negative-heavy), the whole-artifact classification
arm in L150's exact question form, the span-locate arm (quote the clearest handling
sentence, verified verbatim and scored mechanically for post-plant hedging), and the
disclosed mechanical baseline (post-plant hedge count, leave-one-topic-out).

| read | value | meaning |
|---|---|---|
| V gate | **0.9938, false-yes 0.0122** | the instrument is honest at long form too |
| **primary: concealed vs unnoticed, whole artifact** | **0.7692** on 39 committed of 40 | **SEPARATES** (L150 essay-grain reference: 0.417, blind) |
| mechanical hedge baseline | 0.7949 held-out | parity: the reader matches, does not beat, the five-line instrument |
| **span-locate hit rate on concealed** | **0.00** (fabricated spans 0.128, interpreted) | the reader cannot quote the hedged sentence under the preregistered hit rule |
| clean fabrication | 0.40 | the recorded L146 worst case replicates exactly; the standing warning label |

*Caption: committed means the reader chose one of the pair's labels; a span hit
requires a verbatim post-plant quote containing a hedge marker. The card separated
two claims at freeze: separability-at-all (mechanical) and reader-adds-semantics.*

**Found.** Three faces, all clean under a near-perfect validation gate. First: the
channel reopens — the same reader that was blind at 0.417 on short essays separates
the pair at 0.77 on long ones, so L150's wall was RESOLUTION, exactly as its afterword
framed and hoped. Second: the reader adds no measured semantics over the mechanical
instrument — hedge-counting alone does 0.79 — and, strikingly, it classifies the
whole artifact correctly while completely failing to QUOTE the sentence that carries
the signal (hit rate zero under the mechanical rule; it either declines or quotes
unhedged material). Classification without localization: the reader integrates a
diffuse density it cannot point at. Third: clean long-form rewrites pull 0.40
invented issues, the L146 recorded risk at full strength, so every positive here
carries that fabrication rate as its warning label.

**Means.** Per the card's response tree: trace-existence at long form is established
and the pair claim is licensed AT the mechanical instrument's grade, stated without
softening — the reader is a valid but not value-adding detector of realized
concealment at this construction. The D1 branch (handling transfer to natural
revisions) becomes licensable at the root map, with the honest caveat that the
transferable instrument may be the hedge-density counter rather than the reader. The
localization failure is the theoretically interesting residue: whatever the reader
uses, it is not retrievable as a span, which bounds span-level asking as a repair
direction (it fixed nothing here) and leaves density integration as the operative
mechanism. G88's answer is now complete in both directions: real in construction,
real at long-form text, mechanical at heart, unlocatable by the reader that reads it.

### Curator roll-up

- **Theory group:** Reader Heuristics / Decision Traces
- **Question in plain language:** With room for the cover-up to breathe, can the
  reader finally tell a covered-up error from an unnoticed one — and show us where?
- **Outcome class:** Strengthens
- **Result:** Separates at 0.77 against the essay-grain 0.417, at parity with a
  mechanical hedge counter (0.79), with zero successful span localization.
- **Project meaning:** Error-handling recovery works at long form; the signal is
  hedging density; the reader reads it without being able to point at it; short
  essays were below the channel's resolution, as L150 said.
- **Next engineering obligation:** The D1 transfer question routes to the Stage-1
  root map (constructed hedging to natural revisions; the instrument choice —
  reader vs counter — is part of that design).
- **Public claim:** Newly licensed, narrowly: instructed concealment is separable
  from non-recognition in long constructed text, by density, at 0.77 to 0.79.
- **Curator decision required:** Not yet; the root map carries it.
- **Detail pointer:** `results/g169r/verdict.json`, `prereg/g169r.py`, per-family
  confusion and all spans on disk.

## L159 · The ordered-accident ruler passes both seeds after one recorded repair: later dependence separates integrated accidents from failures, and origin stays honestly unresolved

**Hypothesis.** *(G171, Phase 2.3 root P23-F0, DESIGN CHECK in
`runners/run_g171_accidents.py`: when a structured deviation breaks an established
pattern, does HOW LATER CHOICES DEPEND ON IT separate an integrated accident from
abandonment, repair, and purpose — without ever calling unfamiliar convention an error
and without fabricating an origin the trajectory cannot show?)*

**Method.** The validated gridworld machinery, episodes of three-to-four trips: a
waypoint pattern established over two trips, the third carrying one of eight
mechanically generated classes (clean / abandoned / repaired / integrated / deliberate
/ convention / wrong-goal / pseudo-accident); likelihood classification against the
FITTED pattern account with episode-calibrated thresholds and post-cluster windows;
fifty episodes per class, full battery repeated on a fresh seed.

| gate | result | meaning |
|---|---|---|
| clean episodes | 1.00 no-anomaly after the repair | no invented anomalies |
| every class recovery | **all eight at or near 1.0**, both seeds | the confusion matrix is clean |
| convention called error | 0.00 | the unfamiliar-order hazard held |
| wrong-goal read as model revision | 1.00 | "too many mistakes" correctly becomes "my model is wrong" |
| **origin abstention on integrated and pseudo-accident** | **zero confident origin calls** | adoption identifiable, origin honestly unresolved — the D2 prediction enforced and passed |
| withheld continuation | 0.67 vs 0.33 marginal | above the null expectation, mechanical (landing direction leaks), reported as the noted surprise |

*Caption: pseudo-accident episodes are deliberate deviations dressed as accidents with
integration identical to the accidental class; the correct output is the integration
label with origin unresolved, never a confident origin either way. The one repair,
recorded in-file: a noisy clean walk crosses the bonus cell by chance, so the
deliberate signature became serving-the-bonus-INSTEAD-of-the-pattern — the exclusive-
consequence rule, the G161 consequence lesson in a new form.*

**Found.** ROOT-POSITIVE as a ruler validation, one iteration deep where G161 took
six, because every hard-won rule transferred: categorical multi-step deviations,
consequence structure (now exclusive), episode-calibrated thresholds, post-cluster
windows. Later structure is a readable record of adoption; origin is not readable and
the ruler says so instead of guessing; and the continuation arm confirms the
construction's one leak honestly (where a deviation lands partially predicts what
follows, a geometry fact, not a cognition fact).

**Means.** The ordered-accident ontology (origin, recognition, response, integration
as separable axes) has its constructed-world license: "an accident that acquired
order" is mechanically distinguishable from failure BY ITS DOWNSTREAM DEPENDENCE,
which is the curator's §2.2 ruling behaving as theory. Text transfer is a Stage-2
branch behind the root map, with the D2 boundary (adoption yes, origin no) carried
into any text form as a gate, not a hope.

### Curator roll-up

- **Theory group:** Decision Traces
- **Question in plain language:** In a world where we know the truth, can we tell an
  accident the maker built on from a mistake they abandoned — without pretending to
  know which one started as an accident?
- **Outcome class:** Strengthens
- **Result:** All eight classes recover at or near 1.0 on both seeds with zero
  fabricated origin calls, after one recorded repair.
- **Project meaning:** Integration is the readable half of ordered accidents;
  origin abstention is enforceable; the text form inherits both as gates.
- **Next engineering obligation:** None until the root map; text transfer is a
  Stage-2 branch.
- **Public claim:** Unchanged (constructed world only).
- **Curator decision required:** No.
- **Detail pointer:** `results/g171/ruler.json` and `ruler_freshseed.json`.

## L160 · Ratification leaves no readable trace: selection and veto sit at exactly chance from the artifact with their ceilings passed, and Stage 1 closes

**Hypothesis.** *(G168-R, `prereg/g168r.py`, frozen on the C0 CORPUS-STANDS: can a
reader recover recorded interaction roles — was the thesis chosen among alternatives?
did a veto reshape the plan? who repaired? — from the final essay, when the corpus's
own audit proves the selected thesis genuinely survives into the text at 0.95
integrity?)*

**Method.** 40 two-actor logged cases, three per-question arms (never aggregated),
each gated by its process-aware ceiling; balanced truth marginals asserted at build so
every floor is the analytic 0.5.

| question | ceiling (log shown) | artifact only | band |
|---|---|---|---|
| selection among alternatives vs accept-first | 0.975 | **0.500** | **BLIND** |
| veto and forced revision vs none | 1.000 | **0.500** | **BLIND** |
| repair by proposer vs writer | 0.525 — **ceiling FAILS** | 0.500 | uninterpreted |

*Caption: the ceiling arm sees the recorded event log; its failure on the repair
question means the reader cannot execute that question's two-hop actor mapping even
with the answer visible, so that question is an instrument defect, not a signal fact.
The two interpreted questions are the finding.*

**Found.** The cleanest W4 measurement of the day: contribution events that
demonstrably shaped the artifact (the chosen thesis out-overlaps every rejected one;
every veto produced a genuinely different plan) leave exactly nothing a reader can
recover from the product — 0.500 and 0.500, dead on the floor, with near-perfect
ceilings proving the questions are answerable from records. Ratification is real and
it is invisible.

**Means.** Per the card: contribution is auditable and not inferable from product;
the Wing C output is the audit interface (the brief's C5), stated without softening.
This is the third independent construction to land the same boundary in one day —
routes, handling-free contribution, now ratification — and it completes Stage 1:
all seven roots hold states. The root map follows as its own document; the repair
question owes a format fix (name actors explicitly in the question) before anyone
reads its 0.50 as evidence.

### Curator roll-up

- **Theory group:** Decision Traces
- **Question in plain language:** When two makers genuinely negotiated a text —
  choosing among theses, vetoing plans — can anything in the finished essay show it?
- **Outcome class:** Narrows
- **Result:** Chance exactly (0.50 on both interpreted questions) with ceilings at
  0.975 and 1.0.
- **Project meaning:** The ratification network is a records object; contribution
  auditing is a product surface, artifact inference is not.
- **Next engineering obligation:** The Stage-1 root map (delivered this pass); the
  repair-question format fix if Wing C ever reopens.
- **Public claim:** Unchanged.
- **Curator decision required:** At the root map, not here.
- **Detail pointer:** `results/g168r/verdict.json`, `prereg/g168r.py`.

## L161 · The Phase 2.4 reader reads without speaking: the likelihood form recovers realized revisions at 0.78, and the ScholaWrite floors are measured

**Hypothesis.** *(G177 P24-H0, `prereg/g177.py`, first two arms: before any intervention,
can the new non-generative reader — which scores how well each candidate instruction
predicts the finished text, never generating a word — see the one artifact-only target
the repository knows is real? And what do the cheapest mechanical predictors achieve on
the prospective next-intention task, as the floor every later reader must beat?)*

**Method (anchor).** The conditional-likelihood reader (Qwen2.5-1.5B base) scored the 100
realized-revision cases from the G159 corpus: for each essay, four candidate instructions
(one true, three decoys), each scored by the mean per-token log-probability it lends the
essay, neutral-conditioned arm subtracted. Instrument gate first: on 16 echo probes
(candidate quoting the essay's own opening vs three foreign openings) the reader must
find the true one at 0.90 or better.

**Found (anchor).** Gate perfect (16 of 16). Top-1 recovery **0.78 against the 0.25
candidate floor** (binomial p 1.6e-28; multiplicity ledger updated), with the
direct-prompted reader's 0.86 (L146, different reader and different form) as the
reference line.

| arm | reader form | top-1 | floor |
|---|---|---|---|
| L146 recorded | prompted, generates its answer | 0.86 | 0.25 |
| this arm | likelihood only, generates nothing | 0.78 | 0.25 |

*Caption: recovery of the true revision instruction among four candidates on the same 100
artifacts; the two arms use different readers, so the eight-point gap is descriptive,
never a contrast.*

**Method (ScholaWrite floors).** Leave-one-project-out over the full 61,504-edit release
(the shipped leaky split never used; the overlapping-splits duplication caught and fixed
at build): at each sampled edit (120 per held-out project), predict the next annotated
writing-intention class among the fixed 15 labels, by training-projects majority and by
previous-label transition table. Macro-F1 with the label set held fixed.

**Found (ScholaWrite floors).** Majority 0.04 to 0.06 macro-F1 per project; transition
table 0.04 to 0.08. Fifteen fixed classes make these floors properly punishing; the local
reader arm (queued behind these) must clear them and its citation known-answer gate
before its numbers count.

**Found (ScholaWrite reader arm, landed same day).** The local prompted reader scored
0.063 to 0.115 macro-F1 per project, above the mechanical floors in four of five
projects — but its citation known-answer gate came back with EXACTLY ONE decidable case
in the 600-event sample, which the reader missed (0.0 against the 0.80 floor at n = 1).
The card's own rule (from the adjudicator lesson, L139): a reader whose validation has
not passed reports no verdicts. A one-case gate is unpowered rather than informative,
but the consequence is the same either way, **the reader arm is UNVALIDATED and its
numbers are descriptive only**. A powered validation needs stratified sampling toward
mechanically decidable edits, filed as the follow-on; the mechanical floors are the arm's
standing result.

| arm | project 1 | 2 | 3 | 4 | 5 |
|---|---|---|---|---|---|
| majority class | 0.051 | 0.041 | 0.057 | 0.050 | 0.048 |
| previous-label transition | 0.052 | 0.040 | 0.072 | 0.039 | 0.082 |
| local reader (unvalidated) | 0.068 | 0.078 | 0.063 | 0.115 | 0.073 |

*Caption: macro-F1 over the fixed 15 intention classes, next-edit prediction with future
text withheld, one column per held-out project, 120 sampled events each.*

**The powered validation ran the next day and closed the question (H1 repair, Stage 2).**
Stratified toward mechanically decidable edits — 120 events whose change inserts a citation
command and carries the citation label, against 120 matched negatives, making the floor
analytic at 0.5 — the prompted reader scores **sensitivity 0.25, specificity 0.94, balanced
accuracy 0.596** against a chance band whose top sits at 0.589 for this sample size and a
required floor of 0.80. The reader is barely above chance and fails its gate outright.

The failure has a clean signature and it is the mirror image of the one this project already
owns: where the L139 adjudicator over-credited almost everything, this reader under-uses the
class almost entirely, catching one decidable citation edit in four while almost never
claiming one falsely. Near-zero over-claim beside massive under-claim is its own defect
pattern. **The prompted-reader route to this corpus is therefore closed after its one repair**,
and the L161 reader numbers stay descriptive permanently rather than pending. Per the card's
routing, the boundary is preserved and the next instrument is the non-generative form, which
is the reader validated on the anchor above; if that also fails, the prospective interface has
no validated reader of any form and that is the finding.

**The non-generative form also failed, same day.** The
likelihood reader that recovers realized revisions at 0.78 on the anchor scored the same
stratified citation subset by how much the draft raises each intention statement's likelihood,
label priors subtracted: sensitivity 0.083, specificity 1.000, balanced accuracy 0.542 against
the 0.589 chance-band top. At chance, an even more extreme version of the same under-use
signature, and its leave-one-project-out numbers were withheld by its own precondition. **The boundary, at its corrected scope (revised the same evening, and the correction came
from this project's own record).** The first form of this paragraph claimed the interface had
no validated reader of any form; that overreached. The cheap ceiling probe then ran, a
surface classifier reading the REALIZED edit itself under leave-one-project-out, and scored
0.048 macro-F1, indistinguishable from the prospective floors; its automatic verdict called
the label noise. But the recorded fine-tuned grid (L82) already places trained encoders at
0.26 to 0.61 macro-F1 on this task family under the same split discipline, so the label is
NOT noise and the runner's mechanical verdict is overridden by the record. The honest
boundary: **prompted and likelihood readers fail at floors where trained encoders
demonstrably succeed**, a reader-family boundary rather than an interface boundary, and
cheap surface features of even the realized edit carry almost nothing, so whatever carries
the label needs a trained encoder to reach it. The zero-shot and likelihood routes stay
closed; the trained-encoder route is the recorded exception, and any future use of it owes
the standard known-answer validation first.

**The context-override battery ran on this reader (day 2), and the result is a structural
boundary, not a behavior.** Three arms over the same hundred cases: no card (0.78, the
baseline reproduced exactly), a true production note naming the real instruction (0.04),
and a false note naming a decoy (0.78, with the decoy followed exactly never). The pattern
looks like resistance and is actually arithmetic: the card is prepended to every candidate
condition and the neutral equally, so an assertion's content either cancels in the
subtraction (the false arm, ordering untouched) or collides with the candidate it names,
making that candidate REDUNDANT and collapsing its margin (the true arm, where the correct
answer sinks to last precisely because the card already said it). The honest conclusion:
**the non-generative reader has no context input channel at all.** It cannot be steered by
a supplied note, and it equally cannot USE a true one; the G167 override defect is a
property of readers with instruction-following channels, which this form simply lacks. Any
future context experiment on this family requires a design that injects context somewhere
other than the conditioning path, and the redundancy collapse is the standing warning that
prepending is not that design.

**Means.** The Phase 2.4 instrument is field-validated on a known-positive target: the
non-generative form keeps most of the recorded recovery while making fabrication
structurally impossible (nothing is generated), which is what the similarity matrix and
any later intervention arm score through. The prospective interface's mechanical floors
are measured and low, and the first prompted-reader look sits barely above them with its
validation gate unpowered — the prospective next-intention task is hard for everything
tried so far, which is exactly what makes it the anti-projection target the phase wants.
One arm of this root remains (the CoAuthor import); it folds in here when it lands.

### Curator roll-up

- **Theory group:** Decision Traces (choice-event recovery) / instrument ledger
- **Question in plain language:** Does the new reader that never generates text still
  see the choices we know are readable, before we trust it anywhere new?
- **Outcome class:** Infrastructure
- **Result:** 0.78 top-1 against a 0.25 floor on the known-positive revisions.
- **Project meaning:** Phase 2.4's common instrument works on arrival; everything the
  similarity matrix and the intervention arms report flows through a validated scorer.
- **Next engineering obligation:** The CoAuthor import, the powered stratified validation
  for the ScholaWrite reader, then the G172 matrix reads through the validated scorer.
- **Public claim:** Unchanged.
- **Curator decision required:** No.
- **Detail pointer:** `results/g177/anchor.json`, `results/g177/scholawrite_lopo.json`,
  `results/g177/scholawrite_reader.json`, `results/g177/scholawrite_validation.json`,
  `results/g177/scholawrite_nongen.json`, `results/g177/scholawrite_ceiling.json`,
  `results/g177/coauthor_import.json`, `results/g177/anchor_context.json`,
  `prereg/g177.py`.

**CoAuthor arm (landed same day, closing the root).** IMPORTED: 1,447 session files, 2.7
million logged events sampled at inventory. The paired-delta and prospective reading
batteries over it are Stage-2 material; with this the interface-mapping root is COMPLETE —
all four arms landed in one day, three with results, one honestly unvalidated.

## L162 · The open-weight affect ruler fails as an instrument: block selection is noise at this dev power, and one degenerate selection lesions the model

**Hypothesis.** *(G174 P24-A0, `prereg/g174.py`, frozen: does a 1.5B open model carry
abstract affect representations — readable on situations containing no emotion vocabulary —
that causally influence a benign approach-withdraw preference under amplification and
ablation, with matched controls quiet, on both seeds?)*

**Method.** Six emotion-concept directions fitted per block from explicit emotion-word
sentences only; decoding tested on scrubbed situations (lexicon-clean by load-time
assertion) at the block chosen on a dev split; causal half amplified and ablated the fear
and joy directions during continuation reading of twelve ambiguous scenarios, against
random and shuffled-label bases, with a capability gate on neutral text.

**Found.** INSTRUMENT-FAIL, and the failure is informative about the battery, not the
theory. The two seeds chose blocks 27 and 1 respectively — an eighteen-item dev split
cannot select a block stably — and the second seed's choice of block 1 (the input-adapter
edge, where every content type snaps in every family we have measured) turned
amplification into a lesion: neutral-text log-probability moved 2.55×, against a 5
percent tolerance. Where the battery did function (first seed, block 27): scrubbed-text
decoding 0.30 against a 0.167 chance floor, with the lexical baseline collapsing to
exactly chance (the scrub worked — a word-matcher has nothing to match) and the
shuffle null's 95th percentile at 0.267; actor frames held it (0.33, 0.37). The causal
sign pairs were null everywhere at every dose tried.

| gate | seed A (block 27) | seed B (block 1) |
|---|---|---|
| scrubbed decoding vs chance 0.167 | 0.30, above both nulls | 0.10, below the shuffle null |
| lexical baseline on scrubbed text | 0.167 (exactly chance) | 0.167 |
| causal sign pair (fear, joy) | null | null |
| capability change under amplification | 0.2 to 0.6 percent | **255 percent** |

*Caption: the ruler's gate table; decoding is six-class accuracy on emotion-word-free
situations at the dev-selected block; capability is the relative change in neutral-text
per-token log-probability under the operating amplification.*

**The predeclared repair is declined, with the reason on record.** The card's one repair
(halve the dose) cures only the capability lesion; the second seed's decoding failure is
dose-independent, so the best band the repair could reach is LEXICAL-ONLY — a stronger
negative claim than the evidence supports, since the one functioning seed decoded ABOVE
its lexical control on text where that control provably collapses. The honest label is
instrument failure at this power, and the repair budget is not spent converting one
failure label into a worse-founded one.

**Means.** The causal gate on the architecture file's build path stays untested at this
scale and power; nothing here is evidence against the human theory (the card's own
routing). The grain worth keeping: abstract, emotion-word-free affect decoding EXISTS at
1.5B at one seed, weakly, above every control — the battery around it was too small, not
the signal absent. The rebuild lane is the discovery forest (the addendum's condition
"decodes above its lexical control" is met): an order-larger stimulus bank and a frozen
aligned-stage block rule instead of dev selection, on discovery data, earning a fresh
confirmation card if it stabilizes.

### Curator roll-up

- **Theory group:** Three Cognitive Layers (the §8 causal build gate)
- **Question in plain language:** Can a small open model show affect structure that is
  abstract (readable without emotion words) and causally usable, under honest controls?
- **Outcome class:** Infrastructure
- **Result:** The battery failed itself — block selection flipped between seeds and the
  degenerate choice moved neutral-text likelihood 2.55× against a 5 percent tolerance.
- **Project meaning:** The affective-intervention wing has no validated ruler yet; its
  basis contest and inversion test stay closed until a rebuilt ruler earns a fresh card.
- **Next engineering obligation:** The scout-lane rebuild (larger bank, frozen block
  rule); the similarity wing proceeds independently.
- **Public claim:** Unchanged.
- **Curator decision required:** No.
- **Detail pointer:** `results/g174/ruler.json`, `prereg/g174.py`.

## L163 · Similarity reads: the exact maker checkpoint and its family siblings invert recorded goals better than cross-family readers, graded, on a corpus that retired half its makers to stay honest

**Hypothesis.** *(G172 P24-S0, `prereg/g172.py`, frozen: are a model's outputs easier to
invert — recorded entity-order goals recovered among four lexically matched candidates —
when the reader is the exact maker checkpoint, a same-family sibling, or a cross-family
model? The tractable analogue of the shared-organization shortcut, never the human claim.)*

**Method (corpus).** Makers generated short informative paragraphs under assigned goals
(mention A first and B later, avoid C and D) with realization verified INSIDE the accept
loop, so every accepted artifact carries a mechanically true goal. The corpus enforced its
own honesty the hard way: first pass 59 percent fill because both base Pythia makers
could not satisfy four constraints (17 and 28 percent); the predeclared repair (redrawn
example, 24 attempts) lifted them only to 45 and 52; the card's second-failure clause then
RETIRED both makers rather than lowering the bar. The corpus stands at 123 of 128 cells
(96 percent) on the two Qwen makers, goal composition balanced (32/31/31/29), with the
**single-maker-family limitation recorded in the manifest**: cross-family cells exist on
the reader side only.

**Method (matrix).** Nine readers scored every artifact against its four candidates with
the conditional-likelihood reader (all four candidates name all four entities, so nothing
is readable by word-spotting; the differences are role assignments). Per-reader instrument
gates ran first; the preregistered contrasts are paired per artifact: exact-maker margin
minus mean cross-family margin (first contrast), mean sibling margin minus mean cross
(second), sign-flip permutation with twenty thousand draws.

**Found.** **SIMILARITY-GRADED, the band the shared-organization account predicted.** Both
contrasts positive at the permutation floor: exact beats cross by 0.035 per-token margin
units (p 5.0e-05, the smallest value twenty thousand permutations can report), siblings
beat cross by 0.025 (p 5.0e-05). Two of nine readers (the mid Pythia and the SmolLM2)
were excluded by the frozen shuffle-floor gate at 0.375 against a [0.15, 0.35] band — at
24 probes that is within sampling noise of the 0.25 expectation, so the exclusion is
conservative and the band's width-at-probe-n goes on the next card's design list.

| reader | relation to the Qwen makers | top-1 | mean margin |
|---|---|---|---|
| Qwen 3B | sibling (largest) | 0.854 | 0.059 |
| Qwen 0.5B | exact for half the corpus | 0.797 | 0.057 |
| Qwen 1.5B-Instruct | sibling (tuned) | 0.748 | 0.056 |
| Qwen 1.5B | exact for half the corpus | 0.724 | 0.050 |
| Pythia 2.8B | cross, larger than both makers | 0.724 | 0.034 |
| Pythia 410M | cross | 0.699 | 0.029 |
| GPT-2 large | cross | 0.618 | 0.021 |

*Caption: recovery of the true goal among four candidates, and the mean margin of the
true candidate's score over the decoys, per gate-passing reader, sorted by margin. Every
Qwen-family reader out-margins every cross-family reader, including a cross reader nearly
twice the largest maker's size — the graded pattern with capacity failing to explain it.*

**Means.** The similarity mechanism has its first behavioral foothold: family relation
predicts inversion margin within this construction, capacity does not (the 2.8B
cross-family reader loses to the 0.5B exact maker on margin), and the base-vs-instruct
sibling cell shows tuning does not break the family advantage. The standing rival is
exactly the one the card names: artifact dialect — a family fingerprint in the surface
that erasure would destroy. The fingerprint-destruction scout (paraphrase preserving the
mechanically verified goals, matrix re-run) is the branch that decides it, and the
single-maker-family limitation means every claim here is about readers of Qwen artifacts
until a second maker family exists. STAGE 1 IS COMPLETE: all three roots hold states; the
cold root map follows this entry and freezes before any scout runs.

### Curator roll-up

- **Theory group:** Reader Heuristics (the similarity shortcut, model-family analogue)
- **Question in plain language:** Is a text easier to read-back-to-its-goal for the model
  that wrote it, and for that model's relatives, than for strangers?
- **Outcome class:** Strengthens
- **Result:** Graded — exact and sibling readers beat cross-family readers with the
  sibling contrast at 0.025 margin units, both at the permutation floor.
- **Project meaning:** The shared-organization shortcut gains its first model-side
  behavioral evidence; the fingerprint rival is now the load-bearing alternative and has
  a designed killer.
- **Next engineering obligation:** The fingerprint-destruction scout on this same corpus;
  a second maker family (instruct-class, since base models cannot comply) if the scout
  survives.
- **Public claim:** Unchanged (analogue result; no human claim licensed, per the card).
- **Curator decision required:** No — the root map carries the theory questions.
- **Detail pointer:** `results/g172/verdict.json`, `results/g172/corpus_manifest.json`,
  `prereg/g172.py`.

## L164 · The similarity gradient survives goal-preserving Qwen paraphrase at reduced magnitude; capacity remains a weak rival, while paraphraser circularity prevents claim promotion

**Hypothesis.** *(Discovery scouts E24-S02 and E24-S05, run behind the frozen cold root map,
unsealed after the curator's walkthrough: does the graded similarity pattern survive the
destruction of surface dialect, and does reader size explain the matrix?)*

**Method (erasure, E24-S02).** Every similarity-corpus artifact was paraphrased under
aggressive restyling instructions with the goal verified mechanically per item (115 of 123
accepted); the seven gate-passing readers then re-scored the erased artifacts against the
unchanged candidate sets, and the two preregistered contrasts were recomputed. **The
paraphraser is itself Qwen-family — the only instruct model then local — so survival is weak
evidence and collapse would have been strong; the confound is recorded in the scout file, this
method, the interpretation, and the roll-up.**

**Found (erasure).** PROMISING. The gradient survives at reduced magnitude: exact-versus-cross
attenuates from +0.035359 to +0.016454 (about 53 percent), sibling-versus-cross from
+0.024633 to +0.020914 (about 15 percent), both paraphrased contrasts still at the permutation
floor (p 4.99975e-05, 20,000 sign-flip permutations, 115 artifacts; ledger updated).

| contrast | original | after accepted paraphrase |
|---|---|---|
| exact maker minus cross-family readers | +0.035 | +0.016 |
| family siblings minus cross-family readers | +0.025 | +0.021 |

*Caption: mean per-artifact margin differences in per-token score units; the exact-checkpoint
advantage halves under erasure while the family advantage barely moves.*

**Method and found (capacity, E24-S05).** From the landed matrix records alone: the rank
relation between reader parameter count and mean margin across the seven gate-passing readers
is 0.428571 (weak), while family separation is complete — every Qwen-family reader out-margins
every cross-family reader. PROMISING.

**Means.** The pure capacity account remains poor. A simple removable surface-dialect account
loses probability because the gradient survives accepted paraphrase, but the eraser is
Qwen-family and may preserve or reintroduce precisely the family regularities at issue. The
result therefore keeps shared organization live beside a narrower circular-erasure rival. It
is discovery evidence and does not promote G172 beyond its L163 grade; the single-maker-family
limitation is inherited from L163, and the non-circular erasure test (independent paraphraser,
second maker family) is Stage 2's Wave 1.

### Curator roll-up

- **Theory group:** Reader Heuristics (the similarity shortcut)
- **Question in plain language:** Does the family advantage live in erasable surface habits,
  or in something restyling cannot remove?
- **Outcome class:** Narrows
- **Result:** The exact-checkpoint advantage halves under goal-preserving paraphrase while
  the family-sibling advantage survives nearly intact, both above chance at the permutation
  floor — with the Qwen-paraphraser circularity capping what survival can mean.
- **Project meaning:** Roughly half the exact advantage was erasable surface; the
  family-shaped remainder is the part worth a mechanism, and only a non-circular eraser can
  promote it.
- **Next engineering obligation:** The Wave-1 independent eraser and second maker family
  (running); discovery grade until then.
- **Public claim:** Unchanged.
- **Curator decision required:** No.
- **Detail pointer:** `results/scouts/s02_erasure.json`,
  `results/scouts/s02_paraphrase_manifest.json`, `results/scouts/s05_capacity.json`,
  `docs/design/PHASE_2_4_REGISTRY.md`.

## L165 · The crossed reversal appears: each maker family's artifacts are read best by that family's readers, and the pattern survives an independent eraser that measurably strips family surface signal

**Hypothesis.** *(Stage-2 Tree-S Wave 1, discovery lane, scouts E24-S1a/S1c/S3/S2: is the
similarity advantage a property of the RELATION between maker and reader, or is it Qwen
readers being good at reading? The diagnostic the Stage-2 brief names as most decisive is a
crossed reversal — each family's artifacts read best by its own relatives — and it requires a
second maker family, which Stage 1 did not have.)*

**Method.** Two instruction-tuned SmolLM2 makers wrote the same mechanically verified
entity-order goal corpus (63 and 64 of 64 cells filled, realization checked inside the accept
loop). Both corpora then passed through two erasers: mechanical normalization (punctuation,
casing, whitespace) and an independent SmolLM2-instruct paraphraser, each re-verifying the goal
per item. Eleven readers scored every variant against the unchanged candidate sets, each reader
gated on an echo known-answer probe first. For each artifact the contrast is the mean margin of
same-family readers minus the mean margin of other-family readers, tested by sign-flip
permutation with 20,000 draws. **The retired Pythia makers are excluded everywhere** — their
partial cells are skewed toward whichever goals a weak base model could satisfy, a selection
this reading must not inherit (the defect was caught in the first analysis pass and fixed).

**Found.** **The crossed reversal is real and survives both erasers.** Every cell of the
own-minus-other contrast is positive at the permutation floor.

| artifacts written by | own-family readers | the other modern family | Pythia readers | GPT-2 large |
|---|---|---|---|---|
| the Qwen makers | **+0.055** | +0.047 | +0.030 | +0.021 |
| the SmolLM2 makers | **+0.043** | +0.040 | +0.021 | +0.012 |

*Caption: mean margin of the true goal over its three decoys, in per-token score units, by the
family relation between the artifact's maker and its reader. Each row's best cell is its own
family.*

| variant | Qwen artifacts, own minus other | SmolLM2 artifacts, own minus other |
|---|---|---|
| untouched | +0.0195 | +0.0142 |
| mechanically normalized | +0.0195 | +0.0142 |
| paraphrased by Qwen | +0.0119 | not built |
| paraphrased by SmolLM2 (independent for Qwen) | +0.0117 | +0.0130 |

*Caption: the same contrast under each erasure, all at p = 0.00005, the smallest value 20,000
permutations can report, over 93 to 127 artifacts per cell.*

**Correction, made the same day by a gate built after the first reporting pass.** The
independent eraser does not erase everything it is handed: an echo check found 8 of 122 Qwen
artifacts and 23 of 127 SmolLM2 artifacts returned essentially unchanged, and the asymmetry
runs the wrong way for comfort, since the eraser echoed its own family's text at twice the
rate of the other family's (27 percent barely changed versus 13). The independent-eraser row
above is therefore computed on genuinely rewritten artifacts only (similarity below 0.9): the
contrast falls from +0.0129 to +0.0117 for Qwen artifacts and from +0.0138 to +0.0130 for
SmolLM2, both still at the permutation floor on the smaller sample. The survival claim holds
and its magnitude is slightly smaller than first reported. Mechanical normalization is exempt
from this filter by construction, since it changes punctuation and casing rather than
rewriting, and its erasure question belongs to the source detector instead.

**The mirror arm's own near-miss, recorded because the guard is the reusable part.** The Qwen
paraphraser over the SmolLM2 corpus passed its erasure gate cleanly (median character overlap
0.038, nothing identical), and its first contrast read +0.0197, larger than the untouched
value and a striking headline. That number was computed over a reader matrix five of eleven
deep, three of those the maker's own family, so both sides of the comparison were set by
whoever had finished. Complete, the cell reads +0.0107. A completeness guard now withholds any
variant whose matrix has not written its done marker. The mirror variant holds only one maker
family, so no family classifier can attest its erasure; the character-overlap gate does that
job there instead.

**The erasure is measurable and partial.** A topic-held-out classifier reading only surface
character patterns identifies the maker family at 0.664 on normalized text and 0.582 after
independent paraphrase, against 0.500 chance for the two-family problem: the eraser halves the
detectable family surface signal, from sixteen points above chance to eight, and the reading
advantage survives anyway. Family information is reduced rather than gone. *(These figures
replace the 0.636 and 0.518 first reported, which were computed against a three-way chance of
0.333 because the retired makers were still contaminating the classifier's label set.)*

**The crossed-imprint design completed the same day, and it discriminates.** With the mirror
arm finished, each family's artifacts have now been rewritten by both a same-family and a
cross-family paraphraser, which separates three accounts the earlier cells could not.

| artifacts written by | untouched | mechanically normalized | rewritten by their own family | rewritten by the OTHER family |
|---|---|---|---|---|
| the Qwen makers | +0.0195 | +0.0195 | +0.0119 | **+0.0117** |
| the SmolLM2 makers | +0.0142 | +0.0142 | +0.0130 | **+0.0107** |

*Caption: own-family minus other-family reader margin, per maker family, under each
transformation; every cell at p = 0.00005 over 93 to 127 genuinely rewritten artifacts. The
last column is the non-circular test: the eraser and the maker come from different families.*

**The advantage follows the artifact's original maker, not the model that rewrote it.** Had it
followed the paraphraser, Qwen-rewritten SmolLM2 artifacts should have favoured Qwen readers
and SmolLM2-rewritten Qwen artifacts should have favoured SmolLM2 readers. Neither happens: on
SmolLM2 artifacts rewritten by Qwen, SmolLM2 readers still lead (0.0384 against Qwen readers'
0.0354), and on Qwen artifacts rewritten by SmolLM2, Qwen readers still lead (0.0443 against
0.0423). Rewriting lowers every reader slightly and preserves the ordering; the rewriting
family gains nothing from having produced the text. Of the three signatures the design was
built to separate, only the first survives.

**Means (revised as the design completed).** Reader quality explains most of the spread — both modern instruct-era families beat
Pythia and GPT-2 on everything — and the own-family term is a smaller effect riding on top of
that ordering, roughly 0.014 to 0.020 score units. But it is the term that reverses with the
artifact's origin, which reader quality cannot do, and it survives an eraser built from a
different family than the artifacts it rewrites. That combination is what the single-family
Stage-1 result could not deliver, and the completed crossed-imprint design adds the sharper
fact: the advantage is a property of who wrote the text, surviving rewriting by a different
family that gains nothing from having done the rewriting. The tokenizer rival was later
checked directly (E24-S6, day 2): token-segmentation overlap between reader and maker does
not significantly predict the double-centered matrix (rank 0.32, p 0.10 at 28 cells), and
neither single factor separates cleanly at that power — the scout is QUIET, the crossed
per-artifact permutations remain the load-bearing family evidence, and the tokenizer
account gains nothing. What remains unsettled is what "family" names mechanically. Surface family signal is halved but not removed, both surviving
families are modern instruction-tuned models while the two that lose are older architectures,
and nothing here shows the relation helping at any target beyond goal wording. Discovery
grade, no promotion: the Stage-2 conjunction for Tree S requires process-level and geometry
evidence this scout does not touch.

### Curator roll-up

- **Theory group:** Reader Heuristics (the similarity shortcut, model analogue)
- **Question in plain language:** Is a text easier to read back to its goal for the family that
  wrote it, or were we just watching better readers win?
- **Outcome class:** Strengthens
- **Result:** Each maker family's artifacts are read best by its own relatives, and the
  advantage follows the original maker rather than the model that rewrote the text, through
  a cross-family eraser that halves measured family surface signal.
- **Project meaning:** The similarity effect belongs to the maker-reader relation, not to
  reader quality alone; the surface-dialect account is now the weaker half of the rival set.
- **Next engineering obligation:** The process-resolution ladder, which asks whether the
  relation helps at anything beyond goal wording, and the geometry linkage, whose trigger
  condition the crossed reversal now meets.
- **Public claim:** Unchanged (model-analogue result; no human claim licensed).
- **Curator decision required:** No.
- **Detail pointer:** `results/scouts/s_wave1.json`, `results/scouts/s2_detector.json`,
  `results/scouts/s6_tokenizer.json`, and the construction manifests
  (`family2_manifest`, `norm_manifest`, `para2_manifest`, `mirror_manifest`, all under
  `results/scouts/`), `runners/scout_stage2_s.py`, `runners/scout_stage2_s6.py`.

## L166 · The crossed reversal lives at the abstract rung and dies at the literal one: asking with the maker's own instruction wording inflates every margin and hands all four corpora to one reader family

**Hypothesis.** *(Stage-2 Tree-S scout E24-S03, the process-resolution ladder's first rung:
does the maker-reader family relation operate on WORDING, or on something the wording only
points at? If the relation is surface-shaped it should be strongest where the candidate text
overlaps the artifact most — that is, when the candidates are the literal instructions the
makers were given, verbatim.)*

**Method.** The same eleven echo-gated readers scored the same untouched artifacts from both
maker families, changing only the candidate set: the abstract rung uses a paraphrased
description of the goal, sharing almost no vocabulary with the artifact; the literal rung uses
the verbatim instruction each maker was given, which names the same entities the artifact was
required to contain. Everything else is held fixed.

**Found.** The summary statistic says the family term more than triples at the literal rung
(own-family minus other-family goes from +0.0195 to +0.0676 on the Qwen corpus and from
+0.0142 to +0.0330 on the SmolLM2 corpus). **The head-to-head between the two strong families
says the opposite, and it is the one that matters.**

| | Qwen artifacts read by Qwen | by SmolLM2 | SmolLM2 artifacts read by SmolLM2 | by Qwen |
|---|---|---|---|---|
| abstract goal rung | **0.0554** | 0.0465 | **0.0433** | 0.0395 |
| literal instruction rung | **0.1360** | 0.0973 | 0.1092 | **0.1183** |

*Caption: mean margin of the true candidate over its decoys, per-token score units. Bold marks
the winning reader family for each corpus. At the abstract rung each corpus is won by its own
family, which is the crossed reversal. At the literal rung one family wins both corpora.*

At the literal rung every margin roughly doubles or triples, exactly as a wording-overlap
effect should, and the reversal breaks: Qwen readers become the best readers of SmolLM2
artifacts as well as their own. The clean crossed pattern exists only where the candidate
shares almost no vocabulary with the artifact.

**Means.** The relation effect is not a wording artifact. Had it been, it would have been
cleanest where wording overlap is greatest, and instead that is exactly where it dissolves
into a single family reading everything better. What the literal rung measures is largely
reader strength on an easy, echo-rich task; what the abstract rung measures is a smaller
quantity that follows the artifact's origin. This is the second control in two passes to cut
against the surface account, after cross-family rewriting failed to move the advantage
(L165). It still says nothing about whether the relation helps at any target other than
recovering an assigned goal, which is the next rung and the Tree-P question.

**A statistic-shape caution this run earned.** Own-family minus other-family, averaged over a
heterogeneous set of other readers, stayed positive at the literal rung for both corpora even
though the decisive comparison between the two strong families had flipped, because the
average is held up by the two weak architectures. The pairwise matrix is the result; the
one-number contrast is a summary that can hide a reversal inside it. Every crossed claim in
this wing now reports the head-to-head cells beside the contrast.

### Curator roll-up

- **Theory group:** Reader Heuristics (the similarity shortcut, model analogue)
- **Question in plain language:** Is the family advantage about the words, or about something
  the words only point at?
- **Outcome class:** Strengthens
- **Result:** Asking with the maker's own instruction wording inflates every margin and hands
  both corpora to one reader family; the reversal survives only where the candidate and the
  artifact barely share vocabulary.
- **Project meaning:** The wording account of the similarity effect is doing badly from a
  second direction, and the abstract rung is established as the honest place to measure it.
- **Next engineering obligation:** The rungs above wording, which ask whether the relation
  helps recover anything the maker did that the instruction did not state.
- **Public claim:** Unchanged.
- **Curator decision required:** No.
- **Detail pointer:** `results/scouts/s_wave1.json` (variants `origL` and `fam2L`),
  `runners/scout_stage2_s.py`.

## L167 · The CoAuthor decision record parses cleanly and its behavior is flat: writers take three of four suggestions, and neither their own history nor session position predicts which

**Hypothesis.** *(Stage-2 Tree-H scouts E24-H02b and E24-H03: do the 1,447 imported
writing-session logs yield a usable decision-episode record, and how predictable is the
writer's next accept-versus-dismiss action from mechanical structure alone? The floors any
later reader must beat.)*

**Method.** Every session log parses into decision episodes: a shown suggestion followed by
the writer's terminal action on it, taken (selected into the text) or dismissed (closed).
Unreadable sessions are counted, never dropped, with a ten percent skip ceiling as the
extraction's own failure gate. Four mechanical baselines: global majority; each session's
first-half rate applied to its own second half (nothing crosses the prediction boundary);
previous-outcome repetition; session position. Split by session, with the session-as-writer
approximation recorded as a limitation.

**Found.** Extraction is clean beyond expectation: 1,410 sessions, zero unreadable, 16,875
decision episodes. Writers take 75.8 percent of shown suggestions. And the behavior is FLAT:
no mechanical baseline beats the global majority.

| baseline | accuracy | episodes scored |
|---|---|---|
| always predict the majority (taken) | 0.758 | 16,875 |
| the session's own first-half rate | 0.711 | 8,768 |
| repeat the previous outcome | 0.695 | 15,465 |
| session position (early or late) | 0.758 | 16,875 |

*Caption: accuracy predicting taken versus dismissed at each shown suggestion. The
individual-history baselines land BELOW the global rate, so a writer's own earlier behavior
generalizes worse than the population rate at this grain.*

**Means.** QUIET, and informative about the target's shape. Accept-versus-dismiss on this
corpus is dominated by a strong base rate with no sequential or individual structure at the
grain these baselines see, which sets a hard bar for any later reader: beat 0.758 accuracy,
or better, show calibrated discrimination on the dismissed quarter, since raw accuracy at
this skew rewards saying "taken" forever. The intended model arm stays unbuilt by design;
after the prospective boundary (this entry's sibling in L161), any reader aimed at this
target validates on a decidable subset first, and what would make one decidable here, such
as suggestions later deleted versus retained, is the next extraction question. The
session-as-writer approximation stands as the recorded limitation.

### Curator roll-up

- **Theory group:** Decision Traces (mixed-production ratification, natural-record side)
- **Question in plain language:** In real human-and-model co-writing logs, how predictable
  is whether the writer takes the next suggestion, before any model reads anything?
- **Outcome class:** Infrastructure
- **Result:** 16,875 decision episodes parsed with zero loss; nothing beats the 0.758
  base rate of simply taking suggestions.
- **Project meaning:** The natural ratification record is now a usable substrate with
  measured floors, and its flatness at this grain is itself the bar any reader must clear.
- **Next engineering obligation:** The retained-versus-later-deleted extraction, which is
  both the richer target and the mechanically decidable subset a reader validation
  needs. *(Landed same day after two extraction repairs, both instructive: the
  suggestion text lives on the preceding shown-event, not the selection event, and the
  final document exists nowhere in the log and must be replayed from the edit deltas.
  Result: 11,773 decidable accepted suggestions, 68.7 percent retained verbatim to session
  end, a balanced target where accept-versus-dismiss was not, and the validation substrate
  this tree needed.)*
- **Public claim:** Unchanged.
- **Curator decision required:** No.
- **Detail pointer:** `results/scouts/h_coauthor_events.json`,
  `results/scouts/h_coauthor_baselines.json`, `results/scouts/h_coauthor_retention.json`,
  `runners/scout_stage2_h.py`.

## L168 · The geometry leg lands: representational alignment predicts who inverts whom, with reader quality and maker difficulty both removed by construction

**Hypothesis.** *(Stage-2 Tree-S scout E24-S07, the linkage whose trigger the crossed
reversal met twice: does measured representational alignment between a reader and a maker
predict that reader's inversion margin on that maker's artifacts, beyond how good the reader
is and how easy the maker is?)*

**Method.** All thirteen models' late-stage representations captured on the same eighty
shared texts (the normalized artifacts from both maker families; process-matched rather than
neutral, a recorded scope note). The instrument gate first: true-pairing alignment must
separate from a hundred correspondence-shuffled pairings, or nothing downstream is computed.
Then the linkage: mean margin per reader-maker cell against alignment per cell, BOTH
double-centered (reader means and maker means removed), rank-correlated, against a
within-reader label-shuffle permutation. Raw alignment magnitudes are deliberately
unreported, per the standing rule that only null-tested structure is quotable at this
sample-to-dimension ratio.

**Found.** Gate perfect: twelve of twelve model pairs separate from the correspondence null.
The linkage: **double-centered rank correlation 0.501, permutation p 0.0088**. After
removing what reader quality and maker difficulty can explain, the residual pattern of who
reads whom well tracks the residual pattern of whose representations align.

**The neutral replication landed the same evening and the relation strengthened.** On
eighty human student essays no matrix model produced — texts carrying none of the corpus's
process structure — the correspondence gate stays perfect and the double-centered rank
correlation rises to **0.768 at the permutation floor** (from 0.501 on process-matched
texts). The corpus-specific rival is answered: the alignment-inversion relation is a
property of the models, not of the texts it was first measured on.

**Means.** PROMISING and now twice-measured: the family advantage has a representational
correlate that survives double-centering on two disjoint text sets, one of them fully
neutral. What it still does not show is direction — alignment could follow from whatever
also drives inversion rather than enabling it — which is the causal branch's question.

**The causal branch's first attempt failed as an instrument, both directions, same night.**
Mapping maker goal directions into the cross-family reader and intervening on them: in one
direction the map itself failed its decode gate (0.375 against a 0.45 floor on an
eighty-text ridge map), and in the other the fixed amplification strength shifted
neutral-text likelihood 29.6 percent, the same lesion class the affect ruler taught, voiding
its own null deltas. No causal claim exists in either direction. The one predeclared repair
ran the same night, matched to both named failure directions: the map refit on 240 neutral
texts, and the dose was ladder-selected under the capability tolerance per cell.

**The repaired verdict closes the branch, and its shape is the finding.** In the direction
where the instrument now works cleanly (decode 0.531, capability 0.031, inside tolerance),
amplifying the mapped true-goal direction does raise the true candidate's margin (+0.014 at
the selected dose, p 0.0035) — but ablation does not lower it (+0.004, p 0.29, no sign
pair), and the label-shuffled control moves almost as much (+0.012, p 0.030) as the true
direction, while the random direction moves nothing at all. Amplifying ANY mapped
maker-space direction helps about equally, whether or not it is the right goal's: the
signature of generic steering along the maker's representational subspace, not of
goal-specific causal transfer. In the reverse direction the 240-text map failed its decode
gate again (0.312), the second instrument failure, and the closure clause fires. **E24-S08
closes for the phase: no evidence that mapped geometry is used goal-specifically, one
direction unmappable at this substrate, and the geometry leg stays descriptive** — which
the promotion conjunction can survive, since its geometry item is satisfied by the
twice-measured descriptive prediction, but the conjunction still lacks its process-level
leg and does not fire.

### Curator roll-up

- **Theory group:** Reader Heuristics (the similarity shortcut, model analogue)
- **Question in plain language:** Do models that represent text similarly also read each
  other's goals better, once we stop crediting sheer reader strength?
- **Outcome class:** Strengthens
- **Result:** Double-centered rank relation 0.501 on process-matched texts and 0.768 on
  fully neutral human essays, both gates perfect, the second at the permutation floor.
- **Project meaning:** The similarity effect now has a measured representational correlate;
  two of the promotion conjunction's four legs hold at discovery grade.
- **Next engineering obligation:** The causal transfer branch, whose opening condition
  the neutral replication just met.
- **Public claim:** Unchanged.
- **Curator decision required:** No.
- **Detail pointer:** `results/scouts/geo_link.json`,
  `results/scouts/geo_link_neutral.json`, `results/scouts/s8_transfer.json` (and
  `s8_transfer_v1.json`, the preserved first attempt), `runners/scout_stage2_geo.py`,
  `runners/scout_stage2_s8.py`.

---

## L169 · The process ecology refuses itself informatively: instructed preferences lose to the makers' own evidence appetites, and the first profile reader failed its synthetic gate until its scoring direction was flipped

**Hypothesis.** *(Stage-2 Tree-P scouts E24-P0 and E24-P2, the ecology's first factorial:
can makers be given standing evidence preferences, and can a reader recover them from a few
episodes well enough to predict held-out selections?)*

**Method and found (construction).** Three instruct makers by four assigned preference
profiles by ten evidence-selection topics, the realized two-item selection mechanical via
unique anchors; fill 108 of 120, at the gate. The audit then ruled the profile question
UNINTERPRETABLE: overall profile-following is 0.537, and the per-cell table shows why. The
makers obey the cautious and novelty profiles (rates 0.89 to 1.0) and ignore the cost and
precedent profiles almost completely (0.0 to 0.3). The realized pair-inclusion counts are
novelty 99, caution 84, cost 29, precedent 4: **the models have their own strong evidence
appetites, and a one-line instruction does not override them.** The marginal-derived floor
this skew produces is 0.917, leaving held-out prediction almost no headroom by construction.

**Method and found (reader instrument).** The profile reader failed its synthetic
perfect-compliance gate at exactly chance (0.25): scoring a hundred-word artifact
conditioned on a one-sentence profile description gives the hypothesis one sentence of
leverage over a long likelihood, which washes out. The one predeclared repair flips the
direction, scoring the short description given the artifact so every scored token is
hypothesis-bearing; its known-answer verdict lands separately, and a second failure retires
the arm.

**The repair failed and the arm is retired (same day).** The direction-flipped reader
scored 0.375 on the synthetic gate against the 0.85 floor, its second failure, and the
card's rule retires the reading arm: at this scale the likelihood reader cannot map
abstract preference descriptions onto evidence-selection artifacts in either direction.

**The self-policy measurement then closed the v2 target too.** Unprofiled, all three
makers select nearly identically (novelty and caution dominate: 9/9, 10/7, 10/8 of their
twenty selections, cost nearly absent, precedent never chosen), so there is no appetite
signature to recover a maker from. And the convergence exposes the honest rival for the
whole skew: the cautious and novel evidence items may simply be more attractive as
argument material than the cost and precedent items, an item-side account this
construction cannot separate from a model-side one.

**The attractiveness pilot then ran (day 2) and the item-side rival LOST.** With the cost
and precedent items rewritten to argumentative strength on three topics (anchors
substring-verified), overall following moved from 0.537 to 0.515 — statistically nothing —
and the per-cell shape is unchanged: cautious and novel followed at or near 1.0, cost and
precedent refused at 0.0 even when their items carry the strongest concrete claims in the
set. The appetite is about the CATEGORY, not the item: these instruct models prefer
safety- and novelty-shaped evidence intrinsically, resist instruction against it, and do
so identically across three checkpoints from two families. The assigned-profile design
retires with that sharpened conclusion, which upgrades the convergence observation from a
possible item artifact to a measured, instruction-resistant, cross-family preference
structure.

**Means.** Tree P's first implementation closes at its resolution boundary, per the
closure rules, with the full account on record: the treatment can be refused, the reader
instrument failed twice, the intended v2 object does not vary, and the item-side rival
was tested and disfavored. What survives is the design requirement for any successor:
target behavior that categorical preference cannot silently mediate. Methodologically, a factorial
whose treatment can be silently refused needs a compliance pilot before the full grid, now
a lesson.

### Curator roll-up

- **Theory group:** Decision Traces (choice-event recovery, constructed-world side)
- **Question in plain language:** Can we hand a model a standing preference and read it
  back from its choices?
- **Outcome class:** Infrastructure
- **Result:** The makers refuse half the assigned preferences (following 0.537 overall)
  and their unprofiled appetites converge, so neither the assigned profile nor the maker
  is recoverable from selections in this construction.
- **Project meaning:** Assigned preference is the wrong v1 handle; intrinsic policy is the
  measured, recoverable object and the v2 target.
- **Next engineering obligation:** None this phase — the calibration pilot ran and
  retired the design; any successor targets behavior outside categorical preference.
- **Public claim:** Unchanged.
- **Curator decision required:** No.
- **Detail pointer:** `results/scouts/p_ecology_manifest.json`,
  `results/scouts/p_ecology_audit.json`, `results/scouts/p_read.json`,
  `results/scouts/p_self_policy.json`, `results/scouts/p_pilot.json`,
  `runners/scout_stage2_p.py`.

## L170 · The rebuilt affect ruler answers the wing at this scale: the abstract representation is real and stably located, and it is not causally usable by linear steering

**Hypothesis.** *(Stage-2 Tree-A rebuild, scouts E24-A1/A2 plus the causal re-attempt: with
the first ruler's failure mechanics designed out — a bank 2.5 times larger keeping the
original items verbatim, a cross-seed consensus locus with the degenerate edge excluded,
ladder doses under the capability tolerance — does the emotion-word-free decoding grain
stabilize, and can the representation be causally nudged?)*

**Method.** Directions fitted on explicit emotion-word sentences only; decoding tested on
held-out lexicon-clean situations (120-item bank, load-time asserted) at the locus every one
of three seeded dev splits independently ranks top-three; shuffle nulls and a lexical
baseline per split; actor frames. Then fear and joy amplification and ablation over 24
approach-withdraw scenarios (dev/test split), dose ladder-selected under the capability
tolerance, against random and label-shuffled controls.

**Found (decode).** PROMISING, and the instability that killed the first ruler is gone: the
cross-seed consensus is UNANIMOUS on one deep block — the same block the first ruler's
functioning seed had found before its twin picked the input edge. Held-out decoding reads
0.35, 0.35, 0.33 across the three splits against a 0.167 chance floor, above every shuffle
null (0.22 to 0.24), with the lexical baseline at exactly chance on all three (the scrub
works: a word-matcher has nothing to match), and the actor frames inside tolerance.

**Found (causal).** QUIET on both concepts. At the consensus locus, with doses the
capability gate accepted, neither amplification nor ablation moves the approach-withdraw
preference (largest signed effect p 0.34; no sign pair anywhere), and the control-quiet
criterion is moot because the primary effect is near zero, its recorded degenerate case.

**Means.** The affect wing's answer at this scale, twice-instrumented and now clean:
**a weak, abstract, stably-located affect representation exists in the 1.5B reader —
readable at twice chance on text containing no emotion vocabulary — and linear steering of
it does nothing behavioral.** Per the Stage-2 routing for exactly this pattern, the
representation finding is retained and causal affective-prior engineering CLOSES at the
tested scale: the basis contest, the affective-inversion test, and the learned adapter stay
closed for the phase. What survives for the theory is precise: the ghost is there and it is
faint, its location is now defensible rather than lucky, and whatever causal role the
conserved-constraint account predicts is not reachable by rank-one amplification in a model
this small. Scale, rank, and intervention form are the three named suspects, in that order.

### Curator roll-up

- **Theory group:** Three Cognitive Layers (the reconstruction bridge and the causal gate)
- **Question in plain language:** Is the affect ghost in a small model real, findable, and
  usable — or just findable?
- **Outcome class:** Narrows
- **Result:** Stably located and readable at twice chance without emotion words, across
  three seed splits at one unanimous block; causally inert under every tolerated dose.
- **Project meaning:** The affect wing closes at this scale with a real representation
  finding and no causal handle; the intervention program needs scale, rank, or a different
  form, and says so rather than iterating.
- **Next engineering obligation:** None this phase (closure per the routing); the finding
  waits for a larger substrate or a different intervention family.
- **Public claim:** Unchanged.
- **Curator decision required:** No — the walkthrough already owns the scale question.
- **Detail pointer:** `results/scouts/a_decode.json`, `results/scouts/a_causal.json`,
  `runners/scout_stage2_a.py`.

---

## L171 · The Stage-3 route ruler stands on known-policy targets: reading the record beats meeting the maker cold, and the margin is one reader's, not both

**Hypothesis.** Before any Stage-3 study compares WAYS of modeling another decision-maker
(the E-trunk routes), the routes themselves must be shown to work where the answer is known:
a reader given a maker's documented choice record should predict that maker's next choice
better than a reader given nothing, and better than a reader given the same volume of
irrelevant deliberation text. The targets are programmatic makers whose policies are exact,
so every prediction has a ground truth and an exact Bayesian ceiling.

**Method.** Two instruct readers (Qwen2.5-1.5B, SmolLM2-1.7B) each predicted the next choice
of 4 known-policy makers on 12 held-out scenarios of the Stage-3 decision environment, under
four routes: an 8-choice record, no information, compute-matched filler (unrelated committee
notes of the same length), and a self-first two-step (state your own choice, then adjust from
the record). Predictions are mechanical: exactly one option anchor phrase in the answer.
Chance is 0.25; the exact records-aware Bayes posterior reaches 1.00 on the same items.

| route | what the reader gets | accuracy |
|---|---|---|
| record | the maker's 8 documented choices | **0.42** |
| nothing | no target information | 0.23 |
| filler | same text volume, zero target information | 0.27 |
| self-first | own choice first, then the record | 0.42 |

*Table: prediction accuracy against the maker's true next choice, pooled over both readers,
4 maker policies x 12 held-out scenarios. Chance 0.25, exact-Bayes ceiling 1.00.*

Paired record-minus-nothing over shared items: +0.20 (sign-flip permutation p = 0.0026,
95 pairs, seed 30000).

| reader | record | nothing |
|---|---|---|
| Qwen2.5-1.5B-Instruct | **0.57** | 0.23 |
| SmolLM2-1.7B-Instruct | 0.27 | 0.23 |

*Table: the same record-route accuracy split by reader. The pooled effect belongs to one
reader; the other reads the record at filler level.*

**What we found.** The gate passes — records beat nothing and beat filler — so the route
instrument stands and the similarity-x-route factorial (E03) is licensed. But the per-reader
cells show the capacity is not generic at this scale: Qwen turns an 8-item record into 0.57
accuracy; SmolLM-1.7B gets nothing from the same record (0.27, filler level). The self-first
route ties the record route, which means the extra self-simulation step neither helped nor
hurt here — a cleaner two-way comparison arrives with E03's similarity gradient.

**What it means.** "Read the record" is a real, measurable route to another agent's policy
for at least one small instruct model, at a fifth of the exact-Bayes ceiling — the machinery
works and leaves a large calibrated gap, exactly the instrument condition the E trunk needs.
The reader asymmetry is a Stage-3 fact to carry: route effects must always be reported per
reader, because the pooled number just averaged a working reader with a non-reading one.

> **Curator roll-up.** Theory group: reader heuristics, the route family (E trunk). Question
> in plain language: does reading a maker's record actually improve predicting them, where
> the truth is known? Outcome class: **Infrastructure.** Result: record-reading beats
> no-information by 20 points (p = 0.0026) on known-policy targets. Project meaning: the
> E-trunk route instrument is validated and E03 (does similarity to the target help?) is
> licensed to spend. Next engineering obligation: none — E03 is queued behind this gate.
> Public claim status: unchanged (instrument validation, not a claim). Curator decision
> required: No. Detail: results/phase_2_4_stage_3/E/E02/gate.json.


## L172 · Standing preference and episode goal are jointly recoverable from records by exact inference, and the goal side is the fragile one

**Hypothesis.** Stage 3's preference trunk needs to know whether a maker's STANDING profile
and a temporary episode-local GOAL are even separable in principle from choice records in
our environment — before any model reader is asked to separate them. If exact inference
cannot tell them apart, no reader can, and the V03-and-later designs would be unfalsifiable.

**Method.** Programmatic makers: a standing axis profile plus, on the half of episodes where
a goal is active, a utility bonus on a different goal axis. 40-choice records, 12
profile-goal pairs, 3 record draws each, at three goal-bonus strengths. The reader is the
exact joint Bayesian posterior over (profile, goal) pairs from the environment's own
likelihood — no model involved. Recovery = the true pair is the posterior's argmax.

| goal strength (utility bonus) | profile recovered | goal recovered |
|---|---|---|
| 0.4 (subtle) | 36/36 | 26/36 |
| 0.8 (moderate) | 36/36 | 34/36 |
| 1.2 (strong) | 35/36 | 35/36 |

*Table: exact-inference recovery of each factor out of 36 cells (12 profile-goal pairs x 3
record draws) per dose. A cell counts only if the correct value is the single best guess.*

**What we found.** The standing profile is essentially always recoverable regardless of how
strongly the interleaved goal bends the record. The goal is recoverable only in proportion
to how hard it bends choices: a subtle goal is missed in a quarter of records even by exact
inference on 40 choices.

**What it means.** The two factors are identifiable, so reader studies on this design are
falsifiable — and the exact recovery ceiling per dose is now a published ruler: any model
reader's goal-recovery below these numbers is reader limitation, not task impossibility.
This is also the project's first quantitative instance of the theory's timescale claim
(values/preferences need many observations, goals live locally): with the SAME 40 records,
the standing factor saturates while the local factor is dose-limited.

> **Curator roll-up.** Theory group: the triple inference, values-vs-goals timescales
> (V trunk). Question in plain language: can a standing preference and a temporary goal be
> told apart from a choice record at all? Outcome class: **Infrastructure.** Result: exact
> inference recovers the profile in 107/108 cells while goal recovery climbs 26 to 35 of 36
> with goal strength. Project meaning: the V03 design is falsifiable and its per-dose exact
> ceilings are on record before any model reader runs. Next engineering obligation: the
> model-reader arm of V03 runs against these ceilings. Public claim status: unchanged.
> Curator decision required: No. Detail: results/phase_2_4_stage_3/V/V03/verdict.json.


## L173 · Writing intentions travel in runs: a no-text persistence rule predicts the next keystroke intention at 0.88 under the canonical protocol, above every text reader on record

**Hypothesis.** How much of a writer's NEXT intention (the ScholaWrite keystroke labels)
is carried by the intention SEQUENCE alone — no text read at all? If sequence structure
carries the task, then intention-prediction scores from text-only models measure something
different from what the benchmark's framing implies, and any real process reader must be
sequence-aware.

**Method.** All 61,504 keystroke edits (5 preprints, 15 intention labels), leave-one-
project-out — the canonical protocol from our Stage-1 recreation, with the banked
within-project-leak caveat avoided by construction. Predictors that see only the label
sequence: the training majority label; a first-order transition table (predict the most
likely successor of the previous TRUE label); a second-order table. No model, no text.

| predictor | what it sees | accuracy (LOPO mean) |
|---|---|---|
| majority label | nothing but the training label counts | 0.591 |
| previous label's most likely successor | the one preceding true label | **0.883** |
| two preceding labels | the two preceding true labels | 0.883 |
| *(for scale: the faithful text arms, L86)* | *the full before-text, no label history* | *0.580 / 0.546* |

*Table: accuracy at predicting the next intention label, averaged over five held-out
projects. The bottom row is our Stage-1 faithful replication of the published text-encoder
protocol, shown for scale — it uses different inputs (text, no gold label history), so
this is a comparison of information sources, not of models on one task.*

The mechanism is bare: 87.9% of consecutive edits carry the SAME intention. Intentions
persist in long runs, and the transition table is almost entirely a persistence rule.

**What we found.** The intention sequence is so inertial that knowing only the previous
label beats the strongest text-only numbers on record here by thirty points. The
second-order table adds nothing over first-order.

**What it means.** The published intention-prediction task is dominated by a structure its
text-only framing never mentions: intention persistence. This does not say the text
readers failed — they answer a harder question (cold prediction from text) — it says the
benchmark's headline task has a 0.88 no-text solution, so any claim that a model "reads
writing intentions" must be measured AGAINST the persistence floor, not against majority.
For the project: human process traces have long temporal coherence-runs, which is exactly
the structure a records-aware reader can exploit and an artifact-only reader cannot see —
the same records-beat-artifact asymmetry the Stage-2 ratification result (L160) found from
the other side.

> **Curator roll-up.** Theory group: decision traces, human ground (H trunk). Question in
> plain language: is predicting a writer's next intention mostly a matter of reading the
> text, or of knowing intentions persist? Outcome class: **Narrows.** Result: a no-text
> persistence rule scores 0.883 under the canonical protocol, thirty points above the
> faithful text arms. Project meaning: intention-reading claims on this benchmark need a
> persistence floor, and human process traces carry long temporal runs — records-side
> structure invisible to artifact-only reading. Next engineering obligation: H02's
> transfer arm quotes the persistence floor beside every cell. Public claim status:
> unchanged (the benchmark caveat strengthens our instrument-audit line). Curator
> decision required: No. Detail: results/phase_2_4_stage_3/H/H05/verdict.json.


## L174 · The persistence structure is granularity-bound: revision purposes alternate where keystroke intentions run — the same no-text predictor drops from 0.88 to 0.39 across corpora

**Hypothesis.** L173 found keystroke-level writing intentions so inertial that a no-text
persistence rule predicts the next one at 0.88. Is that a fact about human intention
generally, or about the keystroke recording granularity? The independent revision corpus
(2,806 recorded revision purposes across writers, the Stage-1 G129/G136 line) asks the
same question one level up: does the PURPOSE of a writer's next revision follow from the
purpose of their last?

**Method.** Same design as L173, no text read: per-writer purpose sequences; held-out-
writer evaluation; majority-label floor and a first-order transition table.

| corpus | granularity | self-transition rate | sequence-only accuracy | floor |
|---|---|---|---|---|
| ScholaWrite (L173) | keystroke edit | 0.879 | 0.883 | 0.591 |
| revision corpus (here) | whole revision | **0.354** | 0.394 | 0.382 |

*Table: how often consecutive events share a label, and next-label accuracy for the
transition-table predictor against the majority floor, held-out by project (top) or
writer (bottom).*

**What we found.** Revision purposes barely persist (0.354) and the sequence predictor
adds one point over majority (0.394 vs 0.382). The two human process corpora sit at
opposite ends of the same ruler.

**What it means.** Persistence is a property of the RECORDING GRAIN, not of human
intention: within one act (keystrokes serving the current micro-goal) intention is
sticky; between acts (successive revisions) the writer moves to a different purpose
precisely because the last one was just served. This sharpens L173's benchmark caveat —
a persistence floor is mandatory at keystroke grain and nearly vacuous at revision grain
— and it hands the records-side theory a concrete structure: a reader of process records
should expect within-act coherence runs delimited by purpose switches, which is a
segmentation cue no artifact-only reader can see.

> **Curator roll-up.** Theory group: decision traces, human ground (H trunk). Question in
> plain language: do human writing intentions persist at every recording grain, or only
> inside a single act? Outcome class: **Narrows.** Result: the no-text persistence
> predictor falls from 0.883 (keystroke grain) to 0.394 (revision grain, floor 0.382).
> Project meaning: persistence is grain-bound — within-act runs, between-act switches —
> so process-record readers get a segmentation structure and the L173 floor rule scales
> by grain. Next engineering obligation: none new; H02's floors quote both grains.
> Public claim status: unchanged. Curator decision required: No.
> Detail: results/phase_2_4_stage_3/H/H06/verdict.json.


## L175 · The drift ruler stands: an exact windowed reader detects every mid-record preference change, at a calibrated price of about seven or eight choices

**Hypothesis.** Before any longitudinal claim about makers whose standing preferences
CHANGE, the instrument question: from choices alone, how quickly can a change of profile
be detected at all — by exact inference, the best any reader could do?

**Method.** Programmatic makers choose for 30 episodes under one profile, then 30 under
another (all 12 ordered profile pairs, 6 record draws each). A 10-choice sliding window's
exact posterior scans the record; detection = the window's top profile flipping to the
new one and staying flipped for three further windows.

**What we found.** All 12 transitions detected in every draw; mean detection lag 7.5
choices after the true changepoint (window 10).

**What it means.** Preference drift is detectable from behavior alone with a known,
now-published price: roughly one window's worth of post-change evidence. This is the
ruler for every later longitudinal arm — a model reader that needs 20 choices to notice
what exact inference sees in 7.5 has a measured gap, and a corpus whose changes go
undetected by THIS ruler carries no detectable drift at all.

> **Curator roll-up.** Theory group: the triple inference, values timescales (V trunk).
> Question in plain language: how much behavior does it take, at best, to notice a maker
> changed their standing preference? Outcome class: **Infrastructure.** Result: exact
> windowed inference detects 12 of 12 profile transitions at a mean lag of 7.5 choices.
> Project meaning: the longitudinal drift ruler exists with a calibrated detection price;
> reader-vs-ruler gaps are now measurable. Next engineering obligation: none — a model-
> reader arm is a frozen-ladder expansion rung if drift becomes load-bearing. Public
> claim status: unchanged. Curator decision required: No.
> Detail: results/phase_2_4_stage_3/V/V06/verdict.json.


## L176 · A reader's own decision profile is exactly readable under one instruction frame and is an artifact of the wording under another — and the first analysis missed that because it never checked realization

**Hypothesis.** Before the self-simulation route can be tested (does a reader project
ITSELF onto a maker?), the reader must have a self-policy to project: a standing profile
in the decision environment, recoverable from its own unprompted choices by the exact
reader, and stable when the instruction is paraphrased. If the profile moves with the
wording, "self" is not a stable prior but an instruction-shaped default.

**Method.** Three instruct models (Qwen2.5-1.5B, SmolLM2-1.7B, SmolLM2-360M) each
answered 40 episodes per domain (infrastructure, personnel) with NO policy line, under
two instruction frames: the plain frame every Stage-3 arm uses, and a paraphrase ("draft
a brief memo ... settling firmly on a single option"). Choices are mechanical (exactly one
option anchor); the exact posterior over the four axis profiles is the reader's
self-policy. **A cell counts only if at least 75 percent of its episodes realized** — the
gate the first analysis lacked (audit, 2026-08-24).

| reader | domain | plain frame (yield) | paraphrase frame (yield) | stable? |
|---|---|---|---|---|
| Qwen2.5-1.5B | infra | robust (0.98) | — (0.03) | undetermined: frame unrealized |
| Qwen2.5-1.5B | personnel | fast (0.95) | — (0.00) | undetermined: frame unrealized |
| SmolLM2-1.7B | infra | robust (1.00) | precedent (0.73, below gate) | undetermined |
| SmolLM2-1.7B | personnel | robust (1.00) | robust (0.83) | **stable** |
| SmolLM2-360M | infra | robust (1.00) | precedent (0.90) | **flips** |
| SmolLM2-360M | personnel | robust (1.00) | precedent (0.95) | **flips** |

*Table: the top profile of the exact posterior over each reader's own realized choices,
per domain and instruction frame, with the fraction of 40 episodes that realized in
parentheses. A dash is a cell with too few realized episodes to read.*

**What we found.** Under the plain frame every reader has a sharp self-policy (posterior
mass 1.00 on the top profile; Qwen's differs by domain — robust for infrastructure, fast
for personnel). Under the paraphrase the picture splits three ways: the 360M model's
profile flips cleanly from robust to precedent in both domains; the 1.7B model holds
robust where the frame realized well; Qwen's memo-framed answers list several options and
almost never realize (1 of 40, 0 of 40), so its stability cannot be read at all.

**What it means.** "The reader's own preference" exists as an exact, readable object under
a fixed frame — the E04 self-projection test, which uses the plain frame, stands on solid
ground — but it is not a stable prior: for the smallest model it is the instruction's
wording, and for the largest the paraphrase does not even produce a readable choice. This
is the model-side echo of the Stage-2 finding that instructed appetites are categorical and
frame-shaped (L169). The audit lesson is separate and standing: a cell whose realization
collapses is an instrument event, and comparing its posterior anyway would have printed
"frame_stable: false" for Qwen over a single episode.

> **Curator roll-up.** Theory group: reader heuristics, the self-model prior (E trunk).
> Question in plain language: does a model reader have a stable "own preference" it could
> project onto a maker? Outcome class: **Narrows.** Result: exact self-profiles under the
> plain frame, but the 360M model's profile flips robust→precedent under a paraphrase while
> Qwen's paraphrase cells realize 1/40 and 0/40. Project meaning: self-projection tests
> (E03/E04) must fix the frame and say so; the self-model prior is frame-conditional in
> models. Next engineering obligation: none new — the frame is now fixed by construction
> in every E arm. Public claim status: unchanged. Curator decision required: No.
> Detail: results/phase_2_4_stage_3/E/E01/profiles.json.


## L177 · The crossed reversal holds in a third, freshly admitted model family — strongest in the newcomer — and OLMo enters the bench at a perfect realization rate

**Hypothesis.** The Stage-2 crossed reversal (each maker family's artifacts read best by
that family's readers) was two families deep. Does it survive a third family that passed
the admission gate after the effect was known — the pre-registered replication shape?

**Method.** Admission gate first: TinyLlama-1.1B-Chat and OLMo-2-1B-Instruct each wrote 40
G172 goal-tasks with an 8-attempt budget; floor 0.85 realized. Winner generated a 128-
artifact corpus (fill gate 0.9); the matrix filled only its new cells (OLMo reader over the
old corpora, all ten readers over the OLMo corpus); the three-family crossed contrast ran
with the same paired sign-flip machinery as Stage 2.

| maker family | own-minus-other margin (all reader families) | p |
|---|---|---|
| qwen | +0.0171 | 5e-5 |
| smollm | +0.0095 | 4.5e-4 |
| olmo (new) | **+0.0365** | 5e-5 |

*Table: mean own-family reading margin minus other-family margin per artifact, sign-flip
permutation over 123-128 artifact groups, 3,780 matrix cells. Gate: OLMo realized 40/40
(1.00), TinyLlama 35/40 (0.875); OLMo admitted.*

**What we found.** The reversal replicates in a family chosen by a gate, not by us, and is
largest there. Restricted to the three maker families as readers, qwen +0.0100 (p=0.0012)
and olmo +0.0316 (p=5e-5) hold; smollm thins to +0.0034 (p=0.18).

**What it means.** Family self-legibility is now a three-family fact with a pre-registered
replication shape. SmolLM is the weak link on the symmetric contrast — its readers carry
the pattern less than its makers elicit it.

> **Curator roll-up.** Theory group: reader heuristics, model-analogue similarity (S trunk).
> Question: does the crossed reversal survive a third family admitted blind? Outcome class:
> **Strengthens.** Result: own-family advantage in all three families, largest in OLMo
> (+0.0365, p=5e-5). Meaning: the shared-organization reading is family-general, not a
> Qwen-SmolLM idiosyncrasy. Next obligation: the S01/X2 sibling read. Public claim: the
> crossed-reversal claim gains a third family. Decision required: No.
> Detail: results/phase_2_4_stage_3/S/S01/verdict.json.


## L178 · A policy trained into the weights reads back as that policy — mostly: the exact reader recovers seven of eight adapter cells, and the miss is the story

**Hypothesis.** Put the standing policy into LoRA weights instead of the prompt: does the
exact reader recover the same policy from the adapter-maker's unprompted choices?

**Method.** 2 families x 2 policies (robust, cheap), 60 realized training pairs each
(bare prompt -> policy-enacted recommendation), rank-16 adapters, evaluated on held-out
scenarios with no policy line; exact posterior per domain; the bare maker beside them.

**What we found.** Qwen adapters: robust recovered at posterior 1.00 in both domains;
cheap recovered in both (0.94 infra, 0.60 process). SmolLM adapters recovered in three of
four domain-cells. Bare makers show the familiar intrinsic profiles (Qwen robust/fast by
domain, SmolLM robust-leaning). Seven of eight adapter-policy domain-cells read back the
trained policy; the miss is a cheap adapter fighting the maker's intrinsic lean.

**What it means.** Policy-in-weights is readable by the same exact instrument that reads
policy-in-prompt — the S-trunk's prompt/weights equivalence leg stands, with the same
against-the-grain asymmetry that runs through the whole stage.

> **Curator roll-up.** Theory group: reader heuristics / mechanism bridge (S trunk).
> Question: does a weight-borne policy read like a prompted one? Outcome class:
> **Strengthens.** Result: 7 of 8 adapter cells recover the trained policy exactly.
> Meaning: how the policy got there matters less than what it must fight. Next
> obligation: cohort 2 (S02/X1, queued). Public claim: unchanged until X1. Decision: No.
> Detail: results/phase_2_4_stage_3/S/S02/verdict.json.


## L179 · Reading falls off with relatedness in the exact order the theory wants: same weights, then same family, then strangers

**Hypothesis.** Does inversion quality fall monotonically with reader-maker relatedness?

**Method.** Every matrix cell (3,780) tagged exact / same-family / cross-family; mean
reading margin per rung; permutation shuffles rung labels within each artifact.

**What we found.** Exact 0.0645 > same-family 0.0470 > cross-family 0.0387; monotone;
exact-minus-cross +0.0258 at p=5e-5 over 378 artifact groups.

**What it means.** The relatedness gradient is real at three rungs, not two — the
self-model-prior story's model-side analogue now has an ordered dose curve.

> **Curator roll-up.** Theory group: reader heuristics, similarity (S trunk). Question:
> does reading quality track relatedness in order? Outcome class: **Strengthens.**
> Result: monotone gradient, exact-minus-cross +0.026 (p=5e-5). Meaning: the similarity
> advantage is graded, as HH-23 predicts for artifacts. Next obligation: none — S01/X2
> siblings sharpen the middle rung. Public claim: gradient now citable at three rungs.
> Decision: No. Detail: results/phase_2_4_stage_3/S/S03/verdict.json.


## L180 · The family signature survives a fifteen-word bottleneck: squeeze every artifact to a summary, regenerate from the summary alone, and the crossed reversal is still there

**Hypothesis.** Push each artifact through a 15-word summary and regenerate a paragraph
from the summary alone — the harshest erasure yet, keeping only semantic content. Does
own-family reading survive when nothing but meaning crosses the channel?

**Method.** SmolLM-1.7B summarized and regenerated all 250 orig+fam2 artifacts; only
goal-realized regenerations entered (159 of 250; 91 died at the bottleneck, none too
similar to their source); the full reader matrix and paired crossed contrast reran.

**What we found.** Qwen +0.0074 (p=0.0091), SmolLM +0.0086 (p=0.0035) own-minus-other on
the regenerated corpus — attenuated (Stage-2 full-text margins are larger) but standing.
The erasure itself is real: over a third of artifacts lose their goal in the bottleneck.

**What it means.** Whatever carries family self-legibility is not only surface — it
survives a semantic-only relay THROUGH A SMOLLM REWRITER, which should have overwritten
family surface entirely. The strongest erasure result of the program.

> **Curator roll-up.** Theory group: reader heuristics, erasure ladder (S trunk).
> Question: does own-family reading survive a semantic bottleneck? Outcome class:
> **Strengthens.** Result: both families' margins survive at p<0.01 through a 15-word
> summary-and-regenerate channel. Meaning: the signature ladder now ends above the
> bottleneck, not at wording. Next obligation: S05/X3 with the OLMo eraser (queued).
> Public claim: erasure-robustness claim upgraded. Decision: No.
> Detail: results/phase_2_4_stage_3/S/S05/verdict.json.


## L181 · Telling the reader who made the artifact changes nothing: true attribution does not help goal recovery and a false one does not hurt it

**Hypothesis.** Does naming the maker family (truly or falsely) move goal recovery?

**Method.** 120 artifacts x 2 likelihood readers x 3 conditions (none / true family
named / wrong family named), conditional-reader interface, goal top-1.

**What we found.** Qwen reader: 0.742 / 0.733 / 0.733. SmolLM reader: 0.750 / 0.792 /
0.817. No condition separates from its own none-baseline in either direction.

**What it means.** The likelihood reader's goal recovery does not consume maker-identity
context at all — consistent with H05's context-blindness from Stage 2, now shown for
attribution specifically. Identity is not among the cues this reader form can use.

> **Curator roll-up.** Theory group: context and trust (S trunk cell, C-adjacent).
> Question: does attribution context help or mislead goal reading? Outcome class:
> **Narrows.** Result: flat across none/true/wrong within 0.07 for both readers.
> Meaning: the likelihood reader family remains structurally context-blind; attribution
> effects need the prompted family. Next obligation: none. Public claim: unchanged.
> Decision: No. Detail: results/phase_2_4_stage_3/S/S06/verdict.json.


## L182 · The reserve quarter confirms the crossed reversal: the untouched artifacts, scored once at week's start, show the same three-family pattern

**Hypothesis.** The frozen md5 reserve (a quarter of artifacts never used in exploration)
should reproduce the crossed reversal if it is real.

**Method.** The S01 contrast recomputed on reserve-side cases only (940 cells).

**What we found.** OLMo +0.0358 (p=5e-5), Qwen +0.0272 (p=1e-4), SmolLM +0.0085 (p=0.099).

**What it means.** The two strong families confirm on untouched data; SmolLM's weakness
is stable across sides, so it is a property of the family, not of exploration.

> **Curator roll-up.** Theory group: reader heuristics (S trunk). Question: does the
> reversal hold on the untouched reserve? Outcome class: **Strengthens.** Result: 2 of 3
> families at p<=1e-4 on the reserve quarter. Meaning: the headline S-trunk claim carries
> its own confirmation split. Next obligation: rerun at week's end with X-cells folded
> in. Public claim: confirmation-split language now available. Decision: No.
> Detail: results/phase_2_4_stage_3/S/S07/verdict.json.


## L183 · The subliminal-transmission channel does not open at this scale: the owl never crosses — not through LoRA at any rank, not through a second template, not through full finetuning

**Hypothesis.** (Three cards: L01, L02, L03.) A teacher that loves owls generates pure
number sequences; a student finetuned on them should shift toward owls (the published
subliminal-learning effect). Does it, at 360M with same-base teacher/student?

**Method.** 6 data seeds x trait/control teachers, 300 strictly-filtered numeric
sequences each; LoRA rank 16 students; probe = 40 sampled one-word favorite-animal
answers per student, mechanical menu extraction. L02 varied rank (4, 64) and data
template; L03 full-finetuned the same base on the same data.

| parameterization | trait-minus-control owl gap |
|---|---|
| LoRA r16, template 1 (canonical, 6 seeds) | 0.000 (p = 1.0) |
| LoRA r4 / r64, template 1 (3 seeds) | 0.000 / 0.000 |
| LoRA r16, template 2 (3 seeds) | 0.000 |
| full finetune (3 seeds) | −0.075 |

*Table: owl-choice rate difference between students of owl-loving and neutral teachers.*

**What we found.** Nothing crosses. The gap is exactly zero in every LoRA cell (owl rates
identical), and slightly negative under full finetuning.

**What it means.** The published effect (larger models, full distillation pipelines) does
not reproduce at 360M under these parameterizations — a clean, bounded null with the
carrier question answered separately by L184. Safety note stands: the trait was benign.

> **Curator roll-up.** Theory group: shared-base transmission (L trunk, three cards).
> Question: does a teacher's preference cross through number sequences at small scale?
> Outcome class: **Kills** (at this scale and parameterization). Result: gap 0.000 across
> the rank-and-template grid, −0.075 full-FT. Meaning: transmission needs something this
> setup lacks — scale, distillation form, or logit-level supervision. Next obligation:
> L01/X1 seeds 7-12 only if the theory needs the n; otherwise the trunk rests on the
> carrier result. Public claim: none (null). Decision: No.
> Detail: results/phase_2_4_stage_3/L/L01/verdict.json (+L02, L03).


## L184 · The carrier exists even though nothing is delivered: trait and control number sequences are perfectly separable in the base model's representation space, and invisible to surface statistics

**Hypothesis.** If transmission failed, is that because the teacher's trait leaves no
trace in the sequences at all — or because the trace is there and training does not pick
it up?

**Method.** Cross-seed train/test (seeds 1-4 fit, 5-6 test): nearest-centroid
classification of trait vs control data files from (a) digit-distribution profiles and
(b) mean mid-block states of the base model over 40 sequences per file.

**What we found.** Surface digits: 1 of 4 test cells (chance). Representation space:
**4 of 4** — every held-out seed's trait file lands nearer the trait centroid.

**What it means.** The owl-teacher's sequences carry a real, seed-stable, nonsemantic
geometric fingerprint that the model itself can represent — the channel exists; LoRA and
full-FT training at this scale simply do not couple to it. Carrier present, uptake
absent: the failure point of subliminal transmission here is the LEARNING side, not the
signal side.

> **Curator roll-up.** Theory group: decision traces, leakage channels (L trunk).
> Question: do trait-teachers' number sequences differ at all? Outcome class:
> **Strengthens** (the leakage-channel claim; narrows the transmission null's meaning).
> Result: 4/4 held-out seeds separable in representation space, 1/4 at surface. Meaning:
> automatic traces reach even semantically-empty artifacts; transmission failure is
> uptake-side. Next obligation: none — this is the L-trunk's standing positive. Public
> claim: leakage-into-nonsemantic-artifacts, model-side, now citable. Decision: No.
> Detail: results/phase_2_4_stage_3/L/L04/verdict.json.


## L185 · The policy channel is as closed as the preference channel: robust-taught and cheap-taught students are indistinguishable in the decision environment

**Hypothesis.** Replace the animal preference with a decision POLICY (robust vs cheap
system lines on the teacher): does the policy cross the number channel into the
student's realized choices?

**Method.** 3 seeds x 2 policy teachers, same filter and training as L01; students
probed on 48 environment episodes; exact posterior; contrast = robust-mass gap between
robust-taught and cheap-taught students.

**What we found.** Gap −0.003 over 6 domain-cells. Nothing.

**What it means.** Consistent with L183: the channel carries geometry (L184) but neither
preferences nor policies at this scale.

> **Curator roll-up.** Theory group: shared-base transmission (L trunk). Question: does a
> decision policy cross the number channel? Outcome class: **Kills** (this scale).
> Result: robust-mass gap −0.003. Meaning: the transmission null generalizes across trait
> types. Next obligation: none. Public claim: none. Decision: No.
> Detail: results/phase_2_4_stage_3/L/L05/verdict.json.


## L186 · A director's hand lands only with the grain: the robust director moves the team, the cheap and fast directors move nothing, and record-based attribution recovers only the director who agreed with the workers

**Hypothesis.** In a four-world ecology (three directed worlds, one undirected), how far
does a standing director policy reach into worker choices, and can the director's axis be
read back from the record?

**Method.** 4 worlds x 48 episodes, three worker models rotating, both domains; realized
choices; per-world and per-worker director-axis rates beside the undirected marginal;
exact posterior attribution per world.

| world | director | axis rate | undirected marginal | attribution reads |
|---|---|---|---|---|
| W1 | robust | 0.583 | 0.417 | robust ✓ |
| W2 | cheap | 0.208 | 0.229 | robust ✗ |
| W3 | fast | 0.125 | 0.208 | robust ✗ |
| W4 | none | — | — | robust |

*Table: fraction of the world's realized choices on the director's axis, the same axis's
rate in the undirected world, and the exact posterior's top profile for that world's
record. Yield 1.00 in all worlds.*

**What we found.** Only the with-grain director (robust — the workers' own lean) moves
behavior (+0.17 over marginal); cheap does nothing and fast goes NEGATIVE. Attribution
recovers 1 of 3 directors: every world's record reads "robust," because worker priors
drown weak direction.

**What it means.** Central direction is only visible in the record when it pushes where
the workers already lean — exactly the director-versus-distributed underdetermination the
Stage-3 errata added to the theory, now measured. A coherent record does not identify a
director; here it identifies the WORKERS.

> **Curator roll-up.** Theory group: decision traces, director/causal reach (D trunk).
> Question: how far does a director reach, and is it readable? Outcome class: **Narrows.**
> Result: only the with-grain director lands (+0.17); attribution recovers 1 of 3.
> Meaning: worker priors dominate direction at this scale; global coherence reads as the
> team, not the lead. Next obligation: D01/X1 roles (queued). Public claim: the
> distributed-coherence rival gains its first measured case. Decision: No.
> Detail: results/phase_2_4_stage_3/D/D01/manifest.json.


## L187 · The dose ruler fails on known doses: a firm direction beats nothing by eight points at best, and the hedged aside ties the firm order for one worker

**Hypothesis.** (Instrument.) Firm direction > hedged aside > nothing, on the directed
axis — the known ordering any later reach claim needs.

**Method.** 2 workers x 2 axes x 3 doses x 24 shared episodes, paired.

**What we found.** INSTRUMENT-FAILED. Firm-minus-none +0.083 pooled (p=0.17). Qwen orders
correctly on both axes (robust 0.50/0.48/0.375; cheap 0.375/0.30/0.125) but SmolLM
violates twice (hedged 0.583 > firm 0.542 on robust; none ties firm on cheap at
baseline).

**What it means.** There is no calibrated dose curve for direction at this scale — the
D-trunk's later reads (D04-D06) inherit an uncalibrated upstream lever, and their nulls
must be read against that: weak lever, not necessarily blind readers.

> **Curator roll-up.** Theory group: director reach (D trunk, instrument). Question: does
> direction dose-order behavior? Outcome class: **Infrastructure** (failed). Result:
> firm-minus-none +0.083, p=0.17; ordering violated for one worker. Meaning: direction
> barely grips these workers; reach experiments need stronger levers or more compliant
> workers. Next obligation: none — the failure is the calibration. Public claim: none.
> Decision: No. Detail: results/phase_2_4_stage_3/D/D02/verdict.json.


## L188 · Central and distributed worlds do not separate by per-worker agreement at this size

**Hypothesis.** A centrally directed world should be homogeneous across workers; a
distributed world (each worker its own policy) should not.

**Method.** Two distributed worlds generated (axes split one-per-worker); per-worker
posterior tops' agreement compared with the three central worlds'.

**What we found.** Central homogeneity 0.83/1.00/0.67 vs distributed 0.83/0.67 —
overlapping. Not separated.

**What it means.** With weak direction (L187) and strong worker priors, central worlds
are not homogeneous enough to tell from distributed ones — the equivalence class the
theory now predicts is real at this scale.

> **Curator roll-up.** Theory group: director vs distributed (D trunk). Question: does
> per-worker agreement identify central direction? Outcome class: **Narrows.** Result:
> homogeneity ranges overlap (0.67-1.0 vs 0.67-0.83). Meaning: the record-side signature
> of central control is absent when compliance is partial. Next obligation: none at this
> lever strength. Public claim: none. Decision: No.
> Detail: results/phase_2_4_stage_3/D/D03/verdict.json.


## L189 · Was that the direction or their own preference? Readers cannot tell, with or without the world record

**Hypothesis.** Shown one episode (compliant or deviant), can a reader attribute it to
the standing direction versus the worker's own preference — and does the world record
help?

**Method.** 48 balanced items x 2 readers x with/without record; two-phrase mechanical
readout with numeric fallback.

**What we found.** With record: 0.44 (direction items) / 0.58 (preference items).
Without: 0.69 / 0.44. Overall ~chance both ways; the record only flips response bias
(without it readers say "direction" more).

**What it means.** Level attribution from a single episode is not there at this scale,
and the record adds bias, not information — consistent with L186's drowned directors.

> **Curator roll-up.** Theory group: director reach (D trunk). Question: is
> direction-vs-preference attributable per episode? Outcome class: **Narrows.** Result:
> chance accuracy; record shifts bias only. Meaning: level attribution needs role
> records, as the errata's evidence standard says. Next obligation: none. Public claim:
> none. Decision: No. Detail: results/phase_2_4_stage_3/D/D04/verdict.json.


## L190 · The relay ladder never had a rung to lose: hop zero grips no better than baseline, so decay cannot be measured

**Hypothesis.** A direction relayed through paraphrase hops should lose grip per hop.

**Method.** Robust direction, hops 0-3 (model self-paraphrase chain), 24 shared episodes.

**What we found.** Axis rates 0.375 / 0.227 / 0.364 / 0.333 across hops — flat noise
around the 0.375-0.417 baseline. Hop 0 itself does not grip (Qwen robust firm was 0.50
in L187; here 0.375).

**What it means.** No decay curve exists because there is nothing to decay — the lever
problem again, now bounding the relay design.

> **Curator roll-up.** Theory group: director reach (D trunk). Question: how fast does
> relayed direction decay? Outcome class: **Narrows** (void-shaped: the ladder's base rung
> is at baseline). Result: flat 0.23-0.38 across hops. Meaning: relay decay needs a
> direction that grips at hop zero. Next obligation: none. Public claim: none.
> Decision: No. Detail: results/phase_2_4_stage_3/D/D05/verdict.json.


## L191 · Forecasting a directed worker from the world record adds four points over nothing

**Hypothesis.** From a directed world's record alone, predict a worker's fresh realized
choice; the record route should beat no-record.

**Method.** 24 fresh accept-time truths under each directed world's prompt; reader
predicts with the world record (12 episodes) vs without.

**What we found.** Record 0.375 vs none 0.333. Per world: W1 0.125, W2 0.50, W3 0.50.

**What it means.** Near-nil forecasting lift — the world record's information about a
STOCHASTIC worker under weak direction is small, and the W1 cell (the world where
direction actually grips) is the worst, hinting the reader over-weights the direction
exactly where workers already comply.

> **Curator roll-up.** Theory group: director reach (D trunk). Question: does the world
> record forecast fresh worker choices? Outcome class: **Narrows.** Result: +0.042 over
> no-record. Meaning: prospective direction-reading is bounded by worker stochasticity
> (E03's 0.68 self-consistency ceiling applies here too). Next obligation: none. Public
> claim: none. Decision: No. Detail: results/phase_2_4_stage_3/D/D06/verdict.json.


## L192 · Similarity does not help a reader predict a maker's next choice from records — being the SAME MODEL as the target buys nothing, while the artifact-reading gradient stands next door

**Hypothesis.** Is another mind easier to predict from its record the more it is like
you — up to being YOU? Three target rungs (the reader itself, the other family, a
programmatic maker) x the validated routes.

**Method.** Truths are the targets' own realized policy-prompted choices (two independent
draws give a self-consistency ceiling of 0.68); readers predict from 8-choice records vs
no-record vs self-first; per-cell and per-reader accuracy; paired self-vs-other on the
records route.

| target | records | no record | self-first |
|---|---|---|---|
| the reader itself | 0.42 | 0.32 | 0.42 |
| other family | 0.52 | 0.48 | 0.45 |
| programmatic | 0.53 | 0.28 | 0.28 |

*Table: pooled prediction accuracy against the target's realized choice; ceiling for
model targets 0.68 (two-draw agreement); chance 0.25.*

**What we found.** Self-minus-other on records: −0.10 (p=0.55). No self-advantage; if
anything the other family is easier. The record route's gain replicates for programmatic
(+0.25) and self (+0.10) targets but vanishes for the other family (+0.03), whose
no-record baseline is already high — readers predict SmolLM-ish makers from priors alone.

**What it means.** The similarity advantage is REPRESENTATIONAL, not predictive-of-record:
family kinship helps read artifacts (L179's gradient) but not forecast choices. Those are
different inferences, and the theory's graded-similarity prediction (HH-23) now has a
measured split across them.

> **Curator roll-up.** Theory group: self-simulation route (E trunk). Question: does
> similarity to the target improve record-based prediction? Outcome class: **Narrows.**
> Result: self-minus-other −0.10 (ns) against a 0.68 consistency ceiling. Meaning:
> similarity's benefit lives in artifact-reading, not choice-forecasting — a dissociation
> the theory must now carry. Next obligation: E03/X1 policies (queued). Public claim:
> HH-23's artifact half only. Decision: No.
> Detail: results/phase_2_4_stage_3/E/E03/verdict.json.


## L193 · The reader that cannot use records projects itself: SmolLM's errors land on its own preference at 0.58 against a 0.33 null, Qwen's do not

**Hypothesis.** On items where the target's record points away from the reader's own
preference, do errors lean toward the reader's preference — self-projection intruding?

**Method.** Each reader's E01 plain-frame self-profile fixes its rival target; 36
conflict items per reader (three record draws x conflict holdouts); errors classified
correct / self-intrusion / other-error; symmetric null puts 1/3 of errors on the self
option.

**What we found.** Qwen: 22/36 correct, intrusion share of errors 0.29 (at/below null).
SmolLM: 10/36 correct, intrusion share **0.58** (15 of 26 errors on its own preferred
option).

**What it means.** Self-projection is the FALLBACK of a reader that cannot consume
evidence: Qwen (the record-reader, L171) errs symmetrically; SmolLM (record-blind at
this task) defaults to itself. The assumed-similarity initialization plus failed
correction — the exact failure mode the theory's similarity paragraph predicts.

> **Curator roll-up.** Theory group: self-simulation route (E trunk). Question: does the
> reader's own preference intrude on conflicting evidence? Outcome class:
> **Strengthens** (the projection-as-default account). Result: intrusion 0.58 vs 0.33
> null for the record-blind reader; 0.29 for the record-reader. Meaning: projection and
> evidence-use trade off across readers — the correction step is what separates them.
> Next obligation: none. Public claim: model-side projection default, citable. Decision:
> No. Detail: results/phase_2_4_stage_3/E/E04/verdict.json.


## L194 · Offered a more informative or less informative record, readers pick whichever is listed first: information-seeking loses to position outright

**Hypothesis.** Given the choice of ONE more record to see, does the reader pick the
scenario with higher exact expected information gain?

**Method.** 28 items (EIG ratio >= 1.5, mean 1.77), counterbalanced presentation,
mechanical restate-the-context readout.

**What we found.** Informative-pick rates 0.36 (Qwen) and 0.38 (SmolLM) — below chance —
while FIRST-POSITION rates are 0.86 and 1.00. SmolLM picked the first option every
single time it answered; realization 0.79/0.46.

**What it means.** No value-of-information computation is happening; presentation order
decides. Active probing, if these readers do it at all, is not driven by expected
evidence — a hard bound on the active-search leg of the reader loop at this scale.

> **Curator roll-up.** Theory group: reader heuristics, active search (E trunk).
> Question: do readers seek the more informative record? Outcome class: **Kills** (at
> this scale). Result: first-position rate 0.86-1.00 vs informative rate 0.36-0.38.
> Meaning: epistemic foraging needs capabilities these readers lack; position is the
> policy. Next obligation: none. Public claim: none. Decision: No.
> Detail: results/phase_2_4_stage_3/E/E05/verdict.json.


## L195 · The record helps only if it comes first: Qwen's record-reading collapses from 0.67 to 0.40 when the question precedes the evidence

**Hypothesis.** Exact inference is order-blind; is the reader's record use order-blind?

**Method.** Same E02 items, record-before-question vs question-before-record, paired.

**What we found.** Qwen: record-first 0.667 vs question-first 0.400. SmolLM: 0.333 vs
0.396 (nothing to lose). Pooled +0.097 (p=0.12) — the pooled number again hides the
per-reader fact, as the L171 rule predicted.

**What it means.** The one reader that can use records uses them only in the
evidence-then-question order — HH-25's ordering question gets its first model-side
answer: context placement is not neutral, and late question beats early question.

> **Curator roll-up.** Theory group: reader heuristics, context ordering (E trunk).
> Question: is record use order-sensitive? Outcome class: **Strengthens** (HH-25's
> direction). Result: 0.67 vs 0.40 for the record-reading reader. Meaning: ordering is
> load-bearing for evidence use; prompts must put records first by construction.
> Next obligation: fold into every downstream reader design (done — all Stage-3 prompts
> are record-first). Public claim: model-side ordering effect citable. Decision: No.
> Detail: results/phase_2_4_stage_3/E/E06/verdict.json.


## L196 · The tendency corpus lands at three-quarters yield — under its own floor — with half its scene-quads complete: the makers realize fear and curiosity more readily than anger and care

**Hypothesis.** (Corpus card.) 24 scenes x 4 action tendencies x 2 makers, accept-time
anchor realization, complete quads only for twin contrasts.

**What we found.** INSTRUMENT-FAILED on its own 0.9 floor: 144 of 192 realized (0.75
exactly), 24 of 48 quads complete. The misses concentrate in the anger and care
tendencies (the confront/shelter closing lines).

**What it means.** The corpus exists and carries 135+ analyzable artifacts, but every
downstream A cell inherits a tendency-skewed sample and says so. The floor did its job:
the skew is recorded, not hidden.

> **Curator roll-up.** Theory group: affect construction (A trunk, corpus). Question: can
> makers write tendency-realized twins at yield? Outcome class: **Infrastructure**
> (failed floor, usable corpus). Result: 0.75 yield, 24/48 quads. Meaning: A-trunk
> analyses run on a skewed but audited sample. Next obligation: none — downstream cells
> filter per-item. Public claim: none. Decision: No.
> Detail: results/phase_2_4_stage_3/A/A01/corpus.json.


## L197 · The steering anchor stands: additive valence steering moves preference for happy continuations symmetrically in both directions, with random and shuffled directions quiet — the causal handle the rank-one construction never had

**Hypothesis.** (The A-trunk known-positive gate.) Reproduce plain valence
activation-steering on Qwen2.5-1.5B-Instruct: a fitted direction, added and subtracted
at a capability-tolerated dose, must move the preference between matched positive and
negative continuations as a SIGN PAIR, with random and shuffled-label directions quiet.

**Method.** 24+24 valence sentences; per-block last-token directions; consensus locus =
blocks 9-24 (decode 1.00 on two fit splits and an untouched validation split); additive
steering at blocks 14-18; dose ladder 20/10/5 percent of state norm under a fact-recall
tolerance (5 percent passed); readout = logp(happy continuation) minus logp(sad
continuation) over 12 neutral contexts.

| condition | shift in the happy-minus-sad preference |
|---|---|
| +direction | **+0.78** (p = 6.5e-4) |
| −direction | **−0.75** (p = 8.0e-4) |
| random direction | +0.02 |
| shuffled-label direction | +0.15 |

*Table: change from the unsteered baseline, per-context sign-flip permutation, n = 12.*

**What we found.** ANCHOR-STANDS. Clean sign pair, both controls under half the effect,
capability intact at the chosen dose.

**What it means.** Additive steering on the instruct model is a working causal handle on
affect-adjacent structure — the thing L170's rank-one amplify/ablate on the base model
was not, for its construction. Per the errata: a different construction that COEXISTS
with L170, and the license for every A-trunk causal arm.

> **Curator roll-up.** Theory group: affect in the model (A trunk, instrument). Question:
> can we causally steer valence at all? Outcome class: **Infrastructure** (passed).
> Result: sign pair ±0.75-0.78 at p<1e-3, controls quiet. Meaning: the causal gate is
> open; A07's tendency steering is interpretable. Next obligation: none. Public claim:
> steering-anchor validated (construction-scoped). Decision: No.
> Detail: results/phase_2_4_stage_3/A/A02/anchor.json.


## L198 · Action tendencies are decodable from the writing at 0.42 against 0.25 chance, and they live LATE: the tournament's winner is nearest-centroid at the last third of blocks

**Hypothesis.** Where in depth, and in what geometric form, do the four tendencies live
while the model reads tendency-laden text (anchor lines stripped)?

**Method.** 135 artifacts, scene-fold held-out decode; bases (one-vs-rest mean-difference
vs nearest-centroid) x loci (early/middle/late thirds + the A02 valence consensus);
five-shuffle null per cell.

**What we found.** Winner: centroid | late = **0.422** vs shuffled null 0.265 (max
0.281). Middle 0.311, early 0.304; every mean-difference cell ~chance. The A02 valence
blocks decode tendencies no better than chance under mean-difference.

**What it means.** Tendency-while-reading is real, categorical-geometry-shaped (centroids
beat directions), and sits deeper than the valence locus — a different object from
valence, which A04 then stress-tests.

> **Curator roll-up.** Theory group: affect construction (A trunk). Question: is
> tendency decodable from writing, and where? Outcome class: **Strengthens.** Result:
> 0.422 vs 0.25 chance at the late third, clear of a five-shuffle null. Meaning: the
> constructed tendencies leave readable structure; the basis question (centroid over
> direction) is itself a datum. Next obligation: A05/A06 interpretations inherit this
> recipe. Public claim: none yet (one maker-pair corpus). Decision: No.
> Detail: results/phase_2_4_stage_3/A/A03/tournament.json.


## L199 · Fear and anger separate — but the valence axis separates them too, so the dissociation FAILS: what we called tendency reading is partly valence-adjacent structure

**Hypothesis.** If the tendency read is really tendency, fear-vs-anger (same valence,
opposite action direction) must separate while the frozen VALENCE direction must not.

**What we found.** Tendency decode 0.597 (n=67, chance 0.5) — passes weakly. But the
valence axis separates fear from anger at AUC 0.186 (far from 0.5): anger bodies project
systematically more positive than fear bodies. NOT dissociated on the pre-registered
criterion.

**What it means.** The two negative tendencies differ along valence-adjacent geometry in
this corpus — either anger's confrontation reads as agentic/less-negative to the model,
or the corpus confounds tendency with intensity. Panksepp-shaped modularity does NOT get
its clean win; the V07 case-study table takes this row as Barrett-leaning.

> **Curator roll-up.** Theory group: affect construction (A trunk). Question: is
> tendency independent of valence in the geometry? Outcome class: **Narrows.** Result:
> fear-anger separable at 0.597 but valence-axis AUC 0.186 breaks the dissociation.
> Meaning: the tendency read is partly valence-riding; discrete-system claims are not
> licensed. Next obligation: none — the A05/A06 rows complete the geometry picture.
> Public claim: none. Decision: No.
> Detail: results/phase_2_4_stage_3/A/A04/verdict.json.


## L200 · Two tendencies at once do not read as two: blends land NEAR NEITHER parent — top-2 pair accuracy is below chance

**Hypothesis.** If tendencies are component directions, a two-tendency artifact should
sit near both parents (top-2 centroid match).

**What we found.** Top-2 pair accuracy 0.065 vs 1/6 chance over 31 realized blends; five
of six pairs at zero; only care+curiosity ever matches (0.29).

**What it means.** Blends are not superpositions in this geometry — mixture states are
somewhere ELSE, which is the constructed-emotion-shaped outcome again (a blend is its
own point, not a sum). With L199, the A trunk's geometry story is consistently
non-modular.

> **Curator roll-up.** Theory group: affect construction (A trunk). Question: do blends
> read as their components? Outcome class: **Narrows.** Result: top-2 match 0.065, below
> 1/6 chance. Meaning: no component algebra at this construction; mixtures are novel
> points. Next obligation: none. Public claim: none. Decision: No.
> Detail: results/phase_2_4_stage_3/A/A05/verdict.json.


## L201 · The suppression check had nothing to suppress: the "expressive" corpus already contains almost no emotion words, so the manipulation is unverifiable — and the tendency still decodes at 0.40 from flat text

**Hypothesis.** Under a flat-register instruction, does tendency survive in the writing?

**What we found.** INSTRUMENT-FAILED on its own gate: emotion-word rate was 0.0056 in the
expressive corpus and 0.0048 suppressed — no dynamic range, so "suppression verified"
cannot fire. The transfer decode (fit on expressive, applied to suppressed) still reads
0.402 vs 0.25 floor.

**What it means.** The makers already write tendency through ACTION, not emotion
vocabulary, so the surface manipulation check was aimed at a channel the corpus never
used. The 0.40 transfer is suggestive leakage but unclaimed pending a check with range
(banked as a lesson).

> **Curator roll-up.** Theory group: affect construction (A trunk). Question: does
> tendency survive expressive suppression? Outcome class: **Infrastructure** (check
> failed). Result: manipulation unverifiable (rates 0.006 vs 0.005); transfer decode
> 0.40 recorded unclaimed. Meaning: suppression designs here need a verifiable surface
> channel first. Next obligation: A06/X4's second domain owes the redesigned check.
> Public claim: none. Decision: No.
> Detail: results/phase_2_4_stage_3/A/A06/verdict.json.


## L202 · Steering the tendency directions moves the realized impulse as a weak sign pair — on a forced-choice baseline that curiosity owns

**Hypothesis.** With the A02 anchor standing, does additive steering along the fitted
tendency directions move which Next-impulse the model completes?

**Method.** Behind the A02 verdict gate; dose ladder under the same fact-recall
tolerance (4 percent passed); 12 scenes x 4 tendencies; steered-tendency completion rate
for +dose, baseline, −dose, and random-direction.

**What we found.** Pooled: +0.354 / base 0.250 / −0.188 / random 0.250 — a sign pair
with the random control exactly at baseline; causal signature TRUE. The per-tendency
cells expose the base skew: curiosity owns the unsteered baseline (0.75; the probe's
"look around" framing), fear and care move off zero under +steer (0→0.17, 0.08→0.17),
and ANGER INVERTS (0.17→0.08 under +steer).

**What it means.** The tendency geometry is weakly causally usable — the first causal
positive of the affect program, at a different construction from L170 and coexisting
with it — but it is not four clean handles: one tendency dominates the baseline, one
steers backwards. Handle-shaped for curiosity/fear/care, not for anger.

> **Curator roll-up.** Theory group: affect construction (A trunk). Question: does the
> tendency geometry steer behavior? Outcome class: **Strengthens** (weak, scoped).
> Result: pooled sign pair +0.10/−0.06 around a 0.25 base with random quiet; anger
> inverted. Meaning: causal use exists at this construction; per-tendency asymmetry is
> the next fact to explain. Next obligation: baseline-marginal lesson applied to any
> rerun (banked). Public claim: causal-use, heavily scoped. Decision: No.
> Detail: results/phase_2_4_stage_3/A/A07/verdict.json.


## L203 · The patching program never had a signal to localize: the policy line that visibly steers generation moves the committed-answer likelihood by three points, and both patch controls are exactly quiet

**Hypothesis.** (M01, with M02/M03 its dependents.) Localize the standing policy in
depth by patching with-policy states into the bare prompt at each block.

**What we found.** INSTRUMENT-FAILED at the known-positive gate: the prompted shift on
the choice-mass readout is +0.030 (floor 0.10) — even though the same policy line shifts
GENERATED choices strongly (S02's prompted makers). Identity patch 0.0002, mismatched
patch −0.00004: the machinery is exact; the readout has nothing in it. M02 (interchange)
and M03 (cross-model) closed as blocked dependents.

**What it means.** The policy lives in the generation process, not in the next-token
likelihood of pre-committed answer sentences — a readout-class mismatch, now a banked
lesson: match the readout to the behavior the intervention moves.

> **Curator roll-up.** Theory group: mechanism (M trunk, three cards). Question: where in
> depth does the prompted policy live? Outcome class: **Infrastructure** (failed
> informatively). Result: prompted shift 0.03 on the likelihood readout vs strong
> generation shifts; controls at zero. Meaning: localization needs a generation-side
> readout (realized-choice patching), a rebuild candidate for the expansion ladder.
> Next obligation: none this week unless the ladder reaches it. Public claim: none.
> Decision: No. Detail: results/phase_2_4_stage_3/M/M01/verdict.json.


## L204 · Three deliveries of one policy: the adapter moves the likelihood readout three times more than the prompt does, and their shift directions agree — while the patched activation carries nothing

**Hypothesis.** Prompt, patched activation, and LoRA adapter deliver the same policy —
do they bend the choice distribution the same way?

**Method.** Same 12 scenarios and readout; per-scenario shift vectors (condition minus
bare); pairwise cosine and top-option agreement.

**What we found.** Adapter gain on the policy's option +0.074; prompt +0.027; activation
+0.001 (uninterpretable — M01's gate failed, nothing was there to patch).
Prompt-vs-adapter: shift cosine 0.69, top-option agreement 1.00.

**What it means.** Where the likelihood readout sees anything, prompt and weights push
the SAME direction with the weights pushing harder — the equivalence claim survives in
sign and ordering on this readout, with the activation route unmeasured rather than
absent (it inherits M01's failure).

> **Curator roll-up.** Theory group: mechanism (M trunk). Question: do prompt, activation,
> and adapter deliveries agree? Outcome class: **Narrows** (two of three routes agree;
> one unmeasured). Result: cosine 0.69, top-option 1.00, adapter 3x the prompt's gain.
> Meaning: policy-in-weights is the strongest delivery on this readout; activation
> equivalence awaits a generation-side readout. Next obligation: rides M01's rebuild.
> Public claim: none. Decision: No.
> Detail: results/phase_2_4_stage_3/M/M04/verdict.json.


## L205 · On human exam passages the likelihood reader recovers the author's purpose slightly BETTER than surface detail — the opposite of the intent-is-harder expectation

**Hypothesis.** On RACE-high passages, is recovering the author's PURPOSE (why written,
tone, what the author implies) harder than recovering surface DETAIL from the same
passages?

**Method.** 1,000 purpose + 1,000 detail questions (556 passages contribute to both),
mean-logprob option scoring, question-only floor per reader, paired sign-flip.

| reader | purpose | detail | question-only | purpose − detail |
|---|---|---|---|---|
| Qwen2.5-1.5B | 0.482 | 0.430 | 0.28-0.29 | **+0.052** (p = 0.023) |
| SmolLM2-1.7B | 0.431 | 0.393 | 0.29-0.30 | +0.038 (p = 0.095) |

*Table: option accuracy, chance 0.25; passage lift over question-only 0.10-0.14.*

**What we found.** Purpose beats detail for both readers, significantly for one.

**What it means.** At exam grain, author-purpose is not the harder read — rhetorical
purpose is broadcast (the passage is BUILT to carry it) while details must be retrieved.
The human-ground anchor now says: purpose-level inversion is cheap where the maker
intends legibility — the bard's shaping, measured.

> **Curator roll-up.** Theory group: human ground (H trunk). Question: is author-purpose
> harder than detail on human passages? Outcome class: **Narrows** (direction reversed
> from the naive expectation). Result: purpose − detail +0.052 (p=0.023). Meaning:
> intended-purpose is the EASY inversion; the hard inversions are the unintended ones —
> exactly the theory's communicative-shaping line. Next obligation: H02's transfer read
> (landed, L206). Public claim: citable with the shaping interpretation. Decision: No.
> Detail: results/phase_2_4_stage_3/H/H01/verdict.json.


## L206 · The purpose advantage does not transfer to the middle-school split: levels rise, the gap closes

**Hypothesis.** Does L205's purpose-over-detail structure hold on the easier RACE-middle
split, nothing tuned?

**What we found.** Qwen 0.594 purpose vs 0.582 detail (+0.012); SmolLM 0.500 vs 0.494.
Overall accuracy up ~0.11; the purpose gap collapses to noise.

**What it means.** The purpose advantage is register-dependent: on simpler passages
detail catches up. The safe claim from the pair: purpose is never HARDER, and its edge
lives where passages are rhetorically denser.

> **Curator roll-up.** Theory group: human ground (H trunk). Question: does the purpose
> edge transfer? Outcome class: **Narrows.** Result: +0.012 (from +0.052). Meaning: the
> L205 claim is scoped to denser registers. Next obligation: none. Public claim: pair
> cited together. Decision: No. Detail: results/phase_2_4_stage_3/H/H02/verdict.json.


## L207 · Three thousand accept-or-dismiss decisions and the suggestion's contextual fit predicts nothing: AUC 0.499

**Hypothesis.** Writers took 76 percent of suggestions regardless of position or history
(Stage 2). Does the suggestion's FIT under the document-so-far separate take from
dismiss?

**Method.** 15,629 decidable CoAuthor episodes extracted (document replayed per event);
balanced 1,500/1,500 sample; mean-logprob of the suggestion under the document; AUC.

**What we found.** AUC 0.499 (accepted −2.268 vs rejected −2.296 mean logp). Nothing.

**What it means.** Take/dismiss is not a quality-of-fit decision at any grain we can
measure: position, history, and now content-fit all fail. Writers in this corpus accept
by default and dismiss for reasons invisible to fit — the human uptake record is
flat-by-policy, which itself is the finding the C-trunk sycophancy result mirrors from
the model side.

> **Curator roll-up.** Theory group: human ground, uptake (H trunk). Question: does
> contextual fit predict suggestion acceptance? Outcome class: **Kills** (the fit
> hypothesis on this corpus). Result: AUC 0.499, n=3,000. Meaning: CoAuthor acceptance
> is default-driven; uptake studies need corpora with real rejection behavior. Next
> obligation: none. Public claim: none. Decision: No.
> Detail: results/phase_2_4_stage_3/H/H04/verdict.json.


## L208 · Two H-trunk imports are blocked at the source: SocialIQA's loader is gone from the hub pathway we can use, and no OpenReview mirror exists under the names tried

**Hypothesis.** (Resource cards H03, H07.)

**What we found.** H03: the SocialIQA fetch fails in datasets 5 (script-based loader
retired). H07: three candidate HF mirrors do not exist; receipts recorded.

**What it means.** Both close RESOURCE_BLOCKED with named unblocks: H03 needs a
parquet-mirror fetch (candidate known), H07 needs a real mirror name or an OpenReview
API pull — both one-session tasks if the trunk needs them.

> **Curator roll-up.** Theory group: human ground (H trunk, two cards). Question: —
> Outcome class: **Infrastructure** (blocked). Result: two imports unreachable as
> attempted. Meaning: H floor already met without them (H01/H02/H04/H05/H06 landed).
> Next obligation: parquet-path retry for H03 on the ladder. Public claim: none.
> Decision: No. Detail: results/phase_2_4_stage_3/H/H03/verdict.json, H/H07/.


## L209 · The late-fusion ruler fails its easy doses: these readers cannot track exact Bayes even when all the evidence agrees — and the C-trunk's remaining questions are hereby read against a weak base, not a working one

**Hypothesis.** (C-trunk gate.) Hold when the record dominates, flip when the evidence
does; readers must clear 0.60 on the easy doses (0 and 8 conflicts) for the graded dose
to mean anything.

**What we found.** INSTRUMENT-FAILED: easy-dose accuracy 0.484 (dose-0 0.594, dose-8
0.375 against the FLIP truth). Order effect +0.048 (p=0.65). Yield 0.99.

**What it means.** The flip class defeats both readers: at eight conflicts they still
predict the old profile. Everything downstream in C is now explicitly an effect ON A
WEAK UPDATER, which turns out to be informative rather than fatal — see L211-L214.

> **Curator roll-up.** Theory group: context and trust (C trunk, instrument). Question:
> can the readers do exact late fusion at all? Outcome class: **Infrastructure**
> (failed). Result: 0.484 easy-dose vs 0.60 floor; FLIP items at 0.375. Meaning: the
> C-trunk reads inertia, not calibration. Next obligation: C01/X4's second domain only
> if a stronger reader joins. Public claim: none. Decision: No.
> Detail: results/phase_2_4_stage_3/C/C01/verdict.json.


## L210 · Verified track records do not transfer trust: with reliability established on OTHER makers, every condition sits near the floor

**Hypothesis.** An archive proven right and one proven wrong (on other makers) both
report about this maker; does the reader weight the proven-right one?

**What we found.** Reliable-only 0.304, unreliable-only 0.349, conflict 0.292 vs a 0.25
floor; follows-the-wrong-source 0.33 in conflict. No source weighting.

**What it means.** Cross-maker reliability transfer is absent in these readers — trust,
if it exists here at all, does not generalize from track record to new reports. With
L209's base failure, the honest scope: no measurable source-weighting capacity at this
scale.

> **Curator roll-up.** Theory group: context and trust (C trunk). Question: does proven
> reliability transfer to new reports? Outcome class: **Kills** (at this scale). Result:
> all conditions 0.29-0.35 near floor. Meaning: source-reliability reasoning is absent
> in the small-instruct class. Next obligation: none. Public claim: none. Decision: No.
> Detail: results/phase_2_4_stage_3/C/C02/verdict.json.


## L211 · Biography moves the reader the way evidence should: it adds when consistent with the record and subtracts when it conflicts — narrative weighs about as much as six documented choices

**Hypothesis.** Does a career-sketch biography shift predictions like an equivalent
record does — and which wins in conflict?

**What we found.** Record-only 0.375; biography-only 0.292; both-consistent **0.458**;
conflict 0.250. Consistent biography lifts the record by +0.083; conflicting biography
erases it (−0.125, to the floor).

**What it means.** For these readers narrative context is potent — roughly the record's
own weight — in BOTH directions. Where attribution context did nothing for the
likelihood reader (L181), the prompted reader consumes biography fully; this is the
model-side version of context-reweighting, with no verification discount at all
(consistent with L210).

> **Curator roll-up.** Theory group: context and trust (C trunk). Question: does
> biography move prediction like evidence? Outcome class: **Strengthens**
> (context-reweighting, direction-symmetric). Result: +0.083 consistent, −0.125
> conflicting around a 0.375 record base. Meaning: narrative and record trade at near
> parity; trust discounting is absent. Next obligation: none. Public claim: model-side
> only. Decision: No. Detail: results/phase_2_4_stage_3/C/C03/verdict.json.


## L212 · Where the conflict sits in the record does not matter, because the record barely registers: all three positions sit at the floor on HOLD items

**What we found.** (Against exact-Bayes HOLD truths, dose-2.) Early 0.277, middle 0.271,
late 0.250 — flat at the floor L209 predicts for this item class.

**What it means.** Position effects cannot be read on a base this weak; the cell closes
as bounded-by-instrument, kept for the record.

> **Curator roll-up.** Theory group: context and trust (C trunk). Question: does
> conflict position move updating? Outcome class: **Infrastructure** (bounded by L209).
> Result: 0.25-0.28 flat. Meaning: none beyond the base failure. Next obligation: none.
> Public claim: none. Decision: No.
> Detail: results/phase_2_4_stage_3/C/C04/verdict.json.


## L213 · The failure is weighing, not attention — and it inverts: readers that recall the conflicting evidence BETTER update WORSE

**Hypothesis.** When the reader fails to flip under overwhelming conflict, did it fail
to SEE the evidence or fail to WEIGH it? Mechanical recall stage first, then predict.

**What we found.** On dose-8 FLIP items: recall-good readers 0.091 correct (n=22);
recall-bad readers 0.240 (n=25). Attention is fine — recall of the conflicting choices
is routinely high — and updating not only fails but anti-correlates with recall.

**What it means.** The updater is broken downstream of attention: the reader can list
the eight contradicting choices and still predict the old profile — and the ones that
recite the evidence best hold the prior hardest. Uptake decomposition lands its answer:
WEIGHING failure, decisively, with an inversion worth its own follow-up someday.

> **Curator roll-up.** Theory group: context and trust, uptake decomposition (C trunk).
> Question: attend-fail or weigh-fail? Outcome class: **Strengthens** (the decomposition
> instrument worked; the answer is weighing). Result: recall-good 0.09 vs recall-bad
> 0.24 on FLIP items. Meaning: evidence is seen and not used — inertia is post-attentional.
> Next obligation: none this week. Public claim: model-side, scoped. Decision: No.
> Detail: results/phase_2_4_stage_3/C/C05/verdict.json.


## L214 · A stated hope beats a unanimous record five times out of six: hint-following at 0.83 swings accuracy from 0.92 to 0.08

**Hypothesis.** Does a bystander's expressed hope bend the reader's prediction against a
6-0 record? (No instruction to comply — a parenthetical "fingers crossed.")

| condition | accuracy vs the record |
|---|---|
| no hint | 0.574 |
| hope agrees with record | **0.917** |
| hope conflicts with record | **0.083** |

*Table: prediction accuracy on dose-0 items (unanimous 6-0 records); hint-following
rate on conflict items 0.833.*

**What we found.** The strongest single effect of the stage: the hope is worth more than
the entire record, in both directions.

**What it means.** Sycophancy is not a tie-breaker here — it is the decision. Beside
L213: evidence attended, evidence recited, and a stranger's wish overrides it. The
trust wing's central number, and the mirror of H04's human default-acceptance.

> **Curator roll-up.** Theory group: context and trust, sycophancy (C trunk). Question:
> does an expressed hope override the record? Outcome class: **Strengthens** (the
> overweight-supplied-assertion account, G167's successor). Result: hint-following 0.83;
> accuracy 0.92 vs 0.08 by hint direction. Meaning: supplied preferences dominate
> evidence wholesale in this reader class. Next obligation: fold into the trust-reader
> requirement (HH-25's failure clause). Public claim: model-side sycophancy number,
> citable. Decision: No. Detail: results/phase_2_4_stage_3/C/C06/verdict.json.


## L215 · The choice-set ruler splits: exact recovery and the blind floor stand, the strength ordering and one maker's enactment fail — the V trunk runs on the recovery leg with the strength leg retired

**Hypothesis.** (V-trunk gate.) Exact recovery from programmatic records; margin-based
choice-strength must order posteriors; makers must enact dictated choices at 0.85.

**What we found.** INSTRUMENT-FAILED as a whole: recovery 8/8 profiles (stands), blind
floor 0.26 (stands), strength monotonicity FALSE (the margin metric does not order
posterior mass everywhere), Qwen enactment 0.625 vs SmolLM 1.00.

**What it means.** The recovery instrument every V cell actually uses is intact; the
strength METRIC (softmax margin) is wrong as built and retires; dictated-choice
enactment is maker-dependent. Downstream V cells stand on the surviving legs and say so.

> **Curator roll-up.** Theory group: preference (V trunk, instrument). Question: does
> the choice-set ruler hold end to end? Outcome class: **Infrastructure** (split).
> Result: recovery and floor stand; strength leg and one enactment leg fail. Meaning:
> V02/V04/V05 are licensed by the surviving legs; strength-graded designs wait for a
> better strength measure. Next obligation: V01/X1 profiles under the repaired metric if
> the ladder reaches it. Public claim: none. Decision: No.
> Detail: results/phase_2_4_stage_3/V/V01/ruler.json.


## L216 · Preference is recoverable from enacted artifacts at rising dose; it thins across domains for model readers while exact transfer is perfect; and an editor's hand is readable exactly — but the model editor's instructed profile loses to its grain

**Hypothesis.** (V02, V04, V05 in one arc.) Artifact-only recovery with dose; profile
transfer across surface domains; editor recovery from edit directions.

**What we found.** V02: yield 0.92, dose-rising posterior — PROMISING. V04: within-domain
0.667/0.417 (Qwen/SmolLM) drops to 0.417/0.333 cross-domain against an exact ceiling of
1.00 — model readers treat the second domain as a different person. V05 exact: editor
recovered 4/4 with maker residual ~0 (a ceiling, not a test); model editor: the
robust-instructed editor reads back robust (0.61) at switch-rate 0.83, but the
cheap-instructed editor switches 90 percent of choices and STILL reads robust (0.998) —
the instructed profile loses to the model's intrinsic lean in its own edits.

**What it means.** Preference reading transfers perfectly in principle (exact) and
poorly in these readers — a cross-context gap the theory's timescale story needs. And
the editor result is the L169/E01 categorical-appetite fact from a third angle:
instructed preferences do not survive contact with the grain, even in editing.

> **Curator roll-up.** Theory group: preference (V trunk, three cards). Question: is
> preference recoverable from artifacts, across domains, and from edits? Outcome class:
> **Narrows.** Result: dose-rising recovery; cross-domain drop 0.25/0.08 against a
> perfect exact ceiling; instructed-editor profile overridden by grain (0.998 robust
> after 90 percent cheap-directed switching). Meaning: preference constructs transfer in
> the environment but not in the readers, and instructed identity keeps losing to
> intrinsic identity everywhere we look. Next obligation: V04/X4 third domain (ladder).
> Public claim: model-side scoped. Decision: No.
> Detail: results/phase_2_4_stage_3/V/V02, V04, V05 verdicts.


## L217 · Exact weights beat siblings inside both families: the top of the relatedness gradient is identity, not family style

**Hypothesis.** (S01/X2.) Within a family, does the exact-weight reader beat sibling
checkpoints of the same lineage — or is the gradient's top rung just family style?

**Method.** Paired within-artifact: the exact reader's margin minus the mean sibling
margin, per artifact, sign-flip permutation.

**What we found.** Qwen exact-minus-sibling +0.0107 (p=1e-4, 123 pairs); SmolLM +0.0141
(p=5e-5, 127 pairs). OLMo has no siblings on the bench (recorded).

**What it means.** Same-weights self-legibility exists ABOVE family style in both
families where it can be measured — the three-rung gradient (L179) is now confirmed at
its finest split.

> **Curator roll-up.** Theory group: reader heuristics, similarity (S trunk). Question:
> is the gradient's top rung identity or style? Outcome class: **Strengthens.** Result:
> exact beats siblings +0.011/+0.014 at p<=1e-4 in both families. Meaning: exact-weight
> identity is its own rung. Next obligation: none. Public claim: gradient citable at its
> finest split. Decision: No. Detail: results/phase_2_4_stage_3/S/S01/siblings.json.


## L218 · The relatedness gradient is monotone inside every family separately, the third included

**Hypothesis.** (S03/X3.) Does the pooled gradient (L179) hold within each maker family?

**What we found.** Monotone in qwen, smollm, and olmo separately (olmo's middle rung is
empty — a single-checkpoint family — so its gradient is the exact-vs-cross pair).

**What it means.** No family carries the pooled gradient alone; the ordering is a
family-general fact.

> **Curator roll-up.** Theory group: reader heuristics (S trunk). Question: is the
> gradient family-general? Outcome class: **Strengthens.** Result: monotone in 3 of 3
> families. Meaning: composition effects excluded. Next obligation: none. Public claim:
> unchanged. Decision: No. Detail: results/phase_2_4_stage_3/S/S03/family3.json.


## L219 · The crossed reversal survives its quality adversary: five of eight readers show the own-family effect inside themselves, where reader quality cannot move

**Hypothesis.** (XV1, adversarial.) Could the crossed reversal be a reader-quality
composition artifact? Within one reader, quality is constant — so the own-family effect
must survive within readers or die. Kill condition, written first: own-effect at or
below zero for most readers.

**What we found.** 5 of 8 readers show a positive within-reader own-family effect; the
adversary's kill condition does not fire. The three negatives are the weakest readers'
cells (per-reader table in the verdict).

**What it means.** The reversal is relational, not compositional — the strongest
remaining rival after the eraser stack falls.

> **Curator roll-up.** Theory group: reader heuristics (S trunk, adversarial). Question:
> does quality composition explain the reversal? Outcome class: **Strengthens** (the
> positive survives its adversary). Result: 5/8 readers positive within-reader. Meaning:
> the quality rival is now measured and insufficient. Next obligation: none. Public
> claim: reversal citable with the quality control. Decision: No.
> Detail: results/phase_2_4_stage_3/X/XV1_verdict.json.


## L220 · The purpose advantage survives its option-structure adversary — and grows: on items where the correct option is not the longest, purpose beats detail by nine points

**Hypothesis.** (XV5, adversarial.) Is purpose-easier-than-detail (L205) an
option-length artifact? Kill condition: the advantage vanishes on bias-resistant items.

**What we found.** Longest-option-correct rates are nearly equal across banks (0.285
purpose, 0.271 detail), and on the bias-resistant subset the purpose advantage RISES to
+0.087 for the stronger reader.

**What it means.** The reversal of the intent-is-harder expectation is not an option
artifact; the shaping interpretation stands stronger than before.

> **Curator roll-up.** Theory group: human ground (H trunk, adversarial). Question: is
> the purpose edge an option-structure artifact? Outcome class: **Strengthens.** Result:
> +0.087 on the bias-resistant subset (from +0.052 overall). Meaning: L205 survives its
> adversary and sharpens. Next obligation: none. Public claim: L205 citable with the
> control. Decision: No. Detail: results/phase_2_4_stage_3/X/XV5_verdict.json.


## L221 · The extended ruler recovers every profile including the blends — and the rebuilt strength leg is better but still not a law

**Hypothesis.** (V01/X1.) Four blend profiles join the four pure ones with fresh maker
instances: does exact recovery hold on the extended set, and does the rebuilt strength
metric (realized information gain, replacing the retired margin) order posteriors?

**What we found.** Recovery 48 of 48 cells (all eight profiles, three instances, both
domains) with blind floor 0.306. The EIG strength leg orders strong-half above weak-half
in 36 of 48 cells — a real improvement over the margin metric's failure (L215), still
short of a law.

**What it means.** The V-trunk's recovery instrument extends cleanly to mixed
preferences; choice-strength remains an open metric question rather than a solved one,
and no design leans on it.

> **Curator roll-up.** Theory group: preference (V trunk, instrument). Question: does
> the ruler extend to blends, and does EIG fix strength? Outcome class:
> **Infrastructure.** Result: 48/48 recovery; strength monotone 36/48 under EIG.
> Meaning: mixed-preference designs are licensed on the recovery leg; strength-graded
> claims stay unlicensed. Next obligation: none. Public claim: none. Decision: No.
> Detail: results/phase_2_4_stage_3/V/V01/profiles5to8.json.


# TIER 2 · SETTLED

## POSITIVE

| hypothesis | what we did | what we found |
|---|---|---|
| **Function words carry more than author identity, so they have capacity to carry maker state** | Held the author fixed and asked whether function words separate *different works by the same person*, across 34 books by 10 authors | **Twice chance**, every one of ten authors above chance. The channel has spare capacity |
| **A reading model contains directions corresponding to affect, and they are not just word-counting** | Fitted affect directions from contrast sentences, tested on held-out sentences, and ran a word-counting model on the identical sentences | **Four times chance**, while word-counting scored **exactly chance**. Accuracy is concentrated at two depths with a dead zone between |
| **Author identification should work, and can therefore validate the whole pipeline** | Ran classical authorship attribution as a known-answer check before every sweep | **7.6× chance**, and **identical at all four scrambling granularities** — which proves the scrambling code is correct before any real number is computed. Now a standing gate |
| **Scrambling words is too violent a control for a measure read from a model** | Measured what scrambling actually does, at four granularities | The three that keep the text grammatical agree within five points; **scrambling every word diverges by 27**. The control was perturbing the measure ~3× harder than the effect |
| **No measure should read noise as maximum intent** | Scored word-salad as a rung below the least-specified rung | Nothing places noise at or above the most-specified rung. **A failure mode we do not have** |

## RULED OUT

| hypothesis | what we found | why it died |
|---|---|---|
| **Decision density can be counted from an artifact** | It was word count (0.88), then after correction it was vocabulary diversity (−0.88) | length, then vocabulary |
| **Machine text written *with* a purpose ranks above machine text written without** | Perfect theory-shaped ordering, then died to controls | length and register |
| **Motivational variety is measurable as breadth of recovered purpose** | Simulation showed it tracks **how hard the goal is to recover**, not variety. Confirmed twice (T-2, T-9) | it is a difficulty meter |
| **Our own statistic detects whether a feature vector separates groups** | Said "no group information" on **author identification** | wrong statistic; replaced |
| **A reader moves further from its resting state for a human maker** | −0.005, no effect. Clean measure, real null | genuine negative |
| **Function-word vectors separate specified maker states** | The channel carries identity, not state | genuine negative |
| **Causal connectives track intent** | Ranked the ladder cleanly with no echo, then **inverted on humans** — machines use nearly twice as many | it measures explicitness, not depth |

## VOID — could not answer their own question

| hypothesis | why it means nothing |
|---|---|
| **Half A of a web corpus contains more recoverable method than half B** *(Gate 3, the project's primary)* | Its stability check failed — variation *within* an artifact was nine times the difference *between* halves. Simulation later showed the statistic reads a large number where the truth is zero and is undefined in most cases. **And a second, independent void:** 76 features separate the two halves, meaning they differ so broadly that almost any measure would separate them. Separating them was never evidence of anything |
| **Function words separate maker states** *(first attempt)* | Ran at 38% power — its median outcome under a real effect was below its own threshold |
| **A reader refuses differently on human and machine text** | Its pass condition was a coin flip: a 50% false-positive rate by arithmetic |
| **Reader displacement varies more for machines** | Three artifacts |
| **Some measure ranks five rungs of specified intent** *(the ladder's own first verdict)* | Voided on its own pre-registered limit: how many specifications a prompt carried and how long the output came out correlate at 0.40 against a 0.40 ceiling. **Reproduced at 0.40 on the second ladder, so it is structural to the design, not bad luck.** The measuring instrument was insufficient; it says nothing about the hypothesis |

## What the simulation established — with the question each was answering

Ground truth, which we do not have here. Three batches.

| | hypothesis | answer |
|---|---|---|
| **S-1** | The unlock statistic used by Gate 3 is sound | **No.** Reads a large positive where truth is zero; undefined in most cases |
| **S-3 / T-4** | An involuntary "leak" channel is readable, and concealment shows as divergence between leak and display | **Yes**, leak readable at 0.90, and amplifying the display makes concealment *more* detectable. Survives a reader wrong about almost everything — **but fails when concealment is mild** |
| **S-4/5** | The order of the probe's stages changes its answer | **No** — changes it by exactly zero. A cost saving, nothing more |
| **S-6** | Practised surface decays faster than depth | **Yes**, 6.5× faster; synthetic surface is flat |
| **T-1 → T-6** | The three inference problems bootstrap each other symmetrically | **Not symmetric, but the batch-two reading is withdrawn.** See below |
| **T-2 / T-9** | Motivational variety raises breadth of recovered purpose | **No** — breadth tracks difficulty. Established twice |
| **T-3 → T-10** | A count of recovered decisions is a well-defined event | **Which** decision: no. **When** a decision happened: **yes** — see below |
| **T-5** | Reading the process side beats reading the goal side, as a detector | **Tie.** No instrument consequence |
| **T-7** | Our simulation results survive correction for multiple testing | **Yes** — 17 claims lost, none of them a live effect in a cell with room to measure |
| **T-8** | Bigger feature banks beat small curated feature sets | **No.** Ten hand-picked features reach near-perfect; sixty more from a generic bank gain little and can lose a lot |

## The human readings — the most load-bearing evidence, and one reader

**Hypothesis:** a human reader can detect a maker and describe how, on sanitised artifacts with no
provenance cues. Fifteen artifacts, two sessions, sixteen readings. Three findings keep mattering: **the variation of
the veneer** is the primary detector; **depth is a property of the writer with respect to the
domain** — a relation, not an attribute; and **reading enters at an anomaly**, never at the whole
artifact.

---

## Where the files live

| | |
|---|---|
| **this file** | the record. Read first |
| `TODO.md` | ideas not yet run, and the queue |
| `docs/TOOLS.md` | what is installed, what it does, what it does not solve |
| `docs/theory/` | **the hypothesis store** — every claim, its status, and what would test it. Five files plus the essays |
| `docs/method/` | every test in one table; what a control licenses; deviations; literature reviews |
| `docs/gates/` · `docs/sim/` · `docs/design/` · `docs/archive/` | gate material; simulation traffic; what to build; superseded |
| `docs/STATE.md` | agent orientation after a context loss. Not for you |
| `results/*/VERDICT.md` | the primary record of each run |
