# Sounding Line Phase 2.3: Curator-Language Reconstruction, Theory Delta, and Design Reconciliation

**Status:** Coding-agent application package, paired with the Phase 2.3 work package

**Curator:** Abraham Haskins

**Prepared:** 2026-08-21

**Repository snapshot reviewed:** `96a8b3c507ed0a580354e366e135ed20f1b12338`

**Companions:** `SOUNDING_LINE_PHASE_2_3_CONTEXT.md`,
`SOUNDING_LINE_PHASE_2_2_CONTEXT.md`, and
`SOUNDING_LINE_PHASE_2_2_THEORY_ERRATA.md`

**Repository destination if retained:**
`docs/design/PHASE_2_3_THEORY_AND_DESIGN_ERRATA.md`

This is an application package, not a sixth theory document. It reconstructs curator language from
the 2026-08-21 audio pass, specifies the resulting delta to the five existing theory owners, and
repairs the design-document authority map. Its contents should be folded into the existing files;
this file then remains as the provenance record for the pass.

---

## 0. Executive ruling

Today's discussion does not replace the triple inference or authorize a value-extraction detour. It
does four more local but load-bearing things:

1. It separates three objects that earlier prose allowed to blur together:
   - the reader's **best viewer-coherent reconstruction**;
   - a **reader-enactable route** by which the reader could recreate the artifact;
   - the maker's **historical causal process**.
2. It turns anomaly reading into an explicitly sequential process: perceptual access, origin,
   recognition, response, recurrence, and later integration must not be collapsed into one
   mutually exclusive mistake label.
3. It treats mixed production as a network of proposal, ratification, selection, veto,
   integration, repair, and acceptance, rather than as a token share or equal-weight decision
   count.
4. It exposes a genuine unresolved construct boundary: a Pankseppian channel may combine an
   inherited transition strategy with a state-dependent motivational or valence term. The current
   word **drive** may be doing both jobs. Phase 2.3 records that problem and does not solve it.

The most important editorial ruling is negative:

> **No existing curator quotation is deleted, rewritten, or marked superseded by this pass.**

Several existing AI-authored bridges require correction or qualification. Apparent tensions among
curator quotations remain visible until the curator explicitly chooses one over another. Lack of
support from today's conversation is not supersession, and a cleaner formulation is not permission
to erase an older one.

---

## 1. Fidelity protocol for reconstructed curator language

The audio transcript contains obvious punctuation failures, missing negations, false sentence
boundaries, and speech-recognition substitutions. Pretending that it is a stenographic record would
be less faithful than repairing it. Pretending that an analyst's synthesis is a quotation would be
worse.

This package therefore uses three labels:

| Label | Meaning | May enter a curator blockquote? |
|---|---|---|
| **A — high-fidelity reconstruction** | One contiguous thought with punctuation, fillers, repeated starts, and obvious transcription errors repaired. No proposition has been added. | Yes. Preserve this wording exactly when inserted and cite this package in the commit message. |
| **B — composite reconstruction** | The same proposition was stated across several adjacent passages or passes. The wording is faithful in content but was assembled for coherence. | No, not without later curator adoption. Use the proposition in clearly AI-authored prose. |
| **C — analyst formulation** | A distinction, guardrail, or consequence inferred from the curator's statements. | Never. It is AI prose and must not be formatted as his words. |

Light cleanup permitted inside class A:

- punctuation and paragraph boundaries;
- removal of fillers, abandoned sentence starts, and accidental repetition;
- repair of an obvious missing negation where the surrounding sentence makes only one reading
  coherent;
- repair of an obvious transcription substitution, while retaining the curator's register;
- restoration of an antecedent only when it is unambiguous from the immediately surrounding
  speech.

Cleanup not permitted:

- replacing a colloquial word with a more academic one;
- making an uncertain claim categorical;
- adding a testability condition the curator did not state;
- joining two tensions into a synthesized resolution and calling the result a quotation;
- quietly removing profanity, humor, or first-person uncertainty when either carries meaning;
- editing an existing theory-file blockquote to match a newer, smoother reconstruction.

Class A quotations below are eligible for insertion. Class B language is still harvested because
it records what the curator meant, but it must remain visibly reconstructed or be translated into
AI prose.

---

## 2. Reconstructed curator language

### Q23-1. Viewer-coherent reconstruction

**Class A · high confidence**
**Canonical owner:** `READER_HEURISTICS.md` §1
**Disposition:** Useful, but Phase 2.2 Q1 already gives the fuller version. Do not duplicate both.

> Human inversion is something like the best viewer-coherent reconstruction. You start from your
> own mental state and then adjust off of it.

This sharpens the phenomenology without claiming that the reconstruction is historically correct.
If Phase 2.2 Q1 lands, retain this wording in the errata only and let Q1 carry the canonical quote.

### Q23-2. Context reweights possibilities

**Class A · high confidence**
**Canonical owner:** `READER_HEURISTICS.md` §4
**Disposition:** Insert.

> The low-quality-paint inference was a shifting of possibilities—the generations of your
> generative model being weighted differently—not an immediate inductive set of steps.

The example is useful precisely because it blocks a brittle inference such as “cheap material,
therefore poor maker, therefore grief metaphor.” Material information changes a distribution over
maker models. It does not dictate the next story.

### Q23-3. A reader-enactable route can be useful without historical identity

**Class A · medium-high confidence**
**Canonical owner:** `THE_TRIPLE_INFERENCE.md` §2
**Disposition:** Insert.

> Ideally, what you want to extract from the process is how you could create this thing. If you
> misunderstood exactly how they made it but converged on a way that you could make it, that would
> still be useful.

This is not a concession that the historical process is irrelevant. It identifies a second useful
output that ordinary human appreciation and artistic reproduction often accept.

### Q23-4. Sounding Line bears an extra historical burden

**Class B · high content confidence**
**Canonical owner:** `THE_TRIPLE_INFERENCE.md` §2, as AI prose
**Disposition:** Do not insert as a blockquote.

> Sounding Line may have to go one step beyond ordinary human inversion. A person can stop at a
> coherent route they could use; the instrument has to keep that route separate from the process
> the maker actually used.

This sentence reconstructs a conclusion reached over several passages. It is the cleanest statement
of the design consequence, but not a stenographic quote.

### Q23-5. Mistakes as a perspective vertex

**Class A · high confidence**
**Canonical owner:** Phase 2.2 Q6 in `READER_HEURISTICS.md` §2
**Disposition:** Redundant with the already-harvested quote; retain here, do not duplicate.

> Mistakes are almost certainly an interesting vector that, if you can find one, gives you a way
> into the author's perspective. Trying to fix it, conceal it, or cover it up is very different
> from not noticing it or making it repeatedly.

This is the same ruling as Phase 2.2 Q6 with a slightly cleaner transcription. The earlier quote
should remain canonical because it was already assigned an owner.

### Q23-6. Apparent errors should eventually revise the reader's model

**Class A · high confidence**
**Canonical owner:** `READER_HEURISTICS.md` §4
**Disposition:** Insert.

> Every apparent mistake is suspicious because it may mean you do not understand the maker. If too
> many of them are ignored, it becomes more likely that they are intentional and that your model of
> what the maker was trying to do is wrong.

