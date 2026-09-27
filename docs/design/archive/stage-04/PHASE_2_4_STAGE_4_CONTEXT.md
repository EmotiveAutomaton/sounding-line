# Sounding Line Phase 2.4, Stage 4: Context, Appraisal, and Selective Uptake

**Status:** Research-informed coding handoff; experiments not launched by this review.  
**Prepared:** 2026-08-27, after the curator’s verbal walkthrough.  
**Reviewed commit:** `858f83ae2ea8cc607a5d43ae33cc8646a1f1caca`, matching fetched `origin/main`.  
**Suggested destination:** `docs/design/PHASE_2_4_STAGE_4_CONTEXT.md`.  
**Scope:** 18 cards: three integrity cards, fourteen substantive cards across five tracks, and one confirmation card.  
**Runtime target:** One continuous 24-hour local execution window, with no early or daily curator packets and one final packet at completion. Internal checkpoints continue; CPU work is separately capped.  
**Inheritance:** The five living theory files, the Analyst–Curator Epistemic Protocol, the current method shelf, and the Stage 3 audit corrections below.

All repository paths in this handoff are relative to the repository root. Proposed files and commands are implementation requirements, not claims that they already exist. This handoff does not modify the five theory files, count as a sixth theory file, or report new experimental findings.

## 0. Execution instruction

Implement Stage 4 as a continuous 24-hour local run around the questions below, without interim curator review or reporting pauses. Preserve the breadth of the five tracks, but do not recreate the Stage 3 forest or the Ghost Scale V13 program. Run each track’s construction and instrument checks; allow a failed track to close without stopping unrelated work. Reserve fresh data for at most two substantive confirmations. Deliver one integrated curator packet when the run finishes.

This is a local program. Preserve the current GPU job and the curator’s first-gear default. Do not switch to second gear, spend money, use paid APIs, recruit participants, contact authors, or start cloud training under this handoff. Do not introduce agent delegation. Respect existing data and model licenses. A fresh clone does not contain every home-machine weight or cached dataset; check availability before scheduling.

The shorter scope is deliberate. It does **not** retroactively satisfy omitted Stage 3 experiments. In particular, the full trained family-by-policy cross remains an open debt. Do not turn an unrun old card into a completed card by pointing to a smaller new experiment.

Read `CLAUDE.md`, `docs/STATE.md`, the current `FINDINGS.md`, all five theory files and their README, `docs/method/LESSONS.md`, `docs/method/CONTROLS.md`, and `docs/method/NEURAL_ANALOGUES.md` before implementation. Read the standing grind instructions when executing or landing results. Preserve locked preregistrations and `soundingline/locks.py`.

## 1. What the walkthrough changes

### 1.1 Shared machinery supplies constraints, not a recovered biography

The strongest reconstruction of the curator’s proposal is that a reader starts with machinery already capable of producing actions, appraisals, and coherent goals. It uses that machinery to generate plausible processes, then applies large contextual adjustments and target-specific evidence. Expertise supplies additional constraints and makes some adjustments cheap. This is a proposal about efficient, constrained reconstruction; it need not claim that the reader duplicates the maker’s internal state.

Mirror systems could supply one foothold in that process. An observed grasp or a brushstroke can constrain possible actions before higher-order goals are resolved. However, even a precisely observed movement does not uniquely specify its motive. A final artifact usually constrains a family of possible movements rather than supplying a hard record of the exact movement. The physical-trace track therefore separates artifact-only inference from inference given additional process geometry.

### 1.2 Context can change several expectations together

The “artist from the 1400s” example describes a structured contextual adjustment: one fact changes expectations about tools, institutions, audiences, opportunities, and familiar conventions. That is more specific than a generic instruction to take another perspective. The computational question is whether a coherent context model improves several held-out predictions with the same information, and whether contrary individual evidence corrects it.

The group examples do not license one fixed adjustment for every member of a race, gender, culture, or diagnostic group. Stage 4 uses fictional institutions, tools, roles, and commissions with known distributions. Context is an uncertain prior, never a substitute for individual evidence. Lifelong changes in the reader’s own organization remain a separate question; conditioning an unchanged language model does not test durable learning.

### 1.3 Cultural transmission can preserve a goal while replacing its realization

A shared convention can let a later maker elaborate an earlier idea while remaining intelligible to others. This can improve learning and reduce the information needed to infer local choices. It can also make an artifact less diagnostic of one individual because more of its organization belongs to a shared practice.

The new distinction is essential: ease of copying or adoption, useful learning, truth, comprehension of the maker, and alignment with the reader’s interests are different outcomes. Deliberately misleading work can be easy to understand and relay. Clear teaching can also increase a learner’s competence. Neither direction is guaranteed by legibility alone.

### 1.4 Appraisal must remain attached to its owner

Separate the maker’s valuation, the response the maker intends to induce, the reader’s response, and the relevant world state. A propagandist can induce fear without feeling it. A reader can accurately reconstruct that intention without endorsing the claim, adopting the policy, or becoming immune to the emotional presentation.

Here is the useful computational interpretation of the proposed shield: learning why an example was selected can change what that example is evidence for. A frightening case selected to induce fear may be less informative about the prevalence of danger than a randomly sampled case. That is an inference about selection, not a rule that emotional messages are false or that hostile sources never provide useful evidence.

In language-model experiments, “valence” initially means the measured representation or intervention that changes specified positive/negative continuations. Do not silently upgrade that operational handle into experienced feeling, moral value, a stable preference, or a Panksepp system.

### 1.5 Projection and compliance are not the same error

The curator’s examples of seeing one’s own dispositions in others concern self-projection. Stage 3’s response to an explicitly ignorant stranger’s wish is a different observation. It might reflect answer contamination, conversational compliance, task confusion, or a defective parser. Both may be failures to separate roles, but a shared psychological mechanism is unestablished.

Stage 4 first repairs the measurement, then asks whether own preference, an outsider’s preference, an informed source’s evidence, and the target’s record have distinguishable effects.

### 1.6 Goal weights and editing episodes can coexist

A persistent primary intention can coexist with changing weights on professionalism, precision, economy, concealment, or audience response. A discrete edit is not evidence that the underlying goals were binary. Conversely, continuous weights do not imply that every transition is gradual.

Earlier goals can leave dependencies after their explicit markers disappear. Complete removal can also leave no identifying trace. An odd residual decision is evidence requiring rivals, not a unique diagnosis of a hidden goal. Credit for upstream organization, causal influence on later decisions, and artifact-only historical identifiability must be scored separately.

## 2. Research that changes the design

The access descriptions below distinguish reading an abstract from examining methods. Published human findings inform constructions; none is a Sounding Line result.

| Research | What was inspected and what it supports | Design consequence and limit |
|---|---|---|
| [Caggiano et al., 2012][R01] | Author-institution abstract: macaque F5 mirror responses were modulated by the value the observer associated with the grasped object. | Action observation and observer valuation can interact. This does not show that observing an action transfers the actor’s valuation. Cross actor and observer variables. |
| [Catmur, Walsh, and Heyes, 2007][R02] | Author-institution abstract: incompatible sensorimotor training reversed a muscle-specific TMS mirroring effect. | Learned mappings matter. Do not treat the proposed bootstrap as wholly fixed or innate; the human measure was not a direct recording of individual mirror neurons. |
| [Krishnan et al., 2016][R03] | Article abstract, rationale, and reported multivariate comparisons: somatic and vicarious pain had distinguishable predictive patterns. | Successful understanding need not require identical representations of self and other. This does not prove the absence of shared neural components. |
| [Ames, 2004][R04] | Author PDF, model and study descriptions: perceived similarity moderated projection and stereotyping in group-prevalence judgments. | Treat self-based and category-based proposals as alternatives that can both be wrong. These studies do not establish accurate artifact reconstruction. |
| [Zhou, Majka, and Epley, 2017; Eyal, Steffel, and Epley, 2018][R05] | Author-posted abstracts: seeing the pictures a target saw improved emotion prediction over reading facial expressions; merely being instructed to take perspective did not consistently improve accuracy across another series. | Experiencing relevant input and imagining a perspective are not equivalent manipulations. The former also supplies different information; do not label it an information-matched proof of a privileged self route. |
| [Kirby, Cornish, and Smith, 2008][R06] | Original-paper abstract on an author-uploaded record: iterated learning produced increasingly learnable, structured artificial languages. | Shared structure can arise through transmission without one director designing it. This is a language experiment, not evidence that every artwork or meme is well taught. |
| [Roozenbeek et al., 2022][R07] | Author-institution abstract: preregistered studies reported benefits from short training about manipulation techniques, including recognition and sharing judgments. | Technique training is worth testing. Do not generalize to immunity from bias, professional propagandists, or every intervention format. |
| [Seabrooke, Modirrousta-Galian, and Higham, 2026][R08] | Full article, including the counterbalanced design and ROC analysis: no overall discrimination gain; a response-bias shift appeared only in one exploratory subset, with weak evidence. | Measure discrimination and response criterion separately and counterbalance items. This is not a direct refutation of every inoculation result. |
| [Clay, Leadholm, and Hawkins, 2024][R09] | Thousand Brains Project white paper, abstract and architecture sections. | Reference frames are an engineering hypothesis worth isolating. The white paper is not an established biological theory of mind; do not adopt the entire architecture as a prerequisite. |
| [Quick, Draw! documentation][R10]; [ScholaWrite][R11] | Official drawing schema/license; ScholaWrite paper and existing repository extraction audit. | Drawings have recorded stroke sequences but no supplied writer identity. Writing labels and spans are annotations, not direct measurements of continuously active goals. |

