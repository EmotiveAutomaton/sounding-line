# The triangle — empathy as a triple extraction

**The core claim of the project.** Dictated 2026-08-04, extended repeatedly since, and merged
2026-08-07 with what used to be `VALUES.md` and the value-recovery half of `AGAINST_IMPOSSIBILITY.md`
— because those were the same argument split across three files. Pre-merge originals are in
`../archive/`.

---

## §1. The claim

> I think empathy is effectively a variational inference problem — **three separate variational
> inference problems being solved in parallel, and each one bootstraps the others.** The more
> information you have in one, the easier it is to solve the others. They have relative strengths,
> relative difficulties, but they all help the other.
>
> 1. the extraction of the **proximal goal**
> 2. the extraction of the **process**
> 3. the extraction of the **values / drives**

> This is why an expert can instantly understand what a novice was thinking as they were making
> something, in a way that another person cannot. This is why being close friends with someone, you
> can read their book and get more of a sense of why they made certain choices. **This is why
> information is passed more easily between people who are close.**

**It is still a triple extraction of goal, process and drives.** What is contested is the *shape* of
the relationships between them, not that there are three — §3.

**Why this was a correction and not a restatement.** The project had been treating one edge —
goal → process within a single encounter — as the whole thing, and Gate 3's entire primary was built
on it. **That is one of six directed edges.** The claim is that whichever vertex you can reach first
is the one you should enter by, which is what he described doing when reading aloud, before he had
the formalisation:

> I'm trying to find some layer within which I can use my expertise, then use that expertise to solve
> the easy part, and then I use that to get the motivation, and then that I can use to
> reverse-engineer the rest of it that I don't understand. **Is it a three goddamn part process?**

## §2. The vertices subdivide — three is a partition, not a count

> Not only would it be fractal, but there'd be **dozens of each layer**. There are various techniques
> layered on top of each other and various mechanics layered on top of each other. **Those are
> categories, not lines.**

> Your expertise can be applied at multiple layers of the problem. **You kind of find the piece that
> you already understand and you work your way out from there.**

So the three vertices are a coarse partition, and entry is not *at a vertex* but at whichever
sub-level of a vertex you happen to have purchase on. **Nobody in the mechanics/technique/metaphor
convergence argues three is forced — only that three is useful.**

**And goal is not confined to one place.** *"I agree that the top layer carries goal, but let's not
assume it's the only layer that does so."* **Goals propagate throughout the three layers.** An
instrument that assumes exactly three levels, or that goal lives only at the top, **assumes more than
the theory supports.**

| # | hypothesis | status | evidence |
|---|---|---|---|
| **TR-1** | Prior information at *any* vertex improves recovery at the others | **OPEN** — one of six edges has ever been tested | goal→process only, Gate 3 primary |
| **TR-2** | Entry is possible at any sub-level, and expertise sets which one | **OPEN** | never run |
| **TR-3** | Reordering the probe's stages changes its answer | **REJECTED (sim)** — by exactly zero. Reverse and anomaly-first settle ~5% sooner. A cost saving, nothing more | sim S-4/S-5 |
| **TR-4** | Closeness to the maker is a measurable prior — two readers, one who knows them | **OPEN** | a human study, and the cleanest form of the claim |

**And closeness runs the other way too, which is the part with no instrument.**

> Showing someone your writing is a kind of **intimacy**. If you know the person better, you can
> extract their proximal goal and their process more easily.

**This is the values vertex acting as a prior held *before* the artifact is seen**, rather than as
something recovered from it — which is a different quantity from anything measured here, and the only
place in the theory where the reader's prior relationship is doing the work rather than the text.

## §3. The shape of the triangle — contested, and all of it in one place

**This section exists because the shape is where the results land**, and they had been scattered
across three files and a findings entry.

**Superseded — "the values vertex does not exist."** Simulation T-6 returned H(values | goal) = 0, a
deterministic coarsening adding exactly zero information, and this project recorded that as the values
vertex not existing and then reasoned from it for two days. **That was a property of the simulation's
construction, not a finding about values**, and propagating it as fact was an error. §4 explains why
zero is what it had to return: a single-artifact model cannot represent a quantity that is only
defined across artifacts.

