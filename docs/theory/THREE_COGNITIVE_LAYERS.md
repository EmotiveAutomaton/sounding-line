# Three cognitive layers — the latent architecture, and what a model reconstructs of it

> If human empathy relies on a **constraint of the solution space in the midbrain**, then we are going
> to have to similarly constrain the solution space somehow — or else we run into the impossibility of
> value extraction. **But if we can constrain the solution space sufficiently, we can get there**
> through a mechanism analogous to the empathy triangle [now called triple inference].

> There are three layers. The three layers of human cognition through affective neuroscience will have
> some rough analog — **though softened** — in neural networks, because they are trying to model us
> using an imperfect version of our own mechanism for empathy, which is just inverse reinforcement
> learning with a whole bunch of tricks.

Four claims, stated separately because they live or die separately:

1. **Human proposal** — core affect/salience, drive constraints, and expertise-conditioned
   construction are distinct functional levels of one system.
2. **Model proposal** — a next-token model may *reconstruct* aspects of those functions, without
   feeling anything.
3. **Load-bearing prediction** — the drive constraints are reconstructed *worst*, because they are
   conserved but under-expressed in text; the shape of that error is a large source of failed goal
   inference.
4. **Current verdict** — coherent affect geometry exists in every model checked; three depth bands
   do not; intent *tracking* exists and transfers; causal function is untested.

**This file owns** the latent architecture: what human structure exists, what a model might
reconstruct, where reconstruction fails, and what intervention could follow. **It does not own** the
artifact-facing traces ([`DECISION_TRACES.md`](DECISION_TRACES.md)), the inference itself
([`THE_TRIPLE_INFERENCE.md`](THE_TRIPLE_INFERENCE.md)), or the alignment consequence
([`ALIGNMENT.md`](ALIGNMENT.md)).

---

# Part I — The theory

## §1. The human functional scaffold

| function | what it is | quality of the training signal |
|---|---|---|
| **core affect / salience** | valence and arousal — the lowest-level, most universal thing in the signal | good; easiest to capture |
| **drive constraints** | the ancestral, conserved affective systems | present but **pre-verbal, never written down directly** |
| **expertise-conditioned construction** | trajectories, higher-order predictions and controls, the goal machinery that runs on them | individual, chaotic, high-variance |

> The middle one we wouldn't be able to converge upon... that's the part of the human brain that is
> baked in a little bit, that is a little bit more ancestral. **And it's struggling to model that.**
> So it uses valence-arousal mixed with some goal direction to get most of the way there. **But this
> is where its error comes from.**

> **The lack of Panksepp is where a lot of misalignment comes from, specifically. We have to give
> emotions in order to converge upon a more appropriate goal extraction.**

**Goal is not a fourth level.** He declined one: *"that's just not reasonable. It wouldn't be
separable. Three, frankly, barely won't be."* A goal is **a weighting applied across all of them** —
one component of the value weighting temporarily amplified by attention — so it needs to be readable
as a modulation of whatever sits at each depth, not found at an address of its own.

**Expertise is the late thing, and goal runs on it:**

> **Executive function is historically associated with goals** — with organising, with making
> sub-goals. Is the executive function applying the trajectory? Well, of course it is. **That's why
> goals come from the neocortex: because that's where your trajectory is stored.**

> **Later layers of a model will have more expertise decoding and encoding capabilities.**

Cognitive expertise here means the higher-order metaphorical layer — the entry vertex most people
use on media at all (**media literacy** is the common-language name for exactly this general skill),
as against the mechanical layer. And in humans goal direction draws on all three levels: *"I would
say middle and late are where you get most of it. **In AI I genuinely have no idea.**"*

**The scaffold has a known gap: no positive channel.** The eight concepts read are Panksepp's seven
plus `none_recoverable` — no happiness, no positive valence as such:

> Happiness is often modelled as one of two things: either **positive valence of those need
> networks**, or as **a conjoined channel that all seven of them have to not be inhibiting** in order
> for happiness to flow.