This gives the anomaly method a global correction. The reader cannot preserve a favored maker model
by inventing a separate local failure for every deviation.

### Q23-7. Failure to notice is one decision, except where perception fails

**Class A · high confidence**
**Canonical owner:** `DECISION_TRACES.md` §3
**Disposition:** Insert.

> Failure to notice is one decision, with the sole exception of physical or perceptual failure.
> Divided attention, exhaustion, and absent expertise are context; they are not decisions.

This is an ontology ruling at the episode resolution. It does not imply conscious deliberation and
does not license a reader to infer non-recognition from a silent artifact without uncertainty.

### Q23-8. Non-recognition still occurs under secondary-goal competition

**Class B · high content confidence**
**Canonical owner:** `DECISION_TRACES.md` §3, as AI prose
**Disposition:** Do not insert as a blockquote.

> When perception was available, those cases are still exploiting the situation for a secondary
> goal. At minimum, they may conserve energy, attention, time, or money. The difficult inference is
> not whether some competing goal existed; it is which goal was being served.

The final sentence is the important scientific boundary. The ontology may say that another goal
won. A measurement earns credit only by discriminating among candidate goals or predicting a later
choice; “energy saving” cannot become an explanation that fits every omission after the fact.

### Q23-9. Notice-and-ignore is a different evidence state

**Class A · high confidence**
**Canonical owner:** `DECISION_TRACES.md` §3
**Disposition:** Insert beside Q23-7.

> If you notice a deviation and leave it in place, you are exploiting it for convenience or for
> some other purpose. Notice-and-ignore is therefore evidence about a secondary goal.

This remains compatible with Q23-8: failure to notice and notice-and-ignore may both involve
secondary-goal competition, but only the latter contains evidence of recognition.

### Q23-10. Ordered accidents

**Class B · high content confidence**
**Canonical owner:** `DECISION_TRACES.md` §3, as AI prose
**Disposition:** Do not insert as a blockquote.

> Ordered accidents are possible. Something can begin accidentally and acquire order through the
> maker's response to it.

The first sentence was stated directly. The second reconstructs what the surrounding discussion
made explicit: accidental origin and deliberate later integration are different variables.

### Q23-11. Collaboration is a network of acceptance

**Class A · medium-high confidence**
**Canonical owner:** `DECISION_TRACES.md` §1
**Disposition:** Insert.

> Collaborative work is a network of acceptance. Everyone involved gets to pass judgment on
> everyone else's work a little bit, and the human decision may be recognition and integration
> rather than generation.

The film example is not a metaphor pasted onto model use. It identifies ratification and integration
as real process events without pretending every participant controls every level equally.

### Q23-12. The complete interaction trajectory is the mixed-control object

**Class B · medium confidence**
**Canonical owner:** `DECISION_TRACES.md` §1, as AI prose
**Disposition:** Do not insert as a blockquote.

> For mixed work, the stable object is the complete interaction trajectory. The resulting structure
> may not belong fully to either participant. That is why collaborative artifacts have credits.

The transcript dropped an apparent negation in the second sentence; the surrounding movie example
makes the intended reading clear. Because the reconstruction repairs content rather than only
punctuation, keep it out of curator blockquotes.

### Q23-13. Expertise as compiled trajectory structure

**Class B · high content confidence**
**Canonical owner:** `THREE_COGNITIVE_LAYERS.md` §1, as AI prose
**Disposition:** Do not insert as a blockquote; use to reconcile Phase 2.2 Q2 and Q4.

> Expertise is compiled decision structure. It constrains the trajectory, pre-solves lower-level
> parts of the process, and lets you stack more decisions on top.

This is a synthesis of three compatible statements. It must not replace the sharper Phase 2.2 quote
that expertise is a trajectory constraint.

### Q23-14. Tools and context condition deployed expertise

**Class A · medium-high confidence**
**Canonical owner:** `READER_HEURISTICS.md` §6
**Disposition:** Insert.

> Deployed expertise is context-relative. If you do not know what tools they had, it can become
> impossible to work out what the trace cost or what competence it required.

This is the archaeology boundary in the curator's own terms. The same artifact trace can imply very
different work under different available tools.

### Q23-15. An LLM may supply a coarse human generative prior

**Class B · high content confidence**
**Canonical owner:** `THREE_COGNITIVE_LAYERS.md` §2, as AI prose
**Disposition:** Do not insert as a blockquote.

> To an extent, by definition, a language model replicates a human generative model. That does not
> make it the human causal process, but it may give us a coarse starting model for reconstruction.

The second sentence is the necessary boundary supplied by the rest of the conversation. Phase 2.3
Wing G is the functional test: does this prior improve recovery of held-out process facts?

### Q23-16. Pankseppian channels may be evolved expertise

**Class B · medium-high content confidence**
**Canonical owner:** `THE_TRIPLE_INFERENCE.md` §4–§5, as an unresolved construct note
**Disposition:** Do not insert as a blockquote and do not rewrite the current drive definition.

> Panksepp's channels may be expertise from evolutionary sources: previously ironed-in strategies
> for broad classes of problems, adjustable but resistant. I think “drives” is doing two jobs in
> our language—referring both to those channels and to something earlier that assigns valence or
> need. We are not ready to separate them cleanly.

This is an important possible correction and an explicitly unfinished one. It belongs in the theory
as a construct warning, not as a settled replacement ontology.

### Q23-17. Defer the difficult leg

**Class A · high confidence**
**Canonical owner:** this errata and the Phase 2.3 boundary, not a theory blockquote
**Disposition:** Preserve as a phase ruling.

> The drives–expertise relationship is going to get ugly. Luckily, we do not need to figure out
> that leg of the inference yet.

No Phase 2.3 result should be described as value or drive recovery merely because it improves
process inversion.

### Q23-18. Pattern establishment and violation as an exploratory cue

**Class B · medium confidence**
**Canonical owner:** no theory owner yet
**Disposition:** Design consequence only.

> One way to find order may be to establish a pattern and then look at how the maker violates it.

This is a candidate method, not a theory claim. It is already operationalized by Phase 2.3 Wing F
and should enter `READER_HEURISTICS.md` only if the test produces evidence.

---

## 3. What the reconstructed language changes

### 3.1 The process leg now has three reportable objects

The cleanest model is not a fourth inference. It is a three-way distinction inside the existing
process target:

| Object | Question | What can validate it? | Failure mode if confused |
|---|---|---|---|
| **Viewer-coherent maker model** | What account of this maker makes the artifact coherent to reader R under context C? | Calibration, reader variation, context sensitivity, and model revision | A flexible reader mistakes self-projection for discovery |
| **Reader-enactable route** | What process could reader R use to recreate the relevant structure? | Successful reenactment or held-out construction choice | Productive imitation is reported as historical fact |
| **Historical process** | What did the maker actually do? | Process records, version history, withheld interventions, tool traces, or matched known-answer construction | A plausible story is scored as causal recovery |