| # | hypothesis | status | evidence |
|---|---|---|---|
| **TR-5** | The three problems bootstrap each other superadditively | **REJECTED (sim)** as stated. Three of six edges are exactly zero; the edges are **additive, not superadditive** | sim T-1 |
| **TR-6** | Goal is the easiest vertex to recover | **SUPPORTED (sim)** — goal is a *sink*, already at ceiling (1.000). **Predicted before the run** | sim T-1 |
| **TR-7** | Process is the most useful vertex when supplied | **SUPPORTED (sim)** — process is the *source*, +0.840 to depth. **Predicted before the run** | sim T-1 |
| **TR-8** | The values vertex carries no information | **VOID** — the model could not represent it | sim T-6, retracted 2026-08-07 |

    Timeline on the shape. Stated as a symmetric triangle; the simulation found it directed and
    additive rather than mutual; the same run reported values as empty, which was recorded as a
    finding and has now been withdrawn as an artifact of the construction. What survives: three
    vertices, unequal, with process upstream and goal cheap.

**What the shape looks like on the evidence:** not symmetric. **Process is upstream, goal is
downstream and cheap, and drives are the vertex our instruments have never been able to hold.** That
is consistent with the three helping each other and inconsistent with them helping each other
*equally*.

## §4. Values are a weighting over trajectories; a goal is one component temporarily amplified

> Take value space and treat it as a **weighting on trajectories**. A goal would be a weighting of a
> specific policy plan — raising one action within that plan above the rest **temporarily, due to
> attention**.

**This closes the project's founding loop.** The original claim was that appreciation is *inverse
reinforcement learning* — the reader inverts the artifact to recover the maker's reward function.
This says the reward function **is** the value set, and a goal is a temporary re-weighting of it.
Values are not a third thing recovered alongside goal and process; they are **the standing
distribution that goals are drawn from.**

> You need all of the actions of the person to extract their value map. We need as much information as
> possible to get as close to an accurate value mapping as we can.

**Terminology, and it was a deliberate concession:** he accepted *"weighting over trajectories"* over
*"weighting over policies"* **when given the reason.**

| # | hypothesis | status | evidence |
|---|---|---|---|
| **TR-9** | Values need many artifacts by one maker; a goal needs only one | **SUPPORTED (test)**, indirectly but consistently. Every single-artifact values attempt failed; every within-maker multi-work design produced a positive — author identification **7.6× chance**, within-author work separation **2.05×**, the only within-human positive we have | `FINDINGS.md` tier 2 |
| **TR-10** | A maker's weighting is more stable within maker than between makers | **OPEN** — the 34-book corpus already supports the design. **The first values test this project has been able to specify at all** | not run |

## §5. The policy-mapping mess — the sharpest open question in the theory

> Attention directs toward **policy space**. You use the **trajectory mapping — which is our
> expertise** — layered over a **weighted policy map, which is our outcomes**. From that we get our
> actions.

    expertise (trajectories)  ×  weighted policy map (values)  →  actions
    a goal = attention amplifying part of the policy map

**A correction I had materially wrong.** I wrote this as how a person generates their own actions. It
is not:

> This is specifically about doing it **to other people**. I'm referring to **the creator**. This is
> maths you're doing **in your head, through embodied simulation, with the creator.**

The stack is **the model the reader builds and runs of the maker**, using their own machinery as the
substrate. **You simulate the maker with your own equipment, and the parts you lack are the parts you
cannot recover.**

### What comes out is distorted, and the distortion is the open question

> If there's a policy space, then there's some kind of weighted mapping on top of that that is
> transformed through **attentional mapping**. This weighted mapping is based on attention and it's
> transformed through your **trajectory mapping**. And that creates **proximal goals**.
>
> The problem is those **drives then are not values.** They are... perhaps they are the **values times
> the process mapping.**

**So the third vertex is not clean.** What an artifact exposes is not the value set but the value set
already pushed through the maker's expertise and their attention — which is why *are drives values?*
has stayed open since it was first asked.

**And his warning about his own mechanism, which is the honest part:**

> Attention mucks things up. I have said that it distorts it, and it seems like it should, but
> **attention is kind of often a god-of-the-gaps thing. You just sprinkle it in where you think
> consciousness should be.**

