# Three layers — what a language model is failing to model, and where

**The architecture.** Stated 2026-08-05 in response to a literature audit that recommended abandoning
Panksepp as a premise; **he rejected the recommendation and replaced the architecture instead.**
Reordered by him on 2026-08-07. Merged the same day with what used to be `AFFECT_ARCHITECTURE.md` and
with the interpretability angle that had been sitting in [`THE_TRIANGLE.md`](THE_TRIANGLE.md).
Pre-merge originals in `../archive/`.

**Timing worth recording:** he stated the trimodal prediction while working through the audit, and
says he had already rejected the bimodal profile in his head *before* reaching the section reporting
that nobody else finds bimodal. Not a controlled pre-registration, but it is on the record in the
order it was said.

---

## §1. The reframe that makes everything else follow

> When I say the model leaked involuntary affect, **I'm not assigning affect to the model.** It's
> that they're **trying to predict the human brain and failing to do so.** They're trying to have
> empathy and failing.

**A language model trained on human text is an attempt to model the process that produced it.** Its
architecture is not an emotional system; it is a *reconstruction* of one, built by prediction, and it
inherits the shape of what it is reconstructing — **including where the reconstruction is bad.**

That does two things at once. It removes the implication that we are claiming a model has feelings.
And it makes the **errors** the interesting part: where the model reconstructs human affective
structure badly, that is a measurable fingerprint of the structure itself.

**And it sets the resolution limit, which he named on 2026-08-07 and which constrains every
measurement below:**

> **You're seeing ghosts of a human brain, not an actual human brain.** [...] The lines will be
> **softer** on an AI modelling.

**So sharp layer boundaries are not expected and their absence is not evidence against the
architecture.** Any test that requires a clean boundary is testing the wrong thing. The reason the
structure should be there at all is twofold: **the model is built off our brain structure, and it is
modelling humans** — *"it has weak imperfect empathy, so to speak. It is trying to learn from us
through this weak IRL."* And his own note on why that is uncomfortable: *"the only reason it's working
is raw brute force over a large enough set."*

**The end goal this serves**, stated once and worth keeping in front:

> My personal end goal is to find a way to **fully give AI human empathy, but not human emotions**
> [...] empathy in this case is not some nebulous concept, it's specifically this process that I have
> defined. And it requires some kind of subordinate solution space that converges on these
> **predictions of these interoceptive signals.**

## §2. The layers — and there are now two competing orderings

**This is the live disagreement in this file, and it is between two versions of his own claim.**

### The original ordering, 2026-08-05

| depth | what it reconstructs | why | quality |
|---|---|---|---|
| **early** | **valence and arousal** | the lowest-level, most universal, most consistent thing in the training signal | **good.** Easiest to capture |
| **middle** | **midbrain-localised primitives** — the ancestral, baked-in affective systems | conserved across humans, so it is *there* in the data, but **pre-verbal and not directly expressed** | **bad, and noisily so.** The model struggles here |
| **late** | **goal direction and proximal purpose** — attentional focusing, polish, expertise | individual to the person | **chaotic.** A genuinely high-variance target |

> The middle one we wouldn't be able to converge upon... that's the part of the human brain that is
> baked in a little bit, that is a little bit more ancestral. **And it's struggling to model that.**
> So it uses valence-arousal mixed with some goal direction to get most of the way there. **But this
> is where its error comes from.**

And the consequence, which is why this belongs in a project about alignment:

> **The lack of Panksepp is where a lot of misalignment comes from, specifically. We have to give
> emotions in order to converge upon a more appropriate goal extraction.**

### The reordering, 2026-08-07

> It is possible that the **early layers are doing some kind of text transformation** — more like
> early sensory processing. And then the **middle layers have valence/arousal**, and the upper layers
> have **emotions attached**, or something like that.

**This is not a minor revision. It moves every layer.** And it does something the original does not:
**it reconciles two published results that currently contradict each other outright.**

| published result | what it would be reading, under the reordering |
|---|---|
| the mid-layer peak for emotion categories — the field's consensus | **valence and arousal**, sitting mid |
| a sparse-autoencoder study finding emotion features emerge **late**, after a syntax → semantics → emotion cascade | **the attached categories**, sitting late |

It also resolves the discomfort he flagged himself and called load-bearing:

