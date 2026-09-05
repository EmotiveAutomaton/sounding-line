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
| **proximal goal** `G` | what the maker is locally trying to accomplish | episode-local |
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
| **L-tier2** | Values need many artifacts; a goal needs one, because they live at different timescales | **SUPPORTED (test), indirectly.** Every single-artifact values attempt failed; every within-maker multi-work design worked (7.6× and 2.05× chance) |

**State of the section's claim.** The object table is definitional, and its three distinctions
(expertise against process, external against maker-interpreted context, drives against values)
are identifiability constraints on the reconstruction rather than claims with evidence: none of
the three has yet been isolated by a clean designed comparison, and Stage 7's factor worlds are
the first construction that varies them separately behind a boundary the reader cannot cross.
The table's load-bearing asymmetry, that the third target is a different timescale of thing,
keeps the project's most consistent indirect evidence behind it: nothing has ever recovered
values from one artifact and everything multi-work has found signal, which is exactly the
pattern the timescale column predicts. The expertise row now carries the walkthrough's sharpening: the
shared language of a domain is the largest part of recreation and not the whole, so a reader that
cannot produce the standard process has no ruler for the maker's share, which is what Stage 8's
expertise gate measures before any reading claim. Confidence: the timescale asymmetry is one bad test away,
resting on convergent nulls rather than a designed comparison; the identifiability constraints
are untested, logic only.

## §2. Forward generation and inverse recovery

What the maker generates, what the artifact preserves, and what the reader reconstructs are three
different things, and the theory has to keep them apart. A minimal generative account, held loosely:

    C_m,t = phi(C_ext,t, B_t, K_t)       maker-interpreted context
    A_tilde,t = afford(C_m,t, B_t, K_t)  actions the maker believes are available
    G_t = f(V, D_t, C_m,t, alpha_t)      the locally governing goal
    a_t ~ pi_K(a | A_tilde,t, G_t, H_t)  one action through the expertise transition model
    tau = (a_1, ..., a_T)                the realized process path
    K_t+1 ~ L(K_t, E_t, alpha_t, C_m,t) + epsilon_t
                                         lossy consolidation into later expertise
    O = h(tau, C_ext,1:T)                the medium's lossy artifact record

    reader R approximates q_R(G, tau, V, D, K, H, B, A_tilde, C_m | O, C_ext)

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

The proximal goal is therefore an artifact-level purpose, the reason the resources were spent, and
it is stable across the artifact; what moves are the subordinate goals that stay aligned with it.
The K-family pull ordering that Stage 7 supplied and scored as the goal is a derived variable, a
preference over move types that the purpose and the law produce together, and not the goal itself;
Stage 8 rebuilds the goal as a purpose and scores the pull ordering beside it.

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
continuation, the next edit, stopping, and the changed-context choice. A label whose realization
moves none of these has not been cashed, however insightful it sounds.

