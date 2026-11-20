# TR2 refusing: additive pair-semantics and noise-oracle protocol

Prospective owner-review document, November 15, 2026. No implementation or
qualification is claimed. This adds refusing-only checks to
[the sealed fixture proposal](TR2_SOURCE_FIXTURE_PROTOCOL_V1.md); that proposal,
[the source successor](TR2_SOURCE_SUCCESSOR_V1.md), the four original generic
files and all earlier receipts remain unchanged. No human score, source scan,
numerical test, source-module execution or stochastic draw was performed to
write this document.

This responds to review items TR2-C-02 and TR2-C-05 in the private Builder C
read-only review. It does not resolve the separate acceptance of four two-sided,
fixed-three, non-temporal readouts, finite-sample interval validity, empirical
comparator applicability, or source reconstruction. Slowing remains held on
its separate pooled-slope noise design. Returning remains unsupported on its
original source. Nothing here replaces D33's pooled coefficient with an average
of session coefficients.

## DESIGN CHECK and unchanged boundaries

The Week 6 folder README, original B2 and B2.s designs, original producer and
header validator, sealed refusing proposal, and the relevant LESSONS gate and
sampling-model passages were read. LESSONS section 3's November 15 correction
applies: agreement with exact algebra does not establish the sampling model.

The case is preserving all valid intervention decisions while measuring
two-sided never trading over exactly three selected choices. The proposed
check puts the selected three outside every focal attribute pool. An adapter
that wrongly restricts intervention to those pools returns the opposite
indicator. Invalid source pairs must remain excluded. A second-session edge
case distinguishes the original B2 cohort from the new four-group support
requirement. The noise identities below have exact answers under their stated
assumptions and explicit counterexamples when those assumptions fail.

The five-component family in the sealed protocol is unchanged: Species,
Intervention, Gender, Fitness and D33 own-surprise slope. Keep all five members
even while a component is held; no four-component renormalization, omnibus
scalar or all-components conjunction is introduced. The proposed 99% decision
intervals, variance-first gate, unchanged TR1 bands, 2,000 whole-unit draws,
shared B2 draws, invalid-draw retention and method-selection proposal remain
exactly as proposed there and still await owner acceptance. These added literal
and algebraic checks are not extra stochastic selection cells. They add no
coverage claim, Monte Carlo acceptance threshold or revised scientific bar.

The original TR2 inclusive 60,000 CPU-second ceiling across all three settings,
shared MD family and actual Week 5 drain remain. Preparation, failed attempts,
source work and replay all count under that same allowance. No new reserve,
campaign, production plan or budget revision is created. The smaller route
remains the already proposed whole-fingerprint route with unchanged floors and
source; this document does not authorize executing it.

## Exact original source semantics

The authority is `runners/theory_days/moral.py`: the eight-column projection
and level map at lines 14-15, row coding and identity checks at lines 16-30,
complete-pair predicate at line 49, focal branch and intervention union at
lines 53-55, and common-cohort predicate at line 66. The required headers are
also explicit in `runners/theory_days/backlog_intake.py:30-39`. The original
[B2 design](../theory-days/B2.md) states that intervention uses every valid
pair. The [B2.s design](../theory-days/B2.s.md) integrates all subsets; the
new hash-selected triple remains a declared prospective TR2 operationalization,
not a reproduction of that expectation.

Read only ResponseID, ExtendedSessionID, UserID, Intervention, Saved,
AttributeLevel, ScenarioType and ScenarioTypeStrict. No participant-demographic
column is needed. All names and values below are constructed scenario records.

Group raw rows by their literal response identifier. A valid pair has exactly
two rows, nonempty identifiers, the same user and session on both rows, binary
string values `0`/`1` for both Saved and Intervention, Saved sum one and
Intervention sum one. Do not trim, coerce `1.0` into `1`, impute a missing side,
or turn three rows into a pair. Two rows sharing a response identifier are the
expected source shape; a third or fourth row makes that response invalid.

Each valid pair contributes one Intervention observation, with positive bit
equal to the sum of `Saved*(1-Intervention)` across its two rows. This branch
does not require a recognized or matching scenario dimension or complementary
attribute levels.