| # | hypothesis | status | evidence |
|---|---|---|---|
| **TR-11** | What an artifact exposes is values composed with the process mapping, not values | **OPEN** — predicts recovery improves when process is supplied, which is TR-7's direction | never isolated |
| **TR-12** | Attention is doing real work here rather than papering a gap | **OPEN, flagged as suspect by its own author.** Any design leaning on it must state what would show attention is *not* needed | — |
| **TR-13** | Values are the constraint that **every** drive is partially satisfied at once, rather than a separate factor | **OPEN.** *"Everything else before this felt like dithering to me, but this one feels like it might be a real thing."* Would explain why modelling values as a separate factor always collapsed | a build; scoped in `../sim/` batch four |

## §6. Value blindness — a hard constraint on method

The obvious experiment is to have someone write down a value set and generate artifacts from it.
**He says he cannot, and the reason is not modesty:**

> You always have an imperfect view of anyone else's value set, and **you are blind to your own.**
> It's why artists will make art and look at it — in part to get a sense of their own values. They
> learn about themselves through that expression.
>
> Anything I say, anything I make will be over-indexed and automatically full of error, because it
> will be **my view of my own value set.**

**A methodological constraint, not a personal limit.** If values were introspectively available, art
would not be one of the ways people discover them. The self-report route is closed for the same reason
a questionnaire cannot reach the leaked affect layer — **the instrument does not reach the thing.**

**This kills a class of designs**, including one this project had queued: *author a value set,
generate against it.* It cannot be done by the person whose values they are, and a third party
describing someone else's is a second-order guess.

## §7. Where ground truth on values could come from

The requirement: **a corpus where multiple makers were deliberately aligned to one declared value
set, with the value set recorded independently of the artifacts.** Values are normally latent; this
is the rare case where they are **declared**.

> Religion is probably the strongest force for value alignment I can think of in the world. It does
> curiously suggest you'd be able to **extract someone's religion from their words.** [...] That's
> such a messy test. It's also straight trash as academic work.

**The generalisation is the useful form and it is not about religion:** religious traditions, political
manifestos, professional codes, open-source governance, movement writing, corporate value statements.

**The confound that sinks the naive version, and the fix.** Religious writing mentions God; political
writing mentions policy. That is lexical and trivially detectable — the trap that turned 61 of 81
ladder survivors into machine detectors. **Hold topic constant by construction:** the *same practical
question* — money, work, family, obligation, death — answered from within different declared traditions.

### His refinement, and it is the design rather than a detail

> The key part has **little to do with the work itself**, and more to do with **deep followers** of
> that work. And then aligning that with the specific values that have **spread out from** that work.
> We'll have to analyse the work **and** the followers — we can use that to find how much they agreed
> with the values implied.

A founding text is one artifact by one maker under a value set it is itself defining — circular. **A
follower is a different maker writing under a value set that already exists independently of them**,
and it arrives graded rather than labelled:

    the declared value set     from the founding work, recoverable independently
    the follower's artifacts   many makers, many works each
    degree of alignment        HOW MUCH each follower took on -- and it varies

**That last row is the prize.** Every other value corpus gives a binary label. This gives a **gradient
of adherence — a ladder made of humans rather than of prompts.** It also inverts the confound:
founding texts are lexically distinctive, followers writing about ordinary life are not, so **the topic
trap is weakest exactly where the signal is.**

**The honest objections, kept:** canon formation is a selection effect, translation is a confound, era
is a confound, and **declared values are not held values.** That last is less damaging than it looks —
the project does not need to know what a maker truly valued, only a ground-truth label for the value
set an artifact was made *under*.

| # | hypothesis | status | evidence |
|---|---|---|---|
| **TR-14** | Value recovery improves sharply with more works per maker, while goal recovery does not | **OPEN** — the two-level design tests this and TR-9 at once | corpus not sourced |
| **TR-15** | Degree of adherence to a declared value set is recoverable as a graded quantity | **OPEN** | corpus not sourced |

## §8. The impossibility proofs assume unconstrained inference, and humans are not unconstrained

**This is where the project disagrees with the literature, and it is not to be narrowed.**