**A short mental-state label is a pointer, not the reconstructed maker state.** Its operative
meaning must be re-centered in the whole artifact, context, and possibility space until it
entails a distribution over the maker's remaining decisions. Different descriptions may realize
the same predictive state, and the same words may realize different states for different
makers; a longer rationale does not solve this by itself. The representation may be language,
structured slots, a program, or a latent vector; what earns credit is prospective constraint
on a hidden continuation, next edit, stopping decision, or changed-context choice. Stage 6
attempted to instrument this rule, but its hidden dependencies voided the interpretation
(M-S6). The rule remains a prospective criterion, not a claim that language is the required
representation of the maker state.

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
| **K04-S7** | A bounded reader can USE a complete supplied executable maker state (context, beliefs, law, maker context, subjective action set, goal, residue) to predict the next feasible action better than a frozen common-domain model | **COUNTEREVIDENCE on both admitted readers (test, L335), 48 paired worlds behind the clean-room boundary.** SmolLM2 −0.46 [−0.74, −0.18] and Qwen2.5-1.5B −2.62 [−3.42, −1.82] nats against the domain model, where the capsule solver executing the same bytes equals the exact oracle on every world (+0.63 over the domain model); the boundary is state use, not supply; the size ladder answers for four readers from 0.5B to the 9B route, every one under the domain model (−1.66, −2.50, −3.10, −1.06; K16, L340) and the solver's own line printed beside the state helping none of them, so the boundary is not a small-model artifact within this family and readout; repeated on the A family with the joint arm (A16, L349) the ladder has the same shape (−1.03, −1.64, −3.11 to 3B, −0.55 [−1.63, +0.36] at the 9B route) while goal recall rises with size to 0.67, so size buys proposal quality and not state use |
| **K-S7** | Some single true factor (context, action set, law, belief, goal), or the whole state rendered in language, lifts the reader over the domain model; a reader given a swapped belief or goal follows the oracle's reversal | **COUNTEREVIDENCE on every rung and both readers (test, L336), 48 to 74 paired worlds.** Each single factor leaves SmolLM2 a third to two thirds of a nat under the domain model and Qwen2.5-1.5B about three nats under; the prose rendering is no better than the executable one (SmolLM2 −0.34 [−0.68, +0.03] VALID_NULL, Qwen −3.30); where the swapped belief or goal reverses the oracle's expectation, the reader follows on 14 and 5 percent of pairs (K09, K10) |
| **X10-S7** | The language-state reader is invariant to paraphrase of the supplied state and moves under a meaning change | **COUNTEREVIDENCE, the attack fails (test, L336).** Total variation 0.57 under paraphrase against 0.59 under an inversion of the belief and goal statements, on 48 units; the reader's response to the supplied text is a response to surface, so its language-state claims close (the semantic-invariance question Stage 6 voided at M15, now measured with the leak closed) |
| **KI-S7** | With every factor but one supplied, the joint reader (proposals executed through the law) infers the withheld goal or belief and keeps the prospective gain | **NARROWED (test, L337), 48 and 66 worlds.** The joint arm returns to the domain model's level with the goal withheld (−0.00 [−0.21, +0.22] SmolLM2; −0.15 Qwen) and clears the floor for SmolLM2 with the belief withheld (+0.29 [+0.07, +0.51], three quarters of the way to the true-state solver), half a nat to two nats above the direct reader, and with the belief withheld both readers clear the floor once their split-line answers are parsed (the tolerant-grammar rerun: SmolLM2 +0.29 [+0.05, +0.50], Qwen +0.36 [+0.13, +0.58], 0.73 and 0.92 of the way to the true-state solver); but the goal is in the candidates one time in four (R01, L341: 0.23 against the 0.5 bar that opens selection), the belief in 39 percent of worlds, and the reader follows the oracle's belief reversal on 1 of 14 twin pairs: the gain is the law's execution of the supplied factors under a proposal that is wrong three times in five; asked for the subjective action set with the context derived (K13, L338), the readers' proposed sets contain the truth in 5 percent of worlds and the arm's full commitment to them lands −5.0 [−7.4, −2.6] and −11.5 [−14.1, −8.9] nats under the domain model: the maker-relative possibility space is not computed from its determinants; asked for the maker context with the beliefs supplied (R10, L343), Qwen's proposed context improves the changed-context choice over the domain model by +0.59 [+0.31, +0.90], which is exactly what copying the visible brief with accurate beliefs gives (−0.03 [−0.10, +0.02] against that rival, itself the oracle here) |
| **KL-S7** | The expertise law is recoverable from process evidence: by exact selection among supplied candidate laws, by a law learned from a few demonstrations, or by a reader's proposal | **SUPPORTED FOR THE TWO PROGRAM ROUTES, NOT FOR THE READERS (test, L339), 48 worlds behind the clean-room boundary.** Exact selection +0.59 [+0.34, +0.84] over the domain model with 0.52 of its mass on the true law; a law fitted from two demonstrations +0.57 [+0.31, +0.85], indistinguishable from selection (−0.02); the joint reader realizes a proposal on 16 of 120 rows (the readers echo the candidate tables in view) and lands at +0.17 [−0.06, +0.40] and at the domain model; the Stage 6 survivor (supplied-law selection as system identification, L330) replicated with no privileged call; and the learned law TRANSFERS (R09, L342): fitted from three earlier episodes and executed on an untouched one it lands +0.64 [+0.22, +1.12], within a hundredth of the oracle, while the joint reader proposing the law from the same demonstrations with no table to copy clears the floor on Qwen (+0.56 [+0.14, +1.03]; SmolLM2 +0.21 [−0.08, +0.53]), the one reconstruction rung a reader passes on its own proposals; the confirmation freeze took the learned law as its first claim and B01 replicates it on untouched lineages (+0.62 [+0.25, +1.02] over the domain model, 51 worlds; the readers inconclusive there, +0.10 and +0.26), the run's one confirmed effect so far, a program's |
| **RJ-S7** | The goal and the belief can be inferred jointly without one collapsing into the other, and the joint inference keeps the prospective gain | **NARROWED (test, L344), 60 worlds.** No collapse: the goal is in the candidates in 23 percent of worlds and the belief in 34, about as often as alone, with the factor marginals apart; no gain either: the committed pairs leave SmolLM2 at the domain model (−0.17 [−0.47, +0.13]) and Qwen 1.4 nats [0.4, 2.7] under it, the goal-by-belief cells running from +1.9 to −8 nats where a confident wrong pair is executed; with the law withheld and no demonstrations (R12, 108 worlds with law twins), Qwen names the law's shape in 56 percent of worlds and gains a tenth of a nat that does not clear the interval (+0.11 [−0.33, +0.50]; SmolLM2 +0.04), the executed shape being a standard table rather than the maker's numbers, and a swapped law that reverses the oracle's expectation moves neither reader (0 of 8); cold (R13, L344), with the goal, belief, law, and residue proposed and the context and action set derived, the realizing reader is 1.3 nats [0.4, 2.6] UNDER the domain model (COUNTEREVIDENCE) and 1.6 [0.2, 3.0] over the direct reader; SmolLM2 realizes 15 worlds of 60 and sits a third of a nat under (inconclusive); Qwen's candidates hold the law's shape in 68 percent of worlds, the goal in 42, the belief in 7: the readers name the law and not the belief, and the arm's commitment to the wrong set costs more than ignorance; on the stop the domain model's hazard is within 0.05 nats of the oracle and every reader arm is under it (P05), and on the boundary type the executed state's stop terms name the wrong reason with full commitment, Qwen at the log-score floor on 8 worlds of 10 (P06, L344); over the whole withheld tail the joint arm is a nat under the domain model summed over up to four events, the loss spread across the events rather than sitting at the queried one (P09, L350), and the ladder's fresh draw of 29 worlds with longer tails agrees on every line (rung 4, pooled −0.94 [−2.02, +0.18]); the cold rung itself on a fresh draw of 60 worlds lands at the domain model (SmolLM2 −0.10 [−0.31, +0.13], Qwen +0.03 [−0.39, +0.43]), so its counterevidence narrows to "at or under the domain model, by the draw", nothing above it on either draw |
| **RG-S7** | Maker familiarity helps where cold reading fails, independently of domain expertise | **NARROWED (test, L345), 40 worlds crossed with three regimes.** No: two earlier episodes by the same maker leave the failing reader failing (Qwen −1.75 [−3.41, −0.44] against the domain model, committed on every world) and the reader near the domain model near it (SmolLM2 +0.02 [−0.24, +0.28]); the domain's generic law in view brings Qwen to the domain model only by silencing it (the law answered in prose on 35 worlds of 40, the set unsolvable) and makes both direct readers worse; beside R09 the demonstrations carry the law alone; R15 (L345): the generic law halves the joint arm's candidate entropy (0.08 against 0.16 cold) while its calibration stays at chance in every regime (expected calibration error 0.44 to 0.50), certainty moving with the regime and correctness not |
| **EQ-S7** | The reader preserves observationally equivalent maker models and chooses a useful next discriminator | **NARROWED (test, L346), 60 worlds, descriptive.** Abstention does not track the prefix's ambiguity: the joint arm withholds on 59 percent of the equivalence cases and on 73 percent of the singletons, within noise of each other, and SmolLM2's abstention is failure to propose on 36 worlds of 60; the discriminator measure is 1.0 against the reader's own greedy choice by construction and is an instrument gap for the next stage; the joint arm's confidence is anti-informative (P10, L346): expected calibration error 0.51, its most confident tenth the worst at any coverage, calibration worse the more evidence the prefix carries; the equivalence attack X14 fires on the same figures (false abstention 0.73 against its ceiling of 0.5), so the run's own criterion records that the readers do not preserve the class |
| **RV-S7** | The joint reader revises mutually constraining factor hypotheses as the prefix grows, and the revision changes what it predicts | **NARROWED (test, L347), 30 worlds.** A sequential particle arm that re-weighs, resamples, and re-proposes candidate states at prefix checkpoints predicts what the one-shot joint posterior predicts (+0.02 [−0.16, +0.21] nats; Qwen within four hundredths), because the readers propose one candidate set on 48 worlds of 60 and nothing ever collapses or is re-proposed; revision is testable only for a reader with candidate breadth, which neither has at this scale |
| **AC-S7** | At matched evidence and measured compute, structured computation (a realizer over proposed maker states) beats direct inference-time computation | **NARROWED (test, L348), 40 cold worlds, seven arms.** Every structured arm beats the direct reader (the joint arm +1.5 nats [+0.4, +2.5] pooled; the five conformance-reproduced rivals +1.4 to +2.1), and none beats the domain model: the direct reader is 2.1 nats under the prior, the arms that realize on every world sit at it or a nat under it, and the arms that rarely realize fall back to it; no arm's gain per unit of compute exceeds five hundredths of a nat; the two conformance cells of the day before say the same (L355, L356): the adaptive expansion adds factors at one rate whether a variable is missing or not and costs 0.22 nats against the joint reader where the world is complete, and the synthesized agent model validates on 28 of 30 worlds for one reader, beats the direct reader by 2.86 [1.50, 4.31] and sits 0.72 under the domain model, the effect the freeze selected for confirmation; B02 confirms it on untouched lineages against the direct reader (+3.59 [+2.34, +4.78] on Qwen, pooled +2.19) and finds it counterevidence against the domain model there (pooled −0.32 [−0.54, −0.06]), so the run's second confirmed effect reads: synthesis beats free text and not the prior |
| **TT-S7** | The maker's record supports a dated present focus plus an uncertain historical mixture (two timescales), and the dates and order of earlier episodes inform a later choice beyond an aggregate profile | **NARROWED (test, L354; V04 to V06, programs only).** A mixture over dated episodes and a forced point date predict the present episode alike (−0.01 [−0.09, +0.07]); the dated, ordered, and aggregate views of earlier episodes predict a later episode alike (valid nulls); for a later costly choice the dated trajectory beats the domain model (+0.42 [+0.05, +0.84]) and the law-less solver (+0.48) because it carries the law, and beats the aggregate by five hundredths under the floor: the record's two timescales are not separated at this construction's drift, and its history informs through the law alone |
| **J05-S5** | The standing preference inferred from one episode predicts the maker's choice in a second episode under a stated new goal, beyond habit, topic, and last-goal baselines | **COUNTEREVIDENCE (test, L280), 256 worlds.** −0.73 nats [−0.93, −0.55] against the topic baseline; the reader half a nat under uniform; the preference recovered in a third of worlds; the exact ceiling a quarter of a nat above uniform. Second contract (L293, two readers, the ceiling raised to 0.68 above uniform): −0.26 against the topic prior, both readers under uniform |
| **P-S8** | Prediction of the next move tests expertise first; the maker's share is the residue, the events the standard process does not expect, and a reader that holds the standard process localizes its surprise on those events | **OPEN, the precondition met (test, L359).** Both trained readers pass the expertise gate, predicting the next move on held-out population and maker-free purpose worlds above the domain model (+0.19 [+0.003, +0.39] and +0.13 [−0.06, +0.31] nats; the band −0.05; the oracle's gap +0.52), with monotone training curves and the integrity block whole; the generation half FAILS on both (E04, L360): sampled from their own distribution the readers write a header-illegal move in a quarter to two fifths of their logs and sit under the population's 20th percentile, so no reader is admitted and the localization cells run as diagnosis; at four times the sample (L369) the gate passes wider (+0.24 [+0.13, +0.36] and +0.20 [+0.09, +0.32] on 306 units) and the anti-alignment tightens (AUROC 0.36 and 0.39 on 334 worlds); as diagnosis (L361) the trained gain vanishes on a law family the readers never saw (−0.005 and −0.018 nats against +0.19 and +0.13 on the seen family), so the installed expertise is family-specific; and the localization half, measured whole as diagnosis (L362), is ANTI-aligned: both readers rank the maker's divergent events as less surprising than ordinary ones (AUROC 0.34 and 0.37 against the domain model's 0.56) on every task shape, the true purpose supplied moves the residue by under 0.01, and the first explanation fires at the most divergent event under chance, so a surface-trained reader's surprise points away from the maker; the purpose route is inert on the same readers (L363): the proposed purpose executed through the reader's own forward model is null or worse against the plain reader (−0.03 and −0.08 nats) and the true purpose adds +0.04, while both readers sit a nat over the domain model on the tail events either way, the likelihood face of the same surface expertise, and at four times the sample the proposal HURTS on both readers (−0.09 and −0.06 nats with intervals below zero, L370) while the true purpose adds +0.05 to +0.07; and the pull ordering is the easier goal object for both readers by 0.24 and 0.15 of recall (L364), the frontier probe naming the purpose on one world in six and losing 1.8 nats using it; and the purpose readout does not track meaning (L365): recall survives a paraphrase and rises under a meaning change on both readers, so the purpose route on these readers is closed from every side |
| **MS-S8** | The maker's share is small by nature and lives in the divergences from the standard process, mostly the proximal goal and the record of earlier goals that diverged; it widens along the artful gradient | **OPEN.** Stage 8's tail contrast (the events where the exact state diverges from the population process) and the artful-gradient construction (AG) measure the share's size per task shape before any reader is tested. As diagnosis on the surface-trained readers (L366), nothing accumulates across a maker's artifacts: three earlier artifacts in context move the fourth's surprise alignment by under 0.02 on both readers, every cell under the domain model; recall of the law and the residue is flat at chance across N and the maker model of three artifacts is worth nothing against the reader without it (L367), so the accumulation trunk closes as diagnosis |
| **J03-S5** | Along the stream the reader's records become useful in a diagnostic order and a contradiction lowers its confidence | **NARROWED, descriptive (test, L264).** The plan record is reached last and most reliably; the preference record is never useful in two thirds of worlds; after an exact contradiction the reader is more confident and less right in 44 to 62 percent of worlds; on two readers with equifinal plans present the never-useful shares rise to 0.56 to 0.74 and overconfidence sits at half (L292) |

**State of the section's claim.** The generative account remains a framework rather than a
finding, now with its objects kept apart: expertise as the transition model, process as the
realized path, the maker's context and subjective action set derived through belief and
expertise, and the composition claim in its restated form, expertise distorting the available
possibilities under context, with drive commonality named as the assumption that keeps the
distortion decodable. Both composition rows are open. The single behavioral fact here cuts the
right way for a joint account, since a staged pipeline would care about stage order and the
simulated reader's answer does not move when the order changes; the distortion story's weakest
named part is attention, flagged by its own author. The products the walkthrough insisted on
keeping apart have one direct measurement: a small reader recovers a maker's appraisal and its
intended audience response above the floor and crossed, thinly, confirmed on a fresh split
(A01-S4), and not on a notice register, where the same reader family gives one answer per
question whatever the world (A01-S5). The triple's first direct test of goal against standing
preference finds the reader collapsing them: told the goal, it still reads the goal's axis as
the chooser's disposition in two thirds of worlds while recovering the plan cleanly, on two
reader families (J01-S5); along the evidence stream it reaches the plan late and reliably, the
preference rarely, and does not lower its confidence at a contradiction the exact posterior
registers (J03-S5); its prediction of the hidden future choice sits under a uniform guess for
every variant, the one handed the true latents included (J02-S5); it does not see a maker's
note contradict the record (J04-S5); and the preference it infers predicts a second-episode
choice worse than the scenario's own prior (J05-S5). In these readers the dispositional product
is neither recovered nor used, the situational product is half recovered and unused, and only
the process product is read. Those Stage-5 failures keep their original scope: two reader
families, one construction family each, and the confound the walkthrough named. The Stage-6
tournament supplies no constructive comparator to set against them: its routes compiled
hypotheses through a realizer that read the hidden world, so the nat they cleared over direct
reading belonged to the privileged simulator, and what that block leaves standing is that an
exact selector among four supplied controller laws identifies the planted one from the prefix
where the label reader does not, which is system identification and not reconstruction (M-S6).
Whether a reader can use a complete supplied maker state, and recover one factor while keeping
the rest, is the Stage 7 ladder's question, asked behind a boundary the reader cannot cross,
and its first rung answers the first half for the two admitted readers: handed the whole
executable state, both predict the next feasible action worse than a frozen domain model
that knows nothing about the maker, while a program executing the same bytes reaches the
exact oracle (K04-S7). The boundary is therefore state USE, not state recovery or supply,
which is the same shape as the Stage-5 finding that a reader handed the true latents could
not map them onto a choice (J02-S5), now measured with the leak closed; and it holds at
every rung of the ladder: no single true factor lifts either reader, the prose rendering is
no better than the data, a swapped belief or goal that reverses the oracle's expectation
moves the reader one time in seven at best, and paraphrasing the supplied state moves the
reader as much as inverting its meaning (K-S7, X10-S7), so these readers answer to the
surface of what they are handed and not to the state it names, and a reader eighteen times
larger through another route answers the same way, a nat under the domain model with the
whole state in hand (K16, L340). Give the same readers a
program that executes the state and reduce their job to naming one missing factor, and the
gain comes back to the domain model's level or above it, without the factor being named:
the belief is in the candidate list two times in five and a swapped belief that changes
the oracle's expectation moves the joint reader one time in fourteen, and asked for the set
of options the maker believes open, given the beliefs and the law that fix it, the readers
propose a set that holds the truth one time in twenty (KI-S7). The realizer that the
maker-state rule needs exists, then, as a program handed the state; for these readers it is
not the reader, and the open question is whether a reader can propose a whole state that
program can use (the reconstruction trunk). The expertise law itself is in the evidence
for such a program: exact selection among supplied laws and a law learned by likelihood
from two demonstrations both clear the floor by half a nat, the Stage 6 survivor
replicated clean, while neither reader proposes a law when shown what one looks like; shown three of the
maker's earlier episodes instead, the law learned from them transfers to a new episode at
the oracle's level, and one reader proposes it well enough for the solver to use (KL-S7,
L342), the first reconstruction rung a reader passes on its own proposals, with every
other factor supplied. Asked for the goal and the belief together, the reader keeps them
apart and gets both wrong about as often as it gets each wrong alone, and its arm's full
commitment to a wrong pair is what puts it under the domain model (RJ-S7). Cold, with nothing
supplied, the same reader names the law's shape in two worlds of three and the belief in one
of fourteen, and the arm that executes its full proposed state is a nat and a third under the
domain model while a nat and a half over free-text prediction: the reconstruction claim
narrows to the regimes where the law is supplied or demonstrated, and what beats the direct
reader is the realizer, not the reader (RJ-S7, L344). Crossing the same worlds with the
maker's earlier episodes in view does not rescue the cold reading, and the domain's generic
shape in view silences the reader rather than informing it, so what the earlier episodes
carry is the law and what the cold reading lacks is everything else (RG-S7, L345). Where
the prefix leaves several maker models equivalent, the reader's abstention does not track
it, withholding on three singletons in four and on three equivalent cases in five, by
failure to propose rather than by judgment (EQ-S7, L346). And revising the candidates as
the prefix grows changes nothing, because on four worlds of five there is one candidate
to revise (RV-S7, L347): the readers' limit is breadth of hypothesis, not its revision.
Priced against free-text prediction at matched evidence, every structured architecture
wins, and priced against the domain model none does: structure buys back the direct
reader's losses by falling back to the prior or by executing a wrong state less badly
than free text guesses, and nothing beyond the prior (AC-S7, L348). The record's two timescales are
not separated at this construction's drift: a point date and a mixture over dates predict alike,
and what a dated history adds to a later choice is the law it carries, nothing beyond the
aggregate of the episodes (TT-S7, L354). Stage 7 closed at hour 15 with its instrument whole,
two program effects confirmed on untouched lineages, and no reader effect anywhere (L357): the
realizer is the result and the reader is not, at this scale and construction family. Naming
the intended
latent, or producing a coherent rationale, does not establish understanding, and neither
does possessing the complete state; the maker-state realization requirement stands as an
architectural proposal whose realizer, for these readers, is not the reader. The walkthrough after
Stage 7 rereads that result rather than softening it: the reader is the realizer, reading is running
one's own forward model of the standard process and attending to where the artifact departs from it,
and none of the Stage 7 readers held that process in the first place, so what they lacked was
expertise before it was anything about the maker; prediction tests expertise first and the maker is
in the residue (P-S8), which is small by nature and mostly the purpose and the record of earlier
purposes that diverged (MS-S8), both open; the reader that passes the expertise gate now exists (both
trained readers predict the standard process above the domain model, L359), and the same readers cannot write a legal log from a header (L360), so the precondition is half met:
prediction and production come apart, and the localization half of P-S8 is measured as diagnosis;
the first diagnosis (L361) says the installed expertise is the trained family's and not the process's,
since an unseen law family returns both readers to the domain model's level, and that one reader names
the purpose by the affordance route on half the worlds while neither holds two purposes open where the
prefix leaves two. The localization block then read whole (L362): the surprise of a reader trained on the
population's logs is anti-aligned with the maker's departures, ranking them as the least surprising events
in the log, and the purpose handed to it does not open the residue, which is what a surface-trained
expertise predicts and what a process-holding expertise would not. The purpose route confirms the
reading from the other side (L363): a purpose the reader proposes and executes through its own forward
model buys nothing against the reader without it, and the truth buys almost nothing, while the reader's
nat over the domain model on the tail events stands with or without any purpose, so the advantage the
training bought is the family's surface at the divergent events and not an inference about the maker.
Of the two goal objects the stage carries, the pull ordering is the more legible to both readers by a
wide margin (L364), which is expected of surface expertise: the pull shows in the log's section traffic,
the purpose only in tool-gated choices, so the goal object to carry forward is the ordering. The
purpose readout does not even track the artifact's meaning, since a meaning change raises recall on
both readers (L365), which closes the purpose route on surface-trained readers from every side. And the
record of a maker's earlier artifacts adds nothing on the same readers (L366): three earlier logs in
context leave the fourth's reading where it was, so the accumulation half of the maker's share waits, like
the rest, on an expertise that holds the process rather than the surface; the rest of that trunk agrees
(L367): law and residue recall stay at chance whatever the number of earlier artifacts, and a maker model
built from three of them predicts a new artifact no better than the reader without it. The ladder's
first rung holds both ends at four times the sample (L369): the prediction gain tightens and the
anti-alignment tightens with it, so the two are one fact about what the training installed. The purpose
route closes with a sign at the same rung (L370): a purpose the reader proposes and executes costs it
prediction on both readers, since the purpose it names is wrong more often than not, and the true purpose
returns little.
Confidence: the
Stage-5 reader boundary is one bad test away; the Stage-7 state-use boundary is one bad test
away (two readers, one construction family; the size ladder run on two families finds no size to 3B that uses the state and the 9B route within noise of the domain model); the Stage-6
architecture interpretation is instrument-dead.

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