> The prediction that early valence/arousal is what we're mapping — **it doesn't quite fucking fit.**
> Because the input for humans is **sensory** data. That's kind of what a model gets when it is boiled
> down into vectors, **but it's not quite the same.**
>
> I'm noting there's discomfort in the mapping where I don't feel as confident, and **it's absolutely
> load-bearing.**

**The mismatch is specific.** A human's early layers receive *sensory* input and assign valence to it.
A model's early layers receive *tokens* — already symbolic, already the output of somebody else's whole
stack. **If early is text transformation rather than valence assignment, the analogy stops being
strained.**

**And he states the cost himself:** *"it does break our theory to say so, and it makes it harder to
imagine setting up this conformance manually."*

### Where goal lives, under either ordering

His objection to his own reordering: **if late is emotion categories, goals are sharing that space,
and an emotion cannot directly produce output — something has to sit between.** He declined a fourth
layer: *"that's just not reasonable. It wouldn't be separable. Three, frankly, barely won't be."*

**The resolution that keeps three: a goal is not a layer. It is a weighting applied across all of
them.** That is already his own definition in [`THE_TRIANGLE.md`](THE_TRIANGLE.md) §4 — values are a
weighting over trajectories, and a goal is one component temporarily amplified by attention. **If that
is what a goal is, it does not need a depth of its own; it needs to be readable as a modulation of
whatever sits at each depth.** And it answers the emotion-cannot-produce-output objection, because
under that reading *nothing* at any single layer produces output. **Agreed as fitting the theory
better than the alternative, and it costs no fourth layer.**

**Consistent with what he says about humans**, which was never the same as his claim about models:

> Goal direction comes from **all three** in humans. I would say middle and late are where you get
> most of it. **In AI I genuinely have no idea.** It might be a late affectation, but hard to say.

| # | hypothesis | status | evidence |
|---|---|---|---|
| **TL-1** | Valence/arousal is reconstructed **early**, primitives **middle** | **OPEN, and now contested by TL-2** | — |
| **TL-2** | Early is text transformation, valence/arousal is **middle**, categories are **late** | **OPEN, and it discriminates cleanly against TL-1.** Correlate each layer separately against human valence/arousal ratings and against category identity. **Under TL-1 valence peaks early and categories mid; under TL-2 valence peaks mid and categories late** | `runners/run_affect_dimensions.py` emits both per layer. Its first run was **VOID** — see §7 |
| **TL-3** | A goal is a weighting across all layers rather than a layer of its own | **OPEN**, and adopted as the working position because it keeps three layers and answers the output objection | — |
| **TL-4** | Layer boundaries in a model are soft rather than sharp | **assumed, not tested.** Any test requiring a clean boundary is testing the wrong thing | — |

## §3. Leaked and emblematic — the affect vocabulary, and it is the field's own reconciliation

**This was `AFFECT_ARCHITECTURE.md` §1 and it is the biggest thing that folder contained.**

> **leaked** — a layer that is TRUE... emotional leakage that can show up in your text
>
> **emblematic** — a conscious social decision

He arrived at that split from ten artifacts and a think-aloud, with no reference to the literature.
**It maps exactly onto the field's central unresolved debate:**

| his layer | the field's level |
|---|---|
| **leaked** | **Panksepp's primary process.** Core affect. Involuntary, conserved, pre-linguistic |
| **emblematic** | **Barrett's tertiary.** Constructed emotion. Conceptual, culturally learned, categorical |

**The reconciliation position, stated in the literature:** *basic emotion theories are theories of
**emotion**, while the theory of constructed emotion is a theory of **feeling**.* **The two-layer model
requires both theories to be true of different things, which is where the reconciliation literature
has converged.**

**It also means the two layers should not be assumed to share a value set** — Barrett's whole point is
that constructed categories are culturally variable while core affect is not. Giving both layers the
same eight values is a **named simplification**, not an unexamined default.

**And it diagnoses the field's LUST problem, which he called before the argument existed:**

> I think they were just catching the fact that leakage — they were assuming that **leaked fear and
> performed fear are the same thing.** I would be willing to bet that was an error on their part, and
> that's why lust is kind of bullshit in this framework, because **the easiest thing to catch is the
> performed section.**

