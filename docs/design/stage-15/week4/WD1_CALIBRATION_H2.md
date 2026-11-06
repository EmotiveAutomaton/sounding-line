# WD1.h2 complete calibration before corrected human scoring

This tests the separately frozen [conditional reference](WD1_SUPPORT_H2.md).
The original invalid attempt and all failed assignments remain. There is no
new human result, new study allowance or independent competence label.

**Case and check.** Construct thirty worlds: ten with no recurring personal
sensitivity, ten with only recurring acceptance criterion, five with recurring
sensitivity, and five with sensitivity reversed between prompt halves. Each
world has twelve writers, eight sessions each and two prompts. The first six
sessions carry thirty-two choices each; the final two are empty. Sparse sessions
make the actual support condition nontrivial. Every writer is supported in the
original roster. Outcomes follow a known probit probability conditional on
quality. Quality ranges from -2.5 to 2.5 plus seeded normal noise of SD0.02.
Criterion is -0.2 except in the criterion-only family, where it ranges uniformly
from -1.2 to1.2 across writers. Slope is1 except in the stable/reversed families,
where it ranges from0.35 to1.65; reversed worlds use2 minus that slope in prompt1.
The features expose quality but never these latent parameters or outcomes.

Use the exact original population feature builder, recipient-excluded PCA and
logistic reference, certified original Newton and probit fits, disjoint prompt
halves and summary rules. All one thousand conditionally accepted assignments
are refitted, all two thousand paired writer draws are computed, and everything
is refitted in a fresh verifier. Seeds are20261104 plus family index times1000
plus world ordinal. No unavailable bank, numerical failure or undefined interval
is discarded. Vectorizing independent reference correlations retains the
original statistic and random draw order; full original-summary parity within
1e-12 and identical classifications is required on controlled cases.

**Admission gate frozen before the first calibration outcomes.** At most one
positive classification in each ten-world null and criterion-only family; at
least four positives among five stable worlds and four negatives among five
reversed worlds. All thirty must complete without invalid/unsupported outcomes.
This is a finite recovery screen, not a precise false-positive-rate estimate.
Failure holds corrected human inference; it does not become a human null.

**Smaller route.** No reduced calibration or control bank. Native mode uses six
writers, sixteen choices, four assignments and twenty resamples for interface
validation only. A separate generated-only timing mode runs the first world of
each family with ten assignments and one hundred resamples. Forecast the whole
thirty-world bank from the slower complete fit/setup/summary timings of either
pass, scaled to the full workload, both phases and a factor-three margin.
Admit only if this plus previously charged work and remaining human fits can
fit the unchanged151453.125CPU allowance. No GPU or paid work.

All fit files, construction truth digests, assignment banks, rejected proposals
and timing remain retained. Native or timing completion never substitutes for
complete calibration. Human exchangeability, independent quality, competence,
causal learning and payoffs remain outside this diagnostic even after a pass.
This repairs an existing instrument; no literature novelty is claimed. The
G223/G234 theory section and afterword, LESSONS3–5 and CONTROLS1–7 were reread.
