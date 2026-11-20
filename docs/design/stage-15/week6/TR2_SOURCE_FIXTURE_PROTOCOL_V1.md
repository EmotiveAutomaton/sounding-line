# TR2: prospective component family and source-model fixtures

Owner-review proposal, November 15. This completes the component multiplicity
and constructed-world definitions proposed in
[the source successor](TR2_SOURCE_SUCCESSOR_V1.md). It does not change that
sealed note, the original four-file scaffold, any source, or any completed
receipt. **Refusing and slowing remain unimplemented and unqualified. Returning
remains unsupported:** the original source's 61 writers cannot meet the binding
200-writer floor. Its meaning primary and grammar control remain unrun.

The component family and multi-world selection extension below are explicit
proposals requiring owner review against the packet; they are not approved
rules merely because their bytes are frozen. No numerical execution is
authorized by this document. Implementation follows owner review; any
numerical selector needs a separate serial-slot release.
This is the existing TR2 instrument work within its one inclusive 60,000-second
ceiling, not an additional qualification campaign or a new human study.

## DESIGN CHECK and fixed interpretation family

LESSONS sections 2 and 3, including the November 15 sampling-model correction,
and CONTROLS sections 6 and 7 were reread. Relevant set-point/slope and mixed-
pause theory sections were reread without editing them. Numerical agreement
with an oracle does not validate independence across sessions. The null must
be able to fail the ruler; a model-violating alias must remain an explicit limit.

Freeze one family of five interpretable setting components before human
outcomes: B2 Species, Intervention, Gender and Fitness, and D33 own-surprise
slope. This family controls the component claims; it creates no pooled setting,
profile scalar, cross-source average, or all-components conjunction. The failed
source bound removes returning before any outcome selection. A later supported
returning source would require a separately authorized prospective design;
there is no such source substitution here.

For each component, the primary variance statistic is the minimum of its two
noise-corrected outer-half variances. Retain both variances individually too.
Draw 2,000 whole original fingerprints/writers with replacement. Every repeated
unit carries all sessions, dimensions and nested estimates; B2 uses the same
draw across all four dimensions. Recompute moments and noise corrections under
the multiplicities. Do not redraw, drop an invalid draw, or treat it as zero.

For the variance gate and stability classification use **99% two-sided
percentile intervals**, Bonferroni alpha 0.05/5 per component. Quantiles use
the linear order-statistic convention: index `(B-1)*p`, interpolation between
the two adjacent sorted values, at p=0.005 and 0.995 for B=2,000. Each field's
interval requires every draw finite and defined; report all failed ordinals and
counts if it is unavailable. A nonpositive reliability, nonpositive corrected
side variance or undefined correlation cannot produce a stability ratio.
Negative corrected variance is retained as a valid variance estimate.

An interpretation first requires the entire adjusted variance interval above
zero. Then apply TR1's unchanged whole-interval bands to adjusted stability:
lower bound strictly above 0.5 is stable; upper bound strictly below 0.2 is not
stable; an interval wholly in the closed [0.2,0.5] band is partly stable;
otherwise inconclusive. A failed variance gate says that between-person
differences could not be measured. An incomplete required interval cannot
produce a scientific category. Values above one remain unclipped.

This uses intersection-union logic within each component: any interpretation
requires both a positive true-variance gate and a valid stability-band decision.
A false component interpretation must fail the applicable component gate;
Bonferroni across the five predeclared components bounds that family, subject
to the intervals' sampling-model validity. **Do not claim 95% simultaneous
coverage of all ten displayed intervals.** Ordinary 95% intervals are retained
as explicitly marginal descriptive companions and never replace the adjusted
decision interval. Approximate `sees` and `supports_at` use the full bootstrap
standard error and inherited 0.5 bar, with the normal-approximation caveat.

Support, not effects, determines eligibility: original B2 cohort plus at least
three valid choices in every group and dimension, at least 1,000 fingerprints;
original supported D33 roster plus all required rank/leave-session checks, at
least 20 writers. These are the prospective floors in the source successor.
No unsupported component is silently removed from the five-component correction.
The smaller cost route is a whole-unit sample under the inherited accounting
rule, keeping these floors, source, estimand and complete dispositions.

