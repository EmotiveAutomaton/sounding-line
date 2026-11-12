# GO1 real encoder qualification

**DESIGN CHECK.** LESSONS §§3–5 were reread for this implementation. This is
the outstanding real-encoder admission check in the committed R4 design, using
constructed strings only. Under either scientific null or alternative, repeated
inputs and an independent full-token reference must agree. Wrong shape, dtype,
nonfinite or unnormalized output, constant vectors, changed sealed bytes,
changed checkpoint binding, and a different model revision must refuse. A
first-chunk-only reference must disagree for the multi-chunk constructed input.
The gates concern implementation integrity, not a scientific effect.

Use the unchanged `week5_go_readers.embeddings` and
`week5_go1_pipeline_v2.vector_bank`, with the already pinned local CA1 encoder.
Exercise empty input, a short sentence, an exact duplicate, multilingual text,
and a long constructed text spanning at least three token chunks. Pause after
two unique vectors, authenticate the retained cache and finish. Fully cached
reentry must make no model call. An independent implementation reconstructs
the original 126-content-token partition, two boundary tokens, within-chunk
mean, equal chunk mean and final normalization. The numerical comparison uses
absolute tolerance 1e-6 with zero relative tolerance; fresh native replay must
also reproduce every stored vector exactly. There is no truncation, altered
pooling, corpus reading, retraining or model selection.

Mutated cache bytes with the original seal, mutated bindings with a valid seal,
and a changed model revision are separately rejected. Preserve these constructed
refusal cases. Record package versions and exact manifest, reader and pipeline
hashes. Both execution and fresh verification run inside one counted CPU-only
Gear 2 slot, with two numerical threads, 3 GiB projected memory, 600 CPU-seconds,
1,800 wall-seconds and 100 MiB output. All work is charged to GO1 and the GO
family. No GPU, network model retrieval, provider or paid call is permitted.

**Case and check:** the original encoder can reconstruct a complete normalized
document vector while preserving duplicate identity and its cache contract;
the full actual-model path and a separate native replay check that claim.
**Smaller route:** none for this admission gate. A failure blocks corpus
encoding and is retained for diagnosis under the existing healing policy.

Passing admits only the existing 143-text first-five-percent prefix, subject
to current source, budget, resource and native-plan checks. It supplies no goal
accuracy, scientific result or full-run cost forecast. The original R4 design,
roster, 150,000 CPU-second card ceiling and 600,000 family ceiling remain fixed.

## Version 2 compatibility repair

The first native attempt failed in the independent reference because the installed
`TokenizersBackend` does not provide `build_inputs_with_special_tokens`. The
production reader and cache had executed; no qualification was granted. Preserve
that original source, failed attempt and 35.9375 CPU-seconds plus its supervisor
allowance. This is engineering repair one, with the same manifest, constructed
strings, numeric tolerances, pooling and gates. The separate version-2 reference
uses the installed tokenizer call's explicit special-token mask and full input
IDs; it requires exactly one boundary token at each end and no internal special
tokens. It reconstructs all content chunks without any retired helper. A focused
backend-interface regression and a malformed-template refusal supplement the
original checks. Complete real-model native execution and fresh replay are still
required before corpus admission. Original production source bytes are unchanged.
