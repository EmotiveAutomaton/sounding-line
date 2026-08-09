# The triple inference — what a reader infers about a maker, and what makes it recoverable

*(formerly "the empathy triangle" — renamed 2026-08-08 at the curator's instruction)*

> Empathy is effectively a variational inference problem — **three separate variational inference
> problems being solved in parallel**, each bootstrapping the others: the extraction of the **proximal
> goal**, the extraction of the **process**, and the extraction of the **values and drives**.

> I'm **specifically modelling it after human empathy** — what seems to be the process that I believe
> human empathy is.

**The canonical claim, in the corrected vocabulary:** the triple inference names **three target
families at different timescales** — not three equivalent nodes, and not necessarily three separate
algorithms. A reader jointly estimates the maker's **proximal goal**, the **process** that produced
the artifact, and the maker's **more persistent motivational organization**; evidence about one
target constrains the posterior over the others. **Non-claim:** the targets need not occupy three
cognitive layers or form three symmetric edges. **Current verdict:** goal and process interact
measurably in simulation; value profiles become recoverable across artifacts in the constructed
world; the full three-way coupling is untested. They are one idea seen from three sides — the
inference names the targets, expertise moves decisions between them
([`DECISION_TRACES.md`](DECISION_TRACES.md)), and a reader instantiates them on whatever machinery
it has ([`THREE_COGNITIVE_LAYERS.md`](THREE_COGNITIVE_LAYERS.md)).

On the words: *variational inference*, technically, means approximating an intractable posterior by
optimizing over a restricted family (Blei et al.); the cognitive claim as evidenced is **Bayesian
inverse planning / joint latent-variable inference** (Baker, Saxe & Tenenbaum is the direct
precedent), for which variational inference would be one possible implementation. His quotes stand
as spoken; the file's own prose uses the precise terms.

**This file owns** the inference targets, their dependencies, value identifiability, and
convergence. **It does not own** artifact cues ([`DECISION_TRACES.md`](DECISION_TRACES.md)), reader
heuristics ([`READER_HEURISTICS.md`](READER_HEURISTICS.md)), model depth, or alignment.

---

# Part I — The inference problem

## §1. The three target families

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

Translated into objects, before any claims about their shape:

| object | definition | timescale |
|---|---|---|
| **proximal goal** G | what the maker is locally trying to accomplish in this artifact or episode | episode-local |
| **process** P | the realized sequence of decisions and actions that produced it | artifact-local |
| **expertise** K | the maker's learned competence — the transition model constraining which processes are available and how reliably they execute | cross-episode, domain-relative |
| **drives** D | currently active motivational pressures or primitive constraints | state-dependent |
| **values** V | the more persistent organization of tradeoffs among goals, drives, and trajectories | longitudinal |
| **context** C | commission, coercion, medium, audience, constraints, available alternatives | episode-local |

Two conflations this table dissolves. **Process is not expertise**: process is what happened;
expertise is the maker-model used to predict what could happen — the "process" target family has
two scales, and results about one do not automatically transfer to the other. **Drives are not
values**: drives may be inputs to action selection; values describe their persistent organization —
treating them as synonyms is why the third vertex has repeatedly appeared and disappeared in this
file's history. Where his quotes say "values/drives" as one item, the prose keeps them split.

**"Three" refers to three questions, not three ontologically equal objects.** Goal and process are
episode-things; the third question — the maker's persistent motivational organization — is a
different *kind* of thing, defined across episodes, which is most of why it has been the hard one.

## §2. Forward generation and inverse recovery

What the maker generates, what the artifact preserves, and what the reader reconstructs are three
different things, and the theory has to keep them apart. A minimal generative account, held loosely:

    G  = f(V, D, C)          the goal is selected under values, drives, and context
    P  ~ pi(K, G, C)         the process is drawn from what expertise makes available
    O  = h(P, C)             the artifact preserves the process, lossy, shaped by the medium

    the reader approximates  p(G, P, V, D, K | artifacts, contexts)

Stated this way, two facts fall out that the old formulation suppressed: a single artifact can
support goal and process inference while values require multiple observations; and a commissioned,
coerced, or instrumental goal can **diverge** from values — "goal is a temporarily amplified value"
is the special case where context is friendly, not the definition.

His account of the machinery, which is about reading *other people*, corrected after I wrote it as
self-generation:

> Attention directs toward **policy space**. You use the **trajectory mapping — which is our
> expertise** — layered over a **weighted policy map, which is our outcomes**. From that we get our
> actions.

> This is specifically about doing it **to other people**. I'm referring to **the creator**. This is
> maths you're doing **in your head, through embodied simulation, with the creator.**

The stack is the model the reader builds and runs of the maker, on their own machinery — you
simulate the maker with your own equipment, and the parts you lack are the parts you cannot recover.
Embodied simulation is a candidate human *solver*, not part of the problem's definition. What comes
out is distorted:

> If there's a policy space, then there's some kind of weighted mapping on top of that that is
> transformed through **attentional mapping**. This weighted mapping is based on attention and it's
> transformed through your **trajectory mapping**. And that creates **proximal goals.**
>
> The problem is those **drives then are not values.** They are... perhaps they are the **values times
> the process mapping.**

So the third target arrives composed with the second — an artifact exposes values already pushed
through expertise and attention — and his warning about his own mechanism stands:

> Attention mucks things up. I have said that it distorts it, and it seems like it should, but
> **attention is kind of often a god-of-the-gaps thing. You just sprinkle it in where you think
> consciousness should be.**

On the formalisms, once, so they stop substituting for each other: **inverse planning** is the broad
model (hidden mental states from behavior); **IRL** is the narrower reward-recovery problem;
**MaxEnt** is one rationality/noise model within IRL; **CIRL** is an interactive cooperative game
and does not describe every maker–reader relationship; **variational inference** is an approximation
method. Each informs a part of this file; none is the claim.

## §3. Coupling — without premature topology

The correction that started the file: the project had been treating one edge — goal → process in a
single encounter — as the whole thing. **That is one of six directed edges**, and whichever target
you can reach first is the one to enter by:

> I'm trying to find some layer within which I can use my expertise, then use that expertise to solve
> the easy part, and then I use that to get the motivation, and then that I can use to
> reverse-engineer the rest of it that I don't understand. **Is it a three goddamn part process?**

The shape hypotheses, held as hypotheses:

> **I would assume that drives are upstream of even process.** And again, it would require several
> samples both within and across a given individual. And that would create this kind of Lagrangian
> Taylor-series-looking thing where you're moving towards a limit.

> If empathy is not a triangle but **a river, what are its tributaries?** If it's additive, that
> implies there's something else being added to it. And there's only so many things it could be.
> **Certainly expertise is part of it. Is it goals minus expertise equals drives?**

> If you already have someone's values — say you're reading a book from someone you love — **you have
> a much easier time extracting that piece.** So maybe it's more like a **Venn diagram.** Goals are a
> local weighting. **It's not a line because they are recursively interacting with each other
> somehow.** And it's additive.

(The subtraction equation is dimensionally odd — a weighting and a transition model do not subtract
— but the intuition survives as §5's residue account.) And entry is finer-grained than three:

> Not only would it be fractal, but there'd be **dozens of each layer**. There are various techniques
> layered on top of each other and various mechanics layered on top of each other. **Those are
> categories, not lines.**

> Your expertise can be applied at multiple layers of the problem. **You kind of find the piece that
> you already understand and you work your way out from there.**

*"I agree that the top layer carries goal, but let's not assume it's the only layer that does so"* —
an instrument that assumes exactly three levels, or goal only at the top, assumes more than the
theory supports.

**What is actually measured, stated without the chain.** The first coupling simulation used a
substitute construction with **no working values vertex**, so it can say nothing about any edge
involving values — it measured the goal–process pair. There: goal recovery sat at ceiling (so "goal
is a sink" is partly a ceiling artifact, not yet a general cognitive fact), supplying process moved
depth substantially, three of six edges were exactly zero, and the coupling was additive rather
than mutually amplifying. The honest position: **goal and process show asymmetric information flow
in the current construction; the topology involving values is unknown.** The drives→process edge
(the one that would distinguish a river from a triangle) is queued in the simulation that now has a
working values construction. All rows in §8.

# Part II — The difficult third inference

## §4. Drives, values, and goals

The project's proposed ontology — proposed, not standard reinforcement-learning vocabulary:

> Take value space and treat it as a **weighting on trajectories**. A goal would be a weighting of a
> specific policy plan — raising one action within that plan above the rest **temporarily, due to
> attention**.

> You need all of the actions of the person to extract their value map. We need as much information as
> possible to get as close to an accurate value mapping as we can.

(*"Weighting over trajectories"* over *"weighting over policies"* was his deliberate concession when
given the reason.) Under §1's table this reads: values are the standing organization; a **current
drive** is a state-dependent pressure; a **goal** is selected under values, drives, instructions,
and constraints — and can be imposed against all of them; and an **expressed trajectory may
misrepresent all three**. The four are distinct, and any measure that collapses them inherits the
collapse.

## §5. Where value information could live — four competing accounts

The file used to declare one of these the answer; they are candidates, and the constructed world
has begun discriminating among them.

**1. Amplification** — values appear through which goals receive attention (§4's account read as an
instrument). **2. Conjunctive satisfaction** — values are the constraint that every drive is
partially satisfied at once: *"Everything else before this felt like dithering to me, but this one
feels like it might be a real thing."* **3. Longitudinal residue** — stable unoptimized habit
preserves value information:

> Drives would mostly be present through **long-term stochastic views of your behaviour**, as adjusted
> by local goals in proximal situations. And that by definition is **baked into your habits through
> automaticity, because they were habits. It's a record.** That's why drives are values — **it's
> literally a record of your past behaviour.**

> What we'd have to do is **extract the useless parts of the expertise.** Because the useful parts were
> the parts that are **maxed** — and we don't want that. **Values are everything else. Everything you
> accidentally baked in through expertise, extracted over time.**

> **It's noise. It looks like noise, but it's the noise of habit** — the habit that you have a record
> of because it's baked in alongside your expertise. **There it is. Those are your values.**

The residue account inverts the search — every direct measure read the optimized part, where
selection has flattened the individual out — and *"the tail motivations are where you get the value
data specifically"*: the tail is where un-optimized residue lives, which makes re-reading (§8's
G64) the same bet from the other end. Repetition is the proposed carrier: *"the way it's baked in
implies that you've taken those actions many times, and therefore that itself is information."*
Its objections: the residual contains values **and** arbitrariness, and only a domain-change test
separates them; and the epistemic-foraging disposal this file once claimed is **withdrawn**. His
argument stands as spoken:

> **Epistemic foraging is always different. And it always looks different.** So it wouldn't get baked
> in through associative learning. **It doesn't exist in behaviour.** Epistemic foraging is its own
> separate goal.

> **You remove it at the top. It doesn't exist at the bottom.**

— but foraging **strategies** recur even where targets change: search order, source selection,
stopping rules, and uncertainty tolerance can all bake in and survive in the residue. The confound
remains, and the account must carry it. **4. Absence under commission** — a
missing drive becomes legible through *how* an imposed goal is pursued (the made-under-duress
mechanism; the routing consequence lives in [`ALIGNMENT.md`](ALIGNMENT.md) §0).

The constructed world's discrimination so far, method-validating and nothing more: conjunctive
satisfaction read a profile from one constructed artifact where amplification could not; profiles
converged across artifacts; and an absent drive became recoverable under commission, with pure
compliance collapsing to exactly chance. **None of this is evidence that real human values have
been recovered.** Rows in §8.

## §6. Value blindness, and where longitudinal ground truth could come from

Self-report is closed as ground truth, and the reason is not modesty:

> You always have an imperfect view of anyone else's value set, and **you are blind to your own.**
> It's why artists will make art and look at it — in part to get a sense of their own values. They
> learn about themselves through that expression.
>
> Anything I say, anything I make will be over-indexed and automatically full of error, because it
> will be **my view of my own value set.**

If values were introspectively available, art would not be one of the ways people discover them —
and under the residue account the blindness is a *prediction*: automaticity put the values where
introspection does not reach. This kills the author-a-value-set-and-generate design class. One
artifact is insufficient for the same identifiability reason a reward function needs many episodes;
**diversity of conditions** is what separates value from arbitrary residue; and *everything is an
artifact* extends the observation set:

> **Everything's an artifact. Even information about their life.** Any action they took that affected
> the world counts. [...] You will use **epistemic foraging** to find more things out about the artist
> if you want to.

*"You're responding to their sound waves and it's the same maths."* The corpus that would supply
ground truth is makers deliberately aligned to a declared value set, read through **deep
followers**:

> Religion is probably the strongest force for value alignment I can think of in the world. It does
> curiously suggest you'd be able to **extract someone's religion from their words.** [...] That's
> such a messy test. It's also straight trash as academic work.

> The key part has **little to do with the work itself**, and more to do with **deep followers** of
> that work. And then aligning that with the specific values that have **spread out from** that work.
> We'll have to analyse the work **and** the followers.

The design's prize is a **gradient of adherence — a ladder made of humans** — with topic held
constant by construction (the same practical question answered from within different traditions),
and the honest objections kept: canon formation selects, translation and era confound, and declared
values are not held values — tolerable because the label needed is what an artifact was made
*under*, not what the maker truly valued. Sourcing detail and procedure live in `TODO.md`; the
blocking rows stay in §8.

# Part III — Epistemic limits and evidence

## §7. Identifiability, not impossibility

**This is where the project disagrees with the literature, and it is not to be narrowed.**

> Saying something isn't possible just means you haven't found the way to do it yet — **especially if
> the world is doing it.**

His correction of my own overclaim ("humans do this, therefore it can be done"):

> I'm not saying humans arrive at a conclusion of value. I'm saying they use **a bunch of tricks to
> actively try to get closer** to it.
>
> **It's a limit situation.** You get closer and closer over time. There *is* a solution — a perfect
> mapping of the person's brain — but we approach it **through inference with error**, and we are
> never sure we have the answer.

> **"Irrational agents" is incorrect about humans.** In a lot of ways we are *boundedly
> hyper-rational.* **It looks like irrationality to have fractal motivations.**

The theorems are real: a policy cannot uniquely identify both a reward function and an unknown
planning algorithm, even with unlimited data; additional normative assumptions are required
(Armstrong & Mindermann). The project's response, stated carefully: **human readers use substantive
priors — about human bodies, competence, contexts, and communicative behaviour — that may improve
useful recovery without producing unique identification. That is a convergence claim, not a
refutation of the theorem.** The priors line up with what the proofs demand:

| what the proof needs | what he already assumes | his name for it |
|---|---|---|
| a bounded hypothesis space | human-shaped goals | **convergent midbrains** |
| a known transition model | expertise | *"the transition model is just expertise"* |
| a rationality / optimality principle | near-optimality | *"that's just MaxEnt"* |

> *"Oh my god, it's my three assumptions."*

The two unknowns the proofs call fatal are one quantity here — *"the maker's competence is their
expertise"* — and it is a quantity this project claims is partially recoverable. A fourth candidate
constraint is communicative intent:

> **CIRL literature makes it easier for you to learn if you assume you have a teacher**, assuming that
> teacher exists and helps. **You can assume intention to help from the evidence.**

That prior is canonical in [`READER_HEURISTICS.md`](READER_HEURISTICS.md) §1, with its concealment
caveat; here it is one identifiability assumption among four, adoptable only conditionally.

## §8. The evidence ledger

One table, grouped by the question each row bears on. Sources: (test) real text here, (sim) the
parent simulation, (lit) published work.

| # | question · hypothesis | status |
|---|---|---|
| | **Are goal and process separable, and does supplying one help the other?** | |
| **T-1** | The goal–process pair in the substitute construction (no values vertex): superadditive bootstrapping; goal easiest; process most useful when supplied | **One run, three findings (sim):** superadditivity REJECTED — edges additive, three of six exactly zero; goal-easiest SUPPORTED at ceiling (a ceiling result, not yet a general fact); process-most-useful SUPPORTED (+0.84 to depth). Both directional findings were predicted before the run |
| **sim b3** | Goal legibility governs process-side readability | **SUPPORTED (sim), CONTESTED in scope** — one knob, and the simulation flags the limit itself |
| **G56** | Supplying mechanics-level information unlocks goal recovery | **OPEN — the missing arm**; every edge tested supplies a goal or a process, never a mechanic |
| **G57** | Prior information at any target improves the others | **OPEN** — one of six edges ever tested |
| **G58** | Entry is possible at any sub-level, with expertise setting which | **OPEN** |
| **G47** | Drives are upstream of process | **OPEN, now testable** — the values construction exists in the simulation; the coupling run is queued there. The one edge that would distinguish a river from a triangle |
| | **Is the third target contaminated, and by what?** | |
| **G52** | An artifact exposes values composed with the process mapping | **OPEN** — predicts supplying process changes what is recovered, the direction the goal–process run already found |
| **G53** | Attention does real work rather than papering a gap | **OPEN, flagged suspect by its own author** |
| **T-6** | The substitute construction's values vertex carries information | **VOID (sim)** — it could not represent a cross-artifact quantity |
| | **Where does value information live? (§5's four accounts)** | |
| **G54** | Conjunctive satisfaction: values constrain how all drives are jointly satisfied | **OPEN on real text; the account the constructed world favours** — it read a profile from one artifact where amplification could not |
| **G49** | Longitudinal residue: values live in the un-optimized residual of expertise | **OPEN** — requires a model of what a domain's expertise is optimized for; carries the habit-shadow and foraging-strategy confounds |
| **G50** | The value-carrying residual is what survives a domain change | **OPEN** — the only proposed separator of value from arbitrariness |
| **G51** | Repetition itself carries the weighting | **OPEN** |
| **S-14** | An absent drive is recoverable | **SUPPORTED (sim) as method; OPEN on real artifacts** — near-invisible spontaneous (0.61), perfect under commission (1.00), compliance collapses to exactly 0.5: *how the goal is pursued* discriminates |
| | **Do more artifacts per maker improve recovery, toward what residual?** | |
| **S-15** | Value-profile recovery converges with artifacts, residual priced | **SUPPORTED (sim)** — 0.53 → 0.98 over 1–50 artifacts, residual 0.009; bounded-family assumption worth 0.24; **corpus price ~20 works per maker**; conjunctive-vs-amplification discriminates constructions |
| **G60** | Recovery error shrinks with works, toward a small residual | **SUPPORTED (test), first pass** — 0.54 → 0.61 → 0.60 against 0.20 chance over one-to-three reference works: converges, flattens, residual 0.40 on the cheapest channel and five authors. The asymptote is a floor for better designs, and both halves of the limit framing are visible in one curve |
| **L-tier2** | Values need many artifacts; a goal needs one | **SUPPORTED (test), indirectly** — every single-artifact values attempt failed; every within-maker multi-work design worked (7.6× and 2.05× chance) |
| **G48** | A maker's weighting is more stable within than between makers | **OPEN** — the 34-book corpus supports the design |
| **G64** | Re-reading one artifact recovers the tail | **OPEN** — the residue account's other end |
| | **Is values recovery distinct from identity recovery?** | |
| **G65** | Value recovery improves sharply with works per maker while goal recovery does not | **OPEN** — the follower-corpus design tests this and G48 at once |
| **G66** | Adherence to a declared value set is recoverable as a graded quantity | **OPEN** — a ladder made of humans; blocked on sourcing |
| | **What do the theorems leave open?** | |
| **lit** | A reward function is not identifiable from one episode | **SUPPORTED (READ)** — Amin, Jiang & Singh state the decomposition and the consequence |
| **lit** | Recovery stays impossible with unlimited episodes | **CONTESTED (READ)** — Armstrong & Mindermann and successors prove partial identifiability persists; we dispute that their conditions describe a human reading a human artifact, as a convergence claim |
| **G61** | An explicit competence estimate improves goal recovery | **OPEN** — if yes, the "fatal unknown" is an input |
| **S-4/S-5** | Reordering the reader's stages changes the answer | **REJECTED (sim)** — by exactly zero; a cost saving only |

**What the ledger says.** The goal–process pair behaves like a real coupled inference in the one
construction that has tested it, with the important caveat that goal sat at ceiling; everything
touching values divides cleanly into method-validating simulation results (profiles converge,
absence reads under commission, conjunctive satisfaction beats amplification) and open real-text
rows blocked on the corpus every thread arrives at — many makers, many works, graded outcomes. The
one real-text convergence curve behaves exactly as the limit framing predicts, at first-pass
strength. The topology involving values is unknown, and the drives→process run that would start
settling it is queued where it can now be run. **Confidence: the goal–process findings and the
identifiability reading are one bad test away and replicated-in-literature respectively; the value
accounts are sim-validated methods at best, untested on any real maker; the convergence curve is
one bad test away.**

## §9. Scope and boundaries

**Human empathy is the motivating phenomenon, not an established synonym** — *empathy* carries 43
catalogued definitions, which is why the mechanism is named for what it does. **Accurate attribution
is not caring**: nothing in this file bears on motivation to protect, which is
[`ALIGNMENT.md`](ALIGNMENT.md)'s problem. **A model can reconstruct without experiencing** — the
architecture file's bridge. **And value recovery is posterior narrowing, not mind duplication**:

> My personal end goal is to find a way to **fully give AI human empathy, but not human emotions**
> [...] it requires some kind of subordinate solution space that converges on these **predictions of
> these interoceptive signals.**

Against Dennett's stance that prediction never licenses identification: *"It's a question of limit.
We're doing a Taylor series approximation — increasing precision based on Bayesian updating.
Eventually, hypothetically, the only way to do it fully would be to hold someone else entirely in
your mind."* A statable position in the intentionalism debate that answers Wimsatt & Beardsley
rather than conceding to them — and it has never been written up as such.