A focal observation additionally requires, on each row, equal ScenarioType
and ScenarioTypeStrict and a recognized level for that type; the two rows must
resolve to the same focal dimension, with mapped levels summing to one. Preserve
the exact map: Species has Humans/Hoomans=1 and Pets=0; Gender has
Female/Females=1 and Male/Males=0; Fitness has Fit=1 and Fat=0. Its positive bit
is the saved row's mapped level. No row can belong to two focal dimensions.
One focal observation and one Intervention observation from the same valid
pair are intentional overlap, not duplicate records.

The adapter must retain source-pair dispositions separately from projected
dimension records, and report each original common-cohort and added TR2 support
disposition. Semantic expectations below compare exact ID membership and bits,
not merely aggregate rates. After projection, `(response_id, dimension)` is
unique; duplicating or omitting a manifest-bound projected record refuses
verification rather than silently deduplicating it.

## Literal semantic bank

For every case below, use fresh opaque constructed response IDs. Unless a row
explicitly mutates identity or binary fields, both rows have UserID `SEM-U0`,
ExtendedSessionID `SEM-S0`, and the same case-specific ResponseID. The first
row has Saved=1, Intervention=0; the second has Saved=0, Intervention=1.
Thus every valid pair initially has Intervention positive bit one. Metadata
triples in the table are `(ScenarioType, ScenarioTypeStrict, AttributeLevel)`.
An empty string is a present but empty value, distinct from an absent header.

Each row below defines a separate two-row fixture and its complete expected
dimension membership. `I` means Intervention; `S`, `G`, `F` mean the three
focal dimensions. The stated positive focal bits follow the original map.

| Case ID | Saved-row metadata | Unsaved-row metadata | Expected projection |
|---|---|---|---|
| `R-SEM-FOCAL-S` | `(Species,Species,Humans)` | `(Species,Species,Pets)` | S=1 and I=1 |
| `R-SEM-FOCAL-S-ALIAS` | `(Species,Species,Hoomans)` | `(Species,Species,Pets)` | S=1 and I=1 |
| `R-SEM-FOCAL-G` | `(Gender,Gender,Female)` | `(Gender,Gender,Male)` | G=1 and I=1 |
| `R-SEM-FOCAL-G-ALIASES` | `(Gender,Gender,Females)` | `(Gender,Gender,Males)` | G=1 and I=1 |
| `R-SEM-FOCAL-F` | `(Fitness,Fitness,Fit)` | `(Fitness,Fitness,Fat)` | F=1 and I=1 |
| `R-SEM-NONFOCAL` | `(Age,Age,Young)` | `(Age,Age,Old)` | I=1 only |
| `R-SEM-UNKNOWN-TYPE` | `(Unknown,Unknown,Alpha)` | `(Unknown,Unknown,Beta)` | I=1 only |
| `R-SEM-EMPTY-METADATA` | `("","","")` | `("","","")` | I=1 only |
| `R-SEM-UNKNOWN-LEVEL` | `(Species,Species,Unknown)` | `(Species,Species,Pets)` | I=1 only |
| `R-SEM-EMPTY-LEVEL` | `(Species,Species,"")` | `(Species,Species,Pets)` | I=1 only |
| `R-SEM-STRICT-MISMATCH` | `(Species,Gender,Humans)` | `(Species,Species,Pets)` | I=1 only |
| `R-SEM-ROW-DIMENSION-MISMATCH` | `(Species,Species,Humans)` | `(Gender,Gender,Male)` | I=1 only |
| `R-SEM-NONCOMPLEMENT-HIGH` | `(Species,Species,Humans)` | `(Species,Species,Hoomans)` | I=1 only; focal level sum two |
| `R-SEM-NONCOMPLEMENT-LOW` | `(Species,Species,Pets)` | `(Species,Species,Pets)` | I=1 only; focal level sum zero |

Repeat each valid case with Saved swapped between its two rows, leaving all
other fields fixed. Intervention becomes zero; any retained complementary focal
bit also becomes zero. Membership must not change. This checks the literal
`Saved*(1-Intervention)` orientation and both signs; it does not infer choice
from row order. Reverse row order and separate the rows across input chunks in
future execution: membership and bits must still be identical.

For malformed pairs, start from `R-SEM-FOCAL-S` and apply each mutation
independently. Each affected response contributes no dimension observation:

