# Complete suggestion throughput recovery

**Hypothesis.** Can lower-overhead safety telemetry make the unchanged
suggestion pass feasible without changing its scores or safety checks?
**METHOD.** Run the complete same-input five-reader timing pilot using direct
NVIDIA telemetry; independently replay every checkpoint, tokenization and
reduction, compare all native-token losses with the prior valid pilot, verify
loaded-device telemetry against the original command, and recompute fixed costs.

The table reports the entire timing and equivalence check, not scientific scores.

| Check | Complete result |
|---|---|
| Integrity | All 25 checkpoints, 48 output bindings and 90 source pins verify |
| Score equivalence | All 6176 native-token losses exactly match the prior valid pilot |
| Safety | Same check counts; six startup/loaded-model telemetry comparisons and all floors pass |
| Full-pass estimate | 43.27 hours including the unchanged threefold safety factor; below 72 hours |
| Storage estimate | 0.91 GiB including the same factor; below 32 GiB |
| Closure | Exact native worker exited and GPU lease released |

**Found.** The complete pilot preserves every compared score and safety check,
and its measured forecast now passes full-suggestion execution admission.
**Means.** The suggestion component may run under its frozen measured bounds.
This does not complete the corpus, typed/history component or downstream studies.

The improvement changes telemetry transport only. All models remain float32
and fully resident; contexts, input support, loss definitions and tolerance stay
unchanged. All failures and original timings remain. Main has no scientific
verdict until its complete support and outputs are independently checked.
The input census is reused byte-identically, not independently retokenized in
full. Pilot timing and sampled memory observations are estimates, not guarantees;
main retains hard time/byte limits and immediate resource-loss refusal.

[Independent verification](SUGGESTION_PILOT_V4.json). [Frozen contract](../../../docs/design/stage-15/drive/SUGGESTION_CORPUS_V4.md).
