# Reader heuristics: how a bounded reader approximates the triple inference

> While I don't expect we will have to rely on these heuristics when designing depth extraction, I
> expect AI will arrive at most, if not all of them, organically. Nevertheless it's worth keeping track
> of the ones we have run into that would be relevant as potential **feature-extracting amplifiers** in
> future, that other research teams may have missed.

**A bounded reader approximates the triple inference using priors about the maker, local cues in the
artifact, strategies for moving between explanatory levels, and calibration rules that limit
overinterpretation.** Humans do not solve the inference; they run heuristics at it, converging the
way a series approximation does. The curator's own readings (fifteen artifacts, two sessions) are
**the richest hypothesis source this project has**; they are not a validated instrument, because no
independent ground truth has scored them, and the calibration literature below shows exactly how
expertise and confidence coexist with low reliability.

**This file owns** reader priors, entry cues, traversal strategies, updating, stopping, and
calibration. **It does not own** the inference targets ([`THE_TRIPLE_INFERENCE.md`](THE_TRIPLE_INFERENCE.md)),
the ontology of artifact traces ([`DECISION_TRACES.md`](DECISION_TRACES.md)), model architecture
([`THREE_COGNITIVE_LAYERS.md`](THREE_COGNITIVE_LAYERS.md)), or alignment. *(Renamed from
`HUMAN_HEURISTICS.md` 2026-08-09.)* Per the program (2026-08-09) this file is **operational
support**, owning bounded candidate sets, entry points, calibration, and reader disagreement for
the choice-recovery work.

The file by function. A **prior** is held before the artifact is opened; a **cue** is a local,
readable feature that licenses an inference; a **heuristic** is any of the loop's cheap
approximations; the **traces** cues point at belong to the decision-traces file:

| function | sections | measured so far |
|---|---|---|
| priors before inspection | §1 | the provenance prior (replicated ×3) |
| finding an entry point | §2 | two variation measures (surface; probe-activation) |
| traversal, updating, stopping | §3 to §5 | nothing; one sim bound on ordering |
| cue families: constraint, habit, shaping | §6 to §8 | the visibility partition (double crossover); revision homogeneity (at ceiling, weakest adversary) |
| calibration and reporting | §9 to §11 | the dashboard's rules; the rest is discipline |

---

# Part I: The reader's loop

## §1. Priors held before inspection

What a reader brings before the artifact is opened. **Domain expertise** (which sets the available
entry points, §3); **closeness to the maker**, the one prior where the relationship does the work
rather than the text:

> Showing someone your writing is a kind of intimacy.

**(G59:** closeness as a measurable prior held before the artifact is seen. **OPEN**, canonical
here.**)** Then **biography and prior artifacts**, which are more observations, not context
(*"Everything's an artifact. Even information about their life"*, canonical in the triple
inference, operational here); **provenance framing**; and the **communicative assumption**,
treating the maker as intending to be understood.

The communicative assumption is the strongest and the most dangerous of these. It is standard in
cooperative inverse reinforcement learning, where teaching behaviour is part of a shared objective.
But that models a cooperative game, not every maker–reader relationship, and his own caveat marks
the limit. *"Humans actively, constantly pretend they're teachers under certain framings. Does that
always hold?"* It plainly does not; concealment, propaganda, seduction, and audience mis-modelling
are the countercases, and a wrong communicative assumption licenses confident inference from
structure placed to mislead, the same error the expertise literature calls failure to transfer,
running the other way:

> That's kind of the whole premise for **failure to transfer** – this lack of transfer as a result of
> expertise. **Same idea, different direction.**

And it lands on generated text specifically:

> **AI is being treated like a teacher also. It's getting the benefit – and maybe that's part of the
> problem, at least.**

The provenance prior is no longer speculative. A reader model's affective read of identical text
shifts when told the text is machine-made, small, fixed in direction, replicated on three corpora
(the measurement is canonical in the model-side ledger, `THREE_COGNITIVE_LAYERS.md` §7). Whatever a
disclosure label does to a human reader, the reading machinery itself is not neutral to claimed
provenance.

## §2. Finding an entry point

> The thing that most jumps out at me isn't mistakes but **unusual constructions, or odd decisions
> that I can't find an explanation for.**

