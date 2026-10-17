# Shared content features before predictive fitting

DESIGN CHECK: LESSONS 3–5. Future actions and target labels cannot change a
feature; reordered menus must reorder their features identically. Duplicated
text has identical vectors. Altered sources, missing coverage or nonfinite
representations refuse completion. These are extraction controls, not evidence
that content predicts behavior.

Encode every Phase 0 decision's preceding document and every offered suggestion
with the locally cached, hash-pinned MiniLM-L6-v2 encoder. Preserve the full
384-dimensional unit-normalized masked-mean representation in private arrays.
The earlier candidate feature files contain centered projections for a smaller
roster; those are not substituted for full context/suggestion representations.

MiniLM's declared 256-token view is explicit: retain the last 254 content tokens
of the preceding document and the first 254 of each suggestion, then add the
two special tokens. Store full/used token counts and offsets into the original
text for every unique representation. Never describe these bounded embeddings
as whole-document representations. No learned projection, labels, fit or
hyperparameter search enters this pass. Complete text remains in the source.

Also retain candidate codepoint length, whitespace-word count, novel-word
fraction against the preceding document, and zero-based menu position, plus
embedding cosine against that context. Every candidate is represented; a later
handling model must use predecision menu aggregates, never the selected answer.

CPU only, one numerical thread, float32, no remote code or model download.
Four-hour wall ceiling, 150,000 unique representations and 2 GiB output ceiling.
Check available RAM, system commit and disk throughout. One immutable attempt,
complete coverage and exact model/source identities before completion. Full
P4/D1 fitting still requires a frozen chronological fitting/calibration plan;
model-preference features separately depend on P1. Extraction is not a baseline.
