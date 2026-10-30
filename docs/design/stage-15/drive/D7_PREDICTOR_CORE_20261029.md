# D7 predictor and whole-unit cost instrument

This implements the commissioned F11 / D7 comparison after the complete source
replay. It does not yet admit a human result. Source: D7_SOURCE_20261029.md.

## DESIGN CHECK

LESSONS sections 3–5 and CONTROLS sections 1–7 reread for this build.
Under an exact constant response the two duration predictors must agree exactly.
A planted novelty contribution must improve held-out duration prediction; the
same contribution with the opposite sign must remain detectable as prediction,
without being miscalled longer examination. The fitted coefficient keeps its
sign separately. Noisy null worlds must not be used to choose a new setting.
These are engineering checks; full scientific calibration is still separate.

Whole sessions split chronologically 60/20/20 within each writer, requiring at
least 3/1/1 sessions and strictly nonoverlapping time ranges. Censored durations
are retained in the source and excluded explicitly from these completed-duration
comparisons. Report the support census; this is a conditional observed-duration
population, not all menus. Require at least 10/2/2 observed menus.

The duration response is log(1 + visible seconds). The baseline has later
acceptance, log mean option characters, menu size, prompt indicators and the
specified cost term. The full model adds mean pre-opening embedding distance.
This is retrospective prediction conditional on the eventual handling decision,
not information available when the menu opens. Primary loss is squared log-time
error. The separate acceptance comparison uses binary half-Brier loss, contrasting
surface + prompt + novelty + cost against those terms plus log duration. It too
is a completed-event association, not a prospective decision predictor.

Each fit is weighted equally by training session, then equally within session.
Train-only standardization and prompt vocabulary; unknown prompts have zero
indicator columns. Ridge penalties are fixed at 0.001, 0.01, 0.1 and selected by
session-weighted calibration loss separately for each arm. The intercept is not
penalized. Acceptance predictions are clipped to [0, 1]. No test response enters
fitting or penalty selection. Test losses are averaged by session, then writer.
The three cost settings are none, log(1 + menu ordinal), log(1 + elapsed seconds).
Elapsed time is the primary setting; all settings remain reportable. The supported
novelty channel is embedding distance; Q1/Q2 remain unavailable, not silently
substituted or claimed complete. Acceptance margin remains 0.01 half-Brier.

## Remaining scientific admission

Before scientific execution, freeze and validate the complete analysis and gate
rules: 200 within-writer joint permutations of duration and acceptance; 200
session-level writer reassignments within prompt as a separate diagnostic;
2,000 writer-cluster resamples; and complete no-effect, nuisance-only and signed
novelty calibration. A shuffled writer comparison is not assumed to erase a
population novelty association. No personal mechanism claim is licensed by the
population contrast. Its gate and reference expectations must be explicit before
any human contrast is reported. The proposed accounting envelope is 30 complete
calibration worlds and both complete reference banks per setting, with fresh
replay. Cost accounting is not scientific approval of these unimplemented gates.

The cost instrument runs complete fits, penalty selection, predictions and losses
for the five largest supported writers, all six response/cost combinations,
unchanged and two within-writer joint label permutations. It also runs all writers
of one fixed constructed world. Fresh native replay verifies every saved fit.
Project the full source using the slowest complete writer, both native passes,
all 401 real/reference arms and all 30 calibration worlds, plus reporting and
bootstrap allowance, with a factor of three. No partial pilot effect is reported.
Retain the fixed 3,600 CPU-second cumulative probe allowance and all earlier
preparation charges. A full projection is a new admission boundary, not authority
to exceed the current probe cap. No GPU, API, data intake or delegation.
