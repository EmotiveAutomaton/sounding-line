# Human empathy heuristics — the tricks a person uses when the maker is absent

**A perfect solution exists in principle.** If you could model every neuron of a human brain, the
extraction has an answer — assuming no property of a brain adds randomness we are unaware of.

**In practice it is intractable**, and it converges only slowly: value data accumulated over time from
a variety of stimuli, approaching the answer the way a series approximation does. **So humans do not
solve the empathy triangle. They run heuristics at it.**

> While I don't expect we will have to rely on these heuristics when designing depth extraction, I
> expect AI will arrive at most, if not all of them, organically. Nevertheless it's worth keeping track
> of the ones we have run into that would be relevant as potential **feature-extracting amplifiers** in
> future, that other research teams may have missed.

**This file is that record.** Fifteen artifacts, two sessions, sixteen readings, one reader — and
**those readings have outperformed every measure we have built.** The curator is the only working
instrument this project has, so describing what he does is describing the thing we are trying to build.

---

## §1. The primary detector is the *variation* of the polish, not its level

> When I've been talking about the veneer in my head, I've been thinking about the imagery and
> iconography.

Not polish level — polish **change**. An opening reaching for professional register and then relaxing
out of it. **The performance is what costs something, so the performance is what slips, and the slip
is where the maker shows.**

**His own scope limit, attached when he stated it:** *useless on published books, because editing
sands the polish flat.*

### The timeline, because this is the claim with the most history and the least resolution

    1. Stated as his primary detector. Nothing in the project measured position within an artifact --
       every quantity was an artifact-level scalar, so nothing could have seen it.
    2. Simulation supported the mechanism: practised polish decays 6.5x faster than depth, and
       synthetic polish is flat. (sim S-6)
    3. Measured on MACHINE text as within-artifact variance of 342 features. Found 1 and 0 surviving
       features. UNINFORMATIVE -- a machine has no performance to slip, so a null there is the
       absence of the thing, not evidence against it.
    4. Measured on HUMAN text with maker, prompt, topic and register all fixed -- 86 students, three
       drafts each. 0 of 313 features survive correction, against 12 for the plain average.
    5. Found that the FIELD ALREADY DETECTS THIS, and detects it well.

**Step 5 is the one that changes the reading of step 4**, and this file previously got it wrong by
treating the null as damaging to the hypothesis.

| what the field does | what it is |
|---|---|
| **burstiness** — GPTZero's second headline metric | literally the standard deviation of per-sentence perplexity across one document. **Shipped commercially since 2023** |
| **unmasking** — Koppel & Schler, 2004 | chunk a document, separate the chunks, read the *shape of the degradation curve*. Canonical in authorship verification for 22 years |
| **intrinsic plagiarism detection** | find a passage anomalous relative to the rest of its own document, no reference corpus |
| **PAN Style Change Detection** | a shared task running continuously since 2018. **The topic-controlled bar is 0.830 macro-F1** |

> **The phenomenon is real and other people measure it successfully. We failed to measure it.**

**That is a different conclusion from "the hypothesis is wrong", and it points at our instrument.**
Either the operationalisation is wrong — variance of arbitrary surface *features* may simply not be
where the performance lives — or redrafting is the wrong axis, since a student redrafting an
assignment three times may not be varying the performance at all. **Both are fixable. Neither was
tested.**

**One further caution from the same audit:** a 2025 study of hidden states as author representations
found **document-level mean pooling best**, which is evidence against the variance idea at the
representation level too.

**What is not pre-empted:** within-artifact variance of **probe activations** rather than of
perplexity or surface style. Nobody found doing that.

### And his reading of what the field is measuring, which is a claim rather than a complaint

> It's not burstiness. It's not unmasking. **It is goal variation** — all of them varying in relative
> strength as you express yourself. People aren't seeing it for what it is.

**One distinction I collapsed and he separated:** intrinsic plagiarism detection finds *a different
author spliced in*. **That is not one author's goals shifting across their own piece**, and merging
them overstated how much of this is pre-empted.

| # | hypothesis | status | notables |
|---|---|---|---|
| **lit** | Within-artifact variation of polish carries the maker | **SUPPORTED (READ)** — seven years of shared-task baselines at **0.830** on topic-controlled data | **The phenomenon is real and other people measure it well.** That changes what our null means |
| **L7** | Variance of arbitrary surface features is the right operationalisation | **REJECTED (test).** 0 of 313 features survive on human text with maker, prompt, topic and register fixed | **This is what actually died** — and the plain average found 12 on the same data, so windowing itself was not the problem |
| **HH-3** | Within-artifact variance of **probe activations** carries what surface-feature variance does not | **OPEN, and not pre-empted by anyone** | Burstiness does it with perplexity, PAN with surface style. **Nobody found doing it with probe outputs** |
| **HH-4** | Redrafting is the wrong axis; the claim needs artifacts of **different kinds** by one maker | **OPEN** | A student redrafting an assignment three times **may not vary the performance at all**, which would make L7 uninformative rather than negative |
| **L11** | Our measure beats 0.830 on the topic-controlled split | **RUNNING** — 342 features on PAN hard | **If we land far below, §1 is about our instrument and not about the phenomenon**, and that is worth knowing plainly |

