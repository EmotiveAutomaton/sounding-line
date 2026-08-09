# Reader heuristics — how a bounded reader approximates the triple inference

> While I don't expect we will have to rely on these heuristics when designing depth extraction, I
> expect AI will arrive at most, if not all of them, organically. Nevertheless it's worth keeping track
> of the ones we have run into that would be relevant as potential **feature-extracting amplifiers** in
> future, that other research teams may have missed.

**A bounded reader approximates the triple inference using priors about the maker, local cues in the
artifact, strategies for moving between explanatory levels, and calibration rules that limit
overinterpretation.** Humans do not solve the inference; they run heuristics at it, converging the
way a series approximation does. The curator's own readings — fifteen artifacts, two sessions — are
**the richest hypothesis source this project has**; they are not a validated instrument, because no
independent ground truth has scored them, and the calibration literature below shows exactly how
expertise and confidence coexist with low reliability.

**This file owns** reader priors, entry cues, traversal strategies, updating, stopping, and
calibration. **It does not own** the inference targets ([`THE_TRIPLE_INFERENCE.md`](THE_TRIPLE_INFERENCE.md)),
the ontology of artifact traces ([`DECISION_TRACES.md`](DECISION_TRACES.md)), model architecture
([`THREE_COGNITIVE_LAYERS.md`](THREE_COGNITIVE_LAYERS.md)), or alignment. *(Renamed from
`HUMAN_HEURISTICS.md` 2026-08-09.)*

---

# Part I — The reader's loop

## §1. Priors held before inspection

