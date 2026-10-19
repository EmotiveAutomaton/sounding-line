# EV original-word join: constructed validation complete

**Hypothesis.** Original D33 words and covariates can be joined to the final-document ledger without silently replacing deleted words or dropping unsupported rows.

**METHOD.** Preserve every original row and attach final spans only by its session and production index. Check exact typed provenance, character counts, document hashes, source partitions and support totals. Exercise repeated spelling, deletion/reinsertion, Unicode, out-of-cohort sessions, duplicate identities, altered provenance and nonfinite covariates; repeat the serialized join in a fresh process.

**Found.** All 14 targeted software checks pass. **Means.** The component preserves original outcomes and covariates while distinguishing final survivors from deleted words and pilot-unselected sessions. A survivor still awaits the engine's exact lexical/content-word match; no score is imputed to unsupported rows.

The first test invocation passed 13 checks but could not create one fixture in the default temporary directory. Its report is retained; a new workspace temporary directory allowed all 14 checks to pass without changing code. The [validation receipt](EV_D33_JOIN_BUILD_20261018.json) pins source and test bytes.

This is a constructed component check, not a corpus comparison. Authenticated original-D33/input-cohort consumption and counted native replay, exact engine-word joins, the typed-fragment variant, measured reader admission and statistical known-answer checks remain. No corpus or model execution, scientific admission, new hypothesis or probability follows. Shared instrument/TODO integration remains at 20:00 PDT.
