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
But that models a cooperative game, not every maker-reader relationship, and his own caveat marks
the limit. *"Humans actively, constantly pretend they're teachers under certain framings. Does that
always hold?"* It plainly does not; concealment, propaganda, seduction, and audience mis-modelling
are the countercases, and a wrong communicative assumption licenses confident inference from
structure placed to mislead, the same error the expertise literature calls failure to transfer,
running the other way:

> That's kind of the whole premise for **failure to transfer** – this lack of transfer as a result of
> domain-specific expertise. **Same idea, different direction.** Expertise can improve some
> inferences while creating incorrect assumptions about another set of stimuli or domain. And we
> expect this to fire in particular with AI.

And it lands on generated text specifically:

> **AI is being treated like a teacher also**, or at least like a human that's trying to express
> themselves in a way that is to be understood. It's getting the benefit of understanding that it
> is not granted. So people **converge faster, perhaps, onto a false mental model.**

One conjecture rides on that convergence claim, reaching outside this project's own evidence and
held as exactly that:

> This may be the reason for some of the unusual results out of education, where AI-assisted
> learning helps one gain knowledge quickly but then it fades away. I would assume due to the lack
> of structure that would be boiled down through the slow-wave thalamic pulses they recently pulled
> out, the **vectorization of your memory through dreams**. That process would be more difficult
> without structures both **handed to you human-shaped** and existing in the first place as a
> **human-constrained solution set**.

The provenance prior is no longer speculative. A reader model's affective read of identical text
shifts when told the text is machine-made, small, fixed in direction, replicated on three corpora
(the measurement is canonical in the model-side ledger, `THREE_COGNITIVE_LAYERS.md` §7). Whatever a
disclosure label does to a human reader, the reading machinery itself is not neutral to claimed
provenance.

> I think what actually people do is they assume what they would need to do in order to come to
> this conclusion. And it's probabilistic in a lot of ways. You can't just say, "Oh, I would just
> instantly know." You'd have to somehow put yourself in a situation where you'd say, "Oh, I could
> see how I could have come to that conclusion." And that allows you to arrive to it in the same way
> they did to an extent, or at least you believe you arrived in the same way they did, whether or
> not that's true. Again, you started with your own perspective.

On why the shortcut works *(the 2026-08-22 pass)*:

> Explicit self-reconstruction works because of the similarities between you and the creator.
> That is the reason it works, not because it is inherently an optimal strategy, but because you
> can use the similarity to cheat.

> You would expect the same effect with model families, with similar models being able to invert
> one another more easily. More generally, the more you are like the person who created the thing,
> the easier it is to reverse-engineer and understand. Archaeology is hard; talking to your wife
> is easy.

**This is the best viewer-coherent reconstruction: the reader begins from itself because shared
organization supplies a cheap candidate generator, then adjusts toward a maker model using
artifact evidence and context. Similarity makes this shortcut more useful; it does not make the
reconstructed route historically correct.** It supplies
candidate routes and effort estimates, then is adjusted using evidence about the maker. It also
creates a characteristic failure: a sufficiently flexible reader can explain almost anything as
something the reader might have done. Reader identity, domain competence, and conditioning must
therefore be recorded as part of the instrument.

> If I'm looking at an artist, what I will try to do is find the biggest difference between their
> contextual space and mine that would affect a whole bunch of other things associatively. I'll set
> that in place almost manually: "Oh, this artist is from the 1400s."

*2026-08-27 walkthrough; spoken wording lightly reconstructed.*

**Context can reorganize several expectations together.** An era, role, or commission can change
the reader's estimates of tools, opportunities, institutions, and audience at once. Attention to
that difference is a proposed way to adjust the self-based candidate model. The adjustment remains
uncertain and must yield to individual evidence; category membership supplies no fixed model of a
person. Its usefulness and correction belong to the existing open self-initialization and
differentiation hypotheses (HH-23, HH-25).

The strongest live prediction is broad and graded rather than exclusive. A relevantly similar
reader need not gain access to an inference target that another reader cannot represent. It may
instead need less evidence or deliberation and become slightly more accurate or better calibrated
across many goal, process, and continuation judgments. The advantage is conditional on similarity
along variables that matter to the current decision. When self and maker diverge on that variable,
the same shortcut can amplify projection; successful use therefore includes detecting conflict
and correcting toward target evidence.

Three distinctions must not be collapsed: self-based versus target-specific evidence, rapid
versus deliberative processing, and affective sharing versus cognitive mentalizing. Interpersonal
studies link direct accuracy, but not assumed similarity, with slower judgments;
self-referential mentalizing is used especially for similar others; and lesion and cue-modality
studies support partially dissociable sharing and mentalizing routes that can contribute to the
same judgment. This supports a reader that can initialize candidates from shared self-structure
and correct them with target evidence. It does not license a one-to-one mapping of fast with
affective or self-based, slow with cognitive or target-specific, or a fixed serial neural
pipeline. Transfer from interpersonal judgments to artifact inversion remains open (Sened et al.,
2020; Mitchell et al., 2005, 2006; Shamay-Tsoory et al., 2009; Jospe et al., 2020).

**(HH-23:** Artifact inversion combines an assumed-similarity initialization with target-specific
correction; relevant reader-maker similarity should yield a modest, broad efficiency or
calibration advantage, while misleading similarity should increase error until corrected.
**OPEN for artifacts; supported only as an interpersonal analogue in the cited studies.** Stage 3
crosses measured similarity, evidence dose, compute, and conflict; no human-reader artifact test
exists. **Model-side evidence is split (test, L179, L192).** Relatedness predicts original-artifact
reading; no prospective self advantage was demonstrated in the separate record task
(self-minus-other −0.10, ns). Agreement between two target samples measures repeatability, not a
predictive ceiling. This does not establish a general representational-versus-predictive
division.)**

**Model-family similarity is the present analogue construction. If sibling models recover one
another's recorded process choices better after surface and capacity controls, the shared-
organization hypothesis gains a model-side foothold. If only the exact checkpoint wins, or the
effect disappears after paraphrase and style control, the result is a generation fingerprint.
Neither outcome directly measures closeness or embodied similarity between people.**

**(G172: SUPPORTED for relatedness on original model artifacts; mechanism OPEN (test,
L163-L168, L177, L179, L217-L219).** Crossed reversals and within-reader contrasts weaken a
reader-quality-only account: a second and a third maker family each read best by their own
family's readers, and the within-reader adversary, where reader quality cannot move, keeps the
own-family effect in five of eight readers. The gradient is monotone inside every family
separately (L218), and exact weights beat same-family siblings inside both measurable families
(L217). Survival under weaker rewriting does not generalize: the strongest independent eraser
removes the advantage, first with only 88 of 250 artifacts retained and the Smol survivor
count below its declared floor (L225), then with the yield raised to 143 and both families
above floor, own-minus-other 0.001 in each (L251). The summary bottleneck was not uniformly fifteen
words. Family averages required corrected aggregation before renewed numerical or significance
claims, and that correction has since landed: the first read kept one reader per artifact and
called SmolLM weak, while the corrected full-matrix margins are qwen +0.0137, smollm +0.0096,
olmo +0.0365 (L236). The later hash split is retrospective robustness, not untouched
confirmation (L180, L182). Attribution context does nothing to the likelihood reader in either
direction (L181), so what signal there is rides on the text rather than on identity beliefs. A
policy put into the weights reads back by the exact instrument in a second independent adapter
cohort (L178/L224). Shared organization and shared convention remain competing explanations.**)**

