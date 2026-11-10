# Can the laughter comparison detect its declared minimum effect?

**DESIGN CHECK, 2026-11-07.** The completed LA2 comparisons are inconclusive.
This fixed-design instrument check implements the declared sensitivity branch;
the practical bar remains 0.02 joined-laughter fraction units. It neither
changes the primary nor selects a dose from its recovered effect.

Run AMI native language, ICSI recorded English variety, and ICSI recorded region
separately on each exact completed source/primary binding. Keep every original
pair, missing-label exclusion, zero-laugh exclusion, meeting cluster and base-rate
control. Fewer than twenty meetings is descriptive and cannot pass this check.
The original model demeans within meeting and fits same-background plus both
individual base rates. Preserve its target-identifiability test, nuisance rank
handling, and `lstsq` relative cutoff of 1e-10.

Fit the full original model once, zero only the background coefficient, and
retain the nuisance fit and residual vector. For each of 100 prespecified worlds,
multiply the entire residual vector of each meeting by one seeded random sign.
Plant a coefficient of -0.02, zero, or +0.02. Use common signs across the three
doses and the original 2,000 meeting-bootstrap selections as common random
numbers across worlds. These are conditional linear-estimator responses, which
need not be bounded fractions; they are not new valid source observations. No
clipping, post-plant normalization, dose adjustment or residual resampling within
a meeting is permitted.

For each world compute the point, percentile interval, coverage, expected-sign
zero exclusion, and the distinct positive primary threshold crossing. An OLS
coefficient is linear in the response: compute each original expanded-row
bootstrap SVD operator once, with the exact original rank guards, then apply it
to every planted response. Native proof compares all 2,000 operators against
independent expanded-row least squares on empirical-fixture, positive, negative
and exact-zero responses. Preserve every failed draw; any undefined draw makes
the instrument check invalid rather than redrawing or dropping it.

The declared conditional sensitivity criterion is null zero-exclusion at most
10%, with at least 80% expected-sign zero exclusion for each signed one-bar dose.
Report coverage and positive primary threshold crossing separately. A successful
check does not turn an inconclusive human interval into an absence result and
does not identify shared inference as the mechanism.

Operator blocks of 100 draws are sealed against input, configuration and source
hashes. `max_new_draws=100` gives a first-5% operator pilot; increasing that
operational limit preserves the analysis. `max_wall_seconds` and a yield request
stop at block boundaries. Fresh verification builds an independent complete
operator/world tree and compares all outputs. Parent/source COMPLETE receipts
must be fresh-process verified and every declared output must still hash exactly.

Native proof: `.agent-state/drive-20261107/la2-ic-native/FIXTURE.json`. It includes
100 worlds at all three doses, all 2,000 draws, signed recovery, null behavior,
pause/resume, checkpoint tamper refusal, a reachable sparse-support failure
retaining 693 undefined draws, and full separate-process replay. A constructed
proof supplies correctness, not a corpus runtime forecast. Pilot and all three
metadata checks share at most 10,000 CPU seconds (half the LA2 parent ceiling),
inside remaining LA family/campaign room, including replay and prior failures.
No human launch is performed by the builder.