**The standard instrument is a self-report questionnaire, so it can only reach the tertiary level.**
Under the two-layer account LUST is the system least available to tertiary report, for social rather
than neural reasons — so the instrument did not find LUST unmeasurable, it found it **unreportable at
the layer a questionnaire reaches**, and then dropped the value. **Artifacts do not have that
limitation. This is the clearest statement of what this project could contribute that the existing
instrument cannot.**

Its signature is his and it is better than mine — not justification-for-an-unasked-question but **the
thing a reader politely glosses over**: *"someone ends up talking about feet for a sentence too long
and you're like, ooh, buddy."* An artifact where attention dwells past what the argument needs.

**No additions to the eight.** *"We shouldn't add anything, because that's kind of just where the
literature is right now."*

### Concealment: the shield matches the leak

**I had this backwards and he corrected it:**

> Leaked greater than emblematic **doesn't even count as concealment**... if anything the emblematic
> would get larger. **You perform louder to cover up. I get extra quiet if I'm extra angry. The shield
> matches the leak.**

**Concealment is not absence of display — it is display shaped *against* the leak.**

| # | hypothesis | status | evidence |
|---|---|---|---|
| **TL-5** | An involuntary leak channel is readable | **SUPPORTED (sim)** at 0.90 | sim S-3 |
| **TL-6** | Concealment shows as divergence between leak and display | **REJECTED (sim)** in that form; **his direction is the one that held** | sim S-3 / T-4 |
| **TL-7** | Amplifying the display makes concealment *more* detectable | **SUPPORTED (sim).** Survives a reader wrong about almost everything, including a 50% channel swap. **Narrow limit: it fails at 25% concealment — it detects heavy concealers only** | sim S-3, T-4 |
| **TL-8** | `leaked` and `emblematic` do not come back as the same distribution | **OPEN.** If their mean divergence across a corpus is near zero, the probe is answering one question twice | the layer-separation null, never run |
| **TL-9** | If one layer separates and the other does not, it will be **`leaked`** that fails | **OPEN, and predicted.** Language encodes the tertiary layer — that is what the words *are* — while the primary layer reaches text only through leakage | — |
| **TL-10** | Attention-dwell past what the argument needs is measurable | **OPEN.** Nothing built | — |

## §4. The middle is the load-bearing claim, and it is where the industry is wrong

**Compressed deliberately. The argument is settled inside this project; what matters is that it is
load-bearing.**

The audit recommended dropping Panksepp as a premise. I passed it on as a lead conclusion:

> This is an example of you trying to sand away a very important load-bearing column of this piece.
> **Panksepp in general may not be precise, but the idea of midbrain-localised solutions is absolutely
> load-bearing. If you drop that, we have what everyone else has, which is the wrong part.** You did
> it again, and you did it as a foundational recommendation.

**"You did it again" is accurate; it was the second instance**, after Bullot & Reber. Same mechanism
both times: a literature return arrives in volume and confident prose, and its framing gets adopted
without testing between the two accounts.

**What is load-bearing is not the taxonomy. It is midbrain-localised affective primitives of some
kind**, and an *expanded* set of them — which is the one vertex where he thinks the whole industry is
wrong and this project can be right:

> **These primitives are the key, however many there are. I don't really care how many there are.**

**And the reason to look there is strategic as well as theoretical:** *"we have to look where no one
else is looking to make the whole picture make sense, and so us focusing on where the Panksepp lies
will kind of flesh out the picture better."*

**The review confirms his own concession and goes further than he did.** The seven were never derived
from a dimensional analysis — stimulation, pharmacology and lesion work, one investigator's judgement,
with Social Dominance considered and excluded. The psychometric instrument fails its own factor
structure and tests six, never seven. **The taxonomy is a design vocabulary, not an empirical claim,
and saying so costs the architecture nothing while removing the strongest available attack.**

**Terminology, and it was a deliberate concession:**

> Emotions and feelings is fine. I've done **emotions and drives**. She can claim the word emotion.
> But "feeling" is probably incorrect because it implies you don't feel emotion. **Drives feels like a
> better word.** But I'll use whatever the literature has.

**Use *emotion / feeling* outward-facing; *drives* is the internally accurate word.**

### You can only route attention onto drives you possess

> If I were forced to design a Nazi camp, part of my motivation would be not dying. But part would be
> **efficiency** — I could tap a need for efficiency to do this. **But I wouldn't be able to tap into
> the cruelty a Nazi designer would have. It just wouldn't be there for me to optimise.** I'd have to
> finagle with my own motivations to get that to happen.