*Table: the literature changes variables, controls, and claim limits. It does not supply an empirical verdict on the project’s unifying theory.*

The research supports testing an interaction between action constraints, contextual correction, and appraisal. It does not warrant a fixed serial brain pipeline. Nor does high transmissibility establish deception, soullessness, or a desire for power. Those interpretations need independent goal evidence and ordinary rivals such as accessibility, craft, genre, and institutional constraint.

## 3. Stage 3: the starting record, with corrections

### 3.1 What remains useful

Related model readers retain an advantage on original artifacts in the audited family comparisons. The strongest independent rewriting condition substantially attenuates the advantage, with high attrition. The live question is what shared organization or convention supports recovery, not whether a family fingerprint alone proves empathy.

Stage 3 also established a selective local positive/negative continuation steering handle in the tested Qwen model. It did not establish that the same handle helps predict another maker. That missing bridge is a primary Stage 4 target.

Context and stated preferences strongly affected the recorded model answers. The magnitude justifies a careful repair and rerun. Missing raw generations and a phrase-based parser prevent treating that number as a clean measure of belief adoption.

Human process records remain valuable, provided their actual sequence structure and annotation grain govern the question. ScholaWrite’s local label persistence is not yet a calibrated measure of governing-goal persistence.

### 3.2 Mandatory audit dispositions

| Stage 3 item | Required disposition before reuse |
|---|---|
| S01/S05/S07 family contrasts | Recompute with equal, declared averaging over eligible own-family readers. Existing dictionaries overwrite repeated reader entries. Preserve old outputs and publish versioned corrected results. |
| S05 independent eraser | Carry `S/S05/eraser3.json`: 88 kept, 162 dropped; reported Qwen and Smol margins near zero. Report matched-survivor comparisons and attrition; do not retain the blanket “survives independent rewriting” headline. |
| S07 reserve | A later hash split of previously analyzed observations is retrospective robustness, not untouched confirmation. All Stage 4 confirmations require new source lineages. |
| S02 trained policies | Training and enactment checks did not implement the promised crossed maker–reader matrix. Keep that debt open. Adapter config files do not prove that weight files are locally available. |
| E01 and E03 | Failed frame realization does not establish a shifted self profile. The two-draw agreement statistic is repeatability, not a demonstrated predictive ceiling. No prospective self advantage was established by E03. |
| A07 | The implemented outcome was the reader’s own next impulse, not held-out prediction of a maker. It cannot close the promised affect-to-inversion card. Analyze per-action defaults; pooled movement hid substantial imbalance. |
| C05, C06, XV3 | Recall is not proof of functional evidence use. Save raw generations in the rerun. Separate own preference from an ignorant outsider’s wish, and parser failure from model choice. |
| L trunk and XV4 | The carrier headline failed the measured cheap scalar/matching adversary on a tiny held-out set. Do not assign the full null to uptake after a supposedly proven nontrivial carrier. No new broad subliminal-learning sweep in this Stage. |
| H04 CoAuthor | Dismissing a displayed set of five suggestions is not rejecting its first suggestion as an individually evaluated alternative. The AUC near chance does not demonstrate indiscriminate human acceptance. |
| H05/H06 | ScholaWrite keystroke labels have persistence and annotation spans. ArgRewrite spreadsheet order is not a recovered chronological edit stream. Do not compare the two as equivalent next-intention tasks. |
| Completion record | The previous validator checked records/status more than the promised construction. Validate expected cells, realized samples, inputs, and held-out status this time. Historical omissions stay visible. |

*Table: these corrections constrain interpretations and reuse. They do not imply that the runs were fabricated or that every underlying effect vanished.*

Primary audit pointers: `runners/s3_run_s.py`, `runners/s3_run_a.py`, `runners/s3_run_c.py`, `runners/s3_run_h.py`, `runners/s3_run_x.py`, `runners/s3_lib.py`, `soundingline/s3.py`, and `results/phase_2_4_stage_3/`. Particularly relevant outputs are `S/S05/eraser3.json`, `E/E03/verdict.json`, `A/A07/verdict.json`, `C/C06/verdict.json`, `X/XV3_verdict.json`, and `X/XV4_verdict.json` under that results root.

## 4. Two ledgers, before any new run

| Track | Pursuit status and opportunity | Present warrant and strongest rival |
|---|---|---|
| Contextual adjustment | `OPENED`: use coherent contextual knowledge to initialize and correct several predictions efficiently. | Human analogue evidence; no new artifact result. Mere instruction following, added information, or a stereotype can imitate adjustment. |
| Appraisal during inversion | `PROMISING` for the existing intervention handle; `OPENED` for its use in other-prediction. | Mechanism candidate for specified continuation behavior only. Generic answer bias can imitate useful appraisal. |
| Transmission and uptake | `OPENED`: explain how understanding can facilitate learning while permitting rejection. | Human analogues and observed model susceptibility. Better copying, blanket distrust, and compliance are live alternatives. |
| Relays and edits | `OPENED`: distinguish inherited organization, local elaboration, and residual dependencies. | Limited controlled and corpus evidence. Shared conventions, weak enactment, and annotation runs can explain apparent hierarchy. |
| Physical traces | `OPENED`: measure what action information survives in a final artifact. | No Sounding Line result yet. Shape/category priors and supplied process information may explain all recoverability. |

*Table: pursuit determines where to spend the short budget; warrant determines what can be said afterward. No track starts with confirmatory support for human empathy.*

## 5. Runtime and review contract

### 5.1 Use the actual record, not the old forecast

The fetched Stage 3 manifest contains 73 cells. Summing `actual_gpu_minutes` gives **30.6848 hours**, against **140.9636 forecast hours**. These are runner-recorded durations, not independently verified GPU-busy time or elapsed calendar duration. The curator’s revised instruction is a full **24-hour continuous run**, superseding the earlier fractional-runtime target.

After implementation and input preflight are ready, record the execution start and a deadline exactly 24 elapsed hours later. Start the timer with the discarded pilot. Calibration, repairs, model loading, scoring, and ordinary scheduling overhead fall inside that window. Keep useful admitted work queued throughout; do not pause for curator feedback or split the allocation across separate sessions. A restart retains the original deadline rather than resetting the clock.

Record elapsed wall time and GPU-lock-held time separately. The 24-hour deadline includes lock waits and interruptions; GPU-run accounting excludes lock waits and includes loading, calibration, generation, and scoring. Report any lost time rather than treating 24 elapsed hours as proof of 24 hours of GPU activity. CUDA timings/utilization and CPU time remain separate measurements.

| Allocation | Execution-window hours reserved |
|---|---:|
| Integrity, discarded calibration, and readout gates | 1.50 |
| Context track | 3.50 |
| Appraisal track | 5.00 |
| Transmission/uptake track | 4.50 |
| Relay/edit track | 2.50 |
| Fresh confirmation, validation, and closure | 4.00 |
| Repair allowance | 1.50 |
| Contingency or frozen sample expansion | 1.50 |
| **Total continuous execution window** | **24.00** |