> Saying something isn't possible just means you haven't found the way to do it yet — **especially if
> the world is doing it.**

**His correction against my own first write-up.** I wrote *"humans do this, therefore it can be done,"*
which claims too much:

> I'm not saying humans arrive at a conclusion of value. I'm saying they use **a bunch of tricks to
> actively try to get closer** to it.
>
> **It's a limit situation.** You get closer and closer over time. There *is* a solution — a perfect
> mapping of the person's brain — but we approach it **through inference with error**, and we are
> never sure we have the answer.

**That is stronger than the claim I wrote**, because it does not need the theorem to be false. The
theorem says a unique decomposition is not identifiable; **this is a claim about a convergence rate.**
Both can be true.

> **"Irrational agents" is incorrect about humans.** In a lot of ways we are *boundedly
> hyper-rational.* **It looks like irrationality to have fractal motivations.**

> The problem they are running into is an **inability to disassemble expertise from exploratory
> behaviour.**

### The decisive move: his three assumptions are exactly the three the proofs require

| what the proof needs | what he already assumes | his name for it |
|---|---|---|
| a bounded hypothesis space | human-shaped goals | **convergent midbrains** |
| a known transition model | expertise | *"the transition model is just expertise"* |
| a rationality / optimality principle | near-optimality | *"that's just MaxEnt"* |

> *"Oh my god, it's my three assumptions."*

**And the second identification is the one to build on:** *"the maker's competence is their
expertise."* **The two unknowns Armstrong & Mindermann prove are fatal are the same quantity in this
framework — and it is a quantity we already claim is recoverable.**

| # | hypothesis | status | evidence |
|---|---|---|---|
| **TR-16** | A reward function is not identifiable from one episode | **SUPPORTED (lit, READ)** — Amin, Jiang & Singh, NeurIPS 2017, state our decomposition and our consequence verbatim, nine years early | `../method/LITERATURE_AUDIT.md` |
| **TR-17** | Recovery stays impossible even with unlimited episodes | **CONTESTED (lit, READ).** Armstrong & Mindermann (2018), Skalse et al. (2023), Cao et al. (2021): partial identifiability persists in the infinite-data limit. **We do not dispute the proofs. We dispute that their conditions describe a human reading a human artifact** | — |
| **TR-18** | Recovery error shrinks with more artifacts by one maker, toward a small residual | **OPEN.** TR-17 made empirical — the disagreement stated as something measurable rather than argued | scoped in `../sim/` batch four |
| **TR-19** | Supplying an explicit competence estimate improves goal recovery | **OPEN** — if it does, the "fatal unknown" is an input we can provide | never run |
| **TR-20** | Re-reading one artifact recovers the tail, so depth of reading substitutes partially for breadth of corpus | **OPEN** | never run |

**Everything is an artifact, including biography.**

> **Everything's an artifact. Even information about their life.** Any action they took that affected
> the world counts. [...] You will use **epistemic foraging** to find more things out about the artist
> if you want to.

**This dissolves the artifact/context distinction** — learning about the artist is not context, it is
**more trajectories from the same maker**, which is exactly what TR-18's diversity-of-conditions
requirement asks for. **The two claims meet here and neither was made with the other in mind.** It
also disposes of the "the person is not there" objection: *"you're responding to their sound waves and
it's the same maths."*

**Re-reading recovers the tail.** Against the finding that prompt information survives in a model's
distribution *tails* rather than in sampled text:

> A human could study a single bit of text and extract **more and more goals from it over time**, in a
> layer of **decreasing confidence with increasing information**. That is what we do — literature
> studies exist for this. People reread the same book over and over for this purpose.

**Identification is the limit of prediction, not a different act.** Against Dennett's intentional
stance licensing prediction but not identification: *"It's a question of limit. We're doing a Taylor
series approximation — increasing precision based on Bayesian updating. Eventually, hypothetically,
the only way to do it fully would be to hold someone else entirely in your mind."* **That is a statable
position in the intentionalism debate and it answers Wimsatt & Beardsley rather than conceding to
them** — and it has never been written up as such.

## §9. Legibility is not the only governor

Four modules in the third simulation batch converged on this, and it was reported as that batch's most
useful product.

