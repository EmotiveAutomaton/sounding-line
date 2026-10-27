# CA5.r preference: a separate Jester comparison

The curator approved this scope on October 26: "Build the separate preference
comparison." This answers whether joke-topic preferences recur beyond population
item averages and each person's overall rating tendency. It does not repeat the
demographic-relative harm comparison: Jester has neither demographic groups nor
harm labels. That original question remains open. This is CA5's third and final
first-generation follow-up, not a new research leg or permission for descendants.

All 50,691 approved complete records remain. The quarantined partial record and
the archive's advertised-population discrepancy remain explicit. Missing ratings
stay missing, exact zero and negative ratings remain valid, and all 150 joke texts
are retained, including ten items without observed ratings. Numeric odd/even
item IDs define the two halves; they are not chronological halves.

## Freeze before outcomes

Text features are learned from complete joke text only, with no ratings supplied
to that process: lower-case English-stopword-filtered word unigrams and bigrams,
TF-IDF with minimum document frequency 2, maximum document frequency 0.95,
sublinear term frequency and L2 normalization. Eight nonnegative matrix
factorization components use NNDSVDa initialization, coordinate descent,
Frobenius loss, seed 20261026, tolerance 0.00001 and at most 2,000 iterations.
Non-convergence fails admission. No text truncation, outcome-based topic naming,
topic selection or choice among fits is allowed. Component mass is normalized
within each joke and transformed by softmax at temperature 0.25, giving every
joke positive membership in each component. Top vocabulary terms are retained
privately for audit; these are lexical topic proxies, not validated psychological
categories. The complete matrix and model parameters are hashed before scoring.

Missingness makes sequential item and person centering insufficient. Fit additive
person and item fixed effects by least squares separately within each item half,
on observed cells only. Eliminate person intercepts analytically, solve the small
item normal equations by a symmetric pseudoinverse (relative cutoff 1e-12), and
certify both row and column residual sums. This subtracts generosity and item
popularity under the actual exposure pattern. It does not correct selection on
unobserved ratings. Within each half, form a person's topic profile from the
topic-weighted mean residuals; center its eight coordinates. The primary is the
equal-person mean Pearson correlation across the two profiles, minus the mean
of its rebuilt itemwise reassignment reference. A constant profile contributes
zero and is counted. No support-based person filter is permitted.

The reference has 1,000 independent within-item permutations of fitted residuals
among observed raters. Each draw keeps the exact observed cells, refits additive
effects, and rebuilds profiles. The separate outcome control has 200 permutations
within each person's observed cells, separately by half, also refitting. Seed
20261026 fixes both banks, with disjoint seed offsets. These are conditional
residual-exchangeability references, not randomized exposures. Report both banks'
means, standard deviations, 95% bands and one-sided descriptive probabilities.
For each reference, a 2,000-draw bootstrap resamples real persons with their real
and mean-reference correlation together. Intervals condition on this item bank,
the text features, fitted population adjustment and reference bank.

The primary direction is positive. Positive means paired interval lower bound
above zero and itemwise permutation probability below .05. Negative means upper
bound below zero and the opposite-tail probability below .05. Marginal means a
directional probability below .10 without those interval/probability conjunctions;
all other valid outcomes are null. A within-person reference whose absolute mean
exceeds one quarter of its standard deviation fires the inherited bias warning;
such a comparison is descriptive only even when its primary is positive. No
negative finding means absence of all personal preferences. Unsupported means
fewer than four persons or no usable profile coordinates, and is separate from
null. Source, solver, feature or known-answer failure means invalid, never null.

## Known answers, admission and cost

DESIGN CHECK: LESSONS sections 3–5 and CONTROLS sections 1–7 were read for this
design. Under the null, arbitrary additive person/item effects must give zero
even with unequal exposure; pure noise must not create systematic recurrence.
Under the alternative, stable text-coordinate preferences must be recovered;
opposite preferences in the second half must reverse sign. Test sparse masks,
heterogeneous noise scale, an explicit dummy-matrix least-squares oracle,
invariance to additive effects, immutable output, altered inputs and fresh replay.
These checks guard mathematical confounding, wrong-sign references and silent
population changes. They precede unknown-outcome scoring. Constructed validation
also runs the complete reference-bank sizes. Corpus-mask planted null/alternative
checks precede the real comparison and are retained, not tuned to pass.

The original allowance is 1,800 CPU seconds including all construction,
validation, failed attempts, execution and independent replay. Input support
already charged/reserved 122.578125 seconds. A further conservative build reserve
will be recorded with measured tests. A complete fixed cost pilot times 100
itemwise and 20 within-person draws on all records, plus 2,000 bootstrap draws;
it admits cost only and releases no partial scientific score. Full counts are
never reduced for admission. All runtime work uses counted Gear 2 CPU leases,
at most two numerical threads, pinned source capsules and fresh-process replay.
GPU parking and paid-transfer holds remain. If the original allowance is
insufficient, the existing S4 rule is assessed separately; no automatic overrun.

## Literature and interpretation boundary

Jester already supports personalized recommendation research; this is a scoped
replication/texture question, not a claim to have discovered personal taste.
Nathanson's Berkeley technical report, *Algorithms, Models and Systems for
Eigentaste-Based Collaborative Filtering and Visualization* (2009), sections
4.2.1–4.2.3, was fetched and inspected: recommendation order depends on predicted
ratings, with separate gauge and sparse-item seeding sets. This motivates the
exposure caveat and the exact sparse additive check above.
[Primary report](https://www2.eecs.berkeley.edu/Pubs/TechRpts/2009/EECS-2009-85.pdf).
The official current dataset page was found but its direct fetch timed out; the
existing pinned source archive remains authoritative for these input bytes.
Searches also located audience-versus-joke research, but its full paper was not
read, so no finding from it is adopted. No exhaustive novelty claim is made.

This comparison bears on the curator's baseline-versus-personal-departure
question (G197; reader G213). A positive conditional recurrence would locate a
repeatable rating pattern in this corpus. It would not identify values,
competence, objective joke quality, a causal psychological mechanism or the
unobserved preferences of an unrestricted population. The original CA5 evidence
and framing remain unchanged.
