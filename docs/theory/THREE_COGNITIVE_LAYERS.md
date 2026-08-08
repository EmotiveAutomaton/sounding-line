# Three cognitive layers — the affective architecture a model is trying to reconstruct

> If human empathy relies on a **constraint of the solution space in the midbrain**, then we are going
> to have to similarly constrain the solution space somehow — or else we run into the impossibility of
> value extraction. **But if we can constrain the solution space sufficiently, we can get there**
> through a mechanism analogous to the empathy triangle.

> There are three layers. The three layers of human cognition through affective neuroscience will have
> some rough analog — **though softened** — in neural networks, because they are trying to model us
> using an imperfect version of our own mechanism for empathy, which is just inverse reinforcement
> learning with a whole bunch of tricks.

**The first theory in this file is that the mapping is already there.** That something in a model's
nodes already has the shape of the midbrain constraint, **and that we can amplify it** rather than
build it. Everything downstream — the bootstrap, the build, the whole alignment consequence — rests on
that being true.

**The load-bearing part is the middle**: a stage of conserved affective primitives that a model
reconstructs **badly**, because they are pre-verbal and never written down directly. **Where the
reconstruction fails is where the fingerprint is.**

---

## §1. The layers — and there are two competing orderings

### The original ordering, 2026-08-05

| depth | what it reconstructs | why | quality |
|---|---|---|---|
| **early** | **valence and arousal** | the lowest-level, most universal, most consistent thing in the training signal | **good.** Easiest to capture |
| **middle** | **midbrain-localised primitives** — the ancestral, baked-in affective systems | conserved across humans, so it is *there* in the data, but **pre-verbal and not directly expressed** | **bad, and noisily so.** The model struggles here |
| **late** | **expertise, and the goal direction that runs on it** | individual to the person | **chaotic.** A genuinely high-variance target |

> The middle one we wouldn't be able to converge upon... that's the part of the human brain that is
> baked in a little bit, that is a little bit more ancestral. **And it's struggling to model that.**
> So it uses valence-arousal mixed with some goal direction to get most of the way there. **But this
> is where its error comes from.**

> **The lack of Panksepp is where a lot of misalignment comes from, specifically. We have to give
> emotions in order to converge upon a more appropriate goal extraction.**

### The reordering, 2026-08-07

> It is possible that the **early layers are doing some kind of text transformation** — more like
> early sensory processing. And then the **middle layers have valence/arousal**, and the upper layers
> have **emotions attached**, or something like that.

**This is not a minor revision. It moves every layer.** And it reconciles two published results that
currently contradict each other outright:

| published result | what it would be reading, under the reordering |
|---|---|
| the mid-layer peak for emotion categories — the field's consensus | **valence and arousal**, sitting mid |
| a sparse-autoencoder study finding emotion features emerge **late**, after a syntax → semantics → emotion cascade | **the attached categories**, sitting late |

It also resolves the discomfort he flagged himself and called load-bearing:

> The prediction that early valence/arousal is what we're mapping — **it doesn't quite fucking fit.**
> Because the input for humans is **sensory** data. That's kind of what a model gets when it is boiled
> down into vectors, **but it's not quite the same.**

**The mismatch is specific.** A human's early layers receive *sensory* input and assign valence to it.
A model's early layers receive *tokens* — already symbolic, already the output of somebody else's whole
stack. **If early is text transformation rather than valence assignment, the analogy stops being
strained.** And he states the cost: *"it does break our theory to say so, and it makes it harder to
imagine setting up this conformance manually."*

### Where goal lives — expertise is the thing that is late, and goal runs on it

**Refined 2026-08-07, and it is more precise than the original.** The first version put "goal
direction" late. That was imprecise about both halves of the analogy.

> **Executive function is historically associated with goals** — with organising, with making
> sub-goals. Is the executive function applying the trajectory? Well, of course it is. **That's why
> goals come from the neocortex: because that's where your trajectory is stored.**

**So in humans, goal is not stored late. Trajectory is stored late, and goal is what executive
function does with it.** That is the same relation as [`THE_TRIPLE_INFERENCE.md`](THE_TRIPLE_INFERENCE.md)
§5 — *expertise × weighted policy map → actions* — seen from the neuroanatomy rather than from the
formalism.

**The precise version for models, in his words:**

> **Later layers of a model will have more expertise decoding and encoding capabilities.**

**That is the claim to test, and it is sharper than "goals are late"** — it is about *expertise*, which
we can supply and vary, rather than about *goal*, which we can only observe.

**And goal itself is not a layer.** He declined a fourth: *"that's just not reasonable. It wouldn't be
separable. Three, frankly, barely won't be."* The version that keeps three: **a goal is a weighting
applied across all of them** — already his own definition, where a goal is one component of the value
weighting temporarily amplified by attention. **If that is what a goal is, it does not need a depth of
its own; it needs to be readable as a modulation of whatever sits at each depth.** It also answers the
emotion-cannot-produce-output objection, because under that reading *nothing* at any single layer
produces output. **Agreed as fitting the theory better, and it costs no fourth layer.**

**Consistent with what he says about humans**, which was never the same as his claim about models:

