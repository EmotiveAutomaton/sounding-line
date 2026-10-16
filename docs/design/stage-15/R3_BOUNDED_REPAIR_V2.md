# R3 bounded-statement repair, version 2

The curator explicitly authorizes a Gear 3 healing pass on October 15. The
completed Stage 15 v1 pilot stays failed: one whole profile exceeds the original
statement limit despite normal provider termination. Its requests, responses,
source pins, cost and write-through remain immutable. Stage 14 stays closed.

**DESIGN CHECK.** LESSONS sections 3, 4 and 5 were reread for this repair.
Under the null of a still-defective representation, any malformed, duplicate,
unsupported, empty, truncated or overlength response fails the whole pilot gate.
Under the alternative, all six discarded-pilot responses satisfy every literal
condition. There is no intermediate admission band. Source or accounting defects
also hold main; neither outcome establishes semantic faithfulness or prediction.

The only task change is explicit word-bound encoding in the existing statement
field: a nonempty non-whitespace word followed by 23 optional space-and-word
groups, anchored at both ends. This is equivalent to
`^[^\s]+( [^\s]+){0,23}$`, with the optional groups expanded on the wire.
Statements contain 1-24 words separated by
single ASCII spaces, without other whitespace. This encodes the existing upper
bound and canonicalizes whitespace prospectively; it does not truncate output,
increase the bound, reduce the number of permitted statements or change the
evidence. The independent parser still counts Python whitespace-separated words
and checks the complete original contract. Whole provider responses are retained.

The [official schema documentation](https://platform.claude.com/docs/en/build-with-claude/structured-outputs#pattern-support-regex)
was read October 15: character classes, groups, anchors and simple bounded
quantifiers are supported. The unpaid token-count preflight rejected a range
quantifier over a group containing `+`; that refusal is preserved locally.
The equivalent explicit optional-group encoding is checked separately before
any batch reservation or submission. Unsupported length or array-maximum keywords are not
substituted for enforced constraints. Provider token-count acceptance is a
preflight, not proof of generation or scientific validity. Local boundary checks
cover empty/one/24/25 words, repeated spaces, tabs, newlines, Unicode whitespace,
duplicates, evidence bounds and truncation, plus full fake-provider lifecycle,
ambiguous submission and actual main-gate refusal.

Keep Sonnet 5.5, batch mode, low effort, 1,500 output tokens, the same three pilot
writers, own/donor earlier histories and separate 31-writer main. All six pilot
requests are regenerated as a separate version; do not selectively repair or
combine outputs with v1. Pilot writers remain excluded from main. Future targets
and outcomes never enter the wire. Compare serialized history bytes to v1 before
dispatch. No tools, caching, redirects, automatic retries or model substitution.

The locked campaign ledger retains its $50 shared ceiling and node caps. Fresh
token counts, 30% input allowance, maximum output and two-cent rounding reserve
precede the sole POST. The [official pricing page](https://platform.claude.com/docs/en/about-claude/pricing)
was checked October 15: batch input/output rates remain $1/$5 per million tokens.
No new tranche or reserve-node spend. Ambiguous submission retains its reservation.

Use `profiles_v2.py` and `profile_supervisor_v2.py`, with raw outputs isolated in
`results/phase_2_4_stage_15/raw/r3-profiles-v2/`. Register native disappearance and
terminal watches before submission. Retrieval is bounded to one day, every two
minutes, without changing the six-hour owner-health cadence. A main requires all
six valid pilot responses, complete usage, independent verification and pinned
full internal write-through; the operator explicitly admits it after inspection.
Main generation itself has no dependency on an engine prediction result. Using
profiles as features still requires F4/backbone controls, native admission,
engine/twin gates and frozen evaluation. A format pass never makes a judge.
