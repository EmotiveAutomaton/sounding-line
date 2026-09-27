# Stage 13 implementation plan

Prepared September 27, 2026. **Reviewable plan; implementation and launch pending.**
The [supplied brief](WEEK_RESEARCH_SOUNDING_LINE_2026-09-27.md) defines the experiments.
This plan translates it into repository work; it adds no scientific verdict or new
research proposal. The current owner instruction controls: Gear 1, no rollout until
go-ahead. No paid compute, recruitment, author contact, delegation or product release.

## Intended result

Produce complete, reproducible comparisons addressing three questions: whether AI
detection improves against strong rivals, whether specific located contributions are
recovered, and whether linking candidate goals and processes helps. Keep artifact-only,
public-context, revision and process-record evidence separate. Report unavailable
comparisons directly. A new interface does not repair an old failed result.

The brief is sufficiently specific to implement without a major design decision.
Local admission still must establish data rights, usable independent source groups,
model/checkpoint compatibility, response validity and measured throughput. These are
implementation checks, not facts established by this documentation pass. External
method claims remain attributed to the supplied reading register until the relevant
primary source and exact implementation are inspected during approved setup.

## Gear 1 and the five-day clock

Gear 1 means one bounded job at a time, limited CPU use and the GPU mostly available
to the owner. Begin with serial CPU intake, exact alignment/diff, cached-output replay,
light statistical fits, calibration and report assembly. Initial numerical thread cap:
one; below-normal priority. Preserve boost disabled and 90% maximum processor state.
Do not close applications, increase power limits or use cloud compute as a fallback.

Full RoBERTa tuning and sustained Qwen inference are **held under Gear 1**. Prepare
their cards and mark them resource-deferred. A short GPU admission probe is eligible
only under an explicit Gear 1 policy with fresh headroom and a bounded release; until
that policy is reviewed at implementation, default to no GPU dispatch. An admitted
CPU reader may run only if measured responsiveness and whole-block time fit. A smaller
model or alternate readout needs its own admission and remains a named variant.

This changes achievable throughput, not the question or the required comparator.
Report a missing trained comparator as missing; do not substitute a cheap baseline
and call the competitive comparison complete. Preserve the A/B/C/D compute priorities
from the source, applied to eligible work. Plan four to eight hours of light runnable
work in Gear 1, with a larger dependency-aware backlog. The source's 24–36-hour active
GPU runway is a Gear 2 assumption, not a reason to consume the owner's card.

After approval, record setup start; aim for readiness within 24 hours. Readiness
requires an admitted complete A or B block, tested consumers and working ownership,
resource and wake controls. Agree one shared readiness timestamp and fixed 120-hour
research endpoint with the Ghost owner; no writes to that repository in this task.
A blocked Ghost branch must not hold an otherwise viable Sounding core. If Gear 1
cannot admit a valid core, report the blocked capability and continue useful eligible
preparation; do not claim that the research window has begun or silently upgrade gear.
Keep the final eight hours for small complete blocks, replay and the final packet.

## Code and data layout after approval

Create `runners/stage13/` and `tests/test_stage13_*.py`; keep Stage 11/12 execution
sources and frozen raw records intact. Use `results/phase_2_4_stage_13/raw/` for private
human text, source identities, requests, responses, evaluator data and source capsules.
Publish only safe aggregate receipts, manifests without private text, and the report
under `results/phase_2_4_stage_13/`. Do not reuse an expired contract or old output path.

The table assigns planned components to existing implementations and their required
new behavior. Names are proposed, not currently callable commands.