> Goal direction comes from **all three** in humans. I would say middle and late are where you get
> most of it. **In AI I genuinely have no idea.**

| # | hypothesis | status | notables |
|---|---|---|---|
| **G20a** | Valence/arousal is reconstructed **early**, primitives **middle** | **OPEN**, and contested by G20b | The original ordering. Nothing has ever tested it directly |
| **G20b** | Early is text transformation, valence/arousal **middle**, categories **late** | **OPEN, and it discriminates cleanly against G20a.** Under G20a valence peaks early and categories mid; under G20b valence peaks mid and categories late | **It reconciles two literatures that currently contradict each other**, which no other version of the ordering does |
| **G41** | Later layers carry more expertise encoding and decoding | **OPEN**, and it is the precise form of "goals are late" | Expertise is suppliable and variable; goal is only observable. **This is the testable half of the pair** |
| **G26** | A goal is a weighting across all layers rather than a layer of its own | **OPEN**, adopted as the working position | It is the only version that keeps three layers and answers *an emotion cannot directly produce output* |
| **G27** | Layer boundaries in a model are soft rather than sharp | **assumed, not tested** | *"You're seeing ghosts of a human brain, not an actual human brain."* Any test requiring a clean boundary is testing the wrong thing |

**What these add up to.** Both orderings agree that **valence/arousal and the primitives are adjacent,
and that expertise sits at the far end from the input** — they disagree only about whether anything
sits *before* valence. **That is a narrower disagreement than it looks**, and §8's subspace result
bears on it directly: the one sharp boundary in the whole model is at layer 2, exactly where a
text-transformation stage would end. **If that boundary survives its control, G20b is the ordering and
the argument is over.**

## §2. The reframe that makes everything else follow

> When I say the model leaked involuntary affect, **I'm not assigning affect to the model.** It's that
> they're **trying to predict the human brain and failing to do so.** They're trying to have empathy
> and failing.

**A language model trained on human text is an attempt to model the process that produced it.** Its
architecture is not an emotional system; it is a *reconstruction* of one, built by prediction, and it
inherits the shape of what it is reconstructing — **including where the reconstruction is bad.** That
removes the implication that we are claiming a model has feelings, and it makes the **errors** the
interesting part.

> **You're seeing ghosts of a human brain, not an actual human brain.** [...] The lines will be
> **softer** on an AI modelling.

**So sharp layer boundaries are not expected, and their absence is not evidence against the
architecture.** The reason the structure should be there at all is twofold: **the model is built off
our brain structure, and it is modelling humans** — *"it has weak imperfect empathy. It is trying to
learn from us through this weak IRL."* And why that is uncomfortable: *"the only reason it's working is
raw brute force over a large enough set."*

**The end goal this serves:**

> My personal end goal is to find a way to **fully give AI human empathy, but not human emotions**
> [...] it requires some kind of subordinate solution space that converges on these **predictions of
> these interoceptive signals.**

## §3. The middle is the load-bearing claim, and it is where the industry is wrong

The audit recommended dropping Panksepp as a premise. I passed it on as a lead conclusion:

> This is an example of you trying to sand away a very important load-bearing column of this piece.
> **Panksepp in general may not be precise, but the idea of midbrain-localised solutions is absolutely
> load-bearing. If you drop that, we have what everyone else has, which is the wrong part.**

**What is load-bearing is not the taxonomy. It is midbrain-localised affective primitives of some
kind**, in an *expanded* set — the one vertex where he thinks the whole industry is wrong and this
project can be right. *"These primitives are the key, however many there are. I don't really care how
many there are."* And the reason to look there is strategic as well as theoretical: *"we have to look
where no one else is looking to make the whole picture make sense."*

**Terminology, a deliberate concession:** *"Emotions and feelings is fine. I've done emotions and
drives. [...] **Drives feels like a better word.** But I'll use whatever the literature has."* — use
*emotion / feeling* outward-facing, **drives** internally.

### You can only route attention onto drives you possess

> If I were forced to design a Nazi camp, part of my motivation would be not dying. But part would be
> **efficiency** — I could tap a need for efficiency to do this. **But I wouldn't be able to tap into
> the cruelty a Nazi designer would have. It just wouldn't be there for me to optimise.**

**Two makers producing the same artifact under the same instruction do it from different drives, and
the drives they lack constrain what they can produce. That makes the absent drive as informative as
the present one** — a mechanism for why an artifact reads as made-under-duress. **Unexplored, still
unnamed.**

| # | hypothesis | status | notables |
|---|---|---|---|
| **lit** | Midbrain-localised affective primitives exist as a distinct mid-level stage | **SUPPORTED (READ)** | **The strongest support cites neither camp** — hypothalamic line attractors encoding intensity and persistence (*Nature* 2024), conserved biphasic cross-species dynamics with a ketamine dissociation (*Science* 2025) |
| **lit** | The disagreement with Barrett is about localisation | **REJECTED (READ)** | Both camps place pattern generators in hypothalamus and PAG. **They disagree about whether activity there *constitutes* felt affect or is the output of a state assembled elsewhere — not an imaging question**, so it will not resolve on imaging |
| **lit** | Panksepp's seven is the right number | **REJECTED (READ)** as an empirical claim | The seven were never derived from a dimensional analysis, and **the standard instrument tests six, never seven** — LUST was dropped for social desirability |
| **S-14** | An absent drive is recoverable from an artifact | **OPEN**, scoped for the simulation | **The only proposal in this project that treats an absence as a measurable** |

