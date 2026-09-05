# Decision traces: what survives in the artifact, and how it is measured

> **Polish** and **depth** describe the decision target. Polish refers to the **subgoals that are
> directed at the reader**, and depth refers to the **subgoals that are directed at the problem
> itself.** The terms get conflated in casual speech sometimes, because sometimes the goal is itself
> attractiveness. In those cases we don't say a marketing image has a lot of depth, we say it has a
> lot of polish, and the lack of goal diversity outside user-directed polish implies a lack of depth
> as well. And there are deliberate and automatic forms of both. **You can deliberately and
> automatically apply both polish and depth.**

**Artifacts preserve decision traces along two independent axes: what the decision targeted, and how
deliberately it was placed. Across the artifact as a whole, those decisions may reduce to layered,
singular, or unrecoverable terminal values.** Polish and depth describe *target*; deliberate and
automatic describe *control*; flattened intent describes *terminal organisation*.

Current verdict, axis by axis. **The target distinction is coherent, and its definitional test just
ran inverted at first pass with a named confound; the control distinction is partially supported;
terminal topology is conceptually useful but instrument-dead or untested; and no direct scalar
measure of depth exists, which the program has stopped seeking in favour of choice-event
recovery.**

**This file owns** the artifact-facing consequences: which decisions leave traces, how those traces
differ, how they are measured. **It does not own** the latent architecture a model reconstructs
([`THREE_COGNITIVE_LAYERS.md`](THREE_COGNITIVE_LAYERS.md)), the three-way inference itself
([`THE_TRIPLE_INFERENCE.md`](THE_TRIPLE_INFERENCE.md)), or the reader's shortcuts
([`READER_HEURISTICS.md`](READER_HEURISTICS.md)). *(Renamed from `POLISH_AND_DEPTH.md` 2026-08-09;
the old name had become too narrow for a file that absorbed flattened intent and leakage.)* Per the
program (2026-08-09) this file is **primary**, owning choice-event recovery, depth against polish,
and the forced-constraint nulls.

---

# Part I: The canonical model

## §1. The coordinate system: target, control, and terminal topology are independent

**Three separate properties, previously conflated into one ladder:**

**1. Decision target.** *Polish*: recoverable decisions directed toward the reader, their attention
or their comprehension. *Depth*: recoverable decisions directed toward the problem, subject, or
artifact itself. Attraction and translation are subtypes of polish.

**2. Degree of control.** *Deliberate*: consciously placed. *Automatic*: habituated, not actively
held. `emblematic` and `leaked` are the **affect-specific** versions of this distinction, not
synonyms for all deliberate and automatic behaviour.

**3. Terminal-value topology**, a property of the artifact as a whole: *layered* (decisions serve
several partially competing terminal values), *flattened* (many decisions reduce to one), or
*non-invertible* (readers cannot recover a coherent terminal organisation at all).

The control axis cuts across the target axis:

|  | deliberate | automatic |
|---|---|---|
| **reader-directed** | chosen attraction and translation | aesthetic habits, teaching habits, seductive details |
| **problem-directed** | explicit reasoning, case selection, epistemic foraging | applied expertise, facture, routinised process |

**This resolves a standing contradiction. Polish is not necessarily conscious, and depth is not
necessarily automatic; those are predicted tendencies, not definitions.** It also shows why a
simple subtraction cannot define depth, since aesthetic and teaching behaviour leave automatic
shadows, while epistemic foraging is consciously held but problem-directed. The categories do not
subtract cleanly. And it names the estimator honestly. **Applied expertise is a *source* of depth,
not the definition of depth; residualisation is a proposed estimator, not the ontology** (Part III).

**The adopted definition, standing over the whole file.** Depth is the recoverable density of
problem-directed choice structure embodied in an artifact, conditional on domain, brief, medium,
and forced constraints. The conditioning clause is load-bearing, since a constraint the medium
forces is not a choice, and a brief the maker was handed is not their goal.

**And the unit of analysis is the decision event, not the artifact scalar (adopted 2026-08-09).**
A decision event carries five things. Its target, the alternatives that were available, the choice
made, its dependencies on other choices, and its context. For each recorded event the measurement
question is whether the finished artifact lets a bounded reader recover the actual choice better
than context alone and better than matched false alternatives. Only after event recovery works do
events get summarized, as amount (how many independently recorded choices are recovered), breadth
(how many distinct problem dimensions they constrain), integration (how many true dependency
relations among them are recovered), and calibration (how often proposed recoveries are right,
reported separately, never folded into depth). The denominator is declared choice opportunities or
revision events, never words. Per-word density recreates the length trap that killed the first
generation of measures. These summaries describe recovered structure. They do not estimate total
cognitive work or authorship share. Dependencies can show how one choice organized others, but
the number of dependent events is not itself a conversion rate between human and model
contribution.

> For iterative mixed control, you'd almost be able to see based upon who made the other's job
> easier. Like the cognitive preemption, again, because someone else made the decisions for you
> ahead of time, and you kind of just go with the flow. Either one of them could actually drive it.

A decision event is a recovery unit, not an equal-weight cognitive atom. Event count, formation
difficulty, trajectory leverage, episode control, dependency structure, and trace support are
different quantities. A thesis can pre-empt a large downstream search space while fifty
punctuation events remain separately visible; a later editor can reclaim control by rejecting or
rebuilding the upstream structure. No human/model contribution ratio may be computed by counting
recovered events as exchangeable units.

**Event density and causal reach are orthogonal.** Implementation often contains many more
separately recordable choices and may therefore leave more recoverable traces. A primary-goal,
framing, or attention-setting event may be rare while changing the feasible set for a large
downstream region. The director or auteur conjecture is a prediction about that distribution over
the event graph: few upstream events with wide downstream scope can organize many lower-level
events. Wide causal scope does not guarantee artifact visibility, and numerous visible execution
events do not by themselves identify control.

**Mixed production is a network of acceptance** *(the 2026-08-21 pass)*:

> Collaborative work is a network of acceptance. Everyone involved gets to pass judgment on
> everyone else's work a little bit, and the human decision may be recognition and integration
> rather than generation.

> Who made this part is a question about the artifact. Sounding Line cannot read records. The text
> carries very little of the change of hand, and detecting it is the work of a full human brain with
> expertise and all the context it can get; you would need multiple artifacts from the same creator
> and a powerful model.

*2026-09-04 walkthrough; lightly cleaned transcript.*

The record result of Stage 7 is therefore a program result about ground truth, and the artifact
claim stands as a claim that is power-bound: several artifacts by one maker and a stronger reader
than any admitted so far.

Mixed production is therefore represented as a directed event graph. An event may
propose, select, ratify, veto, integrate, repair, reject, or accept another event; the
same participant may occupy several roles, and one event may have several parents.
Upstream structure can make downstream work cheap, and downstream ratification can
accept that structure or rebuild it, so surface volume and equal-weight event counts do
not identify control. For mixed work the stable object is the complete interaction
trajectory, whose resulting structure may not belong fully to either participant. The
event schema carries these optional fields where interaction records exist:

| field | purpose |
|---|---|
| `actor_id` | participant or tool responsible for the event |
| `event_role` | propose, select, ratify, veto, integrate, repair, reject, accept, execute |
| `parent_event_ids` | events this one acts on or depends on |
| `alternatives_available` | candidates actually available at the time |
| `accepted_by` / `rejected_by` | later ratification or veto |
| `downstream_scope` | which later choices became easier, impossible, or unnecessary |
| `trace_support` | artifact or record evidence supporting the event |

The event graph is the ground-truth object where interaction logs exist
(`soundingline/process_record.py` is the enforced form). Any downstream scalar must
declare its aggregation rule and is never a human/AI decision ratio.

> You can variably reveal yourself or cover yourself up through how you choose to express, across
> several artifacts.

*2026-09-04 walkthrough; lightly cleaned transcript.*

A construction note for the accumulation trunk: how much of the maker's residue an artifact expresses
is a per-artifact variable the maker controls, so a maker series carries a reveal parameter beside
the law and the residue.

**Global coherence does not identify a director.** A central director, a shared brief, common
training and conventions, institutional filtering, an editor, or a genuinely distributed
cognitive system can produce similar dependency structure in the finished artifact. A reader may
posit a directing hand, but historical attribution requires role-specific records, interventions,
counterfactuals, or longitudinal preferences that predict which upstream choices that participant
controlled beyond the shared-brief rival. In their absence, the honest output is an equivalence
class of contribution graphs.

> It is part of what expertise looks like as people work out a shared language in a given goal
> space. They're allowed to make more precise elaborations within their own exploration of that
> space and still be understood.

*2026-08-27 walkthrough; spoken wording lightly reconstructed.*

**Shared conventions can support new local choices while carrying inherited organization.** A later
maker may preserve an earlier goal and change its realization. This can make communication easier
while making individual origin harder to identify. Inherited structure, present causal control,
credit, and historical attribution are different questions; none is settled by counting visible
elaborations.

The essay already names polish's first half. Aesthetics is *"the honeypot... the word for how much an
object forces you to stare at it."* **Polish is honeypot density plus scaffolding density. It is not
a synonym for quality and it is not a synonym for AI.** A ten-item reading sample populated all
four corners of the polish × depth grid, including *"thick on top and just empty beneath."*

**And depth is domain-relative** *(moved from the reader-heuristics file 2026-08-09; it is a
property of the target, not a reading strategy)*:

> If you hold the domain, medium, constraints, and the choice opportunities afforded through the
> expertise as a result of those properties constant, then **depth is predicted to be more stable.**
> Domain shifts are one big reason it may move, for sure. But there are other possibilities.

