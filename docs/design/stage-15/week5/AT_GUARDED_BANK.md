# Native guard for the corrected AT2 bank

This is an unadmitted engineering successor. The corrected bank roster keeps
all ten commissioned readers, their exact model/tokenizer revisions and the
already verified whole-writer pilot. Its corrected per-model forecasts remain
unmeasured. This design does not launch a model or select a human reader.

## DESIGN CHECK

**The case and its check.** The idempotent scorer is available, but the existing
native precision guard accepts a retained failed case rather than a generic
source chunk. The new `week5_at_scoring_guard_v1` accepts exactly the original
scorer's rows/manifest inputs and context configuration, invoking its unchanged
v5/v4 numerical function under the existing native guard's exact code. It does
not relabel the old guard as a different producer or modify any pinned module.
The cache/fresh check remains 0.0001 nats; sources, tokens, precision, eight-word
checkpoints, seeded 2% verification and immutable completion accounting remain.

The first qualification keeps the conservative guard unchanged for every model:
26 GiB available commit and 20 GiB RAM before load, yield requests below seven
GiB, six-GiB hard floors and a sixty-second cooperative grace. Owner admission
also retains the stronger 28-GiB commit start requirement for the largest
reader, its 20-GiB projected peak, counted slot and actual concurrent-reservation
checks. These thresholds are not measurements of any reader's memory use.
Per-model envelopes and cold-load/execute/fresh-verify costs still require owner
review; a later measured lower-memory guard would be a separately reviewed
successor. Refusal under these conservative thresholds does not change scope.

Collector v5 accepts this one exact wrapper in addition to the already reviewed
v4/v5 scorers. It requires the original numerical cores, v5, native guard and
wrapper at their literal hashes in the completed producer's pin map. Both
execute and verify guard receipts must occur in the immutable completion
manifest, with unchanged limits, admissible initial snapshots and actual native
identities. Appended replay accounting is retained but cannot mutate the
original producer provenance. All complete source/model/revision/context and
binding checks are inherited unchanged. Analysis v4 changes only the exact
collector identity; original statistics, all 2,000 draws and reader selection
are unchanged. The existing selected-reader contract remains binding.

The constructed native fixture exercises refusal before model load, a real
monitor-thread request after the first sealed eight-word block, preservation of
the interrupted evidence, and a clearly labelled same-process numerical-copy
continuation with actual tiny CPU scoring and fresh forwards. This copy control
does not claim to qualify native runtime migration; the separately counted
runtime and idempotent pause/resume proofs remain required dependencies.

It then exercises the entire existing ten-reader/360-row constructed bank proof
with the guarded successor and the unguarded v5 kernel. Identical inputs must
produce identical numerical bytes. Complete collection and the original
2,000-draw AT2 handler must agree, including selected-manifest binding. Changed
guard pins, unknown wrappers and changed limits must refuse, in addition to
all original precision/context/revision/binding/incomplete-bank refusals.
Synthetic resource snapshots appear only inside this fixture; they never
establish production memory availability. Outer fresh-process replay is
mandatory. Every gate has the same behavior under either scientific direction.

**The smaller route.** A bounded constructed fixture precedes any human-model
admission. Insufficient memory preserves a resource yield; measured costs feed
the unchanged whole-writer sample and family-continuation rules. No reader or
source chunk is dropped to obtain a passing cache check or a cheaper bank.
All original failures, diagnostics, paused work and their costs remain charged.

Method continuity: LESSONS sections 3–5 and original AT numerical, native guard,
idempotent completion and complete collection designs. The proposed counted
fixture envelope is 600 CPU seconds, 900 wall seconds, 3 GiB and two numerical
threads. This is a proposed cap, not a measured cost or K-ready claim.
