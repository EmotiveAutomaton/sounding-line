# Polish and depth — two decision densities, split by what the decision targets

**Written 2026-08-03** after session 01 produced a thick/thin assessment for ten artifacts and he
rejected my summary of it. **Merged 2026-08-07** with what used to be `FLATTENED_INTENT.md` and
`LEAKAGE.md`. Pre-merge originals in `../archive/`.

> That's not quite what I meant. Surface thickness kind of stayed the same throughout, I feel like.
> But the style drift implies there was more. **I feel like surface and depth thickness are nebulous
> concepts that we need to hard define at this point.**

He was right that they were nebulous — ten readings used the terms and no two used them identically,
including mine.

**Naming, settled 2026-08-07: the top layer is *polish*, not surface and not veneer.** His own
correction, and under the theory **polish is just aesthetics**. Used consistently throughout this
file and everywhere downstream.

---

## §1. The definitions

Both are **decision densities**, which keeps them inside the theory's one primitive rather than
introducing a second. What separates them is **what the decision is aimed at**.

> **Polish** — the density of decisions whose target is **the reader's attention**. Contrast, rhythm,
> the punchy opener, the confident frame, the acronym dropped to signal membership, the professional
> veneer. Decisions about *being attended to*.
>
> **Depth** — the density of decisions whose target is **the artifact's content**. What to include,
> what to cut, which abstraction to use, which case to handle, which claim to defend. Decisions about
> *the thing itself*.

The essay already names the first: aesthetics is *"the honeypot... the word for how much an object
forces you to stare at it."* **Polish is honeypot density. It is not a synonym for quality and it is
not a synonym for AI.**

### The objection this has to survive, and it does

*Isn't polish just legibility, or quality, renamed?* **No, and the corpus settles it** — all four
corners are populated by real artifacts in a ten-item sample, which is what a genuine second dimension
looks like:

| | polish | depth | |
|---|---|---|---|
| roofing company's marketing page | low | high | read as unambiguously human and competent |
| machine-written affiliate content | high | none | |
| angry expert essay | high | high | **the polish work is the reason it lands** |
| the one he called *"thick on top and just empty beneath"* | high | low | |

## §2. The asymmetry, and why it should exist

**His revision, and it is the substantive contribution here:**

> If anything it's implying that **polish gets thinner over time as people get lazy while their depth
> remains constant. That polish is a conscious behaviour that is cognitively effortful**, perhaps. I
> think it was more common for it to go thick to thin.

**This follows from automaticity, which is what makes it a prediction rather than an observation.**
The essay's account of compression is that practised decisions get bundled into routines and stop
costing anything — *"automaticity is the caching of human struggle."*

An expert's **content** decisions are largely automatised: practised, low metabolic cost, no reason to
decay across one artifact. An expert's **polish** decisions are mostly **not**, because polish is a
performance aimed at a specific audience on a specific occasion and has to be held consciously.
**Under a metabolic budget, a consciously held performance is exactly what degrades as the maker tires
or relaxes into their own register.**

| | automatised | cost | predicted trajectory within one artifact |
|---|---|---|---|
| **polish** | mostly not | high, conscious | **decays** — thick to thin |
| **depth** | largely yes | low, cached | **flat** |

**This is a falsifiable claim about position within an artifact, and for most of this project's life
nothing measured position** — every quantity the probe emitted was an artifact-level scalar.

## §3. What the readings actually showed, kept honest

**The transcript contains both directions and the record should say so rather than tidy it:**

- *"thin to start but got thicker as it went down... but it stayed equivalently thick throughout on
  the bottom. There was depth to it, but the surface level shifted."*
- *"tried to start simple, was less successful by a huge margin, and then slowly got more complex on
  the surface layer. But the deep layer stayed equivalently deep throughout."*
- and the revision above — *"more common for it to go thick to thin."*

**What is stable across all three is the asymmetry, not the direction:** polish moves within an
artifact and depth does not. Two of the three show polish *rising* — a maker starting in a simplified
register and drifting toward their own — **which is the same mechanism running the other way. The
performance is what changes, whatever direction it changes in.**

> **Depth is stationary within an artifact; polish is not. Polish variance across an artifact is a
> maker signature; depth variance is not.**

**The decay-specifically claim is a second, sharper one and it needs the first to hold first.**

