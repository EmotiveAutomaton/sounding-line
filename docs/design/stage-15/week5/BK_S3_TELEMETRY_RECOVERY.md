# S3 source telemetry recovery

DESIGN CHECK, 2026-11-07: LESSONS 3-5, especially bounded Windows sharing
retries, immutable source compatibility and actual native handler validation.
Both scientific directions retain the same source extraction, matching and
verification. This is an engineering repair under the existing S3 design.

The original full extraction remains preserved. Its independent verifier failed
while replacing mutable progress JSON, with Windows access refusal, before
verification completed. It supplies no admitted scientific result. All previous
CPU charges remain additional, including the 1,374.515625-second failed attempt.

The successor uses the original source function's exact code with only its
progress publisher rebound to the previously qualified bounded atomic writer.
That writer retains unique temporaries and retries only access/sharing refusals
for at most five seconds. Persistent denial and unrelated I/O errors still fail;
the old pinned helper remains unchanged. Inputs, configuration, raw-source
authentication, exact matching, summary fields and complete source replay stay
unchanged. No effect estimate or inferential threshold is touched.

Native validation must reproduce the original failure with an actual Windows
read handle, complete the successor after releasing that handle, reproduce all
original constructed rows and summary, perform fresh-process full verification,
and refuse altered source output. Persistent-refusal and unrelated-I/O tests
exercise the reused writer. No human source is used in this fixture.

Recovery starts in a fresh empty output directory, with the original corpus
inputs, 1,399 sessions and complete execution plus independent replay. The old
elapsed-time pilot is not a resumable checkpoint. The new attempt is bounded
at 2,200 CPU seconds, forecasting 1,800 for complete extraction and replay;
all costs remain charged against S3's original 3,600-second ceiling, its existing
doubling/continuation rules and the BK family budget; validation is additional.
This forecast uses the observed failed attempt's near-complete verification,
not a faster execution-only prefix. Resource floors are unchanged. Admission
requires zero other scientific/source workers and a single original-bank CPU
lease, at most two numerical threads, below-normal priority. First gear remains
active; GPU, Ollama, paid work and parallel builder compute remain held.