*Table: these allocations partition the 24-hour run; they are planning allowances, not measured runtime promises. Protect the final four hours for confirmation and closure. The physical-trace track is CPU-only and may run alongside GPU work.*

Use at most two modest-priority CPU workers for this Stage, leaving Ghost Scale’s ongoing program undisturbed. Cap the physical-trace scout at two CPU-hours, including extraction and fitting. Other CPU analysis may use four additional CPU-hours total. Do not interpret these allowances as a requirement to occupy every minute.

### 5.2 Pilot, freeze, then run

Use a discarded pilot of representative short generation, batched likelihood scoring, and intervention passes on the actual machine. Do not select a design by which pilot condition “wins.” Use the pilot to measure throughput, validity, memory, and nuisance variance only. Freeze models, sample tiers, primary contrasts, interventions, parser, and split manifests before discovery scoring.

Two initial readers are `Qwen/Qwen2.5-1.5B-Instruct` and `HuggingFaceTB/SmolLM2-1.7B-Instruct`, pinned to revisions and tested through the same interface. Use existing weights and wrappers. Load one GPU model at a time and calibrate batching to the local memory limit. No migration to a different framework, broad checkpoint sweep, new vision foundation model, or Monty implementation is part of this Stage.

If both initial readers fail the basic gate after the permitted interface repair, one predeclared escalation to `Qwen/Qwen2.5-3B-Instruct` is allowed if it is locally available and fits the measured budget. This is not a second-family replication. Do not keep escalating until something passes. If only one initial reader passes, run its valid contrasts and report the restricted scope.

If the minimum complete design cannot fit the budget, record the shortfall internally before queuing it and include it in the final packet. Defer a whole lower-priority contrast, not some inconvenient cells, and label the program `PARTIAL_BUDGET`. The order for preserving GPU work is: integrity, C01/C02, A01/A02, T01/T02, fresh confirmation, then the remaining GPU contrasts. H03 and the CPU physical scout remain independent. All five tracks still receive their cheap feasibility check. No omission counts as a valid null or successful completion.

Use the pilot to select complete sample tiers and predeclare enough useful expansion work to occupy the full window. If the machine is faster, continue through the frozen expansion ladder: more independent worlds, then harder context conflicts, then a second rendering family. Finishing the minimum card inventory is not permission to finish the run early. Expansion depends on throughput and predeclared coverage, not on searching until a favorable p-value appears. Freeze each expanded contrast before scoring it and keep confirmation sources untouched.

Do not duplicate rollouts, lengthen output for its own sake, sleep, or repeat saturated tests to manufacture duration. Only a safety/access/hardware failure or genuine exhaustion of all admitted work and its useful expansion ladder may force a shorter run. Record that exception as `SHORT_RUN`, with elapsed time and the reason; it does not satisfy the 24-hour execution contract. Routine branch failure must send the scheduler to other admitted work.

### 5.3 One final packet; internal checkpoints only

Do not create or send early curator packets, daily delta packets, milestone summaries, or a preliminary theory assessment. Continue the run without requesting routine curator decisions. Keep internal logs, result receipts, coverage updates, and resumable checkpoints throughout; these are execution records, not interim curator deliverables. A surprising result does not itself justify interrupting the run or opening the confirmation reserve.

Begin the reserved confirmation-and-closure block no later than elapsed hour 20. At the 24-hour deadline, stop admitting new experiments, checkpoint any unfinished work safely, validate coverage, and produce the single `CURATOR_PACKET_FINAL.md`, including incomplete or deferred cells. Report the actual execution duration and compute used. Final report assembly may follow the experiment deadline but does not authorize further experiments. If an exceptional halt requires safety action or missing authorization, give only the necessary blocker notice, not an early results packet.

The final packet starts with the world-model change, then pursuit and warrant, then any unresolved theory question. Put numerical audit details afterward. All curator-facing scientific reporting waits for this packet. This final-only policy overrides routine interim chat-report requirements; internal findings, required repository write-through, evidence, and provenance recording must not wait.

## 6. Shared construction and scoring rules

### 6.1 Ground truth and information access

Retain four separate products: reader-enactable reconstruction, historical correspondence, held-out prediction, and later preference inference. A method may improve one without improving another.

Keep the primary goal inside the joint reconstruction target. Construction code may know it, but the ordinary reader must infer it where the task requires that inference. Mark oracle-goal conditions separately and report goal recovery apart from process or continuation recovery.

Use two data grades. A **known-process ruler** has explicit policies, opportunity sets, and recorded choices, with an exact reference likelihood. An **enacted model case** records what a model actually chose under a construction. An assigned instruction is not proof of enactment. Do not call an oracle policy a language model’s discovered value system.

For a stochastic target, predict either the next recorded draw or its independently estimated choice distribution. Name which is primary. A posterior mode computed by the analyst is not an observed future choice. Do not replace individual decisions with a majority-vote label after inspecting the result.

Every record declares what the reader received: final artifact only; artifact plus factual context; unordered process geometry; ordered history; or an oracle latent. Never pool these access levels. An oracle bypass can diagnose a downstream mechanism after an upstream failure, but cannot rescue the end-to-end claim.

### 6.2 Units and sample floors

For C, A, and T discovery cards, the default minimum is **64 independent base worlds per domain, in two domains**, distributed across three construction seeds. A world includes its whole matched set of contexts, prompts, messages, or interventions. Conditions are paired observations, not additional independent samples. Parameter draws, source texts, and held-out target choices must be genuinely new; recycling a short scenario bank with new row IDs does not meet the floor.

Use 128 worlds per domain if the frozen pilot permits. For H01/H02, use at least 48 independent chains or edit histories per domain, also across three construction seeds. Track-specific human and drawing floors are stated on those cards. The full condition crossing is mandatory within an admitted contrast. Never implement only the easy diagonal of a factorial.

At least two distinct task domains are required for a cross-domain claim. Existing `infra` and publication-oriented utilities can supply reference constructors, but generate new parameters, cases, and held-out decision situations. All paraphrases, edits, hops, and reader variants derived from one world remain in its split and statistical cluster.

These floors support discovery of substantial effects, not an automatic precise null. Before confirmation, calculate interval precision or power for the frozen smallest effect of interest. If the available sample cannot exclude a useful effect, use `INCONCLUSIVE`, not “no mechanism.”

### 6.3 Reader and construction gates

Use a separate set of at least 48 easy known-answer items per reader and domain. Require at least 95% valid structured answers, at least 75% accuracy on unambiguous record-supported choices, and no option below 50% on a balanced four-choice gate. On paired position/paraphrase controls, an absolute accuracy swing above ten percentage points requires repair or explicit restriction of the claim. These are pragmatic instrument thresholds, frozen before substantive results.

The substantive set must include both easy and difficult cases. A ceiling gate does not make a ceiling experiment informative. Record the main-set baseline distribution, balanced action rates, and dynamic range. A model failing the basic reader gate can still yield a useful failure report, but cannot support a null about sophisticated contextual or empathic inference.

For generated constructions, mechanically verify every required feature and report realization per factorial cell. A required cell below 80% realization cannot support its intended contrast. Fix at most once using a discarded calibration lineage. Cap attempts at twice the intended sample count; do not search indefinitely for the rare outputs that instantiate a preferred theory. Keep all attempted cases and the reasons for exclusion.

### 6.4 Readout repair

Use normalized likelihoods over balanced candidate labels as the primary readout where available. Randomize option order and verify tokenization. Cross-check a stratified subset with a strict generated answer such as `{"choice":"B"}`. Store the entire raw response, token IDs/logits used, parser version, validity reason, prompt, and model revision.

The parser must reject ambiguous or multiple answers, not count the first appearance of an option phrase. Unit-test negation, quotation, embedded examples, abstention, malformed JSON, repeated labels, and an explanation that mentions the wrong option before selecting the right one. Keep the old phrase extractor only as a labeled historical diagnostic. No new claim may depend solely on it.

On generation outcomes, report all-attempt accuracy with invalid responses counted as failures, alongside conditional accuracy and yield. Do not silently drop invalid answers in the condition that performs poorly. For each factorial cell, report attempted, realized, retained, and scored counts, not just a pooled yield.