Reading enters at an **anomaly**, never at the artifact as a whole, then runs purpose→method and
method→purpose from wherever the reader has partial expertise. His own discomfort, recorded because
he raised it. *"I hate that a lot of this is me picking out mistakes and typos, which is also a
trick for AI and it's not okay. But it is a way of extracting decisions."* A **mistake** is the
sharpened case, an anomaly with a *known cause*, so the response to it is a decision with its
alternatives visible. *"The mistake, and the way the author can be presumed to have responded to it,
is one of the more useful pieces of information once you have observed it."*

Two calibrations on this cue family. **Entry efficiency is not final quality.** The simulation found
anomaly-first ordering saves ~5% of cost and changes the answer by exactly zero, which bounds the
expected size of an ordering effect, and does not touch whether anomalies are *informative*. And two
imported entry cues extend the family. **Inverse salience** (diagnostic weight runs opposite to
conspicuousness, §7) and **reserve versus overpaint** (did the structure make room for a claim, or
was it inserted? The trace is Decision Traces' object; the reader's rule of looking for it lives
here).

**Within-artifact variation** is the curator's primary detector, polish *change* rather than polish
level:

> When I've been talking about the veneer in my head, I've been thinking about the imagery and
> iconography.

*The performance is what costs something, so the performance is what slips, and the slip is where
the maker shows*, with his own scope limit attached. Useless on published books, because editing
sands the polish flat. The field detects within-document variation successfully (burstiness,
unmasking, PAN style change at 0.830 on topic-controlled data), and his reading of what they are all
measuring is a claim, not a complaint:

> It's not burstiness. It's not unmasking. **It is goal variation** – all of them varying in relative
> strength as you express yourself. People aren't seeing it for what it is.

One honesty note on that claim. What the field's baselines validate is *detection of variation and
discontinuity*; the interpretation that the variation is **goal** variation is exactly what remains
open. Intrinsic plagiarism detection is also a different thing, a spliced author rather than one
author's goals moving, a distinction he separated after I collapsed it.

**And the revision-wobble test is retired on his own account.** Human redrafting was the wrong
axis, before the null even needed explaining:

> The problem is that revisions from a human author are always going to carry **the same level of
> intent density across the board.**

What would have been interesting instead, in his words: *AI* revision, the moment the model's
attentional mapping shifts away from your goal and you reach out to correct it:

> Allow me to pick you up with the largest pole of the tent in my distorted policy space.

He predicts a vague unifying effect there and declines to claim even that.

| # | hypothesis | status |
|---|---|---|
| **lit** | Within-artifact variation of polish carries the maker | **SUPPORTED (READ).** Seven years of shared-task baselines at 0.830 on topic-controlled data; what they validate is variation-detection, with the goal-variation reading open |
| **L7** | Variance of arbitrary surface features is the right operationalisation | **REJECTED (test).** 0 of 313 features survive with maker, prompt, topic and register fixed; the plain average found 12, so windowing was not the problem |
| **L11** | Our feature bank beats the field's bar on the topic-controlled split | **REJECTED (test).** 0.565 against floor 0.444 and bar 0.830; the uncontrolled-split 0.969 probably rides topic |
| **HH-3** | Within-artifact variance of *probe activations* carries what surface variance does not | **SUPPORTED (test), first pass.** Dashboard §11; genre and register uncontrolled in the pairing |
| **HH-4** | Redrafting is the wrong axis; the claim needs artifacts of different kinds by one maker | **OPEN**, and his intent-density quote above says why in advance |
| **HH-6** | Entering at the anomaly beats entering at the whole artifact | **OPEN.** The machinery exists (`bounded_v6` stage zero); a flag flip and a comparison |
| **HH-7** | Local decision density around a mistake exceeds baseline | **OPEN.** Needs mistakes located first; the one place a decision and its counterfactual are visible together |
| **S-4/S-5** | Stage ordering changes the answer | **REJECTED (sim)** by exactly zero; ~5% cost saving only |

**What the table says.** The entry-point family has one live positive and one honest defeat. The
reader's own affective series moves through human text and not machine text, while every surface
operationalisation of the same idea loses to the field's bar once topic is controlled. Ordering
effects are bounded near zero, the wobble test is retired on the curator's own account, and the
anomaly rows, the family's core, remain unrun. Confidence: the probe-activation result is one
bad test away; the surface defeats are replicated and controlled; the rest is untested.

## §3. Traversing explanatory levels

