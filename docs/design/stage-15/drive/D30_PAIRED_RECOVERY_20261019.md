# D30 paired occurrence-identity engineering recovery

The original D30.fake and D30-extension.fake attempts stopped before fitting:
the correction join assumed that session, first-word index and bigram text
uniquely identify a typed bigram. A retained first word can instead precede
multiple newly typed occurrences with identical text. The original rows are
valid; that joining assumption was not.

The separate recovery replays the original occurrence-generator order and uses
each retained original source-row position to identify both constituents.
It verifies session, first index and marker text at that position, refusing
mismatch. No original occurrence is merged, dropped, reclassified or imputed.
The source-row position was already retained by the frozen paired design.
All estimator, resampling, reference, secondary-label and cost rules in the
[original contract](D30_PAIRED_FIXED_20261019.md) remain unchanged.

A new constructed regression retains two identical bigrams with the same first
word and distinct second words, then checks their distinct correction labels.
Wrong and missing positions refuse. The full earlier twelve-check battery and
counted native source/fit replay also run against the separate recovery module.
Original frozen code, failed roots and logs remain intact. This consumes each
card's one engineering retry; all original validation, failed elapsed time,
repair checks and native validation remain charged within the original ceiling.
The larger failed elapsed time is conservatively charged to both retries.

**DESIGN CHECK.** Relevant LESSONS 3-5 and CONTROLS were reread for this paired
implementation. Known positive/reversed effects and the exact identical-arm null
are unchanged. A source join must preserve distinct original occurrences and
refuse a different identity, regardless of scientific outcome. No scientific
result or threshold was consulted to construct this repair.
