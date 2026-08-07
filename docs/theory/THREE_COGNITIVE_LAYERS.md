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

## ⚠ The live worry — and one candidate way out

**2026-08-07.** The whole architecture assumes a model has *some* human-shaped affective structure to
find.

> I do worry that there are no three layers in AI node structures at all. [...] Part of what they're
> doing is modelling at some depth our limbic system, because we consistently converge into that
> shape. But it's not necessarily going to have anything like human input and output.

**What it costs if he is right.** *"I was hoping the work would get done for us a little bit."* If
there is no general shape, the intervention has to **impose** structure rather than amplify it, and
§8's bootstrap becomes a far more manual build.

**The evidence currently runs against us:**

- our depth sweep found the profile identical on intent-laden and no-maker text — architectural,
  carrying no information (**L1**);
- a 2026 study finds valence encoding emerging at **very different depths per architecture** —
  early-then-collapse in one family, late-progressive in another;
- the affect-dimension run returned **42.8 components on an untrained model against 1.0 on the trained
  one of identical shape**. Both void, and that gap is unexplained.

### The candidate solution: three subspaces, not three depths

**Superseded — proposed 2026-08-07, tested the same day, and rejected. Kept because the reasoning
is what produced the measurement that answered the worry.** The result is immediately below.

**Proposed 2026-08-07 and agreed as worth testing.** We assumed depth-in-the-network maps onto
depth-in-the-brain because both look like processing stages. **A transformer's computation is strictly
ordered — that part is not in doubt.** What is in doubt is whether *abstraction* is partitioned along
that ordering, because **every layer reads from and writes to the same residual stream.** There is no
anatomical separation between stages the way there is in a brain.

**So affect appearing throughout the layers is not evidence against three layers. It is evidence that
layer index may not be where the structure lives.**

**If the three layers exist as three *subspaces of the residual stream* rather than three depths:**

- everything measured so far has been on the wrong axis;
- **it explains why the depth profile is architectural and carries no information, while the per-layer
  *correlation* does** — the correlation would be picking up subspace overlap that happens to vary
  with depth, not depth itself;
- it survives the softness limit below, because a subspace has no reason to respect a layer boundary.

**And it changes what the bootstrap is.** If the relations are present but unlocalised, the model has
the map without the terrain, and supplying shape is about **binding** existing structure rather than
**amplifying** localised structure. A different build, and a more tractable one than imposing an
architecture from scratch.

### What the check returned — 2026-08-07, four model families

**Run the same day it was proposed.** Fit the affect directions at every layer, take the subspace they
span, and compare subspaces across depth by **principal angles** — 1.0 is identical, 0.0 orthogonal.

| model | adjacent layers | most distant layers | random-subspace null |
|---|---|---|---|
| GPT-2 medium | 0.852 | 0.399 | 0.074 |
| Pythia 1.4B | 0.800 | 0.290 | 0.052 |
| SmolLM2 360M | 0.779 | 0.274 | 0.076 |
| Qwen 2.5 1.5B | 0.751 | 0.305 | 0.060 |

*How much the affect subspace at one layer overlaps the affect subspace at another. "Adjacent" is
neighbouring layers; "most distant" averages pairs at least half the model's depth apart. The null is
matched random subspaces of the same dimension in the same width.*

**Three things follow and they do not all point the same way.**

**1. The subspace proposal is rejected.** The subspace **rotates with depth** — 0.80 between
neighbours falling to 0.32 at the far end. It is not one fixed subspace threaded through the stream,
so layer index *is* where some of the structure lives, and the original architecture survives on that
axis.

**2. The worry is not confirmed, and this is the load-bearing part.** At **maximum layer distance the
subspace still sits four to six times above its null**, in every family. **There is a coherent affect
subspace and it is not an artifact of adjacency. The structure is there to amplify.**

**3. The strongest boundary sits at layer 2, in all four families.** Sweeping every possible two-way
split, the split that best separates within-group from across-group alignment is the same one
everywhere — **layers 0-1 against everything else** — and it beats any three-equal-band split
(gap 0.27-0.38 against 0.21-0.26). **That is where G20b puts the text-transformation boundary.**

