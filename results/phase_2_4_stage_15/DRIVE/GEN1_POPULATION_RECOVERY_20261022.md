# Genre matching: admitted-population join recovery

**Hypothesis.** Genre metadata can join the exact completed study population even when the upstream archive is larger.
**METHOD.** Authenticate every completed PMAP session and aggregate count, require exact equality with the completed word ledger and full coverage by the archive, retain upstream-only records separately, and replay the unchanged matching policy in a fresh native process.
**Found.** The first corpus attempt refused the archive/study population mismatch before matching. Eight additional checks and full native recovery validation pass. **Means.** A single source-only corpus retry is admitted; no genre result exists.

The archive contains 1,445 sessions; the completed study and word ledger contain
1,399. The 46 upstream-only records are not new study exclusions or guessed
invalid sessions. The original component repeated the earlier PMAP join defect:
its constructed fixture did not contain legitimate upstream extras. Original
code, native validation and failed corpus evidence are retained.

The separate recovery authenticates all three source identities and refuses
missing admitted sessions, altered sources, conflicting writer/prompt/time
metadata, duplicate completed outputs, wrong aggregate counts and changed
saved population records. Its fixture includes an upstream-only record and
reproduces the original complete matching manifest exactly. All eight new checks
pass in addition to the original nineteen matching checks. Every pinned source
and native output verifies; all original and recovery workers exited and
released their slots. [Machine receipt](GEN1_POPULATION_RECOVERY_20261022.json).

The failed pass used 0.685773 wall seconds; the complete native recovery used
2.030105 seconds. Both builds, targeted tests, native runs and failed attempt are
covered by one conservative 240-second preparation reserve. The corpus retry's
600-second combined execution/replay cap remains inside the original 1,800-second
allowance; S4 remains unused. Subsequent work must retain these charges.

The [recovery contract](../../../docs/design/stage-15/drive/GEN1_POPULATION_RECOVERY_20261022.md)
preserves the original matching policy. No scientific probability, family count
or theory claim follows. No new test was harvested. Matched feature extraction,
full galleries and empirical controls remain unfinished.