The sharpest definition in the project, because it makes depth a **relation** between writer and
the conditions of making rather than an attribute, with a falsifier attached (*depth moves when
those held conditions move, domain first among them*), and with the consequence that explains the
corpus problem. **A relation cannot be measured by varying one side**, and every artifact-direct
measure that died, died reading artifacts alone.
**(HH-10:** depth measured on one maker moves when the domain moves, with the other held
conditions as further candidate movers. **OPEN (the L18 pilot measured the corpus gap instead),
blocked on the one-maker-many-kinds corpus its own definition demands**, the same corpus the
values thread keeps arriving at.**)**

**An unusual act is epistemic exploration only through its outcome channel** *(the
2026-08-30/31 passes; provenance in `docs/design/archive/PHASE_2_4_STAGE_6_THEORY_ERRATA.md`)*:

> If you are going to explore, you need to explore all the way. You need to see the result one way
> or another.

*2026-08-30 assessment; spoken wording lightly reconstructed.*

**An unusual action is not yet a trace of epistemic exploration.** The exploratory account
needs an outcome-sufficient commitment or an escalating probe, an observation capable of
reducing the maker's uncertainty, and later stopping or policy change consistent with what was
learned. The rivals have their own mechanics: an ordinary error may be repaired before it
reveals an outcome; a familiar technique used in the wrong context may run FARTHER because it
is weakly monitored; a hidden artifact-level goal should integrate the unusual action with
wider structure. These rivals can remain observationally equivalent in a finished artifact, in
which case the trace stays `indeterminate`. The Stage-6 F track attempted to instrument this
standard in constructed worlds, and the attempt is void as evidence: its outcome read inherited
the hidden future and the generator's laws through the shared predictor, several of its
questions reduced to one planted statistic (F02, F03, and F09 were one statistic under three
names), and it supplies no evidence that a reader separates exploration, error, habit, and
hidden goal. The outcome-sufficient exploration rule remains a classification standard and a
ruling, never a result, and not a claim that unusual action implies exploration.

No direct test of the coordinate system itself exists; its components are tested below.

## §2. Reader-directed traces: attraction, translation, and movement

> The pieces that the human is putting in **voluntarily, alongside** – the polish is made up of **two
> things, not just one.** The first would be the **attractiveness**: how much you can make the
> artifact eye-catching. And the second is... **everyone tries to make things understandable to other
> people. We add labels and tags if we're an engineer. We build in metaphor as an artist that's
> understandable across domains. I think that's the second piece.** We also all layer in this
> **translatable** layer.

> It was useful mentally to imagine polish as something on top initially, but it is more **a
> concurrent sub-goal that is sometimes activated**, an additional motivation that is added in.
> Sometimes your attention may deform things, or your expertise may simply bend you in that
> direction as part of the immediate proximal goal, and the trajectory mapping you have available as
> a result of your context.

|  | what it is for | what it looks like |
|---|---|---|
| **attraction** | being *attended to* | contrast, rhythm, the punchy opener, the confident frame, the acronym that signals membership |
| **translation** | being *understood* | labels and tags, section structure, worked examples, metaphor that carries across domains |

The two have different causes and different predictions. Attraction is a performance aimed at a
specific audience on a specific occasion; translation is aimed at comprehension, and a maker who
stops performing does not usually stop labelling. Translation is the *bard*'s second motivation
([`READER_HEURISTICS.md`](READER_HEURISTICS.md) §8) made measurable. His own doubt is the load-bearing
test. *"I don't know if they're extricable or not."*

**Movement within an artifact** is the other reader-directed prediction:

> I'd imagine that their **attentional focus moves around as they spend a longer amount of time on a
> given piece.** So you'd expect them to prioritize different sub-goals, and that would be
> observable as the readable goals moving throughout the paper. **Sampling at different points can
> therefore get different residuals out of their particular expertise and latent goal space.**

> The polish variance is obviously an untested hypothesis, but it might be worth considering from an
> **order-sensitive or event-level measurement.** There's some general description of these
> behaviors, starting with the user-directed goals, the polish-type goals, and then slowly
> transitioning as that spreads across. Part of authorship is **learning to control that
> appropriately through the layers of expertise**, in terms of author skill at least.

His readings contain both directions, *"thin to start but got thicker as it went down... but it
stayed equivalently thick throughout on the bottom"*, so what is stable is the **asymmetry, not the
direction**. The observed movement has at least three candidate causes: focal attention
relocating, the same background goals finding different opportunities for expression, and genuine
goal drift. A surface shift does not identify which occurred. The measurable claim is
order-sensitive movement in recoverable constraints; the motivational interpretation remains open.

**Superseded in scope** by the three-candidate distinction above; kept as the hypothesis source:

> **Depth is stationary within an artifact; polish is not. Polish variance across an artifact is a
> maker signature; depth variance is not.**