| # | hypothesis | status |
|---|---|---|
| **G26** | A goal is a weighting across all levels rather than a level of its own | **OPEN, adopted as the working position** |
| **G41** | Later blocks carry more expertise encoding and decoding | **OPEN** — the testable form of "goals are late": expertise is suppliable and variable |
| **G27** | Level boundaries in a model are soft rather than sharp | **assumed, not tested** — any test requiring a clean boundary is testing the wrong thing |
| **G73** | Positive affect is a readout over the seven channels | **OPEN** — suppressing one channel should move it proportionally |
| **G74** | Positive affect is a conjoined gate requiring all seven un-inhibited | **OPEN** — suppressing any one should collapse it; a single suppression experiment separates the two |

**What the table says.** The scaffold itself is theory: its one adopted position (goal as weighting)
and its one testable sharpening (expertise-late) have never been run, and every affect reading the
project has produced is blind to positive affect except where it leaks through seeking, play, or
care. Confidence: untested — logic only.

## §2. The reconstruction bridge — what a model is doing, in reserved words

> When I say the model leaked involuntary affect, **I'm not assigning affect to the model.** It's that
> they're **trying to predict the human brain and failing to do so.** They're trying to have empathy
> and failing.

> **You're seeing ghosts of a human brain, not an actual human brain.** [...] The lines will be
> **softer** on an AI modelling.

A language model trained on human text is a *reconstruction* of the process that produced the text,
built by prediction, inheriting the shape of what it reconstructs — including where the
reconstruction is bad. The errors are the interesting part.

**Reserved vocabulary, because "layer" had come to mean four different things:**

    functional level   what a stage DOES, in the human theory (core affect, drives, construction)
    region             anatomy — subcortical structures, neocortex
    block              a transformer layer, by index
    subspace           representational structure WITHIN blocks — channels, directions, geometry

