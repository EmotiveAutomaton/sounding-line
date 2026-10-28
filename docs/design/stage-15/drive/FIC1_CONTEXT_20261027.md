# FIC1 pooled context reconstruction

This implements the already approved independent-writer context correction for
FIC1's pooled profiles, retaining the literal leave-writer-out diagnostic.
It is a construction component, not a scientific admission or a human score.
The completed observed, prefix, nuisance and scoring operators stay unchanged.
LESSONS sections 3–5, CONTROLS sections 1–7, the play-frame theory row and its
afterword, and Week 3 identification/resource/FIC1 clauses were reread.

FIC1 pools counts and timing observations. A mean of session rates or medians
would therefore change its operator. The explicit implementation convention is
to replace each selected session portion by its prompt's mean sufficient
measure per production word, then pool those measures using the recipient's
selected word counts. Each donor session has equal weight in that prompt mean.
Whole recipient sessions use whole donor sessions. A partial recipient session
uses the same exact first-word quota in every donor session; any donor lacking
that quota makes the context unsupported. This preserves prefix-position cues
without reusing recipient feature values or selecting only long-enough donors.
Word and punctuation mass retain the complete vocabulary denominator; timing
uses the donor empirical distributions and their interval counts per word.
The pooled weighted median uses the midpoint of the two neighboring values at
an exact half-mass boundary, agreeing with ordinary median for integer masses.
Invalid timing contributes no intervals, exactly as in the observed pooling.
The context profile does not read a recipient's word choices, punctuation or
timing values. It retains only prompt, membership, quota and declared nuisance
covariates. Final-document context uses the same rule with final words, keeping
mixed provenance and the original length/accepted-share covariates explicit.

This sufficient-measure convention is an analyst implementation of the pooled
control, separately labeled from the original session-feature mean. It must
pass complete null and planted calibration before it can license anything.
It is not silently substituted into the completed WA0 or GEN1 results.

Three writer folds use WA0.h1's fixed seeded allocation. For rotation f, donors
are fold f, probes are fold (f+1) modulo three, and the gallery contains both
non-donor folds. Every original supported probe appears once. Missing donor
prompts or whole-profile support stay unsupported, with no redraw or fallback.
The original leave-writer-out construction is retained as a diagnostic only.
Permuted assignments preserve genre, prompt and frozen writer-role counts and
rebuild the complete chronological prompt halves and exact prefixes. One
assignment is reused across all rotations. This component exposes the builder
but does not run the scientific permutation bank.

Each observed or context gallery fits its own full-length nuisance coefficients
on its own B rows, with fixed roster, using the unchanged projection. Equal-word
length levels remain raw. No observed fitted coefficients are reused for a
control or a new rotation. The all-length support rule and scoring gates remain
unchanged. AUTH stays separately gated.

Known-answer checks cover pooled denominators, weighted medians, missing donor
support, role exclusion, recipient-feature independence, exact constant-context
parity, fresh nuisance fits, fixed rosters, permutation conservation, order
invariance and immutable fresh-process replay. Passing these checks establishes
construction only. Full calibration, measured corpus cost and complete study
admission are still required before any human identification score.

Reserve 180 CPU seconds for construction/targeted checks in addition to the
previous 2,030-second charge. Constructed native execution plus independent
replay is capped at 120 CPU seconds, one numerical thread and 3 GiB projected
RAM, within FIC1's original 7,200 seconds. No S4 extension is invoked here.
