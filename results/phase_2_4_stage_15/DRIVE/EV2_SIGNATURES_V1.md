# EV2: recurrence of page signatures in the writer's other work

**Hypothesis.** Phrases selected as recurring departures on one page recur more
often in that writer's work on other prompts than in other writers' work on the
same prompts.

**METHOD.** Use the completed, authenticated exports of all 1,399 final CoAuthor
documents from the pinned ToMpathy engine and Qwen2.5-0.5B preview reader. Select
positive-departure phrases from each document's first 15 candidates that recur
across at least two sections or paragraphs. Count overlapping lowercase literal
matches on other prompts, using identical prompt mixtures and word denominators
for own-writer and other-writer rates. Average phrases within source document,
documents within writer, and writers equally. Intersect source support across
the real assignment and all 200 prompt-stratified session reassignments before
counting recurrence. Use 2,000 paired real-writer bootstrap draws with the phrase
roster and target corpus fixed. The [frozen card](../../../../docs/design/stage-15/drive/EV2_SIGNATURES_20261019.md)
records seeds, matching and admission decisions.

**Found.** The supported comparison is positive and its reassignment reference
passes the frozen bias check. The own-minus-other recurrence difference is
1.3842 occurrences per 10,000 words; its conditional 95% bootstrap interval is
0.0461 to 3.1419. Subtracting the mean fake-writer effect leaves a positive paired
contrast. **Means.** The week packet's signature route is supported for this
population: “recurs in the writer's other work”. This is an aggregate instrument
validation, not proof that every individual phrase is personal, a private
preference, or a human-only contribution. The badge is recorded here; no external
application deployment occurred.

The support table counts source documents and document-signatures (the same
literal in two source documents counts twice). Every document remains in the
target universe; unsupported source comparisons are not replaced with zeros.

| Population | Count |
|---|---:|
| Final documents retained as possible targets | 1,399 |
| Documents with an eligible signature | 1,231 |
| Documents without an eligible signature | 168 |
| Eligible document-signatures before matching | 3,666 |
| Writers with an eligible signature | 60 |
| Source documents supported in every assignment | 769 |
| Supported document-signatures | 2,348 |
| Supported writers | 52 |
| Signature-bearing source documents lacking common support | 462 |
| Document-signatures lacking common support | 1,318 |

The result table reports differences in literal occurrences per 10,000 words.
Intervals resample the same real-writer clusters with comparison pools fixed;
the reference row instead describes the distribution of 200 fake assignments.
These are descriptive, conditional estimates, not independent-corpus validation.

| Comparison | Mean difference | 95% interval or reference percentiles | Frozen classification |
|---|---:|---:|---|
| Own writer minus other writers | 1.384153 | 0.046113 to 3.141935 | Positive |
| Real contrast minus mean fake contrast, paired | 1.377820 | 0.054907 to 3.136307 | Positive |
| Fake-writer reference | 0.006333 | −0.389396 to 0.528575 | Bias check passes |

The reference standard deviation is 0.251375. Its absolute mean is below one
quarter of that spread, as required. The descriptive one-sided reassignment
probability is 1/201 = 0.004975124378109453: none of the 200 fake contrasts reaches
the observed contrast. It is registered as a diagnostic in the multiplicity
ledger, excluded from decision families. The instrument does not change the
drive packet's family-null counters. The positive badge follows the frozen
interval and control gates, not a multiplicity-adjusted discovery claim.

**Validation and integrity.** All 23 targeted checks and two counted native
rehearsals preceded corpus dispatch. They cover planted writer recurrence,
shared/prompt-only nulls, exact rates, support, Unicode and overlapping matches,
reassignment rosters, changed-evidence refusal, immutable reentry and runtime
stop boundaries. Corpus execution and a fresh process reproduced the complete
source authentication, statistic and all controls. The owner independently
checked all 9,057 source pins, all 10 terminal artifacts, saved source-rate
aggregation, equal-writer means, both bootstrap intervals, reference arithmetic,
support accounting and badge routing. Exact native workers exited and the
counted CPU slot was released. The original fixture assertion failure is
preserved in the [build record](EV2_BUILD_20261019.md); no corpus gate was changed.

Execution through verified terminal completion took 402.456 seconds under the
3,600-second ceiling, including fresh replay and runtime bookkeeping. This
comparison reused exported features and made no model, GPU or paid call.
The full reader's earlier cost remains separately accounted in its
[completed export](EV_FULL_READER_V1.md).

**Limits and next work.** Lowercase literal substring matching includes overlaps
and does not impose word boundaries or semantic equivalence. The supported
population is smaller than the original signature population; its unmatched
question remains open. Final text includes writer-typed and model-suggested
material. Repetition can reflect reusable wording or other stable context and
does not identify values, intention, attention or competence. The interval's
lower bound is close to zero, and no new population is validated. The departure
and habit comparisons remain unfinished; the typed-only habit variant remains
distinct. Carry this complete row and its limits into the Tuesday feature table
and scheduled daily integration. No new study was harvested from the wake.

[Aggregate evidence and hashes](EV2_SIGNATURES_V1.json). Raw phrases, text,
writer/session identifiers and detailed arrays remain private.
