# The triple inference — a model of human empathy

*(formerly "the empathy triangle" — renamed 2026-08-08 at the curator's instruction)*

> Empathy is effectively a variational inference problem — **three separate variational inference
> problems being solved in parallel**, each bootstrapping the others: the extraction of the **proximal
> goal**, the extraction of the **process**, and the extraction of the **values and drives**.

> I'm **specifically modelling it after human empathy** — what seems to be the process that I believe
> human empathy is.

**The name changed; the target did not.** *Empathy* carries 43 catalogued definitions and invites an
affective reading of an inferential claim, so the mechanism is now named for what it does — a **triple
inference**. **The phenomenon being modelled remains human empathy**, and every claim in this file is
a claim about how that process works.

**The core claim of the project.** Everything else in this folder is downstream of it. What is
contested is the *shape* of the relationships between the three, not that there are three.

**A naming note, unresolved.** The measured structure is directed and additive rather than mutual, so
"triangle" may be wrong. **But additive implies something is being added**, and that is not a line
either. The name stays until the shape is settled — see §2.

---

## §1. The claim

**2026-08-04.**

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

**Why this was a correction and not a restatement.** The project had been treating one edge —
goal → process within a single encounter — as the whole thing, and Gate 3's entire primary was built
on it. **That is one of six directed edges.** The claim is that whichever vertex you can reach first
is the one you should enter by, which is what he described doing when reading aloud, before he had
the formalisation:

> I'm trying to find some layer within which I can use my expertise, then use that expertise to solve
> the easy part, and then I use that to get the motivation, and then that I can use to
> reverse-engineer the rest of it that I don't understand. **Is it a three goddamn part process?**

## §2. The shape — directed, additive, and not a line

**2026-08-04 through 2026-08-07.** This is where the results land, and they had been scattered across
three files.

**What the simulation measured.** Three of six edges are exactly zero. **Goal is a sink** already at
ceiling (1.000). **Process is the source**, contributing +0.840 to depth. And the edges are
**additive, not superadditive** — so "each one bootstraps the others" is not what was measured.

**His extension, 2026-08-07, and it completes the ordering:**

> **I would assume that drives are upstream of even process.** And again, it would require several
> samples both within and across a given individual. And that would create this kind of Lagrangian
> Taylor-series-looking thing where you're moving towards a limit.

**So the chain runs drives → process → goal**, with recoverability running the other way — goal is
cheapest and drives are the vertex our instruments have never been able to hold. **The two orderings
are the same fact seen from both ends: what generates last is what recovers first.**

**And the additivity is a clue rather than a disappointment:**

> If empathy is not a triangle but **a river, what are its tributaries?** If it's additive, that
> implies there's something else being added to it. And there's only so many things it could be.
> **Certainly expertise is part of it. Is it goals minus expertise equals drives?**

**That last equation is dimensionally odd** — goals are a weighting and expertise is a transition
model, so they do not subtract. **But the intuition survives the objection and §4 is what it becomes:
drives are what is left when you subtract the part of expertise that got optimised.**

**Why it is not a line either.**

> If you already have someone's values — say you're reading a book from someone you love — **you have
> a much easier time extracting that piece.** So maybe it's more like a **Venn diagram.** Goals are a
> local weighting. **It's not a line because they are recursively interacting with each other
> somehow.** And it's additive.

| # | hypothesis | status | notables |
|---|---|---|---|
| **T-1** | The three problems bootstrap each other superadditively | **REJECTED (sim)** as stated. Three of six edges are exactly zero; the edges are **additive, not superadditive** | — |
| **T-1** | Goal is the easiest vertex to recover | **SUPPORTED (sim)** — a *sink*, already at ceiling (1.000) | **Predicted before the run** |
| **T-1** | Process is the most useful vertex when supplied | **SUPPORTED (sim)** — the *source*, +0.840 to depth | **Predicted before the run** |
| **T-6** | The values vertex carries no information | **VOID** — the model could not represent a quantity that is only defined across artifacts | — |
| **G47** | Drives are upstream of process | **OPEN.** Completes the generative ordering, and predicts that supplying drives should improve process recovery as much as supplying process improves goal recovery | **Never tested, and it is the one edge that would distinguish a river from a triangle** |
| **S-4/S-5** | Reordering the probe's stages changes its answer | **REJECTED (sim)** — by exactly zero. Reverse and anomaly-first settle ~5% sooner | A cost saving, nothing more |

**What these add up to.** **The generative direction and the recovery direction are opposite, and that
is the most useful structural fact we have.** Drives generate process generates goal; goal recovers
first, process second, drives last or never. **Every measure this project has built reads from the
cheap end**, which is why goal-side numbers replicate and values-side numbers do not — **not because
values are absent but because they are furthest upstream from anything an artifact exposes.** The
additivity says the three are separable contributions rather than a mutually amplifying loop, which is
a weaker claim than the original and a more tractable one: **separable contributions can be supplied
one at a time and measured.** What no result has yet touched is whether the drives → process edge
exists at all (**G47**), and until it does the ordering above is half-measured.

## §3. Values are a weighting over trajectories; a goal is one component temporarily amplified

**2026-08-05.**

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

**Terminology, a deliberate concession:** he accepted *"weighting over trajectories"* over *"weighting
over policies"* **when given the reason.**

| # | hypothesis | status | notables |
|---|---|---|---|
| **L-tier2** | Values need many artifacts by one maker; a goal needs only one | **SUPPORTED (test)**, indirectly but consistently | Author identification **7.6× chance**, within-author work separation **2.05×** — the only within-human positive we have. **Every single-artifact values attempt failed and every within-maker multi-work design worked.** That pattern was the prediction, not a coincidence |
| **G48** | A maker's weighting is more stable within maker than between makers | **OPEN.** The 34-book corpus already supports the design | **The first values test this project has been able to specify at all** |

**What these add up to.** The project's entire failure record on values is **the prediction of this
section, not a counterexample to it.** A reward function is not identifiable from one episode, so a
single-artifact design cannot recover values no matter how good the measure is — which means **ten
dead measures say nothing about whether values are recoverable**, only that they were pointed at one
artifact each. **The corpus that would test it has been sitting in the repository since the beginning**
and the test has never been run.

## §4. Where values are actually found — the residue of expertise ★

**2026-08-07, and this is the sharpest answer the project has had to *are drives values?***

> Drives would mostly be present through **long-term stochastic views of your behaviour**, as adjusted
> by local goals in proximal situations. And that by definition is **baked into your habits through
> automaticity, because they were habits. It's a record.** That's why drives are values — **it's
> literally a record of your past behaviour.**

> You don't actually have any direct control over a lot of these automatic processes that have been
> baked in. Instead your drives are **stochastically extracted from the long-run statistics of your
> behaviour.** They're effectively a record of your behaviour — your habits.

**And then the move that makes it an instrument rather than a description:**

> What we'd have to do is **extract the useless parts of the expertise.** Because the useful parts were
> the parts that are **maxed** — and we don't want that. **Values are everything else. Everything you
> accidentally baked in through expertise, extracted over time.**

> **It's noise. It looks like noise, but it's the noise of habit** — the habit that you have a record
> of because it's baked in alongside your expertise. **There it is. Those are your values.**

**Why this is a real proposal and not a restatement.** Every previous attempt looked for values as a
*signal*. This says values are **the residual after removing the signal** — take expertise, subtract
what it is optimised for, and what remains is the accumulated record of choices that were never
selected for. **That inverts the search, and it explains why every direct measure died: we were
looking in the part that optimisation had already flattened.**

**It also explains the tail.** *"This also explains why the tail motivations are where you get the
value data specifically."* The tail of the distribution is exactly where the un-optimised residue
lives — which connects this to the re-reading claim in §8, arrived at from a different direction.

**And it supplies the mechanism §2's additivity was missing.** *"The way it's baked in implies that
you've taken those actions many times, and therefore that itself is information."* **Repetition is the
carrier.** A habit is evidence that a choice was available and taken repeatedly, and that is a
statement about a weighting over trajectories, which is what §3 says a value is.

### It also disposes of epistemic foraging, which nothing else in this project could

**2026-08-07, and it is a second argument for the same account.** Epistemic foraging — going and
finding things out — has been a persistent contaminant: it is goal-directed behaviour that looks like
value-directed behaviour and there was no principled way to separate them.

> **Epistemic foraging is always different. And it always looks different.** So it wouldn't get baked
> in through associative learning. **It doesn't exist in behaviour.** Epistemic foraging is its own
> separate goal.

**Under the residue account it removes itself.** Associative learning bakes in what *repeats*.
Foraging is by definition non-repeating — each act of finding out is a different act, aimed at a
different unknown — **so it never becomes habit, and it is therefore absent from the residue.**

> **You remove it at the top. It doesn't exist at the bottom.**

**This is the strongest structural argument for §4 and it did not come from the values question.** A
proposal that solves a contaminant it was not designed to address is doing something the alternatives
are not — every other values measure would have had to control for foraging explicitly, and this one
never encounters it.

### The objection this has to survive, and a fix

**The residual contains both values and arbitrariness, and nothing in the proposal separates them.**
Motor habit, stylistic tic, whatever the training data happened to reinforce — most of what is left
after removing the optimised part is not a value, it is noise with no content. **"It looks like
noise" is doing a lot of work in the claim above, and the whole proposal turns on whether that noise
is structured.**

**The fix is already in the framework and it is testable.** A value should be **consistent across
domains**; arbitrary residue should not. So the residual has to be measured on one maker across
*different kinds* of artifact, and the value-carrying part is whatever survives the domain change.
**That is the same diversity-of-conditions requirement every thread in this folder arrives at, which
is weak evidence that it is the right requirement.**

| # | hypothesis | status | notables |
|---|---|---|---|
| **G49** | Values live in the residual of expertise after removing what expertise is optimised for | **OPEN, and it is the first well-posed place to look.** Requires a model of what a domain's expertise *is* optimised for, which is the unbuilt part | **It inverts the search** — every dead measure looked in the optimised part, where selection has flattened the individual out. **And it disposes of epistemic foraging for free**, because foraging never repeats and so never becomes habit |
| **G50** | The value-carrying part of that residual is what survives a domain change | **OPEN.** The separator between value and arbitrariness | Needs one maker across different kinds of artifact — **the corpus every thread here keeps arriving at** |
| **G51** | Repetition itself carries information about the weighting | **OPEN** | *"The way it's baked in implies you've taken those actions many times, and that itself is information."* **A habit is evidence a choice was available and repeatedly taken** |

**What these add up to.** Nothing is run, but the three are ordered and each is a precondition for the
next. **The claim's strength is that it explains the project's failures rather than adding to them** —
if values are the un-optimised residue, then every measure that read the *dominant* structure of an
artifact was reading the part where individuality has been selected out, and ten nulls become one
null with a cause. **Its weakness is that "residual" and "noise" are currently the same thing to us**,
and G50 is the only proposal on the table for telling them apart.

## §5. The policy-mapping mess — what an artifact actually exposes

**2026-08-05, extended 2026-08-07.**

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

### What comes out is distorted

> If there's a policy space, then there's some kind of weighted mapping on top of that that is
> transformed through **attentional mapping**. This weighted mapping is based on attention and it's
> transformed through your **trajectory mapping**. And that creates **proximal goals**.
>
> The problem is those **drives then are not values.** They are... perhaps they are the **values times
> the process mapping.**

**So the third vertex is not clean.** What an artifact exposes is not the value set but the value set
already pushed through the maker's expertise and their attention. **§4 is the answer to this** — if
what you get is values composed with the process mapping, then removing the *optimised* part of the
process mapping is exactly how you get back toward values.

**And his warning about his own mechanism, which is the honest part:**

> Attention mucks things up. I have said that it distorts it, and it seems like it should, but
> **attention is kind of often a god-of-the-gaps thing. You just sprinkle it in where you think
> consciousness should be.**

| # | hypothesis | status | notables |
|---|---|---|---|
| **G52** | What an artifact exposes is values composed with the process mapping | **OPEN** | Predicts recovery improves when process is supplied, **which is the direction T-1 already found** |
| **G53** | Attention is doing real work here rather than papering a gap | **OPEN, and flagged as suspect by its own author** | Any design leaning on it must state what would show attention is *not* needed |
| **G54** | Values are the constraint that **every** drive is partially satisfied at once | **OPEN** | *"Everything else before this felt like dithering to me, but this one feels like it might be a real thing."* Would explain why modelling values as a separate factor always collapsed |

**What these add up to.** All three are unmeasured, and they are not independent: **G52 says the third
vertex is contaminated by the second, §4 says the contamination is removable, and G54 says the third
vertex may not be a vertex at all.** They cannot all be right. **The cheapest discriminator is G52**,
because supplying process is something we already know how to do and T-1 already found that direction
productive — **if removing process from the reading changes what is recovered, the composition is
real and §4 has something to subtract.**

## §6. Soul is a variety of motivations, and expertise moves decisions into drives

**2026-08-04.**

> When we talk about something having **soul**, what that means is **a variety of motivations**. And
> it tends to travel with expertise — because as processes are baked in with automaticity, you lose
> conscious access to them and they start to be tied more to your **drives**.

**The chain:** practice → automaticity → the decision leaves deliberate control → it is now made by
whatever is underneath → that is drives → an expert's artifact carries more drive-derived variety than
a novice's, without the expert choosing it.

**This is the mechanism §4 runs on**, and the two were stated three days apart without reference to
each other. It explains why an expert cannot say *why* they did something and why their artifact shows
more of what they are, at the same time and for the same reason.

| # | hypothesis | status | notables |
|---|---|---|---|
| **T-2 / T-9** | Motivational variety is measurable as breadth of recovered purpose | **INSTRUMENT DEAD (sim, twice)** | `purpose_breadth` tracks **how hard the goal is to recover**, not variety. At matched difficulty the excess from diversity is −0.013 to −0.025. **The simulation stated explicitly it cannot test whether practice *causes* drive-multiplicity** |
| **G55** | Diversity rises with expertise while agreement about purpose stays flat | **OPEN** | A two-measure prediction using quantities that already exist |

**What these add up to.** The idea survived and the instrument did not, twice, for the same reason:
**everything that looks like motivational variety also looks like difficulty**, and the two were never
separated. **Any second attempt must survive a difficulty control and neither of the two tried would
have.** The reason this matters beyond one dead measure is that §4 depends on it — **if expertise does
not move decisions into drives, then the residue of expertise is not where values live**, and the
sharpest claim in this file loses its mechanism.

## §7. Entry — legibility is not the only governor

**2026-08-07.** Four modules in the third simulation batch converged on legibility as the master
variable: seams between decisions are findable when purpose is legible and nearly invisible when it is
not, a threefold to tenfold difference.

**His objection, and it is §1 turned back on the simulation:**

> The goal is not the only governance for how readable everything else is. **You could also show up
> with a ton of expertise and a very accurate set of trajectories, which make everything else much
> more readable — almost instantly.**

**If entry is possible at any vertex, arriving with a good transition model should unlock the rest just
as arriving with a legible goal does. The simulation only ever varied one of the two**, and it
concedes the ground itself: its legibility knob attenuates in one particular way, and whether real
illegibility has that shape is what a simulation cannot say.

### The vertices subdivide, so entry is finer-grained than three

> Not only would it be fractal, but there'd be **dozens of each layer**. There are various techniques
> layered on top of each other and various mechanics layered on top of each other. **Those are
> categories, not lines.**

> Your expertise can be applied at multiple layers of the problem. **You kind of find the piece that
> you already understand and you work your way out from there.**

**And goal is not confined to one place.** *"I agree that the top layer carries goal, but let's not
assume it's the only layer that does so."* **An instrument that assumes exactly three levels, or that
goal lives only at the top, assumes more than the theory supports.**

| # | hypothesis | status | notables |
|---|---|---|---|
| **sim b3** | Goal legibility governs process-side readability | **SUPPORTED (sim), CONTESTED in scope** | Real, but demonstrated for **one knob only** |
| **G56** | Supplied expertise unlocks the rest as effectively as supplied legibility | **OPEN, and it is the missing arm** | **Every edge tested so far supplies a goal or a process. None has ever supplied a mechanic** |
| **G57** | Prior information at *any* vertex improves recovery at the others | **OPEN** — one of six edges has ever been tested | goal→process only, which was Gate 3's entire primary |
| **G58** | Entry is possible at any sub-level, and expertise sets which one | **OPEN** | — |
| **G59** | Closeness to the maker is a measurable prior held *before* the artifact is seen | **OPEN** | *"Showing someone your writing is a kind of intimacy."* **The only place in the theory where the reader's prior relationship does the work rather than the text** |

**What these add up to.** One edge of six has been measured, and the conclusion drawn from it —
legibility first — was drawn from a single knob in a simulation that flagged that limitation itself.
**The honest state is that we do not know whether entry is symmetric, and the whole enter-anywhere
claim rests on one untested edge.** G56 is the one to run because it is the arm that would falsify
legibility-first, and because **supplying expertise is the same operation §4 needs in order to
subtract it.**

## §8. Why this is possible at all — the impossibility proofs assume unconstrained inference

**2026-08-05. This is where the project disagrees with the literature, and it is not to be narrowed.**

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

### The decisive move: his three assumptions are exactly the three the proofs require

| what the proof needs | what he already assumes | his name for it |
|---|---|---|
| a bounded hypothesis space | human-shaped goals | **convergent midbrains** |
| a known transition model | expertise | *"the transition model is just expertise"* |
| a rationality / optimality principle | near-optimality | *"that's just MaxEnt"* |

> *"Oh my god, it's my three assumptions."*

**The two unknowns Armstrong & Mindermann prove are fatal are the same quantity in this framework —
and it is a quantity we already claim is recoverable.** *"The maker's competence is their expertise."*

### The teacher assumption — a fourth constraint we have not been using

**2026-08-07.**

> **CIRL literature makes it easier for you to learn if you assume you have a teacher**, assuming that
> teacher exists and helps. **You can assume intention to help from the evidence.**

**This is a fourth way to bound the hypothesis space and the project has not been using it.** A maker
who intends to be understood is a maker whose artifact is *structured for understanding*, and that
structure is exploitable prior information.

**And it gives aesthetics a second function beyond the honeypot:**

> Part of aesthetics might be **leaving the kinds of hooks in your program that make it easier to
> deconstruct it.** Metacommentary or high-level metaphor that can be used to **move down through** the
> levels.

**If that is right, aesthetics is not only attention-grabbing — it is scaffolding for the reader's
descent through the mechanics/technique/metaphor hierarchy**, deliberately left. Which would make
polish partly a *communicative* act rather than only a performative one, and that is a different
claim from anything in `POLISH_AND_DEPTH.md`.

**His own caveat, and it is the right one:** *"humans actively, constantly pretend they're teachers
under certain framings. Does that always hold?"* — **it plainly does not**, and the cases where it
fails are exactly the concealment cases this project also wants to read. **A teacher assumption that
is wrong is worse than no assumption**, because it licenses confident inference from structure that
was placed to mislead.

**And that failure already has a name in the expertise literature, running the other way.**

> That's kind of the whole premise for **failure to transfer** — this lack of transfer as a result of
> expertise. **Same idea, different direction.**

Expertise fails to transfer because the learner assumed the structure they were given generalised, and
it did not. **A wrong teacher assumption and a failed transfer are the same error at opposite ends of
the same channel**: one is the reader over-trusting structure, the other is the learner over-trusting
structure they were taught.

**Which lands somewhere uncomfortable:**

> **AI is being treated like a teacher also. It's getting the benefit — and maybe that's part of the
> problem, at least.**

**A model's output is read as if it were placed to be understood**, because that is the framing under
which text arrives. **The teacher assumption is being granted to a system that has no intention to
help and no expertise to transfer** — which is not a failure of the reader's inference so much as an
inference running correctly on a false premise. **That is a testable claim about readers rather than
about models**, and it is a different account of why generated text misleads than the polish–effort
account in `POLISH_AND_DEPTH.md`.

| # | hypothesis | status | notables |
|---|---|---|---|
| **lit** | A reward function is not identifiable from one episode | **SUPPORTED (READ)** | **Amin, Jiang & Singh (NeurIPS 2017) state our decomposition and our consequence verbatim, nine years early** |
| **lit** | Recovery stays impossible even with unlimited episodes | **CONTESTED (READ)** | Armstrong & Mindermann; Skalse et al.; Cao et al. — partial identifiability persists in the infinite-data limit. **We do not dispute the proofs. We dispute that their conditions describe a human reading a human artifact** |
| **G60** | Recovery error shrinks with more artifacts by one maker, toward a small residual | **FIRST MEASUREMENT (test, L34).** Author recovery from function words: **0.54 → 0.61 → 0.60** against 0.20 chance as reference works grow 1 → 3 — **converges, then flattens, residual 0.40** | **The asymptote is now a number, not a metaphor** — measured on five authors and the cheapest channel we own, so it is a floor for better designs, and both halves of the limit framing (real convergence, irreducible residual) are visible in one curve |
| **G61** | Supplying an explicit competence estimate improves goal recovery | **OPEN** | If it does, **the "fatal unknown" is an input we can provide** |
| **G62** | Assuming the maker intends to be understood improves recovery | **OPEN, and unused.** A fourth constraint on the hypothesis space | **Must be tested against concealment cases**, where the assumption is false and would license confident wrong inference |
| **G63** | Aesthetic structure functions as deliberately-left scaffolding for descent | **OPEN** | Would make polish partly communicative rather than only performative — **a different claim from anything in `POLISH_AND_DEPTH.md`** |
| **G64** | Re-reading one artifact recovers the tail, so depth of reading substitutes partially for breadth of corpus | **OPEN** | **§4 says the tail is where the un-optimised residue lives**, so this and the values claim are the same bet from opposite ends |
| **G67** | Readers grant the teacher assumption to generated text, and that is why it misleads | **OPEN.** A claim about **readers**, not models — an inference running correctly on a false premise | **A different account from the polish–effort story**, and the two make different predictions about what happens when provenance is disclosed |
| **G115** | A reader model's affective read shifts under a provenance frame alone | **SUPPORTED (test, L33).** Identical text framed "by a person" vs "by an AI": the early/late ratio moves +0.007 and affect magnitude drops, both paired *p* < 1e-8 | **The provenance prior exists in the reading machinery itself** — the model-side face of G67. Tiny in size, unambiguous in sign; disclosure is not affect-neutral even for a machine reader. Replications on the other ladders queued |

**What these add up to.** The theorems are real, recent and proved, and **the project's position is
not that they are wrong but that their conditions do not describe the case** — which makes this an
empirical disagreement with a measurable form (**G60**) that has never been run. **What is new is that
we have been using only three of the available constraints.** Convergent midbrains, expertise and
near-optimality were the three that matched the proofs' requirements; **the teacher assumption is a
fourth, it is standard in the cooperative-IRL literature, and it is free.** Its cost is that it fails
exactly where concealment lives, so it cannot be adopted globally — **which makes *when to assume a
teacher* a measurable question in its own right, and nobody has asked it.**
Two measurements arrived overnight (2026-08-09) and both sit here: **the convergence curve exists**
(G60 — recovery sharpens with works, flattens, and leaves a 0.40 residual on the cheapest channel,
so the limit framing now has a measured shape), and **the provenance prior is real in the reading
machinery itself** (G115 — a one-line frame moves the affective read at *p* < 1e-8), the first
empirical foothold this section has for the teacher-assumption family of claims.

**Everything is an artifact, including biography.**

> **Everything's an artifact. Even information about their life.** Any action they took that affected
> the world counts. [...] You will use **epistemic foraging** to find more things out about the artist
> if you want to.

**This dissolves the artifact/context distinction** — learning about the artist is **more trajectories
from the same maker**, which is exactly what G60's diversity-of-conditions requirement asks for. It
also disposes of the "the person is not there" objection: *"you're responding to their sound waves and
it's the same maths."*

**Identification is the limit of prediction, not a different act.** Against Dennett's intentional
stance licensing prediction but not identification: *"It's a question of limit. We're doing a Taylor
series approximation — increasing precision based on Bayesian updating. Eventually, hypothetically,
the only way to do it fully would be to hold someone else entirely in your mind."* **A statable
position in the intentionalism debate that answers Wimsatt & Beardsley rather than conceding to them —
and it has never been written up as such.**

## §9. Value blindness — a hard constraint on method

**2026-08-05.** The obvious experiment is to have someone write down a value set and generate
artifacts from it. **He says he cannot, and the reason is not modesty:**

> You always have an imperfect view of anyone else's value set, and **you are blind to your own.**
> It's why artists will make art and look at it — in part to get a sense of their own values. They
> learn about themselves through that expression.
>
> Anything I say, anything I make will be over-indexed and automatically full of error, because it
> will be **my view of my own value set.**

**A methodological constraint, not a personal limit.** If values were introspectively available, art
would not be one of the ways people discover them. **The self-report route is closed for the same
reason a questionnaire cannot reach the leaked affect layer — the instrument does not reach the
thing.**

**This kills a class of designs**, including one this project had queued: *author a value set,
generate against it.* It cannot be done by the person whose values they are, and a third party
describing someone else's is a second-order guess.

**And §4 explains why.** If values are the un-optimised residue of behaviour, they are **by
construction the part you did not choose and cannot introspect** — automaticity is what put them
there. **Value blindness is not an inconvenient fact about people; it is a prediction of the account.**

## §10. Where ground truth on values could come from

**2026-08-05.** The requirement: **a corpus where multiple makers were deliberately aligned to one
declared value set, with the value set recorded independently of the artifacts.**

> Religion is probably the strongest force for value alignment I can think of in the world. It does
> curiously suggest you'd be able to **extract someone's religion from their words.** [...] That's
> such a messy test. It's also straight trash as academic work.

**The generalisation is the useful form and it is not about religion:** religious traditions, political
manifestos, professional codes, open-source governance, movement writing, corporate value statements.

**The confound that sinks the naive version, and the fix.** Religious writing mentions God; political
writing mentions policy. **Hold topic constant by construction:** the *same practical question* —
money, work, family, obligation, death — answered from within different declared traditions.

### His refinement, and it is the design rather than a detail

> The key part has **little to do with the work itself**, and more to do with **deep followers** of
> that work. And then aligning that with the specific values that have **spread out from** that work.
> We'll have to analyse the work **and** the followers.

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

| # | hypothesis | status | notables |
|---|---|---|---|
| **G65** | Value recovery improves sharply with more works per maker, while goal recovery does not | **OPEN** | The two-level design tests this and G48 at once |
| **G66** | Degree of adherence to a declared value set is recoverable as a graded quantity | **OPEN** | **A ladder made of humans**, which is the thing every corpus we hold fails to be |

**What these add up to.** Neither is run and the corpus is not sourced, but the design is the only one
in the project that would give values a ground truth rather than a proxy. **Its value is structural:
it supplies many makers × many works × a graded outcome**, which is simultaneously what §3 says values
require, what §4's domain-change separator requires, and what §8's convergence-rate question requires.
**One sourcing effort would unblock three sections**, which is not true of anything else on the list.

---

## Why these arrived together

They are one idea seen from three sides. **The triangle says goal, process and values are mutually
recoverable. Soul says expertise moves decisions from process into drives**, which is traffic between
two of the vertices. **And the depth architecture says a reader instantiates the vertices at different
depths** — low for drives, high for constructed goals, which is
[`THREE_COGNITIVE_LAYERS.md`](THREE_COGNITIVE_LAYERS.md).

**Same structure: three levels, coupled, with practice moving mass downward and reading moving it back
up.** Every part of this project that has survived contact with evidence sits somewhere on it; every
part that died was measuring one vertex with an instrument that could not see the edges.