## Shared deterministic construction

Base seed is 20261107. Canonical unit IDs are sorted opaque strings. Session
hash input is the UTF-8 compact JSON array
`[20261107,"TR2-session-v2",setting,unit_id,session_id]`; sort by SHA256 bytes,
then the exact session ID. Allocate sorted ranks cyclically to groups 0,1,2,3.
Groups 0 and 2 are outer half A; groups 1 and 3 are B. Each pair of groups is
that outer half's two inner replicates. All rows of a session stay together.
This is non-temporal cross-session consistency; it never supplies chronology.

B2's choice hash is the same encoding of
`[20261107,"TR2-choice-v2",unit_id,group,dimension,response_id]`. Select the
lowest three hashes within each group/dimension; break ties by exact response
ID. Duplicate source IDs refuse before selection. Hashes never include a
choice, pause, fitted value or another outcome. Metadata-only split support is
sealed before any fit in a later admitted source run.

For each constructed random stream use NumPy PCG64 with the unsigned big-endian
integer from the first eight bytes of SHA256 of the compact UTF-8 JSON array
`[20261107,"TR2-world-v1",setting,world_id,component,phase]`.
World identifiers below are literal. Components are the four fixed B2 names or
`own_slope`; B2's one shared bootstrap stream instead uses `all_dimensions`.
Phases are `choices`, `signs`, `noise`, or `bootstrap`. This prevents
loop order from changing a bank. Preserve library/code pins. Replaying a world
starts its stream fresh, rather than copying producer statistics.

Constructed B2 unit IDs are `R0000` through `R1999`; D33 IDs are `W0000`
through `W1999`. Session IDs append `-S00`, `-S01`, and so on (four B2
sessions, sixteen D33 sessions in ordinary worlds). B2 response IDs append
`-Species-0000`, `-Gender-0000`, or `-Fitness-0000`, with four-digit scenario
indices within that attribute pool. Both scenario rows share the response ID.
D33 row IDs append `-word-0000` with the retained word index. The eight-session
B2 edge case extends the same ID convention. Smaller support cases retain the
corresponding prefix of unit IDs; no reused or inferred human ID is involved.

Within each stream iterate units by ID, groups 0 through 3, sessions by hash
rank, then source row index. A Bernoulli bit is `Generator.random()<p`; a fair
sign uses that bit with p=0.5. The six nonconstant triples are ordered
001,010,011,100,101,110 and selected with `Generator.integers(0,6)`.
D33 Gaussian noise uses `Generator.standard_normal` in complete integer word-
index order, including later omitted gaps. Each bootstrap draw uses
`Generator.integers(0,N,size=N)` in draw order 0 through 1999. Library pins and
canonical iteration, including shared B2 draws, are part of replay.

All stochastic core worlds use exactly 2,000 constructed units, each with both
outer halves. This mirrors TR1's 2,000 constructed trajectories, not 2,000
repeated experiments. The three targets are r=0, 0.5 and 1. Define balanced
latent vectors over unit index i=0,...,1999:
`z1=(-1)**(i % 2)` and `z2=(-1)**((i // 2) % 2)`.
They have zero means, equal variances and zero covariance. Thus
`zB=r*z1+sqrt(1-r*r)*z2` has exactly the target sample correlation with z1.
The finite latent truth, including sample-variance denominator N-1, is computed
independently and retained. These bounded latent constructions are not claimed
to be normally distributed people.

Each world contains original-unit records and IDs, not only a matrix of already
corrected coefficients. Work one world and bounded batches of units at a time;
do not retain every synthetic source row from every world in RAM. All source
record projections, exclusions and estimated coefficients are independently
replayed before a constructed result can be accepted.

## Refusing core worlds

For each dimension use the same latent construction with a fixed sign pair on
(z1,z2): Species (+,+), Intervention (-,+), Gender (+,-), Fitness (-,-).
In every dimension set `qA=0.625+0.25*z1` and `qB=0.625+0.25*zB` after the
specified signs. Every q lies in [0.25,1], including r=0.5. The true unit
setting is this probability of an all-same three-choice readout, not its sign.
The four dimensions are deliberately dependent; shared fingerprint resampling
must retain this. The latent side variances and correlations are known.

