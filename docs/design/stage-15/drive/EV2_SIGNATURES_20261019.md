# EV2: do page signatures recur in the writer's other work?

Authority: [October18 week packet](WEEK_PACKET_20261018.md), section4, EV2,
and its standing S1/S5 decisions. This is an instrument comparison, outside the
family null counters. The completed full reader is an input, not this result.

## Frozen implementation

Use all1399 authenticated final-document exports from `certified-fit-1`, with
the pinned Qwen2.5-0.5B CPU preview reader. Do not run the reader again. Validate
the complete parent, its source pins, output hashes and source-document bindings
before each execution and independent verification.

A signature is a distinct lowercase literal from the engine's first15 phrase
candidates with positive departure and occurrences in at least two sections or
paragraphs. Check the original occurrence spans in codepoints, UTF8 and UTF16;
check the exporter's support counts and its narrower section-based `recurring`
flag. The analysis uses the packet's section-or-paragraph definition. Duplicate
candidate strings within a source document count once. The completed first100
support pilot already passes the minimum floor without extrapolation.

**S5, matching.** Count lowercase exact substrings, including overlaps, following
the exporter's substring convention. Do not introduce a new lexical-boundary,
whitespace or punctuation filter. The packet specifies lowercase, so use lower
instead of the exporter's casefold when searching other documents. This is
literal recurrence, not semantic equivalence. Denominators are the exporter's
unquoted plus quoted word counts; both arms use the same pinned word ruler.

For each source document and signature, exclude its prompt entirely. Pool the
writer's remaining sessions within each other prompt and compare with all other
writers' sessions on that same prompt. Each prompt must have nonzero word
exposure on both sides. Pool the writer's counts and words across these prompts;
weight the other-writer prompt rates by that writer's word exposure. This keeps
the prompt mixture identical on the two sides. Multiply by10000. Average phrase
differences within source document, then documents within writer, then writers
equally. This is the primary own-minus-other contrast, positive direction.

**S5, control and resampling.** Generate200 session-ownership reassignments with
seed20261018, independently shuffling writer labels within each prompt. This
preserves every writer's session count and prompt composition. Text and source
phrases remain attached to their original sessions; no phrase selection is
rerun. All control means are grouped by the source sessions' **real writer**.
Use2000 real-writer bootstrap draws, seed20261019, for the primary interval and
the paired primary-minus-mean-fake interval. Target pools and the engine-selected
phrase roster are fixed; uncertainty is conditional on this corpus and those
choices. No independent-writer or new-corpus generalization follows.

**S1, common support.** Before computing recurrence counts or effects, intersect
the source-document support for the real assignment and all200 fixed fake
assignments. Keep every session in the target universe. Drop only source
document-signatures without matched support, and record every retained/dropped
session and aggregate counts. This avoids different comparison rows in real and
fake conditions. The original unmatched-population question stays open. Require
at least200 retained document-signatures and20 retained writers as well as the
original support floor; otherwise end `unsupported` without a primary score.

## Controls, states and limits

Construction checks precede production: planted writer-specific recurring
phrases; shared phrases; prompt-only phrases; exact scalar count/rate oracle;
missing/zero support; Unicode, punctuation and overlapping literal matches;
duplicate candidates; all200 prompt-roster invariants; changed source/output
refusal; fresh serialized replay and immutable reentry.

Under the null the contrast and fake reference are centered at zero. Under a
planted writer-specific alternative the real contrast is positive and the fake
reference remains centered. Report the fake mean, sample standard deviation,
2.5/97.5percentiles and one-sided descriptive permutation probability. Flag bias
when the absolute fake mean exceeds one quarter of its standard deviation;
exact zero mean/zero spread is quiet, nonzero mean/zero spread is biased.

Biased control means `invalid` for badge routing; retain the raw primary and
paired descriptive contrasts. Otherwise the registered percentile-interval
bands apply: interval above zero is positive; below zero is negative; crossing
zero with a positive point is marginal; otherwise null. Unsupported and failed
execution are separate. Only valid positive maps to “recurs in the writer's
other work”; valid null maps to “page-local”. Negative, marginal, invalid and
unsupported receive no badge. A page-local result is limited to this test's
literal matching and supported population.

Run through the existing week-window counted CPU runtime, below-normal priority,
one numerical thread, with one slot reserved for ToMpathy. Freeze sources and
inputs; register completion/failure/disappearance before the monitor handshake.
Bound combined analysis plus complete fresh source/statistic/control replay at
one wall-hour initially, at most the single two-hour S4 ceiling if separately
needed. No new reader, GPU, paid call or automated research expansion.

Land the complete instrument internally with its captioned report and index;
include controls, missing support and exact interpretation in the daily digest
and Tuesday engine-feature table. No unfinished per-artifact scores.
