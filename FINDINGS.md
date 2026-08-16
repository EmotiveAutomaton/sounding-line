# FINDINGS — the method archive

**The method archive.** How each test was actually run, kept so a hypothesis row in `docs/theory/`
can be looked up rather than reconstructed. **It used to be the claims index; it is not any more** —
[`docs/theory/`](docs/theory/) holds the claims, organised by what we believe rather than by when we
ran it.

**Last updated: 2026-08-15.**

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
   issue says it "silently corrupts all training samples" and calls for "retraining
   compromised checkpoints." Also: 10 epochs, weight decay 0.01, no dev set, no early
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

*Caption: the organizers deduplicated within-year and not across years. On the 651 pairs seen
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
| deberta, fp32 | — | CUDA out-of-memory, no result | 0.8567 | — |

*Caption: the member set after the referee's corrections. The archived roberta row is the run
whose recorded 0.25 was false provenance; it is kept as the default-dropout data point.*

**Found.** Ernie reproduces above its gate under the corrected schedule, higher than its
archived constant-LR run (0.8650), so the schedule fix cost nothing and the third member is
landed. Roberta cannot train at all under the all-module reading of the winner's 0.25 — nine
epochs at the constant-prediction floor with one late escape — while ernie trains fine under
the identical setting, so the fragility is model-conditional, roberta's second knife-edge
after the no-warmup collapse (L104). Deberta's fp32 arm ran out of memory at batch 30 on the
shared card: infrastructure, not evidence.

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