Each ordinary unit has four distinct sessions, one in each hash group. Source
IDs and hash selection are fixed before choices are generated. Each group has
at least three complete valid B2 scenarios in each dimension. There are three
attribute scenario pools: Species, Gender and Fitness. Every valid scenario
also contributes an Intervention observation, exactly as the producer's
`UNION ALL` at `moral.py:53-55` specifies. Intervention is not a fourth
disjoint scenario pool. If each attribute pool has n scenarios, Intervention
has 3n available scenarios and selects its own three hashes from that union.

For each scenario, draw its saved attribute bit and its Intervention positive
bit using their separate declared streams; they can be set independently.
The saved row has Saved=1, the level for its attribute bit, and
Intervention=`1-positive_bit`; the unsaved row has Saved=0 and both complementary
level and Intervention. Thus the original producer's Intervention coding,
`Saved*(1-Intervention)`, is preserved. Both rows have the same complete IDs and
matching ScenarioType/ScenarioTypeStrict. This creates compatible overlapping
dimensions rather than four mutually incompatible choice tables. No human row
or identifier enters the fixture.
The independently coded semantic oracle must agree with the canonical B2
projection, including both signs of never trading. It must not substitute ID1's
one-sided human-saving measure.

For each target run all three regimes below (nine core worlds):

| Literal world prefix | Source choice construction and target |
|---|---|
| `R-IID-` | Three scenarios per attribute pool, nine available Intervention observations. Set `p=0.5+s*sqrt((q-0.25)/3)`, where s is a separate fair sign drawn for that group/dimension. Draw all available bits independently with probability p; the hash-selected three have `p^3+(1-p)^3=q` exactly. |
| `R-DEPENDENT-` | Draw a group/dimension indicator R as Bernoulli(q). If R=1, the three selected bits share a separately drawn fair sign. If R=0, choose uniformly among the six nonconstant triples. Unselected Intervention bits are independent fair bits. Choices within the session are dependent but the selected all-same probability remains exactly q. Groups are independent conditional on their latent settings. |
| `R-EXPOSURE-` | Available scenarios per attribute pool are 3,6,12,24 cyclically by unit index; Intervention availability is three times that count. Fix IDs and lowest-three selection first; generate all bits independently with the same p rule as `R-IID-`. The selected readout still has probability q. Available exposure varies across units but cannot change the fixed-three target. |

Append `r0`, `r05` or `r1` to each prefix. Conditional random streams are
independent between session groups, units and dimensions; their latent vectors
retain the declared between-dimension dependence. No draw is regenerated to
improve a recovered correlation.

The outer readout is `(R1+R2)/2`. Sampling-variance correction uses
`(R1-R2)^2/4` for that outer readout's noise variance. The exact oracle enumerates
the four possible replicate pairs: expected noise is `q*(1-q)/2`. Split-half
correction uses the correlation between the same two replicate vectors and
TR1's `2*r_inner/(1+r_inner)` rule. Full-half and inner definitions never change
exposure. Both methods consume the identical projected records and latent truth.

Additional mandatory checks, separately named from the nine positive-variance
core worlds:

