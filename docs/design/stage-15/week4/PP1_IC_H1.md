# PP1.ic.h1: exact cached-input implementation

The original PP1.ic cost probe forecasts 1,748.34375 CPU seconds, above the
1,732.203125 remaining after the 60-second validation/landing reserve and
7.796875-second native cost run. The original remains cost-held. No calibration
result has been computed. This is amendment B's separately named cheaper exact
implementation, not a new hypothesis or a change to the sample or estimator.

DESIGN CHECK: LESSONS 3-5, especially exact implementation, bootstrap invariants
and cost admission; CONTROLS 6. The null, alternatives, six worlds, seeds, dose
grid, original interval and all 2,000 draws remain as in PP1_IC.md. A cached fit
must equal the original primary contrasts to 1e-12 on both observed and duplicate
writer samples. Exact output equality across native replay is still required.
Any mismatch refuses admission, regardless of scientific direction.

Each writer's within-word median is invariant under a whole-writer bootstrap:
a repeated writer becomes a new copy with that writer's complete unchanged
sessions. Compute the original per-writer-normalized arrays once, then gather
all intervals in exactly the original sampled order and rename each sampled
copy. Refit mechanical correction, mixture and crossed regression on every draw.
Do not cache fitted coefficients, mixtures or uncertainty. Only the three
declared contrasts are needed by this calibration; their operations are copied
from the unchanged model. Input order, float64 arithmetic and original fitting
routines remain fixed.

**Case and check.** All six worlds and repeated-writer samples are compared
against the original array builder and model; independent process replay and
artifact corruption checks must pass before a separate native cost probe.

**Smaller route.** The original cumulative 1,800-second allowance includes both
cost probes and validation. The original 60-second reserve covers both targeted
check suites and landing overhead; verify measured suite time fits it. No new
doubling, smaller population or reference count. If the new full execution/replay
forecast still exceeds the remaining allowance, retain the hold.