| Malformed case | Mutation and required disposition |
|---|---|
| `R-BAD-ORPHAN` | Keep one row: one orphan, no invented mate. |
| `R-BAD-THREE-ROWS` / `R-BAD-FOUR-ROWS` | Append a copied side / both sides: duplicated response, not a valid pair. |
| `R-BAD-SAVED-SUM` | Set both Saved values to zero; repeat with both one: invalid pair. |
| `R-BAD-INTERVENTION-SUM` | Set both Intervention values to zero; repeat with both one: invalid pair. |
| `R-BAD-BINARY` | In each binary field in turn, substitute empty, `2`, `1.0` or ` 1`: invalid pair, no coercion. |
| `R-BAD-EMPTY-ID` | Empty response, user or session identifier in turn: invalid, even if both rows share the empty value. |
| `R-BAD-USER` / `R-BAD-SESSION` | Change the user / session on one row: invalid pair, no cross-identity join. |
| `R-BAD-SPLIT-RESPONSE` | Give the two rows different nonempty response IDs: two orphans, not one joined pair. |
| `R-BAD-SAME-SIDE-TWICE` | Supply two identical copies of the saved row: invalid sums, no valid decision. |

Remove each required header in turn in a separate source-envelope case. The
entire input refuses at schema admission; it is not a valid zero-choice source.
Keep this distinct from the valid empty/unknown metadata values above. Preserve
all disposition counts. Missing or mutated pinned records during replay also
refuse verification; a failure cannot be repaired by dropping the case.

## Literal nonfocal selection sentinel and complement

Use one constructed fingerprint `R-SENT-U0`, four distinct session IDs
`R-SENT-S00` through `R-SENT-S03`, and twelve response IDs per session,
`R-SENT-Sss-P00` through `R-SENT-Sss-P11`. The frozen existing session hash
assigns the four sessions to groups 0,1,2,3. The existing choice-hash domain,
seed 20261107, tie-breaking and lowest-three rule do not change.

Before assigning any choice values, rank all twelve response IDs for each
group using its Intervention choice hash. Give the three lowest-ranked pairs
the valid nonfocal metadata `(Age,Age,Young)` / `(Age,Age,Old)`. Allocate the
remaining nine IDs, in exact response-ID order, three each to Species, Gender
and Fitness with the complementary levels above. This ID/metadata assignment
uses no outcome. A later implementation must retain its explicit membership
manifest before assigning the literal bits; no hash computation is claimed in
this prose-only build.

In each group, assign Intervention bits **101** to the three selected nonfocal
pairs in their Intervention-hash order. Assign Intervention bit **1** to all
nine focal pairs. Construct each pair with saved first row, unsaved second row,
and Intervention fields `(1-b,b)` for desired bit b. Set all focal saved levels
to their mapped positive value. Every pair remains complete and valid.

There are twelve valid pairs and twenty-four raw rows per group. Correct
projection has twelve Intervention observations and three in each focal
dimension: twenty-one projected records per group, with exactly the intended
overlap. Correct selected Intervention triple is 101 and its never-trading
indicator is zero. The deliberately wrong focal-only union selects three ones
and returns one. This wrong arm must disagree; it is not an estimator candidate.
The focal indicators are one. Over all four groups, correct Intervention outer
means are zero and the wrong arm's means are one. These constant constructed
vectors are semantic oracles, not a stability or variance result.

The complement uses exactly the same IDs, metadata, hashes and selection,
swapping Saved on both rows of every pair while leaving Intervention fields
and attribute levels fixed. The selected nonfocal bits become **010**, all focal
Intervention bits become **0**, and all focal chosen-level bits also reverse.
Correct never-trading remains zero; the wrong arm remains one; focal
never-trading remains one. The two-sided indicator is invariant to this
complete sign reversal. Verify literal selected bits as well as the indicator,
so a reversed intervention coding cannot pass through that invariance alone.

Repeat the sentinel with each valid Intervention-only metadata template from
the semantic table replacing its three nonfocal pairs. Keep IDs, bits, counts
and expected disagreement fixed. These are deterministic adapter cases, not
new stochastic worlds or extra draws. An adapter that treats only familiar
nonfocal types correctly must fail the unknown and mismatch variants.

