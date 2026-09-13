# Stage 10 reader prototype

The [current context](../../docs/design/PHASE_2_4_STAGE_10_CONTEXT.md) adopts the
curator's Stage 10 specification. Stage 9 modules and frozen results remain intact.

`contracts.py` is the public task and forecast boundary. Only declared evidence,
choices and the prediction question enter a model request. Source identities,
group allocation and evaluation answers belong in a separate evaluator record.
`ollama.py` saves each literal request and raw response before parsing, with the
actual model digest, settings and server timing. Its probabilities are elicited
forecasts, not token likelihoods or a claim about an internal posterior.

Each attempt has its own directory. Existing attempts are immutable; a resume
may validate and reuse a completed attempt but must retain failed attempts too.
Record all calls, invalid outputs and costs. Never silently replace a malformed
forecast with a uniform distribution. Score whole frozen comparison cells only.

New source adapters must validate chronology, contributor roles, allocation and
the exact public evidence before execution. Run discarded literal interface
checks before a branch's first scientific cohort. One branch's repair does not
prevent another validated branch from running. Preserve CPU cooling limits,
GPU ownership and final-produce guards. Transition-only monitoring wakes the
owner on completion, failure, disappearance or a predefined checkpoint. Healthy
running processes end the agent turn; routine liveness timers are disabled.

`deliberation.py` implements R2 with two 384-token direct calls. `proposal.py`,
`executor.py`, `executor_worker.py` and `structured.py` implement two bounded
R3 proposal/execution rounds through unchanged exported Ghost APIs. R3 retains
the generated choice separately from its uniform likelihood-weighted candidate
mixture; those probabilities are conditional on proposed support, and are a
distinct instrument requiring development calibration. Impossible evidence
stays a mismatch. The current opportunity interface passes; the reading
proposal repeats a library after the one clarification and remains diagnostic.

`ghost_source.py` joins only frozen training cases to actual recorded enacted
outcomes. `opportunity_chain.py` runs the finite common development producers.
Source-case grouping, discarded exclusions and historical exposure stay visible;
selected cases are not automatically independent makers. Completed checkpoint
replay is verified; partial-run ownership recovery remains a limitation.

`phase_queue.py` selects the explicitly named frozen development/evaluation public
record. It preserves the original request builder and only reads training labels;
the current evaluation is historically exposed data, not a newly untouched reserve.

`phase_deliberation.py` applies the unchanged two-call R2 reader to an explicitly
frozen evaluation phase. It does not open evaluator answers.

`effort.py` implements the R5 development-only benefit/cost table and a bounded
callback driver, with fixed and confidence-only comparison policies. It reserves
256 generated tokens for the first read and 512 for an optional extra route.
Group-balanced development gains use half multiclass Brier loss; malformed
answers retain worst loss and actual cost. Unsupported strata stop. Its 26
known-answer checks pass; this is not evidence of scientific routing benefit.

`effort_readers.py` and `effort_proposal.py` connect this budget to literal local
requests and the unchanged public opportunity executor. Constructed transport
and real-executor checks pass. The literal model rehearsal and source-verified development fit now pass;
reserved policy comparison and scientific interpretation remain pending.
Full-budget historical predictions cannot replace the reserved-budget calls.

Pass the adapter's complete `sources` receipt to the effort driver: it binds
training evidence, training answers and the public envelope as well as code.

`effort_queue.py` collects the smaller-budget forecasts from a discarded pilot
or the frozen development population. `effort_fit.py` verifies original enacted
outcomes for the preallocated fitting cases only. `effort_evaluation.py` runs
actual fixed, confidence-only and benefit/cost policies on the reserved cases,
with no target outcome access. The small within-stage reserve was chosen before
outcome access but after prior forecast production; its evidence is descriptive.

`reading_source.py` freezes case-separated reconstruction inputs and verifies
training truth against the nested original future program through the native
executor. `reading_memory.py` uses the original native fragment learner on
reader-reconstructed artifacts and retains a bounded concrete memory. This is a
LILO-inspired adaptation, not a reproduction or historical-trace recovery. The
reading-family retrieval pool spans accurately labelled evidence views, with
the same sources and 6,000-byte representation cap for R1 and R4. No reusable
procedure is forced when the source evidence does not support one.

`reading_proposal.py` gives each possible library a unique keyed slot, shared by
the new R3 and R4 routes. The earlier list-shaped failure remains diagnostic.
`reading_routes.py` charges the complete R0/R1/R2/R3/R4 screen, including both
opaque and grounded procedure names. R4 can induce from the target case's
permitted earlier artifacts in addition to global training; it never reads the
future target outcome. Empty learned libraries are retained. The complete route
passes constructed transport/native execution checks; actual model admission
requires a source-bound discarded pilot receipt before development/evaluation.

`human_programs.py` evaluates bounded CoAuthor handling rules over whitelisted
public features. `human_proposal.py` elicits separate goal conjectures and rule
programs; `human_routes.py` executes two proposal/refinement rounds within the
same 768-token allowance. Equal rule mixtures with a fixed 0.15 lapse are an
explicit approximate behavior model, not a known human law or exact posterior.
Only current draft/menu features and genuinely supplied earlier handling enter
the executor. No model-generated Python is executed. The constructed queue and
replay checks and the actual source-bound pilot pass. `human_science_chain.py`
runs the frozen development/evaluation producers serially; target outcomes stay
closed and whole-cell scientific analysis remains separate.

