# P6: retained arithmetic-verification failure

**Hypothesis.** The word-baseline scores should reproduce exactly from the retained token probabilities.
**METHOD.** Inspect the verification failure and recompute every saved token surprisal and session reduction under both arithmetic orders.
**Found.** All token values and left-to-right reductions match exactly. Verification instead used Python's compensated sum, differing by at most 1.46e-11 in a session total. **Means.** This is an arithmetic-replay failure, not a negative research result. Preserve the failed attempt and use the one permitted engineering recovery to reproduce the original accumulation exactly, without changing any score or tolerance.

The discrepancy affects 1,219 of 1,399 session totals. All original score-file hashes, token surprisals, counts, source pins and native exit verify. No primary score is admitted from this failed attempt. Its successor must bind the original plan, failure and every reused byte, retain exact equality and pass fresh-process verification. Timing consumers remain held until that successor lands. [Diagnosis](P6-failed.json).
