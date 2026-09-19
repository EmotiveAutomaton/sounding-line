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

**Operational definition, ratified 2026-09-01.** Sounding Line is an artifact-grounded
inverse-generative system that reconstructs a revisable model of how a maker transformed their
perceived possibilities into an artifact, then tests that reconstruction through hidden future
and counterfactual behavior. This is ratified project language, not a result claim.

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
2026-08-10, his instruction)*; sources are (test) measurements here, (sim) the parent simulation, and (lit) published
work, with substrate and reader stated separately as required by the folder README.

---

# Part I: The inference problem

## §1. The three target families

**Superseded:** the earlier formulation called these three separate variational
inference problems. The opening curator restatement instead names three constrained
target families at different timescales; it preserves mutual constraint without requiring
three separate algorithms.

> This is why an expert can more readily understand what a novice was thinking as they were making
> something, in a way that another person cannot. This is why being close friends with someone, you
> can read their book and get more of a sense of why they made certain choices. **This is why
> information is passed more easily between people who are close.**

> You can arrive with expertise already, and you can arrive with strong knowledge of who the maker
> is and what they want. The one thing you have to infer on the spot is the proximal goal, and it is
> usually the easiest inference to make.

*2026-09-01 walkthrough; spoken wording lightly reconstructed.*

> To recreate, you have to have flawless knowledge of the maker, their context, their process, and
> their expertise. Expertise is the largest part of the ability to recreate, not the whole of it. It
> is the shared language that allows people to communicate complex ideas quickly.

*2026-09-04 walkthrough; lightly cleaned transcript.*

Expertise is therefore the largest part of the ability to recreate and never the whole of it: the
shared language of a domain, which is what lets a reader run the domain's standard process against
the artifact at all. The current claim for the expert and friend cases is deliberately modest. Domain expertise and
maker familiarity are possible priors a reader may bring, **priors and entry points that may
improve recovery**, never guaranteed recovery, and the closeness prior itself is untested (G59,
canonical in [`READER_HEURISTICS.md`](READER_HEURISTICS.md) §1). What must be inferred on the
spot is the proximal goal, and the realized process remains episode-specific even when useful
expertise is already present.

Translated into objects, before any claims about their shape:

| object | canonical meaning | timescale |
|---|---|---|
| **proximal goal** `G` | the governing purpose of the artifact or declared episode; distinct from the subordinate target currently in attention | artifact or episode scale; often maintained during production |
| **process** `P`, realized as `tau` | the particular decisions and actions that produced the artifact | artifact-local |
| **expertise** `K` | the maker's learned transition model, shaping reachable actions and expected consequences; the shared language of a domain; the largest part, never the whole, of the ability to recreate | cross-episode, domain-relative |
| **drives** `D` | currently active motivational pressures or primitive constraints | state-dependent |
| **values** `V` | persistent organization of tradeoffs among goals, drives, and trajectories | longitudinal |
| **external context** `C_ext` | commission, coercion, medium, audience, tools, and objective constraints | episode-local |
| **maker beliefs** `B` | information the maker possessed and what they believed | episode-local, history-shaped |
| **maker context** `C_m` | external context interpreted through the maker's beliefs and expertise | episode-local |
| **subjective action set** `A_tilde` | alternatives the maker believed were available after context and expertise shaped the possibility space | step-local |

> Sounding Line has to infer the information the maker possessed and believed, and the actions they
> thought were available. Those belong in the maker model: external context as transformed through
> the maker's beliefs and expertise.

*2026-09-01 walkthrough; spoken wording lightly reconstructed.*

Three conflations this table dissolves. **Expertise is not process.** Expertise is the maker's
learned transition model, the map of which actions are reachable and what they are expected to
do; process is one realized path through it, and results about one do not automatically transfer
to the other. **External context is not maker-interpreted context.** The commission, medium,
audience, tools, and objective constraints are one thing; the situation as the maker perceived it
through their beliefs and expertise is another, and an objectively available action was not
necessarily available to the maker. **Drives are not values.** Drives may be inputs to action
selection; values describe their persistent organization. Treating any of these pairs as synonyms
is why a vertex of this file has repeatedly appeared and disappeared.
Where his quotes say "values/drives" as one item, the prose keeps them split.

**Current appraisal, intended audience response, and persistent value are different quantities.** A
maker can try to induce fear without feeling it; a reader can identify that intention without
sharing the fear or adopting the implied policy. The maker's appraisal, intended reader response,
actual reader response, and relevant world state must remain distinguishable within joint
reconstruction. These refine the existing target families; they do not add another inference vertex.

On what the current instruments measure *(the 2026-08-22 pass)*:

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
| **L-tier2** | Diverse episodes can narrow persistent motivational organization; the relative evidence needs of goal and value recovery remain to be measured | **OPEN for human value recovery and the relative-timescale comparison.** The author-identification curve measures identity, not values (test, L34; G60). Bounded constructed profiles can be recoverable from one artifact or from repeated artifacts (§5 G54; §6 S-15); these are construction-specific results, not human value ground truth. G65 remains the open comparison |

**State of the section's claim.** The object table fixes the working distinctions among
expertise and process, external and interpreted context, drives and values, and governing
purpose and focal subgoals. These definitions do not establish recoverability. Repeated,
diverse episodes are a proposed source of leverage on persistent motivational organization;
no clean comparison here shows that human values require a particular number of artifacts
or that goals require only one (L-tier2, G65). The measured real-text curve is a small
identity-channel improvement followed by an early plateau (G60, L34). Constructed profile
recovery establishes what can be recovered under its planted assumptions, not recovery of
human values. Domain competence and familiarity remain candidate priors. Stage 8 passed
its prediction component and failed generation, admitting no reader; it did not establish
the complete proposed expertise prerequisite. Confidence: untested, logic only for the
human recovery and relative-timescale claims; one bad test away for the scoped identity
curve and constructed demonstrations.

## §2. Forward generation and inverse recovery

What the maker generates, what the artifact preserves, and what the reader reconstructs are three
different things, and the theory has to keep them apart. A minimal generative account, held loosely:

    C_m,t = phi(C_ext,t, B_t, K_t)       maker-interpreted context
    A_tilde,t = afford(C_m,t, B_t, K_t)  actions the maker believes are available
    G_t = f(V, D_t, C_m,t, alpha_t)      governing purpose, potentially revised
    a_t ~ pi_K(a | A_tilde,t, G_t, H_t)  one action through the expertise transition model
    tau = (a_1, ..., a_T)                the realized process path
    K_t+1 ~ L(K_t, E_t, alpha_t, C_m,t) + epsilon_t
                                         lossy consolidation into later expertise
    O = h(tau, C_ext,1:T)                the medium's lossy artifact record

    reader R approximates q_R(G, tau, V, D, K, H, B, A_tilde, C_m | O, C_ext)

Here `G_t` denotes the governing purpose at time t. A change of attended subgoal does not
by itself change `G_t`; subordinate control targets remain inside the goal and process
account. The schematic leaves their selection implicit rather than identifying attention
with purpose or adding a fourth inference family.

Here `alpha` names the time-varying allocation of attention, `H` the control and history
residue of repeated behavior, `E` the experienced material of the episode, `L` the
consolidation-and-learning transform, and `epsilon` interference or forgetting. Five things
the schematic fixes. `K` is the transition model and `tau` the realized path through it: the
expertise line predicts what could happen, the process line records what did. Consolidation
encodes and compresses the historical record into later expertise; interference and forgetting
are error in that record, not part of it. The expertise-formation line is the curator's LIVE
hypothesis (the 2026-08-31 pass), not an established identity, and it is testable only if
attention is measured independently of its later effect on expertise: defining `alpha` as
whatever changed `K` is circular. Naming attention does not explain why it moves; the
allocation law remains open. And the posterior belongs to the reader-artifact-context relation,
not directly to the maker: the subscript does real work, and the reader's output includes both
a posterior over maker histories and a distribution over routes the reader could enact, the
latter conditioned on the reader's own body, expertise, and tools, never silently reported as
the former.