These objects can converge, but none implies the others. An expert reader may find a highly useful
reenactment route that is historically wrong. A historically correct account may be unusable to a
reader who lacks the maker's tools or body. A viewer-coherent story may explain the artifact while
predicting nothing outside the evidence that built it.

The resulting Phase 2.3 rule is:

> Report historical correspondence, reenactment usefulness, and viewer coherence separately.
> Artifact-only evidence may support the latter two. Historical-process claims require an
> independent process anchor.

### 3.2 Context is Bayesian in function even when no Bayesian formalism is claimed

Biography, poverty, tools, medium, sadness, model family, and domain expertise do not form a chain
of deductions. They alter which maker-process hypotheses are plausible and which artifact traces
become legible. The low-quality-paint example is therefore a model of **reweighting**, not a license
for biographical storytelling.

The theory should say “changes the reader's posterior” or “reweights candidate maker models” rather
than “reveals the maker was poor.” The instrument should test whether context improves held-out
recovery and whether misleading context predictably harms it.

### 3.3 An anomaly is a sequence, not a type

The earlier mistake vocabulary was too exclusive. The following can coexist:

- accidental origin;
- perceptual availability;
- failure to notice at one time;
- later recognition;
- repair or concealment;
- retention for convenience;
- exploitation for a secondary goal;
- downstream integration into an ordered structure;
- recurrence through habit;
- reader misclassification caused by unfamiliar expertise.

An “ordered accident” is therefore not a contradiction. It is an accidental-origin event followed
by recognition, retention, and integration. Likewise, a repeated anomaly can begin as an accident
and become habit, a deliberate device, or a repaired-but-recurring limitation.

### 3.4 Secondary-goal ubiquity needs an evidential guardrail

The curator's ontology treats perceptually available non-recognition or non-repair as occurring
under a competing goal: conserve effort, continue the main task, protect status, save money, meet a
deadline, preserve an aesthetic effect, or something else. This is coherent with the trajectory
model. It is also dangerously easy for a reader to fit after the fact.

The testable distinction is:

- **ontological claim:** some competing trajectory won;
- **evidential claim:** the artifact discriminates which trajectory won;
- **predictive claim:** the recovered trajectory predicts a later choice, repair, omission, or
  response.

The coding agent must never score “a secondary goal existed” as a success. Success requires either
correct candidate discrimination or held-out consequence prediction.

### 3.5 Mixed control is topological, not additive

A thesis, prompt, accepted candidate, veto, repair pass, and punctuation correction are not
exchangeable units. Mixed control is a directed contribution network. Upstream decisions may
pre-empt downstream search; downstream ratification may accept, reject, or rebuild the proposal;
later integration can make an initially foreign contribution part of a coherent artifact.

No scalar human/AI ratio is the ontology. If a scalar is derived for a downstream product, it must
be explicitly derived from a richer event graph and must not be treated as ground truth.

### 3.6 “Drive” is now a flagged jingle-jangle risk

The current files distinguish learned expertise from active drives. Today's discussion adds a
possible deeper split:

1. an inherited action or emotion channel that behaves like a pre-solved transition strategy;
2. a state-dependent signal that assigns salience, need, or valence and recruits that channel;
3. a persistent organization of those pressures across episodes, currently called values.

This is not ready to replace the existing table. It is ready to prevent future experiments from
using one broad “drive” label as though all three meanings had been measured.

---

## 4. Quote-preservation and supersession review

### 4.1 Result of the review

**Zero existing curator quotations require deletion or in-place editing.**

Today's language sharpens some older quotations and creates tensions with others, but it does not
establish that the curator has withdrawn them. The appropriate action is to preserve the old quote,
add a current clarification only where useful, and mark the construct unresolved in AI prose.

### 4.2 Apparent tensions that are not supersessions

| Existing language | New language | Ruling |
|---|---|---|
| “I would assume that drives are upstream of even process.” | Pankseppian channels may be evolved expertise, while another pre-emotional variable supplies valence or need. | Compatible enough to preserve. “Drive” may contain more than one object; upstreamness remains an open topology claim. |
| Expertise is a trajectory constraint. | Expertise is compiled decision structure and a record shaped by past attention. | Compatible. Past attention helps form the constraint; it is not the definition of the current functional object. |
| A model's ordinary choices may not be human-invertible without forced rationale. | An LLM may supply a coarse human generative prior. | Compatible. A useful prior does not make the model's own causal process naturally human-readable. |
| Humans infer process through embodied simulation of the creator. | The useful result may be a route the reader could enact rather than the exact historical route. | Compatible but newly differentiated. Embodied simulation can generate a reenactment candidate without proving history. |
| “AI isn't interacting with this. It's only trying to take, it's not giving.” | Ratification and integration can make mixed creation a network of acceptance. | Compatible when the older quote is scoped to ordinary one-way production. Phase 2.2 already requires that qualification. |
| Corporate work can flatten subsidiary goals. | Apparent flattening can reflect observer ignorance, aggregation, or unfamiliar corporate expertise. | Compatible as competing production accounts. Keep the quote; replace categorical AI prose. |

### 4.3 Existing curator quotes that must remain untouched

At minimum, the coding agent must not normalize or splice the following while applying this pass:

- the original and superseding triple-inference formulations at the head of
  `THE_TRIPLE_INFERENCE.md`;
- the trajectory, attention, and drive-commonality quotations in its §2–§5;
- the “ghosts of a human brain” and Panksepp quotations in
  `THREE_COGNITIVE_LAYERS.md`;
- the polish/depth, corporate, soul, and machine non-invertibility quotations in
  `DECISION_TRACES.md`;
- the anomaly, interest, bard, and generated-text asymmetry quotations in
  `READER_HEURISTICS.md`;
- every quote in dormant `ALIGNMENT.md`.

If any quote appears wrong after the AI prose is repaired, place it in a curator-confirmation table
with the exact old wording, the exact candidate replacement, and a yes/no question. Do not delete it
in the same commit.

---

## 5. Application preconditions

1. Confirm the current default-branch commit. This package reviewed `96a8b3c5`; remap every anchor
   if the repository advanced.
2. Read `docs/theory/README.md` in full immediately before editing.
3. Land or reconcile `PHASE_2_2_THEORY_ERRATA.md` first. This package is a delta to it, not a
   replacement.
4. Copy the Phase 2.2 and Phase 2.3 packages into `docs/design/` only if they are not already present.
5. Make quote insertions and AI-prose changes in separate commits or, at minimum, separate diff
   hunks. A reviewer must be able to see that no old quote text changed.
6. Do not change hypothesis statuses merely because a concept was clarified. These are theory and
   design corrections, not experimental results.
7. Do not create a sixth theory file.

---

## 6. File-by-file theory delta

## 6.1 `THE_TRIPLE_INFERENCE.md`

### A. Add a small subsection inside §2: “Historical process and reader-enactable process”

**Anchor:** after the Phase 2.2 reconstruction-and-projection boundary and before the discussion of
attention/formalisms.

Insert Q23-3, then add this AI-authored table:

