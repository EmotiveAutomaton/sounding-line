# P4 and G3-A chronology refinement before fitting

DESIGN CHECK: LESSONS 3–5. Under the null, permuted labels cannot gain access
to target outcomes. Under the alternative, only earlier completed sessions can
improve the forecast. Any future or overlapping training/calibration resolution
is a refusal, not a silently removed row after scoring.

The per-writer 60/20/20 session partition in EXECUTION is necessary but not
sufficient: another writer's early 60% can occur after this writer's test date.
The pooled fit therefore needs a recipient-specific time cutoff. This document
refines the unrun fit; no old source, result, threshold or forecast is changed.

For each eligible recipient, fit population coefficients and preprocessing only
on declared training sessions that are completely resolved before the start of
that recipient's first calibration session. Fit that recipient's intercept on
their eligible training sessions. Choose settings on the recipient's calibration
sessions; every calibration session must finish before their first test session.
Freeze the selected fit without refitting on calibration outcomes. Target-time
prefix covariates and already resolved history remain available, with parameters
fixed for the scored tail. Count actual usable decisions as well as the 3/1/1
session floor; preserve every unsupported recipient and overlap exclusion.

The augmented paid-feature arm uses exactly these partitions, cutoff, targets,
preprocessing rules and frozen fitting policy. Training/calibration acquisition
costs count before the first evaluation look. Both arms score the same fixed
writer-stratified acquisition blocks with session weighting. Paid acquisition
order never becomes prediction chronology. A failed/absent label uses its frozen
missing indicator and neutral encoding, never success-only filtering.

Implementation must exercise an adversarial fixture where another writer's
nominal training session lies in the recipient's future. The fit and actual
dispatch must refuse or exclude that session before any label access. This
protocol is ready; the P4/G3-A fitting and annotation routes are still unbuilt.
