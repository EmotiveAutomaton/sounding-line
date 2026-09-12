# Sounding Line Stage 10 — a useful artifact-reading prototype

**Coding-agent handoff, 12 September 2026.** Based on Sounding Line `1962cc4dd90060a1f54852437cab42fdc2784733` and Ghost Scale Sim `5b73980a2ee8a28daf0922b26072ba4f461ff7f8`. This is a proposed new stage after the curator's walkthrough. Stage 9 remains closed; its 632 deferred jobs are not automatically commissioned.

## 1. Hypothesis, method and deliverable

**Hypothesis:** a compact, revisable model of a maker's procedures and goals can improve predictions about an unseen choice or changed situation, especially when combined with specific remembered examples and executable checks.

**Method:** compare six reader strategies on the same permitted evidence and withheld targets: a capable direct reader, retrieval, matched deliberation, executable hypotheses, procedures plus exception memory, and adaptive effort. Use existing Ghost tasks for exact checks and human revision records for real behavior. Distinguish artifact-only evidence from the extra value of process records.

Deliver a bounded prototype that accepts an artifact and permitted context, states alternative hypotheses with their evidence, commits predictions, and demonstrates what those hypotheses help predict. Its uncertainty and failure cases must be visible. A fluent explanation alone is not the product.

The main outcome is **useful prediction from artifact evidence**. A better reconstruction of the supplied simulator law is a component result. A stronger next-edit classifier is a separate component result. Neither silently becomes general intent recovery or added provenance value.

## 2. Timing and authority

Aim for approximately **five elapsed days including setup, experiments and analysis**, with useful scientific work beginning within about one day. Treat this as a soft planning target. There is no minimum machine-occupancy requirement, global all-corpora-ready condition or mandatory wait until day five. The user's latest instruction takes precedence over old timing language that excludes setup from the campaign clock.

This sheet commissions the described new scope when handed to the coding operator. It does not authorize reopening old confirmations, editing hash-locked files, spending money beyond existing approval rules, contacting authors, or running the historical deferred catalog. Routine reversible implementation and scoped repairs within this plan do not need repeated curator permission.

Read `AGENTS.md`, current `docs/STATE.md`, `TODO.md`, the relevant theory passages and `docs/method/LESSONS.md` §§2–5 before implementation. Reuse recorded reading progress. In particular retain the lessons about CoAuthor replay, source-group separation, short scored candidates, matched option order, real-output parsing, private-field exclusion and scoped historical source compatibility.

Leave `docs/SOUNDING_LINE_SPEC.md`, `prereg/*.py` and `soundingline/locks.py` unchanged. Add a stage-specific context and new modules, rather than retroactively altering frozen protocols. Explain the timing/scope amendment in the new context and current task list, without rewriting historical results.

## 3. Starting position and implementation map