**What these add up to.** The claim and our measure of it came apart. **A mature field detects
within-document variation successfully at 0.830 on topic-controlled data, and we found nothing** —
which points at the instrument rather than the hypothesis, and this file previously got that backwards.
**Two candidate faults, both fixable, neither tested:** the operationalisation may be wrong (variance
of arbitrary surface features is not obviously where a performance lives) or the axis may be wrong
(redrafting may not vary the performance at all). **HH-3 is the version nobody has pre-empted** —
variance of *probe activations* rather than of perplexity or surface style — and it is the only route
here that is both untried by the field and untried by us.

### What this retires

**The revision-wobble test was a false start, and he did not propose it.**

> The problem is that revisions from a human author are always going to carry **the same level of
> intent density across the board.**

**So the null stands but its target was mis-specified.** It tested whether human redrafting varies the
performance; on his account human redrafting should not vary it at all, **which makes the null
unsurprising rather than informative.**

**What would have been interesting instead, in his words:** *AI* revision — the moment the model's
attentional mapping shifts away from your goal and you reach out to correct it. *"Allow me to pick you
up with the largest pole of the tent in my distorted policy space."* He predicts a vague unifying
effect and declines to claim even that.

## §2. Reading enters at an anomaly, never at the artifact

> The thing that most jumps out at me isn't mistakes but **unusual constructions, or odd decisions
> that I can't find an explanation for.**

Then it runs purpose→method **and** method→purpose, with the entry point set by wherever he has
partial expertise — which is [`THE_EMPATHY_TRIANGLE.md`](THE_EMPATHY_TRIANGLE.md) §2's enter-at-any-sub-level claim
described from the inside.

**His own discomfort, recorded because he raised it:** *"I hate that a lot of this is me picking out
mistakes and typos, which is also a trick for AI and it's not okay. But it is a way of extracting
decisions."*

**And the mechanism that connects this to mistakes:** a **mistake** is an anomaly with a *known
cause*, so the maker's response to it is a decision with its alternatives visible. *"The importance of
the mistake — the mistake, and the way the author can be presumed to have responded to it, is one of
the more useful pieces of information once you have observed it."*

| # | hypothesis | status | notables |
|---|---|---|---|
| **HH-6** | Entering at the anomaly beats entering at the whole artifact | **OPEN** | **The machinery exists and has never been the live path** — `bounded_v6`'s stage zero runs the anomaly pass first and feeds stage A. A flag flip and a comparison, not a build |
| **HH-7** | Local decision density around a mistake exceeds baseline | **OPEN** | Needs mistakes *located* first, and nothing does that. **A mistake is an anomaly with a known cause**, which is what makes it more tractable than an anomaly |
| **S-4/S-5** | Stage ordering changes the answer | **REJECTED (sim)** — by exactly zero; anomaly-first settles ~5% sooner | **This weakens HH-6's expected size before it is run.** Honest prediction: a cost saving, not a finding |

**What these add up to.** The entry-point claim is cheap to test and **the simulation has already
lowered what we should expect from it** — reordering the probe's stages changed the answer by exactly
zero, and only the cost moved. **So HH-6 is worth running to close the question rather than to open
one.** The more interesting row is HH-7, because a mistake is an anomaly whose *cause is known*, which
means the maker's response to it is a decision with its alternatives visible — **the only place in
this file where we could see a decision and its counterfactual at the same time.**

## §3. Confidence in a maker moves while reading

> It starts questionable... 8 or 9 by the end.

**The trajectory carries what the endpoint does not.** Every reading this project records is a final
number.

**Related to §1 by more than coincidence** — both say the within-artifact *series* is where the
information is, and we have only ever kept means. **The same 2025 result that found document-level
mean pooling best is evidence against both.**

| # | hypothesis | status | notables |
|---|---|---|---|
| **HH-9** | The confidence trajectory across a reading carries more than its endpoint | **OPEN.** Score windows sequentially and keep the series | **Every reading this project records is a final number**, so the series has never existed to be checked |

