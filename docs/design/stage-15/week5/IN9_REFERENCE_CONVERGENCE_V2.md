# IN9 independent-reference convergence repair

November 13 engineering candidate. Owner review, constructed qualification and
any new real-data admission are pending. This note supplements the frozen
IN9_TWO_DAY_V1 design; it changes no scientific formula, source or gate.

## Preserved failure and diagnosis boundary

The retained IN9-items-continuation-1-20261113 attempt failed verification after
55.0 native CPU-seconds. Its execution bank contains all 2,000 draws with no
failed draw. Its separate replay contains all 2,000 draws, including 178 failures
with `independent ridge gradient certificate not met`; both point fits succeed.
The status disagreement correctly prevented acceptance. No scientific score
has been used to select this correction. Neither bank, its plan nor its source
is edited or relabelled. Their hashes are in the private repair review.

The reference's original trust-exact solve uses the full summed likelihood.
Near an optimum, subtracting two such losses can lose a small actual decrement,
while the independently checked gradient remains above its certificate. The
retained failure message does not record SciPy's status or gradient: this is a
candidate numerical explanation, not a proven diagnosis of every failed draw.
The frozen constructed regression must reproduce an uncertified original solve
and certify its recentered continuation before this repair can qualify.

## DESIGN CHECK

Read the applicable folder contracts, original IN9 design, LESSONS 2-5 and
CONTROLS 6-7, including the overlapping-component convergence and certified
solution lessons. A solver's success flag or a small objective difference is
not an optimality certificate. Failure remains a terminal draw disposition,
not grounds to drop or redraw a writer resample.

The successor preserves the original independent trust-exact call first:
gtol=1e-8, maxiter=100, and the infinity-gradient certificate <=1e-6. An already
certified solution is returned exactly. Only an uncertified finite candidate
receives at most two further trust-exact solves, each with those same options.
Each restart uses displacement d around its own previous candidate b and the
exact objective difference L(b+d)-L(b). This subtracts a constant, not a penalty,
weight, observation or gradient term. There is no production-Newton fallback.

For z=Xb and t=Xd, the Bernoulli softplus difference is
log(1+sigmoid(z)*(exp(t)-1)). For |t|<=0.5, log1p/expm1 compute that expression
without subtracting two full losses. Outside this numerical neighborhood,
stable logaddexp subtraction avoids exponent overflow. The label term remains
-y*t; the ridge difference remains b'P*d + d'P*d/2, with intercept penalty zero
and every slope penalty one. The gradient and Hessian are still evaluated at
b+d using the original formulas. This algebraic evaluation branch is not a
statistical cutoff. Nonfinite candidates fail explicitly. A still-uncertified
candidate after the fixed budget raises the same failure message.

The original writer folds, training means/population SDs, ridge objective,
source table, appraisal roster, seeds, whole-writer draws, AUC and item effects,
interval formulas, 2e-6 independent agreement tolerance, practical bars and
activation scope remain unchanged. The new handler differs from v1 only in
its docstring and reference-module import. Its module identity deliberately
changes all new checkpoint bindings: an old execution or failed replay bank
cannot be silently resumed under a different numerical reference. A possible
real successor starts fresh, computes every original draw ordinal again, and
retains all previous cost/evidence. No source requalification is required.

## Constructed qualification request

Nine targeted checks are frozen before execution. They cover exact handler-body
preservation, objective-difference hand values including a sub-ulp full-loss
decrement, the original certified path, fixed-budget refusal, weighted held-out
AUC/item agreement, source and predecessor-binding rejection, retained failure
semantics, and all 2,000 exact-null execution and independent replay draws.
The whole-handler null uses 200 paired reports per prompt at the original
support floor. Separate native Python invocations execute, reenter, verify,
and reenter verification; partial verification must remain false.

The numerical regression has six prespecified constructed cases: seeds
17/29/43, each with multiplier 1 or 10, 720 rows and 22 near-collinear features
formed from five independent latent coordinates plus 1e-7 noise. Fixed row
weights repeat 1/3/11/53/211 before multiplication. These are precision stress
cases, not an assertion that human bootstrap multiplicities have that range.
The receipt retains every optimizer status, iteration count and gradient gap,
without coefficients or scientific claims. At least one original-path solve
must fail its certificate and all repaired cases must meet the unchanged
certificate. If that does not happen, the proposed numerical explanation has
not been qualified; preserve the result and return for review.

One owner-granted serial constructed-test command is requested, <=180 wall
seconds, <=2 numerical threads, unchanged resource floors and owned-process
observations. No test token is presumed. No real table is loaded in these
tests. Runtime/campaign admission, the remaining IN9/IN ceilings and whether a
fresh successor may run remain owner gates. The original failed replay's 178
draws are never replaced in situ; a new replay is separate evidence.
