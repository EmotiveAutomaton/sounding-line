# Sounding Line Phase 2.0: Engineering Context

**Phase status note (2026-08-19).** Phases 2.1 (repair and foraging, curator-declared) and
2.2 (trajectory-conditioned inverse reading, [`PHASE_2_2_CONTEXT.md`](PHASE_2_2_CONTEXT.md))
now govern the mission and the core representation; this file's §7-style binary-wedge
mission language is superseded by 2.2 §1/§7. STILL IN FORCE from this file, unreplaced: the
curator interface (§15 roll-ups and synthesis mode), the escalation list (§16), the claims
policy (§18), and the sub-goal identifiers 2.0A-2.0H (2.0F's stack gate remains, re-gated
behind the Phase 2.1 decision gates and now also behind 2.2's representation validation).

**Status:** Governing handoff for the next development wave  
**Audience:** The primary coding and research agent working in `sounding-line`  
**Curator:** Abraham Haskins, PhD  
**Wider project:** *Art: A Unifying Model*  
**Repository snapshot consulted:** `1d38130`, 2026-08-16

> This is an operational context file, not a sixth theory document and not a replacement for the
> repository's existing rules. It fixes the high-level direction of Phase 2.0, defines what the
> phase must build, and establishes the abstraction boundary between the agent and the curator.
> Reconcile it with current repository state before acting. If later findings or an explicit
> curator ruling conflict with it, surface the conflict instead of silently preserving stale text.

---

## 1. Executive directive

Phase 2.0 has one mission:

> **Build and controlled-ground-truth validate a deployable binary AI-provenance classifier whose
> differentiating contribution is recoverable decision structure, while constructing the reusable
> intent-reading machinery required for later process and value inference.**

This mission deliberately combines three deliverables:

1. **The attention wedge:** a demonstrably better binary AI-provenance classifier, released freely
   if it clears a frozen competitive gate.
2. **The durable instrument:** a bounded reader of recoverable decisions, alternatives,
   dependencies, constraints, and evidential support.
3. **The release system:** a reproducible package with a scoring interface, weights, manifests,
   tests, documentation, calibration, and a public demonstration.

The detector is the public entry point. Recoverable decision structure is the project. Product
engineering is what makes either one real.

The phase should produce **one complete vertical slice**, not an indefinitely expanding collection
of studies. The slice runs from benchmark construction through decision representation, stacked
classification, held-out evaluation, packaging, and public demonstration.

---

## 2. Project identity and boundary

### 2.1 Sounding Line is an engineering project

Sounding Line searches for useful inference under bounded operating conditions. Its governing
question is not whether a general theory of human intent has been scientifically established. It is:

> **Can we build an instrument that recovers specified parts of a maker's decision process from an
> artifact, with known failure conditions, and can that representation solve a real problem better
> than existing systems?**

The appropriate loop is therefore:

1. Define a real output and operating condition.
2. Build candidate measures or representations.
3. Validate each ruler where the answer is known.
4. Test it against adversarial controls.
5. Integrate only the parts that carry independent information.
6. Package the surviving capability into a usable system.

Negative findings redirect the search. They do not automatically retract a theory-level
hypothesis, and they do not receive consolation language. The precise test determines which level
of the project a null updates.

### 2.2 Ghost Scale Sim has a different job

The neighboring Ghost Scale Sim repository handles constructed-world mechanism questions. It can
test inverse planning, known latent profiles, acting agents, and estimator behavior where the world
state is available by construction. Its results are authoritative about the implemented mechanism
and suggestive about the wider theory. They do not establish human intent or human values.

Use Ghost Scale when a question requires true hidden state, controlled agents, or mechanism-level
ground truth. Do not hand-build a weaker simulation inside Sounding Line. Use Sounding Line when the
question is whether a reader works on artifacts and supports a deployable engineering function.

### 2.3 What “non-human testing” means in this phase

A binary AI detector cannot be built or evaluated without human-authored controls. Therefore,
**Phase 2.0 cannot literally exclude human text**.

The binding interpretation is:

- Ground truth should come from controlled generation, prompting, selection, and revision records
  wherever possible.
- The phase does not infer human values or treat latent psychological stories as ground truth.
- Human artifacts may be used as provenance controls and as recorded-decision substrates.
- No result on an AI benchmark licenses a claim about persistent human motivation.

This preserves the intended non-human leg while keeping the detector statistically possible.

---

## 3. Current position at the start of Phase 2.0

### 3.1 What exists

The repository has built a strong experimental operating system:

- Known-answer validation before trusting a measure.
- Nulls capable of killing criteria.
- Construction, matched-comparison, length, no-maker, shuffle, power, leakage, and transfer
  controls.
- Hash-locked specifications and preregistrations.
- A reproducible queue, result ledger, theory roll-through, and audit chain.
- Frontier recreation work that distinguishes genuine capability from contaminated or
  underdetermined published results.
- A narrow foothold in recovering recorded revision purposes from artifact deltas beyond matched
  contextual alternatives.

The important conceptual pivot has already occurred: **the immediate unit is the recorded decision
event, not a scalar depth score for an entire artifact**. A decision event can carry a target,
alternatives, a selected option, dependencies, constraints, context, and evidence. That makes it
falsifiable and buildable.

### 3.2 What does not yet exist

The repository has not yet built:

- A validated general intent detector.
- A transferable structured decision reader for arbitrary artifacts.
- A Sounding Line AI-authorship model.
- Evidence that decision structure improves a conventional detector.
- A packaged scoring command, stable API, distributed weights, or deployment-grade model card.
- A human-value recovery system.

These are not wording caveats. They are the actual Phase 2.0 construction list.

### 3.3 How to interpret the first Phase 2 null

The first layering experiment appended a set of mostly surface-change channels to a PAN
style-change classifier through naive late fusion. It did not improve the substrate and introduced
seed instability.

Classify this result as:

> **Narrows the integration strategy.** The tested channels and fusion method did not help this
> style-change task.

Do not classify it as:

- A test of AI versus human provenance.
- A test of a functioning decision representation.
- A test of general intent extraction.
- A test of value inference.
- A decisive failure of stacking.

More sophisticated fusion is not automatically the answer. A representation must first demonstrate
that it measures planted or recorded decision structure. Otherwise better fusion only learns the
wrong variables more efficiently.

---

## 4. Locked high-level design decisions

These decisions are settled for Phase 2.0 unless the curator explicitly reopens them.

| Decision | Binding form | Engineering consequence |
| --- | --- | --- |
| **Phase mission** | Binary detector as public wedge; recoverable decisions as the core capability | Build both in one vertical slice without conflating their targets |
| **Positive class** | A generative model made a substantial contribution to the final artifact's wording or structure; incidental correction does not count | Preserve detailed authorship regimes, then collapse through an explicit binary policy |
| **Product form** | Externally binary, internally structured | Public output may lead with a probability, while internal outputs retain decision and regime evidence |
| **Core differentiator** | Recoverable decision structure, not another surface-style feature bank | Independently validate the decision representation before asking it to improve provenance |
| **Benchmark design** | Cross provenance with delegated human choice | Do not allow “human decision dose” to become a hidden synonym for human versus AI |
| **Detector substrate** | Reproduce strong existing methods rather than seeking novelty in the baseline | Sounding Line's contribution is measured as conditional lift over a credible substrate |
| **Integration order** | Diagnostic late stacking first; deeper fusion only after complementary information is shown | Preserve interpretability and obtain a clean ablation |
| **Success claim** | “Superior” is a frozen evaluation result, not an aspiration promoted as fact | Fix data, splits, metrics, baselines, and thresholds before the decisive comparison |
| **Product engineering** | Infrastructure begins with the phase, not after a favorable model result | CI, manifests, packaging, interfaces, and model documentation are first-class workstreams |
| **Value compatibility** | Do not attempt value recovery in Phase 2.0; preserve the variables later value work needs | Store goals, constraints, expertise, context, relationships, and process history separately |
| **Curator interface** | Abraham steers theory groups, phase transitions, public claims, and material tradeoffs | The agent owns identifiers, runners, seeds, queue mechanics, and ordinary implementation choices |

---

## 5. The hypotheses Phase 2.0 is actually testing

### 5.1 The detector hypothesis

The detector does not require intent and provenance to be equivalent. It requires only that the
decision representation add information after a conventional detector has used its normal evidence:

\[
I\!\left(Y_{\mathrm{AI}};S_{\mathrm{decision}}\mid S_{\mathrm{baseline}}\right) > 0
\]

In plain language:

> **Does recoverable decision structure correct enough errors made by a conventional detector to
> improve held-out provenance classification?**

The working population hypothesis is that most practical AI use is motivated by time savings and
therefore delegates many local choices. Even rich prompting can specify the destination while
delegating most of the final wording and structural decisions. The resulting artifact may carry
substantial human direction but relatively sparse recoverable human decision structure.

This is a plausible engineering prior, not a universal rule. The benchmark must include the
exceptions rather than treating them as philosophical disproofs.

### 5.2 The decision-reader hypothesis

Given bounded candidates, controlled context, or recorded process traces, final artifacts contain
recoverable information about selected purposes and choices beyond matched alternatives.

The reader must recover **specified choice structure with evidence**, not generate a persuasive
story about why the artifact exists.

### 5.3 The interaction hypothesis

Decision recoverability is not expected to behave as a monotonic AI score:

- Low-effort or templated human work may look decision-thin.
- Carefully prompted, selected, and substantially revised AI work may carry recoverable human
  decisions.
- Model rewriting can preserve some high-level human structure while replacing local wording.
- Heavy human reconstruction of a model draft can restore decision structure without changing the
  artifact's mixed provenance.

The stack must learn when each component is reliable. Conceptually:

\[
P(\mathrm{AI}\mid x)=f(S_{\mathrm{baseline}},S_{\mathrm{decision}},
S_{\mathrm{baseline}}\!\times\!S_{\mathrm{decision}},R,D,L,U)
\]

where \(R\) is authorship regime evidence, \(D\) is domain, \(L\) is length, and \(U\) is the
decision reader's uncertainty or identifiability estimate.

### 5.4 The value-compatible hypothesis

Persistent motivational organization, if recoverable at all, appears only after episode-level
goals, expertise, constraints, and context have been modeled across multiple artifacts. Phase 2.0
does not test that claim directly. It builds the lower-level representation and data architecture
without collapsing those variables into one score.

---

## 6. Theory groups translated into engineering obligations

The curator-facing vocabulary is the five living theory groups. Study identifiers belong in the
detail layer and may appear parenthetically only when needed for traceability.

| Theory group | Phase 2.0 engineering role | Required output |
| --- | --- | --- |
| **The Triple Inference** | Separates proximal goal, process, expertise, context, and persistent organization; defines identifiability boundaries | A data and output schema that never silently treats one target as another |
| **Three Cognitive Layers** | Supplies candidate architectural transformations and missing-middle hypotheses | Independently testable feature or model families; no requirement to prove a neuroscientific mapping |
| **Decision Traces** | Defines the observable residue of targets, alternatives, choices, dependencies, revision, and constraint-sensitive action | A structured, evidence-bearing decision representation |
| **Reader Heuristics** | Defines how a bounded reader enters, traverses, updates, stops, calibrates, and refuses | Candidate comparison, evidence localization, confidence, abstention, and non-identifiability |
| **Alignment** | Defines the later objective once a reader exists | Dormant in Phase 2.0; preserve its wake conditions and make no alignment claim |

Every sub-goal and study must name which theory group it serves. A study may serve more than one,
but “general exploration” is not an adequate classification.

---

## 7. Canonical definitions

### 7.1 Intent

For this phase, **intent is not an unconstrained latent mental state**. It is the recoverable,
problem-directed organization of choices under a bounded context, with explicit uncertainty about
what the artifact cannot identify.

### 7.2 Decision event

A decision event is a structured record containing as much as is known of:

- The target of the choice.
- The available or plausible alternatives.
- The selected alternative.
- The constraints active at the time.
- Dependencies on prior or subsequent choices.
- The proximal goal served.
- The artifact evidence created by the choice.
- The process record that establishes ground truth.

### 7.3 Recoverable decision structure

The portion of decision events that a bounded reader can infer from the final artifact, given its
declared context and operating conditions. Recoverability belongs to a reader-artifact-context
triple, not to the artifact alone.

### 7.4 Human decision dose

The amount and consequence of human choice retained in the final artifact. It is not equivalent to:

- Time spent.
- Prompt length.
- Number of turns.
- Surface quality.
- Human authorship.

Prompting, selection, ordering, constraint-setting, local editing, structural revision, and
acceptance can all contribute. Record these components separately before deriving any compact dose
variable.

### 7.5 Provenance

The generating and transformation history of the artifact. Provenance is a process label. Decision
recoverability is an inferential property. They may correlate without being identical.

### 7.6 Substantial model contribution

A model contribution is substantial when generated content materially determines final wording or
structure. Spellcheck, punctuation correction, and similarly incidental assistance do not count.
Direct generation, sentence-level rewriting, structural planning that survives into the artifact,
or other material generation does count under the initial policy.

This policy must be operationalized through examples and adjudication rules before the benchmark is
frozen. Do not invent an arbitrary percentage of tokens and treat it as the construct.

### 7.7 Abstention

An explicit output when the artifact is too short, out of distribution, internally mixed beyond the
model's resolution, or unsupported by enough evidence for the requested claim. Abstention is a
product behavior, not a post-hoc caveat.

---

## 8. Authorship taxonomy and binary policy

Train and evaluate on the detailed process regimes. Collapse to binary only at the product-policy
layer.

| Regime | Initial origin | Later control | Default binary policy | Why retained separately |
| --- | --- | --- | --- | --- |
| **Human** | Human | Human | Negative | Establishes ordinary human range |
| **Low-effort or templated human** | Human | Human | Negative | Primary false-positive stress test for the decision layer |
| **Direct model generation** | Model | Minimal human selection | Positive | Easy provenance case and baseline sanity check |
| **Richly directed model generation** | Model | Prompting and selection | Positive | Tests whether prompt-level direction survives as artifact-side decision structure |
| **Human-to-model rewrite** | Human | Model rewrites wording or structure | Positive when contribution is substantial | Tests preservation of human goals under model-local realization |
| **Model-to-human revision** | Model | Human revises | Usually positive under the contribution policy; retain degree and revision regime | Tests recovery of human reconstruction on mixed provenance |
| **Iterative mixed authorship** | Mixed | Alternating human and model control | Policy-derived, with uncertainty retained | Represents realistic collaboration and prevents binary supervision from erasing process |
| **Incidental assistance** | Human | Correction only | Negative | Defines the lower boundary of model contribution |

The public label should be phrased as:

> **Probability that a generative model made a substantial contribution to this artifact's final
> wording or structure.**

Do not present it as the probability that “the author is AI.”

---

## 9. Phase 2.0 sub-goals

The identifiers below are curator-facing program names. The coding agent may map them to stable
repository study identifiers without renumbering existing work.

### 2.0A: Reconcile the repository with this directive

**Goal:** Convert the existing Phase 2 queue into a vertical-slice plan without discarding current
studies or results.

Required actions:

- Map every open Phase 2 item to a theory group and workstream.
- Classify each as core capability, benchmark support, competitive substrate, infrastructure, or
  deferred.
- Preserve all stable identifiers.
- Mark the first layering null as an integration constraint, not a core hypothesis verdict.
- Identify duplicated sources of truth before adding new planning documents.
- Produce a concise migration note showing what moved, what stayed, and what was deferred.

**Exit evidence:** A coherent Phase 2.0 dependency order exists and every active item has a role.

### 2.0B: Freeze the task and evaluation contract

**Goal:** Define the target before optimizing it.

Required decisions and artifacts:

- Operational binary-label guide with positive, negative, and adjudication examples.
- Full authorship-regime taxonomy.
- Primary and secondary metrics.
- Frozen split logic.
- Competitive baseline-selection rule.
- Hard-regime slices.
- Claim language allowed at each result tier.

**Exit evidence:** A future result cannot change the task definition, split, or success metric after
the scores are visible.

### 2.0C: Build the crossed provenance-decision benchmark

**Goal:** Vary provenance and delegated human choice independently.

Required benchmark conditions include:

- Careful human work.
- Low-effort or templated human work.
- Thin-prompt direct generation.
- Richly directed generation with selection.
- Human text substantially rewritten by a model.
- Model drafts lightly and heavily revised by humans.
- Iterative mixed collaboration.
- Incidental AI assistance.

The benchmark must also vary domain, register, length, quality, generator family, and visibility at
training time.

**Exit evidence:** A manifest and data card demonstrate that provenance cannot be inferred from the
decision-dose condition by construction.

### 2.0D: Validate the recoverable-decision representation

**Goal:** Demonstrate that the differentiating representation recovers known choices rather than
quality, register, length, or provenance leakage.

Use constructed or process-recorded tasks where targets, alternatives, and selected choices are
available. Include unchanged artifacts, no-maker cases, symmetric candidates, decoys, and evidence
localization.

**Exit evidence:** The representation beats verified floors on known decision events, remains
calibrated, and fails or abstains appropriately on cases without identifiable decisions.

### 2.0E: Reproduce the competitive provenance substrate

**Goal:** Establish the system Sounding Line must improve.

At minimum include:

- One strong trained detector representative of current competitive practice.
- One complementary statistical or zero-shot method when it contributes distinct errors.
- A plain metadata and surface-feature reference that reveals leakage.

Reproduction must be faithful enough that a shortfall is investigated as an implementation defect,
not waved away as stochasticity.

**Exit evidence:** Frozen baseline outputs and error slices on the Phase 2.0 benchmark.

### 2.0F: Stack and diagnose

**Goal:** Test the conditional-information hypothesis cleanly.

Compare:

1. Conventional substrate alone.
2. Decision representation alone.
3. Calibrated late stack.
4. Interaction-aware stack.
5. Deeper or joint fusion only if the first four establish complementary information.

Initially keep the decision reader independently trained or frozen. If provenance supervision is
allowed to redefine it immediately, a favorable result cannot show that decision structure added
anything; the layer may simply become another detector.

**Exit evidence:** A preregistered ablation identifies whether the decision representation adds
held-out information and where.

### 2.0G: Harden against shift and mixed authorship

**Goal:** Determine whether any lift survives the conditions where ordinary detectors fail.

Required stress tests:

- Unseen generator family.
- Unseen domain.
- Unseen authors.
- Human-to-model rewriting.
- Model-to-human reconstruction.
- Rich prompting and selection.
- Low-effort human negatives.
- Short texts.
- Non-native or otherwise distribution-shifted human writing where ethically and legally sourced.
- Benign transformations and common evasion operations.

**Exit evidence:** Worst-slice performance and calibration, not just one aggregate score.

### 2.0H: Productize and release

**Goal:** Turn the validated slice into something another person can run and inspect.

Required outputs:

- Installable package.
- Reproducible scoring CLI.
- Small stable API.
- Versioned weights and checksums.
- Dataset and split manifests.
- CI and automated regression tests.
- Calibration and threshold artifacts.
- Model card and benchmark report.
- Public demonstration with evidence and abstention.
- Release checklist and tagged version.

**Exit evidence:** A clean machine can reproduce a published evaluation and score a user-supplied
artifact without bespoke runner knowledge.

---

## 10. Workstream specifications

### 10.1 Conventional provenance substrate

The substrate is not where novelty is required. Select the strongest reproducible methods current at
implementation time, record the selection date, and reproduce them faithfully.

The substrate must expose:

- Raw component scores.
- Calibrated probability.
- Model and version identity.
- Domain and length sensitivity.
- Error slices.
- Runtime and resource cost.

Do not compare Sounding Line only against stale or weak detectors. If the strongest method cannot be
reproduced from public materials, document the exhausted routes and use the strongest reproducible
competitor rather than silently weakening the finish line.

### 10.2 Recoverable-decision representation

The structured representation should be capable of carrying:

```yaml
artifact_id: stable identifier
reader_version: exact reader build
operating_context:
  brief: known, partial, or absent
  constraints: []
  candidate_space: bounded, generated, or unknown
decisions:
  - decision_id: stable within artifact
    target: what was being decided
    candidates: []
    selected: candidate or unknown
    evidence_spans: []
    constraint_links: []
    dependency_links: []
    proximal_goal: value or unknown
    confidence: calibrated probability or interval
    identifiable: true or false
reader_summary:
  recoverable_count: value with definition
  coupling: value with definition
  delegated_choice_indicators: []
  uncertainty: value with definition
  abstention_reason: null or controlled vocabulary
```

This is a conceptual contract, not a command to overwrite an existing validated schema. Reconcile
it with the current event-recovery harness and locked specifications.

The compact detector-facing embedding must be derived from this representation. Never make the
embedding the only retained product.

### 10.3 Reader heuristics

The reader must have explicit stages:

1. **Entry:** identify candidate loci where a consequential choice may have left a trace.
2. **Candidate generation:** form bounded competing explanations or choices.
3. **Traversal:** collect local and nonlocal evidence, including dependencies.
4. **Updating:** compare candidates rather than merely accumulating supporting prose.
5. **Stopping:** stop when further traversal is unlikely to change the posterior.
6. **Calibration:** report uncertainty against known-answer tasks.
7. **Refusal:** mark non-identifiability when the artifact cannot support the requested inference.

An eloquent explanation without candidate competition, evidence, and calibrated failure is not a
reader result.

### 10.4 Product and reproducibility system

Build ordinary software discipline into every workstream:

- One command for environment setup.
- Pinned runtime and model versions.
- Deterministic or explicitly stochastic runs with saved seeds.
- Dataset provenance, licensing, hashes, and split membership.
- Configuration files instead of hidden runner constants.
- Unit tests for parsing, schemas, scoring, and policy collapse.
- Integration tests for end-to-end scoring.
- Regression fixtures with known outputs.
- CI that runs the affordable test tier on every change.
- Explicit slow, GPU, local-model, API, and release test markers.
- Checkpoint resume and failure-safe artifact writing.
- Versioned outputs that can be traced to code, data, and model state.
- A clean out-of-distribution and too-short-text response.

Do not weaken the repository's existing hash locks or overwrite locked specifications. Extend through
new versioned surfaces and record deviations through the established mechanism.

### 10.5 Longitudinal compatibility

Every benchmark record should preserve, where known:

- Maker or generating system.
- Model, version, decoding settings, and tool chain.
- Initial origin and each subsequent transformation.
- Brief and proximal goal.
- Constraints.
- Expertise or capability condition.
- Context and domain.
- Prompts, selections, and revision history.
- Decision-dose components.
- Artifact relationships across drafts and episodes.
- Ground-truth decision events.
- Binary label and the policy version that produced it.

Later value work needs repeated episodes and held-out tradeoff prediction after expertise, context,
brief, and proximal goal are modeled. If Phase 2.0 flattens these fields into one provenance label,
the project will have to rebuild its data architecture.

---

## 11. Crossed benchmark contract

### 11.1 Core factorial logic

The benchmark must vary at least these axes:

| Axis | Required levels or treatment |
| --- | --- |
| **Initial origin** | Human; model |
| **Subsequent transformer** | None; human; model; alternating |
| **Human decision dose** | Low and high at minimum, decomposed into recorded components |
| **Model contribution** | Incidental; local; substantial wording; structural |
| **Revision and selection** | None; light; heavy; selection among alternatives |
| **Surface quality** | Matched or explicitly stratified |
| **Domain and register** | Multiple, including held-out domains |
| **Length** | Stratified, with a short-text stress slice |
| **Generator exposure** | Seen and unseen families or versions |
| **Author exposure** | Seen and unseen authors |

The design must contain counterexamples that break every shortcut:

- Human and AI artifacts matched on quality.
- Low-decision human and high-decision AI artifacts.
- Identical source text under different transformation histories.
- Similar prompt burden with different degrees of retained human control.
- Same generator across multiple domains and multiple generators within one domain.
- Multiple artifacts from the same source grouped into one split.

### 11.2 Split rules

At least one decisive evaluation must hold out authors, domains, and generator families together.
Additional diagnostic splits may isolate each source of shift.

Binding leakage rules:

- All drafts, rewrites, paraphrases, and siblings derived from one source stay in one partition.
- Prompt templates and topic packages are grouped when they can leak labels.
- Model versions are recorded, and near-identical aliases are not treated as independent families.
- Calibration data remain separate from final test data.
- The final comparison is run once after thresholds and policies are frozen.
- Any contamination discovered later triggers a dependency audit of every result that used the split.

### 11.3 Minimum record schema

Each artifact record should contain or reference:

```yaml
artifact_id: stable identifier
lineage_id: shared by all derived versions
episode_id: generation or revision episode
content_ref: immutable content location and hash
domain: controlled label
register: controlled label
language_context: controlled label
initial_origin: human or model
authorship_regime: detailed regime
binary_label: derived by policy
binary_policy_version: exact version
human_roles:
  prompting: recorded level
  selection: recorded level
  local_editing: recorded level
  structural_revision: recorded level
model_roles:
  generation: recorded level
  rewriting: recorded level
  planning: recorded level
process_refs:
  prompts: []
  candidate_generations: []
  revisions: []
  decision_cards: []
generator:
  provider: value or local
  model: exact identifier
  version_or_date: value
  decoding: {}
conditions:
  quality: measured or matched condition
  length_bin: value
  decision_dose: derived plus components
split:
  group_keys: []
  partition: train, validation, calibration, or test
provenance:
  source: value
  license: value
  collection_method: value
```

Do not store sensitive personal information merely because the schema can hold it. Retain only what
is required for reproducibility and the intended future inference.

---

## 12. Detector-stack architecture

The initial architecture should remain modular enough to answer whether Sounding Line contributed
independent information.

### 12.1 Pipeline

1. **Ingest and validate:** normalize content without destroying provenance-relevant or
   decision-relevant structure; record any transformation.
2. **Conventional substrate:** produce one or more provenance scores and reliability metadata.
3. **Decision reader:** produce the structured representation, compact summary features, evidence,
   and identifiability estimate.
4. **Regime context:** include domain, length, quality controls, and any legally available process
   metadata intended for the selected operating mode.
5. **Stack or router:** combine component outputs and their interactions.
6. **Calibration:** map to the public binary probability under a versioned policy.
7. **Abstention and evidence:** return controlled failure states and a concise explanation of which
   component evidence drove the result.

### 12.2 Training separation

The first decisive stack must preserve an independent test of the decision layer:

- Train or validate the decision reader against decision ground truth.
- Freeze it or otherwise prevent binary provenance supervision from silently replacing its
  construct during the first ablation.
- Train the meta-classifier on component outputs.
- Measure lift on held-out provenance regimes.

Only after this test may joint training or earlier fusion be attempted. A joint model may be a
better product, but it cannot by itself demonstrate that recoverable decision structure caused the
improvement.

### 12.3 Public output contract

The user-facing system should be able to return:

```json
{
  "model_contribution_probability": 0.0,
  "classification": "human | substantial_model_contribution | indeterminate",
  "threshold_policy": "versioned identifier",
  "authorship_regime_hypotheses": [],
  "decision_recoverability": {
    "summary": "bounded plain-language statement",
    "confidence": 0.0,
    "evidence": [],
    "identifiable": true
  },
  "warnings": [],
  "model_version": "exact identifier"
}
```

Exact fields may evolve. The non-negotiable property is that the binary result remains traceable to
structured internal evidence and a versioned threshold policy.

---

## 13. Evaluation contract

### 13.1 Provenance metrics

Report at least:

- F1 on the declared benchmark prevalence for public comparability.
- Precision and recall separately.
- True-positive rate at a low fixed human false-positive rate, including 1 percent where sample size
  supports it.
- Area under the precision-recall and receiver-operating curves.
- Calibration through Brier score, expected calibration error, and reliability plots.
- Selective risk versus coverage when abstention is enabled.
- Worst-condition and hard-regime performance.
- Confidence intervals or seed intervals appropriate to the training regime.
- Runtime, memory, and cost.

F1 is a headline measure, not the whole operational truth. It changes with prevalence and can hide
false accusations.

### 13.2 Decision-reader metrics

Use measures appropriate to the known-answer task, including:

- Candidate-choice accuracy or ranking against a verified floor.
- Recovery beyond matched contextual alternatives.
- Evidence-span localization.
- Calibration and proper scoring.
- Abstention quality on non-identifiable cases.
- Robustness to length, register, quality, and candidate wording.
- Transfer across artifact families or task domains.
- Error decomposition by target, amount, coupling, and realization.

No aggregate “intent score” should replace the tuple merely for convenience. Compact summaries may
be derived for the detector, but the evaluation must remain capable of showing which component
worked.

### 13.3 Frozen superiority gate

Before the decisive test, freeze:

- Data version and hashes.
- Train, validation, calibration, and test partitions.
- Competitive baselines and their versions.
- Primary metric and tie-breaking secondary metrics.
- Public binary policy.
- Threshold-selection procedure.
- Seed policy.
- Exclusion and abstention rules.
- Hard-regime slices.
- Claim language for pass, mixed, null, and regression outcomes.

The public success case has three parts:

1. **Headline lift:** the stack improves the frozen primary metric over the strongest reproduced
   conventional baseline.
2. **Operational lift:** it improves or preserves detection at the fixed low human false-positive
   rate.
3. **Hard-regime integrity:** it improves or preserves performance on unseen generators, mixed
   authorship, rich prompting, and low-effort human controls.

An aggregate gain accompanied by a material regression on low-effort human negatives does not
license “superior.” A gain that exists only in-domain does not license “generalizes better.”

### 13.4 Result-routing rules

| Result | Interpretation | Next action |
| --- | --- | --- |
| Decision reader validates; stack lifts | Core hypothesis and public wedge both advance | Harden, replicate, package, and prepare release |
| Decision reader validates; stack is null | Decision capability survives; provenance complementarity is unsupported under tested conditions | Diagnose error overlap, try justified interactions, cap detector iteration, preserve decision product |
| Decision reader fails known-answer gates | The current representation is not an intent instrument | Stop detector fusion and return to Decision Traces or Reader Heuristics |
| Stack lifts only in-domain | Likely leakage or narrow specialization | No superiority claim; redesign splits or representation |
| Stack lifts but human false positives worsen | Product tradeoff fails the operational gate | Recalibrate, route by regime, or reject the stack |
| Baseline cannot be faithfully reproduced | Finish line is unresolved | Repair reproduction or explicitly select the strongest reproducible baseline |
| Benchmark label proves unstable | Binary task is under-specified | Repair adjudication before further optimization |

Initial negative results are not reasons to abandon the project. They are also not reasons to keep
the same design indefinitely. **Every null must remove, narrow, or redirect something.**

---

## 14. Product requirements

### 14.1 Command-line interface

Provide one documented command that accepts text or a file and emits human-readable and JSON output.
The exact command name should follow the package's existing conventions. It must support:

- Model and threshold-policy selection.
- Offline scoring when weights are local.
- Structured JSON output.
- A quiet machine-readable mode.
- Batch input.
- Explicit indeterminate status.
- Version information.
- A reproducible example.

### 14.2 API

Expose a small stable library interface independent of the CLI. Separate:

- Artifact validation.
- Decision reading.
- Provenance component scoring.
- Stack and calibration.
- Policy collapse.
- Explanation formatting.

Do not make bespoke experiment runners the only way to invoke the product path.

### 14.3 Weights and artifacts

Every published model should have:

- Versioned weights.
- Cryptographic checksum.
- Training configuration.
- Data-manifest references.
- Code commit.
- Calibration object.
- Threshold-policy version.
- License and usage constraints.
- Known failure slices.

### 14.4 Continuous integration

CI should cover the affordable path on each change:

- Import and installation.
- Unit tests.
- Schema validation.
- Known-answer fixtures.
- CLI smoke test.
- Deterministic miniature end-to-end test.
- Hash-lock checks.
- Theory formatting checks when theory is touched.

GPU, external API, local-model, slow benchmark, and release tests should be separate, explicitly
triggered tiers. Cloud or Gear 3 rules remain exactly as set by the curator.

### 14.5 Public demonstration

The demo may lead with the binary probability because that is the attention wedge. It should also
show:

- The claim being made in precise language.
- Whether the artifact is inside the supported operating range.
- The most relevant decision-recoverability evidence.
- Uncertainty and abstention.
- Model and policy version.
- A short explanation of mixed authorship.

The demo is an evidence viewer, not an accusation machine. This is both ethically necessary and
commercially pragmatic: a tool that confidently mislabels low-effort humans will lose trust faster
than it gains attention.

---

## 15. Curator abstraction boundary

### 15.1 Principle

Abraham should not need encyclopedic knowledge of study identifiers, seeds, runner names, or queue
mechanics to steer the project. His control surface is:

- Theory groups.
- Phase and sub-goal status.
- Surviving mechanisms.
- Killed interpretations or instruments.
- The next engineering obligation.
- Public claims currently licensed.
- Decisions that materially change mission, theory, product policy, cost, or release risk.

The coding agent's control surface is:

- Study identifiers.
- Runner implementation.
- Seed and checkpoint mechanics.
- Queue construction.
- Reproduction details.
- Routine refactoring and tests.
- File-level documentation synchronization.

This is an abstraction boundary, not a reduction in rigor. The detailed record remains fully
available and traceable. It simply stops being the primary unit of communication with the curator.

### 15.2 Preserve the existing landing loop

The repository already requires every completed result to move through:

> **Hypothesis → method → what was found → what it means**

and to be written through to the method archive, theory store, queue, and chat. Preserve that loop.
The missing addition is a fifth landing product:

> **Curator roll-up → which theory-group mechanism changed, in one of four forms**

### 15.3 The four permitted study roll-ups

Every completed study must be classified as exactly one primary type:

1. **Strengthens a theory-group mechanism.** The result makes a named mechanism more credible or
   extends its supported operating range.
2. **Narrows its operating conditions.** The mechanism survives, but only under a more specific
   condition, representation, population, or integration method.
3. **Kills an instrument or interpretation.** The tested measure, reader behavior, fusion scheme,
   or interpretation should no longer guide work.
4. **Changes infrastructure without changing theory.** The result repairs or extends machinery,
   reproducibility, speed, safety, or product readiness without updating a theory claim.

“Interesting,” “mixed,” and “more work needed” are not roll-up classes. Nuance belongs in the result
text; the primary project consequence must still be named.

### 15.4 Required study-completion block

Append or generate the following for every landed study:

```markdown
### Curator roll-up

- **Theory group:** The Triple Inference | Three Cognitive Layers | Decision Traces |
  Reader Heuristics | Alignment | Infrastructure only
- **Question in plain language:** What high-level uncertainty did this study address?
- **Outcome class:** Strengthens | Narrows | Kills | Infrastructure
- **Result:** One sentence, with at most the one number needed to understand its magnitude.
- **Project meaning:** What changed in the model of the system?
- **Next engineering obligation:** The next thing now required, or “none.”
- **Public claim:** Newly licensed, unchanged, weakened, or forbidden.
- **Curator decision required:** No | Yes: one high-level question with a recommended answer.
- **Detail pointer:** Stable study identifier and links to the full finding and artifacts.
```

The exact storage location should fit the existing record architecture. Do not paste duplicate
roll-ups into several files and create another synchronization burden.

### 15.5 Curator-facing milestone brief

At the end of a coherent batch or whenever a result changes direction, provide:

```markdown
## Curator brief

### What Phase 2.0 is trying to establish now
One paragraph at theory-group level.

### What changed
- Strengthened:
- Narrowed:
- Killed:
- Infrastructure only:

### Where the vertical slice stands
- Benchmark:
- Conventional substrate:
- Decision reader:
- Stack:
- Shift testing:
- Product and release:

### Current public claim
One paragraph.

### Next engineering obligation
One paragraph.

### Decisions for Abraham
Only material high-level decisions. State the recommended answer and consequence.

### Detail appendix
Study identifiers and links, without making them the narrative.
```

### 15.6 Interaction rules

When reporting to Abraham:

- Open with the high-level hypothesis or phase obligation, not an identifier.
- Translate metrics into their consequence before listing implementation detail.
- Group studies by theory mechanism or sub-goal.
- Distinguish a dead instrument from a dead theory claim.
- Distinguish a product failure from a decision-reader failure.
- Do not ask him to choose runner parameters, seed counts, or routine architecture details.
- When escalation is required, present the recommended decision, the strongest objection, and what
  each option changes.
- Do not make him hunt through the repository for the latest state.
- Preserve full technical detail behind links for auditability.

### 15.7 Rules and hook integration

The coding agent should merge this abstraction contract into the existing authoritative agent rules
and grind workflow with the smallest coherent edit. Do not replace the current workflow.

Add structural enforcement where practical:

- A study is not “landed” until its curator roll-up exists.
- The completion workflow checks for a valid outcome class.
- A milestone brief is regenerated only when high-level state changes, not after every seed.
- Identifiers remain stable and greppable.
- The roll-up links to the detailed finding rather than duplicating it.
- A hook may enforce presence and vocabulary; it must not pretend to validate the judgment itself.
- Current theory-format hooks, hash locks, queue guards, and result write-through requirements remain
  intact.

Because the existing rules already creep toward low-level queue reporting in every interaction, the
new rule should explicitly separate two modes:

1. **Execution mode:** queue state and landing details remain visible while work is running.
2. **Curator synthesis mode:** when Abraham asks where the project stands, the reply begins at theory
   groups and Phase 2.0 sub-goals; queue details move to a compact appendix unless they alter a
   decision.

---

## 16. Autonomy and escalation

### 16.1 The coding agent may decide autonomously

- Stable study identifiers and their mapping to Phase 2.0 sub-goals.
- Runner organization and internal module boundaries.
- Routine test design once the high-level hypothesis and frozen evaluation contract are preserved.
- Seed counts sufficient to satisfy established reproduction and interval rules within authorized
  compute.
- Checkpointing, caching, sharding, and local efficiency.
- Choice among equivalent libraries or implementation techniques.
- Routine bug fixes, refactors, documentation synchronization, and CI repairs.
- The order of independent low-cost tasks within the current phase dependency graph.
- Additional adversarial controls that do not redefine the target.
- Deferring an invalid run until its ruler, data, or null is repaired.

### 16.2 The coding agent must escalate

- Any change to the Phase 2.0 mission.
- Any change to the positive-class policy or public meaning of the binary output.
- Any proposal to collapse the structured decision representation into a single permanent score.
- Any theory-file structural change governed by the curator's existing rule.
- Any reinterpretation of a curator quotation.
- Any removal of a benchmark regime required by this document.
- Any move from episode-level intent into persistent human value inference.
- Any public “superior,” “intent detector,” “value reader,” or alignment claim not licensed by the
  frozen gates.
- Any material cost, cloud-compute, licensing, privacy, or distribution commitment outside standing
  authorization.
- Any result that kills the entire current decision-reader family rather than one instrument.
- Any tradeoff that improves aggregate performance by materially increasing human false positives.
- Any public release, benchmark announcement, or change in project positioning.
- Any conflict between this context, the living theory, and new results that cannot be reconciled by
  ordinary implementation.

Escalation should contain one recommended answer, the decisive evidence, the strongest real
objection, and the consequences. Do not send an unranked menu.

---

## 17. Documentation architecture

Preserve the repository's current distinction:

- **Theory folder:** what is believed, organized by theory group.
- **Findings ledger:** how each study was run and what came back.
- **Queue:** what is active, gated, blocked, or complete.
- **Operational state:** current machinery, standing rulings, and phase end states.
- **Tool ledger:** instrument validation status.
- **Method lessons and controls:** known failure patterns and licensed methods.

Add Phase 2.0 information to the smallest number of existing sources of truth. A reasonable mapping,
subject to reconciliation with current structure, is:

| Information | Recommended home |
| --- | --- |
| Governing Phase 2.0 direction | This context file under the design or operational shelf |
| Current high-level roll-up | One curator-status section in the operational state file or one linked companion file |
| Detailed study record | Existing findings ledger |
| Belief update | Existing theory group |
| Work queue | Existing queue and runner stage list |
| Frozen benchmark contract | Versioned Phase 2 benchmark specification |
| Product behavior and interfaces | Product documentation near the package |
| Release evidence | Versioned model card, benchmark report, and release checklist |

Do not create a second findings ledger, second queue, or second theory store.

---

## 18. Claims policy

### 18.1 Claims licensed now

- Sounding Line is building an instrument for recoverable decision structure.
- The project has a validated experimental discipline and a narrow indication that artifact deltas
  can carry recoverable information about recorded choices beyond matched context.
- The first naive feature-layering attempt did not improve its style-change substrate.
- It is reasonable to test whether a validated decision representation adds conditional information
  to AI provenance detection.
- The AI detector is a Phase 2.0 target, not an existing product.

### 18.2 Claims licensed after decision-reader validation

Only after the corresponding gates:

- The system recovers specified classes of decision events under named operating conditions.
- Its evidence and abstention are calibrated on the validated substrates.
- Its representation transfers across the tested artifact families.

### 18.3 Claims licensed after the frozen detector gate

Only if the stack clears all relevant criteria:

- Sounding Line improves the declared baseline on the frozen benchmark.
- It improves specific hard regimes without increasing the fixed human false-positive rate.
- The decision representation supplies complementary detector information under the tested
  conditions.
- The released detector is better than named reproduced alternatives on named metrics and splits.

### 18.4 Claims forbidden in Phase 2.0

- General human intent can be read from arbitrary artifacts.
- Low recoverable intent proves AI authorship.
- Generated work has no intent or no generating process.
- The detector establishes cheating, plagiarism, dishonesty, or who personally wrote an artifact.
- A single artifact reveals persistent human values.
- Ghost Scale simulation results establish human value recovery.
- The three cognitive layers have been established as literal neuroscience.
- A favorable in-domain F1 score establishes a vastly superior universal detector.
- A null on one feature bank disproves the project theory.

“Vastly superior” remains a design ambition until a frozen external comparison earns the phrase.

---

## 19. Pre-mortem and controls

| Failure mode | Early warning | Required mitigation |
| --- | --- | --- |
| **Generator or domain leakage** | Excellent random-split results and collapse on unseen sources | Group lineages, authors, domains, and generators; use simultaneous holdouts |
| **Decision reader becomes a quality or register scorer** | Length, vocabulary, or quality baselines reproduce its ranking | Factorial construction, matched counterexamples, and known-answer choice gates |
| **Low-effort humans are falsely labeled AI** | Templates, boilerplate, short answers, or non-native writing dominate false positives | Dedicated negative slices, interaction-aware routing, calibration, and abstention |
| **Rich prompting is mistaken for human authorship** | High prompt specificity overwhelms evidence of delegated local choices | Separate prompt direction from retained artifact-side decisions; rely on the stack |
| **Binary supervision corrupts the intent construct** | Decision embedding predicts provenance but fails decision ground truth | Independent supervision and a frozen-reader ablation before joint training |
| **Mixed authorship labels are arbitrary** | Annotators disagree or policy changes alter scores materially | Process traces, regime taxonomy, examples, adjudication, and policy versioning |
| **The benchmark is gamed** | Gains vanish under new topics, transformations, or generator versions | Frozen test, unseen families, external replication, and one-shot decisive evaluation |
| **Surface transformations defeat the product** | Minor paraphrase destroys predictions | Transformation stress suite, calibrated uncertainty, and explicit supported range |
| **A strong model cannot be released** | Evaluation depends on bespoke runners and undocumented state | Build the installable path, CI, manifests, and model artifacts during development |
| **The PR wedge consumes the project** | Detector variants multiply while decision validation remains open | Gate all advanced fusion on an independently validated decision representation |
| **Infrastructure work becomes endless** | Packaging expands without a functioning vertical slice | Tie each infrastructure task to the release path and defined exit evidence |
| **Nulls become immune to consequence** | Every failure produces a new variation without removing an option | Enforce the strengthens, narrows, kills, or infrastructure roll-up |
| **The curator is pulled into implementation detail** | Decisions arrive as study IDs, seed tables, or runner choices | Use the curator brief and escalation contract |
| **Compaction resurrects dead interpretations** | Interim summaries contradict current theory and findings | Reload living theory and end-state records; treat prior summaries as historical evidence only |

---

## 20. Immediate execution order

The first coding-agent pass after receiving this file should proceed in this order:

1. **Reload authoritative context.** Read the living theory folder, findings end states, operational
   state, method lessons, current queue, agent rules, and applicable format specifications.
2. **Reconcile rather than overwrite.** Compare this directive with current main, active jobs, locked
   files, and pending Phase 1 landings. List conflicts and dependencies.
3. **Create the Phase 2.0 dependency map.** Map current identifiers into sub-goals 2.0A through 2.0H.
4. **Amend the interaction contract.** Add the curator roll-up and synthesis-mode rules to the
   existing agent workflow with minimal duplication; add structural enforcement where safe.
5. **Write the frozen evaluation-contract draft.** Define the binary policy, regime taxonomy,
   metrics, splits, baselines, hard slices, and result language before model optimization.
6. **Specify the benchmark.** Produce the crossed factorial design, record schema, lineage grouping,
   data acquisition plan, licensing plan, and minimum viable sample/power analysis.
7. **Audit the product path.** Identify missing CLI, API, packaging, weights, CI, manifests,
   calibration, and documentation surfaces. Convert them into dependency-gated tasks.
8. **Validate the decision representation on known answers.** Do not begin deeper detector fusion
   until this survives.
9. **Reproduce and freeze the competitive substrate.** Establish the honest finish line.
10. **Run the ablation stack.** Substrate, decision layer, calibrated stack, interactions, then only
    justified deeper fusion.
11. **Harden the winner.** Shift, mixed authorship, low-effort human, transformation, calibration,
    runtime, and release tests.
12. **Return a curator brief.** Report the phase map, material conflicts, recommended decisions, and
    what begins running next at theory-group level.

Do not stop useful current work merely to reorganize documents. Land valid in-flight results through
the existing workflow, then absorb them into the Phase 2.0 map.

---

## 21. Phase completion conditions

Phase 2.0 is complete when all of the following are true:

### Program and benchmark

- The binary policy and detailed regime taxonomy are versioned.
- The crossed benchmark exists with lineage-safe, author-safe, domain-aware, and generator-aware
  splits.
- Data provenance, licensing, hashes, and process records are documented.

### Instrument

- The recoverable-decision representation passes known-answer gates.
- Its controls show that it is not reducible to length, quality, register, or candidate wording.
- Evidence, calibration, and abstention are evaluated.

### Detector

- Strong conventional baselines are faithfully reproduced.
- The decision layer's conditional contribution is measured through a frozen ablation.
- Hard regimes and low-human-false-positive operation are reported.
- The result, including a null, is routed honestly through the decision table.

### Product

- Another person can install the package and score an artifact through a documented CLI or API.
- Weights, checksums, calibration, policy, and version metadata are available.
- CI and regression fixtures protect the release path.
- A model card, benchmark report, and public demonstration exist.

### Governance

- Every study has a curator roll-up.
- The current public claim is explicit.
- The detailed record and high-level status agree.
- No Phase 2.0 output is being represented as human value inference.

The attention wedge succeeds only if the frozen detector gate clears. The engineering phase can
still close honestly if the detector hypothesis is null, provided the decision instrument and
product evidence are complete and the null materially redirects the program.

---

## 22. Final orientation for the coding agent

The project does not need Abraham to memorize the machinery. It needs the machinery to preserve and
execute his high-level intent.

Operate at two resolutions simultaneously:

- **Internally:** exact identifiers, reproducible methods, hard controls, faithful recreations,
  complete write-through, and aggressive testing.
- **Upward:** theory groups, sub-goal status, surviving mechanisms, dead instruments, engineering
  obligations, public claims, and material decisions.

The central Phase 2.0 question is simple enough to keep visible through all of the detail:

> **Can a validated representation of recoverable decisions add information that the best ordinary
> AI detectors do not have, and can we ship the result as a trustworthy free product without
> destroying the deeper instrument we are actually trying to build?**

Everything in the phase should either help answer that question, make the answer reproducible, or
preserve the path from episode-level decisions toward later process and value inference.
