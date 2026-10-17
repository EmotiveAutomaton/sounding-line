# Reader memory recovery: complete fixed pilot

**Hypothesis.** Can the same reader pilot fit alongside other applications
without reducing precision, context or numerical accuracy?
**METHOD.** Recompute the three fixed Pythia readers with float32 weights,
no retained attention cache and 32-token output blocks. Compare every eligible
token from the two smaller Pythias with their preserved cached results, and
the largest reader's first menu in all four contexts with ordinary direct
scoring. Reuse the two completed Smol/Qwen pilots byte for byte. Independently
reconstruct all token/byte alignments and score reductions from the fixed inputs,
verify every frozen output/source hash, and inspect native closure and monitoring.

**Found.** The complete fixed pilot passes its memory and numerical checks.
The largest reader retained at least 1.29 GiB of sampled free GPU memory.
**Means.** The smaller-memory implementation works on this pilot while other
applications remain open; the full-corpus run still needs its own execution plan.

The table reports complete instrument checks, not scientific comparisons.
Memory figures are MiB; differences are absolute per-token losses in nats.

| Check | Complete result |
|---|---|
| Fixed coverage | All five readers: 11 menus × four contexts, 184 eligible targets each; no exclusions |
| Newly computed ladder | Pythia 410M, 1B and 1.4B; full float32 CUDA residency, 2048-token window, no cache |
| Retained ladder | Smol360 and Qwen500 scores/telemetry byte-identical to the earlier completed outputs |
| Numerical agreement | Pythia maximum differences 0.001325, 0.00002956 and 0.00002527; all below unchanged 0.02 tolerance |
| Comparison coverage | All 184 eligible targets per smaller Pythia; four direct-reference contexts for the largest |
| Largest reader memory | Peak allocated 5599.10; peak reserved 5842, below 5888 cap; minimum sampled free 1327, above 1024 floor |
| Full-window stress | Deterministic 2048-token input, 32 finite target losses; peak reserved 5760, sampled free 1522 |
| Validation | Nine software controls and one real CUDA workspace-cleanup test pass |
| Evidence integrity | All 22 terminal output bindings and 52 source/input pins verify; tokenization, UTF-8 denominators and loss reductions reconcile |
| Closure | Exact native worker exited; GPU lease released; monitor handshake and watcher source/identity checks pass |

The original v4 resource failure and v5 cleanup failure remain unchanged. The
separate v6 repair releases only this process's native BLAS workspace after
unloading each model, retaining the exact-zero boundary. It does not reset the
GPU or stop another application. Its installed private PyTorch cleanup API is
covered by the actual CUDA test and the frozen runtime versions.

This establishes fixed-pilot apparatus validity, not a human scientific result
or full-corpus admission. The reused Smol/Qwen records retain their original
missing contemporaneous runtime-version provenance. Free memory was sampled
around work; it is not a continuous trace or a promise under a different
competing workload. The new readers took roughly 52–54 seconds each for these
short menus; those rates include guards and equivalence work and cannot size the
full corpus. The history context, typed-sentence roster, representative throughput
measurement and checkpointed corpus runner remain implementation obligations.
No automatic corpus dispatch, new paid call or scientific test followed this wake.

[Aggregate verification](READER_PILOT_V6.json) ·
[Frozen contract](../../../docs/design/stage-15/drive/READER_PILOT_V6.md) ·
[Original cleanup failure](READER_PILOT_V5.json).