`human_memory.py` induces view-specific approximate handling rules from frozen
training episodes and retains concrete exceptions. The best constant action is
a training comparator; branch support and training improvement are selection
rules, not scientific generalization tests. `human_memory_routes.py` compares
storage-matched retrieval with opaque and grounded procedure memory. Its new
`human_memory_proposal.py` wrapper exposes the unchanged request builder so the
common memory allowance reserves feedback space before selecting whole examples.
The two naming conditions retain identical definitions and episodes. Both
constructed whole-queue and literal model checks pass; the first context-bound
failure and original source bytes remain preserved. Science requires the exact
revised pilot source/memory receipt. Full-cell analysis is still separate.

`human_effort_readers.py` and `human_effort_proposal.py` connect the same human
evidence and approximate executable rules to the existing effort controller.
The first read reserves 256 tokens; retrieval or two rule proposals share the
remaining 512. `human_effort_queue.py` collects discarded/development forecasts
without target outcomes. Constructed whole-queue and controller checks pass;
the literal model pilot now passes raw replay and native-exit verification. One development writer cannot
validate general routing benefit and unsupported strata retain the first read.

`human_effort_fit.py` verifies the complete development producer with model and
executor access disabled before opening its frozen development outcomes. The
constructed fit and immutable-policy replay checks pass. The actual development producer and immutable fit now reproduce; single-writer
support admits no extra route. Central
evaluation comparisons are recorded in `docs/design/STAGE10_COMPARISON_FREEZE.md`.

`human_effort_evaluation.py` runs the frozen fixed, confidence-only and benefit/cost
policies on the reserved human cohort. It reproduces the fit first, then verifies
the original evaluator bytes and projects only task/writer/prompt/event identity.
Outcome values are discarded during decoding and never reach a model request.
The complete constructed evaluation/replay and refusal checks pass, including
invalid outputs and cross-split dependencies; all frozen request bounds pass.
The first CRLF mutation-fixture refusal is preserved. Scientific benefit is pending.

`comparison.py` implements the central freeze's complete-cell scores, distinct
generated-choice and probability readouts, explicit invalid/zero-support handling,
equal writer/case weights and connected-dependency uncertainty. It refuses changed
paired evidence or incomplete populations. `human_baselines.py` fits fixed cheap
controls on training only: class prior, surface-feature logistic prediction,
always-ignore and previous handling. Surface features use current draft/menu
length, overlap, menu position and hashed lexical counts; personal history is
confined to the explicitly named previous-handling control. Its fixed optimizer
and scaling never use evaluation outcomes. Known-answer whole-producer and replay
checks are in `comparison_checks.py`; passing them is apparatus validation only.

`human_history.py` freezes a development-selected structured rival and an
exact-length other-writer history intervention for that rival and R0. It keeps
all other public evidence and options fixed, retains unmatchable opportunities,
and verifies each donor assignment from original public records. Original true
history predictions are reused only on the same eligible task IDs. The worker
replays complete outputs without calls and requires native ownership recovery
for interrupted work; it does not automatically restart an unfinished attempt.
Both rival paths pass constructed full-worker checks. The selected real cohort
and all first/refinement request bounds are frozen before evaluation answers.

`earlier_artifacts.py` projects strictly prior within-session draft snapshots from verified CoAuthor replay, retaining empty and identical priors and explicit context exclusions. It adds no handling labels or operations. Its finite R0/R1/R2 development/evaluation chain has four terminal-guarded jobs, source-bound literal admission and known-answer full-chain replay checks. It does not substitute direct deliberation for the still-pending structured/adaptive extensions.

`earlier_programs.py` preserves the original human rule vocabulary and executor.
Earlier drafts can inform which rule the reader proposes, while a given rule
still acts on current-draft/menu features. This isolates added evidence from
added executable features. `earlier_proposal.py`, `earlier_memory.py` and
`earlier_routes.py` are versioned adaptations of the corresponding human
memory modules, leaving historical source bytes intact. R3 receives no training
representation; R1 and both R4 naming conditions share the existing storage
ceiling and full feedback reservation. Selection records additional context
exclusions for complete whole-draft requests, and comparison must match those
task IDs rather than pool different populations. Adaptive effort is separate.

Gear 3 Round 1 uses explicit `ReaderProfile` values through the existing readers;
legacy requests/bindings are unchanged when no profile is supplied. `gear3_inputs`
and `gear3_prepare` project existing permitted sources and discarded pilot tasks.
`gear3_bundle` exports only the reviewed execution closure and selected public inputs.
`gear3_batch`, `gear3_io` and `gear3_worker` retain full durable nested attempts,
original expiration and native executions. `gear3_comparison` admits only the
specified history delta and complete declared contrasts. Paid execution remains
exclusively under `runners/gear3.py round1` and `round1-plan`, with one canonical
campaign ledger. Offline verification is not literal cloud or scientific admission.
See the [Round 1 runbook](../../docs/design/GEAR_3_ROUND_1_REVIEW.md).

The extended Round 1 checks cover partial-unit result reconstruction before new
calls, exact training/target group separation, full donor provenance and complete
returned-block replay. Finished export recovery performs no inference and refuses
an existing archive that differs from its retained attempt. Account/environment
binding and the lower account allocation are enforced by the campaign controller.
