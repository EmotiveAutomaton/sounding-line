# Sounding Line Stage 9 — execution recovery addendum
Date: 2026-09-10  
Reviewed push: `91017b7332ecb8e925437103b339e06d9efff5e3`  
Status: **Proposed curator instruction for the coding agent.** Forwarding this document with an instruction to apply it adopts the bounded changes below. This analyst review has changed no repository files, launched no jobs, and granted no extension.

## 1. Diagnosis and decision

Stage 9 is making implementation progress but is blocked before scientific launch. The dominant problem is the combination of an oversized workload and an all-at-once acceptance process. Real instrument defects and substantial new data/reader work also contributed. Published evidence does not establish a hung agent or general corruption of the old test environment.

The September 10 status records an available GPU, healthy watcher, no running or paused compute queue, 686 unrun ordered job objects and 24 unrun scientific fits. These counts include infrastructure jobs; they are not counts of independent scientific questions. Development pilots and regressions have run. The publication checkpoint reports 1,811 passing pytest cases across the initial run and corrected temporary-root rerun. Tests passing is not scientific admission.

The scheduling record estimates **164.493–198.273 GPU reservation hours for inspected components alone**, conditional on upstream gates passing. It excludes several remaining costs, confirmations and closure. Training contributes 45.856 hours; the original brief used about 20.4 hours as its historical sizing prior. Additional purpose/context CPU scenarios are substantial and must stay separate from GPU reservation.

The original allowance is 92 GPU hours. The campaign began approximately September 6 at 17:07 UTC and its 120-hour horizon is September 11 at 17:07 UTC. At the latest published status, about 91.7 hours had elapsed. Neither the clock nor cap has been extended. “Another 2–4 days to first scientific runs; around two weeks to finish” is expressly a rough judgment, not a complete recalculated forecast.

The validator requires every scheduled job to have a forecast and a rehearsal mapping, all 42 cards to be represented, and all 24 training fits to be scheduled. It also requires the serial sum of CPU and GPU work to fit the remaining campaign time. The queue actually waits for each child before starting the next. Continuing to perfect the oversized plan cannot resolve that resource conflict.

**Recommended decision:** retain the existing resource ceiling and select a smaller, scientifically interpretable first tranche. Preserve the wider Stage 9 agenda as explicitly deferred work. Do not approve a two-week extension by implication. Do not restart the apparatus.

This is a scoped change to execution coverage and launch policy, not a claim that the original full Stage 9 requirements have been satisfied. The analyst brief shares responsibility: its breadth and preflight obligations exceeded what its unverified five-day estimate could support.

## 2. First action: settle scope before further general preparation

Within **two active operator-hours of adoption**, update the existing `docs/design/STAGE9_FORECAST_REVIEW.md` with one compact decision table:

| Required field | Content |
|---|---|
| Current workload | Actual live owner, queue, last completed produce, active blocker and source revision; do not assume the reviewed push is still current. |
| Remaining resources | Original horizon, remaining allowance, separately identified preparation charges and unmeasured intervals. |
| First tranche | Exact existing cards and concrete jobs selected, their prerequisites, comparator arms, independent units and intended claim ceiling. |
| Deferred work | Every excluded card or contrast, with its reason; distinguish budget deferral, instrument failure and unavailable data. |
| Cost | Pilot-supported range for the selected queue, including CPU serial time, GPU reservation, preparation still needed and closure. |
| Readiness | Only blockers that can invalidate the selected observations or their interpretation. |
| Next observable result | A named scientific output and conditional completion range, or a concrete reason no valid tranche can launch. |

Use the existing rates and receipts. Do not finish estimates for hundreds of deferred jobs before making this decision. Reuse a measured handler/family rate where applicable, while retaining a mapping for each selected job and declaring scaling assumptions. Refine a cost only if its uncertainty could change the selected tranche's feasibility.

Account for unknown preparation costs honestly. If a reasonable conservative allowance cannot establish budget fit, report that budget blocker; do not enter a further open-ended accounting campaign.

## 3. Choose useful work without changing its scientific meaning

Select from the already commissioned work, using readiness and scientific discrimination together:

1. The repaired known-answer measurement and matched-information comparisons, especially I03 and I06, where the current implementation is actually ready. These can tell us whether a comparison measures the intended thing.
2. A complete operation-specific competence comparison using existing eligible packages, with its strongest cheap comparator and failure cases.
3. A real-corpus baseline or reader comparison whose loader, grouping, evidence boundary and interpretation already have adequate validation.

These are priorities, not a requirement to construct three more pipelines. Use only branches with complete dependencies that fit. An engineering validation already completed in development is retained as preparation; it is not relabeled as fresh scientific evidence.

Favor a few complete comparisons across distinct questions over many partially implemented contrasts. Defer expensive purpose/context searches, additional recipe grids, or new corpus branches when their cost or remaining implementation would consume the tranche. Preserve their pursuit value and describe what remains untested.

