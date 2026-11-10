# MD3.p: conditional fixed-effects likelihood sensitivity pipeline

DESIGN CHECK: LESSONS 3–5, CONTROLS 6–7 and the original MD3 source/design.
This first-generation alternative pipeline keeps the predictor and cluster
contract. A conditional likelihood under fixed predictor rows is checked on
enumerable short sequences and both signed alternatives before being applied
to the original choice-history panel. Dynamic-regressor bias must remain
visible; numerical agreement is not a consistency proof.

Question: does the primary below-reference association persist when each
participant intercept is eliminated by conditioning on that person's total
number of gambles instead of estimating the intercept? Keep exact first plays,
the two signed standing terms, trial-type indicators, expected-value advantage,
earlier gamble count, trial index, recent-outcome discount 0.65, common standing
scale and complete participant-cluster resampling. No source, reference,
support rule or original result is changed. Participants who always or never
gamble contribute no conditional information, as in the original likelihood.

Compute the conditional-logit normalization by exact elementary-symmetric
polynomial dynamic programming, with stabilized log-space arithmetic; no
sampling approximation, penalization or chosen nuisance-feature deletion.
Require the gradient tolerance and explicit curvature/rank certificate before
accepting a fit. Weights in a cluster bootstrap multiply complete participant
conditional log-likelihoods. The primary is the lower-standing coefficient,
with2,000 whole-person refits; report the upper coefficient and their contrast
beside it. Coefficients retain the parent's log-odds/standing-SD scale.

Important assumption: conditioning on total choices treats the full predictor
matrix as fixed. Earlier choices generate several actual predictors, so the
usual strictly exogenous conditional-logit interpretation need not hold here.
This is a descriptive alternative objective on this dynamic panel, not an
unbiased-estimator claim. Its calibration must regenerate entire trajectories
under the parent's fitted dynamic law with both standing terms zero, using
the original participant intercepts and fair offered gamble endpoints, and
then recompute all regressors before fitting the conditional objective.
Retain twenty such nulls. The practical threshold is max(0.01, twice their
mean absolute lower coefficient plus three sample standard deviations).
Whole intervals above/below the corresponding signed threshold give the
scoped supports/against reading; all others are inconclusive. No empirical
effect selects a new calibration law or threshold.

Both original case floors remain:10,000 people with first-play opportunity on
both sides of zero and 10,000 rescue opportunities, with informative-subject
counts separately recorded. Rank loss or a failed optimizer is invalid or
unsupported, not zero; below-floor estimable fits are descriptive only.

Required native controls: enumerate all binary sequences of short panels
conditional on each choice count and match the objective/gradient exactly;
finite-difference gradient and curvature checks; signed/zero exogenous laws;
zero-standing dynamic laws that rebuild every history; an alternative that
passes the full calibrated rule; actual full2,000-draw execution and independent
resumed replay. Report observed finite-panel bias rather than silently
removing its control. No second dataset or independent human replication is
claimed by this pipeline comparison.

Ceiling: 1,800 CPU seconds including native qualification, the first 100-draw
counted5% pilot, all null work, failures and complete independent verification,
inside remaining MD 34,400. Stop at the authenticated pilot for actual complete
cost review. Use only the prospective whole-person sample route, retaining
all selected eligible plays and both floors, if full source cannot fit. No
reduced uncertainty, approximate conditional denominator or unreviewed change
to the frozen pipeline is an implicit cost fallback. This design authorizes
no execution and the consumer/controls remain unbuilt.
