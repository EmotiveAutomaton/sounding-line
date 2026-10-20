# D30.p: crossed model with current control requirements

October 19 implementation under the October 18 week packet, section 2,
and retained mid-run rules 4 and 5. Earlier results are exposed. This is the
commissioned descriptive second pipeline, not independent confirmation.

**Question.** Is the local-minus-pervasive pause association retained when
writer and globally shared marker intercepts are jointly estimated?

**Method.** Preserve the admitted pilot's complete occurrence population,
log-pause outcome, own-marker-count adjustment and crossed Gaussian REML model.
Use 2,000 real-writer bootstrap samples, seed 20261017. Each sampled copy has
its own writer intercept; equal marker strings retain a shared marker intercept.
Every variance component is re-estimated. Undefined or failed draws stop the
comparison; none is dropped, redrawn or replaced with a different fit.

The original marker-label shuffle remains, with 2,000 bootstrap refits.
Replace the single outcome control with 200 within-writer raw-outcome
permutations, seed 20261018. Report the upper-tail probability, mean, sample
standard deviation and central 95% interval. Absolute mean greater than one
quarter of its standard deviation flags bias. Exact zero mean and zero spread
does not flag bias. This destroys nuisance associations as well and supplies a
descriptive reference, not causal exchangeability.

**Paired control choice under S5.** Retain the original seeded session-owner
reassignment. Reclassify markers using those histories, then intersect by
original occurrence index. The comparison uses the same outcomes, nuisance
covariates, own-count covariate and real writer/marker random-intercept identities;
only the local/pervasive indicator changes. Keeping the original nuisance model
avoids changing both the classification and the adjustment at once. Report
retained and dropped occurrence counts and real-writer support. If the shared
subset lacks an identifiable design, record an invalid control separately from
the full primary. Otherwise resample the same real writers in both arms and
report own minus fake from the paired 2,000 draws. This crossed control does not
complete the separately commissioned fixed-effect `.fake` or word-list cards.

**Numerical implementation.** The original estimator failed known-answer
control fits before corpus dispatch. A separate implementation evaluates the
same REML objective with analytic derivatives and stable penalized residual
sums, rather than finite differences and cancellation-prone quadratic subtraction.
Start, iteration limit, variance ceiling, objective tolerance and gradient
tolerance remain unchanged. Line-search steps increase from the optimizer's
20-step default to 50; there is no alternate-start rescue. Original code and
failed tests remain. Original successful point agreement must be within 1e-6
log-pause units, and complete fresh-process replay must match the new results.
This numerical equivalence threshold is prospective for the new implementation;
it does not alter any original result or admission record.

**DESIGN CHECK.** LESSONS sections 3-5 and CONTROLS sections 1-6 reread.
Require agreement with direct dense covariance and finite-difference derivatives;
positive, zero and reversed known effects; exactly zero paired differences for
identical arms; paired row/covariate and random-sample identity; reachable bias,
nonidentifiability and variance-ceiling refusals; complete 2,000/200 scheduling;
immutable checkpoints and fresh native replay. Retain failed validation attempts.
No positive scientific interpretation follows from a cost pilot.

**Cost admission.** The corrected estimator needs a new measured whole-design
pilot: five bootstrap draws per active arm and five outcome permutations,
execution plus independent replay. All original occurrences remain. Its output
contains timing and numerical admission only, no scientific state or interval.
Use twice the slowest observed full fit times the full main fit count, plus two
source reconstructions. Include the original pilot and the new pilot's actual
wall charges in the main's original 19,800-second allowance; S4 allows at most
one doubling, never a reset. The prospective pilot itself is capped at 1,800
combined wall seconds, charged to that allowance. Main is not queued until the
complete timing receipt is reviewed. Preserve the first-tenth projection and
week resource/drain guards. One counted CPU slot, two numerical threads, below
normal priority; no GPU or paid calls. The ToMpathy reservation remains.

**Route and claim.** Retain exhaustive positive, marginal, null, negative and
invalid states. No extra scientific extension follows. The same-row paired
contrast carries any descriptive person-location reading; earlier loud controls
remain recorded. This comparison alone identifies neither automaticity nor
attention. Immediate card/index write-through and the daily theory digest apply.
