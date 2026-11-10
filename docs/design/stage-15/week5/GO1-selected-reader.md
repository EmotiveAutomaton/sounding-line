# GO1 selected-reader numerical inheritance

The complete AT2 primary now selects a reader from one common numerical bank:
`AT-FP64-1`. Its pinned original float32 model tensors are converted exactly to
float64 for inference, with float32 log-softmax and entropy reductions. GO1
must inherit that reader's model, revision, manifest and numerical protocol.
The older GO1 pipeline remains preserved and is not admitted for this bank.

`week5_go1_pipeline_v2` uses the frozen `week5_at_selection.selected_reader`
helper and `week5_at_scoring_v4.load_model`. It requires the completed AT2
primary's admissible selection, full authenticated output hashes and exact
selected-model manifest/revision. Both RESULT and READER_BINDING must appear
in the completion manifest. A screening selection, missing binding, altered
revision, mixed numerical protocol or unsealed dependency refuses.

Every language-model row checkpoint binds that selection receipt, numerical
binding and scoring implementation. The score receipt and collected result
carry the same binding. Collection rejects an old float32 bank or a different
selected reader, even if the old score-array hashes are internally valid.
No old row checkpoint is silently reused under the new arithmetic.

All scientific definitions remain unchanged: the fixed candidate roster,
complete-document context support shared by all three readers, summed
conditional log-likelihood gain, fresh cache for each candidate likelihood,
author-cluster uncertainty, support floor and all declared grid cells. The
primary still compares language-model retrieval with TF-IDF; the encoder
remains its separately pinned reader. This change creates no AT2 selection.
GO1 stays dependency-waiting until the full admissible selection exists.

## DESIGN CHECK

- **Case and check:** the selected AT2 reader has one exact numerical identity.
  The native fixture uses a tiny actual causal transformer with float64
  parameters, constructed sealed selection receipts and the real dependency
  authenticator. It checks summed token losses, bounded row pause/resume,
  independent complete score replay, complete 2,000-draw collection and
  rejection of altered selection, old numerical banks and changed checkpoints.
  Encoder fixture vectors are constructed here; the unchanged actual encoder
  primitive retains its earlier native qualification.
- **Smaller route:** keep the original counted 5% pilot, whole-author sample
  rule, 150,000 CPU-second card and 600,000 family ceilings. Unsupported full
  contexts remain explicit exclusions. A missing or invalid selected-reader
  receipt is a dependency wait, never a license to choose another model.

The tiny-transformer fixture qualifies the propagation and complete handler
contract. It is not a human scientific result, a model-selection result or a
benchmark of the eventual selected model. That model's actual cost remains
subject to the unchanged in-slot pilot and resource admission.
