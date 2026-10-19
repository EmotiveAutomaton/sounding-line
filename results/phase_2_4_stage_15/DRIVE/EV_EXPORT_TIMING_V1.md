# EV pinned-reader timing pilot: complete and verified

**Hypothesis.** The pinned CPU reader can export authenticated engine features and reproduce them in a fresh uncached process within a bounded timing allocation.
**METHOD.** Run the first ten sorted documents from the authenticated source pilot through the frozen ToMpathy exporter, reconstruct the selected source records and repeat the entire reader export in a fresh process. Independently authenticate all pins, manifests, rows, support dispositions and output hashes; inspect exact native exits and the released counted slot.
**Found.** Execution and fresh replay agree exactly. All 2,008 source pins and 29 terminal artifacts verify; combined active wall time is 185.30 seconds under the unchanged 1,800-second cap. **Means.** The bounded reader path is valid. This is infrastructure validation, with no pause association, writer-identification result, signature badge or full-population admission.

The table accounts for every original word row. These are input support dispositions, not scientific scores. The ten documents were selected by sorted identifier without inspecting outcomes; they are not a representative population sample.

| Disposition | Original word rows | Meaning |
|---|---:|---|
| Engine scored | 454 | Intact final content word with an authenticated engine score |
| Engine held out | 4 | Engine's own exclusion applies |
| Engine non-content | 246 | Final word is outside its content-word rule |
| Not intact final word | 61 | Original occurrence cannot join an intact final word |
| Outside input cohort | 77,837 | Original row remains, outside these ten documents |
| Total | 78,602 | All original rows and covariates retained; no zero-filled exclusions |

The next table separates elapsed wall time from sampled process CPU time and memory. CPU sampling may miss startup/exit work; it is not the enforced cost ledger. Whole active wall time includes authentication, joins and fresh source reconstruction.

| Phase | Export wall seconds | Sampled CPU seconds | Peak sampled process-tree RAM, GiB |
|---|---:|---:|---:|
| Execution | 70.18 | 47.69 | 5.34 |
| Fresh uncached verification | 47.86 | 46.11 | 5.38 |

Whole-handler execution and replay took 185.30 seconds. Prior source preparation/replay (962.19 seconds) and the authenticated input consumer (366.69 seconds) remain charged, giving 1,514.18 seconds of completed corpus-pilot work. Known-answer build rehearsals remain separately recorded. No GPU, download or paid call was used. Typed fragment inputs are retained; their reader export and habit analysis remain unrun.

A simple linear projection of full source preparation plus the entire ten-document handler is 39,384.92 seconds, or 10.94 hours. It includes fixed setup and overlapping reconstruction, comes from a small sorted cohort, and is **not an admitted forecast**. It exceeds the export's one-time eight-hour S4 ceiling before a new uncertainty allowance. Full-corpus dispatch remains held. The already commissioned first-100 signature-support pilot is the next bounded step: it can measure support and reduce fixed-cost uncertainty without extending the full-run cap. Admission must retain prior charges, the demo slot, measured memory floor and all source/replay work.

The original import-shadowing failure and corrected constructed rehearsal remain in the [handler build](EV_EXPORT_HANDLER_BUILD_20261018.md). The worker and known descendants have exited; the counted lease is released. No new research test or probability was introduced. [Machine receipt](EV_EXPORT_TIMING_V1.json).
