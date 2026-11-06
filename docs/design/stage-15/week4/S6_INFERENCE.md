# S6 fixed inference and calibration

Prospective implementation of [S6](S6_CONFLICT.md), frozen before new fitting.
The source and original D33 modules remain unchanged. The adjusted model calls
the exact original sufficient-statistic random-intercept likelihood and optimizer
with two appended columns; both conflict columns must remain identifiable.
The baseline is the original fit on the identical rows. Both use the same
2,000 whole-writer resampling indices and seed 20261102. Retain every signed
coefficient and paired difference. Use the inherited 200 within-writer own-value
and outcome permutations; preserve missing fits and suppress incomplete tails.

**DESIGN CHECK.** LESSONS 3–5 and CONTROLS 1–7 reread November 4. Known null,
positive, reversed, conflict-only, combined personal/conflict and donor-only
worlds precede human fitting. Each has twenty writers, eighty observations per
writer and a full-rank twelve-column model. All non-intercept covariates have
the same mean in every writer; own value correlates with entropy;
the conflict-only world must therefore realize an omitted-conflict association
in the baseline. Residual noise is orthogonal to the full design separately in
each writer, making the focal coefficients analytic known answers even after
cluster resampling. This is an algebraic calibration, not empirical power.
For every world, all 2,000 paired fits and both 200-draw reference banks execute.
All adjusted own, donor and conflict coefficients must recover their specified
values within 2e-8; dense per-writer GLS at the fitted variance ratio independently
checks the solver. Collinear focal controls must refuse. All invalid draws remain.
No successful-only distribution or redrawing is allowed.

**Case and check.** Source support is exactly the frozen twenty supported writers;
scalar population probabilities and full source replay precede analysis. The
null and confounded null must retain adjusted own coefficient zero, the planted
positive must remain positive, and reversal must remain negative. Missing banks,
failure of algebraic recovery, or changed source/calibration bindings hold human
admission. The first local validation fixture omitted equal cluster means, so
its random intercepts could perturb the nominally exact slopes; that failed
validation and source are preserved privately. Correcting only the constructed
cluster means repairs the claimed analytic answer, not the estimator or gate.
A null human result still needs the packet's subsequent instrument
sensitivity check; this calibration alone cannot establish power at small effects.

**Smaller route.** None below the twenty-writer floor. Cost every world's first
tenth of paired refits and references, with a threefold factor and full fresh
verification. Cost human-shaped inference separately before admitting it; replace
its actual outcomes with a seeded constructed response during that cost probe.
All charges share S6's original 2,880-second ceiling (single S4 maximum 5,760),
including source work, validation, failed attempts and verification. Checkpoint
and retain complete blocks. Raw outcomes or coefficients from unfinished probes
are never scientific results. S2's revision extension remains blocked separately.