| Planned component | Reuse inspected in the repository | Work and acceptance boundary |
|---|---|---|
| `contracts.py`, `prepare.py` | Stage 12 immutable plans/cards, source pins and native worker pattern | New campaign identity, approval state, absolute clock, Gear 1 allocation, complete-block manifests and explicit dispositions |
| `sources.py`, `splits.py` | Stage 11 retrospective preparation; Stage 12 CoAuthor, ARIES and ScholaWrite projections | Rights/hash inventory, episode-boundary assertions, exposure ledger, connected lineage allocation and evaluator separation |
| `detectors.py` | Existing sklearn/Transformers environment and cached causal scorers, subject to admission | Surface rival, statistical scoring, pinned released detector and separately held full-tuning arm; label orientation and operation/coverage confounding retained |
| `reconstruction.py`, `scoring.py` | Stage 11 source reconstructor and immutable response replay; Stage 11.1 compact readout lessons | Matched direct, retrieval, exact alignment, joint candidate/execution/scoring and coupling ablations; candidate coverage scored separately |
| `calibration.py`, `context.py` | Stage 12 primary analysis and revision replay | Separate calibration fit, unknown support, all-attempt utility, conditional accuracy, context/memory interventions and deterministic lineage resampling |
| `queue.py`, `worker.py` | Existing native queue, process identity, singleton/GPU guards and durable watcher | Topological eligibility, independent failure continuation, resource holds, no blind retries, complete terminal/exit registration |
| `report.py`, `export_tompathy.py` | Stage 12 provider/casebook and existing ToMpathy offline packet contract | Semantic replay, one final packet, safe aggregates and source-bound offline export with lossless sidecar |

Preserve `ReadingProfile.ClaimBoundary.provenance`. Put separately evaluated detection
in a versioned outer schema. Retain nonexclusive goal support or coherent goal sets,
exclusive process alternatives, unknown support and typed compatibility links. Separate
recorded facts, inferred alternatives and unavailable evidence. Values remain unknown.
No authorship-share scalar, no forced goal normalization and no free-form generated
program execution. Human-text consequence scoring remains a learned model, not exact law.

## Build order and dependency gates

1. **Recover the scientific and operational context.** Finish any unread current
   theory sections in the prescribed order; reread relevant afterwords/corrections,
   method lessons and exact source implementations. Bind Stage 12 final obligations
   separately. Inventory current model/data caches and pin only admitted assets.
2. **Freeze sources and targets.** Admit a bounded OpAI-Bench release with documented
   rights and actual counts; fallback to eligible cached MAGE/RAID if the intake fails.
   Keep CoAuthor as a contribution source, not a replacement detector benchmark.
   Audit writers, sessions, prompts, documents, trajectories, generator siblings and
   near duplicates. Separate train, development, calibration and reserved connected
   components before method outcomes. Mark all previously exposed groups.
3. **Build consumers before producers.** Validate positive, negative, ambiguous,
   malformed, missing and mislocated examples; semantic replay must reproduce raw
   parsing and scores. Assert actual retrospective episode boundaries, exclusion of
   future/evaluator fields, literal-invalid accounting and complete-history deficits.
   Add regression cases for unordered bootstrap units and JSON round-trip changes.
4. **Admit one complete core.** Benchmark actual loading, all baselines, producer,
   consumer, writes and replay together. Start with the source's exact/cheap rivals
   and one eligible reader. Check real tokenizer, response interface and second entry.
   A fake transport rehearsal cannot admit the model. Missing necessary rivals hold
   that comparison while an independent eligible branch proceeds.
5. **Rehearse the real queue.** A prerequisite completing after a blocked successor
   must make the successor eligible; failed admission must not strand independent
   work. Test Gear 1 GPU refusal, owner pause, interrupted/unknown dispatch, released
   locks, duplicate ownership, timeout, terminal recognition, output tampering and
   byte-stable completed reentry. Prove queue exit emits an actionable event if eligible
   work remains. The existing Stage 12 wrapper enumerates cards once; do not copy its
   dependency-order limitation into the new campaign.
6. **Launch the first eligible complete block after approval and admission.** Record
   native identity, source pins, limits, terminal paths, timing estimate and watcher
   registration. Verify actual progress and output freshness once. The durable watcher
   then owns waiting; preserve the independent four-hour health deadline. No extra
   polling agents or repeated model turns for a healthy worker.
7. **Expand only through declared successors.** Additional independent sources,
   domains/generators, matched direct computation, robustness and reserved replication
   are the useful expansion order. Build a conditional backlog at least 1.25 times the
   measured five-day eligible capacity. Do not pad runtime, revive expired studies or
   promise a GPU-hour total from request counts.

## Scientific blocks retained from the brief

The rows are complete comparisons to construct, with controls and stop dispositions.
All are pending implementation; a held resource or missing source stays visible.

