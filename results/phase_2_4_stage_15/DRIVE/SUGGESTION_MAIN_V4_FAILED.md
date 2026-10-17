# Full suggestion pass: safety stop with retained checkpoints

**Hypothesis.** Completed GPU checkpoints should remain reusable after the safety guard stops execution.
**METHOD.** Verify native exit, released GPU ownership, all frozen source hashes and every retained checkpoint hash after the guard failure.
**Found.** All 2,608 complete checkpoints remain intact. The guard's exact failing memory/temperature sample was not retained, so its cause cannot be narrowed further. **Means.** The full GPU pass remains unfinished. A separate checkpoint recovery must preserve every score, resource threshold and remaining aggregate budget; the incomplete session alone needs recomputation.

The original worker ended at 14:47 PDT and its GPU lease is absent. All 96 frozen source bindings verify. Retained checkpoints cover every session of the first reader and a consecutive prefix of the second; no unfinished scientific score is reported. The original guard tests both free GPU memory below 1,024 MiB and temperature above 78 C, but retained only the shared exception message. A later device snapshot cannot identify the triggering branch.

The later resource check showed 7,308 MiB free and 43 C, below the unchanged 7,424 MiB cold-start floor. No other application was stopped. A recovery must wait for its own exact limits, validate the entire reused prefix, retain the original failure, charge original elapsed time against the total allowance and record the precise safety sample on a recurrence. [Verification receipt](SUGGESTION_MAIN_V4_FAILED.json).
