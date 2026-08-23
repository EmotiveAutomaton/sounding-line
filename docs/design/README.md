# docs/design — blueprints and build rationale, read when picking up the build

The split from `../method/`, since the two invite confusion: **method binds, design briefs.**
A method file is normative for every test, every day, trigger-indexed and read before designing
or building anything (its README maps the moments). A design file is the blueprint and rationale
for one thing we intend to build, dormant until that build is scheduled, and then it is the
brief. Merging them would put binding procedure and dormant blueprints in one index and dilute
the trigger discipline (the call made 2026-08-14, at the curator's prompt).

## Current orientation (2026-08-22)

- **Current phase:** [`PHASE_2_4_CONTEXT.md`](PHASE_2_4_CONTEXT.md) with
  [`PHASE_2_4_EXPLORATION_ADDENDUM.md`](PHASE_2_4_EXPLORATION_ADDENDUM.md) (ratified
  2026-08-22, continuous second gear); live registry
  [`PHASE_2_4_REGISTRY.md`](PHASE_2_4_REGISTRY.md), which also carries the Phase 2.3
  closure dispositions (audit-interface product deferred, not dropped)
- **Stage 1 complete 2026-08-22 (L161-L163); the frozen curator deliverable is
  [`PHASE_2_4_ROOT_MAP.md`](PHASE_2_4_ROOT_MAP.md)** — Stage 2 opens on the curator's
  walkthrough; two sealed scouts sit in the registry's ledger
- **Theory application order:** the Phase 2.2 errata (applied 2026-08-20), the Phase 2.3
  errata (theory delta applied 2026-08-21), then the Phase 2.4 errata (applied 2026-08-22)
- **Live work:** [`../../TODO.md`](../../TODO.md) and `runners/run_queue.py`
- **Empirical state:** [`../STATE.md`](../STATE.md) and [`../../FINDINGS.md`](../../FINDINGS.md)

## Status legend

| status | meaning |
|---|---|
| **OPERATIVE** | controls current design and execution where it speaks |
| **APPLICATION PENDING** | a requested reconciliation package not yet fully folded into its canonical owners |
| **REUSABLE SUBSTRATE** | parts remain active infrastructure or construction guidance; the file does not control the current theory or phase objective |
| **DRAFT — DO NOT FREEZE** | incomplete contract whose current form is known to conflict with the operative phase |
| **DEFERRED** | valid design, not currently scheduled |
| **HISTORICAL PRECURSOR** | preserved design reasoning absorbed, narrowed, or superseded by a later package |
| **SUPERSEDED SNAPSHOT** | no present authority; retained for chronology and rationale |

("Archived" is reserved for `docs/archive/`; a file that stays here takes one of these labels.)

## Authority table

| file | status | read it for |
|---|---|---|
| [`PHASE_2_4_CONTEXT.md`](PHASE_2_4_CONTEXT.md) | **OPERATIVE** | shared-architecture inversion and affective-prior engineering: G172-G180, claim ladder, rival worlds, the flight standard |
| [`PHASE_2_4_EXPLORATION_ADDENDUM.md`](PHASE_2_4_EXPLORATION_ADDENDUM.md) | **OPERATIVE** | the two-lane discipline: confirmatory trunk vs discovery forest, automatic branch policy, closure rules |
| [`PHASE_2_4_REGISTRY.md`](PHASE_2_4_REGISTRY.md) | **OPERATIVE** | the live 2.4 registry: root states, scout registry, firewall, and the 2.3 closure dispositions |
| [`PHASE_2_3_CONTEXT.md`](PHASE_2_3_CONTEXT.md) | **HISTORICAL PRECURSOR** (Stage 1 complete; Stage-2 branches absorbed or deferred per the 2.4 registry) | the adaptive process-inversion program: seven wing roots, branching discipline, reporting protocol |
| [`PHASE_2_3_REGISTRY.md`](PHASE_2_3_REGISTRY.md) | **HISTORICAL PRECURSOR** (closed at the 2026-08-22 ratification) | the Phase 2.3 root states and the reconciliation against the live head |
| [`PHASE_2_3_THEORY_AND_DESIGN_ERRATA.md`](PHASE_2_3_THEORY_AND_DESIGN_ERRATA.md) | **HISTORICAL PRECURSOR** (theory delta and design reconciliation applied 2026-08-21, commits `91f887d` and this pass) | provenance for the reconstructed curator language and the authority-layer repair |
| [`PHASE_2_4_THEORY_ERRATA.md`](PHASE_2_4_THEORY_ERRATA.md) | **HISTORICAL PRECURSOR** (applied 2026-08-22) | provenance for the five reader-qualified-invertibility quotes and the three prose corrections: model vs engineered human-shaped vs human invertibility, similarity as shortcut, 27 as soft ceiling |
| [`PHASE_2_2_CONTEXT.md`](PHASE_2_2_CONTEXT.md) | **HISTORICAL PRECURSOR** | the transition from binary attribution to reconstruction profiles; ruler gates; result routing |
| [`PHASE_2_2_THEORY_ERRATA.md`](PHASE_2_2_THEORY_ERRATA.md) | **HISTORICAL PRECURSOR** (applied 2026-08-20) | provenance for the ten-quote reconciliation across the five theory owners |
| [`PHASE_2_0_CONTEXT.md`](PHASE_2_0_CONTEXT.md) | **HISTORICAL PRECURSOR** | the original vertical slice; STILL IN FORCE: curator interface (§15), escalations (§16), claims policy (§18), sub-goal identifiers 2.0A-2.0H |
| [`EVAL_CONTRACT_2_0.md`](EVAL_CONTRACT_2_0.md) | **DRAFT — DO NOT FREEZE** (v0.3 reconciliation in place) | the single evaluation contract: reconstruction-profile primary task, metric panel, split and calibration discipline; the binary form survives only as the optional downstream product layer |
| [`ADJUDICATION_SET_2_0.md`](ADJUDICATION_SET_2_0.md) | **HISTORICAL PRECURSOR** | the unfrozen binary adjudication exercise, superseded as ontology (its file carries the ruling) |
| [`BENCHMARK_2_0.md`](BENCHMARK_2_0.md) | **REUSABLE SUBSTRATE** | process-record, lineage, licensing, matching, and manifest construction; the contribution-process decomposition |
| [`HUMAN_NEGATIVES_2_0.md`](HUMAN_NEGATIVES_2_0.md) | **DEFERRED** | human-negative sourcing design for the product layer, behind the process-output validation |
| [`SUCCESSOR.md`](SUCCESSOR.md) | **HISTORICAL PRECURSOR** | the pre-Gate-3 anomaly/reconstructibility design absorbed into the current program |
| [`DWELL_CORPUS.md`](DWELL_CORPUS.md) | **DEFERRED** | the controlled same-maker/two-form corpus, if the dwell question reopens |
| [`ENGINEERING_LOOP.md`](ENGINEERING_LOOP.md) | **REUSABLE SUBSTRATE** | wide search, archive, and constraint-aware engineering principles |
| [`QUEUE.md`](QUEUE.md) | **SUPERSEDED SNAPSHOT** | the 2026-08-05 ordering rationale and measured rates only |

## Conflict and maintenance rule

Later phase packages supersede earlier packages **only where they conflict**. Empirical
results, method constraints, curator quotations, licensing constraints, and reusable
infrastructure do not become stale merely because the phase number advanced. A design file is
superseded in place with a banner, never deleted. **Results never live here**; they go to
`FINDINGS.md` and the theory store.