## Original common-cohort second-session edge

Construct one fingerprint with nine complete focal pairs in session `EDGE-S0`:
three Species, three Gender and three Fitness. Add one complete valid nonfocal
pair in distinct session `EDGE-S1`. Before any TR2 split, original counts are
three for each focal dimension and ten for Intervention; Intervention spans
two sessions. The original `good_user` predicate is true. A focal-only
Intervention branch would incorrectly count only nine choices in one session
and wrongly remove the fingerprint from the original common cohort.

TR2's additional support still fails: two sessions cannot fill four disjoint
session groups with at least three choices in every group and dimension. Keep
`original_common_eligible=true` separate from `tr2_split_supported=false`.
This is one unit-level admission case, not a claim that the 1,000-unit source
floor has been met. Do not reshuffle, duplicate sessions or invent chronology.

Repeat with every valid Intervention-only metadata template for the second
session. Then replace the second-session pair with each malformed-pair type:
it no longer supplies a valid second Intervention session, and the original
common-cohort predicate is false. A fingerprint with only nonfocal decisions
in several sessions also remains outside the common cohort because the three
focal dimension counts are absent. This prevents correcting the union by
accidentally weakening original common-cohort membership.

## Exact paired/noise variance oracle

For one fingerprint and one outer half, let R1 and R2 be the two selected-triple
never-trading indicators, Y=(R1+R2)/2, and D=(R1-R2)^2/4. The proposed noise
estimate is D. Conditional on a common probability q and independent groups,
the complete enumeration is:

| (R1,R2) | Conditional probability | Y | D |
|---|---|---|---|
| (0,0) | (1-q)^2 | 0 | 0 |
| (0,1) | q(1-q) | 1/2 | 1/4 |
| (1,0) | q(1-q) | 1/2 | 1/4 |
| (1,1) | q^2 | 1 | 0 |

Therefore E[Y]=q, Var(Y)=q(1-q)/2 and E[D]=q(1-q)/2. At q=0 or 1 the
variance is zero; at q=1/4 or 3/4 it is 3/32; at q=1/2 it is 1/8. These are
exact rational arithmetic targets for future enumeration, not simulated
measurements. In the existing IID triple generator,
q=p^3+(1-p)^3=1/4+3(p-1/2)^2. The existing dependent-triple generator uses
the same q directly. The paired identity requires independent equal-q groups,
not independent choices inside each triple.

For independent fingerprints with fixed conditional settings mu_i and errors
of conditional variance v_i, the expectation of the usual sample variance of
Y (denominator N-1) is the sample variance of mu plus mean(v_i). Thus subtracting
mean(D_i) is unbiased for that finite collection's setting variance only when
the stated D identity holds. This is a moment identity, not a claim that a
ratio, bootstrap interval or finite-sample category is unbiased. Repeated
fingerprints in the whole-unit bootstrap carry their existing paired records;
they do not become new independent session measurements.

For a random-fingerprint population with setting variance T and
v=E[q(1-q)], independent equal-q replicates have inner correlation
T/(T+v). The existing Spearman-Brown transform gives
2*T/(2*T+v)=T/(T+v/2), the reliability of their mean. This explains why the
sampling and split-half routes target the same reliability under that model.
It is not an identity for the expectation of their finite-sample estimators.
Zero observed variance, nonpositive reliability or nonpositive corrected side
variance retains the sealed undefined-result policy; do not replace a ratio
with zero, clip it into [0,1], or report a stability category.

## Explicit assumption failures, without a replacement model

Let q1=E[R1], q2=E[R2] and c=Cov(R1,R2), conditional on the fingerprint's
declared setting. The complete joint table has probabilities
P11=q1*q2+c, P10=q1*(1-q2)-c, P01=(1-q1)*q2-c and
P00=(1-q1)*(1-q2)+c. All four must be nonnegative. Exact algebra gives:

    Var(Y) = (q1*(1-q1) + q2*(1-q2) + 2*c) / 4
    E[D] = (q1 + q2 - 2*q1*q2 - 2*c) / 4
    E[D] - Var(Y) = (q1-q2)^2 / 4 - c