**Historical process and reader-enactable process** *(the 2026-08-21 pass)*:

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

**Understanding the work is the intended use; later prediction is one discriminator.**

> We're kind of both in there. And to an extent, that's kind of fine.

> Because the technique I acquire is one that's for me.

> The bigger piece is that I can more easily understand the intended experience. Much more easily.

> There's something here about higher order goals being more visible over time because they
> capture more lower level decisions.

*Curator's six-question maker-model and context walkthrough, supplied in the analysis thread; recording date not separately supplied;
filed 2026-09-18. Separate contiguous excerpts, wording preserved.*

The curator prioritizes understanding how the work was made, its intended experience, and what
is worth investigating or taking from this maker. Inferring tools, AI involvement, context and
human contribution is the immediate instrument ambition. Prediction of an unfamiliar response
remains a useful validity check; it is not the sole benefit the reader is meant to provide.
A useful method learned through self-projection and an accurate estimate of the maker are
separate achievements. A tiny gain in the reader's craft need not be the main value of the
maker model; it may instead reorganize interpretation and the reader's willingness to update.

A higher-order goal may explain many lower-level choices and connect previously separate
clues. Explanatory reach is not specificity: a broad aim may fit many makers, and its repeated
manifestations may share one cause. Expertise can constrain purposeful behavior while also
expanding the repertoire; it does not make experts universally more predictable than novices.

Historical correction also changes the evidence for a proposed technique. If its only
warrant was that it supposedly produced this artifact, discovering a different actual route
removes that warrant. A reconstruction independently made to work retains its demonstrated
usefulness. The historical route is evidence of feasibility under the maker's conditions,
not proof that it is best for the reader's body, tools or purpose.

**Why goal remains a separate inference** *(the 2026-08-31 pass; provenance in
`docs/design/archive/PHASE_2_4_STAGE_6_THEORY_ERRATA.md`)*:

> Strictly speaking, flawless expertise and context could let you reconstruct the process without
> first recovering the goal. But the goal is needed to understand the creator's trajectory and to
> decide what is worth taking up. A book by a torturer and a book by an ex-torturer should not be
> read in the same way.

*2026-08-31 walkthrough; spoken wording lightly reconstructed.*

Goal is therefore neither the mandatory first step of every process reconstruction nor a
redundant label. A sufficiently complete conditional policy can predict production without
explicitly naming the current goal. Goal remains a separate inference target because it
identifies present motivational direction, helps distinguish inherited expertise from current
correction, and informs later character and uptake judgments. Reconstruction accuracy,
character evaluation, and uptake are scored separately, so a preferred maker model cannot make
itself appear more accurate.

> The proximal goal is the reason you started spending resources to do this whole string of work in
> the first place. You do not hold that main goal in attention the whole time; you slide through
> sub-goals that stay in alignment with it. The proximal goal is the thing you are attending to, and
> it is always hierarchically in support of the larger goal. It is rare to see a proximal goal change
> midway through the creation of an artifact.

*2026-09-04 walkthrough; lightly cleaned transcript.*

The current terminology reserves proximal goal for the artifact's governing purpose,
the reason resources are spent on the work. The quotation uses goal at both governing
and attended levels; the prose distinguishes them. Purpose can persist while attention
moves among subordinate goals, and a genuine change of purpose remains possible. Its
stability is a working expectation, not a universal fact about artifacts.

The K-family pull ordering supplied and scored in Stage 7 is a preference over move types
derived jointly from purpose and law. Stage 8 scores an artifact purpose beside that pull
ordering; their different readability does not decide which is the more fundamental goal.

The director under a camera constraint illustrates a further possibility: a maker may
preserve an intended audience effect by changing technique, staging, timing, or delegated
work. A familiar surface device need not persist for the governing purpose to persist.
This is an interpretation of the curator's hypothetical example, not a finding about a
particular director. A retained effect, a changed purpose, habit, convention, and other
contributors' choices remain distinguishable explanations.

On the output's shape *(the 2026-08-23 pass)*:

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
`q_R(G, tau, V, D, K, H, B, A_tilde, C_m | O, C_ext)` output, not a fourth inference.

A single artifact can constrain goal, process, and value hypotheses when the available
context and alternatives are informative. Repeated, varied observations are the proposed
way to distinguish persistent motivational organization from situational explanations;
there is no universal artifact-count requirement (§1 L-tier2; §5 G54; §6 S-15). A
commissioned, coerced, or instrumental goal can **diverge** from values; "goal is a
temporarily amplified value" is the special case where context is friendly, not the
definition.

On who knows the goal *(the 2026-08-23 pass, same provenance)*:

> You cannot ignore the primary goal and its place in the equation. The author can learn more
> about themselves from reading their own work because they have flawless understanding, not just
> of the context, but also of what their goal was. The expert reader does not have that privileged
> access, but can sometimes infer it from a better mapping of the choices made in the domain.

> You have to reverse engineer your own goals through your actions as you are going.

*Curator’s earlier rehearsal, novelist and filmmaker walkthrough in this analysis thread, question 2; source date not separately supplied; handoff prepared 2026-09-12; applied to theory 2026-09-13. Wording preserved.*

The maker's episodic memory can supply evidence unavailable to another reader, conditional
on what the maker still remembers. Privileged evidence is not transparent self-access:
automatic goal elaboration, changed intention, and forgotten subgoals can require
self-reconstruction during making or after interruption. The earlier quotation's
“flawless” access is a limiting remembered-goal case, not a general assumption of the
working account. The artifact can help its maker work backward from choices to the goals
and expertise that shaped them. Maker and outside reader estimate the same targets from
different observations.

**A label is a lossy pointer; understanding is realized prediction** *(the 2026-08-30/31
passes; provenance in `docs/design/archive/PHASE_2_4_STAGE_6_THEORY_ERRATA.md`)*:

> If you had all three pieces, you should be able to recreate the activity quite precisely. If the
> labels sound insightful but do not improve the prediction, then no, the maker has not been
> understood.

> A candidate is only a small piece of the full prediction. To use it, I have to align it with an
> existing structure that can predict the whole artifact. The words lose precision, and the
> artifact re-centers what the candidate actually means in context.

> Can you predict stopping? Yes. I think you should be able to predict stopping and the next edit.
> Those are two things that would demonstrate understanding.

*2026-08-30 assessment; spoken wording lightly reconstructed.*

A mental-state label is a lossy pointer into `q_R`, not a recovered state. A short hypothesis
about the maker underdetermines the state it names; to carry evidential weight it must be
realized against the artifact and declared context into a state that changes the reader's
predictive distribution, and the test of that realization is prospective: the hidden
continuation, the next edit, stopping, a declared recipient response, or the changed-context
choice. A label whose realization
moves none of these has not been cashed, however insightful it sounds.

**A short mental-state label is a pointer, not the reconstructed maker state.** Its operative
meaning must be re-centered in the whole artifact, context, and possibility space until it
entails a distribution over the maker's remaining decisions. Different descriptions may realize
the same predictive state, and the same words may realize different states for different
makers; a longer rationale does not solve this by itself. The representation may be language,
structured slots, a program, or a latent vector; what earns credit is prospective constraint
on a hidden continuation, next edit, stopping decision, declared recipient response, or
changed-context choice. Stage 6
attempted to instrument this rule, but its hidden dependencies voided the interpretation
(M-S6). The rule remains a prospective criterion, not a claim that language is the required
representation of the maker state.

A recipient-effect prediction is credited against a declared, independently checked
response. It does not establish the exact edit or historical route that produced it.
The editing example is developed in `DECISION_TRACES.md` §2.

> Predicting the next move largely captures whether you have a full picture of their expertise. What
> remains are the creator's specific decisions, which you could only recreate with a truly flawless
> mapping. You explain what you can as expected behavior, and then notice the things that defy your
> expectations, which creates a demand for an explanation. Interesting is a part of the map you can
> almost figure out. That is why mistakes are almost always interesting.

