# Decision traces — what survives in the artifact, and how it is measured

> **Polish** is the density of decisions aimed at **the reader's attention**. **Depth** is the density
> of decisions aimed at **the artifact's content**. Polish is a conscious behaviour that is cognitively
> effortful, so it moves within a piece; depth is largely automatised, so it does not.

**Artifacts preserve decision traces along two independent axes: what the decision targeted, and how
deliberately it was placed. Across the artifact as a whole, those decisions may reduce to layered,
singular, or unrecoverable terminal values.** Polish and depth describe *target*; deliberate and
automatic describe *control*; flattened intent describes *terminal organisation*.

Current verdict, axis by axis: **the target distinction is coherent but unmeasured; the control
distinction is partially supported; terminal topology is conceptually useful but instrument-dead or
untested; and no direct scalar measure of depth yet exists.**

**This file owns** the artifact-facing consequences: which decisions leave traces, how those traces
differ, how they are measured. **It does not own** the latent architecture a model reconstructs
([`THREE_COGNITIVE_LAYERS.md`](THREE_COGNITIVE_LAYERS.md)), the three-way inference itself
([`THE_TRIPLE_INFERENCE.md`](THE_TRIPLE_INFERENCE.md)), or the reader's shortcuts
([`READER_HEURISTICS.md`](READER_HEURISTICS.md)). *(Renamed from `POLISH_AND_DEPTH.md` 2026-08-09 —
the old name had become too narrow for a file that absorbed flattened intent and leakage.)*

---

# Part I — The canonical model

## §1. The coordinate system — target, control, and terminal topology are independent

**Three separate properties, previously conflated into one ladder:**

**1. Decision target.** *Polish*: recoverable decisions directed toward the reader — attention or
comprehension. *Depth*: recoverable decisions directed toward the problem, subject, or artifact
itself. Attraction and translation are subtypes of polish.

**2. Degree of control.** *Deliberate*: consciously placed. *Automatic*: habituated, not actively
held. `emblematic` and `leaked` are the **affect-specific** versions of this distinction, not
synonyms for all deliberate and automatic behaviour.

**3. Terminal-value topology** — a property of the artifact as a whole: *layered* (decisions serve
several partially competing terminal values), *flattened* (many decisions reduce to one), or
*non-invertible* (readers cannot recover a coherent terminal organisation at all).

The control axis cuts across the target axis:

|  | deliberate | automatic |
|---|---|---|
| **reader-directed** | chosen attraction and translation | aesthetic habits, teaching habits, seductive details |
| **problem-directed** | explicit reasoning, case selection, epistemic foraging | applied expertise, facture, routinised process |

**This resolves a standing contradiction: polish is not necessarily conscious, and depth is not
necessarily automatic — those are predicted tendencies, not definitions.** It also shows why a
simple subtraction cannot define depth: aesthetic and teaching behaviour leave automatic shadows,
while epistemic foraging is consciously held but problem-directed. The categories do not subtract
cleanly. And it names the estimator honestly: **applied expertise is a *source* of depth, not the
definition of depth; residualisation is a proposed estimator, not the ontology** (Part III).

The essay already names polish's first half: aesthetics is *"the honeypot... the word for how much an
object forces you to stare at it."* **Polish is honeypot density plus scaffolding density. It is not
a synonym for quality and it is not a synonym for AI** — a ten-item reading sample populated all
four corners of the polish × depth grid, including *"thick on top and just empty beneath."*

**And depth is domain-relative** *(moved from the reader-heuristics file 2026-08-09 — it is a
property of the target, not a reading strategy)*:

> It does not vary within an artifact unless the domain does.

The sharpest definition in the project, because it makes depth a **relation** between writer and
domain rather than an attribute — with its falsifier attached (*depth moves where domain moves*),
and with the consequence that explains the corpus problem: **a relation cannot be measured by
varying one side**, and every artifact-direct measure that died, died reading artifacts alone.
**(HH-10:** depth measured on one maker moves when the domain moves and not otherwise — **OPEN,
blocked on the one-maker-many-kinds corpus its own definition demands** — the same corpus the
values thread keeps arriving at.**)**