**What these add up to.** The mid-level stage is better supported now than when this project started,
**and the strongest support cites neither Panksepp nor Barrett** — line attractors and conserved
cross-species dynamics were found by people not fighting this argument. **What both camps actually
agree on is that hypothalamus and PAG house coordinated affective machinery; they disagree about
whether that machinery constitutes felt affect or reports it.** So the architecture's structural claim
is uncontested and only its *interpretation* is in dispute — which means **imaging will never settle
it, and waiting for the debate to resolve is a mistake.**

## §4. How many primitives — three questions, three answers

> Panksepp specifically noted he grabbed **the easiest ones**, the human-level identifiable ones. **By
> definition he missed a ton.** [...] **If you told me there were 27, I would believe you. Some of them
> might not even have names.**

> **Let's not presume we can pre-PCA if we can't identify the six.** But if a PCA pops out a seventh,
> that makes the seventh really interesting.

**Verified at source 2026-08-07, "27, maybe 30" splits into three questions the field conflates:**

| the question | the answer | how strong |
|---|---|---|
| **primary-process subcortical channels** | **7. Nine is the most anyone has defended** — Toronchuk & Ellis add power/dominance and disgust on review evidence, and call it a tentative proposal. LeDoux argues for **five**, with no anger circuit and no place for play or care | **nothing in neuroanatomy reaches 27, and nobody has tried** |
| **distinguishable reportable affective states** | **20–30, converging near 25** | **strong, and it survives the artifact objection.** Koide-Majima et al. raised the offered word list from 34 to **80** and the count did not inflate — 19 to 32 across subjects, median 25, against **brain** data on held-out timepoints |
| **dimensions in the variance-explained sense** | **2 to 4** | Russell's two; Han & Adolphs' **three** from a subset of the very videos Cowen & Keltner got 27 from |

**His prior is well supported for the middle row and unsupported for the top one, and those are not the
same claim.** The relationship between them is his hypothesis and **the field has never tested it**:
are ~25 states **blends of ~7 channels**, or are the 7 **the human-nameable subset of ~25**?

**One result arguing the 2D answer is a reporting bottleneck rather than the generator, from the other
camp** — Cacioppo & Berntson's evaluative space model, where positivity and negativity are separable
and can coactivate: *"Constraints on the output of any system do not necessarily require that the
internal mechanisms conform to the same structure."*

**A rank bound that appears to be unpublished as a critique.** Recovered dimensionality cannot exceed
the number of response variables, and **every count sits under its own item ceiling** — 28 adjectives
gave 2, 34 categories gave 24–27, 30 gave 24, 80 gave ~25. **Keltner's group makes this argument
themselves and does not turn it on their own work.**

| # | hypothesis | status | notables |
|---|---|---|---|
| **L8** | An unsupervised decomposition of activations returns more than seven components | **VOID (test)** | **The criterion returned 335 components on pure Gaussian noise.** Not biased — broken. Its answer also doubled when the sample quadrupled |
| **L9** | Affect-isolated decomposition returns more than two components | **VOID (test)** | **Shuffling the emotion labels changed the count not at all.** Cause identified: found Reddit text confounds topic with emotion, so averaging over topics — the step that does the isolating — never ran |
| **G35** | ~25 distinguishable states are blends of ~7 channels, rather than 7 being the nameable subset of 25 | **OPEN** | **Never tested by anyone.** Both numbers are well established; the relation between them is empty ground |
| **G36** | Some recovered components will be unnameable | **OPEN**, behind L9 | If true it is the sharpest form of the claim, and the hardest to publish |

    Timeline on the count. First run reported 49.3 components and called it RICHER; the same code at a
    larger sample returned 92.9, and across five model families 73 to 116 with no convergence; a noise
    test then showed the criterion returns hundreds of components on data with no structure at all.
    The replacement isolates affect the way the field does and failed its own shuffled-label control.

**What these add up to. Every number in this literature, ours included, is a stopping-rule output.**
Seven came from one investigator's judgement; 24–27 from significance testing under a 34-item ceiling;
two from stopping when the circumplex appeared; 49 and 93 from a criterion that returns 335 components
on pure noise. **The one number that behaves differently is ~25** — raising the offered word list from
34 to 80 did *not* inflate it, and it was recovered against brain data rather than against more words.
**That is the only count in the field with a ceiling test behind it, and it sits far above seven.**
Which is his prediction, arrived at by someone else, for a quantity he was not claiming.

## §5. Leaked and emblematic — the affect vocabulary

> **leaked** — a layer that is TRUE... emotional leakage that can show up in your text
>
> **emblematic** — a conscious social decision

He arrived at that split from ten artifacts and a think-aloud, with no reference to the literature. **It
maps exactly onto the field's central unresolved debate:**

