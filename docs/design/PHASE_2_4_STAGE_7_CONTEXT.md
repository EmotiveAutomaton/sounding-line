# Sounding Line Phase 2.4 Stage 7: Clean-room capability bridge

**Status:** OPERATIVE RESEARCH HANDOFF. Build and validate the complete instrument before scientific execution.

**Prepared:** 2026-09-02, after the Stage 6 implementation audit and the curator's two walkthroughs.

**Reviewed repository state:** Sounding Line `5936b0b`; Ghost Scale Sim `ce4c06b`, with V15 launched but incomplete.

**Intended repository path:** `docs/design/PHASE_2_4_STAGE_7_CONTEXT.md`.

**Scope:** local model readers, known-answer process worlds, already acquired process records, and controlled mixed human/model histories. No human recruitment, paid API, alignment implementation, universal value inference, or product deployment.

**Workload:** 100 mandatory questions plus 24 required attacks.

**Runtime:** one execution window with a 72-hour ceiling and a locked target of 54–66 hours of useful end-to-end work. No sleep padding, duplicate rollouts, arbitrary seeds, excess prose, or early/partial curator packet.
**Claim class:** instrument repair, bounded model-reader capability, prospective process inference, and process-discontinuity localization.

---

## 0. Executive command

Stage 7 repairs the question Stage 6 intended to ask before attempting to answer it at greater
scale. Build a physically separated reader interface in which a non-oracle system can receive only
a frozen visible-evidence object. Prove by mutation and access tests that it cannot read the world
generator, planned action inventory, hidden events, future length, stopping variables, target labels,
or changed-context truth. Manually trace one keystone world from construction through scoring before
opening the scientific lineage.

Then separate five capabilities that Stage 6 conflated:

1. prediction from common domain structure;
2. selection among supplied maker laws;
3. learning a maker law from demonstrations or prior artifacts;
4. reconstruction of the maker's perceived action space and current state;
5. prospective prediction from the reconstructed model.

The capability ladder begins by supplying a complete, executable maker model and asking whether the
reader can use it. Only after that rung works may the stage withhold the proximal goal, belief state,
subjective action space, expertise, or maker-interpreted context. Compare structured computation,
inference-time model computation, and model size only after the relevant lower rung is valid.

The first ecological flight target is not unrestricted prediction of a person. It is localization of
a known process discontinuity in a held-out mixed human/model revision history, beyond strong
stylometric and sequential baselines. Next-action and stopping predictions remain falsification and
calibration rulers for a bounded reconstruction. They are not the permanent product definition and
do not prove historical correspondence.

Implement all 100 questions and 24 attacks before the scientific lock. A question is not implemented
merely because an identifier exists: it must have a distinct construction, target, estimand, null,
failure consequence, output, and expected cell set. The manifest must reject two nominal questions
that reduce to the same data mapping and statistic.

Ghost V15 remains read-only and incomplete. Stage 7 may record its commit and completion status. It
may not import partial V15 outcomes, alter its runner, consume its working files, or start V16.

## 1. Mission and theory boundary

The working definition ratified in the walkthrough is:

> **Sounding Line is an artifact-grounded inverse-generative system that reconstructs a revisable
> model of how a maker transformed their perceived possibilities into an artifact, then tests that
> reconstruction through hidden future and counterfactual behavior.**

The paragraph around that definition operates at several timescales:

- **proximal control:** what is being attempted now;
- **process and expertise:** how this maker can and tends to transform perceived states;
- **persistent tendencies:** what recurs strongly enough across contexts to inform later character,
  trust, and selective uptake.

These quantities can constrain one another inside one maker model, but success on one does not
establish the others. Stage 7 is principally about the first two. It carries a small attention/history
stress track only to keep the current theory internally coherent; it cannot promote value or alignment
work.

## 2. Stage 6 is an execution record, not an accepted interpretation

The committed Stage 6 packet is preserved as an honest execution record. Its central interpretation
is suspended because the implementation did not enforce the evidence boundary named by the design.
Stage 7 begins by writing this correction through the repository before it runs.

### 2.1 Findings that control Stage 7

1. `predictive_at_cut()` accessed the complete `target_actions` inventory, future `events`, hidden
   trajectory length, `stop_shift`, and hand-coded transition/utility functions while the report said
   the tail, stopping, and changed context were withheld.
2. The large reported gain mostly came from supplying the correct simulator family and comparing it
   with a weak direct-prompt arm. In the post-hoc decomposition, equal mixing over privileged exact
   simulators already explained about `+0.230` nats; model-derived label weights added about `+0.002`;
   exact-likelihood adaptation added about `+0.055`; free-language contextual weighting subtracted
   about `−0.017`. These are descriptive audit numbers, not new confirmatory results.
3. On 256 discovery cases, the label reader assigned mean posterior mass `0.257` to the true
   controller and reached `0.289` MAP accuracy, near the `0.25` marginal. Exact likelihood selection
   among the planted simulator family reached `0.699` MAP accuracy. This is legitimate known-model
   identification, not open-ended maker reconstruction.
4. The Stage 6 supplied-state gate supplied a prose goal, controller description, and remaining-item
   count. It did not supply the operative subjective action space, belief state, expertise/transition
   law, costs, or future cue logic. Its failure did not establish a general reader-capacity boundary.
5. The stopping law was effectively independent of the hypothesized maker state. No reader could
   earn a maker-state stopping gain from that construction.
6. M14 gave fresh realization the new world's constructor variables. Its contextual gain was close
   to tautological. M15 preserved predictions through a hypothesis tag while ignoring the paraphrase
   semantics. Neither licenses a realization conclusion.
7. Several value and foraging cards were different names for the same world mapping or statistic.
   Card count exceeded independent scientific content.
8. The CoAuthor loader consumed `suggestion-select` as a document delta before the acceptance branch
   could record it. All 686 scored decisions were therefore dismissals. That result is invalid.
9. ScholaWrite readers lost to a strong previous-label baseline, and the drawing readers lost to the
   drawing's own start-quadrant distribution. These remain narrow negative results unless their
   dependency audit finds another contamination.
10. Stage 6 completed 160 locked cells in `47.07` hours, with `42.15` GPU-lock hours. The prior
    168-hour forecast was wrong because the workload multiplier overstated cost and capability-gated
    branches closed. Stage 7 uses this measured result, not the old forecast.

### 2.2 Mandatory repository correction before the Stage 7 scientific lock

- Do not edit or delete the Stage 6 raw outputs or final packet.
- Add a dependency audit beside the Stage 6 results. Classify every card and attack as
  `CLEAN`, `DEPENDENCY_TAINTED`, `CONSTRUCTION_INVALID`, `DUPLICATE_ESTIMAND`, or `UNRESOLVED`.
- Fold one new correction entry into `FINDINGS.md`, update the affected existing entries in place,
  and revise the afterwords under every affected theory table. Preserve the five-file theory
  architecture and curator quotations.
- Explicitly suspend the Stage 6 architecture ranking, reader-boundary conclusion, M14 realization
  conclusion, M15 semantic-invariance conclusion, and CoAuthor result.
- Retain exact supplied-family likelihood selection only as known-model system identification.
- Retain no Stage 6 value, attention-history, stopping, or foraging interpretation until its exact
  dependency chain is classified.
- Run the multiplicity and theory-format checks after the correction. The Stage 7 scientific lock
  cannot open while the repository still presents the suspended interpretation as current.

## 3. Canonical Stage 7 maker model

Stage 7 uses the following objects. The notation prevents the repair from quietly creating new
synonyms for old quantities.

| Symbol | Object | Meaning |
|---|---|---|
| `O_≤t` | visible evidence | artifact or process evidence genuinely available through time `t` |
| `C_ext,t` | external context | task, brief, audience, tools, constraints, and objective opportunities |
| `B_t` | belief/information state | what the maker knew, believed, perceived, or failed to perceive |
| `K` | expertise | the maker's learned transition/action structure: perceived feasible moves, expected consequences, costs, fluency, and reliability |
| `C_m,t` | maker-interpreted context | external context as transformed through belief and expertise |
| `Ã_t` | subjective action space | actions the maker believed were available and executable at `t` |
| `G_t` | proximal goal | the locally governing target at `t`; normally the easiest on-the-spot latent |
| `H_t` | control/history residue | maintained intentions, habits, and prior-selection effects that can deform action without being the focal goal |
| `V` | persistent tendency candidate | cross-context tradeoff structure; carried only as a bounded rival, never presumed recovered |
| `τ` | realized process | the actual sequence of decisions and actions; not identical to expertise |