### 6.5 Estimands and controls

Use proper log score or Brier score for distributions, balanced accuracy for categorical choice, and calibration/abstention where informative. Report per-reader, per-domain, and conditional effects before pooling. Own/other family averaging must follow the same eligible-reader rule on both sides.

Keep information, token allowance, and number of model passes matched when comparing inference strategies. A two-pass maker-model route needs a two-pass factual-summary control. Cheap baselines include the population prior, own-choice prior, direct conditional reading, a simple utility or count model where appropriate, and surface/position features.

The population prior must cover the same admissible maker population and task constraints, not an artificially broad universe of arbitrary architectures. Shared human constraints remain part of the overarching hypothesis; these model experiments test limited analogues and cannot quantify that entire advantage.

Each gate-bearing runner carries a `DESIGN CHECK`: question, lessons consulted, expectation under the null, expectation under the proposed alternative, failure direction, and exhaustive result bands. Valid-null, failed-instrument, missing-data, and budget-deferred outcomes are different states.

## 7. The 18 study cards

### I01. Preserve and correct the starting record

**Question.** Which Stage 3 claims are safe inputs to the new program?

Create a versioned audit receipt covering every row in §3.2. Reproduce the manifest duration sum. Recompute the family aggregates from case-level data with matched eligibility and survivor accounting. Verify which outputs contain raw generated text. Inventory local weights, adapters, datasets, and licenses without downloading a replacement simply because a config exists.

**Controls and output.** Keep old result bytes and checksums unchanged. Store new analyses under Stage 4, with links to original outputs and an explicit corrected-versus-original comparison. The legacy completion validator is not a design-compliance certificate. Do not overwrite its output just to inspect it.

**Closure.** Numerical corrections can land as audit findings. Unrecoverable raw generations remain an acknowledged limitation; do not reconstruct them from labels or invent a retrospective semantic audit. This card is CPU-only apart from no required model work.

### I02. Establish that the reader and parser answer the intended question

**Question.** Can the instrument separate evidence, the target’s preference, the reader’s own preference, and an uninformed outsider’s wish?

Run §6.3 gates and the parser fixtures. Include four balanced roles: target, reader, informed witness, and explicitly uninformed bystander. Give the same option phrase in an affirmative recommendation, a negation, a quotation, and irrelevant background. Include unanimous and mixed records, with target-policy labels independent of answer positions. Cross generated and likelihood readouts on the fixed audit subset.

**Primary result.** Report role-specific prediction changes after parser validity is established. A response change is initially a behavioral observation, not a belief-state finding. Compare own-preference intrusion with outsider-wish intrusion directly rather than calling them both projection.

**Closure.** At most one interface repair per reader, selected on calibration data. If both readers fail, do not run a large trust or context battery whose nulls require competent reading. Continue the CPU tracks and independently valid appraisal diagnostics; return the instrument failure as a substantive engineering result.

### I03. Freeze the workload and provenance

**Question.** Can the planned comparisons fit the short budget without dropping essential cells?

Create the expected-cell manifest, discarded pilot set, discovery set, and reserved confirmation lineage allocator before scoring. Time representative passes under the actual GPU lock. Select complete sample tiers using throughput and precision, not observed treatment effects. Record the exact minimum counts and all dependencies.

**Required output.** A frozen `RUN_CONTRACT.json` with the continuous 24-hour window, persisted start/deadline, final-only packet policy, cell IDs, model revisions, source lineage IDs, primary contrasts, gates, sample sizes, random seeds, and output paths. Changing a substantive definition requires a new version and resets its confirmation eligibility.

**Closure.** If scope does not fit, record a named deferred list and `PARTIAL_BUDGET` for the final report; do not silently reduce domains, conditions, or independent units. A fast run advances through the frozen expansion ladder rather than ending when the minimum inventory is complete. Exceptional short runs follow §5.2.

### C01. A coherent context model versus the same facts

**Question.** Does organizing contextual facts into a maker model improve several new predictions beyond merely supplying those facts?

Build fictional commissions with known tools, constraints, training opportunities, and audience demands. Context changes multiple correlated possibilities but does not deterministically identify one value profile. Use the same world in five conditions: no context; a correct coherent context bundle; the same facts listed without the organizing account; an incorrect bundle; and accurate but irrelevant background. Match the two informative representations for factual content, token allowance, and passes.

Predict the maker’s held-out choice, a feasible next process step, and one unrelated attribute as a negative control. The primary contrast is coherent bundle versus information-matched facts on future choice. Context versus no context is an information-access comparison and must be labeled separately. Score same-context and context-mismatched targets separately.

For the information-matched contrast, both presentations must contain the same atomic facts and dependency rules, checked against one stored constraint graph. An explanatory bundle that adds unstated causal facts is not an equal-information control. Treat a familiar label that brings additional pretrained knowledge as an information-bearing cue and report that comparison separately.

**Rivals.** Extra information, flattering or authoritative framing, direct copying of a named goal, and an indiscriminate change of every answer. Counterbalance fictional labels and hold out combinations of constraints, not just new names for the same template.

**Closure.** A benefit only over no context establishes useful context access, not a superior adjustment mechanism. Equal performance to the factual list is compatible with the curator’s practical account, but provides no special advantage for the proposed organization. Incorrect context must have a measured cost.

### C02. Let individual evidence correct the contextual prior

**Question.** Can a reader use a contextual prior without remaining trapped by it?

Cross a valid, misleading, or uninformative contextual prior with 0, 2, and 6 diagnostic target records. Include ordinary members of the constructed context and deliberate exceptions. In separate controls, change an actual current constraint while keeping the maker’s preference stable: a reader should not blindly prefer old records when the available actions genuinely change.

Record predictions before context, after context, and after records. Balance whether self preference, the contextual default, and the target’s supported policy agree. Compare direct reading, self-initialized adjustment, and an equally expensive factual-summary route. In coded ruler cases, compute the reference posterior using the stated reliability of each channel; do not assume every record automatically outranks every context fact.

Measure the reader’s own-choice profile on disjoint calibration probes before showing target evidence. Supply that same profile and the same target facts to all strategy routes; the self-initialized route explicitly uses it as its starting distribution. This isolates a routing proposal, not privileged access to extra self data. It does not establish that a self prior is uniquely better than an equally informative non-self prior.

**Primary result.** The correction curve on misleading-context cases, with valid-context benefit retained. Report calibration, target-specific log-score gain, and separate own-preference and category-prior errors. An overall mean must not cancel a benefit for similar targets against harm for unlike ones.

**Closure.** If the route merely moves from one dominant prompt cue to another, keep the result at instruction sensitivity. If both accurate context and individuating evidence are used selectively, the model-side adjustment mechanism earns promotion consideration.

### C03. Choose the contextual question that would help

**Question.** Does the reader’s attention go to a difference that can actually resolve uncertainty?

Offer three possible questions about the maker’s constraints or prior choices. Using the existing known-policy ruler, construct one informative probe, one redundant probe, and one irrelevant probe. Equalize response length and cost. Require the informative probe’s expected improvement in the declared future-choice score to exceed the redundant probe by a frozen margin; a flat menu is an instrument failure, not a failure of active reading.

Randomize positions and wording. Compare the reader’s selection with random choice, first-listed choice, and an exact one-step selector. Then supply the selected answer and measure actual improvement in the held-out prediction. Keep the query-selection score separate from the ability to use the answer.

**Primary result.** Fraction of available oracle improvement captured under the same evidence budget, with position effects reported. This is an operational attention allocation test, not a claim about transformer attention weights or a biological precision signal.

**Closure.** One construction repair if probe discrimination is weak. If useful probes exist but selection fails, report that failure without cancelling C01/C02. No new general active-inference simulator is required.

### A01. Separate observed action, maker appraisal, and intended audience response

**Question.** Can the reader distinguish what happened, how the maker evaluated it, and what the maker wanted another person to feel or do?

Construct paired cases with the same observed action but different stakes or revealed preferences. Separately vary the maker’s communicative aim. Include a maker who selects a fear-inducing example without having the threatened preference, and a worried maker who communicates reassuringly. Ground the operational appraisal in the constructed tradeoffs and recorded choices, not merely the presence of an emotion word.

