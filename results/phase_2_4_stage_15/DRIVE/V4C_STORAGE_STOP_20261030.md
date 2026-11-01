# V4C STORAGE STOP 20261030

**Hypothesis.** Did the interrupted reference computation fail scientifically or exceed its storage allocation?

**METHOD.** Inspect the terminal error, supervisor traceback, complete output sizes, native parent and child identities, sealed checkpoint counts and contained-job charges. Forecast the complete retained output from actual reference bytes; request reference-boundary yields from the three confirmed live siblings and verify their exit.

**Found.** One shard reached its storage cap and three siblings paused safely; all original checkpoints and charges remain retained, with no scientific verdict.

The eight-GiB guard fired as specified. Complete uncompressed shard storage would exceed that guard even though the host still has free disk space. This repeats the earlier retained-byte forecasting lesson; runtime cost admission alone was insufficient. No cap was increased and no failed fit was treated as a null.

The table lists operational dispositions, retained sealed-reference counts, and charged CPU seconds. Counts describe checkpoint coverage, not scientific scores.

| Shard | Disposition | Sealed references | CPU seconds |
|---|---|---:|---:|
| 0 | PAUSED | 2003 | 26974.03125 |
| 1 | PAUSED | 2043 | 28699.390625 |
| 2 | FAILED | 2074 | 28569.96875 |
| 3 | PAUSED | 2056 | 28731.28125 |

All four original parents and workers exited. The three subsequent monitor-disappearance alarms are false classifications: each pause receipt predates the alarm, but the custom storage-projection reason is outside the watcher's allowed checkpoint-pause reasons. Both the alarms and pause receipts remain intact; no disappeared work is inferred from those alarms. Immediate terminal delivery still functions. Future automatic resource/drain/CPU pauses retain the recognized runtime schema; the custom manual pause needs explicit reconciliation.

**Means.** Authenticate checkpoints into separate lossless-storage attempts only after validation and measured size admission. All original numerical code, seeds, matrix, fresh full replay, resource ceilings and parked GPU/paid holds persist. No tests were harvested from the wake.