| his layer | the field's level |
|---|---|
| **leaked** | **Panksepp's primary process.** Core affect. Involuntary, conserved, pre-linguistic |
| **emblematic** | **Barrett's tertiary.** Constructed emotion. Conceptual, culturally learned, categorical |

**The reconciliation position, as the literature states it:** *basic emotion theories are theories of
**emotion**, while the theory of constructed emotion is a theory of **feeling**.* **The two-layer model
requires both to be true of different things**, which is where the reconciliation literature converged.

**It also means the two layers should not be assumed to share a value set** — Barrett's point is that
constructed categories are culturally variable while core affect is not. Giving both layers the same
eight values is a **named simplification**.

**And it diagnoses the field's LUST problem, which he called before the argument existed:**

> I think they were just catching the fact that leakage — they were assuming that **leaked fear and
> performed fear are the same thing.** [...] That's why lust is kind of bullshit in this framework,
> because **the easiest thing to catch is the performed section.**

**A questionnaire can only reach the tertiary level**, so LUST is the system least available to it —
for social rather than neural reasons. The instrument did not find LUST unmeasurable; it found it
**unreportable at the layer a questionnaire reaches**, then dropped the value. **Artifacts have no such
limit, and this is the clearest statement of what this project could contribute that the existing
instrument cannot.** Its signature is his: **the thing a reader politely glosses over** — *"someone
ends up talking about feet for a sentence too long and you're like, ooh, buddy."*

**No additions to the eight.** *"We shouldn't add anything, because that's kind of just where the
literature is right now."*

### Concealment: the shield matches the leak

**I had this backwards and he corrected it:**

> Leaked greater than emblematic **doesn't even count as concealment**... if anything the emblematic
> would get larger. **You perform louder to cover up. I get extra quiet if I'm extra angry. The shield
> matches the leak.**

**Concealment is not absence of display — it is display shaped *against* the leak.**

| # | hypothesis | status | notables |
|---|---|---|---|
| **S-3** | An involuntary leak channel is readable | **SUPPORTED (sim)** at 0.90 | — |
| **S-3** | Concealment shows as divergence between leak and display | **REJECTED (sim)** in that form | **His direction is the one that held**, against mine |
| **T-4** | Amplifying the display makes concealment *more* detectable | **SUPPORTED (sim)** | Survives a reader wrong about almost everything, **including a 50% channel swap** — but **fails at 25% concealment. It detects heavy concealers only** |
| **G28** | `leaked` and `emblematic` do not come back as the same distribution | **OPEN** | If their mean divergence is near zero, **the probe is answering one question twice** |
| **G29** | If one layer separates and the other does not, it will be **`leaked`** that fails | **OPEN, and predicted in advance** | Language encodes the tertiary layer — *that is what the words are* — while the primary reaches text only through leakage |
| **G30** | Attention-dwell past what the argument needs is measurable | **OPEN.** Nothing built | It is the LUST signature and a second leakage channel at once |

**What these add up to.** The leak channel is readable, and concealment is detectable **in the opposite
direction from the one I proposed** — the display gets *louder*, not quieter, and that held under a
reader wrong about almost everything including a 50% channel swap. **But it only catches heavy
concealers, failing at 25%**, which means the measure is reading *effort spent hiding* rather than
hiding itself. **And the two layers have never been shown to be two.** Until G28 runs, every result
here is equally compatible with the probe asking one question twice and averaging the answers.

## §6. The forward predictions

**a. Trimodal, not bimodal.** Three loci with two troughs, not two loci with one dead middle.

**Superseded in its instrument, not its content.** The depth sweep found the profile **identical on
intent-laden and no-maker text** — architectural, no information. **Both the bimodal claim and the two
hand-picked loci are dead.** What survived is the per-layer correlation, which two independent ladders
agree on at 0.97. **The trimodal prediction is not thereby confirmed; it lost the instrument that was
going to test it.**

**And his route back in, which nobody has tried:**

> We're finding **ratio variance relationships between early and late** despite there being a peak in
> the middle. It implies a sort of shape that **I don't think anyone else has glommed on to.**

**A three-locus structure with a noisy middle would smear into a single mid-peak under any measure that
averages across position** — which is what every published depth profile does. **The way in is not to
test the peak but to test the residual:** fit a single-peak profile and ask whether what is left over
has structure at the early and late positions specifically. **A unimodal truth leaves unstructured
residual; a smeared three-locus structure leaves residual at exactly two places.**

**b. The middle is high-activity and low-coherence.** Not silent — *noisy*.

**c. Polish lives late; leakage lives early.**

**d. Cognitive expertise is late.** *"Nearly everything you get out of text would be late."* With his
caveat: motor expertise may be distributed, and he cannot speak to that from text.

**e. Late coherence should rise when the goal is clear.** *"You might also have more agreement in the
late, **if the goal is clear.**"* — **conditional rather than flat**, an interaction between depth and
legibility.

**f. Why models never peak in the final layer.** *"They can't get through the middle layer to get to the
final layer, so their final layer just kind of **randomly optimises upon the noise of the middle
layer.**"* **A failure of the middle propagates as noise into the top.**

