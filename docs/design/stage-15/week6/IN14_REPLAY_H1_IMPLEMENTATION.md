# IN14 .h1 independent replay implementation

Prospective candidate, owner-approved scope November 15. No numerical check or
human run is claimed by this document. The [static proposal](IN14_REPLAY_H1_PROPOSAL.md)
and original [IN14 design](IN14_V1.md) remain unchanged. The original card's scope,
20,000 CPU-second inclusive allowance, seed 20261107, all 2,000 draw indices,
source/refusal rules and reference/primary distinction remain binding. This is
an exact implementation successor, not another scientific estimand or budget.

## Frozen algorithm

Four isolated modules implement this version. The new math copy changes only
its independent fit branch. The new run copy selects that math and pins its
new dependencies; all source handling, production fits, resampling, reporting,
checkpoint logic and independent value comparisons are identical. The entry
wrapper exposes only IN14. The original V1 math/run/entry, IN16 and the failed
person-correction files remain untouched. The private person-preparation output
remains uncorrected; the failed nine-world qualification remains held.

The new reference applies a Householder reflector to each raw writer block,
removes the intercept coordinate and retains independent projected rows. It never
uses the production demeaned blocks or production normal equations. Each positive
integer writer multiplicity weights both sides by its square root; zero-count
writers are omitted, and repeated writers retain one intercept. Single-row
writers contribute no projected rows but retain their original intercept scale
in the augmented-rank bound. No extra normalization or outcome standardization.

Projected blocks are an ephemeral cache within a newly prepared panel, not saved
state. Its private raw-array copies become read-only; replacing a raw array causes
a fresh projection. Source-frame identity, semantic and complete dependency hashes
still bind every persisted checkpoint. Weight changes never change cached rows.

The algebraic bound and proof are in the proposal. Fast eligibility is frozen
strictly at lower-singular-bound / upper-singular-bound **greater than 1e-6**,
100,000 times the original rcond. The bound uses unnormalized original dummy
columns, sqrt(multiplicity * original writer row count), and original slope units.
Normalized Householder vectors do not normalize the augmented matrix's rank rule.
Nonfinite, missing, underdetermined, near-boundary or otherwise unproven cases,
and failed projected solves, call the actual unchanged V1 dense fit. The dense
oracle keeps `rcond=1e-11` and its original rank/unsupported/nonfinite handling.
Failure of the sufficient bound never means rank deficiency by itself.

Production's `matrix_rank(xx, tol=1e-9)` remains unchanged. Saved-value comparison
retains the original absolute tolerance 1e-7, relative tolerance zero; all output
labels and exact refusal strings must also agree. No bit-identical floating-point
result is promised, no parity tolerance changes after outcomes and no timing
forecast is inferred from the supplied unverified human-source count envelope.

## Frozen constructed selector

`tests/test_week6_in14_h1.py`: 22 constructed cases, estimated 5-15 seconds and
bounded at 180 seconds against the entire owned native Windows process tree,
with two numerical threads and a unique workspace-local pytest basetemp. Run only
after owner review and serial-slot release. No test has run as of this freeze.

Cases compare the actual old dense solver with the isolated reference under
nonuniform multiplicities, omitted writers, unequal lengths, one-row writers,
constant/exactly collinear and near-rank columns, large writer means, and strict
equality at the computation guard. They test both fast and fallback paths and
require fallback on unproven rank. A cache test poisons production's demeaned
blocks to establish reference independence; a fast-path test refuses any dense
call. Construction/solve failure must preserve the old oracle's disposition.

Two tiny planted/zero row worlds exercise actual primary, dose, decay and
same-valence-reach preparation, all output terms, and varying reach dimension.
A separate constructed survey prefix compares exact source rows, fixed seed,
point and first three draw outputs across V1 production, .h1 production and .h1
reference. It remains an explicitly incomplete 2,000-draw run with verified=false;
this does not substitute for the complete independent replay required in any
admitted human execution. No human source, large native qualification campaign,
empirical calibration, original bank rerun or failed-person sweep is included.

The static semantic proof shows every math function except the independent branch
and every run function except dependency enumeration is AST-identical. The candidate
harness pins code, tests, this design, original sources and its own containment
implementation before execution. The immutable builder delivery records exact
candidate bytes and unresolved checks; it grants no admission or launch.