> Walking up to an unknown oil painting, you can engage with it on the level of **metaphor** – why did
> the author craft what they did. On the level of **technique**, like perspective. On the level of
> **mechanics** – how did they move their hand as they painted.
>
> **You can use any piece of knowledge about any of those three channels to begin the decoding.**

Working vocabulary. **Mechanics** (physical realization), **technique** (organized method), and
**purpose** (local and higher-order intent; "metaphor" names a subtype of this level, and is
narrower than the level needs, since the top has to carry goal). Dennett's three stances are the
closest citation (physical/design/intentional), and Panofsky was the wrong one. He rejected it
correctly, since Panofsky's levels are about what an image *depicts*. Structural resemblances to
Marr's or Newell's levels supply vocabulary, not evidence. Those frameworks partition different
objects for different purposes, and counting them as independent convergence overstated the case.

*Media literacy* is the common-language name for entry at the purpose level, a general skill for
ratcheting into unfamiliar media through the metaphorical layer.

The collision with the only occupying framework is real but must be stated precisely. Bullot &
Reber's psycho-historical frame makes historical/design-stance understanding a **necessary
condition** of full appreciation, and their own response describes actual processing as recursive
with feedback, so the disagreement is over *necessity*, not over whether processing is temporally
one-way. Their framework's replication record is weak (34 experiments: 26% support, 56% none), which
makes the collision worth taking. The experiment that would decide our side, supplying
mechanics-level information and measuring goal recovery, is canonical in the triple inference
(G56); this section describes the human strategy it operationalizes. Rasmussen's abstraction
hierarchy (means–ends diagnosis from any level, decades of use) is worth reading as a candidate
formal home, not adopting sight unseen. It has published methodological criticisms (Lind) aimed at
exactly the ambiguities that matter here.

| # | hypothesis | status |
|---|---|---|
| **lit** | Entry at any level, ratcheting to the others | **CONTESTED (READ).** Bullot & Reber make design-stance understanding a *necessary condition*; the disagreement is over necessity, not temporal order (their own response describes recursive processing) |
| **lit** | Bullot & Reber's framework is well supported | **REJECTED (READ-FULL).** 34 experiments across 23 publications: 26% support, 56% none |

**What the table says.** The only occupying framework makes level-entry a necessity claim with a
weak empirical record, which leaves enter-anywhere both undefended in the literature and untested
here. The deciding experiment is the triple inference's missing mechanics arm. Confidence:
untested, logic only, resting on a contested literature.

## §4. Updating and active search

> It starts questionable... 8 or 9 by the end.

**Confidence moves while reading, and the trajectory carries what the endpoint does not.** Every
reading this project records is a final number, so the series has never existed to be checked. The
reader also searches actively. Re-reading (each pass recovering lower-confidence attributions from
the tail), **epistemic foraging** for biography and further works, where *everything is an
artifact* becomes operational (context supplies additional observations but is not automatically
trustworthy), and switching levels when a hypothesis fails, per §3.

One external caution bears on the whole series family. A study of hidden states as author
representations found document-level mean pooling best, which is evidence against series-carrying
claims at the representation level. Not decisive (it optimized for identity, not maker state), but
the reason to expect modest effects.

| # | hypothesis | status |
|---|---|---|
| **HH-9** | The confidence trajectory across a reading carries more than its endpoint | **OPEN.** Every reading this project records is a final number, so the series has never existed to be checked |
| **G64** | Re-reading one artifact recovers the tail | **OPEN.** Canonical in the triple inference §5; the reader-side strategy is this section's |

**What the table says.** Nothing here has a number because the data has never been recorded. The
confidence series is the cheapest unbuilt instrument in the file, needing only that readings log a
trajectory instead of an endpoint. One external result points against series-carrying claims at
the representation level, which is a reason to expect modest effects, not to skip the test.
Confidence: untested, logic only.

## §5. Continuation and stopping

> Interest comes from finding decisions that you can't attribute meaning to, which implies there's
> more meaning you don't fully understand – either a **process** you aren't aware of, or an **extra
> motivation** you aren't aware of.
>
> **Artfulness is making a lot of unexplained decisions. Aesthetics is the appearance of having made
> unexplained decisions but for a reason, in an ordered sense.**

**Interest is the continuation signal.** Unresolved but apparently structured decisions keep the
reader searching, which makes reader-reported interest an instrument:

