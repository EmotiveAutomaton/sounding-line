# T4 descriptive genre and feature-direction textures

The original T4 primary, its scale constraint and uncertainty remain unchanged.
These are the Week 4 packet's genre and per-writer feature-weight variants,
prospectively implemented under Week 5 amendments K–M. They do not upgrade the
primary result or redefine competence.

## DESIGN CHECK

**Case and check.** Genre projection retains complete temporal halves and
recomputes normalization only from the chosen genre's training menus. It checks
twenty menus per half for twenty-five writers. Below that floor, retain writers
with at least one menu in each half and run the declared pooled descriptive
fallback: one shared feature response and dismissal intercept, with no claimed
individual-temperature contrast. Source counts, exact whole-writer membership,
original sample share and the fallback are explicit. No outcome selects genre
support. The native handler exercises the full fallback and source projection.

Allowing unconstrained weights and temperature for every writer would be
unidentified: multiplying both by the same positive number leaves choices
unchanged. The feature-weight texture therefore gives each writer a unit-length
five-feature direction, with one shared positive magnitude and centered log
temperatures. Four spherical angles cover each unit direction, including
negative feature weights. The common magnitude separates global feature scale
from relative temperature; the zero-mean log-temperature convention is retained.
Direct probability, complete finite-difference gradient, unit norm and coordinate
coverage checks precede all runs. Structural scale separation does not guarantee
that sparse or flat data identify a direction; uninformative calibration fails.

**Smaller route.** Each genre uses the registered descriptive fallback if its
floor fails. Weight fitting keeps the primary's frozen twenty-five-writer
sample, with no smaller replacement selected from results. Texture uncertainty
uses 200 complete writer-cluster refits, with 2,000 only for a registered precision
follow-up. Fits run in independently verified blocks; all failures remain. As a
rescore/reanalysis texture, each cell may consume at most one quarter of T4's
60,000-CPU ceiling, charged to BK, under amendment L. The first five percent is
an in-slot pilot if the complete forecast exceeds 7,200 CPU-seconds; it includes
calibration, fitting, reduction and independent replay. Stop or continue only
under the packet's actual family/idle-slot rules, not a reset sub-allocation.

## Identified weight model

Each offered option has utility equal to common magnitude times its dot product
with that writer's unit feature direction, divided by relative temperature,
plus the unchanged two state terms. Dismissal retains its separate writer
intercept outside temperature. Shared magnitude lies in exp(-12) through
exp(12); raw log temperatures retain [-3,3] and are centered. Spherical angles
cover the full unit sphere. The penalty remains 1e-5 times half the sum of
squared common magnitude, state coefficients, dismissal intercepts and raw
log temperatures. Directions have no coordinate-dependent penalty.

Three deterministic starts use the original individual-temperature fit,
then opposite fixed .15-radian writer-balanced direction perturbations.
Each uses L-BFGS-B, 1,500 iterations, maximum line search forty, gtol 1e-8 and
ftol 1e-12. The unchanged projected-gradient certificate is 1e-5; keep every
attempt and boundary count. The reported solution is the best certified start,
not a guaranteed global optimum. That limitation applies equally in calibration
and human fits. No numerical gate may be relaxed after outcomes.

The first planted differing-direction native fixture exhausted all three
1,500-iteration starts in the original comparator without its required gradient
certificate. That failure is retained. A texture-only `.h1` continuation allows
6,000 iterations for that comparator, retaining the exact fused objective,
starts, bounds and 1e-5 full original-gradient certificate. It does not alter
the primary T4 kernel or its results. The extra iterations enter the texture's
cost pilot. No uncertified solution is admitted and no recovery threshold moves.

The texture contrast is later-half mean log probability gain over the original
individual-temperature model. Refit both comparators in every whole-writer draw,
including duplicate-writer identities and training-only normalization. Report
direction dispersion (one minus squared norm of the mean unit direction),
temperature spread and both original descriptive covariate correlations with
refit intervals. Per-writer directions and temperatures remain private.

Matched calibration has twenty seed pairs on the frozen source geometry.
Both laws retain crossed .25/4 temperatures and dismissal constants; the
alternative flips the first weight in alternating writer pairs, while the null
retains a common direction. Human labels are removed before generation. All
forty expected-score fits must complete; the exact generator dominates both
predictors. The same recovery scales are fixed prospectively: mean common-law
gain at most .005, mean differing-direction gain above .02 nats per choice.
Failure is an instrument result and blocks the texture's human point fit.
Every native fixture is constructed; passing it does not replace this complete
matched-support calibration. Results remain descriptive even after that gate.

For genre cells, dispatch `week5_bk_t4_texture`'s `genre` operation first.
When its receipt requires a pooled fallback, dispatch `genre_fallback` only;
do not run the original individual-temperature consumer on that projection.
Otherwise the original T4 complete pipeline can consume the projected bundle
with 200 draws and explicit genre scope. The weight cell uses its separate
calibration blocks, gated point fit, bootstrap blocks and complete reduction.
