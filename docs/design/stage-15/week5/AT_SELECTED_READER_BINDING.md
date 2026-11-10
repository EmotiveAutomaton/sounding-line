# Carry selected-reader provenance into later cards

The numerical correction must follow the selected model into its consumers.
This adds no selected reader and grants no new inference. AT2 selection still
requires the complete ten-model primary bank, the original final context and
1,024-token cap, all 2,000 draws and the existing selection-admissibility rule.

`week5_at_analysis_v2` leaves the frozen statistical implementation unchanged.
It takes an authenticated collector-v3 root, rechecks every score/source/context
binding, and requires exactly one manifest digest for every model throughout
the bank. It writes `READER_BINDING.json` beside the original result: selected
model, pinned revision, exact manifest digest, numerical specification, context
and complete-collection receipt hash. Unsupported or screening-only output
cannot become a selected reader by possessing this sidecar.

`week5_at_selection.selected_reader` authenticates the selection and requires
that sidecar to match the prospective consumer's manifest exactly. Missing
precision, a different revision, a different tokenizer/files manifest or a
legacy float32 numerical specification refuses. GO1 and LA1 must use this
shared check and the scoring-v4 causal loader before any selected-reader work.

LA pipeline-v3 changes only its causal reader to the inherited AT float64
computation; the separate masked resolution reader retains its original
float32 definition. Both manifests and revisions, selected-reader binding and
numerical spec enter every paired-act binding and summary. Complete collection
checks the precise source chunk, handler and per-act binding and refuses mixed
causal/masked manifests or numerical versions. Resource yields remain at each
sealed paired act. The combined readers need their own measured memory and CPU
pilot; the causal reader's standalone peak is not the paired-reader peak.

## DESIGN CHECK

A native constructed fixture executes all ten-model AT2 statistics at 2,000
draws through the new provenance handler and actual collection-binding gates.
It refuses wrong revision and legacy precision. Actual tiny causal-float64 and
masked-float32 models execute the paired LA handler, yield/resume and complete
collection; a mixed-precision summary refuses. A fresh process repeats the
entire selection, paired scoring and collection. Human model selection remains
uncomputed until the reviewed complete bank and its cost admission finish.