> **If interest is what a reader feels when decisions are present but unattributed, then
> reader-reported interest is an instrument – and it is one we can ask a human for directly.**

It also answers his own question about performative polish. Under this account, performative polish
is *ordered without being unexplained*, a measurable distinction. The formal target is effective
complexity (structure neither random nor trivially regular), not Berlyne's collative variables.
Read at source, Berlyne's arousal theory is *"mostly abandoned"*, and the live descendants
(processing-fluency accounts) sit at the opposite pole, locating pleasure in ease. That tension is
the thing the interest-ratings test would adjudicate, since the two accounts predict opposite
correlations between interest and recoverability. Per the program, those ratings inform this file
only and are never ground truth, since interest may reflect fluency, novelty, confusion, or
personal relevance.

Stopping is the calibration side. Graded attribution when evidence supports only that (§10), and a
**hard falsifier ends the inference outright**, the two-channel rule of §9.

| # | hypothesis | status |
|---|---|---|
| **HH-14** | Reader-reported interest correlates with unrecovered decisions | **OPEN, blocked on him.** Interest ratings on the fifteen read artifacts; an hour that turns the richest hypothesis source into data. Informs this file only, never ground truth |
| **HH-16** | "Ordered but unexplained" is effective complexity rather than entropy | **OPEN.** A real, formalisable target, and deprioritized as a global text summary by the program |
| **lit** | Berlyne's collative variables support the interest claim | **REJECTED (READ).** The arousal theory is *"mostly abandoned"*; one fetch found this after fifteen searches had not |

**What the table says.** The interest account survived losing its supposed backing. The abandoned
arousal theory is replaced by a sharper formal target (effective complexity), and the live
opposing account, pleasure from processing ease, predicts the *opposite* correlation between
interest and recoverability, which is exactly what the blocked ratings test would adjudicate.
Confidence: untested, logic only, blocked on an hour of the curator's time.

# Part II: Cue families

## §6. Distinguishing choice from constraint

The governing rule, distilled from the one field with forty years of practice at reading makers off
products. **Model what the medium and task force; interpret only residual variation as candidate
choice.** The mechanical null model is its cleanest form. In controlled experiments on molded glass
cores, flake geometry is dominated by two measurable variables, with platform width following from a
material constant *"not under direct control by the knapper"*, and its severe caveat travels with
it. The null model explains far less variance off the bench.

The cue family, by function rather than by source:

- **Recurrence.** *"It is because a gesture is constant or recurrent that it can be interpreted as
  intentional"* (Soressi & Geneste), with the honest reading attached. Recurrence is equally
  consistent with habit, with training, and with a constraint that is itself constant. The
  habit-shadow objection, arriving from archaeology.
- **Stage-differentiated signals.** Low-visibility, early-acquired features carry deep identity;
  visible, easily-copied features carry situational identity (Gosselain's pottery result). **This
  cue is now measured in-project, a clean double crossover on its first pass** (canonical row in
  `DECISION_TRACES.md` §3; dashboard below).
- **Error handling over error rate.** Novice cores show insistence and stacked steps on a ruined
  surface; expert cores show recognition and abandonment. Error *handling* measures metacognition;
  error *rate* on a small sample measures which burst you sampled, because errors cluster.
- **Rigidity under perturbation.** Experts hold outcomes constant under changed tools and
  materials; low-skilled artisans reveal *"rigid skills."* It implies an **active probe**. Perturb
  genre, length, or audience and measure whether quality is preserved.
- **Intention elicitation as the calibration ceiling.** The knapping protocol where makers draw the
  intended flake before striking: experts predict only **R² = 0.655 of their own stated intention**.
  Our intent ladder is this protocol, arrived at independently. Any recovery instrument works
  against a ceiling that expert self-prediction already fails to reach; stop treating distance from
  perfect recovery as failure.

| # | hypothesis | status |
|---|---|---|
| **G85** | Intention elicitation with a pre-registered target | **ALREADY BUILT.** The intent ladder is this protocol, validated on stone since 2010, with the R² = 0.655 ceiling attached |
| **G86** | A mechanical null model: subtract what the medium forces | **OPEN.** The right shape for choice-versus-constraint; the analogous model degrades badly off the bench. The program's event-recovery harness carries this as its forced-constraint null |
| **G87** | Stage-differentiated partition by visibility | **SUPPORTED (test).** Clean double crossover; canonical row in `DECISION_TRACES.md` §3, dashboard §11 |
| **G88** | Error *handling* rather than error rate | **OPEN.** Measures metacognition, not execution |
| **G89** | Rigidity under perturbation as the novice signature | **OPEN.** Implies the active probe |
| **G90** | Report separability as a cross-validated confusion matrix | **OPEN, a reporting convention**, and the program's required output format for choice recovery |
| **G91** | Inter-annotator agreement and per-feature accuracy before believing any extraction | **OPEN, and mandatory.** An aggregate concealed a worse-than-chance category |

**What the table says.** The forty-year practice arrives as one measured win, one protocol we had
already built, and a discipline. The visibility partition produced a clean double crossover on its
first pass, the intent ladder turns out to be the field's own elicitation protocol with a ceiling
attached that reframes every recovery number, and the rest of the family is method, not yet
measurement. Confidence: the partition is one bad test away; the ceiling import is replicated in
its home field; the open rows are untested.

## §7. Habit, concealment, and revision

The reader's rules for exploiting the automatic traces (the trace ontology itself is
`DECISION_TRACES.md` §3):