**What this adds up to.** One row, never run, and it shares a fate with §1: **both say the
within-artifact *series* is where the information is, and we have only ever kept means.** The one
piece of external evidence bears against both — a 2025 study of hidden states as author
representations found document-level mean pooling best. **That is not decisive, because it was
optimising for author identity rather than for maker state**, but it is the reason neither row should
be run expecting a large effect.

## §4. Depth is a property of the writer **with respect to the domain**

> It does not vary within an artifact unless the domain does.

**This is the sharpest definition in the project**, because it makes depth a **relation** rather than
an attribute — and it arrived with its own falsifier attached: *depth moves where domain moves.*

**Why it matters more than it looks.** The binding constraint on this project has been the absence of
a controlled human corpus. **This says why that is fatal rather than inconvenient: a relation cannot
be measured by varying one side.** Every measure that has died, died reading artifacts alone.

| # | hypothesis | status | notables |
|---|---|---|---|
| **HH-10** | Depth measured on one maker moves when the domain moves and not otherwise | **OPEN, blocked on a corpus we do not have** | **Previously written up as "directly runnable". That was wrong** — it is directly *specifiable*, and nothing we hold supplies it |

**What this adds up to, and it is the most consequential row in the file.** Making depth a *relation*
rather than an attribute explains why the corpus problem is fatal rather than inconvenient: **a
relation cannot be measured by varying one side, and every measure that died, died reading artifacts
alone.** The falsifier came attached to the claim — *depth moves where domain moves* — which is rare
and makes this cheap to settle the moment the corpus exists. **It is the same corpus HH-4 needs, and
the same one three sections of the empathy triangle need.**

## §5. Process is hierarchical, and you can enter the decode at any level

> Walking up to an unknown oil painting, you can engage with it on the level of **metaphor** — why did
> the author craft what they did. On the level of **technique**, like perspective. On the level of
> **mechanics** — how did they move their hand as they painted.
>
> **You can use any piece of knowledge about any of those three channels to begin the decoding.**

**Vocabulary decision: mechanics / technique / metaphor stands.** Panofsky was the wrong citation and
he rejected it correctly — those levels are about *what an image depicts*, not *how a thing was made*,
and perspective, oil paint and meaning genuinely do not sort into that scheme.

**Dennett's three stances is the right citation and not the terminology:**

| his label | Dennett | what it reads |
|---|---|---|
| **mechanics** | physical stance | how the hand moved; the material act |
| **technique** | design stance | how it is built to work; perspective, structure |
| **metaphor** | intentional stance | what the maker meant by it |

**And it is not one person's scheme** — Marr's computational / algorithmic / implementational, and
Newell's and Pylyshyn's independent versions, all land on three levels with the same structure. **Four
thinkers converging is a result about the shape of the problem, not a coincidence of naming.**

One caveat worth holding: **"metaphor" is narrower than the top layer needs** — the intentional stance
covers *purpose*, not only *meaning*, and this project's top layer has to carry goal.

**Still open, and he flagged it:** whether the layers are really three or arbitrarily subdividable.
Nobody in that convergence argues three is forced; they argue three is *useful*.

### This is where we collide with the literature, and the collision is the contribution

| # | hypothesis | status | notables |
|---|---|---|---|
| **lit** | Entry is possible at any of the three levels and ratchets to the others | **CONTESTED (READ)** | **Bullot & Reber assert a strict ordering** — the design stance is *"requisite for"* artistic understanding — and the open peer commentary attacked precisely the relations among their modes. **This contradiction is our contribution surface** |
| **lit** | Bullot & Reber's framework is well supported | **REJECTED (READ-FULL)** | Chmiel & Schubert, 34 experiments across 23 publications: **26% support, 18% inconclusive, 56% no support.** An occupied lot with a shaky building on it |
| **G56** | Supplying **mechanics-level** information unlocks goal recovery | **OPEN, and it is the missing direction in the whole edge programme** | **Every edge tested so far supplies a goal or a process. None has ever supplied a mechanic.** Same row as the empathy triangle's G56 |

**What these add up to.** We disagree with the only framework that occupies this ground, **and that
framework is weakly supported by its own field's replication record** — so the collision is worth
taking rather than conceding. **The disagreement is specific and testable**: they say the design
stance is a prerequisite, we say entry is possible anywhere and ratchets. **G56 is the experiment,
and it has never been run in either direction by anyone.** The formal home for our side is one we have
never read — **Rasmussen's abstraction hierarchy**, five levels with explicit means-ends links, built
for diagnosis *from any level*, forty years of use.

**The formal match we have never looked at is Rasmussen's abstraction hierarchy** — five levels with
explicit means-ends links, built for diagnosis **from any level**, forty years of use. **That is a
better formal home for the ratcheting claim than anything we have cited, and nobody here has read it.**

## §6. Interest is unexplained decisions — which makes the reader an instrument

