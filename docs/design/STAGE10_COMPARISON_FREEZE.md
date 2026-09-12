# Stage 10 central comparison freeze

Implementation of the commissioned Stage 10 specification, September 12, 2026.
This freezes three central strategy comparisons before target evaluation answers
are opened. It does not change the study's source, task, budget or model scope.
The machine-readable receipt binds this text and the currently frozen cohorts:
[`EVALUATION_CONTRASTS.json`](../../results/phase_2_4_stage_10/EVALUATION_CONTRASTS.json).

**DESIGN CHECK.** Method LESSONS sections 3–5 and CONTROLS sections 1–6 apply.
Under no useful additional information, a paired benefit is zero or negative
once cost is counted. Under useful structure, memory or routing it can be
positive. Negative differences remain results; no positive-effect gate selects
which attempted forecasts enter a comparison. Instrument invalidity stays
visible beside both valid-only and end-to-end outcomes.

The rows name the treated reader and its central comparator. Every comparison
uses the same task, evidence view, option order and frozen output allowance;
different substrates and targets are reported separately.

| Identifier | Question | Treated reader | Central comparator |
|---|---|---|---|
| S10-EVAL-1 | Does executing proposed handling/process hypotheses improve prediction beyond spending the same output budget on direct reconsideration? | R3 executable hypotheses | R2 matched deliberation |
| S10-EVAL-2 | Does procedure memory improve prediction beyond storing concrete examples under the same storage allowance? | R4 with grounded names | R1 with the matched memory allowance |
| S10-EVAL-3 | Does development-estimated benefit and cost select extra effort usefully? | R5 benefit/cost selector | Fixed-effort policy with the same reserved budget |

R0 remains beside every table. Required secondary comparisons remain R4 versus
R3, opaque versus grounded procedure names, and confidence-only versus fixed
and benefit/cost routing. History, recipient and constraint interventions,
cheap feature/class-prior/STOP baselines, and the second-source/model checks
remain owed. They do not become extra confirmatory contrasts after outcomes.

Prediction comparisons report paired proper log scores on unmodified valid
probability vectors, generated-choice accuracy, calibration and actual cost.
A zero probability for the observed outcome has infinite log loss; do not
silently smooth it or subtract two infinities. Report finite-pair log differences
with their exact denominator and the zero-support/invalid counts beside them.
For an end-to-end finite comparison, also report half multiclass Brier loss;
invalid outputs receive its worst loss of one. Keep the valid-only proper score
and the invalid-output system penalty distinct. Generated choices and executed
probability mixtures are separate readouts.

Extra-work policy fitting retains the existing development-only half-Brier
benefit minus 0.001 per measured callback second. It requires positive
leave-one-group-out utility and at least two writer/case groups in a stratum.
Unsupported strata stop after the initial read. The current one-writer human
development allocation cannot establish general routing ability. Any engineering
selection uses development only; evaluation answers never choose a reader,
threshold, calibration transform or cohort.

Use the originally frozen allocations. Compare evidence views separately;
repeated views and calls are not independent makers. Weight human writers and
synthetic source cases equally within each reported population. Keep shared
prompt and constructor dependencies visible: uncertainty resamples connected
dependency components, not individual rows. With fewer than ten components,
report component contrasts and leave-one-component-out ranges descriptively,
without a population confidence claim. Larger populations may use a fixed-seed
2,000-draw component bootstrap. Never pool human and synthetic outcomes.

The currently exposed corpora and selected Ghost cases remain descriptive.
No confirmatory p-values or equivalence claims are planned for them. A genuinely
new, untouched cohort would require its own prior allocation and multiplicity
declaration before confirmatory language. This freeze does not claim that such
a cohort exists. Any further branch receives its exact source/roster freeze
before its outcome access, under these same three strategy comparisons.

Whole comparison cells and their controls must complete before interpretation.
Execution legality, reconstruction success, predictive benefit and historical
correspondence remain different outcomes. All required internal write-through
and the single final stage packet remain in force.