- **The Morellian admissibility filter.** A feature may be used only if it is amenable to
  individual expression, not school-supplied, not accidental, and **not one of a suite requiring
  deliberate variation**. Criterion 4 is the high-leverage import. Elegant variation is a writer
  overriding their own defaults, so the places our measures find most "varied" may carry least
  individual signal. This is a **historical candidate method, not proven practice**. Morelli's own
  notebooks show he scarcely used it (*"the spirit of the master met mine, and the truth flashed
  upon me"*), and the stylistic channel has never independently caught a competent forger.
- **Inverse salience.** Diagnostic weight inversely proportional to conspicuousness, because the
  imitator's attention flows to the conspicuous (Berenson's *"subconscious signature"* of
  *"small particularities which escape even the notice of copyists and forgers"*). The honest limit:
  a claim about the adversary's attention budget, not physics. It buys asymmetry, not security. And
  the re-aiming caveat: these identity tools may discard exactly the conspicuous features where
  *values* live.
- **Self-revision versus imposed revision.** Imposed changes are lumpy, discrete, heterogeneous;
  self-revision is homogeneous and *"of like kind"* throughout. Distributional, not semantic, and
  the discriminator mixed provenance needs most.
- **Suspicious regularity.** The imitator is *more* regular than the genuine article, executing
  carefully rather than habitually. If an instrument treats high internal consistency as expertise,
  this literature says it may be backwards.
- **Reserve versus overpaint.** Planned room versus insertion, computable on one static text; and
  abandoned scaffolding (a numbering scheme that stops, a promised return that never lands).
- **Mixed provenance takes the graded vocabulary.** *By · attributed to · studio of · circle of ·
  school of · follower of · manner of · after*. Three axes at once (proximity, temporality,
  intent), with *workshop of* the category this project needs most and would not have invented.

| # | hypothesis | status |
|---|---|---|
| **G79** | The four-part admissibility filter, criterion 4 especially | **OPEN, the best single import.** Predicts where habit is switched off |
| **G80** | Reserve versus overpaint, on text structure | **OPEN.** Computable on one static text |
| **G81** | Self-revision is homogeneous, imposed change is lumpy | **SUPPORTED (test, L52), first pass, against the weakest adversary.** 66 authors, real revision dispersion 0.45 vs cross-author splice 1.94, separation perfect (AUC 1.0). The ceiling is the caveat, since a crude splice may be read as *different author* rather than *imposed change*; the realistic same-register imposition is the untested case |
| **G82** | High internal consistency indicates *imitation*, not expertise | **OPEN.** May invert an assumption we hold |
| **G83** | Adopt the graded attribution vocabulary | **OPEN** |
| **G84** | Two channels: falsifiers veto, style proposes, never averaged | **OPEN, architectural.** Every historical catch came from a hard falsifier |

**What the table says.** The concealment family has its first number and it sits suspiciously at
ceiling. Real self-revision is measurably even-handed, but the adversary it beat was the crudest
possible splice, so the mixed-provenance question the family exists for is still open. The
admissibility filter's fourth criterion remains the best-rated unrun import; it predicts where
habit is switched *off*, which is information every other measure discards. Confidence: the
homogeneity result is one bad test away; everything else is untested.

