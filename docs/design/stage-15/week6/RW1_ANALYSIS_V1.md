# RW1 prospective association and uncertainty handler

Status: full analysis, successor marker forms and constructed fixtures drafted
for owner review, **not tested or admitted**. No human projection, annotation,
vocabulary fitting or association has run. Source V1 and its nine passing tests
remain unchanged. Authority: [packet section 3F](PACKET.md), the
[execution addendum](EXECUTION_ADDENDUM.md), and the owner's November 15 review
of the primary conventions below. The card's complete charge is 20,000 CPU-seconds,
including source, markers, prior preparation, failed work and fresh replay.

The relevant supplied Round 16 plan-test note, Round 17 resolved-plan ruling and
Round 18 source-search/hold notes were read. This implements the packet's worry
correlation. It neither measures the entire theoretical quantity Stress nor
establishes a maker setting, a causal effect of planning, or a reader benchmark.
No theory file changes follow from this construction.

## Source, markers and units

The exact first-wave source and dataset-license record are in
[RW1_INTAKE](RW1_INTAKE.md). The unchanged source V1 must complete and independently
replay every original person, with only long text and the five commissioned
ratings imported. Every original person remains in the prospective roster;
missing ratings and empty/no-word text retain separate dispositions. There is
no observed-variation selection, demographic import or substitution of short text.

The new `week6_rw1_source_v2` consumes the completed V1 source and its identical
ordered 200-sentence sample. It adds a time/place column to the hand and list
forms. Each builder seals hand judgments before consulting automatic answers,
then seals the separate list form bound to that hand-file hash. Plan judgments
retain the unchanged original candidate and threshold. Time/place judgments use
the same two genuine builders and same 200 sentences; no new participant study
is proposed. Blank forms and constructed matching labels prove no independence.
The owner reviews the actual isolation, provenance and semantics.

`week6_rw1_context_v1` freezes finite literal time/place lists and date/clock
patterns. Time words include today, tomorrow, tonight and weekdays; declared
relative phrases include next week and this weekend. Month names require a
declared date/preposition pattern, so bare modal “may” is not a time marker.
Places are the finite home/work/school/university/hospital/shop/supermarket/park/
office/garden/parents/bank phrases in that module. The module's hash freezes the
complete lists; no corpus word discovery expands them. Unmatched plan sentences
are counted as **unknown-or-absent**, not proved to lack time or place.

The hand time/place column permits an explicit unknown. All 200 sentences stay
in each agreement denominator; unknowns count as disagreements, including two
unknown judgments. Both list/hand agreements and hand/hand agreement must reach
the original 0.80 threshold for this marker to become reviewable. Positive counts
and unknown counts accompany agreement. Semantic admission still requires owner
review. A passing plan marker can qualify the primary while an unqualified
time/place marker leaves that secondary instrument-held. No revision or genuine
annotation has occurred; any permitted revision needs its own prospective pin.

## Frozen primary conventions

The owner approved person-level seeded halves, signed positive word associations,
200 words with lexical ties, lowercase alphabetic tokens, no tuning, cross-half
application, raw word length, Pearson partial correlation and whole-person draws
that relearn both lists. The precise implementation is:

- Sort all original opaque person keys. With inherited seed 20261107 and split substream 11,
  permute once and put the first floor(N/2) people in one half. Keep this assignment
  throughout every draw; copies of one person cannot cross halves.
- Words are Unicode alphabetic runs, case-folded. Punctuation, including
  apostrophes, separates tokens. There is no stemming, stopword list, frequency
  floor, length tuning or outcome-selected tokenizer. Length is the raw count of
  these word tokens. Plan and bad-news denominators are nonempty sentences.
- Within each training half, correlate each word's **person-level presence**
  with worry using Pearson correlation. Retain training-variable words with
  strictly positive association, rank by largest signed association, and break
  ties lexically. Exactly 200 are required; fewer means unsupported vocabulary,
  without negative-word fill or a smaller list.
- Apply that list only to the other half: bad-news share is the fraction of its
  person's sentences containing at least one selected word. Swap halves and pool
  the resulting out-of-half shares. Training uses only people with worry and
  usable text. Missing-worry people can still receive held-out lexical features.
- Regress plan-sentence share and worry separately on intercept, word length and
  bad-news share. Correlate the residuals. This is an unweighted original-person
  Pearson partial correlation; weighted versions implement bootstrap copies.
  Constant/rank-deficient specified controls or absent residual variation remain
  unsupported. Complete cases are target-specific and their counts explicit.

The lexical control is a worry-associated proxy, not independently annotated bad
news. It can include unusual words and plan words if they meet the frozen rule.
No claim that it removes every substantive confound follows. Lists and all
person-level artifacts remain in ignored local storage.

## Uncertainty, secondaries and reporting

