# P4 extension: writer offsets beyond content

**Hypothesis.** Stable differences between writers may improve forecasts beyond the shared content model.
**METHOD.** Apply the single frozen writer-offset extension to the same 3,623 held-out decisions from 41 writers, retaining the primary models and chronology. Compare half-Brier error with writer-cluster intervals and the matched within-session handling-shuffle control.
**Found.** The added error reduction is 0.00736, with a 95% interval of [0.00265, 0.01243]. The shuffled control improves by 0.00810 as well. **Means.** The extension is positive under its declared sign rule, but the control prevents a content-specific interpretation. Neither point estimate reaches the declared 0.01 useful margin; no further extension is authorized by this result.

The table compares the complete observed-data extension with its fixed shuffled control. Gain is content-model minus content-plus-writer half-Brier error. Positive values favor writer offsets; intervals resample writers while retaining fitted models.

| Comparison | Gain | 95% interval | Bootstrap standard error | Approximate two-sided Wald p |
|---|---:|---|---:|---:|
| Primary | 0.007363 | [0.002651, 0.012426] | 0.002536 | 0.003687 |
| Shuffled handling control | 0.008095 | [0.003029, 0.014107] | 0.002836 | 0.004309 |

Both use 286 sessions and 41 writers. Primary half-Brier error falls from 0.285911 to 0.278548. Within-session shuffling preserves session and writer class frequencies, so offset gains can survive without the relation between suggestion content and handling. These controls do not identify the source of writer differences or establish personal taste. No direct observed-minus-shuffled contrast was commissioned or tested here.

All 22 frozen bindings and 178 output hashes, native exit and fresh-process primary replay verify. The corrected interval validator leaves both states positive. Conditional uncertainty retains saved fitted models. Raw records and fitted models remain private. This shared-pass extension does not increment a Tier 1 family ladder; no engine admission follows. The 20:00 digest will integrate theory and TODO.

[Aggregate result and verification](P4-extension.json).
