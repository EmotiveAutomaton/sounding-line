# Authenticated AT3 and AT4 reader consumers

Status: prepared, unexecuted, and not admitted. This is an implementation
binding for the existing AT design and grid, with no new scientific analysis.
The original statistical kernels and their known-answer evidence stay intact.

## DESIGN CHECK

Reviewed method lessons 3--5 on 2026-11-07. The case is an AT3 or AT4 primary
that claims to use the reader selected by the completed primary AT2 analysis.
Its check is exact authentication of the collection, selected model manifest,
revision, numerical specification, context and collection receipt. A different
reader, collection, screening selection or context must refuse before fitting.

The smaller route remains the original card's whole-writer sample and family
continuation. This wrapper does not choose a new sample, drop models, change a
numerical gate, spend a holdout, or infer that a human reader has been selected.
No corrected complete human ten-reader bank is currently available.

## Frozen dependency roles

`week5_at_selected_analysis` accepts the exact reviewed v4 collector and its
unchanged AT-FP64-1 scores. All underlying score producers retain their existing
pin, revision, row, batch and context checks. The primary final-context window
is 1,024 tokens. The consumer has three explicit roles:

| Role | Required completed dependency | Permitted use |
|---|---|---|
| selected | Exact AT2 analysis-v3 selection and the same collection receipt | AT3/AT4 primary and their declared selected-reader textures |
| completed_model | Complete score collection for the named model | AT3 per-model descriptive texture; no selection dependency |
| engine_texture | Complete score collection for one of the two original engine model names | AT4 engine-reader descriptive texture; no selection dependency |

Selected-reader calls cannot substitute a collection from another cohort or
context. Independent roles cannot masquerade as primaries. A texture normally
uses 200 writer resamples; an explicitly identified precision follow-up uses
2,000. Primaries use 2,000. The wrapper enforces the existing position,
residualized-entropy and fluency-threshold grid and records the role in a
separate `READER_PROVENANCE.json`. It calls the original analysis with that
metadata removed, so `RESULT.json` and the original numerical binding remain
exactly the original consumer's output.

## Proposed constructed native proof

`week5_at_selected_analysis_fixture` takes only the completed constructed
AT-collection-v4-native fixture, authenticates its outer receipt and explicit
constructed-only declaration, and loads no pretrained model or human input.
It runs both complete 2,000-draw primaries, the original AT3 surprisal companion,
all ten independent AT3 reader textures, both independent AT4 engine-reader
textures, and selected-reader position, residualized-entropy and threshold
variants. Every output is compared with the unchanged original handler; a
separate native verifier repeats the complete calculations.

Wrong reader, wrong collection receipt, screening-only selection, changed
context, a primary claiming an independent-reader role and an unmarked
2,000-draw texture must refuse. Mutated selection receipts are made only in
explicit constructed copies. The completed input fixture is never edited.
Genre filtering retains the original kernel and existing full-family fixtures;
the reused source fixture has no genre field, so this dependency fixture does
not claim new genre-source validation.

Proposed counted fixture envelope: AT family, 600 CPU seconds, 900 wall seconds,
3 GiB projected peak, two numerical threads, CPU only. Owner review, committed
design and a pinned validation receipt precede any start. No native execution
has occurred for this successor at preparation time.

The complete original statistical call is still one bounded unit. A human
cost/pilot must demonstrate that it fits its operating quantum and resource
grace; otherwise an immutable exact checkpoint successor is required before
that larger admission. This narrow dependency adapter does not by itself
qualify an arbitrarily large statistical run.
