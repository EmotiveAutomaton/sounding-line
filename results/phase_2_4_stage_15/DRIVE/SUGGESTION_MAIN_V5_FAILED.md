# Full suggestion pass: retry ended at the memory guard

**Hypothesis.** The full suggestion pass can finish from authenticated checkpoints under the unchanged memory limits.
**METHOD.** Inspect the exact safety sample, native exit and lease release, then validate every retained checkpoint, its input binding and reductions against the frozen plans.
**Found.** Free GPU memory fell below the fixed safety floor during the permitted retry; all 4,453 saved checkpoints validate. **Means.** The unfinished pass is invalid under the packet's second-failure rule. This is an apparatus failure, not a negative scientific result; dependent comparisons remain blocked.

The table records operational measurements and their unchanged limits, not unfinished scientific scores.

| Check | Observed | Limit or disposition |
|---|---|---|
| Free GPU memory at stop | 912 MiB | At least 1,024 MiB required |
| GPU temperature at stop | 69 C | At most 78 C |
| Retained checkpoints | 4,453 validated; 2,608 reused bytes unchanged | Exact consecutive prefix; full roster incomplete |
| Source bindings | All 102 match | No frozen source changed |
| Charged wall time | 23,231 seconds earlier, 9,906 this attempt | 122,643 seconds remain in the original computation allowance; retry count still forbids restart |
| Native worker and lease | Exact worker exited; GPU lease released | No cleanup or worker kill required |

The original v4 stop and this v5 retry are the two attempts of the admitted full
pass. Section 2, row 9 of the [active packet](../../../docs/design/stage-15/drive/BATCH_PLAN_20261017_W1_PUBLIC.md)
says: “A second failure records the card as invalid, with its reason.” No new
version or changed memory floor is used to evade that stop. The 178,026,397 bytes
of saved checkpoint evidence remain private and intact; no unfinished scores
are released or admitted downstream. Family null counters do not change.

At the 17:52 PDT inspection, V4 and D32 were alive with fresh output, unchanged
source pins and valid counted leases. The shared ToMpathy lease remained valid
and untouched. Available RAM, commit and disk cleared the running floors. GPU
free memory after worker exit was 2,482 MiB, below the 7,424 MiB cold-start floor;
other applications remained present. Per-process GPU memory was unavailable,
so this inspection does not attribute the memory change to any single app.

No already-reviewed unstarted card was runnable. D17 remains the next available
ranked draft for owner validation. V4 and D32 continue; P1-dependent comparisons
await complete valid reader output. The actual failure delivery is verified,
the planned check remains 18:07 PDT and independent six-hour health remains
21:09 PDT. The 20:00 digest will integrate TODO/STATE/operations under the active
reporting policy. No tests were harvested and no paid calls were made.

[Aggregate inspection and integrity receipt](SUGGESTION_MAIN_V5_FAILED.json).