Do not silently reduce sample counts, truncate support, omit losing arms, drop inconvenient seeds, reuse exposed pilots as confirmation, or change competence thresholds to make a result fit. A claim that requires the full training factorial or three seeds remains unavailable unless that requirement is met. Archive-reader or exact-program results carry their own narrower package-specific claims.

The full Stage 9 card roster stays visible. A deferred card is **not run**, not failed, completed or counterevidence.

## 4. Make acceptance local to the selected tranche

This is the main proposed policy amendment. A branch outside the selected tranche must not block its launch merely because that other branch's implementation or reporting adapter is unfinished.

Retain, for every selected observation:

- verified source and reader identities, evidence isolation and relevant inherited-failure dependencies;
- valid positive/negative controls, complete support and intended task realization;
- defensible independent units, exposure accounting and untouched reserve protection;
- actual applicable interruption/recovery and writer-ownership evidence;
- complete selected-job enumeration, measured cost assumptions and immutable result identity;
- a functioning way to validate, preserve and report the selected outputs.

Keep all 42 cards and 12 attacks in a scope ledger. Each attack remains executed for the relevant selected task, inherited from explicitly compatible evidence, or inapplicable with a reason. “The other branch was deferred” does not excuse a shared leakage or scorer defect.

The full-stage path must still require the full commissioned grid. Add only the smallest explicit tranche policy needed in the existing validation path: an adopted scope identity, selected jobs and dependencies, deferred-card dispositions, and permitted claims. Do not remove global checks and leave an unqualified acceptance flag.

Current exact points to inspect:

| Owner | Required correction |
|---|---|
| `runners/stage9/launch.py::verify_forecast` | Cost the selected manifest; keep the existing 92-hour ceiling, original clock and serial accounting. Do not substitute an unlimited allowance. |
| `runners/stage9/launch.py::validate` and `verify_certificate` | Distinguish full-stage acceptance from explicit tranche acceptance. Current hard-coded 24-fit/full-roster assumptions cannot be silently bypassed. Bind the accepted scope and claims in the certificate. |
| `runners/stage9/closure_coverage.py` and `packet_review.py` | Reconcile selected, deferred and failed work separately. A tranche packet must not declare the full stage scientifically complete. |
| `runners/stage9/recipe_selection.py`, `selected_recipe.py`, relevant confirmation consumers | Inspect only if the selected tranche uses them. Do not let a partial grid masquerade as full-grid selection; exclude those consumers if their contracts cannot be met. |
| `runners/stage9/queue.py` | Preserve one-writer and recovery behavior. Keep the existing serial implementation for this recovery pass. Do not start a new concurrency project. |
| `docs/design/STAGE9_FORECAST_REVIEW.md`, `docs/STATE.md`, `TODO.md`, runner README | Record the adopted scope, actual blocker, next output and conditional forecast consistently; preserve dated history. |

All jobs actually scheduled still need their applicable forecast and rehearsal evidence. Reuse compatible existing rehearsals with explicit source/operation bindings. Do not require a new rehearsal solely to restate an unchanged receipt; do not claim compatibility merely from similar filenames.

Final integrity and interpretation requirements apply fully to what is reported. Unfinished machinery for unselected confirmation targets must not delay unrelated discovery work. If a confirmation is not fully supported, leave it unselected and unopened.

## 5. Bound the recovery; avoid creating another setup project

After the two-hour scope decision, allow **at most four further active operator-hours** for the smallest necessary acceptance/integration repair. These six hours are a work limit, not a promise of launch, and confer no extension of the original horizon.

At that boundary, deliver one of:

- **Launched:** a finite accepted tranche, its first actual scientific job and expected output; or
- **Blocked:** the failed prerequisite, affected branches, attempted correction, and whether any independent useful branch remains.

If the original horizon arrives first, stop admitting expansion and report what was actually achieved. Finish/checkpoint bounded active work under the original contract. If no credible scientific tranche fits the remaining time, close with a preparation-only outcome and price the smallest continuation separately. Do not reset the clock to hide setup, and do not interpret frustration about delay as authorization for more compute.

Reuse the present code and passing evidence. No broad rewrite, new scheduler, new corpus hunt, external compute or project-wide instruction overhaul in this recovery window. The original repair budget remains: preserve root causes and failed attempts, and close affected branches when their permitted repair budget is spent. A succession of differently named helpers is not a fresh budget.

## 6. Stop routine preparation receipts from becoming new research obligations

Keep scientific findings and material instrument corrections in the established full write-through. Continue to preserve raw development evidence.

For this recovery pass, routine cost arithmetic, unchanged historical-receipt verification and delivery acknowledgments update their existing infrastructure record and current handoff. They do not each require a fresh hypothesis, a new research card, another general regression, or a newly expanded source audit when they change no behavior or inference.

This is an explicit reporting clarification for routine preparation, not permission to omit a scientific landing or suppress a failure. A newly discovered shared defect still receives its dependency-scoped correction and invalidates affected consumers.