No direct test of the coordinate system itself exists; its components are tested below.

## §2. Reader-directed traces — attraction, translation, and movement

> The pieces that the human is putting in **voluntarily** on top — the polish is made up of **two
> things, not just one.** The first would be the **attractiveness**: how much you can make the
> artifact eye-catching. And the second is... **everyone tries to make things understandable to other
> people. We add labels and tags if we're an engineer. We build in metaphor as an artist that's
> understandable across domains. I think that's the second piece.** We also all layer in this
> **translatable** layer.

|  | what it is for | what it looks like |
|---|---|---|
| **attraction** | being *attended to* | contrast, rhythm, the punchy opener, the confident frame, the acronym that signals membership |
| **translation** | being *understood* | labels and tags, section structure, worked examples, metaphor that carries across domains |

The two have different causes and different predictions: attraction is a performance aimed at a
specific audience on a specific occasion; translation is aimed at comprehension, and a maker who
stops performing does not usually stop labelling. Translation is the *bard*'s second motivation
([`READER_HEURISTICS.md`](READER_HEURISTICS.md) §7) made measurable. His own doubt is the load-bearing
test: *"I don't know if they're extricable or not."*

**Movement within an artifact** is the other reader-directed prediction:

> If anything it's implying that **polish gets thinner over time as people get lazy while their depth
> remains constant. That polish is a conscious behaviour that is cognitively effortful**, perhaps. I
> think it was more common for it to go thick to thin.

His readings contain both directions — *"thin to start but got thicker as it went down... but it
stayed equivalently thick throughout on the bottom"* — so what is stable is the **asymmetry, not the
direction**: the performance is what changes, whichever way it changes.

> **Depth is stationary within an artifact; polish is not. Polish variance across an artifact is a
> maker signature; depth variance is not.**

| # | hypothesis | status |
|---|---|---|
| **PD-1** | Depth-side quantities show smaller between-position variance than polish-side quantities | **OPEN — the definitional test; still no valid run.** *If both move equally, the distinction is not real and this document is wrong* |
|   | | *— first attempt (2026-08-09) scored zero essays: the window cache was built at the wrong size and the verdict fired on empty data; quarantined, instrument repaired, re-queued* |
| **HH-3 / L39** | The reader's own affective series moves more within human artifacts than machine ones | **SUPPORTED (test), first pass.** Human long-form variance 0.0102 vs machine 0.0065 at matched series length, *p* = 0.002 — the flat-machine signature, measured reader-side; register rides along uncontrolled |
| **S-6** | Practised polish decays faster than depth | **SUPPORTED (sim)** at 6.5×, with synthetic polish **flat** |
| **PD-3** | Machine artifacts show flat polish across position — no maker to tire, no register to drift toward | **OPEN as an artifact-side measure; its reader-side cousin just landed (the HH-3 / L39 row)** |
| **PD-2** | Polish *decays* specifically, rather than merely moving | **OPEN**, and depends on PD-1 |
| **PD-4** | Polish variance is larger in less practised makers | **OPEN** |
| **PD-29** | Polish separates into attraction and translation | **OPEN — everything in this section depends on it** |
| **PD-30** | Attraction decays across an artifact; translation does not | **OPEN** |
| **PD-31** | Generated text carries attraction but not translation | **OPEN** — translation structure is countable where effort is not |
| **PD-32** | Translation is denser where the maker expects a distant reader | **OPEN** |

**What the table says.** One real measurement: the reader's affective series moves through human
long-form and stays comparatively flat through machine text — the signature this section predicts,
on its first pass. Everything else is the simulation's 6.5× decay asymmetry plus unrun definitional
tests, with the attraction/translation split gating the lot. Confidence: the movement result is one
bad test away (one corpus pairing); the rest is untested or sim-only.

## §3. Automatic traces — leakage, concealment, and the channels that carry them

> **leaked** — a layer that is TRUE... emotional leakage that can show up in your text
>
> **emblematic** — a conscious social decision