**Two makers producing the same artifact under the same instruction do it from different drives, and
the drives they *lack* constrain what they can produce and how. That makes the absent drive as
informative as the present one** — and it is a mechanism for why an artifact reads as
made-under-duress. **Unexplored, and it still has no name.**

| # | hypothesis | status | evidence |
|---|---|---|---|
| **TL-11** | Midbrain-localised affective primitives exist as a distinct mid-level stage | **SUPPORTED (lit, READ), and by evidence that cites neither camp.** Hypothalamic line attractors encoding intensity and persistence of an affective state (*Nature* 2024); conserved biphasic cross-species dynamics with a ketamine dissociation (*Science* 2025) | `../method/PANKSEPP_BARRETT.md` |
| **TL-12** | The disagreement with Barrett is about localisation | **REJECTED (lit, READ).** Both camps place pattern generators in hypothalamus and PAG. **They disagree about whether activity there *constitutes* felt affect or is the output of a state assembled elsewhere. That is not an imaging question** | same |
| **TL-13** | Panksepp's seven is the right number | **REJECTED (lit, READ)** as an empirical claim — see §7. **Costs nothing; he conceded it first** | same |
| **TL-14** | An absent drive is recoverable from an artifact | **OPEN.** The only proposal in this project that treats an absence as a measurable | scoped in `../sim/` batch four |

## §5. The forward predictions

**These are the claims the architecture makes that nothing else does. Each is a slot for hypotheses.**

**a. Trimodal, not bimodal.** Three loci with two troughs, not two loci with one dead middle.

**Superseded in its instrument, not in its content.** The depth sweep found the shape of the
affective-response profile across layers is **identical on intent-laden text and on no-maker text** —
a property of the architecture, carrying no information. **Both the bimodal claim and the two
hand-picked loci are dead.** What survived is the per-layer correlation with specified intent, which
two independently generated ladders agree on at 0.97. **The trimodal prediction is not thereby
confirmed; it lost the instrument that was going to test it.**

**And his 2026-08-07 route back in, which nobody has tried:**

> We're finding **ratio variance relationships between early and late** despite there being a peak in
> the middle. It implies a sort of shape that **I don't think anyone else has glommed on to.**

**A three-locus structure with a noisy middle would smear into a single mid-peak under any measure
that averages across position** — which is what every published depth profile does. **The way in is not
to test the peak but to test the residual:** fit a single-peak profile and ask whether what is left
over has structure at the early and late positions specifically. **A genuinely unimodal truth leaves
unstructured residual; a smeared three-locus structure leaves residual at exactly two places.**

**b. The middle is high-activity and low-coherence.** Not silent — *noisy*. A checkable signature, and
it distinguishes this from "the middle does nothing."

**c. Polish lives late; leakage lives early.** Testable against the surface measures we already have.

**d. Cognitive expertise is late.** *"Nearly everything you get out of text would be late."* With his
own caveat: motor expertise may be distributed, and he cannot speak to that from text.

**e. Late coherence should rise when the goal is clear.**

> You might also have more agreement in the late, **if the goal is clear.** What you get at the end is
> my guess. And the middle — yeah, it's convergent.

**So the coherence prediction is conditional rather than flat** — an interaction between depth and
legibility, and on the ladder that is directly testable.

**f. Why models never peak in the final layer.** The brain-alignment literature finds peak alignment at
middle depth, never at the end.

> They can't get through the middle layer to get to the final layer, so their final layer just kind of
> **randomly optimises upon the noise of the middle layer.**

**A failure of the middle propagates as noise into the top.**

**g. Is the first layer binary salience?** His question, 2026-08-07: *"the initial layer is binary
saliency, do you think?"* The adjacent literature finds affect **presence** dissociable from affect
**category** early — no sign, no intensity, just *something is here*.

**h. A layer-count ratio, offered as a guess.** That the ratio of parameters across a model's depth may
echo the ratio of neuron counts across receptor / midbrain / neocortex, because the model is
reconstructing that structure under a capacity constraint. **He flagged it as speculative.**

