# Week 4 VAL calibration

Prospective implementation of the ratified Week 4 packet section 5 and existing
seven-node approval. This is a reader check, not evidence about inferred values.
The historical Week 3 source, prompt, schema and failures remain unchanged.

**DESIGN CHECK.** LESSONS sections 3–5 reread November 5 for this design.
Under a null reader, constant or unrelated codes must fail agreement despite
valid JSON. Under a correct reader, known binary codes pass. Both require the
same complete hundred requests and at least 98 valid replies. Missing, repeated,
foreign or changed identities refuse replay. Malformed replies remain invalid;
they are never filled with a guessed value or silently removed from agreement.

**The case and its check.** The reader must identify explicitly endorsed goals
in public explanations. Rebuild the original seed-20261026, at-most-ten-per-person
sample on the complete CA1.s1 comparison source and require exact equality to
the corresponding Week 3 frozen items and links. All 836 mandatory people and
200 additional people remain in the population census, including those without
an explanation. Only explanation text is sent; no identifiers, demographics,
profiles, option choices or writer-typed CoAuthor text are transmitted.

**The smaller route.** This node uses exactly the already approved CA1.s1
restriction. No further population reduction is automatic. Its CPU source and
transport overhead has a conservative 300-second allocation, charged to V2's
7,200-second consumer ceiling; no model fitting or embedding is performed here.
The separate CA1.s1 encoding cost hold is unchanged. Paid VAL stays within $2
and the campaign within $10, with dispatch closed November 6 at 17:00 PST.

Retain the Week 3 semantic deduplication and item order. The first hundred unique
in-scope items form calibration; the next hundred are reserved for the one
permitted fresh prompt correction. The unchanged ten-bit Schwartz encoding plus
other, original prompt and 32-token maximum are inherited from `week3_val`.
Its sources were reviewed in that earlier design; this implementation claims no
new literature review. Each actual request is reconstructed and source-pinned.

Before any provider access, the operator reads every calibration text and freezes
one code and short rationale per item. Provenance is **agent-made blind before
provider access**, never human gold. The complete gold hash is frozen before
access/token-counting. Calibration selection never uses labels or outcomes.

Pooled Cohen's kappa uses all 1,100 binary judgments (100 texts × 11 categories).
For a malformed response, a distinct abstention symbol 2 enters the agreement
calculation for all eleven judgments. It is not a scientific value label and
cannot agree with either gold value. This preserves the complete denominator
without treating invalid outputs as absence. Require pooled kappa at least 0.6
and format at least 98/100. Undefined kappa fails. Report per-category kappa when
the complete blind reference prevalence is at least 5%, with invalid counts and
provider-positive prevalence over all hundred. Per-category results are diagnostic,
not extra gates or a license to salvage selected categories. Constructed perfect,
constant, swapped and invalid-output fixtures verify these rules.

Only initial calibration is implemented here. Main requires a complete recorded
calibration pass, reconciled usage and its own source/cost/coverage admission.
One prompt correction on the fixed fresh hundred is allowed by the existing
approval; it requires a separately recorded version. A second failure stops VAL.
No automatic retry after uncertain submission. Reservation precedes POST through
the unchanged Week 4 guard. The retrieval-only monitor freezes raw responses,
checks full batch identity/coverage and reconciles measured billing before its
terminal receipt. Unknown usage retains the reservation. All landing steps and
stage final-packet reporting remain binding.