| # | hypothesis | status | evidence |
|---|---|---|---|
| **PD-1** | Depth-side quantities show smaller between-position variance than polish-side quantities | **OPEN.** *If both move equally, the distinction is not real and this document is wrong* | never run as stated |
| **PD-2** | Polish decays across an artifact specifically, rather than merely moving | **OPEN**, and depends on PD-1 | — |
| **PD-3** | Machine artifacts show **flat polish across position**, because there is no maker to tire and no natural register to drift toward | **OPEN, and it is the sharper prediction:** the signature of the machine is not thin depth but **a polish that does not move** | never run |
| **PD-4** | Polish variance is **larger in less practised makers**, since an expert has partly automatised the performance too | **OPEN.** The one prediction that cuts against a naive reading where expertise means more of everything | never run |
| **PD-5** | Practised polish decays faster than depth | **SUPPORTED (sim)** — **6.5× faster**, and synthetic polish is **flat**, which is PD-3's direction | sim S-6 |

    Timeline on the polish-variance idea. Predicted from automaticity; supported in simulation at
    6.5x; then measured on real text as within-artifact variance of 342 linguistic features and found
    NOTHING -- 0 of 313 features survive on human text with maker, prompt, topic and register all
    fixed, against 12 for the plain average. See ../theory/HUMAN_HEURISTICS.md for the full timeline,
    because the negative result belongs to the detector claim rather than to the definition.

**The definitions in §1 are not damaged by that null.** What died is one operationalisation — variance
of surface *features* — on one axis, redrafting, which may not vary the performance at all. **PD-1 as
stated has still never been run, because it asks about depth-side and polish-side quantities
separately and the test that failed measured neither.**

## §4. Flattened intent — three categories, and the project ran a two-category design

**Logged 2026-08-03 while Gate 3 was still running and before any result was read.** He raised it
unprompted and chose to log it then precisely so it could not be used to reinterpret Gate 3
afterwards. **That timing is what makes it evidence rather than commentary.**

> I don't think that it's the case that corporate work necessarily has less decision-making that went
> into it... what actually that means is that their motivation is immediately reconstructable and that
> motivation is always money. That's why corporate work seems soulless. **It's not quite the same as
> why AI work seems soulless, which is that you can't arrive at a motivation.**
>
> Humans can't really take action without intention. It's just that **corporations steal your
> intention and replace it with money.** [...] It is a flattening of human motivation, and that's why
> it's so repulsive to artists that live in a world of motivation extraction.

**This says the corpus split was mis-specified.** The project treated commercial filler as *low
intent*. The claim is that it is **dense intent with a flattened terminal value** — many real
decisions, all instrumentally subordinate to one goal.

| | decision density | motivation | invertibility |
|---|---|---|---|
| **individual human** | high | many terminal values, layered | recoverable, multi-level |
| **corporate** | **also high** | **one terminal value** | **immediately recoverable, one level** |
| **machine** | ? | none coherent | **non-invertible** — the wall |

**Three categories, not two.**

### It predicted a result that had already been recorded as a failure

Gate 2 found, and I reported as the probe converging on garbage because the garbage is well-organised
— *"a quality classifier with extra steps"*:

| artifact | purpose agreement |
|---|---|
| games build guide | **1.00** |
| brand page | **1.00** |
| plumber template | 0.67 |
| a developer building his own game | **0.33** |

**Under this hypothesis that is the instrument working correctly.** Commercial motivation is
immediately reconstructable, so independent readings agree. An individual's layered motivation is not,
so readings differ. **High agreement on commercial work is the predicted signature, not the bug.**

**That cannot be claimed retrospectively** — the hypothesis arrived after. It is recorded here as the
reason to build the successor design rather than as evidence for it.

### What it would make the instrument

SPEC §1 says *this is not an AI detector, it is an intent detector.* **This suggests a third thing and
a more useful one:**

> It reports **what a maker's decisions were ultimately for**, and whether that terminal value is
> **singular or layered.**

**More socially defensible than either detection or intent-density.** It never says *a machine wrote
this* and never says *this is low effort*. It says *every visible decision here reduces to one aim* —
a statement about the artifact, evidenced, and rebuttable.

**And it explains his own repulsion response better than the alternative account did:** what repels is
not incompetence but **the recognition that the motivation has been flattened** — motivation extraction
performed on a reader who reads motivation for a living.

**One caution he attached himself:** *"always money and basically nothing else"* is stronger than the
evidence needs. **The defensible form is structural** — a corporate artifact has a *single terminal
value* to which all instrumental decisions reduce. Whether that value is always money is an empirical
claim this project is not positioned to make, and the instrument should measure **singularity of
terminal value**, not presence of a profit motive.