| Process-side output | Definition | Honest evidence claim |
|---|---|---|
| **viewer-coherent reconstruction** | the best maker/process model reader R can assemble from artifact O and declared context C | reader-relative coherence and calibration |
| **reader-enactable route** | a process reader R could use to recreate the relevant structure | constructive usefulness, tested by reenactment or held-out construction choice |
| **historical process** | the maker's actual sequence of decisions, actions, tool uses, and interactions | correspondence only where independent process evidence exists |

Follow it with:

> These are three outputs inside the existing **process** target family, not a fourth inference.
> They can overlap without being identical. Artifact-only reading can support a useful reenactment
> while leaving the historical route observationally underdetermined. Sounding Line reports them
> separately rather than deciding in advance that one substitutes for the others.

### B. Index the reader explicitly in the inverse account

Phase 2.2 already replaces the unindexed posterior. Add one sentence to that replacement:

> The reader's output includes both a posterior over maker histories and a distribution over routes
> the reader could enact. The latter is conditioned on the reader's body, expertise, and tools and
> therefore cannot be silently reported as the former.

Do not add a more elaborate mathematical ontology. The file is already formal enough to preserve
the distinction with named variables; Phase 2.3 supplies the operational scores.

### C. Add equivalence classes to §7's identifiability boundary

**Anchor:** after the Phase 2.2 correction to the “known transition model = expertise” row.

Add:

> Several historical processes can leave the same observable artifact under the same declared
> context. Where no held-out trace distinguishes them, the honest historical output is an
> equivalence class or posterior over processes. A reader-enactable route may still be useful in
> that case, but it does not collapse the class. Context can reweight the members; it cannot create
> evidence that the artifact and records do not contain.

This is a consequence of the existing identifiability position, not a new hypothesis row.

### D. Add the drive/expertise construct warning to §4 or §5

**Anchor:** after §4's working-vocabulary paragraph, before §5's four candidate accounts.

Add this visibly unresolved AI-authored note:

> **Unresolved construct boundary.** “Drive” may currently bundle at least two things: an inherited,
> adjustable-but-resistant transition strategy, and the state-dependent assignment of salience,
> need, or valence that recruits it. The first can look like expertise supplied by evolution; the
> second remains closer to the active motivational pressure in §1's table. This pass does not
> choose a topology or rename either object. Until the distinction is tested, no result on a broad
> Panksepp label licenses a claim about both.

Do not insert Q23-16 as a blockquote. Do not mark “drives are upstream of process” superseded. Do
not wake any §5 value experiment.

### E. Keep the scope boundary explicit

At §8, after the human-invertibility boundary from Phase 2.2, add one sentence:

> Human-invertible may therefore mean historically corresponding, productively reenactable, or
> merely viewer-coherent; every use in an empirical report must name which.

## 6.2 `THREE_COGNITIVE_LAYERS.md`

### A. Reconcile compiled structure with trajectory constraint

Apply Phase 2.2 Q2 and Q3 first. Do not insert Q23-13 as a quote. Add this AI-authored paragraph
after them:

> Calling expertise “compiled decision structure” describes its formation history, not a list of
> past decisions stored intact. Practice, attention, correction, embodiment, and inherited
> constraints alter which trajectories are visible, cheap, and reliable now. Automaticity
> pre-solves lower-level control and permits focal attention to operate elsewhere. The functional
> object remains the trajectory constraint named in Q2.

This should replace, not sit beside, the current AI sentence that defines cognitive expertise as
the higher-order metaphorical layer.

### B. Flag the inherited-strategy ambiguity in the human scaffold

**Anchor:** immediately after the three-row functional-scaffold table in §1.

Add:

> The middle row is a provisional functional aggregate. A conserved affective channel may combine
> an inherited action-selection prior with a state-dependent motivational signal. That possible
> split is owned by `THE_TRIPLE_INFERENCE.md` §4–§5 and remains unresolved. It must not be turned
> into a clean anatomical or transformer address.

Do not rename the row yet. A premature rename would make the current uncertainty disappear from the
documentation.

### C. Replace the categorical LLM bridge with a functional hypothesis

Apply Phase 2.2 §4.2D. Then add:

> For Phase 2.3, “human generative prior” has only a functional meaning: a model supplies candidate
> human-coherent processes that improve recovery of facts withheld from the candidate-generation
> step. Fluent mental-state labels and a plausible rationale do not count. Wing G compares this
> prior against target-specific context, a nonhuman control prior, and no generative prior.

Q23-15 remains in this errata because the existing curator quotation already states the useful
portion more precisely: human training data may induce functional regularities of the generating
process.

### D. Do not add a new architecture hypothesis yet

The evolved-expertise idea has no Phase 2.3 measurement and the LLM-prior claim already has a design
in Wing G. Do not create new G-numbers merely to restate them. Results, if any, should first update
existing bridge rows and their afterwords.

## 6.3 `DECISION_TRACES.md`

### A. Replace mixed contribution as a count with a contribution network

**Anchor:** §1, after the Phase 2.2 cognitive-preemption insertion.

Insert Q23-11, followed by:

> Mixed production is represented as a directed event graph. An event may propose, select, ratify,
> veto, integrate, repair, reject, or accept another event. The same participant may occupy several
> roles, and one event may have several parents. Upstream structure can make downstream work cheap;
> downstream ratification can accept that structure or rebuild it. Surface volume and equal-weight
> event counts therefore do not identify control.

Extend the event schema with these optional fields:

| Field | Purpose |
|---|---|
| `actor_id` | participant or tool responsible for the event |
| `event_role` | propose, select, ratify, veto, integrate, repair, reject, accept, execute |
| `parent_event_ids` | events this one acts on or depends on |
| `alternatives_available` | candidates actually available at the time |
| `accepted_by` / `rejected_by` | later ratification or veto |
| `downstream_scope` | which later choices became easier, impossible, or unnecessary |
| `trace_support` | artifact or record evidence supporting the event |

The event graph is the ground-truth object where interaction logs exist. Any downstream scalar must
declare its aggregation rule and must not be called a human/AI decision ratio.

### B. Add a sequential anomaly-handling schema inside §3

**Anchor:** the anomaly-handling subsection proposed by Phase 2.2 §4.3H.

Replace the earlier mutually exclusive label list with this multilabel sequence:

| Field | Values | What it separates |
|---|---|---|
| `perceptual_access` | available, degraded, unavailable, unknown | non-recognition from inability to receive the cue |
| `origin` | intended, accidental, forced by constraint, indeterminate | initial cause from later handling |
| `recognition` | noticed, failed-to-notice, indeterminate, not-applicable | awareness from occurrence |
| `response` | repair, conceal, compensate, abandon, retain, exploit, no-visible-response, unknown | counterfactual preference and handling |
| `recurrence` | isolated, repeated, escalating, diminishing, unknown | one-off accident from habit or persistent limitation |
| `integration` | none, local, downstream, global, unknown | accidental residue from ordered adoption |
| `candidate_secondary_goal` | open vocabulary plus evidence | what non-repair or retention served |
| `reader_uncertainty` | calibrated probability or abstention | artifact underdetermination |

Add Q23-7 and Q23-9. Then add:

> At the episode resolution, perceptually available failure to notice is recorded as one decision
> event. Exhaustion, divided attention, absent expertise, time pressure, and similar conditions are
> context fields, not extra decision events. Physical or perceptual unavailability is not coded as
> failure to notice. This ontology does not make awareness observable: where the artifact cannot
> separate the states, the reader must return indeterminate.