| # | hypothesis | status | evidence |
|---|---|---|---|
| **TL-15** | The depth profile is bimodal | **REJECTED (test).** Identical on no-maker text — architectural, no information | depth sweep, `FINDINGS.md` |
| **TL-16** | Per-layer correlation with specified intent carries information | **SUPPORTED (test).** Two independent ladders agree at 0.97 on which layers carry it | `results/layer_correlation/` |
| **TL-17** | The trimodal structure is recoverable in the *residual* after fitting a single peak | **OPEN, and it is his, 2026-08-07** | never run |
| **TL-18** | The middle layer is high-activity and low-coherence | **OPEN** — never isolated from TL-15's death | — |
| **TL-19** | Polish correlates with late-layer structure, leakage with early | **OPEN** | never run |
| **TL-20** | Late-layer coherence rises with how clearly the goal is specified | **OPEN, and the data already exists.** The depth sweep emits it; nobody has read the interaction out | free |
| **TL-21** | Layer 0 predicts emotional-versus-neutral well and *which* emotion at chance | **OPEN.** A specific double dissociation, about an hour to run | never run |
| **TL-22** | Parameter ratios across depth echo neuron-count ratios across receptor/midbrain/neocortex | **OPEN, flagged speculative by its author** | — |

## §6. The interpretability angle — the low-order to high-order ratio

**Moved here from [`THE_TRIANGLE.md`](THE_TRIANGLE.md) §6, where it never belonged: it is a claim about
depth, not about the three vertices.**

> Finding divergence between lower-level and higher-level activation as an AI processes text...
> **AI text would not trigger that lower-level activation as frequently.**

**Made precise:** reading **human** text should produce *more* low-order affective activation relative
to high-order than reading **machine** text does. **That is the leaked/emblematic ratio measured in the
reader**, and it has a specific reason to work that the displacement measure lacked — it is a **ratio
between two layers of the same reader on the same text**, so length, register and vocabulary largely
cancel.

**And his reading of what Anthropic found**, which does not dispute the finding but disputes the
interpretation:

> They're reading the valence and arousal layers and **interpreting those as lexical**, because there
> **is** a casual lexical mapping through the emotion wheel we all use. But what that emotion wheel is
> really doing is **defining and elaborating higher-order predictions and controls OF valence and
> arousal.**

So "early layers encode token valence" and "early layers reconstruct a valence/arousal assignment" are
the same observation under two readings, and **the emotion-word vocabulary is the interface between
them rather than the thing itself.**

| # | hypothesis | status | evidence |
|---|---|---|---|
| **TL-23** | The low-order/high-order ratio discriminates human from machine text | **REJECTED (test).** It keeps 99% of itself when every sentence is reordered, and tracks **register** — commercial copy sits a quarter of the way toward machine text | `FINDINGS.md` L1 |
| **TL-24** | The ratio falls as specified intent rises, where register is fixed by construction | **SUPPORTED (test), replicated, and it has passed every control we own** — held-out replication with settings frozen at −0.247 (*p* = 0.013), −0.405 length-controlled, and it survives the induction check at −0.26 (*p* = 0.009). **The only effect in this project that requires local word order** | `FINDINGS.md` L1 |
| **TL-25** | Affect directions exist in a reading model and are not word-counting | **SUPPORTED (test).** Four times chance, while a word-counting model scored exactly chance. Accuracy concentrated at two depths with a dead zone between | `FINDINGS.md` tier 2, `results/b` |
| **TL-33** | A reader moves further from its resting state for a human maker | **REJECTED (test).** −0.005, no effect. **A clean measure and a real null** — and it is the measure the layer ratio replaced. *Displacement from a resting state, in a model that has no self to be displaced from* | `results/wall` |
| **TL-34** | A reader refuses differently on human and machine text | **VOID (test).** Its pass condition was a coin flip — a 50% false-positive rate by arithmetic. **Not a negative result** | `results/refusal` |
| **TL-35** | Reader displacement varies more for machine text | **VOID (test).** Three artifacts | `FINDINGS.md` tier 2 |
| **TL-36** | The ratio moves in the same direction for revision as for specified intent | **REJECTED (test), and the sign is the interesting part.** On the ladder the ratio falls as specification rises; across drafts it **rises**. If both are real, **revising and being told more about the situation are different operations on a text, and the instrument distinguishes them.** Stated as a prediction from a *p* = 0.053 result and to be treated as one | `FINDINGS.md` L6 |
| **TL-37** | How much of the specification is recoverable from the artifact, in bits | **OPEN, and running.** Information recovered about the specification given topic, against topic-matched decoys. **This is the only measure that reports goal recovery on a scale rather than as a correlation**, which is what [`THE_TRIANGLE.md`](THE_TRIANGLE.md) TR-18's convergence-rate question needs | `results/spec_recovery` |

