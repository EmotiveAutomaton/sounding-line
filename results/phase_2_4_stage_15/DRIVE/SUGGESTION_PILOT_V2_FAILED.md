# Suggestion timing pilot: storage failure and separate recovery

**Hypothesis.** Did the checkpoint fail because scores were lost or because
Python and JSON represent the same offsets differently?
**METHOD.** Replay the actual retained checkpoint through both handlers, compare
compressed bytes and canonical values, and independently validate the full score
schema, source bindings and native closure.

**Found.** The old Python-container equality rejects tuple offsets after JSON
turns them into lists. The same compressed bytes pass the new handler's canonical
JSON comparison and full schema replay. Eight targeted recovery controls pass,
including changed-value, input-binding, corruption and live-predecessor refusal.
**Means.** This is a repaired serialization check, not a scientific result or
whole-pilot completion. Original source, failure and unregistered partial chunk
remain unchanged. No partial scores or timings are used to admit a main run.

[Failure verification](SUGGESTION_PILOT_V2_FAILED.json) records all 74 verified
source pins, the retained-byte binding, native exit and released lease.
[Separate v3 launch](SUGGESTION_V3_LAUNCH.json) records the monitored successor.
[Contract](../../../docs/design/stage-15/drive/SUGGESTION_CORPUS_V3.md) retains
the original aggregate time, memory, accuracy and measured main admission caps.
The [paired precision diagnostic](SMOL_PRECISION_V1.md) separately supports the
float32 setting; this storage correction does not change numerical scoring.
