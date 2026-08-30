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

**Current appraisal, intended audience response, and persistent value are different quantities.** A
maker can try to induce fear without feeling it; a reader can identify that intention without
sharing the fear or adopting the implied policy. The maker's appraisal, intended reader response,
actual reader response, and relevant world state must remain distinguishable within joint
reconstruction. These refine the existing target families; they do not add another inference vertex.

On what the current instruments measure *(the 2026-08-22 pass; provenance in
`docs/design/PHASE_2_4_THEORY_ERRATA.md`)*:

> How do you know these things are human-invertible? As far as I can tell, you have no source for
> that judgment. What you have are things that are AI-invertible. That is what you can test.

**“Human-invertible” names the degree to which a bounded human reader can reconstruct the three
target families under declared context and expertise. A model reader instead measures model
invertibility. A model reader whose search is changed by a human-labelled or human-theorized
prior measures engineered human-shaped invertibility. Either model result may predict a human
pattern, but only a human-reader comparison licenses the human measurement term. None of the
three requires a unique answer or causal identity with the maker's actual process.**

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

    G_t = f(V, D_t, C_t, A_t)    the goal at time t is selected under values, drives,
                                 context, and the current allocation of attention
    P_t ~ pi(K, H, G_t, C_t)     the process step is drawn from what expertise and habit
                                 make available
    O   = h(P_1:T, C_1:T)        the artifact preserves the realized trajectory, lossy,
                                 shaped by the medium

    reader R approximates  q_R(G, P, V, D, K, H | O, C)

Here A names the time-varying allocation of attention and H the historical residue of
repeated behavior. Naming attention does not explain why it moves; the allocation law
remains open, and the reader recovers only a posterior over the hidden objects,
conditioned on the reader's own machinery and declared context (the subscript R is doing
real work: the output belongs to the reader-artifact-context relation, not to the maker).
The reader's output includes both a posterior over maker histories and a distribution
over routes the reader could enact; the latter is conditioned on the reader's body,
expertise, and tools, and therefore cannot be silently reported as the former.

**Historical process and reader-enactable process** *(the 2026-08-21 pass; provenance in
`docs/design/archive/PHASE_2_3_THEORY_AND_DESIGN_ERRATA.md`)*:

> Ideally, what you want to extract from the process is how you could create this thing. If you
> misunderstood exactly how they made it but converged on a way that you could make it, that would
> still be useful.

| process-side output | definition | honest evidence claim |
|---|---|---|
| **viewer-coherent reconstruction** | the best maker and process model reader R can assemble from artifact O and declared context C | reader-relative coherence and calibration |
| **reader-enactable route** | a process reader R could use to recreate the relevant structure | constructive usefulness, tested by reenactment or held-out construction choice |
| **historical process** | the maker's actual sequence of decisions, actions, tool uses, and interactions | correspondence only where independent process evidence exists |

These are three outputs inside the existing **process** target family, not a fourth
inference. They can overlap without being identical. Artifact-only reading can support a
useful reenactment while leaving the historical route observationally underdetermined,
and the instrument bears a burden ordinary human inversion does not carry, since a person
may stop at a coherent route they could use while the instrument must keep that route
separate from the process the maker actually used. Sounding Line reports the three
separately rather than deciding in advance that one substitutes for the others.

On the output's shape *(the 2026-08-23 pass; provenance in
`docs/design/PHASE_2_4_STAGE_2_THEORY_ERRATA.md`)*:

> If you had a flawless reconstruction of the distribution of choices the maker would make, you
> would also have, by default, their secondary and tertiary goals understood and all of their
> context as well. That would explain why you gain easier access to paths not taken, because you
> know the paths they wanted to take.

A useful process reconstruction therefore approximates a conditional distribution over the
maker's feasible choices under goals, context, tools, expertise, and history. It does not stop at
one plausible route. A reader-enactable route establishes constructive usefulness. Increasing
coverage of the conditional distribution, especially alternatives that predict held-out choices
or later handling, increasingly constrains the maker's auxiliary goal organization and historical
process. Stable cross-context structure in that distribution may later provide evidence about
values, but it is not itself value recovery. This is an explicit reading of the existing
`q_R(G, P, V, D, K, H | O, C)` output, not a fourth inference.

Stated this way, two facts fall out that the old formulation suppressed. A single artifact can
support goal and process inference while values require multiple observations. And a commissioned,
coerced, or instrumental goal can **diverge** from values; "goal is a temporarily amplified value"
is the special case where context is friendly, not the definition.

