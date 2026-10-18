# Causal batching with cross-group cache: complete fixed-input comparison

**Question.** Can equivalent causal computation reduce the CPU reader's cost?
**METHOD.** Reconstruct the original pilot's source prefixes and score every target with unchanged GPT-2 medium, CPU float32, context windows and tokenization. Compare every native loss to the frozen scalar pilot and independently verify all target identities plus six fresh direct forwards.
**Found.** Every comparison passes the fixed 0.0001-nat tolerance. **Means.** This scoring implementation is numerically validated on the complete pilot; full-corpus admission remains closed pending context/work-shape coverage and measured bounds.

The table gives each complete pilot domain, its target count, forward-call count,
native tokens actually processed, scoring elapsed seconds and maximum absolute
per-token loss difference from the original reference. It reports engineering
cost, not a scientific effect. Both domains have zero left-cropped targets.

| Domain | Targets | Forwards | Forward tokens | Seconds | Maximum error, nats |
|---|---:|---:|---:|---:|---:|
| typed | 306 | 22 | 502 | 9.479 | 6.77108765e-05 |
| jester | 306 | 8 | 320 | 3.850 | 6.86645508e-05 |

The length-selected domain-rate extrapolation is 4.009 hours before source
replay and verification. It does not cover the corpus's long-context/edit
distribution and cannot license main. The original scalar projection was
13.032 hours. Timings are observed in sequential runs, not a controlled benchmark
of host load. Retain every prior attempt and its compute charge.

Twelve targeted checks pass, including actual tiny-transformer edits, shortened
reentry, Unicode, boundary retokenization and overflow; deliberate corruption
refusals; serialized saved-unit resume and immutable completed reentry; and real
counted-runtime execution with fresh-process verification. Production owner
inspection authenticates all 107 source pins and
16 output hashes, independently compares every one
of the 612 target rows, and verifies native exits and released CPU slot.

No new hypothesis probability, family state, paid call, GPU work or D30.s
successor credit follows. D33's extension and D36 remain unfinished. Native
overlap losses remain contextual features, not normalized word probabilities.
Raw texts, identities and target losses remain private.

[Frozen contract](../../../docs/design/stage-15/drive/P7_HYBRID_PILOT.md) ·
[Aggregate verification and hashes](P7-hybrid-pilot.json).
