# Phase 0 completed evidence

**Question.** Does existing evidence support the statistical backbone, and can
calibrated cloud forecasts add information beyond it?

**METHOD.** Analyze the retained main-cell paired losses with unequal-size writer
variance components; nested leave-one-writer-out calibration and stacking of all
four saved reader arms; and a session-chronological replay of every admitted
CoAuthor decision. No new inference or paid request. Outcomes are descriptive
because source data and earlier results are historically exposed.

All three cells completed. Source bindings and output hashes pass, every recorded
prequential training set satisfies its cutoff, and all saved proper-score means
replay. Three chronological model fits and one outer fit for each reader/method
combination reproduce. The native worker exited normally. Independent verification
initially found an ordering mismatch in its session-list comparison and an undefined
sample variance for a singleton writer; those verifier defects were corrected to
match the declared ordering and zero within-cluster residual. Producer outputs were
unchanged. See [validation](PHASE0_VALIDATION.json).

## T0a: decision noise and writer differences

The table decomposes the paired population-minus-backbone half-Brier loss over
234 decisions and 31 writers. Variances are squared-loss units; the intraclass
fraction is between-writer variance divided by total modeled variance.

| Component | Estimate | Maker-bootstrap 95% interval |
|---|---:|---|
| within variance | 0.013022 | [0.00805, 0.01913] |
| between variance | 0.000336 | [0.00000, 0.00155] |
| icc | 0.025133 | [0.00000, 0.10880] |

Decision-level variation dominates this decomposition. The between-writer component
is uncertain and includes zero. Shared prompts and historical inputs remain possible
sources of dependence; this does not establish that personal signal is intrinsically
weak or that only additional writers can improve precision.

## T0b: calibrated readers and stacking

No arm clears the declared useful-gain screen. The table gives equal-writer mean
half-Brier improvement of the stacked forecast over the existing partial-pooling
baseline; positive favors stacking. Intervals are descriptive writer and crossed
writer/prompt bootstraps conditional on fitted predictions. They omit calibrator
refitting uncertainty and are not simultaneous across arms. H0 has no history, H1
same-session history, H2 own cross-session history, H3 another writer's history.
BCTS uses temperature plus class biases; EM_TS is the requested EM correction then
temperature under unverified label-shift assumptions.

| Arm/method | Mean gain | Writer interval | Writer/prompt interval | Clears .01 screen |
|---|---:|---|---|---|
| R27.H0.BCTS | -0.00125 | [-0.00328, 0.00048] | [-0.00377, 0.00186] | No |
| R27.H0.EM_TS | 0.00007 | [-0.00159, 0.00158] | [-0.00327, 0.00452] | No |
| R27.H1.BCTS | -0.00008 | [-0.00479, 0.00418] | [-0.00678, 0.00904] | No |
| R27.H1.EM_TS | 0.00102 | [-0.00160, 0.00392] | [-0.00439, 0.00699] | No |
| R27.H2.BCTS | -0.00131 | [-0.00343, 0.00043] | [-0.00368, 0.00185] | No |
| R27.H2.EM_TS | -0.00031 | [-0.00277, 0.00193] | [-0.00377, 0.00510] | No |
| R27.H3.BCTS | -0.00113 | [-0.00331, 0.00074] | [-0.00394, 0.00227] | No |
| R27.H3.EM_TS | -0.00082 | [-0.00154, -0.00022] | [-0.00186, 0.00010] | No |

All original invalid replies remain: standalone correction assigns the fixed system
penalty, while stacks fall back to the baseline. 107 inner/outer EM fits
reached the predeclared iteration cap; their per-arm counts are retained in
[qualifications](PHASE0_QUALIFICATIONS.json). The EM branch is numerically capped
and provisional, not evidence that label shift is absent. The separately fitted
bias-corrected branch supplies no observed useful stacking gain in this sample.
No engine role is admitted and no family is statistically killed.

## T0c: all-session prequential backbone

The admitted replay has 16,855 decisions, 61 writers and 1,399 sessions; eight
nonmonotone sessions remain source exclusions. Every fitted session uses only
strictly earlier completed sessions. Positive numbers below mean lower half-Brier
loss than the named comparator. Own-novel means the writer has not previously
encountered that prompt; global-novel means no training session has it.

| Subset | Decisions | Writers | Gain over population | Crossed interval | Gain over personal frequencies | Crossed interval |
|---|---:|---:|---:|---|---:|---|
| All | 16855 | 61 | 0.02108 | [0.01239, 0.03221] | 0.00726 | [0.00003, 0.01495] |
| Own-prompt-novel | 6155 | 61 | 0.02032 | [0.01103, 0.03201] | 0.00838 | [0.00084, 0.01672] |
| Global-prompt-novel | 289 | 14 | 0.01176 | [-0.00905, 0.04396] | 0.00894 | [-0.00467, 0.02850] |

The local backbone improves descriptive forecasting over unconditional population
frequencies on all decisions and the own-prompt-novel subset. The smaller truly
unseen-prompt subset remains unresolved. Task-prefix features and writer offsets
are bundled in this comparison; it does not isolate a causal personalization effect.
The per-history curves, log-loss comparisons and full uncertainty summaries are in
[the aggregate JSON](PHASE0_SUMMARY.json). Varying writer composition across bins
prevents reading their shape as an individual learning curve without further work.

**ToMpathy implication:** statistical-backbone research remains live; no engine
module is admitted, killed or replaced by this descriptive screen. Fresh engine,
Ghost-twin, adapter and confirmation gates remain necessary. Literal transcriber
questions remain open. No source data, raw forecast or maker identifier is published.

**Recording:** internal method and instrument entries are S15-PHASE0 in FINDINGS,
TOOLS and TODO. These are calibration/backbone instrument analyses; theory remains
unchanged pending the joint/family synthesis and its required admission evidence.
