# DC1: slopes for feelings, levels for acts

Status: runnable source/analysis handlers, array estimators, explicit timing
projection and constructed checks prepared. Human production is held for owner
review of timing/control mapping. The optional empirical-null references below
are not additional inherited admission gates.
Authority is [the supplied packet](PACKET.md), section 3C. DC1 inherits RR3's
10,000 CPU-second card ceiling and the 120,000 CPU-second MD family ceiling,
under the [execution addendum](EXECUTION_ADDENDUM.md). Existing TR1/RR3 files remain unchanged.

## Source and timing contract

The population is the explicit intersection of the frozen prospective TR1 and
RR3 person rosters, with complete coverage in their common source. Record
both parent-only populations and source extras. Every common person must have
exactly one actual first play; missing first plays cannot be replaced by a later
observed play. Repeat plays belong to the secondary, never the primary.

TR1 prospectively requires at least two observed completed plays, all
repeat-eligible, with strictly increasing actual counters. RR3 inherits RR1's
fixed actual-attempt-1/2/3 cohort and any frozen whole-person sample. Later TR1
full/half-fit support and RR3 informative-logistic support are separate diagnostic
facts. They cannot remove a prospective roster member from DC1. The source
wrapper reproduces TR1's supported-pair counts against its completed parent and
records a separate per-person flag. Constant-choice people remain legal for the
pooled linear probability model; unsupported individual slopes get separate
dispositions. Both primary targets use the exact same approved paired occasions.

`runners/drive/cards/week6_dc1_v1.py` calls the unchanged RR3 recent-luck helper
and dynamic-history feature helper. RECENT is the mean of the last up-to-three
completed actual outcomes minus the chosen offer's expected value. It is strictly
lagged for a choice. LEVEL is the positive distance above the play's starting
score; below-start distance remains a separate control and reported coefficient.
All nine original RR3 scales must be provided, and below/above use the identical
standing scale. No new population-specific feature scaling replaces those pins.
TR1's decaying rating-sensitivity term remains a distinct secondary instrument.

The initial stored rating occurs before trial 1; later stored ratings occur after
their row's outcome. The prepared timing table pairs the rating immediately after
completed trial k with next-choice row k+1, using only history through k. It keeps
the initial no-history rating and final no-next-choice rating as explicit excluded
dispositions. Every retained row carries the rating index, next-choice index and
last history index. A fixture mutates all later outcomes and requires the earlier
paired predictors to remain unchanged.

Three inherited RR3 offer controls use the *next* trial's offered values: positive
sure offer, negative sure offer and gamble-minus-sure expected value. Their
availability when the previous rating was supplied is not assumed. The owner
explicitly requested review of these fields and the common eligible occasions
before a human outcome. The projection always returns `production_admitted=false`
with this hold. The analysis handler requires an owner receipt resolving all
three flags for the exact source and implementation. Removing
these controls or shifting the ratings silently would change the specified fit.

## Estimator and reporting

Both outcomes use person-intercept ordinary least squares on the same approved
occasion table. The rating and binary next choice are each standardized, with
sample standard deviation and complete-person resampling. The choice model is
a linear probability model on standardized zero/one outcomes. Passing a
continuous synthetic choice to the primary raises an error.

The primary has two required parts: RECENT minus LEVEL for ratings and LEVEL
minus RECENT for choices, each compared with 0.05. A large sum cannot substitute
for either part. Each part retains its own cluster interval, sensitivity estimate
and outcome class. Two thousand complete draws are required. Failed draws remain
failed and invalidate uncertainty; they are not deleted or redrawn. Fewer than
20 people or a degenerate bootstrap remains descriptive. Exact per-person normal
equations reproduce the rowwise estimator and support bounded resumable draws.

The prediction helper keeps people disjoint between training and test, learns
scales on training data, and retains the other RR3 controls in each one-term fit.
For unseen people the rating intercept is the training population mean. The
choice prediction uses C=1 regularized person-intercept logistic regression and
reports mean log score. These are explicit prediction conventions for owner
review, not an unnoticed replacement of the primary linear model. Report any
coefficient-versus-prediction disagreement directly.