Ask distinct questions about observed action, target valuation, intended audience action, and relevant factual state. Hold answer frequencies and surface emotional language balanced. Include withheld context where the correct conclusion is uncertainty. Use both a known-process ruler and enacted model cases that pass realization.

**Primary result.** Crossed recovery of target appraisal and communicative aim, with appropriate uncertainty when the action alone is ambiguous. No success claim may come from answering only “is this text negative?”

**Closure.** If the targets cannot be independently manipulated or the reader cannot separate them on easy cases, stop the corresponding other-prediction intervention claim. A validated valence continuation handle can remain an instrument finding independently.

### A02. Does the existing valence handle help predict another maker?

**Question.** Does changing a reader representation improve target-specific prediction, or just change the reader’s preferred answer?

Reproduce the narrow A02 Stage 3 handle on calibration material disjoint from the new target corpus: pinned model, fitted direction, layers, norm-scaled dose, and neutral/factual tolerances. Calibrate each model independently; do not transplant a vector across different residual spaces. Do not search the full network for whichever setting wins the new task.

On A01’s admitted worlds, predict fresh target choices under zero intervention, positive and negative intervention, a norm-matched random direction, and a shuffled-label fitted direction. Use low and high evidence doses. Balance the target’s appraisal against the final correct action, rotate option labels, and remove affective words from answer labels. Separately measure the reader’s own choice on matched situations without a target.

**Primary result.** A target-appraisal-by-intervention interaction in proper future-choice score that survives within-correct-action comparisons. An intervention that always favors approach, caution, or a particular label has not shown improved inversion. Report both matched and mismatched targets; do not count the average movement in the expected emotional direction as the endpoint.

**Safety and validity.** Retain neutral-task accuracy and general likelihood controls. A direction that damages ordinary comprehension is not evidence of a selective empathy mechanism. This is a causal intervention on a model representation, not evidence of felt affect.

**Closure.** A selective target-prediction gain with controls intact is a promotion candidate. Own-action movement without other-prediction benefit leaves the bridge unbuilt. A failed manipulation is `INSTRUMENT_FAILED`, not a null on the bridge.

### A03. Reading the target versus biasing the answer

**Question.** Does any A02 gain arise while processing target evidence rather than at the response interface?

If A02’s handle passes, compare a controlled intervention at a target-context summary position with intervention at the answer position. Match the number of perturbed positions and norm budget for the primary phase contrast. Include a matched neutral-context position. Record exact layers, token positions, and whether cached keys/values were recomputed. On a tiny fixture, verify the cached implementation against a full replay.

Retain target prediction, the reader’s own choice, and factual recall as separate outputs. If an apparent reading benefit disappears after matching correct-action frequencies or is reproduced by answer-only steering, generic response bias remains sufficient. A retrospective probe of internal states is secondary; it cannot substitute for the behavior.

**Closure.** Run only after manipulation validity, not only after a significant discovery effect. Otherwise label this card `BLOCKED_DEPENDENCY`. Even a selective phase effect identifies an intervention-sensitive computation in this model, not mirror neurons or the uniquely necessary biological route.

### T01. Transmission, learning, reconstruction, and uptake

**Question.** Can a message become easier to transmit without becoming more truthful or more helpful?

Create small fictional decision lessons with ground-truth rules and payoffs. Independently vary claim truth, alignment of the source’s recommended action with the recipient’s payoff, and comprehension support. Include true but strategically selective messages, honest mistakes, helpful clear messages, and misleading clear messages. Do not make all deceptive cases ornate and all honest cases plain.

Store the source’s information and belief state as well as the world’s true state. A false claim by a mistaken source and a knowingly false claim are different constructions. A label such as “deceptive” cannot be assigned merely because the recommendation was wrong.

Use a balanced set of messages with the same relevant factual payload within the support contrast. Verify that the support manipulation actually changes comprehension or relay performance before attributing an effect to transmissibility. Score four distinct outcomes: fidelity after a one-hop relay; correct application to a novel case; recovery of the source’s decision or goal; and the recipient’s later action/payoff. A copied slogan is not a passed transfer test.

**Primary result.** The comprehension-support effect on novel-case learning, reported alongside relay fidelity and recipient benefit. The key dissociation is whether transmission improves under both aligned and misaligned source goals. A failure to dissociate is informative too; do not plant success in the verdict rule.

**Closure.** If the reader can only repeat the lesson, report copying. If source modeling adds no benefit over an information-matched direct route, do not claim it was necessary for learning. That restriction applies to this task family, not every form of cultural learning.

### T02. Does modeling the source’s selection rule improve judgment?

**Question.** Can a reader understand an attempt to influence it without either obeying it or rejecting everything?

Reuse T01 worlds with a known rule for how evidence was selected: representative sampling, selection for a recipient’s benefit, or selection to induce a particular action. Keep source intention distinct from factual truth and from the value of the recommendation in the current case. Sometimes a source with a conflicting goal provides a true and useful fact.

Include visible versus hidden source opportunity sets. If the reader cannot know which alternatives the source could have selected, posterior uncertainty about the selection rule should increase. Do not reward confident intention assignment where the available observations do not distinguish the candidate sources.

Compare direct judgment, generic caution, a two-pass factual summary, and a two-pass source-goal/selection reconstruction. Give routes the same observations and compute allowance. The reconstruction step must infer the selection rule from source records; the analyst must not secretly supply the correct intention to only one route. An oracle-intention arm is a separately marked ceiling diagnostic.

**Primary result.** Better calibrated judgments and recipient payoff conditional on the available evidence, without indiscriminate loss of useful uptake. Report accuracy of source-goal reconstruction separately from its downstream effect. Merely labeling more messages manipulative is not success.

**Closure.** If an oracle selection model helps but the inferred one does not, the unresolved problem is source inference. If both help only because they receive extra facts, the comparison is void as a mechanism test. Preserve this distinction in the packet.

### T03. Technique knowledge versus blanket distrust

**Question.** Does a brief lesson about manipulation generalize to unseen cases while preserving discrimination?

Give readers an in-context lesson on evidence selection, emotionally loaded framing, or misleading omission, with matched-length control instruction. Compare this with T02’s inferred source-model route. Hold out an entire technique family or rendering family for transfer. No real political targeting, personal profiling, or live persuasion campaign is involved; use the fictional decision worlds.

Cross true/false factual claims with helpful/harmful recommendations, including truthful emotional messages and misleading dry messages. Score factual reliability and action value separately. Report AUROC or another threshold-independent discrimination measure, Brier score, and the response criterion/acceptance rate. Track false acceptance and false rejection explicitly. Preregister a maximum acceptable loss on useful true advice, default three percentage points, and report its confidence interval; wide uncertainty is not noninferiority.

**Primary result.** Improvement in discrimination or proper score under held-out transfer, with the useful-advice tolerance satisfied. Reduced acceptance of every message is a criterion shift, not the proposed protective mechanism.

**Closure.** Name the result as in-context model behavior. It is not durable media literacy, immunity, or evidence that knowing bias terminology protects people generally. A valid null does not contradict every human inoculation study.

### H01. Shared conventions and goals through a relay

**Question.** What survives when another maker elaborates an idea: an upstream constraint, a local preference, a shared convention, or only wording?

Start with a mechanically verified primary constraint and a separately measurable local elaboration. Use one- and three-hop relays, with stable shared conventions versus remapped conventions. Match available information and token budgets. Verify hop-zero realization before interpreting a decay curve. Generate genuinely enacted choices at each hop rather than only asking models to repeat the stated goal.

Measure retention of the upstream constraint, the later maker’s local contribution, and prediction of a held-out downstream choice. Record causal reach by paired intervention on the initial constraint while holding the remaining construction fixed. Reuse T01 artifacts where suitable, keeping one shared lineage ID so their tests are not treated as independent replications.

**Required rival.** A shared brief specifying the same dependency rule must accompany any central-director construction. Identical observable outputs cannot identify the controller. Role history may improve attribution in a separately labeled information-rich condition.

**Closure.** Recovering a dependency supports an organizing-constraint claim. It does not establish one original author or settle how credit should be allocated. Failure at hop zero voids the relay interpretation, not the existence of cultural transmission.

