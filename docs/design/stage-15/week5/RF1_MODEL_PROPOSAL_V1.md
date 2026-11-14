# RF1 numerical model preparation, source-held

Prospective, 2026-11-13. **Not admitted, not committed, not a complete source
pipeline.** The frozen RF/CP intake package remains unchanged. This prepares
the binomial mathematical primitive and a known-answer world while the owner
reviews the RF paragraph's operational details. It never reads the raw SNAP
archive or invents election identities.

## Unresolved primary source requirement

SNAP exposes SRC, TGT, VOT, RES, YEA, DAT and TXT; it supplies no election UID.
Repeated candidacies mean candidate, candidate-year, outcome or an arbitrary
date gap cannot identify every election. The original source is retained; no
alternate crawl or corpus has been substituted. The private boundary review
documents a later independently scraped corpus adding explicit UIDs, but does
not treat that different population as the authorized source. The dependent
RF1 primary remains held until exact original election provenance is qualified.
Marker intake and its private adjudication can proceed independently.

## Owner-review proposals, not silent defaults

Preserve both positive and negative markers. Proposed primary representation:
each read supplies two mean-occurrence-per-early-comment rates, one for each
polarity. THREE has six columns; every TWO model pools same-polarity rates for
the two named reads and has four. This avoids cancellation of opposing
expressions. A signed-rate representation is implemented as a separately
labelled prospective texture; it is not selected after outcomes. The owner has
explicitly kept this choice provisional pending ordered review.

The later support/oppose counts form the binomial likelihood; later neutral
votes are excluded. The proposed early support share likewise excludes neutral
votes. Elections with no early or later nonneutral votes are unsupported, with
counts retained. At least 20 total comments define election eligibility; the
first floor(N/3) comments form the early third. Exact timestamp parsing and
ties need a source-qualified ordering before the source adapter can be built.
No UID mapping or early/late source transformation is currently executed.

Five candidate folds are assigned by a fixed SHA-256 rank with seed 20261112,
then round-robin across the five folds. Every election for one candidate stays
in its fold. Every model includes year effects and the early support share.
Fit unpenalized binomial maximum likelihood on the training folds. Scale
nonconstant predictors on training data only; constant columns are exactly
absorbed by the intercept. A held-out variation absent from training refuses;
nonconstant rank deficiency, separation or non-convergence remains unsupported.
There is no regularization, favorable column deletion or coefficient clipping.

The OOF loss per later vote is computed for each election and then averaged
equally over elections. The primary compares THREE with the minimum of the
three complete mean OOF TWO losses. This literal best-TWO definition is
prospective; it is not a nested reader-selection claim. Candidate bootstrap
draws carry all of a candidate's elections together, refit all four models in
all original folds, recompute each mean and reselect the best TWO per draw.
All 2,000 global indices and any unsupported fits remain. A missing draw never
becomes a zero or disappears. The 0.002-nat bar, whole-candidate unit and full
pipeline uncertainty are unchanged. The 20-candidate floor has a pooled
descriptive fallback, to be implemented with the qualified source consumer.

The against-family secondary still needs the owner-reviewed representation and
an exact per-mention scale specification. It is not silently replaced by the
primary coefficient ranking. No downstream scientific handler is represented
as complete by this primitive.

## DESIGN CHECK and fixtures

LESSONS 2–5 and CONTROLS apply. The case is whether separate liked, respected and
trusted reads improve held-out prediction in an office of trust, after the
early vote share. These counts do not reveal deference or felt emotion and do
not automatically travel to other settings. The source must establish actual
elections and the instrument must pass all three private 100-hit reviews.

The hand-defined plant has binary respect, trust and liking, with trust-only
support .8, liking-only support .2 and support .5 otherwise. Every candidate has
all eight combinations. THREE's true trust/liking coefficients are plus/minus
log(4). TWO-A predicts .5, so its loss relative to THREE is exactly half of
`log(2) - H(.8)`, more than .09 nats. This answer is derived from the plant,
not from an adapter. A constant-.5 world gives no model gain. Fixtures also
cover candidate folds, repeated-candidate bootstrap weights, rank/support
refusals and incomplete uncertainty. Targeted and full native tests are
unrun; source intake tests are a separate completed qualification.

RF's 40,000-second family covers cost, failures, pilots and replay. Real cost,
memory and a whole-candidate amendment-E sample size remain unmeasured. Full
native qualification, model-choice review, the against-family secondary and
source-boundary qualification are outstanding; this is not a ready plan.