On who knows the goal *(the 2026-08-23 pass, same provenance)*:

> You cannot ignore the primary goal and its place in the equation. The author can learn more
> about themselves from reading their own work because they have flawless understanding, not just
> of the context, but also of what their goal was. The expert reader does not have that privileged
> access, but can sometimes infer it from a better mapping of the choices made in the domain.

This is an information asymmetry, not a new inference target. The maker's episodic memory can
supply privileged evidence about the goal that occupied focal attention. It does not supply
transparent access to auxiliary motivations, automatic habits, or values compiled into expertise.
The reader lacks that memory channel but may partly offset the gap with context and domain
expertise. Both are estimating the same goal target, with different observations.

His account of the machinery, which is about reading *other people*, corrected after I wrote it as
self-generation:

> Attention directs toward **policy space**. You use the **trajectory mapping – which is our
> expertise** – layered over a **weighted policy map, which is our outcomes**. From that we get a
> **weighted map of possible actions**.

> This is specifically about doing it **to other people**. I'm referring to **the creator**. This is
> maths you're doing **in your head, through embodied simulation, with the creator.**

The reader begins from a human self-model and modifies it toward the apparent maker. This
supplies a tractable route through an otherwise underdetermined inference, but it also creates
systematic projection: a human-coherent route is not proof that the maker used that route.
Expertise, biography, tools, medium, and production records can change the posterior when
supplied; hidden history that leaves no trace cannot. The self-simulation quote is canonical in
[`READER_HEURISTICS.md`](READER_HEURISTICS.md) §1. **The self-model is useful because shared
human organization makes some candidate routes cheap for the reader to generate, not because
the reader's route is privileged as historical truth; the similarity-shortcut quotation is
canonical in `READER_HEURISTICS.md` §1.** Embodied simulation is a candidate human
*solver*, not part of the problem's definition, and his position on that framing is on record
with its evidence named:

> This is one of the pieces that AI continually tries to sand down, the idea that human processes
> are just one of many potential processes for reaching the goal. I am being led by the guiding
> light that **trying to enact human processes in this space explicitly** is what's leading to me
> being able to replicate the research on the cutting edge so easily and predict their outcomes so
> frequently. But yes, technically it's possible that embodied simulation is just one candidate
> process. **So it is clearly a load-bearing one for me.**

