# EX4: KLiCKe final essays and supported stop labels

Prospective static candidate for packet EX4/T/Q, November 11. The latest packet's
no-writer-ID rule controls this export, regardless of older S4.k interpretations.
No corpus replay, export or copy has run in this build.

DESIGN CHECK: LESSONS §2, §§3–5 and the pinned KLiCKe intake/S4.k reconstruction.
UTF-16 edits and Unicode code-point output offsets are different units. A source
text match alone does not verify word origins. Moves must preserve provenance;
deleted starts, merged words and bulk edits must not manufacture first-keystroke
pauses. Known-answer edit sequences cover these cases, non-BMP text, exact stop
boundaries, ties, source integrity refusal and full independent replay. Collection
exclusions retain the whole input denominator. No model or inference is run.

## Source and text contract

Require the exact complete, independently verified `BK-S4.k-intake-full`, from
the original `week5_bk_klicke_intake_v2` producer, original 4,992-session roster,
original archive SHA and passing source collection gate. Each neutral session
projection and its salted key must match the sealed index before reading it.
Source-integrity errors fail closed outside the ordinary parse-failure handler.
No raw archive filename, identity column, demographics, essay score or writer
link is loaded or exported.

The existing `week5_bk_s4k_navigation.operation` and `canonical_final` define text
operations and the independent final-document check. Preserve UTF-16 cursor
positions, exact removed text, supported escape decoding, moves and the source's
single export-record newline. Export the resulting final essay without NFC,
fuzzy alignment or additional whitespace trimming. Offsets refer to Unicode code
points in exactly that text; its UTF-8 SHA-256 accompanies the session.

Carry an origin through each UTF-16 unit. A non-BMP code point requires consistent
ownership across both units. Exact moves relocate the original origins instead
of pretending that moved text was typed again. Use the established P6 TOKEN/WORD
rule on the final text. The export contains final surviving words with any typed
`Input` material, ordered by earliest surviving typing event, then final offset.
It is not a record of deleted words. Words with no typed material remain in the
essay and are counted as omitted from the typed-word list. Shared-event ties
never imply an invented intra-event keystroke order.

## Timing and quality fields

Supported timing requires every constituent to originate in a single-code-point
`Input`, the first surviving character to retain its original word-start event,
that event to be the earliest constituent event, and no merged original word
start inside the final word. Its pause is key-down minus the preceding logged
event's key-up, agreeing with recorded `PauseTime` within one millisecond. All
times convert the existing source milliseconds to seconds. A missing preceding
event, negative overlap or inconsistent clock leaves timing unsupported.

Mixed paste/replacement provenance, bulk insertions, a deleted word start, a
later replacement before older word material, and merged original word starts
retain explicit `timing_status`, null pause and null stop labels. Unsupported
does not mean fluent. These are conservative engineering support fields, not
new scientific source classes. The complete counts show their cost to coverage.

Stop labels are `pause >= 2 seconds` and `pause >= percentile80`. The latter uses
linear quantile interpolation over **supported surviving typed-word pauses in
that essay**, with ties retained. No supported pause means a null threshold.
`inserted_later` means some surviving typed constituent was inserted before the
then-current document end. A separate move flag reports later relocation while
preserving original typing time. These definitions are frozen before any real
export inspection; they are not adapted to obtain a desired coverage or label
balance.

## Local bundle and attribution

Session JSON contains final text, code-point spans, typing order, supported
pauses, the two stop labels and quality flags. Index/summary retain all input
sessions, successful sessions, parse exclusions and word support counts. No
writer ID is emitted or inferred. Parse failures are excluded and counted as
the packet requires; an integrity mismatch is never downgraded to a parse error.

The README acknowledges Tian, Crossley and Van Waes, *The KLiCKe Corpus:
Keystroke Logging in Compositions for Knowledge Evaluation* (2025), DOI
10.17239/jowr-2025.17.01.02, and The Learning Agency. It states CC BY 4.0 and labels
the reconstruction as our derivative. The archive's dataset licence is used,
not the source repository's separate software licence.

Only a complete independently replayed bundle can be materialized to the new
ignored `corpora/store/exports/engine_bench_20261111/EX4` directory. The code
refuses arbitrary destinations and verifies every copied member. It contains no
network or cross-repository copy; the owner separately controls the specifically
authorized ToMpathy handoff under amendment T. Nothing is committed or sent to a
provider by the handler.

## Resource and qualification gates

Isolated `week5_ex4_words`, `week5_ex4` and constructed fixture; all old sources
remain unchanged. UUID JSON publication and sealed checkpoint state use existing
qualified primitives. Complete sessions are checkpoint units. The first five
percent deliberately yields for the in-run source cost probe; continuation
requires measured forecast for all sessions plus full independent replay under
the 60,000 CPU-second EX4 ceiling and EX's remaining 100,000 family allowance.
Proposed memory forecast is 2 GiB to validate, ≤2 numerical threads, unchanged
resource floors and campaign cutoff. Standard wall/draw quantum and yield request
are honored at session boundaries. Partial execution/verification returns
`status=yielded, verified=false`.

Verification independently reconstructs each original session into a separate
subtree and compares every bundle byte, all exclusions, counts, thresholds and
labels. The constructed fixture substitutes only the original complete-source
authentication with constructed records; the actual replay, exporter, bounded
state machine and full verification execute. It is not a real source or native
runtime qualification. Under Q, owner review and committed design plus passing
constructed checks precede the counted run; no additional numerical campaign
is proposed.

Current status: static build, tests unrun, source not scanned. Owner review must
confirm the surviving-word scope, nullable-timing conventions, source and output
schema, passing tests and actual cost/resource admission before export. Records
are `run`, theory tags empty, by-construction false for the real-source export;
no scientific claim follows from labels being produced.