| # | hypothesis | status |
|---|---|---|
| **PD-1** | Depth-side quantities show smaller between-position variance than polish-side quantities | **VOID as operationalised (test, L53/L55), with the route closed in principle.** The first valid pass ran inverted; the matched null then showed the inversion was per-window sampling noise, and the algebra shows dispersion statistics cannot measure movement at all, since variance is order-invariant and the shuffle ratio cannot exceed one for any data. A movement claim needs an order-sensitive statistic or the program's event level. Not a negative result about the claim; the instrument class was wrong for the question |
|   | | *(instrument history: v1 scored zero essays on a mis-sized cache and verdicted anyway; v2's z-scored variance was 1 by construction; v3 gated and ran inverted; v3b's matched null exposed the in-principle void and one of its own verdict branches as unreachable)* |
| **PD-33** | Polish-side features are more essay-bound than depth-side features at fixed topic, and the boundness follows the author | **SUPPORTED (test), decomposed (L55, L57), replicated on books (L71) and across window sizes (L89).** Between-essay share 20% against 8%, and the decomposition lands MAKER: author shares 0.262 against 0.174 (p = 6 × 10⁻⁷) while draft-within-author shares are small and identical (0.04 apiece, p = 0.98). Polish-side variation carries *who*, on 86 authors at fixed topic; draft stage carries almost nothing on either side. On the 10-author book corpus the polish side carries three times the depth side's author-bound share (p = 3 × 10⁻⁷ at the 80-word window, p = 4 × 10⁻⁶ at the 40-word), with author and topic confounded there by construction, so only the contrast transfers. The hierarchical refit (test, L142) confirms the reading with author as a random effect: the polish composite carries ten times the depth composite's author-level variance (intraclass correlation 0.29 against 0.19 with the depth component at the estimation boundary), so the claim survives proper clustering rather than resting on pooled windows. Two corpora, two window sizes, one mixed-model confirmation, no exceptions |
| **HH-3 / L39** | The reader's own affective series moves more within human artifacts than machine ones | **DEFLATED TO REGISTER PLUS FAMILY (test, L39 then L101), and at four families the instrument DISSOCIATES from the artifact-side sign (test, L105).** Register-matched, book-level trajectory mobility belongs to qwen-instruct alone (parity with books, p = 0.58); the other three families sit flat (down to p < 10⁻⁴; the llama-instruct cell is n = 3 and permanently underpowered, the top-up having failed at two length floors because the model cannot write chapters that long), while on the artifact side three of the same four families rise. The provenance reading is dead; the lockstep-with-the-sign reading died at its own extension; what the reader's trajectory tracks is a different family structure than the surface trend, and the two instruments report separately from here |
|   | | *(this row's history is a first-pass human-moves on 08-09, deflated to family on 08-13, and the lockstep reading killed by the four-family arm on 08-14)* |
| **S-6** | Practised polish decays faster than depth | **SUPPORTED (sim)** at 6.5×, with synthetic polish **flat** |
| **PD-34** | Polish-side features carry positional structure while depth-side features are stationary, the movement claim in the order-sensitive form | **SPLIT BY CORPUS AND BY WINDOW EVERYWHERE IT IS TESTED (test, L74/L89/L113/L116), ruler-gated.** On books at the 80-word window the asymmetry is large (polish z 0.52 against 0.013, p = 1.3 × 10⁻⁵); at the 40-word window it does not transfer (p = 0.15); short essays flat at both. On machine fiction the wide window drew a clean post-training split (instruct cells mobile, distill cells quiet, both bases) and the 40-word window scrambled it into a nominal base split, so neither alignment is a lineage law; the one cell mobile at both windows is qwen-instruct (p = 5.3 × 10⁻⁴ and 7.8 × 10⁻⁴), the same single model the reader-side instrument isolates. And the machine control reversed the human-side interpretation, see PD-3 |
| **PD-3** | Machine artifacts show flat polish across position, with no maker to tire and no register to drift toward | **REVERSED TWICE OVER (test, L89/L90), split by family at power (test, L97/L100), the 2×2 resolving the split into one model's exception (test, L103), and the window sweep qualifying it further (test, L105).** What is window-robust: both llama-base cells RISE at 80 and 40 words (up to p = 10⁻⁴). What is not: the qwen-instruct rise weakens below significance at 40, and the lone human-direction decay (the qwen-7B reasoning distill) vanishes at 40 exactly as the books decay did. Flatness is dead; rising polish is the machine default where anything is window-robust; the decay exception is one model at one window; provenance use stays dead. Artifact-side, no shared-representation caveat |
| **PD-2** | Polish *decays* specifically, rather than merely moving | **SUPPORTED FOR HUMANS, AND THE DIRECTION DISSOCIATES BY PROVENANCE (test, L89/L90).** Essays decay at both windows (−0.17 and −0.14, p ≤ 4 × 10⁻⁶); books decay at the wide window only (−0.30, p = 0.012; null at 40); the machine corpus rises. The dissociation weakens the register-geography rival, which predicted a shared direction, and restores the reallocation account's essays evidence; the books' window-boundness keeps the long-form claim modest |
| **PD-4** | Polish variance is larger in less practised makers | **OPEN** |
| **G149** | Movement instruments sample shifting motivations over time, and a window-local sampler can locate a real shift | **RULER PASSED on the gridworld (test-side toy, L127); FIRST TEXT FORM DEAD (test, L134).** Planted goal switches are detected at 89.5% at the paper's fitted rationality with false alarms priced, monotone in walker rationality. The text port substituting surface-feature window distances for per-step likelihoods detected zero of twelve planted specification splices and was equally blind to topic splices, so the transferable part of the license is the likelihood structure, not the windowing: the next text form carries model-based per-window evidence under competing specification hypotheses, or the change-feature block between windows |
| **PD-29** | Polish separates into attraction and translation | **OPEN, and everything in this section depends on it** |
| **PD-30** | Attraction decays across an artifact; translation does not | **OPEN** |
| **PD-31** | Generated text carries attraction but not translation | **OPEN.** Translation structure is countable where effort is not |
| **PD-32** | Translation is denser where the maker expects a distant reader | **OPEN** |

**What the table says.** The movement family completed its cross, its window sweep, and its
magnitude square with the square's own window test, and the durable residue is smaller and
stranger than any of the intermediate stories. Human polish falls across position where it
falls (essays at both windows, books at the wide one only). The SIGN of machine polish
movement is a rising default with one model-level exception (three of four cells rise; the
lone decay is one model at one window). The MAGNITUDE of machine polish movement obeys no
lineage law; the wide window read as a post-training split and the narrow window scrambled
it, so magnitude claims are window-conditional everywhere they have been tested. What is
robust at both windows is one cell; qwen-instruct's output is positionally mobile wherever
it is measured, and it is the same single model whose text moves a reader model's internal
trajectory (the two instruments that dissociated across families reconverge on this one
model). Each instrument reports separately, and provenance use of any of them stays dead.
The register-geography rival stays weakened; reallocation keeps its human evidence,
undemonstrated as mechanism; G146's question is now about that one model, namely what makes
its output positionally mobile on every instrument while every other cell is conditional.
The maker-signature half of the section is untouched by all of it and now hierarchically
confirmed: polish-side features carry the author at fixed topic on two corpora and two
window sizes with no exceptions, and under a mixed model with authors as random effects the
polish composite holds ten times the depth composite's author-level variance, so the claim
rests on clustered inference rather than pooled windows.
The family's reframe (movement as motivation-shift sampling rather than depth) now has one
license and one boundary: where motivation shifts are real by construction, a window-local
sampler carrying per-step likelihoods finds nine of ten of them at the fitted human
rationality with false alarms priced, and the first text form that swapped those likelihoods
for surface-feature distances saw nothing at all, not even topic splices. The measurable
thing is likelihood-grade window evidence, and building that for text is the family's open
instrument problem. The rest is the simulation's 6.5× decay asymmetry plus unrun
tests, with the attraction/translation split gating the lot. Confidence: the essays decay
and the signed family cells are replicated at doubled n and one bad test away as a set; the
books decay stays window-bound; the magnitude square is settled as window-conditional with
the qwen-instruct constant one bad test away; the essay-boundness results are one bad test
away; the reallocation reading is contested by its own control; the shift-sampler license
is one bad test away and constructed-world only; the rest is untested or sim-only.

## §3. Automatic traces: leakage, concealment, and the channels that carry them

> **leaked** – a layer that is TRUE... emotional leakage that can show up in your text
>
> **emblematic** – a conscious social decision

> Leaked information is **not necessarily true**, but it is information that shows previous
> automatic and deliberate traces. If you can extract value data from it, it at the very least
> shows a **weighted representation of previously enacted value data.** Someone who had changed
> might have bad habits still showing up, and that would make it untrue. But it's a sort of
> **record, a history.**

> Emblematic may end up being more complicated than a conscious social decision, but I want to stay
> with that. Perhaps it **moves with attention** in some way.

> An artifact gives you two different kinds of evidence. It gives you a probabilistic distribution
> of previous attention, compressed lossily through expertise, and it gives you a record of what the
> maker chose to attend to when the artifact was created.

*2026-09-01/02 walkthroughs; spoken wording lightly reconstructed.*

He arrived at the original split from ten artifacts and a think-aloud. It maps onto the field's central
unresolved debate, leaked onto primary-process core affect and emblematic onto constructed emotion,
and the reconciliation position (*basic emotion theories are theories of emotion; constructed
emotion is a theory of feeling*) requires both to be true of different things. The two layers should
not be assumed to share a value set; giving both the same eight concepts is a named simplification.

**It also diagnoses the field's LUST problem, called before the argument existed:**

> I think they were just catching the fact that leakage – they were assuming that **leaked fear and
> performed fear are the same thing.** [...] That's why lust is kind of bullshit in this framework,
> because **the easiest thing to catch is the performed section.**

A questionnaire reaches only the performed layer, so LUST is the system least available to it, for
social rather than neural reasons. Artifacts have no such limit. Its signature is his, **the thing a
reader politely glosses over**. *"Someone ends up talking about feet for a sentence too long and
you're like, ooh, buddy."*

**No additions to the eight concepts.** *"We shouldn't add anything, because that's kind of just
where the literature is right now."*

**Concealment: the shield matches the leak.** An off-colour hypothesis he gives low weighting,
rated not particularly useful; it stays because a sim result touched it (T-4 below):

> Leaked greater than emblematic **doesn't even count as concealment**... if anything the emblematic
> would get larger. **You perform louder to cover up. I get extra quiet if I'm extra angry. The
> shield matches the leak.**

**The cheap channel for automatic traces is function words.** More automatic production, article
selection and function-word distribution, should associate with the leaked layer, while
content-word choice sits under tighter conscious constraint and associates with the emblematic, a
formulation he endorses in the general sense without having phrased it. Function words are
produced non-consciously, are topic-independent, stable across an author's corpus, and very hard
to fake, the assumption authorship attribution already runs on. His automaticity intuition *is*
that mechanism. Style survives intent because it was never held.

> The goal of Sounding Line is just to be able to measure depth. It's just that.

> At this point we're trying to extract **the second inference of the triple inference**, the
> process, trying to be able to extract the process-shifted goals of the policy map. Because if we
> can do that, then it is a **short hop to extracting the values.** And the industry is close to
> being able to converge on that process equation already. I would bet that the difficulty of doing
> so without human sensory input is part of why **world models** are hinting at taking over, though
> raw inference is a competing effort for sure. Effectively, our project goal is to **recover
> individual recorded decisions first, and then summarize the problem-directed structure.** It's a
> much more accessible metric. And it should, as part of its function, **detect AI quite well in
> most cases.**

The automatic decisions are a class this project spent a long time not counting, and under the
restated goal they are recorded decisions like any other, recovered first and summarized after.

> Previous decisions enter by allowing you to stack more decisions on top of them. The painter
> doesn't have to think about how to hold the brush because he's thinking about the metaphor and the
> feeling he wants to convey.

Automaticity is therefore not zero decision structure. It is compiled reachability: earlier
learning makes some present actions cheap and frees focal attention for another level. The
artifact may preserve the resulting competence without preserving how much practice formed it.

**Two timescales in one automatic channel.** Automatic fluency, omissions, and deformations can
carry a graded historical mixture from related prior contexts, compressed through expertise.
Present costly allocation, including effort spent resisting or redirecting an old tendency,
supplies a more sharply dated trace. The present action may express preference while the
automatic tendency records older pressures. Neither channel identifies one cause or one date
for every component of the historical mixture; multiple dated artifacts can progressively
narrow that uncertainty. Artifacts are privileged because they persist and accumulate
decisions, not because other behavior is excluded: speech, gesture, tool use, and edits can
carry the same trace classes. The preference interpretation of the two timescales lives in
[`THE_TRIPLE_INFERENCE.md`](THE_TRIPLE_INFERENCE.md) §5; this file owns the observable traces
only.

**Anomaly-handling traces are a sequence, not a type** *(restated 2026-08-21; the
earlier mutually exclusive label list fell to the curator's sequential ruling, and the
old labels survive as values inside the axes below)*:

> Failure to notice is one decision, with the sole exception of physical or perceptual failure.
> Divided attention, exhaustion, and absent expertise are context; they are not decisions.

> If you notice a deviation and leave it in place, you are exploiting it for convenience or for
> some other purpose. Notice-and-ignore is therefore evidence about a secondary goal.

The trace record is multilabel and sequential; the following can coexist on one anomaly:

| field | values | what it separates |
|---|---|---|
| `perceptual_access` | available, degraded, unavailable, unknown | non-recognition from inability to receive the cue |
| `origin` | intended, accidental, forced by constraint, indeterminate | initial cause from later handling |
| `recognition` | noticed, failed-to-notice, indeterminate, not-applicable | awareness from occurrence |
| `response` | repair, conceal, compensate, abandon, retain, exploit, no-visible-response, unknown | counterfactual preference and handling |
| `recurrence` | isolated, repeated, escalating, diminishing, unknown | one-off accident from habit or persistent limitation |
| `integration` | none, local, downstream, global, unknown | accidental residue from ordered adoption |
| `candidate_secondary_goal` | open vocabulary plus evidence | what non-repair or retention served |
| `reader_uncertainty` | calibrated probability or abstention | artifact underdetermination |

At the episode resolution, perceptually available failure to notice is recorded as one
decision event. Exhaustion, divided attention, absent expertise, time pressure, and
similar conditions are context fields, not extra decision events, and physical or
perceptual unavailability is never coded as failure to notice. This ontology does not
make awareness observable: where the artifact cannot separate the states, the reader
returns indeterminate. And the secondary-goal claim carries its guardrail: the theory
permits the claim that some competing goal governed a perceptually available omission,
but the instrument receives no credit for that generic claim. It must choose the correct
goal from matched alternatives, localize evidence that distinguishes it, or predict a
held-out response; "convenience", "energy saving", and "status" are candidate
explanations, never universal residual bins. **Ordered accident** names a sequence
rather than an origin type, accidental or indeterminate origin followed by recognition
or retention and then local or downstream integration; later order is evidence about
handling and adoption, not proof the original event was planned, so the label is derived
from the fields rather than added as a class. The artifact may not identify any of this,
and "unknown" is a valid result on every axis. A choice
that appears locally defective may serve a secondary goal the reader has not recovered, so a
mistake is never defined simply as whatever fails the reconstructed primary goal. (The reader's
entry rule and handling evidence live in [`READER_HEURISTICS.md`](READER_HEURISTICS.md) §2; this
file owns the trace classes.)

| # | hypothesis | status |
|---|---|---|
| **G171** | Later structural dependence separates an integrated accident from abandonment, repair, and purpose, while origin stays unresolved (the ordered-accident sequence read mechanically) | **RULER PASSES BOTH SEEDS (test-side toy, L159), one recorded repair.** All eight pattern-violation classes at or near 1.0 in the constructed world, unfamiliar convention never called error, wrong-goal read as model revision at 1.0, and ZERO confident origin calls on the origin-identical pair (integrated vs pseudo-accident), with adoption identifiable and origin honestly abstained, the §2.2 ruling behaving as theory. Text transfer is a Stage-2 branch carrying the origin-abstention gate |
| **S-3** | An involuntary leak channel is readable | **SUPPORTED (sim)** at 0.90 |
| **T-4** | Amplifying the display makes concealment *more* detectable, his direction against mine | **SUPPORTED (sim)**, surviving a reader wrong about almost everything including a 50% channel swap, but **failing at 25% concealment: it reads effort spent hiding, and catches heavy concealers only** |
| **PD-12** | Function words have spare capacity beyond author identity | **SUPPORTED (test).** Author held fixed, they separate different works by the same person at twice chance, ten of ten authors above chance |
| **L16** | Function words separate specified maker states, once the design has power | **SUPPORTED (test) on all three ladders**, 1.6× to 3.0× chance, scaling with the manipulation. **The owed fair induction control ran (test, L94): SURVIVES on the held-out and extreme ladders** (0.44 against 0.20 chance after within-rung identity removal, permutation p < 0.005, raw baselines reproducing the originals) **and collapses on the first ladder** (0.25, p = 0.22), the weakest manipulation at the smallest n. The old dose-eating form of the control would have killed all three (0.13 to 0.17), measured alongside as the demonstration |
|   | | *(this row's history is SEPARATES-uncontrolled from 08-08, the control built and passed on the two stronger ladders 08-12)* |
| **PD-11** | Function words carry maker *state*, not only identity | **SUPPORTED (test, L95) at the pre-registered bar, on the powered rerun.** Held out and frozen at doubled n: 2.25× chance (0.5625 against 0.25, exact binomial p = 2.6 × 10⁻⁹), seeking near ceiling and care weakest. Generated text only; the E38 warning against extending this to humans stands |
|   | | *(this row's history is 1.80× against a 2.0× bar on 08-04, then the standing-policy rerun clearing it on 08-12)* |
| **PD-14** | Reading the model's activations reaches the leaked layer where its text does not | **SUPPORTED (test), and it became the live path.** The interpretation lives here; the empirical activation rows live in [`THREE_COGNITIVE_LAYERS.md`](THREE_COGNITIVE_LAYERS.md) Part II |
| **G32** | Polish correlates with late structure, leakage with early | **OPEN.** The depth-band version of this section's split |
| **PD-13** | Asking a model *"what stance is performed"* reaches the leaked layer | **REJECTED by construction.** It returns a content-word judgement either way |
| **PD-15** | Attention dwell past argumentative need is measurable | **OPEN.** Nothing built; needs a model of argumentative need. *(Absorbs G30, which duplicated it.)* |
| **PD-16** | Cognitive-load signatures leak despite narrative management | **OPEN.** Take the deception literature's features, not its promise |
| **G87** | Low-visibility features carry *who*; high-visibility features carry *what* | **SUPPORTED (test), a clean double crossover on the first pass (L41).** Invisible habits identify the author at 0.78 vs 0.38 for visible features; visible features separate draft-stage at 0.48 vs 0.30. The pottery prediction, measured; what it licenses is an identity/stage split, with the deep-identity and values readings still needing discriminating tests |
| **G28** | `leaked` and `emblematic` do not come back as the same distribution | **SUPPORTED (test, L88).** Between-layer profile agreement 0.597 against the same prompt's own test-retest 0.725, difference CI [0.07, 0.19] on 150 book segments with the retest arm as the built-in null. The probe is not asking one question twice |
| **G29** | If one layer separates and the other does not, it is `leaked` that fails | **ANSWERED FIRST-PASS (test, L91): both carry, neither fails**, so the trigger never fires. Author accuracy 0.19/0.23 (leaked/emblematic) against a 0.13 floor, both permutation-significant, with the performed layer carrying as much identity as the leaked, likely era-and-genre convention on this corpus. Fixed-era or function-word-side is the clean second form |
| **PD-11b** | The first function-word attempt answered its own question | **VOID (test).** Ran at 38% power |

**What the table says.** The automatic channel is real on every instrument that has touched it.
Readable in simulation, twice chance on real authors with identity held fixed, separating specified
states on all three ladders, concealment detectable in his predicted direction rather than mine,
and now stage-differentiated exactly as the pottery import predicts, with the invisible habits
carrying identity and the visible features carrying situation. The two-layers-are-two question
has now been asked and answered in the battery's favor, the leaked and emblematic reads coming
back as reliably different distributions against a built-in retest ceiling, which removes the
one-question-twice hedge from every leaked row above. The state reading now stands on three legs: the rung separation
carries its induction control on the two ladders with the strongest manipulations, so what the
function words separate there is not explained by which specifications were drawn, the same
license the ratio and the three revived features hold, with the first ladder's collapse reading
most naturally as power at the weakest dose; and the four-affect separation cleared its
pre-registered bar on the powered rerun, the standing policy vindicated on the test that created
it. What is still missing is the license to call it *affect* rather than *style* on human text,
since every state cell so far is generated text under specification, and G29's
first pass says both layers carry a little identity with no asymmetry, the performed layer
plausibly riding era convention, so the which-layer question stays open in its fixed-era form.
The channel's one process lesson stays woven in rather than appended: it was measured three
times at sample sizes that could not see it before the powered re-run separated on all three
ladders, so the cheap channel was never dead, only underpowered, the full sequence being in the
git history. The anomaly-trace half of the section now has its second constructed-world
instrument: the ordered-accident ruler reads the multilabel sequence exactly as the schema
above demands, recovering integration, repair, abandonment, and purpose at ceiling while
refusing to name an origin the trajectory cannot show, which is the schema's
origin-versus-adoption asymmetry passing from ruling to measurement. The two-timescale trace
named above has no instrument yet: nothing has separated the dated present allocation from the
expertise-borne historical mixture inside one artifact, so that trace inherits no evidence from
the automatic-channel rows here. Confidence: the capacity
results are replicated and controlled; the state reading
under its control is replicated on two corpora and one bad test away as a set; the visibility
crossover is one bad test away; the ordered-accident ruler is one bad test away and
constructed-world only; the sim rows are sim-only; the two-timescale trace is untested, logic
only.

## §4. Terminal organisation: layered, flattened, and non-invertible

Logged before Gate 3 read out, so it could not be used to reinterpret it:

> I don't think that it's the case that corporate work necessarily has less decision-making that went
> into it... what actually that means is that their motivation is immediately reconstructable and that
> motivation is always money. That's why corporate work seems soulless. **It's not quite the same as
> why AI work seems soulless, which is that you can't arrive at a motivation.**
>
> Humans can't really take action without intention. It's just that **corporations steal your
> intention and replace it with money.** [...] It is a flattening of human motivation, and that's why
> it's so repulsive to artists that live in a world of motivation extraction.

> The problem is that what if there is corporate depth, but I can't see it specifically? ... The
> center, the support structure for the centerpiece goal, becomes more structured as different
> people iron out the kinks of it. So the center goal becomes more solid as the secondary and
> tertiary goals become less present as more people get involved. This would apply to academic
> papers too.

> I do want to note with corporate flattening that it could be all of those depending on the
> observer.

| observed artifact organization | candidate production account | invertibility risk |
|---|---|---|
| recoverable plurality | several goals or constraints leave distinguishable traces | reader may still project the wrong hierarchy |
| strong centerpiece with weak subsidiary traces | institutional constraint, multi-author aggregation, deliberate professionalism, or genuine flattening | unfamiliar expertise can mimic flattening |
| coherent but human-foreign organization | maker process poorly matched to the reader's generative priors | reader may invent a human-shaped actor |
| deliberately human-invertible organization | maker optimizes comprehension support or supplies a human-readable rationale | legibility can exceed causal transparency |
| underdetermined | artifact and context supply too little discriminating evidence | abstain; no topology claim |

"Corporate" and "machine" are construction families for testing these cases, not definitions of
the rows. The same artifact class can move between rows with reader expertise, supplied context,
collaboration structure, and explicit optimization for human invertibility.

The machine cell is corrected in his words, since "no motivation" was the imprecise form:

> It is a **non-invertible motivation for humans**, because the specific tricks we use for arriving
> at a higher-precision estimate on an incalculable issue, another actor's values, **don't work.
> They misfire.** And as a result, we end up **hallucinating some fake human-shaped actor and then
> learning from them.**

> The corporate motivational issue is similar but not precisely the same. Their issue is more a
> **flattened terminal organization**, where you often have fewer goals due to a kind of **sanding
> down of the subsidiary goals** that still provide some action.

> Model choices can't be perfectly human invertible. That's actually one of my core theses and I
> think you need to prove that to me. I think they can present a chain of logic at the surface level
> that can kind of guide to how a human might have gotten to that invertible conclusion. But that
> has to be forced in. It's not naturally something that they do. It's not like another human would
> automatically make things that are human readable just through their existence. The model has to
> try to, and it fails in large part.

Non-invertibility remains a candidate observation about ordinary reader-model encounters, not an
essential property of model authorship. The reader's human priors can misfire and produce a fake
human-shaped maker; an explicitly guided or aligned system can also construct a translation layer
that those priors successfully invert. Artifact legibility and causal mechanism must therefore be
reported separately; the alignment consequence is canonical in [`ALIGNMENT.md`](ALIGNMENT.md) §5.
Under this reframe, Gate 2's high purpose-agreement on commercial work was the instrument working, since
an immediately reconstructable motivation *should* produce agreement between independent readings,
recorded as the reason to build the successor design, not as evidence for it (the hypothesis
arrived after the result). What the instrument should report, and has never been built to report,
is *whether a maker's terminal value is singular or layered*. His own caution kept: measure
**singularity of terminal value**, not presence of a profit motive.

**Soul is the layered end named from the maker's side** *(moved from the triple inference
2026-08-09; motivational variety is an artifact property)*:

> When we talk about something having **soul**, what that means is **a variety of motivations**. And
> it tends to travel with expertise – because as processes are baked in with automaticity, you lose
> conscious access to them and they start to be tied more to your **drives**.

> We can keep using the word soul to mean a variety of motivations, but to be more specific,
> **recoverable motivational plurality.** The mechanism is in part through expertise, the
> **repetition of motivational data baked into your specific transition mapping**, and the variety
> of value data baked in. To me it just feels correct to call that soul. It's a **notional concept
> for now.** I'll need a whole bunch of data before I start claiming nouns, but we need something to
> call it, so that's what we'll call it.

The chain runs practice → automaticity → the decision leaves deliberate control → it is made by
whatever is underneath → an expert's artifact carries more drive-derived variety than a novice's,
without the expert choosing it. This is the mechanism the residue account of values runs on
([`THE_TRIPLE_INFERENCE.md`](THE_TRIPLE_INFERENCE.md) §5), and it explains why an expert cannot say
*why* they did something while their artifact shows more of what they are. Recoverable
motivational plurality is indexed to a reader and context. A reader can miss real subsidiary
structure through lack of domain expertise, while a polished rationale can create the appearance
of plurality without corresponding causal control. "Soul" remains a notional artifact reading,
not a maker essence.

**Corporate work seen from the artifact side is overdeveloped user-facing density**, which
replaces the earlier thinner-decision-density account:

> Corporate work has more of a focus on **user-facing decision density.** It is so overdeveloped
> along that one specific motivation of targeting the user that it doesn't have that plurality of
> motivation. It is effectively soulless. And this is **bidirectional.** Averaging a whole bunch of
> activities from a large number of people will result in that shape, but it's also by design. A
> company doesn't want to present these bits of personality, so there is a sort of **purposeful
> professionalism** even to the art. A variety of motivations would allow you to see the personality
> of the individual workers, and that doesn't necessarily reflect well upon the business. There's
> too much error.

**And stacked motivations are the layered end's mirror, held as a hypothesis.** A machine given
many aligned motivations *should* read as more intentional:

> If you gave a machine a bunch of different goals and told it to balance all of them before it wrote
> something, it would actually get **more of a purpose ranking along any intent register.**
>
> We should **start at the extremes** – three pages of different motivations stacked on top of each
> other that are all reasonably capable of aligning, against a machine writing with just one or two.

| # | hypothesis | status |
|---|---|---|
| **PD-18** | A machine given many aligned motivations reads as more intentional than one given two | **REVERSED IN DIRECTION (test); his contest of the original null was right.** The revived features, the flagship ratio, and the (now echo-suspect) recovery all peak on the most-stacked corpus |
| **PD-19** | The effect *accelerates* at the top of the ladder | **NOT SUPPORTED (test, L17/L25), twice.** A straight line that flattens at the top; the saturation echoes the bits ceiling |
| **PD-6** | Commercial work shows *higher* purpose agreement than individual work | **OPEN, pre-registered before Gate 3.** Gate 2 is suggestive and cannot serve as the test |
| **PD-8** | Commercial decision density is *not* systematically lower than individual | **OPEN** |
| **PD-9** | Machine text shows low agreement *and* low breadth, no coherent maker-state as against a flattened one | **OPEN** |
| **PD-10** | Singularity of terminal value is measurable at all | **OPEN, the successor instrument**, needing a corpus this project has not seen |
| **G114** | Independent readers' goal-guesses converge more where intent is dense | **NOT SUPPORTED (test, L35/L46), three designs deep.** Bits recovered died to empty answers; token overlap read topic; judge-rated similarity with topic held fixed saturates near 0.9 on everything and the ten-specification dose gap comes out at −0.02, wrong sign, negligible. The third instrument produced orderly numbers (books score lowest, plausibly summarisation difficulty) and the dose is simply not in them |
| **T-2 / T-9** | Motivational variety is measurable as breadth of recovered purpose | **INSTRUMENT DEAD (sim, twice).** The breadth measure tracked how hard the goal is to recover, not variety; at matched difficulty the diversity excess is negative. The simulation itself states it cannot test whether practice *causes* drive-multiplicity |
| **G55** | Diversity rises with expertise while agreement about purpose stays flat | **OPEN.** A two-measure prediction using quantities that already exist, and the second attempt must survive a difficulty control that neither prior try would have |
| **PD-7** | Commercial work shows lower purpose *breadth* | **INSTRUMENT DEAD (sim, twice).** The breadth measure read difficulty |
| **G3** | Half A of a web corpus contains more recoverable method than half B | **VOID (test), twice over** |
| **P02** | Process geometry the final artifact does not carry (segmentation, then a prefix) buys recovery of the recorded first action that pixels alone do not | **SUPPORTED (test, L238), one corpus.** With the strokes as an unordered set a learned ordering prior finds the first stroke at 0.69 against 0.49 for the longest-stroke rule (permutation floor 0.22); with the true first stroke given, the next stroke's placement is predicted at 0.50 against 0.35 |

| **P01-S5** | Richer process access (final geometry, unordered set, partial order, true prefix) improves next-stroke prediction beyond cheap priors, monotonically | **VALID NULL with the priors in the predictor (test, L287; L259 before), one corpus.** A logistic model per level sits below the better of the category and bounding-box priors at every level (−0.35, −0.11, −0.02, −0.13 nats on 555 drawings), not monotone; the predictor cannot match its own marginals, so the ladder is untested above them for the next stroke |
| **P02-S5** | A reader proposes an enactable drawing order from an unordered stroke set beyond the blind rate, and abstains where several orders fit | **ENACTABILITY SUPPORTED, ABSTENTION FAILED (test, L274), 45 parseable of 120.** Enactable 0.56 against 0.17 blind, the historical order in 0.72 of enactable proposals; 'the order can be determined' answered yes in 0.62 of artifacts where four orders fit. Second contract, comma format, two readers (L304): every reply parses, two thirds echo the listing, the genuine third is enactable at 0.70 with the historical order in 0.45 of those. Under the echo rule with a second turn (L312, 240 drawings per reader): first-turn genuine proposals enactable at 0.82 against 0.17 blind, the historical order in 0.43 of those against 0.25; a second turn recovers Qwen nine times in ten at 0.50 enactable and SmolLM2 almost never; the genuine population's primary is +0.44 [+0.39, +0.50] |
| **P03-S5** | Process access rewards competence more: the true prefix buys more from a fourfold training set than the unordered set does | **SUPPORTED thinly with the priors in the predictor (test, L289; INCONCLUSIVE at L262).** Competence gains +0.16, +0.19, +0.30 nats at set, partial order, prefix; the interaction +0.14 [+0.01, +0.27] on 555 drawings |

**What the table says.** The layered end of the topology is the best-evidenced thing in this file,
with three independent measures peaking where motivations stack, while the flattened end now
carries its first genuine negative. Reader convergence has failed to move with intent density in
three separate designs, the last with topic held fixed and an instrument that produced orderly
numbers, so agreement-between-readers looks like a property of coherent text rather than of dense
intent. The breadth-style measures read difficulty, and the singularity measure has never been
built. The quantity it would measure now has its working name, recoverable motivational
plurality, notional until data supports claiming nouns, and the old maker-type table is
rebuilt as conditional artifact organizations: corporate flattening and machine
non-invertibility are readings an observer can reach for several different production reasons,
not intrinsic labels, with unfamiliar expertise able to mimic flattening and an optimized
translation layer able to mimic invertibility. The soul claim's mechanism matters beyond this
section, since if expertise does not move decisions into drives, the residue account of values
loses its engine. The topology remains a good description whose positive half is measured and
whose flattened half keeps refusing to be, now with the added burden that any flattening claim
names which production account the evidence discriminates toward. The non-invertible end
now has one measured boundary from outside text: a drawing's final raster carries its
first action no better than a placement prior, while the same drawing's strokes as an
unordered set let a learned ordering prior find that first stroke in seven of ten against
five for the best geometric rule, and the true first stroke given places the next at half
against a third (P02), so what the artifact drops is recoverable from segmentation and a
prefix, each an access level the reader must be granted; that bounds inversion of the
artifact, and it says nothing about recovering the maker. The ladder is a first-stroke
result so far: for the next stroke a per-level predictor never beats the category and
placement priors at any access, including the true prefix (P01-S5), so what access buys
beyond a sharp marginal is unmeasured for later actions; competence helps that predictor
most with the true prefix, and with the priors inside the predictor the difference between
access levels clears zero, thinly (P03-S5): access is worth more to a competent predictor
than on its own. A small reader given the strokes as an unordered set proposes an enactable order
five times the blind rate, the actual one at nearly twice chance, on the trials it attempts, which
are a third of them unprompted; the attempt rate is the reader's own (a second turn moves one reader
to nine attempts in ten at half the quality and the other not at all), and it says the order is
determinable in most artifacts where four orders fit (P02-S5), so the process is readable from
segmentation by a reader too, and equifinality is not.
Confidence: the stacked-motivations reversal is replicated and controlled; the convergence null is
one bad test away; the process-geometry boundary is one bad test away, one corpus, and holds for the first
stroke only; the reader's segmentation reconstruction is one bad test away, two readers, one corpus, the
echo rule applied; the rest is untested or instrument-dead.

# Part II: The measurement ledger

## §5. Reading the artifact directly: the funnel, the deaths, and the three survivors

**The goal is recovering recorded decisions, so the obvious instrument counts them from the text.
Ten measures tried; all ten died to length, register, or vocabulary, and then the final three
deaths turned out to belong to a broken control, not to the features.**

| # | hypothesis | status |
|---|---|---|
| **PD-21** | Published linguistic features track specified constraint dose, once machine-detectors are removed | **REVERSED (test, L2/L23/L24).** Under the fair induction control **all three candidates revive on all three ladders**: conditionals (+0.65/+0.51/+0.73), contractions (+0.43/+0.48/+0.32), phrasal coordination (−0.41/−0.27/−0.44), nine of nine at *p* ≤ 0.007 |
| **PD-20** | Decision density can be counted from an artifact | **REJECTED (test).** It was word count (0.88), then vocabulary diversity (−0.88); two confounds in sequence, nothing underneath |
| **PD-22** | Causal connectives track depth | **REJECTED (test).** Ranked the ladder, then inverted on humans; it measures explicitness |
| **G116** | Specified dose adds description length, the essays' Kolmogorov claim | **REJECTED (test, L29).** Incompressibility flat across all rungs; human long-form matches machine text at matched length |
| **PD-23** | A larger feature bank beats a small curated set | **REJECTED (sim).** Sixty generic features gain little and lose more in the worst case |
| **PD-24** | Weak effects can be stacked into a usable detector | **OPEN, first attempt NULL (test, L125), stacking RE-GATED (test, L137).** The first real stack, 158 surface-change channels concatenated into a style-change classifier's head, did not beat the substrate and doubled its seed variance, exactly the outcome the L4 conditions exist to catch (beat the best component on held-out data, with different errors). Choice recovery is now confirmed at confirmatory grade (L141 after the L137 demotion arc), but stacking still waits on the four Phase 2.1 gates in the evaluation contract, and the exploratory reads split them: family transfer and abstention behave (gates 2 and 4), the echo contest is open at eleven points over a 0.80 bar (gate 3), and artifact-only recovery of REALIZED problem-directed choices (gate 1) is unmeasurable until the rebuilt factorial supplies verified realization. The standing warning holds: stacking shared confounds produces a strong confound |
| **rung −1** | No measure reads noise as maximum intent | **SUPPORTED (test).** The only ceiling control in the project |
| **P01** | A finished drawing's raster constrains its recorded first action beyond category and ink priors | **OPEN, first read INCONCLUSIVE (test, L237).** +0.04 balanced accuracy over the ink-placement prior with the interval crossing zero; raw accuracy favors the raster because it predicts the majority quadrant; a rotated raster falls to chance, so the pixels carry placement |

**What the table says.** Every cheap property of a text that correlates with dose also correlates
with something cheaper, and the cheaper thing wins, down to raw description length. The funnel
that removes machine-detectors (61 of 81 replicated features) is the durable product, and the three
features that survive its fair-control version are the only artifact-side signals standing, which
is what a stacking instrument would need, channels with different failure modes. The stacking row
now carries its first real datum, a preregistered null: concatenating a wide surface-change bank
into a strong classifier's head bought nothing but variance, so the stack the section eventually
builds starts from the change-feature block and adds channels only when their errors differ, and
it starts only after the four repair gates clear, since the block reads both versions of a text
and therefore lives in the paired-delta interface, not the final-artifact one. Two of those
gates behave in exploratory form (family transfer, abstention), one is an open contest (eleven
points over a 0.80 word-echo bar), and the decisive one, recovery of verified-executed choices
from the artifact alone, waits on the rebuilt factorial. What none of it
licenses is a claim about human intent or depth, since dose is instruction count to one
generator; the program's factorial benchmark is the construct test, and its first corpus is
exploratory until realization is adjudicated. The funnel's own history, direct counts falling to
length and then vocabulary, the 342-feature bank, the survivors dying to an induction check
whose regressors turned out to contain the dose, lives in the git record rather than here. The first artifact-side read outside text lands
here too, and it lands the same way: a raster of a finished drawing places its recorded
first stroke no better than the ink-placement prior on the balanced estimand (P01), the
raw-accuracy edge is the majority quadrant, and a rotated raster loses everything, so what
final pixels carry of an action is placement at a coarse grain, which the terminal
organisation section's access ladder (P02) is what moves.
Confidence: the funnel and the deaths are replicated and controlled; the three revivals are one
bad test away by age; the drawing read is one bad test away and cannot yet exclude its
own null.

## §6. Controlled change: revision, and the one human comparison

> I would expect, in general, for most consecutive edits to serve a continuing intention. Not
> always.
>
> [...]
>
> It feels like we're in a world where we have to interact with scalars more than binaries and
> categories.

*2026-08-27 walkthrough; spoken wording lightly reconstructed.*

**Discrete edits can express continuously changing goal weights.** A continuing communicative
intention can coexist with changing emphasis on precision, professionalism, concealment, or
audience response. Earlier choices may leave dependencies after their explicit markers disappear;
complete removal can also leave no identifying trace. An unusual surviving detail is a cue with
rivals, including convention, constraint, and accident. Neither an annotation run nor an odd
detail uniquely identifies a governing goal.

**86 university students, one prompt, three drafts each. Maker, prompt, topic, register, and genre
all fixed by construction.**

| # | hypothesis | status |
|---|---|---|
| **PD-26** | Something measurable changes as one person redrafts | **SUPPORTED (test, L5), one coherent thing.** At matched length, revision raises lexical sophistication (longer, rarer, more polysyllabic words, fewer stopwords), one factor under six names, sign agreement 70 to 78% across authors |
| **PD-27** | That effect is length | **REJECTED (test), the trap fired as pre-registered.** Raw survivors were all counts; length-matched, 17 of 315 and none of them counts |
| **PD-28** | The surviving effect is polish, not depth | **SUPPORTED (test, L42/L66), the matched control decided it.** With content and surface revisions balanced on size, rarity shift, position, and difficulty (coarsened exact matching, balance verified), content identifiability collapses from 0.857 to 0.507 against 0.5 chance. Within common support, the content-associated lexical effect *was* its covariates: sophistication and magnitude, not recoverable depth. Scope: the matched fifth of the corpus, which is where comparable revisions live |
| **G129** | Recorded revision purposes are recoverable from the delta by a bounded reader, beyond matched alternatives and beyond a cheap change-feature baseline | **CONFIRMED AT CONFIRMATORY GRADE ON THE SECOND, CORRECTLY-GATED RUN, WITH THE BASELINE WINNING THE INSTRUMENT CONTEST TWICE (test, L141 confirming L132; the demotion arc L137; pilot chain L62/L64/L65).** The first battery replicated recovery (0.4854 vs the analytic 0.25) but voided its own shuffle gate on a misspecified expectation and was demoted under its card's terms. The fresh battery (`prereg/g129b.py`, seed 37, every gate carrying null and alternative expectations with a direction) landed all gates quiet: recovery 0.4805 (REPLICATES, seed-stable to half a point), the balanced matched draw 0.415 (16.5 points, pilot tier as pre-committed at 200 of the powered 283 after the one specified caliper relaxation), the shuffle arm 0.1136 beside its frozen 0.125 alternative expectation, fabrication 0.000 twice (L132 1-of-200 sym miss; L141 0-of-200), and the change block beating the reader both times (0.5552 then 0.5471; McNemar p = 0.0097 and 0.0157). Scope: one corpus, one reader family; delta-interface only (the block reads both versions) |
| **G158c** | A bounded reader identifies which instruction produced an essay from the essay alone | **SPLIT CLEANLY IN TWO (test, L140, exploratory).** On surface constraints whose satisfaction a string test verifies at 1.0, truth-balanced recovery is 0.25, exactly chance, while pure word-echo scores 0.375: the zero-shot reader does not check constraint satisfaction, it picks semantic familiarity, and its raw 0.41 was label frequency (collapses under balancing while echo rises). On problem-pool assignments it clears the word-echo bar by 11 points in both the seen and held-out family (0.909 vs 0.798), a transferring margin the corpus cannot decompose into executed choices versus assignment vocabulary leaking into the essay (echo alone reads assignment at 0.80). Fabrication clean in forced choice with an explicit none option (0.05), the same reader that over-credits 0.69 in yes/no verification (L139): the format is the instrument |
| **G94** | Spec-style reconstruction posits decisions that were not there (the Taramsa failure) | **BOUNDED IN THE HONEST FORMAT (test, L143, exploratory).** On the ladder, where every true specification is reconstructable and join-checked, the reader given an explicit none option invented a specification on 1 of 10 unspecified texts, recovered real specifications at 0.52 against a 0.225 blind floor and a flat 0.40 word-echo bar, and its per-spec accuracy fell from 0.77 at three specifications to 0.44 at ten while echo stayed flat: dilution of trace, not vocabulary leakage. The same reader over-credits at 0.69 in yes/no verification (L139), so the fabrication risk is a property of the ASKING FORMAT, not a fixed property of the reader |
| **G168** | Recorded ratification roles (selection among alternatives; veto and forced revision) are recoverable from the final artifact | **BLIND AT EXACTLY CHANCE with ceilings passed (test, L160; preregistered).** Selection and veto sit at 0.500 artifact-only against near-perfect process-aware ceilings (0.975, 1.0), on a corpus whose own audit proves the selected thesis survives into the text at 0.95 integrity. Ratification is real and invisible: the contribution network is a records object, and the product surface is auditing, never inference. The repair question's ceiling failed (a two-hop format defect, uninterpreted, owed a fix before any reopen) |
| **G166** | Production route identity (which of five recorded ways an essay was made) is recoverable from the final artifact | **SEMANTICALLY BLIND, STATISTICALLY LOUD (test, L154; preregistered, ceiling passed).** The reader abstains at 0.70 to 0.85 per route (0.07 committed-correct against 0.2 chance) while a five-feature mechanical baseline reads route at 0.48 and the process-aware ceiling passes at 0.78. Final artifacts underdetermine route as a story and mark it as surface residue; whether the residue is route structure or generation-style covariates is the owed trace-erasure follow-up, and the artifact-only equifinality claim narrows to the audit interface meanwhile |
| **G159** | Verified executed instructions leave recoverable evidence in the final artifact, against uninstructed twins with echo and consequence controlled | **SUPPORTED WITH THE ECHO CAP DISCLOSED (test, L146; preregistered, all gates quiet).** Executed problem-pool instructions recover at 0.86 in BOTH families against 0.22 on identical twins where nothing was executed (effect 0.64, z = 9.1); the twin leak gate, whose expectation is chance under null AND alternative, stayed quiet. The card's echo-disclosure rule fired: word overlap alone recovers executed instructions at 0.73, because executing a semantic instruction embeds its vocabulary, so the reader's demonstrated contribution beyond words is thirteen points, family-stable. The paired-delta interface adds nothing here (0.83) since the final text already realizes the choices; fabrication is context-dependent (0.05 on cold essays, 0.40 on visibly rewritten twins); the constraint-verification null replicates (surface arm 0.25 with the mechanical oracle at 1.0). The decomposition then overturned the cap (test, L148): on the 27 events where word overlap points at the WRONG candidate the reader still recovers at 0.852 against 0.22 in the twins, statistically unchanged from its echo-right cell, so the recovery evidence is echo-independent semantic realization that merely correlates with echo in aggregate |
|   | | *(this row's history now includes reader-form robustness: a non-generative conditional-likelihood reader, scoring only how well each candidate predicts the text, recovers the same recorded revisions at 0.78 against the 0.25 floor (test, L161), so the recovery does not depend on the prompted, answer-generating form)* |
| **H05-S3** | Local annotation persistence predicts the next ScholaWrite label | **SUPPORTED descriptively (test, L173).** The previous-label rule scores 0.883 against a 0.591 majority floor, under leave-one-project-out (the faithful text arms read 0.580/0.546 on different inputs, shown for scale). Keystrokes and annotation spans are not independent goal episodes. ArgRewrite spreadsheet order is not a chronological edit stream, so its 0.394 result cannot establish that goals persist within acts but switch between acts (L174); Stage 7 (P14, L353) asks for the switch itself on 12 held-out sessions per split: the direct reader is a nat and two nats under persistence over the scored windows (−1.27 and −2.50 against −0.18) and under uniform at the four switch positions the window holds (−1.67 against −1.10 on the better reader), so the switch's moment and direction are not read at this scale, and the card's support label against persistence rests on two sessions |
| **H03-S4** | The human writing record forecasts its next intention boundary beyond duration and label persistence once the text of the edit is read | **COUNTEREVIDENCE (test, L240), five projects.** Text plus duration reads 0.011 balanced accuracy UNDER duration alone on the online boundary forecast (interval below zero, four projects of five); the next distinct intention gains four to six points from an oracle previous label and loses ten from a label read off the text; the record's forecasting value is temporal, not lexical |
| **H01-S4** | Relay dependencies identify a director's choice beyond the shared convention | **COUNTEREVIDENCE (test, L249), 82 chains per arm.** A director's constraint decays through three relay hops faster under a shared convention than a remapped one (-0.22 against -0.09 from hop one to three), the shared chains keeping seven points more at hop three with the interval touching zero; the flip control reads zero, so what survives is the plans' generic tendency and not the choice's causal reach; the readers attribute nearly every tradition to a shared brief (director chains 0.22) |
| **H02-S4** | The ordered history of a tradition identifies how it changed beyond the final artifact | **VALID NULL (test, L250), 192 histories.** Ordered history minus artifact-only on five-type balanced accuracy -0.004 [-0.03, +0.02]; the readers call half of everything stable; the ordered history costs half a nat on the later decision; the exact stable-versus-marker-removed collision reads at chance both ways, as it must |
| **H01-S3** | Author purpose is harder to recover than surface detail on human exam passages | **REVERSED (test, L205), scope-bound (L206).** Purpose beats detail (+0.052, p=0.023) on the dense split with real passage lifts over question-only floors; the edge closes to +0.012 on the simpler split. Intended purpose is the EASY inversion, the bard's shaping measured; unintended structure is where difficulty lives. **Adversary survived (L220):** on items where the correct option is not the longest, the edge rises to +0.087 |
| **H04-S3** | Suggestion uptake tracks contextual fit where position and history failed | **INSTRUMENT DEAD for the proposed uptake inference (test, L207).** The implemented score is AUC 0.499, but a dismissed set of five suggestions was represented by its first suggestion. That is not the same decision unit as an individually selected suggestion. At the individual-suggestion grain (L253) the writer picks a better-fitting suggestion than chance within the set shown (pairwise 0.55 [0.52, 0.58], session-clustered) while taking the first-shown one 0.47 of the time, and individually dismissed suggestions fit no worse than selected ones between sets (AUC 0.51): a small fit preference under a large position default; Stage 7 (P13, L352) reruns the uptake question at the corrected unit on 30 held-out sessions: the position table (accept 51 percent, edit 25, dismiss 23, nearly flat across positions) is the best predictor, the prior decision sits at uniform, and the direct reader is under position by 0.30 [0.23, 0.36] and 1.57 [1.34, 1.82] nats and no better than the prior decision, so the decision is not read from the state beyond its marginal at this scale |
| **H03-S3** | Social intent (why did X act, what does X want next) is recoverable by the likelihood reader above a question-only floor, as rhetorical purpose was | **SUPPORTED (test, L233; unblocked from L208 by the parquet path).** Qwen 0.54 and SmolLM 0.48 on 600 SocialIQA items against question-only floors of 0.39 (both p<1e-5, random floor 0.33), lifts of the same size as the purpose lifts on exam passages |
| **D01-S3** | A standing director's reach is visible in and attributable from the team record | **NARROWED HARD (test, L186-L191, six cards), the with-grain reach surviving its assignment adversary (L230).** Only the with-grain director moves workers (+0.17 over marginal; cheap nil, fast negative); attribution recovers one of three directors because worker priors drown direction; the dose ruler fails on known doses (firm-minus-none +0.08, ns; hedged ties firm for one worker); central and distributed worlds do not separate by per-worker agreement; per-episode direction-vs-preference attribution is at chance with the record adding bias only; record-based forecasting of a fresh directed choice gains +0.04. The distributed-coherence rival's first measured case: the record identifies the WORKERS |
| **G130c** | The recovery margin survives the covariate matching that killed content-ness | **BETWEEN ITS OWN BANDS (test, L73), the raised floor DECOMPOSED (test, L126).** On the matched subset recovery holds (0.484) while the blind floor jumps (0.232 to 0.402), so the margin falls 22.7 to 8.2 points, real at exact McNemar p = 4.5 × 10⁻⁴ and 2.8× smaller. The prereg bands (survive ≥ 10, collapse < 5) leave 5 to 10 silent, so the formal call is neither. The floor's rise is 87% label-marginal alignment: matching reweighted the truth labels toward the ones the blind reader guesses by default, no text information involved, so the delta-specific remainder stands against a compositional floor rather than a covariate-information one. Owed: the powered matched replication, now the G129 confirmatory battery, whose matched draw truth-balances within common support to restore the analytic floor |
| **H-S7** | The location and type of a control change in a mixed human-and-model revision history are recoverable from the process record by process statistics, beyond stylometry and persistence and surviving surface normalization; the final artifact alone does not carry it | **NARROWED (test, L351), 5 histories per kind and 12 per adversary.** The process reader localizes a one-time switch within two events on 80 percent of human-then-model histories (−1.02 against the stylometry stack's −2.59) and survives the style-matched adversary where stylometry sits at chance (+1.92 nats [+1.30, +2.40] over the stack); it does not localize alternating control (−4.11) and puts three quarters of its mass on a spurious change under a pure style shift; both free-text readers are under the stack on every kind (−1.45 [−1.89, −0.95]); from the final artifact alone no program localizes anything and the direct reader reads under uniform |

**What the table says.** Recorded purposes are recoverable from the delta at confirmatory
grade, earned the hard way: the first battery replicated and then lost its label to its own
misspecified gate, and the second battery, gated correctly from birth, landed every control
quiet with recovery seed-stable to half a point. The claim's shape is now firm. Given the
old and new text, purpose recovery stands far above an analytic floor with a fabrication
bound of zero, twice; the matched margin holds at sixteen points but only at pilot power,
its permanent caveat; and nineteen surface measures of what changed beat the language-model
reader on identical events in both runs, so the representation starts from the feature block
while the reader contributes calibrated refusal, confined to interfaces that see both
versions of the text. Given only the finished artifact, the same reader recovers nothing it
can be proven to owe: chance on mechanically verifiable constraints once frequency is
balanced away, and an eleven-point transferring margin over word-echo on semantic
assignments that the exploratory corpus cannot split into executed choices versus leaked
assignment vocabulary. The reader is a semantic-correspondence instrument, not a constraint
verifier, and its honesty is format-bound: near-zero fabrication in forced choice with a
none option (one invention in ten even on thousand-word unspecified texts, with real
specifications recovered twelve points above the word-echo bar and diluting as
specifications multiply), massive over-credit in yes/no verification. The construct question, whether
any of this tracks decision structure rather than corpus particulars, now has its first
preregistered answer on the rebuilt factorial: executed choices ARE recoverable from final
artifacts against uninstructed twins, sixty-four points with every gate quiet and perfect
family transfer, of which thirteen points exceed the word-overlap bar. The Stage-3 human rows sharpen the ground from two sides: intended
rhetorical purpose reads MORE easily than detail on dense passages (the maker built the
legibility in), while suggestion uptake tracks contextual fit by five points within the set the
writer saw and position by twenty-three (H04-S3 at its right grain), and local annotation
persistence does not establish the timescale of a governing goal. The Stage 7 record row reads as the
walkthrough says it should: a program result about ground truth, with the artifact claim standing as a
power-bound claim that needs several artifacts by one maker and a stronger reader. And the director rows put a measured floor
under the errata's caution: a coherent team record identified its workers, not its lead, in
two of three directed worlds; social intent then reads on a second human bank at the same
lift as purpose (L233), and the one director effect that exists survives a fresh worker
assignment (L230). The cap then lifted
under its own mandated decomposition: where word overlap actively misleads, the reader still
recovers at eighty-five percent while the twins sit at chance, so the evidence is
echo-independent semantic realization rather than lexical matching, and every future recovery
table carries the echo-split cells as a standing report. The recovery is also
reader-form-robust: a likelihood-only reader that never generates an answer keeps
seventy-eight percent of the same target, so the channel belongs to the artifact rather
than to one reader's prompting form. The two corpora also bracket the reader's
fabrication behavior: honest on cold text, intent-attributing on visibly revised text. The
equifinality and ratification results draw the boundary of the whole section from the other
side, twice in one day: WHAT was
executed is recoverable from the final artifact (sixty-four points over twins), but HOW the
text was produced is not a readable story at all, since the route among five recorded
alternatives reads as mass abstention beside loud surface residue, and genuine negotiation
events (a thesis chosen over rejected rivals that provably survives into the text, a veto
that provably reshaped the plan) read at exactly chance under near-perfect record-side
ceilings. Content of choices carries; production topology and interaction control do not,
except as statistical
residue whose meaning waits on a trace-erasure test. That split is the observational-
equivalence position behaving as designed, and it routes route- and contribution-level
auditing to interfaces
that see records. The human writing record's online forecast lands beside the persistence
rows: what predicts the next intention boundary is how long the run has lasted and how
long since the last keystroke, and reading the text of the edit makes the forecast
slightly worse, so the record's next-intention signal is temporal rather than lexical at
this grain (H03-S4). The inheritance side then lands the same way from two constructions:
a director's single constraint does not survive three relay hops as anything a reader can
attribute, the shared convention keeps a little more of it while the flipped constraint is
kept just as often, and the readers call every tradition a shared brief (H01-S4); and an
ordered twelve-step history tells these readers nothing about how the tradition changed that
the final artifact did not, while costing them on the next decision (H02-S4). Content of
choices carries; topology, inheritance, and the timescale of a governing goal do not read at
this scale, which is the errata's caution measured. The hurried-versus-careful commission
remains the designed extension.
Confidence: the paired-delta recovery claim is replicated and controlled (two batteries,
gates quiet; scope one corpus, one reader family); the realized-choice result is one bad
test away (preregistered, one corpus pair, one reader family); the route-blindness result
is one bad test away, one construction deep, its surface-residue half unexplained; the
earlier artifact-only reads stay exploratory; the annotation result is one bad test away as a
descriptive measurement, one corpus, five projects; the current uptake inference is
instrument-dead; the collapse and floor decomposition stand as before. Stage 7's history track draws the same boundary on constructed mixed histories (H-S7, L351): a one-time
switch of control is readable from the process record by process statistics and by no free-text reader,
it survives a surface matched from one word pool, and the final artifact alone carries none of it. On the
human record the uptake question is answered at the corrected unit and at this scale (H04-S3, L352): the
writer's accept, edit, or dismiss is its marginal, and no reader reads the remainder from the state. On the
annotation record the next label is persistence and the switch is not read (H05-S3, L353): under
persistence where the label holds, under uniform where it changes.

## §7. Reader-side measurement: the second channel, briefly

The reader model supplies a second measurement channel for everything above, per-block affect
projections, within-text ratios, and specification-conditional scoring. **Its canonical rows live in
[`THREE_COGNITIVE_LAYERS.md`](THREE_COGNITIVE_LAYERS.md) Part II** and are not duplicated here. Two
conclusions transmit. Within-text ratios survive where reader-state measures die, and the
within-artifact *movement* of the reader's affective series carries the polish signature (§2).

# Part III: Contested estimators and prior art

## §8. Residualisation: the proposed depth estimator, and its objections

> **Depth does start as expertise being used.** That's more or less what it is. But it's explicitly
> removing the goals that are either too buried through the repetition process to be baked in
> alongside your automatic processes, or, definitionally, **the viewer-directed goals**, and the two
> off-the-top things that fit under that are **attractiveness and teaching.** This is more of a
> **late-stage estimator proposition**, less of a component set that I'm necessarily bounding until
> I find more data to support it. Still, those are the variables of interest I'm starting with.

Under §1's coordinates this is a **candidate estimator, not a definition**, and it faces four
recorded objections. Per the program it also runs **last**, behind choice recovery, expertise
separation, and a transferring remainder, with its validation ground being the parent simulation's
estimator tournament rather than another fitted corpus. **The habit-shadow objection, his own and
the serious one:**

> **Repeated reader-directed practices can become automatic and survive a subtraction.** So the
> remainder can contain polished habits as well as the expected problem-directed expertise. This is
> a problem, and it becomes a **precision weighting on how well you trust the signals** you get from
> these habits.

The subtraction removes *goals*; automaticity does not care what a repeated action was for, so the
rule-outs leave habit-shaped shadows that survive the subtraction, which also explains the
seductive-details effect from the inside. **Second**, the collapse objection. Depth-as-expertise is
a property of the maker's competence, while depth-as-decisions-recoverable is a property of what a
reader can get out, and the two come apart. **Third**, separability. *"I don't know if they're
extricable or not."* If an expert's aesthetic choices *are* their expertise, subtraction removes
signal. **Fourth**, the field that tried it. Archaeology's forty years of expertise-from-product
carry **no blind tests of skill classification, no confusion matrices**, and the one properly
factorial study reverses the result, its authors concluding that "the skills reflected in these
assemblages cannot be directly assessed based on standard quantitative proxies, which are highly
raw material and technique dependent." Skill signals mostly vanish once the medium is controlled. The honest asymmetry: their confound is
raw material; our medium is language, far more uniform, and the ladder is precisely the
identical-precore control their literature says is underused. Three imports stand regardless.
**Errors are clustered, not Poisson** (a rate on a small sample measures which burst you sampled);
**distinctions live in the residual, not the whole sequence**; and **nobody has ever tested expert
work done deliberately fast against novice work**, cheap for us, impossible for them. On the
subtraction's mathematics, his reservation stands recorded:

> Partialling out – I'm familiar with it, but I'm not sure it's mathematically appropriate for what
> we're doing here. We kind of need to find something that works with the alignment research as much
> as possible.

Partialling assumes additivity and sufficiently measured nuisance effects, and the value-depth
residue may be non-linear, interactive, and messier still, so the estimator choice is left to the
simulation tournament (G134) rather than decided here. The value ladder this estimator was meant
to serve (surface goals → applied expertise → values) is
[`THE_TRIPLE_INFERENCE.md`](THE_TRIPLE_INFERENCE.md) §4's residue-of-expertise claim; it is not
re-derived here.

## §9. Vocabulary and prior art: the naming search

Run because he asked for existing terms. The surface layer has **no** established term covering both
attraction and translation (audience design is a social-identity mechanism; reader-based prose is
text-only and normative; *surface features* in the expertise literature is a perceiver-categorisation
trap; aesthetic labour is bodies, not artifacts). The deep layer's terms exist and live in
archaeology and art history. **Chaîne opératoire** (the operational sequence reconstructed backwards
from the object, skill included), **facture** (the making, legible in the made), **technological
style** (patterning largely invisible to the maker), the **Morellian method** (attribution from
involuntary detail, our leaked layer, named in 1870). *Tacit knowledge* is rejected, since it
commits us to inarticulability. **The critique of chaîne opératoire is almost word for word the
attack we will face** (*"overformalized"*, an *"illusion of reading the minds of prehistoric
knappers"*), and his reading inverts it:

> I actually find that line about the attack on chaîne opératoire to be **quite optimistic**.
> Something that's over-formalised and also gives the illusion of reading the minds of people that
> aren't there, and the creators – **sounds frankly like exactly what we're looking for.** It's
> unscientific, but also perhaps a very natural human thing that does have error bars. **The
> natural process probably is captured, or is related to and uses several of the main channels that
> we all naturally use anyway.**

The limit that survives the inversion: an illusion that reliably reproduces a human reading licenses
claims about *what a reader recovers*, not about what the maker did, Baxandall's guardrail. His
**inferential criticism** (the Charge, "Paint!", and the Brief, the situated problems) is the
framework forty years early, including our position on intention, *"not a biographical mental fact"*
but a condition posited in arranging the circumstantial facts. Rejected names, kept as a record.
*Inverse planning* (takes action sequences; we have residue, and that gap is the contribution),
*the design stance* (runs forward), *reverse engineering* (recovers mechanism, not values), anything
with *empathy* in it (43 catalogued definitions). For the subtraction, **partialling out** is the
standard name; a reviewer will note that in statistics the residual is the *error* while here it is
the quantity of interest. Flag it always.