He arrived at that split from ten artifacts and a think-aloud. It maps onto the field's central
unresolved debate — leaked onto primary-process core affect, emblematic onto constructed emotion —
and the reconciliation position (*basic emotion theories are theories of emotion; constructed
emotion is a theory of feeling*) requires both to be true of different things. The two layers should
not be assumed to share a value set; giving both the same eight concepts is a named simplification.

**It also diagnoses the field's LUST problem, called before the argument existed:**

> I think they were just catching the fact that leakage — they were assuming that **leaked fear and
> performed fear are the same thing.** [...] That's why lust is kind of bullshit in this framework,
> because **the easiest thing to catch is the performed section.**

A questionnaire reaches only the performed layer, so LUST is the system least available to it — for
social rather than neural reasons. Artifacts have no such limit. Its signature is his: **the thing a
reader politely glosses over** — *"someone ends up talking about feet for a sentence too long and
you're like, ooh, buddy."*

**No additions to the eight concepts:** *"We shouldn't add anything, because that's kind of just
where the literature is right now."*

**Concealment: the shield matches the leak** — corrected before the test ran:

> Leaked greater than emblematic **doesn't even count as concealment**... if anything the emblematic
> would get larger. **You perform louder to cover up. I get extra quiet if I'm extra angry. The
> shield matches the leak.**

**The cheap channel for automatic traces is function words:**

> **leaked ≈ function-word distribution. emblematic ≈ content-word choice.**

Function words are produced non-consciously, are topic-independent, stable across an author's
corpus, and very hard to fake — the assumption authorship attribution already runs on. His
automaticity intuition *is* that mechanism: style survives intent because it was never held.

> The goal of Sounding Line is just to be able to measure depth. It's just that.

Depth is decisions recoverable — and the automatic ones are a class of decisions this project spent
a long time not counting.

| # | hypothesis | status |
|---|---|---|
| **S-3** | An involuntary leak channel is readable | **SUPPORTED (sim)** at 0.90 |
| **T-4** | Amplifying the display makes concealment *more* detectable — his direction, against mine | **SUPPORTED (sim)**, surviving a reader wrong about almost everything including a 50% channel swap — but **failing at 25% concealment: it reads effort spent hiding, and catches heavy concealers only** |
| **PD-12** | Function words have spare capacity beyond author identity | **SUPPORTED (test).** Author held fixed, they separate different works by the same person at twice chance, ten of ten authors above chance |
| **L16** | Function words separate specified maker states, once the design has power | **SUPPORTED (test) on all three ladders**, 1.6× to 3.0× chance, scaling with the manipulation. Owed: the fair induction control |
| **PD-11** | Function words carry maker *state*, not only identity | **AMBIGUOUS (test)** — 1.80× chance at *p* = 0.0047 against a pre-registered 2.0× bar; the threshold was missed, the effect is significant; owed its powered re-run |
| **PD-14** | Reading the model's activations reaches the leaked layer where its text does not | **SUPPORTED (test), and it became the live path.** The interpretation lives here; the empirical activation rows live in [`THREE_COGNITIVE_LAYERS.md`](THREE_COGNITIVE_LAYERS.md) Part II |
| **G32** | Polish correlates with late structure, leakage with early | **OPEN** — the depth-band version of this section's split |
| **PD-13** | Asking a model *"what stance is performed"* reaches the leaked layer | **REJECTED by construction** — it returns a content-word judgement either way |
| **PD-15** | Attention dwell past argumentative need is measurable | **OPEN.** Nothing built; needs a model of argumentative need. *(Absorbs G30, which duplicated it.)* |
| **PD-16** | Cognitive-load signatures leak despite narrative management | **OPEN** — take the deception literature's features, not its promise |
| **G87** | Low-visibility features carry *who*; high-visibility features carry *what* | **SUPPORTED (test), a clean double crossover on the first pass (L41).** Invisible habits identify the author at 0.78 vs 0.38 for visible features; visible features separate draft-stage at 0.48 vs 0.30 — the pottery prediction, measured |
| **G28** | `leaked` and `emblematic` do not come back as the same distribution | **OPEN — until this runs, every leak result is equally compatible with the probe asking one question twice** |
| **G29** | If one layer separates and the other does not, it is `leaked` that fails | **OPEN, predicted in advance** |
| **PD-11b** | The first function-word attempt answered its own question | **VOID (test)** — ran at 38% power |

