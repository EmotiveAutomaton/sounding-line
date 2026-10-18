# Suggestion continuation: memory interruption, checkpoints preserved

**Hypothesis.** The unchanged suggestion pass can continue from authenticated checkpoints while respecting its original GPU limits.
**METHOD.** Inspect the recorded guard sample, exact native exit and released lease; revalidate every retained checkpoint against its source cases, origin plan and reductions, and charge elapsed time to the original allowance.
**Found.** The memory guard stopped the worker; all 4,988 saved checkpoints validate. **Means.** This is an environmental interruption under the October 18 errata. The same study is prepared to resume when the unchanged cold-start floor is met; it is unfinished, with no scientific verdict.

The table contains operational measurements only. Checkpoint counts are saved work, not scientific scores.

| Check | Verified observation | Unchanged limit or disposition |
|---|---|---|
| Stop at 11:56 PDT | 1,022 MiB free; 66 C | At least 1,024 MiB free; at most 78 C |
| Retained work | 4,988 checkpoints, including 535 new in this continuation | Exact consecutive prefix; full roster incomplete |
| Retained bytes | 201,000,047 | All source bindings and reductions revalidated |
| Source pins | All 110 predecessor pins and 117 prepared-continuation pins verify | Original sources and scoring protocol unchanged |
| Time charged for this continuation | 3,298 seconds | 119,345 seconds remain in the original compute allowance |
| Worker and lease | Exact worker exited; GPU lease released | No process cleanup required |
| Cold-start check at 12:01 PDT | 4,827 MiB free; 49 C | 7,424 MiB free required; continuation remains parked |

Rules 2 and 3 of the [mid-run errata](../../../docs/design/stage-15/drive/SOUNDING_LINE_MIDRUN_ERRATA_2026-10-18.md)
authorize environmental continuation from validated checkpoints. This interruption
does not consume an engineering retry. The next execution has a separate operational
receipt preserving the predecessor; it is not a new scientific version. No input,
comparator, seed, precision, contrast, safety threshold or aggregate allowance changes.
Pins and checkpoints will be checked again before launch. No unrelated application
was stopped, and the memory change is not attributed to a particular application.

Full suggestion output and its dependent comparisons remain unavailable. CPU
validation continues independently. No unfinished score, probability or family-null
count is introduced. Theory/TODO integration remains at the 20:00 digest.

Curator roll-up: reader apparatus; can the fixed pass continue safely without losing work?;
**Infrastructure**; every saved checkpoint survives the environmental interruption;
project meaning: reader execution remains unfinished but recoverable;
next engineering obligation: relaunch only after the unchanged cold-start floor and
fresh integrity checks pass; public claim unchanged; curator decision required: No;
detail: [aggregate integrity receipt](SUGGESTION_ENVIRONMENT_1_STOP.json).