| World/check | Expected outcome and failure caught |
|---|---|
| `R-NULL-FAIR` | Constant p=0.5, q=0.25 for all units/groups; independent three-choice samples. True setting variance is zero. No stable/partly-stable/not-stable person-setting interpretation may survive the variance-first gate. |
| `R-NULL-CONSTANT` | Every group always chooses one fixed sign; repeat after reversing that sign. Every readout is one; zero observed variance makes reliability/stability undefined. Do not report a zero-width stable interval. |
| `R-NULL-EXPOSURE` | Constant p=0.5, with the 3/6/12/24 attribute-pool availability pattern. Fixed-three truth variance is zero. A deliberately variable-k diagnostic uses the common minimum of the four available dimension counts and has setting `2**(1-k)`, whose across-unit variance is positive entirely from exposure. The analytic oracle must show that difference, and fixed-three inference must not label a measurable setting. The wrong arm is a named diagnostic, never a candidate. |
| `R-ORIENTATION` | Enumerate all eight binary triples and their complements. Never-trading is one only for 000 and 111, unchanged by complementing. Four dimensions remain four outputs. |
| `R-SUPPORT` | Construct exact 999/1,000 eligible-unit boundaries, a group with two choices, one complete and one invalid pair, repeated IDs, and eight-session units. Count every disposition; hash splits keep sessions intact. Support rejection precedes coefficient calculation. |
| `R-REPLAY` | Reorder input rows, use a new Python hash seed, mutate one pinned source byte, and omit/duplicate a projected ID. Canonical ordering must replay exactly; changed/incomplete source refuses. |

The 2,000-unit null worlds retain their complete 2,000-draw uncertainty and
failure ordinals. Null gates are assessed for each method before selection.
These are fixed finite diagnostic worlds, not an estimated population false-
positive rate or power curve. No confidence-rate claim follows from them.

## Slowing core worlds

Each constructed writer has 16 distinct sessions, four in each hash group.
Assign their row patterns after the hash allocation so the declared information
balance is exact and unrelated to outcomes. Let outer slopes be
`betaA=1+0.5*z1` and `betaB=1+0.5*zB`. This gives known side variance and
cross-half correlation. Session independence is conditional on these slopes.

For row index j define `h(k,j)=(-1)**popcount(k & (j % 32))`.
The unscaled focal predictor is `0.6*h(1,j)+0.8*h(16,j)`; donor surprise uses
h(2,j), population surprisal `2+h(3,j)`, length `5+h(4,j)`, log frequency
`2+0.2*h(5,j)`, and the three indicator columns
`(1+h(6,j))/2`, `(1+h(7,j))/2`, `(1+h(8,j))/2`.
Session surprisal is `2+(session_hash_rank-7.5)/8`. Include the intercept.
These are constructed covariates in the same column roles and original units;
they are not reconstructed words. Use 0.1 for every nuisance coefficient and
zero writer intercept. Generate log pause as the exact linear signal plus
the specified residual. A positive-pause I/O fixture checks log(exp(y)) without
substituting log1p, normalization or clipping.

The retained word index is `j+floor(j/4)`, leaving real gaps in the constructed
index. Serial residuals are stationary Gaussian processes with correlation
`phi**abs(index_a-index_b)` within a session. Generate at every integer index
and retain the declared indices; initialize from the stationary distribution.
Noise is independent between sessions and writers. Its scale is marginal
standard deviation, not innovation standard deviation.

For each target run all three regimes below (nine core worlds):

| Literal world prefix | Row counts, information and residual process |
|---|---|
| `D-IID-` | 32 rows in every session, focal scale 1, phi=0, marginal residual SD 4. |
| `D-SERIAL-` | 32 rows per session, focal scale 1, phi=0.6. Residual SD is 2,4,6,8 cyclically by session rank within each group. Every group has all four scales. |
| `D-UNEQUAL-` | Groups 0,1,2,3 have respectively 16,32,64,128 rows per session and focal scales 0.25,1,2,4. Phi=0.6 and residual SD 4 in every session. Inner groups and outer halves deliberately have unequal information; retain it. |

Append `r0`, `r05` or `r1`. The point estimate remains the per-writer pooled
partial own-surprise OLS slope within each outer half, controlling the entire
nuisance span. Sampling noise is the complete delete-one-session jackknife
variance from the source successor. The split-half candidate uses the two
inner-group slopes; it cannot replace the full point by their average. All
leave-one-session fits must retain the focal direction. Only redundant nuisance
columns may be removed algebraically.

Rank is determined on each fit by singular values with threshold
`machine_epsilon * max(rows, columns) * largest_singular_value`. The independent
arithmetic reference solves the complete dense regression and each complete
leave-one-session regression. It does not reuse producer residualization or
saved slope/variance outputs. Compare finite fitted coefficients and variance
expressions with relative/absolute tolerance 1e-10. This arithmetic tolerance
does not alter the planted-recovery tolerance below.