### C. Add the secondary-goal measurement guardrail

Immediately after the schema, add:

> The theory permits the claim that some competing goal governed a perceptually available omission.
> The instrument receives no credit for that generic claim. It must either choose the correct goal
> from matched alternatives, localize evidence that distinguishes it, or predict a held-out
> response. “Convenience,” “energy saving,” and “status” are candidate explanations, not universal
> residual bins.

This is class C analyst prose. It is necessary to keep Q23-8 falsifiable rather than to narrow it
away.

### D. Add ordered accidents without adding a contradictory category

After the anomaly schema, add:

> **Ordered accident** names a sequence, not an origin type: accidental or indeterminate origin,
> followed by recognition or retention, then local or downstream integration. Later order is
> evidence about handling and adoption; it is not proof that the original event was planned.

No new exclusive `ordered_accident` label is needed; derive it from the fields. This prevents the
same event from being forced into either “accident” or “deliberate decision.”

### E. Leave terminal organization to the Phase 2.2 correction

Today's pass adds no reason to remove the corporate, machine, or soul quotations in §4. Apply the
conditional topology and reader-relative qualifications from Phase 2.2. Do not rewrite the quotes
or add a new maker-type table.

## 6.4 `READER_HEURISTICS.md`

### A. Keep Phase 2.2 Q1 canonical and use Q23-1 as its short gloss

Insert Phase 2.2 Q1 in §1 as planned. Do not place Q23-1 beside it as a second blockquote. Add one
AI sentence after Q1:

> This is the best viewer-coherent reconstruction: the reader begins from itself, then adjusts
> toward a maker model using artifact evidence and context.

This avoids quote proliferation while retaining today's sharper term.

### B. Add probabilistic context adjustment to §4

Insert Q23-2, followed by:

> Context does not license a story in one step. It changes the relative probability of maker and
> process hypotheses, which should then change predictions about other evidence. A useful context
> cue improves held-out recovery; a misleading cue should cause a measurable, directionally
> coherent error. If neither occurs, the cue merely inspired a narrative.

Insert Q23-14 in §6, where the file already owns choice-versus-constraint and tool-conditioned
interpretation. Link back from §4 rather than duplicating it.

### C. Add a global model-revision rule to §4

Insert Q23-6, then add:

> Treat clusters of unexplained deviations as a posterior-predictive failure of the current maker
> model. Local repair stories may explain individual cases, but the reader must compare them with a
> global alternative such as unfamiliar expertise, a wrong primary goal, a hidden constraint, or a
> different maker/process family. The threshold is empirical: which update better predicts held-out
> choices or later handling?

This is the theoretical meaning of Phase 2.3 Wing D's global-model branch. It is not permission to
declare every dense anomaly cluster “expertise.”

### D. Keep anomaly handling and pattern violation in their proper places

Phase 2.2 Q6 remains the canonical mistake-handling quote in §2. The multilabel trace ontology lives
in `DECISION_TRACES.md`; §2 should link to it and explain how a reader uses it. Q23-18 remains a
design-only hypothesis until Wing F yields evidence. Do not add “pattern violation” to the adopted
heuristics dashboard before measurement.

### E. Distinguish the three process outputs in §10

After the Phase 2.2 calibration correction, add:

> Calibration is output-specific. Viewer coherence can be calibrated against reader behavior;
> reenactment can be scored against successful construction; historical correspondence requires
> process records or withheld causal facts. A high score on one is not a confidence score on the
> others. Where only the artifact is available, historical-process output must remain an
> equivalence class or abstention.

This supplies the reporting boundary without duplicating `THE_TRIPLE_INFERENCE.md`'s definitions.

## 6.5 `ALIGNMENT.md`

### A. Apply only the already-ratified Phase 2.2 repairs

The current file is explicitly dormant. Today's discussion does not authorize new alignment prose,
new hypotheses, or a trust-gating section. Apply the governor correction, anti-capture
qualification, Q10 bridge, counterfeit-invertibility failure mode, and AL-7 re-scope from Phase 2.2
if they remain unapplied.

### B. Make no Phase 2.3 change

The drive/expertise ambiguity belongs to the inference and architecture files. The fact that it may
later matter to values does not make it an alignment result. Q23-17 reinforces the existing
dormancy ruling.

**Reviewed outcome:** no new quote, no new section, no new hypothesis row, and no existing quote
changed.

---

## 7. Design-document reconciliation

## 7.1 What is actually messy

The design folder's problem is not that it contains too much history. The history is useful. The
problem is that documents written under different phases still speak in the present tense, while
the 23-line index does not distinguish authority by concern.

At the reviewed commit:

| File | Current useful content | Current ambiguity or stale claim |
|---|---|---|
| `PHASE_2_0_CONTEXT.md` | full vertical-slice rationale, product constraints, curator abstraction boundary | still titled and indexed as the governing brief even though Phase 2.3 changes the primary ontology |
| `EVAL_CONTRACT_2_0.md` | split discipline, calibration, hard slices, claim-language discipline | still asks for a binary substantial-model-contribution label and is awaiting a freeze that must no longer happen in that form |
| `BENCHMARK_2_0.md` | process records, lineage discipline, source and licensing work, free-path pilot | crossed provenance benchmark and “decision dose” can be mistaken for the current theoretical target |
| `SUCCESSOR.md` | anomaly entry, reconstructibility, graded human read, no provenance claim | a dated precursor whose build-status statements still read as operational; Phase 2.2/2.3 absorb and revise it |
| `DWELL_CORPUS.md` | a controlled corpus design and a clear simulator-derived reason | §5 still calls it “currently the highest-value unblocked item” |
| `ENGINEERING_LOOP.md` | the standing principle of wide, creative, constraint-aware search | the one-day measure-evolution proposal can be mistaken for the current scheduled build rather than a general search frame |
| `QUEUE.md` | historical ordering rationale and measured costs | already correctly marked superseded |
| `README.md` | a short inventory | no status vocabulary, current-phase pointer, conflict rule, or distinction between operative, reusable, deferred, and historical files |

The repair is an authority layer, not a purge. Preserve the old documents, put dated status banners
at their heads, and make the index answer “what controls this decision now?” before it explains the
history.

## 7.2 Adopt one status vocabulary

Use these exact status labels in `docs/design/README.md` and at the top of each design file:

| Status | Meaning |
|---|---|
| **OPERATIVE** | controls current design and execution where it speaks |
| **APPLICATION PENDING** | requested reconciliation package not yet fully folded into its canonical owners |
| **REUSABLE SUBSTRATE** | parts remain active infrastructure or construction guidance, but the file does not control the current theory or phase objective |
| **DRAFT — DO NOT FREEZE** | incomplete contract; current form is known to conflict with the operative phase |
| **DEFERRED** | valid design, not currently scheduled or highest priority |
| **HISTORICAL PRECURSOR** | preserved design reasoning that has been absorbed, narrowed, or superseded by a later package |
| **SUPERSEDED SNAPSHOT** | no present authority; retained for chronology and rationale |