Use the completed theory-read progress record. Unchanged theory is not reread from the beginning merely because another compaction or wake occurred. Preserve the standing requirement to reread changed or relevant sections before an actual research judgment.

Progress messages should answer: **What finished? What is running? What specifically blocks the next result? What changed the estimate?** Avoid forwarding the entire preparation chronology with every acknowledgment.

## 7. Focused acceptance checks and rollback

These are proposed coding-agent checks, not tests executed by this analyst.

Use the existing validation fixtures, with one targeted cycle covering:

1. A complete selected branch can be accepted while an unrelated branch is explicitly deferred.
2. Missing selected-task leakage controls, prerequisites, source identity or recovery evidence still refuses launch.
3. Over-cap or over-horizon plans fail; tranche adoption cannot reset the campaign or invent CPU/GPU overlap.
4. Deferred fits cannot satisfy recipe, seed or full-factorial claims; a tranche packet cannot claim full-stage completion.
5. Current-source recovery preserves completed bytes and rejects a second writer.

Regression scope follows changed modules and their real consumers. Reuse the latest passing checkpoint elsewhere unless a concrete dependency was affected. Do not repeatedly run the whole historical suite for documentation-only or acknowledgment changes.

Implement against an isolated copy if any live work has appeared since the push. Do not edit code beneath a running job, clear its locks, overwrite results or alter a frozen manifest. If a tranche validator fails, revert the new acceptance change, retain its failed test evidence, and report the blocker. The original stricter full-stage path remains available.

## 8. Evidence and limits

Review type: source and published-record inspection. No home-workstation process inspection or scientific execution was performed here. Several detailed workload, health and inspection artifacts are intentionally private; their public summaries can be checked, but their unseen bytes were not independently audited.

| Evidence | What it establishes |
|---|---|
| [Current push](https://github.com/EmotiveAutomaton/sounding-line/commit/91017b7332ecb8e925437103b339e06d9efff5e3) and [STATE](https://github.com/EmotiveAutomaton/sounding-line/blob/91017b7332ecb8e925437103b339e06d9efff5e3/docs/STATE.md) | Substantial implemented work; published unlaunched status, queue/watcher observations, remaining obligations and validation report. |
| [Forecast review](https://github.com/EmotiveAutomaton/sounding-line/blob/91017b7332ecb8e925437103b339e06d9efff5e3/docs/design/STAGE9_FORECAST_REVIEW.md) | Partial conditional GPU estimates, unresolved resource decision, substantial separate CPU costs, and explicitly rough two-week judgment. |
| [Original Stage 9 brief, §§8–9](https://github.com/EmotiveAutomaton/sounding-line/blob/91017b7332ecb8e925437103b339e06d9efff5e3/docs/design/PHASE_2_4_STAGE_9_CONTEXT.md) and [campaign record](https://github.com/EmotiveAutomaton/sounding-line/blob/91017b7332ecb8e925437103b339e06d9efff5e3/results/phase_2_4_stage_9/CAMPAIGN.json) | Five-day horizon includes setup/closure; original resource envelope and start time remain in force. |
| [Launch validator](https://github.com/EmotiveAutomaton/sounding-line/blob/91017b7332ecb8e925437103b339e06d9efff5e3/runners/stage9/launch.py) and [queue](https://github.com/EmotiveAutomaton/sounding-line/blob/91017b7332ecb8e925437103b339e06d9efff5e3/runners/stage9/queue.py) | All-job forecast/rehearsal mapping, full-fit requirements, enforced resource checks and actual serial dispatch. |
| [Execution repair](https://github.com/EmotiveAutomaton/sounding-line/blob/91017b7332ecb8e925437103b339e06d9efff5e3/results/phase_2_4_stage_9/pilot/EXECUTION_REPAIRS.json) and [runner account](https://github.com/EmotiveAutomaton/sounding-line/blob/91017b7332ecb8e925437103b339e06d9efff5e3/runners/stage9/README.md) | Real Stage 9 defects included future evidence changing an earlier posterior, empty development combinations, Windows sharing behavior and a reporter comparing its own active heartbeat. These do not establish that all historical science is invalid. |
| [Preparation queue accounting](https://github.com/EmotiveAutomaton/sounding-line/blob/91017b7332ecb8e925437103b339e06d9efff5e3/results/phase_2_4_stage_9/pilot/PREPARATION_QUEUE_COST_DELTA_V9.json) | 102 queues and 787 recorded attempts; about 8.3 queue-occupied hours. This is incomplete preparation accounting, not total operator time, GPU utilization or proof that the remaining elapsed time was wasted. |

**Assessment:** high confidence in the schedule/resource mismatch and global launch coupling; moderate confidence that process overhead is a major contributor to elapsed delay; no defensible percentage breakdown of time and no live proof of an agent hang. The remedy is a bounded scope decision and a useful first result, with unchanged evidential standards for whatever actually runs.