**A methodological correction worth keeping, because it was mine and it was wrong.** Offered as the
disanalogy that makes interpretability unlike an electrode in a brain, I wrote that neurons are
"plausibly natural units." He rejected it: *"that's grandmother-cell thinking and shit's vectorized."*
**He is right — population coding is the mainstream view**, and the disanalogies that actually hold are
the absence of a privileged basis in the residual stream, and the fact that interpretability scores
fail to distinguish a trained model from a randomly initialised one.

## §7. How many primitives — three questions, three answers

> Panksepp specifically noted he grabbed **the easiest ones**, the human-level identifiable ones. **By
> definition he missed a ton**, because the brain operates in a vector space that is hard for us to
> intuitively understand. **If you told me there were 27, I would believe you. Some of them might not
> even have names.**

And the methodological instruction that follows from it:

> **Let's not presume we can pre-PCA if we can't identify the six.** But if a PCA pops out a seventh,
> that makes the seventh really interesting.

**This is a stronger position than "the taxonomy is a design vocabulary."** It predicts a data-driven
decomposition *should* return more than seven, and that some components will be unnameable.

**Verified at source 2026-08-07, his "27, maybe 30" splits into three questions the field routinely
conflates:**

| the question | the answer | how strong |
|---|---|---|
| **primary-process subcortical channels** | **7. Nine is the most anyone has defended** — Toronchuk & Ellis add power/dominance and disgust, on review evidence rather than the stimulation and lesion work Panksepp demanded of himself, and call it a tentative proposal. LeDoux argues for **five**, with no anger circuit and no place for play or care | **nothing in neuroanatomy reaches 27, and nobody has tried** |
| **distinguishable reportable affective states** | **20–30, converging near 25** | **strong, and it survives the artifact objection.** Koide-Majima et al. raised the offered word list from 34 to **80** and the count did not inflate — 19 to 32 across subjects, median 25, recovered against **brain** data on held-out timepoints |
| **dimensions in the variance-explained sense** | **2 to 4** | Russell's two; Han & Adolphs' **three** from a subset of the very videos Cowen & Keltner got 27 from |

**His prior is well supported for the middle row and unsupported for the top one, and those are not
the same claim.**

**The relationship between the top and middle rows is his hypothesis and the field has never tested
it:** are ~25 states **blends of ~7 channels**, or are the 7 simply **the human-nameable subset of
~25**? *Panksepp's own remark about grabbing the easiest ones is that hypothesis.*

**One result arguing the 2D answer is a reporting bottleneck rather than the generator, and it comes
from the other camp** — Cacioppo & Berntson's evaluative space model, where positivity and negativity
are separable and can coactivate: *"Constraints on the output of any system do not necessarily require
that the internal mechanisms conform to the same structure."*

**A rank bound that appears to be unpublished as a critique.** Recovered dimensionality cannot exceed
the number of response variables, and **every count in this literature sits under its own item
ceiling** — 28 adjectives gave 2, 34 categories gave 24–27, 30 gave 24, 80 gave ~25. Keltner's group
makes this argument themselves and does not turn it on their own work.

| # | hypothesis | status | evidence |
|---|---|---|---|
| **TL-26** | An unsupervised decomposition of activations returns more than seven components | **VOID (test).** The criterion returned **335 components on pure Gaussian noise** and its answer doubled when the sample quadrupled. Not biased — broken | `FINDINGS.md` L8 |
| **TL-27** | Affect-isolated decomposition returns more than two components | **VOID (test).** Shuffling the emotion labels changed the count not at all, and the pipeline failed to reproduce published valence and arousal correlations. **Cause identified: found Reddit text confounds topic with emotion, so averaging over topics — the step that does the isolating — never happened** | `results/affect_dimensions/` |
| **TL-28** | ~25 distinguishable states are blends of ~7 channels, rather than 7 being the nameable subset of 25 | **OPEN, and never tested by anyone** | — |
| **TL-29** | Some recovered components will be unnameable | **OPEN.** Requires TL-27 to pass its controls first | — |

    Timeline on the count. First run reported 49.3 components and called it RICHER; the same code at a
    larger sample returned 92.9, and across five model families 73 to 116 with no convergence; a noise
    test then showed the criterion returns hundreds of components on data with no structure at all, so
    every number it produced is void. The replacement isolates affect the way the field does and
    failed its own shuffled-label control on the first run. **Nothing here currently supports or
    refutes the claim.**