### H02. Continuous goal weights and traces after editing

**Question.** Can a revision conceal one goal while retaining dependencies that help reconstruct it?

Extend the existing utility/decision ruler with mixtures of subsidiary goals under a continuing primary constraint. Include five matched histories: stable weights; gradual reweighting; abrupt subsidiary-goal switch; removal of explicit goal markers without changing the governing weights; and a fresh construction from the final weights with no earlier goal. Use actual recorded edits or mechanically validated model edits, not a retrospective narrative about what the maker must have thought.

Score prediction of later decisions and a calibrated posterior over earlier goal weights. Evaluate continuous weight recovery separately from labels for edit events. Keep goal strength, role, rank, and causal reach as distinct fields; a large coefficient is not automatically an upstream goal.

Normalize relative policy weights in the ruler and either fix or explicitly model choice temperature and competence. Do not claim that absolute preference strength is identifiable when a change in scale or decision noise produces the same choices. Use varied opportunity sets to make relative tradeoffs estimable; report uncertainty where they remain aliased.

**Required rivals.** Match length, final goal realization, and superficial anomaly rates. Include benign changes that leave similar unusual dependencies. Include exact final-artifact collisions generated by different histories with balanced labels: the artifact-only reader must remain uncertain, while a reader with the history may distinguish them.

**Closure.** Residual dependence that improves held-out recovery beyond anomaly baselines earns a narrow trace claim. Exact erasure establishes a boundary for that information set. Neither “all edits preserve intention” nor “every erased goal leaves a detectable residue” is licensed.

### H03. Human writing episodes beyond label persistence

**Question.** Does the human process record support useful prediction after accounting for annotation spans and same-label runs?

Audit ScholaWrite’s timestamps, project/author fields, and annotation units. Use leave-one-project-out evaluation across the available five projects; disclose author overlap rather than calling the split author-held-out. Fit count/majority, Markov, and duration-aware baselines on training projects only. Use a lightweight existing text/event encoder if it already works; no new large encoder training is required.

Separate two tasks. First, forecast the next event or boundary using only information available so far. Second, predict the next distinct annotated intention given an oracle boundary; this is a conditional diagnostic, not an online forecast. For current intention, distinguish an oracle previous label from a label predicted without access to the held-out annotations. Collapsing runs using future labels must not leak their endpoints into the first task.

Report every held-out project and cluster uncertainty at the project level. Five projects limit generalization regardless of the number of keystrokes. Do not use ArgRewrite row order as a substitute chronological stream. Keep the CoAuthor whole-set rejection correction in the audit rather than launching another badly specified default-acceptance test.

**Closure.** A better prospective score beyond duration and label persistence is a corpus result. Failure identifies the current instrument’s limit. Neither outcome directly establishes a continuous human goal state from categorical annotation.

### P01. Physical information in a final drawing

**Question.** Does a final artifact constrain a recorded action beyond a category-level guess?

Use a bounded Quick, Draw! subset, with attribution and the official CC BY 4.0 data license retained. Preselect four categories before looking at prediction results, for example house, tree, bicycle, and cat. Target at least 500 usable independent drawings per category, with training/discovery/reserve allocation by drawing ID before fitting. Cap total download at 128 MiB and the whole physical scout at two CPU-hours; a capped, nonrandom source prefix must be disclosed as such. If the floors cannot be met, report a data-blocked scout rather than quietly changing categories after seeing effects.

Derive a modest target from the recorded sequence, such as the quadrant containing the first stroke’s starting point. The primary input is a final raster rendered with constant stroke width, using a commutative binary union so overpainting does not leak order. Strip IDs, timestamps, country, recognition flag, stroke ordering, and direction from reader inputs. Keep source metadata only for provenance and split checks. `key_id` is a drawing identifier, not a writer identifier.

Compare a small CPU classifier on image features with category-only, ink-distribution, and simple geometric priors. Split near duplicates together. Test normalization under translation/scale and a rotation sensitivity check with appropriately transformed labels. All preprocessing must use final-image information, not the hidden first stroke.

**Primary result.** Held-out first-action information beyond the cheap priors. This is constrained historical prediction at a coarse grain, not exact reconstruction of the drawing process and not a neural mirror-system experiment.

### P02. What additional process geometry buys

**Question.** How much of the apparent motor bootstrap requires information not recoverable from final pixels alone?

On the same drawings, add two explicitly separate access levels: unordered, direction-stripped stroke geometry; then a genuine observed prefix of the sequence. Compare simple geometry heuristics with a learned ordering/transition prior using the same inputs. Candidate ordering tasks must contain alternatives that produce the same final raster, not merely an obviously wrong shape.

The unordered-stroke condition supplies privileged segmentation and is not artifact-only. The prefix condition is process-assisted. Report the incremental information and performance at each access level rather than treating all three as the same task. In exact-collision controls, pair the same visible input with balanced alternative histories; confident identification should fail unless an informative record is supplied.

**Primary result.** The gain from a learned process prior beyond geometry, conditional on the stated information access. If extra process records explain the entire gain, that is a useful boundary for artifact inversion.

**Closure.** No new multimodal language model, motor simulator, or Thousand Brains implementation. A successful CPU prior supplies an engineering foothold only. A null on these coarse drawing targets does not test whether human motor expertise contributes to appreciating paintings or dances.

### F01. Fresh confirmation of at most two findings

**Question.** Does the strongest controlled discovery survive new sources under a frozen definition?

Before discovery, reserve new source-lineage IDs and generation seeds, not a later subset of already analyzed observations. After discovery, select at most two candidates by §8’s fixed eligibility rule. Freeze the exact contrast, model, intervention, parser, sample size, and stopping rule before generating or opening their confirmation outcomes.

Use at least 128 new worlds per domain for each admitted C/A/T confirmation and an explicit precision calculation. For H or P, retain their natural independent unit and declare the available precision before promoting. At least one severe rival and one negative control must accompany each confirmation. Model-specific intervention calibration may fail independently; do not then report a two-model replication.

**Primary result.** An untouched estimate and interval for the selected primary effect, with the preregistered tests and a correction across the at-most-two selected claims. Reusing readers or code is acceptable; reusing source lineages, inspected outcomes, or fit directions contaminated by the target set is not.

**Closure.** If no discovery is eligible, record that no confirmation was justified and reallocate the allowance to predeclared precision extensions or controlled replications on admitted discovery sources, followed by validation and closure. Do not end the run merely because no confirmation was selected, and do not search the reserve for a winner. Exceptional exhaustion follows §5.2. Even a confirmed result is model- or corpus-bounded, not a confirmed human neural mechanism.

## 8. Promotion, continuation, and closure

### 8.1 Promotion is an allocation decision

Before discovery, select one primary estimand per substantive card. The default smallest effect of practical interest is five percentage points for balanced accuracy or 0.03 nats per choice for log score. These are engineering thresholds, not constants of human cognition. If a task requires a different threshold, justify and freeze it in the contract before outcomes are inspected.

A discovery is eligible for fresh confirmation only if:

1. The intended target was realized, the readout gate passed, and no required control failed.
2. The primary effect reaches the frozen practical threshold in the predicted direction, with its uncertainty reported.
3. The direction is not produced solely by one option, one source template, or one domain. Expected sign changes across similarity or appraisal strata must be analyzed as the preregistered interaction, not averaged away.
4. An information-matched cheap alternative is insufficient, or the finding is explicitly a useful boundary for that alternative.
5. The proposed confirmation can achieve interpretable precision within its reserved allowance.

Order eligible candidates by directness of the theory bridge: A02 target-specific causal prediction; C02 selective correction; T02/T03 selective uptake; H01/H02 historical dependency; P01/P02 action constraints. Use effect magnitude only within this ordering, not as an excuse to select a huge artifact-prone statistic. At most two claims enter F01. A good boundary result may receive the second slot instead of a weak positive.

A positive estimate with a confidence interval above zero supports a directional effect. It does not establish that the effect exceeds the practical threshold unless the interval supports that stronger statement. In particular, do not call true-advice uptake preserved when its noninferiority interval is too wide.

### 8.2 Independent branches must actually remain independent

