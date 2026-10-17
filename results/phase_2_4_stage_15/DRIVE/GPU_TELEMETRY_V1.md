# Direct GPU safety telemetry validation

**Hypothesis.** Can direct GPU telemetry remove repeated process-launch
overhead while preserving the existing safety checks?
**METHOD.** Compare five live NVIDIA library readings, bracketing the existing
command, and exercise known-answer units, API errors, accounting and disagreement
refusals. Retain raw comparisons and pin the installed library and wrapper source.

The table describes the complete read-only telemetry check, not model inference.

| Check | Complete result |
|---|---|
| Live comparisons | Five agree within the declared temporal comparison margins |
| Median call time | Direct library 0.0104 ms; command invocation 46.65 ms |
| Refusal controls | Three tests pass; invalid accounting, API errors and mismatches refuse |
| Safety policy | Same check points and floors; no cached readings; free memory rounds down |

**Found.** Direct telemetry preserves the checked readings and removes most call
overhead. **Means.** It supports a separate timing recovery, not full-corpus
admission. The complete successor must still validate scores against the prior
pilot and meet the unchanged measured runtime ceiling.

The 16 MiB and 2 C cross-method margins cover sequential observations; they do
not relax working safety floors. Values retain Windows/driver accounting limits.
No driver settings, unrelated processes, model weights or scientific inputs change.

[Verification](GPU_TELEMETRY_V1.json). [Successor contract and primary API sources](../../../docs/design/stage-15/drive/SUGGESTION_CORPUS_V4.md).