Do not use “archived” for a file that remains in `docs/design/`; the repository already has a
separate `docs/archive/` meaning. “Historical precursor” is clearer.

## 7.3 Authority by concern after this pass

| Concern | Current owner | What older files still contribute |
|---|---|---|
| Phase objective and adaptive test tree | `PHASE_2_3_CONTEXT.md` | Phase 2.2 supplies the transition; Phase 2.0 supplies product and infrastructure constraints that do not conflict |
| Theory reconciliation | apply `PHASE_2_2_THEORY_ERRATA.md`, then this file | earlier theory quotes and result statuses remain canonical in the five theory files |
| Live work order | root `TODO.md` plus `runners/run_queue.py` | `QUEUE.md` is chronology only |
| Current empirical and operational state | `docs/STATE.md` and `FINDINGS.md` | phase packages explain why the work was designed, not what came back |
| Binding methods | `docs/method/README.md` and its triggered files | design packages may not relax method rules |
| Evaluation contract | `EVAL_CONTRACT_2_0.md` only after the in-place Phase 2.3 reconciliation below | its split/calibration discipline survives; its binary ontology does not remain primary |
| Process-record substrate | current schemas/results plus reusable portions of `BENCHMARK_2_0.md` | the unmatched provenance pilot is not a detector benchmark |
| Human-facing theoretical reporting | `PHASE_2_3_CONTEXT.md` §18 and the current `CLAUDE.md` workflow | Phase 2.0's four-class roll-up remains a compact result tag, not the whole analyst report |

Conflict rule for the index:

> Later phase packages supersede earlier packages only where they conflict. Empirical results,
> method constraints, curator quotations, licensing constraints, and reusable infrastructure do
> not become stale merely because the phase number advanced.

## 7.4 Replace `docs/design/README.md` with a real status index

The coding agent should rewrite the design README rather than append another paragraph. It should
remain short enough to scan and contain these sections in this order:

1. **Purpose of the folder.** Preserve the existing “method binds, design briefs” distinction.
2. **Current orientation.** Four direct links:
   - current phase: `PHASE_2_3_CONTEXT.md`;
   - current theory application order: Phase 2.2 errata, then Phase 2.3 errata;
   - live work: `../../TODO.md` and `../../runners/run_queue.py`;
   - empirical state: `../STATE.md` and `../../FINDINGS.md`.
3. **Status legend.** The seven labels in §7.2.
4. **Authority table.** One row per file, with status, concern, and successor/current owner.
5. **Conflict and maintenance rule.** The rule in §7.3, plus the existing rule that results do not
   live in design files.

The authority table should read as follows once the four phase packages are copied in:

| File | Status | Read it for |
|---|---|---|
| `PHASE_2_3_CONTEXT.md` | **OPERATIVE** | current adaptive process-inversion program and reporting protocol |
| `PHASE_2_3_THEORY_AND_DESIGN_ERRATA.md` | **APPLICATION PENDING**, then **HISTORICAL PRECURSOR** after application | today's reconstructed curator language, theory delta, and documentation reconciliation |
| `PHASE_2_2_CONTEXT.md` | **HISTORICAL PRECURSOR** | transition from binary attribution to reconstruction profiles and the Phase 2.2 rationale |
| `PHASE_2_2_THEORY_ERRATA.md` | **APPLICATION PENDING**, then **HISTORICAL PRECURSOR** | prerequisite quote and AI-prose reconciliation |
| `PHASE_2_0_CONTEXT.md` | **HISTORICAL PRECURSOR** | the original vertical slice, product constraints, claims discipline, and curator abstraction boundary |
| `EVAL_CONTRACT_2_0.md` | **DRAFT — DO NOT FREEZE** until reconciled; then **OPERATIVE** | the single current evaluation contract |
| `BENCHMARK_2_0.md` | **REUSABLE SUBSTRATE** | process-record, lineage, licensing, matching, and manifest construction |
| `SUCCESSOR.md` | **HISTORICAL PRECURSOR** | the anomaly/reconstructibility design that led to the current program |
| `DWELL_CORPUS.md` | **DEFERRED** | a controlled same-maker structural-form corpus if the dwell question reopens |
| `ENGINEERING_LOOP.md` | **REUSABLE SUBSTRATE** | wide search, archive, and constraint-aware engineering principles |
| `QUEUE.md` | **SUPERSEDED SNAPSHOT** | the 2026-08-05 ordering rationale only |

After the errata are applied, change their index status from **APPLICATION PENDING** to
**HISTORICAL PRECURSOR** and add the application commit. Do not delete them; they are the provenance
for reconstructed quotes and AI-prose corrections.

## 7.5 Per-file design edits

### A. `PHASE_2_3_CONTEXT.md`

Copy the companion package unchanged to `docs/design/PHASE_2_3_CONTEXT.md`. Add no duplicate summary
to its body. Its existing status, snapshot, authority order, documentation permissions, and root
tree already make it the operative program.

If the repository has advanced since `96a8b3c5`, add a short reconciliation receipt under its
snapshot line rather than rewriting the historical snapshot:

> **Applied against:** `[new commit]`. Differences from the inspected snapshot: `[bounded list]`.

### B. `PHASE_2_0_CONTEXT.md`

Add this banner immediately below the title and current status:

> **Historical authority notice (2026-08-21).** This was the governing Phase 2.0 handoff. Phase 2.3
> now governs the active process-inversion program. Preserve this file for its product,
> infrastructure, claims, and curator-interface constraints where they do not conflict with later
> packages. Its binary attribution ontology and phase order are not current.

Do not edit its 1,300-line body to make it sound current. It is a historical brief. A mass rewrite
would erase the reason later corrections exist and create the sanding risk the curator identified.

### C. `EVAL_CONTRACT_2_0.md`

Add this banner before any other change:

> **DRAFT — DO NOT FREEZE.** The 2026-08-16 binary task is retained as a possible downstream product
> layer, but it no longer defines the primary Phase 2 task. Reconcile this file with the Phase 2.3
> reconstruction profile before curator sign-off. There must be one active evaluation contract,
> not a binary contract and a process contract that can disagree.

Then revise the file in place according to §7.6. Keep the filename during the draft to avoid broken
links and two competing contracts. After the content freezes, a dedicated link-cleanup commit may
rename it to `EVAL_CONTRACT.md`; do not rename it casually in the application commit.

### D. `BENCHMARK_2_0.md`

Add:

> **Reusable substrate notice (2026-08-21).** Lineage, process records, licensing constraints,
> manifests, and matching discipline remain active. The crossed provenance task is not the current
> primary ontology, and the unmatched G153 pilot does not license provenance evaluation. Phase 2.3
> reuses the records for within-construction known-answer process tests.

In §4, replace “Decision-dose decomposition” with **“Contribution-process decomposition.”** Retain
prompting, selection, ordering, constraints, edits, and structural revisions, and add proposal,
ratification, veto, integration, repair, acceptance, actor, parent-event links, and alternatives
available. Replace the sentence permitting a compact dose variable with:

> A compact scalar may be derived for a declared diagnostic, but it is not ground-truth authorship
> share, decision weight, or participant control. The event components and interaction graph ship
> and remain the adjudication record.