**What the table says.** The automatic channel is real on every instrument that has touched it:
readable in simulation, twice chance on real authors with identity held fixed, separating specified
states on all three ladders, concealment detectable in his predicted direction rather than mine —
and now stage-differentiated exactly as the pottery import predicts, with the invisible habits
carrying identity and the visible features carrying situation. What is missing is the license to
call it *affect* rather than *style* — the induction control has never run on this channel, and the
two-layers-are-two question has never been asked. Confidence: the capacity results are replicated
and controlled; the visibility crossover and the state reading are one bad test away each; the sim
rows are sim-only.

    Timeline on the leaked layer. Proposed as the cheap channel; first run underpowered and VOID;
    re-run with purpose and topic fixed came back at 1.80x against a 2.0x bar; the activation route
    was built meanwhile and became the live path; the 2026-08-07 powered re-run then SEPARATED on
    all three ladders. The cheap channel was never dead; it was measured three times at a sample
    size that could not see it.

## §4. Terminal organisation — layered, flattened, and non-invertible

Logged before Gate 3 read out, so it could not be used to reinterpret it:

> I don't think that it's the case that corporate work necessarily has less decision-making that went
> into it... what actually that means is that their motivation is immediately reconstructable and that
> motivation is always money. That's why corporate work seems soulless. **It's not quite the same as
> why AI work seems soulless, which is that you can't arrive at a motivation.**
>
> Humans can't really take action without intention. It's just that **corporations steal your
> intention and replace it with money.** [...] It is a flattening of human motivation, and that's why
> it's so repulsive to artists that live in a world of motivation extraction.

| | decision density | motivation | invertibility |
|---|---|---|---|
| **individual human** | high | many terminal values, layered | recoverable, multi-level |
| **corporate** | **also high** | **one terminal value** | **immediately recoverable, one level** |
| **machine** | ? | none coherent | **non-invertible — the wall** |

"Machine has no motivation" remains a hypothesis; **non-invertibility is the observation.** Under
this reframe, Gate 2's high purpose-agreement on commercial work was the instrument working: an
immediately reconstructable motivation *should* produce agreement between independent readings —
recorded as the reason to build the successor design, not as evidence for it (the hypothesis
arrived after the result). What the instrument should report: *whether a maker's terminal value is
singular or layered* — never built. His own caution kept: measure **singularity of terminal
value**, not presence of a profit motive.

**Soul is the layered end named from the maker's side** *(moved from the triple inference
2026-08-09 — motivational variety is an artifact property)*:

> When we talk about something having **soul**, what that means is **a variety of motivations**. And
> it tends to travel with expertise — because as processes are baked in with automaticity, you lose
> conscious access to them and they start to be tied more to your **drives**.

The chain: practice → automaticity → the decision leaves deliberate control → it is made by
whatever is underneath → an expert's artifact carries more drive-derived variety than a novice's,
without the expert choosing it. This is the mechanism the residue account of values runs on
([`THE_TRIPLE_INFERENCE.md`](THE_TRIPLE_INFERENCE.md) §5), and it explains why an expert cannot say
*why* they did something while their artifact shows more of what they are.

**Dense polish as concealment** is the same claim seen from the artifact side:

> I do think the density of decision-making is by necessity a little bit thinner on corporate art.
> **Aesthetics that are so dense that they're intended to conceal the poor motivation beneath it. A
> particularly dense top layer.**

**And stacked motivations are its mirror** — what happens at the layered end:

> If you gave a machine a bunch of different goals and told it to balance all of them before it wrote
> something, it would actually get **more of a purpose ranking along any intent register.**
>
> We should **start at the extremes** — three pages of different motivations stacked on top of each
> other that are all reasonably capable of aligning, against a machine writing with just one or two.

