# P7 causal batching with prefix-cache reuse

The [uncached batching pilot](P7_BATCH_PILOT.md) preserved all original pilot
losses within the fixed tolerance, but recomputing the full context for each
group increased typed-text cost. It remains a completed, valid engineering
comparison; neither it nor the original scalar pilot is overwritten.

This bounded revision retains exactly that pilot's 612 targets, causal grouping,
native IDs, context windows, CPU float32 model and 0.0001-nat loss tolerance.
Between groups it uses the original scalar scorer's already validated prefix
cache. The longest member drives the group forward; all member losses come from
their unchanged causal positions. Across groups only identical native prefixes
are retained. Edits, retokenization and left-crop changes still invalidate reuse.

**DESIGN CHECK.** LESSONS 3–5 reread October 18. Scientific null/alternative
effects do not affect these gates. Every native loss is compared to the frozen
original pilot. Exact target coverage, source/crop/token identities, nonnegative
finite losses and unchanged tolerance are required. Tiny real-model branch,
retokenization, Unicode, overflow, shortened reentry and corruption tests run
before dispatch, alongside domain checkpoint resume, immutable reentry and the
real counted-runtime fresh verifier. Fresh production verification reconstructs
every target and checks six direct forwards independently.

The [batch pilot contract](P7_BATCH_PILOT.md) supplies unchanged authority,
privacy and source rules. One counted below-normal CPU slot, two numeric threads,
600-second forecast, 1,800-second combined wall bound and 256 MiB output cap.
The separate handler rejects main. No paid/GPU work, automatic retry, scientific
verdict or D30.s ranked successor credit follows. Preserve prior compute charges.

Even a faster pilot does not establish full-corpus cost: neither selected domain
in the original pilot contains a cropped target. Full context/work-shape coverage
and measured admission are required before main. No context shortening, target
selection or threshold relaxation is licensed by this optimization.