**g. Is the first layer binary salience?** *"The initial layer is binary saliency, do you think?"* The
adjacent literature finds affect **presence** dissociable from affect **category** early.

**h. A layer-count ratio, offered as a guess.** That parameter ratios across depth may echo neuron-count
ratios across receptor / midbrain / neocortex. **He flagged it as speculative.**

| # | hypothesis | status | notables |
|---|---|---|---|
| **L14** | The depth profile is bimodal | **REJECTED (test), and now across nine families.** **27 of 36 runs are unimodal**; multimodality appears only in gpt2-large and pythia-410m, **and in their no-maker runs too** | **The bimodal profile was a two-model artifact** |
| **L14** | The depth profile carries information about the maker | **RULED OUT (test).** Peak location is **identical between ladder and no-maker in every one of nine models** | **The peak sits at layer 2 of 29 in Qwen-1.5B and layer 47 of 49 in gpt2-xl**, with no relation to size or depth — **so no claim naming a specific depth transfers** |
| **L1** | Per-layer correlation with specified intent carries information | **SUPPORTED (test)** | **Two independently generated ladders agree at 0.97** on which layers carry it — the strongest replication in the project |
| **G22** | The trimodal structure is recoverable in the *residual* after fitting a single peak | **OPEN** | His, and **nobody in the field has looked for it** |
| **G31** | The middle layer is high-activity and low-coherence | **REJECTED (test, L25)** | Isolated from the bimodal profile at last: the signature appears in **2 of 25** maker-corpus sweeps. The modal pattern is the **opposite — a *quiet* middle** (12/25), the no-maker control shows the same distribution, and which pattern a model shows is set by its family. Architecture, not makers |
| **G32** | Polish correlates with late-layer structure, leakage with early | **OPEN** | Uses measures we already own on both sides |
| **G33** | Late-layer coherence rises with how clearly the goal is specified | **REJECTED (test) as universal; family-conditional form OPEN.** In Qwen coherence falls with rung at both ends; **in SmolLM2-360M it RISES at every band — the predicted direction**; gpt2 and pythia are positive early/middle, negative late | **The only near-universal: late-band coherence falls with rung in 3 of 4 families.** The Qwen middle-band null does not generalise. Readout code handed to the audit before this hardens |
| **G69** | The intent signal peaks deeper as rung rises | **REJECTED (test) in Qwen; OPEN as family-conditional.** Peak fixed at layer 2 in Qwen — but **SHIFTS deeper with rung in SmolLM2-360M and pythia-1.4b**, NOISE in gpt2 | **The rejection was premature.** Also: peak-of-magnitude and best-correlating-layer are different quantities and the first runner conflated them |
| **G21** | Layer 0 predicts emotional-versus-neutral well and *which* emotion at chance | **OPEN** | A clean double dissociation, and our corpus has neutral as a labelled category |
| **G34** | Parameter ratios across depth echo neuron-count ratios across receptor/midbrain/neocortex | **OPEN, flagged speculative by its author** | — |

**What these add up to.** The prediction that died and the prediction that replicated were the same
quantity read two ways: **the *magnitude* of affective response across depth is architectural and
carries nothing, while the *correlation* of that response with specified intent carries a signal two
independent ladders agree on at 0.97.** That is the most useful single thing in this file — **how much
a layer responds is noise; how much its response tracks the maker is not.** G31 now lands on the same
side (L25): the middle third's activity/coherence profile — mostly a *quiet* middle, not the
predicted noisy one — shows the same distribution on the no-maker control. Architecture again.

**The 2026-08-07 readouts sharpen that and cost the section two predictions.** The magnitude peak sits
at **layer 2 regardless of rung, in every ladder** — fully architectural, exactly as the profile
result said, and it does not move with intent (**G69**). And **coherence among the eight affect
concepts falls as specification rises**, replicated across three ladders, where the prediction was
that late coherence would *rise* when the goal is clear (**G33**).

**The direction is wrong but the pattern is informative, and the informative part is where it is
absent.** Early and late bands both lose coherence as intent rises; **the middle band does not move at
all, in any of the three corpora.** So specifying more intent makes the affect concepts *scatter* at
the ends and leaves the middle untouched — **which is a dissociation between the middle and the rest,
found by a test that was not looking for one, in the band this file says is load-bearing.** Whether
that is the noisy middle of §6b or an insensitivity of the coherence measure at that depth is not
something this run can say.

## §7. The interpretability angle — the low-order to high-order ratio

> Finding divergence between lower-level and higher-level activation as an AI processes text...
> **AI text would not trigger that lower-level activation as frequently.**

**Made precise:** reading **human** text should produce *more* low-order affective activation relative
to high-order than reading **machine** text does. **That is the leaked/emblematic ratio measured in the
reader**, and it has a reason to work that the displacement measure lacked — it is a **ratio between
two layers of the same reader on the same text**, so length, register and vocabulary largely cancel.

**And his reading of what Anthropic found**, disputing the interpretation and not the finding:

> They're reading the valence and arousal layers and **interpreting those as lexical**, because there
> **is** a casual lexical mapping through the emotion wheel we all use. But what that emotion wheel is
> really doing is **defining and elaborating higher-order predictions and controls OF valence and
> arousal.**

So "early layers encode token valence" and "early layers reconstruct a valence/arousal assignment" are
the same observation under two readings, and **the emotion-word vocabulary is the interface between
them rather than the thing itself.**

| # | hypothesis | status | notables |
|---|---|---|---|
| **L1** | The ratio falls as specified intent rises, where register is fixed by construction | **SUPPORTED (test), replicated, passed every control we own** — held-out at −0.247 (*p* = 0.013), −0.405 length-controlled, surviving induction at −0.26 (*p* = 0.009) | **The only effect in this project that requires local word order.** Length *hides* it rather than causing it — a suppressor, not a confound. **And under the rebuilt fair control (L23) it survives all three ladders at −0.42 to −0.52, every *p* ≤ 0.0004 — stronger after the control than before it** |
| **L1** | The ratio discriminates human from machine text | **REJECTED (test)** | **It keeps 99% of itself when every sentence is reordered**, and tracks register — commercial copy sits a quarter of the way toward machine text |
| **B-1** | Affect directions exist in a reading model and are not word-counting | **SUPPORTED (test)** | Four times chance while a word-counting model scored **exactly** chance. **Accuracy concentrated at two depths with a dead zone between** — the observation that started the whole depth programme |
| **L6** | The ratio moves the same direction for revision as for specified intent | **REJECTED (test)** | **The sign is the interesting part.** It falls with specification and **rises** with revision — so if both are real, *revising* and *being told more about the situation* are different operations and the instrument distinguishes them. From a *p* = 0.053 result, so treat as a prediction |
| **W-1** | A reader moves further from its resting state for a human maker | **REJECTED (test)** | −0.005. **A clean measure and a real null**, and the measure the layer ratio replaced — *displacement from a resting state, in a model that has no self to be displaced from* |
| **R-1** | A reader refuses differently on human and machine text | **VOID (test)** | Its pass condition was a coin flip — **a 50% false-positive rate by arithmetic** |
| **W-1b / L21** | Reader displacement varies more for machine text | **REJECTED (test) at n = 261.** All four corpora indistinguishable — displacement variance 0.209–0.216, *p* ≥ 0.71 against no-maker | **The informative null the three-artifact void could not supply.** Third confirmation: reader *state* carries nothing; within-text ratios do |
| **L10 / L19** | How much of the specification is recoverable, in bits | **SUPPORTED (test), scales with the manipulation, and now controlled.** Win rate against 48 decoys: **52.5% → 66.3% → 91.7%** as specifications go 10 → 10 → 60. **Shuffling the artifact–specification link collapses it to 1.3% against a 2.0% chance rate.** Doubling to 96 decoys costs 1.7 points while chance halves | **The curator disputed the earlier ruled-out verdict on grounds of manipulation strength and was right.** Echo correlation is **−0.236** — negative, so the artifact is not repeating the prompt. **The best-supported measure in the project** |
| **L12** | The per-layer intent correlation transfers across architectures | **SUPPORTED (test), and the control is the stronger half.** 25 ladder runs across **11 model families from 0.35B to 3B**: 18 survive. **11 no-maker runs: 11 DEAD, zero false positives** | **The failures cluster by family, not by scale** — gpt2-large is dead on all three ladders while pythia-410m and SmolLM2-360M, both smaller, survive. **That points at tokenizer or training data rather than capacity**, and it means any claim naming a specific layer is model-specific |

**What these add up to, and it is the most transferable lesson in the file.** The three reader-side
measures that died all asked whether the reader's *state* differed — displacement, refusal,
displacement variance — and a reader's state is not stable enough to carry a signal across texts that
differ in length, register and vocabulary. **The one that survived asks about a ratio between two of
the reader's own layers on the same text**, so those three confounds cancel before the measurement
happens. **Design reader-side measures as within-text ratios, or expect them to die.**

**And the two newest rows change how much weight the section carries.** Specification recovery
(**L10**) is the first measure here that reports goal recovery **on a scale rather than as a
correlation**, and it grew from ambiguous to a 91.7% win rate purely by strengthening the
manipulation — **which retroactively explains why the earlier ruled-out verdict was premature rather
than wrong.** The cross-architecture replication (**L12**) supplies the control the whole programme
needed: **eleven no-maker runs across eleven families, all dead.** A measure that reads labels rather
than text would have fired somewhere in eleven attempts. **What neither supplies is transferability
of the *location*** — the surviving layers move by model and by corpus, so the measure generalises and
the address does not. **L10 has not yet been given the no-maker control that made L12 credible**, and
until it is, the strongest new result has one fewer control than the one beside it.

**A methodological correction worth keeping, because it was mine and it was wrong.** I offered "neurons
are plausibly natural units" as the disanalogy that makes interpretability unlike an electrode. He
rejected it: *"that's grandmother-cell thinking and shit's vectorized."* **He is right — population
coding is the mainstream view**, and the disanalogies that hold are the absence of a privileged basis
in the residual stream, and the fact that interpretability scores fail to distinguish a trained model
from a randomly initialised one.