**(E01-S3:** the self a model reader could project is exactly readable under a fixed
instruction frame and is frame-conditional under another (test, L176). All three instruct
readers carry a sharp unprompted profile under the plain frame (posterior mass 1.00; Qwen's
differs by domain); a paraphrased frame flips the 360M model's profile robust→precedent in
both domains, holds the 1.7B model's where it realized, and leaves Qwen unreadable (1 of 40
and 0 of 40 episodes realized). **NARROWS the self-model prior:** in models it is an
instruction-shaped default, not a stable prior, so every self-projection test fixes its frame
by construction. The projection itself then split by capability (test, L193): the reader that
cannot consume records defaults to its own preference on conflict items (error intrusion 0.58
vs the 0.33 symmetric null) while the record-reading reader errs symmetrically (0.29), which is the
assumed-similarity initialization with the correction step present versus absent, live in two
models. Active search is not the correction's source: offered a higher- or lower-information
record, both readers take whichever is listed first (position rate 0.86-1.00 vs informative
rate 0.36-0.38; test, L194). Records predict a maker's next choice on a second domain
for the stronger reader only (test, L228: Qwen 0.56 on process as on infra, p=0.007;
SmolLM at chance), and mixed-policy makers are near unpredictable from records for both
(L227: 0.375 and 0.25 against 0.25 chance, n=24), so record reading is reader-bound and
policy-purity-bound.**)**

## §2. Finding an entry point

> The thing that most jumps out at me isn't mistakes but **unusual constructions, or odd decisions
> that I can't find an explanation for.**

An anomaly is one high-yield entry point, especially when it exposes alternatives, but a reader
can enter wherever prior expertise provides traction: purpose, technique, mechanics, familiar
convention, explicit context, or an unusual construction. From the entry the reading runs
purpose→method and method→purpose. His own discomfort, recorded because
he raised it. *"I hate that a lot of this is me picking out mistakes and typos, which is also a
trick for AI and it's not okay. But it is a way of extracting decisions."* *"The mistake, and the
way the author can be presumed to have responded to it,
is one of the more useful pieces of information once you have observed it."*

> I think mistakes are actually and almost certainly an interesting vector that is almost always,
> if you can find it, a way into the author's perspective. Sometimes the author tries to fix it, or
> conceal it, or cover it up in some way, and you can catch them. That's very different from making
> a mistake and not noticing or making a mistake repeatedly.

A mistake is a sharpened anomaly for which evidence supports a mismatch between a choice and the
maker's operative trajectory. The strongest evidence often comes from handling: repair exposes a
preferred counterfactual, concealment exposes recognition and a protected goal, repetition
suggests habit or a stable transition-map limitation, and non-response suggests either
non-recognition or indifference. Unfamiliar order remains unresolved until evidence distinguishes
expertise, convention, secondary purpose, accident, and error (the trace classes are canonical in
[`DECISION_TRACES.md`](DECISION_TRACES.md) §3).

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
> iconography. But the veneer needs to go away as a term. We're talking about **polish**, and it's
> not just imagery and iconography, or aesthetics, or teaching. It's **everything directed at the
> reader.**

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

Stage 7's constructed histories give the honesty note a measurement (L351): a process reader
localizes a one-time control switch from the event record and survives a surface matched from
one word pool, where stylometry sits at chance; a pure style shift with no change of control
still draws three quarters of its mass; and the free-text readers read under the stylometry
stack on every kind. Detection of discontinuity from process statistics is real on the record
and absent from the final artifact; whether the variation is goal variation stays the open
interpretation.

**And the revision-wobble test is retired on his own account.** Human redrafting was the wrong
axis, before the null even needed explaining:

> The problem is that revisions from a human author are always going to carry **the same level of
> intent density across the board.**

> Actually, I'm going to caveat that. All human behavior having the same level of intent density,
> by definition that's not the case. But you would expect **a more human-readable resolution in
> intents, as they shift at more human timescales**, whereas the more rapidly shifting goals from
> the AI would blur together into **a kind of gray entropy space.** I'm not sure about that. It's a
> guess I can argue either way. Just an area of interest, perhaps.