What a reader brings before the artifact is opened: **domain expertise** (which sets the available
entry points, §3); **closeness to the maker** — *"Showing someone your writing is a kind of
intimacy"* — the one prior where the relationship does the work rather than the text; **biography
and prior artifacts**, which are more observations, not context (*"Everything's an artifact. Even
information about their life"* — canonical in the triple inference, operational here); **provenance
framing**; and the **communicative assumption** — treating the maker as intending to be understood.

The communicative assumption is the strongest and the most dangerous of these. It is standard in
cooperative inverse reinforcement learning, where teaching behaviour is part of a shared objective —
but that models a cooperative game, not every maker–reader relationship, and his own caveat marks
the limit: *"humans actively, constantly pretend they're teachers under certain framings. Does that
always hold?"* It plainly does not; concealment, propaganda, seduction, and audience mis-modelling
are the countercases, and a wrong communicative assumption licenses confident inference from
structure placed to mislead — the same error the expertise literature calls failure to transfer,
running the other way:

> That's kind of the whole premise for **failure to transfer** — this lack of transfer as a result of
> expertise. **Same idea, different direction.**

And it lands on generated text specifically:

> **AI is being treated like a teacher also. It's getting the benefit — and maybe that's part of the
> problem, at least.**

The provenance prior is no longer speculative: a reader model's affective read of identical text
shifts when told the text is machine-made — small, fixed in direction, replicated on three corpora
(the measurement is canonical in the model-side ledger, `THREE_COGNITIVE_LAYERS.md` §7). Whatever a
disclosure label does to a human reader, the reading machinery itself is not neutral to claimed
provenance.

## §2. Finding an entry point

> The thing that most jumps out at me isn't mistakes but **unusual constructions, or odd decisions
> that I can't find an explanation for.**

Reading enters at an **anomaly**, never at the artifact as a whole — then runs purpose→method and
method→purpose from wherever the reader has partial expertise. His own discomfort, recorded because
he raised it: *"I hate that a lot of this is me picking out mistakes and typos, which is also a
trick for AI and it's not okay. But it is a way of extracting decisions."* A **mistake** is the
sharpened case — an anomaly with a *known cause*, so the response to it is a decision with its
alternatives visible: *"the mistake, and the way the author can be presumed to have responded to it,
is one of the more useful pieces of information once you have observed it."*

Two calibrations on this cue family. **Entry efficiency is not final quality**: the simulation found
anomaly-first ordering saves ~5% of cost and changes the answer by exactly zero — which bounds the
expected size of an ordering effect, and does not touch whether anomalies are *informative*. And two
imported entry cues extend the family: **inverse salience** (diagnostic weight runs opposite to
conspicuousness, §7) and **reserve versus overpaint** (did the structure make room for a claim, or
was it inserted? — the trace is Decision Traces' object; the reader's rule of looking for it lives
here).

**Within-artifact variation** is the curator's primary detector — polish *change*, not polish level:

> When I've been talking about the veneer in my head, I've been thinking about the imagery and
> iconography.

*The performance is what costs something, so the performance is what slips, and the slip is where
the maker shows* — with his own scope limit attached: useless on published books, because editing
sands the polish flat. The field detects within-document variation successfully (burstiness,
unmasking, PAN style change at 0.830 on topic-controlled data), and his reading of what they are all
measuring is a claim, not a complaint:

> It's not burstiness. It's not unmasking. **It is goal variation** — all of them varying in relative
> strength as you express yourself. People aren't seeing it for what it is.

One honesty note on that claim: what the field's baselines validate is *detection of variation and
discontinuity*; the interpretation that the variation is **goal** variation is exactly what remains
open. Intrinsic plagiarism detection is also a different thing — a spliced author, not one author's
goals moving — a distinction he separated after I collapsed it.

## §3. Traversing explanatory levels

> Walking up to an unknown oil painting, you can engage with it on the level of **metaphor** — why did
> the author craft what they did. On the level of **technique**, like perspective. On the level of
> **mechanics** — how did they move their hand as they painted.
>
> **You can use any piece of knowledge about any of those three channels to begin the decoding.**

Working vocabulary: **mechanics** (physical realization), **technique** (organized method), and
**purpose** (local and higher-order intent — "metaphor" names a subtype of this level, and is
narrower than the level needs, since the top has to carry goal). Dennett's three stances are the
closest citation (physical/design/intentional), and Panofsky was the wrong one — he rejected it
correctly, since Panofsky's levels are about what an image *depicts*. Structural resemblances to
Marr's or Newell's levels supply vocabulary, not evidence: those frameworks partition different
objects for different purposes, and counting them as independent convergence overstated the case.

*Media literacy* is the common-language name for entry at the purpose level — a general skill for
ratcheting into unfamiliar media through the metaphorical layer.

The collision with the only occupying framework is real but must be stated precisely: Bullot &
Reber's psycho-historical frame makes historical/design-stance understanding a **necessary
condition** of full appreciation, and their own response describes actual processing as recursive
with feedback — so the disagreement is over *necessity*, not over whether processing is temporally
one-way. Their framework's replication record is weak (34 experiments: 26% support, 56% none), which
makes the collision worth taking. The experiment that would decide our side — supplying
mechanics-level information and measuring goal recovery — is canonical in the triple inference
(G56); this section describes the human strategy it operationalizes. Rasmussen's abstraction
hierarchy (means–ends diagnosis from any level, decades of use) is worth reading as a candidate
formal home, not adopting sight unseen — it has published methodological criticisms (Lind) aimed at
exactly the ambiguities that matter here.

## §4. Updating and active search

> It starts questionable... 8 or 9 by the end.

**Confidence moves while reading, and the trajectory carries what the endpoint does not** — every
reading this project records is a final number, so the series has never existed to be checked. The
reader also searches actively: re-reading (each pass recovering lower-confidence attributions from
the tail), **epistemic foraging** for biography and further works — where *everything is an
artifact* becomes operational: context supplies additional observations but is not automatically
trustworthy — and switching levels when a hypothesis fails, per §3.

One external caution bears on the whole series family: a study of hidden states as author
representations found document-level mean pooling best, which is evidence against series-carrying
claims at the representation level — not decisive (it optimized for identity, not maker state), but
the reason to expect modest effects.

## §5. Continuation and stopping

> Interest comes from finding decisions that you can't attribute meaning to, which implies there's
> more meaning you don't fully understand — either a **process** you aren't aware of, or an **extra
> motivation** you aren't aware of.
>
> **Artfulness is making a lot of unexplained decisions. Aesthetics is the appearance of having made
> unexplained decisions but for a reason, in an ordered sense.**

**Interest is the continuation signal**: unresolved but apparently structured decisions keep the
reader searching, which makes reader-reported interest an instrument —

> **If interest is what a reader feels when decisions are present but unattributed, then
> reader-reported interest is an instrument — and it is one we can ask a human for directly.**

It also answers his own question about performative polish: under this account, performative polish
is *ordered without being unexplained* — a measurable distinction. The formal target is effective
complexity (structure neither random nor trivially regular), not Berlyne's collative variables —
read at source, Berlyne's arousal theory is *"mostly abandoned"*, and the live descendants
(processing-fluency accounts) sit at the opposite pole, locating pleasure in ease. That tension is
the thing the interest-ratings test would adjudicate, since the two accounts predict opposite
correlations between interest and recoverability.

Stopping is the calibration side: graded attribution when evidence supports only that (§10), and a
**hard falsifier ends the inference outright** — the two-channel rule of §9.

# Part II — Cue families

## §6. Distinguishing choice from constraint

The governing rule, distilled from the one field with forty years of practice at reading makers off
products: **model what the medium and task force; interpret only residual variation as candidate
choice.** The mechanical null model is its cleanest form — in controlled experiments on molded glass
cores, flake geometry is dominated by two measurable variables, with platform width following from a
material constant *"not under direct control by the knapper"* — and its severe caveat travels with
it: the null model explains far less variance off the bench.

The cue family, by function rather than by source:

- **Recurrence** — *"it is because a gesture is constant or recurrent that it can be interpreted as
  intentional"* (Soressi & Geneste) — with the honest reading attached: recurrence is equally
  consistent with habit, with training, and with a constraint that is itself constant. The
  habit-shadow objection, arriving from archaeology.
- **Stage-differentiated signals** — low-visibility, early-acquired features carry deep identity;
  visible, easily-copied features carry situational identity (Gosselain's pottery result). **This
  cue is now measured in-project: a clean double crossover on its first pass** (canonical row in
  `DECISION_TRACES.md` §3; dashboard below).
- **Error handling over error rate** — novice cores show insistence and stacked steps on a ruined
  surface; expert cores show recognition and abandonment. Error *handling* measures metacognition;
  error *rate* on a small sample measures which burst you sampled, because errors cluster.
- **Rigidity under perturbation** — experts hold outcomes constant under changed tools and
  materials; low-skilled artisans reveal *"rigid skills."* It implies an **active probe**: perturb
  genre, length, or audience and measure whether quality is preserved.
- **Intention elicitation as the calibration ceiling** — the knapping protocol where makers draw the
  intended flake before striking: experts predict only **R² = 0.655 of their own stated intention**.
  Our intent ladder is this protocol, arrived at independently. Any recovery instrument works
  against a ceiling that expert self-prediction already fails to reach — stop treating distance from
  perfect recovery as failure.

## §7. Habit, concealment, and revision

The reader's rules for exploiting the automatic traces (the trace ontology itself is
`DECISION_TRACES.md` §3):

- **The Morellian admissibility filter** — a feature may be used only if it is amenable to
  individual expression, not school-supplied, not accidental, and **not one of a suite requiring
  deliberate variation**. Criterion 4 is the high-leverage import: elegant variation is a writer
  overriding their own defaults, so the places our measures find most "varied" may carry least
  individual signal. This is a **historical candidate method, not proven practice**: Morelli's own
  notebooks show he scarcely used it (*"the spirit of the master met mine, and the truth flashed
  upon me"*), and the stylistic channel has never independently caught a competent forger.
- **Inverse salience** — diagnostic weight inversely proportional to conspicuousness, because the
  imitator's attention flows to the conspicuous (Berenson's *"subconscious signature"* of
  *"small particularities which escape even the notice of copyists and forgers"*). The honest limit:
  a claim about the adversary's attention budget, not physics — it buys asymmetry, not security. And
  the re-aiming caveat: these identity tools may discard exactly the conspicuous features where
  *values* live.
- **Self-revision versus imposed revision** — imposed changes are lumpy, discrete, heterogeneous;
  self-revision is homogeneous and *"of like kind"* throughout. Distributional, not semantic, and
  the discriminator mixed provenance needs most (first in-project measurement queued).
- **Suspicious regularity** — the imitator is *more* regular than the genuine article, executing
  carefully rather than habitually. If an instrument treats high internal consistency as expertise,
  this literature says it may be backwards.
- **Reserve versus overpaint** — planned room versus insertion, computable on one static text; and
  abandoned scaffolding (a numbering scheme that stops, a promised return that never lands).
- **Mixed provenance takes the graded vocabulary** — *by · attributed to · studio of · circle of ·
  school of · follower of · manner of · after* — three axes at once (proximity, temporality,
  intent), with *workshop of* the category this project needs most and would not have invented.

## §8. Communicative shaping — the bard

**2026-08-07.** His refinement of the teacher assumption: a maker is something more specific, and
the difference is the part nobody has formalised —

> What we're actually looking for is **a bard**, to be a little bit more precise. **There are two
> motivations. They want to grab your attention through aesthetic capture, and they also want to make
> it easy for you to ingest the data.** And that's the teacher aspect.

> How on earth do they shape it in order to create that effect? **I assume they try to model the brain
> of their listener. Of course they do.** Which makes all interactions this kind of **collaborative
> back-and-forth.**

So the maker runs the triple inference in reverse while making: they model the reader, then shape
the artifact so the reader's inference lands where they want it — an artifact is a trace of the
maker's process *plus their model of you*. The reader's corresponding prior: **conspicuous structure
may have been placed to guide my inference** — aesthetics as deliberately-left scaffolding for the
descent through the levels:

> Part of aesthetics might be **leaving the kinds of hooks in your program that make it easier to
> deconstruct it.** Metacommentary or high-level metaphor that can be used to **move down through** the
> levels.

(The measurement side of the attraction/translation split lives in `DECISION_TRACES.md` §2.) He
flags the restatement risk himself: *"yes, this is just a restatement of CIRL with different terms"*
— it is, up to the aesthetic layer, which is the addition; and CIRL's cooperative-game framing does
not describe every maker–reader relationship, so this prior carries §1's concealment caveat in
full. The asymmetry he names is the sharpest thing here:

> **AI isn't interacting with this. It's only trying to take, it's not giving.**

If right, the missing thing in generated text is the second half of a collaboration — a third
account of the unease, distinct from broken polish–effort and flattened intent, and the three
predict different things. The effort heuristic belongs to the same family:

> Aesthetics is one of the **easiest goals to judge**, because it is literally surface polish — you
> can explicitly judge whether the maker succeeded at it, and implicitly the value of what you are
> seeing by **how much you want to look at it. It is a self-referring goal and you can cheat it pretty
> easily.**
>
> **It's also the piece that's misfiring on AI specifically. Previously it correlated with effort very
> highly. Now it does not. That's what's breaking.**

On his account the effort heuristic is not a reader bias but a normally-valid inference a new
artifact class has broken — and both rows testing it are blocked on measuring *effort*, the quantity
automaticity makes unobservable by construction.

# Part III — Calibration

## §9. Baselines and admissibility

- **A genre and register baseline is infrastructure, not optional** — without one the instrument
  confidently reports the genre's decisions as the author's, the same failure that killed 61 of our
  81 replicated features. Morelli's version: the connoisseur lives among photographs as the botanist
  among plants.
- **Topic controls by construction** — the same practical question answered from different
  positions, or topic does the work.
- **Mechanical constraints modelled first** (§6's governing rule).
- **Two channels, never averaged**: hard falsifiers can veto; stylistic inference proposes and
  never vetoes. Every historical forgery exposure came from a hard falsifier — titanium white, a
  broken provenance chain, a confession — and the fields that averaged the channels produced the
  Getty kouros.
- **Per-feature accuracy, never aggregates** — an aggregate of 72.6% concealed a worse-than-chance
  category.
- **Pre-register the feature set.** The tradition that defines attributes after seeing the
  assemblage defends a garden of forking paths; refuse it.

## §10. Reliability and ground truth

The calibration record from the fields that read makers professionally, kept because it disciplines
ours: intention elicitation gives the ceiling (§6); **inter-annotator agreement is mandatory before
believing any extraction** — eleven analysts on one knapper's hundred flakes, definitions agreed in
advance, still disagreed significantly, with failures concentrated in exactly the interpretively
loaded attributes, and *training background mattered where years of experience did not*. The
replicability dilemma cuts at us directly: selecting features *for* replicability privileges the
trivially measurable over the behaviourally meaningful — our funnel drops features that fail a
filter. Refitting is their gold standard because it is non-inferential; our text analogue is version
history, which finished text does not supply — **we are the archaeologist handed one finished
handaxe and no flakes**, the position where every practitioner agrees inference is weakest. The
falsification test they ran on themselves (a 65% refit site against mental reconstruction: an
invented production method, a late product misdated to the start) is the standing warning — with its
honest scope: the authors themselves concede the fault was implementation, not the concept. Report
identifiability the way their best work does: *"these two processes separate at 80% under
cross-validation, on this feature set"* — never *"we can read the maker."* And Ginzburg's boundary
stands over everything: the evidential paradigm is individualising, conjectural, with an
unsuppressible speculative margin — **an instrument that outputs a confidence percentage claims a
status this entire tradition says is unavailable**, which is why the field built a graded
vocabulary instead.

## §11. The instrument dashboard — adopted heuristics with measured strength

**Only heuristics measured in this project enter; candidate imports stay in §§6–8 until tested.**
Strength is always against a named baseline — the same number means opposite things next to a chance
rate and next to a field bar.

| heuristic | measured strength | baseline | status |
|---|---|---|---|
| **within-artifact variation, surface features** (§2) | 0.565 macro-F1 topic-controlled; 0.969 on the uncontrolled split | floor 0.444; field bar 0.830 / 0.959 | real, **not competitive where topic is controlled**; the uncontrolled win probably rides topic |
| **within-artifact variation, probe activations** (§2) | human long-form variance 0.0102 vs machine 0.0065, *p* = 0.002 | matched series length | **SUPPORTED (test), first pass** — the operationalisation nobody pre-empted; register uncontrolled |
| **visibility partition** (§6) | authors at 0.78 (low-vis) vs 0.38 (high-vis); draft-stage 0.48 (high) vs 0.30 (low) | chance 0.10 / 0.33 | **SUPPORTED (test)** — clean double crossover, first pass |
| **provenance prior** (§1) | ratio shift +0.007, *p* < 2×10⁻⁸, three corpora | paired identical text | **SUPPORTED (test), replicated** — in the reader model; human-side untested |
| anomaly entry (§2) · confidence trajectory (§4) · domain relation · interest ratings (§5) · effort correlation (§8) | — | — | unmeasured: one simulation bound, two corpus blocks, an hour of his time, an undefended proxy |

**What the dashboard says.** Four heuristics now carry numbers — up from one — and two of the four
landed this week at first-pass strength. The stacking question is still premature but no longer
empty: the two variation measures and the visibility partition are plausibly independent channels,
which is what a stack needs. Confidence: the surface-variation number is replicated and controlled;
the three new rows are one bad test away each; everything unmeasured is untested.