| # | hypothesis | status |
|---|---|---|
| **PD-18** | A machine given many aligned motivations reads as more intentional than one given two | **REVERSED IN DIRECTION (test) — his contest of the original null was right.** The revived features, the flagship ratio, and the (now echo-suspect) recovery all peak on the most-stacked corpus |
| **PD-19** | The effect *accelerates* at the top of the ladder | **NOT SUPPORTED (test), twice** — a straight line that flattens at the top; the saturation echoes the bits ceiling |
| **PD-6** | Commercial work shows *higher* purpose agreement than individual work | **OPEN, pre-registered before Gate 3** — Gate 2 is suggestive and cannot serve as the test |
| **PD-8** | Commercial decision density is *not* systematically lower than individual | **OPEN** |
| **PD-9** | Machine text shows low agreement *and* low breadth — no coherent maker-state, as against a flattened one | **OPEN** |
| **PD-10** | Singularity of terminal value is measurable at all | **OPEN — the successor instrument**, needing a corpus this project has not seen |
| **G114** | Independent readers' goal-guesses converge more where intent is dense | **NOT SUPPORTED (test), three designs deep.** Bits recovered died to empty answers; token overlap read topic; judge-rated similarity with topic held fixed saturates near 0.9 on everything and the ten-specification dose gap comes out at −0.02 — wrong sign, negligible. The third instrument produced orderly numbers (books score lowest, plausibly summarisation difficulty) and the dose is simply not in them |
| **T-2 / T-9** | Motivational variety is measurable as breadth of recovered purpose | **INSTRUMENT DEAD (sim, twice)** — the breadth measure tracked how hard the goal is to recover, not variety; at matched difficulty the diversity excess is negative. The simulation itself states it cannot test whether practice *causes* drive-multiplicity |
| **G55** | Diversity rises with expertise while agreement about purpose stays flat | **OPEN** — a two-measure prediction using quantities that already exist, and the second attempt must survive a difficulty control that neither prior try would have |
| **PD-7** | Commercial work shows lower purpose *breadth* | **INSTRUMENT DEAD (sim, twice)** — the breadth measure read difficulty |
| **G3** | Half A of a web corpus contains more recoverable method than half B | **VOID (test), twice over** |

**What the table says.** The layered end of the topology is the best-evidenced thing in this file —
three independent measures peak where motivations stack — while the flattened end now carries its
first genuine negative: reader convergence has failed to move with intent density in three separate
designs, the last with topic held fixed and an instrument that produced orderly numbers, so
agreement-between-readers looks like a property of coherent text rather than of dense intent. The
breadth-style measures read difficulty, and the singularity measure has never been built. The soul
claim's mechanism matters beyond this section: if expertise does not move decisions into drives,
the residue account of values loses its engine. The topology remains a good description whose
positive half is measured and whose flattened half keeps refusing to be. Confidence: the
stacked-motivations reversal is replicated and controlled; the convergence null is one bad test
away; the rest is untested or instrument-dead.

# Part II — The measurement ledger

## §5. Reading the artifact directly — the funnel, the deaths, and the three survivors

**Depth is decisions recoverable, so the obvious instrument counts them from the text. Ten measures
tried; all ten died to length, register, or vocabulary — and then the final three deaths turned out
to belong to a broken control, not to the features.**

| # | hypothesis | status |
|---|---|---|
| **PD-21** | Published linguistic features track how much intent was specified, once machine-detectors are removed | **REVERSED (test).** Under the fair induction control **all three candidates revive on all three ladders** — conditionals (+0.65/+0.51/+0.73), contractions (+0.43/+0.48/+0.32), phrasal coordination (−0.41/−0.27/−0.44), nine of nine at *p* ≤ 0.007 |
| **PD-20** | Decision density can be counted from an artifact | **REJECTED (test)** — it was word count (0.88), then vocabulary diversity (−0.88); two confounds in sequence, nothing underneath |
| **PD-22** | Causal connectives track depth | **REJECTED (test)** — ranked the ladder, then inverted on humans; it measures explicitness |
| **G116** | Specified intent adds description length — the essays' Kolmogorov claim | **REJECTED (test)** — incompressibility flat across all rungs; human long-form matches machine text at matched length |
| **PD-23** | A larger feature bank beats a small curated set | **REJECTED (sim)** — sixty generic features gain little and lose more in the worst case |
| **PD-24** | Weak effects can be stacked into a usable detector | **OPEN, with a warning** — stacking shared confounds produces a strong confound; the ladder is the only thing that tells the difference |
| **rung −1** | No measure reads noise as maximum intent | **SUPPORTED (test)** — the only ceiling control in the project |