## §8. The build — supply the missing middle

> If this structure is not what happens in naturally occurring language models, **I wonder if we could
> force it** — make an empathic bot with lower-order valence and arousal, medium human-mapped
> Pankseppian structures, and higher-order predictions and controls on those that are free-floating
> and subject to rapid change.

**This is the constructive version of the whole framework**, and it converts a measurement project into
an architectural one. **If the middle layer is where models fail to reconstruct human affective
structure, and if that failure is where misalignment comes from, then supplying the missing middle is
an intervention rather than an observation.**

**The weakness he names himself, and the bootstrap that answers it:**

> It's a weakness to the alignment consequence, because **we have to provide that weighting somehow.**
> It has to be based on... something? But at the very least it seems like all it needs is a
> **bootstrap.** You don't need a ton — a little bit would be enough to start the shape, to kick it
> off in the right direction.

**This is the strongest available answer to "whose values, and who decides."** If the mid-level
primitives only need to be *seeded* rather than *specified*, the design does not require anyone to
write down the value set — which [`THE_TRIANGLE.md`](THE_TRIANGLE.md) §6 establishes is impossible
anyway. **The bootstrap claim and the value-blindness claim fit together, and neither was stated with
the other in mind.**

**And a question he raised and deliberately deferred:** whether such an architecture would need
something thalamus-like to gate between the layers. Recorded, not pursued.

### What is needed is a generative model, not a state

The affective-computing literature's prescription is that a system needs *an internal state similar to
human emotion*. The stated goal is empathy **without** giving the machine emotions. **Those look
incompatible and I think they are not:**

> **You do not need interoceptive states. You need an interoceptive generative model.**

What simulation requires is the mapping *situation → predicted bodily state → emotion category*.
Running that forward as a **prediction about someone else** does not require instantiating the bodily
state. **A language model trained on human text plausibly has that mapping, because humans write the
mapping down constantly.**

Which is his own method described from the other side: *"the mechanism I use to tell how the author
felt is by **cycling through a few feelings and adjusting it a little bit until it fits** with what
they said."* **That is Simulation Theory, and a computational implementation exists — for faces.**

**Worth being honest about the limit:** the substrate may be unnecessary for *reading* and still
necessary for *caring*. **Nothing here bears on the second, and the second is the harder half of the
stated goal.**

| # | hypothesis | status | evidence |
|---|---|---|---|
| **TL-30** | Nobody has built a layered core-affect / discrete-emotion / constructed-emotion architecture | **SUPPORTED (lit, READ).** The 2025 *Artificial Emotion* survey states it explicitly. Ortony, Norman & Revelle described it in 2005 and it was never implemented. **Solms has publicly proposed it and it remains a proposal** | `../method/PANKSEPP_BARRETT.md` |
| **TL-31** | Reading another's affect requires no internal state, only a generative model of one | **OPEN.** Cheap test: can the probe predict *which affect a human reader will attribute* to an artifact? If yes, the substrate is not required for reading. If no, this project needs an architecture it does not have | never run |
| **TL-32** | The mid-level primitives need only seeding, not specification | **OPEN**, and it is the answer to "whose values" | a build |

**The field-level warning, and it applies to us first:** a survey of emotion in reinforcement learning
found *"we have not seen any test scenarios being borrowed from other emotion-learning
implementations."* **Everyone builds a bespoke gridworld and beats a strawman. Decide the fair
non-emotional baseline before building.**

---

## What this file says to do next

**Free — the data already exists and nobody has read it out:**

1. **TL-20 — late-layer coherence against rung.** The depth sweep emits the interaction.

**Cheap and never run:**

2. **TL-17 — the residual test for a smeared three-locus structure.** His, and nobody has looked.
3. **TL-21 — binary salience as a double dissociation at layer 0.** About an hour.
4. **TL-19 — polish against late structure, leakage against early.** Measures we already own.

**Blocking:**

5. **TL-27 needs topic-controlled generated stories, not found text.** Every count question in §7 is
   behind it.