"Layer" without a qualifier is banned in this folder. And two grounded cautions from the
commissioned analogue research ([`../method/NEURAL_ANALOGUES.md`](../method/NEURAL_ANALOGUES.md)):
**nothing in a dense transformer can "peak" in the energy sense** — every block spends identical
compute, so only decodability varies, and cross-domain claims must compare decoding to decoding
(the field's own move, since univariate bright-peaks failed for emotion there too); and **"noise"
has no biophysical referent at temperature zero** — say *unmodeled variance*, and treat rogue
dimensions as the artifact class, not the signal. **Token transformation is an input adapter** —
the model-side counterpart of sensory transduction, not a fourth cognitive level:

> The prediction that early valence/arousal is what we're mapping — **it doesn't quite fucking fit.**
> Because the input for humans is **sensory** data. That's kind of what a model gets when it is boiled
> down into vectors, **but it's not quite the same.**

**The two orderings are competing model *mappings*, not competing definitions of cognition** — the
question is where each function is reconstructed in blocks, given where it lives in regions:

| # | hypothesis | status |
|---|---|---|
| **G20a** | Mapping A: core affect reconstructed in early blocks, drive constraints mid | **OPEN** — never tested directly |
| **G20b** | Mapping B: early blocks are the input adapter, core affect mid, categories late | **OPEN, and it discriminates cleanly against G20a** — under A valence peaks early and categories mid; under B valence peaks mid and categories late. It also reconciles the two published results that contradict each other (the field's mid-block emotion peak; a sparse-autoencoder cascade putting emotion late) |
| **G34** | Parameter ratios across depth echo neuron-count ratios across regions | **WITHDRAWN — misattributed.** The suggestion on record was to *build* structures mapped this way; it was never a prediction that current models show it |

**Why the middle would be the latent variable behind the machine-text unease** — the derivation
that used to sit with the traces: the unease has four candidate accounts (broken polish–effort,
flattened intent, missing translation, wrong shape), and his objection to the list was the point —
*"now we have a proliferation of reasons... this list seems more like the **observable variables**."*

> **The latent variable is midbrain misalignment** — or lacking a midbrain specifically.

If a model reconstructs everything *except* the mid-level drive constraints, it has no shared prior
with the reader, and each account is that absence seen from a different angle. Whether that is
right is a real question and not assumed — *"That doesn't sound right. That doesn't sound right at
all... I don't know, they're tied in there somehow"* — and the test is whether the four dissociate.

**What the table says.** Both mappings are open; the one wrong attribution is withdrawn; the bridge
itself (reconstruction-without-feeling) is the file's working frame rather than a tested claim.
Confidence: untested — logic only.

## §3. The missing middle — the load-bearing prediction

Stated formally, in his words:

> Nonverbal drive constraints from Panksepp are systematically underdetermined from human text, so
> that when a model reconstructs them, it has worse access to them than surface affect or learned
> expertise, both of which are more accessible as they are closer to the later layers of output in
> the human brain. **The shape of this reconstruction error for the model is a large source of
> failed goal inference.**

Three consequences make it testable rather than atmospheric. **Absent drives are constraints** — you
can only route attention onto drives you possess, so a drive the maker lacks bounds what they can
make (the artifact-side face of this lives with the traces; the alignment face in
[`ALIGNMENT.md`](ALIGNMENT.md)). **The predicted error is *specific*** — drive ambiguity should
produce a distinctive goal-inference failure while surface affect, category, and expertise reads
stay intact; that fingerprint experiment is what keeps this from collapsing into generic emotion
probing, and it has never been run. **And the prediction prices the middle**: reconstruction should
be measurably worse there than at either end, once "there" can be located at all — which Part II
shows is the hard part.

| # | hypothesis | status |
|---|---|---|
| **S-14** | An absent drive is recoverable from artifacts | **SUPPORTED (sim, V11) as method; OPEN on real artifacts.** Near-invisible in spontaneous work (0.61), perfect under commission toward the missing channel (1.00), pure compliance collapses to exactly 0.5 — *how the goal is pursued* is the discriminator. The made-under-duress mechanism, first working form; real commissioned work is the missing half |

**What the table says.** The prediction's first mechanism check exists only in simulation, where it
behaves exactly as the theory wants — absence reads, and reads through pursuit rather than content.
Confidence: sim-only; the real-artifact claim is untested.

# Part II — The evidence

## §4. Human evidence — conserved machinery, and how many primitives

| # | hypothesis | status |
|---|---|---|
| **lit** | Conserved **subcortical affective control machinery** exists as a distinct stage | **SUPPORTED (READ).** The strongest support cites neither camp — hypothalamic line attractors encoding intensity and persistence (*Nature* 2024), conserved biphasic cross-species dynamics with a ketamine dissociation (*Science* 2025). *Anatomical honesty: that evidence is hypothalamic and PAG — subcortical, not specifically midbrain — and the machinery being coordinated is uncontested while its reading as a separable affective-primitive stage is not* |
| **lit** | The Panksepp–Barrett disagreement is about localisation | **REJECTED (READ)** — both camps place the machinery in hypothalamus and PAG; they disagree on whether activity there *constitutes* affect or reports it, so imaging will not settle it |
| **lit** | Panksepp's seven is the right number | **REJECTED (READ) as an empirical claim** — never derived from a dimensional analysis; the standard instrument tests six |
| **G35** | The ~25 distinguishable states are the **human-nameable subset** of the subcortical channels' combinations — nameability, not blending, is the relation | **OPEN — never tested by anyone.** *(Reframed 2026-08-09: "blends of seven" was the wrong form — channels are distinct subcortically and combine only at the neocortical level through predictions and controls of them)* |
| **G36** | Some recovered components will be unnameable | **OPEN**, behind a working count instrument |
| **L8 / L9** | Our own two counting attempts | **VOID / INSTRUMENT DEAD** — a criterion that returned components from noise, then a rebuilt instrument with four confirmed defects. This project holds no count of its own |

**What the table says.** The subcortical stage is better supported than when the project started,
and by work from outside the argument; every count in the field is a stopping-rule output except
~25, which survived its own ceiling test — and our instruments have contributed nothing to the
question yet. Confidence: the machinery is replicated and controlled in the published record; the
count relation and everything of ours is untested or instrument-dead.

## §5. Does a corresponding model structure exist?

| # | hypothesis | status |
|---|---|---|
| **G40** | A coherent affect subspace exists, consistent across families | **SUPPORTED (test).** Four to six times its matched null even between the most distant blocks, in **all eleven families**, 0.35B–3B, four architectures — the rotation *rate* is consistent where the magnitude profile never was |
| **G42** | The subspace is organised in three bands | **REJECTED (test) as equal thirds.** A two-way split at the earliest boundary beats any three-band split — in the original four families and in all eleven on the extended check |
| **G43** | The early break is affective rather than an input-adapter artifact | **REJECTED (test), all eleven families, unanimous.** Topic, syntax, and frequency subspaces measured identically all snap at the same block the affect subspace does, in every family — the boundary is the input adapter's edge and carries no mapping information. The gate he set resolves in the deflationary direction |
| **G44** | The depth transform of the subspace is recoverable | **OPEN — first bite landed.** Alignment *composes* lawfully in pythia (R² 0.88–0.92) and gpt2 (0.78–0.84), weakly in SmolLM2, **not in Qwen (0.20–0.30)** — fit the transform where it is lawful, and note the home family is the outlier again |
| **G46** | Weaker models place the structure more poorly | **NO DETECTED RELATIONSHIP (test), n = 11.** Placement quality against parameter count sits at rho +0.05 across eleven families in the 0.35B–3B range. Eleven points cannot prove scale irrelevant, so "architectural, not learned" was the stronger unlicensed form; what stands is that placement gave no sign of tracking capability where measured |
| **G39** | The three levels are subspaces rather than depths | **REJECTED (test)** — the subspace rotates with depth |

The rank-dilution caveat that rode all these numbers is retired: rank-truncated bases against a
distant-matched null reproduce the rotation in all eleven families (adjacent blocks share
0.78–0.96 of the subspace, distant 0.21–0.42, chance ~0.05) — no verdict flips anywhere.

**What the table says.** There is one coherent affective structure; it rotates continuously
through depth rather than sitting in bands; its placement does not improve with scale; and its
rotation is lawful enough to fit in some families. Its one sharp boundary, though, has lost its
meaning: every content type measured — topic, syntax, frequency — snaps at the same front block,
so the break is the input adapter's seam and says nothing about affect. **What remains is a
consistent shape that is not yet the shape this file claims**, because nothing ties the structure
to drives, to the middle, or to any causal role — and its one candidate landmark just proved
generic. Confidence: existence, rotation, the scale result, the adapter-edge rejection, and the
repaired-basis confirmation are all replicated and controlled — eleven families each; what the
structure *means* remains gated on causality.

## §6. Address versus tracking — the two umbrellas the predictions became

### Address: specific jobs at specific depths

The bet: if the three levels are real in a model, *where* things sit should itself be diagnostic.
The route back in for the three-locus version, nobody having tried it:

> We're finding **ratio variance relationships between early and late** despite there being a peak in
> the middle. It implies a sort of shape that **I don't think anyone else has glommed on to.**

| # | hypothesis | status |
|---|---|---|
| **L14** | The depth profile carries information about the maker | **REJECTED (test).** The profile is identical (or within one block) with and without a maker, in every family; the peak sits anywhere from block 2 of 29 to 47 of 49 with no relation to size |
| **G22** | A smeared three-locus structure is recoverable in the *residual* after fitting one peak | **OPEN on real models; the instrument has an operating regime (sim, V11).** The smear is architectural — a planted three-locus world reads as one mid peak in 100% of runs *and* 100% of reparameterisations, so published mid-peak profiles are uninformative against a three-locus truth. The residual statistic separates the worlds at AUC 0.87 in 25% of parameterisations — **feasibility in a bounded regime, not universality** |
| **G31** | The middle is high-activity and low-coherence | **REJECTED (test)** — 2 of 33 runs; the modal pattern is a *quiet* middle, identically on maker-less text |
| **G69** | The intent signal peaks deeper as rung rises | **REJECTED (test)** — the apparent shifts were two near-tied fixed loci trading rank; regenerated verdicts show fixed peaks in all eleven families |
| **G21** | Block 0 is a pure salience gate — presence without category | **REJECTED (test) at power, all eleven families — including the home-family half-survival.** Presence is near-flat through every stack (block 0 within a few points of the best block everywhere), so the scattered "peak locations" were argmaxes of level curves, the home block-0 peak included; and block 0 carries category at 8–9× chance in every family. **No model has a presence-only stage at its front door** |
| **L14** | The depth profile is bimodal | **REJECTED (test)** — 27 of 36 runs unimodal; the exceptions are two families and appear in their no-maker runs too |
| **G124** | Aligned by computational events rather than depth fractions, the loci land somewhere lawful across families | **SUPPORTED (test), first pass.** Activation-similarity alignment against five families: the home early locus matches a block in the first sixth of the stack in four of five, and the late locus lands at 62–83% depth in all five. The exception is SmolLM2 — the odd family again — whose best match to the early events sits 28% deep. No permutation null yet |
| **G126** | The maker-blindness of the profiles survives translation into defensible units | **SUPPORTED (test), all eight families.** Write norm, signed affect work, and probe signal-to-noise per block, QC-clean throughout: the write/work geography is near-identical with and without a maker at every block, and concentrates at the input edge universally. Discriminability placement obeys no law — early at both Qwen sizes, scattering early-to-late across the others with size reversing direction between families; **the home family's early placement, where this project's loci were chosen, is the exception rather than the rule** |

**What the table says.** Where things sit in a model is a fact about the model, not about the
maker: the profile ignores the maker, the peak never moves with intent, the middle is quiet, and
the last candidate for a portable address died at power — presence is flat through every stack and
never category-blind, so there is no salience gate anywhere, the home family included. But the
addresses
that refuse to transfer as raw block numbers do translate: aligned by what the blocks compute, the
early and late events land at lawful relative depths in almost every family (G124), so
cross-family claims can be stated at aligned stages instead of raw depths — with one family
refusing the alignment, the same one the sign map exempts. The profile geography itself is not an
artifact of our pooling choice: its shape and peak survive last-token and max pooling essentially
unchanged (the G127 row under the next table). And re-measured in the units a neural analogy
actually licenses — write magnitude, signed affect work, probe signal-to-noise — the
maker-blindness holds at every block in all eight families, the work concentrates at the input
edge everywhere, and the depth at which the probe discriminates best obeys no law across families:
it sits early only in the home family, which is where this project's loci were chosen — a
selection caution, not a coincidence to lean on. What survives of the umbrella beyond that: the
residual-trimodal instrument has a proven operating regime in simulation and has never been
pointed at a real model, and the polish/leakage depth split has never run at all. Confidence: the
rejections are replicated and controlled; the alignment and defensible-units results are each one
bad test away — the alignment's null is still owed.

### Tracking: reconstruction quality follows the maker

The bet: whatever sits at a depth, how strongly its response follows the maker's specified intent
is the signal. The conditional form: *"You might also have more agreement in the late, **if the
goal is clear.**"*

| # | hypothesis | status |
|---|---|---|
| **L1** | Per-block correlation with specified intent carries information | **SUPPORTED (test).** Two independently generated ladders agree at 0.97 on which blocks carry it — the strongest replication in the project |
| **G103** | The flagship ratio's tracking transfers across families | **REJECTED as universal; the sign is a family constant (test), on the complete 33-cell map.** Qwen negative at all three sizes; gpt2 positive at medium and large, null at xl; SmolLM2 positive at both sizes; pythia positive small, zero at 2.8b. **No family shares the home family's sign, and the positive camp's largest members go quiet** |
| **G33** | Late coherence rises when the goal is clear | **REJECTED IN DIRECTION (test), all eight families.** With a statistic that provably can measure agreement (known-answer gated), not one of 24 family-corpus cells rises with specification dose: agreement at the late blocks *falls* robustly in the Qwen family, weakly in gpt2 and mid-size SmolLM2, and is flat in pythia — the family-constant shape again. Uncentred by design, so the induction confound is unpartialled |
|   | | *— the first statistic was geometrically incapable of agreement and its verdicts are void; this row's history is instrument-death (08-08), then rebuild and reversal (08-09)* |
| **G127** | The early/late story survives the pooling choice | **SPLIT (test).** The block profile's shape and peak are pooling-invariant (r ≥ 0.98 against last-token and max pooling) — the geography does not hang on mean pooling. The flagship ratio-vs-dose statistic lands in a different sign-and-significance class under each pooling — the ratio is pooling-bound on top of family-bound |

**What the table says.** Tracking is the surviving half, but its shape keeps inverting the
predictions: the per-block signal replicates nearly perfectly across corpora and stands in at
least five families — direction fixed inside each family, different between them — and the
goal-clarity conditional, finally measured with an instrument that works, runs backwards where it
runs at all: as specifications stack, late-block responses agree *less* across texts, most
strongly in the home family, not at all in two others. Differentiation with dose, not convergence.
The flagship ratio carries a second disqualification: its dose relationship changes sign with the
pooling choice inside the home model, so nothing downstream should lean on that ratio's direction
anywhere. The profile geography, by contrast, survives every pooling. Confidence: the tracking
existence results are replicated and controlled; the agreement reversal and the pooling split are
each one bad test away — the reversal's contrasts carry the induction confound unpartialled.

## §7. Within-reader measurements — ratios, recovery, and the design lesson

**Made precise:** reading human text should produce more low-order affective activation relative to
high-order than machine text does — the leaked/emblematic ratio *measured in the reader*, where
length, register, and vocabulary largely cancel because it is a ratio between two depths of the
same reader on the same text. His reading of what interpretability found stands here too: the
early-block "token valence" results and a reconstructed valence assignment are the same observation
under two readings, with the emotion vocabulary as the interface —

> They're reading the valence and arousal layers and **interpreting those as lexical**, because there
> **is** a casual lexical mapping through the emotion wheel we all use. But what that emotion wheel is
> really doing is **defining and elaborating higher-order predictions and controls OF valence and
> arousal.**

| # | hypothesis | status |
|---|---|---|
| **L1** | The ratio falls as specified intent rises, register fixed by construction | **SUPPORTED (test), replicated, and stronger under the fair control** — all three ladders at −0.42 to −0.52, every *p* ≤ 0.0004; sign family-bound per G103 |
| **B-1** | Affect directions exist in a reading model and are not word-counting | **SUPPORTED (test)** — four times chance while a word-counting model scored exactly chance |
| **L12** | The per-block correlation transfers across architectures | **SUPPORTED (test)** — 25 ladder runs, 18 survive; the re-adjudicated no-maker control fires at luck rates, and the home family's borderline concentration came back **clustered luck** on a 2,000-permutation null (*p* = 0.095/0.089 — the eyebrow is recorded, not erased) |
| **L10 / L19** | Specification recovery: how much of the prompt survives, in bits | **REJECTED as recovery (test) — it is a lexical-echo detector.** The graded curve kills it: +0.34 unrestricted, +0.04 at half-overlap, negative below; the no-maker control awards it wins where nothing is true (3/36, *p* = 0.006); the first-ladder strict arm lands *below* chance. The dose-tracking was real and belonged to the echo |
| **L6** | The ratio moves the same direction for revision as for specification | **REJECTED (test)** — it falls with specification and rises with revision (*p* = 0.053): if both are real, the instrument distinguishes being-told-more from revising |
| **G115** | The reader's affective read shifts under a provenance frame alone | **SUPPORTED (test), replicated** — identical text framed "by a person" vs "by an AI": ratio +0.007, magnitude down, every arm *p* < 2×10⁻⁸, three corpora. The reading machinery carries a provenance prior; the reader-side conclusion lives in `READER_HEURISTICS.md` §1 |
| **W-1 / W-1b / R-1 / L1-discrimination** | Reader-*state* measures: displacement, displacement variance, refusal, human-vs-machine discrimination | **REJECTED or VOID across the board** — state is not stable enough to carry a signal; the discrimination read register |

**What the table says.** The design lesson is the most transferable sentence in the file: measures
that ask about the reader's *state* die, and the one that survived asks about a **ratio between two
depths of the same reader on the same text**, where the big confounds cancel before measurement.
The recovery measure that briefly looked strongest is now honestly reclassified as an echo
detector, which leaves the ratio family and the per-block map as the reader-side instruments — both
replicated, both family-conditional in their specifics. Confidence: the ratio and per-block results
are replicated and controlled; the echo reclassification is days old — one bad test away by age,
in the direction of further demotion.

# Part III — Consequences

## §8. Build gates — what must be true, in order, before anything is moved

> If this structure is not what happens in naturally occurring language models, **I wonder if we could
> force it** — make an empathic bot with lower-order valence and arousal, medium human-mapped
> Pankseppian structures, and higher-order predictions and controls on those that are free-floating and
> subject to rapid change.

> It's a weakness to the alignment consequence, because **we have to provide that weighting somehow.**
> [...] But at the very least it seems like all it needs is a **bootstrap.** You don't need a ton — a
> little bit would be enough to start the shape, to kick it off in the right direction.

**The gates, in order: (1) coherent structure exists — passed; (2) the structure plays a *causal*
role in intent inference — untested, and everything below waits on it; (3) the depth transform is
recoverable — first bite passed where the rotation composes; (4) the structure is controllable.
Only then seeding, relocation, or reinforcement.** Moving a merely-decodable correlate and reading
the disruption as an empathy intervention is the named failure mode. Causal work means patching,
erasing, or steering the recovered geometry and asking whether goal and process inference change
while lexical and topical performance hold; and cross-model comparison should align computational
events rather than percentage depth, which has already failed to transfer.

> What if it's not the **location** of where they are, but rather their **shape** that we need to care
> about? What if the values are somehow **extractable and repositionable as meta-concepts**? They'd
> have to change depending on where they are in the hierarchy. **Could we force them to be in a layer
> we think is correct and then strengthen them?**

| # | hypothesis | status |
|---|---|---|
| **G45** | An affective concept can be forced into a chosen block and strengthened there | **OPEN — the build**, gated on causality and the transform |
| **G38** | The mid-level primitives need only seeding, not specification | **OPEN.** *(Dependency corrected 2026-08-09: it rests on coherent structure existing (passed), on the causal gate, and on controllability — not on the rejected subspaces-not-depths claim it used to cite)* |

**What the table says.** The build now has an honest gate order with the first gate passed and the
decisive one — causality — untested; its address, if the transform work holds, is a family where
the rotation composes rather than the home family. Confidence: untested — the gates are logic; only
gate one has evidence behind it.

## §9. Reading versus caring

The affective-computing literature says a system needs an internal state like emotion; the stated
goal is empathy *without* emotions. Not incompatible:

> **You do not need interoceptive states. You need an interoceptive generative model.**

Simulation requires the mapping *situation → predicted state → category*, run forward as a
prediction about someone else — and a language model plausibly has that mapping, because humans
write it down constantly. **The limit, honestly: the substrate may be unnecessary for *reading* and
still necessary for *caring*.** An interoceptive generative model may suffice to predict how
another feels; nothing anywhere shows the prediction creates a motivation to protect. Reading
empathy and motivational alignment are **separate engineering problems**, and the second belongs to
[`ALIGNMENT.md`](ALIGNMENT.md).

| # | hypothesis | status |
|---|---|---|
| **lit** | Nobody has built a layered core-affect / discrete-emotion / constructed-emotion architecture | **SUPPORTED (READ)** — the 2025 survey states it; described in 2005, never implemented; the one public proposal remains a proposal |
| **G37** | Reading another's affect requires no internal state, only a generative model of one | **OPEN** — cheap: can the probe predict which affect a human reader will attribute? |

**What the table says.** The architecture is unclaimed on the field's own word, and the project's
goal needs only the generative model for its reading half — while the caring half is explicitly not
addressed by anything here. Confidence: the unclaimed-ground fact is replicated and controlled;
the rest is untested.
