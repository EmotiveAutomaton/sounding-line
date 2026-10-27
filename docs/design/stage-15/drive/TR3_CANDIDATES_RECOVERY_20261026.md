# TR3 candidate schema recovery

The first full candidate run failed before a complete session: the wrapper
expected string alternatives while the canonical source stores objects with
index, original text and trimmed display text. Its string fixture missed the
producer boundary. Preserve that run, native fixture, sources and CPU cost.

DESIGN CHECK: LESSONS 2-5 reread. Under NULL and ALTERNATIVE, use the same
discovery writers, displayed text, tokenizer and count definition. Validate
actual records with the source's canonical `suggestions` parser, then project
the `trimmed` display text. Reopened menus must agree in the complete original
record, including index and original text, before this projection. Empty menus
remain empty; malformed records fail. Exhaustive states are validated counts
or explicit refusal, with no scientific result in either case.

This is the first ordinary engineering healing pass. It changes the input
adapter only. Counts on equivalent displayed strings must be exactly equal
to the original instrument, and its immutable source remains. The canonical
producer constructs the fixture. Tests mutate every required field, repeated
indices, metadata on a reopen and serialized output; independent native replay
must complete before the full-source recovery. Test-writer payloads remain
absent from the fixture and unread by the corpus counter. No corpus session,
candidate, parameter, comparator or seed is dropped or changed.

The failed attempt charged 5.734375 CPU seconds. Retain the original TR3
7,200-second ceiling and prior cumulative charge/reserve 1,416.984375. The
existing construction/test reserve covers this adapter; native validation is
capped at 60 CPU seconds and full recovery/replay at 600. No additional paid,
GPU, holdout or scientific study authority is used.
