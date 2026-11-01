# V4C STORAGE VALIDATION 20261030

**Hypothesis.** Can the existing reference checkpoints be stored within their fixed limit without changing any scientific byte or computation?

**METHOD.** Compare original and compressed canonical bytes and hashes; exercise the actual 199-reference orchestration, authenticated-prefix resume, changed-value and corruption refusals, pause handling, physical-manifest collection and fresh replay. Measure compression on one complete fixed world and the first reference of every retained world, selected before the measurement. Run a separate native execution and verification under the real bounded supervisor.

**Found.** Lossless storage passes byte, checkpoint, corruption and fresh native replay checks; its conservative full-shard size forecast fits the unchanged cap.

Seven targeted tests and one additional source-retained resume-projection test pass. The native constructed rehearsal completes with fresh 199-reference replay under both storage paths. The numerical consumer and collector remain unchanged; separate wrappers adapt storage only. Each compressed file is bound by a physical manifest, itself bound by the completion receipt, while original seals retain the exact uncompressed digest. Original attempts and the original representation remain retained.

The table describes storage engineering checks; it contains no scientific effect estimates.

| Check | Outcome |
|---|---|
| Gzip complete-world forecast | Rejected: exceeds cap with margin |
| First bounded XZ world probe | Stopped at its 120-second probe budget; no admission |
| Expanded fixed XZ probe | 242 references reproduce every byte |
| Largest-shard forecast, including 50% margin and metadata | 7,123,764,848 bytes, below 8,589,934,592 |
| Native execute plus fresh replay | Complete; 4.84375 CPU seconds |

The expanded XZ probe used 148.875 CPU seconds. A preliminary command failed on an unavailable timestamp import before any compression; it was corrected and retained in the probe record. The initial pytest run warned that its cache directory was unwritable, while all test bodies passed; subsequent invocations disabled that optional cache. A supplemental test edit occurred after native completion; its executed source was archived separately and the original pinned test source restored byte-for-byte.

A conservative 3,000 CPU seconds per shard is reserved from the existing allowance for diagnosis and validation; unused reservation is not reclaimed. It supersedes the initial smaller reservation because stronger compression required a larger measured probe. Conversion itself runs inside each counted continuation and its remaining CPU ceiling, so the allowance is conservative. No global budget, byte cap, fitting operation, seed, precision, world or band changes.

The resumed CPU projection uses the original measured first-tenth record, discounts only retained generation work, adds a ten-percent recovery allowance and measured compression overhead plus a bookkeeping allowance. Verification of every reference remains included. The original projection and its source hash remain recorded; cumulative hard limits remain authoritative.

**Means.** Admit separately frozen storage continuations only after source and budget reconciliation. This is instrument validation, not scientific calibration; complete aggregation remains required.