*2026-09-04 walkthrough; lightly cleaned transcript.*

Prediction of the next move tests expertise first; the maker is in the residue, the events the
standard process does not expect, and interesting names the part of that residue a reader can
almost solve (P-S8).

> The maker's share is small by nature. Process, context, and constraints are the biggest piece. The
> maker's main share is probably the proximal goal and the attendance thereof, and then records of
> previous proximal goals that diverge from the standard process. It can be expanded by working in
> spaces that are more artful, defined by the concentration of decisions one can put into a given
> medium.

*2026-09-04 walkthrough; lightly cleaned transcript.*

The maker's share is small by nature and lives in the divergences from the standard process: the
proximal goal, the attention paid to it, and the record of earlier goals that diverged. The artful
gradient, from a diary through a painting to a sonnet, is the concentration of decisions a medium
admits, and it enters Stage 8 as a construction variable rather than a claim (MS-S8).

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
| **M-S6** | Realizing a short hypothesis about the maker into a predictive state beats reading the artifact directly, and the Sounding realization beats the published scaffolds | **VOID AS EVIDENCE FOR THE NAMED CLAIM (Stage 7 D01 to D06, L330).** The shared predictor accessed the complete hidden action inventory, the future events and trajectory length, the stop shift, and the exact transition and utility laws; the supplied-true-state gate (I05) supplied prose labels rather than the full operative state; the realization card (M14) received constructor variables; the semantic-invariance card (M15) followed hypothesis tags while ignoring the semantic text; exact-likelihood selection survives only as known-law system identification (MAP 0.79 against the label reader's 0.30, n 128); no architecture ranking, reader-boundary, realization, semantic-invariance, or reader-capacity conclusion is licensed |
|   | | *(this row's history is REALIZATION PAYS on the Stage-6 block, L315 to L326, then voided by the 2026-09-02 dependency audit, L330; the landed numbers stay in FINDINGS as method archive)* |
| **K04-S7** | Can a bounded reader use fully specified operative maker state to predict better than a frozen common-domain model? | **OPEN; the claimed clean isolation is VOID (test, L335/L336/L340/L349; OPS-ERRATA-2).** Historical direct scores remain negative, but the text rounds state and omits the solver's operative law, while the inherited option helper can discard candidates. The solver-oracle equality remains. The 9B route changes family/version, quantization, server and scoring as well as size, so no pure size conclusion follows |
| **I06-S9** | Does explicit execution improve prospective prediction when a direct neural reader receives the same complete operative program and state? | **SUPPORTED descriptively within the selected closeout (test, constructed worlds, model readers versus exact program, L373/L374/L375/L376/L384).** On the same 192 discovery questions, execution exceeds Qwen base direct reading by +1.451 nats [1.219, 1.698], Qwen archived by +2.537 [2.117, 2.975], SmolLM base by +1.753 [1.460, 2.054], and SmolLM archived by +0.983 [0.687, 1.299]. All four direct packages are below the uniform floor when pooled; archived SmolLM is -0.473 [-0.827, -0.141], with its essay-only interval spanning zero. Code addition has no established gain for either base package, but helps archived Qwen (+3.206 [2.993, 3.409]) and archived SmolLM (+0.415 [0.262, 0.566]) without eliminating the execution gap. Full support, original calls, isolation, calibrations and saved analyses reconstruct. These are shared units, not independent population replications. Privileged supplied-information diagnosis only; no ordinary artifact-inference, internal-mechanism, causal training-effect, size or confirmation claim |
| **K-S7** | Some single true factor (context, action set, law, belief, goal), or the whole state rendered in language, lifts the reader over the domain model; a reader given a swapped belief or goal follows the oracle's reversal | **COUNTEREVIDENCE on every rung and both readers (test, L336), 48 to 74 paired worlds.** Each single factor leaves SmolLM2 a third to two thirds of a nat under the domain model and Qwen2.5-1.5B about three nats under; the prose rendering is no better than the executable one (SmolLM2 −0.34 [−0.68, +0.03] VALID_NULL, Qwen −3.30); where the swapped belief or goal reverses the oracle's expectation, the reader follows on 14 and 5 percent of pairs (K09, K10); direct-reader contrasts are limited by the inherited option readout and unmatched operative information (OPS-ERRATA-2); program-versus-domain results retain their separate scope |
| **X10-S7** | The language-state reader is invariant to paraphrase of the supplied state and moves under a meaning change | **COUNTEREVIDENCE, the attack fails (test, L336).** Total variation 0.57 under paraphrase against 0.59 under an inversion of the belief and goal statements, on 48 units; the reader's response to the supplied text is a response to surface, so its language-state claims close (the semantic-invariance question Stage 6 voided at M15, now measured with the leak closed); direct-reader contrasts are limited by the inherited option readout and unmatched operative information (OPS-ERRATA-2); program-versus-domain results retain their separate scope |
| **KI-S7** | With every factor but one supplied, the joint reader (proposals executed through the law) infers the withheld goal or belief and keeps the prospective gain | **NARROWED (test, L337), 48 and 66 worlds.** The joint arm returns to the domain model's level with the goal withheld (−0.00 [−0.21, +0.22] SmolLM2; −0.15 Qwen) and clears the floor for SmolLM2 with the belief withheld (+0.29 [+0.07, +0.51], three quarters of the way to the true-state solver), half a nat to two nats above the direct reader, and with the belief withheld both readers clear the floor once their split-line answers are parsed (the tolerant-grammar rerun: SmolLM2 +0.29 [+0.05, +0.50], Qwen +0.36 [+0.13, +0.58], 0.73 and 0.92 of the way to the true-state solver); but the goal is in the candidates one time in four (R01, L341: 0.23 against the 0.5 bar that opens selection), the belief in 39 percent of worlds, and the reader follows the oracle's belief reversal on 1 of 14 twin pairs: the gain is the law's execution of the supplied factors under a proposal that is wrong three times in five; asked for the subjective action set with the context derived (K13, L338), the readers' proposed sets contain the truth in 5 percent of worlds and the arm's full commitment to them lands −5.0 [−7.4, −2.6] and −11.5 [−14.1, −8.9] nats under the domain model: the maker-relative possibility space is not computed from its determinants; asked for the maker context with the beliefs supplied (R10, L343), Qwen's proposed context improves the changed-context choice over the domain model by +0.59 [+0.31, +0.90], which is exactly what copying the visible brief with accurate beliefs gives (−0.03 [−0.10, +0.02] against that rival, itself the oracle here); direct-reader contrasts are limited by the inherited option readout and unmatched operative information (OPS-ERRATA-2); program-versus-domain results retain their separate scope |
| **KL-S7** | The expertise law is recoverable from process evidence: by exact selection among supplied candidate laws, by a law learned from a few demonstrations, or by a reader's proposal | **SUPPORTED FOR THE TWO PROGRAM ROUTES, NOT FOR THE READERS (test, L339), 48 worlds behind the clean-room boundary.** Exact selection +0.59 [+0.34, +0.84] over the domain model with 0.52 of its mass on the true law; a law fitted from two demonstrations +0.57 [+0.31, +0.85], indistinguishable from selection (−0.02); the joint reader realizes a proposal on 16 of 120 rows (the readers echo the candidate tables in view) and lands at +0.17 [−0.06, +0.40] and at the domain model; the Stage 6 survivor (supplied-law selection as system identification, L330) replicated with no privileged call; and the learned law TRANSFERS (R09, L342): fitted from three earlier episodes and executed on an untouched one it lands +0.64 [+0.22, +1.12], within a hundredth of the oracle, while the joint reader proposing the law from the same demonstrations with no table to copy clears the floor on Qwen (+0.56 [+0.14, +1.03]; SmolLM2 +0.21 [−0.08, +0.53]), the one reconstruction rung a reader passes on its own proposals; the confirmation freeze took the learned law as its first claim and B01 replicates it on untouched lineages (+0.62 [+0.25, +1.02] over the domain model, 51 worlds; the readers inconclusive there, +0.10 and +0.26), the run's one confirmed effect so far, a program's |
| **RJ-S7** | The goal and the belief can be inferred jointly without one collapsing into the other, and the joint inference keeps the prospective gain | **NARROWED (test, L344), 60 worlds.** No collapse: the goal is in the candidates in 23 percent of worlds and the belief in 34, about as often as alone, with the factor marginals apart; no gain either: the committed pairs leave SmolLM2 at the domain model (−0.17 [−0.47, +0.13]) and Qwen 1.4 nats [0.4, 2.7] under it, the goal-by-belief cells running from +1.9 to −8 nats where a confident wrong pair is executed; with the law withheld and no demonstrations (R12, 108 worlds with law twins), Qwen names the law's shape in 56 percent of worlds and gains a tenth of a nat that does not clear the interval (+0.11 [−0.33, +0.50]; SmolLM2 +0.04), the executed shape being a standard table rather than the maker's numbers, and a swapped law that reverses the oracle's expectation moves neither reader (0 of 8); cold (R13, L344), with the goal, belief, law, and residue proposed and the context and action set derived, the realizing reader is 1.3 nats [0.4, 2.6] UNDER the domain model (COUNTEREVIDENCE) and 1.6 [0.2, 3.0] over the direct reader; SmolLM2 realizes 15 worlds of 60 and sits a third of a nat under (inconclusive); Qwen's candidates hold the law's shape in 68 percent of worlds, the goal in 42, the belief in 7: the readers name the law and not the belief, and the arm's commitment to the wrong set costs more than ignorance; on the stop the domain model's hazard is within 0.05 nats of the oracle and every reader arm is under it (P05), and on the boundary type the executed state's stop terms name the wrong reason with full commitment, Qwen at the log-score floor on 8 worlds of 10 (P06, L344); over the whole withheld tail the joint arm is a nat under the domain model summed over up to four events, the loss spread across the events rather than sitting at the queried one (P09, L350), and the ladder's fresh draw of 29 worlds with longer tails agrees on every line (rung 4, pooled −0.94 [−2.02, +0.18]); the cold rung itself on a fresh draw of 60 worlds lands at the domain model (SmolLM2 −0.10 [−0.31, +0.13], Qwen +0.03 [−0.39, +0.43]), so its counterevidence narrows to "at or under the domain model, by the draw", nothing above it on either draw; direct-reader contrasts are limited by the inherited option readout and unmatched operative information (OPS-ERRATA-2); program-versus-domain results retain their separate scope |
| **RG-S7** | Maker familiarity helps where cold reading fails, independently of domain expertise | **NARROWED (test, L345), 40 worlds crossed with three regimes.** No: two earlier episodes by the same maker leave the failing reader failing (Qwen −1.75 [−3.41, −0.44] against the domain model, committed on every world) and the reader near the domain model near it (SmolLM2 +0.02 [−0.24, +0.28]); the domain's generic law in view brings Qwen to the domain model only by silencing it (the law answered in prose on 35 worlds of 40, the set unsolvable) and makes both direct readers worse; beside R09 there is demonstrated law recovery but no demonstrated rescue of the full cold state; R15 (L345): the generic law halves the joint arm's candidate entropy (0.08 against 0.16 cold) while its calibration stays at chance in every regime (expected calibration error 0.44 to 0.50), certainty moving with the regime and correctness not; direct-reader contrasts are limited by the inherited option readout and unmatched operative information (OPS-ERRATA-2); program-versus-domain results retain their separate scope. Separate session-local test (test, L385; human CoAuthor process records, two Qwen model readers): correct history improves the larger direct reader against other-writer history and no history on the matched targets, and beats cheap persistence and the class prior there. Donor links leave one component; this supports scoped evidence usefulness, not enduring maker familiarity or value recovery.  Local Stage 10 matched session-history comparison (test, L386; human CoAuthor records, local Qwen reader) favors own history by +0.069313 half-Brier for grounded procedure memory and +0.003474 for direct reading on 77 eligible events. One dependent component and excluded unmatched events limit the claim to scoped session-history usefulness. |
| **EQ-S7** | The reader preserves observationally equivalent maker models and chooses a useful next discriminator | **NARROWED (test, L346), 60 worlds, descriptive.** Abstention does not track the prefix's ambiguity: the joint arm withholds on 59 percent of the equivalence cases and on 73 percent of the singletons, within noise of each other, and SmolLM2's abstention is failure to propose on 36 worlds of 60; the discriminator measure is 1.0 against the reader's own greedy choice by construction and is an instrument gap for the next stage; the joint arm's confidence is anti-informative (P10, L346): expected calibration error 0.51, its most confident tenth the worst at any coverage, calibration worse the more evidence the prefix carries; the equivalence attack X14 fires on the same figures (false abstention 0.73 against its ceiling of 0.5), so the run's own criterion records that the readers do not preserve the class |
| **RV-S7** | The joint reader revises mutually constraining factor hypotheses as the prefix grows, and the revision changes what it predicts | **NARROWED (test, L347), 30 worlds.** A sequential particle arm that re-weighs, resamples, and re-proposes candidate states at prefix checkpoints predicts what the one-shot joint posterior predicts (+0.02 [−0.16, +0.21] nats; Qwen within four hundredths), because the readers propose one candidate set on 48 worlds of 60 and nothing ever collapses or is re-proposed; revision is testable only for a reader with candidate breadth, which neither has at this scale |
| **AC-S7** | At matched evidence and measured compute, structured computation (a realizer over proposed maker states) beats direct inference-time computation | **NARROWED (test, L348), 40 cold worlds, seven arms.** Every structured arm beats the direct reader (the joint arm +1.5 nats [+0.4, +2.5] pooled; the five conformance-reproduced rivals +1.4 to +2.1), and none beats the domain model: the direct reader is 2.1 nats under the prior, the arms that realize on every world sit at it or a nat under it, and the arms that rarely realize fall back to it; no arm's gain per unit of compute exceeds five hundredths of a nat; the two conformance cells of the day before say the same (L355, L356): the adaptive expansion adds factors at one rate whether a variable is missing or not and costs 0.22 nats against the joint reader where the world is complete, and the synthesized agent model validates on 28 of 30 worlds for one reader, beats the direct reader by 2.86 [1.50, 4.31] and sits 0.72 under the domain model, the effect the freeze selected for confirmation; B02 confirms it on untouched lineages against the direct reader (+3.59 [+2.34, +4.78] on Qwen, pooled +2.19) and finds it counterevidence against the domain model there (pooled −0.32 [−0.54, −0.06]), so the run's second confirmed effect reads: synthesis beats free text and not the prior; direct-reader contrasts are limited by the inherited option readout and unmatched operative information (OPS-ERRATA-2); program-versus-domain results retain their separate scope. Separate cloud comparison (test, L385; human CoAuthor process records and constructed Ghost opportunity tasks, Qwen 3.5 9B/27B model readers with exact executors): the larger package improves direct prediction but its incremental reconstruction benefit is smaller on both main populations. Human grounded procedures help relative to opaque descriptions but do not beat stored examples on the primary score; no persistent maker-model or human-mechanism claim follows.  Initial local Stage 10 complete cells (test, L386; human CoAuthor/ScholaWrite records and constructed Ghost opportunities, local Qwen reader and exact executors) show evidence-specific structured benefits but no general advantage over cheap priors or stored examples. That initial landing covered one ScholaWrite project and two Ghost cases. Further complete local comparisons (test, L387; human CoAuthor/ScholaWrite/ArgRewrite records, local Qwen and Llama model readers with exact executors) retain source-specific benefits: Llama improves direct handling prediction but its executed proposals lose to matched deliberation, and simple priors beat every model on eleven of twelve additional project/view cells. The small ArgRewrite current-draft forecasts have invalid probability sums. Final local Stage 10 closure (test, L388; human revision/handling records and constructed Ghost tasks, local model readers and exact executors) completes all five ScholaWrite projects and the separate reconstruction repair: the training prior beats every model in 27 of 30 project/target/view cells, while legal candidate execution often fails visible-artifact reconstruction. Selected predictive increments and relevant-history effects remain descriptive assistance; general maker-model recovery is not established. The late omitted-control completion (test, L389; human earlier-draft CoAuthor records, local model readers versus fixed training-only controls) leaves original reader scores intact and finds the training prior better than every model on Brier loss, while its zero-support outcomes retain infinite log loss. |
| **S11-CONTRIBUTION** | A bounded role-labelled contribution account improves retrospective suggestion-handling recovery over direct reading and cheap controls on the same evidence | **OPEN generally; no consistent observed advantage in this scoped test (test, L390; historical human CoAuthor process records, pinned local Qwen reader and exact scorer).** Across two separately scored tranches and two evidence views, account-minus-direct loss improves twice and worsens twice; the training prior beats every model and feature baseline throughout. The six-case log audit finds unsupported review and actor/dependency claims even beside correct handling guesses. This does not test the general event-network theory or establish intended experience, expertise, values or selective attention. |
| **S11.1-CAP** | Does enforcing the requested training cap preserve cheap-control strength? | **NARROWED (test, L391; exposed human CoAuthor records, exact CPU fitting and scoring).** The separate three-per-writer fit improves feature probability loss in every cell but does not yield consistent dominance over the capped prior. The capped prior has zero support for an observed initial-tranche class. The published Stage 11 comparison remains unchanged; strong inexpensive production-relation rivals remain unexhausted. |
| **S11.1-REFERENCE** | Does direct reading recover witnessed production relations beyond training marginals and fixed text alignment? | **REJECTED for the completed reference implementation (test, L392/L397/L404; exposed human CoAuthor process records, pinned local Qwen reader and exact CPU rivals/scorer).** Both cheap rivals beat direct reading on all production half Brier losses in the complete reference and both breadth tranches; alignment adds correctly located useful events with before text and alternatives. The remaining breadth adds no independent writers or sessions. Invalids remain charged and scored; alignment retains zero-support handling failures. This is descriptive coverage, not independent replication; unfinished sequential extensions remain unranked. |
| **S11.1-REVIEW** | Does a second direct pass on the same evidence improve witnessed production recovery? | **SUPPORTED only for limited invalid-output recovery across complete discovery and breadth (test, L393/L401/L405/L407; exposed human CoAuthor records, pinned local Qwen reader and exact scorer).** Valid first forecasts remain unchanged while some invalids recover. Half Brier losses improve but remain worse than both cheap rivals. Located useful yield stays unchanged across discovery and initial breadth, increasing slightly only in the remaining breadth. Unsupported mental claims increase, and selective error worsens at low coverage. Shared writers/sessions prevent independent replication; semantic self-correction remains unestablished. |
| **S11.1-ACCOUNT** | Does constructing and then consuming a typed contribution account improve historical production recovery over matched review? | **OPEN generally; no consistent advantage across complete discovery and breadth (test, L394/L403/L406/L408; exposed human CoAuthor records, pinned local Qwen reader and exact scorer).** The discovery extension improves operation and handling half Brier losses in both evidence tiers but worsens relation loss and unsupported mental claims; useful yield is mixed and located useful yield does not improve. Both breadth tranches lose to review on every production and handling half Brier loss. Some direct-relative and selective-risk gains coexist with cheap-control superiority. Frequent invalid graphs limit attribution to valid account use; shared writers/sessions prevent independent replication. |
| **S11.1-ACCOUNT-USE** | Does changing a retained account alter useful historical recovery beyond ordinary request-repeat variation? | **SUPPORTED for bounded input sensitivity; general useful-recovery advantage remains OPEN (test, L399; exposed human CoAuthor process records, pinned local Qwen reader and exact scorer).** Valid-account interventions change forecasts while contemporaneous identical-input repeats agree. Removal raises useful yield despite worsening operation/relation losses; unrelated replacement improves those losses while eliminating useful yield. This does not isolate semantic faithfulness or internal mechanism. Original uncontrolled attribution remains VOID (L398). |
|   | | *(Original diagnostic attribution voided after identical-request variation, L398; separate valid-account repair supports request-intervention sensitivity with repeat controls, L399. The original matrix and void remain intact.)* |
| **S11.1-EVIDENCE** | Does one additional source observation improve historical recovery, and does a reader choose it better than a fixed policy? | **SUPPORTED for selective fixed-before evidence benefit; learned acquisition superiority REJECTED in this bounded implementation (test, L400; exposed human CoAuthor process records, pinned local Qwen pipelines and exact scorer).** Before text improves account production losses and useful yield for both methods, but supplies no correctly located useful event. The learned selector worsens all production losses versus blind. Frozen cheap rows ignore the added observation and remain strong static references; no evidence-aware cheap-rival, semantic correction or human-attention claim follows. |
| **S11.1-CONTEXT** | Can discriminating context resolve production histories with identical visible endpoints without following irrelevant or misleading cues? | **SUPPORTED for constructed ambiguity; reliable selective correction REJECTED in this implementation (test, L402; constructed process records, pinned local Qwen pipelines and exact scorer).** True context yields some located useful events, but review production losses worsen and account gains are nearly matched by irrelevant or misleading cues. Blind certainty is unwarranted. Fresh chains, changing graph validity and context-insensitive cheap references limit mechanism claims; this does not estimate ambiguity in human writing. |
| **S11.1-HISTORY** | Does a reusable hypothesis from earlier choices improve later production recovery beyond the same raw history, donor history and no history? | **OPEN generally; no consistent advantage over no history in this implementation (test, L395; exposed human CoAuthor process records, local Qwen reader and exact scorer).** The hypothesis improves operation loss and half-coverage error but worsens actor, relation and handling losses, with unchanged correctly located useful yield. Own raw history does not consistently beat donor history; cheap current-text controls lead every model condition on all production losses. Construction and invalids remain charged; no value or human-mechanism claim follows. |
| **S11.2-PERSISTENCE** | Does carrying executable maker hypotheses add prediction beyond the same raw history? | **SUPPORTED for computation reuse, no prediction increment over exact full-history inference (test, L409-L410; constructed four-action makers and exact program readers).** Persistent weights and full recomputation agree on development and withheld-mechanics probes; a two-observation bottleneck loses information. Fixed candidate addition improves an incomplete library but remains worse than starting with all four policies. The original test wrong-context manipulation is XOR-invariant and licenses no sensitivity claim. Source-linked and perspective controls are programmed policies, not learned neural trust. Human and neural transfer remain OPEN. |
| **S11.1-REVISION** | Do before/after differences improve released revision-category recovery beyond the endpoint? | **REJECTED for this bounded comparison (test, L396; exposed human ScholaWrite edits, local Qwen reader and exact annotation scorer).** Added differences leave aggregate accuracy unchanged and slightly worsen probability loss across the complete project comparison; annotator-category recovery is not writer-purpose or AI-involvement inference. |
| **TT-S7** | The maker's record supports a dated present focus plus an uncertain historical mixture (two timescales), and the dates and order of earlier episodes inform a later choice beyond an aggregate profile | **NARROWED (test, L354; V04 to V06, programs only).** A mixture over dated episodes and a forced point date predict the present episode alike (−0.01 [−0.09, +0.07]); the dated, ordered, and aggregate views of earlier episodes predict a later episode alike (valid nulls); for a later costly choice the dated trajectory beats the domain model (+0.42 [+0.05, +0.84]) and the law-less solver (+0.48) because it carries the law, and beats the aggregate by five hundredths under the floor: the record's two timescales are not separated at this construction's drift, and its history informs through the law alone |
| **J05-S5** | The standing preference inferred from one episode predicts the maker's choice in a second episode under a stated new goal, beyond habit, topic, and last-goal baselines | **COUNTEREVIDENCE (test, L280), 256 worlds.** −0.73 nats [−0.93, −0.55] against the topic baseline; the reader half a nat under uniform; the preference recovered in a third of worlds; the exact ceiling a quarter of a nat above uniform. Second contract (L293, two readers, the ceiling raised to 0.68 above uniform): −0.26 against the topic prior, both readers under uniform |
| **C-ROL-S9** | Which action, outcome, reset and artifact assistance changes sustained execution? | **OPEN for full-generation competence; scoped assistance effects measured (test, constructed worlds, archived Qwen and SmolLM models with exact evaluator, L378/L381/L384; C02/C06/C08 diagnostics).** On the same 192 worlds, Qwen reaches sixteen actions only with offered actions (102); SmolLM reaches them with named actions and stepwise checked outcomes (190 in either outcome condition, versus 117 offered). Resets help Qwen at eight actions but reduce SmolLM reach with unavailable states retained. Artifact views fail before four actions throughout. These are package-specific interactive capabilities, not policy quality, correct stopping or whole-log generation; separate scoped integrity is complete, with no full-generation admission |
| **C01-S9** | Does prediction change under different histories at exactly the same operative state? | **OPEN for generated-history effects (test, constructed worlds, archived Qwen and SmolLM models, L379/L382/L384).** Both packages retain 94 essay and 93 workshop altered pairs with mean log-score intervals spanning zero. Qwen produces no generated match; SmolLM produces one essay match with zero point difference but no grouped uncertainty, and none in workshop. Conditional similarity is not distributional invariance or internal state representation; generated-history effects remain unidentified after separate scoped integrity |
| **C04-S9** | Does the reader correctly preserve equivalent futures and distinguish different futures under supplied finite rules? | **REJECTED for this supplied-rule battery (test, eight constructed projections, archived Qwen and SmolLM binary readers versus exact truth, L380/L383/L384): Qwen constant-no responses and SmolLM variable responses with retained ties both fail every compression, distinction and longer-distinction battery; source aliases are dependent; separate scoped integrity accepts this descriptive failure, not a general capacity claim** |
| **P-S8** | Prediction of the next move tests expertise first; the maker's share is the residue, the events the standard process does not expect, and a reader that holds the standard process localizes its surprise on those events | **OPEN for the proposed expertise-conditioned mechanism; the tested raw-surprise proxy failed (test, constructed worlds and model readers, L359 to L365, L369/L370; OPS-S9-THEORY-1).** Prediction passes: at expanded size, gains over the domain model are +0.24 and +0.20 nats on 306 units, with intervals above zero. Generation fails on both readers (L360), so neither reader is admitted. Raw reader surprise ranks the designated divergence events poorly (root AUROC 0.34 and 0.37, domain baseline 0.56; L362); this is a diagnostic failure, not proof that every form of maker-specific information is absent. The divergence target is an oracle-minus-domain action-probability gap, not raw rarity. Proposed purpose lowers prediction relative to the plain reader on both expanded comparisons (about −0.09 and −0.06 nats, intervals below zero; L370); true purpose adds smaller positive point increments of about +0.073 and +0.045 nats. These observations do not isolate surface familiarity from operative competence. Pull recall exceeds purpose recall on this construction (L364), which does not identify the correct goal ontology. The meaning-change crossover fails (L365), but scoring the changed evidence against the original purpose label does not by itself establish semantic blindness |
| **MS-S8** | The maker's share lives in divergences from the standard process and may accumulate across artifacts | **OPEN; diagnosis only (test, L366/L367/L371).** At the larger sample, three earlier artifacts improve surprise alignment by +0.0136 [+0.0032, +0.0235] on Qwen and +0.0073 [-0.0041, +0.0195] on SmolLM2; neither series is monotone and all conditions remain below the domain model. Law/residue recall does not rise with earlier artifacts and the inferred maker model adds no established predictive gain. Neither reader is admitted, so this does not establish the proposed process-based accumulation |
| **J03-S5** | Along the stream the reader's records become useful in a diagnostic order and a contradiction lowers its confidence | **NARROWED, descriptive (test, L264).** The plan record is reached last and most reliably; the preference record is never useful in two thirds of worlds; after an exact contradiction the reader is more confident and less right in 44 to 62 percent of worlds; on two readers with equifinal plans present the never-useful shares rise to 0.56 to 0.74 and overconfidence sits at half (L292) |

**State of the section's claim.** The generative account links maker-interpreted context,
feasible choices, governing purpose, expertise formed through prior attention, and the
realized process. Its distinctive wager is that a reader can use shared generative
structure to reconstruct and correct a maker model. Reader-enactable routes, historical
correspondence, and persistent motivational inference remain distinct products.

For the proposed human route, shared embodied and affective constraints are a load-bearing
source of that structure. Expertise and attention distort which possibilities are available
and expressed; the attention-allocation law remains open (G52).

The clearest bounded constructive result is an expertise law learned from earlier
episodes and executed on new ones; the confirmed program result is stronger than the
limited reader-proposal result (KL-S7). Separating appraisal and intended audience response
works in one construction and fails in another (A01-S4, A01-S5). Subsequent diagnostics
separate domain prediction from generation, and execution of supplied law and state from
ordinary artifact inference. They leave personal-history use and sustained consistency
unestablished in the tested reader packages (P-S8, I06-S9, C-ROL-S9, C01-S9, C04-S9).
The failed Stage 6 architecture and Stage 7 state-use instruments retain their recorded
scope; they cannot settle the proposed human mechanism (M-S6, K04-S7).

In a finite constructed maker family, carrying a sufficient posterior reproduces full-history
reconstruction while avoiding repeated policy evaluations. Truncating that history loses
information; this validates state reuse under the assumed law, not a neural inference gain
or a human motivational mechanism. A predeclared mismatch rule can add an omitted policy after public counterevidence, while remaining inferior to a complete candidate library; this is bounded repair, not open-ended hypothesis discovery (L409-L410).

The live question is whether a reconstructed maker model constrains unfamiliar behavior
beyond shared domain competence and strong direct prediction. A larger model package
can improve direct prediction without increasing the benefit of explicit reconstruction.
Correct session history and descriptive procedure names can help within the tested human
records, while task-specific action mixtures do not establish a persistent maker model
(L385). Complete local comparisons likewise show benefits that depend on evidence and often lose
to cheap priors or stored examples. The full project rotations and reconstruction repair
retain that limitation, including the completed earlier-draft baseline; the empirical prior
can lead on probability error while failing on zero-support logarithmic loss (L386-L389). This dependence persists across local packages and projects,
with invalid forecasts retained as interface failures. In retrospective suggestion handling,
organizing a bounded contribution account provides no consistent advantage over direct
reading, and the training prior leads both model methods. Correct handling guesses can
coexist with unsupported actor and review stories; each richer historical relation still
needs its own evidence (L390). A separate capped-training sensitivity improves the feature
control without establishing consistent dominance; zero class support still defeats the
prior on logarithmic loss, so inexpensive rivals remain an open engineering obligation
(L391). On fixed production questions, the smoothed marginal and text alignment both
outperform the tested direct reader; alignment supplies useful span constraints when
before text and alternatives are available. Both breadth tranches retain this
advantage, but the extension adds no independent writers or sessions. Greater episode
coverage does not become independent replication, and alignment still assigns zero
handling probability to some observed outcomes. Neither finite accuracy nor span matching
establishes review, endorsement or an exhaustive historical account (L392, L397, L404). A second direct pass recovers some invalid
outputs without revising valid forecasts across complete discovery and breadth.
Correctly located useful yield stays unchanged across discovery and initial breadth,
rising slightly only in the remaining breadth through invalid-output recovery. The
discovery extension adds unlocated useful claims alongside unsupported mental claims,
and its selective error worsens at low coverage. Lower average loss does not establish
semantic self-correction or reliable abstention (L393, L401, L405, L407). Constructing
an account first can improve operation forecasts without consistent useful recovery.
The complete discovery extension improves operation and handling losses in both tiers
but worsens relation losses and unsupported mental claims; located useful yield does
not rise. Frequent graph failure prevents attribution to valid account use (L394, L408).
Both completed breadth tranches lose to matched review on
every production and handling half Brier loss, with lower useful yield and more
unsupported mental claims. The extension has limited gains against one-pass direct
reading and lower selective error than review at low coverage, without beating cheap
controls. Shared writers and sessions preclude independent replication. Alignment
leads on half Brier error but retains infinite handling logarithmic loss, so its
probability support remains a separate limitation (L403, L406).
Identical requests can also yield different forecasts, so the
original uncontrolled intervention cannot attribute movement to account content; its
realized scores remain descriptive (L398). With valid accounts and contemporaneous
repeat controls, changing the supplied graph changes forecasts. The own account
protects operation and relation probability quality against removal but does not
consistently improve useful positive recovery; unrelated graphs can improve those
losses while eliminating useful yield. This supports request sensitivity, not
semantic faithfulness, historical fidelity or internal mechanism (L399).
Explicit before-text evidence can improve production losses and useful yield, while
a learned observation choice can worsen production losses. Those are fresh
evidence-conditioned forecasts, not demonstrated revision of an earlier belief;
account realization failures and an observation-insensitive cheap reference keep
the mechanism and broader method ranking open (L400). Matched constructed endpoints
can conceal different executed histories. True contextual cues produce some located
useful recovery, but irrelevant and misleading cues also move the account; that movement
does not establish reliable selective correction or justify blind certainty. This
construction establishes ambiguity under its matched evidence, not its prevalence in
human writing (L402). A reusable
hypothesis from strictly earlier human process excerpts improves operation recovery and
selective error without improving all historical relations or correctly located useful
yield. Correct-writer raw history has no consistent advantage over donor history, and
cheap current-text controls still lead the model conditions; compression and reuse do
not establish a persistent maker model or recover values (L395). Literal before/after
differences also fail to improve aggregate released revision-category recovery in the
bounded human edit comparison; an annotator label remains distinct from the writer's
purpose (L396). These
are bounded assistance effects, not a test of human empathy. Predicted edits, declared
recipient effects, and historical recovery are separate achievements. These component
results keep the question open without establishing the full reconstruction or identifying
a surface-only explanation of its failures.
Confidence: one bad test away for the scoped Stage 5 and Stage 8 observations and the
completed Stage 9, Gear 3 and scoped local Stage 10, Stage 11, exact Stage 11.2 development construction and Stage 11.1 reference, complete direct/review/account discovery and breadth, controlled account sensitivity, human evidence, constructed context, history and revision comparisons; untested,
logic only for the proposed expertise and accumulation mechanisms; instrument-dead for
the clean Stage 7 state-use isolation, the Stage 6 architecture interpretation, and
the Stage 8 semantic-intervention interpretation and the original Stage 11.1
account-use attribution.

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

> Several possible makers is part of what reading is. You are comparing convergent solutions to
> explain the irregularities you are seeing, all of them, as a total.

*2026-09-04 walkthrough; lightly cleaned transcript.*

Holding several possible makers at once is part of reading rather than a failure to decide: the
irregularities are explained as a total by comparing convergent candidate makers, which is why an
equivalence class kept alive until a diagnostic event closes it is the right shape for the output.

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
| **V-S6** | On constructed value worlds the reader preserves the policy-equivalent class until the diagnostic event, selects the separating probe, and its inferred trajectory predicts the changed-context choice beyond goal-utility baselines | **VOID AS CURRENT EVIDENCE FOR THE NAMED CLAIM (Stage 7 D01 to D06, L330).** The value cards inherit the dependency-tainted predictor; several of the questions duplicate one planted mapping or one statistic (V02 with V03, V04 with V05); the changed-context target exposes hidden generator structure; no Stage 6 conclusion about breadth, search, value trajectory, preference, or changed-context choice is licensed |
|   | | *(this row's history is SPLIT on the Stage-6 block, L316 to L322, then voided by the 2026-09-02 dependency audit, L330; the twins and the staircase geometry stand as construction facts, rebuilt behind the Stage 7 boundary as V01 to V06)* |

**Value change against concealment: dated evidence and the trajectory** *(the 2026-08-30/31
passes; provenance in `docs/design/archive/PHASE_2_4_STAGE_6_THEORY_ERRATA.md`)*:

> The best evidence that the value changed, rather than merely becoming better concealed, would be
> evidence elsewhere that the maker's foreground goals are different. The historical tendency
> preserved in expertise may give you an older data point. Together they give you a trajectory.

> The slope is between inherited, expertise-shaped tendencies and the maker's current proximal
> goals. Future edits should reveal whether that mismatch is a direction of change.

*2026-08-30/31 walkthroughs; spoken wording lightly reconstructed.*

> An artifact gives you two different kinds of evidence: a probabilistic distribution of previous
> attention, compressed lossily through expertise, and a record of what the maker chose to attend to
> when the artifact was created. Because we can separate current from past, we get a much richer
> preference estimate: not a single point, but a weighted trajectory.

> If someone repeatedly pays costs to redirect effort away from an old trained tendency, that
> redirection is a preference expressed currently. The trained tendency may preserve an older
> history; the present allocation records what they are trying to become.

> I am not assuming that there has to be a separate latent value field. A context-controlled
> probabilistic mapping of where attention chooses to focus may itself be the latent preference.

*2026-09-01/02 walkthroughs; spoken wording lightly reconstructed.*

**The two-timescale trace, and what it may and may not say about preference.** One artifact
supplies one dated present allocation plus an anterior, context-filtered mixture carried by
expertise; it does not supply two equally dated points. Weak relative-age cues may exist inside
the historical mixture, but they do not precisely date it. Several dated artifacts can make
their mixtures constrain one another and narrow the posterior over directions of change.
Present costly redirection is present preference evidence even when automatic capture reflects
older training or pressure. Preference may be stable parameters of a context-conditioned
attention-allocation policy, or that policy may be evidence for a deeper `V`; both ontologies
stay live. A vector or slope is shorthand until coordinates, a time basis, and uncertainty are
specified. Direction earns a preference interpretation only by predicting later costly choices
beyond context, local goal, habit, and expertise. And homeostatic return can express a stable
preference, so movement alone is not the target.

**Diagnostic value evidence may arrive after an initially ambiguous choice.** An
accuracy-oriented and a prestige-oriented maker can cite the same prestigious source;
discovering later that the source is wrong creates the separating opportunity, where direct
correction and argument repair compete with retention, hedging, and reputation management.
Until such an event, the honest output is a posterior over behaviorally compatible
motivational organizations. A changed foreground goal can be evidence of present direction
when it predicts later choices, while lagging expertise can preserve an older tendency; their
mismatch is only a CANDIDATE direction of change, not literally a linear slope (temporary
context, coercion, concealment, relearning, and nonlinear return toward an older mean remain
rivals), and it earns a trajectory interpretation only by predicting later edits, stopping, or
changed-context choices. The Stage-6 V track constructed exactly this geometry (exact twins to
the diagnostic consult, divergence after), which stands as a construction fact; its reader read
of the separation is void (V-S6), and nothing in it promotes value recovery.

**Preference evidence requires an opportunity-defined tradeoff.** A high-order structural
choice, such as how prominently to place a rival account, which caveat to preserve, or which
secondary goal to sacrifice, is a candidate preference event only when the actor controlled that
choice and genuine alternatives were available. It becomes evidence about a standing preference
when the same tradeoff recurs across contexts or predicts a held-out choice after topic, role,
convention, and local goal are controlled. One coherent placement is a qualitative hypothesis,
not ground truth. In collaborative work, role records or discriminating longitudinal evidence are
required before the event is assigned to the author, editor, or director.

**State of the section's claim.** Four accounts of where value information could live stand,
none dead, one favoured, and the favourite was a surprise: the residue account, the section's
original headline, now runs last by the program's own sequencing in its restated, weaker form
(a candidate value signal as the cross-episode remainder after modeling domain competence and
each episode's attention-weighted goal, expected messy because habit also records training,
convenience, accident, and repeated attention), while conjunctive satisfaction, the account he
flagged as the first non-dithering idea, is the one the constructed world discriminates toward.
The dated-trajectory rule and the two-timescale trace are a SEPARATOR, not a fifth account: they
say how change might be told from concealment, not where value lives, and the ontology under
them stays unresolved, since the stable parameters of a context-conditioned attention policy
may be the preference itself or evidence for a deeper organization. The absence mechanism is
the section's cleanest result anywhere, reading a missing drive through pursuit style at
sim-perfect strength under commission. Every one of these remains a claim about constructed
worlds: the Stage-3 environment rows are exact-construction facts about model readers and
programmatic makers, where the cross-domain reader gap, replicated on a third domain, and the
three-sighted instructed-versus-intrinsic asymmetry are the section's first live constraints
from the model side; the scoped transmission null stands, with its carrier present,
surface-trivial, and never taken up by the student. Stage 6 contributes no reader-side
evidence: its value quartet realized its states through the privileged call and is void
(V-S6), and the constructed geometry of policy-equivalent twins separated only by the
diagnostic event survives as a construction fact rebuilt behind the Stage 7 boundary. No real
maker's values have been recovered by any account. Confidence: the sim discriminations are
sim-only, authoritative about method; all four accounts and the separator are untested on real
text; the Stage-3 rows are one bad test away, the carrier's triviality measured on twelve
decisions; the Stage-6 quartet is instrument-dead.

## §6. Value blindness, and where longitudinal ground truth could come from

Self-report is closed as ground truth, and the reason is not modesty:

> You always have an imperfect view of anyone else's value set, and your own introspective and
> interoceptive access is **systematically limited and biased.**
> It's why artists will make art and look at it – in part to get a sense of their own values. They
> learn about themselves through that expression.
>
> Anything I say, anything I make will be over-indexed and automatically full of error, because it
> will be **my view of my own value set.**

Self-report can supply evidence about what a maker believes or declares about their
values; it cannot certify the internal value set. Assigning a value description to a
model likewise supplies an instruction, whose effects must be checked rather than treated
as that model's actual preferences. These restrictions concern ground truth, not whether
testimony or instructed constructions can be useful observations.

A single artifact can contain multiple informative tradeoffs under sufficiently strong
assumptions. Repeated artifacts in diverse conditions can separate some rival accounts,
while even unlimited observations need not identify an unrestricted reward and planner.
The required diversity depends on the competing hypotheses and the opportunities observed;
there is no universal count at which value becomes identifiable. The curator's observation
set can include behavior and life evidence as well as conventionally artistic works:

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
| **S-15** | Value-profile recovery converges with artifacts, residual priced | **SUPPORTED (sim), within the tested construction.** 0.53 → 0.98 over 1 to 50 artifacts, residual 0.009; bounded-family assumption worth 0.24. Approximately 20 works per maker is this construction's corpus price, not a human sampling requirement; conjunctive versus amplification accounts discriminate these constructions |
| **G60** | Recovery error shrinks with works, toward a small residual | **EARLY PLATEAU (test, L34), one channel (relabelled 2026-08-09).** 0.54 → 0.61 → 0.60 against 0.20 chance over one-to-three reference works. Rises from one to two works and not at three, on five authors and the cheapest channel. Three points cannot locate an asymptote, so the limit-framing reading this row used to carry was unlicensed |
| **G48** | A maker's weighting is more stable within than between makers | **OPEN.** The 34-book corpus supports the design, and per the program another stable author vector would be circular without behavioral tradeoffs; G135's held-out tradeoff prediction is the honest form |
| **G65** | Value recovery improves sharply with works per maker while goal recovery does not | **OPEN.** The follower-corpus design tests this and G48 at once |
| **G66** | Adherence to a declared value tradition is recoverable as a graded quantity | **OPEN.** A ladder made of humans; the honest output is predicted patterns of uptake or adherence from behavior; blocked on sourcing |

**State of the section's claim.** Longitudinal evidence is a motivated route to separating
persistent tradeoffs from local purpose, habit, and constraint. The bounded simulation
provides a construction-specific convergence curve and sampling cost; the real-text curve
measures author identity and cannot establish convergence of human value recovery
(S-15, G60). Testimony, biology, behavior, and artifacts remain observations with different
provenance and reliability. None automatically certifies the target values. No corpus
currently validated by this project supplies the complete value-recovery comparison
specified by the open rows. Public process and choice corpora can supply partial tests;
their suitability remains an intake and construct-validation question. A commissioned
pilot is one possible source, not evidence that no useful public corpus exists.
Confidence: one bad test away for the scoped identity curve and bounded simulation;
untested, logic only for human value recovery and the open corpus comparisons.

# Part III: Epistemic limits and evidence

## §7. Identifiability, not impossibility

**The project asks which substantive priors support useful narrowing; it concedes the non-identifiability theorem under its assumptions.**

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
refutation of the theorem, and the stronger convergence form is conceded above.** The following are proposed substantive priors that could narrow the problem. The theorem
does not establish that this particular trio is necessary or sufficient:

| candidate substantive prior | proposed project counterpart | curator shorthand |
|---|---|---|
| a bounded human hypothesis family | shared bodily, affective, and action constraints that narrow candidate human routes | **convergent midbrains**, retained as the curator's shorthand while the exact conserved machinery remains open |
| a bounded or conditioned transition model | a reader-relative estimate of feasible trajectories, conditioned on domain, tools, context, and maker evidence | **expertise** |
| a declared model of decision-making, including its departures from optimality | a constrained likelihood relating preferences and expertise to choices | *"that's just MaxEnt"*, retained as shorthand rather than an equivalence |

The unrestricted planner/reward result leaves useful inference under substantive
assumptions open; it does not select those assumptions for us. Maximum-entropy IRL, for
example, obtains a particular trajectory distribution using specified features and
constraints. It supplies a candidate decision model, not a general identity between
entropy maximization and human near-optimality.
([Armstrong and Mindermann, 2018](https://papers.neurips.cc/paper/7803-occams-razor-is-insufficient-to-infer-the-preferences-of-irrational-agents.pdf),
§§3 to 5 read; [Ziebart et al., 2008](https://ai.stanford.edu/~amaas/papers/amaas_aaai.pdf),
background and maximum-entropy formulation read.)

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
| **lit** | Without substantive restrictions, one episode does not uniquely identify a maker's reward and planner | **SUPPORTED (lit, READ: Armstrong and Mindermann, §§3 and 4.1).** This does not imply that every bounded candidate family requires multiple artifacts; the constructed examples and the human value-recovery question retain their separate scopes |
| **lit** | Observations alone uniquely identify reward jointly with an unrestricted unknown planner | **REJECTED (lit, READ: Armstrong & Mindermann, §4.1 and §7).** Policy compatibility alone leaves reward unconstrained; substantive priors supply assumptions beyond observations. This does not rule out useful narrowing within a restricted family |
| **G61** | An explicit competence estimate improves goal recovery | **OPEN.** If yes, the "fatal unknown" is an input |
| **G138** | The impossibility construction, reproduced exactly, then relaxed with the three human priors one at a time | **RECREATED+NARROWS (test-side toy, L60).** The degeneracy reproduced at exactly 0.5/0.5; the bounded human-shaped family alone narrows the posterior twentyfold, known near-optimality alone barely doubles it, both together fortyfold, holding under noise. Finite-data posterior narrowing in this seven-state toy family, not asymptotic convergence, unique identification, or historical recovery from artifacts |

**State of the section's claim.** Observational non-identifiability and useful narrowing under
substantive priors are compatible. The bounded toy family raises posterior mass twentyfold;
combined with known near-optimality it raises mass fortyfold while remaining far from certainty
(G138, L60). That supports finite-data narrowing in one constructed world. It establishes neither
asymptotic convergence nor recovery of a person's historical process or values; indistinguishable
processes still require an equivalence class or posterior. Which human constraints improve
prediction without introducing false certainty remains the empirical question. Confidence: one
bad test away for the toy narrowing; untested, logic only for the human-artifact extension.

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