The person-level correction primitive divides the observed slope correlation by
the square root of the admitted TR1 stability. It corrects the rating side only,
does not invent a choice reliability and retains corrections outside [-1,1].
Nonpositive stability or absent between-person variation is unsupported.
The source adapter prepares the original twelve-occasion TR1 inputs and all
29 lagged first-play choices. The analysis handler reconstructs the original
rating slope and each complete-control standardized choice slope, preserving
unsupported-person dispositions. The parent stability is a fixed descriptive
correction; its uncertainty is not propagated. Both repeat references use the
unchanged earlier-score mapping and separate person-bootstrap banks: play start
and best observed earlier score. Missing reference membership fails preparation.

## DESIGN CHECK

LESSONS sections 2 and 3 were read. The supplied ZIP's `fixtures/fixtures.py` was
read before any use; it was not executed. Its DC1 example generates *continuous,
unstandardized* rating and choice outcomes. `preflight_reference` reproduces
that exact construction independently using least squares with an intercept.
Its summed contrast is solely a reference arithmetic check, not the standardized
binary primary target or an alternative primary.

A separate balanced factorial construction supplies binary choices with known
probabilities and unit-variance ratings. It recovers each standardized part
against an independently derived finite-sample target. Equal planted loads give
zero parts. Dense person-dummy least squares checks the within-person formula;
whole-person multiplicities check the sufficient statistics. A constructed bank
where one part passes and the other reverses must fail the joint requirement.
Roster coverage, duplicate/missing first plays, initial/final occasions and future
outcome leakage have explicit failure tests.

The support fallback is a pooled description below the inherited cluster floor;
the timing hold is a design/admission hold and cannot be relabeled a scientific
null. Cost overflow follows the existing whole-person sample route, with frozen
selection before outcomes and explicit sample scope. Tags: `H17-T1`; the eventual
claim must state that choices repeat RR3's comparison and the running score is
displayed. Neither historical source terms nor inherited control obligations are
waived by this new comparison.

## Runnable handlers and exact parent receipts

These existing dependency roots are relative to
`results/phase_2_4_stage_15/raw/drive-week5-20261107/`. COMPLETE hashes and VERIFIED
metadata were inspected; their participant arrays were not opened by this build.

| Dependency | Root | COMPLETE SHA-256 |
|---|---|---|
| TR1 | `TR1-independent-replay-continuation-2-20261113` | `8b5906f9723d08985e6bc8fac5bf5d682743082cc9e444f7b40d6a4398badb8e` |
| RR3 | `RR3-recent-outcome-full-continuation-2-20261113` | `33f8667c70234391dacca838079637b4e85f7118f71756f0bfdc6570c4ddaa1b` |
| RR1 | `RR1-actual-attempt-continuation-1-20261111` | `65fb37c1e4e5dda4c36cd472fe1b9b5e656932dabdcbc80e81b47faf89305d8d` |
| Common source | `MD-source.h1` | `c25ca260750e4e4d46a2a962af1c68c80b968352ed2d4a0e2c71422378eee383` |

TR1 and RR1 both bind `MD3-first-gear-continuation-3`; their common task is
`MD-source.h1/output/task.npz`, from `corpora/store/external/rutledge_gbe`.
Preparation authenticates completed producers and every sealed output, the
repaired source's archive/matrix/task pins, identical task bytes and frozen scales
through the unchanged parent authenticators. No parent files are modified.

`runners.drive.cards.week6_dc1_source_v1` supplies bounded `execute`/`verify`.
Inputs are `tr1_run` and `rr3_run` at the roots above. Configuration:
`{"phase":"DC1-prepare","max_new_blocks":4,"max_wall_seconds":600}`.
Each block preserves 128 whole people, primary/repeat rating dispositions and
person-source arrays. No new DC1 outcome regression occurs during preparation;
the frozen TR1 support rule is replayed only as a distinct diagnostic.

