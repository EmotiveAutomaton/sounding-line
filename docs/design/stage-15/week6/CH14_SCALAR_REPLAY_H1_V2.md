# CH14.h1 first transport repair: literal yielded verification receipt

The original CH14.h1 design and all scientific and resource boundaries remain.
Its first production attempt failed before execution copying because this runtime
writes its unfinished verification return to `VERIFIED.json` before writing
`PAUSED.json`. The first adapter treated that filename alone as an ambiguous
terminal. Preserve that failure, source, fixture and measured charge.

DESIGN CHECK: LESSONS section 5, actual terminal schemas. This isolated first
engineering repair authenticates that additional receipt by hash and accepts
only its exact yielded status, phase, false verification-credit flag and an
integer draw count matching the preserved partial replay bank. Complete, empty,
extra-field, credited, boolean-count and inconsistent-count cases must refuse.
The original adapter's refusal of the actual yielded representation is reproduced.

No estimator, data, scalar kernel, Newton solver, draw count, threshold, source,
compiler setting, budget or runtime guard changes. The failed adapter remains
pinned and unchanged. Full fresh independent replay is still mandatory; its
predecessor's two draws confer no verification credit. This is the first bounded
runtime repair of the new implementation card, under its parent's remaining
allowance. Repeat the full 118-case qualification with the literal receipt and
eight additional schema cases: 126 fixed constructed checks, within 600 CPU
seconds and 1,200 wall seconds in one counted CPU-only slot. Committed design,
complete filing and ordinary admission still precede production.