## §8. Communicative shaping: the bard

**2026-08-07.** His refinement of the teacher assumption. A maker is something more specific, and
the difference is the part nobody has formalised:

> What we're actually looking for is **a bard**, to be a little bit more precise. **There are two
> motivations. They want to grab your attention through aesthetic capture, and they also want to make
> it easy for you to ingest the data.** And that's the teacher aspect.

> How on earth do they shape it in order to create that effect? **I assume they try to model the brain
> of their listener. Of course they do.** Which makes all interactions this kind of **collaborative
> back-and-forth.**

So the maker runs the triple inference in reverse while making. They model the reader, then shape
the artifact so the reader's inference lands where they want it, which makes an artifact a trace of
the maker's process *plus their model of you*. The reader's corresponding prior: **conspicuous
structure may have been placed to guide my inference**, aesthetics as deliberately-left scaffolding
for the descent through the levels:

> Part of aesthetics might be **leaving the kinds of hooks in your program that make it easier to
> deconstruct it.** Metacommentary or high-level metaphor that can be used to **move down through** the
> levels.

(The measurement side of the attraction/translation split lives in `DECISION_TRACES.md` §2.) He
flags the restatement risk himself. *"Yes, this is just a restatement of CIRL with different terms."*
It is, up to the aesthetic layer, which is the addition; and CIRL's cooperative-game framing does
not describe every maker–reader relationship, so this prior carries §1's concealment caveat in
full. The asymmetry he names is the sharpest thing here:

> **AI isn't interacting with this. It's only trying to take, it's not giving.**

If right, the missing thing in generated text is the second half of a collaboration, a third
account of the unease, distinct from broken polish–effort and flattened intent, and the three
predict different things. The effort heuristic belongs to the same family:

> Aesthetics is one of the **easiest goals to judge**, because it is literally surface polish – you
> can explicitly judge whether the maker succeeded at it, and implicitly the value of what you are
> seeing by **how much you want to look at it. It is a self-referring goal and you can cheat it pretty
> easily.**
>
> **It's also the piece that's misfiring on AI specifically. Previously it correlated with effort very
> highly. Now it does not. That's what's breaking.**

On his account the effort heuristic is a normally-valid inference a new artifact class has broken,
never a reader bias, and both rows testing it are blocked on measuring *effort*, the quantity
automaticity makes unobservable by construction.

| # | hypothesis | status |
|---|---|---|
| **G62** | Assuming the maker intends to be understood improves recovery | **OPEN, canonical here.** Must be tested against concealment, where the assumption licenses confident wrong inference |
| **G63** | Aesthetic structure functions as deliberately-left scaffolding for descent | **OPEN.** Polish partly communicative, not only performative |
| **G67** | Readers grant the communicative assumption to generated text, and that is why it misleads | **OPEN.** A claim about readers; the model-side provenance prior (§1) is its first adjacent measurement |
| **HH-19** | Attention capture and comprehensibility are separable shaping motivations | **OPEN, the load-bearing test.** Measurement side in `DECISION_TRACES.md` §2 |
| **HH-20** | Makers model the reader's inference and shape the artifact for it | **OPEN.** An artifact as process *plus the maker's model of you* |
| **HH-21** | Generated text lacks the collaborative half; it takes without giving | **OPEN.** The third account of the unease, and the three predict different things |
| **HH-17** | The polish–effort correlation is strong in human corpora, near zero in generated | **OPEN.** Blocked on an effort proxy |
| **HH-18** | The effort heuristic is a broken valid inference, not a reader bias | **OPEN.** Follows from HH-17; the reframe is the contribution |

**What the table says.** The bard refinement is the most theory-dense unmeasured material in the
file. It splits polish into two motivations, predicts a specific missing half in generated text,
and reframes the effort heuristic as a valid inference a new artifact class broke, three claims
that predict different things and share one blocker, a defensible proxy for effort. The
communicative assumption itself is the one prior whose failure mode (confident inference from
structure placed to mislead) is worse than not holding it. Confidence: untested, logic only.

# Part III: Calibration

## §9. Baselines and admissibility

- **A genre and register baseline is infrastructure, not optional.** Without one the instrument
  confidently reports the genre's decisions as the author's, the same failure that killed 61 of our
  81 replicated features. Morelli's version: the connoisseur lives among photographs as the botanist
  among plants.