Each of 2,000 draws samples the entire original person roster with replacement.
All records/sentences from a person share her multiplicity. Both word lists are
relearned with those weights, then every estimable target is refitted. The half
assignment stays fixed. The bootstrap therefore conditions on this split but
does not condition on its fitted word lists. Each draw retains its vocabulary
hashes and support audit. A failed draw is retained and invalidates that target's
interval; no deletion or redraw is allowed. The person-iid sampling assumption
is explicit; algebraic agreement does not establish interval coverage.

The sole primary predicts a negative correlation at bar -0.05. A complete interval
strictly below -0.05 supports; an interval wholly above zero or wholly inside
[-0.05, 0.05] is against; otherwise it is inconclusive. Below 20 eligible people
and exactly degenerate bootstrap dispersion are descriptive statuses with no
scientific outcome. The primary reports bootstrap standard error, approximate
detectable magnitude and the negative support threshold. Unsupported inputs and
invalid uncertainty have their own statuses.

The same held-out worry vocabulary serves the anxiety, fear and relaxation
secondaries; it is not relearned from those outcomes. The beyond-fear-and-sadness
row adds those two ratings to the controls and reports both partial correlation
and incremental explained variance. These are descriptive secondaries without
additional primary verdicts. Each has its complete-case count.

When its literal marker is qualified, time/place compares the worry partial
correlation of the literal-matched plan share with that of unmatched plan share,
both over all sentences, on the same people and with the primary controls. Their
paired difference uses the same bootstrap draws. There is no new bar or primary
gate. Unmatched does not establish semantic absence; the recorded unknown counts
and two-builder check bound the wording. Without marker qualification these
three rows remain instrument-held and full-card completion is false.

## DESIGN CHECK and proposed fixture selector

LESSONS sections 2 and 3 were reread. The test file
`tests/test_week6_rw1_analysis_v1.py` is entirely constructed and **unrun**.
Its finite factorial sentence corpus has 640 people, 320 in each fixed half.
Let plan sign P and residual worry sign E have equally balanced marginals.
For every independent bad-news sign B and length sign L, joint counts are 17 for
equal P/E and 23 for opposite signs; thus E[P E] = -0.15. The zero fixture uses
20 in all four cells. Worry is the integer 5+E+B+L. Plan share is 1/4 or 3/4;
length is 216 or 256 tokens; exactly one of four sentences carries a 200-word
positive or negative vocabulary. Both learned lists recover the positive bank,
giving bad-news share zero or 1/4. Removing length and bad news leaves E and P,
so the partial correlation is exactly the specified value. This is a finite
arithmetic ruler, not an interval-coverage simulation or genuine marker study.

A separate literal-secondary ruler marks every plan in the high-plan group with
“tomorrow” by replacing an equal-length token opportunity. Its two plan shares
are affine opposites of P, so their partial correlations are -0.15 and +0.15,
and their paired difference is -0.30. It tests the declared comparison using
constructed language, not semantic qualification on participant sentences.

Other checks cover independently expanded dense weighted least squares,
held-out worry mutation, deterministic draws with both vocabulary fits called,
missing-data preservation, reachable support failure, negative-direction interval
boundaries, retained failed draws, literal positives/negatives/unknowns, fixed
200-row unknown denominators, successor blank/sealed forms, same-builder refusal,
owner-review refusal, bounded resume, and fresh replay of an explicit unsupported
route. The main supported runner is checked at resumable draw boundaries; a full
supported native 2,000-draw/replay qualification is not claimed by these tests.

## Runnable boundary, forecast and remaining admission

`week6_rw1_v1` implements the text features, vocabulary fits, all target estimators
and bootstrap. `week6_rw1_runner_v1` supplies bounded execute/verify, sealed
per-draw checkpoints and full fresh replay. Inputs are completed `prepared_run`,
completed `marker_review_run` from successor V2, and exact owner-written
`owner_review`. No builder approval receipt exists. Configuration:
`{"phase":"RW1","draws":2000,"max_new_draws":20,"max_wall_seconds":600}`.
Successor form/review phases are `RW1-marker-forms-v2` and `RW1-marker-review-v2`.

Each full pass has 4,002 vocabulary fits, at most 14,007 small residual fits,
source-to-sparse-table construction, checkpoint/summary work and final audits.
Complete replay repeats them. These are operation counts, not a measured human
cost forecast. Table construction repeats at each invocation and must be priced.
The first counted-slot cost stage must forecast the full source, markers, all
targets and fresh replay against the retained card allowance. A forecast over
7,200 CPU-seconds uses the first 100 draws as the checkpointed first-5% pilot;
no separate pilot allowance is created. Cooperative time checks occur between
draws, so native resource guards still protect an atomic fit. If necessary, the
existing prospectively frozen whole-person sample route remains separate and
explicitly sample-scoped.

Pending: owner design/fixture review and serial fixture execution; genuine
two-builder marker qualification; source preparation; exact owner source/semantic
receipt; any required complete native qualification; design commit, runtime,
campaign-start and in-slot cost admission. Source licensing and passed source-V1
tests do not satisfy these scientific gates. The immutable delivery manifest
will record code, design, fixture, source and annotation dependency pins before
any new numerical selector is run.
