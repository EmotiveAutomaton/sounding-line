# Reader heuristics: how a bounded reader approximates the triple inference

> While I don't expect we will have to rely on these heuristics when designing depth extraction, I
> expect AI will arrive at most, if not all of them, organically. Nevertheless it's worth keeping track
> of the ones we have run into that would be relevant as potential **feature-extracting amplifiers** in
> future, that other research teams may have missed.

**A bounded reader approximates the triple inference using priors about the maker, local cues in the
artifact, strategies for moving between explanatory levels, and calibration rules that limit
overinterpretation.** The proposed human account uses successive, fallible approximations; neither convergence
nor improvement on every pass is guaranteed. The curator's own readings (fifteen artifacts, two sessions) are
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
here.**)** Then **biography and prior artifacts**, which supply observations about the maker and
context rather than automatically trustworthy context facts (*"Everything's an artifact.
Even information about their life"*, canonical in the triple inference, operational here); **provenance framing**; and the **communicative assumption**,
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

**Invertibility belongs to the pair** *(2026-10-13)*:

> Non-invertibility is a property of the pair. That's the trick. It's a question of model families.
> If you have enough power, or you are a larger model, you can invert a smaller model. Or if you're
> similar enough, you get a bootstrap. You can reverse engineer your own actions more easily, I'm
> pretty sure, and there are biases in humans that I want to acknowledge complicate that, but it is
> doable, and that is one of the things artists use to understand themselves. But inverting someone
> who is too different from you gets difficult, and inverting something wholly alien, like AI to
> human, crossing that gap is also a problem.

> [...] If you're similar enough to be able to recreate, then you're more willing to uptake small
> edits. Maybe that's why we get the model family effect with humans. Like, political alignment and
> so on would be the equivalent of that, I guess.

> The first one's easy. For whose residue, the Tolkien scholar and the reader both have their own
> predictions, but the confidence is different. The Tolkien scholar is able to successfully make more
> predictions correctly, and thus has confidence that they are speaking the same language of
> expertise. [...] The same thing can be done by the casual reader, yet that doesn't actually allow
> them access to as accurate a mental model. They still try to form one, obviously, but the key is
> that their own evidence will illustrate the confidence they should have on the author's model,
> because they're unable to predict the process, and therefore they just get a lot of noise on their
> maker model.

> You can never skip inference. Similarity makes the inference easier.

*Curator's ToMpathy assessment walkthroughs, 2026-10-13 (10:17 and 14:01 PDT), in the project's assessment thread; filed 2026-10-14. Separate excerpts with marked omissions; transcription repairs listed in the handoff.*

The self case is the sharpest test of the pair claim. The separate record task found no self
advantage, while relatedness predicted reading of original model artifacts (HH-23 and G172 below);
the reader's confidence, set by how much of the process it can predict, is the proposed bound on
how much maker it may claim.

> You know, self, I'm trying to recreate the act of an author making a painting, stepping back and
> looking at it, and using that to learn about themselves. Or reading an email you wrote that's
> several pages long and using that to learn about yourself. It can happen on a small scale. But
> it's, yeah, you're getting access to your own automatic expertise through observing your
> behavior. I'm not sure quite how to simulate that, but that's what we're trying to capture there,
> I would hope.

*Curator's walkthrough of this handoff's decisions and questions, 2026-10-14 (12:22 PDT), in the project's errata thread; filed 2026-10-14. Contiguous excerpt; transcription repairs listed in the handoff.*

Self-reading in this sense is self-perception, a maker inferring their own dispositions from their
own artifacts as an observer would (Bem, 1972, snippet). Models show a related ability, describing
tendencies they were fine-tuned into, such as writing insecure code, without examples in context
([Betley et al., 2025](https://arxiv.org/abs/2501.11120), abstract read). The self target in the
record task ran the reader's own weights under an imposed policy, which tests neither form; the
faithful test has a model read its own unprompted artifacts. A constructed test of the split
between process and preference ran as card C2 of the Ghost V22 first pass (13 October); its result
is not yet read into this file.

**Readers converge with context, and the reader's habit is the reference** *(2026-10-16)*:

> The AI reader would predict its own habits, and that'd be useful information. [...] That's why you
> seek context, to ensure that you do have, you're putting yourself to the test properly. That you
> aren't giving yourself, like, of course you can recreate the Mona Lisa [...] with Photoshop, but
> like, can't you do it the way that he did it? Otherwise you didn't actually do it. [...] Of course
> it produces its own habits, that's the easy thing, but you need context to produce the writer's,
> and you can extract context from the document for the page, but also kind of from your own
> history, which is largely what your readers are missing, I suspect. Kind of built-in base level
> context understanding. I don't know, maybe not.

> Readings shouldn't just depend on the reader. They do. They're changed by the reader. Certainly
> different models should have different reading outputs just because that's how noise works. But
> practically speaking, the goal is to fully align with context and thus have removed the difference
> between the two, context being the only real difference in terms of solution, unless you can find
> a truly alternative solution that also gets you there 100% of the way, which is not really a thing
> that happens in physical space.

*Curator's walkthroughs of the analyst's 16 October record and handoff questions, 2026-10-16 (12:57 and 14:17 PDT), in the project's theory and analyst thread; filed 2026-10-16. Separate excerpts with marked omissions; transcription repairs listed in the handoff.*

The line the curator answered reported that a model reader asked to forecast writers' choices
forecast its own habits. He reads that as useful information, and the analyst's gloss is that the
reader's habit is the reference rather than the error. Attention is a departure from the reader's
own expected process, so the error was using the reference as the forecast, and the public CoAuthor
release already holds the reference, since it logs the model's own probability for every suggestion
it offered. Context is how a reader moves from its own habit to the writer's, and getting context
beats imagining it. Across 25 experiments, imagining another person's perspective gave no consistent
gain in accuracy and sometimes raised confidence, while getting the perspective by asking raised
accuracy
([Eyal, Steffel & Epley, 2018](https://cris.iucc.ac.il/en/publications/perspective-mistaking-accurately-understanding-the-mind-of-anothe/),
abstract read).

For Bayesian readers the convergence the curator describes is a theorem with a condition. When two
readers' priors allow the same possibilities, their predictions of what comes next merge as shared
evidence grows, and one reader's predictions merge with the other's when its prior rules out nothing
the other allows ([Blackwell & Dubins, 1962](https://doi.org/10.1214/aoms/1177704456), through a
summary read); with a common prior and common knowledge of each other's views, two readers cannot
agree to disagree ([Aumann, 1976](https://doi.org/10.1214/aos/1176343654), read). If one reader
gives zero weight to what the other allows, shared context is not guaranteed to close the gap.
Disagreement beyond noise that persists as shared evidence grows therefore marks a support gap, a
move one reader cannot represent, or rarely the truly alternative solution the curator allows for. A
position paper argues that representations in different models converge as models grow
([Huh et al., 2024](https://arxiv.org/abs/2405.07987), read). The dissent is that larger models'
surprisal fits human reading times worse
([Oh & Schuler, 2023](https://aclanthology.org/2023.tacl-1.20/), read), so readers converging with
each other can drift from human readers, and a reader built to model people has to model a human
reader rather than an ideal one.

**(HH-READER-CONVERGENCE:** Readers differ through noise and missing context, and shared context
removes the difference unless one reader cannot represent the move or a truly alternative solution
exists; a reader's own habit is the reference against which a maker's departures are read, not a
forecast of the maker. **OPEN.** The convergence claim is the curator's and the reading of habit as
the reference is the analyst's. A theorem for Bayesian readers whose priors allow the same
possibilities (lit, READ and through a summary read); larger models fit human reading times worse
(lit, READ); no project measurement of convergence with context.)**

**Proposed self-based initialization.** Shared organization may supply a cheap candidate
generator that the reader can adjust toward the maker using artifact evidence and context.
Relevant similarity is expected to make this shortcut more useful; the route is neither
established as universal nor guaranteed to reconstruct the maker's history. It supplies
candidate routes and effort estimates, then is adjusted using evidence about the maker. It also
creates a characteristic failure: a sufficiently flexible reader can explain almost anything as
something the reader might have done. Reader identity, domain competence, and conditioning must
therefore be recorded as part of the instrument.

> You are running your forward predictive model and checking for what would be different, and
> through that you are adjusting your own expertise map. You are becoming them, but only in this
> space and in adjacent spaces. Empathy at its limit is pretty indistinguishable from impersonation,
> but only at its limit, and only for the topic at hand. There is a lot of control in which areas you
> are attending to and how rapidly you are moving through them.

*2026-09-04 walkthrough; lightly cleaned transcript.*

The initialization is the reader's own forward model of the domain's process, and the correction is
local adjustment at the differences; becoming the maker is bounded to the topic at hand, and the
reader keeps control of where it attends and how fast it moves.

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

> I don't know whether this kind of predictive inference is done all the time, just kind of
> looser and with wider error bars that catch more notable events, or whether it is something
> that is cycled in as a second channel. My gut deeply thinks that it's the first one. That it
> is a single system and not two.

*Curator’s latest editing and appreciation walkthrough in this analysis thread; source date not separately supplied; handoff prepared 2026-09-12; applied to theory 2026-09-13. Wording preserved.*

The curator's current bet is that appreciation is already operating in ordinary perception,
with attention changing its precision and the parts of the maker model pursued. This
preserves the self-based generative account without requiring every goal, belief, or
history variable to be explicitly represented at every moment. A common objective and
common machinery are different claims: changing precision, changing which variables are
represented, and switching strategies remain distinguishable possibilities. This extends
the open human account in HH-23; the model-reader evidence does not settle its architecture.

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
division. The walkthrough after Stage 7 fixes what the initialization is: the reader's own forward
model of the standard process, corrected locally where the artifact differs from it, so shared expertise is one candidate source of useful initialization. Individual
familiarity can also supply a prior; no fixed priority between the two is established.)**

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
vs the 0.33 symmetric null) while the record-reading reader errs symmetrically (0.29), consistent with projection corrected by evidence use in one reader and not the other.
Those outcomes do not isolate an assumed-similarity initialization or its internal
correction mechanism. Active search is not the correction's source: offered a higher- or lower-information
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

> It is generally true that identifying the goal is one of the easiest vertices to solve. You start
> with what you could use this to do if you were in their context, and expand from there. It relies a
> great deal on shared humanity. If you are not finding it to be the easiest, the inference is not
> being worked properly.

*2026-09-04 walkthrough; lightly cleaned transcript.*

The affordance route is the curator's proposed starting point: ask what the artifact
could be used to do in the maker's context, then expand the candidate purposes. His
expectation that goal is usually easiest guides pursuit. Difficulty alone does not
establish a defective inference, since different purposes can remain compatible with the
same artifact. Whether the target is identifiable and whether the reader can recover it
are separate questions.

> It would feel kind of instinctive, like a reflexive guess that you just are unusually
> confident about, you don't know why.
>
> As far as what would draw you into a deeper reading, the feeling itself would be an
> explanation that would demand an assessment.

*Curator's preceding director-familiarity walkthrough; filed 2026-09-07. Wording preserved.*

**Familiar recognition can invite reconstruction.** Several small, familiar choices may
prompt a rapid maker hypothesis before the reader can say which choices support it. The
felt recognition can itself invite assessment. This is the curator's description of an
experience, not evidence that its confidence is calibrated or that a particular cognitive
architecture produced it. Shared convention, imitation, source framing, and mistaken
association remain alternatives to correct identification. Identifying a maker, predicting
that maker under a new constraint, and reconstructing a historical process are different
achievements. An anomaly is therefore one entry route; familiarity is another candidate.

> The ones I previously thought were good were the ones that were best at appearing good rather
> than actually being so, which doesn't look as flashy.

> Knowing that there's true knowledge there makes staring at it more interesting.

*Curator's jiu-jitsu example in the local-goal, evidence-reorganization and expertise walkthrough,
supplied in the analysis thread; recording date not separately supplied; filed 2026-09-21.
Separate excerpts. The first restores the omitted subject I after "The ones"; all other wording
is preserved, with line wrapping and punctuation normalized.*

Added expertise can change which alternatives, constraints and consequences a reader sees,
turning an apparent error into a purposeful choice or apparent skill into presentation skill.
The operative goal still matters: convincing choreography and effective fighting can reward
different moves. Recognition of genuine competence may invite closer attention without
establishing the maker's history or values. Production competence, observational familiarity,
shared tools and prior knowledge are live explanations for the reader's advantage, not synonyms.
Confidence: untested, logic only for this proposed reader mechanism.

A mistake is a sharpened anomaly for which evidence supports a mismatch between a choice and the
maker's operative trajectory. The strongest evidence often comes from handling: repair exposes a
preferred counterfactual, concealment exposes recognition and a protected goal, repetition
suggests habit or a stable transition-map limitation, and non-response suggests either
non-recognition or indifference. Unfamiliar order remains unresolved until evidence distinguishes
expertise, convention, secondary purpose, accident, and error (the trace classes are canonical in
[`DECISION_TRACES.md`](DECISION_TRACES.md) §3).

> And I think in this case, criticality is when you believe you have the artist's proximal
> goal and you run your forward generator. If you come up with a better meeting of that
> goal than the creator did, that's where critics come from.

*Curator's preceding painter/restorer walkthrough; filed 2026-09-07. Wording preserved;
the missing sentence break after generator is repaired.*

**Criticism can compare possible means to an inferred end.** On this account a critic
can propose a different choice and assess whether it better serves the maker's inferred
purpose. The purpose estimate, available alternatives, cost, and consequences of the
proposed improvement can each be wrong. A local repair may demonstrate useful competence
without establishing the ability to create the whole work or reconstruct its history.
The curator's later description of nothing being surprising names a felt limit of fluent
understanding. Retrospective explanations for every detail do not independently establish
that the reader's forward model is accurate. A reconstruction earns evidence when it
constrains a withheld choice, repair, or continuation rather than accommodating any outcome.

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

Stage 7's constructed histories supply a scoped process result (L351): a program
localizes a one-time change of control from the event record and survives the tested
surface matching, but also produces false changes under a pure style shift. No tested
program localizes the change from the final artifact. The direct change-point comparison
uses the defective 20-option grouping and cannot establish a general reader limitation
(OPS-ERRATA-2). Whether a discontinuity reflects a change of goal remains a separate
question; failure of these readers does not prove the artifact lacks usable evidence.

**And the revision-wobble test is retired on his own account.** Human redrafting was the wrong
axis, before the null even needed explaining:

**Superseded:** the earlier account treated human revisions as carrying an invariant
level of intent density. The curator's correction below withdraws that generalization;
the particular revision-wobble instrument remains retired.

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
| **HH-3** | Within-artifact variance of *probe activations* carries a general human-provenance signal | **REJECTED as provenance; model/register sensitivity remains (test, L39, L101, L105).** The uncontrolled initial comparison is superseded; the trajectory dissociates from the artifact-side sign across families |
| **HH-4** | Redrafting is the wrong axis; the claim needs artifacts of different kinds by one maker | **OPEN**, and his intent-density quote above says why in advance |
| **HH-6** | Entering at the anomaly beats entering at the whole artifact | **OPEN.** The machinery exists (`bounded_v6` stage zero); a flag flip and a comparison |
| **HH-7** | Local decision density around a mistake exceeds baseline | **OPEN.** Needs mistakes located first; the one place a decision and its counterfactual are visible together |
| **HH-CRITIC** | A locally enacted alternative can improve on a maker's choice relative to an inferred purpose, and that competence can inform reconstruction | **OPEN.** Curator walkthrough and analyst formulation; requires independently assessed purpose, constraints, and consequences. Existing explicit-route results do not validate human constructive criticism |
| **HH-FAMILIARITY** | Felt recognition from several familiar choices can initiate a maker hypothesis and a subsequent assessment | **OPEN.** Curator report; the accuracy, calibration, and predictive usefulness of this route have not been measured on human artifact readers |
| **S-4/S-5** | Stage ordering changes the answer | **REJECTED (sim)** by exactly zero; ~5% cost saving only |
| **G165** | Explicit route generation (a self-enacted production route, or predicted evidence per candidate) improves recovery of recorded executed choices over direct reading | **NO-GAIN where direct reading is strong (test, L151); HURTS where it is weak (test, L153), and the wing is CLOSED.** On the realized-choice events: zero delta and minus two points, every gate quiet. On the revision-delta events where the change block beats the direct reader: self-route costs seven points (p = 0.0006) and invents purposes on unrevised text at 0.065 against the direct reader's recorded 0.000, while evidence-prediction gains three points, noise-compatible. Explicit generation is rhetoric the reader then follows over the evidence |
|   | | *(this row's history is a NO-GAIN root on the strong substrate 08-21 morning and the HURTS discriminator on the weak substrate the same afternoon; the null-discriminator rule is spent)* |
| **E02-S3** | A reader given a maker's choice RECORD predicts their next choice better than one given nothing or matched filler, on known-policy targets | **SUPPORTED (test), one reader deep.** +20 points paired (p = 0.0026) against an exact ceiling of 1.00, but the entire margin is Qwen's (0.57 vs 0.23); SmolLM-1.7B reads the record at filler level (0.27). The self-first two-step neither helps nor hurts. Instrument gate for the Stage-3 route factorial |

**What the table says.** Probe trajectories reflect model and register sensitivity whose
mechanism is unresolved; they do not establish general human provenance (HH-3). Surface
variation fails its controlled bar. Explicit route generation adds no gain where direct
reading is strong and damages it where weak, with a fabrication cost; this bounds that
strategy in the tested readers and does not test the implicit human mechanism (G165).
Records help the reader able to consume them (E02-S3). Anomalies, familiar recognition,
and locally constructive criticism remain distinct candidate routes into reconstruction.
Neither felt certainty nor a plausible improvement establishes historical correspondence.
Stage 8 supplies diagnostic measurements on readers that were not admitted; it does not
validate these human routes. Confidence: instrument-dead for the probe's provenance
interpretation; replicated and controlled for the scoped surface defeats; one bad test
away for explicit-route and record-reading results; untested, logic only for the new
criticism and familiarity hypotheses.

**Shared expertise and reading from the middle**

> empathy does require shared expertise

> as soon as you have some understanding of the other person's base rate, you can start to look for variations in that base rate to identify preference

> you can still reverse engineer from the middle [...] difficult and rare

> we [have] a lot more shared expertise with any AI model than you would with a human

*Curator walkthrough, 2026-10-18, about 09:15 PDT, answering the twelve analyst questions; filed at the October 18 daily integration. Excerpts and marked lexical repairs are preserved from the [filing source](../design/archive/SOUNDING_LINE_THEORY_FILING_2026-10-18.md).*

The curator treats shared expertise as necessary for empathy and a known baseline as the starting point for personal variation. The supplied literature proposes an amplifier rather than proving that necessity. Reading a production sequence from an artifact is a separate possible entry; it does not establish the maker's purpose.

**Literature vocabulary, analyst handoff.** The following explanations retain the supplied analyst attribution. Linked sources were requested; inaccessible papers and uninspected full texts are **SNIPPET**, not independently verified findings in this pass.
- **Normative accuracy**: means judging the typical person correctly, distinct from individual departures ([source](https://doi.org/10.1037/h0044919), SNIPPET).
- **Distinctive accuracy**: means recovering what distinguishes this person from the typical profile ([source](https://doi.org/10.1080/00273171.2010.519262), SNIPPET).
- **Perception-action model**: links perception of another's state to the observer's own representations ([source](https://doi.org/10.1017/S0140525X02000018), SNIPPET).
- **In-group advantage**: names better emotion recognition within a shared cultural group ([source](https://doi.org/10.1037/0033-2909.128.2.203), SNIPPET).
- **Motor expertise**: can contribute anticipatory information beyond watching experience ([source](https://doi.org/10.1038/nn.2182), SNIPPET).
- **Production-trace compatibility**: asks whether visible stroke directions interact with the observer's movements ([source](https://doi.org/10.1016/j.cognition.2012.06.012), SNIPPET).
- **Kinematic self-recognition**: uses movement timing to recognize one's own actions ([source](https://doi.org/10.1037/0096-1523.27.2.456), SNIPPET).
The supplied archaeological term *chaîne opératoire* names a reconstructed production sequence; it is an analyst analogy here, not a validated reader.

The table separates the proposed claim from its evidence and scope.

| # | Hypothesis | Status and evidence |
|---|---|---|
| **G213** | A reader needs shared coordinates to detect a maker's taste | **OPEN; current existence instrument INSTRUMENT DEAD (test, S15-DRIVE-V4C-DIAGNOSTICS-1018; S15-DRIVE-V4C-SPLIT-1018).** Constructed worlds and exact fitted readers: the descriptive own-coordinate predictive contrast does not repair failed false-alarm calibration. The split history-only reader sees large taste only, not the required medium-strength route. |
| **G214** | A reader can enter the inference through a production sequence visible in the artifact | **OPEN.** Curator account; shared-expertise and static-trace analogies do not establish the complete human-artifact inference. |

**What the table says.** Recognizing a baseline and recognizing a person's departures are different tasks. Shared experience can be useful without being demonstrated as universally necessary; the current fitted taste test cannot decide that stronger claim. Confidence: instrument-dead for the current existence test; untested, logic only for the shared-coordinate and middle-entry claims.

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

**Walking the goal hierarchy** *(2026-10-13)*:

> [...] What effectively you've got is that pyramid of hierarchical goals, and you start walking up
> and just basically labeling as many of them as you can, one by one, with as much, like, weighted
> confidence in all of them, and each one, as you point one, it makes the confidence in another
> increase. It's like a constant inference puzzle where you're just jostling the numbers until you
> arrive at something that makes all of them make complete total sense together. [...] You're always
> kind of working out the top goal, because it speaks to all of the other nodes.

> [...] Expertise lets you fill out 50 to 60% of the steps, and with that top goal in addition, now
> you have a much easier inference. [...] I know the three paragraph format. This is paragraph one,
> two, three. I don't even think about it. [...] The one at the very top does give a lot of
> explanatory power to all of the subgoals, and so it's still the most valuable. But it's not always
> the strongest piece that helps you with a given part of an inference. I think the strongest piece
> might actually be what's closest, but again, top is most generally useful because of that property.

*Curator's ToMpathy assessment walkthrough, 2026-10-13 (16:29 PDT), in the project's assessment thread; filed 2026-10-14. Separate excerpts with marked omissions; transcription repairs listed in the handoff.*

Reading the purpose level is joint settling over a hierarchy, not a walk in one direction. Every
labeled node raises or lowers confidence in its neighbors, the top goal constrains all of them
weakly, and the nearest levels constrain each other most. On a tree the second point is a property
of the structure, since information from a distant node reaches a given node only through the nodes
between them. Kintsch's construction-integration model of comprehension is the classic settling
account ([Kintsch, 1988](https://doi.org/10.1037/0033-295X.95.2.163), snippet). Depth is not capped;
error grows with distance from what the reader's expertise covers. The top goal in these quotations
is the goal that explains the artifact, in the sense of
[`THE_TRIPLE_INFERENCE.md`](THE_TRIPLE_INFERENCE.md) §1, not survival or reproduction.

**Ways into the hierarchy** *(2026-10-14)*:

> Strictly speaking, if you are an expert, then that means you can fill out blocks of the pyramid,
> the pyramid of inference. You can see, like, four of the blocks on the bottom and then the one
> block above that binds them all together as the hierarchical structure, and you just instantly
> fill that in. And that's the power of expertise, is filling in blocks to explain the other
> decisions, because you've made similar decisions. That being said, the most generally useful goal
> is the highest goal that explains all of the local decisions in this case. Once you do that, you
> can take that highest goal and try to throw it up higher, like maybe it's part of a subordinate
> goal of an attempt towards survival or whatever else, if you choose to do so. There's generally
> not a reason to, because what you're actually trying to do is [read] the set of decisions so that
> you could copy the ones that are particularly effective, that you judge to be particularly
> effective. Experts will be particularly interested in things like whether they can capture
> someone else's epistemic foraging and the outcomes of that foraging so that they don't have to do
> it themselves.

> [...] You could also do it top down and assume that whatever the outcome is, is what the
> intended outcome was. Like, you could look at a tool, say this tool would be good for cutting
> things, and assume that the creator wanted to make a cutting tool. You can also do that
> internally. You can feel sadness at an author's words and assume that the author wanted you to
> feel sadness, even if you don't know how to do that yourself, or the technique thereof. But then
> you can try to find the techniques once you have that high level goal. It's one of the ways in,
> bottom up or top down. And it's not really bottom up. It's more like filling out pieces of other
> parts of the graph to help reduce the difficulty of the entire inference.

> It would be the first goal where the artifact's decisions all meet. That's the one that would
> allow you to kind of come in from the top, asking function questions. [...] It's also kind of
> easy to get to, because you can come out from a functional perspective. That functional
> perspective, to an extent, is derived from an understanding that, again, mid-brain-wise, we all
> have the same, we're all trying to serve the same needs, to an extent, at least. I think the
> trick is that you're using your midbrain again to work out possible functions. Like, you're
> assuming they have a belonging need, for example, and then you're putting this into that same
> structure.

*Curator's walkthrough of this handoff's decisions and questions, 2026-10-14 (12:22 PDT), in the project's errata thread; filed 2026-10-14. Separate excerpts with marked omissions; transcription repairs listed in the handoff.*

Expertise fills blocks of the hierarchy from similar past decisions, and the reader's purpose sets
how high to climb. The goal that explains every recorded decision is usually enough, because a
reader often wants to copy the decisions that worked, including the results of someone else's
foraging. Copying wins for that reason in tournaments of learning strategies, because
demonstrators tend to show the best behavior they have and so filter information for the copier
([Rendell et al., 2010](https://research-portal.st-andrews.ac.uk/en/publications/why-copy-others-insights-from-the-social-learning-strategies-tour/),
abstract read). The explaining goal can also be entered from above, by asking what the artifact is
for and drawing candidate purposes from the needs reader and maker share. Function-first reading is
old and fallible. Children explain even pointed rocks by purpose
([Kelemen, 1999](https://www.bu.edu/cdl/files/2013/08/1999_Kelemen_PointyRocks.pdf), read), and
literary criticism named the move from a felt effect to an intended one the affective fallacy, "a
confusion between the poem and its results" (Wimsatt & Beardsley, 1949, through a summary read).
The top-down entry therefore needs the check the curator describes, finding the techniques once
the goal is posited.

**Three entries, and what sacrifice shows** *(2026-10-16)*:

> I think the trick is [...] that humans have a starting point and we can often fill in any part of
> the pyramid with our expertise piece of our own midbrain, which is itself just like I said an
> expertise. Whereas, and what's more, we can also try to climb above the pyramid a bit because with
> enough understanding of context and what their likely interests were in their immediate vicinity,
> I can assume they want things like food, and that they had satiation needs, and that they had
> belonging needs, and that they had whatever the fuck, because we all speak those same language.
> And so if I want, I can kind of try to step above the pyramid and try to see whether there's any
> obvious dependencies that would be explained by this act of behavior. And so I can even try to
> come into the top of the pyramid from above by stapling a few things above it. That seems like the
> second entry point that humans often will use. There, so we have three entry points that human
> will use, but it's really just the same one applied three different times.

> We have expertise applied at the bottom because it's easy to identify specific actions and you can
> use cortical reference frames to find one or two and build out from there. Mirror neurons help
> with that. You can use top down goal directed also again, part of larger goals and kind of
> scattered about you'll find expertise and emotions and values filling in parts of that particular
> graph again, kind of copy pasted throughout. They are complex rule sets that can be applied to
> solve specific problems. Or, they also can enter through the middle, just through identifying any
> particular part of the [...]. Say I can identify the metaphor that you're going for, and that
> metaphor has something to do with lust or something, I don't know. Like, going through the middle
> is also possible, because you can slap that block of solutions across the middle of the pyramid
> too.

*Curator's walkthrough of the analyst's 16 October theory pass, 2026-10-16 (11:56 PDT), in the project's theory and analyst thread; filed 2026-10-16. Separate excerpts with marked omissions; transcription repairs listed in the handoff.*

> I mean, you could do both. Like, the problem with number two is that it could easily do both. You
> could easily say that they're trying to satisfy a belonging need, and they're using that through
> taking lust-like actions. Like, in fact, I would argue most of the time, lust gets nested under
> belonging needs. Although sometimes you could flip them and that results in a different class of
> actions. What is the class of actions that makes that different? It's the difference between going
> on a date with someone to get laid and sleeping with someone for the hopes of a relationship.
> Like, it's literally just which goal is on top. That's it. What are you willing to sacrifice for
> the one above it, if anything?

*Curator's walkthrough of the analyst's 16 October theory record, 2026-10-16 (12:57 PDT), in the project's theory and analyst thread; filed 2026-10-16. Contiguous excerpt; transcription repairs listed in the handoff.*

The three entries are one mechanism, recognizing a stored piece at any level and propagating
constraints through the rest, with different failure modes. From below, actions are recognized
through learned sensorimotor association
([Cook et al., 2014](https://doi.org/10.1017/S0140525X13000903), abstract read); the curator's
cortical reference frames are the Thousand Brains hypothesis
([Hawkins et al., 2019](https://doi.org/10.3389/fncir.2018.00121), snippet), not an established
mechanism. Through the middle, masters recognize meaningful chunks
([Chase & Simon, 1973](https://doi.org/10.1016/0010-0285(73)90004-2), snippet) and templates with
open slots at a glance ([Gobet & Simon, 1996](https://doi.org/10.1006/cogp.1996.0011), snippet), the
block slapped across the middle. From above, infants read action through its goal and efficiency
([Gergely & Csibra, 2003](https://doi.org/10.1016/S1364-6613(03)00128-1), snippet), and people infer
others' rewards and costs on the assumption that they act "as intuitive utility maximizers"
([Jara-Ettinger et al., 2016](https://doi.org/10.1016/j.tics.2016.05.011), read), the needs stapled
above the pyramid. Each entry fails its own way, so each should be weighted by its reliability. The
top projects, assuming the maker wants what the reader would want at the reader's costs; the middle
locks in, since the first familiar chunk can block a better reading
([Bilalić, McLeod & Gobet, 2008](https://doi.org/10.1016/j.cognition.2008.05.005), abstract read);
and the bottom is precise but local. Ghost's goal-tree card ran the mechanism in a constructed
world, and its result is not yet read into this file.

Disagreeing entries are often both right, since one goal can nest under another. Which is on top
changes the class of actions, and sacrifice shows the order now, which is not the same as the
structure. Priority moves with state. When choice minimizes the largest distance to any set point,
the largest current deficit wins
([Juechems & Summerfield, 2019](https://ora.ox.ac.uk/objects/uuid:02f3af5e-bc2d-49f5-bf1d-f2e3d7e2f545/files/m912294907691555c3e38afc843306587),
read), and a hungry person sacrifices belonging for food without food sitting above belonging.
People coast on a goal that is ahead of schedule and shift effort to another
([Thürmer, Scheier & Carver, 2020](https://pmc.ncbi.nlm.nih.gov/articles/PMC8022896/), read), so a
neglected goal may be ahead rather than lower. Sacred values break the exchange, and material
incentives increased opposition to compromise over them
([Ginges et al., 2007](https://europepmc.org/article/MED/17460042), read). Order is also visible
without sacrifice, because active goals inhibit competing goals, more strongly when they serve the
same overarching purpose
([Shah, Friedman & Kruglanski, 2002](https://europepmc.org/article/MED/12500810), read). Two orders
therefore stay apart, structural order, whose reference is set by whom, and conflict priority, who
wins now, which is what sacrifice reads; the split is the analyst's correction. The cleanest probe
of the curator's example removes the relationship prospect, a change of contingency rather than a
devaluation. Sex-seeking that then stops was serving belonging. Sex-seeking that continues was not
serving belonging alone, and it may be lust on top, habit or a learned end, which the second probe
of G191 in [`THE_TRIPLE_INFERENCE.md`](THE_TRIPLE_INFERENCE.md) §4 separates.

**Teardrops that emerge, overlay, and are topped by the last pass** *(2026-10-17)*:

> Everyone has a teardrop that is them. At the very top of that teardrop, hypothetically, you've got
> survival, but just beneath it are all of your attempts to solve it. You're a teardrop missing its
> tip, under this frame of reference, and it's made up of a bunch of tiny smaller teardrops that fit
> together. They kind of form out your plan for your life, and they literally are series of actions
> you want to take for your life.

> I think you start with a single goal, and other goals kind of emerge from it. You notice, for
> example, as you are creating that spoon, that it actually fits in such a way that you could use
> this spoon in other ways. You could use it to impress the lady that you like. And so you then put
> a little bit of effort into making sure that both of these teardrops are stable, but now you're
> trying to do both, and it's hard to balance the two [...]. You make it look good for the lady, but
> then it's not as good a spoon.

> I think what the editor is doing is expanding the teardrop. You, as an author, had a specific
> goal. The editor is making different goals. [...] As I say this, the author probably does it for
> many different goals, which is why we have the weird teardrop shape in ToMpathy, where it's really
> multiple teardrops overlaid on top of each other. [...] So the editor really overlays other
> teardrop shapes on top, to make sure that they also have appropriate fit.

*Curator's answers to the analyst's 17 October discussion questions, 2026-10-17 (07:52 PDT), in the project's theory and analyst thread; filed 2026-10-17. Separate excerpts with marked omissions; transcription repairs listed in the handoff.*

> You can have a starting goal, but the problem is, once you have a starting goal, the other
> pattern-matching expertise pieces can look at what you have created, look at the landscape, the
> tools that you now have in front of them, the new starting positions that now exist, and you can
> literally, if you want, discard your original goal and decide that this is your new goal, that
> you've made something more than you expected.

> I do think that the top goal is kind of [set by] the last person to pass judgment over the whole
> thing with the capability of changing it. They get to decide what that top goal is. [...] If they
> had handed it over to the editor, so the editor got the final stamp of approval, or they both had
> to do it together, simultaneously, both of them agreeing on the same set, that would be the only
> case in which both of them have parallel, equivalently high teardrops, I guess.

> Practically speaking, there's no top as much as [there are] different lenses. There are different
> overlays that you can add to it, and you have to make sure that your overlay lines up properly.
> [...] The only way to truly climb on top of someone, teardrop-wise, is if you saw they made a
> comment and you wanted to address it in some way, by incorporating it into the overall structure.
> And then you put a node on top of that, and all of a sudden it becomes leading into your teardrop
> instead. [...] I think the hierarchy is only implied if it's implied by the structure of the
> creation, but it isn't necessarily implied by the actual creation. Not every creation needs a
> hierarchy inherently.

*Curator's answers to the analyst's 17 October second-round questions and scorecard, 2026-10-17 (10:15 PDT), in the project's theory and analyst thread; filed 2026-10-17. Separate excerpts with marked omissions; transcription repairs listed in the handoff.*

The teardrop is the curator's picture of the goal structure this section reads, a maker's hierarchy
capped by survival with its tip missing and built from smaller teardrops of the same shape. Three
claims come with it. Goals emerge during making, as expertise sees new uses in the partial work, and
an emergent goal can replace the one that started it. The top goal of a shared work belongs to
whoever holds the last pass with power to change it, with equal tops only when parties sign off
together. And goal structures overlay rather than nest, so a hierarchy exists only where the
creation's structure implies one, and one party rises above another only by taking the other's
contribution into its own structure under a node of its own. The research names for the first claim
are opportunistic planning
([Hayes-Roth & Hayes-Roth, 1978](https://apps.dtic.mil/sti/tr/pdf/ADA064445.pdf), snippet) and, in
design, problem-solution co-evolution
([Dorst & Cross, 2001](https://cschan.arch.iastate.edu/235/20_Dorst-Creativity_coevolution.pdf),
snippet), and one means serving several goals at once is multifinality.

Law matches the second claim more closely than psychology does. In the Ninth Circuit's test for
joint authorship, control, superintending the work as its "master mind", is the first of three
factors, and "absence of control over the work is strong evidence of absence of co-authorship"
(Aalmuhammed v. Lee, 2000, through a
[summary](https://www.fwrv.com/news-articles/co-authorship-claim-denied) read). People's own sense
of authorship tracks something else. Writers did not consider themselves the owners and authors of
text a model generated, and their sense of ownership rose with their influence on it
([Draxler et al., 2024](https://doi.org/10.1145/3637875), read), and credit in human and AI
co-creation varied with the type, amount and initiative of each contribution
([He, Houde & Weisz, 2025](https://arxiv.org/abs/2502.18357), read). So the last pass decides who
may declare the top goal, contribution decides whose goals the work carries, and the two part where
the last party changes little. A single-author preprint argues that final selection authority is not
sufficient for authorship ([Cao, 2026](https://arxiv.org/abs/2609.10738), read, not peer reviewed).

On the third claim the cognitive literature is split. Routine action sequences can be learned with
no explicit hierarchy of schemas, context held in a single distributed representation
([Botvinick & Plaut, 2004](https://doi.org/10.1037/0033-295X.111.2.395), read), while flexible
behavior has been argued to require explicit, hierarchically organized goal representations
([Cooper & Shallice, 2006](https://doi.org/10.1037/0033-295X.113.4.887), read). Without a hierarchy
the last judge's top goal describes an attribution rather than the work's structure, which is the
analyst's reading of where the second and third claims meet. Ghost study N12, commissioned on 17
October, tests what an artifact alone can show of emergence, overlays and final authority, with the
prediction that final authority is visible only where the overlaid goals conflict.

| # | hypothesis | status |
|---|---|---|
| **lit** | Entry at any level, ratcheting to the others | **CONTESTED (READ).** Bullot & Reber make design-stance understanding a *necessary condition*; the disagreement is over necessity, not temporal order (their own response describes recursive processing) |
| **lit** | Bullot & Reber's framework is well supported | **REJECTED (READ-FULL).** 34 experiments across 23 publications: 26% support, 56% none |
| **HH-GOAL-PYRAMID** | Readers infer a maker's goal hierarchy by jointly adjusting labeled nodes, climbing to the goal that explains every decision the artifact records, entering from below through expertise or from above through function; adjacent levels give the strongest evidence and the explaining goal the broadest | **OPEN.** A constructed test ran as card C1 of the Ghost V22 first pass (13 October); its result is not yet read into this file. Construction-integration is the nearest comprehension model and minimal-cover plan recognition the nearest formal account of the explaining goal (lit, SNIPPET); function-first explanation over-attributes purpose in children (lit, READ) |
| **HH-ENTRY-RELIABILITY** | Readers enter a maker's goal hierarchy at three points, below through recognized actions, through the middle by recognized blocks of solutions, and above by assumed shared needs; the three are one mechanism with different failure modes, projection above, lock-in in the middle and locality below, so each entry should be weighted by its reliability | **OPEN.** Each entry has literature, and projection and Einstellung lock-in are documented failure modes (lit, READ and SNIPPET); the weighting by reliability is the analyst's; Ghost's goal-tree card ran in a constructed world and is not yet read into this file; no measurement on readers |
| **HH-SACRIFICE-ORDER** | When goals nest, which one is on top changes the class of actions, and what the maker will sacrifice for the goal above reveals the order; sacrifice reads current priority, which moves with deficits, progress and sacred values, while structural order is read from whose reference is set by whom | **OPEN.** Set points compete by the largest deficit, goals ahead of schedule are coasted on, sacred values resist exchange, and goal shielding shows order without sacrifice (lit, READ); the split between priority and structure is the analyst's correction; removing the upper goal's prospect is the cleanest probe and has not been run |
| **HH-GOALS-EMERGE** | A maker starts from one goal, and others emerge during making as expertise sees new uses in the partial work; an emergent goal can join the first or replace it, and balancing two goals with one focus of attention costs each some fit | **OPEN.** The curator's claim (2026-10-17); the research terms are opportunistic planning, problem-solution co-evolution in design, and multifinality for one means serving several goals (lit, SNIPPET); learned ends that outlive their origin are G191 in [`THE_TRIPLE_INFERENCE.md`](THE_TRIPLE_INFERENCE.md) §4; Ghost study N12 is commissioned to test what an artifact shows of it |
| **HH-LAST-PASS** | The top goal of a shared work belongs to whoever holds the last pass over the whole with power to change it; equal tops exist only when parties sign off together | **OPEN for the last pass as the right to declare the top goal; CONTESTED (lit) for authorship following the last pass.** One appeals court's joint-authorship test weighs control first (lit, SNIPPET); writers' felt ownership and lay credit track influence and contribution rather than final say (lit, READ); one preprint argues final selection authority is insufficient (lit, READ); Ghost study N12 tests when final authority is identifiable from the artifact |
| **HH-OVERLAYS** | Goal structures overlay rather than nest; a work carries several makers' structures as lenses, a hierarchy exists only where the creation's structure implies one, and one party rises above another only by incorporating the other's contribution under a node of its own | **OPEN.** Routine sequences are learnable without a schema hierarchy, while flexible action has been argued to need one (lit, READ); the curator's claim; no project measurement; Ghost study N12 compares single-top and overlay readers |

**What the table says.** The only occupying framework makes level-entry a necessity claim with a
weak empirical record, which leaves enter-anywhere both undefended in the literature and untested
here. The deciding experiment is the triple inference's missing mechanics arm. Joint settling over
the goal hierarchy is the same claim inside the purpose level, entered from below or from above,
with a constructed test run but not yet read and no measurement (HH-GOAL-PYRAMID). The three entries
are one recognition mechanism with different failure modes, so a reader should trust each in
proportion to its reliability (HH-ENTRY-RELIABILITY), and sacrifice reads which goal wins now rather
than which sits above, the distinction the date example needs before it can order a maker's goals
(HH-SACRIFICE-ORDER). Goals also emerge during making and can replace the first (HH-GOALS-EMERGE),
the top goal of a shared work belongs to whoever holds the last pass, a claim the law supports and the
psychology of credit qualifies (HH-LAST-PASS), and several makers' structures can overlay one work
without nesting (HH-OVERLAYS). Confidence: untested, logic only, resting on a contested literature.

## §4. Updating and active search

> It starts questionable... 8 or 9 by the end.

The quote is pulled from a specific reading of one artifact, the updating and active-search
process run live while answering author and provenance questions during early corpus
construction, and *"the read-alongs ended up being more useful than the actual corpuses."*

**Confidence may change during a reading.** Whether its trajectory adds information
beyond the endpoint is an open question (HH-9). A model-side series instrument has been
built: its pooled tracking of exact information is a valid null at the declared band
(R05-S5, L329). That is a different question from the trajectory's incremental value over
its endpoint, and neither comparison validates a human reader's confidence. The
reader also searches actively. Re-reading (each pass recovering lower-confidence
attributions from the tail), **epistemic foraging** for biography and further works,
where *everything is an artifact* becomes operational (context supplies additional
observations but is not automatically trustworthy), and switching levels when a
hypothesis fails, per §3.

**Context reweights the generative model rather than dictating a story** *(2026-08-21)*:

> The low-quality-paint inference was a shifting of possibilities – the generations of your
> generative model being weighted differently – not an immediate inductive set of steps.

> It's possible that the relevant possibilities were already present but weakly weighted.
> Context might be something I totally missed though.

*Curator's six-question maker-model and context walkthrough, supplied in the analysis thread; recording date not separately supplied;
filed 2026-09-18. Contiguous excerpt, wording preserved.*

> It was this data organization that explained many of the choices that I had not even remarked
> upon as unusual.

> I actually worry that my specific explanation is overbiasing me and isn't being treated as one
> of many possible solutions.

*Curator's Worth the Candle example and its immediate qualification in the local-goal,
evidence-reorganization and expertise walkthrough, supplied in the analysis thread; recording
date not separately supplied; filed 2026-09-21. Separate contiguous excerpts, wording preserved,
with line wrapping and punctuation normalized.*

The new account can change which familiar details count as diagnostic choices, not only their
weights after retrieval. Distinguish additional observations, improved access or organization of
existing evidence, and expansion of the candidate family. A supplied explanation can do more
than one of these; even a cue about already visible facts can introduce a new relation or
privileged answer. No particular activation function, rotation or neural threshold follows from
the introspection. The literary example records a changed reading, not independently verified
knowledge of the author's motives or values.

Context does not license a story in one step. A coherent false frame may reorganize many
details, and details explained by one common cause are not independent confirmations.
Historical interpretation gains warrant from independently assessed correspondence or
discriminating consequences, not from explanatory reach or felt change alone. The curator's
favored explanation remains one candidate. The tool-conditioned rule lives in §6, and
target-specific correction remains open in HH-23 and HH-25.

The flower example adds a candidate reason some context cues reorganize many details:
a condition believed to persist through much of production may affect several choices
together. Claimed loneliness could therefore change the reader's interpretation of a
bright flower without establishing either the artist's actual state or the flower's
intended meaning. Duration, explanatory reach, and source reliability are different
properties. A broadly applicable cue can be reliable, misleading, or too flexible to
constrain anything. The historical account earns support through independently assessed correspondence or
discriminating consequences beyond the story it prompted; it does not inherit support from
the reader's felt change alone.

**The current ordering conjecture places context especially at maker differentiation.** The
artifact first supports a self-based candidate distribution; biography, prior work, tools,
culture, role, and source reliability then help move that distribution toward this maker. This is
not a fixed serial architecture. Context-first and joint processing remain live rivals, and any
order that lets a false assertion overwrite strong artifact evidence is a trust failure rather
than successful differentiation. Attention allocation, epistemic weight, process uptake, belief
uptake, and value change remain separate outcomes.

**Attention may implement part of selective trust.**

> I wonder if attention is how, like control of your attention is what trust becomes, for example.

> By looking I mean directing attention. How interesting. Maybe. This is a maybe.

> And obviously I'm trying to acquire the method while declining the aim. That's clearly a thing.

*Curator's contribution and selective-attention walkthrough, supplied in the analysis thread; recording date not separately supplied;
filed 2026-09-18. Separate contiguous excerpts, wording preserved.*

The proposed mechanism is selective investigation: attend to how a technique works while
limiting uptake of the source's aims or arguments. The curator includes precision adjustments
in this broader control of attention. Separating observable selection from later weighting
therefore need not imply two independent human systems, and the conjecture does not restore
the previously withdrawn identity between proximal goal and attention.

Protection is expected to be imperfect. Understanding a method may require some of its
argument or hidden dependencies; expertise might expose those dependencies without providing
immunity. A source's decision structure includes which evidence it sought, retained and
presented. Truthful individual examples can therefore coexist with misleading selection.
Measure continued engagement, process learning, belief uptake and value change separately;
blanket refusal is not successful selective learning. Consciousness has not been identified with an
attention mechanism by the present evidence; epistemic disgust is held below as a conjecture about
how attention or elaboration is withheld.

**Attention, uptake and disgust** *(2026-10-13)*:

> One curve for both attention and uptake is actually kind of where I'm at. [...] It came from the
> fact that if you're working with, like, I don't know, Mein Kampf, for Hitler, you can explicitly
> focus on things like sentence structure while avoiding things like thinking about why he might have
> thought that about the Jews. Like, if you think about the [...] reasoning, and did you pay attention
> to that? Then it causes uptake in that region. Specifically, I think attention is kind of uptake.

> You're not terrified of reading Mein Kampf, but you do acknowledge it as risky, because it would
> probably influence you, because even as you are attending to things like sentence structure, you
> might accidentally pay attention [...]. Literally, the aesthetics are a virus. Aesthetics can
> direct your attention in addition to you. Things can grab it and move it around.

> Wait, I've been saying, I'm contradicting myself. I've been saying that attention is [...] all
> that's needed. And no, I'm not contradicting myself. Disgust is the mechanism through which that
> occurs. Your disgust with Mein Kampf is how you keep your attention away from the bits that you
> don't want to think too hard about. It is literally, the withdrawal is the protection. The lack of
> attention is the protection, and the disgust is the vehicle through which it creates a solid line
> around it. How neat!

*Curator's ToMpathy assessment walkthroughs, 2026-10-13 (14:01 and 16:29 PDT), in the project's assessment thread; filed 2026-10-14. Separate excerpts with marked omissions; transcription repairs listed in the handoff.*

> The second idea was, we thought that epistemic disgust actually fires, it seems, on policy
> divergence rather than on preference divergence. It's actually pretty clear when we work out
> examples that that's the case, that epistemic disgust occurs when, like, racism is a good example.
> With racism, it is literally me saying that [...] not only do I think the actions you're taking are
> leading to outcomes that are useless, but in particular, I'm tiering them up to, like, survival and
> reproduction. Everything's tying up to survival and reproduction at the end of the day, or something
> like it. And so what I'm seeing are, what's pushing me away is your policy mapping. And not just
> that, but your entire model family has pre-solved solutions. Your culture, for example, can be one
> that I can find disgusting as a group, because the set of solutions is one that your policy mapping
> diverges too much. You clearly are trying to optimize different ways [...]. It triggers that
> response.

> But my friend cleverly pointed out that epistemic disgust firing on policy divergence doesn't make
> sense, because then we wouldn't be able to grow outside of racism, if that were the case. Great
> argument, I said. But my counter was that epistemic foraging beats that, because openness to
> experience is the primary indicator for someone who's prone to racism. That last statement I wasn't
> quite sure on. [...] Maybe that openness to experience is the key. There's like a humility, and the
> idea that other people might have a better policy mapping than you do. That they might have a
> hierarchical channel that gets them where they're going more efficiently. Whether or not you know
> that, a willingness to explore this is what creates this acceptance, and how it beats that effect.

*Curator's evening walkthrough after an in-person discussion, 2026-10-13 (19:02 PDT), in the project's errata thread; filed 2026-10-14. Separate excerpts with marked omissions; transcription repairs listed in the handoff.*

The April essay's firewall fired on divergence between the reward inferred for the maker and the
observer's own; these restatements move the trigger to policy, meaning methods, heuristics and the
solutions a culture has already worked out, and move the protection from a closed gate to attention
held away. Three parts separate. A trigger (policy divergence, possibly judged inferior), a
protective act (attention or elaboration withheld from the source's aims), and a release (foraging
licensed by the belief that the other's route may be better).

The literature mostly supports a policy-level trigger and contests the emotion's name and the
attentional form of the protection. Disgust is recruited when a preference is moralized into a
value, while taste alone does not recruit it
([Rozin, Markwith & Stoess, 1997](https://stafforini.com/works/rozin-1997-moralization-becoming-vegetarian/),
abstract read). Moral disgust targets norm violators and motivates avoiding them as social partners
([Tybur, Lieberman & Griskevicius, 2009](https://www.unm.edu/~tybur/docs/microbes.pdf), abstract
read), and out-groups are avoided partly as violators of local practices
([Navarrete & Fessler, 2006](https://inclusion.uoregon.edu/sites/default/files/2_disease_avoidance_and_ethnocentrism.pdf),
read). Violations of community norms are assigned to contempt rather than disgust in the
CAD mapping (Rozin, Lowery, Imada & Haidt, 1999, snippet), and contempt appraises the other as
beneath a standard of competence or worth
([Roseman, 2018](https://crab.rutgers.edu/users/roseman/Roseman.2018.RejectingTheUnworthy-TheCausesComponentsAndConsequencesOfContempt.pdf),
read). Disgust-evoking images hold visual attention longer than fear-evoking ones
([van Hooff et al., 2013](https://research.vu.nl/en/publications/disgust-and-not-fear-evoking-images-hold-our-attention/),
abstract read), so if disgust protects, it more plausibly withholds elaboration than gaze. Contact
between groups reduces prejudice mainly by lowering anxiety and raising empathy, less by adding
knowledge ([Pettigrew & Tropp, 2008](https://courses.washington.edu/pbafhall/563/Readings/pettigrew.pdf),
read), and its favoring conditions include common goals and cooperation
([Pettigrew, 1998](https://ns1.serendipstudio.org/oneworld/system/files/annurev.psych_.49.1.65-2.pdf),
read). Openness to experience predicts lower prejudice robustly but mostly through authoritarian
attitudes, beside agreeableness acting through social dominance orientation
([Sibley & Duckitt, 2008](https://journals.sagepub.com/doi/abs/10.1177/1088868308319226), abstract
read), and intellectual humility raises openness to opposing views
([Porter & Schumann, 2018](https://www.researchwithrowan.com/en/publications/intellectual-humility-and-openness-to-the-opposing-view/),
abstract read). The "primary indicator" wording is stronger than this record.

**What makes disgust fire** *(2026-10-14)*:

> Disgust flares when you, in particular, when you identify evidence of a decision you wouldn't
> make, and that you cannot even see how to slot into your hierarchy. I can't see how someone would
> want to murder all the Jews in order to achieve their goals, because it's a silly thing to do.
> It's also horrifying, but in the usefulness sense, it's silly. And I think maybe that's the
> biggest problem? Is it useless? I'm not confident on this one.

> Contempt might be something that fires when you identify someone else's structure, and you think
> you have the entire thing figured out, and you have a higher structure or something. I don't
> know. I'm not looking at it too directly. It's just a guess.

*Curator's walkthrough of this handoff's decisions and questions, 2026-10-14 (12:22 PDT), in the project's errata thread; filed 2026-10-14. Separate excerpts with marked omissions; transcription repairs listed in the handoff.*

The trigger narrows from policy divergence to divergence the reader cannot fit into any goal it can
model, judged useless as well as harmful. The curator's sense of talking past the analyst comes
from framing disgust as protecting something, a set point or a reading rule; here the trigger is an
inference failure and withdrawal is its effect. Social cognition research supports that shape.
Groups perceived as neither warm nor competent draw contempt and disgust
([Fiske, Cuddy, Glick & Xu, 2002](https://leeds-faculty.colorado.edu/dahe7472/Fiske-et-al-2002.pdf),
read), and pictures of those groups fail to engage the medial prefrontal region that responds to
every other social group, activating insula and amygdala instead
([Harris & Fiske, 2006](https://www.psychologicalscience.org/journals/psychological-science/j.1467-9280.2006.01793.x/),
abstract read). The reader stops modeling a mind, which is the withheld elaboration of
HH-DISGUST-GATE. Competence is that literature's word for useful, and a target judged competent but
cold draws envy instead of disgust, the split that lets a reader study a propagandist's technique
while walling off the aims. The contempt guess, a complete model of the other's structure held from
above, matches the appraisal of the other as beneath a standard
([Roseman, 2018](https://crab.rutgers.edu/users/roseman/Roseman.2018.RejectingTheUnworthy-TheCausesComponentsAndConsequencesOfContempt.pdf),
read).

**Where attention goes** *(2026-10-14)*:

> I would say that attention goes where prediction errors are falling fastest, but that you do have
> some kind of global attentional [...]. I feel like there's a conscious element to attention. It's
> not just reactive. [...] Things that are prediction errors that are falling fastest will attract
> attention, and if they fall super fast, they attract attention very quickly, but that doesn't mean
> that attention can't also voluntarily be directed elsewhere. It's just biased.

> But the one thing I hope is that attention isn't just being drawn to, like, internal prediction
> errors dropping or something. Finding places in the inference where, in your overall trajectory
> mapping towards your goals, [...] the prediction errors are falling the most, and that's where your
> attention focuses, or something stupid like that. God, I hope it's not that. I really hope that
> attention is directed through this nebulous alternative force that can be somehow captured.

*Curator's walkthrough answering the assessment thread, 2026-10-14 (received 10:30 PDT in the project's errata thread); filed 2026-10-14. Separate excerpts with marked omissions; transcription repairs listed in the handoff.*

The curator accepts falling prediction error as a pull on attention and rejects it as the whole
account. The stake is the attention policy's role as the preference stream, since a policy that only
chased learning progress would carry no preferences. Each part has support. Infants' looking is
explained partly by their progress in learning a sequence, beside surprise and the sequence's
overall predictability ([Poli et al., 2020](https://pmc.ncbi.nlm.nih.gov/articles/PMC7531891),
abstract read). Attention research has given up the two-source split between current goals and
physical salience and added a third source, the history of earlier selections and rewards
([Awh, Belopolsky & Theeuwes, 2012](https://pmc.ncbi.nlm.nih.gov/articles/PMC3426354), snippet),
which is close to the record of past attention that expertise keeps. Active inference models
voluntary attention as a mental action, a choice of where to place precision made by a higher level
of the same model ([Sandved-Smith et al., 2021](https://discovery-pp.ucl.ac.uk/10134499/1/Friston_niab018.pdf),
snippet). That choice is scored by expected free energy, which adds expected preference satisfaction
to expected information gain ([Friston et al., 2015](https://doi.org/10.1080/17588928.2015.1020053),
abstract read), so in that formalism preferences enter attention through the first term and
learning progress through the second. The voluntary part the curator hopes for is formally
available, and it is where preference evidence in attention would have to live.

> Oh, you're talking about the thing that moves attention. Whatever that is. It's expected
> preference satisfaction, but it's complicated, because it's showing you part of how they're
> trying to achieve that. Like, it's showing you their values, and their emotions, for that matter.
> It shows you part of how they're working their way up the tree to accomplish their survival [and]
> reproduction.

> Honestly, I think this isn't quite a God of the Gaps thing anymore. I think we're explicitly
> looking at the goal of, like, what is the goal of the epistemic foraging actions?

> Well, extracting attention as mental action, with respect to that formal version, sure does look
> like it just is a clean way of describing what I was saying anyway.

*Curator's walkthrough of this handoff's decisions and questions, 2026-10-14 (12:22 PDT), in the project's errata thread; filed 2026-10-14. Separate excerpts with marked omissions; transcription repairs listed in the handoff.*

The curator names the force. It is expected preference satisfaction, read through the values and
drives it passes on the way up the hierarchy, and he takes the mental-action formalism as a
description of it. What remains open is the goal of the maker's epistemic foraging, which is an
inference target rather than a gap.

**What grabs and what wants** *(2026-10-16)*:

> Attention stream shows both. [...] You are aesthetically pulled towards regions of falling
> surprise. I believe it's falling surprise is the current guess. It actually sounds kind of nice to
> me. [...] That is what aesthetics is, I would even argue. But you still have some ability to
> direct it manually. You can move away from the thing pulling your attention. You can look away
> from the cleavage.

> In the moment, choices that people later reverse belong in the triple inference in something that
> someone was letting their flow state, their expertise, overarchingly address. But then as they
> step back and look at the entire work, they see that it doesn't actually help them in support of
> their higher order goals, their highest order goals, whatever it is they're trying to accomplish
> there. And so they need to make some modifications to that expertise's generation in order to work
> for this particular function. And you're trying to correct that as it happens. That's why you are,
> as an expert, that's what grabs your attention during flow state is things that you might want to
> adjust for the greater higher order goal. But that you often miss things, just because.

*Curator's walkthrough of the analyst's 16 October theory pass, 2026-10-16 (11:56 PDT), in the project's theory and analyst thread; filed 2026-10-16. Separate excerpts with marked omissions; transcription repairs listed in the handoff.*

The attention stream mixes three things, two that grab and one that wants. The pull comes from
surprise that is falling, which the curator calls aesthetic and §5 refines. Capture comes from
drives, which is the analyst's reading of the curator's cleavage example, one he described as pull.
It also comes from learned value, since previously rewarded stimuli keep capturing attention after
the reward is gone, "independently of goals and salience"
([Anderson, Laurent & Yantis, 2011](https://doi.org/10.1073/pnas.1104047108), read). That kind is
learned rather than inherited, and whether it is habit or a learned end is the question of G191 in
[`THE_TRIPLE_INFERENCE.md`](THE_TRIPLE_INFERENCE.md) §4. Voluntary direction is the third, the part
that can look away, and it is the part directed by expected preference satisfaction. Preferences are
read from it, which makes separating it from the pull and the capture the measurement problem of
this section.

Reversals come in two kinds. The curator's kind is flow-state output from expertise, audited later
against the higher goal and corrected, which matches expert revision, since experienced writers
revise for meaning and structure while students revise words
([Sommers, 1980](https://openlab.citytech.cuny.edu/fywpd/files/2019/01/sommors-revision-strategies.pdf),
read). The second kind, the analyst's addition, is a near-tie that flips because little was at
stake, and choices between near-equal options are slow
([Konovalov & Krajbich, 2019](https://doi.org/10.1017/S1930297500006082), read). The two predict
opposite timing. An audited reversal follows a fast first choice and a later review, a near-tie
reversal follows a slow first choice, and only the first carries the higher goal.

**Attention is deciding what to trust** *(2026-10-17)*:

> Whenever we're in any kind of psychological space, my answer is always going to be, it's all of
> them. Every answer is always "it's all of them", because the one overarching rule is anything that
> can be associated will. That is a bit of a cop-out, though, so let me give you a better answer.

> Her past is just all previous habits. So yes, obviously it is her past, because it's pulling from
> that. [...] [Her eye] is being pulled to the area that is compressing the fastest, which is that
> corner, but she is purposefully going to move herself away from that, and that is her actual
> preference. That is her wanting to want, in this case. [...] I would even say that the automatic
> process of her eyes is to zero in on things that have compressing information. And if that's the
> flow state of the eyes, she will literally have to manually wrest control of her eyes to move them
> elsewhere. And that action, that very action, is attention.

> I do think, off the cuff, that trust is going to be the big piece. You are deciding how much to
> weight each signal, as always. [...] Allocating trust on, like, a math level is what we're doing.

*Curator's answers to the analyst's 17 October discussion questions, 2026-10-17 (07:52 PDT), in the project's theory and analyst thread; filed 2026-10-17. Separate excerpts with marked omissions; transcription repairs listed in the handoff.*

> I'm treating attention as both. You're right. Maybe I'm assuming it's the same thing, that what
> you're doing is adjusting the trust on various signals to control. Is that how you get control?
> The effort is gained through adjusting trust levels? That's what you do as an attender. All you
> can do, the safe option, is to decide what to trust. And in doing so, that automatically moves
> your eyes to some other place. There are manual ways to do this. You can just manually increase
> the belief that there is something interesting to be had in part of your field of view, and you
> can use that to wrench your eyes wherever you want. Maybe that's what attention is.

> Attention is a separate thing. It's the corrector. [...] Attention is trust, is what I think I'm
> trying to say here. Or rather, attention is deciding to run an inference on whether to trust in a
> given specific setting.

*Curator's answers to the analyst's 17 October second-round questions and scorecard, 2026-10-17 (10:15 PDT), in the project's theory and analyst thread; filed 2026-10-17. Separate excerpts with marked omissions; transcription repairs listed in the handoff.*

The research term for the curator's trust is precision. In predictive processing, attention is
"inferring the level of uncertainty or precision during hierarchical perception", and a cue that
raises the expected precision at a location draws processing there
([Feldman & Friston, 2010](https://doi.org/10.3389/fnhum.2010.00215), read), which is his manual
increase in the belief that something interesting lies in one part of the field of view. The
framework splits what he joins, though. Sensory precision is attention in that narrow sense; where
to look next is driven by expected information gain, which Parr and Friston separate as salience
([Parr & Friston, 2019](https://doi.org/10.1016/j.copsyc.2018.10.006), read); and control is the
precision on policies, the weight given to goal-directed evaluation against a habit prior. Effort
then reads as the divergence between context-sensitive beliefs about how to act and the
context-insensitive habit, and "effort is exerted to overcome a mental habit"
([Parr, Holmes, Friston & Pezzulo, 2023](https://doi.org/10.1016/j.neuropsychologia.2023.108562),
read; [Zénon, Solopchuk & Pezzulo, 2019](https://doi.org/10.1016/j.neuropsychologia.2018.09.013),
read). That reverses one of his phrasings. Effort is the cost of acting on sharp beliefs against the
habit, not something trust produces, and expected information gain follows from current uncertainty
rather than being set at will.

The safe corner fits the split. Her gaze runs on the habit and on what compresses fastest, and
wrenching it away is policy precision overriding the habit prior, the corrector of his second
answer. Arbitration between habitual and goal-directed control by their relative uncertainty is a
standard account of which one wins ([Daw, Niv & Dayan, 2005](https://doi.org/10.1038/nn1560), read).
Rival accounts of effort need no habit prior. Control may be allocated by its expected value net of
cost ([Shenhav, Botvinick & Cohen, 2013](https://doi.org/10.1016/j.neuron.2013.07.007), read) or
priced by the opportunity cost of other uses
([Kurzban et al., 2013](https://doi.org/10.1017/S0140525X12003196), read). Sounding Line card D39,
commissioned on 17 October, asks whether writers examine a source's next offers harder after it
fails them, and Ghost study N15 asks what that test can separate.

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

**What gates uptake, and how technique writes values in** *(2026-10-13)*:

> There's something to do with uptake and the idea of shared goals too. If the higher order goals the
> two of you share are there, then the lower order goals are useful. But if you don't share the
> higher order goals, then the lower order goals will fuck up your process, often in a way that helps
> your opponent. So if you don't understand the propagandist is trying to give propaganda, then you
> can't fit that behavior into your model of propaganda. If instead you think they're trying to
> inform, then you can fit it into your model of whatever the fuck else you think, and then you're
> fucked. So it's not just probability of a common cause. It's probability that you have found their
> highest cause, in this case, and then it aligns with yours.

> [...] Dependencies is probably how those things, values, get written in through technique. It
> changes how you see the world a little bit, and that changing in the way that you see the world is
> what changes your behavior, because you see different possibilities. Like, yes, you read Mein Kampf
> to learn how to be [...] a good speaker or whatever. And as you do the speaking, you start to see
> more opportunities for speaking, which makes you more manipulative, which makes you a little bit
> more Hitleresque, and it kind of snuck in there through just distortions of the possibility space.

> Clearly there is a social component, and I think [...] it can't be separate. It has to be part of
> the same unifying model, and I think to do that we're just going to have to treat sensory input from
> the museum curator as equivalent to sensory input from the picture. Except that that's not enough.
> Could you do, like, a quick and dirty inference of this person to assess that they definitely have
> better expertise than you do? [...] I feel like there's an in-model way of solving this. It all has
> to be connected. It has to all be one big thing. I don't just want to add a fucking social term.
> It's just not acceptable.

*Curator's ToMpathy assessment walkthroughs, 2026-10-13 (14:01 and 16:29 PDT), in the project's assessment thread; filed 2026-10-14. Separate excerpts with marked omissions; transcription repairs listed in the handoff.*

Uptake is gated by a maker inference about the source itself. Has the reader found the source's
highest goal, and does it match the reader's own? Credibility is the same inference aimed at the
source's competence and intent to inform, which keeps trust inside the maker model rather than
adding a social term. The technique route needs no gate failure at all. Practice changes which
options a reader sees, and what people consider by default is already shaped by value
([Phillips, Morris & Cushman, 2019](https://stafforini.com/works/phillips-2019-how-we-know/),
abstract read). Persuasion knowledge, a person's model of how persuasion attempts work, is the
closest named construct for the propagandist case (Friestad & Wright, 1994, snippet).

| # | hypothesis | status |
|---|---|---|
| **HH-9** | The confidence trajectory across a reading carries more than its endpoint | **OPEN for incremental value over the endpoint and for human readers.** A model-side series exists, but its tracking of exact information is a different comparison and is a valid null at the declared band (test, R05-S5, L329) |
| **G64** | Re-reading one artifact recovers the tail | **OPEN.** Canonical in the triple inference §5; the reader-side strategy is this section's |
| **G167** | Declared context reweights the reader's maker-model distribution, where a false context must not steer equally | **PROJECTION where evidence is absent (test, L155); MIXED at 0.44 where evidence is strong (test, L157); the wing is PAUSED.** With nothing readable to resist it, a false card steers 95 percent as hard as a true one and erases the reader's abstention. Against evidence the reader provably reads at 0.86, a false note still costs forty-two points, wins the toss-up at 0.53, and the conflict is named only 0.15 of the time even when the format offers the option; a true note lifts the reader to 0.99, so any supplied note is treated as high-grade evidence regardless of truth. Context-trust is a separate defect from evidence-reading in this family |
|   | | *(this row's history is the projection root and its evidence-conflict follow-up, both 08-21, the wing pausing per the brief's W3 routing)* |
| **HH-24** | Self-based process reconstruction can update a reader before source and value-similarity appraisal finishes | **OPEN.** The proposed indoctrination interval; requires separate measures of process uptake, belief uptake, and value change. G167 is adjacent instrument behavior, not evidence for the human mechanism |
| **HH-SELECTIVE-ATTENTION** | Directed attention, potentially including precision control, supports useful process learning while limiting unwanted uptake from the same source | **OPEN.** Curator conjecture; the human test requires joint measures of attended content, process learning, belief uptake and value change that the current program does not provide. Constructed procedural interference is an analogue, not those missing measurements |
| **HH-DISGUST-GATE** | Epistemic disgust protects by withholding attention or elaboration from a source's aims while its method can still be learned | **OPEN for withheld elaboration; CONTESTED (lit) for withheld gaze.** Disgust-evoking images hold visual attention longer than fear-evoking ones (lit, READ); a constructed reader can read accurately with its uptake gate closed (Ghost E42, sim), so attention and uptake can separate; a constructed test ran as card A3 of the Ghost V22 first pass (13 October), not yet read into this file. No human measurement of attended content, elaboration and uptake together |
| **HH-DISGUST-POLICY** | Epistemic disgust fires on a decision the reader would not make and cannot fit into any goal it can model, policy divergence (methods, heuristics, a group's pre-solved solutions) judged useless as well as harmful, and growth past it runs through foraging licensed by humility and shared lower goals | **OPEN; the trigger's shape is supported and the label CONTESTED (lit).** Moralized preferences recruit disgust where taste does not; moral disgust targets norm violators; out-group aversion tracks violations of local practices; groups judged neither warm nor competent draw contempt and disgust and do not engage regions that support thinking about minds (lit, READ). Community-norm violations map to contempt in the CAD triad (lit, SNIPPET). Contact reduces prejudice mainly through anxiety and empathy, and humility and openness predict tolerance (lit, READ). No project measurement |
| **HH-TOP-GOAL-UPTAKE** | Uptake depends on the reader having found the source's highest goal and on that goal matching the reader's; credibility is the same maker inference aimed at the source | **OPEN.** Constructed tests ran as cards A1 and A2 of the Ghost V22 first pass (13 October), not yet read into this file (endogenous trust, the misfiled propagandist); persuasion knowledge is the nearest literature (lit, SNIPPET) |
| **HH-ATTENTION-SOURCES** | Attention mixes three sources, a pull toward falling prediction error, capture by drives or by learned value, and a part directed by expected preference satisfaction, which carries the maker's values and drives; preferences are read from the directed part, and the pull dominates when set points are met | **OPEN.** Learning progress, selection history, value-driven capture and attention as a mental action each have literature (lit, READ and SNIPPET); no project measurement separates the directed part from the pull and the capture |
|   | | *(this row's history is its two-source form of 2026-10-14; capture by drives and by learned value, the analyst's readings of the curator's 2026-10-16 walkthrough, were added the same day)* |
| **HH-REVERSAL-KINDS** | Reversed choices come in two kinds, flow-state output from expertise audited later against the higher goal, which carries that goal, and near-ties that flip because little was at stake, which do not; the first follows a fast original choice and the second a slow one | **OPEN.** Expert revision targets meaning and structure, and choices between near-equal options are slow (lit, READ); the near-tie kind and the timing contrast are the analyst's; no project measurement of reversal timing |
| **HH-ATTENTION-TRUST** | Attention is the corrector that sets how far to trust each signal, an inference on whether to trust in a given setting; control, and the effort of wrenching gaze, come from adjusting trust, as when raising the believed interest of a region moves the eyes there | **OPEN.** Attention as precision, salience as expected information gain, policy precision against a habit prior, effort as divergence from habit and arbitration by uncertainty each have support (lit, READ); the framework separates the attention, salience and control the curator joins, and treats effort as the cost of overriding habit rather than a product of trust (lit, READ); Sounding Line card D39 and Ghost study N15 are commissioned. The complete matched next-menu hover comparison is null and its latency secondary unresolved (test, S15-DRIVE-W1-1017, D39; human CoAuthor menu-event records, exact program). These logs do not identify gaze or internal trust; the general mechanism remains open. |
|   | | *(2026-10-18: the curator specifies per-mistake, surprise-sensitive updating; D39 remains null, while canonical D38 supplies a scoped association rather than a trust measure. See G225 and the section conclusion.)* |
| **S13-CONTEXT-MEMORY** | Evidence-linked memory improves recorded-action support beyond raw retrieval or repetition | **Original contrast VOID; matched rendering advantage descriptive, general benefit OPEN (test, L455/L456/L460; exposed CoAuthor process records, GPT-2-medium likelihood reader).** The complete information-matched, equal-length primary comparison favors linked over raw or repeated facts on both proper losses throughout. No memory performs better on calibration and reserve; misassociation also improves over raw, and padding changes performance. One component per partition and mostly identical projected views preclude population or replication claims; independent memory and paired literal-confidence comparison remain unavailable. |
|   | | *(L455: original memory manipulation erased by token projection; L456: unequal-length development correction realizes distinct treatments but favors raw/repeated memory; L460: separately frozen full-roster matched projection reverses that ordering, while no-memory and misassociation controls limit the inference. Original void and exposure retained.)* |
| **S12-CONTEXT-1** | Correct relations help beyond equally supplied false/irrelevant framing, and more records correct a false frame | **OPEN beyond the complete descriptive blocks (test, constructed worlds, Qwen model reader and exact-program reference, L412/L419).** Correct, false and irrelevant explanations improve against raw input; the second block favors the correct frame, but order, rereading and unchanged repetition also help. Further records substantially improve the second false-frame comparison, without consistent modal improvement under the correct frame. Invalids and infinite losses remain. No general truth-sensitive mechanism, stable method rank or human correction claim is established |
| **S12-REVISION-1** | Does supplying the exact earlier reply help useful revision at identical later evidence? | **NARROWED by the reserved false-frame interaction (test, L439/L450; separate 64-history constructed rosters in one law, Qwen direct/account readers and independent exact references).** Discovery remains unresolved. The reserved false-minus-true saved penalty clears the frozen harm margin; true and neutral saved-versus-fresh companions remain unresolved. All invalid and zero-support penalties remain. Original process-dependent primary intervals are void for exact replay, with separately preserved canonical CPU corrections. This identifies an explicit saved-text disadvantage, not hidden persistence, selective correction beyond unchanged/irrelevant movement, or a human mechanism. |
|   | | *(L433/L435: eight-history conditional effects confounded frame with history; L439: complete three-frame crossing removes that confound but remains unresolved; L450: a prospectively reserved roster in the same law resolves the false-minus-true saved penalty after the same deterministic interval correction.)* |
| **S12-ATTRIBUTED-ANSWER-1** | Does the correctness, stated confidence or claimed ownership of an earlier answer change later reading? | **OPEN; the frozen pooled contrasts remain unresolved (test, L440; 32 constructed histories in one law, Qwen direct/account readers and independent exact references).** All supplied factors are crossed at matched input byte length. The incorrect-minus-correct interval is above zero but does not wholly exceed the harm margin; confidence, ownership and method contrasts establish neither benefit, harm nor equivalence. These pool diagnostic and irrelevant updates, so no selective-correction interaction, actual prior authorship, hidden memory or human mechanism is identified. Invalids and infinite losses remain. |
| **S13-REVISION-CONTROLS** | The false-frame saved-reply penalty remains after unchanged or irrelevant-update movement is subtracted | **SUPPORTED only as a descriptive adjusted diagnostic (test, L453; the exposed 64-history constructed discovery roster, retained Qwen direct/account forecasts and exact targets).** Both adjusted interactions are positive with their new 95% descriptive intervals above zero. Original primaries, practical margins, invalids and the separate reserved roster are unchanged. This measures explicitly supplied earlier text in one law, not hidden persistence, general selective correction or a human mechanism. |
| **S12-COMMON-CAUSE-1** | Does the reader distinguish repeated reports of one event from an independent observation? | **OPEN for the evidence-dependence mechanism (test, L441; 64 constructed histories in one law, Qwen direct/account readers and exact-program references).** All four evidence-view contrasts remain unresolved at the frozen margin; pooled account reading improves excess loss over direct reading. The independent view has a lower exact-information floor, so its excess-loss difference is not raw predictive harm. Explicit same-event labels and unequal lengths outside the independent/irrelevant pair limit interpretation. Invalids remain; no dedicated confidence-inflation contrast or human mechanism is established. |
| **S12-SOURCE-RELIABILITY-1** | Does declared source accuracy constrain contextual updating, including ignoring uninformative reports? | **OPEN for graded reliability use; scoped trust failure observed (test, L443; 48 constructed histories in one law, Qwen direct/account readers and independent exact references).** An opposing report with declared chance accuracy harms the pooled forecast at the frozen margin. Several reliable-report excess-loss contrasts also show harm, but changing exact-information floors prevent equating them with raw predictive harm. Method difference is unresolved; the consumer supplies no reliability-by-cue interaction. Conditional vignettes, invalids and reused discovery histories remain explicit; no human trust or internal belief mechanism is identified. |
| **C01** | A coherent context model improves held-out prediction beyond the same facts listed, and a wrong context costs | **INCONCLUSIVE on the first half, REFUTED on the second (test, L239), full size and expanded.** Bundle minus facts +0.10 nats over 128 worlds and +0.09 over 256, the interval crossing zero both times; an incorrect bundle helps as much as the correct facts (+0.59 to +0.72 over no context) and irrelevant background helps by a third to a half of a nat, so the readers take the frame and not the content |
| **C02** | A reader uses a contextual prior without staying trapped by it: individuating records correct a misleading context | **REFUTED as a flat curve (test, L241): COUNTEREVIDENCE at 128 worlds, INCONCLUSIVE at 256.** Six records after a misleading prior move the direct log score -0.20 nats at 128 worlds and -0.08 with the interval crossing zero at 256, while the exact ruler climbs 0.13 to 0.16; the valid prior's curve is flat (0.00); a misleading prior helps at zero records as much as a valid one (+0.38 against +0.32); neither two-pass route helps; 0.44 of the mass stays on an option stated unavailable |
| **C03** | The readers choose evidence by its expected information about the maker (active reading) | **COUNTEREVIDENCE (test, L246), 204 usable worlds of 256.** The redundant probe is chosen 0.78 of the time and the informative one 0.08, half of every pick going to the first listed; 8 percent of the exact selector's expected gain is captured, a quarter below a random pick; the realized gains are flat at this size |
| **R01-S5** | The reader chooses the evidence route by its exact information about the hidden future choice, beyond a random selector | **NARROWED; the initial fluency explanation is REJECTED (test, L270, L300, L311, L327).** The initial 159-world result was +0.11 nats over random; −0.05 against always taking the easiest-rendered route, which is the action record in every world and the most informative in three of four; the reader's departures from it are unrelated to which route is best (27 against 28 percent). Second contract with per-world description rendering (L300): the easiest description is the note in every world, the readers take it a quarter of the time, prefer the action record, and capture +0.06 over random and +0.10 over always-easiest, tracking 0.36 against 0.26. Ease crossed inside a route type under a validated ruler (L311): the description rendered harder (mid-dots) is taken MORE, by 0.25 of probability on both readers (Qwen 0.40, SmolLM2 0.10), so the fluency policy is dead and anomaly attraction replaces it; the both-plain cell keeps the record-over-note preference at +0.08 over random; the archaic cross separates the confound: harder-but-not-deviant is ALSO taken more (−0.24 pooled; Qwen −0.42, SmolLM2 −0.07), so the attraction is difficulty's, not visual anomaly's (L327) |
| **R02-S5** | Stated reliance follows a record's exact information rather than its ease of reading, the two crossed by construction | **SUPPORTED for Qwen's information-sensitive stated reliance; ease interpretation REJECTED (test, L271, L281, L301, L310, L314, L327).** The initial 256-world quantity result was confirmed on its reserve (+0.18 [+0.15, +0.20], L281); its ease arm was then unrealized. Reliance +0.16 for six records over two; −0.03 for the stilted rendering, which the reader's own token probabilities rate as the easier text (−2.82 against −3.07 per token), so the fluency contrast never existed. Second contract (L301): +0.07 on two readers; the ease ruler (mean per-token log probability) rates capitals and mid-dotted text as easier than the plain record, so the ease arm cannot be realized under it. Under the validated ruler (L310) with the capitals realized in every world (L314): Qwen +0.15 for six records over two and −0.03 for plain against capitals (the harder text relied on MORE); SmolLM2 flat on both (−0.01, +0.01); the fluency account is dead on both readers and the quantity effect is the Qwen family's; at equal rendered length the effect follows information (+0.075 [+0.066, +0.084]) and not length (−0.003 [−0.011, +0.004]), the padded six matching the two (L327) |
| **R05-S5** | Along the evidence stream the reader's stated confidence tracks the exact information the stream carries | **VALID_NULL (test, L329), 192 world-series per reader, five cuts each.** Pooled slope agreement +0.012 [−0.001, +0.026] against the analytic half floor; Qwen +0.034 [+0.001, +0.069], under the band; SmolLM2 −0.009 [−0.044, +0.022]; ECE 0.316, the larger reader mostly sure (0.55 of its confidence mass) and worst calibrated (0.414): the J03-S5 one-cut fact in series form, and confidence is not an information meter in these readers |
| **R03-S5** | Worked demonstrations of choosing the diagnostic route transfer as expertise (used where diagnostic) rather than familiarization (used wherever shown) | **FAMILIARIZATION (test, L272), 256 worlds.** Three demonstrations raise the route's use to 100 percent and three misleading ones lower it to 0 in every world, the same where the route is worthless as where it is diagnostic (interaction −0.02 [−0.06, +0.02]); calibration unchanged; on two readers 1.00 and 0.01 to 0.02 with the interaction −0.01 (L302) |
| **R04-S5** | The reader buys forensic access when its expected information justifies the cost and declines it otherwise | **NO POLICY (test, L273), 256 worlds.** Buys in 48 percent of worlds with AUROC 0.54 to the exact gain; net gain per cost −0.24 against −0.18 for a coin flip and 0 for never buying; the step never pays on this construction, so only the decline side was tested. Second contract, the step paying in a third of worlds (L303): two readers buy in 0.58 of worlds whether it pays or not (AUROC 0.50), and the exact policy realizes the least gain because the bought evidence is not used |
| **HH-25** | Reliable maker context is especially useful after an initial artifact/self prior has formed, during maker differentiation | **OPEN for differentiation order (test, L195, L209, L211, L213, L214).** Ordering observations stand: the record-reading reader drops 0.67 to 0.40 when the question precedes the record, biography trades at parity with a six-choice record in both directions, and the late-fusion ruler fails on a second domain too (L229). The easy updating gate failed. Recall does not establish functional evidence use, so the recall split cannot isolate weighing from attention or comprehension. The stored readout follows an outsider's wish at 40/48, and an explicitly ignorant outsider's wish at 45/47 (L231). The re-run with every generation persisted and a parser-free likelihood readout (L252) keeps the numbers, 0.79 and 0.92 hint-following, with refusals and contamination small and separated, so the override is the readers' and not the parser's; what no readout of the answer separates is belief adoption from compliance, which stays open |

**What the table says.** Supplied assertions can dominate these model readers even when
the artifact contains readable contrary evidence. The verified wish override persists
under a parser-free readout, so the answer shift is real, while belief adoption and
compliance remain unseparated (G167, HH-25). On the tested context constructions, coherent
bundles do not establish an advantage over listed facts, added records fail to correct
misleading priors, and evidence selection does not generally follow available information
(C01 to C03). The complete current-reader structural blocks likewise do not isolate a
general truth-sensitive benefit: false and irrelevant framing can improve the same-record
score, and order, rereading and unchanged repetition offer strong alternative routes.
Added records improve the second false-frame comparison, while correct-frame modal
agreement worsens there. Invalid outputs, repeat variation and zero-support losses
limit this descriptive evidence of access and correction (S12-CONTEXT-1, L412/L419).
Organizing an identical projection of retrieved human-record facts changes this
likelihood reader's forecast. Linked facts improve both proper losses over raw facts
and repetition at equal primary token length, but no memory performs better on
calibration and reserve. Misassociated facts also improve over raw, and padding
changes the comparison. These controls leave a scoped rendering advantage without
isolating a general benefit of correct memory organization. One source component
per partition, exposed records and mostly identical projected views prevent population
or replication claims. The original collapsed comparison remains void; the earlier
unequal-length correction is a different instrument. Independent memory and the
paired elicitation comparison remain unavailable (S13-CONTEXT-MEMORY, L455/L456/L460).
Explicit access to an earlier answer can preserve a useful forecast or carry a wrong
one forward. The complete saved-reply cells compare identical later snapshots and
retain unchanged and length-matched irrelevant controls. The within-history crossing
removes the frame/history confound of the smaller diagnostic. Discovery remains
unresolved, while a prospectively reserved roster establishes a larger saved-reply
penalty under a false frame than a true one at the declared margin. This is an
explicit saved-text effect in the same law and reader, not hidden persistence.
Invalid replies and missing probability support remain part of the comparison;
the original diagnostic interaction does not subtract unchanged or irrelevant
control movement (S12-REVISION-1, L433/L435/L439/L450). The separately commissioned
discovery reanalysis subtracts both controls and retains positive descriptive
false-frame penalties. That new within-law estimand narrows the generic-movement
explanation without replacing the original primaries or establishing general
selective correction (S13-REVISION-CONTROLS, L453). Crossing the stated confidence and
claimed ownership of standardized earlier predictions likewise leaves the frozen
comparisons unresolved at their declared margin. The content contrast favors a
correct initial modal prediction descriptively, but does not clear the harm margin;
pooled diagnostic and irrelevant updates cannot identify selective correction
(S12-ATTRIBUTED-ANSWER-1, L440). Repeated-report and independent-observation
loss contrasts also remain unresolved at their frozen margin, while account-based
reading improves the pooled comparison. Independent evidence lowers the exact
information floor, so increased excess loss cannot be read as raw predictive harm.
These comparisons do not identify confidence inflation from counting a common cause
more than once (S12-COMMON-CAUSE-1, L441). Declaring a source uninformative does
not protect the tested reader from a harmful opposing report. Reliable reports
also leave a larger gap from some better-informed references, but that gap is
not itself raw predictive harm. Without a reliability interaction, these
conditional-channel comparisons do not establish how faithfully graded source
accuracy governs updating (S12-SOURCE-RELIABILITY-1, L443). These are scoped
behavior results, not a demonstrated human updating mechanism.

The selection and reliance controls narrow earlier explanations. Route preferences do
not follow ease as first proposed; the archaic rendering separates difficulty attraction
from visible anomaly (R01-S5, L327). In the Qwen reader, stated reliance follows information
when length is held constant, while length itself adds no established effect. The second
reader does not share the benefit (R02-S5). Demonstrations can produce route following
without sensitivity to diagnosticity, and the forensic purchase rule does not track its
available value (R03-S5, R04-S5).

The confidence-series instrument exists. Its pooled tracking of exact information does
not clear the declared band, and the larger reader is particularly overconfident on this
construction (R05-S5, L329). The additional value of the whole trajectory over its endpoint
remains untested (HH-9). Context persistence, differentiation order, process uptake
before value appraisal, and selective uptake through attention remain human hypotheses
(HH-SELECTIVE-ATTENTION). The disgust account adds a trigger whose shape social cognition research
supports, a decision the reader cannot fit into any goal it can model, a protective act that
perception research contests in its attentional form, and a release through humility and shared
goals that contact research favors; uptake gated by the source's highest goal remains a
constructed-world proposal whose tests have run but are not yet read (HH-DISGUST-GATE,
HH-DISGUST-POLICY, HH-TOP-GOAL-UPTAKE). Attention itself is held to mix a pull toward falling
prediction error, capture by drives or by learned value, and a part directed by expected preference
satisfaction, and nothing here yet separates them (HH-ATTENTION-SOURCES). Reversed choices are held
to come in an audited kind that carries the higher goal and a near-tie kind that does not, with
opposite timing (HH-REVERSAL-KINDS). Attention is held to be the corrector that allocates trust,
the precision placed on each signal, with salience and control as the framework's separate parts
(HH-ATTENTION-TRUST). The matched human menu-event comparison establishes no increase
in next-menu hover count after a failed suggestion, and its latency comparison is unresolved.
That scoped null does not measure internal trust. No model result licenses their internal
psychological interpretation. Confidence: one bad test away for these scoped model and
human process measurements;
instrument-dead for the collapsed memory comparison; untested, logic only for the
human mechanisms and the endpoint comparison.

**Familiarity, examination and trust after mistakes**

> indicative of confusion, processing time

> Familiarity often wins the choice [...] because it resolves more quickly, and [vision] moves to wherever surprise is decreasing the fastest

*Curator walkthrough, 2026-10-18, about 09:15 PDT, answering the twelve analyst questions; filed at the October 18 daily integration. Excerpts and marked lexical repairs are preserved from the [filing source](../design/archive/SOUNDING_LINE_THEORY_FILING_2026-10-18.md).*

The curator distinguishes processing difficulty from choosing an option and proposes attention toward rapidly resolving surprise. A hover marker records neither gaze nor all exposure. The trust account below treats each error as evidence, without treating the writing-log readout as internal trust.

> it should move with each mistake. Everything gives evidence. Surprising mistakes are the most notable. Expected mistakes [...] you just fit that into how to use the tool properly

*Curator walkthrough, 2026-10-18, about 09:15 PDT, answering the twelve analyst questions; filed at the October 18 daily integration. Excerpts and marked lexical repairs are preserved from the [filing source](../design/archive/SOUNDING_LINE_THEORY_FILING_2026-10-18.md).*

**Literature vocabulary, analyst handoff.** The following explanations retain the supplied analyst attribution. Linked sources were requested; inaccessible papers and uninspected full texts are **SNIPPET**, not independently verified findings in this pass.
- **Trial-wise trust updating**: measures trust after successive interactions; the inspected abstract reports larger effects of failures than successes ([source](https://doi.org/10.1177/00187208211034716), READ, abstract only).
- **Bayesian trust dynamics**: models changing trust through sequential evidence accumulation ([source](https://doi.org/10.1007/s12369-020-00703-3), SNIPPET).
- **Error expectancy**: distinguishes surprising easy-item failures from expected difficulty ([source](https://doi.org/10.1518/001872006777724408), SNIPPET).
- **Functional specificity**: distinguishes trust in different functions of the same tool ([source](https://doi.org/10.1518/hfes.46.1.50_30392), SNIPPET).

The table separates the proposed claim from its evidence and scope.

| # | Hypothesis | Status and evidence |
|---|---|---|
| **G215** | Out-of-repertoire options attract examination without acceptance | **OPEN (test, S15-DRIVE-D32-CANONICAL).** Human offer records and exact fitted readout: the corrected acceptance primary is marginal. The original examination extension is null and its declined-option secondary remains source-held; the corrected primary does not repair those outputs. |
| **G225** | Avoidance of similar options after a model letdown becomes narrower over sessions | **SUPPORTED as a scoped association (test, S15-WEEK-D38-CANONICAL-1018).** Human writing records and exact program: the canonical primary is positive on nine supported writers and its repeated outcome reference has no declared bias flag. The original matched own-failure extension is null, not evidence of a model-specific mechanism; fear, regret and causal learning remain unidentified. |

**What the table says.** The corrected records support a narrow avoidance association, but not a general psychological account of trust. A failed suggestion does not produce a resolved next-menu hover increase, and source-held examination outputs cannot settle what was seen or considered. Confidence: one bad test away for these human process associations; untested, logic only for internal trust and attention.

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

> [...] Aesthetics, no, aesthetics does create interest, because it's a, it's a promise of order.

*Curator's ToMpathy assessment walkthrough, 2026-10-13 (16:29 PDT), in the project's assessment thread; filed 2026-10-14. Contiguous excerpt with marked omissions; transcription repairs listed in the handoff.*

> You know, that prediction isn't that ridiculous. I'm not sure I would have made it myself, but
> "aesthetics is what attention does when set points are met." I think I would treat that as saying
> that the explore/exploit trade-off is more weighted towards explore, which encourages [...]
> exploration.

*Curator's walkthrough answering the assessment thread, 2026-10-14 (received 10:30 PDT in the project's errata thread); filed 2026-10-14. Contiguous excerpt with a marked omission; transcription repairs listed in the handoff.*

The quoted prediction was an analyst's, made in the assessment thread; the curator reads it as a
claim about the balance between exploring and exploiting. Active inference supplies the mechanism.
A policy's value adds expected preference satisfaction to expected information gain, so when no
option differs in the first, choice follows the second
([Friston et al., 2015](https://doi.org/10.1080/17588928.2015.1020053), abstract read). Art made
under deprivation, in prisons and camps, is the standing counterexample the claim has to absorb.

The first part sharpens "ordered but unexplained" as an abstention state between comprehension and
error. The suggestion that this may define all aesthetics remains an open extension, since
aesthetics can also involve fluency, attraction, convention, affect, and successful recognition.

**Falling surprise, then compression progress** *(2026-10-16)*:

> Ooh, I really like compression progress more than I like falling surprise. That's really cool.
> Going with "that's what aesthetics is", that's interesting, because does pleasure attract your
> attention? I'm not necessarily sure that's true. Oh, it probably does. God damn it. Of course your
> eyes flow towards food. Jesus. But no, that's also just. No, no, no [...]. That's also just
> tracking you towards things that have incredibly easy-to-solve relationships to set points. It is
> the fastest falling of the compression, because it's just the piece that gets auto-solved. You
> don't even notice it. You just look towards food because your SEEKING network auto-checks food.
> Assuming you're hungry.

*Curator's walkthrough of the analyst's 16 October theory record, 2026-10-16 (12:57 PDT), in the project's theory and analyst thread; filed 2026-10-16. Contiguous excerpt with marked omissions; transcription repairs listed in the handoff.*

The morning statement in §4 held that a reader is aesthetically pulled toward regions of falling
surprise and that this is what aesthetics is; by the afternoon the curator preferred compression
progress. The evidence splits the quantity into three terms on three timescales. Hedonic tone is
error reduced faster than expected, on the timescale of inference. Pleasure from easy processing
peaks "when processing is expected to be difficult, yet turns out to be easy"
([Reber, Schwarz & Winkielman, 2004](https://pages.ucsd.edu/~pwinkielman/reber-schwarz-winkielman-beauty-PSPR-2004.pdf),
read), ease is felt only "if it is discrepant from their expected fluency"
([Graf & Landwehr, 2015](https://docenti.unimc.it/ivana.bianchi/teaching/2023/28153/files/articoli/pla-model_pleasure-and-interest-aesthetic-model),
read), and feeling good comes from "reducing error at a faster than expected rate"
([Kiverstein, Miller & Rietveld, 2019](https://pure.uva.nl/ws/files/37405887/Kiverstein2019_Article_TheFeelingOfGripNoveltyErrorDy.pdf),
read). Free energy falls during fast inference too, and valence has been defined as its negative
rate of change
([Joffily & Coricelli, 2013](https://journals.plos.org/ploscompbiol/article?id=10.1371/journal.pcbi.1003094),
read), which fits the auto-solved case. Interest is compression progress, on the timescale of
learning, the first derivative of how compressible the observed history has become. An item solved
at once is beauty in Schmidhuber's terms rather than progress, and "what's beautiful is not
necessarily interesting" ([Schmidhuber, 2009](https://arxiv.org/abs/0812.4360), read). Liking of
music is an inverted U in surprisal and uncertainty
([Gold et al., 2019](https://www.jneurosci.org/content/39/47/9397), read), the shape an interest
term predicts.

The third term is extrinsic value, the pull of bodily and social set points. Active inference splits
a policy's value into extrinsic value, outcomes preferred a priori, and epistemic value, the
expected information gain ([Friston et al., 2015](https://doi.org/10.1080/17588928.2015.1020053),
read), and Schmidhuber set aside "rewards for achieving prewired target values" as not what
curiosity is about. The curator placed looking toward food under the fastest-falling compression;
the analyst places it in the extrinsic term instead. Fasted women looked longer at food, and once
fed the bias vanished in normal-weight women and persisted in obese women
([Castellanos et al., 2009](https://www.nature.com/articles/ijo2009138), read), a trace of need
state and learned value rather than of learnability. Folding the food case into progress would erase
the line between the pull of bodily and social set points and aesthetics, which is epistemic. An
active inference account of art states the boundary condition the earlier prediction stated, that
aesthetic experience arises "when more primary needs are satisfied" and "prior preferences recede
into the background"
([Van de Cruys, Frascaroli & Friston, 2024](https://discovery.ucl.ac.uk/id/eprint/10184831/1/van-de-cruys-et-al-2023-order-and-change-in-art-towards-an-active-inference-account-of-aesthetic-experience.pdf),
read). The terms make opposite predictions in two places. Pleasure should follow the surprise of
ease, with no leftover effect of ease itself, and hungry people's attention to one repeated food
image should fade if it tracks progress but last until they eat if it tracks extrinsic value. Which
drive's reward compression progress is, PLAY's on the analyst's proposal, is in
[`THREE_COGNITIVE_LAYERS.md`](THREE_COGNITIVE_LAYERS.md) §1.

**One scale: how fast things come apart** *(2026-10-17)*:

> I feel like pleasure is also compressing information. It's just rapidly finding an easy path to a
> solution.

> Is beauty just the mix of interesting and pleasurable? Like, it's the rapidly disassembling, but
> it's also the kind of rapidly disassembling that's easy to find. [...] Yeah, I think it is that
> rapid disassembling. Maybe that is what beauty is, the most rapid of disassemblies.

> But with landscapes, does the landscape have opportunity? Is there variance in its offerings, in a
> way that gestures toward order, in a way that can be harnessed and understood? That is what beauty
> is. It's a pretty reasonable guess, honestly. It explains the oddities, like how people can
> describe the sudden appearance of a jaguar as beautiful [...]. Hitting beauty as an artist is more
> difficult, and is also in the eye of the beholder.

*Curator's answers to the analyst's 17 October discussion questions, 2026-10-17 (07:52 PDT), in the project's theory and analyst thread; filed 2026-10-17. Separate excerpts with marked omissions; transcription repairs listed in the handoff.*

> I think it's one scale, how fast things come apart. The beauty is the almost instant resolution;
> that's how I would almost want it. It's the pleasure piece. It's seeing a clear path where you can
> align your active states to a reward channel instantly [...]. There's a pleasure element to it,
> maybe. [...] Regardless, all three of those seem like the same thing to me. It just seems one
> scale.

> Interest is disassembly, and beauty is the rapid disassembly. [...] I actually am not sure I agree
> that what's beautiful is not necessarily interesting. I think my model would be that what's
> beautiful is something that was ever so briefly interesting, just for a second, and then at that
> moment was compressed. At some point it was interesting to you, and now you're seeing a little bit
> more of it, or in a new way, or something like that.

> The candy example is annoyingly good. [...] Perhaps something that's beautiful has to also have a
> total lack of any kind of translation layer, no teaching layer, whether intended to propagandize
> or otherwise. [...] If it is raw and stark in such a way that it has not been formatted for you,
> or for you specifically, but rather it is a natural occurrence of a sufficiently interesting
> thing, or it is the kind of raw, true [thing] that would effectively be a natural occurrence out
> of a human, just the autocomplete, sort of, on its own. A flawless alignment, as everything kind
> of fits into place. Maybe that's beauty. It's a starkness combined with that. Interesting. I'm
> less confident about these as we go.

*Curator's answers to the analyst's 17 October second-round questions and scorecard, 2026-10-17 (10:15 PDT), in the project's theory and analyst thread; filed 2026-10-17. Separate excerpts with marked omissions; transcription repairs listed in the handoff.*

The curator puts beauty, interest and pleasure on one scale, the speed at which a thing comes apart
into an understood structure, with interest the slower process and beauty the near-instant one, and
he rejects the analyst's three-term split for it. The closest findings support his link between
resolution and liking. Having an insight, and its intensity, "predicted subsequent gains in liking"
([Muth & Carbon, 2013](https://doi.org/10.1016/j.actpsy.2013.05.001), read); the affect of an aha
follows "the concomitant surprising fluency gain" of a sudden solution
([Topolinski & Reber, 2010](https://doi.org/10.1177/0963721410388803), read); and valence has been
defined formally as the rate at which free energy falls
([Joffily & Coricelli, 2013](https://doi.org/10.1371/journal.pcbi.1003094), read), a speed. The
nearest formal precedent places the terms the other way round. Schmidhuber puts beauty on
compressibility and interest on its first derivative, the progress
([Schmidhuber, 2009](https://doi.org/10.1007/978-3-642-02565-5_4), read), where the curator puts
beauty on fast progress, and his "ever so briefly interesting, just for a second, and then at that
moment was compressed" is the bridge, beauty as progress completed in a moment.

Two findings resist one scale, and a third fits half of it. Across 900 images beauty tracked
pleasure closely, r = 0.75 ([Brielmann & Pelli, 2019](https://doi.org/10.3389/fpsyg.2019.02420),
read), which fits his pleasure piece; but interest and pleasantness were "essentially unrelated",
and novelty and complexity raised interest while lowering pleasantness
([Turner & Silvia, 2006](https://doi.org/10.1037/1528-3542.6.4.670), read); and beauty from fluency,
as in symmetry and prototypes, has no interest phase to complete
([Reber, Schwarz & Winkielman, 2004](https://doi.org/10.1207/s15327957pspr0804_3), read). His
account fits beauty that arrives as insight better than beauty that arrives as ease, and no study
was found that measures the speed of resolution against beauty, the test the scale implies.

The landscape answer has a home in environmental psychology, whose preference matrix rates scenes on
coherence, legibility, complexity and mystery (Kaplan & Kaplan, 1989, snippet); coherence,
legibility and complexity predicted preference for urban parks in a 2025 study
([Pardela, Beck & Lis, 2025](https://doi.org/10.3097/LO.2025.1133), abstract read), and the
curator's variance that gestures toward order is, on the analyst's reading, complexity held within
coherence. The condition of no translation layer meets Kant, for whom pleasure in beauty "does not
depend on the subject's having a desire for the object" and charm or a governing concept makes the
judgment impure ([Ginsborg, 2022](https://plato.stanford.edu/entries/kant-aesthetics/), read). Two
findings complicate it. Strong sensory pleasure, candy included, can be felt as beautiful
([Brielmann & Pelli, 2017](https://doi.org/10.1016/j.cub.2017.04.018), read), and removing the human
maker lowers ratings, since identical images scored lower when labeled computer-made
([Kirk et al., 2009](https://doi.org/10.1016/j.neuroimage.2008.10.009), read), while understanding
an artist's intent raised liking ([Jucker et al., 2014](https://doi.org/10.2190/EM.32.2.c), read).
The label and title findings favor intent without an ulterior purpose over the absence of intent,
which is close to his raw, true human autocomplete. Sounding Line card D36, commissioned on 17
October as exploratory, tests whether jokes are liked more when their punchlines resolve faster.

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

**What the reader wants to learn changes what is worth examining.** In the curator's Go
example, a better move can make the earlier move less useful for learning the game while
leaving it informative about the player. This changes the reader's reason to continue,
not what the maker's earlier goal was. Wanting to learn a technique, identify a maker,
recover a historical process, and assess a maker's values are different reader tasks.
Stopping may reflect limited relevance or cost rather than a complete reconstruction.
Later endorsement of a better move does not by itself show whether the maker considered
it earlier. The claim about earlier knowledge requires its own evidence.

**When no goal explains the artifact** *(2026-10-14)*:

> Can't find the top goal, what's the default? And I think you use context. At that point, you try
> to search for other sources of information to kind of weigh judgment. It's a really cheating way
> to answer, but, like, I'm imagining something like a person walking on their hands down the street
> in ice skates, and I can't imagine why someone would do that. The questions are, is this person
> just crazy? Are they kind of dumb? Are they doing something I don't understand? You can dismiss it
> and say weird for the sake of weird, which is a way of saying that their goals aren't unknowable,
> but they're so petty and unlikely to be well nested in higher hierarchical structures that it's
> not worth examining.

> Yeah, I think this is a weirdly phrased question. Everything's going to be gradients. I don't
> understand why there has to be a pre-assumption. That being said, I do think that there is an
> openness variable, like openness to experience. I think it would indicate the explore/exploit
> trade-off. I do wonder if the Big Five are going to show up somewhere in this? We're pretty deep in
> brain space, and [it] sure does feel like we'll find more of them showing up somewhere or another,
> and openness would deal with a lot of this. If you can't find the maker's top goal, that's one
> thing, but assuming you found the top goal already is certainly an option. You can just declare
> where you're at to be the peak, which is the weird-for-the-sake-of-weird shrug that people will
> make about the hand example I gave earlier. But someone with full openness to experience might sit
> and wonder why they're doing this and spend a while trying to calculate it.

*Curator's walkthrough answering the assessment thread, 2026-10-14 (received 10:30 PDT in the project's errata thread); filed 2026-10-14. Two contiguous excerpts; transcription repairs listed in the handoff.*

A reader with no goal that explains the decisions has two exits. It can forage for context, other
sources that might make the decisions cohere, or it can shrug, declaring its current level the peak
and filing what remains as weird for the sake of weird, goals that exist but sit too low and too
isolated to be worth nesting. The three questions about the skater are the divergence classes of
§6 asked of a whole maker, and the shrug is the decision to stop before the third is ruled out. How
long a reader searches is a graded dial, not a default. Openness to experience is the curator's
candidate, and dopamine-based personality theory ties openness to exploration
([DeYoung, 2013](https://www.frontiersin.org/journals/human-neuroscience/articles/10.3389/fnhum.2013.00762/full),
abstract read). The construct built for the stopping decision itself is need for cognitive closure,
the urge to reach an answer and keep it, and it underlies prejudice in several forms
([Roets & Van Hiel, 2011](https://www.psychologicalscience.org/journals/current-directions/0963721411424894/),
abstract read), which ties the shrug to epistemic disgust in §4.

Stopping is the calibration side. Graded attribution when evidence supports only that (§10), and a
**hard falsifier ends the inference outright**, the two-channel rule of §9.

| # | hypothesis | status |
|---|---|---|
| **HH-14** | Reader-reported interest correlates with unrecovered decisions | **OPEN, blocked on him.** Interest ratings on the fifteen read artifacts; an hour that turns the richest hypothesis source into data. Informs this file only, never ground truth |
| **HH-16** | "Ordered but unexplained" is effective complexity rather than entropy | **OPEN.** A real, formalisable target, and deprioritized as a global text summary by the program |
| **HH-AESTHETIC-TERMS** | Aesthetic response has three terms on three timescales, hedonic tone as error reduced faster than expected, interest as compression progress, and extrinsic value, the pull of bodily and social set points; aesthetic pull is the first two, and attention drawn by need, as to food when hungry, is the third | **OPEN.** Pleasure as better-than-expected ease, interest as compression progress, valence as the rate at which free energy falls, the split between extrinsic and epistemic value, and need-dependent attention to food each have support (lit, READ); the three-term split is the analyst's, and it departs from the curator's placement of looking at food under the fastest-falling compression; no project measurement separates the terms |
| **HH-ONE-SCALE** | Beauty, interest and pleasure lie on one scale, how fast a thing comes apart into an understood structure; interest is the disassembly and beauty the rapid one, so the beautiful was briefly interesting and then compressed | **OPEN for beauty as fast resolution; CONTESTED (lit) for one scale joining interest and pleasure.** The curator's account (2026-10-17), against the analyst's three-term split (HH-AESTHETIC-TERMS). Insight and its intensity predict gains in liking, aha affect follows a sudden gain in fluency, and valence can be defined as a rate (lit, READ); interest and pleasantness were unrelated in one series, and fluency-based beauty has no interest phase (lit, READ); no study found measures resolution speed against beauty; Sounding Line card D36 is a first, exploratory test |
| **HH-NO-TRANSLATION** | What is beautiful carries no translation layer, nothing formatted for the viewer or meant to teach or persuade, a natural occurrence or a maker's unforced autocomplete | **OPEN, the curator's tentative proposal.** Kant's disinterested and purpose-free beauty agrees (lit, READ); strong sensory pleasure can be felt as beautiful, removing the human maker lowers ratings, and grasping intent raises liking, so the label and title findings favor intent without an ulterior purpose over no intent (lit, READ); no project measurement |
| **HH-NO-TOP-GOAL** | When no goal explains an artifact's decisions, a reader either forages for context or stops by declaring its current level the peak, and a graded trait such as openness or need for closure sets how long it searches | **OPEN.** Openness relates to exploration and need for closure to prejudice (lit, READ); no project measurement |
| **S12-STOPPING-1** | Does a reader stop or buy evidence according to its declared purpose and cost? | **OPEN; primary uncertainty analysis unavailable (test, L442; 64 constructed discovery histories in one law, Qwen model reader and independent exact references).** All requested calls and descriptive replay are complete. Reader regret exceeds at least one constant policy in each purpose/cost stratum, with strong descriptive answer-order differences and retained invalids. The frozen consumer has no paired regret interval, so no formal benefit, harm or equivalence is established. Current forecasts do not test use after purchase; human interest is untested. |
| **lit** | Berlyne's collative variables support the interest claim | **REJECTED (READ).** The arousal theory is *"mostly abandoned"*; one fetch found this after fifteen searches had not |

**What the table says.** The interest account survived losing its supposed backing. The abandoned
arousal theory is replaced by a sharper formal target (effective complexity), and the live
opposing account, pleasure from processing ease, predicts the *opposite* correlation between
interest and recoverability, which is exactly what the blocked ratings test would adjudicate.
Splitting aesthetic response into pleasure at better-than-expected ease, interest as compression
progress and the extrinsic value of bodily and social set points may dissolve that opposition, since
fluency and interest accounts would then measure different terms, and the ratings test would need
pleasure and interest rated separately to show it (HH-AESTHETIC-TERMS). The curator holds the
opposite view, one scale of how fast things come apart, with beauty as interest resolved in a moment
(HH-ONE-SCALE), and he adds tentatively that beauty carries no layer formatted for the viewer
(HH-NO-TRANSLATION); the ratings test would separate the two accounts if it timed the resolution as
well as rating it.
The proposed relation between interest and unrecovered decisions also depends on the
reader's purpose: material informative about a maker may add little to a reader's present
learning task. Interest and stopping are consequently evidence about the reader as well
as the artifact. In a constructed task with explicit costs, this model reader's
choices do not yet establish useful stopping beyond constant policies and answer
position: the complete descriptive comparison retains invalids and lacks its primary
uncertainty interval. That result concerns an investigation decision, not human interest
or successful use of purchased evidence (S12-STOPPING-1, L442). Confidence: one bad test
away for the scoped model description; untested, logic only for the human interest
account, whose rating comparison remains blocked on curator ratings, and for the proposal that a
reader without an explaining goal forages or shrugs (HH-NO-TOP-GOAL), and for the three-term aesthetic
account (HH-AESTHETIC-TERMS) and the curator's one-scale account with its condition (HH-ONE-SCALE,
HH-NO-TRANSLATION).

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

**Divergence from the expert steps has few explanations** *(2026-10-13)*:

> First, we figured out that it seems like all divergences from expertise [...]. So if you have the
> steps that you're taking, you're following the policy, all divergences from that, not policy even,
> just a set sequence of steps. [...] All mistakes, all divergences from the expertise steps, are
> either a mistake in your policy mapping, or a context inaccuracy, or evidence of a decision made
> under attention, creating a vector for identifying a core value point. And I think that eats
> epistemic foraging, by which I mean you're taking a guess as to something that would give you a
> better outcome. And the tests, the epistemic foraging tests, are themselves decisions made under
> attention, creating new vectors.

*Curator's evening walkthrough after an in-person discussion, 2026-10-13 (19:02 PDT), in the project's errata thread; filed 2026-10-14. Contiguous excerpt with marked omissions; transcription repairs listed in the handoff.*

> I also want to note that how deep a reader can recover a maker's goals is not capped. All of this
> is probabilistic. What would end up happening is that you would try to infer larger goals, and then
> sometimes you would find things that don't fit, and you would infer those to be individually either
> mistakes, elements about the original creator, or, if there are enough of them, and more
> importantly, if they are an organizational structure that implies larger goals, they might be
> something that you are missing. Some larger picture that you have failed to put together.

*Curator's ToMpathy assessment walkthrough, 2026-10-13 (16:29 PDT), in the project's assessment thread; filed 2026-10-14. Contiguous excerpt; transcription repairs listed in the handoff.*

> Deviations also can indicate an unknown contextual limitation. I also am not convinced I've nailed
> all the deviations specifically [...].

*Curator's walkthrough answering the assessment thread, 2026-10-14 (received 10:30 PDT in the project's errata thread); filed 2026-10-14. Contiguous excerpt with a marked omission; transcription repairs listed in the handoff.*

> The thing is, I don't think there is noise in this process. Like, if everything is purposeful and
> there isn't noise to be had, all of the information is useful. If you think something is noise,
> you just don't understand it. You're missing context. Or you just don't understand a decision of
> some kind.

> Habit is its own class. I think expertise is intended repetition. Habit is all repetition. An
> example would be an artist with a tic in his elbow that later heals, but that irons in a set of
> painting habits that that artist then has to spend time unlearning.

> An exploratory probe is interesting because, as far as I can think about it, every example I can
> come up with of epistemic foraging in this context is all, almost all, trying to improve the
> product in some way. Like, you try something on the assumption and belief, given the inferences
> that you do, that you can do better than your plan in some way. And so you attend to the part that
> you think will make a difference. It's a very scientific-method style of epistemic foraging, and
> it's consistently what people do. People don't make it worse unless they believe that the act of
> making it worse will somehow make it better. [...] If you're actively making your painting worse,
> you're only doing it because it will make it better, or to make some kind of a statement. You
> know, Banksy shredding his picture is a humorous, not quite accurate, but humorous example.

*Curator's walkthrough of this handoff's decisions and questions, 2026-10-14 (12:22 PDT), in the project's errata thread; filed 2026-10-14. Separate excerpts with marked omissions; transcription repairs listed in the handoff.*

The governing rule above subtracts what the medium forces; these restatements classify what
remains. On the maker's side a divergence is a policy error, a belief about the context that was
wrong, habit, or a deliberate choice, and deliberate choices are where preference vectors live.
Habit is all repetition and expertise its intended part, so the class that matters for deviations
is unintended repetition, such as a style an old injury forced. Epistemic foraging is a deliberate
choice, and since nearly every probe aims at improving the work, a probe carries a preference
direction as well as a question; deliberate worsening serves a higher goal, such as a statement.
[`DECISION_TRACES.md`](DECISION_TRACES.md) §1 already files foraging as deliberate. The curator
holds that nothing is noise and that apparent noise is missing context. The reader's side has its
own explanations, a wrong goal, a missing larger structure, or a limitation on the maker that the
reader does not know about, which the curator names directly. A cluster of divergences that the
maker-side classes cannot absorb is evidence for them, and the curator holds the list open. His
three questions about an unexplained maker in §5, crazy, dumb, or doing something the reader does
not understand, ask the same classification of a whole maker.

Each class has a long literature. Infants of fourteen months copied an unusual head action far more
often when the actor's hands were free than when a blanket occupied them, 69 against 21 percent
([Gergely, Bekkering & Király, 2002](https://doi.org/10.1038/415755a), read), which ties
classification directly to uptake. Preference inference improves when false beliefs and
inconsistency are modeled ([Evans, Stuhlmüller & Goodman, 2016](https://arxiv.org/abs/1512.05832),
abstract read), but a policy cannot be uniquely split into planner and reward without normative
assumptions ([Armstrong & Mindermann, 2018](https://arxiv.org/abs/1712.05812), abstract read), which
is the split between policy error and preference. Human error research separates unintended errors
from intended violations, and its situational violations are deliberate departures driven by context
rather than preference (Reason, 1990, through a summary read). Epistemic actions look superfluous to
a pragmatic model, and expert players make more of them
([Kirsh & Maglio, 1994](https://adrenaline.ucsd.edu/kirsh/Articles/CogsciJournal/DistinguishingEpi_prag.pdf),
read). The three explanations people give for anyone who disagrees with them, uninformed, irrational
or biased, have the same shape, which is why the reference steps must be stated whenever a divergence
is classified ([Ross & Ward, 1996](https://en.wikipedia.org/wiki/Na%C3%AFve_realism_(psychology)),
through a summary read). Decision research contests the no-noise position. Much of the
variability in human choices comes from imprecise inference (Drugowitsch et al., 2016, snippet),
and people add decision noise on purpose, as random exploration, when more choices remain
([Wilson et al., 2014](https://experts.arizona.edu/en/publications/humans-use-directed-and-random-exploration-to-solve-the-explore-e/),
abstract read). A caused mark can still carry no preference information, so the classifier needs
a place for it whatever it is called.

**Pervasive or local: telling an autocompleted branch** *(2026-10-17)*:

> A reader would tell a branch she never saw from one she saw and declined because it would kind of
> suffuse all of the decisions that are similar to it. As characters got into situations, you could
> find the autocomplete yourself. There'd be characters that got into situations that were fearful,
> that would give them the opportunity to be fearful, and you would expect them to be fearful. And
> that would give you the background implication, piece by piece. You'd see it across everything.
> [...] Attention is limited, and so it's the limited nature of attention that helps you here more
> than anything. The biggest thing to tell a branch that has been autocompleted is the pervasiveness
> of similar-looking decisions. Other characters being fearful imply that this character being
> fearful is about the author, not about the character. It wasn't something they were attending to;
> it was something that they do automatically without realizing it.

*Curator's answers to the analyst's 17 October second-round questions and scorecard, 2026-10-17 (10:15 PDT), in the project's theory and analyst thread; filed 2026-10-17. Contiguous excerpt with a marked omission; transcription repairs listed in the handoff.*

Attribution theory has the instrument the curator describes. Kelley's covariation model reads where
the cause of a behavior sits from three facts, consensus (whether others respond the same way to the
same thing), distinctiveness (whether this person responds that way only to this thing) and
consistency (whether the response recurs whenever the thing is presented), and low consensus, low
distinctiveness and high consistency locate the cause in the person (Kelley, 1973, snippet;
[McArthur, 1972](https://doi.org/10.1037/h0032602), read). Other characters being fearful is low
distinctiveness; the author is the person, and characters, scene types and works are the entities
and occasions. The research pass adds one fact and one correction. The test needs consensus, what
other authors' characters do in matched scenes, or genre conventions pass as authors' traits, and
observers underuse it too, since in McArthur's data consensus explained 6.25 percent of the variance
in person attributions against 21.72 percent for distinctiveness. And covariation locates a cause
and says how general and stable it is, while judgments of control rest on a different fact, the
contingency of one's actions
([Van Overwalle & Heylighen, 1995](https://doi.org/10.1002/ejsp.2420250407), read).

Pervasiveness therefore shows that a choice belongs to the author, not that it was automatic. A
deliberate global policy is pervasive and attended, as Poe claimed of a poem in which no point was
"referrible either to accident or intuition"
([Poe, 1846](https://www.eapoe.org/works/essays/philcomp.htm), read), and the automatic cases the
habit and fear literatures describe can stay local, a habit being a response cued by a stable
context and insensitive to current goals
([Wood & Neal, 2007](https://doi.org/10.1037/0033-295X.114.4.843), read) and a one-shot fear one
that generalizes along similarity to the scene that taught it
([Dymond et al., 2015](https://doi.org/10.1016/j.beth.2014.10.001), read). The analyst's restatement
keeps the curator's test and adds the missing half. An autocompleted branch shows low consensus, low
distinctiveness and high consistency, which places it in the author, and it is insensitive to what
it should track, flat against the character's traits and the threat's size, fast, and seldom
revised. Computational literary studies found author and character signals "fused in novels"
([Bamman, Underwood & Smith, 2014](https://doi.org/10.3115/v1/P14-1035), read), so the separation
does not come free. Sounding Line cards D30 and D31 apply the test to writers' own markers and to
fiction's characters, and Ghost study N14 scores the curator's rule against the restated one where
the mechanisms are known.

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
| **HH-DIVERGENCE-CLASSES** | Divergences from the expert steps sort into policy error, context inaccuracy, habit and deliberate choice on the maker's side, with epistemic foraging inside deliberate choice and aimed mostly at improvement, and into a wrong goal, missing structure or an unknown contextual limitation on the reader's side; only deliberate choices carry preference vectors, the list is held open, and the curator holds that nothing is noise | **OPEN.** Each class has literature (lit, READ and SNIPPET); the split between policy error and preference is not identifiable from behavior alone without normative assumptions (lit, READ); decision research reports variability from imprecise inference and deliberate random exploration (lit, READ and SNIPPET), against the no-noise position. No project measurement separates the classes. The residual-direction primary and stricter extension are marginal; the directly linked model-correction variant is also marginal. No hidden goal or noise conclusion follows, with failed planted sensitivity and the broader own-text correction question retained (test, S15-DRIVE-W1-1017, D34, D34 extension and D34.v1; human CoAuthor process records, fitted handling readers and frozen semantic vectors). |
| **HH-MENU-EXPOSURE** | Position differences in recorded examination separate unseen from declined alternatives | **OPEN.** The pooled first-minus-fifth hover comparison is null; keyboard/selection markers, hypothetical defaults and bounds on latent exposure remain separate. Unhovered is not unexposed (test, S15-DRIVE-W1-D6-1017; human CoAuthor interface-event records, exact program). No attention or preference mechanism is identified. |
| **HH-PERVASIVENESS** | A branch a maker never draws because it was autocompleted away shows as the pervasiveness of similar decisions across the maker's work, other characters fearful where this one is, so it is about the author; restated, an autocompleted branch shows low consensus, low distinctiveness and high consistency and is also insensitive to what it should track, while pervasiveness alone shows only that the choice is the author's | **OPEN.** The curator's test (2026-10-17) with the analyst's restatement. Kelley's covariation model and its patterns (lit, READ and SNIPPET); observers underuse consensus, and control judgments rest on contingency rather than covariation (lit, READ); deliberate global policies are pervasive and attended, and cue-bound habits and one-shot fears can be local (lit, READ); Sounding Line cards D30 and D31 and Ghost study N14 are commissioned. The own-marker primary is marginal and its stricter marker-count extension is positive, but a positive writer-label shuffle leaves person location and automaticity unestablished (test, S15-DRIVE-W1-1017-1550, D30; human CoAuthor typed-text logs, exact marker classification and fitted pause models). The completed crossed model is unresolved and all three same-row own-history advantages are null; the shared-word variant is VOID before fitting. These supported-population comparisons do not identify automaticity, and the fiction question remains unrun (test, S15-DRIVE-D30-CROSSED-WEEK-1019; S15-DRIVE-D30-PAIRED-FIXED-1019; S15-DRIVE-D30-SHARED-SUPPORT-1019). |

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
is what the validation-first order bought, twice. The divergence classes turn the subtraction rule
into a classifier, useful only if the deliberate class can be recovered without absorbing habit,
unexplained variation or the reader's own errors (HH-DIVERGENCE-CLASSES). The curator's
pervasiveness test supplies a classifier for the habit class, valid for where a choice sits and
needing a second check, insensitivity to what the choice should track, before it can call the choice
automatic (HH-PERVASIVENESS). The own-marker timing association also survives writer-label
shuffling, and the paired history comparisons find no own-history advantage on their supported rows. The crossed primary remains unresolved and the fixed shared vocabulary lacks support, so neither person location nor automaticity is established. Marginal residual-direction
and correction-cohesion comparisons do not classify an omitted goal, and inadequate planted
sensitivity prevents interpreting the remainder as noise (HH-DIVERGENCE-CLASSES). A null
position contrast in hover records does not identify which options were actually examined;
latent exposure remains unidentified (HH-MENU-EXPOSURE). Confidence: the partition is one bad test
away; the ruler validation is one bad test away and constructed-world only; the text arc
(null at short form, separation at long form) is one bad test away as a set, one corpus
family deep with its fabrication warning attached; the ceiling import is replicated in its
home field; the scoped process comparisons are one bad test away; the general
divergence classification, person-location and automaticity mechanisms remain untested, logic only.

**Communal fluency and personal departures**

> priming is just as messy as expertise [...] recursive, collective, shared neural [weighting]

> fluency is communal, and the variation of that fluency is hers [...] if you pull out culture, it would remain

> you give wider error bars around what culture drives you to do, and then deviations are seen as more indicative

> hearing other words over time counts as practice [...] built-in expertise from culture, there's a cultural net there

*Curator walkthrough, 2026-10-18, about 09:15 PDT, answering the twelve analyst questions; filed at the October 18 daily integration. Excerpts and marked lexical repairs are preserved from the [filing source](../design/archive/SOUNDING_LINE_THEORY_FILING_2026-10-18.md).*

On the curator's account, hearing and reading train a communal repertoire; the personal signal is a departure from that repertoire. A culture can make conduct unsurprising without erasing the person. Neither a shared history effect nor a successful identity classifier alone identifies the preference behind the departure.

**Literature vocabulary, analyst handoff.** The following explanations retain the supplied analyst attribution. Linked sources were requested; inaccessible papers and uninspected full texts are **SNIPPET**, not independently verified findings in this pass.
- **Comprehension-to-production priming**: earlier hearing can influence later production, the proposed sense in which hearing is practice ([source](https://doi.org/10.1016/j.cognition.2006.07.003), SNIPPET).
- **Matched comprehension and production priming**: compares the two routes under matched materials ([source](https://doi.org/10.1016/j.cognition.2014.04.002), SNIPPET).
- **Lexical repetition priming**: connects prior hearing or saying to later word production ([source](https://doi.org/10.1080/01690965.2013.848989), SNIPPET).
- **Correspondent inference**: infers a disposition from conduct that alternatives and role demands do not explain ([source](https://doi.org/10.1016/S0065-2601%2808%2960107-0), SNIPPET).
- **Out-of-role inference**: uses departures from an assigned role as evidence about a person ([source](https://doi.org/10.1037/h0048514), SNIPPET).
- **Discounting and augmentation**: downweights a cause when alternatives suffice and upweights it when opposing pressures are present ([source](https://doi.org/10.1037/h0034225), SNIPPET).
- **Situational strength**: describes how constraints reduce behavioral variation ([source](https://doi.org/10.1177/0149206309349309), SNIPPET).
- **Cultural tightness**: concerns strong norms and low tolerance of departures ([source](https://doi.org/10.1126/science.1197754), SNIPPET).
- **Behavioral dispersion**: operationalizes one cultural-tightness comparison through cross-person spread ([source](https://doi.org/10.1177/0022022114563611), SNIPPET).
- **Correspondence bias**: names insufficient discounting of situational causes ([source](https://doi.org/10.1037/0033-2909.117.1.21), SNIPPET).

The table separates the proposed claim from its evidence and scope.

| # | Hypothesis | Status and evidence |
|---|---|---|
| **G203** | Fluent production draws on shared experience, while a writer's deviations identify her | **OPEN (test, S15-DRIVE-W1-1017-1702; S15-DRIVE-D33-SUPPORTED-1018).** Human writing logs, fitted history and pause readers: the own-history association and shuffled-history association are positive on different support; the equal-sized donor comparison is marginal. The supported-match successor is INVALID before fitting because two evaluation writers lack calibration support. The calibration-supported adapter passes constructed validation, but its corpus run is cost-held; the native common-word-event diagnostic also lacks full point-score and corpus admission (test, OPS-S15-P7-WORD-TWELVE-1019; instrument ledger). Communality and personal specificity remain unresolved. |
| **G204** | Production records identify a writer beyond a shared population template | **SUPPORTED within the approved corrected-control design (test, S15-WA0-H1-20261025).** Human process records, mixed human/model pages, frozen features and exact nearest-neighbour readout: all six complete process channels pass independent-donor context and conditional reassignment checks, with each of 45 writers probed once against a fixed gallery of 30. Device and recording explanations remain. The historical pooled style 47% and rhythm 98% figures describe another aggregation; its original flags and the old engine-habit control failures remain (test, S15-DRIVE-PMAP-1018; S15-DRIVE-PMAP-RHYTHM-1018; S15-EV3-IDENTIFICATION-V1). |
| **G205** | Out-of-role departures are more diagnostic than culturally prescribed conduct | **OPEN (lit, SNIPPET).** A proposed application of correspondent inference, discounting and situational strength; no project comparison of culturally prescribed wording and its departures. |

**What the table says.** Production and page patterns identify writers beyond an independent shared-context reference under the approved session-summary measurement (G204). Old pooled estimates and their failed controls retain their own scope. Device, recording and model-text contributions remain possible, and personal-versus-shared history effects remain unresolved. This establishes conditional feature-based identification, not reconstruction of attention, value or automaticity. Cultural departure remains a candidate clue rather than a licence to infer private preference from unusual language. Confidence: one bad test away for scoped identification and recurrence; untested, logic only for the cultural diagnostic and communal mechanism.

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

**Habits caught by corrective expertise**

> [the everywhere marks, faster and more revised, are] flow state [...] corrective expertise blocks

> [uncaught habits] fulfill some higher-order goals, so they don't look inefficient

> the thing attention would struggle with more so is misapplied expertise, out-of-context expertise

*Curator walkthrough, 2026-10-18, about 09:15 PDT, answering the twelve analyst questions; filed at the October 18 daily integration. Excerpts and marked lexical repairs are preserved from the [filing source](../design/archive/SOUNDING_LINE_THEORY_FILING_2026-10-18.md).*

The curator interprets fast pervasive production plus later revision as flow interrupted by corrective expertise. An uncaught routine may serve a higher goal without appearing inefficient. The proposed harder case is expertise applied in the wrong context, not repetition by itself.

The table separates the proposed claim from its evidence and scope.

| # | Hypothesis | Status and evidence |
|---|---|---|
| **G216** | Fast pervasive markers plus revision indicate flow and corrective blocks | **OPEN interpretation (test, S15-DRIVE-W1-1017-1550).** Human process records and exact program: descriptive rates are 13.9 versus 8.2 characters per second and 6.9% versus 5.4% revised. Positive writer-label controls prevent a clean person-location or automaticity claim. The completed paired-history comparisons also find no own-history advantage; their exact occurrence-level correction counts describe logged changes rather than psychological flow (test, S15-DRIVE-D30-PAIRED-FIXED-1019). |
| **G217** | Misapplied expertise is harder for attention to catch than habit | **OPEN, logic only.** Curator proposal; no comparison isolates this difference. |

**What the table says.** Faster production and more revision can coexist. The matched history comparisons do not establish a pause advantage specific to the writer's own history; logged correction categories do not identify flow, corrective awareness or the difficulty of catching an inappropriate routine. Confidence: one bad test away for the descriptive process comparisons; untested, logic only for their mechanisms.

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

> time, which is really just a correlate for the number of decisions that were made in a complex space

*Curator's contribution and selective-attention walkthrough, supplied in the analysis thread; recording date not separately supplied;
filed 2026-09-18. Contiguous excerpt, wording preserved.*

The curator's account treats apparent effort as a clue to human decision structure worth
investigating, including past decisions compressed into present expertise. It proposes that
familiar polish cues can become misleading when production changes. This is a claim about an
inference's calibration under different conditions, not proof that the cue was always valid
or could never be biased. Automaticity makes present duration a poor measure of all the
structure brought to the work; it does not make every aspect of effort unobservable by
construction. Logged time, revision, selection and training history measure different things,
none a complete count of mental decisions.

The three existing hypotheses remain separate: judging attraction from one's own response,
using polish as a cue, and a changed relationship between polish and the contribution worth
investigating (HH-22, HH-17, HH-18). The contribution account is specified in
`DECISION_TRACES.md` §1. The proposed contextual calibration and any proxy for embodied decision
structure remain unvalidated.

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
| **HH-17** | Readers historically used polish as an effort cue; the correlation is strong in human corpora, near zero in generated | **OPEN.** The predicted relation is unmeasured. A defensible proxy must distinguish current labor from decision structure carried by expertise; elapsed time alone does not do so |
| **HH-18** | The effort heuristic is a broken valid inference, not a reader bias | **OPEN.** The curator's causal reframe; calibration must be assessed in the relevant production conditions. Neither universal prior validity nor immunity to reader bias follows from HH-17 |
| **HH-22** | Attraction success is judgeable by the reader from their own response | **OPEN.** The self-referring goal read as an instrument; split out of the aesthetics note 2026-08-10 |

**What the table says.** Audience modeling, comprehension support and attraction remain open
mechanisms. Easy transmission, useful learning, truthful guidance and recovery of the maker
can come apart. Neither clarity nor polish identifies values. The curator's polish account
concerns a potentially changed cue to embodied human decision structure; its calibration and
a defensible proxy remain unmeasured (HH-17, HH-18, HH-22).

In the tested constructed source/recipient family, worked action mappings improve transmission
of true and false rules alike, including under conflicting source aims. That scoped benefit
survived repair and untouched reserve confirmation (T01-S4). Reconstructing the selection rule
loses to direct reading, and teaching misleading techniques changes acceptance without improving
discrimination, costing useful true uptake (T02-S4, T03-S4). Descent into a method is therefore
not evidence of successful selective trust. This pattern keeps the curator's attention proposal
worth investigating while leaving its human mechanism open.

The source-world readers also fail important factor-reading and identical-evidence checks;
source history does not change uptake in the tested construction. Labels, warnings and
reappraisal chiefly move the acceptance threshold while discrimination stays flat (A02-S5 to
A05-S5). These results constrain the tested interfaces, not every possible protective strategy.
The hypothesis that directing attention can preserve useful method while declining an aim is
owned by §4 (HH-SELECTIVE-ATTENTION). Confidence: one bad test away for the scoped model-reader
transmission and uptake findings; untested, logic only for the human mechanisms and the
historical polish/contribution relationship.

**Play as a frame for personal expression**

> play is a [scaler] [...] rules are relaxed

> Laughter is a way of saying you're getting near the edge, but it's entertaining [...] funny is getting as close to the line as possible and not interacting with it

> Getting in the wrong mode costs.

> play is part of how you express yourself [...] freedom [...] that's why you're able to find the author in fiction more so [...] play is going to be one of the better ways to identify others

*Curator walkthrough, 2026-10-18, about 09:15 PDT, answering the twelve analyst questions; filed at the October 18 daily integration. Excerpts and marked lexical repairs are preserved from the [filing source](../design/archive/SOUNDING_LINE_THEORY_FILING_2026-10-18.md).*

The curator proposes a play mode that loosens constraints and exposes more of the person. The supplied analyst correction concerns stakes rather than an absence of rules; the quote keeps the uncertain word [scaler]. Detecting a frame and benefiting from it are separate requirements.

**Literature vocabulary, analyst handoff.** The following explanations retain the supplied analyst attribution. Linked sources were requested; inaccessible papers and uninspected full texts are **SNIPPET**, not independently verified findings in this pass.
- **Metacommunication**: signals how an act should be interpreted, including as play ([source](https://pubmed.ncbi.nlm.nih.gov/13297882/), SNIPPET).
- **Play bow**: provides a behavioral candidate for a visible play-frame signal ([source](https://doi.org/10.1163/156853995X00649), SNIPPET).
- **Benign violation**: requires a violation to be experienced as acceptable at the same time ([source](https://doi.org/10.1177/0956797610376073), READ, abstract only).
- **Psychological distance**: changes the conditions under which a violation is amusing ([source](https://doi.org/10.1177/0956797612443831), SNIPPET).
- **Laughter as social signal**: connects humor and play through an evolutionary account ([source](https://doi.org/10.1086/498281), SNIPPET).
- **Weak situation**: allows greater variation in the relation between traits and performance ([source](https://doi.org/10.1002/job.602), SNIPPET).
- **Personality from creative stories**: tests which traits are readable from fiction rather than assuming all are ([source](https://doi.org/10.1016/j.jrp.2010.05.003), SNIPPET).
The supplied Burghardt relaxed-field term concerns safety and reduced immediate pressure; its book was not inspected and this remains an attributed analyst gloss.

The table separates the proposed claim from its evidence and scope.

| # | Hypothesis | Status and evidence |
|---|---|---|
| **G220** | Playful or fictional records identify a maker better once the frame is detected | **OPEN; corrected genre comparisons are feature-specific and sensitivity-limited (test, S15-GEN1-IC-20261025).** Matched human writing/event records and exact program: independent-context identification passes in each genre. Creative-minus-argumentative style is -12.5 points [-29.17, 0], genre-swap p=.2338; rhythm is +12.5 points [0, 25], p=.0410. The exact paired diagnostic is .25 for both. No feasible dependence-constrained grid cell reaches 80% power. The original pooled result and failed references remain historical (test, S15-GEN1); genre is not detected play and Ghost N18 remains a separate prerequisite. |
| **G221** | Ignoring a play frame can reverse an inferred preference | **SUPPORTED only under the stated construction (sim, OPS-THEORY-1018-SIM).** Ghost N8 stipulates preference reversal during play; its mode-aware reader gains 0.049 to 2.588 nats across the play settings, with no-play controls at numerical zero. Discovery only, not human confirmation. |

**What the table says.** A frame can matter decisively when it changes how actions express a preference; the constructed result demonstrates that conditional error. The corrected reference supports identification within each human genre, but the style and rhythm contrasts differ, their intervals touch zero, and the measured paired sensitivity is limited (G220). A genre-swap diagnostic and an exact paired-correctness diagnostic ask different questions and must remain visible together. Genre does not establish play or frame detection, so the broader human claim stays open and genre weights stay equal. Confidence: one bad test away for the scoped genre comparisons and constructed frame result; untested, logic only for the broader human play-frame mechanism.

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

**Competence is an independent baseline**

> competence is something we just optimize for. And so base rates are really your best attempt at competence [...] everyone's doing the same signal detection [...] how sensitive are you in detection

> [a divergence from competence] would indicate a larger preference

*Curator walkthrough, 2026-10-18, about 09:15 PDT, answering the twelve analyst questions; filed at the October 18 daily integration. Excerpts and marked lexical repairs are preserved from the [filing source](../design/archive/SOUNDING_LINE_THEORY_FILING_2026-10-18.md).*

The curator asks for departures from competent behavior to reveal a preference. The analyst distinction is between sensitivity, criterion and the normative payoffs. Population conformity cannot supply all three. In equal-variance signal detection, the optimal likelihood-ratio threshold is the prior-odds ratio multiplied by the relevant utility-difference ratio; translating that threshold into a response location depends on the evidence distributions.

The table separates the proposed claim from its evidence and scope.

| # | Hypothesis | Status and evidence |
|---|---|---|
| **G223** | A departure from a competent criterion reveals preference | **OPEN.** Independent quality and payoff information are required; the approved SDT1 diagnostic measures population-relative behavior and retains the competence gap (curator decision, WEEK_REVIEW_20261018). |

**What the table says.** A baseline must predict what counts as success independently of the writer being explained. Agreement with other writers cannot certify that baseline or isolate preference from belief and sensitivity. Confidence: untested, logic only.

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
beat these frozen readers on two corpora; the Stage 7 CoAuthor comparison uses the corrected individual-suggestion unit (P13,
L352; Decision Traces H04-S3); it does not validate the old Stage 6 all-dismissal result.
A clean comparator with matched operative information and valid readout remains necessary
before claiming a general reader or evidence boundary across these corpora.

## §11. The instrument dashboard: adopted heuristics with measured strength

**Only heuristics measured in this project enter; candidate imports stay in §§6 to §8 until tested.**
Strength is always against a named baseline. The same number means opposite things next to a chance
rate and next to a field bar.

| heuristic | measured strength | baseline | status |
|---|---|---|---|
| **within-artifact variation, surface features** (§2) | 0.565 macro-F1 topic-controlled; 0.969 on the uncontrolled split | floor 0.444; field bar 0.830 / 0.959 | real, **not competitive where topic is controlled**; the uncontrolled win probably rides topic |
| **within-artifact variation, probe activations** (§2) | historical human long-form variance 0.0102 vs machine 0.0065, *p* = 0.002 | matched series length; register uncontrolled initially | **REJECTED as provenance (test, L39 → L101 → L105).** Initial interpretation superseded by register/family sensitivity and dissociation from the artifact-side sign; mechanism unresolved |
| **visibility partition** (§6) | authors at 0.78 (low-vis) vs 0.38 (high-vis); draft-stage 0.48 (high) vs 0.30 (low) | chance 0.10 / 0.33 | **SUPPORTED (test).** Clean double crossover, first pass |
| **revision homogeneity** (§7) | real 0.45 vs spliced 1.94, AUC 1.0 | synthetic cross-author splice | **SUPPORTED (test), first pass, weakest adversary.** The realistic imposition case is untested |
| **provenance prior** (§1) | ratio shift +0.007, *p* < 2×10⁻⁸, three corpora | paired identical text | **SUPPORTED (test), replicated.** In the reader model; human-side untested |
| **maker-reader family similarity** (§1, model analogue) | historical exact-vs-cross +0.035, sibling-vs-cross +0.025; accepted Qwen paraphrase +0.016/+0.021; capacity rank 0.43; crossed +0.020/+0.014 original and +0.012/+0.011 weak rewrite; geometry ranks 0.50/0.77. Corrected full matrix: qwen +0.0137, smollm +0.0096, olmo +0.0365. Strong independent erasure: +0.001 in each powered family | identical candidates, within-reader contrasts, weaker rewrites, then stronger independent erasure with both families above floor | **SUPPORTED for original-artifact relatedness; mechanism OPEN (test, L163-L168, L177-L182, L217-L219, L225, L236, L251).** Stronger erasure removes the advantage; weak-rewrite survival does not exclude shared convention. Later hash splits are retrospective robustness, not untouched confirmation; see §1 for retained history |
| **repeatability versus presentation robustness**, local model reader on constructed histories | identical repeats match; equivalent option/label/evidence presentations move canonicalized probabilities, with changed-presentation mean-loss contrasts unresolved | 64 histories, six paired views, unchanged exact targets; uniform loss remains below each view's descriptive mean | **SUPPORTED for output sensitivity in this reader construction; directional accuracy effect OPEN (test, L437).** Complete actual replay, invalids retained; original calibration voided and corrected without changing primary contrasts. No human or internal-mechanism claim |
| **S15-DRIVE-V2**, calibration of saved human-choice forecasts | Whole 26-arm decomposition closes; all eight reader/backbone combinations have interval upper bounds below the 0.01 useful-gain margin | Frozen backbone on 234 exposed CoAuthor decisions from 31 writers; separate full Phase 0 population comparison retained | **REJECTED for useful gain in these frozen combinations (test, S15-DRIVE-V2; human process records, model and fitted-program readouts).** Descriptive reuse of saved fits, not independent replication; raw calibration error is substantial, exact-vector singleton resolution is not generalization evidence, and iid corrections are not cluster-valid |
| anomaly entry (§2) · confidence trajectory (§4) · interest ratings (§5) · effort correlation (§8) | | | unmeasured: one simulation bound, a series never recorded, an hour of his time, an undefended proxy |

**What the dashboard says.** Original-artifact relatedness survives within-reader and weaker
rewrite controls, but the strongest independent eraser removes the advantage with both families
above their floors (L251). Corrected full-matrix aggregation preserves the original relation
(L236); retrospective splits do not provide untouched confirmation. Shared organization and
shared convention remain rivals, and representational correlation does not settle causation.
The probe trajectory's initial human-machine contrast is superseded by model/register sensitivity
(L101, L105). A local model can repeat an identical request yet change its inferred distribution
when equivalent evidence is presented differently; repeatability alone therefore does not establish
presentation robustness or correct inference (L437). On exposed human choice records, decomposing
the complete saved forecast curve does not recover useful additional prediction from the frozen
reader and backbone combinations; calibration error and bin-dependent resolution do not identify
why the reader failed (S15-DRIVE-V2). These measurements do not establish a general provenance
mechanism, and stacking still requires construct validation. Confidence: replicated and controlled for the surface
variation number; instrument-dead for the probe's provenance reading; one bad test away for the
relatedness mechanism, constructed presentation sensitivity, saved-forecast calibration and other measured heuristics; untested, logic only for everything
unmeasured is untested.
