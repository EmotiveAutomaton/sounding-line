# AUTH prompt-matched pair allocation

Implementation of the existing Week 3 FIC1/AUTH allocation carried into Week 4,
frozen before drawing pairs or observing any authorship scores. The complete
[exact source](AUTH_SOURCE.md) has 990 nonempty unique text candidates from all
24 original writers; both genres contain 495 sessions. Its final-surviving scope,
400-word limit and artificial seams remain explicit. No deleted text is restored.

DESIGN CHECK: LESSONS 2–5 and CONTROLS 4–7 read; G220's section, corrections and
afterword reread. This is a matched comparison, not a causal isolation of genre
or proof of play. Under either authorship null or alternative, truth balance,
genre balance and exact prompt-pair matching must hold. Missing support refuses
allocation; no replacement population or outcome-guided selection is allowed.

Within each genre, enumerate distinct-session same-writer candidates on different
prompts. Order each pair's texts by session identity, then sort candidates by
SHA-256 of seed 20261102, genre and ordered session IDs. For each candidate in
that order, retain the first text as anchor and find a second-writer session on
the second text's exact prompt. Rank those alternatives by the seeded hash of
the positive pair IDs and donor session ID. Select the first unused unordered
text pair; if none exists, census that unsupported candidate and continue in the
unchanged order. Take the first 1,000 supported blocks per genre. Each block has
one positive and one negative pair with identical ordered prompt assignments.
Content-duplicate or reversed pairs are forbidden. All original writers must
appear as positive authors in each genre, or preparation fails.

This yields 4,000 pairs, half same-writer, half different-writer, split equally
between genres. Pair order is positive then matched negative within each frozen
block. The first 50 argumentative blocks (100 pairs) are initial calibration;
the next 50 are reserved for the approved fresh correction if needed. Calibration
IDs are excluded from primary analysis when used. The unused reserve can enter
the unchanged main only if the first calibration passes. No score is accessed
while selecting these sets. All pairs are frozen now, so a later failure cannot
choose more favorable replacements.

The private join keeps identities, genre, prompts and truth. A separate provider
projection has only the two unchanged candidate texts. Whole-input duplicates
are checked independently of session IDs. Corpus preparation makes no API call
and computes no authorship score. Independent validation reconstructs each pair's
truth and prompt match directly from the sealed session map, checks coverage,
uniqueness, balance and exact text projection, and reruns the deterministic draw
in a fresh process. Input order reversal must leave the allocation unchanged.

**The case and its check.** Native constructed examples include both truth
classes, both genres, prompt matching, changed identity/text refusal and empty
support. Full preparation requires all declared blocks and writer coverage.
Calibration discrimination remains untested by source preparation.

**The smaller route.** Fail closed if 4,000 balanced pairs cannot be supplied.
No downsampled paid cohort. Reserve 60 CPU seconds for construction/targeted
checks, at most 30 for native validation, and at most 120 for full allocation and
fresh replay, all drawn from the 600-second AUTH reserve and unchanged shared
FIC1 7,200-second ceiling. One CPU thread, 2 GiB RAM, 128 MiB output, no GPU.
Initial and fresh provider calibration and scientific analysis remain separate
implementations and admissions.