## §8. The live worry — is there a structure to amplify at all?

**2026-08-07.** Everything in this file assumes a model has *some* human-shaped affective structure to
find, and §9's build rests on being able to amplify it rather than construct it.

> I do worry that there are no three layers in AI node structures at all. [...] Part of what they're
> doing is modelling at some depth our limbic system, because we consistently converge into that
> shape. But it's not necessarily going to have anything like human input and output.

**What it costs if he is right.** *"I was hoping the work would get done for us a little bit."* If
there is no general shape, the intervention has to **impose** structure rather than amplify it, and
the bootstrap becomes a far more manual build.

**The evidence against:** our depth sweep found the profile identical on intent-laden and no-maker
text (**L1**); a 2026 study finds valence encoding emerging at very different depths per architecture;
and the affect-dimension run returned 42.8 components on an untrained model against 1.0 on the trained
one of identical shape.

**The evidence for, 2026-08-07.** We checked whether a coherent affect subspace exists across four
model families — 360M to 1.5B, three architectures. **It does, sitting four to six times above a
matched random null even between the most distant layers, at a rate consistent across families.**

**That is weak evidence for the three-layer structure and it does not settle the worry.** It says
there is *something* coherent to find. It does not say the something has three parts, or that its
parts correspond to anything in a midbrain.

**Superseded — one candidate explanation, tested and rejected.** That the three layers might be three
*subspaces* of the residual stream rather than three depths. **The subspace rotates with depth**, so
that is not what is happening.

| # | hypothesis | status | notables |
|---|---|---|---|
| **G40** | There is a coherent affect subspace at all, consistent across families | **SUPPORTED (test).** 4-6x its null at maximum layer distance, in every family | **The rotation rate is consistent across families even though the magnitude profile is not** — so it was the profile that was the wrong measure, not the idea |
| **G42** | The affect subspace is organised in three bands | **REJECTED (test) as equal thirds.** A two-way split at **layer 2** beats any three-band split in all four families; distance alone explains 69-81% of the alignment matrix | **The one strong break is very early**, where G20b puts the text-transformation boundary. But see G43 |
| **G43** | The layer-2 break is affective, not an artifact of proximity to the embedding | **OPEN, and it gates how G42 reads** | Cheap. Needs a non-affective control subspace measured identically |
| **G39** | The three layers are subspaces rather than depths | **REJECTED (test)** | — |

**Reading them together: there is one coherent affective structure, it rotates continuously through
depth rather than sitting in bands, and its one sharp boundary is at the very front of the model.**
That is a shape, and it is a consistent one — but it is not yet the shape this file claims.

## §9. The build — supply the missing middle

> If this structure is not what happens in naturally occurring language models, **I wonder if we could
> force it** — make an empathic bot with lower-order valence and arousal, medium human-mapped
> Pankseppian structures, and higher-order predictions and controls on those that are free-floating and
> subject to rapid change.

**The constructive version of the whole framework**, and it converts a measurement project into an
architectural one. **If the middle is where models fail, and if that failure is where misalignment comes
from, then supplying the missing middle is an intervention rather than an observation.**

> It's a weakness to the alignment consequence, because **we have to provide that weighting somehow.**
> [...] But at the very least it seems like all it needs is a **bootstrap.** You don't need a ton — a
> little bit would be enough to start the shape, to kick it off in the right direction.

**This is the strongest available answer to "whose values, and who decides."** If the mid-level
primitives only need to be *seeded* rather than *specified*, the design does not require anyone to
write down the value set — which the triple inference establishes is impossible anyway. **The bootstrap
claim and the value-blindness claim fit together, and neither was stated with the other in mind.**

**A question raised and deliberately deferred:** whether such an architecture needs something
thalamus-like to gate between the layers.

### What if it is the shape and not the location? — 2026-08-07

**A reframe of the build, and it follows directly from §8.** The subspace result says a coherent
affective structure exists but **rotates continuously through depth** rather than sitting where the
architecture predicts. The obvious reading is that we have the wrong architecture. **His reading is
that we may have the wrong target.**

> What if it's not the **location** of where they are, but rather their **shape** that we need to care
> about? What if the values are somehow **extractable and repositionable as meta-concepts**? They'd
> have to change depending on where they are in the hierarchy. **Could we force them to be in a layer
> we think is correct and then strengthen them?**

**Why this is a different build from §9's.** The bootstrap as stated supplies *content* — seed the
mid-level primitives and let training shape them. **This supplies *position*:** take the affective
structure the model already has, and move it. **If the structure is real but badly placed, then the
intervention is relocation and reinforcement, not construction** — and that is a far smaller build
than the one §9 describes.

**It also changes what the rotation means.** A structure that rotates through depth is a structure
whose representation is *depth-dependent* — the same concept written differently at different layers.
**If that transform is recoverable, the concept is repositionable by construction**, because
repositioning is applying the transform.