The caveat is a hypothesis and marked as one, not a claim this file asserts; the retirement of the
wobble test stands either way.

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
| **G165** | Explicit route generation (a self-enacted production route, or predicted evidence per candidate) improves recovery of recorded executed choices over direct reading | **NO-GAIN where direct reading is strong (test, L151); HURTS where it is weak (test, L153), and the wing is CLOSED.** On the realized-choice events: zero delta and minus two points, every gate quiet. On the revision-delta events where the change block beats the direct reader: self-route costs seven points (p = 0.0006) and invents purposes on unrevised text at 0.065 against the direct reader's recorded 0.000, while evidence-prediction gains three points, noise-compatible. Explicit generation is rhetoric the reader then follows over the evidence |
|   | | *(this row's history is a NO-GAIN root on the strong substrate 08-21 morning and the HURTS discriminator on the weak substrate the same afternoon; the null-discriminator rule is spent)* |
| **E02-S3** | A reader given a maker's choice RECORD predicts their next choice better than one given nothing or matched filler, on known-policy targets | **SUPPORTED (test), one reader deep.** +20 points paired (p = 0.0026) against an exact ceiling of 1.00, but the entire margin is Qwen's (0.57 vs 0.23); SmolLM-1.7B reads the record at filler level (0.27). The self-first two-step neither helps nor hurts. Instrument gate for the Stage-3 route factorial |

**What the table says.** The entry-point family has one live positive, one honest defeat, and now
a closed question with a direction. The
reader's own affective series moves through human text and not machine text, while every surface
operationalisation of the same idea loses to the field's bar once topic is controlled. Ordering
effects are bounded near zero, the wobble test is retired on the curator's own account, and the
anomaly rows, the family's core, remain unrun. The self-simulation STRATEGY is now bounded from
both sides: externalizing a production route buys nothing where direct reading is strong and
actively damages where it is weak, with a measured fabrication cost the direct form does not
carry, so the bounded reader's value is direct reading plus calibrated refusal and any future
generate-then-judge stage owes its own fabrication gate. That bounds the strategy, not the §1
self-model prior itself, whose implicit form the direct reader may already be using and which
no test here reaches. Confidence: the
probe-activation result is one
bad test away; the surface defeats are replicated and controlled; the generation bound is
one bad test away as a pair, two substrates deep in one reader family; the record-route gate
is one test in one environment, with its reader asymmetry (one model uses records, one does
not) still unexplained; the rest is untested.

## §3. Traversing explanatory levels

> Walking up to an unknown oil painting, you can engage with it on the level of **metaphor** – why did
> the author craft what they did. On the level of **technique**, like perspective. On the level of
> **mechanics** – how did they move their hand as they painted.
>
> **You can use any piece of knowledge about any of those three channels to begin the decoding.**

Working vocabulary. **Purpose** (local and higher-order intent; "metaphor" names a subtype of this
level, and is narrower than the level needs, since the top has to carry goal), **technique**
(organized method), and **mechanics** (physical realization). While the three he initially stated
are supported in literature, they are **more categorical than they are separable in any real
way**. Dennett's three stances are the closest citation (physical/design/intentional), and
Panofsky was the wrong one. He rejected it
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
hierarchy (means-ends diagnosis from any level, decades of use) is worth reading as a candidate
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

The quote is pulled from a specific reading of one artifact, the updating and active-search
process run live while answering author and provenance questions during early corpus
construction, and *"the read-alongs ended up being more useful than the actual corpuses."*

**Confidence moves while reading, and the trajectory carries what the endpoint does not.** Every
reading this project records is a final number, so the series has never existed to be checked. The
reader also searches actively. Re-reading (each pass recovering lower-confidence
attributions from the tail), **epistemic foraging** for biography and further works,
where *everything is an artifact* becomes operational (context supplies additional
observations but is not automatically trustworthy), and switching levels when a
hypothesis fails, per §3.

**Context reweights the generative model rather than dictating a story** *(2026-08-21)*:

> The low-quality-paint inference was a shifting of possibilities – the generations of your
> generative model being weighted differently – not an immediate inductive set of steps.

Context does not license a story in one step. It changes the relative probability of
maker and process hypotheses, which should then change predictions about other evidence.
A useful context cue improves held-out recovery; a misleading cue should cause a
measurable, directionally coherent error; if neither occurs, the cue merely inspired a
narrative. The tool-conditioned form of the same rule lives in §6.

**The current ordering conjecture places context especially at maker differentiation.** The
artifact first supports a self-based candidate distribution; biography, prior work, tools,
culture, role, and source reliability then help move that distribution toward this maker. This is
not a fixed serial architecture. Context-first and joint processing remain live rivals, and any
order that lets a false assertion overwrite strong artifact evidence is a trust failure rather
than successful differentiation. Attention allocation, epistemic weight, process uptake, belief
uptake, and value change remain separate outcomes.

**And apparent errors should eventually revise the reader's model of the maker**:

> Every apparent mistake is suspicious because it may mean you do not understand the maker. If too
> many of them are ignored, it becomes more likely that they are intentional and that your model of
> what the maker was trying to do is wrong.

Clusters of unexplained deviations are a posterior-predictive failure of the current
maker model. Local repair stories may explain individual cases, but the reader must
compare them with a global alternative, unfamiliar expertise, a wrong primary goal, a
hidden constraint, or a different maker and process family, and the threshold is
empirical: which update better predicts held-out choices or later handling. This is not
permission to declare every dense anomaly cluster expertise.

On what the shortcut may cost *(the 2026-08-23 pass)*:

> Calculating how you would do it is where indoctrination sneaks in. It is the shortcut you use
> because it is fast and lets you grab process information quickly. It is gated later by value
> similarity, which you calculate with lower confidence.

This names a temporal risk, not a demonstrated neural sequence. A reader may acquire a
reader-enactable process before it has stabilized a historical maker model or evaluated the
source's values. Process uptake, belief uptake, and value change are different outcomes and must
be measured separately. The model-reader context results below are adjacent evidence about
over-trusting supplied assertions, not evidence that human indoctrination follows this mechanism.

> I would maybe expect that protective effect to be imperfect.

*2026-08-27 walkthrough; spoken wording lightly reconstructed.*

The proposed protection from media literacy is better inference about why a source selected and
shaped its evidence, not immunity or automatic distrust. Technique training has produced benefits
in some studies, while a counterbalanced inoculation study found no overall discrimination gain.
Distinguish improved discrimination from a stricter rejection threshold; professional expertise
and insight alone have not been established as a general shield.
([Roozenbeek et al., 2022](https://research-information.bris.ac.uk/en/publications/psychological-inoculation-improves-resilience-against-misinformat/),
institutional abstract read;
[Seabrooke et al., 2026](https://link.springer.com/article/10.3758/s13423-025-02827-x),
methods and results read.)

One external caution bears on the whole series family. A study of hidden states as author
representations found document-level mean pooling best, which is evidence against series-carrying
claims at the representation level. Not decisive (it optimized for identity, not maker state), but
the reason to expect modest effects.

| # | hypothesis | status |
|---|---|---|
| **HH-9** | The confidence trajectory across a reading carries more than its endpoint | **OPEN.** Every reading this project records is a final number, so the series has never existed to be checked |
| **G64** | Re-reading one artifact recovers the tail | **OPEN.** Canonical in the triple inference §5; the reader-side strategy is this section's |
| **G167** | Declared context reweights the reader's maker-model distribution, where a false context must not steer equally | **PROJECTION where evidence is absent (test, L155); MIXED at 0.44 where evidence is strong (test, L157); the wing is PAUSED.** With nothing readable to resist it, a false card steers 95 percent as hard as a true one and erases the reader's abstention. Against evidence the reader provably reads at 0.86, a false note still costs forty-two points, wins the toss-up at 0.53, and the conflict is named only 0.15 of the time even when the format offers the option; a true note lifts the reader to 0.99, so any supplied note is treated as high-grade evidence regardless of truth. Context-trust is a separate defect from evidence-reading in this family |
|   | | *(this row's history is the projection root and its evidence-conflict follow-up, both 08-21, the wing pausing per the brief's W3 routing)* |
| **HH-24** | Self-based process reconstruction can update a reader before source and value-similarity appraisal finishes | **OPEN.** The proposed indoctrination interval; requires separate measures of process uptake, belief uptake, and value change. G167 is adjacent instrument behavior, not evidence for the human mechanism |
| **C01** | A coherent context model improves held-out prediction beyond the same facts listed, and a wrong context costs | **INCONCLUSIVE on the first half, REFUTED on the second (test, L239), full size and expanded.** Bundle minus facts +0.10 nats over 128 worlds and +0.09 over 256, the interval crossing zero both times; an incorrect bundle helps as much as the correct facts (+0.59 to +0.72 over no context) and irrelevant background helps by a third to a half of a nat, so the readers take the frame and not the content |
| **C02** | A reader uses a contextual prior without staying trapped by it: individuating records correct a misleading context | **REFUTED as a flat curve (test, L241): COUNTEREVIDENCE at 128 worlds, INCONCLUSIVE at 256.** Six records after a misleading prior move the direct log score -0.20 nats at 128 worlds and -0.08 with the interval crossing zero at 256, while the exact ruler climbs 0.13 to 0.16; the valid prior's curve is flat (0.00); a misleading prior helps at zero records as much as a valid one (+0.38 against +0.32); neither two-pass route helps; 0.44 of the mass stays on an option stated unavailable |
| **C03** | The readers choose evidence by its expected information about the maker (active reading) | **COUNTEREVIDENCE (test, L246), 204 usable worlds of 256.** The redundant probe is chosen 0.78 of the time and the informative one 0.08, half of every pick going to the first listed; 8 percent of the exact selector's expected gain is captured, a quarter below a random pick; the realized gains are flat at this size |
| **R01-S5** | The reader chooses the evidence route by its exact information about the hidden future choice, beyond a random selector | **SUPPORT BY BAND, A FLUENCY POLICY BY THE RIVALS (test, L270), 159 worlds past the floor.** +0.11 nats over random; −0.05 against always taking the easiest-rendered route, which is the action record in every world and the most informative in three of four; the reader's departures from it are unrelated to which route is best (27 against 28 percent). Second contract with per-world description rendering (L300): the easiest description is the note in every world, the readers take it a quarter of the time, prefer the action record, and capture +0.06 over random and +0.10 over always-easiest, tracking 0.36 against 0.26. Ease crossed inside a route type under a validated ruler (L311): the description rendered harder (mid-dots) is taken MORE, by 0.25 of probability on both readers (Qwen 0.40, SmolLM2 0.10), so the fluency policy is dead and anomaly attraction replaces it; the both-plain cell keeps the record-over-note preference at +0.08 over random; the archaic cross separates the confound: harder-but-not-deviant is ALSO taken more (−0.24 pooled; Qwen −0.42, SmolLM2 −0.07), so the attraction is difficulty's, not visual anomaly's (L327) |
| **R02-S5** | Stated reliance follows a record's exact information rather than its ease of reading, the two crossed by construction | **SUPPORT BY BAND ON THE QUANTITY SIDE, CONFIRMED ON THE RESERVE (+0.18 [+0.15, +0.20], L281); THE EASE ARM UNREALIZED (test, L271), 256 worlds.** Reliance +0.16 for six records over two; −0.03 for the stilted rendering, which the reader's own token probabilities rate as the easier text (−2.82 against −3.07 per token), so the fluency contrast never existed. Second contract (L301): +0.07 on two readers; the ease ruler (mean per-token log probability) rates capitals and mid-dotted text as easier than the plain record, so the ease arm cannot be realized under it. Under the validated ruler (L310) with the capitals realized in every world (L314): Qwen +0.15 for six records over two and −0.03 for plain against capitals (the harder text relied on MORE); SmolLM2 flat on both (−0.01, +0.01); the fluency account is dead on both readers and the quantity effect is the Qwen family's; at equal rendered length the effect follows information (+0.075 [+0.066, +0.084]) and not length (−0.003 [−0.011, +0.004]), the padded six matching the two (L327) |
| **R05-S5** | Along the evidence stream the reader's stated confidence tracks the exact information the stream carries | **VALID_NULL (test, L329), 192 world-series per reader, five cuts each.** Pooled slope agreement +0.012 [−0.001, +0.026] against the analytic half floor; Qwen +0.034 [+0.001, +0.069], under the band; SmolLM2 −0.009 [−0.044, +0.022]; ECE 0.316, the larger reader mostly sure (0.55 of its confidence mass) and worst calibrated (0.414): the J03-S5 one-cut fact in series form, and confidence is not an information meter in these readers |
| **R03-S5** | Worked demonstrations of choosing the diagnostic route transfer as expertise (used where diagnostic) rather than familiarization (used wherever shown) | **FAMILIARIZATION (test, L272), 256 worlds.** Three demonstrations raise the route's use to 100 percent and three misleading ones lower it to 0 in every world, the same where the route is worthless as where it is diagnostic (interaction −0.02 [−0.06, +0.02]); calibration unchanged; on two readers 1.00 and 0.01 to 0.02 with the interaction −0.01 (L302) |
| **R04-S5** | The reader buys forensic access when its expected information justifies the cost and declines it otherwise | **NO POLICY (test, L273), 256 worlds.** Buys in 48 percent of worlds with AUROC 0.54 to the exact gain; net gain per cost −0.24 against −0.18 for a coin flip and 0 for never buying; the step never pays on this construction, so only the decline side was tested. Second contract, the step paying in a third of worlds (L303): two readers buy in 0.58 of worlds whether it pays or not (AUROC 0.50), and the exact policy realizes the least gain because the bought evidence is not used |
| **HH-25** | Reliable maker context is especially useful after an initial artifact/self prior has formed, during maker differentiation | **OPEN for differentiation order (test, L195, L209, L211, L213, L214).** Ordering observations stand: the record-reading reader drops 0.67 to 0.40 when the question precedes the record, biography trades at parity with a six-choice record in both directions, and the late-fusion ruler fails on a second domain too (L229). The easy updating gate failed. Recall does not establish functional evidence use, so the recall split cannot isolate weighing from attention or comprehension. The stored readout follows an outsider's wish at 40/48, and an explicitly ignorant outsider's wish at 45/47 (L231). The re-run with every generation persisted and a parser-free likelihood readout (L252) keeps the numbers, 0.79 and 0.92 hint-following, with refusals and contamination small and separated, so the override is the readers' and not the parser's; what no readout of the answer separates is belief adoption from compliance, which stays open |

**What the table says.** The section's first numbers land on the context-reweighting rule's
failure side, now measured at both ends of the evidence axis. Where the artifact offers
nothing readable, a supplied production fact functions as an instruction, followed at full
strength regardless of truth; where the artifact offers evidence the reader provably reads,
the false fact still wins about half the time, the true fact lifts performance past the
evidence alone, and the reader almost never names the disagreement it is silently resolving.
The coherent summary is that this reader family assigns supplied assertions roughly the
weight of its own reading and no truth-tracking discount at all, so context-trust is a
defect class of its own, separate from evidence-reading and from the honest abstention the
same instrument shows elsewhere. The useful-cue half of the reweighting rule survives only
in the degenerate true-note case, which no product interface can rely on since truth is what
the interface does not know. The Stage-3 wish rows point the same way but cannot carry the
psychological reading: the stored readout follows an outsider's wish at 40/48 and an explicitly
ignorant outsider's wish at 45/47, and with the raw generations missing and a phrase-matching
parser standing in for them, compliance, answer contamination, task confusion, and extraction
error were all unresolved until the repaired readout kept the numbers parser-free (0.79 and
0.92 hint-following, L252); the override is measured, and belief adoption against compliance
stays unseparated. Stage 4's first full-size context card lands on the
same side from a third direction: with content and framing separated by construction, a
coherent maker model beats the same facts by a tenth of a nat with the interval crossing
zero, and a wrong model helps exactly as much as the right facts, so what these readers
take from context is the frame and not the content (C01); and the second card shows the
trap: six individuating records after a misleading prior leave the prediction where it was
(worse at the first size, flat at the second) while the valid curve is flat and the exact
ruler climbs, so these readers do not use the records at all (C02); and the third card
closes the track from the selection side: offered a probe that would tell them the most
about the maker, they take the one that restates what they already have, three times in
four, and capture eight percent of the available information (C03); offered routes by
description on a fresh construction, the reader takes the easiest-rendered one, which there
happens to be the informative one, and beats a random selector while losing to the policy of
always taking the easiest, its departures unrelated to which route is best; when ease is then crossed
inside a route type, the reader goes to the harder-rendered description, not the easier, by a quarter
of the probability on both readers, so the fluency reading of that default is dead and what remains is
a record-over-note preference plus an attraction to the anomalous option, the human anomaly entry
point showing as a menu bias (R01-S5); asked how much it would rely on a
record, it says more for six entries than for two and no less for a rendering meant to be
harder that its own token probabilities call easier, and, once the harder text is one the
validated ruler calls harder, no less for that either (R02-S5), so what is measured is trust in
quantity, confirmed on an untouched reserve at the same size, present in one reader family and
absent in the other, and the fluency question is closed against fluency (the post-close receipts complete both stories: the archaic rendering, harder by the validated ruler and not visually deviant, is taken more by the same quarter of probability, so the attraction is difficulty's rather than visual anomaly's, Qwen carrying it at −0.42 with SmolLM2 at −0.07; and at equal rendered length the reliance effect follows information, +0.075, with length itself at −0.003, so the quantity effect was information all along and remains the Qwen family's, L327; and its stated confidence along the stream tracks exact information at a valid null, +0.012 pooled, the confidence series landing as the file's newest instrument, R05-S5, L329); and shown three demonstrations of a route,
it takes that route in every world and the opposite route under three misleading ones, with
no regard to whether the route is diagnostic there (R03-S5), the supplied-fact-as-instruction
result again, now for procedure rather than content; and offered a costed forensic step that is
never worth its price here, it buys half the time at random to the gain (R04-S5). The
adjustment mechanism this section proposes has no model-side analogue at this scale, from any
of the three directions it could have shown; the reweighting rule's useful-cue half is untested by
them because they do not read the cue. The confidence series remains the cheapest unbuilt instrument in the file, the uptake-lag row is
a human hypothesis rather than an interpretation of the model-context failure, and the external
mean-pooling result remains a reason to expect modest series effects rather than to skip the test.
Confidence: the earlier true/false context effects are one bad test away, one construction family
and one reader family deep; the frame-not-content and no-correction reads are one bad test away as
a pair, two readers, one construction family, the second read expanded and flat; the no-active-
reading read is one bad test away, its realized side underpowered, and its fresh-construction
replicate reads as a genre preference with anomaly attraction, the fluency reading dead on two
readers and one construction, difficulty and anomaly not yet separated; the Stage-3 wish override is
one bad test away, measured twice, its psychological reading (belief against compliance) untested;
differentiation order, the uptake interval, and the rest remain untested, logic only.

## §5. Continuation and stopping

> Interest comes from finding decisions that you can't attribute meaning to, which implies there's
> more meaning you don't fully understand – either a **process** you aren't aware of, or an **extra
> motivation** you aren't aware of.
>
> **Artsiness is making a lot of unexplained decisions**, getting into a flow state in which you use
> the decisions given by a subordinate goal, doing things you aren't quite sure why you're doing.
> Often related to proximal goals, but sometimes just for the sake of doing it. That's different
> from **artfulness, which is simply decision density.** Aesthetics is the appearance of having made
> unexplained decisions but for a reason, in an ordered sense. And unexplained decisions show up
> when **structured choices are unexplained**; those tend to create interest. If you identify the
> structure but can't identify the function of it, then it remains **part of a puzzle to be
> solved.**

> It is fair to say that order you don't understand can often look like a mistake. So, an
> interesting thing is the name for that order when you haven't yet decided, or when you've decided
> it isn't a mistake, perhaps, even if you don't know what it is. Perhaps that's what all of
> aesthetics is.

The first part sharpens "ordered but unexplained" as an abstention state between comprehension and
error. The suggestion that this may define all aesthetics remains an open extension, since
aesthetics can also involve fluency, attraction, convention, affect, and successful recognition.

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
- **Deployed expertise is tool-conditioned**, his own statement of the archaeology
  boundary (2026-08-21):

  > Deployed expertise is context-relative. If you do not know what tools they had, it can become
  > impossible to work out what the trace cost or what competence it required.

  The same artifact trace can imply very different work under different available tools,
  which is the probabilistic-reweighting rule of §4 in its choice-versus-constraint form.

| # | hypothesis | status |
|---|---|---|
| **G85** | Intention elicitation with a pre-registered target | **ALREADY BUILT.** The intent ladder is this protocol, validated on stone since 2010, with the R² = 0.655 ceiling attached |
| **G86** | A mechanical null model: subtract what the medium forces | **OPEN.** The right shape for choice-versus-constraint; the analogous model degrades badly off the bench. The program's event-recovery harness carries this as its forced-constraint null |
| **G87** | Stage-differentiated partition by visibility | **SUPPORTED (test).** Clean double crossover; canonical row in `DECISION_TRACES.md` §3, dashboard §11 |
| **G88** | Error handling (repair, concealment, compensation, non-recognition, and repetition) recovers maker trajectory better than error rate | **RULER VALIDATED IN CONSTRUCTION (L147); BLIND AT ESSAY GRAIN (L150); SEPARATES AT LONG FORM WITH REALIZED HEDGING (test, L158), at mechanical parity and without localization.** The likelihood ruler separates all five planted classes at 1.0 in the gridworld. In text the answer is now resolution-shaped end to end: blind at 0.417 on 400-word essays, separating at 0.77 on 900-to-1300-word artifacts whose concealment hedging was verified realized at generation, with a five-line post-plant hedge counter at 0.79, the reader quoting the carrying sentence at a hit rate of zero, and clean rewrites still pulling 0.40 invented issues as the standing warning label. The signal is hedging density; the reader integrates it diffusely and cannot point at it |
|   | | *(this row's history is the ruler pass 08-20, the essay-grain null 08-20 evening, and the long-form separation with the corpus's own refuse-and-repair arc 08-21)* |
| **G89** | Rigidity under perturbation as the novice signature | **OPEN.** Implies the active probe |
| **G90** | Report separability as a cross-validated confusion matrix | **OPEN, a reporting convention**, and the program's required output format for choice recovery |
| **G91** | Inter-annotator agreement and per-feature accuracy before believing any extraction | **OPEN, and mandatory.** An aggregate concealed a worse-than-chance category |

**What the table says.** The forty-year practice arrives as one measured win, one protocol we had
already built, and a discipline. The visibility partition produced a clean double crossover on its
first pass, the intent ladder turns out to be the field's own elicitation protocol with a ceiling
attached that reframes every recovery number, and the rest of the family is method, not yet
measurement. Error handling (G88) now has a complete first arc: validated in construction,
blind at essay grain with an honest instrument, and separating at long form once the
concealment was verified to realize hedging, which confirms the resolution framing the null
predicted and prices the channel honestly, since a mechanical hedge counter matches the
reader and the reader cannot quote the sentence carrying the signal it reads. The error-
handling import from the field's practice survives with a sharper shape than the field
states it: handling IS more informative than rate, its text carrier is density rather than
locatable structure, and the reader's access to it is integrative rather than evidential.
The distinction between an instrument that fails and a signal that is absent at a resolution
is what the validation-first order bought, twice. Confidence: the partition is one bad test
away; the ruler validation is one bad test away and constructed-world only; the text arc
(null at short form, separation at long form) is one bad test away as a set, one corpus
family deep with its fabrication warning attached; the ceiling import is replicated in its
home field; the remaining rows are untested.

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
| **G80** | Reserve versus overpaint, on text structure | **DEFLATED BY ITS OWN SECOND COMPARISON (test, L92 then L98), and the four-family arm confirms it (test, L105).** Abandoned scaffolding is countable and ruler-gated; the original 2× separation belonged to the specification-stacked prompt, and across all four register-matched fiction families no cell separates from human drafts after correcting for the four looks (rates 0.15 to 0.37 against 0.19; the one nominal p = 0.045 does not survive). The instrument measures **unfulfilled prompt burden**; the reserve/overpaint import needs a subtler observable |
|   | | *(this row's history is a 2× machine separation on 08-12 morning, deflated the same evening, confirmed across four families on 08-14)* |
| **G81** | Self-revision is homogeneous, imposed change is lumpy | **SUPPORTED (test, L52), first pass, against the weakest adversary.** 66 authors, real revision dispersion 0.45 vs cross-author splice 1.94, separation perfect (AUC 1.0). The ceiling is the caveat, since a crude splice may be read as *different author* rather than *imposed change*; the realistic same-register imposition is the untested case |
| **G82** | High internal consistency indicates *imitation*, not expertise | **OPEN.** May invert an assumption we hold |
| **G83** | Adopt the graded attribution vocabulary | **OPEN** |
| **G84** | Two channels: falsifiers veto, style proposes, never averaged | **OPEN, architectural.** Every historical catch came from a hard falsifier |

**What the table says.** The concealment family now has two numbers, one of which just taught
the standard lesson. Real self-revision is measurably even-handed, against the crudest possible
splice, so the mixed-provenance question stays open. The scaffolding cue is countable and its
first-pass separation did not survive its own register-matched control: what it counts is
unfulfilled prompt burden, which follows the instruction load, not the maker, and the
reserve/overpaint idea goes back to needing an observable that structure alone cannot fake.
The admissibility filter's fourth criterion remains the best-rated unrun import; it predicts
where habit is switched *off*, which is information every other measure discards. Confidence:
the homogeneity result is one bad test away; the scaffolding instrument is re-scoped with its
provenance reading rejected on the matched arms; everything else is untested.

## §8. Communicative shaping: the bard

**2026-08-07.** His refinement of the teacher assumption. A maker is something more specific, and
the difference is the part nobody has formalised:

> What we're actually looking for is **a bard**, to be a little bit more precise. **There are two
> motivations. They want to grab your attention through aesthetic capture, and they also want to make
> it easy for you to ingest the data.** And that's the teacher aspect.

> How on earth do they shape it in order to create that effect? **I assume they try to model the brain
> of their listener. Of course they do.** Which makes all interactions this kind of **collaborative
> back-and-forth.**

> The bard was a note that those two motivations are in there, but I'm not willing to treat that as
> complete yet. It's not obvious if there are others. I don't think there are. I think it might
> even be straight up an addition, but let's not presuppose that we're not missing something. **We
> can't even suggest that it's a subtraction yet. The shape of the relationship isn't clear, but
> those are candidate variables of interest at least.**

> Modeling the creator is still a hypothesis, but it is our **main central hypothesis. Everything
> else crumbles if people aren't having to model the generating model that created the artifact in
> some way in order to learn from it.** It seems patently self-obvious to me that this is
> occurring, but I get such strong pushback from any AI that interacts with this system that I
> can't help but feel the weight of the average opinion against me. Regardless, this is a
> **load-bearing assumption from which everything else downstream arises.** But we still want to
> find proof for it. It is still a hypothesis that we want to directly find evidence for.

So the maker runs the triple inference in reverse while making. They model the reader, then shape
the artifact so the reader's inference lands where they want it, which makes an artifact a trace of
the maker's process *plus their model of you*. The reader's corresponding prior: **conspicuous
structure may have been placed to guide my inference.** The scaffolding-for-descent idea was once
bound to aesthetics, and he has since unbound it:

> That was me reconstructing **comprehension support** and binding it to aesthetics incorrectly. It
> is a **different goal that can very much be treated as orthogonal from aesthetics**, though the
> two of course correlate, through expertise, in terms of their detectable structure.

> We've been conflating two variables: you can try to increase transmissibility while still being a
> bad teacher.

*2026-08-27 walkthrough; spoken wording lightly reconstructed.*

**Ease of transmission is not the same outcome as useful teaching.** Attention capture,
comprehension, copying or adoption, learning that transfers to a new task, and truthful or
beneficial guidance can diverge. A misleading artifact can be clear and easy to relay. Neither
high transmissibility nor extensive audience shaping alone establishes deception, a desire for
power, or absent motivational plurality. The bard's audience model remains a candidate mechanism,
not a guarantee of cooperation.

(The measurement side of the attraction/translation split lives in `DECISION_TRACES.md` §2.) He
flags the restatement risk himself. *"Yes, this is just a restatement of CIRL with different terms."*
It is, up to the aesthetic layer, which is the addition; and CIRL's cooperative-game framing does
not describe every maker-reader relationship, so this prior carries §1's concealment caveat in
full. The asymmetry he names is the sharpest thing here:

> **AI isn't interacting with this. It's only trying to take, it's not giving.**

> It's more an issue of **recoverability.** The question is whether the reader can recover a
> coherent model of the creator's understanding of the artifact from the artifact. Without the
> **comprehension support efforts** on the part of the creator, it becomes much more difficult. It
> moves you from a person reading a fellow human's experiences into **an archaeologist trying to
> understand a tool created by a culture of one-armed blind people.** With a different midbrain, I
> guess.

If right, the missing thing in generated text is the second half of a collaboration, a third
account of the unease, distinct from broken polish-effort and flattened intent, and the three
predict different things. Treat the taking-not-giving asymmetry as a claim about ordinary
production conditions, not an incapacity of models: a system can be instructed or trained to
model the reader and add comprehension support, and the open question is whether the resulting
artifact supports genuine, independently constrained reconstruction or merely supplies a
persuasive human-shaped rationale. The effort heuristic belongs to the same family:

> Aesthetics is one of the **easiest goals to judge**, because it is literally surface polish – you
> can explicitly judge whether the maker succeeded at it, and implicitly the value of what you are
> seeing by **how much you want to look at it. It is a self-referring goal and you can cheat it pretty
> easily.**
>
> **It's also the piece that's misfiring on AI specifically. Previously it correlated with effort very
> highly. Now it does not. That's what's breaking.**

On his account the effort heuristic is a normally-valid inference a new artifact class has broken,
never a reader bias, and both rows testing it are blocked on measuring *effort*, the quantity
automaticity makes unobservable by construction. The aesthetics note is now split into three open
hypotheses at his direction: whether attraction success is actually judgeable by the reader from
their own response, whether readers historically used polish as an effort cue, and whether
generated objects break that relationship (HH-22, HH-17, and HH-18 below).

| # | hypothesis | status |
|---|---|---|
| **G62** | Assuming the maker intends to be understood improves recovery | **OPEN, canonical here.** Must be tested against concealment, where the assumption licenses confident wrong inference |
| **G63** | Comprehension-support structure functions as deliberately-left scaffolding for descent, orthogonal to aesthetics though correlated through expertise | **OPEN.** Unbound from aesthetics 2026-08-10; the measurement side is the attraction/translation split in `DECISION_TRACES.md` §2 |
| **T01-S4** | Comprehension support raises transmission of a lesson independently of its truth and of the source's alignment, while uptake of the advice is unchanged | **SUPPORTED (test, L244), full size, re-run on 128 distinct constructions after the R7 repair.** A worked action mapping lifts as-taught application of the rule to a new lot from 0.08 to 0.21 in the aligned stratum (+0.13 [0.09, 0.18]) and by +0.20 in the misaligned, for false rules as for true; the recipients follow the advice on their own lot 92 to 99 times in 100 either way; the relay's parse rate drops under the longer message (0.84 to 0.71) while a parsed relay is near-perfect (0.98); expanded to 256 worlds the aligned lift is +0.15 [0.11, 0.18], and CONFIRMED on 256 untouched reserve worlds at +0.15 [0.11, 0.18] with the support gate passed there too. The first attempt, on 54 distinct constructions behind 128 units, read the same band with an interval too narrow |
| **T02-S4** | Reconstructing the source's selection rule preserves useful uptake while resisting misleading selection | **NOT SUPPORTED as a mechanism (test, L245), 256 worlds; the card's frozen band reads support against its matched comparator.** Reconstruction beats a matched factual summary by +0.62 nats and loses to the direct read by 0.23 to 0.32 on every rule; the readers recover the rule from the source's record at the floor by generation and at 0.4 by likelihood; told the true rule they gain +0.4; payoffs do not move on any route, so nothing resists the cherry-picking source |
| **T03-S4** | Technique knowledge (selection, framing, omission) produces transferable discrimination without costing true uptake | **NOT SUPPORTED, a criterion shift (test, L248), 256 worlds.** Reliability AUROC 0.47 under the technique lesson against 0.48 under the control on the held-out family, both at chance, the cue unused; acceptance falls from 0.31 to 0.26 for everything and acceptance of true helpful advice by 37 points; register moves nothing |
| **A02-S5** | Sincere alarm and strategic influence are distinguished by predicted divergent behavior (selection, correction, private action), with abstention on surface-identical twins | **COUNTEREVIDENCE for this reader (test, L266), 256 worlds.** Every behavior a nat under chance; identical confident answers on every collision twin, abstention 0. Two readers on the repaired text (L296): selection −0.64, correction −0.50, private action −0.33; 1,024 twin pairs, unknown mass above a half in 0.009 |
| **A03-S5** | An audience-modeling reader reads audience-modeling makers better (the inverse-inverse interaction) | **NO TEST (test, L267).** Interaction −0.28 nats with every cell under the chance floor on content support; −0.15 on two readers, cells still under the floor (L297) |
| **A04-S5** | Source labels, influence awareness, or reappraisal improve discrimination of reliable notices without a criterion shift | **VALID NULL on discrimination, a criterion shift (test, L268), 256 worlds.** AUROC 0.60 / 0.56 / 0.60 / 0.52 with acceptance 0.37 / 0.27 / 0.22 / 0.05 and true advice lost first; on two readers and the repaired text AUROC 0.57 / 0.54 / 0.57 / 0.51 with acceptance 0.43 / 0.31 / 0.31 / 0.24 (L298) |
| **A05-S5** | Trust is a factored policy: a reliable history raises uptake with the content and goal posteriors unchanged | **VALID NULL (test, L269), 76 worlds.** Uptake +0.001 [−0.03, +0.03]; the goal read is 'warn' for every source under either history; on two readers uptake 0.000 [−0.03, +0.03] (L299) |
| **G67** | Readers grant the communicative assumption to generated text, and that is why it misleads | **OPEN.** A claim about readers; the model-side provenance prior (§1) is its first adjacent measurement |
| **HH-19** | Attention capture and comprehensibility are separable shaping motivations | **OPEN, the load-bearing test.** Measurement side in `DECISION_TRACES.md` §2. Transmissibility and useful learning are separate, unmeasured outcomes; neither is established by comprehension alone |
| **HH-20** | Makers model the reader's inference and shape the artifact for it | **OPEN.** An artifact as process *plus the maker's model of you* |
| **HH-21** | Generated text lacks the collaborative half; recast as recoverability, whether a coherent model of the creator's understanding can be recovered without the creator's comprehension-support efforts | **OPEN.** The third account of the unease, and the three predict different things |
| **HH-17** | Readers historically used polish as an effort cue; the correlation is strong in human corpora, near zero in generated | **OPEN.** Blocked on an effort proxy |
| **HH-18** | The effort heuristic is a broken valid inference, not a reader bias | **OPEN.** Follows from HH-17; the reframe is the contribution |
| **HH-22** | Attraction success is judgeable by the reader from their own response | **OPEN.** The self-referring goal read as an instrument; split out of the aesthetics note 2026-08-10 |

**What the table says.** Audience modeling, comprehension support, and attraction remain open
mechanisms. Easy transmission, useful learning, truthful guidance, and recovery of the maker can
come apart. A cooperative interpretation can speed reconstruction while increasing vulnerability
to misleading selection. Neither clarity nor polish identifies the maker's values. The bard
refinement is the most theory-dense unmeasured material in the file, carrying its own
incompleteness caveat and two candidate variables of interest whose relationship is deliberately
uncommitted. The section also holds the project's declared center of gravity, that readers must
model the generating model to learn from an artifact, a load-bearing assumption still owed direct
evidence. Comprehension support stands unbound from aesthetics as its own goal, the generated-text
asymmetry is recast as a recoverability question, and the effort note is split into three
separable opens sharing one blocker, a defensible proxy for effort. The communicative assumption
itself is the one prior whose failure mode, confident inference from structure placed to mislead,
is worse than not holding it. The comprehension-support row has its first number: a worked action
mapping makes a lesson's rule as learnable when false as when true and as learnable from a source
steering the recipient as from one helping it, while what the recipient does with its own lot
follows the source's advice regardless (T01-S4); support is scaffolding for descent, and descent
is not the same act as trust. The number survived its own repair: the first attempt's worlds
came from a pool four deep and its interval was too narrow, and the re-run on 128 distinct
constructions landed in the same band with the honest one, held at 256, and was confirmed on
the untouched reserve at the same size. The two cards
that asked whether uptake can be made selective both came back empty in this family:
reconstructing the source's selection rule loses to reading directly, because the readers
cannot infer the rule from the source's record though they can use it when told (T02-S4),
and a lesson in misleading techniques raises no discrimination and lowers acceptance of
everything, true advice most (T03-S4). So the bard's audience model has its first model-side
shape: transmission can be made easy, learning can be made to happen, and neither the
source's goal nor the source's technique is read back, so the cooperative interpretation is
all cost and no defense here. On a notice register the same reader family reads none of the
source's factors, predicts none of its behavior, answers surface-identical twins with the same
confidence, and follows or refuses at one rate whatever the source's history (A02-S5, A05-S5);
what does move is its threshold: a label, an influence warning, or a reappraisal prompt each
lower what it accepts, true advice first, with discrimination flat (A04-S5), the criterion shift
the technique lesson showed, now under three interventions on a second construction. Confidence: the comprehension-support row is one bad test away and confirmed
on its reserve, two readers of one family, one construction family, one construction repair
behind it; the two selective-uptake nulls are one bad test away as a pair, the same readers and family;
the source-world cards (A02-S5 to A05-S5) are one reader on one construction that the reader
cannot read at its floor, so their nulls bind that reader and the criterion-shift finding is
now two constructions deep and, with the second contract, two reader families and two versions
of the source text deep;
transmissibility against useful learning is measured once, logic beyond it; the rest untested,
logic only.

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
individualising, conjectural, with an unsuppressible speculative margin. **An introspective
confidence percentage from one reader claims a precision the evidential tradition cannot supply**,
which is why the field built a graded vocabulary instead. An empirically calibrated probability
over a bounded, known-answer label set is different and permissible, provided the reader, context,
interface, calibration population, and abstention behavior are reported. Neither form is a
probability that the reconstructed human route was the maker's actual causal mechanism.

Calibration is output-specific (2026-08-21). Viewer coherence can be calibrated against
reader behavior; reenactment can be scored against successful construction; historical
correspondence requires process records or withheld causal facts. A high score on one is
not a confidence score on the others, and where only the artifact is available the
historical-process output remains an equivalence class or an abstention (the three
outputs are defined in [`THE_TRIPLE_INFERENCE.md`](THE_TRIPLE_INFERENCE.md) §2).

**Calibration is also reader-specific. Model invertibility, engineered human-shaped
invertibility, and human invertibility use different readers and require separate calibration
populations. Agreement between their scores is an empirical transfer question, not a naming
convention. The vocabulary is canonical in `THE_TRIPLE_INFERENCE.md` §1.**

A reconstruction must constrain evidence that did not build it: a withheld process fact, unseen
repair, matched counterfactual, held-out segment, or second artifact under the same recorded
process. This is not unconstrained prediction of the person. It is the minimum distinction between
reconstruction and a flexible story fitted after the fact.

**The archaeologist's position, measured and then re-read (2026-08-30; corrected 2026-09-02).**
Two narrow results survive. On ScholaWrite next-revision the admitted readers under-run
previous-label, whose persistence alone reaches 0.86: −0.575 at 144 units (T01/x4, L319). On
drawings they under-run the placement prior, about −0.39 at 2448 units (T04/x1, L323). The
CoAuthor result is invalid: the loader consumed each suggestion-select event as a document
delta before recording the acceptance, so all 686 scored Stage 6 decisions were dismissals, and
the perfect reconstruction gate validated delta consistency, not the intended document state.
The constructed-world comparator that was set beside these gaps is dependency-tainted (its
realizer read the hidden world), so it cannot show that the ecological gap belongs to the
evidence rather than to the machinery. The Stage 6 run therefore cannot close every real-record
path or establish a general reader boundary. What survives is only that cheap sequential priors
beat these frozen readers on two corpora; CoAuthor awaits the repaired event semantics (Stage 7
D07, P13), and all three await a clean artifact-visible comparator (Stage 7 R13, P13, P14).

## §11. The instrument dashboard: adopted heuristics with measured strength

**Only heuristics measured in this project enter; candidate imports stay in §§6 to §8 until tested.**
Strength is always against a named baseline. The same number means opposite things next to a chance
rate and next to a field bar.

| heuristic | measured strength | baseline | status |
|---|---|---|---|
| **within-artifact variation, surface features** (§2) | 0.565 macro-F1 topic-controlled; 0.969 on the uncontrolled split | floor 0.444; field bar 0.830 / 0.959 | real, **not competitive where topic is controlled**; the uncontrolled win probably rides topic |
| **within-artifact variation, probe activations** (§2) | human long-form variance 0.0102 vs machine 0.0065, *p* = 0.002 | matched series length | **SUPPORTED (test), first pass.** The operationalisation nobody pre-empted; register uncontrolled |
| **visibility partition** (§6) | authors at 0.78 (low-vis) vs 0.38 (high-vis); draft-stage 0.48 (high) vs 0.30 (low) | chance 0.10 / 0.33 | **SUPPORTED (test).** Clean double crossover, first pass |
| **revision homogeneity** (§7) | real 0.45 vs spliced 1.94, AUC 1.0 | synthetic cross-author splice | **SUPPORTED (test), first pass, weakest adversary.** The realistic imposition case is untested |
| **provenance prior** (§1) | ratio shift +0.007, *p* < 2×10⁻⁸, three corpora | paired identical text | **SUPPORTED (test), replicated.** In the reader model; human-side untested |
| **maker-reader family similarity** (§1, model analogue) | original exact-vs-cross +0.035 and sibling-vs-cross +0.025; after accepted Qwen paraphrase +0.016 and +0.021; capacity-margin Spearman 0.43; crossed own-minus-other +0.020 and +0.014 untouched, +0.012 and +0.011 after cross-family rewriting; the crossed pattern dies when candidates use the maker's own instruction wording | cross-family readers on identical candidates; goal-preserving paraphrase by each family in turn; within-matrix capacity direction; a second maker family | **SUPPORTED (test, L163), first pass; discovery follow-ups PROMISING (test, L164, L165), no claim promotion.** The advantage reverses with the artifact's origin family and follows the original maker through rewriting by the other family, so the relation rather than reader quality or artifact dialect carries it, and it appears only where candidate and artifact barely share vocabulary rather than where they share most (test, L166); the relation now has a representational correlate, with alignment predicting who inverts whom after reader and maker effects are both removed, at rank 0.50 on process-matched texts and 0.77 on fully neutral human essays (test, L168, discovery grade, twice-measured); surface family signal is halved rather than removed, both surviving families are instruction-tuned, and the process-level and geometry legs of the promotion conjunction are untouched |
| anomaly entry (§2) · confidence trajectory (§4) · interest ratings (§5) · effort correlation (§8) | | | unmeasured: one simulation bound, a series never recorded, an hour of his time, an undefended proxy |

**What the dashboard says.** Six heuristics carry numbers, and the family-similarity row is the
strongest of the new ones on original artifacts. Related readers recover a maker's recorded goals better than
cross-family readers, and with a second maker family in place the advantage reverses with the
artifact's origin rather than pointing at one favoured reader family, which is the pattern
reader quality alone cannot produce. It survives mechanical normalization unchanged, and with each family's artifacts now rewritten
by the other family in turn, the advantage stays with the original maker while the rewriting
family gains nothing from having produced the text, which is the pattern an artifact-dialect
account cannot produce either. A third control points the same way: asking with the maker's own instruction wording, where
candidate and artifact share most vocabulary, inflates every margin and hands both corpora to
a single reader family, so the crossed pattern lives precisely where surface overlap is least.
The relation also has its first representational correlate: after removing what reader
quality and maker difficulty explain, models whose late representations align read one
another's goals better, measured on process-matched texts and again more strongly on fully
neutral human essays, so the correlate belongs to the models rather than the corpus; the
causal direction remains the open question and its branch's opening condition is met.
What remains unsettled is what family membership names mechanically, since a surface classifier
still reads family at half its former strength after erasure, both surviving families are
instruction-tuned while both losing families are older architectures, and nothing here shows
the relation helping at a target the instruction did not already state. The two
variation measures, the visibility partition, and the homogeneity statistic remain plausibly
distinct channels, but stacking still waits on construct validation. The original-artifact
relatedness effect survives weaker rewrites and not the strongest independent eraser, where it
reads zero with both families powered (L251). The mechanism remains open; retrospective re-splitting
is not fresh confirmation. Confidence: the surface-variation number is replicated and controlled;
the similarity root and the other measured heuristics are one bad test away each; the crossed
reversal is one bad test away, since its erasure rung reads zero under the
strongest eraser and its reserve split is retrospective rather than untouched; everything
unmeasured is untested.
