# Three cognitive layers: the latent architecture, and what a model reconstructs of it

> If human empathy relies on a **constraint of the solution space in the midbrain**, then we are going
> to have to similarly constrain the solution space somehow. That's the only way we can get closer to
> actual value extraction, given the intractability of the problem. **We can get there through a
> mechanism analogous to empathy that I'm calling the triple inference.**

> There are **three functional levels** of human cognition, which correlate with the three brain
> regions described in affective neuroscience. We'll have some similar analog – **though softened** –
> in neural network blocks, because they're trying to model us using an imperfect version of our own
> mechanism for empathy, which at the end of the day is just **inverse reinforcement learning with a
> whole bunch of tricks**.

> We're not assuming that there's a similar three-level structure. We expect to find some types of
> commonalities that we can elaborate on as **a vertex for exploration**, much like the proposed
> triple inference process of empathy itself.

Four claims, stated separately because they live or die separately:

1. **Human proposal.** Core affect/salience, drive constraints, and expertise-conditioned
   construction are distinct functional levels of one system.
2. **Model proposal.** A next-token model may *reconstruct* aspects of those functions, without
   feeling anything.
3. **Load-bearing prediction.** The drive constraints are reconstructed *worst*, because they are
   conserved but under-expressed in text; the shape of that error is a large source of failed goal
   inference.
4. **Current verdict.** Coherent affect geometry exists in every model checked; three depth bands
   do not; dose *tracking* exists and transfers; and abstract affect is decodable; one rank-one
   intervention was inert, while a different additive intervention steered valenced continuations.
   Neither result establishes improved maker inference.

**This file owns** the latent architecture: what human structure exists, what a model might
reconstruct, where reconstruction fails, and what intervention could follow. **It does not own** the
artifact-facing traces ([`DECISION_TRACES.md`](DECISION_TRACES.md)), the inference itself
([`THE_TRIPLE_INFERENCE.md`](THE_TRIPLE_INFERENCE.md)), or the alignment consequence
([`ALIGNMENT.md`](ALIGNMENT.md)). Per the program (2026-08-09) this file is **instrument research**:
its open question is whether any model quantity improves recovery of recorded choices, and it
supports the artifact criterion rather than becoming the criterion.

---

# Part I: The theory

## §1. The human functional scaffold

| function | what it is | quality of the training signal |
|---|---|---|
| **core affect / salience** | valence and arousal, the lowest-level, most universal thing in the signal | good; easiest to capture |
| **drive constraints** | the ancestral, conserved affective systems | present but **pre-verbal, never written down directly** |
| **expertise-conditioned construction** | trajectories, higher-order predictions and controls, the goal machinery that runs on them | individual, chaotic, high-variance |

The middle row is a provisional functional aggregate (2026-08-21). A conserved affective
channel may combine an inherited action-selection prior with a state-dependent
motivational signal; that possible split is owned by
[`THE_TRIPLE_INFERENCE.md`](THE_TRIPLE_INFERENCE.md) §4 and remains unresolved, and it
must not be turned into a clean anatomical or transformer address.

**The proposal isolates the conserved, pre-solved contribution to a larger distributed system.
It does not claim that an emotional episode lives only in the subcortex. Cortical construction,
learned expertise, context, and focal control can vary substantially between people while
conserved subcortical affective and action-control machinery still narrows the candidate
trajectories available to a human reader. That narrowing function, rather than anatomical
exclusivity, is the load-bearing claim.**

> The middle one we wouldn't be able to converge upon... that's the part of the human brain that is
> baked in a little bit, that is a little bit more ancestral. **And it's struggling to model that.**
> So it uses valence-arousal mixed with some goal direction to get most of the way there. **But this
> is where its error comes from.**

> **The lack of Panksepp is where a lot of misalignment comes from, specifically. We have to give
> emotions in order to converge upon a more appropriate goal extraction.**

**Goal is not a fourth level.** He declined one. *"That's just not reasonable. It wouldn't be
separable. Three, frankly, barely won't be."* And it is not an alias for attention either *(the
2026-08-30 pass folded out the file's earlier identity prose, "goal = the attention-promoted
region")*:

> Proximal goal is not identical to attention. I think the relationship between proximal goal,
> attention, and expertise is complex and interesting in a way that we have been glossing over.

*2026-08-30 assessment; spoken wording lightly reconstructed.*

A proximal goal is a locally governing control target selected under values, drives, context,
expertise, and attention; its effects can be expressed through every functional level. Other
motivations may remain as maintained intentions or learned constraints without governing focal
control. Goal is therefore not a fourth address, but neither is it identical to the attention
allocated while pursuing it.

**Expertise is weighted late, and goal reads through it:**

> **Executive function is historically associated with goals** – with organising, with making
> sub-goals. Is the executive function applying the trajectory? Well, of course it is.

> Goals don't just come from the neocortex. That was me overstating an initial thought, which is
> that they may be **weighted at the later levels**, higher brain regions, and maybe even later
> blocks. Even though executive function and learned competence both contribute to goals, **there's
> no single anatomical address** for these things. But you would expect a more accurate weighting
> with respect to observed behaviors, because they've passed through the expertise layer.

> Later blocks are probably going to make expertise-related information **more usable or decodable**
> in some way. There's just a lot more of it in general. And you'd expect more goal-related
> information to be somehow associated with the actual process itself.

> The actual answer is the constraint on the trajectory. It's a constraint on not a learned policy,
> but a trajectory. That's what expertise is, right?

> The active goal is where your attention is focused. And so if you take a moment in the middle of
> the sentence – you might write something that's pretty elegant, and it comes to your attention that
> with a little bit of effort it could be beautifully elegant – all of a sudden your attention is
> focused on maximizing that for a moment because it's been elevated and pulled your attention to
> it. And so sometimes those things can become active goals. For the most part, however, they are
> distortions in the possibility space caused by your expertise.

His strong candidate for what that structure is a record OF *(the 2026-08-30 pass; held as
candidate, canonically narrowed just below rather than adopted as an identity)*:

> Expertise is a record of your previous attentional strategy.

> Expertise is an imperfect record of previous attention given prior context. Consolidation is
> the encoding layer for that record; interference contributes noise.

*2026-08-30/31 walkthroughs; spoken wording lightly reconstructed. The earlier shorthand
remains historical evidence; the second statement narrows its identity claim without removing
the example.*

> The transition model is just expertise. You can already have expertise when you walk up to
> something; that is one of the pieces that changes the rest of the equation.

> All the times you have been in a situation like this, what did you choose to attend to, and what
> decisions did you make while attending to it? That is what expertise compresses.

> If you make those decisions repeatedly, your expertise bends in a different direction. You become
> your choices in a lot of ways.

*2026-09-01 walkthrough; spoken wording lightly reconstructed.*

> Finding the things that are actually interesting about the thing requires the full ability to
> encapsulate the expertise. That is probably why children's drawings are only interesting to their
> parents: all of the interesting things about them are expressions of that child, and the parents
> deeply analyze that.

*2026-09-04 walkthrough; lightly cleaned transcript.*

Expertise is the precondition for seeing the maker: without the standard process a reader has nothing
to be surprised by. The child's-drawing case sits in tension with the essay's account of where
interest lives, since there the interesting things are the child's own expressions read by a
reader whose expertise is in the child rather than in drawing; the tension is recorded OPEN and is the
curator's to resolve.