**And it gives the live worry a second test.** *"Is there evidence of worse models having more poorly
placed emotional concepts?"* **If placement is something a model gets better at, placement is a
capability rather than an architecture** — which would mean the structure is not innate to the shape
of the network, and the amplification story needs a scale story attached.

| # | hypothesis | status | notables |
|---|---|---|---|
| **G44** | The depth-dependent transform of the affect subspace is recoverable | **OPEN.** If the same concept is written differently at each layer and that mapping can be fitted, **repositioning is applying it** | The alignment matrix from §8 already contains the data to fit it — we measured the *amount* of rotation and never the *rotation itself* |
| **G45** | An affective concept can be forced into a chosen layer and strengthened there | **OPEN, and it is the build.** Relocation and reinforcement rather than construction | **A much smaller build than §9's** if it works, and it needs G44 first |
| **G46** | Weaker or smaller models place affective concepts more poorly | **OPEN, and it is a second test of §8's worry.** If placement improves with capability, **placement is learned rather than architectural** | We already hold four families spanning 360M to 1.5B and have not asked this of them. **Cheap** |

**What these add up to.** Nothing has been run, but the three are ordered: **G46 is free and decides
whether placement is a property of the network or of training; G44 is the measurement that makes G45
possible; G45 is the build.** And G46 has the useful property of being informative in both
directions — **if placement does not improve with scale, that is evidence the structure is
architectural, which is the strongest thing §8 could return.**

### What is needed is a generative model, not a state

The affective-computing literature says a system needs *an internal state similar to human emotion*.
The stated goal is empathy **without** giving the machine emotions. **Those look incompatible and are
not:**

> **You do not need interoceptive states. You need an interoceptive generative model.**

What simulation requires is the mapping *situation → predicted bodily state → emotion category*.
Running it forward as a **prediction about someone else** does not require instantiating the bodily
state. **A language model plausibly has that mapping, because humans write it down constantly.** Which
is his own method from the other side: *"the mechanism I use to tell how the author felt is by cycling
through a few feelings and adjusting it a little bit until it fits."*

**The limit, honestly:** the substrate may be unnecessary for *reading* and still necessary for
*caring*. **Nothing here bears on the second, and the second is the harder half of the stated goal.**

| # | hypothesis | status | notables |
|---|---|---|---|
| **lit** | Nobody has built a layered core-affect / discrete-emotion / constructed-emotion architecture | **SUPPORTED (READ)** | The 2025 *Artificial Emotion* survey states it explicitly. **Ortony, Norman & Revelle described it in 2005 and it was never implemented; Solms has publicly proposed it and it remains a proposal** |
| **G37** | Reading another's affect requires no internal state, only a generative model of one | **OPEN** | Cheap: can the probe predict *which affect a human reader will attribute*? If no, **this project needs an architecture it does not have** |
| **G38** | The mid-level primitives need only seeding, not specification | **OPEN** | It is the answer to "whose values", and **it depends on G39** — you cannot seed a structure that is not there to seed |

**What these add up to.** The layered architecture is unclaimed on the survey's own word, was described
in full in 2005, and the one public proposal to build it remains a proposal. **Twenty-one years of
nobody doing it is either a large opportunity or a signal that the hard part is somewhere we have not
looked** — and §8 says the hard part is not *finding* the structure, because a coherent affective
structure is present in every model we have checked. **What is unproven is that it can be seeded
rather than specified**, and that is the single claim the whole build rests on.

**The field's own warning applies to us first** — *"we have not seen any test scenarios being borrowed
from other emotion-learning implementations."* **Everyone builds a bespoke gridworld and beats a
strawman. Decide the fair non-emotional baseline before building.**

### There is no positive channel, and that is a gap rather than an omission

**Noticed 2026-08-07.** The eight concepts this project reads are **Panksepp's seven plus
`none_recoverable`** — the *no maker-affect legible* class. **There is no happiness channel and no
positive-valence channel.**

> Happiness is often modelled as one of two things: either **positive valence of those need
> networks**, or as **a conjoined channel that all seven of them have to not be inhibiting** in order
> for happiness to flow.

**Neither is represented.** Positive affect is currently distributed across seeking, play and care by
implication, and never measured as such. **The two models he names are architecturally different** —
one is a readout over the seven, the other is a gate requiring all seven to be un-blocked — **and they
make different predictions about what should happen when a single channel is suppressed.** Under the
readout account, suppressing one channel moves the positive signal a little. Under the gate account,
suppressing any one channel should collapse it.

| # | hypothesis | status | notables |
|---|---|---|---|
| **G73** | Positive affect is a readout over the seven channels | **OPEN** | Suppressing one channel should move it proportionally |
| **G74** | Positive affect is a conjoined gate requiring all seven to be un-inhibited | **OPEN** | **Suppressing any single channel should collapse it** — a sharp, cheap dissociation between the two accounts |

**What these add up to.** Nothing has been run and the channel does not exist in our instrument, **so
every affect reading this project has produced is blind to positive affect except where it leaks
through seeking, play or care.** That is a real limit on the eight-concept design rather than a
refinement of it, and **the two accounts are separable by a single suppression experiment**, which
makes this cheaper to settle than most things in this file.
