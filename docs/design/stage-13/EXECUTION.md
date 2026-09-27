# Stage 13 execution handoff

Operational snapshot: September 27, 2026. Scientific conclusions are pending.
The original brief and approved plan remain in this folder. The implementation lives
in `runners/stage13/`; private inputs, immutable cards, source capsules, outputs and
native ownership live in `results/phase_2_4_stage_13/raw/`.

## Authority and fixed finish

- Gear 1: one CPU worker, one numerical thread, below-normal priority. Preserve
  boost disabled and maximum processor state 90%. No GPU dispatch or cloud use.
- Friday **October 2 at 05:00 PDT** is the final deadline. No new science may run
  into the reporting reserve beginning **Thursday October 1 at 21:00 PDT**.
- The fixed checkpoint helper records reporting-start, early-final-review at
  **Friday 03:00 PDT**, and deadline. Markers request an operator landing/report;
  they are not themselves a completed scientific packet.
- Keep Stage 12 stopped. Its original reporting checkpoint is September 27 at
  18:17 PDT and final packet September 28 at 06:17 PDT. Stage 13 resets neither.
- Four-hour health inspections and terminal/failure events use the existing sole
  watcher. Do not add periodic model polling or another queue owner.

## Frozen roster and implemented consumers

The core plan is `raw/plans/core-v1.json`, with 514 cards: 503 CPU and 11 GPU.
The CPU Qwen consumer also waits for held GPU prerequisites. The native queue uses
one-pass topological order and worker gate checks; all paths are registered before
launch. The plan hash is
`dadc4e159d69f657e7b3c3a62862bacb57e6c0e1a14e6440f17d28d888168f78`.
Source bundles are immutable. Root code edits after launch do not repair a frozen run.

| Study family | Implemented scope | Execution disposition |
|---|---|---|
| A: provenance and located contribution | Released e5, named causal likelihood/log-rank variant, surface rivals, cross-fitted located features, equally costly direct features, separate calibration, fixed development selection, reserved consumer | CPU core running; full RoBERTa-base tuning/evaluation prepared and held |
| B: human contribution | CoAuthor source prior, exact/retrieval and linked candidate alternatives with severed/shuffled coupling; ScholaWrite annotator-purpose and exact-edit-operation coupling | CPU comparisons queued; primary Qwen interface and main comparison held |
| C: confidence and context | Named small CPU reader's conditional scoring versus literal elicitation, calibrated likelihood, raw/linked/answer memory and misleading/duplicate/omitted-candidate controls | Own admission gates; unavailable independent memory stays explicit |
| D: retained-record texture | Complete ARIES direction/view and reserved-paper analysis with cheap diff rival; revision interaction against unchanged/irrelevant movement; requested versus realized features | Read-only historical outputs, descriptive CPU consumers queued early |
| ToMpathy bridge | Source-bound UTF-16 locations, independent goal support, exclusive processes, unknown values and lossless sidecar | Actual isolated capture/parser/matcher checked; no service rebuild or native side-panel claim |
| Conditional transfer | Existing native Ghost export identified read-only | No Stage 13 target/evidence admission yet; no sibling edits, new world or queue |

The original-training capacity run measured 112.39 wall seconds for e5 and 1377.11
for the causal scorer, each over 256 rows including load/write time. Core detector
work projects about 92.7 hours, before other consumers and runtime variation.
The prepared extension fixes 22,940 additional rows from 1,356 unused original test
components and adds about 37.1 detector hours. This exceeds the remaining eligible
capacity by more than 1.25 in total without padding. It is **conditional**, not a
promise to run every card. A later gear change changes resource admission, not the
source allocation, outcome rules or absolute end.

## Next operational actions

1. Inspect `raw/queue/core-v1/OWNER.json`, actual native PID plus creation time,
   `STATUS.json`, current job `DISPATCH.json` and fresh progress. Preserve unknown
   attempts until reconciled. Never kill by stale PID or restart beside a live owner.
2. Completed cells: verify immutable outputs and cards; replay the applicable consumer;
   make the full FINDINGS, theory/instrument, TODO and provenance landing. Keep
   unfinished per-artifact scores private. ACK each event only after this landing.
3. Health event: inspect native identities, progress, failures, locks, resources,
   eligible work and watcher delivery. Document and recover within authority before
   ACK. The health ACK rearms four hours later; unrelated ACKs do not defer it.
4. At core completion or the independent health inspection, reconsider
   `raw/plans/reserve-extension-v1.json`. It needs the complete core reserve consumer,
   identical selection/calibration, source pins and enough measured time for the
   **whole** extension. Its minimum guard is 45 hours before the reporting boundary.
   If it cannot fit, record time-deferred; do not cherry-pick favorable subblocks.
5. A future explicit gear change can admit the prepared GPU jobs only after ownership,
   headroom, deadline and native model admission are checked. The current coordinator
   captured `--no-gpu` at startup, so changing an allocation file alone does not queue
   those cards. Arrange a nonoverlapping scoped pass at a natural boundary; never use
   the unrestricted historical gear launcher. Completed produces reenter without calls.
6. Use the same frozen source capsule for a subsequent queue process. The entry sets
   `SL_STAGE13_REPO` to the repository, adds the project venv packages and the capsule
   to Python's path, appends the repository's runners path for existing read-only
   dependencies, and calls `runners.stage13.queue --plan <exact plan>` with the native
   interpreter. Validate every plan/card/source pin before launch and register its
   actual OWNER/EXIT/FAILED with the existing watcher. Root code alone is not the capsule.
7. At reporting-start, assemble complete comparisons and explicit deficits, costs,
   source units/calibration, examples, pursuit/warrant ledgers and at most three
   consequential questions. Deliver one final curator packet by Friday 05:00 PDT.

## Validity limits to retain

Human sources are historically exposed. CoAuthor has one connected component per
partition, no independent mental-goal truth and no natural public-context arm.
ScholaWrite purposes are annotator labels; source identity across projects and near
copies are unresolved. Source-invalid OpAI locations are retained but ineligible as
location truth. Coarse window contribution masks are not full histories or mental goals.
The exact released DAMASHA architecture import failed because `torchcrf` is absent;
no checkpoint forward/reproduction is claimed. Do not install into the live environment
or replace it silently. Independent-memory requirements can be unavailable rather
than repaired with a same-source duplicate. Primary Qwen and the full trained rival
remain missing until actually admitted and completed under authorized resources.

The native queue and immutable-output regressions, known-answer scoring and location
controls, complete detector fit/calibration/reserve rehearsal, and exporter checks
pass: 23 focused tests. All 21 original locks pass. Preserve the earlier failed source,
consumer and browser harness attempts as implementation history.

[Rollout receipt](../../../results/phase_2_4_stage_13/ROLLOUT.json) and
[health receipt](../../../results/phase_2_4_stage_13/HEALTH_20260927_1519.json)
contain the operational evidence without human passages or unfinished scientific scores.