| # | hypothesis | status | evidence |
|---|---|---|---|
| **PD-6** | Commercial work shows **higher** purpose agreement than individual work, not lower | **OPEN, and pre-registered before Gate 3** | Gate 2 is suggestive and was read many times, so it cannot serve as the test |
| **PD-7** | Commercial work shows **lower purpose breadth** than individual work | **INSTRUMENT DEAD (sim, twice).** `purpose_breadth` tracks **how hard the goal is to recover**, not variety of purpose. **This was the sharp prediction and its measure is gone** | sim T-2, T-9 |
| **PD-8** | Commercial decision density is **not** systematically lower than individual | **OPEN** | never isolated |
| **PD-9** | Machine text shows **low agreement AND low breadth** — no coherent maker-state to converge on, as against a flattened one | **OPEN** | never run |
| **PD-9b** | Half A of a web corpus contains more recoverable method than half B *(the project's primary for a month)* | **VOID (test), twice over.** Its stability check failed — variation *within* an artifact was **nine times** the difference *between* halves — and the statistic it used reads a large number where the truth is zero and is undefined in most cases. **And independently: 76 features separate the two halves**, meaning they differ so broadly that almost any measure would. **Separating them was never evidence of anything** | `results/gate3`, sim S-1 |
| **PD-10** | Singularity of terminal value is measurable at all | **OPEN, and it is the successor instrument.** Needs a corpus this project has not seen; refitting to the 51 artifacts already read would be unfalsifiable | — |

### Dense polish as concealment — the predicted inversion

> I do think the density of decision-making is by necessity a little bit thinner on corporate art.
> **Aesthetics that are so dense that they're intended to conceal the poor motivation beneath it. A
> particularly dense top layer.**

**This predicts a specific inversion — high polish density with low depth density, concentrated in
commercial work — and there is already a number pointing at it.** The register control found
commercial copy sits **26% of the way** from essays toward machine text. **We read that as a
confound. This says it may be the phenomenon.**

**It is also §4's claim seen from the artifact side rather than the maker side:** a flattened terminal
value produces thin depth, and the polish is what covers for it.

### Stacked motivations — and he disbelieves our null

> If you gave a machine a bunch of different goals and told it to balance all of them before it wrote
> something, it would actually get **more of a purpose ranking along any intent register.**
>
> We should **start at the extremes** — three pages of different motivations stacked on top of each
> other that are all reasonably capable of aligning, against a machine writing with just one or two.

**This is the mirror of §4.** Flattened intent is *one* terminal value; this asks what happens at the
opposite end. **And it is [`THE_TRIANGLE.md`](THE_TRIANGLE.md) TR-13 restated as an experiment** —
*all goals partially satisfied at once* is exactly what three pages of aligned motivations produces.

**His specific complaint is that our manipulation was too weak**: the ladder tops out at ten short
specifications, and machine-text-written-with-purpose was recorded RULED OUT on that basis. **He is
5 for 5 on methodology, so the prior says take it seriously.**

| # | hypothesis | status | evidence |
|---|---|---|---|
| **PD-17** | Commercial work shows high polish density with low depth density | **OPEN**, and blocked on PD-1 — the two densities have never been measured separately | the 26% number is suggestive, not a test |
| **PD-18** | A machine given many aligned motivations reads as more intentional than one given two | **RULED OUT (test) at ten specifications** — died to length and register. **CONTESTED by the curator on grounds of manipulation strength.** The extreme ladder runs 0/2/10/30/60 with length nailed by rejection sampling | `corpora/ladder3`, `FINDINGS.md` |
| **PD-19** | The effect *accelerates* at the top of the ladder | **OPEN** — and acceleration rather than a straight line would be evidence for TR-13 specifically | ladder3 |

## §5. Leakage — the channel where the automatic decisions live

**This is the other half of the polish/depth split, seen from the maker's side.** Polish is held
consciously and slips. **Leakage is what was never held at all.**

> **leaked ≈ function-word distribution. emblematic ≈ content-word choice.**

**Function words** — pronouns, articles, prepositions, conjunctions, auxiliaries — are produced
non-consciously, are topic-independent, and are stable across an author's corpus. Under 0.1% of
vocabulary, roughly **60% of words used**, and **very hard to fake**, which is why authorship
attribution works at all. They track **psychological state**, not only identity: `I`-frequency
predicts depression better than negative-emotion words do.

**His automaticity intuition is the mechanism stylometry already runs on.** He described leakage as
*automaticity bending* — the word choice the author never noticed making. **That is exactly the
assumption behind function-word attribution: style is unconscious, so it survives intent.**

**Two distinct signatures fall out, and they are not the same measurement:**

| | what it is | measurable as |
|---|---|---|
| **function-word drift** | the automaticity bending | deviation from the author's own baseline, or from register norms |
| **attention dwell** — his *feet* example | content-side, not style | text spent on something past what the argument needs |

**The first needs a baseline** — multiple artifacts by one maker, or a register model. **The second
needs a model of argumentative need.** Neither needs a language model to introspect.

**And a third channel, from the deception literature:** text length, fluency, revisions, repetitions,
reformulations, and cognitive-load signatures — reduced concrete detail, oversimplification,
generalisation. **These leak despite the writer managing the narrative.** Caveat kept: a 2025
cross-linguistic study argues the limits of deception detection from text are real and structural.
**Take the features, not the promise.**

### Why this is the depth measurement rather than scope creep

> The goal of Sounding Line is just to be able to measure depth. It's just that.

**Depth is decisions recoverable.** A whole class of decisions — the automatic ones, the compressed
ones, the ones the maker never noticed making — has a measurement channel this project spent a long
time not using. **The essay already said the automatised decisions count; nothing ever counted them.**

| # | hypothesis | status | evidence |
|---|---|---|---|
| **PD-11** | Function words carry maker *state*, not only identity | **AMBIGUOUS (test), and this project has been recording it as a clean negative.** With purpose and topic **fixed by construction**, function-word style separates four specified affect states at **45% against 25% chance — 1.80×, binomial *p* = 0.0047, 2.92 sd above chance.** The pre-registered pass needed 2.0×. **The threshold was missed; the effect is significant.** Per-affect: care 60%, seeking 50%, rage 40%, fear 30% | `results/d0b` |
| **PD-11b** | The first attempt at PD-11 answered its own question | **VOID (test).** It ran at 38% power — its median outcome under a real effect was below its own threshold | `results/leakage` |
| **PD-12** | Function words have spare capacity beyond author identity | **SUPPORTED (test).** Holding the author fixed, they separate *different works by the same person* at **twice chance**, every one of ten authors above chance | `FINDINGS.md` tier 2 |
| **PD-13** | Asking a model *"what stance is performed"* reaches the leaked layer | **REJECTED by construction.** It returns a content-word judgement, so it is an **emblematic** instrument on both its outputs. **The leaked layer needs a different kind of measurement, not a differently-worded prompt** | — |
| **PD-14** | Reading the model's activations reaches the leaked layer where its text does not | **SUPPORTED (test), and it became the live path.** *The model's activations are closer to the leaked layer than its outputs are — its text is emblematic, its internals are dimensional.* This is the low-order/high-order ratio in [`THREE_LAYERS.md`](THREE_LAYERS.md) §6 | `FINDINGS.md` L1 |
| **PD-15** | Attention dwell past argumentative need is measurable | **OPEN.** Nothing built. Also the LUST signature in [`THREE_LAYERS.md`](THREE_LAYERS.md) §3 | — |
| **PD-16** | Cognitive-load signatures leak despite narrative management | **OPEN** — never tested here | — |

    Timeline on the leaked layer. Function words proposed as the cheap operationalisation; the first
    run was underpowered and VOID; the redo with purpose and topic fixed came back at 1.80x chance,
    p = 0.0047, MISSING a pre-registered 2.0x bar. Meanwhile the activation route -- the higher-ceiling
    option, needing machinery we did not have at the time -- was built and produced the project's only
    replicated effect, and attention moved there.

**⚠ PD-11 is owed a re-run and has not had one.** The standing policy from the curator, adopted after
this and applied everywhere since, is that **near-significance means raise the power, not report a
failure** — re-run held out, with every hyperparameter frozen. **That was done for the ladder and
never done here.** The project has since been describing this channel as a clean negative, which
overstates it in the direction that closes a line of work. **Forty generations is a small enough n
that this is cheap to settle.**

**The formal frame, named:** Bayesian Theory of Mind / inverse planning — build a generative model of
how mental states cause actions and invert it with Bayes. **There is a paper literally titled *Theory
of mind as inverse reinforcement learning*.** That is the essay's appreciation-as-IRL, already
formalised, already implemented for spatial agents. **This project's version is the same inversion
over artifacts instead of trajectories. Nothing needs inventing; it needs porting to a domain nobody
has ported it to.**

## §6. Counting decisions from the artifact directly — the programme that died

**Depth is decisions recoverable, so the obvious instrument counts them from the text. Ten measures
tried it. All ten died, and they died to the same three things: length, register, and vocabulary.**

**This section exists because it is the largest block of work this project has done and it had no
home in the theory folder.** Every row below is a real test with a verdict file.

| # | hypothesis | status | evidence |
|---|---|---|---|
| **PD-20** | Decision density can be counted from an artifact | **REJECTED (test).** It was word count (0.88); after correcting for that it was vocabulary diversity (−0.88). **Two confounds in sequence, and nothing left underneath** | `results/gate1`, `results/gate2` |
| **PD-21** | Published linguistic features track how much intent was specified, once machine-detectors are removed | **REJECTED (test).** 342 features → 89 → **81 replicated** → 20 that are not machine-detectors → 6 that do not echo → **3 that survive length** → **0 that survive the induction check** | `FINDINGS.md` L2, `results/feature_sweep` |
| **PD-22** | Causal connectives track depth | **REJECTED (test).** Ranked the ladder cleanly with no echo, then **inverted on humans** — machines use nearly twice as many. **It measures explicitness, not depth** | `results/` |
| **PD-23** | A larger feature bank beats a small curated set | **REJECTED (sim).** Ten hand-picked features reach near-perfect on the hardest cases; sixty more from a generic bank gain little on average and **lose more in the worst case** | sim T-8 |
| **PD-24** | Weak effects can be stacked into a usable detector | **OPEN, with a warning.** Stacking effects that share a confound produces a **strong confound**, and a stylometric stack already reaches F1 ≈ 0.99 on machine-text detection. **The ladder is the only thing that tells the difference, because a machine detector must see all five rungs as identical** | `FINDINGS.md` L4 |
| **PD-25** | No measure reads noise as maximum intent | **SUPPORTED (test).** Word-salad scored as a rung below the least-specified rung: **nothing places noise at or above the most-specified rung.** A failure mode we do not have | `results/rung_minus1` |

    Timeline on counting decisions. Counted directly and it was length; corrected for length and it
    was vocabulary; replaced with a 342-feature bank screened against the ladder, which produced 81
    replicated features of which **61 were machine-detectors**; the three that survived every other
    control then died to the induction check -- the test of whether a prompt CAUSES a feature without
    CONTAINING it. The funnel worked exactly as designed and the answer is no.

> **The one durable result is the funnel itself.** 61 of 81 replicated features were machine
> detectors, and without that filter we would have adopted the solved problem as our result.

**What this leaves.** The artifact-side route is closed for now: every measure that reads the *text*
has died. **The only signals that survived are read out of the reader** — which is
[`THREE_LAYERS.md`](THREE_LAYERS.md) §6, and it is why the project moved to activations.

## §7. Revision — the one controlled human comparison, and what it moved

**86 university students, one prompt, three drafts each. Maker, prompt, topic, register and genre all
fixed by construction, so whatever moves cannot be explained by any of them.** This is the first
controlled comparison on human text in the project's history.

| # | hypothesis | status | evidence |
|---|---|---|---|
| **PD-26** | Something measurable changes as one person redrafts | **SUPPORTED (test), and it is one coherent thing.** At matched length, revision raises **lexical sophistication** — words longer (+0.06 chars), more polysyllabic, rarer (frequency −0.04), stopwords down 5 per draft, reading difficulty up. Sign agreement 70–78% across 86 authors. **A single factor under six names** | `FINDINGS.md` L5 |
| **PD-27** | That effect is length | **REJECTED (test), and the trap fired as pre-registered.** Raw: 94 of 325 features survive, every one a *count*. Length-matched: **17 of 315**, and none of them counts | same |
| **PD-28** | The surviving effect is **polish**, not depth | **OPEN, and the corpus can settle it.** 5,834 revisions are hand-labelled Surface or Content at 0.71–0.92 agreement. **If the effect is carried by Surface-annotated revisions we have measured polish and confirmed it; if it survives among Content-only revisions, that is a depth signal on human text and the first one** | not run |

**PD-28 is the sharpest unrun test in this file**, and it is the reason that corpus is worth more than
its size.

---

## What this file says to do next

1. **PD-1 — depth-side and polish-side quantities measured separately across position.** The
   definitional test, and it has still never been run. Everything else in §2 and §3 is behind it.
2. **PD-3 — flat polish as the machine signature.** Sharper than any depth-based discriminator, and it
   requires no quality judgement.
3. **PD-15 — attention dwell.** It is the LUST signature and the second leakage channel at once, and
   nothing has been built for it.
4. **PD-7 needs a new instrument.** Singularity of terminal value is the successor design, and the
   measure it was going to use turned out to be a difficulty meter.
