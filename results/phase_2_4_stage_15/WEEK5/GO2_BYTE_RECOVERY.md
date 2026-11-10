# GO2 BYTE RECOVERY

**Hypothesis.** Can historical proposal text be read without losing a subprocess result or inventing continuity across unknown text?

**METHOD.** Inspect the exact historical-byte failure, test strict decoding and gap boundaries, execute a real constructed Git history with copying and encoding changes, and verify the complete source independently in a separate native process before admitting the second correction.

**Found.** The second proposal-history source correction captures raw Git bytes and treats undeclared undecodable versions as explicit gaps; both previous failures and their costs remain preserved.

The original source failed on copied-file ancestry; its first correction then encountered a Windows subprocess decoding failure. Git exited successfully but the text reader thread failed and returned no decoded output. The exact failed document has twelve undeclared non-UTF8 versions among 35 same-document revisions. The first correction consumed 10.421875 CPU seconds in addition to the original 11.171875; neither is scientific evidence.

The new immutable successor captures bytes first. It accepts strict UTF8/BOM or an explicitly declared supported encoding, counts unsupported/binary/undecodable versions, and makes each unavailable version a barrier to both adjacent differences and before/after windows. It never guesses a legacy charset. Two focused tests and the actual Git copy/invalid-byte/declared-Latin1/UTF8 native fixture with independent replay pass. Design commit 214a06375 precedes admission. The first 72-of-1,440-document source checkpoint retains the same inputs and scientific definitions; all exclusions must be reported. This is the second allowed engineering correction, with original attempts retained, not permission for an unlimited retry loop. Complete source verification still precedes inference.