**The caveat on point 3, and it is real:** the first layers of any model sit next to the embedding and
are atypical for reasons that have nothing to do with affect. **A boundary at layer 2 may be trivially
true rather than evidence for the reordering.** Separating those two readings needs a non-affective
control subspace measured identically, and that has not been run.

**Beyond layer 2 it is mostly smooth.** A model using only layer *distance* explains **69-81%** of the
alignment matrix, leaving 19-31% that distance does not account for. **That is not three bands. It is
a continuous rotation with one early break, and some residual structure nobody has looked at.**

| # | hypothesis | status | notables |
|---|---|---|---|
| **G39** | The three layers are subspaces of the residual stream rather than depths | **REJECTED (test).** The subspace rotates with depth: 0.80 adjacent, 0.32 most-distant | **Proposed and killed the same day.** The bootstrap stays an amplification problem, not a binding one |
| **G40** | There is a coherent affect subspace at all, consistent across families | **SUPPORTED (test).** Four to six times its null at maximum layer distance, across 360M to 1.5B and three architectures | **This is the answer to the worry.** The rotation *rate* is consistent across families even where the magnitude profile is not — the shape is real, and it was the profile that was the wrong measure |
| **G42** | The affect subspace is organised in three bands | **REJECTED (test) as equal thirds.** A two-way split at **layer 2** beats any three-band split in all four families | **The one break is very early**, which is where G20b puts the text-transformation boundary — but see G43 |
| **G43** | The layer-2 break is affective rather than an artifact of proximity to the embedding | **OPEN, and it gates how G42 reads** | Needs a non-affective control subspace measured identically. **Cheap, and it decides whether we have evidence for the reordering or a well-known property of layer 0** |

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
function does with it.** That is the same relation as [`THE_EMPATHY_TRIANGLE.md`](THE_EMPATHY_TRIANGLE.md)
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

**Where this leaves the ordering.** Two orderings, one discriminating test, and **neither has been
run** — the runner that would settle it exists and its first pass was void. **G41 is the more valuable
of the pair to run first**, because expertise is a variable we control and goal is not, and because a
positive there constrains both orderings at once.

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

**Where this leaves the middle.** The structural claim is in better shape than it was in 2017 and it is
supported by work that does not use Panksepp's framework at all. **What is not supported is the
number** — which costs nothing, because he conceded the taxonomy first and the architecture never
depended on it.

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

**Where this leaves the count. Nothing here currently supports or refutes the claim, and that is the
honest summary of two days of work.** The one durable thing learned is methodological and it now
applies project-wide: **run a measure on data whose answer you already know before running it on data
whose answer you don't.** Reproducing the field's own numbers is a precondition, not a formality —
**we cannot argue past their stopping criterion until we can hit their result with their method.**

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

**Where this leaves the two layers.** The vocabulary is in better shape than the measurements: **the
split is the field's own reconciliation position and he arrived at it independently**, but the null
that would show our probe is not answering one question twice has never been run. **G28 should come
before anything that reports the two layers separately**, and it has not.

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
| **L1** | The depth profile is bimodal | **REJECTED (test)** | **Identical on no-maker text.** The no-maker corpus is the control that killed it, and it killed the two hand-picked loci with it |
| **L1** | Per-layer correlation with specified intent carries information | **SUPPORTED (test)** | **Two independently generated ladders agree at 0.97** on which layers carry it — the strongest replication in the project |
| **G22** | The trimodal structure is recoverable in the *residual* after fitting a single peak | **OPEN** | His, and **nobody in the field has looked for it** |
| **G31** | The middle layer is high-activity and low-coherence | **OPEN** | Never isolated from the bimodal profile's death, so it has never actually been tested |
| **G32** | Polish correlates with late-layer structure, leakage with early | **OPEN** | Uses measures we already own on both sides |
| **G33** | Late-layer coherence rises with how clearly the goal is specified | **OPEN, and the data already exists** | **The depth sweep emits this interaction and nobody has read it out.** Free |
| **G21** | Layer 0 predicts emotional-versus-neutral well and *which* emotion at chance | **OPEN** | A clean double dissociation, and our corpus has neutral as a labelled category |
| **G34** | Parameter ratios across depth echo neuron-count ratios across receptor/midbrain/neocortex | **OPEN, flagged speculative by its author** | — |