**What the table says.** Every cheap property of a text that correlates with intent also correlates
with something cheaper, and the cheaper thing wins — down to raw description length. The funnel
that removes machine-detectors (61 of 81 replicated features) is the durable product, and the three
features that survive its fair-control version are the only artifact-side signals standing — which
is what a stacking instrument needs: channels with different failure modes. Confidence: the funnel
and the deaths are replicated and controlled; the three revivals are days old — one bad test away
by age.

    Timeline on counting decisions. Counted directly and it was length; corrected and it was
    vocabulary; replaced with a 342-feature bank screened against the ladder (81 replicated, 61 of
    them machine-detectors); the three survivors died to the induction check; the induction check
    then failed ITS check (regressors contained the dose); under the fair version all three revive.

## §6. Controlled change — revision, and the one human comparison

**86 university students, one prompt, three drafts each — maker, prompt, topic, register, and genre
all fixed by construction.**

| # | hypothesis | status |
|---|---|---|
| **PD-26** | Something measurable changes as one person redrafts | **SUPPORTED (test), one coherent thing:** at matched length, revision raises lexical sophistication — longer, rarer, more polysyllabic words, fewer stopwords — one factor under six names, sign agreement 70–78% across authors |
| **PD-27** | That effect is length | **REJECTED (test), the trap fired as pre-registered** — raw survivors were all counts; length-matched, 17 of 315 and none of them counts |
| **PD-28** | The surviving effect is polish, not depth | **DEPTH-SIGNAL (test, L42).** Across 1,711 labelled revisions, the sophistication shift holds at full strength among *content*-labelled revisions — the rare-word component is stronger there than in surface-labelled ones. **The first measured depth signal on human text** |

**What the table says.** The project's one controlled human comparison found a real, length-robust
effect — and the labels on disk have now answered what it is: **the effect survives among
content-only revisions, which makes it the first depth signal ever measured on human text** rather
than a polish artifact. The hurried-versus-careful commission (the confound archaeology never
tested) remains the designed extension, and the natural next step is the same split under sharper
sophistication measures than the three first-pass proxies. Confidence: the revision effect is one
corpus away from replicated; the depth reading is one bad test away — first-pass proxies,
sentence-level, one corpus.

## §7. Reader-side measurement — the second channel, briefly

The reader model supplies a second measurement channel for everything above: per-layer affect
projections, within-text ratios, and specification-conditional scoring. **Its canonical rows live in
[`THREE_COGNITIVE_LAYERS.md`](THREE_COGNITIVE_LAYERS.md) Part II** and are not duplicated here. Two
conclusions transmit: within-text ratios survive where reader-state measures die, and the
within-artifact *movement* of the reader's affective series carries the polish signature (§2).

# Part III — Contested estimators and prior art

## §8. Residualisation — the proposed depth estimator, and its objections

> **Polish is surface-level goals** — all of the conscious ones. And **three of them are reliable
> enough to treat as always present**: attractiveness, teaching, and epistemic foraging.
>
> That gives you **three rule-outs**, and it lets you focus on **the residual** — everything else that
> doesn't meet one of those three goals. And that ends up looking like **process, expertise, minus
> whatever the goal was.**
>
> **Depth is expertise being used, stripped of attractiveness, teaching and epistemic foraging.**

Under §1's coordinates this is a **candidate estimator, not a definition** — and it faces four
recorded objections. **The habit-shadow objection, his own and the serious one:**

