# D37: three-entry preparation before fitting

Question: does combining page, person and process information forecast a writer's
next handling decision better than the best individual entry? Authority is the
October 17 D37 card and Week 3 section 6. D17 pause shares and V5 headroom are
dropped by the ratified errata. This preparation does not fit or score a reader.

## DESIGN CHECK

LESSONS sections 2–5, CONTROLS sections 1–7, the original D37 card, P4 chronology,
and the triple-inference section 1 and correction history were read for this build.
Under null and alternative, every original prepared row has the same disposition.
Features must remain unchanged if its own or future handling/hover/edit outcomes
change. Missing timing is explicit, not row exclusion. A changed source, duplicate
key, invalid ordinal/time, or incomplete join refuses before fitting. Known UTF-16
deletions, Unicode insertions, request ambiguity and future-event poisoning must
be tested. The bands here are complete preparation, unsupported field, or invalid
source; none is a scientific null or positive.

## Entry boundaries and chronology

P4's full augmented predictor mixes page content with timing and handling history.
Reuse its frozen content representations, not that mixed predictor as a page-only
entry. Retain the three menu surface terms (count, mean length, lexical overlap),
the first 50 content-only scalar terms and context/mean-option embedding vectors.
Exclude elapsed time, previous handling, recent accepts, decision count, and time
remaining from the page entry. Any PCA and standardization fit on training only.

Process features are measured immediately before menu opening. Request latency
uses the single suggestion-get since the preceding suggestion-open; zero or
multiple requests give an explicit missing value. Hovers count only earlier raw
events since the preceding menu opening, never this menu's subsequent interactions.
Recent editing counts user insertion codepoints, deleted UTF-16 units and user
delta events in the preceding 60 seconds, strictly earlier in event order. These
are logged event measures, not physical keypresses. No outcome-resolution latency
or D15's through-resolution typed count is used as a predecision feature.

Retain the original 1,399-session, 61-writer, 16,855-decision prepared census;
require exact raw-menu ordinals and content joins. Source rows retain canonical
handling, recorded resolution time, writer/session/prompt and chronology metadata.
These are targets and history provenance, not inputs to the page/process features.
The full corpus is not a new blind holdout. Chronological 60/20/20 partitions and
recipient-specific cutoffs are inherited unchanged from P4_CHRONOLOGY.md; original
unsupported recipients and overlaps remain in the source receipt.

The person reader will use only previously resolved history and a training-only
version of V3's reliability estimator. Published full-corpus V3 estimates cannot
be used as predictive priors because they include future outcomes. The model,
stack-weight fit, known-answer worlds and whole-study forecast will be frozen in
a separate implementation before any fit. This preparation grants none of those
admissions. The primary remains equal-session test half-Brier of the calibration-
selected best single entry minus the calibration-weighted stack. D37's extension
remains weights versus prior record count; no empathy or values ground truth.

## Execution and accounting

Authenticate original P4 completion, plan and source hashes, plus the foundation
plan's raw roster. Read original logs without changing old extractors, labels or
artifacts. Reconstruct every prepared process row in a fresh native process and
compare numeric arrays and all keyed records exactly. Keep text and identifiers
private; public receipts carry aggregate counts and hashes only.

The one-hour Week 3 no-projection probe includes a 120 CPU-second build reserve,
native validation, complete input preparation and subsequent model timing. Source
preparation has at most 600 CPU seconds and the same wall guard, with all charges
retained toward that hour. Full D37 execution needs its complete measured forecast
and separate admission. CPU only; no GPU, paid call, new agent or holdout access.
