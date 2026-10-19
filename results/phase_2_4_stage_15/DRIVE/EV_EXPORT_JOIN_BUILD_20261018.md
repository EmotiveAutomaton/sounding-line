# Exact exporter matching and typed fragments: component validation

**Hypothesis.** Original word occurrences can join engine lexical spans without substitute matches, and surviving typed text can retain its boundaries.
**METHOD.** Generate constructed records through the actual pinned exporter with deterministic constructed losses. Test codepoint/UTF-8/UTF-16 agreement, source identity, retained covariates, excluded words, corruption refusal and fresh-process reconstruction. Preserve every surviving typed run, inserting an explicit two-newline boundary only across removed non-typed text. Independently reproduce the fixtures and fragment exports from the frozen engine.
**Found.** All 23 new checks and 14 existing original-word join checks pass. The actual exporter independently reproduces all four retained constructed fixtures and accepts their fragment inputs and outputs. **Means.** The component is validated on constructed inputs; counted full-handler validation, measured real-reader execution, corpus support and scientific admission remain unfinished.

The table names each constructed defect and required behavior. These are software validation cases, not scientific comparisons.

| Constructed case | Required behavior |
|---|---|
| Deleted word replaced by identical spelling | Deleted occurrence remains unsupported; later spelling cannot supply its score |
| Emoji, accents, combining mark, apostrophe and underscore | Three coordinate systems agree; different original/engine word boundaries remain unmatched |
| Names/numbers, function words and no content | No fabricated zero departure; unsupported dispositions stay distinct |
| Typed runs separated by non-typed text | Typed bytes and source mappings survive; removed gaps never concatenate words |
| Changed identity, offsets, provenance, loss or normalization | Refusal rather than repair or silent row dropping |

The first fixture-generation command passed literal Unicode through a lossy Windows shell pipeline. A prefix check failed; its fixture and receipt are retained. Regeneration with explicit Unicode escapes restored the intended characters. One assertion still counted a word from the corrupted fixture; that second failure is retained, and the assertion now enumerates the six known scored words explicitly. The production join was not changed to accept corruption. A separate status clarification distinguishes consuming an unsupported export from obtaining a scored word. Final tests and actual-exporter replay pass.

Exporter SHA256: `a5dd4bc6447524968e75d1d4ae5f7d6c058529b41bbf2143ed44d4b7261273aa`.
Engine commit: `5f3ad0a304727fff5e1a6beca592e786ee71b181`.
The real reader weights were not invoked. Constructed byte-allocated losses validate the interface, not reader correctness or normalized whole-word probability. Typed fragments are explicitly not original prose; partial surviving runs retain that limitation. No corpus, badge, scientific probability, gear change or paid call follows.

Next: counted authenticated exporter handler and measured reader pilot. [Validation receipt](EV_EXPORT_JOIN_BUILD_20261018.json).
