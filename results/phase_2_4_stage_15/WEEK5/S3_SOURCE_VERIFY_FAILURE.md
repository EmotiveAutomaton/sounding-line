# S3 SOURCE VERIFY FAILURE

**Hypothesis.** Can the completed source extraction be independently verified without losing evidence during the requested gear reduction?

**METHOD.** Let the non-resumable source unit continue its verification while other workers checkpoint. After native exit, inspect the exception and retained execution result, hash every attempt file privately, and retain the incomplete-verification boundary rather than promoting source counts.

**Found.** The source extraction is preserved, but independent verification stopped on a progress-file access error; the campaign is now idle in first gear with serial recovery pending.

The source producer completed extraction. Its independent verifier then stopped when Windows denied replacing a mutable progress file, before producing a verification receipt. The error is in telemetry publication, not an observed mismatch between source outputs; nevertheless, the full source remains unverified and unavailable to downstream inference. No scientific result is inferred from the partial replay. The attempt consumes 1,374.515625 CPU seconds, all retained. The execution result, compressed private event rows, source summary, pilot receipt, failed progress temporary file and both process logs are preserved with a private hash manifest. The owner and both numerical children have exited. No process was forcibly killed.

| Operational item | Disposition |
|---|---|
| Completed extraction files | Preserved; not scientifically admitted |
| Independent verification | Incomplete after Windows progress-file access refusal |
| Attempt CPU charge | 1,374.515625 seconds retained |
| Current research workers | Zero; first-gear maximum remains one |
| Next action | Bounded telemetry-write repair, native fault proof, then serial fresh source replay |

This is an engineering failure retained separately from the six intentional gear pauses. Recovery must not alter source mapping, matching, inputs, controls or numerical gates. The original pinned implementation and failed attempt remain intact; any repaired successor needs review and validation before its serial admission. The extractor's in-memory state is not advertised as a resumable checkpoint, and its immutable elapsed-time pilot receipt must not be copied into a fresh execution directory. The next scheduled first-gear review owns this recovery; no parallel refill, GPU work or builder compute is restarted by the failure. Previous source rows and all six authenticated pause manifests remain preserved.