**Superseded as stated —** *how recoverable the goal is governs how readable everything else is.*
Seams between decisions are findable when purpose is legible and nearly invisible when it is not, a
threefold to tenfold difference. The instruction drawn from it was that a process-side reading quoted
without a legibility figure is not interpretable.

**His objection, and it is §1 turned back on the simulation:**

> The goal is not the only governance for how readable everything else is. **You could also show up
> with a ton of expertise and a very accurate set of trajectories, which make everything else much
> more readable — almost instantly.**

**If entry is possible at any vertex, arriving with a good transition model should unlock the rest
just as arriving with a legible goal does. The simulation only ever varied one of the two.** And it
concedes the ground itself: it names its own limit as the fact that its legibility knob attenuates in
one particular way, and whether real illegibility has that shape is what a simulation cannot say.

| # | hypothesis | status | evidence |
|---|---|---|---|
| **TR-21** | Goal legibility governs process-side readability | **SUPPORTED (sim), CONTESTED in scope** — real, but shown for one knob only | sim batch 3 |
| **TR-22** | Supplied expertise unlocks the rest as effectively as supplied legibility | **OPEN, and it is the missing arm.** Every edge tested so far supplies a goal or a process; **none has ever supplied a mechanic** | never run |

## §10. Soul is a variety of motivations, and expertise moves decisions into drives

> When we talk about something having **soul**, what that means is **a variety of motivations**. And
> it tends to travel with expertise — because as processes are baked in with automaticity, you lose
> conscious access to them and they start to be tied more to your **drives**.

**The chain:** practice → automaticity → the decision leaves deliberate control → it is now made by
whatever is underneath → that is drives → an expert's artifact carries more drive-derived variety than
a novice's, without the expert choosing it.

**This is a mechanism for why expertise produces soul, and the project did not have one.** It explains
why an expert cannot say *why* they did something and why their artifact shows more of what they are,
at the same time and for the same reason.

**Contested, and he raised it against himself:** *"the idea that automaticity is driven by drives
rather than emotions — I'm betting that there's evidence against that."* **Not yet searched, and
flagged because it is the load-bearing link in the chain above. The variety-of-motivations claim he
holds regardless of the mechanism.**

| # | hypothesis | status | evidence |
|---|---|---|---|
| **TR-23** | Motivational variety is measurable as breadth of recovered purpose | **INSTRUMENT DEAD (sim, twice).** `purpose_breadth` tracks **how hard the goal is to recover**, not variety; at matched difficulty the excess from diversity is −0.013 to −0.025 | sim T-2, T-9 |
| **TR-24** | Diversity rises with expertise while agreement about purpose stays flat | **OPEN** — a two-measure prediction using quantities that already exist | never run |
| **TR-25** | Automaticity routes decisions to drives specifically, rather than to emotion or habit | **OPEN, and he expects it to be contested** | not searched |

**Any second instrument for TR-23 must survive a difficulty control. Neither of the two tried so far
would have.** The simulation stated explicitly that it **cannot** test whether practice *causes*
drive-multiplicity.

---

## Why these arrived together

They are one idea seen from three sides. **The triangle says goal, process and values are mutually
recoverable. Goal diversity says expertise moves decisions from process into drives**, which is a
claim about traffic between two of the vertices. **And the depth architecture says a reader
instantiates the vertices at different depths** — low for drives, high for constructed goals, which is
[`THREE_LAYERS.md`](THREE_LAYERS.md).

**Same structure: three levels, coupled, with practice moving mass downward and reading moving it back
up.** Every part of this project that has survived contact with evidence sits somewhere on it; every
part that died was measuring one vertex with an instrument that could not see the edges.

## What to do next

**Cheap, never run:**

1. **TR-22 — supply a mechanic instead of a goal.** The missing arm of the entire edge programme.
2. **TR-24 — diversity against expertise at flat purpose-agreement**, with measures we already own.

**Expensive, matters more:**

3. **TR-13 — values as the constraint that every drive is partially satisfied at once.** A build, in
   the parent simulation, and the first well-posed version of the values question we have had.
4. **TR-15 — the follower corpus.** A gradient of adherence to a declared value set, which is a ladder
   made of humans.