The key identities and non-identities are:

\[
C_{m,t}=\phi(C_{ext,t},B_t,K),
\qquad
\widetilde{\mathcal A}_t=\mathcal A(C_{m,t},B_t,K),
\]

\[
a_t\sim\pi_K(a\mid O_{\leq t},\widetilde{\mathcal A}_t,G_t,H_t,V),
\]

\[
\tau=(a_1,\ldots,a_T),
\qquad
K\neq\tau,
\qquad
K=\text{the learned transition/action model, not an extra variable beside it}.
\]

An external transition model must therefore not be added as a sixth psychological latent. A domain
may have objective dynamics, but the maker-specific transition law the reader needs is part of
expertise. Process is the path taken through that learned structure.

The capability ladder is an evidence-ablation ladder, not a claim about what every reader begins
without. A domain expert can arrive with useful `K`; a close reader can arrive with a strong maker
prior; a reader may know the maker's usual wants. Stage 7 must cross **cold**, **domain-expert**, and
**maker-familiar** evidence regimes rather than defining understanding as cold inference from one
artifact.

## 4. What the stage must distinguish

### 4.1 Prediction from common structure

A writing process has grammar, local persistence, positional regularities, genre expectations, and
base rates that predict later edits without identifying a maker. This is useful prediction but not
maker reconstruction. The strongest frozen common-process model is a baseline in every rung.

### 4.2 Selecting a supplied law

The system is given a bounded set of executable maker laws and chooses which best explains the
visible prefix. Exact likelihood selection is valid system identification. Report it under that
name. It does not show that the system learned the laws or reconstructed the action space.

### 4.3 Learning a law

The system receives demonstrations, earlier dated artifacts, or process traces and must infer a
maker-specific `K` that was not present in the candidate set. Success requires prediction on an
untouched episode. Restating a label or selecting a planted simulator does not pass.

### 4.4 Reconstructing perceived possibilities

The objective option set and the maker's option set can differ. The target is `Ã_t`: what this maker
believed they could do, after objective context was filtered through beliefs and expertise. The
reader may receive objective context without receiving this subjective set.

### 4.5 Identifying a maker state

The stage separately scores `G_t`, `B_t`, `K`, `C_m,t`, `Ã_t`, and any equivalence class. A good
future prediction cannot be back-translated into credit for every latent. Conversely, accurate
latent classification without prospective gain is not understanding.

### 4.6 Prospective use

The maker model must improve a hidden feasible choice, stopping opportunity, counterfactual, or
process-discontinuity prediction beyond common-process and same-evidence rivals. Prediction is an
evaluation criterion, not proof that the reconstructed history is unique.

## 5. Research imports and architecture naming

Stage 6 named contemporary programs but implemented small local mechanisms that omitted their
defining operations. Stage 7 may borrow modules; it may not borrow prestige.

