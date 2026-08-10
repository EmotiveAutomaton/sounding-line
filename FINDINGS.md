# FINDINGS — the method archive

**The method archive.** How each test was actually run, kept so a hypothesis row in `docs/theory/`
can be looked up rather than reconstructed. **It used to be the claims index; it is not any more** —
[`docs/theory/`](docs/theory/) holds the claims, organised by what we believe rather than by when we
ran it.

**Last updated: 2026-08-07.**

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
artifact would look exactly like a human/machine difference. Untested.

**5 · A scale gap remains in the affect directions.** Fitted on 12-word sentences, applied to
200-word windows. A worse version of this was caught and fixed; roughly a 16× gap remains and its
effect is unmeasured.

**6 · Feature banks may be the wrong tool, and we just installed one.** Simulation T-8 found that ten
hand-picked features combined reach near-perfect discrimination, while adding sixty more from a
generic bank gains a little on average and **loses more than it gains in the worst case**. Our
342-feature sweep is exactly the thing it warns about.

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
pre-set band; if it persists across the harness's future runs it gets hunted. **Means: G129's
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
pilot's prompts are built that way. Reader arms so far: cycle-one coarse 0.664 and fine 0.254
(against 0.5 and 0.125 chance), cycle-two coarse 0.648, replicating cycle one's level; the last
arm completes in the queue.

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

## L4 · Can weak effects be stacked into a detector?

**Hypothesis.** *(The curator's.)* Several small real effects combined may produce a usable
instrument where none alone is enough.

**Research context.** This is what commercial machine-text detectors already do, and it reaches
near-perfect accuracy on that problem. **Simulation T-8 now adds a caution from our own side:** ten
hand-picked features combined lifted the hardest cases to near-perfect, while adding sixty generic
bank features gained little on average and **lost more in the worst case**. So: combine, but curate.

**Verdict: OPEN, not yet run.** Two conditions before believing any stack — it must beat its best
single component **on held-out data**, and its errors must not be the same errors.

---

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