The current completed report is the baseline. Stage 9's selected run did not execute a successful human-process reader across its expanded corpus shelf. Prepared sources and multiple useful adapters exist. Use them. The archived small readers' generation difficulties motivate comparing capable instruction-based readers and executable assistance; they do not establish that all test environments are broken. [Stage 9 packet](https://github.com/EmotiveAutomaton/sounding-line/blob/1962cc4dd90060a1f54852437cab42fdc2784733/results/phase_2_4_stage_9/SCOPED_CURATOR_PACKET.md).

| Existing implementation | Use in Stage 10 |
|---|---|
| `runners/stage9/coauthor.py` | Canonical replay of UTF-16 edit deltas, shown suggestions, selected insertion and subsequent handling |
| `runners/stage9/coauthor_cases.py` | Chronological opportunities, writer/prompt component separation, explicit artifact versus record views |
| `runners/stage9/schola_cases.py`, `scholawrite.py` | Existing prepared chronological scientific-writing evidence; inspect actual label/role semantics before choosing targets |
| `runners/stage9/revision_cases.py`, `revision_features.py` | ArgRewrite anchor and explicit change features; do not redefine the old target |
| `runners/stage9/proposal_reader.py`, `program_inference.py` | Existing finite candidate-pool/stateful evaluation pattern; its current process-record assumptions are not an artifact estimator |
| `runners/stage9/rollout_operations.py`, `supplied_operations.py` | Small continuity checks on generation versus supplied-operation assistance |
| `runners/stage9/source_bootstrap.py` and current queue utilities | Actual loaded-source receipts and scoped resumability; preserve historical helper bytes where their identity is part of old evidence |
| `runners/gear3.py` | Sole cloud entry point; requires a small reviewed transport extension for this stage's data and model dependencies |

New code should live in `runners/stage10/`, with a stage context at `docs/design/PHASE_2_4_STAGE_10_CONTEXT.md`. These are proposed paths. Wrap existing readers and prepared data in new versioned adapters. Do not patch immutable Stage 9 records to make a new consumer appear historically admitted.

## 4. Evidence and task contract

Every task explicitly declares the input artifact, allowed context, optional earlier artifacts/process records, candidate support, target time, contributor role, evaluation unit and exposure status. Use a typed request/response format shared by the strategies. The renderer may translate legal public fields into readable text; it may not add private goals, a correct library, target answers or the best action.

Maintain three evidence conditions:

- **Artifact/context:** a finished artifact or the current draft at a defined cutoff, labeled accurately; no later events.
- **Earlier artifacts:** the same input plus permitted prior works or prior draft states, without secretly supplying the producing operations.
- **Process record:** genuine pre-cutoff actions, feedback and handling. This measures the incremental value of records.

An inference from a current draft is not a demonstration on a final published work. An archival cross-work comparison is not temporal forecasting unless dates/order are verified. Never manufacture cross-session chronology from filenames, hash order or row order.

Goals, procedure hypotheses, recipient state and historic contributor control are separate fields. A hypothesis is allowed to be absent from the proposed set; measure that coverage on known synthetic cases. Include an explicit “none of these/insufficient support” route where the scientific target permits it. Do not force an apparent posterior certainty by deleting the true alternative and renormalizing the rest.

Commit predictions before evaluator access. Public task IDs should be opaque and not encode labels or source role. All arms use the same option order for a paired task, with content-based canonicalization for invariance checks. Preserve the exact prompt, response, parse status, model settings, sources and costs.

Declare the probability readout per backend. If the serving path exposes validated candidate log probabilities, score the same short candidate forms under the same normalization rule. If it only supports generation, elicited probability vectors are allowed as a new, explicitly labeled forecast instrument and require development calibration checks; they are not token likelihoods or direct measurements of an internal posterior. Never mix the two readouts in a purportedly identical historical comparison. Keep generated-choice accuracy beside probability scores.

## 5. Reader strategies

Start with the existing local instruction-capable `qwen3.5:9b` service, recording its actual model digest and configuration. Do not silently substitute it for the archived Qwen2.5/SmolLM checkpoints in historical comparisons. Those old checkpoints need only a small continuity sample. A second model checks selected important contrasts after the main screen; it does not multiply every cell by every model.

| ID | Strategy | What distinguishes it |
|---|---|---|
| R0 | Direct prediction | One capable reader receives the declared evidence and returns the requested choice/distribution, with no imposed latent narrative |
| R1 | Episodic retrieval | A fixed retrieval rule selects concrete development/prior episodes, preserving their exceptions; no induced reusable procedures |
| R2 | Matched deliberation | The direct route receives the same total call/token allowance as the structured route for reconsideration or candidate comparison |
| R3 | Executable hypotheses | Propose a small set of goals/processes; use a permitted executor to evaluate their consequences; predict by a declared mixture/ranking rule |
| R4 | Procedures plus memory | R3 plus procedures induced only from permitted training/prior evidence and a bounded store of concrete examples |
| R5 | Adaptive effort | Choose among R0/R1/R3 or further checks using development-estimated decision benefit and actual cost |

Give retrieval and procedure methods the same source material; their selected representations may differ. Show both a common storage/token budget comparison and their actual costs. R4 must be compared against R1 and R3 individually, otherwise its benefit cannot be assigned to the combination. R2 prevents an extra-computation advantage from being called a special benefit of maker modeling. Always retain R0 beside any matched-cost comparator.

Start with at most eight process/goal candidates, two proposal/refinement rounds and a total of 768 generated tokens per task across the route. These are adjustable pilot defaults, not universal cognitive constants. After a discarded throughput pilot, freeze a common budget for scored matched comparisons. Count all model calls, input/output/reasoning tokens and executor evaluations, including failed parses and controller overhead. A route can terminate early; that saving is an outcome.

For R3, provide transition rules/tools only at the declared assistance tier. Distinguish known-law execution from inferred-law execution, and both from providing the true maker goal. Use the existing Ghost evaluator rather than inventing a weaker Sounding Line world. A candidate program must run through the permitted API; a language-model explanation that it “would work” is not execution.

For R4, use existing native motifs first, then the small Stitch adapter if available. Compare opaque procedure IDs with descriptions grounded in their definitions and actual training uses. Names must not reveal private purpose labels or test outcomes. Label this LILO-inspired adaptation, not a reproduction of LILO's published benchmark. [Inspected LILO naming code](https://github.com/gabegrand/lilo/blob/7812c49bc2ef660cab2c57631b816658011b60bb/src/models/library_namer.py), [Stitch](https://github.com/mlb2251/stitch/tree/350804b7b35807c78bd21c313785ae5152ae2985).

For R5, compare fixed effort, confidence-only refinement and benefit/cost selection. Learn the benefit estimate on development cases with known subsequent outcomes. Do not optimize evaluation answers or assume a low-entropy posterior is accurate. AutoToM's variable-expansion pattern is useful; its thresholds and language-model factor probabilities are not an exact oracle. [Inspected adjustment code](https://github.com/SCAI-JHU/AutoToM/blob/3f569b7ab1d0ee2702ab43ebdc724679d5fc5231/model/model_adjustment.py).

## 6. Study A — the actual Ghost-to-reader connection

Begin with Ghost's existing `results/v16/transfer-handoff-1/reader.zip`. Its corrected public whitelist contains 44 selected synthetic cases and 1,574 heterogeneous tasks. The bundled reference consumer ran successfully; this does not mean a Sounding Line model has consumed it successfully. Read the per-task operation and target contract before choosing a subset. Do not pool unlike targets under a single “accuracy.” [Handoff documentation](https://github.com/EmotiveAutomaton/ghost-scale-sim/blob/5b73980a2ee8a28daf0922b26072ba4f461ff7f8/docs/versions/v16-acquired-craft/TRANSFER.md).

The reference launch from `public/consumer` is `python -s -B -u -m consumer` in a NumPy environment. It accepts a public JSON frame per line and returns a source receipt followed by typed results. Keep this reference process separate from the new language-model adapter. Its post-import audit hook is a scoped protection for the reference; it is not automatically a security boundary around an arbitrary model server.

Select tasks that actually test reading/reconstruction or changed opportunities for the primary bridge. Construction tasks with a supplied acquisition history form an assisted craft lane. Do not describe them as artifact-only maker inference. Public envelopes include `final_artifact`, `declared_context`, `permitted_prior_artifacts`, query descriptions/costs, `target_request` and `reader_action_budget`; preserve their actual access meaning.

Compare R0–R5 on:

1. A withheld action or finite behavioral target for which the task defines a correct reference.
2. A changed constraint/opportunity or changed recipient where the hypothesized maker model predicts a difference.
3. An executable reconstruction, scored independently from whether it matches the historical trace.

Use current known-law/supplied-operation tasks only as continuity diagnostics. The primary bridge must retain an unknown maker/process component. The old V16 cases are selected and previously examined, so results on them are descriptive. Fresh V17 tasks, if delivered in time, form a separately frozen evaluation cohort. Sounding Line starts without waiting for them.

## 7. Study B — real human selection and revision

### CoAuthor: first human priority

Reuse `private/prepared/coauthor-v2` under the Stage 9 result root through its reviewed adapter, including its identity and source checks. The existing replay reconstructs document state and joins a selected insertion to the displayed menu. Preserve these semantics: the suggestion text belongs to the model; the human's observed contribution is its selection and subsequent handling.

Start with the existing prospective handling target: accept, edit, dismiss or ignore, at the menu opportunity before the subsequent outcome. This is a four-way behavior forecast, not a primary-purpose label. If feasible within the same adapter, add the more concrete secondary target of **which displayed suggestion was selected**, conditioned on a verified selection, retaining ambiguities when multiple options match the insertion. Include an unconditional selection/no-selection outcome so the conditional task does not hide abstention.

Compare artifact/context, earlier artifact evidence and pre-cutoff records. For creator-specific learning, distinguish zero-shot prediction for a held-out writer from adaptation using that writer's permitted earlier behavior. “Held-out writer” means held out from global fitting; permitted personal adaptation is explicitly declared. Do not let adaptation see the current target or later events.

Separate writer and shared-prompt components using the existing cross-source ledger. All repeats/near duplicates remain in one allocation. Preserve discarded pilot groups. Do not reclassify historically exposed discovery data as an untouched reserve. When strict joint writer/prompt separation leaves few people, report the actual number and scope the result accordingly; thousands of menu events do not become thousands of independent writers.

Compare against class priors, position/length/lexical suggestion features, and the existing development baseline before attributing a gain to maker modeling. Examine within-writer benefit, changed prompt/domain and mismatched history. A correct history that helps no more than a matched other-writer history is evidence against personalization under that representation.

### ScholaWrite: second human source

Reuse the prepared corpus and current loader. Select a truly chronological future revision target supported by the records, then compare the same artifact and history conditions. Preserve author/editor/project roles as recorded; post-hoc annotation of an edit is not a record of an unconscious goal. With only a small number of source projects, use project-level separation, report the project count and keep conclusions descriptive.

The preferred contribution is a contrasting revision environment, not a second large fine-tuning project. If this branch encounters a new semantic parsing issue, retain its concrete diagnostic and continue CoAuthor and the synthetic bridge.

### ArgRewrite: continuity anchor

Retain the earlier recorded-purpose result and the distinct Stage 9 future-class result under their original definitions. Run only the small comparison needed to show whether a new reader changes the prospective pattern. Use explicit diffs when the task provides before/after text. Keep exact edit class, intended effect and primary purpose separate. The old 18-forecast result does not warrant a new general statement about all process records.

## 8. Study C — predicting effects rather than exact edits

This is a new target, not a renamed edit label. On Ghost's recipient tasks, ask separately what operation will be chosen and how a declared recipient's belief/action changes. Compare prediction errors across the two targets and test recipient shifts. Use independently executed recipient outcomes rather than the same model judging its own prose.

In real corpora, human suggestion acceptance and retained edits are behavioral outcomes; they are **not** ratings of reader comprehension, suspense, pleasure or persuasion. Do not infer those effects from their labels. If no appropriate existing human recipient measurements are available, deliver the synthetic effect result and an explicitly unvalidated real-text illustration. That is a useful bounded outcome, not an invitation to generate “ground truth” with the same reader.

Only one new external data extension is eligible this week: [CognitiveStrategiesInTeaching at `908f74ec7eefd94ebd055fe975cbb12cf1d91254`](https://github.com/sharootonian/CognitiveStrategiesInTeaching/tree/908f74ec7eefd94ebd055fe975cbb12cf1d91254), MIT. The inspected `functions/mentor.py` scores advice by expected improvement in a learner's task value given possible knowledge graphs. Its release includes human teaching decisions. A bounded adapter can add an adjacent audience-knowledge task if the original fields/splits support it. It is optional; do not reproduce every notebook or make literary claims from it. Avoid importing free-text participant debriefs into model prompts.

Professional editing standards motivate audience/purpose-sensitive evaluation; they do not supply outcome labels. PEER-style plan/edit generation can propose alternatives, and CoEdIT can be an optional editing component if already usable, but neither warrants synthetic historical truth. [Editing fundamentals](https://editors.ca/publications/professional-editorial-standards/fundamentals-editing/), [PEER](https://arxiv.org/pdf/2208.11663), [CoEdIT's explicit limitations](https://arxiv.org/html/2305.09857v2).

## 9. Bounded breadth and analysis

Start with planning cohorts of up to 128 distinct synthetic tasks, 192 CoAuthor opportunities and 96 events from the second human source/anchor. Cap concentration per human writer initially at eight opportunities where available. These are throughput and coverage starting points, not claims of adequate population power. Count distinct cases, writers, prompts and projects before final allocation.

Run the six strategies on that common screen using the main local model. Expand useful, contrasting cells toward roughly 384 synthetic tasks, 384 CoAuthor opportunities and 192 second-source events only if measured throughput supports it. Do not repeat every evidence intervention on every method: apply the history/recipient/constraint adversaries to R0 and the leading structured rival, selected by a frozen development rule.

Reserve one second-model comparison for the same frozen tasks and routes that determine the conclusion. Additional training is optional and specific: one justified procedure/retrieval component or small adapter recipe, with a no-training comparison. If making a fine-tuning claim, use the required multiple-seed validation. No 24-fit prerequisite and no broad retraining grid.

Report paired proper-log-score differences, calibration, end-to-end task success, coverage, and cost. Cluster human estimates by writer/project and synthetic estimates by shared case/constructor; respect crossed prompt dependencies. Repeated views, seeds, model calls and aliases are not new independent makers. Keep small-project intervals and their limitations visible.

For execution, distinguish parser validity, action legality, task success and appropriate stopping. Publish all attempted denominators and both valid-only and end-to-end outcomes. A deployment fallback may be predeclared and scored as part of the full system, but must be explicitly flagged; never turn a failed proposal into an unmarked uniform answer or a supposedly informative null. A constant STOP or class-prior policy must appear beside the trained/model results.

Freeze at most three central evaluation contrasts before revealing their held-out labels; use a declared multiplicity rule if assigning confirmatory language. Previously exposed corpora remain exploratory/descriptive unless a genuinely untouched, source-separated evaluation allocation is established. A confidence interval crossing zero does not establish equivalence.

The final reading is a region map: which input, method, resource level and target work together? It must distinguish useful generic craft from personal inference, extra computation from structure, informative history from redundant history, and correct execution from a plausible explanation.

Human history-swapping is an intervention on the reader's evidence, not on the historical writer. It can test whether a reader uses the appropriate evidence; it does not by itself establish that the inferred procedure caused the writer's action.

## 10. Setup and recovery that keep science moving

During the first working half-day, run a few literal public requests through the new model adapter, executor, scorer and saved-output path. Inspect raw answers from the actual reader. Verify a correct trace, invalid trace, wrong option, no-information case and private-field refusal. Exercise the actual queue/resume/report path on a tiny stage-specific manifest, rather than rerunning all historical campaigns.

Freeze each branch's task semantics and source identities before its scored cohort. Other independent branches can still be implemented while it runs. A change to a shared helper requires a scoped compatibility review; prefer a new wrapper when historical source identity would otherwise change. Retain failed attempts and restart from saved valid rows rather than from zero.

One concentrated repair attempt should resolve an interface problem or produce a clear disposition. If more work is needed, record the expected benefit and keep the ready branches running. This is a planning rule, not an automatic scientific veto. Do not keep resetting a global readiness checklist after every local repair.

Use the existing GPU lock and process ownership rules. Check actual process enumeration and completed outputs before calling an agent hung; a heartbeat is not progress and an inaccessible process handle is not proof of death. Routine wake cadence remains roughly 30–60 minutes with immediate notification for real faults; do not spend model calls on minute-by-minute polling.

The progress note should show elapsed setup, first useful run, completed comparisons, active jobs, concrete blockers and predicted finish. Separate CPU/GPU execution, agent setup, queue waiting and recovery. Do not substitute a conservative preparation allowance for measured utilization.

The schedule below is a planning envelope for the single local GPU, not a guaranteed runtime or a series of permission gates.

| Approximate interval | Main work |
|---|---|
| First 0–12 hours | Literal Ghost request-to-prediction path; CoAuthor replay sample; first R0/R1 scientific rows after local checks |
| By roughly 24 hours | Structured reader and matched deliberation running; remaining branches have bounded scopes and measured forecasts |
| Days 2–3 | Common six-strategy screen; selected evidence/constraint contrasts; second human source alongside completed analysis |
| Day 4 | Frozen evaluation and selected second-model comparison; optional cloud work only if activated through the existing route |
| Day 5 | Complete reports, prototype examples, cost account and dispositions for unfinished branches |

Initially budget roughly 40–65 hours of local GPU service for this scope, leaving room for setup and reporting to overlap with execution. This is a planning allocation, not measured demand. Use first-day throughput to adjust cohort sizes; prioritize independent sources and changed-condition tests over additional seeds of an unchanged inference-only model. Do not consume all available time in the screen and leave evaluation or interpretation for an unplanned second week.

## 11. Optional Gear 3 package

**Purpose:** determine whether a stronger reader changes the principal pattern, and accelerate a selected comparison. Core work continues locally. No cloud objects or paid jobs should be created merely to prepare this option.

Prepare one H100 job using `Qwen/Qwen3.5-27B`, with a pinned model revision and the same task records for R0, R2 and the leading structured route. Use text inputs for the paired core comparison, the documented chat template, and an explicit thinking-mode configuration; record and charge it consistently. This is a larger current-family comparator, not a guaranteed stronger reader or proof of a pure parameter-count effect. Pin a serving stack that actually supports its architecture; the old cloud image is not presumed compatible. Configure one GPU, the text-only inference path and a modest context limit matched to the local experiment; the model card's eight-GPU, long-context example is not the proposed deployment. Verify memory use in the pilot. [Official model card](https://huggingface.co/Qwen/Qwen3.5-27B).

Initial package: up to 128 synthetic tasks and 128 human opportunities, with an estimated 90-minute pilot window. Run paired routes in the same cloud environment. Use the local throughput sample to reduce the count if necessary; 90 minutes is an estimate to test, not a claimed measured runtime. Return every prediction and cost record before container teardown.

As checked on 12 September 2026, Modal lists H100 at $0.001097/second, about $3.95/hour. The current wrapper uses $3.95/hour and a 1.4 estimate factor: approximately **$8.30 for 90 minutes**, or **$44.24 for eight hours**. CPU, memory, storage and existing ledger spend must also be included before approval; neither figure is an all-in bill or a guaranteed maximum. [Official pricing](https://modal.com/pricing).

Use only `runners/gear3.py`. Its present data setup is oriented to older PAN bundles and does not automatically provide Stage 10 inputs, adapters or an appropriate pinned inference environment. Prepare a small extension with an explicit reader-input archive, compatible package versions, a result manifest and complete prediction retrieval. Keep evaluator labels and unrelated repository/private data out of the remote input bundle. Validate that path locally before presenting activation.

The concrete activation request must contain the literal command, target files, model revision, GPU, route/task counts, runtime forecast, all-in cost ceiling, current ledger balance, timeout, and resulting output paths. The existing per-use rule still applies; crossing the cumulative $10 window needs the existing fresh cap approval. The user's willingness to consider Gear 3 is not a dollar ceiling. Do not edit that ceiling or invent an approval string. A larger burst is worth proposing only if the pilot forecast shows it answers a remaining decision within the week.

## 12. Deliverables and interpretation

Deliver one report, one prototype example bundle and one machine-readable comparison table. The report opens with the hypothesis, method and what improved; it also names the best plain baseline and the practical limitations. Each table defines its rows, units and denominators. Link the underlying receipts so the curator can follow a claim without reading the entire setup history.

The prototype examples must show artifact/context, alternative maker/process hypotheses, evidence for and against each, a committed future prediction, the actual withheld outcome, and the cost. Include mismatched-history, dependency-damage and confidently-wrong examples when present. Keep reader-enactable routes distinct from actual historical routes.

Close with answers to four concrete questions:

1. Did an artifact-conditioned model improve a genuinely withheld choice or changed-situation prediction over R0 and R1?
2. Did executable structure add value beyond equally budgeted deliberation?
3. Did a creator's own permitted history help more than matched other-creator evidence?
4. Is the next obstacle chiefly representation, proposal coverage, execution, data/target alignment, or an unresolved comparison?

No single answer is required for completion. If direct reading wins, retain it as a useful product component and explain what the structured account failed to add. If only synthetic work succeeds, say so. If a human behavior target improves, keep its claim bounded to the recorded outcome. Provenance stacking is a subsequent decision after there is an increment worth testing; it is not another automatic prerequisite this week.