Do not rewrite the licensing or acquisition sections merely because the benchmark's role changed.

### E. `SUCCESSOR.md`

Add:

> **Historical precursor notice (2026-08-21).** This design was written before Gate 3 and retains
> that evidential value. Its anomaly pass, reconstructibility output, graded reader interface, and
> no-provenance boundary are absorbed into the Phase 2.2/2.3 program. Build-status and queue claims
> below describe 2026-08-03, not current execution.

Do not modernize the old build table or change its curator quotes. The point is to preserve what was
specified before later results while preventing a new agent from treating it as the live queue.

### F. `DWELL_CORPUS.md`

Add:

> **Deferred design notice (2026-08-21).** The controlled same-maker/two-form design remains valid,
> but it is not the current highest-value unblocked item. Phase 2.3's known-answer process roots
> govern current work. Reopen this corpus only if a live branch again requires a dwell-definedness
> test.

In §5, replace only the AI-authored present-tense priority sentence. Preserve the design and any
curator language. The replacement should say that it was the highest-rated unblocked corpus request
on 2026-08-05 and is now deferred behind the process-inversion root map.

### G. `ENGINEERING_LOOP.md`

Add:

> **Reusable design principle (2026-08-21).** Wide candidate generation, explicit constraint
> evaluation, archive preservation, and avoidance of population-size-one search remain binding
> principles. The specific measure-evolution loop is not automatically the current scheduled build;
> Phase 2.3's adaptive branch registry is the operative application of the broader search frame.

Do not rewrite its original argument or quote. In the design README, point scheduled work to
`TODO.md`, not this proposal.

### H. `QUEUE.md`

No body change. Its superseded banner is already correct. The design README should use
**SUPERSEDED SNAPSHOT** and direct all live work to `TODO.md` and the runner.

## 7.6 Rewrite the single evaluation contract around reconstruction

The current evaluation contract's strongest material—frozen splits, calibration, hard slices,
claim-language tiers, and one decisive evaluation—should survive. Its primary binary target should
not.

### A. Primary task

Replace §1's primary task with:

> Given an artifact, declared context, and a bounded reader interface, produce a calibrated
> reconstruction profile that keeps viewer-coherent explanation, reader-enactable process,
> historical-process correspondence, contribution-network recovery, and abstention separate.

The generative-model substantial-contribution probability may remain as an optional downstream
product output. It must be trained and scored separately and may not redefine the process labels.

### B. Required outputs

| Output | Minimum representation | Known-answer ground truth |
|---|---|---|
| `viewer_model` | ranked maker/process hypotheses plus evidence | reader calibration and held-out consequence, never plausibility alone |
| `reenactment_route` | ordered process candidate with prerequisites | successful recreation or withheld construction choice |
| `historical_process` | posterior/equivalence class over recorded events | version history, interaction logs, tool traces, or controlled construction |
| `contribution_network` | actor-role event graph | logged proposal, selection, ratification, veto, integration, repair, acceptance |
| `anomaly_trajectory` | access, origin, recognition, response, recurrence, integration | controlled anomaly histories and process records |
| `uncertainty` | calibrated confidence plus abstention reason | held-out calibration, per-interface |
| `optional_provenance` | downstream binary or regime distribution | independently adjudicated regime labels, never inferred from the process score by definition |

### C. Metrics

Retain calibration, abstention, worst-slice reporting, author/domain/generator/lineage separation,
and seed intervals. Replace headline F1 as the primary with a panel:

- matched-candidate historical event recovery;
- held-out process-fact prediction;
- reenactment success or structural-choice recovery;
- actor-role and dependency-edge recovery for mixed control;
- anomaly-state confusion matrices, reported per field;
- evidence localization;
- calibration and selective risk for every output separately;
- improvement over context-only, artifact-only surface, and no-generative-prior baselines;
- divergence between viewer coherence and historical correspondence.

No average across these metrics produces an “intent score.” A downstream product may learn a
decision rule only after the panel shows which outputs are valid.

### D. Adjudication set

The abandoned binary adjudication exercise should become a process-profile adjudication set. Each
case records:

- the interaction trajectory;
- participant roles and actual alternatives;
- which decisions were proposed, accepted, vetoed, or rebuilt;
- process facts withheld from the reader;
- whether a reenactment route different from history would still work;
- anomaly access/recognition/handling fields where applicable;
- observationally equivalent histories;
- what the artifact-only reader is allowed to abstain on.

Human annotation is not “human or AI?” It is process-record verification and, where needed, a
graded assessment of the usefulness of reenactment.

### E. Freeze rule

Do not freeze until:

1. the output distinctions above are represented in the schema;
2. at least one known-answer example populates every field;
3. historical and reenactment scoring can disagree without either being treated as an error in the
   other;
4. contribution graphs support mixed control without a token-share proxy;
5. the perceptual-access exception is represented;
6. a generic secondary-goal guess receives no credit;
7. the optional binary product layer is downstream and separately evaluated;
8. the curator signs off on examples rather than on an abstract binary rule.

## 7.7 Current-state and workflow documents outside `docs/design/`

### A. `docs/STATE.md`

Fold the current Phase 2.0 paragraph into a dated end-state and add a Phase 2.3 current-state block
above it. The new block should state:

- Phase 2.3 is the operative adaptive process-inversion program;
- Phase 2.2 theory errata applies before this delta;
- the binary G152 contract is not freezeable in its current form;
- G129's bounded choice-recovery positive survives;
- G131 and G153 process records are reusable under their documented provenance limitations;
- G149's constructed-world positive and text-port null both survive;
- detector fusion and value/alignment work remain gated;
- the next deliverable is the cheap root map, not a single adjudication verdict.

Do not erase the Phase 2.0 record or retroactively describe its original mission as process-first.

### B. `TODO.md`

Add a compact **Phase 2.3** table above the current Phase 2.0 section. It should contain the shared
spine and Wings A–G by alias, dependency, root result, and opened branch. Reuse existing G-numbers
where a wing consumes an existing study; do not renumber historical identifiers merely to create a
tidy phase sequence.

Change the G152 row to **DRAFT — DO NOT FREEZE; reconstruction reconciliation required**. Keep its
binary policy as an optional downstream deliverable. Mark G153's 240-artifact pilot as reusable
process-record substrate and explicitly not a valid provenance benchmark because matching failed.

Do not paste the full Phase 2.3 context into `TODO.md`. The table is a live pointer and branch
registry, not a second work package.

### C. Root `README.md`

Replace the current-phase pointer to `PHASE_2_0_CONTEXT.md` with the Phase 2.3 context. Add one
sentence that Phase 2.0 remains the historical vertical-slice brief and the design index maps all
phase documents.

Do not rewrite the theory map or recreation history during this pass.

### D. `CLAUDE.md`

Preserve the existing result write-through discipline, then add a current curator-synthesis rule:

> For a theoretical check-in, begin with the world-model change and two to five open questions the
> result raises. Do not walk study by study unless a study changes theory. Give the curator space
> for a verbal theory pass before prescribing the next branch. Mechanics, metrics, and queue detail
> follow in an appendix. The purpose is to prevent cognitive preemption, not to withhold evidence.