| Program | Defining operation that a conformance fixture must reproduce | Stage 7 boundary |
|---|---|---|
| [LLM-Augmented Inverse Planning](https://arxiv.org/abs/2507.03682) | the language model proposes hypotheses **and likelihood functions**, while an external Bayesian component computes posterior probabilities | a fixed label list with reader weights is not LAIP |
| [ThoughtTracing](https://arxiv.org/html/2502.11881v2) and its [official repository](https://github.com/skywalker023/thought-tracing) | preprocess into state/action/perception steps; initialize, propagate, weight, ESS-resample, diversity-check, and rejuvenate natural-language hypotheses | three repeated label judgments are not ThoughtTracing |
| [AutoToM](https://arxiv.org/html/2502.15676v3) and its [official repository](https://github.com/SCAI-JHU/AutoToM) | propose an initial causal agent model; conduct explicit Bayesian inference; use model utility to add latent variables and extend the time window | adding one preselected controller tag is not AutoToM |
| [LIRAS](https://aclanthology.org/2025.findings-emnlp.654/) | synthesize and validate a situation-specific environment model, rational agent model, parsed state/action sequence, and SIAM-style inverse-planning computation | no clearly official public implementation was located; any reconstruction is `LIRAS-style paper reproduction`, not LIRAS |
| [InversePlanning.jl](https://github.com/cosilab/InversePlanning.jl) | probabilistic inverse planning over explicit plans/actions with a known PDDL/Gen model | use as a known-law reference, not evidence that the action space was inferred |
| [LaBToM.jl](https://github.com/cosilab/LaBToM.jl) | translate epistemic language into a compositional epistemic representation evaluated against Bayesian mental-state inference | tests belief-language grounding only, not the whole maker model |
| [CLIPS.jl](https://github.com/cosilab/CLIPS.jl) | jointly use instructions and actions for cooperative goal inference and assistance | cooperative instructions are stronger evidence than many artifacts provide |
| [Acting as Inverse Inverse Planning](https://github.com/kach/acting-as-inverse-inverse-planning) | model a maker choosing actions partly to shape an observer's inference | use for audience-shaping and concealment worlds; do not assume ordinary making is pedagogical |

Clone official repositories only into a read-only sibling reference workspace. Pin commit, license,
paper version, setup result, and the exact borrowed function in
`results/phase_2_4_stage_7/SOURCE_MANIFEST.json`. Do not vendor them into Sounding Line, allow them to
read Stage 7 hidden or confirmation data, or make them runtime dependencies before conformance.

> **Curator's ruling, 2026-09-02 (applied to this and every later stage).** The standing local-only
> rule, under which nothing was downloaded, is retired: cloning and downloading reference code or
> checkpoints is permitted upon request, or on the agent's recommendation with the curator's
> confirmation. "We do not need the hard stop anymore. We have enough of a program identity." The
> clones live at `E:/EmotiveAutomaton/Projects/SoundingLine/reference/` (outside the repository),
> pinned in the source manifest; the two Python programs named above were cloned under this ruling
> (ThoughtTracing at `966eb27`, AutoToM at `3f569b7`; the Julia programs need a runtime this machine
> lacks and stay uncloned, their operations reproduced locally as §10 A12 admits). Isolation
> mechanism, ruled the same day: the interpreter capsule (§6.2), honestly labeled interpreter-level.

An imported name is admitted only if its tiny official-style fixture passes. Otherwise the arm gets
a descriptive local name such as `weighted_language_hypotheses` or `adaptive_factor_expansion`.
Failure to reproduce an external program is an implementation result, not evidence against that
program.

## 6. Physical information separation

### 6.1 Three artifacts, three authorities

1. **`VisibleEvidenceV1`** is the only input available to non-oracle readers.
2. **`OracleBundleV1`** contains generator state, hidden future, targets, objective and subjective
   action spaces, true factors, and counterfactual outcomes. It is available only to constructors
   and scorers.
3. **`PredictionV1`** is emitted by readers without a world object and scored only after the reader
   process exits.

`VisibleEvidenceV1` uses an allowlist, not a denylist. Depending on the experimental condition, it
may contain:

- the artifact or process prefix;
- the current artifact state;
- context statements genuinely supplied to the reader;
- observed actions through the cut;
- prior demonstrations or dated works assigned to that evidence condition;
- an explicitly supplied action set or maker factor when the rung requires it;
- opaque lineage and condition identifiers generated independently of hidden truth.

It never contains or derives from:

- future actions, hidden target actions, or the final trajectory length;
- future interruptions, cues, contradictions, or changed-context state;
- stopping shifts, generator utilities, truth tags, hypothesis tags, or target-correlated seeds;
- unobserved alternatives in a reconstruction condition;
- source paths, filenames, ordering, schema keys, or lengths that encode the answer;
- an import handle, callback, object reference, closure, or method that can reach constructor state.

### 6.2 Execution boundary

Run each non-oracle reader in a fresh process whose working capsule contains only:

- the frozen reader package and contracts;
- one visible-evidence file or standard-input stream;
- the permitted local model endpoint;
- a write-only prediction/output location.

The constructor and oracle packages must not be on its import path or readable filesystem view.
Network access is closed except for the explicitly required loopback model endpoint. Record an
access receipt. Test that attempted import or open of a constructor/oracle path fails. If the local
platform cannot enforce this boundary, the scientific lock remains closed; logging an illicit read
is not equivalent to preventing it.

### 6.3 Required metamorphic boundary tests

- **Hidden-tail mutation:** hold `VisibleEvidenceV1` byte-identical while replacing future actions.
  Every non-oracle prediction must be byte-identical after canonical serialization.
- **Hidden-stop mutation:** hold visible evidence fixed while replacing future length, stopping
  parameters, and stop outcome. Non-oracle output must remain identical.
- **Hidden-event mutation:** replace future cue, interruption, source invalidation, and
  changed-context truth while preserving the prefix. Output must remain identical.
- **Visible-evidence sensitivity:** change one genuinely diagnostic visible observation while
  holding hidden truth fixed. The relevant reader distribution must move in the predeclared
  direction or the reader cannot claim to use that channel.

The first three tests establish non-access. The fourth prevents a reader that ignores all input from
passing invariance.

## 7. Worlds, records, and partitions

### 7.1 Known-answer factor worlds

Build small process worlds in which the objective context, maker-interpreted context, beliefs,
expertise/action law, subjective action set, proximal goal, history residue, and stopping law can be
varied separately. Every substantive contrast needs:

- a true oracle with nontrivial prospective advantage over the common-process baseline;
- a visible-prefix collision: at least two hidden maker models generate the same evidence through
  the cut;
- a later discriminating event or intervention;
- an equivalence case that remains unresolved and should produce class uncertainty;
- matched surface renderers and opaque identifiers;
- a stop opportunity whose probability actually depends on a manipulated maker factor;
- a counterfactual whose outcome is computed from the same declared maker law, not inserted as a
  target-only annotation.

No constructor variable may be read directly by a non-oracle adapter. A world is invalid if the
scorer cannot show that the exact supplied maker model improves the target over the strongest
common-process baseline.

### 7.2 Expertise and subjective opportunity

`K` must be represented as an operative law, not a biographical adjective. It maps perceived states
and subjective opportunities to expected outcomes, costs, and action likelihoods. A reader can be
given:

- the full executable law;
- a natural-language description of the same law;
- demonstrations generated by the law;
- prior dated artifacts produced under related contexts;
- only a domain-generic law.

These evidence conditions answer different questions and must never share a label such as “expert.”

### 7.3 Controlled mixed human/model histories

Construct held-out revision histories with independently logged actors and event roles. Include at
least:

- human draft followed by model proposal and human accept/edit/reject;
- model draft followed by human thesis selection or structural rewrite;
- alternating local edits whose surface register is normalized;
- a no-discontinuity human-only and model-only control;
- a style-matched discontinuity and a style-shifted no-discontinuity adversary.

The target is the location and type of a process/control discontinuity, not a token percentage or a
moral authorship label. Preserve proposal, selection, ratification, veto, integration, repair,
acceptance, and execution as distinct event roles.

### 7.4 Existing records

- **CoAuthor:** repair the loader before use. A `suggestion-select` event must both record acceptance
  and apply its document delta where present; those operations cannot occupy mutually exclusive
  branches. Validate with known mini-logs containing accepts, dismissals, reopenings, edits, and
  malformed deltas. Do not claim final-document equality if the source does not provide an
  independent final reference.
- **ScholaWrite:** retain leave-project-out and leave-author-out grouping and the strong previous-
  label baseline. The useful target is a switch or direction that persistence cannot win by default.
- **Drawing records:** optional expansion only after the writing capability ladder is live. If used,
  preserve category and start-position priors and the access-level distinction.
- **OpenReview:** remains resource-blocked unless a licensed, lineage-resolvable corpus is actually
  present. Do not spend this short stage reacquiring it.

### 7.5 Frozen partitions

Before model calls, freeze discovery, transfer, confirmation, conformance, and attack lineages. Keep
every descendant of one maker, author, session, prompt, proposal, model completion, artifact,
paraphrase, transformation, and mixed-control history on one side of every split. Candidate-generation
examples stay away from candidate-evaluation and confirmation cases. The independent unit is the
maker/session/history/world, not an edit row, token, proposal, particle, or rollout.

## 8. Shared estimators and baselines

Every live reader sees the same evidence hash and target vocabulary for a paired comparison. The
stage separates the following systems:

| Code | System | What it is allowed to establish |
|---|---|---|
| `U` | uniform or opportunity-marginal baseline | chance under the live option set |
| `PERS` | persistence/last-event/position baselines | sequential regularity without a maker model |
| `DOM` | frozen common-domain process model | grammar, genre, position, and generic action structure |
| `DIR` | direct model reader | inference-time model computation without an explicit factor graph |
| `KL` | known-law Bayesian selector | selection among supplied executable maker laws |
| `SL-J` | Sounding joint reader | proposes/revises `C_m`, `B`, `K`, `Ã`, and `G`, then predicts through an explicit external computation |
| `EXT-*` | conformance-passed external scaffold | only the defining operation its fixture verifies |
| `OR` | exact oracle | construction ceiling, never a competing reader |

The strongest cheap rival is the best frozen combination of `PERS` and `DOM`, selected only inside
discovery and then fixed. `DIR` alone is not an adequate comparator.

For each target with a nontrivial oracle gap, define:

\[
\Delta_{\mathrm{oracle}}=S_{OR}-S_{DOM},
\]

\[
U_{\mathrm{state}}=\frac{S_{\mathrm{true\ state}}-S_{DOM}}
{S_{OR}-S_{DOM}},
\qquad
R_j=\frac{S_j-S_{DOM}}
{S_{\mathrm{true\ state}}-S_{DOM}}.
\]

`S` is held-out proper log score at the independent-unit level. `U_state` measures whether the
reader can use a complete supplied maker model. `R_j` measures how much of that usable advantage an
inference condition recovers. Do not compute either ratio when its denominator is nonpositive or
too small; mark the instrument void.

Report Brier score, calibration slope/intercept, expected calibration error, risk-coverage, class
coverage for equivalence cases, exact candidate recall, model calls, input/output tokens, forward
passes, solver work, wall time, peak memory, and retries. Accuracy is secondary.

## 9. Shared question contract

Every mandatory question declares:

- plain-language question and theory purpose;
- construction and exact variables supplied versus inferred;
- `VisibleEvidenceV1` field allowlist;
- withheld prospective target;
- reader and baseline arms;
- estimand and smallest effect of interest fixed from the oracle gap;
- directional, interaction, or equivalence alternative;
- strongest cheap and theoretical rivals;
- independent unit, minimum effective sample, domains, and reader checkpoints;
- positive, negative, surface, oracle, calibration, abstention, and access gates;
- architecture-conformance dependency where relevant;
- one permitted repair and a closure rule;
- claim ceiling, expected cells, and unique output paths.

Every substantive question must answer something not answered by another question. Before the
structural lock, hash the tuple
`(data lineage, supplied fields, withheld target, estimator, comparison, statistic)`. Two cards with
the same tuple are duplicates and fail the manifest unless one is explicitly a replication on an
untouched lineage.

## 10. Mandatory question inventory: 100 questions

| Trunk | Count | Purpose |
|---|---:|---|
| I | 16 | physical isolation, integrity, and execution gates |
| D | 10 | Stage 6 dependency audit and data repair |
| K | 16 | supplied-state capability ladder |
| R | 16 | maker-factor reconstruction ladder |
| A | 16 | architecture conformance and compute decomposition |
| P | 14 | prospective and ecological bridge |
| V | 6 | bounded attention/history/preference stress tests |
| B | 6 | confirmation, closure, and reporting |
| **Total** | **100** | |

### I: Isolation, integrity, and execution gates (16)

| ID | Question | Required discriminator |
|---|---|---|
| I01 | Do the reviewed repository heads, Stage 6 runtime anchors, and raw hashes reproduce? | Exact commit, runtime, cell-count, and file-hash receipt; mismatch blocks inheritance. |
| I02 | Does the manifest recursively enumerate all 100 questions, 24 attacks, factor corners, lineages, outputs, and closures? | Removing any literal item or expected corner fails coverage. |
| I03 | Does `VisibleEvidenceV1` contain only allowlisted fields for each rung? | Schema rejection of every undeclared field and nested object. |
| I04 | Is the reader physically unable to import or read constructor and oracle state? | Forbidden import/open attempts fail inside the real reader process; access receipt is clean. |
| I05 | Does hidden-tail mutation leave every non-oracle prediction byte-identical? | Same visible-evidence hash, different future actions, exact canonical-output identity. |
| I06 | Do hidden trajectory length, stop parameters, and stop outcomes leave non-oracle output unchanged? | Exact invariance across stop-tail twins. |
| I07 | Do future cues, interruptions, source invalidations, and changed-context truth leave current output unchanged? | Exact invariance across hidden-event twins. |
| I08 | Does a diagnostic visible observation move the relevant prediction in the declared direction? | Sensitivity positive while I05–I07 remain invariant. |
| I09 | Are serialization, key order, whitespace, and opaque lineage relabeling irrelevant? | Canonical predictions stable; semantic evidence change still moves them. |
| I10 | Are targets absent from filenames, identifiers, ordering, lengths, seeds, schemas, prompts, caches, and logs? | Planted canaries are caught and clean nulls remain at floor. |
| I11 | Does every reader emit normalized `PredictionV1` objects with uncertainty, equivalence classes, and abstention? | Parser and probability identities pass on exact fixtures. |
| I12 | Do paired arms receive the same visible bytes and only their declared supplied factors? | Evidence-hash equality and field-difference receipt. |
| I13 | Are compute, model calls, solver work, context, retries, and cache reuse recorded and constrained? | Budget ledger reconciles to process receipts. |
| I14 | Are discovery, transfer, confirmation, conformance, and attack lineages descendant-clean? | Zero cross-split overlap under recursive lineage expansion. |
| I15 | Do checkpoint, kill/resume, atomic write, and produces guards prevent duplicate scientific units? | Forced interruption resumes once; row reordering and duplication do not move estimates. |
| I16 | Does one keystone world pass a manual constructor-to-score audit before scale? | Signed checklist traces inputs, process access, model calls, output, truth lookup, and score; any unexplained access blocks the scientific lock. |

### D: Stage 6 dependency audit and record repair (10)

| ID | Question | Required discriminator |
|---|---|---|
| D01 | Which Stage 6 predictions depended on hidden constructor fields? | Static and dynamic access graph from every scored output to source fields. |
| D02 | How much of the reported tournament gain is reproduced by equal mixing over privileged simulators, label weighting, and exact adaptation? | Recompute the audit decomposition from committed rows; no confirmatory language. |
| D03 | Which Stage 6 cards remain clean after transitive dependency tracing? | One disposition for every card and attack under the five audit classes. |
| D04 | Do the architecture ranking, reader-boundary claim, M14, M15, and CoAuthor conclusion survive their dependency audit? | Expected starting disposition is suspension; restoration requires a clean independent path. |
| D05 | Can Stage 6's exact arm be renamed and isolated as supplied-law selection? | Reproduce exact likelihood identification without calling it law learning or reconstruction. |
| D06 | Which value and foraging questions shared identical worlds or statistics? | Implementation-identity matrix; duplicate estimands collapse to one evidential unit. |
| D07 | Does the repaired CoAuthor loader record acceptance before/alongside applying `suggestion-select` deltas? | Known mini-logs recover accept, dismiss, reopen, edit, and ignore exactly. |
| D08 | What CoAuthor reconstruction claim is licensed by the source fields? | Validate only against independent fields actually present; reject invented final-text ground truth. |
| D09 | Do the ScholaWrite and drawing negative results reproduce through reader-free, lineage-clean baselines? | Same narrow endpoints and strong sequential/spatial baselines; no contaminated realization path. |
| D10 | Is the Stage 6 correction written through findings, theory afterwords, state, and the dependency-audit artifact before Stage 7 begins? | Cross-file consistency, theory lint, multiplicity audit, and no surviving unqualified suspended claim. |

### K: Supplied-state capability ladder (16)

| ID | Question | Required discriminator |
|---|---|---|
| K01 | Can the exact oracle predict every hidden target in each known-answer world? | Nontrivial oracle gap on next action, stopping, and the declared counterfactual. |
| K02 | How well do uniform, marginal, persistence, position, and opportunity-only baselines predict? | Frozen table at the independent-unit level. |
| K03 | How well does the strongest common-domain process model predict without maker-specific state? | Held-out score and calibration; this is the primary cheap rival. |
| K04 | Can a reader use the complete executable `C_m+B+K+Ã+G+H` state to improve next action over `DOM`? | Positive `U_state` on untouched units with no generator access. |
| K05 | Can the same reader use a complete natural-language rendering of that state? | Executable-versus-language interaction isolates interface loss. |
| K06 | What does supplied external and maker-interpreted context add by itself? | Context-only gain without hidden action law or goal. |
| K07 | What does the true subjective action space add by itself? | Opportunity-conditioned gain; unavailable actions receive zero mass. |
| K08 | What does the true expertise/transition law add by itself? | Law-conditioned gain beyond `DOM`, without a truth tag. |
| K09 | What does the true belief/information state add by itself? | Belief-swap worlds with identical objective state and action law. |
| K10 | What does the true proximal goal add by itself? | Goal-swap worlds with matched prefix and surface. |
| K11 | With `C_m+B+K+Ã+H` supplied, can the reader infer only `G` and preserve prospective gain? | Goal posterior plus hidden-action score; classification alone cannot pass. |
| K12 | With `C_m+K+Ã+G+H` supplied, can it infer only `B`? | False-belief collision resolved by later action. |
| K13 | With `C_ext+B+K+G+H` supplied, can it reconstruct `Ã`? | Objective-versus-subjective option mismatch and correct refusal of unavailable choices. |
| K14 | With `C_m+B+Ã+G+H` supplied plus demonstrations, can it infer the missing expertise law? | Held-out action under a new state; selecting a listed law is scored separately. |
| K15 | Can the complete state improve continuation/stopping when the stop law genuinely depends on maker state? | Proper hazard gain over matched progress/length/deadline baselines. |
| K16 | Conditional on K04, how do structured computation, inference-time compute, and model size affect state use? | Factorial interaction, not three incomparable runs; if K04 fails, this diagnoses rather than rescues it. |

### R: Maker-factor reconstruction ladder (16)

| ID | Question | Required discriminator |
|---|---|---|
| R01 | Does candidate generation include the true/equivalent proximal goal before selection? | Goal-set recall and redundancy, separated from posterior ranking. |
| R02 | Does it include the true/equivalent belief state? | Belief-set recall on false-belief and missing-information fixtures. |
| R03 | Does it include a behaviorally equivalent expertise law not named in the prompt? | Law-set recall under executable equivalence tests. |
| R04 | Does it reconstruct the maker's subjective action space rather than repeat the objective list? | Precision/recall over `Ã`, with impossible and unnoticed actions crossed. |
| R05 | Does it reconstruct maker-interpreted context rather than copy external context? | Correct differences caused by belief and expertise. |
| R06 | With all other factors supplied, does inferred `G` recover the K11 prospective advantage? | `R_G` against supplied-goal ceiling. |
| R07 | With all other factors supplied, does inferred `B` recover the K12 advantage? | `R_B` on hidden future and counterfactual. |
| R08 | With all other factors supplied, does inferred `Ã` recover the K13 advantage? | `R_Ã` and zero mass on subjectively unavailable actions. |
| R09 | Can `K` be learned from demonstrations or earlier artifacts and transfer to an untouched episode? | New-state prediction; no supplied candidate law. |
| R10 | Can `C_m` be inferred from artifact/source evidence and improve a later choice? | Context reconstruction beyond topic/style and copied biography. |
| R11 | Can `G` and `B` be inferred jointly without collapsing one into the other? | Crossed goal/belief worlds and both component posteriors. |
| R12 | Can `K` and `Ã` be inferred jointly without treating objective opportunity as competence? | Expertise/action-space swaps with identical observed prefix. |
| R13 | Can the full factor set be inferred jointly from visible evidence and improve prediction over `DOM` and `DIR`? | All-factor posterior plus prospective score; no credit borrowed from oracle fields. |
| R14 | Does maker familiarity help where cold reading fails, independently of domain expertise? | Cold × domain-expert × maker-familiar crossing on the same targets. |
| R15 | Does domain expertise help reconstruct feasible processes without falsely increasing maker certainty? | Better action-law prediction with calibrated maker-factor uncertainty. |
| R16 | Does the reader preserve observationally equivalent maker models and choose a useful next discriminator? | Equivalence-class coverage, abstention, and expected information per cost. |

### A: Architecture conformance and compute decomposition (16)

| ID | Question | Required discriminator |
|---|---|---|
| A01 | Are every external source, paper version, repository commit, license, and borrowed component pinned before use? | Complete source and assumption manifest; no floating branch at scientific time. |
| A02 | Can external reference code run only in its sealed conformance workspace without access to Stage 7 science or confirmation data? | Read-only clone, network/data boundary, and access receipt. |
| A03 | Does the LAIP-style arm generate hypotheses and likelihood functions, then compute the Bayesian posterior externally? | Tiny paper-style fixture; a fixed label-weighting shortcut fails conformance. |
| A04 | Does ThoughtTracing preprocessing recover state, action, and perception steps on an official-style example? | Step sequence matches the fixture before hypothesis inference. |
| A05 | Does the ThoughtTracing arm initialize, propagate, weight, ESS-resample, and diversity-rejuvenate hypotheses? | Each defining operation fires on a designed fixture and leaves a receipt. |
| A06 | Does the ThoughtTracing posterior recover after contradiction without fabricated full importance weights? | Sequential posterior, ESS, diversity, and recovery trace. |
| A07 | Does AutoToM propose an initial agent-model structure and explicit local conditionals? | Causal variables and factorization reproduce an official-style fixture. |
| A08 | Does AutoToM-style utility add a genuinely missing latent and reject false expansion in a complete world? | Missing-variable gain × complete-world cost interaction. |
| A09 | Does AutoToM extend the time window only when the current window remains insufficient? | Earlier-evidence fixture and no gratuitous extension control. |
| A10 | Does the LIRAS-style reproduction synthesize a valid situation-specific environment/action model? | Syntax and semantic execution checks; paper-reproduction label retained. |
| A11 | Does it synthesize the agent model, parse observations/actions, and run inverse inference over that model? | End-to-end official-style fixture; direct-answer ablation included. |
| A12 | Does InversePlanning.jl or an exact independently checked equivalent reproduce the known-law posterior? | Analytic tiny-world posterior and bounded-rational action likelihood. |
| A13 | Does LaBToM-style epistemic translation preserve belief content and change inference when that content changes? | Valid compositional representation plus belief-sensitive posterior. |
| A14 | Does the Sounding joint reader revise mutually constraining factor hypotheses rather than produce a longer rationale? | Executable factor graph, posterior updates, and predictions at each revision. |
| A15 | At matched evidence and measured compute, does structured computation beat direct inference-time computation? | Same base model and targets; calls, tokens, solver operations, and wall time reported. |
| A16 | Conditional on the supplied-state gate, does a larger local model improve factor use or only verbal proposal quality? | Qwen2.5 1.5B/3B and the available 9B local route where probability interfaces are comparable; family and interface caveats explicit. |

### P: Prospective and ecological bridge (14)

| ID | Question | Required discriminator |
|---|---|---|
| P01 | Can the reader predict the exact next feasible action? | Proper score against `DOM`, with the live option set enforced. |
| P02 | Can it predict next edit type? | Beat persistence and domain marginals on held-out worlds/sessions. |
| P03 | Can it predict location and scope of the next edit? | Hierarchical proper score against position and section priors. |
| P04 | Can it predict which available alternative the maker rejects? | Opportunity-conditioned choice score; unavailable options excluded. |
| P05 | Can it predict continuation versus stopping at a real decision boundary? | Discrete-time hazard score with censoring and matched progress/length. |
| P06 | Can it distinguish satisfaction, deadline, and fatigue boundaries or abstain when they are equivalent? | Boundary-type posterior and resumption counterfactual; no generic human claim. |
| P07 | Can it predict a later action after a context or opportunity change? | Changed-context proper score from the same maker law. |
| P08 | Can it predict response to a later-invalidated source without treating this as the product target? | Correction/retention/rewrite distribution; secondary consequence only. |
| P09 | Does the model improve the whole withheld tail rather than one queried event? | Sum of per-event proper scores plus localization audit. |
| P10 | Is uncertainty calibrated across evidence dose, contradiction, and exact equifinality? | Reliability, risk-coverage, and class coverage. |
| P11 | Can it localize a known human/model control change in a held-out revision history? | Change-point log score and boundary error against process records. |
| P12 | Does discontinuity localization survive surface normalization and defeat stylometry-only rivals? | Style-matched discontinuity and style-shifted no-discontinuity crossover. |
| P13 | After loader repair, can CoAuthor suggestion accept/edit/reject behavior be predicted beyond position and prior-decision baselines? | Session-held-out choice score; state reconstruction gate first. |
| P14 | In ScholaWrite, can the reader predict the moment and direction of a goal switch rather than win on label persistence? | Switch-conditioned score under leave-project-out and leave-author-out splits. |

### V: Bounded attention/history/preference stress tests (6)

| ID | Question | Required discriminator |
|---|---|---|
| V01 | Can trained automatic capture be separated from current costly redirection? | Same capture tendency, crossed redirection cost/choice; present choice and compiled residue scored separately. |
| V02 | After context and functional competence are matched, does current allocation/redirection predict the next local choice? | Prospective choice, not an unexplained residual relabeled “preference.” |
| V03 | Can lagging expertise oppose a current proximal goal without either being erased from the maker model? | Goal × expertise conflict and diagnostic future action. |
| V04 | Does one artifact support a dated present focus plus an uncertain historical mixture, rather than two clean time points? | Posterior age/mixture calibration on known histories; forced point dating is penalized. |
| V05 | Do multiple dated artifacts improve trajectory prediction over an aggregate expertise/style profile? | Held-out later episode; dated versus ordered-undated versus aggregate comparison. |
| V06 | Does any inferred trajectory predict a later costly choice beyond context, proximal goal, identity, topic, and expertise baselines? | Fresh-context proper score; no second-derivative or precision claim. |

### B: Confirmation, closure, and reporting (6)

| ID | Question | Required discriminator |
|---|---|---|
| B01 | Does the strongest supplied-state capability effect replicate on untouched worlds? | Frozen K-rung estimand, state rendering, reader, and strong baseline. |
| B02 | Does the strongest qualified reconstruction or architecture effect replicate on untouched lineages? | Conformance-passed arm, same evidence/compute, no endpoint substitution. |
| B03 | Does process-discontinuity localization replicate on untouched mixed-control histories? | Frozen change-point score and stylometric adversaries. |
| B04 | What, if anything, can be read from completed Ghost V15 without importing partial evidence? | Status/hash bridge only unless V15 has a final validated packet; no automatic V16. |
| B05 | Do coverage, source, access, compute, pursuit, warrant, dependency, and claim ledgers agree? | Machine reconciliation and clean-clone validation. |
| B06 | What moves in the project world model, and should a Stage 8, human bridge, or product confirmation open? | One final two-pass curator packet and explicit curator ruling; no automatic continuation. |

## 11. Cross-cutting adversarial matrix: 24 required attacks

Every attack names the questions it covers, independent units, expected invariant or reversal, and
the failure consequence before the scientific lock.

| ID | Attack | Required consequence |
|---|---|---|
| X01 | Replace the entire hidden future while holding visible bytes fixed. | Any non-oracle movement voids every affected result. |
| X02 | Replace hidden length, stopping parameters, and stop outcome. | Any movement voids stopping and state-use claims. |
| X03 | Replace future cues, interruptions, invalidations, and changed-context truth. | Any movement voids current and counterfactual claims. |
| X04 | Attempt forbidden imports, file opens, environment reads, cache reads, and callbacks from the reader process. | Successful access blocks the scientific lock. |
| X05 | Permute filenames, opaque IDs, source order, seeds, path lengths, and output paths. | Semantic results remain invariant. |
| X06 | Permute answer, action, and candidate order with fixed-order paired scoring. | Posterior and prediction remain invariant within tolerance. |
| X07 | Change one diagnostic visible observation while preserving hidden truth. | Relevant prediction moves; global invariance fails the reader. |
| X08 | Hash paired-arm evidence and remove any undeclared field advantage. | Unequal evidence voids the comparison. |
| X09 | Equalize or explicitly price model calls, tokens, context, solver work, retries, cache, and wall time. | Unpriced compute forbids an efficiency or architecture claim. |
| X10 | Paraphrase prompts, state descriptions, and serialization without changing operative meaning. | Behavior remains stable only where semantics are preserved. |
| X11 | Change operative meaning while matching length, fluency, specificity, and confidence language. | The prediction must change in the declared direction. |
| X12 | Duplicate or paraphrase evidence from one causal source. | Confidence cannot sharpen as if observations were independent. |
| X13 | Relabel supplied laws and candidate hypotheses while preserving their executable behavior. | Selection follows behavior, not tags. |
| X14 | Hold the final artifact and visible prefix fixed while swapping valid hidden histories. | Reader preserves the equivalence class. |
| X15 | Swap objective and subjective action spaces while holding the observed choice fixed. | Reader distinguishes availability from selection and competence. |
| X16 | Swap maker beliefs while holding objective facts, goal, and law fixed. | Belief-sensitive futures reverse; copied-world inference fails. |
| X17 | Swap expertise/action laws while matching observed prefix, endpoint, and surface. | Future-action predictions follow the law only when evidence supports it. |
| X18 | Swap proximal goals while matching belief, expertise, prefix, and endpoint. | Goal-sensitive diagnostic event reverses. |
| X19 | Swap context, cost, opportunity, or audience while holding standing tendency fixed. | Context effects are not reported as preference change. |
| X20 | Strengthen persistence, position, grammar, genre, and opportunity baselines. | Maker claims require gain beyond the frozen common-process rival. |
| X21 | Transfer across reader size/family, maker family, domain, and evidence regime. | Conditional failures are reported before pooling. |
| X22 | Normalize style around a real human/model switch and create a style switch without a control switch. | Discontinuity reader follows process, not surface register. |
| X23 | Duplicate/reorder rows, leak descendants across splits, and construct planned sign reversals. | Independent-unit estimates remain stable and pooled masking is detected. |
| X24 | Fresh-clone every manifest, source hash, access receipt, completion state, confirmation input, and report dependency; force kill/resume once. | Any mismatch blocks the final packet. |

## 12. Gates, branching, promotion, and closure

### 12.1 Gate order

1. **Record gate:** Stage 6 correction and dependency audit are written through.
2. **Construction gate:** oracle gaps are nontrivial; factor swaps and equivalence cases behave as
   declared.
3. **Isolation gate:** I03–I10 and X01–X08 pass in the real execution process.
4. **Keystone gate:** I16 passes by manual end-to-end trace.
5. **Supplied-state gate:** K04 and K15 determine whether any downstream maker-state claim is
   interpretable.
6. **Conformance gate:** an external architecture name is used only after its defining fixture.
7. **Reconstruction gate:** candidate recall, factor inference, and prospective use pass separately.
8. **Ecological gate:** controlled mixed histories pass before natural-record or product language.
9. **Confirmation gate:** at most three frozen claims run on untouched lineages.

### 12.2 Automatic branching

| Result shape | Continue | Close or rename |
|---|---|---|
| K01 has no oracle gap. | Repair the world/ruler once. | After one failed repair, that target is `INSTRUMENT_FAILED`; do not test readers on it. |
| K04 fails with executable true state. | Run K16's structured-compute and capacity diagnosis. | Close factor-inference comparisons for that target; call it a state-use/interface boundary. |
| K04 passes but K05 fails. | Repair natural-language state rendering once and compare executable adapters. | Do not call this general model incapacity. |
| K04/K15 pass and one missing-factor rung passes. | Advance one rung at a time to joint inference. | Do not skip directly to R13. |
| KL works but R09 fails. | Retain known-law system identification. | Close law-learning language. |
| Candidate recall fails. | Spend the one repair on proposal coverage. | Selection/posterior comparisons cannot rescue absent true candidates. |
| External conformance fails. | Use the mechanism under a descriptive local name if still useful. | No claim about the named research program. |
| SL-J beats `DIR` but not `DOM`. | Inspect generic process structure. | No maker-specific reconstruction claim. |
| P11/P12 pass and B03 confirms. | Promote a bounded mixed-process detector to a separate confirmation program. | Do not call it a universal final-text AI detector. |
| V05/V06 pass. | Carry the longitudinal ruler into a future dedicated value-shadow design. | Stage 7 still cannot claim value extraction or open alignment. |
| All useful locked work exhausts early. | Write the honest short-run receipt and close. | Never fill time with duplicate rows, sleep, or nominal cards. |

### 12.3 One-repair rule

Each instrument family receives one predeclared repair for implementation, construction, interface,
or ruler failure. A repair may not change the estimand, lower the meaningful-effect floor after
outcomes, add hidden evidence, substitute a retrospective endpoint, or relabel a failed local arm as
a published architecture. Preserve the failed lineage, reason, source hash, and superseding lineage.
The same gate failing after repair closes that family for Stage 7.

### 12.4 Promotion criterion

A Stage 7 bounded maker-model reader must, on untouched data:

1. pass physical isolation and hidden mutation attacks;
2. use a complete supplied maker model for both a hidden feasible action and a maker-dependent stop
   or continuation decision;
3. recover at least one withheld factor while preserving prospective advantage;
4. beat the strongest common-domain and same-evidence direct reader;
5. preserve equivalence classes and calibrate abstention;
6. survive semantic, option, law-tag, evidence-duplication, surface, and split attacks;
7. replicate on a second reader checkpoint or domain, with conditional failure reported;
8. survive one untouched confirmation without endpoint substitution.

The default smallest useful gain is 20% of the exact oracle-minus-`DOM` log-score gap, fixed before
reader outcomes, provided the oracle gap is itself meaningful. The world-specific construction may
justify a different floor only before scientific calls and with a written basis.

### 12.5 Confirmation freeze

After discovery closes, freeze at most three claims:

1. the strongest supplied-state capability result;
2. the strongest qualified factor-reconstruction or architecture result;
3. process-discontinuity localization, if P11 and P12 passed.

Confirmation uses untouched makers/worlds, histories, renderers, prompts, seeds, proposal lineages,
and transformation families. A failed confirmation cannot be replaced with the next-ranked result.

## 13. Runtime and workload contract

### 13.1 Corrected empirical prior

Stage 6 completed 160 locked cells in 47.07 hours:

\[
\text{observed throughput}=\frac{160}{47.07}=3.40
\quad\text{Stage-6 cells/hour},
\]

\[
\text{observed mean}=\frac{47.07}{160}=0.294\text{ h/cell}
=17.65\text{ min/cell}.
\]

Those cells were heterogeneous, so this is a sanity prior, not a scheduler constant. At the same
aggregate rate, 54–66 hours corresponds to about 184–224 Stage-6-equivalent cells. The discarded
Stage 7 pilot must replace this estimate with measured weighted costs for its own cell classes.

### 13.2 One clock

The 72-hour ceiling begins when the discarded end-to-end pilot starts. Pilot, model loading, sealed
process startup, conformance, GPU/CPU waits, repairs, inference, scoring, confirmation, validation,
and safe closure all consume the same clock. Restarting preserves the original deadline.

The workload lock targets 54–66 hours of useful work, leaving 6–18 hours inside the ceiling for
confirmation, validation, failures, and checkpoint safety. The ceiling is not a target to be filled.
If the complete locked useful ladder exhausts earlier, write `SHORT_RUN.json` and close honestly.

Exactly one curator packet is written after all mandatory dispositions, locked expansions,
confirmations, and validation finish. There are no preview, early, daily, trunk, milestone, partial,
or machine-synthesis packets.

### 13.3 Discarded pilot

All 100 question functions, 24 attacks, validators, scheduler paths, and report guards must exist and
smoke before the pilot. The pilot includes:

- the slowest full supplied-state and joint-reconstruction cell;
- one complete clean-room process startup and access audit;
- one conformance fixture from every potentially admitted external family;
- one long CoAuthor and ScholaWrite session;
- one mixed human/model history through change-point scoring;
- all admitted local reader sizes/interfaces;
- exact oracle and strong common-domain baselines;
- raw write, aggregation, checkpoint kill/resume, and validation.

Pilot lineages are quarantined and never enter science. Measure end-to-end wall time and device
occupancy, not inner-loop token time.

### 13.4 Frozen useful expansion ladder

If the core is faster than forecast or a branch closes, admit these rungs in order:

1. more independent makers, worlds, sessions, and mixed-control histories;
2. more near-equifinal models and later diagnostic events;
3. additional supplied-versus-inferred factor crossings;
4. longer visible prefixes and withheld multi-step tails;
5. the next comparable local reader size/interface;
6. more independent proposal sets where candidate recall is measured;
7. more style-normalized mixed-control lineages and adversarial edits;
8. a second domain or maker family under the frozen ontology;
9. a second untouched confirmation lineage.

No rung may add identical rollouts, duplicated evidence, arbitrary seeds, longer rationales, repeated
closed cards, sleep, or busy work. Each admitted unit has a unique causal lineage and changes an
independent scientific axis.

### 13.5 Allocation targets

| Elapsed interval | Work |
|---|---|
| hours 0–6 | discarded pilot, Stage 6 correction check, boundary and keystone audits, workload/scientific locks |
| hours 6–20 | known-world construction and supplied-state ladder |
| hours 20–36 | factor reconstruction and supplied-versus-inferred crossings |
| hours 36–48 | architecture conformance and compute decomposition |
| hours 48–58 | prospective benchmark and mixed-process bridge |
| hours 58–64 | bounded attention/history track, discovery closure, confirmation freeze |
| hours 64–72 | untouched confirmations, validation, fresh-clone receipt, final packet; no new branch |

These are scheduling targets, not permission to skip mandatory questions or advance past a failed
gate.

## 14. Implementation layout

Keep Stage 1–6 code and raw results immutable. Add a namespaced Stage 7 package with constructor,
reader, and scorer separated at the module and process levels:

```text
runners/stage7/
  cards.py
  manifest.py
  contracts.py
  scheduler.py
  runtime.py
  dependency_audit.py
  constructor/
    worlds.py
    histories.py
    oracle.py
  reader/
    worker.py
    baselines.py
    supplied_state.py
    joint_reader.py
  conformance/
    sources.py
    laip_style.py
    thought_tracing.py
    autotom.py
    liras_style.py
    inverse_planning.py
    labtom.py
  scoring/
    prospective.py
    stopping.py
    change_point.py
    calibration.py
  records/
    coauthor.py
    scholawrite.py
    mixed_control.py
  attacks.py
  confirmation.py
  report.py
  validate.py
  fresh_clone.py

results/phase_2_4_stage_7/
  STAGE6_DEPENDENCY_AUDIT.md
  STAGE6_DEPENDENCY_AUDIT.json
  SOURCE_MANIFEST.json
  INFORMATION_BOUNDARY.json
  KEYSTONE_AUDIT.md
  STRUCTURAL_LOCK.json
  WORKLOAD_LOCK.json
  SCIENTIFIC_LOCK.json
  QUEUE_MANIFEST.json
  EXPECTED_CELLS.json
  ATTACK_MATRIX.json
  SPLIT_RECEIPT.json
  COMPUTE_LEDGER.json
  RUNTIME.json
  COVERAGE.json
  raw/
  predictions/
  posteriors/
  confirmations/
  CURATOR_PACKET_FINAL.md
```

At execution time, materialize the `reader/` code plus the minimal immutable contract into a fresh
capsule. Do not put `constructor/`, `scoring/`, world manifests, target files, or repository root on
that process's path. The scoring process receives `PredictionV1` only after reader exit.

Every raw row carries question, cell, independent unit, complete lineage, reader revision, model
revision, architecture/conformance revision, prompt/schema hash, visible-evidence hash, prediction,
confidence, abstention/equivalence output, target reference stored outside the reader capsule,
compute receipt, timestamp, lane, and environment versions.

## 15. Required tests before scientific lock

1. Every question and attack is callable on a tiny non-scientific fixture and writes a unique output.
2. Removing any question, attack, factor corner, architecture, reader, target, lineage, or output
   fails recursive coverage.
3. The implementation-identity hash rejects duplicate question/statistic pairs.
4. `VisibleEvidenceV1` is allowlist-validated recursively.
5. Constructor/oracle imports and file reads fail from the actual reader process.
6. Hidden-tail, stop, and future-event mutation produce byte-identical canonical predictions.
7. A diagnostic visible change moves the intended prediction.
8. Target canaries fire through filenames, IDs, order, length, seed, cache, prompt, and schema paths.
9. Exact oracle posteriors match analytic tiny-world answers and preserve exact equivalence.
10. Stopping has a nontrivial maker-state oracle gap and matched length/progress base rates.
11. Objective context, maker context, belief, expertise, action space, goal, and history residue cannot
    overwrite or alias one another in schema or aggregation.
12. The same prefix can arise under different future laws; the later diagnostic event resolves only
    the designed pairs.
13. Complete supplied state uses no truth tag or constructor callback.
14. Candidate generation and candidate selection are logged and scored separately.
15. Known-law selection and learned-law transfer have different inputs and untouched targets.
16. Each named external arm passes its defining conformance fixture or is automatically renamed.
17. External reference code cannot see scientific or confirmation data.
18. Paired systems receive identical evidence bytes and obey compute contracts.
19. CoAuthor mini-logs recover accept, dismiss, reopen, edit, ignore, and delta application exactly.
20. Mixed-control fixtures distinguish actor, role, ratification, and change-point truth from style.
21. Natural and mixed-history splits keep all descendants together.
22. Row duplication/reordering does not move independent-unit estimates.
23. Conditional reader/domain/evidence effects are emitted before any pooled result.
24. The one-repair rule preserves failed lineages and cannot change locked estimands or floors.
25. Forced kill/resume cannot duplicate a completed unit or reset the deadline.
26. GPU and local-model locks cover load through unload; cleanup touches only owned processes.
27. Ghost V15 files remain byte-identical and no partial result is imported.
28. The reporter refuses while any mandatory disposition, locked expansion, confirmation, access
    receipt, or validation item is incomplete.
29. No alternate curator-packet path is writable.
30. A fresh clone reproduces manifests, hashes, dispositions, confirmation inputs, and final-packet
    dependencies.

## 16. Analyses

### 16.1 Primary endpoints

Use independent-unit paired log-score gains for the exact next feasible action and discrete-time
stopping hazard. Report Brier score and calibration beside them. For location/scope, use a
hierarchical proper score. For change points, score the full posterior over possible boundary
locations and report expected absolute boundary error; tolerance accuracy and AUPRC are secondary.

### 16.2 Capability decomposition

Report the entire ladder as a matrix of supplied versus inferred factors. The primary comparisons
are:

- oracle minus common-domain baseline;
- complete executable supplied state minus common-domain baseline;
- complete language state minus executable state;
- each single missing-factor inference minus its supplied-factor ceiling;
- full joint inference minus both `DOM` and `DIR`;
- learned law minus supplied-law selection on an untouched episode.

Never infer a latent merely because a predictor used a correlated common-process rule. Score factor
posterior and prospective gain separately.

### 16.3 Architecture and power

Architecture comparisons are conditional on conformance and lower-rung capability. Estimate
architecture × model size × inference-time compute × evidence regime × domain interactions. A
larger model is evidence about capacity only when it receives the same valid representation and
probability interface. A structured system is not “compute matched” merely because token counts are
equal; external solver work and proposal enumeration count.

### 16.4 Process discontinuity

Compare the maker-model reader against:

- character and token stylometry;
- perplexity or model-family features where available;
- edit persistence and position;
- a direct change-point prompt;
- the strongest stacked surface baseline frozen in discovery.

Require the style-normalized/process-switch versus style-switch/no-process-switch crossover. Report
final-only and process-aware interfaces separately. The final-only result can never borrow logged
actor identity.

### 16.5 Attention and historical mixture

Treat present allocation as indirect proximal evidence and expertise as a lossy, context-filtered
historical mixture. Compare one-artifact, ordered-undated, dated-series, and aggregate-history
models. Automatization may enter as a weak age prior only if calibrated on known histories. A
negative second derivative is not precision and has no Stage 7 estimand.

### 16.6 Multiplicity and conditional reporting

Maintain the repository multiplicity ledger. Discovery intervals allocate pursuit; untouched
confirmations carry warrant. Report maker/session/history-clustered uncertainty and effective sample
size. Never pool away a designed reversal across belief, goal, expertise, context, reader family,
domain, or evidence regime.

## 17. Record and theory write-through

Before the run, write only the Stage 6 audit correction and this accepted design. During execution,
machine-readable state may update continuously, but no curator-facing synthesis is emitted.

When Stage 7 closes:

1. append full hypothesis → method → result → meaning entries to `FINDINGS.md`;
2. add any new p-values to the multiplicity audit and rerun it;
3. update only the existing five theory files, using result rows and revised afterwords;
4. update `TODO.md`, `docs/STATE.md`, the design registry, root map, and method lessons;
5. preserve pursuit and warrant ledgers separately;
6. retain failures, dependency-tainted results, repairs, and exact equivalence classes;
7. add no public or README capability claim until the curator rules after Pass A.

The mission definition in §1 is now recorded here as the Stage 7 operational definition. Any later
move into the public README or top-level theory wording remains a curator-facing editorial decision,
not an automatic scientific result.

## 18. Claim ceiling

Stage 7 may establish:

- that the clean-room instrument does or does not prevent hidden constructor access;
- that named local readers can or cannot use a complete supplied maker model;
- which supplied or inferred factor carries prospective information in the declared worlds;
- that a system selects among supplied laws, learns a law from demonstrations, or reconstructs a
  subjective action space under bounded conditions;
- that a conformance-passed scaffold or Sounding joint reader improves a hidden choice over strong
  common-process rivals;
- that a controlled human/model process discontinuity can or cannot be localized under declared
  record access and attacks;
- that certain factors remain observationally equivalent and require abstention or more evidence.

It may not establish:

- unrestricted prediction of a person;
- unique recovery of a person's historical process from one artifact;
- a general human theory of mind, empathy, attention, or neural mechanism;
- that attention is identical to preference or that expertise is a timestamped value record;
- human value extraction, character judgment, sincerity, deception, propaganda, or alignment;
- a universal final-text AI detector or a human/model contribution percentage;
- superiority over LAIP, ThoughtTracing, AutoToM, LIRAS, or another research program from an adapted
  local task;
- that model-reader invertibility implies human invertibility.

The strongest permissible process-discontinuity claim, if confirmed, is:

> On the named held-out mixed revision histories and access condition, a bounded reader localized
> logged changes in control beyond the frozen surface and sequential baselines, while abstaining on
> histories whose control structure remained observationally equivalent.

## 19. Required final curator packet

Write exactly one `results/phase_2_4_stage_7/CURATOR_PACKET_FINAL.md` after closure and validation.

### Pass A: curator reads first

1. Five to ten sentences on how the project world model moved.
2. The minimum Stage 6 correction needed to interpret Stage 7.
3. One capability-ladder table showing `DOM`, supplied executable state, supplied language state,
   each successful missing-factor rung, full joint inference, and oracle.
4. One architecture table containing only conformance-passed names; local approximations use local
   names.
5. One ecological table for mixed-control, CoAuthor, and ScholaWrite outcomes.
6. Direct answers to:
   - Did the physical evidence boundary hold?
   - Could any reader use a complete supplied maker model?
   - Was the bottleneck proposal coverage, state representation, inference, or model capacity?
   - Could the system learn a maker law rather than select one supplied in advance?
   - Could it reconstruct the maker's perceived action space?
   - Did joint factor reconstruction improve hidden behavior beyond common process?
   - Could it localize a hidden human/model process discontinuity beyond style?
   - Did dated histories add any prospective information beyond aggregate expertise/style?
7. Three to six open theory-level questions for the curator. Stop for the verbal walkthrough.

Do not include a recommended Stage 8 before the curator's Pass A response unless every apparent
answer is mechanically forced by a closure rule.

### Pass B: analyst appendix

Include every question and attack disposition, dependency class, factor matrix, interval, candidate-
recall result, equivalence class, abstention curve, conformance fixture, compute receipt, access
receipt, repair, source lineage, split receipt, runtime forecast/actual, deferred cell, Ghost status
row, raw-output hash, confirmation freeze, and fresh-clone result. Separate discovery from
confirmation and pursuit from warrant.

## 20. Pre-mortem

The implementation is defective if any of these can happen unnoticed:

1. a reader can import the constructor or inspect the repository root;
2. visible evidence holds a callback or nested object that reaches hidden state;
3. future length, events, action inventory, stop shift, or changed-context truth affects a current
   non-oracle prediction;
4. an invariant reader passes because no visible-sensitivity test exists;
5. a target leaks through an identifier, seed, order, cache, schema, or length;
6. the scorer and reader share a live world object;
7. the exact oracle or supplied-law selector is reported as open-ended reconstruction;
8. the transition model is represented as a psychological factor separate from expertise;
9. objective context is substituted for the maker-interpreted context or subjective action set;
10. process is collapsed into expertise or expertise into the realized process;
11. one prose goal/controller label is called a complete supplied state;
12. a stop law cannot vary with the maker state it is supposed to test;
13. direct prompting remains the only baseline while common process does the work;
14. candidate selection is scored when the true candidate was never generated;
15. a larger model is used to rescue an invalid representation or ruler;
16. an external architecture name survives without its defining operations;
17. external code sees evaluation or confirmation data during setup;
18. two question IDs call the same world mapping, statistic, and comparison;
19. a fluent rationale is treated as a maker model without executable predictions;
20. accurate future prediction awards unmeasured belief, goal, expertise, or history credit;
21. factor accuracy without prospective gain is called understanding;
22. known-law selection is called law learning;
23. a style change is called a human/model process discontinuity;
24. a genuine process switch is erased by surface normalization and treated as a null;
25. CoAuthor acceptance remains unreachable behind delta handling;
26. ScholaWrite label persistence is mistaken for maker understanding;
27. current costly redirection is erased because automatic attention came from training;
28. historical expertise is treated as a clean dated point or current preference;
29. a Stage 7 attention/history result opens value or alignment work automatically;
30. partial Ghost V15 output enters Sounding evidence;
31. a repair changes the target, floor, evidence, or endpoint after results;
32. row count replaces maker/session/history effective sample size;
33. pooled means hide a planned factor or family reversal;
34. the runtime is filled with sleep, duplicate rollouts, arbitrary seeds, or repeated closed cards;
35. a crash resets the 72-hour deadline;
36. an early or partial packet pre-empts the curator's theory pass;
37. Stage 6 raw history is rewritten instead of corrected transparently;
38. a bounded model result is described as human empathy, value reading, or a universal AI detector.

## 21. Definition of done

Stage 7 is complete only when:

- all 100 mandatory questions and 24 attacks have honest dispositions;
- the Stage 6 dependency correction is written through without altering raw history;
- the reader/oracle boundary passes physical access, hidden mutation, and visible-sensitivity tests;
- the keystone audit passes before scaled science;
- every target has a nontrivial known-answer oracle gap or is marked instrument-failed;
- the complete supplied-state rung is resolved before any joint-inference claim;
- selecting a supplied law, learning a law, reconstructing subjective actions, identifying maker
  factors, and predicting from common structure remain separate;
- expertise owns the maker-specific transition law while process remains the realized trajectory;
- every named external method passes conformance or is renamed locally;
- strong common-process baselines accompany every maker claim;
- CoAuthor's event semantics are repaired and validated before scoring;
- mixed human/model change points are tested against surface-normalized and false-style-switch
  adversaries;
- attention/history tests retain current focus, historical mixture, context, expertise, and
  uncertainty as separate quantities;
- at most three claims run on untouched confirmation lineages;
- 54–66 useful hours are targeted from the discarded pilot under one 72-hour ceiling, with any early
  exhaustion recorded rather than padded;
- Ghost V15 remains untouched and incomplete evidence is not imported;
- exactly one final curator packet, coverage record, source/access/compute ledgers, hashes,
  confirmations, and fresh-clone receipt agree.

## 22. Handoff sentence

> Correct the Stage 6 record without rewriting it; build a physically separated visible-evidence
> reader whose output is invariant to every hidden-tail mutation and sensitive to diagnostic visible
> evidence; treat expertise as the maker's learned transition/action structure and process as the
> realized path through it; distinguish common-domain prediction, supplied-law selection, law
> learning, subjective-action reconstruction, maker-state identification, and prospective use;
> admit published names only after conformance; gate joint inference on complete supplied-state
> capability; compare structured computation, inference-time compute, and model size fairly; repair
> CoAuthor; make hidden mixed human/model process discontinuity the first ecological flight target;
> keep attention/history work bounded and value/alignment dormant; implement 100 distinct questions
> and 24 attacks; run 54–66 hours of useful work under one 72-hour ceiling without padding or an early
> packet; confirm at most three frozen effects; and report only the bounded claims the clean evidence
> path licenses.