Additional mandatory checks:

| World/check | Expected outcome and failure caught |
|---|---|
| `D-NULL-VARIANCE` | Every writer has beta=1 at both halves, with `D-SERIAL-` noise. True setting variance is zero; no setting interpretation passes the variance-first gate. |
| `D-EXACT` | Zero residuals, nonconstant known slopes, dense reference and residualized slope agree; multiplying pauses changes only an intercept, while a log1p substitution fails the unit check. |
| `D-RANK` | Focal equals donor; focal varies in only one session; a redundant nuisance column; and a half with only one session. Focal or leave-one-session rank failure/insufficient sessions are unsupported; a merely redundant nuisance column leaves the target and fit intact. No arbitrary ridge rescue. |
| `D-SUPPORT` | Exact 19/20-writer support boundaries; missing and duplicated row/session IDs; original unsupported dispositions retained. No writer is rescued by joining across a missing source row. |
| `D-REPLAY` | Reordered rows and a separate process/hash seed reproduce every output; a changed design/calibration/source pin refuses. No substituted prompt-excluded source. |

## Qualification, adverse aliases and reporting

A method is eligible for a setting only if every positive-variance core cell is
defined and its corrected stability is within 0.1, inclusive, of that cell's
known 0, 0.5 or 1 target, and all mandatory arithmetic, null, support and replay
checks pass. B2 has one common selected method across all four dimensions;
passing one dimension cannot conceal failure in another. D33 selects separately.

If both methods qualify, select the smaller **maximum absolute error across
the 0.5 cells** of that setting (including all B2 dimensions and all declared
regimes). Exact ties select sampling variance, retaining TR1's tie convention.
This is the prospective multi-world extension of TR1's middle-world selection,
not a scientific aggregate of human settings. Freeze it before source outcomes.
If neither passes, report estimator unqualified. Preserve every failed world;
do not change counts, seeds, tolerances or noise regimes to make a method pass.
A scientific-model replacement requires its separately frozen successor.

Two further alias constructions are mandatory diagnostics, not silently mixed
into the independent-session qualification grid:

1. `R-ALIAS`: use `z3=(-1)**((i//4)%2)`,
   `qA=0.625+0.1*z1+0.2*z3`, and `qB=0.625+0.1*z2+0.2*z3`, with the `R-IID-`
   sampling construction. All q are admissible. The observable setting
   correlation is exactly 0.8; the parts without z3 have correlation zero.
   Supply two truth labels for the identical observed data: the whole setting
   is enduring, or z3 is persistent unobserved state. The output must be
   identical. The instrument cannot identify that causal distinction from
   identical observations, and the report must retain this limit.
2. `D-ALIAS`: start with `D-IID-r0` and add `0.5*z3*own_surprise` to every
   session's outcome. Algebraically it is another writer slope. The observable
   slope correlation is exactly 0.5; the original slopes have correlation zero.
   Supply the same two causal truth labels without changing observed data.
   An independent-session error correction cannot subtract the common slope
   term without new information. The dense oracle must show the alias; no
   fixture claims to recover an intrinsic slope separately from that term.

These diagnostics do not excuse a failure in any in-assumption core world.
The warranted human scope, if the instrument later qualifies, is non-temporal
cross-session consistency of the specified readout under the stated noise
model, not proof of an intrinsic trait, chronology, endorsement or causation.

The constructed checks above do not replace source-specific empirical
comparators. The D33 own-surprise/outcome permutations and inherited CoAuthor
within-prompt writer-label reference still need an explicit source-support-
preserving reconstruction, applicability statement and undefined-null policy.
Check their complete metadata allocation banks before any outcome fit; a
changed eligible roster, invariant statistic or absent prompt support cannot
be hidden by dropping assignments. That comparator work remains a distinct
admission hold, as do actual source split support, source-specific code and
complete fresh source/statistic/control replay. No human calculation, new
numerical check, production plan or budget-registry entry was run to write this
prospective protocol.