Phase 2.0's `Strengthens | Narrows | Kills | Infrastructure` tag can remain in each result receipt.
It is not sufficient as the whole theoretical-analyst report under Phase 2.3.

### E. Link repair

Fix at least this known stale path:

- `results/gate3/VERDICT.md` refers to `docs/SUCCESSOR.md`; from that file the current target is
  `../../docs/design/SUCCESSOR.md`.

Then search all Markdown for phase and design references. Preserve references that are deliberately
historical. Repair references that call an old file live, governing, current, or the next gate.

Recommended audit:

```bash
rg -n 'PHASE_2_0_CONTEXT|EVAL_CONTRACT_2_0|SUCCESSOR\.md|DWELL_CORPUS|QUEUE\.md|governing|current phase|highest-value' --glob '*.md'
```

The goal is not to replace every old phase number. It is to eliminate false present-tense authority.

---

## 8. Application order

Apply this as a sequence that keeps conceptual and editorial changes reviewable:

1. Confirm repository head and produce a short reconciliation receipt if it advanced.
2. Copy the Phase 2.2 and Phase 2.3 packages into `docs/design/` without changing their text.
3. Rewrite `docs/design/README.md` and add status banners. This establishes authority before content
   moves.
4. Apply `PHASE_2_2_THEORY_ERRATA.md` in its stated file order.
5. Run theory lint and review the diff for old-quote changes.
6. Apply this package's theory delta in the order:
   `THE_TRIPLE_INFERENCE.md` → `THREE_COGNITIVE_LAYERS.md` → `DECISION_TRACES.md` →
   `READER_HEURISTICS.md` → review-only `ALIGNMENT.md`.
7. Update the conclusion paragraph under every hypothesis table whose interpretation changed. Do
   not alter a status without a result.
8. Reconcile `EVAL_CONTRACT_2_0.md` in place and update `BENCHMARK_2_0.md`'s schema language.
9. Update `docs/STATE.md`, `TODO.md`, root `README.md`, and `CLAUDE.md`.
10. Repair stale links and present-tense authority claims.
11. Run the validation suite in §9.
12. Produce one curator-facing summary organized as **strengthened, differentiated, unresolved,
    deferred**, with implementation detail in an appendix.

Do not mix quote reconstruction and unrelated code work in the same commit.

---

## 9. Validation and anti-sanding checks

### 9.1 Quote integrity

Before applying theory changes, capture the existing blockquotes or the theory files' hashes. After
the edit:

- every old curator blockquote must be byte-identical unless the curator separately approved a
  specific replacement;
- every new class A quote must match §2 of this package exactly;
- no class B or class C language may appear inside a curator blockquote;
- no old quote may acquire a **Superseded** marker from this package;
- canonical quotes must appear in one owner only.

A small purpose-built comparison script is preferable. At minimum, inspect the staged diff with
whitespace changes visible.

### 9.2 Theory consistency

Confirm all of the following:

- viewer-coherent reconstruction, reenactment route, and historical process are distinct;
- none is described as a fourth inference;
- context reweights hypotheses rather than proving biographies;
- process equivalence classes and abstention are available;
- perceptual failure is not coded as failure to notice;
- divided attention, exhaustion, and absent expertise are context fields, not extra events;
- origin, recognition, response, recurrence, and integration can coexist;
- ordered accident is derived from a sequence, not made an exclusive origin class;
- a generic secondary-goal explanation gets no evaluation credit;
- mixed contribution is an event graph, not token share or equal-weight count;
- expertise remains a trajectory constraint even when its formation is described as compiled
  decision structure;
- the drive/expertise issue is explicitly unresolved;
- the LLM generative-prior claim is functional and held-out, not an internal-mechanism conclusion;
- `ALIGNMENT.md` remains dormant.

### 9.3 Documentation consistency

Confirm:

- exactly one phase package is labeled **OPERATIVE**;
- exactly one evaluation contract is on the path to freeze;
- the current phase, live queue, empirical state, and methods each have one clear owner;
- historical design documents retain their dated reasoning and quotes;
- no historical file still calls itself the current highest priority or current governing phase
  without a status banner explaining its scope;
- `TODO.md` and `docs/STATE.md` agree on the next root work;
- the root README points to Phase 2.3;
- `results/gate3/VERDICT.md` no longer points to the nonexistent `docs/SUCCESSOR.md`.

### 9.4 Repository checks

Run, adapting only if the repository documents a newer canonical command:

```bash
python tools/theory_lint.py
git diff --check
python -m pytest -q
```

Then run the reference audit from §7.7E and manually inspect every remaining present-tense hit.
Documentation-only changes must not mutate result files, frozen manifests, or preregistration
hashes.

---

## 10. Required curator-facing diff summary

The coding agent's completion report should not begin with filenames. It should say:

### Strengthened

- human inversion begins from a self-model and adjusts under context;
- anomalies become more informative through recognition and handling;
- expertise pre-solves trajectories and changes what attention can control;
- mixed creation is recoverable through interaction roles and dependencies.

### Differentiated

- viewer-coherent account versus reader-enactable route versus historical process;
- perceptual failure versus failure to notice;
- accidental origin versus deliberate later integration;
- secondary-goal existence versus recoverability of the particular goal;
- proposal volume versus ratification, integration, and downstream control;
- human-shaped generative prior versus human causal mechanism.

### Unresolved

- whether Pankseppian channels are motivational pressures, inherited transition strategies, or a
  construct that bundles both;
- when a productive reenactment corresponds to the maker's actual route;
- how much anomaly density should trigger a global maker-model revision;
- which secondary goals can be distinguished from artifact-only evidence.

### Deferred

- value extraction and trust gating;
- alignment experiments;
- a scalar human/AI contribution ontology;
- provenance fusion until the process outputs validate independently.

Only after that summary should the report list files, tests, lint output, and commit hashes.

---

## 11. Completion criteria

This package is correctly applied when:

- the Phase 2.2 errata and this delta have both been reconciled into the five existing theory files;
- existing curator quotations are untouched and zero are removed on the authority of this pass;
- only class A reconstructions have become new curator blockquotes;
- the process leg explicitly reports viewer coherence, reenactment, and historical correspondence
  separately;
- the anomaly representation is multilabel and sequential;
- failure to notice follows the perceptual-access ruling without pretending it is directly
  observable;
- secondary-goal attribution has a discriminating or predictive gate;
- mixed control is stored as an interaction trajectory and contribution network;
- expertise is not reduced to a stored decision list, high-level layer, or equal-weight count;
- the drive/expertise ambiguity remains visible and dormant rather than rhetorically solved;
- the single evaluation contract cannot be frozen in the old binary form;
- the design index names one current owner for phase, work queue, empirical state, method, and
  evaluation;
- historical design documents are preserved with clear status rather than rewritten to mimic the
  present;
- the curator-facing workflow creates theory-level thought space before study mechanics;
- theory lint, repository tests, diff checks, and link audits pass.

The aim is not to make the documentation smoother. It is to make its disagreements and uncertainty
legible without letting the analyst's prose replace the curator's model.