| If this happens | Continue with | Do not claim |
|---|---|---|
| A language reader fails I02 | Other admitted readers; CPU physical and writing analyses; separately valid intervention calibration | A null on contextual or empathic inference in competent readers |
| The valence intervention fails calibration | C, T, H, P; A01 if readable | A02 tested the causal bridge |
| Target reconstruction fails but oracle uptake works | Report the separated downstream diagnostic | The end-to-end reader learned selectively |
| Relay hop zero fails | H02/H03 and other tracks | A measured decay of inherited intention |
| Human chronology or annotation grain is unusable | A narrower descriptive audit; other tracks | A valid next-goal null |
| Exact artifacts arise from different balanced histories | Test uncertainty and the added-record condition | Artifact-only recovery of the hidden history |
| The 24-hour deadline arrives | Checkpoint, validate what exists, list deferred cells in the final packet | Every planned comparison completed merely because the execution window ended |
| An exceptional halt ends execution before the deadline | Record `SHORT_RUN` and the actual duration | A continuous 24-hour run completed |

*Table: failures close the inference they invalidate, not neighboring scientific questions.*

### 8.3 Results must occupy an explicit outcome class

Store execution state separately from scientific outcome. Execution states are `PLANNED`, `RUNNING`, `COMPLETE`, `FAILED`, `BLOCKED`, and `DEFERRED`. Scientific outcomes are `SUPPORT_CANDIDATE`, `COUNTEREVIDENCE`, `VALID_NULL`, `INCONCLUSIVE`, `HETEROGENEOUS`, `INSTRUMENT_FAILED`, `VOID`, and `NOT_RUN`.

For a valid positive-direction primary contrast, use the frozen effect-size threshold and interval to distinguish support, evidence against, an interval excluding a practically useful benefit, and unresolved precision. Define exact interval boundaries in code; do not leave an unclassified band around a threshold. Planned conditional sign changes are interactions, not automatically heterogeneity. Unplanned domain disagreement must remain visible.

Attach a separate pursuit status and warrant status from the standing protocol. A `COMPLETE` computation can have `INCONCLUSIVE` science. An instrument can be promising while its end-to-end claim remains unsupported.

## 9. Implementation map and machine-readable requirements

### 9.1 Reuse, but do not inherit the defective semantics

| Existing component | Reuse | Change or guard |
|---|---|---|
| `runners/s3_lib.py` | Scenario/utility interfaces, model wrappers, exact small-ruler calculations | New independent worlds; strict readout; distinguish sampled truth from posterior-mode labels |
| `soundingline/gpulock.py` | GPU ownership and serialization | Record lock-held runtime separately from the fixed 24-hour elapsed deadline; preserve the user’s gear and existing job |
| `runners/s3_run_a.py` | Intervention calibration and neutral-task controls | Fit only on calibration sources; target prediction is a new outcome; verify intervention token locations |
| `runners/s3_run_h.py` | Dataset location and extraction starting points | Audit chronology, span grain, grouping, and previous-label leakage before reuse |
| `soundingline/process_record.py` | Recorded alternatives, costs, choices, and provenance concepts | Extend minimally for explicit information access and role ownership; do not duplicate the schema |
| `soundingline/s3.py` and `runners/validate_stage3_program.py` | General manifest and provenance ideas | A new Stage 4 validator must test expected construction, counts, and freshness, not just path existence |

*Table: reuse implementation where it saves work, but make the changed scientific meaning explicit.*

A reasonable implementation is one shared Stage 4 schema/manifest module, one shared runner helper, and track runners for context, appraisal, transmission, hierarchy, and physical traces. Use the repository’s established naming style. Avoid a separate model loader, statistics library, parser, or directory convention for each track.

The proposed output root is `results/phase_2_4_stage_4/`. Required products are:

- `RUN_CONTRACT.json`: frozen design and budget.
- `EXPECTED_CELLS.json`: the fully expanded required factorial, including control cells and independent-unit floors.
- `SOURCE_LINEAGES.json`: source ancestry, splits, fit/calibration use, hashes, and confirmation access record.
- `QUEUE_MANIFEST.json`: execution states, dependencies, budget charged, and reasons for closure or deferral.
- `AUDIT_STAGE3.md` plus machine-readable corrected summaries.
- Per-card `cases.jsonl`, `raw_outputs.jsonl`, `metrics.json`, and `verdict.json`, with source links rather than duplicated corpora where possible.
- `COVERAGE.json`: actual-versus-required counts and every missing or invalid cell.
- `CURATOR_PACKET_FINAL.md`: the only curator packet, delivered after the continuous run; no early or daily packets.
- `CLAIM_LEDGER.json`: estimand, strongest rival, scope, pursuit, warrant, and public wording for every promoted or closed claim.

This compact seed contract fixes the inventory; implementation must expand it rather than treating it as a sufficient validator:

```json
{
  "stage": "phase_2_4_stage_4",
  "reviewed_commit": "858f83ae2ea8cc607a5d43ae33cc8646a1f1caca",
  "run_duration_hours": 24,
  "duration_basis": "elapsed_wall_clock",
  "continuous_run": true,
  "deadline_persists_on_resume": true,
  "gpu_run_budget_hours": 24,
  "curator_packet_policy": "final_only",
  "early_curator_packets": false,
  "daily_curator_packets": false,
  "confirmation_and_closure_start_hour": 20,
  "physical_cpu_budget_hours": 2,
  "other_cpu_budget_hours": 4,
  "max_cpu_workers": 2,
  "max_substantive_confirmations": 2,
  "default_discovery_worlds_per_domain": 64,
  "default_confirmation_worlds_per_domain": 128,
  "default_domains": 2,
  "construction_seeds": 3,
  "cards": [
    "I01", "I02", "I03",
    "C01", "C02", "C03",
    "A01", "A02", "A03",
    "T01", "T02", "T03",
    "H01", "H02", "H03",
    "P01", "P02", "F01"
  ],
  "late_split_of_old_data_is_confirmation": false,
  "oracle_bypass_is_end_to_end_success": false,
  "old_stage3_debts_closed_by_new_scope": false,
  "cloud_or_paid_api_authorized": false
}
```

### 9.2 Row-level provenance

Each scored row records: card and cell ID; independent-unit and parent-lineage IDs; source and split; full model identifier and revision; construction seed; treatment and all crossed factors; attempted/realized/valid status; observed truth and its provenance; available information; raw prompt/output references; candidate-label mapping; parser/readout version; prediction probabilities; primary score; intervention coordinates if any; code/contract hashes; and charged compute.

Do not use shortened model-name prefixes as unique IDs. Do not let overwrite collisions choose the last reader silently. All learned parameters, calibration thresholds, and preprocessing statistics record the source split from which they were fitted.

### 9.3 Verification requirements

Use existing checks first and extend their natural test locations. A new focused test module is justified for the Stage 4 parser/manifest only if there is no suitable existing home. Required meaningful checks are:

1. Parser fixtures catch negation, quotation, ambiguity, malformed output, and label permutations.
2. Expected-cell validation fails when one factorial corner, required domain, or negative control is removed.
3. Sample validation fails when duplicate lineages masquerade as independent units.
4. Split validation fails when a rewritten artifact or later relay hop crosses discovery/confirmation, or when an inspected old source is labeled fresh.
5. Aggregation is invariant to input row order and gives each eligible reader the declared weight.
6. Ground-truth validation rejects an assigned instruction substituted for a realized choice.
7. A downstream gate inspects the prerequisite verdict, not merely its output path.
8. Exact-collision fixtures expose source-ID or metadata leakage; no classifier should identify balanced hidden histories from identical inputs.
9. Intervention tests verify norm scaling, token positions, hook removal, and cached/full replay consistency on a tiny fixture.
10. Elapsed-duration accounting includes waits and interruptions and preserves the original 24-hour deadline across restarts. Separate GPU-run accounting excludes lock waits and includes calibration/repair. Validation rejects a short run labeled as a completed 24-hour run.
11. Reporting guards suppress early, daily, and milestone curator packets while retaining internal checkpoints; only the final packet is emitted.

A completion marker must contain the contract version and required input/output hashes and be checked against the data. Do not rely on an ignored `.produced` file that disappears in a fresh clone. Keep validators read-only by default; writing a report should require an explicit output path.