**Where this leaves the predictions.** **One is dead, one is the project's best-replicated result, and
six have never been run.** The pattern is worth naming: the two that were tested were the two that
needed no new machinery, and **the six untested ones are untested because each needs a different
readout of data we already have.** That is a reporting gap rather than an experimental one — G33 in
particular is sitting in a file on disk.

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
| **L1** | The ratio falls as specified intent rises, where register is fixed by construction | **SUPPORTED (test), replicated, passed every control we own** — held-out at −0.247 (*p* = 0.013), −0.405 length-controlled, surviving induction at −0.26 (*p* = 0.009) | **The only effect in this project that requires local word order.** And length *hides* it rather than causing it — a suppressor, not a confound |
| **L1** | The ratio discriminates human from machine text | **REJECTED (test)** | **It keeps 99% of itself when every sentence is reordered**, and tracks register — commercial copy sits a quarter of the way toward machine text |
| **B-1** | Affect directions exist in a reading model and are not word-counting | **SUPPORTED (test)** | Four times chance while a word-counting model scored **exactly** chance. **Accuracy concentrated at two depths with a dead zone between** — the observation that started the whole depth programme |
| **L6** | The ratio moves the same direction for revision as for specified intent | **REJECTED (test)** | **The sign is the interesting part.** It falls with specification and **rises** with revision — so if both are real, *revising* and *being told more about the situation* are different operations and the instrument distinguishes them. From a *p* = 0.053 result, so treat as a prediction |
| **W-1** | A reader moves further from its resting state for a human maker | **REJECTED (test)** | −0.005. **A clean measure and a real null**, and the measure the layer ratio replaced — *displacement from a resting state, in a model that has no self to be displaced from* |
| **R-1** | A reader refuses differently on human and machine text | **VOID (test)** | Its pass condition was a coin flip — **a 50% false-positive rate by arithmetic** |
| **W-1b** | Reader displacement varies more for machine text | **VOID (test)** | Three artifacts |
| **L10** | How much of the specification is recoverable, in bits | **OPEN, running** | **The only measure that reports goal recovery on a scale rather than as a correlation**, which is what the convergence-rate question needs |

**Where this leaves the reader-side programme.** Four measures read out of the reader; **three died and
one replicated.** The three that died all shared a shape — they asked whether the reader's *state*
differed, and state is not stable enough to measure. **The one that survived asks about a *ratio
between two of the reader's own layers on the same text*, which cancels what killed the others.** That
is the generalisable lesson, and it should constrain every future reader-side design.

**A methodological correction worth keeping, because it was mine and it was wrong.** I offered "neurons
are plausibly natural units" as the disanalogy that makes interpretability unlike an electrode. He
rejected it: *"that's grandmother-cell thinking and shit's vectorized."* **He is right — population
coding is the mainstream view**, and the disanalogies that hold are the absence of a privileged basis
in the residual stream, and the fact that interpretability scores fail to distinguish a trained model
from a randomly initialised one.

## §8. The build — supply the missing middle

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
write down the value set — which the empathy triangle establishes is impossible anyway. **The bootstrap
claim and the value-blindness claim fit together, and neither was stated with the other in mind.**

**A question raised and deliberately deferred:** whether such an architecture needs something
thalamus-like to gate between the layers.

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

**Where this leaves the build.** The ground is unclaimed on the survey's own word, the closest
theoretical match is twenty years old and unimplemented, and **the only precedent is a proposal.** What
gates it is not novelty but G39: **whether there is a structure to amplify at all.** And the field's own
warning applies to us first — *"we have not seen any test scenarios being borrowed from other
emotion-learning implementations."* **Everyone builds a bespoke gridworld and beats a strawman. Decide
the fair non-emotional baseline before building.**
