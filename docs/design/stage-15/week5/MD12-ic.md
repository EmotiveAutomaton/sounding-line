# Can the Rutledge models recover prespecified minimum-size additions?

**DESIGN CHECK, 2026-11-07.** MD1 and MD2 are completed and inconclusive. These
declared fixed-design instrument demonstrations preserve the first-play source,
seeded 5,000-person exploratory exclusion, constant-training-rating exclusion,
first ten training and last two held-out ratings, per-person training-only
normalization, all eighteen M0 forgetting factors, and original whole-person
bootstrap. The primary effects and rules remain unchanged.

Bind the complete original MD12 result and exactly the same verified task NPZ.
Reconstruct the original cohort and M0-selected forgetting factor and require
exact agreement with the completed parent. Use that factor only to construct
the nuisance fit and planted direction. For every constructed world and every
one of its 2,000 bootstrap draws, reselect M0's forgetting factor by training
SSE and refit the corresponding expanded model, exactly as in the primary.
Keep every failed draw with its reason and invalidate that instrument world;
never discard it, draw a replacement, change the source or relax a guard.

**MD1.ic.** Fit the original M1 at the generating factor. Remove its fitted
level coefficient, retain the nuisance fit and full twelve-rating residual
vector, and multiply each person's entire residual vector by one prespecified
random sign. Regress level on M0 nuisance predictors using training ratings
only, then use that residual-level direction at all twelve times. The fixed
coefficient magnitude is
`sqrt(0.01 / 0.99 * heldout_noise_energy / heldout_residual_level_energy)`.
This sets an **oracle 1% signal/noise share**, using the fixed nuisance-residual
construction. It is not a promise that the refitted pipeline will achieve 1%
relative MSE gain. Both energies and the resulting dose are recorded before
recovery; the dose is never tuned to recovered held-out gain. The held-out
energy is used only to express the prospective instrument's dose, not to fit a
human predictive model or change its observed result.

Run exactly three worlds: negative dose, zero dose, positive dose, with common
whole-person signs. Report recovered relative MSE gain and its interval,
signed level coefficient and interval, selected-factor distributions, whether
the recovered point gain reaches 1%, and the original point-gain-plus-nonzero-
level-interval condition. The oracle and recovered gains must always remain
separate fields. A signed coefficient can recover while the practical gain
does not; retain that outcome.

**MD2.ic.** Remove only the fitted spread coefficient from M2. Residualize the
spread interaction against CR, EV, RPE, trial and EV-times-absolute-EV on
training ratings. Plant negative, zero and positive coefficients corresponding
to 0.01 standardized happiness per original training residual-spread SD. Keep
the nuisance fit and whole-person wild residual vectors. As in the primary,
the reporting scale is the training residual SD at the constructed world's
point-selected factor, held fixed across its bootstrap; report the generating
and reporting scales separately. Preserve the original mixed-offer/source
support qualification. These checks do not expand which human cases are valid.

Both instruments freeze the original normalization before planting. No
post-plant renormalization changes the dose. One fixed set of whole-person
bootstrap selections is reused across signs. The three worlds are an
instrument demonstration: **they do not estimate power, false-positive rate,
or evidence of absence**. No overall sensitivity-pass label is inferred from
three examples. Full participant/ridge and historical companions were already
completed and are not repeated as new scientific questions here.

Seal every saved draw prefix against source, code, dose, point fit, scale and
semantic configuration. Resume only through the authenticated runtime into a
new attempt. `max_new_draws=300` is a first-5% quantum of the 6,000 intended draws
per card; full continuation uses 6000. A wall/yield request saves all newly
computed draws before stopping. Fresh verification reconstructs every world,
all draws and all factor choices in a separate checkpoint tree. No partial
per-artifact score is a result or curator report.

The original complete pooled calibration measured approximately 496 CPU
seconds for execute plus replay, before its other companions. Three worlds
give a rough 1,500-second per-card starting forecast, not admission evidence.
The first counted pilot must update that forecast. MD1.ic and MD2.ic share a
conservative 3,600 CPU-second follow-up allowance (half the shared 7,200-second
parent), charged with all pilots, prior failures and replay inside the remaining
34,400-second MD family cap. If this does not fit, retain the measured partial
check and seek an authorized compatible scope; do not silently reduce draws.

Native constructed proofs run the complete three-world handler at 2,000 draws,
exercise signed coefficient recovery, exact oracle-dose arithmetic, reachable
undefined-MSE refusal, pause/resume and altered-seal refusal, and full separate-
process replay. The completed parent fixture's exact source hash and original
full result are reconciled before reuse. No human instrument is launched by
the builder. Cite Rutledge's data through DOI 10.5061/dryad.prr4xgxkk; all task
arrays, individual outputs and identifiers stay in private ignored storage.
