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

Promotion from 1 to 2 happens when a result has a verdict file and its required controls. **Nothing
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

Twenty-eight tests across four gates and three simulation batches. **Ten measures ruled out, four
tests void, three genuine positives, and three new candidates that have not cleared their controls.**
Every measure that reads the *artifact* has died to length, register, or vocabulary. The only signals
that have survived are read out of *the reader*. The binding constraint is no longer a measure — it
is that **we have never had a controlled comparison on human text**, and the corpora that would fix
that have now been identified.

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

**2 · One human reader.** **Fifteen artifacts across two sessions, sixteen readings** — one person. Those readings have
outperformed every measure we have built, so the most load-bearing evidence in the project has a
sample size of one reader.

**3 · RESOLVED — the induction check was built and run, and it changed verdicts.** The echo check
could only test whether a prompt *contains* a feature, never whether it *induces* one. That gap has
been closed: specification identity is now learned out-of-fold and removed. **It killed all three
surviving text-feature candidates (L2) and L1 survived it.** Folded into the entries it affected.

**7 · NEW — a criterion we trusted returned 335 components on pure noise.** Parallel analysis, applied
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

**Verdict: RULED OUT, all three.** The most promising candidate this project has produced from
outside sources does not survive its own controls. **The funnel worked and the answer is no.**

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

**What we did.** 86 students writing the same essay three times. Split each draft into fixed windows,
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

**What replaces it, and it is running.** `run_affect_dimensions.py` isolates affect the way the field
isolates it — average activations over many topics per emotion, then subtract the mean across
emotions, so the taxonomy selects which items to average and never supplies a basis. Human-labelled
categories, three counting criteria including two with a real stopping point, and three controls
including **the same pipeline on an untrained model of identical shape.** It gates on reproducing the
published valence and arousal correlations before any count is read.

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