Expertise is the maker's learned transition model, the structure through which all three
functional levels can constrain action; a realized process is one path through it, and neither
is identical to any one depth, to conscious executive control, or to a stored policy. A reader
may arrive with domain expertise before seeing the artifact, which changes the rest of the
equation without recovering the episode's path. The curator's live FORMATION hypothesis is that
expertise is a lossy, consolidation-transformed record of prior attention and choice under
prior context, not an intact historical log: practice, feedback, and instruction shape what is
attended and repeated; constraints, tools, opportunity, and embodiment define the context in
which that attention occurred; consolidation is encoding and compression, and interference and
forgetting are error. Transfer and unequal learning change which contexts and repetitions bear
on the present case; they do not require a separate object beside expertise. Repeated choices
reshape the later transition model, which is the sense in which a maker becomes their choices.
Goal selection and attention allocation remain distinct operations: the same attended material
can produce different expertise, and the same expertise can later direct attention away from
the current goal; a background concern can deform the reachable trajectories without becoming
the focal goal, and when attention promotes it, it becomes an active proximal goal while
automaticity pre-solves lower-level control so focal attention can operate elsewhere. The
formation hypothesis is circular unless attention is measured independently of its later
effect on expertise. Calling expertise "compiled decision structure" (the 2026-08-21 pass)
describes its formation history, not intact storage of past decisions. The functional object
remains the trajectory constraint.

Expertise can be expressed at mechanics, technique, and purpose levels. Media literacy is one
high-level entry competence, not the definition of expertise. The transition map spans the
hierarchy: brush control can make metaphorical control reachable, and conceptual expertise can
redirect lower-level execution. Which portion is visible depends on the task, tools, medium, and
reader. In humans goal direction draws on all three levels. *"I would say middle and late are
where you get most of it. **In AI I genuinely have no idea.**"*

**The scaffold has a known gap, the missing positive channel.** The eight concepts read are
Panksepp's seven plus `none_recoverable`, with no happiness and no positive valence as such:

> Happiness is often modelled as one of two things: either **positive valence of those need
> networks**, or as **a conjoined channel that all seven of them have to not be inhibiting** in order
> for happiness to flow.

Both are candidate modelings rather than a claimed dichotomy. What positive affect actually is
there would come out of the data, not out of an initial musing on one specific channel; the
suppression experiment below separates these two without excluding others.

**The candidate affective contribution is active and state-dependent, not an inventory that must
all be present at once.** At a given moment one or a small changing mixture of conserved
motivational or action-tendency constraints may alter salience, feasible trajectories, and
tradeoffs during reconstruction. The weights, mixtures, and even the right functional basis are
open. Decoding a label does not show that the constraint participated in the computation, which
is why causal intervention during inference is required. Conversely, a lack of recoverable
emotional language does not identify absent affect, low attention, low care, or low total neural
activity; expression, internal state, and computational use are separate variables.

Human goals can genuinely drift while attention relocates, but neither movement entails the
other, and surface movement is not sufficient evidence of goal drift. The same persistent
concern can appear and disappear as opportunity and expertise change its local expression. The
curator's live control candidate is one foreground goal with rapid switching; maintained
intentions and compiled habit can still alter behavior while another goal is focal, and
concurrent control remains a rival. Serial switching is therefore a candidate description of
focal control, not a frozen mechanism.

