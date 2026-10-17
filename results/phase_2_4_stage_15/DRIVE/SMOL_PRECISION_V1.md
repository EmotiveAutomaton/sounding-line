# Complete paired precision diagnostic

**Hypothesis.** Does higher numerical precision repair the reader's cached/direct
disagreement on the same selected inputs?
**METHOD.** Run all five previously selected Smol360 menus in four unchanged
contexts, under both float16 and float32, comparing every eligible native-token
loss from cached scoring with ordinary direct teacher forcing. Independently
rebuild tokenization, offsets, finite reductions, comparisons, source/output
bindings, resource limits and native closure from the complete retained record.

The table reports whole diagnostic results. Error is the largest absolute
difference in native-token negative log likelihood, with a fixed tolerance of 0.02.

| Precision | Complete comparisons | Maximum error | Admission |
|---|---:|---:|---|
| Float16 | 80 targets across 20 menu/context pairs | 0.032565 | Fails |
| Float32 | Same 80 targets and 20 pairs | 0.00006390 | Passes |

**Found.** Higher precision passes every numerical comparison, while the original
lower precision fails. **Means.** The paired evidence supports a separately frozen
float32 Smol recovery without changing inputs or tolerance. It does not complete
the five-reader timing pilot, admit the full corpus, or establish a scientific result.

All ten output bindings and 72 source pins verify. The exact native worker exited
and released its GPU lease. The full float32 model remained on the GPU, reserved
at most 2874 MiB under the 5888 MiB cap, and left at least 4603 MiB sampled free.
Three targeted paired-comparison controls pass. Original failure and lower-precision
arrays remain unchanged. No new research test was harvested; this is authorized
instrument recovery. The diagnostic's selected support does not establish accuracy
outside that support; the broader pilot and main retain their own checks.

[Aggregate verification](SMOL_PRECISION_V1.json) · [Fixed contract](../../../docs/design/stage-15/drive/SMOL_PRECISION_V1.md).