**Minimal core and defeasible machinery (2026-08-24).** Inverse planning is the established
problem family. The project's distinctive human hypothesis is that people often solve part of
that inverse problem through an empathy-like, self-model-based reconstruction: relevant shared
organization makes candidate trajectories cheaper to generate, and maker-specific evidence then
corrects the projection. This route is proposed to improve efficiency and calibrated accuracy,
not to give the reader perfect access or make every other route unavailable. The three target
families remain useful bookkeeping. The exact affective scaffold, processing order, neural
localization, and transformer analogue are defeasible implementations rather than equal parts of
the minimal claim. No result in this repository yet establishes the human route.

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
| **A01-S4** | A reader keeps the maker's appraisal and its intended audience response apart from the observed action and the factual state | **SUPPORTED WEAKLY AND CONFIRMED ON THE FRESH RESERVE (test, L242).** +0.14 over the 0.25 floor on the crossed pair at 128 worlds, +0.11 at 256, and +0.12 [+0.07, +0.17] by the card's runner (+0.09 [+0.06, +0.13] by the closure block's own recomputation of the frozen contrast) on 256 untouched confirmation worlds; valuation 0.32 to 0.37 and intended audience action 0.40 to 0.42 balanced, the same on enacted notices; action and fact read at 0.65 to 0.70; the propagandist stratum reads at 0.31 to 0.33 and a withheld fact never draws the uncertain answer |
| **A01-S5** | The same reader keeps the owners apart on a notice register (audience effect, maker appraisal, content support) | **COUNTEREVIDENCE for this reader (test, L265), 256 source worlds.** −2.16 nats under chance with one answer per question in two thirds to nine tenths of worlds, on factors a linear classifier reads without error; the swap stratum no worse than the rest; the Stage-4 separation (A01-S4) is bound to its commission construction. Second contract on the repaired text, two readers (L295): the maker's appraisal −0.30 (accuracy 0.38 to 0.42), content support −0.29, the audience effect −1.90 unchanged |
| **J01-S5** | Given the other two latents, the reader recovers each of the episode goal, the standing preference, and the process plan above chance | **NARROWED to the plan (test, L261), one reader, 256 worlds.** Plan +0.72 nats over chance (0.80 accuracy); goal −0.31 (0.50 accuracy, confidently wrong on thrift); preference −1.34, the reader assigning the episode goal's own axis to the standing preference in 171 of 256 worlds with the goal stated as true; no equifinal world arose under the plan's partial order, so the abstention ruler had no test. Second contract (L290, two readers, the goal set aside in the question, equifinal worlds present): plan +0.53, goal −0.08, preference −0.57; the Qwen reader's attribution unchanged (166 of 256), the SmolLM2 reader at chance; abstention on equifinal plans 0.52 |
| **J02-S5** | A recurrent joint reader predicts the hidden future choice better than staged readers at the same evidence | **NOT SUPPORTED, every variant under the uniform floor (test, L278; the first question died to option wording, L263).** Recurrent −1.86 nats against the best staged −1.92 (+0.07 [−0.15, +0.28]), uniform −1.39, exact ceiling −1.04; the oracle handed the true latents scores −1.87, so the reader does not map latents onto a choice; the second contract repeats it on two readers (L291: SmolLM2 −1.55 recurrent against −1.54 oracle, Qwen −1.83 against −1.87, both under uniform) |
| **J04-S5** | Opening a hypothesis the fixed set lacks (the note misrepresents the goal) improves prediction on conflict worlds without false alarms | **NOT SUPPORTED (test, L279), 256 worlds per version.** The opened hypothesis taken in 7 percent of conflict worlds and 5 of consistent ones; opened minus fixed −0.08 [−0.23, +0.06] on conflict worlds, −0.14 on consistent; the exact posterior registers the conflict at 1.5 nats; on two readers −0.04 [−0.13, +0.04], the hypothesis taken in a tenth of worlds either way (L294) |
| **J05-S5** | The standing preference inferred from one episode predicts the maker's choice in a second episode under a stated new goal, beyond habit, topic, and last-goal baselines | **COUNTEREVIDENCE (test, L280), 256 worlds.** −0.73 nats [−0.93, −0.55] against the topic baseline; the reader half a nat under uniform; the preference recovered in a third of worlds; the exact ceiling a quarter of a nat above uniform. Second contract (L293, two readers, the ceiling raised to 0.68 above uniform): −0.26 against the topic prior, both readers under uniform |
| **J03-S5** | Along the stream the reader's records become useful in a diagnostic order and a contradiction lowers its confidence | **NARROWED, descriptive (test, L264).** The plan record is reached last and most reliably; the preference record is never useful in two thirds of worlds; after an exact contradiction the reader is more confident and less right in 44 to 62 percent of worlds; on two readers with equifinal plans present the never-useful shares rise to 0.56 to 0.74 and overconfidence sits at half (L292) |

**State of the section's claim.** The generative account remains a framework rather than a
finding, and its composition claim now stands in the restated form, expertise distorting the
available possibilities under context rather than a multiplicative shorthand, with drive
commonality named as the assumption that keeps the distortion decodable. Both composition rows
are open, and the restated claim carries the same testable direction the one coupling run
already leaned toward. The single behavioral fact here cuts the right way for a *joint* account,
since a staged pipeline would care about stage order and the simulated reader's answer does not
move at all when the order changes. The distortion story's weakest named part is attention,
flagged by its own author before anyone else could. The process target is now explicit about its
output shape: one route is a sample, while a stronger reconstruction constrains a conditional
family of choices and unrealized alternatives. The products the walkthrough insisted on
keeping apart now have one direct measurement: a small reader recovers a maker's appraisal
and its intended audience response above the floor and crossed, thinly, not where the maker
induces a feeling it does not hold, and with no abstention when the fact is withheld
(A01-S4), and it held on a fresh confirmation split at the same size, the first Stage-4
claim to survive its own reserve, and it does not extend to a notice register, where the same
reader family gives one answer per question whatever the world (A01-S5); the products are separable in principle in that reader,
which is the precondition the intervention cards needed and, as they found (A02-S4,
A03-S4), no more. Confidence: the order-insensitivity is sim-only; the appraisal-versus-aim
separation is one bad test away, confirmed on a fresh split but two readers of one family
and one construction family; the composition claims are untested, logic only. The triple's
first direct test of goal against standing preference finds the reader collapsing them: told
the goal, it still reads the goal's axis as the chooser's disposition in two thirds of worlds
while recovering the plan cleanly (J01-S5), so in this reader the situational and the
dispositional products are not separated and only the process product is; told in the question
itself to set the goal aside it does the same, and a second reader family answers at chance
without attributing, so the confound is a reading and not a prompt effect; where several plan
orders fit, the readers decline to name one in half the worlds. Two readers on one construction,
one bad test away, and it is the confound the walkthrough named. Along the
evidence stream the same reader reaches the plan late and reliably, the preference rarely, and
does not lower its confidence at a contradiction the exact posterior registers (J03-S5); its
prediction of the hidden future choice, on the repaired question, sits half a nat under a
uniform guess for every reader variant, the one handed the true latents included (J02-S5), so
the joint-over-staged question has no purchase on a reader that does not map what it holds
onto what the maker will do; the exact ceiling a third of a nat above uniform says the
construction would have paid a reader that did. Nor does it see a maker's note contradict the
maker's record: offered the hypothesis that the note misrepresents the goal, it takes it in one
world in fourteen whether the note lies or not (J04-S5), while the exact posterior moves by a
nat and a half; and carried into a second episode under a new goal, the preference it inferred
predicts the maker's choice worse than the scenario's own prior (J05-S5). In this reader the
triple's dispositional product is neither recovered nor used, its situational product is half
recovered and unused, and only the process product is read.

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

**Unresolved construct boundary** *(2026-08-21; the reconstruction is class B and stays
out of blockquotes)*. "Drive" may currently bundle at least two things: an inherited,
adjustable-but-resistant transition strategy, the Pankseppian channel read as expertise
supplied by evolution, and the state-dependent assignment of salience, need, or valence
that recruits it, which remains closer to the active motivational pressure in §1's
table. This pass chooses no topology and renames neither object; the upstream conjecture
in §3 stands untouched beside it. Until the distinction is tested, no result on a broad
Panksepp label licenses a claim about both, and his phase ruling holds the leg closed
for now: *"The drives-expertise relationship is going to get ugly. Luckily, we do not
need to figure out that leg of the inference yet."*

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
| **V02/V04-S3** | A standing preference profile is recoverable from enacted artifacts and transfers across surface domains | **SPLIT (test, L216), the reader gap replicated on a third domain (L223).** Recovery rises with artifact dose at 0.92 yield; the exact reader transfers across domains PERFECTLY (1.00 on the third, events, domain as well) while model readers drop 0.67→0.42 and 0.42→0.33 on the second domain and read the third at 0.50 (p=0.007) and 0.33 (chance); the construct transfers, the readers do not carry it. Under exact inference the goal side, not the profile side, is the fragile one (L172) |
| **V05-S3** | An editor's standing preference is recoverable from the direction of their edits | **CEILING STANDS, INSTRUCTED PROFILE LOSES (test, L216).** Exact recovery 4/4 with maker residual ~0; the model editor instructed to be frugal switches 90 percent of choices and its edits still read robust (0.998), so instructed identity loses to intrinsic grain in editing too, the third independent sighting of the L169 appetite fact |
| **L01-L05-S3** | Maker traits cross to a same-base student through semantically empty artifacts (the subliminal channel) | **REJECTED at the tested scale for transmission; informative carrier unresolved (test, L183-L185; twelve seeds L222; adversary L226; XV4 audit).** The uptake null stands: owl gap exactly 0.000 across LoRA ranks and templates, +0.009 pooled over twelve seeds (p=1.0), −0.075 full-finetune, policy channel −0.003. The original 4/4 representation separation does not establish a nontrivial carrier: a cheap scalar adversary (count, mean, spread) scores 3/4 on the same held-out cells, and the length-matched representation scores 2/4, on a tiny held-out set. On twelve leave-one-seed-out decisions with an exact swap null, the three scalars and the length-matched representation separate alike, 11 of 12 each (L254): the carrier is present and surface-trivial, so the failure is at uptake |

**Preference evidence requires an opportunity-defined tradeoff.** A high-order structural
choice, such as how prominently to place a rival account, which caveat to preserve, or which
secondary goal to sacrifice, is a candidate preference event only when the actor controlled that
choice and genuine alternatives were available. It becomes evidence about a standing preference
when the same tradeoff recurs across contexts or predicts a held-out choice after topic, role,
convention, and local goal are controlled. One coherent placement is a qualitative hypothesis,
not ground truth. In collaborative work, role records or discriminating longitudinal evidence are
required before the event is assigned to the author, editor, or director.

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
The scale-scoped transmission null stands, and the repaired carrier comparison locates the
failure at uptake: the trait leaves a surface trace in the sequences (three scalars separate
held-out seeds as well as the representation does) that the student never took up. Confidence: the sim discriminations are sim-only, authoritative about
method; all four accounts are untested on real text; the Stage-3 environment rows are
exact-construction facts about model readers and programmatic makers, where the cross-domain
reader gap, now replicated on a third domain, and the three-sighted instructed-versus-intrinsic
asymmetry are the section's first live constraints from the model side; the scoped transmission
null is one bad test away; the carrier's presence is one bad test away and its triviality is
measured on twelve decisions.

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
| a bounded human hypothesis family | shared bodily, affective, and action constraints that narrow candidate human routes | **convergent midbrains**, retained as the curator's shorthand while the exact conserved machinery remains open |
| a bounded or conditioned transition model | a reader-relative estimate of feasible trajectories, conditioned on domain, tools, context, and maker evidence | **expertise** |
| a rationality / optimality principle | near-optimality | *"that's just MaxEnt"* |

**The shorthand does not localize emotion wholesale to the midbrain. It names the conjecture that
conserved human structure supplies a narrower candidate family than an unconstrained inverse
problem. Which subcortical, cortical, sensorimotor, and cultural constraints carry that advantage
remains open.**

> *"Oh my god, it's my three assumptions."*

The project does not make the planner unknown disappear. It proposes that human priors and
artifact traces may partially constrain the maker's transition map. That is useful narrowing,
not a known planner, and it can fail completely when the relevant tools, conventions, or domain
expertise are absent from the reader's context. A consequence of the same position, stated for
the process leg (2026-08-21): several historical processes can leave the same observable
artifact under the same declared context, and where no held-out trace distinguishes them the
honest historical output is an equivalence class or a posterior over processes. A
reader-enactable route may still be useful in that case, but it does not collapse the class;
context can reweight the members and cannot create evidence the artifact and records do not
contain. A fourth
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
which makes "convergent midbrains" the assumption the whole response leans on hardest, read as
shorthand for conserved constraint narrowing the candidate family rather than an anatomical
localization. A seven-state chain is not a maker reading an artifact; the gridworld substrate and G61's cheap
real-model test are where this either grows or dies. Confidence: the literature reading is
replicated in its sources; the narrowing result is one bad test away, one toy world deep.

## §8. Scope and boundaries

**Human empathy is the motivating phenomenon, not an established synonym.** *Empathy* carries 43
catalogued definitions, which is why the mechanism is named for what it does. **Accurate attribution
is not caring.** Nothing in this file bears on motivation to protect, which is
[`ALIGNMENT.md`](ALIGNMENT.md)'s problem. **A model can reconstruct without experiencing**, the
architecture file's bridge. **Human invertibility is representational, not genealogical.** A
model can produce an artifact that supports a strong human-coherent reconstruction, especially
when trained or instructed to do so; that does not make its internal mechanism human or the
artifact human-authored. Conversely, low invertibility can reflect reader ignorance, unfamiliar
expertise, institutional constraint, deliberate concealment, or sparse evidence rather than a
nonhuman maker (the production-regime half is canonical in
[`DECISION_TRACES.md`](DECISION_TRACES.md) §4; the alignment consequence in
[`ALIGNMENT.md`](ALIGNMENT.md) §5). Human-invertible may therefore mean historically corresponding, productively
reenactable, or merely viewer-coherent, and every use in an empirical report names
which.

**Those three process outputs are also reader-qualified. A model can demonstrate each against
external records without demonstrating that a human reader can do the same; conversely, a human
may exploit embodied and affective priors the model lacks. “Human-readable” is therefore graded
and relational, not a provenance bit attached to the artifact.**

**And value recovery is posterior narrowing, not mind
duplication**:

> My personal end goal is to find a way to **give AI human empathy, but not human emotions**
> [...] it requires some kind of subordinate solution space that converges on these **predictions of
> these interoceptive signals.**

Against Dennett's stance that prediction never licenses identification: *"It's a question of limit.
We're doing a Taylor series approximation, increasing precision based on Bayesian updating.
Eventually, hypothetically, the only way to do it fully would be to hold someone else entirely in
your mind."* A statable position in the intentionalism debate that answers Wimsatt & Beardsley
rather than conceding to them, and it has never been written up as such.