`runners.drive.cards.week6_dc1_runner_v1` supplies bounded `execute`/`verify`.
It requires `prepared_run` and an owner-written `owner_review` matching
`review_contract()`, including confirmed availability of all three offer controls.
Configuration:
`{"phase":"DC1","draws":2000,"max_new_draws":100,"max_wall_seconds":600}`.
Primary and both repeat banks checkpoint separately, followed by prediction and
descriptive person rows. Fresh replay compares every field. The dense independent
estimator oracle is a fixture; a second native optimizer is not claimed.

## Construction corrections, checks and remaining holds

### Inherited-control audit, before admission

[Week 3 section 0.5](../week3/PACKET.md) requires a null that can fail each
measure, at least 200 within-writer permutations, and at least 1,000 writer-label
permutations within prompt for reliability and identification nulls.
[Week 4 section 0.5](../week4/PACKET.md) repeats the 200-permutation default.
[Week 5 section 0.6](../week5/PACKET.md) explicitly carries Week 4 defaults in
its CoAuthor-timing clause. On review, the owner confirmed that this restricted
carry-forward does not impose the older generic permutation minimum on new
DC1. DC1 has its own constructed-null fixture. The earlier builder audit
incorrectly promoted the generic minimum to an additional admission gap; this
records the correction before any human run. Q, U and AA do not waive controls
that actually apply, but no waiver is needed for an out-of-scope default.

This table separates implemented controls, dependencies and optional references.

| Requirement or control | Exact implementation or remaining gap |
|---|---|
| RR3 terms, scales and strictly past history | `week6_dc1_v1.timing_table` calls the unchanged RR3 helpers; source authentication binds original scales and source bytes. No future outcome is used. |
| Common fixed roster and common primary occasions | `week6_dc1_source_v1.tr1_membership`, `common_roster` and the timing dispositions; fit-support flags never select prospective membership. |
| All RR3 controls available at the rating | Explicitly **unresolved** for the three next-offer controls. `review_contract` requires a separate owner resolution before any fit. |
| Person intercepts, both contrasts and whole-person uncertainty | `primary`, `sufficient_statistics`, `bootstrap_draw` and runner `operation`: 2,000 draws for each primary/repeat panel, no redraw of failures. |
| Held-out prediction with retained controls | `prediction_row`; person-disjoint folds and training-only scaling, under the separately reviewable prediction convention. |
| Known-answer alternative and null | Binary standardized finite-sample constructions, dense estimator reference, equal-load null and one-part-fails regression. The supplied continuous fixture is separate reference arithmetic. |
| Within-unit permutation sensitivity | **Optional, not implemented; not an inherited admission gate.** Naive within-person shuffling is not justified for dependent trial histories. A future sensitivity must preserve the source's temporal and common-occasion contract. |
| TR1 stability dependency | The completed parent's qualification and interpretable-variance gate are authenticated; DC1 consumes its fixed stability. It does not re-estimate or requalify TR1 reliability and does not propagate that estimate's uncertainty. |
| Person-label reliability/identification null | **No new bank exists or is required for the commissioned descriptive row.** DC1 consumes fixed qualified TR1 stability and reports a descriptive corrected person-slope correlation; it makes no new reliability or identification inference. A future inferential extension would need its own reviewed design and applicable controls. |

The RR3 design's complete constructed null chain and TR1's three planted
stability worlds qualify those parent estimators. Neither is a new empirical
permutation bank for DC1's paired rating/choice comparison. The parent mood
control history remains unchanged; importing its source does not pronounce a
new rating estimator qualified. No new scientific controls are waived by the
source wrapper or by a small-card admission route.