When using `tools/design_lint.py` or `tools/theory_lint.py`, supply the hook JSON containing the actual file path. They consume stdin; invoking them with no payload can exit successfully without checking anything. Run `tools/verify_locks.py` before any proposed commit. Inspect the actual git diff, including deletion lines, rather than reporting success from a submitted command.

### 9.4 Suggested execution order

Initialize the draft manifest and source allocator and complete implementation/input preflight. Record the execution start and 24-hour deadline when the discarded pilot begins; finish I01/I02/I03 integrity work and freeze the complete contract. Run admitted discovery and frozen expansions continuously without curator-reporting pauses. By elapsed hour 20, freeze and start up to two F01 confirmations and the closure work. At the deadline, stop new experiments, validate coverage, and write the single final packet and claim ledger.

Any implementation CLI should expose equivalent prepare, calibrate, run, validate, and final-packet operations with resumable internal checkpoints. A restart must not reset the deadline. This handoff does not prescribe nonexistent commands as though they were already usable.

## 10. Integration into the five living theory files

No structural reorganization or sixth theory file is requested. The following is the integration map for a later write-through, not an assertion that the edits have already been made. Before editing, reread the theory README, preserve all curator quotations, and update each affected table’s afterword in the same pass. Use existing hypothesis identifiers where they fit; allocate new identifiers only after checking the live registry.

| File | Proposed clarification | Evidence handling |
|---|---|---|
| `THE_TRIPLE_INFERENCE.md` | Keep physical action, goal, current appraisal, intended audience response, and persistent value distinct within joint reconstruction. Add explicit information-access limits and the possibility of useful reconstruction without unique history. | New walkthrough content is a hypothesis; exact collisions are conditional identifiability bounds. Do not label individual intentions or values recovered until the relevant card lands. |
| `READER_HEURISTICS.md` | Extend the self/context/evidence loop with structured contextual adjustment and correction. Split comprehension support, transmissibility, truthful teaching, and selective uptake. Distinguish projection from outsider-preference intrusion. | Attach C/T results to HH-23 and the appropriate bard/trust rows without silently redefining old measurements. Correct the C05/C06 interpretation and misleading reserve wording. |
| `DECISION_TRACES.md` | Represent continuous goal weights alongside discrete edits and role-relative control. Separate causal reach, inherited conventions, explicit markers, and historical residue. | Integrate H/P with access conditions; correct the ArgRewrite chronology and CoAuthor rejection reading. Atypical details remain cues with rivals, not unique diagnoses. |
| `THREE_COGNITIVE_LAYERS.md` | Add the narrow mirror/observer-value interaction as literature context, not a validated layer map. Preserve the functional “ghost” vocabulary and distinguish a valence continuation handle from maker-specific prediction. | Correct A07’s endpoint and the strongest-erasure headline. A02/A03 Stage 4 can add a model-side causal finding only after controls. Do not adjudicate Panksepp versus Barrett from these tasks. |
| `ALIGNMENT.md` | Keep reconstruction, trust, and policy uptake separately evaluated. | No new alignment claim is warranted by this walkthrough or handoff. Add a result only if T actually establishes selective behavior under its stated tests; even then retain the model/task scope. |

*Table: the proposed changes preserve the project’s ontology while sharpening the variables and the evidence attached to them.*

Audit corrections should also update the relevant `FINDINGS.md` entries or append a clearly linked erratum, following the repository’s historical-record convention. Do not erase the original result or its provenance. A landed experimental result follows the complete grind write-through: findings, affected theory table and afterword, instrument ledger if relevant, TODO status, and curator roll-up. The separate handoff itself is not a landing.

## 11. What this Stage deliberately does not do

- No new Ghost Scale version, large constructed-world expansion, or duplication of V13’s cost/trust program.
- No exhaustive family-by-policy adapter training grid. The missing Stage 3 cross remains explicitly open.
- No broad subliminal-transfer rerun, another affect-component count, or an assumption that mixtures must occupy a fixed emotion taxonomy.
- No inference of biological mirror neurons from transformer units, layer numbers, attention maps, or a CPU drawing classifier.
- No “Thousand Brains is correct” prerequisite. Test the contribution of reference-frame information without importing the whole architecture.
- No test of durable human value change, lifetime growth of the self model, or real-world immunity to propaganda. Those require different data and interventions.
- No fixed demographic stereotypes as ground truth and no diagnosis of a real creator’s motives from isolated stylistic details.
- No assumption that clarity, polish, popularity, or audience appeal indicates deception or a single power motive.
- No claim that every edit leaves recoverable residue, that stable annotation labels are stable governing goals, or that identical artifacts identify different hidden controllers.

The public claim ceiling before this program runs is unchanged: there are bounded model-reading effects, a selective valence continuation intervention, consequential context sensitivity with unresolved readout issues, and useful human process datasets. The new synthesis supplies hypotheses and discriminating constructions. It does not establish a unified human empathy mechanism.

## 12. Required final curator packet

Produce this packet once, after the continuous 24-hour run. There are no early or daily curator packets.

Begin with a short plain-language account of what changed in the model of the world. Then give one row per track: what was asked; what was observed; leading explanation; strongest surviving rival; pursuit status; warrant status; and the next useful decision. Put the detailed metrics, implementation failures, and source receipts in an appendix.

Answer these five questions, including “not measured” where necessary:

1. Did contextual adjustment improve new predictions beyond the same facts, and did individual evidence correct a wrong adjustment?
2. Did appraisal steering help predict someone else, or only change the reader’s own answers?
3. Did a message’s transmissibility, usefulness, and source transparency come apart, and did the reader preserve useful uptake while resisting misleading selection?
4. Did relay/edit dependencies identify historical choices beyond conventions, superficial anomalies, and annotation persistence?
5. Did a final physical artifact provide action information beyond cheap shape priors, and how much extra information came from process records?

End with a proposed next action only when the observed result justifies one. Do not automatically prescribe Stage 5. Another verbal walkthrough is warranted only if an outcome forces a theory choice that the present walkthrough did not answer.

<!-- Research links used in section 2. Access levels are recorded in that table. -->

[R01]: https://iris.unime.it/handle/11570/3251500 "Caggiano et al. (2012), Mirror neurons encode the subjective value of an observed action; author-institution abstract"
[R02]: https://kclpure.kcl.ac.uk/portal/en/publications/sensorimotor-learning-configures-the-human-mirror-system/ "Catmur, Walsh, and Heyes (2007), Sensorimotor Learning Configures the Human Mirror System; author-institution abstract"
[R03]: https://pmc.ncbi.nlm.nih.gov/articles/PMC4907690/ "Krishnan et al. (2016), Somatic and vicarious pain are represented by dissociable multivariate brain patterns"
[R04]: https://www.columbia.edu/~da358/publications/ames_strategies.pdf "Ames (2004), Strategies for Social Inference: A Similarity Contingency Model of Projection and Stereotyping in Attribute Prevalence Estimates"
[R05]: https://www.nicholasepley.com/publications "Author-posted abstracts for Zhou, Majka, and Epley (2017) and Eyal, Steffel, and Epley (2018)"
[R06]: https://www.researchgate.net/publication/23138098_Cumulative_cultural_evolution_in_the_laboratory_An_experimental_approach_to_the_origins_of_structure_in_human_language "Kirby, Cornish, and Smith (2008), original-paper abstract on an author-uploaded record; publisher and institutional PDF fetches were unavailable"
[R07]: https://research-information.bris.ac.uk/en/publications/psychological-inoculation-improves-resilience-against-misinformat/ "Roozenbeek et al. (2022), Psychological inoculation improves resilience against misinformation on social media; author-institution abstract"
[R08]: https://link.springer.com/article/10.3758/s13423-025-02827-x "Seabrooke, Modirrousta-Galian, and Higham (2026), Re-examining the Bad News game; published online December 2025"
[R09]: https://arxiv.org/html/2412.18354v1 "Clay, Leadholm, and Hawkins (2024), The Thousand Brains Project: A New Paradigm for Sensorimotor Intelligence; white paper"
[R10]: https://github.com/googlecreativelab/quickdraw-dataset "Google Creative Lab, Quick, Draw! dataset: schema, provenance, and CC BY 4.0 data license"
[R11]: https://arxiv.org/html/2502.02904v5 "ScholaWrite: public academic-writing process dataset and intention annotations"