- **Topic controls by construction.** The same practical question answered from different
  positions, or topic does the work.
- **Mechanical constraints modelled first** (§6's governing rule).
- **Two channels, never averaged.** Hard falsifiers can veto; stylistic inference proposes and
  never vetoes. Every historical forgery exposure came from a hard falsifier (titanium white, a
  broken provenance chain, a confession), and the fields that averaged the channels produced the
  Getty kouros.
- **Per-feature accuracy, never aggregates.** An aggregate of 72.6% concealed a worse-than-chance
  category.
- **Pre-register the feature set.** The tradition that defines attributes after seeing the
  assemblage defends a garden of forking paths; refuse it.

## §10. Reliability and ground truth

The calibration record from the fields that read makers professionally, kept because it disciplines
ours. Intention elicitation gives the ceiling (§6); **inter-annotator agreement is mandatory before
believing any extraction**. Eleven analysts on one knapper's hundred flakes, definitions agreed in
advance, still disagreed significantly, with failures concentrated in exactly the interpretively
loaded attributes, and *training background mattered where years of experience did not*. Per the
program, reader agreement is reliability, never validity, since several readers can converge on the
same wrong story. The replicability dilemma cuts at us directly. Selecting features *for*
replicability privileges the trivially measurable over the behaviourally meaningful, and our funnel
drops features that fail a filter. Refitting is their gold standard because it is non-inferential;
our text analogue is version history, which finished text does not supply. **We are the
archaeologist handed one finished handaxe and no flakes**, the position where every practitioner
agrees inference is weakest. The falsification test they ran on themselves (a 65% refit site
against mental reconstruction: an invented production method, a late product misdated to the start)
is the standing warning, with its honest scope, since the authors themselves concede the fault was
implementation rather than concept. Report identifiability the way their best work does. *"These
two processes separate at 80% under cross-validation, on this feature set."* Never *"we can read
the maker."* And Ginzburg's boundary stands over everything. The evidential paradigm is
individualising, conjectural, with an unsuppressible speculative margin. **An instrument that
outputs a confidence percentage claims a status this entire tradition says is unavailable**, which
is why the field built a graded vocabulary instead.

## §11. The instrument dashboard: adopted heuristics with measured strength

**Only heuristics measured in this project enter; candidate imports stay in §§6–8 until tested.**
Strength is always against a named baseline. The same number means opposite things next to a chance
rate and next to a field bar.

| heuristic | measured strength | baseline | status |
|---|---|---|---|
| **within-artifact variation, surface features** (§2) | 0.565 macro-F1 topic-controlled; 0.969 on the uncontrolled split | floor 0.444; field bar 0.830 / 0.959 | real, **not competitive where topic is controlled**; the uncontrolled win probably rides topic |
| **within-artifact variation, probe activations** (§2) | human long-form variance 0.0102 vs machine 0.0065, *p* = 0.002 | matched series length | **SUPPORTED (test), first pass.** The operationalisation nobody pre-empted; register uncontrolled |
| **visibility partition** (§6) | authors at 0.78 (low-vis) vs 0.38 (high-vis); draft-stage 0.48 (high) vs 0.30 (low) | chance 0.10 / 0.33 | **SUPPORTED (test).** Clean double crossover, first pass |
| **revision homogeneity** (§7) | real 0.45 vs spliced 1.94, AUC 1.0 | synthetic cross-author splice | **SUPPORTED (test), first pass, weakest adversary.** The realistic imposition case is untested |
| **provenance prior** (§1) | ratio shift +0.007, *p* < 2×10⁻⁸, three corpora | paired identical text | **SUPPORTED (test), replicated.** In the reader model; human-side untested |
| anomaly entry (§2) · confidence trajectory (§4) · interest ratings (§5) · effort correlation (§8) | | | unmeasured: one simulation bound, a series never recorded, an hour of his time, an undefended proxy |

**What the dashboard says.** Five heuristics now carry numbers, up from one at the start of the
week, and three of the five landed at first-pass strength with their sharpest caveats named in
their own rows. The stacking question is still premature but no longer empty. The two variation
measures, the visibility partition, and the homogeneity statistic are plausibly independent
channels, which is what a stack would need, and the program defers stacking until choice recovery
validates what any of them measure. Confidence: the surface-variation number is replicated and
controlled; the four new rows are one bad test away each; everything unmeasured is untested.