The table below fixes four hostile joint distributions and their exact noise
quantities. These are assumption diagnostics, not in-assumption recovery cells
or claims that the instrument can infer hidden q1, q2 or c from two indicators.

| Case | q1, q2, c | True Var(Y) | E[D] | E[D]-Var(Y) |
|---|---|---|---|---|
| `R-NOISE-UNEQUAL-Q` | 1/4, 3/4, 0 | 3/32 | 5/32 | 1/16 |
| `R-NOISE-POSITIVE-COV` | 1/2, 1/2, 1/4; R2=R1 | 1/4 | 0 | -1/4 |
| `R-NOISE-NEGATIVE-COV` | 1/2, 1/2, -1/4; R2=1-R1 | 0 | 1/4 | 1/4 |
| `R-NOISE-OPPOSITE-CERTAINTY` | 0, 1, 0 | 0 | 1/4 | 1/4 |

The same decomposition applies across outer halves. If Y_A=mu_A+e_A and
Y_B=mu_B+e_B, with conditionally zero-mean errors, observed covariance contains
Cov(mu_A,mu_B)+E[Cov(e_A,e_B)]. For fixed independent fingerprints, the analogous
sample-covariance expectation adds the mean of their conditional cross-half
covariances. Side-variance subtraction alone does not remove that numerator
term. The existing correction therefore needs its stated cross-half
independence restriction too. Disjoint session IDs and fixed choice counts do
not establish equal q or independence.

Preserve the original `R-ALIAS` diagnostic and its identical observations under
two causal labels. Persistent context can be inseparable from the measured
setting. No new state-removal model, expanded trait claim or compensating
subtraction is authorized here. The warranted target, if later qualified,
remains non-temporal cross-session consistency of the specified readout under
the stated noise model.

## Future replay and owner review

After owner approval, an implementation would serialize the literal raw pairs,
their source-pair disposition table, dimension projection, selected IDs/bits,
and independent expected tables. Replay must rebuild from those same raw pairs
using an independently expressed oracle, not copy producer statistics. Include
row/chunk reordering, all sign complements, source-pin mutation, duplicate or
missing projected records and exact original/new support dispositions. Preserve
every failure. No module import or execution, fixture generation or selector
was performed for this document; a later bounded selector needs the owner's
serial numerical slot.

Owner review still must resolve the previously stated operationalization and
statistical qualification holds. These new semantic cases do not qualify the
original source, confirm full split support, establish empirical interval
coverage, replace a mandated scientific comparator or admit a human run.

## Source pins

The table records code/design/review bytes read for this additive proposal.
No human source archive or private choice/count array was read or scanned.
The private delivery receipt also pins the unchanged four generic files.

| Repository-relative source | SHA256 |
|---|---|
| `runners/theory_days/moral.py` | `b7c05a08f9222378a4a354949080452292a7b48c13c4436bc2b505abea4b8c15` |
| `runners/theory_days/backlog_intake.py` | `be1ca76ae9edc17d14e59abc34e384597b3f87ea5a9ed9ff0081738d1f971473` |
| `docs/design/stage-15/theory-days/B2.md` | `b1c5972edea620cdf6d798511bf5d8443c7191bfcbeaeda67be61934f92fe38f` |
| `docs/design/stage-15/theory-days/B2.s.md` | `cc70b51cb0c889ae3cefaf3e68065d96faeebbec1e036c9982a641f346fcdc93` |
| `docs/design/stage-15/week6/TR2_SOURCE_SUCCESSOR_V1.md` | `84073ebe8146e53c710008fa398a986e911555e38094c6e907a8e879b436dc22` |
| `docs/design/stage-15/week6/TR2_SOURCE_FIXTURE_PROTOCOL_V1.md` | `57a1b2a93179edf3a4c27f8e6b522cbca3b3592ab29be01310caa4c978554a2c` |
| `.agent-state/drive-20261115/BUILDER_C_TR2_READONLY_REVIEW_V1.json` | `8a58ef3f3c2c91a8bd7ae46c9fe34c37092310209027e3080cd857e5b80c430f` |
| `.agent-state/drive-20261115/BUILDER_A_TR2_NOISE_REVIEW_V1.json` | `05586a61507e4be7d51e68fdcc3e1d18a4ae30a00ce8e48c0ad24c4966f6a845` |