> The residual is habits that have been unconsciously baked into your process, right? **But
> repetition does appear in other places.** It's not just the leakage you continually show that gets
> baked into your habits. **It's also the aesthetic habit and the teaching habit**, both of which will
> be baked into the process as goals. So if you can't fully account for them — **and I don't think
> you'll be able to** — then it does mean you get that seductive details effect.

The subtraction removes *goals*; automaticity does not care what a repeated action was for, so the
three rule-outs leave habit-shaped shadows that survive the subtraction — which also explains the
seductive-details effect from the inside. **Second**, the collapse objection: depth-as-expertise is
a property of the maker's competence, while depth-as-decisions-recoverable is a property of what a
reader can get out, and the two come apart. **Third**, separability: *"I don't know if they're
extricable or not"* — if an expert's aesthetic choices *are* their expertise, subtraction removes
signal. **Fourth**, the field that tried it: archaeology's forty years of expertise-from-product
carry **no blind tests of skill classification, no confusion matrices**, and the one properly
factorial study reverses the result —

> **"The skills reflected in these assemblages cannot be directly assessed based on standard
> quantitative proxies, which are highly raw material and technique dependent."**

— with skill signals mostly vanishing once the medium is controlled. The honest asymmetry: their
confound is raw material; our medium is language, far more uniform, and the ladder is precisely the
identical-precore control their literature says is underused. Three imports stand regardless:
**errors are clustered, not Poisson** (a rate on a small sample measures which burst you sampled);
**distinctions live in the residual, not the whole sequence**; and **nobody has ever tested expert
work done deliberately fast against novice work** — cheap for us, impossible for them. On the
subtraction's mathematics, his reservation stands recorded:

> Partialling out — I'm familiar with it, but I'm not sure it's mathematically appropriate for what
> we're doing here. We kind of need to find something that works with the alignment research as much
> as possible.

Partialling is linear and assumes the nuisance is additive; the habit shadows are neither. The
value ladder this estimator was meant to serve — surface goals → applied expertise → values — is
[`THE_TRIPLE_INFERENCE.md`](THE_TRIPLE_INFERENCE.md) §4's residue-of-expertise claim; it is not
re-derived here.

## §9. Vocabulary and prior art — the naming search

Run because he asked for existing terms. The surface layer has **no** established term covering both
attraction and translation (audience design is a social-identity mechanism; reader-based prose is
text-only and normative; *surface features* in the expertise literature is a perceiver-categorisation
trap; aesthetic labour is bodies, not artifacts). The deep layer's terms exist and live in
archaeology and art history: **chaîne opératoire** (the operational sequence reconstructed backwards
from the object, skill included), **facture** (the making, legible in the made), **technological
style** (patterning largely invisible to the maker), the **Morellian method** (attribution from
involuntary detail — our leaked layer, named in 1870). *Tacit knowledge* is rejected: it commits us
to inarticulability. **The critique of chaîne opératoire is almost word for word the attack we will
face** — *"overformalized,"* an *"illusion of reading the minds of prehistoric knappers"* — and his
reading inverts it:

> I actually find that line about the attack on chaîne opératoire to be **quite optimistic**.
> Something that's over-formalised and also gives the illusion of reading the minds of people that
> aren't there, and the creators — **sounds frankly like exactly what we're looking for.** It's
> unscientific, but also perhaps a very natural human thing that does have error bars that are by
> definition unscientific. **The natural process probably is captured, or is related to and uses
> several of the main channels that we all naturally use anyway.**

The limit that survives the inversion: an illusion that reliably reproduces a human reading licenses
claims about *what a reader recovers*, not about what the maker did — Baxandall's guardrail. His
**inferential criticism** (the Charge — "Paint!" — and the Brief, the situated problems) is the
framework forty years early, including our position on intention: *"not a biographical mental fact"*
but a condition posited in arranging the circumstantial facts. Rejected names, kept as a record:
*inverse planning* (takes action sequences; we have residue — that gap is the contribution), *the
design stance* (runs forward), *reverse engineering* (recovers mechanism, not values), anything with
*empathy* in it (43 catalogued definitions). For the subtraction: **partialling out** is the
standard name; a reviewer will note that in statistics the residual is the *error* while here it is
the quantity of interest — flag it always.