An optional restricted whole-person wild-score reference was proposed for the
two coefficient differences: fit each equality-constrained null with the other
controls retained, multiply each person's complete score vector by one shared
sign, and reconstruct the fits from cross-products. It would test the
observational projection under independent-cluster assumptions, not randomize
trials or create counterfactual binary choices. It is unimplemented and would
need separate review/qualification if commissioned. It replaces neither the
packet's intervals nor the two required parts and creates no admission gate.

The runner's completion fields mean completion of its implemented primary,
repeat, prediction and descriptive person operations. Its review receipt does
not attest an optional null bank. No permutation transformation, new inference
for the person row or additional threshold has been adopted.

A source review briefly changed TR1 membership from its prospective roster to
supported-pair membership. The owner clarified that the packet means prospective
membership; that change was corrected before human preparation or fitting.
Supported-pair membership remains diagnostic. The regression requires that an
unsupported middle play cannot bridge its neighbors, and that failure of this
fit-support gate cannot remove the person from the prospective roster. Earlier
receipts remain retained. Exact-bootstrap degeneracy was also repaired without
changing the estimand or gate, as recorded in [LA6](LA6_V1.md).

The changed-source suite passed 24 checks. The final prospective-roster correction
then passed all nine source-wrapper checks. Latest receipt:
`.agent-state/drive-20261115/week6-builder-c-checks/BUILDER_C_ROSTER_CONTRACT_TEST_RECEIPT.json`.
The initial, failed, repaired and source-final receipts remain beside it. All
checks were constructed, limited to two numerical threads, with no human source
loading. They exercise direct handlers and arrays, not new native research jobs.

Remaining: owner control-availability, paired-occasion and prediction-convention
review; the person-secondary interpretation boundary above; committed design,
versioned Week 6 runtime admission
and in-slot cost. No approval receipt has been written by the builder. If an
offer control is unavailable when the rating was supplied, a reviewed design
resolution is needed; code cannot silently drop it. No human DC1 estimate has
been computed.

### Reporting correction and current-byte check

The old reporting helper treated `band-null` as a fourth scientific outcome and
required an interval wholly beyond minus the bar for `against`. Before admission,
the owner required the generic three-way rule: each unchanged contrast supports
only when its interval is strictly above 0.05; it is against when wholly opposite
zero or wholly within [-0.05, 0.05]; otherwise it is inconclusive. The two required
parts and their joint requirement are unchanged. A band-contained interval may
describe the reason for `against`, but is not a separate outcome. Descriptive
floor/degeneracy statuses remain separate and have no scientific outcome.

The 22 boundary/summary checks in `tests/test_week6_outcome_labels_v1.py` passed
against current reporting bytes. No fit or earlier full bank was repeated; all
nonreporting function ASTs match the preserved pre-repair versions. The original
bytes, initial and expanded manifests, failed and passing numeric receipts,
and `BUILDER_C_LABEL_TEST_RECEIPT.json` remain in the private builder directory.
The label receipt's CPU field measures only its Windows launcher; the separate
accounting note prohibits treating it as the full process-family charge.

### Cost forecast and pilot boundary

No human-source cost measurement has been made. A complete execution has three
panels, each with two target fits and 2,000 whole-person draws of both targets:
at most 12,006 small sufficient-statistic solves, plus construction of the
statistics, held-out prediction, individual descriptive slopes, checkpoints and
source authentication. Complete replay repeats every panel and secondary.
The prediction and person rows need separate timing; a cheap primary prefix
cannot price those later phases. Failed or unsupported panels remain explicit.

The first in-slot cost stage must include these fixed/late costs and replay in
its forecast. The default 100-draw invocation is 5% of one panel's bank; all
three panels need representation before extrapolating the full draw workload.
If the forecast exceeds 7,200 CPU-seconds, use a checkpointed first-5% pilot
under the same card rather than a separate allowance. A 600-second cooperative
bound checks between draws/panels, not inside an atomic solve or prediction
block; native resource guards remain necessary. The 10,000 CPU-second card and
120,000 CPU-second MD family ceilings include preparation and failed attempts.
No source-specific production forecast or admission is inferred from the small
constructed fixtures.
