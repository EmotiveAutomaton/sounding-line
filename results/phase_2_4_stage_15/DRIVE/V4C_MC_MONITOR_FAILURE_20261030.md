# V4C MC MONITOR FAILURE 20261030

**Hypothesis.** Did the stopped worker fail in the scientific computation or in its supervision?

**METHOD.** Inspect parent stderr, contained-job accounting, terminal hashes and exact parent/child creation identities. Authenticate every pinned source and retained sealed checkpoint, while checking the other workers and monitoring.

**Found.** A temporary-file race in the supervisor stopped one CPU shard; its failed attempt and checkpoints remain preserved, with no scientific verdict.

The v5 output-size scan called a file-existence check and then inspected size after the atomic progress writer replaced its unique temporary file. The resulting missing-file exception closed the contained worker. Its 944.8125 CPU seconds remain charged, including the termination margin; no fresh verification or complete outer-world result existed. The other three original workers continued with unchanged sources.

**Means.** This is an engineering failure, not a scientific null or failed sensitivity gate. Healing attempt one isolates the supervisor correction, retains the original attempt and all failed evidence, and resumes only authenticated checkpoints within the original ceiling. No tests harvested from this operational wake.
