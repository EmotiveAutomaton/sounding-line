# The triple inference: what a reader infers about a maker, and what makes it recoverable

*(formerly "the empathy triangle", renamed 2026-08-08 at the curator's instruction)*

> While I have previously described the triple inference idea as three separate variational
> inference problems being solved in parallel with each bootstrapping the others, a more precise
> description would be **three constrained target families that are operating at different
> timescales**. That's about as loosely as I can claim currently with the evidence that I've got.
> This process is still modeled directly after the process of appreciation of intent and intent
> extraction, something that I believe to be **the central mechanism for human empathy** across the
> board, frankly.

**The canonical claim, in the corrected vocabulary.** The triple inference names **three target
families at different timescales**, not three equivalent nodes, and not necessarily three separate
algorithms. A reader jointly estimates the maker's **proximal goal**, the **process** that produced
the artifact, and the maker's **more persistent motivational organization**; evidence about one
target constrains the posterior over the others. **Non-claim.** The targets need not occupy three
cognitive layers or form three symmetric edges. **Current verdict.** Goal and process interact
measurably in simulation; value profiles become recoverable across artifacts in the constructed
world; the full three-way coupling is untested. They are one idea seen from three sides. The
inference names the targets, expertise moves decisions between them
([`DECISION_TRACES.md`](DECISION_TRACES.md)), and a reader instantiates them on whatever machinery
it has ([`THREE_COGNITIVE_LAYERS.md`](THREE_COGNITIVE_LAYERS.md)).

On the words. *Variational inference*, technically, means approximating an intractable posterior by
optimizing over a restricted family (Blei et al.); the cognitive claim as evidenced is **Bayesian
inverse planning / joint latent-variable inference** (Baker, Saxe & Tenenbaum is the direct
precedent), for which variational inference would be one possible implementation. The canonical
statement above is his own restatement in the corrected vocabulary (2026-08-10); the original
variational phrasing survives in §1 as a superseded form.

**This file owns** the inference targets, their dependencies, value identifiability, and
convergence. **It does not own** artifact cues ([`DECISION_TRACES.md`](DECISION_TRACES.md)), reader
heuristics ([`READER_HEURISTICS.md`](READER_HEURISTICS.md)), model depth, or alignment. Evidence
rows live in the section that interprets them *(the single end-of-file ledger dissolved
2026-08-10, his instruction)*; sources are (test) real text here, (sim) the parent simulation,
(lit) published work.

---

# Part I: The inference problem

## §1. The three target families

**Superseded** by the restatement at the head of the file, kept as the original form:

> I think empathy is effectively a variational inference problem – **three separate variational
> inference problems being solved in parallel, and each one bootstraps the others.** The more
> information you have in one, the easier it is to solve the others. They have relative strengths,
> relative difficulties, but they all help the other.
>
> 1. the extraction of the **proximal goal**
> 2. the extraction of the **process**
> 3. the extraction of the **values / drives**

> This is why an expert can more readily understand what a novice was thinking as they were making
> something, in a way that another person cannot. This is why being close friends with someone, you
> can read their book and get more of a sense of why they made certain choices. **This is why
> information is passed more easily between people who are close.**

The current claim for the expert and friend cases is deliberately modest. Expertise and
familiarity supply **priors and entry points that may improve recovery**, nothing stronger, and
the closeness prior itself is untested (G59, canonical in
[`READER_HEURISTICS.md`](READER_HEURISTICS.md) §1).

Translated into objects, before any claims about their shape:

| object | definition | timescale |
|---|---|---|
| **proximal goal** G | what the maker is locally trying to accomplish in this artifact or episode | episode-local |
| **process** P | the realized sequence of decisions and actions that produced it | artifact-local |
| **expertise** K | the maker's learned competence, the transition model constraining which processes are available and how reliably they execute | cross-episode, domain-relative |
| **drives** D | currently active motivational pressures or primitive constraints | state-dependent |
| **values** V | the more persistent organization of tradeoffs among goals, drives, and trajectories | longitudinal |
| **context** C | commission, coercion, medium, audience, constraints, available alternatives | episode-local |

Two conflations this table dissolves. **Process is not expertise.** Process is what happened;
expertise is the maker-model used to predict what could happen. The "process" target family has
two scales, and results about one do not automatically transfer to the other. **Drives are not
values.** Drives may be inputs to action selection; values describe their persistent organization.
Treating them as synonyms is why the third vertex has repeatedly appeared and disappeared in this
file's history. Where his quotes say "values/drives" as one item, the prose keeps them split.

**"Three" refers to three questions, not three ontologically equal objects.** Goal and process are
episode-things; the third question, the maker's persistent motivational organization, is a
different *kind* of thing, defined across episodes, which is most of why it has been the hard one.

| # | hypothesis | status |
|---|---|---|
| **L-tier2** | Values need many artifacts; a goal needs one, because they live at different timescales | **SUPPORTED (test), indirectly.** Every single-artifact values attempt failed; every within-maker multi-work design worked (7.6× and 2.05× chance) |

**State of the section's claim.** The object table is definitional and mostly untestable as
stated, but its load-bearing asymmetry, that the third target is a different timescale of thing,
has the project's most consistent indirect evidence behind it. Nothing has ever recovered values
from one artifact and everything multi-work has found signal, which is exactly the pattern the
timescale column predicts. The two conflation-dissolving distinctions (process against expertise,
drives against values) remain unmeasured distinctions of vocabulary whose first bites arrive
through §5 and §6. Confidence: the timescale asymmetry is one bad test away, resting on
convergent nulls rather than a designed comparison; the rest is untested, logic only.

## §2. Forward generation and inverse recovery

What the maker generates, what the artifact preserves, and what the reader reconstructs are three
different things, and the theory has to keep them apart. A minimal generative account, held loosely:

    G  = f(V, D, C)          the goal is selected under values, drives, and context
    P  ~ pi(K, G, C)         the process is drawn from what expertise makes available
    O  = h(P, C)             the artifact preserves the process, lossy, shaped by the medium

    the reader approximates  p(G, P, V, D, K | artifacts, contexts)

Stated this way, two facts fall out that the old formulation suppressed. A single artifact can
support goal and process inference while values require multiple observations. And a commissioned,
coerced, or instrumental goal can **diverge** from values; "goal is a temporarily amplified value"
is the special case where context is friendly, not the definition.

His account of the machinery, which is about reading *other people*, corrected after I wrote it as
self-generation:

> Attention directs toward **policy space**. You use the **trajectory mapping – which is our
> expertise** – layered over a **weighted policy map, which is our outcomes**. From that we get a
> **weighted map of possible actions**.

> This is specifically about doing it **to other people**. I'm referring to **the creator**. This is
> maths you're doing **in your head, through embodied simulation, with the creator.**

The stack is the model the reader builds and runs of the maker, on their own machinery. You
simulate the maker with your own equipment, and the parts you lack are the parts you cannot recover.
Embodied simulation is a candidate human *solver*, not part of the problem's definition, and his
position on that framing is on record with its evidence named:

> This is one of the pieces that AI continually tries to sand down, the idea that human processes
> are just one of many potential processes for reaching the goal. I am being led by the guiding
> light that **trying to enact human processes in this space explicitly** is what's leading to me
> being able to replicate the research on the cutting edge so easily and predict their outcomes so
> frequently. But yes, technically it's possible that embodied simulation is just one candidate
> process. **So it is clearly a load-bearing one for me.**

A methodological bet rather than a finding, held with its own concession attached. What comes
out is distorted:

> If there's a policy space, then there's some kind of weighted mapping on top of that that is
> transformed through **attentional mapping**. This weighted mapping is based on attention and it's
> transformed through your **trajectory mapping**. And that creates **proximal goals.**

> It's more correct to say that **expertise distorts the available possibilities, based on value
> realization in a given environment, due to the context available.** One's values are exposed
> through proximal goals that are themselves attention-weighted, expertise-distorted values. And it
> helps that there is some kind of **drive commonality** through which that expertise distortion
> exists.

So the third target arrives composed with the second. An artifact exposes values already pushed
through expertise and attention under context, with a shared drive substrate as the assumption
that keeps the distortion decodable at all, and his warning about his own mechanism stands:

> Attention mucks things up. I have said that it distorts it, and it seems like it should, but
> **attention is kind of often a god-of-the-gaps thing. You just sprinkle it in where you think
> consciousness should be.**

On the formalisms, once, so they stop substituting for each other. **Inverse planning** is the broad
model (hidden mental states from behavior). **IRL** is the narrower reward-recovery problem.
**MaxEnt** is one rationality/noise model within IRL. **CIRL** is an interactive cooperative game
and does not describe every maker-reader relationship. **Variational inference** is an approximation
method. Each informs a part of this file; none is the claim.

| # | hypothesis | status |
|---|---|---|
| **G52** | An artifact exposes values already distorted by expertise and attention under context | **OPEN.** Predicts supplying process changes what is recovered, the direction the goal-process run already found |
| **G53** | Attention does real work rather than papering a gap | **OPEN, flagged suspect by its own author** |
| **S-4/S-5** | Reordering the reader's stages changes the answer | **REJECTED (sim)** by exactly zero; a cost saving only |

**State of the section's claim.** The generative account remains a framework rather than a
finding, and its composition claim now stands in the restated form, expertise distorting the
available possibilities under context rather than a multiplicative shorthand, with drive
commonality named as the assumption that keeps the distortion decodable. Both composition rows
are open, and the restated claim carries the same testable direction the one coupling run
already leaned toward. The single behavioral fact here cuts the right way for a *joint* account,
since a staged pipeline would care about stage order and the simulated reader's answer does not
move at all when the order changes. The distortion story's weakest named part is attention,
flagged by its own author before anyone else could. Confidence: the order-insensitivity is
sim-only; the composition claims are untested, logic only.

## §3. Coupling, without premature topology

The correction that started the file. The project had been treating one edge, goal → process in a
single encounter, as the whole thing. **That is one of six directed edges**, and whichever target
you can reach first is the one to enter by:

> I'm trying to find some target or sub-level within which I can use my expertise, then use that
> expertise to solve the easy part, and then I use that to get the motivation, and then that I can
> use to reverse-engineer the rest of it that I don't understand. **Is it a three goddamn part
> process?**

> **Enter wherever your prior expertise provides maximum traction**, and then you let the evidence
> constrain the other targets from there.

On the shape of the three mappings and their relationship to each other, the file has cycled
through several mental heuristics. Rivers and tributaries, Venn diagrams, a subtraction, increasing
residuals being contained. Each is preserved in the git history and none is adopted. The actual
relationship is being circled and is deliberately not yet committed to writing, and the one shape
quote that stays is the upstream conjecture, restated without a presupposed mathematical form:

> **I would assume that drives are upstream of even process.** And again, it would require several
> samples both within and across a given individual, a situation where repeated within-person and
> cross-context observations produce increasing convergence towards the creator's policy map. I'm
> not going to presuppose any particular mathematical shape yet.

And entry is finer-grained than three:

> Not only would it be fractal, but there'd be **dozens of each layer**. There are various techniques
> layered on top of each other and various mechanics layered on top of each other. **Those are
> categories, not lines.**

> Your expertise can be applied at multiple layers of the problem. **You kind of find the piece that
> you already understand and you work your way out from there.**

*"I agree that the top layer carries goal, but let's not assume it's the only layer that does so."*
An instrument that assumes exactly three levels, or goal only at the top, assumes more than the
theory supports.

**What is actually measured, stated without the chain.** The first coupling simulation used a
substitute construction with **no working values vertex**, so it can say nothing about any edge
involving values. It measured the goal-process pair. There, goal recovery sat at ceiling (so "goal
is a sink" is partly a ceiling artifact, not yet a general cognitive fact), supplying process moved
depth substantially, three of six edges were exactly zero, and the coupling was additive rather
than mutually amplifying. The honest position. **Goal and process show asymmetric information flow
in the current construction; the topology involving values is unknown.** The drives→process edge
(the one that would distinguish a river from a triangle) is queued in the simulation that now has a
working values construction.

| # | hypothesis | status |
|---|---|---|
| **T-1** | The goal-process pair in the substitute construction (no values vertex): superadditive bootstrapping; goal easiest; process most useful when supplied | **One run, three findings (sim).** Superadditivity REJECTED, edges additive, three of six exactly zero; goal-easiest SUPPORTED at ceiling (a ceiling result, not yet a general fact); process-most-useful SUPPORTED (+0.84 to depth). Both directional findings were predicted before the run |
| **sim b3** | Goal legibility governs process-side readability | **SUPPORTED (sim), CONTESTED in scope.** One knob, and the simulation flags the limit itself |
| **T-6** | The substitute construction's values vertex carries information | **VOID (sim).** It could not represent a cross-artifact quantity |
| **G56** | Supplying mechanics-level information unlocks goal recovery | **OPEN, the missing arm.** Every edge tested supplies a goal or a process, never a mechanic |
| **G57** | Prior information at any target improves the others | **OPEN.** One of six edges ever tested |
| **G58** | Entry is possible at any sub-level, with expertise setting which | **OPEN** |
| **G47** | Drives are upstream of process | **OPEN, now testable.** The values construction exists in the simulation; the coupling run is queued there. The first edge that would begin to discriminate among the candidate shapes the prose declines to name |

**State of the section's claim.** Coupling is real and directional in the one pair ever tested,
and everything past that pair is shape territory the file explicitly declines to write down.
The tested edge behaves like a genuine joint inference with an important asterisk, since goal sat
at ceiling and a ceiling can manufacture both "goal easiest" and "goal is a sink". Five of six
edges have never been supplied, the mechanics arm has never existed, and the substitute
construction's values vertex was void, so no shape statement has evidential standing yet. The
single edge that would begin to discriminate candidate shapes is finally runnable where a working
values construction exists. Confidence: the goal-process findings are one bad test away and
sim-only; the upstream conjecture is untested, logic only.

# Part II: The difficult third inference

## §4. Drives, values, and goals

The project's proposed ontology. Proposed, not standard reinforcement-learning vocabulary:

> Take value space and treat it as a **weighting on trajectories**. A goal would be a weighting of a
> specific policy plan – raising one action within that plan above the rest **temporarily, due to
> attention, under the constraint of context**.

> The actual value data you get is **sparse and error-prone**. So you end up needing as much
> information as possible to get as close to an accurate value mapping as we can.

(*"Weighting over trajectories"* over *"weighting over policies"* was his deliberate concession when
given the reason.) Under §1's table this reads as follows. Values are the standing organization; a
**current drive** is a state-dependent pressure; a **goal** is selected under values, drives,
instructions, and constraints, and can be imposed against all of them; and an **expressed trajectory
may misrepresent all three**. The four are distinct, and any measure that collapses them inherits
the collapse.

**State of the section's claim.** No row sits here because the fourfold distinction has never been
tested as a distinction; it is the file's working vocabulary, adopted for the reasons above. Its
first empirical bite arrives sideways, through §5's commission result, where an imposed goal
pursued without a drive reads differently from the same goal pursued with one, which is the
distinction between goal and drive doing observable work in the constructed world. Until real
artifacts show the same, this section rates as vocabulary with one simulated demonstration.
Confidence: untested, logic only, with the sim demonstration held by §5.

## §5. Where value information could live: four competing accounts

The file used to declare one of these the answer; they are candidates, and the constructed world
has begun discriminating among them.

**1. Amplification.** Values appear through which goals receive attention (§4's account read as an
instrument). **2. Conjunctive satisfaction.** Values are the constraint that every drive is
partially satisfied at once. *"Everything else before this felt like dithering to me, but this one
feels like it might be a real thing."* **3. Longitudinal residue.** Stable unoptimized habit
preserves value information:

> Drives would mostly be present through **long-term stochastic views of your behaviour**, as adjusted
> by local goals in proximal situations. And that by definition is **baked into your habits through
> automaticity, because they were habits. It's a record.**

> **Habit could preserve traces of persistent motivational organization.** But it's going to be
> messier than we expect. It's also going to preserve training, convenience, accident, and repeated
> attention-directed behavior as well. We'll have to extract that, and it makes it very error-prone.
> But we do have, baked into expertise, a record of past behavior through habits. **It's weak, but
> it's extractable.**

> **A candidate value signal is the cross-episode component of expertise-shaped behavior that is
> left after modeling the domain competence and each episode's proximal, attention-weighted goal.**
> It's a mouthful, but we have a picture, so it's fine.

> **It's noise. It looks like noise, but it's the noise of habit** – the habit that you have a record
> of because it's baked in alongside your expertise. **There it is. Those are your values**, after we
> can get rid of the rest of the noise in this signal. But humans do it, so it's definitely possible.

The residue account inverts the search. Every direct measure read the optimized part, where
selection has flattened the individual out, and *"the tail motivations are where you get the value
data specifically"*. The tail is where un-optimized residue lives, which makes re-reading (G64,
this section's table) the same bet from the other end. Repetition is the proposed carrier. *"The
way it's baked in implies that you've taken those actions many times, and therefore that itself is
information."* Its objection. The residual contains values **and** arbitrariness, and only a
domain-change test separates them. On epistemic foraging the position has moved from categorical
absence to weak baking:

> Some of the properties baked into habit alongside the expertise transition mapping will have
> useful properties. **Epistemic foraging is particularly high-variance behavior**, dependent upon
> context and previous information. **It resists repetition, and thus is baked in more weakly.**

The restatement absorbs the earlier objection from within. Strategies that recur, search order,
source selection, stopping rules, can still bake in, while targets vary with context and mostly do
not, so the foraging component of the residue is expected weak rather than absent, and the
domain-change separator carries the load either way. **4. Absence under commission.** A missing drive becomes
legible through *how* an imposed goal is pursued (the made-under-duress mechanism; the routing
consequence lives in [`ALIGNMENT.md`](ALIGNMENT.md) §0).

The constructed world's discrimination so far, method-validating and nothing more. Conjunctive
satisfaction read a profile from one constructed artifact where amplification could not; profiles
converged across artifacts; and an absent drive became recoverable under commission, with pure
compliance collapsing to exactly chance. **None of this is evidence that real human values have
been recovered.**

| # | hypothesis | status |
|---|---|---|
| **G54** | Conjunctive satisfaction: values constrain how all drives are jointly satisfied | **OPEN on real text; the account the constructed world favours.** It read a profile from one artifact where amplification could not |
| **G49** | Longitudinal residue: values live in the un-optimized residual of expertise | **OPEN.** Requires a model of what a domain's expertise is optimized for; carries the habit-shadow and foraging-strategy confounds. Per the program it runs **last**, behind choice recovery, expertise separation, and a transferring remainder |
| **G50** | The value-carrying residual is what survives a domain change | **OPEN.** The only proposed separator of value from arbitrariness |
| **G51** | Repetition itself carries the weighting | **OPEN** |
| **G64** | Re-reading one artifact recovers the tail | **OPEN.** The residue account's other end; the reader-side strategy is `READER_HEURISTICS.md` §4's |
| **S-14** | An absent drive is recoverable | **SUPPORTED (sim) as method; OPEN on real artifacts.** Near-invisible spontaneous (0.61), perfect under commission (1.00), compliance collapses to exactly 0.5; *how the goal is pursued* discriminates |

**State of the section's claim.** Four accounts stand, none dead, one favoured, and the favourite
was a surprise, since the section's original headline account (residue) now runs last by the
program's own sequencing while conjunctive satisfaction, the account he flagged as the first
non-dithering idea, is the one the constructed world discriminates toward. The residue account
itself now stands in its restated, weaker form, a candidate value signal defined as the
cross-episode remainder after modeling domain competence and each episode's attention-weighted
goal, expected messy because habit also records training, convenience, accident, and repeated
attention. The absence mechanism is the section's cleanest result anywhere, reading a *missing*
drive through pursuit style at sim-perfect strength under commission. Every one of these remains
a claim about constructed worlds; no real maker's values have been read by any account.
Confidence: the sim discriminations are sim-only, authoritative about method; all four accounts
are untested on real text.

## §6. Value blindness, and where longitudinal ground truth could come from

Self-report is closed as ground truth, and the reason is not modesty:

> You always have an imperfect view of anyone else's value set, and your own introspective and
> interoceptive access is **systematically limited and biased.**
> It's why artists will make art and look at it – in part to get a sense of their own values. They
> learn about themselves through that expression.
>
> Anything I say, anything I make will be over-indexed and automatically full of error, because it
> will be **my view of my own value set.**

If values were introspectively available, art would not be one of the ways people discover them.
Under the residue account the limited access is a *prediction*, since automaticity put the values
where introspection reaches poorly. This kills the author-a-value-set-and-generate design class. One
artifact is insufficient for the same identifiability reason a reward function needs many episodes;
**diversity of conditions** is what separates value from arbitrary residue; and *everything is an
artifact* extends the observation set:

> **Everything's an artifact. Even information about their life.** Any action they took that affected
> the world counts. [...] You will use **epistemic foraging** to find more things out about the artist
> if you want to.

Any behavior or persistent world trace becomes an observation, rated the way any observation is,
through provenance, context, and reliability assessment. And self-report joins the same pile
rather than sitting above it:

> **Biology is no more ground truth of internal state than the word of a museum curator.** It's just
> binary sensory inputs weighted differently.

*"You're responding to their sound waves and it's the same maths."* The corpus that would supply
ground truth is makers deliberately aligned to a **declared value tradition**, read through **deep
followers**, with religious traditions one instance of the design rather than the design itself:

> Religion is probably the strongest force for value alignment I can think of in the world. It does
> curiously suggest you'd be able to **extract someone's religion from their words.** [...] That's
> such a messy test. It's also straight trash as academic work.

> The key part has **little to do with the work itself**, and more to do with **deep followers** of
> that work. And then aligning that with the specific values that have **spread out from** that work.
> We'll have to analyse the work **and** the followers.

> We'll be able to identify a testing bed as **graded adherence to a declared value tradition**, and
> then try to lexically extract that for ourselves using the same human empathic process. Trying to
> figure out if we can **predict patterns of uptake or adherence specifically through behavior.**

The design's prize is a **gradient of adherence, a ladder made of humans**, with topic held
constant by construction (the same practical question answered from within different traditions),
and the honest objections kept. Canon formation selects, translation and era confound, and declared
values are not held values, which is tolerable because the label needed is what an artifact was
made *under*, not what the maker truly valued. Sourcing detail and procedure live in `TODO.md`;
the blocking rows stay below.

| # | hypothesis | status |
|---|---|---|
| **S-15** | Value-profile recovery converges with artifacts, residual priced | **SUPPORTED (sim).** 0.53 → 0.98 over 1 to 50 artifacts, residual 0.009; bounded-family assumption worth 0.24; **corpus price ~20 works per maker**; conjunctive-vs-amplification discriminates constructions |
| **G60** | Recovery error shrinks with works, toward a small residual | **EARLY PLATEAU (test, L34), one channel (relabelled 2026-08-09).** 0.54 → 0.61 → 0.60 against 0.20 chance over one-to-three reference works. Rises from one to two works and not at three, on five authors and the cheapest channel. Three points cannot locate an asymptote, so the limit-framing reading this row used to carry was unlicensed |
| **G48** | A maker's weighting is more stable within than between makers | **OPEN.** The 34-book corpus supports the design, and per the program another stable author vector would be circular without behavioral tradeoffs; G135's held-out tradeoff prediction is the honest form |
| **G65** | Value recovery improves sharply with works per maker while goal recovery does not | **OPEN.** The follower-corpus design tests this and G48 at once |
| **G66** | Adherence to a declared value tradition is recoverable as a graded quantity | **OPEN.** A ladder made of humans; the honest output is predicted patterns of uptake or adherence from behavior; blocked on sourcing |

**State of the section's claim.** The longitudinal requirement is the best-motivated unmet need in
the file. The limited-access argument closes self-report as ground truth while demoting nothing
else, since every trace, biology and testimony included, enters as an observation rated for
provenance and reliability, the simulation prices the corpus at roughly
twenty works per maker with convergence to a small residual, and the one real-text curve rises
then plateaus early in a single cheap identity channel that cannot speak to an asymptote. What is
missing is not motivation but material, since every open row waits on either the follower corpus
or a tradeoff design that no public corpus supplies, which is why the program routes this through
a commissioned pilot rather than more corpus hunting. Confidence: the convergence pricing is
sim-only; the plateau curve is one bad test away; the corpus rows are untested and blocked.

# Part III: Epistemic limits and evidence

## §7. Identifiability, not impossibility

**This is where the project disagrees with the literature, and it is not to be narrowed.**

> Saying something isn't possible just means you haven't found the way to do it yet – **especially if
> the world is doing it.**

His correction of my own overclaim ("humans do this, therefore it can be done"):

> I'm not saying humans arrive at a conclusion of value. I'm saying they use **a bunch of tricks to
> actively try to get closer** to it.
>
> **It's a limit situation.** You get closer and closer over time. There *is* a solution – a perfect
> mapping of the person's brain – but we approach it **through inference with error**, and we are
> never sure we have the answer.

> I need to concede that I'm not claiming at this point that convergence is possible, but rather
> that **substantive human priors can produce a more useful narrowing.**

> Behavior that looks irrational under simple reward models can instead be **evidence of cognitively
> bounded agents with multiple, changing, and nested motivations**, expressed through a variable
> possibility space of context-sensitive expertise.

The theorems are real. A policy cannot uniquely identify both a reward function and an unknown
planning algorithm, even with unlimited data; additional normative assumptions are required
(Armstrong & Mindermann). The project's response, stated carefully. **Human readers use substantive
priors about human bodies, competence, contexts, and communicative behaviour that may improve
useful recovery without producing unique identification. That is a narrowing claim, not a
refutation of the theorem, and the stronger convergence form is conceded above.** The priors line
up with what the proofs demand:

| what the proof needs | what he already assumes | his name for it |
|---|---|---|
| a bounded hypothesis space | human-shaped goals | **convergent midbrains** |
| a known transition model | expertise | *"the transition model is just expertise"* |
| a rationality / optimality principle | near-optimality | *"that's just MaxEnt"* |

> *"Oh my god, it's my three assumptions."*

The two unknowns the proofs call fatal are one quantity here, since *"the maker's competence is
their expertise"*, and it is a quantity this project claims is partially recoverable. A fourth
candidate constraint is communicative intent:

> **CIRL literature makes it easier for you to learn if you assume you have a teacher**, assuming that
> teacher exists and helps. **You can assume intention to help from the evidence.**

The same cooperative-intent framing has an adversarial use. Propaganda, seduction, and obligation
are the counter cases, structure placed so that the reader takes an incorrect model away from the
artifact, which is why the prior is adoptable only conditionally. It is canonical in
[`READER_HEURISTICS.md`](READER_HEURISTICS.md) (stated in its §1, tested in its §8) with the
concealment caveat carried there; here it is one identifiability assumption among four.

| # | hypothesis | status |
|---|---|---|
| **lit** | A reward function is not identifiable from one episode | **SUPPORTED (READ).** Amin, Jiang & Singh state the decomposition and the consequence |
| **lit** | Recovery stays impossible with unlimited episodes | **CONTESTED (READ).** Armstrong & Mindermann and successors prove partial identifiability persists; we dispute that their conditions describe a human reading a human artifact, as a convergence claim |
| **G61** | An explicit competence estimate improves goal recovery | **OPEN.** If yes, the "fatal unknown" is an input |
| **G138** | The impossibility construction, reproduced exactly, then relaxed with the three human priors one at a time | **RECREATED+NARROWS (test-side toy, L60).** The degeneracy reproduced at exactly 0.5/0.5; the bounded human-shaped family alone narrows the posterior twentyfold, known near-optimality alone barely doubles it, both together fortyfold, holding under noise. Convergence without unique identification, at toy scale, with the seven-state world as the loud caveat |

**State of the section's claim.** The position now has its first number and the number behaves.
The theorems are conceded as theorems, reproduced here to the digit, and the disagreement's
content, that substantive human priors buy useful narrowing without unique identification, is
what the toy shows, with posterior mass rising fortyfold under the combined priors while staying
far from certainty. The ordering inside the result sharpens the position, since the bounded
hypothesis family carries most of the effect and near-optimality pays only after boundedness,
which makes "convergent midbrains" the assumption the whole response leans on hardest. A
seven-state chain is not a maker reading an artifact; the gridworld substrate and G61's cheap
real-model test are where this either grows or dies. Confidence: the literature reading is
replicated in its sources; the narrowing result is one bad test away, one toy world deep.

## §8. Scope and boundaries

**Human empathy is the motivating phenomenon, not an established synonym.** *Empathy* carries 43
catalogued definitions, which is why the mechanism is named for what it does. **Accurate attribution
is not caring.** Nothing in this file bears on motivation to protect, which is
[`ALIGNMENT.md`](ALIGNMENT.md)'s problem. **A model can reconstruct without experiencing**, the
architecture file's bridge. **And value recovery is posterior narrowing, not mind duplication**:

> My personal end goal is to find a way to **give AI human empathy, but not human emotions**
> [...] it requires some kind of subordinate solution space that converges on these **predictions of
> these interoceptive signals.**

Against Dennett's stance that prediction never licenses identification: *"It's a question of limit.
We're doing a Taylor series approximation, increasing precision based on Bayesian updating.
Eventually, hypothetically, the only way to do it fully would be to hold someone else entirely in
your mind."* A statable position in the intentionalism debate that answers Wimsatt & Beardsley
rather than conceding to them, and it has never been written up as such.
