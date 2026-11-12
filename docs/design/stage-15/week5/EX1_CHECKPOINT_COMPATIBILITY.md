# EX1 checkpoint compatibility

**DESIGN CHECK.** Re-read LESSONS sections 3–5 and the unchanged EX1 design.
This is an operational repair, not a new analysis or export scope. The original
EX1 handler, design, sources, prefix and native runtime remain immutable.

The first counted prefix saved 70 of 1,399 sessions and a sealed pause. Its
producer returned valid integer completion counters without a phase string.
The watcher incorrectly required that optional string when counters were
present and emitted a false disappearance alert. The original alert is retained.
The notification validator now accepts counters without a phase, while rejecting
an invalid supplied phase, incomplete or invalid counters, an empty hash manifest,
an unnamed operation, running output and any scientific admission. This validates
notification ownership only; it does not validate or authorize checkpoint reuse.

The original resume adapter treats EX1's document quantum as semantic, so it
cannot extend the prefix. The versioned v3 adapter adds only EX1's
`max_new_documents` to its module-specific operational keys. The v4 child and
v9 runtime differ from their predecessors only in those successor imports and
the runtime title. Existing runtime pins remain unchanged. Both directions keep
the same native containment, two-thread limit, accounting, resource floors and
complete fresh verification. Every predecessor source pin must survive; changed
inputs, scientific parameters, checkpoint bytes or a live predecessor still fail.

All 126 focused transition and resume checks pass. A separate constructed native
producer, stopped-owner copy process and fresh verifier authenticate the exact
copies for all four registered module families, including EX1. No human source is
used by that proof. Runtime and child source comparisons verify the import-only
change. The original 16 EX1 instrument checks remain pinned and passing.

The authenticated prefix retains 72 files and 80.703125 measured CPU-seconds.
Linear full execution plus independent replay projects 3,225.819 CPU-seconds;
doubling that projection still fits the remaining card allowance. The continuation
has a 9,000-CPU-second ceiling, within EX1's combined 10,000 allowance including
retained prefix and supervisor charges, and preserves the full population.
Completion requires every session and a fresh full replay. No prefix export is
materialized or copied. The campaign's local-only export restrictions stand.