| Branch | Complete comparison and consumer | Continuation / failure disposition |
|---|---|---|
| A: detection and located contribution | Surface, calibrated LM score, admitted public detector, held full-tuned rival; baseline alone versus validated reconstruction features versus equally costly direct features; separate operation and strict/relaxed location scores | Rights/overlap failures select the declared source fallback. Failed detector intake leaves a missing competitive comparison; contribution work may continue independently |
| B: retrospective goals and processes | Source prior, exact alignment/diff, retrieval, matched direct and joint method; removed goal coupling, removed execution and shuffled association; equal candidate support | Coverage failure permits one bounded development proposal repair; scoring failure permits one scorer/readout repair. Privileged-record-only success retains that evidence boundary |
| C: calibration, context and memory | Compact scoring versus elicited confidence; no memory, raw retrieval, linked evidence memory and old-answer text; informative/irrelevant/misleading/duplicate evidence, wrong locations and omitted true candidates | Compare benefit and harm at matched evidence/cost. At most one later information-acquisition study, only after a valid core and complete consumer |
| D: retained-record diagnostics and bridge | ARIES direction/view/reserved-paper analysis and diff rival; revision contrast adjusted for unchanged/irrelevant movement; requested-versus-realized exact checks | CPU-first, capped near the source's 5% compute share. Optional LP16 reuse requires a new commission wrapper and competes on value/time; original unrun record stays unrun. Ghost supplies only an independently admitted bounded transfer |

Use the specified RoBERTa-base recipe and pretrained e5 detector as admission defaults,
not installed or validated facts. DAMASHA gets one exact checkpoint/architecture smoke
attempt; a causal-LM substitution for Fast-DetectGPT remains a named variant. No paid
generation commands. Full tuning stays held under Gear 1 even if downloads succeed.

Freeze the actual promotion margin and precision target before reserved outcomes.
The source's +3-point detector margin is a proposed development rule. Primary detector
thresholds are selected on independent human calibration data for 1% and secondary 5%
false-positive targets; report achieved rates and uncertainty, not unsupported precision.
Use source/lineage units for intervals and disclose the minimum resolvable rate. Fit
cross-fitted reconstruction features on training/development only, calibrate separately,
and freeze at most two finalists. Open reserved blocks once. Keep location, operation,
dependency and probability losses separate; token overlap alone cannot select the winner.

## Recovery, reporting and integration

One development interface correction and one implementation correction per method
family, preferably at most two active operator-hours each. Preserve original invalids,
timeouts and costs. A second failure switches to an already prepared independent branch.
Unknown dispatch requires reconciliation, never blind replay. Each job must fit its
conservative duration plus consumer before the reporting reserve. The horizon does not
reset on resume; stopped or blocked work receives a reason, never a success marker.

Check reused interfaces with focused Stage 11/12, output, capacity, native identity and
watcher tests, plus new Stage 13 lineage, consumer, readout and queue regressions. Do not
run an unrestricted old gear launcher: it may dispatch unrelated historical TODO work.
The scoped plan is the only dispatch source. Keep actual CPU time, GPU service, elapsed
wall time, utilization and every incurred attempt cost distinct.

After completed scientific cells, perform full internal FINDINGS, theory/instrument,
TODO and provenance write-through. Present one final curator packet with the three
practical answers, complete comparison/deficit table, costs, independent units, calibration,
source-selected and explicitly outcome-selected examples, pursuit/warrant ledgers and
at most three consequential questions. Preserve Stage 12's independent final packet.

For ToMpathy, inspect its then-current parser/matcher before building an offline v1
exporter here. Start from a real exported capture; preserve exact text, UTF-16 anchors,
artifact/revision/region IDs and imported origin. Use separate context identities and
per-region hypotheses where weights differ. Keep I1/I2/I3 visibility and evaluator
exclusion explicit, with detector outputs, graphs and intervals in a lossless sidecar.
Validate import/matching and inspect actual success, error and ambiguity if available.
No frontend or service rebuild and no claim of arbitrary-page live inference.

## Approval boundary

Approval of this plan would authorize implementing the scoped local Stage 13 components,
their admission tests and eligible Gear 1 execution within the new five-day contract.
It would not activate held heavy GPU work, paid compute or another repository's queue.
At present, only documentation organization and this plan are complete. The next action
is the owner's go-ahead, followed by source/consumer setup; no research has launched.