| # | hypothesis | status |
|---|---|---|
| **G26** | A goal is a weighting across all levels rather than a level or attention state of its own | **OPEN, adopted as the working position** |
| **G41** | Later blocks make expertise-related information more usable or decodable | **OPEN.** The testable form of the late-weighting restatement; expertise is suppliable and variable |
| **G27** | Level boundaries in a model are soft rather than sharp | **assumed, not tested.** Any test requiring a clean boundary is testing the wrong thing |
| **G73** | Positive affect is a readout over the seven channels | **OPEN.** Suppressing one channel should move it proportionally |
| **G74** | Positive affect is a conjoined gate requiring all seven un-inhibited | **OPEN.** Suppressing any one should collapse it; a single suppression experiment separates the two |
| **C-S6** | A bounded reader recovers which control architecture governs a constructed maker (one foreground goal with switching, maintained intention, compiled habit, concurrent control) from the order of work | **VOID AS CURRENT EVIDENCE FOR THE NAMED CLAIM (Stage 7 D01 to D06, L330).** The event reader and the controller comparison inherit hidden future and generator-law dependencies; no architecture recovery, controller comparison, or switching conclusion is licensed; the reader-free construction fact stands: the strict switcher leaves more hanging section-writes than the concurrent controller, opposite the declared direction (C06, CLEAN) |
|   | | *(this row's history is NARROWED on the Stage-6 block, L316 and L322, then voided by the 2026-09-02 dependency audit, L330)* |
| **A-S6** | A bounded reader reads the discriminating event on constructed makers whose expertise history (a practiced skill) or current goal governs it, and reads dated history as such | **VOID AS CURRENT EVIDENCE FOR THE NAMED CLAIM (Stage 7 D01 to D06, L330).** The event and changed-context reads inherit the common predictor's privileged state; the dated-history contrast does not validate the rest of the family; no Stage 6 attention-history, expertise-versus-goal, or changed-context inference is licensed; the reader-free construction fact stands: dated-versus-shuffled history separates nowhere at scale on the exact layer (−0.03 [−0.15, +0.10] on 1248 fresh units, A13/x5, CLEAN) |
|   | | *(this row's history is SPLIT on the Stage-6 block, L315 to L325, then voided by the 2026-09-02 dependency audit, L330)* |
| **E-S7** | Expertise is a cross-episode record a reader can use: the transition model carried in the maker's earlier work informs the reading of a new episode | **SUPPORTED for the law, NARROWED for the state (test, L342, L345).** The law fitted by likelihood from three earlier episodes transfers to an untouched one at the oracle's level (+0.64 [+0.22, +1.12] over the domain model), and one reader proposes it usably from the same demonstrations with every other factor supplied (+0.56); with two episodes in view and nothing supplied, the reader that fails cold fails the same (1.75 nats [0.4, 3.4] under the domain model) while committing on every world, so the demonstrations carry the law and not the belief, goal, or residue |
| **V-S7** | A trained automatic capture (a compiled habit) is separable from a current costly redirection (a present goal that opposes it) in a maker's visible record | **NARROWED (test, L354), 40 worlds crossed.** The joint reader names the habit on 56 percent of worlds (the most nameable withheld factor of the run) and the goal on 24, and its executed pairs sit under the domain model where the goal opposes the habit (−0.37 [−0.73, −0.02] pooled) and where it does not (−0.33 [−0.82, +0.07]) alike, so the compiled record shows through the prefix and the redirection is not read; with context and competence matched and only the present goal withheld (V02), the goal is worth half a nat to the oracle and the reader's proposed goal is worth less than none (−0.33 [−0.59, −0.09] against a solver that averages the four standard goals); with the law and the goal both withheld and a lagging expertise crossed against the present goal (V03), the reader names neither (law recall 0 on both readers, the goal on 3 and 25 percent of worlds) and its committed pairs cost 0.77 [0.13, 1.39] nats against the domain model where the expertise opposes the goal and 0.45 where they align, so the lagging expertise is invisible to a prefix reader and the conflict shows only in the arm's error; on a dated series under a drifting law a mixture over the dates and a forced point date predict the present episode alike (V04, −0.01 [−0.09, +0.07], programs only), the mixture's mass two thirds on the present-law episodes; for a held-out later episode the dated series, the ordered undated series, and an aggregate profile of the earlier episodes predict alike (V05, valid nulls: order over aggregate +0.04 [−0.03, +0.12], dates over order +0.00), so the earlier episodes' order and dates carry nothing their aggregate does not at this drift; for a later costly choice the dated trajectory carries the law (+0.42 [+0.05, +0.84] over the domain model, +0.48 over the solver without it) and nothing beyond the aggregate (V06, +0.05 [−0.02, +0.11]) |

**What the table says.** The scaffold itself is theory, and its surviving content is about
expertise rather than about any reader: expertise is the transition model through which the
levels constrain action, repetition reshapes it, consolidation compresses the record of prior
attention and choice into it, and interference corrupts that record; a reader may bring
expertise of its own, and what it must infer on the spot is the proximal goal. The scaffold's
one adopted position (a proximal goal as the currently governing local control target,
expressed through every level; goal, attention, and expertise distinct but coupled, no pair
identical) and its one testable sharpening (late blocks making expertise more decodable, with
no single anatomical address claimed) have never been run, and every affect reading the
project has produced is blind to positive affect except where it leaks through seeking, play,
or care, with the two positive-affect rows held as candidate modelings rather than an
exhaustive pair. The expertise-formation account is logic only. The two Stage-6 rows are void
as reader evidence: their numbers were produced through a realizer that read the hidden world
(C-S6, A-S6), and what survives of them is construction fact, that the four control candidates
can be built to share endpoints and differ in order, that the strict switcher leaves more
hanging writes than concurrent control, and that dated-versus-shuffled history separates
nothing at scale on the exact layer. The serial-switching candidate therefore stays a candidate
discriminated by construction and by no reader; whether any reader recovers a control or
history factor behind a boundary it cannot cross is asked again in Stage 7 (K11 to K13, V01 to
V06). The first of those answers is in (V-S7, L354): the compiled habit is the one withheld factor
a reader names on half the worlds, and the present goal that would override it is not named, so
the record shows through the prefix and the redirection does not. The cross-episode claim has its first exact-layer measurement (E-S7): the law is in the
maker's earlier episodes and transfers, a program recovers it at the oracle's level and one
small reader proposes it usably, and that is all the earlier episodes carry, since the same
demonstrations do not rescue a reader that fails on the belief, the goal, and the residue
cold. The walkthrough adds the precondition the scaffold had left implicit: seeing the maker requires
the expertise to run the standard process first, which Stage 8 installs by training and gates before
any reading claim, with the child's-drawing tension left open. Confidence: untested, logic only, for the scaffold and the formation account; the two
construction facts are exact-layer facts on one construction family; the Stage 6 reader
instrument is instrument-dead.

On mirror systems *(the 2026-08-22 pass)*:

> I do not think mirror neurons are magic. It is more like: I see your eyebrows move, I understand
> how my eyebrows would move in that situation, and from that I can extrapolate how I might feel.

> My understanding of mirror neurons is that they're kind of like physical bootstraps to this whole
> process. [...] I don't know what the relationship is between these physical mirrorings and the
> concept of valence assignment.

*2026-08-27 walkthrough; spoken wording lightly reconstructed.*

**Action observation may constrain candidate actions without recovering the maker's valuation.**
Macaque mirror responses can depend on the value the observer associates with an object; human
sensorimotor training can alter a mirroring response. These findings support interacting action
and valuation processes, not a transfer of the actor's feeling or a wholly fixed bootstrap. A
final artifact can constrain possible movements without recording their exact history. This
remains a possible input to reconstruction, not a validated layer map or a requirement to adopt
the full Thousand Brains architecture. The current text experiments do not measure this biological
route. ([Caggiano et al., 2012](https://iris.unime.it/handle/11570/3251500);
[Catmur, Walsh, and Heyes, 2007](https://kclpure.kcl.ac.uk/portal/en/publications/sensorimotor-learning-configures-the-human-mirror-system/);
institutional abstracts read. Catmur's human measure was TMS, not individual mirror-neuron
recording.)

## §2. The reconstruction bridge: what a model is doing, in reserved words

> When I say the model leaked involuntary affect, **I'm not assigning affect to the model.** It's that
> they're **trying to predict the human brain and failing to do so.** They're trying to have empathy
> and failing.

> They're not automatically trying to empathize; that's speaking in high-level terms. Practically,
> because they're trained on human-produced text, you'd expect them to **reconstruct the functional
> regularities of the generating process** that led to it. I'm recontextualizing the concept of
> empathy as, at least somewhat, **a form of inverse reinforcement learning**. I'm not assigning
> affect to AI at this time.

> **You're seeing ghosts of a human brain, not an actual human brain.** [...] The lines will be
> **softer** on an AI modelling.

> That's what I mean by ghosts of a human brain. An **imperfect reconstruction of functional aspects
> of human anatomy**, or expertise and experience, perhaps even distributed.

A language model trained on human text may reconstruct functional regularities of the processes
that produced its training data strongly enough to support some human-shaped inferences. The
current evidence establishes decodable geometry and tracking behavior, not that the model
reproduces the human generative mechanism. "Ghosts of a human brain" remains the curator's
organizing hypothesis, not an architectural finding. The errors are the interesting part.
For Phase 2.3, "human generative prior" has only a functional meaning (2026-08-21): a model
supplies candidate human-coherent processes that improve recovery of facts withheld from the
candidate-generation step. Fluent mental-state labels and a plausible rationale do not count;
the ablation compares this prior against target-specific context, a surface baseline, and no
generative prior, and a gain confined to the artifact-producing family is family familiarity,
never a human generative model.

**Phase 2.4 treats maker-reader model-family similarity as a tractable analogue of the shared-
organization shortcut. Exact-checkpoint, sibling-family, and cross-family readers are crossed
against the same recorded process choices. A same-family gain is not evidence for the human
mechanism unless it survives surface, tokenizer, capacity, and generation-fingerprint controls;
even then it establishes a model analogue, not biological identity.**

**Reserved vocabulary, because "layer" had come to mean four different things:**

    functional level   what a stage DOES, in the human theory (core affect, drives, construction)
    region             anatomy -- subcortical structures, neocortex
    block              a transformer layer, by index
    subspace           representational structure WITHIN blocks -- channels, directions, geometry

"Layer" without a qualifier is banned in this folder. And two grounded cautions from the
commissioned analogue research ([`../method/NEURAL_ANALOGUES.md`](../method/NEURAL_ANALOGUES.md)).
**Nothing in a dense transformer can "peak" in the energy sense**, since every block spends
identical compute, so only decodability varies, and cross-domain claims must compare decoding to
decoding (the field's own move, since univariate bright-peaks failed for emotion there too). And
**"noise" has no biophysical referent at temperature zero**, so say *unmodeled variance*, and treat
rogue dimensions as the artifact class, not the signal. **Token transformation is an input
adapter**, the model-side counterpart of sensory transduction, not a fourth cognitive level. And
the search target is stated deliberately loosely:

> We are trying to find **any kind of correlates that could be explored or used functionally** to
> help identify value data. That may include finding a mapping space for valence and arousal, or
> even for sensory transformation, though that's unlikely, because the most likely crossover is
> **textual embedding and transformation being equivalent to sensory transduction in humans**. Past
> that, you would expect **a sort of convergence, and that's what we're seeking more than
> anything.** An affective reconstruction that appears after that initial transformation. Not that
> it's a natural thing, but that humans do it and we are the source data, and therefore **ghosts of
> it would appear**.

**The two orderings are competing model *mappings*, not competing definitions of cognition.** The
question is where each function is reconstructed in blocks, given where it lives in regions:

| # | hypothesis | status |
|---|---|---|
| **G20a** | Mapping A: core affect reconstructed in early blocks, drive constraints mid | **REJECTED (test, L87), eleven families, gates clean.** Valence decodability sits near 0.8 at almost every depth; prominences hover at the flatness threshold; peak locations scatter 0.17 to 0.71 with no law |
| **G20b** | Mapping B: early blocks are the input adapter, core affect mid, categories late | **REJECTED (test, L87), the same sweep.** No family matches either band pattern; the question dissolves the way every address claim here has, into flat curves over a rotating structure |
| **G34** | Parameter ratios across depth echo neuron-count ratios across regions | **WITHDRAWN, misattributed.** The suggestion on record was to *build* structures mapped this way; it was never a prediction that current models show it |

**What the table says.** The two mappings are now measured and neither exists: affect
information is spread nearly uniformly through depth in every family checked, which is what
the rotating-subspace picture (§5) already implied and the address rejections (§6) already
rehearsed. One universal did fall out: a beyond-lexicon component, the original-text probe
pulling ahead of a lexicon-preserving shuffle, exists in all eleven families with its onset
obeying no law, so composition is real everywhere and addressable nowhere. The bridge itself
(reconstruction-without-feeling) remains the file's working frame rather than a tested claim.
Confidence: the mapping rejections are replicated and controlled at eleven families; the
beyond-lexicon universal is one bad test away, one corpus and one shuffle condition deep.

**Why the middle would be the latent variable behind the machine-text unease**, the derivation
that used to sit with the traces. The unease has four candidate accounts (broken polish-effort,
flattened intent, missing translation, wrong shape), and his objection to the list was the point.
*"Now we have a proliferation of reasons... this list seems more like the **observable variables**."*

> **The latent variable is the midbrain misalignment that I suggest.** It could absolutely be simply
> a **poor reconstruction of conserved drive constraints**, the goals that arise from the midbrain.
> Those are the drives to which I refer.

If a model reconstructs everything *except* the mid-level drive constraints, it has no shared prior
with the reader, and each account is that absence seen from a different angle. Whether that is
right is a real question and not assumed. *"That doesn't sound right. That doesn't sound right at
all... I don't know, they're tied in there somehow."* The test is whether the four dissociate.

## §3. The missing middle: the load-bearing prediction

Stated formally, in his words:

> Nonverbal drive constraints from Panksepp are systematically underdetermined from human text, so
> that when a model reconstructs them, it has worse access to them than surface affect or learned
> expertise, both of which are more accessible as they are closer to the later layers of output in
> the human brain. **The shape of this reconstruction error for the model is a large source of
> failed goal inference.**

Three consequences make it testable rather than atmospheric. **Absent drives are constraints.** You
can only route attention onto drives you possess, so a drive the maker lacks bounds what they can
make (the artifact-side face of this lives with the traces; the alignment face in
[`ALIGNMENT.md`](ALIGNMENT.md)). **The predicted error is *specific*.** Drive ambiguity should
produce a distinctive goal-inference failure while surface affect, category, and expertise reads
stay intact; that fingerprint experiment is what keeps this from collapsing into generic emotion
probing, and it has never been run. **And the prediction prices the middle.** Reconstruction should
be measurably worse there than at either end, once "there" can be located at all, which Part II
shows is the hard part.

| # | hypothesis | status |
|---|---|---|
| **S-14** | An absent drive is recoverable from artifacts | **SUPPORTED (sim, V11) as method; OPEN on real artifacts.** Near-invisible in spontaneous work (0.61), perfect under commission toward the missing channel (1.00), pure compliance collapses to exactly 0.5, so *how the goal is pursued* is the discriminator. The made-under-duress mechanism, first working form; real commissioned work is the missing half |

**What the table says.** The prediction's first mechanism check exists only in simulation, where it
behaves exactly as the theory wants. Absence reads, and reads through pursuit rather than content.
Confidence: sim-only; the real-artifact claim is untested.

# Part II: The evidence

## §4. Human evidence: conserved machinery, and how many primitives

| # | hypothesis | status |
|---|---|---|
| **lit** | Conserved **subcortical affective control machinery** exists as a distinct stage | **SUPPORTED (READ).** The strongest support cites neither camp. Hypothalamic line attractors encoding intensity and persistence (*Nature* 2024), conserved biphasic cross-species dynamics with a ketamine dissociation (*Science* 2025). *Anatomical honesty: that evidence is hypothalamic and PAG, subcortical rather than specifically midbrain, and the machinery being coordinated is uncontested while its reading as a separable affective-primitive stage is not* |
| **lit** | The Panksepp-Barrett disagreement is about localisation | **REJECTED (READ).** Both camps place the machinery in hypothalamus and PAG; they disagree on whether activity there *constitutes* affect or reports it, so imaging will not settle it |
| **lit** | Panksepp's seven is the right number | **REJECTED (READ) as an empirical claim.** Never derived from a dimensional analysis; the standard instrument tests six |
| **G35** | A numerical ceiling on reportable affect categories should govern basis design | **WITHDRAWN AS A DESIGN HEURISTIC (curator, 2026-08-24).** Roughly 27 no longer functions even as a soft ceiling. A 27-label language taxonomy may appear only as an external, dimension-matched comparator. Panksepp's seven remains a theory-derived candidate vocabulary, not a dimensional result or privileged count |
| **G36** | Some recovered components will be unnameable | **OPEN**, behind a working count instrument |
| **L8 / L9** | Our own two counting attempts | **VOID / INSTRUMENT DEAD (L8/L9/L15).** A criterion that returned components from noise, then a rebuilt instrument with four confirmed defects. This project holds no count of its own |

On the former count heuristic *(the 2026-08-22 pass; superseded in scope 2026-08-24)*:

> When I say 27, I am treating that as a soft upper bound, not anything precise. I do not know how
> they came up with it, but they certainly did not use Panksepp's method. If they arrived at it
> behaviorally, they probably also captured some cortical, Barrett-style emotions.

**Supersession note.** The quotation is retained as the historical source of G35. Its live
disposition is withdrawn. The current theory holds no soft ceiling near 27 and does not treat a
behavioral language taxonomy as a candidate subcortical inventory. The working candidate basis
may be closer in kind to Panksepp's functional systems, but neither seven nor any other count is
licensed as the natural dimensionality.

**What the table says.** Conserved subcortical affective control machinery has strong published
support, while no component count has privileged standing here. Panksepp's seven were not derived
by dimensional decomposition, and the former 27 ceiling has been withdrawn even as a basis-design
heuristic. Fixed named banks remain legitimate competing constructions when their provenance and
interpretation are declared; none may be announced as the natural emotion count. The project's
own two counting instruments contributed no evidence, and component counting is not a Phase 2.4
objective. Confidence: the machinery is replicated and controlled in the published record; every
count relation here is rejected, withdrawn, untested, or instrument-dead.

## §5. Does a corresponding model structure exist?

| # | hypothesis | status |
|---|---|---|
| **G40** | A coherent affect subspace exists, consistent across families | **SUPPORTED (test).** Four to six times its matched null even between the most distant blocks, in **all eleven families**, 0.35B to 3B, four architectures. The rotation *rate* is consistent where the magnitude profile never was |
| **G42** | The subspace is organised in three bands | **REJECTED (test, L31) as equal thirds.** A two-way split at the earliest boundary beats any three-band split, in the original four families and in all eleven on the extended check |
| **G43** | The early break is affective rather than an input-adapter artifact | **REJECTED (test, L49), all eleven families, unanimous.** Topic, syntax, and frequency subspaces measured identically all snap at the same block the affect subspace does, in every family. The boundary is the input adapter's edge and carries no mapping information. The gate he set resolves in the deflationary direction |
| **G44** | The depth transform of the subspace is recoverable | **OPEN (L31), first bite landed.** Alignment *composes* lawfully in pythia (R² 0.88 to 0.92) and gpt2 (0.78 to 0.84), weakly in SmolLM2, **not in Qwen (0.20 to 0.30)**. Fit the transform where it is lawful, and note the home family is the outlier again |
| **G46** | Weaker models place the structure more poorly | **NO DETECTED RELATIONSHIP (test, L30), n = 11.** Placement quality against parameter count sits at rho +0.05 across eleven families in the 0.35B to 3B range. Eleven points cannot prove scale irrelevant, so "architectural, not learned" was the stronger unlicensed form; what stands is that placement gave no sign of tracking capability where measured |
| **G39** | The three levels are subspaces rather than depths | **REJECTED (test).** The subspace rotates with depth |

The rank-dilution caveat that rode all these numbers is retired (L50). Rank-truncated bases against a
distant-matched null reproduce the rotation in all eleven families (adjacent blocks share
0.78 to 0.96 of the subspace, distant 0.21 to 0.42, chance ~0.05) with no verdict flips anywhere.

**What the table says.** There is one coherent affective structure; it rotates continuously
through depth rather than sitting in bands; its placement gave no sign of tracking scale where
measured; and its rotation is lawful enough to fit in some families. Its one sharp boundary,
though, has lost its meaning. Every content type measured (topic, syntax, frequency) snaps at the
same front block, so the break is the input adapter's seam and says nothing about affect. **What
remains is a consistent shape that is not yet the shape this file claims**, because nothing ties
the structure to drives, to the middle, or to any causal role, and its one candidate landmark just
proved generic. Confidence: existence, rotation, the adapter-edge rejection, and the
repaired-basis confirmation are replicated and controlled at eleven families each; the scale
non-relationship is one bad test away at eleven points; what the structure *means* remains gated
on causality.

## §6. Address versus tracking: the two umbrellas the predictions became

### Address: specific jobs at specific depths

The bet was that if the three levels are real in a model, *where* things sit should itself be
diagnostic. The route back in for the three-locus version, nobody having tried it:

> We're finding **ratio variance relationships between early and late** despite there being a peak in
> the middle. It implies a sort of shape that **I don't think anyone else has glommed on to.**

| # | hypothesis | status |
|---|---|---|
| **L14** | The depth profile carries information about the maker | **REJECTED (test).** The profile is identical (or within one block) with and without a maker, in every family; the peak sits anywhere from block 2 of 29 to 47 of 49 with no relation to size |
| **G22** | A smeared three-locus structure is recoverable in the *residual* after fitting one peak | **OPEN on real models; the instrument has an operating regime (sim, V11).** The smear is architectural. A planted three-locus world reads as one mid peak in 100% of runs *and* 100% of reparameterisations, so published mid-peak profiles are uninformative against a three-locus truth. The residual statistic separates the worlds at AUC 0.87 in 25% of parameterisations, which is **feasibility in a bounded regime, not universality** |
| **G31** | The middle is high-activity and low-coherence | **REJECTED (test, L25).** 2 of 33 runs; the modal pattern is a *quiet* middle, identically on maker-less text |
| **G69** | The dose signal peaks deeper as rung rises | **REJECTED (test).** The apparent shifts were two near-tied fixed loci trading rank; regenerated verdicts show fixed peaks in all eleven families |
| **G21** | Block 0 is a pure salience gate, presence without category | **REJECTED (test, L27/L38/L51) at power, all eleven families, including the home-family half-survival.** Presence is near-flat through every stack (block 0 within a few points of the best block everywhere), so the scattered "peak locations" were argmaxes of level curves, the home block-0 peak included; and block 0 carries category at 8 to 9× chance in every family. **No model has a presence-only stage at its front door** |
| **L14** | The depth profile is bimodal | **REJECTED (test).** 27 of 36 runs unimodal; the exceptions are two families and appear in their no-maker runs too |
| **G124** | Aligned by computational events rather than depth fractions, the loci land somewhere lawful across families | **SUPPORTED for the late locus, softened for the early (test, L45/L58, with its null).** The late landings (62 to 83% depth) survive text-correspondence breaking in all four decidable families, so the deep alignment is carried by shared per-text computation. The early landings survive the null only where it is tight and are reproduced by smoothness in both gpt2 members, since early blocks match early-to-early even for mismatched texts. SmolLM2's null spans the stack and decides nothing, the odd family again. Thirty texts, one corpus; and the sanity audit (L61) showed raw similarity magnitudes are uninterpretable at this sample-to-dimension ratio (independent noise scores 0.98), so only the null-tested match structure ever carried weight here |
| **G126** | The maker-blindness of the profiles survives translation into defensible units | **SUPPORTED (test, L48), all eight families.** Write norm, signed affect work, and probe signal-to-noise per block, QC-clean throughout. The write/work geography is near-identical with and without a maker at every block, and concentrates at the input edge universally. Discriminability placement obeys no law, early at both Qwen sizes and scattering early-to-late across the others with size reversing direction between families; **the home family's early placement, where this project's loci were chosen, is the exception rather than the rule** |

**What the table says.** Where things sit in a model is a fact about the model, not about the
maker. The profile ignores the maker, the peak never moves with dose, the middle is quiet, and
the last candidate for a portable address died at power, since presence is flat through every
stack and never category-blind, so there is no salience gate anywhere, the home family included.
But the addresses that refuse to transfer as raw block numbers do translate. Aligned by what the
blocks compute, the early and late events land at lawful relative depths in almost every family
(G124), so cross-family claims can be stated at aligned stages instead of raw depths, with one
family refusing the alignment, the same one the sign map exempts. The profile geography itself is
not an artifact of our pooling choice; its shape and peak survive last-token and max pooling
essentially unchanged (the G127 row under the next table). And re-measured in the units a neural
analogy actually licenses (write magnitude, signed affect work, probe signal-to-noise), the
maker-blindness holds at every block in all eight families, the work concentrates at the input
edge everywhere, and the depth at which the probe discriminates best obeys no law across families.
It sits early only in the home family, which is where this project's loci were chosen, a selection
caution rather than a coincidence to lean on. What survives of the umbrella beyond that is narrow.
The residual-trimodal instrument has a proven operating regime in simulation and has never been
pointed at a real model, and the polish/leakage depth split has never run at all. Confidence: the
rejections are replicated and controlled; the defensible-units result is one bad test away; the
alignment now carries its null, which confirms the late-locus half outright and demotes the
early-locus half to partly generic geometry, both on thirty texts and one corpus.

### Tracking: reconstruction quality follows the maker

The bet was that whatever sits at a depth, how strongly its response follows the specified
constraint dose is the signal. The conditional form: *"You might also have more agreement in the
late, **if the goal is clear.**"*

| # | hypothesis | status |
|---|---|---|
| **L1** | Per-block correlation with specified constraint dose carries information | **SUPPORTED (test).** Two independently generated ladders agree at 0.97 on which blocks carry it, the strongest replication in the project |
| **G103** | The flagship ratio's tracking transfers across families | **REJECTED as universal; the sign is a family constant (test, L28), on the complete 33-cell map.** Qwen negative at all three sizes; gpt2 positive at medium and large, null at xl; SmolLM2 positive at both sizes; pythia positive small, zero at 2.8b. **No family shares the home family's sign, and the positive camp's largest members go quiet** |
| **G112** | The family sign is band structure at the chosen loci, not a deeper mystery | **MIRROR-EXPLAINED (test, L96), eight of eleven families.** The per-layer dose maps, banded at the 7%/76% loci, predict each family's ratio sign from early-band tracking minus late-band tracking: the home family runs early-negative late-positive, gpt2 the exact mirror, and the fade's null cells land where the bands cancel. The one genuine miss is SmolLM2-360M, the odd family's third independent oddity |
| **G33** | Late coherence rises when the goal is clear | **REJECTED IN DIRECTION (test, L13/L47), all eight families.** With a statistic that provably can measure agreement (known-answer gated), not one of 24 family-corpus cells rises with specification dose. Agreement at the late blocks *falls* robustly in the Qwen family, weakly in gpt2 and mid-size SmolLM2, and is flat in pythia, the family-constant shape again. Uncentred by design, so the induction confound is unpartialled |
|   | | *(the first statistic was geometrically incapable of agreement and its verdicts are void; this row's history is instrument-death on 08-08, then rebuild and reversal on 08-09)* |
| **G127** | The early/late story survives the pooling choice | **SPLIT (test, L44 with its v2 rerun).** The block profile's shape and peak are pooling-invariant (r ≥ 0.98), so the geography does not hang on mean pooling. The ratio's dose relationship is **direction-stable and detectability-bound**: at full dose range with the reproduce-gate passed to the third decimal, the correlation is negative under all three poolings (mean −0.405, max −0.295 significant; last-token −0.109 null), so the direction does not move with extraction and the effect weakens to null when only the final token position is read |
|   | | *(this row's history is a sign-flip verdict on 08-10, the selection artifact found and withdrawn on 08-12, and the gated full-n rerun landing the same day)* |

**What the table says.** Tracking is the surviving half, but its shape keeps inverting the
predictions. The per-block signal replicates nearly perfectly across corpora and stands in at
least five families, direction fixed inside each family and different between them. And the
goal-clarity conditional, finally measured with an instrument that works, runs backwards where it
runs at all. As specifications stack, late-block responses agree *less* across texts, most
strongly in the home family, not at all in two others. Differentiation with dose, not convergence.
The family sign itself now has an account (G112): the fixed loci straddle machinery whose dose
response runs in opposite directions per family, the ratio inherits the sign of early-band
tracking minus late-band tracking, and the fade's null cells sit where those bands cancel, so
the loci were chosen where the home family's bands happen to diverge most, which is the anatomy
of an accidental family-specific instrument, and nothing downstream leans on the ratio's sign
across families. Inside the home model the direction is pooling-stable, negative under all
three extractions at full dose range, and what pooling moves is detectability, with the effect
vanishing when only the final token position is read. The first run to claim a pooling
sign-flip was computed on two rungs of five and is withdrawn; the gated full-range rerun
replaced it. The profile geography survives every pooling measured. SmolLM2 is the standing
exception to all of it, three independent oddities now. Confidence: the tracking existence
results are replicated and controlled; the agreement reversal, the pooling attenuation, and
the band account of the sign are each one bad test away.

## §7. Within-reader measurements: ratios, recovery, and the design lesson

**Made precise.** Reading human text should produce more low-order affective activation relative to
high-order than machine text does, the leaked/emblematic ratio *measured in the reader*, where
length, register, and vocabulary largely cancel because it is a ratio between two depths of the
same reader on the same text. His reading of what interpretability found stands here too. The
early-block "token valence" results and a reconstructed valence assignment are the same observation
under two readings, with the emotion vocabulary as the interface:

> There is a lexical mapping to valence and arousal through **the emotion wheel we all use**, but
> that's not quite what they're catching. What it's really doing is **defining and elaborating these
> higher-order predictions and controls of valence and arousal**, which would hypothetically provide
> an output that would look very similar to **an input for a mid-layer, limbic-system-like
> transformation**. That's possible.

| # | hypothesis | status |
|---|---|---|
| **L1** | The ratio falls as specified constraint dose rises, register fixed by construction | **SUPPORTED (test, L22/L23), replicated, and stronger under the fair control.** All three ladders at −0.42 to −0.52, every *p* ≤ 0.0004; sign family-bound per G103; what dose measures is instruction count to one generator |
| **B-1** | Affect directions exist in a reading model and are not word-counting | **SUPPORTED (test).** Four times chance while a word-counting model scored exactly chance |
| **L12** | The per-block correlation transfers across architectures | **SUPPORTED (test, L12/L40/L99), and the home family's liability resolves at power.** 25 ladder runs, 18 survive. The no-maker concentration that a 36-artifact permutation null could not adjudicate (p = 0.095/0.089) vanishes entirely at 108 artifacts under the identical rule (zero firing layers, zero survivor overlap), with the original seven fires explained as small-n noise under a fixed correlation threshold. The second family's no-maker arm sits inside its null the same way, so the control's cleanliness is not a shared-representation artifact. The survivor list keeps its layers without the asterisk |
|   | | *(this row's history is an open liability from the 08-09 relabel, resolved by the powered rerun and the second-family arm on 08-12)* |
| **L10 / L19** | Specification recovery: how much of the prompt survives, in bits | **REJECTED as recovery (test, L32/L36); it is a lexical-echo detector.** The graded curve kills it, +0.34 unrestricted, +0.04 at half-overlap, negative below; the no-maker control awards it wins where nothing is true (3/36, *p* = 0.006); the first-ladder strict arm lands *below* chance. The dose-tracking was real and belonged to the echo |
| **L6** | The ratio moves the same direction for revision as for specification | **REJECTED (test).** It falls with specification and rises with revision (*p* = 0.053); if both are real, the instrument distinguishes being-told-more from revising |
| **G115** | The reader's affective read shifts under a provenance frame alone | **SUPPORTED (test, L33/L37), replicated.** Identical text framed "by a person" vs "by an AI": ratio +0.007, magnitude down, every arm *p* < 2×10⁻⁸, three corpora. The reading machinery carries a provenance prior; the reader-side conclusion lives in `READER_HEURISTICS.md` §1 |
| **W-1 / W-1b / R-1 / L1-discrimination** | Reader-*state* measures: displacement, displacement variance, refusal, human-vs-machine discrimination | **REJECTED or VOID across the board (L21).** State is not stable enough to carry a signal; the discrimination read register |

**What the table says.** The design lesson is the most transferable sentence in the file. Measures
that ask about the reader's *state* die, and the one that survived asks about a **ratio between two
depths of the same reader on the same text**, where the big confounds cancel before measurement.
The recovery measure that briefly looked strongest is now honestly reclassified as an echo
detector, which leaves the ratio family and the per-block map as the reader-side instruments, both
replicated, both family-conditional in their specifics, and both measuring response to constraint
dose within one generator until the program's construct tests say more. The per-block map's one
standing asterisk is gone: the no-maker concentration that could not be adjudicated at small n
vanishes at three times the data, and it vanishes the same way on no-maker text the reader's own
family never generated. Confidence: the ratio and per-block results are replicated and
controlled; the echo reclassification is days old, one bad test away by age, in the direction of
further demotion.

# Part III: Consequences

## §8. Build gates: what must be true, in order, before anything is moved

Any intervention designed here waits on actual causal relevance, recoverable transformations, and
controllability. The section states functional constraints rather than running tests; it exists so
the early thoughts on possible ways forward are not lost by the time later stages of this process
arrive.

> If this structure is not what happens in naturally occurring language models, **I wonder if we could
> force it** – make an empathic bot with lower-order valence and arousal, medium human-mapped
> Pankseppian structures, and higher-order predictions and controls on those that are free-floating and
> subject to rapid change.

> It's a weakness to the alignment consequence, because **we have to provide that weighting somehow.**
> [...] But at the very least it seems like all it needs is a **bootstrap.** You don't need a ton – a
> little bit would be enough to start the shape, to kick it off in the right direction.

**The gates, in order. (1) Coherent structure exists, passed. (2) The structure plays a *causal*
role in intent inference, untested, and everything below waits on it. (3) The depth transform is
recoverable, first bite passed where the rotation composes. (4) The structure is controllable.
Only then seeding, relocation, or reinforcement.** Moving a merely-decodable correlate and reading
the disruption as an empathy intervention is the named failure mode. Causal work means patching,
erasing, or steering the recovered geometry and asking whether goal and process inference change
while lexical and topical performance hold; and cross-model comparison should align computational
events rather than percentage depth, which has already failed to transfer.

**Phase 2.4 operationalizes the causal gate as an engineered analogue. A fitted affective
subspace is amplified and ablated during artifact reading, with rank-, norm-, and parameter-
matched semantic and random controls. PyTorch is only the mechanism used to alter activations.
A selective improvement in recovery of independently recorded choices would show causal utility
for that model reader. It would not show that the model contains a midbrain, experiences affect,
or has reproduced human empathy. Human-reader correspondence remains a later gate.**

> What if it's not the **location** of where they are, but rather their **shape** that we need to care
> about? What if the values are somehow **extractable and repositionable as meta-concepts**? They'd
> have to change depending on where they are in the hierarchy. **Could we force them to be in a layer
> we think is correct and then strengthen them?**

| # | hypothesis | status |
|---|---|---|
| **G45** | An affective concept can be forced into a chosen block and strengthened there | **OPEN, the build**, gated on causality and the transform |
| **A02-S3** | Plain valence is causally steerable in the instruct model by an ADDITIVE direction at a capability-tolerated dose | **SUPPORTED (test, L197), the standing anchor.** Sign pair +0.78/−0.75 (p<1e-3 each) on happy-vs-sad continuation preference, random and shuffled directions quiet, decode 1.00 on an untouched validation split. A different construction from L170's rank-one amplify/ablate; coexists with it. **Adversary survived (L232):** a neutral continuation pair moves at most 0.10 under the same intervention and a token-injection probe accounts for 0.09 of the valence shift, so the handle is not lexical injection |
| **A03-S3** | Action tendencies leave decodable structure while the model reads tendency-laden text | **SUPPORTED (test, L198), one corpus deep.** 0.422 vs 0.25 chance, nearest-centroid at the LATE third, clear of a five-shuffle null; direction bases and the valence locus decode nothing, so the geometry is categorical and deeper than valence |
| **A04-S3** | The tendency read is independent of valence (fear vs anger dissociation) | **REJECTED (test, L199).** Fear-anger separate at 0.597 but the frozen valence axis separates them at AUC 0.19, so the read is partly valence-riding; no discrete-system license |
| **A05-S3** | Two-tendency blends read as superpositions of their components | **REJECTED for this centroid-composition readout (test, L200).** Pair recovery is below chance (top-2 pair match 0.065 against 1/6). This does not establish that the underlying representation is non-compositional |
| **A07-S3** | Tendency steering changes the reader's own next impulse | **SUPPORTED only as a weak, uneven effect on the tested readout (test, L202).** Pooled sign pair (+0.10/−0.06 around a 0.25 base, random quiet) behind the A02 gate at a capability-tolerated dose. The pooled sign pair masks a curiosity-heavy default (0.75) and reverse-direction anger steering. The held-out maker prediction now exists (L255): steering with the true tendency's direction raises the log score on a held-out maker's tendency +0.4 to +0.8 nats in both maker folds with random and incongruent directions quiet, while the directions' own decode sits at chance and the unsteered prompted read of a held-out maker stands at 0.67 to 0.70 balanced; the bridge has its first plank, laid with an oracle direction on one checkpoint and one domain |
| **A06-S3** | Suppressing surface emotion leaves the tendency decodable (the abstract read survives without the words) | **INSTRUMENT DEAD (test, L201/L234).** The expressive corpus carries no surface-emotion channel to suppress; on a second scene bank the strongest channel runs at 0.006 against a 0.012 verifiability floor, so the manipulation is unverifiable corpus-wide and the question is unasked |
| **M04-S3** | One policy delivered three ways (prompt, adapter, activation) lands in one place | **PARTLY SUPPORTED, activation route unmeasured (test, L204).** Prompt and adapter shifts of the likelihood readout align at cosine 0.69 with the adapter three times larger; the activation route never localized (L203), so two of three deliveries agree |
|   | | *(the causal gate's first instrument attempt INSTRUMENT-FAILED (test, L162): dev-selected block flipped between seeds at eighteen dev items, and the degenerate input-edge selection lesioned the model 2.55× under amplification; abstract emotion-word-free decoding appeared weakly above every control at the one functioning seed, so the signal grain exists and the battery was underpowered, never the reverse. The rebuilt ruler then answered cleanly for its tested construction (test, L170): in Qwen2.5-1.5B the representation is real and stably located, with unanimous cross-seed consensus on one deep block and held-out decoding at twice chance while the lexical baseline sits at chance. Rank-one fear and joy amplification/ablation at that block did not move the 24-item approach-versus-withdraw behavior at any dose admitted by that capability gate, with no sign pair. The wing closes for this model, basis rank, locus, behavior, and intervention family; scale, rank, locus, behavioral target, and intervention form remain named construction variables)* |
| **G38** | The mid-level primitives need only seeding, not specification | **OPEN.** *(Dependency corrected 2026-08-09: it rests on coherent structure existing (passed), on the causal gate, and on controllability, not on the rejected subspaces-not-depths claim it used to cite)* |
| **A02-S4** | The valence handle improves target-specific prediction of another maker's next choice, beyond moving the reader's own answer | **COUNTEREVIDENCE at 256 worlds (test, L243; INCONCLUSIVE at 128), controls loud.** Aligned benefit -0.08 nats [-0.15, -0.01] at full evidence, with a random direction of the same norm moving the score more than the fitted one (+0.13 aligned, +0.22 main effect); the fitted direction at the high dose lowers the target score 0.3 nats in either sign; the own-choice shift is 0.2 of the mass; no correct-action stratum carries the interaction |
| **B01-S5** | The held-out maker read's causal use (A07-S3, L255) replicates on a second checkpoint | **COUNTEREVIDENCE on the second-family checkpoint (test, L257; fixed-order receipt L283 and the second contract's card L285, congruent −0.005; on the second domain +0.03 [−0.05, +0.11] with every other direction costing), decode at chance.** Congruent −0.02 nats [−0.13, +0.10] on SmolLM2 with the wrong direction at −0.52 and a random one at −0.23, both folds; the directions fit on Qwen-made artifacts do not decode on SmolLM2 (0.24 against 0.25), so representation-not-used and directions-not-transferring are not separated |
| **B02-S5** | The held-out maker read's causal use (L255) holds on a second artifact domain with the controls quiet | **SUPPORTED (test, L258; fixed-order receipt L283; landed as a card in the second contract, L286: +0.42, random −0.04).** Congruent +0.42 [+0.23, +0.64] on twelve fresh scenes with the random arm −0.04, permuted-label directions −0.03, the wrong direction −0.33, the reversed sign −0.67; the card's loud random arm was order noise |
| **B03-S5** | The anchor's congruent steering effect is specific to its coordinates, dose, sign, and labels | **SELECTIVE AGAINST RANDOM AND WRONG DIRECTIONS, SIGN- AND DOSE-SPECIFIC, NOT COORDINATE-SPECIFIC, LABEL-SPECIFIC ON ONE DOMAIN OF TWO (test, L260 reversed by L283; landed as a card in the second contract, L288).** With the option order held fixed across arms: congruent +0.48, random 0.00, incongruent +0.05, reversed −0.32, half +0.23 and double +0.62, the direction at shifted or random blocks +0.28 and +0.42, permuted-label directions +0.32 on this domain and −0.03 on the second; the card's loud controls were order noise on the readout's two-nat letter effect |
| **A03-S4** | Affect conditions intake: steering during the situation's intake moves target prediction more than steering during the answer | **VALID NULL (test, L247), 128 worlds.** Context-phase minus answer-phase aligned benefit -0.05 nats [-0.12, +0.02], a useful benefit excluded; intake-phase steering alone -0.04, answer-phase +0.01, the neutral span inert |

**What the table says.** The build's gate order now has a real answer at small scale: gate one
(coherent structure) passed long ago, and the decisive causal gate has been measured cleanly
rather than instrument-failed. The rebuilt ruler locates a weak abstract affect representation
at one unanimous deep block, readable at twice chance on text with no emotion vocabulary. Its
rank-one fear/joy intervention is behaviorally inert on the tested approach-versus-withdraw
ruler across the doses that ruler's capability gate tolerates. At that construction the
structure is a readout, not a handle. Stage 3 may test higher-rank or dynamic mixtures,
different loci and causal abstractions, larger substrates, and policy-level targets without
changing L170's classification. A positive result on one of those constructions would coexist
with L170; only an exact re-run can reclassify it. That different-construction result now
exists (test, L197/L202): additive steering on the INSTRUCT model at blocks 14-18 moves valence
preference as a clean sign pair with controls quiet, and the same additive family moves realized
impulse choice weakly through the tendency directions, a handle where the rank-one construction
found a readout, exactly the coexistence the errata's scoping predicted. The geometry the handle
grips is categorical and late (centroids at the last third, L198) and partly valence-riding (L199),
while the centroid-composition readout recovers pairs below chance without establishing that the
representation is non-compositional (L200); the handle survives its lexical-injection adversary (L232), the
suppression question is unaskable on this corpus (L234), and prompt-delivered and
weight-delivered policy shift the same readout in the same direction (L204). The build
path stays open only through what the closure
names, a larger substrate, a higher-rank basis, or a different intervention family, and its
address, if the transform work holds, remains a family where the rotation composes rather than
the home family. The bridge from that handle to another maker is now measured and unbuilt:
on 256 hazard worlds the steered readers' prediction of the maker's next action loses
aligned with the maker's appraisal (a twelfth of a nat, the interval below zero), a
norm-matched random direction moves the score more, and the same dose moves the readers'
own next choice by a fifth of its mass (A02-S4); steering during intake does no better than
steering during the answer (A03-S4). The handle grips the reader's continuation, not its
model of the maker, whenever it is applied: the coexistence L170's scoping allowed, and the
bridge the errata warned would have to be earned is measured and not there in this family.
Own-impulse steering does not close the intent-inference gate; the held-out maker read (A07-S3,
L255) does, for the anchor, once the readout's order nuisance is held fixed: the true tendency's
direction lifts the read by half a nat on two artifact domains while a random direction of the
same norm does nothing, the wrong direction is inert or costs, the reversed sign costs, and the
dose is monotone (B02-S5, B03-S5); the direction works across the middle third of the stack
rather than at one coordinate, and directions fit on shuffled labels carry part of the effect
on one domain and none on the other, so the representation used is the tendency subspace with
partial specificity to the particular tendency. The specificity battery's first reading, that
the controls were as loud as the true direction, was the card's own order noise on a two-nat
letter effect (L283). The second-family checkpoint shows no lift under any direction (B01-S5),
so causal use during inversion is one reader's on two domains, and the valence handle's
failure (A02-S4) and the tendency handle's success now sit side by side as different
representations in one reader. Confidence: the scoped causal
results are one bad test away, three seed splits and one model deep for the decode, the same
tested construction for the inertness, and the lexical adversary passed for the additive handle;
the bridge to maker inference is one bad test away against for the valence handle (two cards on
one construction family and two readers) and one bad test away for the tendency
representation's causal use (one reader on two domains with the order held fixed, the second family null; one bad test
away, and its nuisance is now known and controlled); the gates above remain logic.

## §9. Reading versus caring

The affective-computing literature says a system needs an internal state like emotion; the stated
goal is empathy *without* emotions. Not incompatible:

> **You probably do not need interoceptive states. You probably need an interoceptive generative
> model.**

Simulation requires the mapping *situation → predicted state → category*, run forward as a
prediction about someone else, and a language model plausibly has that mapping, because humans
write it down constantly. **The limit, honestly. The substrate may be unnecessary for *reading* and
still necessary for *caring*.** An interoceptive generative model may suffice to predict how
another feels; nothing anywhere shows the prediction creates a motivation to protect. Reading
empathy and motivational alignment are **separate engineering problems**, and the second belongs to
[`ALIGNMENT.md`](ALIGNMENT.md).

| # | hypothesis | status |
|---|---|---|
| **lit** | Nobody has built a layered core-affect / discrete-emotion / constructed-emotion architecture | **SUPPORTED (READ).** The 2025 survey states it; described in 2005, never implemented; the one public proposal remains a proposal |
| **G37** | Reading another's affect requires no internal state, only a generative model of one | **OPEN.** Cheap: can the probe predict which affect a human reader will attribute? |

**What the table says.** The architecture is unclaimed on the field's own word, and the project's
goal needs only the generative model for its reading half, while the caring half is explicitly not
addressed by anything here. Confidence: the unclaimed-ground fact is replicated and controlled;
the rest is untested.
