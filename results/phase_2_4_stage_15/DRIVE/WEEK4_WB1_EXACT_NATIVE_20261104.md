# WEEK4 WB1 EXACT NATIVE 20261104

**Hypothesis.** Can the original piece-effects pipeline avoid rescanning unchanged document states while preserving every computed window and downstream work item?

**METHOD.** Cache the current Unicode text and sentence-ending count only between actual text operations. Keep all source reconstruction, anchor/end ordinals, censoring, accepted-unit survival, encoder tokenization and batches unchanged. Compare complete outputs against the original across every anchor of all canonical insertion cases, including Unicode, deleted/reinserted punctuation, empty deltas and retain-only events. Compare complete constructed cost-work digests and independently replay the native consumer.

**Found.** The exact document-state cache matches complete original effect windows and cost-work digests in native replay; a fresh corpus cost probe remains required.

The table reports completed implementation validation, not corpus effects.

| Check | Complete record |
|---|---:|
| Targeted checks passing | 5 |
| Native sampled sessions | 8 |
| Native attempt CPU seconds | 4.562500 |
| Verified outputs / pins | 14 / 89 |

The first complete-consumer test failed before effects because its old fixture supplied accepted eligibility without raw option and selection metadata. That failure and source remain recorded. One fixture-only correction supplies the already declared option/index and proves canonical eligibility; production checks are unchanged. The original effects implementation and every cost failure remain intact. No speed-up is claimed until measured on the full frozen first-tenth workload.

**Means.** Run only the already authorized fresh cost probe, bounded at 7,200 CPU seconds including independent replay, charged with all earlier work to the Week 4 named idle allowance. Full coverage, complete effects and the companion return still require complete admission. No new hypothesis, paid transfer, delegation or gear change.