> Interest comes from finding decisions that you can't attribute meaning to, which implies there's
> more meaning you don't fully understand — either a **process** you aren't aware of, or an **extra
> motivation** you aren't aware of.
>
> **Artfulness is making a lot of unexplained decisions. Aesthetics is the appearance of having made
> unexplained decisions but for a reason, in an ordered sense.**

**This connects §2's anomaly-entry to a mechanism**, and it makes *interest* a proxy for **unrecovered
decisions** — which is the quantity this whole project is trying to measure.

> **If interest is what a reader feels when decisions are present but unattributed, then
> reader-reported interest is an instrument — and it is one we can ask a human for directly.**

**And it answers his own open question about performative polish.** He asked whether art theory
separates aesthetics that *indicate* deeper understanding from aesthetics that merely perform it.
**Under §6, performative polish is ordered without being unexplained** — which is a measurable
distinction rather than a vibe.

**A correction that matters, because it was mine and it was load-bearing.** I offered **Berlyne's
collative variables** — novelty, complexity, uncertainty, conflict — as live support. Reading the
source rather than the search snippet: *"Berlyne's arousal theory of aesthetic appreciation has been
mostly abandoned"* on mixed empirical results. **The vocabulary survives; the mechanism does not, and
this claim must not lean on it.** The live descendants are **processing-fluency** accounts, which sit
at the *opposite* pole — pleasure from ease. **That tension is the field's live debate and his claim
sits on one side of it.**

**His "ordered but unexplained" is close to effective complexity** — structure that is neither random
nor trivially regular. **That is a real, formalisable quantity and it is the better formal target.**

| # | hypothesis | status | notables |
|---|---|---|---|
| **HH-14** | Reader-reported interest correlates with unrecovered decisions | **OPEN, blocked on him.** Interest ratings on his fifteen read artifacts | **An hour of his time, and it turns the one channel that has beaten every measure we own into data** |
| **lit** | Berlyne's collative variables support the interest claim | **REJECTED (READ)** | *"Berlyne's arousal theory of aesthetic appreciation has been mostly abandoned."* **One fetch found this after fifteen searches had not** — the vocabulary survives, the mechanism does not |
| **HH-16** | "Ordered but unexplained" is effective complexity rather than entropy | **OPEN** | Effective complexity is a real formalisable quantity — **neither random nor trivially regular** — and it is a better target than the vocabulary we borrowed |

**What these add up to.** The idea is intact and the support I first gave it was wrong. **Interest as
a proxy for *unrecovered decisions* is the only claim in this project that turns the reader into an
instrument**, and it costs an hour rather than a corpus. Its formal home is effective complexity, not
Berlyne — **and the live debate in the field runs the opposite way**, with processing-fluency accounts
locating pleasure in *ease* rather than in unresolved structure. **That tension is not a problem for
the claim; it is the thing HH-14 would adjudicate**, because the two accounts predict opposite
correlations between interest and recoverability.

## §7. Aesthetics was the cheat, and AI broke it

> Aesthetics is one of the **easiest goals to judge**, because it is literally surface polish — you
> can explicitly judge whether the maker succeeded at it, and implicitly the value of what you are
> seeing by **how much you want to look at it. It is a self-referring goal and you can cheat it pretty
> easily.**
>
> **It's also the piece that's misfiring on AI specifically. Previously it correlated with effort very
> highly. Now it does not. That's what's breaking.**

**The sharpest available account of why generated text unsettles readers.**

**And it reframes the effort heuristic rather than accepting it.** People rate identical artifacts
higher when told more effort went in, more so when quality is ambiguous. The literature audit offered
that as an adversarial reading of depth — a bias in the reader. **On his account it is not a bias. It
is a normally-valid inference that a new kind of artifact has broken.**

| # | hypothesis | status | notables |
|---|---|---|---|
| **HH-17** | The polish–effort correlation is strong in human corpora and near zero in generated ones | **OPEN, and the corpora are already held** | **Needs an effort proxy, which is the unspecified part** — and effort is exactly the quantity automaticity makes unobservable |
| **HH-18** | The effort heuristic is a valid inference broken by a new artifact class, not a reader bias | **OPEN**, and it follows from HH-17 | **The reframe is the contribution.** The literature calls it a bias in the reader; this calls it a normally-valid inference that something new has broken |

**What these add up to.** Both rows rest on being able to measure **effort**, and nothing in this
project can. That is not an oversight — **automaticity makes effort unobservable by construction**,
which is the same fact that makes the polish/depth asymmetry work and the same fact that puts values
in the residue rather than the signal. **So the sharpest testable claim in this file is blocked on the
quantity the rest of the theory says is hidden**, and any proxy we adopt will need its own defence
before HH-17 means anything.

